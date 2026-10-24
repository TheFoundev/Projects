/**
 * The local storage of the expense app.
 *
 * The reports, the messages and the settings are kept on the device, so a
 * report that was written on a train is still there at home.
 *
 * No imports, so the store can be tested without a React Native runtime.
 */

import type { Message, Report } from './model';

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

const REPORTS_KEY = 'expensify.reports.v1';
const MESSAGES_KEY = 'expensify.messages.v1';
const SETTINGS_KEY = 'expensify.settings.v1';

/** The store of the app. */
export class ExpenseStore {
  private backend: KeyValueStore;

  constructor(backend: KeyValueStore) {
    this.backend = backend;
  }

  /** Read a value, or null when there is nothing or it cannot be read. */
  async read<T>(key: string): Promise<T | null> {
    let raw: string | null = null;
    try {
      raw = await this.backend.getItem(key);
    } catch {
      return null;
    }
    if (!raw) return null;

    try {
      const parsed = JSON.parse(raw) as T;
      return parsed ?? null;
    } catch {
      return null;
    }
  }

  /** Write a value. A failure is swallowed: the app keeps working. */
  async write<T>(key: string, value: T): Promise<boolean> {
    try {
      await this.backend.setItem(key, JSON.stringify(value));
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

  /** The reports that were saved. */
  async reports(): Promise<Report[] | null> {
    return this.read<Report[]>(REPORTS_KEY);
  }

  /** Write the reports. */
  async saveReports(reports: Report[]): Promise<boolean> {
    return this.write(REPORTS_KEY, reports);
  }

  /** The messages that were saved. */
  async messages(): Promise<Message[] | null> {
    return this.read<Message[]>(MESSAGES_KEY);
  }

  /** Write the messages. */
  async saveMessages(messages: Message[]): Promise<boolean> {
    return this.write(MESSAGES_KEY, messages);
  }

  /** The settings that were saved. */
  async settings<T>(): Promise<T | null> {
    return this.read<T>(SETTINGS_KEY);
  }

  /** Write the settings. */
  async saveSettings(settings: unknown): Promise<boolean> {
    return this.write(SETTINGS_KEY, settings);
  }
}
