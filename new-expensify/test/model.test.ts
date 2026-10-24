/** Tests for the expense model and the store. */
import assert from 'node:assert';
import test from 'node:test';

import {
  CATEGORIES,
  LARGE_REPORT_LIMIT,
  addExpense,
  addMessage,
  awaitingApproval,
  byCategory,
  canTransition,
  checkExpense,
  checkSubmit,
  money,
  moveReport,
  removeExpense,
  searchMessages,
  totalOf,
  totalOfAll,
  transitionError,
  withStatus,
  type Expense,
  type Report,
} from '../src/model.ts';
import { ExpenseStore, createMemoryStore } from '../src/store.ts';

const expense = (id: string, amount: number, category = 'Travel'): Expense => ({
  id,
  title: `Expense ${id}`,
  amount,
  date: 'Apr 21',
  category,
});

const report = (id: string, status: Report['status'], expenses: Expense[]): Report => ({
  id,
  title: `Report ${id}`,
  status,
  currency: 'CAD',
  expenses,
});

test('a report can be submitted from a draft', () => {
  assert.ok(canTransition('draft', 'submitted'));
  assert.ok(!canTransition('draft', 'approved'));
});

test('a submitted report can be approved or rejected', () => {
  assert.ok(canTransition('submitted', 'approved'));
  assert.ok(canTransition('submitted', 'rejected'));
  assert.ok(canTransition('rejected', 'draft'));
});

test('an approved report stays approved', () => {
  assert.ok(!canTransition('approved', 'draft'));
  assert.match(transitionError('approved', 'draft') ?? '', /cannot become/);
  assert.match(transitionError('draft', 'nope') ?? '', /not a state/);
});

test('the total of a report is the sum of its expenses', () => {
  const value = report('r1', 'draft', [expense('e1', 10.5), expense('e2', 4.25)]);
  assert.equal(totalOf(value), 14.75);
  assert.equal(totalOfAll([value, report('r2', 'draft', [expense('e3', 1)])]), 15.75);
});

test('the expenses are grouped by category', () => {
  const value = report('r1', 'draft', [
    expense('e1', 10, 'Travel'),
    expense('e2', 5, 'Travel'),
    expense('e3', 20, 'Meals'),
  ]);
  const groups = byCategory(value);
  // The groups come back with the biggest total first.
  assert.equal(groups[0].category, 'Meals');
  assert.equal(groups[0].total, 20);
  assert.equal(groups[1].category, 'Travel');
  assert.equal(groups[1].total, 15);
  assert.equal(groups[1].count, 2);
});

test('an expense needs a title and a positive amount', () => {
  assert.match(checkExpense({ amount: 10 }) ?? '', /title/);
  assert.match(checkExpense({ title: 'Taxi' }) ?? '', /amount/);
  assert.match(checkExpense({ title: 'Taxi', amount: -1 }) ?? '', /amount/);
  assert.match(checkExpense({ title: 'Taxi', amount: 10, category: 'Bribes' }) ?? '', /category/);
  assert.equal(checkExpense({ title: 'Taxi', amount: 10, category: 'Travel' }), null);
});

test('a report without expenses cannot be submitted', () => {
  assert.match(checkSubmit(report('r1', 'draft', [])) ?? '', /without expenses/);
  assert.match(checkSubmit({ ...report('r1', 'draft', [expense('e1', 1)]), title: '  ' }) ?? '', /title/);
});

test('a large report needs a reason', () => {
  const big = report('r1', 'draft', [expense('e1', LARGE_REPORT_LIMIT + 1)]);
  assert.match(checkSubmit(big) ?? '', /reason/);
  assert.equal(checkSubmit(big, 'Conference'), null);
});

test('the reports can be filtered by their state', () => {
  const reports = [
    report('r1', 'draft', []),
    report('r2', 'submitted', []),
    report('r3', 'approved', []),
  ];
  assert.equal(withStatus(reports, 'submitted').length, 1);
  assert.equal(awaitingApproval(reports).length, 1);
});

test('an expense is added to and removed from a report', () => {
  let value = report('r1', 'draft', []);
  value = addExpense(value, expense('e1', 10));
  assert.equal(value.expenses.length, 1);
  value = removeExpense(value, 'e1');
  assert.equal(value.expenses.length, 0);
});

test('a report moves to another state', () => {
  const value = report('r1', 'draft', [expense('e1', 1)]);
  const answer = moveReport(value, 'submitted');
  assert.equal('report' in answer ? answer.report.status : '', 'submitted');

  const refused = moveReport(value, 'approved');
  assert.equal('error' in refused, true);
});

test('the money is written the way the app shows it', () => {
  assert.equal(money(12.5), '$12.50');
  assert.equal(money(12.5, 'EUR'), '€12.50');
});

test('the messages can be searched', () => {
  const messages = [
    { id: 'm1', sender: 'Priya', body: 'Did the receipts go through?', time: '09:12' },
    { id: 'm2', sender: 'You', body: 'Submitted last night.', time: '09:14' },
  ];
  assert.equal(searchMessages(messages, 'receipts').length, 1);
  assert.equal(searchMessages(messages, 'priya').length, 1);
  assert.equal(searchMessages(messages, '').length, 2);
  assert.equal(searchMessages(messages, 'nothing').length, 0);
});

test('a message is added to the chat', () => {
  const messages = addMessage([], { id: 'm1', sender: 'You', body: 'Hello', time: '09:00' });
  assert.equal(messages.length, 1);
});

test('the categories are the ones the app knows', () => {
  assert.ok(CATEGORIES.includes('Travel'));
  assert.ok(!CATEGORIES.includes('Bribes'));
});

test('the store keeps the reports, the messages and the settings', async () => {
  const store = new ExpenseStore(createMemoryStore());
  await store.saveReports([report('r1', 'draft', [expense('e1', 1)])]);
  await store.saveMessages([{ id: 'm1', sender: 'You', body: 'Hi', time: '09:00' }]);
  await store.saveSettings({ currency: 'CAD' });

  assert.equal((await store.reports())?.length, 1);
  assert.equal((await store.messages())?.length, 1);
  assert.equal((await store.settings<{ currency: string }>())?.currency, 'CAD');
});

test('the store survives a corrupt value', async () => {
  const backend = createMemoryStore();
  await backend.setItem('expensify.reports.v1', 'not json');
  const store = new ExpenseStore(backend);
  assert.equal(await store.reports(), null);
});

test('the store keeps working when the storage fails', async () => {
  const failing = {
    async getItem() { throw new Error('storage unavailable'); },
    async setItem() { throw new Error('storage unavailable'); },
    async removeItem() { throw new Error('storage unavailable'); },
  };
  const store = new ExpenseStore(failing);
  assert.equal(await store.reports(), null);
  assert.equal(await store.saveReports([]), false);
});
