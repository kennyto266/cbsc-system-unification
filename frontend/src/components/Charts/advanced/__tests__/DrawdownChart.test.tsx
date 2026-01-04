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
  height: 400
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

  it('displays statistics', () => {
    render(
      <TestWrapper>
        <DrawdownChart {...mockProps} />
      </TestWrapper>
    )

    // Stats should show max drawdown, avg drawdown, etc.
    expect(screen.getByText(/最大回撤/i)).toBeInTheDocument()
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

  it('displays tooltip on hover', () => {
    render(
      <TestWrapper>
        <DrawdownChart {...mockProps} />
      </TestWrapper>
    )

    // Tooltip wrapper should be present
    const tooltip = document.querySelector('.recharts-tooltip-wrapper')
    expect(tooltip).toBeInTheDocument()
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

    // Should show loading pulse
    const loading = document.querySelector('.animate-pulse')
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

  it('shows grid lines', () => {
    render(
      <TestWrapper>
        <DrawdownChart {...mockProps} />
      </TestWrapper>
    )

    const grid = document.querySelector('.recharts-cartesian-grid')
    expect(grid).toBeInTheDocument()
  })
})
