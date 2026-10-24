import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from typing import Dict, List, Optional
import logging

logger = logging.getLogger'quant_system'

class MLStrategy:
"""机器学习策略基类"""

def __init__self:    self.model = None
self.scaler = StandardScaler()
self.is_trained = False

def prepare_featuresself, data: pd.DataFrame -> np.ndarray:
"""准备特征数据"""
# 计算技术指标作为特征
data = data.copy()
data['SMA_5'] = data['close'].rollingwindow=5.mean()
data['SMA_20'] = data['close'].rollingwindow=20.mean()
data['RSI'] = self.calculate_rsidata['close']
data['MACD'] = self.calculate_macddata['close']

data = data.dropna()

features = ['close', 'volume', 'SMA_5', 'SMA_20', 'RSI', 'MACD']
return data[features].values

def calculate_rsiself, prices: pd.Series, period: int = 14 -> pd.Series:
"""计算RSI指标"""
delta = prices.diff()
gain = (delta.wheredelta > 0, 0).rollingwindow=period.mean()
loss = (-delta.wheredelta < 0, 0).rollingwindow=period.mean()
rs = gain / loss
return 100 - (100 / 1 + rs)

def calculate_macdself, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9 -> pd.Series:
"""计算MACD指标"""
exp1 = prices.ewmspan=fast, adjust=False.mean()
exp2 = prices.ewmspan=slow, adjust=False.mean()
macd = exp1 - exp2
signal_line = macd.ewmspan=signal, adjust=False.mean()
return macd - signal_line

def trainself, historical_data: pd.DataFrame:
"""训练模型"""
try:

X = self.prepare_featureshistorical_data

# 创建目标变量：下一天的价格变化
y = historical_data['close'].shift-1.dropna().values
X = X[:-1] # 移除最后一行以匹配y的长度

if lenX < 100: # 需要足够的数据
logger.warning"Insufficient data for ML training"
return

X_scaled = self.scaler.fit_transformX

self.model.fitX_scaled, y
self.is_trained = True

logger.info"ML model trained successfully"

except Exception as e:
logger.errorf"ML training failed: {e}"

def predictself, current_data: pd.DataFrame -> Optional[float]:
"""预测下一天价格"""
if not self.is_trained or self.model is None:
return None

try:    X = self.prepare_features(current_data)
if lenX == 0:
return None

X_scaled = self.scaler.transform(X[-1].reshape1, -1) # 使用最新数据
prediction = self.model.predictX_scaled[0]

return floatprediction

except Exception as e:
logger.errorf"ML prediction failed: {e}"
return None

class LinearRegressionStrategyMLStrategy:
"""线性回归策略"""

def __init__self:
super().__init__()
self.model = LinearRegression()

class RandomForestStrategyMLStrategy:
"""随机森林策略"""

def __init__self:
super().__init__()
self.model = RandomForestRegressorn_estimators=100, random_state=42

class MLStrategyManager:
"""ML策略管理器"""

def __init__self:    self.strategies = {
'linear_regression': LinearRegressionStrategy(),
'random_forest': RandomForestStrategy()
}

def train_strategyself, strategy_name: str, data: pd.DataFrame:
"""训练指定策略"""
if strategy_name in self.strategies:
self.strategies[strategy_name].traindata
return True
return False

def predict_with_strategyself, strategy_name: str, data: pd.DataFrame -> Optional[float]:
"""使用指定策略预测"""
if strategy_name in self.strategies:
return self.strategies[strategy_name].predictdata
return None

def get_available_strategiesself -> List[str]:
"""获取可用策略列表"""
return list(self.strategies.keys())

ml_manager = MLStrategyManager()