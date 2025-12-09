#!/usr/bin/env python3
"""
第4阶段 Task 19: 时间序列模式分析器
Phase 4 Task 19: Time Series Pattern Analyzer

高级时间序列分析，包括季节性检测、趋势分析和结构断裂检测
Advanced time series analysis with seasonal detection, trend analysis, and structural break detection
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any, Union
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Statistical and time series libraries
from scipy import stats
from scipy.signal import find_peaks, savgol_filter
from statsmodels.tsa.seasonal import STL, seasonal_decompose
from statsmodels.tsa.stattools import adfuller, kpss
from statsmodels.tsa.filters.hp_filter import hpfilter
from statsmodels.tsa.regime_switching.markov_regression import MarkovRegression
import ruptures as rpt

# Machine learning for pattern detection
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

# Visualization
import matplotlib.pyplot as plt
import seaborn as sns

# Logging
import logging
logger = logging.getLogger(__name__)

from ..core.behavioral_config import get_behavioral_config, TimeSeriesConfig


class SeasonalPatternDetector:
    """季节性模式检测器"""

    def __init__(self, config: Optional[TimeSeriesConfig] = None):
        self.config = config or get_behavioral_config().time_series
        self.scaler = StandardScaler()

    def detect_seasonality(self, data: pd.Series) -> Dict[str, Any]:
        """
        检测时间序列的季节性模式

        Args:
            data: 时间序列数据

        Returns:
            季节性分析结果
        """
        try:
            results = {}

            # 基础统计分析
            results['basic_stats'] = self._get_basic_statistics(data)

            # 平稳性检验
            results['stationarity'] = self._test_stationarity(data)

            # STL分解
            results['stl_decomposition'] = self._stl_decomposition(data)

            # 经典季节性分解
            results['classical_decomposition'] = self._classical_decomposition(data)

            # 季节性强度分析
            results['seasonal_strength'] = self._calculate_seasonal_strength(data)

            # 周期性检测
            results['periodicity'] = self._detect_periodicity(data)

            # 季节性模式分类
            results['seasonal_pattern'] = self._classify_seasonal_pattern(results)

            logger.info(f"Seasonality analysis completed for {len(data)} data points")
            return results

        except Exception as e:
            logger.error(f"Error in seasonality detection: {e}")
            return {'error': str(e)}

    def _get_basic_statistics(self, data: pd.Series) -> Dict[str, float]:
        """基础统计信息"""
        return {
            'mean': float(data.mean()),
            'std': float(data.std()),
            'min': float(data.min()),
            'max': float(data.max()),
            'skewness': float(stats.skew(data)),
            'kurtosis': float(stats.kurtosis(data)),
            'cv': float(data.std() / data.mean()) if data.mean() != 0 else 0
        }

    def _test_stationarity(self, data: pd.Series) -> Dict[str, Any]:
        """平稳性检验"""
        try:
            # ADF检验
            adf_result = adfuller(data.dropna())
            adf_statistic = adf_result[0]
            adf_pvalue = adf_result[1]
            adf_critical = adf_result[4]

            # KPSS检验
            kpss_result = kpss(data.dropna())
            kpss_statistic = kpss_result[0]
            kpss_pvalue = kpss_result[1]

            return {
                'adf_statistic': adf_statistic,
                'adf_pvalue': adf_pvalue,
                'adf_critical_values': adf_critical,
                'adf_is_stationary': adf_pvalue < 0.05,
                'kpss_statistic': kpss_statistic,
                'kpss_pvalue': kpss_pvalue,
                'kpss_is_stationary': kpss_pvalue > 0.05,
                'conclusion': 'stationary' if (adf_pvalue < 0.05 and kpss_pvalue > 0.05) else 'non_stationary'
            }
        except Exception as e:
            logger.warning(f"Stationarity test failed: {e}")
            return {'error': str(e)}

    def _stl_decomposition(self, data: pd.Series) -> Dict[str, Any]:
        """STL季节性分解"""
        try:
            # 确保有足够的数据点
            if len(data) < 2 * self.config.seasonal_period:
                logger.warning(f"Insufficient data for STL decomposition: {len(data)} < {2 * self.config.seasonal_period}")
                return {'error': 'Insufficient data for STL decomposition'}

            # STL分解
            stl = STL(data, seasonal=self.config.stl_seasonal,
                     trend=self.config.stl_trend, robust=self.config.stl_robust)
            result = stl.fit()

            # 提取组件
            trend = result.trend
            seasonal = result.seasonal
            residual = result.resid

            # 计算各组件的方差贡献
            total_var = data.var()
            trend_var = trend.var() / total_var if total_var > 0 else 0
            seasonal_var = seasonal.var() / total_var if total_var > 0 else 0
            residual_var = residual.var() / total_var if total_var > 0 else 0

            return {
                'trend': trend.dropna().tolist(),
                'seasonal': seasonal.dropna().tolist(),
                'residual': residual.dropna().tolist(),
                'trend_strength': float(trend_var),
                'seasonal_strength': float(seasonal_var),
                'residual_strength': float(residual_var),
                'decomposition_quality': float(1 - residual_var)  # 1 - residual variance
            }
        except Exception as e:
            logger.warning(f"STL decomposition failed: {e}")
            return {'error': str(e)}

    def _classical_decomposition(self, data: pd.Series) -> Dict[str, Any]:
        """经典季节性分解"""
        try:
            # 经典分解
            decomposition = seasonal_decompose(
                data,
                model=self.config.seasonal_model,
                period=self.config.seasonal_period,
                extrapolate_trend='freq'
            )

            # 计算组件贡献
            total_var = data.var()
            trend_var = decomposition.trend.var() / total_var if total_var > 0 else 0
            seasonal_var = decomposition.seasonal.var() / total_var if total_var > 0 else 0
            residual_var = decomposition.resid.var() / total_var if total_var > 0 else 0

            return {
                'trend': decomposition.trend.dropna().tolist(),
                'seasonal': decomposition.seasonal.dropna().tolist(),
                'residual': decomposition.resid.dropna().tolist(),
                'trend_strength': float(trend_var),
                'seasonal_strength': float(seasonal_var),
                'residual_strength': float(residual_var)
            }
        except Exception as e:
            logger.warning(f"Classical decomposition failed: {e}")
            return {'error': str(e)}

    def _calculate_seasonal_strength(self, data: pd.Series) -> Dict[str, float]:
        """计算季节性强度"""
        try:
            # 使用不同的方法计算季节性强度
            strength_methods = {}

            # 方法1: 基于方差比例
            decomposition = seasonal_decompose(data, period=self.config.seasonal_period, extrapolate_trend='freq')
            if len(decomposition.seasonal.dropna()) > 0:
                seasonal_var = decomposition.seasonal.var()
                total_var = data.var()
                strength_methods['variance_ratio'] = float(seasonal_var / total_var if total_var > 0 else 0)

            # 方法2: 基于自相关函数
            if len(data) >= self.config.seasonal_period:
                autocorr = [data.autocorr(lag=i) for i in range(1, min(25, self.config.seasonal_period//2))]
                if autocorr:
                    strength_methods['autocorr_peak'] = float(max(autocorr))

            # 方法3: 基于季节性模式的一致性
            if len(data) >= 2 * self.config.seasonal_period:
                seasonal_pattern = decomposition.seasonal.dropna()
                if len(seasonal_pattern) >= self.config.seasonal_period:
                    # 计算季节性模式的一致性
                    patterns = []
                    for i in range(0, len(seasonal_pattern) - self.config.seasonal_period + 1, self.config.seasonal_period):
                        pattern = seasonal_pattern.iloc[i:i+self.config.seasonal_period]
                        if len(pattern) == self.config.seasonal_period:
                            patterns.append(pattern.values)

                    if len(patterns) >= 2:
                        # 计算模式之间的相关性
                        correlations = []
                        for i in range(len(patterns)):
                            for j in range(i+1, len(patterns)):
                                corr = np.corrcoef(patterns[i], patterns[j])[0, 1]
                                if not np.isnan(corr):
                                    correlations.append(corr)

                        if correlations:
                            strength_methods['pattern_consistency'] = float(np.mean(correlations))

            return strength_methods

        except Exception as e:
            logger.warning(f"Seasonal strength calculation failed: {e}")
            return {'error': str(e)}

    def _detect_periodicity(self, data: pd.Series) -> Dict[str, Any]:
        """检测周期性"""
        try:
            periodicity_info = {}

            # 使用FFT检测主要频率
            if len(data) >= 20:
                # 去除趋势
                detrended = data - data.rolling(window=min(20, len(data)//4), center=True).mean()
                detrended = detrended.fillna(method='bfill').fillna(method='ffill')

                # FFT分析
                fft = np.fft.fft(detrended.values)
                freq = np.fft.fftfreq(len(detrended))

                # 计算功率谱密度
                psd = np.abs(fft) ** 2

                # 找到主要频率（排除DC分量）
                positive_freq_idx = freq > 0
                if np.any(positive_freq_idx):
                    dominant_freq_idx = np.argmax(psd[positive_freq_idx])
                    dominant_freq = freq[positive_freq_idx][dominant_freq_idx]
                    dominant_period = int(1 / dominant_freq) if dominant_freq > 0 else None

                    if dominant_period and 1 < dominant_period < len(data) // 2:
                        periodicity_info['dominant_period'] = dominant_period
                        periodicity_info['dominant_frequency'] = float(dominant_freq)
                        periodicity_info['psd_peak'] = float(psd[positive_freq_idx][dominant_freq_idx])

            # 使用自相关函数检测周期性
            if len(data) >= self.config.seasonal_period:
                autocorr_values = []
                for lag in range(1, min(self.config.seasonal_period * 2, len(data) // 2)):
                    autocorr = data.autocorr(lag=lag)
                    if not np.isnan(autocorr):
                        autocorr_values.append(autocorr)

                if autocorr_values:
                    # 找到自相关的峰值
                    peaks, _ = find_peaks(autocorr_values, height=0.3, distance=5)
                    if len(peaks) > 0:
                        peak_lags = [peak + 1 for peak in peaks]  # lag = index + 1
                        periodicity_info['autocorr_peaks'] = peak_lags[:5]  # 前5个峰值
                        periodicity_info['max_autocorr'] = float(max(autocorr_values))

            return periodicity_info

        except Exception as e:
            logger.warning(f"Periodicity detection failed: {e}")
            return {'error': str(e)}

    def _classify_seasonal_pattern(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """分类季节性模式"""
        try:
            classification = {}

            # 基于季节性强度的分类
            seasonal_strength = 0
            if 'seasonal_strength' in results and 'variance_ratio' in results['seasonal_strength']:
                seasonal_strength = results['seasonal_strength']['variance_ratio']

            if seasonal_strength > 0.3:
                classification['strength'] = 'strong'
            elif seasonal_strength > 0.1:
                classification['strength'] = 'moderate'
            else:
                classification['strength'] = 'weak'

            # 基于周期性的分类
            has_periodicity = False
            if 'periodicity' in results and 'dominant_period' in results['periodicity']:
                has_periodicity = True
                dominant_period = results['periodicity']['dominant_period']

                # 根据周期长度分类
                if dominant_period <= 5:
                    classification['cycle_type'] = 'intraday'
                elif dominant_period <= 22:  # 大约一个月
                    classification['cycle_type'] = 'weekly_monthly'
                elif dominant_period <= 252:  # 大约一年
                    classification['cycle_type'] = 'seasonal_yearly'
                else:
                    classification['cycle_type'] = 'long_term'

            classification['has_seasonality'] = seasonal_strength > 0.1 and has_periodicity

            # 基于分解质量的分类
            decomposition_quality = 0
            if 'stl_decomposition' in results and 'decomposition_quality' in results['stl_decomposition']:
                decomposition_quality = results['stl_decomposition']['decomposition_quality']

            if decomposition_quality > 0.8:
                classification['decomposition_quality'] = 'excellent'
            elif decomposition_quality > 0.6:
                classification['decomposition_quality'] = 'good'
            elif decomposition_quality > 0.4:
                classification['decomposition_quality'] = 'fair'
            else:
                classification['decomposition_quality'] = 'poor'

            return classification

        except Exception as e:
            logger.warning(f"Seasonal pattern classification failed: {e}")
            return {'error': str(e)}


class TrendAnalyzer:
    """趋势分析器"""

    def __init__(self, config: Optional[TimeSeriesConfig] = None):
        self.config = config or get_behavioral_config().time_series

    def analyze_trend(self, data: pd.Series) -> Dict[str, Any]:
        """
        分析时间序列趋势

        Args:
            data: 时间序列数据

        Returns:
            趋势分析结果
        """
        try:
            results = {}

            # 线性趋势分析
            results['linear_trend'] = self._linear_trend_analysis(data)

            # HP滤波器趋势分析
            results['hp_filter'] = self._hp_filter_analysis(data)

            # 移动平均趋势分析
            results['moving_average_trend'] = self._moving_average_trend(data)

            # 趋势强度分析
            results['trend_strength'] = self._calculate_trend_strength(data)

            # 趋势变化点检测
            results['trend_changes'] = self._detect_trend_changes(data)

            # 趋势分类
            results['trend_classification'] = self._classify_trend(results)

            logger.info(f"Trend analysis completed for {len(data)} data points")
            return results

        except Exception as e:
            logger.error(f"Error in trend analysis: {e}")
            return {'error': str(e)}

    def _linear_trend_analysis(self, data: pd.Series) -> Dict[str, Any]:
        """线性趋势分析"""
        try:
            x = np.arange(len(data))
            y = data.values

            # 线性回归
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

            # 计算趋势线
            trend_line = slope * x + intercept

            # 趋势显著性
            is_significant = p_value < 0.05

            # 趋势方向
            if slope > 0:
                direction = 'increasing'
            elif slope < 0:
                direction = 'decreasing'
            else:
                direction = 'flat'

            return {
                'slope': float(slope),
                'intercept': float(intercept),
                'r_squared': float(r_value ** 2),
                'p_value': float(p_value),
                'standard_error': float(std_err),
                'is_significant': is_significant,
                'direction': direction,
                'trend_line': trend_line.tolist()
            }

        except Exception as e:
            logger.warning(f"Linear trend analysis failed: {e}")
            return {'error': str(e)}

    def _hp_filter_analysis(self, data: pd.Series) -> Dict[str, Any]:
        """Hodrick-Prescott滤波器趋势分析"""
        try:
            # 应用HP滤波器
            cycle, trend = hpfilter(data, lamb=self.config.hp_lambda)

            # 计算趋势和周期的统计信息
            trend_volatility = trend.std()
            cycle_volatility = cycle.std()

            # 趋势平滑度（一阶差分的方差）
            trend_smoothness = trend.diff().var()

            # 趋势单调性
            trend_diff = trend.diff().dropna()
            increasing_periods = (trend_diff > 0).sum()
            decreasing_periods = (trend_diff < 0).sum()

            monotonicity = max(increasing_periods, decreasing_periods) / len(trend_diff)

            return {
                'trend': trend.dropna().tolist(),
                'cycle': cycle.dropna().tolist(),
                'trend_volatility': float(trend_volatility),
                'cycle_volatility': float(cycle_volatility),
                'trend_smoothness': float(trend_smoothness),
                'monotonicity': float(monotonicity),
                'increasing_periods': int(increasing_periods),
                'decreasing_periods': int(decreasing_periods)
            }

        except Exception as e:
            logger.warning(f"HP filter analysis failed: {e}")
            return {'error': str(e)}

    def _moving_average_trend(self, data: pd.Series) -> Dict[str, Any]:
        """移动平均趋势分析"""
        try:
            results = {}

            # 不同周期的移动平均
            periods = [10, 20, 50, 100, 200]
            for period in periods:
                if len(data) >= period:
                    ma = data.rolling(window=period, center=True).mean()
                    results[f'ma_{period}'] = ma.dropna().tolist()

                    # 计算移动平均的斜率
                    ma_diff = ma.diff().dropna()
                    if len(ma_diff) > 0:
                        slope = ma_diff.mean()
                        results[f'ma_{period}_slope'] = float(slope)

                        # 趋势方向
                        if slope > 0:
                            results[f'ma_{period}_direction'] = 'increasing'
                        elif slope < 0:
                            results[f'ma_{period}_direction'] = 'decreasing'
                        else:
                            results[f'ma_{period}_direction'] = 'flat'

            return results

        except Exception as e:
            logger.warning(f"Moving average trend analysis failed: {e}")
            return {'error': str(e)}

    def _calculate_trend_strength(self, data: pd.Series) -> Dict[str, float]:
        """计算趋势强度"""
        try:
            strength_metrics = {}

            # 基于R平方的趋势强度
            x = np.arange(len(data))
            slope, _, r_value, _, _ = stats.linregress(x, data.values)
            strength_metrics['r_squared_strength'] = float(r_value ** 2)

            # 基于方向一致性的趋势强度
            data_diff = data.diff().dropna()
            if len(data_diff) > 0:
                positive_changes = (data_diff > 0).sum()
                negative_changes = (data_diff < 0).sum()
                total_changes = len(data_diff)

                # 趋势一致性 = max(同向变化数) / 总变化数
                consistency = max(positive_changes, negative_changes) / total_changes
                strength_metrics['direction_consistency'] = float(consistency)

            # 基于长期与短期移动平均关系的趋势强度
            if len(data) >= 50:
                short_ma = data.rolling(window=10).mean()
                long_ma = data.rolling(window=50).mean()

                # 计算短期MA在长期MA之上的比例
                ma_relationship = (short_ma > long_ma).sum() / len(short_ma.dropna())
                strength_metrics['ma_relationship_strength'] = float(abs(ma_relationship - 0.5) * 2)  # 归一化到0-1

            # 综合趋势强度
            valid_metrics = [v for v in strength_metrics.values() if not np.isnan(v)]
            if valid_metrics:
                strength_metrics['overall_strength'] = float(np.mean(valid_metrics))
            else:
                strength_metrics['overall_strength'] = 0.0

            return strength_metrics

        except Exception as e:
            logger.warning(f"Trend strength calculation failed: {e}")
            return {'error': str(e)}

    def _detect_trend_changes(self, data: pd.Series) -> Dict[str, Any]:
        """检测趋势变化点"""
        try:
            change_points = []

            # 使用ruptures库检测变化点
            if len(data) >= self.config.min_segment_length * 2:
                # 使用Pelt算法检测变化点
                model = "l2"  # L2成本函数
                algo = rpt.Pelt(model=model, min_size=self.config.min_segment_length).fit(data.values)
                result = algo.predict(pen=10)

                # 提取变化点（去掉最后一个点，它是序列结束）
                if len(result) > 1:
                    change_points = result[:-1]

            # 分析变化点特征
            if change_points:
                change_analysis = {
                    'change_points': change_points,
                    'num_changes': len(change_points),
                    'avg_segment_length': len(data) / (len(change_points) + 1),
                    'change_frequency': len(change_points) / len(data)
                }

                # 计算每个变化点前后的趋势变化
                trend_changes = []
                for i, cp in enumerate(change_points):
                    if i == 0:
                        prev_segment = data.iloc[:cp]
                    else:
                        prev_segment = data.iloc[change_points[i-1]:cp]

                    if i == len(change_points) - 1:
                        next_segment = data.iloc[cp:]
                    else:
                        next_segment = data.iloc[cp:change_points[i+1]]

                    if len(prev_segment) >= 5 and len(next_segment) >= 5:
                        # 计算前后段的斜率
                        prev_slope, _, _, _, _ = stats.linregress(np.arange(len(prev_segment)), prev_segment.values)
                        next_slope, _, _, _, _ = stats.linregress(np.arange(len(next_segment)), next_segment.values)

                        trend_change = next_slope - prev_slope
                        trend_changes.append(float(trend_change))

                if trend_changes:
                    change_analysis['avg_trend_change'] = float(np.mean(trend_changes))
                    change_analysis['trend_changes'] = trend_changes

                return change_analysis
            else:
                return {
                    'change_points': [],
                    'num_changes': 0,
                    'message': 'No significant trend changes detected'
                }

        except Exception as e:
            logger.warning(f"Trend change detection failed: {e}")
            return {'error': str(e)}

    def _classify_trend(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """分类趋势"""
        try:
            classification = {}

            # 基于线性趋势的方向分类
            if 'linear_trend' in results and 'direction' in results['linear_trend']:
                classification['direction'] = results['linear_trend']['direction']
                classification['is_significant'] = results['linear_trend'].get('is_significant', False)

            # 基于趋势强度的分类
            if 'trend_strength' in results and 'overall_strength' in results['trend_strength']:
                strength = results['trend_strength']['overall_strength']
                if strength > 0.7:
                    classification['strength'] = 'strong'
                elif strength > 0.4:
                    classification['strength'] = 'moderate'
                elif strength > 0.2:
                    classification['strength'] = 'weak'
                else:
                    classification['strength'] = 'no_clear_trend'

            # 基于趋势变化的分类
            if 'trend_changes' in results and 'num_changes' in results['trend_changes']:
                num_changes = results['trend_changes']['num_changes']
                if num_changes == 0:
                    classification['stability'] = 'stable'
                elif num_changes <= 2:
                    classification['stability'] = 'few_changes'
                elif num_changes <= 5:
                    classification['stability'] = 'moderate_changes'
                else:
                    classification['stability'] = 'frequent_changes'

            # 综合趋势类型
            trend_type = []
            if classification.get('direction') == 'increasing':
                trend_type.append('uptrend')
            elif classification.get('direction') == 'decreasing':
                trend_type.append('downtrend')

            if classification.get('strength') == 'strong':
                trend_type.append('strong')
            elif classification.get('strength') == 'weak':
                trend_type.append('weak')

            if classification.get('stability') == 'stable':
                trend_type.append('stable')
            elif classification.get('stability') == 'frequent_changes':
                trend_type.append('volatile')

            classification['trend_type'] = '_'.join(trend_type) if trend_type else 'undefined'

            return classification

        except Exception as e:
            logger.warning(f"Trend classification failed: {e}")
            return {'error': str(e)}


class TimeSeriesPatternAnalyzer:
    """时间序列模式分析器主类"""

    def __init__(self, config: Optional[TimeSeriesConfig] = None):
        self.config = config or get_behavioral_config().time_series
        self.seasonal_detector = SeasonalPatternDetector(self.config)
        self.trend_analyzer = TrendAnalyzer(self.config)

    def analyze_patterns(self, data: pd.Series, symbol: str = "UNKNOWN") -> Dict[str, Any]:
        """
        综合时间序列模式分析

        Args:
            data: 时间序列数据
            symbol: 股票代码或数据标识

        Returns:
            综合分析结果
        """
        try:
            logger.info(f"Starting comprehensive time series analysis for {symbol}")

            analysis_results = {
                'symbol': symbol,
                'analysis_time': datetime.now().isoformat(),
                'data_points': len(data),
                'date_range': {
                    'start': str(data.index[0]),
                    'end': str(data.index[-1])
                }
            }

            # 季节性分析
            analysis_results['seasonal_analysis'] = self.seasonal_detector.detect_seasonality(data)

            # 趋势分析
            analysis_results['trend_analysis'] = self.trend_analyzer.analyze_trend(data)

            # 综合模式识别
            analysis_results['pattern_summary'] = self._generate_pattern_summary(analysis_results)

            # 香港市场特定模式
            analysis_results['hk_market_patterns'] = self._detect_hk_market_patterns(data)

            # 预测性分析
            analysis_results['predictive_patterns'] = self._identify_predictive_patterns(data)

            logger.info(f"Time series analysis completed for {symbol}")
            return analysis_results

        except Exception as e:
            logger.error(f"Error in comprehensive pattern analysis: {e}")
            return {'error': str(e), 'symbol': symbol}

    def _generate_pattern_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """生成模式摘要"""
        try:
            summary = {}

            # 季节性摘要
            seasonal_analysis = results.get('seasonal_analysis', {})
            if 'seasonal_pattern' in seasonal_analysis:
                seasonal_summary = seasonal_analysis['seasonal_pattern']
                summary['has_seasonality'] = seasonal_summary.get('has_seasonality', False)
                summary['seasonal_strength'] = seasonal_summary.get('strength', 'unknown')

            # 趋势摘要
            trend_analysis = results.get('trend_analysis', {})
            if 'trend_classification' in trend_analysis:
                trend_summary = trend_analysis['trend_classification']
                summary['trend_direction'] = trend_summary.get('direction', 'unknown')
                summary['trend_strength'] = trend_summary.get('strength', 'unknown')
                summary['trend_stability'] = trend_summary.get('stability', 'unknown')

            # 综合评估
            summary['overall_pattern_type'] = self._classify_overall_pattern(summary)
            summary['analysis_confidence'] = self._calculate_analysis_confidence(results)

            return summary

        except Exception as e:
            logger.warning(f"Pattern summary generation failed: {e}")
            return {'error': str(e)}

    def _classify_overall_pattern(self, summary: Dict[str, Any]) -> str:
        """分类整体模式类型"""
        try:
            has_seasonality = summary.get('has_seasonality', False)
            seasonal_strength = summary.get('seasonal_strength', 'weak')
            trend_direction = summary.get('trend_direction', 'unknown')
            trend_strength = summary.get('trend_strength', 'weak')

            pattern_parts = []

            # 季节性部分
            if has_seasonality and seasonal_strength in ['strong', 'moderate']:
                pattern_parts.append('seasonal')

            # 趋势部分
            if trend_direction != 'unknown' and trend_strength in ['strong', 'moderate']:
                if trend_direction == 'increasing':
                    pattern_parts.append('uptrend')
                elif trend_direction == 'decreasing':
                    pattern_parts.append('downtrend')
                elif trend_direction == 'flat':
                    pattern_parts.append('sideways')

            # 默认分类
            if not pattern_parts:
                return 'no_clear_pattern'

            return '_'.join(pattern_parts)

        except Exception as e:
            logger.warning(f"Overall pattern classification failed: {e}")
            return 'classification_failed'

    def _calculate_analysis_confidence(self, results: Dict[str, Any]) -> float:
        """计算分析置信度"""
        try:
            confidence_factors = []

            # 基于季节性分析的置信度
            seasonal_analysis = results.get('seasonal_analysis', {})
            if 'stl_decomposition' in seasonal_analysis and 'decomposition_quality' in seasonal_analysis['stl_decomposition']:
                quality = seasonal_analysis['stl_decomposition']['decomposition_quality']
                confidence_factors.append(quality)

            # 基于趋势分析的置信度
            trend_analysis = results.get('trend_analysis', {})
            if 'linear_trend' in trend_analysis and 'r_squared' in trend_analysis['linear_trend']:
                r_squared = trend_analysis['linear_trend']['r_squared']
                confidence_factors.append(r_squared)

            # 基于数据量的置信度
            data_points = results.get('data_points', 0)
            if data_points >= 252:  # 一年的交易数据
                confidence_factors.append(1.0)
            elif data_points >= 100:
                confidence_factors.append(0.8)
            elif data_points >= 50:
                confidence_factors.append(0.6)
            else:
                confidence_factors.append(0.3)

            # 计算平均置信度
            if confidence_factors:
                return float(np.mean(confidence_factors))
            else:
                return 0.5  # 默认置信度

        except Exception as e:
            logger.warning(f"Analysis confidence calculation failed: {e}")
            return 0.5

    def _detect_hk_market_patterns(self, data: pd.Series) -> Dict[str, Any]:
        """检测香港市场特定模式"""
        try:
            hk_patterns = {}

            # 检测交易时段模式（如果有日内数据）
            if isinstance(data.index, pd.DatetimeIndex):
                # 提取小时信息
                data_hourly = data.groupby(data.index.hour).mean()

                # 香港交易时段：9:30-12:00, 13:00-16:00
                morning_avg = data_hourly.loc[10:11].mean() if 10 in data_hourly.index and 11 in data_hourly.index else None
                afternoon_avg = data_hourly.loc[14:15].mean() if 14 in data_hourly.index and 15 in data_hourly.index else None

                if morning_avg is not None and afternoon_avg is not None:
                    hk_patterns['session_pattern'] = {
                        'morning_average': float(morning_avg),
                        'afternoon_average': float(afternoon_avg),
                        'session_ratio': float(afternoon_avg / morning_avg) if morning_avg != 0 else 1.0
                    }

                # 午休时间异常检测
                lunch_hour = data.index.hour.isin([12])
                if lunch_hour.any():
                    lunch_data = data[lunch_hour]
                    non_lunch_data = data[~lunch_hour]

                    if len(lunch_data) > 0 and len(non_lunch_data) > 0:
                        lunch_volatility = lunch_data.std()
                        normal_volatility = non_lunch_data.std()

                        hk_patterns['lunch_time_analysis'] = {
                            'lunch_volatility': float(lunch_volatility),
                            'normal_volatility': float(normal_volatility),
                            'volatility_ratio': float(lunch_volatility / normal_volatility) if normal_volatility > 0 else 1.0,
                            'is_abnormal_lunch_time': lunch_volatility > 2 * normal_volatility
                        }

            # 检测月底效应（香港市场常见）
            if isinstance(data.index, pd.DatetimeIndex):
                # 月初和月末的表现
                month_end = data.index.day >= 25
                month_start = data.index.day <= 5

                if month_end.any() and month_start.any():
                    month_end_returns = data.pct_change()[month_end].mean()
                    month_start_returns = data.pct_change()[month_start].mean()

                    hk_patterns['month_end_effect'] = {
                        'month_end_return': float(month_end_returns) if not np.isnan(month_end_returns) else 0.0,
                        'month_start_return': float(month_start_returns) if not np.isnan(month_start_returns) else 0.0,
                        'effect_strength': float(abs(month_end_returns - month_start_returns))
                    }

            return hk_patterns

        except Exception as e:
            logger.warning(f"HK market pattern detection failed: {e}")
            return {'error': str(e)}

    def _identify_predictive_patterns(self, data: pd.Series) -> Dict[str, Any]:
        """识别预测性模式"""
        try:
            predictive_patterns = {}

            # 自相关模式（可预测性指标）
            autocorr_values = []
            for lag in range(1, min(21, len(data) // 4)):
                autocorr = data.autocorr(lag=lag)
                if not np.isnan(autocorr):
                    autocorr_values.append(abs(autocorr))

            if autocorr_values:
                predictive_patterns['autocorr_predictability'] = {
                    'max_autocorr': float(max(autocorr_values)),
                    'avg_autocorr': float(np.mean(autocorr_values)),
                    'predictable_lags': [i+1 for i, ac in enumerate(autocorr_values) if ac > 0.3]
                }

            # 波动率聚集模式
            returns = data.pct_change().dropna()
            if len(returns) > 20:
                volatility = returns.rolling(window=20).std().dropna()
                if len(volatility) > 0:
                    # 检测波动率聚集
                    vol_autocorr = volatility.autocorr(lag=1)
                    predictive_patterns['volatility_clustering'] = {
                        'volatility_autocorr': float(vol_autocorr) if not np.isnan(vol_autocorr) else 0.0,
                        'has_clustering': abs(vol_autocorr) > 0.2 if not np.isnan(vol_autocorr) else False,
                        'avg_volatility': float(volatility.mean()),
                        'volatility_regime': 'high' if volatility.mean() > returns.std() else 'low'
                    }

            # 均值回归模式
            if len(data) >= 50:
                mean_price = data.rolling(window=50).mean()
                deviations = data - mean_price

                # 计算均值回归强度
                mean_reversion_strength = []
                window = 20

                for i in range(window, len(deviations)):
                    if abs(deviations.iloc[i]) > 0:
                        # 检查后续是否向均值回归
                        future_deviation = deviations.iloc[i+1:i+6]
                        if len(future_deviation) > 0:
                            # 如果偏离为正，后续是否减小；如果偏离为负，后续是否增大
                            reversion = np.sign(deviations.iloc[i]) * np.sign(future_deviation.mean())
                            mean_reversion_strength.append(1 if reversion < 0 else 0)

                if mean_reversion_strength:
                    predictive_patterns['mean_reversion'] = {
                        'reversion_probability': float(np.mean(mean_reversion_strength)),
                        'has_mean_reversion': np.mean(mean_reversion_strength) > 0.6,
                        'avg_deviation': float(deviations.abs().mean())
                    }

            return predictive_patterns

        except Exception as e:
            logger.warning(f"Predictive pattern identification failed: {e}")
            return {'error': str(e)}


if __name__ == "__main__":
    # 测试代码
    print("Testing Time Series Pattern Analyzer...")

    # 生成测试数据
    np.random.seed(42)
    dates = pd.date_range(start='2020-01-01', periods=500, freq='D')

    # 生成带有趋势和季节性的模拟数据
    trend = np.linspace(100, 200, 500)
    seasonal = 10 * np.sin(2 * np.pi * np.arange(500) / 25)  # 25天季节周期
    noise = np.random.normal(0, 5, 500)
    prices = trend + seasonal + noise

    test_data = pd.Series(prices, index=dates)

    # 创建分析器
    analyzer = TimeSeriesPatternAnalyzer()

    # 运行分析
    results = analyzer.analyze_patterns(test_data, "TEST_HK_STOCK")

    # 显示结果摘要
    print("\n=== Analysis Results Summary ===")
    if 'pattern_summary' in results:
        summary = results['pattern_summary']
        print(f"Overall Pattern: {summary.get('overall_pattern_type', 'unknown')}")
        print(f"Has Seasonality: {summary.get('has_seasonality', False)}")
        print(f"Trend Direction: {summary.get('trend_direction', 'unknown')}")
        print(f"Analysis Confidence: {summary.get('analysis_confidence', 0):.3f}")

    print("\n=== Seasonal Analysis ===")
    if 'seasonal_analysis' in results and 'seasonal_pattern' in results['seasonal_analysis']:
        seasonal = results['seasonal_analysis']['seasonal_pattern']
        print(f"Seasonal Strength: {seasonal.get('strength', 'unknown')}")
        print(f"Decomposition Quality: {seasonal.get('decomposition_quality', 'unknown')}")

    print("\n=== Trend Analysis ===")
    if 'trend_analysis' in results and 'trend_classification' in results['trend_analysis']:
        trend = results['trend_analysis']['trend_classification']
        print(f"Trend Strength: {trend.get('strength', 'unknown')}")
        print(f"Trend Stability: {trend.get('stability', 'unknown')}")
        print(f"Trend Type: {trend.get('trend_type', 'unknown')}")

    print("\n=== HK Market Patterns ===")
    hk_patterns = results.get('hk_market_patterns', {})
    if hk_patterns:
        print(f"Session Pattern: {'detected' if 'session_pattern' in hk_patterns else 'not detected'}")
        print(f"Lunch Time Analysis: {'available' if 'lunch_time_analysis' in hk_patterns else 'not available'}")
        print(f"Month End Effect: {'detected' if 'month_end_effect' in hk_patterns else 'not detected'}")

    print("\n✅ Time Series Pattern Analyzer test completed successfully!")