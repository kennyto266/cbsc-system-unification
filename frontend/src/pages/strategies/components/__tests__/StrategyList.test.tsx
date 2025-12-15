import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { ConfigProvider } from 'antd'
import StrategyList from '../StrategyList'
import * as strategyAPI from '../../services/strategyAPI'

// Mock the API
jest.mock('../../services/strategyAPI')
const mockStrategyAPI = strategyAPI as jest.Mocked<typeof strategyAPI>

// Mock strategies data
const mockStrategies = [
  {
    id: '1',
    name: 'Test Strategy 1',
    description: 'Test description 1',
    type: 'momentum' as const,
    status: 'active' as const,
    createdBy: 'test user',
    createdAt: '2024-01-01',
    updatedAt: '2024-01-01',
    parameters: {},
    performance: {
      totalReturn: 0.15,
      sharpeRatio: 1.5,
      maxDrawdown: 0.05,
      winRate: 0.6,
    },
  },
  {
    id: '2',
    name: 'Test Strategy 2',
    description: 'Test description 2',
    type: 'mean_reversion' as const,
    status: 'paused' as const,
    createdBy: 'test user',
    createdAt: '2024-01-02',
    updatedAt: '2024-01-02',
    parameters: {},
    performance: {
      totalReturn: -0.05,
      sharpeRatio: 0.5,
      maxDrawdown: 0.1,
      winRate: 0.4,
    },
  },
]

// Wrapper component for testing
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <BrowserRouter>
    <ConfigProvider>
      {children}
    </ConfigProvider>
  </BrowserRouter>
)

describe('StrategyList Component', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockStrategyAPI.getStrategies.mockResolvedValue({
      strategies: mockStrategies,
      total: 2,
      page: 1,
      pageSize: 10,
      totalPages: 1,
    })
  })

  it('renders strategy list correctly', async () => {
    render(
      <TestWrapper>
        <StrategyList />
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.getByText('策略管理')).toBeInTheDocument()
      expect(screen.getByText('Test Strategy 1')).toBeInTheDocument()
      expect(screen.getByText('Test Strategy 2')).toBeInTheDocument()
    })
  })

  it('displays strategy performance metrics', async () => {
    render(
      <TestWrapper>
        <StrategyList />
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.getByText('15.00%')).toBeInTheDocument() // Total return for strategy 1
      expect(screen.getByText('-5.00%')).toBeInTheDocument() // Total return for strategy 2
      expect(screen.getByText('1.50')).toBeInTheDocument() // Sharpe ratio for strategy 1
      expect(screen.getByText('0.50')).toBeInTheDocument() // Sharpe ratio for strategy 2
    })
  })

  it('handles search functionality', async () => {
    render(
      <TestWrapper>
        <StrategyList />
      </TestWrapper>
    )

    await waitFor(() => {
      expect(mockStrategyAPI.getStrategies).toHaveBeenCalledWith({})
    })

    const searchInput = screen.getByPlaceholderText('搜索策略名称...')
    fireEvent.change(searchInput, { target: { value: 'Test Strategy 1' } })

    await waitFor(() => {
      expect(mockStrategyAPI.getStrategies).toHaveBeenCalledWith({
        search: 'Test Strategy 1',
        page: 1,
        pageSize: 10,
      })
    })
  })

  it('handles filter by type', async () => {
    render(
      <TestWrapper>
        <StrategyList />
      </TestWrapper>
    )

    await waitFor(() => {
      expect(mockStrategyAPI.getStrategies).toHaveBeenCalledWith({})
    })

    // Find and click the type filter dropdown
    const typeSelect = screen.getByText('策略类型')
    fireEvent.click(typeSelect)

    // Select 'momentum' option
    const momentumOption = screen.getByText('动量')
    fireEvent.click(momentumOption)

    await waitFor(() => {
      expect(mockStrategyAPI.getStrategies).toHaveBeenCalledWith({
        type: 'momentum',
        page: 1,
        pageSize: 10,
      })
    })
  })

  it('handles strategy run action', async () => {
    mockStrategyAPI.runStrategy.mockResolvedValue({
      runId: 'test-run-id',
      status: 'running',
      startTime: new Date().toISOString(),
    })

    render(
      <TestWrapper>
        <StrategyList />
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.getByText('Test Strategy 1')).toBeInTheDocument()
    })

    // Find the more options button for the first strategy
    const moreButtons = screen.getAllByTestId('more-options')
    fireEvent.click(moreButtons[0])

    // Click the run option
    const runOption = screen.getByText('启动')
    fireEvent.click(runOption)

    await waitFor(() => {
      expect(mockStrategyAPI.runStrategy).toHaveBeenCalledWith({
        strategyId: '1',
      })
    })
  })

  it('handles view mode toggle', async () => {
    render(
      <TestWrapper>
        <StrategyList />
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.getByRole('table')).toBeInTheDocument()
    })

    // Find and click the view mode toggle
    const viewModeToggle = screen.getByText('卡片视图')
    fireEvent.click(viewModeToggle)

    // Should now display cards instead of table
    await waitFor(() => {
      expect(screen.queryByRole('table')).not.toBeInTheDocument()
      expect(screen.getByText('Test Strategy 1')).toBeInTheDocument()
    })
  })

  it('displays loading state', () => {
    mockStrategyAPI.getStrategies.mockReturnValue(new Promise(() => {}))

    render(
      <TestWrapper>
        <StrategyList />
      </TestWrapper>
    )

    // Should show loading spinner in table
    expect(screen.getByRole('table')).toBeInTheDocument()
  })
})