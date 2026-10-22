import { html } from './htm.js';
import { formatCents, centsToStr, strToCents } from './format.js';
import { api } from './api.js';
import { createStore } from './store.js';
import { SyncEngine } from './sync.js';
import { DataLayer } from './data.js';

const React = window.React;
const { useState, useEffect, useCallback, useRef } = React;

const store = createStore();
const engine = new SyncEngine({
  store,
  api,
  isOnline: () => (typeof navigator === 'undefined' ? true : navigator.onLine !== false),
});
const data = new DataLayer({ api, engine });

/** Re-render the app when the sync engine reports a change. */
const listeners = new Set();
function notify() {
  for (const listener of listeners) listener();
}

/** The data layer and the engine, for the tests to reach. */
export function appInternals() {
  return { store, engine, data, api };
}

// ---------------------------------------------------------------------------
// Shared hooks
// ---------------------------------------------------------------------------

function useBootstrap() {
  const [state, setState] = useState({ loading: true, data: null, error: null });

  useEffect(() => {
    let cancelled = false;

    (async () => {
      try {
        // Pull the mirror down first, then bring it up to date with the server.
        await engine.pull().catch(() => {});
        await engine.sync().catch(() => {});
        const bootstrap = await api.bootstrap();
        if (!cancelled) setState({ loading: false, data: bootstrap, error: null });
      } catch (error) {
        if (!cancelled) setState({ loading: false, data: null, error: error.message });
      }
    })();

    return () => { cancelled = true; };
  }, []);

  return state;
}

function useSyncStatus() {
  const [status, setStatus] = useState({ online: true, pending: 0, syncing: false, lastError: null });

  const refresh = useCallback(async () => {
    setStatus((previous) => ({ ...previous, syncing: true }));
    const pending = await engine.pendingCount();
    let online = data.isOnline();
    try {
      await engine.sync();
      online = true;
    } catch {
      online = false;
    }
    setStatus({ online, pending: await engine.pendingCount(), syncing: false, lastError: engine.lastError });
    notify();
  }, []);

  useEffect(() => {
    refresh();
    const onOnline = () => refresh();
    const onOffline = () => setStatus((previous) => ({ ...previous, online: false }));
    if (typeof window !== 'undefined') {
      window.addEventListener('online', onOnline);
      window.addEventListener('offline', onOffline);
    }
    return () => {
      if (typeof window !== 'undefined') {
        window.removeEventListener('online', onOnline);
        window.removeEventListener('offline', onOffline);
      }
    };
  }, [refresh]);

  return { status, refresh };
}

/** Load a list and keep it in state, with a reload function. */
function useList(loader, deps = []) {
  const [state, setState] = useState({ loading: true, rows: [], error: null });

  const reload = useCallback(async () => {
    setState((previous) => ({ ...previous, loading: true }));
    try {
      const rows = await loader();
      setState({ loading: false, rows, error: null });
    } catch (error) {
      setState({ loading: false, rows: [], error: error.message });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(() => { reload(); }, [reload]);

  return { ...state, reload };
}

// ---------------------------------------------------------------------------
// Chrome
// ---------------------------------------------------------------------------

function Nav({ view, setView }) {
  const links = [
    ['budget', 'Budget'],
    ['transactions', 'Transactions'],
    ['accounts', 'Accounts'],
    ['reports', 'Reports'],
    ['rules', 'Rules'],
    ['schedules', 'Schedules'],
    ['goals', 'Goals'],
    ['import', 'Import'],
  ];
  return html`
    <nav class="header__nav">
      ${links.map(([key, label]) => html`
        <a href="#${key}" class="header__link ${view === key ? 'active' : ''}" onClick=${(e) => { e.preventDefault(); setView(key); }}>${label}</a>
      `)}
    </nav>
  `;
}

function SyncBadge({ status, refresh }) {
  const label = status.syncing
    ? 'Syncing...'
    : !status.online
      ? `Offline${status.pending ? ` · ${status.pending} pending` : ''}`
      : status.pending
        ? `${status.pending} pending`
        : 'Online';

  return html`
    <button
      class="header__status ${status.online ? '' : 'negative'}"
      onClick=${refresh}
      title=${status.lastError || 'Click to sync now'}
    >${label}</button>
  `;
}

// ---------------------------------------------------------------------------
// Budget
// ---------------------------------------------------------------------------

function BudgetView({ data: bootstrap }) {
  const [month, setMonth] = useState(bootstrap.month);
  const [budget, setBudget] = useState(bootstrap.budget);
  const [groups, setGroups] = useState(bootstrap.budget_groups);
  const [editing, setEditing] = useState(null);
  const [draft, setDraft] = useState('');
  const [message, setMessage] = useState(null);

  const refresh = async (target) => {
    const res = await api.getBudget(target || month);
    setBudget(res);
    setGroups(res.groups);
    setMonth(res.month);
  };

  const save = async (categoryId) => {
    const cents = strToCents(draft);
    await api.setBudget(month, categoryId, cents);
    setEditing(null);
    setDraft('');
    await refresh(month);
    setMessage({ kind: 'success', text: 'Budget updated.' });
  };

  return html`
    <div class="card">
      <h2>Budget - ${budget.month}</h2>
      <p class="muted">To be budgeted: ${formatCents(budget.to_be_budgeted)}</p>
      ${message && html`<p class="${message.kind}">${message.text}</p>`}
      <table class="table">
        <thead>
          <tr>
            <th>Category</th>
            <th class="money">Budgeted</th>
            <th class="money">Activity</th>
            <th class="money">Available</th>
          </tr>
        </thead>
        ${groups.map((g) => html`
          <tbody>
            <tr>
              <th colspan="4">${g.name} ${g.is_income ? '(Income)' : ''}</th>
            </tr>
            ${g.categories.map((c) => html`
              <tr>
                <td>${c.name}</td>
                <td class="money" onClick=${() => { setEditing(c.id); setDraft(centsToStr(c.budgeted)); }}>
                  ${editing === c.id
                    ? html`<input
                        class="input input--inline"
                        value=${draft}
                        onInput=${(e) => setDraft(e.target.value)}
                        onKeyDown=${(e) => { if (e.key === 'Enter') save(c.id); if (e.key === 'Escape') setEditing(null); }}
                        onBlur=${() => setEditing(null)}
                        autoFocus
                      />`
                    : formatCents(c.budgeted)}
                </td>
                <td class="money">${formatCents(c.activity)}</td>
                <td class="money ${c.available < 0 ? 'negative' : ''}">${formatCents(c.available)}</td>
              </tr>
            `)}
          </tbody>
        `)}
      </table>
      <p class="muted">Click a budgeted amount to edit it.</p>
    </div>
  `;
}

// ---------------------------------------------------------------------------
// Accounts
// ---------------------------------------------------------------------------

function AccountsView({ data: bootstrap }) {
  const [accounts] = useState(bootstrap.accounts);
  return html`
    <div class="card">
      <h2>Accounts</h2>
      <table class="table">
        <thead>
          <tr><th>Name</th><th>Type</th><th>On budget</th><th class="money">Balance</th></tr>
        </thead>
        ${accounts.map((a) => html`
          <tr>
            <td>${a.name}</td>
            <td>${a.type}</td>
            <td>${a.on_budget ? 'Yes' : 'No'}</td>
            <td class="money ${a.balance < 0 ? 'negative' : ''}">${formatCents(a.balance)}</td>
          </tr>
        `)}
      </table>
    </div>
  `;
}

// ---------------------------------------------------------------------------
// Transactions
// ---------------------------------------------------------------------------

function TransactionsView({ data: bootstrap }) {
  const { rows: items, reload } = useList(() => data.listTransactions('limit=200'), []);
  const [form, setForm] = useState({ account_id: '', date: '', payee: '', amount: '', category_id: '', memo: '' });
  const [transfer, setTransfer] = useState({ from: '', to: '', amount: '', date: '' });
  const [message, setMessage] = useState(null);
  const [showTransfer, setShowTransfer] = useState(false);

  const accounts = bootstrap.accounts || [];
  const categories = bootstrap.categories || [];

  const submit = async (event) => {
    event.preventDefault();
    const body = {
      account_id: Number(form.account_id),
      date: form.date,
      payee: form.payee,
      memo: form.memo,
      amount_cents: strToCents(form.amount),
      category_id: form.category_id ? Number(form.category_id) : null,
    };
    if (!body.account_id || !body.date) {
      setMessage({ kind: 'error', text: 'An account and a date are required.' });
      return;
    }
    await data.createTransaction(body);
    setForm({ account_id: '', date: '', payee: '', amount: '', category_id: '', memo: '' });
    setMessage({ kind: 'success', text: 'Transaction added.' });
    await reload();
  };

  const submitTransfer = async (event) => {
    event.preventDefault();
    const cents = strToCents(transfer.amount);
    if (!transfer.from || !transfer.to || !transfer.date || cents === 0) {
      setMessage({ kind: 'error', text: 'Both accounts, a date and an amount are required.' });
      return;
    }
    await data.createTransaction({
      account_id: Number(transfer.from),
      date: transfer.date,
      payee: 'Transfer',
      amount_cents: -Math.abs(cents),
      transfer_account_id: Number(transfer.to),
      category_id: null,
      memo: '',
    });
    await data.createTransaction({
      account_id: Number(transfer.to),
      date: transfer.date,
      payee: 'Transfer',
      amount_cents: Math.abs(cents),
      transfer_account_id: Number(transfer.from),
      category_id: null,
      memo: '',
    });
    setTransfer({ from: '', to: '', amount: '', date: '' });
    setShowTransfer(false);
    setMessage({ kind: 'success', text: 'Transfer recorded.' });
    await reload();
  };

  const recategorise = async (transaction, categoryId) => {
    await data.updateTransaction(transaction.id, { category_id: categoryId ? Number(categoryId) : null });
    await reload();
  };

  const remove = async (transaction) => {
    await data.removeTransaction(transaction.id);
    await reload();
  };

  return html`
    <div class="card">
      <h2>Transactions</h2>
      ${message && html`<p class="${message.kind}">${message.text}</p>`}

      <form class="form" onSubmit=${submit}>
        <h3>Add a transaction</h3>
        <label>
          Account
          <select value=${form.account_id} onChange=${(e) => setForm({ ...form, account_id: e.target.value })}>
            <option value="">Select an account</option>
            ${accounts.map((a) => html`<option value=${a.id}>${a.name}</option>`)}
          </select>
        </label>
        <label>
          Date
          <input type="date" value=${form.date} onInput=${(e) => setForm({ ...form, date: e.target.value })} />
        </label>
        <label>
          Payee
          <input type="text" value=${form.payee} onInput=${(e) => setForm({ ...form, payee: e.target.value })} />
        </label>
        <label>
          Amount
          <input type="text" inputMode="decimal" value=${form.amount} onInput=${(e) => setForm({ ...form, amount: e.target.value })} />
        </label>
        <label>
          Category
          <select value=${form.category_id} onChange=${(e) => setForm({ ...form, category_id: e.target.value })}>
            <option value="">Uncategorised</option>
            ${categories.map((c) => html`<option value=${c.id}>${c.name}</option>`)}
          </select>
        </label>
        <label>
          Memo
          <input type="text" value=${form.memo} onInput=${(e) => setForm({ ...form, memo: e.target.value })} />
        </label>
        <button type="submit">Add transaction</button>
        <button type="button" onClick=${() => setShowTransfer(!showTransfer)}>
          ${showTransfer ? 'Cancel transfer' : 'Record a transfer'}
        </button>
      </form>

      ${showTransfer && html`
        <form class="form" onSubmit=${submitTransfer}>
          <h3>Transfer between accounts</h3>
          <label>
            From
            <select value=${transfer.from} onChange=${(e) => setTransfer({ ...transfer, from: e.target.value })}>
              <option value="">Select an account</option>
              ${accounts.map((a) => html`<option value=${a.id}>${a.name}</option>`)}
            </select>
          </label>
          <label>
            To
            <select value=${transfer.to} onChange=${(e) => setTransfer({ ...transfer, to: e.target.value })}>
              <option value="">Select an account</option>
              ${accounts.map((a) => html`<option value=${a.id}>${a.name}</option>`)}
            </select>
          </label>
          <label>
            Date
            <input type="date" value=${transfer.date} onInput=${(e) => setTransfer({ ...transfer, date: e.target.value })} />
          </label>
          <label>
            Amount
            <input type="text" inputMode="decimal" value=${transfer.amount} onInput=${(e) => setTransfer({ ...transfer, amount: e.target.value })} />
          </label>
          <button type="submit">Record transfer</button>
        </form>
      `}

      <table class="table">
        <thead>
          <tr><th>Date</th><th>Payee</th><th>Account</th><th class="money">Amount</th><th>Category</th><th></th></tr>
        </thead>
        <tbody>
          ${items.map((t) => html`
            <tr key=${t.id}>
              <td>${t.date}</td>
              <td>${t.payee}</td>
              <td>${(accounts.find((a) => a.id === t.account_id) || {}).name || t.account_id}</td>
              <td class="money ${t.amount_cents < 0 ? 'negative' : 'positive'}">${formatCents(t.amount_cents)}</td>
              <td>
                <select value=${t.category_id || ''} onChange=${(e) => recategorise(t, e.target.value)}>
                  <option value="">Uncategorised</option>
                  ${categories.map((c) => html`<option value=${c.id}>${c.name}</option>`)}
                </select>
              </td>
              <td><button onClick=${() => remove(t)}>Delete</button></td>
            </tr>
          `)}
        </tbody>
      </table>
    </div>
  `;
}

// ---------------------------------------------------------------------------
// Reports
// ---------------------------------------------------------------------------

function Sparkline({ points, format = (v) => String(v) }) {
  if (!points || points.length === 0) return html`<p class="muted">No data yet.</p>`;
  const values = points.map((p) => Number(p.value) || 0);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;
  const width = 320;
  const height = 60;
  const step = points.length > 1 ? width / (points.length - 1) : width;

  const coords = values.map((v, i) => `${(i * step).toFixed(1)},${(height - ((v - min) / span) * height).toFixed(1)}`);

  return html`
    <svg class="sparkline" viewBox="0 0 ${width} ${height}" role="img" aria-label="trend">
      <polyline points=${coords.join(' ')} fill="none" stroke="currentColor" stroke-width="2" />
      ${values.map((v, i) => html`
        <text x=${(i * step).toFixed(1)} y=${(height + 12)} font-size="8" text-anchor="middle">${format(v)}</text>
      `)}
    </svg>
  `;
}

function ReportsView() {
  const [networth, setNetworth] = useState(null);
  const [cashflow, setCashflow] = useState(null);
  const [spending, setSpending] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        setNetworth(await api.getNetworth(12));
        setCashflow(await api.getCashflow(12));
        setSpending(await api.getSpending());
      } catch (e) {
        setError(e.message);
      }
    })();
  }, []);

  if (error) return html`<div class="card negative">Error: ${error}</div>`;

  return html`
    <div class="card">
      <h2>Net worth</h2>
      ${networth
        ? html`
          <${Sparkline}
            points=${networth.series.map((s) => ({ label: s.month, value: s.net }))}
            format=${(v) => formatCents(v)}
          />
          <table class="table">
            <thead><tr><th>Month</th><th class="money">Net worth</th></tr></thead>
            <tbody>
              ${networth.series.map((s) => html`
                <tr><td>${s.month}</td><td class="money">${formatCents(s.net)}</td></tr>
              `)}
            </tbody>
          </table>
        `
        : html`<p class="muted">Loading...</p>`}
    </div>

    <div class="card">
      <h2>Cash flow</h2>
      ${cashflow
        ? html`
          <table class="table">
            <thead><tr><th>Month</th><th class="money">In</th><th class="money">Out</th><th class="money">Net</th></tr></thead>
            <tbody>
              ${cashflow.series.map((s) => html`
                <tr>
                  <td>${s.month}</td>
                  <td class="money positive">${formatCents(s.income)}</td>
                  <td class="money negative">${formatCents(s.expense)}</td>
                  <td class="money">${formatCents(s.net)}</td>
                </tr>
              `)}
            </tbody>
          </table>
        `
        : html`<p class="muted">Loading...</p>`}
    </div>

    <div class="card">
      <h2>Spending by category</h2>
      ${spending
        ? html`
          <p class="muted">Total: ${formatCents(spending.total)} for ${spending.month}</p>
          <table class="table">
            <thead><tr><th>Category</th><th class="money">Spent</th></tr></thead>
            <tbody>
              ${spending.categories.map((c) => html`
                <tr><td>${c.name}</td><td class="money">${formatCents(c.total)}</td></tr>
              `)}
            </tbody>
          </table>
        `
        : html`<p class="muted">Loading...</p>`}
    </div>
  `;
}

// ---------------------------------------------------------------------------
// Rules
// ---------------------------------------------------------------------------

const RULE_FIELDS = ['payee', 'memo', 'amount'];
const RULE_OPS = ['contains', 'equals', 'starts_with', 'ends_with', 'gt', 'lt'];

function RulesView({ data: bootstrap }) {
  const { rows: rules, reload } = useList(() => data.list('rules'), []);
  const [form, setForm] = useState({ priority: '0', field: 'payee', op: 'contains', value: '', set_category_id: '', enabled: true });
  const [message, setMessage] = useState(null);
  const categories = bootstrap.categories || [];

  const submit = async (event) => {
    event.preventDefault();
    if (!form.value) {
      setMessage({ kind: 'error', text: 'A rule needs a value to match.' });
      return;
    }
    await data.create('rules', {
      priority: Number(form.priority) || 0,
      field: form.field,
      op: form.op,
      value: form.value,
      set_category_id: form.set_category_id ? Number(form.set_category_id) : null,
      enabled: form.enabled ? 1 : 0,
    });
    setForm({ ...form, value: '' });
    setMessage({ kind: 'success', text: 'Rule added.' });
    await reload();
  };

  const toggle = async (rule) => {
    await data.update('rules', rule.id, { enabled: rule.enabled ? 0 : 1 });
    await reload();
  };

  const remove = async (rule) => {
    await data.remove('rules', rule.id);
    await reload();
  };

  const categoryName = (id) => (categories.find((c) => c.id === id) || {}).name || '—';

  return html`
    <div class="card">
      <h2>Rules</h2>
      <p class="muted">Rules categorise transactions automatically. The first matching rule wins, lowest priority number first.</p>
      ${message && html`<p class="${message.kind}">${message.text}</p>`}

      <form class="form" onSubmit=${submit}>
        <label>
          Priority
          <input type="number" value=${form.priority} onInput=${(e) => setForm({ ...form, priority: e.target.value })} />
        </label>
        <label>
          Field
          <select value=${form.field} onChange=${(e) => setForm({ ...form, field: e.target.value })}>
            ${RULE_FIELDS.map((f) => html`<option value=${f}>${f}</option>`)}
          </select>
        </label>
        <label>
          Match
          <select value=${form.op} onChange=${(e) => setForm({ ...form, op: e.target.value })}>
            ${RULE_OPS.map((o) => html`<option value=${o}>${o}</option>`)}
          </select>
        </label>
        <label>
          Value
          <input type="text" value=${form.value} onInput=${(e) => setForm({ ...form, value: e.target.value })} />
        </label>
        <label>
          Set category
          <select value=${form.set_category_id} onChange=${(e) => setForm({ ...form, set_category_id: e.target.value })}>
            <option value="">No opinion</option>
            ${categories.map((c) => html`<option value=${c.id}>${c.name}</option>`)}
          </select>
        </label>
        <button type="submit">Add rule</button>
      </form>

      <table class="table">
        <thead>
          <tr><th>Priority</th><th>Field</th><th>Match</th><th>Value</th><th>Category</th><th>Enabled</th><th></th></tr>
        </thead>
        <tbody>
          ${rules.map((rule) => html`
            <tr key=${rule.id}>
              <td>${rule.priority}</td>
              <td>${rule.field}</td>
              <td>${rule.op}</td>
              <td>${rule.value}</td>
              <td>${categoryName(rule.set_category_id)}</td>
              <td><button onClick=${() => toggle(rule)}>${rule.enabled ? 'Yes' : 'No'}</button></td>
              <td><button onClick=${() => remove(rule)}>Delete</button></td>
            </tr>
          `)}
        </tbody>
      </table>
    </div>
  `;
}

// ---------------------------------------------------------------------------
// Schedules
// ---------------------------------------------------------------------------

function SchedulesView({ data: bootstrap }) {
  const { rows: schedules, reload } = useList(() => data.list('schedules'), []);
  const [form, setForm] = useState({
    account_id: '', payee: '', amount: '', frequency: 'monthly', interval_n: '1',
    next_date: '', category_id: '', auto_post: false,
  });
  const [message, setMessage] = useState(null);
  const accounts = bootstrap.accounts || [];
  const categories = bootstrap.categories || [];

  const submit = async (event) => {
    event.preventDefault();
    if (!form.account_id || !form.next_date) {
      setMessage({ kind: 'error', text: 'An account and a next date are required.' });
      return;
    }
    await data.create('schedules', {
      account_id: Number(form.account_id),
      payee: form.payee,
      memo: '',
      amount_cents: strToCents(form.amount),
      category_id: form.category_id ? Number(form.category_id) : null,
      frequency: form.frequency,
      interval_n: Number(form.interval_n) || 1,
      next_date: form.next_date,
      auto_post: form.auto_post ? 1 : 0,
    });
    setForm({ ...form, payee: '', amount: '' });
    setMessage({ kind: 'success', text: 'Schedule added.' });
    await reload();
  };

  const remove = async (schedule) => {
    await data.remove('schedules', schedule.id);
    await reload();
  };

  return html`
    <div class="card">
      <h2>Schedules</h2>
      <p class="muted">Recurring transactions: rent, salary, subscriptions.</p>
      ${message && html`<p class="${message.kind}">${message.text}</p>`}

      <form class="form" onSubmit=${submit}>
        <label>
          Account
          <select value=${form.account_id} onChange=${(e) => setForm({ ...form, account_id: e.target.value })}>
            <option value="">Select an account</option>
            ${accounts.map((a) => html`<option value=${a.id}>${a.name}</option>`)}
          </select>
        </label>
        <label>
          Payee
          <input type="text" value=${form.payee} onInput=${(e) => setForm({ ...form, payee: e.target.value })} />
        </label>
        <label>
          Amount
          <input type="text" inputMode="decimal" value=${form.amount} onInput=${(e) => setForm({ ...form, amount: e.target.value })} />
        </label>
        <label>
          Frequency
          <select value=${form.frequency} onChange=${(e) => setForm({ ...form, frequency: e.target.value })}>
            ${['daily', 'weekly', 'monthly', 'yearly'].map((f) => html`<option value=${f}>${f}</option>`)}
          </select>
        </label>
        <label>
          Every
          <input type="number" min="1" value=${form.interval_n} onInput=${(e) => setForm({ ...form, interval_n: e.target.value })} />
        </label>
        <label>
          Next date
          <input type="date" value=${form.next_date} onInput=${(e) => setForm({ ...form, next_date: e.target.value })} />
        </label>
        <label>
          Category
          <select value=${form.category_id} onChange=${(e) => setForm({ ...form, category_id: e.target.value })}>
            <option value="">Uncategorised</option>
            ${categories.map((c) => html`<option value=${c.id}>${c.name}</option>`)}
          </select>
        </label>
        <button type="submit">Add schedule</button>
      </form>

      <table class="table">
        <thead>
          <tr><th>Payee</th><th>Account</th><th class="money">Amount</th><th>Frequency</th><th>Next date</th><th></th></tr>
        </thead>
        <tbody>
          ${schedules.map((s) => html`
            <tr key=${s.id}>
              <td>${s.payee}</td>
              <td>${(accounts.find((a) => a.id === s.account_id) || {}).name || s.account_id}</td>
              <td class="money">${formatCents(s.amount_cents)}</td>
              <td>${s.frequency}${s.interval_n > 1 ? ` x${s.interval_n}` : ''}</td>
              <td>${s.next_date}</td>
              <td><button onClick=${() => remove(s)}>Delete</button></td>
            </tr>
          `)}
        </tbody>
      </table>
    </div>
  `;
}

// ---------------------------------------------------------------------------
// Goals
// ---------------------------------------------------------------------------

function GoalsView({ data: bootstrap }) {
  const { rows: goals, reload } = useList(() => data.list('goals'), []);
  const [form, setForm] = useState({ category_id: '', target_cents: '', monthly_cents: '', target_date: '' });
  const [message, setMessage] = useState(null);
  const categories = bootstrap.categories || [];

  const submit = async (event) => {
    event.preventDefault();
    if (!form.category_id || !form.target_cents) {
      setMessage({ kind: 'error', text: 'A category and a target amount are required.' });
      return;
    }
    await data.create('goals', {
      category_id: Number(form.category_id),
      target_cents: strToCents(form.target_cents),
      monthly_cents: strToCents(form.monthly_cents),
      target_date: form.target_date || null,
    });
    setForm({ ...form, target_cents: '', monthly_cents: '', target_date: '' });
    setMessage({ kind: 'success', text: 'Goal added.' });
    await reload();
  };

  const remove = async (goal) => {
    await data.remove('goals', goal.id);
    await reload();
  };

  return html`
    <div class="card">
      <h2>Goals</h2>
      <p class="muted">A target amount for a category, with an optional monthly contribution.</p>
      ${message && html`<p class="${message.kind}">${message.text}</p>`}

      <form class="form" onSubmit=${submit}>
        <label>
          Category
          <select value=${form.category_id} onChange=${(e) => setForm({ ...form, category_id: e.target.value })}>
            <option value="">Select a category</option>
            ${categories.map((c) => html`<option value=${c.id}>${c.name}</option>`)}
          </select>
        </label>
        <label>
          Target
          <input type="text" inputMode="decimal" value=${form.target_cents} onInput=${(e) => setForm({ ...form, target_cents: e.target.value })} />
        </label>
        <label>
          Monthly
          <input type="text" inputMode="decimal" value=${form.monthly_cents} onInput=${(e) => setForm({ ...form, monthly_cents: e.target.value })} />
        </label>
        <label>
          Target date
          <input type="date" value=${form.target_date} onInput=${(e) => setForm({ ...form, target_date: e.target.value })} />
        </label>
        <button type="submit">Add goal</button>
      </form>

      <table class="table">
        <thead>
          <tr><th>Category</th><th class="money">Target</th><th class="money">Monthly</th><th>Target date</th><th></th></tr>
        </thead>
        <tbody>
          ${goals.map((goal) => html`
            <tr key=${goal.id}>
              <td>${(categories.find((c) => c.id === goal.category_id) || {}).name || goal.category_id}</td>
              <td class="money">${formatCents(goal.target_cents)}</td>
              <td class="money">${formatCents(goal.monthly_cents)}</td>
              <td>${goal.target_date || '—'}</td>
              <td><button onClick=${() => remove(goal)}>Delete</button></td>
            </tr>
          `)}
        </tbody>
      </table>
    </div>
  `;
}

// ---------------------------------------------------------------------------
// Import
// ---------------------------------------------------------------------------

function ImportView({ data: bootstrap }) {
  const accounts = bootstrap.accounts || [];
  const [accountId, setAccountId] = useState(accounts.length ? String(accounts[0].id) : '');
  const [csv, setCsv] = useState('');
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  const onFile = (event) => {
    const file = event.target.files && event.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => setCsv(String(reader.result || ''));
    reader.readAsText(file);
  };

  const run = async (dryRun) => {
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      setResult(await data.importCsv({ account_id: Number(accountId), csv, dry_run: dryRun }));
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  return html`
    <div class="card">
      <h2>Import a bank statement</h2>
      <p class="muted">
        Upload a CSV export. The columns are detected by name, rows that were already imported are
        skipped, and the rules decide the category.
      </p>
      ${error && html`<p class="negative">${error}</p>`}

      <div class="form">
        <label>
          Account
          <select value=${accountId} onChange=${(e) => setAccountId(e.target.value)}>
            ${accounts.map((a) => html`<option value=${a.id}>${a.name}</option>`)}
          </select>
        </label>
        <label>
          CSV file
          <input type="file" accept=".csv,text/csv" onChange=${onFile} />
        </label>
        <label>
          Or paste the CSV
          <textarea rows="6" value=${csv} onInput=${(e) => setCsv(e.target.value)}></textarea>
        </label>
        <button disabled=${busy || !csv} onClick=${() => run(true)}>Preview</button>
        <button disabled=${busy || !csv} onClick=${() => run(false)}>Import</button>
      </div>

      ${result && html`
        <table class="table">
          <thead>
            <tr><th>Rows found</th><th>Imported</th><th>Duplicates</th><th>Skipped</th></tr>
          </thead>
          <tbody>
            <tr>
              <td>${result.rows_found}</td>
              <td>${result.imported}</td>
              <td>${result.duplicates}</td>
              <td>${result.skipped.length}</td>
            </tr>
          </tbody>
        </table>
        ${result.skipped.length > 0 && html`
          <ul class="muted">
            ${result.skipped.map((s) => html`<li>Line ${s.line}: ${s.reason}</li>`)}
          </ul>
        `}
      `}
    </div>
  `;
}

// ---------------------------------------------------------------------------
// Application
// ---------------------------------------------------------------------------

const views = {
  budget: BudgetView,
  transactions: TransactionsView,
  accounts: AccountsView,
  reports: ReportsView,
  rules: RulesView,
  schedules: SchedulesView,
  goals: GoalsView,
  import: ImportView,
};

export function App() {
  const bootstrap = useBootstrap();
  const { status, refresh } = useSyncStatus();
  const [view, setView] = useState('budget');

  if (bootstrap.loading) return html`<div class="card">Loading budget...</div>`;
  if (bootstrap.error) {
    return html`
      <div class="card negative">
        Error: ${bootstrap.error}
        <p>The server is unreachable. The local mirror is still available.</p>
      </div>
    `;
  }

  const View = views[view] || BudgetView;

  return html`
    <div class="app">
      <header class="header">
        <div class="header__brand">Actual Budget</div>
        <${Nav} view=${view} setView=${setView} />
        <${SyncBadge} status=${status} refresh=${refresh} />
      </header>
      <main class="main">
        <${View} data=${bootstrap.data} />
      </main>
    </div>
  `;
}

if (typeof document !== 'undefined') {
  ReactDOM.createRoot(document.getElementById('root')).render(html`<${App} />`);
}
