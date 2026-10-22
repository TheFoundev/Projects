/**
 * The sync engine.
 *
 * The client keeps a mirror of every syncable table in local storage and a
 * queue of the changes it has made while offline. Syncing is:
 *
 *   push  - send the queued rows to the server, which merges them
 *   pull  - fetch everything that changed since the last pull and merge it in
 *
 * Both directions use the same rule: the row with the newer `updated_at`
 * wins. A delete travels like an edit because the flag is part of the row.
 *
 * The engine never touches the network directly, it goes through the `api`
 * object, so it can be tested without a server.
 */

/** The tables the client mirrors. Must match the server's SYNC_TABLES. */
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

const EPOCH = '1970-01-01T00:00:00.000Z';

/**
 * Merge one incoming row into the local row.
 *
 * Returns the row that should be kept, or null when the incoming row loses.
 */
export function mergeRow(local, incoming) {
  if (!local) return incoming;
  if (!incoming) return local;

  const localAt = String(local.updated_at || EPOCH);
  const incomingAt = String(incoming.updated_at || EPOCH);

  if (incomingAt > localAt) return incoming;
  return local;
}

export class SyncEngine {
  /**
   * @param {object} options
   * @param {object} options.store  a store adapter (see store.js)
   * @param {object} options.api    needs getSyncPull(since) and postSyncPush(changes)
   * @param {string[]} options.tables  the tables to mirror
   * @param {() => boolean} options.isOnline  connectivity probe
   */
  constructor({ store, api, tables = SYNC_TABLES, isOnline = () => true }) {
    this.store = store;
    this.api = api;
    this.tables = tables;
    this.isOnline = isOnline;
    this.syncing = false;
    this.lastError = null;
  }

  /** How many changes are waiting to be pushed. */
  async pendingCount() {
    const queue = await this.store.getQueue();
    return queue.length;
  }

  /** The rows of one table, straight from the local mirror. */
  async readTable(table) {
    return this.store.getAll(table);
  }

  /**
   * Apply a local change: write it to the mirror and queue it for the server.
   */
  async applyLocalChange(table, row) {
    const stamped = { ...row, updated_at: row.updated_at || new Date().toISOString() };
    await this.store.putRow(table, stamped);
    await this.store.enqueue(table, stamped);
    return stamped;
  }

  /** Apply a local delete: flag the row deleted and queue it. */
  async applyLocalDelete(table, row) {
    return this.applyLocalChange(table, { ...row, deleted: 1 });
  }

  /**
   * Fetch the changes the server has and merge them into the mirror.
   * Returns the number of rows that were taken from the server.
   */
  async pull() {
    if (!this.isOnline()) return { pulled: 0, offline: true };

    const since = (await this.store.getMeta('lastPulledAt')) || EPOCH;
    const response = await this.api.getSyncPull(since);
    const changes = (response && response.changes) || {};

    let pulled = 0;
    for (const table of this.tables) {
      const incomingRows = changes[table] || [];
      for (const incoming of incomingRows) {
        const local = (await this.store.getAll(table)).find((row) => row.id === incoming.id);
        const winner = mergeRow(local, incoming);
        if (winner === incoming && winner !== local) pulled += 1;
        await this.store.putRow(table, winner);
      }
    }

    if (response && response.server_time) {
      await this.store.setMeta('lastPulledAt', response.server_time);
    }

    return { pulled, offline: false };
  }

  /**
   * Send the queued changes to the server and drop the ones it accepted.
   * A failure leaves the queue untouched so nothing is lost.
   */
  async push() {
    if (!this.isOnline()) return { pushed: 0, offline: true };

    const queue = await this.store.getQueue();
    if (queue.length === 0) return { pushed: 0, offline: false };

    const changes = {};
    for (const entry of queue) {
      if (!changes[entry.table]) changes[entry.table] = [];
      changes[entry.table].push(entry.row);
    }

    const response = await this.api.postSyncPush(changes);
    const applied = (response && response.applied) || {};
    const total = Object.values(applied).reduce((sum, n) => sum + Number(n || 0), 0);

    // Everything the server did not report an error for can leave the queue.
    const failed = new Set((response && response.errors ? response.errors : []).map((e) => e.table));
    const settled = queue.filter((entry) => !failed.has(entry.table));
    await this.store.dropQueueEntries(settled);

    return { pushed: total, offline: false, errors: (response && response.errors) || [] };
  }

  /**
   * Push and then pull. Returns a small summary for the status bar.
   */
  async sync() {
    if (this.syncing) return { skipped: true };
    this.syncing = true;
    this.lastError = null;

    try {
      const push = await this.push();
      const pull = await this.pull();
      return { ...push, ...pull, skipped: false };
    } catch (error) {
      this.lastError = String(error.message || error);
      return { error: this.lastError, skipped: false };
    } finally {
      this.syncing = false;
    }
  }
}
