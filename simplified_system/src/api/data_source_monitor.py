#!/usr/bin/env python3
"""
數據源監控和警報系統
Data Source Monitoring and Alerting System

實時監控數據源健康狀態，提供異常檢測和警報功能
"""

import asyncio
import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import statistics
import aiohttp
import pandas as pd

from .multi_source_data_manager import DataSourceStatus, HealthCheckResult

logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    """警報嚴重程度"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class Alert:
    """警報信息"""
    id: str
    source_name: str
    severity: AlertSeverity
    title: str
    message: str
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class PerformanceMetrics:
    """性能指標"""
    source_name: str
    response_times: List[float]
    success_rates: List[float]
    data_quality_scores: List[float]
    error_counts: Dict[str, int]
    last_updated: datetime

    @property
    def avg_response_time(self) -> float:
        return statistics.mean(self.response_times) if self.response_times else 0.0

    @property
    def avg_success_rate(self) -> float:
        return statistics.mean(self.success_rates) if self.success_rates else 0.0

    @property
    def avg_data_quality(self) -> float:
        return statistics.mean(self.data_quality_scores) if self.data_quality_scores else 0.0

    @property
    def error_rate(self) -> float:
        total_requests = sum(self.error_counts.values())
        failed_requests = sum(count for error_type, count in self.error_counts.items()
                            if error_type != "success")
        return failed_requests / max(total_requests, 1)

class AlertManager:
    """警報管理器"""

    def __init__(self):
        self.alerts: Dict[str, Alert] = {}
        self.alert_handlers: List[Callable[[Alert], None]] = []
        self.alert_rules = self._initialize_alert_rules()

    def _initialize_alert_rules(self) -> Dict[str, Callable]:
        """初始化警報規則"""
        return {
            "high_response_time": self._check_high_response_time,
            "low_success_rate": self._check_low_success_rate,
            "source_down": self._check_source_down,
            "data_quality_degradation": self._check_data_quality_degradation,
            "error_spike": self._check_error_spike
        }

    async def check_alert_conditions(self, health_results: Dict[str, HealthCheckResult],
                                    performance_metrics: Dict[str, PerformanceMetrics]):
        """檢查警報條件"""
        for source_name in health_results:
            health = health_results[source_name]
            metrics = performance_metrics.get(source_name)

            for rule_name, rule_func in self.alert_rules.items():
                try:
                    alert = await rule_func(source_name, health, metrics)
                    if alert:
                        await self._handle_alert(alert)
                except Exception as e:
                    logger.error(f"Alert rule {rule_name} error for {source_name}: {e}")

    async def _check_high_response_time(self, source_name: str, health: HealthCheckResult,
                                      metrics: Optional[PerformanceMetrics]) -> Optional[Alert]:
        """檢查高響應時間"""
        threshold = 5000  # 5 seconds

        if health.response_time > threshold:
            severity = AlertSeverity.CRITICAL if health.response_time > 10000 else AlertSeverity.ERROR
            return Alert(
                id=f"high_response_time_{source_name}_{int(time.time())}",
                source_name=source_name,
                severity=severity,
                title="High Response Time Detected",
                message=f"Response time {health.response_time:.2f}ms exceeds threshold {threshold}ms",
                timestamp=datetime.now(),
                metadata={
                    "response_time": health.response_time,
                    "threshold": threshold
                }
            )
        return None

    async def _check_low_success_rate(self, source_name: str, health: HealthCheckResult,
                                    metrics: Optional[PerformanceMetrics]) -> Optional[Alert]:
        """檢查成功率過低"""
        threshold = 0.95  # 95%

        if health.success_rate < threshold:
            severity = AlertSeverity.CRITICAL if health.success_rate < 0.8 else AlertSeverity.ERROR
            return Alert(
                id=f"low_success_rate_{source_name}_{int(time.time())}",
                source_name=source_name,
                severity=severity,
                title="Low Success Rate Detected",
                message=f"Success rate {health.success_rate:.2%} below threshold {threshold:.2%}",
                timestamp=datetime.now(),
                metadata={
                    "success_rate": health.success_rate,
                    "threshold": threshold
                }
            )
        return None

    async def _check_source_down(self, source_name: str, health: HealthCheckResult,
                                metrics: Optional[PerformanceMetrics]) -> Optional[Alert]:
        """檢查數據源故障"""
        if health.status == DataSourceStatus.UNHEALTHY:
            return Alert(
                id=f"source_down_{source_name}_{int(time.time())}",
                source_name=source_name,
                severity=AlertSeverity.CRITICAL,
                title="Data Source Down",
                message=f"Data source {source_name} is down: {health.error_message or 'Unknown error'}",
                timestamp=datetime.now(),
                metadata={
                    "status": health.status.value,
                    "error_message": health.error_message
                }
            )
        return None

    async def _check_data_quality_degradation(self, source_name: str, health: HealthCheckResult,
                                            metrics: Optional[PerformanceMetrics]) -> Optional[Alert]:
        """檢查數據質量下降"""
        if health.data_quality_score is not None and health.data_quality_score < 0.7:
            severity = AlertSeverity.WARNING if health.data_quality_score >= 0.5 else AlertSeverity.ERROR
            return Alert(
                id=f"data_quality_{source_name}_{int(time.time())}",
                source_name=source_name,
                severity=severity,
                title="Data Quality Degradation",
                message=f"Data quality score {health.data_quality_score:.2f} is below acceptable level",
                timestamp=datetime.now(),
                metadata={
                    "quality_score": health.data_quality_score,
                    "threshold": 0.7
                }
            )
        return None

    async def _check_error_spike(self, source_name: str, health: HealthCheckResult,
                               metrics: Optional[PerformanceMetrics]) -> Optional[Alert]:
        """檢查錯誤激增"""
        if metrics and len(metrics.error_counts) > 1:
            # 計算錯誤率
            total_errors = sum(count for error_type, count in metrics.error_counts.items()
                             if error_type != "success")
            total_requests = sum(metrics.error_counts.values())

            if total_requests > 0:
                error_rate = total_errors / total_requests
                if error_rate > 0.1:  # 10% error rate threshold
                    severity = AlertSeverity.CRITICAL if error_rate > 0.2 else AlertSeverity.ERROR
                    return Alert(
                        id=f"error_spike_{source_name}_{int(time.time())}",
                        source_name=source_name,
                        severity=severity,
                        title="Error Spike Detected",
                        message=f"Error rate {error_rate:.2%} exceeds 10% threshold",
                        timestamp=datetime.now(),
                        metadata={
                            "error_rate": error_rate,
                            "error_counts": metrics.error_counts,
                            "total_requests": total_requests
                        }
                    )
        return None

    async def _handle_alert(self, alert: Alert):
        """處理警報"""
        # 檢查是否已存在未解決的相同警報
        existing_alerts = [
            a for a in self.alerts.values()
            if not a.resolved and a.source_name == alert.source_name and a.title == alert.title
        ]

        if existing_alerts:
            # 更新現有警報
            existing_alert = existing_alerts[0]
            existing_alert.metadata.update(alert.metadata)
            existing_alert.timestamp = alert.timestamp
            logger.warning(f"Updated existing alert: {alert.title}")
        else:
            # 創建新警報
            self.alerts[alert.id] = alert
            logger.error(f"New alert: {alert.title} - {alert.message}")

        # 調用警報處理器
        for handler in self.alert_handlers:
            try:
                await handler(alert)
            except Exception as e:
                logger.error(f"Alert handler error: {e}")

    def add_alert_handler(self, handler: Callable[[Alert], None]):
        """添加警報處理器"""
        self.alert_handlers.append(handler)

    def resolve_alert(self, alert_id: str):
        """解決警報"""
        if alert_id in self.alerts:
            self.alerts[alert_id].resolved = True
            self.alerts[alert_id].resolved_at = datetime.now()
            logger.info(f"Alert resolved: {alert_id}")

    def get_active_alerts(self) -> List[Alert]:
        """獲取活躍警報"""
        return [alert for alert in self.alerts.values() if not alert.resolved]

    def get_alert_history(self, hours: int = 24) -> List[Alert]:
        """獲取警報歷史"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [
            alert for alert in self.alerts.values()
            if alert.timestamp >= cutoff_time
        ]

class DataSourceMonitor:
    """數據源監控器主類"""

    def __init__(self, data_manager, check_interval: int = 60):
        self.data_manager = data_manager
        self.check_interval = check_interval
        self.running = False
        self.monitor_task = None

        # 監控數據
        self.health_history: Dict[str, List[HealthCheckResult]] = {}
        self.performance_metrics: Dict[str, PerformanceMetrics] = {}
        self.alert_manager = AlertManager()

        # 初始化警報處理器
        self._initialize_alert_handlers()

    def _initialize_alert_handlers(self):
        """初始化警報處理器"""
        self.alert_manager.add_alert_handler(self._log_alert_handler)
        self.alert_manager.add_alert_handler(self._persist_alert_handler)

    async def _log_alert_handler(self, alert: Alert):
        """日誌警報處理器"""
        log_level = {
            AlertSeverity.INFO: logger.info,
            AlertSeverity.WARNING: logger.warning,
            AlertSeverity.ERROR: logger.error,
            AlertSeverity.CRITICAL: logger.critical
        }.get(alert.severity, logger.info)

        log_level(f"ALERT [{alert.severity.value.upper()}] {alert.source_name}: {alert.message}")

    async def _persist_alert_handler(self, alert: Alert):
        """持久化警報處理器"""
        try:
            # 這裡可以添加將警報保存到數據庫或文件的邏輯
            alert_file = f"logs/alerts_{datetime.now().strftime('%Y%m%d')}.json"
            with open(alert_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(asdict(alert), default=str) + '\n')
        except Exception as e:
            logger.error(f"Failed to persist alert: {e}")

    async def start_monitoring(self):
        """開始監控"""
        if self.running:
            logger.warning("Monitor is already running")
            return

        self.running = True
        self.monitor_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Data source monitoring started")

    async def stop_monitoring(self):
        """停止監控"""
        self.running = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Data source monitoring stopped")

    async def _monitoring_loop(self):
        """監控循環"""
        while self.running:
            try:
                await self._collect_monitoring_data()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(60)

    async def _collect_monitoring_data(self):
        """收集監控數據"""
        try:
            # 獲取當前健康狀態
            health_results = self.data_manager.get_data_source_health()

            # 更新健康歷史
            for source_name, health_result in health_results.items():
                if source_name not in self.health_history:
                    self.health_history[source_name] = []

                self.health_history[source_name].append(health_result)

                # 保持歷史記錄在合理範圍內（最近100次檢查）
                if len(self.health_history[source_name]) > 100:
                    self.health_history[source_name] = self.health_history[source_name][-100:]

                # 更新性能指標
                self._update_performance_metrics(source_name, health_result)

            # 檢查警報條件
            await self.alert_manager.check_alert_conditions(health_results, self.performance_metrics)

        except Exception as e:
            logger.error(f"Error collecting monitoring data: {e}")

    def _update_performance_metrics(self, source_name: str, health_result: HealthCheckResult):
        """更新性能指標"""
        if source_name not in self.performance_metrics:
            self.performance_metrics[source_name] = PerformanceMetrics(
                source_name=source_name,
                response_times=[],
                success_rates=[],
                data_quality_scores=[],
                error_counts={},
                last_updated=datetime.now()
            )

        metrics = self.performance_metrics[source_name]

        # 更新響應時間
        metrics.response_times.append(health_result.response_time)
        if len(metrics.response_times) > 100:
            metrics.response_times = metrics.response_times[-100:]

        # 更新成功率
        metrics.success_rates.append(health_result.success_rate)
        if len(metrics.success_rates) > 100:
            metrics.success_rates = metrics.success_rates[-100:]

        # 更新數據質量分數
        if health_result.data_quality_score is not None:
            metrics.data_quality_scores.append(health_result.data_quality_score)
            if len(metrics.data_quality_scores) > 100:
                metrics.data_quality_scores = metrics.data_quality_scores[-100:]

        # 更新錯誤計數
        error_type = "success" if health_result.status == DataSourceStatus.HEALTHY else "error"
        metrics.error_counts[error_type] = metrics.error_counts.get(error_type, 0) + 1

        metrics.last_updated = datetime.now()

    def get_monitoring_dashboard(self) -> Dict[str, Any]:
        """獲取監控儀表板數據"""
        active_alerts = self.alert_manager.get_active_alerts()
        recent_alerts = self.alert_manager.get_alert_history(24)

        dashboard = {
            "summary": {
                "total_sources": len(self.health_history),
                "healthy_sources": len([
                    name for name, history in self.health_history.items()
                    if history and history[-1].status == DataSourceStatus.HEALTHY
                ]),
                "active_alerts": len(active_alerts),
                "alerts_24h": len(recent_alerts),
                "last_check": datetime.now().isoformat()
            },
            "sources": {},
            "alerts": {
                "active": [asdict(alert) for alert in active_alerts[:10]],
                "recent": [asdict(alert) for alert in recent_alerts[:20]]
            }
        }

        # 添加各數據源的詳細信息
        for source_name, history in self.health_history.items():
            if not history:
                continue

            latest = history[-1]
            metrics = self.performance_metrics.get(source_name)

            dashboard["sources"][source_name] = {
                "status": latest.status.value,
                "response_time": latest.response_time,
                "success_rate": latest.success_rate,
                "data_quality": latest.data_quality_score,
                "last_check": latest.last_check.isoformat(),
                "uptime_percentage": self._calculate_uptime_percentage(history),
                "performance": {
                    "avg_response_time": metrics.avg_response_time if metrics else 0,
                    "avg_success_rate": metrics.avg_success_rate if metrics else 0,
                    "avg_data_quality": metrics.avg_data_quality if metrics else 0,
                    "error_rate": metrics.error_rate if metrics else 0
                } if metrics else None
            }

        return dashboard

    def _calculate_uptime_percentage(self, history: List[HealthCheckResult]) -> float:
        """計算運行時間百分比"""
        if not history:
            return 0.0

        healthy_checks = sum(1 for h in history if h.status == DataSourceStatus.HEALTHY)
        return healthy_checks / len(history)

    def get_source_trends(self, source_name: str, hours: int = 24) -> Dict[str, List]:
        """獲取數據源趨勢數據"""
        if source_name not in self.health_history:
            return {}

        history = self.health_history[source_name]
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_history = [h for h in history if h.last_check >= cutoff_time]

        return {
            "timestamps": [h.last_check.isoformat() for h in recent_history],
            "response_times": [h.response_time for h in recent_history],
            "success_rates": [h.success_rate for h in recent_history],
            "data_quality_scores": [h.data_quality_score for h in recent_history if h.data_quality_score is not None],
            "statuses": [h.status.value for h in recent_history]
        }

    def export_monitoring_report(self, hours: int = 24) -> Dict[str, Any]:
        """導出監控報告"""
        dashboard = self.get_monitoring_dashboard()
        recent_alerts = self.alert_manager.get_alert_history(hours)

        # 添加詳細分析
        report = {
            "report_metadata": {
                "generated_at": datetime.now().isoformat(),
                "period_hours": hours,
                "total_sources": len(self.health_history)
            },
            "executive_summary": dashboard["summary"],
            "source_analysis": {},
            "performance_analysis": {},
            "alert_analysis": {
                "total_alerts": len(recent_alerts),
                "by_severity": {},
                "by_source": {},
                "top_issues": sorted(
                    [(alert.title, len([a for a in recent_alerts if a.title == alert.title]))
                     for alert in recent_alerts],
                    key=lambda x: x[1], reverse=True
                )[:10]
            }
        }

        # 按嚴重程度統計警報
        for alert in recent_alerts:
            severity = alert.severity.value
            report["alert_analysis"]["by_severity"][severity] = \
                report["alert_analysis"]["by_severity"].get(severity, 0) + 1

        # 按數據源統計警報
        for alert in recent_alerts:
            source = alert.source_name
            report["alert_analysis"]["by_source"][source] = \
                report["alert_analysis"]["by_source"].get(source, 0) + 1

        # 添加各數據源的詳細分析
        for source_name, source_data in dashboard["sources"].items():
            report["source_analysis"][source_name] = {
                "current_status": source_data["status"],
                "uptime_percentage": source_data["uptime_percentage"],
                "performance_summary": source_data["performance"],
                "recent_trends": self.get_source_trends(source_name, hours)
            }

        return report

# Global instance for backward compatibility
_monitor: Optional[DataSourceMonitor] = None

async def get_monitor() -> DataSourceMonitor:
    """獲取全局監控實例"""
    global _monitor
    if _monitor is None:
        data_manager = await get_data_manager()
        _monitor = DataSourceMonitor(data_manager)
        await _monitor.start_monitoring()
    return _monitor