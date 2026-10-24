/**
 * Local storage for the offline mirror.
 *
 * Two adapters implement the same interface:
 *
 *   MemoryStore      - used by the tests and as a fallback when IndexedDB is
 *                      unavailable (private browsing modes, for example).
 *   IndexedDbStore   - the real thing, used in the browser.
 *
 * The interface is deliberately small so the sync engine never has to care
 * which one it is talking to:
 *
 *   getAll(table)              -> rows
 *   putRow(table, row)         -> row
 *   removeRow(table, id)       -> void
 *   getQueue()                 -> [{ table, row }]
 *   enqueue(table, row)        -> void
 *   dropQueueEntries(entries)  -> void
 *   getMeta(key)               -> value | null
 *   setMeta(key, value)        -> void
 */

/** A row id is only unique inside its table, so the key is namespaced. */
function rowKey(table, id) {
  return `${table}:${id}`;
}

/** An in-memory adapter. Also the fallback when IndexedDB is not available. */
export class MemoryStore {
  constructor() {
    this.tables = new Map();
    this.queue = [];
    this.meta = new Map();
  }

  async getAll(table) {
    const rows = this.tables.get(table);
    return rows ? [...rows.values()] : [];
  }

  async putRow(table, row) {
    if (!this.tables.has(table)) this.tables.set(table, new Map());
    this.tables.get(table).set(row.id, { ...row });
    return { ...row };
  }

  async removeRow(table, id) {
    const rows = this.tables.get(table);
    if (rows) rows.delete(id);
  }

  async getQueue() {
    return this.queue.map((entry) => ({ ...entry, row: { ...entry.row } }));
  }

  async enqueue(table, row) {
    this.queue.push({ table, row: { ...row } });
  }

  async dropQueueEntries(entries) {
    const drop = new Set(entries.map((entry) => `${entry.table}:${entry.row.id}:${entry.row.updated_at}`));
    this.queue = this.queue.filter(
      (entry) => !drop.has(`${entry.table}:${entry.row.id}:${entry.row.updated_at}`),
    );
  }

  async getMeta(key) {
    return this.meta.has(key) ? this.meta.get(key) : null;
  }

  async setMeta(key, value) {
    this.meta.set(key, value);
  }
}

/** The IndexedDB adapter used in the browser. */
export class IndexedDbStore {
  constructor({ dbName = 'actual-budget', version = 1 } = {}) {
    this.dbName = dbName;
    this.version = version;
    this.dbPromise = null;
  }

  /** True when the environment can actually use IndexedDB. */
  static isAvailable() {
    return typeof indexedDB !== 'undefined' && indexedDB !== null;
  }

  open() {
    if (this.dbPromise) return this.dbPromise;

    this.dbPromise = new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, this.version);

      request.onupgradeneeded = () => {
        const db = request.result;
        if (!db.objectStoreNames.contains('rows')) {
          const rows = db.createObjectStore('rows', { keyPath: 'key' });
          rows.createIndex('table', 'table', { unique: false });
        }
        if (!db.objectStoreNames.contains('queue')) {
          db.createObjectStore('queue', { keyPath: 'seq', autoIncrement: true });
        }
        if (!db.objectStoreNames.contains('meta')) {
          db.createObjectStore('meta', { keyPath: 'key' });
        }
      };

      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });

    return this.dbPromise;
  }

  /** Run a transaction and resolve with whatever the callback returns. */
  async tx(storeNames, mode, work) {
    const db = await this.open();

    return new Promise((resolve, reject) => {
      const transaction = db.transaction(storeNames, mode);
      let result;
      transaction.oncomplete = () => resolve(result);
      transaction.onerror = () => reject(transaction.error);
      transaction.onabort = () => reject(transaction.error);
      result = work(transaction);
    });
  }

  async getAll(table) {
    return this.tx(['rows'], 'readonly', (transaction) => {
      const store = transaction.objectStore('rows');
      const index = store.index('table');
      const request = index.getAll(table);
      let rows = [];
      request.onsuccess = () => { rows = request.result; };
      return rows;
    });
  }

  async putRow(table, row) {
    const value = { key: rowKey(table, row.id), table, ...row };
    await this.tx(['rows'], 'readwrite', (transaction) => {
      transaction.objectStore('rows').put(value);
    });
    return { ...row };
  }

  async removeRow(table, id) {
    await this.tx(['rows'], 'readwrite', (transaction) => {
      transaction.objectStore('rows').delete(rowKey(table, id));
    });
  }

  async getQueue() {
    return this.tx(['queue'], 'readonly', (transaction) => {
      const request = transaction.objectStore('queue').getAll();
      let entries = [];
      request.onsuccess = () => { entries = request.result; };
      return entries.map((entry) => ({ table: entry.table, row: entry.row }));
    });
  }

  async enqueue(table, row) {
    await this.tx(['queue'], 'readwrite', (transaction) => {
      transaction.objectStore('queue').add({ table, row: { ...row } });
    });
  }

  async dropQueueEntries(entries) {
    if (entries.length === 0) return;
    const drop = new Set(entries.map((entry) => `${entry.table}:${entry.row.id}:${entry.row.updated_at}`));
    await this.tx(['queue'], 'readwrite', (transaction) => {
      const store = transaction.objectStore('queue');
      const request = store.openCursor();
      request.onsuccess = () => {
        const cursor = request.result;
        if (!cursor) return;
        const entry = cursor.value;
        const key = `${entry.table}:${entry.row.id}:${entry.row.updated_at}`;
        if (drop.has(key)) cursor.delete();
        cursor.continue();
      };
    });
  }

  async getMeta(key) {
    return this.tx(['meta'], 'readonly', (transaction) => {
      const request = transaction.objectStore('meta').get(key);
      let value = null;
      request.onsuccess = () => { value = request.result ? request.result.value : null; };
      return value;
    });
  }

  async setMeta(key, value) {
    await this.tx(['meta'], 'readwrite', (transaction) => {
      transaction.objectStore('meta').put({ key, value });
    });
  }
}

/**
 * Return the best available store: IndexedDB in the browser, memory otherwise.
 */
export function createStore(options = {}) {
  if (IndexedDbStore.isAvailable()) return new IndexedDbStore(options);
  return new MemoryStore();
}
