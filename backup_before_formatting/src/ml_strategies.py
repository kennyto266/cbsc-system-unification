import logging
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger("quant_system")


class MLStrategy:
    """机器学习策略基类"""

    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False

    def prepare_features(self, data: pd.DataFrame) -> np.ndarray:
        """准备特征数据"""
        # 计算技术指标作为特征
        data = data.copy()
        data["SMA_5"] = data["close"].rolling(window=5).mean()
        data["SMA_20"] = data["close"].rolling(window=20).mean()
        data["RSI"] = self.calculate_rsi(data["close"])
        data["MACD"] = self.calculate_macd(data["close"])

        # 移除NaN值
        data = data.dropna()

        # 选择特征
        features = ["close", "volume", "SMA_5", "SMA_20", "RSI", "MACD"]
        return data[features].values

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

    def train(self, historical_data: pd.DataFrame):
        """训练模型"""
        try:
            # 准备特征
            X = self.prepare_features(historical_data)

            # 创建目标变量：下一天的价格变化
            y = historical_data["close"].shift(-1).dropna().values
            X = X[:-1]  # 移除最后一行以匹配y的长度

            if len(X) < 100:  # 需要足够的数据
                logger.warning("Insufficient data for ML training")
                return

            # 标准化特征
            X_scaled = self.scaler.fit_transform(X)

            # 训练模型
            self.model.fit(X_scaled, y)
            self.is_trained = True

            logger.info("ML model trained successfully")

        except Exception as e:
            logger.error(f"ML training failed: {e}")

    def predict(self, current_data: pd.DataFrame) -> Optional[float]:
        """预测下一天价格"""
        if not self.is_trained or self.model is None:
            return None

        try:
            X = self.prepare_features(current_data)
            if len(X) == 0:
                return None

            X_scaled = self.scaler.transform(X[-1].reshape(1, -1))  # 使用最新数据
            prediction = self.model.predict(X_scaled)[0]

            return float(prediction)

        except Exception as e:
            logger.error(f"ML prediction failed: {e}")
            return None


class LinearRegressionStrategy(MLStrategy):
    """线性回归策略"""

    def __init__(self):
        super().__init__()
        self.model = LinearRegression()


class RandomForestStrategy(MLStrategy):
    """随机森林策略"""

    def __init__(self):
        super().__init__()
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)


class MLStrategyManager:
    """ML策略管理器"""

    def __init__(self):
        self.strategies = {
            "linear_regression": LinearRegressionStrategy(),
            "random_forest": RandomForestStrategy(),
        }

    def train_strategy(self, strategy_name: str, data: pd.DataFrame):
        """训练指定策略"""
        if strategy_name in self.strategies:
            self.strategies[strategy_name].train(data)
            return True
        return False

    def predict_with_strategy(
        self, strategy_name: str, data: pd.DataFrame
    ) -> Optional[float]:
        """使用指定策略预测"""
        if strategy_name in self.strategies:
            return self.strategies[strategy_name].predict(data)
        return None

    def get_available_strategies(self) -> List[str]:
        """获取可用策略列表"""
        return list(self.strategies.keys())


# 全局实例
ml_manager = MLStrategyManager()
