import assert from 'node:assert/strict';
import test from 'node:test';

import {
  clamp,
  decodeMessage,
  encodeEvent,
  parseEvent,
  relayUrl,
  validateHost,
} from '../src/protocol.ts';

test('a move event needs two numbers', () => {
  const result = parseEvent({ type: 'move', dx: 3, dy: -4 });
  assert.ok(result.ok);
  assert.deepEqual(result.event, { type: 'move', dx: 3, dy: -4 });
});

test('a move without numbers is refused', () => {
  const result = parseEvent({ type: 'move', dx: '3', dy: 4 });
  assert.ok(!result.ok);
  assert.match(result.error, /dx and dy/);
});

test('an unknown event type is refused', () => {
  const result = parseEvent({ type: 'launch', dx: 1 });
  assert.ok(!result.ok);
  assert.match(result.error, /unknown event type/);
});

test('a message that is not an object is refused', () => {
  assert.ok(!parseEvent('move').ok);
  assert.ok(!parseEvent(null).ok);
  assert.ok(!parseEvent([1, 2]).ok);
});

test('a click keeps its button and defaults to the left one', () => {
  const right = parseEvent({ type: 'click', button: 'right' });
  assert.ok(right.ok);
  assert.deepEqual(right.event, { type: 'click', button: 'right' });

  const plain = parseEvent({ type: 'click' });
  assert.ok(plain.ok);
  assert.deepEqual(plain.event, { type: 'click', button: 'left' });

  const middle = parseEvent({ type: 'click', button: 'middle' });
  assert.ok(!middle.ok);
});

test('a scroll needs a number and a text needs a string', () => {
  assert.ok(!parseEvent({ type: 'scroll', dy: 'up' }).ok);
  assert.ok(!parseEvent({ type: 'text', text: 42 }).ok);

  const text = parseEvent({ type: 'text', text: 'hello' });
  assert.ok(text.ok);
  assert.deepEqual(text.event, { type: 'text', text: 'hello' });
});

test('text that is too long is refused', () => {
  const result = parseEvent({ type: 'text', text: 'x'.repeat(5000) });
  assert.ok(!result.ok);
  assert.match(result.error, /too long/);
});

test('a key is lowercased and must have a name', () => {
  const key = parseEvent({ type: 'key', key: 'Enter' });
  assert.ok(key.ok);
  assert.deepEqual(key.event, { type: 'key', key: 'enter' });

  assert.ok(!parseEvent({ type: 'key', key: '' }).ok);
  assert.ok(!parseEvent({ type: 'key' }).ok);
});

test('an event is encoded as JSON and decoded again', () => {
  const event = { type: 'move', dx: 1, dy: 2 } as const;
  const wire = encodeEvent(event);
  assert.equal(wire, '{"type":"move","dx":1,"dy":2}');

  const decoded = decodeMessage(wire);
  assert.ok(decoded.ok);
  assert.deepEqual(decoded.event, event);
});

test('a message that is not JSON is refused', () => {
  const result = decodeMessage('{oops');
  assert.ok(!result.ok);
  assert.match(result.error, /not valid JSON/);
});

test('the movement is clamped and rounded', () => {
  assert.equal(clamp(3.4), 3);
  assert.equal(clamp(-3.6), -4);
  assert.equal(clamp(100000), 2000);
  assert.equal(clamp(-100000), -2000);
});

test('the address of the relay becomes a websocket URL', () => {
  assert.equal(relayUrl('192.168.1.10:8765'), 'ws://192.168.1.10:8765');
  assert.equal(relayUrl(' ws://host:1234 '), 'ws://host:1234');
  assert.equal(relayUrl('wss://host'), 'wss://host');
});

test('the address is checked before the connection is opened', () => {
  assert.equal(validateHost('192.168.1.10:8765'), null);
  assert.equal(validateHost('ws://host:1234'), null);
  assert.match(validateHost('') ?? '', /Enter the address/);
  assert.match(validateHost('ws://') ?? '', /not a valid address/);
});
