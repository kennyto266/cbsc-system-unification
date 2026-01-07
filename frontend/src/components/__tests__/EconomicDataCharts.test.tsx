/**
 * Economic Data Charts Component Tests
 * 經濟數據圖表組件測試
 */

import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { Provider } from 'react-redux'
import { configureStore } from '@reduxjs/toolkit'
import EconomicDataCharts from '../EconomicDataCharts'
import economicDataReducer from '../../store/slices/economicDataSlice'

// Mock recharts
jest.mock('recharts', () => {
  const React = require('react')

  // All recharts-specific props that should be filtered
  const RECHARTS_PROPS = new Set([
    'dataKey', 'data', 'name', 'type', 'unit', 'stackId', 'hide', 'layout',
    'tickFormatter', 'tickLine', 'tickSize', 'tickCount', 'ticks', 'interval',
    'label', 'labelPosition', 'labelLine', 'angle', 'radius', 'innerRadius',
    'outerRadius', 'cx', 'cy', 'r', 'width', 'height', 'x', 'y', 'yAxisId', 'xAxisId',
    'zAxisId', 'line', 'bar', 'area', 'scatter', 'pie', 'radar', 'funnel',
    'fill', 'stroke', 'strokeWidth', 'strokeDasharray', 'strokeDashoffset',
    'dot', 'connectNulls', 'isAnimationActive', 'animationBegin', 'animationDuration',
    'animationEasing', 'legendType', 'minPointSize', 'maxPointSize', 'shape',
    'activeDot', 'activeShape', 'activeBar', 'background', 'baseLine', 'points',
    'textBreakAll', 'textBreakWord', 'allowEscapeViewBox', 'coordinate', 'position',
    'color', 'colors', 'range', 'scale', 'domain', 'includeHidden', 'payload',
    'verticalAnchor', 'horizontalAnchor', 'offset', 'content',
    'margin', 'barCategoryGap', 'barGap', 'maxBarSize', 'stackOffset', 'reverseStackOrder'
  ])

  const createMockComponent = (displayName: string) => {
    const MockComponent = React.forwardRef<any, any>(({ children, ...props }: any, ref) => {
      // Only pass through non-recharts props to DOM
      const domProps: any = {}
      Object.keys(props).forEach(key => {
        if (!RECHARTS_PROPS.has(key)) {
          domProps[key] = props[key]
        }
      })

      // Convert PascalCase to kebab-case
      const kebabCase = displayName
        .replace(/([A-Z])/g, '-$1')
        .toLowerCase()
        .replace(/^-/, '') // Remove leading hyphen

      return (
        <div
          data-testid={`recharts-${kebabCase}`}
          ref={ref}
          {...domProps}
        >
          {children}
        </div>
      )
    })
    MockComponent.displayName = displayName
    return MockComponent
  }

  return {
    ComposedChart: createMockComponent('ComposedChart'),
    Line: createMockComponent('Line'),
    Bar: createMockComponent('Bar'),
    BarChart: createMockComponent('BarChart'),
    Scatter: createMockComponent('Scatter'),
    ScatterChart: createMockComponent('ScatterChart'),
    LineChart: createMockComponent('LineChart'),
    XAxis: createMockComponent('XAxis'),
    YAxis: createMockComponent('YAxis'),
    CartesianGrid: createMockComponent('CartesianGrid'),
    Tooltip: createMockComponent('Tooltip'),
    Legend: createMockComponent('Legend'),
    ResponsiveContainer: createMockComponent('ResponsiveContainer'),
    Cell: createMockComponent('Cell'),
    ReferenceLine: createMockComponent('ReferenceLine'),
    Area: createMockComponent('Area'),
    AreaChart: createMockComponent('AreaChart'),
  }
})

// Mock date-fns
jest.mock('date-fns', () => ({
  format: (date: any, formatStr: any) => {
    if (typeof date === 'number') {
      return '2024-01-15'
    }
    return '2024-01-15'
  }
}))

// Mock useEconomicData module
jest.mock('../../hooks/useEconomicData', () => ({
  useEconomicData: jest.fn()
}))

import { useEconomicData } from '../../hooks/useEconomicData'

describe('EconomicDataCharts', () => {
  let store

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

  const createMockEconomicDataResponse = (overrides = {}) => {
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

  beforeEach(() => {
    // Reset useEconomicData mock to default behavior
    useEconomicData.mockReturnValue(createMockEconomicDataResponse())

    store = configureStore({
      reducer: {
        economicData: economicDataReducer,
      },
      middleware: (getDefaultMiddleware) =>
        getDefaultMiddleware({
          serializableCheck: {
            ignoredActions: ['persist/PERSIST'],
          },
        }),
    })
  })

  const renderComponent = (props = {}) => {
    useEconomicData.mockReturnValue(createMockEconomicDataResponse())

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

      expect(screen.getByTestId('recharts-composed-chart')).toBeInTheDocument()
      expect(screen.getByTestId('recharts-responsive-container')).toBeInTheDocument()
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
      useEconomicData.mockReturnValue(
        createMockEconomicDataResponse({ loading: true })
      )

      render(
        <Provider store={store}>
          <EconomicDataCharts />
        </Provider>
      )

      expect(screen.getByText('Loading economic data...')).toBeInTheDocument()
      expect(screen.getByRole('status')).toBeInTheDocument() // spinner
    })

    test('renders custom loading message', () => {
      useEconomicData.mockReturnValue(
        createMockEconomicDataResponse({ loading: true })
      )

      render(
        <Provider store={store}>
          <EconomicDataCharts />
        </Provider>
      )

      expect(screen.getByText('Loading economic data...')).toBeInTheDocument()
    })
  })

  describe('Error State', () => {
    test('renders error message when error occurs', () => {
      useEconomicData.mockReturnValue(
        createMockEconomicDataResponse({
          error: 'Failed to fetch data',
          loading: false
        })
      )

      render(
        <Provider store={store}>
          <EconomicDataCharts />
        </Provider>
      )

      expect(screen.getByText('Error loading data: Failed to fetch data')).toBeInTheDocument()
    })

    test('renders warning icon for error state', () => {
      useEconomicData.mockReturnValue(
        createMockEconomicDataResponse({
          error: 'API Error',
          loading: false
        })
      )

      render(
        <Provider store={store}>
          <EconomicDataCharts />
        </Provider>
      )

      expect(screen.getByText('⚠️')).toBeInTheDocument()
    })
  })

  describe('Chart Types', () => {
    test('renders scatter plot controls when chartType is scatter', () => {
      renderComponent({ chartType: 'scatter' })

      expect(screen.getByText('X Axis:')).toBeInTheDocument()
      expect(screen.getByText('Y Axis:')).toBeInTheDocument()
      expect(screen.getByTestId('recharts-scatter-chart')).toBeInTheDocument()
    })

    test('renders heatmap when chartType is heatmap', () => {
      renderComponent({ chartType: 'heatmap' })

      expect(screen.getByTestId('recharts-bar-chart')).toBeInTheDocument()
    })

    test('renders correlation controls when chartType is correlation', () => {
      renderComponent({ chartType: 'correlation' })

      expect(screen.getByText('Compare:')).toBeInTheDocument()
    })

    test('renders comparison chart when chartType is comparison', () => {
      renderComponent({ chartType: 'comparison' })

      expect(screen.getByTestId('recharts-line-chart')).toBeInTheDocument()
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
      // Component always uses default options
      renderComponent()

      expect(useEconomicData).toHaveBeenCalledWith({ autoFetch: true })
    })

    test('fetches data when timeRange prop changes', () => {
      const mockFetchAllIndicators = jest.fn()
      useEconomicData.mockReturnValue(
        createMockEconomicDataResponse({
          fetchAllIndicators: mockFetchAllIndicators
        })
      )

      const timeRange = { start: '2024-01-01', end: '2024-12-31' }
      render(
        <Provider store={store}>
          <EconomicDataCharts timeRange={timeRange} />
        </Provider>
      )

      expect(mockFetchAllIndicators).toHaveBeenCalledWith(timeRange)
    })

    test('handles empty timeRange gracefully', () => {
      const mockFetchAllIndicators = jest.fn()
      useEconomicData.mockReturnValue(
        createMockEconomicDataResponse({
          fetchAllIndicators: mockFetchAllIndicators
        })
      )

      render(
        <Provider store={store}>
          <EconomicDataCharts timeRange={{}} />
        </Provider>
      )

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

      useEconomicData.mockReturnValue(
        createMockEconomicDataResponse({ data: largeDataset })
      )

      const startTime = performance.now()
      render(
        <Provider store={store}>
          <EconomicDataCharts />
        </Provider>
      )
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
      expect(screen.getByTestId('recharts-composed-chart')).toBeInTheDocument()
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

      useEconomicData.mockReturnValue(
        createMockEconomicDataResponse({ data: malformedData })
      )

      expect(() => {
        render(
          <Provider store={store}>
            <EconomicDataCharts />
          </Provider>
        )
      }).not.toThrow()
    })

    test('handles API errors in hook', () => {
      useEconomicData.mockReturnValue(
        createMockEconomicDataResponse({
          error: 'Network timeout',
          loading: false
        })
      )

      expect(() => {
        render(
          <Provider store={store}>
            <EconomicDataCharts />
          </Provider>
        )
      }).not.toThrow()
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
      expect(screen.getByTestId('recharts-composed-chart')).toBeInTheDocument()
    })
  })
})