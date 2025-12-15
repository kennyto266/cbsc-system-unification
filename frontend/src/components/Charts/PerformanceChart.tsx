import React from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'

const mockData = [
  { date: '2024-01', value: 100000, benchmark: 100000 },
  { date: '2024-02', value: 102000, benchmark: 101000 },
  { date: '2024-03', value: 105000, benchmark: 102000 },
  { date: '2024-04', value: 103000, benchmark: 103000 },
  { date: '2024-05', value: 108000, benchmark: 104000 },
  { date: '2024-06', value: 112000, benchmark: 105000 },
  { date: '2024-07', value: 115000, benchmark: 106000 },
  { date: '2024-08', value: 113000, benchmark: 107000 },
  { date: '2024-09', value: 118000, benchmark: 108000 },
  { date: '2024-10', value: 123500, benchmark: 109000 },
]

export const PerformanceChart: React.FC = () => {
  const formatCurrency = (value: number) => {
    return `¥${(value / 1000).toFixed(0)}K`
  }

  return (
    <div className="h-80">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={mockData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="date"
            stroke="#6b7280"
            fontSize={12}
            tickLine={false}
            axisLine={false}
          />
          <YAxis
            stroke="#6b7280"
            fontSize={12}
            tickLine={false}
            axisLine={false}
            tickFormatter={formatCurrency}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#ffffff',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
            }}
            formatter={(value: number) => [formatCurrency(value), '']}
          />
          <Line
            type="monotone"
            dataKey="value"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={false}
            name="策略收益"
          />
          <Line
            type="monotone"
            dataKey="benchmark"
            stroke="#9ca3af"
            strokeWidth={2}
            dot={false}
            strokeDasharray="5 5"
            name="基准"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}