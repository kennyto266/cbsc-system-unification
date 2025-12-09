#!/usr/bin/env python3
"""
Phase 3.1: Extended Parameter Space Configuration
擴展參數空間配置系統

Extended Parameter Space System for all technical indicators
Supports trend, momentum, volatility, and specialized indicators
"""

import json
import logging
import math
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class ParameterRange:
    """參數範圍配置"""
    name: str
    min_value: Union[int, float]
    max_value: Union[int, float]
    step: Union[int, float] = 1
    data_type: str = "int"  # int, float, bool, str
    default_value: Union[int, float, bool, str] = None
    description: str = ""

    def generate_values(self) -> List[Union[int, float, bool, str]]:
        """生成參數值列表"""
        if self.data_type == "bool":
            return [True, False]
        elif self.data_type == "str":
            return self.default_value if isinstance(self.default_value, list) else [self.default_value]
        else:
            if self.data_type == "int":
                return list(range(int(self.min_value), int(self.max_value) + 1, int(self.step)))
            else:  # float
                values = []
                current = self.min_value
                while current <= self.max_value + 1e-10:
                    values.append(round(current, 6))
                    current += self.step
                return values

    def validate_value(self, value: Union[int, float, bool, str]) -> bool:
        """驗證參數值是否有效"""
        if self.data_type == "bool":
            return isinstance(value, bool)
        elif self.data_type == "str":
            if isinstance(self.default_value, list):
                return value in self.default_value
            return value == self.default_value
        else:
            try:
                num_value = float(value)
                return self.min_value <= num_value <= self.max_value
            except (ValueError, TypeError):
                return False

@dataclass
class IndicatorConfig:
    """指標配置"""
    name: str
    category: str  # trend, momentum, volatility, specialized
    parameter_ranges: List[ParameterRange] = field(default_factory=list)
    max_combinations: int = 10000
    priority: int = 1
    enabled: bool = True
    description: str = ""

    def estimate_combinations(self) -> int:
        """估算參數組合數量"""
        if not self.parameter_ranges:
            return 1

        total = 1
        for param_range in self.parameter_ranges:
            values = param_range.generate_values()
            total *= len(values)

        return min(total, self.max_combinations)

class ExtendedParameterSpace:
    """擴展參數空間管理器"""

    def __init__(self, config_dir: str = None):
        """初始化參數空間管理器"""
        self.config_dir = Path(config_dir) if config_dir else Path("config")
        self.config_dir.mkdir(exist_ok=True)

        self.indicator_configs: Dict[str, IndicatorConfig] = {}
        self.parameter_space_cache: Dict[str, List[Dict]] = {}

        # 初始化預設配置
        self._initialize_preset_configurations()

        logger.info(f"ExtendedParameterSpace initialized with {len(self.indicator_configs)} indicators")

    def _initialize_preset_configurations(self):
        """初始化預設指標配置"""

        # Trend Indicators - 趨勢指標
        self.add_indicator_config(IndicatorConfig(
            name="RSI",
            category="trend",
            description="Relative Strength Index",
            parameter_ranges=[
                ParameterRange("period", 5, 100, 1, "int", 14, "RSI週期"),
                ParameterRange("oversold", 10, 40, 5, "float", 30.0, "超賣閾值"),
                ParameterRange("overbought", 60, 90, 5, "float", 70.0, "超買閾值")
            ]
        ))

        self.add_indicator_config(IndicatorConfig(
            name="MACD",
            category="trend",
            description="Moving Average Convergence Divergence",
            parameter_ranges=[
                ParameterRange("fast_period", 5, 30, 1, "int", 12, "快線週期"),
                ParameterRange("slow_period", 20, 100, 5, "int", 26, "慢線週期"),
                ParameterRange("signal_period", 5, 20, 1, "int", 9, "信號線週期")
            ]
        ))

        self.add_indicator_config(IndicatorConfig(
            name="KDJ",
            category="trend",
            description="Stochastic Oscillator",
            parameter_ranges=[
                ParameterRange("k_period", 5, 50, 1, "int", 9, "K值週期"),
                ParameterRange("d_period", 1, 20, 1, "int", 3, "D值平滑週期"),
                ParameterRange("j_period", 1, 20, 1, "int", 3, "J值週期")
            ]
        ))

        self.add_indicator_config(IndicatorConfig(
            name="BOLLINGER_BANDS",
            category="trend",
            description="Bollinger Bands",
            parameter_ranges=[
                ParameterRange("period", 5, 50, 1, "int", 20, "移動平均週期"),
                ParameterRange("std_dev", 1.0, 3.0, 0.1, "float", 2.0, "標準差倍數")
            ]
        ))

        self.add_indicator_config(IndicatorConfig(
            name="SMA_CROSS",
            category="trend",
            description="Simple Moving Average Crossover",
            parameter_ranges=[
                ParameterRange("short_period", 5, 30, 1, "int", 10, "短期均線週期"),
                ParameterRange("long_period", 20, 100, 5, "int", 50, "長期均線週期")
            ]
        ))

        self.add_indicator_config(IndicatorConfig(
            name="EMA_CROSS",
            category="trend",
            description="Exponential Moving Average Crossover",
            parameter_ranges=[
                ParameterRange("short_period", 5, 30, 1, "int", 12, "短期EMA週期"),
                ParameterRange("long_period", 20, 100, 5, "int", 26, "長期EMA週期")
            ]
        ))

        # Momentum Indicators - 動量指標
        self.add_indicator_config(IndicatorConfig(
            name="MOMENTUM",
            category="momentum",
            description="Price Momentum",
            parameter_ranges=[
                ParameterRange("period", 5, 50, 1, "int", 10, "動量週期"),
                ParameterRange("threshold", 0.01, 0.1, 0.01, "float", 0.05, "動量閾值")
            ]
        ))

        self.add_indicator_config(IndicatorConfig(
            name="ROC",
            category="momentum",
            description="Rate of Change",
            parameter_ranges=[
                ParameterRange("period", 5, 50, 1, "int", 12, "變化率週期"),
                ParameterRange("threshold", 1.0, 10.0, 1.0, "float", 5.0, "ROC閾值")
            ]
        ))

        self.add_indicator_config(IndicatorConfig(
            name="CCI",
            category="momentum",
            description="Commodity Channel Index",
            parameter_ranges=[
                ParameterRange("period", 10, 50, 1, "int", 20, "CCI週期"),
                ParameterRange("oversold", -200, -100, 20, "int", -100, "超賣水平"),
                ParameterRange("overbought", 100, 200, 20, "int", 100, "超買水平")
            ]
        ))

        self.add_indicator_config(IndicatorConfig(
            name="WILLIAMS_R",
            category="momentum",
            description="Williams %R",
            parameter_ranges=[
                ParameterRange("period", 5, 30, 1, "int", 14, "Williams %R週期"),
                ParameterRange("oversold", -90, -70, 5, "int", -80, "超賣水平"),
                ParameterRange("overbought", -30, -10, 5, "int", -20, "超買水平")
            ]
        ))

        self.add_indicator_config(IndicatorConfig(
            name="STOCH",
            category="momentum",
            description="Stochastic Oscillator",
            parameter_ranges=[
                ParameterRange("k_period", 5, 20, 1, "int", 14, "%K週期"),
                ParameterRange("d_period", 1, 10, 1, "int", 3, "%D平滑週期"),
                ParameterRange("slowing_period", 1, 10, 1, "int", 3, "慢速週期")
            ]
        ))

        # Volatility Indicators - 波動率指標
        self.add_indicator_config(IndicatorConfig(
            name="ATR",
            category="volatility",
            description="Average True Range",
            parameter_ranges=[
                ParameterRange("period", 5, 30, 1, "int", 14, "ATR週期"),
                ParameterRange("multiplier", 1.0, 3.0, 0.1, "float", 2.0, "ATR倍數")
            ]
        ))

        self.add_indicator_config(IndicatorConfig(
            name="VIX_STYLE",
            category="volatility",
            description="VIX-style Volatility Index",
            parameter_ranges=[
                ParameterRange("period", 10, 50, 1, "int", 20, "波動率週期"),
                ParameterRange("threshold", 15.0, 35.0, 5.0, "float", 25.0, "恐慌閾值")
            ]
        ))

        # Specialized Indicators - 專業化指標
        self.add_indicator_config(IndicatorConfig(
            name="MB_KDJ",
            category="specialized",
            description="Monetary Base Enhanced KDJ",
            parameter_ranges=[
                ParameterRange("k_period", 5, 30, 1, "int", 10, "KDJ週期"),
                ParameterRange("d_period", 1, 10, 1, "int", 2, "平滑週期"),
                ParameterRange("monetary_weight", 0.1, 1.0, 0.1, "float", 0.5, "貨幣基礎權重")
            ]
        ))

        self.add_indicator_config(IndicatorConfig(
            name="HIBOR_RSI",
            category="specialized",
            description="HIBOR Enhanced RSI",
            parameter_ranges=[
                ParameterRange("rsi_period", 5, 50, 1, "int", 14, "RSI週期"),
                ParameterRange("hibor_weight", 0.1, 1.0, 0.1, "float", 0.3, "HIBOR權重"),
                ParameterRange("signal_threshold", 0.3, 0.8, 0.1, "float", 0.5, "信號閾值")
            ]
        ))

        self.add_indicator_config(IndicatorConfig(
            name="PROPERTY_MACD",
            category="specialized",
            description="Property Market Enhanced MACD",
            parameter_ranges=[
                ParameterRange("fast_period", 5, 20, 1, "int", 12, "快線週期"),
                ParameterRange("slow_period", 15, 40, 5, "int", 26, "慢線週期"),
                ParameterRange("property_weight", 0.1, 1.0, 0.1, "float", 0.7, "物業市場權重")
            ]
        ))

        self.add_indicator_config(IndicatorConfig(
            name="UNIFIED_SIGNAL",
            category="specialized",
            description="Multi-Source Unified Signal",
            parameter_ranges=[
                ParameterRange("lookback_period", 10, 60, 5, "int", 20, "回溯週期"),
                ParameterRange("signal_threshold", 0.3, 0.9, 0.1, "float", 0.6, "統一信號閾值"),
                ParameterRange("min_sources", 3, 8, 1, "int", 5, "最少數據源")
            ]
        ))

        logger.info("Preset indicator configurations initialized")

    def add_indicator_config(self, config: IndicatorConfig):
        """添加指標配置"""
        self.indicator_configs[config.name] = config
        logger.debug(f"Added indicator configuration: {config.name}")

    def get_indicator_config(self, indicator_name: str) -> Optional[IndicatorConfig]:
        """獲取指標配置"""
        return self.indicator_configs.get(indicator_name)

    def get_indicators_by_category(self, category: str) -> List[IndicatorConfig]:
        """按類別獲取指標配置"""
        return [config for config in self.indicator_configs.values()
                if config.category == category and config.enabled]

    def generate_parameter_combinations(self, indicator_name: str, max_combinations: int = None) -> List[Dict]:
        """生成指標的參數組合"""
        if indicator_name in self.parameter_space_cache:
            return self.parameter_space_cache[indicator_name]

        config = self.get_indicator_config(indicator_name)
        if not config:
            logger.warning(f"No configuration found for indicator: {indicator_name}")
            return []

        # 生成參數組合
        parameter_names = [param.name for param in config.parameter_ranges]
        parameter_values = [param.generate_values() for param in config.parameter_ranges]

        combinations = []
        if parameter_values:
            # 使用迭代器生成組合以避免內存問題
            from itertools import product

            max_allowed = max_combinations or config.max_combinations
            total_combinations = math.prod(len(values) for values in parameter_values)

            if total_combinations > max_allowed:
                logger.warning(f"Too many combinations for {indicator_name}: {total_combinations} > {max_allowed}")
                # 使用智能採樣減少組合數量
                combinations = self._smart_sample_parameter_space(
                    parameter_names, parameter_values, max_allowed
                )
            else:
                for combination in product(*parameter_values):
                    param_dict = dict(zip(parameter_names, combination))
                    combinations.append(param_dict)
        else:
            # 無參數指標
            combinations = [{}]

        # 緩存結果
        self.parameter_space_cache[indicator_name] = combinations

        logger.info(f"Generated {len(combinations)} parameter combinations for {indicator_name}")
        return combinations

    def _smart_sample_parameter_space(self, parameter_names: List[str],
                                    parameter_values: List[List],
                                    max_combinations: int) -> List[Dict]:
        """智能採樣參數空間"""
        combinations = []

        # 對於每個參數，選擇有代表性的值
        sampled_values = []
        for values in parameter_values:
            if len(values) <= max_combinations ** (1/len(parameter_values)):
                sampled_values.append(values)
            else:
                # 等距採樣
                step = max(1, len(values) // int(max_combinations ** (1/len(parameter_values))))
                sampled_values.append(values[::step])

        from itertools import product
        for combination in product(*sampled_values):
            param_dict = dict(zip(parameter_names, combination))
            combinations.append(param_dict)

        return combinations[:max_combinations]

    def validate_parameters(self, indicator_name: str, parameters: Dict) -> bool:
        """驗證參數是否有效"""
        config = self.get_indicator_config(indicator_name)
        if not config:
            return False

        for param_range in config.parameter_ranges:
            if param_range.name in parameters:
                if not param_range.validate_value(parameters[param_range.name]):
                    logger.warning(f"Invalid parameter value for {indicator_name}.{param_range.name}: {parameters[param_range.name]}")
                    return False

        return True

    def get_total_combinations(self, indicator_names: List[str] = None) -> int:
        """獲取總參數組合數量"""
        if indicator_names is None:
            indicator_names = list(self.indicator_configs.keys())

        total = 0
        for indicator_name in indicator_names:
            config = self.get_indicator_config(indicator_name)
            if config and config.enabled:
                total += config.estimate_combinations()

        return total

    def export_configurations(self, file_path: str = None) -> str:
        """導出配置到JSON文件"""
        if file_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = self.config_dir / f"parameter_space_config_{timestamp}.json"

        config_data = {}
        for name, config in self.indicator_configs.items():
            config_data[name] = {
                "category": config.category,
                "max_combinations": config.max_combinations,
                "priority": config.priority,
                "enabled": config.enabled,
                "description": config.description,
                "parameter_ranges": [
                    {
                        "name": param.name,
                        "min_value": param.min_value,
                        "max_value": param.max_value,
                        "step": param.step,
                        "data_type": param.data_type,
                        "default_value": param.default_value,
                        "description": param.description
                    }
                    for param in config.parameter_ranges
                ]
            }

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Configurations exported to {file_path}")
        return str(file_path)

    def import_configurations(self, file_path: str):
        """從JSON文件導入配置"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)

            for name, data in config_data.items():
                parameter_ranges = []
                for param_data in data.get("parameter_ranges", []):
                    parameter_ranges.append(ParameterRange(
                        name=param_data["name"],
                        min_value=param_data["min_value"],
                        max_value=param_data["max_value"],
                        step=param_data["step"],
                        data_type=param_data["data_type"],
                        default_value=param_data.get("default_value"),
                        description=param_data.get("description", "")
                    ))

                config = IndicatorConfig(
                    name=name,
                    category=data["category"],
                    parameter_ranges=parameter_ranges,
                    max_combinations=data.get("max_combinations", 10000),
                    priority=data.get("priority", 1),
                    enabled=data.get("enabled", True),
                    description=data.get("description", "")
                )

                self.indicator_configs[name] = config

            logger.info(f"Configurations imported from {file_path}")

        except Exception as e:
            logger.error(f"Failed to import configurations from {file_path}: {e}")
            raise

    def get_statistics(self) -> Dict[str, Any]:
        """獲取參數空間統計信息"""
        stats = {
            "total_indicators": len(self.indicator_configs),
            "enabled_indicators": sum(1 for config in self.indicator_configs.values() if config.enabled),
            "categories": {},
            "total_combinations": 0
        }

        for config in self.indicator_configs.values():
            if config.enabled:
                if config.category not in stats["categories"]:
                    stats["categories"][config.category] = {
                        "count": 0,
                        "combinations": 0
                    }

                stats["categories"][config.category]["count"] += 1
                combinations = config.estimate_combinations()
                stats["categories"][config.category]["combinations"] += combinations
                stats["total_combinations"] += combinations

        return stats

if __name__ == "__main__":
    # 測試代碼
    logging.basicConfig(level=logging.INFO)

    # 創建參數空間管理器
    param_space = ExtendedParameterSpace()

    # 顯示統計信息
    stats = param_space.get_statistics()
    print("Parameter Space Statistics:")
    print(json.dumps(stats, indent=2))

    # 測試生成RSI參數組合
    rsi_combinations = param_space.generate_parameter_combinations("RSI")
    print(f"\nRSI parameter combinations: {len(rsi_combinations)}")
    print("Sample combinations:", rsi_combinations[:5])

    # 測試參數驗證
    valid_params = {"period": 14, "oversold": 30.0, "overbought": 70.0}
    invalid_params = {"period": 150, "oversold": 30.0, "overbought": 70.0}

    print(f"\nValid parameters test: {param_space.validate_parameters('RSI', valid_params)}")
    print(f"Invalid parameters test: {param_space.validate_parameters('RSI', invalid_params)}")

    # 導出配置
    config_file = param_space.export_configurations()
    print(f"\nConfiguration exported to: {config_file}")