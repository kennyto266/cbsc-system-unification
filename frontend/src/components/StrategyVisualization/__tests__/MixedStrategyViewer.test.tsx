import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import { MixedStrategyViewer } from '../MixedStrategyViewer'

// Mock the child components
jest.mock('../DualAxisChart', () => ({
  DualAxisChart: ({ title, onPointClick }: any) => (
    <div data-testid="dual-axis-chart">
      <div>{title}</div>
      <button onClick={() => onPointClick?.({ date: '2024-01', price: 100 })}>
        Click Point
      </button>
    </div>
  )
}))

jest.mock('../TimeframeSelector', () => ({
  TimeframeSelector: ({ value, onChange }: any) => (
    <select
      data-testid="timeframe-selector"
      value={value}
      onChange={(e) => onChange(e.target.value)}
    >
      <option value="1d">1天</option>
      <option value="1w">1周</option>
      <option value="1m">1月</option>
      <option value="1y">1年</option>
    </select>
  )
}))

jest.mock('../../../contexts/ThemeContext', () => ({
  useTheme: () => ({
    resolvedTheme: 'light'
  })
}))

const mockData = [
  { date: '2024-01', timestamp: 1704067200000, price: 100, volume: 1000, signal: 1, gdp: 2.5 },
  { date: '2024-02', timestamp: 1706745600000, price: 102, volume: 1200, signal: -1, gdp: 2.6 },
  { date: '2024-03', timestamp: 1709337600000, price: 105, volume: 800, signal: 1, gdp: 2.7 }
]

describe('MixedStrategyViewer', () => {
  const defaultProps = {
    data: mockData,
    title: 'Mixed Strategy Viewer'
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders without crashing', () => {
    render(<MixedStrategyViewer {...defaultProps} />)
    expect(screen.getByTestId('dual-axis-chart')).toBeInTheDocument()
    expect(screen.getByTestId('timeframe-selector')).toBeInTheDocument()
  })

  it('displays the provided title', () => {
    render(<MixedStrategyViewer {...defaultProps} />)
    expect(screen.getByText('Mixed Strategy Viewer')).toBeInTheDocument()
  })

  it('switches timeframe when selector changes', async () => {
    const onTimeframeChange = jest.fn()
    render(<MixedStrategyViewer {...defaultProps} onTimeframeChange={onTimeframeChange} />)

    const selector = screen.getByTestId('timeframe-selector')
    fireEvent.change(selector, { target: { value: '1w' } })

    await waitFor(() => {
      expect(onTimeframeChange).toHaveBeenCalledWith('1w')
    })
  })

  it('handles point click on chart', async () => {
    render(<MixedStrategyViewer {...defaultProps} />)

    const clickButton = screen.getByText('Click Point')
    fireEvent.click(clickButton)

    await waitFor(() => {
      expect(screen.getByText(/详细信息/)).toBeInTheDocument()
    })
  })

  it('shows control panel with toggle switches', () => {
    render(<MixedStrategyViewer {...defaultProps} />)

    expect(screen.getByText('显示成交量')).toBeInTheDocument()
    expect(screen.getByText('显示信号')).toBeInTheDocument()
    expect(screen.getByText('显示经济指标')).toBeInTheDocument()
    expect(screen.getByText('显示均线')).toBeInTheDocument()
  })

  it('toggles volume display when checkbox is clicked', () => {
    render(<MixedStrategyViewer {...defaultProps} />)

    const volumeToggle = screen.getByLabelText('显示成交量')
    fireEvent.click(volumeToggle)

    // The chart should re-render with updated props
    expect(screen.getByTestId('dual-axis-chart')).toBeInTheDocument()
  })

  it('displays statistics panel', () => {
    render(<MixedStrategyViewer {...defaultProps} />)

    expect(screen.getByText('统计信息')).toBeInTheDocument()
    expect(screen.getByText(/平均价格/)).toBeInTheDocument()
    expect(screen.getByText(/总成交量/)).toBeInTheDocument()
  })

  it('filters data by date range', () => {
    render(<MixedStrategyViewer {...defaultProps} />)

    const startDateInput = screen.getByLabelText('开始日期')
    const endDateInput = screen.getByLabelText('结束日期')

    fireEvent.change(startDateInput, { target: { value: '2024-01-01' } })
    fireEvent.change(endDateInput, { target: { value: '2024-02-01' } })

    // Component should re-render with filtered data
    expect(screen.getByTestId('dual-axis-chart')).toBeInTheDocument()
  })

  it('exports data when export button is clicked', () => {
    const mockExport = jest.fn()
    render(<MixedStrategyViewer {...defaultProps} onExport={mockExport} />)

    const exportButton = screen.getByText('导出数据')
    fireEvent.click(exportButton)

    expect(mockExport).toHaveBeenCalled()
  })

  it('displays loading state when data is loading', () => {
    render(<MixedStrategyViewer {...defaultProps} loading={true} />)

    expect(screen.getByText('加载中...')).toBeInTheDocument()
  })

  it('shows error message when error occurs', () => {
    render(<MixedStrategyViewer {...defaultProps} error="Failed to load data" />)

    expect(screen.getByText('Failed to load data')).toBeInTheDocument()
  })
})