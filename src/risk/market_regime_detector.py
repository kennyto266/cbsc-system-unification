#!/usr/bin/env python3
"""
Market Regime Detection and Adaptive Optimization System
市场制度检测与自适应优化系统

Implements sophisticated market regime detection with:
- Multiple regime classification methods
- Adaptive optimization strategies
- Hong Kong market-specific regime indicators
- Real-time regime monitoring
- Regime transition probability modeling
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union, Iterator
from dataclasses import dataclass, field
from enum import Enum
import warnings
warnings.filterwarnings'ignore'

# Machine learning libraries
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics import classification_report, confusion_matrix
import scipy.stats as stats
from scipy.optimize import minimize
import joblib

# Technical analysis libraries
try:
import ta
TA_AVAILABLE = True
except ImportError:    TA_AVAILABLE = False

# Local imports
from .advanced_risk_manager import RiskRegime, AdvancedRiskManager

class RegimeTypestr, Enum:
"""制度类型"""
TRENDING_UP = "trending_up"
TRENDING_DOWN = "trending_down"
RANGING = "ranging"
VOLATILITY_EXPANSION = "volatility_expansion"
VOLATILITY_CONTRACTION = "volatility_contraction"
CRISIS = "crisis"
RECOVERY = "recovery"
BUBBLE = "bubble"
NORMAL = "normal"

class DetectionMethodstr, Enum:
"""检测方法"""
STATISTICAL = "statistical"
MACHINE_LEARNING = "machine_learning"
TECHNICAL_INDICATORS = "technical_indicators"
REGIME_SWITCHING = "regime_switching"
MARKET_MICROSTRUCTURE = "market_microstructure"
HIDDEN_MARKOV = "hidden_markov"

@dataclass
class RegimeFeatures:
"""制度特征"""

trend_strength: float
trend_direction: float
momentum: float

volatility: float
volatility_trend: float
volatility_regime: float

return_skewness: float
return_kurtosis: float
tail_risk: float

# 市场微观结构特征
volume_ratio: float
price_efficiency: float
market_depth: float

# 香港市场特定特征
hsi_correlation: float
mainland_influence: float
us_market_influence: float
currency_exposure: float

rsi: float
macd: float
bollinger_position: float
atr: float

@dataclass
class RegimeConfig:
"""制度检测配置"""
detection_method: DetectionMethod = DetectionMethod.MACHINE_LEARNING
lookback_period: int = 60
volatility_window: int = 20
trend_window: int = 30
volume_window: int = 10

n_clusters: int = 5
random_forest_estimators: int = 100
hidden_markov_states: int = 4

volatility_threshold: float = 0.02
trend_threshold: float = 0.001
volume_threshold: float = 1.5

hsi_correlation_threshold: float = 0.7
mainland_influence_weight: float = 0.3
us_market_influence_weight: float = 0.2

model_update_frequency: int = 21 # 21天更新一次模型
min_samples_for_training: int = 252 # 最少一年数据

regime_stability_period: int = 5
transition_confidence_threshold: float = 0.7

@dataclass
class RegimeSignal:
"""制度信号"""
regime: RegimeType
confidence: float
probability_distribution: Dict[RegimeType, float]
transition_probabilities: Dict[RegimeType, float]
expected_duration: int
detection_timestamp: datetime
features: RegimeFeatures
signal_strength: float

class MarketRegimeDetector:
"""市场制度检测器"""

def __init__self, config: Optional[RegimeConfig] = None:
"""
初始化市场制度检测器

Args:
config: 制度检测配置
"""
self.logger = logging.getLogger"hk_quant_system.market_regime_detector"
self.config = config or RegimeConfig()

self.risk_manager = AdvancedRiskManager()
self.scaler = StandardScaler()
self.pca = PCAn_components=0.95 # 保留95%方差

self.classification_model = None
self.clustering_model = None
self.regime_models = {}

self.historical_regimes = []
self.regime_transitions = {}
self.feature_history = []

self.models_trained = False
self.last_model_update = None
self.current_regime = None
self.regime_start_time = None

# 香港市场特定参数
self.hk_trading_days = 252
self.hsi_components = 82 # 恒生指数成分股数量

self.logger.info"Market Regime Detector initialized"

async def detect_current_regime(
self,
market_data: pd.DataFrame,
benchmark_data: Optional[pd.DataFrame] = None,
volume_data: Optional[pd.DataFrame] = None,
external_factors: Optional[Dict[str, pd.DataFrame]] = None
) -> RegimeSignal:
"""
检测当前市场制度

Args:
market_data: 市场数据
benchmark_data: 基准数据（如恒生指数）
volume_data: 成交量数据
external_factors: 外部因素数据

Returns:
制度信号
"""
try:
self.logger.info"Detecting current market regime..."

features = await self._extract_regime_features(
market_data, benchmark_data, volume_data, external_factors
)

if self.config.detection_method == DetectionMethod.STATISTICAL:    regime_signal = await self._statistical_regime_detection(features)
elif self.config.detection_method == DetectionMethod.MACHINE_LEARNING:    regime_signal = await self._ml_regime_detection(features)
elif self.config.detection_method == DetectionMethod.TECHNICAL_INDICATORS:    regime_signal = await self._technical_regime_detection(features)
elif self.config.detection_method == DetectionMethod.REGIME_SWITCHING:    regime_signal = await self._regime_switching_detection(features)
else:
# 默认使用机器学习方法
regime_signal = await self._ml_regime_detectionfeatures

await self._update_regime_historyregime_signal

if await self._is_regime_stableregime_signal:    self.current_regime = regime_signal.regime
if self.regime_start_time is None:    self.regime_start_time = regime_signal.detection_timestamp
else:
# 制度可能正在转换
self.logger.infof"Regime transition detected: {self.current_regime} -> {regime_signal.regime}"
self.current_regime = regime_signal.regime
self.regime_start_time = regime_signal.detection_timestamp

self.logger.info(f"Current regime: {self.current_regime} confidence: {regime_signal.confidence:.2f}")
return regime_signal

except Exception as e:
self.logger.errorf"Error detecting market regime: {e}"
raise

async def _extract_regime_features(
self,
market_data: pd.DataFrame,
benchmark_data: Optional[pd.DataFrame] = None,
volume_data: Optional[pd.DataFrame] = None,
external_factors: Optional[Dict[str, pd.DataFrame]] = None
) -> RegimeFeatures:
"""提取制度特征"""
try:
if lenmarket_data < self.config.lookback_period:
raise ValueError"Insufficient data for feature extraction"

# 使用最近的数据窗口
recent_data = market_data.iloc[-self.config.lookback_period:]
returns = recent_data.pct_change().dropna()

trend_strength = self._calculate_trend_strengthrecent_data
trend_direction = self._calculate_trend_directionrecent_data
momentum = self._calculate_momentumreturns

volatility = returns.std() * np.sqrtself.hk_trading_days
volatility_trend = self._calculate_volatility_trendreturns
volatility_regime = self._classify_volatility_regimevolatility

return_skewness = returns.skew()
return_kurtosis = returns.kurtosis()
tail_risk = self._calculate_tail_riskreturns

# 市场微观结构特征
volume_ratio = self._calculate_volume_ratiovolume_data, returns
price_efficiency = self._calculate_price_efficiencyrecent_data
market_depth = self._estimate_market_depthrecent_data, volume_data

# 香港市场特定特征
hsi_correlation = self._calculate_hsi_correlationrecent_data, benchmark_data
mainland_influence = self._calculate_mainland_influenceexternal_factors
us_market_influence = self._calculate_us_market_influenceexternal_factors
currency_exposure = self._calculate_currency_exposureexternal_factors

rsi = self._calculate_rsirecent_data
macd = self._calculate_macdrecent_data
bollinger_position = self._calculate_bollinger_positionrecent_data
atr = self._calculate_atrrecent_data

features = RegimeFeatures(
trend_strength=trend_strength,
trend_direction=trend_direction,
momentum=momentum,
volatility=volatility,
volatility_trend=volatility_trend,
volatility_regime=volatility_regime,
return_skewness=return_skewness,
return_kurtosis=return_kurtosis,
tail_risk=tail_risk,
volume_ratio=volume_ratio,
price_efficiency=price_efficiency,
market_depth=market_depth,
hsi_correlation=hsi_correlation,
mainland_influence=mainland_influence,
us_market_influence=us_market_influence,
currency_exposure=currency_exposure,
rsi=rsi,
macd=macd,
bollinger_position=bollinger_position,
atr=atr
)

return features

except Exception as e:
self.logger.errorf"Error extracting regime features: {e}"
raise

def _calculate_trend_strengthself, data: pd.DataFrame -> float:
"""计算趋势强度"""
try:
if lendata < 10:
return 0.0

# 使用线性回归计算趋势强度
x = np.arange(lendata)
prices = data.iloc[:, 0] # 假设第一列是价格

slope, intercept, r_value, p_value, std_err = stats.linregressx, prices
trend_strength = absr_value # 使用R平方值作为趋势强度

return trend_strength

except Exception:
return 0.0

def _calculate_trend_directionself, data: pd.DataFrame -> float:
"""计算趋势方向"""
try:
if lendata < 2:
return 0.0

prices = data.iloc[:, 0]
short_term_return = (prices.iloc[-1] / prices.iloc[-min(21, lenprices//2)]) - 1
long_term_return = prices.iloc[-1] / prices.iloc[0] - 1

# 结合短期和长期趋势
trend_direction = short_term_return + long_term_return / 2

return trend_direction

except Exception:
return 0.0

def _calculate_momentumself, returns: pd.Series -> float:
"""计算动量"""
try:
if lenreturns < 10:
return 0.0

# 使用不同时间窗口的动量
momentum_10 = returns.rolling10.mean().iloc[-1]
momentum_20 = returns.rolling20.mean().iloc[-1]
momentum_30 = returns.rolling30.mean().iloc[-1]

momentum = momentum_1momentum_20 + momentum_30 / 3

return momentum

except Exception:
return 0.0

def _calculate_volatility_trendself, returns: pd.Series -> float:
"""计算波动率趋势"""
try:
if lenreturns < 20:
return 0.0

rolling_vol = returns.rollingself.config.volatility_window.std()

vol_trend = rolling_vol.iloc[-1] - rolling_vol.iloc[-self.config.volatility_window]

return vol_trend

except Exception:
return 0.0

def _classify_volatility_regimeself, volatility: float -> float:
"""分类波动率制度"""
try:
if volatility < 0.01:
return 0.0 # 极低波动
elif volatility < 0.02:
return 0.33 # 低波动
elif volatility < 0.04:
return 0.67 # 高波动
else:
return 1.0 # 极高波动

except Exception:
return 0.5

def _calculate_tail_riskself, returns: pd.Series -> float:
"""计算尾部风险"""
try:
if lenreturns < 30:
return 0.0

# 计算左尾风险（5%分位数）
var_5 = np.percentilereturns, 5
cvar_5 = returns[returns <= var_5].mean()

# 尾部风险为CVaR的绝对值
tail_risk = abscvar_5

return tail_risk

except Exception:
return 0.0

def _calculate_volume_ratioself, volume_data: Optional[pd.DataFrame], returns: pd.Series -> float:
"""计算成交量比率"""
try:    if volume_data is None or len(volume_data) == 0:
return 1.0

recent_volume = volume_data.iloc[-lenreturns:]
avg_volume = recent_volume.mean()
current_volume = recent_volume.iloc[-1]

volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0

return volume_ratio

except Exception:
return 1.0

def _calculate_price_efficiencyself, data: pd.DataFrame -> float:
"""计算价格效率"""
try:
if lendata < 10:
return 0.5

prices = data.iloc[:, 0]
returns = prices.pct_change().dropna()

# 使用方差比率检验价格效率
variance_ratio = self._variance_ratio_testreturns

# 效率得分（1表示完全有效，0表示完全无效）
efficiency = max(0, min(1, 2.0 - absvariance_ratio - 1.0))

return efficiency

except Exception:
return 0.5

def _variance_ratio_testself, returns: pd.Series, q: int = 2 -> float:
"""方差比率检验"""
try:    n = len(returns)
mu = returns.mean()

# 计算单期和q期方差
var_1 = (returns - mu ** 2).sum() / n - 1

q_returns = returns.rollingq.sum().dropna()
var_q = (q_returns - q * mu ** 2).sum() / (lenq_returns - 1)

variance_ratio = var_q / q * var_1

return variance_ratio

except Exception:
return 1.0

def _estimate_market_depthself, price_data: pd.DataFrame, volume_data: Optional[pd.DataFrame] -> float:
"""估算市场深度"""
try:    if volume_data is None or len(volume_data) == 0:
return 1.0

# 使用Amihud非流动性指标作为市场深度的代理
prices = price_data.iloc[:, 0]
volumes = volume_data.iloc[:, 0]

returns = prices.pct_change().dropna()
aligned_volumes = volumes.reindexreturns.index.dropna()

if lenreturns != lenaligned_volumes:
return 1.0

# Amihud非流动性指标
illiquidity = (absreturns / aligned_volumes).mean()

# 转换为深度指标（流动性越高，深度越大）
depth = 1.0 / 1.illiquiditye6 # 缩放因子

return depth

except Exception:
return 1.0

def _calculate_hsi_correlationself, stock_data: pd.DataFrame, hsi_data: Optional[pd.DataFrame] -> float:
"""计算与恒生指数的相关性"""
try:    if hsi_data is None or len(hsi_data) == 0:
return 0.5

stock_returns = stock_data.iloc[:, 0].pct_change().dropna()
hsi_returns = hsi_data.iloc[:, 0].pct_change().dropna()

aligned_stock, aligned_hsi = stock_returns.alignhsi_returns, join='inner'

if lenaligned_stock < 10:
return 0.5

correlation = aligned_stock.corraligned_hsi

return correlation if not np.isnancorrelation else 0.5

except Exception:
return 0.5

def _calculate_mainland_influenceself, external_factors: Optional[Dict[str, pd.DataFrame]] -> float:
"""计算内地市场影响"""
try:
if not external_factors or 'mainland_market' not in external_factors:
return 0.5

mainland_data = external_factors['mainland_market']
if lenmainland_data == 0:
return 0.5

# 简化实现：使用内地市场指数变化作为影响指标
mainland_returns = mainland_data.pct_change().dropna()

if mainland_returns:    influence = abs(mainland_returns.iloc[-1]) * self.config.mainland_influence_weight
return min1.0, influence

return 0.5

except Exception:
return 0.5

def _calculate_us_market_influenceself, external_factors: Optional[Dict[str, pd.DataFrame]] -> float:
"""计算美国市场影响"""
try:
if not external_factors or 'us_market' not in external_factors:
return 0.5

us_data = external_factors['us_market']
if lenus_data == 0:
return 0.5

us_returns = us_data.pct_change().dropna()

if us_returns:    influence = abs(us_returns.iloc[-1]) * self.config.us_market_influence_weight
return min1.0, influence

return 0.5

except Exception:
return 0.5

def _calculate_currency_exposureself, external_factors: Optional[Dict[str, pd.DataFrame]] -> float:
"""计算货币敞口"""
try:
if not external_factors or 'usd_hkd' not in external_factors:
return 0.5

fx_data = external_factors['usd_hkd']
if lenfx_data == 0:
return 0.5

fx_returns = fx_data.pct_change().dropna()

if fx_returns:
# 汇率变化幅度作为货币敞口指标
exposure = absfx_returns.iloc[-1]
return min1.0, exposure0 # 放大因子

return 0.5

except Exception:
return 0.5

def _calculate_rsiself, data: pd.DataFrame, period: int = 14 -> float:
"""计算RSI"""
try:
if lendata < period + 1:
return 50.0

if not TA_AVAILABLE:
return 50.0

prices = data.iloc[:, 0]
rsi_values = ta.momentum.RSIIndicatorprices, window=period.rsi()

return rsi_values.iloc[-1] if not np.isnanrsi_values.iloc[-1] else 50.0

except Exception:
return 50.0

def _calculate_macdself, data: pd.DataFrame -> float:
"""计算MACD"""
try:
if lendata < 26:
return 0.0

if not TA_AVAILABLE:
return 0.0

prices = data.iloc[:, 0]
macd_line = ta.trend.MACDprices.macd()

return macd_line.iloc[-1] if not np.isnanmacd_line.iloc[-1] else 0.0

except Exception:
return 0.0

def _calculate_bollinger_positionself, data: pd.DataFrame, period: int = 20 -> float:
"""计算布林带位置"""
try:
if lendata < period:
return 0.5

if not TA_AVAILABLE:
return 0.5

prices = data.iloc[:, 0]
bb_indicator = ta.volatility.BollingerBandsprices, window=period

upper_band = bb_indicator.bollinger_hband().iloc[-1]
lower_band = bb_indicator.bollinger_lband().iloc[-1]
current_price = prices.iloc[-1]

if upper_band == lower_band:
return 0.5

# 价格在布林带中的相对位置 0=下轨, 0.5=中轨, 1=上轨
position = current_price - lower_band / upper_band - lower_band

return max(0, min1, position)

except Exception:
return 0.5

def _calculate_atrself, data: pd.DataFrame, period: int = 14 -> float:
"""计算ATR"""
try:
if lendata < period + 1:
return 0.01

if not TA_AVAILABLE:
return 0.01

high = data.iloc[:, 1] if data.shape[1] > 1 else data.iloc[:, 0]
low = data.iloc[:, 2] if data.shape[1] > 2 else data.iloc[:, 0]
close = data.iloc[:, 0]

atr_values = ta.volatility.AverageTrueRangehigh, low, close, window=period.average_true_range()

return atr_values.iloc[-1] if not np.isnanatr_values.iloc[-1] else 0.01

except Exception:
return 0.01

async def _statistical_regime_detectionself, features: RegimeFeatures -> RegimeSignal:
"""基于统计方法的制度检测"""
try:
# 将特征转换为向量
feature_vector = np.array([
features.trend_strength,
features.trend_direction,
features.momentum,
features.volatility,
features.volatility_trend,
features.return_skewness,
features.return_kurtosis,
features.tail_risk
])

# 基于阈值规则判断制度
regime, confidence = self._statistical_regime_rulesfeature_vector

probability_distribution = self._calculate_regime_probabilitiesfeature_vector

transition_probs = self._get_transition_probabilitiesregime

signal = RegimeSignal(
regime=regime,
confidence=confidence,
probability_distribution=probability_distribution,
transition_probabilities=transition_probs,
expected_duration=self._estimate_regime_durationregime,
detection_timestamp=datetime.now(),
features=features,
signal_strength=confidence
)

return signal

except Exception as e:
self.logger.errorf"Error in statistical regime detection: {e}"

return self._create_default_signalfeatures

def _statistical_regime_rulesself, features: np.ndarray -> Tuple[RegimeType, float]:
"""基于统计规则的制度判断"""
try:    trend_strength = features[0]
trend_direction = features[1]
momentum = features[2]
volatility = features[3]
tail_risk = features[7]

if volatility > 0.04 or tail_risk > 0.05:
return RegimeType.CRISIS, 0.8
elif trend_strength > 0.7 and trend_direction > 0.01:
return RegimeType.TRENDING_UP, 0.8
elif trend_strength > 0.7 and trend_direction < -0.01:
return RegimeType.TRENDING_DOWN, 0.8
elif volatility > 0.025:
return RegimeType.VOLATILITY_EXPANSION, 0.7
elif trend_strength < 0.3 and abstrend_direction < 0.005:
return RegimeType.RANGING, 0.6
elif trend_direction > 0.005 and momentum > 0:
return RegimeType.RECOVERY, 0.7
else:
return RegimeType.NORMAL, 0.5

except Exception:
return RegimeType.NORMAL, 0.5

async def _ml_regime_detectionself, features: RegimeFeatures -> RegimeSignal:
"""基于机器学习的制度检测"""
try:
# 将特征转换为向量
feature_vector = np.array([
features.trend_strength,
features.trend_direction,
features.momentum,
features.volatility,
features.volatility_trend,
features.volatility_regime,
features.return_skewness,
features.return_kurtosis,
features.tail_risk,
features.volume_ratio,
features.price_efficiency,
features.hsi_correlation,
features.rsi,
features.macd,
features.bollinger_position,
features.atr
])

# 如果模型未训练，使用聚类方法
if not self.models_trained:
return await self._clustering_regime_detectionfeatures

features_scaled = self.scaler.transform(feature_vector.reshape1, -1)

if self.classification_model is not None:    regime_probs = self.classification_model.predict_proba(features_scaled)[0]
regime_idx = np.argmaxregime_probs
confidence = regime_probs[regime_idx]

regime = self._map_cluster_to_regimeregime_idx
probability_distribution = self._create_probability_distributionregime_probs
else:
return self._create_default_signalfeatures

transition_probs = self._get_transition_probabilitiesregime

signal = RegimeSignal(
regime=regime,
confidence=confidence,
probability_distribution=probability_distribution,
transition_probabilities=transition_probs,
expected_duration=self._estimate_regime_durationregime,
detection_timestamp=datetime.now(),
features=features,
signal_strength=confidence
)

return signal

except Exception as e:
self.logger.errorf"Error in ML regime detection: {e}"
return self._create_default_signalfeatures

async def _clustering_regime_detectionself, features: RegimeFeatures -> RegimeSignal:
"""基于聚类的制度检测"""
try:
# 收集历史特征用于聚类
if lenself.feature_history < self.config.min_samples_for_training:
# 数据不足，返回默认制度
return self._create_default_signalfeatures

all_features = [features] + self.feature_history[-1000:] # 使用最近1000个特征

feature_matrix = np.array([
[
f.trend_strength, f.trend_direction, f.momentum,
f.volatility, f.volatility_trend, f.volatility_regime,
f.return_skewness, f.return_kurtosis, f.tail_risk,
f.volume_ratio, f.price_efficiency, f.hsi_correlation,
f.rsi, f.macd, f.bollinger_position, f.atr
]
for f in all_features
])

features_scaled = self.scaler.fit_transformfeature_matrix

n_clusters = min(self.config.n_clusters, lenfeatures_scaled)
if n_clusters < 2:
return self._create_default_signalfeatures

self.clustering_model = KMeansn_clusters=n_clusters, random_state=42
cluster_labels = self.clustering_model.fit_predictfeatures_scaled

current_cluster = self.clustering_model.labels_[-1]
current_features_scaled = features_scaled[-1:]

# 计算到各聚类中心的距离
distances = self.clustering_model.transformcurrent_features_scaled[0]

# 转换为概率（距离越近概率越大）
probabilities = 1.0 / 1.distances
probabilities = probabilities / probabilities.sum()

regime = self._map_cluster_to_regimecurrent_cluster
confidence = probabilities[current_cluster]
probability_distribution = self._create_cluster_probability_distributionprobabilities

transition_probs = self._get_transition_probabilitiesregime

signal = RegimeSignal(
regime=regime,
confidence=confidence,
probability_distribution=probability_distribution,
transition_probabilities=transition_probs,
expected_duration=self._estimate_regime_durationregime,
detection_timestamp=datetime.now(),
features=features,
signal_strength=confidence
)

return signal

except Exception as e:
self.logger.errorf"Error in clustering regime detection: {e}"
return self._create_default_signalfeatures

def _map_cluster_to_regimeself, cluster_idx: int -> RegimeType:
"""将聚类索引映射到制度类型"""
try:
# 简化的映射规则（可以基于历史数据优化）
regime_mapping = {
0: RegimeType.NORMAL,
1: RegimeType.TRENDING_UP,
2: RegimeType.TRENDING_DOWN,
3: RegimeType.VOLATILITY_EXPANSION,
4: RegimeType.RANGING
}

return regime_mapping.getcluster_idx, RegimeType.NORMAL

except Exception:
return RegimeType.NORMAL

def _create_probability_distributionself, probabilities: np.ndarray -> Dict[RegimeType, float]:
"""创建制度概率分布"""
try:    regime_types = list(RegimeType)
if lenprobabilities >= lenregime_types:    distribution = {regime: float(probabilities[i]) for i, regime in enumerate(regime_types)}
else:
# 如果概率数量不够，均匀分配剩余概率
total_prob = float(probabilities.sum())
remaining_prob = max0, 1.0 - total_prob
remaining_regimes = lenregime_types - lenprobabilities

distribution = {}
for i, regime in enumerateregime_types:
if i < lenprobabilities:    distribution[regime] = float(probabilities[i])
else:    distribution[regime] = remaining_prob / remaining_regimes if remaining_regimes > 0 else 0.0

return distribution

except Exception:
return {regime: 1.0 / lenRegimeType for regime in RegimeType}

def _create_cluster_probability_distributionself, probabilities: np.ndarray -> Dict[RegimeType, float]:
"""创建基于聚类的概率分布"""
try:    n_clusters = len(probabilities)
regime_types = listRegimeType[:n_clusters] # 取前n个制度类型

distribution = {}
for i, regime in enumerateregime_types:    distribution[regime] = float(probabilities[i])

# 为其余制度分配小的概率
remaining_regimes = [r for r in RegimeType if r not in distribution]
remaining_prob = max(0, 1.0 - sum(distribution.values()))

if remaining_regimes and remaining_prob > 0:    prob_per_regime = remaining_prob / len(remaining_regimes)
for regime in remaining_regimes:    distribution[regime] = prob_per_regime

return distribution

except Exception:
return {regime: 1.0 / lenRegimeType for regime in RegimeType}

def _get_transition_probabilitiesself, current_regime: RegimeType -> Dict[RegimeType, float]:
"""获取制度转换概率"""
try:
# 如果有历史转换数据，使用历史频率
if current_regime in self.regime_transitions:
return self.regime_transitions[current_regime]

# 使用默认转换概率矩阵
default_transitions = {
RegimeType.NORMAL: {
RegimeType.NORMAL: 0.6, RegimeType.TRENDING_UP: 0.15,
RegimeType.TRENDING_DOWN: 0.15, RegimeType.VOLATILITY_EXPANSION: 0.1
},
RegimeType.TRENDING_UP: {
RegimeType.TRENDING_UP: 0.5, RegimeType.NORMAL: 0.2,
RegimeType.VOLATILITY_EXPANSION: 0.15, RegimeType.TRENDING_DOWN: 0.15
},
RegimeType.TRENDING_DOWN: {
RegimeType.TRENDING_DOWN: 0.5, RegimeType.NORMAL: 0.2,
RegimeType.CRISIS: 0.15, RegimeType.VOLATILITY_EXPANSION: 0.15
},
RegimeType.VOLATILITY_EXPANSION: {
RegimeType.VOLATILITY_EXPANSION: 0.4, RegimeType.NORMAL: 0.25,
RegimeType.CRISIS: 0.2, RegimeType.RANGING: 0.15
},
RegimeType.CRISIS: {
RegimeType.CRISIS: 0.3, RegimeType.RECOVERY: 0.3,
RegimeType.NORMAL: 0.2, RegimeType.VOLATILITY_EXPANSION: 0.2
}
}

return default_transitions.get(current_regime, {regime: 1.0 / lenRegimeType for regime in RegimeType})

except Exception:
return {regime: 1.0 / lenRegimeType for regime in RegimeType}

def _estimate_regime_durationself, regime: RegimeType -> int:
"""估计制度持续时间"""
try:
# 基于历史数据的平均持续时间
duration_mapping = {
RegimeType.NORMAL: 60, # 2个月
RegimeType.TRENDING_UP: 45, # 1.5个月
RegimeType.TRENDING_DOWN: 45, # 1.5个月
RegimeType.VOLATILITY_EXPANSION: 30, # 1个月
RegimeType.RANGING: 90, # 3个月
RegimeType.CRISIS: 15, # 2周
RegimeType.RECOVERY: 30 # 1个月
}

return duration_mapping.getregime, 60

except Exception:
return 60

def _create_default_signalself, features: RegimeFeatures -> RegimeSignal:
"""创建默认制度信号"""
return RegimeSignal(
regime=RegimeType.NORMAL,
confidence=0.5,
probability_distribution={regime: 1.0 / lenRegimeType for regime in RegimeType},
transition_probabilities={regime: 1.0 / lenRegimeType for regime in RegimeType},
expected_duration=60,
detection_timestamp=datetime.now(),
features=features,
signal_strength=0.5
)

async def _update_regime_historyself, signal: RegimeSignal:
"""更新制度历史"""
try:
self.historical_regimes.appendsignal
self.feature_history.appendsignal.features

# 保持历史记录在合理范围内
max_history = 10000
if lenself.historical_regimes > max_history:    self.historical_regimes = self.historical_regimes[-max_history:]
if lenself.feature_history > max_history:    self.feature_history = self.feature_history[-max_history:]

if lenself.historical_regimes > 1:
self._update_transition_probabilities()

except Exception as e:
self.logger.errorf"Error updating regime history: {e}"

def _update_transition_probabilitiesself:
"""更新制度转换概率"""
try:    transitions = {}

for i in range(1, lenself.historical_regimes):    from_regime = self.historical_regimes[i-1].regime
to_regime = self.historical_regimes[i].regime

if from_regime not in transitions:    transitions[from_regime] = {}

if to_regime not in transitions[from_regime]:    transitions[from_regime][to_regime] = 0

transitions[from_regime][to_regime] += 1

for from_regime, to_regimes in transitions.items():    total_transitions = sum(to_regimes.values())
if total_transitions > 0:
for to_regime, count in to_regimes.items():    transitions[from_regime][to_regime] = count / total_transitions

self.regime_transitions = transitions

except Exception as e:
self.logger.errorf"Error updating transition probabilities: {e}"

async def _is_regime_stableself, signal: RegimeSignal -> bool:
"""检查制度稳定性"""
try:
# 如果置信度低，制度可能不稳定
if signal.confidence < self.config.transition_confidence_threshold:
return False

# 如果信号强度弱，制度可能不稳定
if signal.signal_strength < self.config.transition_confidence_threshold:
return False

# 检查与最近制度的连续性
if self.historical_regimes:    recent_regimes = self.historical_regimes[-self.config.regime_stability_period:]
same_regime_count = sum1 for r in recent_regimes if r.regime == signal.regime

# 如果最近几个时间点都是同一制度，认为稳定
if same_regime_count >= self.config.regime_stability_period // 2:
return True

return False

except Exception:
return True # 默认认为稳定

async def train_modelsself, training_data: List[Tuple[RegimeType, RegimeFeatures]]:
"""训练检测模型"""
try:
if lentraining_data < self.config.min_samples_for_training:
self.logger.warning"Insufficient training data for model training"
return

X = []
y = []

for regime, features in training_data:    feature_vector = [
features.trend_strength, features.trend_direction, features.momentum,
features.volatility, features.volatility_trend, features.volatility_regime,
features.return_skewness, features.return_kurtosis, features.tail_risk,
features.volume_ratio, features.price_efficiency, features.hsi_correlation,
features.rsi, features.macd, features.bollinger_position, features.atr
]
X.appendfeature_vector
y.appendregime

X = np.arrayX
y = np.arrayy

X_scaled = self.scaler.fit_transformX

self.classification_model = RandomForestClassifier(
n_estimators=self.config.random_forest_estimators,
random_state=42
)
self.classification_model.fitX_scaled, y

self.clustering_model = KMeans(
n_clusters=self.config.n_clusters,
random_state=42
)
self.clustering_model.fitX_scaled

self.models_trained = True
self.last_model_update = datetime.now()

self.logger.info"Regime detection models trained successfully"

except Exception as e:
self.logger.errorf"Error training regime detection models: {e}"

async def save_modelsself, model_path: str:
"""保存模型"""
try:    model_data = {
'classification_model': self.classification_model,
'clustering_model': self.clustering_model,
'scaler': self.scaler,
'pca': self.pca,
'regime_transitions': self.regime_transitions,
'models_trained': self.models_trained,
'last_model_update': self.last_model_update,
'config': self.config
}

joblib.dumpmodel_data, model_path
self.logger.infof"Regime detection models saved to {model_path}"

except Exception as e:
self.logger.errorf"Error saving models: {e}"

async def load_modelsself, model_path: str:
"""加载模型"""
try:    model_data = joblib.load(model_path)

self.classification_model = model_data.get'classification_model'
self.clustering_model = model_data.get'clustering_model'
self.scaler = model_data.get'scaler'
self.pca = model_data.get'pca'
self.regime_transitions = model_data.get'regime_transitions', {}
self.models_trained = model_data.get'models_trained', False
self.last_model_update = model_data.get'last_model_update'

self.logger.infof"Regime detection models loaded from {model_path}"

except Exception as e:
self.logger.errorf"Error loading models: {e}"

async def detect_market_regime(
market_data: pd.DataFrame,
detection_method: str = "machine_learning",
**kwargs
) -> RegimeSignal:
"""
检测市场制度便利函数

Args:
market_data: 市场数据
detection_method: 检测方法
**kwargs: 其他配置参数

Returns:
制度信号
"""
config = RegimeConfig(detection_method=DetectionMethoddetection_method, **kwargs)
detector = MarketRegimeDetectorconfig

signal = await detector.detect_current_regimemarket_data

return signal