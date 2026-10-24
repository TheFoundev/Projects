/**
 * Recurring-transaction arithmetic. Pure: given a schedule, produce dates.
 *
 * Monthly and yearly steps keep the day-of-month where the target month allows
 * it and clamp where it does not, so a schedule on the 31st lands on the 28th
 * (or 29th) in February instead of overflowing into March.
 */

import { addDaysToDate, addMonthsToDate, addYearsToDate } from './dates.js';

export const FREQUENCIES = ['daily', 'weekly', 'monthly', 'yearly'];

/** The date `interval` periods after `date`. */
export function nextDate(date, frequency, interval = 1) {
  const n = Math.max(1, Math.trunc(Number(interval) || 1));
  switch (frequency) {
    case 'daily': return addDaysToDate(date, n);
    case 'weekly': return addDaysToDate(date, 7 * n);
    case 'monthly': return addMonthsToDate(date, n);
    case 'yearly': return addYearsToDate(date, n);
    default: throw new TypeError(`unknown frequency: "${frequency}"`);
  }
}

/**
 * Every occurrence of a schedule between `from` and `to` (inclusive).
 * Stops at `end_date` and after `limit` iterations as a safety net.
 */
export function occurrences(schedule, { from, to, limit = 400 } = {}) {
  const out = [];
  if (!schedule || schedule.deleted) return out;

  let cursor = schedule.next_date;
  let guard = 0;

  while (guard < limit) {
    guard += 1;
    if (schedule.end_date && cursor > schedule.end_date) break;
    if (to && cursor > to) break;
    if (!from || cursor >= from) out.push(cursor);
    const next = nextDate(cursor, schedule.frequency, schedule.interval_n);
    if (next <= cursor) break; // defensive: never loop forever
    cursor = next;
  }

  return out;
}

/**
 * Flatten many schedules into a sorted list of upcoming items within `days`
 * of `from`. Each item carries enough to render without a second lookup.
 */
export function upcoming(schedules, { from, days = 30, limit = 100 } = {}) {
  const to = addDaysToDate(from, days);
  const items = [];

  for (const schedule of schedules) {
    if (schedule.deleted) continue;
    for (const date of occurrences(schedule, { from, to })) {
      items.push({
        schedule_id: schedule.id,
        account_id: schedule.account_id,
        category_id: schedule.category_id,
        payee: schedule.payee,
        memo: schedule.memo,
        amount_cents: schedule.amount_cents,
        date,
      });
    }
  }

  items.sort((a, b) => (a.date < b.date ? -1 : a.date > b.date ? 1 : a.schedule_id - b.schedule_id));
  return items.slice(0, limit);
}
