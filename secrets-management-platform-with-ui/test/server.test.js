"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { createSecretsServer } = require("../src/server");
const { SecretStore } = require("../src/store");

async function withServer(run) {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), "secrets-api-"));
  const store = new SecretStore(path.join(directory, "secrets.json"), "master");
  const server = createSecretsServer(store, "test-token");
  await new Promise((resolve) => server.listen(0, resolve));
  const base = `http://127.0.0.1:${server.address().port}`;
  try {
    await run(base);
  } finally {
    server.closeAllConnections();
    await new Promise((resolve) => server.close(resolve));
    fs.rmSync(directory, { recursive: true, force: true });
  }
}

test("rejects requests without a token", async () => {
  await withServer(async (base) => {
    const response = await fetch(`${base}/api/secrets`);
    assert.equal(response.status, 401);
  });
});

test("full crud with a valid token", async () => {
  await withServer(async (base) => {
    const headers = { "content-type": "application/json", "x-api-token": "test-token" };
    const created = await fetch(`${base}/api/secrets`, {
      method: "POST",
      headers,
      body: JSON.stringify({ name: "db/password", value: "hunter2" }),
    });
    assert.equal(created.status, 201);

    const listed = await fetch(`${base}/api/secrets`, { headers });
    assert.equal((await listed.json()).secrets.length, 1);

    const read = await fetch(`${base}/api/secrets/db%2Fpassword`, { headers });
    assert.equal((await read.json()).value, "hunter2");

    const audit = await fetch(`${base}/api/audit`, { headers });
    assert.equal((await audit.json()).audit.length >= 1, true);

    const removed = await fetch(`${base}/api/secrets/db%2Fpassword`, { method: "DELETE", headers });
    assert.equal(removed.status, 200);

    const missing = await fetch(`${base}/api/secrets/db%2Fpassword`, { headers });
    assert.equal(missing.status, 404);
  });
});
