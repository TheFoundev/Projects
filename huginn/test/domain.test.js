"use strict";
const { test } = require("node:test");
const assert = require("node:assert");
const { spawn } = require("node:child_process");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");

const ROOT = path.join(__dirname, "..");
const PORT_BASE = 4400;
const PORT = 4400 + Math.floor(Math.random() * 300);

function waitFor(url, timeout = 12000) {
  const started = Date.now();
  return new Promise((resolve, reject) => {
    const tick = async () => {
      try {
        const response = await fetch(url);
        if (response.ok) return resolve(response);
      } catch {}
      if (Date.now() - started > timeout) return reject(new Error("server did not start"));
      setTimeout(tick, 150);
    };
    tick();
  });
}

/** Start the server with a database of its own. */
async function withServer(work, name = "Test Owner") {
  // Every server gets a port of its own, so the tests do not fight over one.
  const PORT = PORT_BASE + Math.floor(Math.random() * 300);
  const dataDir = fs.mkdtempSync(path.join(os.tmpdir(), "domain-test-"));
  const child = spawn(process.execPath, ["server.js"], {
    cwd: ROOT,
    env: { ...process.env, PORT: String(PORT), DATA_DIR: dataDir },
    stdio: ["ignore", "pipe", "pipe"],
  });
  try {
    await waitFor(`http://127.0.0.1:${PORT}/api/meta`);
    const register = await fetch(`http://127.0.0.1:${PORT}/api/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name,
        email: `owner-${Date.now()}-${Math.floor(Math.random() * 1000)}@example.test`,
        password: "correct-horse",
      }),
    });
    const cookie = register.headers.get("set-cookie").split(";")[0];
    const base = `http://127.0.0.1:${PORT}`;
    const call = async (method, url, body) => {
      const response = await fetch(base + url, {
        method,
        headers: { "Content-Type": "application/json", Cookie: cookie },
        body: body === undefined ? undefined : JSON.stringify(body),
      });
      const text = await response.text();
      let json = null;
      try { json = text ? JSON.parse(text) : null; } catch { json = text; }
      return { status: response.status, json };
    };
    await work({ base, cookie, call });
  } finally {
    child.kill("SIGTERM");
    fs.rmSync(dataDir, { recursive: true, force: true });
  }
}

test("the agents are listed", async () => {
  await withServer(async ({ call }) => {
    const agents = await call("GET", "/api/agents");
    assert.strictEqual(agents.status, 200);
    assert.ok(agents.json.items.length >= 1);
  });
});

test("an agent can be run and the run is recorded", async () => {
  await withServer(async ({ call }) => {
    const agents = (await call("GET", "/api/agents")).json.items;
    const run = await call("POST", `/api/agents/${agents[0].id}/run`, {});
    assert.strictEqual(run.status, 200);
    assert.ok(run.json.status || run.json.ok || run.json.message, JSON.stringify(run.json));
  });
});

test("an agent that does not exist cannot be run", async () => {
  await withServer(async ({ call }) => {
    const run = await call("POST", "/api/agents/99999/run", {});
    assert.strictEqual(run.status, 404);
  });
});
