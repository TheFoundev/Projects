'use strict';

const app = document.getElementById('app');
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const state = { id: null, session: null, participant: null, source: null, timer: null };

function toast(message) {
  const node = document.getElementById('toast');
  node.textContent = message;
  node.classList.add('show');
  clearTimeout(node._timer);
  node._timer = setTimeout(() => node.classList.remove('show'), 3000);
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
    body: options.body ? JSON.stringify(options.body) : undefined,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || `Request failed (${response.status})`);
  return data;
}

function currentId() {
  return location.hash.replace(/^#\/?/, '') || null;
}

function storeName() { return localStorage.getItem('td.name') || ''; }

/* ---------------------------------------------------------------- */
/* Landing                                                           */
/* ---------------------------------------------------------------- */
function renderLanding() {
  if (state.source) { state.source.close(); state.source = null; }
  state.session = null;
  app.innerHTML = `
    <section class="hero">
      <div>
        <p class="eyebrow">Agile collaboration</p>
        <h1>Decide together,<br>without the meeting maze.</h1>
        <p class="lede">Planning poker, retrospectives and standups in a shared room. No accounts, no installs: create a room and share the link.</p>
      </div>
      <div class="card create">
        <h2>Start a session</h2>
        <form id="create-form">
          <label for="session-name">Session name</label>
          <input id="session-name" name="name" placeholder="Sprint 24 planning" required>
          <label for="mode">Format</label>
          <select id="mode" name="mode">
            <option value="planning">Planning poker</option>
            <option value="retro">Retrospective</option>
            <option value="standup">Daily standup</option>
          </select>
          <label for="your-name">Your name</label>
          <input id="your-name" name="person" value="${esc(storeName())}" placeholder="Alex" required>
          <button class="btn primary" type="submit">Create room</button>
        </form>
      </div>
    </section>
    <section class="card join-card">
      <div>
        <h2>Join an existing room</h2>
        <p class="muted">Paste the room code or open the link a teammate shared.</p>
      </div>
      <form id="join-form" class="row">
        <input name="id" placeholder="Room code" aria-label="Room code" required>
        <input name="person" placeholder="Your name" aria-label="Your name" value="${esc(storeName())}" required>
        <button class="btn" type="submit">Join</button>
      </form>
    </section>
    <section class="grid three">
      <article class="card"><h3>Planning poker</h3><p class="muted">Estimate stories with Fibonacci cards, reveal votes together and keep a decision log.</p></article>
      <article class="card"><h3>Retrospectives</h3><p class="muted">Went well, improve, actions. Everyone writes before the discussion starts.</p></article>
      <article class="card"><h3>Standups</h3><p class="muted">Yesterday, today, blockers. Written updates that respect focus time.</p></article>
    </section>`;

  document.getElementById('create-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    const form = new FormData(event.target);
    const person = String(form.get('person')).trim();
    try {
      const session = await api('/api/sessions', { method: 'POST', body: { name: form.get('name'), mode: form.get('mode') } });
      localStorage.setItem('td.name', person);
      await join(session.id, person);
      location.hash = `#/${session.id}`;
      await loadSession();
    } catch (err) { toast(err.message); }
  });

  document.getElementById('join-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    const form = new FormData(event.target);
    const id = String(form.get('id')).trim().replace(/^#\/?/, '');
    const person = String(form.get('person')).trim();
    try {
      localStorage.setItem('td.name', person);
      await join(id, person);
      location.hash = `#/${id}`;
      await loadSession();
    } catch (err) { toast(err.message); }
  });
}

async function join(id, name) {
  const participant = await api(`/api/sessions/${id}/join`, { method: 'POST', body: { name } });
  state.participant = participant;
  localStorage.setItem(`td.participant.${id}`, JSON.stringify(participant));
}

/* ---------------------------------------------------------------- */
/* Session                                                           */
/* ---------------------------------------------------------------- */
async function loadSession() {
  const id = currentId();
  if (!id) return renderLanding();
  state.id = id;
  try {
    state.session = await api(`/api/sessions/${id}`);
  } catch (err) {
    app.innerHTML = `<div class="card empty"><h1>Room not found</h1><p>${esc(err.message)}</p><a class="btn primary" href="/">Back home</a></div>`;
    return;
  }
  const saved = localStorage.getItem(`td.participant.${id}`);
  state.participant = saved ? JSON.parse(saved) : null;
  if (!state.participant || !state.session.participants.some((p) => p.id === state.participant.id)) {
    return renderJoinGate();
  }
  renderSession();
  subscribe();
}

function renderJoinGate() {
  app.innerHTML = `
    <section class="card create gate">
      <h1>${esc(state.session.name)}</h1>
      <p class="muted">Join this ${esc(state.session.mode)} room to take part.</p>
      <form id="gate-form">
        <label for="gate-name">Your name</label>
        <input id="gate-name" name="person" value="${esc(storeName())}" required placeholder="Alex">
        <button class="btn primary" type="submit">Join room</button>
      </form>
    </section>`;
  document.getElementById('gate-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    const person = String(new FormData(event.target).get('person')).trim();
    try {
      localStorage.setItem('td.name', person);
      await join(state.id, person);
      renderSession();
      subscribe();
    } catch (err) { toast(err.message); }
  });
}

function subscribe() {
  if (state.source) state.source.close();
  state.source = new EventSource(`/api/sessions/${state.id}/events`);
  state.source.addEventListener('change', () => {
    clearTimeout(state.timer);
    state.timer = setTimeout(async () => {
      try {
        state.session = await api(`/api/sessions/${state.id}`);
        renderSession();
      } catch (_err) { /* transient */ }
    }, 120);
  });
}

function participantName(id) {
  const found = state.session.participants.find((p) => p.id === id);
  return found ? found.name : 'Someone';
}

function activeStory() {
  return state.session.stories[state.session.stories.length - 1] || null;
}

function renderSession() {
  const session = state.session;
  const active = activeStory();
  const modeLabel = { planning: 'Planning poker', retro: 'Retrospective', standup: 'Daily standup' }[session.mode] || session.mode;
  const voteDisplay = (story) => {
    if (!story || !story.revealed) return '';
    const values = Object.values(story.votes).map(Number).filter((n) => !Number.isNaN(n));
    if (!values.length) return '';
    const avg = values.reduce((a, b) => a + b, 0) / values.length;
    return `<span class="badge">avg ${avg.toFixed(1)}</span>`;
  };

  const participants = session.participants.map((p) => {
    const voted = active && active.votes[p.id] !== undefined;
    const shown = active && active.revealed ? (active.votes[p.id] || '–') : (voted ? '✓' : '–');
    return `<span class="chip ${voted ? 'voted' : ''}">${esc(p.name)}${p.id === state.participant.id ? ' (you)' : ''}<b>${esc(shown)}</b></span>`;
  }).join('');

  const storyList = session.stories.slice().reverse().map((story) => `
    <li class="story ${active && story.id === active.id ? 'active' : ''}">
      <div><strong>${esc(story.title)}</strong><div class="muted small">${Object.keys(story.votes).length} votes ${story.revealed ? '· revealed' : ''}</div></div>
      ${voteDisplay(story)}
    </li>`).join('') || '<li class="muted">No stories yet. Add the first one below.</li>';

  let body = '';
  if (session.mode === 'planning') {
    const votedAlready = active && active.votes[state.participant.id] !== undefined;
    body = `
      <section class="grid two board">
        <div class="card">
          <div class="row between"><h2>Stories</h2><span class="badge">${session.stories.length}</span></div>
          <ul class="stories">${storyList}</ul>
          <form id="story-form" class="row tight">
            <input name="title" placeholder="Add a story to estimate…" required>
            <button class="btn" type="submit">Add</button>
          </form>
        </div>
        <div class="card">
          <h2>${active ? esc(active.title) : 'Waiting for a story'}</h2>
          <p class="muted small">${active ? (active.revealed ? 'Votes revealed. Discuss outliers, then reset for the next round.' : 'Pick your estimate. Votes stay hidden until the reveal.') : 'Add a story to start estimating.'}</p>
          <div class="cards">
            ${['0','1','2','3','5','8','13','21','?'].map((value) =>
              `<button class="vote ${active && active.votes[state.participant.id] === value ? 'selected' : ''}" data-value="${value}" ${!active || active.revealed ? 'disabled' : ''}>${value}</button>`).join('')}
          </div>
          <div class="row gap" style="margin-top:14px">
            <button id="reveal" class="btn primary" ${!active || active.revealed ? 'disabled' : ''}>Reveal votes</button>
            <button id="reset" class="btn" ${!active ? 'disabled' : ''}>Reset round</button>
          </div>
          ${active && active.revealed ? `<div class="reveal-list">${Object.entries(active.votes).map(([pid, value]) => `<div><span>${esc(participantName(pid))}</span><b>${esc(value)}</b></div>`).join('')}</div>` : ''}
        </div>
      </section>`;
  } else {
    const columns = session.mode === 'retro'
      ? [['went-well', 'Went well'], ['improve', 'Improve'], ['actions', 'Actions']]
      : [['yesterday', 'Yesterday'], ['today', 'Today'], ['blockers', 'Blockers']];
    body = `<section class="grid three notes">${columns.map(([key, label]) => `
      <div class="card column">
        <div class="row between"><h2>${label}</h2><span class="badge">${session.notes.filter((n) => n.column === key).length}</span></div>
        <div class="note-list">${session.notes.filter((n) => n.column === key).map((n) =>
          `<div class="note"><p>${esc(n.body)}</p><span>${esc(n.author || 'Anonymous')}</span></div>`).join('') || '<p class="muted small">Nothing yet.</p>'}</div>
        <form class="note-form" data-column="${key}">
          <textarea name="body" rows="2" placeholder="Add a note…" required></textarea>
          <button class="btn small" type="submit">Add note</button>
        </form>
      </div>`).join('')}</section>`;
  }

  app.innerHTML = `
    <section class="room-head">
      <div>
        <p class="eyebrow">${esc(modeLabel)}</p>
        <h1>${esc(session.name)}</h1>
        <div class="muted small">Room code <button class="code" id="copy-code">${esc(session.id)}</button></div>
      </div>
      <div class="participants">${participants}</div>
    </section>
    ${body}`;

  document.getElementById('copy-code').addEventListener('click', async () => {
    try { await navigator.clipboard.writeText(location.href); toast('Room link copied'); }
    catch { toast(location.href); }
  });

  const storyForm = document.getElementById('story-form');
  if (storyForm) storyForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    try {
      await api(`/api/sessions/${state.id}/stories`, { method: 'POST', body: { title: new FormData(storyForm).get('title') } });
      storyForm.reset();
      await refresh();
    } catch (err) { toast(err.message); }
  });

  document.querySelectorAll('.vote').forEach((button) => button.addEventListener('click', async () => {
    try {
      await api(`/api/sessions/${state.id}/vote`, { method: 'POST', body: { story_id: active.id, participant_id: state.participant.id, value: button.dataset.value } });
      await refresh();
    } catch (err) { toast(err.message); }
  }));

  const reveal = document.getElementById('reveal');
  if (reveal) reveal.addEventListener('click', async () => {
    try {
      await api(`/api/sessions/${state.id}/reveal`, { method: 'POST', body: { story_id: active.id } });
      await refresh();
    } catch (err) { toast(err.message); }
  });

  const reset = document.getElementById('reset');
  if (reset) reset.addEventListener('click', async () => {
    try {
      await api(`/api/sessions/${state.id}/reset`, { method: 'POST', body: { story_id: active.id } });
      await refresh();
    } catch (err) { toast(err.message); }
  });

  document.querySelectorAll('.note-form').forEach((form) => form.addEventListener('submit', async (event) => {
    event.preventDefault();
    try {
      await api(`/api/sessions/${state.id}/notes`, { method: 'POST', body: {
        column: form.dataset.column, body: new FormData(form).get('body'), author: state.participant.name } });
      form.reset();
      await refresh();
    } catch (err) { toast(err.message); }
  }));
}

async function refresh() {
  state.session = await api(`/api/sessions/${state.id}`);
  renderSession();
}

window.addEventListener('hashchange', loadSession);
if (currentId()) loadSession(); else renderLanding();
