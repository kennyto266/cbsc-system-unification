import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ToastContainer } from 'react-toastify';
import StrategyControlDashboard from '../StrategyControlDashboard';

// Mock the strategy control service
jest.mock('../../../../services/strategyControlService', () => ({
  __esModule: true,
  default: {
    controlStrategy: jest.fn(),
    batchControlStrategies: jest.fn(),
  }
}));

// Mock react-toastify
jest.mock('react-toastify', () => ({
  ToastContainer: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  toast: {
    success: jest.fn(),
    error: jest.fn(),
    warning: jest.fn(),
  }
}));

const mockStrategies = [
  {
    id: 'direct_rsi',
    name: '直接RSI情绪策略',
    type: 'direct_rsi',
    category: 'core_cbsc',
    status: 'active',
    isActive: true,
    description: '基于牛熊比例的RSI计算，识别极端情绪信号',
    lastUpdated: new Date('2023-12-01T10:30:00Z')
  },
  {
    id: 'sentiment_momentum',
    name: '情绪动量策略',
    type: 'sentiment_momentum',
    category: 'core_cbsc',
    status: 'inactive',
    isActive: false,
    description: 'MACD风格的情绪变化率分析，捕捉情绪转折点',
    lastUpdated: new Date('2023-12-01T10:25:00Z')
  },
  {
    id: 'composite_index',
    name: '复合指标策略',
    type: 'composite_index',
    category: 'multi_factor',
    status: 'active',
    isActive: true,
    description: '多维度情绪综合，布林带风格的情绪区间分析',
    lastUpdated: new Date('2023-12-01T10:35:00Z')
  },
  {
    id: 'volatility_adjusted',
    name: '波动率调整策略',
    type: 'volatility_adjusted',
    category: 'multi_factor',
    status: 'inactive',
    isActive: false,
    description: '成交量加权的情绪分析，考虑市场信心度',
    lastUpdated: new Date('2023-12-01T10:20:00Z')
  }
];

const mockOnStrategyUpdate = jest.fn();

const renderWithToast = (component: React.ReactElement) => {
  return render(
    <>
      <ToastContainer />
      {component}
    </>
  );
};

describe('StrategyControlIntegration', () => {
  const strategyControlService = require('../../../../services/strategyControlService').default;

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders complete strategy control dashboard', () => {
    renderWithToast(
      <StrategyControlDashboard
        strategies={mockStrategies}
        onStrategyUpdate={mockOnStrategyUpdate}
      />
    );

    // Check header
    expect(screen.getByText('策略控制中心')).toBeInTheDocument();
    expect(screen.getByText('管理您的量化交易策略啟用/禁用狀態')).toBeInTheDocument();

    // Check status summary
    expect(screen.getByText('2')).toBeInTheDocument(); // Active strategies
    expect(screen.getByText('2')).toBeInTheDocument(); // Inactive strategies
    expect(screen.getByText('4')).toBeInTheDocument(); // Total strategies

    // Check all strategies are listed
    expect(screen.getByText('直接RSI情绪策略')).toBeInTheDocument();
    expect(screen.getByText('情绪动量策略')).toBeInTheDocument();
    expect(screen.getByText('复合指标策略')).toBeInTheDocument();
    expect(screen.getByText('波动率调整策略')).toBeInTheDocument();
  });

  it('filters strategies correctly', async () => {
    renderWithToast(
      <StrategyControlDashboard
        strategies={mockStrategies}
        onStrategyUpdate={mockOnStrategyUpdate}
      />
    );

    // Filter by active strategies
    const statusFilter = screen.getByDisplayValue('全部');
    fireEvent.change(statusFilter, { target: { value: 'active' } });

    await waitFor(() => {
      expect(screen.getByText('直接RSI情绪策略')).toBeInTheDocument();
      expect(screen.getByText('复合指标策略')).toBeInTheDocument();
      expect(screen.queryByText('情绪动量策略')).not.toBeInTheDocument();
      expect(screen.queryByText('波动率调整策略')).not.toBeInTheDocument();
    });

    // Filter by inactive strategies
    fireEvent.change(statusFilter, { target: { value: 'inactive' } });

    await waitFor(() => {
      expect(screen.queryByText('直接RSI情绪策略')).not.toBeInTheDocument();
      expect(screen.queryByText('复合指标策略')).not.toBeInTheDocument();
      expect(screen.getByText('情绪动量策略')).toBeInTheDocument();
      expect(screen.getByText('波动率调整策略')).toBeInTheDocument();
    });
  });

  it('searches strategies correctly', async () => {
    renderWithToast(
      <StrategyControlDashboard
        strategies={mockStrategies}
        onStrategyUpdate={mockOnStrategyUpdate}
      />
    );

    // Search for "RSI"
    const searchInput = screen.getByPlaceholderText('搜索策略名稱、類型或分類...');
    fireEvent.change(searchInput, { target: { value: 'RSI' } });

    await waitFor(() => {
      expect(screen.getByText('直接RSI情绪策略')).toBeInTheDocument();
      expect(screen.queryByText('情绪动量策略')).not.toBeInTheDocument();
      expect(screen.queryByText('复合指标策略')).not.toBeInTheDocument();
      expect(screen.queryByText('波动率调整策略')).not.toBeInTheDocument();
    });
  });

  it('switches between grid and list view', () => {
    renderWithToast(
      <StrategyControlDashboard
        strategies={mockStrategies}
        onStrategyUpdate={mockOnStrategyUpdate}
      />
    );

    // Default should be grid view
    expect(screen.getByRole('button', { name: '網格' })).toHaveClass('bg-white');
    expect(screen.getByRole('button', { name: '列表' })).not.toHaveClass('bg-white');

    // Switch to list view
    fireEvent.click(screen.getByRole('button', { name: '列表' }));

    expect(screen.getByRole('button', { name: '列表' })).toHaveClass('bg-white');
    expect(screen.getByRole('button', { name: '網格' })).not.toHaveClass('bg-white');
  });

  it('performs individual strategy control', async () => {
    strategyControlService.controlStrategy.mockResolvedValue({
      success: true,
      strategy_id: 'sentiment_momentum',
      action: 'enable',
      previous_status: false,
      new_status: true,
      message: 'Strategy enabled successfully',
      timestamp: new Date().toISOString()
    });

    renderWithToast(
      <StrategyControlDashboard
        strategies={mockStrategies}
        onStrategyUpdate={mockOnStrategyUpdate}
      />
    );

    // Find the disable toggle for sentiment_momentum strategy
    const strategyCard = screen.getByText('情绪动量策略').closest('[role="switch"]')?.parentElement?.parentElement;
    const toggleButton = strategyCard?.querySelector('[role="switch"]');

    if (toggleButton) {
      fireEvent.click(toggleButton);

      await waitFor(() => {
        expect(strategyControlService.controlStrategy).toHaveBeenCalledWith(
          'sentiment_momentum',
          { action: 'enable' }
        );
      });

      expect(mockOnStrategyUpdate).toHaveBeenCalledWith('sentiment_momentum', true);
      expect(toast.success).toHaveBeenCalled();
    }
  });

  it('performs batch strategy control', async () => {
    strategyControlService.batchControlStrategies.mockResolvedValue({
      total_count: 2,
      success_count: 2,
      failure_count: 0,
      results: [
        {
          strategy_id: 'sentiment_momentum',
          success: true,
          action: 'enable',
          previous_status: false,
          new_status: true,
          message: 'Strategy enabled successfully',
          timestamp: new Date().toISOString()
        },
        {
          strategy_id: 'volatility_adjusted',
          success: true,
          action: 'enable',
          previous_status: false,
          new_status: true,
          message: 'Strategy enabled successfully',
          timestamp: new Date().toISOString()
        }
      ],
      batch_id: 'batch_123',
      timestamp: new Date().toISOString()
    });

    renderWithToast(
      <StrategyControlDashboard
        strategies={mockStrategies}
        onStrategyUpdate={mockOnStrategyUpdate}
      />
    );

    // Select inactive strategies
    const strategy1Checkbox = screen.getAllByRole('checkbox')[1]; // sentiment_momentum
    const strategy2Checkbox = screen.getAllByRole('checkbox')[3]; // volatility_adjusted

    fireEvent.click(strategy1Checkbox);
    fireEvent.click(strategy2Checkbox);

    // Click batch enable button
    const batchEnableButton = screen.getByText('全部啟用');
    fireEvent.click(batchEnableButton);

    await waitFor(() => {
      expect(strategyControlService.batchControlStrategies).toHaveBeenCalledWith({
        strategy_ids: ['sentiment_momentum', 'volatility_adjusted'],
        action: 'enable',
        reason: undefined
      });
    });

    expect(mockOnStrategyUpdate).toHaveBeenCalledTimes(2);
    expect(mockOnStrategyUpdate).toHaveBeenCalledWith('sentiment_momentum', true);
    expect(mockOnStrategyUpdate).toHaveBeenCalledWith('volatility_adjusted', true);
    expect(toast.success).toHaveBeenCalled();
  });

  it('shows operation history', async () => {
    strategyControlService.controlStrategy.mockResolvedValue({
      success: true,
      strategy_id: 'sentiment_momentum',
      action: 'enable',
      previous_status: false,
      new_status: true,
      message: 'Strategy enabled successfully',
      timestamp: new Date().toISOString()
    });

    renderWithToast(
      <StrategyControlDashboard
        strategies={mockStrategies}
        onStrategyUpdate={mockOnStrategyUpdate}
      />
    );

    // Perform an operation
    const strategyCard = screen.getByText('情绪动量策略').closest('[role="switch"]')?.parentElement?.parentElement;
    const toggleButton = strategyCard?.querySelector('[role="switch"]');

    if (toggleButton) {
      fireEvent.click(toggleButton);

      await waitFor(() => {
        expect(screen.getByText('操作歷史')).toBeInTheDocument();
        expect(screen.getByText('情绪动量策略')).toBeInTheDocument();
      });
    }
  });

  it('handles empty state correctly', () => {
    renderWithToast(
      <StrategyControlDashboard
        strategies={[]}
        onStrategyUpdate={mockOnStrategyUpdate}
      />
    );

    expect(screen.getByText('沒有策略')).toBeInTheDocument();
    expect(screen.getByText('請先添加策略到系統中')).toBeInTheDocument();
  });

  it('handles search with no results', async () => {
    renderWithToast(
      <StrategyControlDashboard
        strategies={mockStrategies}
        onStrategyUpdate={mockOnStrategyUpdate}
      />
    );

    // Search for non-existent strategy
    const searchInput = screen.getByPlaceholderText('搜索策略名稱、類型或分類...');
    fireEvent.change(searchInput, { target: { value: 'nonexistent' } });

    await waitFor(() => {
      expect(screen.getByText('沒有找到匹配的策略')).toBeInTheDocument();
      expect(screen.getByText('請嘗試其他搜索詞或清除過濾條件')).toBeInTheDocument();
    });
  });

  it('shows confirmation dialog for dangerous batch operations', async () => {
    renderWithToast(
      <StrategyControlDashboard
        strategies={mockStrategies}
        onStrategyUpdate={mockOnStrategyUpdate}
      />
    );

    // Select all strategies
    const selectAllButton = screen.getByText('全選');
    fireEvent.click(selectAllButton);

    // Click emergency stop button
    const emergencyStopButton = screen.getByText('緊急停止');
    fireEvent.click(emergencyStopButton);

    await waitFor(() => {
      expect(screen.getByText('確認批量停止')).toBeInTheDocument();
      expect(screen.getByText(/您確定要停止選中的 4 個策略嗎？/)).toBeInTheDocument();
    });

    // Check that all strategies are listed in the dialog
    expect(screen.getByText('直接RSI情绪策略')).toBeInTheDocument();
    expect(screen.getByText('情绪动量策略')).toBeInTheDocument();
    expect(screen.getByText('复合指标策略')).toBeInTheDocument();
    expect(screen.getByText('波动率调整策略')).toBeInTheDocument();
  });

  it('executes emergency stop operation', async () => {
    strategyControlService.batchControlStrategies.mockResolvedValue({
      total_count: 4,
      success_count: 4,
      failure_count: 0,
      results: mockStrategies.map(strategy => ({
        strategy_id: strategy.id,
        success: true,
        action: 'stop',
        previous_status: strategy.isActive,
        new_status: false,
        message: 'Strategy stopped successfully',
        timestamp: new Date().toISOString()
      })),
      batch_id: 'emergency_stop_123',
      timestamp: new Date().toISOString()
    });

    renderWithToast(
      <StrategyControlDashboard
        strategies={mockStrategies}
        onStrategyUpdate={mockOnStrategyUpdate}
      />
    );

    // Select all strategies
    const selectAllButton = screen.getByText('全選');
    fireEvent.click(selectAllButton);

    // Click emergency stop
    const emergencyStopButton = screen.getByText('緊急停止');
    fireEvent.click(emergencyStopButton);

    // Wait for confirmation dialog
    await waitFor(() => {
      expect(screen.getByText('確認批量停止')).toBeInTheDocument();
    });

    // Confirm the operation
    const confirmButton = screen.getByText('確認停止');
    fireEvent.click(confirmButton);

    await waitFor(() => {
      expect(strategyControlService.batchControlStrategies).toHaveBeenCalledWith({
        strategy_ids: ['direct_rsi', 'sentiment_momentum', 'composite_index', 'volatility_adjusted'],
        action: 'stop',
        reason: undefined
      });
    });

    expect(mockOnStrategyUpdate).toHaveBeenCalledTimes(4);
    expect(toast.success).toHaveBeenCalledWith(
      expect.stringContaining('批量操作完成'),
      expect.any(Object)
    );
  });

  it('cleares operation history', async () => {
    strategyControlService.controlStrategy.mockResolvedValue({
      success: true,
      strategy_id: 'sentiment_momentum',
      action: 'enable',
      previous_status: false,
      new_status: true,
      message: 'Strategy enabled successfully',
      timestamp: new Date().toISOString()
    });

    renderWithToast(
      <StrategyControlDashboard
        strategies={mockStrategies}
        onStrategyUpdate={mockOnStrategyUpdate}
      />
    );

    // Perform an operation to create history
    const strategyCard = screen.getByText('情绪动量策略').closest('[role="switch"]')?.parentElement?.parentElement;
    const toggleButton = strategyCard?.querySelector('[role="switch"]');

    if (toggleButton) {
      fireEvent.click(toggleButton);

      await waitFor(() => {
        expect(screen.getByText('操作歷史')).toBeInTheDocument();
      });

      // Clear history
      const clearButton = screen.getByText('清除');
      fireEvent.click(clearButton);

      await waitFor(() => {
        expect(screen.queryByText('操作歷史')).not.toBeInTheDocument();
      });
    }
  });
});