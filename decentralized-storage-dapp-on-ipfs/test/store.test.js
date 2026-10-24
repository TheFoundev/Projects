"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { createStore } = require("../src/store");

test("stores and returns content by cid", () => {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), "store-"));
  const store = createStore(directory);
  const cid = store.add("hello ipfs");
  assert.equal(store.has(cid), true);
  assert.equal(store.get(cid).toString("utf8"), "hello ipfs");
  assert.equal(store.list().length, 1);
  fs.rmSync(directory, { recursive: true, force: true });
});

test("adding the same content returns the same cid", () => {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), "store-"));
  const store = createStore(directory);
  const first = store.add("same");
  const second = store.add("same");
  assert.equal(first, second);
  assert.equal(store.list().length, 1);
  fs.rmSync(directory, { recursive: true, force: true });
});

test("unknown cid returns null", () => {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), "store-"));
  const store = createStore(directory);
  const cid = store.add("present");
  const missing = "b" + "a".repeat(58);
  assert.equal(store.get(missing), null);
  assert.equal(store.has(cid), true);
  fs.rmSync(directory, { recursive: true, force: true });
});
