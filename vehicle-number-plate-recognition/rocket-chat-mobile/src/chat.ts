/**
 * The chat client.
 *
 * The client speaks the DDP protocol over a websocket: a JSON message with a
 * `msg` field, a `method` for the calls and a `id` for the answers. The
 * socket is given to the client, so the tests can answer without a network.
 *
 * No imports, so the client can be tested without a React Native runtime.
 */

export type Channel = {
  id: string;
  name: string;
  topic: string;
  unread: number;
  members: number;
  private?: boolean;
};

export type ChatMessage = {
  id: string;
  channelId: string;
  sender: string;
  body: string;
  time: string;
  mine?: boolean;
};

/** A message of the DDP protocol. */
export type DdpMessage = {
  msg: string;
  id?: number | string;
  method?: string;
  params?: unknown[];
  result?: unknown;
  error?: { message?: string; errorType?: string };
  session?: string;
  version?: string;
  support?: string[];
};

/** The socket the client talks over. */
export type Socket = {
  send(payload: string): void;
  close(): void;
  onMessage(handler: (data: string) => void): void;
  onClose(handler: () => void): void;
  /** Lets a test push a message as if the server had sent it. */
  push?(data: string): void;
};

/** The state of the connection. */
export type ConnectionState = 'idle' | 'connecting' | 'connected' | 'closed' | 'error';

export class DdpError extends Error {
  errorType: string;

  constructor(message: string, errorType = 'error') {
    super(message);
    this.name = 'DdpError';
    this.errorType = errorType;
  }
}

/** The ping that keeps the connection alive, in the DDP way. */
export const PING_METHOD = 'ping';

/** The call that lists the channels. */
export const LIST_CHANNELS = 'channels.list';

/** The call that sends a message. */
export const SEND_MESSAGE = 'chat.sendMessage';

/** The call that reads the messages of a channel. */
export const LIST_MESSAGES = 'chat.getMessages';

/**
 * The DDP client.
 *
 * Every call answers with a promise. A call that the server refuses is a
 * DdpError with the message of the server.
 */
export class DdpClient {
  private socket: Socket | null = null;
  private nextId = 1;
  private pending = new Map<number, { resolve: (value: unknown) => void; reject: (error: Error) => void }>();
  private messageHandler: ((message: DdpMessage) => void) | null = null;
  private currentState: ConnectionState = 'idle';

  private socketFactory: (url: string) => Socket;

  constructor(socketFactory: (url: string) => Socket) {
    this.socketFactory = socketFactory;
  }

  /** The state of the connection. */
  get state(): ConnectionState {
    return this.currentState;
  }

  /** The answers the server sends on its own, such as the messages of a channel. */
  onMessage(handler: (message: DdpMessage) => void): void {
    this.messageHandler = handler;
  }

  /** Open the connection and wait for the server to accept it. */
  connect(url: string, timeout = 10000): Promise<string> {
    if (this.socket) this.close();
    this.currentState = 'connecting';

    return new Promise((resolve, reject) => {
      let socket: Socket;
      try {
        socket = this.socketFactory(url);
      } catch (error) {
        this.currentState = 'error';
        reject(error instanceof Error ? error : new Error('the socket could not be opened'));
        return;
      }
      this.socket = socket;

      const timer = setTimeout(() => {
        this.currentState = 'error';
        reject(new DdpError('the server did not answer in time', 'timeout'));
      }, timeout);

      socket.onMessage((data) => {
        let message: DdpMessage;
        try {
          message = JSON.parse(data) as DdpMessage;
        } catch {
          return;
        }

        if (message.msg === 'connected') {
          clearTimeout(timer);
          this.currentState = 'connected';
          resolve(message.session ?? '');
          return;
        }

        if (message.msg === 'result' && typeof message.id === 'number') {
          const waiting = this.pending.get(message.id);
          if (!waiting) return;
          this.pending.delete(message.id);
          if (message.error) {
            waiting.reject(new DdpError(message.error.message ?? 'the call failed', message.error.errorType));
          } else {
            waiting.resolve(message.result);
          }
          return;
        }

        if (message.msg === 'ping') {
          this.raw({ msg: 'pong', id: message.id });
          return;
        }

        this.messageHandler?.(message);
      });

      socket.onClose(() => {
        this.currentState = 'closed';
        for (const waiting of this.pending.values()) {
          waiting.reject(new DdpError('the connection was closed', 'closed'));
        }
        this.pending.clear();
      });

      this.raw({ msg: 'connect', version: '1', support: ['1'] });
    });
  }

  /** Send a message without waiting for an answer. */
  raw(message: DdpMessage): void {
    this.socket?.send(JSON.stringify(message));
  }

  /** Call a method and wait for the answer. */
  call(method: string, params: unknown[] = [], timeout = 10000): Promise<unknown> {
    if (!this.socket) return Promise.reject(new DdpError('there is no connection', 'no-connection'));
    const id = this.nextId;
    this.nextId += 1;

    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        this.pending.delete(id);
        reject(new DdpError(`${method} timed out`, 'timeout'));
      }, timeout);

      this.pending.set(id, {
        resolve: (value) => {
          clearTimeout(timer);
          resolve(value);
        },
        reject: (error) => {
          clearTimeout(timer);
          reject(error);
        },
      });

      this.raw({ msg: 'method', method, params, id });
    });
  }

  /** Close the connection. */
  close(): void {
    this.socket?.close();
    this.socket = null;
    this.currentState = 'closed';
  }
}

/** The channels of the answer of the server. */
export function toChannels(raw: unknown): Channel[] {
  if (!Array.isArray(raw)) return [];
  return raw
    .filter((item): item is Record<string, unknown> => typeof item === 'object' && item !== null)
    .map((item) => ({
      id: String(item._id ?? item.id ?? ''),
      name: String(item.name ?? ''),
      topic: String(item.topic ?? ''),
      unread: Number(item.unread ?? 0),
      members: Number(item.membersCount ?? item.members ?? 0),
      private: Boolean(item.private),
    }))
    .filter((channel) => channel.id !== '');
}

/** The user name of the sender of a message, when the server sent one. */
function readUsername(item: Record<string, unknown>): string | undefined {
  const user = item.u;
  if (typeof user !== 'object' || user === null) return undefined;
  const username = (user as Record<string, unknown>).username;
  return typeof username === 'string' ? username : undefined;
}

/** The messages of the answer of the server. */
export function toMessages(raw: unknown): ChatMessage[] {
  if (!Array.isArray(raw)) return [];
  return raw
    .filter((item): item is Record<string, unknown> => typeof item === 'object' && item !== null)
    .map((item) => ({
      id: String(item._id ?? item.id ?? ''),
      channelId: String(item.channelId ?? item.rid ?? ''),
      sender: String(readUsername(item) ?? item.sender ?? 'unknown'),
      body: String(item.msg ?? item.body ?? ''),
      time: String(item.ts ?? item.time ?? ''),
    }))
    .filter((message) => message.id !== '');
}

/** The unread count of every channel. */
export function unreadCounts(channels: Channel[]): Record<string, number> {
  const counts: Record<string, number> = {};
  for (const channel of channels) counts[channel.id] = channel.unread;
  return counts;
}

/** The messages of one channel, oldest first. */
export function messagesOf(messages: ChatMessage[], channelId: string): ChatMessage[] {
  return messages.filter((message) => message.channelId === channelId);
}

/** The channels that have something unread, with the most unread first. */
export function channelsWithUnread(channels: Channel[]): Channel[] {
  return channels.filter((channel) => channel.unread > 0).sort((left, right) => right.unread - left.unread);
}

/** Add a message to the list, keeping the order. */
export function appendMessage(messages: ChatMessage[], message: ChatMessage): ChatMessage[] {
  return [...messages, message];
}

/** The message that is sent, in the shape the server takes. */
export function toSendMessage(channelId: string, body: string, mine = true): ChatMessage {
  return {
    id: `local-${Date.now()}`,
    channelId,
    sender: 'You',
    body: body.trim(),
    time: 'now',
    mine,
  };
}
