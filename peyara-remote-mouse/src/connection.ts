/**
 * The connection to the relay.
 *
 * The class owns a websocket, keeps the status of the connection and
 * reconnects with a growing delay when the relay goes away.
 *
 * The socket and the timers are injected, so the whole class can be tested
 * without a network and without React Native.
 */

import { encodeEvent, relayUrl, type RelayEvent } from './protocol.ts';

export type ConnectionPhase =
  | 'idle'
  | 'connecting'
  | 'connected'
  | 'waiting'
  | 'failed'
  | 'closed';

export type ConnectionSnapshot = {
  phase: ConnectionPhase;
  /** True only when the socket is open. */
  connected: boolean;
  host: string;
  /** A short sentence for the user. */
  message: string;
  /** How many times the client has tried to reconnect. */
  attempt: number;
  /** The last event that was sent, for the status card. */
  lastEvent: string;
};

/** The part of a websocket the client uses. */
export type SocketLike = {
  readyState: number;
  send(data: string): void;
  close(): void;
  onopen: (() => void) | null;
  onclose: (() => void) | null;
  onerror: (() => void) | null;
  onmessage: ((event: { data: unknown }) => void) | null;
};

/** The value of `readyState` of an open socket. */
export const SOCKET_OPEN = 1;

export type Timer = {
  setTimeout(handler: () => void, delay: number): unknown;
  clearTimeout(handle: unknown): void;
};

export type RelayConnectionOptions = {
  createSocket: (url: string) => SocketLike;
  timers?: Timer;
  /** The first delay before a reconnect, in milliseconds. */
  baseDelay?: number;
  /** The longest delay between two tries, in milliseconds. */
  maxDelay?: number;
  /** How many times the client tries before it gives up. */
  maxAttempts?: number;
};

export type ConnectionListener = (snapshot: ConnectionSnapshot) => void;

/** The delay before the nth try, growing but never past `maxDelay`. */
export function backoffDelay(attempt: number, baseDelay = 1000, maxDelay = 30000): number {
  if (attempt <= 0) return 0;
  const delay = baseDelay * 2 ** (attempt - 1);
  return Math.min(delay, maxDelay);
}

/** The sentence shown for a phase. */
export function phaseMessage(phase: ConnectionPhase, attempt: number): string {
  switch (phase) {
    case 'idle':
      return 'Not connected';
    case 'connecting':
      return 'Connecting…';
    case 'connected':
      return 'Connected to relay';
    case 'waiting':
      return `Reconnecting in a moment (try ${attempt})…`;
    case 'failed':
      return 'Could not reach the relay';
    case 'closed':
      return 'Disconnected';
    default:
      return 'Not connected';
  }
}

/** The connection to the relay, with an automatic reconnect. */
export class RelayConnection {
  private socket: SocketLike | null = null;
  private host = '';
  private phase: ConnectionPhase = 'idle';
  private attempt = 0;
  private lastEvent = '—';
  private timer: unknown = null;
  private readonly listeners = new Set<ConnectionListener>();
  private readonly createSocket: (url: string) => SocketLike;
  private readonly timers: Timer;
  private readonly baseDelay: number;
  private readonly maxDelay: number;
  private readonly maxAttempts: number;

  constructor(options: RelayConnectionOptions) {
    this.createSocket = options.createSocket;
    this.timers = options.timers ?? {
      setTimeout: (handler, delay) => setTimeout(handler, delay),
      clearTimeout: (handle) => clearTimeout(handle as ReturnType<typeof setTimeout>),
    };
    this.baseDelay = options.baseDelay ?? 1000;
    this.maxDelay = options.maxDelay ?? 30000;
    this.maxAttempts = options.maxAttempts ?? 5;
  }

  /** The current status. */
  snapshot(): ConnectionSnapshot {
    return {
      phase: this.phase,
      connected: this.phase === 'connected',
      host: this.host,
      message: phaseMessage(this.phase, this.attempt),
      attempt: this.attempt,
      lastEvent: this.lastEvent,
    };
  }

  /** Listen to the status. Returns a function that stops the listening. */
  subscribe(listener: ConnectionListener): () => void {
    this.listeners.add(listener);
    listener(this.snapshot());
    return () => {
      this.listeners.delete(listener);
    };
  }

  /** Open the connection to the relay. */
  connect(host: string): void {
    this.stopTimer();
    this.closeSocket();
    this.host = host.trim();
    this.attempt = 0;
    this.open();
  }

  /** Close the connection and stop reconnecting. */
  disconnect(): void {
    this.stopTimer();
    this.closeSocket();
    this.attempt = 0;
    this.setPhase('closed');
  }

  /** Send an event to the relay. */
  send(event: RelayEvent): boolean {
    if (!this.socket || this.socket.readyState !== SOCKET_OPEN) return false;
    const payload = encodeEvent(event);
    this.socket.send(payload);
    this.lastEvent = payload.slice(0, 80);
    this.emit();
    return true;
  }

  private open(): void {
    this.setPhase('connecting');
    let socket: SocketLike;
    try {
      socket = this.createSocket(relayUrl(this.host));
    } catch {
      this.scheduleReconnect();
      return;
    }
    this.socket = socket;

    socket.onopen = () => {
      this.attempt = 0;
      this.setPhase('connected');
    };
    socket.onclose = () => {
      this.socket = null;
      this.scheduleReconnect();
    };
    socket.onerror = () => {
      this.socket = null;
    };
    socket.onmessage = (event) => {
      this.lastEvent = String(event.data).slice(0, 80);
      this.emit();
    };
  }

  private scheduleReconnect(): void {
    if (this.phase === 'closed') return;
    this.attempt += 1;
    if (this.attempt > this.maxAttempts) {
      this.setPhase('failed');
      return;
    }
    this.setPhase('waiting');
    this.timer = this.timers.setTimeout(() => {
      this.timer = null;
      if (this.phase === 'closed') return;
      this.open();
    }, backoffDelay(this.attempt, this.baseDelay, this.maxDelay));
  }

  private closeSocket(): void {
    if (!this.socket) return;
    this.socket.onopen = null;
    this.socket.onclose = null;
    this.socket.onerror = null;
    this.socket.onmessage = null;
    try {
      this.socket.close();
    } catch {
      // The socket was already gone.
    }
    this.socket = null;
  }

  private stopTimer(): void {
    if (this.timer === null) return;
    this.timers.clearTimeout(this.timer);
    this.timer = null;
  }

  private setPhase(phase: ConnectionPhase): void {
    this.phase = phase;
    this.emit();
  }

  private emit(): void {
    const snapshot = this.snapshot();
    this.listeners.forEach((listener) => listener(snapshot));
  }
}
