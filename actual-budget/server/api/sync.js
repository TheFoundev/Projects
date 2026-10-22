/**
 * Local-first sync.
 *
 * The client keeps a mirror of every syncable table and pushes its queued rows
 * here. Conflicts resolve last-write-wins, per row, by `updated_at`
 * (ISO-8601 UTC) — the same rule the client applies in the other direction.
 *
 * Deletes are soft, so a deletion travels exactly like an edit.
 */

import { SYNC_TABLES, SYNC_COLUMNS } from '../db.js';
import { nowIso, toPlain, badRequest } from '../util.js';

const EPOCH = '1970-01-01T00:00:00.000Z';

function has(row, key) {
  return Object.prototype.hasOwnProperty.call(row, key);
}

/** Find the stored row an incoming row refers to, by id or natural key. */
function findExisting(db, table, row) {
  if (row.id != null) {
    const byId = db.prepare(`SELECT * FROM ${table} WHERE id = ?`).get(Number(row.id));
    if (byId) return byId;
  }
  if (table === 'budget_months' && row.month && row.category_id != null) {
    return db.prepare('SELECT * FROM budget_months WHERE month = ? AND category_id = ?').get(String(row.month), Number(row.category_id)) || null;
  }
  return null;
}

/**
 * Apply one incoming row. Returns 'inserted' | 'updated' | 'skipped'.
 * An incoming row that is not newer than what is stored is skipped, which is
 * what makes the merge last-write-wins.
 */
export function applyIncoming(db, table, row) {
  const columns = SYNC_COLUMNS[table];
  if (!columns) throw badRequest(`unknown sync table "${table}"`);

  const updatedAt = typeof row.updated_at === 'string' && row.updated_at ? row.updated_at : nowIso();
  const deleted = row.deleted ? 1 : 0;

  const values = {};
  for (const column of columns) {
    if (has(row, column)) values[column] = row[column];
  }

  const existing = findExisting(db, table, row);

  if (existing) {
    if (String(updatedAt) <= String(existing.updated_at)) return 'skipped';

    const sets = Object.keys(values).map((c) => `${c} = ?`);
    const params = Object.keys(values).map((c) => values[c]);
    sets.push('updated_at = ?', 'deleted = ?');
    params.push(updatedAt, deleted);

    db.prepare(`UPDATE ${table} SET ${sets.join(', ')} WHERE id = ?`).run(...params, existing.id);
    return 'updated';
  }

  const insertColumns = Object.keys(values);
  const placeholders = insertColumns.map(() => '?');
  const params = insertColumns.map((c) => values[c]);

  if (row.id != null) {
    insertColumns.unshift('id');
    placeholders.unshift('?');
    params.unshift(Number(row.id));
  }

  insertColumns.push('updated_at', 'deleted');
  placeholders.push('?', '?');
  params.push(updatedAt, deleted);

  db.prepare(`INSERT INTO ${table} (${insertColumns.join(', ')}) VALUES (${placeholders.join(', ')})`).run(...params);
  return 'inserted';
}

export function registerSync(router, db) {
  // Everything changed since the client's last pull.
  router.get('/api/sync/pull', (ctx) => {
    const since = (ctx.query.get('since') || EPOCH).slice(0, 40);
    const changes = {};
    let total = 0;

    for (const table of SYNC_TABLES) {
      const rows = db.prepare(`SELECT * FROM ${table} WHERE updated_at > ? ORDER BY updated_at ASC`).all(since);
      changes[table] = rows.map((r) => toPlain(r));
      total += rows.length;
    }

    return { server_time: nowIso(), since, total, changes };
  });

  // Apply the client's queued rows.
  router.post('/api/sync/push', (ctx) => {
    const changes = ctx.body && ctx.body.changes;
    if (!changes || typeof changes !== 'object') throw badRequest('"changes" must be an object of table -> rows');

    const applied = {};
    const skipped = {};
    const errors = [];

    for (const [table, rows] of Object.entries(changes)) {
      if (!SYNC_TABLES.includes(table)) { errors.push({ table, message: 'unknown table' }); continue; }
      if (!Array.isArray(rows)) { errors.push({ table, message: 'expected an array of rows' }); continue; }

      applied[table] = 0;
      skipped[table] = 0;

      db.exec('BEGIN');
      try {
        for (const row of rows) {
          applyIncoming(db, table, row) === 'skipped' ? (skipped[table] += 1) : (applied[table] += 1);
        }
        db.exec('COMMIT');
      } catch (error) {
        db.exec('ROLLBACK');
        applied[table] = 0;
        skipped[table] = 0;
        errors.push({ table, message: String(error.message || error) });
      }
    }

    return { server_time: nowIso(), applied, skipped, errors };
  });

  router.get('/api/sync/status', () => {
    const counts = {};
    for (const table of SYNC_TABLES) {
      counts[table] = db.prepare(`SELECT COUNT(*) AS n FROM ${table} WHERE deleted = 0`).get().n;
    }
    return { server_time: nowIso(), tables: SYNC_TABLES, counts };
  });
}
