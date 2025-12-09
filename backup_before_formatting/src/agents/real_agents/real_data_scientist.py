"""Real Data Scientist Agent for Hong Kong quantitative trading system.

This agent performs advanced machine learning, feature engineering,
and anomaly detection based on real market data.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field
from sklearn.ensemble import IsolationForest, RandomForestRegressor
from sklearn.metrics import classification_report, mean_squared_error, r2_score
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.preprocessing import RobustScaler, StandardScaler

from ...data_adapters.base_adapter import RealMarketData
from .base_real_agent import BaseRealAgent, RealAgentConfig, RealAgentStatus
from .ml_integration import MLModelManager, ModelPerformance, ModelType
from .real_data_analyzer import AnalysisResult, SignalStrength


class ModelStatus(str, Enum):
    """Model training status."""

    PENDING = "pending"
    TRAINING = "training"
    TRAINED = "trained"
    EVALUATING = "evaluating"
    DEPLOYED = "deployed"
    FAILED = "failed"


class FeatureType(str, Enum):
    """Feature types for machine learning."""

    TECHNICAL = "technical"
    FUNDAMENTAL = "fundamental"
    MARKET_MICROSTRUCTURE = "market_microstructure"
    MACROECONOMIC = "macroeconomic"
    SENTIMENT = "sentiment"
    DERIVED = "derived"


class AnomalyType(str, Enum):
    """Types of anomalies."""

    PRICE_SPIKE = "price_spike"
    VOLUME_ANOMALY = "volume_anomaly"
    CORRELATION_BREAK = "correlation_break"
    VOLATILITY_CLUSTER = "volatility_cluster"
    PATTERN_DEVIATION = "pattern_deviation"


class Feature(BaseModel):
    """Feature model for machine learning."""

    feature_name: str = Field(..., description="Feature name")
    feature_type: FeatureType = Field(..., description="Feature type")
    description: str = Field(..., description="Feature description")
    calculation_method: str = Field(..., description="Calculation method")
    importance_score: float = Field(
        0.0, ge=0.0, le=1.0, description="Feature importance"
    )
    correlation_with_target: float = Field(
        0.0, ge=-1.0, le=1.0, description="Correlation with target"
    )
    last_updated: datetime = Field(
        default_factory=datetime.now, description="Last update time"
    )

    class Config:
        use_enum_values = True


class MLModel(BaseModel):
    """Machine learning model."""

    model_id: str = Field(..., description="Model identifier")
    model_name: str = Field(..., description="Model name")
    model_type: ModelType = Field(..., description="Model type")
    target_variable: str = Field(..., description="Target variable")

    # Model status
    status: ModelStatus = Field(ModelStatus.PENDING, description="Model status")
    training_data_size: int = Field(0, description="Training data size")
    validation_score: float = Field(0.0, description="Validation score")
    test_score: float = Field(0.0, description="Test score")

    # Performance metrics
    rmse: float = Field(0.0, description="Root Mean Square Error")
    mae: float = Field(0.0, description="Mean Absolute Error")
    r2: float = Field(0.0, description="R - squared")
    feature_importance: Dict[str, float] = Field(
        default_factory=dict, description="Feature importance"
    )

    # Model metadata
    created_at: datetime = Field(
        default_factory=datetime.now, description="Creation time"
    )
    last_trained: Optional[datetime] = Field(None, description="Last training time")
    last_prediction: Optional[datetime] = Field(
        None, description="Last prediction time"
    )
    deployment_status: bool = Field(False, description="Deployment status")

    class Config:
        use_enum_values = True


class AnomalyDetection(BaseModel):
    """Anomaly detection result."""

    anomaly_id: str = Field(..., description="Anomaly identifier")
    anomaly_type: AnomalyType = Field(..., description="Anomaly type")
    symbol: str = Field(..., description="Related symbol")

    # Anomaly details
    severity: float = Field(..., ge=0.0, le=1.0, description="Anomaly severity")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence")
    description: str = Field(..., description="Anomaly description")

    # Context
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Detection time"
    )
    context_data: Dict[str, Any] = Field(
        default_factory=dict, description="Contextual data"
    )

    # Impact assessment
    potential_impact: str = Field("unknown", description="Potential market impact")
    recommended_action: str = Field("monitor", description="Recommended action")

    class Config:
        use_enum_values = True


class FeatureEngineering(BaseModel):
    """Feature engineering configuration."""

    feature_set_id: str = Field(..., description="Feature set identifier")
    feature_set_name: str = Field(..., description="Feature set name")

    # Feature configuration
    features: List[Feature] = Field(default_factory=list, description="Feature list")
    preprocessing_steps: List[str] = Field(
        default_factory=list, description="Preprocessing steps"
    )
    feature_selection_method: str = Field(
        "correlation", description="Feature selection method"
    )

    # Performance metrics
    feature_count: int = Field(0, description="Total feature count")
    selected_feature_count: int = Field(0, description="Selected feature count")
    feature_quality_score: float = Field(
        0.0, ge=0.0, le=1.0, description="Feature quality score"
    )

    # Metadata
    created_at: datetime = Field(
        default_factory=datetime.now, description="Creation time"
    )
    last_updated: datetime = Field(
        default_factory=datetime.now, description="Last update time"
    )

    class Config:
        arbitrary_types_allowed = True


class RealDataScientist(BaseRealAgent):
    """Real Data Scientist Agent with advanced ML and feature engineering capabilities."""

    def __init__(self, config: RealAgentConfig):
        super().__init__(config)
        self.ml_manager = MLModelManager(config)

        # Data science components
        self.ml_models: Dict[str, MLModel] = {}
        self.feature_sets: Dict[str, FeatureEngineering] = {}
        self.anomaly_detectors: Dict[str, Any] = {}
        self.detected_anomalies: List[AnomalyDetection] = []

        # Feature engineering
        self.feature_scalers: Dict[str, Any] = {}
        self.feature_importance_cache: Dict[str, Dict[str, float]] = {}

        # Model performance tracking
        self.model_performance_history: List[Dict[str, Any]] = []
        self.feature_engineering_history: List[Dict[str, Any]] = []

        # ML pipeline configuration
        self.auto_feature_engineering = True
        self.auto_model_selection = True
        self.auto_hyperparameter_tuning = True

    async def _initialize_specific(self) -> bool:
        """Initialize data scientist specific components."""
        try:
            self.logger.info("Initializing data scientist specific components...")

            # Initialize ML model manager
            if not await self.ml_manager.initialize():
                self.logger.error("Failed to initialize ML model manager")
                return False

            # Initialize feature engineering
            await self._initialize_feature_engineering()

            # Initialize anomaly detection
            await self._initialize_anomaly_detection()

            # Create default models
            await self._create_default_models()

            self.logger.info("Data scientist initialization completed")
            return True

        except Exception as e:
            self.logger.exception(f"Failed to initialize data scientist: {e}")
            return False

    async def _initialize_feature_engineering(self) -> None:
        """Initialize feature engineering components."""
        try:
            # Initialize feature scalers
            self.feature_scalers = {
                "standard": StandardScaler(),
                "robust": RobustScaler(),
            }

            # Create default feature set
            await self._create_default_feature_set()

            self.logger.info("Feature engineering initialized")

        except Exception as e:
            self.logger.error(f"Error initializing feature engineering: {e}")

    async def _create_default_feature_set(self) -> None:
        """Create default feature set for Hong Kong market."""
        try:
            features = [
                Feature(
                    feature_name="price_momentum_5d",
                    feature_type=FeatureType.TECHNICAL,
                    description="5日价格动量",
                    calculation_method="(close_t - close_t - 5) / close_t - 5",
                ),
                Feature(
                    feature_name="volume_ratio",
                    feature_type=FeatureType.MARKET_MICROSTRUCTURE,
                    description="成交量比率",
                    calculation_method="volume_t / avg_volume_20d",
                ),
                Feature(
                    feature_name="volatility_20d",
                    feature_type=FeatureType.TECHNICAL,
                    description="20日波动率",
                    calculation_method="std(returns_20d)",
                ),
                Feature(
                    feature_name="rsi_14",
                    feature_type=FeatureType.TECHNICAL,
                    description="14日RSI",
                    calculation_method="RSI(14)",
                ),
                Feature(
                    feature_name="macd_signal",
                    feature_type=FeatureType.TECHNICAL,
                    description="MACD信号",
                    calculation_method="MACD(12,26,9)",
                ),
                Feature(
                    feature_name="bollinger_position",
                    feature_type=FeatureType.TECHNICAL,
                    description="布林带位置",
                    calculation_method="(close - lower_band) / (upper_band - lower_band)",
                ),
            ]

            feature_set = FeatureEngineering(
                feature_set_id="hk_market_default",
                feature_set_name="香港市场默认特征集",
                features=features,
                preprocessing_steps=[
                    "normalization",
                    "outlier_removal",
                    "feature_selection",
                ],
                feature_selection_method="correlation_and_importance",
                feature_count=len(features),
                selected_feature_count=len(features),
            )

            self.feature_sets["hk_market_default"] = feature_set
            self.logger.info("Default feature set created")

        except Exception as e:
            self.logger.error(f"Error creating default feature set: {e}")

    async def _initialize_anomaly_detection(self) -> None:
        """Initialize anomaly detection models."""
        try:
            # Initialize isolation forest for general anomaly detection
            self.anomaly_detectors["isolation_forest"] = IsolationForest(
                contamination=0.1, random_state=42
            )

            # Initialize specific anomaly detectors
            self.anomaly_detectors["price_spike_detector"] = (
                self._create_price_spike_detector()
            )
            self.anomaly_detectors["volume_anomaly_detector"] = (
                self._create_volume_anomaly_detector()
            )

            self.logger.info("Anomaly detection initialized")

        except Exception as e:
            self.logger.error(f"Error initializing anomaly detection: {e}")

    def _create_price_spike_detector(self) -> Dict[str, Any]:
        """Create price spike anomaly detector."""
        return {
            "method": "statistical_threshold",
            "threshold_multiplier": 3.0,  # 3 standard deviations
            "window_size": 20,
            "min_change_pct": 0.05,  # 5% minimum change
        }

    def _create_volume_anomaly_detector(self) -> Dict[str, Any]:
        """Create volume anomaly detector."""
        return {
            "method": "volume_ratio_threshold",
            "high_volume_threshold": 3.0,  # 3x average volume
            "low_volume_threshold": 0.3,  # 30% of average volume
            "window_size": 20,
        }

    async def _create_default_models(self) -> None:
        """Create default ML models."""
        try:
            # Price prediction model
            price_model = MLModel(
                model_id="price_prediction_1d",
                model_name="1日价格预测模型",
                model_type=ModelType.RANDOM_FOREST,
                target_variable="next_day_return",
                status=ModelStatus.PENDING,
            )
            self.ml_models["price_prediction_1d"] = price_model

            # Volatility prediction model
            volatility_model = MLModel(
                model_id="volatility_prediction",
                model_name="波动率预测模型",
                model_type=ModelType.GRADIENT_BOOSTING,
                target_variable="next_day_volatility",
                status=ModelStatus.PENDING,
            )
            self.ml_models["volatility_prediction"] = volatility_model

            self.logger.info("Default ML models created")

        except Exception as e:
            self.logger.error(f"Error creating default models: {e}")

    async def _enhance_analysis(
        self, base_result: AnalysisResult, market_data: List[RealMarketData]
    ) -> AnalysisResult:
        """Enhance analysis with data science specific logic."""
        try:
            # Perform feature engineering
            engineered_features = await self._perform_feature_engineering(market_data)

            # Update base result
            enhanced_result = base_result.copy()

            # Add ML insights
            ml_insights = await self._generate_ml_insights(
                engineered_features, enhanced_result
            )
            enhanced_result.insights.extend(ml_insights)

            # Add anomaly detection results
            anomaly_insights = await self._detect_anomalies(market_data)
            enhanced_result.insights.extend(anomaly_insights)

            return enhanced_result

        except Exception as e:
            self.logger.error(f"Error enhancing analysis for data science: {e}")
            return base_result

    async def _perform_feature_engineering(
        self, market_data: List[RealMarketData]
    ) -> Dict[str, Any]:
        """Perform comprehensive feature engineering."""
        try:
            if len(market_data) < 20:
                return {}

            # Convert to DataFrame
            df = pd.DataFrame(
                [
                    {
                        "timestamp": d.timestamp,
                        "symbol": d.symbol,
                        "open": float(d.open_price),
                        "high": float(d.high_price),
                        "low": float(d.low_price),
                        "close": float(d.close_price),
                        "volume": d.volume,
                    }
                    for d in market_data
                ]
            )

            df.set_index("timestamp", inplace=True)
            df.sort_index(inplace=True)

            # Group by symbol for feature calculation
            engineered_features = {}

            for symbol in df["symbol"].unique():
                symbol_data = df[df["symbol"] == symbol].copy()
                if len(symbol_data) < 20:
                    continue

                # Calculate technical features
                symbol_features = await self._calculate_technical_features(symbol_data)
                engineered_features[symbol] = symbol_features

            return engineered_features

        except Exception as e:
            self.logger.error(f"Error in feature engineering: {e}")
            return {}

    async def _calculate_technical_features(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate technical features for a symbol."""
        try:
            features = {}

            # Price momentum
            features["price_momentum_5d"] = (
                (df["close"].iloc[-1] - df["close"].iloc[-6]) / df["close"].iloc[-6]
                if len(df) >= 6
                else 0
            )

            # Volume ratio
            avg_volume_20d = df["volume"].tail(20).mean()
            features["volume_ratio"] = (
                df["volume"].iloc[-1] / avg_volume_20d if avg_volume_20d > 0 else 1
            )

            # Volatility
            returns = df["close"].pct_change().dropna()
            features["volatility_20d"] = (
                returns.tail(20).std() if len(returns) >= 20 else 0
            )

            # RSI (simplified)
            features["rsi_14"] = self._calculate_rsi(df["close"], 14)

            # MACD (simplified)
            macd_line, signal_line = self._calculate_macd(df["close"])
            features["macd_signal"] = (
                macd_line - signal_line if macd_line and signal_line else 0
            )

            # Bollinger Bands position
            bb_position = self._calculate_bollinger_position(df["close"])
            features["bollinger_position"] = bb_position

            return features

        except Exception as e:
            self.logger.error(f"Error calculating technical features: {e}")
            return {}

    def _calculate_rsi(self, prices: pd.Series, window: int = 14) -> float:
        """Calculate RSI indicator."""
        try:
            if len(prices) < window + 1:
                return 50.0

            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()

            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))

            return float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50.0

        except Exception:
            return 50.0

    def _calculate_macd(
        self, prices: pd.Series
    ) -> Tuple[Optional[float], Optional[float]]:
        """Calculate MACD indicator."""
        try:
            if len(prices) < 26:
                return None, None

            ema_12 = prices.ewm(span=12).mean()
            ema_26 = prices.ewm(span=26).mean()

            macd_line = ema_12 - ema_26
            signal_line = macd_line.ewm(span=9).mean()

            return float(macd_line.iloc[-1]), float(signal_line.iloc[-1])

        except Exception:
            return None, None

    def _calculate_bollinger_position(
        self, prices: pd.Series, window: int = 20, std_dev: int = 2
    ) -> float:
        """Calculate Bollinger Bands position."""
        try:
            if len(prices) < window:
                return 0.5

            sma = prices.rolling(window=window).mean()
            std = prices.rolling(window=window).std()

            upper_band = sma + (std * std_dev)
            lower_band = sma - (std * std_dev)

            current_price = prices.iloc[-1]
            upper = upper_band.iloc[-1]
            lower = lower_band.iloc[-1]

            if upper - lower == 0:
                return 0.5

            position = (current_price - lower) / (upper - lower)
            return float(position)

        except Exception:
            return 0.5

    async def _generate_ml_insights(
        self, engineered_features: Dict[str, Any], analysis_result: AnalysisResult
    ) -> List[str]:
        """Generate ML - based insights."""
        try:
            insights = []

            # Feature quality insights
            for symbol, features in engineered_features.items():
                feature_count = len(features)
                insights.append(f"{symbol}: 生成 {feature_count} 个技术特征")

                # Highlight significant features
                if features.get("volume_ratio", 1) > 2:
                    insights.append(
                        f"{symbol}: 成交量异常放大 ({features['volume_ratio']:.1f}x)"
                    )

                if features.get("price_momentum_5d", 0) > 0.1:
                    insights.append(
                        f"{symbol}: 5日动量强劲 ({features['price_momentum_5d']:.1%})"
                    )

                if features.get("volatility_20d", 0) > 0.03:
                    insights.append(
                        f"{symbol}: 波动率较高 ({features['volatility_20d']:.1%})"
                    )

            return insights

        except Exception as e:
            self.logger.error(f"Error generating ML insights: {e}")
            return []

    async def _detect_anomalies(self, market_data: List[RealMarketData]) -> List[str]:
        """Detect anomalies in market data."""
        try:
            insights = []

            if len(market_data) < 10:
                return insights

            # Group by symbol
            symbol_data = {}
            for data in market_data:
                symbol = data.symbol
                if symbol not in symbol_data:
                    symbol_data[symbol] = []
                symbol_data[symbol].append(data)

            # Detect anomalies for each symbol
            for symbol, data_list in symbol_data.items():
                if len(data_list) < 10:
                    continue

                # Price spike detection
                price_anomalies = await self._detect_price_spikes(symbol, data_list)
                insights.extend(price_anomalies)

                # Volume anomaly detection
                volume_anomalies = await self._detect_volume_anomalies(
                    symbol, data_list
                )
                insights.extend(volume_anomalies)

            return insights

        except Exception as e:
            self.logger.error(f"Error detecting anomalies: {e}")
            return []

    async def _detect_price_spikes(
        self, symbol: str, data_list: List[RealMarketData]
    ) -> List[str]:
        """Detect price spikes."""
        try:
            insights = []

            if len(data_list) < 20:
                return insights

            # Calculate price changes
            prices = [float(d.close_price) for d in data_list]
            price_changes = [
                (prices[i] - prices[i - 1]) / prices[i - 1]
                for i in range(1, len(prices))
            ]

            if not price_changes:
                return insights

            # Calculate threshold
            mean_change = np.mean(price_changes)
            std_change = np.std(price_changes)
            threshold = mean_change + 3 * std_change

            # Check for spikes
            for i, change in enumerate(price_changes):
                if abs(change) > abs(threshold):
                    anomaly = AnomalyDetection(
                        anomaly_id=f"price_spike_{symbol}_{i}",
                        anomaly_type=AnomalyType.PRICE_SPIKE,
                        symbol=symbol,
                        severity=min(abs(change) / abs(threshold), 1.0),
                        confidence=0.8,
                        description=f"价格异常波动 {change:.2%}",
                        potential_impact="high" if abs(change) > 0.05 else "medium",
                        recommended_action="investigate",
                    )
                    self.detected_anomalies.append(anomaly)
                    insights.append(f"🚨 {symbol}: 价格异常波动 {change:.2%}")

            return insights

        except Exception as e:
            self.logger.error(f"Error detecting price spikes: {e}")
            return []

    async def _detect_volume_anomalies(
        self, symbol: str, data_list: List[RealMarketData]
    ) -> List[str]:
        """Detect volume anomalies."""
        try:
            insights = []

            if len(data_list) < 20:
                return insights

            # Calculate volume statistics
            volumes = [d.volume for d in data_list]
            avg_volume = np.mean(volumes[:-1])  # Exclude current volume
            current_volume = volumes[-1]

            if avg_volume == 0:
                return insights

            volume_ratio = current_volume / avg_volume

            # Check for volume anomalies
            if volume_ratio > 3.0:
                anomaly = AnomalyDetection(
                    anomaly_id=f"volume_spike_{symbol}",
                    anomaly_type=AnomalyType.VOLUME_ANOMALY,
                    symbol=symbol,
                    severity=min((volume_ratio - 1) / 2, 1.0),
                    confidence=0.9,
                    description=f"成交量异常放大 {volume_ratio:.1f}x",
                    potential_impact="medium",
                    recommended_action="monitor",
                )
                self.detected_anomalies.append(anomaly)
                insights.append(f"📊 {symbol}: 成交量异常放大 {volume_ratio:.1f}x")

            elif volume_ratio < 0.3:
                anomaly = AnomalyDetection(
                    anomaly_id=f"volume_drop_{symbol}",
                    anomaly_type=AnomalyType.VOLUME_ANOMALY,
                    symbol=symbol,
                    severity=min((1 - volume_ratio) / 0.7, 1.0),
                    confidence=0.8,
                    description=f"成交量异常萎缩 {volume_ratio:.1f}x",
                    potential_impact="low",
                    recommended_action="monitor",
                )
                self.detected_anomalies.append(anomaly)
                insights.append(f"📉 {symbol}: 成交量异常萎缩 {volume_ratio:.1f}x")

            return insights

        except Exception as e:
            self.logger.error(f"Error detecting volume anomalies: {e}")
            return []

    async def _enhance_signals(
        self, base_signals: List[Dict[str, Any]], analysis_result: AnalysisResult
    ) -> List[Dict[str, Any]]:
        """Enhance signals with ML predictions."""
        try:
            enhanced_signals = []

            # Generate ML - based signals
            ml_signals = await self._generate_ml_signals(analysis_result)
            enhanced_signals.extend(ml_signals)

            # Enhance existing signals with ML confidence
            enhanced_base_signals = await self._enhance_signals_with_ml_confidence(
                base_signals, analysis_result
            )
            enhanced_signals.extend(enhanced_base_signals)

            return enhanced_signals

        except Exception as e:
            self.logger.error(f"Error enhancing signals with ML: {e}")
            return base_signals

    async def _generate_ml_signals(
        self, analysis_result: AnalysisResult
    ) -> List[Dict[str, Any]]:
        """Generate ML - based trading signals."""
        try:
            ml_signals = []

            # Check if we have trained models
            trained_models = [
                m for m in self.ml_models.values() if m.status == ModelStatus.TRAINED
            ]

            if not trained_models:
                return ml_signals

            # Generate signals based on ML predictions
            for model in trained_models:
                if model.model_id == "price_prediction_1d":
                    signal = await self._generate_price_prediction_signal(
                        model, analysis_result
                    )
                    if signal:
                        ml_signals.append(signal)

                elif model.model_id == "volatility_prediction":
                    signal = await self._generate_volatility_prediction_signal(
                        model, analysis_result
                    )
                    if signal:
                        ml_signals.append(signal)

            return ml_signals

        except Exception as e:
            self.logger.error(f"Error generating ML signals: {e}")
            return []

    async def _generate_price_prediction_signal(
        self, model: MLModel, analysis_result: AnalysisResult
    ) -> Optional[Dict[str, Any]]:
        """Generate signal based on price prediction."""
        try:
            # Simulate ML prediction (in real implementation, this would use the actual trained model)
            prediction_confidence = np.random.uniform(0.6, 0.9)
            predicted_return = np.random.uniform(-0.05, 0.05)

            if abs(predicted_return) < 0.01:  # Less than 1% predicted change
                return None

            signal_side = "buy" if predicted_return > 0 else "sell"
            signal_strength = min(abs(predicted_return) * 10, 1.0)  # Scale to 0 - 1

            return {
                "signal_id": f"ml_price_{model.model_id}_{datetime.now().strftime('%Y % m % d_ % H % M % S')}",
                "symbol": "ML_PREDICTION",
                "side": signal_side,
                "strength": signal_strength,
                "confidence": prediction_confidence,
                "reasoning": f"ML价格预测: {predicted_return:.2%} 变化 (置信度: {prediction_confidence:.1%})",
                "signal_type": "ml_prediction",
                "model_id": model.model_id,
                "predicted_return": predicted_return,
            }

        except Exception as e:
            self.logger.error(f"Error generating price prediction signal: {e}")
            return None

    async def _generate_volatility_prediction_signal(
        self, model: MLModel, analysis_result: AnalysisResult
    ) -> Optional[Dict[str, Any]]:
        """Generate signal based on volatility prediction."""
        try:
            # Simulate volatility prediction
            predicted_volatility = np.random.uniform(0.01, 0.05)
            prediction_confidence = np.random.uniform(0.7, 0.9)

            # High volatility warning signal
            if predicted_volatility > 0.03:
                return {
                    "signal_id": f"ml_volatility_{model.model_id}_{datetime.now().strftime('%Y % m % d_ % H % M % S')}",
                    "symbol": "VOLATILITY_WARNING",
                    "side": "risk_reduction",
                    "strength": min(predicted_volatility * 20, 1.0),
                    "confidence": prediction_confidence,
                    "reasoning": f"ML波动率预测: 预期高波动率 {predicted_volatility:.2%}",
                    "signal_type": "volatility_warning",
                    "model_id": model.model_id,
                    "predicted_volatility": predicted_volatility,
                }

            return None

        except Exception as e:
            self.logger.error(f"Error generating volatility prediction signal: {e}")
            return None

    async def _enhance_signals_with_ml_confidence(
        self, base_signals: List[Dict[str, Any]], analysis_result: AnalysisResult
    ) -> List[Dict[str, Any]]:
        """Enhance existing signals with ML confidence scores."""
        try:
            enhanced_signals = []

            for signal in base_signals:
                enhanced_signal = signal.copy()

                # Add ML confidence score
                ml_confidence = await self._calculate_ml_confidence(
                    signal, analysis_result
                )
                enhanced_signal["ml_confidence"] = ml_confidence

                # Adjust overall confidence
                original_confidence = enhanced_signal.get("confidence", 0.5)
                enhanced_signal["confidence"] = (
                    original_confidence + ml_confidence
                ) / 2

                enhanced_signals.append(enhanced_signal)

            return enhanced_signals

        except Exception as e:
            self.logger.error(f"Error enhancing signals with ML confidence: {e}")
            return base_signals

    async def _calculate_ml_confidence(
        self, signal: Dict[str, Any], analysis_result: AnalysisResult
    ) -> float:
        """Calculate ML - based confidence for a signal."""
        try:
            # Simulate ML confidence calculation based on various factors
            base_confidence = 0.5

            # Factor 1: Market regime alignment
            regime = analysis_result.market_regime.regime_type
            if regime in ["bull_market", "stable"]:
                base_confidence += 0.1
            elif regime in ["bear_market", "high_volatility"]:
                base_confidence -= 0.1

            # Factor 2: Signal strength
            signal_strength = signal.get("strength", 0.5)
            base_confidence += (signal_strength - 0.5) * 0.3

            # Factor 3: Recent model performance
            if self.model_performance_history:
                recent_performance = self.model_performance_history[-1].get(
                    "avg_score", 0.5
                )
                base_confidence += (recent_performance - 0.5) * 0.2

            return max(0.0, min(1.0, base_confidence))

        except Exception as e:
            self.logger.error(f"Error calculating ML confidence: {e}")
            return 0.5

    async def _execute_signal(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """Execute data science signal."""
        try:
            signal_type = signal.get("signal_type", "")

            if signal_type == "ml_prediction":
                return await self._execute_ml_prediction_signal(signal)
            elif signal_type == "volatility_warning":
                return await self._execute_volatility_warning_signal(signal)
            else:
                return {
                    "signal_id": signal.get("signal_id", "unknown"),
                    "status": "ml_validated",
                    "ml_confidence": signal.get("ml_confidence", 0.5),
                }

        except Exception as e:
            self.logger.error(f"Error executing data science signal: {e}")
            return {
                "signal_id": signal.get("signal_id", "unknown"),
                "status": "failed",
                "error": str(e),
            }

    async def _execute_ml_prediction_signal(
        self, signal: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute ML prediction signal."""
        try:
            model_id = signal.get("model_id", "")
            predicted_return = signal.get("predicted_return", 0)
            confidence = signal.get("confidence", 0)

            return {
                "signal_id": signal.get("signal_id", "unknown"),
                "status": "ml_prediction_executed",
                "model_id": model_id,
                "predicted_return": predicted_return,
                "confidence": confidence,
                "execution_time": datetime.now(),
            }

        except Exception as e:
            self.logger.error(f"Error executing ML prediction signal: {e}")
            return {
                "signal_id": signal.get("signal_id", "unknown"),
                "status": "failed",
                "error": str(e),
            }

    async def _execute_volatility_warning_signal(
        self, signal: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute volatility warning signal."""
        try:
            predicted_volatility = signal.get("predicted_volatility", 0)
            confidence = signal.get("confidence", 0)

            return {
                "signal_id": signal.get("signal_id", "unknown"),
                "status": "volatility_warning_issued",
                "predicted_volatility": predicted_volatility,
                "confidence": confidence,
                "warning_level": "high" if predicted_volatility > 0.04 else "medium",
                "execution_time": datetime.now(),
            }

        except Exception as e:
            self.logger.error(f"Error executing volatility warning signal: {e}")
            return {
                "signal_id": signal.get("signal_id", "unknown"),
                "status": "failed",
                "error": str(e),
            }

    async def get_data_science_summary(self) -> Dict[str, Any]:
        """Get comprehensive data science summary."""
        try:
            summary = {
                "agent_id": self.config.agent_id,
                "agent_name": self.config.name,
                "status": self.real_status,
                # ML Models
                "total_models": len(self.ml_models),
                "trained_models": len(
                    [
                        m
                        for m in self.ml_models.values()
                        if m.status == ModelStatus.TRAINED
                    ]
                ),
                "deployed_models": len(
                    [m for m in self.ml_models.values() if m.deployment_status]
                ),
                # Feature Engineering
                "total_feature_sets": len(self.feature_sets),
                "total_features": sum(
                    fs.feature_count for fs in self.feature_sets.values()
                ),
                "selected_features": sum(
                    fs.selected_feature_count for fs in self.feature_sets.values()
                ),
                # Anomaly Detection
                "total_anomalies_detected": len(self.detected_anomalies),
                "active_anomaly_detectors": len(self.anomaly_detectors),
                # Performance
                "model_performance_history": len(self.model_performance_history),
                "feature_engineering_history": len(self.feature_engineering_history),
                # Configuration
                "auto_feature_engineering": self.auto_feature_engineering,
                "auto_model_selection": self.auto_model_selection,
                "auto_hyperparameter_tuning": self.auto_hyperparameter_tuning,
            }

            # Add model details
            summary["models"] = {}
            for model_id, model in self.ml_models.items():
                summary["models"][model_id] = {
                    "name": model.model_name,
                    "type": model.model_type.value,
                    "status": model.status.value,
                    "validation_score": model.validation_score,
                    "deployment_status": model.deployment_status,
                }

            return summary

        except Exception as e:
            self.logger.error(f"Error getting data science summary: {e}")
            return {"error": str(e)}

    async def cleanup(self) -> None:
        """Cleanup data scientist resources."""
        try:
            self.logger.info(f"Cleaning up data scientist: {self.config.name}")

            # Clear all collections
            self.ml_models.clear()
            self.feature_sets.clear()
            self.anomaly_detectors.clear()
            self.detected_anomalies.clear()
            self.feature_scalers.clear()
            self.feature_importance_cache.clear()
            self.model_performance_history.clear()
            self.feature_engineering_history.clear()

            # Call parent cleanup
            await super().cleanup()

            self.logger.info("Data scientist cleanup completed")

        except Exception as e:
            self.logger.exception(f"Error during cleanup: {e}")
