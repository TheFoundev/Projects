/**
 * Envelope budgeting maths.
 *
 * `available` is recursive: this month's available for a category is last
 * month's available, plus whatever was budgeted, plus the month's activity.
 * `computeBudget` therefore walks forward from the earliest month that has any
 * data, so the figure is the same no matter which month is opened.
 *
 * It returns values and never writes anything.
 */

import { addMonths, monthBounds, monthKey } from './dates.js';

/** The earliest month any live transaction or budget row touches. */
export function earliestDataMonth(transactions, budgetRows) {
  let min = null;
  for (const tx of transactions) {
    if (tx.deleted) continue;
    const m = monthKey(tx.date);
    if (min === null || m < min) min = m;
  }
  for (const row of budgetRows) {
    if (row.deleted) continue;
    if (min === null || row.month < min) min = row.month;
  }
  return min;
}

/**
 * Compute one month of the budget, with carry-over from all earlier months.
 *
 * @returns {{
 *   month: string,
 *   to_be_budgeted: number,
 *   income: number,
 *   budgeted_total: number,
 *   categories: Array<{category_id:number, group_id:number|null, name:string,
 *                      budgeted:number, activity:number, available:number}>
 * }}
 */
export function computeBudget({ month, categories, groups = [], transactions = [], budgetRows = [] }) {
  const cats = categories.filter((c) => !c.deleted);
  const groupById = new Map(groups.filter((g) => !g.deleted).map((g) => [g.id, g]));
  const catById = new Map(cats.map((c) => [c.id, c]));

  const isIncomeCategory = (id) => {
    const cat = catById.get(id);
    if (!cat) return false;
    const group = groupById.get(cat.group_id);
    return Boolean(group && group.is_income);
  };

  const earliest = earliestDataMonth(transactions, budgetRows);
  const from = earliest === null || earliest > month ? month : earliest;

  const available = new Map();
  let toBeBudgeted = 0;
  let detail = null;

  for (let m = from; ; m = addMonths(m, 1)) {
    const { start, end } = monthBounds(m);

    const budgeted = new Map();
    for (const row of budgetRows) {
      if (row.deleted || row.month !== m) continue;
      if (!catById.has(row.category_id)) continue;
      budgeted.set(row.category_id, (budgeted.get(row.category_id) || 0) + (Number(row.budgeted_cents) || 0));
    }

    const activity = new Map();
    for (const tx of transactions) {
      if (tx.deleted || tx.category_id == null) continue;
      if (tx.date < start || tx.date > end) continue;
      activity.set(tx.category_id, (activity.get(tx.category_id) || 0) + (Number(tx.amount_cents) || 0));
    }

    let income = 0;
    let budgetedTotal = 0;
    for (const cat of cats) {
      const bud = budgeted.get(cat.id) || 0;
      const act = activity.get(cat.id) || 0;
      available.set(cat.id, (available.get(cat.id) || 0) + bud + act);
      budgetedTotal += bud;
      if (isIncomeCategory(cat.id)) income += act;
    }

    toBeBudgeted = toBeBudgeted + income - budgetedTotal;

    if (m === month) {
      detail = {
        month: m,
        to_be_budgeted: toBeBudgeted,
        income,
        budgeted_total: budgetedTotal,
        categories: cats.map((cat) => ({
          category_id: cat.id,
          group_id: cat.group_id,
          name: cat.name,
          budgeted: budgeted.get(cat.id) || 0,
          activity: activity.get(cat.id) || 0,
          available: available.get(cat.id) || 0,
        })),
      };
    }

    if (m >= month) break;
  }

  return detail ?? {
    month,
    to_be_budgeted: 0,
    income: 0,
    budgeted_total: 0,
    categories: cats.map((cat) => ({
      category_id: cat.id,
      group_id: cat.group_id,
      name: cat.name,
      budgeted: 0,
      activity: 0,
      available: 0,
    })),
  };
}

/** "To be budgeted" for a month — the income you have not allocated yet. */
export function toBeBudgeted(args) {
  return computeBudget(args).to_be_budgeted;
}
