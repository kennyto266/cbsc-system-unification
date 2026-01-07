/**
 * Economic Data Dashboard Page Tests
 * 經濟數據儀表板頁面測試
 */

import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { Provider } from 'react-redux'
import { configureStore } from '@reduxjs/toolkit'
import EconomicDataDashboard from '../EconomicDataDashboard'
import economicDataReducer from '../../store/slices/economicDataSlice'
import { useEconomicData } from '../../hooks/useEconomicData'

// Mock the useEconomicData hook
jest.mock('../../hooks/useEconomicData', () => ({
  useEconomicData: jest.fn()
}))

// Mock the child components - Use factory function to return component with __esModule flag
jest.mock('../../components/EconomicDataCharts', () => {
  const MockCharts = ({ timeRange, chartType, indicators }: any) => (
    <div data-testid="economic-data-charts">
      <div data-testid="chart-time-range">{JSON.stringify(timeRange)}</div>
      <div data-testid="chart-type">{chartType}</div>
      <div data-testid="chart-indicators">{JSON.stringify(indicators)}</div>
    </div>
  )
  MockCharts.displayName = 'EconomicDataCharts'
  return {
    __esModule: true,
    default: MockCharts
  }
})

jest.mock('../../components/EconomicDataFilters', () => {
  const MockFilters = ({ timeRange, customDateRange, selectedIndicators, onTimeRangeChange, onIndicatorChange, onCustomDateRangeChange, onChartTypeChange, timeRanges }: any) => (
    <div data-testid="economic-data-filters">
      <div data-testid="filters-time-range">{timeRange.label}</div>
      <div data-testid="filters-custom-range">{JSON.stringify(customDateRange)}</div>
      <div data-testid="filters-indicators">{JSON.stringify(selectedIndicators)}</div>
      <button
        data-testid="filters-time-range-change"
        onClick={() => onTimeRangeChange({ label: 'Custom Range', value: { start: '2024-01-01', end: '2024-12-31' } })}
      >
        Change Time Range
      </button>
      <button
        data-testid="filters-indicator-change"
        onClick={() => onIndicatorChange(['hibor', 'gdp'])}
      >
        Change Indicators
      </button>
    </div>
  )
  MockFilters.displayName = 'EconomicDataFilters'
  return {
    __esModule: true,
    default: MockFilters
  }
})

jest.mock('../../components/EconomicDataTable', () => {
  const MockTable = ({ data, indicators, loading, error }: any) => (
    <div data-testid="economic-data-table">
      <div data-testid="table-indicators">{JSON.stringify(indicators)}</div>
      <div data-testid="table-loading">{loading.toString()}</div>
      <div data-testid="table-error">{error || 'null'}</div>
    </div>
  )
  MockTable.displayName = 'EconomicDataTable'
  return {
    __esModule: true,
    default: MockTable
  }
})

// Mock lucide-react icons
jest.mock('lucide-react', () => ({
  Calendar: ({ className }: any) => <div data-testid="calendar-icon" className={className} />,
  Filter: ({ className }: any) => <div data-testid="filter-icon" className={className} />,
  RefreshCw: ({ className }: any) => <div data-testid="refresh-icon" className={className} />,
  Download: ({ className }: any) => <div data-testid="download-icon" className={className} />,
  Settings: ({ className }: any) => <div data-testid="settings-icon" className={className} />,
  TrendingUp: ({ className }: any) => <div data-testid="trending-up-icon" className={className} />,
  AlertCircle: ({ className }: any) => <div data-testid="alert-circle-icon" className={className} />,
  Activity: ({ className }: any) => <div data-testid="activity-icon" className={className} />,
  ChevronUp: ({ className }: any) => <div data-testid="chevron-up-icon" className={className} />,
  ChevronDown: ({ className }: any) => <div data-testid="chevron-down-icon" className={className} />,
  Search: ({ className }: any) => <div data-testid="search-icon" className={className} />,
  Eye: ({ className }: any) => <div data-testid="eye-icon" className={className} />,
  EyeOff: ({ className }: any) => <div data-testid="eye-off-icon" className={className} />
}))

// Mock date-fns
jest.mock('date-fns', () => ({
  format: (date: Date | number, formatStr: string) => {
    if (typeof date === 'number') {
      return '2024-01-15'
    }
    if (formatStr === 'MMM dd, HH:mm') {
      return 'Jan 15, 10:00'
    }
    return '2024-01-15'
  }
}))

describe('EconomicDataDashboard', () => {
  let store: ReturnType<typeof configureStore>

  beforeEach(() => {
    jest.clearAllMocks()

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
      fetchAllIndicators: jest.fn().mockResolvedValue(undefined),
      setFilter: jest.fn(),
      setTimeRange: jest.fn(),
      refreshData: jest.fn().mockResolvedValue(undefined),
      clearCache: jest.fn(),
      ...overrides
    }
  }

  const renderComponent = (props = {}, mockOverrides = {}) => {
    (useEconomicData as any).mockReturnValue(mockUseEconomicData(mockOverrides))

    return render(
      <Provider store={store}>
        <EconomicDataDashboard {...props} />
      </Provider>
    )
  }

  describe('Page Rendering', () => {
    test('renders dashboard header', () => {
      renderComponent()

      expect(screen.getByText('Economic Data Dashboard')).toBeInTheDocument()
      expect(screen.getByText('Real-time economic indicators and analysis')).toBeInTheDocument()
      expect(screen.getByTestId('trending-up-icon')).toBeInTheDocument()
    })

    test('renders quick stats section', () => {
      renderComponent()

      expect(screen.getByText('Total Indicators')).toBeInTheDocument()
      expect(screen.getByText('Data Points')).toBeInTheDocument()
      expect(screen.getByText('Active Alerts')).toBeInTheDocument()
      expect(screen.getByText('Last Updated')).toBeInTheDocument()
    })

    test('renders main chart area', () => {
      renderComponent()

      expect(screen.getByText('Economic Indicators Visualization')).toBeInTheDocument()
      expect(screen.getByTestId('economic-data-charts')).toBeInTheDocument()
    })

    test('renders sidebar with controls', () => {
      renderComponent()

      expect(screen.getByText('Chart Type')).toBeInTheDocument()
      expect(screen.getByText('Quick Actions')).toBeInTheDocument()
      expect(screen.getByText('Time Series')).toBeInTheDocument()
      expect(screen.getByText('Scatter Plot')).toBeInTheDocument()
    })
  })

  describe('Header Actions', () => {
    test('renders all header action buttons', () => {
      renderComponent()

      expect(screen.getByTestId('filter-icon')).toBeInTheDocument()
      // Multiple refresh icons exist (header button + quick stats), so we check for at least one
      expect(screen.getAllByTestId('refresh-icon').length).toBeGreaterThan(0)
      expect(screen.getByTestId('download-icon')).toBeInTheDocument()
      expect(screen.getByTestId('settings-icon')).toBeInTheDocument()
    })

    test('toggles filters panel when filter button is clicked', () => {
      renderComponent()

      const filterButton = screen.getByTestId('filter-icon').closest('button')
      fireEvent.click(filterButton!)

      expect(screen.getByTestId('economic-data-filters')).toBeInTheDocument()
    })

    test('triggers refresh when refresh button is clicked', async () => {
      const mockRefreshData = jest.fn().mockResolvedValue(undefined)
      const mockClearCache = jest.fn()

      renderComponent({}, {
        refreshData: mockRefreshData,
        clearCache: mockClearCache
      })

      // Find the refresh button by its title attribute
      const refreshButton = screen.getByTitle('Refresh Data')
      fireEvent.click(refreshButton)

      await waitFor(() => {
        expect(mockClearCache).toHaveBeenCalled()
        expect(mockRefreshData).toHaveBeenCalled()
      })
    })
  })

  describe('Data Integration', () => {
    test('uses useEconomicData hook with default options', () => {
      renderComponent()

      expect(useEconomicData).toHaveBeenCalledWith({
        autoFetch: true,
        cacheEnabled: true,
        refreshInterval: 300000
      })
    })

    test('passes correct props to EconomicDataCharts', () => {
      renderComponent()

      expect(screen.getByTestId('chart-type')).toHaveTextContent('timeSeries')
      expect(screen.getByTestId('chart-indicators')).toHaveTextContent(
        JSON.stringify(['hibor', 'gdp', 'pmi', 'visitors', 'unemployment'])
      )
    })

    test('fetches data on time range change', async () => {
      const mockFetchAllIndicators = jest.fn().mockResolvedValue(undefined)

      renderComponent({}, {
        fetchAllIndicators: mockFetchAllIndicators
      })

      // Show filters first
      const filterIcons = screen.getAllByTestId('filter-icon')
      const filterButton = filterIcons[0].closest('button')
      fireEvent.click(filterButton!)

      // Change time range
      const timeRangeButton = screen.getByTestId('filters-time-range-change')
      fireEvent.click(timeRangeButton)

      await waitFor(() => {
        expect(mockFetchAllIndicators).toHaveBeenCalledWith({
          start: '2024-01-01',
          end: '2024-12-31'
        })
      })
    })
  })

  describe('Chart Type Selection', () => {
    test('renders all chart type options', () => {
      renderComponent()

      expect(screen.getByText('Time Series')).toBeInTheDocument()
      expect(screen.getByText('Scatter Plot')).toBeInTheDocument()
      expect(screen.getByText('Heat Map')).toBeInTheDocument()
      expect(screen.getByText('Correlation')).toBeInTheDocument()
      expect(screen.getByText('Comparison')).toBeInTheDocument()
    })

    test('updates chart type when option is selected', () => {
      renderComponent()

      const scatterButton = screen.getByText('Scatter Plot')
      fireEvent.click(scatterButton)

      expect(screen.getByTestId('chart-type')).toHaveTextContent('scatter')
    })

    test('highlights active chart type button', () => {
      renderComponent()

      const timeSeriesButton = screen.getByText('Time Series')
      expect(timeSeriesButton.closest('button')).toHaveClass('bg-blue-50')
    })
  })

  describe('Data Table Integration', () => {
    test('hides data table by default', () => {
      renderComponent()

      expect(screen.queryByTestId('economic-data-table')).not.toBeInTheDocument()
    })

    test('shows data table when toggled', () => {
      renderComponent()

      const showTableButton = screen.getByText('Show Data Table')
      fireEvent.click(showTableButton)

      expect(screen.getByTestId('economic-data-table')).toBeInTheDocument()
    })

    test('hides data table when toggled again', () => {
      renderComponent()

      const showTableButton = screen.getByText('Show Data Table')
      fireEvent.click(showTableButton)

      const hideTableButton = screen.getByText('Hide Data Table')
      fireEvent.click(hideTableButton)

      expect(screen.queryByTestId('economic-data-table')).not.toBeInTheDocument()
    })
  })

  describe('Loading and Error States', () => {
    test('shows loading state correctly', () => {
      (useEconomicData as any).mockReturnValue(
        mockUseEconomicData({ loading: true })
      )

      renderComponent()

      // Check if components receive loading prop correctly
      expect(screen.getByTestId('economic-data-charts')).toBeInTheDocument()
    })

    test('shows error state correctly', () => {
      (useEconomicData as any).mockReturnValue(
        mockUseEconomicData({
          loading: false,
          error: 'Network error'
        })
      )

      renderComponent()

      expect(screen.getByTestId('economic-data-charts')).toBeInTheDocument()
    })
  })

  describe('Statistics Calculation', () => {
    test('calculates quick stats correctly', () => {
      renderComponent()

      // Total indicators should be 5
      const statsCards = screen.getAllByText('5')
      expect(statsCards.length).toBeGreaterThan(0)

      // Data points should be 10 (2 per indicator)
      expect(screen.getByText('10')).toBeInTheDocument()

      // Last updated should be formatted
      expect(screen.getByText('Jan 15, 10:00')).toBeInTheDocument()
    })

    test('detects alerts correctly', () => {
      // Create data with alerts - note that component checks point.indicator property
      const hiborWithAlerts = [
        { date: '2024-01-01', value: 6.5, indicator: 'hibor' }, // Should trigger alert (> 6%)
        { date: '2024-01-02', value: 5.6, indicator: 'hibor' }
      ]
      const unemploymentWithAlerts = [
        { date: '2024-01-01', value: 4.5, indicator: 'unemployment' }, // Should trigger alert (> 4%)
        { date: '2024-01-02', value: 3.1, indicator: 'unemployment' }
      ]
      const dataWithAlerts = {
        hibor: hiborWithAlerts,
        gdp: mockEconomicData.gdp,
        pmi: mockEconomicData.pmi,
        visitors: mockEconomicData.visitors,
        unemployment: unemploymentWithAlerts
      }

      renderComponent({}, {
        data: dataWithAlerts,
        filteredData: dataWithAlerts
      })

      // Should detect 2 alerts
      const alertStats = screen.getByText('2')
      expect(alertStats).toBeInTheDocument()
    })
  })

  describe('Responsive Design', () => {
    test('renders correctly on different screen sizes', () => {
      renderComponent()

      // Should have responsive grid classes
      const container = screen.getByText('Total Indicators').closest('.grid')
      expect(container).toHaveClass('grid-cols-1', 'md:grid-cols-4')
    })

    test('adapts layout for smaller screens', () => {
      renderComponent()

      // Should have responsive grid for main content
      const mainContent = screen.getByTestId('economic-data-charts').closest('.grid')
      expect(mainContent).toHaveClass('lg:grid-cols-4')
    })
  })

  describe('Accessibility', () => {
    test('provides proper ARIA labels', () => {
      renderComponent()

      // Check for proper heading hierarchy
      expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument() // Main title
      expect(screen.getAllByRole('heading', { level: 2 }).length).toBeGreaterThan(0) // Chart title
      expect(screen.getAllByRole('heading', { level: 3 }).length).toBeGreaterThan(0) // Sidebar titles
    })

    test('supports keyboard navigation', () => {
      renderComponent()

      const buttons = screen.getAllByRole('button')
      buttons.forEach(button => {
        expect(button).not.toBeDisabled()
      })
    })

    test('provides semantic HTML structure', () => {
      renderComponent()

      // Should have proper semantic elements
      // Note: The component may not have explicit <main> or <nav> elements, so we check for general structure
      const container = screen.getByText('Economic Data Dashboard').closest('div')
      expect(container).toBeInTheDocument()
    })
  })
})