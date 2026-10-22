/** Small shared helpers. No I/O, no domain rules. */

/** Current time as an ISO-8601 UTC string. The one clock the app trusts. */
export function nowIso() {
  return new Date().toISOString();
}

/**
 * node:sqlite hands back null-prototype rows. Copy them into ordinary objects
 * so they behave like every other object in the codebase (and JSON).
 */
export function toPlain(row) {
  return row ? { ...row } : row;
}

export function toPlainList(rows) {
  return rows.map((r) => ({ ...r }));
}

/** HTTP-aware error. `status` is the response code, `code` a stable machine tag. */
export class HttpError extends Error {
  constructor(status, code, message, details) {
    super(message);
    this.name = 'HttpError';
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

export const badRequest = (message, details) => new HttpError(400, 'bad_request', message, details);
export const notFound = (message = 'not found') => new HttpError(404, 'not_found', message);
export const conflict = (message, details) => new HttpError(409, 'conflict', message, details);

/** Clamp an integer into [min, max]. */
export function clamp(n, min, max) {
  return Math.min(Math.max(n, min), max);
}

/** True for the strings a truthy flag usually arrives as. */
export function isTruthy(value) {
  if (typeof value === 'boolean') return value;
  if (typeof value === 'number') return value !== 0;
  return ['1', 'true', 'yes', 'on'].includes(String(value).toLowerCase());
}
