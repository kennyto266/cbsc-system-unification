#!/usr/bin/env python3
"""
Real-Time Progress Monitoring System
實時進度監控系統 (Selection 5.A)

實時進度追蹤功能:
- Live Dashboard: Real-time progress bars and completion estimates
- Parallel Job Status: Monitor multiple concurrent optimizations
- Performance Metrics: CPU, memory, and algorithm convergence tracking
- Alert System: Notifications for completion, failures, or milestones
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
import json
import time
import threading
import queue
from collections import defaultdict, deque
import psutil
import numpy as np
from pathlib import Path

logger = logging.getLogger(__name__)

class AlertLevel(Enum):
    """警報級別"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class MetricType(Enum):
    """指標類型"""
    PROGRESS = "progress"
    PERFORMANCE = "performance"
    SYSTEM = "system"
    QUALITY = "quality"

@dataclass
class Alert:
    """警報"""
    alert_id: str
    job_id: str
    level: AlertLevel
    message: str
    timestamp: datetime
    metric_name: Optional[str] = None
    threshold_value: Optional[float] = None
    actual_value: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class JobProgress:
    """任務進度"""
    job_id: str
    strategy_name: str
    current_iteration: int
    total_iterations: int
    combinations_per_second: float
    current_best_score: float
    estimated_completion_time: Optional[datetime]
    convergence_rate: float
    algorithm_efficiency: float
    last_update: datetime
    parallel_status: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class SystemMetrics:
    """系統指標"""
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    memory_available_gb: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_io_sent_mb: float
    network_io_recv_mb: float
    active_threads: int
    process_count: int

@dataclass
class PerformanceMetrics:
    """性能指標"""
    job_id: str
    timestamp: datetime
    combinations_processed: int
    combinations_per_second: float
    memory_usage_mb: float
    cache_hit_rate: float
    convergence_speed: float
    algorithm_stability: float

class MetricsCollector:
    """指標收集器"""

    def __init__(self, collection_interval: float = 1.0):
        self.collection_interval = collection_interval
        self.is_collecting = False
        self.collection_thread = None
        self.metrics_history = {
            'system': deque(maxlen=3600),  # 1小時歷史
            'performance': defaultdict(lambda: deque(maxlen=3600))
        }
        self.callbacks = []

    def start_collection(self):
        """開始收集指標"""
        if self.is_collecting:
            return

        self.is_collecting = True
        self.collection_thread = threading.Thread(target=self._collection_loop, daemon=True)
        self.collection_thread.start()
        logger.info("Started metrics collection")

    def stop_collection(self):
        """停止收集指標"""
        self.is_collecting = False
        if self.collection_thread:
            self.collection_thread.join(timeout=5)
        logger.info("Stopped metrics collection")

    def _collection_loop(self):
        """收集循環"""
        while self.is_collecting:
            try:
                # 收集系統指標
                system_metrics = self._collect_system_metrics()
                self.metrics_history['system'].append(system_metrics)

                # 通知回調
                for callback in self.callbacks:
                    try:
                        callback('system', system_metrics)
                    except Exception as e:
                        logger.warning(f"Callback error: {e}")

                time.sleep(self.collection_interval)

            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
                time.sleep(self.collection_interval)

    def _collect_system_metrics(self) -> SystemMetrics:
        """收集系統指標"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=None)

            # 內存使用率
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            memory_available_gb = memory.available / (1024**3)

            # 磁盤IO
            disk_io = psutil.disk_io_counters()
            disk_io_read_mb = disk_io.read_bytes / (1024**2) if disk_io else 0
            disk_io_write_mb = disk_io.write_bytes / (1024**2) if disk_io else 0

            # 網絡IO
            network_io = psutil.net_io_counters()
            network_io_sent_mb = network_io.bytes_sent / (1024**2) if network_io else 0
            network_io_recv_mb = network_io.bytes_recv / (1024**2) if network_io else 0

            # 進程數
            process_count = len(psutil.pids())

            # 線程數
            current_process = psutil.Process()
            active_threads = current_process.num_threads()

            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_usage=cpu_percent,
                memory_usage=memory_usage,
                memory_available_gb=memory_available_gb,
                disk_io_read_mb=disk_io_read_mb,
                disk_io_write_mb=disk_io_write_mb,
                network_io_sent_mb=network_io_sent_mb,
                network_io_recv_mb=network_io_recv_mb,
                active_threads=active_threads,
                process_count=process_count
            )

        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_usage=0, memory_usage=0, memory_available_gb=0,
                disk_io_read_mb=0, disk_io_write_mb=0,
                network_io_sent_mb=0, network_io_recv_mb=0,
                active_threads=0, process_count=0
            )

    def collect_job_metrics(self, job_id: str, progress: JobProgress):
        """收集任務指標"""
        try:
            current_process = psutil.Process()
            memory_info = current_process.memory_info()
            memory_usage_mb = memory_info.rss / (1024**2)

            performance_metrics = PerformanceMetrics(
                job_id=job_id,
                timestamp=datetime.now(),
                combinations_processed=progress.current_iteration,
                combinations_per_second=progress.combinations_per_second,
                memory_usage_mb=memory_usage_mb,
                cache_hit_rate=0.0,  # 需要從優化器獲取
                convergence_speed=progress.convergence_rate,
                algorithm_stability=progress.algorithm_efficiency
            )

            self.metrics_history['performance'][job_id].append(performance_metrics)

        except Exception as e:
            logger.error(f"Failed to collect job metrics for {job_id}: {e}")

    def add_callback(self, callback: Callable[[str, Any], None]):
        """添加回調函數"""
        self.callbacks.append(callback)

    def get_metrics_history(self, metric_type: str, job_id: Optional[str] = None,
                          minutes: int = 60) -> List[Any]:
        """獲取指標歷史"""
        if metric_type == 'system':
            history = list(self.metrics_history['system'])
        elif metric_type == 'performance' and job_id:
            history = list(self.metrics_history['performance'][job_id])
        else:
            return []

        # 過濾時間範圍
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        return [m for m in history if m.timestamp >= cutoff_time]

class ProgressTracker:
    """進度追蹤器"""

    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        self.active_jobs = {}
        self.job_progress_history = defaultdict(deque)
        self.convergence_data = defaultdict(list)
        self.performance_trends = defaultdict(deque)

    def track_job_progress(self, job_id: str, strategy_name: str,
                          current_iteration: int, total_iterations: int,
                          best_score: float, combinations_per_second: float = 0.0):
        """追蹤任務進度"""

        now = datetime.now()

        # 計算收斂率
        convergence_rate = self._calculate_convergence_rate(job_id, best_score)
        algorithm_efficiency = self._calculate_algorithm_efficiency(
            job_id, combinations_per_second
        )

        # 估算完成時間
        eta = self._estimate_completion_time(
            current_iteration, total_iterations, combinations_per_second
        )

        # 創建進度對象
        progress = JobProgress(
            job_id=job_id,
            strategy_name=strategy_name,
            current_iteration=current_iteration,
            total_iterations=total_iterations,
            combinations_per_second=combinations_per_second,
            current_best_score=best_score,
            estimated_completion_time=eta,
            convergence_rate=convergence_rate,
            algorithm_efficiency=algorithm_efficiency,
            last_update=now
        )

        # 更新活躍任務
        self.active_jobs[job_id] = progress

        # 記錄歷史
        self.job_progress_history[job_id].append(progress)
        self.convergence_data[job_id].append((now, best_score))
        self.performance_trends[job_id].append((now, combinations_per_second))

        # 收集性能指標
        self.metrics_collector.collect_job_metrics(job_id, progress)

        # 檢查警報條件
        self._check_alert_conditions(progress)

    def _calculate_convergence_rate(self, job_id: str, current_score: float) -> float:
        """計算收斂率"""
        convergence_history = self.convergence_data[job_id]

        if len(convergence_history) < 2:
            return 0.0

        # 計算最近10個點的收斂趨勢
        recent_scores = [score for _, score in convergence_history[-10:]]
        if len(recent_scores) < 2:
            return 0.0

        # 計算改進率
        initial_score = recent_scores[0]
        latest_score = recent_scores[-1]
        improvement = latest_score - initial_score

        # 收斂率 = 改進率 / 時間跨度
        time_span = (convergence_history[-1][0] - convergence_history[-10][0]).total_seconds()
        if time_span > 0:
            return improvement / time_span
        return 0.0

    def _calculate_algorithm_efficiency(self, job_id: str, combos_per_sec: float) -> float:
        """計算算法效率"""
        performance_history = self.performance_trends[job_id]

        if len(performance_history) < 5:
            return min(1.0, combos_per_sec / 100)  # 簡化效率計算

        # 計算平均性能
        recent_performance = [perf for _, perf in performance_history[-10:]]
        avg_performance = np.mean(recent_performance)

        # 效率 = 當前性能 / 平均性能
        if avg_performance > 0:
            efficiency = combos_per_sec / avg_performance
            return min(2.0, efficiency)  # 限制最大效率

        return 1.0

    def _estimate_completion_time(self, current_iteration: int, total_iterations: int,
                                 combos_per_sec: float) -> Optional[datetime]:
        """估算完成時間"""
        if combos_per_sec <= 0 or current_iteration >= total_iterations:
            return None

        remaining_iterations = total_iterations - current_iteration
        remaining_seconds = remaining_iterations / combos_per_sec

        return datetime.now() + timedelta(seconds=remaining_seconds)

    def _check_alert_conditions(self, progress: JobProgress):
        """檢查警報條件"""
        # 這裡可以添加各種警報條件
        # 例如：性能下降、收斂停滯、資源不足等

        pass

    def get_job_progress(self, job_id: str) -> Optional[JobProgress]:
        """獲取任務進度"""
        return self.active_jobs.get(job_id)

    def get_all_active_jobs(self) -> List[JobProgress]:
        """獲取所有活躍任務"""
        return list(self.active_jobs.values())

    def remove_job(self, job_id: str):
        """移除任務"""
        if job_id in self.active_jobs:
            del self.active_jobs[job_id]

class AlertManager:
    """警報管理器"""

    def __init__(self):
        self.alerts = deque(maxlen=10000)  # 保存最近10000個警報
        self.alert_subscribers = defaultdict(list)
        self.alert_rules = self._initialize_alert_rules()
        self.alert_history = defaultdict(list)

    def _initialize_alert_rules(self) -> Dict[str, Callable]:
        """初始化警報規則"""
        return {
            'high_cpu_usage': lambda metrics: metrics.cpu_usage > 80,
            'high_memory_usage': lambda metrics: metrics.memory_usage > 85,
            'low_performance': lambda progress: progress.combinations_per_second < 10,
            'convergence_stagnation': lambda progress: progress.convergence_rate < 0.001,
            'job_timeout': self._check_job_timeout,
            'error_rate_high': self._check_error_rate
        }

    def subscribe_to_alerts(self, job_id: str, callback: Callable[[Alert], None]):
        """訂閱警報"""
        self.alert_subscribers[job_id].append(callback)

    def create_alert(self, job_id: str, level: AlertLevel, message: str,
                    metric_name: Optional[str] = None,
                    threshold_value: Optional[float] = None,
                    actual_value: Optional[float] = None,
                    metadata: Optional[Dict[str, Any]] = None) -> Alert:
        """創建警報"""

        alert = Alert(
            alert_id=str(uuid.uuid4()),
            job_id=job_id,
            level=level,
            message=message,
            timestamp=datetime.now(),
            metric_name=metric_name,
            threshold_value=threshold_value,
            actual_value=actual_value,
            metadata=metadata or {}
        )

        # 添加到警報歷史
        self.alerts.append(alert)
        self.alert_history[job_id].append(alert)

        # 通知訂閱者
        for callback in self.alert_subscribers.get(job_id, []):
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Alert callback error: {e}")

        # 記錄警報
        log_level = {
            AlertLevel.INFO: logging.INFO,
            AlertLevel.WARNING: logging.WARNING,
            AlertLevel.ERROR: logging.ERROR,
            AlertLevel.CRITICAL: logging.CRITICAL
        }.get(level, logging.INFO)

        logger.log(log_level, f"Alert [{level.value.upper()}] {job_id}: {message}")

        return alert

    def check_system_alerts(self, metrics: SystemMetrics):
        """檢查系統警報"""
        # CPU使用率警報
        if metrics.cpu_usage > 90:
            self.create_alert(
                job_id="system",
                level=AlertLevel.CRITICAL,
                message=f"CPU usage critically high: {metrics.cpu_usage:.1f}%",
                metric_name="cpu_usage",
                threshold_value=90.0,
                actual_value=metrics.cpu_usage
            )
        elif metrics.cpu_usage > 80:
            self.create_alert(
                job_id="system",
                level=AlertLevel.WARNING,
                message=f"CPU usage high: {metrics.cpu_usage:.1f}%",
                metric_name="cpu_usage",
                threshold_value=80.0,
                actual_value=metrics.cpu_usage
            )

        # 內存使用率警報
        if metrics.memory_usage > 90:
            self.create_alert(
                job_id="system",
                level=AlertLevel.CRITICAL,
                message=f"Memory usage critically high: {metrics.memory_usage:.1f}%",
                metric_name="memory_usage",
                threshold_value=90.0,
                actual_value=metrics.memory_usage
            )
        elif metrics.memory_usage > 85:
            self.create_alert(
                job_id="system",
                level=AlertLevel.WARNING,
                message=f"Memory usage high: {metrics.memory_usage:.1f}%",
                metric_name="memory_usage",
                threshold_value=85.0,
                actual_value=metrics.memory_usage
            )

    def check_job_alerts(self, progress: JobProgress):
        """檢查任務警報"""
        # 性能下降警報
        if progress.combinations_per_second < 1.0:
            self.create_alert(
                job_id=progress.job_id,
                level=AlertLevel.WARNING,
                message=f"Low performance: {progress.combinations_per_second:.1f} combos/sec",
                metric_name="combinations_per_second",
                threshold_value=1.0,
                actual_value=progress.combinations_per_second
            )

        # 收斂停滯警報
        if progress.convergence_rate < 0.001 and progress.current_iteration > 100:
            self.create_alert(
                job_id=progress.job_id,
                level=AlertLevel.WARNING,
                message="Convergence stagnation detected",
                metric_name="convergence_rate",
                threshold_value=0.001,
                actual_value=progress.convergence_rate
            )

    def get_alerts(self, job_id: Optional[str] = None,
                   level: Optional[AlertLevel] = None,
                   minutes: int = 60) -> List[Alert]:
        """獲取警報"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)

        alerts = []
        for alert in self.alerts:
            if alert.timestamp < cutoff_time:
                continue

            if job_id and alert.job_id != job_id:
                continue

            if level and alert.level != level:
                continue

            alerts.append(alert)

        return sorted(alerts, key=lambda a: a.timestamp, reverse=True)

    def _check_job_timeout(self, job_data: Any) -> bool:
        """檢查任務超時"""
        # 實現任務超時檢查邏輯
        return False

    def _check_error_rate(self, job_data: Any) -> bool:
        """檢查錯誤率"""
        # 實現錯誤率檢查邏輯
        return False

class RealTimeMonitoringSystem:
    """實時監控系統"""

    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.progress_tracker = ProgressTracker(self.metrics_collector)
        self.alert_manager = AlertManager()

        # 啟動指標收集
        self.metrics_collector.start_collection()

        # 添加回調
        self.metrics_collector.add_callback(self._on_system_metrics_update)

        logger.info("Real-time monitoring system initialized")

    def _on_system_metrics_update(self, metric_type: str, metrics: Any):
        """系統指標更新回調"""
        if metric_type == 'system' and isinstance(metrics, SystemMetrics):
            self.alert_manager.check_system_alerts(metrics)

    def start_monitoring(self, job_id: str, strategy_name: str,
                        total_iterations: int):
        """開始監控任務"""
        logger.info(f"Started monitoring job {job_id}")

    def update_progress(self, job_id: str, strategy_name: str,
                        current_iteration: int, total_iterations: int,
                        best_score: float, combinations_per_second: float = 0.0):
        """更新進度"""
        self.progress_tracker.track_job_progress(
            job_id, strategy_name, current_iteration, total_iterations,
            best_score, combinations_per_second
        )

        # 檢查任務警報
        progress = self.progress_tracker.get_job_progress(job_id)
        if progress:
            self.alert_manager.check_job_alerts(progress)

    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """獲取任務狀態"""
        progress = self.progress_tracker.get_job_progress(job_id)
        if not progress:
            return None

        return {
            'job_id': progress.job_id,
            'strategy_name': progress.strategy_name,
            'progress_percentage': (progress.current_iteration / max(1, progress.total_iterations)) * 100,
            'current_iteration': progress.current_iteration,
            'total_iterations': progress.total_iterations,
            'combinations_per_second': progress.combinations_per_second,
            'current_best_score': progress.current_best_score,
            'estimated_completion_time': progress.estimated_completion_time.isoformat() if progress.estimated_completion_time else None,
            'convergence_rate': progress.convergence_rate,
            'algorithm_efficiency': progress.algorithm_efficiency,
            'last_update': progress.last_update.isoformat(),
            'parallel_status': progress.parallel_status
        }

    def get_system_status(self) -> Dict[str, Any]:
        """獲取系統狀態"""
        latest_system_metrics = list(self.metrics_collector.metrics_history['system'])
        if latest_system_metrics:
            system_metrics = latest_system_metrics[-1]
        else:
            system_metrics = SystemMetrics(
                timestamp=datetime.now(), cpu_usage=0, memory_usage=0,
                memory_available_gb=0, disk_io_read_mb=0, disk_io_write_mb=0,
                network_io_sent_mb=0, network_io_recv_mb=0,
                active_threads=0, process_count=0
            )

        active_jobs = self.progress_tracker.get_all_active_jobs()
        recent_alerts = self.alert_manager.get_alerts(minutes=5)

        return {
            'system_metrics': {
                'cpu_usage': system_metrics.cpu_usage,
                'memory_usage': system_metrics.memory_usage,
                'memory_available_gb': system_metrics.memory_available_gb,
                'active_threads': system_metrics.active_threads,
                'process_count': system_metrics.process_count,
                'timestamp': system_metrics.timestamp.isoformat()
            },
            'optimization_status': {
                'active_jobs_count': len(active_jobs),
                'active_jobs': [
                    {
                        'job_id': job.job_id,
                        'strategy_name': job.strategy_name,
                        'progress_percentage': (job.current_iteration / max(1, job.total_iterations)) * 100,
                        'combinations_per_second': job.combinations_per_second,
                        'current_best_score': job.current_best_score
                    }
                    for job in active_jobs
                ]
            },
            'alerts': {
                'recent_count': len(recent_alerts),
                'critical_count': len([a for a in recent_alerts if a.level == AlertLevel.CRITICAL]),
                'warning_count': len([a for a in recent_alerts if a.level == AlertLevel.WARNING]),
                'recent_alerts': [
                    {
                        'alert_id': alert.alert_id,
                        'job_id': alert.job_id,
                        'level': alert.level.value,
                        'message': alert.message,
                        'timestamp': alert.timestamp.isoformat()
                    }
                    for alert in recent_alerts[:10]  # 最近10個警報
                ]
            }
        }

    def subscribe_to_alerts(self, job_id: str, callback: Callable[[Alert], None]):
        """訂閱警報"""
        self.alert_manager.subscribe_to_alerts(job_id, callback)

    def stop_monitoring(self, job_id: str):
        """停止監控任務"""
        self.progress_tracker.remove_job(job_id)
        logger.info(f"Stopped monitoring job {job_id}")

    def cleanup(self):
        """清理資源"""
        self.metrics_collector.stop_collection()
        logger.info("Real-time monitoring system cleaned up")

# 全局實例
_monitoring_system = None

def get_monitoring_system() -> RealTimeMonitoringSystem:
    """獲取監控系統實例"""
    global _monitoring_system
    if _monitoring_system is None:
        _monitoring_system = RealTimeMonitoringSystem()
    return _monitoring_system