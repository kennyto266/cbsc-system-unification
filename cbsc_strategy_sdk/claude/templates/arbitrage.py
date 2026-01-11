"""
Arbitrage Strategy Template

Template for arbitrage trading strategies.
Generates code for statistical and cross-asset arbitrage strategies.
"""

from typing import Any
from .base import StrategyTemplate, StrategyType, TemplateFactory


class ArbitrageTemplate(StrategyTemplate):
    """
    Template for arbitrage strategies.

    Generates strategies that identify and exploit price discrepancies
    between related assets or markets.

    Required Parameters:
        - assets: List of asset symbols to monitor
        - correlation_window: Window for correlation calculation
        - entry_threshold: Z-score threshold for entry
        - exit_threshold: Z-score threshold for exit

    Optional Parameters:
        - hedge_ratio_method: Method for calculating hedge ratio
        - min_profit_threshold: Minimum profit for trade execution
        - max_position_duration: Maximum time to hold position
    """

    @classmethod
    def get_strategy_type(cls) -> StrategyType:
        return StrategyType.ARBITRAGE

    @classmethod
    def get_required_parameters(cls) -> list[str]:
        return [
            "assets",
            "correlation_window",
            "entry_threshold",
            "exit_threshold",
        ]

    @classmethod
    def get_optional_parameters(cls) -> list[str]:
        return [
            "hedge_ratio_method",
            "min_profit_threshold",
            "max_position_duration",
            "position_size",
        ]

    def generate_code(
        self,
        parameters: dict[str, Any],
        indicators: dict[str, Any],
    ) -> str:
        """Generate arbitrage strategy code."""
        strategy_name = parameters.get("name", "ArbitrageStrategy")
        assets = parameters.get("assets", ["ASSET_A", "ASSET_B"])
        corr_window = parameters.get("correlation_window", 30)
        entry_threshold = parameters.get("entry_threshold", 2.0)
        exit_threshold = parameters.get("exit_threshold", 0.5)
        position_size = parameters.get("position_size", 0.5)

        hedge_method = parameters.get("hedge_ratio_method", "ols")

        hedge_ratio_code = ""
        if hedge_method == "ols":
            hedge_ratio_code = """
        # Calculate hedge ratio using OLS regression
        import statsmodels.api as sm
        x = sm.add_constant(data[self.assets[0]])
        model = sm.OLS(data[self.assets[1]], x).fit()
        hedge_ratio = model.params[1]"""
        else:
            hedge_ratio_code = """
        # Simple hedge ratio (ratio of prices)
        hedge_ratio = data[self.assets[0]] / data[self.assets[1]]"""

        return f'''"""
{strategy_name}

Statistical arbitrage strategy that identifies and trades price
discrepancies between related assets.

Parameters:
    - assets: {assets} - Assets to monitor for arbitrage
    - correlation_window: {corr_window} - Window for correlation calculation
    - entry_threshold: {entry_threshold} - Z-score threshold for entry
    - exit_threshold: {exit_threshold} - Z-score threshold for exit
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, Any


class {strategy_name}:
    \"\"\"
    Statistical Arbitrage Strategy Implementation.

    Identifies price discrepancies between correlated assets and trades
    the expected convergence.
    \"\"\"

    def __init__(
        self,
        assets: list[str] = {assets},
        correlation_window: int = {corr_window},
        entry_threshold: float = {entry_threshold},
        exit_threshold: float = {exit_threshold},
        position_size: float = {position_size},
    ):
        \"\"\"
        Initialize arbitrage strategy.

        Args:
            assets: List of asset symbols to trade
            correlation_window: Window for correlation calculation
            entry_threshold: Z-score threshold for entry
            exit_threshold: Z-score threshold for exit
            position_size: Fraction of capital to allocate
        \"\"\"
        self.assets = assets
        self.correlation_window = correlation_window
        self.entry_threshold = entry_threshold
        self.exit_threshold = exit_threshold
        self.position_size = position_size
        self.hedge_ratio = None

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        \"\"\"
        Generate trading signals for arbitrage.

        Args:
            data: DataFrame with asset prices as columns

        Returns:
            DataFrame with signals for each asset
        \"\"\"
        # Calculate spread between assets
        spread = self._calculate_spread(data)

        # Calculate z-score of spread
        spread_mean = spread.rolling(window=self.correlation_window).mean()
        spread_std = spread.rolling(window=self.correlation_window).std()
        z_score = (spread - spread_mean) / spread_std

        # Generate signals
        signals = pd.DataFrame(0, index=data.index, columns=self.assets)

        # Long spread (long first asset, short second)
        signals.loc[z_score < -self.entry_threshold, self.assets[0]] = 1
        signals.loc[z_score < -self.entry_threshold, self.assets[1]] = -1

        # Short spread (short first asset, long second)
        signals.loc[z_score > self.entry_threshold, self.assets[0]] = -1
        signals.loc[z_score > self.entry_threshold, self.assets[1]] = 1

        # Exit positions
        exit_mask = abs(z_score) < self.exit_threshold
        for asset in self.assets:
            signals.loc[exit_mask, asset] = 0

        return signals

    def _calculate_spread(self, data: pd.DataFrame) -> pd.Series:
        \"\"\"
        Calculate spread between assets.

        Args:
            data: DataFrame with asset prices

        Returns:
            Series of spread values
        \"\"\"
        if self.hedge_ratio is None:
{hedge_ratio_code}
        else:
            hedge_ratio = self.hedge_ratio

        spread = data[self.assets[1]] - hedge_ratio * data[self.assets[0]]
        return spread

    def update_hedge_ratio(self, data: pd.DataFrame):
        \"\"\"
        Update hedge ratio based on recent data.

        Args:
            data: DataFrame with asset prices
        \"\"\"
{hedge_ratio_code}
        self.hedge_ratio = hedge_ratio

    def check_correlation(self, data: pd.DataFrame) -> float:
        \"\"\"
        Check correlation between assets.

        Args:
            data: DataFrame with asset prices

        Returns:
            Correlation coefficient
        \"\"\"
        returns = data[self.assets].pct_change().dropna()
        corr = returns[self.assets[0]].corr(returns[self.assets[1]])
        return corr

    def backtest(
        self,
        data: pd.DataFrame,
        initial_capital: float = 100000
    ) -> Dict[str, Any]:
        \"\"\"
        Run backtest on historical data.

        Args:
            data: Historical price data
            initial_capital: Starting capital

        Returns:
            Dictionary with backtest results
        \"\"\"
        signals = self.generate_signals(data)

        # Calculate returns for each asset
        total_return = pd.Series(0.0, index=data.index)

        for asset in self.assets:
            asset_return = signals[asset].shift(1) * data[asset].pct_change()
            total_return += asset_return * self.position_size

        # Calculate equity curve
        equity = (1 + total_return).cumprod() * initial_capital

        return {{
            "final_equity": equity.iloc[-1],
            "total_return": (equity.iloc[-1] / initial_capital) - 1,
            "sharpe_ratio": self._calculate_sharpe(total_return),
            "max_drawdown": self._calculate_max_drawdown(equity),
            "equity_curve": equity,
            "signals": signals,
            "correlation": self.check_correlation(data),
        }}

    def _calculate_sharpe(self, returns: pd.Series) -> float:
        \"\"\"Calculate Sharpe ratio.\"\"\"
        return returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0

    def _calculate_max_drawdown(self, equity: pd.Series) -> float:
        \"\"\"Calculate maximum drawdown.\"\"\"
        rolling_max = equity.expanding().max()
        drawdown = (equity - rolling_max) / rolling_max
        return drawdown.min()
'''

    def _validate_parameter_values(
        self,
        parameters: dict[str, Any]
    ) -> tuple[bool, Any]:
        """Validate arbitrage specific parameters."""
        assets = parameters.get("assets")
        if assets is not None and len(assets) < 2:
            return False, "At least 2 assets required for arbitrage"

        corr_window = parameters.get("correlation_window")
        if corr_window is not None and corr_window < 5:
            return False, "correlation_window must be at least 5"

        entry_threshold = parameters.get("entry_threshold")
        exit_threshold = parameters.get("exit_threshold")
        if entry_threshold is not None and exit_threshold is not None:
            if entry_threshold <= exit_threshold:
                return False, "entry_threshold must be greater than exit_threshold"

        return True, None


# Register template
TemplateFactory.register(ArbitrageTemplate)
