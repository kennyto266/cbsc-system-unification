import React, { useState, useEffect } from 'react'
import {
  ScatterPlot,
  RadarChart,
  HeatmapChart,
  CandlestickChart,
  PerformanceGauge,
  DataTable,
  ChartContainer,
  generateColorPalette,
  formatNumber,
  formatPercentage
} from '../components/charts'

// Sample data generators
const generateScatterData = (points: number = 100) => {
  const data = []
  for (let i = 0; i < points; i++) {
    data.push({
      x: Math.random() * 100,
      y: Math.random() * 100,
      z: Math.random() * 50 + 10,
      label: `Point ${i + 1}`
    })
  }
  return data
}

const generateRadarData = (categories: string[]) => {
  return categories.map(cat => Math.floor(Math.random() * 100))
}

const generateHeatmapData = (rows: number, cols: number) => {
  const data = []
  for (let i = 0; i < rows; i++) {
    for (let j = 0; j < cols; j++) {
      data.push({
        x: i,
        y: j,
        value: Math.random() * 100
      })
    }
  }
  return data
}

const generateOHLCData = (days: number) => {
  const data = []
  let basePrice = 100
  const now = new Date()

  for (let i = 0; i < days; i++) {
    const date = new Date(now)
    date.setDate(date.getDate() - (days - i))

    const open = basePrice
    const volatility = Math.random() * 10 - 5
    const close = open + volatility
    const high = Math.max(open, close) + Math.random() * 5
    const low = Math.min(open, close) - Math.random() * 5
    const volume = Math.floor(Math.random() * 1000000)

    data.push({
      timestamp: date,
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

const generateTableData = (rows: number) => {
  const data = []
  const strategies = ['MA Cross', 'RSI Mean Reversion', 'Bollinger Bands', 'MACD Trend', 'Grid Trading']
  const statuses = ['Active', 'Paused', 'Stopped']

  for (let i = 0; i < rows; i++) {
    const strategy = strategies[Math.floor(Math.random() * strategies.length)]
    const status = statuses[Math.floor(Math.random() * statuses.length)]
    const returnRate = (Math.random() - 0.5) * 50
    const sharpe = Math.random() * 3 - 0.5
    const maxDD = Math.random() * 20

    data.push({
      id: i + 1,
      strategy,
      status,
      returnRate,
      sharpe,
      maxDrawdown: maxDD,
      trades: Math.floor(Math.random() * 1000),
      winRate: Math.random() * 100,
      lastUpdate: new Date()
    })
  }

  return data
}

// Example components
export const ScatterPlotExample: React.FC = () => {
  const [data, setData] = useState(() => generateScatterData(200))

  return (
    <ChartContainer
      title="策略風險收益散點圖"
      subtitle="X軸：風險（波動率）| Y軸：收益率"
      description="點的大小代表資產規模，點的顏色代表不同類別"
      toolbar={{
        enabled: true,
        showFullscreen: true,
        showDownload: true
      }}
      width={800}
      height={500}
    >
      <ScatterPlot
        data={data}
        xAxis={{
          label: '風險（年化波動率%）',
          min: 0,
          max: 40,
          format: (value) => `${value.toFixed(1)}%`
        }}
        yAxis={{
          label: '收益率（%）',
          min: -20,
          max: 30,
          format: (value) => `${value.toFixed(1)}%`
        }}
        showRegression={true}
        clustering={{
          enabled: true,
          algorithm: 'kmeans',
          clusters: 3
        }}
        theme="light"
        onPointClick={(point) => {
          console.log('Clicked point:', point)
        }}
      />
    </ChartContainer>
  )
}

export const RadarChartExample: React.FC = () => {
  const categories = ['盈利能力', '風險控制', '流動性', '穩定性', '成長性', '效率']

  const datasets = [
    {
      label: '當前策略',
      data: generateRadarData(categories),
      backgroundColor: 'rgba(54, 162, 235, 0.2)',
      borderColor: 'rgba(54, 162, 235, 1)',
      borderWidth: 2
    },
    {
      label: '基準策略',
      data: generateRadarData(categories),
      backgroundColor: 'rgba(255, 99, 132, 0.2)',
      borderColor: 'rgba(255, 99, 132, 1)',
      borderWidth: 2
    },
    {
      label: '優秀策略',
      data: categories.map(() => 85),
      backgroundColor: 'rgba(75, 192, 192, 0.2)',
      borderColor: 'rgba(75, 192, 192, 1)',
      borderWidth: 2,
      borderDash: [5, 5]
    }
  ]

  return (
    <ChartContainer
      title="策略評分雷達圖"
      description="六維度評分體系，滿分100分"
      width={600}
      height={600}
    >
      <RadarChart
        labels={categories}
        datasets={datasets}
        showBenchmark={true}
        benchmarkData={categories.map(() => 70)}
        benchmarkLabel="行業平均"
        fillArea={true}
        theme="light"
      />
    </ChartContainer>
  )
}

export const HeatmapChartExample: React.FC = () => {
  const timeIntervals = ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00']
  const weekdays = ['週一', '週二', '週三', '週四', '週五']

  const data = generateHeatmapData(5, 6)

  return (
    <ChartContainer
      title="交易活躍度熱力圖"
      subtitle="顯示一週內不同時間段的交易頻率"
      width={800}
      height={400}
    >
      <HeatmapChart
        dataset={{
          data,
          colorScale: {
            type: 'sequential',
            colors: ['#f7fafc', '#2d3748'],
            steps: 10
          },
          showLabels: true,
          labelFormat: (value) => value.toFixed(0)
        }}
        xAxis={{
          label: '時間',
          categories: timeIntervals
        }}
        yAxis={{
          label: '星期',
          categories: weekdays
        }}
        showColorScale={true}
        colorScalePosition="right"
        theme="light"
      />
    </ChartContainer>
  )
}

export const CandlestickChartExample: React.FC = () => {
  const [data, setData] = useState(() => generateOHLCData(60))
  const [showVolume, setShowVolume] = useState(true)

  return (
    <ChartContainer
      title="BTC/USDT K線圖"
      subtitle="最近60天走勢"
      toolbar={{
        enabled: true,
        showFullscreen: true,
        showDownload: true,
        showSettings: true,
        customActions: [
          {
            key: 'toggle-volume',
            label: showVolume ? '隱藏成交量' : '顯示成交量',
            onClick: () => setShowVolume(!showVolume),
            tooltip: showVolume ? '隱藏成交量' : '顯示成交量'
          }
        ]
      }}
      width={1000}
      height={600}
    >
      <CandlestickChart
        data={data}
        volumeData={data}
        technicalIndicators={[
          { type: 'SMA', params: { period: 20 }, color: '#ff6384', visible: true },
          { type: 'EMA', params: { period: 50 }, color: '#36a2eb', visible: true },
          { type: 'BB', params: { period: 20 }, visible: true }
        ]}
        showVolume={showVolume}
        volumeHeight={25}
        showGrid={true}
        showCrosshair={true}
        zoomEnabled={true}
        panEnabled={true}
        theme="light"
        onCandleClick={(candle, index) => {
          console.log('Candle clicked:', candle, index)
        }}
      />
    </ChartContainer>
  )
}

export const PerformanceGaugeExample: React.FC = () => {
  const [value, setValue] = useState(75.5)
  const [thresholds] = useState([
    { value: 50, color: '#ef5350', label: '差' },
    { value: 70, color: '#ff9800', label: '中' },
    { value: 90, color: '#66bb6a', label: '優' },
    { value: 100, color: '#26c6da', label: '極佳' }
  ])

  useEffect(() => {
    const timer = setInterval(() => {
      setValue(prev => {
        const change = (Math.random() - 0.5) * 10
        const newValue = prev + change
        return Math.max(0, Math.min(100, newValue))
      })
    }, 3000)

    return () => clearInterval(timer)
  }, [])

  return (
    <ChartContainer
      title="策略當前收益"
      width={300}
      height={300}
    >
      <PerformanceGauge
        value={value}
        min={0}
        max={100}
        thresholds={thresholds}
        unit="%"
        formatValue={(val) => formatNumber(val, { decimals: 2, suffix: '%' })}
        showValue={true}
        showThresholds={true}
        needle={{
          show: true,
          width: 3,
          length: 70,
          color: '#666'
        }}
        theme="light"
      />
    </ChartContainer>
  )
}

export const DataTableExample: React.FC = () => {
  const columns = [
    { id: 'id', Header: 'ID', accessor: 'id', width: 60 },
    { id: 'strategy', Header: '策略名稱', accessor: 'strategy', sortable: true },
    {
      id: 'status',
      Header: '狀態',
      accessor: 'status',
      sortable: true,
      Cell: ({ value }) => (
        <span style={{
          color: value === 'Active' ? '#52c41a' : value === 'Paused' ? '#faad14' : '#ff4d4f'
        }}>
          {value}
        </span>
      )
    },
    {
      id: 'returnRate',
      Header: '收益率',
      accessor: 'returnRate',
      sortable: true,
      align: 'right' as const,
      Cell: ({ value }) => formatPercentage(value / 100, 2, true)
    },
    {
      id: 'sharpe',
      Header: '夏普比率',
      accessor: 'sharpe',
      sortable: true,
      align: 'right' as const,
      Cell: ({ value }) => formatNumber(value, { decimals: 2 })
    },
    {
      id: 'maxDrawdown',
      Header: '最大回撤',
      accessor: 'maxDrawdown',
      sortable: true,
      align: 'right' as const,
      Cell: ({ value }) => formatPercentage(value / 100, 2)
    },
    {
      id: 'trades',
      Header: '交易次數',
      accessor: 'trades',
      sortable: true,
      align: 'right' as const
    },
    {
      id: 'winRate',
      Header: '勝率',
      accessor: 'winRate',
      sortable: true,
      align: 'right' as const,
      Cell: ({ value }) => formatPercentage(value / 100, 1)
    },
    {
      id: 'lastUpdate',
      Header: '最後更新',
      accessor: 'lastUpdate',
      sortable: true,
      Cell: ({ value }) => value.toLocaleString('zh-TW')
    }
  ]

  const data = useState(() => generateTableData(50))[0]

  return (
    <ChartContainer
      title="策略列表"
      toolbar={{
        enabled: true,
        showRefresh: true,
        showDownload: true,
        customActions: [
          {
            key: 'export-excel',
            label: '導出Excel',
            onClick: () => console.log('Export to Excel'),
            tooltip: '導出為Excel文件'
          }
        ]
      }}
      width={1200}
      height={600}
    >
      <DataTable
        columns={columns}
        data={data}
        virtualized={true}
        rowHeight={50}
        maxHeight={500}
        pagination={{
          enabled: true,
          pageSize: 20,
          showSizeChanger: true,
          pageSizeOptions: [10, 20, 50, 100]
        }}
        selection={{
          enabled: true,
          mode: 'multiple',
          onSelect: (selectedRows) => console.log('Selected rows:', selectedRows)
        }}
        sorting={{
          enabled: true,
          defaultSortBy: [{ id: 'returnRate', desc: true }]
        }}
        actions={{
          enabled: true,
          actions: [
            {
              key: 'start',
              label: '啟動',
              onClick: (rows) => console.log('Start strategies:', rows),
              disabled: (rows) => rows.length === 0
            },
            {
              key: 'stop',
              label: '停止',
              onClick: (rows) => console.log('Stop strategies:', rows),
              disabled: (rows) => rows.length === 0
            },
            {
              key: 'delete',
              label: '刪除',
              onClick: (rows) => console.log('Delete strategies:', rows),
              disabled: (rows) => rows.length === 0
            }
          ]
        }}
        export={{
          enabled: true,
          formats: ['csv', 'json', 'excel']
        }}
        onRowClick={(row, index) => {
          console.log('Row clicked:', row, index)
        }}
        theme="light"
      />
    </ChartContainer>
  )
}

// Main example container
export const VisualizationExamples: React.FC = () => {
  const [activeExample, setActiveExample] = useState('scatter')

  const examples = {
    scatter: { component: ScatterPlotExample, title: '散點圖' },
    radar: { component: RadarChartExample, title: '雷達圖' },
    heatmap: { component: HeatmapChartExample, title: '熱力圖' },
    candlestick: { component: CandlestickChartExample, title: 'K線圖' },
    gauge: { component: PerformanceGaugeExample, title: '性能儀表' },
    table: { component: DataTableExample, title: '數據表格' }
  }

  const ActiveComponent = examples[activeExample as keyof typeof examples].component

  return (
    <div style={{ padding: '20px' }}>
      <h1>數據可視化組件示例</h1>

      <div style={{ marginBottom: '20px' }}>
        {Object.entries(examples).map(([key, example]) => (
          <button
            key={key}
            onClick={() => setActiveExample(key)}
            style={{
              padding: '8px 16px',
              marginRight: '10px',
              backgroundColor: activeExample === key ? '#1890ff' : '#f0f0f0',
              color: activeExample === key ? '#fff' : '#000',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            {example.title}
          </button>
        ))}
      </div>

      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
        <ActiveComponent />
      </div>
    </div>
  )
}

export default VisualizationExamples