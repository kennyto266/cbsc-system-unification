import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import { WeightAnalysis } from '../WeightAnalysis'

// Mock recharts
jest.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="responsive-container">{children}</div>
  ),
  PieChart: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="pie-chart">{children}</div>
  ),
  Pie: (props: any) => <div data-testid="pie" {...props} />,
  Cell: (props: any) => <div data-testid="cell" {...props} />,
  BarChart: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="bar-chart">{children}</div>
  ),
  Bar: (props: any) => <div data-testid="bar" {...props} />,
  XAxis: (props: any) => <div data-testid="x-axis" {...props} />,
  YAxis: (props: any) => <div data-testid="y-axis" {...props} />,
  CartesianGrid: (props: any) => <div data-testid="cartesian-grid" {...props} />,
  Tooltip: (props: any) => <div data-testid="tooltip" {...props} />,
  Legend: (props: any) => <div data-testid="legend" {...props} />,
  RadarChart: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="radar-chart">{children}</div>
  ),
  PolarGrid: (props: any) => <div data-testid="polar-grid" {...props} />,
  PolarAngleAxis: (props: any) => <div data-testid="polar-angle-axis" {...props} />,
  PolarRadiusAxis: (props: any) => <div data-testid="polar-radius-axis" {...props} />,
  Radar: (props: any) => <div data-testid="radar" {...props} />
}))

jest.mock('../../../contexts/ThemeContext', () => ({
  useTheme: () => ({
    resolvedTheme: 'light'
  })
}))

const mockWeights = {
  price: 0.4,
  economic: 0.3,
  volume: 0.2,
  technical: 0.1
}

const mockContributions = [
  { name: '价格策略', value: 0.4, contribution: 0.35, performance: 0.12 },
  { name: '经济指标', value: 0.3, contribution: 0.25, performance: 0.08 },
  { name: '成交量', value: 0.2, contribution: 0.25, performance: 0.15 },
  { name: '技术指标', value: 0.1, contribution: 0.15, performance: -0.02 }
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
    expect(screen.getByTestId('responsive-container')).toBeInTheDocument()
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
    render(<WeightAnalysis {...defaultProps} adjustable={true} />)

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
    render(<WeightAnalysis {...defaultProps} showCorrelation={true} />)

    expect(screen.getByText('相关性分析')).toBeInTheDocument()
  })

  it('handles zero weights gracefully', () => {
    const zeroWeights = { price: 0, economic: 0, volume: 0, technical: 0 }
    render(<WeightAnalysis {...defaultProps} weights={zeroWeights} />)

    expect(screen.getByText('权重分布')).toBeInTheDocument()
  })

  it('exports weight configuration when export button is clicked', () => {
    const mockExport = jest.fn()
    render(<WeightAnalysis {...defaultProps} onExport={mockExport} />)

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

  it('validates weight constraints', () => {
    render(<WeightAnalysis {...defaultProps} adjustable={true} />)

    // Try to set invalid weight
    const priceSlider = screen.getByLabelText('价格策略权重')
    fireEvent.change(priceSlider, { target: { value: '1.5' } })

    expect(screen.getByText(/权重不能超过/)).toBeInTheDocument()
  })
})