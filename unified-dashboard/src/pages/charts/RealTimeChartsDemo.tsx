import React, { useState, useEffect } from 'react'
import { Row, Col, Card, Space, Button, Select, Tag } from 'antd'
import {
  LineChartOutlined,
  BarChartOutlined,
  PieChartOutlined,
  SettingOutlined,
  FullscreenOutlined
} from '@ant-design/icons'
import { motion } from 'framer-motion'

// Import real-time chart components
import {
  TechnicalIndicatorChart,
  CandlestickChart,
  DepthChart,
  TechnicalIndicatorsManager,
  RealTimeChartProvider,
  useChart,
  ChartPerformanceMonitor,
  type IndicatorConfig,
  type PerformanceMetrics
} from '../../components/Charts'

// Mock data generator
const generateMockOHLC = (count: number = 100) => {
  const data = []
  let basePrice = 50000
  const now = new Date()

  for (let i = count - 1; i >= 0; i--) {
    const timestamp = new Date(now.getTime() - i * 60000) // 1 minute intervals

    const volatility = 0.02
    const change = (Math.random() - 0.5) * volatility

    const open = basePrice
    const close = basePrice * (1 + change)
    const high = Math.max(open, close) * (1 + Math.random() * 0.01)
    const low = Math.min(open, close) * (1 - Math.random() * 0.01)
    const volume = 1000000 + Math.random() * 9000000

    data.push({
      timestamp,
      open,
      high,
      low,
      close,
      volume
    })

    basePrice = close
  }

  return data
}

const RealTimeChartsDemo: React.FC = () => {
  const [symbol, setSymbol] = useState('BTC/USDT')
  const [timeframe, setTimeframe] = useState('1h')
  const [activeIndicators, setActiveIndicators] = useState<IndicatorConfig[]>([
    {
      id: 'sma-20',
      indicatorId: 'sma',
      name: 'SMA (20)',
      parameters: { period: 20 },
      enabled: true,
      color: '#10B981',
      style: 'line',
      width: 2,
      opacity: 0.8,
      visible: true
    },
    {
      id: 'ema-50',
      indicatorId: 'ema',
      name: 'EMA (50)',
      parameters: { period: 50 },
      enabled: true,
      color: '#F59E0B',
      style: 'line',
      width: 2,
      opacity: 0.8,
      visible: true
    }
  ])
  const [showPerformanceMonitor, setShowPerformanceMonitor] = useState(true)
  const [chartData, setChartData] = useState(generateMockOHLC(200))

  // Mock performance metrics
  const [performanceMetrics, setPerformanceMetrics] = useState<PerformanceMetrics>({
    fps: 60,
    renderTime: 12,
    dataPoints: 200,
    memoryUsage: 45 * 1024 * 1024,
    updateFrequency: 60,
    droppedFrames: 0,
    lastUpdate: new Date()
  })

  // Simulate real-time updates
  useEffect(() => {
    const interval = setInterval(() => {
      setChartData(prev => {
        const newData = [...prev.slice(1)]
        const lastCandle = newData[newData.length - 1]

        const newCandle = {
          timestamp: new Date(),
          open: lastCandle.close,
          high: lastCandle.close * (1 + Math.random() * 0.01),
          low: lastCandle.close * (1 - Math.random() * 0.01),
          close: lastCandle.close * (1 + (Math.random() - 0.5) * 0.02),
          volume: 1000000 + Math.random() * 9000000
        }

        newData.push(newCandle)
        return newData
      })

      // Update performance metrics
      setPerformanceMetrics(prev => ({
        ...prev,
        fps: 55 + Math.random() * 10,
        renderTime: 10 + Math.random() * 10,
        memoryUsage: prev.memoryUsage + (Math.random() - 0.5) * 1000000,
        updateFrequency: 58 + Math.random() * 4,
        droppedFrames: Math.random() > 0.95 ? prev.droppedFrames + 1 : prev.droppedFrames,
        lastUpdate: new Date()
      }))
    }, 1000)

    return () => clearInterval(interval)
  }, [])

  // Indicator handlers
  const handleIndicatorAdd = (config: IndicatorConfig) => {
    setActiveIndicators(prev => [...prev, config])
  }

  const handleIndicatorUpdate = (id: string, updates: Partial<IndicatorConfig>) => {
    setActiveIndicators(prev =>
      prev.map(ind => ind.id === id ? { ...ind, ...updates } : ind)
    )
  }

  const handleIndicatorRemove = (id: string) => {
    setActiveIndicators(prev => prev.filter(ind => ind.id !== id))
  }

  const handleIndicatorToggle = (id: string) => {
    setActiveIndicators(prev =>
      prev.map(ind => ind.id === id ? { ...ind, visible: !ind.visible } : ind)
    )
  }

  const optimizePerformance = () => {
    console.log('Optimizing performance...')
    // Implementation for performance optimization
  }

  return (
    <RealTimeChartProvider>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5 }}
        className="p-6"
      >
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold mb-2">Real-Time Chart Components</h1>
          <p className="text-gray-600">
            High-performance real-time charts supporting 477 technical indicators
          </p>
        </div>

        {/* Controls */}
        <Card className="mb-4">
          <Space wrap>
            <Select
              value={symbol}
              onChange={setSymbol}
              style={{ width: 120 }}
              options={[
                { label: 'BTC/USDT', value: 'BTC/USDT' },
                { label: 'ETH/USDT', value: 'ETH/USDT' },
                { label: 'BNB/USDT', value: 'BNB/USDT' }
              ]}
            />

            <Select
              value={timeframe}
              onChange={setTimeframe}
              style={{ width: 100 }}
              options={[
                { label: '1m', value: '1m' },
                { label: '5m', value: '5m' },
                { label: '15m', value: '15m' },
                { label: '1h', value: '1h' },
                { label: '4h', value: '4h' },
                { label: '1d', value: '1d' }
              ]}
            />

            <Tag color="blue">
              Active Indicators: {activeIndicators.filter(i => i.visible).length}
            </Tag>

            <Tag color="green">
              Data Points: {chartData.length}
            </Tag>

            <Button
              icon={<SettingOutlined />}
              onClick={() => setShowPerformanceMonitor(!showPerformanceMonitor)}
            >
              {showPerformanceMonitor ? 'Hide' : 'Show'} Performance
            </Button>
          </Space>
        </Card>

        {/* Performance Monitor */}
        {showPerformanceMonitor && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="mb-4"
          >
            <ChartPerformanceMonitor
              visible={showPerformanceMonitor}
              metrics={performanceMetrics}
              onOptimize={optimizePerformance}
            />
          </motion.div>
        )}

        {/* Main Charts */}
        <Row gutter={[16, 16]}>
          {/* Candlestick Chart */}
          <Col xs={24} lg={16}>
            <motion.div
              initial={{ x: -50, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              transition={{ delay: 0.1 }}
            >
              <CandlestickChart
                symbol={symbol}
                data={chartData}
                timeframe={timeframe}
                height={500}
                showVolume={true}
                showMA={true}
                maPeriods={[20, 50, 200]}
                realTime={true}
              />
            </motion.div>
          </Col>

          {/* Depth Chart */}
          <Col xs={24} lg={8}>
            <motion.div
              initial={{ x: 50, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              transition={{ delay: 0.2 }}
            >
              <DepthChart
                symbol={symbol}
                depth={20}
                height={500}
                realTime={true}
                showOrders={true}
                showCumulative={true}
              />
            </motion.div>
          </Col>

          {/* Technical Indicator Chart */}
          <Col xs={24} lg={16}>
            <motion.div
              initial={{ y: 50, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.3 }}
            >
              <TechnicalIndicatorChart
                symbol={symbol}
                timeframe={timeframe}
                indicators={activeIndicators}
                priceData={chartData}
                height={400}
                showVolume={true}
                realTime={true}
                onIndicatorChange={setActiveIndicators}
              />
            </motion.div>
          </Col>

          {/* Technical Indicators Manager */}
          <Col xs={24} lg={8}>
            <motion.div
              initial={{ y: 50, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.4 }}
            >
              <TechnicalIndicatorsManager
                symbol={symbol}
                timeframe={timeframe}
                activeIndicators={activeIndicators}
                onIndicatorAdd={handleIndicatorAdd}
                onIndicatorUpdate={handleIndicatorUpdate}
                onIndicatorRemove={handleIndicatorRemove}
                onIndicatorToggle={handleIndicatorToggle}
              />
            </motion.div>
          </Col>
        </Row>
      </motion.div>
    </RealTimeChartProvider>
  )
}

export default RealTimeChartsDemo