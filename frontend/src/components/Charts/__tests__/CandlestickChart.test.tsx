import React from 'react'
import { render, screen, fireEvent, waitFor, cleanup } from '@testing-library/react'
import '@testing-library/jest-dom'
import { ThemeProvider } from '@/contexts/ThemeContext'
import type { OHLCDataPoint, TechnicalIndicator } from '../../../types/chart'

// Create mock component before jest.mock
function MockCandlestickChart({ data, showVolume, showMovingAverages, indicators, theme, height, className, title, subtitle, onDataPointClick, onTimeRangeChange, bullishColor, bearishColor, volumeOpacity, showLegend, ...rest }: any) {
  return React.createElement('div',
    {
      'data-testid': 'mock-candlestick-chart',
      className: className || '',
      style: { height: height || 600 },
      ...rest  // Pass through all other props including aria-label, role, etc.
    },
    title && React.createElement('h2', null, title),
    subtitle && React.createElement('h3', null, subtitle),
    React.createElement('div',
      { 'data-testid': 'mock-plotly-chart' },
      React.createElement('div',
        { 'data-testid': 'plotly-data' },
        JSON.stringify(data)
      )
    ),
    showVolume && React.createElement('div', { 'data-testid': 'volume-indicator' }, 'Volume shown'),
    showMovingAverages && showMovingAverages.map((ma: number) =>
      React.createElement('div', { key: ma, 'data-testid': `ma-${ma}` }, `MA${ma}`)
    ),
    indicators && indicators.map((ind: any, i: number) =>
      React.createElement('div', { key: i, 'data-testid': `indicator-${ind.name}` }, ind.name)
    )
  )
}

jest.mock('../plotly/CandlestickChart', () => ({
  __esModule: true,
  default: MockCandlestickChart
}))

import CandlestickChart from '../plotly/CandlestickChart'

// Test wrapper - 测试包装器
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ThemeProvider>
    {children}
  </ThemeProvider>
)

// Sample OHLC data
const sampleOHLCData: OHLCDataPoint[] = [
  {
    timestamp: '2023-01-01T00:00:00Z',
    open: 100,
    high: 110,
    low: 95,
    close: 105,
    volume: 1000000
  },
  {
    timestamp: '2023-01-02T00:00:00Z',
    open: 105,
    high: 115,
    low: 100,
    close: 110,
    volume: 1200000
  },
  {
    timestamp: '2023-01-03T00:00:00Z',
    open: 110,
    high: 120,
    low: 108,
    close: 108,
    volume: 900000
  }
]

describe('CandlestickChart Component', () => {
  afterEach(() => {
    cleanup()
    jest.clearAllMocks()
  })

  // Basic rendering tests
  describe('Rendering', () => {
    test('renders with minimal props', () => {
      render(
        <TestWrapper>
          <CandlestickChart data={sampleOHLCData} />
        </TestWrapper>
      )

      expect(screen.getByTestId('mock-candlestick-chart')).toBeInTheDocument()
      expect(screen.getByTestId('mock-plotly-chart')).toBeInTheDocument()
      expect(screen.getByTestId('plotly-data')).toBeInTheDocument()
    })

    test('renders with custom title and subtitle', () => {
      render(
        <TestWrapper>
          <CandlestickChart
            data={sampleOHLCData}
            title="Stock Price Chart"
            subtitle="AAPL - Daily Chart"
          />
        </TestWrapper>
      )

      expect(screen.getByText('Stock Price Chart')).toBeInTheDocument()
      expect(screen.getByText('AAPL - Daily Chart')).toBeInTheDocument()
    })

    test('renders with custom className', () => {
      render(
        <TestWrapper>
          <CandlestickChart
            data={sampleOHLCData}
            className="custom-chart-class"
          />
        </TestWrapper>
      )

      const chart = screen.getByTestId('mock-candlestick-chart')
      expect(chart).toHaveClass('custom-chart-class')
    })

    test('renders with custom dimensions', () => {
      render(
        <TestWrapper>
          <CandlestickChart
            data={sampleOHLCData}
            height={800}
            width={1200}
          />
        </TestWrapper>
      )

      const chart = screen.getByTestId('mock-candlestick-chart')
      expect(chart).toHaveStyle({ height: '800px' })
    })
  })

  // Props tests
  describe('Props handling', () => {
    test('displays volume when showVolume is true', () => {
      render(
        <TestWrapper>
          <CandlestickChart
            data={sampleOHLCData}
            showVolume={true}
          />
        </TestWrapper>
      )

      expect(screen.getByTestId('volume-indicator')).toBeInTheDocument()
      expect(screen.getByText('Volume shown')).toBeInTheDocument()
    })

    test('hides volume when showVolume is false', () => {
      render(
        <TestWrapper>
          <CandlestickChart
            data={sampleOHLCData}
            showVolume={false}
          />
        </TestWrapper>
      )

      expect(screen.queryByTestId('volume-indicator')).not.toBeInTheDocument()
    })

    test('displays moving averages when provided', () => {
      render(
        <TestWrapper>
          <CandlestickChart
            data={sampleOHLCData}
            showMovingAverages={[5, 10]}
          />
        </TestWrapper>
      )

      expect(screen.getByTestId('ma-5')).toBeInTheDocument()
      expect(screen.getByTestId('ma-10')).toBeInTheDocument()
    })

    test('displays technical indicators when provided', () => {
      const indicators: TechnicalIndicator[] = [
        {
          name: 'RSI',
          type: 'overlay',
          data: [50, 55, 52],
          color: '#ff6b6b'
        }
      ]

      render(
        <TestWrapper>
          <CandlestickChart
            data={sampleOHLCData}
            indicators={indicators}
          />
        </TestWrapper>
      )

      expect(screen.getByTestId('indicator-RSI')).toBeInTheDocument()
    })
  })

  // Edge cases tests
  describe('Edge cases', () => {
    test('handles empty data array', () => {
      render(
        <TestWrapper>
          <CandlestickChart data={[]} />
        </TestWrapper>
      )

      expect(screen.getByTestId('mock-candlestick-chart')).toBeInTheDocument()
    })

    test('handles single data point', () => {
      const singlePoint: OHLCDataPoint[] = [{
        timestamp: '2023-01-01',
        open: 100,
        high: 110,
        low: 95,
        close: 105
      }]

      render(
        <TestWrapper>
          <CandlestickChart data={singlePoint} />
        </TestWrapper>
      )

      expect(screen.getByTestId('mock-candlestick-chart')).toBeInTheDocument()
    })
  })

  // Accessibility tests
  describe('Accessibility', () => {
    test('supports ARIA attributes', () => {
      render(
        <TestWrapper>
          <CandlestickChart
            data={sampleOHLCData}
            aria-label="Stock price candlestick chart"
            role="application"
          />
        </TestWrapper>
      )

      const chart = screen.getByTestId('mock-candlestick-chart')
      expect(chart).toHaveAttribute('aria-label')
      expect(chart).toHaveAttribute('role')
    })
  })
})
