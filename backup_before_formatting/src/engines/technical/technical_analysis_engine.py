"""
Technical Analysis Engine Implementation
技術分析引擎實現

Enhanced technical analysis engine with comprehensive indicator calculations,
pattern recognition, and trend analysis capabilities.
增強的技術分析引擎，包含全面的指標計算、形態識別和趨勢分析功能。
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

from ..base.base_engine import BaseEngine, EngineConfig, EngineResult
from ...core.logging import log_performance


class TechnicalAnalysisEngine(BaseEngine):
    """
    Enhanced Technical Analysis Engine

    Provides comprehensive technical analysis capabilities including:
    - Trend indicators (SMA, EMA, MACD)
    - Momentum indicators (RSI, Stochastic)
    - Volatility indicators (Bollinger Bands, ATR)
    - Volume indicators (OBV, Volume MA)
    - Pattern recognition
    - Trend analysis
    """

    def __init__(self, config: Optional[EngineConfig] = None):
        """
        Initialize technical analysis engine.

        Args:
            config: Engine configuration
        """
        if config is None:
            config = EngineConfig(
                name="technical_analysis",
                version="2.0.0",
                timeout_seconds=60,
                cache_enabled=True,
                cache_ttl=300
            )

        super().__init__(config)

        # Indicator configurations
        self.indicator_configs = {
            "sma_periods": [5, 10, 20, 50, 200],
            "ema_periods": [12, 26],
            "rsi_period": 14,
            "macd_fast": 12,
            "macd_slow": 26,
            "macd_signal": 9,
            "bollinger_period": 20,
            "bollinger_std": 2,
            "atr_period": 14,
            "stoch_k": 14,
            "stoch_d": 3,
            "volume_ma_periods": [10, 20]
        }

        self.logger.info(
            "Technical Analysis Engine initialized",
            config=self.indicator_configs
        )

    async def _analyze(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Perform comprehensive technical analysis.

        Args:
            data: OHLCV data for analysis
            **kwargs: Additional parameters
                - indicators: List of specific indicators to calculate
                - include_patterns: Whether to include pattern analysis
                - trend_period: Period for trend analysis

        Returns:
            Dictionary with technical analysis results
        """
        if not await self.validate_input(data):
            raise ValueError("Invalid input data for technical analysis")

        df = self._prepare_dataframe(data)

        # Get requested indicators or calculate all
        requested_indicators = kwargs.get("indicators", "all")
        include_patterns = kwargs.get("include_patterns", True)
        trend_period = kwargs.get("trend_period", 20)

        results = {
            "symbol": data.get("symbol", "UNKNOWN"),
            "data_points": len(df),
            "latest_price": float(df["close"].iloc[-1]),
            "price_change": self._calculate_price_change(df),
            "analysis_timestamp": datetime.now().isoformat()
        }

        # Calculate indicators
        indicators = await self._calculate_indicators(df, requested_indicators)
        results["indicators"] = indicators

        # Perform trend analysis
        trend_analysis = await self._analyze_trend(df, trend_period)
        results["trend_analysis"] = trend_analysis

        # Pattern analysis if requested
        if include_patterns:
            patterns = await self._analyze_patterns(df)
            results["patterns"] = patterns

        # Generate trading signals
        signals = await self._generate_signals(df, indicators)
        results["signals"] = signals

        # Support and resistance levels
        support_resistance = await self._calculate_support_resistance(df)
        results["support_resistance"] = support_resistance

        return results

    def _prepare_dataframe(self, data: Dict[str, Any]) -> pd.DataFrame:
        """Prepare and validate dataframe for analysis."""
        if "data" in data:
            df = pd.DataFrame(data["data"])
        else:
            df = pd.DataFrame(data)

        # Ensure required columns exist
        required_columns = ["open", "high", "low", "close"]
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"Missing required column: {col}")

        # Convert to numeric
        for col in required_columns + ["volume"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # Add volume if not present
        if "volume" not in df.columns:
            df["volume"] = 0

        # Remove rows with NaN values in essential columns
        df = df.dropna(subset=["close"])

        # Sort by index/date if available
        if "timestamp" in df.columns:
            df = df.sort_values("timestamp")
        elif "date" in df.columns:
            df = df.sort_values("date")
        else:
            df = df.reset_index(drop=True)

        return df

    @log_performance("calculate_indicators")
    async def _calculate_indicators(
        self,
        df: pd.DataFrame,
        requested_indicators: Union[str, List[str]] = "all"
    ) -> Dict[str, Any]:
        """Calculate technical indicators."""
        indicators = {}
        close = df["close"]

        # Trend indicators
        if requested_indicators == "all" or "trend" in requested_indicators:
            indicators.update(self._calculate_trend_indicators(df))

        # Momentum indicators
        if requested_indicators == "all" or "momentum" in requested_indicators:
            indicators.update(self._calculate_momentum_indicators(df))

        # Volatility indicators
        if requested_indicators == "all" or "volatility" in requested_indicators:
            indicators.update(self._calculate_volatility_indicators(df))

        # Volume indicators
        if requested_indicators == "all" or "volume" in requested_indicators:
            indicators.update(self._calculate_volume_indicators(df))

        return indicators

    def _calculate_trend_indicators(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate trend-based indicators."""
        indicators = {}
        close = df["close"]

        # Simple Moving Averages
        for period in self.indicator_configs["sma_periods"]:
            if len(close) >= period:
                sma = close.rolling(window=period).mean()
                indicators[f"sma_{period}"] = float(sma.iloc[-1])

        # Exponential Moving Averages
        for period in self.indicator_configs["ema_periods"]:
            if len(close) >= period:
                ema = close.ewm(span=period).mean()
                indicators[f"ema_{period}"] = float(ema.iloc[-1])

        return indicators

    def _calculate_momentum_indicators(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate momentum-based indicators."""
        indicators = {}
        close = df["close"]

        # RSI
        rsi_period = self.indicator_configs["rsi_period"]
        if len(close) >= rsi_period + 1:
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
            rs = gain / loss.replace(0, np.nan)
            rsi = 100 - (100 / (1 + rs))
            indicators["rsi"] = float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50.0

        # MACD
        fast = self.indicator_configs["macd_fast"]
        slow = self.indicator_configs["macd_slow"]
        signal = self.indicator_configs["macd_signal"]

        if len(close) >= slow + signal:
            ema_fast = close.ewm(span=fast).mean()
            ema_slow = close.ewm(span=slow).mean()
            macd_line = ema_fast - ema_slow
            signal_line = macd_line.ewm(span=signal).mean()
            histogram = macd_line - signal_line

            indicators["macd"] = float(macd_line.iloc[-1])
            indicators["macd_signal"] = float(signal_line.iloc[-1])
            indicators["macd_histogram"] = float(histogram.iloc[-1])

        # Stochastic Oscillator
        k_period = self.indicator_configs["stoch_k"]
        d_period = self.indicator_configs["stoch_d"]

        if len(df) >= k_period + d_period:
            low_min = df["low"].rolling(window=k_period).min()
            high_max = df["high"].rolling(window=k_period).max()
            k_percent = 100 * ((close - low_min) / (high_max - low_min))
            d_percent = k_percent.rolling(window=d_period).mean()

            indicators["stoch_k"] = float(k_percent.iloc[-1]) if not pd.isna(k_percent.iloc[-1]) else 50.0
            indicators["stoch_d"] = float(d_percent.iloc[-1]) if not pd.isna(d_percent.iloc[-1]) else 50.0

        return indicators

    def _calculate_volatility_indicators(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate volatility-based indicators."""
        indicators = {}
        close = df["close"]

        # Bollinger Bands
        period = self.indicator_configs["bollinger_period"]
        std_multiplier = self.indicator_configs["bollinger_std"]

        if len(close) >= period:
            sma = close.rolling(window=period).mean()
            std = close.rolling(window=period).std()

            indicators["bb_upper"] = float((sma + std_multiplier * std).iloc[-1])
            indicators["bb_middle"] = float(sma.iloc[-1])
            indicators["bb_lower"] = float((sma - std_multiplier * std).iloc[-1])
            indicators["bb_width"] = indicators["bb_upper"] - indicators["bb_lower"]

        # Average True Range (ATR)
        atr_period = self.indicator_configs["atr_period"]
        if len(df) >= atr_period:
            high = df["high"]
            low = df["low"]
            close_shift = close.shift(1)

            tr1 = high - low
            tr2 = abs(high - close_shift)
            tr3 = abs(low - close_shift)

            true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = true_range.rolling(window=atr_period).mean()
            indicators["atr"] = float(atr.iloc[-1]) if not pd.isna(atr.iloc[-1]) else 0.0

        return indicators

    def _calculate_volume_indicators(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate volume-based indicators."""
        indicators = {}
        volume = df["volume"]

        if volume.sum() > 0:  # Only calculate if volume data exists
            # Volume Moving Averages
            for period in self.indicator_configs["volume_ma_periods"]:
                if len(volume) >= period:
                    vol_ma = volume.rolling(window=period).mean()
                    indicators[f"volume_ma_{period}"] = float(vol_ma.iloc[-1])

            # On-Balance Volume (OBV)
            close = df["close"]
            if len(close) >= 2:
                obv = np.where(close > close.shift(), volume,
                      np.where(close < close.shift(), -volume, 0)).cumsum()
                indicators["obv"] = float(obv[-1])

        return indicators

    async def _analyze_trend(self, df: pd.DataFrame, period: int = 20) -> Dict[str, Any]:
        """Analyze price trend."""
        if len(df) < period:
            return {"trend": "INSUFFICIENT_DATA"}

        close = df["close"]
        current_price = close.iloc[-1]

        # Calculate moving averages
        sma_short = close.rolling(window=period // 2).mean().iloc[-1]
        sma_long = close.rolling(window=period).mean().iloc[-1]

        # Determine trend direction
        if current_price > sma_short > sma_long:
            trend_direction = "UP"
            trend_strength = "STRONG"
        elif current_price > sma_short and current_price > sma_long:
            trend_direction = "UP"
            trend_strength = "MODERATE"
        elif current_price < sma_short < sma_long:
            trend_direction = "DOWN"
            trend_strength = "STRONG"
        elif current_price < sma_short and current_price < sma_long:
            trend_direction = "DOWN"
            trend_strength = "MODERATE"
        else:
            trend_direction = "SIDEWAYS"
            trend_strength = "WEAK"

        # Calculate momentum
        price_change = (current_price - close.iloc[-period]) / close.iloc[-period] * 100

        return {
            "direction": trend_direction,
            "strength": trend_strength,
            "momentum_percent": round(price_change, 2),
            "current_price": float(current_price),
            "sma_short": float(sma_short),
            "sma_long": float(sma_long)
        }

    async def _analyze_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze candlestick patterns (simplified version)."""
        if len(df) < 3:
            return {"patterns": []}

        patterns = []
        recent_candles = df.tail(3)

        # Simple pattern recognition
        latest = recent_candles.iloc[-1]
        prev = recent_candles.iloc[-2]

        # Doji pattern
        body_size = abs(latest["close"] - latest["open"])
        range_size = latest["high"] - latest["low"]
        if body_size < range_size * 0.1:  # Body less than 10% of range
            patterns.append({
                "name": "DOJI",
                "signal": "NEUTRAL",
                "strength": "MODERATE"
            })

        # Hammer pattern
        lower_shadow = latest["open"] - latest["low"] if latest["close"] > latest["open"] else latest["close"] - latest["low"]
        upper_shadow = latest["high"] - (latest["open"] if latest["close"] > latest["open"] else latest["close"])
        if lower_shadow > 2 * body_size and upper_shadow < body_size * 0.5:
            patterns.append({
                "name": "HAMMER",
                "signal": "BULLISH",
                "strength": "MODERATE"
            })

        return {"patterns": patterns}

    async def _generate_signals(
        self,
        df: pd.DataFrame,
        indicators: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate trading signals based on indicators."""
        signals = {
            "overall_signal": "NEUTRAL",
            "confidence": 0.0,
            "individual_signals": {}
        }

        signal_votes = []

        # RSI signals
        if "rsi" in indicators:
            rsi = indicators["rsi"]
            if rsi < 30:
                signals["individual_signals"]["rsi"] = "BUY"
                signal_votes.append("BUY")
            elif rsi > 70:
                signals["individual_signals"]["rsi"] = "SELL"
                signal_votes.append("SELL")
            else:
                signals["individual_signals"]["rsi"] = "NEUTRAL"

        # MACD signals
        if "macd" in indicators and "macd_signal" in indicators:
            macd = indicators["macd"]
            macd_signal = indicators["macd_signal"]
            if macd > macd_signal and indicators.get("macd_histogram", 0) > 0:
                signals["individual_signals"]["macd"] = "BUY"
                signal_votes.append("BUY")
            elif macd < macd_signal and indicators.get("macd_histogram", 0) < 0:
                signals["individual_signals"]["macd"] = "SELL"
                signal_votes.append("SELL")
            else:
                signals["individual_signals"]["macd"] = "NEUTRAL"

        # Bollinger Bands signals
        if "bb_upper" in indicators and "bb_lower" in indicators:
            current_price = df["close"].iloc[-1]
            bb_upper = indicators["bb_upper"]
            bb_lower = indicators["bb_lower"]

            if current_price <= bb_lower:
                signals["individual_signals"]["bollinger"] = "BUY"
                signal_votes.append("BUY")
            elif current_price >= bb_upper:
                signals["individual_signals"]["bollinger"] = "SELL"
                signal_votes.append("SELL")
            else:
                signals["individual_signals"]["bollinger"] = "NEUTRAL"

        # Calculate overall signal and confidence
        if signal_votes:
            buy_votes = signal_votes.count("BUY")
            sell_votes = signal_votes.count("SELL")
            total_votes = len(signal_votes)

            if buy_votes > sell_votes:
                signals["overall_signal"] = "BUY"
                signals["confidence"] = buy_votes / total_votes
            elif sell_votes > buy_votes:
                signals["overall_signal"] = "SELL"
                signals["confidence"] = sell_votes / total_votes
            else:
                signals["overall_signal"] = "NEUTRAL"
                signals["confidence"] = 0.5

        signals["confidence"] = round(signals["confidence"] * 100, 1)

        return signals

    async def _calculate_support_resistance(
        self,
        df: pd.DataFrame,
        lookback_periods: List[int] = [10, 20, 50]
    ) -> Dict[str, Any]:
        """Calculate support and resistance levels."""
        if len(df) < max(lookback_periods):
            return {"support": [], "resistance": []}

        high = df["high"]
        low = df["low"]
        current_price = df["close"].iloc[-1]

        support_levels = []
        resistance_levels = []

        for period in lookback_periods:
            if len(df) >= period:
                # Recent highs and lows
                recent_high = high.tail(period).max()
                recent_low = low.tail(period).min()

                # Check if they're valid support/resistance
                if recent_low < current_price * 0.95:  # Within 5% of current price
                    support_levels.append({
                        "level": float(recent_low),
                        "period": period,
                        "strength": "MODERATE"
                    })

                if recent_high > current_price * 1.05:  # Within 5% of current price
                    resistance_levels.append({
                        "level": float(recent_high),
                        "period": period,
                        "strength": "MODERATE"
                    })

        return {
            "support": sorted(support_levels, key=lambda x: x["level"], reverse=True),
            "resistance": sorted(resistance_levels, key=lambda x: x["level"])
        }

    def _calculate_price_change(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate price change metrics."""
        if len(df) < 2:
            return {"change": 0.0, "change_percent": 0.0}

        current_price = df["close"].iloc[-1]
        previous_price = df["close"].iloc[-2]

        change = current_price - previous_price
        change_percent = (change / previous_price) * 100 if previous_price > 0 else 0.0

        return {
            "change": round(change, 2),
            "change_percent": round(change_percent, 2)
        }

    async def validate_input(self, data: Dict[str, Any]) -> bool:
        """Validate input data for technical analysis."""
        if not await super().validate_input(data):
            return False

        # Check for OHLCV data
        required_keys = ["data"]
        if not all(key in data for key in required_keys):
            # Check if direct OHLCV columns are provided
            ohlcv_keys = ["open", "high", "low", "close"]
            if not all(key in data for key in ohlcv_keys):
                self.logger.warning("Missing required OHLCV data")
                return False

        # Validate data structure
        if "data" in data:
            data_points = data["data"]
            if not isinstance(data_points, list) or len(data_points) < 2:
                self.logger.warning("Insufficient data points for analysis")
                return False

            # Check first data point structure
            sample = data_points[0] if data_points else {}
            required_columns = ["open", "high", "low", "close"]
            if not all(col in sample for col in required_columns):
                self.logger.warning("Missing required OHLCV columns in data points")
                return False

        return True