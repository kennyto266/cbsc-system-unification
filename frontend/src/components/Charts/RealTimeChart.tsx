import React, { useState, useEffect, useRef } from 'react'
import { Line, LineChart, ResponsiveContainer, XAxis, YAxis, Tooltip } from 'recharts'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card'
import { Badge } from '../ui/badge'
import { Button } from '../ui/button'
import { Play, Pause, RotateCcw } from 'lucide-react'
import { cn } from '@/lib/utils'

interface RealTimeChartProps {
  title?: string
  dataSource?: () => Promise<number>
  updateInterval?: number
  maxDataPoints?: number
  height?: number
  className?: string
}

interface DataPoint {
  time: string
  value: number
}

export const RealTimeChart: React.FC<RealTimeChartProps> = ({
  title = '实时数据图表',
  dataSource,
  updateInterval = 1000,
  maxDataPoints = 50,
  height = 300,
  className
}) => {
  const [data, setData] = useState<DataPoint[]>([])
  const [isRunning, setIsRunning] = useState(true)
  const [lastValue, setLastValue] = useState<number>(0)
  const intervalRef = useRef<NodeJS.Timeout>()

  // Fetch data point
  const fetchDataPoint = async (): Promise<number> => {
    if (dataSource) {
      return await dataSource()
    }
    // Mock data generation
    return Math.random() * 100
  }

  // Add new data point
  const addDataPoint = async () => {
    try {
      const value = await fetchDataPoint()
      const now = new Date()
      const timeString = now.toLocaleTimeString('zh-CN')

      setData(prevData => {
        const newPoint = { time: timeString, value }
        const updatedData = [...prevData, newPoint]

        // Keep only the last maxDataPoints
        if (updatedData.length > maxDataPoints) {
          return updatedData.slice(-maxDataPoints)
        }

        return updatedData
      })

      setLastValue(value)
    } catch (error) {
      console.error('Error fetching data:', error)
    }
  }

  // Initialize with some data
  useEffect(() => {
    const initializeData = async () => {
      const initialData: DataPoint[] = []
      for (let i = maxDataPoints - 10; i > 0; i--) {
        const now = new Date()
        now.setSeconds(now.getSeconds() - i)
        initialData.push({
          time: now.toLocaleTimeString('zh-CN'),
          value: Math.random() * 100
        })
      }
      setData(initialData)
    }

    initializeData()
  }, [maxDataPoints])

  // Real-time updates
  useEffect(() => {
    if (isRunning) {
      addDataPoint() // Add first point immediately

      intervalRef.current = setInterval(() => {
        addDataPoint()
      }, updateInterval)
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [isRunning, updateInterval])

  const handleToggle = () => {
    setIsRunning(!isRunning)
  }

  const handleReset = () => {
    setData([])
    setIsRunning(false)
  }

  // Calculate statistics
  const stats = React.useMemo(() => {
    if (data.length === 0) return { avg: 0, min: 0, max: 0, trend: 'stable' }

    const values = data.map(d => d.value)
    const avg = values.reduce((a, b) => a + b, 0) / values.length
    const min = Math.min(...values)
    const max = Math.max(...values)

    // Calculate trend
    const firstHalf = values.slice(0, Math.floor(values.length / 2))
    const secondHalf = values.slice(Math.floor(values.length / 2))
    const firstAvg = firstHalf.reduce((a, b) => a + b, 0) / firstHalf.length
    const secondAvg = secondHalf.reduce((a, b) => a + b, 0) / secondHalf.length

    const trend = secondAvg > firstAvg * 1.02 ? 'up' :
                  secondAvg < firstAvg * 0.98 ? 'down' : 'stable'

    return { avg, min, max, trend }
  }, [data])

  return (
    <Card className={cn("w-full", className)}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium">{title}</CardTitle>
          <div className="flex items-center space-x-2">
            <Badge
              variant={isRunning ? "default" : "secondary"}
              className="text-xs"
            >
              {isRunning ? '运行中' : '已暂停'}
            </Badge>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleToggle}
              className="h-8 w-8 p-0"
            >
              {isRunning ? <Pause className="h-3 w-3" /> : <Play className="h-3 w-3" />}
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleReset}
              className="h-8 w-8 p-0"
            >
              <RotateCcw className="h-3 w-3" />
            </Button>
          </div>
        </div>

        {/* Stats Bar */}
        <div className="flex items-center justify-between mt-2 text-xs text-muted-foreground">
          <span>当前: {lastValue.toFixed(2)}</span>
          <span>平均: {stats.avg.toFixed(2)}</span>
          <span>最大: {stats.max.toFixed(2)}</span>
          <span>最小: {stats.min.toFixed(2)}</span>
        </div>
      </CardHeader>

      <CardContent className="p-0">
        <ResponsiveContainer width="100%" height={height}>
          <LineChart data={data} margin={{ top: 5, right: 5, bottom: 5, left: 5 }}>
            <XAxis
              dataKey="time"
              tick={{ fontSize: 10 }}
              interval="preserveStartEnd"
            />
            <YAxis
              tick={{ fontSize: 10 }}
              domain={['dataMin - 5', 'dataMax + 5']}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'hsl(var(--card))',
                border: '1px solid hsl(var(--border))',
                borderRadius: '6px'
              }}
              labelStyle={{ color: 'hsl(var(--foreground))' }}
            />
            <Line
              type="monotone"
              dataKey="value"
              stroke="hsl(var(--primary))"
              strokeWidth={2}
              dot={false}
              animationDuration={300}
            />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}