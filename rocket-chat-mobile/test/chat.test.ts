/** Tests for the chat client and the chat model. */
import assert from 'node:assert';
import test from 'node:test';

import {
  DdpClient,
  DdpError,
  LIST_CHANNELS,
  SEND_MESSAGE,
  appendMessage,
  channelsWithUnread,
  messagesOf,
  toChannels,
  toMessages,
  toSendMessage,
  unreadCounts,
  type Socket,
} from '../src/chat.ts';

/** A socket that answers with the messages it is given. */
function fakeSocket(answers: Record<string, unknown> = {}) {
  const sent: string[] = [];
  let onMessage: (data: string) => void = () => {};
  let onClose: () => void = () => {};

  const socket: Socket = {
    send(payload) {
      sent.push(payload);
      const request = JSON.parse(payload);
      if (request.msg === 'connect') {
        setTimeout(() => onMessage(JSON.stringify({ msg: 'connected', session: 'session-1' })), 0);
        return;
      }
      if (request.msg === 'method' && answers[request.method] !== undefined) {
        setTimeout(
          () => onMessage(JSON.stringify({ msg: 'result', id: request.id, result: answers[request.method] })),
          0,
        );
      }
    },
    close() {
      onClose();
    },
    onMessage(handler) {
      onMessage = handler;
    },
    push(data: string) {
      onMessage(data);
    },
    onClose(handler) {
      onClose = handler;
    },
  };

  return { socket, sent };
}

/** Push a message to the client, as the server would. */
function push(socket: Socket, payload: string): void {
  socket.push?.(payload);
}

test('the client connects and gets a session', async () => {
  const { socket } = fakeSocket();
  const client = new DdpClient(() => socket);

  const session = await client.connect('wss://chat.example/websocket');
  assert.equal(session, 'session-1');
  assert.equal(client.state, 'connected');
});

test('a call answers with the result of the server', async () => {
  const { socket } = fakeSocket({ [LIST_CHANNELS]: [{ _id: 'general', name: 'general' }] });
  const client = new DdpClient(() => socket);
  await client.connect('wss://chat.example/websocket');

  const result = await client.call(LIST_CHANNELS);
  assert.equal(Array.isArray(result), true);
  assert.equal((result as unknown[]).length, 1);
});

test('a call without a connection is refused', async () => {
  const client = new DdpClient(() => fakeSocket().socket);
  await assert.rejects(() => client.call(LIST_CHANNELS), (error: Error) => {
    assert.ok(error instanceof DdpError);
    assert.equal((error as DdpError).errorType, 'no-connection');
    return true;
  });
});

test('the answer of the server is turned into channels', () => {
  const channels = toChannels([
    { _id: 'general', name: 'general', topic: 'hello', unread: 2, membersCount: 38 },
    { _id: 'design', name: 'design', unread: 0, membersCount: 9, private: true },
  ]);
  assert.equal(channels.length, 2);
  assert.equal(channels[0].id, 'general');
  assert.equal(channels[0].unread, 2);
  assert.equal(channels[1].private, true);
});

test('a bad answer gives no channels', () => {
  assert.deepEqual(toChannels(null), []);
  assert.deepEqual(toChannels('nope'), []);
});

test('the answer of the server is turned into messages', () => {
  const messages = toMessages([
    { _id: 'm1', channelId: 'general', msg: 'hello', u: { username: 'priya' }, ts: '08:40' },
  ]);
  assert.equal(messages.length, 1);
  assert.equal(messages[0].body, 'hello');
  assert.equal(messages[0].sender, 'priya');
});

test('the unread count of every channel', () => {
  const channels = toChannels([
    { _id: 'general', name: 'general', unread: 2 },
    { _id: 'design', name: 'design', unread: 0 },
  ]);
  const counts = unreadCounts(channels);
  assert.equal(counts.general, 2);
  assert.equal(counts.design, 0);
});

test('the messages of a channel are picked out', () => {
  const messages = [
    { id: 'm1', channelId: 'general', sender: 'a', body: 'x', time: '1' },
    { id: 'm2', channelId: 'design', sender: 'b', body: 'y', time: '2' },
  ];
  assert.equal(messagesOf(messages, 'general').length, 1);
  assert.equal(messagesOf(messages, 'nothing').length, 0);
});

test('a message is added to the list', () => {
  const messages = appendMessage([], { id: 'm1', channelId: 'general', sender: 'You', body: 'hi', time: 'now' });
  assert.equal(messages.length, 1);
});

test('the message that is sent is trimmed', () => {
  const message = toSendMessage('general', '  hello  ');
  assert.equal(message.body, 'hello');
  assert.equal(message.channelId, 'general');
  assert.equal(message.mine, true);
});

test('the channels with something unread are sorted', () => {
  const channels = toChannels([
    { _id: 'a', name: 'a', unread: 1 },
    { _id: 'b', name: 'b', unread: 5 },
    { _id: 'c', name: 'c', unread: 0 },
  ]);
  const sorted = channelsWithUnread(channels);
  assert.equal(sorted.length, 2);
  assert.equal(sorted[0].id, 'b');
});

test('a call that the server refuses is an error', async () => {
  const { socket } = fakeSocket();
  const client = new DdpClient(() => socket);
  await client.connect('wss://chat.example/websocket');

  // The fake socket says nothing, so the call times out.
  await assert.rejects(() => client.call(SEND_MESSAGE, ['general', 'hi'], 50), (error: Error) => {
    assert.ok(error instanceof DdpError);
    assert.equal((error as DdpError).errorType, 'timeout');
    return true;
  });
});

test('a message the server sends on its own reaches the handler', async () => {
  const { socket } = fakeSocket();
  const client = new DdpClient(() => socket);

  const seen: unknown[] = [];
  client.onMessage((message) => seen.push(message));
  await client.connect('wss://chat.example/websocket');

  // The server pushes a message of its own.
  push(socket, JSON.stringify({ msg: 'method', method: 'notify', params: [{ body: 'hi' }] }));
  assert.equal(seen.length, 1);
  assert.equal((seen[0] as { method: string }).method, 'notify');
});

test('the client answers a ping with a pong', async () => {
  const { socket, sent } = fakeSocket();
  const client = new DdpClient(() => socket);
  await client.connect('wss://chat.example/websocket');

  push(socket, JSON.stringify({ msg: 'ping', id: 'ping-1' }));
  await new Promise((resolve) => setTimeout(resolve, 10));

  const pongs = sent.map((entry) => JSON.parse(entry)).filter((entry) => entry.msg === 'pong');
  assert.equal(pongs.length, 1);
  assert.equal(pongs[0].id, 'ping-1');
});
