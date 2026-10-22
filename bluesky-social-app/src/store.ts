/**
 * Local persistence for the feed.
 *
 * The store talks to a tiny key/value interface, so the app can use
 * AsyncStorage while the tests use the in-memory implementation below. No
 * imports, so this module can be unit tested without a React Native runtime.
 */

import type { Post, LikeMap } from './feed';

export type KeyValueStore = {
  getItem(key: string): Promise<string | null>;
  setItem(key: string, value: string): Promise<void>;
  removeItem(key: string): Promise<void>;
};

/** An in-memory key/value store, used by the tests and as a fallback. */
export function createMemoryStore(): KeyValueStore & { dump(): Record<string, string> } {
  const values = new Map<string, string>();

  return {
    async getItem(key) {
      return values.has(key) ? values.get(key)! : null;
    },
    async setItem(key, value) {
      values.set(key, value);
    },
    async removeItem(key) {
      values.delete(key);
    },
    dump() {
      return Object.fromEntries(values.entries());
    },
  };
}

export type FeedState = {
  posts: Post[];
  liked: LikeMap;
};

const FEED_KEY = 'bluesky.feed.v1';

/** Reads and writes the feed and the like map. */
export class FeedStore {
  private backend: KeyValueStore;

  constructor(backend: KeyValueStore) {
    this.backend = backend;
  }

  /**
   * Read the saved state. A corrupt or missing value gives an empty state
   * instead of an error, so a bad write can never break the app.
   */
  async load(): Promise<FeedState> {
    let raw: string | null = null;
    try {
      raw = await this.backend.getItem(FEED_KEY);
    } catch {
      return { posts: [], liked: {} };
    }
    if (!raw) return { posts: [], liked: {} };

    try {
      const parsed = JSON.parse(raw) as Partial<FeedState>;
      return {
        posts: Array.isArray(parsed.posts) ? (parsed.posts as Post[]) : [],
        liked: parsed.liked && typeof parsed.liked === 'object' ? (parsed.liked as LikeMap) : {},
      };
    } catch {
      return { posts: [], liked: {} };
    }
  }

  /** Save the state. A failure is swallowed: the UI keeps working. */
  async save(state: FeedState): Promise<boolean> {
    try {
      await this.backend.setItem(FEED_KEY, JSON.stringify(state));
      return true;
    } catch {
      return false;
    }
  }

  /** Forget everything that was saved. */
  async clear(): Promise<void> {
    try {
      await this.backend.removeItem(FEED_KEY);
    } catch {
      /* nothing to do */
    }
  }
}
