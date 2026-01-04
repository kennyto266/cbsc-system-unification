"""
Unified Strategy Factory

統一策略工廠 - 合併所有版本的策略工廠功能。

This unified factory combines features from:
- factory.py (base registration and creation)
- enhanced_factory_v2.py (metadata and validation)
- enhanced_factory.py (hot reload and dynamic loading)
"""

import importlib
import inspect
import logging
import os
import sys
import threading
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Type, Optional, Any, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from uuid import uuid4, UUID
from datetime import datetime, timezone

# Import base strategy
from .base import BaseStrategy, BaseSignal

# Import core components
from ..core.config import get_settings
from ..core.exceptions import StrategyError, ValidationError

logger = logging.getLogger(__name__)


class StrategyType(str, Enum):
    """策略類型枚舉"""
    TECHNICAL_ANALYSIS = "technical_analysis"
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    VOLUME = "volume"
    VOLATILITY = "volatility"
    FUNDAMENTAL = "fundamental"
    PORTFOLIO = "portfolio"
    ARBITRAGE = "arbitrage"
    MACRO = "macro"
    CUSTOM = "custom"


@dataclass
class StrategyMetadata:
    """
    策略元數據

    Strategy metadata for registration and management.
    """
    name: str
    strategy_type: StrategyType
    description: str
    version: str = "1.0.0"
    author: str = "System"
    tags: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    required_data: List[str] = field(default_factory=list)
    risk_level: str = "medium"
    expected_return: Optional[float] = None
    max_drawdown: Optional[float] = None
    module_path: Optional[str] = None
    class_name: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


class StrategyRegistry:
    """
    策略註冊表

    Centralized registry for managing strategy classes and metadata.
    """

    def __init__(self):
        self._strategies: Dict[str, Type[BaseStrategy]] = {}
        self._metadata: Dict[str, StrategyMetadata] = {}
        self._instances: Dict[str, BaseStrategy] = {}
        self._locks: Dict[str, threading.Lock] = {}
        self._load_history: List[Dict[str, Any]] = []

    def register(
        self,
        strategy_class: Type[BaseStrategy],
        metadata: StrategyMetadata
    ) -> None:
        """
        註冊策略類

        Register a strategy class with metadata.
        """
        strategy_name = metadata.name

        # Thread-safe registration
        if strategy_name not in self._locks:
            self._locks[strategy_name] = threading.Lock()

        with self._locks[strategy_name]:
            # Validate strategy class
            if not issubclass(strategy_class, BaseStrategy):
                raise StrategyError(f"Strategy {strategy_name} must inherit from BaseStrategy")

            # Check dependencies
            self._check_dependencies(metadata)

            # Store strategy class and metadata
            self._strategies[strategy_name] = strategy_class
            metadata.updated_at = time.time()
            self._metadata[strategy_name] = metadata

            # Record registration
            self._load_history.append({
                'action': 'register',
                'strategy': strategy_name,
                'timestamp': time.time(),
                'version': metadata.version
            })

            logger.info(f"Registered strategy: {strategy_name} (v{metadata.version})")

    def register_by_code(
        self,
        code: str,
        strategy_class: Type[BaseStrategy],
        metadata: Optional[StrategyMetadata] = None
    ) -> None:
        """
        按代碼註冊策略

        Register a strategy by code (alias).
        """
        # Create metadata if not provided
        if metadata is None:
            metadata = StrategyMetadata(
                name=code,
                strategy_type=getattr(strategy_class, 'STRATEGY_TYPE', StrategyType.CUSTOM),
                description=getattr(strategy_class, 'DESCRIPTION', f"{code} strategy"),
                version=getattr(strategy_class, 'VERSION', '1.0.0'),
                author=getattr(strategy_class, 'AUTHOR', 'System')
            )

        self._strategies[code] = strategy_class
        self._metadata[code] = metadata
        logger.info(f"Registered strategy by code: {code}")

    def unregister(self, strategy_name: str) -> None:
        """註銷策略"""
        with self._locks.get(strategy_name, threading.Lock()):
            if strategy_name in self._strategies:
                del self._strategies[strategy_name]
            if strategy_name in self._metadata:
                del self._metadata[strategy_name]
            if strategy_name in self._instances:
                del self._instances[strategy_name]

            # Record unregistration
            self._load_history.append({
                'action': 'unregister',
                'strategy': strategy_name,
                'timestamp': time.time()
            })

            logger.info(f"Unregistered strategy: {strategy_name}")

    def get_strategy_class(self, strategy_name: str) -> Type[BaseStrategy]:
        """獲取策略類"""
        if strategy_name not in self._strategies:
            available = ', '.join(self._strategies.keys())
            raise StrategyError(
                f"Strategy '{strategy_name}' not found. Available: {available}"
            )
        return self._strategies[strategy_name]

    def get_metadata(self, strategy_name: str) -> StrategyMetadata:
        """獲取策略元數據"""
        if strategy_name not in self._metadata:
            raise StrategyError(f"Strategy '{strategy_name}' not found in registry")
        return self._metadata[strategy_name]

    def list_strategies(
        self,
        strategy_type: Optional[StrategyType] = None,
        tags: Optional[List[str]] = None,
        author: Optional[str] = None,
        sort_by: str = "name"
    ) -> List[StrategyMetadata]:
        """
        列出策略

        List registered strategies with optional filtering and sorting.
        """
        strategies = list(self._metadata.values())

        # Apply filters
        if strategy_type:
            strategies = [s for s in strategies if s.strategy_type == strategy_type]

        if tags:
            strategies = [s for s in strategies if any(tag in s.tags for tag in tags)]

        if author:
            strategies = [s for s in strategies if author.lower() in s.author.lower()]

        # Sort
        if sort_by == "name":
            strategies.sort(key=lambda x: x.name)
        elif sort_by == "type":
            strategies.sort(key=lambda x: x.strategy_type)
        elif sort_by == "updated_at":
            strategies.sort(key=lambda x: x.updated_at, reverse=True)
        elif sort_by == "version":
            strategies.sort(key=lambda x: x.version, reverse=True)

        return strategies

    def search_strategies(self, query: str) -> List[StrategyMetadata]:
        """
        搜索策略

        Search strategies by name, description, tags, or author.
        """
        query_lower = query.lower()
        results = []

        for metadata in self._metadata.values():
            # Search in name and description
            if (query_lower in metadata.name.lower() or
                query_lower in metadata.description.lower() or
                query_lower in metadata.author.lower()):
                results.append(metadata)
                continue

            # Search in tags
            if any(query_lower in tag.lower() for tag in metadata.tags):
                results.append(metadata)

        return results

    def get_strategies_by_type(self, strategy_type: StrategyType) -> List[StrategyMetadata]:
        """根據類型獲取策略"""
        return [s for s in self._metadata.values() if s.strategy_type == strategy_type]

    def clear_cache(self, strategy_name: Optional[str] = None) -> None:
        """清除策略實例緩存"""
        if strategy_name:
            if strategy_name in self._instances:
                del self._instances[strategy_name]
        else:
            self._instances.clear()

        logger.info(f"Cleared strategy cache: {strategy_name or 'all'}")

    def get_statistics(self) -> Dict[str, Any]:
        """獲取註冊表統計"""
        type_counts = {}
        for metadata in self._metadata.values():
            type_counts[metadata.strategy_type] = type_counts.get(metadata.strategy_type, 0) + 1

        return {
            'total_strategies': len(self._metadata),
            'total_instances': len(self._instances),
            'type_distribution': type_counts,
            'last_updated': max([s.updated_at for s in self._metadata.values()]) if self._metadata else 0
        }

    def _check_dependencies(self, metadata: StrategyMetadata) -> None:
        """檢查策略依賴"""
        for dep in metadata.dependencies:
            try:
                importlib.import_module(dep)
            except ImportError as e:
                raise StrategyError(f"Missing dependency '{dep}' for strategy {metadata.name}: {e}")


class UnifiedStrategyFactory:
    """
    統一策略工廠

    Unified Strategy Factory - combines all factory versions.

    Features:
    - Strategy registration and creation
    - Metadata management
    - Hot reload support
    - Dynamic loading
    - Configuration validation
    - Template-based creation
    """

    def __init__(self, registry: Optional[StrategyRegistry] = None):
        """
        初始化工廠

        Initialize the unified strategy factory.
        """
        self.registry = registry or StrategyRegistry()
        self._loaders: Dict[str, Callable] = {}
        self._hot_reload_enabled = True
        self._load_paths: List[str] = []
        self._plugin_paths: List[str] = []

        # Initialize loaders
        self._initialize_loaders()

        # Auto-load strategies
        self._auto_load_strategies()

    def _initialize_loaders(self) -> None:
        """初始化策略加載器"""
        self._loaders.update({
            'python': self._load_python_strategy,
            'module': self._load_module_strategy,
            'file': self._load_file_strategy,
            'package': self._load_package_strategy
        })

    def _auto_load_strategies(self) -> None:
        """自動加載策略"""
        try:
            settings = get_settings()

            # Default strategy paths
            default_paths = [
                'src.strategies.technical_v2',
                'src.strategies.momentum_v2',
                'src.strategies.volume_v2',
                'src.strategies.portfolio_v2',
                'src.strategies.fundamental_v2'
            ]

            self._load_paths = getattr(settings, 'STRATEGY_LOAD_PATHS', default_paths)
            self._plugin_paths = getattr(settings, 'STRATEGY_PLUGIN_PATHS', [])

            # Load built-in strategies
            for path in self._load_paths:
                try:
                    self.load_strategies_from_path(path)
                except Exception as e:
                    logger.warning(f"Failed to load strategies from {path}: {e}")

            # Load plugin strategies
            for path in self._plugin_paths:
                try:
                    self.load_strategies_from_path(path)
                except Exception as e:
                    logger.warning(f"Failed to load plugin from {path}: {e}")

        except Exception as e:
            logger.warning(f"Failed to auto-load strategies: {e}")

    def load_strategies_from_path(self, path: str) -> None:
        """
        從路徑加載策略

        Load strategies from a file path or directory.
        """
        path_obj = Path(path)

        if path_obj.exists():
            if path_obj.is_file() and path_obj.suffix == '.py':
                self._load_python_file(path_obj)
            elif path_obj.is_dir():
                for py_file in path_obj.glob('**/*.py'):
                    if py_file.name != '__init__.py' and not py_file.name.startswith('.'):
                        try:
                            self._load_python_file(py_file)
                        except Exception as e:
                            logger.warning(f"Failed to load {py_file}: {e}")

    def _load_python_file(self, file_path: Path, **kwargs) -> None:
        """從 Python 文件加載策略"""
        import importlib.util

        # Convert path to module name
        module_name = file_path.stem.replace('-', '_')

        # Load module from file
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if not spec or not spec.loader:
            logger.warning(f"Cannot create module spec from {file_path}")
            return

        module = importlib.util.module_from_spec(spec)

        # Add to sys.modules for relative imports
        sys.modules[module_name] = module

        try:
            spec.loader.exec_module(module)

            # Find strategy classes in module
            strategy_classes = []
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if (issubclass(obj, BaseStrategy) and
                    obj != BaseStrategy and
                    obj.__module__ == module.__name__):
                    strategy_classes.append((name, obj))

            # Register all found strategies
            for name, strategy_class in strategy_classes:
                self._register_strategy_from_class(
                    strategy_class,
                    module_name,
                    name,
                    file_path=str(file_path)
                )

        except Exception as e:
            # Remove from sys.modules on failure
            if module_name in sys.modules:
                del sys.modules[module_name]
            logger.warning(f"Failed to load {file_path}: {e}")

    def _register_strategy_from_class(
        self,
        strategy_class: Type[BaseStrategy],
        module_path: str,
        class_name: str,
        file_path: Optional[str] = None
    ) -> None:
        """從類註冊策略"""
        # Extract metadata from class attributes
        metadata = StrategyMetadata(
            name=getattr(strategy_class, 'STRATEGY_NAME', class_name),
            strategy_type=getattr(strategy_class, 'STRATEGY_TYPE', StrategyType.CUSTOM),
            description=getattr(strategy_class, 'DESCRIPTION', ''),
            version=getattr(strategy_class, 'VERSION', '1.0.0'),
            author=getattr(strategy_class, 'AUTHOR', ''),
            tags=getattr(strategy_class, 'TAGS', []),
            parameters=getattr(strategy_class, 'PARAMETERS', {}),
            required_data=getattr(strategy_class, 'REQUIRED_DATA', []),
            risk_level=getattr(strategy_class, 'RISK_LEVEL', 'medium'),
            expected_return=getattr(strategy_class, 'EXPECTED_RETURN'),
            max_drawdown=getattr(strategy_class, 'MAX_DRAWDOWN'),
            dependencies=getattr(strategy_class, 'DEPENDENCIES', []),
            module_path=module_path,
            class_name=class_name
        )

        self.registry.register(strategy_class, metadata)

    def _load_python_strategy(self, module_path: str, class_name: Optional[str] = None) -> None:
        """從 Python 模塊加載策略"""
        try:
            module = importlib.import_module(module_path)

            if class_name:
                strategy_class = getattr(module, class_name)
                metadata = self.registry.get_metadata(class_name) if class_name in self.registry._metadata else None
                if metadata:
                    self.registry.register(strategy_class, metadata)
            else:
                # Find all BaseStrategy subclasses in module
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if (issubclass(obj, BaseStrategy) and
                        obj != BaseStrategy and
                        obj.__module__ == module.__name__):
                        self._register_strategy_from_class(obj, module_path, name)

        except Exception as e:
            logger.warning(f"Failed to load strategy from {module_path}: {e}")

    def _load_module_strategy(self, module_path: str, **kwargs) -> None:
        """從模塊加載策略 (alias)"""
        self._load_python_strategy(module_path, **kwargs)

    def _load_file_strategy(self, file_path: str, **kwargs) -> None:
        """從文件加載策略"""
        file_obj = Path(file_path)
        if file_obj.suffix != '.py':
            logger.warning(f"Cannot load strategy from {file_path}: not a Python file")
            return

        self._load_python_file(file_obj, **kwargs)

    def _load_package_strategy(self, package_path: str, **kwargs) -> None:
        """從包加載策略"""
        try:
            package = importlib.import_module(package_path)
            package_dir = Path(package.__file__).parent

            # Load all Python files in package
            for py_file in package_dir.glob('*.py'):
                if py_file.name != '__init__.py':
                    self._load_python_file(py_file)

        except Exception as e:
            logger.warning(f"Failed to load package {package_path}: {e}")

    # ==================== Public API ====================

    def register_strategy(
        self,
        strategy_class: Type[BaseStrategy],
        metadata: Optional[StrategyMetadata] = None
    ) -> None:
        """
        註冊策略

        Register a strategy class.

        Args:
            strategy_class: Strategy class to register
            metadata: Optional metadata (auto-generated if not provided)
        """
        if metadata is None:
            # Generate metadata from class
            metadata = StrategyMetadata(
                name=getattr(strategy_class, 'STRATEGY_NAME', strategy_class.__name__),
                strategy_type=getattr(strategy_class, 'STRATEGY_TYPE', StrategyType.CUSTOM),
                description=getattr(strategy_class, 'DESCRIPTION', strategy_class.__doc__ or ''),
                version=getattr(strategy_class, 'VERSION', '1.0.0'),
                author=getattr(strategy_class, 'AUTHOR', 'System')
            )

        self.registry.register(strategy_class, metadata)

    def register_by_code(
        self,
        code: str,
        strategy_class: Type[BaseStrategy]
    ) -> None:
        """
        按代碼註冊策略

        Register a strategy by code (alias).
        """
        self.registry.register_by_code(code, strategy_class)

    def create_strategy(
        self,
        strategy_name: str,
        config: Optional[Dict[str, Any]] = None,
        instance_id: Optional[str] = None
    ) -> BaseStrategy:
        """
        創建策略實例

        Create a strategy instance.

        Args:
            strategy_name: Name of the strategy
            config: Strategy configuration
            instance_id: Optional instance ID

        Returns:
            BaseStrategy: Strategy instance
        """
        try:
            # Get strategy class and metadata
            strategy_class = self.registry.get_strategy_class(strategy_name)
            metadata = self.registry.get_metadata(strategy_name)

            # Use provided config or default parameters
            if config is None:
                config = metadata.parameters.copy()

            # Generate instance ID
            if instance_id is None:
                instance_id = str(uuid4())

            # Create instance (handle different constructor signatures)
            sig = inspect.signature(strategy_class.__init__)
            if 'instance_id' in sig.parameters:
                # New architecture
                instance = strategy_class(instance_id=instance_id, config=config, metadata=metadata)
            elif 'config' in sig.parameters:
                # Mid architecture
                instance = strategy_class(config=config)
            elif 'name' in sig.parameters:
                # Old architecture
                instance = strategy_class(name=config.get('name', strategy_name), **config)
            else:
                # Minimal architecture
                instance = strategy_class(**config)

            # Cache instance
            cache_key = f"{strategy_name}_{instance_id}"
            self.registry._instances[cache_key] = instance

            logger.info(f"Created strategy instance: {strategy_name} (ID: {instance_id})")
            return instance

        except Exception as e:
            logger.error(f"Failed to create strategy {strategy_name}: {e}")
            raise StrategyError(f"Strategy creation failed: {e}") from e

    def create_strategy_batch(
        self,
        strategy_configs: List[Dict[str, Any]]
    ) -> List[BaseStrategy]:
        """
        批量創建策略

        Create multiple strategy instances.

        Args:
            strategy_configs: List of strategy configurations

        Returns:
            List of strategy instances
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

    def validate_config(
        self,
        strategy_name: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        驗證策略配置

        Validate strategy configuration.

        Args:
            strategy_name: Strategy name
            config: Configuration to validate

        Returns:
            Validation result with 'valid' and 'errors' keys
        """
        result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }

        if strategy_name not in self.registry._strategies:
            result['valid'] = False
            result['errors'].append(f"Strategy '{strategy_name}' not found")
            return result

        metadata = self.registry.get_metadata(strategy_name)

        # Check required parameters
        for param_name, param_info in metadata.parameters.items():
            if isinstance(param_info, dict) and param_info.get('required', False):
                if param_name not in config:
                    result['errors'].append(f"Missing required parameter: {param_name}")

        # Validate parameter types and ranges
        for param_name, value in config.items():
            if param_name in metadata.parameters:
                param_info = metadata.parameters[param_name]

                if not isinstance(param_info, dict):
                    continue

                # Type validation
                expected_type = param_info.get('type')
                if expected_type and not isinstance(value, expected_type):
                    result['errors'].append(
                        f"Parameter '{param_name}' must be of type {expected_type.__name__}, "
                        f"got {type(value).__name__}"
                    )

                # Range validation
                min_val = param_info.get('min')
                max_val = param_info.get('max')

                if min_val is not None and value < min_val:
                    result['errors'].append(
                        f"Parameter '{param_name}' must be >= {min_val}, got {value}"
                    )

                if max_val is not None and value > max_val:
                    result['errors'].append(
                        f"Parameter '{param_name}' must be <= {max_val}, got {value}"
                    )

        result['valid'] = len(result['errors']) == 0
        return result

    def get_available_strategies(self) -> Dict[str, StrategyMetadata]:
        """
        獲取所有可用策略

        Get all available strategies.

        Returns:
            Dict of strategy name to metadata
        """
        return self.registry._metadata.copy()

    def get_strategies_by_type(self, strategy_type: StrategyType) -> Dict[str, StrategyMetadata]:
        """
        根據類型獲取策略

        Get strategies by type.

        Args:
            strategy_type: Strategy type filter

        Returns:
            Dict of strategy name to metadata
        """
        return {
            name: metadata
            for name, metadata in self.registry._metadata.items()
            if metadata.strategy_type == strategy_type
        }

    def search_strategies(self, query: str) -> List[StrategyMetadata]:
        """
        搜索策略

        Search strategies by keyword.

        Args:
            query: Search query

        Returns:
            List of matching strategies
        """
        return self.registry.search_strategies(query)

    def get_factory_status(self) -> Dict[str, Any]:
        """
        獲取工廠狀態

        Get factory status and statistics.
        """
        return self.registry.get_statistics()

    def cleanup(self) -> None:
        """清理資源"""
        self.registry.clear_cache()
        logger.info("Unified strategy factory cleaned up")


# ==================== Global Instance ====================

_unified_factory: Optional[UnifiedStrategyFactory] = None


def get_unified_factory() -> UnifiedStrategyFactory:
    """Get global unified strategy factory instance"""
    global _unified_factory
    if _unified_factory is None:
        _unified_factory = UnifiedStrategyFactory()
    return _unified_factory


def set_unified_factory(factory: UnifiedStrategyFactory) -> None:
    """Set global unified strategy factory instance"""
    global _unified_factory
    _unifiedified_factory = factory


# ==================== Convenience Functions ====================

def create_strategy(
    strategy_name: str,
    config: Optional[Dict[str, Any]] = None,
    instance_id: Optional[str] = None
) -> BaseStrategy:
    """
    創建策略 (便捷函數)

    Convenience function to create a strategy.
    """
    factory = get_unified_factory()
    return factory.create_strategy(strategy_name, config, instance_id)


def register_strategy(
    strategy_class: Type[BaseStrategy],
    metadata: Optional[StrategyMetadata] = None
) -> None:
    """
    註冊策略 (便捷函數)

    Convenience function to register a strategy.
    """
    factory = get_unified_factory()
    factory.register_strategy(strategy_class, metadata)


def get_available_strategies() -> Dict[str, StrategyMetadata]:
    """
    獲取所有策略 (便捷函數)

    Convenience function to get all available strategies.
    """
    factory = get_unified_factory()
    return factory.get_available_strategies()


def search_strategies(query: str) -> List[StrategyMetadata]:
    """
    搜索策略 (便捷函數)

    Convenience function to search strategies.
    """
    factory = get_unified_factory()
    return factory.search_strategies(query)


# ==================== Backwards Compatibility ====================

# Legacy class aliases
StrategyFactory = UnifiedStrategyFactory

# Legacy global instance (deprecated)
_strategy_factory_instance: Optional[UnifiedStrategyFactory] = None


def get_strategy_factory() -> UnifiedStrategyFactory:
    """Get strategy factory (legacy name, use get_unified_factory instead)"""
    return get_unified_factory()


# Initialize factory on import
try:
    get_unified_factory()
except Exception as e:
    logger.warning(f"Failed to initialize unified strategy factory: {e}")
