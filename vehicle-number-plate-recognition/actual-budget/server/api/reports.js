/** Report endpoints. Thin wrappers over server/domain/reports.js. */

import { toPlainList } from '../util.js';
import { lastMonths, netWorthSeries, spendingByCategory, cashFlowSeries } from '../domain/reports.js';
import { accountBalances, isLiability } from '../domain/accounts.js';

function loadAccounts(db) {
  return toPlainList(db.prepare('SELECT * FROM accounts').all());
}

function loadTransactions(db) {
  return toPlainList(db.prepare('SELECT * FROM transactions').all());
}

function loadCategories(db) {
  return toPlainList(db.prepare('SELECT * FROM categories').all());
}

function endMonth(ctx, fallback) {
  const end = ctx.query.get('end');
  if (end && /^\d{4}-\d{2}$/.test(end)) return end;
  return fallback;
}

function monthCount(ctx, fallback = 12) {
  const n = Number(ctx.query.get('months'));
  return Number.isFinite(n) && n > 0 && n <= 120 ? Math.trunc(n) : fallback;
}

export function registerReports(router, db) {
  router.get('/api/reports/networth', (ctx) => {
    const months = lastMonths(monthCount(ctx), endMonth(ctx, new Date().toISOString().slice(0, 7)));
    return { months, series: netWorthSeries({ accounts: loadAccounts(db), transactions: loadTransactions(db), months }) };
  });

  router.get('/api/reports/spending', (ctx) => {
    const month = (ctx.query.get('month') || new Date().toISOString().slice(0, 7)).slice(0, 7);
    const rows = spendingByCategory({ transactions: loadTransactions(db), categories: loadCategories(db), month });
    const total = rows.reduce((acc, r) => acc + r.total, 0);
    return { month, total, categories: rows };
  });

  router.get('/api/reports/cashflow', (ctx) => {
    const months = lastMonths(monthCount(ctx), endMonth(ctx, new Date().toISOString().slice(0, 7)));
    return { months, series: cashFlowSeries({ transactions: loadTransactions(db), months }) };
  });

  router.get('/api/reports/accounts', () => {
    const accounts = loadAccounts(db);
    const balances = accountBalances(accounts, loadTransactions(db));

    const rows = accounts
      .filter((a) => !a.deleted)
      .map((a) => ({
        id: a.id,
        name: a.name,
        type: a.type,
        on_budget: a.on_budget,
        closed: a.closed,
        balance: balances.get(a.id) || 0,
        is_liability: isLiability(a.type) ? 1 : 0,
      }));

    const netWorth = rows.reduce((acc, r) => acc + r.balance, 0);
    return { accounts: rows, net_worth: netWorth };
  });
}
