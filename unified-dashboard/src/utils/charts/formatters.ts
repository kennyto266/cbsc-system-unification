// Number formatting utilities
export const formatNumber = (
  value: number,
  decimals: number = 2,
  locale: string = 'zh-TW'
): string => {
  if (isNaN(value)) return '0'

  return new Intl.NumberFormat(locale, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value)
}

export const formatLargeNumber = (value: number): string => {
  if (Math.abs(value) >= 1e9) {
    return `${(value / 1e9).toFixed(2)}B`
  } else if (Math.abs(value) >= 1e6) {
    return `${(value / 1e6).toFixed(2)}M`
  } else if (Math.abs(value) >= 1e3) {
    return `${(value / 1e3).toFixed(2)}K`
  }
  return formatNumber(value)
}

export const formatPercentage = (
  value: number,
  decimals: number = 2,
  showSign: boolean = true
): string => {
  const formatted = formatNumber(value * 100, decimals)
  if (showSign && value > 0) {
    return `+${formatted}%`
  } else if (showSign && value < 0) {
    return `${formatted}%`
  }
  return `${formatted}%`
}

export const formatCurrency = (
  value: number,
  currency: string = 'USD',
  locale: string = 'zh-TW',
  decimals: number = 2
): string => {
  if (isNaN(value)) return `0.00 ${currency}`

  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency,
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value)
}

export const formatCryptoCurrency = (
  value: number,
  symbol: string = 'BTC',
  decimals: number = 8
): string => {
  if (value < 0.0001 && decimals > 4) {
    return `${value.toFixed(decimals)} ${symbol}`
  }
  return `${formatNumber(value, 4)} ${symbol}`
}

export const formatPrice = (
  value: number,
  decimals: number = 2,
  currency?: string
): string => {
  if (currency) {
    return formatCurrency(value, currency)
  }
  return formatNumber(value, decimals)
}

// Date and time formatting utilities
export const formatDate = (
  date: string | Date,
  format: 'short' | 'medium' | 'long' | 'iso' = 'medium',
  locale: string = 'zh-TW'
): string => {
  const dateObj = new Date(date)

  switch (format) {
    case 'short':
      return dateObj.toLocaleDateString(locale, {
        month: 'short',
        day: 'numeric',
      })
    case 'long':
      return dateObj.toLocaleDateString(locale, {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      })
    case 'iso':
      return dateObj.toISOString()
    default:
      return dateObj.toLocaleDateString(locale, {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      })
  }
}

export const formatTime = (
  date: string | Date,
  format: 'short' | 'medium' | 'long' | '24h' = 'medium',
  locale: string = 'zh-TW'
): string => {
  const dateObj = new Date(date)

  switch (format) {
    case 'short':
      return dateObj.toLocaleTimeString(locale, {
        hour: '2-digit',
        minute: '2-digit',
      })
    case '24h':
      return dateObj.toLocaleTimeString('en-US', {
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      })
    case 'long':
      return dateObj.toLocaleTimeString(locale, {
        hour12: true,
        hour: 'numeric',
        minute: '2-digit',
        second: '2-digit',
      })
    default:
      return dateObj.toLocaleTimeString(locale, {
        hour12: true,
        hour: 'numeric',
        minute: '2-digit',
      })
  }
}

export const formatDateTime = (
  date: string | Date,
  dateLocale: string = 'zh-TW',
  timeLocale: string = 'zh-TW'
): string => {
  const dateObj = new Date(date)
  const dateStr = formatDate(dateObj, 'medium', dateLocale)
  const timeStr = formatTime(dateObj, 'medium', timeLocale)
  return `${dateStr} ${timeStr}`
}

export const formatDuration = (milliseconds: number): string => {
  const seconds = Math.floor(milliseconds / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)

  if (days > 0) {
    return `${days}d ${hours % 24}h`
  } else if (hours > 0) {
    return `${hours}h ${minutes % 60}m`
  } else if (minutes > 0) {
    return `${minutes}m ${seconds % 60}s`
  } else {
    return `${seconds}s`
  }
}

export const formatRelativeTime = (
  date: string | Date,
  baseDate: string | Date = new Date(),
  locale: string = 'zh-TW'
): string => {
  const target = new Date(date)
  const base = new Date(baseDate)
  const diffInSeconds = Math.floor((base.getTime() - target.getTime()) / 1000)

  const rtf = new Intl.RelativeTimeFormat(locale, { numeric: 'auto' })

  if (Math.abs(diffInSeconds) < 60) {
    return rtf.format(-diffInSeconds, 'second')
  } else if (Math.abs(diffInSeconds) < 3600) {
    return rtf.format(-Math.floor(diffInSeconds / 60), 'minute')
  } else if (Math.abs(diffInSeconds) < 86400) {
    return rtf.format(-Math.floor(diffInSeconds / 3600), 'hour')
  } else {
    return rtf.format(-Math.floor(diffInSeconds / 86400), 'day')
  }
}

// Specialized formatting functions for financial data
export const formatPriceChange = (
  change: number,
  decimals: number = 2,
  currency?: string
): string => {
  const sign = change >= 0 ? '+' : ''
  const value = formatNumber(Math.abs(change), decimals)
  return `${sign}${currency ? formatCurrency(change, currency) : value}`
}

export const formatPriceChangePercent = (
  changePercent: number,
  decimals: number = 2
): string => {
  const sign = changePercent >= 0 ? '+' : ''
  return `${sign}${formatNumber(changePercent, decimals)}%`
}

export const formatVolume = (
  volume: number,
  locale: string = 'zh-TW'
): string => {
  if (volume >= 1e9) {
    return `${formatNumber(volume / 1e9, 2, locale)}B`
  } else if (volume >= 1e6) {
    return `${formatNumber(volume / 1e6, 2, locale)}M`
  } else if (volume >= 1e3) {
    return `${formatNumber(volume / 1e3, 2, locale)}K`
  }
  return formatNumber(volume, 0, locale)
}

export const formatMarketCap = (marketCap: number, currency: string = 'USD'): string => {
  return formatCurrency(marketCap, currency)
}

export const formatYield = (yieldValue: number, decimals: number = 2): string => {
  return formatPercentage(yieldValue, decimals)
}

export const formatSpread = (bid: number, ask: number, decimals: number = 4): string => {
  const spread = ask - bid
  const spreadPercent = (spread / bid) * 100
  return `${formatNumber(spread, decimals)} (${formatPercentage(spreadPercent / 100, 2)})`
}

export const formatPnL = (
  pnl: number,
  decimals: number = 2,
  currency: string = 'USD'
): string => {
  const colorClass = pnl > 0 ? 'text-green-500' : pnl < 0 ? 'text-red-500' : 'text-gray-500'
  return {
    value: formatPriceChange(pnl, decimals, currency),
    className: colorClass,
  }
}

// Utility function to format based on context
export const smartFormat = (
  value: number,
  type?: 'price' | 'percentage' | 'volume' | 'currency' | 'large',
  options: {
    currency?: string
    decimals?: number
    locale?: string
  } = {}
): string => {
  const { currency = 'USD', decimals = 2, locale = 'zh-TW' } = options

  switch (type) {
    case 'price':
      return formatPrice(value, decimals, currency)
    case 'percentage':
      return formatPercentage(value, decimals)
    case 'volume':
      return formatVolume(value, locale)
    case 'currency':
      return formatCurrency(value, currency, locale, decimals)
    case 'large':
      return formatLargeNumber(value)
    default:
      return formatNumber(value, decimals, locale)
  }
}