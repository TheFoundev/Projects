import test from 'node:test';
import assert from 'node:assert';

import { monthKey, addMonths, addDays, addMonthsToDate } from '../server/domain/dates.js';
import { parseCents, formatCents } from '../server/money.js';
import { accountBalances } from '../server/domain/accounts.js';
import { computeBudget } from '../server/domain/budget.js';
import { applyRules } from '../server/domain/rules.js';
import { nextDate, occurrences } from '../server/domain/schedule.js';
import { netWorthSeries } from '../server/domain/reports.js';

test('parseCents and formatCents', () => {
  assert.equal(parseCents('12.34'), 1234);
  assert.equal(parseCents('-5'), -500);
  assert.equal(parseCents('$1,234.5'), 123450);
  assert.equal(parseCents('1.005'), 101);
  assert.equal(formatCents(1234), '12.34');
  assert.equal(formatCents(-450), '-4.50');
});

test('month arithmetic', () => {
  assert.equal(monthKey('2026-03-14'), '2026-03');
  assert.equal(addMonths('2026-02', 1), '2026-03');
  assert.equal(addMonths('2026-02', -1), '2026-01');
  assert.equal(addMonths('2026-12', 1), '2027-01');
  assert.equal(addMonthsToDate('2026-01-31', 1), '2026-02-28');
  assert.equal(addDays('2026-02-28', 1), '2026-03-01');
});

test('account balances', () => {
  const accounts = [
    { id: 1, deleted: 0, on_budget: 1, type: 'checking' },
    { id: 2, deleted: 0, on_budget: 1, type: 'credit' },
  ];
  const tx = [
    { id: 1, account_id: 1, amount_cents: 1000, deleted: 0 },
    { id: 2, account_id: 1, amount_cents: -300, deleted: 0 },
    { id: 3, account_id: 2, amount_cents: -500, deleted: 0 },
  ];
  const b = accountBalances(accounts, tx);
  assert.equal(b.get(1), 700);
  assert.equal(b.get(2), -500);
});

test('rules match transactions in priority order', () => {
  const rules = [
    { id: 1, priority: 20, field: 'payee', op: 'contains', value: 'netflix', set_category_id: 30, enabled: 1, deleted: 0 },
    { id: 2, priority: 10, field: 'payee', op: 'contains', value: 'netflix', set_category_id: 40, enabled: 1, deleted: 0 },
    { id: 3, priority: 5, field: 'payee', op: 'contains', value: 'other', set_category_id: 50, enabled: 0, deleted: 0 },
  ];
  const tx = { payee: 'Netflix Monthly', memo: '', amount_cents: -1299 };
  assert.equal(applyRules(rules, tx), 40);
});

test('schedules clamp 31st into February', () => {
  assert.equal(nextDate('2026-01-31', 'monthly', 1), '2026-02-28');
  assert.equal(nextDate('2024-01-31', 'monthly', 1), '2024-02-29');
  assert.equal(nextDate('2026-01-05', 'weekly', 2), '2026-01-19');
  const schedule = { next_date: '2026-01-31', frequency: 'monthly', interval_n: 1, end_date: '2026-03-31', deleted: 0 };
  assert.deepEqual(occurrences(schedule, { from: '2026-01-01', to: '2026-04-01' }), ['2026-01-31', '2026-02-28', '2026-03-31']);
});

test('net worth accumulates', () => {
  const accounts = [
    { id: 1, deleted: 0, type: 'checking' },
    { id: 2, deleted: 0, type: 'credit' },
  ];
  const transactions = [
    { id: 1, account_id: 1, date: '2026-01-01', amount_cents: 50000, deleted: 0 },
    { id: 2, account_id: 2, date: '2026-01-10', amount_cents: -10000, deleted: 0 },
  ];
  const series = netWorthSeries({ accounts, transactions, months: ['2026-01', '2026-02'] });
  assert.equal(series.length, 2);
  assert.equal(series[0].net, 40000);
  assert.equal(series[1].net, 40000);
});
