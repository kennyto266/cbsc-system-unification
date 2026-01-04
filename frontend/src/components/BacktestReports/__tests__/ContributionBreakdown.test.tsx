import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import ContributionBreakdown from '../ContributionBreakdown';

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

  it('displays summary cards with total contribution', () => {
    render(<ContributionBreakdown data={mockData} />);

    expect(screen.getByText('Total Contribution')).toBeInTheDocument();
    expect(screen.getByText('Number of Factors')).toBeInTheDocument();
    expect(screen.getByText('Top Contributor')).toBeInTheDocument();
  });

  it('displays contribution percentages', () => {
    render(<ContributionBreakdown data={mockData} />);

    // Check that contribution values are displayed
    const interestRateCard = screen.getByText('Interest Rate Exposure').closest('.bg-white');
    expect(interestRateCard?.textContent).toContain('8.50%');
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
    expect(screen.getByText(/The top contributing factor is/)).toBeInTheDocument();
  });
});
