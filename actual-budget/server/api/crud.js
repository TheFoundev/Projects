/**
 * Generic CRUD for the plain entities: one table, one column spec, five routes.
 *
 * Column specs declare how a request field becomes a SQL value and what an
 * absent field becomes on create. Table and column names come from these
 * constants; every value is bound as a parameter.
 */

import { notFound, nowIso, toPlain, toPlainList, badRequest, isTruthy } from '../util.js';
import { ACCOUNT_TYPES } from '../domain/accounts.js';
import { RULE_FIELDS, RULE_OPS } from '../domain/rules.js';
import { FREQUENCIES } from '../domain/schedule.js';
import * as V from './validate.js';

const str = (field, opts = {}) => (value) => V.asString(value, { field, ...opts });
const int = (field, opts = {}) => (value) => V.asInt(value, { field, ...opts });
const bool = (field, defaultValue = 0) => (value) => V.asBool(value, { field, defaultValue });
const cents = (field, opts = {}) => (value) => V.asCents(value, { field, ...opts });
const date = (field, opts = {}) => (value) => V.asDate(value, { field, ...opts });

/** @type {Record<string, {table:string, columns:Object, filters?:Object, order:string}>} */
export const ENTITY_SPECS = {
  accounts: {
    table: 'accounts',
    order: 'sort_order ASC, name COLLATE NOCASE ASC',
    filters: { on_budget: 'bool', closed: 'bool' },
    columns: {
      name: { coerce: str('name', { allowEmpty: false, max: 120 }), required: true },
      type: { coerce: (v) => V.asEnum(v, ACCOUNT_TYPES, { field: 'type', defaultValue: 'checking' }), default: 'checking' },
      on_budget: { coerce: bool('on_budget', 1), default: 1 },
      closed: { coerce: bool('closed', 0), default: 0 },
      note: { coerce: str('note', { max: 1000 }), default: '' },
      sort_order: { coerce: int('sort_order'), default: 0 },
    },
  },

  category_groups: {
    table: 'category_groups',
    order: 'sort_order ASC, id ASC',
    filters: { is_income: 'bool' },
    columns: {
      name: { coerce: str('name', { allowEmpty: false, max: 120 }), required: true },
      is_income: { coerce: bool('is_income', 0), default: 0 },
      sort_order: { coerce: int('sort_order'), default: 0 },
    },
  },

  categories: {
    table: 'categories',
    order: 'sort_order ASC, name COLLATE NOCASE ASC',
    filters: { group_id: 'int', hidden: 'bool' },
    columns: {
      group_id: { coerce: int('group_id', { nullable: true }), default: null },
      name: { coerce: str('name', { allowEmpty: false, max: 120 }), required: true },
      note: { coerce: str('note', { max: 1000 }), default: '' },
      sort_order: { coerce: int('sort_order'), default: 0 },
      hidden: { coerce: bool('hidden', 0), default: 0 },
    },
  },

  rules: {
    table: 'rules',
    order: 'priority ASC, id ASC',
    filters: { enabled: 'bool', set_category_id: 'int' },
    columns: {
      priority: { coerce: int('priority', { defaultValue: 0 }), default: 0 },
      field: { coerce: (value) => V.asEnum(value, RULE_FIELDS, { field: 'field', required: true }), required: true },
      op: { coerce: (value) => V.asEnum(value, RULE_OPS, { field: 'op', required: true }), required: true },
      value: { coerce: str('value', { allowEmpty: false, max: 200 }), required: true },
      set_category_id: { coerce: int('set_category_id', { nullable: true }), default: null },
      enabled: { coerce: bool('enabled', 1), default: 1 },
    },
  },

  schedules: {
    table: 'schedules',
    order: 'next_date ASC, id ASC',
    filters: { account_id: 'int', category_id: 'int', auto_post: 'bool' },
    columns: {
      account_id: { coerce: int('account_id', { required: true }), required: true },
      payee: { coerce: str('payee', { max: 200 }), default: '' },
      memo: { coerce: str('memo', { max: 500 }), default: '' },
      amount_cents: { coerce: cents('amount_cents', { required: true }), required: true },
      category_id: { coerce: int('category_id', { nullable: true }), default: null },
      frequency: { coerce: (value) => V.asEnum(value, FREQUENCIES, { field: 'frequency', defaultValue: 'monthly' }), default: 'monthly' },
      interval_n: { coerce: int('interval_n', { min: 1, max: 120, defaultValue: 1 }), default: 1 },
      next_date: { coerce: date('next_date', { required: true }), required: true },
      end_date: { coerce: date('end_date', { nullable: true }), default: null },
      auto_post: { coerce: bool('auto_post', 0), default: 0 },
    },
  },

  goals: {
    table: 'goals',
    order: 'target_date ASC, id ASC',
    filters: { category_id: 'int' },
    columns: {
      category_id: { coerce: int('category_id', { required: true }), required: true },
      target_cents: { coerce: cents('target_cents', { required: true }), required: true },
      target_date: { coerce: date('target_date', { nullable: true }), default: null },
      monthly_cents: { coerce: cents('monthly_cents', { defaultValue: 0 }), default: 0 },
    },
  },
};

/** Turn a request body into column values. Unknown keys are ignored. */
export function buildValues(spec, body, { patch }) {
  const values = {};

  for (const [column, def] of Object.entries(spec.columns)) {
    const provided = Object.prototype.hasOwnProperty.call(body, column);

    if (!provided) {
      if (patch) continue;
      if ('default' in def) { values[column] = def.default; continue; }
      if (def.required) throw badRequest(`"${column}" is required`);
      continue;
    }

    values[column] = def.coerce(body[column], column);
  }

  return values;
}

function idParam(ctx) {
  const id = Number(ctx.params.id);
  if (!Number.isInteger(id) || id <= 0) throw badRequest('id must be a positive integer');
  return id;
}

function selectById(db, table, id, { includeDeleted = false } = {}) {
  const sql = `SELECT * FROM ${table} WHERE id = ?${includeDeleted ? '' : ' AND deleted = 0'}`;
  const row = db.prepare(sql).get(id);
  if (!row) throw notFound(`${table} ${id} not found`);
  return toPlain(row);
}

function listRows(db, spec, ctx) {
  const where = [];
  const params = [];

  if (ctx.query.get('include_deleted') === '1') {
    where.push('1 = 1');
  } else {
    where.push('deleted = 0');
  }

  for (const [column, type] of Object.entries(spec.filters || {})) {
    const raw = ctx.query.get(column);
    if (raw === null) continue;
    where.push(`${column} = ?`);
    params.push(type === 'bool' ? (isTruthy(raw) ? 1 : 0) : Number(raw));
  }

  const sql = `SELECT * FROM ${spec.table} WHERE ${where.join(' AND ')} ORDER BY ${spec.order}`;
  return toPlainList(db.prepare(sql).all(...params));
}

function createRow(db, spec, ctx) {
  const values = buildValues(spec, ctx.body, { patch: false });
  const columns = Object.keys(values);

  const sql = columns.length
    ? `INSERT INTO ${spec.table} (${columns.join(', ')}, updated_at, deleted) VALUES (${columns.map(() => '?').join(', ')}, ?, 0)`
    : `INSERT INTO ${spec.table} (updated_at, deleted) VALUES (?, 0)`;

  const info = db.prepare(sql).run(...columns.map((c) => values[c]), nowIso());
  return selectById(db, spec.table, Number(info.lastInsertRowid), { includeDeleted: true });
}

function updateRow(db, spec, ctx) {
  const id = idParam(ctx);
  selectById(db, spec.table, id); // 404s if missing

  const values = buildValues(spec, ctx.body, { patch: true });
  const columns = Object.keys(values);

  if (columns.length > 0) {
    const sql = `UPDATE ${spec.table} SET ${columns.map((c) => `${c} = ?`).join(', ')}, updated_at = ? WHERE id = ?`;
    db.prepare(sql).run(...columns.map((c) => values[c]), nowIso(), id);
  }

  return selectById(db, spec.table, id);
}

function deleteRow(db, spec, ctx) {
  const id = idParam(ctx);
  selectById(db, spec.table, id);
  db.prepare(`UPDATE ${spec.table} SET deleted = 1, updated_at = ? WHERE id = ?`).run(nowIso(), id);
  return { id, deleted: true };
}

/** Register the five CRUD routes for one entity. */
export function registerEntity(router, db, name) {
  const spec = ENTITY_SPECS[name];
  if (!spec) throw new Error(`no spec for entity "${name}"`);

  router.get(`/api/${name}`, (ctx) => listRows(db, spec, ctx));
  router.get(`/api/${name}/:id`, (ctx) => selectById(db, spec.table, idParam(ctx), { includeDeleted: true }));
  router.post(`/api/${name}`, (ctx) => createRow(db, spec, ctx));
  router.patch(`/api/${name}/:id`, (ctx) => updateRow(db, spec, ctx));
  router.delete(`/api/${name}/:id`, (ctx) => deleteRow(db, spec, ctx));
}
