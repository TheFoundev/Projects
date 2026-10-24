/**
 * The rule engine: match a transaction's payee / memo / amount and decide which
 * category it belongs to.
 *
 * This module is intentionally pure. `applyRules(rules, tx)` called twice with
 * the same arguments returns the same answer and touches nothing.
 */

import { parseCents } from '../money.js';

export const RULE_FIELDS = ['payee', 'memo', 'amount'];
export const RULE_OPS = ['contains', 'equals', 'starts_with', 'ends_with', 'gt', 'lt'];

const TEXT_OPS = ['contains', 'equals', 'starts_with', 'ends_with'];
const AMOUNT_OPS = ['gt', 'lt', 'equals'];

/** Rules that should run, in order: lowest priority first, then lowest id. */
export function sortRules(rules) {
  return rules
    .filter((r) => !r.deleted && r.enabled !== 0 && r.enabled !== false)
    .slice()
    .sort((a, b) => (a.priority - b.priority) || (a.id - b.id));
}

/** Does a single rule match a transaction? Never throws on bad input. */
export function ruleMatches(rule, tx) {
  if (!rule || rule.deleted || rule.enabled === 0 || rule.enabled === false) return false;

  if (rule.field === 'amount') {
    if (!AMOUNT_OPS.includes(rule.op)) return false;
    let target;
    try {
      target = parseCents(String(rule.value));
    } catch {
      return false;
    }
    const amount = Number(tx.amount_cents) || 0;
    if (rule.op === 'gt') return amount > target;
    if (rule.op === 'lt') return amount < target;
    return amount === target;
  }

  if (!TEXT_OPS.includes(rule.op)) return false;
  const haystack = String(tx[rule.field] ?? '').toLowerCase();
  const needle = String(rule.value ?? '').toLowerCase();
  if (needle === '') return false;

  switch (rule.op) {
    case 'contains': return haystack.includes(needle);
    case 'equals': return haystack === needle;
    case 'starts_with': return haystack.startsWith(needle);
    case 'ends_with': return haystack.endsWith(needle);
    default: return false;
  }
}

/**
 * The category the first matching rule assigns, or null when nothing matches.
 * `set_category_id` of null is treated as "no opinion" rather than a match.
 */
export function applyRules(rules, tx) {
  for (const rule of sortRules(rules)) {
    if (ruleMatches(rule, tx) && rule.set_category_id != null) {
      return rule.set_category_id;
    }
  }
  return null;
}

/** Which rule wins, for the UI's explanation. */
export function firstMatchingRule(rules, tx) {
  return sortRules(rules).find((rule) => ruleMatches(rule, tx)) ?? null;
}
