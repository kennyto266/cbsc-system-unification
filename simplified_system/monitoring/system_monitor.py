#!/usr / bin / env python3
# -*- coding: utf - 8 -*-
"""
System Monitoring and Alerting
系统监控和警报 - Phase 6.1

Real - time monitoring, performance tracking, and alerting system
实时监控、性能跟踪和警报系统
"""

import logging
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import numpy as np
import pandas as pd
import psutil

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """警报级别"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MetricType(Enum):
    """指标类型"""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class Metric:
    """监控指标"""

    name: str
    value: float
    metric_type: MetricType
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory = dict)
    unit: Optional[str] = None


@dataclass
class Alert:
    """警报信息"""

    level: AlertLevel
    message: str
    metric_name: str
    current_value: float
    threshold: float
    timestamp: datetime
    resolved: bool = False
    context: Dict[str, Any] = field(default_factory = dict)


@dataclass
class MonitoringConfig:
    """监控配置"""

    metrics_collection_interval: int = 60  # seconds
    alert_evaluation_interval: int = 30  # seconds
    retention_period_days: int = 30
    enable_real_time_monitoring: bool = True
    enable_performance_profiling: bool = True
    enable_resource_monitoring: bool = True


class PerformanceMonitor:
    """性能监控器"""

    def __init__(self, config: MonitoringConfig):
        self.config = config
        self.metrics_history = defaultdict(lambda: deque(maxlen = 1000))
        self.alerts = deque(maxlen = 1000)
        self.thresholds = {}
        self.alert_callbacks = []
        self.is_monitoring = False
        self.monitor_thread = None
        self.alert_thread = None

        # 性能指标缓存
        self.performance_cache = {}
        self.last_collection_time = {}

        # 初始化默认阈值
        self._initialize_default_thresholds()

    def _initialize_default_thresholds(self):
        """初始化默认阈值"""
        self.thresholds = {
            "memory_usage_percent": {"warning": 70.0, "error": 85.0, "critical": 95.0},
            "cpu_usage_percent": {"warning": 60.0, "error": 80.0, "critical": 90.0},
            "disk_usage_percent": {"warning": 70.0, "error": 85.0, "critical": 95.0},
            "response_time_ms": {
                "warning": 1000.0,
                "error": 2000.0,
                "critical": 5000.0,
            },
            "error_rate_percent": {"warning": 1.0, "error": 5.0, "critical": 10.0},
        }

    def start_monitoring(self):
        """启动监控"""
        if self.is_monitoring:
            logger.warning("Monitoring is already running")
            return

        self.is_monitoring = True

        # 启动指标收集线程
        self.monitor_thread = threading.Thread(
            target = self._monitoring_loop, daemon = True
        )
        self.monitor_thread.start()

        # 启动警报评估线程
        self.alert_thread = threading.Thread(target = self._alert_loop, daemon = True)
        self.alert_thread.start()

        logger.info("System monitoring started")

    def stop_monitoring(self):
        """停止监控"""
        self.is_monitoring = False

        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout = 5)

        if self.alert_thread and self.alert_thread.is_alive():
            self.alert_thread.join(timeout = 5)

        logger.info("System monitoring stopped")

    def record_metric(self, metric: Metric):
        """记录指标"""
        self.metrics_history[metric.name].append(metric)

        # 触发实时警报检查
        self._check_alerts_immediate(metric)

    def _monitoring_loop(self):
        """监控循环"""
        while self.is_monitoring:
            try:
                # 收集系统指标
                self._collect_system_metrics()

                # 收集应用指标
                self._collect_application_metrics()

                # 清理过期数据
                self._cleanup_old_data()

                time.sleep(self.config.metrics_collection_interval)

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(10)  # 出错时等待10秒

    def _collect_system_metrics(self):
        """收集系统指标"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval = 1)
            self.record_metric(
                Metric(
                    name="cpu_usage_percent",
                    value = cpu_percent,
                    metric_type = MetricType.GAUGE,
                    timestamp = datetime.now(),
                    unit="percent",
                )
            )

            # 内存使用率
            memory = psutil.virtual_memory()
            self.record_metric(
                Metric(
                    name="memory_usage_percent",
                    value = memory.percent,
                    metric_type = MetricType.GAUGE,
                    timestamp = datetime.now(),
                    unit="percent",
                )
            )

            # 磁盘使用率
            disk = psutil.disk_usage("/")
            disk_usage_percent = (disk.used / disk.total) * 100
            self.record_metric(
                Metric(
                    name="disk_usage_percent",
                    value = disk_usage_percent,
                    metric_type = MetricType.GAUGE,
                    timestamp = datetime.now(),
                    unit="percent",
                )
            )

            # 网络IO
            network = psutil.net_io_counters()
            self.record_metric(
                Metric(
                    name="network_bytes_sent",
                    value = network.bytes_sent,
                    metric_type = MetricType.COUNTER,
                    timestamp = datetime.now(),
                    unit="bytes",
                )
            )

            self.record_metric(
                Metric(
                    name="network_bytes_received",
                    value = network.bytes_recv,
                    metric_type = MetricType.COUNTER,
                    timestamp = datetime.now(),
                    unit="bytes",
                )
            )

        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")

    def _collect_application_metrics(self):
        """收集应用指标"""
        try:
            # Python进程指标
            process = psutil.Process()

            # 进程内存
            process_memory = process.memory_info()
            self.record_metric(
                Metric(
                    name="process_memory_rss_mb",
                    value = process_memory.rss / (1024 * 1024),
                    metric_type = MetricType.GAUGE,
                    timestamp = datetime.now(),
                    unit="MB",
                )
            )

            # 进程CPU
            process_cpu = process.cpu_percent()
            self.record_metric(
                Metric(
                    name="process_cpu_percent",
                    value = process_cpu,
                    metric_type = MetricType.GAUGE,
                    timestamp = datetime.now(),
                    unit="percent",
                )
            )

            # 线程数
            num_threads = process.num_threads()
            self.record_metric(
                Metric(
                    name="process_thread_count",
                    value = num_threads,
                    metric_type = MetricType.GAUGE,
                    timestamp = datetime.now(),
                    unit="count",
                )
            )

            # 文件描述符数
            num_fds = process.num_fds()
            self.record_metric(
                Metric(
                    name="process_fd_count",
                    value = num_fds,
                    metric_type = MetricType.GAUGE,
                    timestamp = datetime.now(),
                    unit="count",
                )
            )

        except Exception as e:
            logger.error(f"Error collecting application metrics: {e}")

    def _check_alerts_immediate(self, metric: Metric):
        """立即检查警报"""
        if metric.name in self.thresholds:
            thresholds = self.thresholds[metric.name]

            for level, threshold_value in thresholds.items():
                if metric.value >= threshold_value:
                    alert_level = AlertLevel(level)

                    alert = Alert(
                        level = alert_level,
                        message = f"Metric {metric.name} exceeded {level.value} threshold",
                        metric_name = metric.name,
                        current_value = metric.value,
                        threshold = threshold_value,
                        timestamp = datetime.now(),
                        context={"unit": metric.unit, "tags": metric.tags},
                    )

                    self.alerts.append(alert)
                    self._trigger_alert_callbacks(alert)

                    logger.warning(
                        f"Alert triggered: {alert.message} (Value: {metric.value}, Threshold: {threshold_value})"
                    )

    def _alert_loop(self):
        """警报循环"""
        while self.is_monitoring:
            try:
                # 评估警报条件
                self._evaluate_alert_conditions()

                # 清理已解决的警报
                self._cleanup_resolved_alerts()

                time.sleep(self.config.alert_evaluation_interval)

            except Exception as e:
                logger.error(f"Error in alert loop: {e}")
                time.sleep(10)

    def _evaluate_alert_conditions(self):
        """评估警报条件"""
        current_time = datetime.now()

        # 检查最近5分钟的指标趋势
        trend_window = timedelta(minutes = 5)

        for metric_name, history in self.metrics_history.items():
            if len(history) < 2:
                continue

            # 获取最近的指标
            recent_metrics = [
                metric
                for metric in history
                if current_time - metric.timestamp <= trend_window
            ]

            if len(recent_metrics) < 2:
                continue

            # 计算趋势
            values = [metric.value for metric in recent_metrics]
            if len(values) >= 2:
                trend_slope = (values[-1] - values[0]) / len(values)

                # 检查趋势警报
                self._check_trend_alerts(metric_name, values, trend_slope)

                # 检查阈值警报
                latest_metric = recent_metrics[-1]
                self._check_threshold_alerts(metric_name, latest_metric)

    def _check_trend_alerts(
        self, metric_name: str, values: List[float], trend_slope: float
    ):
        """检查趋势警报"""
        # 如果指标持续增长或下降
        if len(values) >= 5:
            all_increasing = all(
                values[i] < values[i + 1] for i in range(len(values) - 1)
            )
            all_decreasing = all(
                values[i] > values[i + 1] for i in range(len(values) - 1)
            )

            if all_increasing and trend_slope > 0.1:
                self._create_trend_alert(metric_name, "increasing", values, trend_slope)
            elif all_decreasing and trend_slope < -0.1:
                self._create_trend_alert(metric_name, "decreasing", values, trend_slope)

    def _check_threshold_alerts(self, metric_name: str, metric: Metric):
        """检查阈值警报"""
        if metric.name in self.thresholds:
            thresholds = self.thresholds[metric.name]
            latest_value = metric.value

            for level, threshold_value in thresholds.items():
                if latest_value >= threshold_value:
                    alert_level = AlertLevel(level)

                    # 检查是否已经存在相同级别的警报
                    existing_alert = next(
                        (
                            alert
                            for alert in reversed(self.alerts)
                            if (
                                alert.metric_name == metric_name
                                and alert.level == alert_level
                                and not alert.resolved
                                and datetime.now() - alert.timestamp
                                < timedelta(minutes = 5)
                            )
                        ),
                        None,
                    )

                    if not existing_alert:
                        alert = Alert(
                            level = alert_level,
                            message = f"{metric_name} threshold breach",
                            metric_name = metric_name,
                            current_value = latest_value,
                            threshold = threshold_value,
                            timestamp = datetime.now(),
                            context={"unit": metric.unit, "tags": metric.tags},
                        )

                        self.alerts.append(alert)
                        self._trigger_alert_callbacks(alert)

    def _create_trend_alert(
        self, metric_name: str, trend_type: str, values: List[float], slope: float
    ):
        """创建趋势警报"""
        alert_level = AlertLevel.WARNING if abs(slope) < 0.5 else AlertLevel.ERROR

        message = f"Metric {metric_name} showing {trend_type} trend"

        alert = Alert(
            level = alert_level,
            message = message,
            metric_name = metric_name,
            current_value = values[-1],
            threshold = 0,
            timestamp = datetime.now(),
            context={
                "trend_type": trend_type,
                "trend_slope": slope,
                "values_count": len(values),
                "recent_values": values[-5:],
            },
        )

        self.alerts.append(alert)
        self._trigger_alert_callbacks(alert)

    def _cleanup_resolved_alerts(self):
        """清理已解决的警报"""
        current_time = datetime.now()
        cleanup_time = timedelta(hours = 1)

        self.alerts = deque(
            alert
            for alert in self.alerts
            if not alert.resolved and (current_time - alert.timestamp < cleanup_time)
        )

    def _cleanup_old_data(self):
        """清理过期数据"""
        cutoff_time = datetime.now() - timedelta(days = self.config.retention_period_days)

        for metric_name, history in self.metrics_history.items():
            # 保留最近的数据
            valid_metrics = deque(
                metric for metric in history if metric.timestamp > cutoff_time
            )
            self.metrics_history[metric_name] = valid_metrics

    def _trigger_alert_callbacks(self, alert: Alert):
        """触发警报回调"""
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")

    def add_alert_callback(self, callback: Callable[[Alert], None]):
        """添加警报回调函数"""
        self.alert_callbacks.append(callback)

    def get_metrics_summary(self, hours: int = 1) -> Dict[str, Any]:
        """获取指标摘要"""
        cutoff_time = datetime.now() - timedelta(hours = hours)
        summary = {}

        for metric_name, history in self.metrics_history.items():
            recent_metrics = [
                metric for metric in history if metric.timestamp > cutoff_time
            ]

            if recent_metrics:
                values = [metric.value for metric in recent_metrics]
                summary[metric_name] = {
                    "count": len(values),
                    "current": values[-1],
                    "min": min(values),
                    "max": max(values),
                    "avg": np.mean(values),
                    "std": np.std(values) if len(values) > 1 else 0,
                    "metric_type": recent_metrics[-1].metric_type.value,
                    "unit": recent_metrics[-1].unit,
                    "last_updated": recent_metrics[-1].timestamp,
                }

        return summary

    def get_alerts_summary(self, hours: int = 24) -> Dict[str, Any]:
        """获取警报摘要"""
        cutoff_time = datetime.now() - timedelta(hours = hours)

        recent_alerts = [
            alert for alert in self.alerts if alert.timestamp > cutoff_time
        ]

        alert_counts = defaultdict(int)
        for alert in recent_alerts:
            alert_counts[alert.level.value] += 1

        return {
            "total_alerts": len(recent_alerts),
            "alert_counts": dict(alert_counts),
            "recent_alerts": [
                {
                    "level": alert.level.value,
                    "message": alert.message,
                    "metric_name": alert.metric_name,
                    "timestamp": alert.timestamp.isoformat(),
                    "current_value": alert.current_value,
                }
                for alert in recent_alerts[-10:]  # 最近10个警报
            ],
        }

    def create_performance_dashboard_data(self) -> Dict[str, Any]:
        """创建性能仪表板数据"""
        metrics_summary = self.get_metrics_summary(hours = 1)
        alerts_summary = self.get_alerts_summary(hours = 24)

        dashboard_data = {
            "timestamp": datetime.now().isoformat(),
            "system_health": {
                "overall_status": (
                    "healthy" if alerts_summary["total_alerts"] < 5 else "degraded"
                ),
                "active_alerts": alerts_summary["total_alerts"],
                "critical_alerts": alert_counts.get("critical", 0),
            },
            "key_metrics": {},
            "performance_trends": {},
            "resource_utilization": {},
        }

        # 关键性能指标
        key_metric_names = [
            "cpu_usage_percent",
            "memory_usage_percent",
            "disk_usage_percent",
        ]
        for metric_name in key_metric_names:
            if metric_name in metrics_summary:
                dashboard_data["key_metrics"][metric_name] = metrics_summary[
                    metric_name
                ]

        # 资源利用率
        dashboard_data["resource_utilization"] = {
            "cpu": metrics_summary.get("cpu_usage_percent", {}),
            "memory": metrics_summary.get("memory_usage_percent", {}),
            "disk": metrics_summary.get("disk_usage_percent", {}),
        }

        # 警报统计
        dashboard_data["alerts"] = alerts_summary

        return dashboard_data


def default_email_alert_callback(alert: Alert):
    """默认邮件警报回调"""
    # 这里可以实现邮件发送逻辑
    logger.info(f"EMAIL ALERT: [{alert.level.value.upper()}] {alert.message}")
    logger.info(f"  Metric: {alert.metric_name}")
    logger.info(f"  Value: {alert.current_value}")
    logger.info(f"  Time: {alert.timestamp}")


def default_slack_alert_callback(alert: Alert):
    """默认Slack警报回调"""
    # 这里可以实现Slack通知逻辑
    logger.info(f"SLACK ALERT: [{alert.level.value.upper()}] {alert.message}")
    logger.info(f"  Metric: {alert.metric_name} = {alert.current_value}")
    logger.info(f"  Context: {alert.context}")


def example_usage():
    """使用示例"""
    # 创建监控配置
    config = MonitoringConfig(
        metrics_collection_interval = 30,
        alert_evaluation_interval = 15,
        enable_real_time_monitoring = True,
    )

    # 创建性能监控器
    monitor = PerformanceMonitor(config)

    # 添加警报回调
    monitor.add_alert_callback(default_email_alert_callback)
    monitor.add_alert_callback(default_slack_alert_callback)

    # 启动监控
    monitor.start_monitoring()

    try:
        # 模拟一些工作负载
        logger.info("Running application workload...")

        # 记录一些自定义指标
        for i in range(10):
            monitor.record_metric(
                Metric(
                    name="custom_processing_time",
                    value = np.random.uniform(50, 200),
                    metric_type = MetricType.TIMER,
                    timestamp = datetime.now(),
                    unit="ms",
                    tags={"operation": f"batch_{i}"},
                )
            )

            time.sleep(5)

    finally:
        # 停止监控
        monitor.stop_monitoring()

        # 获取摘要报告
        metrics_summary = monitor.get_metrics_summary()
        alerts_summary = monitor.get_alerts_summary()

        logger.info("Monitoring Summary:")
        logger.info(f"  Metrics tracked: {len(metrics_summary)}")
        logger.info(f"  Total alerts: {alerts_summary['total_alerts']}")
        logger.info(
            f"  Critical alerts: {alerts_summary['alert_counts'].get('critical', 0)}"
        )


if __name__ == "__main__":
    example_usage()
