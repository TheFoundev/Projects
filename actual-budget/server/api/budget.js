/** Budget endpoints: read a month, and set what one category is budgeted. */

import { badRequest, nowIso, toPlainList } from '../util.js';
import { computeBudget } from '../domain/budget.js';

/**
 * Everything the budget maths needs, already filtered to the budget.
 * Tracking (off-budget) accounts are excluded: their spending is not budgeting.
 */
export function budgetInputs(db) {
  const accounts = toPlainList(db.prepare('SELECT * FROM accounts WHERE deleted = 0').all());
  const onBudgetIds = new Set(accounts.filter((a) => a.on_budget).map((a) => a.id));
  const transactions = toPlainList(
    db.prepare('SELECT id, account_id, date, amount_cents, category_id, transfer_account_id, deleted FROM transactions').all()
  ).filter((tx) => onBudgetIds.has(tx.account_id));

  return {
    categories: toPlainList(db.prepare('SELECT * FROM categories WHERE deleted = 0 ORDER BY sort_order ASC, id ASC').all()),
    groups: toPlainList(db.prepare('SELECT * FROM category_groups WHERE deleted = 0 ORDER BY sort_order ASC, id ASC').all()),
    transactions,
    budgetRows: toPlainList(db.prepare('SELECT * FROM budget_months').all()),
  };
}

/** Group the computed categories for display, preserving group order. */
export function groupBudget(computed, groups) {
  const byGroup = new Map();
  const ungrouped = [];

  for (const category of computed.categories) {
    if (category.group_id == null) { ungrouped.push(category); continue; }
    if (!byGroup.has(category.group_id)) byGroup.set(category.group_id, []);
    byGroup.get(category.group_id).push(category);
  }

  const totals = (list) => list.reduce(
    (acc, c) => ({ budgeted: acc.budgeted + c.budgeted, activity: acc.activity + c.activity, available: acc.available + c.available }),
    { budgeted: 0, activity: 0, available: 0 },
  );

  const result = groups.map((group) => {
    const categories = byGroup.get(group.id) || [];
    return { id: group.id, name: group.name, is_income: group.is_income, categories, ...totals(categories) };
  });

  if (ungrouped.length) {
    result.push({ id: null, name: 'Uncategorised', is_income: 0, categories: ungrouped, ...totals(ungrouped) });
  }
  return result;
}

export function registerBudget(router, db) {
  router.get('/api/budget/:month', (ctx) => {
    const month = ctx.params.month;
    if (!/^\d{4}-\d{2}$/.test(month)) throw badRequest('month must be YYYY-MM');
    const inputs = budgetInputs(db);
    const computed = computeBudget({ month, ...inputs });
    return { ...computed, groups: groupBudget(computed, inputs.groups) };
  });

  router.put('/api/budget/:month/:categoryId', (ctx) => {
    const month = ctx.params.month;
    if (!/^\d{4}-\d{2}$/.test(month)) throw badRequest('month must be YYYY-MM');

    const categoryId = Number(ctx.params.categoryId);
    if (!Number.isInteger(categoryId) || categoryId <= 0) throw badRequest('categoryId must be a positive integer');

    const category = db.prepare('SELECT id FROM categories WHERE id = ? AND deleted = 0').get(categoryId);
    if (!category) throw badRequest(`category ${categoryId} does not exist`);

    const budgeted = Number(ctx.body.budgeted_cents);
    if (!Number.isFinite(budgeted)) throw badRequest('"budgeted_cents" must be a number');

    db.prepare(
      `INSERT INTO budget_months (month, category_id, budgeted_cents, updated_at, deleted)
       VALUES (?, ?, ?, ?, 0)
       ON CONFLICT(month, category_id) DO UPDATE
         SET budgeted_cents = excluded.budgeted_cents, updated_at = excluded.updated_at, deleted = 0`
    ).run(month, categoryId, Math.trunc(budgeted), nowIso());

    return { month, category_id: categoryId, budgeted_cents: Math.trunc(budgeted) };
  });
}
