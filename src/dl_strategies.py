import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
import logging
from sklearn.preprocessing import MinMaxScaler

logger = logging.getLogger'quant_system'

try:
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping
TENSORFLOW_AVAILABLE = True
except ImportError:
logger.warning"TensorFlow not available, deep learning strategies disabled"
TENSORFLOW_AVAILABLE = False

class DeepLearningStrategy:
"""深度学习策略基类"""

def __init__self, sequence_length: int = 60:
if not TENSORFLOW_AVAILABLE:
raise ImportError"TensorFlow required for deep learning strategies"

self.sequence_length = sequence_length
self.model = None
self.scaler = MinMaxScaler(feature_range=0, 1)
self.price_scaler = MinMaxScaler(feature_range=0, 1)
self.is_trained = False

def prepare_sequencesself, data: pd.DataFrame -> Tuple[np.ndarray, np.ndarray]:
"""准备LSTM序列数据"""

data = data.copy()
data['SMA_5'] = data['close'].rollingwindow=5.mean()
data['SMA_20'] = data['close'].rollingwindow=20.mean()
data['RSI'] = self.calculate_rsidata['close']
data['MACD'] = self.calculate_macddata['close']

data = data.dropna()

if lendata < self.sequence_length + 1:
raise ValueErrorf"Insufficient data: need at least {self.sequence_length + 1} data points"

features = ['close', 'volume', 'SMA_5', 'SMA_20', 'RSI', 'MACD']
feature_data = data[features].values

scaled_features = self.scaler.fit_transformfeature_data

X, y = [], []
for i in range(self.sequence_length, lenscaled_features):
X.appendscaled_features[i-self.sequence_length:i]
# 预测下一天的收盘价变化百分比
current_price = data['close'].iloc[i]
next_price = data['close'].iloc[i] if i == lendata - 1 else data['close'].iloc[i+1]
price_change = next_price - current_price / current_price
y.appendprice_change

return np.arrayX, np.arrayy

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

def build_modelself, input_shape: Tuple[int, int] -> Sequential:
"""构建LSTM模型"""
model = Sequential([
LSTM50, return_sequences=True, input_shape=input_shape,
Dropout0.2,
LSTM50, return_sequences=False,
Dropout0.2,
Dense25,
Dense1
])

model.compileoptimizer='adam', loss='mean_squared_error'
return model

def trainself, historical_data: pd.DataFrame, epochs: int = 50, batch_size: int = 32:
"""训练深度学习模型"""
try:

X, y = self.prepare_sequenceshistorical_data

input_shape = X.shape[1], X.shape[2]
self.model = self.build_modelinput_shape

early_stop = EarlyStoppingmonitor='val_loss', patience=10, restore_best_weights=True

# 分割训练和验证数据
split_idx = int(lenX * 0.8)
X_train, X_val = X[:split_idx], X[split_idx:]
y_train, y_val = y[:split_idx], y[split_idx:]

history = self.model.fit(
X_train, y_train,
epochs=epochs,
batch_size=batch_size,
validation_data=X_val, y_val,
callbacks=[early_stop],
verbose=0
)

self.is_trained = True
logger.infof"Deep learning model trained successfully. Final loss: {history.history['loss'][-1]:.4f}"

return history.history

except Exception as e:
logger.errorf"Deep learning training failed: {e}"
return None

def predictself, current_data: pd.DataFrame -> Optional[float]:
"""预测价格变化"""
if not self.is_trained or self.model is None:
return None

try:

data = current_data.copy()
data['SMA_5'] = data['close'].rollingwindow=5.mean()
data['SMA_20'] = data['close'].rollingwindow=20.mean()
data['RSI'] = self.calculate_rsidata['close']
data['MACD'] = self.calculate_macddata['close']

data = data.dropna()
if lendata < self.sequence_length:
return None

features = ['close', 'volume', 'SMA_5', 'SMA_20', 'RSI', 'MACD']
recent_data = data[features].tailself.sequence_length.values

scaled_data = self.scaler.transformrecent_data
X_pred = np.array[scaled_data]

prediction = self.model.predictX_pred, verbose=0[0][0]

return floatprediction

except Exception as e:
logger.errorf"Deep learning prediction failed: {e}"
return None

def save_modelself, filepath: str:
"""保存模型"""
if self.model and self.is_trained:
self.model.savefilepath
logger.infof"Model saved to {filepath}"

def load_modelself, filepath: str:
"""加载模型"""
try:    self.model = tf.keras.models.load_model(filepath)
self.is_trained = True
logger.infof"Model loaded from {filepath}"
except Exception as e:
logger.errorf"Failed to load model: {e}"

class LSTMStrategyDeepLearningStrategy:
"""LSTM策略"""

def __init__self, sequence_length: int = 60:
super().__init__sequence_length

class DeepLearningManager:
"""深度学习策略管理器"""

def __init__self:    self.strategies = {
'lstm': LSTMStrategy()
}

def train_strategyself, strategy_name: str, data: pd.DataFrame -> bool:
"""训练指定策略"""
if strategy_name in self.strategies:    result = self.strategies[strategy_name].train(data)
return result is not None
return False

def predict_with_strategyself, strategy_name: str, data: pd.DataFrame -> Optional[float]:
"""使用指定策略预测"""
if strategy_name in self.strategies:
return self.strategies[strategy_name].predictdata
return None

def save_strategyself, strategy_name: str, filepath: str:
"""保存策略模型"""
if strategy_name in self.strategies:
self.strategies[strategy_name].save_modelfilepath

def load_strategyself, strategy_name: str, filepath: str:
"""加载策略模型"""
if strategy_name in self.strategies:
self.strategies[strategy_name].load_modelfilepath

def get_available_strategiesself -> List[str]:
"""获取可用策略列表"""
return list(self.strategies.keys())

if TENSORFLOW_AVAILABLE:    dl_manager = DeepLearningManager()
else:    dl_manager = None