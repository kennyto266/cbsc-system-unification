import React from 'react'
import { motion } from 'framer-motion'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { cn, formatNumber, formatPercent, formatCurrency } from '@/lib/utils'

interface MetricCardProps {
  title: string
  value: number | string
  precision?: number
  prefix?: string
  suffix?: string
  trend?: number
  icon?: React.ReactNode
  loading?: boolean
  className?: string
  variant?: 'default' | 'compact' | 'large'
  format?: 'number' | 'currency' | 'percentage'
  currency?: string
  showTrendIcon?: boolean
  trendLabel?: string
  description?: string
  onClick?: () => void
}

const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  precision = 2,
  prefix,
  suffix,
  trend,
  icon,
  loading = false,
  className,
  variant = 'default',
  format = 'number',
  currency = 'USD',
  showTrendIcon = true,
  trendLabel,
  description,
  onClick,
}) => {
  // Format value based on format type
  const formatValue = (val: number | string) => {
    if (typeof val === 'string') return val

    switch (format) {
      case 'currency':
        return formatCurrency(val, currency)
      case 'percentage':
        return formatPercent(val, precision)
      default:
        return formatNumber(val)
    }
  }

  // Get trend color and icon
  const getTrendInfo = (trendValue?: number) => {
    if (!trendValue && trendValue !== 0) return null

    const isPositive = trendValue > 0
    const isNegative = trendValue < 0
    const isNeutral = trendValue === 0

    const colorClass = isPositive
      ? 'text-success-600'
      : isNegative
      ? 'text-error-600'
      : 'text-gray-500'

    const bgColorClass = isPositive
      ? 'bg-success-50'
      : isNegative
      ? 'bg-error-50'
      : 'bg-gray-50'

    const Icon = isPositive ? TrendingUp : isNegative ? TrendingDown : Minus

    return { colorClass, bgColorClass, Icon }
  }

  const trendInfo = getTrendInfo(trend)

  // Variant styles
  const variantStyles = {
    default: 'p-6',
    compact: 'p-4',
    large: 'p-8',
  }

  // Animation variants
  const cardVariants = {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    hover: { scale: 1.02, y: -4 },
  }

  // Loading skeleton
  if (loading) {
    return (
      <Card className={cn('relative overflow-hidden', variantStyles[variant], className)}>
        <CardContent className="p-0">
          <div className="animate-pulse">
            <div className="flex items-center justify-between mb-4">
              <div className="h-4 bg-gray-200 rounded w-1/2"></div>
              <div className="h-8 bg-gray-200 rounded w-8"></div>
            </div>
            <div className="h-8 bg-gray-200 rounded w-3/4 mb-2"></div>
            <div className="h-4 bg-gray-200 rounded w-1/4"></div>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <motion.div
      variants={cardVariants}
      initial="initial"
      animate="animate"
      whileHover="hover"
      transition={{ type: "spring", stiffness: 300, damping: 30 }}
    >
      <Card
        className={cn(
          'relative overflow-hidden border-0 shadow-lg hover:shadow-xl transition-all duration-300 cursor-pointer group',
          variantStyles[variant],
          'bg-gradient-to-br from-white to-gray-50',
          onClick && 'hover:scale-[1.02] active:scale-[0.98]',
          className
        )}
        onClick={onClick}
      >
        {/* Background gradient decoration */}
        <div className="absolute inset-0 bg-gradient-to-br from-primary-50/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

        <CardContent className="p-0 relative">
          <div className="flex items-start justify-between mb-4">
            <div className="flex-1">
              <h3 className="text-sm font-medium text-gray-600 mb-1">{title}</h3>
              {description && (
                <p className="text-xs text-gray-500 mt-1">{description}</p>
              )}
            </div>
            {icon && (
              <div className="p-2 rounded-lg bg-primary-50 text-primary-600 group-hover:scale-110 transition-transform">
                {icon}
              </div>
            )}
          </div>

          {/* Main value */}
          <div className="flex items-baseline mb-3">
            <span className={cn(
              'font-semibold tracking-tight',
              variant === 'large' ? 'text-3xl' : variant === 'compact' ? 'text-xl' : 'text-2xl',
              'text-gray-900'
            )}>
              {prefix && <span className="mr-1 text-gray-500">{prefix}</span>}
              {formatValue(value)}
              {suffix && <span className="ml-1 text-gray-500">{suffix}</span>}
            </span>
          </div>

          {/* Trend indicator */}
          {trendInfo && (
            <div className="flex items-center gap-2">
              <div className={cn(
                'flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium',
                trendInfo.bgColorClass,
                trendInfo.colorClass
              )}>
                {showTrendIcon && (
                  <trendInfo.Icon className="w-3 h-3" />
                )}
                <span>
                  {trendLabel || `Change: ${Math.abs(trend).toFixed(precision)}%`}
                </span>
              </div>
              <span className="text-xs text-gray-500">
                vs last period
              </span>
            </div>
          )}

          {/* Decorative elements */}
          <div className="absolute -bottom-2 -right-2 w-24 h-24 bg-gradient-to-br from-primary-100/30 to-transparent rounded-full opacity-50" />
          <div className="absolute -top-1 -right-1 w-12 h-12 bg-gradient-to-br from-cbsc-cyan/20 to-transparent rounded-full" />
        </CardContent>
      </Card>
    </motion.div>
  )
}

export default MetricCard