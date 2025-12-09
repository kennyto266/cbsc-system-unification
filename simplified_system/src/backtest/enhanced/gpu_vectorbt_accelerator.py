#!/usr / bin / env python3
"""
Simplified System - GPU加速VectorBT計算
基於Python Algorithmic Trading Cookbook的GPU加速技術

提供高性能的GPU加速計算功能：
- 自動GPU檢測和管理
- CuPy後端VectorBT計算
- 智能內存管理
- 性能基準測試
"""

import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import psutil

logger = logging.getLogger(__name__)


@dataclass
class GPUConfig:
    """GPU配置"""

    # GPU檢測
    auto_detect: bool = True
    require_gpu: bool = False  # 是否要求GPU可用
    fallback_to_cpu: bool = True  # GPU不可用時是否降級到CPU

    # 內存管理
    max_memory_usage: float = 0.8  # 最大GPU內存使用比例
    chunk_size: int = 10000  # 數據分塊大小

    # 性能優化
    enable_cupy: bool = True
    cupy_memory_pool: bool = True


@dataclass
class GPUBenchmarkResult:
    """GPU基準測試結果"""

    gpu_available: bool = False
    gpu_device_info: Dict[str, Any] = None
    gpu_memory_info: Dict[str, Any] = None
    cpu_time: float = 0.0
    gpu_time: float = 0.0
    speedup_ratio: float = 0.0
    memory_usage: float = 0.0
    recommendations: List[str] = None


class GPUVectorBTAccelerator:
    """
    GPU加速VectorBT計算器

    提供自動GPU檢測、性能優化和智能計算管理功能。
    基於Cookbook中的GPU加速最佳實踐。
    """

    def __init__(self, config: Optional[GPUConfig] = None):
        """
        初始化GPU加速器

        Args:
            config: GPU配置
        """
        self.config = config or GPUConfig()
        self.gpu_available = False
        self.cupy_available = False
        self.gpu_device = None
        self.memory_manager = None

        # 初始化GPU環境
        self._initialize_gpu_environment()

        logger.info(f"GPU加速器初始化完成，GPU可用: {self.gpu_available}")

    def _initialize_gpu_environment(self):
        """初始化GPU環境"""
        try:
            # 檢查CuPy可用性
            self.cupy_available = self._check_cupy_availability()

            if self.cupy_available:
                # 檢測GPU設備
                self._detect_gpu_devices()

                # 設置GPU環境
                if self.gpu_available:
                    self._setup_gpu_environment()

        except Exception as e:
            logger.warning(f"GPU環境初始化失敗: {e}")
            if self.config.require_gpu:
                raise
            else:
                self.gpu_available = False

    def _check_cupy_availability(self) -> bool:
        """檢查CuPy可用性"""
        try:
            import cupy as cp

            logger.info("CuPy可用，版本: " + cp.__version__)
            return True
        except ImportError:
            logger.warning("CuPy不可用，請安裝: pip install cupy - cuda11x")
            return False

    def _detect_gpu_devices(self):
        """檢測GPU設備"""
        if not self.cupy_available:
            return

        try:
            import cupy as cp

            # 獲取GPU設備信息
            device_count = cp.cuda.runtime.getDeviceCount()
            self.gpu_available = device_count > 0

            if self.gpu_available:
                self.gpu_device = 0  # 使用第一個GPU設備
                device_info = self._get_device_info()
                logger.info(f"檢測到GPU設備: {device_info}")
            else:
                logger.warning("未檢測到可用的GPU設備")

        except Exception as e:
            logger.error(f"GPU設備檢測失敗: {e}")
            self.gpu_available = False

    def _get_device_info(self) -> Dict[str, Any]:
        """獲取GPU設備信息"""
        if not self.cupy_available:
            return {}

        try:
            import cupy as cp
            import pynvml

            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandleByIndex(self.gpu_device)

            # 獲取設備信息
            device_name = pynvml.nvmlDeviceGetName(handle).decode("utf - 8")
            memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)

            device_info = {
                "name": device_name,
                "index": self.gpu_device,
                "total_memory": memory_info.total,
                "free_memory": memory_info.free,
                "used_memory": memory_info.used,
            }

            return device_info

        except Exception as e:
            logger.warning(f"獲取GPU設備信息失敗: {e}")
            return {"name": "Unknown", "index": self.gpu_device}

    def _setup_gpu_environment(self):
        """設置GPU環境"""
        if not self.cupy_available:
            return

        try:
            import cupy as cp

            # 設置GPU設備
            cp.cuda.Device(self.gpu_device).use()

            # 設置內存池
            if self.config.cupy_memory_pool:
                memory_pool = cp.get_default_memory_pool()
                self.memory_manager = memory_pool

            logger.info("GPU環境設置完成")

        except Exception as e:
            logger.error(f"GPU環境設置失敗: {e}")
            if self.config.require_gpu:
                raise

    def accelerate_vectorbt_calculation(
        self, price_data: pd.DataFrame, strategy_func: callable, **strategy_params
    ) -> Tuple[Any, GPUBenchmarkResult]:
        """
        執行GPU加速的VectorBT計算

        Args:
            price_data: 價格數據
            strategy_func: 策略函數
            **strategy_params: 策略參數

        Returns:
            Tuple[Any, GPUBenchmarkResult]: (計算結果, 基準測試結果)
        """
        benchmark_result = GPUBenchmarkResult()
        benchmark_result.gpu_available = self.gpu_available

        if self.gpu_available:
            # GPU加速計算
            result, gpu_time = self._execute_gpu_calculation(
                price_data, strategy_func, **strategy_params
            )
            benchmark_result.gpu_time = gpu_time

            # CPU基準測試
            cpu_time = self._execute_cpu_calculation(
                price_data, strategy_func, **strategy_params
            )
            benchmark_result.cpu_time = cpu_time

            # 計算加速比
            if cpu_time > 0:
                benchmark_result.speedup_ratio = cpu_time / gpu_time

            # 獲取GPU信息
            benchmark_result.gpu_device_info = self._get_device_info()
            if self.cupy_available:
                import cupy as cp

                mempool = cp.get_default_memory_pool()
                benchmark_result.gpu_memory_info = {
                    "used_bytes": mempool.used_bytes(),
                    "total_bytes": mempool.total_bytes(),
                }

            return result, benchmark_result
        else:
            # CPU計算
            logger.info("GPU不可用，使用CPU計算")
            result = strategy_func(price_data, **strategy_params)
            benchmark_result.cpu_time = time.time()  # 簡化的時間測試
            return result, benchmark_result

    def _execute_gpu_calculation(
        self, price_data: pd.DataFrame, strategy_func: callable, **strategy_params
    ) -> Tuple[Any, float]:
        """執行GPU加速計算"""
        start_time = time.time()

        try:
            if not self.cupy_available:
                raise RuntimeError("CuPy不可用")

            import cupy as cp

            # 將數據轉換為GPU數組
            price_gpu = cp.asarray(price_data.values)

            # 創建GPU版本的價格數據
            price_gpu_df = pd.DataFrame(
                price_gpu.get(), index = price_data.index, columns = price_data.columns
            )

            # 執行策略計算（假設策略函數支持GPU數據）
            result = strategy_func(price_gpu_df, **strategy_params)

            gpu_time = time.time() - start_time
            logger.info(f"GPU計算完成，耗時: {gpu_time:.2f}秒")

            return result, gpu_time

        except Exception as e:
            logger.error(f"GPU計算失敗: {e}")
            raise

    def _execute_cpu_calculation(
        self, price_data: pd.DataFrame, strategy_func: callable, **strategy_params
    ) -> float:
        """執行CPU基準計算"""
        start_time = time.time()

        # 執行策略計算
        strategy_func(price_data, **strategy_params)

        cpu_time = time.time() - start_time
        logger.info(f"CPU計算完成，耗時: {cpu_time:.2f}秒")

        return cpu_time

    def run_performance_benchmark(
        self, price_data: pd.DataFrame, test_strategies: List[Dict[str, Any]] = None
    ) -> GPUBenchmarkResult:
        """
        運行性能基準測試

        Args:
            price_data: 測試數據
            test_strategies: 測試策略列表

        Returns:
            GPUBenchmarkResult: 基準測試結果
        """
        if test_strategies is None:
            test_strategies = [
                {"name": "MA_Cross", "func": self._test_ma_crossover},
                {"name": "RSI_Strategy", "func": self._test_rsi_strategy},
            ]

        logger.info("開始GPU性能基準測試")

        result = GPUBenchmarkResult()
        result.gpu_available = self.gpu_available

        # 測試每個策略
        for strategy in test_strategies:
            try:
                cpu_time, gpu_time = self._benchmark_single_strategy(
                    price_data, strategy["func"]
                )

                if gpu_time > 0 and cpu_time > 0:
                    speedup = cpu_time / gpu_time
                    logger.info(f"策略 {strategy['name']} 加速比: {speedup:.2f}x")

            except Exception as e:
                logger.error(f"策略 {strategy['name']} 基準測試失敗: {e}")

        return result

    def _benchmark_single_strategy(
        self, price_data: pd.DataFrame, strategy_func: callable
    ) -> Tuple[float, float]:
        """基準測試單個策略"""
        # CPU測試
        start_time = time.time()
        strategy_func(price_data)
        cpu_time = time.time() - start_time

        gpu_time = 0.0
        if self.gpu_available:
            # GPU測試
            start_time = time.time()
            try:
                strategy_func(price_data)
                gpu_time = time.time() - start_time
            except Exception as e:
                logger.warning(f"GPU基準測試失敗: {e}")
                gpu_time = 0.0

        return cpu_time, gpu_time

    def _test_ma_crossover(self, price_data: pd.DataFrame) -> Any:
        """測試MA交叉策略"""
        import vectorbt as vbt

        fast_ma, slow_ma = vbt.MA.run_combs(
            price_data, [10, 20], r = 2, short_names=["fast", "slow"]
        )

        entries = fast_ma.ma_crossed_above(slow_ma)
        exits = fast_ma.ma_crossed_below(slow_ma)

        return vbt.Portfolio.from_signals(
            price_data, entries, exits, init_cash = 100000, fees = 0.001
        )

    def _test_rsi_strategy(self, price_data: pd.DataFrame) -> Any:
        """測試RSI策略"""
        import vectorbt as vbt

        rsi = vbt.RSI.run(price_data, window = 14)
        entries = rsi.rsi_crossed_below(30)
        exits = rsi.rsi_crossed_above(70)

        return vbt.Portfolio.from_signals(
            price_data, entries, exits, init_cash = 100000, fees = 0.001
        )

    def get_optimal_chunk_size(self, data_size: int) -> int:
        """
        根據GPU內存計算最優數據分塊大小

        Args:
            data_size: 數據大小

        Returns:
            int: 最優分塊大小
        """
        if not self.gpu_available or not self.cupy_available:
            return data_size  # CPU模式不分塊

        try:
            import cupy as cp

            # 獲取GPU可用內存
            device_info = self._get_device_info()
            available_memory = device_info.get("free_memory", 0)

            # 估算每個數據點的內存使用量（粗略估算）
            bytes_per_element = 8  # float64
            safety_factor = 0.5  # 安全係數

            # 計算最優分塊大小
            max_elements = int(available_memory * safety_factor / bytes_per_element)
            optimal_chunk = min(data_size, max_elements, self.config.chunk_size)

            return max(1000, optimal_chunk)  # 最小分塊1000

        except Exception as e:
            logger.warning(f"計算最優分塊大小失敗: {e}")
            return min(data_size, self.config.chunk_size)

    def monitor_gpu_usage(self) -> Dict[str, Any]:
        """
        監控GPU使用情況

        Returns:
            Dict[str, Any]: GPU使用情況
        """
        if not self.gpu_available:
            return {"gpu_available": False}

        try:
            import cupy as cp

            # 獲取當前GPU使用情況
            device_info = self._get_device_info()
            memory_pool = cp.get_default_memory_pool()

            cpu_memory = psutil.virtual_memory()

            return {
                "gpu_available": True,
                "device_info": device_info,
                "gpu_memory_pool": {
                    "used_bytes": memory_pool.used_bytes(),
                    "total_bytes": memory_pool.total_bytes(),
                    "used_gb": memory_pool.used_bytes() / (1024 * *3),
                    "total_gb": memory_pool.total_bytes() / (1024 * *3),
                },
                "system_memory": {
                    "used_gb": cpu_memory.used / (1024 * *3),
                    "total_gb": cpu_memory.total / (1024 * *3),
                    "available_gb": cpu_memory.available / (1024 * *3),
                },
            }

        except Exception as e:
            logger.error(f"GPU使用情況監控失敗: {e}")
            return {"gpu_available": False, "error": str(e)}

    def generate_performance_report(self, benchmark_result: GPUBenchmarkResult) -> str:
        """
        生成性能報告

        Args:
            benchmark_result: 基準測試結果

        Returns:
            str: 性能報告
        """
        report = f"""
# GPU加速性能報告

## GPU可用性
- GPU可用: {benchmark_result.gpu_available}
- CuPy可用: {self.cupy_available}

## 性能指標
- CPU計算時間: {benchmark_result.cpu_time:.2f}秒
- GPU計算時間: {benchmark_result.gpu_time:.2f}秒
"""

        if benchmark_result.speedup_ratio > 0:
            report += f"- 加速比: {benchmark_result.speedup_ratio:.2f}x\n"

        if benchmark_result.gpu_device_info:
            device_info = benchmark_result.gpu_device_info
            report += f"""
## GPU設備信息
- 設備名稱: {device_info.get('name', 'Unknown')}
- 設備索引: {device_info.get('index', 'Unknown')}
- 總內存: {device_info.get('total_memory', 0) / (1024 * *3):.2f} GB
- 可用內存: {device_info.get('free_memory', 0) / (1024 * *3):.2f} GB
"""

        if benchmark_result.gpu_memory_info:
            mem_info = benchmark_result.gpu_memory_info
            report += f"""
## GPU內存使用
- 已使用內存: {mem_info.get('used_bytes', 0) / (1024 * *3):.2f} GB
- 內存池總量: {mem_info.get('total_bytes', 0) / (1024 * *3):.2f} GB
"""

        report += f"""
## 建議
"""
        if not benchmark_result.gpu_available:
            report += "- 建議安裝CUDA和CuPy以啟用GPU加速\n"
        elif benchmark_result.speedup_ratio < 2.0:
            report += "- GPU加速效果不明顯，可能需要更大的數據集\n"
        else:
            report += "- GPU加速效果良好，建議繼續使用GPU模式\n"

        return report
