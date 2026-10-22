const currencyFormatter = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 2, maximumFractionDigits: 2 });

export function formatCents(cents) {
  const value = (Number(cents) || 0) / 100;
  return currencyFormatter.format(value);
}

export function centsToStr(cents) {
  const n = Math.trunc(Number(cents) || 0);
  const sign = n < 0 ? '-' : '';
  const abs = Math.abs(n);
  return `${sign}${Math.floor(abs / 100)}.${String(abs % 100).padStart(2, '0')}`;
}

export function strToCents(str) {
  if (!str) return 0;
  const cleaned = str.trim().replace(/[$,\s]/g, '');
  if (cleaned === '' || cleaned === '-' || cleaned === '+') return 0;
  const neg = cleaned.startsWith('-');
  const body = cleaned.replace(/^[+-]/, '');
  const [whole = '0', frac = ''] = body.split('.');
  let c = Number(whole) * 100 + Number((frac + '00').slice(0, 2));
  if (neg) c = -c;
  return Math.round(c);
}
