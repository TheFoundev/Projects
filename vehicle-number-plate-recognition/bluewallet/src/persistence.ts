/**
 * Wires the wallet to the device: AsyncStorage for the local copy and a
 * websocket for the Electrum server.
 *
 * This module is the only one that imports a native package, so the rest of
 * the app stays testable outside a React Native runtime.
 */

import AsyncStorage from '@react-native-async-storage/async-storage';
import { WalletStore, type KeyValueStore } from './store';
import type { Transport, TransportFactory } from './wallet-core';

const backend: KeyValueStore = {
  getItem: (key) => AsyncStorage.getItem(key),
  setItem: (key, value) => AsyncStorage.setItem(key, value),
  removeItem: (key) => AsyncStorage.removeItem(key),
};

/** The store the app uses. */
export const walletStore = new WalletStore(backend);

/**
 * A transport over the websocket API of React Native.
 *
 * Electrum speaks JSON-RPC over a websocket, so the only thing the client
 * needs is a way to send text and to be told when text arrives.
 */
export const websocketTransport: TransportFactory = (url) => {
  const socket = new WebSocket(url);
  let messageHandler: (data: string) => void = () => {};
  let closeHandler: () => void = () => {};

  socket.onmessage = (event) => messageHandler(String(event.data));
  socket.onclose = () => closeHandler();
  socket.onerror = () => closeHandler();

  return {
    send(payload) {
      if (socket.readyState === WebSocket.OPEN) socket.send(payload);
    },
    close() {
      socket.close();
    },
    onMessage(handler) {
      messageHandler = handler;
    },
    onClose(handler) {
      closeHandler = handler;
    },
  };
};
