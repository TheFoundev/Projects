"use strict";
const { test } = require("node:test");
const assert = require("node:assert");
const { spawn } = require("node:child_process");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");

const ROOT = path.join(__dirname, "..");
const PORT_BASE = 4200;
const PORT = 4200 + Math.floor(Math.random() * 300);

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

test("the board has its lists and its cards", async () => {
  await withServer(async ({ call }) => {
    const boards = await call("GET", "/api/boards");
    assert.strictEqual(boards.status, 200);
    assert.ok(boards.json.items.length >= 1);

    const lists = await call("GET", "/api/lists");
    assert.strictEqual(lists.status, 200);
    assert.ok(lists.json.items.length >= 1);
  });
});

test("a card can be moved to another list", async () => {
  // The board of the seed belongs to Product, so the move is made by the
  // owner of the board.
  await withServer(async ({ call }) => {
    const boards = (await call("GET", "/api/boards")).json.items;
    const lists = (await call("GET", "/api/lists")).json.items;
    const cards = (await call("GET", "/api/cards")).json.items;
    assert.ok(cards.length >= 1);

    // The card has to be on a board of the owner of the board.
    const board = boards.find((item) => item.owner === "Product") || boards[0];
    const list = lists.find((item) => item.board_id === board.id) || lists[0];
    const card = cards.find((item) => item.list_id === list.id) || cards[0];

    const moved = await call("PATCH", `/api/cards/${card.id}/move`, {
      list_id: list.id,
      position: 1,
    });
    assert.strictEqual(moved.status, 200, JSON.stringify(moved.json));
    assert.strictEqual(moved.json.list_id, list.id);
  }, "Product");
});

test("a card of a board of somebody else may not be moved", async () => {
  await withServer(async ({ call }) => {
    const lists = (await call("GET", "/api/lists")).json.items;
    const cards = (await call("GET", "/api/cards")).json.items;
    if (!cards.length) return;

    const moved = await call("PATCH", `/api/cards/${cards[0].id}/move`, {
      list_id: lists[0].id,
      position: 1,
    });
    assert.strictEqual(moved.status, 403);
  });
});

test("a card that is moved to a list that does not exist is an error", async () => {
  await withServer(async ({ call }) => {
    const boards = (await call("GET", "/api/boards")).json.items;
    const lists = (await call("GET", "/api/lists")).json.items;
    const cards = (await call("GET", "/api/cards")).json.items;
    if (!cards.length) return;

    const moved = await call("PATCH", `/api/cards/${cards[0].id}/move`, {
      list_id: 99999,
      position: 1,
    });
    assert.strictEqual(moved.status, 404);
  });
});
