#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPU内存管理器
优化GPU内存使用，实现批处理和内存清理
"""

import logging
import gc
import numpy as np
from typing import List, Dict, Any, Optional, Union
import warnings

try:
    import cupy as cp
    GPU_AVAILABLE = True
except ImportError:
    cp = None
    GPU_AVAILABLE = False

logger = logging.getLogger(__name__)

class GPUMemoryManager:
    """GPU内存管理器"""

    def __init__(self, device_id: int = 0):
        self.device_id = device_id
        self.memory_pools = {}
        self.allocation_stats = {
            'total_allocations': 0,
            'total_freed': 0,
            'peak_memory_mb': 0,
            'current_memory_mb': 0
        }
        self.gpu_available = GPU_AVAILABLE

        if self.gpu_available:
            try:
                cp.cuda.Device(device_id).use()
                self.memory_pool = cp.get_default_memory_pool()
                self.pinned_memory_pool = cp.get_default_pinned_memory_pool()
                self._initialize_memory_tracking()
                logger.info(f"GPU内存管理器初始化，设备: {device_id}")
            except Exception as e:
                logger.error(f"GPU内存管理器初始化失败: {e}")
                self.gpu_available = False
        else:
            logger.warning("GPU不可用，内存管理器禁用")

    def _initialize_memory_tracking(self):
        """初始化内存跟踪"""
        try:
            # 获取GPU总内存
            device = cp.cuda.Device(self.device_id)
            self.total_memory_mb = device.attributes['TotalGlobalMem'] / (1024 * 1024)
            logger.info(f"GPU总内存: {self.total_memory_mb:.1f} MB")
        except Exception as e:
            logger.error(f"内存跟踪初始化失败: {e}")
            self.total_memory_mb = 0

    def get_memory_usage(self) -> Dict[str, float]:
        """获取当前内存使用情况"""
        if not self.gpu_available:
            return {'error': 'GPU不可用'}

        try:
            used_bytes = self.memory_pool.used_bytes()
            total_bytes = self.memory_pool.total_bytes()
            free_bytes, total_bytes_device = cp.cuda.runtime.memGetInfo()

            usage = {
                'used_mb': used_bytes / (1024 * 1024),
                'total_mb': total_bytes / (1024 * 1024),
                'utilization': (used_bytes / total_bytes * 100) if total_bytes > 0 else 0,
                'device_used_mb': (total_bytes_device - free_bytes) / (1024 * 1024),
                'device_total_mb': total_bytes_device / (1024 * 1024),
                'device_utilization': ((total_bytes_device - free_bytes) / total_bytes_device * 100) if total_bytes_device > 0 else 0
            }

            # 更新统计
            self.allocation_stats['current_memory_mb'] = usage['used_mb']
            if usage['used_mb'] > self.allocation_stats['peak_memory_mb']:
                self.allocation_stats['peak_memory_mb'] = usage['used_mb']

            return usage

        except Exception as e:
            logger.error(f"内存使用查询失败: {e}")
            return {'error': str(e)}

    def allocate_optimal(self, data_shape: tuple, dtype=cp.float32) -> cp.ndarray:
        """优化内存分配"""
        if not self.gpu_available:
            raise RuntimeError("GPU不可用")

        try:
            # 检查可用内存
            memory_usage = self.get_memory_usage()
            if 'error' in memory_usage:
                raise RuntimeError(memory_usage['error'])

            # 估算所需内存
            element_size = 4 if dtype == cp.float32 else 8  # float32=4字节, float64=8字节
            required_mb = (data_shape[0] * element_size) / (1024 * 1024)

            # 检查是否有足够内存
            available_mb = memory_usage['total_mb'] - memory_usage['used_mb']
            if required_mb > available_mb * 0.8:  # 保留20%缓冲
                logger.warning(f"内存不足，尝试清理后重新分配: 需要 {required_mb:.1f}MB，可用 {available_mb:.1f}MB")
                self.cleanup_memory()

                # 重新检查内存
                memory_usage = self.get_memory_usage()
                available_mb = memory_usage['total_mb'] - memory_usage['used_mb']

                if required_mb > available_mb * 0.8:
                    raise RuntimeError(f"内存不足: 需要 {required_mb:.1f}MB，可用 {available_mb:.1f}MB")

            # 分配内存
            array = cp.zeros(data_shape, dtype=dtype)
            self.allocation_stats['total_allocations'] += 1

            logger.debug(f"成功分配GPU内存: {data_shape}, {required_mb:.1f}MB")
            return array

        except Exception as e:
            logger.error(f"GPU内存分配失败: {e}")
            raise

    def batch_process(self, data_list: List[Union[np.ndarray, cp.ndarray]],
                     batch_size: Optional[int] = None, operation_func=None) -> List[cp.ndarray]:
        """大数据分批处理"""
        if not self.gpu_available:
            raise RuntimeError("GPU不可用")

        if not data_list:
            return []

        # 自动确定批处理大小
        if batch_size is None:
            batch_size = self._calculate_optimal_batch_size(data_list)

        results = []
        total_batches = (len(data_list) + batch_size - 1) // batch_size

        logger.info(f"开始批处理: {len(data_list)}个项目，批大小: {batch_size}，总批次数: {total_batches}")

        for i in range(0, len(data_list), batch_size):
            batch = data_list[i:i + batch_size]
            batch_num = i // batch_size + 1

            try:
                # 处理当前批次
                if operation_func:
                    batch_result = operation_func(batch)
                else:
                    batch_result = [cp.asarray(item) for item in batch]

                results.extend(batch_result)

                logger.debug(f"批次 {batch_num}/{total_batches} 处理完成")

                # 每处理几个批次后清理内存
                if batch_num % 5 == 0:
                    self.cleanup_memory()

            except Exception as e:
                logger.error(f"批次 {batch_num} 处理失败: {e}")
                # 继续处理下一批次
                continue

        logger.info(f"批处理完成: 成功处理 {len(results)}/{len(data_list)} 个项目")
        return results

    def _calculate_optimal_batch_size(self, data_list: List[Union[np.ndarray, cp.ndarray]]) -> int:
        """计算最优批处理大小"""
        try:
            # 获取内存使用情况
            memory_usage = self.get_memory_usage()
            if 'error' in memory_usage:
                return min(100, len(data_list))  # 默认值

            available_mb = memory_usage['total_mb'] - memory_usage['used_mb']
            safe_available_mb = available_mb * 0.7  # 保留30%安全边际

            # 估算单个项目的内存需求
            if data_list:
                sample_item = data_list[0]
                if hasattr(sample_item, 'nbytes'):
                    item_size_mb = sample_item.nbytes / (1024 * 1024)
                elif hasattr(sample_item, 'size'):
                    # 假设float32
                    item_size_mb = (sample_item.size * 4) / (1024 * 1024)
                else:
                    item_size_mb = 1.0  # 默认1MB

                # 计算批大小
                optimal_batch_size = max(1, int(safe_available_mb / item_size_mb))
                return min(optimal_batch_size, len(data_list), 1000)  # 限制最大批大小

            return min(100, len(data_list))

        except Exception as e:
            logger.error(f"批大小计算失败: {e}")
            return min(100, len(data_list))

    def cleanup_memory(self, aggressive: bool = False):
        """清理GPU内存"""
        if not self.gpu_available:
            return

        try:
            # 基础清理
            self.memory_pool.free_all_blocks()
            self.pinned_memory_pool.free_all_blocks()

            # 强制垃圾回收
            gc.collect()

            if aggressive:
                # 激进清理：同步所有GPU操作
                cp.cuda.Device(self.device_id).synchronize()

                # 清理所有缓存
                cp.get_default_memory_pool().free_all_blocks()
                cp.get_default_pinned_memory_pool().free_all_blocks()

                # 多次垃圾回收
                for _ in range(3):
                    gc.collect()

            logger.debug("GPU内存清理完成")

        except Exception as e:
            logger.error(f"GPU内存清理失败: {e}")

    def memory_efficient_copy(self, source: Union[np.ndarray, cp.ndarray],
                            target: Optional[cp.ndarray] = None) -> cp.ndarray:
        """内存高效的数组复制"""
        if not self.gpu_available:
            raise RuntimeError("GPU不可用")

        try:
            # 如果已经在GPU上，直接复制
            if isinstance(source, cp.ndarray):
                if target is not None and target.shape == source.shape:
                    target[:] = source
                    return target
                else:
                    return source.copy()

            # 如果在CPU上，传输到GPU
            else:
                if target is not None and target.shape == source.shape:
                    target.set(source)
                    return target
                else:
                    return cp.asarray(source)

        except Exception as e:
            logger.error(f"内存高效复制失败: {e}")
            raise

    def optimize_memory_layout(self, array: cp.ndarray) -> cp.ndarray:
        """优化内存布局"""
        if not isinstance(array, cp.ndarray):
            return cp.asarray(array)

        try:
            # 确保内存连续
            if not array.flags['C_CONTIGUOUS']:
                array = cp.ascontiguousarray(array)

            return array

        except Exception as e:
            logger.error(f"内存布局优化失败: {e}")
            return array

    def get_memory_stats(self) -> Dict[str, Any]:
        """获取内存统计信息"""
        stats = self.allocation_stats.copy()
        stats.update(self.get_memory_usage())
        stats['device_id'] = self.device_id
        stats['gpu_available'] = self.gpu_available
        return stats

    def benchmark_memory_performance(self, data_size: int = 1000000) -> Dict[str, float]:
        """内存性能基准测试"""
        if not self.gpu_available:
            return {'error': 'GPU不可用'}

        try:
            import time
            import numpy as np

            # 生成测试数据
            test_data = np.random.rand(data_size).astype(np.float32)

            # 测试分配性能
            start_time = time.time()
            gpu_array = self.allocate_optimal((data_size,), cp.float32)
            allocation_time = time.time() - start_time

            # 测试传输性能
            start_time = time.time()
            gpu_array.set(test_data)
            transfer_time = time.time() - start_time

            # 测试复制性能
            start_time = time.time()
            copied_array = gpu_array.copy()
            copy_time = time.time() - start_time

            # 清理
            del gpu_array, copied_array
            self.cleanup_memory()

            return {
                'data_size_mb': data_size * 4 / (1024 * 1024),
                'allocation_time_ms': allocation_time * 1000,
                'transfer_time_ms': transfer_time * 1000,
                'copy_time_ms': copy_time * 1000,
                'allocation_speed_mb_per_s': (data_size * 4 / (1024 * 1024)) / allocation_time,
                'transfer_speed_mb_per_s': (data_size * 4 / (1024 * 1024)) / transfer_time
            }

        except Exception as e:
            logger.error(f"内存性能基准测试失败: {e}")
            return {'error': str(e)}

    def create_memory_profile(self, duration_seconds: int = 60) -> Dict[str, Any]:
        """创建内存使用档案"""
        if not self.gpu_available:
            return {'error': 'GPU不可用'}

        try:
            import time

            profile_data = []
            start_time = time.time()

            logger.info(f"开始内存建档，持续时间: {duration_seconds}秒")

            while time.time() - start_time < duration_seconds:
                memory_usage = self.get_memory_usage()
                memory_usage['timestamp'] = time.time()
                profile_data.append(memory_usage)

                time.sleep(1)  # 每秒采样一次

            # 分析档案数据
            if profile_data:
                avg_utilization = sum(p['utilization'] for p in profile_data) / len(profile_data)
                max_utilization = max(p['utilization'] for p in profile_data)
                min_utilization = min(p['utilization'] for p in profile_data)

                return {
                    'duration_seconds': duration_seconds,
                    'sample_count': len(profile_data),
                    'avg_utilization': avg_utilization,
                    'max_utilization': max_utilization,
                    'min_utilization': min_utilization,
                    'profile_data': profile_data
                }
            else:
                return {'error': '无数据收集'}

        except Exception as e:
            logger.error(f"内存建档失败: {e}")
            return {'error': str(e)}

    def reset_statistics(self):
        """重置统计信息"""
        self.allocation_stats = {
            'total_allocations': 0,
            'total_freed': 0,
            'peak_memory_mb': 0,
            'current_memory_mb': 0
        }
        logger.info("内存统计信息已重置")


def get_gpu_memory_manager(device_id: int = 0) -> GPUMemoryManager:
    """获取GPU内存管理器实例"""
    return GPUMemoryManager(device_id)


# 内存管理上下文
class ManagedGPUMemory:
    """GPU内存管理上下文"""

    def __init__(self, device_id: int = 0):
        self.memory_manager = get_gpu_memory_manager(device_id)
        self.allocations = []

    def __enter__(self):
        return self.memory_manager

    def __exit__(self, exc_type, exc_val, exc_tb):
        # 清理所有分配的内存
        self.memory_manager.cleanup_memory(aggressive=True)
        return False


# 测试代码
if __name__ == "__main__":
    # 测试GPU内存管理器
    try:
        import numpy as np

        with ManagedGPUMemory() as memory_manager:
            print("Starting GPU memory management test...")

            # 获取内存使用情况
            memory_usage = memory_manager.get_memory_usage()
            print(f"Initial memory usage: {memory_usage}")

            # 测试内存分配
            test_array = memory_manager.allocate_optimal((10000,), cp.float32)
            print(f"Allocated 10000 float32 array")

            memory_usage = memory_manager.get_memory_usage()
            print(f"Memory usage after allocation: {memory_usage}")

            # 测试批处理
            test_data = [np.random.rand(1000) for _ in range(10)]
            batch_results = memory_manager.batch_process(test_data, batch_size=3)
            print(f"Batch processing completed: {len(batch_results)} results")

            # 性能基准测试
            benchmark = memory_manager.benchmark_memory_performance(500000)
            print(f"Memory performance benchmark: {benchmark}")

            # 获取统计信息
            stats = memory_manager.get_memory_stats()
            print(f"Memory stats: {stats}")

            # 清理内存
            memory_manager.cleanup_memory()
            print("Memory cleanup completed")

    except Exception as e:
        print(f"GPU memory management test failed: {e}")