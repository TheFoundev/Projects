import test from 'node:test';
import assert from 'node:assert';

import { sha256Hex, sha256HexReversed } from '../src/sha256';
import {
  decodeBech32,
  isValidBech32,
  isValidSegwitAddress,
  isValidBase58Address,
  isValidAddress,
  scriptHashFromSegwitAddress,
} from '../src/address';
import {
  buildUnsignedTransaction,
  selectUtxos,
  estimateFee,
  balanceOf,
  DemoWalletCore,
  ElectrumWalletCore,
  type Transaction,
  type Utxo,
  type Transport,
} from '../src/wallet-core';

// A real mainnet address (BIP-173 test vector).
const VALID_SEGWIT = 'bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4';
const VALID_P2WPKH = 'bc1qrp33g0q5c5txsp9arysrx4k6zdkfs4nce4xj0gdcccefvpysxf3qccfmv3';

test('sha256 matches the known digest of the empty string', () => {
  assert.equal(
    sha256Hex(''),
    'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
  );
});

test('sha256 matches the known digest of "abc"', () => {
  assert.equal(
    sha256Hex('abc'),
    'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad',
  );
});

test('sha256 matches the known digest of a long input', () => {
  assert.equal(
    sha256Hex('abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq'),
    '248d6a61d20638b8e5c026930c3e6039a33ce45964ff2167f6ecedd419db06c1',
  );
});

test('the pure TypeScript sha256 agrees with the reference implementation', async () => {
  const { createHash } = await import('node:crypto');
  for (const input of ['', 'abc', 'a'.repeat(200), 'the quick brown fox']) {
    assert.equal(sha256Hex(input), createHash('sha256').update(input).digest('hex'), `digest of ${input.length} bytes`);
  }
});

test('the reversed hash is the digest with its bytes reversed', async () => {
  const { createHash } = await import('node:crypto');
  const bytes = new Uint8Array([1, 2, 3, 4]);
  const expected = Buffer.from(createHash('sha256').update(bytes).digest()).reverse().toString('hex');
  assert.equal(sha256HexReversed(bytes), expected);
});

test('a valid bech32 address decodes', () => {
  const decoded = decodeBech32(VALID_SEGWIT);
  assert.ok(decoded);
  assert.equal(decoded?.prefix, 'bc');
  assert.equal(decoded?.words.length, 33);
});

test('a corrupted checksum is rejected', () => {
  const broken = `${VALID_SEGWIT.slice(0, -1)}${VALID_SEGWIT.slice(-1) === '4' ? '5' : '4'}`;
  assert.equal(decodeBech32(broken), null);
  assert.equal(isValidBech32(broken), false);
});

test('a string that is not bech32 at all is rejected', () => {
  assert.equal(decodeBech32('not an address'), null);
  assert.equal(decodeBech32(''), null);
  assert.equal(decodeBech32('bc1'), null);
});

test('a native segwit address is valid', () => {
  assert.equal(isValidSegwitAddress(VALID_SEGWIT), true);
  assert.equal(isValidSegwitAddress(VALID_P2WPKH), true);
  assert.equal(isValidAddress(VALID_SEGWIT), true);
});

test('a legacy base58 address is valid', () => {
  assert.equal(isValidBase58Address('1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2'), true);
  assert.equal(isValidBase58Address('3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy'), true);
  assert.equal(isValidAddress('1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2'), true);
});

test('a made up address is rejected', () => {
  assert.equal(isValidAddress('hello world'), false);
  assert.equal(isValidAddress('0x1234567890abcdef'), false);
  assert.equal(isValidSegwitAddress('bc1qdemo0x7f3k9m2n8p4r6t0v5w1y2z3a4b5c6d7e8'), false);
});

test('the script hash of an address is 64 hex characters', () => {
  const hash = scriptHashFromSegwitAddress(VALID_SEGWIT);
  assert.ok(hash);
  assert.match(hash!, /^[0-9a-f]{64}$/);
});

test('the script hash is the sha256 of the output script, reversed', () => {
  // P2WPKH: OP_0 <20 byte program>. The witness program of the BIP-173
  // test vector is 751e76e8199196d454941c45d1b3a323f1433bd6, so the script
  // is 0014751e76e8199196d454941c45d1b3a323f1433bd6.
  const expected = '9623df75239b5daa7f5f03042d325b51498c4bb7059c7748b17049bf96f73888';
  assert.equal(scriptHashFromSegwitAddress(VALID_SEGWIT), expected);
});

test('a non segwit address has no script hash', () => {
  assert.equal(scriptHashFromSegwitAddress('1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2'), null);
});

test('selectUtxos picks the largest coins first', () => {
  const utxos: Utxo[] = [
    { tx_hash: 'a', tx_pos: 0, value: 1000, height: 1 },
    { tx_hash: 'b', tx_pos: 0, value: 5000, height: 1 },
    { tx_hash: 'c', tx_pos: 0, value: 2000, height: 1 },
  ];
  const chosen = selectUtxos(utxos, 6000);
  assert.ok(chosen);
  assert.deepEqual(chosen!.map((u) => u.tx_hash), ['b', 'c']);
  assert.equal(chosen!.reduce((sum, u) => sum + u.value, 0), 7000);
});

test('selectUtxos returns null when the wallet cannot cover the target', () => {
  const utxos: Utxo[] = [{ tx_hash: 'a', tx_pos: 0, value: 1000, height: 1 }];
  assert.equal(selectUtxos(utxos, 5000), null);
});

test('the fee grows with the number of inputs', () => {
  assert.ok(estimateFee(1, 2) < estimateFee(3, 2));
  assert.ok(estimateFee(1, 2) >= 141);
});

test('building a transaction rejects a bad address', () => {
  const result = buildUnsignedTransaction([], 'nope', 1000);
  assert.ok('error' in result);
  assert.match((result as { error: string }).error, /address/i);
});

test('building a transaction rejects a bad amount', () => {
  const result = buildUnsignedTransaction([], VALID_SEGWIT, 0);
  assert.ok('error' in result);
  assert.match((result as { error: string }).error, /amount/i);
});

test('building a transaction picks inputs, a fee and the change', () => {
  const utxos: Utxo[] = [{ tx_hash: 'a', tx_pos: 0, value: 100000, height: 1 }];
  const result = buildUnsignedTransaction(utxos, VALID_SEGWIT, 25000);
  assert.ok('tx' in result);

  const tx = (result as { tx: { inputs: Utxo[]; outputs: { value: number }[]; fee: number; change: number } }).tx;
  assert.equal(tx.inputs.length, 1);
  assert.equal(tx.outputs[0].value, 25000);
  assert.equal(tx.outputs.length, 2);
  assert.equal(tx.change, 100000 - 25000 - tx.fee);
  assert.equal(tx.fee, estimateFee(1, 2));
});

test('building a transaction fails when there is not enough money', () => {
  const utxos: Utxo[] = [{ tx_hash: 'a', tx_pos: 0, value: 1000, height: 1 }];
  const result = buildUnsignedTransaction(utxos, VALID_SEGWIT, 5000);
  assert.ok('error' in result);
  assert.match((result as { error: string }).error, /not enough funds/i);
});

test('the balance adds up the transactions', () => {
  const transactions: Transaction[] = [
    { id: '1', type: 'received', amountSats: 82000, counterparty: 'a', date: 'x', status: 'confirmed' },
    { id: '2', type: 'sent', amountSats: 24000, counterparty: 'b', date: 'x', status: 'confirmed' },
    { id: '3', type: 'sent', amountSats: 12000, counterparty: 'c', date: 'x', status: 'pending' },
  ];
  const balance = balanceOf(transactions);
  assert.equal(balance.confirmed, 58000);
  assert.equal(balance.unconfirmed, -12000);
});

test('the demo wallet reports a balance from its transactions', async () => {
  const core = new DemoWalletCore([
    { id: '1', type: 'received', amountSats: 100000, counterparty: 'a', date: 'x', status: 'confirmed' },
  ]);
  const balance = await core.getBalance();
  assert.equal(balance.confirmed, 100000);
});

test('the demo wallet broadcasts and records a pending transaction', async () => {
  const core = new DemoWalletCore([
    { id: '1', type: 'received', amountSats: 100000, counterparty: 'a', date: 'x', status: 'confirmed' },
  ]);

  const tx = await core.buildTransaction(VALID_SEGWIT, 25000);
  const id = await core.broadcast(tx);

  assert.ok(id);
  const transactions = await core.getTransactions();
  assert.equal(transactions[0].type, 'sent');
  assert.equal(transactions[0].status, 'pending');
});

test('the demo wallet refuses to build a transaction it cannot pay for', async () => {
  const core = new DemoWalletCore([
    { id: '1', type: 'received', amountSats: 1000, counterparty: 'a', date: 'x', status: 'confirmed' },
  ]);
  await assert.rejects(() => core.buildTransaction(VALID_SEGWIT, 50000), /not enough funds/i);
});

// ---------------------------------------------------------------------------
// The Electrum client
// ---------------------------------------------------------------------------

/** A transport that answers with canned responses. */
function fakeTransport(responses: Record<string, unknown>) {
  const sent: string[] = [];
  let onMessage: (data: string) => void = () => {};
  let onClose: () => void = () => {};

  const transport: Transport = {
    send(payload) {
      sent.push(payload);
      const request = JSON.parse(payload);
      const result = responses[request.method];
      if (result === undefined) {
        onMessage(JSON.stringify({ jsonrpc: '2.0', id: request.id, error: { message: 'unknown method' } }));
        return;
      }
      setTimeout(() => onMessage(JSON.stringify({ jsonrpc: '2.0', id: request.id, result })), 0);
    },
    close() { onClose(); },
    onMessage(handler) { onMessage = handler; },
    onClose(handler) { onClose = handler; },
  };

  return { transport, sent };
}

test('the Electrum client asks the server for the balance', async () => {
  const { transport, sent } = fakeTransport({
    'blockchain.scripthash.get_balance': { confirmed: 12345, unconfirmed: 67 },
  });

  const core = new ElectrumWalletCore({
    address: VALID_SEGWIT,
    transportFactory: () => transport,
  });

  const balance = await core.getBalance();
  assert.deepEqual(balance, { confirmed: 12345, unconfirmed: 67 });

  const request = JSON.parse(sent[0]);
  assert.equal(request.method, 'blockchain.scripthash.get_balance');
  assert.equal(request.params[0], '9623df75239b5daa7f5f03042d325b51498c4bb7059c7748b17049bf96f73888');
});

test('the Electrum client lists the unspent outputs', async () => {
  const { transport } = fakeTransport({
    'blockchain.scripthash.listunspent': [
      { tx_hash: 'aa', tx_pos: 0, value: 100000, height: 800000 },
    ],
  });

  const core = new ElectrumWalletCore({ address: VALID_SEGWIT, transportFactory: () => transport });
  const utxos = await core.listUnspent();
  assert.equal(utxos.length, 1);
  assert.equal(utxos[0].value, 100000);
});

test('the Electrum client turns a history into transactions', async () => {
  const { transport } = fakeTransport({
    'blockchain.scripthash.get_history': [{ tx_hash: 'bb', height: 800001 }],
    'blockchain.transaction.get': {
      txid: 'bb',
      vin: [],
      vout: [
        { value: 0.0005, scriptPubKey: { addresses: [VALID_SEGWIT] } },
        { value: 0.1, scriptPubKey: { addresses: ['bc1qother'] } },
      ],
    },
  });

  const core = new ElectrumWalletCore({ address: VALID_SEGWIT, transportFactory: () => transport });
  const transactions = await core.getTransactions();

  assert.equal(transactions.length, 1);
  assert.equal(transactions[0].type, 'received');
  assert.equal(transactions[0].amountSats, 50000);
  assert.equal(transactions[0].status, 'confirmed');
});

test('the Electrum client refuses a legacy address', () => {
  assert.throws(
    () => new ElectrumWalletCore({ address: '1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2', transportFactory: () => fakeTransport({}).transport }),
    /segwit/i,
  );
});
