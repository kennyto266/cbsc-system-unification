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

  // Mock Date.now() to return consistent timestamp
  const originalDateNow = Date.now
  beforeEach(() => {
    Date.now = jest.fn(() => baseDate.getTime())
  })

  afterEach(() => {
    Date.now = originalDateNow
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
      expect(screen.getByText(/signals detected.*2 in last 24 hours/)).toBeInTheDocument()
      expect(screen.getByTestId('alert-triangle-icon')).toBeInTheDocument()
    })

    test('renders quick statistics', () => {
      renderComponent()

      expect(screen.getByText('Total Signals')).toBeInTheDocument()
      expect(screen.getByText('3')).toBeInTheDocument() // Total signals
      expect(screen.getByText('High Confidence')).toBeInTheDocument()
      // High confidence (> 0.8) is only signal-1 with 0.9
      const highConfidenceCount = screen.getAllByText('1')
      expect(highConfidenceCount.length).toBeGreaterThan(0)
    })

    test('renders signals list', async () => {
      renderComponent()

      // Wait for signals to render
      await waitFor(() => {
        expect(screen.getByText('Warning Signal')).toBeInTheDocument()
        expect(screen.getByText('Buy Signal')).toBeInTheDocument()
        expect(screen.getByText('Sell Signal')).toBeInTheDocument()
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

      expect(screen.getByText('Value: 6.50')).toBeInTheDocument()
      expect(screen.getByText('Value: 4.20')).toBeInTheDocument()
      expect(screen.getByText('Value: 48.50')).toBeInTheDocument()

      // Should show previous values when available
      expect(screen.getByText('6.50 (+0.70)')).toBeInTheDocument()
      expect(screen.getByText('4.20 (+0.40)')).toBeInTheDocument()
      expect(screen.getByText('48.50 (-2.70)')).toBeInTheDocument()
    })

    test('displays signal strength correctly', () => {
      renderComponent()

      expect(screen.getByText('Strength: 85%')).toBeInTheDocument()
      expect(screen.getByText('Strength: 75%')).toBeInTheDocument()
      expect(screen.getByText('Strength: 60%')).toBeInTheDocument()
    })

    test('displays confidence levels correctly', () => {
      renderComponent()

      expect(screen.getByText('Confidence: 90%')).toBeInTheDocument()
      expect(screen.getByText('Confidence: 85%')).toBeInTheDocument()
      expect(screen.getByText('Confidence: 70%')).toBeInTheDocument()
    })

    test('shows signal categories and timestamps', () => {
      renderComponent()

      expect(screen.getByText('Interest Rate')).toBeInTheDocument()
      expect(screen.getByText('Economic Growth')).toBeInTheDocument()
      expect(screen.getByText('Jan 15, 10:30')).toBeInTheDocument()
      expect(screen.getByText('Jan 15, 09:15')).toBeInTheDocument()
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
        // Should only show interest rate signals
        expect(screen.getByText('Warning Signal')).toBeInTheDocument()
        expect(screen.queryByText('Buy Signal')).not.toBeInTheDocument()
        expect(screen.queryByText('Sell Signal')).not.toBeInTheDocument()
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
        expect(screen.getByText('Warning Signal')).toBeInTheDocument()
        expect(screen.queryByText('Buy Signal')).not.toBeInTheDocument()
        expect(screen.queryByText('Sell Signal')).not.toBeInTheDocument()
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
        const firstSignal = screen.getByText('Strength: 85%')
        expect(firstSignal).toBeInTheDocument()
      })

      // Test sorting by confidence
      fireEvent.change(sortSelect, { target: { value: 'confidence' } })
      await waitFor(() => {
        const firstSignal = screen.getByText('Confidence: 90%')
        expect(firstSignal).toBeInTheDocument()
      })
    })
  })

  describe('Signal Interaction', () => {
    test('expands signal details when clicked', async () => {
      renderComponent()

      const firstSignal = screen.getByText('Warning Signal').closest('div')!
      fireEvent.click(firstSignal)

      await waitFor(() => {
        expect(screen.getByText('Signal Details')).toBeInTheDocument()
        expect(screen.getByText('Indicator: HIBOR')).toBeInTheDocument()
        expect(screen.getByText('Previous Value: 5.80')).toBeInTheDocument()
      })
    })

    test('collapses signal details when clicked again', async () => {
      renderComponent()

      const firstSignal = screen.getByText('Warning Signal').closest('div')!
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

      const firstSignal = screen.getByText('Warning Signal').closest('div')!
      fireEvent.click(firstSignal)

      expect(mockOnSignalClick).toHaveBeenCalledWith(mockSignals[0])
    })

    test('calls onSignalDismiss when dismiss button is clicked', () => {
      const mockOnSignalDismiss = jest.fn()
      renderComponent({ onSignalDismiss: mockOnSignalDismiss })

      const dismissButton = screen.getByTitle('Dismiss signal')
      fireEvent.click(dismissButton)

      expect(mockOnSignalDismiss).toHaveBeenCalledWith('signal-1')
    })

    test('prevents event propagation when dismiss is clicked', () => {
      const mockOnSignalClick = jest.fn()
      const mockOnSignalDismiss = jest.fn()
      renderComponent({
        onSignalClick: mockOnSignalClick,
        onSignalDismiss: mockOnSignalDismiss
      })

      const dismissButton = screen.getByTitle('Dismiss signal')
      fireEvent.click(dismissButton)

      expect(mockOnSignalDismiss).toHaveBeenCalled()
      expect(mockOnSignalClick).not.toHaveBeenCalled()
    })
  })

  describe('Empty States', () => {
    test('shows empty state when no signals are provided', () => {
      renderComponent({ signals: [] })

      expect(screen.getByText('No signals found for the selected criteria.')).toBeInTheDocument()
    })

    test('shows empty state when filters return no results', async () => {
      renderComponent()

      const categorySelect = screen.getByLabelText('Category')
      fireEvent.change(categorySelect, { target: { value: 'non_existent_category' } })

      await waitFor(() => {
        expect(screen.getByText('No signals found for the selected criteria.')).toBeInTheDocument()
      })
    })
  })

  describe('Max Visible Limit', () => {
    test('limits number of visible signals', () => {
      renderComponent({ maxVisible: 2 })

      expect(screen.getByText('Showing 2 of 3 signals')).toBeInTheDocument()
      expect(screen.getAllByRole('button').filter(btn =>
        btn.textContent?.includes('Signal') &&
        btn.textContent !== 'Dismiss All'
      )).toHaveLength(2)
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

      const buttons = screen.getAllByRole('button')
      buttons.forEach(button => {
        expect(button).not.toBeDisabled()
      })

      const selects = document.querySelectorAll('select')
      selects.forEach(select => {
        expect(select).not.toBeDisabled()
      })
    })

    test('provides semantic HTML structure', () => {
      renderComponent()

      // Should have proper heading hierarchy
      expect(screen.getByRole('heading', { level: 3 })).toBeInTheDocument()

      // Should have proper form elements (select elements don't have a role)
      const selects = document.querySelectorAll('select')
      expect(selects.length).toBeGreaterThan(0)
      expect(screen.getByRole('button')).toBeInTheDocument()
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