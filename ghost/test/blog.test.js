'use strict';
const { test } = require('node:test');
const assert = require('node:assert');
const { spawn } = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const blog = require('../blog');

const ROOT = path.join(__dirname, '..');
const PORT = 4500 + Math.floor(Math.random() * 300);

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

async function startServer() {
  const dataDir = fs.mkdtempSync(path.join(os.tmpdir(), 'blog-test-'));
  const child = spawn(process.execPath, ['server.js'], {
    cwd: ROOT,
    env: { ...process.env, PORT: String(PORT), DATA_DIR: dataDir },
    stdio: ['ignore', 'pipe', 'pipe'],
  });
  await waitFor(`http://127.0.0.1:${PORT}/api/meta`);

  const register = await fetch(`http://127.0.0.1:${PORT}/api/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: 'Test Editor', email: 'editor@example.test', password: 'correct-horse' }),
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

test('a title becomes a slug', () => {
  assert.equal(blog.slugify('Hello, World!'), 'hello-world');
  assert.equal(blog.slugify('  Spaces   everywhere  '), 'spaces-everywhere');
  assert.equal(blog.slugify("It's fine"), 'its-fine');
  assert.equal(blog.slugify(''), '');
});

test('a taken slug gets a number', () => {
  assert.equal(blog.uniqueSlug('My Post', []), 'my-post');
  assert.equal(blog.uniqueSlug('My Post', ['my-post']), 'my-post-2');
  assert.equal(blog.uniqueSlug('My Post', ['my-post', 'my-post-2']), 'my-post-3');
});

test('a post can be published, scheduled and archived', () => {
  assert.ok(blog.canTransitionPost('draft', 'published'));
  assert.ok(blog.canTransitionPost('draft', 'scheduled'));
  assert.ok(blog.canTransitionPost('published', 'archived'));
  assert.ok(blog.canTransitionPost('archived', 'draft'));
});

test('a published post cannot go back to a draft on its own', () => {
  assert.ok(!blog.canTransitionPost('published', 'draft'));
  assert.match(blog.postTransitionError('published', 'draft'), /cannot go/);
  assert.match(blog.postTransitionError('draft', 'archived!'), /not a post status/);
});

test('only published posts are on the public blog', () => {
  const posts = [
    { id: 1, title: 'Live', status: 'published', published_at: '2026-04-01T00:00:00.000Z' },
    { id: 2, title: 'Draft', status: 'draft', published_at: null },
    { id: 3, title: 'Later', status: 'published', published_at: '2099-01-01T00:00:00.000Z' },
  ];
  const live = blog.publishedPosts(posts, new Date('2026-05-01T00:00:00.000Z'));
  assert.equal(live.length, 1);
  assert.equal(live[0].id, 1);
});

test('the blog is newest first', () => {
  const posts = [
    { id: 1, status: 'published', published_at: '2026-04-01T00:00:00.000Z' },
    { id: 2, status: 'published', published_at: '2026-04-03T00:00:00.000Z' },
    { id: 3, status: 'published', published_at: '2026-04-02T00:00:00.000Z' },
  ];
  assert.deepEqual(blog.publishedPosts(posts).map((p) => p.id), [2, 3, 1]);
});

test('a post with a future date is scheduled and one without a date is a draft', () => {
  const now = new Date('2026-05-01T00:00:00.000Z');
  assert.equal(blog.draftStateFor({ published_at: null }, now), 'draft');
  assert.equal(blog.draftStateFor({ published_at: '2099-01-01T00:00:00.000Z' }, now), 'scheduled');
  assert.equal(blog.draftStateFor({ published_at: '2026-04-01T00:00:00.000Z' }, now), 'published');
});

test('the content search looks in the title, the excerpt and the body', () => {
  const posts = [
    { id: 1, title: 'Kubernetes', excerpt: 'pods', body: 'nothing here', status: 'published' },
    { id: 2, title: 'Gardening', excerpt: 'nothing', body: 'about kubernetes', status: 'published' },
    { id: 3, title: 'Cooking', excerpt: 'nothing', body: 'nothing', status: 'draft' },
  ];
  const found = blog.searchPosts(posts, 'kubernetes', { publishedOnly: false });
  assert.equal(found.length, 2);
  const published = blog.searchPosts(posts, 'kubernetes', { publishedOnly: true });
  assert.equal(published.length, 2);
});

test('the member summary counts the plans and the states', () => {
  const members = [
    { plan: 'free', status: 'active' },
    { plan: 'pro', status: 'active' },
    { plan: 'pro', status: 'suspended' },
  ];
  const summary = blog.memberSummary(members);
  assert.equal(summary.total, 3);
  assert.equal(summary.by_plan.pro, 2);
  assert.equal(summary.by_plan.free, 1);
  assert.equal(summary.by_status.active, 2);
});

test('a newsletter issue carries the published posts that were not sent', () => {
  const posts = [
    { id: 1, status: 'published', published_at: '2026-04-01T00:00:00.000Z' },
    { id: 2, status: 'published', published_at: '2026-04-02T00:00:00.000Z' },
    { id: 3, status: 'draft', published_at: null },
  ];
  const content = blog.issueContent(posts, { id: 1 }, [1]);
  assert.equal(content.length, 1);
  assert.equal(content[0].id, 2);
});

test('a sent issue cannot be sent again', () => {
  assert.ok(blog.canTransitionNewsletter('draft', 'sent'));
  assert.ok(blog.canTransitionNewsletter('scheduled', 'sent'));
  assert.ok(!blog.canTransitionNewsletter('sent', 'sent'));
  assert.ok(!blog.canTransitionNewsletter('sent', 'draft'));
});

// ---------------------------------------------------------------------------
// The API
// ---------------------------------------------------------------------------

test('a new post starts as a draft with the configured defaults', async () => {
  const { call, stop } = await startServer();
  try {
    const created = await call('POST', '/api/posts', { title: 'My first post', slug: 'my-first-post', body: 'Hello' });
    assert.strictEqual(created.status, 201);
    assert.strictEqual(created.json.status, 'draft');
    assert.strictEqual(created.json.author, 'Editor');
  } finally {
    stop();
  }
});

test('a post can be published and then shows on the public blog', async () => {
  const { call, stop } = await startServer();
  try {
    const created = await call('POST', '/api/posts', { title: 'My first post', slug: 'my-first-post', body: 'Hello' });
    const published = await call('POST', `/api/posts/${created.json.id}/publish`, { status: 'published' });
    assert.strictEqual(published.status, 200);
    assert.strictEqual(published.json.status, 'published');
    assert.ok(published.json.published_at);

    const blogPage = await call('GET', '/api/blog');
    assert.strictEqual(blogPage.status, 200);
    assert.ok(blogPage.json.items.some((post) => post.id === created.json.id));
  } finally {
    stop();
  }
});

test('a draft is not on the public blog', async () => {
  const { call, stop } = await startServer();
  try {
    const created = await call('POST', '/api/posts', { title: 'Secret', slug: 'secret', body: 'Hello' });
    const blogPage = await call('GET', '/api/blog');
    assert.ok(!blogPage.json.items.some((post) => post.id === created.json.id));
  } finally {
    stop();
  }
});

test('a published post cannot go back to a draft', async () => {
  const { call, stop } = await startServer();
  try {
    const created = await call('POST', '/api/posts', { title: 'Live', slug: 'live', body: 'Hello' });
    await call('POST', `/api/posts/${created.json.id}/publish`, { status: 'published' });
    const result = await call('POST', `/api/posts/${created.json.id}/publish`, { status: 'draft' });
    assert.strictEqual(result.status, 400);
  } finally {
    stop();
  }
});

test('the content search finds a published post', async () => {
  const { call, stop } = await startServer();
  try {
    const created = await call('POST', '/api/posts', { title: 'Kubernetes notes', slug: 'k8s', body: 'pods and services' });
    await call('POST', `/api/posts/${created.json.id}/publish`, { status: 'published' });

    const found = await call('GET', '/api/blog/search?q=kubernetes');
    assert.strictEqual(found.status, 200);
    assert.ok(found.json.items.some((post) => post.id === created.json.id));
  } finally {
    stop();
  }
});

test('a free slug is offered for a post', async () => {
  const { call, stop } = await startServer();
  try {
    const first = await call('POST', '/api/posts', { title: 'Same title', slug: 'same-title', body: 'a' });
    const second = await call('POST', '/api/posts', { title: 'Same title', slug: 'same-title-2', body: 'b' });

    // The suggestion ignores the post's own slug, so the second post with
    // the same title is offered "same-title-2".
    const slug = await call('GET', `/api/posts/${second.json.id}/slug`);
    assert.strictEqual(slug.status, 200);
    assert.strictEqual(slug.json.slug, 'same-title-2');
    assert.ok(first.json.id !== second.json.id);
  } finally {
    stop();
  }
});

test('the members are counted by plan', async () => {
  const { call, stop } = await startServer();
  try {
    const summary = await call('GET', '/api/members/summary');
    assert.strictEqual(summary.status, 200);
    assert.ok(summary.json.total >= 1);
    assert.ok(summary.json.by_plan.free >= 1);
  } finally {
    stop();
  }
});

test('a newsletter issue can be sent and the posts are released once', async () => {
  const { call, stop } = await startServer();
  try {
    const created = await call('POST', '/api/posts', { title: 'Issue one', slug: 'issue-one', body: 'Hello' });
    await call('POST', `/api/posts/${created.json.id}/publish`, { status: 'published' });

    const issue = await call('POST', '/api/newsletters', { title: 'April', subject: 'What happened in April' });
    assert.strictEqual(issue.status, 201);
    assert.strictEqual(issue.json.status, 'draft');

    const content = await call('GET', `/api/newsletters/${issue.json.id}/content`);
    assert.ok(content.json.count >= 1);

    const sent = await call('POST', `/api/newsletters/${issue.json.id}/send`, {});
    assert.strictEqual(sent.status, 200);
    assert.strictEqual(sent.json.issue.status, 'sent');
    assert.ok(sent.json.released >= 1);

    const after = await call('GET', `/api/newsletters/${issue.json.id}/content`);
    assert.strictEqual(after.json.count, 0);
  } finally {
    stop();
  }
});

test('a sent issue cannot be sent again', async () => {
  const { call, stop } = await startServer();
  try {
    const issue = await call('POST', '/api/newsletters', { title: 'April', subject: 'What happened' });
    await call('POST', `/api/newsletters/${issue.json.id}/send`, {});
    const again = await call('POST', `/api/newsletters/${issue.json.id}/send`, {});
    assert.strictEqual(again.status, 400);
  } finally {
    stop();
  }
});
