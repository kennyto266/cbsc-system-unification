#!/usr / bin / env python3
"""
Multi - Indicator Signal Fusion Engine
Phase 4.2: Multi - Indicator Signal Fusion

Implements weighted signal combination, configurable fusion strategies,
regime - based indicator selection, and signal confidence scoring.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

from .enhanced_technical_indicators import (
    CrossIndicatorAnalyzer,
    IndicatorCategory,
    IndicatorSignal,
    VectorizedTechnicalIndicators,
)

logger = logging.getLogger(__name__)


class FusionStrategy(Enum):
    """Signal fusion strategies"""

    WEIGHTED_AVERAGE = "weighted_average"
    MAJORITY_VOTE = "majority_vote"
    ENSEMBLE = "ensemble"
    DYNAMIC_WEIGHTING = "dynamic_weighting"
    MACHINE_LEARNING = "machine_learning"


class MarketRegime(Enum):
    """Market regime types"""

    BULL_TRENDING = "bull_trending"
    BEAR_TRENDING = "bear_trending"
    SIDEWAYS = "sideways"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"


@dataclass
class SignalFusionConfig:
    """Configuration for signal fusion"""

    strategy: FusionStrategy = FusionStrategy.WEIGHTED_AVERAGE
    indicator_weights: Dict[str, float] = field(default_factory = dict)
    regime_weights: Dict[MarketRegime, Dict[str, float]] = field(default_factory = dict)
    confidence_threshold: float = 0.6
    rebalance_frequency: int = 20  # days
    lookback_window: int = 252  # days


@dataclass
class FusedSignal:
    """Fused signal from multiple indicators"""

    timestamp: datetime
    signal_value: float  # -1 to 1
    confidence: float  # 0 to 1
    contributing_indicators: List[str]
    market_regime: MarketRegime
    fusion_method: str
    metadata: Dict[str, Any] = field(default_factory = dict)


class RegimeDetector:
    """Market regime detection system"""

    def __init__(self, lookback_window: int = 60):
        """
        Initialize regime detector

        Args:
            lookback_window: Lookback window for regime detection
        """
        self.lookback_window = lookback_window
        self.regime_history = []

    def detect_regime(self, price_data: pd.DataFrame) -> MarketRegime:
        """
        Detect current market regime

        Args:
            price_data: Price data for regime detection

        Returns:
            Current market regime
        """
        returns = price_data["close"].pct_change()

        if len(returns) < self.lookback_window:
            return MarketRegime.SIDEWAYS

        # Calculate regime metrics
        recent_returns = returns.tail(self.lookback_window)
        mean_return = recent_returns.mean()
        volatility = recent_returns.std()
        trend_strength = abs(mean_return) / volatility if volatility > 0 else 0

        # Long - term trend
        long_term_ma = price_data["close"].rolling(50).mean()
        short_term_ma = price_data["close"].rolling(10).mean()

        if len(long_term_ma) > 0 and len(short_term_ma) > 0:
            current_price = price_data["close"].iloc[-1]
            ma_ratio = current_price / long_term_ma.iloc[-1]

            # Determine regime
            if ma_ratio > 1.05 and trend_strength > 0.5:
                return MarketRegime.BULL_TRENDING
            elif ma_ratio < 0.95 and trend_strength > 0.5:
                return MarketRegime.BEAR_TRENDING
            elif volatility > returns.std() * 1.5:
                return MarketRegime.HIGH_VOLATILITY
            elif volatility < returns.std() * 0.7:
                return MarketRegime.LOW_VOLATILITY
            else:
                return MarketRegime.SIDEWAYS

        return MarketRegime.SIDEWAYS

    def get_regime_transition_history(
        self, price_data: pd.DataFrame
    ) -> List[Tuple[datetime, MarketRegime]]:
        """Get history of regime transitions"""
        regime_history = []
        current_regime = None

        for date in price_data.index:
            window_data = price_data.loc[:date]
            if len(window_data) >= self.lookback_window:
                new_regime = self.detect_regime(window_data)

                if current_regime != new_regime:
                    regime_history.append((date, new_regime))
                    current_regime = new_regime

        return regime_history


class WeightedSignalFusion:
    """Weighted signal combination system"""

    def __init__(self, config: SignalFusionConfig):
        """
        Initialize weighted signal fusion

        Args:
            config: Signal fusion configuration
        """
        self.config = config
        self.indicator_weights = config.indicator_weights or self._get_default_weights()
        self.fusion_history = []

    def fuse_signals(
        self, indicator_signals: Dict[str, IndicatorSignal], market_regime: MarketRegime
    ) -> FusedSignal:
        """
        Fuse multiple indicator signals

        Args:
            indicator_signals: Dictionary of indicator signals
            market_regime: Current market regime

        Returns:
            Fused signal
        """
        if self.config.strategy == FusionStrategy.WEIGHTED_AVERAGE:
            return self._weighted_average_fusion(indicator_signals, market_regime)
        elif self.config.strategy == FusionStrategy.MAJORITY_VOTE:
            return self._majority_vote_fusion(indicator_signals, market_regime)
        elif self.config.strategy == FusionStrategy.DYNAMIC_WEIGHTING:
            return self._dynamic_weighting_fusion(indicator_signals, market_regime)
        else:
            return self._weighted_average_fusion(indicator_signals, market_regime)

    def _weighted_average_fusion(
        self, indicator_signals: Dict[str, IndicatorSignal], market_regime: MarketRegime
    ) -> FusedSignal:
        """Weighted average signal fusion"""
        total_weight = 0
        weighted_signal = 0
        contributing_indicators = []
        confidences = []

        # Get regime - specific weights if available
        regime_weights = self.config.regime_weights.get(
            market_regime, self.indicator_weights
        )

        for indicator_name, signal in indicator_signals.items():
            weight = regime_weights.get(
                indicator_name, self.indicator_weights.get(indicator_name, 0.1)
            )

            if weight > 0 and signal.confidence > self.config.confidence_threshold:
                weighted_signal += signal.signal_value * weight * signal.confidence
                total_weight += weight * signal.confidence
                contributing_indicators.append(indicator_name)
                confidences.append(signal.confidence)

        # Calculate final signal and confidence
        final_signal = weighted_signal / total_weight if total_weight > 0 else 0
        final_confidence = np.mean(confidences) if confidences else 0

        return FusedSignal(
            timestamp = indicator_signals[list(indicator_signals.keys())[0]].timestamp,
            signal_value = final_signal,
            confidence = final_confidence,
            contributing_indicators = contributing_indicators,
            market_regime = market_regime,
            fusion_method="weighted_average",
            metadata={
                "total_weight": total_weight,
                "indicator_count": len(contributing_indicators),
            },
        )

    def _majority_vote_fusion(
        self, indicator_signals: Dict[str, IndicatorSignal], market_regime: MarketRegime
    ) -> FusedSignal:
        """Majority vote signal fusion"""
        buy_signals = []
        sell_signals = []
        neutral_signals = []
        confidences = []
        contributing_indicators = []

        for indicator_name, signal in indicator_signals.items():
            if signal.confidence > self.config.confidence_threshold:
                if signal.signal_value > 0.2:
                    buy_signals.append((indicator_name, signal.confidence))
                elif signal.signal_value < -0.2:
                    sell_signals.append((indicator_name, signal.confidence))
                else:
                    neutral_signals.append((indicator_name, signal.confidence))

                contributing_indicators.append(indicator_name)
                confidences.append(signal.confidence)

        # Determine majority signal
        total_votes = len(buy_signals) + len(sell_signals) + len(neutral_signals)

        if total_votes == 0:
            final_signal = 0
        elif len(buy_signals) > len(sell_signals):
            final_signal = min(len(buy_signals) / total_votes, 1.0)
        elif len(sell_signals) > len(buy_signals):
            final_signal = -min(len(sell_signals) / total_votes, 1.0)
        else:
            final_signal = 0

        final_confidence = np.mean(confidences) if confidences else 0

        return FusedSignal(
            timestamp = indicator_signals[list(indicator_signals.keys())[0]].timestamp,
            signal_value = final_signal,
            confidence = final_confidence,
            contributing_indicators = contributing_indicators,
            market_regime = market_regime,
            fusion_method="majority_vote",
            metadata={
                "buy_votes": len(buy_signals),
                "sell_votes": len(sell_signals),
                "neutral_votes": len(neutral_signals),
            },
        )

    def _dynamic_weighting_fusion(
        self, indicator_signals: Dict[str, IndicatorSignal], market_regime: MarketRegime
    ) -> FusedSignal:
        """Dynamic weighting based on recent performance"""
        # Calculate recent performance - based weights
        performance_weights = self._calculate_performance_weights(indicator_signals)

        # Combine with base weights
        combined_weights = {}
        for indicator_name in indicator_signals.keys():
            base_weight = self.indicator_weights.get(indicator_name, 0.1)
            perf_weight = performance_weights.get(indicator_name, 0.1)
            combined_weights[indicator_name] = (base_weight + perf_weight) / 2

        # Use combined weights for weighted average
        total_weight = 0
        weighted_signal = 0
        contributing_indicators = []
        confidences = []

        for indicator_name, signal in indicator_signals.items():
            weight = combined_weights.get(indicator_name, 0.1)

            if weight > 0 and signal.confidence > self.config.confidence_threshold:
                weighted_signal += signal.signal_value * weight * signal.confidence
                total_weight += weight * signal.confidence
                contributing_indicators.append(indicator_name)
                confidences.append(signal.confidence)

        final_signal = weighted_signal / total_weight if total_weight > 0 else 0
        final_confidence = np.mean(confidences) if confidences else 0

        return FusedSignal(
            timestamp = indicator_signals[list(indicator_signals.keys())[0]].timestamp,
            signal_value = final_signal,
            confidence = final_confidence,
            contributing_indicators = contributing_indicators,
            market_regime = market_regime,
            fusion_method="dynamic_weighting",
            metadata={
                "performance_weights": performance_weights,
                "combined_weights": combined_weights,
            },
        )

    def _calculate_performance_weights(
        self, indicator_signals: Dict[str, IndicatorSignal]
    ) -> Dict[str, float]:
        """Calculate performance - based weights"""
        # Simplified performance weighting based on signal strength and consistency
        performance_weights = {}

        for indicator_name, signal in indicator_signals.items():
            # Weight based on signal strength and confidence
            performance = abs(signal.signal_value) * signal.confidence
            performance_weights[indicator_name] = performance

        # Normalize weights
        total_performance = sum(performance_weights.values())
        if total_performance > 0:
            performance_weights = {
                k: v / total_performance for k, v in performance_weights.items()
            }

        return performance_weights

    def _get_default_weights(self) -> Dict[str, float]:
        """Get default indicator weights"""
        return {
            "rsi": 0.25,
            "macd": 0.25,
            "bollinger_bands": 0.20,
            "moving_average": 0.15,
            "stochastic": 0.10,
            "atr": 0.05,
        }


class RegimeBasedSignalFusion:
    """Regime - based indicator selection and fusion"""

    def __init__(self):
        """Initialize regime - based signal fusion"""
        self.regime_configs = self._initialize_regime_configs()
        self.regime_detector = RegimeDetector()

    def _initialize_regime_configs(self) -> Dict[MarketRegime, SignalFusionConfig]:
        """Initialize configurations for different market regimes"""
        return {
            MarketRegime.BULL_TRENDING: SignalFusionConfig(
                strategy = FusionStrategy.WEIGHTED_AVERAGE,
                indicator_weights={
                    "macd": 0.35,
                    "moving_average": 0.30,
                    "rsi": 0.20,
                    "stochastic": 0.15,
                },
                confidence_threshold = 0.5,
            ),
            MarketRegime.BEAR_TRENDING: SignalFusionConfig(
                strategy = FusionStrategy.MAJORITY_VOTE,
                indicator_weights={
                    "moving_average": 0.40,
                    "macd": 0.35,
                    "bollinger_bands": 0.25,
                },
                confidence_threshold = 0.7,
            ),
            MarketRegime.SIDEWAYS: SignalFusionConfig(
                strategy = FusionStrategy.WEIGHTED_AVERAGE,
                indicator_weights={
                    "rsi": 0.35,
                    "stochastic": 0.30,
                    "bollinger_bands": 0.35,
                },
                confidence_threshold = 0.6,
            ),
            MarketRegime.HIGH_VOLATILITY: SignalFusionConfig(
                strategy = FusionStrategy.DYNAMIC_WEIGHTING,
                indicator_weights={
                    "atr": 0.25,
                    "bollinger_bands": 0.30,
                    "stochastic": 0.25,
                    "rsi": 0.20,
                },
                confidence_threshold = 0.8,
            ),
            MarketRegime.LOW_VOLATILITY: SignalFusionConfig(
                strategy = FusionStrategy.WEIGHTED_AVERAGE,
                indicator_weights={"moving_average": 0.40, "rsi": 0.35, "macd": 0.25},
                confidence_threshold = 0.5,
            ),
        }

    def fuse_signals_by_regime(
        self, price_data: pd.DataFrame, indicator_signals: Dict[str, IndicatorSignal]
    ) -> FusedSignal:
        """
        Fuse signals based on current market regime

        Args:
            price_data: Price data for regime detection
            indicator_signals: Dictionary of indicator signals

        Returns:
            Regime - appropriate fused signal
        """
        # Detect current regime
        current_regime = self.regime_detector.detect_regime(price_data)

        # Get regime - specific configuration
        regime_config = self.regime_configs[current_regime]

        # Initialize weighted fusion with regime config
        fusion_engine = WeightedSignalFusion(regime_config)

        # Fuse signals
        fused_signal = fusion_engine.fuse_signals(indicator_signals, current_regime)

        return fused_signal


class MachineLearningSignalFusion:
    """Machine learning - based signal fusion"""

    def __init__(self, model_type: str = "random_forest"):
        """
        Initialize ML - based signal fusion

        Args:
            model_type: Type of ML model ('random_forest', 'gradient_boosting')
        """
        self.model_type = model_type
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        self.feature_columns = []

    def train_fusion_model(
        self, features: pd.DataFrame, targets: pd.Series, test_size: float = 0.2
    ) -> Dict[str, Any]:
        """
        Train machine learning fusion model

        Args:
            features: DataFrame with indicator features
            targets: Target signals
            test_size: Proportion of data for testing

        Returns:
            Training results
        """
        # Split data
        split_index = int(len(features) * (1 - test_size))
        X_train, X_test = features[:split_index], features[split_index:]
        y_train, y_test = targets[:split_index], targets[split_index:]

        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Initialize model
        if self.model_type == "random_forest":
            self.model = RandomForestClassifier(
                n_estimators = 100, max_depth = 10, random_state = 42
            )
        else:
            raise ValueError(f"Unsupported model type: {self.model_type}")

        # Train model
        self.model.fit(X_train_scaled, y_train)

        # Evaluate model
        train_score = self.model.score(X_train_scaled, y_train)
        test_score = self.model.score(X_test_scaled, y_test)

        # Feature importance
        feature_importance = dict(
            zip(features.columns, self.model.feature_importances_)
        )

        self.is_trained = True
        self.feature_columns = list(features.columns)

        return {
            "train_accuracy": train_score,
            "test_accuracy": test_score,
            "feature_importance": feature_importance,
            "feature_columns": self.feature_columns,
        }

    def predict_fused_signal(self, indicator_features: Dict[str, float]) -> FusedSignal:
        """
        Predict fused signal using trained model

        Args:
            indicator_features: Dictionary of indicator features

        Returns:
            ML - predicted fused signal
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")

        # Prepare features
        feature_vector = np.array(
            [indicator_features.get(col, 0) for col in self.feature_columns]
        ).reshape(1, -1)

        # Scale features
        scaled_features = self.scaler.transform(feature_vector)

        # Predict
        prediction = self.model.predict(scaled_features)[0]
        prediction_proba = self.model.predict_proba(scaled_features)[0]

        # Convert to signal value
        signal_value = prediction if prediction != 0 else 0
        confidence = np.max(prediction_proba)

        return FusedSignal(
            timestamp = datetime.now(),
            signal_value = float(signal_value),
            confidence = float(confidence),
            contributing_indicators = list(indicator_features.keys()),
            market_regime = MarketRegime.SIDEWAYS,  # Not regime - specific
            fusion_method="machine_learning",
            metadata={
                "model_type": self.model_type,
                "prediction_proba": prediction_proba.tolist(),
            },
        )


class SignalConfidenceScoring:
    """Signal confidence scoring and validation"""

    def __init__(self):
        """Initialize confidence scoring system"""
        self.historical_performance = {}

    def calculate_signal_confidence(
        self,
        signal_value: float,
        indicator_name: str,
        current_price: float,
        historical_signals: Optional[List[Dict]] = None,
    ) -> float:
        """
        Calculate confidence score for a signal

        Args:
            signal_value: Raw signal value
            indicator_name: Name of the indicator
            current_price: Current price
            historical_signals: Historical signal performance data

        Returns:
            Confidence score (0 - 1)
        """
        # Base confidence from signal strength
        signal_strength_confidence = min(abs(signal_value), 1.0)

        # Historical performance confidence
        if historical_signals:
            performance_confidence = self._calculate_performance_confidence(
                indicator_name, historical_signals
            )
        else:
            performance_confidence = 0.5

        # Market condition confidence
        market_confidence = self._calculate_market_confidence(
            indicator_name, signal_value
        )

        # Combined confidence
        combined_confidence = (
            0.4 * signal_strength_confidence
            + 0.4 * performance_confidence
            + 0.2 * market_confidence
        )

        return min(max(combined_confidence, 0), 1)

    def _calculate_performance_confidence(
        self, indicator_name: str, historical_signals: List[Dict]
    ) -> float:
        """Calculate confidence based on historical performance"""
        if not historical_signals:
            return 0.5

        # Calculate historical success rate
        successful_signals = sum(
            1 for s in historical_signals if s.get("success", False)
        )
        total_signals = len(historical_signals)

        success_rate = successful_signals / total_signals if total_signals > 0 else 0.5

        return success_rate

    def _calculate_market_confidence(
        self, indicator_name: str, signal_value: float
    ) -> float:
        """Calculate confidence based on market conditions"""
        # Simplified market confidence based on signal type
        if "rsi" in indicator_name.lower():
            # RSI signals are more reliable at extremes
            if abs(signal_value) > 0.8:
                return 0.8
            elif abs(signal_value) > 0.6:
                return 0.6
            else:
                return 0.4
        elif "macd" in indicator_name.lower():
            # MACD signals are generally reliable
            return 0.7
        elif "ma" in indicator_name.lower():
            # Moving average signals are trend - dependent
            return 0.6
        else:
            return 0.5


class SignalFusionEngine:
    """Main signal fusion engine"""

    def __init__(self, config: Optional[SignalFusionConfig] = None):
        """
        Initialize signal fusion engine

        Args:
            config: Optional fusion configuration
        """
        self.config = config or SignalFusionConfig()
        self.enhanced_indicators = VectorizedTechnicalIndicators()
        self.regime_detector = RegimeDetector()
        self.weighted_fusion = WeightedSignalFusion(self.config)
        self.regime_fusion = RegimeBasedSignalFusion()
        self.ml_fusion = MachineLearningSignalFusion()
        self.confidence_scorer = SignalConfidenceScoring()

        self.signal_history = []

    def generate_fused_signals(
        self, price_data: pd.DataFrame, indicators_to_use: Optional[List[str]] = None
    ) -> List[FusedSignal]:
        """
        Generate fused signals over time

        Args:
            price_data: Price data
            indicators_to_use: List of indicators to use (None for all)

        Returns:
            List of fused signals
        """
        # Calculate indicators
        indicators = self._calculate_indicators(price_data, indicators_to_use)

        # Generate individual signals
        individual_signals = self._generate_individual_signals(indicators)

        # Generate fused signals over time
        fused_signals = []

        for date in price_data.index:
            # Get signals for this date
            date_signals = {
                name: signal
                for name, signal in individual_signals.items()
                if signal.timestamp == date
            }

            if date_signals:
                # Detect market regime
                date_price_data = price_data.loc[:date]
                current_regime = self.regime_detector.detect_regime(date_price_data)

                # Fuse signals based on strategy
                if (
                    self.config.strategy == FusionStrategy.MACHINE_LEARNING
                    and self.ml_fusion.is_trained
                ):
                    # ML - based fusion
                    indicator_features = self._extract_features(
                        date_signals, indicators, date
                    )
                    fused_signal = self.ml_fusion.predict_fused_signal(
                        indicator_features
                    )
                elif self.config.strategy == FusionStrategy.DYNAMIC_WEIGHTING:
                    # Regime - based fusion
                    fused_signal = self.regime_fusion.fuse_signals_by_regime(
                        date_price_data, date_signals
                    )
                else:
                    # Weighted fusion
                    fused_signal = self.weighted_fusion.fuse_signals(
                        date_signals, current_regime
                    )

                fused_signals.append(fused_signal)

        self.signal_history.extend(fused_signals)
        return fused_signals

    def _calculate_indicators(
        self, price_data: pd.DataFrame, indicators_to_use: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Calculate technical indicators"""
        indicators_to_use = indicators_to_use or [
            "rsi",
            "macd",
            "bollinger_bands",
            "moving_average",
        ]

        indicators = {}

        if "rsi" in indicators_to_use:
            indicators["rsi"] = self.enhanced_indicators.calculate_rsi_vectorized(
                price_data
            )

        if "macd" in indicators_to_use:
            indicators["macd"] = self.enhanced_indicators.calculate_macd_vectorized(
                price_data
            )

        if "bollinger_bands" in indicators_to_use:
            indicators["bollinger_bands"] = (
                self.enhanced_indicators.calculate_bollinger_bands_vectorized(
                    price_data
                )
            )

        if "moving_average" in indicators_to_use:
            indicators["moving_average"] = (
                self.enhanced_indicators.calculate_moving_averages_vectorized(
                    price_data
                )
            )

        if "stochastic" in indicators_to_use:
            indicators["stochastic"] = (
                self.enhanced_indicators.calculate_stochastic_oscillator_vectorized(
                    price_data
                )
            )

        if "atr" in indicators_to_use:
            indicators["atr"] = self.enhanced_indicators.calculate_atr_vectorized(
                price_data
            )

        return indicators

    def _generate_individual_signals(
        self, indicators: Dict[str, Any]
    ) -> Dict[str, IndicatorSignal]:
        """Generate individual indicator signals"""
        signals = {}

        for indicator_type, indicator_data in indicators.items():
            if indicator_type == "rsi":
                for period, rsi_series in indicator_data.items():
                    signal = self._generate_rsi_signal(period, rsi_series)
                    signals[f"rsi_{period}"] = signal

            elif indicator_type == "macd":
                for params, macd_data in indicator_data.items():
                    signal = self._generate_macd_signal(params, macd_data)
                    signals[f"macd_{params}"] = signal

            elif indicator_type == "bollinger_bands":
                for params, bb_data in indicator_data.items():
                    signal = self._generate_bb_signal(params, bb_data)
                    signals[f"bb_{params}"] = signal

            elif indicator_type == "moving_average":
                for period, ma_series in indicator_data.items():
                    signal = self._generate_ma_signal(period, ma_series)
                    signals[f"ma_{period}"] = signal

        return signals

    def _generate_rsi_signal(
        self, period: int, rsi_series: pd.Series
    ) -> IndicatorSignal:
        """Generate RSI signal"""
        latest_rsi = rsi_series.iloc[-1]

        if latest_rsi > 70:
            signal_value = -1  # Sell signal
            signal_type = "sell"
        elif latest_rsi < 30:
            signal_value = 1  # Buy signal
            signal_type = "buy"
        else:
            signal_value = 0  # Neutral
            signal_type = "neutral"

        confidence = max(
            abs(latest_rsi - 50) / 50, 0.2
        )  # Higher confidence at extremes

        return IndicatorSignal(
            indicator_name = f"rsi_{period}",
            signal_type = signal_type,
            signal_value = signal_value,
            confidence = confidence,
            timestamp = rsi_series.index[-1],
            parameters={"period": period},
            signal_value = latest_rsi,
        )

    def _generate_macd_signal(
        self, params: str, macd_data: Dict[str, pd.Series]
    ) -> IndicatorSignal:
        """Generate MACD signal"""
        macd_data["macd"].iloc[-1]
        macd_data["signal"].iloc[-1]
        latest_histogram = macd_data["histogram"].iloc[-1]

        if latest_histogram > 0:
            signal_value = 1  # Buy signal
            signal_type = "buy"
        else:
            signal_value = -1  # Sell signal
            signal_type = "sell"

        confidence = min(
            abs(latest_histogram) / 0.01, 0.9
        )  # Confidence based on histogram strength

        return IndicatorSignal(
            indicator_name = f"macd_{params}",
            signal_type = signal_type,
            signal_value = signal_value,
            confidence = confidence,
            timestamp = macd_data["macd"].index[-1],
            parameters={"params": params},
            signal_value = latest_histogram,
        )

    def _generate_bb_signal(
        self, params: str, bb_data: Dict[str, pd.Series]
    ) -> IndicatorSignal:
        """Generate Bollinger Bands signal"""
        latest_price = bb_data["middle"].iloc[-1]  # Use middle as proxy for price
        bb_data["upper"].iloc[-1]
        bb_data["lower"].iloc[-1]
        latest_percent_b = bb_data.get(
            "percent_b", pd.Series([0.5], index=[bb_data["upper"].index[-1]])
        ).iloc[-1]

        if latest_percent_b > 0.8:
            signal_value = -1  # Sell signal
            signal_type = "sell"
        elif latest_percent_b < 0.2:
            signal_value = 1  # Buy signal
            signal_type = "buy"
        else:
            signal_value = 0  # Neutral
            signal_type = "neutral"

        confidence = max(abs(latest_percent_b - 0.5) * 2, 0.3)

        return IndicatorSignal(
            indicator_name = f"bb_{params}",
            signal_type = signal_type,
            signal_value = signal_value,
            confidence = confidence,
            timestamp = bb_data["upper"].index[-1],
            parameters={"params": params},
            signal_value = latest_percent_b,
        )

    def _generate_ma_signal(self, period: int, ma_series: pd.Series) -> IndicatorSignal:
        """Generate Moving Average signal"""
        # Simplified MA signal based on position relative to recent highs / lows
        recent_ma = ma_series.tail(20)
        latest_ma = ma_series.iloc[-1]

        if latest_ma > recent_ma.mean():
            signal_value = 1  # Buy signal
            signal_type = "buy"
        else:
            signal_value = -1  # Sell signal
            signal_type = "sell"

        confidence = min(abs(latest_ma - recent_ma.mean()) / recent_ma.std(), 0.8)

        return IndicatorSignal(
            indicator_name = f"ma_{period}",
            signal_type = signal_type,
            signal_value = signal_value,
            confidence = confidence,
            timestamp = ma_series.index[-1],
            parameters={"period": period},
            signal_value = latest_ma,
        )

    def _extract_features(
        self,
        signals: Dict[str, IndicatorSignal],
        indicators: Dict[str, Any],
        timestamp: datetime,
    ) -> Dict[str, float]:
        """Extract features for ML model"""
        features = {}

        for signal_name, signal in signals.items():
            features[f"{signal_name}_value"] = signal.signal_value
            features[f"{signal_name}_confidence"] = signal.confidence

        return features

    def get_fusion_performance_summary(self) -> Dict[str, Any]:
        """Get summary of fusion performance"""
        if not self.signal_history:
            return {"status": "No signals generated"}

        signals_df = pd.DataFrame(
            [
                {
                    "timestamp": s.timestamp,
                    "signal_value": s.signal_value,
                    "confidence": s.confidence,
                    "market_regime": s.market_regime.value,
                    "fusion_method": s.fusion_method,
                }
                for s in self.signal_history
            ]
        )

        summary = {
            "total_signals": len(self.signal_history),
            "average_confidence": signals_df["confidence"].mean(),
            "signal_distribution": {
                "buy": len(signals_df[signals_df["signal_value"] > 0.2]),
                "sell": len(signals_df[signals_df["signal_value"] < -0.2]),
                "neutral": len(
                    signals_df[
                        (signals_df["signal_value"] >= -0.2)
                        & (signals_df["signal_value"] <= 0.2)
                    ]
                ),
            },
            "regime_distribution": signals_df["market_regime"].value_counts().to_dict(),
            "fusion_methods_used": signals_df["fusion_method"].unique().tolist(),
        }

        return summary


# Example usage and testing functions


def test_signal_fusion_engine():
    """Test signal fusion engine functionality"""
    logger.info("Testing signal fusion engine...")

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

    # Initialize fusion engine
    config = SignalFusionConfig(
        strategy = FusionStrategy.WEIGHTED_AVERAGE, confidence_threshold = 0.5
    )
    fusion_engine = SignalFusionEngine(config)

    # Generate fused signals
    fused_signals = fusion_engine.generate_fused_signals(
        price_data, indicators_to_use=["rsi", "macd", "bollinger_bands"]
    )

    # Get performance summary
    summary = fusion_engine.get_fusion_performance_summary()

    logger.info(f"Signal fusion test completed:")
    logger.info(f"  Total fused signals: {summary['total_signals']}")
    logger.info(f"  Average confidence: {summary['average_confidence']:.3f}")
    logger.info(f"  Signal distribution: {summary['signal_distribution']}")
    logger.info(f"  Regime distribution: {summary['regime_distribution']}")

    return {"fused_signals": fused_signals, "performance_summary": summary}


if __name__ == "__main__":
    # Test signal fusion engine
    results = test_signal_fusion_engine()
