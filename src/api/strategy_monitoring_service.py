#!/usr/bin/env python3
"""
實時策略監控服務
Real-time Strategy Monitoring Service

提供策略實時狀態監控、性能追蹤和異常告警功能
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
import uuid

logger = logging.getLogger(__name__)

# ============================================================================
# 監控核心類型 (Monitoring Core Types)
# ============================================================================

class MonitoringLevel(str, Enum):
    """監控級別"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AlertType(str, Enum):
    """告警類型"""
    PERFORMANCE_DEGRADATION = "performance_degradation"
    EXECUTION_ERROR = "execution_error"
    RISK_LIMIT_BREACH = "risk_limit_breach"
    CONNECTIVITY_ISSUE = "connectivity_issue"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    STRATEGY_ANOMALY = "strategy_anomaly"

@dataclass
class StrategyMetric:
    """策略指標"""
    strategy_id: str
    timestamp: datetime
    metric_name: str
    metric_value: float
    unit: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class StrategyAlert:
    """策略告警"""
    alert_id: str
    strategy_id: str
    alert_type: AlertType
    level: MonitoringLevel
    message: str
    timestamp: datetime
    metric_value: Optional[float] = None
    threshold: Optional[float] = None
    is_resolved: bool = False
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class StrategyStatus:
    """策略狀態"""
    strategy_id: str
    is_running: bool
    last_update: datetime
    current_position: Optional[str] = None
    unrealized_pnl: float = 0.0
    daily_pnl: float = 0.0
    total_trades: int = 0
    error_count: int = 0
    last_signal: Optional[datetime] = None
    performance_metrics: Dict[str, float] = field(default_factory=dict)

# ============================================================================
# 監控配置 (Monitoring Configuration)
# ============================================================================

@dataclass
class MonitoringConfig:
    """監控配置"""
    update_interval: timedelta = timedelta(seconds=5)
    metrics_retention_period: timedelta = timedelta(days=7)
    alert_retention_period: timedelta = timedelta(days=30)
    max_concurrent_monitors: int = 100
    enable_auto_recovery: bool = True
    performance_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "max_drawdown": 0.15,  # 15%
        "min_sharpe_ratio": 0.5,
        "max_daily_loss": 0.05,  # 5%
        "min_win_rate": 0.3,    # 30%
        "max_error_rate": 0.1   # 10%
    })

# ============================================================================
# 實時監控服務 (Real-time Monitoring Service)
# ============================================================================

class StrategyMonitoringService:
    """策略監控服務"""

    def __init__(self, config: MonitoringConfig):
        self.config = config
        self.logger = logging.getLogger("strategy_monitoring")

        # 監控數據存儲
        self.strategy_statuses: Dict[str, StrategyStatus] = {}
        self.metrics_history: Dict[str, List[StrategyMetric]] = {}
        self.active_alerts: Dict[str, List[StrategyAlert]] = {}
        self.alert_history: Dict[str, List[StrategyAlert]] = {}

        # 監控任務
        self.monitoring_tasks: Dict[str, asyncio.Task] = {}
        self.is_running = False

        # 回調函數
        self.status_callbacks: List[Callable[[str, StrategyStatus], None]] = []
        self.alert_callbacks: List[Callable[[StrategyAlert], None]] = []
        self.metric_callbacks: List[Callable[[StrategyMetric], None]] = []

        # 異常檢測規則
        self.anomaly_detectors: List[Callable[[StrategyStatus], Optional[StrategyAlert]]] = []

    async def start_monitoring(self):
        """啟動監控服務"""
        try:
            self.is_running = True
            self.logger.info("策略監控服務啟動")

            # 啟動定期清理任務
            asyncio.create_task(self._cleanup_old_data())

            self.logger.info("策略監控服務啟動成功")
            return True

        except Exception as e:
            self.logger.error(f"啟動監控服務失敗: {e}")
            return False

    async def stop_monitoring(self):
        """停止監控服務"""
        try:
            self.is_running = False

            # 停止所有監控任務
            for task in self.monitoring_tasks.values():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

            self.monitoring_tasks.clear()
            self.logger.info("策略監控服務已停止")

        except Exception as e:
            self.logger.error(f"停止監控服務失敗: {e}")

    async def add_strategy_monitor(self, strategy_id: str, initial_status: Optional[StrategyStatus] = None):
        """添加策略監控"""
        try:
            if strategy_id in self.monitoring_tasks:
                self.logger.warning(f"策略已在監控中: {strategy_id}")
                return False

            if len(self.monitoring_tasks) >= self.config.max_concurrent_monitors:
                raise RuntimeError(f"超出最大監控數量: {self.config.max_concurrent_monitors}")

            # 初始化策略狀態
            if initial_status:
                self.strategy_statuses[strategy_id] = initial_status
            else:
                self.strategy_statuses[strategy_id] = StrategyStatus(
                    strategy_id=strategy_id,
                    is_running=False,
                    last_update=datetime.now()
                )

            # 初始化監控數據
            self.metrics_history[strategy_id] = []
            self.active_alerts[strategy_id] = []
            self.alert_history[strategy_id] = []

            # 啟動監控任務
            task = asyncio.create_task(self._monitor_strategy_loop(strategy_id))
            self.monitoring_tasks[strategy_id] = task

            self.logger.info(f"策略監控已添加: {strategy_id}")
            return True

        except Exception as e:
            self.logger.error(f"添加策略監控失敗: {e}")
            return False

    async def remove_strategy_monitor(self, strategy_id: str):
        """移除策略監控"""
        try:
            if strategy_id not in self.monitoring_tasks:
                self.logger.warning(f"策略未在監控中: {strategy_id}")
                return False

            # 停止監控任務
            task = self.monitoring_tasks[strategy_id]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

            # 清理數據
            del self.monitoring_tasks[strategy_id]
            if strategy_id in self.strategy_statuses:
                del self.strategy_statuses[strategy_id]
            if strategy_id in self.metrics_history:
                del self.metrics_history[strategy_id]
            if strategy_id in self.active_alerts:
                del self.active_alerts[strategy_id]

            self.logger.info(f"策略監控已移除: {strategy_id}")
            return True

        except Exception as e:
            self.logger.error(f"移除策略監控失敗: {e}")
            return False

    async def update_strategy_status(self, strategy_id: str, status_update: Dict[str, Any]):
        """更新策略狀態"""
        try:
            if strategy_id not in self.strategy_statuses:
                self.logger.warning(f"策略未在監控中: {strategy_id}")
                return

            status = self.strategy_statuses[strategy_id]

            # 更新狀態字段
            for key, value in status_update.items():
                if hasattr(status, key):
                    setattr(status, key, value)

            status.last_update = datetime.now()

            # 記錄指標
            await self._record_metrics(strategy_id, status)

            # 異常檢測
            await self._detect_anomalies(strategy_id, status)

            # 通知狀態變更
            await self._notify_status_change(strategy_id, status)

            self.logger.debug(f"策略狀態已更新: {strategy_id}")

        except Exception as e:
            self.logger.error(f"更新策略狀態失敗: {e}")

    async def get_strategy_status(self, strategy_id: str) -> Optional[StrategyStatus]:
        """獲取策略狀態"""
        return self.strategy_statuses.get(strategy_id)

    async def get_all_strategies_status(self) -> Dict[str, StrategyStatus]:
        """獲取所有策略狀態"""
        return self.strategy_statuses.copy()

    async def get_strategy_metrics(
        self,
        strategy_id: str,
        metric_name: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[StrategyMetric]:
        """獲取策略指標"""
        try:
            metrics = self.metrics_history.get(strategy_id, [])

            # 過濾指標名稱
            if metric_name:
                metrics = [m for m in metrics if m.metric_name == metric_name]

            # 過濾時間範圍
            if start_time:
                metrics = [m for m in metrics if m.timestamp >= start_time]
            if end_time:
                metrics = [m for m in metrics if m.timestamp <= end_time]

            return metrics

        except Exception as e:
            self.logger.error(f"獲取策略指標失敗: {e}")
            return []

    async def get_active_alerts(self, strategy_id: Optional[str] = None) -> List[StrategyAlert]:
        """獲取活躍告警"""
        try:
            if strategy_id:
                return self.active_alerts.get(strategy_id, [])
            else:
                all_alerts = []
                for alerts in self.active_alerts.values():
                    all_alerts.extend(alerts)
                return all_alerts

        except Exception as e:
            self.logger.error(f"獲取活躍告警失敗: {e}")
            return []

    async def acknowledge_alert(self, alert_id: str, strategy_id: str) -> bool:
        """確認告警"""
        try:
            if strategy_id not in self.active_alerts:
                return False

            for i, alert in enumerate(self.active_alerts[strategy_id]):
                if alert.alert_id == alert_id:
                    # 移動到歷史記錄
                    alert.is_resolved = True
                    alert.resolved_at = datetime.now()

                    self.active_alerts[strategy_id].pop(i)
                    self.alert_history.setdefault(strategy_id, []).append(alert)

                    self.logger.info(f"告警已確認: {alert_id}")
                    return True

            return False

        except Exception as e:
            self.logger.error(f"確認告警失敗: {e}")
            return False

    def add_status_callback(self, callback: Callable[[str, StrategyStatus], None]):
        """添加狀態變更回調"""
        self.status_callbacks.append(callback)

    def add_alert_callback(self, callback: Callable[[StrategyAlert], None]):
        """添加告警回調"""
        self.alert_callbacks.append(callback)

    def add_metric_callback(self, callback: Callable[[StrategyMetric], None]):
        """添加指標回調"""
        self.metric_callbacks.append(callback)

    # 私有方法
    async def _monitor_strategy_loop(self, strategy_id: str):
        """策略監控循環"""
        try:
            while self.is_running:
                status = self.strategy_statuses.get(strategy_id)
                if not status:
                    break

                # 檢查策略健康狀態
                await self._check_strategy_health(strategy_id, status)

                # 等待下次監控
                await asyncio.sleep(self.config.update_interval.total_seconds())

        except asyncio.CancelledError:
            self.logger.info(f"策略監控循環已取消: {strategy_id}")
        except Exception as e:
            self.logger.error(f"策略監控循環失敗: {strategy_id}, {e}")

    async def _check_strategy_health(self, strategy_id: str, status: StrategyStatus):
        """檢查策略健康狀態"""
        try:
            current_time = datetime.now()
            time_since_update = current_time - status.last_update

            # 檢查更新時間
            if status.is_running and time_since_update > timedelta(minutes=5):
                await self._create_alert(
                    strategy_id,
                    AlertType.CONNECTIVITY_ISSUE,
                    MonitoringLevel.WARNING,
                    f"策略超過5分鐘未更新"
                )

            # 檢查性能指標
            await self._check_performance_metrics(strategy_id, status)

            # 檢查錯誤率
            if status.error_count > 10:
                await self._create_alert(
                    strategy_id,
                    AlertType.EXECUTION_ERROR,
                    MonitoringLevel.ERROR,
                    f"策略錯誤次數過多: {status.error_count}"
                )

        except Exception as e:
            self.logger.error(f"檢查策略健康狀態失敗: {e}")

    async def _check_performance_metrics(self, strategy_id: str, status: StrategyStatus):
        """檢查性能指標"""
        try:
            metrics = status.performance_metrics

            # 檢查最大回撤
            if "max_drawdown" in metrics:
                max_drawdown = metrics["max_drawdown"]
                threshold = self.config.performance_thresholds["max_drawdown"]
                if max_drawdown > threshold:
                    await self._create_alert(
                        strategy_id,
                        AlertType.RISK_LIMIT_BREACH,
                        MonitoringLevel.CRITICAL,
                        f"最大回撤超過閾值: {max_drawdown:.2%} > {threshold:.2%}",
                        metric_value=max_drawdown,
                        threshold=threshold
                    )

            # 檢查夏普比率
            if "sharpe_ratio" in metrics and metrics["sharpe_ratio"] is not None:
                sharpe_ratio = metrics["sharpe_ratio"]
                threshold = self.config.performance_thresholds["min_sharpe_ratio"]
                if sharpe_ratio < threshold:
                    await self._create_alert(
                        strategy_id,
                        AlertType.PERFORMANCE_DEGRADATION,
                        MonitoringLevel.WARNING,
                        f"夏普比率過低: {sharpe_ratio:.2f} < {threshold:.2f}",
                        metric_value=sharpe_ratio,
                        threshold=threshold
                    )

            # 檢查日收益率
            if "daily_return" in metrics:
                daily_return = metrics["daily_return"]
                threshold = self.config.performance_thresholds["max_daily_loss"]
                if daily_return < -threshold:
                    await self._create_alert(
                        strategy_id,
                        AlertType.PERFORMANCE_DEGRADATION,
                        MonitoringLevel.ERROR,
                        f"日損失過大: {daily_return:.2%} < -{threshold:.2%}",
                        metric_value=daily_return,
                        threshold=-threshold
                    )

        except Exception as e:
            self.logger.error(f"檢查性能指標失敗: {e}")

    async def _record_metrics(self, strategy_id: str, status: StrategyStatus):
        """記錄指標"""
        try:
            timestamp = datetime.now()

            # 記錄基本指標
            basic_metrics = [
                ("unrealized_pnl", status.unrealized_pnl, "currency"),
                ("daily_pnl", status.daily_pnl, "currency"),
                ("total_trades", status.total_trades, "count"),
                ("error_count", status.error_count, "count")
            ]

            for metric_name, value, unit in basic_metrics:
                metric = StrategyMetric(
                    strategy_id=strategy_id,
                    timestamp=timestamp,
                    metric_name=metric_name,
                    metric_value=float(value),
                    unit=unit
                )
                await self._add_metric(metric)

            # 記錄性能指標
            for metric_name, value in status.performance_metrics.items():
                if value is not None:
                    metric = StrategyMetric(
                        strategy_id=strategy_id,
                        timestamp=timestamp,
                        metric_name=metric_name,
                        metric_value=float(value)
                    )
                    await self._add_metric(metric)

        except Exception as e:
            self.logger.error(f"記錄指標失敗: {e}")

    async def _add_metric(self, metric: StrategyMetric):
        """添加指標"""
        try:
            if metric.strategy_id not in self.metrics_history:
                self.metrics_history[metric.strategy_id] = []

            self.metrics_history[metric.strategy_id].append(metric)

            # 通知指標回調
            for callback in self.metric_callbacks:
                try:
                    callback(metric)
                except Exception as e:
                    self.logger.error(f"指標回調執行失敗: {e}")

        except Exception as e:
            self.logger.error(f"添加指標失敗: {e}")

    async def _detect_anomalies(self, strategy_id: str, status: StrategyStatus):
        """異常檢測"""
        try:
            for detector in self.anomaly_detectors:
                alert = detector(status)
                if alert:
                    await self._add_alert(alert)

        except Exception as e:
            self.logger.error(f"異常檢測失敗: {e}")

    async def _create_alert(
        self,
        strategy_id: str,
        alert_type: AlertType,
        level: MonitoringLevel,
        message: str,
        metric_value: Optional[float] = None,
        threshold: Optional[float] = None
    ):
        """創建告警"""
        try:
            alert = StrategyAlert(
                alert_id=str(uuid.uuid4()),
                strategy_id=strategy_id,
                alert_type=alert_type,
                level=level,
                message=message,
                timestamp=datetime.now(),
                metric_value=metric_value,
                threshold=threshold
            )

            await self._add_alert(alert)

        except Exception as e:
            self.logger.error(f"創建告警失敗: {e}")

    async def _add_alert(self, alert: StrategyAlert):
        """添加告警"""
        try:
            if alert.strategy_id not in self.active_alerts:
                self.active_alerts[alert.strategy_id] = []

            self.active_alerts[alert.strategy_id].append(alert)

            # 通知告警回調
            for callback in self.alert_callbacks:
                try:
                    callback(alert)
                except Exception as e:
                    self.logger.error(f"告警回調執行失敗: {e}")

            self.logger.warning(f"新告警: [{alert.level.value.upper()}] {alert.strategy_id} - {alert.message}")

        except Exception as e:
            self.logger.error(f"添加告警失敗: {e}")

    async def _notify_status_change(self, strategy_id: str, status: StrategyStatus):
        """通知狀態變更"""
        try:
            for callback in self.status_callbacks:
                try:
                    callback(strategy_id, status)
                except Exception as e:
                    self.logger.error(f"狀態回調執行失敗: {e}")

        except Exception as e:
            self.logger.error(f"通知狀態變更失敗: {e}")

    async def _cleanup_old_data(self):
        """定期清理舊數據"""
        try:
            while self.is_running:
                current_time = datetime.now()

                # 清理舊指標
                for strategy_id, metrics in self.metrics_history.items():
                    cutoff_time = current_time - self.config.metrics_retention_period
                    self.metrics_history[strategy_id] = [
                        m for m in metrics if m.timestamp > cutoff_time
                    ]

                # 清理解決的告警
                for strategy_id, alerts in self.alert_history.items():
                    cutoff_time = current_time - self.config.alert_retention_period
                    self.alert_history[strategy_id] = [
                        a for a in alerts if (a.resolved_at and a.resolved_at > cutoff_time) or a.timestamp > cutoff_time
                    ]

                # 每小時清理一次
                await asyncio.sleep(3600)

        except asyncio.CancelledError:
            self.logger.info("數據清理任務已取消")
        except Exception as e:
            self.logger.error(f"數據清理失敗: {e}")

# ============================================================================
# 全局監控服務實例
# ============================================================================

_monitoring_service: Optional[StrategyMonitoringService] = None

def get_monitoring_service() -> StrategyMonitoringService:
    """獲取全局監控服務實例"""
    global _monitoring_service
    if _monitoring_service is None:
        config = MonitoringConfig()
        _monitoring_service = StrategyMonitoringService(config)
    return _monitoring_service

async def initialize_monitoring_service():
    """初始化監控服務"""
    service = get_monitoring_service()
    await service.start_monitoring()
    logger.info("監控服務已初始化")

async def shutdown_monitoring_service():
    """關閉監控服務"""
    service = get_monitoring_service()
    await service.stop_monitoring()
    logger.info("監控服務已關閉")

# ============================================================================
# 導出
# ============================================================================

__all__ = [
    "StrategyMonitoringService",
    "get_monitoring_service",
    "initialize_monitoring_service",
    "shutdown_monitoring_service",
    "StrategyMetric",
    "StrategyAlert",
    "StrategyStatus",
    "MonitoringLevel",
    "AlertType",
    "MonitoringConfig"
]