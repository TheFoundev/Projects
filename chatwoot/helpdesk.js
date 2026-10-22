'use strict';
/**
 * The helpdesk domain.
 *
 * The rules that make a conversation a support conversation: the states it
 * can be in, the transitions between them, the priority levels, the reply
 * types and the way a conversation is routed to an agent.
 *
 * Pure functions, no database access, so the rules can be unit tested on
 * their own.
 */

/** The states a conversation can be in. */
const STATUSES = ['open', 'pending', 'closed'];

/** The priority levels, from calmest to loudest. */
const PRIORITIES = ['low', 'normal', 'high', 'urgent'];

/** The kinds of message that can be added to a conversation. */
const DIRECTIONS = ['inbound', 'outbound', 'note'];

/**
 * The transitions that are allowed.
 *
 * A closed conversation can be reopened, everything else can move to any
 * other state.
 */
const TRANSITIONS = {
  open: ['open', 'pending', 'closed'],
  pending: ['open', 'pending', 'closed'],
  closed: ['open', 'closed'],
};

/** True when the status is one the app knows. */
function isValidStatus(status) {
  return STATUSES.includes(String(status));
}

/** True when the priority is one the app knows. */
function isValidPriority(priority) {
  return PRIORITIES.includes(String(priority));
}

/** True when the direction is one the app knows. */
function isValidDirection(direction) {
  return DIRECTIONS.includes(String(direction));
}

/** True when a conversation may move from one status to another. */
function canTransition(from, to) {
  const allowed = TRANSITIONS[String(from)];
  if (!allowed) return false;
  return allowed.includes(String(to));
}

/** The error message for an illegal transition, or null when it is fine. */
function transitionError(from, to) {
  if (!isValidStatus(to)) return `"${to}" is not a status.`;
  if (!canTransition(from, to)) return `A conversation cannot go from "${from}" to "${to}".`;
  return null;
}

/**
 * The thread of a conversation.
 *
 * The replies are in the order they arrived. Internal notes are kept, but
 * they are marked: the requester must never see them.
 */
function buildThread(conversation, messages) {
  const replies = (messages || [])
    .filter((message) => Number(message.conversation_id) === Number(conversation.id))
    .slice()
    .sort((a, b) => Number(a.id) - Number(b.id))
    .map((message) => ({
      id: message.id,
      body: message.body,
      sender: message.sender,
      direction: message.direction,
      internal: message.direction === 'note',
      created_at: message.created_at,
    }));

  const visible = replies.filter((reply) => !reply.internal);
  const lastReply = replies.length ? replies[replies.length - 1] : null;
  const lastVisible = visible.length ? visible[visible.length - 1] : null;

  return {
    conversation,
    replies,
    reply_count: replies.length,
    public_reply_count: visible.length,
    internal_note_count: replies.length - visible.length,
    last_reply_at: lastReply ? lastReply.created_at : null,
    waiting_since: lastVisible ? lastVisible.created_at : conversation.created_at,
  };
}

/**
 * The shared inbox.
 *
 * The conversations are grouped by state, with the counters a support team
 * looks at first: how many are waiting, how many have nobody on them.
 */
function summariseInbox(conversations, filters = {}) {
  const status = filters.status ? String(filters.status) : null;
  const priority = filters.priority ? String(filters.priority) : null;
  const assignee = filters.assignee !== undefined && filters.assignee !== null ? String(filters.assignee) : null;
  const query = filters.q ? String(filters.q).toLowerCase() : null;

  const items = (conversations || []).filter((conversation) => {
    if (status && conversation.status !== status) return false;
    if (priority && conversation.priority !== priority) return false;
    if (assignee !== null && String(conversation.assignee || '') !== assignee) return false;
    if (query) {
      const haystack = `${conversation.subject || ''} ${conversation.requester || ''} ${conversation.email || ''}`.toLowerCase();
      if (!haystack.includes(query)) return false;
    }
    return true;
  });

  const counts = { open: 0, pending: 0, closed: 0 };
  let unassigned = 0;
  for (const conversation of items) {
    if (counts[conversation.status] !== undefined) counts[conversation.status] += 1;
    if (!conversation.assignee) unassigned += 1;
  }

  const sorted = items.slice().sort((a, b) => {
    const weight = (conversation) => PRIORITIES.indexOf(conversation.priority || 'normal');
    if (weight(a) !== weight(b)) return weight(b) - weight(a);
    return Number(b.id) - Number(a.id);
  });

  return { items: sorted, counts, total: items.length, unassigned };
}

/**
 * The agent a new conversation should go to.
 *
 * The agent with the fewest open conversations wins, so the work is spread
 * out. When nothing is open yet the first agent is used.
 */
function chooseAssignee(conversations, agents) {
  if (!agents || agents.length === 0) return '';
  const load = new Map(agents.map((agent) => [agent, 0]));
  for (const conversation of conversations || []) {
    const name = conversation.assignee;
    if (name && load.has(name)) load.set(name, load.get(name) + 1);
  }
  let best = agents[0];
  let bestLoad = load.get(best);
  for (const agent of agents) {
    const current = load.get(agent);
    if (current < bestLoad) {
      best = agent;
      bestLoad = current;
    }
  }
  return best;
}

/**
 * The canned responses that match a query.
 *
 * The title and the body are searched, case insensitively. The best matches
 * come first: a title that starts with the query beats one that only
 * contains it.
 */
function searchCannedResponses(responses, query) {
  const needle = String(query || '').trim().toLowerCase();
  const list = (responses || []).slice();
  if (!needle) return list;

  const scored = [];
  for (const response of list) {
    const title = String(response.title || '').toLowerCase();
    const body = String(response.body || '').toLowerCase();
    const category = String(response.category || '').toLowerCase();

    let score = 0;
    if (title === needle) score = 100;
    else if (title.startsWith(needle)) score = 80;
    else if (title.includes(needle)) score = 60;
    else if (category.includes(needle)) score = 40;
    else if (body.includes(needle)) score = 20;

    if (score > 0) scored.push({ response, score });
  }

  scored.sort((a, b) => b.score - a.score || String(a.response.title).localeCompare(String(b.response.title)));
  return scored.map((entry) => entry.response);
}

/** The event that is written to the conversation history. */
function buildEvent(conversationId, type, detail, actor) {
  return {
    conversation_id: Number(conversationId),
    type,
    detail: detail || '',
    actor: actor || '',
    created_at: new Date().toISOString(),
  };
}

module.exports = {
  STATUSES,
  PRIORITIES,
  DIRECTIONS,
  TRANSITIONS,
  isValidStatus,
  isValidPriority,
  isValidDirection,
  canTransition,
  transitionError,
  buildThread,
  summariseInbox,
  chooseAssignee,
  searchCannedResponses,
  buildEvent,
};
