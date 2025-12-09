import logging
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

logger = logging.getLogger("quant_system")

try:
    import tensorflow as tf
    from tensorflow.keras.callbacks import EarlyStopping
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    from tensorflow.keras.models import Sequential

    TENSORFLOW_AVAILABLE = True
except ImportError:
    logger.warning("TensorFlow not available, deep learning strategies disabled")
    TENSORFLOW_AVAILABLE = False


class DeepLearningStrategy:
    """深度学习策略基类"""

    def __init__(self, sequence_length: int = 60):
        if not TENSORFLOW_AVAILABLE:
            raise ImportError("TensorFlow required for deep learning strategies")

        self.sequence_length = sequence_length
        self.model = None
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.price_scaler = MinMaxScaler(feature_range=(0, 1))
        self.is_trained = False

    def prepare_sequences(self, data: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """准备LSTM序列数据"""
        # 计算技术指标
        data = data.copy()
        data["SMA_5"] = data["close"].rolling(window=5).mean()
        data["SMA_20"] = data["close"].rolling(window=20).mean()
        data["RSI"] = self.calculate_rsi(data["close"])
        data["MACD"] = self.calculate_macd(data["close"])

        # 移除NaN值
        data = data.dropna()

        if len(data) < self.sequence_length + 1:
            raise ValueError(
                f"Insufficient data: need at least {self.sequence_length + 1} data points"
            )

        # 选择特征
        features = ["close", "volume", "SMA_5", "SMA_20", "RSI", "MACD"]
        feature_data = data[features].values

        # 标准化特征
        scaled_features = self.scaler.fit_transform(feature_data)

        # 创建序列
        X, y = [], []
        for i in range(self.sequence_length, len(scaled_features)):
            X.append(scaled_features[i - self.sequence_length : i])
            # 预测下一天的收盘价变化百分比
            current_price = data["close"].iloc[i]
            next_price = (
                data["close"].iloc[i]
                if i == len(data) - 1
                else data["close"].iloc[i + 1]
            )
            price_change = (next_price - current_price) / current_price
            y.append(price_change)

        return np.array(X), np.array(y)

    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """计算RSI指标"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def calculate_macd(
        self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
    ) -> pd.Series:
        """计算MACD指标"""
        exp1 = prices.ewm(span=fast, adjust=False).mean()
        exp2 = prices.ewm(span=slow, adjust=False).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        return macd - signal_line

    def build_model(self, input_shape: Tuple[int, int]) -> Sequential:
        """构建LSTM模型"""
        model = Sequential(
            [
                LSTM(50, return_sequences=True, input_shape=input_shape),
                Dropout(0.2),
                LSTM(50, return_sequences=False),
                Dropout(0.2),
                Dense(25),
                Dense(1),
            ]
        )

        model.compile(optimizer="adam", loss="mean_squared_error")
        return model

    def train(
        self, historical_data: pd.DataFrame, epochs: int = 50, batch_size: int = 32
    ):
        """训练深度学习模型"""
        try:
            # 准备序列数据
            X, y = self.prepare_sequences(historical_data)

            # 构建模型
            input_shape = (X.shape[1], X.shape[2])
            self.model = self.build_model(input_shape)

            # 设置早停
            early_stop = EarlyStopping(
                monitor="val_loss", patience=10, restore_best_weights=True
            )

            # 分割训练和验证数据
            split_idx = int(len(X) * 0.8)
            X_train, X_val = X[:split_idx], X[split_idx:]
            y_train, y_val = y[:split_idx], y[split_idx:]

            # 训练模型
            history = self.model.fit(
                X_train,
                y_train,
                epochs=epochs,
                batch_size=batch_size,
                validation_data=(X_val, y_val),
                callbacks=[early_stop],
                verbose=0,
            )

            self.is_trained = True
            logger.info(
                f"Deep learning model trained successfully. Final loss: {history.history['loss'][-1]:.4f}"
            )

            return history.history

        except Exception as e:
            logger.error(f"Deep learning training failed: {e}")
            return None

    def predict(self, current_data: pd.DataFrame) -> Optional[float]:
        """预测价格变化"""
        if not self.is_trained or self.model is None:
            return None

        try:
            # 准备最新序列
            data = current_data.copy()
            data["SMA_5"] = data["close"].rolling(window=5).mean()
            data["SMA_20"] = data["close"].rolling(window=20).mean()
            data["RSI"] = self.calculate_rsi(data["close"])
            data["MACD"] = self.calculate_macd(data["close"])

            data = data.dropna()
            if len(data) < self.sequence_length:
                return None

            features = ["close", "volume", "SMA_5", "SMA_20", "RSI", "MACD"]
            recent_data = data[features].tail(self.sequence_length).values

            # 标准化
            scaled_data = self.scaler.transform(recent_data)
            X_pred = np.array([scaled_data])

            # 预测
            prediction = self.model.predict(X_pred, verbose=0)[0][0]

            return float(prediction)

        except Exception as e:
            logger.error(f"Deep learning prediction failed: {e}")
            return None

    def save_model(self, filepath: str):
        """保存模型"""
        if self.model and self.is_trained:
            self.model.save(filepath)
            logger.info(f"Model saved to {filepath}")

    def load_model(self, filepath: str):
        """加载模型"""
        try:
            self.model = tf.keras.models.load_model(filepath)
            self.is_trained = True
            logger.info(f"Model loaded from {filepath}")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")


class LSTMStrategy(DeepLearningStrategy):
    """LSTM策略"""

    def __init__(self, sequence_length: int = 60):
        super().__init__(sequence_length)


class DeepLearningManager:
    """深度学习策略管理器"""

    def __init__(self):
        self.strategies = {"lstm": LSTMStrategy()}

    def train_strategy(self, strategy_name: str, data: pd.DataFrame) -> bool:
        """训练指定策略"""
        if strategy_name in self.strategies:
            result = self.strategies[strategy_name].train(data)
            return result is not None
        return False

    def predict_with_strategy(
        self, strategy_name: str, data: pd.DataFrame
    ) -> Optional[float]:
        """使用指定策略预测"""
        if strategy_name in self.strategies:
            return self.strategies[strategy_name].predict(data)
        return None

    def save_strategy(self, strategy_name: str, filepath: str):
        """保存策略模型"""
        if strategy_name in self.strategies:
            self.strategies[strategy_name].save_model(filepath)

    def load_strategy(self, strategy_name: str, filepath: str):
        """加载策略模型"""
        if strategy_name in self.strategies:
            self.strategies[strategy_name].load_model(filepath)

    def get_available_strategies(self) -> List[str]:
        """获取可用策略列表"""
        return list(self.strategies.keys())


# 全局实例
if TENSORFLOW_AVAILABLE:
    dl_manager = DeepLearningManager()
else:
    dl_manager = None
