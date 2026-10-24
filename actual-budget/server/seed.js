/**
 * Demo data, so the app has something to show the first time it is opened.
 *
 * Run it directly to (re)create data/budget.db, or import `seed(db)` from a
 * test to populate an in-memory database. Running it twice is safe: it clears
 * the demo tables first, inside a transaction.
 */

import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { openDatabase, DEFAULT_DB_PATH, withTransaction } from './db.js';
import { nowIso } from './util.js';
import { addMonths, todayIso } from './domain/dates.js';

/** Demo tables in child-first order, so the deletes respect foreign keys. */
const DEMO_TABLES = [
  'transactions',
  'budget_months',
  'rules',
  'schedules',
  'goals',
  'categories',
  'category_groups',
  'accounts',
];

/** Insert the demo budget into `db`. Returns the new ids, for tests. */
export function seed(db) {
  const now = nowIso();
  const thisMonth = todayIso().slice(0, 7);
  const lastMonth = addMonths(thisMonth, -1);
  const day = (month, n) => `${month}-${String(n).padStart(2, '0')}`;

  return withTransaction(db, () => {
    for (const table of DEMO_TABLES) db.prepare(`DELETE FROM ${table}`).run();

    const account = db.prepare(
      'INSERT INTO accounts (name, type, on_budget, closed, note, sort_order, updated_at, deleted) VALUES (?, ?, ?, 0, ?, ?, ?, 0)'
    );
    const checking = Number(account.run('Everyday Checking', 'checking', 1, 'Main spending account', 0, now).lastInsertRowid);
    const savings = Number(account.run('Savings', 'savings', 1, 'Emergency fund', 1, now).lastInsertRowid);
    const credit = Number(account.run('Credit Card', 'credit', 1, 'Paid in full monthly', 2, now).lastInsertRowid);
    const brokerage = Number(account.run('Brokerage', 'investment', 0, 'Tracking, off budget', 3, now).lastInsertRowid);

    const group = db.prepare(
      'INSERT INTO category_groups (name, is_income, sort_order, updated_at, deleted) VALUES (?, ?, ?, ?, 0)'
    );
    const incomeGroup = Number(group.run('Income', 1, 0, now).lastInsertRowid);
    const billsGroup = Number(group.run('Bills', 0, 1, now).lastInsertRowid);
    const everydayGroup = Number(group.run('Everyday', 0, 2, now).lastInsertRowid);
    const goalsGroup = Number(group.run('Savings goals', 0, 3, now).lastInsertRowid);

    const category = db.prepare(
      'INSERT INTO categories (group_id, name, note, sort_order, hidden, updated_at, deleted) VALUES (?, ?, ?, ?, 0, ?, 0)'
    );
    const cat = (groupId, name, order = 0, note = '') => Number(category.run(groupId, name, note, order, now).lastInsertRowid);

    const salary = cat(incomeGroup, 'Salary', 0);
    const otherIncome = cat(incomeGroup, 'Other income', 1);
    const rent = cat(billsGroup, 'Rent', 0);
    const utilities = cat(billsGroup, 'Utilities', 1);
    const phone = cat(billsGroup, 'Phone', 2);
    const subscriptions = cat(billsGroup, 'Subscriptions', 3);
    const groceries = cat(everydayGroup, 'Groceries', 0);
    const transport = cat(everydayGroup, 'Transport', 1);
    const eatingOut = cat(everydayGroup, 'Eating out', 2);
    const household = cat(everydayGroup, 'Household', 3);
    const emergency = cat(goalsGroup, 'Emergency fund', 0);
    const holiday = cat(goalsGroup, 'Holiday', 1);

    // ---- transactions -----------------------------------------------------
    const tx = db.prepare(
      'INSERT INTO transactions (account_id, date, payee, memo, amount_cents, category_id, cleared, reconciled, updated_at, deleted) VALUES (?, ?, ?, ?, ?, ?, 1, 0, ?, 0)'
    );
    const spend = (accountId, date, payee, amount, categoryId, memo = '') =>
      tx.run(accountId, date, payee, memo, amount, categoryId, now);

    spend(checking, day(lastMonth, 1), 'Acme Corp', 250000, salary, 'Monthly salary');
    spend(checking, day(lastMonth, 1), 'Rent', -120000, rent);
    spend(checking, day(lastMonth, 4), 'Power & Water', -8500, utilities);
    spend(checking, day(lastMonth, 6), 'Mobile', -2500, phone);
    spend(credit, day(lastMonth, 8), 'Netflix', -1299, subscriptions);
    spend(checking, day(lastMonth, 10), 'Fresh Market', -42000, groceries);
    spend(checking, day(lastMonth, 14), 'Metro', -15000, transport);
    spend(credit, day(lastMonth, 20), 'Pizza Place', -8000, eatingOut);
    spend(savings, day(lastMonth, 25), 'Transfer in', 20000, emergency);

    spend(checking, day(thisMonth, 1), 'Acme Corp', 250000, salary, 'Monthly salary');
    spend(checking, day(thisMonth, 1), 'Rent', -120000, rent);
    spend(credit, day(thisMonth, 3), 'Netflix', -1299, subscriptions);
    spend(checking, day(thisMonth, 5), 'Fresh Market', -18500, groceries);
    spend(checking, day(thisMonth, 6), 'Metro', -6000, transport);
    spend(credit, day(thisMonth, 7), 'Pizza Place', -3200, eatingOut);
    spend(checking, day(thisMonth, 9), 'Hardware Store', -4500, household);
    // Off-budget account: proves the budget maths ignores tracking accounts.
    spend(brokerage, day(thisMonth, 2), 'Deposit', 50000, null, 'Monthly investment');

    // ---- plan -------------------------------------------------------------
    const budget = db.prepare(
      'INSERT INTO budget_months (month, category_id, budgeted_cents, updated_at, deleted) VALUES (?, ?, ?, ?, 0)'
    );
    const plan = (month, categoryId, amount) => budget.run(month, categoryId, amount, now);

    const rows = [rent, utilities, phone, subscriptions, groceries, transport, eatingOut, household, emergency, holiday];
    const amounts = [120000, 12000, 3000, 2000, 45000, 18000, 12000, 8000, 20000, 10000];
    rows.forEach((categoryId, i) => {
      plan(lastMonth, categoryId, amounts[i]);
      plan(thisMonth, categoryId, amounts[i]);
    });

    // ---- rules ------------------------------------------------------------
    const rule = db.prepare(
      'INSERT INTO rules (priority, field, op, value, set_category_id, enabled, updated_at, deleted) VALUES (?, ?, ?, ?, ?, 1, ?, 0)'
    );
    rule.run(10, 'payee', 'contains', 'netflix', subscriptions, now);
    rule.run(20, 'payee', 'contains', 'fresh market', groceries, now);
    rule.run(30, 'payee', 'equals', 'metro', transport, now);
    rule.run(40, 'payee', 'equals', 'rent', rent, now);

    // ---- schedules --------------------------------------------------------
    const schedule = db.prepare(
      'INSERT INTO schedules (account_id, payee, memo, amount_cents, category_id, frequency, interval_n, next_date, end_date, auto_post, updated_at, deleted) VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, 0, ?, 0)'
    );
    const nextMonthFirst = `${addMonths(thisMonth, 1)}-01`;
    schedule.run(checking, 'Rent', '', -120000, rent, 'monthly', 1, nextMonthFirst, now);
    schedule.run(checking, 'Acme Corp', 'Salary', 250000, salary, 'monthly', 1, nextMonthFirst, now);
    schedule.run(credit, 'Netflix', '', -1299, subscriptions, 'monthly', 1, `${thisMonth}-03`, now);

    // ---- goals ------------------------------------------------------------
    const goal = db.prepare(
      'INSERT INTO goals (category_id, target_cents, target_date, monthly_cents, updated_at, deleted) VALUES (?, ?, ?, ?, ?, 0)'
    );
    goal.run(emergency, 600000, `${addMonths(thisMonth, 12)}-01`, 20000, now);
    goal.run(holiday, 150000, `${addMonths(thisMonth, 10)}-01`, 10000, now);

    return {
      checking,
      savings,
      credit,
      brokerage,
      categories: { salary, otherIncome, rent, utilities, phone, subscriptions, groceries, transport, eatingOut, household, emergency, holiday },
      months: { lastMonth, thisMonth },
    };
  });
}

const isMain = process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);

if (isMain) {
  const dbPath = process.env.FOUNDEV_DB || DEFAULT_DB_PATH;
  const db = openDatabase(dbPath);
  seed(db);
  db.close();
  console.log(`seeded ${dbPath}`);
}
