/**
 * Calendar helpers. All dates are plain `YYYY-MM-DD` strings and all months are
 * `YYYY-MM` strings, so they sort lexicographically and survive JSON intact.
 * Arithmetic is done in UTC to keep it free of local-time zones.
 */

const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/;
const ISO_MONTH = /^\d{4}-\d{2}$/;

export function isDate(value) {
  return typeof value === 'string' && ISO_DATE.test(value);
}

export function isMonth(value) {
  return typeof value === 'string' && ISO_MONTH.test(value);
}

/** Today as `YYYY-MM-DD` (UTC). */
export function todayIso(clock = new Date()) {
  return clock.toISOString().slice(0, 10);
}

/** The month a date belongs to: "2026-03-14" -> "2026-03". */
export function monthKey(date) {
  return String(date).slice(0, 7);
}

/** Number of days in a month. Handles leap years. */
export function daysInMonth(month) {
  const [year, mon] = month.split('-').map(Number);
  return new Date(Date.UTC(year, mon, 0)).getUTCDate();
}

/** First and last day of a month: -> { start: "2026-03-01", end: "2026-03-31" }. */
export function monthBounds(month) {
  const year = month.slice(0, 4);
  const last = daysInMonth(month);
  return { start: `${month}-01`, end: `${month}-${String(last).padStart(2, '0')}` };
}

/** Shift a month key by n months (n may be negative). */
export function addMonths(month, n) {
  const [year, mon] = month.split('-').map(Number);
  const total = (year * 12 + (mon - 1)) + n;
  const y = Math.floor(total / 12);
  const m = (total % 12 + 12) % 12 + 1;
  return `${String(y).padStart(4, '0')}-${String(m).padStart(2, '0')}`;
}

export function prevMonth(month) {
  return addMonths(month, -1);
}

/** Shift a date by n days. */
export function addDays(date, n) {
  const [y, m, d] = date.split('-').map(Number);
  const t = Date.UTC(y, m - 1, d) + n * 86400000;
  return new Date(t).toISOString().slice(0, 10);
}

/** A date clamped to a day that exists in its month (31 Jan -> 28 Feb). */
export function clampDay(year, month, day) {
  const last = new Date(Date.UTC(year, month, 0)).getUTCDate();
  return `${String(year).padStart(4, '0')}-${String(month).padStart(2, '0')}-${String(Math.min(day, last)).padStart(2, '0')}`;
}

/**
 * Add n months to a date, keeping the day-of-month where the target month
 * allows it and clamping where it does not. This is what stops a schedule on
 * the 31st from spilling into the next month.
 *
 * Schedules that fall on the last day of a month (e.g. 31st of January) are
 * treated as "end of month" and produce the last day of each subsequent month
 * (28th/29th in February, 31st in March, etc.), matching common budgeting apps.
 */
export function addMonthsToDate(date, n) {
  const [year, mon, day] = date.split('-').map(Number);
  const srcLast = new Date(Date.UTC(year, mon, 0)).getUTCDate();
  const isEndOfMonth = day >= srcLast;

  const [y, m] = addMonths(`${String(year).padStart(4, '0')}-${String(mon).padStart(2, '0')}`, n).split('-').map(Number);
  const tgtLast = new Date(Date.UTC(y, m, 0)).getUTCDate();

  const targetDay = isEndOfMonth ? tgtLast : Math.min(day, tgtLast);
  return `${String(y).padStart(4, '0')}-${String(m).padStart(2, '0')}-${String(targetDay).padStart(2, '0')}`;
}

export function addYearsToDate(date, n) {
  const year = Number(date.slice(0, 4)) + n;
  const [, mon, day] = date.split('-').map(Number);
  return clampDay(year, mon, day);
}

export function addDaysToDate(date, n) {
  return addDays(date, n);
}

/** Compare two ISO dates/dates-strings, -1 / 0 / 1. */
export function compareDates(a, b) {
  return a < b ? -1 : a > b ? 1 : 0;
}
