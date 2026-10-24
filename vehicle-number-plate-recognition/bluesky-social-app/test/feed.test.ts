import test from 'node:test';
import assert from 'node:assert';

import {
  canPublish,
  publishPost,
  toggleLike,
  likeCount,
  filterByTopic,
  myPosts,
  mergeRemotePosts,
  profileStats,
  MAX_POST_LENGTH,
  type Post,
} from '../src/feed.ts';
import { FeedStore, createMemoryStore } from '../src/store.ts';

const post = (id: string, overrides: Partial<Post> = {}): Post => ({
  id,
  author: 'Mina Park',
  handle: 'mina.bsky.social',
  text: 'hello',
  time: '1m',
  likes: 3,
  replies: 1,
  topic: 'engineering',
  ...overrides,
});

test('canPublish rejects empty text and text that is too long', () => {
  assert.equal(canPublish(''), false);
  assert.equal(canPublish('   '), false);
  assert.equal(canPublish('hello'), true);
  assert.equal(canPublish('x'.repeat(MAX_POST_LENGTH + 1)), false);
});

test('publishPost puts the new post on top and trims the text', () => {
  const posts = [post('p1')];
  const result = publishPost(posts, '  shipping today  ', 1000);

  assert.equal(result.length, 2);
  assert.equal(result[0].text, 'shipping today');
  assert.equal(result[0].mine, true);
  assert.equal(result[0].likes, 0);
  assert.equal(result[0].id, 'local-1000');
  // the original array is not touched
  assert.equal(posts.length, 1);
});

test('publishPost ignores empty text', () => {
  const posts = [post('p1')];
  assert.equal(publishPost(posts, '   '), posts);
});

test('toggleLike flips the state of one post', () => {
  const liked = toggleLike({}, 'p1');
  assert.equal(liked.p1, true);

  const unliked = toggleLike(liked, 'p1');
  assert.equal(unliked.p1, false);
  assert.equal(liked.p1, true, 'toggleLike does not mutate the previous state');
});

test('likeCount adds the local like to the stored count', () => {
  const p = post('p1', { likes: 10 });
  assert.equal(likeCount(p, {}), 10);
  assert.equal(likeCount(p, { p1: true }), 11);
});

test('filterByTopic keeps everything for All', () => {
  const posts = [post('p1', { topic: 'engineering' }), post('p2', { topic: 'design' })];
  assert.equal(filterByTopic(posts, 'All').length, 2);
  assert.equal(filterByTopic(posts, '').length, 2);
  assert.equal(filterByTopic(posts, 'design').length, 1);
  assert.equal(filterByTopic(posts, 'design')[0].id, 'p2');
});

test('myPosts keeps only the posts of the signed-in user', () => {
  const posts = [post('p1'), post('p2', { mine: true }), post('p3', { mine: true })];
  assert.deepEqual(myPosts(posts).map((p) => p.id), ['p2', 'p3']);
});

test('mergeRemotePosts adds new posts and does not duplicate known ones', () => {
  const local = [post('p1')];
  const remote = [post('p1', { text: 'server copy' }), post('p9')];
  const merged = mergeRemotePosts(local, remote);

  assert.equal(merged.length, 2);
  assert.equal(merged[0].id, 'p1');
  assert.equal(merged[0].text, 'hello', 'the local copy wins for a known post');
  assert.equal(merged[1].id, 'p9');
});

test('profileStats counts the posts, likes and replies of the user', () => {
  const posts = [post('p1'), post('p2', { mine: true, likes: 5, replies: 2 }), post('p3', { mine: true, likes: 1, replies: 1 })];
  const stats = profileStats(posts, { p2: true });

  assert.equal(stats.posts, 2);
  assert.equal(stats.likes, 7);
  assert.equal(stats.replies, 3);
});

test('the feed store round-trips the state', async () => {
  const backend = createMemoryStore();
  const store = new FeedStore(backend);

  const posts = [post('p1', { mine: true })];
  await store.save({ posts, liked: { p1: true } });

  const loaded = await store.load();
  assert.equal(loaded.posts.length, 1);
  assert.equal(loaded.posts[0].id, 'p1');
  assert.equal(loaded.liked.p1, true);
});

test('the feed store returns an empty state when nothing was saved', async () => {
  const store = new FeedStore(createMemoryStore());
  const loaded = await store.load();
  assert.deepEqual(loaded, { posts: [], liked: {} });
});

test('the feed store survives a corrupt saved value', async () => {
  const backend = createMemoryStore();
  await backend.setItem('bluesky.feed.v1', 'not json at all');
  const store = new FeedStore(backend);

  const loaded = await store.load();
  assert.deepEqual(loaded, { posts: [], liked: {} });
});

test('the feed store ignores a saved value of the wrong shape', async () => {
  const backend = createMemoryStore();
  await backend.setItem('bluesky.feed.v1', JSON.stringify({ posts: 'nope', liked: 5 }));
  const store = new FeedStore(backend);

  const loaded = await store.load();
  assert.deepEqual(loaded.posts, []);
  assert.deepEqual(loaded.liked, {});
});

test('the feed store keeps working when the backend fails', async () => {
  const failing = {
    async getItem() { throw new Error('storage unavailable'); },
    async setItem() { throw new Error('storage unavailable'); },
    async removeItem() { throw new Error('storage unavailable'); },
  };
  const store = new FeedStore(failing);

  const loaded = await store.load();
  assert.deepEqual(loaded, { posts: [], liked: {} });
  assert.equal(await store.save({ posts: [], liked: {} }), false);
});

test('the feed store can be cleared', async () => {
  const backend = createMemoryStore();
  const store = new FeedStore(backend);

  await store.save({ posts: [post('p1')], liked: {} });
  await store.clear();

  const loaded = await store.load();
  assert.deepEqual(loaded.posts, []);
});
