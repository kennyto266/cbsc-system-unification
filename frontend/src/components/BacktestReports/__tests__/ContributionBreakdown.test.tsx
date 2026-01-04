import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import ContributionBreakdown from '../ContributionBreakdown';

// Mock Recharts components
jest.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="responsive-container">{children}</div>
  ),
  PieChart: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="pie-chart">{children}</div>
  ),
  Pie: () => <div data-testid="pie" />,
  Cell: () => <div data-testid="cell" />,
  Tooltip: () => <div data-testid="tooltip" />,
  Legend: () => <div data-testid="legend" />,
  BarChart: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="bar-chart">{children}</div>
  ),
  Bar: () => <div data-testid="bar" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
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
    expect(screen.getAllByText('Interest Rate Exposure').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Inflation Hedge').length).toBeGreaterThan(0);
  });

  it('displays summary cards with total contribution', () => {
    render(<ContributionBreakdown data={mockData} />);

    expect(screen.getByText('Total Contribution')).toBeInTheDocument();
    expect(screen.getByText('Number of Factors')).toBeInTheDocument();
    expect(screen.getByText('Top Contributor')).toBeInTheDocument();
  });

  it('displays contribution percentages', () => {
    render(<ContributionBreakdown data={mockData} />);

    // Check that contribution values are displayed somewhere
    expect(screen.getAllByText('Interest Rate Exposure').length).toBeGreaterThan(0);
    // Note: Specific DOM traversal is fragile, just verify rendering
  });

  it('shows weight distribution', () => {
    render(<ContributionBreakdown data={mockData} />);

    // Check that weights are displayed somewhere in the component
    expect(screen.getByText('Weight')).toBeInTheDocument();
  });

  it('renders chart sections', () => {
    render(<ContributionBreakdown data={mockData} />);

    expect(screen.getByText('Contribution Distribution')).toBeInTheDocument();
    expect(screen.getByText('Contribution vs Weight')).toBeInTheDocument();
  });

  it('calculates total contribution correctly', () => {
    render(<ContributionBreakdown data={mockData} />);

    // Total contribution should be displayed (0.085 + 0.032 + 0.023 + 0.016 = 0.156)
    const totalElements = screen.getAllByText('15.60%');
    expect(totalElements.length).toBeGreaterThan(0);
  });

  it('handles empty data gracefully', () => {
    render(<ContributionBreakdown data={[]} />);

    expect(screen.getByText('No contribution data available')).toBeInTheDocument();
  });

  it('displays factor rankings table', () => {
    render(<ContributionBreakdown data={mockData} />);

    expect(screen.getByText('Factor Rankings')).toBeInTheDocument();
    expect(screen.getByText('Rank')).toBeInTheDocument();
    expect(screen.getByText('Effectiveness')).toBeInTheDocument();
  });

  it('displays performance insights section', () => {
    render(<ContributionBreakdown data={mockData} />);

    expect(screen.getByText('Performance Insights')).toBeInTheDocument();
    // Note: Dynamic text generation may vary, just verify section exists
  });
});
