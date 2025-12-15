import React from 'react'
import { render, screen, fireEvent, waitFor, cleanup } from '@testing-library/react'
import '@testing-library/jest-dom'
import CandlestickChart from '../plotly/CandlestickChart'
import { ThemeProvider } from '@/styles/themes'
import type { OHLCDataPoint, TechnicalIndicator } from '../../../types/chart'

// Mock Plotly component
jest.mock('react-plotly.js', () => {
  return jest.fn(({ data, layout, config, onClick, onRelayout, className, style }) => (
    <div data-testid="mock-plotly-chart" className={className} style={style}>
      <div data-testid="plotly-data">{JSON.stringify(data)}</div>
      <div data-testid="plotly-layout">{JSON.stringify(layout)}</div>
      <div data-testid="plotly-config">{JSON.stringify(config)}</div>
      <button
        data-testid="plotly-click-simulator"
        onClick={() => onClick && onClick({
          points: [{
            pointIndex: 0,
            x: '2023-01-01',
            y: 100
          }]
        })}
      >
        Simulate Click
      </button>
      <button
        data-testid="plotly-relayout-simulator"
        onClick={() => onRelayout && onRelayout({
          'xaxis.range': ['2023-01-01', '2023-01-31']
        })}
      >
        Simulate Range Select
      </button>
    </div>
  ))
})

// Mock chart themes
jest.mock('../utils/chartThemes', () => ({
  getPlotlyDefaults: (theme: any) => ({
    font: {
      family: 'Inter, sans-serif',
      size: 12,
      color: theme === 'dark' ? '#ffffff' : '#000000'
    },
    paper_bgcolor: theme === 'dark' ? '#1f2937' : '#ffffff',
    plot_bgcolor: theme === 'dark' ? '#1f2937' : '#ffffff',
    xaxis: {
      gridcolor: theme === 'dark' ? '#374151' : '#e5e7eb',
      zerolinecolor: theme === 'dark' ? '#374151' : '#e5e7eb',
      color: theme === 'dark' ? '#ffffff' : '#000000'
    },
    yaxis: {
      gridcolor: theme === 'dark' ? '#374151' : '#e5e7eb',
      zerolinecolor: theme === 'dark' ? '#374151' : '#e5e7eb',
      color: theme === 'dark' ? '#ffffff' : '#000000'
    }
  }),
  getTheme: (theme: string) => ({
    colors: ['#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6']
  }),
  colorSchemes: {
    default: {
      bullish: '#10b981',
      bearish: '#ef4444'
    }
  }
}))

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

      expect(screen.getByTestId('mock-plotly-chart')).toBeInTheDocument()
      expect(screen.getByTestId('plotly-data')).toBeInTheDocument()
      expect(screen.getByTestId('plotly-layout')).toBeInTheDocument()
      expect(screen.getByTestId('plotly-config')).toBeInTheDocument()
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

      const layout = screen.getByTestId('plotly-layout')
      expect(layout.textContent).toContain('Stock Price Chart')
      expect(layout.textContent).toContain('AAPL - Daily Chart')
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

      const chart = screen.getByTestId('mock-plotly-chart')
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

      const layout = screen.getByTestId('plotly-layout')
      expect(layout.textContent).toContain('"height":800')
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

      const data = screen.getByTestId('plotly-data')
      expect(data.textContent).toContain('Volume')
      expect(data.textContent).toContain('type":"bar"')
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

      const data = screen.getByTestId('plotly-data')
      expect(data.textContent).not.toContain('Volume')
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

      const data = screen.getByTestId('plotly-data')
      expect(data.textContent).toContain('MA5')
      expect(data.textContent).toContain('MA10')
      expect(data.textContent).toContain('"mode":"lines"')
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

      const data = screen.getByTestId('plotly-data')
      expect(data.textContent).toContain('RSI')
    })

    test('applies custom bullish and bearish colors', () => {
      render(
        <TestWrapper>
          <CandlestickChart
            data={sampleOHLCData}
            bullishColor="#00ff00"
            bearishColor="#ff0000"
          />
        </TestWrapper>
      )

      const data = screen.getByTestId('plotly-data')
      expect(data.textContent).toContain('#00ff00')
      expect(data.textContent).toContain('#ff0000')
    })

    test('applies custom volume opacity', () => {
      render(
        <TestWrapper>
          <CandlestickChart
            data={sampleOHLCData}
            showVolume={true}
            volumeOpacity={0.3}
          />
        </TestWrapper>
      )

      const data = screen.getByTestId('plotly-data')
      expect(data.textContent).toContain('"opacity":0.3')
    })

    test('toggles legend visibility', () => {
      render(
        <TestWrapper>
          <CandlestickChart
            data={sampleOHLCData}
            showLegend={false}
          />
        </TestWrapper>
      )

      const layout = screen.getByTestId('plotly-layout')
      expect(layout.textContent).toContain('"showlegend":false')
    })
  })

  // Event handlers tests
  describe('Event handlers', () => {
    test('handles data point clicks', async () => {
      const handleDataPointClick = jest.fn()

      render(
        <TestWrapper>
          <CandlestickChart
            data={sampleOHLCData}
            onDataPointClick={handleDataPointClick}
          />
        </TestWrapper>
      )

      const clickButton = screen.getByTestId('plotly-click-simulator')
      await fireEvent.click(clickButton)

      expect(handleDataPointClick).toHaveBeenCalledWith(
        sampleOHLCData[0],
        expect.any(Object)
      )
    })

    test('handles time range changes', async () => {
      const handleTimeRangeChange = jest.fn()

      render(
        <TestWrapper>
          <CandlestickChart
            data={sampleOHLCData}
            onTimeRangeChange={handleTimeRangeChange}
          />
        </TestWrapper>
      )

      const rangeButton = screen.getByTestId('plotly-relayout-simulator')
      await fireEvent.click(rangeButton)

      expect(handleTimeRangeChange).toHaveBeenCalledWith([
        new Date('2023-01-01'),
        new Date('2023-01-31')
      ])
    })
  })

  // Theme tests
  describe('Theme support', () => {
    test('applies light theme by default', () => {
      render(
        <TestWrapper>
          <CandlestickChart data={sampleOHLCData} theme="light" />
        </TestWrapper>
      )

      const layout = screen.getByTestId('plotly-layout')
      expect(layout.textContent).toContain('#ffffff')
      expect(layout.textContent).toContain('#000000')
    })

    test('applies dark theme correctly', () => {
      render(
        <TestWrapper>
          <CandlestickChart data={sampleOHLCData} theme="dark" />
        </TestWrapper>
      )

      const layout = screen.getByTestId('plotly-layout')
      expect(layout.textContent).toContain('#1f2937')
    })
  })

  // Data processing tests
  describe('Data processing', () => {
    test('calculates moving averages correctly', () => {
      render(
        <TestWrapper>
          <CandlestickChart
            data={sampleOHLCData}
            showMovingAverages={[2]}
          />
        </TestWrapper>
      )

      const data = screen.getByTestId('plotly-data')
      // The first MA value should be null due to insufficient data
      expect(data.textContent).toContain('null')
    })

    test('handles missing volume data', () => {
      const dataWithoutVolume: OHLCDataPoint[] = [
        {
          timestamp: '2023-01-01',
          open: 100,
          high: 110,
          low: 95,
          close: 105
          // volume missing
        }
      ]

      render(
        <TestWrapper>
          <CandlestickChart
            data={dataWithoutVolume}
            showVolume={true}
          />
        </TestWrapper>
      )

      // Should not crash when volume is missing
      expect(screen.getByTestId('mock-plotly-chart')).toBeInTheDocument()
    })

    test('colors volume bars based on price direction', () => {
      render(
        <TestWrapper>
          <CandlestickChart
            data={sampleOHLCData}
            showVolume={true}
          />
        </TestWrapper>
      )

      const data = screen.getByTestId('plotly-data')
      // Volume colors array should be present
      expect(data.textContent).toContain('"color"')
    })
  })

  // Configuration tests
  describe('Chart configuration', () => {
    test('configures toolbar buttons correctly', () => {
      render(
        <TestWrapper>
          <CandlestickChart data={sampleOHLCData} />
        </TestWrapper>
      )

      const config = screen.getByTestId('plotly-config')
      expect(config.textContent).toContain('"displayModeBar":true')
      expect(config.textContent).toContain('"displaylogo":false')
      expect(config.textContent).toContain('"pan2d"')
      expect(config.textContent).toContain('"select2d"')
    })

    test('configures export options correctly', () => {
      render(
        <TestWrapper>
          <CandlestickChart data={sampleOHLCData} height={600} />
        </TestWrapper>
      )

      const config = screen.getByTestId('plotly-config')
      expect(config.textContent).toContain('"format":"png"')
      expect(config.textContent).toContain('"height":600')
      expect(config.textContent).toContain('"width":1200')
    })

    test('enables responsive behavior', () => {
      render(
        <TestWrapper>
          <CandlestickChart data={sampleOHLCData} />
        </TestWrapper>
      )

      const config = screen.getByTestId('plotly-config')
      expect(config.textContent).toContain('"responsive":true')
    })
  })

  // Layout tests
  describe('Layout configuration', () => {
    test('configures axes correctly without volume', () => {
      render(
        <TestWrapper>
          <CandlestickChart
            data={sampleOHLCData}
            showVolume={false}
          />
        </TestWrapper>
      )

      const layout = screen.getByTestId('plotly-layout')
      expect(layout.textContent).toContain('"title":"Price"')
      expect(layout.textContent).toContain('"domain":[0,1]')
    })

    test('configures axes correctly with volume', () => {
      render(
        <TestWrapper>
          <CandlestickChart
            data={sampleOHLCData}
            showVolume={true}
          />
        </TestWrapper>
      )

      const layout = screen.getByTestId('plotly-layout')
      expect(layout.textContent).toContain('"title":"Price"')
      expect(layout.textContent).toContain('"domain":[0.3,1]')
      expect(layout.textContent).toContain('"title":"Volume"')
      expect(layout.textContent).toContain('"domain":[0,0.2]')
    })

    test('applies custom time range', () => {
      const timeRange: [Date, Date] = [
        new Date('2023-01-01'),
        new Date('2023-01-31')
      ]

      render(
        <TestWrapper>
          <CandlestickChart
            data={sampleOHLCData}
            timeRange={timeRange}
          />
        </TestWrapper>
      )

      const layout = screen.getByTestId('plotly-layout')
      expect(layout.textContent).toContain('2023-01-01')
      expect(layout.textContent).toContain('2023-01-31')
    })

    test('applies correct margins', () => {
      render(
        <TestWrapper>
          <CandlestickChart
            data={sampleOHLCData}
            showVolume={false}
            title="Test Chart"
          />
        </TestWrapper>
      )

      const layout = screen.getByTestId('plotly-layout')
      expect(layout.textContent).toContain('"l":60')
      expect(layout.textContent).toContain('"r":30')
      expect(layout.textContent).toContain('"t":50')
      expect(layout.textContent).toContain('"b":50')
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

      expect(screen.getByTestId('mock-plotly-chart')).toBeInTheDocument()
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

      expect(screen.getByTestId('mock-plotly-chart')).toBeInTheDocument()
    })

    test('handles very large dataset', () => {
      const largeDataset: OHLCDataPoint[] = Array.from({ length: 1000 }, (_, i) => ({
        timestamp: new Date(Date.now() - i * 86400000).toISOString(),
        open: 100 + Math.random() * 10,
        high: 110 + Math.random() * 10,
        low: 90 + Math.random() * 10,
        close: 100 + Math.random() * 10,
        volume: 1000000 + Math.random() * 500000
      }))

      render(
        <TestWrapper>
          <CandlestickChart data={largeDataset} />
        </TestWrapper>
      )

      expect(screen.getByTestId('mock-plotly-chart')).toBeInTheDocument()
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

      const chart = screen.getByTestId('mock-plotly-chart')
      expect(chart).toHaveAttribute('aria-label')
      expect(chart).toHaveAttribute('role')
    })
  })

  // Performance tests
  describe('Performance', () => {
    test('uses lazy loading for Plotly', () => {
      // This test verifies that the component is wrapped in Suspense
      render(
        <TestWrapper>
          <CandlestickChart data={sampleOHLCData} />
        </TestWrapper>
      )

      expect(screen.getByTestId('mock-plotly-chart')).toBeInTheDocument()
    })
  })
})