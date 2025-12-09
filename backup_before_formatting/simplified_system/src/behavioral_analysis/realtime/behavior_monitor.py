#!/usr/bin/env python3
"""
第4阶段 Task 25: 实时行为监控器
Phase 4 Task 25: Real-time Behavior Monitor

实时数据流监控、滑动窗口分析和早期预警系统
Real-time data stream monitoring with sliding window analysis and early warning system
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any, Union, Callable
from datetime import datetime, timedelta
import time
import threading
import queue
import warnings
warnings.filterwarnings('ignore')

# Real-time data processing
from collections import deque, defaultdict
from concurrent.futures import ThreadPoolExecutor
import asyncio

# Statistical analysis
from scipy import stats
from scipy.signal import savgol_filter

# Machine learning for online learning
from sklearn.linear_model import SGDClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import NearestNeighbors

# Alert system
import json
from pathlib import Path

# Visualization and monitoring
import matplotlib.pyplot as plt
import seaborn as sns

# Logging
import logging
logger = logging.getLogger(__name__)

from ..core.behavioral_config import get_behavioral_config, RealTimeMonitoringConfig, AnomalyType
from ..ml_anomaly.ml_anomaly_detector import MLAnomalyDetector, EnsembleAnomalyDetector


class SlidingWindowProcessor:
    """滑动窗口处理器"""

    def __init__(self, config: Optional[RealTimeMonitoringConfig] = None):
        self.config = config or get_behavioral_config().realtime_monitoring
        self.windows = {
            'short': deque(maxlen=self.config.short_window_size),
            'medium': deque(maxlen=self.config.medium_window_size),
            'long': deque(maxlen=self.config.long_window_size)
        }
        self.timestamps = {
            'short': deque(maxlen=self.config.short_window_size),
            'medium': deque(maxlen=self.config.medium_window_size),
            'long': deque(maxlen=self.config.long_window_size)
        }

    def add_data_point(self, value: float, timestamp: Optional[datetime] = None) -> None:
        """添加新数据点到所有滑动窗口"""
        if timestamp is None:
            timestamp = datetime.now()

        for window_type in self.windows:
            self.windows[window_type].append(value)
            self.timestamps[window_type].append(timestamp)

    def get_window_data(self, window_type: str) -> np.ndarray:
        """获取指定窗口的数据"""
        return np.array(self.windows[window_type])

    def get_window_timestamps(self, window_type: str) -> List[datetime]:
        """获取指定窗口的时间戳"""
        return list(self.timestamps[window_type])

    def get_statistics(self, window_type: str) -> Dict[str, float]:
        """计算窗口统计信息"""
        data = self.get_window_data(window_type)
        if len(data) == 0:
            return {}

        return {
            'mean': float(np.mean(data)),
            'std': float(np.std(data)),
            'min': float(np.min(data)),
            'max': float(np.max(data)),
            'median': float(np.median(data)),
            'skewness': float(stats.skew(data)),
            'kurtosis': float(stats.kurtosis(data)),
            'cv': float(np.std(data) / np.mean(data)) if np.mean(data) != 0 else 0
        }

    def detect_change_point(self, window_type: str) -> Dict[str, Any]:
        """检测变化点"""
        try:
            data = self.get_window_data(window_type)
            if len(data) < 20:
                return {'has_change_point': False, 'reason': 'insufficient_data'}

            # 使用简单的CUSUM方法检测变化点
            mean_value = np.mean(data)
            cumulative_sum = np.cumsum(data - mean_value)

            # 检测显著偏离
            threshold = 3 * np.std(cumulative_sum)
            max_deviation = np.max(np.abs(cumulative_sum))
            has_change = max_deviation > threshold

            if has_change:
                change_point_idx = np.argmax(np.abs(cumulative_sum))
                relative_position = change_point_idx / len(data)

                return {
                    'has_change_point': True,
                    'change_point_index': int(change_point_idx),
                    'relative_position': float(relative_position),
                    'deviation_magnitude': float(max_deviation),
                    'threshold': float(threshold)
                }
            else:
                return {
                    'has_change_point': False,
                    'max_deviation': float(max_deviation),
                    'threshold': float(threshold)
                }

        except Exception as e:
            logger.warning(f"Error in change point detection: {e}")
            return {'error': str(e)}

    def calculate_volatility_regime(self, window_type: str) -> Dict[str, Any]:
        """计算波动率状态"""
        try:
            data = self.get_window_data(window_type)
            if len(data) < 10:
                return {'regime': 'unknown', 'reason': 'insufficient_data'}

            # 计算收益率和波动率
            returns = np.diff(data) / data[:-1]
            returns = returns[~np.isnan(returns)]

            if len(returns) < 5:
                return {'regime': 'unknown', 'reason': 'insufficient_returns'}

            volatility = np.std(returns)
            mean_return = np.mean(returns)

            # 分类波动率状态
            if volatility < 0.01:
                regime = 'low_volatility'
            elif volatility < 0.03:
                regime = 'normal_volatility'
            else:
                regime = 'high_volatility'

            return {
                'regime': regime,
                'volatility': float(volatility),
                'mean_return': float(mean_return),
                'volatility_percentile': float(stats.percentileofscore([volatility], volatility))
            }

        except Exception as e:
            logger.warning(f"Error in volatility regime calculation: {e}")
            return {'error': str(e)}


class AdaptiveThresholdManager:
    """自适应阈值管理器"""

    def __init__(self, config: Optional[RealTimeMonitoringConfig] = None):
        self.config = config or get_behavioral_config().realtime_monitoring
        self.thresholds = {}
        self.learning_rate = self.config.learning_rate
        self.decay_factor = self.config.decay_factor
        self.baseline_statistics = {}
        self.alert_history = deque(maxlen=1000)

    def initialize_thresholds(self, baseline_data: Dict[str, np.ndarray]) -> None:
        """基于基线数据初始化阈值"""
        for metric_name, data in baseline_data.items():
            if len(data) > 0:
                self.baseline_statistics[metric_name] = {
                    'mean': float(np.mean(data)),
                    'std': float(np.std(data)),
                    'percentiles': {
                        '5': float(np.percentile(data, 5)),
                        '25': float(np.percentile(data, 25)),
                        '75': float(np.percentile(data, 75)),
                        '95': float(np.percentile(data, 95))
                    }
                }

                # 初始阈值设置为95%分位数
                self.thresholds[metric_name] = {
                    'warning': float(np.percentile(data, 90)),
                    'critical': float(np.percentile(data, 95)),
                    'last_updated': datetime.now()
                }

        logger.info(f"Initialized thresholds for {len(self.thresholds)} metrics")

    def update_thresholds(self, metric_name: str, new_value: float, is_anomaly: bool) -> None:
        """更新自适应阈值"""
        if metric_name not in self.thresholds:
            return

        current_thresholds = self.thresholds[metric_name]

        # 如果是异常，略微降低阈值（更敏感）
        # 如果是正常，略微提高阈值（更鲁棒）
        adjustment_factor = 1.0
        if is_anomaly:
            adjustment_factor = 1.0 - self.learning_rate * 0.1
        else:
            adjustment_factor = 1.0 + self.learning_rate * 0.05

        # 应用衰减因子
        current_thresholds['warning'] = (
            self.decay_factor * current_thresholds['warning'] +
            (1 - self.decay_factor) * current_thresholds['warning'] * adjustment_factor
        )

        current_thresholds['critical'] = (
            self.decay_factor * current_thresholds['critical'] +
            (1 - self.decay_factor) * current_thresholds['critical'] * adjustment_factor
        )

        current_thresholds['last_updated'] = datetime.now()

    def check_thresholds(self, metric_name: str, value: float) -> Dict[str, Any]:
        """检查值是否超过阈值"""
        if metric_name not in self.thresholds:
            return {'status': 'no_threshold', 'level': 'unknown'}

        thresholds = self.thresholds[metric_name]

        if value >= thresholds['critical']:
            status = 'critical'
            level = 'critical'
        elif value >= thresholds['warning']:
            status = 'warning'
            level = 'warning'
        else:
            status = 'normal'
            level = 'normal'

        return {
            'status': status,
            'level': level,
            'value': float(value),
            'warning_threshold': float(thresholds['warning']),
            'critical_threshold': float(thresholds['critical']),
            'distance_to_warning': float(value - thresholds['warning']),
            'distance_to_critical': float(value - thresholds['critical'])
        }

    def get_threshold_info(self, metric_name: str) -> Dict[str, Any]:
        """获取阈值信息"""
        if metric_name not in self.thresholds:
            return {'error': 'Threshold not found'}

        thresholds = self.thresholds[metric_name]
        baseline = self.baseline_statistics.get(metric_name, {})

        return {
            'current_thresholds': thresholds,
            'baseline_statistics': baseline,
            'threshold_adjustment_count': len(self.alert_history)
        }


class RealTimeBehaviorMonitor:
    """实时行为监控器主类"""

    def __init__(self,
                 config: Optional[RealTimeMonitoringConfig] = None,
                 anomaly_detector: Optional[MLAnomalyDetector] = None):
        self.config = config or get_behavioral_config().realtime_monitoring
        self.anomaly_detector = anomaly_detector

        # 核心组件
        self.window_processor = SlidingWindowProcessor(self.config)
        self.threshold_manager = AdaptiveThresholdManager(self.config)

        # 数据流管理
        self.data_buffer = queue.Queue(maxsize=self.config.buffer_size)
        self.is_running = False
        self.monitoring_thread = None

        # 告警系统
        self.alert_callbacks = []
        self.alert_history = deque(maxlen=1000)
        self.last_alert_time = {}

        # 在线学习模型
        self.online_models = {
            'trend_detector': SGDClassifier(loss='log_loss', random_state=42),
            'volatility_classifier': GaussianNB()
        }
        self.online_models_trained = False

        # 监控指标
        self.metrics = defaultdict(list)
        self.performance_stats = {
            'processed_samples': 0,
            'alerts_generated': 0,
            'average_processing_time': 0,
            'start_time': None
        }

        # 香港市场特定配置
        self.hk_trading_hours = {
            'morning_start': time(9, 30),
            'morning_end': time(12, 0),
            'afternoon_start': time(13, 0),
            'afternoon_end': time(16, 0)
        }

    def start_monitoring(self) -> None:
        """启动实时监控"""
        if self.is_running:
            logger.warning("Monitoring is already running")
            return

        self.is_running = True
        self.performance_stats['start_time'] = datetime.now()
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()

        logger.info("Real-time behavior monitoring started")

    def stop_monitoring(self) -> None:
        """停止实时监控"""
        self.is_running = False
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=5)

        logger.info("Real-time behavior monitoring stopped")

    def _monitoring_loop(self) -> None:
        """监控主循环"""
        logger.info("Monitoring loop started")

        while self.is_running:
            try:
                start_time = time.time()

                # 从缓冲区获取数据
                try:
                    data_point = self.data_buffer.get(timeout=1.0)
                except queue.Empty:
                    continue

                # 处理数据点
                self._process_data_point(data_point)

                # 更新性能统计
                processing_time = (time.time() - start_time) * 1000  # 转换为毫秒
                self._update_performance_stats(processing_time)

                # 检查处理时间限制
                if processing_time > self.config.max_processing_time_ms:
                    logger.warning(f"Processing time exceeded limit: {processing_time:.2f}ms")

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                continue

        logger.info("Monitoring loop stopped")

    def add_data_point(self, value: float, timestamp: Optional[datetime] = None, **metadata) -> None:
        """添加新的数据点"""
        if timestamp is None:
            timestamp = datetime.now()

        data_point = {
            'value': value,
            'timestamp': timestamp,
            'metadata': metadata
        }

        try:
            self.data_buffer.put_nowait(data_point)
        except queue.Full:
            logger.warning("Data buffer is full, dropping oldest data point")
            try:
                self.data_buffer.get_nowait()
                self.data_buffer.put_nowait(data_point)
            except queue.Empty:
                pass

    def _process_data_point(self, data_point: Dict[str, Any]) -> None:
        """处理单个数据点"""
        value = data_point['value']
        timestamp = data_point['timestamp']

        # 更新滑动窗口
        self.window_processor.add_data_point(value, timestamp)

        # 计算实时指标
        metrics = self._calculate_realtime_metrics()

        # 异常检测
        anomaly_result = self._detect_anomaly(data_point, metrics)

        # 阈值检查
        threshold_results = {}
        for metric_name, metric_value in metrics.items():
            if metric_name in self.threshold_manager.thresholds:
                threshold_result = self.threshold_manager.check_thresholds(metric_name, metric_value)
                threshold_results[metric_name] = threshold_result

        # 生成告警
        self._generate_alerts(data_point, metrics, anomaly_result, threshold_results)

        # 在线学习更新
        self._update_online_models(data_point, metrics, anomaly_result)

        # 记录指标
        for metric_name, metric_value in metrics.items():
            self.metrics[metric_name].append(metric_value)

    def _calculate_realtime_metrics(self) -> Dict[str, float]:
        """计算实时指标"""
        metrics = {}

        # 各窗口的统计指标
        for window_type in ['short', 'medium', 'long']:
            window_stats = self.window_processor.get_statistics(window_type)
            if window_stats:
                for stat_name, stat_value in window_stats.items():
                    metrics[f"{window_type}_{stat_name}"] = stat_value

        # 变化点检测
        for window_type in ['short', 'medium']:
            change_point = self.window_processor.detect_change_point(window_type)
            metrics[f"{window_type}_has_change_point"] = float(change_point.get('has_change_point', False))
            if change_point.get('has_change_point', False):
                metrics[f"{window_type}_change_magnitude"] = float(change_point.get('deviation_magnitude', 0))

        # 波动率状态
        for window_type in ['short', 'medium', 'long']:
            volatility_regime = self.window_processor.calculate_volatility_regime(window_type)
            metrics[f"{window_type}_volatility"] = float(volatility_regime.get('volatility', 0))

            regime = volatility_regime.get('regime', 'unknown')
            metrics[f"{window_type}_is_high_volatility"] = float(regime == 'high_volatility')
            metrics[f"{window_type}_is_low_volatility"] = float(regime == 'low_volatility')

        # 趋势强度
        if len(self.window_processor.get_window_data('medium')) >= 10:
            data = self.window_processor.get_window_data('medium')
            x = np.arange(len(data))
            slope, _, r_value, _, _ = stats.linregress(x, data)
            metrics['medium_trend_strength'] = float(abs(r_value))
            metrics['medium_trend_direction'] = float(slope)

        # 香港市场特定指标
        current_time = datetime.now().time()
        metrics['is_trading_hours'] = float(self._is_hk_trading_hours(current_time))
        metrics['is_lunch_time'] = float(self.hk_trading_hours['morning_end'] <= current_time < self.hk_trading_hours['afternoon_start'])

        return metrics

    def _detect_anomaly(self, data_point: Dict[str, Any], metrics: Dict[str, float]) -> Dict[str, Any]:
        """检测异常"""
        anomaly_result = {
            'is_anomaly': False,
            'anomaly_score': 0.0,
            'anomaly_type': None,
            'confidence': 0.0
        }

        try:
            # 如果有异常检测器，使用ML模型
            if self.anomaly_detector and self.anomaly_detector.ensemble.is_fitted:
                # 构建特征向量
                feature_vector = np.array([metrics.get(key, 0) for key in sorted(metrics.keys())]).reshape(1, -1)

                # 预测异常
                prediction = self.anomaly_detector.ensemble.predict(feature_vector)[0]
                probability = self.anomaly_detector.ensemble.predict_proba(feature_vector)[0, 1]
                decision_score = self.anomaly_detector.ensemble.decision_function(feature_vector)[0]

                anomaly_result.update({
                    'is_anomaly': bool(prediction),
                    'anomaly_score': float(decision_score),
                    'anomaly_probability': float(probability),
                    'confidence': float(abs(decision_score)),
                    'method': 'ml_ensemble'
                })

            else:
                # 使用简单的统计方法
                anomaly_result = self._statistical_anomaly_detection(data_point, metrics)

        except Exception as e:
            logger.warning(f"Error in anomaly detection: {e}")
            anomaly_result['error'] = str(e)

        return anomaly_result

    def _statistical_anomaly_detection(self, data_point: Dict[str, Any], metrics: Dict[str, float]) -> Dict[str, Any]:
        """统计异常检测方法"""
        anomaly_result = {
            'is_anomaly': False,
            'anomaly_score': 0.0,
            'anomaly_type': None,
            'confidence': 0.0,
            'method': 'statistical'
        }

        try:
            # Z-score异常检测
            short_mean = metrics.get('short_mean', 0)
            short_std = metrics.get('short_std', 0)
            current_value = data_point['value']

            if short_std > 0:
                z_score = abs((current_value - short_mean) / short_std)
                anomaly_result['z_score'] = float(z_score)

                if z_score > 3:  # 3-sigma规则
                    anomaly_result['is_anomaly'] = True
                    anomaly_result['anomaly_score'] = float(z_score)
                    anomaly_result['anomaly_type'] = 'statistical_outlier'
                    anomaly_result['confidence'] = min(1.0, (z_score - 3) / 2)

            # 变化点异常检测
            if metrics.get('short_has_change_point', 0):
                anomaly_result['is_anomaly'] = True
                anomaly_result['anomaly_type'] = 'change_point'
                anomaly_result['confidence'] = metrics.get('short_change_magnitude', 0) / 10

            # 波动率异常检测
            if metrics.get('short_is_high_volatility', 0):
                anomaly_result['is_anomaly'] = True
                anomaly_result['anomaly_type'] = 'volatility_spike'
                anomaly_result['confidence'] = 0.7

        except Exception as e:
            logger.warning(f"Error in statistical anomaly detection: {e}")
            anomaly_result['error'] = str(e)

        return anomaly_result

    def _generate_alerts(self, data_point: Dict[str, Any], metrics: Dict[str, float],
                        anomaly_result: Dict[str, Any], threshold_results: Dict[str, Dict[str, Any]]) -> None:
        """生成告警"""
        current_time = datetime.now()
        alerts = []

        # 异常告警
        if anomaly_result.get('is_anomaly', False):
            alert = {
                'type': 'anomaly',
                'severity': 'high' if anomaly_result.get('confidence', 0) > 0.8 else 'medium',
                'timestamp': current_time,
                'data_point': data_point,
                'anomaly_details': anomaly_result,
                'metrics': metrics
            }
            alerts.append(alert)

        # 阈值告警
        for metric_name, threshold_result in threshold_results.items():
            if threshold_result.get('level') in ['warning', 'critical']:
                alert = {
                    'type': 'threshold',
                    'severity': threshold_result['level'],
                    'timestamp': current_time,
                    'metric_name': metric_name,
                    'threshold_details': threshold_result,
                    'data_point': data_point,
                    'metrics': metrics
                }
                alerts.append(alert)

        # 检查告警冷却时间
        filtered_alerts = []
        for alert in alerts:
            alert_key = f"{alert['type']}_{alert.get('metric_name', 'unknown')}_{alert.get('severity', 'unknown')}"

            last_alert_time = self.last_alert_time.get(alert_key)
            if last_alert_time is None or (current_time - last_alert_time).total_seconds() > self.config.alert_cooldown:
                filtered_alerts.append(alert)
                self.last_alert_time[alert_key] = current_time

        # 发送告警
        for alert in filtered_alerts:
            self.alert_history.append(alert)
            self.performance_stats['alerts_generated'] += 1

            # 调用告警回调
            for callback in self.alert_callbacks:
                try:
                    callback(alert)
                except Exception as e:
                    logger.error(f"Error in alert callback: {e}")

            logger.warning(f"Alert generated: {alert['type']} - {alert.get('severity', 'unknown')}")

    def _update_online_models(self, data_point: Dict[str, Any], metrics: Dict[str, float],
                            anomaly_result: Dict[str, Any]) -> None:
        """更新在线学习模型"""
        try:
            if not self.online_models_trained:
                # 初始化在线模型（需要一些历史数据）
                if len(self.metrics['short_mean']) >= 50:
                    self._initialize_online_models()
                    self.online_models_trained = True
                return

            # 准备训练数据
            feature_vector = np.array([metrics.get(key, 0) for key in sorted(metrics.keys())])
            label = 1 if anomaly_result.get('is_anomaly', False) else 0

            # 更新趋势检测模型
            if 'medium_trend_direction' in metrics:
                trend_label = 1 if metrics['medium_trend_direction'] > 0 else 0
                self.online_models['trend_detector'].partial_fit(
                    feature_vector.reshape(1, -1),
                    np.array([trend_label]),
                    classes=[0, 1]
                )

            # 更新波动率分类模型
            if 'short_is_high_volatility' in metrics:
                vol_label = 1 if metrics['short_is_high_volatility'] > 0 else 0
                # GaussianNB需要特殊处理（不能partial_fit单个样本）
                if not hasattr(self, '_vol_training_data'):
                    self._vol_training_data = {'X': [], 'y': []}

                self._vol_training_data['X'].append(feature_vector)
                self._vol_training_data['y'].append(vol_label)

                # 定期重新训练
                if len(self._vol_training_data['X']) >= 100:
                    X_batch = np.array(self._vol_training_data['X'])
                    y_batch = np.array(self._vol_training_data['y'])
                    self.online_models['volatility_classifier'].fit(X_batch, y_batch)
                    self._vol_training_data = {'X': [], 'y': []}

        except Exception as e:
            logger.warning(f"Error updating online models: {e}")

    def _initialize_online_models(self) -> None:
        """初始化在线学习模型"""
        try:
            # 准备训练数据
            feature_vectors = []
            trend_labels = []

            # 使用历史数据初始化
            for i in range(len(self.metrics['short_mean'])):
                if i < len(self.metrics['short_mean']) - 1:
                    # 简单的趋势标签：如果下一个值大于当前值，则为上升趋势
                    current_trend = 1 if self.metrics['short_mean'][i+1] > self.metrics['short_mean'][i] else 0
                    feature_vectors.append([
                        self.metrics['short_mean'][i],
                        self.metrics['short_std'][i],
                        self.metrics['medium_mean'][i] if i < len(self.metrics['medium_mean']) else 0
                    ])
                    trend_labels.append(current_trend)

            if len(feature_vectors) > 10:
                X = np.array(feature_vectors)
                y = np.array(trend_labels)
                self.online_models['trend_detector'].partial_fit(X, y, classes=[0, 1])

            logger.info("Online models initialized successfully")

        except Exception as e:
            logger.warning(f"Error initializing online models: {e}")

    def _is_hk_trading_hours(self, current_time: time) -> bool:
        """检查是否在香港交易时间"""
        return ((self.hk_trading_hours['morning_start'] <= current_time < self.hk_trading_hours['morning_end']) or
                (self.hk_trading_hours['afternoon_start'] <= current_time < self.hk_trading_hours['afternoon_end']))

    def _update_performance_stats(self, processing_time: float) -> None:
        """更新性能统计"""
        self.performance_stats['processed_samples'] += 1

        # 更新平均处理时间
        total_samples = self.performance_stats['processed_samples']
        current_avg = self.performance_stats['average_processing_time']
        self.performance_stats['average_processing_time'] = (
            (current_avg * (total_samples - 1) + processing_time) / total_samples
        )

    def add_alert_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """添加告警回调函数"""
        self.alert_callbacks.append(callback)

    def initialize_from_baseline(self, baseline_data: pd.Series) -> None:
        """从基线数据初始化监控器"""
        try:
            # 计算基线指标
            baseline_metrics = {}

            # 滑动窗口统计
            for window_size in [self.config.short_window_size, self.config.medium_window_size, self.config.long_window_size]:
                if len(baseline_data) >= window_size:
                    window_data = baseline_data.rolling(window=window_size).mean().dropna()
                    baseline_metrics[f'rolling_mean_{window_size}'] = window_data.values

            # 收益率统计
            returns = baseline_data.pct_change().dropna()
            if len(returns) > 0:
                baseline_metrics['returns'] = returns.values

            # 初始化阈值管理器
            self.threshold_manager.initialize_thresholds(baseline_metrics)

            # 添加基线数据到窗口处理器
            for value in baseline_data.tail(self.config.long_window_size).values:
                self.window_processor.add_data_point(float(value))

            logger.info(f"Monitor initialized with {len(baseline_data)} baseline data points")

        except Exception as e:
            logger.error(f"Error initializing from baseline: {e}")
            raise

    def get_current_status(self) -> Dict[str, Any]:
        """获取当前监控状态"""
        current_time = datetime.now()

        status = {
            'monitoring_active': self.is_running,
            'current_time': current_time.isoformat(),
            'is_trading_hours': self._is_hk_trading_hours(current_time.time()),
            'buffer_size': self.data_buffer.qsize(),
            'performance_stats': self.performance_stats.copy(),
            'window_sizes': {
                'short': len(self.window_processor.windows['short']),
                'medium': len(self.window_processor.windows['medium']),
                'long': len(self.window_processor.windows['long'])
            },
            'recent_alerts': [
                {
                    'type': alert['type'],
                    'severity': alert['severity'],
                    'timestamp': alert['timestamp'].isoformat()
                }
                for alert in list(self.alert_history)[-5:]  # 最近5个告警
            ]
        }

        # 当前指标
        if len(self.window_processor.windows['short']) > 0:
            current_metrics = self._calculate_realtime_metrics()
            status['current_metrics'] = current_metrics

        return status

    def get_monitoring_report(self) -> Dict[str, Any]:
        """获取监控报告"""
        if not self.performance_stats['start_time']:
            return {'error': 'Monitoring not started'}

        runtime = datetime.now() - self.performance_stats['start_time']

        report = {
            'monitoring_period': {
                'start_time': self.performance_stats['start_time'].isoformat(),
                'end_time': datetime.now().isoformat(),
                'duration_seconds': runtime.total_seconds()
            },
            'performance_summary': {
                'total_samples_processed': self.performance_stats['processed_samples'],
                'total_alerts_generated': self.performance_stats['alerts_generated'],
                'average_processing_time_ms': self.performance_stats['average_processing_time'],
                'samples_per_second': self.performance_stats['processed_samples'] / runtime.total_seconds() if runtime.total_seconds() > 0 else 0
            },
            'alert_summary': self._summarize_alerts(),
            'metric_summary': self._summarize_metrics(),
            'threshold_status': {
                name: self.threshold_manager.get_threshold_info(name)
                for name in self.threshold_manager.thresholds.keys()
            }
        }

        return report

    def _summarize_alerts(self) -> Dict[str, Any]:
        """汇总告警信息"""
        if not self.alert_history:
            return {'total_alerts': 0}

        alert_types = defaultdict(int)
        alert_severities = defaultdict(int)

        for alert in self.alert_history:
            alert_types[alert['type']] += 1
            alert_severities[alert['severity']] += 1

        return {
            'total_alerts': len(self.alert_history),
            'alert_types': dict(alert_types),
            'alert_severities': dict(alert_severities),
            'alerts_per_hour': len(self.alert_history) / (self.performance_stats['processed_samples'] / 60) if self.performance_stats['processed_samples'] > 0 else 0
        }

    def _summarize_metrics(self) -> Dict[str, Any]:
        """汇总指标信息"""
        metric_summary = {}

        for metric_name, values in self.metrics.items():
            if values:
                metric_summary[metric_name] = {
                    'current_value': float(values[-1]),
                    'mean_value': float(np.mean(values)),
                    'std_value': float(np.std(values)),
                    'min_value': float(np.min(values)),
                    'max_value': float(np.max(values)),
                    'total_observations': len(values)
                }

        return metric_summary


if __name__ == "__main__":
    # 测试代码
    print("Testing Real-time Behavior Monitor...")

    # 生成测试数据
    np.random.seed(42)
    n_samples = 500
    baseline_data = np.random.normal(100, 5, n_samples)

    # 添加一些异常值
    anomaly_indices = [100, 200, 300, 400]
    for idx in anomaly_indices:
        baseline_data[idx] = baseline_data[idx] + np.random.choice([-20, 20])  # 显著的异常

    # 创建时间序列
    dates = pd.date_range(start='2024-01-01', periods=n_samples, freq='1min')
    test_series = pd.Series(baseline_data, index=dates)

    # 创建监控器
    monitor = RealTimeBehaviorMonitor()

    # 告警回调函数
    def alert_callback(alert):
        print(f"🚨 ALERT: {alert['type']} - {alert['severity']} at {alert['timestamp']}")
        if 'anomaly_details' in alert:
            print(f"   Anomaly score: {alert['anomaly_details'].get('anomaly_score', 0):.3f}")
        if 'threshold_details' in alert:
            print(f"   Threshold breach: {alert['metric_name']} = {alert['threshold_details'].get('value', 0):.3f}")

    # 添加告警回调
    monitor.add_alert_callback(alert_callback)

    # 从基线数据初始化
    print("Initializing monitor from baseline data...")
    monitor.initialize_from_baseline(test_series)

    # 开始监控
    print("Starting real-time monitoring...")
    monitor.start_monitoring()

    # 模拟实时数据流
    print("Simulating real-time data stream...")
    for i, value in enumerate(baseline_data):
        monitor.add_data_point(float(value))
        time.sleep(0.01)  # 模拟实时数据间隔

        if i % 100 == 0:
            print(f"Processed {i} samples...")
            status = monitor.get_current_status()
            print(f"  Buffer size: {status['buffer_size']}")
            print(f"  Samples processed: {status['performance_stats']['processed_samples']}")
            print(f"  Alerts generated: {status['performance_stats']['alerts_generated']}")

    # 停止监控
    print("Stopping monitoring...")
    monitor.stop_monitoring()

    # 获取监控报告
    print("\n=== Monitoring Report ===")
    report = monitor.get_monitoring_report()

    if 'performance_summary' in report:
        perf = report['performance_summary']
        print(f"Total samples processed: {perf['total_samples_processed']}")
        print(f"Total alerts generated: {perf['total_alerts_generated']}")
        print(f"Average processing time: {perf['average_processing_time_ms']:.3f} ms")
        print(f"Processing rate: {perf['samples_per_second']:.2f} samples/second")

    if 'alert_summary' in report:
        alerts = report['alert_summary']
        print(f"\nAlert Summary:")
        print(f"  Total alerts: {alerts['total_alerts']}")
        print(f"  Alert types: {alerts['alert_types']}")
        print(f"  Alert severities: {alerts['alert_severities']}")

    print("\n✅ Real-time Behavior Monitor test completed successfully!")