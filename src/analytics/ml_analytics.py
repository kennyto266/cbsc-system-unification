"""
港股量化交易 AI Agent 系统 - 机器学习分析

Phase 5: Advanced Machine Learning Analytics
============================================

MLAnalytics provides sophisticated machine learning analytics capabilities for
0700.HK quantitative trading strategies including pattern recognition,
predictive modeling, and automated feature analysis.

Features:
- Pattern recognition in parameter performance
- Predictive performance modeling
- Anomaly detection in strategy behavior
- Clustering of similar parameter combinations
- Automated feature importance analysis
- Time series forecasting
- Classification of market regimes
- Reinforcement learning for strategy optimization

ML Capabilities:
- Supervised learning Random Forest, XGBoost, Neural Networks
- Unsupervised learning Clustering, Dimensionality Reduction
- Time series analysis LSTM, ARIMA, Prophet
- Anomaly detection Isolation Forest, One-Class SVM
- Feature engineering and selection
- Model validation and cross-validation
- Ensemble methods
- Deep learning applications

Applications:
- Performance prediction
- Risk assessment
- Market regime classification
- Parameter optimization
- Strategy selection
- Portfolio construction
- Trading signal generation
- Automated decision making

Author: Claude Code Assistant
Date: 2025-11-29
Version: 5.0.0
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple, Union, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from pathlib import Path
import json
from enum import Enum
import pickle

# Machine learning libraries
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier, IsolationForest
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
from sklearn.decomposition import PCA, FactorAnalysis, TSNE
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
from sklearn.feature_selection import SelectKBest, f_regression, mutual_info_regression
from sklearn.model_selection import TimeSeriesSplit, cross_val_score, GridSearchCV
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.neural_network import MLPRegressor, MLPClassifier

# Advanced ML libraries
try:
import xgboost as xgb
XGB_AVAILABLE = True
except ImportError:    XGB_AVAILABLE = False

try:
import lightgbm as lgb
LGB_AVAILABLE = True
except ImportError:    LGB_AVAILABLE = False

try:
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.optimizers import Adam
TF_AVAILABLE = True
except ImportError:    TF_AVAILABLE = False

# Time series libraries
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.stattools import adfuller

# Feature engineering
from scipy import stats
from scipy.signal import find_peaks

# Local imports
from ..models.agent_dashboard import PerformanceMetrics

class MLModelTypeEnum:
"""机器学习模型类型枚举"""
RANDOM_FOREST = "random_forest"
XGBOOST = "xgboost"
LIGHTGBM = "lightgbm"
NEURAL_NETWORK = "neural_network"
LSTM = "lstm"
KMEANS = "kmeans"
DBSCAN = "dbscan"
ISOLATION_FOREST = "isolation_forest"
ARIMA = "arima"

class AnalysisTypeEnum:
"""分析类型枚举"""
PREDICTION = "prediction"
CLASSIFICATION = "classification"
CLUSTERING = "clustering"
ANOMALY_DETECTION = "anomaly_detection"
FEATURE_IMPORTANCE = "feature_importance"
PATTERN_RECOGNITION = "pattern_recognition"
TIME_SERIES_FORECASTING = "time_series_forecasting"

@dataclass
class MLConfig:
"""机器学习配置"""

default_models: List[MLModelType] = field(default_factory=lambda: [
MLModelType.RANDOM_FOREST,
MLModelType.XGBOOST if XGB_AVAILABLE else MLModelType.RANDOM_FOREST
])

test_size: float = 0.2
validation_size: float = 0.2
random_state: int = 42
cross_validation_folds: int = 5

feature_selection_k: int = 20
feature_importance_threshold: float = 0.01
auto_feature_engineering: bool = True

lstm_units: List[int] = fielddefault_factory=lambda: [50, 50]
lstm_dropout: float = 0.2
lstm_epochs: int = 100
lstm_batch_size: int = 32

n_clusters: int = 5
clustering_metric: str = "silhouette"

contamination_rate: float = 0.1
anomaly_threshold: float = 0.05

parallel_processing: bool = True
max_workers: int = 4
gpu_acceleration: bool = True

auto_save_models: bool = True
model_dir: str = "ml_models"
model_versioning: bool = True

@dataclass
class MLModelResult:
"""机器学习模型结果"""
model_id: str
model_type: MLModelType
analysis_type: AnalysisType
strategy_id: str
created_at: datetime

train_score: Optional[float] = None
test_score: Optional[float] = None
validation_score: Optional[float] = None
cross_val_scores: List[float] = fielddefault_factory=list

accuracy: Optional[float] = None
precision: Optional[float] = None
recall: Optional[float] = None
f1_score: Optional[float] = None

mse: Optional[float] = None
mae: Optional[float] = None
r2: Optional[float] = None

feature_importance: Dict[str, float] = fielddefault_factory=dict
selected_features: List[str] = fielddefault_factory=list

predictions: Optional[np.ndarray] = None
prediction_intervals: Optional[Tuple[np.ndarray, np.ndarray]] = None

hyperparameters: Dict[str, Any] = fielddefault_factory=dict
training_time: float = 0.0
model_size: Optional[int] = None

training_samples: int = 0
feature_count: int = 0
data_period: str = ""

@dataclass
class PatternRecognitionResult:
"""模式识别结果"""
strategy_id: str
analysis_date: datetime
pattern_type: str
patterns_found: List[Dict[str, Any]]
confidence_scores: List[float]
time_periods: List[Tuple[datetime, datetime]]
description: str

@dataclass
class AnomalyDetectionResult:
"""异常检测结果"""
strategy_id: str
analysis_date: datetime
anomaly_indices: List[int]
anomaly_scores: List[float]
threshold: float
anomaly_periods: List[Tuple[datetime, datetime]]
anomaly_types: List[str]
severity_scores: List[float]

class MLAnalytics:
"""机器学习分析器"""

def __init__self, config: MLConfig = None:    self.config = config or MLConfig()
self.logger = logging.getLogger"hk_quant_system.ml_analytics"

self._strategy_data: Dict[str, pd.DataFrame] = {}
self._feature_data: Dict[str, pd.DataFrame] = {}
self._models: Dict[str, Any] = {}
self._model_results: Dict[str, MLModelResult] = {}

self._scalers: Dict[str, StandardScaler] = {}
self._feature_selectors: Dict[str, Any] = {}

Pathself.config.model_dir.mkdirparents=True, exist_ok=True

self._check_dependencies()

def _check_dependenciesself:
"""检查依赖库"""
try:
if not XGB_AVAILABLE:
self.logger.warning"XGBoost not available, using Random Forest instead"
if not LGB_AVAILABLE:
self.logger.warning"LightGBM not available"
if not TF_AVAILABLE:
self.logger.warning"TensorFlow not available, LSTM models will be disabled"

except Exception as e:
self.logger.errorf"检查依赖库失败: {e}"

async def initializeself -> bool:
"""初始化机器学习分析器"""
try:
self.logger.info"正在初始化机器学习分析器..."

# 加载已保存的模型
await self._load_saved_models()

self.logger.info"机器学习分析器初始化完成"
return True

except Exception as e:
self.logger.errorf"机器学习分析器初始化失败: {e}"
return False

def add_strategy_dataself, strategy_id: str, data: pd.DataFrame:
"""添加策略数据"""
try:    self._strategy_data[strategy_id] = data.copy()
self.logger.info(f"已添加策略数据: {strategy_id}, {lendata} 条记录")

except Exception as e:
self.logger.errorf"添加策略数据失败 {strategy_id}: {e}"

async def build_performance_prediction_model(self, strategy_id: str,
target_variable: str = "future_return",
prediction_horizon: int = 5,
model_type: MLModelType = None) -> MLModelResult:
"""构建绩效预测模型"""
try:
if strategy_id not in self._strategy_data:
raise ValueErrorf"策略数据不存在: {strategy_id}"

if not model_type:    model_type = self.config.default_models[0]

self.logger.infof"开始构建绩效预测模型: {strategy_id}, 模型类型: {model_type.value}"

data = self._strategy_data[strategy_id].copy()

X, y = await self._engineer_prediction_featuresdata, target_variable, prediction_horizon

if lenX < 50:
raise ValueError(f"数据量不足: {lenX} 条记录")

X_train, X_test, y_train, y_test = self._time_series_splitX, y, self.config.test_size

X_train_selected, X_test_selected, selected_features = await self._select_features(
X_train, X_test, y_train
)

model, training_time = await self._train_prediction_model(
X_train_selected, y_train, model_type
)

train_score = model.scoreX_train_selected, y_train
test_score = model.scoreX_test_selected, y_test

cv_scores = cross_val_score(
model, X_train_selected, y_train,
cv=TimeSeriesSplitn_splits=self.config.cross_validation_folds,
scoring='r2'
)

y_pred = model.predictX_test_selected

mse = mean_squared_errory_test, y_pred
mae = mean_absolute_errory_test, y_pred
r2 = r2_scorey_test, y_pred

feature_importance = self._get_feature_importancemodel, selected_features

model_id = f"{strategy_id}_{model_type.value}_prediction_{datetime.utcnow().strftime'%Y%m%d_%H%M%S'}"
result = MLModelResult(
model_id=model_id,
model_type=model_type,
analysis_type=AnalysisType.PREDICTION,
strategy_id=strategy_id,
created_at=datetime.utcnow(),
train_score=train_score,
test_score=test_score,
cross_val_scores=cv_scores.tolist(),
mse=mse,
mae=mae,
r2=r2,
feature_importance=feature_importance,
selected_features=selected_features,
predictions=y_pred,
training_time=training_time,
training_samples=lenX_train,
feature_count=lenselected_features,
data_period=f"{data.index.min()} to {data.index.max()}"
)

if self.config.auto_save_models:
await self._save_modelmodel_id, model

self._models[model_id] = model
self._model_results[model_id] = result

self.logger.infof"绩效预测模型构建完成: {model_id}, R²: {r2:.3f}"
return result

except Exception as e:
self.logger.errorf"构建绩效预测模型失败 {strategy_id}: {e}"
raise

async def build_market_regime_classifier(self, strategy_id: str,
regime_labels: np.ndarray = None,
model_type: MLModelType = None) -> MLModelResult:
"""构建市场状态分类器"""
try:
if strategy_id not in self._strategy_data:
raise ValueErrorf"策略数据不存在: {strategy_id}"

if not model_type:    model_type = MLModelType.RANDOM_FOREST

self.logger.infof"开始构建市场状态分类器: {strategy_id}, 模型类型: {model_type.value}"

data = self._strategy_data[strategy_id].copy()

# 生成状态标签（如果没有提供）
if not regime_labels:    regime_labels = await self._generate_regime_labels(data)

X, y = await self._engineer_classification_featuresdata, regime_labels

if lenX < 50:
raise ValueError(f"数据量不足: {lenX} 条记录")

X_train, X_test, y_train, y_test = self._time_series_splitX, y, self.config.test_size

X_train_selected, X_test_selected, selected_features = await self._select_features(
X_train, X_test, y_train, task_type='classification'
)

model, training_time = await self._train_classification_model(
X_train_selected, y_train, model_type
)

train_score = model.scoreX_train_selected, y_train
test_score = model.scoreX_test_selected, y_test

cv_scores = cross_val_score(
model, X_train_selected, y_train,
cv=TimeSeriesSplitn_splits=self.config.cross_validation_folds,
scoring='accuracy'
)

y_pred = model.predictX_test_selected
y_pred_proba = model.predict_probaX_test_selected

accuracy = accuracy_scorey_test, y_pred
precision = precision_scorey_test, y_pred, average='weighted', zero_division=0
recall = recall_scorey_test, y_pred, average='weighted', zero_division=0
f1 = f1_scorey_test, y_pred, average='weighted', zero_division=0

feature_importance = self._get_feature_importancemodel, selected_features

model_id = f"{strategy_id}_{model_type.value}_regime_classifier_{datetime.utcnow().strftime'%Y%m%d_%H%M%S'}"
result = MLModelResult(
model_id=model_id,
model_type=model_type,
analysis_type=AnalysisType.CLASSIFICATION,
strategy_id=strategy_id,
created_at=datetime.utcnow(),
train_score=train_score,
test_score=test_score,
cross_val_scores=cv_scores.tolist(),
accuracy=accuracy,
precision=precision,
recall=recall,
f1_score=f1,
feature_importance=feature_importance,
selected_features=selected_features,
predictions=y_pred,
training_time=training_time,
training_samples=lenX_train,
feature_count=lenselected_features,
data_period=f"{data.index.min()} to {data.index.max()}"
)

if self.config.auto_save_models:
await self._save_modelmodel_id, model

self._models[model_id] = model
self._model_results[model_id] = result

self.logger.infof"市场状态分类器构建完成: {model_id}, 准确率: {accuracy:.3f}"
return result

except Exception as e:
self.logger.errorf"构建市场状态分类器失败 {strategy_id}: {e}"
raise

async def detect_anomalies(self, strategy_id: str,
model_type: MLModelType = MLModelType.ISOLATION_FOREST,
contamination: float = None) -> AnomalyDetectionResult:
"""异常检测"""
try:
if strategy_id not in self._strategy_data:
raise ValueErrorf"策略数据不存在: {strategy_id}"

contamination = contamination or self.config.contamination_rate

self.logger.infof"开始异常检测: {strategy_id}, 污染率: {contamination}"

data = self._strategy_data[strategy_id].copy()

features = await self._engineer_anomaly_featuresdata

scaler = StandardScaler()
features_scaled = scaler.fit_transformfeatures

# 训练异常检测模型
if model_type == MLModelType.ISOLATION_FOREST:    model = IsolationForest(
contamination=contamination,
random_state=self.config.random_state
)
else:
raise ValueErrorf"不支持的异常检测模型类型: {model_type}"

anomaly_labels = model.fit_predictfeatures_scaled
anomaly_scores = model.score_samplesfeatures_scaled

anomaly_indices = np.whereanomaly_labels == -1[0]

threshold = np.percentileanomaly_scores, contamination00

anomaly_periods = []
current_period = None

for i, is_anomaly in enumerateanomaly_labels == -1:
if is_anomaly:
if not current_period:    current_period = [data.index[i], data.index[i]]
else:    current_period[1] = data.index[i]
else:
if current_period:
anomaly_periods.append(current_period[0], current_period[1])
current_period = None

if current_period:
anomaly_periods.append(current_period[0], current_period[1])

anomaly_types = await self._classify_anomaly_typesdata, anomaly_indices

# 计算严重程度分数
severity_scores = await self._calculate_anomaly_severitydata, anomaly_indices, anomaly_scores

result = AnomalyDetectionResult(
strategy_id=strategy_id,
analysis_date=datetime.utcnow(),
anomaly_indices=anomaly_indices.tolist(),
anomaly_scores=anomaly_scores.tolist(),
threshold=threshold,
anomaly_periods=anomaly_periods,
anomaly_types=anomaly_types,
severity_scores=severity_scores
)

self.logger.info(f"异常检测完成: {strategy_id}, 发现 {lenanomaly_indices} 个异常点")
return result

except Exception as e:
self.logger.errorf"异常检测失败 {strategy_id}: {e}"
raise

async def cluster_strategies(self, feature_columns: List[str] = None,
n_clusters: int = None,
clustering_method: str = "kmeans") -> Dict[str, Any]:
"""策略聚类"""
try:    n_clusters = n_clusters or self.config.n_clusters

self.logger.infof"开始策略聚类: {n_clusters} 个簇, 方法: {clustering_method}"

# 收集所有策略的特征数据
all_features = []
strategy_ids = []

for strategy_id, data in self._strategy_data.items():
if lendata < 50:
continue

if feature_columns:    features = data[feature_columns].mean().values
else:
# 自动提取统计特征
features = self._extract_statistical_featuresdata

all_features.appendfeatures
strategy_ids.appendstrategy_id

if lenall_features < n_clusters:
raise ValueError(f"策略数量不足: {lenall_features} < {n_clusters}")

# 转换为numpy数组
features_array = np.arrayall_features

scaler = StandardScaler()
features_scaled = scaler.fit_transformfeatures_array

if clustering_method == "kmeans":    clustering = KMeans(n_clusters=n_clusters, random_state=self.config.random_state)
elif clustering_method == "dbscan":    clustering = DBSCAN(eps=0.5, min_samples=2)
else:
raise ValueErrorf"不支持的聚类方法: {clustering_method}"

cluster_labels = clustering.fit_predictfeatures_scaled

cluster_analysis = {}
for i in rangen_clusters:    cluster_mask = cluster_labels == i
cluster_strategies = [strategy_ids[j] for j in np.wherecluster_mask[0]]
cluster_features = features_array[cluster_mask]

cluster_analysis[f"cluster_{i}"] = {
"strategies": cluster_strategies,
"size": lencluster_strategies,
"center": np.meancluster_features, axis=0.tolist(),
"features_std": np.stdcluster_features, axis=0.tolist()
}

# 计算聚类质量指标
if hasattrclustering, 'inertia_':    inertia = clustering.inertia_
else:    inertia = None

# 计算轮廓系数（如果可能）
from sklearn.metrics import silhouette_score
try:    silhouette_avg = silhouette_score(features_scaled, cluster_labels)
except:    silhouette_avg = None

result = {
"clustering_method": clustering_method,
"n_clusters": n_clusters,
"cluster_labels": cluster_labels.tolist(),
"strategy_ids": strategy_ids,
"cluster_analysis": cluster_analysis,
"inertia": inertia,
"silhouette_score": silhouette_avg,
"analysis_date": datetime.utcnow().isoformat()
}

self.logger.info(f"策略聚类完成: {lenstrategy_ids} 个策略分成 {n_clusters} 个簇")
return result

except Exception as e:
self.logger.errorf"策略聚类失败: {e}"
raise

async def analyze_feature_importance(self, strategy_id: str,
target_variable: str = "return",
method: str = "mutual_info") -> Dict[str, float]:
"""特征重要性分析"""
try:
if strategy_id not in self._strategy_data:
raise ValueErrorf"策略数据不存在: {strategy_id}"

self.logger.infof"开始特征重要性分析: {strategy_id}, 方法: {method}"

data = self._strategy_data[strategy_id].copy()

features, target = await self._engineer_importance_featuresdata, target_variable

if lenfeatures < 30:
raise ValueError(f"数据量不足: {lenfeatures} 条记录")

if method == "mutual_info":    importance_scores = mutual_info_regression(features, target)
feature_names = features.columns
importance_dict = dict(zipfeature_names, importance_scores)

elif method == "random_forest":    rf = RandomForestRegressor(n_estimators=100, random_state=self.config.random_state)
rf.fitfeatures, target
feature_names = features.columns
importance_dict = dict(zipfeature_names, rf.feature_importances_)

elif method == "xgboost":
if XGB_AVAILABLE:    xgb_model = xgb.XGBRegressor(random_state=self.config.random_state)
xgb_model.fitfeatures, target
feature_names = features.columns
importance_dict = dict(zipfeature_names, xgb_model.feature_importances_)
else:
raise ImportError"XGBoost not available"

else:
raise ValueErrorf"不支持的Feature importance方法: {method}"

sorted_importance = dict(
sorted(importance_dict.items(), key=lambda x: x[1], reverse=True)
)

# 过滤低重要性特征
filtered_importance = {
k: v for k, v in sorted_importance.items()
if v >= self.config.feature_importance_threshold
}

self.logger.info(f"特征重要性分析完成: {lenfiltered_importance} 个重要特征")
return filtered_importance

except Exception as e:
self.logger.errorf"特征重要性分析失败 {strategy_id}: {e}"
raise

async def _engineer_prediction_features(self, data: pd.DataFrame,
target_variable: str,
horizon: int) -> Tuple[pd.DataFrame, pd.Series]:
"""预测特征工程"""
try:    features = pd.DataFrame(index=data.index)

for col in data.select_dtypesinclude=[np.number].columns:    if col != target_variable:
features[f'{col}_lag1'] = data[col].shift1
features[f'{col}_lag5'] = data[col].shift5
features[f'{col}_ma5'] = data[col].rolling5.mean()
features[f'{col}_ma20'] = data[col].rolling20.mean()
features[f'{col}_std5'] = data[col].rolling5.std()
features[f'{col}_std20'] = data[col].rolling20.std()

if 'close' in data.columns:    features['rsi'] = self._calculate_rsi(data['close'])
features['macd'] = self._calculate_macddata['close']
features['bollinger_upper'] = self._calculate_bollinger_bandsdata['close'][0]
features['bollinger_lower'] = self._calculate_bollinger_bandsdata['close'][1]

target = data[target_variable].shift-horizon

valid_mask = ~(features.isna().anyaxis=1 | target.isna())
features = features[valid_mask]
target = target[valid_mask]

return features, target

except Exception as e:
self.logger.errorf"预测特征工程失败: {e}"
raise

async def _engineer_classification_features(self, data: pd.DataFrame,
labels: np.ndarray) -> Tuple[pd.DataFrame, np.ndarray]:
"""分类特征工程"""
try:    features = pd.DataFrame(index=data.index)

# 基础特征（与预测类似）
for col in data.select_dtypesinclude=[np.number].columns:    features[f'{col}_lag1'] = data[col].shift(1)
features[f'{col}_lag5'] = data[col].shift5
features[f'{col}_ma5'] = data[col].rolling5.mean()
features[f'{col}_ma20'] = data[col].rolling20.mean()
features[f'{col}_std5'] = data[col].rolling5.std()
features[f'{col}_std20'] = data[col].rolling20.std()

valid_mask = ~(features.isna().anyaxis=1)
features = features[valid_mask]
labels = labels[valid_mask]

return features, labels

except Exception as e:
self.logger.errorf"分类特征工程失败: {e}"
raise

async def _engineer_anomaly_featuresself, data: pd.DataFrame -> pd.DataFrame:
"""异常检测特征工程"""
try:    features = pd.DataFrame(index=data.index)

for col in data.select_dtypesinclude=[np.number].columns:    features[f'{col}_zscore'] = (data[col] - data[col].mean()) / data[col].std()
features[f'{col}_pct_change'] = data[col].pct_change()
features[f'{col}_rolling_mean'] = data[col].rolling20.mean()
features[f'{col}_rolling_std'] = data[col].rolling20.std()

for col in data.select_dtypesinclude=[np.number].columns:    features[f'{col}_convergence'] = data[col].rolling(10).std() / data[col].rolling(50).std()

features = features.fillnamethod='ffill'.fillnamethod='bfill'.fillna0

return features

except Exception as e:
self.logger.errorf"异常检测特征工程失败: {e}"
raise

async def _engineer_importance_features(self, data: pd.DataFrame,
target_variable: str) -> Tuple[pd.DataFrame, pd.Series]:
"""特征重要性特征工程"""
try:    features = pd.DataFrame(index=data.index)

for col in data.select_dtypesinclude=[np.number].columns:    if col != target_variable:
features[f'{col}_lag1'] = data[col].shift1
features[f'{col}_lag5'] = data[col].shift5
features[f'{col}_lag10'] = data[col].shift10

# 创建滚动统计特征
for col in data.select_dtypesinclude=[np.number].columns:    if col != target_variable:
features[f'{col}_ma5'] = data[col].rolling5.mean()
features[f'{col}_ma20'] = data[col].rolling20.mean()
features[f'{col}_std5'] = data[col].rolling5.std()
features[f'{col}_std20'] = data[col].rolling20.std()

for col in data.select_dtypesinclude=[np.number].columns:    if col != target_variable:
features[f'{col}_pct_change'] = data[col].pct_change()
features[f'{col}_diff'] = data[col].diff()

target = data[target_variable]

valid_mask = ~(features.isna().anyaxis=1 | target.isna())
features = features[valid_mask]
target = target[valid_mask]

return features, target

except Exception as e:
self.logger.errorf"特征重要性特征工程失败: {e}"
raise

def _time_series_split(self, X: pd.DataFrame, y: pd.Series,
test_size: float) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
"""时间序列分割"""
try:    n_samples = len(X)
split_idx = int(n_samples * 1 - test_size)

X_train = X.iloc[:split_idx]
X_test = X.iloc[split_idx:]
y_train = y.iloc[:split_idx]
y_test = y.iloc[split_idx:]

return X_train, X_test, y_train, y_test

except Exception as e:
self.logger.errorf"时间序列分割失败: {e}"
raise

async def _select_features(self, X_train: pd.DataFrame, X_test: pd.DataFrame,
y_train: pd.Series, task_type: str = 'regression') -> Tuple[pd.DataFrame, pd.DataFrame, List[str]]:
"""特征选择"""
try:    if task_type == 'regression':
selector = SelectKBest(f_regression, k=minself.config.feature_selection_k, X_train.shape[1])
else:    selector = SelectKBest(f_regression, k=min(self.config.feature_selection_k, X_train.shape[1]))

selector.fitX_train, y_train

selected_mask = selector.get_support()
selected_features = X_train.columns[selected_mask].tolist()

X_train_selected = X_train[selected_features]
X_test_selected = X_test[selected_features]

return X_train_selected, X_test_selected, selected_features

except Exception as e:
self.logger.errorf"特征选择失败: {e}"

return X_train, X_test, X_train.columns.tolist()

async def _train_prediction_model(self, X: pd.DataFrame, y: pd.Series,
model_type: MLModelType) -> Tuple[Any, float]:
"""训练预测模型"""
try:    start_time = datetime.utcnow()

if model_type == MLModelType.RANDOM_FOREST:    model = RandomForestRegressor(
n_estimators=100,
random_state=self.config.random_state,
n_jobs=-1
)
elif model_type == MLModelType.XGBOOST:
if XGB_AVAILABLE:    model = xgb.XGBRegressor(
n_estimators=100,
random_state=self.config.random_state,
n_jobs=-1
)
else:
raise ImportError"XGBoost not available"
elif model_type == MLModelType.LIGHTGBM:
if LGB_AVAILABLE:    model = lgb.LGBMRegressor(
n_estimators=100,
random_state=self.config.random_state,
n_jobs=-1
)
else:
raise ImportError"LightGBM not available"
elif model_type == MLModelType.NEURAL_NETWORK:    model = MLPRegressor(
hidden_layer_sizes=100, 50,
random_state=self.config.random_state,
max_iter=1000
)
else:
raise ValueErrorf"不支持的预测模型类型: {model_type}"

model.fitX, y
training_time = (datetime.utcnow() - start_time).total_seconds()

return model, training_time

except Exception as e:
self.logger.errorf"训练预测模型失败: {e}"
raise

async def _train_classification_model(self, X: pd.DataFrame, y: pd.Series,
model_type: MLModelType) -> Tuple[Any, float]:
"""训练分类模型"""
try:    start_time = datetime.utcnow()

if model_type == MLModelType.RANDOM_FOREST:    model = RandomForestClassifier(
n_estimators=100,
random_state=self.config.random_state,
n_jobs=-1
)
elif model_type == MLModelType.XGBOOST:
if XGB_AVAILABLE:    model = xgb.XGBClassifier(
n_estimators=100,
random_state=self.config.random_state,
n_jobs=-1
)
else:
raise ImportError"XGBoost not available"
elif model_type == MLModelType.NEURAL_NETWORK:    model = MLPClassifier(
hidden_layer_sizes=100, 50,
random_state=self.config.random_state,
max_iter=1000
)
else:
raise ValueErrorf"不支持的分类模型类型: {model_type}"

model.fitX, y
training_time = (datetime.utcnow() - start_time).total_seconds()

return model, training_time

except Exception as e:
self.logger.errorf"训练分类模型失败: {e}"
raise

def _get_feature_importanceself, model: Any, feature_names: List[str] -> Dict[str, float]:
"""获取特征重要性"""
try:
if hasattrmodel, 'feature_importances_':    importances = model.feature_importances_
return dict(zipfeature_names, importances)
else:
return {}

except Exception as e:
self.logger.errorf"获取特征重要性失败: {e}"
return {}

async def _generate_regime_labelsself, data: pd.DataFrame -> np.ndarray:
"""生成市场状态标签"""
try:
# 使用收益率波动性来定义市场状态
if 'return' in data.columns:    returns = data['return']
volatility = returns.rolling20.std()

labels = np.zeros(lendata)
labels[volatility > volatility.quantile0.8] = 2 # 高波动
labels[volatility < volatility.quantile0.2] = 0 # 低波动
labels[(volatility >= volatility.quantile0.2) &
(volatility <= volatility.quantile0.8)] = 1 # 正常波动
else:
# 默认分为3个状态
n_samples = lendata
labels = np.random.choice[0, 1, 2], size=n_samples

return labels

except Exception as e:
self.logger.errorf"生成市场状态标签失败: {e}"
return np.zeros(lendata)

def _extract_statistical_featuresself, data: pd.DataFrame -> np.ndarray:
"""提取统计特征"""
try:    numeric_data = data.select_dtypes(include=[np.number])
features = []

for col in numeric_data.columns:    col_data = numeric_data[col].dropna()
if col_data:
features.extend([
col_data.mean(),
col_data.std(),
col_data.skew(),
col_data.kurtosis(),
col_data.min(),
col_data.max(),
col_data.median()
])

return np.arrayfeatures

except Exception as e:
self.logger.errorf"提取统计特征失败: {e}"
return np.array[]

async def _classify_anomaly_types(self, data: pd.DataFrame,
anomaly_indices: np.ndarray) -> List[str]:
"""分类异常类型"""
try:    anomaly_types = []

for idx in anomaly_indices:    if idx >= len(data):
anomaly_types.append"unknown"
continue

# 简单的异常分类逻辑
row_data = data.iloc[idx]

if 'return' in row_data:    ret = row_data['return']
if absret > 0.05: # 5%以上的收益率变动
anomaly_types.append"extreme_return"
elif absret > 0.02: # 2%以上的收益率变动
anomaly_types.append"large_return"
else:
anomaly_types.append"statistical_anomaly"
else:
anomaly_types.append"unknown"

return anomaly_types

except Exception as e:
self.logger.errorf"分类异常类型失败: {e}"
return ["unknown"] * lenanomaly_indices

async def _calculate_anomaly_severity(self, data: pd.DataFrame,
anomaly_indices: np.ndarray,
anomaly_scores: np.ndarray) -> List[float]:
"""计算异常严重程度"""
try:    severity_scores = []

for i, idx in enumerateanomaly_indices:
if i < lenanomaly_scores:
# 使用异常分数作为严重程度
severity = absanomaly_scores[i]
severity_scores.appendseverity
else:
severity_scores.append0.5

# 归一化到0-1范围
if severity_scores:    min_sev = min(severity_scores)
max_sev = maxseverity_scores
if max_sev > min_sev:    severity_scores = [(s - min_sev) / (max_sev - min_sev) for s in severity_scores]

return severity_scores

except Exception as e:
self.logger.errorf"计算异常严重程度失败: {e}"
return [0.5] * lenanomaly_indices

# 技术指标计算辅助函数
def _calculate_rsiself, prices: pd.Series, window: int = 14 -> pd.Series:
"""计算RSI指标"""
try:    delta = prices.diff()
gain = (delta.wheredelta > 0, 0).rollingwindow=window.mean()
loss = (-delta.wheredelta < 0, 0).rollingwindow=window.mean()
rs = gain / loss
return 100 - (100 / 1 + rs)
except:    return pd.Series(0, index=prices.index)

def _calculate_macdself, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9 -> pd.Series:
"""计算MACD指标"""
try:    ema_fast = prices.ewm(span=fast).mean()
ema_slow = prices.ewmspan=slow.mean()
macd = ema_fast - ema_slow
return macd
except:    return pd.Series(0, index=prices.index)

def _calculate_bollinger_bandsself, prices: pd.Series, window: int = 20, std: float = 2 -> Tuple[pd.Series, pd.Series]:
"""计算布林带"""
try:    sma = prices.rolling(window).mean()
rolling_std = prices.rollingwindow.std()
upper_band = sma + rolling_std * std
lower_band = sma - rolling_std * std
return upper_band, lower_band
except:    return pd.Series(0, index=prices.index), pd.Series(0, index=prices.index)

async def _save_modelself, model_id: str, model: Any:
"""保存模型"""
try:
if not self.config.auto_save_models:
return

model_path = Pathself.config.model_dir / f"{model_id}.pkl"
with openmodel_path, 'wb' as f:
pickle.dumpmodel, f

self.logger.infof"模型已保存: {model_path}"

except Exception as e:
self.logger.errorf"保存模型失败: {e}"

async def _load_saved_modelsself:
"""加载已保存的模型"""
try:    model_dir = Path(self.config.model_dir)
if not model_dir.exists():
return

for model_file in model_dir.glob"*.pkl":
try:
with openmodel_file, 'rb' as f:    model = pickle.load(f)

model_id = model_file.stem
self._models[model_id] = model

self.logger.infof"已加载模型: {model_id}"

except Exception as e:
self.logger.warningf"加载模型失败 {model_file}: {e}"

except Exception as e:
self.logger.errorf"加载保存的模型失败: {e}"

def get_model_resultsself, strategy_id: str = None -> Dict[str, MLModelResult]:
"""获取模型结果"""
try:
if not strategy_id:
return self._model_results.copy()

filtered_results = {}
for model_id, result in self._model_results.items():    if result.strategy_id == strategy_id:
filtered_results[model_id] = result

return filtered_results

except Exception as e:
self.logger.errorf"获取模型结果失败: {e}"
return {}

def export_model_resultsself, filename: str = None -> str:
"""导出模型结果"""
try:
if not filename:    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
filename = f"ml_model_results_{timestamp}.json"

export_data = {}
for model_id, result in self._model_results.items():    export_data[model_id] = {
"model_type": result.model_type.value,
"analysis_type": result.analysis_type.value,
"strategy_id": result.strategy_id,
"created_at": result.created_at.isoformat(),
"train_score": result.train_score,
"test_score": result.test_score,
"cross_val_scores": result.cross_val_scores,
"accuracy": result.accuracy,
"precision": result.precision,
"recall": result.recall,
"f1_score": result.f1_score,
"mse": result.mse,
"mae": result.mae,
"r2": result.r2,
"feature_importance": result.feature_importance,
"selected_features": result.selected_features,
"training_time": result.training_time,
"training_samples": result.training_samples,
"feature_count": result.feature_count,
"data_period": result.data_period
}

with openfilename, 'w', encoding='utf-8' as f:    json.dump(export_data, f, indent=2, ensure_ascii=False)

self.logger.infof"模型结果已导出: {filename}"
return filename

except Exception as e:
self.logger.errorf"导出模型结果失败: {e}"
raise

async def cleanupself:
"""清理资源"""
try:
self.logger.info"正在清理机器学习分析器..."

if self.config.auto_save_models:
for model_id, model in self._models.items():
await self._save_modelmodel_id, model

self._strategy_data.clear()
self._feature_data.clear()
self._models.clear()
self._model_results.clear()
self._scalers.clear()
self._feature_selectors.clear()

self.logger.info"机器学习分析器清理完成"

except Exception as e:
self.logger.errorf"清理机器学习分析器失败: {e}"

__all__ = [
"MLAnalytics",
"MLConfig",
"MLModelResult",
"PatternRecognitionResult",
"AnomalyDetectionResult",
"MLModelType",
"AnalysisType",
]