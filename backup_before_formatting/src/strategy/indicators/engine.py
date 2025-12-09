"""
技术指标计算引擎

提供统一的指标计算引擎，支持向量化计算、缓存、批量处理和性能监控。
"""

from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Set, Union

import numpy as np
import pandas as pd

from ..traits import BaseIndicator, IndicatorResult
from . import (
    create_indicator,
    get_all_configs,
    get_indicator_config,
)

logger = logging.getLogger(__name__)


class IndicatorEngine:
    """技术指标计算引擎

    Features:
    - 统一计算接口
    - 向量化计算优化
    - LRU缓存机制
    - 批量处理支持
    - 性能监控
    - 并行计算（可选）
    """

    def __init__(
        self,
        cache_size: int = 1000,
        enable_parallel: bool = False,
        max_workers: int = 4,
    ) -> None:
        """初始化计算引擎

        Args:
            cache_size: 缓存大小，默认1000
            enable_parallel: 是否启用并行计算，默认False
            max_workers: 最大工作线程数，默认4
        """
        self.cache_size = cache_size
        self.cache: Dict[str, Any] = {}
        self.cache_order: List[str] = []
        self.enable_parallel = enable_parallel
        self.max_workers = max_workers
        self._stats: Dict[str, int] = {
            "cache_hits": 0,
            "cache_misses": 0,
            "calculations": 0,
        }
        self._registry = get_all_configs()

    def calculate(
        self,
        indicator_name: str,
        data: pd.DataFrame,
        **params: Any,
    ) -> IndicatorResult:
        """计算单个指标

        Args:
            indicator_name: 指标名称
            data: 输入数据
            **params: 指标参数

        Returns:
            计算结果
        """
        start_time = time.perf_counter()

        # 生成缓存键
        cache_key = self._generate_cache_key(indicator_name, data, params)

        # 检查缓存
        if cache_key in self.cache:
            self._stats["cache_hits"] += 1
            result = self.cache[cache_key]
            calculation_time = 0.0  # 从缓存返回，时间为0
            return IndicatorResult(
                data=result,
                indicator_name=indicator_name,
                calculation_time_ms=calculation_time,
                cache_hit=True,
            )

        # 创建指标实例
        try:
            indicator = create_indicator(indicator_name, **params)
        except Exception as e:
            raise ValueError(f"创建指标 {indicator_name} 失败: {e}")

        # 计算指标
        self._stats["cache_misses"] += 1
        self._stats["calculations"] += 1

        try:
            result = indicator.calculate(data)
        except Exception as e:
            logger.error(f"计算指标 {indicator_name} 失败: {e}")
            raise

        # 更新缓存
        self._update_cache(cache_key, result)

        calculation_time = (time.perf_counter() - start_time) * 1000

        return IndicatorResult(
            data=result,
            indicator_name=indicator_name,
            calculation_time_ms=calculation_time,
            cache_hit=False,
        )

    def calculate_multiple(
        self,
        indicators: List[Dict[str, Any]],
        data: pd.DataFrame,
    ) -> Dict[str, IndicatorResult]:
        """批量计算多个指标

        Args:
            indicators: 指标配置列表，每个元素为 {'name': str, 'params': dict}
            data: 输入数据

        Returns:
            指标名称到结果的映射
        """
        if not indicators:
            return {}

        if not self.enable_parallel or len(indicators) == 1:
            # 串行计算
            results = {}
            for config in indicators:
                name = config["name"]
                params = config.get("params", {})
                results[name] = self.calculate(name, data, **params)
            return results

        # 并行计算
        results = {}
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交任务
            future_to_name = {
                executor.submit(
                    self.calculate, config["name"], data, **config.get("params", {})
                ): config["name"]
                for config in indicators
            }

            # 收集结果
            for future in as_completed(future_to_name):
                name = future_to_name[future]
                try:
                    results[name] = future.result()
                except Exception as e:
                    logger.error(f"并行计算指标 {name} 失败: {e}")
                    # 返回错误结果
                    results[name] = IndicatorResult(
                        data=pd.DataFrame(),
                        indicator_name=name,
                        calculation_time_ms=0.0,
                        cache_hit=False,
                    )

        return results

    def calculate_sequential(
        self,
        indicators: List[Dict[str, Any]],
        data: pd.DataFrame,
    ) -> pd.DataFrame:
        """顺序计算多个指标，将结果合并

        Args:
            indicators: 指标配置列表
            data: 输入数据

        Returns:
            包含所有指标结果的DataFrame
        """
        if not indicators:
            return data

        result_data = data.copy()

        for config in indicators:
            name = config["name"]
            params = config.get("params", {})

            # 计算指标
            indicator_result = self.calculate(name, result_data, **params)

            # 合并结果（仅添加新的列）
            new_columns = set(indicator_result.data.columns) - set(result_data.columns)
            for col in new_columns:
                result_data[col] = indicator_result.data[col]

        return result_data

    def _generate_cache_key(
        self,
        indicator_name: str,
        data: pd.DataFrame,
        params: Dict[str, Any],
    ) -> str:
        """生成缓存键

        Args:
            indicator_name: 指标名称
            data: 输入数据
            params: 参数

        Returns:
            缓存键
        """
        # 使用数据形状和参数生成键
        data_hash = f"{data.shape}_{data.iloc[0, 0] if not data.empty else 0}"
        params_hash = hash(str(sorted(params.items())))
        return f"{indicator_name}:{data_hash}:{params_hash}"

    def _update_cache(self, key: str, value: Any) -> None:
        """更新缓存（LRU策略）

        Args:
            key: 缓存键
            value: 缓存值
        """
        if key in self.cache:
            # 移到末尾
            self.cache_order.remove(key)
            self.cache_order.append(key)
        else:
            # 添加新项
            self.cache[key] = value
            self.cache_order.append(key)

            # 检查是否超过大小限制
            if len(self.cache) > self.cache_size:
                # 移除最久未使用的项
                oldest_key = self.cache_order.pop(0)
                del self.cache[oldest_key]

    def clear_cache(self) -> None:
        """清空缓存"""
        self.cache.clear()
        self.cache_order.clear()
        logger.info("指标计算引擎缓存已清空")

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息

        Returns:
            统计信息字典
        """
        cache_hit_rate = 0.0
        if self._stats["cache_hits"] + self._stats["cache_misses"] > 0:
            cache_hit_rate = (
                self._stats["cache_hits"]
                / (self._stats["cache_hits"] + self._stats["cache_misses"])
            ) * 100

        return {
            "cache_size": len(self.cache),
            "cache_hits": self._stats["cache_hits"],
            "cache_misses": self._stats["cache_misses"],
            "cache_hit_rate": f"{cache_hit_rate:.2f}%",
            "total_calculations": self._stats["calculations"],
            "cache_entries": len(self.cache),
        }

    def validate_data(self, data: pd.DataFrame, indicator_name: str) -> bool:
        """验证数据是否适用于指定指标

        Args:
            data: 输入数据
            indicator_name: 指标名称

        Returns:
            是否有效
        """
        config = get_indicator_config(indicator_name)
        if config is None:
            return False

        required_cols = config.required_columns
        return all(col in data.columns for col in required_cols)

    def get_supported_indicators(self) -> List[str]:
        """获取支持的指标列表

        Returns:
            指标名称列表
        """
        return list(self._registry.keys())

    def benchmark(
        self,
        indicator_name: str,
        data: pd.DataFrame,
        iterations: int = 100,
        **params: Any,
    ) -> Dict[str, float]:
        """性能基准测试

        Args:
            indicator_name: 指标名称
            data: 测试数据
            iterations: 测试迭代次数
            **params: 指标参数

        Returns:
            性能统计信息
        """
        times = []

        # 预热
        for _ in range(5):
            self.calculate(indicator_name, data, **params)

        # 正式测试
        for _ in range(iterations):
            start = time.perf_counter()
            self.calculate(indicator_name, data, **params)
            end = time.perf_counter()
            times.append((end - start) * 1000)  # 转换为毫秒

        times = np.array(times)

        return {
            "mean_ms": float(np.mean(times)),
            "median_ms": float(np.median(times)),
            "min_ms": float(np.min(times)),
            "max_ms": float(np.max(times)),
            "std_ms": float(np.std(times)),
            "p95_ms": float(np.percentile(times, 95)),
            "p99_ms": float(np.percentile(times, 99)),
            "iterations": iterations,
            "data_points": len(data),
        }


# 全局默认引擎实例
default_engine = IndicatorEngine()


def calculate_indicator(
    indicator_name: str,
    data: pd.DataFrame,
    **params: Any,
) -> IndicatorResult:
    """便捷函数：使用默认引擎计算指标

    Args:
        indicator_name: 指标名称
        data: 输入数据
        **params: 指标参数

    Returns:
        计算结果
    """
    return default_engine.calculate(indicator_name, data, **params)


def calculate_multiple_indicators(
    indicators: List[Dict[str, Any]],
    data: pd.DataFrame,
) -> Dict[str, IndicatorResult]:
    """便捷函数：使用默认引擎批量计算指标

    Args:
        indicators: 指标配置列表
        data: 输入数据

    Returns:
        结果字典
    """
    return default_engine.calculate_multiple(indicators, data)
