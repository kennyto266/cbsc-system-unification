"""
Trading Metrics Module
交易指標監控模塊

Provides comprehensive metrics collection and analysis for the trading system
including performance monitoring, error tracking, and real-time alerts.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
from uuid import UUID
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict, deque
import statistics
import json

from ..trading.order_manager_v2 import OrderManagerV2
from ..trading.position_manager_v2 import PositionManagerV2
from ..trading.risk_manager import RiskManager
from ..trading.execution_service import ExecutionService


class MetricType(str, Enum):
    """指標類型"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


class AlertSeverity(str, Enum):
    """告警嚴重程度"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Metric:
    """指標數據"""
    name: str
    value: float
    metric_type: MetricType
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Alert:
    """告警"""
    alert_id: str
    name: str
    severity: AlertSeverity
    message: str
    metric_name: str
    threshold: float
    current_value: float
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    resolved: bool = False
    resolved_at: Optional[datetime] = None


@dataclass
class PerformanceReport:
    """性能報告"""
    period_start: datetime
    period_end: datetime
    total_orders: int
    successful_orders: int
    failed_orders: int
    average_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    throughput: float  # orders per second
    error_rate: float
    slippage_stats: Dict[str, float]
    execution_quality_score: float


class TradingMetricsCollector:
    """
    交易指標收集器

    負責：
    - 實時指標收集
    - 性能分析
    - 告警檢測
    - 報告生成
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger("trading_metrics")

        # Metrics storage
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.counters: Dict[str, float] = defaultdict(float)
        self.gauges: Dict[str, float] = defaultdict(float)
        self.histograms: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))

        # Performance data
        self.latency_data: deque = deque(maxlen=10000)
        self.execution_times: deque = deque(maxlen=10000)
        self.slippage_data: deque = deque(maxlen=1000)
        self.fill_rates: deque = deque(maxlen=1000)

        # Alerts
        self.alerts: List[Alert] = []
        self.alert_rules: Dict[str, Dict] = {}

        # Background tasks
        self._background_tasks: List[asyncio.Task] = []
        self._running = False
        self._shutdown_event = asyncio.Event()

        # Component references
        self.order_manager: Optional[OrderManagerV2] = None
        self.position_manager: Optional[PositionManagerV2] = None
        self.risk_manager: Optional[RiskManager] = None
        self.execution_service: Optional[ExecutionService] = None

        # Initialize alert rules
        self._initialize_alert_rules()

    async def initialize(self) -> None:
        """初始化指標收集器"""
        self.logger.info("Initializing trading metrics collector...")

        self._running = False
        self._shutdown_event.clear()

        # Start background tasks
        self._background_tasks = [
            asyncio.create_task(self._collect_metrics()),
            asyncio.create_task(self._check_alerts()),
            asyncio.create_task(self._generate_reports()),
            asyncio.create_task(self._cleanup_old_data())
        ]

        self.logger.info("Trading metrics collector initialized")

    async def shutdown(self) -> None:
        """關閉指標收集器"""
        self.logger.info("Shutting down trading metrics collector...")

        self._running = False
        self._shutdown_event.set()

        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        self.logger.info("Trading metrics collector shutdown complete")

    def register_components(
        self,
        order_manager: OrderManagerV2,
        position_manager: PositionManagerV2,
        risk_manager: RiskManager,
        execution_service: ExecutionService
    ) -> None:
        """註冊組件引用"""
        self.order_manager = order_manager
        self.position_manager = position_manager
        self.risk_manager = risk_manager
        self.execution_service = execution_service

    def record_counter(self, name: str, value: float = 1.0, labels: Dict[str, str] = None) -> None:
        """記錄計數器"""
        self.counters[name] += value
        self._store_metric(name, value, MetricType.COUNTER, labels)

    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None) -> None:
        """設置儀表盤值"""
        self.gauges[name] = value
        self._store_metric(name, value, MetricType.GAUGE, labels)

    def record_histogram(self, name: str, value: float, labels: Dict[str, str] = None) -> None:
        """記錄直方圖"""
        self.histograms[name].append(value)
        self._store_metric(name, value, MetricType.HISTOGRAM, labels)

    def record_latency(self, operation: str, latency_ms: float) -> None:
        """記錄延遲"""
        self.latency_data.append(latency_ms)
        self.record_histogram(f"{operation}_latency_ms", latency_ms)

    def record_execution_time(self, time_ms: float) -> None:
        """記錄執行時間"""
        self.execution_times.append(time_ms)
        self.record_histogram("execution_time_ms", time_ms)

    def record_slippage(self, slippage_pct: float) -> None:
        """記錄滑點"""
        self.slippage_data.append(slippage_pct)
        self.record_histogram("slippage_percentage", slippage_pct)

    def record_fill_rate(self, rate: float) -> None:
        """記錄成交率"""
        self.fill_rates.append(rate)
        self.set_gauge("current_fill_rate", rate)

    async def get_current_metrics(self) -> Dict[str, Any]:
        """獲取當前指標"""
        try:
            metrics = {
                "counters": dict(self.counters),
                "gauges": dict(self.gauges),
                "timestamp": datetime.utcnow().isoformat()
            }

            # Add histogram statistics
            for name, values in self.histograms.items():
                if values:
                    metrics[f"{name}_stats"] = {
                        "count": len(values),
                        "mean": statistics.mean(values),
                        "median": statistics.median(values),
                        "p95": self._percentile(values, 0.95),
                        "p99": self._percentile(values, 0.99),
                        "min": min(values),
                        "max": max(values)
                    }

            # Add component metrics
            if self.order_manager:
                metrics["order_manager"] = self.order_manager.get_metrics()

            if self.position_manager:
                metrics["position_manager"] = self.position_manager.get_metrics()

            if self.execution_service:
                metrics["execution_service"] = {
                    "average_execution_time": self.execution_service.average_execution_time
                }

            return metrics

        except Exception as e:
            self.logger.error(f"Error getting current metrics: {e}")
            return {}

    async def get_performance_report(
        self,
        period_minutes: int = 60
    ) -> Optional[PerformanceReport]:
        """獲取性能報告"""
        try:
            period_start = datetime.utcnow() - timedelta(minutes=period_minutes)
            period_end = datetime.utcnow()

            # Get order statistics
            total_orders = self.counters.get("total_orders", 0)
            successful_orders = self.counters.get("successful_orders", 0)
            failed_orders = self.counters.get("failed_orders", 0)

            # Calculate latency statistics
            recent_latencies = [
                l for l in self.latency_data
                if len(self.latency_data) > 0  # Simplified filtering
            ]

            if recent_latencies:
                average_latency = statistics.mean(recent_latencies)
                p95_latency = self._percentile(recent_latencies, 0.95)
                p99_latency = self._percentile(recent_latencies, 0.99)
            else:
                average_latency = p95_latency = p99_latency = 0

            # Calculate throughput
            throughput = total_orders / (period_minutes * 60) if period_minutes > 0 else 0

            # Calculate error rate
            error_rate = failed_orders / max(1, total_orders)

            # Calculate slippage statistics
            if self.slippage_data:
                slippage_stats = {
                    "mean": statistics.mean(self.slippage_data),
                    "median": statistics.median(self.slippage_data),
                    "p95": self._percentile(self.slippage_data, 0.95),
                    "max": max(self.slippage_data),
                    "min": min(self.slippage_data)
                }
            else:
                slippage_stats = {}

            # Calculate execution quality score (0-100)
            quality_score = self._calculate_quality_score(
                average_latency,
                error_rate,
                slippage_stats.get("mean", 0),
                statistics.mean(self.fill_rates) if self.fill_rates else 0
            )

            return PerformanceReport(
                period_start=period_start,
                period_end=period_end,
                total_orders=int(total_orders),
                successful_orders=int(successful_orders),
                failed_orders=int(failed_orders),
                average_latency_ms=average_latency,
                p95_latency_ms=p95_latency,
                p99_latency_ms=p99_latency,
                throughput=throughput,
                error_rate=error_rate,
                slippage_stats=slippage_stats,
                execution_quality_score=quality_score
            )

        except Exception as e:
            self.logger.error(f"Error generating performance report: {e}")
            return None

    async def create_alert_rule(
        self,
        name: str,
        metric_name: str,
        threshold: float,
        operator: str = "gt",
        severity: AlertSeverity = AlertSeverity.WARNING,
        duration_minutes: int = 5
    ) -> None:
        """創建告警規則"""
        self.alert_rules[name] = {
            "metric_name": metric_name,
            "threshold": threshold,
            "operator": operator,
            "severity": severity,
            "duration_minutes": duration_minutes,
            "created_at": datetime.utcnow()
        }

    async def get_active_alerts(self) -> List[Alert]:
        """獲取活躍告警"""
        return [alert for alert in self.alerts if not alert.resolved]

    def _store_metric(
        self,
        name: str,
        value: float,
        metric_type: MetricType,
        labels: Dict[str, str] = None
    ) -> None:
        """存儲指標"""
        metric = Metric(
            name=name,
            value=value,
            metric_type=metric_type,
            labels=labels or {}
        )
        self.metrics[name].append(metric)

    def _percentile(self, data: List[float], percentile: float) -> float:
        """計算百分位數"""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile)
        return sorted_data[min(index, len(sorted_data) - 1)]

    def _calculate_quality_score(
        self,
        latency_ms: float,
        error_rate: float,
        avg_slippage: float,
        avg_fill_rate: float
    ) -> float:
        """計算執行質量分數"""
        # Latency score (lower is better)
        latency_score = max(0, 100 - (latency_ms / 10))  # 10ms = 90 points

        # Error rate score (lower is better)
        error_score = max(0, 100 - (error_rate * 1000))  # 1% = 0 points

        # Slippage score (lower is better)
        slippage_score = max(0, 100 - (avg_slippage * 100))  # 1% = 0 points

        # Fill rate score (higher is better)
        fill_score = avg_fill_rate * 100

        # Weighted average
        total_score = (
            latency_score * 0.3 +
            error_score * 0.3 +
            slippage_score * 0.2 +
            fill_score * 0.2
        )

        return min(100, max(0, total_score))

    def _initialize_alert_rules(self) -> None:
        """初始化默認告警規則"""
        default_rules = [
            {
                "name": "high_latency",
                "metric_name": "execution_time_ms",
                "threshold": 1000,  # 1 second
                "operator": "gt",
                "severity": AlertSeverity.WARNING
            },
            {
                "name": "high_error_rate",
                "metric_name": "error_rate",
                "threshold": 0.05,  # 5%
                "operator": "gt",
                "severity": AlertSeverity.ERROR
            },
            {
                "name": "high_slippage",
                "metric_name": "slippage_percentage",
                "threshold": 0.5,  # 0.5%
                "operator": "gt",
                "severity": AlertSeverity.WARNING
            },
            {
                "name": "low_fill_rate",
                "metric_name": "current_fill_rate",
                "threshold": 0.9,  # 90%
                "operator": "lt",
                "severity": AlertSeverity.WARNING
            }
        ]

        for rule in default_rules:
            asyncio.create_task(self.create_alert_rule(**rule))

    async def _collect_metrics(self) -> None:
        """收集指標後台任務"""
        self.logger.info("Starting metrics collector...")

        while not self._shutdown_event.is_set():
            try:
                # Collect metrics from components
                if self.order_manager:
                    metrics = self.order_manager.get_metrics()
                    self.set_gauge("order_manager_total_orders", metrics.total_orders)
                    self.set_gauge("order_manager_success_rate", metrics.success_rate)
                    self.set_gauge("order_manager_error_rate", metrics.error_rate)

                if self.position_manager:
                    metrics = self.position_manager.get_metrics()
                    self.set_gauge("positions_tracked", metrics["positions_tracked"])
                    self.set_gauge("portfolio_count", metrics["portfolios"])

                if self.execution_service:
                    self.set_gauge("execution_avg_time", self.execution_service.average_execution_time)

                # Collect system metrics
                self.set_gauge("alert_count", len(await self.get_active_alerts()))

                await asyncio.sleep(5)  # Collect every 5 seconds

            except Exception as e:
                self.logger.error(f"Error collecting metrics: {e}")
                await asyncio.sleep(5)

    async def _check_alerts(self) -> None:
        """檢查告警後台任務"""
        self.logger.info("Starting alert checker...")

        while not self._shutdown_event.is_set():
            try:
                current_metrics = await self.get_current_metrics()

                for rule_name, rule in self.alert_rules.items():
                    metric_name = rule["metric_name"]
                    threshold = rule["threshold"]
                    operator = rule["operator"]

                    # Get current metric value
                    value = None
                    if f"{metric_name}_stats" in current_metrics:
                        value = current_metrics[f"{metric_name}_stats"]["mean"]
                    elif metric_name in current_metrics.get("gauges", {}):
                        value = current_metrics["gauges"][metric_name]

                    if value is None:
                        continue

                    # Check threshold
                    triggered = False
                    if operator == "gt" and value > threshold:
                        triggered = True
                    elif operator == "lt" and value < threshold:
                        triggered = True
                    elif operator == "eq" and value == threshold:
                        triggered = True

                    if triggered:
                        # Check if alert already exists
                        existing_alert = next(
                            (a for a in self.alerts
                             if a.metric_name == metric_name and not a.resolved),
                            None
                        )

                        if not existing_alert:
                            # Create new alert
                            alert = Alert(
                                alert_id=f"{rule_name}_{int(datetime.utcnow().timestamp())}",
                                name=rule_name,
                                severity=rule["severity"],
                                message=f"Alert: {metric_name} is {value:.4f} (threshold: {threshold})",
                                metric_name=metric_name,
                                threshold=threshold,
                                current_value=value
                            )
                            self.alerts.append(alert)
                            self.logger.warning(f"Alert triggered: {alert.message}")
                    else:
                        # Resolve existing alerts
                        existing_alerts = [
                            a for a in self.alerts
                            if a.metric_name == metric_name and not a.resolved
                        ]
                        for alert in existing_alerts:
                            alert.resolved = True
                            alert.resolved_at = datetime.utcnow()
                            self.logger.info(f"Alert resolved: {alert.name}")

                await asyncio.sleep(10)  # Check every 10 seconds

            except Exception as e:
                self.logger.error(f"Error checking alerts: {e}")
                await asyncio.sleep(10)

    async def _generate_reports(self) -> None:
        """生成報告後台任務"""
        self.logger.info("Starting report generator...")

        while not self._shutdown_event.is_set():
            try:
                # Generate hourly performance report
                report = await self.get_performance_report(period_minutes=60)

                if report:
                    self.logger.info(
                        f"Performance Report - Orders: {report.total_orders}, "
                        f"Success Rate: {(1 - report.error_rate) * 100:.2f}%, "
                        f"Avg Latency: {report.average_latency_ms:.2f}ms, "
                        f"Quality Score: {report.execution_quality_score:.2f}"
                    )

                await asyncio.sleep(3600)  # Generate every hour

            except Exception as e:
                self.logger.error(f"Error generating report: {e}")
                await asyncio.sleep(3600)

    async def _cleanup_old_data(self) -> None:
        """清理舊數據後台任務"""
        self.logger.info("Starting data cleanup...")

        while not self._shutdown_event.is_set():
            try:
                # Clean up old alerts (keep last 1000)
                if len(self.alerts) > 1000:
                    self.alerts = self.alerts[-1000:]

                # Clean up resolved alerts older than 24 hours
                cutoff = datetime.utcnow() - timedelta(hours=24)
                self.alerts = [
                    a for a in self.alerts
                    if not a.resolved or (a.resolved_at and a.resolved_at > cutoff)
                ]

                await asyncio.sleep(3600)  # Cleanup every hour

            except Exception as e:
                self.logger.error(f"Error in data cleanup: {e}")
                await asyncio.sleep(3600)