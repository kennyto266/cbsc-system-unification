#!/usr/bin/env python3
"""
基礎設施監控模塊
Infrastructure Monitoring Module

監控服務器資源、GPU、Docker容器、數據庫等基礎設施
"""

import time
import psutil
import logging
import asyncio
import aiohttp
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import socket
import docker
from prometheus_client import CollectorRegistry, Gauge, Counter, Histogram, generate_latest
import GPUtil
import subprocess
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class SystemMetrics:
    """系統指標數據類"""
    timestamp: float
    hostname: str

    # CPU指標
    cpu_percent: float
    cpu_count: int
    cpu_freq: float

    # 內存指標
    memory_total: int
    memory_used: int
    memory_available: int
    memory_percent: float

    # 磁盤指標
    disk_total: int
    disk_used: int
    disk_free: int
    disk_percent: float

    # 網絡指標
    network_bytes_sent: int
    network_bytes_recv: int
    network_packets_sent: int
    network_packets_recv: int

    # 負載指標
    load_avg_1m: float
    load_avg_5m: float
    load_avg_15m: float

@dataclass
class GPUMetrics:
    """GPU指標數據類"""
    timestamp: float
    hostname: str

    # GPU基本信息
    gpu_id: str
    gpu_name: str
    gpu_temperature: float
    gpu_utilization: float

    # GPU內存
    memory_total: int
    memory_used: int
    memory_free: int
    memory_percent: float

    # GPU功耗
    power_draw: float
    power_limit: float

    # 進程信息
    processes: List[Dict[str, Any]]

class InfrastructureMonitor:
    """基礎設施監控器"""

    def __init__(self):
        """初始化監控器"""
        self.hostname = socket.gethostname()
        self.docker_client = None

        # 初始化Prometheus指標
        self.registry = CollectorRegistry()

        # 系統指標
        self.cpu_usage = Gauge('system_cpu_usage_percent', 'CPU usage percentage', ['hostname'], registry=self.registry)
        self.memory_usage = Gauge('system_memory_usage_percent', 'Memory usage percentage', ['hostname'], registry=self.registry)
        self.disk_usage = Gauge('system_disk_usage_percent', 'Disk usage percentage', ['hostname', 'mountpoint'], registry=self.registry)
        self.network_bytes_sent = Counter('system_network_bytes_sent_total', 'Total network bytes sent', ['hostname'], registry=self.registry)
        self.network_bytes_recv = Counter('system_network_bytes_recv_total', 'Total network bytes received', ['hostname'], registry=self.registry)
        self.load_average = Gauge('system_load_average', 'System load average', ['hostname', 'period'], registry=self.registry)

        # GPU指標
        self.gpu_utilization = Gauge('gpu_utilization_percent', 'GPU utilization percentage', ['hostname', 'gpu_id'], registry=self.registry)
        self.gpu_temperature = Gauge('gpu_temperature_celsius', 'GPU temperature in Celsius', ['hostname', 'gpu_id'], registry=self.registry)
        self.gpu_memory_usage = Gauge('gpu_memory_usage_percent', 'GPU memory usage percentage', ['hostname', 'gpu_id'], registry=self.registry)
        self.gpu_power_draw = Gauge('gpu_power_draw_watts', 'GPU power draw in watts', ['hostname', 'gpu_id'], registry=self.registry)

        # Docker指標
        self.docker_containers_total = Gauge('docker_containers_total', 'Total number of Docker containers', ['hostname'], registry=self.registry)
        self.docker_containers_running = Gauge('docker_containers_running', 'Number of running Docker containers', ['hostname'], registry=self.registry)
        self.docker_containers_stopped = Gauge('docker_containers_stopped', 'Number of stopped Docker containers', ['hostname'], registry=self.registry)

        # 監控狀態
        self.monitoring_active = True
        self.last_network_stats = None

        logger.info(f"Infrastructure monitor initialized for host: {self.hostname}")

        # 嘗試初始化Docker客戶端
        self._init_docker_client()

    def _init_docker_client(self):
        """初始化Docker客戶端"""
        try:
            self.docker_client = docker.from_env()
            self.docker_client.ping()
            logger.info("Docker client initialized successfully")
        except Exception as e:
            logger.warning(f"Docker client initialization failed: {e}")
            self.docker_client = None

    def collect_system_metrics(self) -> SystemMetrics:
        """
        收集系統指標

        Returns:
            SystemMetrics: 系統指標數據
        """
        try:
            # CPU指標
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq().current if psutil.cpu_freq() else 0

            # 內存指標
            memory = psutil.virtual_memory()

            # 磁盤指標
            disk = psutil.disk_usage('/')

            # 網絡指標
            network = psutil.net_io_counters()

            # 負載指標 (Linux/Unix系統)
            try:
                load_avg = psutil.getloadavg()
                load_avg_1m, load_avg_5m, load_avg_15m = load_avg
            except (AttributeError, OSError):
                # Windows系統沒有負載平均
                load_avg_1m = load_avg_5m = load_avg_15m = 0

            metrics = SystemMetrics(
                timestamp=time.time(),
                hostname=self.hostname,
                cpu_percent=cpu_percent,
                cpu_count=cpu_count,
                cpu_freq=cpu_freq,
                memory_total=memory.total,
                memory_used=memory.used,
                memory_available=memory.available,
                memory_percent=memory.percent,
                disk_total=disk.total,
                disk_used=disk.used,
                disk_free=disk.free,
                disk_percent=disk.percent,
                network_bytes_sent=network.bytes_sent,
                network_bytes_recv=network.bytes_recv,
                network_packets_sent=network.packets_sent,
                network_packets_recv=network.packets_recv,
                load_avg_1m=load_avg_1m,
                load_avg_5m=load_avg_5m,
                load_avg_15m=load_avg_15m
            )

            # 更新Prometheus指標
            self._update_system_prometheus_metrics(metrics)

            return metrics

        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            raise

    def collect_gpu_metrics(self) -> List[GPUMetrics]:
        """
        收集GPU指標

        Returns:
            List[GPUMetrics]: GPU指標數據列表
        """
        try:
            gpu_metrics = []
            gpus = GPUtil.getGPUs()

            for gpu in gpus:
                processes = []
                try:
                    # 獲取GPU進程信息
                    gpu_processes = gpulib.get_gpu_processes(gpu.id)  # 需要安裝nvidia-ml-py3
                    for proc in gpu_processes:
                        processes.append({
                            'pid': proc['pid'],
                            'process_name': proc['process_name'],
                            'memory_used': proc['used_memory'],
                            'gpu_utilization': proc['gpu_util']
                        })
                except:
                    # 如果無法獲取進程信息，使用空列表
                    pass

                metrics = GPUMetrics(
                    timestamp=time.time(),
                    hostname=self.hostname,
                    gpu_id=str(gpu.id),
                    gpu_name=gpu.name,
                    gpu_temperature=gpu.temperature,
                    gpu_utilization=gpu.load * 100,  # 轉換為百分比
                    memory_total=int(gpu.memoryTotal * 1024 * 1024),  # 轉換為字節
                    memory_used=int(gpu.memoryUsed * 1024 * 1024),
                    memory_free=int(gpu.memoryFree * 1024 * 1024),
                    memory_percent=(gpu.memoryUsed / gpu.memoryTotal) * 100,
                    power_draw=getattr(gpu, 'powerDraw', 0),
                    power_limit=getattr(gpu, 'powerLimit', 0),
                    processes=processes
                )

                gpu_metrics.append(metrics)

                # 更新Prometheus指標
                self._update_gpu_prometheus_metrics(metrics)

            return gpu_metrics

        except Exception as e:
            logger.error(f"Failed to collect GPU metrics: {e}")
            return []

    def collect_docker_metrics(self) -> Dict[str, Any]:
        """
        收集Docker指標

        Returns:
            Dict[str, Any]: Docker指標數據
        """
        if not self.docker_client:
            return {}

        try:
            containers = self.docker_client.containers.list(all=True)

            running_count = sum(1 for c in containers if c.status == 'running')
            stopped_count = sum(1 for c in containers if c.status != 'running')

            # 收集容器詳細信息
            container_details = []
            for container in containers:
                try:
                    stats = container.stats(stream=False)
                    container_details.append({
                        'name': container.name,
                        'status': container.status,
                        'image': container.image.tags[0] if container.image.tags else 'unknown',
                        'cpu_usage': self._calculate_container_cpu_usage(stats),
                        'memory_usage': self._calculate_container_memory_usage(stats),
                        'network_rx': stats.get('networks', {}).get('eth0', {}).get('rx_bytes', 0),
                        'network_tx': stats.get('networks', {}).get('eth0', {}).get('tx_bytes', 0)
                    })
                except Exception as e:
                    logger.warning(f"Failed to get stats for container {container.name}: {e}")
                    continue

            docker_metrics = {
                'total_containers': len(containers),
                'running_containers': running_count,
                'stopped_containers': stopped_count,
                'container_details': container_details
            }

            # 更新Prometheus指標
            self._update_docker_prometheus_metrics(docker_metrics)

            return docker_metrics

        except Exception as e:
            logger.error(f"Failed to collect Docker metrics: {e}")
            return {}

    def collect_database_metrics(self) -> Dict[str, Any]:
        """
        收集數據庫指標

        Returns:
            Dict[str, Any]: 數據庫指標數據
        """
        try:
            db_metrics = {}

            # PostgreSQL指標 (如果可用)
            try:
                db_metrics['postgresql'] = self._collect_postgresql_metrics()
            except Exception as e:
                logger.debug(f"PostgreSQL metrics collection failed: {e}")

            # Redis指標 (如果可用)
            try:
                db_metrics['redis'] = self._collect_redis_metrics()
            except Exception as e:
                logger.debug(f"Redis metrics collection failed: {e}")

            return db_metrics

        except Exception as e:
            logger.error(f"Failed to collect database metrics: {e}")
            return {}

    def _collect_postgresql_metrics(self) -> Dict[str, Any]:
        """收集PostgreSQL指標"""
        try:
            import psycopg2
            # 這裡需要根據實際數據庫配置調整連接參數
            conn = psycopg2.connect(
                host="localhost",
                database="postgres",
                user="postgres",
                password="password"
            )

            with conn.cursor() as cursor:
                # 活躍連接數
                cursor.execute("SELECT count(*) FROM pg_stat_activity WHERE state = 'active'")
                active_connections = cursor.fetchone()[0]

                # 數據庫大小
                cursor.execute(
                    "SELECT pg_database_size('quantitative_trading')"
                )
                database_size = cursor.fetchone()[0]

                # 查詢統計
                cursor.execute(
                    """
                    SELECT
                        count(*) as total_queries,
                        avg(extract(epoch from (now() - query_start))) as avg_query_time
                    FROM pg_stat_activity
                    WHERE state = 'active'
                    """
                )
                query_stats = cursor.fetchone()

            conn.close()

            return {
                'active_connections': active_connections,
                'database_size': database_size,
                'total_queries': query_stats[0] if query_stats else 0,
                'avg_query_time': query_stats[1] if query_stats else 0
            }

        except Exception as e:
            logger.debug(f"PostgreSQL metrics not available: {e}")
            return {}

    def _collect_redis_metrics(self) -> Dict[str, Any]:
        """收集Redis指標"""
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, decode_responses=True)
            info = r.info()

            return {
                'used_memory': info.get('used_memory', 0),
                'used_memory_peak': info.get('used_memory_peak', 0),
                'connected_clients': info.get('connected_clients', 0),
                'total_commands_processed': info.get('total_commands_processed', 0),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'hit_rate': (
                    info.get('keyspace_hits', 0) /
                    (info.get('keyspace_hits', 0) + info.get('keyspace_misses', 1))
                ) if info.get('keyspace_hits', 0) + info.get('keyspace_misses', 0) > 0 else 0
            }

        except Exception as e:
            logger.debug(f"Redis metrics not available: {e}")
            return {}

    def _update_system_prometheus_metrics(self, metrics: SystemMetrics):
        """更新系統Prometheus指標"""
        try:
            self.cpu_usage.labels(hostname=self.hostname).set(metrics.cpu_percent)
            self.memory_usage.labels(hostname=self.hostname).set(metrics.memory_percent)
            self.disk_usage.labels(hostname=self.hostname, mountpoint="/").set(metrics.disk_percent)
            self.load_average.labels(hostname=self.hostname, period="1m").set(metrics.load_avg_1m)
            self.load_average.labels(hostname=self.hostname, period="5m").set(metrics.load_avg_5m)
            self.load_average.labels(hostname=self.hostname, period="15m").set(metrics.load_avg_15m)

            # 網絡指標是計數器，需要增量更新
            if self.last_network_stats:
                self.network_bytes_sent.labels(hostname=self.hostname)._value._value += (
                    metrics.network_bytes_sent - self.last_network_stats['bytes_sent']
                )
                self.network_bytes_recv.labels(hostname=self.hostname)._value._value += (
                    metrics.network_bytes_recv - self.last_network_stats['bytes_recv']
                )

            self.last_network_stats = {
                'bytes_sent': metrics.network_bytes_sent,
                'bytes_recv': metrics.network_bytes_recv
            }

        except Exception as e:
            logger.error(f"Failed to update system Prometheus metrics: {e}")

    def _update_gpu_prometheus_metrics(self, metrics: GPUMetrics):
        """更新GPU Prometheus指標"""
        try:
            self.gpu_utilization.labels(hostname=self.hostname, gpu_id=metrics.gpu_id).set(metrics.gpu_utilization)
            self.gpu_temperature.labels(hostname=self.hostname, gpu_id=metrics.gpu_id).set(metrics.gpu_temperature)
            self.gpu_memory_usage.labels(hostname=self.hostname, gpu_id=metrics.gpu_id).set(metrics.memory_percent)
            self.gpu_power_draw.labels(hostname=self.hostname, gpu_id=metrics.gpu_id).set(metrics.power_draw)

        except Exception as e:
            logger.error(f"Failed to update GPU Prometheus metrics: {e}")

    def _update_docker_prometheus_metrics(self, metrics: Dict[str, Any]):
        """更新Docker Prometheus指標"""
        try:
            self.docker_containers_total.labels(hostname=self.hostname).set(metrics['total_containers'])
            self.docker_containers_running.labels(hostname=self.hostname).set(metrics['running_containers'])
            self.docker_containers_stopped.labels(hostname=self.hostname).set(metrics['stopped_containers'])

        except Exception as e:
            logger.error(f"Failed to update Docker Prometheus metrics: {e}")

    def _calculate_container_cpu_usage(self, stats: Dict[str, Any]) -> float:
        """計算容器CPU使用率"""
        try:
            cpu_stats = stats.get('cpu_stats', {})
            precpu_stats = stats.get('precpu_stats', {})

            cpu_delta = cpu_stats.get('cpu_usage', {}).get('total_usage', 0) - \
                       precpu_stats.get('cpu_usage', {}).get('total_usage', 0)
            system_delta = cpu_stats.get('system_cpu_usage', 0) - \
                          precpu_stats.get('system_cpu_usage', 0)

            if system_delta > 0:
                cpu_count = cpu_stats.get('online_cpus', 1)
                return (cpu_delta / system_delta) * cpu_count * 100

            return 0.0

        except Exception:
            return 0.0

    def _calculate_container_memory_usage(self, stats: Dict[str, Any]) -> float:
        """計算容器內存使用量"""
        try:
            memory_stats = stats.get('memory_stats', {})
            usage = memory_stats.get('usage', 0)
            limit = memory_stats.get('limit', 1)

            return (usage / limit) * 100 if limit > 0 else 0.0

        except Exception:
            return 0.0

    async def collect_all_metrics(self) -> Dict[str, Any]:
        """
        異步收集所有指標

        Returns:
            Dict[str, Any]: 所有指標數據
        """
        try:
            # 並行收集各類指標
            tasks = [
                asyncio.create_task(asyncio.to_thread(self.collect_system_metrics)),
                asyncio.create_task(asyncio.to_thread(self.collect_gpu_metrics)),
                asyncio.create_task(asyncio.to_thread(self.collect_docker_metrics)),
                asyncio.create_task(asyncio.to_thread(self.collect_database_metrics))
            ]

            system_metrics, gpu_metrics, docker_metrics, db_metrics = await asyncio.gather(*tasks)

            return {
                'timestamp': time.time(),
                'hostname': self.hostname,
                'system': asdict(system_metrics) if system_metrics else None,
                'gpus': [asdict(gpu) for gpu in gpu_metrics] if gpu_metrics else [],
                'docker': docker_metrics,
                'database': db_metrics
            }

        except Exception as e:
            logger.error(f"Failed to collect all metrics: {e}")
            return {}

    def get_prometheus_metrics(self) -> str:
        """
        獲取Prometheus格式的指標

        Returns:
            str: Prometheus格式指標數據
        """
        return generate_latest(self.registry).decode('utf-8')

    async def start_monitoring_loop(self, interval: int = 15):
        """
        啟動監控循環

        Args:
            interval: 監控間隔(秒)
        """
        logger.info(f"Starting infrastructure monitoring loop with {interval}s interval")

        while self.monitoring_active:
            try:
                metrics = await self.collect_all_metrics()

                # 保存指標到文件 (可選，用於調試)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                metrics_file = f"infrastructure_metrics_{timestamp}.json"

                # 可以根據需要保存指標
                # with open(metrics_file, 'w') as f:
                #     json.dump(metrics, f, indent=2, default=str)

                logger.debug(f"Infrastructure metrics collected: {len(str(metrics))} bytes")

                await asyncio.sleep(interval)

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(interval)

    def stop_monitoring(self):
        """停止監控"""
        self.monitoring_active = False
        logger.info("Infrastructure monitoring stopped")

# 全局監控器實例
infrastructure_monitor = InfrastructureMonitor()

def get_infrastructure_monitor() -> InfrastructureMonitor:
    """獲取基礎設施監控器實例"""
    return infrastructure_monitor

if __name__ == "__main__":
    async def main():
        """測試監控功能"""
        monitor = InfrastructureMonitor()

        # 測試收集指標
        print("Testing metrics collection...")

        system_metrics = monitor.collect_system_metrics()
        print(f"System metrics: CPU={system_metrics.cpu_percent}%, Memory={system_metrics.memory_percent}%")

        gpu_metrics = monitor.collect_gpu_metrics()
        if gpu_metrics:
            print(f"GPU metrics: {len(gpu_metrics)} GPUs found")
            for gpu in gpu_metrics:
                print(f"  GPU {gpu.gpu_id}: {gpu.gpu_utilization:.1f}% utilization, {gpu.gpu_temperature:.1f}°C")

        docker_metrics = monitor.collect_docker_metrics()
        if docker_metrics:
            print(f"Docker metrics: {docker_metrics['running_containers']}/{docker_metrics['total_containers']} running")

        # 獲取Prometheus指標
        prometheus_metrics = monitor.get_prometheus_metrics()
        print(f"\nPrometheus metrics generated: {len(prometheus_metrics)} bytes")

        # 啟動監控循環 (測試運行5次)
        print("\nStarting monitoring loop (5 iterations)...")
        for i in range(5):
            metrics = await monitor.collect_all_metrics()
            print(f"Collection {i+1}: System OK, GPU count: {len(metrics.get('gpus', []))}")
            await asyncio.sleep(10)

        print("Monitoring test completed!")

    asyncio.run(main())