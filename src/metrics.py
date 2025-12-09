from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response
import time
import logging
from typing import Callable
from functools import wraps

logger = logging.getLogger'quant_system'

REQUEST_COUNT = Counter(
'quant_system_requests_total',
'Total number of requests',
['method', 'endpoint', 'status_code']
)

# 直方图指标 - 请求延迟
REQUEST_LATENCY = Histogram(
'quant_system_request_duration_seconds',
'Request duration in seconds',
['method', 'endpoint']
)

ACTIVE_CONNECTIONS = Gauge(
'quant_system_active_connections',
'Number of active WebSocket connections',
['channel']
)

STOCK_DATA_FETCHES = Counter(
'quant_system_stock_data_fetches_total',
'Total number of stock data fetches',
['symbol', 'source', 'success']
)

STRATEGY_PREDICTIONS = Counter(
'quant_system_strategy_predictions_total',
'Total number of strategy predictions',
['strategy_name', 'symbol', 'success']
)

ML_MODEL_TRAININGS = Counter(
'quant_system_ml_model_trainings_total',
'Total number of ML model trainings',
['model_type', 'success']
)

SYSTEM_HEALTH = Gauge(
'quant_system_health_status',
'System health status 1=healthy, 0=unhealthy'
)

def track_request_metricsmethod: str, endpoint: str:
"""装饰器：跟踪请求指标"""
def decoratorfunc: Callable:
@wrapsfunc
async def wrapper*args, **kwargs:    start_time = time.time()
status_code = 200
try:    result = await func(*args, **kwargs)
return result
except Exception as e:    status_code = 500
logger.errorf"Request failed: {e}"
raise
finally:    duration = time.time() - start_time
REQUEST_COUNT.labelsmethod=method, endpoint=endpoint, status_code=status_code.inc()
REQUEST_LATENCY.labelsmethod=method, endpoint=endpoint.observeduration
return wrapper
return decorator

def track_websocket_connectionschannel: str, action: str:
"""跟踪WebSocket连接"""
if action == 'connect':    ACTIVE_CONNECTIONS.labels(channel=channel).inc()
elif action == 'disconnect':    ACTIVE_CONNECTIONS.labels(channel=channel).dec()

def track_stock_data_fetchsymbol: str, source: str, success: bool:
"""跟踪股票数据获取"""
STOCK_DATA_FETCHES.labels(symbol=symbol, source=source, success=strsuccess).inc()

def track_strategy_predictionstrategy_name: str, symbol: str, success: bool:
"""跟踪策略预测"""
STRATEGY_PREDICTIONS.labels(strategy_name=strategy_name, symbol=symbol, success=strsuccess).inc()

def track_ml_trainingmodel_type: str, success: bool:
"""跟踪ML模型训练"""
ML_MODEL_TRAININGS.labels(model_type=model_type, success=strsuccess).inc()

def update_system_healthstatus: bool:
"""更新系统健康状态"""
SYSTEM_HEALTH.set1 if status else 0

async def metrics_endpoint():
"""Prometheus指标端点"""
return Response(
generate_latest(),
media_type=CONTENT_TYPE_LATEST
)

class MetricsCollector:
"""指标收集器"""

def __init__self:    self.start_time = time.time()
update_system_healthTrue

def record_system_startupself:
"""记录系统启动"""
logger.info"System startup recorded in metrics"

def record_system_shutdownself:
"""记录系统关闭"""
update_system_healthFalse
logger.info"System shutdown recorded in metrics"

def get_uptime_secondsself -> float:
"""获取系统运行时间"""
return time.time() - self.start_time

def record_custom_metricself, name: str, value: float, labels: dict = None:
"""记录自定义指标"""
# 这里可以扩展为动态创建指标
logger.infof"Custom metric: {name} = {value}, labels: {labels}"

metrics_collector = MetricsCollector()