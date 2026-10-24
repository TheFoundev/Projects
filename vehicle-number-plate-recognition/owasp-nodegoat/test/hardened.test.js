"use strict";

// The hardened version is turned on before the application is loaded.
process.env.NODEGOAT_HARDENED = "1";

const test = require("node:test");
const assert = require("node:assert");
const { createApp } = require("../src/app");

/** Start the application on a port of its own. */
async function withApp(work) {
  const server = createApp();
  const port = await new Promise((resolve) => {
    server.listen(0, "127.0.0.1", () => resolve(server.address().port));
  });
  try {
    await work(port);
  } finally {
    server.close();
  }
}

test("the hardened version escapes the reflected value", async () => {
  const { createApp } = require("../src/app");
  const server = createApp();
  const port = await new Promise((resolve) => {
    server.listen(0, "127.0.0.1", () => resolve(server.address().port));
  });
  try {
    const response = await fetch(`http://127.0.0.1:${port}/profile?name=${encodeURIComponent("<script>alert(1)</script>")}`);
    const body = await response.text();
    assert.ok(!body.includes("<script>alert(1)</script>"), "the markup has to be escaped");
    assert.ok(body.includes("&lt;script&gt;"));
  } finally {
    server.close();
  }
});

test("the hardened version does not trust the role of the cookie", async () => {
  const { createApp } = require("../src/app");
  const server = createApp();
  const port = await new Promise((resolve) => {
    server.listen(0, "127.0.0.1", () => resolve(server.address().port));
  });
  try {
    const response = await fetch(`http://127.0.0.1:${port}/admin`, {
      headers: { cookie: "role=admin" },
    });
    assert.strictEqual(response.status, 403);
  } finally {
    server.close();
  }
});
