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
    expect(screen.getByText('15.60%')).toBeInTheDocument(); // Total return
    expect(screen.getByText('1.45')).toBeInTheDocument(); // Sharpe ratio
    expect(screen.getByText('-8.20%')).toBeInTheDocument(); // Max drawdown
  });

  it('applies correct color coding based on metric values', () => {
    render(<PerformanceMetrics metrics={mockMetrics} />);

    // Positive returns should be green
    const totalReturn = screen.getByText('15.60%');
    expect(totalReturn).toHaveClass('text-green-600');

    // Negative drawdown should be red
    const maxDrawdown = screen.getByText('-8.20%');
    expect(maxDrawdown).toHaveClass('text-red-600');

    // Good Sharpe ratio should be green
    const sharpeRatio = screen.getByText('1.45');
    expect(sharpeRatio).toHaveClass('text-green-600');
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

    expect(screen.getByText('0.00%')).toBeInTheDocument(); // Zero return
    expect(screen.getByText('0.00')).toBeInTheDocument(); // Zero Sharpe
  });

  it('formats currency values correctly', () => {
    render(<PerformanceMetrics metrics={mockMetrics} />);

    expect(screen.getByText('$1,250.50')).toBeInTheDocument(); // Average win
    expect(screen.getByText('($675.30)')).toBeInTheDocument(); // Average loss
  });

  it('displays win rate and profit factor correctly', () => {
    render(<PerformanceMetrics metrics={mockMetrics} />);

    expect(screen.getByText('62.00%')).toBeInTheDocument(); // Win rate
    expect(screen.getByText('1.85')).toBeInTheDocument(); // Profit factor
  });
});