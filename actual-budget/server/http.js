/** HTTP plumbing: JSON responses, body reading, and a tiny pattern router. */

import { HttpError } from './util.js';

export function sendJson(res, status, payload) {
  const body = JSON.stringify(payload);
  res.writeHead(status, {
    'content-type': 'application/json; charset=utf-8',
    'content-length': Buffer.byteLength(body),
    'cache-control': 'no-store',
  });
  res.end(body);
}

/** Read and parse a JSON request body. Empty body -> {}. */
export async function readJson(req, { limit = 2 * 1024 * 1024 } = {}) {
  const chunks = [];
  let size = 0;

  for await (const chunk of req) {
    size += chunk.length;
    if (size > limit) throw new HttpError(413, 'payload_too_large', 'request body is too large');
    chunks.push(chunk);
  }

  if (size === 0) return {};
  const text = Buffer.concat(chunks).toString('utf8').trim();
  if (text === '') return {};

  let parsed;
  try {
    parsed = JSON.parse(text);
  } catch {
    throw new HttpError(400, 'bad_request', 'request body is not valid JSON');
  }
  if (parsed === null || typeof parsed !== 'object' || Array.isArray(parsed)) {
    throw new HttpError(400, 'bad_request', 'request body must be a JSON object');
  }
  return parsed;
}

/** Read and parse a raw text body (used by CSV import). */
export async function readText(req, { limit = 8 * 1024 * 1024 } = {}) {
  const chunks = [];
  let size = 0;
  for await (const chunk of req) {
    size += chunk.length;
    if (size > limit) throw new HttpError(413, 'payload_too_large', 'body is too large');
    chunks.push(chunk);
  }
  return Buffer.concat(chunks).toString('utf8');
}

/**
 * A router keyed on method + path, with `:name` parameters.
 *
 *   router.get('/api/accounts/:id', (ctx) => ...)   // ctx.params.id
 */
export class Router {
  constructor() {
    this.routes = [];
  }

  add(method, pattern, handler) {
    const names = [];
    const source = pattern
      .replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
      .replace(/\\?:([A-Za-z_][A-Za-z0-9_]*)/g, (_, name) => {
        names.push(name);
        return '([^/]+)';
      });
    this.routes.push({ method, regex: new RegExp(`^${source}/?$`), names, handler, pattern });
    return this;
  }

  get(pattern, handler) { return this.add('GET', pattern, handler); }
  post(pattern, handler) { return this.add('POST', pattern, handler); }
  put(pattern, handler) { return this.add('PUT', pattern, handler); }
  patch(pattern, handler) { return this.add('PATCH', pattern, handler); }
  delete(pattern, handler) { return this.add('DELETE', pattern, handler); }

  /** @returns {{handler:Function, params:Object}|null} */
  match(method, pathname) {
    for (const route of this.routes) {
      if (route.method !== method) continue;
      const m = route.regex.exec(pathname);
      if (!m) continue;
      const params = {};
      route.names.forEach((name, i) => {
        params[name] = decodeURIComponent(m[i + 1]);
      });
      return { handler: route.handler, params };
    }
    return null;
  }
}

/** Turn a thrown value into a JSON error response body. */
export function errorBody(error) {
  if (error instanceof HttpError) {
    return { status: error.status, body: { error: error.code, message: error.message, details: error.details } };
  }
  const message = String(error && error.message ? error.message : error);
  if (/SQLITE_CONSTRAINT/i.test(message)) {
    const code = /UNIQUE/i.test(message) ? 'conflict' : 'constraint_failed';
    const status = code === 'conflict' ? 409 : 400;
    return { status, body: { error: code, message } };
  }
  return { status: 500, body: { error: 'internal_error', message } };
}
