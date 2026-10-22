const API_BASE = '';

async function request(path, { method = 'GET', body, headers = {} } = {}) {
  const res = await fetch(API_BASE + path, {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...headers,
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    let message = res.statusText;
    try { const err = await res.json(); message = err.message || err.error || message; } catch {}
    throw new Error(message || `request failed: ${res.status}`);
  }
  const data = await res.json();
  return data.data ?? data;
}

export const api = {
  // Generic access, used by the data layer for the plain entities.
  get: (path) => request(path.startsWith('/api/') ? path : `/api/${path}`),
  post: (path, body) => request(path.startsWith('/api/') ? path : `/api/${path}`, { method: 'POST', body }),
  patch: (path, body) => request(path.startsWith('/api/') ? path : `/api/${path}`, { method: 'PATCH', body }),
  del: (path) => request(path.startsWith('/api/') ? path : `/api/${path}`, { method: 'DELETE' }),

  getHealth: () => request('/api/health'),
  bootstrap: (params) => request(`/api/bootstrap${params ? `?${params}` : ''}`),
  getBudget: (month) => request(`/api/budget/${month}`),
  setBudget: (month, categoryId, budgetedCents) => request(`/api/budget/${month}/${categoryId}`, { method: 'PUT', body: { budgeted_cents: budgetedCents } }),
  getTransactions: (q) => request(`/api/transactions${q ? `?${q}` : ''}`),
  getAccounts: () => request('/api/reports/accounts'),
  getNetworth: (months = 12) => request(`/api/reports/networth?months=${months}`),
  getCashflow: (months = 12) => request(`/api/reports/cashflow?months=${months}`),
  getSpending: (month) => request(`/api/reports/spending?month=${month}`),
  getCategories: () => request('/api/categories'),
  getGroups: () => request('/api/category_groups'),
  getRules: () => request('/api/rules'),
  getSchedules: () => request('/api/schedules'),
  getGoals: () => request('/api/goals'),
  postAccount: (body) => request('/api/accounts', { method: 'POST', body }),
  postTransaction: (body) => request('/api/transactions', { method: 'POST', body }),
  postSchedule: (body) => request('/api/schedules', { method: 'POST', body }),
  postRule: (body) => request('/api/rules', { method: 'POST', body }),
  postGoal: (body) => request('/api/goals', { method: 'POST', body }),
  postCategory: (body) => request('/api/categories', { method: 'POST', body }),
  postGroup: (body) => request('/api/category_groups', { method: 'POST', body }),
  importCsv: (body) => request('/api/import/csv', { method: 'POST', body }),
  patchTransaction: (id, body) => request(`/api/transactions/${id}`, { method: 'PATCH', body }),
  deleteTransaction: (id) => request(`/api/transactions/${id}`, { method: 'DELETE' }),
  getSyncPull: (since) => request(`/api/sync/pull?since=${encodeURIComponent(since)}`),
  postSyncPush: (changes) => request('/api/sync/push', { method: 'POST', body: { changes } }),
  getSyncStatus: () => request('/api/sync/status'),
};
