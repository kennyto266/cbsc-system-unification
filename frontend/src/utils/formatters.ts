/**
 * Formatting utilities for displaying data
 */

// Format currency value with appropriate symbol and decimals
export const formatCurrency = (
  value: number,
  currency: string = '¥',
  decimals: number = 2
): string => {
  return `${currency}${value.toFixed(decimals).replace(/\B(?=(\d{3})+(?!\d))/g, ',')}`;
};

// Format percentage value
export const formatPercentage = (
  value: number,
  decimals: number = 2
): string => {
  return `${(value * 100).toFixed(decimals)}%`;
};

// Format large number with appropriate unit
export const formatLargeNumber = (value: number): string => {
  if (value >= 1e9) {
    return `${(value / 1e9).toFixed(1)}B`;
  }
  if (value >= 1e6) {
    return `${(value / 1e6).toFixed(1)}M`;
  }
  if (value >= 1e3) {
    return `${(value / 1e3).toFixed(1)}K`;
  }
  return value.toFixed(0);
};

// Format date/time based on locale
export const formatDateTime = (
  date: string | Date,
  format: 'date' | 'time' | 'datetime' = 'datetime'
): string => {
  const d = new Date(date);
  const options: Intl.DateTimeFormatOptions = {};

  switch (format) {
    case 'date':
      options.year = 'numeric';
      options.month = '2-digit';
      options.day = '2-digit';
      break;
    case 'time':
      options.hour = '2-digit';
      options.minute = '2-digit';
      options.second = '2-digit';
      break;
    case 'datetime':
      options.year = 'numeric';
      options.month = '2-digit';
      options.day = '2-digit';
      options.hour = '2-digit';
      options.minute = '2-digit';
      break;
  }

  return d.toLocaleString('zh-CN', options);
};

// Format relative time (e.g., "2 hours ago")
export const formatRelativeTime = (date: string | Date): string => {
  const d = new Date(date);
  const now = new Date();
  const diff = now.getTime() - d.getTime();
  const seconds = Math.floor(diff / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (days > 7) {
    return formatDateTime(date, 'date');
  }
  if (days > 0) {
    return `${days}天前`;
  }
  if (hours > 0) {
    return `${hours}小时前`;
  }
  if (minutes > 0) {
    return `${minutes}分钟前`;
  }
  return '刚刚';
};

// Format trading volume
export const formatVolume = (volume: number): string => {
  if (volume >= 1e8) {
    return `${(volume / 1e8).toFixed(2)}亿`;
  }
  if (volume >= 1e4) {
    return `${(volume / 1e4).toFixed(1)}万`;
  }
  return volume.toString();
};

// Format price with appropriate decimals based on symbol
export const formatPrice = (
  price: number,
  symbol?: string,
  decimals?: number
): string => {
  // Default decimals based on price range
  if (!decimals) {
    if (price >= 1000) decimals = 1;
    else if (price >= 100) decimals = 2;
    else decimals = 3;
  }

  // Special cases for Chinese stocks
  if (symbol && symbol.startsWith('00') || symbol.startsWith('30')) {
    decimals = 2;
  }

  return price.toFixed(decimals);
};

// Format number with thousands separator
export const formatNumber = (
  value: number,
  decimals: number = 2,
  separator: string = ','
): string => {
  const parts = value.toFixed(decimals).split('.');
  parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, separator);
  return parts.join('.');
};