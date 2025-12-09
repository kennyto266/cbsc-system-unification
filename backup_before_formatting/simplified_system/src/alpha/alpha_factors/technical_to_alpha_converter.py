#!/usr/bin/env python3
"""
Technical to Alpha Factor Converter
技術指標到Alpha因子轉換器

將現有的477種技術指標轉換為標準化的Alpha因子
支持來自CoreIndicators系統的所有技術指標
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
import logging
from dataclasses import dataclass
from abc import ABC, abstractmethod
import warnings

# 嘗試導入現有技術指標系統
try:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'indicators'))
    from core_indicators import CoreIndicators
    TECHNICAL_INDICATORS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Could not import technical indicators: {e}")
    TECHNICAL_INDICATORS_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class FactorMapping:
    """因子映射配置"""
    indicator_name: str
    factor_type: str
    factor_name: str
    description: str
    transformation_method: str  # 'direct', 'normalized', 'zscore', 'rank'
    parameters: Dict[str, Any] = None

class TechnicalIndicatorConverter:
    """
    技術指標到Alpha因子轉換器

    將477種技術指標轉換為標準化的Alpha因子，支持多種轉換方法。
    """

    def __init__(self):
        """初始化轉換器"""
        if TECHNICAL_INDICATORS_AVAILABLE:
            self.core_indicators = CoreIndicators()
            logger.info("Technical indicators integration loaded")
        else:
            self.core_indicators = None
            logger.warning("Technical indicators integration not available")

        # 預定義因子映射
        self.factor_mappings = self._initialize_factor_mappings()

    def _initialize_factor_mappings(self) -> Dict[str, List[FactorMapping]]:
        """初始化因子映射配置"""
        mappings = {
            'momentum': [
                FactorMapping('RSI', 'momentum', 'rsi_momentum', 'RSI-based momentum factor', 'normalized'),
                FactorMapping('MACD', 'momentum', 'macd_signal', 'MACD signal factor', 'direct'),
                FactorMapping('CCI', 'momentum', 'cci_momentum', 'CCI momentum factor', 'zscore'),
                FactorMapping('Stochastic', 'momentum', 'stoch_momentum', 'Stochastic momentum factor', 'normalized'),
                FactorMapping('Williams_R', 'momentum', 'williams_r_momentum', 'Williams %R momentum factor', 'direct'),
            ],
            'reversal': [
                FactorMapping('RSI', 'reversal', 'rsi_reversal', 'RSI reversal factor', 'inverse'),
                FactorMapping('Stochastic', 'reversal', 'stoch_reversal', 'Stochastic reversal factor', 'inverse'),
                FactorMapping('Williams_R', 'reversal', 'williams_r_reversal', 'Williams %R reversal factor', 'direct'),
            ],
            'volatility': [
                FactorMapping('ATR', 'volatility', 'atr_volatility', 'ATR-based volatility factor', 'normalized'),
                FactorMapping('Bollinger_Width', 'volatility', 'bb_width', 'Bollinger Band width factor', 'zscore'),
                FactorMapping('Standard_Deviation', 'volatility', 'std_dev', 'Standard deviation factor', 'normalized'),
            ],
            'volume': [
                FactorMapping('Volume_SMA', 'volume', 'volume_sma_ratio', 'Volume SMA ratio factor', 'normalized'),
                FactorMapping('On_Balance_Volume', 'volume', 'obv_trend', 'OBV trend factor', 'zscore'),
                FactorMapping('Money_Flow_Index', 'volume', 'mfi_signal', 'Money Flow Index factor', 'normalized'),
            ],
            'trend': [
                FactorMapping('ADX', 'trend', 'adx_trend', 'ADX trend strength factor', 'normalized'),
                FactorMapping('Aroon', 'trend', 'aroon_trend', 'Aroon trend factor', 'normalized'),
                FactorMapping('DMI', 'trend', 'dmi_trend', 'DMI trend factor', 'zscore'),
            ],
            'quality': [
                FactorMapping('Chaikin_Money_Flow', 'quality', 'cmf_quality', 'Chaikin Money Flow quality factor', 'normalized'),
                FactorMapping('Force_Index', 'quality', 'force_quality', 'Force Index quality factor', 'zscore'),
            ]
        }
        return mappings

    def convert_technical_to_alpha(self,
                                  data: pd.DataFrame,
                                  indicator_names: List[str] = None,
                                  lookback_periods: List[int] = None) -> pd.DataFrame:
        """
        將技術指標轉換為Alpha因子

        Args:
            data: 市場數據，必須包含OHLCV列
            indicator_names: 要轉換的技術指標名稱列表
            lookback_periods: 回看期數列表

        Returns:
            pd.DataFrame: Alpha因子數據
        """
        if not TECHNICAL_INDICATORS_AVAILABLE:
            raise RuntimeError("Technical indicators system not available")

        if indicator_names is None:
            # 使用所有可用的技術指標類別
            indicator_names = ['RSI', 'MACD', 'Bollinger', 'ATR', 'ADX', 'Stochastic', 'Williams_R', 'CCI']

        if lookback_periods is None:
            lookback_periods = [5, 10, 14, 20, 30, 60]

        alpha_factors = pd.DataFrame(index=data.index)

        for indicator_name in indicator_names:
            try:
                # 計算技術指標
                indicator_data = self._calculate_technical_indicator(data, indicator_name, lookback_periods)

                # 轉換為Alpha因子
                for period in lookback_periods:
                    if period in indicator_data:
                        factor_data = indicator_data[period]

                        # 應用轉換方法
                        for mapping in self._get_mappings_for_indicator(indicator_name):
                            factor_name = f"{mapping.factor_name}_{period}"

                            if mapping.transformation_method == 'direct':
                                alpha_factors[factor_name] = factor_data

                            elif mapping.transformation_method == 'normalized':
                                alpha_factors[factor_name] = self._normalize_factor(factor_data)

                            elif mapping.transformation_method == 'zscore':
                                alpha_factors[factor_name] = self._zscore_factor(factor_data)

                            elif mapping.transformation_method == 'inverse':
                                alpha_factors[factor_name] = -factor_data

                            elif mapping.transformation_method == 'rank':
                                alpha_factors[factor_name] = factor_data.rank(pct=True)

            except Exception as e:
                logger.warning(f"Failed to convert {indicator_name} to alpha factor: {e}")
                continue

        logger.info(f"Converted {len(alpha_factors.columns)} technical indicators to alpha factors")
        return alpha_factors

    def _calculate_technical_indicator(self,
                                     data: pd.DataFrame,
                                     indicator_name: str,
                                     lookback_periods: List[int]) -> Dict[int, pd.Series]:
        """
        計算技術指標數據

        Args:
            data: 市場數據
            indicator_name: 技術指標名稱
            lookback_periods: 回看期數列表

        Returns:
            Dict[int, pd.Series]: 按期數分組的技術指標數據
        """
        indicator_data = {}

        for period in lookback_periods:
            try:
                if indicator_name == 'RSI':
                    indicator_data[period] = self.core_indicators.calculate_rsi(data['Close'], period)

                elif indicator_name == 'MACD':
                    # MACD使用固定參數，但可以根據期數調整
                    fast = min(period, 12)
                    slow = max(period, 26)
                    signal = min(period // 3, 9)
                    macd_line, signal_line, histogram = self.core_indicators.calculate_macd(
                        data['Close'], fast, slow, signal
                    )
                    indicator_data[period] = macd_line

                elif indicator_name == 'Bollinger':
                    upper, middle, lower = self.core_indicators.calculate_bollinger_bands(
                        data['Close'], period, 2
                    )
                    # 布林帶位置因子
                    indicator_data[period] = (data['Close'] - lower) / (upper - lower)

                elif indicator_name == 'ATR':
                    indicator_data[period] = self.core_indicators.calculate_atr(data, period)

                elif indicator_name == 'ADX':
                    indicator_data[period] = self.core_indicators.calculate_adx(data, period)

                elif indicator_name == 'Stochastic':
                    k_percent, d_percent = self.core_indicators.calculate_stochastic(data, period, 3)
                    indicator_data[period] = k_percent

                elif indicator_name == 'Williams_R':
                    indicator_data[period] = self.core_indicators.calculate_williams_r(data, period)

                elif indicator_name == 'CCI':
                    indicator_data[period] = self.core_indicators.calculate_cci(data, period)

                elif indicator_name == 'Standard_Deviation':
                    indicator_data[period] = data['Close'].rolling(window=period).std()

                elif indicator_name == 'Volume_SMA':
                    if 'Volume' in data.columns:
                        indicator_data[period] = data['Volume'] / data['Volume'].rolling(window=period).mean()
                    else:
                        logger.warning(f"Volume data not available for {indicator_name}")

                elif indicator_name == 'On_Balance_Volume':
                    if 'Volume' in data.columns:
                        obv = self.core_indicators.calculate_obv(data)
                        indicator_data[period] = obv.rolling(window=period).mean()
                    else:
                        logger.warning(f"Volume data not available for {indicator_name}")

                elif indicator_name == 'Money_Flow_Index':
                    indicator_data[period] = self.core_indicators.calculate_mfi(data, period)

                elif indicator_name == 'Bollinger_Width':
                    upper, middle, lower = self.core_indicators.calculate_bollinger_bands(
                        data['Close'], period, 2
                    )
                    indicator_data[period] = (upper - lower) / middle

                elif indicator_name == 'Aroon':
                    aroon_up, aroon_down = self.core_indicators.calculate_aroon(data, period)
                    indicator_data[period] = aroon_up - aroon_down

                elif indicator_name == 'DMI':
                    di_plus, di_minus, adx = self.core_indicators.calculate_dmi(data, period)
                    indicator_data[period] = di_plus - di_minus

                elif indicator_name == 'Chaikin_Money_Flow':
                    indicator_data[period] = self.core_indicators.calculate_cmf(data, period)

                elif indicator_name == 'Force_Index':
                    indicator_data[period] = self.core_indicators.calculate_force_index(data, period)

                else:
                    logger.warning(f"Unknown technical indicator: {indicator_name}")

            except Exception as e:
                logger.warning(f"Failed to calculate {indicator_name} with period {period}: {e}")
                continue

        return indicator_data

    def _get_mappings_for_indicator(self, indicator_name: str) -> List[FactorMapping]:
        """獲取技術指標的因子映射"""
        mappings = []
        for factor_type, type_mappings in self.factor_mappings.items():
            for mapping in type_mappings:
                if mapping.indicator_name == indicator_name:
                    mappings.append(mapping)
        return mappings

    def _normalize_factor(self, factor_data: pd.Series) -> pd.Series:
        """標準化因子值到0-1範圍"""
        min_val = factor_data.min()
        max_val = factor_data.max()

        if max_val != min_val:
            return (factor_data - min_val) / (max_val - min_val)
        else:
            return pd.Series(0.5, index=factor_data.index)

    def _zscore_factor(self, factor_data: pd.Series, window: int = 252) -> pd.Series:
        """計算Z-score標準化的因子值"""
        rolling_mean = factor_data.rolling(window=window).mean()
        rolling_std = factor_data.rolling(window=window).std()

        return (factor_data - rolling_mean) / rolling_std

    def get_available_indicators(self) -> List[str]:
        """獲取可用的技術指標列表"""
        if not TECHNICAL_INDICATORS_AVAILABLE:
            return []

        # 基於現有CoreIndicators系統的可用指標
        available_indicators = [
            'RSI', 'MACD', 'Bollinger', 'ATR', 'ADX', 'Stochastic',
            'Williams_R', 'CCI', 'Standard_Deviation', 'Volume_SMA',
            'On_Balance_Volume', 'Money_Flow_Index', 'Bollinger_Width',
            'Aroon', 'DMI', 'Chaikin_Money_Flow', 'Force_Index'
        ]

        return available_indicators

    def generate_factor_universe(self,
                                data: pd.DataFrame,
                                factor_types: List[str] = None) -> pd.DataFrame:
        """
        生成完整的Alpha因子宇宙

        Args:
            data: 市場數據
            factor_types: 要生成的因子類型列表

        Returns:
            pd.DataFrame: 完整的Alpha因子數據
        """
        if factor_types is None:
            factor_types = list(self.factor_mappings.keys())

        all_factors = pd.DataFrame(index=data.index)

        for factor_type in factor_types:
            if factor_type in self.factor_mappings:
                mappings = self.factor_mappings[factor_type]
                indicator_names = list(set(mapping.indicator_name for mapping in mappings))

                type_factors = self.convert_technical_to_alpha(data, indicator_names)
                all_factors = pd.concat([all_factors, type_factors], axis=1)

        logger.info(f"Generated factor universe with {len(all_factors.columns)} factors")
        return all_factors

class BulkTechnicalConverter:
    """
    批量技術指標轉換器

    專為處理大量技術指標到Alpha因子的轉換而設計
    """

    def __init__(self):
        self.converter = TechnicalIndicatorConverter()

    def convert_all_available_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        轉換所有可用的技術指標為Alpha因子

        Args:
            data: 市場數據

        Returns:
            pd.DataFrame: 所有轉換的Alpha因子
        """
        available_indicators = self.converter.get_available_indicators()

        if not available_indicators:
            logger.warning("No technical indicators available for conversion")
            return pd.DataFrame(index=data.index)

        # 使用較少的期數以提高效率
        lookback_periods = [5, 10, 14, 20, 30, 60]

        logger.info(f"Converting {len(available_indicators)} technical indicators to alpha factors")

        alpha_factors = self.converter.convert_technical_to_alpha(
            data=data,
            indicator_names=available_indicators,
            lookback_periods=lookback_periods
        )

        return alpha_factors

    def create_factor_metadata(self, alpha_factors: pd.DataFrame) -> pd.DataFrame:
        """
        創建因子元數據

        Args:
            alpha_factors: Alpha因子數據

        Returns:
            pd.DataFrame: 因子元數據
        """
        metadata = []

        for factor_name in alpha_factors.columns:
            # 解析因子名稱
            parts = factor_name.split('_')

            if len(parts) >= 2:
                base_indicator = '_'.join(parts[:-1])
                period = parts[-1]
            else:
                base_indicator = factor_name
                period = 'unknown'

            # 確定因子類型
            factor_type = 'unknown'
            for ftype, mappings in self.converter.factor_mappings.items():
                for mapping in mappings:
                    if base_indicator.startswith(mapping.factor_name):
                        factor_type = ftype
                        break
                if factor_type != 'unknown':
                    break

            metadata.append({
                'factor_name': factor_name,
                'base_indicator': base_indicator,
                'factor_type': factor_type,
                'period': period,
                'data_points': len(alpha_factors[factor_name].dropna()),
                'first_valid_date': alpha_factors[factor_name].first_valid_index(),
                'last_valid_date': alpha_factors[factor_name].last_valid_index()
            })

        return pd.DataFrame(metadata)