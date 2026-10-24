/**
 * Local persistence for the check history.
 *
 * The store talks to a tiny key/value interface, so the app can use
 * AsyncStorage while the tests use the in-memory implementation.
 */

import type { Check } from './exposure';

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

const CHECKS_KEY = 'covid-alert.checks.v1';

/** Reads and writes the check history. */
export class CheckStore {
  private backend: KeyValueStore;

  constructor(backend: KeyValueStore) {
    this.backend = backend;
  }

  /** Read the saved history, or an empty one when there is nothing usable. */
  async load(): Promise<Check[]> {
    let raw: string | null = null;
    try {
      raw = await this.backend.getItem(CHECKS_KEY);
    } catch {
      return [];
    }
    if (!raw) return [];

    try {
      const parsed = JSON.parse(raw) as unknown;
      if (!Array.isArray(parsed)) return [];
      return parsed.filter(
        (item): item is Check =>
          typeof item === 'object' &&
          item !== null &&
          typeof (item as Check).id === 'string' &&
          typeof (item as Check).result === 'string',
      );
    } catch {
      return [];
    }
  }

  /** Save the history. A failure is swallowed so the UI keeps working. */
  async save(checks: Check[]): Promise<boolean> {
    try {
      await this.backend.setItem(CHECKS_KEY, JSON.stringify(checks));
      return true;
    } catch {
      return false;
    }
  }

  /** Forget everything that was saved. */
  async clear(): Promise<void> {
    try {
      await this.backend.removeItem(CHECKS_KEY);
    } catch {
      /* nothing to do */
    }
  }
}
