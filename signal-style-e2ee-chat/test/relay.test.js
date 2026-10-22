"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const { createChatServer } = require("../src/server");
const { generateKeyPair, deriveSharedKey, encrypt, decrypt } = require("../src/crypto");

function open(socket) {
  return new Promise((resolve, reject) => {
    socket.addEventListener("open", () => resolve(), { once: true });
    socket.addEventListener("error", () => reject(new Error("websocket failed")), { once: true });
  });
}

function nextMessage(socket) {
  return new Promise((resolve, reject) => {
    socket.addEventListener(
      "message",
      (event) => {
        try {
          resolve(JSON.parse(event.data));
        } catch (error) {
          reject(error);
        }
      },
      { once: true },
    );
  });
}

test("serves the client page", async () => {
  const server = createChatServer();
  await new Promise((resolve) => server.listen(0, resolve));
  const base = `http://127.0.0.1:${server.address().port}`;
  try {
    const response = await fetch(`${base}/`);
    const body = await response.text();
    assert.equal(response.status, 200);
    assert.equal(body.includes("Signal-style chat demo"), true);
  } finally {
    server.closeAllConnections();
    await new Promise((resolve) => server.close(resolve));
  }
});

test("relays an opaque envelope between two clients", async () => {
  const server = createChatServer();
  await new Promise((resolve) => server.listen(0, resolve));
  const port = server.address().port;
  const alice = new WebSocket(`ws://127.0.0.1:${port}`);
  const bob = new WebSocket(`ws://127.0.0.1:${port}`);
  try {
    await Promise.all([open(alice), open(bob)]);

    const aliceKeys = generateKeyPair();
    const bobKeys = generateKeyPair();
    const aliceKey = deriveSharedKey(aliceKeys.privateKey, bobKeys.publicKey);
    const bobKey = deriveSharedKey(bobKeys.privateKey, aliceKeys.publicKey);
    assert.equal(aliceKey.equals(bobKey), true);

    const received = nextMessage(bob);
    alice.send(JSON.stringify({ type: "message", name: "alice", payload: encrypt(aliceKey, "hello bob") }));
    const message = await received;
    assert.equal(message.type, "message");
    assert.equal(message.name, "alice");
    assert.equal(decrypt(bobKey, message.payload), "hello bob");
  } finally {
    alice.close();
    bob.close();
    server.closeAllConnections();
    await new Promise((resolve) => server.close(resolve));
  }
});
