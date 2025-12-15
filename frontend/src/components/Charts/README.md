# Chart Library Documentation

## 概述

这是一个强大的 React 图表库，专为 CBSC 量化交易系统设计，提供丰富的数据可视化功能。该库基于 Chart.js 和 Plotly.js 构建，支持实时数据更新、主题切换、导出功能等高级特性。

## 目录

- [安装](#安装)
- [快速开始](#快速开始)
- [API 文档](#api-文档)
- [主题系统](#主题系统)
- [实时数据集成](#实时数据集成)
- [高级功能](#高级功能)
- [测试](#测试)
- [最佳实践](#最佳实践)
- [故障排除](#故障排除)
- [贡献指南](#贡献指南)

## 安装

### 依赖要求

确保您的项目中已安装以下依赖：

```bash
# Chart.js 及相关依赖
npm install chart.js@^4.5.1 react-chartjs-2@^5.3.1
npm install chartjs-adapter-date-fns@^3.0.0
npm install chartjs-plugin-annotation@^3.1.0 chartjs-plugin-zoom@^2.2.0

# Plotly.js
npm install plotly.js@^3.3.1 react-plotly.js@^2.6.0

# 实用工具
npm install html2canvas date-fns
npm install socket.io-client@^4.7.4  # 用于实时数据
```

### 类型定义

```bash
# 如果需要额外的类型定义
npm install --save-dev @types/chart.js
```

## 快速开始

### 1. 导入组件

```tsx
import React from 'react'
import {
  ChartManagerProvider,
  LineChart,
  CandlestickChart,
  ChartsDashboard
} from '@/components/Charts'
```

### 2. 基础折线图

```tsx
import { LineChartData } from '@/types/chart'

const data: LineChartData = {
  labels: ['一月', '二月', '三月', '四月', '五月'],
  datasets: [
    {
      label: '收益',
      data: [12, 19, 3, 5, 2],
      borderColor: '#1890ff',
      backgroundColor: 'rgba(24, 144, 255, 0.1)',
      tension: 0.4
    },
    {
      label: '基准',
      data: [8, 12, 6, 7, 4],
      borderColor: '#52c41a',
      backgroundColor: 'rgba(82, 196, 26, 0.1)',
      tension: 0.4
    }
  ]
}

function BasicLineChart() {
  return (
    <LineChart
      data={data}
      height={400}
      options={{
        responsive: true,
        plugins: {
          legend: {
            position: 'top'
          }
        }
      }}
    />
  )
}
```

### 3. 使用 ChartManager Provider

```tsx
function App() {
  return (
    <ChartManagerProvider>
      <MyCharts />
    </ChartManagerProvider>
  )
}

function MyCharts() {
  const { enableRealTimeUpdates } = useChartManager()

  React.useEffect(() => {
    enableRealTimeUpdates(true)
  }, [enableRealTimeUpdates])

  return (
    <ChartsDashboard
      strategies={strategies}
      height={600}
      showControls={true}
    />
  )
}
```

### 4. 实时数据图表

```tsx
import { useRealTimeChart } from '@/components/Charts/hooks/useRealTimeChart'

function RealTimeLineChart() {
  const { data, isConnected, isPaused, pause, resume } = useRealTimeChart({
    channel: 'strategy-performance',
    maxDataPoints: 100,
    updateInterval: 1000
  })

  const chartData: LineChartData = {
    labels: data.map(d => new Date(d.timestamp).toLocaleTimeString()),
    datasets: [
      {
        label: '实时收益',
        data: data.map(d => d.value),
        borderColor: '#1890ff',
        backgroundColor: 'rgba(24, 144, 255, 0.1)',
        tension: 0.4
      }
    ]
  }

  return (
    <div>
      <div className="flex gap-2 mb-4">
        <button
          onClick={isPaused ? resume : pause}
          className={`px-4 py-2 rounded ${
            isPaused ? 'bg-green-500' : 'bg-yellow-500'
          } text-white`}
        >
          {isPaused ? '恢复' : '暂停'}
        </button>
        <span className={`px-3 py-2 rounded ${
          isConnected ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
        }`}>
          {isConnected ? '已连接' : '未连接'}
        </span>
      </div>
      <LineChart data={chartData} height={400} />
    </div>
  )
}
```

## API 文档

### Chart.js 组件

#### LineChart

折线图组件，支持时间序列、区域填充等功能。

```tsx
interface LineChartProps extends Omit<BaseChartProps<'line'>, 'type'> {
  timeSeries?: boolean      // 是否为时间序列
  areaFill?: boolean        // 是否填充区域
  stepped?: 'before' | 'after' | 'middle' | boolean
  tension?: number          // 曲线张力 (0-1)
  pointRadius?: number      // 数据点半径
  pointHoverRadius?: number // 悬停时数据点半径
  borderWidth?: number      // 线条宽度
  showGrid?: boolean        // 是否显示网格
  gridColor?: string        // 网格颜色
  animationDuration?: number // 动画持续时间
}
```

**示例：**

```tsx
<LineChart
  data={data}
  height={400}
  timeSeries={true}
  areaFill={true}
  tension={0.4}
  showGrid={true}
  onDataPointClick={(point, element) => {
    console.log('Clicked:', point, element)
  }}
/>
```

#### BarChart

柱状图组件，支持分组、堆叠等模式。

```tsx
interface BarChartProps extends Omit<BaseChartProps<'bar'>, 'type'> {
  stacked?: boolean         // 是否堆叠
  barPercentage?: number    // 柱子宽度占比
  categoryPercentage?: number // 分类宽度占比
  showValues?: boolean      // 是否显示数值
}
```

**示例：**

```tsx
<BarChart
  data={data}
  height={400}
  stacked={false}
  barPercentage={0.8}
  showValues={true}
/>
```

#### PieChart

饼图组件，支持环形图、自定义标签等。

```tsx
interface PieChartProps extends Omit<BaseChartProps<'pie'>, 'type'> {
  doughnut?: boolean        // 是否为环形图
  cutout?: number | string  // 环形图中心空白大小
  showLabels?: boolean      // 是否显示标签
  labelPosition?: 'inside' | 'outside' | 'auto'
}
```

**示例：**

```tsx
<PieChart
  data={data}
  height={400}
  doughnut={true}
  cutout="50%"
  showLabels={true}
/>
```

### Plotly.js 组件

#### CandlestickChart

K线图组件，支持成交量、移动平均线、技术指标等。

```tsx
interface CandlestickChartProps {
  data: OHLCDataPoint[]               // OHLC数据
  showVolume?: boolean                // 显示成交量
  showMovingAverages?: number[]       // 移动平均线周期
  indicators?: TechnicalIndicator[]   // 技术指标
  timeRange?: [Date, Date]           // 时间范围
  onTimeRangeChange?: (range: [Date, Date]) => void
  bullishColor?: string              // 上涨颜色
  bearishColor?: string              // 下跌颜色
  volumeOpacity?: number             // 成交量透明度
  showLegend?: boolean               // 显示图例
  title?: string                     // 标题
  subtitle?: string                  // 副标题
}
```

**示例：**

```tsx
<CandlestickChart
  data={ohlcData}
  height={600}
  showVolume={true}
  showMovingAverages={[5, 10, 20]}
  bullishColor="#10b981"
  bearishColor="#ef4444"
  onDataPointClick={(point) => {
    console.log('Candle clicked:', point)
  }}
/>
```

#### Heatmap

热力图组件，用于数据相关性或密度可视化。

```tsx
interface HeatmapProps {
  data: HeatmapData[]      // 热力图数据
  colorScale?: string[]    // 颜色刻度
  height?: number
  showColorscale?: boolean // 显示颜色条
  reversescale?: boolean   // 反转颜色刻度
}
```

**示例：**

```tsx
<Heatmap
  data={correlationData}
  height={500}
  colorScale={['#313695', '#4575b4', '#74add1', '#abd9e9', '#e0f3f8', '#ffffbf', '#fee090', '#fdae61', '#f46d43', '#d73027', '#a50026']}
  showColorscale={true}
/>
```

### 通用组件

#### ChartContainer

所有图表的容器组件，提供加载状态、错误处理等功能。

```tsx
interface ChartContainerProps {
  title?: string
  subtitle?: string
  loading?: boolean
  error?: string
  actions?: React.ReactNode
  className?: string
  children: React.ReactNode
}
```

**示例：**

```tsx
<ChartContainer
  title="策略收益"
  subtitle="最近30天表现"
  loading={isLoading}
  actions={
    <button onClick={exportChart}>
      导出
    </button>
  }
>
  <LineChart data={data} />
</ChartContainer>
```

#### ChartToolbar

图表工具栏，提供导出、刷新、全屏等功能。

```tsx
interface ChartToolbarProps {
  onExport?: (format: string) => void
  onRefresh?: () => void
  onFullscreen?: () => void
  showExport?: boolean
  showRefresh?: boolean
  showFullscreen?: boolean
}
```

### Hooks

#### useRealTimeChart

实时数据管理 Hook。

```tsx
interface RealTimeChartConfig {
  url?: string              // WebSocket URL
  channel?: string          // 数据频道
  maxDataPoints?: number    // 最大数据点数
  updateInterval?: number   // 更新间隔(ms)
  autoReconnect?: boolean   // 自动重连
  reconnectDelay?: number   // 重连延迟
}

// 返回值
interface UseRealTimeChartReturn {
  data: RealTimeDataPoint[]
  isConnected: boolean
  isPaused: boolean
  error: string | null
  lastUpdate: Date | null
  pause: () => void
  resume: () => void
  clear: () => void
  reconnect: () => void
}
```

#### useChartExport

图表导出 Hook。

```tsx
interface ExportConfig {
  filename?: string
  format?: 'png' | 'svg' | 'csv' | 'json'
  quality?: number
  scale?: number
}

// 使用示例
const chartRef = useRef<HTMLDivElement>(null)
const { isExporting, exportChart } = useChartExport(chartRef)

// 导出图表
await exportChart({
  filename: 'my-chart',
  format: 'png',
  quality: 0.95,
  scale: 2
})
```

## 主题系统

### 内置主题

```tsx
import {
  themes,
  squareLightTheme,
  darkTheme,
  cbscTheme,
  getTheme
} from '@/components/Charts/utils/chartThemes'

// 使用主题
const chartTheme = getTheme('dark')
```

#### 1. Square Light Theme

默认的浅色主题，适合明亮环境。

```tsx
const lightTheme = {
  backgroundColor: 'transparent',
  borderColor: '#e8e8e8',
  gridColor: '#f0f0f0',
  textColor: '#262626',
  colors: [
    '#1890ff', '#52c41a', '#faad14', '#f5222d',
    '#722ed1', '#13c2c2', '#eb2f96', '#fa8c16'
  ]
}
```

#### 2. Dark Theme

深色主题，适合暗光环境。

```tsx
const darkTheme = {
  backgroundColor: '#141414',
  borderColor: '#434343',
  gridColor: '#303030',
  textColor: '#ffffff',
  colors: [
    '#177ddc', '#49aa19', '#d89614', '#dc4446',
    '#642ab5', '#39a9c9', '#d32029', '#cf1322'
  ]
}
```

#### 3. CBSC Brand Theme

品牌主题，使用 CBSC 配色方案。

```tsx
const cbscTheme = {
  backgroundColor: 'transparent',
  borderColor: '#d9d9d9',
  gridColor: '#f5f5f5',
  textColor: '#333333',
  colors: [
    '#2f54eb', '#52c41a', '#fa8c16', '#ff4d4f',
    '#722ed1', '#13c2c2', '#eb2f96', '#faad14'
  ]
}
```

### 自定义主题

```tsx
import { ChartTheme } from '@/types/chart'

const customTheme: ChartTheme = {
  backgroundColor: '#ffffff',
  borderColor: '#d0d0d0',
  gridColor: '#f5f5f5',
  textColor: '#333333',
  colors: [
    '#6366f1', '#8b5cf6', '#ec4899', '#f43f5e',
    '#f59e0b', '#10b981', '#14b8a6', '#06b6d4'
  ],
  fontFamily: 'Inter, sans-serif',
  fontSize: 12
}

// 应用自定义主题
<LineChart
  data={data}
  theme="custom"
  options={{
    // 主题会自动应用到图表
  }}
/>
```

### 主题切换

```tsx
import { useState } from 'react'

function ThemedChart() {
  const [theme, setTheme] = useState<'light' | 'dark'>('light')

  return (
    <div>
      <button
        onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}
        className="mb-4 px-4 py-2 bg-blue-500 text-white rounded"
      >
        切换主题
      </button>
      <LineChart
        data={data}
        theme={theme}
        height={400}
      />
    </div>
  )
}
```

## 实时数据集成

### WebSocket 连接

```tsx
import { useRealTimeChart } from '@/components/Charts/hooks/useRealTimeChart'

function RealtimeChart() {
  const { data, isConnected, error } = useRealTimeChart({
    url: 'ws://localhost:3003',
    channel: 'real-time-data',
    maxDataPoints: 200,
    updateInterval: 500
  })

  if (error) {
    return <div className="text-red-500">连接错误: {error}</div>
  }

  return (
    <LineChart
      data={{
        labels: data.map(d => new Date(d.timestamp).toLocaleTimeString()),
        datasets: [{
          label: '实时数据',
          data: data.map(d => d.value),
          borderColor: isConnected ? '#10b981' : '#6b7280'
        }]
      }}
      height={400}
    />
  )
}
```

### 批量数据更新

```tsx
import { useWebSocketChannel } from '@/components/Charts/hooks/useWebSocketChannel'

function BatchUpdateChart() {
  const [data, setData] = useState<ChartData>(initialData)
  const channel = useWebSocketChannel('batch-updates')

  useEffect(() => {
    channel.on('batch-data', (batchData) => {
      setData(prevData => ({
        ...prevData,
        datasets: prevData.datasets.map((dataset, index) => ({
          ...dataset,
          data: [...dataset.data.slice(-100), ...batchData[index]]
        }))
      }))
    })

    return () => channel.off('batch-data')
  }, [channel])

  return <LineChart data={data} height={400} />
}
```

### 实时性能监控

```tsx
import { useChartPerformance } from '@/components/Charts'

function PerformanceMonitoredChart() {
  const { metrics, isOptimized } = useChartPerformance()

  return (
    <div>
      {!isOptimized && (
        <div className="bg-yellow-100 p-2 mb-2 rounded">
          警告: 图表性能可能需要优化
          <div>渲染时间: {metrics.renderTime}ms</div>
          <div>FPS: {metrics.fps}</div>
        </div>
      )}
      <LineChart data={data} height={400} />
    </div>
  )
}
```

## 高级功能

### 1. 图表导出

```tsx
import { useChartExport } from '@/components/Charts/hooks/useChartExport'

function ExportableChart() {
  const chartRef = useRef<HTMLDivElement>(null)
  const { isExporting, exportChart, exportData } = useChartExport(chartRef)

  const handleExport = async (format: 'png' | 'svg' | 'csv') => {
    if (format === 'csv') {
      await exportData(chartData, {
        filename: 'chart-data',
        format: 'csv'
      })
    } else {
      await exportChart({
        filename: 'chart',
        format,
        quality: 0.95,
        scale: 2
      })
    }
  }

  return (
    <div>
      <div className="flex gap-2 mb-4">
        <button
          onClick={() => handleExport('png')}
          disabled={isExporting}
          className="px-4 py-2 bg-blue-500 text-white rounded disabled:opacity-50"
        >
          {isExporting ? '导出中...' : '导出为 PNG'}
        </button>
        <button
          onClick={() => handleExport('svg')}
          disabled={isExporting}
          className="px-4 py-2 bg-green-500 text-white rounded disabled:opacity-50"
        >
          导出为 SVG
        </button>
        <button
          onClick={() => handleExport('csv')}
          disabled={isExporting}
          className="px-4 py-2 bg-purple-500 text-white rounded disabled:opacity-50"
        >
          导出数据为 CSV
        </button>
      </div>
      <div ref={chartRef}>
        <LineChart data={data} height={400} />
      </div>
    </div>
  )
}
```

### 2. 响应式图表

```tsx
import { useResponsive } from '@/hooks/useResponsive'

function ResponsiveChart() {
  const { isMobile, isTablet } = useResponsive()

  const chartOptions = useMemo(() => ({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: !isMobile,
        position: isTablet ? 'bottom' : 'top' as const
      },
      tooltip: {
        mode: isMobile ? 'nearest' as const : 'index' as const
      }
    },
    scales: {
      x: {
        ticks: {
          maxTicksLimit: isMobile ? 5 : 10
        }
      }
    }
  }), [isMobile, isTablet])

  return (
    <div className="w-full h-[400px]">
      <LineChart
        data={data}
        options={chartOptions}
        height={400}
      />
    </div>
  )
}
```

### 3. 虚拟滚动大数据集

```tsx
import { useVirtualScroll } from '@/hooks/useVirtualScroll'

function VirtualizedChart({ allData }: { allData: ChartData }) {
  const containerRef = useRef<HTMLDivElement>(null)
  const { visibleItems, totalSize, scrollElementProps } = useVirtualScroll({
    itemCount: allData.labels.length,
    itemHeight: 40,
    containerHeight: 400
  })

  const visibleData = useMemo(() => ({
    ...allData,
    labels: allData.labels.slice(
      visibleItems.startIndex,
      visibleItems.endIndex
    ),
    datasets: allData.datasets.map(dataset => ({
      ...dataset,
      data: dataset.data.slice(
        visibleItems.startIndex,
        visibleItems.endIndex
      )
    }))
  }), [allData, visibleItems])

  return (
    <div className="relative">
      <div
        ref={containerRef}
        className="overflow-auto"
        style={{ height: 400 }}
        {...scrollElementProps}
      >
        <div style={{ height: totalSize }}>
          <LineChart
            data={visibleData}
            height={totalSize}
            options={{
              maintainAspectRatio: false,
              animation: false // 禁用动画以提高性能
            }}
          />
        </div>
      </div>
    </div>
  )
}
```

### 4. 图表缩放和平移

```tsx
import { useState } from 'react'
import { ZoomOptions } from 'chart.js'

function ZoomableChart() {
  const [zoomOptions, setZoomOptions] = useState<ZoomOptions>({
    enable: true,
    mode: 'x',
    wheelEnabled: true,
    pinchEnabled: true,
    dragEnabled: true
  })

  const handleResetZoom = () => {
    // 重置缩放
    chartRef.current?.resetZoom()
  }

  const chartOptions = {
    responsive: true,
    plugins: {
      zoom: zoomOptions,
      tooltip: {
        mode: 'index' as const,
        intersect: false
      }
    },
    scales: {
      x: {
        type: 'time' as const,
        time: {
          displayFormats: {
            minute: 'HH:mm',
            hour: 'HH:mm'
          }
        }
      }
    }
  }

  return (
    <div>
      <div className="flex gap-2 mb-4">
        <button
          onClick={handleResetZoom}
          className="px-4 py-2 bg-gray-500 text-white rounded"
        >
          重置缩放
        </button>
        <button
          onClick={() => setZoomOptions(prev => ({
            ...prev,
            enable: !prev.enable
          }))}
          className="px-4 py-2 bg-blue-500 text-white rounded"
        >
          {zoomOptions.enable ? '禁用' : '启用'}缩放
        </button>
      </div>
      <LineChart
        data={data}
        options={chartOptions}
        height={400}
      />
    </div>
  )
}
```

### 5. 自定义插件

```tsx
import { Chart as ChartJS, Plugin } from 'chart.js'

// 创建自定义插件
const customPlugin: Plugin<'line'> = {
  id: 'customAnnotation',
  afterDraw: (chart) => {
    const ctx = chart.ctx
    const xAxis = chart.scales.x
    const yAxis = chart.scales.y

    // 在特定位置绘制标注
    ctx.save()
    ctx.beginPath()
    ctx.moveTo(xAxis.getPixelForValue('2024-01-15'), yAxis.top)
    ctx.lineTo(xAxis.getPixelForValue('2024-01-15'), yAxis.bottom)
    ctx.lineWidth = 2
    ctx.strokeStyle = '#ff0000'
    ctx.stroke()

    // 添加文本标注
    ctx.fillStyle = '#ff0000'
    ctx.font = '12px Arial'
    ctx.fillText(
      '重要事件',
      xAxis.getPixelForValue('2024-01-15') + 10,
      yAxis.top + 20
    )
    ctx.restore()
  }
}

function ChartWithCustomPlugin() {
  // 注册插件
  useEffect(() => {
    ChartJS.register(customPlugin)

    return () => {
      ChartJS.unregister(customPlugin)
    }
  }, [])

  return (
    <LineChart
      data={data}
      options={{
        plugins: {
          // 其他插件配置
        }
      }}
      height={400}
    />
  )
}
```

## 测试

### 单元测试示例

```tsx
import { render, screen } from '@testing-library/react'
import { LineChart } from '@/components/Charts'
import { LineChartData } from '@/types/chart'

describe('LineChart', () => {
  const mockData: LineChartData = {
    labels: ['Jan', 'Feb', 'Mar'],
    datasets: [{
      label: 'Test',
      data: [1, 2, 3],
      borderColor: '#1890ff'
    }]
  }

  test('renders chart correctly', () => {
    render(<LineChart data={mockData} height={400} />)
    expect(screen.getByRole('img')).toBeInTheDocument()
  })

  test('applies custom theme', () => {
    render(
      <LineChart
        data={mockData}
        height={400}
        theme="dark"
      />
    )
    const chart = screen.getByRole('img')
    expect(chart).toHaveStyle('background-color: #141414')
  })

  test('handles click events', () => {
    const handleClick = jest.fn()
    render(
      <LineChart
        data={mockData}
        height={400}
        onDataPointClick={handleClick}
      />
    )

    // 模拟点击
    const chartElement = screen.getByRole('img')
    chartElement.click()

    // 验证回调是否被调用
    expect(handleClick).toHaveBeenCalled()
  })
})
```

### 集成测试

```tsx
import { renderHook, act } from '@testing-library/react'
import { useRealTimeChart } from '@/components/Charts/hooks/useRealTimeChart'

// Mock WebSocket
const mockWebSocket = {
  on: jest.fn(),
  off: jest.fn(),
  emit: jest.fn(),
  close: jest.fn()
}

jest.mock('socket.io-client', () => ({
  io: jest.fn(() => mockWebSocket)
}))

describe('useRealTimeChart', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  test('initializes with empty data', () => {
    const { result } = renderHook(() => useRealTimeChart())

    expect(result.current.data).toEqual([])
    expect(result.current.isConnected).toBe(false)
    expect(result.current.isPaused).toBe(false)
  })

  test('handles pause/resume', () => {
    const { result } = renderHook(() => useRealTimeChart())

    act(() => {
      result.current.pause()
    })
    expect(result.current.isPaused).toBe(true)

    act(() => {
      result.current.resume()
    })
    expect(result.current.isPaused).toBe(false)
  })
})
```

### 性能测试

```tsx
import { performance } from 'perf_hooks'

describe('Chart Performance', () => {
  test('renders large dataset efficiently', async () => {
    const largeData = {
      labels: Array.from({ length: 10000 }, (_, i) => `Point ${i}`),
      datasets: [{
        label: 'Large Dataset',
        data: Array.from({ length: 10000 }, () => Math.random() * 100)
      }]
    }

    const startTime = performance.now()

    render(<LineChart data={largeData} height={400} />)

    const endTime = performance.now()
    const renderTime = endTime - startTime

    // 渲染时间应该在合理范围内（例如小于 1 秒）
    expect(renderTime).toBeLessThan(1000)
  })
})
```

### 运行测试

```bash
# 运行所有图表测试
npm test -- --testPathPattern=Charts

# 运行测试并生成覆盖率报告
npm run test:coverage -- --testPathPattern=Charts

# 运行特定组件测试
npm test -- LineChart.test.tsx

# 监听模式
npm test -- --watch --testPathPattern=Charts
```

## 最佳实践

### 1. 性能优化

```tsx
// ✅ 好的做法：使用 useMemo 缓存数据转换
const optimizedData = useMemo(() => ({
  labels: rawLabels.map(formatLabel),
  datasets: rawDatasets.map(transformDataset)
}), [rawLabels, rawDatasets])

// ✅ 好的做法：使用 React.memo 包装组件
export const MemoizedLineChart = React.memo(LineChart)

// ✅ 好的做法：合理的数据限制
const MAX_DATA_POINTS = 1000
const limitedData = useMemo(() => ({
  ...fullData,
  datasets: fullData.datasets.map(ds => ({
    ...ds,
    data: ds.data.slice(-MAX_DATA_POINTS)
  }))
}), [fullData])

// ❌ 避免的做法：在渲染函数中创建新对象
function BadExample({ data }) {
  return (
    <LineChart
      data={{
        labels: data.map(d => d.label), // 每次渲染都创建新对象
        datasets: data.map(d => ({...d}))
      }}
    />
  )
}
```

### 2. 内存管理

```tsx
// ✅ 清理图表实例
function ChartWithCleanup() {
  const chartRef = useRef<ChartJS>(null)

  useEffect(() => {
    return () => {
      // 组件卸载时销毁图表
      if (chartRef.current) {
        chartRef.current.destroy()
      }
    }
  }, [])

  return <LineChart ref={chartRef} data={data} />
}

// ✅ 清理定时器和事件监听器
function ChartWithTimers() {
  const intervalRef = useRef<NodeJS.Timeout>()

  useEffect(() => {
    intervalRef.current = setInterval(updateChart, 1000)

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [])
}

// ✅ 清理 WebSocket 连接
function RealtimeChartWithCleanup() {
  const socketRef = useRef<Socket | null>(null)

  useEffect(() => {
    socketRef.current = io(url)

    return () => {
      socketRef.current?.disconnect()
    }
  }, [])
}
```

### 3. 错误处理

```tsx
// ✅ 优雅的错误处理
function SafeChart({ data }: { data: ChartData }) {
  const [error, setError] = useState<string | null>(null)

  if (!data || !data.datasets || data.datasets.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 bg-gray-100 rounded">
        <p className="text-gray-500">没有可显示的数据</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64 bg-red-50 rounded">
        <p className="text-red-500">图表加载失败: {error}</p>
      </div>
    )
  }

  try {
    return <LineChart data={data} height={400} />
  } catch (err) {
    setError(err.message)
    return null
  }
}

// ✅ 边界值检查
function validateChartData(data: ChartData): boolean {
  if (!data.labels || data.labels.length === 0) return false
  if (!data.datasets || data.datasets.length === 0) return false

  for (const dataset of data.datasets) {
    if (!dataset.data || dataset.data.length === 0) return false
    if (dataset.data.length !== data.labels.length) return false
  }

  return true
}
```

### 4. 可访问性

```tsx
// ✅ 添加 ARIA 标签
function AccessibleChart({ data, title }: { data: ChartData; title: string }) {
  return (
    <div role="img" aria-label={`${title} 图表`}>
      <LineChart
        data={data}
        options={{
          plugins: {
            legend: {
              labels: {
                generateLabels: (chart) => {
                  // 为屏幕阅读器生成描述性标签
                  return chart.data.datasets.map((dataset, i) => ({
                    text: `${dataset.label} 数据`,
                    fillStyle: dataset.backgroundColor,
                    datasetIndex: i
                  }))
                }
              }
            },
            tooltip: {
              callbacks: {
                label: (context) => {
                  // 提供有意义的工具提示
                  return `${context.dataset.label}: ${context.parsed.y} (${context.label})`
                }
              }
            }
          }
        }}
      />
      {/* 提供数据表格作为备选 */}
      <table className="sr-only">
        <caption>{title}</caption>
        <thead>
          <tr>
            {data.labels.map(label => (
              <th key={label}>{label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.datasets.map(dataset => (
            <tr key={dataset.label}>
              <th>{dataset.label}</th>
              {dataset.data.map((value, i) => (
                <td key={i}>{value}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
```

### 5. 类型安全

```tsx
// ✅ 使用 TypeScript 接口
interface StrategyPerformanceChartProps {
  strategies: Strategy[]
  timeRange: TimeRange
  showBenchmark?: boolean
  onDataPointClick?: (point: DataPoint, strategy: Strategy) => void
}

// ✅ 使用泛型确保类型安全
function GenericChart<T extends ChartType>({
  type,
  data,
  options
}: {
  type: T
  data: ChartData<T>
  options?: ChartOptions<T>
}) {
  return <Chart type={type} data={data} options={options} />
}

// ✅ 使用类型守卫
function isTimeSeriesData(data: any[]): data is TimeSeriesDataPoint[] {
  return data.every(
    point =>
      typeof point.timestamp !== 'undefined' &&
      typeof point.value !== 'undefined'
  )
}
```

## 故障排除

### 常见问题

#### 1. 图表不显示

**问题：** 图表渲染空白或容器高度为 0

**解决方案：**

```tsx
// 确保容器有明确的高度
<div style={{ height: '400px', width: '100%' }}>
  <LineChart data={data} />
</div>

// 或者使用 CSS 类
.chart-container {
  height: 400px;
  width: 100%;
  position: relative;
}

// 检查数据格式
if (!data || !data.datasets || data.datasets.length === 0) {
  console.error('Invalid chart data')
  return
}
```

#### 2. 实时更新不工作

**问题：** WebSocket 连接失败或数据不更新

**解决方案：**

```tsx
// 检查连接状态
const { isConnected, error } = useRealTimeChart()

useEffect(() => {
  if (!isConnected) {
    console.error('WebSocket not connected:', error)
  }
}, [isConnected, error])

// 确保在 ChartManagerProvider 内
<ChartManagerProvider>
  <MyChartComponent />
</ChartManagerProvider>

// 检查频道名称是否正确
const { data } = useRealTimeChart({
  channel: 'strategy-updates', // 确保与后端一致
  maxDataPoints: 100
})
```

#### 3. 性能问题

**问题：** 大数据集导致卡顿

**解决方案：**

```tsx
// 启用数据采样
import { sampleData } from '@/utils/dataSampling'

const sampledData = useMemo(
  () => sampleData(originalData, 1000), // 限制到 1000 个点
  [originalData]
)

// 禁用动画
<LineChart
  data={sampledData}
  options={{
    animation: false,
    responsive: true,
    maintainAspectRatio: false
  }}
/>

// 使用虚拟滚动
<VirtualizedChart allData={hugeDataset} />
```

#### 4. 主题不生效

**问题：** 自定义主题颜色未应用

**解决方案：**

```tsx
// 确保正确导入主题
import { getTheme, themes } from '@/components/Charts/utils/chartThemes'

// 应用主题到选项
const chartOptions = {
  plugins: {
    legend: {
      labels: {
        color: getTheme(theme).textColor
      }
    }
  },
  scales: {
    x: {
      grid: {
        color: getTheme(theme).gridColor
      },
      ticks: {
        color: getTheme(theme).textColor
      }
    }
  }
}

// 或者使用默认配置
import { getChartJsDefaults } from '@/components/Charts/utils/chartThemes'

const options = {
  ...getChartJsDefaults(theme),
  // 自定义选项
}
```

#### 5. 导出功能失败

**问题：** 图表导出时出错

**解决方案：**

```tsx
// 确保 ref 正确设置
const chartRef = useRef<HTMLDivElement>(null)

// 检查元素是否存在
const exportChart = async () => {
  if (!chartRef.current) {
    console.error('Chart ref is null')
    return
  }

  try {
    await exportAsImage(chartRef.current, 'chart.png')
  } catch (error) {
    console.error('Export failed:', error)
  }
}

// 对于 Plotly 图表，使用内置导出功能
const plotlyConfig = {
  toImageButtonOptions: {
    format: 'png',
    filename: 'my-chart',
    height: 600,
    width: 1000,
    scale: 1
  }
}

<Plot data={plotlyData} config={plotlyConfig} />
```

### 调试技巧

```tsx
// 1. 启用调试模式
import { Chart } from 'chart.js'

// Chart.js 调试
Chart.defaults.debug = true

// 2. 使用 React DevTools
// 安装 React DevTools 浏览器扩展来检查组件状态

// 3. 性能分析
function DebuggableChart({ data }: { data: ChartData }) {
  const renderCount = useRef(0)
  renderCount.current++

  console.log(`Chart rendered ${renderCount.current} times`)

  return <LineChart data={data} />
}

// 4. 网络调试
// 在浏览器开发者工具中：
// - Network 标签页检查 WebSocket 连接
// - Console 查看错误信息
// - Performance 标签页分析渲染性能

// 5. 使用 React Query DevTools
// 如果使用 React Query 管理数据
import { ReactQueryDevtools } from 'react-query/devtools'

function App() {
  return (
    <>
      <MyCharts />
      <ReactQueryDevtools initialIsOpen={false} />
    </>
  )
}
```

## 贡献指南

### 开发环境设置

1. **Fork 仓库**
   ```bash
   git clone https://github.com/your-username/cbsc-frontend.git
   cd cbsc-frontend
   ```

2. **安装依赖**
   ```bash
   npm install
   ```

3. **启动开发服务器**
   ```bash
   npm run dev
   ```

4. **运行测试**
   ```bash
   npm test
   ```

### 代码规范

1. **TypeScript**
   - 使用严格模式
   - 为所有公共 API 提供类型定义
   - 避免使用 `any` 类型

2. **代码风格**
   - 使用 ESLint 和 Prettier
   - 遵循项目的命名约定
   - 组件使用 PascalCase
   - 文件名使用 kebab-case 或 PascalCase

3. **提交规范**
   ```bash
   # 提交格式
   git commit -m "feat: 添加新的图表类型"
   git commit -m "fix: 修复实时数据更新问题"
   git commit -m "docs: 更新 API 文档"
   git commit -m "test: 添加组件测试"
   ```

### 添加新图表组件

1. **创建组件文件**
   ```bash
   # Chart.js 组件
   touch src/components/Charts/chartjs/NewChart.tsx

   # Plotly 组件
   touch src/components/Charts/plotly/NewChart.tsx
   ```

2. **实现组件**
   ```tsx
   // src/components/Charts/chartjs/NewChart.tsx
   import React from 'react'
   import { BaseChartProps } from '../../../types/chart'

   export interface NewChartProps extends BaseChartProps<'new'> {
     // 特定属性
   }

   export const NewChart: React.FC<NewChartProps> = ({
     data,
     options = {},
     ...props
   }) => {
     return (
       // 实现
     )
   }
   ```

3. **导出组件**
   ```tsx
   // src/components/Charts/index.ts
   export { NewChart } from '../Charts/chartjs/NewChart'
   ```

4. **添加测试**
   ```tsx
   // src/components/Charts/__tests__/NewChart.test.tsx
   import { render, screen } from '@testing-library/react'
   import { NewChart } from '../chartjs/NewChart'

   describe('NewChart', () => {
     test('renders correctly', () => {
       render(<NewChart data={mockData} />)
       // 测试
     })
   })
   ```

5. **更新文档**
   - 更新本 README 文件
   - 添加 API 文档
   - 提供使用示例

### 性能优化贡献

1. **识别瓶颈**
   - 使用 Chrome DevTools Performance
   - 分析组件渲染次数
   - 检查内存使用

2. **优化建议**
   - 使用 `React.memo` 包装组件
   - 实现数据采样算法
   - 优化大数据集渲染
   - 实现图表懒加载

3. **提交优化**
   ```bash
   git commit -m "perf: 优化大数据集渲染性能"
   ```

### 报告问题

1. **Bug 报告**
   - 使用 GitHub Issues
   - 提供最小复现示例
   - 包含错误日志
   - 说明浏览器和环境信息

2. **功能请求**
   - 详细描述需求
   - 提供使用场景
   - 考虑向后兼容性

### 版本发布

1. **更新版本号**
   ```bash
   npm version patch  # 修复版本
   npm version minor  # 新功能
   npm version major  # 破坏性更新
   ```

2. **更新 CHANGELOG**
   ```markdown
   ## [1.2.0] - 2024-01-15

   ### Added
   - 新增热力图组件
   - 支持自定义主题

   ### Fixed
   - 修复实时数据更新问题

   ### Changed
   - 优化大数据集性能
   ```

3. **创建发布**
   ```bash
   git tag v1.2.0
   git push origin v1.2.0
   ```

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](../../../LICENSE) 文件。

## 更多资源

- [Chart.js 官方文档](https://www.chartjs.org/docs/)
- [Plotly.js 文档](https://plotly.com/javascript/)
- [React Chart.js 文档](https://react-chartjs-2.js.org/)
- [React Plotly.js 文档](https://plotly.com/javascript/react/)

## 联系方式

如有问题或建议，请联系：

- 项目维护者：开发团队
- 邮箱：dev-team@cbsc.com
- GitHub Issues：[提交问题](https://github.com/cbsc/frontend/issues)