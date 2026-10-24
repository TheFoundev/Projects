/**
 * The wallet core.
 *
 * The screens talk to this interface, never to a network library directly.
 * Two implementations exist:
 *
 *   DemoWalletCore       the offline wallet the app ships with
 *   ElectrumWalletCore   a real client for an Electrum server
 *
 * Both answer the same questions, so the UI is identical whether the app is
 * online or not, and both can be unit tested.
 */

import { isValidAddress, scriptHashFromSegwitAddress } from './address';

export type Transaction = {
  id: string;
  type: 'received' | 'sent';
  amountSats: number;
  counterparty: string;
  date: string;
  status: 'confirmed' | 'pending';
};

export type Utxo = {
  tx_hash: string;
  tx_pos: number;
  value: number;
  height: number;
};

export type Balance = {
  confirmed: number;
  unconfirmed: number;
};

export type UnsignedTransaction = {
  inputs: Utxo[];
  outputs: { address: string; value: number }[];
  fee: number;
  total: number;
  change: number;
};

/** What the app needs from a wallet. */
export type WalletCore = {
  readonly name: string;
  readonly address: string;
  getBalance(): Promise<Balance>;
  getTransactions(): Promise<Transaction[]>;
  listUnspent(): Promise<Utxo[]>;
  /** Build an unsigned transaction, or throw with a message for the user. */
  buildTransaction(address: string, amountSats: number): Promise<UnsignedTransaction>;
  /** Broadcast a transaction and return its id. */
  broadcast(tx: UnsignedTransaction): Promise<string>;
};

/** The fee a transaction costs, for a given size estimate. */
export function estimateFee(inputCount: number, outputCount: number, feeRate = 2): number {
  // A native segwit input is about 68 vbytes, an output about 31.
  const vbytes = 11 + inputCount * 68 + outputCount * 31;
  return Math.max(141, vbytes * feeRate);
}

/**
 * Pick the UTXOs to spend.
 *
 * Largest first, which keeps the number of inputs (and the fee) down.
 * Returns null when the wallet does not hold enough.
 */
export function selectUtxos(utxos: Utxo[], targetSats: number): Utxo[] | null {
  const sorted = [...utxos].sort((a, b) => b.value - a.value);
  const chosen: Utxo[] = [];
  let total = 0;

  for (const utxo of sorted) {
    if (total >= targetSats) break;
    chosen.push(utxo);
    total += utxo.value;
  }

  return total >= targetSats ? chosen : null;
}

/**
 * Build an unsigned transaction from the available UTXOs.
 *
 * Returns an error message instead of a transaction when the address is
 * wrong, the amount is not a positive integer, or the wallet cannot cover
 * the amount plus the fee.
 */
export function buildUnsignedTransaction(
  utxos: Utxo[],
  address: string,
  amountSats: number,
  feeRate = 2,
): { tx: UnsignedTransaction } | { error: string } {
  if (!isValidAddress(address)) {
    return { error: 'That does not look like a Bitcoin address.' };
  }
  if (!Number.isInteger(amountSats) || amountSats <= 0) {
    return { error: 'Enter an amount in satoshis.' };
  }

  // Estimate the fee with a change output, then try again without it if the
  // change would be dust.
  let fee = estimateFee(1, 2, feeRate);
  let inputs = selectUtxos(utxos, amountSats + fee);

  if (!inputs) {
    // A single input may be enough once the fee is known.
    const single = selectUtxos(utxos, amountSats);
    if (!single) return { error: 'Not enough funds in this wallet.' };
    fee = estimateFee(single.length, 2, feeRate);
    inputs = selectUtxos(utxos, amountSats + fee);
    if (!inputs) return { error: 'Not enough funds in this wallet, once the fee is paid.' };
  }

  const total = inputs.reduce((sum, utxo) => sum + utxo.value, 0);
  const change = total - amountSats - fee;

  if (change < 0) return { error: 'Not enough funds in this wallet, once the fee is paid.' };

  const outputs = [{ address, value: amountSats }];
  if (change >= 546) outputs.push({ address: '', value: change });

  return {
    tx: {
      inputs,
      outputs,
      fee,
      total,
      change: change >= 546 ? change : 0,
    },
  };
}

/** The balance a list of transactions adds up to. */
export function balanceOf(transactions: Transaction[]): Balance {
  let confirmed = 0;
  let unconfirmed = 0;

  for (const transaction of transactions) {
    const signed = transaction.type === 'received' ? transaction.amountSats : -transaction.amountSats;
    if (transaction.status === 'confirmed') confirmed += signed;
    else unconfirmed += signed;
  }

  return { confirmed, unconfirmed };
}

/** The offline wallet the app ships with. */
export class DemoWalletCore implements WalletCore {
  name = 'Everyday wallet';
  address = 'bc1qdemo0x7f3k9m2n8p4r6t0v5w1y2z3a4b5c6d7e8';

  private transactions: Transaction[];
  private utxos: Utxo[];

  constructor(transactions: Transaction[] = [], utxos?: Utxo[]) {
    this.transactions = [...transactions];
    this.utxos = utxos ?? transactions.map((transaction, index) => ({
      tx_hash: `demo${index}`,
      tx_pos: 0,
      value: transaction.amountSats,
      height: 800000 + index,
    }));
  }

  async getBalance(): Promise<Balance> {
    return balanceOf(this.transactions);
  }

  async getTransactions(): Promise<Transaction[]> {
    return [...this.transactions];
  }

  async listUnspent(): Promise<Utxo[]> {
    return [...this.utxos];
  }

  async buildTransaction(address: string, amountSats: number): Promise<UnsignedTransaction> {
    const result = buildUnsignedTransaction(this.utxos, address, amountSats);
    if ('error' in result) throw new Error(result.error);
    return result.tx;
  }

  async broadcast(tx: UnsignedTransaction): Promise<string> {
    const id = `demo-${tx.inputs.length}-${tx.total}`;
    this.transactions = [
      {
        id,
        type: 'sent',
        amountSats: tx.outputs[0].value,
        counterparty: tx.outputs[0].address,
        date: 'just now',
        status: 'pending',
      },
      ...this.transactions,
    ];
    return id;
  }
}

/** The transport the Electrum client talks over. */
export type Transport = {
  send(payload: string): void;
  close(): void;
  onMessage(handler: (data: string) => void): void;
  onClose(handler: () => void): void;
};

export type TransportFactory = (url: string) => Transport;

/**
 * A client for an Electrum server.
 *
 * The protocol is JSON-RPC over a websocket: every request has an id and a
 * method, and the answer carries the same id.
 */
export class ElectrumWalletCore implements WalletCore {
  name: string;
  address: string;

  private transport: Transport | null = null;
  private nextId = 1;
  private pending = new Map<number, { resolve: (value: unknown) => void; reject: (error: Error) => void }>();
  private scriptHash: string;

  constructor(options: {
    address: string;
    name?: string;
    host?: string;
    port?: number;
    protocol?: 'tcp' | 'ssl' | 'ws' | 'wss';
    transportFactory: TransportFactory;
  }) {
    this.address = options.address;
    this.name = options.name ?? 'Bitcoin wallet';

    const scriptHash = scriptHashFromSegwitAddress(options.address);
    if (!scriptHash) throw new Error('Only native segwit addresses are supported.');
    this.scriptHash = scriptHash;

    this.transportFactory = options.transportFactory;
    this.host = options.host ?? 'electrum.blockstream.info';
    this.port = options.port ?? 50002;
    this.protocol = options.protocol ?? 'ssl';
  }

  private host: string;
  private port: number;
  private protocol: string;
  private transportFactory: TransportFactory;

  /** Open the connection, if it is not open already. */
  connect(): Transport {
    if (this.transport) return this.transport;

    const url = `${this.protocol}://${this.host}:${this.port}`;
    const transport = this.transportFactory(url);

    transport.onMessage((data) => {
      let message: { id?: number; result?: unknown; error?: { message?: string } };
      try {
        message = JSON.parse(data);
      } catch {
        return;
      }
      if (typeof message.id !== 'number') return;
      const waiting = this.pending.get(message.id);
      if (!waiting) return;
      this.pending.delete(message.id);
      if (message.error) waiting.reject(new Error(message.error.message ?? 'electrum error'));
      else waiting.resolve(message.result);
    });

    transport.onClose(() => {
      for (const waiting of this.pending.values()) waiting.reject(new Error('the connection closed'));
      this.pending.clear();
      this.transport = null;
    });

    this.transport = transport;
    return transport;
  }

  /** Send one JSON-RPC request and wait for the answer. */
  async call(method: string, params: unknown[]): Promise<unknown> {
    const transport = this.connect();
    const id = this.nextId;
    this.nextId += 1;

    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        this.pending.delete(id);
        reject(new Error(`${method} timed out`));
      }, 15000);

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

      transport.send(JSON.stringify({ jsonrpc: '2.0', id, method, params }));
    });
  }

  async getBalance(): Promise<Balance> {
    const result = (await this.call('blockchain.scripthash.get_balance', [this.scriptHash])) as {
      confirmed: number;
      unconfirmed: number;
    };
    return { confirmed: result.confirmed, unconfirmed: result.unconfirmed };
  }

  async listUnspent(): Promise<Utxo[]> {
    const result = (await this.call('blockchain.scripthash.listunspent', [this.scriptHash])) as Utxo[];
    return result ?? [];
  }

  async getTransactions(): Promise<Transaction[]> {
    const history = (await this.call('blockchain.scripthash.get_history', [this.scriptHash])) as {
      tx_hash: string;
      height: number;
    }[];
    const transactions: Transaction[] = [];

    for (const entry of history ?? []) {
      const raw = (await this.call('blockchain.transaction.get', [entry.tx_hash, true])) as {
        txid: string;
        vin: { prevout?: { value: number; scriptPubKey?: { addresses?: string[] } } }[];
        vout: { value: number; scriptPubKey?: { addresses?: string[] } }[];
      };

      const received = raw.vout
        .filter((output) => output.scriptPubKey?.addresses?.includes(this.address))
        .reduce((sum, output) => sum + Math.round(output.value * 100_000_000), 0);

      const spent = raw.vin
        .filter((input) => input.prevout?.scriptPubKey?.addresses?.includes(this.address))
        .reduce((sum, input) => sum + Math.round((input.prevout?.value ?? 0) * 100_000_000), 0);

      const amount = received - spent;
      if (amount === 0) continue;

      transactions.push({
        id: raw.txid,
        type: amount > 0 ? 'received' : 'sent',
        amountSats: Math.abs(amount),
        counterparty: '—',
        date: entry.height > 0 ? 'confirmed' : 'pending',
        status: entry.height > 0 ? 'confirmed' : 'pending',
      });
    }

    return transactions;
  }

  async buildTransaction(address: string, amountSats: number): Promise<UnsignedTransaction> {
    const utxos = await this.listUnspent();
    const result = buildUnsignedTransaction(utxos, address, amountSats);
    if ('error' in result) throw new Error(result.error);
    return result.tx;
  }

  async broadcast(tx: UnsignedTransaction): Promise<string> {
    const hex = (await this.call('blockchain.transaction.broadcast', [tx])) as string;
    return hex;
  }
}
