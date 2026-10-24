"use strict";
const { test } = require("node:test");
const assert = require("node:assert");
const { spawn } = require("node:child_process");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");

const ROOT = path.join(__dirname, "..");
const PORT_BASE = 4500;
const PORT = 4500 + Math.floor(Math.random() * 300);

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

test("the channels are listed", async () => {
  await withServer(async ({ call }) => {
    const channels = await call("GET", "/api/channels");
    assert.strictEqual(channels.status, 200);
    assert.ok(channels.json.items.length >= 1);
  });
});

test("a message can be sent and read back", async () => {
  await withServer(async ({ call }) => {
    const channels = (await call("GET", "/api/channels")).json.items;
    const sent = await call("POST", "/api/messages", {
      channel_id: channels[0].id,
      author: "Test Owner",
      body: "hello from the test",
    });
    assert.strictEqual(sent.status, 201, JSON.stringify(sent.json));

    const list = await call("GET", "/api/messages");
    assert.strictEqual(list.status, 200);
    assert.ok(list.json.items.length >= 1);
    assert.ok(list.json.items.some((message) => message.body === "hello from the test"));
  });
});

test("a message without a body is refused", async () => {
  await withServer(async ({ call }) => {
    const channels = (await call("GET", "/api/channels")).json.items;
    const sent = await call("POST", "/api/messages", { channel_id: channels[0].id, body: "  " });
    assert.strictEqual(sent.status, 400);
  });
});

test("the stream of the events answers", async () => {
  await withServer(async ({ base }) => {
    const response = await fetch(`${base}/api/stream`);
    assert.strictEqual(response.status, 200);
    assert.ok(response.headers.get("content-type").includes("text/event-stream"));
    response.body.cancel();
  });
});
