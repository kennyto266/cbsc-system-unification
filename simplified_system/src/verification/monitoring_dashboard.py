#!/usr / bin / env python3
"""
Phase 5: System Integration and Optimization
監控儀表板與即時指標系統 - Monitoring Dashboard

提供實時性能監控、可視化儀表板和警報管理：
- 實時性能指標監控
- Web儀表板界面
- 數據可視化和圖表
- 警報規則和通知
- 歷史數據存儲和分析
- API健康檢查
"""

import asyncio
import json
import logging
import time
import uuid
from collections import defaultdict, deque
from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Dict, List, Optional

import GPUtil
import plotly.graph_objs as go
import plotly.utils

# 系統監控
import psutil

# Web框架和可視化
from flask import Flask, Response, jsonify, render_template, request
from plotly.subplots import make_subplots

from .async_processor import AsyncProcessor, get_processor_metrics
from .intelligent_cache import IntelligentCache, get_cache_stats

# 導入驗證系統組件
from .unified_verification_manager import UnifiedVerificationManager, get_system_metrics

# Setup logging
logger = logging.getLogger(__name__)


@dataclass
class MetricPoint:
    """指標數據點"""

    timestamp: float
    value: float
    metadata: Dict[str, Any] = field(default_factory = dict)


@dataclass
class AlertRule:
    """警報規則"""

    rule_id: str
    name: str
    metric_path: str  # 指標路徑，如 "performance.avg_response_time"
    operator: str  # ">", "<", ">=", "<=", "==", "!="
    threshold: float
    severity: str  # "low", "medium", "high", "critical"
    enabled: bool = True
    cooldown_seconds: int = 300  # 冷卻時間
    description: str = ""
    created_at: float = field(default_factory = time.time)
    last_triggered: Optional[float] = None
    trigger_count: int = 0

    def should_trigger(self, current_value: float) -> bool:
        """檢查是否應觸發警報"""
        if not self.enabled:
            return False

        # 檢查冷卻時間
        if (
            self.last_triggered
            and time.time() - self.last_triggered < self.cooldown_seconds
        ):
            return False

        # 檢查閾值
        if self.operator == ">":
            return current_value > self.threshold
        elif self.operator == "<":
            return current_value < self.threshold
        elif self.operator == ">=":
            return current_value >= self.threshold
        elif self.operator == "<=":
            return current_value <= self.threshold
        elif self.operator == "==":
            return current_value == self.threshold
        elif self.operator == "!=":
            return current_value != self.threshold

        return False

    def trigger(self):
        """觸發警報"""
        self.last_triggered = time.time()
        self.trigger_count += 1


class MetricsCollector:
    """指標收集器"""

    def __init__(self, collection_interval: int = 10):
        self.collection_interval = collection_interval
        self.metrics_data = defaultdict(
            lambda: deque(maxlen = 1000)
        )  # 保留最近1000個數據點
        self.is_collecting = False
        self.collection_task = None

        # 自定義指標收集器
        self.custom_collectors = {}

        logger.info("MetricsCollector initialized")

    async def start_collection(self):
        """開始指標收集"""
        if self.is_collecting:
            return

        self.is_collecting = True
        self.collection_task = asyncio.create_task(self._collection_loop())
        logger.info("Metrics collection started")

    async def stop_collection(self):
        """停止指標收集"""
        if not self.is_collecting:
            return

        self.is_collecting = False

        if self.collection_task:
            self.collection_task.cancel()
            try:
                await self.collection_task
            except asyncio.CancelledError:
                pass

        logger.info("Metrics collection stopped")

    async def _collection_loop(self):
        """收集循環"""
        while self.is_collecting:
            try:
                # 收集系統指標
                await self._collect_system_metrics()

                # 收集驗證系統指標
                await self._collect_verification_metrics()

                # 收集緩存指標
                await self._collect_cache_metrics()

                # 收集異步處理器指標
                await self._collect_processor_metrics()

                # 收集自定義指標
                await self._collect_custom_metrics()

                # 等待下次收集
                await asyncio.sleep(self.collection_interval)

            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
                await asyncio.sleep(self.collection_interval)

    async def _collect_system_metrics(self):
        """收集系統指標"""
        current_time = time.time()

        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval = 1)
        self._add_metric_point("system.cpu_usage", current_time, cpu_percent)

        # 內存使用率
        memory = psutil.virtual_memory()
        self._add_metric_point("system.memory_usage", current_time, memory.percent)
        self._add_metric_point(
            "system.memory_used_gb", current_time, memory.used / (1024 * *3)
        )

        # 磁盤使用率
        disk = psutil.disk_usage("/")
        self._add_metric_point("system.disk_usage", current_time, disk.percent)
        self._add_metric_point(
            "system.disk_used_gb", current_time, disk.used / (1024 * *3)
        )

        # GPU使用率（如果可用）
        try:
            gpus = GPUtil.getGPUs()
            for i, gpu in enumerate(gpus):
                self._add_metric_point(
                    f"system.gpu_{i}_usage", current_time, gpu.load * 100
                )
                self._add_metric_point(
                    f"system.gpu_{i}_memory", current_time, gpu.memoryUtil * 100
                )
        except Exception:
            pass

        # 網絡統計
        network = psutil.net_io_counters()
        self._add_metric_point(
            "system.network_bytes_sent", current_time, network.bytes_sent
        )
        self._add_metric_point(
            "system.network_bytes_recv", current_time, network.bytes_recv
        )

    async def _collect_verification_metrics(self):
        """收集驗證系統指標"""
        current_time = time.time()

        try:
            # 獲取系統指標
            metrics = get_system_metrics()

            self._add_metric_point(
                "verification.total_verifications",
                current_time,
                metrics.total_verifications,
            )
            self._add_metric_point(
                "verification.successful_verifications",
                current_time,
                metrics.successful_verifications,
            )
            self._add_metric_point(
                "verification.failed_verifications",
                current_time,
                metrics.failed_verifications,
            )
            self._add_metric_point(
                "verification.success_rate",
                current_time,
                (
                    metrics.successful_verifications / metrics.total_verifications
                    if metrics.total_verifications > 0
                    else 0
                ),
            )
            self._add_metric_point(
                "verification.avg_response_time_ms",
                current_time,
                metrics.avg_response_time_ms,
            )
            self._add_metric_point(
                "verification.cache_hit_rate", current_time, metrics.cache_hit_rate
            )
            self._add_metric_point(
                "verification.error_rate", current_time, metrics.error_rate
            )
            self._add_metric_point(
                "verification.throughput_per_second",
                current_time,
                metrics.throughput_per_second,
            )

        except Exception as e:
            logger.debug(f"Error collecting verification metrics: {e}")

    async def _collect_cache_metrics(self):
        """收集緩存指標"""
        current_time = time.time()

        try:
            # 獲取緩存統計
            stats = get_cache_stats()

            self._add_metric_point(
                "cache.entries_count", current_time, stats.get("entries_count", 0)
            )
            self._add_metric_point(
                "cache.memory_usage_mb", current_time, stats.get("memory_usage_mb", 0)
            )
            self._add_metric_point(
                "cache.hit_rate", current_time, stats.get("hit_rate", 0)
            )
            self._add_metric_point("cache.hits", current_time, stats.get("hits", 0))
            self._add_metric_point("cache.misses", current_time, stats.get("misses", 0))
            self._add_metric_point(
                "cache.evictions", current_time, stats.get("evictions", 0)
            )
            self._add_metric_point(
                "cache.compressions", current_time, stats.get("compressions", 0)
            )

        except Exception as e:
            logger.debug(f"Error collecting cache metrics: {e}")

    async def _collect_processor_metrics(self):
        """收集異步處理器指標"""
        current_time = time.time()

        try:
            # 獲取處理器指標
            metrics = get_processor_metrics()

            perf_metrics = metrics.get("performance_metrics", {})
            self._add_metric_point(
                "processor.total_tasks",
                current_time,
                perf_metrics.get("total_tasks", 0),
            )
            self._add_metric_point(
                "processor.successful_tasks",
                current_time,
                perf_metrics.get("successful_tasks", 0),
            )
            self._add_metric_point(
                "processor.failed_tasks",
                current_time,
                perf_metrics.get("failed_tasks", 0),
            )
            self._add_metric_point(
                "processor.avg_execution_time",
                current_time,
                perf_metrics.get("avg_execution_time", 0),
            )
            self._add_metric_point(
                "processor.throughput_per_second",
                current_time,
                perf_metrics.get("throughput_per_second", 0),
            )

            scheduler_stats = metrics.get("scheduler_stats", {})
            self._add_metric_point(
                "processor.running_tasks",
                current_time,
                scheduler_stats.get("running_tasks", 0),
            )
            self._add_metric_point(
                "processor.completed_tasks",
                current_time,
                scheduler_stats.get("completed_tasks", 0),
            )

        except Exception as e:
            logger.debug(f"Error collecting processor metrics: {e}")

    async def _collect_custom_metrics(self):
        """收集自定義指標"""
        current_time = time.time()

        for metric_name, collector in self.custom_collectors.items():
            try:
                value = await collector()
                self._add_metric_point(f"custom.{metric_name}", current_time, value)
            except Exception as e:
                logger.debug(f"Error collecting custom metric {metric_name}: {e}")

    def _add_metric_point(
        self,
        metric_name: str,
        timestamp: float,
        value: float,
        metadata: Dict[str, Any] = None,
    ):
        """添加指標數據點"""
        point = MetricPoint(timestamp, value, metadata or {})
        self.metrics_data[metric_name].append(point)

    def add_custom_collector(self, metric_name: str, collector: Callable[[], float]):
        """添加自定義指標收集器"""
        self.custom_collectors[metric_name] = collector

    def get_metric_data(
        self,
        metric_name: str,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
    ) -> List[MetricPoint]:
        """獲取指標數據"""
        data = list(self.metrics_data[metric_name])

        if start_time:
            data = [point for point in data if point.timestamp >= start_time]

        if end_time:
            data = [point for point in data if point.timestamp <= end_time]

        return data

    def get_latest_metric(self, metric_name: str) -> Optional[MetricPoint]:
        """獲取最新指標"""
        data = self.metrics_data[metric_name]
        return data[-1] if data else None

    def get_all_metrics_names(self) -> List[str]:
        """獲取所有指標名稱"""
        return list(self.metrics_data.keys())


class AlertManager:
    """警報管理器"""

    def __init__(self):
        self.alert_rules = {}
        self.active_alerts = {}
        self.alert_history = deque(maxlen = 1000)
        self.alert_callbacks = []

        logger.info("AlertManager initialized")

    def add_rule(self, rule: AlertRule):
        """添加警報規則"""
        self.alert_rules[rule.rule_id] = rule
        logger.info(f"Alert rule added: {rule.name}")

    def remove_rule(self, rule_id: str):
        """移除警報規則"""
        if rule_id in self.alert_rules:
            del self.alert_rules[rule_id]
            logger.info(f"Alert rule removed: {rule_id}")

    def add_alert_callback(self, callback: Callable[[AlertRule, float], None]):
        """添加警報回調"""
        self.alert_callbacks.append(callback)

    async def check_alerts(self, metrics_collector: MetricsCollector):
        """檢查警報"""
        for rule in self.alert_rules.values():
            try:
                # 獲取對應指標的最新值
                latest_point = metrics_collector.get_latest_metric(rule.metric_path)

                if latest_point:
                    if rule.should_trigger(latest_point.value):
                        await self._trigger_alert(rule, latest_point.value)
                    else:
                        # 如果警報條件不再滿足，清除活躍警報
                        if rule.rule_id in self.active_alerts:
                            await self._resolve_alert(rule.rule_id)

            except Exception as e:
                logger.error(f"Error checking alert rule {rule.rule_id}: {e}")

    async def _trigger_alert(self, rule: AlertRule, current_value: float):
        """觸發警報"""
        rule.trigger()

        # 記錄警報
        alert = {
            "rule_id": rule.rule_id,
            "rule_name": rule.name,
            "severity": rule.severity,
            "metric_path": rule.metric_path,
            "current_value": current_value,
            "threshold": rule.threshold,
            "operator": rule.operator,
            "triggered_at": time.time(),
            "description": rule.description,
        }

        self.active_alerts[rule.rule_id] = alert
        self.alert_history.append(alert)

        logger.warning(
            f"Alert triggered: {rule.name} - {rule.metric_path} {rule.operator} {rule.threshold} (current: {current_value})"
        )

        # 執行回調
        for callback in self.alert_callbacks:
            try:
                await callback(rule, current_value)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")

    async def _resolve_alert(self, rule_id: str):
        """解決警報"""
        if rule_id in self.active_alerts:
            alert = self.active_alerts[rule_id]
            alert["resolved_at"] = time.time()

            del self.active_alerts[rule_id]
            logger.info(f"Alert resolved: {alert['rule_name']}")

    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """獲取活躍警報"""
        return list(self.active_alerts.values())

    def get_alert_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """獲取警報歷史"""
        return list(self.alert_history)[-limit:]


class MonitoringDashboard:
    """監控儀表板"""

    def __init__(self, host: str = "0.0.0.0", port: int = 8080):
        self.host = host
        self.port = port
        self.app = Flask(__name__)
        self.app.config["JSON_SORT_KEYS"] = False

        # 初始化組件
        self.metrics_collector = MetricsCollector()
        self.alert_manager = AlertManager()

        # 設置路由
        self._setup_routes()

        logger.info(f"MonitoringDashboard initialized - {host}:{port}")

    def _setup_routes(self):
        """設置Flask路由"""

        @self.app.route("/")
        def dashboard():
            """主儀表板頁面"""
            return render_template("dashboard.html")

        @self.app.route("/api / metrics")
        def get_metrics():
            """獲取所有指標"""
            metrics = {}
            for metric_name in self.metrics_collector.get_all_metrics_names():
                data = self.metrics_collector.get_metric_data(metric_name)
                metrics[metric_name] = [
                    {
                        "timestamp": point.timestamp,
                        "value": point.value,
                        "metadata": point.metadata,
                    }
                    for point in data
                ]

            return jsonify(metrics)

        @self.app.route("/api / metrics/<metric_name>")
        def get_metric(metric_name):
            """獲取特定指標"""
            start_time = request.args.get("start_time", type = float)
            end_time = request.args.get("end_time", type = float)

            data = self.metrics_collector.get_metric_data(
                metric_name, start_time, end_time
            )
            result = [
                {
                    "timestamp": point.timestamp,
                    "value": point.value,
                    "metadata": point.metadata,
                }
                for point in data
            ]

            return jsonify(result)

        @self.app.route("/api / metrics/<metric_name>/latest")
        def get_latest_metric(metric_name):
            """獲取最新指標"""
            point = self.metrics_collector.get_latest_metric(metric_name)
            if point:
                return jsonify(
                    {
                        "timestamp": point.timestamp,
                        "value": point.value,
                        "metadata": point.metadata,
                    }
                )
            else:
                return jsonify({"error": "Metric not found"}), 404

        @self.app.route("/api / metrics / summary")
        def get_metrics_summary():
            """獲取指標摘要"""
            summary = {}

            for metric_name in self.metrics_collector.get_all_metrics_names():
                latest_point = self.metrics_collector.get_latest_metric(metric_name)
                if latest_point:
                    summary[metric_name] = {
                        "latest_value": latest_point.value,
                        "latest_timestamp": latest_point.timestamp,
                        "data_points_count": len(
                            self.metrics_collector.metrics_data[metric_name]
                        ),
                    }

            return jsonify(summary)

        @self.app.route("/api / alerts / rules")
        def get_alert_rules():
            """獲取警報規則"""
            rules = {}
            for rule_id, rule in self.alert_manager.alert_rules.items():
                rules[rule_id] = asdict(rule)

            return jsonify(rules)

        @self.app.route("/api / alerts / rules", methods=["POST"])
        def add_alert_rule():
            """添加警報規則"""
            data = request.json

            rule = AlertRule(
                rule_id = data.get("rule_id", str(uuid.uuid4())),
                name = data.get("name", ""),
                metric_path = data.get("metric_path", ""),
                operator = data.get("operator", ">"),
                threshold = data.get("threshold", 0),
                severity = data.get("severity", "medium"),
                description = data.get("description", ""),
            )

            self.alert_manager.add_rule(rule)
            return jsonify(asdict(rule))

        @self.app.route("/api / alerts / rules/<rule_id>", methods=["DELETE"])
        def delete_alert_rule(rule_id):
            """刪除警報規則"""
            self.alert_manager.remove_rule(rule_id)
            return jsonify({"success": True})

        @self.app.route("/api / alerts / active")
        def get_active_alerts():
            """獲取活躍警報"""
            return jsonify(self.alert_manager.get_active_alerts())

        @self.app.route("/api / alerts / history")
        def get_alert_history():
            """獲取警報歷史"""
            limit = request.args.get("limit", 100, type = int)
            return jsonify(self.alert_manager.get_alert_history(limit))

        @self.app.route("/api / health")
        def health_check():
            """健康檢查"""
            try:
                # 檢查各個組件的狀態
                system_metrics = get_system_metrics()
                cache_stats = get_cache_stats()
                processor_metrics = get_processor_metrics()

                health_status = {
                    "status": "healthy",
                    "timestamp": time.time(),
                    "components": {
                        "verification_system": (
                            "healthy" if system_metrics else "unhealthy"
                        ),
                        "cache_system": "healthy" if cache_stats else "unhealthy",
                        "processor_system": (
                            "healthy" if processor_metrics else "unhealthy"
                        ),
                    },
                    "system_metrics": {
                        "cpu_usage": psutil.cpu_percent(),
                        "memory_usage": psutil.virtual_memory().percent,
                        "disk_usage": psutil.disk_usage("/").percent,
                    },
                }

                return jsonify(health_status)

            except Exception as e:
                return (
                    jsonify(
                        {
                            "status": "unhealthy",
                            "error": str(e),
                            "timestamp": time.time(),
                        }
                    ),
                    500,
                )

        @self.app.route("/api / charts/<chart_type>")
        def get_chart(chart_type):
            """獲取圖表數據"""
            try:
                if chart_type == "system_overview":
                    return jsonify(self._create_system_overview_chart())
                elif chart_type == "verification_performance":
                    return jsonify(self._create_verification_performance_chart())
                elif chart_type == "cache_performance":
                    return jsonify(self._create_cache_performance_chart())
                else:
                    return jsonify({"error": "Unknown chart type"}), 404

            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api / performance / realtime")
        def get_realtime_performance():
            """獲取實時性能數據"""
            try:
                # 獲取最新系統指標
                cpu_usage = psutil.cpu_percent()
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage("/")

                # 獲取驗證系統指標
                verification_metrics = get_system_metrics()

                # 獲取緩存統統指標
                cache_stats = get_cache_stats()

                # 獲取處理器指標
                processor_metrics = get_processor_metrics()

                return jsonify(
                    {
                        "timestamp": time.time(),
                        "system": {
                            "cpu_usage": cpu_usage,
                            "memory_usage": memory.percent,
                            "memory_available_gb": memory.available / (1024 * *3),
                            "disk_usage": disk.percent,
                            "disk_free_gb": disk.free / (1024 * *3),
                        },
                        "verification": {
                            "total_verifications": verification_metrics.total_verifications,
                            "success_rate": (
                                verification_metrics.successful_verifications
                                / verification_metrics.total_verifications
                                if verification_metrics.total_verifications > 0
                                else 0
                            ),
                            "avg_response_time_ms": verification_metrics.avg_response_time_ms,
                            "cache_hit_rate": verification_metrics.cache_hit_rate,
                            "error_rate": verification_metrics.error_rate,
                            "throughput_per_second": verification_metrics.throughput_per_second,
                        },
                        "cache": {
                            "entries_count": cache_stats.get("entries_count", 0),
                            "memory_usage_mb": cache_stats.get("memory_usage_mb", 0),
                            "hit_rate": cache_stats.get("hit_rate", 0),
                            "hit_ratio": cache_stats.get("hit_rate", 0),
                        },
                        "processor": {
                            "total_tasks": processor_metrics.get(
                                "performance_metrics", {}
                            ).get("total_tasks", 0),
                            "running_tasks": processor_metrics.get(
                                "scheduler_stats", {}
                            ).get("running_tasks", 0),
                            "throughput_per_second": processor_metrics.get(
                                "performance_metrics", {}
                            ).get("throughput_per_second", 0),
                        },
                        "alerts": {
                            "active_count": len(self.alert_manager.get_active_alerts()),
                            "active_alerts": self.alert_manager.get_active_alerts(),
                        },
                    }
                )

            except Exception as e:
                return jsonify({"error": str(e)}), 500

    def _create_system_overview_chart(self):
        """創建系統概覽圖表"""
        fig = make_subplots(
            rows = 2,
            cols = 2,
            subplot_titles=("CPU Usage", "Memory Usage", "Disk Usage", "Network I / O"),
            specs=[
                [{"secondary_y": False}, {"secondary_y": False}],
                [{"secondary_y": False}, {"secondary_y": True}],
            ],
        )

        current_time = time.time()
        time_window = 300  # 最近5分鐘

        # CPU使用率
        cpu_data = self.metrics_collector.get_metric_data(
            "system.cpu_usage", current_time - time_window
        )
        if cpu_data:
            fig.add_trace(
                go.Scatter(
                    x=[point.timestamp for point in cpu_data],
                    y=[point.value for point in cpu_data],
                    name="CPU %",
                    line = dict(color="blue"),
                ),
                row = 1,
                col = 1,
            )

        # 內存使用率
        memory_data = self.metrics_collector.get_metric_data(
            "system.memory_usage", current_time - time_window
        )
        if memory_data:
            fig.add_trace(
                go.Scatter(
                    x=[point.timestamp for point in memory_data],
                    y=[point.value for point in memory_data],
                    name="Memory %",
                    line = dict(color="red"),
                ),
                row = 1,
                col = 2,
            )

        # 磁盤使用率
        disk_data = self.metrics_collector.get_metric_data(
            "system.disk_usage", current_time - time_window
        )
        if disk_data:
            fig.add_trace(
                go.Scatter(
                    x=[point.timestamp for point in disk_data],
                    y=[point.value for point in disk_data],
                    name="Disk %",
                    line = dict(color="green"),
                ),
                row = 2,
                col = 1,
            )

        fig.update_layout(title="System Overview", showlegend = True, height = 600)

        return json.loads(plotly.utils.PlotlyJSONEncoder().encode(fig))

    def _create_verification_performance_chart(self):
        """創建驗證性能圖表"""
        fig = make_subplots(
            rows = 2,
            cols = 2,
            subplot_titles=(
                "Response Time",
                "Success Rate",
                "Cache Hit Rate",
                "Throughput",
            ),
            specs=[
                [{"secondary_y": False}, {"secondary_y": False}],
                [{"secondary_y": False}, {"secondary_y": False}],
            ],
        )

        current_time = time.time()
        time_window = 300  # 最近5分鐘

        # 響應時間
        response_time_data = self.metrics_collector.get_metric_data(
            "verification.avg_response_time_ms", current_time - time_window
        )
        if response_time_data:
            fig.add_trace(
                go.Scatter(
                    x=[point.timestamp for point in response_time_data],
                    y=[point.value for point in response_time_data],
                    name="Response Time (ms)",
                    line = dict(color="blue"),
                ),
                row = 1,
                col = 1,
            )

        # 成功率
        success_rate_data = self.metrics_collector.get_metric_data(
            "verification.success_rate", current_time - time_window
        )
        if success_rate_data:
            fig.add_trace(
                go.Scatter(
                    x=[point.timestamp for point in success_rate_data],
                    y=[point.value for point in success_rate_data],
                    name="Success Rate",
                    line = dict(color="green"),
                ),
                row = 1,
                col = 2,
            )

        # 緩存命中率
        cache_hit_data = self.metrics_collector.get_metric_data(
            "verification.cache_hit_rate", current_time - time_window
        )
        if cache_hit_data:
            fig.add_trace(
                go.Scatter(
                    x=[point.timestamp for point in cache_hit_data],
                    y=[point.value for point in cache_hit_data],
                    name="Cache Hit Rate",
                    line = dict(color="orange"),
                ),
                row = 2,
                col = 1,
            )

        # 吞吐量
        throughput_data = self.metrics_collector.get_metric_data(
            "verification.throughput_per_second", current_time - time_window
        )
        if throughput_data:
            fig.add_trace(
                go.Scatter(
                    x=[point.timestamp for point in throughput_data],
                    y=[point.value for point in throughput_data],
                    name="Throughput (req / s)",
                    line = dict(color="purple"),
                ),
                row = 2,
                col = 2,
            )

        fig.update_layout(
            title="Verification System Performance", showlegend = True, height = 600
        )

        return json.loads(plotly.utils.PlotlyJSONEncoder().encode(fig))

    def _create_cache_performance_chart(self):
        """創建緩存性能圖表"""
        fig = make_subplots(
            rows = 2,
            cols = 2,
            subplot_titles=(
                "Cache Hit Rate",
                "Memory Usage",
                "Entries Count",
                "Compression Ratio",
            ),
            specs=[
                [{"secondary_y": False}, {"secondary_y": False}],
                [{"secondary_y": False}, {"secondary_y": False}],
            ],
        )

        current_time = time.time()
        time_window = 300  # 最近5分鐘

        # 緩存命中率
        hit_rate_data = self.metrics_collector.get_metric_data(
            "cache.hit_rate", current_time - time_window
        )
        if hit_rate_data:
            fig.add_trace(
                go.Scatter(
                    x=[point.timestamp for point in hit_rate_data],
                    y=[point.value for point in hit_rate_data],
                    name="Hit Rate",
                    line = dict(color="blue"),
                ),
                row = 1,
                col = 1,
            )

        # 內存使用量
        memory_usage_data = self.metrics_collector.get_metric_data(
            "cache.memory_usage_mb", current_time - time_window
        )
        if memory_usage_data:
            fig.add_trace(
                go.Scatter(
                    x=[point.timestamp for point in memory_usage_data],
                    y=[point.value for point in memory_usage_data],
                    name="Memory Usage (MB)",
                    line = dict(color="red"),
                ),
                row = 1,
                col = 2,
            )

        # 條目數量
        entries_data = self.metrics_collector.get_metric_data(
            "cache.entries_count", current_time - time_window
        )
        if entries_data:
            fig.add_trace(
                go.Scatter(
                    x=[point.timestamp for point in entries_data],
                    y=[point.value for point in entries_data],
                    name="Entries Count",
                    line = dict(color="green"),
                ),
                row = 2,
                col = 1,
            )

        fig.update_layout(title="Cache System Performance", showlegend = True, height = 600)

        return json.loads(plotly.utils.PlotlyJSONEncoder().encode(fig))

    async def start(self):
        """啟動監控儀表板"""
        # 啟動指標收集
        await self.metrics_collector.start_collection()

        # 啟動警報檢查任務
        asyncio.create_task(self._alert_check_loop())

        logger.info(f"MonitoringDashboard started on http://{self.host}:{self.port}")

    async def stop(self):
        """停止監控儀表板"""
        await self.metrics_collector.stop_collection()
        logger.info("MonitoringDashboard stopped")

    async def _alert_check_loop(self):
        """警報檢查循環"""
        while True:
            try:
                await self.alert_manager.check_alerts(self.metrics_collector)
                await asyncio.sleep(10)  # 每10秒檢查一次警報
            except Exception as e:
                logger.error(f"Alert check error: {e}")
                await asyncio.sleep(30)

    def run(self, debug: bool = False):
        """運行Flask應用"""
        self.app.run(host = self.host, port = self.port, debug = debug, threaded = True)


# 全局監控儀表板實例
monitoring_dashboard = MonitoringDashboard()


# 預設警報規則
def setup_default_alert_rules():
    """設置默認警報規則"""
    rules = [
        AlertRule(
            rule_id="high_response_time",
            name="High Response Time",
            metric_path="verification.avg_response_time_ms",
            operator=">",
            threshold = 100,
            severity="high",
            description="Verification response time is above 100ms",
        ),
        AlertRule(
            rule_id="low_success_rate",
            name="Low Success Rate",
            metric_path="verification.success_rate",
            operator="<",
            threshold = 0.9,
            severity="medium",
            description="Verification success rate is below 90%",
        ),
        AlertRule(
            rule_id="low_cache_hit_rate",
            name="Low Cache Hit Rate",
            metric_path="verification.cache_hit_rate",
            operator="<",
            threshold = 0.7,
            severity="low",
            description="Cache hit rate is below 70%",
        ),
        AlertRule(
            rule_id="high_cpu_usage",
            name="High CPU Usage",
            metric_path="system.cpu_usage",
            operator=">",
            threshold = 80,
            severity="high",
            description="CPU usage is above 80%",
        ),
        AlertRule(
            rule_id="high_memory_usage",
            name="High Memory Usage",
            metric_path="system.memory_usage",
            operator=">",
            threshold = 85,
            severity="critical",
            description="Memory usage is above 85%",
        ),
        AlertRule(
            rule_id="high_error_rate",
            name="High Error Rate",
            metric_path="verification.error_rate",
            operator=">",
            threshold = 0.1,
            severity="critical",
            description="Verification error rate is above 10%",
        ),
    ]

    for rule in rules:
        monitoring_dashboard.alert_manager.add_rule(rule)

    logger.info(f"Default alert rules configured: {len(rules)} rules")


# 便捷函數
async def start_monitoring():
    """啟動監控系統"""
    setup_default_alert_rules()
    await monitoring_dashboard.start()


async def stop_monitoring():
    """停止監控系統"""
    await monitoring_dashboard.stop()


def run_dashboard(host: str = "0.0.0.0", port: int = 8080, debug: bool = False):
    """運行監控儀表板"""
    monitoring_dashboard.host = host
    monitoring_dashboard.port = port
    monitoring_dashboard.run(debug)


if __name__ == "__main__":

    async def test_monitoring():
        """測試監控系統"""
        print("Testing Monitoring Dashboard...")

        # 啟動監控系統
        await start_monitoring()

        try:
            # 模擬一些指標數據
            print("Simulating metrics data...")
            for i in range(10):
                # 添加一些測試指標
                monitoring_dashboard.metrics_collector._add_metric_point(
                    "test.metric1", time.time(), i * 10
                )
                await asyncio.sleep(1)

            # 獲取指標摘要
            print("\nMetrics summary:")
            summary = {}
            for (
                metric_name
            ) in monitoring_dashboard.metrics_collector.get_all_metrics_names():
                latest_point = monitoring_dashboard.metrics_collector.get_latest_metric(
                    metric_name
                )
                if latest_point:
                    summary[metric_name] = latest_point.value

            print(f"Latest metrics: {summary}")

            # 獲取警報信息
            print("\nAlert information:")
            active_alerts = monitoring_dashboard.alert_manager.get_active_alerts()
            print(f"Active alerts: {len(active_alerts)}")
            alert_rules = len(monitoring_dashboard.alert_manager.alert_rules)
            print(f"Alert rules: {alert_rules}")

            print(
                f"Dashboard available at: http://{monitoring_dashboard.host}:{monitoring_dashboard.port}"
            )

            # 保持運行一段時間
            await asyncio.sleep(30)

        finally:
            # 停止監控系統
            await stop_monitoring()

        print("Monitoring Dashboard test completed!")

    # 運行測試
    asyncio.run(test_monitoring())
