import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { ChatStore, type KeyValueStore } from './store';
import {
  DdpClient,
  LIST_CHANNELS,
  LIST_MESSAGES,
  SEND_MESSAGE,
  appendMessage,
  toChannels,
  toMessages,
  toSendMessage,
  type Channel,
  type ChatMessage,
  type ConnectionState,
  type Socket,
} from './chat';
import { channels as seedChannels, initialMessages as seedMessages } from './data';

const backend: KeyValueStore = {
  getItem: (key) => AsyncStorage.getItem(key),
  setItem: (key, value) => AsyncStorage.setItem(key, value),
  removeItem: (key) => AsyncStorage.removeItem(key),
};

const store = new ChatStore(backend);

/** The server the app talks to. */
export const CHAT_SERVER = process.env.EXPO_PUBLIC_CHAT_URL ?? 'wss://chat.school.example/websocket';

type ChatContextValue = {
  channels: Channel[];
  messages: ChatMessage[];
  connection: ConnectionState;
  error: string | null;
  /** Send a message in a channel. */
  send(channelId: string, body: string): void;
  /** Connect to the server again. */
  reconnect(): void;
};

const ChatContext = createContext<ChatContextValue | null>(null);

/**
 * The websocket the client talks over.
 *
 * React Native has a websocket, and the tests give the client another one.
 */
function createSocket(url: string): Socket {
  const socket = new WebSocket(url);
  let onMessage: (data: string) => void = () => {};
  let onClose: () => void = () => {};

  socket.onmessage = (event) => onMessage(String(event.data));
  socket.onclose = () => onClose();
  socket.onerror = () => onClose();

  return {
    send(payload) {
      if (socket.readyState === WebSocket.OPEN) socket.send(payload);
    },
    close() {
      socket.close();
    },
    onMessage(handler) {
      onMessage = handler;
    },
    onClose(handler) {
      onClose = handler;
    },
  };
}

/** Holds the channels and the messages, and keeps the connection alive. */
export function ChatProvider({ children }: { children: React.ReactNode }) {
  const [channels, setChannels] = useState<Channel[]>(seedChannels);
  const [messages, setMessages] = useState<ChatMessage[]>(seedMessages);
  const [connection, setConnection] = useState<ConnectionState>('idle');
  const [error, setError] = useState<string | null>(null);
  const [client, setClient] = useState<DdpClient | null>(null);

  const connect = useCallback(async () => {
    const next = new DdpClient(createSocket);
    setClient(next);

    next.onMessage((message) => {
      // The server pushes the messages of a channel.
      if (message.method === LIST_MESSAGES) {
        const received = toMessages(message.params?.[0]);
        if (received.length) {
          setMessages((current) => [...current, ...received]);
        }
      }
    });

    try {
      await next.connect(CHAT_SERVER);
      setConnection('connected');
      setError(null);

      const answer = await next.call(LIST_CHANNELS);
      const received = toChannels(answer);
      if (received.length) {
        setChannels(received);
        await store.saveChannels(received);
      }
    } catch (failure) {
      setConnection('error');
      setError(failure instanceof Error ? failure.message : 'The server could not be reached.');
    }
  }, []);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      const cachedChannels = await store.channels();
      const cachedMessages = await store.messages();
      if (cancelled) return;
      if (cachedChannels?.length) setChannels(cachedChannels);
      if (cachedMessages?.length) setMessages(cachedMessages);
      await connect();
    })();

    return () => {
      cancelled = true;
    };
  }, [connect]);

  useEffect(() => {
    void store.saveMessages(messages);
  }, [messages]);

  const send = useCallback(
    (channelId: string, body: string) => {
      const text = body.trim();
      if (!text) return;

      const message = toSendMessage(channelId, text);
      setMessages((current) => appendMessage(current, message));

      if (client && connection === 'connected') {
        client.call(SEND_MESSAGE, [channelId, text]).catch((failure: Error) => {
          setError(failure.message);
        });
      }
    },
    [client, connection],
  );

  const value = useMemo(
    () => ({ channels, messages, connection, error, send, reconnect: connect }),
    [channels, messages, connection, error, send, connect],
  );

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>;
}

/** The state of the chat. Throws when it is used outside the provider. */
export function useChat(): ChatContextValue {
  const value = useContext(ChatContext);
  if (!value) throw new Error('useChat must be used inside a ChatProvider');
  return value;
}
