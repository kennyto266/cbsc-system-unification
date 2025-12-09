"""
生产级Prometheus监控服务器
量化交易系统实时指标收集和警报
"""

import time
import logging
from typing import Dict, Any, List
from dataclasses import dataclass
from prometheus_client import start_http_server, Gauge, Counter, Histogram, Info
import psutil
import asyncio
import pandas as pd

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class MetricsConfig:
    """监控配置"""
    prometheus_port: int = 9090
    collection_interval: int = 15
    max_workers: int = 4

class QuantitativeTradingMetrics:
    """量化交易系统指标收集器"""
    
    def __init__(self, config: MetricsConfig):
        self.config = config
        
        # 系统性能指标
        self.cpu_usage = Gauge('cpu_usage_percent', 'CPU使用率')
        self.memory_usage = Gauge('memory_usage_percent', '内存使用率')
        self.memory_total = Gauge('memory_total_bytes', '总内存量')
        self.memory_available = Gauge('memory_available_bytes', '可用内存量')
        self.disk_usage = Gauge('disk_usage_percent', '磁盘使用率')
        self.disk_total = Gauge('disk_total_bytes', '总磁盘空间')
        self.disk_free = Gauge('disk_free_bytes', '可用磁盘空间')
        
        # API性能指标
        self.http_requests_total = Counter('http_requests_total', 'HTTP请求总数', ['method', 'endpoint', 'status'])
        self.http_request_duration = Histogram('http_request_duration_seconds', 'HTTP请求延迟', ['method', 'endpoint'])
        self.api_response_size = Histogram('api_response_size_bytes', 'API响应大小', ['endpoint'])
        
        # 量化交易业务指标
        self.active_strategies = Gauge('active_strategies_count', '活跃策略数量')
        self.total_backtests = Counter('total_backtests', '回测总数')
        self.optimization_queue_size = Gauge('optimization_queue_size', '优化队列大小')
        self.optimization_in_progress = Gauge('optimization_in_progress', '进行中的优化任务')
        
        # 策略性能指标
        self.strategy_sharpe_ratio = Gauge('strategy_sharpe_ratio', '策略Sharpe比率', ['strategy_name', 'symbol'])
        self.strategy_total_return = Gauge('strategy_total_return', '策略总回报率', ['strategy_name', 'symbol'])
        self.strategy_max_drawdown = Gauge('strategy_max_drawdown', '策略最大回撤', ['strategy_name', 'symbol'])
        self.strategy_win_rate = Gauge('strategy_win_rate', '策略胜率', ['strategy_name', 'symbol'])
        self.strategy_execution_time = Histogram('strategy_execution_time_seconds', '策略执行时间')
        
        # 数据质量指标
        self.data_freshness = Gauge('data_freshness_minutes', '数据新鲜度（分钟）')
        self.missing_data_points = Counter('missing_data_points_total', '缺失数据点', ['symbol', 'data_type'])
        self.data_quality_score = Gauge('data_quality_score', '数据质量评分', ['symbol'])
        
        # 风险管理指标
        self.portfolio_value = Gauge('portfolio_value', '投资组合价值')
        self.daily_pnl = Gauge('daily_pnl', '日盈亏')
        self.position_count = Gauge('position_count', '持仓数量')
        self.risk_score = Gauge('risk_score', '风险评分')
        self.margin_call_warning = Gauge('margin_call_warning', '保证金警告')
        
        # 应用信息
        self.app_info = Info('application_info', '应用信息')
        
        # 设置应用信息
        self.app_info.info({
            'version': '1.0.0',
            'environment': 'production',
            'build_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'python_version': f"{psutil.sys.version_info.major}.{psutil.sys.version_info.minor}",
            'cpu_count': str(psutil.cpu_count()),
            'memory_total_gb': f"{psutil.virtual_memory().total // (1024**3)}GB"
        })
        
        # 初始化系统状态
        self._running = False
        self._system_stats_history = []
        
    def start_metrics_server(self):
        """启动Prometheus指标服务器"""
        try:
            start_http_server(self.config.prometheus_port)
            logger.info(f"Prometheus metrics server started on port {self.config.prometheus_port}")
            self._running = True
        except Exception as e:
            logger.error(f"Failed to start metrics server: {e}")
            raise
    
    async def collect_system_metrics(self):
        """收集系统性能指标"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            self.cpu_usage.set(cpu_percent)
            
            # 内存使用情况
            memory = psutil.virtual_memory()
            self.memory_usage.set(memory.percent)
            self.memory_total.set(memory.total)
            self.memory_available.set(memory.available)
            
            # 磁盘使用情况
            disk = psutil.disk_usage('/')
            self.disk_usage.set((disk.used / disk.total) * 100)
            self.disk_total.set(disk.total)
            self.disk_free.set(disk.free)
            
            # 记录历史数据
            self._system_stats_history.append({
                'timestamp': time.time(),
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'disk_percent': (disk.used / disk.total) * 100
            })
            
            # 保持历史数据在合理范围内
            if len(self._system_stats_history) > 1000:
                self._system_stats_history = self._system_stats_history[-500:]
                
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
    
    def record_api_request(self, method: str, endpoint: str, status: int, duration: float, response_size: int):
        """记录API请求指标"""
        try:
            self.http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status=str(status)
            ).inc()
            
            self.http_request_duration.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
            
            self.api_response_size.labels(endpoint=endpoint).observe(response_size)
            
        except Exception as e:
            logger.error(f"Failed to record API request metrics: {e}")
    
    def update_strategy_performance(self, strategy_name: str, symbol: str, 
                                  sharpe_ratio: float, total_return: float, 
                                  max_drawdown: float, win_rate: float):
        """更新策略性能指标"""
        try:
            self.strategy_sharpe_ratio.labels(
                strategy_name=strategy_name,
                symbol=symbol
            ).set(sharpe_ratio)
            
            self.strategy_total_return.labels(
                strategy_name=strategy_name,
                symbol=symbol
            ).set(total_return)
            
            self.strategy_max_drawdown.labels(
                strategy_name=strategy_name,
                symbol=symbol
            ).set(max_drawdown)
            
            self.strategy_win_rate.labels(
                strategy_name=strategy_name,
                symbol=symbol
            ).set(win_rate)
            
        except Exception as e:
            logger.error(f"Failed to update strategy performance metrics: {e}")
    
    def record_strategy_execution(self, execution_time: float):
        """记录策略执行时间"""
        try:
            self.strategy_execution_time.observe(execution_time)
        except Exception as e:
            logger.error(f"Failed to record strategy execution time: {e}")
    
    def update_optimization_metrics(self, queue_size: int, in_progress: int):
        """更新优化任务指标"""
        try:
            self.optimization_queue_size.set(queue_size)
            self.optimization_in_progress.set(in_progress)
        except Exception as e:
            logger.error(f"Failed to update optimization metrics: {e}")
    
    def increment_backtest_count(self):
        """增加回测计数"""
        try:
            self.total_backtests.inc()
        except Exception as e:
            logger.error(f"Failed to increment backtest count: {e}")
    
    def update_data_quality_metrics(self, symbol: str, freshness_minutes: int, 
                                  quality_score: float, missing_points: Dict[str, int]):
        """更新数据质量指标"""
        try:
            self.data_freshness.set(freshness_minutes)
            self.data_quality_score.labels(symbol=symbol).set(quality_score)
            
            for data_type, count in missing_points.items():
                self.missing_data_points.labels(
                    symbol=symbol,
                    data_type=data_type
                ).inc(count)
                
        except Exception as e:
            logger.error(f"Failed to update data quality metrics: {e}")
    
    def update_risk_metrics(self, portfolio_value: float, daily_pnl: float, 
                          position_count: int, risk_score: float, margin_warning: int):
        """更新风险管理指标"""
        try:
            self.portfolio_value.set(portfolio_value)
            self.daily_pnl.set(daily_pnl)
            self.position_count.set(position_count)
            self.risk_score.set(risk_score)
            self.margin_call_warning.set(margin_warning)
        except Exception as e:
            logger.error(f"Failed to update risk metrics: {e}")
    
    def get_system_summary(self) -> Dict[str, Any]:
        """获取系统状态摘要"""
        try:
            current_time = time.time()
            recent_stats = [s for s in self._system_stats_history 
                          if current_time - s['timestamp'] < 3600]  # 最近1小时
            
            if not recent_stats:
                return {"error": "No recent data available"}
            
            # 计算平均值
            avg_cpu = sum(s['cpu_percent'] for s in recent_stats) / len(recent_stats)
            avg_memory = sum(s['memory_percent'] for s in recent_stats) / len(recent_stats)
            avg_disk = sum(s['disk_percent'] for s in recent_stats) / len(recent_stats)
            
            return {
                "timestamp": current_time,
                "current_cpu": recent_stats[-1]['cpu_percent'],
                "current_memory": recent_stats[-1]['memory_percent'],
                "current_disk": recent_stats[-1]['disk_percent'],
                "avg_cpu_1h": avg_cpu,
                "avg_memory_1h": avg_memory,
                "avg_disk_1h": avg_disk,
                "data_points": len(recent_stats),
                "health_status": "healthy" if avg_cpu < 80 and avg_memory < 85 else "warning"
            }
            
        except Exception as e:
            logger.error(f"Failed to get system summary: {e}")
            return {"error": str(e)}
    
    async def run_metrics_collection_loop(self):
        """运行指标收集循环"""
        logger.info("Starting metrics collection loop")
        
        while self._running:
            try:
                await self.collect_system_metrics()
                await asyncio.sleep(self.config.collection_interval)
            except Exception as e:
                logger.error(f"Error in metrics collection loop: {e}")
                await asyncio.sleep(5)  # 错误时短暂等待
    
    def stop(self):
        """停止指标收集"""
        logger.info("Stopping metrics collection")
        self._running = False

async def main():
    """主函数 - 启动监控服务器"""
    config = MetricsConfig()
    metrics = QuantitativeTradingMetrics(config)
    
    try:
        # 启动Prometheus服务器
        metrics.start_metrics_server()
        
        # 启动指标收集循环
        await metrics.run_metrics_collection_loop()
        
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
        metrics.stop()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        metrics.stop()
        raise

if __name__ == "__main__":
    asyncio.run(main())