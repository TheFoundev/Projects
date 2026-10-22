export type Transaction = {
  id: string;
  type: 'received' | 'sent';
  amountSats: number;
  counterparty: string;
  date: string;
  status: 'confirmed' | 'pending';
};

/**
 * The demo wallet the app ships with.
 *
 * The balance is not a constant any more: it is the sum of the transactions
 * below, which the wallet core computes.
 */
export const seedTransactions: Transaction[] = [
  { id: 't1', type: 'received', amountSats: 82000, counterparty: 'bc1q…9x2f', date: 'Apr 22, 10:14', status: 'confirmed' },
  { id: 't2', type: 'sent', amountSats: 24000, counterparty: 'bc1q…7m1k', date: 'Apr 20, 16:02', status: 'confirmed' },
  { id: 't3', type: 'received', amountSats: 90500, counterparty: 'bc1q…4v8p', date: 'Apr 18, 09:30', status: 'confirmed' },
  { id: 't4', type: 'sent', amountSats: 12000, counterparty: 'Lightning invoice', date: 'Apr 17, 21:14', status: 'pending' },
];

export function formatSats(value: number): string {
  return value.toLocaleString('en-US');
}

export function satsToBtc(value: number): string {
  return (value / 100_000_000).toFixed(8);
}
