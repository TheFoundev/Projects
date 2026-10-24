/**
 * The local cache of the app.
 *
 * The repositories and the issues that were fetched last are kept on the
 * device, so the app shows something the moment it opens and keeps working
 * when the network is gone.
 *
 * No imports, so the store can be tested without a React Native runtime.
 */

export type CacheEntry<T> = {
  value: T;
  savedAt: string;
};

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

const REPOS_KEY = 'gitpoint.repos.v1';
const ISSUES_KEY = 'gitpoint.issues.v1';
const PROFILE_KEY = 'gitpoint.profile.v1';

/** The cache of the app. */
export class CacheStore {
  private backend: KeyValueStore;

  constructor(backend: KeyValueStore) {
    this.backend = backend;
  }

  /** Read a value, or null when there is nothing or it cannot be read. */
  async read<T>(key: string): Promise<CacheEntry<T> | null> {
    let raw: string | null = null;
    try {
      raw = await this.backend.getItem(key);
    } catch {
      return null;
    }
    if (!raw) return null;

    try {
      const parsed = JSON.parse(raw) as CacheEntry<T>;
      if (!parsed || typeof parsed !== 'object' || !('value' in parsed)) return null;
      return parsed;
    } catch {
      return null;
    }
  }

  /** Write a value. A failure is swallowed: the app keeps working. */
  async write<T>(key: string, value: T): Promise<boolean> {
    try {
      await this.backend.setItem(key, JSON.stringify({ value, savedAt: new Date().toISOString() } as CacheEntry<T>));
      return true;
    } catch {
      return false;
    }
  }

  /** Forget a value. */
  async clear(key: string): Promise<void> {
    try {
      await this.backend.removeItem(key);
    } catch {
      /* nothing to do */
    }
  }

  /** The repositories that were cached. */
  async repos(): Promise<CacheEntry<unknown[]> | null> {
    return this.read<unknown[]>(REPOS_KEY);
  }

  /** Write the repositories. */
  async saveRepos(value: unknown[]): Promise<boolean> {
    return this.write(REPOS_KEY, value);
  }

  /** The issues that were cached. */
  async issues(): Promise<CacheEntry<unknown[]> | null> {
    return this.read<unknown[]>(ISSUES_KEY);
  }

  /** Write the issues. */
  async saveIssues(value: unknown[]): Promise<boolean> {
    return this.write(ISSUES_KEY, value);
  }

  /** The profile that was cached. */
  async profile(): Promise<CacheEntry<unknown> | null> {
    return this.read<unknown>(PROFILE_KEY);
  }

  /** Write the profile. */
  async saveProfile(value: unknown): Promise<boolean> {
    return this.write(PROFILE_KEY, value);
  }

  /** How old the cache is, in seconds, or null when there is no cache. */
  async ageOf(key: string): Promise<number | null> {
    const entry = await this.read(key);
    if (!entry) return null;
    const saved = Date.parse(entry.savedAt);
    if (Number.isNaN(saved)) return null;
    return Math.max(0, Math.round((Date.now() - saved) / 1000));
  }
}
