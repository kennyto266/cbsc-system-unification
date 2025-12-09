#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPU性能监控系统
实时监控GPU使用情况，确保GPU真正被利用
提供详细的性能分析和优化建议
"""

import time
import threading
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
import subprocess
import warnings
from collections import deque

try:
    import cupy as cp
    GPU_AVAILABLE = True
except ImportError:
    cp = None
    GPU_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class GPUMetrics:
    """GPU性能指标"""
    timestamp: float
    gpu_utilization: float      # GPU利用率 (%)
    memory_utilization: float   # 内存利用率 (%)
    memory_used_mb: float      # 已用内存 (MB)
    memory_total_mb: float     # 总内存 (MB)
    temperature: float         # 温度 (°C)
    power_usage: float         # 功耗 (W)
    compute_utilization: float # 计算利用率 (%)
    gpu_clock: float          # GPU时钟频率 (MHz)
    memory_clock: float       # 内存时钟频率 (MHz)

@dataclass
class ComputationMetrics:
    """计算性能指标"""
    operation_name: str
    start_time: float
    end_time: float
    data_size: int
    gpu_time_ms: float
    cpu_time_ms: float
    speedup: float
    success: bool
    error_message: Optional[str] = None

class GPUMonitor:
    """GPU性能监控器"""

    def __init__(self, device_id: int = 0, sampling_interval: float = 1.0, max_history: int = 1000):
        self.device_id = device_id
        self.sampling_interval = sampling_interval
        self.max_history = max_history

        # 监控状态
        self.monitoring = False
        self.monitor_thread = None

        # 数据存储
        self.metrics_history = deque(maxlen=max_history)
        self.computation_history = deque(maxlen=max_history)

        # 性能统计
        self.total_operations = 0
        self.successful_operations = 0
        self.gpu_computations = 0
        self.cpu_fallbacks = 0

        # 预警阈值
        self.alert_thresholds = {
            'low_gpu_utilization': 50.0,
            'low_memory_utilization': 30.0,
            'high_temperature': 85.0,
            'high_cpu_fallback_rate': 10.0
        }

        # NVIDIA-SMI检查
        self.nvidia_smi_available = self._check_nvidia_smi()

        logger.info(f"GPU监控器初始化，设备: {device_id}")

    def _check_nvidia_smi(self) -> bool:
        """检查NVIDIA-SMI是否可用"""
        try:
            result = subprocess.run(['nvidia-smi', '--version'],
                                  capture_output=True, text=True, timeout=5)
            available = result.returncode == 0
            logger.info(f"NVIDIA-SMI可用: {available}")
            return available
        except Exception as e:
            logger.warning(f"NVIDIA-SMI检查失败: {e}")
            return False

    def start_monitoring(self):
        """启动实时监控"""
        if self.monitoring:
            logger.warning("监控已在运行")
            return

        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("GPU监控已启动")

    def stop_monitoring(self):
        """停止监控"""
        if not self.monitoring:
            logger.warning("监控未在运行")
            return

        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)

        logger.info("GPU监控已停止")

    def _monitor_loop(self):
        """监控循环"""
        while self.monitoring:
            try:
                # 收集GPU指标
                metrics = self._collect_gpu_metrics()
                if metrics:
                    self.metrics_history.append(metrics)

                # 检查预警
                self._check_performance_alerts(metrics)

                time.sleep(self.sampling_interval)

            except Exception as e:
                logger.error(f"监控循环错误: {e}")
                time.sleep(self.sampling_interval)

    def _collect_gpu_metrics(self) -> Optional[GPUMetrics]:
        """收集GPU性能指标"""
        try:
            if self.nvidia_smi_available:
                return self._collect_nvidia_smi_metrics()
            elif GPU_AVAILABLE:
                return self._collect_cupy_metrics()
            else:
                logger.warning("无法获取GPU指标：NVIDIA-SMI和CuPy都不可用")
                return None

        except Exception as e:
            logger.error(f"GPU指标收集失败: {e}")
            return None

    def _collect_nvidia_smi_metrics(self) -> GPUMetrics:
        """通过NVIDIA-SMI收集指标"""
        try:
            # 构建nvidia-smi查询命令
            query = [
                'nvidia-smi',
                f'--query-gpu=utilization.gpu,utilization.memory,memory.used,memory.total,temperature.gpu,power.draw,clocks.graphics,clocks.memory',
                '--format=csv,noheader,nounits',
                f'--id={self.device_id}'
            ]

            result = subprocess.run(query, capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                raise RuntimeError(f"NVIDIA-SMI查询失败: {result.stderr}")

            # 解析输出
            values = result.stdout.strip().split(', ')
            if len(values) < 8:
                raise ValueError("NVIDIA-SMI输出格式不正确")

            # 创建指标对象
            metrics = GPUMetrics(
                timestamp=time.time(),
                gpu_utilization=float(values[0]),
                memory_utilization=float(values[1]),
                memory_used_mb=float(values[2]),
                memory_total_mb=float(values[3]),
                temperature=float(values[4]),
                power_usage=float(values[5]),
                compute_utilization=float(values[0]),  # 假设计算利用率等于GPU利用率
                gpu_clock=float(values[6]),
                memory_clock=float(values[7])
            )

            return metrics

        except Exception as e:
            logger.error(f"NVIDIA-SMI指标收集失败: {e}")
            # 返回默认值
            return self._get_default_metrics()

    def _collect_cupy_metrics(self) -> GPUMetrics:
        """通过CuPy收集指标"""
        try:
            # CuPy内存信息
            memory_pool = cp.get_default_memory_pool()
            used_bytes = memory_pool.used_bytes()
            total_bytes = memory_pool.total_bytes()

            # 获取设备属性
            device = cp.cuda.Device(self.device_id)
            device_props = device.attributes

            # 创建指标对象（部分信息可能不完整）
            metrics = GPUMetrics(
                timestamp=time.time(),
                gpu_utilization=0.0,  # CuPy无法直接获取
                memory_utilization=(used_bytes / total_bytes * 100) if total_bytes > 0 else 0,
                memory_used_mb=used_bytes / (1024 * 1024),
                memory_total_mb=device_props['TotalGlobalMem'] / (1024 * 1024),
                temperature=0.0,  # CuPy无法获取
                power_usage=0.0,  # CuPy无法获取
                compute_utilization=0.0,  # CuPy无法获取
                gpu_clock=0.0,  # CuPy无法获取
                memory_clock=0.0  # CuPy无法获取
            )

            return metrics

        except Exception as e:
            logger.error(f"CuPy指标收集失败: {e}")
            return self._get_default_metrics()

    def _get_default_metrics(self) -> GPUMetrics:
        """获取默认指标（当无法获取真实指标时）"""
        return GPUMetrics(
            timestamp=time.time(),
            gpu_utilization=0.0,
            memory_utilization=0.0,
            memory_used_mb=0.0,
            memory_total_mb=0.0,
            temperature=0.0,
            power_usage=0.0,
            compute_utilization=0.0,
            gpu_clock=0.0,
            memory_clock=0.0
        )

    def record_computation(self, operation_name: str, start_time: float, end_time: float,
                         data_size: int, gpu_time_ms: float, cpu_time_ms: float,
                         success: bool, error_message: Optional[str] = None):
        """记录计算性能数据"""
        computation = ComputationMetrics(
            operation_name=operation_name,
            start_time=start_time,
            end_time=end_time,
            data_size=data_size,
            gpu_time_ms=gpu_time_ms,
            cpu_time_ms=cpu_time_ms,
            speedup=cpu_time_ms / gpu_time_ms if gpu_time_ms > 0 and success else 0,
            success=success,
            error_message=error_message
        )

        self.computation_history.append(computation)

        # 更新统计
        self.total_operations += 1
        if success:
            self.successful_operations += 1
            if gpu_time_ms > 0:
                self.gpu_computations += 1
        else:
            self.cpu_fallbacks += 1

    def get_current_metrics(self) -> Optional[GPUMetrics]:
        """获取当前性能指标"""
        if self.metrics_history:
            return self.metrics_history[-1]
        return self._collect_gpu_metrics()

    def get_recent_metrics(self, count: int = 10) -> List[GPUMetrics]:
        """获取最近的性能指标"""
        return list(self.metrics_history)[-count:]

    def _check_performance_alerts(self, metrics: Optional[GPUMetrics]):
        """检查性能预警"""
        if not metrics:
            return

        alerts = []

        # GPU利用率过低
        if metrics.gpu_utilization < self.alert_thresholds['low_gpu_utilization']:
            alerts.append({
                'level': 'WARNING',
                'metric': 'gpu_utilization',
                'value': metrics.gpu_utilization,
                'threshold': self.alert_thresholds['low_gpu_utilization'],
                'message': f'GPU利用率过低: {metrics.gpu_utilization:.1f}%'
            })

        # 内存利用率过低
        if metrics.memory_utilization < self.alert_thresholds['low_memory_utilization']:
            alerts.append({
                'level': 'WARNING',
                'metric': 'memory_utilization',
                'value': metrics.memory_utilization,
                'threshold': self.alert_thresholds['low_memory_utilization'],
                'message': f'内存利用率过低: {metrics.memory_utilization:.1f}%'
            })

        # 温度过高
        if metrics.temperature > self.alert_thresholds['high_temperature']:
            alerts.append({
                'level': 'ERROR',
                'metric': 'temperature',
                'value': metrics.temperature,
                'threshold': self.alert_thresholds['high_temperature'],
                'message': f'GPU温度过高: {metrics.temperature:.1f}°C'
            })

        # CPU回退率过高
        if self.total_operations > 10:
            cpu_fallback_rate = (self.cpu_fallbacks / self.total_operations) * 100
            if cpu_fallback_rate > self.alert_thresholds['high_cpu_fallback_rate']:
                alerts.append({
                    'level': 'ERROR',
                    'metric': 'cpu_fallback_rate',
                    'value': cpu_fallback_rate,
                    'threshold': self.alert_thresholds['high_cpu_fallback_rate'],
                    'message': f'CPU回退率过高: {cpu_fallback_rate:.1f}%'
                })

        # 输出预警
        for alert in alerts:
            logger.warning(f"[{alert['level']}] {alert['message']}")

    def generate_performance_report(self) -> Dict[str, Any]:
        """生成综合性能报告"""
        try:
            # 基础统计
            if self.metrics_history:
                recent_metrics = list(self.metrics_history)[-60:]  # 最近60个采样点
                avg_gpu_utilization = sum(m.gpu_utilization for m in recent_metrics) / len(recent_metrics)
                avg_memory_utilization = sum(m.memory_utilization for m in recent_metrics) / len(recent_metrics)
                avg_temperature = sum(m.temperature for m in recent_metrics if m.temperature > 0) / len([m for m in recent_metrics if m.temperature > 0]) if any(m.temperature > 0 for m in recent_metrics) else 0
            else:
                avg_gpu_utilization = avg_memory_utilization = avg_temperature = 0

            # 计算性能统计
            if self.computation_history:
                avg_speedup = sum(c.speedup for c in self.computation_history if c.success and c.speedup > 0) / len([c for c in self.computation_history if c.success and c.speedup > 0])
                successful_operations = len([c for c in self.computation_history if c.success])
                gpu_success_rate = (self.gpu_computations / self.total_operations * 100) if self.total_operations > 0 else 0
            else:
                avg_speedup = successful_operations = gpu_success_rate = 0

            # 生成优化建议
            optimization_suggestions = self._generate_optimization_suggestions()

            # 构建报告
            report = {
                'timestamp': datetime.now().isoformat(),
                'monitoring_duration_minutes': len(self.metrics_history) * self.sampling_interval / 60,
                'device_id': self.device_id,
                'nvidia_smi_available': self.nvidia_smi_available,
                'gpu_available': GPU_AVAILABLE,

                'current_metrics': asdict(self.get_current_metrics()) if self.get_current_metrics() else None,

                'performance_summary': {
                    'avg_gpu_utilization': avg_gpu_utilization,
                    'avg_memory_utilization': avg_memory_utilization,
                    'avg_temperature': avg_temperature,
                    'avg_speedup': avg_speedup,
                    'gpu_success_rate': gpu_success_rate,
                    'total_operations': self.total_operations,
                    'successful_operations': successful_operations,
                    'cpu_fallbacks': self.cpu_fallbacks
                },

                'computation_breakdown': self._get_computation_breakdown(),

                'optimization_suggestions': optimization_suggestions,

                'alert_summary': self._get_alert_summary(),

                'detailed_history': {
                    'recent_metrics': [asdict(m) for m in self.get_recent_metrics(10)],
                    'recent_computations': [asdict(c) for c in list(self.computation_history)[-10:]]
                }
            }

            return report

        except Exception as e:
            logger.error(f"性能报告生成失败: {e}")
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}

    def _generate_optimization_suggestions(self) -> List[str]:
        """生成优化建议"""
        suggestions = []

        if self.metrics_history:
            recent_metrics = list(self.metrics_history)[-30:]
            avg_gpu_util = sum(m.gpu_utilization for m in recent_metrics) / len(recent_metrics)
            avg_mem_util = sum(m.memory_utilization for m in recent_metrics) / len(recent_metrics)

            if avg_gpu_util < 50:
                suggestions.append("GPU利用率过低，建议：检查数据是否真正在GPU上计算，避免CPU回退")
                suggestions.append("考虑增加批处理大小以提高GPU利用率")

            if avg_mem_util < 30:
                suggestions.append("内存利用率过低，建议：增加数据批次大小或并行处理更多任务")

            cpu_fallback_rate = (self.cpu_fallbacks / self.total_operations * 100) if self.total_operations > 0 else 0
            if cpu_fallback_rate > 10:
                suggestions.append(f"CPU回退率过高({cpu_fallback_rate:.1f}%)，建议：检查GPU数据格式兼容性")

        if self.computation_history:
            avg_speedup = sum(c.speedup for c in self.computation_history if c.success and c.speedup > 0) / len([c for c in self.computation_history if c.success and c.speedup > 0])
            if avg_speedup < 2:
                suggestions.append("GPU加速效果不明显，建议：优化GPU内核实现或检查数据传输开销")

        if not suggestions:
            suggestions.append("GPU性能表现良好，无需特别优化")

        return suggestions

    def _get_computation_breakdown(self) -> Dict[str, Any]:
        """获取计算性能分解"""
        if not self.computation_history:
            return {}

        # 按操作类型分组
        operation_stats = {}
        for comp in self.computation_history:
            if comp.operation_name not in operation_stats:
                operation_stats[comp.operation_name] = {
                    'count': 0,
                    'success_count': 0,
                    'avg_speedup': 0,
                    'avg_data_size': 0,
                    'total_gpu_time': 0,
                    'total_cpu_time': 0
                }

            stats = operation_stats[comp.operation_name]
            stats['count'] += 1
            if comp.success:
                stats['success_count'] += 1
                if comp.speedup > 0:
                    stats['total_gpu_time'] += comp.gpu_time_ms
                    stats['total_cpu_time'] += comp.cpu_time_ms

        # 计算平均值
        for op_name, stats in operation_stats.items():
            if stats['count'] > 0:
                success_computations = [c for c in self.computation_history if c.operation_name == op_name and c.success and c.speedup > 0]
                if success_computations:
                    stats['avg_speedup'] = sum(c.speedup for c in success_computations) / len(success_computations)
                    stats['avg_data_size'] = sum(c.data_size for c in success_computations) / len(success_computations)
                stats['success_rate'] = stats['success_count'] / stats['count'] * 100

        return operation_stats

    def _get_alert_summary(self) -> Dict[str, int]:
        """获取预警摘要"""
        return {
            'total_operations': self.total_operations,
            'cpu_fallbacks': self.cpu_fallbacks,
            'gpu_computations': self.gpu_computations,
            'successful_operations': self.successful_operations
        }

    def save_report(self, filename: str = None) -> str:
        """保存性能报告到文件"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"gpu_performance_report_{timestamp}.json"

        try:
            report = self.generate_performance_report()
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)

            logger.info(f"性能报告已保存到: {filename}")
            return filename

        except Exception as e:
            logger.error(f"保存性能报告失败: {e}")
            raise

    def reset_statistics(self):
        """重置统计信息"""
        self.metrics_history.clear()
        self.computation_history.clear()
        self.total_operations = 0
        self.successful_operations = 0
        self.gpu_computations = 0
        self.cpu_fallbacks = 0
        logger.info("统计信息已重置")

    def set_alert_thresholds(self, **thresholds):
        """设置预警阈值"""
        self.alert_thresholds.update(thresholds)
        logger.info(f"预警阈值已更新: {thresholds}")


def get_gpu_monitor(device_id: int = 0, sampling_interval: float = 1.0) -> GPUMonitor:
    """获取GPU监控器实例"""
    return GPUMonitor(device_id, sampling_interval)


# 上下文管理器用于临时监控
class TemporaryGPUMonitor:
    """临时GPU监控上下文管理器"""

    def __init__(self, device_id: int = 0, sampling_interval: float = 0.5):
        self.monitor = get_gpu_monitor(device_id, sampling_interval)
        self.operation_start_time = None
        self.operation_name = None

    def __enter__(self):
        self.monitor.start_monitoring()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.monitor.stop_monitoring()
        return False

    def start_operation(self, operation_name: str):
        """开始监控操作"""
        self.operation_name = operation_name
        self.operation_start_time = time.time()

    def end_operation(self, data_size: int = 0, cpu_time_ms: float = 0, success: bool = True, error_message: str = None):
        """结束监控操作"""
        if self.operation_start_time and self.operation_name:
            end_time = time.time()
            gpu_time_ms = (end_time - self.operation_start_time) * 1000
            self.monitor.record_computation(
                self.operation_name,
                self.operation_start_time,
                end_time,
                data_size,
                gpu_time_ms,
                cpu_time_ms,
                success,
                error_message
            )


# 测试代码
if __name__ == "__main__":
    # 测试GPU监控器
    try:
        with TemporaryGPUMonitor() as monitor:
            print("开始GPU监控测试...")

            # 模拟一些计算
            monitor.start_operation("test_rsi")
            time.sleep(2)  # 模拟计算时间
            monitor.end_operation(data_size=10000, cpu_time_ms=5000, success=True)

            monitor.start_operation("test_macd")
            time.sleep(1)
            monitor.end_operation(data_size=5000, cpu_time_ms=3000, success=True)

            time.sleep(2)  # 等待一些指标收集

            # 生成报告
            report = monitor.monitor.generate_performance_report()
            print("性能报告:")
            print(json.dumps(report, indent=2, ensure_ascii=False))

            # 保存报告
            filename = monitor.monitor.save_report()
            print(f"报告已保存到: {filename}")

    except Exception as e:
        print(f"GPU监控测试失败: {e}")