#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPU內存管理器 - 解決大規模參數搜索的內存限制
GPU Memory Manager - Solving memory limitations for large-scale parameter search

實現動態批量大小計算、內存池管理和實時內存監控
"""

import numpy as np
import pandas as pd
import logging
import time
from typing import Dict, List, Tuple, Any, Optional, Union
from dataclasses import dataclass, field
from pathlib import Path
import json

# GPU加速庫
try:
    import cupy as cp
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False
    cp = None

from simplified_system.src.utils.gpu_detector import get_gpu_environment

logger = logging.getLogger(__name__)

@dataclass
class GPUMemoryMetrics:
    """GPU內存指標"""
    total_memory_mb: float = 0.0
    available_memory_mb: float = 0.0
    used_memory_mb: float = 0.0
    utilization_percentage: float = 0.0
    memory_fragmentation_score: float = 0.0
    allocation_efficiency: float = 0.0

@dataclass
class BatchSizeCalculation:
    """批量大小計算結果"""
    optimal_batch_size: int
    memory_per_item_mb: float
    estimated_utilization: float
    recommended_action: str
    safety_margin: float

class GPUMemoryManager:
    """
    GPU內存管理器

    實現智能GPU內存管理，支持：
    - 動態批量大小計算
    - 內存池管理
    - 實時內存監控
    - 內存溢出保護
    """

    def __init__(self,
                 memory_fraction: float = 0.8,
                 min_batch_size: int = 100,
                 max_batch_size: int = 10000,
                 safety_margin: float = 0.1):
        """
        初始化GPU內存管理器

        Args:
            memory_fraction: GPU內存使用比例 (0.1-0.95)
            min_batch_size: 最小批量大小
            max_batch_size: 最大批量大小
            safety_margin: 安全邊際比例
        """
        self.memory_fraction = max(0.1, min(0.95, memory_fraction))
        self.min_batch_size = min_batch_size
        self.max_batch_size = max_batch_size
        self.safety_margin = safety_margin

        # 初始化GPU環境
        self.gpu_env = get_gpu_environment()
        self.use_gpu = self.gpu_env.is_gpu_available() and GPU_AVAILABLE

        # 內存池
        self.memory_pool = {}
        self.allocated_blocks = {}

        # 性能統計
        self.allocation_history = []
        self.batch_size_history = []
        self.optimization_stats = {
            'total_allocations': 0,
            'successful_allocations': 0,
            'memory_overflows_prevented': 0,
            'average_batch_size': 0,
            'peak_memory_usage': 0
        }

        # 監控配置
        self.monitoring_enabled = True
        self.monitoring_interval = 1.0  # 秒
        self.last_monitoring_time = time.time()

        if self.use_gpu:
            self._initialize_gpu_memory_management()
        else:
            logger.warning("GPU not available, falling back to CPU memory management")

    def _initialize_gpu_memory_management(self) -> None:
        """初始化GPU內存管理"""
        try:
            # 獲取GPU信息
            gpu_info = self.gpu_env.get_system_info()
            logger.info(f"Initializing GPU memory management for {gpu_info.get('device_name', 'Unknown')}")

            # 預分配內存池
            self._initialize_memory_pool()

            logger.info(f"GPU Memory Manager initialized - Available: {self.get_memory_metrics().available_memory_mb:.1f} MB")

        except Exception as e:
            logger.error(f"Failed to initialize GPU memory management: {e}")
            self.use_gpu = False

    def _initialize_memory_pool(self) -> None:
        """初始化GPU內存池"""
        if not self.use_gpu:
            return

        try:
            # 計算池大小
            available_memory = self._get_available_gpu_memory()
            pool_size = int(available_memory * self.memory_fraction * 0.3)  # 30% for pool

            # 預分配常見大小的內存塊
            common_sizes = [1024, 2048, 4096, 8192, 16384]  # 不同大小的塊
            self.memory_pool = {}

            for size in common_sizes:
                num_blocks = min(10, pool_size // size)
                if num_blocks > 0:
                    self.memory_pool[size] = []
                    for _ in range(num_blocks):
                        try:
                            block = cp.zeros(size, dtype=cp.float32)
                            self.memory_pool[size].append(block)
                        except cp.cuda.memory.OutOfMemoryError:
                            logger.warning(f"Could not allocate memory pool block of size {size}")
                            break

            logger.info(f"GPU memory pool initialized with {sum(len(blocks) for blocks in self.memory_pool.values())} blocks")

        except Exception as e:
            logger.error(f"Failed to initialize memory pool: {e}")

    def _get_available_gpu_memory(self) -> float:
        """獲取可用GPU內存（MB）"""
        if not self.use_gpu:
            return 0.0

        try:
            # 使用CuPy獲取內存信息
            mempool = cp.get_default_memory_pool()
            total_bytes = mempool.total_bytes()
            used_bytes = mempool.used_bytes()

            total_mb = total_bytes / (1024 * 1024)
            available_mb = (total_bytes - used_bytes) / (1024 * 1024)

            return available_mb

        except Exception as e:
            logger.warning(f"Could not get GPU memory info: {e}")
            return 0.0

    def calculate_optimal_batch_size(self,
                                    parameter_combinations: List[Dict],
                                    estimated_memory_per_item: Optional[float] = None) -> BatchSizeCalculation:
        """
        動態計算最優批量大小

        Args:
            parameter_combinations: 參數組合列表
            estimated_memory_per_item: 每個項目的估計內存需求（MB）

        Returns:
            批量大小計算結果
        """
        if not self.use_gpu:
            # CPU模式使用較小批量
            return BatchSizeCalculation(
                optimal_batch_size=min(1000, len(parameter_combinations)),
                memory_per_item_mb=0.0,
                estimated_utilization=0.5,
                recommended_action="CPU mode - using conservative batch size",
                safety_margin=0.2
            )

        try:
            # 估算每個參數組合的內存需求
            if estimated_memory_per_item is None:
                estimated_memory_per_item = self._estimate_memory_per_combination(parameter_combinations[0] if parameter_combinations else {})

            # 獲取可用內存
            available_memory = self._get_available_gpu_memory()
            usable_memory = available_memory * (1 - self.safety_margin)

            # 計算理論批量大小
            theoretical_batch_size = int(usable_memory / estimated_memory_per_item)

            # 應用限制
            optimal_batch_size = max(
                self.min_batch_size,
                min(theoretical_batch_size, self.max_batch_size, len(parameter_combinations))
            )

            # 計算預期利用率
            estimated_usage = optimal_batch_size * estimated_memory_per_item
            estimated_utilization = estimated_usage / available_memory

            # 確定建議操作
            if estimated_utilization > 0.9:
                recommended_action = "High memory usage - monitor closely"
            elif estimated_utilization > 0.7:
                recommended_action = "Optimal memory usage"
            elif estimated_utilization > 0.5:
                recommended_action = "Moderate memory usage - could increase batch size"
            else:
                recommended_action = "Low memory usage - could significantly increase batch size"

            # 記錄批量大小歷史
            self.batch_size_history.append({
                'timestamp': time.time(),
                'batch_size': optimal_batch_size,
                'utilization': estimated_utilization,
                'items_processed': len(parameter_combinations)
            })

            return BatchSizeCalculation(
                optimal_batch_size=optimal_batch_size,
                memory_per_item_mb=estimated_memory_per_item,
                estimated_utilization=estimated_utilization,
                recommended_action=recommended_action,
                safety_margin=self.safety_margin
            )

        except Exception as e:
            logger.error(f"Error calculating optimal batch size: {e}")
            return BatchSizeCalculation(
                optimal_batch_size=self.min_batch_size,
                memory_per_item_mb=0.0,
                estimated_utilization=0.0,
                recommended_action=f"Error: {e}",
                safety_margin=self.safety_margin
            )

    def _estimate_memory_per_combination(self, sample_params: Dict) -> float:
        """
        估算單個參數組合的內存需求

        Args:
            sample_params: 樣本參數

        Returns:
            估算內存需求（MB）
        """
        try:
            # 基礎內存需求
            base_memory = 1.0  # MB

            # 參數相關內存
            param_memory = len(sample_params) * 0.1  # 每個參數0.1MB

            # 數據相關內存（基於經驗估算）
            data_memory = 5.0  # 假設每個組合需要5MB數據緩存

            # GPU計算緩衝
            gpu_buffer_memory = 2.0  # MB

            total_memory = base_memory + param_memory + data_memory + gpu_buffer_memory

            return total_memory

        except Exception as e:
            logger.warning(f"Error estimating memory per combination: {e}")
            return 10.0  # 保守估算

    def allocate_from_pool(self, size: int) -> Optional[cp.ndarray]:
        """
        從內存池分配內存

        Args:
            size: 所需內存大小（元素數量）

        Returns:
            分配的內存塊，如果失敗返回None
        """
        if not self.use_gpu or not self.memory_pool:
            return None

        try:
            # 尋找最接近的可用塊
            pool_sizes = sorted(self.memory_pool.keys())

            for pool_size in pool_sizes:
                if pool_size >= size and self.memory_pool[pool_size]:
                    block = self.memory_pool[pool_size].pop()
                    self.allocated_blocks[id(block)] = (pool_size, time.time())
                    return block

            # 如果沒有合適的塊，直接分配
            return cp.zeros(size, dtype=cp.float32)

        except Exception as e:
            logger.error(f"Error allocating from pool: {e}")
            return None

    def return_to_pool(self, block: cp.ndarray) -> None:
        """
        將內存塊返回到池中

        Args:
            block: 要返回的內存塊
        """
        if not self.use_gpu or not self.memory_pool:
            return

        try:
            block_id = id(block)
            if block_id in self.allocated_blocks:
                pool_size, _ = self.allocated_blocks[block_id]

                if pool_size in self.memory_pool and len(self.memory_pool[pool_size]) < 10:
                    # 重置並返回到池中
                    block.fill(0)
                    self.memory_pool[pool_size].append(block)
                else:
                    # 釋放內存
                    del block

                del self.allocated_blocks[block_id]

        except Exception as e:
            logger.warning(f"Error returning block to pool: {e}")

    def get_memory_metrics(self) -> GPUMemoryMetrics:
        """
        獲取GPU內存指標

        Returns:
            GPU內存指標
        """
        if not self.use_gpu:
            return GPUMemoryMetrics()

        try:
            mempool = cp.get_default_memory_pool()
            total_bytes = mempool.total_bytes()
            used_bytes = mempool.used_bytes()

            total_mb = total_bytes / (1024 * 1024)
            used_mb = used_bytes / (1024 * 1024)
            available_mb = (total_bytes - used_bytes) / (1024 * 1024)
            utilization = used_bytes / total_bytes if total_bytes > 0 else 0

            # 計算內存碎片分數（簡化版）
            fragmentation_score = self._calculate_fragmentation_score()

            # 計算分配效率
            allocation_efficiency = self._calculate_allocation_efficiency()

            # 更新峰值使用量
            peak_usage = max(self.optimization_stats['peak_memory_usage'], used_mb)
            self.optimization_stats['peak_memory_usage'] = peak_usage

            return GPUMemoryMetrics(
                total_memory_mb=total_mb,
                available_memory_mb=available_mb,
                used_memory_mb=used_mb,
                utilization_percentage=utilization * 100,
                memory_fragmentation_score=fragmentation_score,
                allocation_efficiency=allocation_efficiency
            )

        except Exception as e:
            logger.error(f"Error getting memory metrics: {e}")
            return GPUMemoryMetrics()

    def _calculate_fragmentation_score(self) -> float:
        """計算內存碎片分數（0-1，越高越嚴重）"""
        try:
            if not self.memory_pool:
                return 0.0

            total_blocks = sum(len(blocks) for blocks in self.memory_pool.values())
            allocated_blocks = len(self.allocated_blocks)

            if total_blocks == 0:
                return 0.0

            # 簡化的碎片分數計算
            fragmentation = min(1.0, allocated_blocks / total_blocks)
            return fragmentation

        except Exception:
            return 0.0

    def _calculate_allocation_efficiency(self) -> float:
        """計算內存分配效率（0-1，越高越好）"""
        try:
            total_allocations = self.optimization_stats['total_allocations']
            successful_allocations = self.optimization_stats['successful_allocations']

            if total_allocations == 0:
                return 1.0

            efficiency = successful_allocations / total_allocations
            return min(1.0, efficiency)

        except Exception:
            return 1.0

    def check_memory_overflow_risk(self, batch_size: int, memory_per_item: float) -> bool:
        """
        檢查內存溢出風險

        Args:
            batch_size: 批量大小
            memory_per_item: 每個項目的內存需求

        Returns:
            是否有溢出風險
        """
        if not self.use_gpu:
            return False

        try:
            available_memory = self._get_available_gpu_memory()
            required_memory = batch_size * memory_per_item
            risk_threshold = available_memory * 0.95  # 95%閾值

            if required_memory > risk_threshold:
                self.optimization_stats['memory_overflows_prevented'] += 1
                logger.warning(f"Memory overflow risk detected: required={required_memory:.1f}MB, available={available_memory:.1f}MB")
                return True

            return False

        except Exception as e:
            logger.error(f"Error checking memory overflow risk: {e}")
            return True  # 保守處理

    def monitor_memory_usage(self) -> Dict[str, Any]:
        """
        監控內存使用情況

        Returns:
            內存監控報告
        """
        current_time = time.time()

        # 檢查是否需要監控
        if current_time - self.last_monitoring_time < self.monitoring_interval:
            return {}

        self.last_monitoring_time = current_time

        try:
            metrics = self.get_memory_metrics()

            monitor_report = {
                'timestamp': current_time,
                'gpu_available': self.use_gpu,
                'total_memory_mb': metrics.total_memory_mb,
                'available_memory_mb': metrics.available_memory_mb,
                'used_memory_mb': metrics.used_memory_mb,
                'utilization_percentage': metrics.utilization_percentage,
                'fragmentation_score': metrics.memory_fragmentation_score,
                'allocation_efficiency': metrics.allocation_efficiency,
                'memory_pool_blocks': sum(len(blocks) for blocks in self.memory_pool.values()) if self.memory_pool else 0,
                'allocated_blocks': len(self.allocated_blocks)
            }

            # 性能統計
            monitor_report['optimization_stats'] = self.optimization_stats.copy()

            # 記錄監控歷史
            self.allocation_history.append(monitor_report)

            # 保持歷史記錄在合理範圍內
            if len(self.allocation_history) > 1000:
                self.allocation_history = self.allocation_history[-1000:]

            return monitor_report

        except Exception as e:
            logger.error(f"Error in memory monitoring: {e}")
            return {'error': str(e), 'timestamp': current_time}

    def get_optimization_report(self) -> Dict[str, Any]:
        """
        獲取優化報告

        Returns:
            優化統計報告
        """
        try:
            stats = self.optimization_stats.copy()

            # 計算平均批量大小
            if self.batch_size_history:
                avg_batch_size = np.mean([item['batch_size'] for item in self.batch_size_history])
                stats['average_batch_size'] = avg_batch_size
                stats['batch_size_variance'] = np.var([item['batch_size'] for item in self.batch_size_history])
                stats['total_batches_processed'] = len(self.batch_size_history)

            # 當前內存狀態
            current_metrics = self.get_memory_metrics()
            stats['current_memory_state'] = {
                'utilization_percentage': current_metrics.utilization_percentage,
                'available_memory_mb': current_metrics.available_memory_mb,
                'fragmentation_score': current_metrics.memory_fragmentation_score,
                'allocation_efficiency': current_metrics.allocation_efficiency
            }

            # 內存池效率
            if self.memory_pool:
                total_pool_blocks = sum(len(blocks) for blocks in self.memory_pool.values())
                stats['memory_pool_efficiency'] = {
                    'total_blocks': total_pool_blocks,
                    'allocated_blocks': len(self.allocated_blocks),
                    'pool_utilization': len(self.allocated_blocks) / max(1, total_pool_blocks)
                }

            return stats

        except Exception as e:
            logger.error(f"Error generating optimization report: {e}")
            return {'error': str(e)}

    def cleanup(self) -> None:
        """清理資源"""
        try:
            if self.use_gpu:
                # 清理內存池
                if self.memory_pool:
                    for size_blocks in self.memory_pool.values():
                        for block in size_blocks:
                            del block
                    self.memory_pool.clear()

                # 清理分配的塊
                for block_id in list(self.allocated_blocks.keys()):
                    block = self.allocated_blocks[block_id][0] if block_id in self.allocated_blocks else None
                    if block is not None:
                        del block
                self.allocated_blocks.clear()

                # 清理CuPy緩存
                cp.get_default_memory_pool().free_all_blocks()

            logger.info("GPU Memory Manager cleaned up successfully")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

# 便利函數
def create_gpu_memory_manager(memory_fraction: float = 0.8) -> GPUMemoryManager:
    """
    創建GPU內存管理器實例

    Args:
        memory_fraction: 內存使用比例

    Returns:
        GPU內存管理器實例
    """
    return GPUMemoryManager(memory_fraction=memory_fraction)

if __name__ == "__main__":
    # 測試GPU內存管理器
    logging.basicConfig(level=logging.INFO)

    memory_manager = create_gpu_memory_manager()

    # 測試批量大小計算
    test_params = [{'rsi_period': 14, 'oversold': 30, 'overbought': 70}]
    batch_calc = memory_manager.calculate_optimal_batch_size(test_params * 1000)

    print(f"Optimal batch size: {batch_calc.optimal_batch_size}")
    print(f"Estimated utilization: {batch_calc.estimated_utilization:.2%}")
    print(f"Recommended action: {batch_calc.recommended_action}")

    # 顯示內存指標
    metrics = memory_manager.get_memory_metrics()
    print(f"Available GPU memory: {metrics.available_memory_mb:.1f} MB")
    print(f"Current utilization: {metrics.utilization_percentage:.1f}%")

    # 清理
    memory_manager.cleanup()