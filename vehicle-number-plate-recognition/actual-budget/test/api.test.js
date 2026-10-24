import test from 'node:test';
import assert from 'node:assert';

import { openDatabase } from '../server/db.js';
import { createServer } from '../server/index.js';
import { seed } from '../server/seed.js';

/** Start a server on an ephemeral port with a seeded database. */
async function startServer() {
  const db = openDatabase(':memory:');
  seed(db);
  const server = createServer({ db });
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  const base = `http://127.0.0.1:${server.address().port}`;
  return { db, server, base };
}

/** Call the API and return the JSON body. */
async function call(base, method, path, body) {
  const response = await fetch(base + path, {
    method,
    headers: { 'content-type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const text = await response.text();
  let json = null;
  try { json = text ? JSON.parse(text) : null; } catch { json = text; }
  return { status: response.status, json };
}

test('the rules endpoint creates, lists, updates and deletes a rule', async () => {
  const { db, server, base } = await startServer();

  const created = await call(base, 'POST', '/api/rules', {
    priority: 5, field: 'payee', op: 'contains', value: 'coffee', set_category_id: 1, enabled: 1,
  });
  assert.equal(created.status, 200);
  assert.equal(created.json.data.value, 'coffee');
  const id = created.json.data.id;

  const listed = await call(base, 'GET', '/api/rules');
  assert.ok(listed.json.data.some((rule) => rule.id === id));

  const updated = await call(base, 'PATCH', `/api/rules/${id}`, { value: 'tea' });
  assert.equal(updated.json.data.value, 'tea');

  const removed = await call(base, 'DELETE', `/api/rules/${id}`);
  assert.equal(removed.json.data.deleted, true);

  const after = await call(base, 'GET', '/api/rules');
  assert.ok(!after.json.data.some((rule) => rule.id === id));

  db.close();
  server.close();
  server.closeAllConnections?.();
});

test('a rule with an unknown field is rejected', async () => {
  const { db, server, base } = await startServer();
  const result = await call(base, 'POST', '/api/rules', { field: 'nope', op: 'contains', value: 'x' });
  assert.equal(result.status, 400);
  db.close();
  server.close();
  server.closeAllConnections?.();
});

test('the schedules endpoint stores a recurring transaction', async () => {
  const { db, server, base } = await startServer();

  const created = await call(base, 'POST', '/api/schedules', {
    account_id: 1, payee: 'Rent', amount_cents: -120000, frequency: 'monthly',
    interval_n: 1, next_date: '2026-11-01',
  });
  assert.equal(created.status, 200);
  assert.equal(created.json.data.frequency, 'monthly');
  assert.equal(created.json.data.amount_cents, -120000);

  const listed = await call(base, 'GET', '/api/schedules');
  assert.equal(listed.json.data.length >= 1, true);

  db.close();
  server.close();
  server.closeAllConnections?.();
});

test('the goals endpoint stores a target for a category', async () => {
  const { db, server, base } = await startServer();

  const created = await call(base, 'POST', '/api/goals', {
    category_id: 1, target_cents: 500000, monthly_cents: 25000, target_date: '2027-01-01',
  });
  assert.equal(created.status, 200);
  assert.equal(created.json.data.target_cents, 500000);

  const listed = await call(base, 'GET', '/api/goals');
  assert.equal(listed.json.data.length >= 1, true);

  db.close();
  server.close();
  server.closeAllConnections?.();
});

test('a CSV import categorises rows and skips duplicates', async () => {
  const { db, server, base } = await startServer();

  const csv = [
    'date,payee,amount',
    '2026-10-01,Coffee Shop,-4.50',
    '2026-10-02,Book Store,-12.00',
  ].join('\n');

  const first = await call(base, 'POST', '/api/import/csv', { account_id: 1, csv });
  assert.equal(first.status, 200);
  assert.equal(first.json.data.rows_found, 2);
  assert.equal(first.json.data.imported, 2);
  assert.equal(first.json.data.duplicates, 0);

  const second = await call(base, 'POST', '/api/import/csv', { account_id: 1, csv });
  assert.equal(second.json.data.imported, 0);
  assert.equal(second.json.data.duplicates, 2);

  db.close();
  server.close();
  server.closeAllConnections?.();
});

test('a CSV import can run as a dry run', async () => {
  const { db, server, base } = await startServer();

  const csv = 'date,payee,amount\n2026-10-01,Coffee,-4.50';
  const preview = await call(base, 'POST', '/api/import/csv', { account_id: 1, csv, dry_run: true });
  assert.equal(preview.json.data.dry_run, true);
  assert.equal(preview.json.data.imported, 0);
  assert.equal(preview.json.data.transactions.length, 1);

  db.close();
  server.close();
  server.closeAllConnections?.();
});

test('the import rejects a CSV without a date column', async () => {
  const { db, server, base } = await startServer();
  const result = await call(base, 'POST', '/api/import/csv', { account_id: 1, csv: 'payee,amount\nx,-1' });
  assert.equal(result.status, 400);
  db.close();
  server.close();
  server.closeAllConnections?.();
});

test('the reports endpoints return a net worth, cash flow and spending series', async () => {
  const { db, server, base } = await startServer();

  const networth = await call(base, 'GET', '/api/reports/networth?months=6');
  assert.equal(networth.status, 200);
  assert.equal(networth.json.data.series.length, 6);
  assert.ok(typeof networth.json.data.series[0].net === 'number');

  const cashflow = await call(base, 'GET', '/api/reports/cashflow?months=6');
  assert.equal(cashflow.json.data.series.length, 6);
  assert.ok(typeof cashflow.json.data.series[0].net === 'number');

  const spending = await call(base, 'GET', '/api/reports/spending');
  assert.ok(Array.isArray(spending.json.data.categories));
  assert.ok(typeof spending.json.data.total === 'number');

  db.close();
  server.close();
  server.closeAllConnections?.();
});

test('a transaction can be created, categorised and deleted', async () => {
  const { db, server, base } = await startServer();

  const created = await call(base, 'POST', '/api/transactions', {
    account_id: 1, date: '2026-10-05', payee: 'Train ticket', amount_cents: -1250, category_id: null,
  });
  assert.equal(created.status, 200);
  const id = created.json.data.transaction.id;

  const categorised = await call(base, 'PATCH', `/api/transactions/${id}`, { category_id: 2 });
  assert.equal(categorised.json.data.transaction.category_id, 2);

  const removed = await call(base, 'DELETE', `/api/transactions/${id}`);
  assert.equal(removed.json.data.deleted, true);

  db.close();
  server.close();
  server.closeAllConnections?.();
});

test('sync pushes queued rows and pulls them back', async () => {
  const { db, server, base } = await startServer();

  const pushed = await call(base, 'POST', '/api/sync/push', {
    changes: {
      rules: [{
        id: 900, priority: 1, field: 'payee', op: 'contains', value: 'pushed',
        set_category_id: 1, enabled: 1, updated_at: '2026-10-20T09:00:00.000Z', deleted: 0,
      }],
    },
  });
  assert.equal(pushed.status, 200);
  assert.equal(pushed.json.data.applied.rules, 1);

  const pulled = await call(base, 'GET', '/api/sync/pull?since=1970-01-01T00:00:00.000Z');
  const rules = pulled.json.data.changes.rules;
  assert.ok(rules.some((rule) => rule.value === 'pushed'));

  db.close();
  server.close();
  server.closeAllConnections?.();
});

test('sync rejects an unknown table', async () => {
  const { db, server, base } = await startServer();
  const result = await call(base, 'POST', '/api/sync/push', { changes: { nonsense: [] } });
  assert.equal(result.status, 200);
  assert.equal(result.json.data.errors.length, 1);
  db.close();
  server.close();
  server.closeAllConnections?.();
});
