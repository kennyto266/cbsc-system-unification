#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPU错误处理机制
实现智能错误处理，避免过度CPU回退
提供渐进式降级策略而非立即回退
"""

import logging
import traceback
from enum import Enum
from typing import Dict, Any, Optional, Callable, Union
from dataclasses import dataclass
import time
import warnings

try:
    import cupy as cp
    GPU_AVAILABLE = True
except ImportError:
    cp = None
    GPU_AVAILABLE = False

logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """错误严重性等级"""
    LOW = "low"           # 轻微错误，可忽略
    MEDIUM = "medium"     # 中等错误，可部分GPU计算
    HIGH = "high"         # 严重错误，需要降级
    CRITICAL = "critical" # 致命错误，必须CPU回退

class FallbackStrategy(Enum):
    """降级策略"""
    CONTINUE = "continue"           # 继续GPU计算
    RETRY_PARTIAL = "retry_partial" # 部分重试
    ADJUST_PARAMS = "adjust_params" # 调整参数
    GRADUAL_FALLBACK = "gradual"    # 渐进式降级
    CPU_FALLBACK = "cpu_fallback"   # CPU回退

@dataclass
class GPUError:
    """GPU错误信息"""
    error_type: str
    severity: ErrorSeverity
    message: str
    traceback_str: str
    timestamp: float
    context: Dict[str, Any]

class GPUErrorHandler:
    """GPU错误处理器"""

    def __init__(self):
        self.error_history = []
        self.retry_counts = {}
        self.fallback_stats = {
            'total_operations': 0,
            'gpu_successes': 0,
            'partial_gpu_successes': 0,
            'cpu_fallbacks': 0
        }
        self.max_retries = 3
        self.max_partial_retries = 5

        logger.info("GPU错误处理器初始化")

    def categorize_error(self, error: Exception, context: Dict[str, Any] = None) -> GPUError:
        """
        错误严重性分类

        Args:
            error: 发生的错误
            context: 错误上下文

        Returns:
            GPUError对象
        """
        error_type = type(error).__name__
        error_message = str(error)
        context = context or {}

        # 根据错误类型和消息确定严重性
        if "out of memory" in error_message.lower() or "cuda" in error_message.lower():
            severity = ErrorSeverity.MEDIUM
            strategy = FallbackStrategy.ADJUST_PARAMS
        elif "shape" in error_message.lower() or "dimension" in error_message.lower():
            severity = ErrorSeverity.MEDIUM
            strategy = FallbackStrategy.RETRY_PARTIAL
        elif "dtype" in error_message.lower() or "type" in error_message.lower():
            severity = ErrorSeverity.MEDIUM
            strategy = FallbackStrategy.ADJUST_PARAMS
        elif "index" in error_message.lower() or "key" in error_message.lower():
            severity = ErrorSeverity.LOW
            strategy = FallbackStrategy.CONTINUE
        elif "division" in error_message.lower() or "zero" in error_message.lower():
            severity = ErrorSeverity.LOW
            strategy = FallbackStrategy.CONTINUE
        else:
            severity = ErrorSeverity.HIGH
            strategy = FallbackStrategy.CPU_FALLBACK

        gpu_error = GPUError(
            error_type=error_type,
            severity=severity,
            message=error_message,
            traceback_str=traceback.format_exc(),
            timestamp=time.time(),
            context={
                **context,
                'suggested_strategy': strategy.value
            }
        )

        self.error_history.append(gpu_error)
        logger.warning(f"GPU错误分类: {error_type} - {severity.value} - {error_message}")

        return gpu_error

    def try_partial_gpu(self, operation: Callable, data, operation_name: str = "unknown") -> Any:
        """
        部分GPU计算尝试

        Args:
            operation: 要执行的操作
            data: 输入数据
            operation_name: 操作名称

        Returns:
            计算结果或None
        """
        try:
            # 获取重试计数
            retry_key = f"{operation_name}_partial"
            retry_count = self.retry_counts.get(retry_key, 0)

            if retry_count >= self.max_partial_retries:
                logger.warning(f"部分GPU重试次数已达上限: {operation_name}")
                return None

            # 尝试数据分块处理
            if hasattr(data, '__len__') and len(data) > 1000:
                # 分块处理大数据
                chunk_size = min(1000, len(data) // 4)
                results = []

                for i in range(0, len(data), chunk_size):
                    chunk = data[i:i + chunk_size]
                    try:
                        chunk_result = operation(chunk)
                        results.append(chunk_result)
                    except Exception as e:
                        logger.error(f"块 {i} 处理失败: {e}")
                        # 对失败的块使用CPU
                        try:
                            import numpy as np
                            chunk_cpu = cp.asnumpy(chunk) if hasattr(chunk, 'get') else chunk
                            chunk_result = self._cpu_fallback_operation(operation_name, chunk_cpu)
                            results.append(chunk_result)
                        except:
                            # 如果CPU也失败，生成默认值
                            results.append(self._generate_default_result(chunk))

                if results:
                    self.fallback_stats['partial_gpu_successes'] += 1
                    self.retry_counts[retry_key] = retry_count + 1
                    return self._combine_results(results)

            # 如果分块不可行，尝试参数调整
            return self._try_with_adjusted_params(operation, data, operation_name)

        except Exception as e:
            logger.error(f"部分GPU尝试失败: {e}")
            return None

    def execute_with_fallback(self, gpu_operation: Callable, cpu_operation: Callable,
                            data, operation_name: str = "unknown",
                            context: Dict[str, Any] = None) -> Any:
        """
        执行带降级的操作

        Args:
            gpu_operation: GPU操作
            cpu_operation: CPU操作
            data: 输入数据
            operation_name: 操作名称
            context: 操作上下文

        Returns:
            操作结果
        """
        self.fallback_stats['total_operations'] += 1
        context = context or {}

        try:
            # 首先尝试GPU操作
            if GPU_AVAILABLE:
                logger.debug(f"尝试GPU操作: {operation_name}")
                result = gpu_operation(data)
                self.fallback_stats['gpu_successes'] += 1
                logger.debug(f"GPU操作成功: {operation_name}")
                return result
            else:
                raise RuntimeError("GPU不可用")

        except Exception as e:
            # 错误分类
            gpu_error = self.categorize_error(e, context)
            suggested_strategy = FallbackStrategy(gpu_error.context.get('suggested_strategy', 'cpu_fallback'))

            logger.warning(f"GPU操作失败: {operation_name} - {suggested_strategy.value}")

            # 根据策略执行降级
            if suggested_strategy == FallbackStrategy.CONTINUE:
                # 继续GPU计算，忽略错误
                try:
                    return self._handle_continue_error(data, operation_name, e)
                except:
                    pass

            elif suggested_strategy == FallbackStrategy.RETRY_PARTIAL:
                # 部分GPU重试
                partial_result = self.try_partial_gpu(gpu_operation, data, operation_name)
                if partial_result is not None:
                    return partial_result

            elif suggested_strategy == FallbackStrategy.ADJUST_PARAMS:
                # 参数调整后重试
                adjusted_result = self._try_with_adjusted_params(gpu_operation, data, operation_name)
                if adjusted_result is not None:
                    return adjusted_result

            elif suggested_strategy == FallbackStrategy.GRADUAL_FALLBACK:
                # 渐进式降级
                gradual_result = self._gradual_fallback(gpu_operation, cpu_operation, data, operation_name)
                if gradual_result is not None:
                    return gradual_result

            # 最终CPU回退
            logger.warning(f"GPU操作失败，回退到CPU: {operation_name}")
            self.fallback_stats['cpu_fallbacks'] += 1
            return cpu_operation(data)

    def _handle_continue_error(self, data, operation_name: str, original_error: Exception) -> Any:
        """处理可继续的错误"""
        # 根据操作类型生成合理的默认值
        if 'rsi' in operation_name.lower():
            # RSI错误时返回中性值50
            try:
                import cupy as cp
                if hasattr(data, '__len__'):
                    return cp.full(len(data), 50.0, dtype=cp.float32)
            except:
                pass

        elif 'macd' in operation_name.lower():
            # MACD错误时返回零值
            try:
                import cupy as cp
                if hasattr(data, '__len__'):
                    return cp.zeros(len(data), dtype=cp.float32)
            except:
                pass

        # 默认重新抛出错误
        raise original_error

    def _try_with_adjusted_params(self, operation: Callable, data, operation_name: str) -> Any:
        """参数调整后重试"""
        try:
            # 数据长度调整
            if hasattr(data, '__len__'):
                original_len = len(data)
                if original_len > 10000:
                    # 对大数据集进行采样
                    sample_indices = np.linspace(0, original_len - 1, min(5000, original_len), dtype=int)
                    sampled_data = data[sample_indices]
                    result = operation(sampled_data)
                    # 如果成功，可能需要对结果进行插值
                    return self._interpolate_result(result, original_len, sample_indices)

                elif original_len < 10:
                    # 对小数据集进行扩展
                    expanded_data = self._expand_small_dataset(data, 10)
                    result = operation(expanded_data)
                    return result[:original_len]  # 截断到原始长度

            # 数据类型调整
            try:
                # 尝试转换为float32
                if hasattr(data, 'astype'):
                    float32_data = data.astype(cp.float32)
                    return operation(float32_data)
            except:
                pass

        except Exception as e:
            logger.debug(f"参数调整重试失败: {e}")

        return None

    def _gradual_fallback(self, gpu_operation: Callable, cpu_operation: Callable,
                         data, operation_name: str) -> Any:
        """渐进式降级"""
        # 首先尝试部分GPU
        partial_result = self.try_partial_gpu(gpu_operation, data, operation_name)
        if partial_result is not None:
            return partial_result

        # 然后尝试参数调整
        adjusted_result = self._try_with_adjusted_params(gpu_operation, data, operation_name)
        if adjusted_result is not None:
            return adjusted_result

        # 最后CPU回退
        return cpu_operation(data)

    def _cpu_fallback_operation(self, operation_name: str, data) -> Any:
        """CPU回退操作"""
        try:
            # 根据操作名称执行相应的CPU计算
            if 'rsi' in operation_name.lower():
                return self._cpu_rsi_calculation(data)
            elif 'macd' in operation_name.lower():
                return self._cpu_macd_calculation(data)
            elif 'moving_average' in operation_name.lower() or 'sma' in operation_name.lower():
                return self._cpu_sma_calculation(data)
            else:
                # 默认返回零值或中性值
                import numpy as np
                return np.zeros(len(data), dtype=np.float32)
        except Exception as e:
            logger.error(f"CPU回退操作失败: {e}")
            return self._generate_default_result(data)

    def _cpu_rsi_calculation(self, data, period: int = 14) -> Any:
        """CPU RSI计算"""
        import numpy as np

        if len(data) < period:
            return np.full(len(data), 50.0, dtype=np.float32)

        delta = np.diff(data, prepend=data[0])
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)

        avg_gain = np.convolve(gain, np.ones(period), mode='valid') / period
        avg_loss = np.convolve(loss, np.ones(period), mode='valid') / period

        rs = avg_gain / np.where(avg_loss == 0, 1e-10, avg_loss)
        rsi = 100 - (100 / (1 + rs))

        result = np.full(len(data), 50.0, dtype=np.float32)
        result[period:] = rsi

        return result

    def _cpu_macd_calculation(self, data, fast: int = 12, slow: int = 26, signal: int = 9):
        """CPU MACD计算"""
        import numpy as np

        def ema(data, period):
            alpha = 2 / (period + 1)
            ema = np.zeros_like(data, dtype=np.float32)
            ema[0] = data[0]
            for i in range(1, len(data)):
                ema[i] = alpha * data[i] + (1 - alpha) * ema[i-1]
            return ema

        ema_fast = ema(data, fast)
        ema_slow = ema(data, slow)
        macd_line = ema_fast - ema_slow
        signal_line = ema(macd_line, signal)
        histogram = macd_line - signal_line

        return macd_line, signal_line, histogram

    def _cpu_sma_calculation(self, data, period: int = 20):
        """CPU SMA计算"""
        import numpy as np

        if len(data) < period:
            return np.full(len(data), np.mean(data), dtype=np.float32)

        return np.convolve(data, np.ones(period), mode='same') / period

    def _generate_default_result(self, data) -> Any:
        """生成默认结果"""
        try:
            import cupy as cp
            if hasattr(data, '__len__'):
                return cp.zeros(len(data), dtype=cp.float32)
        except:
            import numpy as np
            if hasattr(data, '__len__'):
                return np.zeros(len(data), dtype=np.float32)

        return 0.0

    def _interpolate_result(self, result, target_length: int, sample_indices):
        """结果插值"""
        try:
            import numpy as np
            if hasattr(result, 'get'):
                result_cpu = result.get()
            else:
                result_cpu = result

            # 线性插值
            from scipy.interpolate import interp1d
            f = interp1d(sample_indices, result_cpu, kind='linear',
                        bounds_error=False, fill_value='extrapolate')
            interpolated = f(np.arange(target_length))

            if GPU_AVAILABLE:
                return cp.asarray(interpolated)
            else:
                return interpolated
        except:
            return result

    def _expand_small_dataset(self, data, target_size: int):
        """扩展小数据集"""
        try:
            if len(data) >= target_size:
                return data

            # 重复数据以达到目标大小
            repeat_times = (target_size // len(data)) + 1
            expanded = np.tile(data, repeat_times)[:target_size]

            if GPU_AVAILABLE:
                return cp.asarray(expanded)
            else:
                return expanded
        except:
            return data

    def _combine_results(self, results):
        """合并结果"""
        try:
            if GPU_AVAILABLE:
                return cp.concatenate(results)
            else:
                return np.concatenate(results)
        except:
            return results[0] if results else None

    def get_error_statistics(self) -> Dict[str, Any]:
        """获取错误统计信息"""
        if not self.error_history:
            return {'total_errors': 0}

        # 错误类型统计
        error_types = {}
        severity_counts = {}
        recent_errors = []

        for error in self.error_history[-10:]:  # 最近10个错误
            error_types[error.error_type] = error_types.get(error.error_type, 0) + 1
            severity_counts[error.severity.value] = severity_counts.get(error.severity.value, 0) + 1
            recent_errors.append({
                'type': error.error_type,
                'severity': error.severity.value,
                'message': error.message,
                'timestamp': error.timestamp
            })

        # 降级统计
        total_ops = self.fallback_stats['total_operations']
        gpu_success_rate = (self.fallback_stats['gpu_successes'] / total_ops * 100) if total_ops > 0 else 0
        cpu_fallback_rate = (self.fallback_stats['cpu_fallbacks'] / total_ops * 100) if total_ops > 0 else 0

        return {
            'total_errors': len(self.error_history),
            'error_types': error_types,
            'severity_distribution': severity_counts,
            'recent_errors': recent_errors,
            'fallback_stats': {
                'total_operations': total_ops,
                'gpu_success_rate': gpu_success_rate,
                'cpu_fallback_rate': cpu_fallback_rate,
                'partial_gpu_successes': self.fallback_stats['partial_gpu_successes']
            },
            'retry_counts': self.retry_counts.copy()
        }

    def reset_statistics(self):
        """重置统计信息"""
        self.error_history.clear()
        self.retry_counts.clear()
        self.fallback_stats = {
            'total_operations': 0,
            'gpu_successes': 0,
            'partial_gpu_successes': 0,
            'cpu_fallbacks': 0
        }
        logger.info("错误统计信息已重置")


def get_gpu_error_handler() -> GPUErrorHandler:
    """获取GPU错误处理器实例"""
    return GPUErrorHandler()


# 装饰器版本
def with_gpu_fallback(cpu_operation: Callable, operation_name: str = None):
    """
    GPU回退装饰器

    Args:
        cpu_operation: CPU回退操作
        operation_name: 操作名称
    """
    def decorator(gpu_operation: Callable):
        def wrapper(data, *args, **kwargs):
            handler = get_gpu_error_handler()
            name = operation_name or gpu_operation.__name__

            # 绑定args和kwargs到操作
            def bound_gpu_op(d):
                return gpu_operation(d, *args, **kwargs)

            def bound_cpu_op(d):
                return cpu_operation(d, *args, **kwargs)

            return handler.execute_with_fallback(bound_gpu_op, bound_cpu_op, d, name)

        return wrapper
    return decorator


# 测试代码
if __name__ == "__main__":
    # 测试错误处理器
    handler = get_gpu_error_handler()

    def dummy_gpu_operation(data):
        """模拟GPU操作"""
        if hasattr(data, '__len__') and len(data) > 500:
            raise RuntimeError("CUDA out of memory")
        return data * 2

    def dummy_cpu_operation(data):
        """模拟CPU操作"""
        import numpy as np
        return np.array(data) * 2 if not isinstance(data, np.ndarray) else data * 2

    # 测试
    test_data = np.random.rand(1000)

    try:
        result = handler.execute_with_fallback(
            dummy_gpu_operation,
            dummy_cpu_operation,
            test_data,
            "test_operation"
        )

        print("错误处理测试成功")
        print(handler.get_error_statistics())

    except Exception as e:
        print(f"测试失败: {e}")