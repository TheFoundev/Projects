import test from 'node:test';
import assert from 'node:assert';

import {
  SimulatedExposureService,
  assessSymptoms,
  formatCheckStamp,
  lastCheck,
  nextCheckDue,
  toCheck,
  DISCLAIMER,
  type Check,
} from '../src/exposure.ts';
import { CheckStore, createMemoryStore } from '../src/store.ts';

test('a simulated check with no matches comes back clear', async () => {
  const service = new SimulatedExposureService(0, () => new Date('2026-04-23T08:10:00Z'));
  const result = await service.check();

  assert.equal(result.status, 'clear');
  assert.equal(result.source, 'simulated');
  assert.match(result.detail, /No matching codes/);
});

test('a simulated check with a match comes back exposed', async () => {
  const service = new SimulatedExposureService(2, () => new Date('2026-04-23T08:10:00Z'));
  const result = await service.check();

  assert.equal(result.status, 'exposed');
  assert.match(result.detail, /2 matching codes/);
});

test('one matching code is written in the singular', async () => {
  const service = new SimulatedExposureService(1);
  const result = await service.check();
  assert.match(result.detail, /1 matching code in/);
});

test('a check is turned into a history row', async () => {
  const service = new SimulatedExposureService(0, () => new Date('2026-04-23T08:10:00Z'));
  const check = toCheck(await service.check(), 'c-1');

  assert.equal(check.id, 'c-1');
  assert.equal(check.result, 'clear');
  assert.equal(check.source, 'simulated');
  assert.ok(check.date.length > 0);
});

test('the last check is the first one in the history', () => {
  const checks: Check[] = [
    { id: 'a', date: 'Apr 23, 08:10', checkedAt: '2026-04-23T08:10:00.000Z', result: 'clear', note: '', source: 'simulated' },
    { id: 'b', date: 'Apr 20, 19:42', checkedAt: '2026-04-20T19:42:00.000Z', result: 'clear', note: '', source: 'simulated' },
  ];
  assert.equal(lastCheck(checks)?.id, 'a');
  assert.equal(lastCheck([]), null);
});

test('the next check is due in a day after a fresh check', () => {
  const checks: Check[] = [
    { id: 'a', date: 'now', checkedAt: new Date().toISOString(), result: 'clear', note: '', source: 'simulated' },
  ];
  const due = nextCheckDue(checks, 1);
  assert.ok(due !== null);
  assert.ok(due! >= 0 && due! <= 1);
});

test('an old check means the next check is already due', () => {
  const checks: Check[] = [{ id: 'a', date: 'Jan 01, 08:10', checkedAt: '2026-01-01T08:10:00.000Z', result: 'clear', note: '', source: 'simulated' }];
  assert.equal(nextCheckDue(checks, 1), null);
});

test('without a check there is nothing due', () => {
  assert.equal(nextCheckDue([], 1), null);
});

test('the symptom score adds up the weights', () => {
  assert.equal(assessSymptoms([]).score, 0);
  assert.equal(assessSymptoms(['fever']).score, 3);
  assert.equal(assessSymptoms(['fever', 'cough']).score, 5);
  assert.equal(assessSymptoms(['throat', 'fatigue']).score, 2);
});

test('the risk level follows the score', () => {
  assert.equal(assessSymptoms([]).level, 'low');
  assert.equal(assessSymptoms(['throat']).level, 'low');
  assert.equal(assessSymptoms(['throat', 'fatigue']).level, 'moderate');
  assert.equal(assessSymptoms(['cough', 'taste']).level, 'high');
  assert.equal(assessSymptoms(['fever']).level, 'high');
  assert.equal(assessSymptoms(['breath']).level, 'high');
});

test('a symptom that is not ticked twice is only counted once', () => {
  assert.equal(assessSymptoms(['fever', 'fever']).score, 3);
});

test('an unknown symptom does not change the score', () => {
  assert.equal(assessSymptoms(['not-a-symptom']).score, 0);
});

test('every assessment comes with advice', () => {
  for (const symptoms of [[], ['cough'], ['fever']]) {
    assert.ok(assessSymptoms(symptoms).advice.length > 10);
  }
  assert.ok(DISCLAIMER.length > 10);
});

test('the stamp is formatted the way the history shows it', () => {
  const stamp = formatCheckStamp(new Date(2026, 3, 23, 8, 10));
  assert.match(stamp, /Apr 23, 08:10/);
});

// ---------------------------------------------------------------------------
// Persistence
// ---------------------------------------------------------------------------

test('the check history round-trips', async () => {
  const store = new CheckStore(createMemoryStore());
  const checks: Check[] = [{ id: 'a', date: 'Apr 23, 08:10', checkedAt: '2026-04-23T08:10:00.000Z', result: 'clear', note: 'fine', source: 'simulated' }];

  await store.save(checks);
  const loaded = await store.load();

  assert.equal(loaded.length, 1);
  assert.equal(loaded[0].id, 'a');
  assert.equal(loaded[0].result, 'clear');
});

test('an empty history is returned when nothing was saved', async () => {
  const store = new CheckStore(createMemoryStore());
  assert.deepEqual(await store.load(), []);
});

test('a corrupt saved value gives an empty history', async () => {
  const backend = createMemoryStore();
  await backend.setItem('covid-alert.checks.v1', 'not json');
  const store = new CheckStore(backend);

  assert.deepEqual(await store.load(), []);
});

test('rows that are not checks are dropped', async () => {
  const backend = createMemoryStore();
  await backend.setItem(
    'covid-alert.checks.v1',
    JSON.stringify([{ id: 'a', result: 'clear' }, { nope: true }, 'string']),
  );
  const store = new CheckStore(backend);

  const loaded = await store.load();
  assert.equal(loaded.length, 1);
  assert.equal(loaded[0].id, 'a');
});

test('the store keeps working when the backend fails', async () => {
  const failing = {
    async getItem() { throw new Error('storage unavailable'); },
    async setItem() { throw new Error('storage unavailable'); },
    async removeItem() { throw new Error('storage unavailable'); },
  };
  const store = new CheckStore(failing);

  assert.deepEqual(await store.load(), []);
  assert.equal(await store.save([]), false);
});

test('the history can be cleared', async () => {
  const store = new CheckStore(createMemoryStore());
  await store.save([{ id: 'a', date: 'x', checkedAt: '2026-04-23T08:10:00.000Z', result: 'clear', note: '', source: 'simulated' }]);
  await store.clear();

  assert.deepEqual(await store.load(), []);
});
