'use strict';
const { test } = require('node:test');
const assert = require('node:assert');
const { spawn } = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const helpdesk = require('../helpdesk');

const ROOT = path.join(__dirname, '..');
const PORT = 4200 + Math.floor(Math.random() * 300);

function waitFor(url, timeout = 12000) {
  const started = Date.now();
  return new Promise((resolve, reject) => {
    const tick = async () => {
      try {
        const response = await fetch(url);
        if (response.ok) return resolve(response);
      } catch {}
      if (Date.now() - started > timeout) return reject(new Error('server did not start'));
      setTimeout(tick, 150);
    };
    tick();
  });
}

/** Start the server and sign in, returning a helper for the API. */
async function startServer() {
  const dataDir = fs.mkdtempSync(path.join(os.tmpdir(), 'helpdesk-test-'));
  const child = spawn(process.execPath, ['server.js'], {
    cwd: ROOT,
    env: { ...process.env, PORT: String(PORT), DATA_DIR: dataDir },
    stdio: ['ignore', 'pipe', 'pipe'],
  });
  await waitFor(`http://127.0.0.1:${PORT}/api/meta`);

  const register = await fetch(`http://127.0.0.1:${PORT}/api/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: 'Test Agent', email: 'agent@example.test', password: 'correct-horse' }),
  });
  const cookie = register.headers.get('set-cookie').split(';')[0];

  const call = async (method, urlPath, body) => {
    const response = await fetch(`http://127.0.0.1:${PORT}${urlPath}`, {
      method,
      headers: { 'Content-Type': 'application/json', Cookie: cookie },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    const text = await response.text();
    let json = null;
    try { json = text ? JSON.parse(text) : null; } catch { json = text; }
    return { status: response.status, json };
  };

  const stop = () => {
    child.kill('SIGTERM');
    fs.rmSync(dataDir, { recursive: true, force: true });
  };

  return { call, stop };
}

// ---------------------------------------------------------------------------
// The rules
// ---------------------------------------------------------------------------

test('the known statuses and priorities are the ones the app uses', () => {
  assert.deepEqual(helpdesk.STATUSES, ['open', 'pending', 'closed']);
  assert.deepEqual(helpdesk.PRIORITIES, ['low', 'normal', 'high', 'urgent']);
  assert.ok(helpdesk.isValidStatus('open'));
  assert.ok(!helpdesk.isValidStatus('archived'));
  assert.ok(helpdesk.isValidPriority('urgent'));
  assert.ok(!helpdesk.isValidPriority('critical'));
});

test('a conversation can be moved between the open states', () => {
  assert.ok(helpdesk.canTransition('open', 'pending'));
  assert.ok(helpdesk.canTransition('open', 'closed'));
  assert.ok(helpdesk.canTransition('pending', 'open'));
  assert.ok(helpdesk.canTransition('closed', 'open'));
});

test('an unknown state is never a legal transition', () => {
  assert.ok(!helpdesk.canTransition('open', 'archived'));
  assert.ok(!helpdesk.canTransition('archived', 'open'));
  assert.match(helpdesk.transitionError('open', 'archived'), /not a status/);
  assert.equal(helpdesk.transitionError('open', 'closed'), null);
});

test('the thread keeps the internal notes apart', () => {
  const conversation = { id: 1, subject: 'Help', created_at: '2026-04-23T08:00:00.000Z' };
  const messages = [
    { id: 2, conversation_id: 1, sender: 'A', body: 'hi', direction: 'inbound', created_at: '2026-04-23T08:01:00.000Z' },
    { id: 1, conversation_id: 1, sender: 'B', body: 'internal', direction: 'note', created_at: '2026-04-23T08:02:00.000Z' },
    { id: 3, conversation_id: 2, sender: 'C', body: 'other', direction: 'inbound', created_at: '2026-04-23T08:03:00.000Z' },
  ];

  const thread = helpdesk.buildThread(conversation, messages);
  assert.equal(thread.reply_count, 2);
  assert.equal(thread.public_reply_count, 1);
  assert.equal(thread.internal_note_count, 1);
  // The replies are in the order they arrived, so the note with the lower id
  // comes first even though it was written later.
  assert.equal(thread.replies[0].body, 'internal');
  assert.equal(thread.replies[0].internal, true);
  assert.equal(thread.replies[1].body, 'hi');
  assert.equal(thread.replies[1].internal, false);
});

test('the inbox counts the conversations by state', () => {
  const conversations = [
    { id: 1, subject: 'a', status: 'open', priority: 'high', assignee: 'Ana' },
    { id: 2, subject: 'b', status: 'open', priority: 'low', assignee: '' },
    { id: 3, subject: 'c', status: 'closed', priority: 'normal', assignee: 'Bo' },
  ];

  const inbox = helpdesk.summariseInbox(conversations);
  assert.equal(inbox.total, 3);
  assert.equal(inbox.counts.open, 2);
  assert.equal(inbox.counts.closed, 1);
  assert.equal(inbox.unassigned, 1);
});

test('the inbox puts the urgent conversation first', () => {
  const conversations = [
    { id: 1, subject: 'a', status: 'open', priority: 'low', assignee: '' },
    { id: 2, subject: 'b', status: 'open', priority: 'urgent', assignee: '' },
    { id: 3, subject: 'c', status: 'open', priority: 'normal', assignee: '' },
  ];
  const inbox = helpdesk.summariseInbox(conversations);
  assert.equal(inbox.items[0].id, 2);
  assert.equal(inbox.items[1].id, 3);
});

test('the inbox filters by state, priority, agent and text', () => {
  const conversations = [
    { id: 1, subject: 'invoice', requester: 'Ann', email: 'ann@example.test', status: 'open', priority: 'high', assignee: 'Ana' },
    { id: 2, subject: 'refund', requester: 'Bob', email: 'bob@example.test', status: 'closed', priority: 'low', assignee: 'Bo' },
  ];

  assert.equal(helpdesk.summariseInbox(conversations, { status: 'open' }).total, 1);
  assert.equal(helpdesk.summariseInbox(conversations, { priority: 'low' }).total, 1);
  assert.equal(helpdesk.summariseInbox(conversations, { assignee: 'Ana' }).total, 1);
  assert.equal(helpdesk.summariseInbox(conversations, { q: 'invoice' }).total, 1);
  assert.equal(helpdesk.summariseInbox(conversations, { q: 'nothing' }).total, 0);
});

test('the agent with the least work gets the next conversation', () => {
  const conversations = [
    { assignee: 'Ana' }, { assignee: 'Ana' }, { assignee: 'Bo' },
  ];
  assert.equal(helpdesk.chooseAssignee(conversations, ['Ana', 'Bo']), 'Bo');
  assert.equal(helpdesk.chooseAssignee([], ['Ana', 'Bo']), 'Ana');
  assert.equal(helpdesk.chooseAssignee([], []), '');
});

test('the canned response search puts the best match first', () => {
  const responses = [
    { id: 1, title: 'Refund policy', body: 'We refund within 30 days.', category: 'billing' },
    { id: 2, title: 'Reset your password', body: 'Use the reset link.', category: 'account' },
    { id: 3, title: 'Shipping times', body: 'Refunds are not about shipping.', category: 'shipping' },
  ];

  const found = helpdesk.searchCannedResponses(responses, 'refund');
  assert.equal(found[0].id, 1);
  assert.equal(helpdesk.searchCannedResponses(responses, '').length, 3);
  assert.equal(helpdesk.searchCannedResponses(responses, 'zzz').length, 0);
});

// ---------------------------------------------------------------------------
// The API
// ---------------------------------------------------------------------------

test('the inbox endpoint lists the seeded conversations', async () => {
  const { call, stop } = await startServer();
  try {
    const inbox = await call('GET', '/api/inbox');
    assert.strictEqual(inbox.status, 200);
    assert.ok(inbox.json.total >= 1);
    assert.ok(inbox.json.counts.open >= 1);
  } finally {
    stop();
  }
});

test('a reply can be added to a conversation', async () => {
  const { call, stop } = await startServer();
  try {
    const created = await call('POST', '/api/conversations', {
      subject: 'Need help', requester: 'Ann', email: 'ann@example.test',
    });
    assert.strictEqual(created.status, 201);
    const id = created.json.id;

    const reply = await call('POST', `/api/conversations/${id}/messages`, {
      body: 'Hello, how can we help?', direction: 'outbound',
    });
    assert.strictEqual(reply.status, 201);
    assert.strictEqual(reply.json.direction, 'outbound');
  } finally {
    stop();
  }
});

test('a reply with an unknown direction is rejected', async () => {
  const { call, stop } = await startServer();
  try {
    const created = await call('POST', '/api/conversations', {
      subject: 'Need help', requester: 'Ann', email: 'ann@example.test',
    });
    const reply = await call('POST', `/api/conversations/${created.json.id}/messages`, {
      body: 'Hello', direction: 'sideways',
    });
    assert.strictEqual(reply.status, 400);
  } finally {
    stop();
  }
});

test('an internal note is kept out of the public reply count', async () => {
  const { call, stop } = await startServer();
  try {
    const created = await call('POST', '/api/conversations', {
      subject: 'Need help', requester: 'Ann', email: 'ann@example.test',
    });
    const id = created.json.id;

    await call('POST', `/api/conversations/${id}/messages`, { body: 'Public answer', direction: 'outbound' });
    await call('POST', `/api/conversations/${id}/messages`, { body: 'Internal thought', direction: 'note' });

    const thread = await call('GET', `/api/conversations/${id}/thread`);
    assert.strictEqual(thread.json.reply_count, 2);
    assert.strictEqual(thread.json.public_reply_count, 1);
    assert.strictEqual(thread.json.internal_note_count, 1);
  } finally {
    stop();
  }
});

test('the status can be changed and the change is recorded', async () => {
  const { call, stop } = await startServer();
  try {
    const created = await call('POST', '/api/conversations', {
      subject: 'Need help', requester: 'Ann', email: 'ann@example.test',
    });
    const id = created.json.id;

    const changed = await call('POST', `/api/conversations/${id}/status`, { status: 'pending' });
    assert.strictEqual(changed.status, 200);
    assert.strictEqual(changed.json.status, 'pending');

    const events = await call('GET', `/api/conversations/${id}/events`);
    assert.ok(events.json.items.some((event) => event.type === 'status'));
  } finally {
    stop();
  }
});

test('a reply reopens a conversation that is waiting', async () => {
  const { call, stop } = await startServer();
  try {
    const created = await call('POST', '/api/conversations', {
      subject: 'Need help', requester: 'Ann', email: 'ann@example.test',
    });
    const id = created.json.id;

    await call('POST', `/api/conversations/${id}/status`, { status: 'pending' });
    await call('POST', `/api/conversations/${id}/messages`, { body: 'An answer', direction: 'outbound' });

    const conversation = await call('GET', `/api/conversations/${id}`);
    assert.strictEqual(conversation.json.status, 'open');
  } finally {
    stop();
  }
});

test('a conversation can be assigned to an agent', async () => {
  const { call, stop } = await startServer();
  try {
    const created = await call('POST', '/api/conversations', {
      subject: 'Need help', requester: 'Ann', email: 'ann@example.test',
    });
    const id = created.json.id;

    const assigned = await call('POST', `/api/conversations/${id}/assign`, { assignee: 'Test Agent' });
    assert.strictEqual(assigned.status, 200);
    assert.strictEqual(assigned.json.assignee, 'Test Agent');
  } finally {
    stop();
  }
});

test('a conversation cannot be assigned to somebody who is not an agent', async () => {
  const { call, stop } = await startServer();
  try {
    const created = await call('POST', '/api/conversations', {
      subject: 'Need help', requester: 'Ann', email: 'ann@example.test',
    });
    const assigned = await call('POST', `/api/conversations/${created.json.id}/assign`, { assignee: 'Nobody' });
    assert.strictEqual(assigned.status, 400);
  } finally {
    stop();
  }
});

test('a canned response can be sent as a reply', async () => {
  const { call, stop } = await startServer();
  try {
    const created = await call('POST', '/api/conversations', {
      subject: 'Need help', requester: 'Ann', email: 'ann@example.test',
    });
    const canned = await call('POST', '/api/canned_responses', {
      title: 'Refund policy', body: 'We refund within 30 days.', category: 'billing',
    });
    assert.strictEqual(canned.status, 201);

    const reply = await call('POST', `/api/conversations/${created.json.id}/canned/${canned.json.id}`, {});
    assert.strictEqual(reply.status, 201);
    assert.strictEqual(reply.json.body, 'We refund within 30 days.');
    assert.strictEqual(reply.json.direction, 'outbound');
  } finally {
    stop();
  }
});

test('the canned responses can be searched', async () => {
  const { call, stop } = await startServer();
  try {
    await call('POST', '/api/canned_responses', { title: 'Password reset', body: 'Use the link.', category: 'account' });
    const found = await call('GET', '/api/canned_responses/search?q=password');
    assert.strictEqual(found.status, 200);
    assert.ok(found.json.items.some((item) => item.title === 'Password reset'));
  } finally {
    stop();
  }
});

test('replying needs a signed-in agent', async () => {
  const { call, stop } = await startServer();
  try {
    const created = await call('POST', '/api/conversations', {
      subject: 'Need help', requester: 'Ann', email: 'ann@example.test',
    });
    const response = await fetch(`http://127.0.0.1:${PORT}/api/conversations/${created.json.id}/messages`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ body: 'Hello', direction: 'outbound' }),
    });
    assert.strictEqual(response.status, 401);
  } finally {
    stop();
  }
});
