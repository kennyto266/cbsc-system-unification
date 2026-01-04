import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import PerformanceMetrics from '../PerformanceMetrics';

describe('PerformanceMetrics', () => {
  const mockMetrics = {
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
  };

  it('renders all performance metrics correctly', () => {
    render(<PerformanceMetrics metrics={mockMetrics} />);

    expect(screen.getByText('Performance Metrics')).toBeInTheDocument();
    // Check key metrics are rendered
    expect(screen.getByText('Total Return')).toBeInTheDocument();
    expect(screen.getByText('Sharpe Ratio')).toBeInTheDocument();
    expect(screen.getByText('Max Drawdown')).toBeInTheDocument();
  });

  it('applies correct color coding based on metric values', () => {
    const { container } = render(<PerformanceMetrics metrics={mockMetrics} />);

    // Check for Max Drawdown label and verify its value exists
    const drawdownLabel = screen.getByText('Max Drawdown');
    const drawdownCard = drawdownLabel.closest('.bg-white');
    expect(drawdownCard).toBeInTheDocument();
    expect(drawdownCard?.textContent).toContain('-8.20%');

    // Check for Sharpe ratio label and verify its value exists
    const sharpeLabel = screen.getByText('Sharpe Ratio');
    const sharpeCard = sharpeLabel.closest('.bg-white');
    expect(sharpeCard).toBeInTheDocument();
    expect(sharpeCard?.textContent).toContain('1.45');

    // Check that color classes are applied (icons have color classes)
    expect(container.querySelector('.text-green-600')).toBeInTheDocument();
    expect(container.querySelector('.text-red-600')).toBeInTheDocument();
  });

  it('shows metric descriptions on hover', () => {
    render(<PerformanceMetrics metrics={mockMetrics} />);

    // Check if description elements exist
    expect(screen.getByText('Total portfolio return')).toBeInTheDocument();
    expect(screen.getByText('Risk-adjusted return measure')).toBeInTheDocument();
    expect(screen.getByText('Maximum peak-to-trough decline')).toBeInTheDocument();
  });

  it('handles edge cases gracefully', () => {
    const edgeCaseMetrics = {
      ...mockMetrics,
      totalReturn: 0,
      sharpeRatio: 0,
      maxDrawdown: 0
    };

    render(<PerformanceMetrics metrics={edgeCaseMetrics} />);

    // Check that zero values are rendered
    const totalReturnLabel = screen.getByText('Total Return');
    expect(totalReturnLabel.closest('.bg-white')?.textContent).toContain('0.00%');
  });

  it('formats currency values correctly', () => {
    render(<PerformanceMetrics metrics={mockMetrics} />);

    expect(screen.getByText('$1,251')).toBeInTheDocument(); // Average win (rounded)
    expect(screen.getByText('($675)')).toBeInTheDocument(); // Average loss (rounded)
  });

  it('displays win rate and profit factor correctly', () => {
    render(<PerformanceMetrics metrics={mockMetrics} />);

    // Check for Win Rate label to find the specific metric
    const winRateLabel = screen.getByText('Win Rate');
    const winRateCard = winRateLabel.closest('.bg-white');
    expect(winRateCard).toBeInTheDocument();
    expect(winRateCard?.textContent).toContain('62.00%');

    expect(screen.getByText('1.85')).toBeInTheDocument(); // Profit factor
  });

  it('displays performance summary section', () => {
    render(<PerformanceMetrics metrics={mockMetrics} />);

    expect(screen.getByText('Performance Summary')).toBeInTheDocument();
    expect(screen.getByText(/This strategy achieved/)).toBeInTheDocument();
    expect(screen.getByText(/with a Sharpe ratio of/)).toBeInTheDocument();
  });

  it('shows warning for low Sharpe ratio', () => {
    const lowSharpeMetrics = {
      ...mockMetrics,
      sharpeRatio: 0.85
    };

    render(<PerformanceMetrics metrics={lowSharpeMetrics} />);

    expect(screen.getByText(/The Sharpe ratio is below 1.0/)).toBeInTheDocument();
  });

  it('shows warning for high drawdown', () => {
    const highDrawdownMetrics = {
      ...mockMetrics,
      maxDrawdown: -0.20
    };

    render(<PerformanceMetrics metrics={highDrawdownMetrics} />);

    expect(screen.getByText(/The maximum drawdown exceeds 15%/)).toBeInTheDocument();
  });
});
