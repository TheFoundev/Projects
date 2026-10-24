import test from 'node:test';
import assert from 'node:assert';

import { MemoryStore } from '../client/lib/store.js';
import { SyncEngine, mergeRow, SYNC_TABLES } from '../client/lib/sync.js';
import { DataLayer } from '../client/lib/data.js';

/** A fake API that records what was pushed and can be made to fail. */
function fakeApi({ server = {}, failPush = false, failPull = false } = {}) {
  const calls = { pull: [], push: [] };
  return {
    calls,
    server,
    async getSyncPull(since) {
      calls.pull.push(since);
      if (failPull) throw new Error('offline');
      return { server_time: '2026-10-20T10:00:00.000Z', since, total: 0, changes: server };
    },
    async postSyncPush(changes) {
      calls.push.push(changes);
      if (failPush) throw new Error('offline');
      const applied = {};
      for (const table of Object.keys(changes)) applied[table] = changes[table].length;
      return { server_time: '2026-10-20T10:00:00.000Z', applied, skipped: {}, errors: [] };
    },
  };
}

test('the mirrored table list matches the server', () => {
  assert.deepEqual(SYNC_TABLES, [
    'accounts', 'category_groups', 'categories', 'transactions',
    'budget_months', 'rules', 'schedules', 'goals',
  ]);
});

test('mergeRow keeps the newer row', () => {
  const older = { id: 1, name: 'old', updated_at: '2026-10-01T00:00:00.000Z' };
  const newer = { id: 1, name: 'new', updated_at: '2026-10-02T00:00:00.000Z' };
  assert.equal(mergeRow(older, newer), newer);
  assert.equal(mergeRow(newer, older), newer);
  assert.equal(mergeRow(null, newer), newer);
  assert.equal(mergeRow(older, null), older);
});

test('a local change is written to the mirror and queued', async () => {
  const store = new MemoryStore();
  const engine = new SyncEngine({ store, api: fakeApi() });

  await engine.applyLocalChange('rules', { id: 7, value: 'coffee', updated_at: '2026-10-20T09:00:00.000Z' });

  const rows = await store.getAll('rules');
  assert.equal(rows.length, 1);
  assert.equal(rows[0].value, 'coffee');
  assert.equal(await engine.pendingCount(), 1);
});

test('a local delete is queued as a soft delete', async () => {
  const store = new MemoryStore();
  const engine = new SyncEngine({ store, api: fakeApi() });

  await engine.applyLocalChange('rules', { id: 7, value: 'coffee', updated_at: '2026-10-20T09:00:00.000Z' });
  await engine.applyLocalDelete('rules', { id: 7, value: 'coffee' });

  const rows = await store.getAll('rules');
  assert.equal(rows[0].deleted, 1);
});

test('push sends the queued rows and empties the queue', async () => {
  const store = new MemoryStore();
  const api = fakeApi();
  const engine = new SyncEngine({ store, api });

  await engine.applyLocalChange('rules', { id: 1, value: 'a', updated_at: '2026-10-20T09:00:00.000Z' });
  await engine.applyLocalChange('goals', { id: 2, target_cents: 100, updated_at: '2026-10-20T09:00:00.000Z' });

  const result = await engine.push();
  assert.equal(result.pushed, 2);
  assert.equal(await engine.pendingCount(), 0);
  assert.equal(Object.keys(api.calls.push[0]).sort().join(','), 'goals,rules');
});

test('a failed push keeps the queue so nothing is lost', async () => {
  const store = new MemoryStore();
  const engine = new SyncEngine({ store, api: fakeApi({ failPush: true }) });

  await engine.applyLocalChange('rules', { id: 1, value: 'a', updated_at: '2026-10-20T09:00:00.000Z' });

  await assert.rejects(() => engine.push());
  assert.equal(await engine.pendingCount(), 1);
});

test('pull merges the server rows into the mirror', async () => {
  const store = new MemoryStore();
  const api = fakeApi({
    server: {
      rules: [{ id: 3, value: 'from server', updated_at: '2026-10-20T08:00:00.000Z' }],
    },
  });
  const engine = new SyncEngine({ store, api });

  const result = await engine.pull();
  assert.equal(result.pulled, 1);

  const rows = await store.getAll('rules');
  assert.equal(rows.length, 1);
  assert.equal(rows[0].value, 'from server');
  assert.equal(await store.getMeta('lastPulledAt'), '2026-10-20T10:00:00.000Z');
});

test('pull does not overwrite a newer local row', async () => {
  const store = new MemoryStore();
  const api = fakeApi({
    server: {
      rules: [{ id: 3, value: 'old server', updated_at: '2026-10-01T00:00:00.000Z' }],
    },
  });
  const engine = new SyncEngine({ store, api });

  await store.putRow('rules', { id: 3, value: 'new local', updated_at: '2026-10-20T08:00:00.000Z' });
  await engine.pull();

  const rows = await store.getAll('rules');
  assert.equal(rows[0].value, 'new local');
});

test('the second pull only asks for what changed since the first', async () => {
  const store = new MemoryStore();
  const api = fakeApi();
  const engine = new SyncEngine({ store, api });

  await engine.pull();
  await engine.pull();

  assert.equal(api.calls.pull[0], '1970-01-01T00:00:00.000Z');
  assert.equal(api.calls.pull[1], '2026-10-20T10:00:00.000Z');
});

test('an offline client does not touch the network', async () => {
  const store = new MemoryStore();
  const api = fakeApi();
  const engine = new SyncEngine({ store, api, isOnline: () => false });

  await engine.applyLocalChange('rules', { id: 1, value: 'a', updated_at: '2026-10-20T09:00:00.000Z' });

  const push = await engine.push();
  const pull = await engine.pull();

  assert.equal(push.offline, true);
  assert.equal(pull.offline, true);
  assert.equal(api.calls.push.length, 0);
  assert.equal(api.calls.pull.length, 0);
  assert.equal(await engine.pendingCount(), 1);
});

test('the data layer falls back to the mirror when the server is down', async () => {
  const store = new MemoryStore();
  const api = {
    async get() { throw new Error('offline'); },
    async post() { throw new Error('offline'); },
    async patch() { throw new Error('offline'); },
    async del() { throw new Error('offline'); },
  };
  const engine = new SyncEngine({ store, api, isOnline: () => false });
  const layer = new DataLayer({ api, engine });

  await store.putRow('rules', { id: 1, value: 'cached', updated_at: '2026-10-20T08:00:00.000Z' });

  const rows = await layer.list('rules');
  assert.equal(rows.length, 1);
  assert.equal(rows[0].value, 'cached');
  assert.equal(layer.isOnline(), false);
});

test('the data layer queues a write made while offline', async () => {
  const store = new MemoryStore();
  const api = {
    async get() { throw new Error('offline'); },
    async post() { throw new Error('offline'); },
  };
  const engine = new SyncEngine({ store, api, isOnline: () => false });
  const layer = new DataLayer({ api, engine });

  await layer.create('rules', { value: 'coffee', field: 'payee', op: 'contains' });

  assert.equal(await engine.pendingCount(), 1);
  const rows = await store.getAll('rules');
  assert.equal(rows[0].value, 'coffee');
});
