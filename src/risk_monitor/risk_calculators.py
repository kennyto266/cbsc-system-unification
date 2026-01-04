"""
Core risk calculation algorithms

This module implements various risk metrics calculations including:
- Value at Risk (VaR)
- Expected Shortfall (ES)
- Maximum Drawdown
- Volatility calculations
- Correlation analysis
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional, Union
from datetime import datetime, timedelta
import logging
from scipy import stats
from sklearn.covariance import LedoitWolf

logger = logging.getLogger(__name__)


class VaRCalculator:
    """Value at Risk Calculator"""

    def __init__(self, confidence_levels: List[float] = [0.95, 0.99]):
        """
        Initialize VaR calculator

        Args:
            confidence_levels: List of confidence levels for VaR calculation
        """
        self.confidence_levels = confidence_levels
        self.methods = ["historical", "parametric", "monte_carlo"]

    def calculate_historical_var(
        self,
        returns: pd.Series,
        confidence_level: float = 0.95,
        window: Optional[int] = None
    ) -> float:
        """
        Calculate historical VaR

        Args:
            returns: Portfolio returns series
            confidence_level: Confidence level (e.g., 0.95 for 95% VaR)
            window: Rolling window size (None for full history)

        Returns:
            VaR value
        """
        if window is not None:
            returns = returns.tail(window)

        # Historical VaR is the quantile of returns
        var = np.percentile(returns, (1 - confidence_level) * 100)
        return abs(var)

    def calculate_parametric_var(
        self,
        returns: pd.Series,
        confidence_level: float = 0.95,
        distribution: str = "normal"
    ) -> float:
        """
        Calculate parametric VaR

        Args:
            returns: Portfolio returns series
            confidence_level: Confidence level
            distribution: Distribution assumption ("normal" or "t")

        Returns:
            VaR value
        """
        mean = returns.mean()
        std = returns.std()

        if distribution == "normal":
            z_score = stats.norm.ppf(1 - confidence_level)
            var = mean - z_score * std
        elif distribution == "t":
            # Estimate degrees of freedom
            df = self._estimate_t_df(returns)
            t_score = stats.t.ppf(1 - confidence_level, df)
            var = mean - t_score * std * np.sqrt((df - 2) / df)
        else:
            raise ValueError(f"Unsupported distribution: {distribution}")

        return abs(var)

    def calculate_monte_carlo_var(
        self,
        returns: pd.Series,
        confidence_level: float = 0.95,
        n_simulations: int = 10000,
        time_horizon: int = 1
    ) -> float:
        """
        Calculate Monte Carlo VaR

        Args:
            returns: Portfolio returns series
            confidence_level: Confidence level
            n_simulations: Number of Monte Carlo simulations
            time_horizon: Time horizon in days

        Returns:
            VaR value
        """
        mean = returns.mean()
        std = returns.std()

        # Generate random scenarios
        scenarios = np.random.normal(
            mean * time_horizon,
            std * np.sqrt(time_horizon),
            n_simulations
        )

        var = np.percentile(scenarios, (1 - confidence_level) * 100)
        return abs(var)

    def calculate_conditional_var(
        self,
        returns: pd.Series,
        confidence_level: float = 0.95,
        lookback: int = 20
    ) -> pd.Series:
        """
        Calculate conditional VaR (rolling)

        Args:
            returns: Portfolio returns series
            confidence_level: Confidence level
            lookback: Lookback window for conditional VaR

        Returns:
            Rolling VaR series
        """
        rolling_var = returns.rolling(lookback).apply(
            lambda x: self.calculate_historical_var(x, confidence_level),
            raw=False
        )
        return rolling_var

    def _estimate_t_df(self, returns: pd.Series) -> float:
        """Estimate degrees of freedom for t-distribution"""
        params = stats.t.fit(returns)
        return params[0]


class ExpectedShortfallCalculator:
    """Expected Shortfall (Conditional VaR) Calculator"""

    def __init__(self, confidence_levels: List[float] = [0.95, 0.97, 0.99]):
        """
        Initialize ES calculator

        Args:
            confidence_levels: List of confidence levels
        """
        self.confidence_levels = confidence_levels

    def calculate_historical_es(
        self,
        returns: pd.Series,
        confidence_level: float = 0.95,
        window: Optional[int] = None
    ) -> float:
        """
        Calculate historical Expected Shortfall

        Args:
            returns: Portfolio returns series
            confidence_level: Confidence level
            window: Rolling window size

        Returns:
            Expected Shortfall value
        """
        if window is not None:
            returns = returns.tail(window)

        # Calculate VaR threshold
        var_threshold = np.percentile(returns, (1 - confidence_level) * 100)

        # ES is mean of returns beyond VaR threshold
        tail_returns = returns[returns <= var_threshold]
        es = tail_returns.mean()

        return abs(es)

    def calculate_parametric_es(
        self,
        returns: pd.Series,
        confidence_level: float = 0.95,
        distribution: str = "normal"
    ) -> float:
        """
        Calculate parametric Expected Shortfall

        Args:
            returns: Portfolio returns series
            confidence_level: Confidence level
            distribution: Distribution assumption

        Returns:
            Expected Shortfall value
        """
        mean = returns.mean()
        std = returns.std()

        if distribution == "normal":
            z_score = stats.norm.ppf(1 - confidence_level)
            # For normal distribution, ES = sigma * phi(z) / (1 - Phi(z))
            phi_z = stats.norm.pdf(z_score)
            es = mean - std * phi_z / (1 - confidence_level)
        elif distribution == "t":
            df = self._estimate_t_df(returns)
            t_score = stats.t.ppf(1 - confidence_level, df)
            # For t-distribution
            phi_t = stats.t.pdf(t_score, df)
            es = mean - std * np.sqrt((df - 2) / df) * \
                 (phi_t * (df + t_score**2) / ((df - 1) * (1 - confidence_level)))
        else:
            raise ValueError(f"Unsupported distribution: {distribution}")

        return abs(es)

    def _estimate_t_df(self, returns: pd.Series) -> float:
        """Estimate degrees of freedom for t-distribution"""
        params = stats.t.fit(returns)
        return params[0]


class MaxDrawdownCalculator:
    """Maximum Drawdown Calculator"""

    def __init__(self, window: int = 252):
        """
        Initialize max drawdown calculator

        Args:
            window: Default window for calculation (trading days)
        """
        self.window = window

    def calculate_max_drawdown(
        self,
        prices: pd.Series,
        window: Optional[int] = None
    ) -> Dict[str, float]:
        """
        Calculate maximum drawdown and related metrics

        Args:
            prices: Price series
            window: Calculation window

        Returns:
            Dictionary containing drawdown metrics
        """
        if window is not None:
            prices = prices.tail(window)

        # Calculate cumulative returns
        cumulative = (1 + prices.pct_change()).cumprod()

        # Calculate running maximum (peak)
        running_max = cumulative.expanding().max()

        # Calculate drawdown
        drawdown = (cumulative - running_max) / running_max

        # Maximum drawdown
        max_dd = drawdown.min()

        # Maximum drawdown duration
        dd_duration = self._calculate_drawdown_duration(drawdown)

        # Recovery time
        recovery_time = self._calculate_recovery_time(drawdown)

        return {
            "max_drawdown": abs(max_dd),
            "max_drawdown_duration": dd_duration,
            "recovery_time": recovery_time,
            "current_drawdown": abs(drawdown.iloc[-1]) if len(drawdown) > 0 else 0
        }

    def calculate_rolling_max_drawdown(
        self,
        prices: pd.Series,
        window: int = 252
    ) -> pd.Series:
        """
        Calculate rolling maximum drawdown

        Args:
            prices: Price series
            window: Rolling window size

        Returns:
            Rolling max drawdown series
        """
        rolling_dd = prices.rolling(window).apply(
            lambda x: self.calculate_max_drawdown(x)["max_drawdown"],
            raw=False
        )
        return rolling_dd

    def _calculate_drawdown_duration(self, drawdown: pd.Series) -> int:
        """Calculate maximum drawdown duration in days"""
        # Find periods when drawdown is positive
        is_drawdown = drawdown < 0
        drawdown_periods = is_drawdown.astype(int).groupby(
            (~is_drawdown).cumsum()
        ).cumsum()

        return drawdown_periods.max() if len(drawdown_periods) > 0 else 0

    def _calculate_recovery_time(self, drawdown: pd.Series) -> int:
        """Calculate time to recover from maximum drawdown"""
        max_dd_idx = drawdown.idxmin()
        if pd.isna(max_dd_idx):
            return 0

        # Find next time drawdown becomes zero
        recovery_mask = drawdown.loc[max_dd_idx:] >= 0
        if not recovery_mask.any():
            return len(drawdown) - drawdown.index.get_loc(max_dd_idx)

        recovery_idx = recovery_mask.idxmax()
        return (recovery_idx - max_dd_idx).days


class VolatilityCalculator:
    """Volatility Calculator"""

    def __init__(self, annualization_factor: int = 252):
        """
        Initialize volatility calculator

        Args:
            annualization_factor: Number of trading days per year
        """
        self.annualization_factor = annualization_factor

    def calculate_returns_volatility(
        self,
        returns: pd.Series,
        window: int = 20,
        annualize: bool = True
    ) -> float:
        """
        Calculate returns volatility

        Args:
            returns: Returns series
            window: Rolling window
            annualize: Whether to annualize

        Returns:
            Volatility value
        """
        if window and len(returns) > window:
            returns = returns.tail(window)

        vol = returns.std()

        if annualize:
            vol = vol * np.sqrt(self.annualization_factor)

        return vol

    def calculate Parkinson_volatility(
        self,
        high: pd.Series,
        low: pd.Series,
        window: int = 20,
        annualize: bool = True
    ) -> pd.Series:
        """
        Calculate Parkinson volatility (using high/low prices)

        Args:
            high: High prices
            low: Low prices
            window: Rolling window
            annualize: Whether to annualize

        Returns:
            Parkinson volatility series
        """
        hl_ratio = np.log(high / low) ** 2
        parkinson_vol = np.sqrt(hl_ratio.rolling(window).mean() / (4 * np.log(2)))

        if annualize:
            parkinson_vol = parkinson_vol * np.sqrt(self.annualization_factor)

        return parkinson_vol

    def calculate_garman_klass_volatility(
        self,
        open_: pd.Series,
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        window: int = 20,
        annualize: bool = True
    ) -> pd.Series:
        """
        Calculate Garman-Klass volatility (OHLC)

        Args:
            open_: Opening prices
            high: High prices
            low: Low prices
            close: Closing prices
            window: Rolling window
            annualize: Whether to annualize

        Returns:
            Garman-Klass volatility series
        """
        hl_ratio = (np.log(high / low) ** 2) / 2
        co_ratio = (np.log(close / open_) ** 2) * (2 * np.log(2) - 1)

        gk_vol = np.sqrt((hl_ratio - co_ratio).rolling(window).mean())

        if annualize:
            gk_vol = gk_vol * np.sqrt(self.annualization_factor)

        return gk_vol

    def calculate_ewma_volatility(
        self,
        returns: pd.Series,
        lambda_param: float = 0.94,
        annualize: bool = True
    ) -> pd.Series:
        """
        Calculate EWMA volatility

        Args:
            returns: Returns series
            lambda_param: Decay factor
            annualize: Whether to annualize

        Returns:
            EWMA volatility series
        """
        # Initialize with first variance
        ewma_var = pd.Series(index=returns.index, dtype=float)
        ewma_var.iloc[0] = returns.iloc[0] ** 2

        # Calculate EWMA variance
        for i in range(1, len(returns)):
            ewma_var.iloc[i] = (
                lambda_param * ewma_var.iloc[i-1] +
                (1 - lambda_param) * returns.iloc[i-1] ** 2
            )

        ewma_vol = np.sqrt(ewma_var)

        if annualize:
            ewma_vol = ewma_vol * np.sqrt(self.annualization_factor)

        return ewma_vol


class CorrelationAnalyzer:
    """Correlation and Concentration Analysis"""

    def __init__(self):
        """Initialize correlation analyzer"""
        pass

    def calculate_correlation_matrix(
        self,
        returns_df: pd.DataFrame,
        method: str = "pearson",
        min_periods: int = 20
    ) -> pd.DataFrame:
        """
        Calculate correlation matrix

        Args:
            returns_df: DataFrame of returns for multiple assets
            method: Correlation method ("pearson", "spearman", "kendall")
            min_periods: Minimum periods for calculation

        Returns:
            Correlation matrix
        """
        return returns_df.corr(method=method, min_periods=min_periods)

    def calculate_rolling_correlation(
        self,
        returns_df: pd.DataFrame,
        window: int = 60,
        method: str = "pearson"
    ) -> Dict[Tuple[str, str], pd.Series]:
        """
        Calculate rolling correlations

        Args:
            returns_df: DataFrame of returns
            window: Rolling window
            method: Correlation method

        Returns:
            Dictionary of rolling correlations for each pair
        """
        correlations = {}
        assets = returns_df.columns

        for i, asset1 in enumerate(assets):
            for asset2 in assets[i+1:]:
                corr = returns_df[asset1].rolling(window).corr(returns_df[asset2])
                correlations[(asset1, asset2)] = corr

        return correlations

    def calculate_average_correlation(
        self,
        correlation_matrix: pd.DataFrame
    ) -> float:
        """
        Calculate average correlation in the matrix

        Args:
            correlation_matrix: Correlation matrix

        Returns:
            Average correlation value
        """
        # Exclude diagonal
        mask = ~np.eye(correlation_matrix.shape[0], dtype=bool)
        avg_corr = correlation_matrix.values[mask].mean()
        return avg_corr

    def calculate_concentration_ratio(
        self,
        weights: pd.Series,
        top_n: Optional[int] = None
    ) -> Dict[str, float]:
        """
        Calculate concentration ratios

        Args:
            weights: Portfolio weights
            top_n: Number of top positions to consider

        Returns:
            Dictionary of concentration metrics
        """
        weights = weights.abs().sort_values(ascending=False)
        total_weight = weights.sum()

        # Calculate concentration ratios
        concentration_metrics = {}

        if top_n is None:
            top_n = min(10, len(weights))

        # Top N concentration
        concentration_metrics[f"top_{top_n}_concentration"] = \
            weights.head(top_n).sum() / total_weight

        # Herfindahl-Hirschman Index (HHI)
        hhi = (weights / total_weight) ** 2
        concentration_metrics["hhi"] = hhi.sum()

        # Effective number of positions
        concentration_metrics["effective_positions"] = 1 / hhi.sum()

        # Gini coefficient
        gini = self._calculate_gini_coefficient(weights.values)
        concentration_metrics["gini_coefficient"] = gini

        return concentration_metrics

    def _calculate_gini_coefficient(self, values: np.ndarray) -> float:
        """Calculate Gini coefficient"""
        # Sort values
        sorted_values = np.sort(values)
        n = len(values)

        # Calculate cumulative sum
        cumulative = np.cumsum(sorted_values)

        # Calculate Gini coefficient
        gini = (n + 1 - 2 * np.sum(cumulative) / cumulative[-1]) / n
        return gini

    def estimate_covariance_matrix(
        self,
        returns_df: pd.DataFrame,
        method: str = "ledoit_wolf"
    ) -> pd.DataFrame:
        """
        Estimate covariance matrix with shrinkage

        Args:
            returns_df: Returns DataFrame
            method: Estimation method ("sample", "ledoit_wolf", "oracle_approximating")

        Returns:
            Estimated covariance matrix
        """
        if method == "sample":
            return returns_df.cov()
        elif method == "ledoit_wolf":
            lw = LedoitWolf()
            shrunk_cov = lw.fit(returns_df.dropna())
            return pd.DataFrame(
                shrunk_cov.covariance_,
                index=returns_df.columns,
                columns=returns_df.columns
            )
        else:
            raise ValueError(f"Unsupported method: {method}")