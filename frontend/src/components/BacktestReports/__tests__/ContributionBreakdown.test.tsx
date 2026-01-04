import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import ContributionBreakdown from '../ContributionBreakdown';

// Mock recharts
jest.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  PieChart: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  Pie: () => <div data-testid="pie-chart" />,
  Cell: () => <div data-testid="cell" />,
  BarChart: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  Bar: () => <div data-testid="bar-chart" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  Legend: () => <div data-testid="legend" />
}));

describe('ContributionBreakdown', () => {
  const mockData = [
    { factor: 'Interest Rate Exposure', contribution: 0.085, weight: 0.45 },
    { factor: 'Inflation Hedge', contribution: 0.032, weight: 0.20 },
    { factor: 'Currency Impact', contribution: 0.023, weight: 0.15 },
    { factor: 'Market Timing', contribution: 0.016, weight: 0.20 }
  ];

  it('renders contribution breakdown correctly', () => {
    render(<ContributionBreakdown data={mockData} />);

    expect(screen.getByText('Performance Contribution Breakdown')).toBeInTheDocument();
    expect(screen.getByText('Interest Rate Exposure')).toBeInTheDocument();
    expect(screen.getByText('Inflation Hedge')).toBeInTheDocument();
  });

  it('displays contribution percentages correctly', () => {
    render(<ContributionBreakdown data={mockData} />);

    expect(screen.getByText('8.50%')).toBeInTheDocument(); // Interest Rate contribution
    expect(screen.getByText('3.20%')).toBeInTheDocument(); // Inflation Hedge contribution
  });

  it('shows weight distribution', () => {
    render(<ContributionBreakdown data={mockData} />);

    expect(screen.getByText('45.00%')).toBeInTheDocument(); // Interest Rate weight
    expect(screen.getByText('20.00%')).toBeInTheDocument(); // Inflation Hedge weight
  });

  it('renders pie chart for visualization', () => {
    render(<ContributionBreakdown data={mockData} />);

    expect(screen.getByTestId('pie-chart')).toBeInTheDocument();
    expect(screen.getByTestId('bar-chart')).toBeInTheDocument();
  });

  it('calculates total contribution correctly', () => {
    render(<ContributionBreakdown data={mockData} />);

    // Total should be 0.156 or 15.6%
    expect(screen.getByText('15.60%')).toBeInTheDocument();
  });

  it('applies different colors to factors', () => {
    render(<ContributionBreakdown data={mockData} />);

    const cells = screen.getAllByTestId('cell');
    expect(cells).toHaveLength(mockData.length);
  });

  it('shows contribution vs weight comparison', () => {
    render(<ContributionBreakdown data={mockData} />);

    expect(screen.getByText('Contribution vs Weight')).toBeInTheDocument();
    expect(screen.getByText('Effectiveness Ratio')).toBeInTheDocument();
  });

  it('handles empty data gracefully', () => {
    render(<ContributionBreakdown data={[]} />);

    expect(screen.getByText('No contribution data available')).toBeInTheDocument();
  });

  it('displays factor rankings', () => {
    render(<ContributionBreakdown data={mockData} />);

    expect(screen.getByText('#1')).toBeInTheDocument(); // Top contributor
    expect(screen.getByText('Interest Rate Exposure')).toBeInTheDocument(); // Should be ranked first
  });
});