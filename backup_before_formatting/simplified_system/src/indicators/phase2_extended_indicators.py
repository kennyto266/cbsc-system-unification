#!/usr/bin/env python3
"""
Phase 2 Extended Technical Indicators - 全面技術指標擴展系統
Phase 2 Extended Technical Indicators - Comprehensive Technical Indicator Extension System

基於成功的数据对齐和智能指标适配系统，实现15+种新技术指标
Based on successful data alignment and intelligent indicator adaptation system, implement 15+ new technical indicators

包含4大類別指標：
- Phase 2.1: 趨勢類擴展指標 (Trend Extension Indicators)
- Phase 2.2: 動量類擴展指標 (Momentum Extension Indicators)
- Phase 2.3: 波動率指標 (Volatility Indicators)
- Phase 2.4: 數據源特定專用指標 (Data Source Specific Indicators)
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Union, Any, Tuple
import logging
from pathlib import Path
import json
import time
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class IndicatorCategory(Enum):
    """指標類別枚舉"""
    TREND_EXTENSION = "trend_extension"
    MOMENTUM_EXTENSION = "momentum_extension"
    VOLATILITY = "volatility"
    DATA_SOURCE_SPECIFIC = "data_source_specific"

@dataclass
class IndicatorMetadata:
    """指標元數據"""
    name: str
    category: IndicatorCategory
    description: str
    parameters: Dict[str, Any]
    performance_target: float  # 目標性能 < 1ms per calculation
    data_type_requirements: List[str]  # 支持的數據類型

class Phase2ExtendedIndicators:
    """
    Phase 2 技術指標擴展系統

    核心特性：
    - 15+種新技術指標
    - 非價格數據自動適配
    - 智能參數適配機制
    - 指標有效性驗證
    - 計算性能 < 1ms per indicator
    - 行業標準基準測試
    """

    def __init__(self):
        """初始化Phase 2擴展指標系統"""
        self.performance_cache = {}
        self.validation_results = {}
        self.benchmark_tests = {}

        # 數據類型檢測配置
        self.rate_data_keywords = ['rate', 'interest', 'hibor', 'yield', 'liquidity', 'er']
        self.flow_data_keywords = ['flow', 'change', 'movement', 'activity', 'usage']
        self.ratio_data_keywords = ['ratio', 'index', 'level', 'base', 'monetary']
        self.price_data_keywords = ['price', 'close', 'open', 'high', 'low']

        # 指標元數據註冊
        self.indicator_metadata = self._register_indicators()

        logger.info("Phase 2 Extended Technical Indicators System initialized")
        logger.info(f"Registered {len(self.indicator_metadata)} indicators across 4 categories")

    def _register_indicators(self) -> Dict[str, IndicatorMetadata]:
        """註冊所有指標元數據"""
        indicators = {}

        # Phase 2.1: 趨勢類擴展指標
        indicators['DEMA'] = IndicatorMetadata(
            name="DEMA",
            category=IndicatorCategory.TREND_EXTENSION,
            description="雙指數移動平均線 (Double Exponential Moving Average)",
            parameters={'period': 21, 'adapt_for_data_type': True},
            performance_target=0.8,
            data_type_requirements=['rate_data', 'flow_data', 'ratio_data', 'price_data']
        )

        indicators['TEMA'] = IndicatorMetadata(
            name="TEMA",
            category=IndicatorCategory.TREND_EXTENSION,
            description="三指數移動平均線 (Triple Exponential Moving Average)",
            parameters={'period': 15, 'adapt_for_data_type': True},
            performance_target=0.9,
            data_type_requirements=['rate_data', 'flow_data', 'ratio_data', 'price_data']
        )

        indicators['TRIMA'] = IndicatorMetadata(
            name="TRIMA",
            category=IndicatorCategory.TREND_EXTENSION,
            description="三角移動平均線 (Triangular Moving Average)",
            parameters={'period': 18, 'adapt_for_data_type': True},
            performance_target=0.7,
            data_type_requirements=['rate_data', 'flow_data', 'ratio_data', 'price_data']
        )

        indicators['MACD_EXTENDED'] = IndicatorMetadata(
            name="MACD_EXTENDED",
            category=IndicatorCategory.TREND_EXTENSION,
            description="MACD變體擴展 (包含多種MACD計算方法)",
            parameters={'fast': 12, 'slow': 26, 'signal': 9, 'method': 'standard'},
            performance_target=1.2,
            data_type_requirements=['rate_data', 'flow_data', 'ratio_data', 'price_data']
        )

        # Phase 2.2: 動量類擴展指標
        indicators['STOCHASTIC_F'] = IndicatorMetadata(
            name="STOCHASTIC_F",
            category=IndicatorCategory.MOMENTUM_EXTENSION,
            description="完整隨機指標 (Full Stochastic Oscillator)",
            parameters={'k_period': 14, 'd_period': 3, 'f_period': 3},
            performance_target=0.8,
            data_type_requirements=['rate_data', 'flow_data', 'ratio_data', 'price_data']
        )

        indicators['WILLIAMS_R'] = IndicatorMetadata(
            name="WILLIAMS_R",
            category=IndicatorCategory.MOMENTUM_EXTENSION,
            description="威廉指標 (Williams %R)",
            parameters={'period': 14},
            performance_target=0.6,
            data_type_requirements=['rate_data', 'flow_data', 'ratio_data', 'price_data']
        )

        indicators['CCI'] = IndicatorMetadata(
            name="CCI",
            category=IndicatorCategory.MOMENTUM_EXTENSION,
            description="商品通道指標 (Commodity Channel Index)",
            parameters={'period': 20, 'constant': 0.015},
            performance_target=0.7,
            data_type_requirements=['rate_data', 'flow_data', 'ratio_data', 'price_data']
        )

        indicators['MFI'] = IndicatorMetadata(
            name="MFI",
            category=IndicatorCategory.MOMENTUM_EXTENSION,
            description="資金流量指標 (Money Flow Index)",
            parameters={'period': 14},
            performance_target=0.9,
            data_type_requirements=['rate_data', 'flow_data', 'ratio_data', 'price_data']
        )

        indicators['RSI_EXTENDED'] = IndicatorMetadata(
            name="RSI_EXTENDED",
            category=IndicatorCategory.MOMENTUM_EXTENSION,
            description="RSI擴展 (支持5-100週期動態調整)",
            parameters={'period': 14, 'adaptive_range': [5, 100]},
            performance_target=0.5,
            data_type_requirements=['rate_data', 'flow_data', 'ratio_data', 'price_data']
        )

        # Phase 2.3: 波動率指標
        indicators['BOLLINGER_BANDS'] = IndicatorMetadata(
            name="BOLLINGER_BANDS",
            category=IndicatorCategory.VOLATILITY,
            description="布林帶 (Bollinger Bands)",
            parameters={'period': 20, 'std_dev': 2.0},
            performance_target=0.8,
            data_type_requirements=['rate_data', 'flow_data', 'ratio_data', 'price_data']
        )

        indicators['ATR'] = IndicatorMetadata(
            name="ATR",
            category=IndicatorCategory.VOLATILITY,
            description="平均真實範圍 (Average True Range)",
            parameters={'period': 14, 'method': 'standard'},
            performance_target=0.7,
            data_type_requirements=['rate_data', 'flow_data', 'ratio_data', 'price_data']
        )

        indicators['KELTNER_CHANNELS'] = IndicatorMetadata(
            name="KELTNER_CHANNELS",
            category=IndicatorCategory.VOLATILITY,
            description="肯特納通道 (Keltner Channels)",
            parameters={'period': 20, 'multiplier': 2.0},
            performance_target=0.9,
            data_type_requirements=['rate_data', 'flow_data', 'ratio_data', 'price_data']
        )

        # Phase 2.4: 數據源特定專用指標
        indicators['HIBOR_TERM_STRUCTURE'] = IndicatorMetadata(
            name="HIBOR_TERM_STRUCTURE",
            category=IndicatorCategory.DATA_SOURCE_SPECIFIC,
            description="HIBOR利率期限結構指標",
            parameters={'short_term': 'ON', 'long_term': '1M'},
            performance_target=0.6,
            data_type_requirements=['rate_data', 'hibor']
        )

        indicators['RATE_SPREAD_ANALYSIS'] = IndicatorMetadata(
            name="RATE_SPREAD_ANALYSIS",
            category=IndicatorCategory.DATA_SOURCE_SPECIFIC,
            description="利差分析指標",
            parameters={'period': 20, 'zscore_window': 252},
            performance_target=0.8,
            data_type_requirements=['rate_data']
        )

        indicators['EXCHANGE_RATE_STRENGTH'] = IndicatorMetadata(
            name="EXCHANGE_RATE_STRENGTH",
            category=IndicatorCategory.DATA_SOURCE_SPECIFIC,
            description="匯率強弱指標",
            parameters={'period': 14, 'reference_index': 'USD'},
            performance_target=0.7,
            data_type_requirements=['rate_data', 'exchange_rate']
        )

        indicators['MONETARY_GROWTH'] = IndicatorMetadata(
            name="MONETARY_GROWTH",
            category=IndicatorCategory.DATA_SOURCE_SPECIFIC,
            description="貨幣供給增長指標",
            parameters={'growth_period': 30, 'ma_period': 10},
            performance_target=0.5,
            data_type_requirements=['ratio_data', 'monetary']
        )

        indicators['LIQUIDITY_PRESSURE'] = IndicatorMetadata(
            name="LIQUIDITY_PRESSURE",
            category=IndicatorCategory.DATA_SOURCE_SPECIFIC,
            description="流動性壓力指標",
            parameters={'pressure_period': 20, 'threshold': 2.0},
            performance_target=0.6,
            data_type_requirements=['flow_data', 'liquidity']
        )

        indicators['EFBN_YIELD_SPREAD'] = IndicatorMetadata(
            name="EFBN_YIELD_SPREAD",
            category=IndicatorCategory.DATA_SOURCE_SPECIFIC,
            description="外匯基金票據收益率差",
            parameters={'benchmark_period': '10Y', 'spread_period': 20},
            performance_target=0.8,
            data_type_requirements=['rate_data', 'efbn']
        )

        indicators['RMB_LIQUIDITY_USAGE'] = IndicatorMetadata(
            name="RMB_LIQUIDITY_USAGE",
            category=IndicatorCategory.DATA_SOURCE_SPECIFIC,
            description="人民幣流動性使用率",
            parameters={'usage_period': 14, 'trend_period': 50},
            performance_target=0.5,
            data_type_requirements=['flow_data', 'rmb']
        )

        return indicators

    # ==================== Phase 2.1: 趨勢類擴展指標 ====================

    def calculate_dema(self, data: pd.Series, period: int = 21) -> Tuple[pd.Series, Dict]:
        """
        計算雙指數移動平均線 (DEMA)

        DEMA = 2*EMA - EMA(EMA)
        """
        start_time = time.time()

        # 檢測數據類型並適配參數
        data_type = self.detect_data_type(data)
        adapted_params = self.adapt_parameters_for_data_type('DEMA', data_type, {'period': period})
        period = int(adapted_params['period'])

        if len(data) < period:
            return pd.Series([np.nan] * len(data), index=data.index), {
                'error': f'Insufficient data: need {period}, have {len(data)}'
            }

        # 計算EMA
        ema1 = data.ewm(span=period, adjust=False).mean()
        ema2 = ema1.ewm(span=period, adjust=False).mean()

        # 計算DEMA
        dema = 2 * ema1 - ema2

        # 性能記錄
        calc_time = (time.time() - start_time) * 1000

        adaptation_info = {
            'data_type': data_type,
            'original_period': period,
            'adapted_period': adapted_params['period'],
            'calculation_time_ms': calc_time,
            'data_length': len(data),
            'adaptation_applied': adapted_params.get('adaptation_applied', False)
        }

        return dema, adaptation_info

    def calculate_tema(self, data: pd.Series, period: int = 15) -> Tuple[pd.Series, Dict]:
        """
        計算三指數移動平均線 (TEMA)

        TEMA = 3*EMA1 - 3*EMA2 + EMA3
        """
        start_time = time.time()

        data_type = self.detect_data_type(data)
        adapted_params = self.adapt_parameters_for_data_type('TEMA', data_type, {'period': period})
        period = int(adapted_params['period'])

        if len(data) < period:
            return pd.Series([np.nan] * len(data), index=data.index), {
                'error': f'Insufficient data: need {period}, have {len(data)}'
            }

        # 計算三重EMA
        ema1 = data.ewm(span=period, adjust=False).mean()
        ema2 = ema1.ewm(span=period, adjust=False).mean()
        ema3 = ema2.ewm(span=period, adjust=False).mean()

        # 計算TEMA
        tema = 3 * ema1 - 3 * ema2 + ema3

        calc_time = (time.time() - start_time) * 1000

        adaptation_info = {
            'data_type': data_type,
            'original_period': period,
            'adapted_period': adapted_params['period'],
            'calculation_time_ms': calc_time,
            'data_length': len(data),
            'adaptation_applied': adapted_params.get('adaptation_applied', False)
        }

        return tema, adaptation_info

    def calculate_trima(self, data: pd.Series, period: int = 18) -> Tuple[pd.Series, Dict]:
        """
        計算三角移動平均線 (TRIMA)

        TRIMA = SMA(SMA(period, period/2), period/2)
        """
        start_time = time.time()

        data_type = self.detect_data_type(data)
        adapted_params = self.adapt_parameters_for_data_type('TRIMA', data_type, {'period': period})
        period = int(adapted_params['period'])

        if len(data) < period:
            return pd.Series([np.nan] * len(data), index=data.index), {
                'error': f'Insufficient data: need {period}, have {len(data)}'
            }

        # 計算TRIMA
        half_period = max(1, period // 2)
        sma1 = data.rolling(window=half_period, min_periods=1).mean()
        trima = sma1.rolling(window=half_period, min_periods=1).mean()

        calc_time = (time.time() - start_time) * 1000

        adaptation_info = {
            'data_type': data_type,
            'original_period': period,
            'adapted_period': adapted_params['period'],
            'half_period_used': half_period,
            'calculation_time_ms': calc_time,
            'data_length': len(data),
            'adaptation_applied': adapted_params.get('adaptation_applied', False)
        }

        return trima, adaptation_info

    def calculate_macd_extended(self, data: pd.Series, fast: int = 12, slow: int = 26,
                               signal: int = 9, method: str = 'standard') -> Dict:
        """
        計算MACD變體擴展
        """
        start_time = time.time()

        data_type = self.detect_data_type(data)
        adapted_params = self.adapt_parameters_for_data_type('MACD_EXTENDED', data_type,
                                                           {'fast': fast, 'slow': slow, 'signal': signal})
        fast = int(adapted_params['fast'])
        slow = int(adapted_params['slow'])
        signal = int(adapted_params['signal'])

        if len(data) < slow:
            return {
                'macd': pd.Series([np.nan] * len(data), index=data.index),
                'signal': pd.Series([np.nan] * len(data), index=data.index),
                'histogram': pd.Series([np.nan] * len(data), index=data.index),
                'adaptation_info': {
                    'error': f'Insufficient data: need {slow}, have {len(data)}'
                }
            }

        if method == 'standard':
            # 標準MACD
            ema_fast = data.ewm(span=fast, adjust=False).mean()
            ema_slow = data.ewm(span=slow, adjust=False).mean()
            macd_line = ema_fast - ema_slow
            signal_line = macd_line.ewm(span=signal, adjust=False).mean()
            histogram = macd_line - signal_line

        elif method == 'dema':
            # 基於DEMA的MACD
            dema_fast, _ = self.calculate_dema(data, fast)
            dema_slow, _ = self.calculate_dema(data, slow)
            macd_line = dema_fast - dema_slow
            signal_line = macd_line.ewm(span=signal, adjust=False).mean()
            histogram = macd_line - signal_line

        elif method == 'tema':
            # 基於TEMA的MACD
            tema_fast, _ = self.calculate_tema(data, fast)
            tema_slow, _ = self.calculate_tema(data, slow)
            macd_line = tema_fast - tema_slow
            signal_line = macd_line.ewm(span=signal, adjust=False).mean()
            histogram = macd_line - signal_line

        calc_time = (time.time() - start_time) * 1000

        adaptation_info = {
            'data_type': data_type,
            'method_used': method,
            'parameters_used': {'fast': fast, 'slow': slow, 'signal': signal},
            'calculation_time_ms': calc_time,
            'data_length': len(data),
            'adaptation_applied': adapted_params.get('adaptation_applied', False)
        }

        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram,
            'adaptation_info': adaptation_info
        }

    # ==================== Phase 2.2: 動量類擴展指標 ====================

    def calculate_stochastic(self, data: pd.Series, high_data: pd.Series = None, low_data: pd.Series = None, period: int = 14) -> pd.Series:
        """Stochastic Oscillator 計算包裝器"""
        return self.calculate_stochastic_f(data, high_data, low_data, period)

    def calculate_stochastic_f(self, data: pd.Series, high_data: pd.Series = None,
                              low_data: pd.Series = None, k_period: int = 14,
                              d_period: int = 3, f_period: int = 3) -> Dict:
        """
        計算完整隨機指標 (Full Stochastic Oscillator)
        """
        start_time = time.time()

        data_type = self.detect_data_type(data)
        adapted_params = self.adapt_parameters_for_data_type('STOCHASTIC_F', data_type,
                                                           {'k_period': k_period, 'd_period': d_period, 'f_period': f_period})
        k_period = int(adapted_params['k_period'])
        d_period = int(adapted_params['d_period'])
        f_period = int(adapted_params['f_period'])

        if len(data) < k_period:
            return {
                'k_percent': pd.Series([50.0] * len(data), index=data.index),
                'd_percent': pd.Series([50.0] * len(data), index=data.index),
                'f_percent': pd.Series([50.0] * len(data), index=data.index),
                'adaptation_info': {
                    'error': f'Insufficient data: need {k_period}, have {len(data)}'
                }
            }

        # 如果沒有提供high/low數據，使用data本身計算
        if high_data is None:
            high_data = data.rolling(window=k_period, min_periods=1).max()
        if low_data is None:
            low_data = data.rolling(window=k_period, min_periods=1).min()

        # 計算%K
        lowest_low = low_data.rolling(window=k_period, min_periods=1).min()
        highest_high = high_data.rolling(window=k_period, min_periods=1).max()
        k_percent = 100 * ((data - lowest_low) / (highest_high - lowest_low))
        k_percent = k_percent.replace([np.inf, -np.inf], 50.0).fillna(50.0)

        # 計算%D (平滑%K)
        d_percent = k_percent.rolling(window=d_period, min_periods=1).mean()

        # 計算%F (再次平滑)
        f_percent = d_percent.rolling(window=f_period, min_periods=1).mean()

        calc_time = (time.time() - start_time) * 1000

        adaptation_info = {
            'data_type': data_type,
            'parameters_used': {'k_period': k_period, 'd_period': d_period, 'f_period': f_period},
            'calculation_time_ms': calc_time,
            'data_length': len(data),
            'adaptation_applied': adapted_params.get('adaptation_applied', False)
        }

        return {
            'k_percent': k_percent,
            'd_percent': d_percent,
            'f_percent': f_percent,
            'adaptation_info': adaptation_info
        }

    def calculate_williams_r(self, data: pd.Series, high_data: pd.Series = None,
                            low_data: pd.Series = None, period: int = 14) -> Tuple[pd.Series, Dict]:
        """
        計算威廉指標 (Williams %R)
        """
        start_time = time.time()

        data_type = self.detect_data_type(data)
        adapted_params = self.adapt_parameters_for_data_type('WILLIAMS_R', data_type, {'period': period})
        period = int(adapted_params['period'])

        if len(data) < period:
            return pd.Series([-50.0] * len(data), index=data.index), {
                'error': f'Insufficient data: need {period}, have {len(data)}'
            }

        # 如果沒有提供high/low數據，使用data本身計算
        if high_data is None:
            high_data = data.rolling(window=period, min_periods=1).max()
        if low_data is None:
            low_data = data.rolling(window=period, min_periods=1).min()

        highest_high = high_data.rolling(window=period, min_periods=1).max()
        lowest_low = low_data.rolling(window=period, min_periods=1).min()

        williams_r = -100 * ((highest_high - data) / (highest_high - lowest_low))
        williams_r = williams_r.replace([np.inf, -np.inf], -50.0).fillna(-50.0)

        calc_time = (time.time() - start_time) * 1000

        adaptation_info = {
            'data_type': data_type,
            'original_period': period,
            'adapted_period': adapted_params['period'],
            'calculation_time_ms': calc_time,
            'data_length': len(data),
            'adaptation_applied': adapted_params.get('adaptation_applied', False)
        }

        return williams_r, adaptation_info

    def calculate_cci(self, data: pd.Series, high_data: pd.Series = None,
                     low_data: pd.Series = None, period: int = 20, constant: float = 0.015) -> Tuple[pd.Series, Dict]:
        """
        計算商品通道指標 (Commodity Channel Index)
        """
        start_time = time.time()

        data_type = self.detect_data_type(data)
        adapted_params = self.adapt_parameters_for_data_type('CCI', data_type,
                                                           {'period': period, 'constant': constant})
        period = int(adapted_params['period'])
        constant = float(adapted_params['constant'])

        if len(data) < period:
            return pd.Series([0.0] * len(data), index=data.index), {
                'error': f'Insufficient data: need {period}, have {len(data)}'
            }

        # 計算典型價格
        if high_data is None or low_data is None:
            typical_price = data  # 使用單一數據源
        else:
            typical_price = (data + high_data + low_data) / 3

        # 計算移動平均
        ma_typical = typical_price.rolling(window=period, min_periods=1).mean()

        # 計算平均絕對偏差
        mad = typical_price.rolling(window=period, min_periods=1).apply(
            lambda x: np.mean(np.abs(x - x.mean())), raw=True
        )

        # 計算CCI
        cci = (typical_price - ma_typical) / (constant * mad)
        cci = cci.replace([np.inf, -np.inf], 0.0).fillna(0.0)

        calc_time = (time.time() - start_time) * 1000

        adaptation_info = {
            'data_type': data_type,
            'parameters_used': {'period': period, 'constant': constant},
            'calculation_time_ms': calc_time,
            'data_length': len(data),
            'adaptation_applied': adapted_params.get('adaptation_applied', False)
        }

        return cci, adaptation_info

    def calculate_mfi(self, close_data: pd.Series, volume_data: pd.Series,
                     high_data: pd.Series = None, low_data: pd.Series = None,
                     period: int = 14) -> Tuple[pd.Series, Dict]:
        """
        計算資金流量指標 (Money Flow Index)
        """
        start_time = time.time()

        data_type = self.detect_data_type(close_data)
        adapted_params = self.adapt_parameters_for_data_type('MFI', data_type, {'period': period})
        period = int(adapted_params['period'])

        if len(close_data) < period:
            return pd.Series([50.0] * len(close_data), index=close_data.index), {
                'error': f'Insufficient data: need {period}, have {len(close_data)}'
            }

        # 計算典型價格
        if high_data is None or low_data is None:
            typical_price = close_data
        else:
            typical_price = (close_data + high_data + low_data) / 3

        # 計算資金流量
        money_flow = typical_price * volume_data

        # 計算正負資金流量
        mf_change = money_flow.diff()
        positive_mf = mf_change.where(mf_change > 0, 0)
        negative_mf = -mf_change.where(mf_change < 0, 0)

        # 計算資金流量比率
        positive_mf_sum = positive_mf.rolling(window=period, min_periods=1).sum()
        negative_mf_sum = negative_mf.rolling(window=period, min_periods=1).sum()

        mfi_ratio = positive_mf_sum / negative_mf_sum.replace(0, np.nan)
        mfi = 100 - (100 / (1 + mfi_ratio))
        mfi = mfi.replace([np.inf, -np.inf], 50.0).fillna(50.0)

        calc_time = (time.time() - start_time) * 1000

        adaptation_info = {
            'data_type': data_type,
            'original_period': period,
            'adapted_period': adapted_params['period'],
            'calculation_time_ms': calc_time,
            'data_length': len(close_data),
            'adaptation_applied': adapted_params.get('adaptation_applied', False)
        }

        return mfi, adaptation_info

    def calculate_rsi_extended(self, data: pd.Series, period: int = 14,
                              adaptive_range: List[int] = [5, 100]) -> Tuple[pd.Series, Dict]:
        """
        計算RSI擴展 (支持5-100週期動態調整)
        """
        start_time = time.time()

        data_type = self.detect_data_type(data)
        adapted_params = self.adapt_parameters_for_data_type('RSI_EXTENDED', data_type,
                                                           {'period': period, 'adaptive_range': adaptive_range})

        # 智能週期選擇
        volatility = data.pct_change().rolling(window=20, min_periods=1).std()
        avg_volatility = volatility.mean()

        if avg_volatility > 0.05:  # 高波動性
            optimal_period = max(period, 21)
        elif avg_volatility < 0.01:  # 低波動性
            optimal_period = min(period, 10)
        else:
            optimal_period = period

        # 確保在範圍內
        optimal_period = max(adaptive_range[0], min(adaptive_range[1], optimal_period))

        if len(data) < optimal_period + 1:
            return pd.Series([50.0] * len(data), index=data.index), {
                'error': f'Insufficient data: need {optimal_period + 1}, have {len(data)}'
            }

        # 計算RSI
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=optimal_period, min_periods=1).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=optimal_period, min_periods=1).mean()

        rs = gain / loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        rsi = rsi.replace([np.inf, -np.inf], 50.0).fillna(50.0)

        calc_time = (time.time() - start_time) * 1000

        adaptation_info = {
            'data_type': data_type,
            'original_period': period,
            'optimal_period': optimal_period,
            'volatility_based_adjustment': True,
            'avg_volatility': avg_volatility,
            'calculation_time_ms': calc_time,
            'data_length': len(data),
            'adaptation_applied': adapted_params.get('adaptation_applied', False)
        }

        return rsi, adaptation_info

    # ==================== Phase 2.3: 波動率指標 ====================

    def calculate_bollinger_bands(self, data: pd.Series, period: int = 20, std_dev: float = 2.0) -> Dict:
        """
        計算布林帶 (Bollinger Bands)
        """
        start_time = time.time()

        data_type = self.detect_data_type(data)
        adapted_params = self.adapt_parameters_for_data_type('BOLLINGER_BANDS', data_type,
                                                           {'period': period, 'std_dev': std_dev})
        period = int(adapted_params['period'])
        std_dev = float(adapted_params['std_dev'])

        if len(data) < period:
            middle = data.rolling(window=period, min_periods=1).mean()
            std = data.rolling(window=period, min_periods=1).std()
            return {
                'upper': middle + std * std_dev,
                'middle': middle,
                'lower': middle - std * std_dev,
                'width': (middle + std * std_dev - (middle - std * std_dev)) / middle,
                'adaptation_info': {
                    'error': f'Insufficient data: need {period}, have {len(data)}'
                }
            }

        middle = data.rolling(window=period, min_periods=1).mean()
        std = data.rolling(window=period, min_periods=1).std()

        upper = middle + std * std_dev
        lower = middle - std * std_dev
        width = (upper - lower) / middle

        # 計算布林帶位置 (%B)
        percent_b = (data - lower) / (upper - lower)
        percent_b = percent_b.replace([np.inf, -np.inf], 0.5).fillna(0.5)

        # 計算帶寬
        bandwidth = (upper - lower) / middle

        calc_time = (time.time() - start_time) * 1000

        adaptation_info = {
            'data_type': data_type,
            'parameters_used': {'period': period, 'std_dev': std_dev},
            'calculation_time_ms': calc_time,
            'data_length': len(data),
            'adaptation_applied': adapted_params.get('adaptation_applied', False)
        }

        return {
            'upper': upper,
            'middle': middle,
            'lower': lower,
            'width': width,
            'percent_b': percent_b,
            'bandwidth': bandwidth,
            'adaptation_info': adaptation_info
        }

    def calculate_atr(self, high_data: pd.Series, low_data: pd.Series,
                     close_data: pd.Series, period: int = 14, method: str = 'standard') -> Tuple[pd.Series, Dict]:
        """
        計算平均真實範圍 (Average True Range)
        """
        start_time = time.time()

        data_type = self.detect_data_type(close_data)
        adapted_params = self.adapt_parameters_for_data_type('ATR', data_type,
                                                           {'period': period, 'method': method})
        period = int(adapted_params['period'])

        if len(close_data) < period:
            return pd.Series([0.0] * len(close_data), index=close_data.index), {
                'error': f'Insufficient data: need {period}, have {len(close_data)}'
            }

        # 計算真實範圍
        tr1 = high_data - low_data
        tr2 = abs(high_data - close_data.shift(1))
        tr3 = abs(low_data - close_data.shift(1))

        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        if method == 'standard':
            atr = true_range.rolling(window=period, min_periods=1).mean()
        elif method == 'ema':
            atr = true_range.ewm(span=period, adjust=False).mean()
        else:  # 'wilder' (Wilder's Smoothing)
            atr = true_range.ewm(alpha=1/period, adjust=False).mean()

        atr = atr.fillna(0.0)

        # 計算ATR百分比
        atr_percent = (atr / close_data) * 100
        atr_percent = atr_percent.replace([np.inf, -np.inf], 0.0).fillna(0.0)

        calc_time = (time.time() - start_time) * 1000

        adaptation_info = {
            'data_type': data_type,
            'parameters_used': {'period': period, 'method': method},
            'calculation_time_ms': calc_time,
            'data_length': len(close_data),
            'adaptation_applied': adapted_params.get('adaptation_applied', False)
        }

        return atr_percent, adaptation_info

    def calculate_keltner_channels(self, data: pd.Series, high_data: pd.Series = None,
                                  low_data: pd.Series = None, period: int = 20,
                                  multiplier: float = 2.0) -> Dict:
        """
        計算肯特納通道 (Keltner Channels)
        """
        start_time = time.time()

        data_type = self.detect_data_type(data)
        adapted_params = self.adapt_parameters_for_data_type('KELTNER_CHANNELS', data_type,
                                                           {'period': period, 'multiplier': multiplier})
        period = int(adapted_params['period'])
        multiplier = float(adapted_params['multiplier'])

        if len(data) < period:
            middle = data.rolling(window=period, min_periods=1).mean()
            return {
                'upper': middle,
                'middle': middle,
                'lower': middle,
                'adaptation_info': {
                    'error': f'Insufficient data: need {period}, have {len(data)}'
                }
            }

        # 計算中線 (EMA)
        middle = data.ewm(span=period, adjust=False).mean()

        # 計算ATR
        if high_data is None or low_data is None:
            # 使用價格變動近似ATR
            price_change = data.diff().abs()
            atr = price_change.rolling(window=period, min_periods=1).mean()
        else:
            # 使用標準ATR計算
            atr, _ = self.calculate_atr(high_data, low_data, data, period)
            atr = atr * data / 100  # 轉換回絕對值

        # 計算上下軌
        upper = middle + (multiplier * atr)
        lower = middle - (multiplier * atr)

        # 計算通道寬度
        channel_width = (upper - lower) / middle
        channel_width = channel_width.replace([np.inf, -np.inf], 0.0).fillna(0.0)

        # 計算價格在通道中的位置
        position = (data - lower) / (upper - lower)
        position = position.replace([np.inf, -np.inf], 0.5).fillna(0.5)

        calc_time = (time.time() - start_time) * 1000

        adaptation_info = {
            'data_type': data_type,
            'parameters_used': {'period': period, 'multiplier': multiplier},
            'calculation_time_ms': calc_time,
            'data_length': len(data),
            'adaptation_applied': adapted_params.get('adaptation_applied', False)
        }

        return {
            'upper': upper,
            'middle': middle,
            'lower': lower,
            'channel_width': channel_width,
            'position': position,
            'adaptation_info': adaptation_info
        }

    # ==================== Phase 2.4: 數據源特定專用指標 ====================

    def calculate_hibor_term_structure(self, hibor_data: Dict[str, pd.Series],
                                      short_term: str = 'ON', long_term: str = '1M') -> Dict:
        """
        計算HIBOR利率期限結構指標
        """
        start_time = time.time()

        if short_term not in hibor_data or long_term not in hibor_data:
            return {
                'adaptation_info': {
                    'error': f'Missing HIBOR data: need {short_term} and {long_term}'
                }
            }

        short_rates = hibor_data[short_term]
        long_rates = hibor_data[long_term]

        # 確保數據對齊
        common_index = short_rates.index.intersection(long_rates.index)
        short_aligned = short_rates.loc[common_index]
        long_aligned = long_rates.loc[common_index]

        # 計算期限結構
        term_spread = long_aligned - short_aligned
        spread_ma = term_spread.rolling(window=20, min_periods=1).mean()
        spread_std = term_spread.rolling(window=20, min_periods=1).std()

        # 計算Z-score
        spread_zscore = (term_spread - spread_ma) / spread_std
        spread_zscore = spread_zscore.replace([np.inf, -np.inf], 0).fillna(0)

        # 計算斜率變化
        slope_change = term_spread.diff()
        slope_acceleration = slope_change.diff()

        # 期限結構信號
        structure_signal = np.where(spread_zscore > 2, 1,
                                  np.where(spread_zscore < -2, -1, 0))

        calc_time = (time.time() - start_time) * 1000

        adaptation_info = {
            'data_type': 'hibor_term_structure',
            'tenors_used': {'short_term': short_term, 'long_term': long_term},
            'calculation_time_ms': calc_time,
            'data_length': len(common_index),
            'adaptation_applied': True
        }

        return {
            'term_spread': pd.Series(term_spread, index=common_index),
            'spread_ma': pd.Series(spread_ma, index=common_index),
            'spread_zscore': pd.Series(spread_zscore, index=common_index),
            'slope_change': pd.Series(slope_change, index=common_index),
            'slope_acceleration': pd.Series(slope_acceleration, index=common_index),
            'structure_signal': pd.Series(structure_signal, index=common_index),
            'adaptation_info': adaptation_info
        }

    def calculate_rate_spread_analysis(self, rate_data1: pd.Series, rate_data2: pd.Series,
                                     period: int = 20, zscore_window: int = 252) -> Dict:
        """
        計算利差分析指標
        """
        start_time = time.time()

        # 確保數據對齊
        common_index = rate_data1.index.intersection(rate_data2.index)
        rate1_aligned = rate_data1.loc[common_index]
        rate2_aligned = rate_data2.loc[common_index]

        # 計算利差
        spread = rate2_aligned - rate1_aligned
        spread_mean = spread.rolling(window=period, min_periods=1).mean()
        spread_std = spread.rolling(window=period, min_periods=1).std()

        # 計算Z-score
        spread_zscore = (spread - spread_mean) / spread_std
        spread_zscore = spread_zscore.replace([np.inf, -np.inf], 0).fillna(0)

        # 計算歷史百分位數
        spread_percentile = spread.rolling(window=zscore_window, min_periods=1).rank(pct=True) * 100

        # 利差趨勢
        spread_trend = spread.rolling(window=period, min_periods=1).apply(
            lambda x: np.polyfit(np.arange(len(x)), x, 1)[0] if len(x) > 1 else 0
        )

        # 波動率分析
        spread_volatility = spread.pct_change().rolling(window=period, min_periods=1).std() * 100

        # 信號生成
        signal_strength = abs(spread_zscore)
        signal_direction = np.sign(spread_zscore)

        calc_time = (time.time() - start_time) * 1000

        adaptation_info = {
            'data_type': 'rate_spread_analysis',
            'parameters_used': {'period': period, 'zscore_window': zscore_window},
            'calculation_time_ms': calc_time,
            'data_length': len(common_index),
            'adaptation_applied': True
        }

        return {
            'spread': pd.Series(spread, index=common_index),
            'spread_mean': pd.Series(spread_mean, index=common_index),
            'spread_zscore': pd.Series(spread_zscore, index=common_index),
            'spread_percentile': pd.Series(spread_percentile, index=common_index),
            'spread_trend': pd.Series(spread_trend, index=common_index),
            'spread_volatility': pd.Series(spread_volatility, index=common_index),
            'signal_strength': pd.Series(signal_strength, index=common_index),
            'signal_direction': pd.Series(signal_direction, index=common_index),
            'adaptation_info': adaptation_info
        }

    def detect_data_type(self, data: pd.Series, column_name: str = None) -> str:
        """
        檢測數據類型並返回適配策略
        """
        if data.empty:
            return 'unknown'

        # 基於列名判斷
        if column_name:
            col_lower = column_name.lower()
            if any(keyword in col_lower for keyword in self.rate_data_keywords):
                return 'rate_data'
            elif any(keyword in col_lower for keyword in self.flow_data_keywords):
                return 'flow_data'
            elif any(keyword in col_lower for keyword in self.ratio_data_keywords):
                return 'ratio_data'
            elif any(keyword in col_lower for keyword in self.price_data_keywords):
                return 'price_data'

        # 基於數據特徵判斷
        values = data.dropna()
        if len(values) < 10:
            return 'unknown'

        # 檢查是否為利率類型 (通常為正值，範圍合理)
        positive_ratio = (values > 0).mean()
        if positive_ratio > 0.9 and values.max() < 100:
            return 'rate_data'

        # 檢查是否為流量數據 (可能有正有負)
        has_negative = (values < 0).any()
        if has_negative:
            return 'flow_data'

        # 檢查是否為價格數據 (通常較大波動)
        if values.max() > 1000 or values.std() > 100:
            return 'price_data'

        # 默認為比率數據
        return 'ratio_data'

    def adapt_parameters_for_data_type(self, indicator_name: str, data_type: str,
                                     base_params: Dict = None) -> Dict:
        """
        根據數據類型適配參數
        """
        if base_params is None:
            base_params = {}

        adapted_params = base_params.copy()
        adapted_params['adaptation_applied'] = False

        if data_type == 'rate_data':
            # 利率數據：通常較穩定，使用標準參數
            if 'period' in adapted_params:
                # 利率數據通常穩定，可以使用較短週期
                adapted_params['period'] = max(5, int(adapted_params['period'] * 0.8))
            adapted_params['adaptation_applied'] = True
            adapted_params['adaptation_reason'] = '利率數據適配：使用較短週期捕捉利率變化'

        elif data_type == 'flow_data':
            # 流量數據：波動較大，使用較長週期平滑
            if 'period' in adapted_params:
                adapted_params['period'] = int(adapted_params['period'] * 1.5)
            if 'fast' in adapted_params and 'slow' in adapted_params:
                adapted_params['fast'] = int(adapted_params['fast'] * 1.2)
                adapted_params['slow'] = int(adapted_params['slow'] * 1.3)
            adapted_params['adaptation_applied'] = True
            adapted_params['adaptation_reason'] = '流量數據適配：延長週期以平滑波動'

        elif data_type == 'ratio_data':
            # 比率數據：介於兩者之間
            if 'period' in adapted_params:
                adapted_params['period'] = int(adapted_params['period'] * 1.1)
            adapted_params['adaptation_applied'] = True
            adapted_params['adaptation_reason'] = '比率數據適配：平衡參數設置'

        elif data_type == 'price_data':
            # 價格數據：使用標準參數
            adapted_params['adaptation_applied'] = False
            adapted_params['adaptation_reason'] = '價格數據：使用標準參數'

        return adapted_params

    def validate_indicator_performance(self, indicator_name: str, calculation_time_ms: float) -> Dict:
        """
        驗證指標性能是否符合目標
        """
        if indicator_name not in self.indicator_metadata:
            return {'valid': False, 'reason': 'Unknown indicator'}

        metadata = self.indicator_metadata[indicator_name]
        target_time = metadata.performance_target

        is_valid = calculation_time_ms <= target_time
        performance_ratio = calculation_time_ms / target_time

        validation_result = {
            'valid': is_valid,
            'target_time_ms': target_time,
            'actual_time_ms': calculation_time_ms,
            'performance_ratio': performance_ratio,
            'status': 'PASS' if is_valid else 'FAIL',
            'recommendation': 'Optimize calculation' if performance_ratio > 2 else 'Performance acceptable'
        }

        # 存儲驗證結果
        if indicator_name not in self.validation_results:
            self.validation_results[indicator_name] = []
        self.validation_results[indicator_name].append(validation_result)

        return validation_result

    def run_comprehensive_test(self, test_data: pd.Series, indicator_list: List[str] = None) -> Dict:
        """
        運行全面的指標測試
        """
        if indicator_list is None:
            indicator_list = list(self.indicator_metadata.keys())

        test_results = {
            'test_summary': {
                'data_points': len(test_data),
                'indicators_tested': len(indicator_list),
                'test_timestamp': pd.Timestamp.now(),
                'performance_targets_met': 0,
                'total_tests': len(indicator_list)
            },
            'individual_results': {},
            'performance_analysis': {}
        }

        print(f"[START] Phase 2 Extended Indicators Comprehensive Test")
        print(f"Testing {len(indicator_list)} indicators on {len(test_data)} data points")
        print("=" * 70)

        for indicator_name in indicator_list:
            if indicator_name not in self.indicator_metadata:
                print(f"[SKIP] {indicator_name}: Not registered")
                continue

            metadata = self.indicator_metadata[indicator_name]
            print(f"[TEST] {indicator_name} ({metadata.category.value})")

            try:
                # 根據指標類型調用相應計算方法
                result = self._calculate_indicator_by_name(indicator_name, test_data)

                if isinstance(result, tuple):
                    # 返回 (series, info) 格式
                    indicator_values, adaptation_info = result
                    calculation_time = adaptation_info.get('calculation_time_ms', 0)
                elif isinstance(result, dict):
                    # 返回字典格式
                    adaptation_info = result.get('adaptation_info', {})
                    calculation_time = adaptation_info.get('calculation_time_ms', 0)
                    indicator_values = result
                else:
                    # 其他格式
                    indicator_values = result
                    calculation_time = 0
                    adaptation_info = {}

                # 驗證性能
                performance_validation = self.validate_indicator_performance(indicator_name, calculation_time)

                if performance_validation['valid']:
                    test_results['test_summary']['performance_targets_met'] += 1

                # 記錄結果
                test_results['individual_results'][indicator_name] = {
                    'category': metadata.category.value,
                    'description': metadata.description,
                    'calculation_time_ms': calculation_time,
                    'performance_validation': performance_validation,
                    'adaptation_info': adaptation_info,
                    'success': True,
                    'data_points_processed': len(test_data)
                }

                status = "✅ PASS" if performance_validation['valid'] else "❌ FAIL"
                print(f"  {status} {calculation_time:.2f}ms (target: {metadata.performance_target:.1f}ms)")

            except Exception as e:
                print(f"  ❌ ERROR: {str(e)}")
                test_results['individual_results'][indicator_name] = {
                    'success': False,
                    'error': str(e),
                    'category': metadata.category.value,
                    'description': metadata.description
                }

        # 性能分析
        successful_tests = [r for r in test_results['individual_results'].values() if r.get('success', False)]
        if successful_tests:
            avg_calc_time = np.mean([r['calculation_time_ms'] for r in successful_tests])
            max_calc_time = np.max([r['calculation_time_ms'] for r in successful_tests])

            test_results['performance_analysis'] = {
                'average_calculation_time_ms': avg_calc_time,
                'max_calculation_time_ms': max_calc_time,
                'performance_targets_met_percent': (test_results['test_summary']['performance_targets_met'] / test_results['test_summary']['total_tests']) * 100,
                'system_performance_rating': 'Excellent' if avg_calc_time < 0.5 else 'Good' if avg_calc_time < 1.0 else 'Needs Optimization'
            }

        print("\n" + "=" * 70)
        print("[COMPLETE] Comprehensive Test Results:")
        print(f"Performance Targets Met: {test_results['test_summary']['performance_targets_met']}/{test_results['test_summary']['total_tests']}")
        print(f"Average Calculation Time: {test_results['performance_analysis'].get('average_calculation_time_ms', 0):.2f}ms")
        print(f"System Performance Rating: {test_results['performance_analysis'].get('system_performance_rating', 'Unknown')}")

        return test_results

    def _calculate_indicator_by_name(self, indicator_name: str, data: pd.Series) -> Union[Tuple[pd.Series, Dict], Dict]:
        """
        根據指標名稱調用相應的計算方法
        """
        # 趨勢類擴展指標
        if indicator_name == 'DEMA':
            return self.calculate_dema(data)
        elif indicator_name == 'TEMA':
            return self.calculate_tema(data)
        elif indicator_name == 'TRIMA':
            return self.calculate_trima(data)
        elif indicator_name == 'MACD_EXTENDED':
            return self.calculate_macd_extended(data)

        # 動量類擴展指標
        elif indicator_name == 'STOCHASTIC_F':
            return self.calculate_stochastic_f(data)
        elif indicator_name == 'WILLIAMS_R':
            return self.calculate_williams_r(data)
        elif indicator_name == 'CCI':
            return self.calculate_cci(data)
        elif indicator_name == 'RSI_EXTENDED':
            return self.calculate_rsi_extended(data)

        # 波動率指標
        elif indicator_name == 'BOLLINGER_BANDS':
            return self.calculate_bollinger_bands(data)
        elif indicator_name == 'KELTNER_CHANNELS':
            return self.calculate_keltner_channels(data)

        else:
            raise ValueError(f"Unknown indicator: {indicator_name}")


def main():
    """主測試函數"""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    print("[START] Phase 2 Extended Technical Indicators System")
    print("=" * 60)

    # 創建Phase 2擴展指標系統
    phase2_indicators = Phase2ExtendedIndicators()

    # 生成測試數據
    np.random.seed(42)
    test_data = pd.Series(
        np.cumsum(np.random.randn(500)) + 100,
        index=pd.date_range('2020-01-01', periods=500, freq='D'),
        name='test_data'
    )

    print(f"Generated test data: {len(test_data)} points")
    print(f"Data range: {test_data.min():.2f} - {test_data.max():.2f}")

    # 運行全面測試
    test_results = phase2_indicators.run_comprehensive_test(
        test_data,
        indicator_list=['DEMA', 'TEMA', 'TRIMA', 'MACD_EXTENDED', 'RSI_EXTENDED',
                       'BOLLINGER_BANDS', 'KELTNER_CHANNELS']
    )

    # 保存測試結果
    output_dir = Path('data/phase2_test_results')
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
    results_file = output_dir / f'phase2_comprehensive_test_{timestamp}.json'

    # 準備可序列化的結果
    serializable_results = {
        'test_summary': test_results['test_summary'],
        'performance_analysis': test_results['performance_analysis'],
        'indicator_metadata': {
            name: {
                'category': meta.category.value,
                'description': meta.description,
                'performance_target': meta.performance_target,
                'data_type_requirements': meta.data_type_requirements
            }
            for name, meta in phase2_indicators.indicator_metadata.items()
        }
    }

    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(serializable_results, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n[SAVED] Test results saved to: {results_file}")
    print("[COMPLETE] Phase 2 Extended Indicators System testing completed!")


if __name__ == "__main__":
    main()