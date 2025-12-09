#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPU加速支持系統
GPU Acceleration Support System

提供安全、可靠的GPU加速功能，包括檢測、配置、性能優化和錯誤恢復
Provides secure, reliable GPU acceleration features including detection, configuration, performance optimization and error recovery
"""

import logging
import time
import json
import warnings
from typing import Dict, Any, Optional, List, Tuple, Union
from pathlib import Path
from dataclasses import dataclass
import numpy as np
import pandas as pd

# 安全導入GPU依賴
try:
    import cupy as cp
    import cupyx.scipy as cusp
    import cupyx.scipy.ndimage as cupyx_ndimage
    GPU_AVAILABLE = True
except ImportError:
    cp = None
    cusp = None
    cupyx_ndimage = None
    GPU_AVAILABLE = False

try:
    import numba
    from numba import cuda
    NUMBA_AVAILABLE = True
except ImportError:
    numba = None
    cuda = None
    NUMBA_AVAILABLE = False

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    torch = None
    TORCH_AVAILABLE = False

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    psutil = None
    PSUTIL_AVAILABLE = False

# 導入項目模塊
from src.utils.dependency_manager import DependencyManager

logger = logging.getLogger(__name__)

@dataclass
class GPUSafetyConfig:
    """GPU安全配置"""
    max_gpu_memory_usage: float = 0.8  # 最大GPU內存使用率80%
    max_gpu_temperature: float = 85.0  # 最大GPU溫度85°C
    enable_memory_check: bool = True
    enable_temperature_check: bool = True
    enable_driver_validation: bool = True
    auto_fallback_to_cpu: bool = True
    performance_monitoring: bool = True

@dataclass
class GPUPerformanceProfile:
    """GPU性能配置文件"""
    device_name: str
    device_id: int
    memory_total: int  # MB
    memory_available: int  # MB
    compute_capability: str
    driver_version: str
    cuda_version: str
    theoretical_bandwidth: float  # GB/s
    multiprocessor_count: int

@dataclass
class GPUBenchmarkResult:
    """GPU基準測試結果"""
    test_name: str
    cpu_time: float
    gpu_time: float
    speedup_ratio: float
    memory_usage_mb: float
    peak_memory_mb: float
    success: bool
    error_message: Optional[str] = None

class GPUSafetyManager:
    """GPU安全管理器"""

    def __init__(self, config: GPUSafetyConfig = None):
        self.config = config or GPUSafetyConfig()
        self.performance_profile: Optional[GPUPerformanceProfile] = None
        self.benchmark_results: List[GPUBenchmarkResult] = []
        self.initialized = False

    def initialize_gpu_environment(self) -> bool:
        """安全初始化GPU環境"""
        if not GPU_AVAILABLE:
            logger.warning("CuPy不可用，無法初始化GPU環境")
            return False

        try:
            # 1. 驅動程序驗證
            if self.config.enable_driver_validation and not self._validate_gpu_driver():
                logger.error("GPU驅動程序驗證失敗")
                return False

            # 2. 設備檢測
            if not self._detect_gpu_device():
                logger.error("GPU設備檢測失敗")
                return False

            # 3. 內存安全檢查
            if self.config.enable_memory_check and not self._validate_gpu_memory():
                logger.error("GPU內存驗證失敗")
                return False

            # 4. 溫度檢查
            if self.config.enable_temperature_check and not self._validate_gpu_temperature():
                logger.error("GPU溫度驗證失敗")
                return False

            # 5. 性能測試
            if not self._run_initial_performance_test():
                logger.error("GPU性能測試失敗")
                return False

            self.initialized = True
            logger.info("GPU環境初始化成功")
            return True

        except Exception as e:
            logger.error(f"GPU環境初始化失敗: {e}")
            if self.config.auto_fallback_to_cpu:
                logger.info("自動降級到CPU模式")
            return False

    def _validate_gpu_driver(self) -> bool:
        """驗證GPU驅動程序安全性"""
        try:
            if not GPU_AVAILABLE:
                return False

            # 檢查CUDA運行時
            if cp.cuda.is_available():
                # 檢查驅動版本
                driver_version = cp.cuda.runtime.runtimeGetVersion()
                logger.info(f"CUDA運行時版本: {driver_version}")

                # 檢查設備
                device_count = cp.cuda.runtime.getDeviceCount()
                if device_count <= 0:
                    logger.error("未檢測到CUDA設備")
                    return False

                logger.info(f"檢測到 {device_count} 個CUDA設備")
                return True
            else:
                logger.error("CUDA運行時不可用")
                return False

        except Exception as e:
            logger.error(f"GPU驅動程序驗證失敗: {e}")
            return False

    def _detect_gpu_device(self) -> bool:
        """檢測GPU設備信息"""
        try:
            if not GPU_AVAILABLE:
                return False

            # 獲取GPU設備信息
            device = cp.cuda.Device()
            device_id = device.id
            device_name = device.name.decode('utf-8') if isinstance(device.name, bytes) else device_name

            # 內存信息
            memory_info = device.mem_info
            memory_total = memory_info[0] // (1024 * 1024)  # MB
            memory_available = memory_info[1] // (1024 * 1024)  # MB

            # 計算能力
            compute_capability = f"{device.compute_capability[0]}.{device.compute_capability[1]}"

            # 創建性能配置文件
            self.performance_profile = GPUPerformanceProfile(
                device_name=device_name,
                device_id=device_id,
                memory_total=memory_total,
                memory_available=memory_available,
                compute_capability=compute_capability,
                driver_version="Unknown",  # 需要nvidia-ml-py獲取
                cuda_version="Unknown",
                theoretical_bandwidth=self._estimate_bandwidth(device),
                multiprocessor_count=device.attributes["MultiProcessorCount"]
            )

            logger.info(f"檢測到GPU: {device_name} ({memory_total}MB)")
            return True

        except Exception as e:
            logger.error(f"GPU設備檢測失敗: {e}")
            return False

    def _estimate_bandwidth(self, device) -> float:
        """估算GPU內存帶寬"""
        try:
            # 簡化的帶寬估算，實際應用中可以使用nvidia-ml-py獲取精確值
            sm_count = device.attributes["MultiProcessorCount"]
            # 假設每個SM的帶寬為64GB/s（保守估計）
            return sm_count * 64.0
        except:
            return 512.0  # 默認值

    def _validate_gpu_memory(self) -> bool:
        """驗證GPU內存狀態"""
        try:
            if not self.performance_profile:
                return False

            # 檢查可用內存
            memory_usage_ratio = 1.0 - (self.performance_profile.memory_available / self.performance_profile.memory_total)

            if memory_usage_ratio > self.config.max_gpu_memory_usage:
                logger.warning(f"GPU內存使用率過高: {memory_usage_ratio:.1%}")
                return False

            logger.info(f"GPU內存狀態正常，使用率: {memory_usage_ratio:.1%}")
            return True

        except Exception as e:
            logger.error(f"GPU內存驗證失敗: {e}")
            return False

    def _validate_gpu_temperature(self) -> bool:
        """驗證GPU溫度"""
        try:
            # 需要nvidia-ml-py來獲取溫度，這裡做簡化檢查
            # 在生產環境中應該安裝nvidia-ml-py獲取準確的溫度信息
            logger.info("GPU溫度檢查跳過（需要nvidia-ml-py）")
            return True

        except Exception as e:
            logger.error(f"GPU溫度驗證失敗: {e}")
            return False

    def _run_initial_performance_test(self) -> bool:
        """運行初始性能測試"""
        try:
            if not GPU_AVAILABLE:
                return False

            # 簡單的矩陣乘法測試
            size = 1000
            a = cp.random.random((size, size), dtype=cp.float32)
            b = cp.random.random((size, size), dtype=cp.float32)

            start_time = time.time()
            c = cp.dot(a, b)
            cp.cuda.Stream.null.synchronize()
            gpu_time = time.time() - start_time

            logger.info(f"GPU性能測試通過 ({size}x{size} 矩陣乘法: {gpu_time:.3f}s)")
            return True

        except Exception as e:
            logger.error(f"GPU性能測試失敗: {e}")
            return False

    def get_memory_usage(self) -> Dict[str, float]:
        """獲取當前GPU內存使用情況"""
        if not GPU_AVAILABLE or not self.initialized:
            return {"error": "GPU不可用"}

        try:
            memory_pool = cp.get_default_memory_pool()
            used_bytes = memory_pool.used_bytes()
            total_bytes = memory_pool.total_bytes()

            return {
                "used_mb": used_bytes / (1024 * 1024),
                "total_mb": total_bytes / (1024 * 1024),
                "usage_ratio": used_bytes / total_bytes if total_bytes > 0 else 0.0
            }
        except Exception as e:
            return {"error": str(e)}

    def cleanup_gpu_memory(self):
        """清理GPU內存"""
        if GPU_AVAILABLE:
            try:
                cp.get_default_memory_pool().free_all_blocks()
                cp.fuse.clear_cache()
                logger.info("GPU內存已清理")
            except Exception as e:
                logger.error(f"GPU內存清理失敗: {e}")

class GPUPerformanceManager:
    """GPU性能管理器"""

    def __init__(self, safety_manager: GPUSafetyManager):
        self.safety_manager = safety_manager
        self.benchmark_data: List[GPUBenchmarkResult] = []

    def run_comprehensive_benchmark(self, data_size: int = 10000) -> Dict[str, GPUBenchmarkResult]:
        """運行綜合性能基準測試"""
        if not GPU_AVAILABLE or not self.safety_manager.initialized:
            logger.warning("GPU不可用，跳過基準測試")
            return {}

        benchmarks = {}

        # 1. 向量運算基準
        benchmarks['vector_add'] = self._benchmark_vector_operations(data_size)

        # 2. 矩陣運算基準
        benchmarks['matrix_multiply'] = self._benchmark_matrix_operations(data_size // 10)

        # 3. 統計計算基準
        benchmarks['statistics'] = self._benchmark_statistics(data_size)

        # 4. 技術指標基準
        benchmarks['technical_indicators'] = self._benchmark_technical_indicators(data_size)

        # 保存結果
        self.benchmark_data.extend(benchmarks.values())

        return benchmarks

    def _benchmark_vector_operations(self, size: int) -> GPUBenchmarkResult:
        """向量運算基準測試"""
        try:
            # 生成測試數據
            np.random.seed(42)  # 確保可重複性
            a_cpu = np.random.random(size).astype(np.float32)
            b_cpu = np.random.random(size).astype(np.float32)

            # CPU基準
            start_time = time.time()
            c_cpu = a_cpu + b_cpu
            cpu_time = time.time() - start_time

            # GPU基準
            a_gpu = cp.asarray(a_cpu)
            b_gpu = cp.asarray(b_cpu)

            # 預熱
            c_gpu = a_gpu + b_gpu
            cp.cuda.Stream.null.synchronize()

            # 測試
            start_time = time.time()
            c_gpu = a_gpu + b_gpu
            cp.cuda.Stream.null.synchronize()
            gpu_time = time.time() - start_time

            # 內存使用
            memory_usage = self.safety_manager.get_memory_usage()

            return GPUBenchmarkResult(
                test_name="vector_add",
                cpu_time=cpu_time,
                gpu_time=gpu_time,
                speedup_ratio=cpu_time / gpu_time,
                memory_usage_mb=memory_usage.get("used_mb", 0),
                peak_memory_mb=memory_usage.get("total_mb", 0),
                success=True
            )

        except Exception as e:
            return GPUBenchmarkResult(
                test_name="vector_add",
                cpu_time=0, gpu_time=0, speedup_ratio=0,
                memory_usage_mb=0, peak_memory_mb=0,
                success=False, error_message=str(e)
            )

    def _benchmark_matrix_operations(self, size: int) -> GPUBenchmarkResult:
        """矩陣運算基準測試"""
        try:
            # 生成測試數據
            np.random.seed(42)
            a_cpu = np.random.random((size, size)).astype(np.float32)
            b_cpu = np.random.random((size, size)).astype(np.float32)

            # CPU基準
            start_time = time.time()
            c_cpu = np.dot(a_cpu, b_cpu)
            cpu_time = time.time() - start_time

            # GPU基準
            a_gpu = cp.asarray(a_cpu)
            b_gpu = cp.asarray(b_cpu)

            # 預熱
            c_gpu = cp.dot(a_gpu, b_gpu)
            cp.cuda.Stream.null.synchronize()

            # 測試
            start_time = time.time()
            c_gpu = cp.dot(a_gpu, b_gpu)
            cp.cuda.Stream.null.synchronize()
            gpu_time = time.time() - start_time

            # 內存使用
            memory_usage = self.safety_manager.get_memory_usage()

            return GPUBenchmarkResult(
                test_name="matrix_multiply",
                cpu_time=cpu_time,
                gpu_time=gpu_time,
                speedup_ratio=cpu_time / gpu_time,
                memory_usage_mb=memory_usage.get("used_mb", 0),
                peak_memory_mb=memory_usage.get("total_mb", 0),
                success=True
            )

        except Exception as e:
            return GPUBenchmarkResult(
                test_name="matrix_multiply",
                cpu_time=0, gpu_time=0, speedup_ratio=0,
                memory_usage_mb=0, peak_memory_mb=0,
                success=False, error_message=str(e)
            )

    def _benchmark_statistics(self, size: int) -> GPUBenchmarkResult:
        """統計計算基準測試"""
        try:
            # 生成測試數據
            np.random.seed(42)
            data_cpu = np.random.normal(100, 15, size).astype(np.float32)

            # CPU基準
            start_time = time.time()
            mean_cpu = np.mean(data_cpu)
            std_cpu = np.std(data_cpu)
            corr_cpu = np.corrcoef(data_cpu[:-1], data_cpu[1:])[0, 1]
            cpu_time = time.time() - start_time

            # GPU基準
            data_gpu = cp.asarray(data_cpu)

            # 預熱
            mean_gpu = cp.mean(data_gpu)
            std_gpu = cp.std(data_gpu)
            cp.cuda.Stream.null.synchronize()

            # 測試
            start_time = time.time()
            mean_gpu = cp.mean(data_gpu)
            std_gpu = cp.std(data_gpu)
            # 相關係數計算（簡化版）
            corr_gpu = cp.corrcoef(data_gpu[:-1], data_gpu[1:])[0, 1]
            cp.cuda.Stream.null.synchronize()
            gpu_time = time.time() - start_time

            # 內存使用
            memory_usage = self.safety_manager.get_memory_usage()

            return GPUBenchmarkResult(
                test_name="statistics",
                cpu_time=cpu_time,
                gpu_time=gpu_time,
                speedup_ratio=cpu_time / gpu_time,
                memory_usage_mb=memory_usage.get("used_mb", 0),
                peak_memory_mb=memory_usage.get("total_mb", 0),
                success=True
            )

        except Exception as e:
            return GPUBenchmarkResult(
                test_name="statistics",
                cpu_time=0, gpu_time=0, speedup_ratio=0,
                memory_usage_mb=0, peak_memory_mb=0,
                success=False, error_message=str(e)
            )

    def _benchmark_technical_indicators(self, size: int) -> GPUBenchmarkResult:
        """技術指標基準測試"""
        try:
            # 生成測試數據
            np.random.seed(42)
            prices_cpu = np.random.uniform(50, 150, size).astype(np.float32)

            # CPU基準 - RSI計算
            def calculate_rsi_cpu(prices, period=14):
                delta = np.diff(prices, prepend=prices[0])
                gain = np.where(delta > 0, delta, 0)
                loss = np.where(delta < 0, -delta, 0)
                avg_gain = np.convolve(gain, np.ones(period), mode='valid') / period
                avg_loss = np.convolve(loss, np.ones(period), mode='valid') / period
                rs = avg_gain / np.where(avg_loss == 0, 1e-10, avg_loss)
                rsi = 100 - (100 / (1 + rs))
                result = np.full(len(prices), 50.0)
                result[period:] = rsi
                return result

            start_time = time.time()
            rsi_cpu = calculate_rsi_cpu(prices_cpu)
            cpu_time = time.time() - start_time

            # GPU基準 - RSI計算
            prices_gpu = cp.asarray(prices_cpu)

            def calculate_rsi_gpu(prices, period=14):
                delta = cp.diff(prices, prepend=prices[:1])
                gain = cp.where(delta > 0, delta, 0.0)
                loss = cp.where(delta < 0, -delta, 0.0)
                avg_gain = self._calculate_moving_average_gpu(gain, period)
                avg_loss = self._calculate_moving_average_gpu(loss, period)
                rs = avg_gain / cp.where(avg_loss == 0, 1e-10, avg_loss)
                rsi = 100 - (100 / (1 + rs))
                rsi[:period] = 50.0
                return rsi

            def _calculate_moving_average_gpu(data_gpu, period):
                if period <= 1:
                    return data_gpu.copy()
                n = len(data_gpu)
                if n < period:
                    return cp.full(n, cp.mean(data_gpu), dtype=cp.float32)
                cumsum = cp.cumsum(data_gpu, dtype=cp.float32)
                result = cp.zeros_like(data_gpu, dtype=cp.float32)
                if n > period:
                    result[period:] = (cumsum[period:] - cumsum[:-period]) / period
                    result[:period] = cp.mean(data_gpu[:period])
                elif n == period:
                    result[:] = cp.mean(data_gpu)
                return result

            start_time = time.time()
            rsi_gpu = calculate_rsi_gpu(prices_gpu)
            cp.cuda.Stream.null.synchronize()
            gpu_time = time.time() - start_time

            # 內存使用
            memory_usage = self.safety_manager.get_memory_usage()

            return GPUBenchmarkResult(
                test_name="technical_indicators",
                cpu_time=cpu_time,
                gpu_time=gpu_time,
                speedup_ratio=cpu_time / gpu_time,
                memory_usage_mb=memory_usage.get("used_mb", 0),
                peak_memory_mb=memory_usage.get("total_mb", 0),
                success=True
            )

        except Exception as e:
            return GPUBenchmarkResult(
                test_name="technical_indicators",
                cpu_time=0, gpu_time=0, speedup_ratio=0,
                memory_usage_mb=0, peak_memory_mb=0,
                success=False, error_message=str(e)
            )

    def generate_performance_report(self) -> Dict[str, Any]:
        """生成性能報告"""
        if not self.benchmark_data:
            return {"error": "無基準測試數據"}

        successful_tests = [b for b in self.benchmark_data if b.success]
        failed_tests = [b for b in self.benchmark_data if not b.success]

        if not successful_tests:
            return {"error": "所有基準測試均失敗"}

        # 計算平均加速比
        avg_speedup = np.mean([b.speedup_ratio for b in successful_tests])
        max_speedup = max([b.speedup_ratio for b in successful_tests])
        min_speedup = min([b.speedup_ratio for b in successful_tests])

        # 內存使用統計
        avg_memory = np.mean([b.memory_usage_mb for b in successful_tests])
        peak_memory = max([b.peak_memory_mb for b in successful_tests])

        return {
            "summary": {
                "total_tests": len(self.benchmark_data),
                "successful_tests": len(successful_tests),
                "failed_tests": len(failed_tests),
                "success_rate": len(successful_tests) / len(self.benchmark_data),
                "average_speedup": round(avg_speedup, 2),
                "max_speedup": round(max_speedup, 2),
                "min_speedup": round(min_speedup, 2)
            },
            "memory_usage": {
                "average_mb": round(avg_memory, 2),
                "peak_mb": round(peak_memory, 2)
            },
            "test_results": [
                {
                    "name": b.test_name,
                    "speedup": round(b.speedup_ratio, 2),
                    "cpu_time": round(b.cpu_time, 4),
                    "gpu_time": round(b.gpu_time, 4),
                    "memory_mb": round(b.memory_usage_mb, 2),
                    "success": b.success
                } for b in successful_tests
            ],
            "failed_tests": [
                {
                    "name": b.test_name,
                    "error": b.error_message
                } for b in failed_tests
            ],
            "recommendations": self._generate_recommendations(successful_tests, avg_speedup)
        }

    def _generate_recommendations(self, successful_tests: List[GPUBenchmarkResult], avg_speedup: float) -> List[str]:
        """生成性能優化建議"""
        recommendations = []

        if avg_speedup < 2.0:
            recommendations.append("GPU加速效果不明顯，建議檢查GPU驅動和CUDA版本")

        if any(b.memory_usage_mb > 1000 for b in successful_tests):
            recommendations.append("GPU內存使用較高，建議優化數據批次大小")

        failed_count = len([b for b in self.benchmark_data if not b.success])
        if failed_count > 0:
            recommendations.append(f"有{failed_count}個測試失敗，建議檢查GPU環境配置")

        if avg_speedup > 5.0:
            recommendations.append("GPU加速效果顯著，建議在生產環境中啟用")

        return recommendations

class GPUAccelerationManager:
    """GPU加速管理器 - 主要接口類"""

    def __init__(self, config_path: str = "config/gpu_config.json"):
        self.config_path = Path(config_path)
        self.config = self._load_config()

        # 初始化管理器
        self.safety_manager = GPUSafetyManager(self.config.get("safety"))
        self.performance_manager = GPUPerformanceManager(self.safety_manager)

        # 狀態標誌
        self.gpu_enabled = False
        self.initialized = False

        logger.info("GPU加速管理器初始化完成")

    def _load_config(self) -> Dict[str, Any]:
        """加載配置"""
        default_config = {
            "safety": {
                "max_gpu_memory_usage": 0.8,
                "max_gpu_temperature": 85.0,
                "enable_memory_check": True,
                "enable_temperature_check": True,
                "enable_driver_validation": True,
                "auto_fallback_to_cpu": True,
                "performance_monitoring": True
            },
            "performance": {
                "auto_benchmark": True,
                "benchmark_data_size": 10000,
                "enable_profiling": False
            },
            "optimization": {
                "auto_select_mode": True,
                "prefer_gpu": True,
                "min_speedup_threshold": 1.5
            }
        }

        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                # 合併配置
                for key in default_config:
                    if key in user_config:
                        default_config[key].update(user_config[key])
            except Exception as e:
                logger.error(f"加載GPU配置失敗，使用默認配置: {e}")

        return default_config

    def initialize(self) -> bool:
        """初始化GPU加速系統"""
        logger.info("正在初始化GPU加速系統...")

        try:
            # 1. 依賴檢查
            if not GPU_AVAILABLE:
                logger.warning("CuPy不可用，無法啟用GPU加速")
                return False

            # 2. 安全初始化
            if not self.safety_manager.initialize_gpu_environment():
                logger.error("GPU環境安全檢查失敗")
                return False

            # 3. 性能基準測試
            if self.config.get("performance", {}).get("auto_benchmark", True):
                benchmark_size = self.config.get("performance", {}).get("benchmark_data_size", 10000)
                self.performance_manager.run_comprehensive_benchmark(benchmark_size)

            self.gpu_enabled = True
            self.initialized = True
            logger.info("GPU加速系統初始化成功")
            return True

        except Exception as e:
            logger.error(f"GPU加速系統初始化失敗: {e}")
            return False

    def get_acceleration_status(self) -> Dict[str, Any]:
        """獲取加速狀態"""
        if not self.initialized:
            return {
                "status": "uninitialized",
                "message": "系統未初始化",
                "gpu_available": GPU_AVAILABLE,
                "safety_check_passed": False,
                "performance_profile": None,
                "memory_usage": {"error": "Not initialized"}
            }

        status = {
            "status": "enabled" if self.gpu_enabled else "disabled",
            "gpu_available": GPU_AVAILABLE,
            "safety_check_passed": self.safety_manager.initialized,
            "performance_profile": None,
            "memory_usage": self.safety_manager.get_memory_usage()
        }

        if self.safety_manager.performance_profile:
            status["performance_profile"] = {
                "device_name": self.safety_manager.performance_profile.device_name,
                "memory_total_mb": self.safety_manager.performance_profile.memory_total,
                "memory_available_mb": self.safety_manager.performance_profile.memory_available,
                "compute_capability": self.safety_manager.performance_profile.compute_capability,
                "multiprocessor_count": self.safety_manager.performance_profile.multiprocessor_count
            }

        return status

    def get_performance_report(self) -> Dict[str, Any]:
        """獲取性能報告"""
        if not self.initialized or not self.performance_manager.benchmark_data:
            return {"error": "無性能數據"}

        return self.performance_manager.generate_performance_report()

    def should_use_gpu(self, task_size: int, min_speedup_threshold: float = None) -> bool:
        """智能判斷是否應該使用GPU"""
        if not self.initialized or not self.gpu_enabled:
            return False

        # 配置閾值
        threshold = min_speedup_threshold or self.config.get("optimization", {}).get("min_speedup_threshold", 1.5)

        # 基於任務大小的決策
        if task_size < 1000:
            logger.debug("任務規模過小，使用CPU")
            return False

        # 基於歷史性能的決策
        if self.performance_manager.benchmark_data:
            avg_speedup = np.mean([b.speedup_ratio for b in self.performance_manager.benchmark_data if b.success])
            if avg_speedup < threshold:
                logger.debug(f"GPU加速效果不足 ({avg_speedup:.2f}x < {threshold}x)，使用CPU")
                return False

        return True

    def cleanup(self):
        """清理資源"""
        logger.info("正在清理GPU加速資源...")

        try:
            # 清理GPU內存
            self.safety_manager.cleanup_gpu_memory()

            # 重置狀態
            self.gpu_enabled = False
            self.initialized = False

            logger.info("GPU加速資源清理完成")

        except Exception as e:
            logger.error(f"GPU資源清理失敗: {e}")

    def save_config(self):
        """保存配置"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logger.info(f"GPU配置已保存到: {self.config_path}")
        except Exception as e:
            logger.error(f"保存GPU配置失敗: {e}")

# 全局實例
_gpu_acceleration_manager: Optional[GPUAccelerationManager] = None

def get_gpu_acceleration_manager() -> GPUAccelerationManager:
    """獲取全局GPU加速管理器實例"""
    global _gpu_acceleration_manager
    if _gpu_acceleration_manager is None:
        _gpu_acceleration_manager = GPUAccelerationManager()
    return _gpu_acceleration_manager

def initialize_gpu_acceleration() -> bool:
    """初始化GPU加速（便捷函數）"""
    manager = get_gpu_acceleration_manager()
    return manager.initialize()

def cleanup_gpu_acceleration():
    """清理GPU加速（便捷函數）"""
    manager = get_gpu_acceleration_manager()
    manager.cleanup()