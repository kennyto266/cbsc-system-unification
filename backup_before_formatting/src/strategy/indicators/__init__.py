"""
技术指标包

提供完整的技术分析指标集合。
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from ..traits import BaseIndicator, IndicatorConfig

logger = logging.getLogger(__name__)

# 全局指标注册表
_INDICATOR_REGISTRY: Dict[str, IndicatorConfig] = {}


def register_indicator(name: Optional[str] = None, **kwargs) -> callable:
    """指标注册装饰器"""

    def decorator(cls):
        if not issubclass(cls, BaseIndicator):
            raise ValueError(f"类 {cls.__name__} 必须继承自 BaseIndicator")

        indicator_name = name or cls.__name__
        config = IndicatorConfig(
            name=indicator_name,
            indicator_class=cls,
            params_schema=kwargs.get("params_schema", {}),
            description=kwargs.get("description", ""),
            required_columns=kwargs.get("required_columns", ["close"]),
            output_columns=kwargs.get("output_columns", [indicator_name.lower()]),
        )
        _INDICATOR_REGISTRY[indicator_name] = config
        return cls

    return decorator


def register_indicator_config(config: IndicatorConfig) -> None:
    """注册指标配置"""
    _INDICATOR_REGISTRY[config.name] = config


def get_indicator_config(name: str) -> Optional[IndicatorConfig]:
    """获取指标配置"""
    return _INDICATOR_REGISTRY.get(name)


def list_indicators() -> List[str]:
    """列出所有指标"""
    return list(_INDICATOR_REGISTRY.keys())


def get_all_configs() -> Dict[str, IndicatorConfig]:
    """获取所有配置"""
    return _INDICATOR_REGISTRY.copy()


def create_indicator(name: str, **params: Any) -> BaseIndicator:
    """创建指标实例"""
    config = get_indicator_config(name)
    if config is None:
        raise ValueError(f"未找到指标: {name}")
    return config.indicator_class(**params)


def validate_registry() -> Dict[str, List[str]]:
    """验证注册表"""
    errors = {}
    for name, config in _INDICATOR_REGISTRY.items():
        try:
            instance = config.indicator_class()
        except Exception as e:
            errors[name] = [str(e)]
    return errors


def get_registry_stats() -> Dict[str, int]:
    """获取统计信息"""
    return {
        "total_indicators": len(_INDICATOR_REGISTRY),
    }


# 导入所有指标模块以触发自动注册
from . import ma, macd, rsi

# 导出公共API
__all__ = [
    "register_indicator",
    "register_indicator_config",
    "get_indicator_config",
    "list_indicators",
    "get_all_configs",
    "create_indicator",
    "discover_indicators",
    "validate_registry",
    "get_registry_stats",
]
