/**
 * The local storage of the chat app.
 *
 * The channels and the messages that were fetched last are kept on the
 * device, so the app shows something the moment it opens and keeps working
 * when the server is out of reach.
 *
 * No imports, so the store can be tested without a React Native runtime.
 */

import type { Channel, ChatMessage } from './chat';

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

const CHANNELS_KEY = 'rocketchat.channels.v1';
const MESSAGES_KEY = 'rocketchat.messages.v1';

/** The store of the app. */
export class ChatStore {
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

  /** The channels that were cached. */
  async channels(): Promise<Channel[] | null> {
    return this.read<Channel[]>(CHANNELS_KEY);
  }

  /** Write the channels. */
  async saveChannels(channels: Channel[]): Promise<boolean> {
    return this.write(CHANNELS_KEY, channels);
  }

  /** The messages that were cached. */
  async messages(): Promise<ChatMessage[] | null> {
    return this.read<ChatMessage[]>(MESSAGES_KEY);
  }

  /** Write the messages. */
  async saveMessages(messages: ChatMessage[]): Promise<boolean> {
    return this.write(MESSAGES_KEY, messages);
  }
}
