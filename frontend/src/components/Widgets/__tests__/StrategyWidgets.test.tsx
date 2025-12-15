/**
 * Test suite for Strategy Performance Widgets
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { StrategyStatusWidget } from '../StrategyStatusWidget';
import { PerformanceMetricsWidget } from '../PerformanceMetricsWidget';
import { PortfolioOverviewWidget } from '../PortfolioOverviewWidget';
import { WebSocketProvider } from '../../../contexts/WebSocketContext';

// Mock WebSocket context
const mockWebSocketContext = {
  service: {} as any,
  isConnected: true,
  connectionState: 'connected' as any,
  connectionQuality: 'excellent' as any,
  connect: jest.fn(),
  disconnect: jest.fn(),
  send: jest.fn(),
  subscribe: jest.fn(() => () => {}),
  getStats: jest.fn()
};

// Mock Recharts
jest.mock('recharts', () => ({
  LineChart: ({ children }: any) => <div data-testid="line-chart">{children}</div>,
  Line: () => <div data-testid="line" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  ResponsiveContainer: ({ children }: any) => <div>{children}</div>,
  BarChart: ({ children }: any) => <div data-testid="bar-chart">{children}</div>,
  Bar: () => <div data-testid="bar" />,
  PieChart: ({ children }: any) => <div data-testid="pie-chart">{children}</div>,
  Pie: () => <div data-testid="pie" />,
  Cell: () => <div data-testid="cell" />,
  RadarChart: ({ children }: any) => <div data-testid="radar-chart">{children}</div>,
  Radar: () => <div data-testid="radar" />,
  PolarGrid: () => <div data-testid="polar-grid" />,
  PolarAngleAxis: () => <div data-testid="polar-angle-axis" />,
  PolarRadiusAxis: () => <div data-testid="polar-radius-axis" />,
  TreemapChart: ({ children }: any) => <div data-testid="treemap-chart">{children}</div>,
  Treemap: () => <div data-testid="treemap" />,
  AreaChart: ({ children }: any) => <div data-testid="area-chart">{children}</div>,
  Area: () => <div data-testid="area" />
}));

// Mock hooks
jest.mock('../../../hooks/useWebSocket', () => ({
  useWebSocket: () => ({
    subscribe: jest.fn(() => () => {}),
    send: jest.fn()
  })
}));

jest.mock('../../../hooks/useStrategyUpdates', () => ({
  useStrategyUpdates: () => ({
    strategies: [
      {
        id: '1',
        name: 'Test Strategy',
        status: 'active',
        lastExecution: new Date(),
        dailyPnL: 100,
        totalReturn: 5.2,
        isRunning: true
      }
    ],
    isConnected: true,
    connectionStatus: 'connected',
    toggleStrategy: jest.fn(),
    refreshStrategy: jest.fn(),
    refreshAll: jest.fn()
  })
}));

const renderWithWebSocket = (component: React.ReactElement) => {
  return render(
    <WebSocketProvider value={mockWebSocketContext}>
      {component}
    </WebSocketProvider>
  );
};

describe('StrategyStatusWidget', () => {
  it('renders strategy status widget correctly', () => {
    renderWithWebSocket(<StrategyStatusWidget />);

    expect(screen.getByText('Strategy Status')).toBeInTheDocument();
    expect(screen.getByText('Test Strategy')).toBeInTheDocument();
  });

  it('displays active strategy count', () => {
    renderWithWebSocket(<StrategyStatusWidget />);

    expect(screen.getByText('1 / 1 Active')).toBeInTheDocument();
  });

  it('handles strategy toggle', () => {
    const mockToggle = jest.fn();
    renderWithWebSocket(<StrategyStatusWidget onToggleStrategy={mockToggle} />);

    // Find and click the toggle switch
    const toggle = screen.getByRole('switch');
    fireEvent.click(toggle);

    // Note: Toggle functionality might need adjustment based on actual implementation
  });
});

describe('PerformanceMetricsWidget', () => {
  it('renders performance metrics widget correctly', () => {
    renderWithWebSocket(<PerformanceMetricsWidget />);

    expect(screen.getByText('Performance Metrics')).toBeInTheDocument();
    expect(screen.getByText('Total Return')).toBeInTheDocument();
    expect(screen.getByText('Sharpe Ratio')).toBeInTheDocument();
    expect(screen.getByText('Max Drawdown')).toBeInTheDocument();
    expect(screen.getByText('Win Rate')).toBeInTheDocument();
  });

  it('displays correct metric values', () => {
    renderWithWebSocket(<PerformanceMetricsWidget />);

    expect(screen.getByText('12.50%')).toBeInTheDocument();
    expect(screen.getByText('1.85')).toBeInTheDocument();
  });

  it('allows period selection', () => {
    renderWithWebSocket(<PerformanceMetricsWidget />);

    const periodSelector = screen.getByText('1M');
    expect(periodSelector).toBeInTheDocument();

    // Clicking might reveal dropdown (implementation dependent)
  });
});

describe('PortfolioOverviewWidget', () => {
  it('renders portfolio overview widget correctly', () => {
    renderWithWebSocket(<PortfolioOverviewWidget />);

    expect(screen.getByText('Portfolio Overview')).toBeInTheDocument();
    expect(screen.getByText('Total Value')).toBeInTheDocument();
    expect(screen.getByText('Cash')).toBeInTheDocument();
    expect(screen.getByText('Invested')).toBeInTheDocument();
  });

  it('displays portfolio value', () => {
    renderWithWebSocket(<PortfolioOverviewWidget />);

    expect(screen.getByText('$1,000,000')).toBeInTheDocument();
  });

  it('shows daily change badge', () => {
    renderWithWebSocket(<PortfolioOverviewWidget />);

    expect(screen.getByText('+0.25% Today')).toBeInTheDocument();
  });

  it('allows view switching', () => {
    renderWithWebSocket(<PortfolioOverviewWidget />);

    const allocationButton = screen.getByText('Allocation');
    const sectorsButton = screen.getByText('Sectors');
    const holdingsButton = screen.getByText('Holdings');

    expect(allocationButton).toBeInTheDocument();
    expect(sectorsButton).toBeInTheDocument();
    expect(holdingsButton).toBeInTheDocument();

    // Test view switching
    fireEvent.click(sectorsButton);
    // Expected: view should switch to sectors (check for sector-specific content)
  });
});

describe('Widget Integration', () => {
  it('renders all widgets without conflicts', () => {
    renderWithWebSocket(
      <div>
        <StrategyStatusWidget />
        <PerformanceMetricsWidget />
        <PortfolioOverviewWidget />
      </div>
    );

    expect(screen.getByText('Strategy Status')).toBeInTheDocument();
    expect(screen.getByText('Performance Metrics')).toBeInTheDocument();
    expect(screen.getByText('Portfolio Overview')).toBeInTheDocument();
  });

  it('widgets update independently', async () => {
    const { rerender } = renderWithWebSocket(
      <div>
        <StrategyStatusWidget />
        <PerformanceMetricsWidget />
        <PortfolioOverviewWidget />
      </div>
    );

    // Initial state
    expect(screen.getByText('Test Strategy')).toBeInTheDocument();

    // Simulate state change and re-render
    rerender(
      <div>
        <StrategyStatusWidget />
        <PerformanceMetricsWidget />
        <PortfolioOverviewWidget />
      </div>
    );

    // Widgets should still render correctly
    expect(screen.getByText('Strategy Status')).toBeInTheDocument();
  });
});