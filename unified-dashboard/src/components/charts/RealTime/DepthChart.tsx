import React, { useMemo, useState, useEffect, useRef, useCallback } from 'react'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ChartOptions,
  ChartData,
  Scale,
  CoreScaleOptions
} from 'chart.js'
import { Line } from 'react-chartjs-2'
import { Card, Select, Space, Button, Switch, Tag, Slider, Row, Col, InputNumber } from 'antd'
import {
  DownloadOutlined,
  BarChartOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  SettingOutlined,
  SyncOutlined,
  ReloadOutlined
} from '@ant-design/icons'
import { useWebSocket } from '../../../hooks/useWebSocket'
import { debounce } from 'lodash'

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend
)

// Order book data interface
export interface OrderBookLevel {
  price: number
  amount: number
  total: number
}

export interface OrderBookData {
  bids: OrderBookLevel[]  // Buy orders
  asks: OrderBookLevel[]  // Sell orders
  lastUpdate: Date
  spread: number
  midPrice: number
}

// Props interface
export interface DepthChartProps {
  symbol: string
  data?: OrderBookData
  depth?: number  // Number of levels to show
  height?: number
  realTime?: boolean
  theme?: 'light' | 'dark'
  showOrders?: boolean
  showCumulative?: boolean
  onDepthChange?: (depth: number) => void
  exportOptions?: {
    enabled: boolean
    formats: ('png' | 'jpg' | 'svg')[]
  }
}

// Order book colors
const COLORS = {
  bids: {
    border: '#10B981',
    background: 'rgba(16, 185, 129, 0.2)',
    fill: 'rgba(16, 185, 129, 0.1)'
  },
  asks: {
    border: '#EF4444',
    background: 'rgba(239, 68, 68, 0.2)',
    fill: 'rgba(239, 68, 68, 0.1)'
  },
  spread: '#F59E0B',
  midPrice: '#3B82F6'
}

// Main component
const DepthChart: React.FC<DepthChartProps> = ({
  symbol,
  data,
  depth = 20,
  height = 400,
  realTime = true,
  theme = 'light',
  showOrders = true,
  showCumulative = true,
  onDepthChange,
  exportOptions = { enabled: true, formats: ['png'] }
}) => {
  const [isPlaying, setIsPlaying] = useState(realTime)
  const [showSettings, setShowSettings] = useState(false)
  const [orderBookData, setOrderBookData] = useState<OrderBookData | null>(data || null)
  const [precision, setPrecision] = useState(2)
  const [autoDepth, setAutoDepth] = useState(false)
  const chartRef = useRef<ChartJS<'line'>>(null)
  const { isConnected, subscribe, unsubscribe } = useWebSocket()

  // Initialize empty order book if no data provided
  useEffect(() => {
    if (!data) {
      // Generate mock data for demonstration
      const mockData: OrderBookData = {
        bids: [],
        asks: [],
        lastUpdate: new Date(),
        spread: 0,
        midPrice: 0
      }

      // Generate mock bids and asks
      const basePrice = 50000
      for (let i = 0; i < depth; i++) {
        const bidPrice = basePrice - (i + 1) * 10
        const askPrice = basePrice + (i + 1) * 10
        const bidAmount = Math.random() * 10 + 0.1
        const askAmount = Math.random() * 10 + 0.1

        mockData.bids.push({
          price: bidPrice,
          amount: bidAmount,
          total: bidPrice * bidAmount
        })

        mockData.asks.push({
          price: askPrice,
          amount: askAmount,
          total: askPrice * askAmount
        })
      }

      mockData.spread = mockData.asks[0].price - mockData.bids[0].price
      mockData.midPrice = (mockData.asks[0].price + mockData.bids[0].price) / 2

      setOrderBookData(mockData)
    }
  }, [data, depth])

  // WebSocket subscription for real-time updates
  useEffect(() => {
    if (realTime && isConnected) {
      const channel = `depth.${symbol}`

      const handleDepthUpdate = (newData: any) => {
        setOrderBookData(prevData => {
          if (!prevData) return null

          const updated = { ...prevData }

          // Update bids
          if (newData.bids) {
            newData.bids.forEach((bid: any) => {
              const index = updated.bids.findIndex(b => b.price === bid[0])
              if (bid[1] === 0) {
                // Remove level if amount is 0
                if (index !== -1) {
                  updated.bids.splice(index, 1)
                }
              } else {
                // Update or add level
                if (index !== -1) {
                  updated.bids[index] = {
                    price: bid[0],
                    amount: bid[1],
                    total: bid[0] * bid[1]
                  }
                } else {
                  updated.bids.push({
                    price: bid[0],
                    amount: bid[1],
                    total: bid[0] * bid[1]
                  })
                }
              }
            })

            // Sort bids by price (descending)
            updated.bids.sort((a, b) => b.price - a.price)
            updated.bids = updated.bids.slice(0, depth)
          }

          // Update asks
          if (newData.asks) {
            newData.asks.forEach((ask: any) => {
              const index = updated.asks.findIndex(a => a.price === ask[0])
              if (ask[1] === 0) {
                // Remove level if amount is 0
                if (index !== -1) {
                  updated.asks.splice(index, 1)
                }
              } else {
                // Update or add level
                if (index !== -1) {
                  updated.asks[index] = {
                    price: ask[0],
                    amount: ask[1],
                    total: ask[0] * ask[1]
                  }
                } else {
                  updated.asks.push({
                    price: ask[0],
                    amount: ask[1],
                    total: ask[0] * ask[1]
                  })
                }
              }
            })

            // Sort asks by price (ascending)
            updated.asks.sort((a, b) => a.price - b.price)
            updated.asks = updated.asks.slice(0, depth)
          }

          // Calculate spread and mid price
          if (updated.bids.length > 0 && updated.asks.length > 0) {
            updated.spread = updated.asks[0].price - updated.bids[0].price
            updated.midPrice = (updated.asks[0].price + updated.bids[0].price) / 2
          }

          updated.lastUpdate = new Date()
          return updated
        })
      }

      subscribe(channel, handleDepthUpdate)

      return () => {
        unsubscribe(channel, handleDepthUpdate)
      }
    }
  }, [realTime, isConnected, symbol, depth, subscribe, unsubscribe])

  // Calculate cumulative volume
  const calculateCumulative = useCallback((levels: OrderBookLevel[]): number[] => {
    const cumulative: number[] = []
    let sum = 0

    for (let i = levels.length - 1; i >= 0; i--) {
      sum += levels[i].total
      cumulative.unshift(sum)
    }

    return cumulative
  }, [])

  // Chart data preparation
  const chartData = useMemo((): ChartData<'line'> => {
    if (!orderBookData) {
      return { labels: [], datasets: [] }
    }

    // Prepare prices (x-axis)
    const bidPrices = orderBookData.bids.map(b => b.price).reverse()
    const askPrices = orderBookData.asks.map(a => a.price)
    const allPrices = [...bidPrices, orderBookData.midPrice || 0, ...askPrices]

    // Prepare datasets
    const datasets: any[] = []

    if (showOrders) {
      // Order book depth
      const bidAmounts = orderBookData.bids.map(b => b.total).reverse()
      const askAmounts = orderBookData.asks.map(a => a.total)

      datasets.push(
        {
          label: 'Bid Depth',
          data: bidPrices.map((price, i) => ({
            x: price,
            y: bidAmounts[i] || 0
          })),
          borderColor: COLORS.bids.border,
          backgroundColor: COLORS.bids.background,
          borderWidth: 2,
          fill: false,
          pointRadius: 0,
          tension: 0.4
        },
        {
          label: 'Ask Depth',
          data: askPrices.map((price, i) => ({
            x: price,
            y: askAmounts[i] || 0
          })),
          borderColor: COLORS.asks.border,
          backgroundColor: COLORS.asks.background,
          borderWidth: 2,
          fill: false,
          pointRadius: 0,
          tension: 0.4
        }
      )
    }

    if (showCumulative) {
      // Cumulative volume
      const bidCumulative = calculateCumulative(orderBookData.bids).reverse()
      const askCumulative = calculateCumulative(orderBookData.asks)

      datasets.push(
        {
          label: 'Bid Cumulative',
          data: bidPrices.map((price, i) => ({
            x: price,
            y: bidCumulative[i] || 0
          })),
          borderColor: COLORS.bids.border,
          backgroundColor: COLORS.bids.fill,
          borderWidth: 1,
          fill: '+1', // Fill to next dataset
          pointRadius: 0,
          tension: 0.1
        },
        {
          label: 'Ask Cumulative',
          data: askPrices.map((price, i) => ({
            x: price,
            y: askCumulative[i] || 0
          })),
          borderColor: COLORS.asks.border,
          backgroundColor: COLORS.asks.fill,
          borderWidth: 1,
          fill: '-1', // Fill to previous dataset
          pointRadius: 0,
          tension: 0.1
        }
      )
    }

    // Mid price line
    if (orderBookData.midPrice) {
      datasets.push({
        label: 'Mid Price',
        data: [{
          x: orderBookData.midPrice,
          y: Math.max(
            ...datasets.map(d => Math.max(...(d.data as any[]).map((p: any) => p.y || 0)))
          )
        }, {
          x: orderBookData.midPrice,
          y: 0
        }],
        borderColor: COLORS.midPrice,
        borderWidth: 2,
        borderDash: [5, 5],
        fill: false,
        pointRadius: 0,
        showLine: true
      })
    }

    return {
      datasets
    }
  }, [orderBookData, showOrders, showCumulative, calculateCumulative])

  // Chart options
  const chartOptions: ChartOptions<'line'> = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'nearest' as const,
      intersect: false,
      axis: 'x'
    },
    animation: false, // Disable for performance
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
          usePointStyle: true,
          padding: 10,
          font: {
            size: 11
          },
          color: theme === 'dark' ? '#fff' : '#374151'
        }
      },
      title: {
        display: false
      },
      tooltip: {
        backgroundColor: theme === 'dark' ? 'rgba(0, 0, 0, 0.9)' : 'rgba(0, 0, 0, 0.8)',
        padding: 12,
        cornerRadius: 8,
        callbacks: {
          title: function(context) {
            return `Price: ${context[0].parsed.x?.toFixed(precision)}`
          },
          label: function(context) {
            return `${context.dataset.label}: ${context.parsed.y?.toFixed(2)}`
          }
        }
      }
    },
    scales: {
      x: {
        type: 'linear' as const,
        position: 'bottom' as const,
        display: true,
        title: {
          display: true,
          text: 'Price',
          color: theme === 'dark' ? '#fff' : '#374151'
        },
        grid: {
          color: theme === 'dark' ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)'
        },
        ticks: {
          color: theme === 'dark' ? '#9CA3AF' : '#6B7280',
          callback: function(value) {
            return (value as number).toFixed(precision)
          }
        }
      },
      y: {
        display: true,
        title: {
          display: true,
          text: 'Volume',
          color: theme === 'dark' ? '#fff' : '#374151'
        },
        grid: {
          color: theme === 'dark' ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)'
        },
        ticks: {
          color: theme === 'dark' ? '#9CA3AF' : '#6B7280',
          callback: function(value) {
            return (value as number).toLocaleString()
          }
        }
      }
    }
  }

  // Export chart
  const handleExport = (format: string) => {
    const canvas = chartRef.current?.canvas
    if (canvas) {
      const url = canvas.toDataURL(`image/${format}`)
      const link = document.createElement('a')
      link.download = `${symbol}-depth-${Date.now()}.${format}`
      link.href = url
      link.click()
    }
  }

  // Refresh data
  const handleRefresh = () => {
    // Trigger data refresh
    setIsPlaying(false)
    setTimeout(() => setIsPlaying(realTime), 100)
  }

  // Order book statistics
  const totalBidVolume = orderBookData?.bids.reduce((sum, b) => sum + b.total, 0) || 0
  const totalAskVolume = orderBookData?.asks.reduce((sum, a) => sum + a.total, 0) || 0
  const volumeImbalance = totalBidVolume && totalAskVolume
    ? ((totalBidVolume - totalAskVolume) / (totalBidVolume + totalAskVolume)) * 100
    : 0

  return (
    <Card
      className="depth-chart"
      title={
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <span className="text-lg font-semibold">
              {symbol} Order Book
            </span>
            {orderBookData && (
              <div className="flex items-center space-x-2">
                <Tag color="blue">
                  Spread: {orderBookData.spread.toFixed(precision)}
                </Tag>
                <Tag color="purple">
                  Mid: {orderBookData.midPrice?.toFixed(precision)}
                </Tag>
                <Tag color={volumeImbalance >= 0 ? 'green' : 'red'}>
                  Imbalance: {volumeImbalance >= 0 ? '+' : ''}{volumeImbalance.toFixed(1)}%
                </Tag>
              </div>
            )}
          </div>
          {isPlaying && (
            <div className="flex items-center space-x-1">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-xs text-gray-500">
                Real-time
              </span>
            </div>
          )}
        </div>
      }
      extra={
        <Space>
          <Button
            type="text"
            size="small"
            icon={<SettingOutlined />}
            onClick={() => setShowSettings(!showSettings)}
          />

          <Button
            type="text"
            size="small"
            icon={isPlaying ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
            onClick={() => setIsPlaying(!isPlaying)}
          />

          <Button
            type="text"
            size="small"
            icon={<ReloadOutlined />}
            onClick={handleRefresh}
          />

          {exportOptions.enabled && (
            <Select
              size="small"
              style={{ width: 80 }}
              placeholder="Export"
              onSelect={handleExport}
            >
              {exportOptions.formats.map(format => (
                <Select.Option key={format} value={format}>
                  {format.toUpperCase()}
                </Select.Option>
              ))}
            </Select>
          )}
        </Space>
      }
    >
      {/* Settings Panel */}
      {showSettings && (
        <div className="mb-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <Row gutter={[16, 16]}>
            <Col span={6}>
              <label className="block text-sm font-medium mb-2">
                Depth Levels
              </label>
              <InputNumber
                min={5}
                max={100}
                step={5}
                value={depth}
                onChange={(value) => onDepthChange?.(value || 20)}
                style={{ width: '100%' }}
              />
            </Col>
            <Col span={6}>
              <label className="block text-sm font-medium mb-2">
                Price Precision
              </label>
              <Select
                value={precision}
                onChange={setPrecision}
                style={{ width: '100%' }}
              >
                <Select.Option value={0}>0</Select.Option>
                <Select.Option value={1}>1</Select.Option>
                <Select.Option value={2}>2</Select.Option>
                <Select.Option value={3}>3</Select.Option>
                <Select.Option value={4}>4</Select.Option>
                <Select.Option value={5}>5</Select.Option>
                <Select.Option value={6}>6</Select.Option>
                <Select.Option value={7}>7</Select.Option>
                <Select.Option value={8}>8</Select.Option>
              </Select>
            </Col>
            <Col span={6}>
              <label className="block text-sm font-medium mb-2">
                Show Orders
              </label>
              <Switch
                checked={showOrders}
                onChange={(checked) => {/* Handle toggle */}}
              />
            </Col>
            <Col span={6}>
              <label className="block text-sm font-medium mb-2">
                Show Cumulative
              </label>
              <Switch
                checked={showCumulative}
                onChange={(checked) => {/* Handle toggle */}}
              />
            </Col>
          </Row>
        </div>
      )}

      {/* Depth Chart */}
      <div style={{ height }}>
        {orderBookData ? (
          <Line
            ref={chartRef}
            data={chartData}
            options={chartOptions}
          />
        ) : (
          <div className="flex items-center justify-center h-full text-gray-500">
            <div className="text-center">
              <div className="text-6xl mb-4">📊</div>
              <div>Loading order book data...</div>
            </div>
          </div>
        )}
      </div>

      {/* Order Book Table */}
      {orderBookData && (
        <div className="mt-4">
          <Row gutter={[16, 0]}>
            <Col span={12}>
              <div className="text-sm font-medium mb-2 text-green-500">Bids</div>
              <div className="space-y-1 max-h-40 overflow-y-auto">
                {orderBookData.bids.slice(0, 10).map((bid, i) => (
                  <div key={i} className="flex justify-between text-xs">
                    <span className="text-green-500">
                      {bid.price.toFixed(precision)}
                    </span>
                    <span>{bid.amount.toFixed(4)}</span>
                    <span>{bid.total.toLocaleString()}</span>
                  </div>
                ))}
              </div>
            </Col>
            <Col span={12}>
              <div className="text-sm font-medium mb-2 text-red-500">Asks</div>
              <div className="space-y-1 max-h-40 overflow-y-auto">
                {orderBookData.asks.slice(0, 10).map((ask, i) => (
                  <div key={i} className="flex justify-between text-xs">
                    <span className="text-red-500">
                      {ask.price.toFixed(precision)}
                    </span>
                    <span>{ask.amount.toFixed(4)}</span>
                    <span>{ask.total.toLocaleString()}</span>
                  </div>
                ))}
              </div>
            </Col>
          </Row>
        </div>
      )}
    </Card>
  )
}

export default DepthChart