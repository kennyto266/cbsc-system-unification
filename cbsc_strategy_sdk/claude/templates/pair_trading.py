"""
Pair Trading Strategy Template

Template for pair trading strategies.
Generates code for cointegration-based pair trading strategies.
"""

from typing import Any
from .base import StrategyTemplate, StrategyType, TemplateFactory


class PairTradingTemplate(StrategyTemplate):
    """
    Template for pair trading strategies.

    Generates strategies that identify cointegrated asset pairs
    and trade the mean reversion of their spread.

    Required Parameters:
        - pair: Tuple of two asset symbols
        - lookback_window: Window for spread calculation
        - entry_threshold: Standard deviations for entry
        - exit_threshold: Standard deviations for exit

    Optional Parameters:
        - coint_test_method: Cointegration test method ('eg' or 'johansen')
        - half_life: Use half-life for position sizing
        - transaction_costs: Include transaction cost estimates
    """

    @classmethod
    def get_strategy_type(cls) -> StrategyType:
        return StrategyType.PAIR_TRADING

    @classmethod
    def get_required_parameters(cls) -> list[str]:
        return [
            "pair",
            "lookback_window",
            "entry_threshold",
            "exit_threshold",
        ]

    @classmethod
    def get_optional_parameters(cls) -> list[str]:
        return [
            "coint_test_method",
            "use_half_life",
            "transaction_costs",
            "position_size",
        ]

    def generate_code(
        self,
        parameters: dict[str, Any],
        indicators: dict[str, Any],
    ) -> str:
        """Generate pair trading strategy code."""
        strategy_name = parameters.get("name", "PairTradingStrategy")
        pair = parameters.get("pair", ("ASSET_A", "ASSET_B"))
        lookback = parameters.get("lookback_window", 30)
        entry_threshold = parameters.get("entry_threshold", 2.0)
        exit_threshold = parameters.get("exit_threshold", 0.5)
        position_size = parameters.get("position_size", 0.5)

        coint_method = parameters.get("coint_test_method", "eg")

        cointegration_code = ""
        if coint_method == "johansen":
            cointegration_code = """
    def test_cointegration(self, data: pd.DataFrame) -> dict:
        \"\"\"Test cointegration using Johansen test.\"\"\"
        from statsmodels.tsa.vector_ar.vecm import coint_johansen

        try:
            result = coint_johansen(data, det_order=0, k_ar_diff=1)
            return {
                "is_cointegrated": all(result.eig > 0.1),
                "eigenvalues": result.eig,
                "trace_stat": result.lr1,
                "critical_values": result.cvt,
            }
        except Exception as e:
            return {"is_cointegrated": False, "error": str(e)}"""
        else:
            cointegration_code = """
    def test_cointegration(self, data: pd.DataFrame) -> dict:
        \"\"\"Test cointegration using Engle-Granger test.\"\"\"
        from statsmodels.tsa.stattools import coint

        try:
            score, pvalue, _ = coint(
                data[self.pair[0]],
                data[self.pair[1]]
            )
            return {
                "is_cointegrated": pvalue < 0.05,
                "p_value": pvalue,
                "test_statistic": score,
            }
        except Exception as e:
            return {"is_cointegrated": False, "error": str(e)}"""

        half_life_code = ""
        if parameters.get("use_half_life"):
            half_life_code = """

    def calculate_half_life(self, spread: pd.Series) -> float:
        \"\"\"Calculate half-life of mean reversion for position sizing.\"\"\"
        spread_lag = spread.shift(1)
        delta_spread = spread - spread_lag

        # Remove NaN values
        valid = pd.DataFrame({
            'spread': spread[1:],
            'spread_lag': spread_lag[1:],
            'delta_spread': delta_spread[1:]
        }).dropna()

        if len(valid) < 10:
            return 10.0  # Default half-life

        # Run regression: delta_spread = alpha + beta * spread_lag
        beta = np.polyfit(valid['spread_lag'], valid['delta_spread'], 1)[0]
        half_life = -np.log(2) / beta if beta < 0 else 10.0
        return max(1.0, half_life)"""

        transaction_cost_code = ""
        if parameters.get("transaction_costs"):
            cost_per_trade = parameters.get("transaction_costs", 0.001)
            transaction_cost_code = f"""

        # Apply transaction costs
        transaction_cost = {cost_per_trade}
        returns = returns - (signals.abs().sum(axis=1) * transaction_cost)"""

        return f'''"""
{strategy_name}

Pair trading strategy that identifies cointegrated asset pairs
and trades the mean reversion of their spread.

Parameters:
    - pair: {pair} - Asset pair to trade
    - lookback_window: {lookback} - Window for spread calculation
    - entry_threshold: {entry_threshold} - Z-score for entry
    - exit_threshold: {exit_threshold} - Z-score for exit
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, Tuple


class {strategy_name}:
    \"\"\"
    Pair Trading Strategy Implementation.

    Identifies cointegrated asset pairs and trades the mean reversion
    of their spread using statistical arbitrage techniques.
    \"\"\"

    def __init__(
        self,
        pair: Tuple[str, str] = {pair},
        lookback_window: int = {lookback},
        entry_threshold: float = {entry_threshold},
        exit_threshold: float = {exit_threshold},
        position_size: float = {position_size},
    ):
        \"\"\"
        Initialize pair trading strategy.

        Args:
            pair: Tuple of two asset symbols
            lookback_window: Window for spread statistics
            entry_threshold: Z-score threshold for entry
            exit_threshold: Z-score threshold for exit
            position_size: Fraction of capital per trade
        \"\"\"
        self.pair = pair
        self.lookback_window = lookback_window
        self.entry_threshold = entry_threshold
        self.exit_threshold = exit_threshold
        self.position_size = position_size
        self.hedge_ratio = None

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        \"\"\"
        Generate trading signals for pair trading.

        Args:
            data: DataFrame with asset prices

        Returns:
            DataFrame with signals for each asset
        \"\"\"
        # Calculate hedge ratio
        self._calculate_hedge_ratio(data)

        # Calculate spread
        spread = self._calculate_spread(data)

        # Calculate z-score of spread
        spread_mean = spread.rolling(window=self.lookback_window).mean()
        spread_std = spread.rolling(window=self.lookback_window).std()
        z_score = (spread - spread_mean) / spread_std

        # Generate signals
        signals = pd.DataFrame(0, index=data.index, columns=list(self.pair))

        # Long spread (long first, short second)
        signals.loc[z_score < -self.entry_threshold, self.pair[0]] = 1
        signals.loc[z_score < -self.entry_threshold, self.pair[1]] = -1

        # Short spread (short first, long second)
        signals.loc[z_score > self.entry_threshold, self.pair[0]] = -1
        signals.loc[z_score > self.entry_threshold, self.pair[1]] = 1

        # Exit positions
        exit_mask = abs(z_score) < self.exit_threshold
        signals.loc[exit_mask, self.pair[0]] = 0
        signals.loc[exit_mask, self.pair[1]] = 0

        return signals

    def _calculate_hedge_ratio(self, data: pd.DataFrame):
        \"\"\"Calculate hedge ratio using OLS regression.\"\"\"
        import statsmodels.api as sm

        y = data[self.pair[1]]
        x = data[self.pair[0]]
        x = sm.add_constant(x)

        model = sm.OLS(y, x, missing='drop').fit()
        self.hedge_ratio = model.params[1]

    def _calculate_spread(self, data: pd.DataFrame) -> pd.Series:
        \"\"\"Calculate spread between cointegrated pair.\"\"\"
        if self.hedge_ratio is None:
            self._calculate_hedge_ratio(data)

        spread = data[self.pair[1]] - self.hedge_ratio * data[self.pair[0]]
        return spread
{cointegration_code}
{half_life_code}

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

        # Calculate returns for each leg
        returns = pd.Series(0.0, index=data.index)

        for asset in self.pair:
            asset_return = signals[asset].shift(1) * data[asset].pct_change()
            returns += asset_return * self.position_size
{transaction_cost_code}

        # Calculate equity curve
        equity = (1 + returns).cumprod() * initial_capital

        # Test cointegration
        coint_result = self.test_cointegration(data)

        return {{
            "final_equity": equity.iloc[-1],
            "total_return": (equity.iloc[-1] / initial_capital) - 1,
            "sharpe_ratio": self._calculate_sharpe(returns),
            "max_drawdown": self._calculate_max_drawdown(equity),
            "equity_curve": equity,
            "signals": signals,
            "hedge_ratio": self.hedge_ratio,
            "cointegration": coint_result,
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
        """Validate pair trading specific parameters."""
        pair = parameters.get("pair")
        if pair is not None and (not isinstance(pair, (tuple, list)) or len(pair) != 2):
            return False, "pair must be a tuple/list of exactly 2 assets"

        lookback = parameters.get("lookback_window")
        if lookback is not None and lookback < 5:
            return False, "lookback_window must be at least 5"

        entry_threshold = parameters.get("entry_threshold")
        exit_threshold = parameters.get("exit_threshold")
        if entry_threshold is not None and exit_threshold is not None:
            if entry_threshold <= exit_threshold:
                return False, "entry_threshold must be greater than exit_threshold"

        return True, None


# Register template
TemplateFactory.register(PairTradingTemplate)
