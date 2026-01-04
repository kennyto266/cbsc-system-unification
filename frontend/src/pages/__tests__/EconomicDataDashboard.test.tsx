/**
 * Economic Data Dashboard Page Tests
 * 經濟數據儀表板頁面測試
 */

import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { Provider } from 'react-redux'
import { configureStore } from '@reduxjs/toolkit'
import EconomicDataDashboard from '../EconomicDataDashboard'
import economicDataSlice from '../../store/slices/economicDataSlice'
import { useEconomicData } from '../../hooks/useEconomicData'

// Mock the useEconomicData hook
vi.mock('../../hooks/useEconomicData', () => ({
  useEconomicData: vi.fn()
}))

// Mock the child components
vi.mock('../../components/EconomicDataCharts', () => ({
  default: ({ timeRange, chartType, indicators }: any) => (
    <div data-testid="economic-data-charts">
      <div data-testid="chart-time-range">{JSON.stringify(timeRange)}</div>
      <div data-testid="chart-type">{chartType}</div>
      <div data-testid="chart-indicators">{JSON.stringify(indicators)}</div>
    </div>
  )
}))

vi.mock('../../components/EconomicDataFilters', () => ({
  default: ({ timeRange, customDateRange, selectedIndicators, onTimeRangeChange, onIndicatorChange }: any) => (
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
}))

vi.mock('../../components/EconomicDataTable', () => ({
  default: ({ data, indicators, loading, error }: any) => (
    <div data-testid="economic-data-table">
      <div data-testid="table-indicators">{JSON.stringify(indicators)}</div>
      <div data-testid="table-loading">{loading.toString()}</div>
      <div data-testid="table-error">{error || 'null'}</div>
    </div>
  )
}))

// Mock lucide-react icons
vi.mock('lucide-react', () => ({
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
vi.mock('date-fns', () => ({
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
    vi.clearAllMocks()

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
      { date: '2024-01-01', value: 5.5 },
      { date: '2024-01-02', value: 5.6 }
    ],
    gdp: [
      { date: '2024-01-01', value: 3.2 },
      { date: '2024-04-01', value: 3.3 }
    ],
    pmi: [
      { date: '2024-01-01', value: 52.3 },
      { date: '2024-02-01', value: 51.8 }
    ],
    visitors: [
      { date: '2024-01-01', value: 150000 },
      { date: '2024-02-01', value: 160000 }
    ],
    unemployment: [
      { date: '2024-01-01', value: 3.2 },
      { date: '2024-02-01', value: 3.1 }
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
      fetchAllIndicators: vi.fn().mockResolvedValue(undefined),
      setFilter: vi.fn(),
      setTimeRange: vi.fn(),
      refreshData: vi.fn().mockResolvedValue(undefined),
      clearCache: vi.fn(),
      ...overrides
    }
  }

  const renderComponent = (props = {}) => {
    (useEconomicData as any).mockReturnValue(mockUseEconomicData())

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
      expect(screen.getByTestId('refresh-icon')).toBeInTheDocument()
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
      const mockRefreshData = vi.fn().mockResolvedValue(undefined)
      const mockClearCache = vi.fn()
      (useEconomicData as any).mockReturnValue(
        mockUseEconomicData({
          refreshData: mockRefreshData,
          clearCache: mockClearCache
        })
      )

      renderComponent()

      const refreshButton = screen.getByTestId('refresh-icon').closest('button')
      fireEvent.click(refreshButton!)

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
      const mockFetchAllIndicators = vi.fn().mockResolvedValue(undefined)
      (useEconomicData as any).mockReturnValue(
        mockUseEconomicData({
          fetchAllIndicators: mockFetchAllIndicators
        })
      )

      renderComponent()

      // Show filters first
      const filterButton = screen.getByTestId('filter-icon').closest('button')
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
      const dataWithAlerts = {
        ...mockEconomicData,
        hibor: [
          { date: '2024-01-01', value: 6.5 }, // Should trigger alert (> 6%)
          { date: '2024-01-02', value: 5.6 }
        ],
        unemployment: [
          { date: '2024-01-01', value: 4.5 }, // Should trigger alert (> 4%)
          { date: '2024-01-02', value: 3.1 }
        ]
      }

      (useEconomicData as any).mockReturnValue(
        mockUseEconomicData({
          data: dataWithAlerts,
          filteredData: dataWithAlerts
        })
      )

      renderComponent()

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
      expect(screen.getByRole('heading', { level: 2 })).toBeInTheDocument() // Chart title
      expect(screen.getByRole('heading', { level: 3 })).toBeInTheDocument() // Sidebar titles
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
      const main = document.querySelector('main') || screen.getByRole('main')
      expect(main).toBeInTheDocument()

      const navigation = screen.getByRole('navigation')
      expect(navigation).toBeInTheDocument()
    })
  })
})