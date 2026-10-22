"use strict";

const crypto = require("node:crypto");

const ALGORITHM = "aes-256-gcm";
const INFO = "signal-style-chat-v1";

function generateKeyPair() {
  const { publicKey, privateKey } = crypto.generateKeyPairSync("x25519");
  return {
    publicKey: publicKey.export({ type: "spki", format: "der" }).toString("base64"),
    privateKey: privateKey.export({ type: "pkcs8", format: "der" }).toString("base64"),
  };
}

function toPublicKey(base64) {
  return crypto.createPublicKey({ key: Buffer.from(base64, "base64"), format: "der", type: "spki" });
}

function toPrivateKey(base64) {
  return crypto.createPrivateKey({ key: Buffer.from(base64, "base64"), format: "der", type: "pkcs8" });
}

function deriveSharedKey(privateKeyBase64, publicKeyBase64, salt) {
  const secret = crypto.diffieHellman({
    privateKey: toPrivateKey(privateKeyBase64),
    publicKey: toPublicKey(publicKeyBase64),
  });
  // The salt is what tells two sessions apart. Both sides have to use the
  // same one, so it is derived from the room and not made up on the spot.
  const used = salt === undefined ? sessionSalt("default") : salt;
  return Buffer.from(crypto.hkdfSync("sha256", secret, used, INFO, 32));
}

/**
 * The salt of a room.
 *
 * Both sides of a room derive the same salt from its name, so they come to
 * the same key without having to send it.
 */
function sessionSalt(roomId) {
  return crypto.createHash("sha256").update(String(roomId)).digest();
}

/**
 * Encrypt a message with a counter.
 *
 * The counter is part of the data that is authenticated, so a message that
 * is sent again with the same number is refused.
 */
function encryptWithCounter(key, plaintext, counter) {
  const iv = crypto.randomBytes(12);
  const cipher = crypto.createCipheriv(ALGORITHM, key, iv);
  const header = Buffer.alloc(8);
  header.writeBigUInt64BE(BigInt(counter));
  cipher.setAAD(header);
  const ciphertext = Buffer.concat([cipher.update(String(plaintext), "utf8"), cipher.final()]);
  return {
    iv: iv.toString("base64"),
    ciphertext: ciphertext.toString("base64"),
    tag: cipher.getAuthTag().toString("base64"),
    counter: String(counter),
  };
}

/**
 * Open a message and check its counter.
 *
 * The counter has to be bigger than the last one that was seen, or the
 * message is a replay.
 */
function decryptWithCounter(key, envelope, lastCounter) {
  const iv = Buffer.from(envelope.iv, "base64");
  const decipher = crypto.createDecipheriv(ALGORITHM, key, iv);
  decipher.setAuthTag(Buffer.from(envelope.tag, "base64"));
  const header = Buffer.alloc(8);
  header.writeBigUInt64BE(BigInt(envelope.counter || 0));
  decipher.setAAD(header);
  const plaintext = Buffer.concat([
    decipher.update(Buffer.from(envelope.ciphertext, "base64")),
    decipher.final(),
  ]).toString("utf8");

  const counter = Number(envelope.counter || 0);
  if (lastCounter !== undefined && counter <= lastCounter) {
    throw new Error("the message is a replay");
  }
  return { plaintext, counter };
}

function encrypt(key, plaintext) {
  const iv = crypto.randomBytes(12);
  const cipher = crypto.createCipheriv(ALGORITHM, key, iv);
  const ciphertext = Buffer.concat([cipher.update(plaintext, "utf8"), cipher.final()]);
  return {
    iv: iv.toString("base64"),
    ciphertext: ciphertext.toString("base64"),
    tag: cipher.getAuthTag().toString("base64"),
  };
}

function decrypt(key, envelope) {
  const iv = Buffer.from(envelope.iv, "base64");
  const ciphertext = Buffer.from(envelope.ciphertext, "base64");
  const tag = Buffer.from(envelope.tag, "base64");
  const decipher = crypto.createDecipheriv(ALGORITHM, key, iv);
  decipher.setAuthTag(tag);
  return Buffer.concat([decipher.update(ciphertext), decipher.final()]).toString("utf8");
}

module.exports = {
  generateKeyPair,
  deriveSharedKey,
  sessionSalt,
  encrypt,
  decrypt,
  encryptWithCounter,
  decryptWithCounter,
};
