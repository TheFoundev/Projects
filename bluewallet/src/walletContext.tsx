import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { walletStore } from './persistence';
import {
  DemoWalletCore,
  balanceOf,
  type Balance,
  type Transaction,
  type UnsignedTransaction,
  type WalletCore,
} from './wallet-core';
import { seedTransactions } from './data';

type WalletContextValue = {
  core: WalletCore;
  balance: Balance;
  transactions: Transaction[];
  ready: boolean;
  /** Build and broadcast a payment. Returns the transaction id. */
  send(address: string, amountSats: number): Promise<string>;
  /** The fee the next payment would cost. */
  quoteFee(amountSats: number): Promise<number>;
};

const WalletContext = createContext<WalletContextValue | null>(null);

/** Holds the wallet state and keeps it in sync with the core. */
export function WalletProvider({
  children,
  core: injected,
}: {
  children: React.ReactNode;
  core?: WalletCore;
}) {
  const core = useMemo(() => injected ?? new DemoWalletCore(seedTransactions), [injected]);
  const [balance, setBalance] = useState<Balance>({ confirmed: 0, unconfirmed: 0 });
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [ready, setReady] = useState(false);

  const refresh = useCallback(async () => {
    const [nextBalance, nextTransactions] = await Promise.all([
      core.getBalance(),
      core.getTransactions(),
    ]);
    setBalance(nextBalance);
    setTransactions(nextTransactions);
    await walletStore.save({ transactions: nextTransactions, address: core.address });
  }, [core]);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      const saved = await walletStore.load();
      if (!cancelled && saved.transactions.length > 0) setTransactions(saved.transactions);

      try {
        await refresh();
      } catch {
        // The server is unreachable: keep whatever was saved.
        if (!cancelled && saved.transactions.length > 0) {
          setBalance(balanceOf(saved.transactions));
        }
      }
      if (!cancelled) setReady(true);
    })();

    return () => {
      cancelled = true;
    };
  }, [refresh]);

  const send = useCallback(
    async (address: string, amountSats: number) => {
      const tx: UnsignedTransaction = await core.buildTransaction(address, amountSats);
      const id = await core.broadcast(tx);
      await refresh();
      return id;
    },
    [core, refresh],
  );

  const quoteFee = useCallback(
    async (amountSats: number) => {
      const utxos = await core.listUnspent();
      if (utxos.length === 0) return 0;
      const result = await core.buildTransaction(core.address, amountSats).catch(() => null);
      return result ? result.fee : 0;
    },
    [core],
  );

  const value = useMemo(
    () => ({ core, balance, transactions, ready, send, quoteFee }),
    [core, balance, transactions, ready, send, quoteFee],
  );

  return <WalletContext.Provider value={value}>{children}</WalletContext.Provider>;
}

/** The wallet state. Throws when it is used outside the provider. */
export function useWallet(): WalletContextValue {
  const value = useContext(WalletContext);
  if (!value) throw new Error('useWallet must be used inside a WalletProvider');
  return value;
}
