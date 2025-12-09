#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPU数据验证器
解决GPU计算中的数据格式不兼容问题
确保所有输入数据完全兼容CuPy GPU计算
"""

import numpy as np
import pandas as pd
from typing import Union, List, Dict, Any, Tuple
import logging
from datetime import datetime
import warnings

try:
    import cupy as cp
    GPU_AVAILABLE = True
except ImportError:
    cp = None
    GPU_AVAILABLE = False

logger = logging.getLogger(__name__)

class GPUDataValidator:
    """GPU数据验证和转换器"""

    def __init__(self, gpu_device: int = 0):
        self.gpu_device = gpu_device
        self.compatible_dtypes = [
            cp.float32, cp.float64,
            cp.int32, cp.int64
        ]

        if GPU_AVAILABLE:
            cp.cuda.Device(gpu_device).use()
            logger.info(f"GPU数据验证器初始化，使用设备: {gpu_device}")
        else:
            logger.warning("CuPy不可用，GPU功能将禁用")

    def validate_and_convert(self, data: Union[np.ndarray, pd.Series, list, Dict, int, float]) -> Union[cp.ndarray, Dict[str, cp.ndarray]]:
        """
        验证输入数据并转换为CuPy数组

        Args:
            data: 输入数据（支持多种格式）

        Returns:
            GPU兼容的CuPy数组或字典

        Raises:
            ValueError: 数据格式不支持
            RuntimeError: GPU内存不足
        """
        if not GPU_AVAILABLE:
            raise RuntimeError("GPU unavailable, cannot convert data")

        try:
            if isinstance(data, dict):
                return self._convert_dict_to_gpu(data)
            elif isinstance(data, pd.DataFrame):
                return self._convert_dataframe_to_gpu(data)
            elif isinstance(data, pd.Series):
                return self._convert_series_to_gpu(data)
            elif isinstance(data, np.ndarray):
                return self._convert_numpy_to_gpu(data)
            elif isinstance(data, list):
                return self._convert_list_to_gpu(data)
            elif isinstance(data, (int, float)):
                # 处理标量数据
                array_data = self._handle_scalar_data(data)
                return self._convert_numpy_to_gpu(array_data)
            else:
                raise ValueError(f"Unsupported data type: {type(data)}")

        except Exception as e:
            logger.error(f"Data conversion failed: {e}")
            raise

    def _convert_dict_to_gpu(self, data_dict: Dict[str, Any]) -> Dict[str, cp.ndarray]:
        """转换字典数据到GPU"""
        result = {}
        for key, value in data_dict.items():
            try:
                result[key] = self.validate_and_convert(value)
            except Exception as e:
                logger.error(f"转换字典键 {key} 失败: {e}")
                raise
        return result

    def _convert_dataframe_to_gpu(self, df: pd.DataFrame) -> Dict[str, cp.ndarray]:
        """转换DataFrame到GPU字典"""
        result = {}
        for column in df.columns:
            try:
                # 处理日期时间列
                if pd.api.types.is_datetime64_any_dtype(df[column]):
                    result[column] = self._convert_datetime_to_gpu(df[column])
                else:
                    # 处理数值列
                    series = df[column].dropna()
                    if len(series) > 0:
                        result[column] = self._convert_series_to_gpu(series)
                    else:
                        logger.warning(f"列 {column} 为空")
            except Exception as e:
                logger.error(f"转换列 {column} 失败: {e}")
                raise
        return result

    def _convert_series_to_gpu(self, series: pd.Series) -> cp.ndarray:
        """转换pandas Series到GPU"""
        # 移除NaN值
        clean_series = series.dropna()

        if len(clean_series) == 0:
            raise ValueError("Series为空或全部为NaN")

        # 提取数值
        values = clean_series.values

        # 转换为numpy然后到GPU
        return self._convert_numpy_to_gpu(values)

    def _convert_numpy_to_gpu(self, array: np.ndarray) -> cp.ndarray:
        """转换numpy数组到GPU"""
        # 检查数据类型
        if not self._is_supported_dtype(array.dtype):
            # 尝试类型转换
            array = self._convert_to_supported_dtype(array)

        # 确保内存连续
        if not array.flags['C_CONTIGUOUS']:
            array = np.ascontiguousarray(array)

        # 转换到GPU
        try:
            gpu_array = cp.asarray(array)

            # 确保GPU数组内存连续
            if not gpu_array.flags['C_CONTIGUOUS']:
                gpu_array = cp.ascontiguousarray(gpu_array)

            return gpu_array

        except Exception as e:
            raise RuntimeError(f"GPU内存分配失败: {e}")

    def _convert_list_to_gpu(self, data_list: list) -> cp.ndarray:
        """转换列表到GPU"""
        # 先转换为numpy
        array = np.array(data_list)
        return self._convert_numpy_to_gpu(array)

    def _convert_datetime_to_gpu(self, datetime_series: pd.Series) -> cp.ndarray:
        """转换日期时间到GPU（转换为时间戳）"""
        try:
            # 标准化时区
            if datetime_series.dt.tz is not None:
                datetime_series = datetime_series.dt.tz_localize(None)

            # 转换为时间戳（秒）
            timestamps = datetime_series.astype('int64') // 10**9
            return self._convert_numpy_to_gpu(timestamps.astype(np.int64))

        except Exception as e:
            logger.error(f"日期时间转换失败: {e}")
            raise

    def _is_supported_dtype(self, dtype) -> bool:
        """检查数据类型是否支持"""
        try:
            if not GPU_AVAILABLE:
                return False

            # 检查是否为支持的numpy类型
            supported_types = [np.float32, np.float64, np.int32, np.int64]
            return dtype in supported_types
        except:
            return False

    def _convert_to_supported_dtype(self, array: np.ndarray) -> np.ndarray:
        """转换为支持的数据类型"""
        try:
            if np.issubdtype(array.dtype, np.floating):
                # 浮点数转为float32以节省内存
                return array.astype(np.float32)
            elif np.issubdtype(array.dtype, np.integer):
                # 整数转为int32
                return array.astype(np.int32)
            elif np.issubdtype(array.dtype, np.object_):
                # 对象类型尝试转换为float
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    converted = pd.to_numeric(array, errors='coerce')
                    if converted.isna().all():
                        raise ValueError("无法转换为数值类型")
                    return converted.dropna().values.astype(np.float32)
            else:
                # 尝试转为float32
                return array.astype(np.float32)

        except Exception as e:
            raise ValueError(f"无法转换数据类型 {array.dtype} 到支持的类型: {e}")

    def _handle_scalar_data(self, data) -> np.ndarray:
        """处理标量数据"""
        try:
            # 将标量转换为单元素数组
            if isinstance(data, (int, float)):
                return np.array([data], dtype=np.float32)
            else:
                # 尝试直接转换
                return np.array(data, dtype=np.float32)
        except Exception as e:
            raise ValueError(f"无法处理标量数据 {data}: {e}")

    def validate_prices(self, prices: Union[np.ndarray, pd.Series, list]) -> cp.ndarray:
        """专门验证价格数据"""
        try:
            gpu_prices = self.validate_and_convert(prices)

            # 价格数据验证
            if len(gpu_prices) == 0:
                raise ValueError("价格数据为空")

            # 检查价格合理性
            if cp.any(gpu_prices <= 0):
                logger.warning("价格数据包含非正值")

            # 检查价格变化
            if len(gpu_prices) > 1:
                price_changes = cp.diff(gpu_prices)
                extreme_changes = cp.abs(price_changes) > gpu_prices[:-1] * 0.5
                if cp.any(extreme_changes):
                    logger.warning("检测到极端价格变化")

            return gpu_prices

        except Exception as e:
            logger.error(f"价格数据验证失败: {e}")
            raise

    def validate_financial_data(self, data: Union[pd.DataFrame, Dict[str, Any]]) -> Dict[str, cp.ndarray]:
        """验证金融时间序列数据"""
        try:
            if isinstance(data, pd.DataFrame):
                gpu_data = self._convert_dataframe_to_gpu(data)
            elif isinstance(data, dict):
                gpu_data = self.validate_and_convert(data)
            else:
                raise ValueError("数据格式不支持")

            # 金融数据验证
            for key, array in gpu_data.items():
                # 检查数据长度
                if len(array) == 0:
                    logger.warning(f"数据 {key} 为空")

                # 检查NaN和无穷值
                if cp.any(cp.isnan(array)) or cp.any(cp.isinf(array)):
                    logger.warning(f"数据 {key} 包含NaN或无穷值")

                # 检查数据范围合理性
                if 'price' in key.lower() or 'close' in key.lower():
                    if cp.any(array <= 0):
                        logger.warning(f"价格数据 {key} 包含非正值")

            return gpu_data

        except Exception as e:
            logger.error(f"金融数据验证失败: {e}")
            raise

    def ensure_contiguous(self, data: cp.ndarray) -> cp.ndarray:
        """确保GPU数组内存连续"""
        if not data.flags['C_CONTIGUOUS']:
            data = cp.ascontiguousarray(data)
        return data

    def get_memory_usage(self) -> Dict[str, float]:
        """获取当前GPU内存使用情况"""
        if not GPU_AVAILABLE:
            return {'error': 'GPU不可用'}

        try:
            memory_pool = cp.get_default_memory_pool()
            used_bytes = memory_pool.used_bytes()
            total_bytes = memory_pool.total_bytes()

            return {
                'used_mb': used_bytes / (1024 * 1024),
                'total_mb': total_bytes / (1024 * 1024),
                'utilization': (used_bytes / total_bytes * 100) if total_bytes > 0 else 0
            }
        except Exception as e:
            return {'error': str(e)}

    def cleanup_memory(self):
        """清理GPU内存"""
        if GPU_AVAILABLE:
            try:
                cp.get_default_memory_pool().free_all_blocks()
                cp.get_default_pinned_memory_pool().free_all_blocks()
                logger.info("GPU内存已清理")
            except Exception as e:
                logger.error(f"GPU内存清理失败: {e}")


def get_gpu_data_validator(gpu_device: int = 0) -> GPUDataValidator:
    """获取GPU数据验证器实例"""
    return GPUDataValidator(gpu_device)


# 测试代码
if __name__ == "__main__":
    # 测试数据验证器
    validator = get_gpu_data_validator()

    # 测试数据
    test_data = {
        'prices': [100, 101, 102, 103, 104, 105],
        'volume': [1000, 1100, 1200, 1300, 1400, 1500],
        'dates': pd.date_range('2024-01-01', periods=6)
    }

    try:
        # 转换测试
        gpu_data = validator.validate_and_convert(test_data)
        print("GPU数据转换成功")
        print(f"内存使用: {validator.get_memory_usage()}")

        # 清理内存
        validator.cleanup_memory()

    except Exception as e:
        print(f"测试失败: {e}")