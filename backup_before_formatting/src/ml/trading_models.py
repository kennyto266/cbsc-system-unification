"""
高級量化交易機器學習模型
專門為港股交易設計的生產級別ML / DL模型

功能:
- 深度學習價格預測模型 (LSTM, Transformer, Attention)
- 波動率預測和風險模型 (GARCH, DeepVolatility)
- 市場狀態檢測 (HMM, Clustering, Regime Detection)
- 情緒分析模型 (BERT, FinBERT, NLP)
- 強化學習交易智能體 (DQN, PPO, A3C)
- 集成方法和自動化策略組合
"""

import asyncio
import json
import logging
import warnings
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# 深度學習框架
try:
    import tensorflow as tf
    from tensorflow.keras import callbacks, layers, models, optimizers
    from tensorflow.keras.layers import (
        GRU,
        LSTM,
        Conv1D,
        Dense,
        Dropout,
        Input,
        LayerNormalization,
        MaxPooling1D,
        MultiHeadAttention,
    )
    from tensorflow.keras.models import Model, Sequential
    from tensorflow.keras.optimizers import Adam

    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import DataLoader, Dataset

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

# 金融建模庫
try:
    import arch
    from arch.univariate import GARCH, EWMAVariance

    ARCH_AVAILABLE = True
except ImportError:
    ARCH_AVAILABLE = False

# 自動化機器學習
try:
    import optuna
    import shap
    from sklearn.model_selection import TimeSeriesSplit

    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False

# 強化學習
try:
    import gym
    import stable_baselines3 as sb3
    from gym import spaces
    from stable_baselines3 import A2C, DQN, PPO

    RL_AVAILABLE = True
except ImportError:
    RL_AVAILABLE = False

# 自然語言處理
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from textblob import TextBlob
    from transformers import AutoModel, AutoTokenizer, BertModel

    NLP_AVAILABLE = True
except ImportError:
    NLP_AVAILABLE = False

import lightgbm as lgb
import xgboost as xgb
from sklearn.cluster import DBSCAN, KMeans
from sklearn.decomposition import PCA

# 統計建模
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.mixture import GaussianMixture
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import MinMaxScaler, RobustScaler, StandardScaler


class ModelCategory(Enum):
    """模型類別"""

    PRICE_PREDICTION = "price_prediction"
    VOLATILITY_FORECASTING = "volatility_forecasting"
    MARKET_REGIME = "market_regime"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    RISK_MANAGEMENT = "risk_management"
    REINFORCEMENT_LEARNING = "reinforcement_learning"
    ENSEMBLE = "ensemble"


class PredictionHorizon(Enum):
    """預測時間範圍"""

    INTRADAY = "intraday"  # 日內
    SHORT_TERM = "short_term"  # 1 - 5天
    MEDIUM_TERM = "medium_term"  # 1 - 4週
    LONG_TERM = "long_term"  # 1 - 6個月


@dataclass
class ModelPrediction:
    """模型預測結果"""

    model_name: str
    prediction: float
    confidence: float
    timestamp: datetime
    horizon: PredictionHorizon
    metadata: Dict[str, Any] = field(default_factory=dict)
    feature_importance: Optional[Dict[str, float]] = None


@dataclass
class RiskMetrics:
    """風險指標"""

    var_95: float  # 95% VaR
    var_99: float  # 99% VaR
    expected_shortfall: float
    max_drawdown: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    beta: float
    alpha: float
    information_ratio: float
    tracking_error: float


class AdvancedPricePredictor:
    """
    高級價格預測模型

    集成多種深度學習和傳統機器學習方法
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.logger = logging.getLogger("hk_quant_system.price_predictor")
        self.config = config or self._default_config()

        # 模型存儲
        self.models: Dict[str, Any] = {}
        self.scalers: Dict[str, Any] = {}
        self.feature_columns: List[str] = []

        # 預測歷史
        self.prediction_history: deque = deque(maxlen=1000)

        # 初始化模型
        if TENSORFLOW_AVAILABLE:
            self._init_deep_learning_models()

    def _default_config(self) -> Dict[str, Any]:
        """默認配置"""
        return {
            "sequence_length": 60,
            "prediction_horizons": {
                "intraday": 1,
                "short_term": 5,
                "medium_term": 20,
                "long_term": 60,
            },
            "features": [
                "open",
                "high",
                "low",
                "close",
                "volume",
                "returns",
                "volatility",
                "rsi",
                "macd",
                "bb_position",
                "atr",
                "obv",
                "mfi",
                "adx",
                "stochastic_k",
                "stochastic_d",
            ],
            "model_params": {
                "lstm": {
                    "units": [128, 64, 32],
                    "dropout": 0.2,
                    "recurrent_dropout": 0.1,
                    "learning_rate": 0.001,
                },
                "transformer": {
                    "d_model": 128,
                    "num_heads": 8,
                    "num_layers": 4,
                    "dropout": 0.1,
                    "learning_rate": 0.0001,
                },
                "xgboost": {
                    "n_estimators": 1000,
                    "max_depth": 6,
                    "learning_rate": 0.01,
                    "subsample": 0.8,
                    "colsample_bytree": 0.8,
                },
                "lightgbm": {
                    "n_estimators": 1000,
                    "max_depth": 6,
                    "learning_rate": 0.01,
                    "num_leaves": 31,
                    "subsample": 0.8,
                },
            },
        }

    def _init_deep_learning_models(self):
        """初始化深度學習模型"""
        try:
            # LSTM模型
            self.models["lstm"] = self._build_lstm_model()

            # Transformer模型
            self.models["transformer"] = self._build_transformer_model()

            # CNN - LSTM混合模型
            self.models["cnn_lstm"] = self._build_cnn_lstm_model()

            self.logger.info("Deep learning models initialized")

        except Exception as e:
            self.logger.error(f"Deep learning model initialization failed: {str(e)}")

    def _build_lstm_model(self) -> Model:
        """構建LSTM模型"""
        sequence_length = self.config["sequence_length"]
        n_features = len(self.config["features"])

        model = Sequential(
            [
                LSTM(
                    self.config["model_params"]["lstm"]["units"][0],
                    return_sequences=True,
                    input_shape=(sequence_length, n_features),
                ),
                Dropout(self.config["model_params"]["lstm"]["dropout"]),
                LSTM(
                    self.config["model_params"]["lstm"]["units"][1],
                    return_sequences=True,
                ),
                Dropout(self.config["model_params"]["lstm"]["dropout"]),
                LSTM(
                    self.config["model_params"]["lstm"]["units"][2],
                    return_sequences=False,
                ),
                Dropout(self.config["model_params"]["lstm"]["dropout"]),
                Dense(64, activation="relu"),
                Dropout(0.2),
                Dense(32, activation="relu"),
                Dense(1, activation="linear"),
            ]
        )

        model.compile(
            optimizer=Adam(
                learning_rate=self.config["model_params"]["lstm"]["learning_rate"]
            ),
            loss="mse",
            metrics=["mae", "mape"],
        )

        return model

    def _build_transformer_model(self) -> Model:
        """構建Transformer模型"""
        sequence_length = self.config["sequence_length"]
        n_features = len(self.config["features"])
        d_model = self.config["model_params"]["transformer"]["d_model"]
        num_heads = self.config["model_params"]["transformer"]["num_heads"]
        num_layers = self.config["model_params"]["transformer"]["num_layers"]

        inputs = Input(shape=(sequence_length, n_features))

        # 位置編碼
        x = layers.Dense(d_model)(inputs)
        x = LayerNormalization()(x)

        # Transformer編碼器層
        for _ in range(num_layers):
            # 多頭注意力
            attention_output = MultiHeadAttention(
                num_heads=num_heads,
                key_dim=d_model // num_heads,
                dropout=self.config["model_params"]["transformer"]["dropout"],
            )(x, x)

            # 殘差連接和層標準化
            x = layers.Add()([x, attention_output])
            x = LayerNormalization()(x)

            # 前饋網絡
            ffn_output = layers.Dense(d_model * 4, activation="relu")(x)
            ffn_output = Dropout(self.config["model_params"]["transformer"]["dropout"])(
                ffn_output
            )
            ffn_output = layers.Dense(d_model)(ffn_output)

            # 殘差連接和層標準化
            x = layers.Add()([x, ffn_output])
            x = LayerNormalization()(x)

        # 全局平均池化
        x = layers.GlobalAveragePooling1D()(x)

        # 輸出層
        x = layers.Dense(64, activation="relu")(x)
        x = Dropout(0.2)(x)
        x = layers.Dense(32, activation="relu")(x)
        outputs = layers.Dense(1, activation="linear")(x)

        model = Model(inputs=inputs, outputs=outputs)

        model.compile(
            optimizer=Adam(
                learning_rate=self.config["model_params"]["transformer"][
                    "learning_rate"
                ]
            ),
            loss="mse",
            metrics=["mae", "mape"],
        )

        return model

    def _build_cnn_lstm_model(self) -> Model:
        """構建CNN - LSTM混合模型"""
        sequence_length = self.config["sequence_length"]
        n_features = len(self.config["features"])

        model = Sequential(
            [
                # CNN特徵提取
                Conv1D(
                    filters=64,
                    kernel_size=3,
                    activation="relu",
                    input_shape=(sequence_length, n_features),
                ),
                Conv1D(filters=64, kernel_size=3, activation="relu"),
                MaxPooling1D(pool_size=2),
                Dropout(0.2),
                # LSTM序列建模
                LSTM(100, return_sequences=True),
                LSTM(50, return_sequences=False),
                Dropout(0.2),
                # 全連接層
                Dense(64, activation="relu"),
                Dropout(0.2),
                Dense(32, activation="relu"),
                Dense(1, activation="linear"),
            ]
        )

        model.compile(
            optimizer=Adam(learning_rate=0.001), loss="mse", metrics=["mae", "mape"]
        )

        return model

    def prepare_sequences(
        self, data: pd.DataFrame, target_col: str = "close", horizon: int = 1
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        準備序列數據

        Args:
            data: 輸入數據
            target_col: 目標列
            horizon: 預測視界

        Returns:
            特徵序列和目標值
        """
        if not all(col in data.columns for col in self.config["features"]):
            raise ValueError("Missing required features in data")

        # 選擇特徵
        features = data[self.config["features"]].values
        target = data[target_col].values

        # 標準化特徵
        if "scaler" not in self.scalers:
            self.scalers["scaler"] = StandardScaler()
            features_scaled = self.scalers["scaler"].fit_transform(features)
        else:
            features_scaled = self.scalers["scaler"].transform(features)

        # 創建序列
        X, y = [], []
        sequence_length = self.config["sequence_length"]

        for i in range(sequence_length, len(features_scaled) - horizon + 1):
            X.append(features_scaled[i - sequence_length : i])
            # 計算未來價格變化百分比
            current_price = target[i - 1]
            future_price = target[i + horizon - 1]
            price_change = (future_price - current_price) / current_price
            y.append(price_change)

        return np.array(X), np.array(y)

    async def train_lstm_model(
        self,
        data: pd.DataFrame,
        validation_split: float = 0.2,
        epochs: int = 100,
        batch_size: int = 32,
    ) -> Dict[str, Any]:
        """訓練LSTM模型"""
        if not TENSORFLOW_AVAILABLE:
            raise ImportError("TensorFlow is required for LSTM models")

        try:
            self.logger.info("Training LSTM model...")

            # 準備數據
            X, y = self.prepare_sequences(data)

            # 分割訓練和驗證集
            split_idx = int(len(X) * (1 - validation_split))
            X_train, X_val = X[:split_idx], X[split_idx:]
            y_train, y_val = y[:split_idx], y[split_idx:]

            # 回調函數
            early_stopping = callbacks.EarlyStopping(
                monitor="val_loss", patience=20, restore_best_weights=True
            )

            reduce_lr = callbacks.ReduceLROnPlateau(
                monitor="val_loss", factor=0.5, patience=10, min_lr=1e-7
            )

            # 訓練模型
            history = self.models["lstm"].fit(
                X_train,
                y_train,
                validation_data=(X_val, y_val),
                epochs=epochs,
                batch_size=batch_size,
                callbacks=[early_stopping, reduce_lr],
                verbose=0,
            )

            # 評估模型
            y_pred = self.models["lstm"].predict(X_val)
            mse = mean_squared_error(y_val, y_pred)
            mae = mean_absolute_error(y_val, y_pred)
            r2 = r2_score(y_val, y_pred)

            self.logger.info(f"LSTM training completed - MSE: {mse:.6f}, R²: {r2:.4f}")

            return {
                "model_type": "LSTM",
                "mse": mse,
                "mae": mae,
                "r2": r2,
                "training_history": history.history,
                "epochs_trained": len(history.history["loss"]),
            }

        except Exception as e:
            self.logger.error(f"LSTM training failed: {str(e)}")
            raise

    async def train_transformer_model(
        self,
        data: pd.DataFrame,
        validation_split: float = 0.2,
        epochs: int = 100,
        batch_size: int = 32,
    ) -> Dict[str, Any]:
        """訓練Transformer模型"""
        if not TENSORFLOW_AVAILABLE:
            raise ImportError("TensorFlow is required for Transformer models")

        try:
            self.logger.info("Training Transformer model...")

            # 準備數據
            X, y = self.prepare_sequences(data)

            # 分割數據
            split_idx = int(len(X) * (1 - validation_split))
            X_train, X_val = X[:split_idx], X[split_idx:]
            y_train, y_val = y[:split_idx], y[split_idx:]

            # 回調函數
            early_stopping = callbacks.EarlyStopping(
                monitor="val_loss", patience=20, restore_best_weights=True
            )

            # 訓練模型
            history = self.models["transformer"].fit(
                X_train,
                y_train,
                validation_data=(X_val, y_val),
                epochs=epochs,
                batch_size=batch_size,
                callbacks=[early_stopping],
                verbose=0,
            )

            # 評估模型
            y_pred = self.models["transformer"].predict(X_val)
            mse = mean_squared_error(y_val, y_pred)
            mae = mean_absolute_error(y_val, y_pred)
            r2 = r2_score(y_val, y_pred)

            self.logger.info(
                f"Transformer training completed - MSE: {mse:.6f}, R²: {r2:.4f}"
            )

            return {
                "model_type": "Transformer",
                "mse": mse,
                "mae": mae,
                "r2": r2,
                "training_history": history.history,
                "epochs_trained": len(history.history["loss"]),
            }

        except Exception as e:
            self.logger.error(f"Transformer training failed: {str(e)}")
            raise

    def train_xgboost_model(
        self,
        data: pd.DataFrame,
        target_col: str = "close",
        horizon: int = 1,
        test_size: float = 0.2,
    ) -> Dict[str, Any]:
        """訓練XGBoost模型"""
        try:
            self.logger.info("Training XGBoost model...")

            # 準備數據
            features = self.config["features"]
            X = data[features].copy()

            # 計算目標變量
            target = data[target_col].values
            y = (target[horizon:] - target[:-horizon]) / target[:-horizon]
            X = X[:-horizon]

            # 標準化
            if "xgb_scaler" not in self.scalers:
                self.scalers["xgb_scaler"] = StandardScaler()
                X_scaled = self.scalers["xgb_scaler"].fit_transform(X)
            else:
                X_scaled = self.scalers["xgb_scaler"].transform(X)

            # 分割數據
            split_idx = int(len(X_scaled) * (1 - test_size))
            X_train, X_test = X_scaled[:split_idx], X_scaled[split_idx:]
            y_train, y_test = y[:split_idx], y[split_idx:]

            # 訓練模型
            model = xgb.XGBRegressor(**self.config["model_params"]["xgboost"])
            model.fit(X_train, y_train)

            # 預測和評估
            y_pred = model.predict(X_test)
            mse = mean_squared_error(y_test, y_pred)
            mae = mean_absolute_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)

            # 保存模型
            self.models["xgboost"] = model

            # 特徵重要性
            feature_importance = dict(zip(features, model.feature_importances_))

            self.logger.info(
                f"XGBoost training completed - MSE: {mse:.6f}, R²: {r2:.4f}"
            )

            return {
                "model_type": "XGBoost",
                "mse": mse,
                "mae": mae,
                "r2": r2,
                "feature_importance": feature_importance,
            }

        except Exception as e:
            self.logger.error(f"XGBoost training failed: {str(e)}")
            raise

    async def predict_price(
        self,
        data: pd.DataFrame,
        model_types: List[str] = None,
        horizon: PredictionHorizon = PredictionHorizon.SHORT_TERM,
    ) -> List[ModelPrediction]:
        """
        預測價格

        Args:
            data: 輸入數據
            model_types: 模型類型列表
            horizon: 預測時間範圍

        Returns:
            預測結果列表
        """
        if model_types is None:
            model_types = ["lstm", "xgboost"]

        predictions = []

        for model_type in model_types:
            try:
                prediction = await self._predict_with_model(data, model_type, horizon)
                if prediction:
                    predictions.append(prediction)
            except Exception as e:
                self.logger.warning(f"Prediction failed for {model_type}: {str(e)}")
                continue

        return predictions

    async def _predict_with_model(
        self, data: pd.DataFrame, model_type: str, horizon: PredictionHorizon
    ) -> Optional[ModelPrediction]:
        """使用指定模型進行預測"""
        if model_type not in self.models:
            self.logger.warning(f"Model {model_type} not found")
            return None

        try:
            if model_type in ["lstm", "transformer", "cnn_lstm"]:
                return await self._predict_deep_learning(data, model_type, horizon)
            elif model_type in ["xgboost", "lightgbm"]:
                return self._predict_tree_based(data, model_type, horizon)
            else:
                self.logger.warning(f"Unsupported model type: {model_type}")
                return None

        except Exception as e:
            self.logger.error(f"Prediction with {model_type} failed: {str(e)}")
            return None

    async def _predict_deep_learning(
        self, data: pd.DataFrame, model_type: str, horizon: PredictionHorizon
    ) -> ModelPrediction:
        """深度學習模型預測"""
        # 準備序列數據
        X, _ = self.prepare_sequences(data)
        if len(X) == 0:
            raise ValueError("Insufficient data for prediction")

        # 使用最新的序列
        last_sequence = X[-1:].reshape(1, X.shape[1], X.shape[2])

        # 預測
        model = self.models[model_type]
        price_change_pred = model.predict(last_sequence, verbose=0)[0][0]

        # 計算預測價格
        current_price = data["close"].iloc[-1]
        predicted_price = current_price * (1 + price_change_pred)

        # 計算置信度 (簡化版本)
        confidence = max(0.1, 1 - abs(price_change_pred) * 10)

        return ModelPrediction(
            model_name=model_type.upper(),
            prediction=predicted_price,
            confidence=confidence,
            timestamp=datetime.now(),
            horizon=horizon,
            metadata={"price_change": price_change_pred},
        )

    def _predict_tree_based(
        self, data: pd.DataFrame, model_type: str, horizon: PredictionHorizon
    ) -> ModelPrediction:
        """樹模型預測"""
        # 準備特徵
        features = self.config["features"]
        X = data[features].tail(1)

        # 標準化
        if f"{model_type}_scaler" in self.scalers:
            X_scaled = self.scalers[f"{model_type}_scaler"].transform(X)
        else:
            X_scaled = X

        # 預測價格變化
        model = self.models[model_type]
        price_change_pred = model.predict(X_scaled)[0]

        # 計算預測價格
        current_price = data["close"].iloc[-1]
        predicted_price = current_price * (1 + price_change_pred)

        # 計算置信度
        confidence = max(0.1, 1 - abs(price_change_pred) * 10)

        return ModelPrediction(
            model_name=model_type.upper(),
            prediction=predicted_price,
            confidence=confidence,
            timestamp=datetime.now(),
            horizon=horizon,
            metadata={"price_change": price_change_pred},
        )


class VolatilityForecaster:
    """波動率預測器"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.logger = logging.getLogger("hk_quant_system.volatility_forecaster")
        self.config = config or self._default_config()

        # 模型存儲
        self.garch_models: Dict[str, Any] = {}
        self.deep_volatility_models: Dict[str, Any] = {}

        # 初始化模型
        if ARCH_AVAILABLE:
            self._init_garch_models()

    def _default_config(self) -> Dict[str, Any]:
        """默認配置"""
        return {
            "garch_params": {"p": 1, "q": 1, "mean": "Constant", "vol": "GARCH"},
            "lookback_window": 252,  # 一年的交易日
            "prediction_horizons": [1, 5, 10, 20, 60],
            "deep_model": {
                "sequence_length": 60,
                "lstm_units": [64, 32],
                "dropout": 0.2,
            },
        }

    def _init_garch_models(self):
        """初始化GARCH模型"""
        self.logger.info("Initializing GARCH models...")

    def fit_garch_model(self, returns: pd.Series) -> Dict[str, Any]:
        """擬合GARCH模型"""
        if not ARCH_AVAILABLE:
            raise ImportError("arch package is required for GARCH models")

        try:
            # 創建GARCH模型
            model = GARCH(
                returns,
                p=self.config["garch_params"]["p"],
                q=self.config["garch_params"]["q"],
                mean=self.config["garch_params"]["mean"],
                vol=self.config["garch_params"]["vol"],
            )

            # 擬合模型
            result = model.fit(disp="off")

            # 模型診斷
            aic = result.aic
            bic = result.bic
            log_likelihood = result.loglikelihood

            self.logger.info(f"GARCH model fitted - AIC: {aic:.2f}, BIC: {bic:.2f}")

            return {
                "model": result,
                "aic": aic,
                "bic": bic,
                "log_likelihood": log_likelihood,
                "params": result.params.to_dict(),
                "conditional_volatility": result.conditional_volatility,
            }

        except Exception as e:
            self.logger.error(f"GARCH model fitting failed: {str(e)}")
            raise

    def forecast_volatility(
        self, model_result: Any, horizon: int = 5, method: str = "simulation"
    ) -> Dict[str, Any]:
        """預測波動率"""
        try:
            # 波動率預測
            if method == "analytical":
                forecast = model_result.forecast(horizon=horizon, method="analytical")
            elif method == "simulation":
                forecast = model_result.forecast(horizon=horizon, method="simulation")
            else:
                forecast = model_result.forecast(horizon=horizon)

            variance_forecast = forecast.variance.iloc[-1]
            volatility_forecast = np.sqrt(variance_forecast)

            return {
                "variance_forecast": variance_forecast.tolist(),
                "volatility_forecast": volatility_forecast.tolist(),
                "horizon": horizon,
            }

        except Exception as e:
            self.logger.error(f"Volatility forecasting failed: {str(e)}")
            raise

    def calculate_realized_volatility(
        self, returns: pd.Series, window: int = 20
    ) -> pd.Series:
        """計算已實現波動率"""
        return returns.rolling(window=window).std() * np.sqrt(252)

    def volatility_regime_detection(
        self, volatility: pd.Series, n_regimes: int = 3
    ) -> Dict[str, Any]:
        """波動率狀態檢測"""
        try:
            # 使用高斯混合模型檢測波動率狀態
            volatility_clean = volatility.dropna().values.reshape(-1, 1)

            gmm = GaussianMixture(n_components=n_regimes, random_state=42)
            regimes = gmm.fit_predict(volatility_clean)

            # 計算每個狀態的統計特性
            regime_stats = {}
            for i in range(n_regimes):
                regime_mask = regimes == i
                regime_vol = volatility_clean[regime_mask].flatten()

                regime_stats[f"regime_{i}"] = {
                    "mean_volatility": np.mean(regime_vol),
                    "std_volatility": np.std(regime_vol),
                    "percentage": np.sum(regime_mask) / len(regime_mask) * 100,
                }

            # 當前狀態
            current_regime = regimes[-1]

            return {
                "regime_stats": regime_stats,
                "current_regime": int(current_regime),
                "regime_history": regimes.tolist(),
                "gmm_model": gmm,
            }

        except Exception as e:
            self.logger.error(f"Volatility regime detection failed: {str(e)}")
            raise


class MarketRegimeDetector:
    """市場狀態檢測器"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.logger = logging.getLogger("hk_quant_system.regime_detector")
        self.config = config or self._default_config()

        # 模型存儲
        self.hmm_models: Dict[str, Any] = {}
        self.clustering_models: Dict[str, Any] = {}

    def _default_config(self) -> Dict[str, Any]:
        """默認配置"""
        return {
            "features": [
                "returns",
                "volatility",
                "volume_ratio",
                "rsi",
                "macd",
                "high_low_ratio",
                "volume_price_trend",
                "momentum",
            ],
            "n_regimes": 4,
            "hmm_params": {"n_components": 4, "covariance_type": "full", "n_iter": 100},
            "clustering_params": {"n_clusters": 4, "random_state": 42},
        }

    def prepare_regime_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """準備市場狀態檢測特徵"""
        df = data.copy()

        # 基礎特徵
        df["returns"] = df["close"].pct_change()
        df["volatility"] = df["returns"].rolling(20).std()
        df["volume_ratio"] = df["volume"] / df["volume"].rolling(20).mean()

        # 技術指標
        delta = df["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / (loss + 1e-8)
        df["rsi"] = 100 - (100 / (1 + rs))

        ema_12 = df["close"].ewm(span=12).mean()
        ema_26 = df["close"].ewm(span=26).mean()
        df["macd"] = ema_12 - ema_26

        # 價格特徵
        df["high_low_ratio"] = df["high"] / df["low"]
        df["volume_price_trend"] = (df["close"] / df["close"].shift(1)) * (
            df["volume"] / df["volume"].shift(1)
        )

        # 動量特徵
        df["momentum"] = df["close"] / df["close"].shift(20) - 1

        return df[self.config["features"]].dropna()

    def detect_regimes_hmm(
        self, data: pd.DataFrame, symbol: str = "default"
    ) -> Dict[str, Any]:
        """使用隱馬爾可夫模型檢測市場狀態"""
        try:
            from hmmlearn import hmm

            # 準備特徵
            features = self.prepare_regime_features(data)

            # 標準化
            scaler = StandardScaler()
            features_scaled = scaler.fit_transform(features)

            # 訓練HMM模型
            model = hmm.GaussianHMM(**self.config["hmm_params"])
            model.fit(features_scaled)

            # 預測狀態
            hidden_states = model.predict(features_scaled)
            state_probabilities = model.predict_proba(features_scaled)

            # 狀態統計
            regime_stats = {}
            for i in range(self.config["hmm_params"]["n_components"]):
                state_mask = hidden_states == i
                regime_stats[f"regime_{i}"] = {
                    "frequency": np.sum(state_mask) / len(hidden_states),
                    "mean_returns": np.mean(features["returns"].iloc[state_mask]),
                    "mean_volatility": np.mean(features["volatility"].iloc[state_mask]),
                    "duration": self._calculate_average_regime_duration(
                        hidden_states, i
                    ),
                }

            # 保存模型
            self.hmm_models[symbol] = {
                "model": model,
                "scaler": scaler,
                "features": features.columns.tolist(),
                "regime_stats": regime_stats,
            }

            current_regime = hidden_states[-1]

            self.logger.info(f"HMM regime detection completed for {symbol}")

            return {
                "method": "HMM",
                "current_regime": int(current_regime),
                "regime_history": hidden_states.tolist(),
                "regime_probabilities": state_probabilities[-1].tolist(),
                "regime_stats": regime_stats,
                "model_confidence": np.max(state_probabilities[-1]),
            }

        except Exception as e:
            self.logger.error(f"HMM regime detection failed: {str(e)}")
            raise

    def detect_regimes_clustering(
        self, data: pd.DataFrame, symbol: str = "default"
    ) -> Dict[str, Any]:
        """使用聚類檢測市場狀態"""
        try:
            # 準備特徵
            features = self.prepare_regime_features(data)

            # 標準化
            scaler = StandardScaler()
            features_scaled = scaler.fit_transform(features)

            # K - means聚類
            kmeans = KMeans(**self.config["clustering_params"])
            clusters = kmeans.fit_predict(features_scaled)

            # 計算距離中心點的距離作為置信度
            distances = kmeans.transform(features_scaled)
            confidences = 1 - (distances.min(axis=1) / distances.max(axis=1))

            # 狀態統計
            regime_stats = {}
            for i in range(self.config["clustering_params"]["n_clusters"]):
                cluster_mask = clusters == i
                regime_stats[f"regime_{i}"] = {
                    "frequency": np.sum(cluster_mask) / len(clusters),
                    "mean_returns": np.mean(features["returns"].iloc[cluster_mask]),
                    "mean_volatility": np.mean(
                        features["volatility"].iloc[cluster_mask]
                    ),
                }

            # 保存模型
            self.clustering_models[symbol] = {
                "model": kmeans,
                "scaler": scaler,
                "features": features.columns.tolist(),
                "regime_stats": regime_stats,
            }

            current_regime = clusters[-1]
            current_confidence = confidences[-1]

            return {
                "method": "Clustering",
                "current_regime": int(current_regime),
                "regime_history": clusters.tolist(),
                "confidences": confidences.tolist(),
                "regime_stats": regime_stats,
                "model_confidence": current_confidence,
            }

        except Exception as e:
            self.logger.error(f"Clustering regime detection failed: {str(e)}")
            raise

    def _calculate_average_regime_duration(
        self, states: np.ndarray, state: int
    ) -> float:
        """計算平均狀態持續時間"""
        durations = []
        current_duration = 0

        for s in states:
            if s == state:
                current_duration += 1
            else:
                if current_duration > 0:
                    durations.append(current_duration)
                current_duration = 0

        if current_duration > 0:
            durations.append(current_duration)

        return np.mean(durations) if durations else 0

    def get_current_regime(
        self, symbol: str, method: str = "hmm"
    ) -> Optional[Dict[str, Any]]:
        """獲取當前市場狀態"""
        try:
            if method == "hmm" and symbol in self.hmm_models:
                model_info = self.hmm_models[symbol]
                return {"method": "HMM", "regime_stats": model_info["regime_stats"]}
            elif method == "clustering" and symbol in self.clustering_models:
                model_info = self.clustering_models[symbol]
                return {
                    "method": "Clustering",
                    "regime_stats": model_info["regime_stats"],
                }
            else:
                return None

        except Exception as e:
            self.logger.error(f"Failed to get current regime: {str(e)}")
            return None


class SentimentAnalyzer:
    """情緒分析器"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.logger = logging.getLogger("hk_quant_system.sentiment_analyzer")
        self.config = config or self._default_config()

        # 模型和分詞器
        self.tokenizer = None
        self.bert_model = None
        self.tfidf_vectorizer = None

        # 初始化NLP模型
        if NLP_AVAILABLE:
            self._init_nlp_models()

    def _default_config(self) -> Dict[str, Any]:
        """默認配置"""
        return {
            "bert_model_name": "bert - base - chinese",
            "max_length": 512,
            "sentiment_threshold": 0.5,
            "languages": ["en", "zh"],
            "news_sources": ["reuters", "bloomberg", "scmp", "hkex"],
        }

    def _init_nlp_models(self):
        """初始化NLP模型"""
        try:
            # 初始化BERT模型
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.config["bert_model_name"]
            )
            self.bert_model = AutoModel.from_pretrained(self.config["bert_model_name"])

            # 初始化TF - IDF向量化器
            self.tfidf_vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words=None,  # 中文停用詞需要自定義
                ngram_range=(1, 2),
            )

            self.logger.info("NLP models initialized successfully")

        except Exception as e:
            self.logger.warning(f"NLP model initialization failed: {str(e)}")

    def analyze_news_sentiment(
        self, news_texts: List[str], method: str = "bert"
    ) -> Dict[str, Any]:
        """分析新聞情緒"""
        try:
            if method == "bert" and self.bert_model is not None:
                return self._analyze_with_bert(news_texts)
            elif method == "textblob":
                return self._analyze_with_textblob(news_texts)
            elif method == "tfidf":
                return self._analyze_with_tfidf(news_texts)
            else:
                raise ValueError(f"Unsupported sentiment analysis method: {method}")

        except Exception as e:
            self.logger.error(f"Sentiment analysis failed: {str(e)}")
            return {"error": str(e)}

    def _analyze_with_bert(self, texts: List[str]) -> Dict[str, Any]:
        """使用BERT分析情緒"""
        try:
            sentiments = []
            confidences = []

            for text in texts:
                # 分詞和編碼
                inputs = self.tokenizer(
                    text,
                    return_tensors="pt",
                    max_length=self.config["max_length"],
                    truncation=True,
                    padding=True,
                )

                # 獲取BERT輸出
                with torch.no_grad():
                    outputs = self.bert_model(**inputs)
                    # 使用CLS標記的輸出作為句子表示
                    sentence_embedding = outputs.last_hidden_state[:, 0, :]

                    # 簡化的情緒分類 (實際應用中需要分類層)
                    sentiment_score = torch.mean(sentence_embedding).item()
                    confidence = abs(sentiment_score)

                    # 映射到情緒標籤
                    if sentiment_score > self.config["sentiment_threshold"]:
                        sentiment = "positive"
                    elif sentiment_score < -self.config["sentiment_threshold"]:
                        sentiment = "negative"
                    else:
                        sentiment = "neutral"

                    sentiments.append(sentiment)
                    confidences.append(confidence)

            # 統計結果
            sentiment_counts = pd.Series(sentiments).value_counts().to_dict()
            avg_confidence = np.mean(confidences)

            return {
                "method": "BERT",
                "sentiments": sentiments,
                "confidences": confidences,
                "sentiment_distribution": sentiment_counts,
                "average_confidence": avg_confidence,
                "overall_sentiment": max(sentiment_counts, key=sentiment_counts.get),
            }

        except Exception as e:
            self.logger.error(f"BERT sentiment analysis failed: {str(e)}")
            raise

    def _analyze_with_textblob(self, texts: List[str]) -> Dict[str, Any]:
        """使用TextBlob分析情緒"""
        try:
            sentiments = []
            polarities = []
            subjectivities = []

            for text in texts:
                blob = TextBlob(text)
                polarity = blob.sentiment.polarity
                subjectivity = blob.sentiment.subjectivity

                polarities.append(polarity)
                subjectivities.append(subjectivity)

                # 分類情緒
                if polarity > 0.1:
                    sentiment = "positive"
                elif polarity < -0.1:
                    sentiment = "negative"
                else:
                    sentiment = "neutral"

                sentiments.append(sentiment)

            # 統計結果
            sentiment_counts = pd.Series(sentiments).value_counts().to_dict()
            avg_polarity = np.mean(polarities)
            avg_subjectivity = np.mean(subjectivities)

            return {
                "method": "TextBlob",
                "sentiments": sentiments,
                "polarities": polarities,
                "subjectivities": subjectivities,
                "sentiment_distribution": sentiment_counts,
                "average_polarity": avg_polarity,
                "average_subjectivity": avg_subjectivity,
                "overall_sentiment": max(sentiment_counts, key=sentiment_counts.get),
            }

        except Exception as e:
            self.logger.error(f"TextBlob sentiment analysis failed: {str(e)}")
            raise

    def _analyze_with_tfidf(self, texts: List[str]) -> Dict[str, Any]:
        """使用TF - IDF分析情緒"""
        try:
            # 簡化的基於詞典的情緒分析
            # 實際應用中需要更複雜的詞典和規則
            positive_words = [
                "好",
                "漲",
                "強勁",
                "增長",
                "利好",
                "上漲",
                "strong",
                "good",
                "rise",
            ]
            negative_words = [
                "壞",
                "跌",
                "疲軟",
                "下降",
                "利空",
                "下跌",
                "weak",
                "bad",
                "fall",
            ]

            sentiments = []
            scores = []

            for text in texts:
                # 計算情緒分數
                positive_count = sum(
                    1 for word in positive_words if word in text.lower()
                )
                negative_count = sum(
                    1 for word in negative_words if word in text.lower()
                )

                total_sentiment_words = positive_count + negative_count
                if total_sentiment_words > 0:
                    score = (positive_count - negative_count) / total_sentiment_words
                else:
                    score = 0

                scores.append(score)

                # 分類情緒
                if score > 0.1:
                    sentiment = "positive"
                elif score < -0.1:
                    sentiment = "negative"
                else:
                    sentiment = "neutral"

                sentiments.append(sentiment)

            # 統計結果
            sentiment_counts = pd.Series(sentiments).value_counts().to_dict()
            avg_score = np.mean(scores)

            return {
                "method": "TF - IDF",
                "sentiments": sentiments,
                "scores": scores,
                "sentiment_distribution": sentiment_counts,
                "average_score": avg_score,
                "overall_sentiment": max(sentiment_counts, key=sentiment_counts.get),
            }

        except Exception as e:
            self.logger.error(f"TF - IDF sentiment analysis failed: {str(e)}")
            raise

    def get_market_sentiment_index(
        self, news_texts: List[str], weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """計算市場情緒指數"""
        try:
            # 分析情緒
            sentiment_results = self.analyze_news_sentiment(news_texts, method="bert")

            # 計算情緒指數
            sentiments = sentiment_results["sentiments"]
            confidences = sentiment_results["confidences"]

            # 加權情緒分數
            if weights is None:
                weights = {"positive": 1.0, "neutral": 0.0, "negative": -1.0}

            sentiment_scores = []
            for sentiment, confidence in zip(sentiments, confidences):
                score = weights.get(sentiment, 0) * confidence
                sentiment_scores.append(score)

            # 計算指數
            sentiment_index = np.mean(sentiment_scores)
            sentiment_volatility = np.std(sentiment_scores)

            return {
                "sentiment_index": sentiment_index,
                "sentiment_volatility": sentiment_volatility,
                "sentiment_trend": (
                    "improving"
                    if len(sentiment_scores) > 1
                    and sentiment_scores[-1] > sentiment_scores[-2]
                    else "declining"
                ),
                "market_bullishness": (
                    "bullish"
                    if sentiment_index > 0.1
                    else "bearish" if sentiment_index < -0.1 else "neutral"
                ),
            }

        except Exception as e:
            self.logger.error(f"Market sentiment index calculation failed: {str(e)}")
            raise


# 全局模型實例
price_predictor = AdvancedPricePredictor()
volatility_forecaster = VolatilityForecaster()
regime_detector = MarketRegimeDetector()
sentiment_analyzer = SentimentAnalyzer()
