"""
基础策略和技术指标接口定义

此模块定义了技术指标系统的核心协议和抽象类，
提供统一的接口用于实现各种技术分析指标。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol, Type, Union

import numpy as np
import pandas as pd


class IndicatorProtocol(Protocol):
    """技术指标协议定义"""

    def __init__(self, **kwargs: Any) -> None:
        """初始化指标"""
        ...

    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算指标值

        Args:
            data: 包含OHLCV数据的DataFrame

        Returns:
            包含指标值的DataFrame
        """
        ...

    def get_required_columns(self) -> List[str]:
        """获取指标所需的数据列

        Returns:
            所需列名列表
        """
        ...

    def get_output_columns(self) -> List[str]:
        """获取指标输出的列名

        Returns:
            输出列名列表
        """
        ...


class BaseStrategy(ABC):
    """策略基类"""

    @abstractmethod
    async def initialize(self) -> None:
        """初始化策略"""
        pass

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """生成交易信号"""
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """清理资源"""
        pass


class BaseIndicator(ABC):
    """技术指标基类"""

    def __init__(self, name: str, params: Optional[Dict[str, Any]] = None) -> None:
        """初始化指标

        Args:
            name: 指标名称
            params: 指标参数
        """
        self.name = name
        self.params = params or {}
        self._cache: Dict[str, Any] = {}

    @abstractmethod
    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算指标

        Args:
            data: 包含OHLCV数据的DataFrame

        Returns:
            包含指标值的DataFrame
        """
        pass

    @abstractmethod
    def get_required_columns(self) -> List[str]:
        """获取所需的输入列

        Returns:
            所需列名列表
        """
        pass

    @abstractmethod
    def get_output_columns(self) -> List[str]:
        """获取输出的列名

        Returns:
            输出列名列表
        """
        pass

    def validate_input(self, data: pd.DataFrame) -> None:
        """验证输入数据

        Args:
            data: 输入数据

        Raises:
            ValueError: 当数据不符合要求时
        """
        required_cols = self.get_required_columns()
        missing_cols = [col for col in required_cols if col not in data.columns]
        if missing_cols:
            raise ValueError(f"缺少必需的列: {missing_cols}")

        if data.empty:
            raise ValueError("输入数据为空")

    def get_cache_key(self, data_shape: tuple, params: Dict[str, Any]) -> str:
        """生成缓存键

        Args:
            data_shape: 数据形状
            params: 参数字典

        Returns:
            缓存键字符串
        """
        return f"{self.name}_{data_shape}_{hash(str(sorted(params.items())))}"

    def clear_cache(self) -> None:
        """清空缓存"""
        self._cache.clear()


class IndicatorResult:
    """指标计算结果"""

    def __init__(
        self,
        data: pd.DataFrame,
        indicator_name: str,
        calculation_time_ms: float,
        cache_hit: bool = False,
    ) -> None:
        """初始化结果

        Args:
            data: 计算结果数据
            indicator_name: 指标名称
            calculation_time_ms: 计算耗时(毫秒)
            cache_hit: 是否命中缓存
        """
        self.data = data
        self.indicator_name = indicator_name
        self.calculation_time_ms = calculation_time_ms
        self.cache_hit = cache_hit

    @property
    def is_valid(self) -> bool:
        """检查结果是否有效"""
        return not self.data.empty

    def __str__(self) -> str:
        return f"IndicatorResult({self.indicator_name}, time={self.calculation_time_ms:.2f}ms)"


class IndicatorConfig:
    """指标配置"""

    def __init__(
        self,
        name: str,
        indicator_class: Type[BaseIndicator],
        params_schema: Dict[str, Any],
        description: str,
        required_columns: List[str],
        output_columns: List[str],
    ) -> None:
        """初始化配置

        Args:
            name: 指标名称
            indicator_class: 指标类
            params_schema: 参数模式
            description: 指标描述
            required_columns: 必需列
            output_columns: 输出列
        """
        self.name = name
        self.indicator_class = indicator_class
        self.params_schema = params_schema
        self.description = description
        self.required_columns = required_columns
        self.output_columns = output_columns

    def validate_params(self, params: Dict[str, Any]) -> bool:
        """验证参数

        Args:
            params: 待验证的参数

        Returns:
            是否有效
        """
        # 简化的参数验证
        for key, schema in self.params_schema.items():
            if key in params:
                if "type" in schema:
                    expected_type = schema["type"]
                    if not isinstance(params[key], expected_type):
                        return False
                if "min" in schema and params[key] < schema["min"]:
                    return False
                if "max" in schema and params[key] > schema["max"]:
                    return False
        return True


# 类型别名
NumericArray = Union[np.ndarray, pd.Series, List[float]]
DataFrameLike = Union[pd.DataFrame, np.ndarray]
