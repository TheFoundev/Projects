/**
 * SQLite access. One database, opened through `node:sqlite`'s DatabaseSync,
 * with WAL enabled for the on-disk case.
 *
 * Every syncable table carries `updated_at` (ISO-8601 UTC) and `deleted`
 * (0/1). Deletes are soft so they can travel through sync like any other row.
 */

import { DatabaseSync } from 'node:sqlite';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { nowIso } from './util.js';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

export const DEFAULT_DB_PATH = process.env.FOUNDEV_DB || path.join(ROOT, 'data', 'budget.db');

/** Tables that participate in push/pull sync, in dependency order. */
export const SYNC_TABLES = [
  'accounts',
  'category_groups',
  'categories',
  'transactions',
  'budget_months',
  'rules',
  'schedules',
  'goals',
];

/** Columns the sync layer may write, per table. `id` is assigned by the server. */
export const SYNC_COLUMNS = {
  accounts: ['name', 'type', 'on_budget', 'closed', 'note', 'sort_order'],
  category_groups: ['name', 'is_income', 'sort_order'],
  categories: ['group_id', 'name', 'note', 'sort_order', 'hidden'],
  transactions: ['account_id', 'date', 'payee', 'memo', 'amount_cents', 'category_id', 'cleared', 'reconciled', 'transfer_account_id', 'schedule_id', 'import_hash'],
  budget_months: ['month', 'category_id', 'budgeted_cents'],
  rules: ['priority', 'field', 'op', 'value', 'set_category_id', 'enabled'],
  schedules: ['account_id', 'payee', 'memo', 'amount_cents', 'category_id', 'frequency', 'interval_n', 'next_date', 'end_date', 'auto_post'],
  goals: ['category_id', 'target_cents', 'target_date', 'monthly_cents'],
};

const SCHEMA = `
CREATE TABLE IF NOT EXISTS settings (
  key        TEXT PRIMARY KEY,
  value      TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS accounts (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  name        TEXT    NOT NULL,
  type        TEXT    NOT NULL DEFAULT 'checking',
  on_budget   INTEGER NOT NULL DEFAULT 1,
  closed      INTEGER NOT NULL DEFAULT 0,
  note        TEXT    NOT NULL DEFAULT '',
  sort_order  INTEGER NOT NULL DEFAULT 0,
  updated_at  TEXT    NOT NULL,
  deleted     INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS category_groups (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  name        TEXT    NOT NULL,
  is_income   INTEGER NOT NULL DEFAULT 0,
  sort_order  INTEGER NOT NULL DEFAULT 0,
  updated_at  TEXT    NOT NULL,
  deleted     INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS categories (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  group_id    INTEGER REFERENCES category_groups(id) ON DELETE SET NULL,
  name        TEXT    NOT NULL,
  note        TEXT    NOT NULL DEFAULT '',
  sort_order  INTEGER NOT NULL DEFAULT 0,
  hidden      INTEGER NOT NULL DEFAULT 0,
  updated_at  TEXT    NOT NULL,
  deleted     INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS transactions (
  id                  INTEGER PRIMARY KEY AUTOINCREMENT,
  account_id          INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
  date                TEXT    NOT NULL,
  payee               TEXT    NOT NULL DEFAULT '',
  memo                TEXT    NOT NULL DEFAULT '',
  amount_cents        INTEGER NOT NULL,
  category_id         INTEGER REFERENCES categories(id) ON DELETE SET NULL,
  cleared             INTEGER NOT NULL DEFAULT 0,
  reconciled          INTEGER NOT NULL DEFAULT 0,
  transfer_account_id INTEGER REFERENCES accounts(id) ON DELETE SET NULL,
  schedule_id         INTEGER,
  import_hash         TEXT,
  updated_at          TEXT    NOT NULL,
  deleted             INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_tx_date     ON transactions(date);
CREATE INDEX IF NOT EXISTS idx_tx_account  ON transactions(account_id);
CREATE INDEX IF NOT EXISTS idx_tx_category ON transactions(category_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_tx_import_hash
  ON transactions(import_hash) WHERE import_hash IS NOT NULL;

CREATE TABLE IF NOT EXISTS budget_months (
  id             INTEGER PRIMARY KEY AUTOINCREMENT,
  month          TEXT    NOT NULL,
  category_id    INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
  budgeted_cents INTEGER NOT NULL DEFAULT 0,
  updated_at     TEXT    NOT NULL,
  deleted        INTEGER NOT NULL DEFAULT 0,
  UNIQUE(month, category_id)
);

CREATE TABLE IF NOT EXISTS rules (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  priority        INTEGER NOT NULL DEFAULT 0,
  field           TEXT    NOT NULL,
  op              TEXT    NOT NULL,
  value           TEXT    NOT NULL,
  set_category_id INTEGER REFERENCES categories(id) ON DELETE CASCADE,
  enabled         INTEGER NOT NULL DEFAULT 1,
  updated_at      TEXT    NOT NULL,
  deleted         INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS schedules (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  account_id  INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
  payee       TEXT    NOT NULL DEFAULT '',
  memo        TEXT    NOT NULL DEFAULT '',
  amount_cents INTEGER NOT NULL,
  category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
  frequency   TEXT    NOT NULL DEFAULT 'monthly',
  interval_n  INTEGER NOT NULL DEFAULT 1,
  next_date   TEXT    NOT NULL,
  end_date    TEXT,
  auto_post   INTEGER NOT NULL DEFAULT 0,
  updated_at  TEXT    NOT NULL,
  deleted     INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS goals (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  category_id   INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
  target_cents  INTEGER NOT NULL,
  target_date   TEXT,
  monthly_cents INTEGER NOT NULL DEFAULT 0,
  updated_at    TEXT    NOT NULL,
  deleted       INTEGER NOT NULL DEFAULT 0
);
`;

/** Open (and migrate) the database. Pass ":memory:" for tests. */
export function openDatabase(dbPath = DEFAULT_DB_PATH) {
  if (dbPath !== ':memory:') fs.mkdirSync(path.dirname(dbPath), { recursive: true });

  const db = new DatabaseSync(dbPath);
  db.exec('PRAGMA foreign_keys = ON;');
  if (dbPath !== ':memory:') {
    try { db.exec('PRAGMA journal_mode = WAL;'); } catch { /* older builds */ }
  }
  db.exec(SCHEMA);
  installDefaultSettings(db);
  return db;
}

function installDefaultSettings(db) {
  const defaults = {
    currency: 'USD',
    locale: 'en-US',
    month: nowIso().slice(0, 7),
  };
  const insert = db.prepare(
    'INSERT INTO settings (key, value, updated_at) VALUES (?, ?, ?) ON CONFLICT(key) DO NOTHING'
  );
  for (const [key, value] of Object.entries(defaults)) {
    db.prepare('INSERT OR IGNORE INTO settings (key, value, updated_at) VALUES (?, ?, ?)').run(key, value, nowIso());
    void defaults;
  }
}

/** Read one setting. */
export function getSetting(db, key, fallback = null) {
  const row = db.prepare('SELECT value FROM settings WHERE key = ?').get(key);
  return row ? row.value : fallback;
}

/** Write one setting. */
export function setSetting(db, key, value) {
  db.prepare(
    `INSERT INTO settings (key, value, updated_at) VALUES (?, ?, ?)
     ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at`
  ).run(String(key), String(value), nowIso());
}

/** Read every setting as a plain object. */
export function allSettings(db) {
  const out = {};
  for (const row of db.prepare('SELECT key, value FROM settings').all()) {
    out[row.key] = row.value;
  }
  return out;
}

/** Run `fn` inside a transaction, rolling back if it throws. */
export function withTransaction(db, fn) {
  db.exec('BEGIN');
  try {
    const result = fn();
    db.exec('COMMIT');
    return result;
  } catch (error) {
    try { db.exec('ROLLBACK'); } catch { /* already rolled back */ }
    throw error;
  }
}
