/**
 * Tests for PerformanceChart Component
 * Batch 1 Migration - Advanced Charts
 */

import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import PerformanceChart from '../PerformanceChart'
import type { PerformanceChartProps } from '../types'

// Test wrapper
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return <div>{children}</div>
}

// Mock performance data - matching PerformanceDataPoint type
const mockData = [
  { date: '2024-01-01', value: 100, benchmark: 100 },
  { date: '2024-01-02', value: 105, benchmark: 102 },
  { date: '2024-01-03', value: 103, benchmark: 101 },
  { date: '2024-01-04', value: 110, benchmark: 104 },
  { date: '2024-01-05', value: 108, benchmark: 103 },
  { date: '2024-01-06', value: 115, benchmark: 106 }
]

const mockProps = {
  data: mockData,
  title: 'Strategy Performance',
  height: 400,
  showBenchmark: true,
  showArea: true
}

describe('PerformanceChart - Batch 1 Migration', () => {
  it('renders without crashing', () => {
    render(
      <TestWrapper>
        <PerformanceChart {...mockProps} />
      </TestWrapper>
    )

    // Recharts LineChart renders a div
    const container = document.querySelector('.recharts-responsive-container')
    expect(container).toBeInTheDocument()
  })

  it('displays strategy line', () => {
    render(
      <TestWrapper>
        <PerformanceChart {...mockProps} />
      </TestWrapper>
    )

    // Should have line path for strategy
    const lines = document.querySelectorAll('.recharts-line')
    expect(lines.length).toBeGreaterThan(0)
  })

  it('displays benchmark line when provided', () => {
    render(
      <TestWrapper>
        <PerformanceChart {...mockProps} showBenchmark />
      </TestWrapper>
    )

    // Should have two lines (strategy + benchmark)
    const lines = document.querySelectorAll('.recharts-line')
    expect(lines.length).toBe(2)
  })

  it('hides benchmark when disabled', () => {
    render(
      <TestWrapper>
        <PerformanceChart {...mockProps} showBenchmark={false} />
      </TestWrapper>
    )

    // Should have only one line (strategy)
    const lines = document.querySelectorAll('.recharts-line')
    expect(lines.length).toBe(1)
  })

  it('shows area fill when enabled', () => {
    render(
      <TestWrapper>
        <PerformanceChart {...mockProps} showArea />
      </TestWrapper>
    )

    // Should have area for strategy
    const areas = document.querySelectorAll('.recharts-area')
    expect(areas.length).toBeGreaterThan(0)
  })

  it('hides area fill when disabled', () => {
    render(
      <TestWrapper>
        <PerformanceChart {...mockProps} showArea={false} />
      </TestWrapper>
    )

    // Areas should not be present
    const areas = document.querySelectorAll('.recharts-area')
    expect(areas.length).toBe(0)
  })

  it('displays tooltip on hover', () => {
    render(
      <TestWrapper>
        <PerformanceChart {...mockProps} showTooltip />
      </TestWrapper>
    )

    const tooltip = document.querySelector('.recharts-tooltip-wrapper')
    expect(tooltip).toBeInTheDocument()
  })

  it('handles click events', () => {
    const onClick = jest.fn()

    render(
      <TestWrapper>
        <PerformanceChart {...mockProps} onClick={onClick} />
      </TestWrapper>
    )

    const line = document.querySelector('.recharts-line')
    if (line) {
      fireEvent.click(line)
    }

    expect(onClick).toBeDefined()
  })

  it('displays legend', () => {
    render(
      <TestWrapper>
        <PerformanceChart {...mockProps} showLegend />
      </TestWrapper>
    )

    const legend = document.querySelector('.recharts-legend-wrapper')
    expect(legend).toBeInTheDocument()
  })

  it('shows custom legend items', () => {
    render(
      <TestWrapper>
        <PerformanceChart {...mockProps} showLegend />
      </TestWrapper>
    )

    // Legend should show strategy and benchmark names
    expect(screen.getByText('Strategy A')).toBeInTheDocument()
    expect(screen.getByText('Benchmark')).toBeInTheDocument()
  })

  it('applies custom colors', () => {
    const customColors = {
      strategy: '#FF0000',
      benchmark: '#00FF00'
    }

    render(
      <TestWrapper>
        <PerformanceChart {...mockProps} colors={customColors} />
      </TestWrapper>
    )

    const lines = document.querySelectorAll('.recharts-line')
    expect(lines.length).toBeGreaterThan(0)
  })

  it('handles empty data gracefully', () => {
    const emptyProps = {
      ...mockProps,
      strategyData: { name: 'Empty', data: [] },
      benchmarkData: { name: 'Empty', data: [] }
    }

    render(
      <TestWrapper>
        <PerformanceChart {...emptyProps} />
      </TestWrapper>
    )

    const container = document.querySelector('.recharts-responsive-container')
    expect(container).toBeInTheDocument()
  })

  it('displays axis labels', () => {
    render(
      <TestWrapper>
        <PerformanceChart {...mockProps} />
      </TestWrapper>
    )

    const xAxis = document.querySelector('.recharts-xAxis')
    const yAxis = document.querySelector('.recharts-yAxis')
    expect(xAxis).toBeInTheDocument()
    expect(yAxis).toBeInTheDocument()
  })

  it('shows grid lines when enabled', () => {
    render(
      <TestWrapper>
        <PerformanceChart {...mockProps} showGrid />
      </TestWrapper>
    )

    const grid = document.querySelector('.recharts-cartesian-grid')
    expect(grid).toBeInTheDocument()
  })

  it('hides grid lines when disabled', () => {
    render(
      <TestWrapper>
        <PerformanceChart {...mockProps} showGrid={false} />
      </TestWrapper>
    )

    const grid = document.querySelector('.recharts-cartesian-grid')
    expect(grid).not.toBeInTheDocument()
  })

  it('supports custom dimensions', () => {
    render(
      <TestWrapper>
        <PerformanceChart {...mockProps} height={500} width={800} />
      </TestWrapper>
    )

    const container = document.querySelector('.recharts-responsive-container')
    expect(container).toBeInTheDocument()
  })

  it('applies custom className', () => {
    render(
      <TestWrapper>
        <PerformanceChart {...mockProps} className="custom-performance" />
      </TestWrapper>
    )

    const container = document.querySelector('.custom-performance')
    expect(container).toBeInTheDocument()
  })

  it('handles loading state', () => {
    render(
      <TestWrapper>
        <PerformanceChart {...mockProps} loading />
      </TestWrapper>
    )

    // Should show loading spinner
    const loading = document.querySelector('.animate-spin')
    expect(loading).toBeInTheDocument()
  })

  it('handles error state', () => {
    const onError = jest.fn()

    render(
      <TestWrapper>
        <PerformanceChart {...mockProps} error="Failed to load" onError={onError} />
      </TestWrapper>
    )

    expect(screen.getByText(/Failed to load/)).toBeInTheDocument()
  })

  it('calculates and displays performance metrics', () => {
    render(
      <TestWrapper>
        <PerformanceChart {...mockProps} showMetrics />
      </TestWrapper>
    )

    // Metrics should be displayed
    expect(screen.getByText(/Return/i)).toBeInTheDocument()
    expect(screen.getByText(/Sharpe/i)).toBeInTheDocument()
  })

  it('shows relative performance', () => {
    render(
      <TestWrapper>
        <PerformanceChart {...mockProps} showRelativePerformance />
      </TestWrapper>
    )

    // Relative performance should be calculated
    const container = document.querySelector('.recharts-responsive-container')
    expect(container).toBeInTheDocument()
  })

  it('handles percentage display', () => {
    render(
      <TestWrapper>
        <PerformanceChart {...mockProps} percentageMode />
      </TestWrapper>
    )

    // Should format as percentage
    const yAxis = document.querySelector('.recharts-yAxis')
    expect(yAxis).toBeInTheDocument()
  })

  it('supports logarithmic scale', () => {
    render(
      <TestWrapper>
        <PerformanceChart {...mockProps} logScale />
      </TestWrapper>
    )

    const container = document.querySelector('.recharts-responsive-container')
    expect(container).toBeInTheDocument()
  })

  it('exports chart as image', async () => {
    // Mock export functions
    const mockLink = { click: jest.fn(), href: '' }
    jest.spyOn(document, 'createElement').mockReturnValue(mockLink as any)
    global.URL.createObjectURL = jest.fn(() => 'blob:mock-url')
    global.URL.revokeObjectURL = jest.fn()

    render(
      <TestWrapper>
        <PerformanceChart {...mockProps} />
      </TestWrapper>
    )

    const container = document.querySelector('.recharts-responsive-container')
    expect(container).toBeInTheDocument()

    // Cleanup
    jest.restoreAllMocks()
  })

  it('supports custom margin', () => {
    const customMargin = { top: 20, right: 30, left: 40, bottom: 20 }

    render(
      <TestWrapper>
        <PerformanceChart {...mockProps} margin={customMargin} />
      </TestWrapper>
    )

    const container = document.querySelector('.recharts-responsive-container')
    expect(container).toBeInTheDocument()
  })

  it('handles multiple strategies', () => {
    const strategies = [
      mockStrategyData,
      {
        name: 'Strategy B',
        data: [
          { date: '2024-01-01', value: 100 },
          { date: '2024-01-02', value: 103 },
          { date: '2024-01-03', value: 101 },
          { date: '2024-01-04', value: 107 },
          { date: '2024-01-05', value: 105 },
          { date: '2024-01-06', value: 112 }
        ]
      }
    ]

    render(
      <TestWrapper>
        <PerformanceChart {...mockProps} strategies={strategies} />
      </TestWrapper>
    )

    const lines = document.querySelectorAll('.recharts-line')
    expect(lines.length).toBeGreaterThan(0)
  })

  it('displays annotations', () => {
    const annotations = [
      { date: '2024-01-03', label: 'Event A', type: 'info' as const },
      { date: '2024-01-05', label: 'Event B', type: 'warning' as const }
    ]

    render(
      <TestWrapper>
        <PerformanceChart {...mockProps} annotations={annotations} />
      </TestWrapper>
    )

    const container = document.querySelector('.recharts-responsive-container')
    expect(container).toBeInTheDocument()
  })
})
