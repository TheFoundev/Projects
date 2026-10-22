/**
 * CSV bank import.
 *
 * This is the part of "bank sync" that can honestly work offline: read an
 * export, find the date / payee / amount columns, detect duplicates by content
 * hash, and let rules categorise the rows on the way in.
 */

import { createHash } from 'node:crypto';
import { badRequest, nowIso } from '../util.js';
import { parseCents } from '../money.js';
import { applyRules } from '../domain/rules.js';
import * as V from './validate.js';

const DATE_KEYS = ['date', 'transaction_date', 'posted_date', 'posting_date', 'value_date', 'booked_at'];
const PAYEE_KEYS = ['payee', 'description', 'name', 'merchant', 'details', 'narrative', 'reference'];
const MEMO_KEYS = ['memo', 'notes', 'note', 'comment', 'message'];
const AMOUNT_KEYS = ['amount', 'value', 'transaction_amount'];
const DEBIT_KEYS = ['debit', 'withdrawal', 'withdrawals', 'money_out', 'paid_out'];
const CREDIT_KEYS = ['credit', 'deposit', 'deposits', 'money_in', 'paid_in'];

const pad2 = (n) => String(n).padStart(2, '0');

/** Minimal RFC-4180 parser: quotes, escaped quotes, embedded commas/newlines. */
export function parseCsv(text) {
  const rows = [];
  let row = [];
  let field = '';
  let quoted = false;

  for (let i = 0; i < text.length; i += 1) {
    const ch = text[i];
    if (quoted) {
      if (ch === '"') {
        if (text[i + 1] === '"') { field += '"'; i += 1; } else quoted = false;
      } else field += ch;
    } else if (ch === '"') {
      quoted = true;
    } else if (ch === ',') {
      row.push(field); field = '';
    } else if (ch === '\n') {
      row.push(field); rows.push(row); row = []; field = '';
    } else if (ch !== '\r') {
      field += ch;
    }
  }
  if (field !== '' || row.length) { row.push(field); rows.push(row); }
  return rows;
}

function normalize(text) {
  return String(text || '').trim().toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '');
}

function pick(header, keys) {
  for (const key of keys) {
    const index = header.indexOf(key);
    if (index !== -1) return index;
  }
  return -1;
}

/** Best-effort date parsing: ISO, YYYY/MM/DD, MM/DD/YYYY (DD/MM when >12). */
export function parseImportDate(value) {
  const raw = String(value || '').trim();
  if (!raw) return null;

  if (/^\d{4}-\d{2}-\d{2}/.test(raw)) return raw.slice(0, 10);

  let m = raw.match(/^(\d{4})[/.](\d{1,2})[/.](\d{1,2})$/);
  if (m) return `${m[1]}-${pad2(m[2])}-${pad2(m[3])}`;

  m = raw.match(/^(\d{1,2})[/.](\d{1,2})[/.](\d{2,4})$/);
  if (m) {
    let [, a, b, year] = m;
    const month = Number(a) > 12 ? b : a;
    const day = Number(a) > 12 ? a : b;
    if (year.length === 2) year = `20${year}`;
    return `${year}-${pad2(month)}-${pad2(day)}`;
  }

  const parsed = new Date(raw);
  return Number.isNaN(parsed.getTime()) ? null : parsed.toISOString().slice(0, 10);
}

function readCents(value) {
  const raw = String(value ?? '').trim();
  if (!raw) return null;
  try { return parseCents(raw); } catch { return null; }
}

/** Parse CSV text into transaction rows plus a list of skipped lines. */
export function parseStatement(text) {
  const rows = parseCsv(text).filter((r) => r.some((c) => String(c).trim() !== ''));
  if (rows.length === 0) throw badRequest('the CSV is empty');

  const header = rows.shift().map(normalize);
  const idx = {
    date: pick(header, DATE_KEYS),
    payee: pick(header, PAYEE_KEYS),
    memo: pick(header, MEMO_KEYS),
    amount: pick(header, AMOUNT_KEYS),
    debit: pick(header, DEBIT_KEYS),
    credit: pick(header, CREDIT_KEYS),
  };

  if (idx.date === -1) throw badRequest(`no date column found (looked for: ${DATE_KEYS.join(', ')})`);
  if (idx.amount === -1 && idx.debit === -1 && idx.credit === -1) {
    throw badRequest('no amount column found (need an "amount", or "debit"/"credit" pair)');
  }

  const parsed = [];
  const skipped = [];

  rows.forEach((row, i) => {
    const date = parseImportDate(row[idx.date]);

    let amount = idx.amount !== -1 ? readCents(row[idx.amount]) : null;
    if (amount === null && (idx.debit !== -1 || idx.credit !== -1)) {
      const debit = idx.debit !== -1 ? Math.abs(readCents(row[idx.debit]) ?? 0) : 0;
      const credit = idx.credit !== -1 ? Math.abs(readCents(row[idx.credit]) ?? 0) : 0;
      if (debit || credit) amount = credit - debit;
    }

    if (!date || amount === null) {
      skipped.push({ line: i + 2, reason: !date ? 'unreadable date' : 'unreadable amount' });
      return;
    }

    parsed.push({
      date,
      payee: idx.payee !== -1 ? String(row[idx.payee] ?? '').trim() : '',
      memo: idx.memo !== -1 ? String(row[idx.memo] ?? '').trim() : '',
      amount_cents: amount,
    });
  });

  return { parsed, skipped };
}

/** Stable content hash, so re-importing the same export adds nothing. */
export function importHash(accountId, date, amountCents, payee) {
  return createHash('sha1')
    .update(`${accountId}|${date}|${amountCents}|${String(payee).toLowerCase()}`)
    .digest('hex');
}

export function registerImport(router, db) {
  router.post('/api/import/csv', (ctx) => {
    const accountId = V.asInt(ctx.body.account_id, { field: 'account_id', required: true });
    const account = db.prepare('SELECT id, name FROM accounts WHERE id = ? AND deleted = 0').get(accountId);
    if (!account) throw badRequest(`account ${accountId} does not exist`);

    if (typeof ctx.body.csv !== 'string' || ctx.body.csv.trim() === '') {
      throw badRequest('"csv" must be the CSV text');
    }

    const dryRun = Boolean(ctx.body.dry_run);
    const { parsed, skipped } = parseStatement(ctx.body.csv);
    const rules = db.prepare('SELECT * FROM rules WHERE deleted = 0').all();

    let imported = 0;
    let duplicates = 0;
    const inserted = [];

    for (const row of parsed) {
      const hash = importHash(accountId, row.date, row.amount_cents, row.payee);
      if (db.prepare('SELECT id FROM transactions WHERE import_hash = ?').get(hash)) {
        duplicates += 1;
        continue;
      }

      const matched = applyRules(rules, row);

      if (dryRun) {
        inserted.push({ ...row, category_id: matched });
        continue;
      }

      const info = db.prepare(
        `INSERT INTO transactions
           (account_id, date, payee, memo, amount_cents, category_id, cleared, reconciled, import_hash, updated_at, deleted)
         VALUES (?, ?, ?, ?, ?, ?, 0, 0, ?, ?, 0)`
      ).run(accountId, row.date, row.payee, row.memo, row.amount_cents, matched, hash, nowIso());

      imported += 1;
      inserted.push({ id: Number(info.lastInsertRowid), ...row, category_id: matched });
    }

    return {
      account_id: accountId,
      dry_run: dryRun,
      rows_found: parsed.length,
      imported,
      duplicates,
      skipped,
      transactions: inserted.slice(0, 200),
    };
  });
}
