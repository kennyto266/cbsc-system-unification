#!/usr/bin/env python3
"""
技術指標處理管道 - 實現標準化的技術指標計算和驗證
Technical Indicator Processing Pipeline - Standardized calculation and validation
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import asyncio
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing as mp

from ..shared.indicators.non_price_ta_id_system import NonPriceTACalculator, TAIndicatorID

logger = logging.getLogger(__name__)


@dataclass
class IndicatorConfig:
    """技術指標配置"""
    indicator_type: str  # 'RSI', 'MACD', 'SMA', etc.
    parameters: Dict[str, Any] = field(default_factory=dict)
    data_source: str = 'price'  # 'price', 'hibor', 'gdp', 'trade'
    quality_threshold: float = 0.8  # 數據質量閾值
    validation_enabled: bool = True


@dataclass
class IndicatorResult:
    """技術指標計算結果"""
    indicator_id: str
    values: pd.Series
    quality_score: float
    data_points: int
    calculation_time: float
    is_valid: bool
    metadata: Dict[str, Any] = field(default_factory=dict)


class DataQualityValidator:
    """數據質量驗證器"""
    
    def __init__(self):
        self.quality_metrics = {}
    
    def validate_time_series(self, data: pd.Series, data_type: str = 'price') -> Dict[str, Any]:
        """驗證時間序列數據質量"""
        if data.empty:
            return {'valid': False, 'reason': 'Empty data', 'quality_score': 0.0}
        
        quality_score = 1.0
        issues = []
        
        # 檢查缺失值
        missing_ratio = data.isna().sum() / len(data)
        if missing_ratio > 0.1:
            quality_score -= missing_ratio * 0.5
            issues.append(f"High missing ratio: {missing_ratio:.2%}")
        
        # 檢查異常值 (基於IQR方法)
        if data_type in ['price', 'close', 'volume']:
            Q1 = data.quantile(0.25)
            Q3 = data.quantile(0.75)
            IQR = Q3 - Q1
            outliers = ((data < (Q1 - 1.5 * IQR)) | (data > (Q3 + 1.5 * IQR))).sum()
            outlier_ratio = outliers / len(data)
            if outlier_ratio > 0.05:
                quality_score -= outlier_ratio * 0.3
                issues.append(f"High outlier ratio: {outlier_ratio:.2%}")
        
        # 檢查數據頻率一致性
        if len(data) > 1:
            time_diffs = data.index.to_series().diff().dt.days.dropna()
            if not time_diffs.empty:
                freq_std = time_diffs.std()
                if freq_std > 1.0:  # 超過1天的標準差
                    quality_score -= min(freq_std * 0.1, 0.2)
                    issues.append(f"Inconsistent frequency: std={freq_std:.1f} days")
        
        # 檢查數據範圍合理性
        if data_type == 'price':
            if (data <= 0).any():
                quality_score -= 0.5
                issues.append("Negative or zero prices found")
        elif data_type == 'volume':
            if (data < 0).any():
                quality_score -= 0.5
                issues.append("Negative volume found")
        
        return {
            'valid': quality_score >= 0.7,
            'quality_score': max(0.0, quality_score),
            'issues': issues,
            'missing_ratio': missing_ratio,
            'data_points': len(data),
            'date_range': [data.index.min().isoformat(), data.index.max().isoformat()] if not data.empty else None
        }
    
    def validate_cross_source_consistency(self, price_data: pd.DataFrame, 
                                        economic_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """驗證跨數據源一致性"""
        consistency_results = {}
        
        if price_data.empty:
            return {'overall_consistency': 0.0, 'details': 'No price data'}
        
        price_dates = set(price_data.index)
        overall_score = 1.0
        
        for source_name, econ_df in economic_data.items():
            if econ_df.empty:
                consistency_results[source_name] = {
                    'consistency_score': 0.0,
                    'overlap_ratio': 0.0,
                    'issue': 'Empty data'
                }
                overall_score -= 0.2
                continue
            
            econ_dates = set(econ_df.index)
            overlap = price_dates.intersection(econ_dates)
            overlap_ratio = len(overlap) / len(price_dates) if price_dates else 0
            
            # 檢查時間對齊質量
            if overlap_ratio < 0.8:
                overall_score -= 0.3
            
            consistency_results[source_name] = {
                'consistency_score': overlap_ratio,
                'overlap_ratio': overlap_ratio,
                'overlap_days': len(overlap),
                'price_data_points': len(price_dates),
                'economic_data_points': len(econ_dates)
            }
        
        return {
            'overall_consistency': max(0.0, overall_score),
            'details': consistency_results
        }


class StandardizedTechnicalIndicatorPipeline:
    """標準化技術指標處理管道"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.quality_validator = DataQualityValidator()
        self.ta_calculator = NonPriceTACalculator()
        self.indicator_cache = {}
        self.performance_metrics = {
            'total_calculations': 0,
            'average_calculation_time': 0.0,
            'cache_hits': 0,
            'quality_failures': 0
        }
        
        # 支持的技術指標配置
        self.supported_indicators = {
            'RSI': {
                'class': 'RSI',
                'required_params': ['window'],
                'default_params': {'window': 14},
                'data_types': ['price', 'hibor', 'gdp', 'trade']
            },
            'MACD': {
                'class': 'MACD',
                'required_params': ['fast', 'slow', 'signal'],
                'default_params': {'fast': 12, 'slow': 26, 'signal': 9},
                'data_types': ['price', 'hibor']
            },
            'SMA': {
                'class': 'SMA',
                'required_params': ['window'],
                'default_params': {'window': 20},
                'data_types': ['price', 'hibor', 'gdp', 'trade']
            },
            'EMA': {
                'class': 'EMA',
                'required_params': ['window'],
                'default_params': {'window': 20},
                'data_types': ['price', 'hibor']
            },
            'BOLLINGER': {
                'class': 'BollingerBands',
                'required_params': ['window', 'std_dev'],
                'default_params': {'window': 20, 'std_dev': 2.0},
                'data_types': ['price']
            },
            'STOCHASTIC': {
                'class': 'Stochastic',
                'required_params': ['k_window', 'd_window'],
                'default_params': {'k_window': 14, 'd_window': 3},
                'data_types': ['price']
            }
        }
    
    def create_indicator_config(self, indicator_type: str, parameters: Dict[str, Any] = None,
                              data_source: str = 'price', quality_threshold: float = 0.8) -> IndicatorConfig:
        """創建技術指標配置"""
        if indicator_type not in self.supported_indicators:
            raise ValueError(f"Unsupported indicator type: {indicator_type}")
        
        indicator_spec = self.supported_indicators[indicator_type]
        
        # 使用默認參數填充
        final_params = indicator_spec['default_params'].copy()
        if parameters:
            final_params.update(parameters)
        
        # 驗證必需參數
        missing_params = [p for p in indicator_spec['required_params'] if p not in final_params]
        if missing_params:
            raise ValueError(f"Missing required parameters for {indicator_type}: {missing_params}")
        
        return IndicatorConfig(
            indicator_type=indicator_type,
            parameters=final_params,
            data_source=data_source,
            quality_threshold=quality_threshold
        )
    
    async def calculate_indicator(self, config: IndicatorConfig, 
                                data: pd.Series) -> IndicatorResult:
        """計算單個技術指標"""
        start_time = datetime.now()
        
        # 數據質量驗證
        quality_result = self.quality_validator.validate_time_series(data, config.data_source)
        
        if quality_result['quality_score'] < config.quality_threshold:
            logger.warning(f"Data quality too low for {config.indicator_type}: {quality_result['quality_score']:.2f}")
            self.performance_metrics['quality_failures'] += 1
            
            return IndicatorResult(
                indicator_id=f"{config.data_source}_{config.indicator_type}_{config.parameters.get('window', 'default')}_v1",
                values=pd.Series(dtype=float),
                quality_score=quality_result['quality_score'],
                data_points=0,
                calculation_time=0.0,
                is_valid=False,
                metadata={'quality_issues': quality_result['issues']}
            )
        
        # 檢查緩存
        cache_key = f"{config.data_source}_{config.indicator_type}_{hash(frozenset(config.parameters.items()))}_{hash(data.values.tobytes())}"
        if cache_key in self.indicator_cache:
            self.performance_metrics['cache_hits'] += 1
            cached_result = self.indicator_cache[cache_key]
            return cached_result
        
        try:
            # 根據指標類型計算
            if config.indicator_type == 'RSI':
                result_values = self._calculate_rsi(data, config.parameters['window'])
            elif config.indicator_type == 'MACD':
                result_values = self._calculate_macd(data, config.parameters)
            elif config.indicator_type == 'SMA':
                result_values = self._calculate_sma(data, config.parameters['window'])
            elif config.indicator_type == 'EMA':
                result_values = self._calculate_ema(data, config.parameters['window'])
            elif config.indicator_type == 'BOLLINGER':
                result_values = self._calculate_bollinger(data, config.parameters)
            elif config.indicator_type == 'STOCHASTIC':
                result_values = self._calculate_stochastic(data, config.parameters)
            else:
                # 嘗試使用非價格TA計算器
                result_values = self._calculate_non_price_indicator(config, data)
            
            calculation_time = (datetime.now() - start_time).total_seconds()
            
            # 創建結果
            indicator_result = IndicatorResult(
                indicator_id=f"{config.data_source}_{config.indicator_type}_{config.parameters.get('window', 'default')}_v1",
                values=result_values,
                quality_score=quality_result['quality_score'],
                data_points=len(result_values),
                calculation_time=calculation_time,
                is_valid=True,
                metadata={
                    'parameters': config.parameters,
                    'data_source': config.data_source,
                    'quality_details': quality_result
                }
            )
            
            # 緩存結果
            self.indicator_cache[cache_key] = indicator_result
            
            # 更新性能指標
            self.performance_metrics['total_calculations'] += 1
            self.performance_metrics['average_calculation_time'] = (
                (self.performance_metrics['average_calculation_time'] * (self.performance_metrics['total_calculations'] - 1) + calculation_time) /
                self.performance_metrics['total_calculations']
            )
            
            return indicator_result
            
        except Exception as e:
            logger.error(f"Error calculating {config.indicator_type}: {e}")
            return IndicatorResult(
                indicator_id=f"{config.data_source}_{config.indicator_type}_error_v1",
                values=pd.Series(dtype=float),
                quality_score=0.0,
                data_points=0,
                calculation_time=(datetime.now() - start_time).total_seconds(),
                is_valid=False,
                metadata={'error': str(e)}
            )
    
    def _calculate_rsi(self, data: pd.Series, window: int) -> pd.Series:
        """計算RSI指標"""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_macd(self, data: pd.Series, params: Dict[str, int]) -> pd.Series:
        """計算MACD指標（返回MACD線）"""
        ema_fast = data.ewm(span=params['fast']).mean()
        ema_slow = data.ewm(span=params['slow']).mean()
        macd_line = ema_fast - ema_slow
        return macd_line
    
    def _calculate_sma(self, data: pd.Series, window: int) -> pd.Series:
        """計算SMA指標"""
        return data.rolling(window=window).mean()
    
    def _calculate_ema(self, data: pd.Series, window: int) -> pd.Series:
        """計算EMA指標"""
        return data.ewm(span=window).mean()
    
    def _calculate_bollinger(self, data: pd.Series, params: Dict[str, Any]) -> pd.Series:
        """計算布林帶指標（返回上軌）"""
        sma = data.rolling(window=params['window']).mean()
        std = data.rolling(window=params['window']).std()
        upper_band = sma + (std * params['std_dev'])
        return upper_band
    
    def _calculate_stochastic(self, data: pd.Series, params: Dict[str, int]) -> pd.Series:
        """計算隨機指標（返回%K）"""
        # 需要高低收數據，這裡簡化處理
        low_min = data.rolling(window=params['k_window']).min()
        high_max = data.rolling(window=params['k_window']).max()
        k_percent = 100 * ((data - low_min) / (high_max - low_min))
        return k_percent
    
    def _calculate_non_price_indicator(self, config: IndicatorConfig, data: pd.Series) -> pd.Series:
        """使用非價格TA計算器計算指標"""
        try:
            # 轉換為非價格TA計算器格式
            df_data = pd.DataFrame({'value': data})
            
            # 生成指標ID
            indicator_id = f"{config.data_source.upper()}_{config.indicator_type}_{list(config.parameters.values())[0]}_v1"
            
            # 調用非價格計算器
            result = self.ta_calculator.calculate_non_price_ta(indicator_id, df_data)
            
            if isinstance(result, dict) and 'values' in result:
                return pd.Series(result['values'], index=data.index)
            elif isinstance(result, pd.Series):
                return result
            else:
                return pd.Series([np.nan] * len(data), index=data.index)
                
        except Exception as e:
            logger.warning(f"Non-price TA calculator failed for {config.indicator_type}: {e}")
            return pd.Series([np.nan] * len(data), index=data.index)
    
    async def calculate_multiple_indicators(self, 
                                         configs: List[IndicatorConfig], 
                                         data_dict: Dict[str, pd.Series]) -> Dict[str, IndicatorResult]:
        """並行計算多個技術指標"""
        tasks = []
        
        for config in configs:
            data = data_dict.get(config.data_source)
            if data is None or data.empty:
                logger.warning(f"No data available for source: {config.data_source}")
                continue
            
            task = self.calculate_indicator(config, data)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 組織結果
        indicator_results = {}
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Indicator calculation failed: {result}")
                continue
            
            if i < len(configs):
                config = configs[i]
                indicator_results[config.indicator_type] = result
        
        return indicator_results
    
    def batch_calculate_with_multiprocessing(self, 
                                           configs: List[IndicatorConfig],
                                           data_dict: Dict[str, pd.Series],
                                           num_processes: int = None) -> Dict[str, IndicatorResult]:
        """使用多進程批量計算技術指標"""
        if num_processes is None:
            num_processes = mp.cpu_count() - 1
        
        # 準備任務數據
        tasks = []
        for config in configs:
            data = data_dict.get(config.data_source)
            if data is None or data.empty:
                continue
            tasks.append((config, data))
        
        if not tasks:
            return {}
        
        # 多進程計算
        results = {}
        with ProcessPoolExecutor(max_workers=num_processes) as executor:
            # 提交任務
            future_to_config = {
                executor.submit(self._calculate_indicator_sync, config, data): config
                for config, data in tasks
            }
            
            # 收集結果
            for future in as_completed(future_to_config):
                config = future_to_config[future]
                try:
                    result = future.result()
                    results[f"{config.data_source}_{config.indicator_type}"] = result
                except Exception as e:
                    logger.error(f"Multiprocessing calculation failed for {config.indicator_type}: {e}")
        
        return results
    
    def _calculate_indicator_sync(self, config: IndicatorConfig, data: pd.Series) -> IndicatorResult:
        """同步版本的技術指標計算（用於多進程）"""
        # 簡化版本的同步計算
        try:
            if config.indicator_type == 'RSI':
                values = self._calculate_rsi(data, config.parameters['window'])
            elif config.indicator_type == 'SMA':
                values = self._calculate_sma(data, config.parameters['window'])
            else:
                values = pd.Series([np.nan] * len(data), index=data.index)
            
            return IndicatorResult(
                indicator_id=f"{config.data_source}_{config.indicator_type}_v1",
                values=values,
                quality_score=0.8,  # 簡化質量評分
                data_points=len(values),
                calculation_time=0.1,
                is_valid=True
            )
        except Exception as e:
            return IndicatorResult(
                indicator_id=f"{config.data_source}_{config.indicator_type}_error_v1",
                values=pd.Series(dtype=float),
                quality_score=0.0,
                data_points=0,
                calculation_time=0.0,
                is_valid=False,
                metadata={'error': str(e)}
            )
    
    def generate_quality_report(self) -> Dict[str, Any]:
        """生成數據質量和性能報告"""
        return {
            'performance_metrics': self.performance_metrics,
            'cache_efficiency': self.performance_metrics['cache_hits'] / max(1, self.performance_metrics['total_calculations']),
            'average_quality': 1.0 - (self.performance_metrics['quality_failures'] / max(1, self.performance_metrics['total_calculations'])),
            'supported_indicators': list(self.supported_indicators.keys()),
            'cache_size': len(self.indicator_cache)
        }
    
    def clear_cache(self):
        """清除緩存"""
        self.indicator_cache.clear()
        logger.info("Technical indicator cache cleared")