#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VectorBT Enhanced Technical Indicators
VectorBT增强技术指标 - Phase 4.1

使用VectorBT原生方法实现高性能向量化技术指标计算
High-performance vectorized technical indicators using VectorBT native methods
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Union, Tuple, Any
import logging
from dataclasses import dataclass
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing as mp

try:
    import vectorbt as vbt
    VECTORBT_AVAILABLE = True
except ImportError:
    VECTORBT_AVAILABLE = False
    logging.warning("VectorBT not available - falling back to pandas calculations")

from .core_indicators import CoreIndicators

logger = logging.getLogger(__name__)

@dataclass
class IndicatorPerformance:
    """技术指标性能分析"""
    indicator_name: str
    calculation_time: float
    memory_usage: float
    signal_quality: float  # 信号质量评分
    predictive_power: float  # 预测能力
    stability_score: float  # 稳定性评分

class VectorBTIndicators:
    """
    VectorBT增强技术指标类

    利用VectorBT的原生向量化方法实现:
    - 批量参数计算
    - 交叉指标分析
    - 自适应参数调整
    - 性能归因分析
    """

    def __init__(self, enable_gpu: bool = False):
        """
        初始化VectorBT技术指标

        Args:
            enable_gpu: 是否启用GPU加速
        """
        self.enable_gpu = enable_gpu
        self.core_indicators = CoreIndicators()
        self.performance_cache = {}
        self.adaptive_params = {}

        if not VECTORBT_AVAILABLE:
            logger.warning("VectorBT not available - some features will be limited")
        else:
            logger.info("VectorBT Enhanced Indicators initialized")

        # GPU设置
        if self.enable_gpu and VECTORBT_AVAILABLE:
            try:
                import cupy as cp
                vbt.settings.uses_cupy = True
                logger.info("GPU acceleration enabled")
            except ImportError:
                logger.warning("CuPy not available - falling back to CPU")
                self.enable_gpu = False

    def batch_calculate_rsi(self, prices: pd.DataFrame,
                           periods: List[int] = None) -> pd.DataFrame:
        """
        批量计算RSI指标

        Args:
            prices: 多资产价格数据 (时间 x 资产)
            periods: RSI周期列表

        Returns:
            RSI指标矩阵 (时间 x 资产 x 周期)
        """
        if periods is None:
            periods = [14, 21, 30, 50]

        logger.info(f"Batch calculating RSI for {len(periods)} periods across {prices.shape[1]} assets")

        if VECTORBT_AVAILABLE:
            # 使用VectorBT的批量RSI计算
            rsi_indicator = vbt.RSI.run(prices, window=periods)

            # 转换为更友好的格式
            if len(periods) == 1:
                return rsi_indicator.rsi
            else:
                # 多周期情况下重塑数据
                rsi_values = {}
                for i, period in enumerate(periods):
                    rsi_values[f'RSI_{period}'] = rsi_indicator.rsi.iloc[:, i]

                return pd.DataFrame(rsi_values, index=prices.index)
        else:
            # 回退到逐个计算
            rsi_results = {}
            for period in periods:
                rsi_values = []
                for asset in prices.columns:
                    asset_rsi = self.core_indicators.calculate_rsi(prices[asset], period)
                    rsi_values.append(asset_rsi)

                rsi_results[f'RSI_{period}'] = pd.concat(rsi_values, axis=1)

            return pd.concat(rsi_results, axis=1)

    def batch_calculate_macd(self, prices: pd.DataFrame,
                            fast_periods: List[int] = None,
                            slow_periods: List[int] = None,
                            signal_periods: List[int] = None) -> Dict[str, pd.DataFrame]:
        """
        批量计算MACD指标

        Args:
            prices: 多资产价格数据
            fast_periods: 快线周期列表
            slow_periods: 慢线周期列表
            signal_periods: 信号线周期列表

        Returns:
            包含MACD线、信号线、柱状图的字典
        """
        if fast_periods is None:
            fast_periods = [12]
        if slow_periods is None:
            slow_periods = [26]
        if signal_periods is None:
            signal_periods = [9]

        logger.info(f"Batch calculating MACD with {len(fast_periods)}x{len(slow_periods)}x{len(signal_periods)} combinations")

        if VECTORBT_AVAILABLE:
            # 使用VectorBT批量MACD计算
            macd_indicator = vbt.MACD.run(
                prices,
                fast_window=fast_periods,
                slow_window=slow_periods,
                signal_window=signal_periods
            )

            return {
                'macd': macd_indicator.macd,
                'signal': macd_indicator.signal,
                'histogram': macd_indicator.histogram
            }
        else:
            # 回退实现
            macd_results = {'macd': [], 'signal': [], 'histogram': []}

            for fast in fast_periods:
                for slow in slow_periods:
                    for signal in signal_periods:
                        macd_values = []
                        signal_values = []
                        histogram_values = []

                        for asset in prices.columns:
                            macd_dict = self.core_indicators.calculate_macd(
                                prices[asset], fast, slow, signal
                            )

                            macd_values.append(macd_dict['macd'])
                            signal_values.append(macd_dict['signal'])
                            histogram_values.append(macd_dict['histogram'])

                        macd_results['macd'].append(pd.concat(macd_values, axis=1))
                        macd_results['signal'].append(pd.concat(signal_values, axis=1))
                        macd_results['histogram'].append(pd.concat(histogram_values, axis=1))

            return macd_results

    def vectorized_cross_indicator_analysis(self, prices: pd.DataFrame,
                                         indicator_configs: Dict[str, Dict]) -> Dict[str, Any]:
        """
        向量化交叉指标分析

        Args:
            prices: 价格数据
            indicator_configs: 指标配置字典

        Returns:
            交叉分析结果
        """
        logger.info(f"Performing cross-indicator analysis with {len(indicator_configs)} indicators")

        results = {}

        # 批量计算所有指标
        all_indicators = {}
        for name, config in indicator_configs.items():
            if config['type'] == 'rsi':
                periods = config.get('periods', [14])
                indicators = self.batch_calculate_rsi(prices, periods)
            elif config['type'] == 'macd':
                fast_periods = config.get('fast_periods', [12])
                slow_periods = config.get('slow_periods', [26])
                indicators = self.batch_calculate_macd(
                    prices, fast_periods, slow_periods
                )
            elif config['type'] == 'bollinger':
                indicators = self.batch_calculate_bollinger_bands(
                    prices,
                    config.get('periods', [20]),
                    config.get('std_devs', [2.0])
                )
            else:
                continue

            all_indicators[name] = indicators

        # 计算指标间的相关性
        correlations = self._calculate_indicator_correlations(all_indicators)

        # 生成交易信号
        signals = self._generate_cross_indicator_signals(all_indicators, prices)

        # 性能归因分析
        attribution = self._analyze_indicator_attribution(all_indicators, signals, prices)

        results = {
            'indicators': all_indicators,
            'correlations': correlations,
            'signals': signals,
            'attribution': attribution,
            'analysis_date': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        return results

    def batch_calculate_bollinger_bands(self, prices: pd.DataFrame,
                                     periods: List[int] = None,
                                     std_devs: List[float] = None) -> Dict[str, pd.DataFrame]:
        """
        批量计算布林带指标

        Args:
            prices: 多资产价格数据
            periods: 周期列表
            std_devs: 标准差倍数列表

        Returns:
            包含上轨、中轨、下轨的字典
        """
        if periods is None:
            periods = [20]
        if std_devs is None:
            std_devs = [2.0]

        logger.info(f"Batch calculating Bollinger Bands with {len(periods)}x{len(std_devs)} combinations")

        if VECTORBT_AVAILABLE:
            # 使用VectorBT批量布林带计算
            bb_indicator = vbt.BBANDS.run(
                prices,
                window=periods,
                std=std_devs
            )

            return {
                'upper': bb_indicator.upper,
                'middle': bb_indicator.middle,
                'lower': bb_indicator.lower
            }
        else:
            # 回退实现
            bb_results = {'upper': [], 'middle': [], 'lower': []}

            for period in periods:
                for std_dev in std_devs:
                    upper_values = []
                    middle_values = []
                    lower_values = []

                    for asset in prices.columns:
                        bb_dict = self.core_indicators.calculate_bollinger_bands(
                            prices[asset], period, std_dev
                        )

                        upper_values.append(bb_dict['upper'])
                        middle_values.append(bb_dict['middle'])
                        lower_values.append(bb_dict['lower'])

                    bb_results['upper'].append(pd.concat(upper_values, axis=1))
                    bb_results['middle'].append(pd.concat(middle_values, axis=1))
                    bb_results['lower'].append(pd.concat(lower_values, axis=1))

            return bb_results

    def adaptive_parameter_optimization(self, prices: pd.DataFrame,
                                     returns: pd.Series,
                                     indicator_type: str,
                                     param_ranges: Dict[str, List],
                                     optimization_window: int = 252,
                                     rebalance_frequency: int = 20) -> Dict[str, Any]:
        """
        自适应指标参数优化

        Args:
            prices: 价格数据
            returns: 收益率数据
            indicator_type: 指标类型
            param_ranges: 参数范围
            optimization_window: 优化窗口
            rebalance_frequency: 再平衡频率

        Returns:
            优化结果
        """
        logger.info(f"Starting adaptive parameter optimization for {indicator_type}")

        # 滚动窗口优化
        optimal_params = []
        performance_scores = []

        for start_idx in range(0, len(prices) - optimization_window, rebalance_frequency):
            end_idx = start_idx + optimization_window

            # 训练窗口数据
            train_prices = prices.iloc[start_idx:end_idx]
            train_returns = returns.iloc[start_idx:end_idx]

            # 网格搜索最优参数
            best_params, best_score = self._grid_search_parameters(
                train_prices, train_returns, indicator_type, param_ranges
            )

            optimal_params.append(best_params)
            performance_scores.append(best_score)

            # 测试窗口验证
            test_start = end_idx
            test_end = min(test_start + rebalance_frequency, len(prices))

            if test_end > test_start:
                test_prices = prices.iloc[test_start:test_end]
                test_returns = returns.iloc[test_start:test_end]

                # 使用最优参数计算测试性能
                test_score = self._evaluate_parameters(
                    test_prices, test_returns, indicator_type, best_params
                )

                performance_scores[-1] = (performance_scores[-1] + test_score) / 2

        # 构建时间序列的最优参数
        param_timeline = []
        for i, params in enumerate(optimal_params):
            start_date = prices.index[i * rebalance_frequency]
            end_date = prices.index[min((i + 1) * rebalance_frequency, len(prices) - 1)]

            param_timeline.append({
                'start_date': start_date,
                'end_date': end_date,
                'optimal_params': params,
                'performance_score': performance_scores[i]
            })

        return {
            'indicator_type': indicator_type,
            'param_timeline': param_timeline,
            'average_performance': np.mean(performance_scores),
            'performance_stability': np.std(performance_scores),
            'optimization_summary': self._summarize_optimization_results(optimal_params)
        }

    def calculate_indicator_performance_attribution(self, prices: pd.DataFrame,
                                                signals: Dict[str, pd.Series],
                                                benchmark_returns: pd.Series) -> Dict[str, IndicatorPerformance]:
        """
        计算指标性能归因

        Args:
            prices: 价格数据
            signals: 交易信号字典
            benchmark_returns: 基准收益率

        Returns:
            性能归因结果
        """
        logger.info("Calculating indicator performance attribution")

        attribution_results = {}

        for indicator_name, signal in signals.items():
            # 计算信号质量
            signal_quality = self._calculate_signal_quality(signal, prices)

            # 计算预测能力
            predictive_power = self._calculate_predictive_power(signal, benchmark_returns)

            # 计算稳定性
            stability_score = self._calculate_stability_score(signal)

            # 性能指标
            performance = IndicatorPerformance(
                indicator_name=indicator_name,
                calculation_time=0.0,  # 实际应用中需要计时
                memory_usage=0.0,  # 实际应用中需要监控内存
                signal_quality=signal_quality,
                predictive_power=predictive_power,
                stability_score=stability_score
            )

            attribution_results[indicator_name] = performance

        return attribution_results

    def _calculate_indicator_correlations(self, indicators: Dict[str, Any]) -> Dict[str, pd.DataFrame]:
        """计算指标间相关性"""
        correlations = {}

        # 提取所有指标的数值序列
        indicator_series = {}
        for name, indicator_data in indicators.items():
            if isinstance(indicator_data, dict):
                for key, series in indicator_data.items():
                    if isinstance(series, pd.DataFrame):
                        for col in series.columns:
                            indicator_series[f"{name}_{key}_{col}"] = series[col]
                    elif isinstance(series, pd.Series):
                        indicator_series[f"{name}_{key}"] = series
            elif isinstance(indicator_data, pd.DataFrame):
                for col in indicator_data.columns:
                    indicator_series[f"{name}_{col}"] = indicator_data[col]
            elif isinstance(indicator_data, pd.Series):
                indicator_series[name] = indicator_data

        if len(indicator_series) > 1:
            # 创建DataFrame并计算相关性
            corr_df = pd.DataFrame(indicator_series)
            correlations['matrix'] = corr_df.corr()
            correlations['summary'] = {
                'avg_correlation': corr_df.corr().values[np.triu_indices_from(corr_df.corr().values, k=1)].mean(),
                'max_correlation': corr_df.corr().values[np.triu_indices_from(corr_df.corr().values, k=1)].max(),
                'min_correlation': corr_df.corr().values[np.triu_indices_from(corr_df.corr().values, k=1)].min()
            }

        return correlations

    def _generate_cross_indicator_signals(self, indicators: Dict[str, Any],
                                       prices: pd.DataFrame) -> Dict[str, pd.Series]:
        """生成交叉指标信号"""
        signals = {}

        # RSI信号
        if 'RSI' in indicators:
            rsi_data = indicators['RSI']
            if isinstance(rsi_data, pd.DataFrame):
                for col in rsi_data.columns:
                    # RSI超买超卖信号
                    overbought = (rsi_data[col] > 70).astype(int)
                    oversold = (rsi_data[col] < 30).astype(int)

                    signals[f'RSI_{col}_overbought'] = overbought
                    signals[f'RSI_{col}_oversold'] = oversold

        # MACD信号
        if 'MACD' in indicators:
            macd_data = indicators['MACD']
            if isinstance(macd_data, dict) and 'macd' in macd_data:
                macd_line = macd_data['macd']
                signal_line = macd_data['signal']

                if isinstance(macd_line, pd.DataFrame) and isinstance(signal_line, pd.DataFrame):
                    for col in macd_line.columns:
                        if col in signal_line.columns:
                            # MACD金叉死叉信号
                            golden_cross = (macd_line[col] > signal_line[col]).astype(int)
                            death_cross = (macd_line[col] < signal_line[col]).astype(int)

                            signals[f'MACD_{col}_golden_cross'] = golden_cross
                            signals[f'MACD_{col}_death_cross'] = death_cross

        # 布林带信号
        if 'Bollinger' in indicators:
            bb_data = indicators['Bollinger']
            if isinstance(bb_data, dict):
                upper = bb_data.get('upper')
                lower = bb_data.get('lower')

                if isinstance(upper, pd.DataFrame) and isinstance(lower, pd.DataFrame):
                    for col in upper.columns:
                        if col in lower.columns and col in prices.columns:
                            # 价格突破布林带信号
                            upper_breakout = (prices[col] > upper[col]).astype(int)
                            lower_breakout = (prices[col] < lower[col]).astype(int)

                            signals[f'BB_{col}_upper_breakout'] = upper_breakout
                            signals[f'BB_{col}_lower_breakout'] = lower_breakout

        return signals

    def _analyze_indicator_attribution(self, indicators: Dict[str, Any],
                                    signals: Dict[str, pd.Series],
                                    prices: pd.DataFrame) -> Dict[str, Any]:
        """分析指标归因"""
        attribution = {}

        for indicator_name in indicators.keys():
            indicator_signals = {k: v for k, v in signals.items() if indicator_name in k}

            if indicator_signals:
                # 计算该指标的信号数量和质量
                signal_count = len(indicator_signals)
                avg_signal_strength = np.mean([signal.mean() for signal in indicator_signals.values()])

                # 计算信号与价格变化的相关性
                price_changes = prices.pct_change().fillna(0)
                signal_correlations = {}

                for signal_name, signal in indicator_signals.items():
                    if len(signal) == len(price_changes):
                        # 找到对应的资产
                        for asset in price_changes.columns:
                            correlation = np.corrcoef(signal.fillna(0), price_changes[asset])[0, 1]
                            if not np.isnan(correlation):
                                signal_correlations[f"{signal_name}_{asset}"] = correlation

                attribution[indicator_name] = {
                    'signal_count': signal_count,
                    'avg_signal_strength': avg_signal_strength,
                    'signal_correlations': signal_correlations,
                    'max_correlation': max(signal_correlations.values()) if signal_correlations else 0,
                    'avg_correlation': np.mean(list(signal_correlations.values())) if signal_correlations else 0
                }

        return attribution

    def _grid_search_parameters(self, prices: pd.DataFrame, returns: pd.Series,
                              indicator_type: str, param_ranges: Dict[str, List]) -> Tuple[Dict, float]:
        """网格搜索最优参数"""
        best_score = float('-inf')
        best_params = {}

        # 简化的网格搜索实现
        for period in param_ranges.get('periods', [14]):
            if indicator_type == 'rsi':
                rsi = self.core_indicators.calculate_rsi(prices.iloc[:, 0], period)
                # 基于RSI生成信号并计算性能
                signals = pd.Series(0, index=prices.index)
                signals[rsi < 30] = 1  # 买入信号
                signals[rsi > 70] = -1  # 卖出信号

                score = self._calculate_signal_performance(signals, returns)

                if score > best_score:
                    best_score = score
                    best_params = {'period': period}

        return best_params, best_score

    def _evaluate_parameters(self, prices: pd.DataFrame, returns: pd.Series,
                           indicator_type: str, params: Dict) -> float:
        """评估参数性能"""
        if indicator_type == 'rsi':
            rsi = self.core_indicators.calculate_rsi(prices.iloc[:, 0], params['period'])
            signals = pd.Series(0, index=prices.index)
            signals[rsi < 30] = 1
            signals[rsi > 70] = -1

            return self._calculate_signal_performance(signals, returns)

        return 0.0

    def _calculate_signal_performance(self, signals: pd.Series, returns: pd.Series) -> float:
        """计算信号性能"""
        # 简化的夏普比率计算
        strategy_returns = signals.shift(1) * returns  # 信号下一天执行
        if strategy_returns.std() > 0:
            return strategy_returns.mean() / strategy_returns.std()
        return 0.0

    def _summarize_optimization_results(self, optimal_params: List[Dict]) -> Dict[str, Any]:
        """总结优化结果"""
        if not optimal_params:
            return {}

        param_stats = {}
        for key in optimal_params[0].keys():
            values = [params[key] for params in optimal_params]
            param_stats[key] = {
                'mean': np.mean(values),
                'std': np.std(values),
                'min': min(values),
                'max': max(values),
                'stability': 1 - (np.std(values) / np.mean(values)) if np.mean(values) > 0 else 0
            }

        return param_stats

    def _calculate_signal_quality(self, signal: pd.Series, prices: pd.DataFrame) -> float:
        """计算信号质量"""
        # 信号频率（避免过于频繁或稀少的信号）
        signal_frequency = signal.abs().mean()
        frequency_score = 1 - abs(signal_frequency - 0.1) * 10  # 目标10%的信号频率
        frequency_score = max(0, min(1, frequency_score))

        # 信号平滑度（避免频繁切换）
        if len(signal) > 1:
            signal_changes = (signal.diff() != 0).sum()
            change_ratio = signal_changes / len(signal)
            smoothness_score = 1 - change_ratio
        else:
            smoothness_score = 1.0

        return (frequency_score + smoothness_score) / 2

    def _calculate_predictive_power(self, signal: pd.Series, returns: pd.Series) -> float:
        """计算预测能力"""
        if len(signal) != len(returns):
            return 0.0

        # 将信号对齐到收益
        aligned_signal = signal.shift(1).fillna(0)

        # 计算相关性
        correlation = np.corrcoef(aligned_signal, returns)[0, 1]

        return abs(correlation) if not np.isnan(correlation) else 0.0

    def _calculate_stability_score(self, signal: pd.Series) -> float:
        """计算稳定性评分"""
        if len(signal) < 2:
            return 1.0

        # 计算信号的变化程度
        signal_std = signal.std()

        # 标准化稳定性评分
        if signal_std > 0:
            stability = 1 / (1 + signal_std)
        else:
            stability = 1.0

        return max(0, min(1, stability))

# 便利函数
def create_vectorbt_indicators(enable_gpu: bool = False) -> VectorBTIndicators:
    """创建VectorBT技术指标实例"""
    return VectorBTIndicators(enable_gpu)

# 测试函数
def test_vectorbt_indicators():
    """测试VectorBT技术指标功能"""
    logger.info("Testing VectorBT Enhanced Indicators...")

    # 创建测试数据
    np.random.seed(42)
    dates = pd.date_range('2020-01-01', '2023-12-31', freq='D')
    assets = ['Asset_A', 'Asset_B', 'Asset_C']

    prices_data = {}
    for asset in assets:
        prices = 100 * np.exp(np.cumsum(np.random.normal(0.001, 0.02, len(dates))))
        prices_data[asset] = pd.Series(prices, index=dates)

    prices_df = pd.DataFrame(prices_data)
    returns = prices_df.pct_change().fillna(0)

    # 创建指标实例
    vbt_indicators = VectorBTIndicators()

    # 测试批量RSI计算
    rsi_results = vbt_indicators.batch_calculate_rsi(prices_df, [14, 21])
    logger.info(f"RSI batch calculation completed: {rsi_results.shape}")

    # 测试交叉指标分析
    indicator_configs = {
        'RSI': {'type': 'rsi', 'periods': [14, 21]},
        'MACD': {'type': 'macd', 'fast_periods': [12], 'slow_periods': [26]}
    }

    cross_analysis = vbt_indicators.vectorized_cross_indicator_analysis(prices_df, indicator_configs)
    logger.info(f"Cross-indicator analysis completed: {len(cross_analysis)} components")

    # 测试自适应参数优化
    param_ranges = {'periods': [10, 14, 20, 30]}
    adaptive_results = vbt_indicators.adaptive_parameter_optimization(
        prices_df, returns.iloc[:, 0], 'rsi', param_ranges, optimization_window=100
    )
    logger.info(f"Adaptive optimization completed: {adaptive_results['average_performance']:.3f}")

    return {
        'rsi_results': rsi_results,
        'cross_analysis': cross_analysis,
        'adaptive_results': adaptive_results
    }

if __name__ == "__main__":
    test_vectorbt_indicators()