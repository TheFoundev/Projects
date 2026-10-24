/**
 * The bridge to AsyncStorage.
 *
 * This is the only module of the app that imports a native package, so the
 * rest of the code stays testable outside a React Native runtime.
 */

import AsyncStorage from '@react-native-async-storage/async-storage';

import type { KeyValueStore } from './settings';

/** AsyncStorage, seen as a key/value store. */
export const asyncStorageStore: KeyValueStore = {
  getItem: (key: string) => AsyncStorage.getItem(key),
  setItem: (key: string, value: string) => AsyncStorage.setItem(key, value),
  removeItem: (key: string) => AsyncStorage.removeItem(key),
};
