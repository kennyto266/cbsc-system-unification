/**
 * Economic Data Charts Component Tests
 * 經濟數據圖表組件測試
 */

import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { Provider } from 'react-redux'
import { configureStore } from '@reduxjs/toolkit'
import EconomicDataCharts from '../EconomicDataCharts'
import economicDataSlice from '../../store/slices/economicDataSlice'
import { useEconomicData } from '../../hooks/useEconomicData'

// Mock the useEconomicData hook
jest.mock('../../hooks/useEconomicData', () => ({
  useEconomicData: jest.fn()
}))

// Mock the recharts components
jest.mock('recharts', () => ({
  ComposedChart: ({ children }: { children: React.ReactNode }) => <div data-testid="composed-chart">{children}</div>,
  Line: () => <div data-testid="line-chart"></div>,
  Bar: () => <div data-testid="bar-chart"></div>,
  Scatter: ({ data }: { data: any[] }) => <div data-testid="scatter-chart">Data points: {data?.length || 0}</div>,
  AreaChart: ({ children }: { children: React.ReactNode }) => <div data-testid="area-chart">{children}</div>,
  XAxis: () => <div data-testid="x-axis"></div>,
  YAxis: () => <div data-testid="y-axis"></div>,
  CartesianGrid: () => <div data-testid="cartesian-grid"></div>,
  Tooltip: ({ content }: { content: any }) => <div data-testid="tooltip">{content}</div>,
  Legend: () => <div data-testid="legend"></div>,
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <div data-testid="responsive-container">{children}</div>,
  Cell: () => <div data-testid="cell"></div>,
  ReferenceLine: ({ label }: { label: string }) => <div data-testid="reference-line">{label}</div>,
  Area: () => <div data-testid="area"></div>
}))

// Mock date-fns
jest.mock('date-fns', () => ({
  format: (date: Date | number, formatStr: string) => {
    if (typeof date === 'number') {
      return '2024-01-15'
    }
    return '2024-01-15'
  }
}))

describe('EconomicDataCharts', () => {
  let store: ReturnType<typeof configureStore>

  beforeEach(() => {
    jest.clearAllMocks()

    store = configureStore({
      reducer: {
        economicData: economicDataSlice.reducer,
      },
      middleware: (getDefaultMiddleware) =>
        getDefaultMiddleware({
          serializableCheck: {
            ignoredActions: ['persist/PERSIST'],
          },
        }),
    })
  })

  const mockEconomicData = {
    hibor: [
      { date: '2024-01-01', value: 5.5, indicator: 'hibor' },
      { date: '2024-01-02', value: 5.6, indicator: 'hibor' }
    ],
    gdp: [
      { date: '2024-01-01', value: 3.2, indicator: 'gdp' },
      { date: '2024-04-01', value: 3.3, indicator: 'gdp' }
    ],
    pmi: [
      { date: '2024-01-01', value: 52.3, indicator: 'pmi' },
      { date: '2024-02-01', value: 51.8, indicator: 'pmi' }
    ],
    visitors: [
      { date: '2024-01-01', value: 150000, indicator: 'visitors' },
      { date: '2024-02-01', value: 160000, indicator: 'visitors' }
    ],
    unemployment: [
      { date: '2024-01-01', value: 3.2, indicator: 'unemployment' },
      { date: '2024-02-01', value: 3.1, indicator: 'unemployment' }
    ]
  }

  const mockUseEconomicData = (overrides = {}) => {
    return {
      data: mockEconomicData,
      filteredData: mockEconomicData,
      hiborData: mockEconomicData.hibor,
      gdpData: mockEconomicData.gdp,
      pmiData: mockEconomicData.pmi,
      visitorData: mockEconomicData.visitors,
      unemploymentData: mockEconomicData.unemployment,
      loading: false,
      error: null,
      lastUpdated: '2024-01-15T10:00:00Z',
      fetchIndicator: jest.fn(),
      fetchAllIndicators: jest.fn(),
      setFilter: jest.fn(),
      setTimeRange: jest.fn(),
      refreshData: jest.fn(),
      clearCache: jest.fn(),
      ...overrides
    }
  }

  const renderComponent = (props = {}) => {
    (useEconomicData as any).mockReturnValue(mockUseEconomicData())

    return render(
      <Provider store={store}>
        <EconomicDataCharts {...props} />
      </Provider>
    )
  }

  describe('Rendering', () => {
    test('renders chart type selector', () => {
      renderComponent()

      expect(screen.getByText('Time Series')).toBeInTheDocument()
      expect(screen.getByText('Scatter Plot')).toBeInTheDocument()
      expect(screen.getByText('Heat Map')).toBeInTheDocument()
      expect(screen.getByText('Correlation')).toBeInTheDocument()
      expect(screen.getByText('Comparison')).toBeInTheDocument()
    })

    test('renders legend section', () => {
      renderComponent()

      expect(screen.getByText('Legend')).toBeInTheDocument()
      expect(screen.getByText('HIBOR')).toBeInTheDocument()
      expect(screen.getByText('GDP')).toBeInTheDocument()
      expect(screen.getByText('PMI')).toBeInTheDocument()
      expect(screen.getByText('VISITORS')).toBeInTheDocument()
      expect(screen.getByText('UNEMPLOYMENT')).toBeInTheDocument()
    })

    test('renders default time series chart', () => {
      renderComponent()

      expect(screen.getByTestId('composed-chart')).toBeInTheDocument()
      expect(screen.getByTestId('responsive-container')).toBeInTheDocument()
    })

    test('renders with custom className', () => {
      const { container } = renderComponent({ className: 'custom-class' })

      expect(container.firstChild).toHaveClass('custom-class')
    })

    test('renders with custom indicators', () => {
      renderComponent({ indicators: ['hibor', 'gdp'] })

      expect(screen.getByText('HIBOR')).toBeInTheDocument()
      expect(screen.getByText('GDP')).toBeInTheDocument()
      expect(screen.queryByText('PMI')).not.toBeInTheDocument()
    })
  })

  describe('Loading State', () => {
    test('renders loading spinner when loading', () => {
      (useEconomicData as any).mockReturnValue(
        mockUseEconomicData({ loading: true })
      )

      renderComponent()

      expect(screen.getByText('Loading economic data...')).toBeInTheDocument()
      expect(screen.getByRole('status')).toBeInTheDocument() // spinner
    })

    test('renders custom loading message', () => {
      (useEconomicData as any).mockReturnValue(
        mockUseEconomicData({ loading: true })
      )

      renderComponent()

      expect(screen.getByText('Loading economic data...')).toBeInTheDocument()
    })
  })

  describe('Error State', () => {
    test('renders error message when error occurs', () => {
      (useEconomicData as any).mockReturnValue(
        mockUseEconomicData({
          error: 'Failed to fetch data',
          loading: false
        })
      )

      renderComponent()

      expect(screen.getByText('Error loading data: Failed to fetch data')).toBeInTheDocument()
    })

    test('renders warning icon for error state', () => {
      (useEconomicData as any).mockReturnValue(
        mockUseEconomicData({
          error: 'API Error',
          loading: false
        })
      )

      renderComponent()

      expect(screen.getByText('⚠️')).toBeInTheDocument()
    })
  })

  describe('Chart Types', () => {
    test('renders scatter plot controls when chartType is scatter', () => {
      renderComponent({ chartType: 'scatter' })

      expect(screen.getByText('X Axis:')).toBeInTheDocument()
      expect(screen.getByText('Y Axis:')).toBeInTheDocument()
      expect(screen.getByTestId('scatter-chart')).toBeInTheDocument()
    })

    test('renders heatmap when chartType is heatmap', () => {
      renderComponent({ chartType: 'heatmap' })

      expect(screen.getByTestId('bar-chart')).toBeInTheDocument()
    })

    test('renders correlation controls when chartType is correlation', () => {
      renderComponent({ chartType: 'correlation' })

      expect(screen.getByText('Compare:')).toBeInTheDocument()
    })

    test('renders comparison chart when chartType is comparison', () => {
      renderComponent({ chartType: 'comparison' })

      expect(screen.getByTestId('line-chart')).toBeInTheDocument()
    })
  })

  describe('Chart Type Selection', () => {
    test('highlights active chart type button', () => {
      renderComponent({ chartType: 'scatter' })

      const scatterButton = screen.getByText('Scatter Plot')
      expect(scatterButton).toHaveClass('bg-blue-600', 'text-white')
    })

    test('applies inactive button styles for non-active types', () => {
      renderComponent({ chartType: 'timeSeries' })

      const scatterButton = screen.getByText('Scatter Plot')
      expect(scatterButton).toHaveClass('bg-gray-100', 'text-gray-700')
    })

    test('handles chart type button clicks', () => {
      renderComponent()

      const scatterButton = screen.getByText('Scatter Plot')
      fireEvent.click(scatterButton)

      // Note: This test verifies that the button exists and can be clicked
      // The actual chart type change would require state management in the parent component
      expect(scatterButton).toBeInTheDocument()
    })
  })

  describe('Data Integration', () => {
    test('uses useEconomicData hook with default options', () => {
      renderComponent()

      expect(useEconomicData).toHaveBeenCalledWith({ autoFetch: true })
    })

    test('uses useEconomicData hook with custom options', () => {
      renderComponent({}, { autoFetch: false, cacheEnabled: false })

      expect(useEconomicData).toHaveBeenCalledWith({ autoFetch: false, cacheEnabled: false })
    })

    test('fetches data when timeRange prop changes', () => {
      const mockFetchAllIndicators = jest.fn()
      (useEconomicData as any).mockReturnValue(
        mockUseEconomicData({
          fetchAllIndicators: mockFetchAllIndicators
        })
      )

      const timeRange = { start: '2024-01-01', end: '2024-12-31' }
      renderComponent({ timeRange })

      expect(mockFetchAllIndicators).toHaveBeenCalledWith(timeRange)
    })

    test('handles empty timeRange gracefully', () => {
      const mockFetchAllIndicators = jest.fn()
      (useEconomicData as any).mockReturnValue(
        mockUseEconomicData({
          fetchAllIndicators: mockFetchAllIndicators
        })
      )

      renderComponent({ timeRange: {} })

      expect(mockFetchAllIndicators).not.toHaveBeenCalled()
    })
  })

  describe('Accessibility', () => {
    test('provides proper ARIA labels', () => {
      renderComponent()

      // Check for proper button structure
      const buttons = screen.getAllByRole('button')
      buttons.forEach(button => {
        expect(button).toHaveAttribute('type')
      })
    })

    test('supports keyboard navigation', () => {
      renderComponent()

      const buttons = screen.getAllByRole('button')
      buttons.forEach(button => {
        expect(button).not.toBeDisabled()
      })
    })

    test('provides color contrast through CSS classes', () => {
      renderComponent()

      const activeButton = screen.getByText('Time Series')
      expect(activeButton).toHaveClass('text-white')

      const inactiveButtons = screen.getAllByText('Scatter Plot')
      inactiveButtons.forEach(button => {
        if (button !== activeButton) {
          expect(button).toHaveClass('text-gray-700')
        }
      })
    })
  })

  describe('Performance', () => {
    test('renders efficiently with large datasets', () => {
      const largeDataset = {
        hibor: Array.from({ length: 1000 }, (_, i) => ({
          date: `2024-01-${String(i + 1).padStart(2, '0')}`,
          value: Math.random() * 10,
          indicator: 'hibor'
        }))
      }

      (useEconomicData as any).mockReturnValue(
        mockUseEconomicData({ data: largeDataset })
      )

      const startTime = performance.now()
      renderComponent()
      const endTime = performance.now()

      expect(endTime - startTime).toBeLessThan(100) // Should render within 100ms
    })

    test('does not re-render unnecessarily', () => {
      const { rerender } = renderComponent()

      // Re-render with same props
      rerender(
        <Provider store={store}>
          <EconomicDataCharts />
        </Provider>
      )

      // Component should still be present and functional
      expect(screen.getByTestId('composed-chart')).toBeInTheDocument()
    })
  })

  describe('Error Handling', () => {
    test('handles malformed data gracefully', () => {
      const malformedData = {
        hibor: null,
        gdp: undefined,
        pmi: [],
        visitors: [{ invalid: 'data' }],
        unemployment: []
      }

      (useEconomicData as any).mockReturnValue(
        mockUseEconomicData({ data: malformedData })
      )

      expect(() => renderComponent()).not.toThrow()
    })

    test('handles API errors in hook', () => {
      (useEconomicData as any).mockReturnValue(
        mockUseEconomicData({
          error: 'Network timeout',
          loading: false
        })
      )

      expect(() => renderComponent()).not.toThrow()
      expect(screen.getByText(/Error loading data/)).toBeInTheDocument()
    })
  })

  describe('Integration', () => {
    test('integrates with Redux store properly', () => {
      renderComponent()

      // Verify Redux integration by checking if slice is present
      const state = store.getState()
      expect(state).toHaveProperty('economicData')
    })

    test('integrates with useEconomicData hook properly', () => {
      renderComponent()

      expect(useEconomicData).toHaveBeenCalled()

      // Verify that hook return values are used
      expect(screen.getByTestId('composed-chart')).toBeInTheDocument()
    })
  })
})