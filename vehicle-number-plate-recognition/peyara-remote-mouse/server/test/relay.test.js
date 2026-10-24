const assert = require('node:assert/strict');
const test = require('node:test');

const { createRelay } = require('../relay');

/** A robotjs that records what it was asked to do. */
function fakeRobot() {
  const calls = [];
  return {
    calls,
    getMousePos: () => ({ x: 100, y: 200 }),
    moveMouse: (x, y) => calls.push(['moveMouse', x, y]),
    mouseClick: (button) => calls.push(['mouseClick', button]),
    scrollMouse: (horizontal, vertical) => calls.push(['scrollMouse', horizontal, vertical]),
    typeString: (text) => calls.push(['typeString', text]),
    keyTap: (key) => calls.push(['keyTap', key]),
  };
}

/** A logger that keeps the lines instead of printing them. */
function fakeLogger() {
  const lines = [];
  return { lines, log: (...args) => lines.push(args.join(' ')) };
}

test('a move moves the cursor from where it is', () => {
  const robot = fakeRobot();
  const relay = createRelay({ robot, logger: fakeLogger() });

  const result = relay.handleMessage(JSON.stringify({ type: 'move', dx: 10, dy: -5 }));

  assert.equal(result.status, 'ok');
  assert.equal(result.performed, true);
  assert.deepEqual(robot.calls, [['moveMouse', 115, 192.5]]);
});

test('the sensitivity of the relay can be changed', () => {
  const robot = fakeRobot();
  const relay = createRelay({ robot, logger: fakeLogger(), sensitivity: 1 });

  relay.handleMessage(JSON.stringify({ type: 'move', dx: 10, dy: 5 }));
  assert.deepEqual(robot.calls, [['moveMouse', 110, 205]]);
});

test('a click presses the right button', () => {
  const robot = fakeRobot();
  const relay = createRelay({ robot, logger: fakeLogger() });

  relay.handleMessage(JSON.stringify({ type: 'click', button: 'right' }));
  relay.handleMessage(JSON.stringify({ type: 'click', button: 'left' }));

  assert.deepEqual(robot.calls, [
    ['mouseClick', 'right'],
    ['mouseClick', 'left'],
  ]);
});

test('a scroll is passed on', () => {
  const robot = fakeRobot();
  const relay = createRelay({ robot, logger: fakeLogger() });

  relay.handleMessage(JSON.stringify({ type: 'scroll', dy: -3 }));
  assert.deepEqual(robot.calls, [['scrollMouse', 0, -3]]);
});

test('text is typed and a special key is mapped', () => {
  const robot = fakeRobot();
  const relay = createRelay({ robot, logger: fakeLogger() });

  relay.handleMessage(JSON.stringify({ type: 'text', text: 'hello' }));
  relay.handleMessage(JSON.stringify({ type: 'key', key: 'Enter' }));
  relay.handleMessage(JSON.stringify({ type: 'key', key: 'esc' }));

  assert.deepEqual(robot.calls, [
    ['typeString', 'hello'],
    ['keyTap', 'enter'],
    ['keyTap', 'escape'],
  ]);
});

test('a message that is not JSON is ignored', () => {
  const relay = createRelay({ robot: fakeRobot(), logger: fakeLogger() });
  const result = relay.handleMessage('{oops');
  assert.equal(result.status, 'invalid');
  assert.match(result.reason, /not valid JSON/);
});

test('an event the relay does not know is ignored', () => {
  const robot = fakeRobot();
  const relay = createRelay({ robot, logger: fakeLogger() });
  const result = relay.handleMessage(JSON.stringify({ type: 'launch' }));
  assert.equal(result.status, 'ignored');
  assert.equal(robot.calls.length, 0);
});

test('without robotjs the events are only logged', () => {
  const logger = fakeLogger();
  const relay = createRelay({ robot: null, logger });

  const result = relay.handleMessage(JSON.stringify({ type: 'click', button: 'left' }));

  assert.equal(result.status, 'ok');
  assert.equal(result.performed, false);
  assert.equal(relay.hasRobot(), false);
  assert.match(logger.lines.join('\n'), /"type":"click"/);
});

test('the relay counts the connections, the events and the ignored messages', () => {
  const relay = createRelay({ robot: fakeRobot(), logger: fakeLogger() });

  relay.onConnection();
  relay.handleMessage(JSON.stringify({ type: 'move', dx: 1, dy: 1 }));
  relay.handleMessage(JSON.stringify({ type: 'launch' }));
  relay.handleMessage('nope');
  relay.onDisconnection();

  const stats = relay.stats();
  assert.equal(stats.connected, 1);
  assert.equal(stats.handled, 1);
  assert.equal(stats.ignored, 1);
  assert.equal(stats.invalid, 1);
});
