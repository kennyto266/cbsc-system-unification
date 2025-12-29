#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CBSC Enhanced Metrics Collector
CBSC增強指標收集器

專為477技術指標系統和生產環境監控設計的全面指標收集器
"""

import time
import asyncio
import logging
import psutil
import json
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import threading
from functools import wraps

import prometheus_client as prom
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

@dataclass
class IndicatorMetric:
    """指標計算指標"""
    indicator_type: str
    calculation_time: float
    timestamp: datetime
    status: str  # 'success', 'error', 'timeout'
    error_message: Optional[str] = None
    data_points: int = 0

@dataclass
class ChartMetric:
    """圖表渲染指標"""
    chart_type: str
    render_time: float
    timestamp: datetime
    data_points: int
    user_agent: str
    status: str

@dataclass
class WebSocketMetric:
    """WebSocket連接指標"""
    connection_id: str
    message_type: str
    message_size: int
    latency: float
    timestamp: datetime
    direction: str  # 'sent', 'received'

class EnhancedMetricsCollector:
    """增強指標收集器"""

    def __init__(self):
        self.start_time = time.time()
        self.indicator_metrics = deque(maxlen=10000)
        self.chart_metrics = deque(maxlen=5000)
        self.websocket_metrics = deque(maxlen=10000)
        self.user_sessions = {}
        self.performance_history = defaultdict(list)

        # Prometheus指標定義
        self._init_prometheus_metrics()

        # 性能監控線程
        self.monitoring_thread = None
        self.is_monitoring = False

    def _init_prometheus_metrics(self):
        """初始化Prometheus指標"""

        # 477技術指標專用指標
        self.indicator_calculations_total = prom.Counter(
            'indicator_calculations_total',
            '477指標計算總數',
            ['indicator_type', 'status']
        )

        self.indicator_calculation_duration = prom.Histogram(
            'indicator_calculation_duration_seconds',
            '477指標計算耗時',
            ['indicator_type'],
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
        )

        self.active_indicators_count = prom.Gauge(
            'active_indicators_count',
            '活躍477指標數量'
        )

        self.indicator_last_update_timestamp = prom.Gauge(
            'indicator_last_update_timestamp_seconds',
            '指標最後更新時間戳'
        )

        # 圖表渲染指標
        self.chart_renders_total = prom.Counter(
            'chart_renders_total',
            '圖表渲染總數',
            ['chart_type', 'status']
        )

        self.chart_render_duration = prom.Histogram(
            'chart_render_duration_seconds',
            '圖表渲染耗時',
            ['chart_type'],
            buckets=[0.01, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0]
        )

        # 用戶體驗指標
        self.active_users_total = prom.Gauge(
            'active_users_total',
            '當前活躍用戶數'
        )

        self.user_indicator_requests_total = prom.Counter(
            'user_indicator_requests_total',
            '用戶指標請求總數',
            ['user_id', 'indicator_type']
        )

        self.page_load_duration = prom.Histogram(
            'page_load_duration_seconds',
            '頁面加載時間',
            ['page'],
            buckets=[0.5, 1.0, 2.0, 3.0, 5.0, 10.0]
        )

        # 實時性能指標
        self.realtime_update_latency = prom.Histogram(
            'realtime_update_latency_seconds',
            '實時更新延遲',
            ['update_type'],
            buckets=[0.01, 0.05, 0.1, 0.2, 0.5, 1.0]
        )

        self.data_freshness = prom.Gauge(
            'data_freshness_seconds',
            '數據新鮮度',
            ['data_source']
        )

        # 系統健康指標
        self.system_health_score = prom.Gauge(
            'system_health_score',
            '系統健康分數(0-100)'
        )

        self.error_budget_remaining = prom.Gauge(
            'error_budget_remaining_percentage',
            '錯誤預算剩餘百分比'
        )

        # 業務指標
        self.strategy_executions_total = prom.Counter(
            'strategy_executions_total',
            '策略執行總數',
            ['strategy_type', 'status']
        )

        self.market_data_quality_score = prom.Gauge(
            'market_data_quality_score',
            '市場數據質量分數',
            ['data_source']
        )

    def record_indicator_calculation(self, metric: IndicatorMetric):
        """記錄指標計算"""
        # 存儲到內存
        self.indicator_metrics.append(metric)

        # 更新Prometheus指標
        self.indicator_calculations_total.labels(
            indicator_type=metric.indicator_type,
            status=metric.status
        ).inc()

        self.indicator_calculation_duration.labels(
            indicator_type=metric.indicator_type
        ).observe(metric.calculation_time)

        # 更新時間戳
        self.indicator_last_update_timestamp.set(time.time())

        # 記錄性能歷史
        self.performance_history[metric.indicator_type].append({
            'timestamp': metric.timestamp,
            'duration': metric.calculation_time,
            'status': metric.status
        })

        # 限制歷史記錄長度
        if len(self.performance_history[metric.indicator_type]) > 1000:
            self.performance_history[metric.indicator_type] = \
                self.performance_history[metric.indicator_type][-500:]

    def record_chart_render(self, metric: ChartMetric):
        """記錄圖表渲染"""
        self.chart_metrics.append(metric)

        self.chart_renders_total.labels(
            chart_type=metric.chart_type,
            status=metric.status
        ).inc()

        self.chart_render_duration.labels(
            chart_type=metric.chart_type
        ).observe(metric.render_time)

    def record_websocket_activity(self, metric: WebSocketMetric):
        """記錄WebSocket活動"""
        self.websocket_metrics.append(metric)

        # 更新WebSocket相關的Prometheus指標
        if hasattr(self, 'websocket_messages_total'):
            self.websocket_messages_total.labels(
                message_type=metric.message_type,
                direction=metric.direction
            ).inc()

    def update_active_users(self, user_sessions: Dict[str, Any]):
        """更新活躍用戶數"""
        active_count = len(user_sessions)
        self.active_users_total.set(active_count)
        self.user_sessions = user_sessions

    def calculate_system_health_score(self) -> float:
        """計算系統健康分數"""
        factors = []

        # 服務可用性 (40%)
        uptime_percentage = min(100, (time.time() - self.start_time) / 3600 * 100)
        factors.append(('uptime', min(1.0, uptime_percentage / 100), 0.4))

        # 指標計算成功率 (30%)
        recent_metrics = [m for m in self.indicator_metrics
                         if m.timestamp > datetime.now() - timedelta(minutes=5)]
        if recent_metrics:
            success_rate = sum(1 for m in recent_metrics if m.status == 'success') / len(recent_metrics)
            factors.append(('indicator_success', success_rate, 0.3))
        else:
            factors.append(('indicator_success', 1.0, 0.3))

        # 響應時間 (20%)
        if recent_metrics:
            avg_response_time = sum(m.calculation_time for m in recent_metrics) / len(recent_metrics)
            # 將響應時間轉換為0-1分數 (目標<1秒)
            response_score = max(0, 1 - (avg_response_time - 1) / 5)
            factors.append(('response_time', min(1.0, response_score), 0.2))
        else:
            factors.append(('response_time', 1.0, 0.2))

        # 錯誤率 (10%)
        error_rate = 0.05  # 默認5%錯誤率閾值
        if recent_metrics:
            actual_error_rate = sum(1 for m in recent_metrics if m.status == 'error') / len(recent_metrics)
            error_score = max(0, 1 - (actual_error_rate / error_rate))
            factors.append(('error_rate', error_score, 0.1))
        else:
            factors.append(('error_rate', 1.0, 0.1))

        # 計算加權平均分
        health_score = sum(score * weight for _, score, weight in factors)
        self.system_health_score.set(health_score * 100)

        return health_score

    def calculate_error_budget_remaining(self) -> float:
        """計算錯誤預算剩餘"""
        # 假設月度錯誤預算為1%
        monthly_error_budget = 0.01
        month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        monthly_metrics = [m for m in self.indicator_metrics
                          if m.timestamp > month_start]

        if monthly_metrics:
            actual_error_rate = sum(1 for m in monthly_metrics if m.status == 'error') / len(monthly_metrics)
            remaining_budget = max(0, (monthly_error_budget - actual_error_rate) / monthly_error_budget)
        else:
            remaining_budget = 1.0

        self.error_budget_remaining.set(remaining_budget * 100)
        return remaining_budget

    def start_system_monitoring(self):
        """啟動系統監控"""
        if self.is_monitoring:
            return

        self.is_monitoring = True
        self.monitoring_thread = threading.Thread(target=self._system_monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        logger.info("Enhanced metrics collector monitoring started")

    def stop_system_monitoring(self):
        """停止系統監控"""
        self.is_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join()
        logger.info("Enhanced metrics collector monitoring stopped")

    def _system_monitoring_loop(self):
        """系統監控循環"""
        while self.is_monitoring:
            try:
                # 計算系統健康分數
                self.calculate_system_health_score()

                # 計算錯誤預算
                self.calculate_error_budget_remaining()

                # 更新數據新鮮度
                if self.indicator_metrics:
                    last_update = self.indicator_metrics[-1].timestamp
                    freshness = (datetime.now() - last_update).total_seconds()
                    self.data_freshness.labels(data_source='indicators').set(freshness)

                # 清理舊數據
                self._cleanup_old_metrics()

            except Exception as e:
                logger.error(f"Error in system monitoring loop: {e}")

            time.sleep(30)  # 每30秒更新一次

    def _cleanup_old_metrics(self):
        """清理舊指標數據"""
        cutoff_time = datetime.now() - timedelta(hours=24)

        # 清理指標數據
        self.indicator_metrics = deque(
            (m for m in self.indicator_metrics if m.timestamp > cutoff_time),
            maxlen=10000
        )

        self.chart_metrics = deque(
            (m for m in self.chart_metrics if m.timestamp > cutoff_time),
            maxlen=5000
        )

        self.websocket_metrics = deque(
            (m for m in self.websocket_metrics if m.timestamp > cutoff_time),
            maxlen=10000
        )

    def get_performance_summary(self) -> Dict[str, Any]:
        """獲取性能摘要"""
        recent_time = datetime.now() - timedelta(minutes=5)
        recent_indicators = [m for m in self.indicator_metrics if m.timestamp > recent_time]

        if not recent_indicators:
            return {
                'total_calculations': 0,
                'success_rate': 1.0,
                'avg_duration': 0,
                'error_count': 0,
                'indicator_types': {}
            }

        success_count = sum(1 for m in recent_indicators if m.status == 'success')
        error_count = sum(1 for m in recent_indicators if m.status == 'error')
        total_count = len(recent_indicators)

        # 按類型統計
        type_stats = defaultdict(list)
        for m in recent_indicators:
            type_stats[m.indicator_type].append(m.calculation_time)

        indicator_types = {}
        for indicator_type, durations in type_stats.items():
            indicator_types[indicator_type] = {
                'count': len(durations),
                'avg_duration': sum(durations) / len(durations),
                'min_duration': min(durations),
                'max_duration': max(durations)
            }

        return {
            'total_calculations': total_count,
            'success_rate': success_count / total_count if total_count > 0 else 1.0,
            'avg_duration': sum(m.calculation_time for m in recent_indicators) / total_count,
            'error_count': error_count,
            'indicator_types': indicator_types,
            'system_health_score': self.calculate_system_health_score(),
            'error_budget_remaining': self.calculate_error_budget_remaining()
        }

# 全局指標收集器實例
metrics_collector = EnhancedMetricsCollector()

def track_indicator_performance(indicator_type: str):
    """指標性能追蹤裝飾器"""
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            status = 'success'
            error_message = None

            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = 'error'
                error_message = str(e)
                logger.error(f"Indicator calculation failed for {indicator_type}: {e}")
                raise
            finally:
                duration = time.time() - start_time
                metric = IndicatorMetric(
                    indicator_type=indicator_type,
                    calculation_time=duration,
                    timestamp=datetime.now(),
                    status=status,
                    error_message=error_message
                )
                metrics_collector.record_indicator_calculation(metric)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            status = 'success'
            error_message = None

            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = 'error'
                error_message = str(e)
                logger.error(f"Indicator calculation failed for {indicator_type}: {e}")
                raise
            finally:
                duration = time.time() - start_time
                metric = IndicatorMetric(
                    indicator_type=indicator_type,
                    calculation_time=duration,
                    timestamp=datetime.now(),
                    status=status,
                    error_message=error_message
                )
                metrics_collector.record_indicator_calculation(metric)

        # 根據函數類型返回對應的包裝器
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator

class EnhancedMetricsMiddleware(BaseHTTPMiddleware):
    """增強指標收集中間件"""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # 處理請求
        response = await call_next(request)

        # 計算處理時間
        process_time = time.time() - start_time

        # 更新基礎HTTP指標
        method = request.method
        path = request.url.path
        status_code = str(response.status_code)

        # 過滤健康檢查端點
        if path not in ['/health', '/metrics', '/ready', '/live']:
            if hasattr(metrics_collector, 'http_requests_total'):
                metrics_collector.http_requests_total.labels(
                    method=method,
                    endpoint=path,
                    status_code=status_code
                ).inc()

            if hasattr(metrics_collector, 'http_request_duration'):
                metrics_collector.http_request_duration.labels(
                    method=method,
                    endpoint=path
                ).observe(process_time)

        # 記錄頁面加載時間
        if path.startswith('/') and path != '/':
            if hasattr(metrics_collector, 'page_load_duration'):
                metrics_collector.page_load_duration.labels(
                    page=path
                ).observe(process_time)

        return response

# 初始化監控
def initialize_enhanced_metrics():
    """初始化增強監控"""
    logger.info("Initializing enhanced metrics collector...")
    metrics_collector.start_system_monitoring()
    logger.info("Enhanced metrics collector initialized successfully")

# 清理監控
def cleanup_enhanced_metrics():
    """清理增強監控"""
    logger.info("Cleaning up enhanced metrics collector...")
    metrics_collector.stop_system_monitoring()
    logger.info("Enhanced metrics collector cleaned up")