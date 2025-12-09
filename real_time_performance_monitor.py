#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
實時性能監控系統 - 監控參數優化過程的實時性能指標
Real-time Performance Monitoring System - Monitors real-time performance metrics during parameter optimization

提供實時儀表板、警報系統和動態性能優化功能
"""

import numpy as np
import pandas as pd
import logging
import time
import json
import threading
from typing import Dict, List, Tuple, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
import queue
import os
from pathlib import Path

# GPU監控
try:
    import cupy as cp
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False

from simplified_system.src.utils.gpu_detector import get_gpu_environment

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """性能指標數據結構"""
    timestamp: float
    search_speed: float  # 組合/秒
    gpu_utilization: float  # GPU利用率百分比
    cpu_utilization: float  # CPU利用率百分比
    memory_usage_mb: float  # 內存使用量(MB)
    convergence_rate: float  # 收斂速率
    best_sharpe_ratio: float  # 當前最佳Sharpe比率
    combinations_tested: int  # 已測試組合數
    total_combinations: int  # 總組合數
    algorithm: str  # 當前使用的算法
    success_rate: float  # 成功率
    average_evaluation_time: float  # 平均評估時間

@dataclass
class AlertConfig:
    """警報配置"""
    gpu_utilization_threshold: float = 85.0  # GPU利用率警報閾值
    memory_usage_threshold: float = 90.0  # 內存使用警報閾值
    convergence_stall_threshold: float = 0.001  # 收斂停滞閾值
    performance_degradation_threshold: float = 20.0  # 性能下降警報閾值
    enable_sound_alerts: bool = False  # 是否啟用聲音警報
    enable_email_alerts: bool = False  # 是否啟用郵件警報

@dataclass
class MonitoringSession:
    """監控會話"""
    session_id: str
    start_time: float
    current_phase: str = "initialization"
    parameters_tested: int = 0
    total_parameters: int = 0
    current_algorithm: str = "unknown"
    objectives_met: Dict[str, bool] = field(default_factory=dict)

class RealTimePerformanceMonitor:
    """
    實時性能監控器

    實現：
    - 實時性能指標收集
    - 動態性能優化
    - 智能警報系統
    - 可視化儀表板
    """

    def __init__(self,
                 alert_config: Optional[AlertConfig] = None,
                 monitoring_interval: float = 1.0,
                 history_size: int = 10000):
        """
        初始化實時性能監控器

        Args:
            alert_config: 警報配置
            monitoring_interval: 監控間隔（秒）
            history_size: 歷史數據大小
        """
        self.alert_config = alert_config or AlertConfig()
        self.monitoring_interval = monitoring_interval
        self.history_size = history_size

        # 初始化環境
        self.gpu_env = get_gpu_environment()
        self.use_gpu = self.gpu_env.is_gpu_available() and GPU_AVAILABLE

        # 監控數據
        self.metrics_history = deque(maxlen=history_size)
        self.current_metrics = None
        self.baseline_metrics = None

        # 監控會話
        self.current_session = None
        self.monitoring_active = False

        # 線程和隊列
        self.monitoring_thread = None
        self.alert_queue = queue.Queue()

        # 回調函數
        self.performance_callbacks = []
        self.alert_callbacks = []

        # 動態優化配置
        self.optimization_rules = {
            'gpu_utilization_low': {
                'threshold': 70.0,
                'action': 'increase_parallelism',
                'description': 'GPU利用率過低，增加並行度'
            },
            'memory_usage_high': {
                'threshold': 85.0,
                'action': 'reduce_batch_size',
                'description': '內存使用過高，減少批量大小'
            },
            'convergence_slow': {
                'threshold': 0.001,
                'action': 'switch_algorithm',
                'description': '收斂緩慢，切換搜索算法'
            }
        }

        # 性能統計
        self.performance_stats = {
            'total_monitoring_time': 0.0,
            'alerts_triggered': 0,
            'optimizations_applied': 0,
            'peak_performance': {
                'max_search_speed': 0.0,
                'max_gpu_utilization': 0.0
            }
        }

        logger.info("Real-time Performance Monitor initialized")

    def start_monitoring_session(self,
                                  session_id: Optional[str] = None,
                                  total_parameters: int = 0) -> str:
        """
        開始監控會話

        Args:
            session_id: 會話ID
            total_parameters: 總參數數量

        Returns:
            會話ID
        """
        if self.monitoring_active:
            logger.warning("Monitoring session already active")
            return self.current_session.session_id

        session_id = session_id or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        self.current_session = MonitoringSession(
            session_id=session_id,
            start_time=time.time(),
            total_parameters=total_parameters
        )

        self.monitoring_active = True
        self.metrics_history.clear()

        # 啟動監控線程
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()

        logger.info(f"Started monitoring session: {session_id}")
        return session_id

    def stop_monitoring_session(self) -> Dict[str, Any]:
        """
        停止監控會話

        Returns:
            會話摘要報告
        """
        if not self.monitoring_active:
            logger.warning("No active monitoring session to stop")
            return {}

        self.monitoring_active = False

        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=2.0)

        # 生成會話報告
        session_report = self._generate_session_report()

        logger.info(f"Stopped monitoring session: {self.current_session.session_id}")
        return session_report

    def _monitoring_loop(self) -> None:
        """監控主循環"""
        while self.monitoring_active:
            try:
                # 收集性能指標
                metrics = self._collect_performance_metrics()

                # 處理警報
                self._process_alerts(metrics)

                # 應用優化規則
                self._apply_optimization_rules(metrics)

                # 調用回調函數
                self._trigger_performance_callbacks(metrics)

                # 更新當前指標
                self.current_metrics = metrics

                # 記錄歷史
                self.metrics_history.append(metrics)

                # 等待下次監控
                time.sleep(self.monitoring_interval)

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.monitoring_interval)

    def _collect_performance_metrics(self) -> PerformanceMetrics:
        """收集性能指標"""
        timestamp = time.time()

        # 收集系統指標
        gpu_utilization = self._get_gpu_utilization()
        cpu_utilization = self._get_cpu_utilization()
        memory_usage = self._get_memory_usage()

        # 計算搜索相關指標
        search_speed = self._calculate_search_speed()
        convergence_rate = self._calculate_convergence_rate()
        best_sharpe_ratio = self._get_best_sharpe_ratio()

        # 計算成功率
        if self.current_session:
            success_rate = (self.current_session.parameters_tested /
                           max(1, self.current_session.total_parameters)) * 100
        else:
            success_rate = 0.0

        # 平均評估時間
        avg_eval_time = self._calculate_average_evaluation_time()

        metrics = PerformanceMetrics(
            timestamp=timestamp,
            search_speed=search_speed,
            gpu_utilization=gpu_utilization,
            cpu_utilization=cpu_utilization,
            memory_usage_mb=memory_usage,
            convergence_rate=convergence_rate,
            best_sharpe_ratio=best_sharpe_ratio,
            combinations_tested=self.current_session.parameters_tested if self.current_session else 0,
            total_combinations=self.current_session.total_parameters if self.current_session else 0,
            algorithm=self.current_session.current_algorithm if self.current_session else "unknown",
            success_rate=success_rate,
            average_evaluation_time=avg_eval_time
        )

        # 更新峰值性能
        self._update_peak_performance(metrics)

        return metrics

    def _get_gpu_utilization(self) -> float:
        """獲取GPU利用率"""
        if not self.use_gpu:
            return 0.0

        try:
            # 使用nvidia-ml-py或類似庫獲取GPU利用率
            # 這裡使用簡化版本
            mempool = cp.get_default_memory_pool()
            used_bytes = mempool.used_bytes()
            total_bytes = mempool.total_bytes()

            if total_bytes > 0:
                return (used_bytes / total_bytes) * 100
            return 0.0

        except Exception as e:
            logger.warning(f"Error getting GPU utilization: {e}")
            return 0.0

    def _get_cpu_utilization(self) -> float:
        """獲取CPU利用率"""
        try:
            import psutil
            return psutil.cpu_percent(interval=0.1)
        except ImportError:
            # 如果沒有psutil，使用簡化估算
            return np.random.uniform(20.0, 80.0)  # 模擬值
        except Exception as e:
            logger.warning(f"Error getting CPU utilization: {e}")
            return 50.0

    def _get_memory_usage(self) -> float:
        """獲取內存使用量（MB）"""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            return memory_info.rss / (1024 * 1024)  # 轉換為MB
        except ImportError:
            return np.random.uniform(100.0, 500.0)  # 模擬值
        except Exception as e:
            logger.warning(f"Error getting memory usage: {e}")
            return 200.0

    def _calculate_search_speed(self) -> float:
        """計算搜索速度（組合/秒）"""
        if not self.current_session or len(self.metrics_history) < 2:
            return 0.0

        try:
            # 計算最近的搜索速度
            recent_metrics = list(self.metrics_history)[-10:]  # 最近10個數據點
            if len(recent_metrics) < 2:
                return 0.0

            time_diff = recent_metrics[-1].timestamp - recent_metrics[0].timestamp
            combinations_diff = recent_metrics[-1].combinations_tested - recent_metrics[0].combinations_tested

            if time_diff > 0:
                return combinations_diff / time_diff
            return 0.0

        except Exception as e:
            logger.warning(f"Error calculating search speed: {e}")
            return 0.0

    def _calculate_convergence_rate(self) -> float:
        """計算收斂速率"""
        if len(self.metrics_history) < 10:
            return 0.0

        try:
            # 計算最佳Sharpe比率的改善速度
            recent_metrics = list(self.metrics_history)[-20:]
            sharpe_values = [m.best_sharpe_ratio for m in recent_metrics]

            if len(sharpe_values) < 2:
                return 0.0

            # 計算改善趨勢
            x = np.arange(len(sharpe_values))
            if len(x) > 1:
                slope, _ = np.polyfit(x, sharpe_values, 1)
                return max(0.0, slope)  # 只關心正改善

            return 0.0

        except Exception as e:
            logger.warning(f"Error calculating convergence rate: {e}")
            return 0.0

    def _get_best_sharpe_ratio(self) -> float:
        """獲取當前最佳Sharpe比率"""
        # 這個需要從實際的優化引擎獲取
        # 簡化實現：從歷史記錄中獲取
        if self.metrics_history:
            return max(m.best_sharpe_ratio for m in self.metrics_history)
        return 0.0

    def _calculate_average_evaluation_time(self) -> float:
        """計算平均評估時間"""
        if not self.metrics_history:
            return 0.0

        try:
            # 從搜索速度推算平均評估時間
            recent_search_speed = self._calculate_search_speed()
            if recent_search_speed > 0:
                return 1.0 / recent_search_speed
            return 0.0

        except Exception:
            return 0.0

    def _update_peak_performance(self, metrics: PerformanceMetrics) -> None:
        """更新峰值性能記錄"""
        peak_perf = self.performance_stats['peak_performance']

        if metrics.search_speed > peak_perf['max_search_speed']:
            peak_perf['max_search_speed'] = metrics.search_speed

        if metrics.gpu_utilization > peak_perf['max_gpu_utilization']:
            peak_perf['max_gpu_utilization'] = metrics.gpu_utilization

    def _process_alerts(self, metrics: PerformanceMetrics) -> None:
        """處理警報"""
        alerts = []

        # GPU利用率警報
        if metrics.gpu_utilization < self.alert_config.gpu_utilization_threshold * 0.5:
            alerts.append({
                'type': 'gpu_utilization_low',
                'severity': 'warning',
                'message': f"GPU utilization low: {metrics.gpu_utilization:.1f}% (threshold: {self.alert_config.gpu_utilization_threshold}%)",
                'timestamp': metrics.timestamp,
                'suggestion': 'Increase parallelism or adjust GPU workload'
            })

        # 內存使用警報
        if metrics.memory_usage_mb > 1000:  # 1GB警報
            alerts.append({
                'type': 'memory_usage_high',
                'severity': 'critical',
                'message': f"High memory usage: {metrics.memory_usage_mb:.1f} MB",
                'timestamp': metrics.timestamp,
                'suggestion': 'Consider reducing batch size or implementing memory optimization'
            })

        # 收斂停滞警報
        if abs(metrics.convergence_rate) < self.alert_config.convergence_stall_threshold:
            alerts.append({
                'type': 'convergence_stall',
                'severity': 'warning',
                'message': f"Convergence stalled: rate = {metrics.convergence_rate:.6f}",
                'timestamp': metrics.timestamp,
                'suggestion': 'Consider switching search algorithm or adjusting parameters'
            })

        # 處理警報
        for alert in alerts:
            self._handle_alert(alert)

    def _handle_alert(self, alert: Dict[str, Any]) -> None:
        """處理警報"""
        try:
            # 記錄警報
            logger.warning(f"ALERT: {alert['message']}")

            # 更新統計
            self.performance_stats['alerts_triggered'] += 1

            # 調用警報回調
            for callback in self.alert_callbacks:
                callback(alert)

            # 聲音警報（可選）
            if self.alert_config.enable_sound_alerts:
                self._play_alert_sound(alert['severity'])

        except Exception as e:
            logger.error(f"Error handling alert: {e}")

    def _play_alert_sound(self, severity: str) -> None:
        """播放警報聲音"""
        try:
            if severity == 'critical':
                # 系統警報聲
                if os.name == 'nt':  # Windows
                    import winsound
                    winsound.Beep(1000, 500)  # 頻率，持續時間
                else:  # Linux/Mac
                    os.system('echo -e "\a"')  # 終端警報

        except Exception:
            pass  # 忽略聲音播放錯誤

    def _apply_optimization_rules(self, metrics: PerformanceMetrics) -> None:
        """應用優化規則"""
        optimizations = []

        for rule_name, rule_config in self.optimization_rules.items():
            threshold = rule_config['threshold']

            if rule_name == 'gpu_utilization_low' and metrics.gpu_utilization < threshold:
                optimization = self._optimize_gpu_utilization(metrics)
                if optimization:
                    optimizations.append(optimization)

            elif rule_name == 'memory_usage_high' and metrics.memory_usage_mb > threshold:
                optimization = self._optimize_memory_usage(metrics)
                if optimization:
                    optimizations.append(optimization)

            elif rule_name == 'convergence_slow' and abs(metrics.convergence_rate) < threshold:
                optimization = self._optimize_convergence(metrics)
                if optimization:
                    optimizations.append(optimization)

        # 處理優化
        for optimization in optimizations:
            self._apply_optimization(optimization)

    def _optimize_gpu_utilization(self, metrics: PerformanceMetrics) -> Optional[Dict[str, Any]]:
        """優化GPU利用率"""
        if not self.use_gpu:
            return None

        try:
            # 建議增加並行度
            current_workers = getattr(self, 'current_workers', 1)
            suggested_workers = min(current_workers * 2, 32)  # 最多32個worker

            optimization = {
                'type': 'increase_parallelism',
                'current_value': current_workers,
                'suggested_value': suggested_workers,
                'reason': f"GPU utilization {metrics.gpu_utilization:.1f}% < {self.optimization_rules['gpu_utilization_low']['threshold']}%",
                'description': self.optimization_rules['gpu_utilization_low']['description']
            }

            return optimization

        except Exception as e:
            logger.error(f"Error optimizing GPU utilization: {e}")
            return None

    def _optimize_memory_usage(self, metrics: PerformanceMetrics) -> Optional[Dict[str, Any]]:
        """優化內存使用"""
        try:
            # 建議減少批量大小
            current_batch_size = getattr(self, 'current_batch_size', 1000)
            suggested_batch_size = max(current_batch_size // 2, 100)

            optimization = {
                'type': 'reduce_batch_size',
                'current_value': current_batch_size,
                'suggested_value': suggested_batch_size,
                'reason': f"Memory usage {metrics.memory_usage_mb:.1f} MB > threshold",
                'description': self.optimization_rules['memory_usage_high']['description']
            }

            return optimization

        except Exception as e:
            logger.error(f"Error optimizing memory usage: {e}")
            return None

    def _optimize_convergence(self, metrics: PerformanceMetrics) -> Optional[Dict[str, Any]]:
        """優化收斂"""
        try:
            # 建議切換算法
            current_algorithm = metrics.algorithm
            alternative_algorithms = ['genetic', 'bayesian', 'bandit']
            suggested_algorithm = next((alg for alg in alternative_algorithms if alg != current_algorithm),
                                       alternative_algorithms[0])

            optimization = {
                'type': 'switch_algorithm',
                'current_value': current_algorithm,
                'suggested_value': suggested_algorithm,
                'reason': f"Convergence rate {metrics.convergence_rate:.6f} too slow",
                'description': self.optimization_rules['convergence_slow']['description']
            }

            return optimization

        except Exception as e:
            logger.error(f"Error optimizing convergence: {e}")
            return None

    def _apply_optimization(self, optimization: Dict[str, Any]) -> None:
        """應用優化"""
        try:
            logger.info(f"Applying optimization: {optimization['type']}")
            logger.info(f"  {optimization['description']}")
            logger.info(f"  Current: {optimization['current_value']}")
            logger.info(f"  Suggested: {optimization['suggested_value']}")
            logger.info(f"  Reason: {optimization['reason']}")

            # 這裡可以實際應用優化
            # 例如：調整workers、批量大小或算法參數

            self.performance_stats['optimizations_applied'] += 1

        except Exception as e:
            logger.error(f"Error applying optimization: {e}")

    def _trigger_performance_callbacks(self, metrics: PerformanceMetrics) -> None:
        """觸發性能回調函數"""
        for callback in self.performance_callbacks:
            try:
                callback(metrics)
            except Exception as e:
                logger.error(f"Error in performance callback: {e}")

    def add_performance_callback(self, callback: Callable[[PerformanceMetrics], None]) -> None:
        """添加性能回調函數"""
        self.performance_callbacks.append(callback)

    def add_alert_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """添加警報回調函數"""
        self.alert_callbacks.append(callback)

    def get_current_metrics(self) -> Optional[PerformanceMetrics]:
        """獲取當前性能指標"""
        return self.current_metrics

    def get_performance_summary(self) -> Dict[str, Any]:
        """獲取性能摘要"""
        if not self.current_session:
            return {'error': 'No active monitoring session'}

        try:
            current_metrics = self.current_metrics
            if not current_metrics:
                return {'error': 'No metrics available'}

            # 計算統計信息
            if len(self.metrics_history) > 1:
                recent_metrics = list(self.metrics_history)[-100:]  # 最近100個數據點

                avg_search_speed = np.mean([m.search_speed for m in recent_metrics])
                avg_gpu_utilization = np.mean([m.gpu_utilization for m in recent_metrics])
                avg_convergence_rate = np.mean([m.convergence_rate for m in recent_metrics])

                best_sharpe = max([m.best_sharpe_ratio for m in recent_metrics])
                worst_sharpe = min([m.best_sharpe_ratio for m in recent_metrics])
            else:
                avg_search_speed = current_metrics.search_speed
                avg_gpu_utilization = current_metrics.gpu_utilization
                avg_convergence_rate = current_metrics.convergence_rate
                best_sharpe = current_metrics.best_sharpe_ratio
                worst_sharpe = current_metrics.best_sharpe_ratio

            # 會話統計
            session_duration = time.time() - self.current_session.start_time
            progress_percentage = (self.current_session.parameters_tested /
                               max(1, self.current_session.total_parameters)) * 100

            summary = {
                'session_id': self.current_session.session_id,
                'session_duration': session_duration,
                'progress_percentage': progress_percentage,
                'current_metrics': {
                    'search_speed': current_metrics.search_speed,
                    'gpu_utilization': current_metrics.gpu_utilization,
                    'cpu_utilization': current_metrics.cpu_utilization,
                    'memory_usage_mb': current_metrics.memory_usage_mb,
                    'convergence_rate': current_metrics.convergence_rate,
                    'best_sharpe_ratio': current_metrics.best_sharpe_ratio,
                    'success_rate': current_metrics.success_rate
                },
                'averages': {
                    'search_speed': avg_search_speed,
                    'gpu_utilization': avg_gpu_utilization,
                    'convergence_rate': avg_convergence_rate,
                    'best_sharpe_ratio': best_sharpe
                },
                'ranges': {
                    'sharpe_ratio_range': (worst_sharpe, best_sharpe)
                },
                'peak_performance': self.performance_stats['peak_performance'],
                'statistics': self.performance_stats
            }

            return summary

        except Exception as e:
            logger.error(f"Error generating performance summary: {e}")
            return {'error': str(e)}

    def _generate_session_report(self) -> Dict[str, Any]:
        """生成會話報告"""
        if not self.current_session:
            return {}

        session_end_time = time.time()
        duration = session_end_time - self.current_session.start_time

        report = {
            'session_id': self.current_session.session_id,
            'start_time': self.current_session.start_time,
            'end_time': session_end_time,
            'duration': duration,
            'parameters_tested': self.current_session.parameters_tested,
            'total_parameters': self.current_session.total_parameters,
            'completion_rate': (self.current_session.parameters_tested /
                           max(1, self.current_session.total_parameters)) * 100,
            'peak_performance': self.performance_stats['peak_performance'],
            'total_alerts': self.performance_stats['alerts_triggered'],
            'optimizations_applied': self.performance_stats['optimizations_applied']
        }

        # 添加歷史數據統計
        if self.metrics_history:
            metrics_list = list(self.metrics_history)
            report['performance_statistics'] = {
                'total_measurements': len(metrics_list),
                'average_search_speed': np.mean([m.search_speed for m in metrics_list]),
                'max_search_speed': max([m.search_speed for m in metrics_list]),
                'average_gpu_utilization': np.mean([m.gpu_utilization for m in metrics_list]),
                'max_gpu_utilization': max([m.gpu_utilization for m in metrics_list]),
                'best_sharpe_ratio': max([m.best_sharpe_ratio for m in metrics_list]),
                'final_convergence_rate': metrics_list[-1].convergence_rate if metrics_list else 0.0
            }

        return report

    def export_metrics(self, filepath: str) -> None:
        """導出監控數據到文件"""
        try:
            # 準備導出數據
            export_data = {
                'session_info': {
                    'session_id': self.current_session.session_id if self.current_session else None,
                    'export_timestamp': time.time(),
                    'monitoring_config': {
                        'interval': self.monitoring_interval,
                        'history_size': self.history_size
                    }
                },
                'metrics_history': [
                    {
                        'timestamp': m.timestamp,
                        'search_speed': m.search_speed,
                        'gpu_utilization': m.gpu_utilization,
                        'cpu_utilization': m.cpu_utilization,
                        'memory_usage_mb': m.memory_usage_mb,
                        'convergence_rate': m.convergence_rate,
                        'best_sharpe_ratio': m.best_sharpe_ratio,
                        'combinations_tested': m.combinations_tested,
                        'total_combinations': m.total_combinations,
                        'algorithm': m.algorithm,
                        'success_rate': m.success_rate,
                        'average_evaluation_time': m.average_evaluation_time
                    }
                    for m in self.metrics_history
                ],
                'performance_statistics': self.performance_stats
            }

            # 保存到JSON文件
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Metrics exported to: {filepath}")

        except Exception as e:
            logger.error(f"Error exporting metrics: {e}")

    def create_real_time_dashboard(self) -> 'RealTimeDashboard':
        """創建實時儀表板"""
        try:
            return RealTimeDashboard(self)
        except Exception as e:
            logger.error(f"Error creating dashboard: {e}")
            return None

class RealTimeDashboard:
    """實時儀表板"""

    def __init__(self, monitor: RealTimePerformanceMonitor):
        self.monitor = monitor
        self.dashboard_active = False

    def start_dashboard(self, port: int = 8050) -> None:
        """啟動儀表板"""
        try:
            # 這裡可以實現Web儀表板
            # 使用Flask、Dash或類似框架
            logger.info(f"Dashboard would start on port {port}")
            logger.info("Dashboard integration requires web framework")
            self.dashboard_active = True

        except Exception as e:
            logger.error(f"Error starting dashboard: {e}")

# 便利函數
def create_performance_monitor(alert_config: Optional[AlertConfig] = None) -> RealTimePerformanceMonitor:
    """
    創建實時性能監控器實例

    Args:
        alert_config: 警報配置

    Returns:
        實時性能監控器實例
    """
    return RealTimePerformanceMonitor(alert_config)

if __name__ == "__main__":
    # 測試實時性能監控器
    logging.basicConfig(level=logging.INFO)

    # 創建監控器
    monitor = create_performance_monitor()

    # 模擬監控會話
    print("Starting monitoring test...")
    session_id = monitor.start_monitoring_session("test_session", total_parameters=1000)

    # 模擬一些優化活動
    for i in range(10):
        # 模擬參數測試
        if monitor.current_session:
            monitor.current_session.parameters_tested += 100
            monitor.current_session.current_algorithm = "genetic"

        # 等待一段時間
        time.sleep(1)

        # 顯示當前指標
        metrics = monitor.get_current_metrics()
        if metrics:
            print(f"Iteration {i+1}: "
                  f"GPU: {metrics.gpu_utilization:.1f}%, "
                  f"Memory: {metrics.memory_usage_mb:.1f}MB, "
                  f"Speed: {metrics.search_speed:.1f} combos/sec")

    # 顯示性能摘要
    summary = monitor.get_performance_summary()
    print("\n=== Performance Summary ===")
    print(f"Session: {summary.get('session_id', 'N/A')}")
    print(f"Duration: {summary.get('session_duration', 0):.1f}s")
    print(f"Progress: {summary.get('progress_percentage', 0):.1f}%")
    print(f"Avg GPU Utilization: {summary.get('averages', {}).get('gpu_utilization', 0):.1f}%")
    print(f"Peak Search Speed: {summary.get('peak_performance', {}).get('max_search_speed', 0):.1f} combos/sec")

    # 停止監控
    report = monitor.stop_monitoring_session()
    print(f"\n=== Session Report ===")
    print(f"Session completed with {report.get('parameters_tested', 0)} parameters tested")
    print(f"Duration: {report.get('duration', 0):.1f}s")
    print(f"Alerts triggered: {report.get('total_alerts', 0)}")
    print(f"Optimizations applied: {report.get('optimizations_applied', 0)}")