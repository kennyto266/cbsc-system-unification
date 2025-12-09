#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPU檢測和環境配置模塊 - 增強版，專門針對非價格數據處理
自動檢測GPU可用性並配置計算後端
"""

import os
import logging
import platform
import subprocess
from typing import Dict, Any, Optional

# Configure logging
logger = logging.getLogger(__name__)

class GPUEnvironment:
    """GPU環境檢測和配置類 - 增強版"""

    def __init__(self):
        self.cupy_available = False
        self.cuda_available = False
        self.gpu_memory_gb = 0
        self.gpu_count = 0
        self.fallback_enabled = True
        self.backend = 'cpu'

        # 增強的GPU信息
        self.cuda_version = None
        self.driver_version = None
        self.gpu_name = None
        self.compute_capability = None
        self.gpu_bandwidth_gbps = 0
        self.cuda_cores = 0

        # 非價格數據處理相關
        self.nonprice_optimization_ready = False
        self.memory_efficiency_score = 0
        self.parallel_capability_score = 0

        self._detect_environment()
        self._assess_nonprice_capability()

    def _detect_environment(self) -> None:
        """檢測GPU環境"""
        # 檢查CuPy可用性
        self.cupy_available = self._check_cupy()

        # 檢查CUDA驅動
        self.cuda_available = self._check_cuda()

        # 獲取GPU信息
        if self.cupy_available and self.cuda_available:
            self._get_gpu_info()

        # 確定後端
        self.backend = self.get_compute_backend()

        # 記錄檢測結果
        self._log_detection_results()

    def _check_cupy(self) -> bool:
        """檢查CuPy是否可用"""
        try:
            import cupy
            logger.info(f"CuPy version: {cupy.__version__}")
            return True
        except ImportError:
            logger.info("CuPy not installed. GPU acceleration unavailable.")
            return False
        except Exception as e:
            logger.warning(f"CuPy import error: {e}")
            return False

    def _check_cuda(self) -> bool:
        """檢查CUDA驅動是否可用"""
        if not self.cupy_available:
            return False

        try:
            import cupy as cp
            device_count = cp.cuda.runtime.getDeviceCount()
            return device_count > 0
        except Exception as e:
            logger.warning(f"CUDA detection failed: {e}")
            return False

    def _get_gpu_info(self) -> None:
        """獲取GPU詳細信息 - 增強版"""
        if not self.cupy_available or not self.cuda_available:
            return

        try:
            import cupy as cp
            self.gpu_count = cp.cuda.runtime.getDeviceCount()

            if self.gpu_count > 0:
                # 獲取第一個GPU的信息
                device = 0
                cp.cuda.Device(device).use()

                # 獲取GPU屬性
                gpu_device = cp.cuda.Device(device)
                device_props = gpu_device.attributes

                if hasattr(device_props, 'TotalGlobalMem'):
                    self.gpu_memory_gb = device_props['TotalGlobalMem'] / (1024**3)

                # 獲取更詳細的GPU信息
                try:
                    # GPU名稱
                    if hasattr(gpu_device, 'name'):
                        self.gpu_name = gpu_device.name.decode('utf-8') if isinstance(gpu_device.name, bytes) else str(gpu_device.name)

                    # 計算能力
                    if hasattr(device_props, 'ComputeCapability'):
                        self.compute_capability = f"{device_props['ComputeCapabilityMajor']}.{device_props['ComputeCapabilityMinor']}"

                    # CUDA核心數（估算）
                    if hasattr(device_props, 'MultiprocessorCount'):
                        sm_count = device_props['MultiprocessorCount']
                        # 根據GPU架構估算核心數
                        if self.compute_capability:
                            major = int(self.compute_capability.split('.')[0])
                            if major >= 8:  # RTX 30系列+
                                cores_per_sm = 128
                            elif major >= 7:  # RTX 20系列
                                cores_per_sm = 64
                            elif major >= 6:  # GTX 10系列
                                cores_per_sm = 128
                            else:
                                cores_per_sm = 64
                            self.cuda_cores = sm_count * cores_per_sm

                    # 內存帶寬（估算）
                    if self.gpu_name:
                        if 'RTX 4090' in self.gpu_name:
                            self.gpu_bandwidth_gbps = 1008
                        elif 'RTX 4080' in self.gpu_name:
                            self.gpu_bandwidth_gbps = 716
                        elif 'RTX 4070' in self.gpu_name:
                            self.gpu_bandwidth_gbps = 504
                        elif 'RTX 3090' in self.gpu_name:
                            self.gpu_bandwidth_gbps = 936
                        elif 'RTX 3080' in self.gpu_name:
                            self.gpu_bandwidth_gbps = 760
                        elif 'RTX 3070' in self.gpu_name:
                            self.gpu_bandwidth_gbps = 448

                except Exception as e:
                    logger.debug(f"Failed to get detailed GPU info: {e}")

                # 獲取CUDA版本信息
                try:
                    self.cuda_version = cp.cuda.runtime.runtimeGetVersion()
                except:
                    pass

                logger.info(f"GPU devices detected: {self.gpu_count}")
                logger.info(f"GPU {device}: {self.gpu_name}, Memory: {self.gpu_memory_gb:.1f} GB")
                logger.info(f"Compute Capability: {self.compute_capability}, CUDA Cores: {self.cuda_cores}")
                logger.info(f"Memory Bandwidth: {self.gpu_bandwidth_gbps} GB/s")

        except Exception as e:
            logger.warning(f"Failed to get GPU info: {e}")
            self.gpu_count = 0
            self.gpu_memory_gb = 0

    def _assess_nonprice_capability(self) -> None:
        """評估非價格數據處理能力"""
        if not self.is_gpu_available():
            self.nonprice_optimization_ready = False
            return

        # 評估內存效率
        if self.gpu_memory_gb >= 8:
            self.memory_efficiency_score = 100
        elif self.gpu_memory_gb >= 6:
            self.memory_efficiency_score = 75
        elif self.gpu_memory_gb >= 4:
            self.memory_efficiency_score = 50
        else:
            self.memory_efficiency_score = 25

        # 評估並行處理能力
        if self.cuda_cores >= 10000:
            self.parallel_capability_score = 100
        elif self.cuda_cores >= 5000:
            self.parallel_capability_score = 75
        elif self.cuda_cores >= 2000:
            self.parallel_capability_score = 50
        elif self.cuda_cores > 0:
            self.parallel_capability_score = 25
        else:
            self.parallel_capability_score = 0

        # 綜合評估
        avg_score = (self.memory_efficiency_score + self.parallel_capability_score) / 2
        self.nonprice_optimization_ready = avg_score >= 50

        if self.nonprice_optimization_ready:
            logger.info(f"GPU ready for non-price optimization (score: {avg_score:.1f})")
        else:
            logger.info(f"GPU not optimal for non-price optimization (score: {avg_score:.1f})")

    def _log_detection_results(self) -> None:
        """記錄檢測結果"""
        logger.info("=== GPU Environment Detection ===")
        logger.info(f"CuPy available: {self.cupy_available}")
        logger.info(f"CUDA available: {self.cuda_available}")
        logger.info(f"GPU count: {self.gpu_count}")
        logger.info(f"GPU memory: {self.gpu_memory_gb:.1f} GB")
        logger.info(f"Compute backend: {self.backend}")
        logger.info(f"Fallback enabled: {self.fallback_enabled}")
        logger.info("================================")

    def get_compute_backend(self) -> str:
        """獲取計算後端"""
        if self.cupy_available and self.cuda_available and self.gpu_count > 0:
            return 'gpu'
        return 'cpu'

    def is_gpu_available(self) -> bool:
        """檢查GPU是否可用"""
        return self.backend == 'gpu'

    def get_system_info(self) -> Dict[str, Any]:
        """獲取系統信息字典 - 增強版"""
        return {
            # 基礎信息
            'cupy_available': self.cupy_available,
            'cuda_available': self.cuda_available,
            'gpu_count': self.gpu_count,
            'gpu_memory_gb': self.gpu_memory_gb,
            'backend': self.backend,
            'fallback_enabled': self.fallback_enabled,
            'gpu_acceleration_possible': self.is_gpu_available(),

            # 增強的GPU信息
            'gpu_name': self.gpu_name,
            'compute_capability': self.compute_capability,
            'cuda_cores': self.cuda_cores,
            'gpu_bandwidth_gbps': self.gpu_bandwidth_gbps,
            'cuda_version': self.cuda_version,

            # 非價格數據處理能力
            'nonprice_optimization_ready': self.nonprice_optimization_ready,
            'memory_efficiency_score': self.memory_efficiency_score,
            'parallel_capability_score': self.parallel_capability_score,

            # 系統環境
            'platform': platform.system(),
            'python_version': platform.python_version(),
        }

    def is_ready_for_nonprice_optimization(self) -> bool:
        """檢查是否準備好進行非價格數據優化"""
        return self.nonprice_optimization_ready and self.is_gpu_available()

    def get_gpu_optimization_recommendations(self) -> Dict[str, Any]:
        """獲取GPU優化建議"""
        recommendations = {
            'recommended': False,
            'reasons': [],
            'batch_size_suggestion': 1000,
            'memory_limit_gb': 1.0,
            'parallel_streams': 1
        }

        if not self.is_gpu_available():
            recommendations['reasons'].append("GPU not available")
            return recommendations

        if not self.nonprice_optimization_ready:
            recommendations['reasons'].append("GPU not optimal for non-price processing")
            return recommendations

        # 根據GPU能力提供建議
        recommendations['recommended'] = True

        if self.gpu_memory_gb >= 12:
            recommendations['batch_size_suggestion'] = 50000
            recommendations['memory_limit_gb'] = 10.0
            recommendations['parallel_streams'] = 4
        elif self.gpu_memory_gb >= 8:
            recommendations['batch_size_suggestion'] = 25000
            recommendations['memory_limit_gb'] = 6.0
            recommendations['parallel_streams'] = 2
        elif self.gpu_memory_gb >= 6:
            recommendations['batch_size_suggestion'] = 15000
            recommendations['memory_limit_gb'] = 4.0
            recommendations['parallel_streams'] = 1
        else:
            recommendations['batch_size_suggestion'] = 5000
            recommendations['memory_limit_gb'] = 2.0
            recommendations['parallel_streams'] = 1

        if self.cuda_cores >= 8000:
            recommendations['parallel_streams'] = min(recommendations['parallel_streams'] + 2, 8)

        return recommendations

    def test_gpu_computation(self, size: int = 1000) -> Dict[str, Any]:
        """測試GPU計算能力"""
        test_results = {
            'gpu_test_passed': False,
            'cpu_time': 0.0,
            'gpu_time': 0.0,
            'speedup': 0.0,
            'error': None
        }

        if not self.is_gpu_available():
            test_results['error'] = 'GPU not available'
            return test_results

        try:
            import numpy as np
            import cupy as cp
            import time

            # 生成測試數據
            np.random.seed(42)
            data_cpu = np.random.random(size)

            # CPU測試
            start_time = time.time()
            result_cpu = np.sum(data_cpu * 2)
            cpu_time = time.time() - start_time

            # GPU測試
            data_gpu = cp.array(data_cpu)
            start_time = time.time()
            result_gpu = cp.sum(data_gpu * 2)
            cp.cuda.Stream.null.synchronize()  # 確保GPU計算完成
            gpu_time = time.time() - start_time

            # 驗證結果
            cpu_result = float(result_cpu)
            gpu_result = float(result_gpu)
            results_match = abs(cpu_result - gpu_result) < 1e-6

            if results_match:
                test_results.update({
                    'gpu_test_passed': True,
                    'cpu_time': cpu_time,
                    'gpu_time': gpu_time,
                    'speedup': cpu_time / gpu_time if gpu_time > 0 else 0,
                    'cpu_result': cpu_result,
                    'gpu_result': gpu_result
                })
                logger.info(f"GPU computation test passed. Speedup: {test_results['speedup']:.2f}x")
            else:
                test_results['error'] = f'Results mismatch: CPU={cpu_result}, GPU={gpu_result}'
                logger.warning(f"GPU computation test failed: {test_results['error']}")

        except Exception as e:
            test_results['error'] = str(e)
            logger.warning(f"GPU test error: {e}")

        return test_results

# 全局GPU環境實例
_gpu_env = None

def get_gpu_environment() -> GPUEnvironment:
    """獲取全局GPU環境實例"""
    global _gpu_env
    if _gpu_env is None:
        _gpu_env = GPUEnvironment()
    return _gpu_env

def is_gpu_available() -> bool:
    """檢查GPU是否可用（簡化接口）"""
    return get_gpu_environment().is_gpu_available()

def get_compute_backend() -> str:
    """獲取計算後端（簡化接口）"""
    return get_gpu_environment().get_compute_backend()

# 兼容性函數
def check_gpu_environment() -> Dict[str, Any]:
    """檢查GPU環境（兼容性接口）"""
    return get_gpu_environment().get_system_info()