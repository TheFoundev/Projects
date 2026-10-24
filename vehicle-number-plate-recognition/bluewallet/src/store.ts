/**
 * Local persistence for the wallet.
 *
 * The store talks to a tiny key/value interface, so the app can use
 * AsyncStorage while the tests use the in-memory implementation.
 */

import type { Transaction } from './wallet-core';

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

const WALLET_KEY = 'bluewallet.wallet.v1';

export type WalletState = {
  transactions: Transaction[];
  address: string;
};

/** Reads and writes the wallet state. */
export class WalletStore {
  private backend: KeyValueStore;

  constructor(backend: KeyValueStore) {
    this.backend = backend;
  }

  /** Read the saved state, or an empty state when there is nothing usable. */
  async load(): Promise<WalletState> {
    let raw: string | null = null;
    try {
      raw = await this.backend.getItem(WALLET_KEY);
    } catch {
      return { transactions: [], address: '' };
    }
    if (!raw) return { transactions: [], address: '' };

    try {
      const parsed = JSON.parse(raw) as Partial<WalletState>;
      return {
        transactions: Array.isArray(parsed.transactions) ? (parsed.transactions as Transaction[]) : [],
        address: typeof parsed.address === 'string' ? parsed.address : '',
      };
    } catch {
      return { transactions: [], address: '' };
    }
  }

  /** Save the state. A failure is swallowed so the UI keeps working. */
  async save(state: WalletState): Promise<boolean> {
    try {
      await this.backend.setItem(WALLET_KEY, JSON.stringify(state));
      return true;
    } catch {
      return false;
    }
  }

  /** Forget everything that was saved. */
  async clear(): Promise<void> {
    try {
      await this.backend.removeItem(WALLET_KEY);
    } catch {
      /* nothing to do */
    }
  }
}
