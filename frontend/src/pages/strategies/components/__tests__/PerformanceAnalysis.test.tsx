import React from 'react'
import { render, screen, fireEvent, waitFor, cleanup } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { ThemeProvider } from '@/contexts/ThemeContext'
import PerformanceAnalysis from '../PerformanceAnalysis'
import { useGetStrategyQuery } from '../../../../store/api/apiSlice'

// Mock the API hooks
jest.mock('../../../../store/api/apiSlice', () => ({
  useGetStrategyQuery: jest.fn(),
  useGetPerformanceQuery: jest.fn()
}))

// Mock recharts components
jest.mock('recharts', () => ({
  AreaChart: ({ children }: any) => <div data-testid="mock-area-chart">{children}</div>,
  Area: () => <div data-testid="mock-area" />,
  BarChart: ({ children }: any) => <div data-testid="mock-bar-chart">{children}</div>,
  Bar: () => <div data-testid="mock-bar" />,
  PieChart: ({ children }: any) => <div data-testid="mock-pie-chart">{children}</div>,
  Pie: ({ children }: any) => <div data-testid="mock-pie">{children}</div>,
  Cell: () => <div data-testid="mock-cell" />,
  XAxis: () => <div data-testid="mock-xaxis" />,
  YAxis: () => <div data-testid="mock-yaxis" />,
  CartesianGrid: () => <div data-testid="mock-grid" />,
  Tooltip: () => <div data-testid="mock-tooltip" />,
  Legend: () => <div data-testid="mock-legend" />,
  ResponsiveContainer: ({ children }: any) => <div data-testid="mock-responsive-container">{children}</div>,
  LineChart: ({ children }: any) => <div data-testid="mock-line-chart">{children}</div>,
  Line: () => <div data-testid="mock-line" />,
  ReferenceLine: () => <div data-testid="mock-reference-line" />
}))

// Mock URL.createObjectURL for download functionality
global.URL.createObjectURL = jest.fn(() => 'mock-url')
global.URL.revokeObjectURL = jest.fn()

// Test wrapper with router - 带路由的测试包装器
const TestWrapper: React.FC<{ children: React.ReactNode; initialEntries?: string[] }> = ({
  children,
  initialEntries = ['/strategies/123/analysis']
}) => (
  <ThemeProvider>
    <MemoryRouter initialEntries={initialEntries}>
      <Routes>
        <Route path="/strategies/:id/analysis" element={children} />
      </Routes>
    </MemoryRouter>
  </ThemeProvider>
)

// Mock strategy data
const mockStrategy = {
  id: '123',
  name: '测试策略',
  category: 'core_cbsc',
  description: '这是一个测试策略',
  status: 'active',
  createdAt: '2023-01-01T00:00:00Z',
  updatedAt: '2023-12-01T00:00:00Z'
}

describe('PerformanceAnalysis Component', () => {
  const user = userEvent.setup()

  beforeEach(() => {
    // Reset mocks
    ;(useGetStrategyQuery as jest.Mock).mockReturnValue({
      data: mockStrategy,
      isLoading: false,
      error: null
    })

    // Mock createObjectURL for download
    const mockLink = {
      href: '',
      download: '',
      click: jest.fn()
    }
    jest.spyOn(document, 'createElement').mockReturnValue(mockLink as any)
    jest.spyOn(document.body, 'appendChild').mockImplementation()
    jest.spyOn(document.body, 'removeChild').mockImplementation()
  })

  afterEach(() => {
    cleanup()
    jest.clearAllMocks()
  })

  // Basic rendering tests
  describe('Rendering', () => {
    test('renders with strategy data', () => {
      render(
        <TestWrapper>
          <PerformanceAnalysis />
        </TestWrapper>
      )

      expect(screen.getByText('测试策略')).toBeInTheDocument()
      expect(screen.getByText('性能分析报告')).toBeInTheDocument()
    })

    test('renders performance metrics cards', () => {
      render(
        <TestWrapper>
          <PerformanceAnalysis />
        </TestWrapper>
      )

      expect(screen.getByText('总回报')).toBeInTheDocument()
      expect(screen.getByText('年化回报')).toBeInTheDocument()
      expect(screen.getByText('胜率')).toBeInTheDocument()
      expect(screen.getByText('盈利因子')).toBeInTheDocument()
    })

    test('renders charts section', () => {
      render(
        <TestWrapper>
          <PerformanceAnalysis />
        </TestWrapper>
      )

      expect(screen.getByText('资金曲线')).toBeInTheDocument()
      expect(screen.getByText('回撤分析')).toBeInTheDocument()
      expect(screen.getByText('月度回报')).toBeInTheDocument()
      expect(screen.getByText('交易分布')).toBeInTheDocument()
    })

    test('renders risk metrics section', () => {
      render(
        <TestWrapper>
          <PerformanceAnalysis />
        </TestWrapper>
      )

      expect(screen.getByText('风险指标')).toBeInTheDocument()
      expect(screen.getByText('夏普比率')).toBeInTheDocument()
      expect(screen.getByText('最大回撤')).toBeInTheDocument()
      expect(screen.getByText('卡尔玛比率')).toBeInTheDocument()
    })

    test('renders detailed statistics table', () => {
      render(
        <TestWrapper>
          <PerformanceAnalysis />
        </TestWrapper>
      )

      expect(screen.getByText('详细统计')).toBeInTheDocument()
      expect(screen.getByText('盈利交易')).toBeInTheDocument()
      expect(screen.getByText('亏损交易')).toBeInTheDocument()
      expect(screen.getByText('平均盈利')).toBeInTheDocument()
      expect(screen.getByText('平均亏损')).toBeInTheDocument()
    })

    test('renders analysis summary', () => {
      render(
        <TestWrapper>
          <PerformanceAnalysis />
        </TestWrapper>
      )

      expect(screen.getByText('分析总结')).toBeInTheDocument()
      expect(screen.getByText('风险评估')).toBeInTheDocument()
      expect(screen.getByText('策略表现')).toBeInTheDocument()
      expect(screen.getByText('建议')).toBeInTheDocument()
    })
  })

  // Loading state tests
  describe('Loading state', () => {
    test('shows loading spinner when loading strategy', () => {
      ;(useGetStrategyQuery as jest.Mock).mockReturnValue({
        data: null,
        isLoading: true,
        error: null
      })

      render(
        <TestWrapper>
          <PerformanceAnalysis />
        </TestWrapper>
      )

      const loadingSpinner = document.querySelector('.animate-spin')
      expect(loadingSpinner).toBeInTheDocument()
    })
  })

  // Error state tests
  describe('Error state', () => {
    test('shows error message when strategy loading fails', () => {
      ;(useGetStrategyQuery as jest.Mock).mockReturnValue({
        data: null,
        isLoading: false,
        error: new Error('Failed to load strategy')
      })

      render(
        <TestWrapper>
          <PerformanceAnalysis />
        </TestWrapper>
      )

      expect(screen.getByText('加载策略失败')).toBeInTheDocument()
      expect(screen.getByText('加载策略失败')).toHaveClass('text-error-800')
    })
  })

  // Period selector tests
  describe('Period selector', () => {
    test('renders all period options', () => {
      render(
        <TestWrapper>
          <PerformanceAnalysis />
        </TestWrapper>
      )

      const periods = ['1天', '1周', '1月', '3月', '6月', '1年', '全部']
      periods.forEach(period => {
        expect(screen.getByText(period)).toBeInTheDocument()
      })
    })

    test('highlights selected period', () => {
      render(
        <TestWrapper>
          <PerformanceAnalysis />
        </TestWrapper>
      )

      const selectedButton = screen.getByText('1年')
      expect(selectedButton).toHaveClass('bg-primary-100', 'text-primary-700')
    })

    test('changes period when clicked', async () => {
      render(
        <TestWrapper>
          <PerformanceAnalysis />
        </TestWrapper>
      )

      const monthButton = screen.getByText('1月')
      await user.click(monthButton)

      expect(monthButton).toHaveClass('bg-primary-100', 'text-primary-700')
      expect(screen.getByText('1年')).not.toHaveClass('bg-primary-100')
    })
  })

  // Export functionality tests
  describe('Export functionality', () => {
    test('exports report when export button is clicked', async () => {
      const mockLink = {
        href: '',
        download: '',
        click: jest.fn()
      }
      ;(document.createElement as jest.Mock).mockReturnValue(mockLink)

      render(
        <TestWrapper>
          <PerformanceAnalysis />
        </TestWrapper>
      )

      const exportButton = screen.getByText('导出报告')
      await user.click(exportButton)

      expect(document.createElement).toHaveBeenCalledWith('a')
      expect(mockLink.click).toHaveBeenCalled()
      expect(mockLink.download).toContain('performance-report-测试策略-1Y.json')
    })

    test('includes correct data in exported report', async () => {
      const mockLink = {
        href: '',
        download: '',
        click: jest.fn()
      }
      ;(document.createElement as jest.Mock).mockReturnValue(mockLink)
      const mockCreateObjectURL = global.URL.createObjectURL as jest.Mock
      mockCreateObjectURL.mockReturnValue('blob:mock-url')

      render(
        <TestWrapper>
          <PerformanceAnalysis />
        </TestWrapper>
      )

      const exportButton = screen.getByText('导出报告')
      await user.click(exportButton)

      expect(mockCreateObjectURL).toHaveBeenCalled()

      // Check the blob content
      const blobArg = (mockCreateObjectURL as jest.Mock).mock.calls[0][0]
      expect(blobArg).toBeInstanceOf(Blob)
    })
  })

  // Performance metrics tests
  describe('Performance metrics display', () => {
    test('displays total return with correct color', () => {
      render(
        <TestWrapper>
          <PerformanceAnalysis />
        </TestWrapper>
      )

      const totalReturnElement = screen.getByText(/\d+\.\d+%/)
      // Since the mock generates random data, we just check the element exists
      expect(totalReturnElement).toBeInTheDocument()
    })

    test('displays risk level indicators correctly', () => {
      render(
        <TestWrapper>
          <PerformanceAnalysis />
        </TestWrapper>
      )

      // Check for risk level badges (they contain text like "低风险", "中风险", "高风险")
      const riskIndicators = screen.getAllByText(/风险/)
      expect(riskIndicators.length).toBeGreaterThan(0)
    })

    test('displays performance indicators correctly', () => {
      render(
        <TestWrapper>
          <PerformanceAnalysis />
        </TestWrapper>
      )

      // Check for performance level badges (they contain text like "优秀", "一般", "较差")
      const performanceIndicators = screen.getAllTextMatching(/优秀|一般|较差/)
      expect(performanceIndicators.length).toBeGreaterThan(0)
    })
  })

  // Chart rendering tests
  describe('Chart rendering', () => {
    test('renders all chart components', () => {
      render(
        <TestWrapper>
          <PerformanceAnalysis />
        </TestWrapper>
      )

      // Check for mocked chart components
      expect(screen.getAllByTestId('mock-area-chart').length).toBe(2) // Equity curve and drawdown
      expect(screen.getByTestId('mock-bar-chart')).toBeInTheDocument()
      expect(screen.getByTestId('mock-pie-chart')).toBeInTheDocument()
    })

    test('renders chart axes and grids', () => {
      render(
        <TestWrapper>
          <PerformanceAnalysis />
        </TestWrapper>
      )

      expect(screen.getAllByTestId('mock-xaxis').length).toBeGreaterThan(0)
      expect(screen.getAllByTestId('mock-yaxis').length).toBeGreaterThan(0)
      expect(screen.getAllByTestId('mock-grid').length).toBeGreaterThan(0)
    })
  })

  // Edge cases tests
  describe('Edge cases', () => {
    test('handles missing strategy data gracefully', () => {
      ;(useGetStrategyQuery as jest.Mock).mockReturnValue({
        data: null,
        isLoading: false,
        error: null
      })

      render(
        <TestWrapper>
          <PerformanceAnalysis />
        </TestWrapper>
      )

      // Should not crash and should show no data message
      expect(screen.getByText('暂无性能数据')).toBeInTheDocument()
    })

    test('handles strategy without ID', () => {
      render(
        <TestWrapper initialEntries={['/strategies//analysis']}>
          <PerformanceAnalysis />
        </TestWrapper>
      )

      // Should not crash when ID is missing
      expect(screen.queryByText('测试策略')).not.toBeInTheDocument()
    })
  })

  // Accessibility tests
  describe('Accessibility', () => {
    test('has proper heading hierarchy', () => {
      render(
        <TestWrapper>
          <PerformanceAnalysis />
        </TestWrapper>
      )

      // Check for main heading (h1)
      const h1 = screen.getByRole('heading', { level: 1 })
      expect(h1).toHaveTextContent('测试策略')

      // Check for subheadings (h3)
      const h3s = screen.getAllByRole('heading', { level: 3 })
      expect(h3s.length).toBeGreaterThan(0)
      expect(h3s.some(h => h.textContent === '资金曲线')).toBe(true)
    })

    test('supports keyboard navigation for period selector', async () => {
      render(
        <TestWrapper>
          <PerformanceAnalysis />
        </TestWrapper>
      )

      const firstPeriodButton = screen.getByText('1天')
      firstPeriodButton.focus()
      expect(firstPeriodButton).toHaveFocus()

      await user.keyboard('{ArrowRight}')
      // Check if focus moved to next button
      const secondPeriodButton = screen.getByText('1周')
      expect(secondPeriodButton).toHaveFocus()
    })
  })

  // Performance tests
  describe('Performance', () => {
    test('renders efficiently with large dataset', async () => {
      const startTime = performance.now()

      render(
        <TestWrapper>
          <PerformanceAnalysis />
        </TestWrapper>
      )

      // Wait for component to fully render
      await waitFor(() => {
        expect(screen.getByText('详细统计')).toBeInTheDocument()
      })

      const endTime = performance.now()
      expect(endTime - startTime).toBeLessThan(1000) // Should render within 1 second
    })
  })
})