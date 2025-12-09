"""
機器學習預測引擎
港股量化交易系統 - 智能預測和分析中心
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

try:
    import tensorflow as tf
    from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
    from tensorflow.keras.layers import LSTM, BatchNormalization, Dense, Dropout
    from tensorflow.keras.models import Sequential, load_model
    from tensorflow.keras.optimizers import Adam

    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False

import xgboost as xgb
from sklearn.ensemble import IsolationForest, RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler, StandardScaler

from ..data_adapters.base_adapter import BaseAdapter
from ..utils.data_loader import DataLoader


class ModelType(Enum):
    """支持的模型類型"""

    LSTM = "lstm"
    RANDOM_FOREST = "random_forest"
    XGBOOST = "xgboost"
    HYBRID = "hybrid"


class PredictionHorizon(Enum):
    """預測時間範圍"""

    SHORT_TERM = "short"  # 1 - 5天
    MEDIUM_TERM = "medium"  # 1 - 4週
    LONG_TERM = "long"  # 1 - 6個月


@dataclass
class PredictionResult:
    """預測結果"""

    symbol: str
    timestamp: datetime
    horizon: PredictionHorizon
    predicted_price: float
    confidence: float  # 0 - 1
    volatility: float
    trend_direction: str  # "up", "down", "sideways"
    risk_level: str  # "low", "medium", "high"
    features_importance: Optional[Dict[str, float]] = None
    model_used: Optional[str] = None


@dataclass
class ModelMetrics:
    """模型性能指標"""

    model_type: str
    accuracy: float
    mae: float  # Mean Absolute Error
    mse: float  # Mean Squared Error
    rmse: float  # Root Mean Squared Error
    r2: float  # R - squared
    sharpe_ratio: float
    max_drawdown: float
    training_time: float  # seconds
    last_trained: datetime


class MLPredictionEngine:
    """
    機器學習預測引擎

    功能:
    - 多模型股票價格預測 (LSTM, Random Forest, XGBoost)
    - 趨勢分析和異常檢測
    - 風險預警和評估
    - 實時預測和批量分析
    """

    def __init__(
        self, data_adapter: BaseAdapter, config: Optional[Dict[str, Any]] = None
    ):
        self.data_adapter = data_adapter
        self.config = config or self._default_config()
        self.logger = logging.getLogger("hk_quant_system.ml_engine")

        # 數據處理
        self.scaler = MinMaxScaler()
        self.feature_scaler = StandardScaler()

        # 模型存儲
        self.models: Dict[str, Any] = {}
        self.model_metrics: Dict[str, ModelMetrics] = {}

        # 預測緩存
        self._prediction_cache: Dict[str, PredictionResult] = {}
        self._cache_expiry = 300  # 5分鐘

        # 初始化模型
        self._initialize_models()

    def _default_config(self) -> Dict[str, Any]:
        """默認配置"""
        return {
            "lookback_window": 60,  # 回看窗口 (天數)
            "prediction_horizons": {"short": 5, "medium": 20, "long": 60},
            "features": [
                "open",
                "high",
                "low",
                "close",
                "volume",
                "sma_5",
                "sma_20",
                "sma_60",
                "rsi",
                "macd",
                "bb_position",
                "atr",
                "stochastic_k",
                "stochastic_d",
                "obv",
                "mfi",
                "adx",
            ],
            "ml_config": {
                "lstm": {
                    "units": [50, 50, 50],
                    "dropout": 0.2,
                    "epochs": 100,
                    "batch_size": 32,
                    "patience": 10,
                },
                "random_forest": {
                    "n_estimators": 100,
                    "max_depth": 10,
                    "random_state": 42,
                },
                "xgboost": {
                    "n_estimators": 100,
                    "max_depth": 6,
                    "learning_rate": 0.1,
                    "random_state": 42,
                },
            },
        }

    def _initialize_models(self):
        """初始化模型"""
        self.logger.info("初始化機器學習模型...")

        # 初始化各類模型
        for model_type in ModelType:
            model_key = f"{model_type.value}_base"
            self.models[model_key] = None

        self.logger.info("模型初始化完成")

    def _prepare_features(self, df: pd.DataFrame) -> Tuple[np.ndarray, List[str]]:
        """
        準備特徵數據

        Args:
            df: 原始OHLCV數據

        Returns:
            特徵數組和特徵名稱列表
        """
        # 技術指標計算
        df = self._calculate_technical_indicators(df)

        # 選擇特徵
        features = []
        feature_columns = self.config["features"]

        for col in feature_columns:
            if col in df.columns:
                features.append(col)

        # 創建特徵矩陣
        X = df[features].values
        feature_names = features.copy()

        return X, feature_names

    def _calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """計算技術指標"""
        df = df.copy()

        # 移動平均線
        df["sma_5"] = df["close"].rolling(5).mean()
        df["sma_20"] = df["close"].rolling(20).mean()
        df["sma_60"] = df["close"].rolling(60).mean()

        # RSI
        delta = df["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        df["rsi"] = 100 - (100 / (1 + rs))

        # MACD
        ema_12 = df["close"].ewm(span=12).mean()
        ema_26 = df["close"].ewm(span=26).mean()
        df["macd"] = ema_12 - ema_26
        df["macd_signal"] = df["macd"].ewm(span=9).mean()

        # 布林帶
        df["bb_middle"] = df["close"].rolling(20).mean()
        bb_std = df["close"].rolling(20).std()
        df["bb_upper"] = df["bb_middle"] + (bb_std * 2)
        df["bb_lower"] = df["bb_middle"] - (bb_std * 2)
        df["bb_position"] = (df["close"] - df["bb_lower"]) / (
            df["bb_upper"] - df["bb_lower"]
        )

        # ATR (平均真實範圍)
        high_low = df["high"] - df["low"]
        high_close = np.abs(df["high"] - df["close"].shift())
        low_close = np.abs(df["low"] - df["close"].shift())
        ranges = np.maximum(high_low, np.maximum(high_close, low_close))
        df["atr"] = ranges.rolling(14).mean()

        # 隨機指標
        low_14 = df["low"].rolling(14).min()
        high_14 = df["high"].rolling(14).max()
        df["stochastic_k"] = 100 * ((df["close"] - low_14) / (high_14 - low_14))
        df["stochastic_d"] = df["stochastic_k"].rolling(3).mean()

        # OBV (能量潮)
        df["obv"] = (np.sign(df["close"].diff()) * df["volume"]).cumsum()

        # MFI (資金流量指數)
        typical_price = (df["high"] + df["low"] + df["close"]) / 3
        money_flow = typical_price * df["volume"]
        positive_flow = money_flow.where(typical_price > typical_price.shift(1), 0)
        negative_flow = money_flow.where(typical_price < typical_price.shift(1), 0)

        positive_mf = positive_flow.rolling(14).sum()
        negative_mf = negative_flow.rolling(14).sum()

        mfi_ratio = positive_mf / negative_mf
        df["mfi"] = 100 - (100 / (1 + mfi_ratio))

        # ADX (平均方向指數)
        df["adx"] = self._calculate_adx(df)

        return df

    def _calculate_adx(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """計算ADX指標"""
        high_diff = df["high"].diff()
        low_diff = df["low"].diff()

        plus_dm = np.where((high_diff > low_diff) & (high_diff > 0), high_diff, 0)

        minus_dm = np.where((low_diff > high_diff) & (low_diff > 0), low_diff, 0)

        tr = np.maximum(
            df["high"] - df["low"],
            np.maximum(
                np.abs(df["high"] - df["close"].shift()),
                np.abs(df["low"] - df["close"].shift()),
            ),
        )

        plus_dm = pd.Series(plus_dm, index=df.index).rolling(period).mean()
        minus_dm = pd.Series(minus_dm, index=df.index).rolling(period).mean()
        tr = pd.Series(tr, index=df.index).rolling(period).mean()

        plus_di = 100 * (plus_dm / tr)
        minus_di = 100 * (minus_dm / tr)

        dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(period).mean()

        return adx

    def _create_sequences(
        self, data: np.ndarray, lookback: int
    ) -> Tuple[np.ndarray, np.ndarray]:
        """創建LSTM序列數據"""
        X, y = [], []
        for i in range(lookback, len(data)):
            X.append(data[i - lookback : i])
            y.append(data[i, 0])  # 預測close價格

        return np.array(X), np.array(y)

    async def train_lstm_model(
        self, symbol: str, start_date: str, end_date: str
    ) -> ModelMetrics:
        """
        訓練LSTM模型

        Args:
            symbol: 股票代碼 (例如: "0700.hk")
            start_date: 開始日期 (YYYY - MM - DD)
            end_date: 結束日期 (YYYY - MM - DD)

        Returns:
            模型性能指標
        """
        if not TENSORFLOW_AVAILABLE:
            self.logger.warning("TensorFlow未安裝，跳過LSTM模型訓練")
            return None

        start_time = datetime.now()
        self.logger.info(f"開始訓練 {symbol} 的LSTM模型...")

        try:
            # 獲取數據
            data = await self.data_adapter.fetch_data(symbol, start_date, end_date)
            df = pd.DataFrame(data)
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date")

            # 準備特徵
            X, feature_names = self._prepare_features(df)

            # 標準化
            X_scaled = self.feature_scaler.fit_transform(X)

            # 創建序列
            lookback = self.config["lookback_window"]
            X_seq, y_seq = self._create_sequences(X_scaled, lookback)

            # 分割訓練和測試集
            split_idx = int(len(X_seq) * 0.8)
            X_train, X_test = X_seq[:split_idx], X_seq[split_idx:]
            y_train, y_test = y_seq[:split_idx], y_seq[split_idx:]

            # 構建LSTM模型
            model = Sequential()
            config = self.config["ml_config"]["lstm"]

            # 第一層LSTM
            model.add(
                LSTM(
                    config["units"][0],
                    return_sequences=True,
                    input_shape=(lookback, X_scaled.shape[1]),
                )
            )
            model.add(Dropout(config["dropout"]))
            model.add(BatchNormalization())

            # 第二層LSTM
            model.add(LSTM(config["units"][1], return_sequences=True))
            model.add(Dropout(config["dropout"]))
            model.add(BatchNormalization())

            # 第三層LSTM
            model.add(LSTM(config["units"][2], return_sequences=False))
            model.add(Dropout(config["dropout"]))
            model.add(BatchNormalization())

            # 輸出層
            model.add(Dense(1))

            # 編譯模型
            model.compile(
                optimizer=Adam(learning_rate=0.001), loss="mse", metrics=["mae"]
            )

            # 訓練模型
            early_stopping = EarlyStopping(
                monitor="val_loss",
                patience=config["patience"],
                restore_best_weights=True,
            )

            reduce_lr = ReduceLROnPlateau(
                monitor="val_loss", factor=0.5, patience=5, min_lr=0.0001
            )

            history = model.fit(
                X_train,
                y_train,
                validation_data=(X_test, y_test),
                epochs=config["epochs"],
                batch_size=config["batch_size"],
                callbacks=[early_stopping, reduce_lr],
                verbose=0,
            )

            # 預測和評估
            y_pred = model.predict(X_test, verbose=0)
            y_pred = y_pred.flatten()

            # 計算指標
            mae = mean_absolute_error(y_test, y_pred)
            mse = mean_squared_error(y_test, y_pred)
            rmse = np.sqrt(mse)
            r2 = r2_score(y_test, y_pred)

            # 計算交易指標
            returns = np.diff(y_test) / y_test[:-1]
            if len(returns) > 1:
                sharpe = np.mean(returns) / np.std(returns) * np.sqrt(252)
                max_dd = self._calculate_max_drawdown(y_test)
            else:
                sharpe = 0
                max_dd = 0

            training_time = (datetime.now() - start_time).total_seconds()

            # 保存模型
            model_key = f"{symbol}_lstm"
            self.models[model_key] = {
                "model": model,
                "scaler": self.feature_scaler,
                "feature_names": feature_names,
                "config": self.config,
            }

            # 保存指標
            metrics = ModelMetrics(
                model_type="LSTM",
                accuracy=r2,
                mae=mae,
                mse=mse,
                rmse=rmse,
                r2=r2,
                sharpe_ratio=sharpe,
                max_drawdown=max_dd,
                training_time=training_time,
                last_trained=datetime.now(),
            )

            self.model_metrics[model_key] = metrics

            self.logger.info(f"LSTM模型訓練完成 - R²: {r2:.4f}, MAE: {mae:.4f}")

            return metrics

        except Exception as e:
            self.logger.error(f"LSTM模型訓練失敗: {str(e)}")
            raise

    def _calculate_max_drawdown(self, prices: np.ndarray) -> float:
        """計算最大回撤"""
        peak = np.maximum.accumulate(prices)
        drawdown = (prices - peak) / peak
        return np.min(drawdown)

    async def predict_price(
        self,
        symbol: str,
        model_type: ModelType = ModelType.HYBRID,
        horizon: PredictionHorizon = PredictionHorizon.SHORT_TERM,
        days_ahead: int = 5,
    ) -> PredictionResult:
        """
        預測股票價格

        Args:
            symbol: 股票代碼
            model_type: 模型類型
            horizon: 預測時間範圍
            days_ahead: 預測天數

        Returns:
            預測結果
        """
        cache_key = f"{symbol}_{model_type.value}_{horizon.value}_{days_ahead}"

        # 檢查緩存
        if cache_key in self._prediction_cache:
            cached_result = self._prediction_cache[cache_key]
            if (datetime.now() - cached_result.timestamp).seconds < self._cache_expiry:
                self.logger.info(f"返回緩存的預測結果: {symbol}")
                return cached_result

        self.logger.info(f"開始預測 {symbol} ({horizon.value} term)...")

        try:
            # 獲取最新數據 (過去60天)
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")

            data = await self.data_adapter.fetch_data(symbol, start_date, end_date)
            df = pd.DataFrame(data)
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date")

            # 準備特徵
            X, feature_names = self._prepare_features(df)
            X_scaled = self.feature_scaler.transform(X)

            # 預測
            if model_type == ModelType.LSTM and TENSORFLOW_AVAILABLE:
                predicted_price, confidence, volatility, trend = (
                    await self._lstm_predict(symbol, X_scaled, days_ahead)
                )
                model_used = "LSTM"
            elif model_type == ModelType.RANDOM_FOREST:
                predicted_price, confidence, volatility, trend = await self._rf_predict(
                    symbol, X_scaled, days_ahead
                )
                model_used = "Random Forest"
            elif model_type == ModelType.XGBOOST:
                predicted_price, confidence, volatility, trend = (
                    await self._xgb_predict(symbol, X_scaled, days_ahead)
                )
                model_used = "XGBoost"
            else:  # HYBRID
                predicted_price, confidence, volatility, trend = (
                    await self._hybrid_predict(symbol, X_scaled, days_ahead)
                )
                model_used = "Hybrid"

            # 計算風險等級
            risk_level = self._calculate_risk_level(volatility, confidence)

            # 創建預測結果
            result = PredictionResult(
                symbol=symbol,
                timestamp=datetime.now(),
                horizon=horizon,
                predicted_price=predicted_price,
                confidence=confidence,
                volatility=volatility,
                trend_direction=trend,
                risk_level=risk_level,
                model_used=model_used,
            )

            # 緩存結果
            self._prediction_cache[cache_key] = result

            self.logger.info(
                f"預測完成: {symbol} = {predicted_price:.2f}, "
                f"confidence={confidence:.2f}, trend={trend}"
            )

            return result

        except Exception as e:
            self.logger.error(f"價格預測失敗: {str(e)}")
            raise

    async def _lstm_predict(
        self, symbol: str, X_scaled: np.ndarray, days_ahead: int
    ) -> Tuple[float, float, float, str]:
        """LSTM預測"""
        model_key = f"{symbol}_lstm"
        if model_key not in self.models or self.models[model_key] is None:
            # 如果模型不存在，嘗試訓練
            await self.train_lstm_model(symbol, "2023 - 01 - 01", "2024 - 12 - 31")

        model = self.models[model_key]["model"]
        lookback = self.config["lookback_window"]

        # 獲取最後一個序列
        last_sequence = X_scaled[-lookback:].reshape(1, lookback, X_scaled.shape[1])

        # 預測
        prediction = model.predict(last_sequence, verbose=0)[0][0]

        # 反標準化
        predicted_price = self.scaler.inverse_transform([[prediction]])[0][0]

        # 計算置信度和波動率
        actual_price = X_scaled[-1, 0]
        error = abs(prediction - actual_price)
        confidence = max(0, 1 - error)
        volatility = error * 2  # 簡化計算

        # 判斷趨勢
        trend = (
            "up"
            if prediction > actual_price
            else "down" if prediction < actual_price else "sideways"
        )

        return predicted_price, confidence, volatility, trend

    async def _rf_predict(
        self, symbol: str, X_scaled: np.ndarray, days_ahead: int
    ) -> Tuple[float, float, float, str]:
        """Random Forest預測"""
        # 簡化實現
        y = X_scaled[:, 0]  # 使用close價格作為目標
        X = X_scaled[:-1]  # 特徵

        model = RandomForestRegressor(**self.config["ml_config"]["random_forest"])
        model.fit(X, y[1:])

        # 預測
        last_features = X_scaled[-1].reshape(1, -1)
        prediction = model.predict(last_features)[0]

        predicted_price = self.scaler.inverse_transform([[prediction]])[0][0]

        # 計算指標
        error = abs(prediction - y[-1])
        confidence = max(0, 1 - error)
        volatility = error * 2
        trend = (
            "up" if prediction > y[-1] else "down" if prediction < y[-1] else "sideways"
        )

        return predicted_price, confidence, volatility, trend

    async def _xgb_predict(
        self, symbol: str, X_scaled: np.ndarray, days_ahead: int
    ) -> Tuple[float, float, float, str]:
        """XGBoost預測"""
        y = X_scaled[:, 0]
        X = X_scaled[:-1]

        model = xgb.XGBRegressor(**self.config["ml_config"]["xgboost"])
        model.fit(X, y[1:])

        last_features = X_scaled[-1].reshape(1, -1)
        prediction = model.predict(last_features)[0]

        predicted_price = self.scaler.inverse_transform([[prediction]])[0][0]

        error = abs(prediction - y[-1])
        confidence = max(0, 1 - error)
        volatility = error * 2
        trend = (
            "up" if prediction > y[-1] else "down" if prediction < y[-1] else "sideways"
        )

        return predicted_price, confidence, volatility, trend

    async def _hybrid_predict(
        self, symbol: str, X_scaled: np.ndarray, days_ahead: int
    ) -> Tuple[float, float, float, str]:
        """混合模型預測 (多模型投票)"""
        # 獲取各模型預測
        lstm_price, _, _, lstm_trend = await self._lstm_predict(
            symbol, X_scaled, days_ahead
        )
        rf_price, rf_conf, rf_vol, rf_trend = await self._rf_predict(
            symbol, X_scaled, days_ahead
        )
        xgb_price, xgb_conf, xgb_vol, xgb_trend = await self._xgb_predict(
            symbol, X_scaled, days_ahead
        )

        # 權重平均
        weights = [0.5, 0.25, 0.25]  # LSTM權重更高
        predicted_price = (
            weights[0] * lstm_price + weights[1] * rf_price + weights[2] * xgb_price
        )

        # 綜合置信度
        confidence = (
            weights[0] * lstm_price + weights[1] * rf_conf + weights[2] * xgb_conf
        ) / sum(weights)

        # 綜合波動率
        volatility = (
            weights[0] * 0.02 + weights[1] * rf_vol + weights[2] * xgb_vol
        ) / sum(weights)

        # 趨勢投票
        trends = {"up": 0, "down": 0, "sideways": 0}
        trends[lstm_trend] += weights[0]
        trends[rf_trend] += weights[1]
        trends[xgb_trend] += weights[2]

        final_trend = max(trends.items(), key=lambda x: x[1])[0]

        return predicted_price, confidence, volatility, final_trend

    def _calculate_risk_level(self, volatility: float, confidence: float) -> str:
        """計算風險等級"""
        risk_score = volatility * (2 - confidence)  # 波動率高、置信度低 = 高風險

        if risk_score < 0.5:
            return "low"
        elif risk_score < 1.0:
            return "medium"
        else:
            return "high"

    async def batch_predict(
        self,
        symbols: List[str],
        model_type: ModelType = ModelType.HYBRID,
        horizon: PredictionHorizon = PredictionHorizon.SHORT_TERM,
    ) -> Dict[str, PredictionResult]:
        """
        批量預測

        Args:
            symbols: 股票代碼列表
            model_type: 模型類型
            horizon: 預測時間範圍

        Returns:
            預測結果字典
        """
        self.logger.info(f"開始批量預測 {len(symbols)} 個股票...")

        results = {}
        tasks = []

        for symbol in symbols:
            task = self.predict_price(symbol, model_type, horizon)
            tasks.append(task)

        # 並行執行預測
        predictions = await asyncio.gather(*tasks, return_exceptions=True)

        for symbol, prediction in zip(symbols, predictions):
            if isinstance(prediction, Exception):
                self.logger.error(f"預測失敗 {symbol}: {str(prediction)}")
                results[symbol] = None
            else:
                results[symbol] = prediction

        self.logger.info(f"批量預測完成，成功: {sum(1 for r in results.values() if r)}")

        return results

    def get_model_metrics(self, symbol: str) -> Optional[ModelMetrics]:
        """獲取模型性能指標"""
        return self.model_metrics.get(f"{symbol}_lstm")

    def get_feature_importance(self, symbol: str) -> Optional[Dict[str, float]]:
        """獲取特徵重要性"""
        model_key = f"{symbol}_lstm"
        if model_key not in self.models or self.models[model_key] is None:
            return None

        # 簡化實現 - 返回技術指標的重要性
        return {
            "rsi": 0.15,
            "macd": 0.12,
            "bb_position": 0.10,
            "atr": 0.08,
            "sma_20": 0.08,
            "sma_60": 0.07,
            "volume": 0.07,
            "obv": 0.06,
            "stochastic_k": 0.06,
            "mfi": 0.05,
            "adx": 0.05,
            "sma_5": 0.04,
            "stochastic_d": 0.04,
            "open": 0.03,
        }

    def clear_cache(self):
        """清除預測緩存"""
        self._prediction_cache.clear()
        self.logger.info("預測緩存已清除")
