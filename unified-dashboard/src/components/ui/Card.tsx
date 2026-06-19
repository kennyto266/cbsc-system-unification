import React, { HTMLAttributes, forwardRef } from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const cardVariants = cva(
  'rounded-lg border bg-white text-gray-950 shadow-sm',
  {
    variants: {
      variant: {
        default: 'border-gray-200',
        elevated: 'border-gray-200 shadow-lg',
        outlined: 'border-2 border-gray-200 shadow-none',
        ghost: 'border-transparent shadow-none bg-transparent',
      },
      padding: {
        none: 'p-0',
        sm: 'p-4',
        default: 'p-6',
        lg: 'p-8',
      },
    },
    defaultVariants: {
      variant: 'default',
      padding: 'default',
    },
  }
)

export interface CardProps
  extends HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof cardVariants> {}

const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ className, variant, padding, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(cardVariants({ variant, padding, className }))}
      {...props}
    />
  )
)
Card.displayName = 'Card'

const CardHeader = forwardRef<
  HTMLDivElement,
  HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn('flex flex-col space-y-1.5 pb-6', className)}
    {...props}
  />
))
CardHeader.displayName = 'CardHeader'

const CardTitle = forwardRef<
  HTMLParagraphElement,
  HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
  <h3
    ref={ref}
    className={cn(
      'text-2xl font-semibold leading-none tracking-tight',
      className
    )}
    {...props}
  />
))
CardTitle.displayName = 'CardTitle'

const CardDescription = forwardRef<
  HTMLParagraphElement,
  HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <p
    ref={ref}
    className={cn('text-sm text-gray-500', className)}
    {...props}
  />
))
CardDescription.displayName = 'CardDescription'

const CardContent = forwardRef<
  HTMLDivElement,
  HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div ref={ref} className={cn('pt-0', className)} {...props} />
))
CardContent.displayName = 'CardContent'

const CardFooter = forwardRef<
  HTMLDivElement,
  HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn('flex items-center pt-6', className)}
    {...props}
  />
))
CardFooter.displayName = 'CardFooter'

// CBSC-specific card components
export const MetricCard = forwardRef<
  HTMLDivElement,
  HTMLAttributes<HTMLDivElement> & {
    title?: string
    value?: string | number
    change?: number
    changeType?: 'increase' | 'decrease' | 'neutral'
    icon?: React.ReactNode
  }
>(({ className, title, value, change, changeType = 'neutral', icon, children, ...props }, ref) => (
  <Card
    ref={ref}
    className={cn(
      'hover:shadow-md transition-shadow duration-200',
      className
    )}
    {...props}
  >
    <CardContent className="p-4">
      <div className="flex items-center justify-between space-y-0 pb-2">
        <h3 className="text-sm font-medium">{title}</h3>
        {icon}
      </div>
      <div className="text-2xl font-bold">{value}</div>
      {change !== undefined && (
        <p className={cn(
          'text-xs',
          changeType === 'increase' && 'text-green-600',
          changeType === 'decrease' && 'text-red-600',
          changeType === 'neutral' && 'text-gray-600'
        )}>
          {changeType === 'increase' && '+'}
          {typeof change === 'number' ? change.toFixed(2) : change}%
        </p>
      )}
      {children}
    </CardContent>
  </Card>
))
MetricCard.displayName = 'MetricCard'

export const TradingCard = forwardRef<
  HTMLDivElement,
  HTMLAttributes<HTMLDivElement> & {
    symbol: string
    price: number
    change: number
    changePercent: number
    volume?: string
  }
>(({ className, symbol, price, change, changePercent, volume, ...props }, ref) => (
  <Card
    ref={ref}
    className={cn(
      'hover:shadow-lg transition-all duration-200 cursor-pointer',
      change >= 0 ? 'border-l-4 border-l-green-500' : 'border-l-4 border-l-red-500',
      className
    )}
    {...props}
  >
    <CardContent className="p-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-bold text-lg">{symbol}</h3>
          <p className="text-2xl font-bold">
            {price.toFixed(2)}
          </p>
        </div>
        <div className="text-right">
          <p className={cn(
            'font-semibold',
            change >= 0 ? 'text-green-600' : 'text-red-600'
          )}>
            {change >= 0 ? '+' : ''}{change.toFixed(2)}
          </p>
          <p className={cn(
            'text-sm',
            change >= 0 ? 'text-green-600' : 'text-red-600'
          )}>
            ({change >= 0 ? '+' : ''}{changePercent.toFixed(2)}%)
          </p>
        </div>
      </div>
      {volume && (
        <p className="text-xs text-gray-500 mt-2">
          Vol: {volume}
        </p>
      )}
    </CardContent>
  </Card>
))
TradingCard.displayName = 'TradingCard'

export const StrategyCard = forwardRef<
  HTMLDivElement,
  HTMLAttributes<HTMLDivElement> & {
    name: string
    status: 'active' | 'paused' | 'stopped'
    performance?: {
      totalReturn?: number
      winRate?: number
      maxDrawdown?: number
    }
    lastRun?: string
  }
>(({ className, name, status, performance, lastRun, ...props }, ref) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800'
      case 'paused': return 'bg-yellow-100 text-yellow-800'
      case 'stopped': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'active': return '運行中'
      case 'paused': return '暫停'
      case 'stopped': return '停止'
      default: return '未知'
    }
  }

  return (
    <Card
      ref={ref}
      className={cn(
        'hover:shadow-md transition-shadow duration-200',
        className
      )}
      {...props}
    >
      <CardContent className="p-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-bold text-lg">{name}</h3>
          <span className={cn(
            'px-2 py-1 rounded-full text-xs font-medium',
            getStatusColor(status)
          )}>
            {getStatusText(status)}
          </span>
        </div>

        {performance && (
          <div className="grid grid-cols-3 gap-2 text-xs">
            <div>
              <p className="text-gray-500">總回報</p>
              <p className={cn(
                'font-semibold',
                (performance.totalReturn || 0) >= 0 ? 'text-green-600' : 'text-red-600'
              )}>
                {performance.totalReturn?.toFixed(2)}%
              </p>
            </div>
            <div>
              <p className="text-gray-500">勝率</p>
              <p className="font-semibold text-blue-600">
                {performance.winRate?.toFixed(1)}%
              </p>
            </div>
            <div>
              <p className="text-gray-500">最大回撤</p>
              <p className="font-semibold text-red-600">
                {performance.maxDrawdown?.toFixed(2)}%
              </p>
            </div>
          </div>
        )}

        {lastRun && (
          <p className="text-xs text-gray-500 mt-3">
            最後運行: {new Date(lastRun).toLocaleString('zh-HK')}
          </p>
        )}
      </CardContent>
    </Card>
  )
})
StrategyCard.displayName = 'StrategyCard'

export { Card, CardHeader, CardFooter, CardTitle, CardDescription, CardContent }