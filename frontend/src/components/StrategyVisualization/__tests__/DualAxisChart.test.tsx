import React from 'react'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import { DualAxisChart } from '../DualAxisChart'

// Mock Recharts components
jest.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="responsive-container">{children}</div>
  ),
  ComposedChart: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="composed-chart">{children}</div>
  ),
  Line: (props: any) => <div data-testid="line" {...props} />,
  Bar: (props: any) => <div data-testid="bar" {...props} />,
  XAxis: (props: any) => <div data-testid="x-axis" {...props} />,
  YAxis: (props: any) => <div data-testid="y-axis" {...props} />,
  CartesianGrid: (props: any) => <div data-testid="cartesian-grid" {...props} />,
  Tooltip: (props: any) => <div data-testid="tooltip" {...props} />,
  Legend: (props: any) => <div data-testid="legend" {...props} />,
  ReferenceLine: (props: any) => <div data-testid="reference-line" {...props} />
}))

// Mock ThemeContext
jest.mock('../../../contexts/ThemeContext', () => ({
  useTheme: () => ({
    resolvedTheme: 'light'
  })
}))

const mockData = [
  { date: '2024-01', price: 100, volume: 1000, signal: 1 },
  { date: '2024-02', price: 102, volume: 1200, signal: -1 },
  { date: '2024-03', price: 105, volume: 800, signal: 1 },
  { date: '2024-04', price: 103, volume: 1500, signal: 0 },
  { date: '2024-05', price: 108, volume: 900, signal: 1 }
]

describe('DualAxisChart', () => {
  const defaultProps = {
    data: mockData,
    priceKey: 'price',
    volumeKey: 'volume',
    signalKey: 'signal',
    height: 400
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders without crashing', () => {
    render(<DualAxisChart {...defaultProps} />)
    expect(screen.getByTestId('responsive-container')).toBeInTheDocument()
    expect(screen.getByTestId('composed-chart')).toBeInTheDocument()
  })

  it('displays title when provided', () => {
    render(<DualAxisChart {...defaultProps} title="Test Chart" />)
    expect(screen.getByText('Test Chart')).toBeInTheDocument()
  })

  it('renders price line chart', () => {
    render(<DualAxisChart {...defaultProps} />)
    const priceLine = screen.getAllByTestId('line')[0]
    expect(priceLine).toHaveAttribute('dataKey', 'price')
    expect(priceLine).toHaveAttribute('stroke', '#3b82f6')
  })

  it('renders volume bar chart', () => {
    render(<DualAxisChart {...defaultProps} showVolume={true} />)
    const volumeBar = screen.getByTestId('bar')
    expect(volumeBar).toHaveAttribute('dataKey', 'volume')
    expect(volumeBar).toHaveAttribute('fill', '#10b981')
  })

  it('renders signal markers when enabled', () => {
    render(<DualAxisChart {...defaultProps} showSignals={true} />)
    const signals = screen.getAllByTestId('line').filter(line =>
      line.getAttribute('dataKey') === 'signalPosition'
    )
    expect(signals).toHaveLength(1)
  })

  it('hides volume chart when showVolume is false', () => {
    render(<DualAxisChart {...defaultProps} showVolume={false} />)
    expect(screen.queryByTestId('bar')).not.toBeInTheDocument()
  })

  it('displays loading state when no data', () => {
    render(<DualAxisChart {...defaultProps} data={[]} />)
    expect(screen.getByText('暂无数据')).toBeInTheDocument()
  })

  it('applies custom height', () => {
    render(<DualAxisChart {...defaultProps} height={500} />)
    const container = screen.getByTestId('responsive-container').parentElement
    expect(container?.style.height).toBe('500px')
  })

  it('supports custom colors', () => {
    const customColors = {
      price: '#ff0000',
      volume: '#00ff00',
      signal: '#0000ff'
    }
    render(<DualAxisChart {...defaultProps} colors={customColors} />)

    const priceLine = screen.getAllByTestId('line')[0]
    expect(priceLine).toHaveAttribute('stroke', '#ff0000')
  })

  it('shows reference lines for thresholds', () => {
    render(
      <DualAxisChart
        {...defaultProps}
        showThresholds={true}
        thresholds={{ upper: 110, lower: 95 }}
      />
    )

    const referenceLines = screen.getAllByTestId('reference-line')
    expect(referenceLines).toHaveLength(2)
  })
})