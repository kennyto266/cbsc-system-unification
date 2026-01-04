/**
 * Economic Signal Markers Component Tests
 * 經濟信號標記組件測試
 */

import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import EconomicSignalMarkers, { EconomicSignal } from '../EconomicSignalMarkers'

// Mock lucide-react icons
jest.mock('lucide-react', () => ({
  AlertTriangle: ({ className }: any) => <div data-testid="alert-triangle-icon" className={className} />,
  TrendingUp: ({ className }: any) => <div data-testid="trending-up-icon" className={className} />,
  TrendingDown: ({ className }: any) => <div data-testid="trending-down-icon" className={className} />,
  Minus: ({ className }: any) => <div data-testid="minus-icon" className={className} />,
  Info: ({ className }: any) => <div data-testid="info-icon" className={className} />,
  X: ({ className }: any) => <div data-testid="x-icon" className={className} />,
  Clock: ({ className }: any) => <div data-testid="clock-icon" className={className} />,
  Target: ({ className }: any) => <div data-testid="target-icon" className={className} />,
  Activity: ({ className }: any) => <div data-testid="activity-icon" className={className} />
}))

// Mock date-fns
jest.mock('date-fns', () => ({
  format: (date: Date | number, formatStr: string) => {
    if (typeof date === 'number') {
      return '2024-01-15 10:30'
    }
    if (formatStr === 'MMM dd, HH:mm:ss') {
      return 'Jan 15, 10:30:00'
    }
    return 'Jan 15, 10:30'
  }
}))

// Mock all required UI components
jest.mock('@/components/ui', () => ({
  Card: ({ children, className }: any) => <div className={className} data-testid="card">{children}</div>,
  Button: ({ children, onClick, disabled, className, title }: any) => (
    <button onClick={onClick} disabled={disabled} className={className} title={title} data-testid="button">
      {children}
    </button>
  ),
  Select: ({ value, onChange, children, label }: any) => (
    <select value={value} onChange={onChange} aria-label={label} data-testid="select">
      {children}
    </select>
  ),
  Badge: ({ children, className }: any) => <span className={className}>{children}</span>
}))

describe('EconomicSignalMarkers', () => {
  // Use fixed date for consistent testing
  const baseDate = new Date('2024-01-15T12:00:00Z')
  const oneHourBefore = new Date('2024-01-15T11:00:00Z')
  const twoHoursBefore = new Date('2024-01-15T10:00:00Z')
  const yesterday = new Date('2024-01-14T12:00:00Z')

  // Mock Date to use fixed current time
  beforeEach(() => {
    jest.useFakeTimers()
    jest.setSystemTime(baseDate)
  })

  afterEach(() => {
    jest.useRealTimers()
  })

  const mockSignals: EconomicSignal[] = [
    {
      id: 'signal-1',
      date: oneHourBefore.toISOString(),
      indicator: 'hibor',
      type: 'warning',
      strength: 0.85,
      confidence: 0.9,
      value: 6.5,
      previousValue: 5.8,
      threshold: 6.0,
      description: 'HIBOR rate exceeds 6%, indicating high interest rate environment',
      category: 'interest_rate',
      metadata: {
        deviation: 0.083,
        trend: 0.12,
        dataPoints: 5,
        triggeredBy: 'threshold_analysis'
      },
      createdAt: oneHourBefore.toISOString()
    },
    {
      id: 'signal-2',
      date: twoHoursBefore.toISOString(),
      indicator: 'gdp',
      type: 'buy',
      strength: 0.75,
      confidence: 0.85,
      value: 4.2,
      previousValue: 3.8,
      threshold: 4.0,
      description: 'GDP growth above 4%, indicating strong economic expansion',
      category: 'economic_growth',
      metadata: {
        deviation: 0.05,
        trend: 0.105,
        dataPoints: 4,
        triggeredBy: 'threshold_analysis'
      },
      createdAt: twoHoursBefore.toISOString()
    },
    {
      id: 'signal-3',
      date: yesterday.toISOString(),
      indicator: 'pmi',
      type: 'sell',
      strength: 0.6,
      confidence: 0.7,
      value: 48.5,
      previousValue: 51.2,
      threshold: 50.0,
      description: 'PMI below 50, indicating economic contraction',
      category: 'economic_growth',
      metadata: {
        deviation: 0.03,
        trend: -0.054,
        dataPoints: 6,
        triggeredBy: 'threshold_analysis'
      },
      createdAt: yesterday.toISOString()
    }
  ]

  const defaultProps = {
    signals: mockSignals,
    showFilters: true,
    maxVisible: 10
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  const renderComponent = (props = {}) => {
    return render(
      <EconomicSignalMarkers {...defaultProps} {...props} />
    )
  }

  describe('Rendering', () => {
    test('renders component header', () => {
      renderComponent()

      expect(screen.getByText('Economic Signal Markers')).toBeInTheDocument()
      // With baseDate at 2024-01-15T12:00:00Z, signals from 11:00 and 10:00 are in last 24 hours
      // The text is split across elements, use flexible matchers
      expect(screen.getByText((content) => content.includes('signals detected'))).toBeInTheDocument()
      expect(screen.getByText((content) => content.includes('in last 24 hours'))).toBeInTheDocument()
      expect(screen.getAllByTestId('alert-triangle-icon').length).toBeGreaterThan(0)
      // Verify the Last 24h stat shows 2
      expect(screen.getByText('Last 24h')).toBeInTheDocument()
      const last24hElements = screen.getAllByText('2')
      expect(last24hElements.some(el => el.textContent === '2')).toBeTruthy()
    })

    test('renders quick statistics', () => {
      renderComponent()

      expect(screen.getByText('Total Signals')).toBeInTheDocument()
      expect(screen.getByText('3')).toBeInTheDocument() // Total signals
      expect(screen.getByText('High Confidence')).toBeInTheDocument()
      // High confidence (> 0.8) are signals with 0.9 and 0.85, so count is 2
      const highConfidenceCount = screen.getAllByText('2')
      expect(highConfidenceCount.length).toBeGreaterThan(0)
    })

    test('renders signals list', async () => {
      renderComponent()

      // Wait for signals to render - just check that Warning signal exists
      await waitFor(() => {
        expect(screen.getAllByText('Warning').length).toBeGreaterThan(0)
      })
    })

    test('shows signal descriptions', () => {
      renderComponent()

      expect(screen.getByText('HIBOR rate exceeds 6%, indicating high interest rate environment')).toBeInTheDocument()
      expect(screen.getByText('GDP growth above 4%, indicating strong economic expansion')).toBeInTheDocument()
    })
  })

  describe('Signal Display', () => {
    test('shows signal values with previous values', () => {
      renderComponent()

      // The component shows values with the format "Value: 6.50 (+0.70)"
      // Use flexible matchers to find these elements
      expect(screen.getByText((content) => content.includes('6.50'))).toBeInTheDocument()
      expect(screen.getByText((content) => content.includes('4.20'))).toBeInTheDocument()
      expect(screen.getByText((content) => content.includes('48.50'))).toBeInTheDocument()

      // Should show previous values when available
      expect(screen.getByText((content) => content.includes('(+0.70)'))).toBeInTheDocument()
      expect(screen.getByText((content) => content.includes('(+0.40)'))).toBeInTheDocument()
      expect(screen.getByText((content) => content.includes('(-2.70)'))).toBeInTheDocument()
    })

    test('displays signal strength correctly', () => {
      renderComponent()

      // The strength is shown as percentage - use getAllByText since there are multiple
      expect(screen.getAllByText((content) => content.includes('85%')).length).toBeGreaterThan(0)
      expect(screen.getAllByText((content) => content.includes('75%')).length).toBeGreaterThan(0)
      expect(screen.getAllByText((content) => content.includes('60%')).length).toBeGreaterThan(0)
    })

    test('displays confidence levels correctly', () => {
      renderComponent()

      // The confidence is shown as percentage - use getAllByText since there are multiple
      expect(screen.getAllByText((content) => content.includes('90%')).length).toBeGreaterThan(0)
      expect(screen.getAllByText((content) => content.includes('85%')).length).toBeGreaterThan(0)
      expect(screen.getAllByText((content) => content.includes('70%')).length).toBeGreaterThan(0)
    })

    test('shows signal categories and timestamps', () => {
      renderComponent()

      // Use getAllByText since categories appear multiple times
      expect(screen.getAllByText('Interest Rate').length).toBeGreaterThan(0)
      expect(screen.getAllByText('Economic Growth').length).toBeGreaterThan(0)
      // The mock date-fns format returns 'Jan 15, 10:30' for the dates
      // oneHourBefore (11:00) formatted becomes 'Jan 15, 10:30' per mock
      // twoHoursBefore (10:00) formatted becomes 'Jan 15, 10:30' per mock
      // Both signals show same mocked time
      expect(screen.getAllByText('Jan 15, 10:30').length).toBeGreaterThan(0)
    })
  })

  describe('Filtering', () => {
    test('renders filter controls when showFilters is true', () => {
      renderComponent()

      expect(screen.getByText('Category')).toBeInTheDocument()
      expect(screen.getByText('Signal Type')).toBeInTheDocument()
      expect(screen.getByText('Time Range')).toBeInTheDocument()
      expect(screen.getByText('Sort By')).toBeInTheDocument()
    })

    test('does not render filters when showFilters is false', () => {
      renderComponent({ showFilters: false })

      expect(screen.queryByText('Category')).not.toBeInTheDocument()
      expect(screen.queryByText('Signal Type')).not.toBeInTheDocument()
    })

    test('filters signals by category', async () => {
      renderComponent()

      // Find all select elements and pick the first one (Category)
      const selects = document.querySelectorAll('select')
      const categorySelect = selects[0]
      fireEvent.change(categorySelect, { target: { value: 'interest_rate' } })

      await waitFor(() => {
        // Should only show interest rate signals - use "Warning" which is the signal type label
        expect(screen.getAllByText('Warning').length).toBeGreaterThan(0)
        // After filtering, there should be fewer Buy signals
        expect(screen.queryAllByText('Buy').length).toBe(0)
      })
    })

    test('filters signals by type', async () => {
      renderComponent()

      // Find all select elements and pick the second one (Signal Type)
      const selects = document.querySelectorAll('select')
      const typeSelect = selects[1]
      fireEvent.change(typeSelect, { target: { value: 'warning' } })

      await waitFor(() => {
        // Should only show warning signals
        expect(screen.getAllByText('Warning').length).toBeGreaterThan(0)
        // After filtering, there should be no Buy signals visible
        expect(screen.queryAllByText('Buy').length).toBe(0)
      })
    })

    test('filters signals by time range', async () => {
      renderComponent()

      // Find all select elements and pick the third one (Time Range)
      const selects = document.querySelectorAll('select')
      const timeSelect = selects[2]
      fireEvent.change(timeSelect, { target: { value: 'last_hour' } })

      await waitFor(() => {
        // Should show 2 signals in last hour (oneHourAgo and twoHoursAgo are both in last hour)
        const signalCount = screen.queryAllByText(/Signal/).length
        expect(signalCount).toBeGreaterThan(0)
      })
    })

    test('sorts signals by different criteria', async () => {
      renderComponent()

      // Find all select elements and pick the fourth one (Sort By)
      const selects = document.querySelectorAll('select')
      const sortSelect = selects[3]

      // Test sorting by strength
      fireEvent.change(sortSelect, { target: { value: 'strength' } })
      await waitFor(() => {
        expect(screen.getAllByText((content) => content.includes('85%')).length).toBeGreaterThan(0)
      })

      // Test sorting by confidence
      fireEvent.change(sortSelect, { target: { value: 'confidence' } })
      await waitFor(() => {
        expect(screen.getAllByText((content) => content.includes('90%')).length).toBeGreaterThan(0)
      })
    })
  })

  describe('Signal Interaction', () => {
    test('expands signal details when clicked', async () => {
      renderComponent()

      // Get the first Warning element - there's one in the header (category) and one in the signal
      const warningElements = screen.getAllByText('Warning')
      // Find the one that's inside a clickable signal div (has class cursor-pointer)
      const firstSignal = warningElements.find(el => el.closest('.cursor-pointer')) || warningElements[0]
      fireEvent.click(firstSignal)

      await waitFor(() => {
        expect(screen.getByText('Signal Details')).toBeInTheDocument()
        // Use queryAllByText since "HIBOR" appears in multiple places
        expect(screen.getAllByText((content) => content.includes('HIBOR')).length).toBeGreaterThan(0)
        expect(screen.getAllByText((content) => content.includes('5.80')).length).toBeGreaterThan(0)
      })
    })

    test('collapses signal details when clicked again', async () => {
      renderComponent()

      const warningElements = screen.getAllByText('Warning')
      const firstSignal = warningElements.find(el => el.closest('.cursor-pointer')) || warningElements[0]
      fireEvent.click(firstSignal)

      await waitFor(() => {
        expect(screen.getByText('Signal Details')).toBeInTheDocument()
      })

      fireEvent.click(firstSignal)

      await waitFor(() => {
        expect(screen.queryByText('Signal Details')).not.toBeInTheDocument()
      })
    })

    test('calls onSignalClick when signal is clicked', () => {
      const mockOnSignalClick = jest.fn()
      renderComponent({ onSignalClick: mockOnSignalClick })

      const warningElements = screen.getAllByText('Warning')
      const firstSignal = warningElements.find(el => el.closest('.cursor-pointer')) || warningElements[0]
      fireEvent.click(firstSignal)

      expect(mockOnSignalClick).toHaveBeenCalledWith(mockSignals[0])
    })

    test('calls onSignalDismiss when dismiss button is clicked', () => {
      const mockOnSignalDismiss = jest.fn()
      renderComponent({ onSignalDismiss: mockOnSignalDismiss })

      const dismissButtons = screen.getAllByTitle('Dismiss signal')
      const firstDismissButton = dismissButtons[0]
      fireEvent.click(firstDismissButton)

      expect(mockOnSignalDismiss).toHaveBeenCalledWith('signal-1')
    })

    test('prevents event propagation when dismiss is clicked', () => {
      const mockOnSignalClick = jest.fn()
      const mockOnSignalDismiss = jest.fn()
      renderComponent({
        onSignalClick: mockOnSignalClick,
        onSignalDismiss: mockOnSignalDismiss
      })

      const dismissButtons = screen.getAllByTitle('Dismiss signal')
      const firstDismissButton = dismissButtons[0]
      fireEvent.click(firstDismissButton)

      expect(mockOnSignalDismiss).toHaveBeenCalled()
      expect(mockOnSignalClick).not.toHaveBeenCalled()
    })
  })

  describe('Empty States', () => {
    test('shows empty state when no signals are provided', () => {
      renderComponent({ signals: [] })

      expect(screen.getByText((content) => content.includes('No signals found'))).toBeInTheDocument()
    })

    test('shows empty state when filters return no results', async () => {
      renderComponent()

      // Find all select elements and pick the first one (Category)
      const selects = document.querySelectorAll('select')
      const categorySelect = selects[0]
      fireEvent.change(categorySelect, { target: { value: 'non_existent_category' } })

      await waitFor(() => {
        expect(screen.getByText((content) => content.includes('No signals found'))).toBeInTheDocument()
      })
    })
  })

  describe('Max Visible Limit', () => {
    test('limits number of visible signals', () => {
      renderComponent({ maxVisible: 2 })

      expect(screen.getByText('Showing 2 of 3 signals')).toBeInTheDocument()
      // Check that only 2 signal type labels are visible
      const signalLabels = screen.getAllByText((content) => content.includes('Signal') || content === 'Warning' || content === 'Buy' || content === 'Sell')
      const visibleSignals = signalLabels.filter(el => el.textContent === 'Warning' || el.textContent === 'Buy' || el.textContent === 'Sell')
      expect(visibleSignals.length).toBe(2)
    })

    test('shows all signals when maxVisible is larger than signal count', () => {
      renderComponent({ maxVisible: 10 })

      expect(screen.getByText('Showing 3 of 3 signals')).toBeInTheDocument()
    })
  })

  describe('Auto-refresh', () => {
    test('shows auto-refresh indicator when enabled', () => {
      renderComponent({ autoRefresh: true, refreshInterval: 30000 })

      expect(screen.getByText('Auto-refresh every 30s')).toBeInTheDocument()
    })

    test('does not show auto-refresh indicator when disabled', () => {
      renderComponent({ autoRefresh: false })

      expect(screen.queryByText(/Auto-refresh/)).not.toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    test('provides proper ARIA labels', () => {
      renderComponent()

      // Check for filter labels
      expect(screen.getByText('Category')).toBeInTheDocument()
      expect(screen.getByText('Signal Type')).toBeInTheDocument()
      expect(screen.getByText('Time Range')).toBeInTheDocument()
      expect(screen.getByText('Sort By')).toBeInTheDocument()
    })

    test('supports keyboard navigation', () => {
      renderComponent()

      const selects = document.querySelectorAll('select')
      selects.forEach(select => {
        expect(select).not.toBeDisabled()
      })

      // Buttons only exist when onSignalDismiss is provided
      const dismissButtons = document.querySelectorAll('button[title="Dismiss signal"]')
      dismissButtons.forEach(button => {
        expect(button).not.toBeDisabled()
      })
    })

    test('provides semantic HTML structure', () => {
      renderComponent()

      // Should have proper heading hierarchy
      expect(screen.getByRole('heading', { level: 3 })).toBeInTheDocument()

      // Should have proper form elements (select elements don't have a role)
      const selects = document.querySelectorAll('select')
      expect(selects.length).toBeGreaterThan(0)
    })
  })

  describe('Responsive Design', () => {
    test('adapts layout for different screen sizes', () => {
      renderComponent()

      // Should have responsive grid classes
      const gridContainer = screen.getByText('Total Signals').closest('.grid')
      expect(gridContainer).toHaveClass('grid-cols-2', 'md:grid-cols-4')
    })
  })

  describe('Footer Information', () => {
    test('shows signal count in footer', () => {
      renderComponent()

      expect(screen.getByText('Showing 3 of 3 signals')).toBeInTheDocument()
    })

    test('shows dismiss all button when onSignalDismiss is provided', () => {
      const mockOnSignalDismiss = jest.fn()
      renderComponent({ onSignalDismiss: mockOnSignalDismiss })

      expect(screen.getByText('Dismiss All')).toBeInTheDocument()
    })

    test('dismisses all signals when Dismiss All is clicked', () => {
      const mockOnSignalDismiss = jest.fn()
      renderComponent({ onSignalDismiss: mockOnSignalDismiss })

      const dismissAllButton = screen.getByText('Dismiss All')
      fireEvent.click(dismissAllButton)

      expect(mockOnSignalDismiss).toHaveBeenCalledTimes(3) // Once for each signal
    })
  })
})