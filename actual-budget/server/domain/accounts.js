/** Account classification and balances. Pure functions over plain rows. */

/** Account types that represent things you own. */
export const ASSET_TYPES = ['checking', 'savings', 'cash', 'investment', 'other'];

/** Account types that represent money you owe. */
export const LIABILITY_TYPES = ['credit', 'loan'];

export const ACCOUNT_TYPES = [...ASSET_TYPES, ...LIABILITY_TYPES];

export function isLiability(type) {
  return LIABILITY_TYPES.includes(type);
}

/** Balance per account id: the sum of its live transactions. @returns Map */
export function accountBalances(accounts, transactions) {
  const balances = new Map();
  for (const account of accounts) {
    if (account.deleted) continue;
    balances.set(account.id, 0);
  }
  for (const tx of transactions) {
    if (tx.deleted) continue;
    if (!balances.has(tx.account_id)) continue;
    balances.set(tx.account_id, balances.get(tx.account_id) + (Number(tx.amount_cents) || 0));
  }
  return balances;
}

/** Total across the accounts on the budget. */
export function onBudgetTotal(accounts, transactions) {
  const balances = accountBalances(accounts, transactions);
  let total = 0;
  for (const account of accounts) {
    if (account.deleted || !account.on_budget) continue;
    total += balances.get(account.id) || 0;
  }
  return total;
}
