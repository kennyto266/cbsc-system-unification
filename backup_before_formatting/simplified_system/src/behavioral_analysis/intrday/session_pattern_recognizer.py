#!/usr/bin/env python3
"""
第4阶段 Task 20: 盘中模式识别器
Phase 4 Task 20: Intraday Pattern Recognition

香港交易时段模式识别，专门针对9:30-16:00 HKT交易时间分析
Hong Kong trading session pattern recognition, specifically for 9:30-16:00 HKT analysis
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any, Union
from datetime import datetime, time, timedelta
import warnings
warnings.filterwarnings('ignore')

# Statistical and pattern recognition libraries
from scipy import stats
from scipy.signal import find_peaks, find_cwt
from scipy.spatial.distance import euclidean, cosine
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score

# Time series specific
from statsmodels.tsa.stattools import acf, pacf
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf

# Pattern matching
from tslearn.metrics import dtw
from tslearn.clustering import TimeSeriesKMeans
import ruptures as rpt

# Visualization
import matplotlib.pyplot as plt
import seaborn as sns

# Logging
import logging
logger = logging.getLogger(__name__)

from ..core.behavioral_config import get_behavioral_config, IntradayPatternConfig, TradingSession


class TradingSessionAnalyzer:
    """交易时段分析器"""

    def __init__(self, config: Optional[IntradayPatternConfig] = None):
        self.config = config or get_behavioral_config().intraday_pattern
        self.trading_hours = {
            TradingSession.PRE_MARKET: (time(9, 0), time(9, 30)),
            TradingSession.MORNING_SESSION: (time(9, 30), time(12, 0)),
            TradingSession.LUNCH_BREAK: (time(12, 0), time(13, 0)),
            TradingSession.AFTERNOON_SESSION: (time(13, 0), time(16, 0)),
            TradingSession.AFTER_MARKET: (time(16, 0), time(17, 0))
        }

    def analyze_trading_sessions(self, data: pd.Series) -> Dict[str, Any]:
        """
        分析不同交易时段的模式

        Args:
            data: 带时间索引的价格数据

        Returns:
            交易时段分析结果
        """
        try:
            results = {}

            # 确保数据有时间索引
            if not isinstance(data.index, pd.DatetimeIndex):
                logger.error("Data must have DatetimeIndex for session analysis")
                return {'error': 'Data must have DatetimeIndex'}

            # 分析各交易时段
            for session, (start_time, end_time) in self.trading_hours.items():
                session_data = self._extract_session_data(data, start_time, end_time)
                if not session_data.empty:
                    results[session.value] = self._analyze_session(session_data, session.value)

            # 比较不同时段
            results['session_comparison'] = self._compare_sessions(results)

            # 时段间转移分析
            results['session_transitions'] = self._analyze_session_transitions(data)

            logger.info(f"Trading session analysis completed for {len(data)} data points")
            return results

        except Exception as e:
            logger.error(f"Error in trading session analysis: {e}")
            return {'error': str(e)}

    def _extract_session_data(self, data: pd.Series, start_time: time, end_time: time) -> pd.Series:
        """提取特定时段的数据"""
        try:
            # 筛选时间范围内的数据
            time_mask = (data.index.time >= start_time) & (data.index.time < end_time)
            return data[time_mask]
        except Exception as e:
            logger.warning(f"Error extracting session data: {e}")
            return pd.Series()

    def _analyze_session(self, session_data: pd.Series, session_name: str) -> Dict[str, Any]:
        """分析单个交易时段"""
        try:
            analysis = {
                'data_points': len(session_data),
                'time_range': {
                    'start': str(session_data.index[0]),
                    'end': str(session_data.index[-1])
                }
            }

            # 基础统计
            analysis['statistics'] = {
                'mean_price': float(session_data.mean()),
                'std_price': float(session_data.std()),
                'min_price': float(session_data.min()),
                'max_price': float(session_data.max()),
                'price_range': float(session_data.max() - session_data.min())
            }

            # 价格变动分析
            if len(session_data) > 1:
                returns = session_data.pct_change().dropna()
                if len(returns) > 0:
                    analysis['returns'] = {
                        'mean_return': float(returns.mean()),
                        'std_return': float(returns.std()),
                        'total_return': float((session_data.iloc[-1] / session_data.iloc[0]) - 1),
                        'volatility': float(returns.std() * np.sqrt(252))  # 年化波动率
                    }

            # 成交量模式（如果有成交量数据）
            # 这里假设只有价格数据，实际应用中可以扩展

            # 时段特定的模式
            if session_name == TradingSession.MORNING_SESSION.value:
                analysis['morning_patterns'] = self._analyze_morning_patterns(session_data)
            elif session_name == TradingSession.AFTERNOON_SESSION.value:
                analysis['afternoon_patterns'] = self._analyze_afternoon_patterns(session_data)
            elif session_name == TradingSession.LUNCH_BREAK.value:
                analysis['lunch_patterns'] = self._analyze_lunch_patterns(session_data)

            return analysis

        except Exception as e:
            logger.warning(f"Error analyzing session {session_name}: {e}")
            return {'error': str(e), 'session': session_name}

    def _analyze_morning_patterns(self, data: pd.Series) -> Dict[str, Any]:
        """分析早盘特定模式"""
        try:
            patterns = {}

            # 开盘冲击分析
            if len(data) >= 10:
                open_price = data.iloc[0]
                first_10min_avg = data.iloc[:10].mean()
                patterns['opening_impact'] = {
                    'open_price': float(open_price),
                    'first_10min_avg': float(first_10min_avg),
                    'opening_movement': float((first_10min_avg / open_price) - 1)
                }

            # 早盘趋势强度
            if len(data) >= 30:
                x = np.arange(len(data))
                slope, _, r_value, _, _ = stats.linregress(x, data.values)
                patterns['morning_trend'] = {
                    'slope': float(slope),
                    'r_squared': float(r_value ** 2),
                    'direction': 'up' if slope > 0 else 'down' if slope < 0 else 'flat'
                }

            # 早盘波动率模式
            if len(data) >= 20:
                rolling_vol = data.pct_change().rolling(window=10).std()
                patterns['volatility_pattern'] = {
                    'early_volatility': float(rolling_vol.iloc[:10].mean()),
                    'late_volatility': float(rolling_vol.iloc[-10:].mean()),
                    'volatility_trend': 'increasing' if rolling_vol.iloc[-10:].mean() > rolling_vol.iloc[:10].mean() else 'decreasing'
                }

            return patterns

        except Exception as e:
            logger.warning(f"Error in morning pattern analysis: {e}")
            return {'error': str(e)}

    def _analyze_afternoon_patterns(self, data: pd.Series) -> Dict[str, Any]:
        """分析午盘特定模式"""
        try:
            patterns = {}

            # 午后开盘冲击
            if len(data) >= 10:
                lunch_end_price = data.iloc[0]  # 午休后第一笔交易
                first_10min_avg = data.iloc[:10].mean()
                patterns['post_lunch_impact'] = {
                    'lunch_end_price': float(lunch_end_price),
                    'first_10min_avg': float(first_10min_avg),
                    'post_lunch_movement': float((first_10min_avg / lunch_end_price) - 1)
                }

            # 收盘前模式
            if len(data) >= 30:
                last_30min = data.iloc[-30:]
                if len(last_30min) > 1:
                    close_price = data.iloc[-1]
                    last_30min_avg = last_30min.mean()
                    patterns['closing_patterns'] = {
                        'close_price': float(close_price),
                        'last_30min_avg': float(last_30min_avg),
                        'closing_rally': float((close_price / last_30min_avg) - 1)
                    }

            # 午后趋势持续性
            if len(data) >= 20:
                returns = data.pct_change().dropna()
                positive_periods = (returns > 0).sum()
                total_periods = len(returns)
                patterns['afternoon_consistency'] = {
                    'positive_period_ratio': float(positive_periods / total_periods),
                    'trend_consistency': 'consistent' if positive_periods / total_periods > 0.6 else 'mixed'
                }

            return patterns

        except Exception as e:
            logger.warning(f"Error in afternoon pattern analysis: {e}")
            return {'error': str(e)}

    def _analyze_lunch_patterns(self, data: pd.Series) -> Dict[str, Any]:
        """分析午休时间模式"""
        try:
            patterns = {}

            # 午休时间通常交易量较少，但可能有异常活动
            if len(data) > 1:
                returns = data.pct_change().dropna()
                volatility = returns.std() if len(returns) > 0 else 0

                patterns['lunch_activity'] = {
                    'volatility': float(volatility),
                    'is_abnormal_activity': volatility > 0.02,  # 2%以上波动视为异常
                    'price_stability': 'stable' if volatility < 0.005 else 'unstable'
                }

            # 午休时间价格偏离度
            if len(data) >= 5:
                lunch_avg = data.mean()
                patterns['price_deviation'] = {
                    'average_price': float(lunch_avg),
                    'price_range': float(data.max() - data.min()),
                    'relative_volatility': float((data.max() - data.min()) / lunch_avg) if lunch_avg != 0 else 0
                }

            return patterns

        except Exception as e:
            logger.warning(f"Error in lunch pattern analysis: {e}")
            return {'error': str(e)}

    def _compare_sessions(self, session_results: Dict[str, Any]) -> Dict[str, Any]:
        """比较不同交易时段的表现"""
        try:
            comparison = {}

            # 提取各时段的关键指标
            session_metrics = {}
            for session, data in session_results.items():
                if isinstance(data, dict) and 'statistics' in data:
                    stats = data['statistics']
                    session_metrics[session] = {
                        'avg_price': stats.get('mean_price', 0),
                        'price_range': stats.get('price_range', 0),
                        'volatility': data.get('returns', {}).get('volatility', 0)
                    }

            if len(session_metrics) >= 2:
                # 比较价格水平
                avg_prices = [m['avg_price'] for m in session_metrics.values()]
                comparison['price_level_comparison'] = {
                    'highest_avg_session': max(session_metrics.keys(), key=lambda k: session_metrics[k]['avg_price']),
                    'lowest_avg_session': min(session_metrics.keys(), key=lambda k: session_metrics[k]['avg_price']),
                    'price_range_span': float(max(avg_prices) - min(avg_prices))
                }

                # 比较波动率
                volatilities = {k: v['volatility'] for k, v in session_metrics.items() if v['volatility'] > 0}
                if volatilities:
                    comparison['volatility_comparison'] = {
                        'most_volatile_session': max(volatilities.keys(), key=lambda k: volatilities[k]),
                        'least_volatile_session': min(volatilities.keys(), key=lambda k: volatilities[k]),
                        'volatility_ratio': float(max(volatilities.values()) / min(volatilities.values()))
                    }

            return comparison

        except Exception as e:
            logger.warning(f"Error in session comparison: {e}")
            return {'error': str(e)}

    def _analyze_session_transitions(self, data: pd.Series) -> Dict[str, Any]:
        """分析交易时段间的转移模式"""
        try:
            transitions = {}

            # 找到关键的转移时间点
            transition_times = [
                (time(9, 30), "market_open"),
                (time(12, 0), "lunch_start"),
                (time(13, 0), "lunch_end"),
                (time(16, 0), "market_close")
            ]

            for transition_time, transition_name in transition_times:
                # 找到转移时间前后的数据点
                before_mask = data.index.time < transition_time
                after_mask = data.index.time >= transition_time

                before_data = data[before_mask]
                after_data = data[after_mask]

                if len(before_data) > 0 and len(after_data) > 0:
                    before_price = before_data.iloc[-1]
                    after_price = after_data.iloc[0]

                    transitions[transition_name] = {
                        'before_price': float(before_price),
                        'after_price': float(after_price),
                        'price_gap': float((after_price / before_price) - 1),
                        'gap_significance': abs((after_price / before_price) - 1) > 0.005  # 0.5%以上认为显著
                    }

            return transitions

        except Exception as e:
            logger.warning(f"Error in session transition analysis: {e}")
            return {'error': str(e)}


class VolatilityPatternRecognizer:
    """波动率模式识别器"""

    def __init__(self, config: Optional[IntradayPatternConfig] = None):
        self.config = config or get_behavioral_config().intraday_pattern

    def recognize_volatility_patterns(self, data: pd.Series) -> Dict[str, Any]:
        """
        识别波动率模式

        Args:
            data: 价格数据

        Returns:
            波动率模式分析结果
        """
        try:
            results = {}

            # 计算收益率
            returns = data.pct_change().dropna()
            if len(returns) == 0:
                return {'error': 'Insufficient data for volatility analysis'}

            # 多时间窗口波动率分析
            results['multi_timeframe_volatility'] = self._analyze_multi_timeframe_volatility(returns)

            # 波动率聚集检测
            results['volatility_clustering'] = self._detect_volatility_clustering(returns)

            # 波动率模式识别
            results['volatility_patterns'] = self._identify_volatility_patterns(returns)

            # 极端波动事件检测
            results['extreme_events'] = self._detect_extreme_volatility_events(returns)

            logger.info(f"Volatility pattern recognition completed for {len(data)} data points")
            return results

        except Exception as e:
            logger.error(f"Error in volatility pattern recognition: {e}")
            return {'error': str(e)}

    def _analyze_multi_timeframe_volatility(self, returns: pd.Series) -> Dict[str, Any]:
        """多时间框架波动率分析"""
        try:
            volatility_analysis = {}

            # 不同时间窗口的波动率
            windows = [
                (self.config.vol_short_window, 'short_term'),
                (self.config.vol_medium_window, 'medium_term'),
                (self.config.vol_long_window, 'long_term')
            ]

            for window, label in windows:
                if len(returns) >= window:
                    rolling_vol = returns.rolling(window=window).std().dropna()
                    if len(rolling_vol) > 0:
                        volatility_analysis[label] = {
                            'window': window,
                            'current_volatility': float(rolling_vol.iloc[-1]),
                            'avg_volatility': float(rolling_vol.mean()),
                            'volatility_trend': self._calculate_volatility_trend(rolling_vol),
                            'volatility_range': {
                                'min': float(rolling_vol.min()),
                                'max': float(rolling_vol.max()),
                                'range_ratio': float(rolling_vol.max() / rolling_vol.min()) if rolling_vol.min() > 0 else float('inf')
                            }
                        }

            # 波动率期限结构
            if len(volatility_analysis) >= 2:
                short_vol = volatility_analysis.get('short_term', {}).get('current_volatility', 0)
                long_vol = volatility_analysis.get('long_term', {}).get('current_volatility', 0)

                if long_vol > 0:
                    volatility_analysis['term_structure'] = {
                        'volatility_ratio': float(short_vol / long_vol),
                        'structure_type': 'contango' if short_vol > long_vol else 'backwardation',
                        'curve_steepness': float(abs(short_vol - long_vol) / long_vol)
                    }

            return volatility_analysis

        except Exception as e:
            logger.warning(f"Error in multi-timeframe volatility analysis: {e}")
            return {'error': str(e)}

    def _calculate_volatility_trend(self, volatility_series: pd.Series) -> str:
        """计算波动率趋势"""
        try:
            if len(volatility_series) < 10:
                return 'insufficient_data'

            # 计算线性趋势
            x = np.arange(len(volatility_series))
            slope, _, r_value, _, _ = stats.linregress(x, volatility_series.values)

            if abs(slope) < 1e-6:
                return 'stable'
            elif r_value ** 2 > 0.3:  # 趋势显著
                return 'increasing' if slope > 0 else 'decreasing'
            else:
                return 'no_clear_trend'

        except Exception as e:
            logger.warning(f"Error calculating volatility trend: {e}")
            return 'error'

    def _detect_volatility_clustering(self, returns: pd.Series) -> Dict[str, Any]:
        """检测波动率聚集"""
        try:
            clustering_analysis = {}

            # 计算绝对收益率
            abs_returns = abs(returns)

            # 计算不同滞后的自相关
            lags = [1, 5, 10, 20]
            autocorrelations = {}

            for lag in lags:
                if len(abs_returns) > lag:
                    autocorr = abs_returns.autocorr(lag=lag)
                    if not np.isnan(autocorr):
                        autocorrelations[f'lag_{lag}'] = float(autocorr)

            clustering_analysis['autocorrelations'] = autocorrelations

            # 评估聚集强度
            if autocorrelations:
                avg_autocorr = np.mean(list(autocorrelations.values()))
                clustering_analysis['clustering_strength'] = float(avg_autocorr)
                clustering_analysis['has_clustering'] = avg_autocorr > 0.2

                # 聚集类型
                if avg_autocorr > 0.4:
                    clustering_analysis['clustering_type'] = 'strong'
                elif avg_autocorr > 0.2:
                    clustering_analysis['clustering_type'] = 'moderate'
                else:
                    clustering_analysis['clustering_type'] = 'weak'

            # Engle's ARCH检验（波动率聚集的统计检验）
            try:
                from statsmodels.stats.diagnostic import het_arch
                arch_stat, arch_pvalue, _, _ = het_arch(returns, nlags=10)
                clustering_analysis['arch_test'] = {
                    'statistic': float(arch_stat),
                    'p_value': float(arch_pvalue),
                    'has_arch_effects': arch_pvalue < 0.05
                }
            except:
                clustering_analysis['arch_test'] = 'failed'

            return clustering_analysis

        except Exception as e:
            logger.warning(f"Error in volatility clustering detection: {e}")
            return {'error': str(e)}

    def _identify_volatility_patterns(self, returns: pd.Series) -> Dict[str, Any]:
        """识别波动率模式"""
        try:
            patterns = {}

            # 计算滚动波动率
            window = min(20, len(returns) // 4)
            rolling_vol = returns.rolling(window=window).std().dropna()

            if len(rolling_vol) == 0:
                return {'error': 'Insufficient data for pattern identification'}

            # 检测波动率峰值
            peaks, peak_properties = find_peaks(rolling_vol, height=rolling_vol.quantile(0.9), distance=5)
            if len(peaks) > 0:
                patterns['volatility_spikes'] = {
                    'spike_indices': peaks.tolist(),
                    'spike_values': [float(rolling_vol.iloc[i]) for i in peaks],
                    'num_spikes': len(peaks),
                    'avg_spike_height': float(np.mean([rolling_vol.iloc[i] for i in peaks]))
                }

            # 检测波动率低谷
            inverted_vol = -rolling_vol
            troughs, trough_properties = find_peaks(inverted_vol, height=-rolling_vol.quantile(0.1), distance=5)
            if len(troughs) > 0:
                patterns['volatility_troughs'] = {
                    'trough_indices': troughs.tolist(),
                    'trough_values': [float(rolling_vol.iloc[i]) for i in troughs],
                    'num_troughs': len(troughs),
                    'avg_trough_depth': float(np.mean([rolling_vol.iloc[i] for i in troughs]))
                }

            # 波动率周期性
            if len(rolling_vol) >= 40:
                # 使用FFT检测周期性
                fft_vol = np.fft.fft(rolling_vol.values)
                freq = np.fft.fftfreq(len(rolling_vol))
                psd = np.abs(fft_vol) ** 2

                # 找到主要频率（排除DC分量）
                positive_freq_idx = freq > 0
                if np.any(positive_freq_idx):
                    dominant_freq_idx = np.argmax(psd[positive_freq_idx])
                    dominant_period = int(1 / freq[positive_freq_idx][dominant_freq_idx]) if freq[positive_freq_idx][dominant_freq_idx] > 0 else None

                    if dominant_period and 1 < dominant_period < len(rolling_vol) // 2:
                        patterns['volatility_cyclicity'] = {
                            'dominant_period': dominant_period,
                            'is_cyclical': dominant_period > 5,
                            'cycle_strength': float(psd[positive_freq_idx][dominant_freq_idx])
                        }

            return patterns

        except Exception as e:
            logger.warning(f"Error in volatility pattern identification: {e}")
            return {'error': str(e)}

    def _detect_extreme_volatility_events(self, returns: pd.Series) -> Dict[str, Any]:
        """检测极端波动事件"""
        try:
            extreme_events = {}

            # 定义极端事件的阈值
            vol_threshold = returns.std() * 3  # 3倍标准差
            return_threshold = returns.quantile(0.99) - returns.quantile(0.01)

            # 检测极端收益率
            extreme_returns = returns[abs(returns) > vol_threshold]
            if len(extreme_returns) > 0:
                extreme_events['extreme_returns'] = {
                    'num_events': len(extreme_returns),
                    'events': [
                        {
                            'date': str(idx),
                            'return': float(ret),
                            'magnitude': abs(float(ret))
                        }
                        for idx, ret in extreme_returns.items()
                    ],
                    'avg_magnitude': float(abs(extreme_returns).mean()),
                    'max_magnitude': float(abs(extreme_returns).max())
                }

            # 检测波动率突变
            if len(returns) >= 10:
                rolling_vol = returns.rolling(window=10).std()
                vol_changes = rolling_vol.diff().abs()
                vol_threshold = vol_changes.quantile(0.95)

                extreme_vol_changes = vol_changes[vol_changes > vol_threshold]
                if len(extreme_vol_changes) > 0:
                    extreme_events['volatility_jumps'] = {
                        'num_events': len(extreme_vol_changes),
                        'events': [
                            {
                                'date': str(idx),
                                'vol_change': float(change)
                            }
                            for idx, change in extreme_vol_changes.items()
                        ],
                        'avg_change': float(extreme_vol_changes.mean()),
                        'max_change': float(extreme_vol_changes.max())
                    }

            # 事件聚集分析
            if extreme_events:
                total_events = 0
                if 'extreme_returns' in extreme_events:
                    total_events += extreme_events['extreme_returns']['num_events']
                if 'volatility_jumps' in extreme_events:
                    total_events += extreme_events['volatility_jumps']['num_events']

                extreme_events['summary'] = {
                    'total_extreme_events': total_events,
                    'event_frequency': float(total_events / len(returns)),
                    'is_high_frequency': total_events / len(returns) > 0.05  # 5%以上认为高频
                }

            return extreme_events

        except Exception as e:
            logger.warning(f"Error in extreme volatility event detection: {e}")
            return {'error': str(e)}


class IntradayPatternRecognizer:
    """盘中模式识别器主类"""

    def __init__(self, config: Optional[IntradayPatternConfig] = None):
        self.config = config or get_behavioral_config().intraday_pattern
        self.session_analyzer = TradingSessionAnalyzer(self.config)
        self.volatility_analyzer = VolatilityPatternRecognizer(self.config)
        self.scaler = StandardScaler()

    def recognize_intraday_patterns(self, data: pd.Series, symbol: str = "UNKNOWN") -> Dict[str, Any]:
        """
        综合盘中模式识别

        Args:
            data: 带时间索引的价格数据
            symbol: 股票代码

        Returns:
            综合模式识别结果
        """
        try:
            logger.info(f"Starting comprehensive intraday pattern recognition for {symbol}")

            analysis_results = {
                'symbol': symbol,
                'analysis_time': datetime.now().isoformat(),
                'data_points': len(data),
                'time_range': {
                    'start': str(data.index[0]),
                    'end': str(data.index[-1])
                }
            }

            # 交易时段分析
            analysis_results['trading_sessions'] = self.session_analyzer.analyze_trading_sessions(data)

            # 波动率模式识别
            analysis_results['volatility_patterns'] = self.volatility_analyzer.recognize_volatility_patterns(data)

            # 价格行为模式
            analysis_results['price_behavior_patterns'] = self._analyze_price_behavior_patterns(data)

            # 香港市场特定模式
            analysis_results['hk_specific_patterns'] = self._detect_hk_specific_patterns(data)

            # 模式综合分析
            analysis_results['pattern_summary'] = self._generate_pattern_summary(analysis_results)

            # 预测性信号
            analysis_results['predictive_signals'] = self._generate_predictive_signals(analysis_results)

            logger.info(f"Intraday pattern recognition completed for {symbol}")
            return analysis_results

        except Exception as e:
            logger.error(f"Error in comprehensive intraday pattern recognition: {e}")
            return {'error': str(e), 'symbol': symbol}

    def _analyze_price_behavior_patterns(self, data: pd.Series) -> Dict[str, Any]:
        """分析价格行为模式"""
        try:
            patterns = {}

            # 价格动量模式
            if len(data) >= 20:
                returns = data.pct_change().dropna()
                patterns['momentum_patterns'] = self._analyze_momentum_patterns(returns)

            # 价格反转模式
            if len(data) >= 30:
                patterns['reversal_patterns'] = self._analyze_reversal_patterns(data)

            # 价格突破模式
            if len(data) >= 40:
                patterns['breakout_patterns'] = self._analyze_breakout_patterns(data)

            # 价格区间模式
            if len(data) >= 50:
                patterns['range_patterns'] = self._analyze_range_patterns(data)

            return patterns

        except Exception as e:
            logger.warning(f"Error in price behavior pattern analysis: {e}")
            return {'error': str(e)}

    def _analyze_momentum_patterns(self, returns: pd.Series) -> Dict[str, Any]:
        """分析动量模式"""
        try:
            momentum_analysis = {}

            # 短期动量
            short_ma = returns.rolling(window=self.config.short_window).mean()
            long_ma = returns.rolling(window=self.config.medium_window).mean()

            if len(short_ma.dropna()) > 0 and len(long_ma.dropna()) > 0:
                momentum_analysis['short_term_momentum'] = {
                    'current_short_momentum': float(short_ma.iloc[-1]),
                    'current_long_momentum': float(long_ma.iloc[-1]),
                    'momentum_signal': 'bullish' if short_ma.iloc[-1] > long_ma.iloc[-1] else 'bearish'
                }

            # 动量持续性
            momentum_periods = (returns > 0).astype(int)
            if len(momentum_periods) >= 10:
                consecutive_periods = []
                current_streak = 0

                for i in range(len(momentum_periods)):
                    if i == 0:
                        current_streak = 1
                    elif momentum_periods.iloc[i] == momentum_periods.iloc[i-1]:
                        current_streak += 1
                    else:
                        consecutive_periods.append(current_streak)
                        current_streak = 1

                if current_streak > 0:
                    consecutive_periods.append(current_streak)

                if consecutive_periods:
                    momentum_analysis['momentum_persistence'] = {
                        'avg_streak_length': float(np.mean(consecutive_periods)),
                        'max_streak_length': float(max(consecutive_periods)),
                        'is_persistent': np.mean(consecutive_periods) > 3
                    }

            return momentum_analysis

        except Exception as e:
            logger.warning(f"Error in momentum pattern analysis: {e}")
            return {'error': str(e)}

    def _analyze_reversal_patterns(self, data: pd.Series) -> Dict[str, Any]:
        """分析反转模式"""
        try:
            reversal_analysis = {}

            # 局部极值检测
            if len(data) >= 20:
                # 寻找局部峰值和谷值
                peaks, _ = find_peaks(data, distance=5)
                troughs, _ = find_peaks(-data, distance=5)

                if len(peaks) > 0 and len(troughs) > 0:
                    reversal_analysis['extreme_points'] = {
                        'peaks': [int(p) for p in peaks],
                        'troughs': [int(t) for t in troughs],
                        'num_reversals': len(peaks) + len(troughs)
                    }

                    # 反转强度分析
                    peak_values = [data.iloc[p] for p in peaks]
                    trough_values = [data.iloc[t] for t in troughs]

                    if peak_values and trough_values:
                        peak_volatility = np.std(peak_values)
                        trough_volatility = np.std(trough_values)

                        reversal_analysis['reversal_strength'] = {
                            'peak_volatility': float(peak_volatility),
                            'trough_volatility': float(trough_volatility),
                            'avg_volatility': float((peak_volatility + trough_volatility) / 2)
                        }

            # RSI反转信号（简化版）
            if len(data) >= 14:
                # 计算价格变化
                delta = data.diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()

                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))

                if len(rsi.dropna()) > 0:
                    current_rsi = rsi.dropna().iloc[-1]
                    reversal_analysis['rsi_signals'] = {
                        'current_rsi': float(current_rsi),
                        'overbought_signal': current_rsi > 70,
                        'oversold_signal': current_rsi < 30,
                        'reversal_likelihood': 'high' if current_rsi > 80 or current_rsi < 20 else 'medium' if current_rsi > 70 or current_rsi < 30 else 'low'
                    }

            return reversal_analysis

        except Exception as e:
            logger.warning(f"Error in reversal pattern analysis: {e}")
            return {'error': str(e)}

    def _analyze_breakout_patterns(self, data: pd.Series) -> Dict[str, Any]:
        """分析突破模式"""
        try:
            breakout_analysis = {}

            # 支撑阻力位
            if len(data) >= 50:
                # 使用滚动最大最小值确定支撑阻力
                resistance = data.rolling(window=20).max()
                support = data.rolling(window=20).min()

                current_price = data.iloc[-1]
                current_resistance = resistance.iloc[-1]
                current_support = support.iloc[-1]

                breakout_analysis['support_resistance'] = {
                    'current_price': float(current_price),
                    'resistance_level': float(current_resistance),
                    'support_level': float(current_support),
                    'price_position': 'near_resistance' if current_price > current_resistance * 0.98 else 'near_support' if current_price < current_support * 1.02 else 'middle'
                }

                # 突破信号
                if len(data) >= 20:
                    recent_high = data.iloc[-20:].max()
                    recent_low = data.iloc[-20:].min()

                    breakout_analysis['breakout_signals'] = {
                        'resistance_breakout': current_price > recent_high * 1.02,
                        'support_breakdown': current_price < recent_low * 0.98,
                        'breakout_strength': float((current_price - recent_high) / recent_high) if current_price > recent_high else float((recent_low - current_price) / recent_low) if current_price < recent_low else 0
                    }

            # 波动率突破
            if len(data) >= 30:
                returns = data.pct_change().dropna()
                volatility = returns.rolling(window=20).std()
                avg_volatility = volatility.mean()

                current_volatility = volatility.iloc[-1]
                breakout_analysis['volatility_breakout'] = {
                    'current_volatility': float(current_volatility),
                    'avg_volatility': float(avg_volatility),
                    'volatility_expansion': current_volatility > avg_volatility * 1.5,
                    'expansion_factor': float(current_volatility / avg_volatility) if avg_volatility > 0 else 1
                }

            return breakout_analysis

        except Exception as e:
            logger.warning(f"Error in breakout pattern analysis: {e}")
            return {'error': str(e)}

    def _analyze_range_patterns(self, data: pd.Series) -> Dict[str, Any]:
        """分析区间模式"""
        try:
            range_analysis = {}

            if len(data) >= 50:
                # 价格区间统计
                price_range = data.max() - data.min()
                mean_price = data.mean()

                range_analysis['price_range'] = {
                    'range_width': float(price_range),
                    'range_width_pct': float(price_range / mean_price) if mean_price != 0 else 0,
                    'upper_bound': float(data.max()),
                    'lower_bound': float(data.min()),
                    'mid_point': float((data.max() + data.min()) / 2)
                }

                # 区间bound强度
                upper_touches = (data > data.max() * 0.98).sum()
                lower_touches = (data < data.min() * 1.02).sum()
                total_periods = len(data)

                range_analysis['boundary_strength'] = {
                    'upper_touches': int(upper_touches),
                    'lower_touches': int(lower_touches),
                    'upper_touch_frequency': float(upper_touches / total_periods),
                    'lower_touch_frequency': float(lower_touches / total_periods),
                    'is_strong_range': (upper_touches + lower_touches) / total_periods > 0.1
                }

                # 区内波动性
                if len(data) >= 20:
                    normalized_data = (data - data.min()) / (data.max() - data.min())
                    normalized_volatility = normalized_data.std()

                    range_analysis['intra_range_volatility'] = {
                        'normalized_volatility': float(normalized_volatility),
                        'is_tight_range': normalized_volatility < 0.1,
                        'is_wide_range': normalized_volatility > 0.3
                    }

            return range_analysis

        except Exception as e:
            logger.warning(f"Error in range pattern analysis: {e}")
            return {'error': str(e)}

    def _detect_hk_specific_patterns(self, data: pd.Series) -> Dict[str, Any]:
        """检测香港市场特定模式"""
        try:
            hk_patterns = {}

            # 午休时间异常活动
            if isinstance(data.index, pd.DatetimeIndex):
                lunch_data = data[(data.index.time >= time(12, 0)) & (data.index.time < time(13, 0))]
                non_lunch_data = data[(data.index.time >= time(9, 30)) & (data.index.time < time(16, 0)) &
                                     ~((data.index.time >= time(12, 0)) & (data.index.time < time(13, 0)))]

                if len(lunch_data) > 0 and len(non_lunch_data) > 0:
                    lunch_volatility = lunch_data.pct_change().std()
                    normal_volatility = non_lunch_data.pct_change().std()

                    hk_patterns['lunch_time_activity'] = {
                        'lunch_volatility': float(lunch_volatility) if not np.isnan(lunch_volatility) else 0,
                        'normal_volatility': float(normal_volatility) if not np.isnan(normal_volatility) else 0,
                        'activity_ratio': float(lunch_volatility / normal_volatility) if normal_volatility > 0 else 1,
                        'has_abnormal_lunch_activity': lunch_volatility > normal_volatility * 1.5
                    }

                # 收盘前集合竞价影响
                close_data = data[(data.index.time >= time(15, 30)) & (data.index.time < time(16, 0))]
                if len(close_data) > 0:
                    pre_close_data = data[(data.index.time >= time(15, 0)) & (data.index.time < time(15, 30))]
                    if len(pre_close_data) > 0:
                        close_return = close_data.pct_change().mean()
                        pre_close_return = pre_close_data.pct_change().mean()

                        hk_patterns['closing_auction_effect'] = {
                            'close_period_return': float(close_return) if not np.isnan(close_return) else 0,
                            'pre_close_return': float(pre_close_return) if not np.isnan(pre_close_return) else 0,
                            'auction_impact': float(abs(close_return - pre_close_return)) if not np.isnan(close_return) and not np.isnan(pre_close_return) else 0
                        }

            return hk_patterns

        except Exception as e:
            logger.warning(f"Error in HK specific pattern detection: {e}")
            return {'error': str(e)}

    def _generate_pattern_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """生成模式摘要"""
        try:
            summary = {}

            # 交易时段摘要
            if 'trading_sessions' in results and 'session_comparison' in results['trading_sessions']:
                comparison = results['trading_sessions']['session_comparison']
                summary['most_active_session'] = comparison.get('volatility_comparison', {}).get('most_volatile_session', 'unknown')

            # 波动率模式摘要
            if 'volatility_patterns' in results and 'volatility_clustering' in results['volatility_patterns']:
                clustering = results['volatility_patterns']['volatility_clustering']
                summary['volatility_regime'] = {
                    'has_clustering': clustering.get('has_clustering', False),
                    'clustering_strength': clustering.get('clustering_strength', 0),
                    'regime_type': clustering.get('clustering_type', 'unknown')
                }

            # 价格行为摘要
            if 'price_behavior_patterns' in results:
                price_patterns = results['price_behavior_patterns']

                # 动量信号
                if 'momentum_patterns' in price_patterns:
                    momentum = price_patterns['momentum_patterns']
                    summary['momentum_signal'] = momentum.get('short_term_momentum', {}).get('momentum_signal', 'neutral')

                # 反转信号
                if 'reversal_patterns' in price_patterns:
                    reversal = price_patterns['reversal_patterns']
                    rsi_signal = reversal.get('rsi_signals', {}).get('reversal_likelihood', 'low')
                    summary['reversal_likelihood'] = rsi_signal

                # 突破信号
                if 'breakout_patterns' in price_patterns:
                    breakout = price_patterns['breakout_patterns']
                    support_resistance = breakout.get('support_resistance', {})
                    summary['price_position'] = support_resistance.get('price_position', 'middle')

            # 香港市场特征
            if 'hk_specific_patterns' in results:
                hk_patterns = results['hk_specific_patterns']
                lunch_activity = hk_patterns.get('lunch_time_activity', {})
                summary['hk_market_features'] = {
                    'abnormal_lunch_activity': lunch_activity.get('has_abnormal_lunch_activity', False)
                }

            return summary

        except Exception as e:
            logger.warning(f"Error generating pattern summary: {e}")
            return {'error': str(e)}

    def _generate_predictive_signals(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """生成预测性信号"""
        try:
            signals = {
                'short_term_signals': [],
                'medium_term_signals': [],
                'risk_warnings': []
            }

            # 基于动量的信号
            pattern_summary = results.get('pattern_summary', {})
            momentum_signal = pattern_summary.get('momentum_signal', 'neutral')
            if momentum_signal in ['bullish', 'bearish']:
                signals['short_term_signals'].append({
                    'type': 'momentum',
                    'direction': momentum_signal,
                    'confidence': 0.7,
                    'time_horizon': '1-5 days'
                })

            # 基于反转的信号
            reversal_likelihood = pattern_summary.get('reversal_likelihood', 'low')
            if reversal_likelihood == 'high':
                signals['short_term_signals'].append({
                    'type': 'reversal',
                    'direction': 'potential_reversal',
                    'confidence': 0.8,
                    'time_horizon': '1-3 days'
                })

            # 基于突破的信号
            price_position = pattern_summary.get('price_position', 'middle')
            if price_position in ['near_resistance', 'near_support']:
                signals['medium_term_signals'].append({
                    'type': 'breakout',
                    'direction': 'potential_breakout' if price_position == 'near_resistance' else 'potential_breakdown',
                    'confidence': 0.6,
                    'time_horizon': '3-10 days'
                })

            # 基于波动率的风险警告
            volatility_regime = pattern_summary.get('volatility_regime', {})
            if volatility_regime.get('has_clustering', False) and volatility_regime.get('clustering_strength', 0) > 0.3:
                signals['risk_warnings'].append({
                    'type': 'volatility_clustering',
                    'severity': 'high' if volatility_regime.get('clustering_strength', 0) > 0.5 else 'medium',
                    'message': 'High volatility clustering detected, expect continued volatility'
                })

            # 香港市场特定警告
            hk_features = pattern_summary.get('hk_market_features', {})
            if hk_features.get('abnormal_lunch_activity', False):
                signals['risk_warnings'].append({
                    'type': 'abnormal_trading_pattern',
                    'severity': 'medium',
                    'message': 'Abnormal lunch time activity detected, monitor for unusual market conditions'
                })

            return signals

        except Exception as e:
            logger.warning(f"Error generating predictive signals: {e}")
            return {'error': str(e)}


if __name__ == "__main__":
    # 测试代码
    print("Testing Intraday Pattern Recognizer...")

    # 生成测试数据（模拟一天的交易数据）
    np.random.seed(42)
    dates = pd.date_range(start='2024-01-15 09:00:00', end='2024-01-15 16:30:00', freq='5min')

    # 模拟价格走势（包含不同时段的特征）
    base_price = 100
    price_changes = []

    for i, date in enumerate(dates):
        hour = date.hour
        minute = date.minute

        # 不同时段的波动模式
        if 9 <= hour < 9.5:  # 盘前
            change = np.random.normal(0, 0.1)
        elif 9.5 <= hour < 12:  # 早盘
            change = np.random.normal(0.02, 0.3)  # 轻微上涨趋势
        elif 12 <= hour < 13:  # 午休
            change = np.random.normal(0, 0.05)  # 低波动
        elif 13 <= hour < 16:  # 午盘
            change = np.random.normal(-0.01, 0.25)  # 轻微下跌趋势
        else:  # 盘后
            change = np.random.normal(0, 0.1)

        price_changes.append(change)

    # 生成价格序列
    prices = [base_price]
    for change in price_changes:
        new_price = prices[-1] * (1 + change / 100)
        prices.append(new_price)

    prices = prices[1:]  # 去掉初始价格
    test_data = pd.Series(prices, index=dates)

    # 创建识别器
    recognizer = IntradayPatternRecognizer()

    # 运行分析
    results = recognizer.recognize_intraday_patterns(test_data, "TEST_HK_STOCK")

    # 显示结果摘要
    print("\n=== Pattern Recognition Results Summary ===")
    if 'pattern_summary' in results:
        summary = results['pattern_summary']
        print(f"Most Active Session: {summary.get('most_active_session', 'unknown')}")
        print(f"Momentum Signal: {summary.get('momentum_signal', 'neutral')}")
        print(f"Reversal Likelihood: {summary.get('reversal_likelihood', 'low')}")
        print(f"Price Position: {summary.get('price_position', 'middle')}")

    print("\n=== Volatility Analysis ===")
    if 'volatility_patterns' in results and 'volatility_clustering' in results['volatility_patterns']:
        clustering = results['volatility_patterns']['volatility_clustering']
        print(f"Has Volatility Clustering: {clustering.get('has_clustering', False)}")
        print(f"Clustering Strength: {clustering.get('clustering_strength', 0):.3f}")
        print(f"Clustering Type: {clustering.get('clustering_type', 'unknown')}")

    print("\n=== Trading Sessions Analysis ===")
    if 'trading_sessions' in results and 'session_comparison' in results['trading_sessions']:
        comparison = results['trading_sessions']['session_comparison']
        print(f"Volatility Comparison: {'available' if 'volatility_comparison' in comparison else 'not available'}")
        print(f"Price Level Comparison: {'available' if 'price_level_comparison' in comparison else 'not available'}")

    print("\n=== HK Specific Patterns ===")
    hk_patterns = results.get('hk_specific_patterns', {})
    if hk_patterns:
        print(f"Lunch Time Activity: {'detected' if 'lunch_time_activity' in hk_patterns else 'not detected'}")
        print(f"Closing Auction Effect: {'detected' if 'closing_auction_effect' in hk_patterns else 'not detected'}")

    print("\n=== Predictive Signals ===")
    if 'predictive_signals' in results:
        signals = results['predictive_signals']
        print(f"Short Term Signals: {len(signals.get('short_term_signals', []))}")
        print(f"Medium Term Signals: {len(signals.get('medium_term_signals', []))}")
        print(f"Risk Warnings: {len(signals.get('risk_warnings', []))}")

        for warning in signals.get('risk_warnings', []):
            print(f"  - {warning.get('message', 'Unknown warning')}")

    print("\n✅ Intraday Pattern Recognizer test completed successfully!")