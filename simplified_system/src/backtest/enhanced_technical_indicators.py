#!/usr / bin / env python3
"""
Enhanced Technical Indicators System
Phase 4.1: Vectorized Indicator Implementation

Refactors CoreIndicators class to use VectorBT native methods,
implements cross - indicator analysis, performance attribution,
and adaptive indicator parameter adjustment.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

# VectorBT imports
try:
    import vectorbt as vbt

    VECTORTBT_AVAILABLE = True
except ImportError:
    VECTORTBT_AVAILABLE = False
    logging.warning("VectorBT not available - using fallback calculations")

# Core indicators import
try:
    from src.indicators.core_indicators import CoreIndicators
    from src.indicators.technical_analyzer import TechnicalAnalyzer
except ImportError:
    CoreIndicators = None
    TechnicalAnalyzer = None

logger = logging.getLogger(__name__)


class IndicatorCategory(Enum):
    """Technical indicator categories"""

    TREND = "trend"
    MOMENTUM = "momentum"
    VOLATILITY = "volatility"
    VOLUME = "volume"
    PRICE_PATTERN = "price_pattern"
    SENTIMENT = "sentiment"
    ECONOMIC = "economic"


@dataclass
class IndicatorSignal:
    """Technical indicator signal"""

    indicator_name: str
    signal_type: str  # 'buy', 'sell', 'neutral'
    strength: float  # 0 - 1 signal strength
    confidence: float  # 0 - 1 confidence level
    timestamp: datetime
    parameters: Dict[str, Any]
    signal_value: float


@dataclass
class IndicatorPerformance:
    """Indicator performance attribution"""

    indicator_name: str
    total_return: float
    sharpe_ratio: float
    win_rate: float
    max_drawdown: float
    signal_count: int
    profitable_signals: int
    avg_signal_return: float
    hit_rate: float


class VectorizedTechnicalIndicators:
    """Vectorized technical indicators using VectorBT native methods"""

    def __init__(self):
        """Initialize vectorized technical indicators"""
        self.core_indicators = CoreIndicators() if CoreIndicators else None
        self.technical_analyzer = TechnicalAnalyzer() if TechnicalAnalyzer else None
        self.indicator_cache = {}
        self.performance_cache = {}

    def calculate_rsi_vectorized(
        self,
        price_data: pd.DataFrame,
        periods: List[int] = [14, 21, 30],
        overwrite: bool = False,
    ) -> Dict[str, pd.Series]:
        """
        Calculate RSI using VectorBT for multiple periods

        Args:
            price_data: DataFrame with OHLCV data
            periods: List of RSI periods to calculate
            overwrite: Whether to overwrite cached results

        Returns:
            Dictionary of RSI series for each period
        """
        cache_key = f"rsi_{periods}"
        if not overwrite and cache_key in self.indicator_cache:
            return self.indicator_cache[cache_key]

        if VECTORTBT_AVAILABLE and "close" in price_data.columns:
            # Use VectorBT native RSI calculation
            results = {}
            for period in periods:
                try:
                    rsi = vbt.RSI.run(price_data["close"], window = period)
                    results[f"rsi_{period}"] = rsi.rsi
                    logger.debug(f"VectorBT RSI({period}) calculated successfully")
                except Exception as e:
                    logger.warning(
                        f"VectorBT RSI({period}) failed, using fallback: {e}"
                    )
                    # Fallback to core indicators
                    if self.core_indicators:
                        rsi_series = self.core_indicators.calculate_rsi(
                            price_data["close"], period
                        )
                        results[f"rsi_{period}"] = rsi_series
                    else:
                        # Manual RSI calculation
                        results[f"rsi_{period}"] = self._calculate_rsi_manual(
                            price_data["close"], period
                        )
        else:
            # Fallback to manual calculations
            results = {}
            for period in periods:
                if self.core_indicators:
                    results[f"rsi_{period}"] = self.core_indicators.calculate_rsi(
                        price_data["close"], period
                    )
                else:
                    results[f"rsi_{period}"] = self._calculate_rsi_manual(
                        price_data["close"], period
                    )

        self.indicator_cache[cache_key] = results
        return results

    def calculate_macd_vectorized(
        self,
        price_data: pd.DataFrame,
        fast_periods: List[int] = [12],
        slow_periods: List[int] = [26],
        signal_periods: List[int] = [9],
        overwrite: bool = False,
    ) -> Dict[str, Dict[str, pd.Series]]:
        """
        Calculate MACD using VectorBT for multiple parameter combinations

        Args:
            price_data: DataFrame with OHLCV data
            fast_periods: List of fast EMA periods
            slow_periods: List of slow EMA periods
            signal_periods: List of signal line periods
            overwrite: Whether to overwrite cached results

        Returns:
            Dictionary with MACD components for each parameter combination
        """
        cache_key = f"macd_{fast_periods}_{slow_periods}_{signal_periods}"
        if not overwrite and cache_key in self.indicator_cache:
            return self.indicator_cache[cache_key]

        if VECTORTBT_AVAILABLE and "close" in price_data.columns:
            results = {}
            for fast in fast_periods:
                for slow in slow_periods:
                    for signal in signal_periods:
                        param_key = f"macd_{fast}_{slow}_{signal}"
                        try:
                            macd = vbt.MACD.run(
                                price_data["close"],
                                fast_window = fast,
                                slow_window = slow,
                                signal_window = signal,
                            )
                            results[param_key] = {
                                "macd": macd.macd,
                                "signal": macd.signal,
                                "histogram": macd.histogram,
                            }
                            logger.debug(
                                f"VectorBT MACD({fast},{slow},{signal}) calculated successfully"
                            )
                        except Exception as e:
                            logger.warning(
                                f"VectorBT MACD({fast},{slow},{signal}) failed, using fallback: {e}"
                            )
                            # Fallback calculation
                            results[param_key] = self._calculate_macd_manual(
                                price_data["close"], fast, slow, signal
                            )
        else:
            # Fallback to manual calculations
            results = {}
            for fast in fast_periods:
                for slow in slow_periods:
                    for signal in signal_periods:
                        param_key = f"macd_{fast}_{slow}_{signal}"
                        results[param_key] = self._calculate_macd_manual(
                            price_data["close"], fast, slow, signal
                        )

        self.indicator_cache[cache_key] = results
        return results

    def calculate_bollinger_bands_vectorized(
        self,
        price_data: pd.DataFrame,
        periods: List[int] = [20],
        std_devs: List[float] = [2.0],
        overwrite: bool = False,
    ) -> Dict[str, Dict[str, pd.Series]]:
        """
        Calculate Bollinger Bands using VectorBT

        Args:
            price_data: DataFrame with OHLCV data
            periods: List of lookback periods
            std_devs: List of standard deviation multipliers
            overwrite: Whether to overwrite cached results

        Returns:
            Dictionary with Bollinger Band components
        """
        cache_key = f"bb_{periods}_{std_devs}"
        if not overwrite and cache_key in self.indicator_cache:
            return self.indicator_cache[cache_key]

        if VECTORTBT_AVAILABLE and "close" in price_data.columns:
            results = {}
            for period in periods:
                for std_dev in std_devs:
                    param_key = f"bb_{period}_{std_dev:.1f}"
                    try:
                        bb = vbt.BBANDS.run(
                            price_data["close"], window = period, alpha = std_dev
                        )
                        results[param_key] = {
                            "upper": bb.upper,
                            "middle": bb.middle,
                            "lower": bb.lower,
                            "bandwidth": bb.bandwidth,
                            "percent_b": bb.percent_b,
                        }
                        logger.debug(
                            f"VectorBT BB({period},{std_dev}) calculated successfully"
                        )
                    except Exception as e:
                        logger.warning(
                            f"VectorBT BB({period},{std_dev}) failed, using fallback: {e}"
                        )
                        # Fallback calculation
                        results[param_key] = self._calculate_bollinger_bands_manual(
                            price_data["close"], period, std_dev
                        )
        else:
            # Fallback to manual calculations
            results = {}
            for period in periods:
                for std_dev in std_devs:
                    param_key = f"bb_{period}_{std_dev:.1f}"
                    results[param_key] = self._calculate_bollinger_bands_manual(
                        price_data["close"], period, std_dev
                    )

        self.indicator_cache[cache_key] = results
        return results

    def calculate_moving_averages_vectorized(
        self,
        price_data: pd.DataFrame,
        periods: List[int] = [10, 20, 50, 100, 200],
        ma_types: List[str] = ["sma", "ema"],
        overwrite: bool = False,
    ) -> Dict[str, pd.Series]:
        """
        Calculate moving averages using VectorBT

        Args:
            price_data: DataFrame with OHLCV data
            periods: List of lookback periods
            ma_types: List of MA types ('sma', 'ema')
            overwrite: Whether to overwrite cached results

        Returns:
            Dictionary of moving average series
        """
        cache_key = f"ma_{periods}_{ma_types}"
        if not overwrite and cache_key in self.indicator_cache:
            return self.indicator_cache[cache_key]

        if VECTORTBT_AVAILABLE and "close" in price_data.columns:
            results = {}
            for period in periods:
                for ma_type in ma_types:
                    param_key = f"{ma_type}_{period}"
                    try:
                        if ma_type == "sma":
                            ma = vbt.MA.run(price_data["close"], window = period)
                        elif ma_type == "ema":
                            ma = vbt.MA.run(
                                price_data["close"], window = period, ewm = True
                            )
                        else:
                            continue

                        results[param_key] = ma.ma
                        logger.debug(
                            f"VectorBT {ma_type.upper()}({period}) calculated successfully"
                        )
                    except Exception as e:
                        logger.warning(
                            f"VectorBT {ma_type.upper()}({period}) failed, using fallback: {e}"
                        )
                        # Fallback calculation
                        results[param_key] = self._calculate_ma_manual(
                            price_data["close"], period, ma_type
                        )
        else:
            # Fallback to manual calculations
            results = {}
            for period in periods:
                for ma_type in ma_types:
                    param_key = f"{ma_type}_{period}"
                    results[param_key] = self._calculate_ma_manual(
                        price_data["close"], period, ma_type
                    )

        self.indicator_cache[cache_key] = results
        return results

    def calculate_stochastic_oscillator_vectorized(
        self,
        price_data: pd.DataFrame,
        k_periods: List[int] = [14],
        d_periods: List[int] = [3],
        overwrite: bool = False,
    ) -> Dict[str, Dict[str, pd.Series]]:
        """
        Calculate Stochastic Oscillator using VectorBT

        Args:
            price_data: DataFrame with OHLCV data
            k_periods: List of %K periods
            d_periods: List of %D smoothing periods
            overwrite: Whether to overwrite cached results

        Returns:
            Dictionary with Stochastic components
        """
        cache_key = f"stoch_{k_periods}_{d_periods}"
        if not overwrite and cache_key in self.indicator_cache:
            return self.indicator_cache[cache_key]

        if VECTORTBT_AVAILABLE and all(
            col in price_data.columns for col in ["high", "low", "close"]
        ):
            results = {}
            for k_period in k_periods:
                for d_period in d_periods:
                    param_key = f"stoch_{k_period}_{d_period}"
                    try:
                        stoch = vbt.STOCH.run(
                            high = price_data["high"],
                            low = price_data["low"],
                            close = price_data["close"],
                            k_window = k_period,
                            d_window = d_period,
                        )
                        results[param_key] = {
                            "stoch_k": stoch.stoch_k,
                            "stoch_d": stoch.stoch_d,
                        }
                        logger.debug(
                            f"VectorBT Stoch({k_period},{d_period}) calculated successfully"
                        )
                    except Exception as e:
                        logger.warning(
                            f"VectorBT Stoch({k_period},{d_period}) failed, using fallback: {e}"
                        )
                        # Fallback calculation
                        results[param_key] = self._calculate_stochastic_manual(
                            price_data["high"],
                            price_data["low"],
                            price_data["close"],
                            k_period,
                            d_period,
                        )
        else:
            # Fallback to manual calculations
            results = {}
            for k_period in k_periods:
                for d_period in d_periods:
                    param_key = f"stoch_{k_period}_{d_period}"
                    results[param_key] = self._calculate_stochastic_manual(
                        price_data.get("high", price_data["close"]),
                        price_data.get("low", price_data["close"]),
                        price_data["close"],
                        k_period,
                        d_period,
                    )

        self.indicator_cache[cache_key] = results
        return results

    def calculate_atr_vectorized(
        self,
        price_data: pd.DataFrame,
        periods: List[int] = [14, 21],
        overwrite: bool = False,
    ) -> Dict[str, pd.Series]:
        """
        Calculate Average True Range using VectorBT

        Args:
            price_data: DataFrame with OHLCV data
            periods: List of ATR periods
            overwrite: Whether to overwrite cached results

        Returns:
            Dictionary of ATR series
        """
        cache_key = f"atr_{periods}"
        if not overwrite and cache_key in self.indicator_cache:
            return self.indicator_cache[cache_key]

        if VECTORTBT_AVAILABLE and all(
            col in price_data.columns for col in ["high", "low", "close"]
        ):
            results = {}
            for period in periods:
                param_key = f"atr_{period}"
                try:
                    atr = vbt.ATR.run(
                        high = price_data["high"],
                        low = price_data["low"],
                        close = price_data["close"],
                        window = period,
                    )
                    results[param_key] = atr.atr
                    logger.debug(f"VectorBT ATR({period}) calculated successfully")
                except Exception as e:
                    logger.warning(
                        f"VectorBT ATR({period}) failed, using fallback: {e}"
                    )
                    # Fallback calculation
                    results[param_key] = self._calculate_atr_manual(
                        price_data["high"],
                        price_data["low"],
                        price_data["close"],
                        period,
                    )
        else:
            # Fallback to manual calculations
            results = {}
            for period in periods:
                param_key = f"atr_{period}"
                results[param_key] = self._calculate_atr_manual(
                    price_data.get("high", price_data["close"]),
                    price_data.get("low", price_data["close"]),
                    price_data["close"],
                    period,
                )

        self.indicator_cache[cache_key] = results
        return results

    def calculate_adaptive_parameters(
        self,
        price_data: pd.DataFrame,
        indicator_type: str,
        base_period: int,
        adaptation_speed: float = 0.1,
    ) -> pd.Series:
        """
        Calculate adaptive indicator parameters based on market conditions

        Args:
            price_data: DataFrame with OHLCV data
            indicator_type: Type of indicator ('rsi', 'macd', 'bb', etc.)
            base_period: Base period for the indicator
            adaptation_speed: Speed of parameter adaptation (0 - 1)

        Returns:
            Series of adaptive periods
        """
        # Calculate market regime and volatility
        returns = price_data["close"].pct_change()
        volatility = returns.rolling(20).std()
        trend_strength = abs(returns.rolling(20).mean())

        # Normalize volatility and trend
        vol_norm = (volatility - volatility.min()) / (
            volatility.max() - volatility.min() + 1e - 10
        )
        trend_norm = (trend_strength - trend_strength.min()) / (
            trend_strength.max() - trend_strength.min() + 1e - 10
        )

        # Calculate adaptive period based on market conditions
        if indicator_type in ["rsi", "stoch"]:
            # For oscillators: shorter periods in high volatility, longer in trends
            volatility_factor = 1 - (vol_norm * adaptation_speed)
            trend_factor = 1 + (trend_norm * adaptation_speed * 0.5)
            adaptive_period = base_period * volatility_factor * trend_factor
        elif indicator_type in ["ma", "ema"]:
            # For moving averages: shorter periods in trends, longer in choppy markets
            trend_factor = 1 - (trend_norm * adaptation_speed)
            adaptive_period = base_period * trend_factor
        else:
            # Default adaptation
            adaptive_period = base_period * (1 + (vol_norm - 0.5) * adaptation_speed)

        # Ensure reasonable bounds
        min_period = max(base_period * 0.5, 5)
        max_period = base_period * 2
        adaptive_period = adaptive_period.clip(min_period, max_period)

        return adaptive_period.round().astype(int)

    # Manual fallback calculations
    def _calculate_rsi_manual(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Manual RSI calculation"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window = period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window = period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _calculate_macd_manual(
        self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
    ) -> Dict[str, pd.Series]:
        """Manual MACD calculation"""
        ema_fast = prices.ewm(span = fast).mean()
        ema_slow = prices.ewm(span = slow).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span = signal).mean()
        histogram = macd_line - signal_line
        return {"macd": macd_line, "signal": signal_line, "histogram": histogram}

    def _calculate_bollinger_bands_manual(
        self, prices: pd.Series, period: int = 20, std_dev: float = 2.0
    ) -> Dict[str, pd.Series]:
        """Manual Bollinger Bands calculation"""
        middle = prices.rolling(window = period).mean()
        std = prices.rolling(window = period).std()
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        bandwidth = (upper - lower) / middle
        percent_b = (prices - lower) / (upper - lower)
        return {
            "upper": upper,
            "middle": middle,
            "lower": lower,
            "bandwidth": bandwidth,
            "percent_b": percent_b,
        }

    def _calculate_ma_manual(
        self, prices: pd.Series, period: int, ma_type: str = "sma"
    ) -> pd.Series:
        """Manual moving average calculation"""
        if ma_type == "sma":
            return prices.rolling(window = period).mean()
        elif ma_type == "ema":
            return prices.ewm(span = period).mean()
        else:
            raise ValueError(f"Unknown MA type: {ma_type}")

    def _calculate_stochastic_manual(
        self,
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        k_period: int = 14,
        d_period: int = 3,
    ) -> Dict[str, pd.Series]:
        """Manual Stochastic Oscillator calculation"""
        lowest_low = low.rolling(window = k_period).min()
        highest_high = high.rolling(window = k_period).max()
        k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        d_percent = k_percent.rolling(window = d_period).mean()
        return {"stoch_k": k_percent, "stoch_d": d_percent}

    def _calculate_atr_manual(
        self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14
    ) -> pd.Series:
        """Manual ATR calculation"""
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        true_range = pd.concat([tr1, tr2, tr3], axis = 1).max(axis = 1)
        atr = true_range.rolling(window = period).mean()
        return atr


class CrossIndicatorAnalyzer:
    """Cross - indicator analysis and signal fusion"""

    def __init__(self):
        """Initialize cross - indicator analyzer"""
        self.indicators = VectorizedTechnicalIndicators()
        self.signal_weights = {
            "trend": 0.4,
            "momentum": 0.3,
            "volatility": 0.2,
            "volume": 0.1,
        }

    def analyze_indicator_correlation(
        self, indicators: Dict[str, pd.Series], method: str = "pearson"
    ) -> pd.DataFrame:
        """
        Analyze correlation between indicators

        Args:
            indicators: Dictionary of indicator series
            method: Correlation method ('pearson', 'spearman')

        Returns:
            Correlation matrix DataFrame
        """
        # Create DataFrame from indicators
        indicator_df = pd.DataFrame(indicators)

        # Calculate correlation matrix
        correlation_matrix = indicator_df.corr(method = method)

        return correlation_matrix

    def generate_weighted_signals(
        self,
        price_data: pd.DataFrame,
        indicators: Dict[str, Any],
        weights: Optional[Dict[str, float]] = None,
    ) -> pd.Series:
        """
        Generate weighted signals from multiple indicators

        Args:
            price_data: Price data for signal generation
            indicators: Dictionary of calculated indicators
            weights: Optional custom weights for indicators

        Returns:
            Combined signal series (-1 to 1)
        """
        if weights is None:
            weights = self.signal_weights

        signals = pd.Series(0.0, index = price_data.index)

        # Process each indicator type
        for indicator_name, indicator_data in indicators.items():
            indicator_signals = self._indicator_to_signals(
                indicator_name, indicator_data
            )

            # Apply category weight
            category = self._get_indicator_category(indicator_name)
            category_weight = weights.get(category, 0.25)

            # Add to combined signals
            signals += indicator_signals * category_weight

        # Normalize signals to -1 to 1 range
        if signals.abs().max() > 0:
            signals = signals / signals.abs().max()

        return signals

    def detect_regime_based_signals(
        self, price_data: pd.DataFrame, indicators: Dict[str, Any]
    ) -> Dict[str, pd.Series]:
        """
        Detect regime - based signals

        Args:
            price_data: Price data
            indicators: Dictionary of indicators

        Returns:
            Dictionary of regime - based signals
        """
        returns = price_data["close"].pct_change()
        volatility = returns.rolling(20).std()

        # Define market regimes
        trending_regime = abs(returns.rolling(50).mean()) > returns.rolling(50).std()
        volatile_regime = volatility > volatility.rolling(100).mean()
        calm_regime = ~(trending_regime | volatile_regime)

        regime_signals = {}

        # Trending regime signals
        if "ma" in str(indicators.keys()).lower():
            regime_signals["trending"] = self._generate_trending_signals(
                price_data, indicators, trending_regime
            )

        # Volatile regime signals
        if "bb" in str(indicators.keys()).lower():
            regime_signals["volatile"] = self._generate_volatility_signals(
                price_data, indicators, volatile_regime
            )

        # Calm regime signals
        regime_signals["calm"] = self._generate_mean_reversion_signals(
            price_data, indicators, calm_regime
        )

        return regime_signals

    def _indicator_to_signals(
        self, indicator_name: str, indicator_data: Any
    ) -> pd.Series:
        """Convert indicator values to signals"""
        if isinstance(indicator_data, pd.Series):
            if "rsi" in indicator_name.lower():
                # RSI signals: >70 = sell, <30 = buy
                signals = np.where(
                    indicator_data > 70, -1, np.where(indicator_data < 30, 1, 0)
                )
                return pd.Series(signals, index = indicator_data.index)

            elif "macd" in indicator_name.lower():
                # MACD signals: positive = buy, negative = sell
                if isinstance(indicator_data, dict) and "macd" in indicator_data:
                    signals = np.where(indicator_data["macd"] > 0, 1, -1)
                    return pd.Series(signals, index = indicator_data["macd"].index)

            elif "stoch" in indicator_name.lower():
                # Stochastic signals: >80 = sell, <20 = buy
                if isinstance(indicator_data, dict) and "stoch_k" in indicator_data:
                    signals = np.where(
                        indicator_data["stoch_k"] > 80,
                        -1,
                        np.where(indicator_data["stoch_k"] < 20, 1, 0),
                    )
                    return pd.Series(signals, index = indicator_data["stoch_k"].index)

        # Default neutral signal
        if isinstance(indicator_data, pd.Series):
            return pd.Series(0, index = indicator_data.index)
        elif isinstance(indicator_data, dict) and "macd" in indicator_data:
            return pd.Series(0, index = indicator_data["macd"].index)
        else:
            return pd.Series(0)

    def _get_indicator_category(self, indicator_name: str) -> str:
        """Get indicator category from name"""
        indicator_name_lower = indicator_name.lower()

        if any(x in indicator_name_lower for x in ["rsi", "macd", "stoch"]):
            return "momentum"
        elif any(x in indicator_name_lower for x in ["ma", "ema"]):
            return "trend"
        elif any(x in indicator_name_lower for x in ["bb", "atr"]):
            return "volatility"
        elif "volume" in indicator_name_lower:
            return "volume"
        else:
            return "momentum"  # Default

    def _generate_trending_signals(self, price_data, indicators, regime_mask):
        """Generate signals for trending regime"""
        signals = pd.Series(0.0, index = price_data.index)

        if regime_mask.any():
            # Use moving average crossovers in trending markets
            for indicator_name, indicator_data in indicators.items():
                if "ma" in indicator_name.lower() and isinstance(
                    indicator_data, pd.Series
                ):
                    # Simple MA crossover logic
                    ma_values = indicator_data[regime_mask]
                    if len(ma_values) > 1:
                        crossover = (ma_values.diff() > 0).astype(float)
                        crossover = crossover.reindex(signals.index, fill_value = 0)
                        signals[regime_mask] += crossover

        return signals

    def _generate_volatility_signals(self, price_data, indicators, regime_mask):
        """Generate signals for volatile regime"""
        signals = pd.Series(0.0, index = price_data.index)

        if regime_mask.any():
            # Use Bollinger Bands in volatile markets
            for indicator_name, indicator_data in indicators.items():
                if "bb" in indicator_name.lower() and isinstance(indicator_data, dict):
                    if "percent_b" in indicator_data:
                        # Bollinger Band %B signals
                        bb_percent = indicator_data["percent_b"][regime_mask]
                        if len(bb_percent) > 1:
                            band_signals = np.where(
                                bb_percent > 0.8, -1, np.where(bb_percent < 0.2, 1, 0)
                            )
                            band_series = pd.Series(
                                band_signals, index = bb_percent.index
                            )
                            band_series = band_series.reindex(
                                signals.index, fill_value = 0
                            )
                            signals[regime_mask] += band_series

        return signals

    def _generate_mean_reversion_signals(self, price_data, indicators, regime_mask):
        """Generate signals for calm regime"""
        signals = pd.Series(0.0, index = price_data.index)

        if regime_mask.any():
            # Use RSI for mean reversion in calm markets
            for indicator_name, indicator_data in indicators.items():
                if "rsi" in indicator_name.lower() and isinstance(
                    indicator_data, pd.Series
                ):
                    rsi_values = indicator_data[regime_mask]
                    if len(rsi_values) > 1:
                        rsi_signals = np.where(
                            rsi_values > 70, -1, np.where(rsi_values < 30, 1, 0)
                        )
                        rsi_series = pd.Series(rsi_signals, index = rsi_values.index)
                        rsi_series = rsi_series.reindex(signals.index, fill_value = 0)
                        signals[regime_mask] += rsi_series

        return signals


class AdaptiveIndicatorParameters:
    """Adaptive indicator parameter adjustment system"""

    def __init__(self):
        """Initialize adaptive parameter system"""
        self.parameter_history = {}
        self.market_regime = None

    def optimize_indicator_parameters(
        self,
        price_data: pd.DataFrame,
        indicator_type: str,
        optimization_window: int = 252,
        rebalance_frequency: int = 20,
    ) -> Dict[int, Dict[str, float]]:
        """
        Optimize indicator parameters over rolling windows

        Args:
            price_data: Price data for optimization
            indicator_type: Type of indicator to optimize
            optimization_window: Window size for parameter optimization
            rebalance_frequency: Frequency of parameter rebalancing

        Returns:
            Dictionary mapping timestamps to optimal parameters
        """
        optimal_params = {}

        # Iterate through data in optimization windows
        for i in range(optimization_window, len(price_data), rebalance_frequency):
            window_end = price_data.index[i]
            window_start = price_data.index[i - optimization_window]

            window_data = price_data.loc[window_start:window_end]

            # Optimize parameters for this window
            params = self._optimize_single_window(window_data, indicator_type)
            optimal_params[window_end] = params

        return optimal_params

    def _optimize_single_window(
        self, price_data: pd.DataFrame, indicator_type: str
    ) -> Dict[str, float]:
        """Optimize parameters for a single time window"""
        if indicator_type == "rsi":
            return self._optimize_rsi_parameters(price_data)
        elif indicator_type == "macd":
            return self._optimize_macd_parameters(price_data)
        elif indicator_type == "bb":
            return self._optimize_bb_parameters(price_data)
        else:
            return {}

    def _optimize_rsi_parameters(self, price_data: pd.DataFrame) -> Dict[str, float]:
        """Optimize RSI parameters"""
        returns = price_data["close"].pct_change()
        best_sharpe = -np.inf
        best_period = 14

        for period in range(5, 31, 2):  # Test odd periods from 5 to 29
            rsi = VectorizedTechnicalIndicators()._calculate_rsi_manual(
                price_data["close"], period
            )

            # Generate signals
            signals = np.where(rsi > 70, -1, np.where(rsi < 30, 1, 0))

            # Calculate performance
            strategy_returns = signals[:-1] * returns[1:]  # Align with returns

            if len(strategy_returns) > 30:
                sharpe = strategy_returns.mean() / strategy_returns.std() * np.sqrt(252)
                if sharpe > best_sharpe:
                    best_sharpe = sharpe
                    best_period = period

        return {"period": best_period, "sharpe": best_sharpe}

    def _optimize_macd_parameters(self, price_data: pd.DataFrame) -> Dict[str, float]:
        """Optimize MACD parameters"""
        returns = price_data["close"].pct_change()
        best_sharpe = -np.inf
        best_params = {"fast": 12, "slow": 26, "signal": 9}

        # Test parameter combinations
        for fast in [8, 10, 12, 15]:
            for slow in [21, 24, 26, 30]:
                for signal in [6, 8, 9, 12]:
                    if fast < slow:
                        macd_data = (
                            VectorizedTechnicalIndicators()._calculate_macd_manual(
                                price_data["close"], fast, slow, signal
                            )
                        )

                        # Generate signals based on MACD crossover
                        signals = np.where(
                            macd_data["macd"] > macd_data["signal"], 1, -1
                        )

                        # Calculate performance
                        strategy_returns = signals[:-1] * returns[1:]

                        if len(strategy_returns) > 30:
                            sharpe = (
                                strategy_returns.mean()
                                / strategy_returns.std()
                                * np.sqrt(252)
                            )
                            if sharpe > best_sharpe:
                                best_sharpe = sharpe
                                best_params = {
                                    "fast": fast,
                                    "slow": slow,
                                    "signal": signal,
                                }

        best_params["sharpe"] = best_sharpe
        return best_params

    def _optimize_bb_parameters(self, price_data: pd.DataFrame) -> Dict[str, float]:
        """Optimize Bollinger Band parameters"""
        returns = price_data["close"].pct_change()
        best_sharpe = -np.inf
        best_params = {"period": 20, "std_dev": 2.0}

        for period in [10, 15, 20, 25]:
            for std_dev in [1.5, 2.0, 2.5]:
                bb_data = (
                    VectorizedTechnicalIndicators()._calculate_bollinger_bands_manual(
                        price_data["close"], period, std_dev
                    )
                )

                # Generate signals based on Bollinger Bands
                signals = np.where(
                    price_data["close"] > bb_data["upper"],
                    -1,
                    np.where(price_data["close"] < bb_data["lower"], 1, 0),
                )

                # Calculate performance
                strategy_returns = signals[:-1] * returns[1:]

                if len(strategy_returns) > 30:
                    sharpe = (
                        strategy_returns.mean() / strategy_returns.std() * np.sqrt(252)
                    )
                    if sharpe > best_sharpe:
                        best_sharpe = sharpe
                        best_params = {"period": period, "std_dev": std_dev}

        best_params["sharpe"] = best_sharpe
        return best_params


# Utility functions


def benchmark_indicator_performance(
    price_data: pd.DataFrame,
    indicators: Dict[str, Any],
    benchmark_returns: Optional[pd.Series] = None,
) -> Dict[str, IndicatorPerformance]:
    """
    Benchmark individual indicator performance

    Args:
        price_data: Price data for backtesting
        indicators: Dictionary of calculated indicators
        benchmark_returns: Optional benchmark returns

    Returns:
        Dictionary of indicator performance metrics
    """
    returns = price_data["close"].pct_change()
    performance_results = {}

    for indicator_name, indicator_data in indicators.items():
        # Generate signals
        if isinstance(indicator_data, pd.Series):
            signals = np.where(indicator_data > indicator_data.mean(), 1, -1)
        elif isinstance(indicator_data, dict) and "macd" in indicator_data:
            signals = np.where(indicator_data["macd"] > 0, 1, -1)
        else:
            continue

        # Calculate strategy returns
        strategy_returns = signals[:-1] * returns[1:]

        if len(strategy_returns) > 30:
            # Calculate performance metrics
            total_return = (1 + strategy_returns).prod() - 1
            sharpe_ratio = (
                strategy_returns.mean() / strategy_returns.std() * np.sqrt(252)
            )
            win_rate = (strategy_returns > 0).mean()
            max_drawdown = self._calculate_max_drawdown(strategy_returns)

            signal_count = len(signals[signals != 0])
            profitable_signals = (strategy_returns > 0).sum()
            avg_signal_return = (
                strategy_returns[strategy_returns != 0].mean()
                if len(strategy_returns[strategy_returns != 0]) > 0
                else 0
            )
            hit_rate = profitable_signals / signal_count if signal_count > 0 else 0

            performance_results[indicator_name] = IndicatorPerformance(
                indicator_name = indicator_name,
                total_return = total_return,
                sharpe_ratio = sharpe_ratio,
                win_rate = win_rate,
                max_drawdown = max_drawdown,
                signal_count = int(signal_count),
                profitable_signals = int(profitable_signals),
                avg_signal_return = avg_signal_return,
                hit_rate = hit_rate,
            )

    return performance_results


def _calculate_max_drawdown(returns: pd.Series) -> float:
    """Calculate maximum drawdown"""
    cumulative = (1 + returns).cumprod()
    running_max = cumulative.expanding().max()
    drawdown = (cumulative - running_max) / running_max
    return drawdown.min()


# Example usage
def test_enhanced_technical_indicators():
    """Test enhanced technical indicators system"""
    logger.info("Testing enhanced technical indicators...")

    # Create test data
    dates = pd.date_range("2023 - 01 - 01", periods = 252, freq="D")
    np.random.seed(42)
    prices = 100 + np.cumsum(np.random.normal(0.001, 0.02, 252))
    high = prices * (1 + np.random.uniform(0, 0.02, 252))
    low = prices * (1 - np.random.uniform(0, 0.02, 252))
    volume = np.random.randint(1000000, 10000000, 252)

    price_data = pd.DataFrame(
        {
            "open": prices * (1 + np.random.normal(0, 0.005, 252)),
            "high": high,
            "low": low,
            "close": prices,
            "volume": volume,
        },
        index = dates,
    )

    # Initialize enhanced indicators
    enhanced_indicators = VectorizedTechnicalIndicators()

    # Test vectorized calculations
    logger.info("Testing vectorized RSI...")
    rsi_results = enhanced_indicators.calculate_rsi_vectorized(price_data, [14, 21])

    logger.info("Testing vectorized MACD...")
    macd_results = enhanced_indicators.calculate_macd_vectorized(price_data)

    logger.info("Testing vectorized Bollinger Bands...")
    bb_results = enhanced_indicators.calculate_bollinger_bands_vectorized(price_data)

    logger.info("Testing vectorized Moving Averages...")
    ma_results = enhanced_indicators.calculate_moving_averages_vectorized(price_data)

    logger.info("Testing Stochastic Oscillator...")
    stoch_results = enhanced_indicators.calculate_stochastic_oscillator_vectorized(
        price_data
    )

    logger.info("Testing ATR...")
    atr_results = enhanced_indicators.calculate_atr_vectorized(price_data)

    # Test adaptive parameters
    logger.info("Testing adaptive parameters...")
    adaptive_rsi_period = enhanced_indicators.calculate_adaptive_parameters(
        price_data, "rsi", 14, adaptation_speed = 0.2
    )

    # Test cross - indicator analysis
    logger.info("Testing cross - indicator analysis...")
    analyzer = CrossIndicatorAnalyzer()

    # Combine all indicators for analysis
    all_indicators = {}
    all_indicators.update(rsi_results)
    all_indicators.update({f"{k}_macd": v["macd"] for k, v in macd_results.items()})
    all_indicators.update({f"{k}_upper": v["upper"] for k, v in bb_results.items()})
    all_indicators.update(ma_results)

    correlation_matrix = analyzer.analyze_indicator_correlation(all_indicators)

    logger.info(f"✓ Enhanced technical indicators test completed:")
    logger.info(f"  RSI indicators: {len(rsi_results)}")
    logger.info(f"  MACD indicators: {len(macd_results)}")
    logger.info(f"  Bollinger Band indicators: {len(bb_results)}")
    logger.info(f"  Moving Average indicators: {len(ma_results)}")
    logger.info(f"  Stochastic indicators: {len(stoch_results)}")
    logger.info(f"  ATR indicators: {len(atr_results)}")
    logger.info(f"  Correlation matrix: {correlation_matrix.shape}")

    return {
        "rsi": rsi_results,
        "macd": macd_results,
        "bollinger_bands": bb_results,
        "moving_averages": ma_results,
        "stochastic": stoch_results,
        "atr": atr_results,
        "adaptive_parameters": adaptive_rsi_period,
        "correlation_matrix": correlation_matrix,
    }


if __name__ == "__main__":
    # Test enhanced technical indicators
    results = test_enhanced_technical_indicators()
