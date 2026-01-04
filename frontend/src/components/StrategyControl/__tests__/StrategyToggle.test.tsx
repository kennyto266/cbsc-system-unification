import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ToastContainer } from 'react-toastify';
import StrategyToggleEnhanced, { StrategyData, StrategyStatus } from '../StrategyToggleEnhanced';

// Mock window.confirm
global.confirm = jest.fn(() => true);

// Mock the strategy control adapter
const mockToggleStrategy = jest.fn();
jest.mock('../../../services/strategyControlAdapter', () => ({
  strategyControlAdapter: {
    toggleStrategy: jest.fn(() => Promise.resolve({ success: true, data: { success: true } })),
  },
}));

// Mock react-toastify
jest.mock('react-toastify', () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
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

const mockStrategy: StrategyData = {
  id: 'test-strategy-1',
  name: '测试策略',
  isActive: false,
  status: 'inactive' as StrategyStatus,
  performance: {
    sharpeRatio: 1.5,
    maxDrawdown: 0.1,
    totalReturn: 0.25,
    winRate: 0.6,
  },
};

describe('StrategyToggleEnhanced', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  const renderComponent = (props = {}) => {
    const defaultProps = {
      strategyId: mockStrategy.id,
      strategyName: mockStrategy.name,
      isActive: mockStrategy.isActive,
      status: mockStrategy.status,
      onToggle: jest.fn(),
    };

    return render(
      <>
        <ToastContainer />
        <StrategyToggleEnhanced {...defaultProps} {...props} />
      </>
    );
  };

  it('renders strategy toggle correctly', () => {
    renderComponent();

    expect(screen.getByText('测试策略')).toBeInTheDocument();
    expect(screen.getByText('已禁用')).toBeInTheDocument();
    expect(screen.getByRole('switch')).toBeInTheDocument();
  });

  it('shows enabled state correctly', () => {
    renderComponent({
      isActive: true,
      status: 'active' as StrategyStatus,
    });

    expect(screen.getByText('已启用')).toBeInTheDocument();
    expect(screen.getByRole('switch')).toHaveAttribute('aria-checked', 'true');
  });

  it('handles toggle to enabled state', async () => {
    const { strategyControlAdapter } = require('../../../services/strategyControlAdapter');
    strategyControlAdapter.toggleStrategy.mockResolvedValue({
      success: true,
      data: { success: true },
    });

    const onToggle = jest.fn();
    renderComponent({ onToggle });

    const toggle = screen.getByRole('switch');
    fireEvent.click(toggle);

    await waitFor(() => {
      expect(strategyControlAdapter.toggleStrategy).toHaveBeenCalledWith(
        mockStrategy.id,
        true
      );
    });

    await waitFor(() => {
      expect(onToggle).toHaveBeenCalledWith(mockStrategy.id, true);
    });

    expect(screen.getByText('策略 "测试策略" 已成功启用')).toBeInTheDocument();
  });

  it('handles toggle to disabled state with confirmation', async () => {
    const { strategyControlAdapter } = require('../../../services/strategyControlAdapter');
    strategyControlAdapter.toggleStrategy.mockResolvedValue({
      success: true,
      data: { success: true },
    });

    // Mock window.confirm
    const originalConfirm = window.confirm;
    window.confirm = jest.fn(() => true);

    renderComponent({
      isActive: true,
      status: 'active' as StrategyStatus,
    });

    const toggle = screen.getByRole('switch');
    fireEvent.click(toggle);

    expect(window.confirm).toHaveBeenCalledWith(
      '确定要禁用策略 "测试策略" 吗？这将停止策略的所有运行和交易。'
    );

    await waitFor(() => {
      expect(strategyControlAdapter.toggleStrategy).toHaveBeenCalledWith(
        mockStrategy.id,
        false
      );
    });

    // Restore original confirm
    window.confirm = originalConfirm;
  });

  it('cancels toggle when confirmation is denied', async () => {
    const { strategyControlAdapter } = require('../../../services/strategyControlAdapter');
    strategyControlAdapter.toggleStrategy.mockResolvedValue({
      success: true,
      data: { success: true },
    });

    // Mock window.confirm to return false
    const originalConfirm = window.confirm;
    window.confirm = jest.fn(() => false);

    renderComponent({
      isActive: true,
      status: 'active' as StrategyStatus,
    });

    const toggle = screen.getByRole('switch');
    fireEvent.click(toggle);

    expect(window.confirm).toHaveBeenCalled();
    expect(strategyControlAdapter.toggleStrategy).not.toHaveBeenCalled();

    // Restore original confirm
    window.confirm = originalConfirm;
  });

  it('handles toggle error', async () => {
    const { strategyControlAdapter } = require('../../../services/strategyControlAdapter');
    strategyControlAdapter.toggleStrategy.mockResolvedValue({
      success: false,
      error: 'Network error',
    });

    const { toast } = require('react-toastify');
    renderComponent();

    const toggle = screen.getByRole('switch');
    fireEvent.click(toggle);

    await waitFor(() => {
      expect(strategyControlAdapter.toggleStrategy).toHaveBeenCalled();
    });

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith(
        '操作失败: Network error',
        expect.any(Object)
      );
    });
  });

  it('prevents multiple rapid toggles', async () => {
    const { strategyControlAdapter } = require('../../../services/strategyControlAdapter');
    strategyControlAdapter.toggleStrategy.mockImplementation(
      () => new Promise(resolve => setTimeout(() => resolve({ success: true }), 100))
    );

    renderComponent();

    const toggle = screen.getByRole('switch');
    fireEvent.click(toggle);
    fireEvent.click(toggle); // Second click should be ignored

    await waitFor(() => {
      expect(strategyControlAdapter.toggleStrategy).toHaveBeenCalledTimes(1);
    }, 200);
  });

  it('shows different status colors correctly', () => {
    const statuses: StrategyStatus[] = ['active', 'inactive', 'paused', 'stopped', 'error'];
    const colors = ['bg-green-500', 'bg-gray-400', 'bg-yellow-500', 'bg-red-500', 'bg-red-600'];

    statuses.forEach((status, index) => {
      const { unmount } = renderComponent({ status });
      const statusIndicator = document.querySelector('.rounded-full');
      expect(statusIndicator).toHaveClass(colors[index]);
      unmount();
    });
  });

  it('handles keyboard events', async () => {
    const { strategyControlAdapter } = require('../../../services/strategyControlAdapter');
    strategyControlAdapter.toggleStrategy.mockResolvedValue({
      success: true,
      data: { success: true },
    });

    renderComponent();

    const toggle = screen.getByRole('switch');
    fireEvent.keyDown(toggle, { key: 'Enter' });

    await waitFor(() => {
      expect(strategyControlAdapter.toggleStrategy).toHaveBeenCalledWith(
        mockStrategy.id,
        true
      );
    });
  });

  it('is disabled when disabled prop is true', () => {
    renderComponent({ disabled: true });

    const toggle = screen.getByRole('switch');
    expect(toggle).toBeDisabled();
    expect(toggle).toHaveClass('cursor-not-allowed');
  });

  it('shows loading state', async () => {
    const { strategyControlAdapter } = require('../../../services/strategyControlAdapter');
    strategyControlAdapter.toggleStrategy.mockImplementation(
      () => new Promise(resolve => setTimeout(() => resolve({ success: true }), 100))
    );

    renderComponent();

    const toggle = screen.getByRole('switch');
    fireEvent.click(toggle);

    // Check for loading state
    await waitFor(() => {
      expect(screen.getByText('处理中...')).toBeInTheDocument();
    });
  });

  it('hides labels when showLabels is false', () => {
    renderComponent({ showLabels: false });

    expect(screen.queryByText('测试策略')).not.toBeInTheDocument();
    expect(screen.queryByText('已禁用')).not.toBeInTheDocument();
  });

  it('applies size classes correctly', () => {
    const sizes = ['small', 'medium', 'large'];
    const scaleClasses = ['scale-75', 'scale-100', 'scale-125'];

    sizes.forEach((size, index) => {
      const { unmount } = renderComponent({ size: size as any });
      const switchElement = screen.getByRole('switch');
      expect(switchElement).toHaveClass(scaleClasses[index]);
      unmount();
    });
  });
});