"""
Standardized Performance Metrics Calculator for Unified Backtesting

Comprehensive metrics calculation system that ensures consistent and accurate
performance measurement across all trading strategies and parameter combinations.

Key Features:
- Standardized Sharpe Ratio calculation with configurable risk-free rate
- Maximum Drawdown calculation with drawdown periods analysis
- Comprehensive risk-adjusted return metrics (Calmar, Sortino, etc.)
- Trade statistics and performance attribution
- Benchmark comparison and relative performance analysis
- Monte Carlo simulation for performance validation
- Risk metrics (VaR, CVaR, volatility, beta)
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union, Any
from dataclasses import dataclass, asdict
import logging
from scipy import stats
import warnings

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Standardized performance metrics structure"""
    # Return Metrics
    total_return: float
    annualized_return: float
    cumulative_return: float

    # Risk-Adjusted Return Metrics
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    information_ratio: float
    treynor_ratio: float

    # Risk Metrics
    max_drawdown: float
    max_drawdown_duration: int
    volatility: float
    downside_volatility: float
    var_95: float
    cvar_95: float
    beta: float
    alpha: float

    # Trade Statistics
    trades_count: int
    win_rate: float
    profit_factor: float
    avg_win: float
    avg_loss: float
    best_trade: float
    worst_trade: float
    avg_trade_duration: float

    # Benchmark Comparison
    beta_to_benchmark: float
    alpha_to_benchmark: float
    correlation_to_benchmark: float
    tracking_error: float

    # Additional Metrics
    skewness: float
    kurtosis: float
    tail_ratio: float
    gain_to_pain_ratio: float
    recovery_factor: float

    # Validation Metrics
    stability_score: float
    consistency_score: float


class StandardizedMetricsCalculator:
    """
    Standardized calculator for performance metrics across all strategies

    Ensures consistent calculation methods and comparability across different
    trading strategies and parameter combinations.
    """

    def __init__(self, config=None):
        """Initialize metrics calculator"""
        if config is None:
            from ..core.config import DEFAULT_CONFIG
            config = DEFAULT_CONFIG

        self.config = config
        self.risk_free_rate = config.risk_free_rate
        self.trading_days_per_year = config.trading_days_per_year

        logger.info(f"Initialized StandardizedMetricsCalculator")
        logger.info(f"Risk-free rate: {self.risk_free_rate}, Trading days: {self.trading_days_per_year}")

    def calculate_comprehensive_metrics(self, returns: pd.Series,
                                      benchmark_returns: Optional[pd.Series] = None,
                                      positions: Optional[pd.Series] = None,
                                      trades: Optional[pd.DataFrame] = None) -> PerformanceMetrics:
        """
        Calculate comprehensive performance metrics

        Args:
            returns: Portfolio returns series
            benchmark_returns: Optional benchmark returns for comparison
            positions: Position series for trade analysis
            trades: Trade dataframe with detailed trade information

        Returns:
            PerformanceMetrics object with all calculated metrics
        """
        try:
            # Basic return calculations
            total_return, annualized_return, cumulative_return = self._calculate_return_metrics(returns)

            # Risk-adjusted return calculations
            sharpe_ratio, sortino_ratio, calmar_ratio, info_ratio, treynor_ratio = self._calculate_risk_adjusted_metrics(
                returns, benchmark_returns
            )

            # Risk calculations
            (max_dd, max_dd_duration, volatility, downside_vol,
             var_95, cvar_95, beta, alpha) = self._calculate_risk_metrics(returns, benchmark_returns)

            # Trade statistics
            trade_stats = self._calculate_trade_statistics(returns, positions, trades)

            # Benchmark comparison
            benchmark_stats = self._calculate_benchmark_comparison(returns, benchmark_returns)

            # Additional metrics
            additional_stats = self._calculate_additional_metrics(returns)

            # Validation metrics
            validation_stats = self._calculate_validation_metrics(returns)

            return PerformanceMetrics(
                total_return=total_return,
                annualized_return=annualized_return,
                cumulative_return=cumulative_return,

                sharpe_ratio=sharpe_ratio,
                sortino_ratio=sortino_ratio,
                calmar_ratio=calmar_ratio,
                information_ratio=info_ratio,
                treynor_ratio=treynor_ratio,

                max_drawdown=max_dd,
                max_drawdown_duration=max_dd_duration,
                volatility=volatility,
                downside_volatility=downside_vol,
                var_95=var_95,
                cvar_95=cvar_95,
                beta=beta,
                alpha=alpha,

                **trade_stats,

                **benchmark_stats,

                **additional_stats,

                **validation_stats
            )

        except Exception as e:
            logger.error(f"Error calculating metrics: {str(e)}")
            # Return empty metrics in case of error
            return self._get_empty_metrics()

    def _calculate_return_metrics(self, returns: pd.Series) -> Tuple[float, float, float]:
        """Calculate basic return metrics"""
        total_return = (1 + returns).prod() - 1
        cumulative_return = (1 + returns).cumprod() - 1

        # Annualized return
        years = len(returns) / self.trading_days_per_year
        annualized_return = (1 + total_return) ** (1/years) - 1 if years > 0 else 0

        return total_return, annualized_return, cumulative_return.iloc[-1] if len(cumulative_return) > 0 else 0

    def _calculate_risk_adjusted_metrics(self, returns: pd.Series,
                                       benchmark_returns: Optional[pd.Series] = None) -> Tuple[float, float, float, float, float]:
        """Calculate risk-adjusted return metrics"""
        # Sharpe Ratio (annualized)
        excess_returns = returns - self.risk_free_rate / self.trading_days_per_year
        sharpe_ratio = np.sqrt(self.trading_days_per_year) * excess_returns.mean() / returns.std() if returns.std() != 0 else 0

        # Sortino Ratio (downside deviation)
        downside_returns = returns[returns < 0]
        downside_std = downside_returns.std() if len(downside_returns) > 0 else 1
        sortino_ratio = np.sqrt(self.trading_days_per_year) * excess_returns.mean() / downside_std if downside_std != 0 else 0

        # Calmar Ratio (annualized return / max drawdown)
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()
        annualized_return = (1 + returns.sum()) ** (self.trading_days_per_year / len(returns)) - 1
        calmar_ratio = annualized_return / abs(max_drawdown) if max_drawdown != 0 else 0

        # Information Ratio (relative to benchmark)
        if benchmark_returns is not None:
            active_returns = returns - benchmark_returns
            information_ratio = np.sqrt(self.trading_days_per_year) * active_returns.mean() / active_returns.std() if active_returns.std() != 0 else 0
        else:
            information_ratio = 0

        # Treynor Ratio (requires beta calculation)
        if benchmark_returns is not None:
            beta = self._calculate_beta(returns, benchmark_returns)
            treynor_ratio = excess_returns.mean() * self.trading_days_per_year / beta if beta != 0 else 0
        else:
            treynor_ratio = 0

        return sharpe_ratio, sortino_ratio, calmar_ratio, information_ratio, treynor_ratio

    def _calculate_risk_metrics(self, returns: pd.Series,
                              benchmark_returns: Optional[pd.Series] = None) -> Tuple[float, int, float, float, float, float, float, float]:
        """Calculate risk metrics"""
        # Maximum Drawdown and Duration
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()

        # Drawdown duration
        in_drawdown = drawdown < 0
        drawdown_periods = []
        current_duration = 0
        max_duration = 0

        for is_dd in in_drawdown:
            if is_dd:
                current_duration += 1
                max_duration = max(max_duration, current_duration)
            else:
                if current_duration > 0:
                    drawdown_periods.append(current_duration)
                current_duration = 0

        max_drawdown_duration = max_duration

        # Volatility (annualized)
        volatility = returns.std() * np.sqrt(self.trading_days_per_year)

        # Downside volatility
        downside_returns = returns[returns < 0]
        downside_volatility = downside_returns.std() * np.sqrt(self.trading_days_per_year) if len(downside_returns) > 0 else 0

        # Value at Risk (95%)
        var_95 = returns.quantile(0.05)

        # Conditional Value at Risk (Expected Shortfall)
        var_95_threshold = var_95
        cvar_95 = returns[returns <= var_95_threshold].mean()

        # Beta and Alpha (relative to benchmark)
        if benchmark_returns is not None:
            beta = self._calculate_beta(returns, benchmark_returns)
            alpha = self._calculate_alpha(returns, benchmark_returns, beta)
        else:
            beta = 0
            alpha = 0

        return max_drawdown, max_drawdown_duration, volatility, downside_volatility, var_95, cvar_95, beta, alpha

    def _calculate_trade_statistics(self, returns: pd.Series,
                                  positions: Optional[pd.Series] = None,
                                  trades: Optional[pd.DataFrame] = None) -> Dict[str, float]:
        """Calculate trade statistics"""
        if trades is not None and not trades.empty:
            # Use provided trades dataframe
            trades_count = len(trades)
            winning_trades = trades[trades['pnl'] > 0]
            losing_trades = trades[trades['pnl'] <= 0]

            win_rate = len(winning_trades) / trades_count if trades_count > 0 else 0

            avg_win = winning_trades['pnl'].mean() if len(winning_trades) > 0 else 0
            avg_loss = losing_trades['pnl'].mean() if len(losing_trades) > 0 else 0

            total_wins = winning_trades['pnl'].sum() if len(winning_trades) > 0 else 0
            total_losses = abs(losing_trades['pnl'].sum()) if len(losing_trades) > 0 else 1
            profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')

            best_trade = trades['pnl'].max() if trades_count > 0 else 0
            worst_trade = trades['pnl'].min() if trades_count > 0 else 0

            # Calculate average trade duration if duration data available
            if 'duration' in trades.columns:
                avg_trade_duration = trades['duration'].mean()
            else:
                avg_trade_duration = 0

        else:
            # Estimate from returns series
            # Simple threshold-based trade identification
            threshold = 0.001  # 0.1% threshold
            trade_signals = (returns.abs() > threshold).astype(int)
            trades_count = trade_signals.sum() // 2  # Approximate number of round trips

            positive_returns = returns[returns > 0]
            negative_returns = returns[returns < 0]

            win_rate = len(positive_returns) / len(returns[returns != 0]) if len(returns[returns != 0]) > 0 else 0

            avg_win = positive_returns.mean() if len(positive_returns) > 0 else 0
            avg_loss = negative_returns.mean() if len(negative_returns) > 0 else 0

            total_wins = positive_returns.sum() if len(positive_returns) > 0 else 0
            total_losses = abs(negative_returns.sum()) if len(negative_returns) > 0 else 1
            profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')

            best_trade = returns.max() if len(returns) > 0 else 0
            worst_trade = returns.min() if len(returns) > 0 else 0
            avg_trade_duration = 1  # Default assumption

        return {
            'trades_count': trades_count,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'best_trade': best_trade,
            'worst_trade': worst_trade,
            'avg_trade_duration': avg_trade_duration
        }

    def _calculate_benchmark_comparison(self, returns: pd.Series,
                                      benchmark_returns: Optional[pd.Series] = None) -> Dict[str, float]:
        """Calculate benchmark comparison metrics"""
        if benchmark_returns is None or len(benchmark_returns) == 0:
            return {
                'beta_to_benchmark': 0,
                'alpha_to_benchmark': 0,
                'correlation_to_benchmark': 0,
                'tracking_error': 0
            }

        # Align series
        common_index = returns.index.intersection(benchmark_returns.index)
        if len(common_index) == 0:
            return {
                'beta_to_benchmark': 0,
                'alpha_to_benchmark': 0,
                'correlation_to_benchmark': 0,
                'tracking_error': 0
            }

        aligned_returns = returns.loc[common_index]
        aligned_benchmark = benchmark_returns.loc[common_index]

        # Beta calculation
        beta_to_benchmark = self._calculate_beta(aligned_returns, aligned_benchmark)

        # Alpha calculation
        alpha_to_benchmark = self._calculate_alpha(aligned_returns, aligned_benchmark, beta_to_benchmark)

        # Correlation
        correlation_to_benchmark = aligned_returns.corr(aligned_benchmark)

        # Tracking Error
        active_returns = aligned_returns - aligned_benchmark
        tracking_error = active_returns.std() * np.sqrt(self.trading_days_per_year)

        return {
            'beta_to_benchmark': beta_to_benchmark,
            'alpha_to_benchmark': alpha_to_benchmark,
            'correlation_to_benchmark': correlation_to_benchmark,
            'tracking_error': tracking_error
        }

    def _calculate_additional_metrics(self, returns: pd.Series) -> Dict[str, float]:
        """Calculate additional performance metrics"""
        # Skewness and Kurtosis
        skewness = stats.skew(returns.dropna())
        kurtosis = stats.kurtosis(returns.dropna())

        # Tail Ratio (95th percentile / 5th percentile)
        tail_ratio = abs(returns.quantile(0.95)) / abs(returns.quantile(0.05)) if returns.quantile(0.05) != 0 else float('inf')

        # Gain to Pain Ratio (positive returns / absolute negative returns)
        positive_returns = returns[returns > 0].sum()
        negative_returns = abs(returns[returns < 0].sum())
        gain_to_pain_ratio = positive_returns / negative_returns if negative_returns > 0 else float('inf')

        # Recovery Factor (total return / max drawdown)
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = abs(drawdown.min())
        total_return = cumulative.iloc[-1] - 1
        recovery_factor = total_return / max_drawdown if max_drawdown > 0 else float('inf')

        return {
            'skewness': skewness,
            'kurtosis': kurtosis,
            'tail_ratio': tail_ratio,
            'gain_to_pain_ratio': gain_to_pain_ratio,
            'recovery_factor': recovery_factor
        }

    def _calculate_validation_metrics(self, returns: pd.Series) -> Dict[str, float]:
        """Calculate validation metrics for strategy robustness"""
        # Stability Score (rolling sharpe ratio consistency)
        rolling_window = min(63, len(returns) // 4)  # Quarter of data or 3 months
        if len(returns) >= rolling_window:
            rolling_sharpe = returns.rolling(window=rolling_window).apply(
                lambda x: np.sqrt(252) * x.mean() / x.std() if x.std() > 0 else 0
            )
            stability_score = 1 - (rolling_sharpe.std() / abs(rolling_sharpe.mean())) if rolling_sharpe.mean() != 0 else 0
        else:
            stability_score = 0

        # Consistency Score (positive return periods)
        positive_periods = (returns > 0).sum()
        total_periods = len(returns)
        consistency_score = positive_periods / total_periods if total_periods > 0 else 0

        return {
            'stability_score': max(0, stability_score),
            'consistency_score': consistency_score
        }

    def _calculate_beta(self, returns: pd.Series, benchmark_returns: pd.Series) -> float:
        """Calculate beta relative to benchmark"""
        if len(returns) < 2 or len(benchmark_returns) < 2:
            return 0

        # Calculate covariance and variance
        covariance = np.cov(returns.dropna(), benchmark_returns.dropna())[0][1]
        benchmark_variance = np.var(benchmark_returns.dropna())

        return covariance / benchmark_variance if benchmark_variance != 0 else 0

    def _calculate_alpha(self, returns: pd.Series, benchmark_returns: pd.Series, beta: float) -> float:
        """Calculate alpha relative to benchmark"""
        if len(returns) < 1 or len(benchmark_returns) < 1:
            return 0

        # Annualized returns
        portfolio_return = returns.mean() * self.trading_days_per_year
        benchmark_return = benchmark_returns.mean() * self.trading_days_per_year

        # Alpha = Portfolio Return - (Risk Free Rate + Beta * (Benchmark Return - Risk Free Rate))
        alpha = portfolio_return - (self.risk_free_rate + beta * (benchmark_return - self.risk_free_rate))

        return alpha

    def _get_empty_metrics(self) -> PerformanceMetrics:
        """Return empty PerformanceMetrics for error cases"""
        return PerformanceMetrics(
            total_return=0.0, annualized_return=0.0, cumulative_return=0.0,
            sharpe_ratio=0.0, sortino_ratio=0.0, calmar_ratio=0.0,
            information_ratio=0.0, treynor_ratio=0.0,
            max_drawdown=0.0, max_drawdown_duration=0, volatility=0.0,
            downside_volatility=0.0, var_95=0.0, cvar_95=0.0,
            beta=0.0, alpha=0.0, trades_count=0, win_rate=0.0,
            profit_factor=0.0, avg_win=0.0, avg_loss=0.0,
            best_trade=0.0, worst_trade=0.0, avg_trade_duration=0.0,
            beta_to_benchmark=0.0, alpha_to_benchmark=0.0,
            correlation_to_benchmark=0.0, tracking_error=0.0,
            skewness=0.0, kurtosis=0.0, tail_ratio=0.0,
            gain_to_pain_ratio=0.0, recovery_factor=0.0,
            stability_score=0.0, consistency_score=0.0
        )

    def run_monte_carlo_simulation(self, returns: pd.Series,
                                 num_simulations: int = 1000) -> Dict[str, float]:
        """
        Run Monte Carlo simulation to validate strategy performance

        Args:
            returns: Historical returns
            num_simulations: Number of Monte Carlo simulations

        Returns:
            Dictionary with simulation statistics
        """
        try:
            # Generate random scenarios using historical returns
            simulated_results = []

            for _ in range(num_simulations):
                # Randomly sample from historical returns
                simulated_returns = np.random.choice(returns, size=len(returns), replace=True)
                sim_portfolio = (1 + simulated_returns).cumprod()

                # Calculate metrics for simulation
                sim_return = sim_portfolio[-1] - 1
                sim_max_dd = self._calculate_max_drawdown(sim_portfolio)

                simulated_results.append({
                    'return': sim_return,
                    'max_drawdown': sim_max_dd,
                    'sharpe': self._calculate_simple_sharpe(simulated_returns)
                })

            # Calculate statistics from simulations
            sim_df = pd.DataFrame(simulated_results)

            return {
                'mean_return': sim_df['return'].mean(),
                'std_return': sim_df['return'].std(),
                'percentile_5_return': sim_df['return'].quantile(0.05),
                'percentile_95_return': sim_df['return'].quantile(0.95),
                'mean_max_drawdown': sim_df['max_drawdown'].mean(),
                'std_max_drawdown': sim_df['max_drawdown'].std(),
                'mean_sharpe': sim_df['sharpe'].mean(),
                'probability_positive_return': (sim_df['return'] > 0).mean(),
                'probability_sharpe_above_1': (sim_df['sharpe'] > 1).mean()
            }

        except Exception as e:
            logger.error(f"Error in Monte Carlo simulation: {str(e)}")
            return {}

    def _calculate_max_drawdown(self, portfolio_values: np.ndarray) -> float:
        """Calculate maximum drawdown for portfolio values"""
        running_max = np.maximum.accumulate(portfolio_values)
        drawdown = (portfolio_values - running_max) / running_max
        return drawdown.min()

    def _calculate_simple_sharpe(self, returns: np.ndarray) -> float:
        """Calculate simple Sharpe ratio"""
        if len(returns) < 2 or returns.std() == 0:
            return 0
        return np.sqrt(252) * returns.mean() / returns.std()