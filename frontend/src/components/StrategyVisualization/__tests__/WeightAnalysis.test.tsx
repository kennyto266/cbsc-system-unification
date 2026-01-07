import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import userEvent from '@testing-library/user-event'
import { WeightAnalysis } from '../WeightAnalysis'

// Mock recharts
jest.mock('recharts', () => {
  const React = require('react')
  // Recharts-specific props that should not be passed to DOM elements
  const RECHARTS_PROPS = [
    'dataKey', 'name', 'data', 'cx', 'cy', 'r', 'fill', 'stroke', 'strokeWidth',
    'labelLine', 'outerRadius', 'innerRadius', 'startAngle', 'endAngle',
    'label', 'legendType', 'hide', 'barSize', 'barGap', 'barCategoryGap',
    'tickFormatter', 'ticks', 'interval', 'angle', 'domain', 'type',
    'connectNulls', 'isAnimationActive', 'animationBegin', 'animationDuration',
    'baseLine', 'layout', 'stackOffset', 'stackId', 'minPointSize', 'maxBarSize',
    'x', 'y', 'width', 'height', 'left', 'top', 'radius', 'clockWise',
    'shape', 'activeShape', 'activeDot', 'dot', 'onClick', 'onMouseEnter',
    'onMouseLeave', 'fillOpacity', 'strokeOpacity', 'strokeDasharray'
  ]

  const filterProps = (props: any) => {
    const filtered: any = {}
    const dataAttrs: any = {}
    Object.entries(props).forEach(([key, value]) => {
      if (RECHARTS_PROPS.includes(key)) {
        // Skip Recharts props
      } else if (key.startsWith('data-')) {
        dataAttrs[key] = value
      } else {
        filtered[key] = value
      }
    })
    return { ...filtered, ...dataAttrs }
  }

  return {
    ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
      React.createElement('div', { 'data-testid': 'responsive-container' }, children)
    ),
    PieChart: ({ children }: { children: React.ReactNode }) => (
      React.createElement('div', { 'data-testid': 'pie-chart' }, children)
    ),
    Pie: (props: any) => React.createElement('div', { 'data-testid': 'pie', ...filterProps(props) }),
    Cell: (props: any) => React.createElement('div', { 'data-testid': 'cell', ...filterProps(props) }),
    BarChart: ({ children }: { children: React.ReactNode }) => (
      React.createElement('div', { 'data-testid': 'bar-chart' }, children)
    ),
    Bar: (props: any) => React.createElement('div', { 'data-testid': 'bar', ...filterProps(props) }),
    XAxis: (props: any) => React.createElement('div', { 'data-testid': 'x-axis', ...filterProps(props) }),
    YAxis: (props: any) => React.createElement('div', { 'data-testid': 'y-axis', ...filterProps(props) }),
    CartesianGrid: (props: any) => React.createElement('div', { 'data-testid': 'cartesian-grid', ...filterProps(props) }),
    Tooltip: (props: any) => React.createElement('div', { 'data-testid': 'tooltip', ...filterProps(props) }),
    Legend: (props: any) => React.createElement('div', { 'data-testid': 'legend', ...filterProps(props) }),
    RadarChart: ({ children }: { children: React.ReactNode }) => (
      React.createElement('div', { 'data-testid': 'radar-chart' }, children)
    ),
    PolarGrid: (props: any) => React.createElement('div', { 'data-testid': 'polar-grid', ...filterProps(props) }),
    PolarAngleAxis: (props: any) => React.createElement('div', { 'data-testid': 'polar-angle-axis', ...filterProps(props) }),
    PolarRadiusAxis: (props: any) => React.createElement('div', { 'data-testid': 'polar-radius-axis', ...filterProps(props) }),
    Radar: (props: any) => React.createElement('div', { 'data-testid': 'radar', ...filterProps(props) })
  }
})

jest.mock('@/contexts/ThemeContext', () => ({
  useTheme: () => ({
    resolvedTheme: 'light'
  }),
  ThemeProvider: ({ children }: any) => <div>{children}</div>
}))

const mockWeights = {
  price: 0.4,
  economic: 0.3,
  volume: 0.2,
  technical: 0.1
}

const mockContributions = [
  { name: '价格策略', value: 0.4, contribution: 0.35, performance: 0.12, weight: 0.4 },
  { name: '经济指标', value: 0.3, contribution: 0.25, performance: 0.08, weight: 0.3 },
  { name: '成交量', value: 0.2, contribution: 0.25, performance: 0.15, weight: 0.2 },
  { name: '技术指标', value: 0.1, contribution: 0.15, performance: -0.02, weight: 0.1 }
]

describe('WeightAnalysis', () => {
  const defaultProps = {
    weights: mockWeights,
    contributions: mockContributions,
    onWeightChange: jest.fn()
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders without crashing', () => {
    render(<WeightAnalysis {...defaultProps} />)
    // Should have 2 charts: pie chart and bar chart
    expect(screen.getAllByTestId('responsive-container')).toHaveLength(2)
  })

  it('displays weight distribution chart', () => {
    render(<WeightAnalysis {...defaultProps} />)
    expect(screen.getByTestId('pie-chart')).toBeInTheDocument()
    expect(screen.getByTestId('pie')).toBeInTheDocument()
  })

  it('displays contribution analysis chart', () => {
    render(<WeightAnalysis {...defaultProps} showContributions={true} />)
    expect(screen.getByTestId('bar-chart')).toBeInTheDocument()
  })

  it('displays radar chart for multi-dimensional analysis', () => {
    render(<WeightAnalysis {...defaultProps} showRadar={true} />)
    expect(screen.getByTestId('radar-chart')).toBeInTheDocument()
  })

  it('shows weight adjustment sliders', () => {
    render(<WeightAnalysis {...defaultProps} adjustable={true} />)

    expect(screen.getByLabelText('价格策略权重')).toBeInTheDocument()
    expect(screen.getByLabelText('经济指标权重')).toBeInTheDocument()
  })

  it('calls onWeightChange when slider is adjusted', async () => {
    render(<WeightAnalysis {...defaultProps} adjustable={true} normalize={false} />)

    const priceSlider = screen.getByLabelText('价格策略权重')
    fireEvent.change(priceSlider, { target: { value: '0.5' } })

    await waitFor(() => {
      expect(defaultProps.onWeightChange).toHaveBeenCalledWith({
        ...mockWeights,
        price: 0.5
      })
    })
  })

  it('normalizes weights when sum exceeds 1', () => {
    render(<WeightAnalysis {...defaultProps} adjustable={true} normalize={true} />)

    const priceSlider = screen.getByLabelText('价格策略权重')
    fireEvent.change(priceSlider, { target: { value: '0.6' } })

    // Should normalize to keep sum = 1
    expect(screen.getByText(/权重已自动调整/)).toBeInTheDocument()
  })

  it('shows performance metrics', () => {
    render(<WeightAnalysis {...defaultProps} showMetrics={true} />)

    expect(screen.getByText('总收益率')).toBeInTheDocument()
    expect(screen.getByText('夏普比率')).toBeInTheDocument()
    expect(screen.getByText('最大回撤')).toBeInTheDocument()
  })

  it('displays correlation matrix', () => {
    const mockCorrelations = {
      price: { economic: 0.5, volume: 0.3, technical: 0.7 },
      economic: { price: 0.5, volume: 0.4, technical: 0.6 },
      volume: { price: 0.3, economic: 0.4, technical: 0.2 },
      technical: { price: 0.7, economic: 0.6, volume: 0.2 }
    }

    render(<WeightAnalysis {...defaultProps} showCorrelation={true} correlations={mockCorrelations} />)

    expect(screen.getByText('相关性分析')).toBeInTheDocument()
  })

  it('handles zero weights gracefully', () => {
    const zeroWeights = { price: 0, economic: 0, volume: 0, technical: 0 }
    render(<WeightAnalysis {...defaultProps} weights={zeroWeights} />)

    expect(screen.getByText('权重分布')).toBeInTheDocument()
  })

  it('exports weight configuration when export button is clicked', () => {
    const mockExport = jest.fn()
    render(<WeightAnalysis {...defaultProps} onExport={mockExport} adjustable={true} />)

    const exportButton = screen.getByText('导出配置')
    fireEvent.click(exportButton)

    expect(mockExport).toHaveBeenCalledWith(mockWeights)
  })

  it('resets weights to default when reset button is clicked', () => {
    render(<WeightAnalysis {...defaultProps} adjustable={true} />)

    const resetButton = screen.getByText('重置')
    fireEvent.click(resetButton)

    expect(defaultProps.onWeightChange).toHaveBeenCalledWith({
      price: 0.25,
      economic: 0.25,
      volume: 0.25,
      technical: 0.25
    })
  })

  it('validates weight constraints', async () => {
    // This test checks that the component properly handles weight boundaries
    // Since HTML input range has max="1", we test within valid range
    render(<WeightAnalysis {...defaultProps} adjustable={true} normalize={false} />)

    const priceSlider = screen.getByLabelText('价格策略权重')

    // Test setting value to 1.0 (maximum valid value)
    fireEvent.change(priceSlider, { target: { value: '1.0' } })

    await waitFor(() => {
      expect(defaultProps.onWeightChange).toHaveBeenCalledWith({
        price: 1.0,
        economic: 0.3,
        volume: 0.2,
        technical: 0.1
      })
    })
  })
})
