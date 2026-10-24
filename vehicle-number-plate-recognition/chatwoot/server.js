'use strict';
/**
 * Chatwoot - application server.
 *
 * Zero runtime dependencies. Uses Node's built-in HTTP server and SQLite
 * driver (node:sqlite). Domain configuration lives in config.json.
 */
const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { DatabaseSync } = require('node:sqlite');
const helpdesk = require('./helpdesk');

const ROOT = __dirname;
const CONFIG = JSON.parse(fs.readFileSync(path.join(ROOT, 'config.json'), 'utf8'));
const DATA_DIR = process.env.DATA_DIR || path.join(ROOT, 'data');
const PORT = Number(process.env.PORT || CONFIG.port || 3000);
fs.mkdirSync(DATA_DIR, { recursive: true });

const db = new DatabaseSync(path.join(DATA_DIR, 'app.db'));
db.exec('PRAGMA journal_mode = WAL');
db.exec('PRAGMA foreign_keys = ON');

const TYPES = { text: 'TEXT', int: 'INTEGER', real: 'REAL', bool: 'INTEGER' };

function initSchema() {
  db.exec(`CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'member',
    created_at TEXT NOT NULL
  )`);
  db.exec(`CREATE TABLE IF NOT EXISTS sessions (
    token TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires_at TEXT NOT NULL
  )`);
  for (const r of CONFIG.resources) {
    const cols = r.fields.map((f) => `"${f.name}" ${TYPES[f.type] || 'TEXT'}`).join(',\n    ');
    db.exec(`CREATE TABLE IF NOT EXISTS "${r.name}" (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ${cols}${cols ? ',' : ''}
    created_at TEXT NOT NULL
  )`);
    const count = db.prepare(`SELECT COUNT(*) AS n FROM "${r.name}"`).get().n;
    if (count === 0) {
      const rows = (CONFIG.seed && CONFIG.seed[r.name]) || [];
      for (const row of rows) {
        const now = new Date().toISOString();
        const keys = Object.keys(row);
        const sql = `INSERT INTO "${r.name}" (${keys.map((k) => `"${k}"`).join(',')}, created_at)
          VALUES (${keys.map(() => '?').join(',')}, ?)`;
        db.prepare(sql).run(...keys.map((k) => row[k]), now);
      }
    }
  }
  if (CONFIG.special === 'helpdesk') {
    db.exec(`CREATE TABLE IF NOT EXISTS conversation_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL,
    type TEXT NOT NULL,
    detail TEXT NOT NULL DEFAULT '',
    actor TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
  )`);
  }
  if (CONFIG.special === 'uptime') {
    db.exec(`CREATE TABLE IF NOT EXISTS checks (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      monitor_id INTEGER NOT NULL REFERENCES monitors(id) ON DELETE CASCADE,
      status TEXT NOT NULL, latency_ms INTEGER, error TEXT, checked_at TEXT NOT NULL
    )`);
  }
  if (CONFIG.special === 'wiki') {
    db.exec(`CREATE TABLE IF NOT EXISTS page_revisions (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      page_id INTEGER NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
      title TEXT NOT NULL, body TEXT NOT NULL, version INTEGER NOT NULL, created_at TEXT NOT NULL
    )`);
  }
  if (CONFIG.special === 'commerce') {
    db.exec(`CREATE TABLE IF NOT EXISTS order_items (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
      product_id INTEGER NOT NULL, name TEXT NOT NULL, quantity INTEGER NOT NULL,
      unit_cents INTEGER NOT NULL
    )`);
  }
}

function dbAll(sql, ...params) { return db.prepare(sql).all(...params); }
function dbGet(sql, ...params) { return db.prepare(sql).get(...params); }
function dbRun(sql, ...params) { return db.prepare(sql).run(...params); }

function hashPassword(password) {
  const salt = crypto.randomBytes(16).toString('hex');
  const hash = crypto.scryptSync(password, salt, 64).toString('hex');
  return `${salt}:${hash}`;
}
function verifyPassword(password, stored) {
  const [salt, hash] = String(stored).split(':');
  if (!salt || !hash) return false;
  const candidate = crypto.scryptSync(password, salt, 64);
  const expected = Buffer.from(hash, 'hex');
  return candidate.length === expected.length && crypto.timingSafeEqual(candidate, expected);
}

function parseCookies(req) {
  const out = {};
  for (const part of String(req.headers.cookie || '').split(';')) {
    const i = part.indexOf('=');
    if (i > -1) out[part.slice(0, i).trim()] = decodeURIComponent(part.slice(i + 1).trim());
  }
  return out;
}

function currentUser(req) {
  const token = parseCookies(req).sid;
  if (!token) return null;
  const row = dbGet(`SELECT u.id, u.email, u.name, u.role FROM sessions s
    JOIN users u ON u.id = s.user_id WHERE s.token = ? AND s.expires_at > ?`,
    token, new Date().toISOString());
  return row || null;
}

function json(res, status, body, headers = {}) {
  const data = JSON.stringify(body);
  res.writeHead(status, {
    'Content-Type': 'application/json; charset=utf-8',
    'Content-Length': Buffer.byteLength(data),
    'Cache-Control': 'no-store',
    ...headers,
  });
  res.end(data);
}

function readBody(req, limit = 1_000_000) {
  return new Promise((resolve, reject) => {
    let size = 0;
    const chunks = [];
    req.on('data', (chunk) => {
      size += chunk.length;
      if (size > limit) { reject(new Error('payload too large')); req.destroy(); return; }
      chunks.push(chunk);
    });
    req.on('end', () => {
      if (!chunks.length) return resolve({});
      try { resolve(JSON.parse(Buffer.concat(chunks).toString('utf8'))); }
      catch { reject(new Error('invalid JSON body')); }
    });
    req.on('error', reject);
  });
}

function pickFields(resource, body, partial = false) {
  const out = {};
  for (const f of resource.fields) {
    if (body[f.name] === undefined) {
      // A field that was not sent keeps the default from the configuration.
      // A partial update leaves the field alone.
      if (!partial && f.default !== undefined) out[f.name] = f.default;
      continue;
    }
    let value = body[f.name];
    if (f.type === 'int') value = value === '' || value === null ? null : parseInt(value, 10);
    if (f.type === 'real') value = value === '' || value === null ? null : parseFloat(value);
    if (f.type === 'bool') value = value === true || value === 'true' || value === 1 || value === '1' ? 1 : 0;
    if (f.type === 'text' && value !== null) value = String(value);
    out[f.name] = value;
  }
  return out;
}

function validate(resource, body, partial = false) {
  for (const f of resource.fields) {
    if (f.required && !partial && (body[f.name] === undefined || body[f.name] === '')) {
      return `${f.label || f.name} is required`;
    }
    if (body[f.name] !== undefined && body[f.name] !== null && f.type === 'int' && Number.isNaN(body[f.name])) {
      return `${f.label || f.name} must be a number`;
    }
  }
  return null;
}

function findResource(name) {
  return CONFIG.resources.find((r) => r.name === name);
}

/* ------------------------------------------------------------------ */
/* Domain helpers                                                      */
/* ------------------------------------------------------------------ */

async function checkMonitor(monitor) {
  const started = Date.now();
  let status = 'down';
  let error = null;
  try {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 8000);
    const response = await fetch(monitor.url, { signal: controller.signal, redirect: 'follow' });
    clearTimeout(timer);
    status = response.ok ? 'up' : 'degraded';
    if (!response.ok) error = `HTTP ${response.status}`;
  } catch (err) {
    error = err.name === 'AbortError' ? 'timeout' : String(err.message || err);
  }
  const latency = Date.now() - started;
  dbRun('INSERT INTO checks (monitor_id, status, latency_ms, error, checked_at) VALUES (?, ?, ?, ?, ?)',
    monitor.id, status, latency, error, new Date().toISOString());
  return { status, latency_ms: latency, error };
}

function availability(slug, date) {
  const event = dbGet('SELECT * FROM event_types WHERE slug = ?', slug);
  if (!event) return null;
  const duration = Number(event.duration_minutes) || 30;
  const slots = [];
  const dayStart = new Date(`${date}T09:00:00`);
  const dayEnd = new Date(`${date}T17:00:00`);
  if (Number.isNaN(dayStart.valueOf())) return null;
  const booked = dbAll('SELECT start_at FROM bookings WHERE event_type_id = ? AND status != ?', event.id, 'cancelled')
    .map((b) => new Date(b.start_at).valueOf());
  for (let t = dayStart.valueOf(); t + duration * 60000 <= dayEnd.valueOf(); t += duration * 60000) {
    if (!booked.includes(t)) slots.push(new Date(t).toISOString());
  }
  return { event, slots };
}

function icsEscape(value) {
  return String(value).replace(/\\/g, '\\\\').replace(/\n/g, '\\n').replace(/,/g, '\\,').replace(/;/g, '\\;');
}

const sseClients = new Set();
function broadcast(event, data) {
  const payload = `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`;
  for (const res of sseClients) { try { res.write(payload); } catch { sseClients.delete(res); } }
}

/* ------------------------------------------------------------------ */
/* Request handling                                                    */
/* ------------------------------------------------------------------ */

async function handleApi(req, res, url) {
  const user = currentUser(req);
  const method = req.method;
  const parts = url.pathname.split('/').filter(Boolean); // api, ...

  if (url.pathname === '/api/meta' && method === 'GET') {
    return json(res, 200, {
      name: CONFIG.name, tagline: CONFIG.tagline, description: CONFIG.description,
      special: CONFIG.special || 'generic', features: CONFIG.features,
      resources: CONFIG.resources.map((r) => ({
        name: r.name, label: r.label, icon: r.icon || '•',
        fields: r.fields.map((f) => ({ ...f, required: !!f.required })),
      })),
      publicRead: CONFIG.publicRead !== false,
      user,
    });
  }

  if (url.pathname === '/api/auth/register' && method === 'POST') {
    const body = await readBody(req);
    const email = String(body.email || '').trim().toLowerCase();
    const name = String(body.name || '').trim();
    const password = String(body.password || '');
    if (!email.includes('@') || !name || password.length < 8) {
      return json(res, 400, { error: 'A valid email, name and password of at least 8 characters are required.' });
    }
    if (dbGet('SELECT id FROM users WHERE email = ?', email)) {
      return json(res, 409, { error: 'That email is already registered.' });
    }
    const isFirst = dbGet('SELECT COUNT(*) AS n FROM users').n === 0;
    const info = dbRun('INSERT INTO users (email, name, password, role, created_at) VALUES (?, ?, ?, ?, ?)',
      email, name, hashPassword(password), isFirst ? 'owner' : 'member', new Date().toISOString());
    const token = crypto.randomBytes(32).toString('hex');
    const expires = new Date(Date.now() + 7 * 86400000).toISOString();
    dbRun('INSERT INTO sessions (token, user_id, expires_at) VALUES (?, ?, ?)', token, info.lastInsertRowid, expires);
    return json(res, 201, { user: { id: Number(info.lastInsertRowid), email, name, role: isFirst ? 'owner' : 'member' } },
      { 'Set-Cookie': `sid=${token}; HttpOnly; SameSite=Lax; Path=/; Max-Age=604800` });
  }

  if (url.pathname === '/api/auth/login' && method === 'POST') {
    const body = await readBody(req);
    const email = String(body.email || '').trim().toLowerCase();
    const row = dbGet('SELECT * FROM users WHERE email = ?', email);
    if (!row || !verifyPassword(String(body.password || ''), row.password)) {
      return json(res, 401, { error: 'Invalid email or password.' });
    }
    const token = crypto.randomBytes(32).toString('hex');
    const expires = new Date(Date.now() + 7 * 86400000).toISOString();
    dbRun('INSERT INTO sessions (token, user_id, expires_at) VALUES (?, ?, ?)', token, row.id, expires);
    return json(res, 200, { user: { id: row.id, email: row.email, name: row.name, role: row.role } },
      { 'Set-Cookie': `sid=${token}; HttpOnly; SameSite=Lax; Path=/; Max-Age=604800` });
  }

  if (url.pathname === '/api/auth/logout' && method === 'POST') {
    const token = parseCookies(req).sid;
    if (token) dbRun('DELETE FROM sessions WHERE token = ?', token);
    return json(res, 200, { ok: true }, { 'Set-Cookie': 'sid=; HttpOnly; SameSite=Lax; Path=/; Max-Age=0' });
  }

  /* ---------- special public endpoints ---------- */

  if (CONFIG.special === 'shortener' && parts[1] === 'r' && parts[2] && method === 'GET') {
    const link = dbGet('SELECT * FROM links WHERE slug = ?', parts[2]);
    if (!link) return json(res, 404, { error: 'Unknown short link' });
    dbRun('UPDATE links SET clicks = COALESCE(clicks, 0) + 1 WHERE id = ?', link.id);
    res.writeHead(302, { Location: link.target, 'Cache-Control': 'no-store' });
    return res.end();
  }

  if (CONFIG.special === 'uptime' && url.pathname === '/api/status' && method === 'GET') {
    const monitors = dbAll('SELECT * FROM monitors ORDER BY id');
    const now = new Date().toISOString();
    const items = monitors.map((m) => {
      const last = dbGet('SELECT * FROM checks WHERE monitor_id = ? ORDER BY id DESC LIMIT 1', m.id);
      const up = dbGet("SELECT COUNT(*) AS n FROM checks WHERE monitor_id = ? AND status = 'up'", m.id).n;
      const total = dbGet('SELECT COUNT(*) AS n FROM checks WHERE monitor_id = ?', m.id).n;
      return { ...m, last, uptime_percent: total ? Math.round((up / total) * 1000) / 10 : null };
    });
    return json(res, 200, { generated_at: now, monitors: items });
  }

  if (CONFIG.special === 'booking' && url.pathname === '/api/availability' && method === 'GET') {
    const result = availability(url.searchParams.get('slug'), url.searchParams.get('date'));
    if (!result) return json(res, 404, { error: 'Unknown event type or invalid date' });
    return json(res, 200, { event: result.event, slots: result.slots });
  }

  if (CONFIG.special === 'booking' && url.pathname === '/api/bookings.ics' && method === 'GET') {
    const eventSlug = url.searchParams.get('slug');
    const event = eventSlug ? dbGet('SELECT * FROM event_types WHERE slug = ?', eventSlug) : null;
    const bookings = event
      ? dbAll('SELECT * FROM bookings WHERE event_type_id = ? ORDER BY start_at', event.id)
      : dbAll('SELECT * FROM bookings ORDER BY start_at');
    const lines = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//Foundev//Booking//EN', 'CALSCALE:GREGORIAN'];
    for (const b of bookings) {
      const start = new Date(b.start_at);
      const duration = (event && event.duration_minutes) || 30;
      const end = new Date(start.valueOf() + duration * 60000);
      const fmt = (d) => d.toISOString().replace(/[-:]/g, '').replace(/\.\d{3}/, '');
      lines.push('BEGIN:VEVENT', `UID:booking-${b.id}@foundev.local`, `DTSTAMP:${fmt(new Date())}`,
        `DTSTART:${fmt(start)}`, `DTEND:${fmt(end)}`, `SUMMARY:${icsEscape(b.booker_name)}`,
        `DESCRIPTION:${icsEscape(b.notes || '')}`, 'END:VEVENT');
    }
    lines.push('END:VCALENDAR');
    res.writeHead(200, { 'Content-Type': 'text/calendar; charset=utf-8', 'Content-Disposition': 'attachment; filename="bookings.ics"' });
    return res.end(lines.join('\r\n'));
  }

  if (CONFIG.special === 'chat' && url.pathname === '/api/stream' && method === 'GET') {
    res.writeHead(200, { 'Content-Type': 'text/event-stream', 'Cache-Control': 'no-cache', Connection: 'keep-alive' });
    res.write('event: ready\ndata: {}\n\n');
    sseClients.add(res);
    const timer = setInterval(() => res.write(': ping\n\n'), 20000);
    req.on('close', () => { clearInterval(timer); sseClients.delete(res); });
    return;
  }

  if (CONFIG.special === 'readlater' && url.pathname === '/api/extract' && method === 'POST') {
    const body = await readBody(req);
    const target = String(body.url || '');
    if (!/^https?:\/\//i.test(target)) return json(res, 400, { error: 'Enter an http(s) URL' });
    let title = target;
    let excerpt = '';
    try {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), 8000);
      const response = await fetch(target, { signal: controller.signal });
      clearTimeout(timer);
      const html = (await response.text()).slice(0, 400000);
      const titleMatch = html.match(/<title[^>]*>([^<]+)<\/title>/i);
      if (titleMatch) title = titleMatch[1].trim().slice(0, 240);
      const bodyMatch = html.match(/<meta[^>]+name=["']description["'][^>]+content=["']([^"']+)/i)
        || html.match(/<p[^>]*>([^<]{80,400})<\/p>/i);
      if (bodyMatch) excerpt = bodyMatch[1].replace(/\s+/g, ' ').trim().slice(0, 400);
    } catch (err) {
      excerpt = `Could not extract automatically: ${err.message}`;
    }
    return json(res, 200, { url: target, title, excerpt });
  }

  /* ---------- authenticated endpoints ---------- */

  if (url.pathname === '/api/dashboard' && method === 'GET') {
    const counts = {};
    for (const r of CONFIG.resources) counts[r.name] = dbGet(`SELECT COUNT(*) AS n FROM "${r.name}"`).n;
    let extra = {};
    if (CONFIG.special === 'uptime') {
      extra = {
        monitors: dbGet('SELECT COUNT(*) AS n FROM monitors').n,
        down: dbGet("SELECT COUNT(DISTINCT monitor_id) AS n FROM checks c1 WHERE status != 'up' AND id = (SELECT MAX(id) FROM checks c2 WHERE c2.monitor_id = c1.monitor_id)").n,
      };
    }
    if (CONFIG.special === 'commerce') {
      extra.revenue_cents = dbGet("SELECT COALESCE(SUM(total_cents), 0) AS n FROM orders WHERE status != 'cancelled'").n;
    }
    if (CONFIG.special === 'booking') {
      extra.upcoming = dbGet('SELECT COUNT(*) AS n FROM bookings WHERE start_at > ?', new Date().toISOString()).n;
    }
    if (CONFIG.special === 'helpdesk') {
      const inbox = helpdesk.summariseInbox(dbAll('SELECT * FROM conversations'));
      extra.open = inbox.counts.open;
      extra.pending = inbox.counts.pending;
      extra.unassigned = inbox.unassigned;
      extra.waiting = dbGet("SELECT COUNT(*) AS n FROM conversations WHERE status = 'pending'").n;
    }
    return json(res, 200, { counts, extra });
  }

  if (CONFIG.special === 'uptime' && parts[1] === 'monitors' && parts[2] && parts[3] === 'check' && method === 'POST') {
    if (!user) return json(res, 401, { error: 'Sign in to run a check.' });
    const monitor = dbGet('SELECT * FROM monitors WHERE id = ?', Number(parts[2]));
    if (!monitor) return json(res, 404, { error: 'Monitor not found' });
    return json(res, 200, await checkMonitor(monitor));
  }

  if (CONFIG.special === 'uptime' && parts[1] === 'monitors' && parts[2] && parts[3] === 'checks' && method === 'GET') {
    return json(res, 200, { checks: dbAll('SELECT * FROM checks WHERE monitor_id = ? ORDER BY id DESC LIMIT 100', Number(parts[2])).reverse() });
  }

  if (CONFIG.special === 'booking' && url.pathname === '/api/book' && method === 'POST') {
    const body = await readBody(req);
    const event = dbGet('SELECT * FROM event_types WHERE id = ?', Number(body.event_type_id));
    if (!event) return json(res, 404, { error: 'Event type not found' });
    const start = new Date(body.start_at);
    if (Number.isNaN(start.valueOf()) || start < new Date()) return json(res, 400, { error: 'Choose a future start time.' });
    if (!body.booker_name || !String(body.booker_email || '').includes('@')) {
      return json(res, 400, { error: 'Name and a valid email are required.' });
    }
    const clash = dbGet('SELECT id FROM bookings WHERE event_type_id = ? AND start_at = ? AND status != ?',
      event.id, start.toISOString(), 'cancelled');
    if (clash) return json(res, 409, { error: 'That slot has just been booked.' });
    const info = dbRun('INSERT INTO bookings (event_type_id, start_at, booker_name, booker_email, notes, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
      event.id, start.toISOString(), String(body.booker_name), String(body.booker_email), String(body.notes || ''), 'confirmed', new Date().toISOString());
    return json(res, 201, { id: Number(info.lastInsertRowid) });
  }

  if (CONFIG.special === 'commerce' && url.pathname === '/api/checkout' && method === 'POST') {
    const body = await readBody(req);
    const items = Array.isArray(body.items) ? body.items : [];
    if (!items.length) return json(res, 400, { error: 'Cart is empty.' });
    const email = String(body.email || '');
    if (!email.includes('@')) return json(res, 400, { error: 'A valid email is required.' });
    const priced = [];
    let total = 0;
    for (const item of items) {
      const product = dbGet('SELECT * FROM products WHERE id = ?', Number(item.product_id));
      const qty = Math.max(1, parseInt(item.quantity, 10) || 1);
      if (!product) return json(res, 404, { error: 'A product in the cart no longer exists.' });
      if (product.stock < qty) return json(res, 409, { error: `${product.name} only has ${product.stock} left.` });
      priced.push({ product, qty });
      total += product.price_cents * qty;
    }
    db.exec('BEGIN');
    try {
      const info = dbRun('INSERT INTO orders (customer_email, total_cents, status, created_at) VALUES (?, ?, ?, ?)',
        email, total, 'paid', new Date().toISOString());
      for (const { product, qty } of priced) {
        dbRun('INSERT INTO order_items (order_id, product_id, name, quantity, unit_cents) VALUES (?, ?, ?, ?, ?)',
          info.lastInsertRowid, product.id, product.name, qty, product.price_cents);
        dbRun('UPDATE products SET stock = stock - ? WHERE id = ?', qty, product.id);
      }
      db.exec('COMMIT');
      return json(res, 201, { order_id: Number(info.lastInsertRowid), total_cents: total, email });
    } catch (err) {
      db.exec('ROLLBACK');
      return json(res, 500, { error: 'Checkout failed: ' + err.message });
    }
  }

  if (CONFIG.special === 'kanban' && parts[1] === 'cards' && parts[2] && parts[3] === 'move' && method === 'PATCH') {
    if (!user) return json(res, 401, { error: 'Sign in to move cards.' });
    const body = await readBody(req);
    dbRun('UPDATE cards SET list_id = ?, position = ? WHERE id = ?',
      Number(body.list_id), Number(body.position) || 0, Number(parts[2]));
    return json(res, 200, { ok: true });
  }

  if (CONFIG.special === 'wiki' && parts[1] === 'pages' && parts[2] && parts[3] === 'revisions' && method === 'GET') {
    return json(res, 200, { revisions: dbAll('SELECT * FROM page_revisions WHERE page_id = ? ORDER BY id DESC', Number(parts[2])) });
  }

  if (CONFIG.special === 'social' && parts[1] === 'posts' && parts[2] && parts[3] === 'like' && method === 'POST') {
    if (!user) return json(res, 401, { error: 'Sign in to like posts.' });
    dbRun('UPDATE posts SET likes = COALESCE(likes, 0) + 1 WHERE id = ?', Number(parts[2]));
    return json(res, 200, dbGet('SELECT * FROM posts WHERE id = ?', Number(parts[2])));
  }


  /* ---------- helpdesk endpoints ---------- */

  if (CONFIG.special === 'helpdesk' && url.pathname === '/api/inbox' && method === 'GET') {
    const conversations = dbAll('SELECT * FROM conversations');
    const filters = {
      status: url.searchParams.get('status'),
      priority: url.searchParams.get('priority'),
      assignee: url.searchParams.get('assignee'),
      q: url.searchParams.get('q'),
    };
    if (filters.assignee === null) filters.assignee = undefined;
    return json(res, 200, helpdesk.summariseInbox(conversations, filters));
  }

  if (CONFIG.special === 'helpdesk' && parts[1] === 'canned_responses' && parts[2] === 'search' && method === 'GET') {
    const responses = dbAll('SELECT * FROM canned_responses');
    return json(res, 200, { items: helpdesk.searchCannedResponses(responses, url.searchParams.get('q')) });
  }

  if (CONFIG.special === 'helpdesk' && parts[1] === 'conversations' && parts[2] && parts[3] === 'thread' && method === 'GET') {
    const conversation = dbGet('SELECT * FROM conversations WHERE id = ?', Number(parts[2]));
    if (!conversation) return json(res, 404, { error: 'Conversation not found' });
    const messages = dbAll('SELECT * FROM messages WHERE conversation_id = ? ORDER BY id ASC', conversation.id);
    return json(res, 200, helpdesk.buildThread(conversation, messages));
  }

  if (CONFIG.special === 'helpdesk' && parts[1] === 'conversations' && parts[2] && parts[3] === 'messages' && method === 'POST') {
    if (!user) return json(res, 401, { error: 'Sign in to reply.' });
    const conversation = dbGet('SELECT * FROM conversations WHERE id = ?', Number(parts[2]));
    if (!conversation) return json(res, 404, { error: 'Conversation not found' });
    const body = await readBody(req);
    const direction = String(body.direction || 'outbound');
    if (!helpdesk.isValidDirection(direction)) {
      return json(res, 400, { error: `"${direction}" is not a reply type.` });
    }
    const text = String(body.body || '').trim();
    if (!text) return json(res, 400, { error: 'A reply needs a body.' });
    const sender = String(body.sender || user.name || user.email);
    const info = dbRun('INSERT INTO messages (conversation_id, sender, body, direction, created_at) VALUES (?, ?, ?, ?, ?)',
      conversation.id, sender, text, direction, new Date().toISOString());
    dbRun('INSERT INTO conversation_events (conversation_id, type, detail, actor, created_at) VALUES (?, ?, ?, ?, ?)',
      conversation.id, 'reply', text.slice(0, 200), sender, new Date().toISOString());
    if (direction === 'outbound' && conversation.status === 'pending') {
      dbRun('UPDATE conversations SET status = ? WHERE id = ?', 'open', conversation.id);
    }
    return json(res, 201, dbGet('SELECT * FROM messages WHERE id = ?', info.lastInsertRowid));
  }

  if (CONFIG.special === 'helpdesk' && parts[1] === 'conversations' && parts[2] && parts[3] === 'status' && method === 'POST') {
    if (!user) return json(res, 401, { error: 'Sign in to change the status.' });
    const conversation = dbGet('SELECT * FROM conversations WHERE id = ?', Number(parts[2]));
    if (!conversation) return json(res, 404, { error: 'Conversation not found' });
    const body = await readBody(req);
    const next = String(body.status || '');
    const problem = helpdesk.transitionError(conversation.status, next);
    if (problem) return json(res, 400, { error: problem });
    dbRun('UPDATE conversations SET status = ? WHERE id = ?', next, conversation.id);
    dbRun('INSERT INTO conversation_events (conversation_id, type, detail, actor, created_at) VALUES (?, ?, ?, ?, ?)',
      conversation.id, 'status', `${conversation.status} -> ${next}`, user.name || user.email, new Date().toISOString());
    return json(res, 200, dbGet('SELECT * FROM conversations WHERE id = ?', conversation.id));
  }

  if (CONFIG.special === 'helpdesk' && parts[1] === 'conversations' && parts[2] && parts[3] === 'assign' && method === 'POST') {
    if (!user) return json(res, 401, { error: 'Sign in to assign a conversation.' });
    const conversation = dbGet('SELECT * FROM conversations WHERE id = ?', Number(parts[2]));
    if (!conversation) return json(res, 404, { error: 'Conversation not found' });
    const body = await readBody(req);
    let assignee = String(body.assignee || '').trim();
    if (!assignee && body.auto) {
      const agents = dbAll("SELECT name FROM users WHERE role IN ('owner', 'member')").map((row) => row.name);
      assignee = helpdesk.chooseAssignee(dbAll('SELECT * FROM conversations'), agents);
    }
    if (assignee) {
      const known = dbGet('SELECT id FROM users WHERE name = ?', assignee);
      if (!known) return json(res, 400, { error: `"${assignee}" is not an agent.` });
    }
    dbRun('UPDATE conversations SET assignee = ? WHERE id = ?', assignee, conversation.id);
    dbRun('INSERT INTO conversation_events (conversation_id, type, detail, actor, created_at) VALUES (?, ?, ?, ?, ?)',
      conversation.id, 'assigned', assignee, user.name || user.email, new Date().toISOString());
    return json(res, 200, dbGet('SELECT * FROM conversations WHERE id = ?', conversation.id));
  }

  if (CONFIG.special === 'helpdesk' && parts[1] === 'conversations' && parts[2] && parts[3] === 'canned' && parts[4] && method === 'POST') {
    if (!user) return json(res, 401, { error: 'Sign in to use a canned response.' });
    const conversation = dbGet('SELECT * FROM conversations WHERE id = ?', Number(parts[2]));
    if (!conversation) return json(res, 404, { error: 'Conversation not found' });
    const canned = dbGet('SELECT * FROM canned_responses WHERE id = ?', Number(parts[4]));
    if (!canned) return json(res, 404, { error: 'Canned response not found' });
    const sender = String((await readBody(req)).sender || user.name || user.email);
    const info = dbRun('INSERT INTO messages (conversation_id, sender, body, direction, created_at) VALUES (?, ?, ?, ?, ?)',
      conversation.id, sender, canned.body, 'outbound', new Date().toISOString());
    dbRun('INSERT INTO conversation_events (conversation_id, type, detail, actor, created_at) VALUES (?, ?, ?, ?, ?)',
      conversation.id, 'canned', canned.title, sender, new Date().toISOString());
    return json(res, 201, dbGet('SELECT * FROM messages WHERE id = ?', info.lastInsertRowid));
  }

  if (CONFIG.special === 'helpdesk' && parts[1] === 'conversations' && parts[2] && parts[3] === 'events' && method === 'GET') {
    return json(res, 200, { items: dbAll('SELECT * FROM conversation_events WHERE conversation_id = ? ORDER BY id ASC', Number(parts[2])) });
  }

  /* ---------- generic resource CRUD ---------- */

  if (parts[1] && parts[1] !== 'auth' && parts[1] !== 'meta') {
    const resource = findResource(parts[1]);
    if (!resource) return json(res, 404, { error: 'Unknown resource' });
    const table = `"${resource.name}"`;
    const id = parts[2] ? Number(parts[2]) : null;

    if (method === 'GET' && !id) {
      const q = String(url.searchParams.get('q') || '').trim();
      const limit = Math.min(200, Math.max(1, Number(url.searchParams.get('limit')) || 100));
      const offset = Math.max(0, Number(url.searchParams.get('offset')) || 0);
      let sql = `SELECT * FROM ${table}`;
      const params = [];
      if (q) {
        const textFields = resource.fields.filter((f) => f.type === 'text' || !f.type);
        if (textFields.length) {
          sql += ' WHERE ' + textFields.map((f) => `"${f.name}" LIKE ?`).join(' OR ');
          params.push(...textFields.map(() => `%${q}%`));
        }
      }
      sql += ` ORDER BY id DESC LIMIT ? OFFSET ?`;
      params.push(limit, offset);
      return json(res, 200, { items: dbAll(sql, ...params) });
    }

    if (method === 'GET' && id) {
      const row = dbGet(`SELECT * FROM ${table} WHERE id = ?`, id);
      return row ? json(res, 200, row) : json(res, 404, { error: 'Not found' });
    }

    if (method === 'POST' && !id) {
      if (!user) return json(res, 401, { error: 'Sign in to create records.' });
      const body = await readBody(req);
      const values = pickFields(resource, body);
      const error = validate(resource, values);
      if (error) return json(res, 400, { error });
      const keys = Object.keys(values);
      if (!keys.length) return json(res, 400, { error: 'No fields supplied.' });
      const info = dbRun(`INSERT INTO ${table} (${keys.map((k) => `"${k}"`).join(',')}, created_at) VALUES (${keys.map(() => '?').join(',')}, ?)`,
        ...keys.map((k) => values[k]), new Date().toISOString());
      return json(res, 201, dbGet(`SELECT * FROM ${table} WHERE id = ?`, info.lastInsertRowid));
    }

    if (method === 'PATCH' && id) {
      if (!user) return json(res, 401, { error: 'Sign in to edit records.' });
      const body = await readBody(req);
      const values = pickFields(resource, body, true);
      const error = validate(resource, values, true);
      if (error) return json(res, 400, { error });
      if (CONFIG.special === 'wiki' && resource.name === 'pages') {
        const previous = dbGet('SELECT * FROM pages WHERE id = ?', id);
        if (previous) {
          const version = (previous.version || 1);
          dbRun('INSERT INTO page_revisions (page_id, title, body, version, created_at) VALUES (?, ?, ?, ?, ?)',
            id, previous.title, previous.body, version, new Date().toISOString());
          values.version = version + 1;
        }
      }
      const keys = Object.keys(values);
      if (!keys.length) return json(res, 400, { error: 'No fields supplied.' });
      dbRun(`UPDATE ${table} SET ${keys.map((k) => `"${k}" = ?`).join(', ')} WHERE id = ?`,
        ...keys.map((k) => values[k]), id);
      return json(res, 200, dbGet(`SELECT * FROM ${table} WHERE id = ?`, id));
    }

    if (method === 'DELETE' && id) {
      if (!user) return json(res, 401, { error: 'Sign in to delete records.' });
      dbRun(`DELETE FROM ${table} WHERE id = ?`, id);
      return json(res, 200, { ok: true });
    }
  }

  return json(res, 404, { error: 'Not found' });
}

const MIME = {
  '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8', '.svg': 'image/svg+xml', '.png': 'image/png',
  '.ico': 'image/x-icon', '.json': 'application/json; charset=utf-8', '.webmanifest': 'application/manifest+json',
};

function serveStatic(req, res, url) {
  let rel = decodeURIComponent(url.pathname);
  if (rel === '/') rel = '/index.html';
  const file = path.join(ROOT, 'public', rel);
  const publicDir = path.join(ROOT, 'public');
  if (!file.startsWith(publicDir + path.sep) && file !== path.join(publicDir, 'index.html')) {
    res.writeHead(403); return res.end('Forbidden');
  }
  fs.readFile(file, (err, data) => {
    if (err) {
      if (rel !== '/index.html' && !path.extname(rel)) return serveStatic(req, res, new URL('/index.html', 'http://x'));
      res.writeHead(404, { 'Content-Type': 'text/plain' }); return res.end('Not found');
    }
    res.writeHead(200, { 'Content-Type': MIME[path.extname(file)] || 'application/octet-stream' });
    res.end(data);
  });
}

initSchema();

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://${req.headers.host || 'localhost'}`);
  try {
    if (url.pathname.startsWith('/api/')) return await handleApi(req, res, url);
    if (req.method !== 'GET' && req.method !== 'HEAD') { res.writeHead(405); return res.end(); }
    return serveStatic(req, res, url);
  } catch (err) {
    console.error(err);
    if (!res.headersSent) json(res, 500, { error: 'Internal server error' });
    else res.end();
  }
});

if (require.main === module) {
  server.listen(PORT, () => {
    console.log(`${CONFIG.name} listening on http://localhost:${PORT}`);
  });
}

module.exports = { server, db, CONFIG };
