#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Performance Monitor Module
性能監控模組 - 基於OpenSpec enhance-nonprice-ta-system提案

提供實時性能監控、統計分析、瓶頸識別等功能
"""

import time
import threading
import psutil
import numpy as np
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json

@dataclass
class PerformanceMetrics:
    """性能指標數據類"""
    timestamp: float = field(default_factory=time.time)
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    memory_percent: float = 0.0
    execution_time: float = 0.0
    strategies_per_second: float = 0.0
    cache_hit_rate: float = 0.0

@dataclass
class OptimizationMetrics:
    """優化過程指標"""
    total_strategies: int = 0
    completed_strategies: int = 0
    successful_strategies: int = 0
    failed_strategies: int = 0
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    parallel_workers: int = 32

class PerformanceMonitor:
    """
    性能監控器
    提供實時系統性能監控和優化建議
    """

    def __init__(self, monitoring_interval: float = 1.0):
        self.monitoring_interval = monitoring_interval
        self.is_monitoring = False
        self.monitoring_thread = None

        # 性能數據存儲
        self.performance_history: List[PerformanceMetrics] = []
        self.optimization_metrics: Optional[OptimizationMetrics] = None

        # API調用統計
        self.api_call_stats: Dict[str, List[float]] = {}

        # 瓶頸檢測閾值
        self.cpu_threshold = 80.0  # CPU使用率閾值
        self.memory_threshold = 80.0  # 內存使用率閾值
        self.performance_threshold = 300.0  # 策略/秒性能閾值

    def start_monitoring(self):
        """開始性能監控"""
        if self.is_monitoring:
            return

        self.is_monitoring = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()

    def stop_monitoring(self):
        """停止性能監控"""
        self.is_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join()

    def _monitoring_loop(self):
        """監控循環"""
        while self.is_monitoring:
            try:
                metrics = self._collect_system_metrics()
                self.performance_history.append(metrics)

                # 保持歷史數據在合理範圍內
                if len(self.performance_history) > 1000:
                    self.performance_history = self.performance_history[-500:]

                time.sleep(self.monitoring_interval)

            except Exception as e:
                print(f"[PERFORMANCE_MONITOR] 監控錯誤: {e}")

    def _collect_system_metrics(self) -> PerformanceMetrics:
        """收集系統性能指標"""
        try:
            # CPU和內存使用率
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()

            process = psutil.Process()
            process_memory = process.memory_info().rss / 1024 / 1024  # MB

            return PerformanceMetrics(
                cpu_usage=cpu_percent,
                memory_usage=process_memory,
                memory_percent=memory.percent
            )

        except Exception as e:
            print(f"[PERFORMANCE_MONITOR] 系統指標收集失敗: {e}")
            return PerformanceMetrics()

    def start_optimization(self, total_strategies: int):
        """開始優化監控"""
        self.optimization_metrics = OptimizationMetrics(
            total_strategies=total_strategies,
            start_time=time.time()
        )
        self.start_monitoring()

    def end_optimization(self, execution_time: float, successful_count: int):
        """結束優化監控"""
        if self.optimization_metrics:
            self.optimization_metrics.end_time = time.time()
            self.optimization_metrics.completed_strategies = self.optimization_metrics.total_strategies
            self.optimization_metrics.successful_strategies = successful_count
            self.optimization_metrics.failed_strategies = (
                self.optimization_metrics.total_strategies - successful_count
            )

            # 計算性能指標
            if execution_time > 0:
                self.optimization_metrics.execution_time = execution_time
                self.optimization_metrics.strategies_per_second = (
                    self.optimization_metrics.total_strategies / execution_time
                )

        self.stop_monitoring()

    def record_api_call(self, api_name: str, execution_time: float, success: bool):
        """記錄API調用性能"""
        if api_name not in self.api_call_stats:
            self.api_call_stats[api_name] = []

        self.api_call_stats[api_name].append(execution_time)

        # 保持統計數據在合理範圍內
        if len(self.api_call_stats[api_name]) > 100:
            self.api_call_stats[api_name] = self.api_call_stats[api_name][-50:]

    def get_performance_summary(self) -> Dict[str, Any]:
        """獲取性能總結"""
        summary = {}

        # 優化過程統計
        if self.optimization_metrics:
            opt = self.optimization_metrics
            summary['optimization'] = {
                'total_strategies': opt.total_strategies,
                'successful_strategies': opt.successful_strategies,
                'failed_strategies': opt.failed_strategies,
                'success_rate': (opt.successful_strategies / opt.total_strategies * 100) if opt.total_strategies > 0 else 0,
                'execution_time_minutes': opt.execution_time / 60,
                'strategies_per_second': opt.strategies_per_second,
                'parallel_workers': opt.parallel_workers
            }

        # 系統性能統計
        if self.performance_history:
            cpu_values = [m.cpu_usage for m in self.performance_history]
            memory_values = [m.memory_percent for m in self.performance_history]

            summary['system'] = {
                'avg_cpu_usage': np.mean(cpu_values),
                'max_cpu_usage': np.max(cpu_values),
                'avg_memory_usage': np.mean(memory_values),
                'max_memory_usage': np.max(memory_values),
                'samples_count': len(self.performance_history)
            }

        # API調用統計
        summary['api_calls'] = {}
        for api_name, times in self.api_call_stats.items():
            if times:
                summary['api_calls'][api_name] = {
                    'call_count': len(times),
                    'avg_time': np.mean(times),
                    'max_time': np.max(times),
                    'min_time': np.min(times)
                }

        return summary

    def detect_bottlenecks(self) -> List[str]:
        """檢測性能瓶頸"""
        bottlenecks = []

        if not self.performance_history:
            return bottlenecks

        # CPU瓶頸檢測
        cpu_values = [m.cpu_usage for m in self.performance_history]
        avg_cpu = np.mean(cpu_values)
        max_cpu = np.max(cpu_values)

        if max_cpu > self.cpu_threshold:
            bottlenecks.append(f"CPU使用率過高: 最大{max_cpu:.1f}% (閾值: {self.cpu_threshold}%)")

        if avg_cpu > self.cpu_threshold * 0.8:
            bottlenecks.append(f"CPU平均使用率較高: {avg_cpu:.1f}%")

        # 內存瓶頸檢測
        memory_values = [m.memory_percent for m in self.performance_history]
        avg_memory = np.mean(memory_values)
        max_memory = np.max(memory_values)

        if max_memory > self.memory_threshold:
            bottlenecks.append(f"內存使用率過高: 最大{max_memory:.1f}% (閾值: {self.memory_threshold}%)")

        if avg_memory > self.memory_threshold * 0.8:
            bottlenecks.append(f"內存平均使用率較高: {avg_memory:.1f}%")

        # 性能瓶頸檢測
        if self.optimization_metrics and self.optimization_metrics.strategies_per_second:
            current_perf = self.optimization_metrics.strategies_per_second
            if current_perf < self.performance_threshold:
                bottlenecks.append(f"處理速度低於預期: {current_perf:.1f} 策略/秒 (期望: {self.performance_threshold}+)")

        return bottlenecks

    def get_optimization_recommendations(self) -> List[str]:
        """獲取優化建議"""
        recommendations = []
        bottlenecks = self.detect_bottlenecks()

        # 基於瓶頸提供建議
        if any("CPU" in b for b in bottlenecks):
            recommendations.append("考慮增加並行工作線程數量")
            recommendations.append("檢查是否有CPU密集型操作可以優化")

        if any("內存" in b for b in bottlenecks):
            recommendations.append("啟用或增加緩存系統以減少內存重複計算")
            recommendations.append("考慮使用內存映射文件處理大數據集")

        if any("處理速度" in b for b in bottlenecks):
            recommendations.append("啟用智能緩存系統")
            recommendations.append("檢查數據源API響應時間")
            recommendations.append("考慮使用更高效的數據結構")

        # API調用優化建議
        for api_name, times in self.api_call_stats.items():
            if times and np.mean(times) > 2.0:  # API響應時間超過2秒
                recommendations.append(f"優化 {api_name} API調用性能 (當前平均: {np.mean(times):.2f}秒)")

        # 通用優化建議
        if not recommendations:
            recommendations.append("系統運行良好，考慮進一步優化以提升性能")
            recommendations.append("監控長期運行趨勢以預防潛在問題")

        return recommendations

    def export_performance_report(self, filename: Optional[str] = None) -> str:
        """導出性能報告"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"enhanced_performance_report_{timestamp}.json"

        report = {
            'timestamp': datetime.now().isoformat(),
            'performance_summary': self.get_performance_summary(),
            'bottlenecks': self.detect_bottlenecks(),
            'recommendations': self.get_optimization_recommendations(),
            'performance_history': [
                {
                    'timestamp': m.timestamp,
                    'cpu_usage': m.cpu_usage,
                    'memory_usage': m.memory_usage,
                    'memory_percent': m.memory_percent
                }
                for m in self.performance_history[-100:]  # 只保存最近100個數據點
            ]
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        return filename

    def get_real_time_metrics(self) -> Dict[str, float]:
        """獲取實時性能指標"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            process = psutil.Process()
            process_memory = process.memory_info().rss / 1024 / 1024  # MB

            return {
                'cpu_usage': cpu_percent,
                'memory_percent': memory.percent,
                'process_memory_mb': process_memory,
                'timestamp': time.time()
            }

        except Exception as e:
            print(f"[PERFORMANCE_MONITOR] 實時指標獲取失敗: {e}")
            return {}