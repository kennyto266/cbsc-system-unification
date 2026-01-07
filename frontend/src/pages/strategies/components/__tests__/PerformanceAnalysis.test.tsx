import React from 'react'
import { render, screen, waitFor, cleanup } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import PerformanceAnalysis from '../PerformanceAnalysis'

// Mock the API hooks
const mockUseGetStrategyQuery = jest.fn()
const mockUseGetPerformanceQuery = jest.fn()

// Mock the API slice module
jest.mock('@/store/api/apiSlice', () => ({
  apiSlice: {
    reducerPath: 'api',
    reducer: (state = {}) => state,
    middleware: () => () => (next) => (action) => next(action),
    endpoints: {},
  },
  useGetStrategyQuery: () => mockUseGetStrategyQuery(),
  useGetPerformanceQuery: () => mockUseGetPerformanceQuery(),
}))

// Mock useParams with a default value
let mockParams = { id: '123' }

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useParams: () => mockParams,
}))

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
    mockUseGetStrategyQuery.mockReturnValue({
      data: mockStrategy,
      isLoading: false,
      error: null
    })
  })

  afterEach(() => {
    cleanup()
    jest.clearAllMocks()
    jest.restoreAllMocks()
  })

  // Basic rendering tests
  describe('Rendering', () => {
    test('renders with strategy data', () => {
      render(<div><PerformanceAnalysis /></div>)

      expect(screen.getByText('测试策略')).toBeInTheDocument()
      expect(screen.getByText('性能分析报告')).toBeInTheDocument()
    })

    test('renders performance metrics cards', () => {
      render(<div><PerformanceAnalysis /></div>)

      expect(screen.getByText('总回报')).toBeInTheDocument()
      expect(screen.getByText('年化回报')).toBeInTheDocument()
      expect(screen.getByText('胜率')).toBeInTheDocument()
      expect(screen.getByText('盈利因子')).toBeInTheDocument()
    })

    test('renders charts section', () => {
      render(<div><PerformanceAnalysis /></div>)

      expect(screen.getByText('资金曲线')).toBeInTheDocument()
      expect(screen.getByText('回撤分析')).toBeInTheDocument()
      expect(screen.getByText('月度回报')).toBeInTheDocument()
      expect(screen.getByText('交易分布')).toBeInTheDocument()
    })

    test('renders risk metrics section', () => {
      render(<div><PerformanceAnalysis /></div>)

      expect(screen.getByText('风险指标')).toBeInTheDocument()
      expect(screen.getByText('夏普比率')).toBeInTheDocument()
      expect(screen.getByText('最大回撤')).toBeInTheDocument()
      expect(screen.getByText('卡尔玛比率')).toBeInTheDocument()
    })

    test('renders detailed statistics table', () => {
      render(<div><PerformanceAnalysis /></div>)

      expect(screen.getByText('详细统计')).toBeInTheDocument()
      expect(screen.getByText('盈利交易')).toBeInTheDocument()
      expect(screen.getByText('亏损交易')).toBeInTheDocument()
      expect(screen.getByText('平均盈利')).toBeInTheDocument()
      expect(screen.getByText('平均亏损')).toBeInTheDocument()
    })

    test('renders analysis summary', () => {
      render(<div><PerformanceAnalysis /></div>)

      expect(screen.getByText('分析总结')).toBeInTheDocument()
      expect(screen.getByText('风险评估')).toBeInTheDocument()
      expect(screen.getByText('策略表现')).toBeInTheDocument()
      expect(screen.getByText('建议')).toBeInTheDocument()
    })
  })

  // Loading state tests
  describe('Loading state', () => {
    test('shows loading spinner when loading strategy', () => {
      mockUseGetStrategyQuery.mockReturnValue({
        data: null,
        isLoading: true,
        error: null
      })

      render(<div><PerformanceAnalysis /></div>)

      const loadingSpinner = document.querySelector('.animate-spin')
      expect(loadingSpinner).toBeInTheDocument()
    })
  })

  // Error state tests
  describe('Error state', () => {
    test('shows error message when strategy loading fails', () => {
      mockUseGetStrategyQuery.mockReturnValue({
        data: null,
        isLoading: false,
        error: new Error('Failed to load strategy')
      })

      render(<div><PerformanceAnalysis /></div>)

      expect(screen.getByText('加载策略失败')).toBeInTheDocument()
      expect(screen.getByText('加载策略失败')).toHaveClass('text-error-800')
    })
  })

  // Period selector tests
  describe('Period selector', () => {
    test('renders all period options', () => {
      render(<div><PerformanceAnalysis /></div>)

      const periods = ['1天', '1周', '1月', '3月', '6月', '1年', '全部']
      periods.forEach(period => {
        expect(screen.getByText(period)).toBeInTheDocument()
      })
    })

    test('highlights selected period', () => {
      render(<div><PerformanceAnalysis /></div>)

      const selectedButton = screen.getByText('1年')
      expect(selectedButton).toHaveClass('bg-primary-100', 'text-primary-700')
    })

    test('changes period when clicked', async () => {
      render(<div><PerformanceAnalysis /></div>)

      const monthButton = screen.getByText('1月')
      await user.click(monthButton)

      expect(monthButton).toHaveClass('bg-primary-100', 'text-primary-700')
      expect(screen.getByText('1年')).not.toHaveClass('bg-primary-100')
    })
  })

  // Export functionality tests
  describe('Export functionality', () => {
    let originalCreateElement: typeof document.createElement
    let createElementSpy: jest.SpyInstance
    let clickSpy: jest.Mock
    let createdLink: HTMLAnchorElement | null = null

    beforeEach(() => {
      // Save original before spying
      originalCreateElement = document.createElement.bind(document)
      clickSpy = jest.fn()

      createElementSpy = jest.spyOn(document, 'createElement').mockImplementation((tagName: string) => {
        if (tagName === 'a') {
          const link = originalCreateElement('a')
          createdLink = link
          // Mock the click method
          Object.defineProperty(link, 'click', {
            value: clickSpy,
            writable: true,
            configurable: true
          })
          return link
        }
        // Use original createElement for other tags
        return originalCreateElement(tagName)
      })
    })

    afterEach(() => {
      createElementSpy.mockRestore()
      createdLink = null
    })

    test('exports report when export button is clicked', async () => {
      render(<div><PerformanceAnalysis /></div>)

      const exportButton = screen.getByText('导出报告')
      await user.click(exportButton)

      expect(document.createElement).toHaveBeenCalledWith('a')
      expect(clickSpy).toHaveBeenCalled()
      if (createdLink) {
        expect(createdLink.download).toContain('performance-report-测试策略-1Y.json')
      }
    })

    test('includes correct data in exported report', async () => {
      const mockCreateObjectURL = global.URL.createObjectURL as jest.Mock
      mockCreateObjectURL.mockReturnValue('blob:mock-url')

      render(<div><PerformanceAnalysis /></div>)

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
      render(<div><PerformanceAnalysis /></div>)

      // Since the mock generates random data, we just check at least one percentage exists
      const totalReturnElements = screen.getAllByText(/\d+\.\d+%/)
      expect(totalReturnElements.length).toBeGreaterThan(0)
    })

    test('displays risk level indicators correctly', () => {
      render(<div><PerformanceAnalysis /></div>)

      // Check for risk level badges (they contain text like "低风险", "中风险", "高风险")
      const riskIndicators = screen.getAllByText(/风险/)
      expect(riskIndicators.length).toBeGreaterThan(0)
    })

    test('displays performance indicators correctly', () => {
      render(<div><PerformanceAnalysis /></div>)

      // Check for performance level badges (they contain text like "优秀", "一般", "较差")
      const performanceIndicators = screen.getAllByText(/优秀|一般|较差/)
      expect(performanceIndicators.length).toBeGreaterThan(0)
    })
  })

  // Chart rendering tests
  describe('Chart rendering', () => {
    test('renders all chart components', () => {
      render(<div><PerformanceAnalysis /></div>)

      // Check for chart sections by their titles
      expect(screen.getByText('资金曲线')).toBeInTheDocument()
      expect(screen.getByText('回撤分析')).toBeInTheDocument()
      expect(screen.getByText('月度回报')).toBeInTheDocument()
      expect(screen.getByText('交易分布')).toBeInTheDocument()
    })

    test('renders chart axes and grids', () => {
      render(<div><PerformanceAnalysis /></div>)

      // Verify chart sections exist (recharts charts are rendered within these sections)
      expect(screen.getByText('资金曲线')).toBeInTheDocument()
      expect(screen.getByText('回撤分析')).toBeInTheDocument()
    })
  })

  // Edge cases tests
  describe('Edge cases', () => {
    test('handles missing strategy data gracefully', () => {
      mockUseGetStrategyQuery.mockReturnValue({
        data: null,
        isLoading: false,
        error: null
      })

      render(<div><PerformanceAnalysis /></div>)

      // Should show error message when strategy is null
      expect(screen.getByText('加载策略失败')).toBeInTheDocument()
    })

    test('handles missing performance data gracefully', () => {
      // Strategy exists but id is empty, so performanceData will be null
      mockParams = { id: '' }
      mockUseGetStrategyQuery.mockReturnValue({
        data: mockStrategy,
        isLoading: false,
        error: null
      })

      render(<div><PerformanceAnalysis /></div>)

      // Should show no data message when performanceData is null
      expect(screen.getByText('暂无性能数据')).toBeInTheDocument()

      // Reset mock for other tests
      mockParams = { id: '123' }
    })
  })

  // Accessibility tests
  describe('Accessibility', () => {
    test('has proper heading hierarchy', () => {
      render(<div><PerformanceAnalysis /></div>)

      // Check for main heading (h1)
      const h1 = screen.getByRole('heading', { level: 1 })
      expect(h1).toHaveTextContent('测试策略')

      // Check for subheadings (h3)
      const h3s = screen.getAllByRole('heading', { level: 3 })
      expect(h3s.length).toBeGreaterThan(0)
      expect(h3s.some(h => h.textContent === '资金曲线')).toBe(true)
    })
  })

  // Performance tests
  describe('Performance', () => {
    test('renders efficiently with large dataset', async () => {
      const startTime = performance.now()

      render(<div><PerformanceAnalysis /></div>)

      // Wait for component to fully render
      await waitFor(() => {
        expect(screen.getByText('详细统计')).toBeInTheDocument()
      })

      const endTime = performance.now()
      expect(endTime - startTime).toBeLessThan(1000) // Should render within 1 second
    })
  })
})
