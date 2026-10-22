# Data model

SQLite schema (`server/db.js`). Every syncable table carries `updated_at`
(ISO-8601 UTC) and `deleted` (0/1) for last-write-wins sync.

## settings

| column | type | notes |
|---|---|---|
| key | TEXT PK | |
| value | TEXT | |
| updated_at | TEXT | |

Holds `currency`, `locale`, `last_server_time`, and the current month.

## accounts

| column | type | notes |
|---|---|---|
| id | INTEGER PK | |
| name | TEXT | |
| type | TEXT | `checking`, `savings`, `cash`, `credit`, `loan`, `investment`, `other` |
| on_budget | INTEGER | 1 = counts toward the budget |
| closed | INTEGER | |
| note | TEXT | |
| sort_order | INTEGER | |
| updated_at / deleted | | sync |

**Balance** = `SUM(amount_cents)` of the account's live transactions.

## category_groups

| column | type | notes |
|---|---|---|
| id | INTEGER PK | |
| name | TEXT | e.g. `Everyday`, `Bills`, `Savings` |
| is_income | INTEGER | 1 for the income group |
| sort_order | INTEGER | |

## categories

| column | type | notes |
|---|---|---|
| id | INTEGER PK | |
| group_id | INTEGER → category_groups | |
| name | TEXT | |
| note | TEXT | |
| sort_order | INTEGER | |
| hidden | INTEGER | |

## transactions

| column | type | notes |
|---|---|---|
| id | INTEGER PK | |
| account_id | INTEGER → accounts | |
| date | TEXT | `YYYY-MM-DD` |
| payee | TEXT | |
| memo | TEXT | |
| amount_cents | INTEGER | negative = outflow |
| category_id | INTEGER → categories, nullable | null = uncategorised |
| cleared | INTEGER | |
| reconciled | INTEGER | |
| transfer_account_id | INTEGER → accounts, nullable | the other leg of a transfer |
| schedule_id | INTEGER, nullable | set when posted from a schedule |
| import_hash | TEXT, nullable | unique; dedupes bank imports |
| updated_at / deleted | | sync |

## budget_months

One row per category that has a non-zero budget in a month.

| column | type | notes |
|---|---|---|
| month | TEXT | `YYYY-MM` |
| category_id | INTEGER → categories | |
| budgeted_cents | INTEGER | |
| — | | `UNIQUE(month, category_id)` |

## rules

| column | type | notes |
|---|---|---|
| priority | INTEGER | lower runs first |
| field | TEXT | `payee`, `memo`, `amount` |
| op | TEXT | `contains`, `equals`, `starts_with`, `ends_with`, `gt`, `lt` |
| value | TEXT | |
| set_category_id | INTEGER → categories | what to assign |
| enabled | INTEGER | |

## schedules

| column | type | notes |
|---|---|---|
| account_id | INTEGER → accounts | |
| payee / memo | TEXT | |
| amount_cents | INTEGER | |
| category_id | INTEGER, nullable | |
| frequency | TEXT | `daily`, `weekly`, `monthly`, `yearly` |
| interval_n | INTEGER | every *n* periods |
| next_date | TEXT | `YYYY-MM-DD` |
| end_date | TEXT, nullable | |
| auto_post | INTEGER | |

## goals

| column | type | notes |
|---|---|---|
| category_id | INTEGER → categories | |
| target_cents | INTEGER | |
| target_date | TEXT, nullable | |
| monthly_cents | INTEGER | planned funding per month |

## Derived values (never stored)

| value | formula |
|---|---|
| account balance | `Σ amount_cents` over live transactions |
| category activity (month) | `Σ amount_cents` for that month + category |
| category available (month) | `available(prev) + budgeted + activity` |
| to be budgeted | `tbb(prev) + income(month) − budgeted(month)` |
| net worth | `Σ` balances of asset accounts `−` liabilities |
