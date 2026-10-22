/** One call for everything the UI needs to render from scratch. */

import { nowIso, toPlainList } from '../util.js';
import { SYNC_TABLES } from '../db.js';
import { accountBalances } from '../domain/accounts.js';
import { computeBudget } from '../domain/budget.js';
import { upcoming } from '../domain/schedule.js';
import { todayIso } from '../domain/dates.js';
import { budgetInputs, groupBudget } from './budget.js';

export function registerBootstrap(router, db) {
  router.get('/api/bootstrap', (ctx) => {
    const month = (ctx.query.get('month') || nowIso().slice(0, 7)).slice(0, 7);

    const settings = Object.fromEntries(
      db.prepare('SELECT key, value FROM settings').all().map((r) => [r.key, r.value])
    );

    const accounts = toPlainList(
      db.prepare('SELECT * FROM accounts WHERE deleted = 0 ORDER BY sort_order ASC, name COLLATE NOCASE ASC').all()
    );
    const transactions = toPlainList(db.prepare('SELECT * FROM transactions WHERE deleted = 0').all());
    const balances = accountBalances(accounts, transactions);

    const inputs = budgetInputs(db);
    const computed = computeBudget({ month, ...inputs });
    const schedules = toPlainList(db.prepare('SELECT * FROM schedules WHERE deleted = 0').all());

    return {
      server_time: nowIso(),
      month,
      currency: 'USD',
      accounts: accounts.map((a) => ({ ...a, balance: balances.get(a.id) || 0 })),
      groups: inputs.groups,
      categories: inputs.categories,
      budget: computed,
      budget_groups: groupBudget(computed, inputs.groups),
      rules: toPlainList(db.prepare('SELECT * FROM rules WHERE deleted = 0 ORDER BY priority ASC, id ASC').all()),
      schedules,
      goals: toPlainList(db.prepare('SELECT * FROM goals WHERE deleted = 0').all()),
      upcoming: upcoming(schedules, { from: new Date().toISOString().slice(0, 10), days: 30 }),
      tables: SYNC_TABLES,
    };
  });
}
