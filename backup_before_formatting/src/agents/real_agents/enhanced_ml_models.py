"""
增強型機器學習模型 - 真實AI模型實現

包含多種專業的量化交易AI模型
"""

import asyncio
import json
import logging
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import (
    GradientBoostingRegressor,
    RandomForestClassifier,
    RandomForestRegressor,
)
from sklearn.linear_model import Lasso, LinearRegression, Ridge
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.neural_network import MLPClassifier, MLPRegressor
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from sklearn.svm import SVC, SVR

try:
    import xgboost as xgb
except ImportError:
    xgb = None

try:
    import lightgbm as lgb
except ImportError:
    lgb = None

from .ml_integration import FeatureConfig, ModelPerformance, ModelType


class TechnicalIndicatorEngine:
    """技術指標計算引擎 - 優化版本"""

    def __init__(self):
        self.logger = logging.getLogger("hk_quant_system.technical_indicators")
        # 緩存已計算的指標
        self._indicator_cache = {}
        self._cache_size_limit = 1000

    def _get_cache_key(self, prices: pd.Series, indicator: str, **params) -> str:
        """生成緩存鍵"""
        return f"{indicator}_{hash(prices.iloc[-10:].tobytes())}_{params}"

    def _clean_cache(self):
        """清理緩存"""
        if len(self._indicator_cache) > self._cache_size_limit:
            # 保留最近的一半
            items = list(self._indicator_cache.items())
            self._indicator_cache = dict(items[-self._cache_size_limit // 2 :])

    def calculate_sma(self, prices: pd.Series, period: int) -> pd.Series:
        """簡單移動平均線 - 優化版本"""
        cache_key = self._get_cache_key(prices, "sma", period=period)
        if cache_key in self._indicator_cache:
            return self._indicator_cache[cache_key]

        result = prices.rolling(window=period, min_periods=1).mean()
        self._indicator_cache[cache_key] = result
        self._clean_cache()
        return result

    def calculate_ema(self, prices: pd.Series, period: int) -> pd.Series:
        """指數移動平均線 - 優化版本"""
        cache_key = self._get_cache_key(prices, "ema", period=period)
        if cache_key in self._indicator_cache:
            return self._indicator_cache[cache_key]

        result = prices.ewm(span=period, min_periods=1).mean()
        self._indicator_cache[cache_key] = result
        self._clean_cache()
        return result

    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """相對強弱指數 - 優化版本"""
        cache_key = self._get_cache_key(prices, "rsi", period=period)
        if cache_key in self._indicator_cache:
            return self._indicator_cache[cache_key]

        # 使用向量化計算提高性能
        delta = prices.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        # 使用指數移動平均提高計算效率
        avg_gain = gain.ewm(alpha=1 / period, min_periods=period).mean()
        avg_loss = loss.ewm(alpha=1 / period, min_periods=period).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        result = rsi.fillna(50)

        self._indicator_cache[cache_key] = result
        self._clean_cache()
        return result

    def calculate_macd(
        self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """MACD指標 - 優化版本"""
        cache_key = self._get_cache_key(
            prices, "macd", fast=fast, slow=slow, signal=signal
        )
        if cache_key in self._indicator_cache:
            return self._indicator_cache[cache_key]

        # 並行計算EMA
        ema_fast = prices.ewm(span=fast, min_periods=1).mean()
        ema_slow = prices.ewm(span=slow, min_periods=1).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, min_periods=1).mean()
        histogram = macd_line - signal_line

        result = (macd_line, signal_line, histogram)
        self._indicator_cache[cache_key] = result
        self._clean_cache()
        return result

    def calculate_bollinger_bands(
        self, prices: pd.Series, period: int = 20, std_dev: float = 2.0
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """布林帶 - 優化版本"""
        cache_key = self._get_cache_key(prices, "bb", period=period, std_dev=std_dev)
        if cache_key in self._indicator_cache:
            return self._indicator_cache[cache_key]

        # 使用rolling計算提高效率
        rolling_stats = prices.rolling(window=period, min_periods=1)
        sma = rolling_stats.mean()
        std = rolling_stats.std()

        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)

        result = (upper_band, sma, lower_band)
        self._indicator_cache[cache_key] = result
        self._clean_cache()
        return result

    def calculate_stochastic(
        self,
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        k_period: int = 14,
        d_period: int = 3,
    ) -> Tuple[pd.Series, pd.Series]:
        """隨機指標 - 優化版本"""
        cache_key = self._get_cache_key(
            close, "stoch", k_period=k_period, d_period=d_period
        )
        if cache_key in self._indicator_cache:
            return self._indicator_cache[cache_key]

        # 向量化計算
        lowest_low = low.rolling(window=k_period, min_periods=1).min()
        highest_high = high.rolling(window=k_period, min_periods=1).max()

        # 避免除零錯誤
        denominator = highest_high - lowest_low
        denominator = denominator.replace(0, np.nan)

        k_percent = 100 * ((close - lowest_low) / denominator)
        d_percent = k_percent.rolling(window=d_period, min_periods=1).mean()

        result = (k_percent.fillna(50), d_percent.fillna(50))
        self._indicator_cache[cache_key] = result
        self._clean_cache()
        return result

    def calculate_atr(
        self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14
    ) -> pd.Series:
        """平均真實範圍 - 優化版本"""
        cache_key = self._get_cache_key(close, "atr", period=period)
        if cache_key in self._indicator_cache:
            return self._indicator_cache[cache_key]

        # 向量化計算TR
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())

        # 使用numpy.maximum提高性能
        tr = np.maximum(tr1, np.maximum(tr2, tr3))
        atr = pd.Series(tr).rolling(window=period, min_periods=1).mean()

        result = atr.fillna(0)
        self._indicator_cache[cache_key] = result
        self._clean_cache()
        return result

    def calculate_adx(
        self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14
    ) -> pd.Series:
        """平均方向指數 - 優化版本"""
        cache_key = self._get_cache_key(close, "adx", period=period)
        if cache_key in self._indicator_cache:
            return self._indicator_cache[cache_key]

        # 使用緩存的ATR
        tr = self.calculate_atr(high, low, close, period)

        # 向量化計算DM
        plus_dm = high.diff()
        minus_dm = low.diff()

        # 向量化條件判斷
        plus_dm = np.where((plus_dm > minus_dm) & (plus_dm > 0), plus_dm, 0)
        minus_dm = np.where((minus_dm > plus_dm) & (minus_dm > 0), minus_dm, 0)

        plus_dm = pd.Series(plus_dm, index=high.index)
        minus_dm = pd.Series(minus_dm, index=high.index)

        plus_di = 100 * (plus_dm.rolling(window=period, min_periods=1).mean() / tr)
        minus_di = 100 * (minus_dm.rolling(window=period, min_periods=1).mean() / tr)

        # 避免除零錯誤
        denominator = plus_di + minus_di
        denominator = denominator.replace(0, np.nan)

        dx = 100 * abs(plus_di - minus_di) / denominator
        adx = dx.rolling(window=period, min_periods=1).mean()

        result = adx.fillna(0)
        self._indicator_cache[cache_key] = result
        self._clean_cache()
        return result


class FeatureEngineer:
    """特徵工程器"""

    def __init__(self):
        self.logger = logging.getLogger("hk_quant_system.feature_engineer")
        self.technical_engine = TechnicalIndicatorEngine()

    def create_price_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """創建價格相關特徵"""
        features = df.copy()

        # 價格變化
        features["price_change"] = df["close"].pct_change()
        features["price_change_abs"] = abs(features["price_change"])

        # 價格比率
        features["high_low_ratio"] = df["high"] / df["low"]
        features["close_open_ratio"] = df["close"] / df["open"]
        features["high_close_ratio"] = df["high"] / df["close"]
        features["low_close_ratio"] = df["low"] / df["close"]

        # 價格位置
        features["close_position"] = (df["close"] - df["low"]) / (
            df["high"] - df["low"]
        )

        # 價格波動
        features["price_range"] = df["high"] - df["low"]
        features["price_range_ratio"] = features["price_range"] / df["close"]

        return features

    def create_volume_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """創建成交量相關特徵"""
        features = df.copy()

        # 成交量變化
        features["volume_change"] = df["volume"].pct_change()
        features["volume_change_abs"] = abs(features["volume_change"])

        # 成交量移動平均
        features["volume_sma_5"] = df["volume"].rolling(window=5).mean()
        features["volume_sma_20"] = df["volume"].rolling(window=20).mean()

        # 成交量比率
        features["volume_ratio_5"] = df["volume"] / features["volume_sma_5"]
        features["volume_ratio_20"] = df["volume"] / features["volume_sma_20"]

        # 價量關係
        features["price_volume"] = df["close"] * df["volume"]
        features["price_volume_change"] = features["price_volume"].pct_change()

        return features

    def create_technical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """創建技術指標特徵"""
        features = df.copy()

        # 移動平均線
        for period in [5, 10, 20, 50]:
            features[f"sma_{period}"] = self.technical_engine.calculate_sma(
                df["close"], period
            )
            features[f"ema_{period}"] = self.technical_engine.calculate_ema(
                df["close"], period
            )

        # RSI
        features["rsi"] = self.technical_engine.calculate_rsi(df["close"])
        features["rsi_oversold"] = (features["rsi"] < 30).astype(int)
        features["rsi_overbought"] = (features["rsi"] > 70).astype(int)

        # MACD
        macd_line, signal_line, histogram = self.technical_engine.calculate_macd(
            df["close"]
        )
        features["macd"] = macd_line
        features["macd_signal"] = signal_line
        features["macd_histogram"] = histogram
        features["macd_bullish"] = (macd_line > signal_line).astype(int)

        # 布林帶
        bb_upper, bb_middle, bb_lower = self.technical_engine.calculate_bollinger_bands(
            df["close"]
        )
        features["bb_upper"] = bb_upper
        features["bb_middle"] = bb_middle
        features["bb_lower"] = bb_lower
        features["bb_position"] = (df["close"] - bb_lower) / (bb_upper - bb_lower)
        features["bb_squeeze"] = ((bb_upper - bb_lower) / bb_middle < 0.1).astype(int)

        # 隨機指標
        k_percent, d_percent = self.technical_engine.calculate_stochastic(
            df["high"], df["low"], df["close"]
        )
        features["stoch_k"] = k_percent
        features["stoch_d"] = d_percent
        features["stoch_oversold"] = (k_percent < 20).astype(int)
        features["stoch_overbought"] = (k_percent > 80).astype(int)

        # ATR
        features["atr"] = self.technical_engine.calculate_atr(
            df["high"], df["low"], df["close"]
        )
        features["atr_ratio"] = features["atr"] / df["close"]

        # ADX
        features["adx"] = self.technical_engine.calculate_adx(
            df["high"], df["low"], df["close"]
        )
        features["adx_trending"] = (features["adx"] > 25).astype(int)

        return features

    def create_lag_features(
        self, df: pd.DataFrame, lags: List[int] = [1, 2, 3, 5, 10]
    ) -> pd.DataFrame:
        """創建滯後特徵"""
        features = df.copy()

        for lag in lags:
            features[f"close_lag_{lag}"] = df["close"].shift(lag)
            features[f"volume_lag_{lag}"] = df["volume"].shift(lag)
            features[f"price_change_lag_{lag}"] = df["close"].pct_change().shift(lag)

        return features

    def create_time_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """創建時間特徵"""
        features = df.copy()

        if "timestamp" in df.columns:
            timestamp = pd.to_datetime(df["timestamp"])
            features["hour"] = timestamp.dt.hour
            features["day_of_week"] = timestamp.dt.dayofweek
            features["day_of_month"] = timestamp.dt.day
            features["month"] = timestamp.dt.month
            features["quarter"] = timestamp.dt.quarter

            # 時間週期性特徵
            features["hour_sin"] = np.sin(2 * np.pi * features["hour"] / 24)
            features["hour_cos"] = np.cos(2 * np.pi * features["hour"] / 24)
            features["day_sin"] = np.sin(2 * np.pi * features["day_of_week"] / 7)
            features["day_cos"] = np.cos(2 * np.pi * features["day_of_week"] / 7)

        return features

    def create_volatility_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """創建波動率特徵"""
        features = df.copy()

        # 不同週期的波動率
        for period in [5, 10, 20]:
            features[f"volatility_{period}"] = df["close"].rolling(window=period).std()
            features[f"volatility_ratio_{period}"] = (
                features[f"volatility_{period}"] / df["close"]
            )

        # 波動率變化
        features["volatility_change"] = features["volatility_20"].pct_change()

        # 高波動率標識
        features["high_volatility"] = (
            features["volatility_20"]
            > features["volatility_20"].rolling(window=50).quantile(0.8)
        ).astype(int)

        return features

    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """綜合特徵工程"""
        try:
            self.logger.info("Starting feature engineering...")

            # 確保必要的列存在
            required_columns = ["open", "high", "low", "close", "volume"]
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                self.logger.error(f"Missing required columns: {missing_columns}")
                return df

            # 創建各種特徵
            features = self.create_price_features(df)
            features = self.create_volume_features(features)
            features = self.create_technical_features(features)
            features = self.create_lag_features(features)
            features = self.create_time_features(features)
            features = self.create_volatility_features(features)

            # 填充缺失值
            features = features.fillna(method="ffill").fillna(method="bfill")

            # 移除無窮大值
            features = features.replace([np.inf, -np.inf], np.nan)
            features = features.fillna(0)

            self.logger.info(
                f"Feature engineering completed. Created {len(features.columns)} features"
            )
            return features

        except Exception as e:
            self.logger.error(f"Error in feature engineering: {e}")
            return df


class EnhancedMLModels:
    """增強型機器學習模型集合"""

    def __init__(self):
        self.logger = logging.getLogger("hk_quant_system.enhanced_ml")
        self.feature_engineer = FeatureEngineer()
        self.models: Dict[str, Any] = {}
        self.scalers: Dict[str, Any] = {}
        self.model_performance: Dict[str, ModelPerformance] = {}

    async def create_price_prediction_model(
        self, data: pd.DataFrame, target_column: str = "future_return"
    ) -> Optional[Any]:
        """創建價格預測模型"""
        try:
            self.logger.info("Creating price prediction model...")

            # 特徵工程
            features_df = self.feature_engineer.engineer_features(data)

            # 創建目標變量（未來收益率）
            if target_column not in features_df.columns:
                features_df[target_column] = (
                    features_df["close"].shift(-1) / features_df["close"] - 1
                )

            # 準備特徵和目標
            feature_columns = [
                col
                for col in features_df.columns
                if col
                not in [
                    "timestamp",
                    target_column,
                    "open",
                    "high",
                    "low",
                    "close",
                    "volume",
                ]
            ]
            X = features_df[feature_columns].dropna()
            y = features_df[target_column].loc[X.index]

            if len(X) < 100:
                self.logger.warning("Insufficient data for model training")
                return None

            # 分割數據
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )

            # 特徵縮放
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)

            # 訓練多個模型並選擇最佳
            models = {
                "random_forest": RandomForestRegressor(
                    n_estimators=100, random_state=42
                ),
                "gradient_boosting": GradientBoostingRegressor(
                    n_estimators=100, random_state=42
                ),
                "xgboost": (
                    xgb.XGBRegressor(n_estimators=100, random_state=42) if xgb else None
                ),
                "lightgbm": (
                    lgb.LGBMRegressor(n_estimators=100, random_state=42, verbose=-1)
                    if lgb
                    else None
                ),
                "neural_network": MLPRegressor(
                    hidden_layer_sizes=(100, 50), random_state=42, max_iter=500
                ),
            }

            best_model = None
            best_score = -np.inf
            best_model_name = None

            for model_name, model in models.items():
                try:
                    if (
                        model is None
                    ):  # Skip if model is None (e.g., xgboost / lgb not available)
                        continue

                    # 訓練模型
                    if model_name in ["neural_network"]:
                        model.fit(X_train_scaled, y_train)
                        y_pred = model.predict(X_test_scaled)
                    else:
                        model.fit(X_train, y_train)
                        y_pred = model.predict(X_test)

                    # 評估模型
                    score = r2_score(y_test, y_pred)
                    self.logger.info(f"{model_name} R² score: {score:.4f}")

                    if score > best_score:
                        best_score = score
                        best_model = model
                        best_model_name = model_name

                except Exception as e:
                    self.logger.error(f"Error training {model_name}: {e}")
                    continue

            if best_model is None:
                self.logger.error("No model could be trained successfully")
                return None

            # 保存最佳模型
            self.models["price_prediction"] = best_model
            self.scalers["price_prediction"] = scaler

            # 計算性能指標
            if best_model_name in ["neural_network"]:
                y_pred = best_model.predict(X_test_scaled)
            else:
                y_pred = best_model.predict(X_test)

            performance = ModelPerformance(
                model_name="price_prediction",
                model_type=ModelType.REGRESSION,
                mse=mean_squared_error(y_test, y_pred),
                mae=mean_absolute_error(y_test, y_pred),
                r2_score=r2_score(y_test, y_pred),
                training_time=0.0,  # 實際訓練時間
                last_trained=datetime.now(),
                training_samples=len(X_train),
                feature_count=len(feature_columns),
                model_size_mb=0.0,  # 實際模型大小
            )

            self.model_performance["price_prediction"] = performance

            self.logger.info(
                f"Price prediction model created successfully. Best model: {best_model_name}, R²: {best_score:.4f}"
            )
            return best_model

        except Exception as e:
            self.logger.error(f"Error creating price prediction model: {e}")
            return None

    async def create_signal_classification_model(
        self, data: pd.DataFrame
    ) -> Optional[Any]:
        """創建信號分類模型"""
        try:
            self.logger.info("Creating signal classification model...")

            # 特徵工程
            features_df = self.feature_engineer.engineer_features(data)

            # 創建目標變量（買賣信號）
            future_return = features_df["close"].shift(-1) / features_df["close"] - 1
            features_df["signal"] = 0  # hold
            features_df.loc[future_return > 0.02, "signal"] = 1  # buy
            features_df.loc[future_return < -0.02, "signal"] = -1  # sell

            # 準備特徵和目標
            feature_columns = [
                col
                for col in features_df.columns
                if col
                not in ["timestamp", "signal", "open", "high", "low", "close", "volume"]
            ]
            X = features_df[feature_columns].dropna()
            y = features_df["signal"].loc[X.index]

            if len(X) < 100:
                self.logger.warning("Insufficient data for model training")
                return None

            # 分割數據
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )

            # 特徵縮放
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)

            # 訓練多個模型並選擇最佳
            models = {
                "random_forest": RandomForestClassifier(
                    n_estimators=100, random_state=42
                ),
                "gradient_boosting": GradientBoostingRegressor(
                    n_estimators=100, random_state=42
                ),
                "xgboost": (
                    xgb.XGBClassifier(n_estimators=100, random_state=42)
                    if xgb
                    else None
                ),
                "lightgbm": (
                    lgb.LGBMClassifier(n_estimators=100, random_state=42, verbose=-1)
                    if lgb
                    else None
                ),
                "neural_network": MLPClassifier(
                    hidden_layer_sizes=(100, 50), random_state=42, max_iter=500
                ),
            }

            best_model = None
            best_score = -np.inf
            best_model_name = None

            for model_name, model in models.items():
                try:
                    if (
                        model is None
                    ):  # Skip if model is None (e.g., xgboost / lgb not available)
                        continue

                    # 訓練模型
                    if model_name in ["neural_network"]:
                        model.fit(X_train_scaled, y_train)
                        y_pred = model.predict(X_test_scaled)
                    else:
                        model.fit(X_train, y_train)
                        y_pred = model.predict(X_test)

                    # 評估模型
                    score = accuracy_score(y_test, y_pred)
                    self.logger.info(f"{model_name} accuracy: {score:.4f}")

                    if score > best_score:
                        best_score = score
                        best_model = model
                        best_model_name = model_name

                except Exception as e:
                    self.logger.error(f"Error training {model_name}: {e}")
                    continue

            if best_model is None:
                self.logger.error("No model could be trained successfully")
                return None

            # 保存最佳模型
            self.models["signal_classification"] = best_model
            self.scalers["signal_classification"] = scaler

            # 計算性能指標
            if best_model_name in ["neural_network"]:
                y_pred = best_model.predict(X_test_scaled)
            else:
                y_pred = best_model.predict(X_test)

            performance = ModelPerformance(
                model_name="signal_classification",
                model_type=ModelType.CLASSIFICATION,
                accuracy=accuracy_score(y_test, y_pred),
                training_time=0.0,
                last_trained=datetime.now(),
                training_samples=len(X_train),
                feature_count=len(feature_columns),
                model_size_mb=0.0,
            )

            self.model_performance["signal_classification"] = performance

            self.logger.info(
                f"Signal classification model created successfully. Best model: {best_model_name}, Accuracy: {best_score:.4f}"
            )
            return best_model

        except Exception as e:
            self.logger.error(f"Error creating signal classification model: {e}")
            return None

    async def create_volatility_prediction_model(
        self, data: pd.DataFrame
    ) -> Optional[Any]:
        """創建波動率預測模型"""
        try:
            self.logger.info("Creating volatility prediction model...")

            # 特徵工程
            features_df = self.feature_engineer.engineer_features(data)

            # 創建目標變量（未來波動率）
            future_volatility = features_df["close"].rolling(window=5).std().shift(-5)
            features_df["future_volatility"] = future_volatility

            # 準備特徵和目標
            feature_columns = [
                col
                for col in features_df.columns
                if col
                not in [
                    "timestamp",
                    "future_volatility",
                    "open",
                    "high",
                    "low",
                    "close",
                    "volume",
                ]
            ]
            X = features_df[feature_columns].dropna()
            y = features_df["future_volatility"].loc[X.index]

            if len(X) < 100:
                self.logger.warning("Insufficient data for model training")
                return None

            # 分割數據
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )

            # 特徵縮放
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)

            # 訓練模型
            model = RandomForestRegressor(n_estimators=100, random_state=42)
            model.fit(X_train, y_train)

            # 預測和評估
            y_pred = model.predict(X_test)
            score = r2_score(y_test, y_pred)

            # 保存模型
            self.models["volatility_prediction"] = model
            self.scalers["volatility_prediction"] = scaler

            # 計算性能指標
            performance = ModelPerformance(
                model_name="volatility_prediction",
                model_type=ModelType.REGRESSION,
                mse=mean_squared_error(y_test, y_pred),
                mae=mean_absolute_error(y_test, y_pred),
                r2_score=r2_score(y_test, y_pred),
                training_time=0.0,
                last_trained=datetime.now(),
                training_samples=len(X_train),
                feature_count=len(feature_columns),
                model_size_mb=0.0,
            )

            self.model_performance["volatility_prediction"] = performance

            self.logger.info(
                f"Volatility prediction model created successfully. R²: {score:.4f}"
            )
            return model

        except Exception as e:
            self.logger.error(f"Error creating volatility prediction model: {e}")
            return None

    async def predict_price_direction(self, data: pd.DataFrame) -> Dict[str, Any]:
        """預測價格方向"""
        try:
            if "signal_classification" not in self.models:
                self.logger.warning("Signal classification model not available")
                return {"prediction": 0, "confidence": 0.0}

            # 特徵工程
            features_df = self.feature_engineer.engineer_features(data)

            # 準備特徵
            feature_columns = [
                col
                for col in features_df.columns
                if col
                not in ["timestamp", "signal", "open", "high", "low", "close", "volume"]
            ]
            X = features_df[feature_columns].iloc[-1:].fillna(0)

            # 預測
            model = self.models["signal_classification"]
            scaler = self.scalers.get("signal_classification")

            if scaler:
                X_scaled = scaler.transform(X)
                prediction = model.predict(X_scaled)[0]
                confidence = max(model.predict_proba(X_scaled)[0])
            else:
                prediction = model.predict(X)[0]
                confidence = max(model.predict_proba(X)[0])

            return {
                "prediction": int(prediction),
                "confidence": float(confidence),
                "signal": (
                    "buy" if prediction == 1 else "sell" if prediction == -1 else "hold"
                ),
            }

        except Exception as e:
            self.logger.error(f"Error predicting price direction: {e}")
            return {"prediction": 0, "confidence": 0.0}

    async def predict_future_return(self, data: pd.DataFrame) -> Dict[str, Any]:
        """預測未來收益率"""
        try:
            if "price_prediction" not in self.models:
                self.logger.warning("Price prediction model not available")
                return {"prediction": 0.0, "confidence": 0.0}

            # 特徵工程
            features_df = self.feature_engineer.engineer_features(data)

            # 準備特徵
            feature_columns = [
                col
                for col in features_df.columns
                if col
                not in [
                    "timestamp",
                    "future_return",
                    "open",
                    "high",
                    "low",
                    "close",
                    "volume",
                ]
            ]
            X = features_df[feature_columns].iloc[-1:].fillna(0)

            # 預測
            model = self.models["price_prediction"]
            scaler = self.scalers.get("price_prediction")

            if scaler:
                X_scaled = scaler.transform(X)
                prediction = model.predict(X_scaled)[0]
            else:
                prediction = model.predict(X)[0]

            # 計算置信度（基於預測值的絕對值）
            confidence = min(abs(prediction) * 10, 1.0)

            return {
                "prediction": float(prediction),
                "confidence": float(confidence),
                "direction": "bullish" if prediction > 0 else "bearish",
            }

        except Exception as e:
            self.logger.error(f"Error predicting future return: {e}")
            return {"prediction": 0.0, "confidence": 0.0}

    async def save_models(self, filepath: str) -> bool:
        """保存模型"""
        try:
            models_dir = Path(filepath)
            models_dir.mkdir(parents=True, exist_ok=True)

            # 保存模型
            for model_name, model in self.models.items():
                model_file = models_dir / f"{model_name}_model.pkl"
                with open(model_file, "wb") as f:
                    pickle.dump(model, f)

            # 保存縮放器
            for scaler_name, scaler in self.scalers.items():
                scaler_file = models_dir / f"{scaler_name}_scaler.pkl"
                with open(scaler_file, "wb") as f:
                    pickle.dump(scaler, f)

            # 保存性能指標
            performance_file = models_dir / "model_performance.json"
            performance_data = {}
            for name, perf in self.model_performance.items():
                performance_data[name] = perf.dict()

            with open(performance_file, "w") as f:
                json.dump(performance_data, f, indent=2, default=str)

            self.logger.info(f"Models saved to {filepath}")
            return True

        except Exception as e:
            self.logger.error(f"Error saving models: {e}")
            return False

    async def load_models(self, filepath: str) -> bool:
        """加載模型"""
        try:
            models_dir = Path(filepath)
            if not models_dir.exists():
                self.logger.warning(f"Models directory not found: {filepath}")
                return False

            # 加載模型
            for model_file in models_dir.glob("*_model.pkl"):
                model_name = model_file.stem.replace("_model", "")
                with open(model_file, "rb") as f:
                    self.models[model_name] = pickle.load(f)

            # 加載縮放器
            for scaler_file in models_dir.glob("*_scaler.pkl"):
                scaler_name = scaler_file.stem.replace("_scaler", "")
                with open(scaler_file, "rb") as f:
                    self.scalers[scaler_name] = pickle.load(f)

            # 加載性能指標
            performance_file = models_dir / "model_performance.json"
            if performance_file.exists():
                with open(performance_file, "r") as f:
                    performance_data = json.load(f)
                    for name, perf_data in performance_data.items():
                        self.model_performance[name] = ModelPerformance(**perf_data)

            self.logger.info(f"Models loaded from {filepath}")
            return True

        except Exception as e:
            self.logger.error(f"Error loading models: {e}")
            return False

    def get_model_info(self) -> Dict[str, Any]:
        """獲取模型信息"""
        return {
            "available_models": list(self.models.keys()),
            "available_scalers": list(self.scalers.keys()),
            "model_performance": {
                name: perf.dict() for name, perf in self.model_performance.items()
            },
        }
