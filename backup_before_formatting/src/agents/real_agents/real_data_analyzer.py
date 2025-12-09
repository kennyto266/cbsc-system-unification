"""Real data analyzer for processing actual market data and generating insights."""

import asyncio
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from ...data_adapters.base_adapter import (
    DataQuality,
    DataValidationResult,
    RealMarketData,
)

# Avoid importing RealAgentConfig here to prevent circular imports


class SignalStrength(str, Enum):
    """Signal strength levels."""

    VERY_WEAK = "very_weak"
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    VERY_STRONG = "very_strong"


class TechnicalIndicator(BaseModel):
    """Technical indicator result."""

    name: str = Field(..., description="Indicator name")
    value: float = Field(..., description="Indicator value")
    signal: str = Field(..., description="Signal (buy / sell / hold)")
    strength: float = Field(..., ge=0.0, le=1.0, description="Signal strength")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence level")


class MarketRegime(BaseModel):
    """Market regime classification."""

    regime_type: str = Field(..., description="Market regime type")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Regime confidence")
    volatility_level: str = Field(..., description="Volatility level")
    trend_direction: str = Field(..., description="Trend direction")


class AnalysisResult(BaseModel):
    """Comprehensive analysis result."""

    timestamp: datetime = Field(
        default_factory=datetime.now, description="Analysis timestamp"
    )
    symbols_analyzed: List[str] = Field(..., description="List of analyzed symbols")

    # Technical analysis
    technical_indicators: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict, description="Technical indicators by symbol"
    )

    # Signal analysis
    signal_strength: float = Field(
        ..., ge=0.0, le=1.0, description="Overall signal strength"
    )
    signal_direction: str = Field(..., description="Overall signal direction")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Analysis confidence")

    # Market regime
    market_regime: MarketRegime = Field(..., description="Market regime classification")

    # Risk metrics
    risk_metrics: Dict[str, float] = Field(
        default_factory=dict, description="Risk metrics"
    )

    # Quality metrics
    data_quality: DataQuality = Field(..., description="Data quality assessment")
    analysis_quality: float = Field(
        ..., ge=0.0, le=1.0, description="Analysis quality score"
    )

    # Additional insights
    insights: List[str] = Field(default_factory=list, description="Key insights")
    warnings: List[str] = Field(default_factory=list, description="Analysis warnings")

    class Config:
        use_enum_values = True


class RealDataAnalyzer:
    """Analyzer for real market data with technical analysis and signal generation."""

    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(
            f"hk_quant_system.data_analyzer.{config.agent_id}"
        )
        self._initialized = False
        self._data_cache: Dict[str, List[RealMarketData]] = {}
        self._analysis_cache: Dict[str, AnalysisResult] = {}

    async def initialize(self) -> bool:
        """Initialize the data analyzer."""
        try:
            self.logger.info("Initializing real data analyzer...")

            # Initialize technical analysis components
            await self._initialize_technical_analysis()

            # Initialize market regime detection
            await self._initialize_regime_detection()

            self._initialized = True
            self.logger.info("Real data analyzer initialized successfully")
            return True

        except Exception as e:
            self.logger.exception(f"Failed to initialize data analyzer: {e}")
            return False

    async def _initialize_technical_analysis(self) -> None:
        """Initialize technical analysis components."""
        # This would typically load technical analysis libraries
        # For now, we'll use basic implementations
        pass

    async def _initialize_regime_detection(self) -> None:
        """Initialize market regime detection components."""
        # This would typically load regime detection models
        # For now, we'll use basic implementations
        pass

    async def analyze(self, market_data: List[RealMarketData]) -> AnalysisResult:
        """Analyze market data and generate comprehensive insights."""
        if not self._initialized:
            raise RuntimeError("Data analyzer not initialized")

        try:
            self.logger.debug(f"Analyzing {len(market_data)} market data points")

            # Group data by symbol
            symbol_data = self._group_data_by_symbol(market_data)

            # Perform technical analysis for each symbol
            technical_indicators = {}
            for symbol, data in symbol_data.items():
                indicators = await self._calculate_technical_indicators(symbol, data)
                technical_indicators[symbol] = indicators

            # Calculate overall signal strength
            signal_strength, signal_direction = await self._calculate_signal_strength(
                technical_indicators
            )

            # Determine market regime
            market_regime = await self._detect_market_regime(market_data)

            # Calculate risk metrics
            risk_metrics = await self._calculate_risk_metrics(market_data)

            # Assess data quality
            data_quality = await self._assess_data_quality(market_data)

            # Generate insights
            insights, warnings = await self._generate_insights(
                technical_indicators, market_regime, risk_metrics, data_quality
            )

            # Calculate analysis quality
            analysis_quality = await self._calculate_analysis_quality(
                technical_indicators, signal_strength, data_quality
            )

            # Calculate confidence
            confidence = await self._calculate_confidence(
                signal_strength, data_quality, analysis_quality
            )

            result = AnalysisResult(
                symbols_analyzed=list(symbol_data.keys()),
                technical_indicators=technical_indicators,
                signal_strength=signal_strength,
                signal_direction=signal_direction,
                confidence=confidence,
                market_regime=market_regime,
                risk_metrics=risk_metrics,
                data_quality=data_quality,
                analysis_quality=analysis_quality,
                insights=insights,
                warnings=warnings,
            )

            # Cache result
            cache_key = f"{datetime.now().strftime('%Y % m % d_ % H % M')}"
            self._analysis_cache[cache_key] = result

            self.logger.info(
                f"Analysis completed. Signal: {signal_direction} ({signal_strength:.3f}), Confidence: {confidence:.3f}"
            )
            return result

        except Exception as e:
            self.logger.exception(f"Error during analysis: {e}")
            raise

    def _group_data_by_symbol(
        self, market_data: List[RealMarketData]
    ) -> Dict[str, List[RealMarketData]]:
        """Group market data by symbol."""
        symbol_data = {}
        for data in market_data:
            if data.symbol not in symbol_data:
                symbol_data[data.symbol] = []
            symbol_data[data.symbol].append(data)

        # Sort each symbol's data by timestamp
        for symbol in symbol_data:
            symbol_data[symbol].sort(key=lambda x: x.timestamp)

        return symbol_data

    async def _calculate_technical_indicators(
        self, symbol: str, data: List[RealMarketData]
    ) -> Dict[str, Any]:
        """Calculate technical indicators for a symbol."""
        try:
            if len(data) < 2:
                return {}

            # Convert to DataFrame for easier calculation
            df = pd.DataFrame(
                [
                    {
                        "timestamp": d.timestamp,
                        "open": float(d.open_price),
                        "high": float(d.high_price),
                        "low": float(d.low_price),
                        "close": float(d.close_price),
                        "volume": d.volume,
                    }
                    for d in data
                ]
            )

            df.set_index("timestamp", inplace=True)
            df.sort_index(inplace=True)

            indicators = {}

            # Simple Moving Averages
            indicators["sma_20"] = (
                df["close"].rolling(window=20).mean().iloc[-1]
                if len(df) >= 20
                else df["close"].mean()
            )
            indicators["sma_50"] = (
                df["close"].rolling(window=50).mean().iloc[-1]
                if len(df) >= 50
                else df["close"].mean()
            )

            # RSI (Relative Strength Index)
            indicators["rsi"] = await self._calculate_rsi(df["close"])

            # MACD
            macd_line, signal_line, histogram = await self._calculate_macd(df["close"])
            indicators["macd"] = macd_line
            indicators["macd_signal"] = signal_line
            indicators["macd_histogram"] = histogram

            # Bollinger Bands
            bb_upper, bb_middle, bb_lower = await self._calculate_bollinger_bands(
                df["close"]
            )
            indicators["bb_upper"] = bb_upper
            indicators["bb_middle"] = bb_middle
            indicators["bb_lower"] = bb_lower

            # Volume indicators
            indicators["volume_sma"] = (
                df["volume"].rolling(window=20).mean().iloc[-1]
                if len(df) >= 20
                else df["volume"].mean()
            )
            indicators["volume_ratio"] = (
                df["volume"].iloc[-1] / indicators["volume_sma"]
                if indicators["volume_sma"] > 0
                else 1.0
            )

            # Price momentum
            indicators["momentum"] = (
                (df["close"].iloc[-1] - df["close"].iloc[-5]) / df["close"].iloc[-5]
                if len(df) >= 5
                else 0.0
            )

            # Volatility
            returns = df["close"].pct_change().dropna()
            indicators["volatility"] = (
                returns.std() * np.sqrt(252) if len(returns) > 1 else 0.0
            )

            return indicators

        except Exception as e:
            self.logger.error(
                f"Error calculating technical indicators for {symbol}: {e}"
            )
            return {}

    async def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Calculate RSI (Relative Strength Index)."""
        try:
            if len(prices) < period + 1:
                return 50.0  # Neutral RSI if insufficient data

            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))

            return float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50.0

        except Exception:
            return 50.0

    async def _calculate_macd(
        self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
    ) -> Tuple[float, float, float]:
        """Calculate MACD (Moving Average Convergence Divergence)."""
        try:
            if len(prices) < slow:
                return 0.0, 0.0, 0.0

            ema_fast = prices.ewm(span=fast).mean()
            ema_slow = prices.ewm(span=slow).mean()

            macd_line = ema_fast - ema_slow
            signal_line = macd_line.ewm(span=signal).mean()
            histogram = macd_line - signal_line

            return (
                float(macd_line.iloc[-1]) if not pd.isna(macd_line.iloc[-1]) else 0.0,
                (
                    float(signal_line.iloc[-1])
                    if not pd.isna(signal_line.iloc[-1])
                    else 0.0
                ),
                float(histogram.iloc[-1]) if not pd.isna(histogram.iloc[-1]) else 0.0,
            )

        except Exception:
            return 0.0, 0.0, 0.0

    async def _calculate_bollinger_bands(
        self, prices: pd.Series, period: int = 20, std_dev: float = 2.0
    ) -> Tuple[float, float, float]:
        """Calculate Bollinger Bands."""
        try:
            if len(prices) < period:
                current_price = float(prices.iloc[-1])
                return current_price, current_price, current_price

            sma = prices.rolling(window=period).mean()
            std = prices.rolling(window=period).std()

            upper_band = sma + (std * std_dev)
            middle_band = sma
            lower_band = sma - (std * std_dev)

            return (
                (
                    float(upper_band.iloc[-1])
                    if not pd.isna(upper_band.iloc[-1])
                    else float(prices.iloc[-1])
                ),
                (
                    float(middle_band.iloc[-1])
                    if not pd.isna(middle_band.iloc[-1])
                    else float(prices.iloc[-1])
                ),
                (
                    float(lower_band.iloc[-1])
                    if not pd.isna(lower_band.iloc[-1])
                    else float(prices.iloc[-1])
                ),
            )

        except Exception:
            current_price = float(prices.iloc[-1])
            return current_price, current_price, current_price

    async def _calculate_signal_strength(
        self, technical_indicators: Dict[str, Dict[str, Any]]
    ) -> Tuple[float, str]:
        """Calculate overall signal strength and direction."""
        try:
            if not technical_indicators:
                return 0.0, "neutral"

            buy_signals = 0
            sell_signals = 0
            total_strength = 0.0
            signal_count = 0

            for symbol, indicators in technical_indicators.items():
                # RSI signals
                rsi = indicators.get("rsi", 50)
                if rsi < 30:  # Oversold
                    buy_signals += 1
                    total_strength += (30 - rsi) / 30
                elif rsi > 70:  # Overbought
                    sell_signals += 1
                    total_strength += (rsi - 70) / 30

                # MACD signals
                macd = indicators.get("macd", 0)
                macd_signal = indicators.get("macd_signal", 0)
                if macd > macd_signal:
                    buy_signals += 1
                    total_strength += abs(macd - macd_signal) / max(abs(macd), 0.001)
                else:
                    sell_signals += 1
                    total_strength += abs(macd - macd_signal) / max(abs(macd), 0.001)

                # Bollinger Bands signals
                close_price = indicators.get("close_price", 0)
                bb_upper = indicators.get("bb_upper", close_price)
                bb_lower = indicators.get("bb_lower", close_price)
                if close_price <= bb_lower:
                    buy_signals += 1
                    total_strength += 0.5
                elif close_price >= bb_upper:
                    sell_signals += 1
                    total_strength += 0.5

                signal_count += 3  # RSI, MACD, BB

            if signal_count == 0:
                return 0.0, "neutral"

            avg_strength = total_strength / signal_count
            normalized_strength = min(avg_strength, 1.0)

            # Determine direction
            if buy_signals > sell_signals:
                direction = "buy"
            elif sell_signals > buy_signals:
                direction = "sell"
            else:
                direction = "neutral"

            return normalized_strength, direction

        except Exception as e:
            self.logger.error(f"Error calculating signal strength: {e}")
            return 0.0, "neutral"

    async def _detect_market_regime(
        self, market_data: List[RealMarketData]
    ) -> MarketRegime:
        """Detect current market regime."""
        try:
            if len(market_data) < 20:
                return MarketRegime(
                    regime_type="unknown",
                    confidence=0.0,
                    volatility_level="unknown",
                    trend_direction="unknown",
                )

            # Calculate volatility
            prices = [float(d.close_price) for d in market_data[-20:]]
            returns = [prices[i] / prices[i - 1] - 1 for i in range(1, len(prices))]
            volatility = np.std(returns) * np.sqrt(252)

            # Determine volatility level
            if volatility < 0.15:
                volatility_level = "low"
            elif volatility < 0.25:
                volatility_level = "medium"
            else:
                volatility_level = "high"

            # Determine trend direction
            sma_short = np.mean(prices[-5:])
            sma_long = np.mean(prices[-20:])

            if sma_short > sma_long * 1.02:
                trend_direction = "bullish"
            elif sma_short < sma_long * 0.98:
                trend_direction = "bearish"
            else:
                trend_direction = "sideways"

            # Determine regime type
            if volatility_level == "low" and trend_direction == "bullish":
                regime_type = "bull_market"
                confidence = 0.8
            elif volatility_level == "low" and trend_direction == "bearish":
                regime_type = "bear_market"
                confidence = 0.8
            elif volatility_level == "high":
                regime_type = "volatile"
                confidence = 0.7
            else:
                regime_type = "consolidation"
                confidence = 0.6

            return MarketRegime(
                regime_type=regime_type,
                confidence=confidence,
                volatility_level=volatility_level,
                trend_direction=trend_direction,
            )

        except Exception as e:
            self.logger.error(f"Error detecting market regime: {e}")
            return MarketRegime(
                regime_type="unknown",
                confidence=0.0,
                volatility_level="unknown",
                trend_direction="unknown",
            )

    async def _calculate_risk_metrics(
        self, market_data: List[RealMarketData]
    ) -> Dict[str, float]:
        """Calculate risk metrics."""
        try:
            if len(market_data) < 2:
                return {}

            prices = [float(d.close_price) for d in market_data]
            returns = [prices[i] / prices[i - 1] - 1 for i in range(1, len(prices))]

            risk_metrics = {
                "volatility": np.std(returns) * np.sqrt(252),
                "max_drawdown": await self._calculate_max_drawdown(prices),
                "sharpe_ratio": (
                    np.mean(returns) / np.std(returns) * np.sqrt(252)
                    if np.std(returns) > 0
                    else 0
                ),
                "var_95": np.percentile(returns, 5),
                "var_99": np.percentile(returns, 1),
            }

            return risk_metrics

        except Exception as e:
            self.logger.error(f"Error calculating risk metrics: {e}")
            return {}

    async def _calculate_max_drawdown(self, prices: List[float]) -> float:
        """Calculate maximum drawdown."""
        try:
            peak = prices[0]
            max_dd = 0.0

            for price in prices:
                if price > peak:
                    peak = price
                drawdown = (peak - price) / peak
                if drawdown > max_dd:
                    max_dd = drawdown

            return max_dd

        except Exception:
            return 0.0

    async def _assess_data_quality(
        self, market_data: List[RealMarketData]
    ) -> DataQuality:
        """Assess data quality."""
        try:
            if not market_data:
                return DataQuality.POOR

            total_records = len(market_data)
            valid_records = 0

            for data in market_data:
                # Check for missing values
                if (
                    data.open_price
                    and data.high_price
                    and data.low_price
                    and data.close_price
                    and data.volume >= 0
                ):
                    valid_records += 1

            quality_ratio = valid_records / total_records

            if quality_ratio >= 0.95:
                return DataQuality.EXCELLENT
            elif quality_ratio >= 0.8:
                return DataQuality.GOOD
            elif quality_ratio >= 0.6:
                return DataQuality.FAIR
            else:
                return DataQuality.POOR

        except Exception:
            return DataQuality.UNKNOWN

    async def _generate_insights(
        self,
        technical_indicators: Dict[str, Dict[str, Any]],
        market_regime: MarketRegime,
        risk_metrics: Dict[str, float],
        data_quality: DataQuality,
    ) -> Tuple[List[str], List[str]]:
        """Generate insights and warnings."""
        insights = []
        warnings = []

        # Market regime insights
        insights.append(
            f"Market regime: {market_regime.regime_type} ({market_regime.confidence:.1%} confidence)"
        )

        # Volatility insights
        volatility = risk_metrics.get("volatility", 0)
        if volatility > 0.3:
            warnings.append(f"High volatility detected: {volatility:.1%}")
        elif volatility < 0.1:
            insights.append(f"Low volatility environment: {volatility:.1%}")

        # Technical indicator insights
        for symbol, indicators in technical_indicators.items():
            rsi = indicators.get("rsi", 50)
            if rsi < 30:
                insights.append(f"{symbol}: Oversold conditions (RSI: {rsi:.1f})")
            elif rsi > 70:
                insights.append(f"{symbol}: Overbought conditions (RSI: {rsi:.1f})")

            volume_ratio = indicators.get("volume_ratio", 1)
            if volume_ratio > 2:
                insights.append(
                    f"{symbol}: High volume activity ({volume_ratio:.1f}x average)"
                )

        # Data quality warnings
        if data_quality in [DataQuality.POOR, DataQuality.UNKNOWN]:
            warnings.append(f"Data quality concerns: {data_quality.value}")

        return insights, warnings

    async def _calculate_analysis_quality(
        self,
        technical_indicators: Dict[str, Dict[str, Any]],
        signal_strength: float,
        data_quality: DataQuality,
    ) -> float:
        """Calculate analysis quality score."""
        try:
            # Base quality from data quality
            quality_score = {
                DataQuality.EXCELLENT: 1.0,
                DataQuality.GOOD: 0.8,
                DataQuality.FAIR: 0.6,
                DataQuality.POOR: 0.3,
                DataQuality.UNKNOWN: 0.1,
            }.get(data_quality, 0.1)

            # Adjust based on signal strength
            if signal_strength > 0.7:
                quality_score *= 1.1
            elif signal_strength < 0.3:
                quality_score *= 0.9

            # Adjust based on number of indicators
            if len(technical_indicators) > 0:
                avg_indicators = sum(
                    len(indicators) for indicators in technical_indicators.values()
                ) / len(technical_indicators)
                if avg_indicators >= 8:
                    quality_score *= 1.05
                elif avg_indicators < 4:
                    quality_score *= 0.95

            return min(quality_score, 1.0)

        except Exception:
            return 0.5

    async def _calculate_confidence(
        self, signal_strength: float, data_quality: DataQuality, analysis_quality: float
    ) -> float:
        """Calculate overall confidence score."""
        try:
            # Base confidence from signal strength
            confidence = signal_strength

            # Adjust based on data quality
            quality_multiplier = {
                DataQuality.EXCELLENT: 1.0,
                DataQuality.GOOD: 0.9,
                DataQuality.FAIR: 0.7,
                DataQuality.POOR: 0.5,
                DataQuality.UNKNOWN: 0.3,
            }.get(data_quality, 0.3)

            confidence *= quality_multiplier

            # Adjust based on analysis quality
            confidence *= analysis_quality

            return min(confidence, 1.0)

        except Exception:
            return 0.5

    async def cleanup(self) -> None:
        """Cleanup analyzer resources."""
        self._data_cache.clear()
        self._analysis_cache.clear()
        self._initialized = False
        self.logger.info("Real data analyzer cleanup completed")
