#!/usr/bin/env python3
"""
GPU管理器 - 简化GPU检测和使用
GPU Manager - Simplified GPU detection and usage
"""

import os
import sys
import logging
import warnings
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class GPUEnvironment:
    """GPU环境信息"""
    is_available: bool = False
    gpu_count: int = 0
    gpu_name: str = "Unknown"
    cuda_version: str = "Not available"
    cudnn_version: str = "Not available"
    memory_gb: float = 0.0
    compute_capability: str = "Unknown"

class GPUDetector:
    """GPU检测器"""

    def __init__(self):
        self.env = self._detect_gpu_environment()

    def _detect_gpu_environment(self) -> GPUEnvironment:
        """检测GPU环境"""
        env = GPUEnvironment()

        try:
            # 检测CUDA
            cuda_info = self._detect_cuda()
            if cuda_info['available']:
                env.is_available = True
                env.cuda_version = cuda_info['version']
                env.gpu_count = cuda_info['gpu_count']
                env.gpu_name = cuda_info['gpu_name']
                env.memory_gb = cuda_info['memory_gb']

            # 检测cuDNN
            cudnn_info = self._detect_cudnn()
            if cudnn_info['available']:
                env.cudnn_version = cudnn_info['version']

            logger.info(f"GPU Environment detected: {env.gpu_count} GPUs, CUDA {env.cuda_version}")

        except Exception as e:
            logger.warning(f"GPU detection failed: {e}")
            logger.info("Falling back to CPU-only computation")

        return env

    def _detect_cuda(self) -> Dict[str, Any]:
        """检测CUDA"""
        try:
            # 尝试导入torch
            import torch

            if torch.cuda.is_available():
                return {
                    'available': True,
                    'version': torch.version.cuda,
                    'gpu_count': torch.cuda.device_count(),
                    'gpu_name': torch.cuda.get_device_name(0) if torch.cuda.device_count() > 0 else "Unknown",
                    'memory_gb': torch.cuda.get_device_properties(0).total_memory / 1e9 if torch.cuda.device_count() > 0 else 0
                }
            else:
                return {'available': False}

        except ImportError:
            pass

        try:
            # 尝试导入cupy
            import cupy as cp

            if cp.cuda.is_available():
                return {
                    'available': True,
                    'version': "Unknown",
                    'gpu_count': 1,
                    'gpu_name': "Unknown",
                    'memory_gb': cp.cuda.Device().mem_info[1] / 1e9
                }
            else:
                return {'available': False}

        except ImportError:
            pass

        # 检查nvidia-smi
        try:
            import subprocess
            result = subprocess.run(['nvidia-smi'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                # 解析nvidia-smi输出
                output = result.stdout
                if 'CUDA Version' in output:
                    version_line = [line for line in output.split('\n') if 'CUDA Version' in line][0]
                    version = version_line.split('CUDA Version: ')[1].split()[0]
                    return {'available': True, 'version': version}
        except:
            pass

        return {'available': False}

    def _detect_cudnn(self) -> Dict[str, Any]:
        """检测cuDNN"""
        try:
            import torch
            if torch.backends.cudnn.is_available():
                return {
                    'available': True,
                    'version': torch.backends.cudnn.version()
                }
        except:
            pass

        return {'available': False}

    def get_environment_info(self) -> Dict[str, Any]:
        """获取环境信息"""
        return {
            'gpu_available': self.env.is_available,
            'gpu_count': self.env.gpu_count,
            'gpu_name': self.env.gpu_name,
            'cuda_version': self.env.cuda_version,
            'cudnn_version': self.env.cudnn_version,
            'memory_gb': self.env.memory_gb,
            'system_info': self._get_system_info()
        }

    def _get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        import platform
        import psutil

        return {
            'platform': platform.system(),
            'platform_release': platform.release(),
            'platform_version': platform.version(),
            'cpu_count': os.cpu_count(),
            'memory_gb': psutil.virtual_memory().total / 1e9,
            'python_version': sys.version
        }

class GPUManager:
    """
    GPU管理器

    提供简化的GPU使用接口，自动回退到CPU
    """

    def __init__(self, auto_fallback: bool = True):
        self.detector = GPUDetector()
        self.env = self.detector.env
        self.auto_fallback = auto_fallback
        self.backend = None
        self._initialize_backend()

    def _initialize_backend(self):
        """初始化后端"""
        if not self.env.is_available:
            if self.auto_fallback:
                logger.info("GPU not available, using CPU backend")
                self.backend = CPUBackend()
            else:
                raise RuntimeError("GPU not available and auto_fallback is disabled")
            return

        # 尝试初始化GPU后端
        try:
            self.backend = self._create_gpu_backend()
            logger.info(f"GPU backend initialized: {self.backend.get_backend_info()}")
        except Exception as e:
            logger.warning(f"Failed to initialize GPU backend: {e}")
            if self.auto_fallback:
                logger.info("Falling back to CPU backend")
                self.backend = CPUBackend()
            else:
                raise

    def _create_gpu_backend(self):
        """创建GPU后端"""
        # 优先尝试PyTorch
        try:
            return PyTorchGPUBackend(self.env)
        except ImportError:
            pass

        # 尝试CuPy
        try:
            return CuPyGPUBackend(self.env)
        except ImportError:
            pass

        raise RuntimeError("No GPU backend available")

    def is_gpu_available(self) -> bool:
        """检查GPU是否可用"""
        return self.env.is_available

    def get_backend_info(self) -> Dict[str, Any]:
        """获取后端信息"""
        if self.backend:
            info = self.backend.get_backend_info()
            info.update({
                'gpu_environment': {
                    'available': self.env.is_available,
                    'gpu_count': self.env.gpu_count,
                    'gpu_name': self.env.gpu_name,
                    'cuda_version': self.env.cuda_version
                }
            })
            return info
        return {'error': 'No backend initialized'}

    def array(self, data, *args, **kwargs):
        """创建数组"""
        return self.backend.array(data, *args, **kwargs)

    def asarray(self, data, *args, **kwargs):
        """转换为数组"""
        return self.backend.asarray(data, *args, **kwargs)

    def compute_indicators(self, prices, indicators_config):
        """计算指标"""
        return self.backend.compute_indicators(prices, indicators_config)

class CPUBackend:
    """CPU后端（回退选项）"""

    def get_backend_info(self):
        return {
            'backend_type': 'CPU',
            'description': 'CPU-based computation backend',
            'acceleration': False
        }

    def array(self, data, *args, **kwargs):
        import numpy as np
        return np.array(data, *args, **kwargs)

    def asarray(self, data, *args, **kwargs):
        import numpy as np
        return np.asarray(data, *args, **kwargs)

    def compute_indicators(self, prices, indicators_config):
        """CPU指标计算"""
        import numpy as np
        import pandas as pd

        results = {}

        if 'rsi' in indicators_config:
            config = indicators_config['rsi']
            period = config.get('period', 14)
            results['RSI'] = self._calculate_rsi_cpu(prices, period)

        if 'macd' in indicators_config:
            config = indicators_config['macd']
            fast = config.get('fast', 12)
            slow = config.get('slow', 26)
            signal = config.get('signal', 9)
            macd_data = self._calculate_macd_cpu(prices, fast, slow, signal)
            results.update(macd_data)

        return results

    def _calculate_rsi_cpu(self, prices, period=14):
        """CPU RSI计算"""
        import numpy as np
        import pandas as pd

        if isinstance(prices, pd.Series):
            prices = prices.values

        delta = np.diff(prices, prepend=prices[0])
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)

        avg_gain = pd.Series(gain).rolling(window=period, min_periods=1).mean().values
        avg_loss = pd.Series(loss).rolling(window=period, min_periods=1).mean().values

        rs = avg_gain / np.where(avg_loss == 0, np.nan, avg_loss)
        rsi = 100 - (100 / (1 + rs))
        rsi = np.nan_to_num(rsi, nan=50.0)

        return rsi

    def _calculate_macd_cpu(self, prices, fast=12, slow=26, signal=9):
        """CPU MACD计算"""
        import pandas as pd

        if isinstance(prices, np.ndarray):
            prices = pd.Series(prices)

        ema_fast = prices.ewm(span=fast, adjust=False).mean()
        ema_slow = prices.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line

        return {
            'MACD': macd_line.values,
            'MACD_Signal': signal_line.values,
            'MACD_Histogram': histogram.values
        }

class PyTorchGPUBackend:
    """PyTorch GPU后端"""

    def __init__(self, env: GPUEnvironment):
        import torch
        self.torch = torch
        self.env = env
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    def get_backend_info(self):
        return {
            'backend_type': 'PyTorch GPU',
            'device': str(self.device),
            'torch_version': self.torch.__version__,
            'cuda_available': self.torch.cuda.is_available(),
            'acceleration': True
        }

    def array(self, data, *args, **kwargs):
        return self.torch.tensor(data, *args, **kwargs, device=self.device)

    def asarray(self, data, *args, **kwargs):
        if not isinstance(data, self.torch.Tensor):
            return self.torch.tensor(data, *args, **kwargs, device=self.device)
        return data.to(self.device)

    def compute_indicators(self, prices, indicators_config):
        """PyTorch GPU指标计算"""
        import torch

        # 转换为GPU张量
        if not isinstance(prices, torch.Tensor):
            prices_tensor = torch.tensor(prices, dtype=torch.float32, device=self.device)
        else:
            prices_tensor = prices.to(self.device)

        results = {}

        if 'rsi' in indicators_config:
            config = indicators_config['rsi']
            period = config.get('period', 14)
            results['RSI'] = self._calculate_rsi_torch(prices_tensor, period)

        if 'macd' in indicators_config:
            config = indicators_config['macd']
            fast = config.get('fast', 12)
            slow = config.get('slow', 26)
            signal = config.get('signal', 9)
            macd_data = self._calculate_macd_torch(prices_tensor, fast, slow, signal)
            results.update(macd_data)

        # 转换回CPU用于进一步处理
        for key in results:
            results[key] = results[key].cpu().numpy()

        return results

    def _calculate_rsi_torch(self, prices, period=14):
        """PyTorch GPU RSI计算"""
        delta = torch.diff(prices, prepend=prices[:1])
        gain = torch.where(delta > 0, delta, torch.tensor(0.0, device=self.device))
        loss = torch.where(delta < 0, -delta, torch.tensor(0.0, device=self.device))

        # 使用滑动窗口计算平均值
        avg_gain = torch.zeros_like(gain)
        avg_loss = torch.zeros_like(loss)

        for i in range(period):
            avg_gain[i] = gain[:i+1].mean()
            avg_loss[i] = loss[:i+1].mean()

        for i in range(period, len(gain)):
            avg_gain[i] = (avg_gain[i-1] * (period-1) + gain[i]) / period
            avg_loss[i] = (avg_loss[i-1] * (period-1) + loss[i]) / period

        rs = avg_gain / torch.where(avg_loss == 0, torch.tensor(float('nan'), device=self.device), avg_loss)
        rsi = 100 - (100 / (1 + rs))
        rsi = torch.nan_to_num(rsi, nan=50.0)

        return rsi

    def _calculate_macd_torch(self, prices, fast=12, slow=26, signal=9):
        """PyTorch GPU MACD计算"""
        # 使用指数加权移动平均
        def ema_torch(data, span):
            alpha = 2 / (span + 1)
            ema = torch.zeros_like(data)
            ema[0] = data[0]

            for i in range(1, len(data)):
                ema[i] = alpha * data[i] + (1 - alpha) * ema[i-1]

            return ema

        ema_fast = ema_torch(prices, fast)
        ema_slow = ema_torch(prices, slow)
        macd_line = ema_fast - ema_slow
        signal_line = ema_torch(macd_line, signal)
        histogram = macd_line - signal_line

        return {
            'MACD': macd_line,
            'MACD_Signal': signal_line,
            'MACD_Histogram': histogram
        }

class CuPyGPUBackend:
    """CuPy GPU后端"""

    def __init__(self, env: GPUEnvironment):
        import cupy as cp
        self.cp = cp
        self.env = env

    def get_backend_info(self):
        return {
            'backend_type': 'CuPy GPU',
            'cupy_version': self.cp.__version__,
            'device': f"{self.cp.cuda.runtime.getDeviceCount()} devices",
            'acceleration': True
        }

    def array(self, data, *args, **kwargs):
        return self.cp.array(data, *args, **kwargs)

    def asarray(self, data, *args, **kwargs):
        return self.cp.asarray(data, *args, **kwargs)

    def compute_indicators(self, prices, indicators_config):
        """CuPy GPU指标计算"""
        import cupy as cp

        # 转换为GPU数组
        if not isinstance(prices, cp.ndarray):
            prices_gpu = cp.asarray(prices, dtype=cp.float32)
        else:
            prices_gpu = prices

        results = {}

        if 'rsi' in indicators_config:
            config = indicators_config['rsi']
            period = config.get('period', 14)
            results['RSI'] = self._calculate_rsi_cupy(prices_gpu, period)

        if 'macd' in indicators_config:
            config = indicators_config['macd']
            fast = config.get('fast', 12)
            slow = config.get('slow', 26)
            signal = config.get('signal', 9)
            macd_data = self._calculate_macd_cupy(prices_gpu, fast, slow, signal)
            results.update(macd_data)

        # 转换回CPU用于进一步处理
        for key in results:
            results[key] = cp.asnumpy(results[key])

        return results

    def _calculate_rsi_cupy(self, prices, period=14):
        """CuPy GPU RSI计算"""
        import cupy as cp

        delta = cp.diff(prices, prepend=prices[:1])
        gain = cp.where(delta > 0, delta, 0.0)
        loss = cp.where(delta < 0, -delta, 0.0)

        # 使用滑动窗口计算平均值
        avg_gain = cp.zeros_like(gain)
        avg_loss = cp.zeros_like(loss)

        # 简化的EMA计算
        alpha = 1.0 / period
        avg_gain[period-1] = cp.mean(gain[:period])
        avg_loss[period-1] = cp.mean(loss[:period])

        for i in range(period, len(gain)):
            avg_gain[i] = alpha * gain[i] + (1 - alpha) * avg_gain[i-1]
            avg_loss[i] = alpha * loss[i] + (1 - alpha) * avg_loss[i-1]

        rs = avg_gain / cp.where(avg_loss == 0, cp.nan, avg_loss)
        rsi = 100 - (100 / (1 + rs))
        rsi = cp.nan_to_num(rsi, nan=50.0)

        return rsi

    def _calculate_macd_cupy(self, prices, fast=12, slow=26, signal=9):
        """CuPy GPU MACD计算"""
        import cupy as cp

        def ema_cupy(data, span):
            alpha = 2 / (span + 1)
            ema = cp.zeros_like(data)
            ema[0] = data[0]

            for i in range(1, len(data)):
                ema[i] = alpha * data[i] + (1 - alpha) * ema[i-1]

            return ema

        ema_fast = ema_cupy(prices, fast)
        ema_slow = ema_cupy(prices, slow)
        macd_line = ema_fast - ema_slow
        signal_line = ema_cupy(macd_line, signal)
        histogram = macd_line - signal_line

        return {
            'MACD': macd_line,
            'MACD_Signal': signal_line,
            'MACD_Histogram': histogram
        }

# 全局GPU管理器
_global_gpu_manager = None

def get_gpu_manager(auto_fallback: bool = True) -> GPUManager:
    """获取全局GPU管理器"""
    global _global_gpu_manager
    if _global_gpu_manager is None:
        _global_gpu_manager = GPUManager(auto_fallback=auto_fallback)
    return _global_gpu_manager

def get_gpu_environment() -> GPUEnvironment:
    """获取GPU环境信息"""
    detector = GPUDetector()
    return detector.env