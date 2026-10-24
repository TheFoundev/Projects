"use strict";
const { test } = require("node:test");
const assert = require("node:assert");
const { spawn } = require("node:child_process");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");

const ROOT = path.join(__dirname, "..");
const PORT_BASE = 4300;
const PORT = 4300 + Math.floor(Math.random() * 300);

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

test("the storefront holds the products", async () => {
  await withServer(async ({ call }) => {
    const shop = await call("GET", "/api/products");
    assert.strictEqual(shop.status, 200);
    assert.ok(shop.json.items.length >= 1);
    assert.ok(shop.json.items[0].price_cents >= 0);
  });
});

test("a cart is priced and a checkout gives an order", async () => {
  await withServer(async ({ call }) => {
    const shop = (await call("GET", "/api/products")).json;
    const product = shop.items[0];
    const order = await call("POST", "/api/checkout", {
      email: "buyer@example.test",
      items: [{ product_id: product.id, quantity: 2 }],
    });
    assert.strictEqual(order.status, 201, JSON.stringify(order.json));
    assert.ok(order.json.order_id);
    assert.ok(order.json.total_cents > 0);
  });
});

test("an empty cart cannot be checked out", async () => {
  await withServer(async ({ call }) => {
    const order = await call("POST", "/api/checkout", { email: "buyer@example.test", items: [] });
    assert.strictEqual(order.status, 400);
  });
});

test("an address without an @ is refused", async () => {
  await withServer(async ({ call }) => {
    const shop = (await call("GET", "/api/products")).json;
    const order = await call("POST", "/api/checkout", {
      email: "not-an-email",
      items: [{ product_id: shop.items[0].id, quantity: 1 }],
    });
    assert.strictEqual(order.status, 400);
  });
});

test("more than there is cannot be ordered", async () => {
  await withServer(async ({ call }) => {
    const shop = (await call("GET", "/api/products")).json;
    const order = await call("POST", "/api/checkout", {
      email: "buyer@example.test",
      items: [{ product_id: shop.items[0].id, quantity: 9999 }],
    });
    assert.strictEqual(order.status, 409);
  });
});
