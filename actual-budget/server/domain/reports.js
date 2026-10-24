/** Report aggregations. Pure: rows in, rows out. */

import { addMonths, monthBounds } from './dates.js';
import { isLiability } from './accounts.js';

/** A transaction that is one leg of a transfer (excluded from spending). */
export function isTransfer(tx) {
  return tx.transfer_account_id != null;
}

/** The last `count` months ending at `endMonth`, oldest first. */
export function lastMonths(count, endMonth) {
  const months = [];
  for (let i = count - 1; i >= 0; i -= 1) months.push(addMonths(endMonth, -i));
  return months;
}

/**
 * Assets, liabilities and net worth at the end of each month.
 * Balances accumulate, so month n includes everything up to its last day.
 */
export function netWorthSeries({ accounts = [], transactions = [], months = [] } = {}) {
  const live = accounts.filter((a) => !a.deleted);
  const balances = new Map(live.map((a) => [a.id, 0]));
  const assetIds = new Set(live.filter((a) => !isLiability(a.type)).map((a) => a.id));

  const sorted = transactions
    .filter((t) => !t.deleted && balances.has(t.account_id))
    .slice()
    .sort((a, b) => (a.date < b.date ? -1 : a.date > b.date ? 1 : 0));

  const out = [];
  let i = 0;

  for (const month of months) {
    const end = monthBounds(month).end;
    while (i < sorted.length && sorted[i].date <= end) {
      const tx = sorted[i];
      i += 1;
      balances.set(tx.account_id, balances.get(tx.account_id) + (Number(tx.amount_cents) || 0));
    }

    let assets = 0;
    let liabilities = 0;
    for (const [id, balance] of balances) {
      if (assetIds.has(id)) assets += balance;
      else liabilities += balance;
    }

    out.push({
      month: months[months.indexOf(month)] ?? month,
      assets,
      liabilities,          // signed: money owed is negative
      debt: -liabilities,   // positive figure for a chart
      net: assets + liabilities,
    });
  }

  return out;
}

/** Spending (negative amounts only) per category for one month. */
export function spendingByCategory({ transactions = [], categories = [], month } = {}) {
  const { start, end } = monthBounds(month);
  const nameById = new Map(categories.filter((c) => !c.deleted).map((c) => [c.id, c.name]));
  const totals = new Map();

  for (const tx of transactions) {
    if (tx.deleted || tx.category_id == null) continue;
    if (tx.date < start || tx.date > end) continue;
    if (isTransfer(tx)) continue;
    const amount = Number(tx.amount_cents) || 0;
    if (amount >= 0) continue;
    totals.set(tx.category_id, (totals.get(tx.category_id) || 0) + amount);
  }

  return [...totals.entries()]
    .map(([category_id, total]) => ({
      category_id,
      name: nameById.get(category_id) || `Category ${category_id}`,
      total,
    }))
    .sort((a, b) => a.total - b.total);
}

/** Income vs expense per month. Transfers are excluded so nothing double-counts. */
export function cashFlowSeries({ transactions = [], months = [] } = {}) {
  return months.map((month) => {
    const { start, end } = monthBounds(month);
    let income = 0;
    let expense = 0;

    for (const tx of transactions) {
      if (tx.deleted || isTransfer(tx)) continue;
      if (tx.date < start || tx.date > end) continue;
      const amount = Number(tx.amount_cents) || 0;
      if (amount >= 0) income += amount;
      else expense += amount;
    }

    return { month, income, expense, net: income + expense };
  });
}
