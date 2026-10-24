/**
 * Real-time Monitor Widget Component
 * Displays real-time market data and strategy performance
 */

import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { useWebSocket } from '../../hooks/useWebSocket'
import { useRealTimeData } from '../../hooks/useWebSocket'

interface RealTimeMonitorWidgetProps {
  widgetId: string
  config?: any
}

interface DataPoint {
  time: string
  value: number
  timestamp: number
}

const RealTimeMonitorWidget: React.FC<RealTimeMonitorWidgetProps> = ({ widgetId, config = {} }) => {
  const [data, setData] = useState<DataPoint[]>([])
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date())
  const { isConnected } = useWebSocket()

  // Mock real-time data
  useEffect(() => {
    const generateDataPoint = (): DataPoint => {
      const now = new Date()
      return {
        time: now.toLocaleTimeString('zh-HK', { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
        value: 100 + Math.random() * 20,
        timestamp: now.getTime(),
      }
    }

    // Initialize with some data
    const initialData: DataPoint[] = []
    for (let i = 19; i >= 0; i--) {
      const point = generateDataPoint()
      point.timestamp = Date.now() - i * 1000
      point.time = new Date(point.timestamp).toLocaleTimeString('zh-HK', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      })
      initialData.push(point)
    }
    setData(initialData)

    // Update data every second
    const interval = setInterval(() => {
      setData(prevData => {
        const newPoint = generateDataPoint()
        const updatedData = [...prevData.slice(1), newPoint]
        setLastUpdate(new Date())
        return updatedData
      })
    }, 1000)

    return () => clearInterval(interval)
  }, [])

  return (
    <div className="h-full w-full p-4">
      <div className="flex flex-col h-full">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div>
            <h4 className="text-sm font-medium text-gray-900 dark:text-white">實時監控</h4>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              最後更新: {lastUpdate.toLocaleTimeString('zh-HK')}
            </p>
          </div>
          <div className={`flex items-center space-x-1 ${isConnected ? 'text-green-500' : 'text-red-500'}`}>
            <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
            <span className="text-xs">
              {isConnected ? '連線中' : '離線'}
            </span>
          </div>
        </div>

        {/* Chart */}
        <div className="flex-1 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart
              data={data}
              margin={{ top: 5, right: 5, left: 5, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis
                dataKey="time"
                stroke="#6b7280"
                fontSize={10}
                tick={{ fontSize: 10 }}
              />
              <YAxis
                stroke="#6b7280"
                fontSize={10}
                tick={{ fontSize: 10 }}
                domain={['dataMin - 5', 'dataMax + 5']}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'rgba(255, 255, 255, 0.95)',
                  border: '1px solid #e5e7eb',
                  borderRadius: '6px',
                  fontSize: '12px',
                }}
                labelStyle={{ color: '#374151', fontWeight: 'bold' }}
              />
              <Line
                type="monotone"
                dataKey="value"
                stroke="#3b82f6"
                strokeWidth={2}
                dot={false}
                activeDot={{
                  r: 4,
                  fill: '#3b82f6',
                  stroke: '#fff',
                  strokeWidth: 2,
                }}
                animationDuration={300}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Stats */}
        <div className="mt-4 grid grid-cols-3 gap-2">
          <div className="text-center p-2 bg-blue-50 dark:bg-blue-900/20 rounded">
            <div className="text-xs text-gray-500 dark:text-gray-400">當前值</div>
            <div className="text-sm font-semibold text-blue-600 dark:text-blue-400">
              {data.length > 0 ? data[data.length - 1].value.toFixed(2) : '-'}
            </div>
          </div>
          <div className="text-center p-2 bg-green-50 dark:bg-green-900/20 rounded">
            <div className="text-xs text-gray-500 dark:text-gray-400">變化</div>
            <div className="text-sm font-semibold text-green-600 dark:text-green-400">
              {data.length > 1 ? (
                ((data[data.length - 1].value - data[data.length - 2].value)).toFixed(2)
              ) : '-'}
            </div>
          </div>
          <div className="text-center p-2 bg-purple-50 dark:bg-purple-900/20 rounded">
            <div className="text-xs text-gray-500 dark:text-gray-400">範圍</div>
            <div className="text-sm font-semibold text-purple-600 dark:text-purple-400">
              {data.length > 0 ? (
                (Math.max(...data.map(d => d.value)) - Math.min(...data.map(d => d.value))).toFixed(2)
              ) : '-'}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default RealTimeMonitorWidget