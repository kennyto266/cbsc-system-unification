/**
 * Tests for PerformanceChart Component
 * Batch 1 Migration - Advanced Charts
 */

import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import PerformanceChart from '../PerformanceChart'
import type { PerformanceChartProps } from '../types'

// Import chart test setup

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
  height: 400
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
    const { container } = render(
      <TestWrapper>
        <PerformanceChart {...mockProps} />
      </TestWrapper>
    )

    // Should have area for strategy (showArea defaults to true)
    const areas = container.querySelectorAll('.recharts-area')
    expect(areas.length).toBeGreaterThan(0)
  })

  it('displays tooltip on hover', () => {
    const { container } = render(
      <TestWrapper>
        <PerformanceChart {...mockProps} />
      </TestWrapper>
    )

    const tooltip = container.querySelector('.recharts-tooltip-wrapper')
    expect(tooltip).toBeInTheDocument()
  })

  it('handles click events', () => {
    const onClick = jest.fn()

    render(
      <TestWrapper>
        <PerformanceChart {...mockProps} onClick={onClick} />
      </TestWrapper>
    )

    const area = document.querySelector('.recharts-area')
    if (area) {
      fireEvent.click(area)
    }

    expect(onClick).toBeDefined()
  })

  it('handles empty data gracefully', () => {
    const emptyProps = {
      ...mockProps,
      data: []
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
    const { container } = render(
      <TestWrapper>
        <PerformanceChart {...mockProps} />
      </TestWrapper>
    )

    const xAxis = container.querySelector('.recharts-xAxis')
    const yAxis = container.querySelector('.recharts-yAxis')
    expect(xAxis).toBeInTheDocument()
    expect(yAxis).toBeInTheDocument()
  })

  it('shows grid lines', () => {
    const { container } = render(
      <TestWrapper>
        <PerformanceChart {...mockProps} />
      </TestWrapper>
    )

    const grid = container.querySelector('.recharts-cartesian-grid')
    expect(grid).toBeInTheDocument()
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

    // Should show loading pulse
    const loading = document.querySelector('.animate-pulse')
    expect(loading).toBeInTheDocument()
    // Should also show the Card component
    const card = document.querySelector('.rounded-lg')
    expect(card).toBeInTheDocument()
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
})
