import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ToastContainer } from 'react-toastify';
import BatchOperationsPanel from '../BatchOperationsPanel';

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
    id: 'strategy-1',
    name: 'RSI Strategy',
    isActive: true,
    status: 'active',
    category: 'core_cbsc'
  },
  {
    id: 'strategy-2',
    name: 'Momentum Strategy',
    isActive: false,
    status: 'inactive',
    category: 'multi_factor'
  },
  {
    id: 'strategy-3',
    name: 'Composite Strategy',
    isActive: true,
    status: 'active',
    category: 'core_cbsc'
  }
];

const mockOnBatchControl = jest.fn();
const mockOnSelectionChange = jest.fn();

const renderWithToast = (component: React.ReactElement) => {
  return render(
    <>
      <ToastContainer />
      {component}
    </>
  );
};

describe('BatchOperationsPanel', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders batch operations panel correctly', () => {
    renderWithToast(
      <BatchOperationsPanel
        strategies={mockStrategies}
        selectedStrategies={new Set()}
        onSelectionChange={mockOnSelectionChange}
        onBatchControl={mockOnBatchControl}
      />
    );

    // Check if main components are rendered
    expect(screen.getByText('已選擇:')).toBeInTheDocument();
    expect(screen.getByText('0')).toBeInTheDocument();
    expect(screen.getByText('/ 3')).toBeInTheDocument();
    expect(screen.getByText('全選')).toBeInTheDocument();
    expect(screen.getByText('全部啟用')).toBeInTheDocument();
    expect(screen.getByText('全部禁用')).toBeInTheDocument();
    expect(screen.getByText('全部暫停')).toBeInTheDocument();
    expect(screen.getByText('緊急停止')).toBeInTheDocument();
  });

  it('handles select all correctly', () => {
    renderWithToast(
      <BatchOperationsPanel
        strategies={mockStrategies}
        selectedStrategies={new Set()}
        onSelectionChange={mockOnSelectionChange}
        onBatchControl={mockOnBatchControl}
      />
    );

    const selectAllButton = screen.getByText('全選');
    fireEvent.click(selectAllButton);

    expect(mockOnSelectionChange).toHaveBeenCalledWith(
      new Set(['strategy-1', 'strategy-2', 'strategy-3'])
    );
  });

  it('handles deselect all correctly', () => {
    renderWithToast(
      <BatchOperationsPanel
        strategies={mockStrategies}
        selectedStrategies={new Set(['strategy-1', 'strategy-2', 'strategy-3'])}
        onSelectionChange={mockOnSelectionChange}
        onBatchControl={mockOnBatchControl}
      />
    );

    const deselectAllButton = screen.getByText('取消全選');
    fireEvent.click(deselectAllButton);

    expect(mockOnSelectionChange).toHaveBeenCalledWith(new Set());
  });

  it('shows selected strategies count correctly', () => {
    renderWithToast(
      <BatchOperationsPanel
        strategies={mockStrategies}
        selectedStrategies={new Set(['strategy-1', 'strategy-2'])}
        onSelectionChange={mockOnSelectionChange}
        onBatchControl={mockOnBatchControl}
      />
    );

    expect(screen.getByText('2')).toBeInTheDocument();
    expect(screen.getByText('/ 3')).toBeInTheDocument();
    expect(screen.getByText('取消全選')).toBeInTheDocument();
  });

  it('executes quick enable action without confirmation', async () => {
    mockOnBatchControl.mockResolvedValue({
      success_count: 1,
      failure_count: 0,
      results: [
        {
          strategy_id: 'strategy-2',
          success: true,
          message: 'Strategy enabled successfully'
        }
      ]
    });

    // Select an inactive strategy
    renderWithToast(
      <BatchOperationsPanel
        strategies={mockStrategies}
        selectedStrategies={new Set(['strategy-2'])
        onSelectionChange={mockOnSelectionChange}
        onBatchControl={mockOnBatchControl}
      />
    );

    const enableButton = screen.getByText('全部啟用');
    fireEvent.click(enableButton);

    await waitFor(() => {
      expect(mockOnBatchControl).toHaveBeenCalledWith(
        ['strategy-2'],
        'enable',
        undefined
      );
    });

    expect(toast.success).toHaveBeenCalled();
  });

  it('shows confirmation dialog for dangerous actions', async () => {
    renderWithToast(
      <BatchOperationsPanel
        strategies={mockStrategies}
        selectedStrategies={new Set(['strategy-1'])
        onSelectionChange={mockOnSelectionChange}
        onBatchControl={mockOnBatchControl}
      />
    );

    const stopButton = screen.getByText('緊急停止');
    fireEvent.click(stopButton);

    await waitFor(() => {
      expect(screen.getByText('確認批量停止')).toBeInTheDocument();
    });

    // Check dialog content
    expect(screen.getByText(/您確定要停止選中的 1 個策略嗎？/)).toBeInTheDocument();
    expect(screen.getByText('取消')).toBeInTheDocument();
    expect(screen.getByText('確認停止')).toBeInTheDocument();
  });

  it('executes dangerous action when confirmed', async () => {
    mockOnBatchControl.mockResolvedValue({
      success_count: 1,
      failure_count: 0,
      results: [
        {
          strategy_id: 'strategy-1',
          success: true,
          message: 'Strategy stopped successfully'
        }
      ]
    });

    renderWithToast(
      <BatchOperationsPanel
        strategies={mockStrategies}
        selectedStrategies={new Set(['strategy-1'])
        onSelectionChange={mockOnSelectionChange}
        onBatchControl={mockOnBatchControl}
      />
    );

    // Click stop button to show dialog
    const stopButton = screen.getByText('緊急停止');
    fireEvent.click(stopButton);

    await waitFor(() => {
      expect(screen.getByText('確認批量停止')).toBeInTheDocument();
    });

    // Add reason
    const reasonTextarea = screen.getByPlaceholderText('請輸入批量操作的原因（可選）...');
    fireEvent.change(reasonTextarea, { target: { value: 'Market volatility' } });

    // Click confirm
    const confirmButton = screen.getByText('確認停止');
    fireEvent.click(confirmButton);

    await waitFor(() => {
      expect(mockOnBatchControl).toHaveBeenCalledWith(
        ['strategy-1'],
        'stop',
        'Market volatility'
      );
    });

    expect(toast.success).toHaveBeenCalled();
  });

  it('cancels dangerous action when cancel is clicked', async () => {
    renderWithToast(
      <BatchOperationsPanel
        strategies={mockStrategies}
        selectedStrategies={new Set(['strategy-1'])
        onSelectionChange={mockOnSelectionChange}
        onBatchControl={mockOnBatchControl}
      />
    );

    const stopButton = screen.getByText('緊急停止');
    fireEvent.click(stopButton);

    await waitFor(() => {
      expect(screen.getByText('確認批量停止')).toBeInTheDocument();
    });

    const cancelButton = screen.getByText('取消');
    fireEvent.click(cancelButton);

    await waitFor(() => {
      expect(screen.queryByText('確認批量停止')).not.toBeInTheDocument();
    });

    expect(mockOnBatchControl).not.toHaveBeenCalled();
  });

  it('shows warning when no strategies selected for dangerous action', async () => {
    renderWithToast(
      <BatchOperationsPanel
        strategies={mockStrategies}
        selectedStrategies={new Set()}
        onSelectionChange={mockOnSelectionChange}
        onBatchControl={mockOnBatchControl}
      />
    );

    const stopButton = screen.getByText('緊急停止');
    fireEvent.click(stopButton);

    await waitFor(() => {
      expect(toast.warning).toHaveBeenCalledWith(
        '請先選擇要操作的策略',
        expect.any(Object)
      );
    });
  });

  it('executes quick actions on all strategies when none selected', async () => {
    mockOnBatchControl.mockResolvedValue({
      success_count: 2,
      failure_count: 0,
      results: [
        {
          strategy_id: 'strategy-1',
          success: true,
          message: 'Strategy disabled successfully'
        },
        {
          strategy_id: 'strategy-3',
          success: true,
          message: 'Strategy disabled successfully'
        }
      ]
    });

    renderWithToast(
      <BatchOperationsPanel
        strategies={mockStrategies}
        selectedStrategies={new Set()}
        onSelectionChange={mockOnSelectionChange}
        onBatchControl={mockOnBatchControl}
      />
    );

    // Click disable without any selection
    const disableButton = screen.getByText('全部禁用');
    fireEvent.click(disableButton);

    // Should operate on all active strategies (strategy-1 and strategy-3)
    await waitFor(() => {
      expect(mockOnBatchControl).toHaveBeenCalledWith(
        ['strategy-1', 'strategy-3'],
        'disable',
        undefined
      );
    });
  });

  it('shows detailed error message for partial failures', async () => {
    mockOnBatchControl.mockResolvedValue({
      success_count: 1,
      failure_count: 1,
      results: [
        {
          strategy_id: 'strategy-1',
          success: true,
          message: 'Strategy disabled successfully'
        },
        {
          strategy_id: 'strategy-2',
          success: false,
          message: 'Strategy not found'
        }
      ]
    });

    renderWithToast(
      <BatchOperationsPanel
        strategies={mockStrategies}
        selectedStrategies={new Set(['strategy-1', 'strategy-2'])
        onSelectionChange={mockOnSelectionChange}
        onBatchControl={mockOnBatchControl}
      />
    );

    const disableButton = screen.getByText('全部禁用');
    fireEvent.click(disableButton);

    await waitFor(() => {
      expect(toast.success).toHaveBeenCalledWith(
        expect.stringContaining('批量操作完成'),
        expect.any(Object)
      );
    });

    // Should also show detailed failure information
    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith(
        expect.stringContaining('部分策略操作失敗詳情'),
        expect.any(Object)
      );
    }, { timeout: 2000 });
  });

  it('handles network errors gracefully', async () => {
    mockOnBatchControl.mockRejectedValue(new Error('Network error'));

    renderWithToast(
      <BatchOperationsPanel
        strategies={mockStrategies}
        selectedStrategies={new Set(['strategy-1'])
        onSelectionChange={mockOnSelectionChange}
        onBatchControl={mockOnBatchControl}
      />
    );

    const enableButton = screen.getByText('全部啟用');
    fireEvent.click(enableButton);

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith(
        expect.stringContaining('系統錯誤'),
        expect.any(Object)
      );
    });
  });

  it('disables buttons during processing', async () => {
    mockOnBatchControl.mockImplementation(() => new Promise(resolve => setTimeout(() => resolve({
      success_count: 1,
      failure_count: 0,
      results: [{ strategy_id: 'strategy-1', success: true, message: 'Success' }]
    }), 100)));

    renderWithToast(
      <BatchOperationsPanel
        strategies={mockStrategies}
        selectedStrategies={new Set(['strategy-1'])
        onSelectionChange={mockOnSelectionChange}
        onBatchControl={mockOnBatchControl}
      />
    );

    const enableButton = screen.getByText('全部啟用');
    fireEvent.click(enableButton);

    await waitFor(() => {
      expect(enableButton).toBeDisabled();
      expect(enableButton).toHaveClass('opacity-50', 'cursor-not-allowed');
    });
  });

  it('shows processing indicator during operation', async () => {
    mockOnBatchControl.mockImplementation(() => new Promise(resolve => setTimeout(() => resolve({
      success_count: 1,
      failure_count: 0,
      results: [{ strategy_id: 'strategy-1', success: true, message: 'Success' }]
    }), 100)));

    renderWithToast(
      <BatchOperationsPanel
        strategies={mockStrategies}
        selectedStrategies={new Set(['strategy-1'])
        onSelectionChange={mockOnSelectionChange}
        onBatchControl={mockOnBatchControl}
      />
    );

    const enableButton = screen.getByText('全部啟用');
    fireEvent.click(enableButton);

    await waitFor(() => {
      expect(screen.getByText('正在執行批量操作，請稍候...')).toBeInTheDocument();
    });
  });
});