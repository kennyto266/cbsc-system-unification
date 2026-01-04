import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ToastContainer } from 'react-toastify';
import StrategyControlDashboard from '../StrategyControlDashboard';
import { StrategyData, StrategyStatus } from '../StrategyToggleEnhanced';

// Mock window.confirm
global.confirm = jest.fn(() => true);

// Mock the strategy control adapter
jest.mock('../../../services/strategyControlAdapter', () => ({
  strategyControlAdapter: {
    getAllStrategies: jest.fn(() => Promise.resolve({
      success: true,
      data: []
    })),
    toggleStrategy: jest.fn(() => Promise.resolve({
      success: true,
      data: { success: true }
    })),
    batchControlStrategies: jest.fn(() => Promise.resolve({
      success: true,
      results: []
    })),
  },
}));

// Mock react-toastify
jest.mock('react-toastify', () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
    warning: jest.fn(),
  },
  ToastContainer: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

// Mock @headlessui/react Switch
jest.mock('@headlessui/react', () => ({
  Switch: ({
    checked,
    onChange,
    disabled,
    children,
    ...props
  }: any) => (
    <button
      {...props}
      role="switch"
      aria-checked={checked}
      disabled={disabled}
      onClick={() => onChange(!checked)}
    >
      {children}
    </button>
  ),
}));

const mockStrategies: StrategyData[] = [
  {
    id: 'direct_rsi',
    name: '直接RSI情绪策略',
    isActive: false,
    status: 'inactive' as StrategyStatus,
    performance: {
      sharpeRatio: 1.85,
      maxDrawdown: 0.12,
      totalReturn: 0.35,
      winRate: 0.65,
    },
  },
  {
    id: 'sentiment_momentum',
    name: '情绪动量策略',
    isActive: true,
    status: 'active' as StrategyStatus,
    performance: {
      sharpeRatio: 2.12,
      maxDrawdown: 0.08,
      totalReturn: 0.42,
      winRate: 0.71,
    },
  },
  {
    id: 'composite_index',
    name: '综合指数策略',
    isActive: false,
    status: 'inactive' as StrategyStatus,
    performance: {
      sharpeRatio: 1.65,
      maxDrawdown: 0.15,
      totalReturn: 0.28,
      winRate: 0.58,
    },
  },
  {
    id: 'volatility_adjusted',
    name: '波动率调整策略',
    isActive: true,
    status: 'paused' as StrategyStatus,
    performance: {
      sharpeRatio: 1.93,
      maxDrawdown: 0.10,
      totalReturn: 0.38,
      winRate: 0.67,
    },
  },
];

describe('StrategyControlDashboard Integration', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  const renderDashboard = (props = {}) => {
    const defaultProps = {
      strategies: mockStrategies,
    };

    return render(
      <>
        <ToastContainer />
        <StrategyControlDashboard {...defaultProps} {...props} />
      </>
    );
  };

  it('renders dashboard with all components', async () => {
    const { strategyControlAdapter } = require('../../../services/strategyControlAdapter');
    strategyControlAdapter.getAllStrategies.mockResolvedValue({
      success: true,
      data: mockStrategies,
    });

    renderDashboard();

    // Check header
    expect(screen.getByText('策略控制中心')).toBeInTheDocument();
    expect(screen.getByText('管理和控制您的交易策略')).toBeInTheDocument();

    // Check status summary
    await waitFor(() => {
      expect(screen.getByText('4')).toBeInTheDocument(); // Total
      expect(screen.getByText('1')).toBeInTheDocument(); // Active
      expect(screen.getByText('2')).toBeInTheDocument(); // Inactive
      expect(screen.getByText('1')).toBeInTheDocument(); // Paused
    });

    // Check strategy list
    expect(screen.getByText('直接RSI情绪策略')).toBeInTheDocument();
    expect(screen.getByText('情绪动量策略')).toBeInTheDocument();

    // Check batch operations panel
    expect(screen.getByText('批量操作')).toBeInTheDocument();
    expect(screen.getByText('操作历史')).toBeInTheDocument();
  });

  it('loads strategies on mount', async () => {
    const { strategyControlAdapter } = require('../../../services/strategyControlAdapter');
    strategyControlAdapter.getAllStrategies.mockResolvedValue({
      success: true,
      data: mockStrategies,
    });

    const onStrategyUpdate = jest.fn();
    renderDashboard({ onStrategyUpdate });

    await waitFor(() => {
      expect(strategyControlAdapter.getAllStrategies).toHaveBeenCalled();
    });

    await waitFor(() => {
      expect(onStrategyUpdate).toHaveBeenCalledWith(mockStrategies);
    });
  });

  it('handles strategy toggle in the dashboard', async () => {
    const { strategyControlAdapter } = require('../../../services/strategyControlAdapter');
    strategyControlAdapter.getAllStrategies.mockResolvedValue({
      success: true,
      data: mockStrategies,
    });
    strategyControlAdapter.toggleStrategy.mockResolvedValue({
      success: true,
      data: { success: true },
    });

    const onStrategyUpdate = jest.fn();
    renderDashboard({ onStrategyUpdate });

    await waitFor(() => {
      expect(screen.getByText('直接RSI情绪策略')).toBeInTheDocument();
    });

    // Find the toggle for the first strategy
    const toggles = screen.getAllByRole('switch');
    expect(toggles.length).toBeGreaterThan(0);

    const firstToggle = toggles.find(toggle =>
      toggle.closest('[data-testid*="direct_rsi"]')
    ) || toggles[0];

    // Click the toggle to enable the strategy
    fireEvent.click(firstToggle);

    await waitFor(() => {
      expect(strategyControlAdapter.toggleStrategy).toHaveBeenCalledWith(
        'direct_rsi',
        true
      );
    });

    await waitFor(() => {
      expect(onStrategyUpdate).toHaveBeenCalled();
    });

    // Check if operation was added to history
    await waitFor(() => {
      expect(screen.getByText('启用')).toBeInTheDocument();
      expect(screen.getByText('直接RSI情绪策略')).toBeInTheDocument();
    });
  });

  it('handles search functionality', async () => {
    const { strategyControlAdapter } = require('../../../services/strategyControlAdapter');
    strategyControlAdapter.getAllStrategies.mockResolvedValue({
      success: true,
      data: mockStrategies,
    });

    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText('直接RSI情绪策略')).toBeInTheDocument();
      expect(screen.getByText('情绪动量策略')).toBeInTheDocument();
    });

    // Search for "RSI"
    const searchInput = screen.getByPlaceholderText('搜索策略...');
    fireEvent.change(searchInput, { target: { value: 'RSI' } });

    // Should only show RSI strategy
    await waitFor(() => {
      expect(screen.getByText('直接RSI情绪策略')).toBeInTheDocument();
      expect(screen.queryByText('情绪动量策略')).not.toBeInTheDocument();
    });
  });

  it('handles status filter', async () => {
    const { strategyControlAdapter } = require('../../../services/strategyControlAdapter');
    strategyControlAdapter.getAllStrategies.mockResolvedValue({
      success: true,
      data: mockStrategies,
    });

    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText('策略列表 (4)')).toBeInTheDocument();
    });

    // Filter by active status
    const activeButton = screen.getByText('运行中');
    fireEvent.click(activeButton);

    // Should only show active strategies
    await waitFor(() => {
      expect(screen.getByText('情绪动量策略')).toBeInTheDocument();
      expect(screen.queryByText('直接RSI情绪策略')).not.toBeInTheDocument();
      expect(screen.queryByText('综合指数策略')).not.toBeInTheDocument();
      expect(screen.queryByText('波动率调整策略')).not.toBeInTheDocument();
    });
  });

  it('handles view mode toggle', async () => {
    const { strategyControlAdapter } = require('../../../services/strategyControlAdapter');
    strategyControlAdapter.getAllStrategies.mockResolvedValue({
      success: true,
      data: mockStrategies,
    });

    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText('策略列表 (4)')).toBeInTheDocument();
    });

    // Check grid view is default
    const strategyContainer = screen.getByText('策略列表 (4)').closest('div')?.parentElement;
    expect(strategyContainer).toHaveClass('md:grid-cols-2');

    // Switch to list view
    const listButton = screen.getByText('列表');
    fireEvent.click(listButton);

    // Should switch to list layout
    expect(strategyContainer).not.toHaveClass('md:grid-cols-2');
  });

  it('handles batch operation', async () => {
    const { strategyControlAdapter } = require('../../../services/strategyControlAdapter');
    strategyControlAdapter.getAllStrategies.mockResolvedValue({
      success: true,
      data: mockStrategies,
    });
    strategyControlAdapter.batchControlStrategies.mockResolvedValue({
      success: true,
      results: [
        { strategyId: 'direct_rsi', success: true },
        { strategyId: 'composite_index', success: true },
      ],
    });

    // Mock window.confirm
    const originalConfirm = window.confirm;
    window.confirm = jest.fn(() => true);

    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText('批量操作')).toBeInTheDocument();
    });

    // Select strategies for batch operation
    const checkboxes = screen.getAllByRole('checkbox');
    fireEvent.click(checkboxes[0]); // Select first strategy
    fireEvent.click(checkboxes[2]); // Select third strategy

    // Perform batch enable
    const batchEnableButton = screen.getByText('批量启用');
    fireEvent.click(batchEnableButton);

    await waitFor(() => {
      expect(strategyControlAdapter.batchControlStrategies).toHaveBeenCalledWith(
        ['direct_rsi', 'composite_index'],
        'enable'
      );
    });

    // Restore original confirm
    window.confirm = originalConfirm;
  });

  it('shows loading state', async () => {
    const { strategyControlAdapter } = require('../../../services/strategyControlAdapter');
    strategyControlAdapter.getAllStrategies.mockImplementation(
      () => new Promise(resolve => setTimeout(() => resolve({ success: true, data: mockStrategies }), 100))
    );

    renderDashboard();

    // Check for loading spinner
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('handles empty strategy list', async () => {
    const { strategyControlAdapter } = require('../../../services/strategyControlAdapter');
    strategyControlAdapter.getAllStrategies.mockResolvedValue({
      success: true,
      data: [],
    });

    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText('策略列表 (0)')).toBeInTheDocument();
      expect(screen.getByText('暂无策略')).toBeInTheDocument();
    });
  });

  it('handles API error', async () => {
    const { strategyControlAdapter } = require('../../../services/strategyControlAdapter');
    const { toast } = require('react-toastify');

    strategyControlAdapter.getAllStrategies.mockResolvedValue({
      success: false,
      error: 'Failed to load strategies',
    });

    renderDashboard();

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith(
        '加载策略失败: Failed to load strategies',
        expect.any(Object)
      );
    });
  });

  it('shows operation history', async () => {
    const { strategyControlAdapter } = require('../../../services/strategyControlAdapter');
    strategyControlAdapter.getAllStrategies.mockResolvedValue({
      success: true,
      data: mockStrategies,
    });
    strategyControlAdapter.toggleStrategy.mockResolvedValue({
      success: true,
      data: { success: true },
    });

    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText('操作历史')).toBeInTheDocument();
    });

    // Toggle a strategy to add to history
    const toggles = screen.getAllByRole('switch');
    fireEvent.click(toggles[0]);

    await waitFor(() => {
      expect(screen.getByText('启用')).toBeInTheDocument();
    });
  });

  it('switches between grid and list view modes', async () => {
    const { strategyControlAdapter } = require('../../../services/strategyControlAdapter');
    strategyControlAdapter.getAllStrategies.mockResolvedValue({
      success: true,
      data: mockStrategies,
    });

    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText('策略列表 (4)')).toBeInTheDocument();
    });

    // Test list view
    const listButton = screen.getByText('列表');
    fireEvent.click(listButton);

    const strategyItems = screen.getAllByText(/策略/);
    expect(strategyItems.length).toBeGreaterThan(0);

    // Test grid view
    const gridButton = screen.getByText('网格');
    fireEvent.click(gridButton);

    const gridContainer = screen.getByText('策略列表 (4)').closest('div')?.parentElement;
    expect(gridContainer).toHaveClass('md:grid-cols-2');
  });
});