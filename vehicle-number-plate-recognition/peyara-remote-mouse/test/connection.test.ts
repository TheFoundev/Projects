import assert from 'node:assert/strict';
import test from 'node:test';

import { RelayConnection, backoffDelay, type SocketLike } from '../src/connection.ts';

type FakeSocket = SocketLike & {
  sent: string[];
  closed: boolean;
  open(): void;
  drop(): void;
  fail(): void;
};

function fakeSocket(): FakeSocket {
  const socket: FakeSocket = {
    readyState: 0,
    sent: [],
    closed: false,
    send(data: string) {
      socket.sent.push(data);
    },
    close() {
      socket.closed = true;
      socket.readyState = 3;
    },
    onopen: null,
    onclose: null,
    onerror: null,
    onmessage: null,
    open() {
      socket.readyState = 1;
      socket.onopen?.();
    },
    drop() {
      socket.readyState = 3;
      socket.onclose?.();
    },
    fail() {
      socket.readyState = 3;
      socket.onerror?.();
    },
  };
  return socket;
}

/** A timer the test drives by hand. */
function fakeTimers() {
  const pending: { delay: number; handler: () => void }[] = [];
  const scheduled: number[] = [];
  return {
    timers: {
      setTimeout(handler: () => void, delay: number) {
        pending.push({ delay, handler });
        scheduled.push(delay);
        return pending.length - 1;
      },
      clearTimeout(handle: unknown) {
        pending[handle as number] = { delay: 0, handler: () => {} };
      },
    },
    get delays() {
      return scheduled;
    },
    runNext() {
      const next = pending.shift();
      next?.handler();
      return next;
    },
    get count() {
      return pending.length;
    },
  };
}

test('the delay grows with every try and never past the maximum', () => {
  assert.equal(backoffDelay(1, 1000, 30000), 1000);
  assert.equal(backoffDelay(2, 1000, 30000), 2000);
  assert.equal(backoffDelay(3, 1000, 30000), 4000);
  assert.equal(backoffDelay(10, 1000, 30000), 30000);
  assert.equal(backoffDelay(0, 1000, 30000), 0);
});

test('the connection opens the socket with the address of the relay', () => {
  const sockets: FakeSocket[] = [];
  const clock = fakeTimers();
  const connection = new RelayConnection({
    createSocket: () => {
      const socket = fakeSocket();
      sockets.push(socket);
      return socket;
    },
    timers: clock.timers,
  });

  connection.connect('192.168.1.10:8765');
  assert.equal(sockets.length, 1);
  assert.equal(connection.snapshot().phase, 'connecting');
  assert.equal(connection.snapshot().host, '192.168.1.10:8765');
});

test('the status turns to connected when the socket opens', () => {
  const socket = fakeSocket();
  const connection = new RelayConnection({ createSocket: () => socket });
  connection.connect('host:1');
  socket.open();
  assert.equal(connection.snapshot().phase, 'connected');
  assert.equal(connection.snapshot().connected, true);
  assert.match(connection.snapshot().message, /Connected/);
});

test('an event is sent only when the socket is open', () => {
  const socket = fakeSocket();
  const connection = new RelayConnection({ createSocket: () => socket });
  connection.connect('host:1');

  assert.equal(connection.send({ type: 'move', dx: 1, dy: 2 }), false);
  socket.open();
  assert.equal(connection.send({ type: 'move', dx: 1, dy: 2 }), true);
  assert.deepEqual(socket.sent, ['{"type":"move","dx":1,"dy":2}']);
});

test('a dropped relay is reconnected with a growing delay', () => {
  const sockets: FakeSocket[] = [];
  const clock = fakeTimers();
  const connection = new RelayConnection({
    createSocket: () => {
      const socket = fakeSocket();
      sockets.push(socket);
      return socket;
    },
    timers: clock.timers,
    baseDelay: 1000,
    maxDelay: 8000,
  });

  connection.connect('host:1');
  sockets[0].open();
  sockets[0].drop();

  assert.equal(connection.snapshot().phase, 'waiting');
  assert.equal(connection.snapshot().attempt, 1);
  assert.deepEqual(clock.delays, [1000]);

  clock.runNext();
  assert.equal(sockets.length, 2);
  sockets[1].drop();
  assert.deepEqual(clock.delays, [1000, 2000]);

  clock.runNext();
  sockets[2].drop();
  assert.deepEqual(clock.delays, [1000, 2000, 4000]);
});

test('the delay never grows past the maximum', () => {
  const sockets: FakeSocket[] = [];
  const clock = fakeTimers();
  const connection = new RelayConnection({
    createSocket: () => {
      const socket = fakeSocket();
      sockets.push(socket);
      return socket;
    },
    timers: clock.timers,
    baseDelay: 1000,
    maxDelay: 2500,
  });

  connection.connect('host:1');
  sockets[0].drop();
  clock.runNext();
  sockets[1].drop();
  clock.runNext();
  sockets[2].drop();

  assert.deepEqual(clock.delays, [1000, 2000, 2500]);
});

test('the client gives up after the last try', () => {
  const sockets: FakeSocket[] = [];
  const clock = fakeTimers();
  const connection = new RelayConnection({
    createSocket: () => {
      const socket = fakeSocket();
      sockets.push(socket);
      return socket;
    },
    timers: clock.timers,
    maxAttempts: 2,
  });

  connection.connect('host:1');
  sockets[0].drop();
  clock.runNext();
  sockets[1].drop();
  clock.runNext();
  sockets[2].drop();

  assert.equal(connection.snapshot().phase, 'failed');
  assert.match(connection.snapshot().message, /Could not reach/);
});

test('a connection that comes back resets the counter of the tries', () => {
  const sockets: FakeSocket[] = [];
  const clock = fakeTimers();
  const connection = new RelayConnection({
    createSocket: () => {
      const socket = fakeSocket();
      sockets.push(socket);
      return socket;
    },
    timers: clock.timers,
  });

  connection.connect('host:1');
  sockets[0].open();
  sockets[0].drop();
  clock.runNext();
  sockets[1].open();

  assert.equal(connection.snapshot().attempt, 0);
  assert.equal(connection.snapshot().phase, 'connected');
});

test('disconnecting stops the reconnects', () => {
  const sockets: FakeSocket[] = [];
  const clock = fakeTimers();
  const connection = new RelayConnection({
    createSocket: () => {
      const socket = fakeSocket();
      sockets.push(socket);
      return socket;
    },
    timers: clock.timers,
  });

  connection.connect('host:1');
  sockets[0].open();
  connection.disconnect();

  assert.equal(connection.snapshot().phase, 'closed');
  assert.equal(connection.snapshot().connected, false);
  assert.equal(clock.count, 0);
  assert.equal(sockets.length, 1);
});

test('a listener hears every change of the status', () => {
  const socket = fakeSocket();
  const connection = new RelayConnection({ createSocket: () => socket });
  const phases: string[] = [];
  const stop = connection.subscribe((snapshot) => phases.push(snapshot.phase));

  connection.connect('host:1');
  socket.open();
  stop();
  socket.drop();

  assert.deepEqual(phases, ['idle', 'connecting', 'connected']);
});
