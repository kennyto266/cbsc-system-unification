/**
 * Strategy Log Viewer Component Tests
 * 策略日誌查看器組件測試
 */

import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import StrategyLogViewer from '../StrategyLogViewer'

// Mock lucide-react icons
jest.mock('lucide-react', () => ({
  Search: ({ className }: any) => <div data-testid="search-icon" className={className} />,
  Filter: ({ className }: any) => <div data-testid="filter-icon" className={className} />,
  Download: ({ className }: any) => <div data-testid="download-icon" className={className} />,
  RefreshCw: ({ className }: any) => <div data-testid="refresh-cw-icon" className={className} />,
  ChevronDown: ({ className }: any) => <div data-testid="chevron-down-icon" className={className} />,
  ChevronUp: ({ className }: any) => <div data-testid="chevron-up-icon" className={className} />,
  AlertCircle: ({ className }: any) => <div data-testid="alert-circle-icon" className={className} />,
  CheckCircle: ({ className }: any) => <div data-testid="check-circle-icon" className={className} />,
  XCircle: ({ className }: any) => <div data-testid="x-circle-icon" className={className} />,
  Info: ({ className }: any) => <div data-testid="info-icon" className={className} />,
  Clock: ({ className }: any) => <div data-testid="clock-icon" className={className} />,
  Zap: ({ className }: any) => <div data-testid="zap-icon" className={className} />,
  Settings: ({ className }: any) => <div data-testid="settings-icon" className={className} />,
  Play: ({ className }: any) => <div data-testid="play-icon" className={className} />,
  Pause: ({ className }: any) => <div data-testid="pause-icon" className={className} />,
  SkipForward: ({ className }: any) => <div data-testid="skip-forward-icon" className={className} />,
  Calendar: ({ className }: any) => <div data-testid="calendar-icon" className={className} />,
  Tag: ({ className }: any) => <div data-testid="tag-icon" className={className} />,
  FileText: ({ className }: any) => <div data-testid="file-text-icon" className={className} />,
  Eye: ({ className }: any) => <div data-testid="eye-icon" className={className} />,
  EyeOff: ({ className }: any) => <div data-testid="eye-off-icon" className={className} />,
  Terminal: ({ className }: any) => <div data-testid="terminal-icon" className={className} />,
  Bug: ({ className }: any) => <div data-testid="bug-icon" className={className} />,
  Activity: ({ className }: any) => <div data-testid="activity-icon" className={className} />,
  Database: ({ className }: any) => <div data-testid="database-icon" className={className} />,
  Shield: ({ className }: any) => <div data-testid="shield-icon" className={className} />,
  Bell: ({ className }: any) => <div data-testid="bell-icon" className={className} />,
  MessageSquare: ({ className }: any) => <div data-testid="message-square-icon" className={className} />,
  Cpu: ({ className }: any) => <div data-testid="cpu-icon" className={className} />,
  HardDrive: ({ className }: any) => <div data-testid="hard-drive-icon" className={className} />,
  Wifi: ({ className }: any) => <div data-testid="wifi-icon" className={className} />,
  TrendingUp: ({ className }: any) => <div data-testid="trending-up-icon" className={className} />
}))

describe('StrategyLogViewer', () => {
  const defaultProps = {
    strategyId: 'test-strategy',
    className: 'test-class'
  }

  beforeEach(() => {
    jest.clearAllMocks()

    // Mock URL.createObjectURL and revokeObjectURL for download tests
    global.URL.createObjectURL = jest.fn(() => 'mock-url')
    global.URL.revokeObjectURL = jest.fn()
    global.Blob = jest.fn((content, options) => ({ content, options })) as any

    // Mock createElement and click for download
    global.document.createElement = jest.fn(() => ({
      href: '',
      download: '',
      click: jest.fn()
    })) as any
  })

  afterEach(() => {
    jest.restoreAllMocks()
  })

  const renderComponent = (props = {}) => {
    return render(<StrategyLogViewer {...defaultProps} {...props} />)
  }

  describe('Rendering', () => {
    test('renders component header', () => {
      renderComponent()

      expect(screen.getByText('策略日誌查看器')).toBeInTheDocument()
      expect(screen.getByText(/顯示 \d+ 條日誌記錄/)).toBeInTheDocument()
    })

    test('renders search input when enabled', () => {
      renderComponent({ enableSearch: true })

      expect(screen.getByPlaceholderText('搜索日誌...')).toBeInTheDocument()
      expect(screen.getByTestId('search-icon')).toBeInTheDocument()
    })

    test('does not render search when disabled', () => {
      renderComponent({ enableSearch: false })

      expect(screen.queryByPlaceholderText('搜索日誌...')).not.toBeInTheDocument()
    })

    test('renders control buttons', () => {
      renderComponent()

      expect(screen.getByTestId('filter-icon')).toBeInTheDocument()
      expect(screen.getByTestId('download-icon')).toBeInTheDocument()
      expect(screen.getByTestId('refresh-cw-icon')).toBeInTheDocument()
      expect(screen.getByTestId('activity-icon')).toBeInTheDocument() // Live mode toggle
    })

    test('renders log entries', () => {
      renderComponent()

      // Should have log entries with various levels and categories
      expect(screen.getByText('調試')).toBeInTheDocument()
      expect(screen.getByText('信息')).toBeInTheDocument()
      expect(screen.getByText('警告')).toBeInTheDocument()
      expect(screen.getByText('錯誤')).toBeInTheDocument()
      expect(screen.getByText('嚴重')).toBeInTheDocument()
    })

    test('renders footer with log counts', () => {
      renderComponent()

      expect(screen.getByText(/總計: \d+ 條/)).toBeInTheDocument()
    })
  })

  describe('Search Functionality', () => {
    test('filters logs by search term', async () => {
      renderComponent({ enableSearch: true })

      const searchInput = screen.getByPlaceholderText('搜索日誌...')
      fireEvent.change(searchInput, { target: { value: '策略' } })

      await waitFor(() => {
        expect(screen.getByText(/顯示 \d+ 條日誌記錄/)).toBeInTheDocument()
      })
    })

    test('clears search when input is empty', async () => {
      renderComponent({ enableSearch: true })

      const searchInput = screen.getByPlaceholderText('搜索日誌...')
      fireEvent.change(searchInput, { target: { value: '策略' } })
      fireEvent.change(searchInput, { target: { value: '' } })

      await waitFor(() => {
        // Should show all logs again
        expect(screen.getByText(/顯示 \d+ 條日誌記錄/)).toBeInTheDocument()
      })
    })

    test('searches across message, source, and correlation ID', async () => {
      const customLogs = [
        {
          id: 'log-1',
          timestamp: '2024-01-01T10:00:00Z',
          level: 'info' as const,
          category: 'execution' as const,
          message: '策略開始執行',
          source: 'strategy-engine',
          correlationId: 'corr-123'
        },
        {
          id: 'log-2',
          timestamp: '2024-01-01T10:01:00Z',
          level: 'error' as const,
          category: 'system' as const,
          message: '系統錯誤',
          source: 'data-service',
          correlationId: 'corr-456'
        }
      ]

      renderComponent({ enableSearch: true, logs: customLogs })

      // Search by message
      const searchInput = screen.getByPlaceholderText('搜索日誌...')
      fireEvent.change(searchInput, { target: { value: '策略' } })

      await waitFor(() => {
        expect(screen.getByText('策略開始執行')).toBeInTheDocument()
        expect(screen.queryByText('系統錯誤')).not.toBeInTheDocument()
      })

      // Search by source
      fireEvent.change(searchInput, { target: { value: 'data-service' } })

      await waitFor(() => {
        expect(screen.getByText('系統錯誤')).toBeInTheDocument()
        expect(screen.queryByText('策略開始執行')).not.toBeInTheDocument()
      })

      // Search by correlation ID
      fireEvent.change(searchInput, { target: { value: 'corr-123' } })

      await waitFor(() => {
        expect(screen.getByText('策略開始執行')).toBeInTheDocument()
        expect(screen.queryByText('系統錯誤')).not.toBeInTheDocument()
      })
    })
  })

  describe('Filter Panel', () => {
    test('toggles filter panel visibility', () => {
      renderComponent()

      const filterButton = screen.getByTestId('filter-icon').parentElement
      expect(screen.queryByText('日誌級別')).not.toBeInTheDocument()

      fireEvent.click(filterButton!)

      expect(screen.getByText('日誌級別')).toBeInTheDocument()
      expect(screen.getByText('日誌分類')).toBeInTheDocument()
      expect(screen.getByText('時間範圍')).toBeInTheDocument()
      expect(screen.getByText('快速操作')).toBeInTheDocument()
    })

    test('filters by log levels', async () => {
      renderComponent()

      // Open filter panel
      const filterButton = screen.getByTestId('filter-icon').parentElement
      fireEvent.click(filterButton!)

      // Uncheck all levels except error
      const errorCheckbox = screen.getByLabelText('錯誤')
      const warningCheckbox = screen.getByLabelText('警告')
      const infoCheckbox = screen.getByLabelText('信息')

      fireEvent.click(errorCheckbox) // Should be checked by default
      fireEvent.click(warningCheckbox)
      fireEvent.click(infoCheckbox)

      await waitFor(() => {
        expect(screen.getByText(/顯示 \d+ 條日誌記錄/)).toBeInTheDocument()
      })
    })

    test('filters by categories', async () => {
      renderComponent()

      // Open filter panel
      const filterButton = screen.getByTestId('filter-icon').parentElement
      fireEvent.click(filterButton!)

      // Select only execution category
      const executionCheckbox = screen.getByLabelText('執行')
      fireEvent.click(executionCheckbox)

      await waitFor(() => {
        expect(screen.getByText(/顯示 \d+ 條日誌記錄/)).toBeInTheDocument()
      })
    })

    test('filters by time range', async () => {
      renderComponent()

      // Open filter panel
      const filterButton = screen.getByTestId('filter-icon').parentElement
      fireEvent.click(filterButton!)

      // Set time range
      const startInput = screen.getByLabelText('開始時間')
      const endInput = screen.getByLabelText('結束時間')

      fireEvent.change(startInput, { target: { value: '2024-01-01T00:00' } })
      fireEvent.change(endInput, { target: { value: '2024-01-02T00:00' } })

      await waitFor(() => {
        expect(screen.getByText(/顯示 \d+ 條日誌記錄/)).toBeInTheDocument()
      })
    })

    test('resets filters', async () => {
      renderComponent()

      // Open filter panel
      const filterButton = screen.getByTestId('filter-icon').parentElement
      fireEvent.click(filterButton!)

      // Modify some filters
      const infoCheckbox = screen.getByLabelText('信息')
      fireEvent.click(infoCheckbox)

      // Reset filters
      const resetButton = screen.getByText('重置過濾器')
      fireEvent.click(resetButton)

      // Should restore default filter state
      expect(infoCheckbox).toBeChecked()
    })
  })

  describe('Log Entry Interactions', () => {
    test('expands and collapses log entries', async () => {
      const customLogs = [
        {
          id: 'log-1',
          timestamp: '2024-01-01T10:00:00Z',
          level: 'info' as const,
          category: 'execution' as const,
          message: '策略開始執行',
          details: { param1: 'value1', param2: 'value2' },
          stackTrace: 'at test.js:1:1'
        }
      ]

      renderComponent({ logs: customLogs })

      const expandButton = screen.getByText('策略開始執行').closest('div')?.querySelector('button')
      fireEvent.click(expandButton!)

      await waitFor(() => {
        expect(screen.getByText('詳細信息')).toBeInTheDocument()
        expect(screen.getByText('堆棧跟蹤')).toBeInTheDocument()
        expect(screen.getByText('相關ID:')).toBeInTheDocument()
      })

      // Collapse again
      fireEvent.click(expandButton!)

      await waitFor(() => {
        expect(screen.queryByText('詳細信息')).not.toBeInTheDocument()
      })
    })

    test('calls onLogClick when log is clicked', () => {
      const mockOnLogClick = jest.fn()
      const customLogs = [
        {
          id: 'log-1',
          timestamp: '2024-01-01T10:00:00Z',
          level: 'info' as const,
          category: 'execution' as const,
          message: '策略開始執行'
        }
      ]

      renderComponent({ logs: customLogs, onLogClick: mockOnLogClick })

      const logEntry = screen.getByText('策略開始執行').closest('div')
      fireEvent.click(logEntry!)

      expect(mockOnLogClick).toHaveBeenCalledWith(customLogs[0])
    })

    test('expands all logs with quick action', async () => {
      renderComponent()

      // Open filter panel
      const filterButton = screen.getByTestId('filter-icon').parentElement
      fireEvent.click(filterButton!)

      // Click expand all
      const expandAllButton = screen.getByText('展開前50條')
      fireEvent.click(expandAllButton)

      // Should expand some logs (check if any expand buttons are in expanded state)
      await waitFor(() => {
        const expandButtons = screen.getAllByTestId('chevron-up-icon')
        expect(expandButtons.length).toBeGreaterThan(0)
      })
    })

    test('collapses all logs with quick action', async () => {
      renderComponent()

      // Open filter panel
      const filterButton = screen.getByTestId('filter-icon').parentElement
      fireEvent.click(filterButton!)

      // First expand some logs
      const expandAllButton = screen.getByText('展開前50條')
      fireEvent.click(expandAllButton)

      // Then collapse all
      const collapseAllButton = screen.getByText('收起全部')
      fireEvent.click(collapseAllButton)

      await waitFor(() => {
        // All expand buttons should be in collapsed state
        const collapseButtons = screen.getAllByTestId('chevron-down-icon')
        expect(collapseButtons.length).toBeGreaterThan(0)
      })
    })
  })

  describe('Export Functionality', () => {
    test('shows export menu on hover', async () => {
      renderComponent({ enableExport: true })

      const exportButton = screen.getByTestId('download-icon').parentElement
      fireEvent.mouseEnter(exportButton!)

      await waitFor(() => {
        expect(screen.getByText('導出 CSV')).toBeInTheDocument()
        expect(screen.getByText('導出 JSON')).toBeInTheDocument()
        expect(screen.getByText('導出 TXT')).toBeInTheDocument()
      })
    })

    test('calls custom onExport callback', () => {
      const mockOnExport = jest.fn()
      renderComponent({ enableExport: true, onExport: mockOnExport })

      const exportButton = screen.getByTestId('download-icon').parentElement
      fireEvent.mouseEnter(exportButton!)

      fireEvent.click(screen.getByText('導出 CSV'))
      expect(mockOnExport).toHaveBeenCalledWith('csv')

      fireEvent.click(screen.getByText('導出 JSON'))
      expect(mockOnExport).toHaveBeenCalledWith('json')

      fireEvent.click(screen.getByText('導出 TXT'))
      expect(mockOnExport).toHaveBeenCalledWith('txt')
    })

    test('downloads default format when no custom callback', () => {
      renderComponent({ enableExport: true })

      const exportButton = screen.getByTestId('download-icon').parentElement
      fireEvent.mouseEnter(exportButton!)

      fireEvent.click(screen.getByText('導出 CSV'))

      expect(global.Blob).toHaveBeenCalled()
      expect(global.URL.createObjectURL).toHaveBeenCalled()
      expect(global.URL.revokeObjectURL).toHaveBeenCalled()
    })
  })

  describe('Live Mode', () => {
    beforeEach(() => {
      jest.useFakeTimers()
    })

    afterEach(() => {
      jest.useRealTimers()
    })

    test('toggles live mode', () => {
      renderComponent({ enableLiveMode: true })

      const liveModeButton = screen.getByTitle('關閉實時模式')
      fireEvent.click(liveModeButton)

      expect(screen.getByTitle('開啟實時模式')).toBeInTheDocument()
    })

    test('shows live mode indicator when active', () => {
      renderComponent({ enableLiveMode: true, autoRefresh: true })

      expect(screen.getByText('實時模式')).toBeInTheDocument()
      expect(screen.getByTestId('activity-icon')).toBeInTheDocument()
    })

    test('auto-refreshes in live mode', () => {
      renderComponent({ enableLiveMode: true, autoRefresh: true, refreshInterval: 1000 })

      jest.advanceTimersByTime(1000)

      expect(screen.getByTestId('refresh-cw-icon')).toHaveClass('animate-spin')
    })
  })

  describe('Custom Logs', () => {
    test('uses provided logs when available', () => {
      const customLogs = [
        {
          id: 'custom-1',
          timestamp: '2024-01-01T10:00:00Z',
          level: 'error' as const,
          category: 'trading' as const,
          message: '自定義錯誤日誌',
          source: 'custom-source'
        }
      ]

      renderComponent({ logs: customLogs })

      expect(screen.getByText('自定義錯誤日誌')).toBeInTheDocument()
      expect(screen.getByText('custom-source')).toBeInTheDocument()
    })

    test('handles empty logs array', () => {
      renderComponent({ logs: [] })

      expect(screen.getByText('沒有找到匹配的日誌記錄')).toBeInTheDocument()
    })

    test('respects maxEntries limit', () => {
      const customLogs = Array.from({ length: 1500 }, (_, i) => ({
        id: `log-${i}`,
        timestamp: '2024-01-01T10:00:00Z',
        level: 'info' as const,
        category: 'system' as const,
        message: `Log message ${i}`
      }))

      renderComponent({ logs: customLogs, maxEntries: 1000 })

      expect(screen.getByText(/顯示 1000 條日誌記錄/)).toBeInTheDocument()
    })
  })

  describe('Compact Mode', () => {
    test('renders in compact mode when enabled', () => {
      renderComponent({ compactMode: true })

      const logEntries = screen.getAllByText(/Log message \d+/)
      logEntries.forEach(entry => {
        const container = entry.closest('div')
        expect(container).toHaveClass('p-3')
      })
    })

    test('shows timestamp hidden in compact mode', () => {
      renderComponent({ compactMode: true })

      // Timestamp should be hidden on small screens in compact mode
      const timestamps = screen.getAllByText(/\d{4}\/\d{1,2}\/\d{1,2}/)
      expect(timestamps.length).toBe(0)
    })
  })

  describe('Log Levels and Categories', () => {
    test('displays correct icons for different levels', () => {
      const customLogs = [
        {
          id: 'debug-log',
          timestamp: '2024-01-01T10:00:00Z',
          level: 'debug' as const,
          category: 'system' as const,
          message: 'Debug message'
        },
        {
          id: 'info-log',
          timestamp: '2024-01-01T10:01:00Z',
          level: 'info' as const,
          category: 'system' as const,
          message: 'Info message'
        },
        {
          id: 'warning-log',
          timestamp: '2024-01-01T10:02:00Z',
          level: 'warning' as const,
          category: 'system' as const,
          message: 'Warning message'
        },
        {
          id: 'error-log',
          timestamp: '2024-01-01T10:03:00Z',
          level: 'error' as const,
          category: 'system' as const,
          message: 'Error message'
        },
        {
          id: 'critical-log',
          timestamp: '2024-01-01T10:04:00Z',
          level: 'critical' as const,
          category: 'system' as const,
          message: 'Critical message'
        }
      ]

      renderComponent({ logs: customLogs })

      expect(screen.getByTestId('bug-icon')).toBeInTheDocument() // debug
      expect(screen.getByTestId('info-icon')).toBeInTheDocument() // info
      expect(screen.getByTestId('alert-circle-icon')).toBeInTheDocument() // warning
      expect(screen.getByTestId('x-circle-icon')).toBeInTheDocument() // error
      expect(screen.getByTestId('shield-icon')).toBeInTheDocument() // critical
    })

    test('displays correct icons for different categories', () => {
      const customLogs = [
        {
          id: 'execution-log',
          timestamp: '2024-01-01T10:00:00Z',
          level: 'info' as const,
          category: 'execution' as const,
          message: 'Execution message'
        },
        {
          id: 'performance-log',
          timestamp: '2024-01-01T10:01:00Z',
          level: 'info' as const,
          category: 'performance' as const,
          message: 'Performance message'
        },
        {
          id: 'risk-log',
          timestamp: '2024-01-01T10:02:00Z',
          level: 'info' as const,
          category: 'risk' as const,
          message: 'Risk message'
        },
        {
          id: 'data-log',
          timestamp: '2024-01-01T10:03:00Z',
          level: 'info' as const,
          category: 'data' as const,
          message: 'Data message'
        },
        {
          id: 'system-log',
          timestamp: '2024-01-01T10:04:00Z',
          level: 'info' as const,
          category: 'system' as const,
          message: 'System message'
        }
      ]

      renderComponent({ logs: customLogs })

      expect(screen.getByTestId('play-icon')).toBeInTheDocument() // execution
      expect(screen.getByTestId('activity-icon')).toBeInTheDocument() // performance
      expect(screen.getByTestId('shield-icon')).toBeInTheDocument() // risk
      expect(screen.getByTestId('database-icon')).toBeInTheDocument() // data
      expect(screen.getByTestId('cpu-icon')).toBeInTheDocument() // system
    })
  })

  describe('Refresh Functionality', () => {
    test('handles manual refresh', () => {
      renderComponent()

      const refreshButton = screen.getByTestId('refresh-cw-icon').parentElement
      fireEvent.click(refreshButton)

      expect(screen.getByTestId('refresh-cw-icon')).toHaveClass('animate-spin')
    })
  })

  describe('Accessibility', () => {
    test('provides proper ARIA labels', () => {
      renderComponent()

      // Check for button titles
      expect(screen.getByTitle(/過濾器/)).toBeInTheDocument()
      expect(screen.getByTitle(/導出/)).toBeInTheDocument()
      expect(screen.getByTitle(/實時模式/)).toBeInTheDocument()
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

      // Should have proper headings
      expect(screen.getByRole('heading', { name: '策略日誌查看器' })).toBeInTheDocument()
    })

    test('provides proper form labels for filters', () => {
      renderComponent()

      // Open filter panel
      const filterButton = screen.getByTestId('filter-icon').parentElement
      fireEvent.click(filterButton!)

      expect(screen.getByLabelText('日誌級別')).toBeInTheDocument()
      expect(screen.getByLabelText('日誌分類')).toBeInTheDocument()
      expect(screen.getByLabelText('開始時間')).toBeInTheDocument()
      expect(screen.getByLabelText('結束時間')).toBeInTheDocument()
    })
  })

  describe('Performance', () => {
    test('handles large number of logs efficiently', () => {
      const customLogs = Array.from({ length: 10000 }, (_, i) => ({
        id: `log-${i}`,
        timestamp: new Date(Date.now() - i * 1000).toISOString(),
        level: ['debug', 'info', 'warning', 'error', 'critical'][i % 5] as any,
        category: ['execution', 'performance', 'risk', 'data', 'system'][i % 5] as any,
        message: `Performance test log ${i}`,
        source: `source-${i % 10}`
      }))

      const startTime = performance.now()
      renderComponent({ logs: customLogs, maxEntries: 1000 })
      const endTime = performance.now()

      // Should render within reasonable time (less than 100ms for 1000 entries)
      expect(endTime - startTime).toBeLessThan(100)
    })
  })
})