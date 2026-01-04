"""
Enhanced Strategy Factory v2.0
增強的策略工廠實現

統一管理和創建所有類型的策略
"""

import logging
from typing import Dict, Any, List, Type, Optional, Union
from uuid import uuid4
from enum import Enum

# Import strategy bases
from .base import BaseStrategy
from .enhanced_factory import StrategyMetadata, StrategyType

# Import technical strategies
from .technical_v2 import (
    BaseTechnicalIndicatorStrategy,
    TECHNICAL_STRATEGIES
)

# Import momentum strategies
from .momentum_v2 import (
    BaseMomentumStrategy,
    MOMENTUM_STRATEGIES
)

# Import volume strategies
from .volume_v2 import (
    BaseVolumeStrategy,
    VOLUME_STRATEGIES
)

# Import portfolio strategies
from .portfolio_v2 import (
    BasePortfolioStrategy,
    PORTFOLIO_STRATEGIES
)

# Import fundamental strategies
from .fundamental_v2 import (
    BaseFundamentalStrategy,
    FUNDAMENTAL_STRATEGIES
)

# Import existing strategies for backward compatibility
from .momentum import ADXStrategy as LegacyADXStrategy
from .volume_strategies import (
    VolumePriceTrendStrategy,
    OnBalanceVolumeStrategy as LegacyOBVStrategy,
    VWAPStrategy as LegacyVWAPStrategy,
    MoneyFlowIndexStrategy as LegacyMFIStrategy
)

logger = logging.getLogger(__name__)


class StrategyFactoryV2:
    """
    Enhanced Strategy Factory v2.0

    統一的策略創建、註冊和管理工廠
    """

    def __init__(self):
        """初始化策略工廠"""
        self._strategies: Dict[str, Type[BaseStrategy]] = {}
        self._strategy_metadata: Dict[str, StrategyMetadata] = {}
        self._strategy_instances: Dict[str, BaseStrategy] = {}

        # 註冊所有策略
        self._register_all_strategies()

        logger.info(f"Strategy Factory initialized with {len(self._strategies)} strategies")

    def _register_all_strategies(self):
        """註冊所有可用的策略"""
        # 註冊技術指標策略
        for name, strategy_class in TECHNICAL_STRATEGIES.items():
            self._register_strategy(name, strategy_class, StrategyType.TECHNICAL_ANALYSIS)

        # 註冊動量策略
        for name, strategy_class in MOMENTUM_STRATEGIES.items():
            self._register_strategy(name, strategy_class, StrategyType.MOMENTUM)

        # 註冊成交量策略
        for name, strategy_class in VOLUME_STRATEGIES.items():
            self._register_strategy(name, strategy_class, StrategyType.VOLUME)

        # 註冊組合策略
        for name, strategy_class in PORTFOLIO_STRATEGIES.items():
            self._register_strategy(name, strategy_class, StrategyType.PORTFOLIO)

        # 註冊基本面策略
        for name, strategy_class in FUNDAMENTAL_STRATEGIES.items():
            self._register_strategy(name, strategy_class, StrategyType.FUNDAMENTAL)

        # 註冊遺留策略（向後兼容）
        legacy_strategies = {
            "adx_legacy": LegacyADXStrategy,
            "obv_legacy": LegacyOBVStrategy,
            "vwap_legacy": LegacyVWAPStrategy,
            "mfi_legacy": LegacyMFIStrategy,
            "vpt": VolumePriceTrendStrategy
        }

        for name, strategy_class in legacy_strategies.items():
            # 判斷策略類型
            if "ADX" in strategy_class.__name__:
                strategy_type = StrategyType.MOMENTUM
            elif any(x in strategy_class.__name__ for x in ["OBV", "VWAP", "VPT", "MFI"]):
                strategy_type = StrategyType.VOLUME
            elif any(x in strategy_class.__name__ for x in ["HIBOR", "GDP", "PMI", "Fundamental"]):
                strategy_type = StrategyType.FUNDAMENTAL
            else:
                strategy_type = StrategyType.TECHNICAL_ANALYSIS

            self._register_strategy(name, strategy_class, strategy_type)

    def _register_strategy(self, name: str, strategy_class: Type[BaseStrategy],
                          strategy_type: StrategyType):
        """註冊單個策略"""
        # 創建策略元數據
        metadata = StrategyMetadata(
            name=name,
            strategy_type=strategy_type,
            description=getattr(strategy_class, 'DESCRIPTION', f"{name} strategy"),
            version=getattr(strategy_class, 'VERSION', '1.0.0'),
            author=getattr(strategy_class, 'AUTHOR', 'System'),
            parameters=getattr(strategy_class, 'DEFAULT_PARAMETERS', {})
        )

        self._strategies[name] = strategy_class
        self._strategy_metadata[name] = metadata

        logger.debug(f"Registered strategy: {name} ({strategy_type.value})")

    def get_available_strategies(self) -> Dict[str, StrategyMetadata]:
        """
        獲取所有可用策略列表

        Returns:
            策略名稱到元數據的映射
        """
        return self._strategy_metadata.copy()

    def get_strategies_by_type(self, strategy_type: StrategyType) -> Dict[str, StrategyMetadata]:
        """
        根據類型獲取策略列表

        Args:
            strategy_type: 策略類型

        Returns:
            指定類型的策略列表
        """
        return {
            name: metadata
            for name, metadata in self._strategy_metadata.items()
            if metadata.strategy_type == strategy_type
        }

    def create_strategy(self, strategy_name: str, config: Optional[Dict[str, Any]] = None,
                        instance_id: Optional[str] = None) -> BaseStrategy:
        """
        創建策略實例

        Args:
            strategy_name: 策略名稱
            config: 策略配置參數
            instance_id: 實例ID（可選）

        Returns:
            策略實例

        Raises:
            ValueError: 策略不存在或創建失敗
        """
        if strategy_name not in self._strategies:
            available = ', '.join(self._strategies.keys())
            raise ValueError(f"Strategy '{strategy_name}' not found. Available: {available}")

        strategy_class = self._strategies[strategy_name]
        metadata = self._strategy_metadata[strategy_name]

        # 使用提供的配置或默認配置
        if config is None:
            config = metadata.parameters.copy()

        # 生成實例ID
        if instance_id is None:
            instance_id = str(uuid4())

        try:
            # 檢查策略是否需要instance_id參數
            import inspect
            sig = inspect.signature(strategy_class.__init__)
            if 'instance_id' in sig.parameters:
                # 新版策略架構
                instance = strategy_class(instance_id=instance_id, config=config, metadata=metadata)
            else:
                # 遺留策略架構
                if 'name' in sig.parameters:
                    instance = strategy_class(name=config.get('name', strategy_name), **config)
                else:
                    instance = strategy_class(**config)

            # 存儲實例（可選）
            # self._strategy_instances[f"{strategy_name}_{instance_id}"] = instance

            logger.info(f"Created strategy instance: {strategy_name} ({instance_id})")
            return instance

        except Exception as e:
            logger.error(f"Failed to create strategy {strategy_name}: {e}")
            raise ValueError(f"Failed to create strategy {strategy_name}: {e}") from e

    def create_strategy_batch(self, strategy_configs: List[Dict[str, Any]]) -> List[BaseStrategy]:
        """
        批量創建策略實例

        Args:
            strategy_configs: 策略配置列表，每個配置包含 'name' 和其他參數

        Returns:
            策略實例列表
        """
        strategies = []

        for config in strategy_configs:
            strategy_name = config.pop('name', None)
            if strategy_name is None:
                logger.warning(f"Skipping strategy config without name: {config}")
                continue

            try:
                instance = self.create_strategy(strategy_name, config)
                strategies.append(instance)
            except Exception as e:
                logger.error(f"Failed to create strategy {strategy_name}: {e}")

        return strategies

    def validate_strategy_config(self, strategy_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        驗證策略配置

        Args:
            strategy_name: 策略名稱
            config: 配置參數

        Returns:
            驗證結果，包含 'valid' 和 'errors' 字段
        """
        result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }

        if strategy_name not in self._strategies:
            result['valid'] = False
            result['errors'].append(f"Strategy '{strategy_name}' not found")
            return result

        strategy_class = self._strategies[strategy_name]

        # 檢查必需參數
        required_params = getattr(strategy_class, 'REQUIRED_PARAMETERS', [])
        for param in required_params:
            if param not in config:
                result['errors'].append(f"Missing required parameter: {param}")

        # 檢查參數範圍
        optional_params = getattr(strategy_class, 'OPTIONAL_PARAMETERS', {})
        for param, value in config.items():
            if param in optional_params:
                param_config = optional_params[param]

                # 類型檢查
                expected_type = param_config.get("type")
                if expected_type and not isinstance(value, expected_type):
                    result['errors'].append(
                        f"Parameter '{param}' must be of type {expected_type.__name__}, "
                        f"got {type(value).__name__}"
                    )

                # 範圍檢查
                min_val = param_config.get("min")
                max_val = param_config.get("max")

                if min_val is not None and value < min_val:
                    result['errors'].append(
                        f"Parameter '{param}' must be >= {min_val}, got {value}"
                    )

                if max_val is not None and value > max_val:
                    result['errors'].append(
                        f"Parameter '{param}' must be <= {max_val}, got {value}"
                    )

        result['valid'] = len(result['errors']) == 0
        return result

    def get_strategy_info(self, strategy_name: str) -> Optional[StrategyMetadata]:
        """
        獲取策略信息

        Args:
            strategy_name: 策略名稱

        Returns:
            策略元數據
        """
        return self._strategy_metadata.get(strategy_name)

    def search_strategies(self, keyword: str) -> List[StrategyMetadata]:
        """
        搜索策略

        Args:
            keyword: 搜索關鍵詞

        Returns:
            匹配的策略列表
        """
        keyword = keyword.lower()
        results = []

        for name, metadata in self._strategy_metadata.items():
            if (keyword in name.lower() or
                keyword in metadata.description.lower() or
                keyword in metadata.author.lower()):
                results.append(metadata)

        return results

    def get_strategy_stats(self) -> Dict[str, Any]:
        """
        獲取策略統計信息

        Returns:
            策略統計數據
        """
        stats = {
            'total_strategies': len(self._strategies),
            'by_type': {},
            'latest_version': '2.0.0'
        }

        # 按類型統計
        for strategy_type in StrategyType:
            count = len([
                metadata for metadata in self._strategy_metadata.values()
                if metadata.strategy_type == strategy_type
            ])
            stats['by_type'][strategy_type.value] = count

        return stats

    def export_strategy_config(self, strategy_name: str) -> Optional[Dict[str, Any]]:
        """
        導出策略配置模板

        Args:
            strategy_name: 策略名稱

        Returns:
            配置模板
        """
        if strategy_name not in self._strategy_metadata:
            return None

        metadata = self._strategy_metadata[strategy_name]
        strategy_class = self._strategies[strategy_name]

        # 構建配置模板
        template = {
            'name': strategy_name,
            'type': metadata.strategy_type.value,
            'description': metadata.description,
            'parameters': metadata.parameters.copy(),
            'required_parameters': getattr(strategy_class, 'REQUIRED_PARAMETERS', []),
            'optional_parameters': getattr(strategy_class, 'OPTIONAL_PARAMETERS', {}),
            'indicators': getattr(strategy_class, 'INDICATORS', {}),
            'supported_timeframes': getattr(strategy_class, 'SUPPORTED_TIMEFRAMES', [])
        }

        return template

    def cleanup_strategy_instances(self):
        """清理策略實例緩存"""
        self._strategy_instances.clear()
        logger.info("Cleaned up strategy instance cache")


# 全局策略工廠實例
strategy_factory = StrategyFactoryV2()


# 便捷函數
def create_strategy(strategy_name: str, config: Optional[Dict[str, Any]] = None,
                  instance_id: Optional[str] = None) -> BaseStrategy:
    """
    創建策略的便捷函數

    Args:
        strategy_name: 策略名稱
        config: 策略配置
        instance_id: 實例ID

    Returns:
        策略實例
    """
    return strategy_factory.create_strategy(strategy_name, config, instance_id)


def get_available_strategies() -> Dict[str, StrategyMetadata]:
    """
    獲取所有可用策略的便捷函數

    Returns:
        策略列表
    """
    return strategy_factory.get_available_strategies()


def get_strategies_by_type(strategy_type: StrategyType) -> Dict[str, StrategyMetadata]:
    """
    根據類型獲取策略的便捷函數

    Args:
        strategy_type: 策略類型

    Returns:
        策略列表
    """
    return strategy_factory.get_strategies_by_type(strategy_type)