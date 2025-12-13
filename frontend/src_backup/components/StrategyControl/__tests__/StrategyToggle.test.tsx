import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ToastContainer } from 'react-toastify';
import StrategyToggle from '../StrategyToggle';

// Mock the strategy control service
jest.mock('../../../../services/strategyControlService', () => ({
  __esModule: true,
  default: {
    enableStrategy: jest.fn(),
    disableStrategy: jest.fn(),
    startStrategy: jest.fn(),
    stopStrategy: jest.fn(),
    pauseStrategy: jest.fn(),
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

const mockStrategy = {
  id: 'test-strategy-1',
  name: 'Test RSI Strategy',
  isActive: false,
  status: 'inactive'
};

const mockOnToggle = jest.fn();

const renderWithToast = (component: React.ReactElement) => {
  return render(
    <>
      <ToastContainer />
      {component}
    </>
  );
};

describe('StrategyToggle', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders strategy toggle with correct initial state', () => {
    renderWithToast(
      <StrategyToggle
        strategyId={mockStrategy.id}
        strategyName={mockStrategy.name}
        isActive={mockStrategy.isActive}
        status={mockStrategy.status}
        onToggle={mockOnToggle}
      />
    );

    // Check if strategy name is displayed
    expect(screen.getByText('Test RSI Strategy')).toBeInTheDocument();

    // Check if status shows as inactive
    expect(screen.getByText('已停止')).toBeInTheDocument();

    // Check if toggle is in off position
    const toggleButton = screen.getByRole('switch');
    expect(toggleButton).toHaveAttribute('aria-checked', 'false');
  });

  it('renders active strategy correctly', () => {
    renderWithToast(
      <StrategyToggle
        strategyId={mockStrategy.id}
        strategyName={mockStrategy.name}
        isActive={true}
        status="active"
        onToggle={mockOnToggle}
      />
    );

    // Check if status shows as active
    expect(screen.getByText('運行中')).toBeInTheDocument();

    // Check if toggle is in on position
    const toggleButton = screen.getByRole('switch');
    expect(toggleButton).toHaveAttribute('aria-checked', 'true');
  });

  it('handles enable action without confirmation', async () => {
    mockOnToggle.mockResolvedValue(true);

    renderWithToast(
      <StrategyToggle
        strategyId={mockStrategy.id}
        strategyName={mockStrategy.name}
        isActive={false}
        status="inactive"
        onToggle={mockOnToggle}
      />
    );

    const toggleButton = screen.getByRole('switch');
    fireEvent.click(toggleButton);

    // Should call onToggle with 'enable' action without showing confirmation dialog
    await waitFor(() => {
      expect(mockOnToggle).toHaveBeenCalledWith(mockStrategy.id, 'enable');
    });

    // Should show success toast
    expect(toast.success).toHaveBeenCalledWith(
      expect.stringContaining('已成功啟用'),
      expect.any(Object)
    );
  });

  it('shows confirmation dialog for dangerous actions', async () => {
    renderWithToast(
      <StrategyToggle
        strategyId={mockStrategy.id}
        strategyName={mockStrategy.name}
        isActive={true}
        status="active"
        onToggle={mockOnToggle}
      />
    );

    const toggleButton = screen.getByRole('switch');
    fireEvent.click(toggleButton);

    // Should show confirmation dialog
    await waitFor(() => {
      expect(screen.getByText('確認禁用策略')).toBeInTheDocument();
    });

    // Check dialog content
    expect(screen.getByText(/您確定要禁用策略/)).toBeInTheDocument();
    expect(screen.getByText('取消')).toBeInTheDocument();
    expect(screen.getByText('禁用')).toBeInTheDocument();
  });

  it('cancels dangerous action when cancel is clicked', async () => {
    renderWithToast(
      <StrategyToggle
        strategyId={mockStrategy.id}
        strategyName={mockStrategy.name}
        isActive={true}
        status="active"
        onToggle={mockOnToggle}
      />
    );

    const toggleButton = screen.getByRole('switch');
    fireEvent.click(toggleButton);

    // Wait for confirmation dialog
    await waitFor(() => {
      expect(screen.getByText('確認禁用策略')).toBeInTheDocument();
    });

    // Click cancel
    const cancelButton = screen.getByText('取消');
    fireEvent.click(cancelButton);

    // Dialog should close
    await waitFor(() => {
      expect(screen.queryByText('確認禁用策略')).not.toBeInTheDocument();
    });

    // onToggle should not be called
    expect(mockOnToggle).not.toHaveBeenCalled();
  });

  it('executes dangerous action when confirmed', async () => {
    mockOnToggle.mockResolvedValue(true);

    renderWithToast(
      <StrategyToggle
        strategyId={mockStrategy.id}
        strategyName={mockStrategy.name}
        isActive={true}
        status="active"
        onToggle={mockOnToggle}
      />
    );

    const toggleButton = screen.getByRole('switch');
    fireEvent.click(toggleButton);

    // Wait for confirmation dialog
    await waitFor(() => {
      expect(screen.getByText('確認禁用策略')).toBeInTheDocument();
    });

    // Add reason
    const reasonTextarea = screen.getByPlaceholderText('請輸入操作原因...');
    fireEvent.change(reasonTextarea, { target: { value: 'Test reason' } });

    // Click confirm
    const confirmButton = screen.getByText('禁用');
    fireEvent.click(confirmButton);

    // Should call onToggle with 'disable' action
    await waitFor(() => {
      expect(mockOnToggle).toHaveBeenCalledWith(mockStrategy.id, 'disable');
    });

    // Dialog should close
    expect(screen.queryByText('確認禁用策略')).not.toBeInTheDocument();
  });

  it('handles failed operations', async () => {
    mockOnToggle.mockRejectedValue(new Error('Network error'));

    renderWithToast(
      <StrategyToggle
        strategyId={mockStrategy.id}
        strategyName={mockStrategy.name}
        isActive={false}
        status="inactive"
        onToggle={mockOnToggle}
      />
    );

    const toggleButton = screen.getByRole('switch');
    fireEvent.click(toggleButton);

    // Should show error toast
    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith(
        expect.stringContaining('操作失敗'),
        expect.any(Object)
      );
    });
  });

  it('is disabled when disabled prop is true', () => {
    renderWithToast(
      <StrategyToggle
        strategyId={mockStrategy.id}
        strategyName={mockStrategy.name}
        isActive={false}
        status="inactive"
        onToggle={mockOnToggle}
        disabled={true}
      />
    );

    const toggleButton = screen.getByRole('switch');
    expect(toggleButton).toBeDisabled();
    expect(toggleButton).toHaveClass('opacity-50', 'cursor-not-allowed');
  });

  it('renders with different sizes', () => {
    const { rerender } = renderWithToast(
      <StrategyToggle
        strategyId={mockStrategy.id}
        strategyName={mockStrategy.name}
        isActive={false}
        status="inactive"
        onToggle={mockOnToggle}
        size="small"
      />
    );

    // Small size
    expect(screen.getByRole('switch')).toHaveClass('w-8', 'h-4');

    // Medium size (default)
    rerender(
      <StrategyToggle
        strategyId={mockStrategy.id}
        strategyName={mockStrategy.name}
        isActive={false}
        status="inactive"
        onToggle={mockOnToggle}
        size="medium"
      />
    );
    expect(screen.getByRole('switch')).toHaveClass('w-12', 'h-6');

    // Large size
    rerender(
      <StrategyToggle
        strategyId={mockStrategy.id}
        strategyName={mockStrategy.name}
        isActive={false}
        status="inactive"
        onToggle={mockOnToggle}
        size="large"
      />
    );
    expect(screen.getByRole('switch')).toHaveClass('w-16', 'h-8');
  });

  it('hides labels when showLabels is false', () => {
    renderWithToast(
      <StrategyToggle
        strategyId={mockStrategy.id}
        strategyName={mockStrategy.name}
        isActive={false}
        status="inactive"
        onToggle={mockOnToggle}
        showLabels={false}
      />
    );

    // Status text should not be shown
    expect(screen.queryByText('已停止')).not.toBeInTheDocument();
  });

  it('shows loading state during operation', async () => {
    mockOnToggle.mockImplementation(() => new Promise(resolve => setTimeout(() => resolve(true), 100)));

    renderWithToast(
      <StrategyToggle
        strategyId={mockStrategy.id}
        strategyName={mockStrategy.name}
        isActive={false}
        status="inactive"
        onToggle={mockOnToggle}
      />
    );

    const toggleButton = screen.getByRole('switch');
    fireEvent.click(toggleButton);

    // Should show loading state
    await waitFor(() => {
      expect(screen.getByText('處理中...')).toBeInTheDocument();
    });

    // Loading spinner should be present
    expect(screen.getByRole('switch')).toBeDisabled();
  });

  it('applies custom className', () => {
    renderWithToast(
      <StrategyToggle
        strategyId={mockStrategy.id}
        strategyName={mockStrategy.name}
        isActive={false}
        status="inactive"
        onToggle={mockOnToggle}
        className="custom-toggle-class"
      />
    );

    // Check if custom class is applied to the container
    const container = screen.getByRole('switch').parentElement?.parentElement;
    expect(container).toHaveClass('custom-toggle-class');
  });
});