/**
 * Money is stored and passed around as integer cents, never as a float.
 *
 * The only places a decimal ever exists are (a) this module parsing user input
 * and (b) the client formatting for display. Everything between is integers.
 */

/** Pad a fraction string to at least three digits so rounding is defined. */
function padFraction(fraction) {
  return (fraction + '000').slice(0, 3);
}

/**
 * Parse a user-facing amount into integer cents.
 *
 *   "12.34"     -> 1234
 *   "-5"        -> -500
 *   "$1,234.5"  -> 123450
 *   "1.005"     -> 101   (half-up on the third decimal)
 */
export function parseCents(input) {
  if (typeof input === 'number') {
    if (!Number.isFinite(input)) throw new TypeError('amount must be a finite number');
    return Math.round(input);
  }
  if (typeof input === 'bigint') return Number(input);
  if (typeof input !== 'string') {
    throw new TypeError('amount must be a string, a number or a bigint');
  }

  const cleaned = input.trim().replace(/[$,\s\u00a0]/g, '');
  if (cleaned === '' || cleaned === '-' || cleaned === '+' || cleaned === '.') {
    throw new TypeError(`not an amount: "${input}"`);
  }
  if (!/^[+-]?(\d+(\.\d*)?|\.\d+)$/.test(cleaned)) {
    throw new TypeError(`not an amount: "${input}"`);
  }

  const negative = cleaned.startsWith('-');
  const body = cleaned.replace(/^[+-]/, '');
  const [whole = '0', fraction = ''] = body.split('.');
  const padded = padFraction(fraction);

  let cents = Number(whole || '0') * 100 + Number(padded.slice(0, 2));
  if (Number(padded[2]) >= 5) cents += 1;

  return negative ? -cents : cents;
}

/** Format integer cents as a plain decimal string: -1234 -> "-12.34". */
export function formatCents(cents) {
  const n = Math.trunc(Number(cents) || 0);
  const sign = n < 0 ? '-' : '';
  const abs = Math.abs(n);
  return `${sign}${Math.floor(abs / 100)}.${String(abs % 100).padStart(2, '0')}`;
}

/**
 * Format cents for display with the user's currency and locale.
 * Falls back to a plain decimal when Intl has no data for the locale.
 */
export function formatMoney(cents, { currency = 'USD', locale = 'en-US', showPlus = false } = {}) {
  const value = (Math.trunc(Number(cents) || 0)) / 100;
  try {
    return new Intl.NumberFormat(locale, {
      style: 'currency',
      currency,
      signDisplay: showPlus ? 'exceptZero' : 'auto',
    }).format(value);
  } catch {
    return `${value < 0 ? '-' : showPlus && value > 0 ? '+' : ''}$${Math.abs(value).toFixed(2)}`;
  }
}

/** Sum a list of cent values without ever touching a float. */
export function sumCents(values) {
  let total = 0;
  for (const v of values) total += Number(v) || 0;
  return total;
}
