// Re-export utility functions for @/lib/utils imports (shadcn/ui convention)
export { cn } from '../utils/cn'

// Common formatters used across square-ui components
export function formatNumber(value: number, decimals = 2): string {
  return Number(value).toLocaleString('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })
}

export function formatPercent(value: number, decimals = 2): string {
  return `${formatNumber(value, decimals)}%`
}

export function formatCurrency(value: number, currency = 'HKD'): string {
  return Number(value).toLocaleString('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}
