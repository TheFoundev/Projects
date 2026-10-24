"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { createStatusServer } = require("../src/server");
const { openDatabase } = require("../src/db");

async function withServer(run) {
  const file = path.join(fs.mkdtempSync(path.join(os.tmpdir(), "status-api-")), "status.db");
  const store = openDatabase(file);
  const server = createStatusServer(store);
  await new Promise((resolve) => server.listen(0, resolve));
  const base = `http://127.0.0.1:${server.address().port}`;
  try {
    await run(base);
  } finally {
    server.closeAllConnections();
    await new Promise((resolve) => server.close(resolve));
    store.close();
    fs.rmSync(path.dirname(file), { recursive: true, force: true });
  }
}

test("creates a monitor and runs a check", async () => {
  await withServer(async (base) => {
    const created = await fetch(`${base}/api/monitors`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ name: "example", url: "http://127.0.0.1:1/", intervalSeconds: 30 }),
    });
    assert.equal(created.status, 201);
    const { monitor } = await created.json();

    const check = await fetch(`${base}/api/monitors/${monitor.id}/check`, { method: "POST" });
    const checkBody = await check.json();
    assert.equal(check.status, 200);
    assert.equal(checkBody.result.status, "down");

    const checks = await fetch(`${base}/api/monitors/${monitor.id}/checks`);
    assert.equal((await checks.json()).checks.length, 1);

    const listed = await fetch(`${base}/api/monitors`);
    assert.equal((await listed.json()).monitors[0].status, "down");

    const removed = await fetch(`${base}/api/monitors/${monitor.id}`, { method: "DELETE" });
    assert.equal(removed.status, 200);

    const missing = await fetch(`${base}/api/monitors/${monitor.id}`, { method: "DELETE" });
    assert.equal(missing.status, 404);
  });
});

test("serves the dashboard page", async () => {
  await withServer(async (base) => {
    const response = await fetch(`${base}/`);
    const body = await response.text();
    assert.equal(response.status, 200);
    assert.equal(body.includes("Status"), true);
  });
});
