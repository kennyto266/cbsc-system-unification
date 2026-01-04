"""
Advanced Risk Calculators
Sophisticated risk metrics calculation for comprehensive risk management
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta
from scipy import stats
from sklearn.covariance import LedoitWolf
import logging

logger = logging.getLogger(__name__)


class AdvancedVaRCalculator:
    """Advanced Value-at-Risk calculator with multiple methods"""

    def __init__(self, confidence_levels: List[float] = [0.95, 0.99]):
        self.confidence_levels = confidence_levels

    def calculate_historical_var(
        self,
        returns: pd.Series,
        confidence: float,
        method: str = "simple",
        window: Optional[int] = None
    ) -> float:
        """
        Calculate Historical VaR

        Args:
            returns: Return series
            confidence: Confidence level (e.g., 0.95 for 95% VaR)
            method: 'simple', 'weighted', or 'filtered'
            window: Lookback window (None for full history)

        Returns:
            VaR value (negative number representing loss)
        """
        if window:
            returns = returns.tail(window)

        if method == "simple":
            # Simple historical VaR
            var = np.percentile(returns, (1 - confidence) * 100)

        elif method == "weighted":
            # Exponentially weighted historical VaR
            weights = np.exp(np.linspace(-1, 0, len(returns)))
            weights = weights / weights.sum()
            sorted_idx = np.argsort(returns)
            cum_weights = np.cumsum(weights[sorted_idx])
            var_idx = np.searchsorted(cum_weights, 1 - confidence)
            var = returns.iloc[sorted_idx[var_idx]]

        elif method == "filtered":
            # Filtered Historical VaR (simplified GARCH)
            # Estimate volatility using EWMA
            lambda_param = 0.94
            ewma_var = returns.ewm(alpha=1 - lambda_param).var()
            scaled_returns = returns / np.sqrt(ewma_var)
            var_percentile = np.percentile(scaled_returns.dropna(), (1 - confidence) * 100)
            current_vol = np.sqrt(ewma_var.iloc[-1])
            var = var_percentile * current_vol

        else:
            raise ValueError(f"Unknown VaR method: {method}")

        return float(var)

    def calculate_parametric_var(
        self,
        returns: pd.Series,
        confidence: float,
        distribution: str = "normal",
        method: str = "full"
    ) -> float:
        """
        Calculate Parametric VaR

        Args:
            returns: Return series
            confidence: Confidence level
            distribution: 'normal', 't', or 'skewed_t'
            method: 'full' or 'rolling' estimation

        Returns:
            VaR value (negative number representing loss)
        """
        if method == "full":
            mean = returns.mean()
            std = returns.std()
        else:  # rolling
            mean = returns.rolling(20).mean().iloc[-1]
            std = returns.rolling(20).std().iloc[-1]

        if distribution == "normal":
            # Normal distribution
            z_score = stats.norm.ppf(1 - confidence)
            var = mean + z_score * std

        elif distribution == "t":
            # Student's t-distribution
            # Estimate degrees of freedom
            params = stats.t.fit(returns)
            dof = params[0]
            t_score = stats.t.ppf(1 - confidence, dof)
            var = mean + t_score * std * np.sqrt((dof - 2) / dof)

        elif distribution == "skewed_t":
            # Skewed t-distribution (simplified)
            # Use skew-normal approximation
            skewness = stats.skew(returns)
            if skewness != 0:
                # Adjust for skewness
                adj_mean = mean + skewness * std**3 / 6
                var = stats.norm.ppf(1 - confidence) * std + adj_mean
            else:
                var = self.calculate_parametric_var(returns, confidence, "normal", method)

        return float(var)

    def calculate_monte_carlo_var(
        self,
        returns: pd.Series,
        confidence: float,
        n_simulations: int = 10000,
        horizon: int = 1
    ) -> float:
        """
        Calculate Monte Carlo VaR

        Args:
            returns: Historical returns for parameter estimation
            confidence: Confidence level
            n_simulations: Number of Monte Carlo simulations
            horizon: Time horizon in days

        Returns:
            VaR value (negative number representing loss)
        """
        # Estimate parameters
        mean = returns.mean()
        std = returns.std()

        # Generate simulations
        simulated_returns = np.random.normal(
            mean * horizon,
            std * np.sqrt(horizon),
            n_simulations
        )

        # Calculate VaR
        var = np.percentile(simulated_returns, (1 - confidence) * 100)

        return float(var)

    def calculate_cvar(
        self,
        returns: pd.Series,
        confidence: float,
        method: str = "historical"
    ) -> float:
        """
        Calculate Conditional Value-at-Risk (Expected Shortfall)

        Args:
            returns: Return series
            confidence: Confidence level
            method: 'historical', 'parametric', or 'monte_carlo'

        Returns:
            CVaR value (negative number representing expected loss)
        """
        if method == "historical":
            var = self.calculate_historical_var(returns, confidence)
            # Expected shortfall is mean of returns below VaR
            cvar = returns[returns <= var].mean()

        elif method == "parametric":
            # For normal distribution, CVaR = -σ * φ(z) / (1 - α)
            mean = returns.mean()
            std = returns.std()
            z = stats.norm.ppf(1 - confidence)
            phi_z = stats.norm.pdf(z)
            cvar = mean - std * phi_z / (1 - confidence)

        return float(cvar)


class StressTestCalculator:
    """Stress testing calculator for scenario analysis"""

    def __init__(self):
        self.scenarios = self._initialize_scenarios()

    def _initialize_scenarios(self) -> Dict[str, Dict]:
        """Initialize predefined stress scenarios"""
        return {
            "market_crash": {
                "description": "30% market decline",
                "market_shock": -0.30,
                "volatility_increase": 2.0,
                "correlation_increase": 0.3
            },
            "volatility_spike": {
                "description": "Volatility increases 3x",
                "market_shock": 0,
                "volatility_increase": 3.0,
                "correlation_increase": 0.2
            },
            "correlation_breakdown": {
                "description": "All correlations converge to 1",
                "market_shock": -0.15,
                "volatility_increase": 1.5,
                "correlation_increase": 1.0
            },
            "liquidity_crisis": {
                "description": "20% market decline with 5x volatility",
                "market_shock": -0.20,
                "volatility_increase": 5.0,
                "correlation_increase": 0.4
            }
        }

    def calculate_stress_loss(
        self,
        positions: Dict[str, float],
        returns_matrix: pd.DataFrame,
        scenario: str
    ) -> Dict[str, float]:
        """
        Calculate stress scenario losses

        Args:
            positions: Dict of {symbol: position_value}
            returns_matrix: Historical returns matrix
            scenario: Scenario name or custom dict

        Returns:
            Dict with stress test results
        """
        if isinstance(scenario, str):
            if scenario not in self.scenarios:
                raise ValueError(f"Unknown scenario: {scenario}")
            scenario_params = self.scenarios[scenario]
        else:
            scenario_params = scenario

        # Get current portfolio value
        portfolio_value = sum(abs(v) for v in positions.values())

        # Calculate stress scenario returns
        stress_returns = self._generate_stress_returns(
            returns_matrix,
            scenario_params
        )

        # Calculate position losses
        position_losses = {}
        for symbol, value in positions.items():
            if symbol in stress_returns:
                loss = value * stress_returns[symbol]
                position_losses[symbol] = loss

        # Calculate aggregate metrics
        total_loss = sum(position_losses.values())
        loss_percentage = total_loss / portfolio_value if portfolio_value > 0 else 0

        return {
            "scenario": scenario,
            "portfolio_value": portfolio_value,
            "total_loss": total_loss,
            "loss_percentage": loss_percentage,
            "position_losses": position_losses,
            "worst_position": max(position_losses.items(), key=lambda x: x[1])[0] if position_losses else None,
            "var_breaches": self._check_var_breaches(loss_percentage)
        }

    def _generate_stress_returns(
        self,
        returns_matrix: pd.DataFrame,
        scenario: Dict
    ) -> Dict[str, float]:
        """Generate stress scenario returns"""
        stress_returns = {}

        # Calculate base statistics
        mean_returns = returns_matrix.mean()
        vol = returns_matrix.std()
        corr_matrix = returns_matrix.corr()

        # Apply scenario parameters
        for asset in returns_matrix.columns:
            base_return = mean_returns[asset]
            asset_vol = vol[asset]

            # Apply market shock and volatility increase
            shocked_return = base_return + scenario.get("market_shock", 0)
            shocked_vol = asset_vol * scenario.get("volatility_increase", 1.0)

            # Generate correlated random shock
            if scenario.get("correlation_increase", 0) > 0:
                # Simplified correlation adjustment
                # In practice, this would use more sophisticated methods
                shocked_return *= (1 + scenario["correlation_increase"])

            stress_returns[asset] = shocked_return

        return stress_returns

    def _check_var_breaches(self, loss_pct: float) -> Dict[str, bool]:
        """Check if stress loss exceeds VaR limits"""
        return {
            "var_95": loss_pct > 0.02,  # 2% daily VaR
            "var_99": loss_pct > 0.03,  # 3% daily VaR
            "var_999": loss_pct > 0.05  # 5% daily VaR
        }

    def custom_scenario(
        self,
        name: str,
        market_shock: float,
        volatility_increase: float,
        correlation_increase: float,
        description: str = ""
    ):
        """Define custom stress scenario"""
        self.scenarios[name] = {
            "description": description,
            "market_shock": market_shock,
            "volatility_increase": volatility_increase,
            "correlation_increase": correlation_increase
        }


class LiquidityRiskCalculator:
    """Liquidity risk calculator"""

    def __init__(self):
        pass

    def calculate_liquidity_metrics(
        self,
        positions: Dict[str, Dict],
        market_data: Dict[str, Dict]
    ) -> Dict[str, float]:
        """
        Calculate liquidity risk metrics

        Args:
            positions: {symbol: {quantity, market_value}}
            market_data: {symbol: {volume, bid_ask_spread, price}}

        Returns:
            Liquidity risk metrics
        """
        metrics = {}

        # Liquidity-adjusted VaR
        liquidity_costs = []
        total_value = sum(p['market_value'] for p in positions.values())

        for symbol, position in positions.items():
            if symbol in market_data:
                # Calculate liquidity cost
                spread = market_data[symbol].get('bid_ask_spread', 0.001)
                daily_volume = market_data[symbol].get('volume', 0)
                position_value = position['market_value']

                # Liquidity cost as % of position
                if daily_volume > 0:
                    turnover_ratio = abs(position['quantity']) / daily_volume
                    # Higher cost for larger turnover ratios
                    liquidity_cost = spread * (1 + turnover_ratio * 10)
                else:
                    liquidity_cost = spread * 10  # Illiquid penalty

                liquidity_costs.append(liquidity_cost * position_value)

        metrics['liquidity_cost'] = sum(liquidity_costs)
        metrics['liquidity_cost_pct'] = (
            metrics['liquidity_cost'] / total_value if total_value > 0 else 0
        )

        # Liquidity at risk (L@R)
        # Simplified calculation based on spread volatility
        spreads = [m.get('bid_ask_spread', 0.001) for m in market_data.values()]
        if spreads:
            spread_vol = np.std(spreads)
            metrics['liquidity_at_risk'] = total_value * spread_vol * 2.33  # 99% L@R
        else:
            metrics['liquidity_at_risk'] = 0

        return metrics


class CorrelationRiskCalculator:
    """Correlation risk calculator"""

    def __init__(self, method: str = "pearson"):
        self.method = method

    def calculate_correlation_metrics(
        self,
        returns_matrix: pd.DataFrame,
        weights: Optional[np.ndarray] = None
    ) -> Dict[str, Union[float, np.ndarray]]:
        """
        Calculate correlation risk metrics

        Args:
            returns_matrix: Asset returns matrix
            weights: Portfolio weights (optional)

        Returns:
            Correlation risk metrics
        """
        metrics = {}

        # Calculate correlation matrix
        if self.method == "pearson":
            corr_matrix = returns_matrix.corr()
        elif self.method == "spearman":
            corr_matrix = returns_matrix.corr(method='spearman')
        elif self.method == "shrinkage":
            # Ledoit-Wolf shrinkage
            lw = LedoitWolf().fit(returns_matrix)
            corr_matrix = pd.DataFrame(
                lw.covariance_,
                index=returns_matrix.columns,
                columns=returns_matrix.columns
            )
            # Convert covariance to correlation
            std_dev = np.sqrt(np.diag(lw.covariance_))
            corr_matrix = lw.covariance_ / np.outer(std_dev, std_dev)
            corr_matrix = pd.DataFrame(
                corr_matrix,
                index=returns_matrix.columns,
                columns=returns_matrix.columns
            )
        else:
            raise ValueError(f"Unknown correlation method: {self.method}")

        metrics['correlation_matrix'] = corr_matrix

        # Average correlation
        n = len(corr_matrix)
        if n > 1:
            # Exclude diagonal elements
            mask = ~np.eye(n, dtype=bool)
            avg_corr = corr_matrix.values[mask].mean()
            metrics['average_correlation'] = float(avg_corr)

            # Maximum correlation
            max_corr = corr_matrix.values[mask].max()
            metrics['maximum_correlation'] = float(max_corr)

            # Minimum correlation
            min_corr = corr_matrix.values[mask].min()
            metrics['minimum_correlation'] = float(min_corr)

            # Correlation concentration (Herfindahl index)
            corr_squared = corr_matrix.values[mask] ** 2
            metrics['correlation_concentration'] = float(corr_squared.sum() / len(corr_squared))

        # Portfolio correlation risk (if weights provided)
        if weights is not None:
            # Diversification ratio
            weighted_vol = np.sqrt(np.dot(weights.T, np.dot(corr_matrix, weights)))
            equal_weight_vol = np.sqrt(np.mean(corr_matrix.values[mask]))
            metrics['diversification_ratio'] = float(equal_weight_vol / weighted_vol)

            # Effective number of bets
            effective_bets = 1 / np.dot(weights.T, np.dot(corr_matrix, weights))
            metrics['effective_bets'] = float(effective_bets)

        return metrics

    def calculate_regime_correlation(
        self,
        returns_matrix: pd.DataFrame,
        regime_threshold: float = -0.02
    ) -> Dict[str, pd.DataFrame]:
        """
        Calculate correlation in different market regimes

        Args:
            returns_matrix: Asset returns matrix
            regime_threshold: Return threshold for bear market definition

        Returns:
            Correlation matrices for different regimes
        """
        # Identify market regimes
        market_returns = returns_matrix.mean(axis=1)
        bull_mask = market_returns > 0
        bear_mask = market_returns < regime_threshold
        neutral_mask = ~(bull_mask | bear_mask)

        results = {}

        for regime, mask in [
            ("bull", bull_mask),
            ("bear", bear_mask),
            ("neutral", neutral_mask)
        ]:
            if mask.sum() > 10:  # Need sufficient data
                regime_returns = returns_matrix[mask]
                results[f"{regime}_correlation"] = regime_returns.corr()
                results[f"{regime}_avg_correlation"] = float(
                    regime_returns.corr().values[~np.eye(len(regime_returns.columns), dtype=bool)].mean()
                )

        return results


class TailRiskCalculator:
    """Tail risk calculator for extreme events"""

    def __init__(self):
        pass

    def calculate_tail_metrics(
        self,
        returns: pd.Series,
        confidence_levels: List[float] = [0.95, 0.99, 0.999]
    ) -> Dict[str, float]:
        """
        Calculate tail risk metrics

        Args:
            returns: Return series
            confidence_levels: List of confidence levels

        Returns:
            Tail risk metrics
        """
        metrics = {}

        # Sort returns for easier calculation
        sorted_returns = np.sort(returns)

        for confidence in confidence_levels:
            tail_prob = (1 - confidence) / 2  # Two-tailed
            n = len(sorted_returns)

            # Left tail (losses)
            left_idx = int(tail_prob * n)
            metrics[f"tail_loss_{confidence}"] = float(sorted_returns[left_idx])

            # Right tail (gains)
            right_idx = int((1 - tail_prob) * n)
            metrics[f"tail_gain_{confidence}"] = float(sorted_returns[right_idx])

        # Tail ratio (99th percentile gain vs 1st percentile loss)
        if "tail_gain_99" in metrics and "tail_loss_99" in metrics:
            metrics["tail_ratio"] = abs(
                metrics["tail_gain_99"] / metrics["tail_loss_99"]
            ) if metrics["tail_loss_99"] != 0 else float('inf')

        # Skewness and kurtosis
        metrics["skewness"] = float(stats.skew(returns))
        metrics["excess_kurtosis"] = float(stats.kurtosis(returns, fisher=True))

        # Maximum drawdown in tail
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        metrics["max_tail_drawdown"] = float(drawdown.min())

        # Expected tail loss (beyond VaR)
        var_99 = metrics.get("tail_loss_99", np.percentile(returns, 1))
        tail_losses = returns[returns <= var_99]
        if len(tail_losses) > 0:
            metrics["expected_tail_loss"] = float(tail_losses.mean())
            metrics["tail_loss_frequency"] = len(tail_losses) / len(returns)
        else:
            metrics["expected_tail_loss"] = 0
            metrics["tail_loss_frequency"] = 0

        return metrics