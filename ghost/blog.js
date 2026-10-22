'use strict';
/**
 * The blogging domain.
 *
 * The rules behind a post: the states it can be in, the transitions, the
 * slug it gets, the way it is published and the newsletter that carries it.
 *
 * Pure functions, no database access, so the rules can be unit tested on
 * their own.
 */

/** The states a post can be in. */
const POST_STATUSES = ['draft', 'published', 'scheduled', 'archived'];

/** The states a member can be in. */
const MEMBER_STATUSES = ['active', 'invited', 'suspended'];

/** The plans a member can be on. */
const PLANS = ['free', 'basic', 'pro'];

/** The states a newsletter issue can be in. */
const NEWSLETTER_STATUSES = ['draft', 'scheduled', 'sent'];

/** The transitions a post may make. */
const POST_TRANSITIONS = {
  draft: ['draft', 'published', 'scheduled', 'archived'],
  published: ['published', 'archived'],
  scheduled: ['scheduled', 'published', 'draft', 'archived'],
  archived: ['archived', 'draft'],
};

/** The transitions a newsletter issue may make. */
const NEWSLETTER_TRANSITIONS = {
  draft: ['draft', 'scheduled', 'sent'],
  scheduled: ['scheduled', 'sent', 'draft'],
  sent: [],
};

function isValidPostStatus(status) {
  return POST_STATUSES.includes(String(status));
}

function isValidMemberStatus(status) {
  return MEMBER_STATUSES.includes(String(status));
}

function isValidPlan(plan) {
  return PLANS.includes(String(plan));
}

function isValidNewsletterStatus(status) {
  return NEWSLETTER_STATUSES.includes(String(status));
}

/** True when a post may move from one state to another. */
function canTransitionPost(from, to) {
  const allowed = POST_TRANSITIONS[String(from)];
  if (!allowed) return false;
  return allowed.includes(String(to));
}

/** The error message for an illegal post transition, or null. */
function postTransitionError(from, to) {
  if (!isValidPostStatus(to)) return `"${to}" is not a post status.`;
  if (!canTransitionPost(from, to)) return `A post cannot go from "${from}" to "${to}".`;
  return null;
}

/** True when a newsletter issue may move from one state to another. */
function canTransitionNewsletter(from, to) {
  const allowed = NEWSLETTER_TRANSITIONS[String(from)];
  if (!allowed) return false;
  return allowed.includes(String(to));
}

/**
 * Turn a title into a slug.
 *
 * The letters are kept as they are, the spaces become dashes and everything
 * else is dropped. An empty title gives an empty slug.
 */
function slugify(title) {
  return String(title || '')
    .trim()
    .toLowerCase()
    .replace(/['’]/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

/**
 * A slug that is not taken yet.
 *
 * The suffix is a number: "my-post", "my-post-2", "my-post-3".
 */
function uniqueSlug(title, taken) {
  const base = slugify(title) || 'untitled';
  const used = new Set((taken || []).map((slug) => String(slug).toLowerCase()));
  if (!used.has(base)) return base;

  let counter = 2;
  while (used.has(`${base}-${counter}`)) counter += 1;
  return `${base}-${counter}`;
}

/**
 * The posts of the public blog.
 *
 * Only the published ones, and only the ones whose published date has
 * passed, newest first.
 */
function publishedPosts(posts, now = new Date()) {
  const time = now instanceof Date ? now.getTime() : new Date(now).getTime();
  return (posts || [])
    .filter((post) => post.status === 'published')
    .filter((post) => !post.published_at || Date.parse(post.published_at) <= time)
    .slice()
    .sort((a, b) => {
      const left = Date.parse(a.published_at || 0) || 0;
      const right = Date.parse(b.published_at || 0) || 0;
      return right - left;
    });
}

/**
 * The state a post is in when it is saved.
 *
 * A post with a date in the future is scheduled, a post without a date
 * stays a draft.
 */
function draftStateFor(post, now = new Date()) {
  const time = now instanceof Date ? now.getTime() : new Date(now).getTime();
  if (!post.published_at) return 'draft';
  const published = Date.parse(post.published_at);
  if (Number.isNaN(published)) return 'draft';
  return published > time ? 'scheduled' : 'published';
}

/**
 * The search results for the content API.
 *
 * The title, the excerpt and the body are searched. The posts come back
 * newest first and the published ones are only included when the caller
 * asks for them.
 */
function searchPosts(posts, query, { publishedOnly = false, now = new Date() } = {}) {
  const needle = String(query || '').trim().toLowerCase();
  const pool = publishedOnly ? publishedPosts(posts, now) : (posts || []).slice();

  const matches = pool.filter((post) => {
    if (!needle) return true;
    const haystack = `${post.title || ''} ${post.excerpt || ''} ${post.body || ''} ${post.author || ''}`.toLowerCase();
    return haystack.includes(needle);
  });

  return matches.sort((a, b) => Number(b.id) - Number(a.id));
}

/**
 * The reader view of a post: the title, the date and the body.
 */
function toPublicPost(post) {
  return {
    id: post.id,
    title: post.title,
    slug: post.slug,
    excerpt: post.excerpt || '',
    body: post.body,
    author: post.author,
    published_at: post.published_at,
  };
}

/**
 * The members, with the plan and the state they are in.
 */
function memberSummary(members) {
  const list = (members || []).slice();
  const byPlan = {};
  const byStatus = {};
  for (const plan of PLANS) byPlan[plan] = 0;
  for (const status of MEMBER_STATUSES) byStatus[status] = 0;

  for (const member of list) {
    if (byPlan[member.plan] !== undefined) byPlan[member.plan] += 1;
    if (byStatus[member.status] !== undefined) byStatus[member.status] += 1;
  }

  return { total: list.length, by_plan: byPlan, by_status: byStatus };
}

/**
 * The posts a newsletter issue carries.
 *
 * A published post that was not sent yet, newest first.
 */
function issueContent(posts, issue, sentAt) {
  const alreadySent = new Set((sentAt || []).map((id) => Number(id)));
  return (posts || [])
    .filter((post) => post.status === 'published')
    .filter((post) => !alreadySent.has(Number(post.id)))
    .slice()
    .sort((a, b) => {
      const left = Date.parse(a.published_at || 0) || 0;
      const right = Date.parse(b.published_at || 0) || 0;
      return right - left;
    });
}

module.exports = {
  POST_STATUSES,
  MEMBER_STATUSES,
  PLANS,
  NEWSLETTER_STATUSES,
  POST_TRANSITIONS,
  NEWSLETTER_TRANSITIONS,
  isValidPostStatus,
  isValidMemberStatus,
  isValidPlan,
  isValidNewsletterStatus,
  canTransitionPost,
  postTransitionError,
  canTransitionNewsletter,
  slugify,
  uniqueSlug,
  publishedPosts,
  draftStateFor,
  searchPosts,
  toPublicPost,
  memberSummary,
  issueContent,
};
