"""
Momentum Strategy Template

Template for momentum-based trading strategies.
Generates code for strategies that trade based on price momentum.
"""

from typing import Any
from .base import StrategyTemplate, StrategyType, TemplateFactory


class MomentumTemplate(StrategyTemplate):
    """
    Template for momentum-based strategies.

    Generates strategies that identify and trade assets with strong
    directional momentum based on price changes over a lookback period.

    Required Parameters:
        - lookback_period: Period for momentum calculation
        - threshold: Momentum threshold for signal generation
        - position_size: Size of positions to take

    Optional Parameters:
        - use_rsi: Use RSI filter
        - rsi_period: RSI calculation period
        - rsi_overbought: Overbought threshold
        - rsi_oversold: Oversold threshold
    """

    @classmethod
    def get_strategy_type(cls) -> StrategyType:
        return StrategyType.MOMENTUM

    @classmethod
    def get_required_parameters(cls) -> list[str]:
        return [
            "lookback_period",
            "threshold",
            "position_size",
        ]

    @classmethod
    def get_optional_parameters(cls) -> list[str]:
        return [
            "use_rsi",
            "rsi_period",
            "rsi_overbought",
            "rsi_oversold",
            "stop_loss",
            "take_profit",
        ]

    def generate_code(
        self,
        parameters: dict[str, Any],
        indicators: dict[str, Any],
    ) -> str:
        """Generate momentum strategy code."""
        strategy_name = parameters.get("name", "MomentumStrategy")
        lookback = parameters.get("lookback_period", 20)
        threshold = parameters.get("threshold", 0.02)
        position_size = parameters.get("position_size", 0.1)
        use_rsi = parameters.get("use_rsi", False)

        rsi_filter = ""
        if use_rsi:
            rsi_period = parameters.get("rsi_period", 14)
            rsi_overbought = parameters.get("rsi_overbought", 70)
            rsi_oversold = parameters.get("rsi_oversold", 30)
            rsi_filter = f"""
        # RSI filter
        rsi = self._calculate_rsi(data, {rsi_period})
        signals[(rsi > {rsi_overbought}) & (momentum > 0)] = 0  # Exit long
        signals[(rsi < {rsi_oversold}) & (momentum < 0)] = 0  # Exit short
"""

        stop_loss_code = ""
        if "stop_loss" in parameters or "take_profit" in parameters:
            stop_loss = parameters.get("stop_loss", 0.05)
            take_profit = parameters.get("take_profit", 0.10)
            stop_loss_code = f"""
    def _apply_risk_management(
        self,
        signals: pd.Series,
        data: pd.DataFrame
    ) -> pd.Series:
        \"\"\"Apply stop-loss and take-profit rules.\"\"\"
        positions = signals.copy()
        entry_prices = data['close'].copy()

        for i in range(1, len(positions)):
            if positions.iloc[i-1] != 0 and positions.iloc[i] == 0:
                entry_prices.iloc[i:] = data['close'].iloc[i]

            if positions.iloc[i-1] != 0:
                pnl = (data['close'].iloc[i] - entry_prices.iloc[i]) / entry_prices.iloc[i]

                if positions.iloc[i-1] > 0:  # Long position
                    if pnl < -{stop_loss} or pnl > {take_profit}:
                        positions.iloc[i] = 0
                else:  # Short position
                    if pnl > {stop_loss} or pnl < -{take_profit}:
                        positions.iloc[i] = 0

        return positions
"""

        return f'''"""
{strategy_name}

Momentum-based trading strategy that identifies assets with strong
directional price momentum and trades accordingly.

Parameters:
    - lookback_period: {lookback} - Period for momentum calculation
    - threshold: {threshold} - Momentum threshold for signals
    - position_size: {position_size} - Position sizing
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, Any


class {strategy_name}:
    \"\"\"
    Momentum Strategy Implementation.

    Generates trading signals based on price momentum over a specified
    lookback period. Uses momentum threshold to determine entry/exit points.
    \"\"\"

    def __init__(
        self,
        lookback_period: int = {lookback},
        threshold: float = {threshold},
        position_size: float = {position_size},
    ):
        \"\"\"
        Initialize momentum strategy.

        Args:
            lookback_period: Period for momentum calculation (days)
            threshold: Minimum momentum for signal generation
            position_size: Fraction of capital to allocate per trade
        \"\"\"
        self.lookback_period = lookback_period
        self.threshold = threshold
        self.position_size = position_size
{self._get_rsi_init(parameters)}

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        \"\"\"
        Generate trading signals based on momentum.

        Args:
            data: DataFrame with 'close' prices

        Returns:
            Series of trading signals (1=long, -1=short, 0=neutral)
        \"\"\"
        # Calculate momentum
        momentum = self._calculate_momentum(data)
{self._get_rsi_calculation(parameters)}

        # Generate initial signals
        signals = pd.Series(0, index=data.index)
        signals[momentum > self.threshold] = 1
        signals[momentum < -self.threshold] = -1
{rsi_filter}
        return signals

    def _calculate_momentum(self, data: pd.DataFrame) -> pd.Series:
        \"\"\"
        Calculate price momentum.

        Args:
            data: DataFrame with 'close' prices

        Returns:
            Series of momentum values
        \"\"\"
        return data['close'].pct_change(self.lookback_period)
{self._get_rsi_helper(parameters)}
{stop_loss_code}

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

        # Calculate returns
        returns = signals.shift(1) * data['close'].pct_change()

        # Calculate equity curve
        equity = (1 + returns * self.position_size).cumprod() * initial_capital

        return {{
            "final_equity": equity.iloc[-1],
            "total_return": (equity.iloc[-1] / initial_capital) - 1,
            "sharpe_ratio": self._calculate_sharpe(returns * self.position_size),
            "max_drawdown": self._calculate_max_drawdown(equity),
            "equity_curve": equity,
            "signals": signals,
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

    def _get_rsi_init(self, parameters: dict) -> str:
        """Get RSI initialization code if enabled."""
        if parameters.get("use_rsi"):
            return f"""
        self.rsi_period = {parameters.get('rsi_period', 14)}
        self.rsi_overbought = {parameters.get('rsi_overbought', 70)}
        self.rsi_oversold = {parameters.get('rsi_oversold', 30)}"""
        return ""

    def _get_rsi_calculation(self, parameters: dict) -> str:
        """Get RSI calculation code if enabled."""
        if parameters.get("use_rsi"):
            return """
        # Calculate RSI for filtering
        rsi = self._calculate_rsi(data)"""
        return ""

    def _get_rsi_helper(self, parameters: dict) -> str:
        """Get RSI helper method if enabled."""
        if parameters.get("use_rsi"):
            period = parameters.get("rsi_period", 14)
            return f"""

    def _calculate_rsi(self, data: pd.DataFrame, period: int = {period}) -> pd.Series:
        \"\"\"
        Calculate Relative Strength Index (RSI).

        Args:
            data: DataFrame with 'close' prices
            period: RSI calculation period

        Returns:
            Series of RSI values
        \"\"\"
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi"""
        return ""

    def _validate_parameter_values(
        self,
        parameters: dict[str, Any]
    ) -> tuple[bool, Any]:
        """Validate momentum-specific parameter values."""
        lookback = parameters.get("lookback_period")
        threshold = parameters.get("threshold")
        position_size = parameters.get("position_size")

        if lookback is not None and lookback <= 0:
            return False, "lookback_period must be positive"

        if threshold is not None and threshold < 0:
            return False, "threshold must be non-negative"

        if position_size is not None and (position_size <= 0 or position_size > 1):
            return False, "position_size must be between 0 and 1"

        return True, None


# Register template
TemplateFactory.register(MomentumTemplate)
