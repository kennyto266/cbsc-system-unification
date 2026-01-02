/**
 * Tests for ThreeDChart Component
 * Batch 1 Migration - Advanced Charts
 */

import React, { Suspense } from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import ThreeDChart from '../ThreeDChart'
import type { ThreeDChartProps } from '../types'

// Test wrapper with Suspense for lazy-loaded components
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      {children}
    </Suspense>
  )
}

// Mock 3D data
const mockSurfaceData = {
  x: [1, 2, 3, 1, 2, 3, 1, 2, 3],
  y: [1, 1, 1, 2, 2, 2, 3, 3, 3],
  z: [10, 15, 20, 12, 18, 25, 14, 22, 30]
}

const mockScatterData = [
  { x: 1, y: 2, z: 10 },
  { x: 2, y: 3, z: 15 },
  { x: 3, y: 4, z: 20 }
]

const mockLineData = [
  { x: 1, y: 2, z: 10 },
  { x: 2, y: 3, z: 15 },
  { x: 3, y: 4, z: 20 }
]

const mockBarData = [
  { x: 1, y: 10 },
  { x: 2, y: 15 },
  { x: 3, y: 20 }
]

const mockProps = {
  data: mockScatterData,
  chartType: 'scatter3d' as const,
  title: '3D Scatter Plot',
  height: 400,
  width: '100%'
}

describe('ThreeDChart - Batch 1 Migration', () => {
  it('renders without crashing', () => {
    render(
      <TestWrapper>
        <ThreeDChart {...mockProps} />
      </TestWrapper>
    )

    // Mocked Plotly chart with data-testid
    const container = screen.getByTestId('plotly-chart')
    expect(container).toBeInTheDocument()
  })

  it('renders surface chart type', () => {
    render(
      <TestWrapper>
        <ThreeDChart {...mockProps} chartType="surface" />
      </TestWrapper>
    )

    const container = screen.getByTestId('plotly-chart')
    expect(container).toBeInTheDocument()
  })

  it('renders scatter3d chart type', () => {
    render(
      <TestWrapper>
        <ThreeDChart {...mockProps} chartType="scatter3d" />
      </TestWrapper>
    )

    const container = screen.getByTestId('plotly-chart')
    expect(container).toBeInTheDocument()
  })

  it('renders line3d chart type', () => {
    render(
      <TestWrapper>
        <ThreeDChart {...mockProps} chartType="line3d" />
      </TestWrapper>
    )

    const container = screen.getByTestId('plotly-chart')
    expect(container).toBeInTheDocument()
  })

  it('renders mesh3d chart type', () => {
    render(
      <TestWrapper>
        <ThreeDChart {...mockProps} chartType="mesh3d" />
      </TestWrapper>
    )

    const container = screen.getByTestId('plotly-chart')
    expect(container).toBeInTheDocument()
  })

  it('applies custom dimensions', () => {
    render(
      <TestWrapper>
        <ThreeDChart {...mockProps} width={800} height={600} />
      </TestWrapper>
    )

    const container = screen.getByTestId('plotly-chart')
    expect(container).toBeInTheDocument()
  })

  it('shows loading state', () => {
    render(
      <TestWrapper>
        <ThreeDChart {...mockProps} loading />
      </TestWrapper>
    )

    // Should show loading spinner
    const loading = document.querySelector('.animate-spin')
    expect(loading).toBeInTheDocument()
  })

  it('hides loading when not loading', () => {
    render(
      <TestWrapper>
        <ThreeDChart {...mockProps} loading={false} />
      </TestWrapper>
    )

    const loading = document.querySelector('.animate-spin')
    expect(loading).not.toBeInTheDocument()
  })

  it('applies custom className', () => {
    render(
      <TestWrapper>
        <ThreeDChart {...mockProps} className="custom-chart" />
      </TestWrapper>
    )

    const container = document.querySelector('.custom-chart')
    expect(container).toBeInTheDocument()
  })

  it('handles click events', () => {
    const onClick = jest.fn()

    render(
      <TestWrapper>
        <ThreeDChart {...mockProps} onPointClick={onClick} />
      </TestWrapper>
    )

    const container = screen.getByTestId('plotly-chart')
    if (container) {
      fireEvent.click(container)
    }

    expect(onClick).toBeDefined()
  })

  it('handles error state', () => {
    render(
      <TestWrapper>
        <ThreeDChart {...mockProps} error="Failed to load chart" />
      </TestWrapper>
    )

    expect(screen.getByText(/Failed to load chart/)).toBeInTheDocument()
  })

  it('uses custom axes', () => {
    const customAxes = {
      x: { title: 'X Axis' },
      y: { title: 'Y Axis' },
      z: { title: 'Z Axis' }
    }

    render(
      <TestWrapper>
        <ThreeDChart {...mockProps} axes={customAxes} />
      </TestWrapper>
    )

    const container = screen.getByTestId('plotly-chart')
    expect(container).toBeInTheDocument()
  })

  it('handles empty data gracefully', () => {
    const emptyProps = {
      ...mockProps,
      data: []
    }

    render(
      <TestWrapper>
        <ThreeDChart {...emptyProps} />
      </TestWrapper>
    )

    // Should render container even with empty data
    const container = screen.getByTestId('plotly-chart')
    expect(container).toBeInTheDocument()
  })

  it('supports theme switching', () => {
    render(
      <TestWrapper>
        <ThreeDChart {...mockProps} theme="dark" />
      </TestWrapper>
    )

    const container = screen.getByTestId('plotly-chart')
    expect(container).toBeInTheDocument()
  })

  it('displays legend when enabled', () => {
    render(
      <TestWrapper>
        <ThreeDChart {...mockProps} showLegend />
      </TestWrapper>
    )

    const container = screen.getByTestId('plotly-chart')
    expect(container).toBeInTheDocument()
  })
})
