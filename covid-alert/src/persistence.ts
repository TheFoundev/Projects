/**
 * Wires the check history to AsyncStorage.
 *
 * This module is the only one that imports a native package, so the rest of
 * the app stays testable outside a React Native runtime.
 */

import AsyncStorage from '@react-native-async-storage/async-storage';
import { CheckStore, type KeyValueStore } from './store';

const backend: KeyValueStore = {
  getItem: (key) => AsyncStorage.getItem(key),
  setItem: (key, value) => AsyncStorage.setItem(key, value),
  removeItem: (key) => AsyncStorage.removeItem(key),
};

/** The store the app uses. */
export const checkStore = new CheckStore(backend);
