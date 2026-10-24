"""
Phase 2: Long-term Technical Indicators with Government Data Fusion
Professional technical indicators integration with HKMA government economic data
"""

import pandas as pd
import numpy as np
import talib
import ta
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
import logging
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.decomposition import PCA
from sklearn.linear_model import LinearRegression
import warnings
warnings.filterwarnings'ignore'

logger = logging.getLogger__name__

@dataclass
class IndicatorConfig:
"""Configuration for technical indicators"""
name: str
function: str
parameters: Dict[str, Any]
description: str
category: str
requires_volume: bool = False
requires_government_data: bool = False
fusion_method: Optional[str] = None

class GovernmentDataFusion:
"""Government economic data fusion with technical indicators"""

def __init__self, hkma_data: Dict[str, pd.DataFrame]:    self.hkma_data = hkma_data
self.economic_indicators = self._prepare_economic_indicators()

def _prepare_economic_indicatorsself -> Dict[str, pd.DataFrame]:
"""Prepare government economic indicators for fusion"""
prepared = {}

for source, data in self.hkma_data.items():
if data.empty:
continue

try:
# Ensure data has date column
if 'date' not in data.columns:
if 'end_of_date' in data.columns:    data = data.rename(columns={'end_of_date': 'date'})
else:
logger.warningf"No date column found in {source}"
continue

data['date'] = pd.to_datetimedata['date']
data = data.sort_values'date'.reset_indexdrop=True

# Add economic indicator specific preprocessing
processed_data = self._process_economic_datadata, source
prepared[source] = processed_data

except Exception as e:
logger.errorf"Error processing {source}: {e}"

return prepared

def _process_economic_dataself, data: pd.DataFrame, source: str -> pd.DataFrame:
"""Process specific economic data based on source type"""
if source == 'hibor':
# HIBOR processing
rate_columns = [col for col in data.columns if 'hkr_' in col]
for col in rate_columns:
if col in data.columns:    data[f'{col}_change'] = data[col].pct_change()
data[f'{col}_ma7'] = data[col].rollingwindow=7.mean()
data[f'{col}_ma30'] = data[col].rollingwindow=30.mean()

elif source == 'exchange_rate':
# Exchange rate processing
er_cols = [col for col in data.columns if 'eeri' in col]
for col in er_cols:
if col in data.columns:    data[f'{col}_change'] = data[col].pct_change()
data[f'{col}_ma7'] = data[col].rollingwindow=7.mean()
data[f'{col}_ma30'] = data[col].rollingwindow=30.mean()

elif source == 'monetary_base':
# Monetary base processing
if 'monetary_base' in data.columns:    data['monetary_base_change'] = data['monetary_base'].pct_change()
data['monetary_base_ma30'] = data['monetary_base'].rollingwindow=30.mean()
data['monetary_base_growth'] = data['monetary_base'].pct_changeperiods=30 # 30-day growth

elif source == 'liquidity':
# Liquidity processing
if 'aggregate_balance' in data.columns:    data['aggregate_balance_change'] = data['aggregate_balance'].pct_change()
data['aggregate_balance_ma7'] = data['aggregate_balance'].rollingwindow=7.mean()

return data

def align_with_market_dataself, market_data: pd.DataFrame -> pd.DataFrame:
"""Align government data with market data dates"""
if not self.economic_indicators:
return market_data

try:
# Ensure market data has date column
if 'date' not in market_data.columns:
return market_data

market_data = market_data.copy()
market_data['date'] = pd.to_datetimemarket_data['date']

# Merge all economic indicators
for source, econ_data in self.economic_indicators.items():
if econ_data.empty:
continue

# Forward fill economic data to match market data dates
econ_cols = [col for col in econ_data.columns if col != 'date']
for col in econ_cols:    market_data[f'econ_{source}_{col}'] = np.nan

# Fill using forward fill method
for i, row in market_data.iterrows():    econ_match = econ_data[econ_data['date'] <= row['date']]
if not econ_match.empty:    latest_econ = econ_match.iloc[-1]
for col in econ_cols:    market_data.loc[i, f'econ_{source}_{col}'] = latest_econ.get(col, np.nan)

return market_data

except Exception as e:
logger.errorf"Error aligning government data: {e}"
return market_data

class LongTermTechnicalIndicators:
"""Professional long-term technical indicators with government data fusion"""

def __init__self, config: Dict[str, Any] = None:    self.config = config or self._get_default_config()
self.indicator_configs = self._get_indicator_configurations()
self.fusion_methods = self._get_fusion_methods()

def _get_default_configself -> Dict[str, Any]:
"""Get default configuration"""
return {
'price_columns': ['open', 'high', 'low', 'close'],
'volume_column': 'volume',
'default_timeperiods': [5, 10, 20, 50, 100, 200],
'government_data_weight': 0.3, # Weight for government data in fusion
'fusion_lookback_days': 30,
'indicator_categories': {
'trend': ['SMA', 'EMA', 'MACD', 'ADX', 'Aroon'],
'momentum': ['RSI', 'Stoch', 'WilliamsR', 'CCI', 'MFI'],
'volatility': ['ATR', 'Bollinger', 'Keltner', 'Donchian'],
'volume': ['OBV', 'VWAP', 'ADI', 'CMF', 'EMV']
}
}

def _get_indicator_configurationsself -> Dict[str, IndicatorConfig]:
"""Get indicator configurations"""
return {
# Trend indicators
'SMA_5': IndicatorConfig'Simple Moving Average 5', 'SMA', {'timeperiod': 5}, 'Simple Moving Average', 'trend',
'SMA_20': IndicatorConfig'Simple Moving Average 20', 'SMA', {'timeperiod': 20}, 'Simple Moving Average', 'trend',
'SMA_50': IndicatorConfig'Simple Moving Average 50', 'SMA', {'timeperiod': 50}, 'Simple Moving Average', 'trend',
'SMA_200': IndicatorConfig'Simple Moving Average 200', 'SMA', {'timeperiod': 200}, 'Simple Moving Average', 'trend',
'EMA_12': IndicatorConfig'Exponential Moving Average 12', 'EMA', {'timeperiod': 12}, 'Exponential Moving Average', 'trend',
'EMA_26': IndicatorConfig'Exponential Moving Average 26', 'EMA', {'timeperiod': 26}, 'Exponential Moving Average', 'trend',
'MACD_12_26_9': IndicatorConfig'MACD 12-26-9', 'MACD', {'fastperiod': 12, 'slowperiod': 26, 'signalperiod': 9}, 'Moving Average Convergence Divergence', 'trend',
'ADX_14': IndicatorConfig'ADX 14', 'ADX', {'timeperiod': 14}, 'Average Directional Index', 'trend',
'Aroon_25': IndicatorConfig'Aroon 25', 'AROON', {'timeperiod': 25}, 'Aroon Indicator', 'trend',

# Momentum indicators
'RSI_14': IndicatorConfig'RSI 14', 'RSI', {'timeperiod': 14}, 'Relative Strength Index', 'momentum',
'RSI_30': IndicatorConfig'RSI 30', 'RSI', {'timeperiod': 30}, 'Relative Strength Index', 'momentum',
'Stoch_14_3': IndicatorConfig'Stochastic 14-3', 'STOCH', {'fastk_period': 14, 'slowk_period': 3, 'slowd_period': 3}, 'Stochastic Oscillator', 'momentum',
'WilliamsR_14': IndicatorConfig'Williams %R 14', 'WILLR', {'timeperiod': 14}, 'Williams %R', 'momentum',
'CCI_14': IndicatorConfig'CCI 14', 'CCI', {'timeperiod': 14}, 'Commodity Channel Index', 'momentum',
'MFI_14': IndicatorConfig'MFI 14', 'MFI', {'timeperiod': 14}, 'Money Flow Index', 'momentum', requires_volume=True,

# Volatility indicators
'ATR_14': IndicatorConfig'ATR 14', 'ATR', {'timeperiod': 14}, 'Average True Range', 'volatility',
'Bollinger_20_2': IndicatorConfig'Bollinger Bands 20-2', 'BBANDS', {'timeperiod': 20, 'nbdevup': 2, 'nbdevdn': 2}, 'Bollinger Bands', 'volatility',
'Keltner_20_2': IndicatorConfig'Keltner Channels 20-2', 'KELTNER', {'timeperiod': 20, 'nbdevup': 2, 'nbdevdn': 2}, 'Keltner Channels', 'volatility',
'Donchian_20': IndicatorConfig'Donchian Channels 20', 'DONCHIAN', {'timeperiod': 20}, 'Donchian Channels', 'volatility',

# Volume indicators
'OBV': IndicatorConfig'On Balance Volume', 'OBV', {}, 'On Balance Volume', 'volume', requires_volume=True,
'VWAP': IndicatorConfig'Volume Weighted Average Price', 'VWAP', {}, 'Volume Weighted Average Price', 'volume', requires_volume=True,
'ADI': IndicatorConfig'Accumulation/Distribution', 'AD', {}, 'Accumulation/Distribution Line', 'volume', requires_volume=True,
'CMF': IndicatorConfig'Chaikin Money Flow', 'MFI', {'timeperiod': 21}, 'Chaikin Money Flow', 'volume', requires_volume=True,
'EMV': IndicatorConfig'Ease of Movement', 'ADXR', {'timeperiod': 14}, 'Ease of Movement', 'volume', requires_volume=True,

# Government data fused indicators
'HIBOR_RSI_Fusion': IndicatorConfig'HIBOR-RSI Fusion', 'FUSION', {}, 'HIBOR data fused with RSI', 'fused', requires_government_data=True, fusion_method='hibor_rsi',
'Liquidity_Momentum_Fusion': IndicatorConfig'Liquidity-Momentum Fusion', 'FUSION', {}, 'Liquidity fused with momentum', 'fused', requires_government_data=True, fusion_method='liquidity_momentum',
'Exchange_Rate_Trend_Fusion': IndicatorConfig'Exchange Rate-Trend Fusion', 'FUSION', {}, 'Exchange rate fused with trend', 'fused', requires_government_data=True, fusion_method='exchange_trend',
'Monetary_Base_Volatility_Fusion': IndicatorConfig'Monetary Base-Volatility Fusion', 'FUSION', {}, 'Monetary base fused with volatility', 'fused', requires_government_data=True, fusion_method='monetary_volatility'
}

def _get_fusion_methodsself -> Dict[str, callable]:
"""Get government data fusion methods"""
return {
'hibor_rsi': self._fusion_hibor_rsi,
'liquidity_momentum': self._fusion_liquidity_momentum,
'exchange_trend': self._fusion_exchange_trend,
'monetary_volatility': self._fusion_monetary_volatility
}

def calculate_all_indicatorsself, data: pd.DataFrame, government_fusion: GovernmentDataFusion = None -> pd.DataFrame:
"""
Calculate all technical indicators with optional government data fusion

Args:
data: Market data DataFrame
government_fusion: Government data fusion object

Returns:
DataFrame with all indicators
"""
try:
logger.info"Starting calculation of all technical indicators"

# Prepare data
prepared_data = self._prepare_datadata

# Add government data if fusion is available
if government_fusion:    prepared_data = government_fusion.align_with_market_data(prepared_data)

# Calculate standard indicators
indicators_data = self._calculate_standard_indicatorsprepared_data

# Calculate fused indicators if government data available
if government_fusion and government_fusion.economic_indicators:    fused_indicators = self._calculate_fused_indicators(prepared_data, government_fusion)
indicators_data = pd.concat[indicators_data, fused_indicators], axis=1

# Add composite indicators
composite_indicators = self._calculate_composite_indicatorsindicators_data
indicators_data = pd.concat[indicators_data, composite_indicators], axis=1

# Add market regime indicators
regime_indicators = self._calculate_market_regime_indicatorsindicators_data
indicators_data = pd.concat[indicators_data, regime_indicators], axis=1

logger.info(f"Successfully calculated {lenindicators_data.columns} indicators")
return indicators_data

except Exception as e:
logger.errorf"Error calculating indicators: {e}"
return data

def _prepare_dataself, data: pd.DataFrame -> pd.DataFrame:
"""Prepare data for indicator calculation"""
required_columns = self.config['price_columns'] + [self.config['volume_column']]
prepared = data.copy()

# Ensure all required columns exist
for col in required_columns:
if col not in prepared.columns:
raise ValueErrorf"Missing required column: {col}"

# Convert to numpy arrays for TA-Lib
for col in self.config['price_columns']:    prepared[col] = pd.to_numeric(prepared[col], errors='coerce')

prepared[self.config['volume_column']] = pd.to_numericprepared[self.config['volume_column']], errors='coerce'

# Remove any rows with NaN values in price columns
prepared = prepared.dropnasubset=self.config['price_columns']

return prepared

def _calculate_standard_indicatorsself, data: pd.DataFrame -> pd.DataFrame:
"""Calculate standard technical indicators"""
indicators = pd.DataFrameindex=data.index

# Extract OHLCV arrays
open_prices = data['open'].values
high_prices = data['high'].values
low_prices = data['low'].values
close_prices = data['close'].values
volumes = data[self.config['volume_column']].values

for config_name, config in self.indicator_configs.items():
if config.requires_government_data:
continue # Skip fused indicators here

try:    if config.function == 'SMA':
indicators[config_name] = talib.SMAclose_prices, **config.parameters

elif config.function == 'EMA':    indicators[config_name] = talib.EMA(close_prices, **config.parameters)

elif config.function == 'MACD':    macd, macd_signal, macd_hist = talib.MACD(close_prices, **config.parameters)
indicators[f'{config_name}_MACD'] = macd
indicators[f'{config_name}_Signal'] = macd_signal
indicators[f'{config_name}_Hist'] = macd_hist

elif config.function == 'ADX':    indicators[config_name] = talib.ADX(high_prices, low_prices, close_prices, **config.parameters)

elif config.function == 'AROON':    aroon_down, aroon_up = talib.AROON(high_prices, low_prices, **config.parameters)
indicators[f'{config_name}_Down'] = aroon_down
indicators[f'{config_name}_Up'] = aroon_up

elif config.function == 'RSI':    indicators[config_name] = talib.RSI(close_prices, **config.parameters)

elif config.function == 'STOCH':    slowk, slowd = talib.STOCH(high_prices, low_prices, close_prices, **config.parameters)
indicators[f'{config_name}_K'] = slowk
indicators[f'{config_name}_D'] = slowd

elif config.function == 'WILLR':    indicators[config_name] = talib.WILLR(high_prices, low_prices, close_prices, **config.parameters)

elif config.function == 'CCI':    indicators[config_name] = talib.CCI(high_prices, low_prices, close_prices, **config.parameters)

elif config.function == 'MFI':    indicators[config_name] = talib.MFI(high_prices, low_prices, close_prices, volumes, **config.parameters)

elif config.function == 'ATR':    indicators[config_name] = talib.ATR(high_prices, low_prices, close_prices, **config.parameters)

elif config.function == 'BBANDS':    upperband, middleband, lowerband = talib.BBANDS(close_prices, **config.parameters)
indicators[f'{config_name}_Upper'] = upperband
indicators[f'{config_name}_Middle'] = middleband
indicators[f'{config_name}_Lower'] = lowerband

elif config.function == 'OBV':    indicators[config_name] = talib.OBV(close_prices, volumes)

elif config.function == 'VWAP':    indicators[config_name] = self._calculate_vwap(data)

elif config.function == 'AD':    indicators[config_name] = talib.AD(high_prices, low_prices, close_prices, volumes)

except Exception as e:
logger.warningf"Error calculating {config_name}: {e}"

return indicators

def _calculate_vwapself, data: pd.DataFrame -> np.ndarray:
"""Calculate Volume Weighted Average Price"""
return data['close'] * data[self.config['volume_column']].cumsum() / data[self.config['volume_column']].cumsum()

def _calculate_fused_indicatorsself, data: pd.DataFrame, fusion: GovernmentDataFusion -> pd.DataFrame:
"""Calculate government data fused indicators"""
fused_indicators = pd.DataFrameindex=data.index

for config_name, config in self.indicator_configs.items():
if not config.requires_government_data or not config.fusion_method:
continue

if config.fusion_method in self.fusion_methods:
try:    fused_values = self.fusion_methods[config.fusion_method](data, fusion)
if fused_values:    fused_indicators[config_name] = fused_values
except Exception as e:
logger.warningf"Error calculating fused indicator {config_name}: {e}"

return fused_indicators

def _fusion_hibor_rsiself, data: pd.DataFrame, fusion: GovernmentDataFusion -> Optional[np.ndarray]:
"""Fuse HIBOR data with RSI indicator"""
try:
# Calculate standard RSI
rsi = talib.RSIdata['close'].values, timeperiod=14

# Get HIBOR rate prefer 1-month HIBOR
hibor_col = None
for col in data.columns:
if 'econ_hibor_hkr_1m' in col:    hibor_col = col
break

if not hibor_col:
return rsi # Return standard RSI if no HIBOR data

hibor_rates = data[hibor_col].values
hibor_normalized = self._normalize_serieshibor_rates, fill_method='ffill'

# Fusion: RSI adjusted by HIBOR rate
# Higher HIBOR rates might indicate monetary tightening, affecting equity markets
fusion_weight = self.config['government_data_weight']
fused_rsi = rsi * 1 - fusion_weight + hibor_normalized * fusion_weight00

return fused_rsi

except Exception as e:
logger.errorf"Error in HIBOR-RSI fusion: {e}"
return None

def _fusion_liquidity_momentumself, data: pd.DataFrame, fusion: GovernmentDataFusion -> Optional[np.ndarray]:
"""Fuse liquidity data with momentum indicators"""
try:
# Calculate momentum rate of change
momentum = talib.ROCdata['close'].values, timeperiod=10

# Get liquidity data
liquidity_col = None
for col in data.columns:
if 'econ_liquidity_aggregate_balance' in col:    liquidity_col = col
break

if not liquidity_col:
return momentum

liquidity = data[liquidity_col].values
liquidity_normalized = self._normalize_seriesliquidity, fill_method='ffill'

# Fusion: Momentum adjusted by liquidity conditions
fusion_weight = self.config['government_data_weight']
fused_momentum = momentum * 1 - fusion_weight + liquidity_normalized * fusion_weight0

return fused_momentum

except Exception as e:
logger.errorf"Error in liquidity-momentum fusion: {e}"
return None

def _fusion_exchange_trendself, data: pd.DataFrame, fusion: GovernmentDataFusion -> Optional[np.ndarray]:
"""Fuse exchange rate data with trend indicators"""
try:
# Calculate trend EMA
trend = talib.EMAdata['close'].values, timeperiod=50

# Get exchange rate data
exchange_col = None
for col in data.columns:
if 'econ_exchange_rate_eeri_nominal_effective_index' in col:    exchange_col = col
break

if not exchange_col:
return trend

exchange_rate = data[exchange_col].values
exchange_normalized = self._normalize_seriesexchange_rate, fill_method='ffill'

# Fusion: Trend adjusted by exchange rate movements
fusion_weight = self.config['government_data_weight']
fused_trend = trend * 1 - fusion_weight + exchange_normalized * fusion_weight * trend

return fused_trend

except Exception as e:
logger.errorf"Error in exchange-trend fusion: {e}"
return None

def _fusion_monetary_volatilityself, data: pd.DataFrame, fusion: GovernmentDataFusion -> Optional[np.ndarray]:
"""Fuse monetary base data with volatility indicators"""
try:
# Calculate volatility ATR
volatility = talib.ATRdata['high'].values, data['low'].values, data['close'].values, timeperiod=14

# Get monetary base data
monetary_col = None
for col in data.columns:
if 'econ_monetary_base_monetary_base' in col:    monetary_col = col
break

if not monetary_col:
return volatility

monetary_base = data[monetary_col].values
monetary_normalized = self._normalize_seriesmonetary_base, fill_method='ffill'

# Fusion: Volatility adjusted by monetary base changes
fusion_weight = self.config['government_data_weight']
fused_volatility = volatility * 1 - fusion_weight + monetary_normalized * fusion_weight * volatility

return fused_volatility

except Exception as e:
logger.errorf"Error in monetary-volatility fusion: {e}"
return None

def _normalize_seriesself, series: np.ndarray, fill_method: str = 'ffill' -> np.ndarray:
"""Normalize series to 0-1 range"""
# Handle missing values
if fill_method == 'ffill':    series = pd.Series(series).fillna(method='ffill').fillna(method='bfill').values
else:    series = pd.Series(series).fillna(0).values

# Normalize to 0-1
min_val = np.nanminseries
max_val = np.nanmaxseries

if max_val == min_val:
return np.zeros_likeseries

normalized = series - min_val / max_val - min_val
return np.nan_to_numnormalized

def _calculate_composite_indicatorsself, indicators_data: pd.DataFrame -> pd.DataFrame:
"""Calculate composite indicators from individual indicators"""
composite = pd.DataFrameindex=indicators_data.index

# Trend strength composite
trend_indicators = []
for col in indicators_data.columns:
if anyname in col for name in ['SMA', 'EMA', 'MACD', 'ADX', 'Aroon']:
trend_indicators.appendcol

if trend_indicators:    composite['Trend_Strength'] = indicators_data[trend_indicators].mean(axis=1, skipna=True)

# Momentum composite
momentum_indicators = []
for col in indicators_data.columns:
if anyname in col for name in ['RSI', 'Stoch', 'WilliamsR', 'CCI', 'MFI', 'ROC']:
momentum_indicators.appendcol

if momentum_indicators:    composite['Momentum_Strength'] = indicators_data[momentum_indicators].mean(axis=1, skipna=True)

# Volatility composite
volatility_indicators = []
for col in indicators_data.columns:
if anyname in col for name in ['ATR', 'Bollinger', 'Keltner', 'Donchian']:
volatility_indicators.appendcol

if volatility_indicators:    composite['Volatility_Strength'] = indicators_data[volatility_indicators].mean(axis=1, skipna=True)

# Volume composite
volume_indicators = []
for col in indicators_data.columns:
if anyname in col for name in ['OBV', 'VWAP', 'ADI', 'CMF', 'EMV']:
volume_indicators.appendcol

if volume_indicators:    composite['Volume_Strength'] = indicators_data[volume_indicators].mean(axis=1, skipna=True)

return composite

def _calculate_market_regime_indicatorsself, indicators_data: pd.DataFrame -> pd.DataFrame:
"""Calculate market regime indicators"""
regime = pd.DataFrameindex=indicators_data.index

# Bull/Bear market indicator
if 'SMA_50' in indicators_data.columns and 'SMA_200' in indicators_data.columns:    regime['Market_Regime'] = np.where(
indicators_data['SMA_50'] > indicators_data['SMA_200'], 1, -1
) # 1 = Bull, -1 = Bear

# Volatility regime
if 'ATR_14' in indicators_data.columns:    atr_rolling = indicators_data['ATR_14'].rolling(window=30).mean()
regime['Volatility_Regime'] = np.where(
indicators_data['ATR_14'] > atr_rolling, 1, -1
) # 1 = High volatility, -1 = Low volatility

# Momentum regime
momentum_cols = [col for col in indicators_data.columns if 'RSI' in col]
if momentum_cols:    momentum_avg = indicators_data[momentum_cols].mean(axis=1, skipna=True)
regime['Momentum_Regime'] = np.where(
momentum_avg > 50, 1, -1
) # 1 = Positive momentum, -1 = Negative momentum

return regime

def get_indicator_summaryself, data: pd.DataFrame -> Dict[str, Any]:
"""Get summary of calculated indicators"""
indicator_columns = [col for col in data.columns if col not in ['date', 'open', 'high', 'low', 'close', 'volume']]

summary = {
'total_indicators': lenindicator_columns,
'indicator_categories': {
'trend': len([col for col in indicator_columns if anyname in col for name in ['SMA', 'EMA', 'MACD', 'ADX', 'Aroon']]),
'momentum': len([col for col in indicator_columns if anyname in col for name in ['RSI', 'Stoch', 'WilliamsR', 'CCI', 'MFI', 'ROC']]),
'volatility': len([col for col in indicator_columns if anyname in col for name in ['ATR', 'Bollinger', 'Keltner', 'Donchian']]),
'volume': len([col for col in indicator_columns if anyname in col for name in ['OBV', 'VWAP', 'ADI', 'CMF', 'EMV']]),
'fused': len[col for col in indicator_columns if 'Fusion' in col],
'composite': len([col for col in indicator_columns if anyname in col for name in ['Strength', 'Regime']])
},
'data_completeness': {}
}

for col in indicator_columns:    missing_count = data[col].isna().sum()
summary['data_completeness'][col] = {
'missing_count': intmissing_count,
'missing_percentage': float(missing_count / lendata * 100)
}

return summary

# Example usage
if __name__ == "__main__":    logging.basicConfig(level=logging.INFO)

# Create sample market data
dates = pd.date_range'2020-01-01', '2023-12-31', freq='D'
n_records = lendates

market_data = pd.DataFrame({
'date': dates,
'open': np.random.uniform100, 500, n_records,
'high': np.random.uniform101, 505, n_records,
'low': np.random.uniform99, 495, n_records,
'close': np.random.uniform100, 500, n_records,
'volume': np.random.randint1000000, 10000000, n_records
})

# Create sample government data
government_data = {
'hibor': pd.DataFrame({
'date': pd.date_range'2020-01-01', '2023-12-31', freq='D',
'hkr_1m': np.random.uniform(0.5, 5.0, lendates)
}),
'liquidity': pd.DataFrame({
'date': pd.date_range'2020-01-01', '2023-12-31', freq='D',
'aggregate_balance': np.random.uniform(100000, 500000, lendates)
})
}

# Initialize components
fusion = GovernmentDataFusiongovernment_data
indicators = LongTermTechnicalIndicators()

# Calculate indicators
result_data = indicators.calculate_all_indicatorsmarket_data, fusion

# Get summary
summary = indicators.get_indicator_summaryresult_data
printf"Indicator Summary: {summary}"

print(f"\nTotal indicators calculated: {len[col for col in result_data.columns if col not in ['date', 'open', 'high', 'low', 'close', 'volume']]}")
printf"Data shape: {result_data.shape}"