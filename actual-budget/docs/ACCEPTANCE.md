# Acceptance criteria

Each item is verifiable by running the app or the test suite.

## Budget maths

1. A category with `budgeted = 30000` (300.00) and a `-4500` (45.00) expense in
   the same month has `available = 25500`.
2. Unspent budget carries into the next month: if month A ends with
   `available = 10000` and nothing is budgeted or spent in month B, month B's
   `available` is still `10000`.
3. Overspending carries as a negative `available` (no silent clamp to zero).
4. `to_be_budgeted` in a month equals the previous month's figure plus income
   minus the sum of everything budgeted that month.
5. Income only counts once its transaction is assigned to a category in the
   income group.

## Transactions

6. Amounts accept `12.34`, `-5`, `$1,234.5` and store as `1234`, `-500`,
   `123450` cents respectively.
7. An account balance equals the sum of its live transactions.
8. Deleting a transaction removes it from balances and from activity, but the
   row remains soft-deleted for sync.

## Rules

9. A rule `payee contains "netflix" → Subscriptions` assigns that category.
10. Lower `priority` wins; ties break by lowest `id`.
11. Disabled rules never match.
12. `applyRules` is pure: calling it twice on the same input is identical.

## Schedules

13. A monthly schedule on the 31st clamps into February instead of overflowing.
14. `weekly × 2` advances 14 days.
15. Posting a schedule creates a transaction with `schedule_id` set and advances
    `next_date`.
16. A schedule past its `end_date` produces no further occurrences.

## Reports

17. Net worth = assets − liabilities, aggregated by month end.
18. Spending by category for a month sums to the month's negative activity.
19. Cash flow splits income and expense per month.

## Local-first

20. A mutation appears in the UI before any network call completes.
21. With the server stopped, mutations still apply and increment the pending
    count.
22. When the server returns, the queue drains and the pending count reaches 0.
23. `pull` only returns rows whose `updated_at` is newer than `since`.
24. An incoming row older than the stored row is ignored (LWW).

## Platform

25. `node server/index.js` starts with no `npm install`.
26. `npm test` passes with no network access.
27. The app is usable at 375px width (mobile) without horizontal scrolling.
