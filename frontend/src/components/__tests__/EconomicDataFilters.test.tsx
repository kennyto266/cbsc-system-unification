/**
 * Economic Data Filters Component Tests
 * 經濟數據過濾器組件測試
 */

import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import EconomicDataFilters from '../EconomicDataFilters'

// Mock lucide-react icons
jest.mock('lucide-react', () => ({
  Filter: ({ className }: any) => <div data-testid="filter-icon" className={className} />,
  X: ({ className }: any) => <div data-testid="x-icon" className={className} />,
  ChevronDown: ({ className }: any) => <div data-testid="chevron-down-icon" className={className} />
}))

// Mock date-fns
jest.mock('date-fns', () => ({
  format: (date: Date | number, formatStr: string) => {
    return '2024-01-15'
  }
}))

describe('EconomicDataFilters', () => {
  const defaultProps = {
    timeRange: { label: 'Last 30 Days', value: { start: '2024-01-01', end: '2024-01-30' } },
    customDateRange: { start: '', end: '' },
    selectedIndicators: ['hibor', 'gdp', 'pmi'],
    onTimeRangeChange: jest.fn(),
    onCustomDateRangeChange: jest.fn(),
    onIndicatorChange: jest.fn(),
    onChartTypeChange: jest.fn(),
    timeRanges: [
      { label: 'Last 7 Days', value: { start: '2024-01-24', end: '2024-01-31' }, shortcut: '7d' },
      { label: 'Last 30 Days', value: { start: '2024-01-01', end: '2024-01-30' }, shortcut: '30d' },
      { label: 'Custom Range', value: { start: '', end: '' } }
    ]
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  const renderComponent = (props = {}) => {
    return render(
      <EconomicDataFilters {...defaultProps} {...props} />
    )
  }

  describe('Rendering', () => {
    test('renders filter sections', () => {
      renderComponent()

      expect(screen.getByText('Dashboard Filters')).toBeInTheDocument()
      expect(screen.getByText('Time Range')).toBeInTheDocument()
      expect(screen.getByText('Economic Indicators')).toBeInTheDocument()
      expect(screen.getByText('Visualization Type')).toBeInTheDocument()
    })

    test('renders time range options', () => {
      renderComponent()

      expect(screen.getByText('Last 7 Days')).toBeInTheDocument()
      expect(screen.getByText('Last 30 Days')).toBeInTheDocument()
      expect(screen.getByText('Custom Range')).toBeInTheDocument()
      expect(screen.getByText('7d')).toBeInTheDocument()
      expect(screen.getByText('30d')).toBeInTheDocument()
    })

    test('renders indicator options', () => {
      renderComponent()

      expect(screen.getByText('HIBOR Rate')).toBeInTheDocument()
      expect(screen.getByText('GDP Growth')).toBeInTheDocument()
      expect(screen.getByText('PMI')).toBeInTheDocument()
      expect(screen.getByText('Visitor Arrivals')).toBeInTheDocument()
      expect(screen.getByText('Unemployment Rate')).toBeInTheDocument()
    })

    test('renders chart type options', () => {
      renderComponent()

      expect(screen.getByText('Time Series')).toBeInTheDocument()
      expect(screen.getByText('Scatter Plot')).toBeInTheDocument()
      expect(screen.getByText('Heat Map')).toBeInTheDocument()
      expect(screen.getByText('Correlation')).toBeInTheDocument()
      expect(screen.getByText('Comparison')).toBeInTheDocument()
    })
  })

  describe('Time Range Selection', () => {
    test('highlights selected time range', () => {
      renderComponent()

      const selectedButton = screen.getByText('Last 30 Days').closest('button')
      expect(selectedButton).toHaveClass('bg-blue-50', 'border-blue-200')
    })

    test('calls onTimeRangeChange when time range is clicked', () => {
      renderComponent()

      const timeRangeButton = screen.getByText('Last 7 Days')
      fireEvent.click(timeRangeButton)

      expect(defaultProps.onTimeRangeChange).toHaveBeenCalledWith({
        label: 'Last 7 Days',
        value: { start: '2024-01-24', end: '2024-01-31' }
      })
    })

    test('shows custom date picker when Custom Range is selected', () => {
      renderComponent()

      const customRangeButton = screen.getByText('Custom Range')
      fireEvent.click(customRangeButton)

      expect(screen.getByText('Start Date')).toBeInTheDocument()
      expect(screen.getByText('End Date')).toBeInTheDocument()
      expect(screen.getByText('Apply')).toBeInTheDocument()
      expect(screen.getByText('Clear')).toBeInTheDocument()
    })

    test('handles custom date range application', () => {
      renderComponent()

      // Show custom date picker
      const customRangeButton = screen.getByText('Custom Range')
      fireEvent.click(customRangeButton)

      // Fill in dates
      const startDateInput = screen.getByLabelText('Start Date')
      const endDateInput = screen.getByLabelText('End Date')

      fireEvent.change(startDateInput, { target: { value: '2024-01-01' } })
      fireEvent.change(endDateInput, { target: { value: '2024-12-31' } })

      // Apply date range
      const applyButton = screen.getByText('Apply')
      fireEvent.click(applyButton)

      expect(defaultProps.onCustomDateRangeChange).toHaveBeenCalledWith({
        start: '2024-01-01',
        end: '2024-12-31'
      })
    })

    test('clears custom date range', () => {
      renderComponent({
        ...defaultProps,
        customDateRange: { start: '2024-01-01', end: '2024-12-31' }
      })

      // Show custom date picker
      const customRangeButton = screen.getByText('Custom Range')
      fireEvent.click(customRangeButton)

      // Clear date range
      const clearButton = screen.getByText('Clear')
      fireEvent.click(clearButton)

      expect(defaultProps.onCustomDateRangeChange).toHaveBeenCalledWith({
        start: '',
        end: ''
      })
    })
  })

  describe('Indicator Selection', () => {
    test('shows selected indicators correctly', () => {
      renderComponent()

      const hiborIndicator = screen.getByText('HIBOR Rate')
      expect(hiborIndicator.closest('button')).toHaveClass('bg-blue-50', 'border-blue-200')

      const gdpIndicator = screen.getByText('GDP Growth')
      expect(gdpIndicator.closest('button')).toHaveClass('bg-blue-50', 'border-blue-200')

      const visitorsIndicator = screen.getByText('Visitor Arrivals')
      expect(visitorsIndicator.closest('button')).toHaveClass('bg-white', 'border-gray-200')
    })

    test('toggles indicator selection', () => {
      renderComponent()

      const visitorsIndicator = screen.getByText('Visitor Arrivals')
      fireEvent.click(visitorsIndicator)

      expect(defaultProps.onIndicatorChange).toHaveBeenCalledWith([
        'hibor', 'gdp', 'pmi', 'visitors'
      ])
    })

    test('removes indicator from selection', () => {
      renderComponent()

      const hiborIndicator = screen.getByText('HIBOR Rate')
      fireEvent.click(hiborIndicator)

      expect(defaultProps.onIndicatorChange).toHaveBeenCalledWith(['gdp', 'pmi'])
    })

    test('shows indicator descriptions', () => {
      renderComponent()

      expect(screen.getByText('Hong Kong Interbank Offered Rate')).toBeInTheDocument()
      expect(screen.getByText('Gross Domestic Product Growth Rate')).toBeInTheDocument()
      expect(screen.getByText('Purchasing Managers Index')).toBeInTheDocument()
      expect(screen.getByText('Tourist visitor statistics')).toBeInTheDocument()
      expect(screen.getByText('Labor market unemployment rate')).toBeInTheDocument()
    })

    test('shows indicator colors', () => {
      renderComponent()

      // Check for color indicators
      const colorDots = document.querySelectorAll('[class*="bg-blue-500"], [class*="bg-green-500"], [class*="bg-yellow-500"], [class*="bg-purple-500"], [class*="bg-red-500"]')
      expect(colorDots.length).toBeGreaterThan(0)
    })
  })

  describe('Chart Type Selection', () => {
    test('calls onChartTypeChange when chart type is selected', () => {
      renderComponent()

      const scatterButton = screen.getByText('Scatter Plot')
      fireEvent.click(scatterButton)

      expect(defaultProps.onChartTypeChange).toHaveBeenCalledWith('scatter')
    })

    test('renders chart type icons', () => {
      renderComponent()

      // Should have emoji icons for chart types
      expect(screen.getByText('📈')).toBeInTheDocument() // Time Series
      expect(screen.getByText('📊')).toBeInTheDocument() // Scatter Plot
      expect(screen.getByText('🔥')).toBeInTheDocument() // Heat Map
      expect(screen.getByText('🔗')).toBeInTheDocument() // Correlation
      expect(screen.getByText('⚖️')).toBeInTheDocument() // Comparison
    })
  })

  describe('Reset Functionality', () => {
    test('calls reset handlers when Reset All is clicked', () => {
      renderComponent()

      const resetButton = screen.getByText('Reset All')
      fireEvent.click(resetButton)

      expect(defaultProps.onIndicatorChange).toHaveBeenCalledWith([
        'hibor', 'gdp', 'pmi', 'visitors', 'unemployment'
      ])
      expect(defaultProps.onTimeRangeChange).toHaveBeenCalledWith(defaultProps.timeRanges[1])
    })
  })

  describe('Summary Section', () => {
    test('shows selection summary', () => {
      renderComponent()

      expect(screen.getByText('3 indicators selected • Last 30 Days')).toBeInTheDocument()
    })

    test('shows warning when no indicators selected', () => {
      renderComponent({
        ...defaultProps,
        selectedIndicators: []
      })

      expect(screen.getByText('Please select at least one indicator')).toBeInTheDocument()
    })
  })

  describe('Date Input Validation', () => {
    test('disables apply button when dates are incomplete', () => {
      renderComponent()

      // Show custom date picker
      const customRangeButton = screen.getByText('Custom Range')
      fireEvent.click(customRangeButton)

      // Fill only start date
      const startDateInput = screen.getByLabelText('Start Date')
      fireEvent.change(startDateInput, { target: { value: '2024-01-01' } })

      const applyButton = screen.getByText('Apply')
      expect(applyButton).toBeDisabled()
    })

    test('enables apply button when dates are complete', () => {
      renderComponent()

      // Show custom date picker
      const customRangeButton = screen.getByText('Custom Range')
      fireEvent.click(customRangeButton)

      // Fill both dates
      const startDateInput = screen.getByLabelText('Start Date')
      const endDateInput = screen.getByLabelText('End Date')

      fireEvent.change(startDateInput, { target: { value: '2024-01-01' } })
      fireEvent.change(endDateInput, { target: { value: '2024-12-31' } })

      const applyButton = screen.getByText('Apply')
      expect(applyButton).not.toBeDisabled()
    })

    test('sets minimum date for end date based on start date', () => {
      renderComponent()

      // Show custom date picker
      const customRangeButton = screen.getByText('Custom Range')
      fireEvent.click(customRangeButton)

      // Fill start date
      const startDateInput = screen.getByLabelText('Start Date')
      fireEvent.change(startDateInput, { target: { value: '2024-01-01' } })

      const endDateInput = screen.getByLabelText('End Date')
      expect(endDateInput).toHaveAttribute('min', '2024-01-01')
    })
  })

  describe('Accessibility', () => {
    test('provides proper ARIA labels', () => {
      renderComponent()

      // Check for proper form labels
      expect(screen.getByLabelText('Start Date')).toBeInTheDocument()
      expect(screen.getByLabelText('End Date')).toBeInTheDocument()

      // Check for button text content
      const buttons = screen.getAllByRole('button')
      buttons.forEach(button => {
        const textContent = button.textContent
        expect(textContent && textContent.trim().length > 0).toBeTruthy()
      })
    })

    test('supports keyboard navigation', () => {
      renderComponent()

      const buttons = screen.getAllByRole('button')
      buttons.forEach(button => {
        expect(button).not.toBeDisabled()
      })

      const inputs = screen.getAllByRole('textbox')
      inputs.forEach(input => {
        expect(input).not.toBeDisabled()
      })
    })

    test('provides semantic HTML structure', () => {
      renderComponent()

      // Should have proper heading hierarchy
      expect(screen.getByRole('heading', { level: 3 })).toBeInTheDocument()

      // Should have form elements
      const formElements = screen.getAllByRole('button', 'textbox')
      expect(formElements.length).toBeGreaterThan(0)
    })
  })

  describe('Visual Design', () => {
    test('applies correct hover states', () => {
      renderComponent()

      const buttons = screen.getAllByRole('button')
      buttons.forEach(button => {
        const classes = button.className
        expect(classes).toContain('transition-colors')
      })
    })

    test('shows custom date picker with proper styling', () => {
      renderComponent()

      const customRangeButton = screen.getByText('Custom Range')
      fireEvent.click(customRangeButton)

      const datePicker = screen.getByText('Start Date').closest('.bg-gray-50')
      expect(datePicker).toHaveClass('bg-gray-50', 'rounded-lg', 'border')
    })
  })
})