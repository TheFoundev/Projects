'use strict';
const { test } = require('node:test');
const assert = require('node:assert');
const { spawn } = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const ROOT = path.join(__dirname, '..');
const PORT = 3900 + Math.floor(Math.random() * 300);

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

test('health, auth and resource cycle', async () => {
  const dataDir = fs.mkdtempSync(path.join(os.tmpdir(), 'app-test-'));
  const child = spawn(process.execPath, ['server.js'], {
    cwd: ROOT,
    env: { ...process.env, PORT: String(PORT), DATA_DIR: dataDir },
    stdio: ['ignore', 'pipe', 'pipe'],
  });
  try {
    await waitFor(`http://127.0.0.1:${PORT}/api/meta`);
    const meta = await (await fetch(`http://127.0.0.1:${PORT}/api/meta`)).json();
    assert.ok(meta.name);
    assert.ok(Array.isArray(meta.resources));

    const register = await fetch(`http://127.0.0.1:${PORT}/api/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: 'Test Owner', email: 'owner@example.test', password: 'correct-horse' }),
    });
    assert.strictEqual(register.status, 201);
    const cookie = register.headers.get('set-cookie').split(';')[0];

    const first = meta.resources[0];
    const payload = {};
    for (const field of first.fields) {
      if (field.type === 'int' || field.type === 'real') payload[field.name] = 1;
      else if (field.type === 'bool') payload[field.name] = 1;
      else payload[field.name] = 'smoke test';
    }
    const created = await fetch(`http://127.0.0.1:${PORT}/api/${first.name}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Cookie: cookie },
      body: JSON.stringify(payload),
    });
    assert.strictEqual(created.status, 201, await created.text());
    const list = await (await fetch(`http://127.0.0.1:${PORT}/api/${first.name}`)).json();
    assert.ok(list.items.length >= 1);
  } finally {
    child.kill('SIGTERM');
    fs.rmSync(dataDir, { recursive: true, force: true });
  }
});
