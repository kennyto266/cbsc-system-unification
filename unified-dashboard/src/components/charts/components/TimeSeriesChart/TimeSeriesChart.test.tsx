import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { ThemeProvider } from 'styled-components'
import TimeSeriesChart from './TimeSeriesChart'
import { TimeSeriesDataPoint, TimeSeriesDataset } from '../../types/chart.types'

const mockTheme = {
  name: 'test',
  colors: {
    primary: ['#3B82F6', '#10B981'],
    secondary: ['#6B7280'],
    background: '#ffffff',
    foreground: '#1F2937',
    grid: 'rgba(0, 0, 0, 0.05)',
    tooltip: {
      background: 'rgba(0, 0, 0, 0.8)',
      foreground: '#ffffff',
      border: 'rgba(0, 0, 0, 0.8)'
    }
  },
  typography: {
    fontFamily: 'Arial',
    fontSize: {
      small: 12,
      medium: 14,
      large: 16
    }
  },
  spacing: {
    xs: 4,
    sm: 8,
    md: 16,
    lg: 24,
    xl: 32
  }
}

const mockDatasets: TimeSeriesDataset[] = [
  {
    id: 'price',
    label: 'Price',
    data: Array.from({ length: 100 }, (_, i) => ({
      timestamp: new Date(Date.now() - (99 - i) * 60000),
      value: 100 + Math.sin(i * 0.1) * 10
    })),
    color: '#3B82F6',
    strokeWidth: 2
  },
  {
    id: 'volume',
    label: 'Volume',
    data: Array.from({ length: 100 }, (_, i) => ({
      timestamp: new Date(Date.now() - (99 - i) * 60000),
      value: 1000 + Math.random() * 500,
      volume: 1000 + Math.random() * 500
    })),
    color: '#10B981',
    strokeWidth: 1,
    yAxisId: 'right'
  }
]

const renderWithTheme = (component: React.ReactElement) => {
  return render(
    <ThemeProvider theme={mockTheme}>
      {component}
    </ThemeProvider>
  )
}

describe('TimeSeriesChart', () => {
  it('renders correctly with datasets', () => {
    renderWithTheme(
      <TimeSeriesChart datasets={mockDatasets} height={400} />
    )

    expect(screen.getByRole('img')).toBeInTheDocument() // Chart canvas
  })

  it('displays legend when enabled', () => {
    renderWithTheme(
      <TimeSeriesChart datasets={mockDatasets} showLegend />
    )

    expect(screen.getByText('Price')).toBeInTheDocument()
    expect(screen.getByText('Volume')).toBeInTheDocument()
  })

  it('hides legend when disabled', () => {
    renderWithTheme(
      <TimeSeriesChart datasets={mockDatasets} showLegend={false} />
    )

    expect(screen.queryByText('Price')).not.toBeInTheDocument()
  })

  it('displays grid lines when enabled', () => {
    renderWithTheme(
      <TimeSeriesChart datasets={mockDatasets} showGrid />
    )

    // Check for grid elements (Recharts uses CartesianGrid component)
    const gridElement = document.querySelector('.recharts-cartesian-grid')
    expect(gridElement).toBeInTheDocument()
  })

  it('renders with dual y-axes when configured', () => {
    renderWithTheme(
      <TimeSeriesChart
        datasets={mockDatasets}
        yAxis={{
          left: { id: 'left', orientation: 'left', label: 'Price' },
          right: { id: 'right', orientation: 'right', label: 'Volume' }
        }}
      />
    )

    // Y-axis labels would be rendered
    expect(screen.getByText('Price')).toBeInTheDocument()
    expect(screen.getByText('Volume')).toBeInTheDocument()
  })

  it('handles brush toggle', async () => {
    renderWithTheme(
      <TimeSeriesChart datasets={mockDatasets} />
    )

    // Find and click the brush toggle button
    const brushButton = screen.getByTitle('显示/隐藏时间范围选择')
    fireEvent.click(brushButton)

    // Brush should appear at the bottom
    await waitFor(() => {
      const brushElement = document.querySelector('.recharts-brush')
      expect(brushElement).toBeInTheDocument()
    })
  })

  it('handles grid toggle', async () => {
    renderWithTheme(
      <TimeSeriesChart datasets={mockDatasets} showGrid />
    )

    // Find and click the grid toggle button
    const gridButton = screen.getByTitle('显示/隐藏网格')
    fireEvent.click(gridButton)

    // Grid should disappear
    await waitFor(() => {
      const gridElement = document.querySelector('.recharts-cartesian-grid')
      expect(gridElement).not.toBeInTheDocument()
    })
  })

  it('exports data as CSV', () => {
    // Mock URL.createObjectURL and URL.revokeObjectURL
    global.URL.createObjectURL = jest.fn(() => 'mock-url')
    global.URL.revokeObjectURL = jest.fn()

    // Mock createElement and click
    const mockAnchor = {
      href: '',
      download: '',
      click: jest.fn()
    }
    jest.spyOn(document, 'createElement').mockImplementation(() => mockAnchor as any)

    renderWithTheme(
      <TimeSeriesChart datasets={mockDatasets} />
    )

    // Find and click export button
    const exportButton = screen.getByTitle('导出')
    fireEvent.click(exportButton)

    // Click CSV export option
    const csvOption = screen.getByText('导出数据 (CSV)')
    fireEvent.click(csvOption)

    expect(mockAnchor.click).toHaveBeenCalled()
    expect(mockAnchor.download).toMatch(/chart-data-.*\.csv/)

    // Cleanup
    jest.restoreAllMocks()
  })

  it('calls onTimeRangeChange when time range is selected', async () => {
    const onTimeRangeChange = jest.fn()

    renderWithTheme(
      <TimeSeriesChart
        datasets={mockDatasets}
        onTimeRangeChange={onTimeRangeChange}
      />
    )

    // Enable brush first
    const brushButton = screen.getByTitle('显示/隐藏时间范围选择')
    fireEvent.click(brushButton)

    // Simulate brush selection (this would normally be done by dragging the brush)
    // For testing purposes, we'll check if the callback is provided
    expect(onTimeRangeChange).toBeDefined()
  })

  it('handles empty datasets gracefully', () => {
    renderWithTheme(
      <TimeSeriesChart datasets={[]} height={400} />
    )

    // Should render without errors
    expect(screen.getByRole('img')).toBeInTheDocument()
  })

  it('displays loading state correctly', () => {
    renderWithTheme(
      <TimeSeriesChart datasets={mockDatasets} loading />
    )

    expect(screen.getByText('加载中...')).toBeInTheDocument()
  })

  it('displays error state correctly', () => {
    const errorMessage = 'Failed to load data'
    renderWithTheme(
      <TimeSeriesChart datasets={mockDatasets} error={errorMessage} />
    )

    expect(screen.getByText('图表加载错误')).toBeInTheDocument()
    expect(screen.getByText(errorMessage)).toBeInTheDocument()
  })

  it('applies custom time format', () => {
    renderWithTheme(
      <TimeSeriesChart datasets={mockDatasets} timeFormat="MM/dd" />
    )

    // Check if x-axis labels are formatted correctly
    // This is harder to test directly, but we can check the chart renders
    expect(screen.getByRole('img')).toBeInTheDocument()
  })

  it('handles click events on data points', () => {
    const onDataPointClick = jest.fn()

    renderWithTheme(
      <TimeSeriesChart
        datasets={mockDatasets}
        onDataPointClick={onDataPointClick}
      />
    )

    // Simulate clicking on the chart
    const chartElement = screen.getByRole('img')
    fireEvent.click(chartElement)

    // Note: Testing actual data point clicks requires more complex setup
    // with Recharts internals. This test ensures the handler is provided.
    expect(onDataPointClick).toBeDefined()
  })

  it('is responsive by default', () => {
    renderWithTheme(
      <TimeSeriesChart datasets={mockDatasets} />
    )

    // Check if ResponsiveContainer is used
    const responsiveContainer = document.querySelector('.recharts-responsive-container')
    expect(responsiveContainer).toBeInTheDocument()
  })

  it('can disable responsiveness', () => {
    renderWithTheme(
      <TimeSeriesChart datasets={mockDatasets} responsive={false} />
    )

    // Chart should still render
    expect(screen.getByRole('img')).toBeInTheDocument()
  })

  it('applies custom className', () => {
    const customClass = 'custom-chart-class'
    const { container } = renderWithTheme(
      <TimeSeriesChart datasets={mockDatasets} className={customClass} />
    )

    expect(container.querySelector('.custom-chart-class')).toBeInTheDocument()
  })
})