import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import EconomicBacktestReports from '../EconomicBacktestReports';

// Mock recharts
jest.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  LineChart: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  Line: () => <div data-testid="line-chart" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  Legend: () => <div data-testid="legend" />,
  BarChart: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  Bar: () => <div data-testid="bar-chart" />,
  Cell: () => <div data-testid="cell" />,
  PieChart: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  Pie: () => <div data-testid="pie-chart" />,
  RadarChart: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  Radar: () => <div data-testid="radar-chart" />,
  PolarGrid: () => <div data-testid="polar-grid" />,
  PolarAngleAxis: () => <div data-testid="polar-angle-axis" />,
  PolarRadiusAxis: () => <div data-testid="polar-radius-axis" />,
  ScatterChart: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  Scatter: () => <div data-testid="scatter-chart" />,
  ComposedChart: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  Area: () => <div data-testid="area-chart" />
}));

// Mock subcomponents
jest.mock('../PerformanceMetrics', () => {
  return function MockPerformanceMetrics({ metrics }: { metrics: any }) {
    return <div data-testid="performance-metrics">{JSON.stringify(metrics)}</div>;
  };
});

jest.mock('../CorrelationAnalysis', () => {
  return function MockCorrelationAnalysis({ data }: { data: any }) {
    return <div data-testid="correlation-analysis">{JSON.stringify(data)}</div>;
  };
});

jest.mock('../ContributionBreakdown', () => {
  return function MockContributionBreakdown({ data }: { data: any }) {
    return <div data-testid="contribution-breakdown">{JSON.stringify(data)}</div>;
  };
});

describe('EconomicBacktestReports', () => {
  const mockReport = {
    id: 'test-report-1',
    strategyName: 'Interest Rate Strategy',
    strategy: {
      name: 'Interest Rate Differential',
      category: 'economic',
      parameters: {
        interestRateThreshold: 0.02,
        lookbackPeriod: 30
      }
    },
    period: {
      start: '2023-01-01',
      end: '2024-01-01',
      duration: 365
    },
    metrics: {
      totalReturn: 0.156,
      annualizedReturn: 0.156,
      maxDrawdown: -0.082,
      sharpeRatio: 1.45,
      sortinoRatio: 2.03,
      calmarRatio: 1.90,
      volatility: 0.145,
      winRate: 0.62,
      profitFactor: 1.85,
      averageWin: 1250.50,
      averageLoss: -675.30,
      totalTrades: 48,
      winningTrades: 30,
      losingTrades: 18
    },
    economicData: {
      indicators: [
        { name: 'Fed Funds Rate', values: [4.5, 4.75, 5.0, 5.25, 5.5] },
        { name: 'CPI YoY', values: [3.2, 3.5, 3.8, 4.0, 3.9] },
        { name: 'Unemployment Rate', values: [3.6, 3.7, 3.8, 3.9, 4.0] }
      ],
      correlation: {
        'Fed Funds Rate': 0.65,
        'CPI YoY': -0.32,
        'Unemployment Rate': -0.48
      }
    },
    strategyComparison: [
      {
        name: 'Interest Rate Strategy',
        totalReturn: 0.156,
        sharpeRatio: 1.45,
        maxDrawdown: -0.082,
        correlation: 1.0
      },
      {
        name: 'Momentum Strategy',
        totalReturn: 0.098,
        sharpeRatio: 0.87,
        maxDrawdown: -0.156,
        correlation: 0.34
      },
      {
        name: 'Value Strategy',
        totalReturn: 0.112,
        sharpeRatio: 0.95,
        maxDrawdown: -0.124,
        correlation: 0.42
      }
    ],
    contributionBreakdown: [
      { factor: 'Interest Rate Exposure', contribution: 0.085, weight: 0.45 },
      { factor: 'Inflation Hedge', contribution: 0.032, weight: 0.20 },
      { factor: 'Currency Impact', contribution: 0.023, weight: 0.15 },
      { factor: 'Market Timing', contribution: 0.016, weight: 0.20 }
    ],
    equityCurve: Array.from({ length: 12 }, (_, i) => ({
      date: `2023-${String(i + 1).padStart(2, '0')}-01`,
      portfolioValue: 100000 * (1 + 0.156 * (i + 1) / 12),
      benchmarkValue: 100000 * (1 + 0.089 * (i + 1) / 12)
    })),
    trades: Array.from({ length: 10 }, (_, i) => ({
      date: `2023-${String(Math.floor(i / 2) + 1).padStart(2, '0')}-${String((i % 2) * 15 + 1).padStart(2, '0')}`,
      type: i % 2 === 0 ? 'buy' : 'sell',
      price: 100 + i * 5,
      quantity: 100,
      profit: i % 2 === 1 ? 250 * (i / 2) : undefined,
      profitPercent: i % 2 === 1 ? 0.025 * (i / 2) : undefined
    })),
    generatedAt: '2024-01-02T10:00:00Z'
  };

  it('renders economic backtest report correctly', async () => {
    render(<EconomicBacktestReports report={mockReport} />);

    expect(screen.getByText('Economic Strategy Backtest Report')).toBeInTheDocument();
    expect(screen.getByText('Interest Rate Strategy')).toBeInTheDocument();
    expect(screen.getByText('2023/1/1 - 2024/1/1')).toBeInTheDocument();
  });

  it('displays performance metrics tab by default', async () => {
    render(<EconomicBacktestReports report={mockReport} />);

    expect(screen.getByTestId('performance-metrics')).toBeInTheDocument();
    expect(screen.getByText('15.60%')).toBeInTheDocument(); // Total return
    expect(screen.getByText('1.45')).toBeInTheDocument(); // Sharpe ratio
  });

  it('switches tabs correctly', async () => {
    render(<EconomicBacktestReports report={mockReport} />);

    // Click correlation analysis tab
    const correlationTab = screen.getByText('Correlation Analysis');
    correlationTab.click();

    await waitFor(() => {
      expect(screen.getByTestId('correlation-analysis')).toBeInTheDocument();
    });

    // Click contribution breakdown tab
    const contributionTab = screen.getByText('Contributions');
    contributionTab.click();

    await waitFor(() => {
      expect(screen.getByTestId('contribution-breakdown')).toBeInTheDocument();
    });

    // Click strategy comparison tab
    const comparisonTab = screen.getByText('Strategy Comparison');
    comparisonTab.click();

    await waitFor(() => {
      expect(screen.getByText('Compare with other strategies')).toBeInTheDocument();
    });
  });

  it('displays economic indicators correctly', async () => {
    render(<EconomicBacktestReports report={mockReport} />);

    expect(screen.getByText('Fed Funds Rate')).toBeInTheDocument();
    expect(screen.getByText('CPI YoY')).toBeInTheDocument();
    expect(screen.getByText('Unemployment Rate')).toBeInTheDocument();
  });

  it('shows export functionality', async () => {
    render(<EconomicBacktestReports report={mockReport} />);

    const exportButton = screen.getByText('Export Report');
    expect(exportButton).toBeInTheDocument();

    exportButton.click();

    await waitFor(() => {
      expect(screen.getByText('Export Format')).toBeInTheDocument();
      expect(screen.getByText('PDF Report')).toBeInTheDocument();
      expect(screen.getByText('Excel Data')).toBeInTheDocument();
    });
  });

  it('handles strategy comparison data', async () => {
    render(<EconomicBacktestReports report={mockReport} />);

    const comparisonTab = screen.getByText('Strategy Comparison');
    comparisonTab.click();

    await waitFor(() => {
      expect(screen.getByText('Momentum Strategy')).toBeInTheDocument();
      expect(screen.getByText('Value Strategy')).toBeInTheDocument();
      expect(screen.getByText('9.80%')).toBeInTheDocument(); // Momentum return
    });
  });

  it('displays contribution breakdown correctly', async () => {
    render(<EconomicBacktestReports report={mockReport} />);

    const contributionTab = screen.getByText('Contributions');
    contributionTab.click();

    await waitFor(() => {
      expect(screen.getByTestId('contribution-breakdown')).toBeInTheDocument();
    });
  });

  it('formats dates and numbers correctly', () => {
    render(<EconomicBacktestReports report={mockReport} />);

    // Check date formatting
    expect(screen.getByText('Generated: 2024/1/2 上午10:00:00')).toBeInTheDocument();

    // Check number formatting
    expect(screen.getByText('$1,250.50')).toBeInTheDocument(); // Average win
    expect(screen.getByText('48')).toBeInTheDocument(); // Total trades
  });

  it('handles empty economic data gracefully', () => {
    const reportWithNoEconomicData = {
      ...mockReport,
      economicData: {
        indicators: [],
        correlation: {}
      }
    };

    render(<EconomicBacktestReports report={reportWithNoEconomicData} />);

    expect(screen.getByText('No economic data available')).toBeInTheDocument();
  });

  it('handles missing comparison data gracefully', () => {
    const reportWithNoComparison = {
      ...mockReport,
      strategyComparison: []
    };

    render(<EconomicBacktestReports report={reportWithNoComparison} />);

    const comparisonTab = screen.getByText('Strategy Comparison');
    comparisonTab.click();

    expect(screen.getByText('No comparison strategies available')).toBeInTheDocument();
  });
});