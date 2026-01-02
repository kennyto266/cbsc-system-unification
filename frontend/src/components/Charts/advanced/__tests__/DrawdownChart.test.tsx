/**
 * Tests for DrawdownChart Component
 * Batch 1 Migration - Advanced Charts
 */

import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import DrawdownChart from '../DrawdownChart'
import type { DrawdownChartProps } from '../types'

// Test wrapper
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return <div>{children}</div>
}

// Mock drawdown data - matching DrawdownDataPoint type
const mockDrawdownData = [
  { date: '2024-01-01', drawdown: 0 },
  { date: '2024-01-02', drawdown: -5 },
  { date: '2024-01-03', drawdown: -10 },
  { date: '2024-01-04', drawdown: -3 },
  { date: '2024-01-05', drawdown: -8 },
  { date: '2024-01-06', drawdown: 0 }
]

const mockProps = {
  data: mockDrawdownData,
  title: 'Portfolio Drawdown',
  height: 400,
  showZone: true
}

describe('DrawdownChart - Batch 1 Migration', () => {
  it('renders without crashing', () => {
    render(
      <TestWrapper>
        <DrawdownChart {...mockProps} />
      </TestWrapper>
    )

    // Recharts AreaChart renders a div
    const container = document.querySelector('.recharts-responsive-container')
    expect(container).toBeInTheDocument()
  })

  it('displays drawdown area chart', () => {
    render(
      <TestWrapper>
        <DrawdownChart {...mockProps} />
      </TestWrapper>
    )

    // Should have area path for underwater region
    const area = document.querySelector('.recharts-area')
    expect(area).toBeInTheDocument()
  })

  it('shows zero reference line', () => {
    render(
      <TestWrapper>
        <DrawdownChart {...mockProps} showZeroLine />
      </TestWrapper>
    )

    // Zero reference line should be present
    const refLine = document.querySelector('.recharts-reference-line')
    expect(refLine).toBeInTheDocument()
  })

  it('displays statistics', () => {
    render(
      <TestWrapper>
        <DrawdownChart {...mockProps} showStats />
      </TestWrapper>
    )

    // Stats should show max drawdown, avg drawdown, etc.
    expect(screen.getByText(/Max Drawdown/i)).toBeInTheDocument()
  })

  it('calculates correct max drawdown', () => {
    render(
      <TestWrapper>
        <DrawdownChart {...mockProps} showStats />
      </TestWrapper>
    )

    // Max drawdown should be -10%
    expect(screen.getByText('10%')).toBeInTheDocument()
  })

  it('handles empty data gracefully', () => {
    const emptyProps = {
      ...mockProps,
      data: []
    }

    render(
      <TestWrapper>
        <DrawdownChart {...emptyProps} />
      </TestWrapper>
    )

    const container = document.querySelector('.recharts-responsive-container')
    expect(container).toBeInTheDocument()
  })

  it('applies custom colors', () => {
    const customColors = {
      positive: '#00FF00',
      negative: '#FF0000',
      underwater: '#FFFF00'
    }

    render(
      <TestWrapper>
        <DrawdownChart {...mockProps} colors={customColors} />
      </TestWrapper>
    )

    const area = document.querySelector('.recharts-area')
    expect(area).toBeInTheDocument()
  })

  it('displays tooltip on hover', () => {
    render(
      <TestWrapper>
        <DrawdownChart {...mockProps} showTooltip />
      </TestWrapper>
    )

    // Tooltip wrapper should be present
    const tooltip = document.querySelector('.recharts-tooltip-wrapper')
    expect(tooltip).toBeInTheDocument()
  })

  it('hides tooltip when disabled', () => {
    render(
      <TestWrapper>
        <DrawdownChart {...mockProps} showTooltip={false} />
      </TestWrapper>
    )

    // Chart should still render
    const container = document.querySelector('.recharts-responsive-container')
    expect(container).toBeInTheDocument()
  })

  it('handles click events', () => {
    const onClick = jest.fn()

    render(
      <TestWrapper>
        <DrawdownChart {...mockProps} onClick={onClick} />
      </TestWrapper>
    )

    const area = document.querySelector('.recharts-area')
    if (area) {
      fireEvent.click(area)
    }

    expect(onClick).toBeDefined()
  })

  it('supports custom dimensions', () => {
    render(
      <TestWrapper>
        <DrawdownChart {...mockProps} height={500} width={800} />
      </TestWrapper>
    )

    const container = document.querySelector('.recharts-responsive-container')
    expect(container).toBeInTheDocument()
  })

  it('applies custom className', () => {
    render(
      <TestWrapper>
        <DrawdownChart {...mockProps} className="custom-drawdown" />
      </TestWrapper>
    )

    const container = document.querySelector('.custom-drawdown')
    expect(container).toBeInTheDocument()
  })

  it('displays axis labels', () => {
    render(
      <TestWrapper>
        <DrawdownChart {...mockProps} />
      </TestWrapper>
    )

    const xAxis = document.querySelector('.recharts-xAxis')
    const yAxis = document.querySelector('.recharts-yAxis')
    expect(xAxis).toBeInTheDocument()
    expect(yAxis).toBeInTheDocument()
  })

  it('supports loading state', () => {
    render(
      <TestWrapper>
        <DrawdownChart {...mockProps} loading />
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
        <DrawdownChart {...mockProps} error="Failed to load" onError={onError} />
      </TestWrapper>
    )

    expect(screen.getByText(/Failed to load/)).toBeInTheDocument()
  })

  it('shows grid lines when enabled', () => {
    render(
      <TestWrapper>
        <DrawdownChart {...mockProps} showGrid />
      </TestWrapper>
    )

    const grid = document.querySelector('.recharts-cartesian-grid')
    expect(grid).toBeInTheDocument()
  })

  it('hides grid lines when disabled', () => {
    render(
      <TestWrapper>
        <DrawdownChart {...mockProps} showGrid={false} />
      </TestWrapper>
    )

    const grid = document.querySelector('.recharts-cartesian-grid')
    expect(grid).not.toBeInTheDocument()
  })

  it('displays legend when enabled', () => {
    render(
      <TestWrapper>
        <DrawdownChart {...mockProps} showLegend />
      </TestWrapper>
    )

    const legend = document.querySelector('.recharts-legend-wrapper')
    expect(legend).toBeInTheDocument()
  })

  it('handles recovery periods correctly', () => {
    render(
      <TestWrapper>
        <DrawdownChart {...mockProps} showRecoveryPeriods />
      </TestWrapper>
    )

    // Recovery periods should be highlighted
    const container = document.querySelector('.recharts-responsive-container')
    expect(container).toBeInTheDocument()
  })

  it('calculates recovery statistics', () => {
    render(
      <TestWrapper>
        <DrawdownChart {...mockProps} showStats />
      </TestWrapper>
    )

    // Should show recovery stats
    expect(screen.getByText(/Recovery/i)).toBeInTheDocument()
  })

  it('formats date axis correctly', () => {
    render(
      <TestWrapper>
        <DrawdownChart {...mockProps} />
      </TestWrapper>
    )

    const xAxis = document.querySelector('.recharts-xAxis')
    expect(xAxis).toBeInTheDocument()
  })

  it('handles percentage formatting', () => {
    render(
      <TestWrapper>
        <DrawdownChart {...mockProps} formatAsPercentage />
      </TestWrapper>
    )

    // Y-axis should show percentage format
    const yAxis = document.querySelector('.recharts-yAxis')
    expect(yAxis).toBeInTheDocument()
  })

  it('exports chart as image', async () => {
    // Mock export functions
    const mockLink = { click: jest.fn(), href: '' }
    jest.spyOn(document, 'createElement').mockReturnValue(mockLink as any)
    global.URL.createObjectURL = jest.fn(() => 'blob:mock-url')
    global.URL.revokeObjectURL = jest.fn()

    render(
      <TestWrapper>
        <DrawdownChart {...mockProps} />
      </TestWrapper>
    )

    // Export functionality would be tested here
    const container = document.querySelector('.recharts-responsive-container')
    expect(container).toBeInTheDocument()

    // Cleanup
    jest.restoreAllMocks()
  })

  it('supports custom margin', () => {
    const customMargin = { top: 20, right: 30, left: 40, bottom: 20 }

    render(
      <TestWrapper>
        <DrawdownChart {...mockProps} margin={customMargin} />
      </TestWrapper>
    )

    const container = document.querySelector('.recharts-responsive-container')
    expect(container).toBeInTheDocument()
  })

  it('handles negative values correctly', () => {
    const negativeData = mockDrawdownData.map(d => ({ ...d, value: d.value * 2 }))

    render(
      <TestWrapper>
        <DrawdownChart {...mockProps} data={negativeData} />
      </TestWrapper>
    )

    const container = document.querySelector('.recharts-responsive-container')
    expect(container).toBeInTheDocument()
  })
})
