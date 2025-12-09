"""
性能监控工具
监控系统性能指标，提供优化建议
"""

import asyncio
import logging
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import psutil


@dataclass
class PerformanceMetrics:
    """性能指标"""

    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_sent_mb: float
    network_recv_mb: float
    active_connections: int
    load_average: float


@dataclass
class AgentPerformanceMetrics:
    """代理性能指标"""

    agent_name: str
    start_time: datetime
    end_time: Optional[datetime]
    duration_seconds: Optional[float]
    memory_peak_mb: float
    cpu_peak_percent: float
    api_calls_count: int
    success: bool
    error_message: Optional[str] = None


class PerformanceMonitor:
    """性能监控器"""

    def __init__(self, max_history: int = 100):
        self.logger = logging.getLogger("hk_quant_system.performance_monitor")
        self.max_history = max_history
        self.metrics_history: deque = deque(maxlen=max_history)
        self.agent_metrics: Dict[str, AgentPerformanceMetrics] = {}
        self.is_monitoring = False
        self.monitor_task: Optional[asyncio.Task] = None

        # 初始系统状态
        self.initial_cpu = psutil.cpu_percent()
        self.initial_memory = psutil.virtual_memory()
        self.initial_disk = psutil.disk_io_counters()
        self.initial_network = psutil.net_io_counters()

    async def start_monitoring(self, interval_seconds: int = 10):
        """开始性能监控"""
        if self.is_monitoring:
            self.logger.warning("性能监控已在运行")
            return

        self.is_monitoring = True
        self.monitor_task = asyncio.create_task(self._monitor_loop(interval_seconds))
        self.logger.info(f"性能监控已启动，间隔: {interval_seconds}秒")

    async def stop_monitoring(self):
        """停止性能监控"""
        if not self.is_monitoring:
            return

        self.is_monitoring = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass

        self.logger.info("性能监控已停止")

    async def _monitor_loop(self, interval_seconds: int):
        """监控循环"""
        while self.is_monitoring:
            try:
                metrics = self._collect_metrics()
                self.metrics_history.append(metrics)

                # 检查性能警告
                await self._check_performance_warnings(metrics)

                await asyncio.sleep(interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"性能监控出错: {e}")
                await asyncio.sleep(interval_seconds)

    def _collect_metrics(self) -> PerformanceMetrics:
        """收集性能指标"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)

            # 内存使用情况
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_mb = memory.used / (1024 * 1024)

            # 磁盘IO
            disk_io = psutil.disk_io_counters()
            disk_read_mb = (
                (disk_io.read_bytes - self.initial_disk.read_bytes) / (1024 * 1024)
                if self.initial_disk
                else 0
            )
            disk_write_mb = (
                (disk_io.write_bytes - self.initial_disk.write_bytes) / (1024 * 1024)
                if self.initial_disk
                else 0
            )

            # 网络IO
            network_io = psutil.net_io_counters()
            network_sent_mb = (
                (network_io.bytes_sent - self.initial_network.bytes_sent)
                / (1024 * 1024)
                if self.initial_network
                else 0
            )
            network_recv_mb = (
                (network_io.bytes_recv - self.initial_network.bytes_recv)
                / (1024 * 1024)
                if self.initial_network
                else 0
            )

            # 活跃连接数
            connections = len(psutil.net_connections())

            # 系统负载（Linux / Unix）
            try:
                load_avg = psutil.getloadavg()[0]
            except AttributeError:
                load_avg = 0.0  # Windows不支持

            return PerformanceMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_used_mb=memory_used_mb,
                disk_io_read_mb=disk_read_mb,
                disk_io_write_mb=disk_write_mb,
                network_sent_mb=network_sent_mb,
                network_recv_mb=network_recv_mb,
                active_connections=connections,
                load_average=load_avg,
            )
        except Exception as e:
            self.logger.error(f"收集性能指标失败: {e}")
            return PerformanceMetrics(
                timestamp=datetime.now(),
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_used_mb=0.0,
                disk_io_read_mb=0.0,
                disk_io_write_mb=0.0,
                network_sent_mb=0.0,
                network_recv_mb=0.0,
                active_connections=0,
                load_average=0.0,
            )

    async def _check_performance_warnings(self, metrics: PerformanceMetrics):
        """检查性能警告"""
        warnings = []

        # CPU使用率警告
        if metrics.cpu_percent > 80:
            warnings.append(f"CPU使用率过高: {metrics.cpu_percent:.1f}%")

        # 内存使用率警告
        if metrics.memory_percent > 85:
            warnings.append(f"内存使用率过高: {metrics.memory_percent:.1f}%")

        # 系统负载警告
        if metrics.load_average > 4.0:
            warnings.append(f"系统负载过高: {metrics.load_average:.2f}")

        # 输出警告
        for warning in warnings:
            self.logger.warning(f"性能警告: {warning}")

    def start_agent_monitoring(self, agent_name: str) -> str:
        """开始监控代理性能"""
        agent_id = f"{agent_name}_{int(time.time())}"
        self.agent_metrics[agent_id] = AgentPerformanceMetrics(
            agent_name=agent_name,
            start_time=datetime.now(),
            end_time=None,
            duration_seconds=None,
            memory_peak_mb=0.0,
            cpu_peak_percent=0.0,
            api_calls_count=0,
            success=False,
        )
        return agent_id

    def update_agent_metrics(
        self,
        agent_id: str,
        memory_mb: float = None,
        cpu_percent: float = None,
        api_calls: int = None,
    ):
        """更新代理性能指标"""
        if agent_id not in self.agent_metrics:
            return

        metrics = self.agent_metrics[agent_id]

        if memory_mb is not None:
            metrics.memory_peak_mb = max(metrics.memory_peak_mb, memory_mb)

        if cpu_percent is not None:
            metrics.cpu_peak_percent = max(metrics.cpu_peak_percent, cpu_percent)

        if api_calls is not None:
            metrics.api_calls_count += api_calls

    def end_agent_monitoring(
        self, agent_id: str, success: bool = True, error_message: str = None
    ):
        """结束代理性能监控"""
        if agent_id not in self.agent_metrics:
            return

        metrics = self.agent_metrics[agent_id]
        metrics.end_time = datetime.now()
        metrics.duration_seconds = (
            metrics.end_time - metrics.start_time
        ).total_seconds()
        metrics.success = success
        metrics.error_message = error_message

        self.logger.info(
            f"代理 {metrics.agent_name} 性能统计: "
            f"耗时 {metrics.duration_seconds:.2f}s, "
            f"内存峰值 {metrics.memory_peak_mb:.1f}MB, "
            f"CPU峰值 {metrics.cpu_peak_percent:.1f}%, "
            f"API调用 {metrics.api_calls_count}次"
        )

    def get_performance_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        if not self.metrics_history:
            return {"error": "没有性能数据"}

        latest = self.metrics_history[-1]
        avg_cpu = sum(m.cpu_percent for m in self.metrics_history) / len(
            self.metrics_history
        )
        avg_memory = sum(m.memory_percent for m in self.metrics_history) / len(
            self.metrics_history
        )

        # 代理性能统计
        agent_stats = {}
        for agent_id, metrics in self.agent_metrics.items():
            if metrics.duration_seconds:
                agent_stats[metrics.agent_name] = {
                    "duration_seconds": metrics.duration_seconds,
                    "memory_peak_mb": metrics.memory_peak_mb,
                    "cpu_peak_percent": metrics.cpu_peak_percent,
                    "api_calls_count": metrics.api_calls_count,
                    "success": metrics.success,
                }

        return {
            "current_metrics": {
                "cpu_percent": latest.cpu_percent,
                "memory_percent": latest.memory_percent,
                "memory_used_mb": latest.memory_used_mb,
                "active_connections": latest.active_connections,
                "load_average": latest.load_average,
            },
            "average_metrics": {
                "avg_cpu_percent": avg_cpu,
                "avg_memory_percent": avg_memory,
            },
            "agent_performance": agent_stats,
            "monitoring_duration": len(self.metrics_history),
            "is_monitoring": self.is_monitoring,
        }

    def get_optimization_recommendations(self) -> List[str]:
        """获取优化建议"""
        recommendations = []

        if not self.metrics_history:
            return ["需要更多性能数据来提供建议"]

        # 分析最近10个数据点
        recent_metrics = list(self.metrics_history)[-10:]

        # CPU使用率分析
        avg_cpu = sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics)
        if avg_cpu > 70:
            recommendations.append("CPU使用率较高，建议启用并行处理或减少并发数")

        # 内存使用率分析
        avg_memory = sum(m.memory_percent for m in recent_metrics) / len(recent_metrics)
        if avg_memory > 80:
            recommendations.append("内存使用率较高，建议启用数据缓存清理或减少缓存大小")

        # 代理性能分析
        slow_agents = []
        for agent_id, metrics in self.agent_metrics.items():
            if metrics.duration_seconds and metrics.duration_seconds > 60:
                slow_agents.append(metrics.agent_name)

        if slow_agents:
            recommendations.append(
                f"以下代理执行较慢，建议优化: {', '.join(slow_agents)}"
            )

        # 系统负载分析
        if recent_metrics[-1].load_average > 2.0:
            recommendations.append("系统负载较高，建议减少同时运行的代理数量")

        if not recommendations:
            recommendations.append("系统性能良好，无需特别优化")

        return recommendations


# 全局性能监控实例
performance_monitor = PerformanceMonitor()
