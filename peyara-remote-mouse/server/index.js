// The WebSocket relay of the Peyara remote-mouse app.
//
// It receives the JSON events of the phone and drives the local cursor when
// robotjs is installed. Without robotjs the events are only logged, so the
// protocol can still be seen working.
//
// The logic lives in relay.js, which has no dependency on ws or robotjs and
// is covered by the tests in server/test.
const { WebSocketServer } = require('ws');

const { createRelay } = require('./relay');

let robot = null;
try {
  robot = require('robotjs');
  console.log('robotjs loaded: events will control the real cursor.');
} catch {
  console.log('robotjs not installed: events will only be logged.');
}

const port = Number(process.env.PORT || 8765);
const sensitivity = Number(process.env.SENSITIVITY || 1.5);
const relay = createRelay({ robot, sensitivity });

const wss = new WebSocketServer({ port });

wss.on('connection', (socket) => {
  relay.onConnection();
  socket.send(JSON.stringify({ type: 'welcome', message: 'relay ready' }));

  socket.on('message', (raw) => {
    relay.handleMessage(raw);
  });

  socket.on('close', () => relay.onDisconnection());
});

console.log(`Peyara relay listening on ws://0.0.0.0:${port}`);
