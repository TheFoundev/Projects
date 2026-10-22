/**
 * The data layer the views talk to.
 *
 * Reads go to the server when it is reachable and fall back to the local
 * mirror when it is not. Writes are always applied to the mirror first, then
 * queued for the server, so a write made on a train is not lost.
 */

/** The generic entities that map one to one onto a table. */
export const GENERIC_ENTITIES = [
  'accounts',
  'category_groups',
  'categories',
  'rules',
  'schedules',
  'goals',
];

/** The tables the client keeps a mirror of. */
export const MIRRORED_TABLES = [
  'accounts',
  'category_groups',
  'categories',
  'transactions',
  'budget_months',
  'rules',
  'schedules',
  'goals',
];

export class DataLayer {
  constructor({ api, engine }) {
    this.api = api;
    this.engine = engine;
    this.online = true;
  }

  /** True when the last interaction with the server succeeded. */
  isOnline() {
    return this.online;
  }

  /**
   * List a generic entity. The server is asked first; when it cannot be
   * reached the local mirror is used instead.
   */
  async list(entity, query = '') {
    try {
      const rows = await this.api.get(`/${entity}${query}`);
      this.online = true;
      for (const row of rows) await this.engine.store.putRow(entity, row);
      return rows;
    } catch (error) {
      this.online = false;
      return this.engine.store.getAll(entity);
    }
  }

  /** Read one row of a generic entity. */
  async get(entity, id) {
    try {
      const row = await this.api.get(`/${entity}/${id}`);
      this.online = true;
      await this.engine.store.putRow(entity, row);
      return row;
    } catch (error) {
      this.online = false;
      const rows = await this.engine.store.getAll(entity);
      return rows.find((row) => row.id === Number(id)) || null;
    }
  }

  /**
   * Create a row. The row is written to the mirror and queued, and the server
   * is asked to create it as well. The server's row (with its id) wins.
   */
  async create(entity, body) {
    const local = await this.engine.applyLocalChange(entity, { ...body, id: body.id || -Date.now() });
    try {
      const created = await this.api.post(`/${entity}`, body);
      this.online = true;
      await this.engine.store.putRow(entity, created);
      return created;
    } catch (error) {
      this.online = false;
      return local;
    }
  }

  /** Update a row. */
  async update(entity, id, body) {
    const existing = await this.get(entity, id);
    const merged = { ...(existing || {}), ...body, id: Number(id) };
    await this.engine.applyLocalChange(entity, merged);

    try {
      const updated = await this.api.patch(`/${entity}/${id}`, body);
      this.online = true;
      await this.engine.store.putRow(entity, updated);
      return updated;
    } catch (error) {
      this.online = false;
      return merged;
    }
  }

  /** Delete a row (a soft delete on the server, a deleted flag locally). */
  async remove(entity, id) {
    const existing = await this.get(entity, id);
    if (existing) await this.engine.applyLocalDelete(entity, existing);

    try {
      await this.api.del(`/${entity}/${id}`);
      this.online = true;
      await this.engine.store.removeRow(entity, Number(id));
      return true;
    } catch (error) {
      this.online = false;
      return false;
    }
  }

  /** List transactions, from the server or the mirror. */
  async listTransactions(query = '') {
    try {
      const rows = await this.api.getTransactions(query);
      this.online = true;
      for (const row of rows) await this.engine.store.putRow('transactions', row);
      return rows;
    } catch (error) {
      this.online = false;
      return this.engine.store.getAll('transactions');
    }
  }

  /** Create a transaction. */
  async createTransaction(body) {
    const local = await this.engine.applyLocalChange('transactions', { ...body, id: -Date.now() });
    try {
      const response = await this.api.postTransaction(body);
      this.online = true;
      // The endpoint answers with { transaction, counterpart }.
      const created = response.transaction || response;
      await this.engine.store.putRow('transactions', created);
      return created;
    } catch (error) {
      this.online = false;
      return local;
    }
  }

  /** Update a transaction. */
  async updateTransaction(id, body) {
    const existing = (await this.listTransactions()).find((row) => row.id === Number(id));
    if (existing) await this.engine.applyLocalChange('transactions', { ...existing, ...body, id: Number(id) });

    try {
      const response = await this.api.patchTransaction(id, body);
      this.online = true;
      const updated = response.transaction || response;
      if (updated) await this.engine.store.putRow('transactions', updated);
      return updated || existing;
    } catch (error) {
      this.online = false;
      return existing;
    }
  }

  /** Delete a transaction. */
  async removeTransaction(id) {
    const existing = (await this.listTransactions()).find((row) => row.id === Number(id));
    if (existing) await this.engine.applyLocalDelete('transactions', existing);

    try {
      await this.api.deleteTransaction(id);
      this.online = true;
      await this.engine.store.removeRow('transactions', Number(id));
      return true;
    } catch (error) {
      this.online = false;
      return false;
    }
  }

  /** Import a CSV statement. */
  async importCsv(body) {
    const result = await this.api.importCsv(body);
    this.online = true;
    return result;
  }
}
