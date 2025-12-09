"""
生产级健康监控系统
实时监控量化交易系统各组件健康状态
"""

import asyncio
import time
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
import psutil

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    """健康状态枚举"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

@dataclass
class ComponentHealth:
    """组件健康状态"""
    name: str
    status: HealthStatus
    message: str
    last_check: float
    response_time: Optional[float] = None
    metrics: Optional[Dict[str, Any]] = None

@dataclass
class HealthCheckResult:
    """健康检查结果"""
    overall_status: HealthStatus
    components: List[ComponentHealth]
    timestamp: float
    system_metrics: Dict[str, Any]

class HealthMonitor:
    """健康监控器"""
    
    def __init__(self, check_interval: int = 30):
        self.check_interval = check_interval
        self.components = {}
        self._running = False
        self._health_history = []
        
        # 健康检查端点配置
        self.check_endpoints = {
            "api_server": {
                "url": "http://localhost:8000/health",
                "timeout": 5,
                "expected_status": 200
            },
            "trading_engine": {
                "url": "http://localhost:8001/health",
                "timeout": 5,
                "expected_status": 200
            },
            "redis_cache": {
                "url": "http://localhost:6379",
                "timeout": 3,
                "type": "redis"
            },
            "prometheus": {
                "url": "http://localhost:9090/-/healthy",
                "timeout": 5,
                "expected_status": 200
            }
        }
    
    async def check_component_health(self, component_name: str, config: Dict[str, Any]) -> ComponentHealth:
        """检查单个组件健康状态"""
        start_time = time.time()
        
        try:
            if config.get("type") == "redis":
                # Redis健康检查
                health = await self._check_redis_health(config)
            else:
                # HTTP健康检查
                health = await self._check_http_health(component_name, config)
            
            response_time = time.time() - start_time
            health.response_time = response_time
            health.last_check = time.time()
            
            return health
            
        except Exception as e:
            logger.error(f"Health check failed for {component_name}: {e}")
            return ComponentHealth(
                name=component_name,
                status=HealthStatus.CRITICAL,
                message=f"Health check failed: {str(e)}",
                last_check=time.time(),
                response_time=time.time() - start_time
            )
    
    async def _check_http_health(self, component_name: str, config: Dict[str, Any]) -> ComponentHealth:
        """HTTP组件健康检查"""
        url = config["url"]
        timeout = config.get("timeout", 5)
        expected_status = config.get("expected_status", 200)
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=timeout) as response:
                if response.status == expected_status:
                    # 尝试解析健康检查响应
                    try:
                        health_data = await response.json()
                        message = health_data.get("status", "OK")
                        metrics = health_data.get("metrics", {})
                        
                        return ComponentHealth(
                            name=component_name,
                            status=HealthStatus.HEALTHY,
                            message=message,
                            last_check=time.time(),
                            metrics=metrics
                        )
                    except (json.JSONDecodeError, KeyError):
                        return ComponentHealth(
                            name=component_name,
                            status=HealthStatus.HEALTHY,
                            message=f"HTTP {response.status}",
                            last_check=time.time()
                        )
                else:
                    return ComponentHealth(
                        name=component_name,
                        status=HealthStatus.WARNING if response.status < 500 else HealthStatus.CRITICAL,
                        message=f"HTTP {response.status}: {response.reason}",
                        last_check=time.time()
                    )
    
    async def _check_redis_health(self, config: Dict[str, Any]) -> ComponentHealth:
        """Redis健康检查"""
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, decode_responses=True)
            
            # 测试基本连接
            info = r.info()
            
            # 检查内存使用
            memory_usage = info.get('used_memory', 0)
            max_memory = info.get('maxmemory', 0)
            
            if max_memory > 0:
                memory_percent = (memory_usage / max_memory) * 100
                if memory_percent > 90:
                    status = HealthStatus.WARNING
                    message = f"Redis memory usage high: {memory_percent:.1f}%"
                else:
                    status = HealthStatus.HEALTHY
                    message = f"Memory usage: {memory_percent:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"Memory usage: {memory_usage} bytes"
            
            metrics = {
                "connected_clients": info.get('connected_clients', 0),
                "used_memory": memory_usage,
                "uptime_seconds": info.get('uptime_in_seconds', 0)
            }
            
            return ComponentHealth(
                name="redis_cache",
                status=status,
                message=message,
                last_check=time.time(),
                metrics=metrics
            )
            
        except Exception as e:
            return ComponentHealth(
                name="redis_cache",
                status=HealthStatus.CRITICAL,
                message=f"Redis connection failed: {str(e)}",
                last_check=time.time()
            )
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """获取系统级指标"""
        try:
            # CPU信息
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # 内存信息
            memory = psutil.virtual_memory()
            
            # 磁盘信息
            disk = psutil.disk_usage('/')
            
            # 网络信息
            network = psutil.net_io_counters()
            
            # 进程信息
            process = psutil.Process()
            process_memory = process.memory_info()
            process_cpu = process.cpu_percent()
            
            return {
                "cpu": {
                    "usage_percent": cpu_percent,
                    "count": cpu_count
                },
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "used": memory.used,
                    "free": memory.free
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": (disk.used / disk.total) * 100
                },
                "network": {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv
                },
                "process": {
                    "pid": process.pid,
                    "memory_rss": process_memory.rss,
                    "memory_vms": process_memory.vms,
                    "cpu_percent": process_cpu,
                    "num_threads": process.num_threads(),
                    "create_time": process.create_time()
                }
            }
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            return {"error": str(e)}
    
    async def perform_health_checks(self) -> HealthCheckResult:
        """执行所有健康检查"""
        logger.info("Performing health checks...")
        
        # 检查所有组件
        components = []
        for component_name, config in self.check_endpoints.items():
            health = await self.check_component_health(component_name, config)
            components.append(health)
        
        # 获取系统指标
        system_metrics = self.get_system_metrics()
        
        # 确定整体健康状态
        overall_status = self._determine_overall_status(components, system_metrics)
        
        result = HealthCheckResult(
            overall_status=overall_status,
            components=components,
            timestamp=time.time(),
            system_metrics=system_metrics
        )
        
        # 记录健康检查历史
        self._health_history.append(result)
        if len(self._health_history) > 100:  # 保持最近100次检查
            self._health_history = self._health_history[-50:]
        
        return result
    
    def _determine_overall_status(self, components: List[ComponentHealth], 
                                system_metrics: Dict[str, Any]) -> HealthStatus:
        """确定整体健康状态"""
        # 检查是否有严重问题
        critical_components = [c for c in components if c.status == HealthStatus.CRITICAL]
        if critical_components:
            return HealthStatus.CRITICAL
        
        # 检查系统资源使用情况
        try:
            cpu_usage = system_metrics["cpu"]["usage_percent"]
            memory_usage = system_metrics["memory"]["percent"]
            disk_usage = system_metrics["disk"]["percent"]
            
            # 如果任何资源使用过高，标记为警告
            if cpu_usage > 90 or memory_usage > 90 or disk_usage > 95:
                return HealthStatus.WARNING
        except KeyError:
            pass  # 如果获取系统指标失败，跳过此检查
        
        # 检查是否有警告状态的组件
        warning_components = [c for c in components if c.status == HealthStatus.WARNING]
        if warning_components:
            return HealthStatus.WARNING
        
        # 所有检查都通过，系统健康
        return HealthStatus.HEALTHY
    
    def get_health_summary(self) -> Dict[str, Any]:
        """获取健康状态摘要"""
        if not self._health_history:
            return {"error": "No health check data available"}
        
        latest = self._health_history[-1]
        
        # 统计组件状态
        component_stats = {}
        for component in latest.components:
            status = component.status.value
            component_stats[status] = component_stats.get(status, 0) + 1
        
        # 计算可用性（最近一小时）
        one_hour_ago = time.time() - 3600
        recent_checks = [c for c in self._health_history if c.timestamp > one_hour_ago]
        
        if recent_checks:
            healthy_checks = len([c for c in recent_checks if c.overall_status == HealthStatus.HEALTHY])
            availability = (healthy_checks / len(recent_checks)) * 100
        else:
            availability = 0
        
        return {
            "overall_status": latest.overall_status.value,
            "timestamp": latest.timestamp,
            "components": component_stats,
            "availability_1h": availability,
            "total_checks": len(self._health_history),
            "last_check_age": time.time() - latest.timestamp
        }
    
    async def health_check_loop(self):
        """健康检查循环"""
        logger.info("Starting health check loop")
        
        while self._running:
            try:
                result = await self.perform_health_checks()
                
                # 记录健康状态
                logger.info(f"Health check completed: {result.overall_status.value}")
                
                if result.overall_status in [HealthStatus.WARNING, HealthStatus.CRITICAL]:
                    # 记录详细的问题信息
                    issues = [c for c in result.components if c.status != HealthStatus.HEALTHY]
                    for issue in issues:
                        logger.warning(f"Component {issue.name}: {issue.message}")
                
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
                await asyncio.sleep(10)  # 错误时短暂等待
    
    async def start(self):
        """启动健康监控"""
        logger.info("Starting health monitor...")
        self._running = True
        
        # 执行初始健康检查
        try:
            await self.perform_health_checks()
        except Exception as e:
            logger.error(f"Initial health check failed: {e}")
        
        # 启动健康检查循环
        await self.health_check_loop()
    
    def stop(self):
        """停止健康监控"""
        logger.info("Stopping health monitor...")
        self._running = False
    
    def export_health_data(self, filename: str = None) -> str:
        """导出健康数据为JSON"""
        if not filename:
            filename = f"health_data_{int(time.time())}.json"
        
        try:
            health_data = {
                "export_time": time.time(),
                "summary": self.get_health_summary(),
                "recent_checks": [asdict(check) for check in self._health_history[-10:]],
                "check_endpoints": self.check_endpoints
            }
            
            # 转换枚举为字符串
            def convert_enums(obj):
                if isinstance(obj, HealthStatus):
                    return obj.value
                elif isinstance(obj, dict):
                    return {k: convert_enums(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_enums(item) for item in obj]
                return obj
            
            health_data = convert_enums(health_data)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(health_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Health data exported to {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Failed to export health data: {e}")
            raise

async def main():
    """主函数 - 启动健康监控"""
    monitor = HealthMonitor(check_interval=30)
    
    try:
        await monitor.start()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
        monitor.stop()
        
        # 导出健康数据
        try:
            monitor.export_health_data()
        except Exception as e:
            logger.error(f"Failed to export health data on shutdown: {e}")
            
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        monitor.stop()
        raise

if __name__ == "__main__":
    asyncio.run(main())