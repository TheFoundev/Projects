import test from 'node:test';
import assert from 'node:assert';

import { WalletStore, createMemoryStore } from '../src/store';
import type { Transaction } from '../src/wallet-core';

const transaction: Transaction = {
  id: 't1',
  type: 'received',
  amountSats: 82000,
  counterparty: 'bc1q…9x2f',
  date: 'Apr 22, 10:14',
  status: 'confirmed',
};

test('the wallet store round-trips the state', async () => {
  const store = new WalletStore(createMemoryStore());
  await store.save({ transactions: [transaction], address: 'bc1qexample' });

  const loaded = await store.load();
  assert.equal(loaded.transactions.length, 1);
  assert.equal(loaded.transactions[0].id, 't1');
  assert.equal(loaded.address, 'bc1qexample');
});

test('the wallet store returns an empty state when nothing was saved', async () => {
  const store = new WalletStore(createMemoryStore());
  assert.deepEqual(await store.load(), { transactions: [], address: '' });
});

test('the wallet store survives a corrupt saved value', async () => {
  const backend = createMemoryStore();
  await backend.setItem('bluewallet.wallet.v1', '{{{not json');
  const store = new WalletStore(backend);

  assert.deepEqual(await store.load(), { transactions: [], address: '' });
});

test('the wallet store keeps working when the backend fails', async () => {
  const failing = {
    async getItem() { throw new Error('storage unavailable'); },
    async setItem() { throw new Error('storage unavailable'); },
    async removeItem() { throw new Error('storage unavailable'); },
  };
  const store = new WalletStore(failing);

  assert.deepEqual(await store.load(), { transactions: [], address: '' });
  assert.equal(await store.save({ transactions: [], address: '' }), false);
});

test('the wallet store can be cleared', async () => {
  const store = new WalletStore(createMemoryStore());
  await store.save({ transactions: [transaction], address: 'bc1qexample' });
  await store.clear();

  assert.deepEqual(await store.load(), { transactions: [], address: '' });
});
