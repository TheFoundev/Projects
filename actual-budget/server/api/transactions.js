/**
 * Transactions. CRUD plus three behaviours the generic layer cannot express:
 * rule-based categorisation, transfers, and a bulk "apply rules" pass.
 */

import { badRequest, notFound, nowIso, toPlain, toPlainList, isTruthy } from '../util.js';
import { monthBounds } from '../domain/dates.js';
import { applyRules } from '../domain/rules.js';
import * as V from './validate.js';

const SORTABLE = { date: 'date', payee: 'payee', amount: 'amount_cents', id: 'id' };

function has(body, key) {
  return Object.prototype.hasOwnProperty.call(body, key);
}

/** Coerce a request body into a transactions row. */
export function coerceTransaction(body, { patch }) {
  const out = {};
  const has2 = (k) => Object.prototype.hasOwnProperty.call(body, k);

  if (!patch) {
    for (const field of ['account_id', 'date', 'amount_cents']) {
      if (!has2(field)) throw badRequest(`"${field}" is required`);
    }
  }

  if (has2('account_id')) out.account_id = V.asInt(body.account_id, { field: 'account_id', required: true });
  if (has2('date')) out.date = V.asDate(body.date, { field: 'date', required: true });
  if (has2('amount_cents')) out.amount_cents = V.asCents(body.amount_cents, { field: 'amount_cents' });
  if (has2('payee')) out.payee = V.asString(body.payee, { field: 'payee', max: 200 });
  if (has2('memo')) out.memo = V.asString(body.memo, { field: 'memo', max: 500 });
  if (has2('category_id')) out.category_id = V.asInt(body.category_id, { field: 'category_id', nullable: true });
  if (has2('cleared')) out.cleared = V.asBool(body.cleared, { field: 'cleared' });
  if (has2('reconciled')) out.reconciled = V.asBool(body.reconciled, { field: 'reconciled' });
  if (has2('transfer_account_id')) {
    out.transfer_account_id = V.asInt(body.transfer_account_id, { field: 'transfer_account_id', nullable: true });
  }
  if (has2('schedule_id')) out.schedule_id = V.asInt(body.schedule_id, { field: 'schedule_id', nullable: true });
  if (has2('import_hash')) out.import_hash = V.asString(body.import_hash, { field: 'import_hash', max: 200 }) || null;

  return out;
}

function insertTransaction(db, values) {
  const columns = Object.keys(values);
  const sql = `INSERT INTO transactions (${columns.join(', ')}, updated_at, deleted) VALUES (${columns.map(() => '?').join(', ')}, ?, 0)`;
  const info = db.prepare(sql).run(...columns.map((c) => values[c]), nowIso());
  return Number(info.lastInsertRowid);
}

/** The other leg of a transfer, if it exists. */
function findCounterpart(db, tx) {
  if (tx.transfer_account_id == null) return null;
  return db.prepare(
    `SELECT * FROM transactions
      WHERE deleted = 0
        AND account_id = ? AND transfer_account_id = ?
        AND date = ? AND amount_cents = ?
      LIMIT 1`
  ).get(tx.transfer_account_id, tx.account_id, tx.date, -tx.amount_cents) || null;
}

function createWithTransfer(db, values) {
  if (values.transfer_account_id == null) {
    const id = insertTransaction(db, values);
    return { transaction: getTransaction(db, id) };
  }

  const from = values.account_id;
  const to = values.transfer_account_id;
  if (from === to) throw badRequest('a transfer needs two different accounts');

  const primaryId = insertTransaction(db, { ...values, category_id: null });
  const counterpartId = insertTransaction(db, {
    account_id: to,
    date: values.date,
    payee: values.payee ?? '',
    memo: values.memo ?? '',
    amount_cents: -values.amount_cents,
    category_id: null,
    cleared: values.cleared ?? 0,
    reconciled: 0,
    transfer_account_id: from,
  });

  return { transaction: getTransaction(db, primaryId), counterpart: getTransaction(db, counterpartId) };
}

export function getTransaction(db, id) {
  const row = db.prepare('SELECT * FROM transactions WHERE id = ? AND deleted = 0').get(id);
  if (!row) throw notFound(`transaction ${id} not found`);
  return toPlain(row);
}

function listTransactions(db, ctx) {
  const where = [];
  const params = [];

  if (ctx.query.get('include_deleted') === '1') where.push('1 = 1');
  else where.push('deleted = 0');

  const month = ctx.query.get('month');
  if (month && /^\d{4}-\d{2}$/.test(month)) {
    const { start, end } = monthBounds(month);
    where.push('date >= ? AND date <= ?');
    params.push(start, end);
  }
  const from = ctx.query.get('from');
  const to = ctx.query.get('to');
  if (from) { where.push('date >= ?'); params.push(from); }
  if (to) { where.push('date <= ?'); params.push(to); }

  const accountId = ctx.query.get('account_id');
  if (accountId) { where.push('account_id = ?'); params.push(Number(accountId)); }

  const categoryId = ctx.query.get('category_id');
  if (categoryId === 'uncategorized') where.push('category_id IS NULL');
  else if (categoryId) { where.push('category_id = ?'); params.push(Number(categoryId)); }

  const search = ctx.query.get('search');
  if (search) {
    where.push('(payee LIKE ? OR memo LIKE ?)');
    params.push(`%${search}%`, `%${search}%`);
  }

  const sortCol = ({ date: 'date', amount: 'amount_cents' })[ctx.query.get('sort')] || 'date';
  const dir = ctx.query.get('dir') === 'asc' ? 'ASC' : 'DESC';
  const limit = Math.min(Number(ctx.query.get('limit')) || 500, 2000);
  const offset = Math.max(Number(ctx.query.get('offset')) || 0, 0);

  const sql = `SELECT * FROM transactions WHERE ${where.join(' AND ')} ORDER BY ${sortCol} ${dir}, id ${dir} LIMIT ? OFFSET ?`;
  return toPlainList(db.prepare(sql).all(...params, limit, offset));
}

/** Register the transaction routes. */
export function registerTransactions(router, db) {
  router.get('/api/transactions', (ctx) => listTransactions(db, ctx));

  router.get('/api/transactions/:id', (ctx) => getTransaction(db, Number(ctx.params.id)));

  router.post('/api/transactions', (ctx) => {
    const values = coerceTransaction(ctx.body, { patch: false });

    // Auto-categorise with rules unless the caller was explicit, or it is a transfer.
    if (values.transfer_account_id == null && values.category_id == null && !has(ctx.body, 'category_id')) {
      const rules = db.prepare('SELECT * FROM rules WHERE deleted = 0').all();
      const matched = applyRules(rules, values);
      if (matched != null) values.category_id = matched;
    }

    const result = createWithTransfer(db, values);
    return { transaction: result.transaction, counterpart: result.counterpart ?? null };
  });

  router.patch('/api/transactions/:id', (ctx) => {
    const id = Number(ctx.params.id);
    getTransaction(db, id);
    const values = coerceTransaction(ctx.body, { patch: true });
    const columns = Object.keys(values);
    if (columns.length) {
      db.prepare(`UPDATE transactions SET ${columns.map((c) => `${c} = ?`).join(', ')}, updated_at = ? WHERE id = ?`)
        .run(...columns.map((c) => values[c]), nowIso(), id);
    }
    // The same shape the create endpoint answers with, so a client can
    // handle both without special casing.
    return { transaction: getTransaction(db, id), counterpart: findCounterpart(db, getTransaction(db, id)) };
  });

  router.delete('/api/transactions/:id', (ctx) => {
    const id = Number(ctx.params.id);
    const tx = getTransaction(db, id);
    const counterpart = findCounterpart(db, tx);

    db.prepare('UPDATE transactions SET deleted = 1, updated_at = ? WHERE id = ?').run(nowIso(), id);
    if (counterpart) {
      db.prepare('UPDATE transactions SET deleted = 1, updated_at = ? WHERE id = ?').run(nowIso(), counterpart.id);
    }
    return { id, deleted: true, counterpart_deleted: counterpart ? counterpart.id : null };
  });

  // Apply every enabled rule to the transactions that still have no category.
  router.post('/api/transactions/apply-rules', () => {
    const rules = db.prepare('SELECT * FROM rules WHERE deleted = 0').all();
    const pending = db.prepare('SELECT * FROM transactions WHERE deleted = 0 AND category_id IS NULL').all();

    let updated = 0;
    for (const tx of pending) {
      const matched = applyRules(rules, tx);
      if (matched != null) {
        db.prepare('UPDATE transactions SET category_id = ?, updated_at = ? WHERE id = ?').run(matched, nowIso(), tx.id);
        updated += 1;
      }
    }
    return { scanned: pending.length, updated };
  });
}
