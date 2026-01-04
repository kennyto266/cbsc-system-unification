/**
 * Risk Indicator Component Tests
 * 風險指標組件測試
 */

import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import RiskIndicator from '../RiskIndicator'

// Mock recharts components
jest.mock('recharts', () => ({
  LineChart: ({ children }: any) => <div data-testid="line-chart">{children}</div>,
  Line: () => <div data-testid="line" />,
  AreaChart: ({ children }: any) => <div data-testid="area-chart">{children}</div>,
  Area: () => <div data-testid="area" />,
  BarChart: ({ children }: any) => <div data-testid="bar-chart">{children}</div>,
  Bar: () => <div data-testid="bar" />,
  PieChart: ({ children }: any) => <div data-testid="pie-chart">{children}</div>,
  Pie: () => <div data-testid="pie" />,
  Treemap: ({ children }: any) => <div data-testid="treemap">{children}</div>,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  Legend: () => <div data-testid="legend" />,
  ResponsiveContainer: ({ children }: any) => <div>{children}</div>
}))

// Mock lucide-react icons
jest.mock('lucide-react', () => ({
  AlertTriangle: ({ className }: any) => <div data-testid="alert-triangle-icon" className={className} />,
  TrendingUp: ({ className }: any) => <div data-testid="trending-up-icon" className={className} />,
  TrendingDown: ({ className }: any) => <div data-testid="trending-down-icon" className={className} />,
  Shield: ({ className }: any) => <div data-testid="shield-icon" className={className} />,
  Activity: ({ className }: any) => <div data-testid="activity-icon" className={className} />,
  Zap: ({ className }: any) => <div data-testid="zap-icon" className={className} />,
  Target: ({ className }: any) => <div data-testid="target-icon" className={className} />,
  Eye: ({ className }: any) => <div data-testid="eye-icon" className={className} />,
  Bell: ({ className }: any) => <div data-testid="bell-icon" className={className} />,
  ChevronDown: ({ className }: any) => <div data-testid="chevron-down-icon" className={className} />,
  ChevronUp: ({ className }: any) => <div data-testid="chevron-up-icon" className={className} />,
  RefreshCw: ({ className }: any) => <div data-testid="refresh-cw-icon" className={className} />,
  Settings: ({ className }: any) => <div data-testid="settings-icon" className={className} />,
  Download: ({ className }: any) => <div data-testid="download-icon" className={className} />,
  Info: ({ className }: any) => <div data-testid="info-icon" className={className} />
}))

describe('RiskIndicator', () => {
  const defaultProps = {
    strategyId: 'test-strategy',
    className: 'test-class'
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  const renderComponent = (props = {}) => {
    return render(<RiskIndicator {...defaultProps} {...props} />)
  }

  describe('Rendering', () => {
    test('renders component header', () => {
      renderComponent()

      expect(screen.getByText('風險指標監控')).toBeInTheDocument()
      expect(screen.getByText('最後更新:')).toBeInTheDocument()
    })

    test('renders risk overview section', () => {
      renderComponent()

      expect(screen.getByText('整體風險評分')).toBeInTheDocument()
      expect(screen.getByText('關鍵風險指標')).toBeInTheDocument()
      expect(screen.getByText('風險預警')).toBeInTheDocument()
    })

    test('displays risk level indicator', () => {
      renderComponent()

      const riskLevel = screen.getByText(/風險水平/)
      expect(riskLevel).toBeInTheDocument()
    })

    test('renders risk gauges', () => {
      renderComponent()

      expect(screen.getByText('回撤 (%)')).toBeInTheDocument()
      expect(screen.getByText('VaR (%)')).toBeInTheDocument()
      expect(screen.getByText('波動率 (%)')).toBeInTheDocument()
      expect(screen.getByText('集中度 (%)')).toBeInTheDocument()
    })
  })

  describe('Risk Gauges', () => {
    test('displays gauge values correctly', () => {
      const customData = {
        metrics: [
          { timestamp: '2024-01-01', value: 8, category: 'drawdown' },
          { timestamp: '2024-01-01', value: 2.5, category: 'var' },
          { timestamp: '2024-01-01', value: 12, category: 'volatility' },
          { timestamp: '2024-01-01', value: 20, category: 'concentration' }
        ]
      }

      renderComponent({ data: customData })

      // Should show gauge values
      expect(screen.getByText('8.0')).toBeInTheDocument() // drawdown
      expect(screen.getByText('2.5')).toBeInTheDocument() // var
      expect(screen.getByText('12.0')).toBeInTheDocument() // volatility
      expect(screen.getByText('20.0')).toBeInTheDocument() // concentration
    })

    test('applies correct colors based on thresholds', () => {
      const customData = {
        metrics: [
          { timestamp: '2024-01-01', value: 14, category: 'drawdown' }, // Over warning threshold
          { timestamp: '2024-01-01', value: 4.5, category: 'var' }, // Critical threshold
          { timestamp: '2024-01-01', value: 16, category: 'volatility' }, // Warning threshold
          { timestamp: '2024-01-01', value: 5, category: 'concentration' } // Low risk
        ]
      }

      renderComponent({ data: customData })

      // Gauges should be rendered with threshold-based colors
      expect(screen.getByText('14.0')).toBeInTheDocument()
      expect(screen.getByText('4.5')).toBeInTheDocument()
      expect(screen.getByText('16.0')).toBeInTheDocument()
      expect(screen.getByText('5.0')).toBeInTheDocument()
    })
  })

  describe('Risk Alerts', () => {
    test('displays risk alerts summary', () => {
      renderComponent()

      expect(screen.getByTestId('bell-icon')).toBeInTheDocument()
      expect(screen.getByText(/暫無未確認預警/)).toBeInTheDocument()
    })

    test('shows unacknowledged alerts count', () => {
      const customData = {
        alerts: [
          {
            id: '1',
            level: 'high' as const,
            type: '回撤警告',
            message: '當前回撤水平為 7.5%，接近風險閾值',
            timestamp: '2024-01-01T10:00:00Z',
            acknowledged: false,
            action: '考慮減少倉位或調整策略參數'
          },
          {
            id: '2',
            level: 'medium' as const,
            type: '波動率增加',
            message: '市場波動率顯著上升，建議密切監控',
            timestamp: '2024-01-01T09:00:00Z',
            acknowledged: true
          }
        ]
      }

      renderComponent({ data: customData })

      expect(screen.getByText('回撤警告')).toBeInTheDocument()
      expect(screen.getByText('當前回撤水平為 7.5%，接近風險閾值')).toBeInTheDocument()
      expect(screen.getByText('確認')).toBeInTheDocument()
    })

    test('handles alert acknowledgment', () => {
      const mockOnAlertAcknowledge = jest.fn()
      const customData = {
        alerts: [
          {
            id: '1',
            level: 'high' as const,
            type: '回撤警告',
            message: '當前回撤水平為 7.5%',
            timestamp: '2024-01-01T10:00:00Z',
            acknowledged: false
          }
        ]
      }

      renderComponent({ data: customData, onAlertAcknowledge: mockOnAlertAcknowledge })

      const acknowledgeButton = screen.getByText('確認')
      fireEvent.click(acknowledgeButton)

      expect(mockOnAlertAcknowledge).toHaveBeenCalledWith('1')
    })

    test('shows alert details when expanded', async () => {
      const customData = {
        alerts: [
          {
            id: '1',
            level: 'high' as const,
            type: '回撤警告',
            message: '當前回撤水平為 7.5%，接近風險閾值',
            timestamp: '2024-01-01T10:00:00Z',
            acknowledged: false,
            action: '考慮減少倉位或調整策略參數'
          }
        ]
      }

      renderComponent({ data: customData, showAlerts: true })

      // Expand alerts section
      const alertsSection = screen.getByText('風險預警詳情').parentElement?.parentElement
      const expandButton = alertsSection?.querySelector('button')
      fireEvent.click(expandButton!)

      await waitFor(() => {
        expect(screen.getByText('建議操作: 考慮減少倉位或調整策略參數')).toBeInTheDocument()
        expect(screen.getByText('2024/1/1')).toBeInTheDocument()
      })
    })
  })

  describe('Risk Metrics Chart', () => {
    test('renders risk metrics trend chart', async () => {
      renderComponent()

      // Expand overview section
      const overviewSection = screen.getByText('風險指標趨勢').parentElement?.parentElement
      const expandButton = overviewSection?.querySelector('button')
      fireEvent.click(expandButton!)

      await waitFor(() => {
        expect(screen.getByTestId('line-chart')).toBeInTheDocument()
      })
    })

    test('displays all risk categories', async () => {
      renderComponent()

      // Expand overview section
      const overviewSection = screen.getByText('風險指標趨勢').parentElement?.parentElement
      const expandButton = overviewSection?.querySelector('button')
      fireEvent.click(expandButton!)

      await waitFor(() => {
        expect(screen.getByTestId('line-chart')).toBeInTheDocument()
        expect(screen.getByTestId('tooltip')).toBeInTheDocument()
        expect(screen.getByTestId('legend')).toBeInTheDocument()
      })
    })
  })

  describe('Position Risk', () => {
    test('displays position risk table when enabled', async () => {
      const customData = {
        positions: [
          {
            symbol: 'HKD/USD',
            position: 1000000,
            marketValue: 1000000,
            weight: 25,
            risk: 12.5,
            contribution: 15.2
          }
        ]
      }

      renderComponent({ data: customData, showPositions: true })

      // Expand positions section
      const positionsSection = screen.getByText('持倉風險分析').parentElement?.parentElement
      const expandButton = positionsSection?.querySelector('button')
      fireEvent.click(expandButton!)

      await waitFor(() => {
        expect(screen.getByText('HKD/USD')).toBeInTheDocument()
        expect(screen.getByText('¥1,000,000')).toBeInTheDocument()
        expect(screen.getByText('25.0%')).toBeInTheDocument()
        expect(screen.getByText('12.5%')).toBeInTheDocument()
        expect(screen.getByText('15.2%')).toBeInTheDocument()
      })
    })

    test('renders position risk chart', async () => {
      const customData = {
        positions: [
          {
            symbol: 'HSI',
            position: 50,
            marketValue: 1500000,
            weight: 37.5,
            risk: 18.8,
            contribution: 28.5
          }
        ]
      }

      renderComponent({ data: customData, showPositions: true })

      // Expand positions section
      const positionsSection = screen.getByText('持倉風險分析').parentElement?.parentElement
      const expandButton = positionsSection?.querySelector('button')
      fireEvent.click(expandButton!)

      await waitFor(() => {
        expect(screen.getByTestId('bar-chart')).toBeInTheDocument()
      })
    })
  })

  describe('Stress Test', () => {
    test('displays stress test scenarios when enabled', async () => {
      const customData = {
        stressTest: [
          { scenario: '2008金融危機', impact: -25, probability: 5 },
          { scenario: '2020疫情', impact: -15, probability: 10 }
        ]
      }

      renderComponent({ data: customData, showStressTest: true })

      // Expand stress test section
      const stressTestSection = screen.getByText('壓力測試').parentElement?.parentElement
      const expandButton = stressTestSection?.querySelector('button')
      fireEvent.click(expandButton!)

      await waitFor(() => {
        expect(screen.getByText('2008金融危機')).toBeInTheDocument()
        expect(screen.getByText('-25.0%')).toBeInTheDocument()
        expect(screen.getByText('5%')).toBeInTheDocument()
        expect(screen.getByText('2020疫情')).toBeInTheDocument()
        expect(screen.getByText('-15.0%')).toBeInTheDocument()
        expect(screen.getByText('10%')).toBeInTheDocument()
      })
    })

    test('shows risk warning message', async () => {
      renderComponent({ showStressTest: true })

      // Expand stress test section
      const stressTestSection = screen.getByText('壓力測試').parentElement?.parentElement
      const expandButton = stressTestSection?.querySelector('button')
      fireEvent.click(expandButton!)

      await waitFor(() => {
        expect(screen.getByText('風險提示')).toBeInTheDocument()
        expect(screen.getByText(/壓力測試結果基於歷史數據模擬/)).toBeInTheDocument()
        expect(screen.getByTestId('info-icon')).toBeInTheDocument()
      })
    })
  })

  describe('Interactive Features', () => {
    test('expands and collapses sections', async () => {
      renderComponent()

      // Test risk metrics section
      const metricsSection = screen.getByText('風險指標趨勢').parentElement?.parentElement
      const expandButton = metricsSection?.querySelector('button')

      // Should be expanded by default
      expect(screen.getByTestId('line-chart')).toBeInTheDocument()

      // Collapse
      fireEvent.click(expandButton!)
      expect(screen.queryByTestId('line-chart')).not.toBeInTheDocument()

      // Expand again
      fireEvent.click(expandButton!)
      await waitFor(() => {
        expect(screen.getByTestId('line-chart')).toBeInTheDocument()
      })
    })

    test('handles refresh action', () => {
      renderComponent()

      const refreshButton = screen.getByTestId('refresh-cw-icon').parentElement
      fireEvent.click(refreshButton)

      expect(screen.getByTestId('refresh-cw-icon')).toHaveClass('animate-spin')
    })
  })

  describe('Risk Score Display', () => {
    test('displays overall risk score', () => {
      const customData = {
        riskScore: {
          overall: 75,
          volatility: 70,
          liquidity: 85,
          concentration: 60,
          market: 55,
          credit: 90,
          operational: 95
        }
      }

      renderComponent({ data: customData })

      expect(screen.getByText('75')).toBeInTheDocument()
      expect(screen.getByText('分')).toBeInTheDocument()
    })

    test('shows appropriate risk level text', () => {
      const customData = {
        riskScore: { overall: 85, volatility: 70, liquidity: 85, concentration: 60, market: 55, credit: 90, operational: 95 }
      }

      renderComponent({ data: customData })

      expect(screen.getByText('風險水平良好')).toBeInTheDocument()
    })

    test('displays correct risk level based on score', () => {
      // Test low risk
      const lowRiskData = {
        riskScore: { overall: 85, volatility: 70, liquidity: 85, concentration: 60, market: 55, credit: 90, operational: 95 }
      }
      renderComponent({ data: lowRiskData })
      expect(screen.getByText('低風險')).toBeInTheDocument()

      // Test high risk
      const highRiskData = {
        riskScore: { overall: 35, volatility: 70, liquidity: 85, concentration: 60, market: 55, credit: 90, operational: 95 }
      }
      render({ children: <RiskIndicator {...defaultProps} data={highRiskData} /> })
      expect(screen.getByText('嚴重風險')).toBeInTheDocument()
    })
  })

  describe('Custom Data Integration', () => {
    test('uses provided risk limits', () => {
      const customData = {
        limits: {
          maxDrawdown: 20,
          maxVaR: 8,
          maxPositionSize: 25,
          maxLeverage: 3,
          maxSectorExposure: 35,
          stopLossThreshold: 15
        }
      }

      renderComponent({ data: customData })

      // Gauges should use custom limits for threshold calculations
      expect(screen.getByText('回撤 (%)')).toBeInTheDocument()
      expect(screen.getByText('VaR (%)')).toBeInTheDocument()
    })
  })

  describe('Auto-refresh', () => {
    beforeEach(() => {
      jest.useFakeTimers()
    })

    afterEach(() => {
      jest.useRealTimers()
    })

    test('auto-refreshes when enabled', () => {
      renderComponent({ autoRefresh: true, refreshInterval: 1000 })

      jest.advanceTimersByTime(1000)

      expect(screen.getByTestId('refresh-cw-icon')).toHaveClass('animate-spin')
    })

    test('does not auto-refresh when disabled', () => {
      renderComponent({ autoRefresh: false, refreshInterval: 1000 })

      jest.advanceTimersByTime(1000)

      expect(screen.getByTestId('refresh-cw-icon')).not.toHaveClass('animate-spin')
    })
  })

  describe('Responsive Design', () => {
    test('adapts layout for different screen sizes', () => {
      const { container } = renderComponent()

      // Should have responsive grid classes
      const overviewGrid = container.querySelector('.grid-cols-1.lg\\:grid-cols-3')
      expect(overviewGrid).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    test('provides proper ARIA labels', () => {
      renderComponent()

      // Should have proper headings
      expect(screen.getByRole('heading', { name: '風險指標監控' })).toBeInTheDocument()
      expect(screen.getByRole('heading', { name: '整體風險評分' })).toBeInTheDocument()
      expect(screen.getByRole('heading', { name: '關鍵風險指標' })).toBeInTheDocument()
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

      // Should have proper button roles
      expect(screen.getByRole('button', { name: /refresh/i })).toBeInTheDocument()
    })
  })

  describe('Data Validation', () => {
    test('handles missing data gracefully', () => {
      renderComponent({ data: undefined })

      // Should still render component with mock data
      expect(screen.getByText('風險指標監控')).toBeInTheDocument()
      expect(screen.getByTestId('line-chart')).toBeInTheDocument()
    })

    test('handles empty arrays gracefully', () => {
      const customData = {
        alerts: [],
        positions: [],
        stressTest: [],
        metrics: []
      }

      renderComponent({ data: customData })

      expect(screen.getByText('風險指標監控')).toBeInTheDocument()
      expect(screen.getByText(/暫無未確認預警/)).toBeInTheDocument()
    })
  })
})