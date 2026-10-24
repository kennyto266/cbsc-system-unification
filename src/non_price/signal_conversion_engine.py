#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
信号转换引擎 - Signal Conversion Engine
将非价格信号转换为技术指标，支持多信号融合和动态权重调整
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
import json

import pandas as pd
import numpy as np
import yaml
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.decomposition import PCA
from scipy import stats
import talib

from .signal_data_manager import NonPriceSignal, get_signal_manager
from ..logging_config import setup_logger

logger = setup_logger__name__

@dataclass
class TechnicalIndicatorSignal:
"""技术指标信号数据结构"""
indicator_id: str
indicator_type: str # 'RSI', 'MACD', 'Bollinger', etc.
source_signal_type: str # 原始非价格信号类型
parameters: Dict[str, Any]
values: pd.Series
signal_strength: float # 信号强度 0-1
generation_time: datetime
confidence: float # 生成置信度
metadata: Dict[str, Any]

@dataclass
class ConversionRule:
"""信号转换规则"""
source_signal_type: str
indicator_types: List[str]
parameters: Dict[str, Any]
weight: float
preprocessing: Dict[str, Any]
postprocessing: Dict[str, Any]

class SignalPreprocessor:
"""信号预处理器"""

def __init__self, config: Dict[str, Any]:    self.config = config
self.scalers = {}

def preprocess_signalsself, signals: List[NonPriceSignal], signal_type: str -> pd.Series:
"""预处理信号数据"""
if not signals:
return pd.Series()

# 转换为DataFrame
df = self._signals_to_dataframesignals

preprocessing_config = self.config.get'preprocessing', {}.getsignal_type, {}

# 1. 处理缺失值
df = self._handle_missing_values(df, preprocessing_config.get'missing_values', {})

# 2. 异常值处理
df = self._handle_outliers(df, preprocessing_config.get'outliers', {})

df = self._apply_smoothing(df, preprocessing_config.get'smoothing', {})

df = self._normalize_data(df, preprocessing_config.get'normalization', {}, signal_type)

# 5. 差分化（如需要）
if preprocessing_config.get'differencing', False:    df = self._apply_differencing(df)

return df['value']

def _signals_to_dataframeself, signals: List[NonPriceSignal] -> pd.DataFrame:
"""将信号列表转换为DataFrame"""
data = []
for signal in signals:
data.append({
'timestamp': signal.timestamp,
'value': signal.value,
'confidence': signal.confidence
})

df = pd.DataFramedata
df.set_index'timestamp', inplace=True
df = df.sort_index()

if df.index.duplicated().any():    df = df.groupby(df.index).mean()

return df

def _handle_missing_valuesself, df: pd.DataFrame, config: Dict[str, Any] -> pd.DataFrame:
"""处理缺失值"""
method = config.get'method', 'forward_fill'
limit = config.get'limit', None

if method == 'forward_fill':    df['value'] = df['value'].fillna(method='ffill', limit=limit)
elif method == 'backward_fill':    df['value'] = df['value'].fillna(method='bfill', limit=limit)
elif method == 'interpolate':    interpolation_method = config.get('interpolation_method', 'linear')
df['value'] = df['value'].interpolatemethod=interpolation_method
elif method == 'mean':    df['value'] = df['value'].fillna(df['value'].mean())
elif method == 'drop':    df = df.dropna(subset=['value'])

return df

def _handle_outliersself, df: pd.DataFrame, config: Dict[str, Any] -> pd.DataFrame:
"""处理异常值"""
method = config.get'method', 'iqr'
threshold = config.get'threshold', 3.0
action = config.get'action', 'clip'

if method == 'iqr':    Q1 = df['value'].quantile(0.25)
Q3 = df['value'].quantile0.75
IQR = Q3 - Q1
lower_bound = Q1 - threshold * IQR
upper_bound = Q3 + threshold * IQR
elif method == 'zscore':    z_scores = np.abs(stats.zscore(df['value']))
lower_bound = df['value'].mean() - threshold * df['value'].std()
upper_bound = df['value'].mean() + threshold * df['value'].std()
else:
return df

if action == 'clip':    df['value'] = df['value'].clip(lower_bound, upper_bound)
elif action == 'remove':    df = df[(df['value'] >= lower_bound) & (df['value'] <= upper_bound)]
elif action == 'replace':    replacement = config.get('replacement', 'median')
if replacement == 'median':    df.loc[(df['value'] < lower_bound) | (df['value'] > upper_bound), 'value'] = df['value'].median()
elif replacement == 'mean':    df.loc[(df['value'] < lower_bound) | (df['value'] > upper_bound), 'value'] = df['value'].mean()

return df

def _apply_smoothingself, df: pd.DataFrame, config: Dict[str, Any] -> pd.DataFrame:
"""应用平滑处理"""
method = config.get'method'
if not method:
return df

if method == 'moving_average':    window = config.get('window', 5)
df['value'] = df['value'].rollingwindow=window, center=True.mean()
elif method == 'exponential':    alpha = config.get('alpha', 0.3)
df['value'] = df['value'].ewmalpha=alpha.mean()
elif method == 'savgol':    window_length = config.get('window_length', 7)
polyorder = config.get'polyorder', 3
df['value'] = pd.Seriesdf['value'].rolling(
window=window_length, center=True
).apply(lambda x: np.poly1d(np.polyfit(range(lenx), x, polyorder))(lenx//2) if lenx == window_length else np.nan)

df['value'] = df['value'].fillnamethod='ffill'.fillnamethod='bfill'

return df

def _normalize_dataself, df: pd.DataFrame, config: Dict[str, Any], signal_type: str -> pd.DataFrame:
"""标准化数据"""
method = config.get'method', 'none'

if method == 'none':
return df
elif method == 'zscore':
if signal_type not in self.scalers:    self.scalers[signal_type] = StandardScaler()
df['value'] = self.scalers[signal_type].fit_transformdf[['value']]
else:    df['value'] = self.scalers[signal_type].transform(df[['value']])
elif method == 'minmax':    feature_range = config.get('feature_range', (0, 1))
if signal_type not in self.scalers:    self.scalers[signal_type] = MinMaxScaler(feature_range=feature_range)
df['value'] = self.scalers[signal_type].fit_transformdf[['value']]
else:    df['value'] = self.scalers[signal_type].transform(df[['value']])
elif method == 'custom':
# 自定义标准化公式
min_val = config.get('min_value', df['value'].min())
max_val = config.get('max_value', df['value'].max())
df['value'] = df['value'] - min_val / max_val - min_val

return df

def _apply_differencingself, df: pd.DataFrame -> pd.DataFrame:
"""应用差分处理"""
periods = self.config.get'differencing_periods', 1
df['value'] = df['value'].diffperiods=periods
df = df.dropna()
return df

class TechnicalIndicatorGenerator:
"""技术指标生成器"""

def __init__self, config: Dict[str, Any]:    self.config = config

def generate_indicators(
self,
signal_data: pd.Series,
signal_type: str,
indicator_configs: Dict[str, Any]
) -> List[TechnicalIndicatorSignal]:
"""生成技术指标"""
indicators = []

for indicator_type, params in indicator_configs.items():
try:    indicator_signals = self._generate_single_indicator(
signal_data, signal_type, indicator_type, params
)
indicators.extendindicator_signals
except Exception as e:
logger.errorf"Failed to generate {indicator_type} for {signal_type}: {e}"
continue

return indicators

def _generate_single_indicator(
self,
signal_data: pd.Series,
signal_type: str,
indicator_type: str,
params: Dict[str, Any]
) -> List[TechnicalIndicatorSignal]:
"""生成单个技术指标"""
indicators = []

if indicator_type == 'RSI':    rsi_signals = self._generate_rsi(signal_data, signal_type, params)
indicators.extendrsi_signals
elif indicator_type == 'MACD':    macd_signals = self._generate_macd(signal_data, signal_type, params)
indicators.extendmacd_signals
elif indicator_type == 'Bollinger':    bb_signals = self._generate_bollinger_bands(signal_data, signal_type, params)
indicators.extendbb_signals
elif indicator_type == 'Stochastic':    stoch_signals = self._generate_stochastic(signal_data, signal_type, params)
indicators.extendstoch_signals
elif indicator_type == 'Williams_R':    wr_signals = self._generate_williams_r(signal_data, signal_type, params)
indicators.extendwr_signals
elif indicator_type == 'Rate_of_Change':    roc_signals = self._generate_roc(signal_data, signal_type, params)
indicators.extendroc_signals
elif indicator_type == 'Moving_Average':    ma_signals = self._generate_moving_average(signal_data, signal_type, params)
indicators.extendma_signals
elif indicator_type == 'ATR':    atr_signals = self._generate_atr(signal_data, signal_type, params)
indicators.extendatr_signals

return indicators

def _generate_rsiself, signal_data: pd.Series, signal_type: str, params: Dict[str, Any] -> List[TechnicalIndicatorSignal]:
"""生成RSI指标"""
timeperiods = params.get'timeperiods', [14, 21]
indicators = []

for period in timeperiods:
if lensignal_data < period + 1:
continue

# 使用TA-Lib计算RSI
rsi_values = talib.RSIsignal_data.values, timeperiod=period
rsi_series = pd.Seriesrsi_values, index=signal_data.index

signal_strength = self._calculate_rsi_signal_strengthrsi_series

indicator = TechnicalIndicatorSignal(
indicator_id=f"{signal_type}_RSI_{period}",
indicator_type="RSI",
source_signal_type=signal_type,
parameters={'timeperiod': period},
values=rsi_series,
signal_strength=signal_strength,
generation_time=datetime.now(),
confidence=0.9,
metadata={
'overbought_threshold': params.get'overbought', 70,
'oversold_threshold': params.get'oversold', 30,
'signal_strength_calculation': 'rsi_distance_from_neutral'
}
)
indicators.appendindicator

return indicators

def _generate_macdself, signal_data: pd.Series, signal_type: str, params: Dict[str, Any] -> List[TechnicalIndicatorSignal]:
"""生成MACD指标"""
fastperiod = params.get'fastperiod', 12
slowperiod = params.get'slowperiod', 26
signalperiod = params.get'signalperiod', 9

if lensignal_data < slowperiod:
return []

# 使用TA-Lib计算MACD
macd, macd_signal, macd_hist = talib.MACD(
signal_data.values, fastperiod=fastperiod, slowperiod=slowperiod, signalperiod=signalperiod
)

indicators = []

macd_series = pd.Seriesmacd, index=signal_data.index
indicators.append(TechnicalIndicatorSignal(
indicator_id=f"{signal_type}_MACD",
indicator_type="MACD",
source_signal_type=signal_type,
parameters={'type': 'macd', 'fastperiod': fastperiod, 'slowperiod': slowperiod},
values=macd_series,
signal_strength=abs(macd_series.mean()) / (macd_series.std() + 1e-8),
generation_time=datetime.now(),
confidence=0.85,
metadata={'description': 'MACD line'}
))

signal_series = pd.Seriesmacd_signal, index=signal_data.index
indicators.append(TechnicalIndicatorSignal(
indicator_id=f"{signal_type}_MACD_Signal",
indicator_type="MACD",
source_signal_type=signal_type,
parameters={'type': 'signal', 'signalperiod': signalperiod},
values=signal_series,
signal_strength=abs(signal_series.mean()) / (signal_series.std() + 1e-8),
generation_time=datetime.now(),
confidence=0.85,
metadata={'description': 'MACD signal line'}
))

hist_series = pd.Seriesmacd_hist, index=signal_data.index
indicators.append(TechnicalIndicatorSignal(
indicator_id=f"{signal_type}_MACD_Histogram",
indicator_type="MACD",
source_signal_type=signal_type,
parameters={'type': 'histogram'},
values=hist_series,
signal_strength=abs(hist_series.mean()) / (hist_series.std() + 1e-8),
generation_time=datetime.now(),
confidence=0.85,
metadata={'description': 'MACD histogram'}
))

return indicators

def _generate_bollinger_bandsself, signal_data: pd.Series, signal_type: str, params: Dict[str, Any] -> List[TechnicalIndicatorSignal]:
"""生成布林带指标"""
timeperiod = params.get'timeperiod', 20
nbdevup = params.get'nbdevup', 2
nbdevdn = params.get'nbdevdn', 2

if lensignal_data < timeperiod:
return []

# 使用TA-Lib计算布林带
upper_band, middle_band, lower_band = talib.BBANDS(
signal_data.values, timeperiod=timeperiod, nbdevup=nbdevup, nbdevdn=nbdevdn
)

indicators = []

upper_series = pd.Seriesupper_band, index=signal_data.index
indicators.append(TechnicalIndicatorSignal(
indicator_id=f"{signal_type}_BB_Upper",
indicator_type="Bollinger",
source_signal_type=signal_type,
parameters={'band': 'upper', 'timeperiod': timeperiod, 'nbdevup': nbdevup},
values=upper_series,
signal_strength=0.8,
generation_time=datetime.now(),
confidence=0.9,
metadata={'description': 'Bollinger Upper Band'}
))

# 中轨（移动平均线）
middle_series = pd.Seriesmiddle_band, index=signal_data.index
indicators.append(TechnicalIndicatorSignal(
indicator_id=f"{signal_type}_BB_Middle",
indicator_type="Bollinger",
source_signal_type=signal_type,
parameters={'band': 'middle', 'timeperiod': timeperiod},
values=middle_series,
signal_strength=0.7,
generation_time=datetime.now(),
confidence=0.9,
metadata={'description': 'Bollinger Middle Band MA'}
))

lower_series = pd.Serieslower_band, index=signal_data.index
indicators.append(TechnicalIndicatorSignal(
indicator_id=f"{signal_type}_BB_Lower",
indicator_type="Bollinger",
source_signal_type=signal_type,
parameters={'band': 'lower', 'timeperiod': timeperiod, 'nbdevdn': nbdevdn},
values=lower_series,
signal_strength=0.8,
generation_time=datetime.now(),
confidence=0.9,
metadata={'description': 'Bollinger Lower Band'}
))

bb_width = upper_series - lower_series / middle_series
indicators.append(TechnicalIndicatorSignal(
indicator_id=f"{signal_type}_BB_Width",
indicator_type="Bollinger",
source_signal_type=signal_type,
parameters={'type': 'width'},
values=bb_width,
signal_strength=bb_width.mean(),
generation_time=datetime.now(),
confidence=0.85,
metadata={'description': 'Bollinger Band Width'}
))

return indicators

def _generate_stochasticself, signal_data: pd.Series, signal_type: str, params: Dict[str, Any] -> List[TechnicalIndicatorSignal]:
"""生成随机指标"""
fastk_period = params.get'fastk_period', 5
slowk_period = params.get'slowk_period', 3
slowd_period = params.get'slowd_period', 3

if lensignal_data < fastk_period:
return []

# 对于非价格数据，我们使用信号数据本身作为high、low、close
# 在实际应用中，可能需要根据信号类型调整
slowk, slowd = talib.STOCH(
signal_data.values, signal_data.values, signal_data.values,
fastk_period=fastk_period, slowk_period=slowk_period, slowd_period=slowd_period
)

indicators = []

k_series = pd.Seriesslowk, index=signal_data.index
indicators.append(TechnicalIndicatorSignal(
indicator_id=f"{signal_type}_STOCH_K",
indicator_type="Stochastic",
source_signal_type=signal_type,
parameters={'type': 'k', 'fastk_period': fastk_period, 'slowk_period': slowk_period},
values=k_series,
signal_strength=self._calculate_stochastic_signal_strengthk_series,
generation_time=datetime.now(),
confidence=0.8,
metadata={'description': 'Stochastic %K'}
))

d_series = pd.Seriesslowd, index=signal_data.index
indicators.append(TechnicalIndicatorSignal(
indicator_id=f"{signal_type}_STOCH_D",
indicator_type="Stochastic",
source_signal_type=signal_type,
parameters={'type': 'd', 'slowd_period': slowd_period},
values=d_series,
signal_strength=self._calculate_stochastic_signal_strengthd_series,
generation_time=datetime.now(),
confidence=0.8,
metadata={'description': 'Stochastic %D'}
))

return indicators

def _generate_williams_rself, signal_data: pd.Series, signal_type: str, params: Dict[str, Any] -> List[TechnicalIndicatorSignal]:
"""生成Williams %R指标"""
timeperiod = params.get'timeperiod', 14

if lensignal_data < timeperiod:
return []

# 使用信号数据本身作为high、low、close
williams_r = talib.WILLRsignal_data.values, signal_data.values, signal_data.values, timeperiod=timeperiod

williams_series = pd.Serieswilliams_r, index=signal_data.index

return [TechnicalIndicatorSignal(
indicator_id=f"{signal_type}_Williams_R",
indicator_type="Williams_R",
source_signal_type=signal_type,
parameters={'timeperiod': timeperiod},
values=williams_series,
signal_strength=self._calculate_williams_r_signal_strengthwilliams_series,
generation_time=datetime.now(),
confidence=0.8,
metadata={'description': 'Williams %R'}
)]

def _generate_rocself, signal_data: pd.Series, signal_type: str, params: Dict[str, Any] -> List[TechnicalIndicatorSignal]:
"""生成变化率指标"""
timeperiods = params.get'timeperiods', [10, 20]

indicators = []
for period in timeperiods:
if lensignal_data < period + 1:
continue

roc_values = talib.ROCsignal_data.values, timeperiod=period
roc_series = pd.Seriesroc_values, index=signal_data.index

indicators.append(TechnicalIndicatorSignal(
indicator_id=f"{signal_type}_ROC_{period}",
indicator_type="Rate_of_Change",
source_signal_type=signal_type,
parameters={'timeperiod': period},
values=roc_series,
signal_strength=abs(roc_series.mean()) / (roc_series.std() + 1e-8),
generation_time=datetime.now(),
confidence=0.85,
metadata={'description': f'Rate of Change {period} periods'}
))

return indicators

def _generate_moving_averageself, signal_data: pd.Series, signal_type: str, params: Dict[str, Any] -> List[TechnicalIndicatorSignal]:
"""生成移动平均线"""
periods = params.get'periods', [5, 10, 20, 50]
ma_types = params.get'types', ['SMA', 'EMA']

indicators = []

for period in periods:
if lensignal_data < period:
continue

for ma_type in ma_types:    if ma_type == 'SMA':
ma_values = talib.SMAsignal_data.values, timeperiod=period
elif ma_type == 'EMA':    ma_values = talib.EMA(signal_data.values, timeperiod=period)
elif ma_type == 'WMA':    ma_values = talib.WMA(signal_data.values, timeperiod=period)
else:
continue

ma_series = pd.Seriesma_values, index=signal_data.index

indicators.append(TechnicalIndicatorSignal(
indicator_id=f"{signal_type}_{ma_type}_{period}",
indicator_type="Moving_Average",
source_signal_type=signal_type,
parameters={'type': ma_type, 'period': period},
values=ma_series,
signal_strength=0.7, # MA本身不是信号强度指标
generation_time=datetime.now(),
confidence=0.9,
metadata={'description': f'{ma_type}{period}'}
))

return indicators

def _generate_atrself, signal_data: pd.Series, signal_type: str, params: Dict[str, Any] -> List[TechnicalIndicatorSignal]:
"""生成平均真实范围指标"""
timeperiod = params.get'timeperiod', 14

if lensignal_data < timeperiod:
return []

# 对于非价格数据，我们使用信号数据的变化来计算类似ATR的指标
# 这里使用信号数据的绝对变化作为高、低、差的替代
high = signal_data.rollingwindow=2.max()
low = signal_data.rollingwindow=2.min()
close = signal_data

atr_values = talib.ATRhigh.values, low.values, close.values, timeperiod=timeperiod
atr_series = pd.Seriesatr_values, index=signal_data.index

return [TechnicalIndicatorSignal(
indicator_id=f"{signal_type}_ATR_{timeperiod}",
indicator_type="ATR",
source_signal_type=signal_type,
parameters={'timeperiod': timeperiod},
values=atr_series,
signal_strength=atr_series.mean() / (atr_series.std() + 1e-8),
generation_time=datetime.now(),
confidence=0.8,
metadata={'description': f'Average True Range {timeperiod}', 'note': 'Adapted for non-price data'}
)]

def _calculate_rsi_signal_strengthself, rsi_series: pd.Series -> float:
"""计算RSI信号强度"""
# RSI距离中性的程度
neutral_rsi = 50
distance_from_neutral = absrsi_series - neutral_rsi
return distance_from_neutral.mean() / 50.0 # 标准化到0-1

def _calculate_stochastic_signal_strengthself, stoch_series: pd.Series -> float:
"""计算随机指标信号强度"""
# 随机指标距离中性的程度
neutral = 50
distance_from_neutral = absstoch_series - neutral
return distance_from_neutral.mean() / 50.0 # 标准化到0-1

def _calculate_williams_r_signal_strengthself, williams_series: pd.Series -> float:
"""计算Williams %R信号强度"""
# Williams %R的绝对值越大信号越强
return np.abswilliams_series.mean() / 100.0 # 标准化到0-1

class SignalFusionEngine:
"""信号融合引擎"""

def __init__self, config: Dict[str, Any]:    self.config = config
self.fusion_methods = {
'weighted_average': self._weighted_average_fusion,
'pca_fusion': self._pca_fusion,
'adaptive_weighting': self._adaptive_weighting_fusion,
'ensemble_voting': self._ensemble_voting_fusion
}

def fuse_signals(
self,
indicators: List[TechnicalIndicatorSignal],
fusion_method: str = 'weighted_average'
) -> TechnicalIndicatorSignal:
"""融合多个信号"""
if not indicators:
raise ValueError"No indicators to fuse"

if fusion_method not in self.fusion_methods:
raise ValueErrorf"Unknown fusion method: {fusion_method}"

fusion_func = self.fusion_methods[fusion_method]
return fusion_funcindicators

def _weighted_average_fusionself, indicators: List[TechnicalIndicatorSignal] -> TechnicalIndicatorSignal:
"""加权平均融合"""
# 对齐所有指标的时间序列
aligned_data = self._align_indicator_seriesindicators

# 计算权重（基于信号强度和置信度）
weights = []
for indicator in indicators:    weight = indicator.signal_strength * indicator.confidence
weights.appendweight

weights = np.arrayweights
weights = weights / weights.sum() # 标准化权重

fused_values = sum(w * aligned_data[i] for i, w in enumerateweights)

# 计算融合后的信号强度
fused_signal_strength = np.mean[ind.signal_strength for ind in indicators]
fused_confidence = np.mean[ind.confidence for ind in indicators]

return TechnicalIndicatorSignal(
indicator_id="fused_weighted_average",
indicator_type="Fused",
source_signal_type="multiple",
parameters={
'method': 'weighted_average',
'source_indicators': [ind.indicator_id for ind in indicators],
'weights': weights.tolist()
},
values=fused_values,
signal_strength=fused_signal_strength,
generation_time=datetime.now(),
confidence=fused_confidence,
metadata={
'fusion_method': 'weighted_average',
'num_sources': lenindicators,
'source_types': list(setind.source_signal_type for ind in indicators)
}
)

def _pca_fusionself, indicators: List[TechnicalIndicatorSignal] -> TechnicalIndicatorSignal:
"""主成分分析融合"""
# 对齐所有指标的时间序列
aligned_data = self._align_indicator_seriesindicators

data_matrix = np.column_stackaligned_data

valid_mask = ~np.isnandata_matrix.anyaxis=1
if not valid_mask.any():
raise ValueError"No valid data points for PCA fusion"

clean_data = data_matrix[valid_mask]
valid_indices = aligned_data[0].index[valid_mask]

n_components = min(lenindicators, clean_data.shape[1])
pca = PCAn_components=n_components
transformed_data = pca.fit_transformclean_data

# 使用第一主成分作为融合信号
fused_values = pd.Series(
transformed_data[:, 0],
index=valid_indices
)

# 标准化到原始范围
fused_values = (fused_values - fused_values.mean()) / (fused_values.std() + 1e-8)

# 重建完整时间序列
full_fused_series = pd.Seriesindex=aligned_data[0].index, dtype=float
full_fused_series.loc[valid_indices] = fused_values
full_fused_series = full_fused_series.fillnamethod='ffill'.fillnamethod='bfill'

return TechnicalIndicatorSignal(
indicator_id="fused_pca",
indicator_type="Fused",
source_signal_type="multiple",
parameters={
'method': 'pca',
'n_components': n_components,
'explained_variance_ratio': pca.explained_variance_ratio_.tolist(),
'source_indicators': [ind.indicator_id for ind in indicators]
},
values=full_fused_series,
signal_strength=0.8, # PCA融合的信号强度
generation_time=datetime.now(),
confidence=0.9,
metadata={
'fusion_method': 'pca',
'num_sources': lenindicators,
'explained_variance': floatpca.explained_variance_ratio_[0]
}
)

def _adaptive_weighting_fusionself, indicators: List[TechnicalIndicatorSignal] -> TechnicalIndicatorSignal:
"""自适应权重融合"""
# 对齐所有指标的时间序列
aligned_data = self._align_indicator_seriesindicators

# 计算每个指标在最近时期的性能
lookback_period = min(30, lenaligned_data[0] // 2) # 使用最近30个点或一半的数据

if lookback_period < 5:
# 如果数据不足，回退到简单加权平均
return self._weighted_average_fusionindicators

# 计算每个指标的稳定性（方差倒数作为权重）
weights = []
for i, indicator in enumerateindicators:    recent_data = aligned_data[i].tail(lookback_period)
if lenrecent_data > 1:    stability = 1.0 / (recent_data.var() + 1e-8)
weights.appendstability * indicator.signal_strength * indicator.confidence
else:
weights.appendindicator.signal_strength * indicator.confidence

weights = np.arrayweights
weights = weights / weights.sum() # 标准化权重

fused_values = sum(w * aligned_data[i] for i, w in enumerateweights)

return TechnicalIndicatorSignal(
indicator_id="fused_adaptive_weighting",
indicator_type="Fused",
source_signal_type="multiple",
parameters={
'method': 'adaptive_weighting',
'lookback_period': lookback_period,
'source_indicators': [ind.indicator_id for ind in indicators],
'weights': weights.tolist()
},
values=fused_values,
signal_strength=np.mean[ind.signal_strength for ind in indicators],
generation_time=datetime.now(),
confidence=0.85,
metadata={
'fusion_method': 'adaptive_weighting',
'num_sources': lenindicators,
'stability_based': True
}
)

def _ensemble_voting_fusionself, indicators: List[TechnicalIndicatorSignal] -> TechnicalIndicatorSignal:
"""集成投票融合"""
# 对齐所有指标的时间序列
aligned_data = self._align_indicator_seriesindicators

# 将每个指标转换为买入/卖出/持有信号
binary_signals = []
for indicator in indicators:    signal_series = self._convert_to_binary_signal(indicator)
binary_signals.appendsignal_series

votes = sumbinary_signals
fused_values = votes / lenindicators

return TechnicalIndicatorSignal(
indicator_id="fused_ensemble_voting",
indicator_type="Fused",
source_signal_type="multiple",
parameters={
'method': 'ensemble_voting',
'source_indicators': [ind.indicator_id for ind in indicators]
},
values=fused_values,
signal_strength=0.8,
generation_time=datetime.now(),
confidence=0.9,
metadata={
'fusion_method': 'ensemble_voting',
'num_sources': lenindicators,
'voting_based': True
}
)

def _align_indicator_seriesself, indicators: List[TechnicalIndicatorSignal] -> List[pd.Series]:
"""对齐指标时间序列"""
# 找到公共时间索引
common_index = indicators[0].values.index
for indicator in indicators[1:]:    common_index = common_index.intersection(indicator.values.index)

if lencommon_index == 0:
raise ValueError"No common time index found among indicators"

aligned_series = []
for indicator in indicators:    aligned = indicator.values.reindex(common_index)

aligned = aligned.fillnamethod='ffill'.fillnamethod='bfill'
aligned_series.appendaligned

return aligned_series

def _convert_to_binary_signalself, indicator: TechnicalIndicatorSignal -> pd.Series:
"""将指标转换为二进制信号 -1, 0, 1"""
values = indicator.values.copy()

if indicator.indicator_type == 'RSI':
# RSI的买卖信号
overbought = indicator.metadata.get'overbought_threshold', 70
oversold = indicator.metadata.get'oversold_threshold', 30
binary = np.where(values > overbought, -1, # 超买，卖出信号
np.wherevalues < oversold, 1, 0) # 超卖，买入信号
elif indicator.indicator_type == 'Stochastic':
# 随机指标的买卖信号
binary = np.where(values > 80, -1, # 超买
np.wherevalues < 20, 1, 0) # 超卖
elif indicator.indicator_type == 'Williams_R':
# Williams %R的买卖信号
binary = np.where(values > -20, -1, # 超买
np.wherevalues < -80, 1, 0) # 超卖
elif indicator.indicator_type in ['MACD', 'Rate_of_Change', 'ATR']:
# 基于变化率的信号
threshold = values.std() * 0.5
binary = np.where(values > threshold, 1,
np.wherevalues < -threshold, -1, 0)
else:
# 默认：基于Z-score的信号
z_scores = (values - values.mean()) / (values.std() + 1e-8)
binary = np.where(z_scores > 1, 1,
np.wherez_scores < -1, -1, 0)

return pd.Seriesbinary, index=values.index

class SignalConversionEngine:
"""信号转换核心引擎"""

def __init__self, config_path: str = "config/non_price_signals.yaml":    self.config_path = Path(config_path)
self.config = self._load_config()

self.signal_manager = get_signal_manager()
self.preprocessor = SignalPreprocessorself.config
self.indicator_generator = TechnicalIndicatorGeneratorself.config
self.fusion_engine = SignalFusionEngineself.config

self.conversion_rules = self._load_conversion_rules()

logger.info"Signal Conversion Engine initialized"

def _load_configself -> Dict[str, Any]:
"""加载配置文件"""
try:    with open(self.config_path, 'r', encoding='utf-8') as f:
return yaml.safe_loadf
except FileNotFoundError:
logger.warningf"Config file not found: {self.config_path}"
return self._get_default_config()
except Exception as e:
logger.errorf"Failed to load config: {e}"
return self._get_default_config()

def _get_default_configself -> Dict[str, Any]:
"""获取默认配置"""
return {
'conversion_rules': {
'hibor': {
'indicators': ['RSI', 'MACD', 'Bollinger', 'Stochastic'],
'rsi': {'timeperiods': [14, 21]},
'macd': {'fastperiod': 12, 'slowperiod': 26, 'signalperiod': 9},
'bollinger': {'timeperiod': 20, 'nbdevup': 2, 'nbdevdn': 2},
'stochastic': {'fastk_period': 5, 'slowk_period': 3, 'slowd_period': 3}
},
'monetary_base': {
'indicators': ['Rate_of_Change', 'Moving_Average', 'MACD'],
'roc': {'timeperiods': [10, 20, 30]},
'moving_average': {'periods': [5, 10, 20], 'types': ['SMA', 'EMA']},
'macd': {'fastperiod': 12, 'slowperiod': 26, 'signalperiod': 9}
},
'exchange_rate': {
'indicators': ['RSI', 'Bollinger', 'Williams_R'],
'rsi': {'timeperiods': [14, 21]},
'bollinger': {'timeperiod': 20, 'nbdevup': 2, 'nbdevdn': 2},
'williams_r': {'timeperiod': 14}
},
'interbank_liquidity': {
'indicators': ['Rate_of_Change', 'Stochastic', 'ATR'],
'roc': {'timeperiods': [10, 20]},
'stochastic': {'fastk_period': 5, 'slowk_period': 3, 'slowd_period': 3},
'atr': {'timeperiod': 14}
},
'efbn': {
'indicators': ['RSI', 'MACD', 'Moving_Average'],
'rsi': {'timeperiods': [14]},
'macd': {'fastperiod': 12, 'slowperiod': 26, 'signalperiod': 9},
'moving_average': {'periods': [5, 10, 20], 'types': ['SMA']}
},
'rmb_liquidity': {
'indicators': ['Rate_of_Change', 'Bollinger'],
'roc': {'timeperiods': [10, 20]},
'bollinger': {'timeperiod': 20, 'nbdevup': 2, 'nbdevdn': 2}
}
},
'preprocessing': {
'missing_values': {'method': 'forward_fill'},
'outliers': {'method': 'iqr', 'threshold': 1.5, 'action': 'clip'},
'smoothing': {'method': 'exponential', 'alpha': 0.3},
'normalization': {'method': 'zscore'}
},
'fusion': {
'default_method': 'weighted_average',
'enable_pca': True,
'enable_adaptive': True,
'min_signals_for_fusion': 2
}
}

def _load_conversion_rulesself -> Dict[str, ConversionRule]:
"""加载转换规则"""
rules = {}
for signal_type, rule_config in self.config.get'conversion_rules', {}.items():    rules[signal_type] = ConversionRule(
source_signal_type=signal_type,
indicator_types=rule_config.get'indicators', [],
parameters=rule_config,
weight=1.0,
preprocessing=self.config.get'preprocessing', {},
postprocessing={}
)
return rules

def convert_signals_to_indicators(
self,
signal_types: List[str],
start_date: datetime,
end_date: datetime,
enable_fusion: bool = True
) -> Dict[str, List[TechnicalIndicatorSignal]]:
"""将非价格信号转换为技术指标"""
logger.infof"Converting signals to indicators for types: {signal_types}"

all_indicators = {}

# 获取原始信号数据
for signal_type in signal_types:
if signal_type not in self.conversion_rules:
logger.warningf"No conversion rule for signal type: {signal_type}"
continue

try:

raw_signals = self.signal_manager.get_signal_data(
signal_type, start_date, end_date
)

if not raw_signals:
logger.warningf"No data available for signal type: {signal_type}"
continue

processed_data = self.preprocessor.preprocess_signalsraw_signals, signal_type

conversion_rule = self.conversion_rules[signal_type]
indicator_configs = {
indicator: conversion_rule.parameters.get(indicator.lower(), {})
for indicator in conversion_rule.indicator_types
}

indicators = self.indicator_generator.generate_indicators(
processed_data, signal_type, indicator_configs
)

all_indicators[signal_type] = indicators
logger.info(f"Generated {lenindicators} indicators for {signal_type}")

except Exception as e:
logger.errorf"Failed to convert {signal_type}: {e}"
all_indicators[signal_type] = []

if enable_fusion and lenall_indicators > 1:
try:    fused_indicators = self._perform_signal_fusion(all_indicators)
if fused_indicators:    all_indicators['fused'] = fused_indicators
logger.info(f"Generated {lenfused_indicators} fused indicators")
except Exception as e:
logger.errorf"Failed to perform signal fusion: {e}"

return all_indicators

def _perform_signal_fusionself, all_indicators: Dict[str, List[TechnicalIndicatorSignal]] -> List[TechnicalIndicatorSignal]:
"""执行信号融合"""

all_technical_indicators = []
for signal_type, indicators in all_indicators.items():
all_technical_indicators.extendindicators

if lenall_technical_indicators < 2:
return []

fusion_method = self.config.get'fusion', {}.get'default_method', 'weighted_average'
min_signals = self.config.get'fusion', {}.get'min_signals_for_fusion', 2

# 尝试不同的融合方法
fusion_methods = [fusion_method]
if self.config.get'fusion', {}.get'enable_pca', True:
fusion_methods.append'pca_fusion'
if self.config.get'fusion', {}.get'enable_adaptive', True:
fusion_methods.append'adaptive_weighting'

fused_indicators = []
for method in fusion_methods:
try:    fused_indicator = self.fusion_engine.fuse_signals(all_technical_indicators, method)
fused_indicators.appendfused_indicator
except Exception as e:
logger.debugf"Fusion method {method} failed: {e}"
continue

return fused_indicators

def get_conversion_statisticsself -> Dict[str, Any]:
"""获取转换统计信息"""
return {
'config_path': strself.config_path,
'conversion_rules_count': lenself.conversion_rules,
'supported_signal_types': list(self.conversion_rules.keys()),
'preprocessors_initialized': True,
'fusion_engine_initialized': True,
'supported_fusion_methods': list(self.fusion_engine.fusion_methods.keys())
}

_conversion_engine = None

def get_conversion_engine() -> SignalConversionEngine:
"""获取信号转换引擎实例"""
global _conversion_engine
if not _conversion_engine:    _conversion_engine = SignalConversionEngine()
return _conversion_engine