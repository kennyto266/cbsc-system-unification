"""
Enhanced Risk Metrics for CBSC Backtest System
Calculates advanced risk metrics for portfolio analysis
"""
import numpy as np
import pandas as pd
from typing import Dict, Optional, Tuple, Union
from scipy import stats
from arch import arch_model
import warnings

warnings.filterwarnings('ignore')


class EnhancedRiskMetrics:
    """
    Calculate enhanced risk metrics for backtest analysis
    """

    def __init__(self, risk_free_rate: float = 0.02):
        """
        Initialize EnhancedRiskMetrics

        Args:
            risk_free_rate: Annual risk-free rate (default: 2%)
        """
        self.risk_free_rate = risk_free_rate

    def calculate_all_metrics(
        self,
        returns: pd.Series,
        benchmark_returns: Optional[pd.Series] = None,
        periods_per_year: int = 252
    ) -> Dict[str, float]:
        """
        Calculate all enhanced risk metrics

        Args:
            returns: Portfolio returns series
            benchmark_returns: Benchmark returns series (optional)
            periods_per_year: Number of trading periods per year

        Returns:
            Dict[str, float]: Dictionary of all risk metrics
        """
        metrics = {}

        # Basic metrics
        metrics.update(self._calculate_basic_metrics(returns, periods_per_year))

        # Enhanced metrics
        metrics['calmar_ratio'] = self.calmar_ratio(returns, periods_per_year)
        metrics['sortino_ratio'] = self.sortino_ratio(returns, periods_per_year)
        metrics['information_ratio'] = self.information_ratio(returns, benchmark_returns, periods_per_year)
        metrics['treynor_ratio'] = self.treynor_ratio(returns, periods_per_year)
        metrics['jensen_alpha'] = self.jensen_alpha(returns, benchmark_returns, periods_per_year)

        # Drawdown metrics
        dd_analysis = self.drawdown_analysis(returns)
        metrics.update(dd_analysis)

        # Distribution metrics
        dist_metrics = self._calculate_distribution_metrics(returns)
        metrics.update(dist_metrics)

        # VaR and CVaR
        var_metrics = self._calculate_var_cvar(returns)
        metrics.update(var_metrics)

        return metrics

    def _calculate_basic_metrics(self, returns: pd.Series, periods_per_year: int) -> Dict[str, float]:
        """Calculate basic risk metrics"""
        total_return = (1 + returns).prod() - 1
        annual_return = (1 + total_return) ** (periods_per_year / len(returns)) - 1
        annual_volatility = returns.std() * np.sqrt(periods_per_year)
        sharpe_ratio = (annual_return - self.risk_free_rate) / annual_volatility if annual_volatility > 0 else 0

        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'annual_volatility': annual_volatility,
            'sharpe_ratio': sharpe_ratio
        }

    def calmar_ratio(self, returns: pd.Series, periods_per_year: int = 252) -> float:
        """
        Calculate Calmar Ratio (Annual Return / Maximum Drawdown)

        Args:
            returns: Returns series
            periods_per_year: Number of periods per year

        Returns:
            float: Calmar Ratio
        """
        annual_return = (1 + returns).prod() ** (periods_per_year / len(returns)) - 1
        max_dd = self.max_drawdown(returns)

        return annual_return / abs(max_dd) if max_dd != 0 else 0

    def sortino_ratio(
        self,
        returns: pd.Series,
        periods_per_year: int = 252,
        target_return: float = 0
    ) -> float:
        """
        Calculate Sortino Ratio (Return / Downside Deviation)

        Args:
            returns: Returns series
            periods_per_year: Number of periods per year
            target_return: Target/minimum acceptable return

        Returns:
            float: Sortino Ratio
        """
        excess_returns = returns - target_return / periods_per_year
        downside_returns = excess_returns[excess_returns < 0]

        if len(downside_returns) == 0:
            return np.inf

        downside_deviation = np.sqrt((downside_returns ** 2).mean()) * np.sqrt(periods_per_year)
        annual_return = returns.mean() * periods_per_year

        return (annual_return - self.risk_free_rate) / downside_deviation if downside_deviation > 0 else 0

    def information_ratio(
        self,
        returns: pd.Series,
        benchmark_returns: Optional[pd.Series],
        periods_per_year: int = 252
    ) -> float:
        """
        Calculate Information Ratio (Active Return / Tracking Error)

        Args:
            returns: Portfolio returns
            benchmark_returns: Benchmark returns
            periods_per_year: Number of periods per year

        Returns:
            float: Information Ratio
        """
        if benchmark_returns is None:
            return 0

        # Align series
        returns, benchmark_returns = returns.align(benchmark_returns, join='inner')
        active_returns = returns - benchmark_returns

        tracking_error = active_returns.std() * np.sqrt(periods_per_year)
        active_return = active_returns.mean() * periods_per_year

        return active_return / tracking_error if tracking_error > 0 else 0

    def treynor_ratio(
        self,
        returns: pd.Series,
        periods_per_year: int = 252,
        benchmark_returns: Optional[pd.Series] = None
    ) -> float:
        """
        Calculate Treynor Ratio (Excess Return / Beta)

        Args:
            returns: Portfolio returns
            periods_per_year: Number of periods per year
            benchmark_returns: Benchmark returns for beta calculation

        Returns:
            float: Treynor Ratio
        """
        if benchmark_returns is None:
            return 0

        # Calculate beta
        beta = self._calculate_beta(returns, benchmark_returns)
        if beta == 0:
            return 0

        annual_return = returns.mean() * periods_per_year
        excess_return = annual_return - self.risk_free_rate

        return excess_return / beta

    def jensen_alpha(
        self,
        returns: pd.Series,
        benchmark_returns: Optional[pd.Series],
        periods_per_year: int = 252
    ) -> float:
        """
        Calculate Jensen's Alpha

        Args:
            returns: Portfolio returns
            benchmark_returns: Benchmark returns
            periods_per_year: Number of periods per year

        Returns:
            float: Jensen's Alpha
        """
        if benchmark_returns is None:
            return 0

        # Align series
        returns, benchmark_returns = returns.align(benchmark_returns, join='inner')

        # Calculate parameters
        portfolio_annual = returns.mean() * periods_per_year
        benchmark_annual = benchmark_returns.mean() * periods_per_year
        beta = self._calculate_beta(returns, benchmark_returns)

        # Jensen's Alpha = Portfolio Return - (Risk Free + Beta * (Benchmark Return - Risk Free))
        expected_return = self.risk_free_rate + beta * (benchmark_annual - self.risk_free_rate)
        alpha = portfolio_annual - expected_return

        return alpha

    def _calculate_beta(self, returns: pd.Series, benchmark_returns: pd.Series) -> float:
        """Calculate beta coefficient"""
        # Align series
        returns, benchmark_returns = returns.align(benchmark_returns, join='inner')

        # Calculate covariance and variance
        covariance = np.cov(returns, benchmark_returns)[0, 1]
        variance = np.var(benchmark_returns)

        return covariance / variance if variance != 0 else 0

    def max_drawdown(self, returns: pd.Series) -> float:
        """
        Calculate Maximum Drawdown

        Args:
            returns: Returns series

        Returns:
            float: Maximum drawdown (negative value)
        """
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max

        return drawdown.min()

    def drawdown_analysis(self, returns: pd.Series) -> Dict[str, float]:
        """
        Comprehensive drawdown analysis

        Args:
            returns: Returns series

        Returns:
            Dict[str, float]: Drawdown metrics
        """
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max

        # Find drawdown periods
        in_drawdown = drawdown < 0
        drawdown_periods = []
        start_dd = None

        for i, is_dd in enumerate(in_drawdown):
            if is_dd and start_dd is None:
                start_dd = i
            elif not is_dd and start_dd is not None:
                drawdown_periods.append((start_dd, i - 1))
                start_dd = None

        # Handle case where we end in drawdown
        if start_dd is not None:
            drawdown_periods.append((start_dd, len(in_drawdown) - 1))

        # Calculate metrics
        max_dd = drawdown.min()
        avg_dd = drawdown[drawdown < 0].mean() if (drawdown < 0).any() else 0
        max_dd_duration = max((end - start + 1 for start, end in drawdown_periods), default=0)

        return {
            'max_drawdown': max_dd,
            'avg_drawdown': avg_dd,
            'max_drawdown_duration': max_dd_duration,
            'drawdown_periods': len(drawdown_periods)
        }

    def _calculate_distribution_metrics(self, returns: pd.Series) -> Dict[str, float]:
        """Calculate distribution-related metrics"""
        return {
            'skewness': stats.skew(returns),
            'kurtosis': stats.kurtosis(returns),
            'jarque_bera': stats.jarque_bera(returns)[0],
            'jarque_bera_pvalue': stats.jarque_bera(returns)[1]
        }

    def _calculate_var_cvar(self, returns: pd.Series, confidence_levels: list = [0.95, 0.99]) -> Dict[str, float]:
        """
        Calculate Value at Risk (VaR) and Conditional VaR

        Args:
            returns: Returns series
            confidence_levels: List of confidence levels

        Returns:
            Dict[str, float]: VaR and CVaR metrics
        """
        metrics = {}

        for confidence in confidence_levels:
            # Historical VaR
            var_historical = np.percentile(returns, (1 - confidence) * 100)
            metrics[f'var_{int(confidence*100)}_historical'] = var_historical

            # Parametric VaR (assuming normal distribution)
            mean = returns.mean()
            std = returns.std()
            var_parametric = mean - stats.norm.ppf(confidence) * std
            metrics[f'var_{int(confidence*100)}_parametric'] = var_parametric

            # CVaR (Expected Shortfall)
            cvar = returns[returns <= var_historical].mean()
            metrics[f'cvar_{int(confidence*100)}'] = cvar

        return metrics

    def calculate_omega_ratio(
        self,
        returns: pd.Series,
        threshold: float = 0,
        periods_per_year: int = 252
    ) -> float:
        """
        Calculate Omega Ratio

        Args:
            returns: Returns series
            threshold: Threshold return (annualized)
            periods_per_year: Number of periods per year

        Returns:
            float: Omega Ratio
        """
        threshold_period = threshold / periods_per_year

        gains = returns[returns > threshold_period] - threshold_period
        losses = threshold_period - returns[returns <= threshold_period]

        if len(losses) == 0:
            return np.inf

        return gains.sum() / losses.sum()

    def calculate_upside_capture(
        self,
        returns: pd.Series,
        benchmark_returns: pd.Series
    ) -> float:
        """
        Calculate Upside Capture Ratio

        Args:
            returns: Portfolio returns
            benchmark_returns: Benchmark returns

        Returns:
            float: Upside Capture Ratio
        """
        # Align series
        returns, benchmark_returns = returns.align(benchmark_returns, join='inner')

        upside_portfolio = returns[benchmark_returns > 0].mean()
        upside_benchmark = benchmark_returns[benchmark_returns > 0].mean()

        return (upside_portfolio / upside_benchmark) if upside_benchmark != 0 else 0

    def calculate_downside_capture(
        self,
        returns: pd.Series,
        benchmark_returns: pd.Series
    ) -> float:
        """
        Calculate Downside Capture Ratio

        Args:
            returns: Portfolio returns
            benchmark_returns: Benchmark returns

        Returns:
            float: Downside Capture Ratio
        """
        # Align series
        returns, benchmark_returns = returns.align(benchmark_returns, join='inner')

        downside_portfolio = returns[benchmark_returns < 0].mean()
        downside_benchmark = benchmark_returns[benchmark_returns < 0].mean()

        return (downside_portfolio / downside_benchmark) if downside_benchmark != 0 else 0

    def calculate_gain_loss_ratio(self, returns: pd.Series) -> float:
        """
        Calculate Gain-to-Loss Ratio

        Args:
            returns: Returns series

        Returns:
            float: Gain-to-Loss Ratio
        """
        gains = returns[returns > 0]
        losses = returns[returns < 0]

        if len(losses) == 0:
            return np.inf if len(gains) > 0 else 0

        return gains.mean() / abs(losses.mean())

    def calculate_win_rate(self, returns: pd.Series) -> float:
        """
        Calculate Win Rate

        Args:
            returns: Returns series

        Returns:
            float: Win Rate (0 to 1)
        """
        wins = (returns > 0).sum()
        total = len(returns)

        return wins / total if total > 0 else 0

    def calculate_profit_factor(self, returns: pd.Series) -> float:
        """
        Calculate Profit Factor

        Args:
            returns: Returns series

        Returns:
            float: Profit Factor
        """
        gross_profit = returns[returns > 0].sum()
        gross_loss = abs(returns[returns < 0].sum())

        return gross_profit / gross_loss if gross_loss != 0 else np.inf

    def rolling_metrics(
        self,
        returns: pd.Series,
        window: int = 252,
        periods_per_year: int = 252
    ) -> pd.DataFrame:
        """
        Calculate rolling risk metrics

        Args:
            returns: Returns series
            window: Rolling window size
            periods_per_year: Number of periods per year

        Returns:
            pd.DataFrame: Rolling metrics
        """
        rolling_metrics = pd.DataFrame(index=returns.index)

        # Rolling Sharpe
        rolling_mean = returns.rolling(window).mean() * periods_per_year
        rolling_std = returns.rolling(window).std() * np.sqrt(periods_per_year)
        rolling_metrics['rolling_sharpe'] = (rolling_mean - self.risk_free_rate) / rolling_std

        # Rolling Sortino
        downside_returns = returns.copy()
        downside_returns[downside_returns > 0] = 0
        rolling_downside_std = downside_returns.rolling(window).std() * np.sqrt(periods_per_year)
        rolling_metrics['rolling_sortino'] = (rolling_mean - self.risk_free_rate) / rolling_downside_std

        # Rolling Max Drawdown
        rolling_cumulative = (1 + returns).rolling(window).apply(lambda x: (1 + x).cumprod().iloc[-1])
        rolling_max = rolling_cumulative.rolling(window).expanding().max()
        rolling_metrics['rolling_max_dd'] = (rolling_cumulative - rolling_max) / rolling_max

        return rolling_metrics.dropna()