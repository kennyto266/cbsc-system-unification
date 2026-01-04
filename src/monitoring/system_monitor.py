"""
System Metrics Collector
系統指標收集器

提供系統級別的指標收集，包括 CPU、內存、磁盤、網絡和進程指標。

Usage:
    ```python
    from src.monitoring import get_system_monitor

    monitor = get_system_monitor()

    # Get system metrics
    cpu = monitor.get_cpu_usage()
    memory = monitor.get_memory_usage()
    disk = monitor.get_disk_usage()

    # Start continuous monitoring
    await monitor.start_monitoring(interval=15)
    ```
"""

import time
import asyncio
import threading
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from collections import deque
from enum import Enum

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("Warning: psutil not available. Install with: pip install psutil")


class MetricCategory(Enum):
    """指標類別"""
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    PROCESS = "process"


@dataclass
class CPUMetrics:
    """CPU 指標"""
    timestamp: float
    usage_percent: float
    usage_per_core: List[float]
    load_average: List[float]
    context_switches: int
    interrupts: int


@dataclass
class MemoryMetrics:
    """內存指標"""
    timestamp: float
    total_bytes: int
    available_bytes: int
    used_bytes: int
    free_bytes: int
    cached_bytes: int
    buffers_bytes: int
    swap_total_bytes: int
    swap_used_bytes: int
    usage_percent: float


@dataclass
class DiskMetrics:
    """磁盤指標"""
    timestamp: float
    mount_point: str
    total_bytes: int
    used_bytes: int
    free_bytes: int
    usage_percent: float
    read_bytes: int
    write_bytes: int
    read_count: int
    write_count: int


@dataclass
class NetworkMetrics:
    """網絡指標"""
    timestamp: float
    interface: str
    bytes_sent: int
    bytes_recv: int
    packets_sent: int
    packets_recv: int
    errors_in: int
    errors_out: int
    drops_in: int
    drops_out: int


@dataclass
class ProcessMetrics:
    """進程指標"""
    timestamp: float
    pid: int
    name: str
    status: str
    cpu_percent: float
    memory_percent: float
    memory_rss_bytes: int
    memory_vms_bytes: int
    num_threads: int
    num_fds: int
    create_time: float


@dataclass
class SystemSnapshot:
    """系統快照"""
    timestamp: float
    cpu: CPUMetrics
    memory: MemoryMetrics
    disks: Dict[str, DiskMetrics]
    networks: Dict[str, NetworkMetrics]
    processes: Dict[int, ProcessMetrics]


class SystemMetricsCollector:
    """
    系統指標收集器

    收集系統級別的性能指標，包括 CPU、內存、磁盤、網絡和進程。

    Attributes:
        history_size: 歷史數據保留數量
        monitoring_interval: 監控間隔（秒）
    """

    def __init__(self, history_size: int = 1000, monitoring_interval: float = 15.0):
        self.history_size = history_size
        self.monitoring_interval = monitoring_interval
        self._monitoring_active = False
        self._monitoring_task: Optional[asyncio.Task] = None

        # History storage
        self._cpu_history: deque = deque(maxlen=history_size)
        self._memory_history: deque = deque(maxlen=history_size)
        self._snapshots: deque = deque(maxlen=history_size)

        # Network baseline (for calculating deltas)
        self._network_baseline: Dict[str, Dict[str, int]] = {}

    def get_cpu_usage(self, per_cpu: bool = True) -> CPUMetrics:
        """獲取 CPU 使用率"""
        if not PSUTIL_AVAILABLE:
            return self._mock_cpu_metrics()

        cpu_percent = psutil.cpu_percent(interval=0.1)
        per_cpu_percent = psutil.cpu_percent(interval=0.1, percpu=True) if per_cpu else []

        # Load average (Unix only)
        load_avg = list(psutil.getloadavg()) if hasattr(psutil, 'getloadavg') else [0, 0, 0]

        # CPU stats
        cpu_stats = psutil.cpu_stats()

        return CPUMetrics(
            timestamp=time.time(),
            usage_percent=cpu_percent,
            usage_per_core=per_cpu_percent,
            load_average=load_avg,
            context_switches=cpu_stats.ctx_switches,
            interrupts=cpu_stats.interrupts
        )

    def get_memory_usage(self) -> MemoryMetrics:
        """獲取內存使用情況"""
        if not PSUTIL_AVAILABLE:
            return self._mock_memory_metrics()

        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()

        return MemoryMetrics(
            timestamp=time.time(),
            total_bytes=memory.total,
            available_bytes=memory.available,
            used_bytes=memory.used,
            free_bytes=memory.free,
            cached_bytes=getattr(memory, 'cached', 0),
            buffers_bytes=getattr(memory, 'buffers', 0),
            swap_total_bytes=swap.total,
            swap_used_bytes=swap.used,
            usage_percent=memory.percent
        )

    def get_disk_usage(self, mount_point: str = None) -> Dict[str, DiskMetrics]:
        """獲取磁盤使用情況"""
        if not PSUTIL_AVAILABLE:
            return {}

        disks = {}
        partitions = psutil.disk_partitions(all=True)

        for partition in partitions:
            try:
                if mount_point and partition.mountpoint != mount_point:
                    continue

                usage = psutil.disk_usage(partition.mountpoint)
                disks[partition.mountpoint] = DiskMetrics(
                    timestamp=time.time(),
                    mount_point=partition.mountpoint,
                    total_bytes=usage.total,
                    used_bytes=usage.used,
                    free_bytes=usage.free,
                    usage_percent=usage.percent,
                    read_bytes=0,
                    write_bytes=0,
                    read_count=0,
                    write_count=0
                )
            except (PermissionError, OSError):
                continue

        return disks

    def get_disk_io(self) -> Dict[str, DiskMetrics]:
        """獲取磁盤 I/O 統計"""
        if not PSUTIL_AVAILABLE:
            return {}

        disks = {}
        io_counters = psutil.disk_io_counters(perdisk=True)

        for device, counters in io_counters.items():
            disks[device] = DiskMetrics(
                timestamp=time.time(),
                mount_point="",
                total_bytes=0,
                used_bytes=0,
                free_bytes=0,
                usage_percent=0,
                read_bytes=counters.read_bytes,
                write_bytes=counters.write_bytes,
                read_count=counters.read_count,
                write_count=counters.write_count
            )

        return disks

    def get_network_stats(self) -> Dict[str, NetworkMetrics]:
        """獲取網絡統計"""
        if not PSUTIL_AVAILABLE:
            return {}

        networks = {}
        io_counters = psutil.net_io_counters(pernic=True)

        for interface, counters in io_counters.items():
            networks[interface] = NetworkMetrics(
                timestamp=time.time(),
                interface=interface,
                bytes_sent=counters.bytes_sent,
                bytes_recv=counters.bytes_recv,
                packets_sent=counters.packets_sent,
                packets_recv=counters.packets_recv,
                errors_in=counters.errin,
                errors_out=counters.errout,
                drops_in=counters.dropin,
                drops_out=counters.dropout
            )

        return networks

    def get_process_info(self, pid: int = None) -> ProcessMetrics:
        """獲取進程信息"""
        if not PSUTIL_AVAILABLE:
            return self._mock_process_metrics()

        try:
            process = psutil.Process(pid)
            with process.oneshot():
                return ProcessMetrics(
                    timestamp=time.time(),
                    pid=process.pid,
                    name=process.name(),
                    status=process.status(),
                    cpu_percent=process.cpu_percent(),
                    memory_percent=process.memory_percent(),
                    memory_rss_bytes=process.memory_info().rss,
                    memory_vms_bytes=process.memory_info().vms,
                    num_threads=process.num_threads(),
                    num_fds=process.num_fds() if hasattr(process, 'num_fds') else 0,
                    create_time=process.create_time()
                )
        except psutil.NoSuchProcess:
            return self._mock_process_metrics()

    def get_all_processes(self, filter_name: str = None) -> Dict[int, ProcessMetrics]:
        """獲取所有進程信息"""
        if not PSUTIL_AVAILABLE:
            return {}

        processes = {}
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if filter_name and filter_name.lower() not in proc.info['name'].lower():
                    continue

                with proc.oneshot():
                    processes[proc.pid] = ProcessMetrics(
                        timestamp=time.time(),
                        pid=proc.pid,
                        name=proc.name(),
                        status=proc.status(),
                        cpu_percent=proc.cpu_percent(),
                        memory_percent=proc.memory_percent(),
                        memory_rss_bytes=proc.memory_info().rss,
                        memory_vms_bytes=proc.memory_info().vms,
                        num_threads=proc.num_threads(),
                        num_fds=proc.num_fds() if hasattr(proc, 'num_fds') else 0,
                        create_time=proc.create_time()
                    )
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return processes

    def take_snapshot(self) -> SystemSnapshot:
        """創建系統快照"""
        return SystemSnapshot(
            timestamp=time.time(),
            cpu=self.get_cpu_usage(),
            memory=self.get_memory_usage(),
            disks=self.get_disk_usage(),
            networks=self.get_network_stats(),
            processes=self.get_all_processes()
        )

    async def start_monitoring(self, interval: float = None):
        """啟動持續監控"""
        if self._monitoring_active:
            return

        interval = interval or self.monitoring_interval
        self._monitoring_active = True

        async def monitoring_loop():
            while self._monitoring_active:
                snapshot = self.take_snapshot()
                self._snapshots.append(snapshot)
                self._cpu_history.append(snapshot.cpu)
                self._memory_history.append(snapshot.memory)
                await asyncio.sleep(interval)

        self._monitoring_task = asyncio.create_task(monitoring_loop())

    async def stop_monitoring(self):
        """停止監控"""
        self._monitoring_active = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
            self._monitoring_task = None

    def get_cpu_history(self, count: int = 100) -> List[CPUMetrics]:
        """獲取 CPU 歷史數據"""
        return list(self._cpu_history)[-count:]

    def get_memory_history(self, count: int = 100) -> List[MemoryMetrics]:
        """獲取內存歷史數據"""
        return list(self._memory_history)[-count:]

    def get_average_cpu(self, samples: int = 100) -> float:
        """獲取平均 CPU 使用率"""
        history = self.get_cpu_history(samples)
        if not history:
            return 0
        return sum(m.usage_percent for m in history) / len(history)

    def get_average_memory(self, samples: int = 100) -> float:
        """獲取平均內存使用率"""
        history = self.get_memory_history(samples)
        if not history:
            return 0
        return sum(m.usage_percent for m in history) / len(history)

    def get_summary(self) -> Dict[str, Any]:
        """獲取系統摘要"""
        snapshot = self.take_snapshot()

        return {
            "timestamp": snapshot.timestamp,
            "cpu": {
                "usage_percent": snapshot.cpu.usage_percent,
                "cores": len(snapshot.cpu.usage_per_core),
                "load_average": snapshot.cpu.load_average,
            },
            "memory": {
                "total_gb": snapshot.memory.total_bytes / (1024**3),
                "used_gb": snapshot.memory.used_bytes / (1024**3),
                "available_gb": snapshot.memory.available_bytes / (1024**3),
                "usage_percent": snapshot.memory.usage_percent,
            },
            "disks": {
                mount: {
                    "total_gb": disk.total_bytes / (1024**3),
                    "used_gb": disk.used_bytes / (1024**3),
                    "free_gb": disk.free_bytes / (1024**3),
                    "usage_percent": disk.usage_percent,
                }
                for mount, disk in snapshot.disks.items()
            },
            "network": {
                interface: {
                    "bytes_sent": net.bytes_sent,
                    "bytes_recv": net.bytes_recv,
                    "packets_sent": net.packets_sent,
                    "packets_recv": net.packets_recv,
                }
                for interface, net in snapshot.networks.items()
            },
            "processes": {
                "total": len(snapshot.processes),
                "top_cpu": sorted(
                    [(p.name, p.cpu_percent) for p in snapshot.processes.values()],
                    key=lambda x: x[1],
                    reverse=True
                )[:10],
            },
            "psutil_available": PSUTIL_AVAILABLE,
        }

    # Mock methods for when psutil is not available
    def _mock_cpu_metrics(self) -> CPUMetrics:
        return CPUMetrics(
            timestamp=time.time(),
            usage_percent=0,
            usage_per_core=[],
            load_average=[0, 0, 0],
            context_switches=0,
            interrupts=0
        )

    def _mock_memory_metrics(self) -> MemoryMetrics:
        return MemoryMetrics(
            timestamp=time.time(),
            total_bytes=0,
            available_bytes=0,
            used_bytes=0,
            free_bytes=0,
            cached_bytes=0,
            buffers_bytes=0,
            swap_total_bytes=0,
            swap_used_bytes=0,
            usage_percent=0
        )

    def _mock_process_metrics(self) -> ProcessMetrics:
        return ProcessMetrics(
            timestamp=time.time(),
            pid=0,
            name="unknown",
            status="unknown",
            cpu_percent=0,
            memory_percent=0,
            memory_rss_bytes=0,
            memory_vms_bytes=0,
            num_threads=0,
            num_fds=0,
            create_time=0
        )


# Global singleton
_system_monitor: Optional[SystemMetricsCollector] = None


def get_system_monitor(history_size: int = 1000,
                        monitoring_interval: float = 15.0) -> SystemMetricsCollector:
    """獲取全局系統監控單例"""
    global _system_monitor
    if _system_monitor is None:
        _system_monitor = SystemMetricsCollector(history_size, monitoring_interval)
    return _system_monitor
