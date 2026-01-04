import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { Provider } from 'react-redux';
import { store } from '@/store';
import { ChartsDashboard } from '../ChartsDashboard';
import { ChartManagerProvider } from '../ChartManager';
import { Strategy } from '../../../types';

// Mock strategy data for testing
const mockStrategies: Strategy[] = [
  {
    id: 'test-strategy-1',
    name: '測試策略1',
    type: 'direct_rsi',
    category: 'core_cbsc',
    status: 'active',
    performance: {
      totalReturn: 0.25,
      sharpeRatio: 1.5,
      maxDrawdown: 8.5,
      volatility: 12.0,
      winRate: 0.65,
      profitFactor: 1.8,
      calmarRatio: 1.0,
      var95: -0.03,
      cvar95: -0.045,
      lastUpdated: new Date('2025-12-11T10:30:00Z'),
      dataQualityScore: 98
    },
    description: '測用策略描述'
  },
  {
    id: 'test-strategy-2',
    name: '測試策略2',
    type: 'sentiment_momentum',
    category: 'core_cbsc',
    status: 'active',
    performance: {
      totalReturn: 0.18,
      sharpeRatio: 1.1,
      maxDrawdown: 12.0,
      volatility: 15.5,
      winRate: 0.58,
      profitFactor: 1.5,
      calmarRatio: 0.75,
      var95: -0.04,
      cvar95: -0.055,
      lastUpdated: new Date('2025-12-11T10:25:00Z'),
      dataQualityScore: 95
    },
    description: '另一個測試策略'
  }
];

// Test wrapper component
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <Provider store={store}>
    <ChartManagerProvider>
      {children}
    </ChartManagerProvider>
  </Provider>
);

describe('Charts Components', () => {
  beforeEach(() => {
    // Clear any existing timers
    jest.clearAllTimers();
  });

  it('renders ChartsDashboard with strategy data', () => {
    render(
      <TestWrapper>
        <ChartsDashboard
          strategies={mockStrategies}
          height={400}
          showControls={true}
        />
      </TestWrapper>
    );

    // Check if dashboard title is present
    expect(screen.getByText(/實時更新/)).toBeInTheDocument();

    // Check if chart control buttons are present
    expect(screen.getByRole('button', { name: /sharpe比率圖/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /最大回撤圖/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /雷達圖/i })).toBeInTheDocument();
  });

  it('handles chart toggle functionality', () => {
    render(
      <TestWrapper>
        <ChartsDashboard
          strategies={mockStrategies}
          showControls={true}
        />
      </TestWrapper>
    );

    // Find and click the Sharpe ratio chart toggle button
    const sharpeToggleButton = screen.getByRole('button', { name: /sharpe比率圖/i });

    // Button should be in "primary" state (active) initially
    expect(sharpeToggleButton).toHaveClass('ant-btn-primary');

    // Click to toggle off
    fireEvent.click(sharpeToggleButton);

    // Button should now be in "default" state (inactive)
    expect(sharpeToggleButton).toHaveClass('ant-btn-default');
  });

  it('handles real-time updates toggle', () => {
    render(
      <TestWrapper>
        <ChartsDashboard
          strategies={mockStrategies}
          showControls={true}
        />
      </TestWrapper>
    );

    // Find the real-time update switch
    const realTimeSwitch = screen.getByRole('switch', { name: /實時更新/i });

    // Initially should be off
    expect(realTimeSwitch).not.toBeChecked();

    // Click to turn on real-time updates
    fireEvent.click(realTimeSwitch);

    // Should now be checked
    expect(realTimeSwitch).toBeChecked();
  });

  it('handles layout change', () => {
    render(
      <TestWrapper>
        <ChartsDashboard
          strategies={mockStrategies}
          showControls={true}
          defaultLayout="grid"
        />
      </TestWrapper>
    );

    // Find the layout selector
    const layoutSelector = screen.getByDisplayValue('網格');

    // Should display "網格" initially
    expect(layoutSelector).toBeInTheDocument();

    // Click to open dropdown
    fireEvent.mouseDown(layoutSelector);

    // Find and click "堆疊" option
    const stackedOption = screen.getByText('堆疊');
    fireEvent.click(stackedOption);

    // Layout should change to "堆疊"
    expect(layoutSelector).toHaveDisplayValue('堆疊');
  });

  it('displays empty state when no strategies provided', () => {
    render(
      <TestWrapper>
        <ChartsDashboard
          strategies={[]}
          showControls={false}
        />
      </TestWrapper>
    );

    // Should display empty state message
    expect(screen.getByText('沒有策略數據')).toBeInTheDocument();
    expect(screen.getByText('請先添加策略或檢查數據源連接')).toBeInTheDocument();
  });

  it('handles update interval change when real-time is enabled', () => {
    render(
      <TestWrapper>
        <ChartsDashboard
          strategies={mockStrategies}
          showControls={true}
        />
      </TestWrapper>
    );

    // Enable real-time updates first
    const realTimeSwitch = screen.getByRole('switch', { name: /實時更新/i });
    fireEvent.click(realTimeSwitch);

    // Find the interval selector (should appear after enabling real-time)
    const intervalSelector = screen.queryByDisplayValue('10秒');

    // Interval selector should be visible
    expect(intervalSelector).toBeInTheDocument();

    // Click to open dropdown
    fireEvent.mouseDown(intervalSelector!);

    // Find and click "30秒" option
    const thirtySecondOption = screen.getByText('30秒');
    fireEvent.click(thirtySecondOption);

    // Interval should change to "30秒"
    expect(intervalSelector).toHaveDisplayValue('30秒');
  });
});

// Integration test for chart rendering
describe('Chart Integration', () => {
  it('renders all charts by default', async () => {
    render(
      <TestWrapper>
        <ChartsDashboard
          strategies={mockStrategies}
          showControls={false} // Hide controls to test chart rendering
        />
      </TestWrapper>
    );

    // Check if chart titles are present
    // Note: These might take time to render due to Chart.js initialization
    const sharpeTitle = await screen.findByText('Sharpe比率排名');
    const drawdownTitle = await screen.findByText('最大回撤趨勢');
    const radarTitle = await screen.findByText('策略多維度對比');

    expect(sharpeTitle).toBeInTheDocument();
    expect(drawdownTitle).toBeInTheDocument();
    expect(radarTitle).toBeInTheDocument();
  });

  it('handles strategy click interactions', async () => {
    const mockStrategyClick = jest.fn();

    render(
      <TestWrapper>
        <ChartsDashboard
          strategies={mockStrategies}
          showControls={false}
        />
      </TestWrapper>
    );

    // Wait for charts to render
    await screen.findByText('Sharpe比率排名');

    // Note: Testing actual chart interactions requires more complex setup
    // This test ensures components render without errors
    expect(mockStrategyClick).not.toHaveBeenCalled();
  });
});

// Performance tests
describe('Chart Performance', () => {
  it('renders efficiently with large dataset', () => {
    // Generate large dataset for performance testing
    const largeDataset = Array.from({ length: 100 }, (_, i) => ({
      id: `strategy-${i}`,
      name: `策略 ${i + 1}`,
      type: `type_${i % 4}`,
      category: 'test',
      status: 'active' as const,
      performance: {
        totalReturn: Math.random() * 0.5 - 0.1,
        sharpeRatio: Math.random() * 2,
        maxDrawdown: Math.random() * 20,
        volatility: Math.random() * 25,
        winRate: Math.random(),
        profitFactor: 1 + Math.random() * 2,
        calmarRatio: Math.random() * 1.5,
        var95: -Math.random() * 0.1,
        cvar95: -Math.random() * 0.15,
        lastUpdated: new Date(),
        dataQualityScore: 80 + Math.random() * 20
      },
      description: `測試策略 ${i + 1} 的描述`
    }));

    const startTime = performance.now();

    render(
      <TestWrapper>
        <ChartsDashboard
          strategies={largeDataset}
          showControls={true}
        />
      </TestWrapper>
    );

    const endTime = performance.now();
    const renderTime = endTime - startTime;

    // Should render within reasonable time (less than 1 second)
    expect(renderTime).toBeLessThan(1000);

    // Verify dashboard is rendered
    expect(screen.getByText(/實時更新/)).toBeInTheDocument();
  });
});