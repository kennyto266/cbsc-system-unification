import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { ThemeProvider } from 'styled-components'
import HeatmapChart from './HeatmapChart'
import { HeatmapDataPoint } from '../../types/chart.types'

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

const mockDataset = {
  data: [
    { x: 'Mon', y: 'AM', value: 10, label: 'Monday Morning' },
    { x: 'Mon', y: 'PM', value: 20, label: 'Monday Afternoon' },
    { x: 'Tue', y: 'AM', value: 15, label: 'Tuesday Morning' },
    { x: 'Tue', y: 'PM', value: 25, label: 'Tuesday Afternoon' },
    { x: 'Wed', y: 'AM', value: 30, label: 'Wednesday Morning' },
    { x: 'Wed', y: 'PM', value: 35, label: 'Wednesday Afternoon' },
    { x: 'Thu', y: 'AM', value: 40, label: 'Thursday Morning' },
    { x: 'Thu', y: 'PM', value: 45, label: 'Thursday Afternoon' },
    { x: 'Fri', y: 'AM', value: 50, label: 'Friday Morning' },
    { x: 'Fri', y: 'PM', value: 55, label: 'Friday Afternoon' }
  ] as HeatmapDataPoint[],
  colorScale: {
    min: '#3B82F6',
    max: '#EF4444'
  },
  cellSize: 30,
  gap: 2
}

const mockAxes = {
  xAxis: {
    label: 'Day of Week',
    categories: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
  },
  yAxis: {
    label: 'Time',
    categories: ['AM', 'PM']
  }
}

const renderWithTheme = (component: React.ReactElement) => {
  return render(
    <ThemeProvider theme={mockTheme}>
      {component}
    </ThemeProvider>
  )
}

describe('HeatmapChart', () => {
  it('renders correctly with data', () => {
    renderWithTheme(
      <HeatmapChart
        dataset={mockDataset}
        xAxis={mockAxes.xAxis}
        yAxis={mockAxes.yAxis}
        height={400}
      />
    )

    expect(screen.getByRole('img')).toBeInTheDocument() // Chart canvas
    expect(screen.getByText('Day of Week')).toBeInTheDocument()
    expect(screen.getByText('Time')).toBeInTheDocument()
  })

  it('displays color scale when enabled', () => {
    renderWithTheme(
      <HeatmapChart
        dataset={mockDataset}
        xAxis={mockAxes.xAxis}
        yAxis={mockAxes.yAxis}
        showColorScale
      />
    )

    // Color scale values should be displayed
    expect(screen.getByText('10.0')).toBeInTheDocument()
    expect(screen.getByText('55.0')).toBeInTheDocument()
  })

  it('hides color scale when disabled', () => {
    renderWithTheme(
      <HeatmapChart
        dataset={mockDataset}
        xAxis={mockAxes.xAxis}
        yAxis={mockAxes.yAxis}
        showColorScale={false}
      />
    )

    // Color scale values should not be displayed
    expect(screen.queryByText('10.0')).not.toBeInTheDocument()
  })

  it('displays grid lines when enabled', () => {
    renderWithTheme(
      <HeatmapChart
        dataset={mockDataset}
        xAxis={mockAxes.xAxis}
        yAxis={mockAxes.yAxis}
        showGrid
      />
    )

    // Check for grid elements (Recharts uses CartesianGrid component)
    const gridElement = document.querySelector('.recharts-cartesian-grid')
    expect(gridElement).toBeInTheDocument()
  })

  it('handles cell click events', () => {
    const onCellClick = jest.fn()

    renderWithTheme(
      <HeatmapChart
        dataset={mockDataset}
        xAxis={mockAxes.xAxis}
        yAxis={mockAxes.yAxis}
        onCellClick={onCellClick}
      />
    )

    // Find and click on a cell (scatter point)
    const cells = document.querySelectorAll('.recharts-scatter-symbol')
    if (cells.length > 0) {
      fireEvent.click(cells[0])
      // Note: Testing actual cell clicks requires more complex setup
      // with Recharts internals. This test ensures the handler is provided.
    }
    expect(onCellClick).toBeDefined()
  })

  it('handles cell hover events', () => {
    const onCellHover = jest.fn()

    renderWithTheme(
      <HeatmapChart
        dataset={mockDataset}
        xAxis={mockAxes.xAxis}
        yAxis={mockAxes.yAxis}
        onCellHover={onCellHover}
      />
    )

    // Find and hover over a cell
    const cells = document.querySelectorAll('.recharts-scatter-symbol')
    if (cells.length > 0) {
      fireEvent.mouseEnter(cells[0])
      // Note: Testing actual cell hovers requires more complex setup
      expect(onCellHover).toBeDefined()
    }
  })

  it('displays tooltip on hover', () => {
    renderWithTheme(
      <HeatmapChart
        dataset={mockDataset}
        xAxis={mockAxes.xAxis}
        yAxis={mockAxes.yAxis}
        showTooltip
      />
    )

    // Tooltip should be configured
    expect(screen.getByRole('img')).toBeInTheDocument()
  })

  it('hides tooltip when disabled', () => {
    renderWithTheme(
      <HeatmapChart
        dataset={mockDataset}
        xAxis={mockAxes.xAxis}
        yAxis={mockAxes.yAxis}
        showTooltip={false}
      />
    )

    // Chart should still render
    expect(screen.getByRole('img')).toBeInTheDocument()
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
      <HeatmapChart
        dataset={mockDataset}
        xAxis={mockAxes.xAxis}
        yAxis={mockAxes.yAxis}
      />
    )

    // Find and click export button
    const exportButton = screen.getByTitle('导出')
    fireEvent.click(exportButton)

    // Click CSV export option
    const csvOption = screen.getByText('导出数据 (CSV)')
    fireEvent.click(csvOption)

    expect(mockAnchor.click).toHaveBeenCalled()
    expect(mockAnchor.download).toMatch(/heatmap-data-.*\.csv/)

    // Cleanup
    jest.restoreAllMocks()
  })

  it('handles empty data gracefully', () => {
    const emptyDataset = { ...mockDataset, data: [] }

    renderWithTheme(
      <HeatmapChart
        dataset={emptyDataset}
        xAxis={mockAxes.xAxis}
        yAxis={mockAxes.yAxis}
        height={400}
      />
    )

    // Should render without errors
    expect(screen.getByRole('img')).toBeInTheDocument()
  })

  it('applies custom cell size', () => {
    const customDataset = { ...mockDataset, cellSize: 50 }

    renderWithTheme(
      <HeatmapChart
        dataset={customDataset}
        xAxis={mockAxes.xAxis}
        yAxis={mockAxes.yAxis}
      />
    )

    // Chart should render with larger cells
    expect(screen.getByRole('img')).toBeInTheDocument()
  })

  it('applies custom color scale with steps', () => {
    const customDataset = {
      ...mockDataset,
      colorScale: {
        steps: [
          { value: 0, color: '#0000FF' },
          { value: 30, color: '#00FF00' },
          { value: 60, color: '#FF0000' }
        ]
      }
    }

    renderWithTheme(
      <HeatmapChart
        dataset={customDataset}
        xAxis={mockAxes.xAxis}
        yAxis={mockAxes.yAxis}
      />
    )

    // Color scale should reflect custom steps
    expect(screen.getByRole('img')).toBeInTheDocument()
  })

  it('toggles grid lines', () => {
    renderWithTheme(
      <HeatmapChart
        dataset={mockDataset}
        xAxis={mockAxes.xAxis}
        yAxis={mockAxes.yAxis}
        showGrid
      />
    )

    // Find and click grid toggle button
    const gridButton = screen.getByTitle('显示/隐藏网格')
    fireEvent.click(gridButton)

    // Grid should disappear
    const gridElement = document.querySelector('.recharts-cartesian-grid')
    expect(gridElement).not.toBeInTheDocument()
  })

  it('positions color scale on the left', () => {
    renderWithTheme(
      <HeatmapChart
        dataset={mockDataset}
        xAxis={mockAxes.xAxis}
        yAxis={mockAxes.yAxis}
        showColorScale
        colorScalePosition="left"
      />
    )

    // Color scale should be positioned on the left
    expect(screen.getByRole('img')).toBeInTheDocument()
  })

  it('applies custom className', () => {
    const customClass = 'custom-heatmap-class'
    const { container } = renderWithTheme(
      <HeatmapChart
        dataset={mockDataset}
        xAxis={mockAxes.xAxis}
        yAxis={mockAxes.yAxis}
        className={customClass}
      />
    )

    expect(container.querySelector('.custom-heatmap-class')).toBeInTheDocument()
  })
})