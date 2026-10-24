/**
 * The feed model.
 *
 * Pure functions, no imports, so they can be unit tested without a React
 * Native runtime. The screens call these instead of juggling state by hand.
 */

export type Post = {
  id: string;
  author: string;
  handle: string;
  text: string;
  time: string;
  likes: number;
  replies: number;
  topic: string;
  mine?: boolean;
  createdAt?: number;
};

export type LikeMap = Record<string, boolean>;

export const MAX_POST_LENGTH = 300;

/** True when the text is long enough to be worth posting. */
export function canPublish(text: string): boolean {
  return text.trim().length > 0 && text.trim().length <= MAX_POST_LENGTH;
}

/** Add a post to the top of the feed. */
export function publishPost(posts: Post[], text: string, now: number = Date.now()): Post[] {
  if (!canPublish(text)) return posts;

  const post: Post = {
    id: `local-${now}`,
    author: 'You',
    handle: 'you.bsky.social',
    text: text.trim(),
    time: 'now',
    likes: 0,
    replies: 0,
    topic: 'buildinpublic',
    mine: true,
    createdAt: now,
  };

  return [post, ...posts];
}

/** Flip the like state of one post. */
export function toggleLike(liked: LikeMap, postId: string): LikeMap {
  return { ...liked, [postId]: !liked[postId] };
}

/** The number of likes a post shows, taking the local like into account. */
export function likeCount(post: Post, liked: LikeMap): number {
  return post.likes + (liked[post.id] ? 1 : 0);
}

/** Keep only the posts of one topic. "All" keeps everything. */
export function filterByTopic(posts: Post[], topic: string): Post[] {
  if (!topic || topic === 'All') return posts;
  return posts.filter((post) => post.topic === topic);
}

/** The posts the signed-in user wrote. */
export function myPosts(posts: Post[]): Post[] {
  return posts.filter((post) => post.mine);
}

/**
 * Merge a list of remote posts into the local feed.
 *
 * A post that is already known keeps the local copy (the user may have liked
 * it), a new post is added, and a post that is in both lists is not
 * duplicated. Remote posts are placed after the local ones.
 */
export function mergeRemotePosts(local: Post[], remote: Post[]): Post[] {
  const known = new Set(local.map((post) => post.id));
  const incoming = remote.filter((post) => !known.has(post.id));
  return [...local, ...incoming];
}

/** The number of posts, likes and replies, for the profile screen. */
export function profileStats(posts: Post[], liked: LikeMap) {
  const mine = myPosts(posts);
  return {
    posts: mine.length,
    likes: mine.reduce((sum, post) => sum + likeCount(post, liked), 0),
    replies: mine.reduce((sum, post) => sum + post.replies, 0),
  };
}
