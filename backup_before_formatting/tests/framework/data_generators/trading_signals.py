"""
Trading signal generator for testing purposes.
"""

import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


class TradingSignalGenerator:
    """Generate realistic trading signals for testing."""

    def __init__(self):
        self.random = random.Random(42)  # Fixed seed for reproducible tests

    def generate_signals(
        self,
        symbols: List[str],
        count: int = 10,
        types: List[str] = None,
        confidence_range: Tuple[float, float] = (0.6, 0.95),
        timestamp_range: Optional[Tuple[datetime, datetime]] = None,
    ) -> List[Dict[str, Any]]:
        """Generate trading signals."""
        if types is None:
            types = ["BUY", "SELL", "HOLD"]

        if timestamp_range is None:
            end_time = datetime.now()
            start_time = end_time - timedelta(days=1)
        else:
            start_time, end_time = timestamp_range

        signals = []

        for i in range(count):
            symbol = self.random.choice(symbols)
            signal_type = self.random.choice(types)
            confidence = self.random.uniform(*confidence_range)

            # Generate timestamp within range
            timestamp = start_time + timedelta(
                seconds=self.random.randint(
                    0, int((end_time - start_time).total_seconds())
                )
            )

            # Generate signal metadata
            signal = {
                "signal_id": f"signal_{i:06d}",
                "symbol": symbol,
                "signal": signal_type,
                "confidence": round(confidence, 3),
                "timestamp": timestamp.isoformat(),
                "strategy": self.random.choice(
                    [
                        "RSI",
                        "MACD",
                        "BollingerBands",
                        "Momentum",
                        "MeanReversion",
                        "Breakout",
                        "TrendFollowing",
                    ]
                ),
                "timeframe": self.random.choice(["1m", "5m", "15m", "1h", "4h", "1d"]),
                "price": round(np.random.uniform(50, 500), 2),
                "volume": int(np.random.uniform(1000, 100000)),
                "metadata": self._generate_signal_metadata(signal_type, confidence),
            }

            signals.append(signal)

        return signals

    def _generate_signal_metadata(
        self, signal_type: str, confidence: float
    ) -> Dict[str, Any]:
        """Generate metadata for trading signal."""
        metadata = {
            "indicators": {},
            "reasoning": "Signal generated based on technical analysis",
            "risk_level": (
                "low" if confidence > 0.8 else "medium" if confidence > 0.6 else "high"
            ),
        }

        # Add indicator values based on signal type
        if signal_type == "BUY":
            metadata["indicators"] = {
                "rsi": np.random.uniform(20, 35),
                "macd": np.random.uniform(-0.5, -0.1),
                "price_above_sma": True,
                "volume_spike": np.random.choice([True, False], p=[0.6, 0.4]),
            }
            metadata["reasoning"] = "Oversold conditions with bullish momentum"
        elif signal_type == "SELL":
            metadata["indicators"] = {
                "rsi": np.random.uniform(65, 85),
                "macd": np.random.uniform(0.1, 0.5),
                "price_below_sma": True,
                "volume_spike": np.random.choice([True, False], p=[0.4, 0.6]),
            }
            metadata["reasoning"] = "Overbought conditions with bearish divergence"
        else:  # HOLD
            metadata["indicators"] = {
                "rsi": np.random.uniform(40, 60),
                "macd": np.random.uniform(-0.1, 0.1),
                "price_near_sma": True,
                "volume_spike": False,
            }
            metadata["reasoning"] = "Neutral conditions, waiting for clearer signal"

        return metadata

    def generate_signal_series(
        self,
        symbol: str,
        start_date: datetime,
        days: int,
        frequency: str = "1h",
        strategy: str = "RSI",
    ) -> pd.DataFrame:
        """Generate a time series of trading signals for a single symbol."""
        # Calculate number of signals
        freq_to_hours = {
            "1min": 1 / 60,
            "5min": 5 / 60,
            "15min": 15 / 60,
            "30min": 30 / 60,
            "1h": 1,
            "4h": 4,
            "1d": 24,
        }

        if frequency not in freq_to_hours:
            raise ValueError(f"Unsupported frequency: {frequency}")

        hours_per_point = freq_to_hours[frequency]
        total_hours = days * 24
        num_signals = int(total_hours / hours_per_point)

        # Generate timestamps
        timestamps = [
            start_date + timedelta(hours=i * hours_per_point)
            for i in range(num_signals)
        ]

        # Generate price data (simple trend with noise)
        base_price = np.random.uniform(100, 300)
        trend = np.random.uniform(-0.001, 0.001)  # Daily trend
        noise = np.random.normal(0, 0.02, num_signals)

        prices = [base_price]
        for i in range(1, num_signals):
            new_price = prices[-1] * (1 + trend * hours_per_point + noise[i])
            new_price = max(new_price, base_price * 0.5)  # Prevent negative prices
            prices.append(new_price)

        # Generate signals based on strategy
        signals = []
        for i, (timestamp, price) in enumerate(zip(timestamps, prices)):
            signal, confidence = self._generate_strategy_signal(
                prices[: i + 1], strategy, i
            )

            signals.append(
                {
                    "timestamp": timestamp,
                    "symbol": symbol,
                    "signal": signal,
                    "confidence": confidence,
                    "price": round(price, 2),
                    "strategy": strategy,
                    "indicators": self._calculate_indicators(prices[: i + 1], strategy),
                }
            )

        return pd.DataFrame(signals)

    def _generate_strategy_signal(
        self, prices: List[float], strategy: str, current_index: int
    ) -> Tuple[str, float]:
        """Generate signal based on specific strategy."""
        if len(prices) < 20:
            return "HOLD", 0.5

        if strategy == "RSI":
            rsi = self._calculate_rsi(prices)
            if rsi < 30:
                return "BUY", min(0.9, (30 - rsi) / 30)
            elif rsi > 70:
                return "SELL", min(0.9, (rsi - 70) / 30)
            else:
                return "HOLD", 0.5

        elif strategy == "MACD":
            macd_signal = self._calculate_macd_signal(prices)
            if macd_signal > 0.1:
                return "BUY", min(0.9, macd_signal)
            elif macd_signal < -0.1:
                return "SELL", min(0.9, abs(macd_signal))
            else:
                return "HOLD", 0.5

        elif strategy == "BollingerBands":
            bb_signal = self._calculate_bollinger_signal(prices)
            return bb_signal

        elif strategy == "Momentum":
            momentum = self._calculate_momentum(prices)
            if momentum > 0.02:
                return "BUY", min(0.9, momentum / 0.05)
            elif momentum < -0.02:
                return "SELL", min(0.9, abs(momentum) / 0.05)
            else:
                return "HOLD", 0.5

        elif strategy == "MeanReversion":
            mean_rev_signal = self._calculate_mean_reversion_signal(prices)
            return mean_rev_signal

        else:  # Default or TrendFollowing
            trend = self._calculate_trend(prices)
            if trend > 0.01:
                return "BUY", min(0.9, trend / 0.02)
            elif trend < -0.01:
                return "SELL", min(0.9, abs(trend) / 0.02)
            else:
                return "HOLD", 0.5

    def _calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate RSI indicator."""
        if len(prices) < period + 1:
            return 50.0

        price_changes = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
        gains = [max(0, change) for change in price_changes[-period:]]
        losses = [max(0, -change) for change in price_changes[-period:]]

        avg_gain = np.mean(gains)
        avg_loss = np.mean(losses)

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _calculate_macd_signal(self, prices: List[float]) -> float:
        """Calculate MACD signal."""
        if len(prices) < 26:
            return 0.0

        # Calculate EMAs
        ema_12 = self._calculate_ema(prices, 12)
        ema_26 = self._calculate_ema(prices, 26)
        ema_signal = self._calculate_ema([ema_12 - ema_26], 9)

        macd_line = ema_12 - ema_26
        signal_line = ema_signal

        return macd_line - signal_line

    def _calculate_ema(self, prices: List[float], period: int) -> float:
        """Calculate Exponential Moving Average."""
        if len(prices) < period:
            return np.mean(prices)

        multiplier = 2 / (period + 1)
        ema = prices[0]

        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))

        return ema

    def _calculate_bollinger_signal(self, prices: List[float]) -> Tuple[str, float]:
        """Calculate Bollinger Bands signal."""
        if len(prices) < 20:
            return "HOLD", 0.5

        recent_prices = prices[-20:]
        sma = np.mean(recent_prices)
        std = np.std(recent_prices)

        upper_band = sma + (2 * std)
        lower_band = sma - (2 * std)
        current_price = prices[-1]

        if current_price < lower_band:
            return "BUY", min(0.9, (lower_band - current_price) / (2 * std))
        elif current_price > upper_band:
            return "SELL", min(0.9, (current_price - upper_band) / (2 * std))
        else:
            return "HOLD", 0.5

    def _calculate_momentum(self, prices: List[float], period: int = 10) -> float:
        """Calculate momentum indicator."""
        if len(prices) < period + 1:
            return 0.0

        current_price = prices[-1]
        past_price = prices[-(period + 1)]

        return (current_price - past_price) / past_price

    def _calculate_mean_reversion_signal(
        self, prices: List[float]
    ) -> Tuple[str, float]:
        """Calculate mean reversion signal."""
        if len(prices) < 50:
            return "HOLD", 0.5

        recent_prices = prices[-50:]
        mean_price = np.mean(recent_prices)
        std_price = np.std(recent_prices)

        current_price = prices[-1]
        z_score = (current_price - mean_price) / std_price

        if z_score < -2:  # Significantly below mean
            return "BUY", min(0.9, abs(z_score) / 3)
        elif z_score > 2:  # Significantly above mean
            return "SELL", min(0.9, abs(z_score) / 3)
        else:
            return "HOLD", 0.5

    def _calculate_trend(self, prices: List[float], period: int = 20) -> float:
        """Calculate trend indicator."""
        if len(prices) < period + 1:
            return 0.0

        # Simple linear regression slope
        x = np.arange(len(prices[-period:]))
        y = np.array(prices[-period:])

        slope = np.polyfit(x, y, 1)[0]
        current_price = prices[-1]

        return slope / current_price  # Normalized slope

    def _calculate_indicators(
        self, prices: List[float], strategy: str
    ) -> Dict[str, float]:
        """Calculate relevant indicators for a strategy."""
        indicators = {}

        if len(prices) < 2:
            return indicators

        if strategy in ["RSI", "MACD", "BollingerBands"]:
            indicators["rsi"] = self._calculate_rsi(prices)

        if strategy in ["MACD", "TrendFollowing"]:
            indicators["macd"] = self._calculate_macd_signal(prices)

        if strategy in ["BollingerBands", "MeanReversion"]:
            if len(prices) >= 20:
                recent_prices = prices[-20:]
                indicators["sma_20"] = np.mean(recent_prices)
                indicators["upper_bb"] = indicators["sma_20"] + (
                    2 * np.std(recent_prices)
                )
                indicators["lower_bb"] = indicators["sma_20"] - (
                    2 * np.std(recent_prices)
                )

        if strategy in ["Momentum", "TrendFollowing"]:
            indicators["momentum_10"] = self._calculate_momentum(prices, 10)
            indicators["momentum_5"] = self._calculate_momentum(prices, 5)

        return indicators

    def generate_correlated_signals(
        self,
        symbols: List[str],
        base_signals: List[Dict[str, Any]],
        correlation_factor: float = 0.7,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Generate correlated signals across multiple symbols."""
        correlated_signals = {symbol: [] for symbol in symbols}

        for base_signal in base_signals:
            base_symbol = base_signal["symbol"]
            base_type = base_signal["signal"]
            base_confidence = base_signal["confidence"]

            for symbol in symbols:
                if symbol == base_symbol:
                    # Keep original signal for base symbol
                    correlated_signals[symbol].append(base_signal)
                else:
                    # Generate correlated signal
                    if self.random.random() < correlation_factor:
                        # Correlated: same signal type with adjusted confidence
                        correlated_type = base_type
                        confidence_adjustment = self.random.uniform(-0.2, 0.2)
                        correlated_confidence = max(
                            0.1, min(0.95, base_confidence + confidence_adjustment)
                        )
                    else:
                        # Uncorrelated: random signal
                        correlated_type = self.random.choice(["BUY", "SELL", "HOLD"])
                        correlated_confidence = self.random.uniform(0.5, 0.9)

                    correlated_signal = base_signal.copy()
                    correlated_signal["symbol"] = symbol
                    correlated_signal["signal"] = correlated_type
                    correlated_signal["confidence"] = round(correlated_confidence, 3)
                    correlated_signal["signal_id"] = (
                        f"signal_{self.random.randint(0, 999999):06d}"
                    )
                    correlated_signal["correlated_to"] = base_signal["signal_id"]

                    correlated_signals[symbol].append(correlated_signal)

        return correlated_signals

    def generate_portfolio_signals(
        self,
        portfolio_positions: Dict[str, float],
        market_conditions: str = "normal",
        risk_tolerance: str = "medium",
    ) -> List[Dict[str, Any]]:
        """Generate signals based on current portfolio positions."""
        signals = []

        # Define market condition parameters
        condition_params = {
            "bullish": {"buy_bias": 0.6, "sell_bias": 0.2, "hold_bias": 0.2},
            "bearish": {"buy_bias": 0.2, "sell_bias": 0.6, "hold_bias": 0.2},
            "sideways": {"buy_bias": 0.3, "sell_bias": 0.3, "hold_bias": 0.4},
            "volatile": {"buy_bias": 0.25, "sell_bias": 0.25, "hold_bias": 0.5},
            "normal": {"buy_bias": 0.33, "sell_bias": 0.33, "hold_bias": 0.34},
        }

        params = condition_params.get(market_conditions, condition_params["normal"])

        # Define risk tolerance adjustments
        risk_adjustments = {
            "low": {"confidence_multiplier": 1.2, "hold_probability": 0.5},
            "medium": {"confidence_multiplier": 1.0, "hold_probability": 0.3},
            "high": {"confidence_multiplier": 0.8, "hold_probability": 0.1},
        }

        risk_adj = risk_adjustments.get(risk_tolerance, risk_adjustments["medium"])

        for symbol, position_weight in portfolio_positions.items():
            # Adjust signal bias based on position size
            if position_weight > 0.4:  # Large position
                # More likely to get sell / hold signals to reduce risk
                adjusted_params = {
                    "buy_bias": params["buy_bias"] * 0.5,
                    "sell_bias": params["sell_bias"] * 1.5,
                    "hold_bias": params["hold_bias"] * 1.2,
                }
            elif position_weight < 0.05:  # Small or no position
                # More likely to get buy signals
                adjusted_params = {
                    "buy_bias": params["buy_bias"] * 1.5,
                    "sell_bias": params["sell_bias"] * 0.5,
                    "hold_bias": params["hold_bias"] * 0.8,
                }
            else:
                adjusted_params = params

            # Normalize biases
            total_bias = sum(adjusted_params.values())
            for key in adjusted_params:
                adjusted_params[key] /= total_bias

            # Generate signal based on adjusted probabilities
            rand = self.random.random()
            cumulative_prob = 0

            if rand < adjusted_params["buy_bias"]:
                signal_type = "BUY"
            elif rand < adjusted_params["buy_bias"] + adjusted_params["sell_bias"]:
                signal_type = "SELL"
            else:
                signal_type = "HOLD"

            # Adjust confidence based on risk tolerance
            base_confidence = self.random.uniform(0.6, 0.9)
            adjusted_confidence = min(
                0.95, base_confidence * risk_adj["confidence_multiplier"]
            )

            # Apply hold probability for risk - averse strategies
            if risk_adj["hold_probability"] > self.random.random():
                signal_type = "HOLD"
                adjusted_confidence *= 0.8

            signal = {
                "signal_id": f"portfolio_signal_{len(signals):06d}",
                "symbol": symbol,
                "signal": signal_type,
                "confidence": round(adjusted_confidence, 3),
                "timestamp": datetime.now().isoformat(),
                "strategy": "PortfolioOptimization",
                "position_weight": position_weight,
                "market_conditions": market_conditions,
                "risk_tolerance": risk_tolerance,
                "metadata": {"position_adjusted": True, "risk_adjusted": True},
            }

            signals.append(signal)

        return signals
