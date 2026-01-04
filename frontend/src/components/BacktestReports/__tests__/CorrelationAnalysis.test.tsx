import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import CorrelationAnalysis from '../CorrelationAnalysis';

// Mock recharts
jest.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  ScatterChart: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  Scatter: () => <div data-testid="scatter-chart" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  Legend: () => <div data-testid="legend" />,
  Cell: () => <div data-testid="cell" />,
  BarChart: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  Bar: () => <div data-testid="bar-chart" />
}));

describe('CorrelationAnalysis', () => {
  const mockData = {
    economicIndicators: [
      {
        name: 'Fed Funds Rate',
        values: [4.5, 4.75, 5.0, 5.25, 5.5],
        dates: ['2023-01-01', '2023-02-01', '2023-03-01', '2023-04-01', '2023-05-01']
      },
      {
        name: 'CPI YoY',
        values: [3.2, 3.5, 3.8, 4.0, 3.9],
        dates: ['2023-01-01', '2023-02-01', '2023-03-01', '2023-04-01', '2023-05-01']
      },
      {
        name: 'Unemployment Rate',
        values: [3.6, 3.7, 3.8, 3.9, 4.0],
        dates: ['2023-01-01', '2023-02-01', '2023-03-01', '2023-04-01', '2023-05-01']
      }
    ],
    strategyReturns: [0.02, 0.015, 0.025, 0.01, 0.018],
    correlationMatrix: {
      'Fed Funds Rate': 0.65,
      'CPI YoY': -0.32,
      'Unemployment Rate': -0.48
    }
  };

  it('renders correlation analysis correctly', () => {
    render(<CorrelationAnalysis data={mockData} />);

    expect(screen.getByText('Economic Data Correlation Analysis')).toBeInTheDocument();
    expect(screen.getByText('Fed Funds Rate')).toBeInTheDocument();
    expect(screen.getByText('CPI YoY')).toBeInTheDocument();
    expect(screen.getByText('Unemployment Rate')).toBeInTheDocument();
  });

  it('displays correlation values correctly', () => {
    render(<CorrelationAnalysis data={mockData} />);

    expect(screen.getByText('0.65')).toBeInTheDocument(); // Fed Funds Rate correlation
    expect(screen.getByText('-0.32')).toBeInTheDocument(); // CPI correlation
    expect(screen.getByText('-0.48')).toBeInTheDocument(); // Unemployment correlation
  });

  it('applies correct color coding for correlation strength', () => {
    render(<CorrelationAnalysis data={mockData} />);

    // Strong positive correlation should be green
    const fedCorrelation = screen.getByText('0.65');
    expect(fedCorrelation.closest('div')).toHaveClass('text-green-600');

    // Negative correlations should be red
    const cpiCorrelation = screen.getByText('-0.32');
    expect(cpiCorrelation.closest('div')).toHaveClass('text-red-600');
  });

  it('shows correlation interpretation', () => {
    render(<CorrelationAnalysis data={mockData} />);

    expect(screen.getByText('Strong Positive')).toBeInTheDocument();
    expect(screen.getByText('Moderate Negative')).toBeInTheDocument();
  });

  it('renders scatter chart for correlation visualization', () => {
    render(<CorrelationAnalysis data={mockData} />);

    expect(screen.getByTestId('scatter-chart')).toBeInTheDocument();
  });

  it('handles empty data gracefully', () => {
    const emptyData = {
      economicIndicators: [],
      strategyReturns: [],
      correlationMatrix: {}
    };

    render(<CorrelationAnalysis data={emptyData} />);

    expect(screen.getByText('No correlation data available')).toBeInTheDocument();
  });

  it('displays correlation heatmap', () => {
    render(<CorrelationAnalysis data={mockData} />);

    expect(screen.getByText('Correlation Heatmap')).toBeInTheDocument();
    expect(screen.getByTestId('bar-chart')).toBeInTheDocument();
  });

  it('shows statistical significance indicators', () => {
    render(<CorrelationAnalysis data={mockData} />);

    expect(screen.getByText('Statistical Significance')).toBeInTheDocument();
    expect(screen.getByText('p < 0.05')).toBeInTheDocument();
  });
});