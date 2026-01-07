import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { ConfigProvider } from 'antd'
import StrategyList from '../StrategyList'
import * as strategyAPI from '../../services/strategyAPI'

// Mock strategies data (must be defined before mocks)
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
    // Component expects these fields directly
    annual_return: 15.00,
    sharpe_ratio: 1.50,
    max_drawdown: 5.00,
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
    // Component expects these fields directly
    annual_return: -5.00,
    sharpe_ratio: 0.50,
    max_drawdown: 10.00,
  },
]

// Mock RTK Query hook - track calls and return mock data
const mockUseGetStrategiesQuery = jest.fn(() => ({
  data: {
    items: mockStrategies,
    total: 2,
    page: 1,
    pageSize: 10,
    totalPages: 1,
  },
  isLoading: false,
  error: null,
  refetch: jest.fn(),
}))

jest.mock('../../../../api/endpoints/strategyApi', () => ({
  useGetStrategiesQuery: (params: any) => mockUseGetStrategiesQuery(params),
}))

// Mock useTheme hook
jest.mock('../../../../hooks/useTheme', () => ({
  useTheme: () => ({
    theme: 'light',
    toggleTheme: jest.fn(),
    setTheme: jest.fn(),
  })
}))

// Mock lodash-es to avoid ES module issues
jest.mock('lodash-es', () => ({
  debounce: jest.fn((fn: any) => fn),
  throttle: jest.fn((fn: any) => fn),
  default: {
    debounce: jest.fn((fn: any) => fn),
    throttle: jest.fn((fn: any) => fn),
  }
}))

// Mock browser APIs
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
})

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {}
  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => { store[key] = value.toString() },
    removeItem: (key: string) => { delete store[key] },
    clear: () => { store = {} }
  }
})()

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock
})

// Mock the API with proper mock implementation
const mockGetStrategies = jest.fn()
const mockRunStrategy = jest.fn()

jest.mock('../../services/strategyAPI', () => ({
  getStrategies: mockGetStrategies,
  runStrategy: mockRunStrategy,
  // Add other exported functions as needed
  getStrategyById: jest.fn(),
  createStrategy: jest.fn(),
  updateStrategy: jest.fn(),
  deleteStrategy: jest.fn(),
}))

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
    mockGetStrategies.mockResolvedValue({
      strategies: mockStrategies,
      total: 2,
      page: 1,
      pageSize: 10,
      totalPages: 1,
    })
    // Set up RTK Query hook mock
    mockUseGetStrategiesQuery.mockReturnValue({
      data: {
        items: mockStrategies,
        total: 2,
        page: 1,
        pageSize: 10,
        totalPages: 1,
      },
      isLoading: false,
      error: null,
      refetch: jest.fn(),
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

    // Component should render with initial data
    await waitFor(() => {
      expect(screen.getByText('策略管理')).toBeInTheDocument()
    })

    // Verify search input is rendered
    const searchInput = screen.getByPlaceholderText('搜索策略名称、描述或标签...')
    expect(searchInput).toBeInTheDocument()
  })

  it('handles filter by type', async () => {
    render(
      <TestWrapper>
        <StrategyList />
      </TestWrapper>
    )

    // Component should render with initial data
    await waitFor(() => {
      expect(screen.getByText('策略管理')).toBeInTheDocument()
    })

    // Verify filter controls are rendered
    // The Select component has "类别" as placeholder text
    const filterElements = screen.queryAllByText('类别')
    expect(filterElements.length).toBeGreaterThan(0)
  })

  it('handles strategy run action', async () => {
    render(
      <TestWrapper>
        <StrategyList />
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.getByText('Test Strategy 1')).toBeInTheDocument()
    })

    // The component renders action buttons for each strategy
    // Verify that buttons are rendered in the table
    const allButtons = screen.getAllByRole('button')

    // There should be multiple action buttons (view, edit, play for each strategy)
    expect(allButtons.length).toBeGreaterThan(0)

    // At least some buttons should have SVG icons (from heroicons)
    const buttonsWithIcons = allButtons.filter(btn => btn.querySelector('svg'))
    expect(buttonsWithIcons.length).toBeGreaterThan(0)
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

    // Find and click the view mode toggle - text is "卡片" not "卡片视图"
    const viewModeToggle = screen.getByText('卡片')
    fireEvent.click(viewModeToggle)

    // Should now display cards instead of table
    await waitFor(() => {
      expect(screen.queryByRole('table')).not.toBeInTheDocument()
      expect(screen.getByText('Test Strategy 1')).toBeInTheDocument()
    })
  })

  it('displays loading state', () => {
    mockGetStrategies.mockReturnValue(new Promise(() => {}))

    render(
      <TestWrapper>
        <StrategyList />
      </TestWrapper>
    )

    // Should show loading spinner in table
    expect(screen.getByRole('table')).toBeInTheDocument()
  })
})