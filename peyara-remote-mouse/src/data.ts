// The connection to the relay is kept in a tiny module store so that all
// three screens share it.
import { useEffect, useMemo, useSyncExternalStore } from 'react';

import { RelayConnection, type ConnectionSnapshot, type SocketLike } from './connection.ts';
import { asyncStorageStore } from './persistence.ts';
import { loadSettings, saveSettings, type KeyValueStore } from './settings.ts';
import type { RelayEvent } from './protocol.ts';

export type ConnectionState = ConnectionSnapshot & {
  /** The label shown in the status pill. */
  label: string;
  /** True when the relay can be reached. */
  connected: boolean;
};

type Listener = () => void;

/** Creates the socket the connection talks over. */
function createSocket(url: string): SocketLike {
  const socket = new WebSocket(url);
  return {
    get readyState() {
      return socket.readyState;
    },
    send: (data: string) => socket.send(data),
    close: () => socket.close(),
    set onopen(handler: (() => void) | null) {
      socket.onopen = handler;
    },
    set onclose(handler: (() => void) | null) {
      socket.onclose = handler;
    },
    set onerror(handler: (() => void) | null) {
      socket.onerror = handler;
    },
    set onmessage(handler: ((event: { data: unknown }) => void) | null) {
      socket.onmessage = handler as ((event: MessageEvent) => void) | null;
    },
  };
}

const connection = new RelayConnection({ createSocket });
const listeners = new Set<Listener>();
let snapshot = connection.snapshot();
let store: KeyValueStore = asyncStorageStore;

connection.subscribe((next) => {
  snapshot = next;
  listeners.forEach((listener) => listener());
});

export function useConnection() {
  return useSyncExternalStore(
    (listener) => {
      listeners.add(listener);
      return () => {
        listeners.delete(listener);
      };
    },
    () => snapshot,
    () => snapshot,
  );
}

/** Replace the store, used by the tests. */
export function setSettingsStore(next: KeyValueStore): void {
  store = next;
}

/** The address of the relay that was used last, if there is one. */
export async function loadLastHost(): Promise<string | null> {
  const settings = await loadSettings(store);
  return settings?.host ?? null;
}

/** Remember the address of the relay. */
export async function rememberHost(host: string): Promise<void> {
  await saveSettings(store, { host });
}

/** Open the connection to the relay and remember the address. */
export function connect(host: string): void {
  const trimmed = host.trim();
  void rememberHost(trimmed);
  connection.connect(trimmed);
}

/** Close the connection and stop reconnecting. */
export function disconnect(): void {
  connection.disconnect();
}

/** Send an event to the relay. */
export function send(event: RelayEvent): boolean {
  return connection.send(event);
}

export function useConnectionStatus() {
  const state = useConnection();
  const label = useMemo(
    () =>
      ({
        idle: 'offline',
        connecting: 'connecting',
        connected: 'connected',
        waiting: 'reconnecting',
        failed: 'offline',
        closed: 'offline',
      })[state.phase],
    [state.phase]
  );
  useEffect(() => {}, []);
  return { ...state, label };
}
