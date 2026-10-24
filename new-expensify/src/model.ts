/**
 * The model of the expense app.
 *
 * The rules of a report: what a report may cost, when it may be submitted,
 * how the expenses are grouped and what the totals are.
 *
 * Pure functions, no imports, so they can be tested without a React Native
 * runtime.
 */

export type Expense = {
  id: string;
  title: string;
  amount: number;
  date: string;
  category: string;
};

export type ReportStatus = 'draft' | 'submitted' | 'approved' | 'rejected';

export type Report = {
  id: string;
  title: string;
  status: ReportStatus;
  currency: string;
  expenses: Expense[];
};

export type Message = {
  id: string;
  sender: string;
  body: string;
  time: string;
  mine?: boolean;
};

/** The states a report can be in, and the ones it may move to. */
export const REPORT_TRANSITIONS: Record<ReportStatus, ReportStatus[]> = {
  draft: ['draft', 'submitted'],
  submitted: ['submitted', 'approved', 'rejected', 'draft'],
  approved: ['approved'],
  rejected: ['rejected', 'draft'],
};

/** The categories an expense can have. */
export const CATEGORIES = ['Travel', 'Lodging', 'Meals', 'Equipment', 'Events', 'Other'];

/** The most a report may cost before it needs a note. */
export const LARGE_REPORT_LIMIT = 500;

/** True when the report may move from one state to another. */
export function canTransition(from: ReportStatus, to: ReportStatus): boolean {
  return (REPORT_TRANSITIONS[from] ?? []).includes(to);
}

/** The error message for an illegal move, or null. */
export function transitionError(from: ReportStatus, to: string): string | null {
  if (!REPORT_TRANSITIONS[to as ReportStatus]) return `"${to}" is not a state of a report.`;
  if (!canTransition(from, to as ReportStatus)) {
    return `A ${from} report cannot become ${to}.`;
  }
  return null;
}

/** The total of a report. */
export function totalOf(report: Report): number {
  return report.expenses.reduce((sum, expense) => sum + expense.amount, 0);
}

/** The total of every report. */
export function totalOfAll(reports: Report[]): number {
  return reports.reduce((sum, report) => sum + totalOf(report), 0);
}

/** The expenses of a report, grouped by category. */
export function byCategory(report: Report): { category: string; total: number; count: number }[] {
  const groups = new Map<string, { total: number; count: number }>();
  for (const expense of report.expenses) {
    const current = groups.get(expense.category) ?? { total: 0, count: 0 };
    current.total += expense.amount;
    current.count += 1;
    groups.set(expense.category, current);
  }
  return [...groups.entries()]
    .map(([category, value]) => ({ category, total: value.total, count: value.count }))
    .sort((left, right) => right.total - left.total);
}

/**
 * Check an expense before it is added to a report.
 *
 * The title and the amount are needed, the amount has to be a positive
 * number and the category has to be one the app knows.
 */
export function checkExpense(expense: Partial<Expense>): string | null {
  if (!String(expense.title ?? '').trim()) return 'The expense needs a title.';
  const amount = Number(expense.amount);
  if (!Number.isFinite(amount) || amount <= 0) return 'The amount has to be a number above zero.';
  if (expense.category && !CATEGORIES.includes(expense.category)) {
    return `"${expense.category}" is not a category.`;
  }
  return null;
}

/**
 * Check a report before it is submitted.
 *
 * A report needs a title, at least one expense and a reason when it is
 * large.
 */
export function checkSubmit(report: Report, reason = ''): string | null {
  if (!report.title.trim()) return 'The report needs a title.';
  if (report.expenses.length === 0) return 'A report without expenses cannot be submitted.';
  if (totalOf(report) > LARGE_REPORT_LIMIT && !reason.trim()) {
    return `The report is over ${LARGE_REPORT_LIMIT}, so it needs a reason.`;
  }
  return null;
}

/** The reports that are waiting for an approval. */
export function awaitingApproval(reports: Report[]): Report[] {
  return reports.filter((report) => report.status === 'submitted');
}

/** The reports of one state. */
export function withStatus(reports: Report[], status: ReportStatus): Report[] {
  return reports.filter((report) => report.status === status);
}

/** Add an expense to a report. */
export function addExpense(report: Report, expense: Expense): Report {
  return { ...report, expenses: [...report.expenses, expense] };
}

/** Remove an expense from a report. */
export function removeExpense(report: Report, expenseId: string): Report {
  return { ...report, expenses: report.expenses.filter((expense) => expense.id !== expenseId) };
}

/** Move a report to another state, when the move is allowed. */
export function moveReport(report: Report, to: ReportStatus): { report: Report } | { error: string } {
  const problem = transitionError(report.status, to);
  if (problem) return { error: problem };
  return { report: { ...report, status: to } };
}

/** The money, written the way the app shows it. */
export function money(value: number, currency = 'CAD'): string {
  const symbol = currency === 'CAD' ? '$' : currency === 'EUR' ? '€' : currency === 'USD' ? '$' : '';
  return `${symbol}${value.toFixed(2)}`;
}

/** The chats of the app, newest last. */
export function addMessage(messages: Message[], message: Message): Message[] {
  return [...messages, message];
}

/** The messages that mention a word. */
export function searchMessages(messages: Message[], query: string): Message[] {
  const needle = query.trim().toLowerCase();
  if (!needle) return messages;
  return messages.filter((message) =>
    `${message.sender} ${message.body}`.toLowerCase().includes(needle),
  );
}
