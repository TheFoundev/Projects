/** Request-field coercion. Every failure is a 400 with a useful message. */

import { badRequest, isTruthy } from '../util.js';
import { parseCents } from '../money.js';

export function asString(value, { field, max = 500, required = false, allowEmpty = true } = {}) {
  if (value === undefined || value === null) {
    if (required) throw badRequest(`"${field}" is required`);
    return '';
  }
  if (typeof value !== 'string') throw badRequest(`"${field}" must be a string`);
  const trimmed = value.trim();
  if (!allowEmpty && trimmed === '') throw badRequest(`"${field}" must not be empty`);
  if (trimmed.length > max) throw badRequest(`"${field}" must be at most ${max} characters`);
  return trimmed;
}

export function asInt(value, {
  field,
  min = -Number.MAX_SAFE_INTEGER,
  max = Number.MAX_SAFE_INTEGER,
  defaultValue = 0,
  nullable = false,
  required = false,
} = {}) {
  if (value === undefined || value === null || value === '') {
    if (nullable) return null;
    if (required) throw badRequest(`"${field}" is required`);
    return defaultValue;
  }
  const n = typeof value === 'number' ? value : Number(String(value).trim());
  if (!Number.isFinite(n)) throw badRequest(`"${field}" must be a number`);
  const i = Math.trunc(n);
  if (i < min || i > max) throw badRequest(`"${field}" must be between ${min} and ${max}`);
  return i;
}

export function asBool(value, { field, defaultValue = 0 } = {}) {
  if (value === undefined || value === null) return defaultValue;
  if (typeof value === 'boolean') return value ? 1 : 0;
  if (typeof value === 'number') return value !== 0 ? 1 : 0;
  if (typeof value !== 'string') throw badRequest(`"${field}" must be a boolean`);
  return isTruthy(value) ? 1 : 0;
}

export function asEnum(value, values, { field, defaultValue, required = false } = {}) {
  if (value === undefined || value === null || value === '') {
    if (defaultValue !== undefined) return defaultValue;
    if (required) throw badRequest(`"${field}" is required`);
    return null;
  }
  const v = String(value);
  if (!values.includes(v)) {
    throw badRequest(`"${field}" must be one of: ${values.join(', ')}`, { allowed: values });
  }
  return v;
}

export function asDate(value, { field, required = false, nullable = false } = {}) {
  if (value === undefined || value === null || value === '') {
    if (nullable) return null;
    if (required) throw badRequest(`"${field}" is required`);
    return null;
  }
  const v = String(value).slice(0, 10);
  if (!/^\d{4}-\d{2}-\d{2}$/.test(v)) throw badRequest(`"${field}" must be a date as YYYY-MM-DD`);
  return v;
}

export function asMonth(value, { field, required = false } = {}) {
  if (value === undefined || value === null || value === '') {
    if (required) throw badRequest(`"${field}" is required`);
    return null;
  }
  const v = String(value).slice(0, 7);
  if (!/^\d{4}-\d{2}$/.test(v)) throw badRequest(`"${field}" must be a month as YYYY-MM`);
  return v;
}

export function asCents(value, { field, nullable = false, defaultValue = 0 } = {}) {
  if (value === undefined || value === null || value === '') {
    if (nullable) return null;
    return defaultValue;
  }
  try {
    return parseCents(value);
  } catch (error) {
    throw badRequest(`"${field}" ${error.message}`);
  }
}
