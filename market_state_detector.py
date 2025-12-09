#!/usr/bin/env python3
"""
Market State Detector
Detects market regimes and states for adaptive strategy selection
"""

import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import pickle
from pathlib import Path
import json
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix
import warnings
warnings.filterwarnings('ignore')

# Import our framework components
from comprehensive_strategy_framework import MarketState, StrategyType

logger = logging.getLogger(__name__)


@dataclass
class MarketStateFeatures:
    """Market state features for regime detection"""
    timestamp: datetime
    price_change_1d: float
    price_change_5d: float
    price_change_20d: float
    volatility_20d: float
    volume_ratio_20d: float
    rsi_14: float
    macd_signal: float
    bb_position: float
    ma_trend_20d: float
    vix_like_volatility: float
    momentum_10d: float
    mean_reversion_signal: float
    trend_strength: float
    volume_trend: float

    # Additional derived features
    price_velocity: float = 0.0
    price_acceleration: float = 0.0
    volatility_trend: float = 0.0
    volume_acceleration: float = 0.0


@dataclass
class MarketStateDetection:
    """Market state detection result"""
    timestamp: datetime
    current_state: MarketState
    confidence: float  # 0.0 to 1.0
    transition_probability: Dict[MarketState, float]
    state_duration: int  # days in current state
    feature_importance: Dict[str, float]
    market_indicators: Dict[str, float]
    recommendation: str
    risk_level: str  # low, medium, high


class MarketStateDetector:
    """Advanced market state detection system"""

    def __init__(self, model_path: str = "data/market_state_models"):
        self.model_path = model_path
        self.logger = logging.getLogger(__name__)

        # Ensure model directory exists
        Path(model_path).mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.scaler = StandardScaler()
        self.classifier = None
        self.state_history = []
        self.current_state = MarketState.TRANSITION
        self.state_start_date = None

        # Feature names
        self.feature_names = [
            'price_change_1d', 'price_change_5d', 'price_change_20d',
            'volatility_20d', 'volume_ratio_20d', 'rsi_14', 'macd_signal',
            'bb_position', 'ma_trend_20d', 'vix_like_volatility',
            'momentum_10d', 'mean_reversion_signal', 'trend_strength',
            'volume_trend', 'price_velocity', 'price_acceleration',
            'volatility_trend', 'volume_acceleration'
        ]

        # Initialize model
        self._initialize_model()

    def _initialize_model(self):
        """Initialize the market state classifier"""
        try:
            # Try to load existing model
            model_file = Path(self.model_path) / "market_state_classifier.pkl"
            scaler_file = Path(self.model_path) / "feature_scaler.pkl"

            if model_file.exists() and scaler_file.exists():
                self.classifier = pickle.load(open(model_file, 'rb'))
                self.scaler = pickle.load(open(scaler_file, 'rb'))
                self.logger.info("Loaded existing market state models")
            else:
                self.logger.info("No existing models found, will create new ones during training")

        except Exception as e:
            self.logger.error(f"Error loading models: {e}")
            self._create_new_models()

    def _create_new_models(self):
        """Create new classification models"""
        self.classifier = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )

    def extract_features(self, data: pd.DataFrame, window: int = 20) -> List[MarketStateFeatures]:
        """Extract market state features from price data"""
        features = []

        # Ensure data has required columns
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in required_cols:
            if col not in data.columns:
                raise ValueError(f"Missing required column: {col}")

        # Calculate technical indicators
        df = data.copy()

        # Price changes
        df['price_change_1d'] = df['close'].pct_change(1)
        df['price_change_5d'] = df['close'].pct_change(5)
        df['price_change_20d'] = df['close'].pct_change(20)

        # Volatility
        df['volatility_20d'] = df['close'].pct_change().rolling(window).std()

        # Volume indicators
        df['volume_sma_20d'] = df['volume'].rolling(window).mean()
        df['volume_ratio_20d'] = df['volume'] / df['volume_sma_20d']

        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi_14'] = 100 - (100 / (1 + rs))

        # MACD
        df['ema_12'] = df['close'].ewm(span=12).mean()
        df['ema_26'] = df['close'].ewm(span=26).mean()
        df['macd'] = df['ema_12'] - df['ema_26']
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']

        # Bollinger Bands
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        df['bb_std'] = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (df['bb_std'] * 2)
        df['bb_lower'] = df['bb_middle'] - (df['bb_std'] * 2)
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])

        # Moving average trend
        df['ma_20d'] = df['close'].rolling(window=20).mean()
        df['ma_trend_20d'] = (df['close'] / df['ma_20d'] - 1)

        # VIX-like volatility
        df['vix_like_volatility'] = df['volatility_20d'] * np.sqrt(252) * 100

        # Momentum
        df['momentum_10d'] = df['close'].pct_change(10)

        # Mean reversion signal (distance from moving average)
        df['mean_reversion_signal'] = (df['close'] - df['ma_20d']) / df['ma_20d']

        # Trend strength (based on moving average consistency)
        df['ma_5d'] = df['close'].rolling(window=5).mean()
        df['ma_10d'] = df['close'].rolling(window=10).mean()
        df['trend_strength'] = np.abs(df['ma_5d'] / df['ma_10d'] - 1)

        # Volume trend
        df['volume_ma_5d'] = df['volume'].rolling(window=5).mean()
        df['volume_trend'] = df['volume'] / df['volume_ma_5d']

        # Additional derived features
        df['price_velocity'] = df['price_change_1d'] - df['price_change_1d'].shift(1)
        df['price_acceleration'] = df['price_velocity'] - df['price_velocity'].shift(1)
        df['volatility_trend'] = df['volatility_20d'] - df['volatility_20d'].shift(5)
        df['volume_acceleration'] = df['volume_trend'] - df['volume_trend'].shift(1)

        # Create feature objects
        for i in range(window, len(df)):
            try:
                feature = MarketStateFeatures(
                    timestamp=df.index[i],
                    price_change_1d=df['price_change_1d'].iloc[i],
                    price_change_5d=df['price_change_5d'].iloc[i],
                    price_change_20d=df['price_change_20d'].iloc[i],
                    volatility_20d=df['volatility_20d'].iloc[i],
                    volume_ratio_20d=df['volume_ratio_20d'].iloc[i],
                    rsi_14=df['rsi_14'].iloc[i],
                    macd_signal=df['macd_histogram'].iloc[i],
                    bb_position=df['bb_position'].iloc[i],
                    ma_trend_20d=df['ma_trend_20d'].iloc[i],
                    vix_like_volatility=df['vix_like_volatility'].iloc[i],
                    momentum_10d=df['momentum_10d'].iloc[i],
                    mean_reversion_signal=df['mean_reversion_signal'].iloc[i],
                    trend_strength=df['trend_strength'].iloc[i],
                    volume_trend=df['volume_trend'].iloc[i],
                    price_velocity=df['price_velocity'].iloc[i],
                    price_acceleration=df['price_acceleration'].iloc[i],
                    volatility_trend=df['volatility_trend'].iloc[i],
                    volume_acceleration=df['volume_acceleration'].iloc[i]
                )
                features.append(feature)
            except Exception as e:
                self.logger.warning(f"Error creating features at index {i}: {e}")
                continue

        return features

    def label_training_data(self, features: List[MarketStateFeatures], data: pd.DataFrame) -> List[str]:
        """Create labels for training based on market conditions"""
        labels = []

        for i, feature in enumerate(features):
            # Get corresponding data point
            try:
                data_idx = data.index.get_loc(feature.timestamp)

                # Define state based on multiple conditions
                price_20d_change = feature.price_change_20d
                volatility = feature.volatility_20d
                trend = feature.ma_trend_20d
                rsi = feature.rsi_14

                # Bull market conditions
                if (price_20d_change > 0.05 and  # Upward trend
                    trend > 0.02 and
                    rsi > 50 and
                    volatility < 0.03):
                    labels.append(MarketState.BULL_MARKET.value)

                # Bear market conditions
                elif (price_20d_change < -0.05 and  # Downward trend
                      trend < -0.02 and
                      rsi < 50 and
                      volatility > 0.02):
                    labels.append(MarketState.BEAR_MARKET.value)

                # High volatility
                elif volatility > 0.04:
                    labels.append(MarketState.HIGH_VOLATILITY.value)

                # Low volatility
                elif volatility < 0.015:
                    labels.append(MarketState.LOW_VOLATILITY.value)

                # Sideways market
                elif abs(price_20d_change) < 0.02 and abs(trend) < 0.01:
                    labels.append(MarketState.SIDEWAYS.value)

                # Default to transition state
                else:
                    labels.append(MarketState.TRANSITION.value)

            except Exception as e:
                self.logger.warning(f"Error labeling data point {i}: {e}")
                labels.append(MarketState.TRANSITION.value)

        return labels

    def train_models(self, data: pd.DataFrame) -> bool:
        """Train market state detection models"""
        try:
            self.logger.info("Training market state detection models")

            # Extract features
            features = self.extract_features(data)

            if len(features) < 100:
                self.logger.error("Insufficient data for training (need at least 100 data points)")
                return False

            # Create labels
            labels = self.label_training_data(features, data)

            # Prepare training data
            X = []
            for feature in features:
                feature_vector = [
                    feature.price_change_1d, feature.price_change_5d, feature.price_change_20d,
                    feature.volatility_20d, feature.volume_ratio_20d, feature.rsi_14,
                    feature.macd_signal, feature.bb_position, feature.ma_trend_20d,
                    feature.vix_like_volatility, feature.momentum_10d, feature.mean_reversion_signal,
                    feature.trend_strength, feature.volume_trend, feature.price_velocity,
                    feature.price_acceleration, feature.volatility_trend, feature.volume_acceleration
                ]
                X.append(feature_vector)

            X = np.array(X)
            y = np.array(labels)

            # Handle missing values
            X = np.nan_to_num(X, nan=0.0, posinf=1e10, neginf=-1e10)

            # Scale features
            X_scaled = self.scaler.fit_transform(X)

            # Train classifier
            self.classifier.fit(X_scaled, y)

            # Save models
            model_file = Path(self.model_path) / "market_state_classifier.pkl"
            scaler_file = Path(self.model_path) / "feature_scaler.pkl"

            with open(model_file, 'wb') as f:
                pickle.dump(self.classifier, f)
            with open(scaler_file, 'wb') as f:
                pickle.dump(self.scaler, f)

            # Evaluate model
            train_accuracy = self.classifier.score(X_scaled, y)
            self.logger.info(f"Model training completed. Train accuracy: {train_accuracy:.3f}")

            # Get feature importance
            feature_importance = dict(zip(self.feature_names, self.classifier.feature_importances_))
            top_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:10]

            self.logger.info("Top 10 most important features:")
            for feature, importance in top_features:
                self.logger.info(f"  {feature}: {importance:.3f}")

            return True

        except Exception as e:
            self.logger.error(f"Error training models: {e}")
            return False

    def detect_market_state(self, data: pd.DataFrame, last_n_days: int = 1) -> List[MarketStateDetection]:
        """Detect current market state"""
        try:
            # Extract features for recent data
            features = self.extract_features(data)

            if len(features) == 0:
                self.logger.warning("No features extracted")
                return []

            # Get most recent features
            recent_features = features[-last_n_days:]

            results = []

            for feature in recent_features:
                # Prepare feature vector
                feature_vector = [
                    feature.price_change_1d, feature.price_change_5d, feature.price_change_20d,
                    feature.volatility_20d, feature.volume_ratio_20d, feature.rsi_14,
                    feature.macd_signal, feature.bb_position, feature.ma_trend_20d,
                    feature.vix_like_volatility, feature.momentum_10d, feature.mean_reversion_signal,
                    feature.trend_strength, feature.volume_trend, feature.price_velocity,
                    feature.price_acceleration, feature.volatility_trend, feature.volume_acceleration
                ]

                feature_vector = np.array(feature_vector).reshape(1, -1)
                feature_vector = np.nan_to_num(feature_vector, nan=0.0, posinf=1e10, neginf=-1e10)

                # Scale features
                feature_vector_scaled = self.scaler.transform(feature_vector)

                # Predict state
                prediction = self.classifier.predict(feature_vector_scaled)[0]
                probabilities = self.classifier.predict_proba(feature_vector_scaled)[0]

                # Get class probabilities
                class_probabilities = {}
                for i, class_name in enumerate(self.classifier.classes_):
                    class_probabilities[MarketState(class_name)] = probabilities[i]

                # Create detection result
                current_state = MarketState(prediction)
                confidence = max(probabilities)

                # Calculate state duration
                state_duration = 0
                if hasattr(self, '_last_state_date'):
                    if self.current_state == current_state:
                        state_duration = (feature.timestamp - self._last_state_date).days
                    else:
                        self._last_state_date = feature.timestamp

                self.current_state = current_state

                # Generate recommendation
                recommendation = self._generate_recommendation(current_state, feature, class_probabilities)

                # Determine risk level
                risk_level = self._assess_risk_level(current_state, feature, confidence)

                # Create detection result
                detection = MarketStateDetection(
                    timestamp=feature.timestamp,
                    current_state=current_state,
                    confidence=confidence,
                    transition_probability=class_probabilities,
                    state_duration=state_duration,
                    feature_importance=dict(zip(self.feature_names, self.classifier.feature_importances_)),
                    market_indicators={
                        'rsi': feature.rsi_14,
                        'volatility': feature.volatility_20d,
                        'trend': feature.ma_trend_20d,
                        'momentum': feature.momentum_10d,
                        'volume_ratio': feature.volume_ratio_20d
                    },
                    recommendation=recommendation,
                    risk_level=risk_level
                )

                results.append(detection)

            return results

        except Exception as e:
            self.logger.error(f"Error detecting market state: {e}")
            return []

    def _generate_recommendation(self, state: MarketState, features: MarketStateFeatures, probabilities: Dict[MarketState, float]) -> str:
        """Generate strategy recommendations based on market state"""
        recommendations = {
            MarketState.BULL_MARKET: "Focus on trend-following strategies. Consider momentum and breakout strategies. Reduce mean reversion exposure.",
            MarketState.BEAR_MARKET: "Emphasize defensive strategies. Consider short-selling, volatility strategies, and cash preservation.",
            MarketState.HIGH_VOLATILITY: "Prioritize volatility-based strategies. Use wider stops, smaller position sizes. Consider options strategies.",
            MarketState.LOW_VOLATILITY: "Mean reversion strategies tend to perform well. Range-bound trading strategies may be effective.",
            MarketState.SIDEWAYS: "Range trading and mean reversion strategies are preferred. Avoid trend-following strategies.",
            MarketState.TRANSITION: "Wait for clearer market signals. Reduce position sizes and focus on capital preservation."
        }

        base_recommendation = recommendations.get(state, "Exercise caution and wait for clearer market signals.")

        # Add specific advice based on key indicators
        if features.rsi_14 > 80:
            base_recommendation += " RSI indicates overbought conditions - consider profit-taking."
        elif features.rsi_14 < 20:
            base_recommendation += " RSI indicates oversold conditions - look for buying opportunities."

        if features.volatility_20d > 0.04:
            base_recommendation += " High volatility detected - use wider risk management."

        return base_recommendation

    def _assess_risk_level(self, state: MarketState, features: MarketStateFeatures, confidence: float) -> str:
        """Assess overall market risk level"""
        risk_score = 0

        # State-based risk
        state_risk = {
            MarketState.BULL_MARKET: 0.3,
            MarketState.BEAR_MARKET: 0.7,
            MarketState.HIGH_VOLATILITY: 0.9,
            MarketState.LOW_VOLATILITY: 0.2,
            MarketState.SIDEWAYS: 0.4,
            MarketState.TRANSITION: 0.6
        }

        risk_score += state_risk.get(state, 0.5)

        # Volatility-based risk
        if features.volatility_20d > 0.05:
            risk_score += 0.3
        elif features.volatility_20d < 0.01:
            risk_score -= 0.1

        # Trend-based risk
        if abs(features.ma_trend_20d) > 0.1:
            risk_score += 0.2
        elif abs(features.ma_trend_20d) < 0.02:
            risk_score -= 0.1

        # Confidence-based risk
        if confidence < 0.6:
            risk_score += 0.2

        # RSI-based risk (extreme levels)
        if features.rsi_14 > 80 or features.rsi_14 < 20:
            risk_score += 0.1

        # Convert score to risk level
        if risk_score < 0.3:
            return "low"
        elif risk_score < 0.6:
            return "medium"
        else:
            return "high"

    def get_strategy_recommendations(self, market_state: MarketStateDetection) -> Dict[str, float]:
        """Get strategy recommendations based on market state"""
        recommendations = {
            # Trend following strategies
            StrategyType.TREND_FOLLOWING: 0.0,
            StrategyType.CBSC_SENTIMENT: 0.0,

            # Mean reversion strategies
            StrategyType.MEAN_REVERSION: 0.0,
            StrategyType.VOLATILITY: 0.0,
            StrategyType.VOLUME: 0.0,
            StrategyType.PRICE_ACTION: 0.0,
        }

        state = market_state.current_state
        confidence = market_state.confidence

        if state == MarketState.BULL_MARKET:
            recommendations[StrategyType.TREND_FOLLOWING] = 0.8 * confidence
            recommendations[StrategyType.MOMENTUM] = 0.7 * confidence

        elif state == MarketState.BEAR_MARKET:
            recommendations[StrategyType.TREND_FOLLOWING] = 0.6 * confidence  # Short strategies
            recommendations[StrategyType.VOLATILITY] = 0.8 * confidence
            recommendations[StrategyType.CBSC_SENTIMENT] = 0.7 * confidence

        elif state == MarketState.HIGH_VOLATILITY:
            recommendations[StrategyType.VOLATILITY] = 0.9 * confidence
            recommendations[StrategyType.OPTIONS] = 0.8 * confidence
            recommendations[StrategyType.RISK_MANAGEMENT] = 0.9 * confidence

        elif state == MarketState.LOW_VOLATILITY:
            recommendations[StrategyType.MEAN_REVERSION] = 0.8 * confidence
            recommendations[StrategyType.STATISTICAL_ARBITRAGE] = 0.7 * confidence

        elif state == MarketState.SIDEWAYS:
            recommendations[StrategyType.MEAN_REVERSION] = 0.8 * confidence
            recommendations[StrategyType.RANGE_TRADING] = 0.7 * confidence

        elif state == MarketState.TRANSITION:
            # Conservative approach during transitions
            recommendations[StrategyType.CASH] = 0.8 * confidence
            recommendations[StrategyType.WAIT_AND_SEE] = 0.7 * confidence

        return recommendations

    def save_detection_history(self, detections: List[MarketStateDetection], file_path: str):
        """Save detection history to file"""
        try:
            history_data = []
            for detection in detections:
                history_data.append({
                    'timestamp': detection.timestamp.isoformat(),
                    'current_state': detection.current_state.value,
                    'confidence': detection.confidence,
                    'transition_probability': {k.value: v for k, v in detection.transition_probability.items()},
                    'state_duration': detection.state_duration,
                    'recommendation': detection.recommendation,
                    'risk_level': detection.risk_level,
                    'market_indicators': detection.market_indicators
                })

            with open(file_path, 'w') as f:
                json.dump(history_data, f, indent=2)

            self.logger.info(f"Saved {len(detections)} detection records to {file_path}")

        except Exception as e:
            self.logger.error(f"Error saving detection history: {e}")

    def load_detection_history(self, file_path: str) -> List[MarketStateDetection]:
        """Load detection history from file"""
        try:
            with open(file_path, 'r') as f:
                history_data = json.load(f)

            detections = []
            for data in history_data:
                transition_prob = {MarketState(k): v for k, v in data['transition_probability'].items()}

                detection = MarketStateDetection(
                    timestamp=datetime.fromisoformat(data['timestamp']),
                    current_state=MarketState(data['current_state']),
                    confidence=data['confidence'],
                    transition_probability=transition_prob,
                    state_duration=data['state_duration'],
                    feature_importance={},  # Will be empty unless stored
                    market_indicators=data['market_indicators'],
                    recommendation=data['recommendation'],
                    risk_level=data['risk_level']
                )
                detections.append(detection)

            self.logger.info(f"Loaded {len(detections)} detection records from {file_path}")
            return detections

        except Exception as e:
            self.logger.error(f"Error loading detection history: {e}")
            return []


# Factory function
def create_market_state_detector(model_path: str = "data/market_state_models") -> MarketStateDetector:
    """Factory function to create market state detector"""
    return MarketStateDetector(model_path)


# Main execution for testing
if __name__ == "__main__":
    print("Market State Detector Test")
    print("=" * 40)

    # Generate test data
    np.random.seed(42)
    dates = pd.date_range('2022-01-01', '2024-12-31', freq='D')
    dates = dates[dates.weekday < 5]  # Weekdays only

    base_price = 100.0
    # Simulate different market regimes
    prices = []
    current_regime = 0
    regime_length = 0

    for i in range(len(dates)):
        # Change regime every 100 days
        if regime_length > 100:
            current_regime = (current_regime + 1) % 4
            regime_length = 0

        if current_regime == 0:  # Bull market
            trend = 0.0008
            volatility = 0.015
        elif current_regime == 1:  # Bear market
            trend = -0.0005
            volatility = 0.025
        elif current_regime == 2:  # High volatility
            trend = 0.0
            volatility = 0.04
        else:  # Sideways
            trend = 0.0001
            volatility = 0.01

        daily_return = trend + np.random.normal(0, volatility)
        if i == 0:
            prices.append(base_price)
        else:
            prices.append(prices[-1] * (1 + daily_return))

        regime_length += 1

    data = pd.DataFrame({
        'open': prices,
        'high': [p * 1.02 for p in prices],
        'low': [p * 0.98 for p in prices],
        'close': prices,
        'volume': np.random.randint(1000000, 5000000, len(dates))
    }, index=dates)

    print(f"Generated test data: {len(data)} records across 4 market regimes")

    # Create detector
    detector = create_market_state_detector()

    # Train models
    print("\nTraining market state models...")
    training_success = detector.train_models(data)

    if training_success:
        print("Training completed successfully!")

        # Test detection
        print("\nTesting market state detection...")
        detections = detector.detect_market_state(data, last_n_days=10)

        print(f"Detected {len(detections)} market states:")
        for detection in detections:
            print(f"  {detection.timestamp.strftime('%Y-%m-%d')}: {detection.current_state.value} "
                  f"(confidence: {detection.confidence:.2f}, risk: {detection.risk_level})")
            print(f"    Recommendation: {detection.recommendation[:80]}...")

        # Test strategy recommendations
        if detections:
            latest_detection = detections[-1]
            print(f"\nStrategy recommendations for {latest_detection.current_state.value}:")
            recommendations = detector.get_strategy_recommendations(latest_detection)

            for strategy_type, weight in recommendations.items():
                if weight > 0:
                    print(f"  {strategy_type.value}: {weight:.2f}")

        # Save detection history
        history_file = "market_state_detection_history.json"
        detector.save_detection_history(detections, history_file)
        print(f"\nSaved detection history to: {history_file}")

    else:
        print("Training failed!")

    print("\nMarket state detector test completed!")