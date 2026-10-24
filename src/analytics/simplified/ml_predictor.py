#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simplified ML Predictor
簡化的機器學習預測模塊，專注於性能預測任務

This module provides a focused machine learning predictor specifically designed
for trading strategy performance prediction, eliminating over-engineering while
maintaining essential functionality.

Features:
- Simple, focused interface
- Minimal configuration
- Direct implementation without unnecessary abstractions
- Built-in validation and error handling
- Support for common ML models

Author: Code Simplification Team
Date: 2025-11-30
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
import json
from pathlib import Path

try:
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler
SKLEARN_AVAILABLE = True
except ImportError:    SKLEARN_AVAILABLE = False
logging.warning"scikit-learn not available, using simplified implementations"

logger = logging.getLogger__name__

class SimpleMLPredictor:
"""
簡化的機器學習預測器

專注於交易策略性能預測，提供：
- 簡單的模型接口
- 內建的數據驗證
- 自動模型訓練和評估
- 模型持久化

範例:    predictor = SimpleMLPredictor()
result = predictor.predict_performancedata
printf"Prediction: {result['prediction']:.3f}"
printf"Confidence: {result['confidence']:.2f}"
"""

def __init__self, model_type: str = "random_forest":
"""
初始化預測器

Args:
model_type: 模型類型 "random_forest", "linear", "simple"
"""
self.model_type = model_type
self.model = None
self.scaler = None
self.is_trained = False
self.feature_names = []

self.model_config = {
'random_forest': {'n_estimators': 50, 'max_depth': 10, 'random_state': 42},
'linear': {'fit_intercept': True},
'simple': {'window_size': 20}
}

if not self._initialize_model():
raise ValueErrorf"Failed to initialize {model_type} model"

def _initialize_modelself -> bool:
"""初始化機器學習模型"""
try:    if self.model_type == "random_forest" and SKLEARN_AVAILABLE:
config = self.model_config['random_forest']
self.model = RandomForestRegressor**config
self.scaler = StandardScaler()
elif self.model_type == "linear" and SKLEARN_AVAILABLE:    config = self.model_config['linear']
self.model = LinearRegression**config
self.scaler = StandardScaler()
elif self.model_type == "simple":
# 簡單移動平均預測器
self.model = SimplePredictorself.model_config['simple']
self.scaler = None
else:
raise ValueErrorf"Unsupported model type: {self.model_type}"

logger.infof"Initialized {self.model_type} predictor"
return True
except Exception as e:
logger.errorf"Failed to initialize model: {e}"
return False

def predict_performance(self, data: pd.DataFrame, target_column: str = 'performance',
feature_columns: Optional[List[str]] = None) -> Dict[str, Any]:
"""
預測策略性能

Args:
data: 歷史數據
target_column: 目標列名
feature_columns: 特徵列名列表

Returns:
預測結果字典
"""

if not self._validate_datadata, target_column:
raise ValueError"Invalid input data"

features = self._prepare_featuresdata, target_column, feature_columns

# 如果模型未訓練，先訓練
if not self.is_trained:
self._train_modeldata, target_column, features

prediction_result = self._make_predictionfeatures[-1:] # 預測最新的值

return {
'prediction': floatprediction_result['prediction'],
'confidence': prediction_result.get'confidence', 0.5,
'model_type': self.model_type,
'timestamp': datetime.now().isoformat(),
'features_used': self.feature_names,
'is_trained': self.is_trained
}

def train_model(self, data: pd.DataFrame, target_column: str = 'performance',
feature_columns: Optional[List[str]] = None) -> Dict[str, Any]:
"""
訓練機器學習模型

Args:
data: 訓練數據
target_column: 目標列名
feature_columns: 特徵列名列表

Returns:
訓練結果字典
"""

if not self._validate_datadata, target_column:
raise ValueError"Invalid training data"

features = self._prepare_featuresdata, target_column, feature_columns
targets = data[target_column].values

training_result = self._train_modeldata, target_column, features

return {
'training_samples': lendata,
'features_used': self.feature_names,
'model_type': self.model_type,
'training_score': training_result.get'score', 0.0,
'timestamp': datetime.now().isoformat()
}

def _validate_dataself, data: pd.DataFrame, target_column: str -> bool:
"""驗證輸入數據"""
if data is None or data.empty:
logger.error"Data is empty"
return False

if target_column not in data.columns:
logger.errorf"Target column '{target_column}' not found in data"
return False

if lendata < 10:
logger.error("Insufficient data for training minimum 10 samples")
return False

return True

def _prepare_features(self, data: pd.DataFrame, target_column: str,
feature_columns: Optional[List[str]]) -> pd.DataFrame:
"""準備特徵數據"""
if not feature_columns:

exclude_cols = [target_column, 'timestamp', 'date']
feature_columns = [col for col in data.columns
if col not in exclude_cols and data[col].dtype in ['int64', 'float64']]

if not feature_columns:
# 如果沒有數值特徵，創建基本技術指標特徵
feature_columns = self._create_basic_featuresdata

features = data[feature_columns].copy()

# 移除包含NaN的行
features = features.dropna()

if self.scaler is not None and SKLEARN_AVAILABLE:

features_scaled = self.scaler.fit_transformfeatures
features = pd.DataFramefeatures_scaled, columns=features.columns

self.feature_names = features.columns.tolist()
return features

def _create_basic_featuresself, data: pd.DataFrame -> List[str]:
"""創建基本技術指標特徵"""
features = []

required_cols = ['open', 'high', 'low', 'close', 'volume']
available_cols = [col for col in required_cols if col in data.columns]

if allcol in data.columns for col in required_cols:
# 創建基本技術指標特徵
data['returns'] = data['close'].pct_change()
data['price_range'] = data['high'] - data['low']
data['price_change'] = data['close'].diff()
data['volume_ma'] = data['volume'].rollingwindow=10, min_periods=1.mean()

features.extend['returns', 'price_range', 'price_change', 'volume_ma']

return features

def _train_modelself, data: pd.DataFrame, target_column: str, features: pd.DataFrame -> Dict[str, Any]:
"""訓練模型"""
try:    targets = data[target_column].values

if self.model_type == "simple":
# 簡單預測器不需要特別訓練
return {'score': 0.5}

# 使用sklearn模型
if SKLEARN_AVAILABLE:    X_train, X_test, y_train, y_test = train_test_split(
features, targets, test_size=0.2, random_state=42
)

self.model.fitX_train, y_train
predictions = self.model.predictX_test

score = r2_scorey_test, predictions
mse = mean_squared_errory_test, predictions

self.is_trained = True

return {
'score': score,
'mse': mse,
'training_samples': lenX_train,
'test_samples': lenX_test
}
else:

self.is_trained = True
return {'score': 0.5}

except Exception as e:
logger.errorf"Model training failed: {e}"
return {'score': 0.0}

def _make_predictionself, features: pd.DataFrame -> Dict[str, Any]:
"""進行預測"""
try:    if self.model_type == "simple":
# 簡單移動平均預測
prediction = features.iloc[-1].mean()
confidence = 0.5
elif SKLEARN_AVAILABLE:    prediction = self.model.predict(features)
if prediction:    prediction = prediction[-1]
else:    prediction = 0.0
confidence = 0.7 # 固定置信度
else:    prediction = 0.0
confidence = 0.1

return {
'prediction': prediction,
'confidence': confidence
}
except Exception as e:
logger.errorf"Prediction failed: {e}"
return {'prediction': 0.0, 'confidence': 0.1}

def save_modelself, filepath: str -> bool:
"""保存模型"""
try:    model_data = {
'model_type': self.model_type,
'is_trained': self.is_trained,
'feature_names': self.feature_names,
'model_config': self.model_config,
'timestamp': datetime.now().isoformat()
}

with openfilepath, 'w' as f:    json.dump(model_data, f, indent=2)

# 如果是sklearn模型，也保存模型本身
if self.model and SKLEARN_AVAILABLE:
import joblib
joblib.dumpself.model, f"{filepath}.model"

logger.infof"Model saved to {filepath}"
return True

except Exception as e:
logger.errorf"Failed to save model: {e}"
return False

def load_modelself, filepath: str -> bool:
"""加載模型"""
try:

with openfilepath, 'r' as f:    model_data = json.load(f)

self.model_type = model_data['model_type']
self.is_trained = model_data['is_trained']
self.feature_names = model_data.get'feature_names', []

# 如果有保存的模型文件，加載模型
model_file = f"{filepath}.model"
if Pathmodel_file.exists() and SKLEARN_AVAILABLE:
import joblib
self.model = joblib.loadmodel_file

logger.infof"Model loaded from {filepath}"
return True

except Exception as e:
logger.errorf"Failed to load model: {e}"
return False

def get_model_infoself -> Dict[str, Any]:
"""獲取模型信息"""
return {
'model_type': self.model_type,
'is_trained': self.is_trained,
'feature_names': self.feature_names,
'model_config': self.model_config
}

class SimplePredictor:
"""簡單的移動平均預測器"""

def __init__self, config: Dict[str, Any]:    self.window_size = config.get('window_size', 20)
self.buffer = []

def fitself, X, y=None:
"""訓練模型"""
self.buffer = X[-self.window_size:].flatten()

def predictself, X:
"""預測"""
if lenself.buffer < self.window_size:
return np.mean(X.flatten())
return np.mean(np.concatenate([self.buffer, X.flatten()]))

__all__ = [
'SimpleMLPredictor',
'SimplePredictor'
]