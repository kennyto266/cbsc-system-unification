import React, { useMemo, useState, useEffect, useRef } from 'react'
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
  TimeScale,
  ChartOptions
} from 'chart.js'
import { Line, Bar } from 'react-chartjs-2'
import { Card, Select, Space, Button, Switch, Tag } from 'antd'
import { DownloadOutlined, LineChartOutlined, PlayCircleOutlined, PauseCircleOutlined } from '@ant-design/icons'
import { Strategy } from '../../types'

// 註冊Chart.js組件
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  TimeScale
)

interface PriceData {
  timestamp: Date
  open: number
  high: number
  low: number
  close: number
  volume: number
}

interface TechnicalIndicator {
  sma: number[]
  ema: number[]
  rsi: number[]
  macd: number[]
  bollinger: {
    upper: number[]
    middle: number[]
    lower: number[]
  }
}

interface RealTimePriceChartProps {
  strategy?: Strategy
  symbol?: string
  timeFrame?: '1m' | '5m' | '15m' | '1h' | '4h' | '1d'
  showVolume?: boolean
  showIndicators?: boolean
  autoUpdate?: boolean
}

const RealTimePriceChart: React.FC<RealTimePriceChartProps> = ({
  strategy,
  symbol = 'BTC/USDT',
  timeFrame = '1h',
  showVolume = true,
  showIndicators = true,
  autoUpdate = true
}) => {
  const [priceData, setPriceData] = useState<PriceData[]>([])
  const [indicators, setIndicators] = useState<TechnicalIndicator | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isPlaying, setIsPlaying] = useState(autoUpdate)
  const intervalRef = useRef<NodeJS.Timeout | null>(null)

  // 生成模擬價格數據
  const generatePriceData = (candles: number = 100): PriceData[] => {
    const data: PriceData[] = []
    const now = new Date()
    let basePrice = 50000 + Math.random() * 10000

    for (let i = candles - 1; i >= 0; i--) {
      const timestamp = new Date(now.getTime() - i * 60 * 60 * 1000) // 假設是1小時時間框架

      const volatility = 0.02
      const trend = Math.random() > 0.5 ? 1 : -1
      const change = (Math.random() - 0.5) * volatility + trend * 0.001

      const open = basePrice
      const close = basePrice * (1 + change)
      const high = Math.max(open, close) * (1 + Math.random() * 0.01)
      const low = Math.min(open, close) * (1 - Math.random() * 0.01)
      const volume = 1000 + Math.random() * 9000

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

  // 計算技術指標
  const calculateIndicators = (data: PriceData[]): TechnicalIndicator => {
    const prices = data.map(d => d.close)
    const periods = 20

    // SMA (簡單移動平均線)
    const sma = []
    for (let i = 0; i < prices.length; i++) {
      if (i < periods - 1) {
        sma.push(NaN)
      } else {
        const sum = prices.slice(i - periods + 1, i + 1).reduce((a, b) => a + b, 0)
        sma.push(sum / periods)
      }
    }

    // EMA (指數移動平均線)
    const ema = []
    const multiplier = 2 / (periods + 1)
    ema[0] = prices[0]
    for (let i = 1; i < prices.length; i++) {
      ema.push((prices[i] - ema[i - 1]) * multiplier + ema[i - 1])
    }

    // RSI (相對強弱指標)
    const rsi = []
    const rsiPeriod = 14
    for (let i = 0; i < prices.length; i++) {
      if (i < rsiPeriod) {
        rsi.push(NaN)
      } else {
        let gains = 0
        let losses = 0
        for (let j = i - rsiPeriod + 1; j <= i; j++) {
          const change = prices[j] - prices[j - 1]
          if (change > 0) gains += change
          else losses -= change
        }
        const avgGain = gains / rsiPeriod
        const avgLoss = losses / rsiPeriod
        const rs = avgGain / avgLoss
        rsi.push(100 - (100 / (1 + rs)))
      }
    }

    // MACD
    const macd = []
    for (let i = 0; i < prices.length; i++) {
      if (i < 26) {
        macd.push(NaN)
      } else {
        const ema12 = ema[i]
        const ema26 = ema[i - 13] // 簡化計算
        macd.push(ema12 - ema26)
      }
    }

    // 布林帶
    const bollinger = {
      upper: [],
      middle: sma.slice(),
      lower: []
    }

    for (let i = 0; i < data.length; i++) {
      if (i < periods - 1) {
        bollinger.upper.push(NaN)
        bollinger.lower.push(NaN)
      } else {
        const slice = prices.slice(i - periods + 1, i + 1)
        const mean = slice.reduce((a, b) => a + b, 0) / slice.length
        const variance = slice.reduce((sum, price) => sum + Math.pow(price - mean, 2), 0) / slice.length
        const stdDev = Math.sqrt(variance)

        bollinger.upper.push(mean + 2 * stdDev)
        bollinger.lower.push(mean - 2 * stdDev)
      }
    }

    return { sma, ema, rsi, macd, bollinger }
  }

  // 初始化數據
  useEffect(() => {
    const data = generatePriceData()
    setPriceData(data)
    setIndicators(calculateIndicators(data))
  }, [])

  // 實時更新
  useEffect(() => {
    if (isPlaying && autoUpdate) {
      intervalRef.current = setInterval(() => {
        setPriceData(prevData => {
          const newData = [...prevData.slice(1)]
          const lastCandle = newData[newData.length - 1]

          const newCandle: PriceData = {
            timestamp: new Date(),
            open: lastCandle.close,
            high: lastCandle.close * (1 + Math.random() * 0.01),
            low: lastCandle.close * (1 - Math.random() * 0.01),
            close: lastCandle.close * (1 + (Math.random() - 0.5) * 0.02),
            volume: 1000 + Math.random() * 9000
          }

          newData.push(newCandle)
          return newData
        })
      }, 5000) // 每5秒更新一次
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [isPlaying, autoUpdate])

  // 更新技術指標
  useEffect(() => {
    if (priceData.length > 0) {
      setIndicators(calculateIndicators(priceData))
    }
  }, [priceData])

  // 價格圖表數據
  const priceChartData = useMemo(() => {
    if (!indicators) return { labels: [], datasets: [] }

    const labels = priceData.map(d =>
      d.timestamp.toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit' })
    )

    const datasets = [
      {
        label: '價格',
        data: priceData.map(d => d.close),
        borderColor: '#3B82F6',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        borderWidth: 2,
        pointRadius: 0,
        pointHoverRadius: 4,
        tension: 0.1
      }
    ]

    if (showIndicators) {
      datasets.push(
        {
          label: 'SMA',
          data: indicators.sma,
          borderColor: '#10B981',
          backgroundColor: 'transparent',
          borderWidth: 1,
          pointRadius: 0,
          borderDash: [5, 5]
        },
        {
          label: 'EMA',
          data: indicators.ema,
          borderColor: '#F59E0B',
          backgroundColor: 'transparent',
          borderWidth: 1,
          pointRadius: 0
        },
        {
          label: '布林帶上軌',
          data: indicators.bollinger.upper,
          borderColor: '#8B5CF6',
          backgroundColor: 'transparent',
          borderWidth: 1,
          pointRadius: 0,
          borderDash: [2, 2]
        },
        {
          label: '布林帶下軌',
          data: indicators.bollinger.lower,
          borderColor: '#8B5CF6',
          backgroundColor: 'rgba(139, 92, 246, 0.1)',
          borderWidth: 1,
          pointRadius: 0,
          borderDash: [2, 2],
          fill: '-1' // 填充到上一個數據集
        }
      )
    }

    return { labels, datasets }
  }, [priceData, indicators, showIndicators])

  // 成交量圖表數據
  const volumeChartData = useMemo(() => {
    const labels = priceData.map(d =>
      d.timestamp.toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit' })
    )

    const volumes = priceData.map(d => d.volume)
    const maxVolume = Math.max(...volumes)

    return {
      labels,
      datasets: [
        {
          label: '成交量',
          data: volumes,
          backgroundColor: priceData.map((d, i) => {
            if (i === 0) return 'rgba(156, 163, 175, 0.6)'
            return d.close >= priceData[i - 1].close
              ? 'rgba(16, 185, 129, 0.6)'
              : 'rgba(239, 68, 68, 0.6)'
          }),
          borderColor: priceData.map((d, i) => {
            if (i === 0) return 'rgba(156, 163, 175, 1)'
            return d.close >= priceData[i - 1].close
              ? 'rgba(16, 185, 129, 1)'
              : 'rgba(239, 68, 68, 1)'
          }),
          borderWidth: 1
        }
      ]
    }
  }, [priceData])

  const priceOptions: ChartOptions<'line'> = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index' as const,
      intersect: false,
    },
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
          usePointStyle: true,
          padding: 10,
          font: {
            size: 11
          }
        }
      },
      title: {
        display: false
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        padding: 12,
        cornerRadius: 8,
        callbacks: {
          label: function(context) {
            const value = context.parsed.y
            return `${context.dataset.label}: $${value.toFixed(2)}`
          }
        }
      }
    },
    scales: {
      x: {
        display: true,
        grid: {
          display: false
        }
      },
      y: {
        display: true,
        position: 'left' as const,
        grid: {
          color: 'rgba(0, 0, 0, 0.05)'
        },
        ticks: {
          callback: function(value) {
            return '$' + (value as number).toLocaleString('zh-TW', {
              minimumFractionDigits: 0,
              maximumFractionDigits: 0
            })
          }
        }
      }
    }
  }

  const volumeOptions: ChartOptions<'bar'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false
      },
      title: {
        display: false
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        padding: 8,
        cornerRadius: 4,
        callbacks: {
          label: function(context) {
            return `成交量: ${(context.parsed.y as number).toLocaleString('zh-TW')}`
          }
        }
      }
    },
    scales: {
      x: {
        display: false
      },
      y: {
        display: true,
        position: 'right' as const,
        grid: {
          color: 'rgba(0, 0, 0, 0.05)'
        },
        ticks: {
          callback: function(value) {
            return (value as number).toLocaleString('zh-TW')
          }
        }
      }
    }
  }

  const handleExport = () => {
    const canvas = document.querySelector('.price-chart canvas')
    if (canvas) {
      const url = canvas.toDataURL('image/png')
      const link = document.createElement('a')
      link.download = `price-chart-${symbol}-${Date.now()}.png`
      link.href = url
      link.click()
    }
  }

  const currentPrice = priceData.length > 0 ? priceData[priceData.length - 1].close : 0
  const priceChange = priceData.length > 1 ?
    ((currentPrice - priceData[priceData.length - 2].close) / priceData[priceData.length - 2].close) * 100 : 0

  return (
    <Card
      title={
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <span className="text-lg font-semibold">
              {symbol} {strategy && `- ${strategy.name}`}
            </span>
            <div className="flex items-center space-x-2">
              <span className="text-xl font-bold">${currentPrice.toFixed(2)}</span>
              <Tag color={priceChange >= 0 ? 'green' : 'red'}>
                {priceChange >= 0 ? '+' : ''}{priceChange.toFixed(2)}%
              </Tag>
            </div>
          </div>
          {isPlaying && (
            <div className="flex items-center space-x-1">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-xs text-gray-500">實時</span>
            </div>
          )}
        </div>
      }
      className="real-time-price-chart-card"
      extra={
        <Space>
          <Select
            value={timeFrame}
            onChange={(value) => console.log('更改時間框架:', value)}
            style={{ width: 80 }}
            size="small"
          >
            <Select.Option value="1m">1分</Select.Option>
            <Select.Option value="5m">5分</Select.Option>
            <Select.Option value="15m">15分</Select.Option>
            <Select.Option value="1h">1小時</Select.Option>
            <Select.Option value="4h">4小時</Select.Option>
            <Select.Option value="1d">1天</Select.Option>
          </Select>
          <div className="flex items-center space-x-2">
            <span className="text-xs text-gray-600">成交量</span>
            <Switch
              size="small"
              checked={showVolume}
              onChange={(checked) => console.log('切換成交量顯示:', checked)}
            />
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-xs text-gray-600">指標</span>
            <Switch
              size="small"
              checked={showIndicators}
              onChange={(checked) => console.log('切換技術指標:', checked)}
            />
          </div>
          <Button
            type="text"
            size="small"
            icon={isPlaying ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
            onClick={() => setIsPlaying(!isPlaying)}
            title={isPlaying ? '暫停' : '播放'}
          />
          <Button
            type="text"
            size="small"
            icon={<DownloadOutlined />}
            onClick={handleExport}
            title="導出圖表"
          />
        </Space>
      }
    >
      <div className="space-y-4">
        {/* 價格圖表 */}
        <div className="price-chart" style={{ height: showVolume ? '300px' : '400px' }}>
          {priceData.length > 0 ? (
            <Line data={priceChartData} options={priceOptions} />
          ) : (
            <div className="flex items-center justify-center h-full text-gray-500">
              <div className="text-center">
                <div className="text-6xl mb-4">📈</div>
                <div>載入中...</div>
              </div>
            </div>
          )}
        </div>

        {/* 成交量圖表 */}
        {showVolume && (
          <div className="volume-chart" style={{ height: '100px' }}>
            {priceData.length > 0 ? (
              <Bar data={volumeChartData} options={volumeOptions} />
            ) : null}
          </div>
        )}
      </div>
    </Card>
  )
}

export default RealTimePriceChart