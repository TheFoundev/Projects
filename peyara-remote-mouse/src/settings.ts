/**
 * The settings of the app.
 *
 * The store is a small key/value interface, so the settings can be tested
 * with a memory store and stored on the device with AsyncStorage.
 */

export type KeyValueStore = {
  getItem(key: string): Promise<string | null>;
  setItem(key: string, value: string): Promise<void>;
  removeItem(key: string): Promise<void>;
};

/** A store that keeps everything in memory. */
export function createMemoryStore(seed: Record<string, string> = {}) {
  const values = new Map<string, string>(Object.entries(seed));
  return {
    async getItem(key: string): Promise<string | null> {
      return values.has(key) ? (values.get(key) as string) : null;
    },
    async setItem(key: string, value: string): Promise<void> {
      values.set(key, value);
    },
    async removeItem(key: string): Promise<void> {
      values.delete(key);
    },
    /** Everything the store holds. Only used by the tests. */
    dump(): Record<string, string> {
      return Object.fromEntries(values.entries());
    },
  };
}

/** The key the settings are stored under. */
export const SETTINGS_KEY = 'peyara.relay.v1';

export type RelaySettings = {
  /** The address of the relay, as the user typed it. */
  host: string;
};

/** Read the settings, or null when there are none. */
export async function loadSettings(store: KeyValueStore): Promise<RelaySettings | null> {
  const raw = await store.getItem(SETTINGS_KEY);
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as Partial<RelaySettings>;
    if (typeof parsed.host !== 'string') return null;
    return { host: parsed.host };
  } catch {
    return null;
  }
}

/** Write the settings. */
export async function saveSettings(store: KeyValueStore, settings: RelaySettings): Promise<void> {
  await store.setItem(SETTINGS_KEY, JSON.stringify(settings));
}

/** Forget the settings. */
export async function clearSettings(store: KeyValueStore): Promise<void> {
  await store.removeItem(SETTINGS_KEY);
}
