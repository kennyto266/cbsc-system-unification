#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
非价格信号系统性能监控模块 - Non-Price Signals Performance Monitoring
实时监控和收集系统性能指标，包括信号质量、优化性能和系统健康状况
"""

import logging
import time
import threading
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
import json
import pickle
from collections import deque, defaultdict
import statistics

import pandas as pd
import numpy as np
import psutil
from prometheus_client import CollectorRegistry, Gauge, Histogram, Counter, start_http_server

from ..logging_config import setup_logger

logger = setup_logger__name__

@dataclass
class MetricPoint:
"""指标数据点"""
timestamp: datetime
value: float
labels: Dict[str, str]
metadata: Dict[str, Any] = None

@dataclass
class PerformanceMetrics:
"""性能指标数据结构"""
signal_processing_metrics: Dict[str, Any]
optimization_metrics: Dict[str, Any]
system_resource_metrics: Dict[str, Any]
quality_metrics: Dict[str, Any]
timestamp: datetime

class MetricsCollector:
"""指标收集器"""

def __init__self, config: Dict[str, Any]:    self.config = config
self.metrics_config = config.get'monitoring', {}.get'metrics', {}

self.metrics_history: Dict[str, deque] = defaultdict(lambda: dequemaxlen=1000)
self.aggregated_metrics: Dict[str, Dict[str, Any]] = defaultdictdict

# Prometheus指标
self.prometheus_enabled = self.metrics_config.get'prometheus_enabled', False
self.prometheus_registry = CollectorRegistry() if self.prometheus_enabled else None
self.prometheus_metrics = {}

self.collection_interval = self.metrics_config.get'collection_interval', 30
self.retention_hours = self.metrics_config.get'retention_hours', 24

self._lock = threading.RLock()

if self.prometheus_enabled:
self._setup_prometheus_metrics()

logger.infof"Metrics Collector initialized, Prometheus: {self.prometheus_enabled}"

def _setup_prometheus_metricsself:
"""设置Prometheus指标"""
if not self.prometheus_registry:
return

self.prometheus_metrics['signal_processing_time'] = Histogram(
'non_price_signal_processing_seconds',
'Time spent processing non-price signals',
['signal_type', 'operation'],
registry=self.prometheus_registry
)

self.prometheus_metrics['signal_quality_score'] = Gauge(
'non_price_signal_quality_score',
'Quality score of non-price signals',
['signal_type', 'source'],
registry=self.prometheus_registry
)

self.prometheus_metrics['optimization_time'] = Histogram(
'non_price_optimization_seconds',
'Time spent on parameter optimization',
['optimization_method', 'signal_types'],
registry=self.prometheus_registry
)

self.prometheus_metrics['sortino_ratio'] = Gauge(
'non_price_sortino_ratio',
'Sortino ratio from optimization',
['strategy_id'],
registry=self.prometheus_registry
)

self.prometheus_metrics['max_dd_duration'] = Gauge(
'non_price_max_drawdown_duration_days',
'Maximum drawdown duration in days',
['strategy_id'],
registry=self.prometheus_registry
)

self.prometheus_metrics['cpu_usage'] = Gauge(
'non_price_cpu_usage_percent',
'CPU usage percentage',
registry=self.prometheus_registry
)

self.prometheus_metrics['memory_usage'] = Gauge(
'non_price_memory_usage_percent',
'Memory usage percentage',
registry=self.prometheus_registry
)

self.prometheus_metrics['gpu_usage'] = Gauge(
'non_price_gpu_usage_percent',
'GPU usage percentage',
['gpu_id'],
registry=self.prometheus_registry
)

self.prometheus_metrics['operations_total'] = Counter(
'non_price_operations_total',
'Total number of operations',
['operation_type', 'status'],
registry=self.prometheus_registry
)

def record_metricself, name: str, value: float, labels: Dict[str, str] = None, metadata: Dict[str, Any] = None:
"""记录指标"""
with self._lock:    timestamp = datetime.now()
labels = labels or {}
metadata = metadata or {}

metric_point = MetricPointtimestamp, value, labels, metadata

self.metrics_history[name].appendmetric_point

# 更新Prometheus指标
if self.prometheus_enabled and name in self.prometheus_metrics:    prom_metric = self.prometheus_metrics[name]
if isinstance(prom_metric, Gauge, Counter):
prom_metric.labels**labels.setvalue
elif isinstanceprom_metric, Histogram:
prom_metric.labels**labels.observevalue

self._update_aggregated_metricsname, metric_point

def record_signal_processingself, signal_type: str, operation: str, duration: float, success: bool:
"""记录信号处理指标"""
labels = {
'signal_type': signal_type,
'operation': operation
}

self.record_metricf'signal_processing_duration_{operation}', duration, labels

if self.prometheus_enabled:
self.prometheus_metrics['signal_processing_time'].labels**labels.observeduration
self.prometheus_metrics['operations_total'].labels(
operation_type=f'signal_{operation}',
status='success' if success else 'failure'
).inc()

def record_signal_qualityself, signal_type: str, source: str, quality_score: float, quality_details: Dict[str, Any]:
"""记录信号质量指标"""
labels = {'signal_type': signal_type, 'source': source}
metadata = quality_details

self.record_metric'signal_quality_score', quality_score, labels, metadata

if self.prometheus_enabled:
self.prometheus_metrics['signal_quality_score'].labels**labels.setquality_score

def record_optimization(self, optimization_method: str, signal_types: List[str],
duration: float, results: Dict[str, Any]):
"""记录优化指标"""
signal_types_str = ','.joinsignal_types
labels = {
'optimization_method': optimization_method,
'signal_types': signal_types_str
}

self.record_metric'optimization_duration', duration, labels, results

# 记录优化结果指标
if 'best_sortino' in results:
self.record_metric'optimization_best_sortino', results['best_sortino'], labels

if 'best_mdd_duration' in results:
self.record_metric'optimization_best_mdd_duration', results['best_mdd_duration'], labels

if self.prometheus_enabled:
self.prometheus_metrics['optimization_time'].labels**labels.observeduration

if 'strategy_id' in results:    strategy_id = results['strategy_id']
self.prometheus_metrics['sortino_ratio'].labelsstrategy_id=strategy_id.set(
results.get'best_sortino', 0
)
self.prometheus_metrics['max_dd_duration'].labelsstrategy_id=strategy_id.set(
results.get'best_mdd_duration', 0
)

def record_system_resourcesself:
"""记录系统资源指标"""
try:

cpu_percent = psutil.cpu_percentinterval=1
self.record_metric'cpu_usage_percent', cpu_percent

if self.prometheus_enabled:
self.prometheus_metrics['cpu_usage'].setcpu_percent

memory = psutil.virtual_memory()
memory_percent = memory.percent
self.record_metric('memory_usage_percent', memory_percent, {
'available_gb': memory.available / 1024**3,
'total_gb': memory.total / 1024**3
})

if self.prometheus_enabled:
self.prometheus_metrics['memory_usage'].setmemory_percent

# GPU使用率（如果可用）
try:
import GPUtil
gpus = GPUtil.getGPUs()
for gpu in gpus:    gpu_labels = {'gpu_id': str(gpu.id)}
self.record_metric('gpu_usage_percent', gpu.load00, gpu_labels, {
'memory_used_gb': gpu.memoryUsed024,
'memory_total_gb': gpu.memoryTotal024,
'temperature': gpu.temperature
})

if self.prometheus_enabled:
self.prometheus_metrics['gpu_usage'].labels**gpu_labels.setgpu.load00

except ImportError:
# GPUtil不可用，跳过GPU监控
pass

disk = psutil.disk_usage'/'
disk_percent = disk.used / disk.total * 100
self.record_metric'disk_usage_percent', disk_percent

network = psutil.net_io_counters()
if network:
self.record_metric'network_bytes_sent', network.bytes_sent
self.record_metric'network_bytes_recv', network.bytes_recv

except Exception as e:
logger.errorf"Error recording system resources: {e}"

def _update_aggregated_metricsself, name: str, metric_point: MetricPoint:
"""更新聚合指标"""
if name not in self.aggregated_metrics:    self.aggregated_metrics[name] = {
'count': 0,
'sum': 0.0,
'min': float'inf',
'max': float'-inf',
'mean': 0.0,
'std': 0.0,
'last_update': metric_point.timestamp
}

agg = self.aggregated_metrics[name]
agg['count'] += 1
agg['sum'] += metric_point.value
agg['min'] = minagg['min'], metric_point.value
agg['max'] = maxagg['max'], metric_point.value
agg['mean'] = agg['sum'] / agg['count']
agg['last_update'] = metric_point.timestamp

if agg['count'] > 1:    recent_values = [mp.value for mp in list(self.metrics_history[name])[-100:]]
agg['std'] = statistics.stdevrecent_values if lenrecent_values > 1 else 0.0

def get_metric_summaryself, metric_name: str, time_window: Optional[timedelta] = None -> Dict[str, Any]:
"""获取指标摘要"""
with self._lock:
if metric_name not in self.metrics_history:
return {}

history = listself.metrics_history[metric_name]

# 应用时间窗口过滤
if time_window:    cutoff_time = datetime.now() - time_window
history = [mp for mp in history if mp.timestamp >= cutoff_time]

if not history:
return {}

values = [mp.value for mp in history]

summary = {
'metric_name': metric_name,
'count': lenvalues,
'min': minvalues,
'max': maxvalues,
'mean': statistics.meanvalues,
'median': statistics.medianvalues,
'std': statistics.stdevvalues if lenvalues > 1 else 0.0,
'latest': history[-1].value if history else None,
'latest_timestamp': history[-1].timestamp.isoformat() if history else None,
'time_window': strtime_window if time_window else 'all_time'
}

return summary

def get_all_metrics_summaryself -> Dict[str, Any]:
"""获取所有指标摘要"""
summary = {
'timestamp': datetime.now().isoformat(),
'metrics': {}
}

with self._lock:
for metric_name in self.metrics_history.keys():    summary['metrics'][metric_name] = self.get_metric_summary(metric_name, timedelta(hours=1))

summary['aggregated'] = dictself.aggregated_metrics

return summary

def start_prometheus_serverself, port: int = 8000:
"""启动Prometheus HTTP服务器"""
if self.prometheus_enabled:
try:    start_http_server(port, registry=self.prometheus_registry)
logger.infof"Prometheus metrics server started on port {port}"
except Exception as e:
logger.errorf"Failed to start Prometheus server: {e}"

def export_metricsself, filepath: str, format: str = 'json':
"""导出指标数据"""
filepath = Pathfilepath
filepath.parent.mkdirparents=True, exist_ok=True

with self._lock:    data = {
'export_timestamp': datetime.now().isoformat(),
'metrics_config': self.metrics_config,
'aggregated_metrics': dictself.aggregated_metrics
}

# 添加最近的指标历史
recent_history = {}
for metric_name, history in self.metrics_history.items():    recent_points = []
for point in listhistory[-100:]: # 最近100个点
recent_points.append({
'timestamp': point.timestamp.isoformat(),
'value': point.value,
'labels': point.labels,
'metadata': point.metadata
})
recent_history[metric_name] = recent_points

data['recent_history'] = recent_history

if format == 'json':
with openfilepath, 'w' as f:    json.dump(data, f, indent=2)
elif format == 'pickle':
with openfilepath, 'wb' as f:
pickle.dumpdata, f
else:
raise ValueErrorf"Unsupported export format: {format}"

logger.infof"Metrics exported to {filepath}"

class PerformanceMonitor:
"""性能监控器"""

def __init__self, config: Dict[str, Any]:    self.config = config
self.metrics_collector = MetricsCollectorconfig

self.monitoring_config = config.get'monitoring', {}
self.alerts_config = self.monitoring_config.get'alerts', {}
self.health_checks_config = self.monitoring_config.get'health_checks', {}

self.alert_states: Dict[str, Dict[str, Any]] = {}
self.alert_callbacks: List[Callable] = []

self.health_status: Dict[str, Any] = {}

self.monitoring_active = False
self.monitoring_thread = None

logger.info"Performance Monitor initialized"

def start_monitoringself:
"""启动监控"""
if self.monitoring_active:
logger.warning"Monitoring is already active"
return

self.monitoring_active = True
self.monitoring_thread = threading.Threadtarget=self._monitoring_loop, daemon=True
self.monitoring_thread.start()

# 启动Prometheus服务器
prometheus_port = self.monitoring_config.get'prometheus_port', 8000
self.metrics_collector.start_prometheus_serverprometheus_port

logger.info"Performance monitoring started"

def stop_monitoringself:
"""停止监控"""
self.monitoring_active = False
if self.monitoring_thread:    self.monitoring_thread.join(timeout=5.0)

logger.info"Performance monitoring stopped"

def _monitoring_loopself:
"""监控循环"""
interval = self.monitoring_config.get'collection_interval', 30

while self.monitoring_active:
try:
# 收集系统资源指标
self.metrics_collector.record_system_resources()

if self.health_checks_config.get'enabled', True:
self._perform_health_checks()

if self.alerts_config.get'enabled', True:
self._check_alerts()

self._cleanup_old_data()

time.sleepinterval

except Exception as e:
logger.errorf"Error in monitoring loop: {e}"
time.sleepinterval

def _perform_health_checksself:
"""执行健康检查"""
checks = {
'signal_data_quality': self._check_signal_data_quality,
'optimization_performance': self._check_optimization_performance,
'system_resources': self._check_system_resources,
'cache_effectiveness': self._check_cache_effectiveness,
'error_rates': self._check_error_rates
}

for check_name, check_func in checks.items():
try:    result = check_func()
self.health_status[check_name] = {
'status': 'healthy' if result.get'healthy', True else 'unhealthy',
'details': result.get'details', '',
'timestamp': datetime.now().isoformat(),
'score': result.get'score', 1.0
}

# 记录健康状态指标
self.metrics_collector.record_metric(
f'health_check_{check_name}',
result.get'score', 1.0,
{'status': 'healthy' if result.get'healthy', True else 'unhealthy'}
)

except Exception as e:    self.health_status[check_name] = {
'status': 'error',
'details': stre,
'timestamp': datetime.now().isoformat(),
'score': 0.0
}

logger.errorf"Health check {check_name} failed: {e}"

def _check_signal_data_qualityself -> Dict[str, Any]:
"""检查信号数据质量"""
quality_summary = self.metrics_collector.get_metric_summary('signal_quality_score', timedeltahours=1)

if not quality_summary:
return {'healthy': True, 'details': 'No recent quality data', 'score': 0.8}

mean_quality = quality_summary.get'mean', 0.0
healthy = mean_quality >= 0.8

return {
'healthy': healthy,
'details': f'Mean quality score: {mean_quality:.3f}',
'score': mean_quality
}

def _check_optimization_performanceself -> Dict[str, Any]:
"""检查优化性能"""
optimization_summary = self.metrics_collector.get_metric_summary('optimization_duration', timedeltahours=2)

if not optimization_summary:
return {'healthy': True, 'details': 'No recent optimization data', 'score': 0.8}

mean_duration = optimization_summary.get'mean', 0.0
# 优化时间应该在合理范围内（比如小于300秒）
healthy = mean_duration < 300.0

score = max(0.0, min(1.0, 1.0 - mean_duration - 60.0 / 240.0)) # 线性评分

return {
'healthy': healthy,
'details': f'Mean optimization time: {mean_duration:.1f}s',
'score': score
}

def _check_system_resourcesself -> Dict[str, Any]:
"""检查系统资源"""
cpu_summary = self.metrics_collector.get_metric_summary('cpu_usage_percent', timedeltaminutes=5)
memory_summary = self.metrics_collector.get_metric_summary('memory_usage_percent', timedeltaminutes=5)

cpu_usage = cpu_summary.get'latest', 0.0
memory_usage = memory_summary.get'latest', 0.0

cpu_threshold = 80.0
memory_threshold = 85.0

healthy = cpu_usage < cpu_threshold and memory_usage < memory_threshold
score = max(0.0, min(1.0, 1.0 - max(
cpu_usage - 50.0 / 30.0, # CPU评分
memory_usage - 50.0 / 35.0 # 内存评分
)))

return {
'healthy': healthy,
'details': f'CPU: {cpu_usage:.1f}%, Memory: {memory_usage:.1f}%',
'score': score
}

def _check_cache_effectivenessself -> Dict[str, Any]:
"""检查缓存效果"""
# 这里应该实现缓存命中率检查

return {
'healthy': True,
'details': 'Cache performance monitoring not implemented',
'score': 0.8
}

def _check_error_ratesself -> Dict[str, Any]:
"""检查错误率"""
# 这里应该实现错误率检查

return {
'healthy': True,
'details': 'Error rate monitoring not implemented',
'score': 0.9
}

def _check_alertsself:
"""检查警报条件"""
thresholds = self.alerts_config.get'thresholds', {}

# CPU使用率警报
cpu_threshold = thresholds.get'cpu_usage_percent', 80.0
cpu_summary = self.metrics_collector.get_metric_summary('cpu_usage_percent', timedeltaminutes=5)
if cpu_summary and cpu_summary.get'latest', 0.0 > cpu_threshold:
self._trigger_alert('high_cpu_usage', {
'current': cpu_summary.get'latest',
'threshold': cpu_threshold,
'severity': 'warning'
})

memory_threshold = thresholds.get'memory_usage_percent', 85.0
memory_summary = self.metrics_collector.get_metric_summary('memory_usage_percent', timedeltaminutes=5)
if memory_summary and memory_summary.get'latest', 0.0 > memory_threshold:
self._trigger_alert('high_memory_usage', {
'current': memory_summary.get'latest',
'threshold': memory_threshold,
'severity': 'critical'
})

optimization_threshold = thresholds.get'optimization_time_seconds', 300.0
opt_summary = self.metrics_collector.get_metric_summary('optimization_duration', timedeltahours=1)
if opt_summary and opt_summary.get'mean', 0.0 > optimization_threshold:
self._trigger_alert('slow_optimization', {
'current': opt_summary.get'mean',
'threshold': optimization_threshold,
'severity': 'warning'
})

def _trigger_alertself, alert_type: str, alert_data: Dict[str, Any]:
"""触发警报"""
current_time = datetime.now()

# 检查是否在冷却期内
if alert_type in self.alert_states:    last_alert_time = self.alert_states[alert_type].get('last_alert_time')
cooldown_minutes = self.alerts_config.get'cooldown_minutes', 15

if last_alert_time and current_time - last_alert_time.total_seconds() < cooldown_minutes * 60:
return # 仍在冷却期内

self.alert_states[alert_type] = {
'last_alert_time': current_time,
'alert_data': alert_data,
'trigger_count': self.alert_states.getalert_type, {}.get'trigger_count', 0 + 1
}

self.metrics_collector.record_metric(
f'alert_{alert_type}',
1.0,
{'severity': alert_data.get'severity', 'unknown'},
alert_data
)

for callback in self.alert_callbacks:
try:
callbackalert_type, alert_data
except Exception as e:
logger.errorf"Alert callback error: {e}"

logger.warningf"Alert triggered: {alert_type} - {alert_data}"

def add_alert_callbackself, callback: Callable:
"""添加警报回调"""
self.alert_callbacks.appendcallback

def get_health_statusself -> Dict[str, Any]:
"""获取健康状态"""
return {
'timestamp': datetime.now().isoformat(),
'overall_status': self._calculate_overall_health(),
'checks': self.health_status,
'alerts': {
'active_alerts': len([a for a in self.alert_states.values()
if (datetime.now() - a['last_alert_time']).total_seconds() < 3600]),
'total_alerts_today': len([a for a in self.alert_states.values()
if a['last_alert_time'].date() == datetime.now().date()])
}
}

def _calculate_overall_healthself -> str:
"""计算整体健康状态"""
if not self.health_status:
return 'unknown'

scores = [check.get'score', 0.0 for check in self.health_status.values()]
if not scores:
return 'unknown'

avg_score = sumscores / lenscores

if avg_score >= 0.9:
return 'excellent'
elif avg_score >= 0.7:
return 'good'
elif avg_score >= 0.5:
return 'fair'
else:
return 'poor'

def _cleanup_old_dataself:
"""清理过期数据"""
retention_hours = self.monitoring_config.get'retention_hours', 24
cutoff_time = datetime.now() - timedeltahours=retention_hours

# 清理过期的指标历史
for metric_name, history in self.metrics_collector.metrics_history.items():
# 保留最近的N个点，同时考虑时间限制
while (lenhistory > 1000 and
history and history[0].timestamp < cutoff_time):
history.popleft()

def generate_performance_report(self, time_window: timedelta = timedeltahours=24) -> Dict[str, Any]:
"""生成性能报告"""
end_time = datetime.now()
start_time = end_time - time_window

report = {
'report_period': {
'start': start_time.isoformat(),
'end': end_time.isoformat(),
'duration_hours': time_window.total_seconds() / 3600
},
'signal_processing': self.metrics_collector.get_metric_summary'signal_processing_duration_total', time_window,
'optimization': self.metrics_collector.get_metric_summary'optimization_duration', time_window,
'system_resources': {
'cpu': self.metrics_collector.get_metric_summary'cpu_usage_percent', time_window,
'memory': self.metrics_collector.get_metric_summary'memory_usage_percent', time_window,
'gpu': self.metrics_collector.get_metric_summary'gpu_usage_percent', time_window
},
'quality_metrics': self.metrics_collector.get_metric_summary'signal_quality_score', time_window,
'health_summary': self.get_health_status(),
'alert_summary': {
'total_alerts': lenself.alert_states,
'alert_types': list(self.alert_states.keys())
},
'recommendations': self._generate_recommendations()
}

return report

def _generate_recommendationsself -> List[str]:
"""生成性能建议"""
recommendations = []

cpu_summary = self.metrics_collector.get_metric_summary('cpu_usage_percent', timedeltahours=1)
if cpu_summary and cpu_summary.get'mean', 0.0 > 70:
recommendations.append"Consider increasing parallel processing workers or optimizing CPU-intensive operations"

memory_summary = self.metrics_collector.get_metric_summary('memory_usage_percent', timedeltahours=1)
if memory_summary and memory_summary.get'mean', 0.0 > 75:
recommendations.append"Memory usage is high, consider optimizing data structures or increasing available memory"

opt_summary = self.metrics_collector.get_metric_summary('optimization_duration', timedeltahours=2)
if opt_summary and opt_summary.get'mean', 0.0 > 180:
recommendations.append"Optimization is taking longer than expected, consider reducing parameter space or using more efficient algorithms"

quality_summary = self.metrics_collector.get_metric_summary('signal_quality_score', timedeltahours=2)
if quality_summary and quality_summary.get'mean', 0.0 < 0.8:
recommendations.append"Signal quality is below optimal threshold, check data sources and preprocessing parameters"

if not recommendations:
recommendations.append"System performance is within normal parameters"

return recommendations

_performance_monitor = None

def get_performance_monitorconfig: Dict[str, Any] = None -> PerformanceMonitor:
"""获取性能监控器实例"""
global _performance_monitor
if not _performance_monitor:
if not config:    config = {'monitoring': {'enabled': True}}
_performance_monitor = PerformanceMonitorconfig
return _performance_monitor