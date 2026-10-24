'use strict';
/**
 * The clinical domain.
 *
 * The rules a hospital needs before it lets an appointment, a prescription
 * or a lab order be written down: nobody is booked twice, a prescription
 * needs a dose and a patient, a lab order moves through its states and an
 * incident is graded by severity.
 *
 * Pure functions, no database access, so the rules can be unit tested on
 * their own.
 */

/** The states a patient record can be in. */
const PATIENT_STATUSES = ['active', 'inactive', 'deceased'];

/** The states an appointment can be in. */
const APPOINTMENT_STATUSES = ['scheduled', 'checked_in', 'in_progress', 'completed', 'cancelled', 'no_show'];

/** The states a prescription can be in. */
const PRESCRIPTION_STATUSES = ['active', 'filled', 'discontinued'];

/** The states a lab order can be in. */
const LAB_STATUSES = ['ordered', 'collected', 'in_progress', 'completed', 'cancelled'];

/** The states an incident can be in. */
const INCIDENT_STATUSES = ['open', 'under_review', 'resolved'];

/** The severities an incident can have. */
const SEVERITIES = ['low', 'medium', 'high', 'critical'];

/** The lab priorities. */
const PRIORITIES = ['routine', 'urgent', 'stat'];

/** The blood types. */
const BLOOD_TYPES = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'];

/** How long an appointment lasts, in minutes. */
const DEFAULT_SLOT_MINUTES = 30;

/** The states a lab order may move to. */
const LAB_TRANSITIONS = {
  ordered: ['ordered', 'collected', 'cancelled'],
  collected: ['collected', 'in_progress', 'cancelled'],
  in_progress: ['in_progress', 'completed', 'cancelled'],
  completed: ['completed'],
  cancelled: ['cancelled'],
};

/** The states a prescription may move to. */
const PRESCRIPTION_TRANSITIONS = {
  active: ['active', 'filled', 'discontinued'],
  filled: ['filled', 'discontinued'],
  discontinued: ['discontinued'],
};

/** The states an incident may move to. */
const INCIDENT_TRANSITIONS = {
  open: ['open', 'under_review', 'resolved'],
  under_review: ['under_review', 'resolved', 'open'],
  resolved: ['resolved'],
};

function isValidPatientStatus(status) {
  return PATIENT_STATUSES.includes(String(status));
}

function isValidAppointmentStatus(status) {
  return APPOINTMENT_STATUSES.includes(String(status));
}

function isValidPrescriptionStatus(status) {
  return PRESCRIPTION_STATUSES.includes(String(status));
}

function isValidLabStatus(status) {
  return LAB_STATUSES.includes(String(status));
}

function isValidIncidentStatus(status) {
  return INCIDENT_STATUSES.includes(String(status));
}

function isValidSeverity(severity) {
  return SEVERITIES.includes(String(severity));
}

function isValidPriority(priority) {
  return PRIORITIES.includes(String(priority));
}

function isValidBloodType(type) {
  return BLOOD_TYPES.includes(String(type).trim());
}

/** True when a lab order may move from one state to another. */
function canTransitionLab(from, to) {
  const allowed = LAB_TRANSITIONS[String(from)];
  return Boolean(allowed && allowed.includes(String(to)));
}

/** True when a prescription may move from one state to another. */
function canTransitionPrescription(from, to) {
  const allowed = PRESCRIPTION_TRANSITIONS[String(from)];
  return Boolean(allowed && allowed.includes(String(to)));
}

/** True when an incident may move from one state to another. */
function canTransitionIncident(from, to) {
  const allowed = INCIDENT_TRANSITIONS[String(from)];
  return Boolean(allowed && allowed.includes(String(to)));
}

/** The error message for an illegal lab transition, or null. */
function labTransitionError(from, to) {
  if (!isValidLabStatus(to)) return `"${to}" is not a lab order state.`;
  if (!canTransitionLab(from, to)) return `A lab order cannot go from "${from}" to "${to}".`;
  return null;
}

/** The minutes between two ISO timestamps, or null when they cannot be read. */
function minutesBetween(from, to) {
  const left = Date.parse(from);
  const right = Date.parse(to);
  if (Number.isNaN(left) || Number.isNaN(right)) return null;
  return Math.round((right - left) / 60000);
}

/**
 * The end of an appointment.
 *
 * The slot length is configurable, 30 minutes by default.
 */
function appointmentEnd(start, minutes = DEFAULT_SLOT_MINUTES) {
  const time = Date.parse(start);
  if (Number.isNaN(time)) return null;
  return new Date(time + minutes * 60000).toISOString();
}

/** True when two appointments overlap in time. */
function overlaps(aStart, aMinutes, bStart, bMinutes = DEFAULT_SLOT_MINUTES) {
  const left = Date.parse(aStart);
  const right = Date.parse(bStart);
  if (Number.isNaN(left) || Number.isNaN(right)) return false;
  const aEnd = left + aMinutes * 60000;
  const bEnd = right + bMinutes * 60000;
  return left < bEnd && right < aEnd;
}

/**
 * Check an appointment against the ones that already exist.
 *
 * Two things are checked: the provider cannot be in two places at once and
 * the patient cannot be booked twice. An appointment that is cancelled or
 * did not happen does not block anything.
 *
 * Returns an error message, or null when the appointment is fine.
 */
function checkAppointment(appointment, existing, patients) {
  const start = appointment.scheduled_at;
  if (!start || Number.isNaN(Date.parse(start))) {
    return 'The appointment needs a valid date and time.';
  }

  const patientId = Number(appointment.patient_id);
  const provider = String(appointment.provider || '').trim();
  if (!provider) return 'The appointment needs a provider.';

  // The patient has to exist, unless there is no patient list to check
  // against.
  if (Array.isArray(patients)) {
    const patient = patients.find((row) => Number(row.id) === patientId);
    if (!patient) return 'The patient does not exist.';
    if (patient.status && patient.status !== 'active') {
      return `The record of ${patient.name} is ${patient.status}.`;
    }
  }

  const blocking = (existing || []).filter((other) => {
    if (Number(other.id) === Number(appointment.id)) return false;
    return !['cancelled', 'no_show'].includes(String(other.status));
  });

  for (const other of blocking) {
    if (Number(other.patient_id) === patientId) {
      return `This patient already has an appointment on ${other.scheduled_at}.`;
    }
    if (String(other.provider) === provider && overlaps(start, DEFAULT_SLOT_MINUTES, other.scheduled_at, DEFAULT_SLOT_MINUTES)) {
      return `${provider} already has an appointment at ${other.scheduled_at}.`;
    }
  }

  return null;
}

/**
 * Check a prescription before it is written down.
 *
 * The patient has to exist and be active, and the medication and the dose
 * have to be there.
 */
function checkPrescription(prescription, patients) {
  const patientId = Number(prescription.patient_id);
  const patient = (patients || []).find((row) => Number(row.id) === patientId);
  if (!patient) return 'The patient does not exist.';
  if (patient.status && patient.status !== 'active') {
    return `The record of ${patient.name} is ${patient.status}.`;
  }
  if (!String(prescription.medication || '').trim()) return 'The prescription needs a medication.';
  if (!String(prescription.dose || '').trim()) return 'The prescription needs a dose.';
  return null;
}

/**
 * Check a lab order.
 *
 * The patient has to exist and be active, the test has to be named and the
 * priority has to be one of the three the lab knows.
 */
function checkLabOrder(order, patients) {
  const patientId = Number(order.patient_id);
  const patient = (patients || []).find((row) => Number(row.id) === patientId);
  if (!patient) return 'The patient does not exist.';
  if (patient.status && patient.status !== 'active') {
    return `The record of ${patient.name} is ${patient.status}.`;
  }
  if (!String(order.test || '').trim()) return 'The lab order needs a test.';
  if (!isValidPriority(order.priority || 'routine')) {
    return `"${order.priority}" is not a lab priority.`;
  }
  return null;
}

/**
 * The alerts a patient record raises.
 *
 * An allergy without a blood type, or a blood type that is not one the
 * system knows, is a safety problem worth flagging.
 */
function patientAlerts(patient) {
  const alerts = [];
  const allergies = String(patient.allergies || '').trim();

  if (allergies && allergies.toLowerCase() !== 'none' && allergies.toLowerCase() !== 'no known allergies') {
    alerts.push({ level: 'high', text: `Allergies: ${allergies}` });
  }
  if (patient.blood_type && !isValidBloodType(patient.blood_type)) {
    alerts.push({ level: 'medium', text: `"${patient.blood_type}" is not a blood type the system knows.` });
  }
  if (!patient.blood_type) {
    alerts.push({ level: 'low', text: 'No blood type on file.' });
  }
  if (patient.status && patient.status !== 'active') {
    alerts.push({ level: 'medium', text: `The record is ${patient.status}.` });
  }
  return alerts;
}

/**
 * The severity of an incident, and what has to happen because of it.
 */
function severityOf(incident) {
  const severity = String(incident.severity || 'low');
  if (!isValidSeverity(severity)) return 'low';
  return severity;
}

/** What has to be done for an incident of this severity. */
function severityAction(severity) {
  switch (String(severity)) {
    case 'critical':
      return 'Escalate to the duty manager now and open an incident review.';
    case 'high':
      return 'Report to the department lead within the hour.';
    case 'medium':
      return 'Report to the department lead the same day.';
    default:
      return 'Report through the ordinary channel.';
  }
}

/**
 * The clinic diary: the appointments of one day, in order.
 */
function daySchedule(appointments, day) {
  const target = String(day).slice(0, 10);
  return (appointments || [])
    .filter((appointment) => String(appointment.scheduled_at || '').slice(0, 10) === target)
    .filter((appointment) => appointment.status !== 'cancelled')
    .slice()
    .sort((a, b) => Date.parse(a.scheduled_at) - Date.parse(b.scheduled_at));
}

/**
 * The patient's summary: the appointments, the prescriptions and the labs.
 */
function patientSummary(patient, { appointments = [], prescriptions = [], labOrders = [] } = {}) {
  const id = Number(patient.id);
  const own = (rows) => rows.filter((row) => Number(row.patient_id) === id);

  return {
    patient,
    alerts: patientAlerts(patient),
    appointments: own(appointments),
    prescriptions: own(prescriptions),
    lab_orders: own(labOrders),
    active_prescriptions: own(prescriptions).filter((row) => row.status === 'active'),
    pending_labs: own(labOrders).filter((row) => ['ordered', 'collected', 'in_progress'].includes(row.status)),
  };
}

module.exports = {
  PATIENT_STATUSES,
  APPOINTMENT_STATUSES,
  PRESCRIPTION_STATUSES,
  LAB_STATUSES,
  INCIDENT_STATUSES,
  SEVERITIES,
  PRIORITIES,
  BLOOD_TYPES,
  DEFAULT_SLOT_MINUTES,
  isValidPatientStatus,
  isValidAppointmentStatus,
  isValidPrescriptionStatus,
  isValidLabStatus,
  isValidIncidentStatus,
  isValidSeverity,
  isValidPriority,
  isValidBloodType,
  canTransitionLab,
  canTransitionPrescription,
  canTransitionIncident,
  labTransitionError,
  minutesBetween,
  appointmentEnd,
  overlaps,
  checkAppointment,
  checkPrescription,
  checkLabOrder,
  patientAlerts,
  severityOf,
  severityAction,
  daySchedule,
  patientSummary,
};
