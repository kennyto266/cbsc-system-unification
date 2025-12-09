"""Machine learning integration for real AI agents."""

import asyncio
import logging
import pickle
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from .base_real_agent import RealAgentConfig


class ModelType(str, Enum):
    """Types of machine learning models."""

    REGRESSION = "regression"
    CLASSIFICATION = "classification"
    TIME_SERIES = "time_series"
    REINFORCEMENT_LEARNING = "reinforcement_learning"
    DEEP_LEARNING = "deep_learning"
    ENSEMBLE = "ensemble"


class ModelPerformance(BaseModel):
    """Model performance metrics."""

    model_name: str = Field(..., description="Model name")
    model_type: ModelType = Field(..., description="Model type")

    # Performance metrics
    accuracy: Optional[float] = Field(None, description="Model accuracy")
    precision: Optional[float] = Field(None, description="Model precision")
    recall: Optional[float] = Field(None, description="Model recall")
    f1_score: Optional[float] = Field(None, description="F1 score")
    mse: Optional[float] = Field(None, description="Mean squared error")
    mae: Optional[float] = Field(None, description="Mean absolute error")
    r2_score: Optional[float] = Field(None, description="R - squared score")
    sharpe_ratio: Optional[float] = Field(
        None, description="Sharpe ratio for trading models"
    )

    # Training metrics
    training_time: float = Field(..., description="Training time in seconds")
    last_trained: datetime = Field(..., description="Last training timestamp")
    training_samples: int = Field(..., description="Number of training samples")

    # Model metadata
    feature_count: int = Field(..., description="Number of features")
    model_size_mb: float = Field(..., description="Model size in MB")

    class Config:
        use_enum_values = True


class FeatureConfig(BaseModel):
    """Configuration for feature engineering."""

    technical_indicators: bool = Field(True, description="Include technical indicators")
    price_features: bool = Field(True, description="Include price - based features")
    volume_features: bool = Field(True, description="Include volume - based features")
    time_features: bool = Field(True, description="Include time - based features")
    market_features: bool = Field(True, description="Include market - wide features")

    # Technical indicator parameters
    sma_periods: List[int] = Field(
        default_factory=lambda: [5, 10, 20, 50], description="SMA periods"
    )
    ema_periods: List[int] = Field(
        default_factory=lambda: [12, 26], description="EMA periods"
    )
    rsi_period: int = Field(14, description="RSI period")
    macd_params: Dict[str, int] = Field(
        default_factory=lambda: {"fast": 12, "slow": 26, "signal": 9},
        description="MACD parameters",
    )

    # Feature engineering parameters
    lookback_periods: List[int] = Field(
        default_factory=lambda: [1, 3, 5, 10],
        description="Lookback periods for lag features",
    )
    volatility_periods: List[int] = Field(
        default_factory=lambda: [5, 10, 20],
        description="Volatility calculation periods",
    )


class MLModelManager:
    """Manager for machine learning models in real AI agents."""

    def __init__(self, config: Optional[RealAgentConfig] = None):
        self.config = config
        self.logger = logging.getLogger("hk_quant_system.ml_manager")
        self.models: Dict[str, Any] = {}
        self.model_performance: Dict[str, ModelPerformance] = {}
        self.feature_config = FeatureConfig()
        self._initialized = False

    async def initialize(self) -> bool:
        """Initialize the ML model manager."""
        try:
            self.logger.info("Initializing ML model manager...")

            # Load existing models if any
            await self._load_existing_models()

            self._initialized = True
            self.logger.info("ML model manager initialized successfully")
            return True

        except Exception as e:
            self.logger.exception(f"Failed to initialize ML model manager: {e}")
            return False

    async def _load_existing_models(self) -> None:
        """Load existing models from storage."""
        try:
            models_dir = Path("models")
            if not models_dir.exists():
                models_dir.mkdir(parents=True)
                return

            for model_file in models_dir.glob("*.pkl"):
                try:
                    model_name = model_file.stem
                    with open(model_file, "rb") as f:
                        model = pickle.load(f)

                    self.models[model_name] = model
                    self.logger.info(f"Loaded model: {model_name}")

                except Exception as e:
                    self.logger.error(f"Failed to load model {model_file}: {e}")

        except Exception as e:
            self.logger.exception(f"Error loading existing models: {e}")

    async def load_model(self, model_name: str) -> Optional[Any]:
        """Load a specific model."""
        try:
            if model_name in self.models:
                return self.models[model_name]

            # Try to load from file
            model_file = Path(f"models/{model_name}.pkl")
            if model_file.exists():
                with open(model_file, "rb") as f:
                    model = pickle.load(f)
                self.models[model_name] = model
                self.logger.info(f"Loaded model from file: {model_name}")
                return model

            self.logger.warning(f"Model not found: {model_name}")
            return None

        except Exception as e:
            self.logger.error(f"Error loading model {model_name}: {e}")
            return None

    async def save_model(
        self, model_name: str, model: Any, performance: ModelPerformance
    ) -> bool:
        """Save a model to storage."""
        try:
            # Save model
            models_dir = Path("models")
            models_dir.mkdir(parents=True, exist_ok=True)

            model_file = models_dir / f"{model_name}.pkl"
            with open(model_file, "wb") as f:
                pickle.dump(model, f)

            # Update performance tracking
            self.model_performance[model_name] = performance

            self.logger.info(f"Saved model: {model_name}")
            return True

        except Exception as e:
            self.logger.error(f"Error saving model {model_name}: {e}")
            return False

    async def train_model(
        self,
        model_name: str,
        model_type: ModelType,
        training_data: pd.DataFrame,
        target_column: str,
        model_params: Optional[Dict[str, Any]] = None,
    ) -> Optional[ModelPerformance]:
        """Train a new model."""
        try:
            self.logger.info(f"Training model: {model_name} ({model_type})")

            # Prepare features and target
            features = training_data.drop(columns=[target_column])
            target = training_data[target_column]

            # Feature engineering
            features = await self._engineer_features(features)

            # Train model based on type
            model = await self._train_model_by_type(
                model_type, features, target, model_params
            )

            if model is None:
                self.logger.error(f"Failed to train model: {model_name}")
                return None

            # Evaluate model
            performance = await self._evaluate_model(
                model, model_type, features, target, model_name
            )

            # Save model
            if await self.save_model(model_name, model, performance):
                self.models[model_name] = model
                return performance
            else:
                return None

        except Exception as e:
            self.logger.exception(f"Error training model {model_name}: {e}")
            return None

    async def _train_model_by_type(
        self,
        model_type: ModelType,
        features: pd.DataFrame,
        target: pd.Series,
        model_params: Optional[Dict[str, Any]],
    ) -> Optional[Any]:
        """Train model based on type."""
        try:
            if model_type == ModelType.REGRESSION:
                from sklearn.ensemble import RandomForestRegressor

                model = RandomForestRegressor(
                    n_estimators=model_params.get("n_estimators", 100),
                    max_depth=model_params.get("max_depth", 10),
                    random_state=42,
                )
                model.fit(features, target)
                return model

            elif model_type == ModelType.CLASSIFICATION:
                from sklearn.ensemble import RandomForestClassifier

                model = RandomForestClassifier(
                    n_estimators=model_params.get("n_estimators", 100),
                    max_depth=model_params.get("max_depth", 10),
                    random_state=42,
                )
                model.fit(features, target)
                return model

            elif model_type == ModelType.TIME_SERIES:
                # Simple ARIMA - like model for demonstration
                # In practice, you might use more sophisticated time series models
                from sklearn.linear_model import LinearRegression

                # Create lag features
                lag_features = features.copy()
                for lag in [1, 2, 3, 5, 10]:
                    lag_features[f"lag_{lag}"] = target.shift(lag)

                lag_features = lag_features.dropna()
                lag_target = target.iloc[len(target) - len(lag_features) :]

                model = LinearRegression()
                model.fit(lag_features, lag_target)
                return model

            elif model_type == ModelType.ENSEMBLE:
                from sklearn.ensemble import RandomForestRegressor, VotingRegressor
                from sklearn.linear_model import LinearRegression

                # Create ensemble of different models
                models = [
                    ("linear", LinearRegression()),
                    ("rf", RandomForestRegressor(n_estimators=50, random_state=42)),
                ]

                ensemble = VotingRegressor(models)
                ensemble.fit(features, target)
                return ensemble

            else:
                self.logger.warning(f"Unsupported model type: {model_type}")
                return None

        except Exception as e:
            self.logger.error(f"Error training {model_type} model: {e}")
            return None

    async def _engineer_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Engineer features for machine learning."""
        try:
            features = data.copy()

            # Ensure we have required columns
            required_columns = ["open", "high", "low", "close", "volume"]
            for col in required_columns:
                if col not in features.columns:
                    self.logger.warning(f"Missing required column: {col}")
                    continue

            if not all(col in features.columns for col in required_columns):
                return features

            # Technical indicators
            if self.feature_config.technical_indicators:
                # Simple Moving Averages
                for period in self.feature_config.sma_periods:
                    features[f"sma_{period}"] = (
                        features["close"].rolling(window=period).mean()
                    )

                # Exponential Moving Averages
                for period in self.feature_config.ema_periods:
                    features[f"ema_{period}"] = (
                        features["close"].ewm(span=period).mean()
                    )

                # RSI
                features["rsi"] = await self._calculate_rsi(
                    features["close"], self.feature_config.rsi_period
                )

                # MACD
                macd_params = self.feature_config.macd_params
                ema_fast = features["close"].ewm(span=macd_params["fast"]).mean()
                ema_slow = features["close"].ewm(span=macd_params["slow"]).mean()
                features["macd"] = ema_fast - ema_slow
                features["macd_signal"] = (
                    features["macd"].ewm(span=macd_params["signal"]).mean()
                )
                features["macd_histogram"] = features["macd"] - features["macd_signal"]

            # Price features
            if self.feature_config.price_features:
                features["price_change"] = features["close"].pct_change()
                features["high_low_ratio"] = features["high"] / features["low"]
                features["close_open_ratio"] = features["close"] / features["open"]

                # Price volatility
                for period in self.feature_config.volatility_periods:
                    features[f"volatility_{period}"] = (
                        features["close"].rolling(window=period).std()
                    )

            # Volume features
            if self.feature_config.volume_features:
                features["volume_change"] = features["volume"].pct_change()
                features["volume_sma_20"] = features["volume"].rolling(window=20).mean()
                features["volume_ratio"] = (
                    features["volume"] / features["volume_sma_20"]
                )

            # Time features
            if self.feature_config.time_features:
                if "timestamp" in features.columns:
                    features["hour"] = pd.to_datetime(features["timestamp"]).dt.hour
                    features["day_of_week"] = pd.to_datetime(
                        features["timestamp"]
                    ).dt.dayofweek
                    features["month"] = pd.to_datetime(features["timestamp"]).dt.month

            # Lag features
            for lag in self.feature_config.lookback_periods:
                for col in ["close", "volume"]:
                    if col in features.columns:
                        features[f"{col}_lag_{lag}"] = features[col].shift(lag)

            # Fill NaN values
            features = features.fillna(method="ffill").fillna(method="bfill")

            return features

        except Exception as e:
            self.logger.error(f"Error engineering features: {e}")
            return data

    async def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI for feature engineering."""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))

            return rsi.fillna(50)  # Neutral RSI for NaN values

        except Exception:
            return pd.Series([50] * len(prices), index=prices.index)

    async def _evaluate_model(
        self,
        model: Any,
        model_type: ModelType,
        features: pd.DataFrame,
        target: pd.Series,
        model_name: str,
    ) -> ModelPerformance:
        """Evaluate model performance."""
        try:
            from sklearn.metrics import (
                accuracy_score,
                f1_score,
                mean_absolute_error,
                mean_squared_error,
                precision_score,
                r2_score,
                recall_score,
            )

            # Make predictions
            predictions = model.predict(features)

            # Calculate metrics based on model type
            if model_type == ModelType.CLASSIFICATION:
                accuracy = accuracy_score(target, predictions)
                precision = precision_score(
                    target, predictions, average="weighted", zero_division=0
                )
                recall = recall_score(
                    target, predictions, average="weighted", zero_division=0
                )
                f1 = f1_score(target, predictions, average="weighted", zero_division=0)

                performance = ModelPerformance(
                    model_name=model_name,
                    model_type=model_type,
                    accuracy=accuracy,
                    precision=precision,
                    recall=recall,
                    f1_score=f1,
                    training_time=0.0,  # Would be calculated during training
                    last_trained=datetime.now(),
                    training_samples=len(features),
                    feature_count=len(features.columns),
                    model_size_mb=0.0,  # Would be calculated from model size
                )

            else:  # Regression or other types
                mse = mean_squared_error(target, predictions)
                mae = mean_absolute_error(target, predictions)
                r2 = r2_score(target, predictions)

                # Calculate Sharpe ratio if applicable (for trading models)
                sharpe_ratio = None
                if len(predictions) > 1:
                    returns = np.diff(predictions) / predictions[:-1]
                    if np.std(returns) > 0:
                        sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252)

                performance = ModelPerformance(
                    model_name=model_name,
                    model_type=model_type,
                    mse=mse,
                    mae=mae,
                    r2_score=r2,
                    sharpe_ratio=sharpe_ratio,
                    training_time=0.0,
                    last_trained=datetime.now(),
                    training_samples=len(features),
                    feature_count=len(features.columns),
                    model_size_mb=0.0,
                )

            return performance

        except Exception as e:
            self.logger.error(f"Error evaluating model {model_name}: {e}")
            # Return basic performance metrics
            return ModelPerformance(
                model_name=model_name,
                model_type=model_type,
                training_time=0.0,
                last_trained=datetime.now(),
                training_samples=len(features),
                feature_count=len(features.columns),
                model_size_mb=0.0,
            )

    async def predict(
        self, model_name: str, features: pd.DataFrame
    ) -> Optional[np.ndarray]:
        """Make predictions using a trained model."""
        try:
            if model_name not in self.models:
                await self.load_model(model_name)

            if model_name not in self.models:
                self.logger.error(f"Model not found: {model_name}")
                return None

            model = self.models[model_name]

            # Engineer features if needed
            engineered_features = await self._engineer_features(features)

            # Make predictions
            predictions = model.predict(engineered_features)
            return predictions

        except Exception as e:
            self.logger.error(f"Error making predictions with model {model_name}: {e}")
            return None

    async def get_model_performance(
        self, model_name: str
    ) -> Optional[ModelPerformance]:
        """Get performance metrics for a model."""
        return self.model_performance.get(model_name)

    async def list_models(self) -> List[str]:
        """List all available models."""
        return list(self.models.keys())

    async def delete_model(self, model_name: str) -> bool:
        """Delete a model."""
        try:
            # Remove from memory
            if model_name in self.models:
                del self.models[model_name]

            # Remove from performance tracking
            if model_name in self.model_performance:
                del self.model_performance[model_name]

            # Remove file
            model_file = Path(f"models/{model_name}.pkl")
            if model_file.exists():
                model_file.unlink()

            self.logger.info(f"Deleted model: {model_name}")
            return True

        except Exception as e:
            self.logger.error(f"Error deleting model {model_name}: {e}")
            return False

    async def retrain_model(
        self, model_name: str, new_data: pd.DataFrame, target_column: str
    ) -> Optional[ModelPerformance]:
        """Retrain an existing model with new data."""
        try:
            if model_name not in self.models:
                self.logger.error(f"Model not found for retraining: {model_name}")
                return None

            # Get existing model performance to determine model type
            existing_performance = self.model_performance.get(model_name)
            if not existing_performance:
                self.logger.error(f"No performance data found for model: {model_name}")
                return None

            # Retrain model
            new_performance = await self.train_model(
                model_name, existing_performance.model_type, new_data, target_column
            )

            return new_performance

        except Exception as e:
            self.logger.error(f"Error retraining model {model_name}: {e}")
            return None

    async def cleanup(self) -> None:
        """Cleanup ML model manager resources."""
        self.models.clear()
        self.model_performance.clear()
        self._initialized = False
        self.logger.info("ML model manager cleanup completed")
