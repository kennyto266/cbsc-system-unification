#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPU加速模塊 - 深度集成版本
GPU Acceleration Module - Deep Integration Version

提供完整的GPU加速功能，包括：
- 技術指標計算加速
- 參數優化加速
- 回測引擎加速
- 內存管理和性能監控
"""

from .gpu_accelerated_indicators import (
    GPUAcceleratedIndicators,
    GPUIndicatorConfig,
    GPUComputeStats,
    get_gpu_indicators,
    reset_gpu_indicators
)

from .gpu_parameter_optimizer import (
    GPUParameterOptimizer,
    OptimizationConfig,
    OptimizationResult,
    get_gpu_optimizer,
    reset_gpu_optimizer
)

from .gpu_backtest_engine import (
    GPUBacktestEngine,
    BacktestConfig,
    BacktestResult,
    get_gpu_backtest_engine,
    reset_gpu_backtest_engine
)

# 保留原有模塊導入（向後兼容）
try:
    from .nonprice_engine import (
        NonPriceGPUEngine,
        get_nonprice_gpu_engine
    )
except ImportError:
    NonPriceGPUEngine = None
    get_nonprice_gpu_engine = None

try:
    from .parameter_optimizer import (
        GPUParameterOptimizer as LegacyGPUParameterOptimizer,
        OptimizationConfig as LegacyOptimizationConfig,
        get_gpu_parameter_optimizer
    )
except ImportError:
    LegacyGPUParameterOptimizer = None
    LegacyOptimizationConfig = None
    get_gpu_parameter_optimizer = None

try:
    from .performance_monitor import (
        PerformanceMonitor,
        get_performance_monitor
    )
except ImportError:
    PerformanceMonitor = None
    get_performance_monitor = None

# 版本信息
__version__ = "2.1.0"
__author__ = "GPU Computing Team"

# GPU環境檢查
GPU_AVAILABLE = False
GPU_BACKEND = None
CUDA_VERSION = None

try:
    import cupy as cp
    GPU_AVAILABLE = True
    GPU_BACKEND = "cupy"
    CUDA_VERSION = cp.cuda.runtime.runtimeGetVersion()
except ImportError:
    try:
        import torch
        if torch.cuda.is_available():
            GPU_AVAILABLE = True
            GPU_BACKEND = "pytorch"
            CUDA_VERSION = torch.version.cuda
    except ImportError:
        pass

# 導出主要類和函數
__all__ = [
    # 新版本核心類
    'GPUAcceleratedIndicators',
    'GPUParameterOptimizer',
    'GPUBacktestEngine',

    # 新版本配置類
    'GPUIndicatorConfig',
    'OptimizationConfig',
    'BacktestConfig',

    # 新版本結果類
    'GPUComputeStats',
    'OptimizationResult',
    'BacktestResult',

    # 新版本便利函數
    'get_gpu_indicators',
    'get_gpu_optimizer',
    'get_gpu_backtest_engine',

    # 新版本重置函數
    'reset_gpu_indicators',
    'reset_gpu_optimizer',
    'reset_gpu_backtest_engine',

    # 環境信息
    'GPU_AVAILABLE',
    'GPU_BACKEND',
    'CUDA_VERSION',

    # 向後兼容的舊版本
    'NonPriceGPUEngine',
    'LegacyGPUParameterOptimizer',
    'LegacyOptimizationConfig',
    'get_nonprice_gpu_engine',
    'get_gpu_parameter_optimizer',
    'PerformanceMonitor',
    'get_performance_monitor'
]

def get_gpu_info() -> dict:
    """獲取GPU環境信息"""
    info = {
        'gpu_available': GPU_AVAILABLE,
        'backend': GPU_BACKEND,
        'cuda_version': CUDA_VERSION
    }

    if GPU_AVAILABLE:
        if GPU_BACKEND == "cupy":
            try:
                info['device_count'] = cp.cuda.runtime.getDeviceCount()
                if info['device_count'] > 0:
                    device = cp.cuda.Device()
                    mem_info = device.mem_info
                    info['current_device'] = {
                        'name': device.name.decode(),
                        'memory_total': mem_info[1],
                        'memory_free': mem_info[0],
                        'compute_capability': device.compute_capability
                    }
            except:
                pass

        elif GPU_BACKEND == "pytorch":
            try:
                info['device_count'] = torch.cuda.device_count()
                if info['device_count'] > 0:
                    current_device = torch.cuda.current_device()
                    props = torch.cuda.get_device_properties(current_device)
                    info['current_device'] = {
                        'name': props.name,
                        'memory_total': props.total_memory,
                        'memory_allocated': torch.cuda.memory_allocated(current_device),
                        'memory_reserved': torch.cuda.memory_reserved(current_device),
                        'compute_capability': f"{props.major}.{props.minor}"
                    }
            except:
                pass

    return info

def initialize_gpu_system():
    """初始化GPU系統"""
    if not GPU_AVAILABLE:
        print("⚠️  GPU不可用，系統將使用CPU模式")
        return False

    print(f"🚀 GPU加速系統初始化成功")
    print(f"   後端: {GPU_BACKEND}")
    print(f"   CUDA版本: {CUDA_VERSION}")

    gpu_info = get_gpu_info()
    if 'current_device' in gpu_info:
        device = gpu_info['current_device']
        print(f"   設備: {device['name']}")
        print(f"   計算能力: {device['compute_capability']}")
        if 'memory_total' in device:
            memory_gb = device['memory_total'] / (1024**3)
            print(f"   顯存: {memory_gb:.1f}GB")

    return True

# 模塊初始化時檢查GPU環境
if __name__ != "__main__":
    # 確保在導入時初始化GPU環境
    try:
        initialize_gpu_system()
    except Exception as e:
        print(f"⚠️  GPU系統初始化警告: {e}")

# 高級便利函數
def quick_gpu_rsi_optimization(data, symbol="UNKNOWN", periods=None):
    """快速GPU RSI優化"""
    optimizer = get_gpu_optimizer()

    if periods is None:
        periods = list(range(5, 51))

    param_ranges = {
        'period': periods,
        'oversold': [20, 25, 30, 35, 40],
        'overbought': [60, 65, 70, 75, 80]
    }

    return optimizer.optimize_rsi_strategy(data, symbol, param_ranges)

def quick_gpu_macd_optimization(data, symbol="UNKNOWN"):
    """快速GPU MACD優化"""
    optimizer = get_gpu_optimizer()
    return optimizer.optimize_macd_strategy(data, symbol)

def quick_gpu_backtest(data, strategy, params, symbol="UNKNOWN"):
    """快速GPU回測"""
    engine = get_gpu_backtest_engine()
    return engine.backtest_strategy(data, strategy, params, symbol)

def benchmark_gpu_performance(data_size=10000):
    """GPU性能基準測試"""
    indicators = get_gpu_indicators()
    return indicators.benchmark_performance(data_size)

# 高級便利函數導出
__all__.extend([
    'get_gpu_info',
    'initialize_gpu_system',
    'quick_gpu_rsi_optimization',
    'quick_gpu_macd_optimization',
    'quick_gpu_backtest',
    'benchmark_gpu_performance'
])