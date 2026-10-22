"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const { generateKeyPair, deriveSharedKey, encrypt, decrypt } = require("../src/crypto");

test("both sides derive the same session key", () => {
  const alice = generateKeyPair();
  const bob = generateKeyPair();
  const aliceKey = deriveSharedKey(alice.privateKey, bob.publicKey);
  const bobKey = deriveSharedKey(bob.privateKey, alice.publicKey);
  assert.equal(aliceKey.length, 32);
  assert.equal(aliceKey.equals(bobKey), true);
});

test("encrypt and decrypt round trip", () => {
  const alice = generateKeyPair();
  const bob = generateKeyPair();
  const key = deriveSharedKey(alice.privateKey, bob.publicKey);
  const envelope = encrypt(key, "hello from the other side");
  assert.equal(typeof envelope.iv, "string");
  assert.equal(decrypt(key, envelope), "hello from the other side");
});

test("a tampered tag fails decryption", () => {
  const alice = generateKeyPair();
  const bob = generateKeyPair();
  const key = deriveSharedKey(alice.privateKey, bob.publicKey);
  const envelope = encrypt(key, "important");
  envelope.tag = Buffer.from(envelope.tag, "base64").map((byte, index) => (index === 0 ? byte ^ 0xff : byte)).toString("base64");
  assert.throws(() => decrypt(key, envelope));
});

test("the wrong key cannot decrypt", () => {
  const alice = generateKeyPair();
  const bob = generateKeyPair();
  const mallory = generateKeyPair();
  const aliceKey = deriveSharedKey(alice.privateKey, bob.publicKey);
  const malloryKey = deriveSharedKey(mallory.privateKey, alice.publicKey);
  const envelope = encrypt(aliceKey, "secret");
  assert.throws(() => decrypt(malloryKey, envelope));
});

test("the salt of the key derivation tells two rooms apart", () => {
  const { generateKeyPair, deriveSharedKey, sessionSalt } = require("../src/crypto");
  const alice = generateKeyPair();
  const bob = generateKeyPair();

  const first = deriveSharedKey(alice.privateKey, bob.publicKey, sessionSalt("room-1"));
  const second = deriveSharedKey(alice.privateKey, bob.publicKey, sessionSalt("room-2"));

  assert.equal(first.length, 32);
  // A different room gives a different key.
  assert.notDeepStrictEqual(first, second);
  // The same room gives the same key on both sides.
  const other = deriveSharedKey(bob.privateKey, alice.publicKey, sessionSalt("room-1"));
  assert.deepStrictEqual(first, other);
});

test("a message that is sent again is refused", () => {
  const { encryptWithCounter, decryptWithCounter } = require("../src/crypto");
  const key = Buffer.alloc(32, 7);

  const envelope = encryptWithCounter(key, "hello", 1);
  const opened = decryptWithCounter(key, envelope, 0);
  assert.equal(opened.plaintext, "hello");
  assert.equal(opened.counter, 1);

  // The same message with the same counter is a replay.
  assert.throws(() => decryptWithCounter(key, envelope, 1), /replay/);
});
