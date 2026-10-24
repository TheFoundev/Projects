import assert from 'node:assert/strict';
import test from 'node:test';

import {
  SETTINGS_KEY,
  clearSettings,
  createMemoryStore,
  loadSettings,
  saveSettings,
} from '../src/settings.ts';

test('the address of the relay is remembered', async () => {
  const store = createMemoryStore();
  assert.equal(await loadSettings(store), null);

  await saveSettings(store, { host: '192.168.1.10:8765' });
  const settings = await loadSettings(store);
  assert.ok(settings);
  assert.equal(settings.host, '192.168.1.10:8765');
});

test('the settings survive a restart of the app', async () => {
  const store = createMemoryStore();
  await saveSettings(store, { host: 'host:1234' });

  const afterRestart = createMemoryStore(store.dump());
  const settings = await loadSettings(afterRestart);
  assert.equal(settings?.host, 'host:1234');
});

test('a corrupt value is ignored instead of breaking the app', async () => {
  const store = createMemoryStore({ [SETTINGS_KEY]: 'not json' });
  assert.equal(await loadSettings(store), null);
});

test('a value without an address is ignored', async () => {
  const store = createMemoryStore({ [SETTINGS_KEY]: JSON.stringify({ other: 1 }) });
  assert.equal(await loadSettings(store), null);
});

test('the settings can be forgotten', async () => {
  const store = createMemoryStore();
  await saveSettings(store, { host: 'host:1234' });
  await clearSettings(store);
  assert.equal(await loadSettings(store), null);
});
