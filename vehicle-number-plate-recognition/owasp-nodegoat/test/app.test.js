"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const { createApp } = require("../src/app");
const store = require("../src/store");

async function withServer(run) {
  const server = createApp();
  await new Promise((resolve) => server.listen(0, resolve));
  const base = `http://127.0.0.1:${server.address().port}`;
  try {
    await run(base);
  } finally {
    server.closeAllConnections();
    await new Promise((resolve) => server.close(resolve));
  }
}

test("search returns matching users", async () => {
  await withServer(async (base) => {
    const response = await fetch(`${base}/search?q=ali`);
    const body = await response.json();
    assert.equal(body.results.length, 1);
    assert.equal(body.results[0].username, "alice");
  });
});

test("search injection returns every user", async () => {
  await withServer(async (base) => {
    const query = encodeURIComponent("' OR '1'='1");
    const response = await fetch(`${base}/search?q=${query}`);
    const body = await response.json();
    assert.equal(body.results.length, 3);
  });
});

test("idor exposes another user's record", async () => {
  await withServer(async (base) => {
    const response = await fetch(`${base}/api/users/2`);
    const body = await response.json();
    assert.equal(body.username, "bob");
    assert.equal(body.ssn, "222-22-2222");
  });
});

test("reflected xss is not escaped", async () => {
  await withServer(async (base) => {
    const payload = encodeURIComponent("<script>alert(1)</script>");
    const response = await fetch(`${base}/profile?name=${payload}`);
    const body = await response.text();
    assert.equal(body.includes("<script>alert(1)</script>"), true);
  });
});

test("stored xss is rendered back", async () => {
  await withServer(async (base) => {
    store.reset();
    const response = await fetch(`${base}/comments`, {
      method: "POST",
      headers: { "content-type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({ text: "<img src=x onerror=alert(1)>" }),
    });
    assert.equal(response.status, 201);
    const page = await fetch(`${base}/comments`);
    const body = await page.text();
    assert.equal(body.includes("<img src=x onerror=alert(1)>"), true);
  });
});

test("admin cookie can be set by logging in as admin", async () => {
  await withServer(async (base) => {
    const denied = await fetch(`${base}/admin`);
    assert.equal(denied.status, 403);

    const login = await fetch(`${base}/login`, {
      method: "POST",
      headers: { "content-type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({ username: "admin", password: "admin" }),
      redirect: "manual",
    });
    assert.equal(login.status, 302);
    assert.equal((login.headers.get("set-cookie") || "").includes("role=admin"), true);

    const allowed = await fetch(`${base}/admin`, { headers: { cookie: "role=admin" } });
    assert.equal(allowed.status, 200);
  });
});
