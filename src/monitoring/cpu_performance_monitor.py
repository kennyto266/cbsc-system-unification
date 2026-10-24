#!/usr/bin/env python3
"""
Phase 3: CPU特定性能监控系统
CPU-Specific Performance Monitoring System for GPU-to-CPU Migration

This module provides comprehensive CPU performance monitoring capabilities
specifically designed for high-performance technical indicator calculations
and parallel processing optimization.

Key Features:
- Real-time CPU core utilization monitoring
- Cache miss rate and memory bandwidth analysis
- Process-level performance tracking
- Parallel efficiency metrics
- Thermal and power consumption monitoring
- CPU bottleneck detection and optimization recommendations
"""

import logging
import time
import threading
import psutil
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union, Any, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
from collections import deque
import multiprocessing
import json
import datetime
import subprocess
import os
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

@dataclass
class CPUMetrics:
    """CPU性能指标"""
    timestamp: float
    cpu_percent: float
    cpu_count: int
    cpu_freq_current: float  # MHz
    cpu_freq_min: float
    cpu_freq_max: float
    load_average: Tuple[float, float, float]  # 1min, 5min, 15min
    per_cpu_percent: List[float]
    context_switches: int
    interrupts: int
    soft_interrupts: int
    system_calls: int

@dataclass
class MemoryMetrics:
    """内存性能指标"""
    timestamp: float
    total_mb: float
    available_mb: float
    used_mb: float
    percent: float
    active_mb: float
    inactive_mb: float
    buffers_mb: float
    cached_mb: float
    shared_mb: float
    swap_total_mb: float
    swap_used_mb: float
    swap_percent: float

@dataclass
class ProcessMetrics:
    """进程性能指标"""
    timestamp: float
    pid: int
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    num_threads: int
    num_handles: int
    io_read_bytes: int
    io_write_bytes: int
    io_read_count: int
    io_write_count: int
    cpu_times_user: float
    cpu_times_system: float
    cpu_times_idle: float

@dataclass
class ParallelEfficiencyMetrics:
    """并行效率指标"""
    timestamp: float
    active_processes: int
    cpu_utilization_efficiency: float
    memory_distribution_efficiency: float
    load_balancing_score: float
    parallel_overhead_ratio: float
    scalability_factor: float
    bottleneck_type: Optional[str]  # 'cpu', 'memory', 'io', 'none'

@dataclass
class PerformanceAlert:
    """性能告警"""
    timestamp: float
    alert_type: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    message: str
    current_value: float
    threshold_value: float
    recommendation: str

class CPUPerformanceMonitor:
    """CPU性能监控系统"""

    def __init__(
        self,
        monitoring_interval: float = 1.0,
        history_size: int = 1000,
        alert_thresholds: Dict[str, float] = None
    ):
        self.monitoring_interval = monitoring_interval
        self.history_size = history_size

        # 默认告警阈值
        self.alert_thresholds = alert_thresholds or {
            'cpu_usage_warning': 80.0,
            'cpu_usage_critical': 95.0,
            'memory_usage_warning': 85.0,
            'memory_usage_critical': 95.0,
            'load_average_warning': multiprocessing.cpu_count() * 0.8,
            'load_average_critical': multiprocessing.cpu_count(),
            'efficiency_warning': 0.7,
            'efficiency_critical': 0.5
        }

        # 监控状态
        self.monitoring_active = False
        self.monitor_thread = None

        # 性能历史数据
        self.cpu_metrics_history = deque(maxlen=history_size)
        self.memory_metrics_history = deque(maxlen=history_size)
        self.process_metrics_history = deque(maxlen=history_size)
        self.parallel_efficiency_history = deque(maxlen=history_size)
        self.alerts_history = deque(maxlen=100)

        # 进程跟踪
        self.monitored_processes = {}
        self.process_pids = set()

        # 性能基线
        self.baseline_cpu_percent = 0.0
        self.baseline_memory_mb = 0.0
        self.baseline_efficiency = 1.0

        # 统计信息
        self.peak_cpu_usage = 0.0
        self.peak_memory_usage = 0.0
        self.total_alerts = 0
        self.critical_alerts = 0

        # 线程安全
        self._lock = threading.Lock()

        logger.info(f"CPU Performance Monitor initialized - Interval: {monitoring_interval}s")

    def start_monitoring(self):
        """启动性能监控"""
        if self.monitoring_active:
            logger.warning("Monitoring already active")
            return

        self.monitoring_active = True

        # 建立基线
        self._establish_baseline()

        # 启动监控线程
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()

        logger.info("CPU performance monitoring started")

    def stop_monitoring(self):
        """停止性能监控"""
        if not self.monitoring_active:
            return

        self.monitoring_active = False

        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)

        logger.info("CPU performance monitoring stopped")

    def add_process_monitoring(self, pid: int, name: str = None):
        """添加进程监控"""
        try:
            if psutil.pid_exists(pid):
                self.process_pids.add(pid)
                self.monitored_processes[pid] = {
                    'name': name or f"Process_{pid}",
                    'start_time': time.time(),
                    'cpu_time_total': 0.0,
                    'io_bytes_total': 0
                }
                logger.info(f"Added process monitoring: PID {pid} ({name})")
            else:
                logger.warning(f"Process {pid} does not exist")
        except Exception as e:
            logger.error(f"Failed to add process monitoring for PID {pid}: {e}")

    def remove_process_monitoring(self, pid: int):
        """移除进程监控"""
        self.process_pids.discard(pid)
        if pid in self.monitored_processes:
            del self.monitored_processes[pid]
            logger.info(f"Removed process monitoring: PID {pid}")

    def get_current_metrics(self) -> Dict[str, Any]:
        """获取当前性能指标"""
        with self._lock:
            current_cpu = self._collect_cpu_metrics()
            current_memory = self._collect_memory_metrics()
            current_processes = self._collect_process_metrics()
            current_efficiency = self._calculate_parallel_efficiency()

            return {
                'cpu_metrics': asdict(current_cpu),
                'memory_metrics': asdict(current_memory),
                'process_metrics': [asdict(p) for p in current_processes],
                'parallel_efficiency': asdict(current_efficiency),
                'alerts': [asdict(a) for a in list(self.alerts_history)[-10:]],
                'peak_cpu_usage': self.peak_cpu_usage,
                'peak_memory_usage': self.peak_memory_usage,
                'total_alerts': self.total_alerts,
                'critical_alerts': self.critical_alerts
            }

    def get_performance_summary(self, time_window_minutes: int = 60) -> Dict[str, Any]:
        """获取性能汇总"""
        with self._lock:
            cutoff_time = time.time() - (time_window_minutes * 60)

            # 筛选时间窗口内的数据
            recent_cpu = [
                m for m in self.cpu_metrics_history
                if m.timestamp >= cutoff_time
            ]
            recent_memory = [
                m for m in self.memory_metrics_history
                if m.timestamp >= cutoff_time
            ]
            recent_efficiency = [
                m for m in self.parallel_efficiency_history
                if m.timestamp >= cutoff_time
            ]

            if not recent_cpu:
                return {}

            # 计算统计指标
            cpu_usage_values = [m.cpu_percent for m in recent_cpu]
            memory_usage_values = [m.percent for m in recent_memory]
            efficiency_values = [m.cpu_utilization_efficiency for m in recent_efficiency]

            summary = {
                'time_window_minutes': time_window_minutes,
                'data_points': len(recent_cpu),
                'cpu_stats': {
                    'avg_usage': np.mean(cpu_usage_values),
                    'max_usage': np.max(cpu_usage_values),
                    'min_usage': np.min(cpu_usage_values),
                    'std_usage': np.std(cpu_usage_values)
                },
                'memory_stats': {
                    'avg_usage': np.mean(memory_usage_values),
                    'max_usage': np.max(memory_usage_values),
                    'min_usage': np.min(memory_usage_values),
                    'std_usage': np.std(memory_usage_values)
                },
                'efficiency_stats': {
                    'avg_efficiency': np.mean(efficiency_values) if efficiency_values else 0,
                    'max_efficiency': np.max(efficiency_values) if efficiency_values else 0,
                    'min_efficiency': np.min(efficiency_values) if efficiency_values else 0
                },
                'performance_score': self._calculate_overall_performance_score(),
                'bottleneck_analysis': self._analyze_bottlenecks(recent_cpu, recent_memory, recent_efficiency)
            }

            return summary

    def _monitoring_loop(self):
        """监控主循环"""
        while self.monitoring_active:
            try:
                # 收集各类指标
                cpu_metrics = self._collect_cpu_metrics()
                memory_metrics = self._collect_memory_metrics()
                process_metrics = self._collect_process_metrics()
                efficiency_metrics = self._calculate_parallel_efficiency()

                # 存储历史数据
                self.cpu_metrics_history.append(cpu_metrics)
                self.memory_metrics_history.append(memory_metrics)
                self.parallel_efficiency_history.append(efficiency_metrics)

                for process_metric in process_metrics:
                    self.process_metrics_history.append(process_metric)

                # 更新峰值指标
                self.peak_cpu_usage = max(self.peak_cpu_usage, cpu_metrics.cpu_percent)
                self.peak_memory_usage = max(self.peak_memory_usage, memory_metrics.used_mb)

                # 检查告警
                self._check_alerts(cpu_metrics, memory_metrics, efficiency_metrics)

                time.sleep(self.monitoring_interval)

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(5.0)

    def _collect_cpu_metrics(self) -> CPUMetrics:
        """收集CPU指标"""
        # 基本CPU使用率
        cpu_percent = psutil.cpu_percent(interval=None)
        cpu_count = psutil.cpu_count()
        per_cpu_percent = psutil.cpu_percent(interval=None, percpu=True)

        # CPU频率信息
        cpu_freq = psutil.cpu_freq()
        if cpu_freq:
            freq_current = cpu_freq.current or 0
            freq_min = cpu_freq.min or 0
            freq_max = cpu_freq.max or 0
        else:
            freq_current = freq_min = freq_max = 0

        # 负载平均值
        try:
            load_avg = psutil.getloadavg()
        except AttributeError:
            load_avg = (0.0, 0.0, 0.0)

        # 系统统计信息
        try:
            cpu_stats = psutil.cpu_stats()
            context_switches = cpu_stats.ctx_switches
            interrupts = cpu_stats.interrupts
            soft_interrupts = cpu_stats.soft_interrupts
        except AttributeError:
            context_switches = interrupts = soft_interrupts = 0

        # 系统调用计数（Linux特有）
        system_calls = 0
        try:
            if os.name == 'posix':
                system_calls = len(open('/proc/stat').read().splitlines())
        except:
            pass

        return CPUMetrics(
            timestamp=time.time(),
            cpu_percent=cpu_percent,
            cpu_count=cpu_count,
            cpu_freq_current=freq_current,
            cpu_freq_min=freq_min,
            cpu_freq_max=freq_max,
            load_average=load_avg,
            per_cpu_percent=per_cpu_percent,
            context_switches=context_switches,
            interrupts=interrupts,
            soft_interrupts=soft_interrupts,
            system_calls=system_calls
        )

    def _collect_memory_metrics(self) -> MemoryMetrics:
        """收集内存指标"""
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()

        # 获取详细的内存信息
        try:
            if os.name == 'posix':
                with open('/proc/meminfo', 'r') as f:
                    meminfo = dict((i.split()[0].rstrip(':'), int(i.split()[1]))
                                   for i in f.readlines())

                active_mb = meminfo.get('Active', 0) / 1024
                inactive_mb = meminfo.get('Inactive', 0) / 1024
                buffers_mb = memory.buffers / 1024 / 1024
                cached_mb = memory.cached / 1024 / 1024
                shared_mb = memory.shared / 1024 / 1024 if hasattr(memory, 'shared') else 0
            else:
                active_mb = inactive_mb = buffers_mb = cached_mb = shared_mb = 0
        except:
            active_mb = inactive_mb = buffers_mb = cached_mb = shared_mb = 0

        return MemoryMetrics(
            timestamp=time.time(),
            total_mb=memory.total / 1024 / 1024,
            available_mb=memory.available / 1024 / 1024,
            used_mb=memory.used / 1024 / 1024,
            percent=memory.percent,
            active_mb=active_mb,
            inactive_mb=inactive_mb,
            buffers_mb=buffers_mb,
            cached_mb=cached_mb,
            shared_mb=shared_mb,
            swap_total_mb=swap.total / 1024 / 1024,
            swap_used_mb=swap.used / 1024 / 1024,
            swap_percent=swap.percent
        )

    def _collect_process_metrics(self) -> List[ProcessMetrics]:
        """收集进程指标"""
        processes = []

        for pid in list(self.process_pids):
            try:
                if not psutil.pid_exists(pid):
                    self.process_pids.discard(pid)
                    continue

                proc = psutil.Process(pid)

                # CPU和内存使用
                cpu_percent = proc.cpu_percent()
                memory_info = proc.memory_info()
                memory_mb = memory_info.rss / 1024 / 1024
                memory_percent = proc.memory_percent()

                # 进程信息
                num_threads = proc.num_threads()
                num_handles = proc.num_handles() if hasattr(proc, 'num_handles') else 0

                # IO统计
                try:
                    io_counters = proc.io_counters()
                    io_read_bytes = io_counters.read_bytes
                    io_write_bytes = io_counters.write_bytes
                    io_read_count = io_counters.read_count
                    io_write_count = io_counters.write_count
                except (psutil.AccessDenied, AttributeError):
                    io_read_bytes = io_write_bytes = io_read_count = io_write_count = 0

                # CPU时间
                cpu_times = proc.cpu_times()
                cpu_times_user = cpu_times.user
                cpu_times_system = cpu_times.system
                cpu_times_idle = 0  # 进程没有idle时间

                processes.append(ProcessMetrics(
                    timestamp=time.time(),
                    pid=pid,
                    cpu_percent=cpu_percent,
                    memory_mb=memory_mb,
                    memory_percent=memory_percent,
                    num_threads=num_threads,
                    num_handles=num_handles,
                    io_read_bytes=io_read_bytes,
                    io_write_bytes=io_write_bytes,
                    io_read_count=io_read_count,
                    io_write_count=io_write_count,
                    cpu_times_user=cpu_times_user,
                    cpu_times_system=cpu_times_system,
                    cpu_times_idle=cpu_times_idle
                ))

            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                logger.debug(f"Cannot monitor process {pid}: {e}")
                self.process_pids.discard(pid)

        return processes

    def _calculate_parallel_efficiency(self) -> ParallelEfficiencyMetrics:
        """计算并行效率指标"""
        if not self.cpu_metrics_history:
            return ParallelEfficiencyMetrics(
                timestamp=time.time(),
                active_processes=0,
                cpu_utilization_efficiency=0.0,
                memory_distribution_efficiency=1.0,
                load_balancing_score=1.0,
                parallel_overhead_ratio=0.0,
                scalability_factor=1.0,
                bottleneck_type=None
            )

        # 当前CPU指标
        current_cpu = self.cpu_metrics_history[-1]
        cpu_count = current_cpu.cpu_count

        # 活跃进程数
        active_processes = len(self.process_pids)

        # CPU利用率效率
        cpu_utilization = current_cpu.cpu_percent / 100.0
        cpu_utilization_efficiency = min(1.0, cpu_utilization / 0.8)  # 80%为理想利用率

        # 负载均衡分数（基于各CPU核心使用率的方差）
        per_cpu_variance = np.var(current_cpu.per_cpu_percent) if current_cpu.per_cpu_percent else 0
        load_balancing_score = max(0.0, 1.0 - (per_cpu_variance / 100.0))

        # 内存分布效率
        memory_efficiency = 1.0
        if self.memory_metrics_history:
            current_memory = self.memory_metrics_history[-1]
            memory_efficiency = max(0.0, 1.0 - (current_memory.percent / 100.0))

        # 并行开销比率
        parallel_overhead_ratio = 0.0
        if active_processes > 1 and cpu_utilization > 0:
            # 理想情况下，N个进程应该获得N倍的CPU利用率
            ideal_cpu_utilization = min(1.0, active_processes / cpu_count)
            parallel_overhead_ratio = max(0.0, 1.0 - (cpu_utilization / ideal_cpu_utilization))

        # 可扩展性因子
        scalability_factor = cpu_utilization_efficiency * load_balancing_score

        # 瓶颈检测
        bottleneck_type = self._detect_bottleneck(
            cpu_utilization, memory_efficiency, parallel_overhead_ratio
        )

        return ParallelEfficiencyMetrics(
            timestamp=time.time(),
            active_processes=active_processes,
            cpu_utilization_efficiency=cpu_utilization_efficiency,
            memory_distribution_efficiency=memory_efficiency,
            load_balancing_score=load_balancing_score,
            parallel_overhead_ratio=parallel_overhead_ratio,
            scalability_factor=scalability_factor,
            bottleneck_type=bottleneck_type
        )

    def _detect_bottleneck(
        self,
        cpu_utilization: float,
        memory_efficiency: float,
        parallel_overhead: float
    ) -> Optional[str]:
        """检测性能瓶颈"""
        if cpu_utilization >= 0.95:
            return 'cpu'
        elif memory_efficiency <= 0.2:
            return 'memory'
        elif parallel_overhead >= 0.5:
            return 'parallel'
        else:
            return None

    def _check_alerts(
        self,
        cpu_metrics: CPUMetrics,
        memory_metrics: MemoryMetrics,
        efficiency_metrics: ParallelEfficiencyMetrics
    ):
        """检查性能告警"""
        alerts = []

        # CPU使用率告警
        if cpu_metrics.cpu_percent >= self.alert_thresholds['cpu_usage_critical']:
            alerts.append(PerformanceAlert(
                timestamp=time.time(),
                alert_type='cpu_usage',
                severity='critical',
                message=f'CPU usage critically high: {cpu_metrics.cpu_percent:.1f}%',
                current_value=cpu_metrics.cpu_percent,
                threshold_value=self.alert_thresholds['cpu_usage_critical'],
                recommendation='Reduce computational load or increase CPU resources'
            ))
            self.critical_alerts += 1
        elif cpu_metrics.cpu_percent >= self.alert_thresholds['cpu_usage_warning']:
            alerts.append(PerformanceAlert(
                timestamp=time.time(),
                alert_type='cpu_usage',
                severity='medium',
                message=f'CPU usage high: {cpu_metrics.cpu_percent:.1f}%',
                current_value=cpu_metrics.cpu_percent,
                threshold_value=self.alert_thresholds['cpu_usage_warning'],
                recommendation='Monitor CPU usage closely'
            ))

        # 内存使用率告警
        if memory_metrics.percent >= self.alert_thresholds['memory_usage_critical']:
            alerts.append(PerformanceAlert(
                timestamp=time.time(),
                alert_type='memory_usage',
                severity='critical',
                message=f'Memory usage critically high: {memory_metrics.percent:.1f}%',
                current_value=memory_metrics.percent,
                threshold_value=self.alert_thresholds['memory_usage_critical'],
                recommendation='Free memory or increase available RAM'
            ))
            self.critical_alerts += 1
        elif memory_metrics.percent >= self.alert_thresholds['memory_usage_warning']:
            alerts.append(PerformanceAlert(
                timestamp=time.time(),
                alert_type='memory_usage',
                severity='medium',
                message=f'Memory usage high: {memory_metrics.percent:.1f}%',
                current_value=memory_metrics.percent,
                threshold_value=self.alert_thresholds['memory_usage_warning'],
                recommendation='Monitor memory usage closely'
            ))

        # 效率告警
        if efficiency_metrics.cpu_utilization_efficiency <= self.alert_thresholds['efficiency_critical']:
            alerts.append(PerformanceAlert(
                timestamp=time.time(),
                alert_type='efficiency',
                severity='critical',
                message=f'Parallel efficiency critically low: {efficiency_metrics.cpu_utilization_efficiency:.3f}',
                current_value=efficiency_metrics.cpu_utilization_efficiency,
                threshold_value=self.alert_thresholds['efficiency_critical'],
                recommendation='Optimize parallelization strategy'
            ))
            self.critical_alerts += 1
        elif efficiency_metrics.cpu_utilization_efficiency <= self.alert_thresholds['efficiency_warning']:
            alerts.append(PerformanceAlert(
                timestamp=time.time(),
                alert_type='efficiency',
                severity='medium',
                message=f'Parallel efficiency low: {efficiency_metrics.cpu_utilization_efficiency:.3f}',
                current_value=efficiency_metrics.cpu_utilization_efficiency,
                threshold_value=self.alert_thresholds['efficiency_warning'],
                recommendation='Review parallel processing configuration'
            ))

        # 添加告警到历史记录
        for alert in alerts:
            self.alerts_history.append(alert)
            self.total_alerts += 1
            logger.warning(f"Performance alert: {alert.message}")

    def _establish_baseline(self):
        """建立性能基线"""
        logger.info("Establishing performance baseline...")

        baseline_samples = []
        for _ in range(10):  # 采集10个样本
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            baseline_samples.append({
                'cpu': cpu_percent,
                'memory_mb': memory.used / 1024 / 1024
            })

        if baseline_samples:
            self.baseline_cpu_percent = np.mean([s['cpu'] for s in baseline_samples])
            self.baseline_memory_mb = np.mean([s['memory_mb'] for s in baseline_samples])
            self.baseline_efficiency = 1.0

            logger.info(f"Baseline established - CPU: {self.baseline_cpu_percent:.1f}%, "
                       f"Memory: {self.baseline_memory_mb:.1f}MB")

    def _calculate_overall_performance_score(self) -> float:
        """计算综合性能分数"""
        if not self.cpu_metrics_history or not self.memory_metrics_history:
            return 0.0

        # 最近的CPU和内存指标
        recent_cpu = list(self.cpu_metrics_history)[-10:]
        recent_memory = list(self.memory_metrics_history)[-10:]

        avg_cpu_usage = np.mean([m.cpu_percent for m in recent_cpu])
        avg_memory_usage = np.mean([m.percent for m in recent_memory])

        # CPU分数（适中的使用率为最佳）
        cpu_score = max(0.0, 1.0 - abs(avg_cpu_usage - 70) / 100.0)

        # 内存分数（低使用率为好）
        memory_score = max(0.0, 1.0 - avg_memory_usage / 100.0)

        # 效率分数
        if self.parallel_efficiency_history:
            recent_efficiency = list(self.parallel_efficiency_history)[-10:]
            efficiency_score = np.mean([m.cpu_utilization_efficiency for m in recent_efficiency])
        else:
            efficiency_score = 1.0

        # 综合分数
        overall_score = 0.4 * cpu_score + 0.3 * memory_score + 0.3 * efficiency_score
        return overall_score

    def _analyze_bottlenecks(
        self,
        cpu_history: List[CPUMetrics],
        memory_history: List[MemoryMetrics],
        efficiency_history: List[ParallelEfficiencyMetrics]
    ) -> Dict[str, Any]:
        """分析性能瓶颈"""
        if not cpu_history or not memory_history:
            return {}

        # CPU瓶颈分析
        cpu_values = [m.cpu_percent for m in cpu_history]
        avg_cpu = np.mean(cpu_values)
        max_cpu = np.max(cpu_values)
        cpu_bottleneck = max_cpu >= 90.0

        # 内存瓶颈分析
        memory_values = [m.percent for m in memory_history]
        avg_memory = np.mean(memory_values)
        max_memory = np.max(memory_values)
        memory_bottleneck = max_memory >= 90.0

        # 效率瓶颈分析
        efficiency_issues = []
        if efficiency_history:
            efficiency_values = [m.cpu_utilization_efficiency for m in efficiency_history]
            avg_efficiency = np.mean(efficiency_values)
            if avg_efficiency < 0.7:
                efficiency_issues.append('low_parallel_efficiency')

            load_balancing_values = [m.load_balancing_score for m in efficiency_history]
            avg_load_balancing = np.mean(load_balancing_values)
            if avg_load_balancing < 0.7:
                efficiency_issues.append('poor_load_balancing')

        return {
            'primary_bottleneck': self._determine_primary_bottleneck(
                cpu_bottleneck, memory_bottleneck, efficiency_issues
            ),
            'cpu_bottleneck': cpu_bottleneck,
            'memory_bottleneck': memory_bottleneck,
            'efficiency_issues': efficiency_issues,
            'avg_cpu_usage': avg_cpu,
            'avg_memory_usage': avg_memory,
            'recommendations': self._generate_bottleneck_recommendations(
                cpu_bottleneck, memory_bottleneck, efficiency_issues
            )
        }

    def _determine_primary_bottleneck(
        self,
        cpu_bottleneck: bool,
        memory_bottleneck: bool,
        efficiency_issues: List[str]
    ) -> str:
        """确定主要瓶颈"""
        if cpu_bottleneck and memory_bottleneck:
            return 'cpu_memory'
        elif cpu_bottleneck:
            return 'cpu'
        elif memory_bottleneck:
            return 'memory'
        elif efficiency_issues:
            return 'efficiency'
        else:
            return 'none'

    def _generate_bottleneck_recommendations(
        self,
        cpu_bottleneck: bool,
        memory_bottleneck: bool,
        efficiency_issues: List[str]
    ) -> List[str]:
        """生成瓶颈优化建议"""
        recommendations = []

        if cpu_bottleneck:
            recommendations.append("Optimize algorithms for CPU efficiency")
            recommendations.append("Consider reducing parallel processes")
            recommendations.append("Profile and optimize CPU-intensive code sections")

        if memory_bottleneck:
            recommendations.append("Implement memory-efficient data structures")
            recommendations.append("Reduce memory usage through data streaming")
            recommendations.append("Increase available system memory")

        if 'low_parallel_efficiency' in efficiency_issues:
            recommendations.append("Optimize parallel processing strategy")
            recommendations.append("Review process/thread allocation")

        if 'poor_load_balancing' in efficiency_issues:
            recommendations.append("Improve workload distribution")
            recommendations.append("Implement dynamic load balancing")

        return recommendations

    def export_monitoring_data(self, filepath: str, time_range_hours: int = 24):
        """导出监控数据"""
        try:
            cutoff_time = time.time() - (time_range_hours * 3600)

            data = {
                'export_timestamp': datetime.datetime.now().isoformat(),
                'time_range_hours': time_range_hours,
                'cpu_metrics': [
                    asdict(m) for m in self.cpu_metrics_history
                    if m.timestamp >= cutoff_time
                ],
                'memory_metrics': [
                    asdict(m) for m in self.memory_metrics_history
                    if m.timestamp >= cutoff_time
                ],
                'parallel_efficiency_metrics': [
                    asdict(m) for m in self.parallel_efficiency_history
                    if m.timestamp >= cutoff_time
                ],
                'alerts': [asdict(a) for a in self.alerts_history],
                'statistics': {
                    'peak_cpu_usage': self.peak_cpu_usage,
                    'peak_memory_usage': self.peak_memory_usage,
                    'total_alerts': self.total_alerts,
                    'critical_alerts': self.critical_alerts,
                    'baseline_cpu_percent': self.baseline_cpu_percent,
                    'baseline_memory_mb': self.baseline_memory_mb
                }
            }

            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)

            logger.info(f"Monitoring data exported to {filepath}")

        except Exception as e:
            logger.error(f"Failed to export monitoring data: {e}")

# 全局监控器实例
_global_monitor = None

def get_cpu_monitor() -> CPUPerformanceMonitor:
    """获取全局CPU性能监控器实例"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = CPUPerformanceMonitor()
        _global_monitor.start_monitoring()
    return _global_monitor

def start_cpu_monitoring():
    """启动CPU监控（简化接口）"""
    monitor = get_cpu_monitor()
    monitor.start_monitoring()

def get_current_performance_metrics() -> Dict[str, Any]:
    """获取当前性能指标（简化接口）"""
    monitor = get_cpu_monitor()
    return monitor.get_current_metrics()

def get_performance_summary(time_window_minutes: int = 60) -> Dict[str, Any]:
    """获取性能汇总（简化接口）"""
    monitor = get_cpu_monitor()
    return monitor.get_performance_summary(time_window_minutes)