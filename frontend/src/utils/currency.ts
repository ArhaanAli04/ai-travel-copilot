// ─────────────────────────────────────────────────────────────────────────────
// Currency utility — single source of truth for formatting across the app
// ─────────────────────────────────────────────────────────────────────────────

export const CURRENCY_SYMBOLS: Record<string, string> = {
  USD: '$',
  EUR: '€',
  GBP: '£',
  INR: '₹',
  JPY: '¥',
  AUD: 'A$',
  CAD: 'C$',
  SGD: 'S$',
  AED: 'AED',
  THB: '฿',
};

export const getCurrencySymbol = (currency: string): string => {
  return CURRENCY_SYMBOLS[currency?.toUpperCase()] ?? currency ?? '$';
};

export const formatCurrency = (
  amount: number | undefined | null,
  currency: string,
  options: { decimals?: number; showCode?: boolean } = {}
): string => {
  if (amount === undefined || amount === null) return '—';
  const { decimals = 2, showCode = false } = options;
  const symbol = getCurrencySymbol(currency);
  const formatted = amount.toLocaleString('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
  return showCode
    ? `${symbol}${formatted} ${currency}`
    : `${symbol}${formatted}`;
};
