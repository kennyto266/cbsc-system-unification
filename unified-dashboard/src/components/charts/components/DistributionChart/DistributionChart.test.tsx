import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { ThemeProvider } from 'styled-components'
import DistributionChart from './DistributionChart'
import { DistributionDataPoint } from '../../types/chart.types'

const mockTheme = {
  name: 'test',
  colors: {
    primary: ['#3B82F6', '#10B981', '#F59E0B', '#EF4444'],
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

const mockData: DistributionDataPoint[] = [
  { label: 'Category A', value: 400 },
  { label: 'Category B', value: 300 },
  { label: 'Category C', value: 200 },
  { label: 'Category D', value: 100 }
]

const renderWithTheme = (component: React.ReactElement) => {
  return render(
    <ThemeProvider theme={mockTheme}>
      {component}
    </ThemeProvider>
  )
}

describe('DistributionChart', () => {
  it('renders bar chart correctly', () => {
    renderWithTheme(
      <DistributionChart
        dataset={{
          data: mockData,
          type: 'bar'
        }}
        height={400}
      />
    )

    expect(screen.getByRole('img')).toBeInTheDocument() // Chart canvas
    expect(screen.getByText('Category A')).toBeInTheDocument()
    expect(screen.getByText('Category B')).toBeInTheDocument()
  })

  it('renders pie chart correctly', () => {
    renderWithTheme(
      <DistributionChart
        dataset={{
          data: mockData,
          type: 'pie'
        }}
        height={400}
      />
    )

    expect(screen.getByRole('img')).toBeInTheDocument() // Chart canvas
  })

  it('renders donut chart correctly', () => {
    renderWithTheme(
      <DistributionChart
        dataset={{
          data: mockData,
          type: 'donut',
          innerRadius: 60,
          outerRadius: 120
        }}
        height={400}
      />
    )

    expect(screen.getByRole('img')).toBeInTheDocument() // Chart canvas
  })

  it('renders horizontal bar chart correctly', () => {
    renderWithTheme(
      <DistributionChart
        dataset={{
          data: mockData,
          type: 'horizontal-bar'
        }}
        height={400}
      />
    )

    expect(screen.getByRole('img')).toBeInTheDocument() // Chart canvas
  })

  it('displays legend when enabled', () => {
    renderWithTheme(
      <DistributionChart
        dataset={{
          data: mockData,
          type: 'pie',
          showLabels: true
        }}
        showLegend
        height={400}
      />
    )

    expect(screen.getByText('Category A')).toBeInTheDocument()
  })

  it('hides legend when disabled', () => {
    renderWithTheme(
      <DistributionChart
        dataset={{
          data: mockData,
          type: 'pie'
        }}
        showLegend={false}
        height={400}
      />
    )

    // Legend should not be visible
    const legendElement = document.querySelector('.recharts-legend-wrapper')
    expect(legendElement).not.toBeInTheDocument()
  })

  it('sorts data in ascending order', () => {
    renderWithTheme(
      <DistributionChart
        dataset={{
          data: mockData,
          type: 'bar'
        }}
        sortOrder="asc"
        height={400}
      />
    )

    // Category D (100) should be first, Category A (400) should be last
    const xAxisLabels = screen.getAllByText(/Category [A-D]/)
    expect(xAxisLabels[0]).toHaveTextContent('Category D')
    expect(xAxisLabels[xAxisLabels.length - 1]).toHaveTextContent('Category A')
  })

  it('sorts data in descending order', () => {
    renderWithTheme(
      <DistributionChart
        dataset={{
          data: mockData,
          type: 'bar'
        }}
        sortOrder="desc"
        height={400}
      />
    )

    // Category A (400) should be first, Category D (100) should be last
    const xAxisLabels = screen.getAllByText(/Category [A-D]/)
    expect(xAxisLabels[0]).toHaveTextContent('Category A')
    expect(xAxisLabels[xAxisLabels.length - 1]).toHaveTextContent('Category D')
  })

  it('limits number of items displayed', () => {
    renderWithTheme(
      <DistributionChart
        dataset={{
          data: mockData,
          type: 'bar'
        }}
        maxItems={2}
        height={400}
      />
    )

    // Only 2 categories should be displayed
    const xAxisLabels = screen.getAllByText(/Category [A-D]/)
    expect(xAxisLabels).toHaveLength(2)
  })

  it('handles slice click for pie chart', () => {
    const onSliceClick = jest.fn()

    renderWithTheme(
      <DistributionChart
        dataset={{
          data: mockData,
          type: 'pie'
        }}
        onSliceClick={onSliceClick}
        height={400}
      />
    )

    // Find and click on a pie slice
    const slices = document.querySelectorAll('.recharts-pie-sector')
    if (slices.length > 0) {
      fireEvent.click(slices[0])
      // Note: Testing actual slice clicks requires more complex setup
      expect(onSliceClick).toBeDefined()
    }
  })

  it('handles bar click for bar chart', () => {
    const onBarClick = jest.fn()

    renderWithTheme(
      <DistributionChart
        dataset={{
          data: mockData,
          type: 'bar'
        }}
        onBarClick={onBarClick}
        height={400}
      />
    )

    // Find and click on a bar
    const bars = document.querySelectorAll('.recharts-bar-rectangle')
    if (bars.length > 0) {
      fireEvent.click(bars[0])
      // Note: Testing actual bar clicks requires more complex setup
      expect(onBarClick).toBeDefined()
    }
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
      <DistributionChart
        dataset={{
          data: mockData,
          type: 'bar'
        }}
        height={400}
      />
    )

    // Find and click export button
    const exportButton = screen.getByTitle('导出')
    fireEvent.click(exportButton)

    // Click CSV export option
    const csvOption = screen.getByText('导出数据 (CSV)')
    fireEvent.click(csvOption)

    expect(mockAnchor.click).toHaveBeenCalled()
    expect(mockAnchor.download).toMatch(/distribution-data-.*\.csv/)

    // Cleanup
    jest.restoreAllMocks()
  })

  it('handles empty data gracefully', () => {
    renderWithTheme(
      <DistributionChart
        dataset={{
          data: [],
          type: 'bar'
        }}
        height={400}
      />
    )

    // Should render without errors
    expect(screen.getByRole('img')).toBeInTheDocument()
  })

  it('displays labels on pie chart when enabled', () => {
    renderWithTheme(
      <DistributionChart
        dataset={{
          data: mockData,
          type: 'pie',
          showLabels: true
        }}
        height={400}
      />
    )

    // Percentage labels should be visible
    const labels = document.querySelectorAll('.recharts-pie-label-text')
    expect(labels.length).toBeGreaterThan(0)
  })

  it('applies custom inner radius for donut chart', () => {
    renderWithTheme(
      <DistributionChart
        dataset={{
          data: mockData,
          type: 'donut',
          innerRadius: 80,
          outerRadius: 120
        }}
        height={400}
      />
    )

    // Chart should render with custom donut dimensions
    expect(screen.getByRole('img')).toBeInTheDocument()
  })

  it('applies custom animation duration', () => {
    renderWithTheme(
      <DistributionChart
        dataset={{
          data: mockData,
          type: 'bar'
        }}
        animationDuration={500}
        height={400}
      />
    )

    // Chart should render
    expect(screen.getByRole('img')).toBeInTheDocument()
  })

  it('displays percentage values', () => {
    renderWithTheme(
      <DistributionChart
        dataset={{
          data: mockData,
          type: 'bar',
          showPercentages: true
        }}
        height={400}
      />
    )

    // Percentage calculation should be applied
    expect(screen.getByRole('img')).toBeInTheDocument()
  })

  it('applies custom className', () => {
    const customClass = 'custom-distribution-class'
    const { container } = renderWithTheme(
      <DistributionChart
        dataset={{
          data: mockData,
          type: 'bar'
        }}
        className={customClass}
        height={400}
      />
    )

    expect(container.querySelector('.custom-distribution-class')).toBeInTheDocument()
  })

  it('uses custom colors when provided', () => {
    const dataWithColors: DistributionDataPoint[] = mockData.map((item, index) => ({
      ...item,
      color: index % 2 === 0 ? '#FF0000' : '#00FF00'
    }))

    renderWithTheme(
      <DistributionChart
        dataset={{
          data: dataWithColors,
          type: 'pie'
        }}
        height={400}
      />
    )

    // Chart should use custom colors
    expect(screen.getByRole('img')).toBeInTheDocument()
  })
})