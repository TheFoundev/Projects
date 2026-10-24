'use strict';
/* HospitalRun single-page client. Dependency-free. */

const $ = (sel, root = document) => root.querySelector(sel);
const el = (tag, attrs = {}, ...children) => {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === 'class') node.className = v;
    else if (k === 'html') node.innerHTML = v;
    else if (k.startsWith('on')) node.addEventListener(k.slice(2).toLowerCase(), v);
    else if (v !== false && v !== null && v !== undefined) node.setAttribute(k, v === true ? '' : v);
  }
  for (const child of children.flat()) {
    if (child === null || child === undefined || child === false) continue;
    node.append(child.nodeType ? child : document.createTextNode(String(child)));
  }
  return node;
};
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmtMoney = (cents) => (Number(cents || 0) / 100).toLocaleString(undefined, { style: 'currency', currency: 'USD' });
const fmtDate = (s) => s ? new Date(s).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' }) : '—';
const relTime = (s) => {
  if (!s) return '—';
  const diff = (Date.now() - new Date(s).valueOf()) / 1000;
  if (diff < 60) return 'just now';
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return new Date(s).toLocaleDateString();
};

const state = { meta: null, user: null, route: '', data: {}, cart: [] };

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    credentials: 'same-origin',
    ...options,
    body: options.body ? JSON.stringify(options.body) : undefined,
  });
  const type = response.headers.get('content-type') || '';
  const data = type.includes('json') ? await response.json() : await response.text();
  if (!response.ok) throw new Error((data && data.error) || `Request failed (${response.status})`);
  return data;
}

let toastTimer;
function toast(message) {
  const node = $('#toast');
  node.textContent = message;
  node.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => node.classList.remove('show'), 3200);
}

function modal(title, content, onClose) {
  const root = $('#modal-root');
  const close = () => { root.innerHTML = ''; if (onClose) onClose(); };
  const backdrop = el('div', { class: 'modal-backdrop', onclick: (e) => { if (e.target === backdrop) close(); } },
    el('div', { class: 'modal', role: 'dialog', 'aria-modal': 'true' },
      el('header', {}, el('h2', {}, title), el('button', { class: 'icon-btn', onclick: close, 'aria-label': 'Close' }, '×')),
      content));
  root.innerHTML = '';
  root.append(backdrop);
  const first = backdrop.querySelector('input, select, textarea, button');
  if (first) setTimeout(() => first.focus(), 30);
  return close;
}

function fieldInput(field, value) {
  const common = { name: field.name, id: `f-${field.name}`, required: field.required };
  if (field.type === 'text' && field.multiline) {
    return el('textarea', { ...common, rows: 5 }, value || '');
  }
  if (field.options) {
    const select = el('select', common);
    for (const option of field.options) {
      const opt = el('option', { value: option }, option);
      if (String(value) === String(option)) opt.selected = true;
      select.append(opt);
    }
    return select;
  }
  if (field.type === 'bool') {
    const input = el('input', { ...common, type: 'checkbox' });
    input.checked = !!value;
    return input;
  }
  const type = field.type === 'int' || field.type === 'real' ? 'number' : field.type === 'date' ? 'date' : 'text';
  return el('input', { ...common, type, value: value ?? '', step: field.type === 'real' ? 'any' : undefined,
    placeholder: field.placeholder || '' });
}

function resourceForm(resource, record, onSubmit) {
  const form = el('form', {});
  const fields = el('div', {});
  for (const field of resource.fields) {
    const input = fieldInput(field, record ? record[field.name] : field.default ?? '');
    fields.append(el('div', { class: 'field' },
      el('label', { for: `f-${field.name}` }, field.label || field.name, field.required ? ' *' : ''),
      input));
  }
  form.append(fields);
  form.append(el('div', { class: 'row gap', style: 'justify-content:flex-end;margin-top:8px' },
    el('button', { type: 'submit', class: 'btn primary' }, record ? 'Save changes' : 'Create')));
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const body = {};
    for (const field of resource.fields) {
      const node = form.querySelector(`[name="${field.name}"]`);
      if (!node) continue;
      body[field.name] = field.type === 'bool' ? node.checked : node.value;
    }
    try { await onSubmit(body); } catch (err) { toast(err.message); }
  });
  return form;
}

function emptyState(title, text, action) {
  return el('div', { class: 'empty' }, el('h3', {}, title), el('p', {}, text), action || '');
}

/* ---------------------------------------------------------------- */
/* Navigation                                                        */
/* ---------------------------------------------------------------- */

function navItems() {
  const items = [{ href: '#/', label: 'Dashboard', icon: '◫' }];
  for (const r of state.meta.resources) items.push({ href: `#/${r.name}`, label: r.label, icon: r.icon });
  if (state.meta.special === 'uptime') items.push({ href: '#/status', label: 'Public status', icon: '◉' });
  if (state.meta.special === 'booking') items.push({ href: '#/schedule', label: 'Public booking', icon: '◷' });
  if (state.meta.special === 'blog') items.push({ href: '#/blog', label: 'Public blog', icon: '✎' });
  if (state.meta.special === 'wiki') items.push({ href: '#/wiki', label: 'Knowledge base', icon: '▤' });
  if (state.meta.special === 'kanban') items.push({ href: '#/board', label: 'Board', icon: '▥' });
  if (state.meta.special === 'commerce') items.push({ href: '#/store', label: 'Store', icon: '◫' });
  if (state.meta.special === 'chat') items.push({ href: '#/channels', label: 'Channels', icon: '#' });
  if (state.meta.special === 'shortener') items.push({ href: '#/links', label: 'Short links', icon: '↗' });
  if (state.meta.special === 'readlater') items.push({ href: '#/reading', label: 'Reading list', icon: '▤' });
  return items;
}

function renderNav() {
  const nav = $('#nav');
  nav.innerHTML = '';
  nav.append(el('span', { class: 'nav-label' }, 'Workspace'));
  for (const item of navItems()) {
    const active = state.route === item.href.slice(1);
    nav.append(el('a', { href: item.href, class: active ? 'active' : '' },
      el('span', { 'aria-hidden': 'true' }, item.icon), item.label));
  }
  const box = $('#user-box');
  box.innerHTML = '';
  if (state.user) {
    box.append(el('div', { class: 'row between gap' },
      el('div', {}, el('strong', { class: 'small' }, state.user.name),
        el('div', { class: 'muted small' }, state.user.email)),
      el('button', { class: 'btn small', onclick: logout }, 'Sign out')));
  } else {
    box.append(el('button', { class: 'btn primary', style: 'width:100%', onclick: () => authModal('login') }, 'Sign in'));
  }
}

async function logout() {
  await api('/api/auth/logout', { method: 'POST' });
  state.user = null;
  renderNav();
  render();
}

function authModal(mode = 'login') {
  const isRegister = mode === 'register';
  const form = el('form', {});
  if (isRegister) form.append(el('div', { class: 'field' }, el('label', {}, 'Name'), el('input', { name: 'name', required: true, autocomplete: 'name' })));
  form.append(
    el('div', { class: 'field' }, el('label', {}, 'Email'), el('input', { name: 'email', type: 'email', required: true, autocomplete: 'email' })),
    el('div', { class: 'field' }, el('label', {}, 'Password'), el('input', { name: 'password', type: 'password', required: true, minlength: 8, autocomplete: isRegister ? 'new-password' : 'current-password' })),
    el('p', { class: 'muted small', style: 'margin-bottom:12px' }, isRegister ? 'The first account becomes the workspace owner. Passwords are hashed with scrypt.' : 'Use the account you registered on this instance.'),
    el('button', { class: 'btn primary', style: 'width:100%', type: 'submit' }, isRegister ? 'Create account' : 'Sign in'),
    el('p', { class: 'small', style: 'margin-top:12px;text-align:center' },
      isRegister ? 'Already registered? ' : 'New here? ',
      el('a', { href: '#', onclick: (e) => { e.preventDefault(); close(); authModal(isRegister ? 'login' : 'register'); } }, isRegister ? 'Sign in' : 'Create an account'))
  );
  const close = modal(isRegister ? 'Create your account' : 'Sign in', form);
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const body = Object.fromEntries(new FormData(form));
    try {
      const data = await api(`/api/auth/${isRegister ? 'register' : 'login'}`, { method: 'POST', body });
      state.user = data.user;
      close();
      renderNav();
      toast(`Welcome, ${data.user.name}`);
      render();
    } catch (err) { toast(err.message); }
  });
}

/* ---------------------------------------------------------------- */
/* Views                                                             */
/* ---------------------------------------------------------------- */

function setHeader(title, subtitle, actions = []) {
  $('#page-title').textContent = title;
  $('#page-subtitle').textContent = subtitle || '';
  const box = $('#top-actions');
  box.innerHTML = '';
  for (const action of actions) box.append(action);
}

async function renderDashboard() {
  setHeader('Dashboard', state.meta.tagline);
  const summary = await api('/api/dashboard');
  const view = $('#view');
  view.innerHTML = '';
  const cards = el('div', { class: 'grid cols-3' });
  for (const resource of state.meta.resources) {
    cards.append(el('a', { class: 'card stat', href: `#/${resource.name}`, style: 'color:inherit;text-decoration:none' },
      el('span', {}, resource.label), el('b', {}, summary.counts[resource.name] ?? 0), el('span', { class: 'muted small' }, 'records')));
  }
  if (state.meta.special === 'commerce') {
    cards.append(el('div', { class: 'card stat' }, el('span', {}, 'Revenue'), el('b', {}, fmtMoney(summary.extra.revenue_cents)), el('span', { class: 'muted small' }, 'paid orders')));
  }
  if (state.meta.special === 'booking') {
    cards.append(el('div', { class: 'card stat' }, el('span', {}, 'Upcoming'), el('b', {}, summary.extra.upcoming), el('span', { class: 'muted small' }, 'confirmed bookings')));
  }
  view.append(cards);
  view.append(el('div', { class: 'grid cols-2', style: 'margin-top:16px' },
    el('div', { class: 'card' },
      el('h2', {}, 'What this does'),
      el('p', { class: 'muted', style: 'margin:8px 0 14px' }, state.meta.description),
      el('div', { class: 'pill-list' }, state.meta.features.map((f) => el('span', { class: 'badge' }, f)))),
    el('div', { class: 'card' },
      el('h2', {}, 'Quick start'),
      el('ol', { class: 'muted', style: 'margin:10px 0 0;padding-left:18px;line-height:1.9' },
        el('li', {}, 'Create an account (first user becomes owner).'),
        el('li', {}, `Add ${state.meta.resources[0] ? state.meta.resources[0].label.toLowerCase() : 'records'} from the sidebar.`),
        el('li', {}, state.meta.special === 'uptime' ? 'Run a check and watch the public status page.' : 'Use the UI or the JSON API under /api.')))));
  if (!state.user) {
    view.append(el('div', { class: 'card', style: 'margin-top:16px' },
      el('div', { class: 'row between wrap gap' },
        el('div', {}, el('h2', {}, 'Sign in to edit'), el('p', { class: 'muted' }, 'Read-only browsing is available. Create an account to add and change records.')),
        el('button', { class: 'btn primary', onclick: () => authModal('register') }, 'Create account'))));
  }
}

async function renderResource(resourceName) {
  const resource = state.meta.resources.find((r) => r.name === resourceName);
  if (!resource) return renderNotFound();
  setHeader(resource.label, `Browse and manage ${resource.label.toLowerCase()}.`, []);
  if (state.user) {
    $('#top-actions').append(el('button', { class: 'btn primary', onclick: () => openCreate(resource) }, '+ New'));
  }
  const view = $('#view');
  view.innerHTML = '';
  const search = el('input', { type: 'search', placeholder: `Search ${resource.label.toLowerCase()}…`, 'aria-label': 'Search' });
  const toolbar = el('div', { class: 'toolbar' }, search, el('span', { class: 'grow' }));
  const results = el('div', { class: 'card table-wrap' });
  view.append(toolbar, results);

  const load = async () => {
    results.innerHTML = '<p class="muted" style="padding:16px">Loading…</p>';
    try {
      const data = await api(`/api/${resource.name}?q=${encodeURIComponent(search.value)}`);
      results.innerHTML = '';
      if (!data.items.length) {
        results.append(emptyState('Nothing here yet', `Create the first ${resource.label.toLowerCase().replace(/s$/, '')} to get started.`,
          state.user ? el('button', { class: 'btn primary', style: 'margin-top:12px', onclick: () => openCreate(resource) }, 'Create') : ''));
        return;
      }
      const table = el('table');
      const head = el('tr', {}, el('th', {}, '#'));
      for (const f of resource.fields) head.append(el('th', {}, f.label || f.name));
      head.append(el('th', {}, 'Created'), el('th', {}, ''));
      table.append(el('thead', {}, head));
      const body = el('tbody');
      for (const row of data.items) {
        const tr = el('tr', {}, el('td', { class: 'muted' }, row.id));
        for (const f of resource.fields) {
          let value = row[f.name];
          if (f.type === 'bool') value = value ? 'Yes' : 'No';
          if (f.type === 'date' && value) value = new Date(value).toLocaleDateString();
          const text = String(value ?? '—');
          tr.append(el('td', {}, text.length > 90 ? text.slice(0, 90) + '…' : text));
        }
        tr.append(el('td', { class: 'muted small' }, relTime(row.created_at)));
        const actions = el('td', {});
        if (state.user && state.meta.special === 'automation' && resource.name === 'agents') {
          actions.append(el('button', { class: 'btn small', style: 'margin-right:6px', onclick: async (e) => {
            e.target.disabled = true;
            try { const r = await api(`/api/agents/${row.id}/run`, { method: 'POST' }); toast(`${r.status}: ${r.message}`); load(); }
            catch (err) { toast(err.message); e.target.disabled = false; }
          } }, 'Run'));
        }
        if (state.user) {
          actions.append(el('button', { class: 'btn small', onclick: () => openEdit(resource, row, load) }, 'Edit'));
          actions.append(el('button', { class: 'btn small danger', style: 'margin-left:6px', onclick: async () => {
            if (!confirm(`Delete this ${resource.label.replace(/s$/, '').toLowerCase()}?`)) return;
            try { await api(`/api/${resource.name}/${row.id}`, { method: 'DELETE' }); toast('Deleted'); load(); }
            catch (err) { toast(err.message); }
          } }, 'Delete'));
        }
        tr.append(actions);
        body.append(tr);
      }
      table.append(body);
      results.append(table);
    } catch (err) {
      results.innerHTML = '';
      results.append(emptyState('Could not load', err.message));
    }
  };
  let timer;
  search.addEventListener('input', () => { clearTimeout(timer); timer = setTimeout(load, 220); });
  await load();
}

function openCreate(resource) {
  const close = modal(`New ${resource.label.replace(/s$/, '')}`, resourceForm(resource, null, async (body) => {
    await api(`/api/${resource.name}`, { method: 'POST', body });
    close(); toast('Created'); render();
  }));
}

function openEdit(resource, record, reload) {
  const close = modal(`Edit ${resource.label.replace(/s$/, '')}`, resourceForm(resource, record, async (body) => {
    await api(`/api/${resource.name}/${record.id}`, { method: 'PATCH', body });
    close(); toast('Saved'); reload ? reload() : render();
  }));
}

/* ------------------------- shortener ---------------------------- */
async function renderShortener() {
  setHeader('Short links', 'Create a keyword and redirect visitors.', []);
  const view = $('#view'); view.innerHTML = '';
  const form = el('form', { class: 'card', style: 'margin-bottom:16px' });
  form.append(el('div', { class: 'form-row' },
    el('div', { class: 'field' }, el('label', {}, 'Destination URL'), el('input', { name: 'target', type: 'url', required: true, placeholder: 'https://example.com/page' })),
    el('div', { class: 'field' }, el('label', {}, 'Custom keyword (optional)'), el('input', { name: 'slug', placeholder: 'launch' }))));
  form.append(el('button', { class: 'btn primary', type: 'submit' }, 'Shorten'));
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!state.user) return authModal('login');
    const body = Object.fromEntries(new FormData(form));
    body.slug = body.slug || Math.random().toString(36).slice(2, 8);
    try {
      await api('/api/links', { method: 'POST', body: { ...body, clicks: 0 } });
      form.reset(); toast('Short link created'); render();
    } catch (err) { toast(err.message); }
  });
  view.append(form);
  const list = el('div', { class: 'card' });
  view.append(list);
  const data = await api('/api/links');
  if (!data.items.length) list.append(emptyState('No links yet', 'Your short links will appear here.'));
  for (const link of data.items) {
    list.append(el('div', { class: 'row between wrap gap', style: 'padding:10px 0;border-bottom:1px solid var(--line)' },
      el('div', {}, el('strong', {}, `/${link.slug}`), el('div', { class: 'muted small' }, link.target)),
      el('div', { class: 'row gap' },
        el('span', { class: 'badge' }, `${link.clicks || 0} clicks`),
        el('a', { class: 'btn small', href: `/r/${link.slug}`, target: '_blank', rel: 'noopener' }, 'Open'))));
  }
}

/* --------------------------- uptime ----------------------------- */
async function renderUptime() {
  setHeader('Monitors', 'HTTP checks, latency and public status.', []);
  const view = $('#view'); view.innerHTML = '';
  if (state.user) {
    $('#top-actions').append(el('button', { class: 'btn', onclick: () => { location.hash = '#/monitors'; } }, 'Manage monitors'));
  }
  const status = await api('/api/status');
  const summary = el('div', { class: 'grid cols-3', style: 'margin-bottom:16px' });
  const up = status.monitors.filter((m) => m.last && m.last.status === 'up').length;
  summary.append(
    el('div', { class: 'card stat' }, el('span', {}, 'Monitors'), el('b', {}, status.monitors.length), el('span', { class: 'muted small' }, 'configured')),
    el('div', { class: 'card stat' }, el('span', {}, 'Operational'), el('b', {}, up), el('span', { class: 'muted small' }, 'last check up')),
    el('div', { class: 'card stat' }, el('span', {}, 'Generated'), el('b', { style: 'font-size:1rem' }, fmtDate(status.generated_at)), el('span', { class: 'muted small' }, 'UTC')));
  view.append(summary);
  for (const monitor of status.monitors) {
    const statusName = monitor.last ? monitor.last.status : 'unknown';
    const card = el('div', { class: 'card', style: 'margin-bottom:12px' });
    card.append(el('div', { class: 'row between wrap gap' },
      el('div', {}, el('h3', {}, monitor.name), el('p', { class: 'muted small' }, monitor.url)),
      el('div', { class: 'row gap' },
        el('span', { class: 'badge ' + (statusName === 'up' ? 'ok' : statusName === 'down' ? 'bad' : 'warn') },
          el('span', { class: 'dot ' + statusName }), statusName),
        monitor.uptime_percent !== null ? el('span', { class: 'badge' }, `${monitor.uptime_percent}% uptime`) : '',
        el('span', { class: 'badge' }, monitor.last ? `${monitor.last.latency_ms} ms` : 'not checked'))));
    const checks = await api(`/api/monitors/${monitor.id}/checks`);
    if (checks.checks.length) {
      const spark = el('div', { class: 'spark', style: 'margin-top:12px' });
      const max = Math.max(...checks.checks.map((c) => c.latency_ms || 1), 1);
      for (const check of checks.checks.slice(-40)) {
        spark.append(el('i', { style: `height:${Math.max(8, ((check.latency_ms || 1) / max) * 100)}%;background:${check.status === 'up' ? 'var(--ok)' : 'var(--danger)'}`, title: `${fmtDate(check.checked_at)} · ${check.latency_ms}ms` }));
      }
      card.append(spark);
    }
    if (state.user) {
      card.append(el('button', { class: 'btn small', style: 'margin-top:12px', onclick: async (e) => {
        e.target.disabled = true;
        try { const r = await api(`/api/monitors/${monitor.id}/check`, { method: 'POST' }); toast(`${monitor.name}: ${r.status} (${r.latency_ms}ms)`); render(); }
        catch (err) { toast(err.message); e.target.disabled = false; }
      } }, 'Check now'));
    }
    view.append(card);
  }
  if (!status.monitors.length) view.append(emptyState('No monitors', 'Add a monitor to start checking uptime.'));
}

/* -------------------------- booking ----------------------------- */
async function renderBooking() {
  setHeader('Book a meeting', 'Pick an event and reserve an open slot.', []);
  const view = $('#view'); view.innerHTML = '';
  const events = await api('/api/event_types');
  if (!events.items.length) return view.append(emptyState('No event types', 'Create an event type first.'));
  const form = el('form', { class: 'card', style: 'margin-bottom:16px' });
  const eventSelect = el('select', { name: 'event_type_id' });
  for (const event of events.items) eventSelect.append(el('option', { value: event.id }, `${event.name} · ${event.duration_minutes} min`));
  const date = el('input', { type: 'date', name: 'date', required: true });
  date.value = new Date(Date.now() + 86400000).toISOString().slice(0, 10);
  const slotsBox = el('div', { class: 'pill-list', style: 'margin:8px 0 14px' });
  form.append(el('div', { class: 'form-row' },
    el('div', { class: 'field' }, el('label', {}, 'Event'), eventSelect),
    el('div', { class: 'field' }, el('label', {}, 'Date'), date)),
    el('label', {}, 'Available slots'), slotsBox);
  const name = el('input', { name: 'booker_name', required: true, placeholder: 'Your name' });
  const email = el('input', { name: 'booker_email', type: 'email', required: true, placeholder: 'you@example.com' });
  const notes = el('textarea', { name: 'notes', rows: 3, placeholder: 'Anything the host should know?' });
  form.append(el('div', { class: 'form-row' },
    el('div', { class: 'field' }, el('label', {}, 'Name'), name),
    el('div', { class: 'field' }, el('label', {}, 'Email'), email)),
    el('div', { class: 'field' }, el('label', {}, 'Notes'), notes),
    el('button', { class: 'btn primary', type: 'submit' }, 'Confirm booking'));
  view.append(form);
  let selected = null;
  const loadSlots = async () => {
    const event = events.items.find((e) => String(e.id) === eventSelect.value);
    slotsBox.innerHTML = '<span class="muted small">Loading…</span>';
    try {
      const data = await api(`/api/availability?slug=${encodeURIComponent(event.slug)}&date=${date.value}`);
      slotsBox.innerHTML = '';
      selected = null;
      if (!data.slots.length) return slotsBox.append(el('span', { class: 'muted small' }, 'No open slots on this day.'));
      for (const slot of data.slots) {
        slotsBox.append(el('button', { type: 'button', class: 'btn small', onclick: (e) => {
          selected = slot;
          for (const b of slotsBox.querySelectorAll('button')) b.classList.remove('primary');
          e.target.classList.add('primary');
        } }, new Date(slot).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })));
      }
    } catch (err) { slotsBox.textContent = err.message; }
  };
  eventSelect.addEventListener('change', loadSlots);
  date.addEventListener('change', loadSlots);
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!selected) return toast('Pick an available slot first.');
    try {
      await api('/api/book', { method: 'POST', body: {
        event_type_id: Number(eventSelect.value), start_at: selected,
        booker_name: name.value, booker_email: email.value, notes: notes.value } });
      toast('Booking confirmed'); form.reset(); loadSlots();
    } catch (err) { toast(err.message); }
  });
  await loadSlots();
  view.append(el('a', { class: 'btn small', href: '/api/bookings.ics' }, 'Download bookings (.ics)'));
}

/* ---------------------------- chat ------------------------------ */
let chatSource;
async function renderChat() {
  setHeader('Channels', 'Real-time team conversation.', []);
  const view = $('#view'); view.innerHTML = '';
  const data = await api('/api/channels');
  const layout = el('div', { class: 'chat-layout' });
  const list = el('div', { class: 'card chat-list' });
  const pane = el('div', { class: 'card' });
  layout.append(list, pane); view.append(layout);
  if (!data.items.length) return view.append(emptyState('No channels', 'Create a channel to start chatting.'));
  let active = data.items[0];
  const renderPane = async () => {
    pane.innerHTML = '';
    pane.append(el('h2', {}, `# ${active.name}`), el('p', { class: 'muted small', style: 'margin-bottom:10px' }, active.topic || ''));
    const messages = el('div', { class: 'messages' });
    pane.append(messages);
    const form = el('form', { class: 'row gap', style: 'margin-top:10px' });
    const input = el('input', { placeholder: state.user ? 'Write a message…' : 'Sign in to send messages', disabled: !state.user });
    form.append(input, el('button', { class: 'btn primary', type: 'submit' }, 'Send'));
    pane.append(form);
    const load = async () => {
      const m = await api(`/api/messages?q=&limit=200`);
      const mine = m.items.filter((x) => Number(x.channel_id) === Number(active.id)).reverse();
      messages.innerHTML = '';
      if (!mine.length) messages.append(el('p', { class: 'muted', style: 'padding:20px' }, 'No messages yet. Say hello.'));
      for (const msg of mine) {
        messages.append(el('div', { class: 'msg' + (state.user && msg.author === state.user.name ? ' mine' : '') },
          el('b', {}, msg.author), el('div', {}, msg.body), el('span', {}, relTime(msg.created_at))));
      }
      messages.scrollTop = messages.scrollHeight;
    };
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      if (!input.value.trim()) return;
      try {
        await api('/api/messages', { method: 'POST', body: { channel_id: active.id, body: input.value, author: state.user.name } });
        input.value = ''; load();
      } catch (err) { toast(err.message); }
    });
    await load();
  };
  for (const channel of data.items) {
    list.append(el('button', { onclick: () => { active = channel; renderChat(); } }, `# ${channel.name}`));
  }
  await renderPane();
  if (chatSource) chatSource.close();
  chatSource = new EventSource('/api/stream');
  chatSource.addEventListener('message', () => renderChat());
}

/* --------------------------- kanban ----------------------------- */
async function renderKanban() {
  setHeader('Board', 'Cards, lists and drag-free moving.', []);
  const view = $('#view'); view.innerHTML = '';
  const [boards, lists, cards] = await Promise.all([api('/api/boards'), api('/api/lists'), api('/api/cards')]);
  if (!boards.items.length) return view.append(emptyState('No boards', 'Create a board to get started.'));
  const board = boards.items[0];
  view.append(el('div', { class: 'row between', style: 'margin-bottom:12px' },
    el('h2', {}, board.name), state.user ? el('a', { class: 'btn small', href: '#/boards' }, 'Manage') : ''));
  const boardLists = lists.items.filter((l) => Number(l.board_id) === Number(board.id)).sort((a, b) => (a.position || 0) - (b.position || 0));
  const wrap = el('div', { class: 'kanban' });
  for (const list of boardLists) {
    const col = el('div', { class: 'kanban-col' }, el('h3', {}, list.name));
    const listCards = cards.items.filter((c) => Number(c.list_id) === Number(list.id)).sort((a, b) => (a.position || 0) - (b.position || 0));
    for (const card of listCards) {
      col.append(el('div', { class: 'kcard' }, el('strong', {}, card.title),
        card.notes ? el('p', {}, card.notes) : '', el('div', { class: 'muted small' }, card.assignee || '', card.due_date ? ` · ${card.due_date}` : ''),
        state.user ? el('div', { class: 'row gap', style: 'margin-top:8px' },
          el('select', { class: 'small', onchange: async (e) => {
            try { await api(`/api/cards/${card.id}/move`, { method: 'PATCH', body: { list_id: Number(e.target.value), position: 0 } }); render(); }
            catch (err) { toast(err.message); }
          } }, boardLists.map((l) => el('option', { value: l.id, selected: Number(l.id) === Number(list.id) }, l.name)))) : ''));
    }
    wrap.append(col);
  }
  view.append(wrap);
}

/* -------------------------- commerce ---------------------------- */
async function renderCommerce() {
  setHeader('Store', 'Products, a cart and a checkout.', []);
  const view = $('#view'); view.innerHTML = '';
  const products = await api('/api/products');
  const grid = el('div', { class: 'product-grid' });
  for (const product of products.items) {
    grid.append(el('div', { class: 'card product' },
      el('div', { class: 'row between' }, el('span', { class: 'badge' }, product.category || 'Product'), el('span', { class: 'badge ' + (product.stock > 0 ? 'ok' : 'bad') }, `${product.stock} in stock`)),
      el('h3', {}, product.name), el('p', { class: 'muted small' }, product.description || ''),
      el('div', { class: 'row between' }, el('span', { class: 'price' }, fmtMoney(product.price_cents)),
        el('button', { class: 'btn small', disabled: product.stock <= 0, onclick: () => {
          const existing = state.cart.find((i) => i.product_id === product.id);
          if (existing) existing.quantity++;
          else state.cart.push({ product_id: product.id, name: product.name, price_cents: product.price_cents, quantity: 1 });
          toast(`${product.name} added to cart`); renderCommerce();
        } }, 'Add to cart'))));
  }
  view.append(grid);
  if (state.cart.length) {
    const total = state.cart.reduce((sum, i) => sum + i.price_cents * i.quantity, 0);
    const cart = el('div', { class: 'card', style: 'margin-top:16px' },
      el('h2', {}, 'Cart'),
      ...state.cart.map((item) => el('div', { class: 'row between gap', style: 'padding:6px 0' },
        el('span', {}, `${item.name} × ${item.quantity}`), el('span', {}, fmtMoney(item.price_cents * item.quantity)))),
      el('hr', { style: 'border:0;border-top:1px solid var(--line);margin:10px 0' }),
      el('div', { class: 'row between' }, el('strong', {}, 'Total'), el('strong', {}, fmtMoney(total))));
    const form = el('form', { class: 'row gap', style: 'margin-top:12px' });
    form.append(el('input', { name: 'email', type: 'email', placeholder: 'Email for receipt', required: true }),
      el('button', { class: 'btn primary', type: 'submit' }, 'Checkout'));
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      try {
        const result = await api('/api/checkout', { method: 'POST', body: { email: form.email.value, items: state.cart } });
        state.cart = []; toast(`Order #${result.order_id} paid · ${fmtMoney(result.total_cents)}`); renderCommerce();
      } catch (err) { toast(err.message); }
    });
    cart.append(form);
    view.append(cart);
  }
}

/* ---------------------------- wiki ------------------------------ */
async function renderWiki() {
  setHeader('Knowledge base', 'Books, pages and revision history.', []);
  const view = $('#view'); view.innerHTML = '';
  const [books, pages] = await Promise.all([api('/api/books'), api('/api/pages')]);
  const layout = el('div', { class: 'grid cols-2' });
  const left = el('div', { class: 'card' });
  left.append(el('h2', {}, 'Books'));
  for (const book of books.items) {
    const bookPages = pages.items.filter((p) => Number(p.book_id) === Number(book.id));
    left.append(el('div', { style: 'padding:10px 0;border-bottom:1px solid var(--line)' },
      el('strong', {}, book.title), el('p', { class: 'muted small' }, book.description || ''),
      el('div', { class: 'pill-list', style: 'margin-top:6px' }, bookPages.map((p) => el('button', { class: 'btn small', onclick: () => openPage(p) }, p.title)))));
  }
  const right = el('div', { class: 'card' }, el('h2', {}, 'Recent pages'));
  for (const page of pages.items.slice(0, 8)) {
    right.append(el('div', { style: 'padding:10px 0;border-bottom:1px solid var(--line)' },
      el('a', { href: '#', onclick: (e) => { e.preventDefault(); openPage(page); } }, page.title),
      el('p', { class: 'muted small' }, `${page.body.slice(0, 110)}…`)));
  }
  layout.append(left, right); view.append(layout);
  async function openPage(page) {
    const revisions = await api(`/api/pages/${page.id}/revisions`);
    modal(page.title, el('div', {},
      el('p', { style: 'white-space:pre-wrap' }, page.body),
      el('p', { class: 'muted small', style: 'margin-top:16px' }, `Version ${page.version || 1} · ${revisions.revisions.length} earlier revisions`),
      revisions.revisions.length ? el('div', { style: 'margin-top:10px' }, revisions.revisions.map((r) => el('div', { class: 'badge', style: 'margin-right:6px' }, `v${r.version} · ${relTime(r.created_at)}`))) : ''));
  }
}

/* --------------------------- social ----------------------------- */
async function renderSocial() {
  setHeader('Feed', 'Posts from people you follow.', []);
  const view = $('#view'); view.innerHTML = '';
  const form = el('form', { class: 'card', style: 'margin-bottom:16px' });
  const input = el('textarea', { name: 'body', rows: 3, placeholder: state.user ? "What's happening?" : 'Sign in to post', disabled: !state.user });
  form.append(el('div', { class: 'field' }, input),
    el('div', { class: 'row between' }, el('span', { class: 'muted small' }, state.user ? `Posting as ${state.user.name}` : 'Read-only'),
      el('button', { class: 'btn primary', type: 'submit', disabled: !state.user }, 'Post')));
  form.addEventListener('submit', async (e) => {
    e.preventDefault(); if (!input.value.trim()) return;
    try { await api('/api/posts', { method: 'POST', body: { body: input.value, author: state.user.name, likes: 0 } }); input.value = ''; renderSocial(); }
    catch (err) { toast(err.message); }
  });
  view.append(form);
  const posts = await api('/api/posts?limit=50');
  if (!posts.items.length) view.append(emptyState('No posts yet', 'Start the conversation.'));
  for (const post of posts.items) {
    view.append(el('div', { class: 'card', style: 'margin-bottom:12px' },
      el('div', { class: 'row between' }, el('strong', {}, post.author), el('span', { class: 'muted small' }, relTime(post.created_at))),
      el('p', { style: 'margin:10px 0' }, post.body),
      el('div', { class: 'row gap' },
        el('button', { class: 'btn small', onclick: async () => {
          if (!state.user) return authModal('login');
          try { await api(`/api/posts/${post.id}/like`, { method: 'POST' }); renderSocial(); } catch (err) { toast(err.message); }
        } }, `♥ ${post.likes || 0}`))));
  }
}

/* -------------------------- helpdesk ---------------------------- */
async function renderHelpdesk() {
  setHeader('Inbox', 'Conversations and replies.', []);
  const view = $('#view'); view.innerHTML = '';
  const [convos, messages] = await Promise.all([api('/api/conversations'), api('/api/messages')]);
  const layout = el('div', { class: 'grid cols-2' });
  const list = el('div', { class: 'card' });
  list.append(el('h2', {}, 'Conversations'));
  const pane = el('div', { class: 'card' }, el('p', { class: 'muted' }, 'Select a conversation.'));
  for (const convo of convos.items) {
    const count = messages.items.filter((m) => Number(m.conversation_id) === Number(convo.id)).length;
    list.append(el('button', { class: 'chat-list', style: 'width:100%;border:0;background:transparent;text-align:left;padding:10px 0;cursor:pointer', onclick: async () => {
      pane.innerHTML = '';
      pane.append(el('h2', {}, convo.subject), el('p', { class: 'muted small' }, `${convo.requester} · ${convo.status}`));
      const thread = messages.items.filter((m) => Number(m.conversation_id) === Number(convo.id));
      const box = el('div', { class: 'messages' });
      for (const msg of thread) box.append(el('div', { class: 'msg' }, el('b', {}, msg.sender), el('div', {}, msg.body)));
      pane.append(box);
      const form = el('form', { class: 'row gap' });
      form.append(el('input', { name: 'body', placeholder: 'Reply…', required: true }), el('button', { class: 'btn primary', type: 'submit' }, 'Send'));
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        try { await api('/api/messages', { method: 'POST', body: { conversation_id: convo.id, sender: state.user ? state.user.name : 'Agent', body: form.body.value } }); renderHelpdesk(); }
        catch (err) { toast(err.message); }
      });
      pane.append(form);
    } },
      el('strong', {}, convo.subject), el('div', { class: 'muted small' }, `${convo.requester} · ${count} messages`),
      el('span', { class: 'badge', style: 'margin-top:5px' }, convo.status)));
  }
  layout.append(list, pane); view.append(layout);
}

/* ------------------------- read later --------------------------- */
async function renderReadLater() {
  setHeader('Reading list', 'Save an article and read it without the noise.', []);
  const view = $('#view'); view.innerHTML = '';
  const form = el('form', { class: 'card row gap wrap', style: 'margin-bottom:16px' });
  form.append(el('input', { name: 'url', type: 'url', placeholder: 'https://…', required: true, style: 'flex:1;min-width:220px' }),
    el('button', { class: 'btn primary', type: 'submit' }, 'Extract & save'));
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!state.user) return authModal('login');
    try {
      const article = await api('/api/extract', { method: 'POST', body: { url: form.url.value } });
      await api('/api/articles', { method: 'POST', body: { ...article, read: 0, tags: '' } });
      toast('Saved to reading list'); render();
    } catch (err) { toast(err.message); }
  });
  view.append(form);
  const articles = await api('/api/articles');
  if (!articles.items.length) view.append(emptyState('Nothing saved', 'Paste a URL above to extract a readable copy.'));
  for (const article of articles.items) {
    view.append(el('div', { class: 'card', style: 'margin-bottom:12px' },
      el('div', { class: 'row between gap wrap' }, el('h3', {}, article.title || article.url),
        el('span', { class: 'badge ' + (article.read ? 'ok' : '') }, article.read ? 'read' : 'unread')),
      el('p', { class: 'muted', style: 'margin:8px 0' }, article.excerpt || ''),
      el('div', { class: 'row gap' }, el('a', { class: 'btn small', href: article.url, target: '_blank', rel: 'noopener' }, 'Open original'),
        state.user ? el('button', { class: 'btn small', onclick: async () => { await api(`/api/articles/${article.id}`, { method: 'PATCH', body: { read: article.read ? 0 : 1 } }); render(); } }, article.read ? 'Mark unread' : 'Mark read') : '')));
  }
}

/* ---------------------------- blog ------------------------------ */
async function renderBlog() {
  setHeader('Journal', 'Published notes from the team.');
  const view = $('#view'); view.innerHTML = '';
  const data = await api('/api/blog');
  if (state.user) $('#top-actions').append(el('a', { class: 'btn primary', href: '#/posts' }, '+ Write a post'));
  const head = el('div', { class: 'card', style: 'margin-bottom:16px' },
    el('div', { class: 'row between wrap gap' },
      el('div', {}, el('h2', {}, state.meta.name), el('p', { class: 'muted' }, state.meta.description)),
      el('span', { class: 'badge' }, `${data.members} members`)));
  view.append(head);
  if (!data.posts.length) return view.append(emptyState('No published posts', 'Publish a post from the Posts resource to see it here.'));
  for (const post of data.posts) {
    view.append(el('article', { class: 'card', style: 'margin-bottom:14px' },
      el('div', { class: 'muted small' }, `${post.author || 'Editor'} · ${post.published_at || relTime(post.created_at)}`),
      el('h2', { style: 'margin:6px 0' }, post.title),
      el('p', { class: 'muted' }, post.excerpt || String(post.body || '').slice(0, 180)),
      el('button', { class: 'btn small', style: 'margin-top:10px', onclick: () => modal(post.title,
        el('div', {}, el('p', { class: 'muted small' }, `${post.author || 'Editor'} · ${post.published_at || ''}`),
          el('div', { style: 'white-space:pre-wrap;line-height:1.75;margin-top:12px' }, post.body))) }, 'Read post')));
  }
}

/* ---------------------- generic fallback ------------------------ */
async function renderNotFound() {
  setHeader('Not found', 'That page does not exist.');
  $('#view').innerHTML = '';
  $('#view').append(emptyState('404', 'Try the dashboard.', el('a', { class: 'btn primary', href: '#/' }, 'Go home')));
}

/* ---------------------------------------------------------------- */
/* Router                                                            */
/* ---------------------------------------------------------------- */
async function render() {
  const hash = location.hash.replace(/^#/, '') || '/';
  state.route = hash;
  renderNav();
  const [section, sub] = hash.split('/').filter(Boolean);
  try {
    if (!section) return await renderDashboard();
    if (state.meta.special === 'shortener' && section === 'links') return await renderShortener();
    if (state.meta.special === 'uptime' && section === 'status') return await renderUptime();
    if (state.meta.special === 'uptime' && section === 'monitors') return await renderResource('monitors');
    if (state.meta.special === 'booking' && section === 'schedule') return await renderBooking();
    if (state.meta.special === 'chat' && section === 'channels') return await renderChat();
    if (state.meta.special === 'kanban' && section === 'board') return await renderKanban();
    if (state.meta.special === 'commerce' && section === 'store') return await renderCommerce();
    if (state.meta.special === 'wiki' && section === 'wiki') return await renderWiki();
    if (state.meta.special === 'social' && section === 'feed') return await renderSocial();
    if (state.meta.special === 'helpdesk' && section === 'inbox') return await renderHelpdesk();
    if (state.meta.special === 'readlater' && section === 'reading') return await renderReadLater();
    if (state.meta.special === 'blog' && section === 'blog') return await renderBlog();
    return await renderResource(section);
  } catch (err) {
    $('#view').innerHTML = '';
    $('#view').append(emptyState('Something went wrong', err.message));
  }
}

async function boot() {
  try {
    state.meta = await api('/api/meta');
    state.user = state.meta.user;
    document.title = state.meta.name;
    renderNav();
    await render();
  } catch (err) {
    $('#view').innerHTML = `<div class="empty"><h3>Cannot reach the server</h3><p>${esc(err.message)}</p></div>`;
  }
  $('#menu-btn').addEventListener('click', () => $('.sidebar').classList.toggle('open'));
  document.addEventListener('click', (e) => {
    if (e.target.closest('.nav a') && window.innerWidth < 720) $('.sidebar').classList.remove('open');
  });
  window.addEventListener('hashchange', render);
  const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  if (prefersDark) document.documentElement.dataset.theme = 'dark';
}
boot();
