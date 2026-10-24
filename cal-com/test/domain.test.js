"use strict";
const { test } = require("node:test");
const assert = require("node:assert");
const { spawn } = require("node:child_process");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");

const ROOT = path.join(__dirname, "..");
const PORT_BASE = 4100;
const PORT = 4100 + Math.floor(Math.random() * 300);

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

test("the availability of an event type holds the slots of the day", async () => {
  await withServer(async ({ base, call }) => {
    const answer = await call("GET", "/api/availability?slug=intro-call&date=2026-05-04");
    assert.strictEqual(answer.status, 200);
    assert.ok(Array.isArray(answer.json.slots));
    assert.ok(answer.json.slots.length > 0);
    assert.ok(answer.json.event);
  });
});

test("the availability of an event type that does not exist is an error", async () => {
  await withServer(async ({ call }) => {
    const answer = await call("GET", "/api/availability?slug=nope&date=2026-05-04");
    assert.strictEqual(answer.status, 404);
  });
});

test("the calendar of the bookings is a calendar", async () => {
  await withServer(async ({ call }) => {
    const answer = await call("GET", "/api/bookings.ics");
    assert.strictEqual(answer.status, 200);
    assert.ok(answer.json.startsWith("BEGIN:VCALENDAR"));
    assert.ok(answer.json.includes("END:VCALENDAR"));
  });
});

test("a booking needs an address", async () => {
  await withServer(async ({ call }) => {
    const answer = await call("POST", "/api/bookings", { event_type_id: 1, email: "not-an-email", start_at: "2026-05-04T10:00:00Z" });
    assert.strictEqual(answer.status, 400);
  });
});
