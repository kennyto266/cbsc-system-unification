import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ToastContainer } from 'react-toastify';
import BatchOperationsPanel, { BatchOperation } from '../BatchOperationsPanel';
import { StrategyData, StrategyStatus } from '../StrategyToggleEnhanced';

// Mock the strategy control adapter
jest.mock('../../../services/strategyControlAdapter', () => ({
  strategyControlAdapter: {
    batchControlStrategies: jest.fn(),
  },
}));

// Mock react-toastify
jest.mock('react-toastify', () => ({
  toast: {
    success: jest.fn(),
    warning: jest.fn(),
    error: jest.fn(),
  },
  ToastContainer: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

const mockStrategies: StrategyData[] = [
  {
    id: 'strategy-1',
    name: '策略1',
    isActive: true,
    status: 'active' as StrategyStatus,
  },
  {
    id: 'strategy-2',
    name: '策略2',
    isActive: false,
    status: 'inactive' as StrategyStatus,
  },
  {
    id: 'strategy-3',
    name: '策略3',
    isActive: true,
    status: 'paused' as StrategyStatus,
  },
  {
    id: 'strategy-4',
    name: '策略4',
    isActive: false,
    status: 'stopped' as StrategyStatus,
  },
];

describe('BatchOperationsPanel', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  const renderComponent = (props = {}) => {
    const defaultProps = {
      strategies: mockStrategies,
      selectedStrategies: new Set<string>(),
      onSelectionChange: jest.fn(),
      onBatchControl: jest.fn(),
    };

    return render(
      <>
        <ToastContainer />
        <BatchOperationsPanel {...defaultProps} {...props} />
      </>
    );
  };

  it('renders batch operations panel correctly', () => {
    renderComponent();

    expect(screen.getByText('批量操作')).toBeInTheDocument();
    expect(screen.getByText('选择多个策略进行批量操作')).toBeInTheDocument();
    expect(screen.getByText('总数')).toBeInTheDocument();
    expect(screen.getByText('4')).toBeInTheDocument();
    expect(screen.getByText('运行中')).toBeInTheDocument();
    expect(screen.getByText('1')).toBeInTheDocument();
    expect(screen.getByText('未激活')).toBeInTheDocument();
    expect(screen.getByText('1')).toBeInTheDocument();
    expect(screen.getByText('已暂停')).toBeInTheDocument();
    expect(screen.getByText('1')).toBeInTheDocument();
    expect(screen.getByText('已停止')).toBeInTheDocument();
    expect(screen.getByText('1')).toBeInTheDocument();
  });

  it('handles strategy selection', () => {
    const onSelectionChange = jest.fn();
    renderComponent({ onSelectionChange });

    const checkboxes = screen.getAllByRole('checkbox');
    fireEvent.click(checkboxes[0]); // Select first strategy

    expect(onSelectionChange).toHaveBeenCalledWith(
      expect.any(Set)
    );
    const calledSet = onSelectionChange.mock.calls[0][0];
    expect(calledSet.has('strategy-1')).toBe(true);
  });

  it('handles select all', () => {
    const onSelectionChange = jest.fn();
    renderComponent({
      selectedStrategies: new Set(['strategy-1']),
      onSelectionChange,
    });

    const selectAllButton = screen.getByText('取消全选');
    fireEvent.click(selectAllButton);

    expect(onSelectionChange).toHaveBeenCalledWith(new Set());
  });

  it('handles select by status', () => {
    const onSelectionChange = jest.fn();
    renderComponent({ onSelectionChange });

    const selectActiveButton = screen.getByText('选择运行中');
    fireEvent.click(selectActiveButton);

    expect(onSelectionChange).toHaveBeenCalledWith(
      new Set(['strategy-1'])
    );
  });

  it('shows warning when no strategies selected for batch operation', async () => {
    const { toast } = require('react-toastify');
    renderComponent();

    const batchEnableButton = screen.getByText('批量启用');
    fireEvent.click(batchEnableButton);

    await waitFor(() => {
      expect(toast.warning).toHaveBeenCalledWith(
        '请先选择要操作的策略',
        expect.any(Object)
      );
    });
  });

  it('handles batch enable operation', async () => {
    const { strategyControlAdapter } = require('../../../services/strategyControlAdapter');
    strategyControlAdapter.batchControlStrategies.mockResolvedValue({
      success: true,
      results: [
        { strategyId: 'strategy-1', success: true },
        { strategyId: 'strategy-2', success: true },
      ],
    });

    const onBatchControl = jest.fn();
    renderComponent({
      selectedStrategies: new Set(['strategy-1', 'strategy-2']),
      onBatchControl,
    });

    // Mock window.confirm
    const originalConfirm = window.confirm;
    window.confirm = jest.fn(() => true);

    const batchEnableButton = screen.getByText('批量启用');
    fireEvent.click(batchEnableButton);

    expect(window.confirm).toHaveBeenCalledWith(
      '确定要启用选中的 2 个策略吗？\n\n此操作无法撤销。'
    );

    await waitFor(() => {
      expect(strategyControlAdapter.batchControlStrategies).toHaveBeenCalledWith(
        ['strategy-1', 'strategy-2'],
        'enable'
      );
    });

    await waitFor(() => {
      expect(onBatchControl).toHaveBeenCalledWith('enable', ['strategy-1', 'strategy-2']);
    });

    expect(screen.getByText('批量启用操作完成')).toBeInTheDocument();

    // Restore original confirm
    window.confirm = originalConfirm;
  });

  it('handles batch disable operation', async () => {
    const { strategyControlAdapter } = require('../../../services/strategyControlAdapter');
    strategyControlAdapter.batchControlStrategies.mockResolvedValue({
      success: true,
      results: [
        { strategyId: 'strategy-1', success: true },
      ],
    });

    const onBatchControl = jest.fn();
    renderComponent({
      selectedStrategies: new Set(['strategy-1']),
      onBatchControl,
    });

    // Mock window.confirm
    const originalConfirm = window.confirm;
    window.confirm = jest.fn(() => true);

    const batchDisableButton = screen.getByText('批量禁用');
    fireEvent.click(batchDisableButton);

    await waitFor(() => {
      expect(strategyControlAdapter.batchControlStrategies).toHaveBeenCalledWith(
        ['strategy-1'],
        'disable'
      );
    });

    // Restore original confirm
    window.confirm = originalConfirm;
  });

  it('handles batch operation error', async () => {
    const { strategyControlAdapter } = require('../../../services/strategyControlAdapter');
    strategyControlAdapter.batchControlStrategies.mockResolvedValue({
      success: false,
      error: 'Network error',
    });

    const { toast } = require('react-toastify');
    renderComponent({
      selectedStrategies: new Set(['strategy-1']),
    });

    // Mock window.confirm
    const originalConfirm = window.confirm;
    window.confirm = jest.fn(() => true);

    const batchEnableButton = screen.getByText('批量启用');
    fireEvent.click(batchEnableButton);

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith(
        '批量操作失败: Network error',
        expect.any(Object)
      );
    });

    // Restore original confirm
    window.confirm = originalConfirm;
  });

  it('shows loading state during batch operation', async () => {
    const { strategyControlAdapter } = require('../../../services/strategyControlAdapter');
    strategyControlAdapter.batchControlStrategies.mockImplementation(
      () => new Promise(resolve => setTimeout(() => resolve({ success: true }), 100))
    );

    renderComponent({
      selectedStrategies: new Set(['strategy-1']),
    });

    // Mock window.confirm
    const originalConfirm = window.confirm;
    window.confirm = jest.fn(() => true);

    const batchEnableButton = screen.getByText('批量启用');
    fireEvent.click(batchEnableButton);

    // Check for loading state
    await waitFor(() => {
      expect(screen.getByText('启用中...')).toBeInTheDocument();
      expect(batchEnableButton).toBeDisabled();
    });

    // Restore original confirm
    window.confirm = originalConfirm;
  });

  it('cancels batch operation when confirmation is denied', async () => {
    const { strategyControlAdapter } = require('../../../services/strategyControlAdapter');
    strategyControlAdapter.batchControlStrategies.mockResolvedValue({
      success: true,
      results: [],
    });

    renderComponent({
      selectedStrategies: new Set(['strategy-1']),
    });

    // Mock window.confirm to return false
    const originalConfirm = window.confirm;
    window.confirm = jest.fn(() => false);

    const batchEnableButton = screen.getByText('批量启用');
    fireEvent.click(batchEnableButton);

    expect(window.confirm).toHaveBeenCalled();
    expect(strategyControlAdapter.batchControlStrategies).not.toHaveBeenCalled();

    // Restore original confirm
    window.confirm = originalConfirm;
  });

  it('shows empty state when no strategies', () => {
    renderComponent({
      strategies: [],
    });

    expect(screen.getByText('暂无策略')).toBeInTheDocument();
  });

  it('disables batch operation buttons when loading', () => {
    renderComponent({
      selectedStrategies: new Set(['strategy-1']),
    });

    // Get all batch operation buttons
    const buttons = screen.getAllByText(/批量/);
    buttons.forEach(button => {
      expect(button).toBeDisabled();
    });
  });

  it('disables batch operation buttons when no strategies selected', () => {
    renderComponent({
      selectedStrategies: new Set(),
    });

    // Get all batch operation buttons
    const buttons = screen.getAllByText(/批量/);
    buttons.forEach(button => {
      expect(button).toBeDisabled();
    });
  });

  it('shows correct operation names in confirmation dialogs', () => {
    renderComponent({
      selectedStrategies: new Set(['strategy-1']),
    });

    // Mock window.confirm to capture the message
    const originalConfirm = window.confirm;
    let confirmMessage = '';
    window.confirm = jest.fn((message) => {
      confirmMessage = message;
      return true;
    });

    const operations: Array<{ button: string; expectedText: string }> = [
      { button: '批量启用', expectedText: '确定要启用' },
      { button: '批量禁用', expectedText: '确定要禁用' },
      { button: '批量暂停', expectedText: '确定要暂停' },
      { button: '批量停止', expectedText: '确定要停止' },
    ];

    operations.forEach(({ button, expectedText }) => {
      confirmMessage = '';
      fireEvent.click(screen.getByText(button));
      expect(confirmMessage).toContain(expectedText);
      expect(confirmMessage).toContain('1 个策略');
    });

    // Restore original confirm
    window.confirm = originalConfirm;
  });
});