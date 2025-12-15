import React, { useState, useEffect } from 'react'
import { Line, LineChart, ResponsiveContainer, XAxis, YAxis, Tooltip, ReferenceLine } from 'recharts'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card'
import { Badge } from '../ui/badge'
import { TrendingUp, TrendingDown, DollarSign } from 'lucide-react'
import { cn } from '../../lib/utils'
import { useRealTimeChart } from '../../hooks/useRealTimeChart'

interface MarketPriceChartProps {
  symbol: string
  initialPrice?: number
  height?: number
  className?: string
}

interface PriceData {
  time: string
  price: number
  ma?: number
}

export const MarketPriceChart: React.FC<MarketPriceChartProps> = ({
  symbol,
  initialPrice = 100,
  height = 200,
  className
}) => {
  const [currentPrice, setCurrentPrice] = useState(initialPrice)
  const [priceChange, setPriceChange] = useState(0)
  const [priceChangePercent, setPriceChangePercent] = useState(0)

  // Initialize with mock historical data
  const initialData: PriceData[] = []
  let mockPrice = initialPrice
  const now = new Date()

  for (let i = 60; i >= 0; i--) {
    const time = new Date(now.getTime() - i * 60000)
    const change = (Math.random() - 0.48) * 0.5 // Slight upward bias
    mockPrice = mockPrice * (1 + change / 100)
    initialData.push({
      time: time.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
      price: mockPrice
    })
  }

  const { data, isRunning, lastValue, start, stop } = useRealTimeChart({
    initialData,
    updateInterval: 2000,
    maxDataPoints: 60,
    autoStart: true
  })

  // Simulate price updates
  useEffect(() => {
    const handleUpdate = (event: CustomEvent) => {
      const { addDataPoint } = event.detail
      const change = (Math.random() - 0.48) * 0.5
      const newPrice = currentPrice * (1 + change / 100)

      setCurrentPrice(newPrice)
      addDataPoint(newPrice)

      // Calculate change from initial price
      const absoluteChange = newPrice - initialPrice
      const percentChange = (absoluteChange / initialPrice) * 100

      setPriceChange(absoluteChange)
      setPriceChangePercent(percentChange)
    }

    window.addEventListener('realTimeChartUpdate', handleUpdate as EventListener)
    return () => {
      window.removeEventListener('realTimeChartUpdate', handleUpdate as EventListener)
    }
  }, [currentPrice, initialPrice])

  // Calculate moving average
  const dataWithMA = data.map((point, index) => ({
    ...point,
    ma: index >= 10 ? data.slice(index - 10, index).reduce((sum, p) => sum + p.price, 0) / 10 : undefined
  }))

  const isPositive = priceChange >= 0

  return (
    <Card className={cn("w-full", className)}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <DollarSign className="h-4 w-4" />
            <CardTitle className="text-sm font-medium">{symbol}</CardTitle>
          </div>
          <div className="flex items-center space-x-2">
            <Badge
              variant={isRunning ? "default" : "secondary"}
              className="text-xs cursor-pointer"
              onClick={isRunning ? stop : start}
            >
              {isRunning ? '实时' : '暂停'}
            </Badge>
          </div>
        </div>

        {/* Price Display */}
        <div className="mt-2">
          <div className="flex items-baseline space-x-2">
            <span className="text-2xl font-bold">
              ${currentPrice.toFixed(2)}
            </span>
            <div className={cn(
              "flex items-center text-sm",
              isPositive ? "text-green-600" : "text-red-600"
            )}>
              {isPositive ? (
                <TrendingUp className="h-3 w-3 mr-1" />
              ) : (
                <TrendingDown className="h-3 w-3 mr-1" />
              )}
              <span>
                {isPositive ? '+' : ''}{priceChange.toFixed(2)} ({isPositive ? '+' : ''}{priceChangePercent.toFixed(2)}%)
              </span>
            </div>
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-0">
        <ResponsiveContainer width="100%" height={height}>
          <LineChart data={dataWithMA} margin={{ top: 5, right: 5, bottom: 5, left: 5 }}>
            <XAxis
              dataKey="time"
              tick={{ fontSize: 10 }}
              interval="preserveStartEnd"
            />
            <YAxis
              tick={{ fontSize: 10 }}
              domain={['dataMin - 1', 'dataMax + 1']}
              tickFormatter={(value) => `$${value}`}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'hsl(var(--card))',
                border: '1px solid hsl(var(--border))',
                borderRadius: '6px'
              }}
              labelStyle={{ color: 'hsl(var(--foreground))' }}
              formatter={(value: number) => [`$${value.toFixed(2)}`, '价格']}
            />
            <ReferenceLine
              y={initialPrice}
              stroke="hsl(var(--muted-foreground))"
              strokeDasharray="3 3"
            />
            <Line
              type="monotone"
              dataKey="price"
              stroke={isPositive ? "hsl(142, 76%, 36%)" : "hsl(0, 84%, 60%)"}
              strokeWidth={2}
              dot={false}
              animationDuration={300}
            />
            <Line
              type="monotone"
              dataKey="ma"
              stroke="hsl(var(--muted-foreground))"
              strokeWidth={1}
              strokeDasharray="3 3"
              dot={false}
              connectNulls={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}