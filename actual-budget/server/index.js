/**
 * HTTP server.
 *
 * Serves the JSON API under /api and the static client from client/ (with the
 * vendored React/htm bundles from vendor/). No framework, no build step.
 */

import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { openDatabase, DEFAULT_DB_PATH } from './db.js';
import { Router, sendJson, readJson, errorBody } from './http.js';
import { ENTITY_SPECS, registerEntity } from './api/crud.js';
import { registerTransactions } from './api/transactions.js';
import { registerBudget } from './api/budget.js';
import { registerReports } from './api/reports.js';
import { registerSync } from './api/sync.js';
import { registerBootstrap } from './api/bootstrap.js';
import { registerBank } from './api/bank.js';
import { registerImport } from './api/import.js';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const CLIENT_DIR = path.join(ROOT, 'client');
const VENDOR_DIR = path.join(ROOT, 'vendor');

/** Every API route, in one place. */
export function buildRouter(db) {
  const router = new Router();

  router.get('/api/health', () => ({ ok: true, app: 'actual-budget', time: new Date().toISOString() }));

  for (const name of Object.keys(ENTITY_SPECS)) registerEntity(router, db, name);

  registerTransactions(router, db);   // must come after the generic entities
  registerBudget(router, db);
  registerReports(router, db);
  registerSync(router, db);
  registerBootstrap(router, db);
  registerBank(router);
  registerImport(router, db);

  return router;
}

const MIME_TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.mjs': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.ico': 'image/x-icon',
};

function sendFile(res, filePath) {
  const body = fs.readFileSync(filePath);
  const type = MIME_TYPES[path.extname(filePath).toLowerCase()] || 'application/octet-stream';
  res.writeHead(200, { 'content-type': type, 'content-length': body.length, 'cache-control': 'no-cache' });
  res.end(body);
}

/** Resolve a URL path to a file under one of the static roots, or null. */
function resolveStatic(pathname) {
  const roots = pathname.startsWith('/vendor/')
    ? [[VENDOR_DIR, pathname.slice('/vendor'.length)]]
    : [[CLIENT_DIR, pathname]];

  for (const [root, rel] of roots) {
    const candidate = path.join(root, path.normalize(rel).replace(/^(\.\.[\\/])+/, ''));
    if (!candidate.startsWith(root)) continue;
    if (fs.existsSync(candidate) && fs.statSync(candidate).isFile()) return candidate;
  }
  return null;
}

export function createServer({ db }) {
  const router = buildRouter(db);

  return http.createServer(async (req, res) => {
    const url = new URL(req.url, `http://${req.headers.host || 'localhost'}`);
    const pathname = decodeURIComponent(url.pathname);

    const matched = router.match(req.method, pathname);
    if (matched) {
      try {
        let body = {};
        if (req.method === 'POST' || req.method === 'PUT' || req.method === 'PATCH') {
          body = await readJson(req);
        }
        const result = await matched.handler({ db, params: matched.params, query: url.searchParams, body });
        if (!res.writableEnded) sendJson(res, 200, { data: result });
      } catch (error) {
        const { status, body } = errorBody(error);
        sendJson(res, status, body);
      }
      return;
    }

    if (req.method === 'GET' || req.method === 'HEAD') {
      const filePath = resolveStatic(pathname === '/' ? '/index.html' : pathname);
      if (filePath) {
        try { return sendFile(res, filePath); } catch { /* fall through to 404 */ }
      }
    }

    sendJson(res, 404, { error: 'not_found', message: `no route for ${req.method} ${pathname}` });
  });
}

const isMain = process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);

if (isMain) {
  const port = Number(process.env.PORT) || 8787;
  const dbPath = process.env.FOUNDEV_DB || DEFAULT_DB_PATH;
  const db = openDatabase(dbPath);
  const server = createServer({ db });

  server.listen(port, () => {
    console.log(`actual-budget listening on http://localhost:${port}`);
    console.log(`database: ${dbPath}`);
  });

  const shutdown = () => { try { db.close(); } catch { /* ignore */ } server.close(() => process.exit(0)); };
  process.on('SIGINT', shutdown);
  process.on('SIGTERM', shutdown);
}
