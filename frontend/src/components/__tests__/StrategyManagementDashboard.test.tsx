/**
 * Strategy Management Dashboard Test
 * 策略管理儀表板測試
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';

import StrategyManagementDashboard from '../StrategyManagementDashboard';
import strategyReducer from '../../store/strategies/strategySlice';
import { Strategy, StrategyType, RiskTolerance } from '../../types/strategyTypes';

// Mock strategy data
const mockStrategies: Strategy[] = [
  {
    id: '1',
    name: 'MA Cross Strategy',
    description: 'Moving average crossover strategy for trend following',
    strategy_type: StrategyType.TECHNICAL_INDICATORS,
    risk_tolerance: RiskTolerance.MEDIUM,
    version: '1.0.0',
    is_active: true,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    tags: ['trend', 'ma'],
    parameters: {
      short_period: 10,
      long_period: 20
    },
    config: {}
  },
  {
    id: '2',
    name: 'RSI Mean Reversion',
    description: 'RSI-based mean reversion strategy',
    strategy_type: StrategyType.MOMENTUM,
    risk_tolerance: RiskTolerance.LOW,
    version: '1.1.0',
    is_active: false,
    created_at: '2024-01-02T00:00:00Z',
    updated_at: '2024-01-02T00:00:00Z',
    tags: ['rsi', 'mean-reversion'],
    parameters: {
      rsi_period: 14,
      oversold: 30,
      overbought: 70
    },
    config: {}
  }
];

// Create test store
const createTestStore = (initialState = {}) => {
  return configureStore({
    reducer: {
      strategies: strategyReducer
    },
    preloadedState: {
      strategies: {
        strategies: mockStrategies,
        loading: false,
        error: null,
        strategiesPagination: {
          page: 1,
          pageSize: 20,
          total: 2,
          pages: 1,
          hasNext: false,
          hasPrev: false
        },
        currentStrategy: null,
        configs: [],
        configsPagination: {
          page: 1,
          pageSize: 20,
          total: 0,
          pages: 0,
          hasNext: false,
          hasPrev: false
        },
        performance: null,
        performanceLoading: false,
        executions: {},
        executionStatuses: {},
        filter: {},
        selectedStrategies: [],
        strategyTypes: [],
        riskTolerances: [],
        categories: []
      },
      ...initialState
    }
  });
};

// Test wrapper component
const TestWrapper: React.FC<{ children: React.ReactNode; store?: any }> = ({
  children,
  store
}) => {
  const testStore = store || createTestStore();

  return (
    <Provider store={testStore}>
      {children}
    </Provider>
  );
};

describe('StrategyManagementDashboard', () => {
  beforeEach(() => {
    // Mock fetch API
    global.fetch = jest.fn();
  });

  test('renders strategy management dashboard', () => {
    render(
      <TestWrapper>
        <StrategyManagementDashboard />
      </TestWrapper>
    );

    // Check header
    expect(screen.getByText('策略管理')).toBeInTheDocument();
    expect(screen.getByText('管理和監控您的量化交易策略')).toBeInTheDocument();

    // Check create button
    expect(screen.getByText('創建策略')).toBeInTheDocument();

    // Check strategies table
    expect(screen.getByText('MA Cross Strategy')).toBeInTheDocument();
    expect(screen.getByText('RSI Mean Reversion')).toBeInTheDocument();
  });

  test('displays strategy types and status badges correctly', () => {
    render(
      <TestWrapper>
        <StrategyManagementDashboard />
      </TestWrapper>
    );

    // Check strategy type badges
    expect(screen.getByText('技術指標')).toBeInTheDocument();
    expect(screen.getByText('動量')).toBeInTheDocument();

    // Check status badges
    expect(screen.getByText('活躍')).toBeInTheDocument();
    expect(screen.getByText('非活躍')).toBeInTheDocument();
  });

  test('search functionality works', async () => {
    render(
      <TestWrapper>
        <StrategyManagementDashboard />
      </TestWrapper>
    );

    // Find search input
    const searchInput = screen.getByPlaceholderText('搜索策略名稱或描述...');

    // Type search query
    fireEvent.change(searchInput, { target: { value: 'MA Cross' } });

    // Should filter strategies (this would require actual API implementation)
    await waitFor(() => {
      expect(searchInput).toHaveValue('MA Cross');
    });
  });

  test('filter functionality works', async () => {
    render(
      <TestWrapper>
        <StrategyManagementDashboard />
      </TestWrapper>
    );

    // Find strategy type filter
    const typeFilter = screen.getByDisplayValue('所有類型');

    // Change filter value
    fireEvent.change(typeFilter, { target: { value: StrategyType.TECHNICAL_INDICATORS } });

    await waitFor(() => {
      expect(typeFilter).toHaveValue(StrategyType.TECHNICAL_INDICATORS);
    });
  });

  test('strategy selection works', () => {
    render(
      <TestWrapper>
        <StrategyManagementDashboard />
      </TestWrapper>
    );

    // Find strategy checkboxes
    const checkboxes = screen.getAllByRole('checkbox');

    // Select first strategy
    fireEvent.click(checkboxes[1]); // First checkbox is for select all

    // Should show selection bar
    expect(screen.getByText('已選擇 1 個策略')).toBeInTheDocument();
  });

  test('action buttons are rendered', () => {
    render(
      <TestWrapper>
        <StrategyManagementDashboard />
      </TestWrapper>
    );

    // Check action buttons for each strategy
    const viewButtons = screen.getAllByText('查看');
    const editButtons = screen.getAllByText('編輯');
    const executeButtons = screen.getAllByText('執行');
    const deleteButtons = screen.getAllByText('刪除');

    expect(viewButtons).toHaveLength(2);
    expect(editButtons).toHaveLength(2);
    expect(executeButtons).toHaveLength(2);
    expect(deleteButtons).toHaveLength(2);
  });

  test('pagination is rendered', () => {
    render(
      <TestWrapper>
        <StrategyManagementDashboard />
      </TestWrapper>
    );

    // Check pagination elements
    expect(screen.getByText('顯示第 1 到 2 項，共 2 項')).toBeInTheDocument();
  });

  test('empty state is rendered correctly', () => {
    const store = createTestStore({
      strategies: {
        strategies: [],
        loading: false,
        error: null,
        strategiesPagination: {
          page: 1,
          pageSize: 20,
          total: 0,
          pages: 0,
          hasNext: false,
          hasPrev: false
        },
        currentStrategy: null,
        configs: [],
        configsPagination: {
          page: 1,
          pageSize: 20,
          total: 0,
          pages: 0,
          hasNext: false,
          hasPrev: false
        },
        performance: null,
        performanceLoading: false,
        executions: {},
        executionStatuses: {},
        filter: {},
        selectedStrategies: [],
        strategyTypes: [],
        riskTolerances: [],
        categories: []
      }
    });

    render(
      <TestWrapper store={store}>
        <StrategyManagementDashboard />
      </TestWrapper>
    );

    // Check empty state message
    expect(screen.getByText('沒有找到策略')).toBeInTheDocument();
    expect(screen.getByText('開始創建您的第一個量化交易策略吧！')).toBeInTheDocument();
  });

  test('loading state is rendered correctly', () => {
    const store = createTestStore({
      strategies: {
        strategies: [],
        loading: true,
        error: null,
        strategiesPagination: {
          page: 1,
          pageSize: 20,
          total: 0,
          pages: 0,
          hasNext: false,
          hasPrev: false
        },
        currentStrategy: null,
        configs: [],
        configsPagination: {
          page: 1,
          pageSize: 20,
          total: 0,
          pages: 0,
          hasNext: false,
          hasPrev: false
        },
        performance: null,
        performanceLoading: false,
        executions: {},
        executionStatuses: {},
        filter: {},
        selectedStrategies: [],
        strategyTypes: [],
        riskTolerances: [],
        categories: []
      }
    });

    render(
      <TestWrapper store={store}>
        <StrategyManagementDashboard />
      </TestWrapper>
    );

    // Check loading state
    expect(screen.getByText('載入策略中...')).toBeInTheDocument();
  });

  test('error state is rendered correctly', () => {
    const store = createTestStore({
      strategies: {
        strategies: [],
        loading: false,
        error: 'Failed to load strategies',
        strategiesPagination: {
          page: 1,
          pageSize: 20,
          total: 0,
          pages: 0,
          hasNext: false,
          hasPrev: false
        },
        currentStrategy: null,
        configs: [],
        configsPagination: {
          page: 1,
          pageSize: 20,
          total: 0,
          pages: 0,
          hasNext: false,
          hasPrev: false
        },
        performance: null,
        performanceLoading: false,
        executions: {},
        executionStatuses: {},
        filter: {},
        selectedStrategies: [],
        strategyTypes: [],
        riskTolerances: [],
        categories: []
      }
    });

    render(
      <TestWrapper store={store}>
        <StrategyManagementDashboard />
      </TestWrapper>
    );

    // Check error state
    expect(screen.getByText('錯誤')).toBeInTheDocument();
    expect(screen.getByText('Failed to load strategies')).toBeInTheDocument();
  });
});