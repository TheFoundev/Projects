"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const { createGameServer } = require("../src/server");

test("serves the game page and logic bundle", async () => {
  const server = createGameServer();
  await new Promise((resolve) => server.listen(0, resolve));
  const base = `http://127.0.0.1:${server.address().port}`;
  try {
    const page = await fetch(`${base}/`);
    assert.equal(page.status, 200);
    assert.equal((await page.text()).includes("canvas"), true);

    const logic = await fetch(`${base}/logic.js`);
    assert.equal(logic.status, 200);
    assert.equal((await logic.text()).includes("module.exports"), true);

    const missing = await fetch(`${base}/nope.js`);
    assert.equal(missing.status, 404);
  } finally {
    server.closeAllConnections();
    await new Promise((resolve) => server.close(resolve));
  }
});
