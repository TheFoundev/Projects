'use strict';
const { test } = require('node:test');
const assert = require('node:assert');
const { spawn } = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const clinical = require('../clinical');

const ROOT = path.join(__dirname, '..');
const PORT = 4800 + Math.floor(Math.random() * 300);

function waitFor(url, timeout = 12000) {
  const started = Date.now();
  return new Promise((resolve, reject) => {
    const tick = async () => {
      try {
        const response = await fetch(url);
        if (response.ok) return resolve(response);
      } catch {}
      if (Date.now() - started > timeout) return reject(new Error('server did not start'));
      setTimeout(tick, 150);
    };
    tick();
  });
}

async function startServer() {
  const dataDir = fs.mkdtempSync(path.join(os.tmpdir(), 'clinical-test-'));
  const child = spawn(process.execPath, ['server.js'], {
    cwd: ROOT,
    env: { ...process.env, PORT: String(PORT), DATA_DIR: dataDir },
    stdio: ['ignore', 'pipe', 'pipe'],
  });
  await waitFor(`http://127.0.0.1:${PORT}/api/meta`);

  const register = await fetch(`http://127.0.0.1:${PORT}/api/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: 'Test Clinician', email: 'clinician@example.test', password: 'correct-horse' }),
  });
  const cookie = register.headers.get('set-cookie').split(';')[0];

  const call = async (method, urlPath, body) => {
    const response = await fetch(`http://127.0.0.1:${PORT}${urlPath}`, {
      method,
      headers: { 'Content-Type': 'application/json', Cookie: cookie },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    const text = await response.text();
    let json = null;
    try { json = text ? JSON.parse(text) : null; } catch { json = text; }
    return { status: response.status, json };
  };

  const stop = () => {
    child.kill('SIGTERM');
    fs.rmSync(dataDir, { recursive: true, force: true });
  };

  return { call, stop };
}

// ---------------------------------------------------------------------------
// The rules
// ---------------------------------------------------------------------------

test('two appointments in the same place at the same time overlap', () => {
  assert.ok(clinical.overlaps('2026-04-23T09:00:00.000Z', 30, '2026-04-23T09:15:00.000Z'));
  assert.ok(!clinical.overlaps('2026-04-23T09:00:00.000Z', 30, '2026-04-23T09:30:00.000Z'));
  assert.ok(!clinical.overlaps('2026-04-23T09:00:00.000Z', 30, '2026-04-24T09:00:00.000Z'));
});

test('an appointment that needs no time is refused', () => {
  const problem = clinical.checkAppointment({ patient_id: 1, provider: 'Dr Who', scheduled_at: 'not a date' }, []);
  assert.match(problem, /valid date and time/);
});

test('a patient cannot be booked twice', () => {
  const existing = [{ id: 1, patient_id: 1, provider: 'Dr Who', scheduled_at: '2026-04-23T09:00:00.000Z', status: 'scheduled' }];
  const problem = clinical.checkAppointment(
    { id: 2, patient_id: 1, provider: 'Dr Other', scheduled_at: '2026-04-23T11:00:00.000Z' },
    existing,
  );
  assert.match(problem, /already has an appointment/);
});

test('a provider cannot be in two places at once', () => {
  const existing = [{ id: 1, patient_id: 1, provider: 'Dr Who', scheduled_at: '2026-04-23T09:00:00.000Z', status: 'scheduled' }];
  const problem = clinical.checkAppointment(
    { id: 2, patient_id: 2, provider: 'Dr Who', scheduled_at: '2026-04-23T09:15:00.000Z' },
    existing,
  );
  assert.match(problem, /already has an appointment/);
});

test('a cancelled appointment blocks nothing', () => {
  const existing = [{ id: 1, patient_id: 1, provider: 'Dr Who', scheduled_at: '2026-04-23T09:00:00.000Z', status: 'cancelled' }];
  assert.equal(clinical.checkAppointment(
    { id: 2, patient_id: 1, provider: 'Dr Who', scheduled_at: '2026-04-23T09:00:00.000Z' },
    existing,
  ), null);
});

test('an appointment without a provider is refused', () => {
  const problem = clinical.checkAppointment({ patient_id: 1, provider: '', scheduled_at: '2026-04-23T09:00:00.000Z' }, []);
  assert.match(problem, /provider/);
});

test('an appointment for a patient that does not exist is refused', () => {
  const patients = [{ id: 1, name: 'Ann', status: 'active' }];
  const problem = clinical.checkAppointment(
    { patient_id: 99, provider: 'Dr Who', scheduled_at: '2026-04-23T09:00:00.000Z' },
    [],
    patients,
  );
  assert.match(problem, /does not exist/);
});

test('a prescription needs a real patient, a medication and a dose', () => {
  const patients = [{ id: 1, name: 'Ann', status: 'active' }];
  assert.match(clinical.checkPrescription({ patient_id: 99, medication: 'X', dose: '1' }, patients), /does not exist/);
  assert.match(clinical.checkPrescription({ patient_id: 1, medication: '', dose: '1' }, patients), /medication/);
  assert.match(clinical.checkPrescription({ patient_id: 1, medication: 'X', dose: '' }, patients), /dose/);
  assert.equal(clinical.checkPrescription({ patient_id: 1, medication: 'X', dose: '1 tablet' }, patients), null);
});

test('a prescription for an inactive patient is refused', () => {
  const patients = [{ id: 1, name: 'Ann', status: 'deceased' }];
  assert.match(clinical.checkPrescription({ patient_id: 1, medication: 'X', dose: '1' }, patients), /deceased/);
});

test('a lab order needs a patient, a test and a known priority', () => {
  const patients = [{ id: 1, name: 'Ann', status: 'active' }];
  assert.match(clinical.checkLabOrder({ patient_id: 99, test: 'CBC' }, patients), /does not exist/);
  assert.match(clinical.checkLabOrder({ patient_id: 1, test: '' }, patients), /test/);
  assert.match(clinical.checkLabOrder({ patient_id: 1, test: 'CBC', priority: 'whenever' }, patients), /priority/);
  assert.equal(clinical.checkLabOrder({ patient_id: 1, test: 'CBC', priority: 'stat' }, patients), null);
});

test('a lab order moves through its states', () => {
  assert.ok(clinical.canTransitionLab('ordered', 'collected'));
  assert.ok(clinical.canTransitionLab('collected', 'in_progress'));
  assert.ok(clinical.canTransitionLab('in_progress', 'completed'));
  assert.ok(!clinical.canTransitionLab('completed', 'ordered'));
  assert.ok(!clinical.canTransitionLab('ordered', 'completed'));
  assert.match(clinical.labTransitionError('completed', 'ordered'), /cannot go/);
});

test('a prescription and an incident have their own transitions', () => {
  assert.ok(clinical.canTransitionPrescription('active', 'filled'));
  assert.ok(!clinical.canTransitionPrescription('filled', 'active'));
  assert.ok(clinical.canTransitionIncident('open', 'under_review'));
  assert.ok(!clinical.canTransitionIncident('resolved', 'open'));
});

test('the blood types and the severities are the ones the system knows', () => {
  assert.ok(clinical.isValidBloodType('O+'));
  assert.ok(clinical.isValidBloodType('AB-'));
  assert.ok(!clinical.isValidBloodType('C+'));
  assert.ok(clinical.isValidSeverity('critical'));
  assert.ok(!clinical.isValidSeverity('catastrophic'));
});

test('a patient record raises the right alerts', () => {
  const alerts = clinical.patientAlerts({ name: 'Ann', allergies: 'penicillin', blood_type: 'O+' });
  assert.ok(alerts.some((alert) => alert.level === 'high' && /penicillin/.test(alert.text)));

  const none = clinical.patientAlerts({ name: 'Ann', allergies: 'None', blood_type: 'O+' });
  assert.ok(!none.some((alert) => alert.level === 'high'));

  const unknownType = clinical.patientAlerts({ name: 'Ann', allergies: '', blood_type: 'C+' });
  assert.ok(unknownType.some((alert) => /not a blood type/.test(alert.text)));
});

test('the severity decides what has to happen', () => {
  assert.match(clinical.severityAction('critical'), /now/);
  assert.match(clinical.severityAction('high'), /within the hour/);
  assert.match(clinical.severityAction('low'), /ordinary channel/);
  assert.equal(clinical.severityOf({ severity: 'nonsense' }), 'low');
});

test('the day schedule is in order and skips the cancelled ones', () => {
  const appointments = [
    { id: 1, scheduled_at: '2026-04-23T11:00:00.000Z', status: 'scheduled' },
    { id: 2, scheduled_at: '2026-04-23T09:00:00.000Z', status: 'scheduled' },
    { id: 3, scheduled_at: '2026-04-23T10:00:00.000Z', status: 'cancelled' },
    { id: 4, scheduled_at: '2026-04-24T09:00:00.000Z', status: 'scheduled' },
  ];
  const schedule = clinical.daySchedule(appointments, '2026-04-23');
  // The cancelled one is dropped, the other day is a different day.
  assert.equal(schedule.length, 2);
  assert.deepEqual(schedule.map((row) => row.id), [2, 1]);
});

test('the patient summary gathers everything about one patient', () => {
  const patient = { id: 1, name: 'Ann', status: 'active', blood_type: 'O+' };
  const summary = clinical.patientSummary(patient, {
    appointments: [{ id: 1, patient_id: 1 }, { id: 2, patient_id: 2 }],
    prescriptions: [{ id: 1, patient_id: 1, status: 'active' }, { id: 2, patient_id: 1, status: 'discontinued' }],
    labOrders: [{ id: 1, patient_id: 1, status: 'ordered' }],
  });

  assert.equal(summary.appointments.length, 1);
  assert.equal(summary.active_prescriptions.length, 1);
  assert.equal(summary.pending_labs.length, 1);
});

// ---------------------------------------------------------------------------
// The API
// ---------------------------------------------------------------------------

test('a patient is created with the configured defaults', async () => {
  const { call, stop } = await startServer();
  try {
    const created = await call('POST', '/api/patients', { name: 'Ann Smith', dob: '1990-04-23', blood_type: 'O+' });
    assert.strictEqual(created.status, 201);
    assert.strictEqual(created.json.status, 'active');
  } finally {
    stop();
  }
});

test('a patient with an impossible blood type is refused', async () => {
  const { call, stop } = await startServer();
  try {
    const created = await call('POST', '/api/patients', { name: 'Ann Smith', blood_type: 'C+' });
    assert.strictEqual(created.status, 400);
  } finally {
    stop();
  }
});

test('an appointment for a patient that does not exist is refused', async () => {
  const { call, stop } = await startServer();
  try {
    const created = await call('POST', '/api/appointments', {
      patient_id: 999, provider: 'Dr Who', scheduled_at: '2026-04-23T09:00:00.000Z',
    });
    assert.strictEqual(created.status, 400);
  } finally {
    stop();
  }
});

test('a patient cannot be booked twice', async () => {
  const { call, stop } = await startServer();
  try {
    const patient = await call('POST', '/api/patients', { name: 'Ann Smith' });
    const first = await call('POST', '/api/appointments', {
      patient_id: patient.json.id, provider: 'Dr Who', scheduled_at: '2026-04-23T09:00:00.000Z',
    });
    assert.strictEqual(first.status, 201);

    const second = await call('POST', '/api/appointments', {
      patient_id: patient.json.id, provider: 'Dr Other', scheduled_at: '2026-04-23T11:00:00.000Z',
    });
    assert.strictEqual(second.status, 400);
    assert.match(second.json.error, /already has an appointment/);
  } finally {
    stop();
  }
});

test('a prescription without a dose is refused', async () => {
  const { call, stop } = await startServer();
  try {
    const patient = await call('POST', '/api/patients', { name: 'Ann Smith' });
    const created = await call('POST', '/api/prescriptions', {
      patient_id: patient.json.id, medication: 'Aspirin', dose: '',
    });
    assert.strictEqual(created.status, 400);
  } finally {
    stop();
  }
});

test('a lab order moves through its states and cannot go back', async () => {
  const { call, stop } = await startServer();
  try {
    const patient = await call('POST', '/api/patients', { name: 'Ann Smith' });
    const order = await call('POST', '/api/lab_orders', { patient_id: patient.json.id, test: 'CBC' });
    assert.strictEqual(order.status, 201);
    assert.strictEqual(order.json.status, 'ordered');

    const collected = await call('POST', `/api/lab_orders/${order.json.id}/status`, { status: 'collected' });
    assert.strictEqual(collected.status, 200);
    assert.strictEqual(collected.json.status, 'collected');

    const back = await call('POST', `/api/lab_orders/${order.json.id}/status`, { status: 'ordered' });
    assert.strictEqual(back.status, 400);
  } finally {
    stop();
  }
});

test('the patient summary lists the appointments, the prescriptions and the labs', async () => {
  const { call, stop } = await startServer();
  try {
    const patient = await call('POST', '/api/patients', { name: 'Ann Smith', blood_type: 'O+' });
    await call('POST', '/api/appointments', {
      patient_id: patient.json.id, provider: 'Dr Who', scheduled_at: '2026-04-23T09:00:00.000Z',
    });
    await call('POST', '/api/prescriptions', { patient_id: patient.json.id, medication: 'Aspirin', dose: '1 tablet' });
    await call('POST', '/api/lab_orders', { patient_id: patient.json.id, test: 'CBC' });

    const summary = await call('GET', `/api/patients/${patient.json.id}/summary`);
    assert.strictEqual(summary.status, 200);
    assert.equal(summary.json.appointments.length, 1);
    assert.equal(summary.json.active_prescriptions.length, 1);
    assert.equal(summary.json.pending_labs.length, 1);
  } finally {
    stop();
  }
});

test('the clinic diary shows the appointments of a day', async () => {
  const { call, stop } = await startServer();
  try {
    const patient = await call('POST', '/api/patients', { name: 'Ann Smith' });
    await call('POST', '/api/appointments', {
      patient_id: patient.json.id, provider: 'Dr Who', scheduled_at: '2026-04-23T09:00:00.000Z',
    });

    const schedule = await call('GET', '/api/schedule?day=2026-04-23');
    assert.strictEqual(schedule.status, 200);
    assert.equal(schedule.json.appointments.length, 1);
  } finally {
    stop();
  }
});

test('the severity of an incident comes with an action', async () => {
  const { call, stop } = await startServer();
  try {
    const incident = await call('POST', '/api/incidents', { title: 'Wrong patient', severity: 'high' });
    assert.strictEqual(incident.status, 201);

    const severity = await call('GET', `/api/incidents/${incident.json.id}/severity`);
    assert.strictEqual(severity.status, 200);
    assert.strictEqual(severity.json.severity, 'high');
    assert.match(severity.json.action, /within the hour/);
  } finally {
    stop();
  }
});

test('an incident with an unknown severity is refused', async () => {
  const { call, stop } = await startServer();
  try {
    const created = await call('POST', '/api/incidents', { title: 'Something', severity: 'catastrophic' });
    assert.strictEqual(created.status, 400);
  } finally {
    stop();
  }
});
