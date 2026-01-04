"""
Enhanced Strategy Factory Module

Implements the Factory pattern for strategy instantiation and management.
Provides centralized strategy creation, registration, discovery mechanisms,
dynamic loading, and hot reload functionality.
"""

import importlib
import inspect
import logging
import os
import sys
from abc import ABC, abstractmethod
from typing import Dict, Type, Any, Optional, List, Callable, Union
from enum import Enum
from dataclasses import dataclass, field
from pathlib import Path
from uuid import uuid4, UUID
import threading
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from .base import BaseStrategy
from ..core.config import get_settings
from ..core.exceptions import StrategyError

logger = logging.getLogger(__name__)


class StrategyType(str, Enum):
    """Strategy type enumeration"""
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    TECHNICAL_ANALYSIS = "technical_analysis"
    FUNDAMENTAL = "fundamental"
    PORTFOLIO = "portfolio"
    ARBITRAGE = "arbitrage"
    CUSTOM = "custom"
    VOLUME = "volume"
    VOLATILITY = "volatility"


@dataclass
class StrategyMetadata:
    """Strategy metadata for registration"""
    name: str
    strategy_type: StrategyType
    description: str
    version: str
    author: str
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


class StrategyFileWatcher(FileSystemEventHandler):
    """File system event handler for strategy file changes"""

    def __init__(self, factory: 'EnhancedStrategyFactory'):
        self.factory = factory
        self.last_reload = {}

    def on_modified(self, event):
        """Handle file modification events"""
        if event.is_directory:
            return

        file_path = event.src_path
        if not file_path.endswith('.py'):
            return

        # Debounce rapid file changes
        current_time = time.time()
        if file_path in self.last_reload:
            if current_time - self.last_reload[file_path] < 1.0:  # 1 second debounce
                return

        self.last_reload[file_path] = current_time

        try:
            # Find strategies that use this file
            affected_strategies = []
            for name, metadata in self.factory.registry._metadata.items():
                if metadata.module_path and file_path in metadata.module_path:
                    affected_strategies.append(name)

            # Reload affected strategies
            for strategy_name in affected_strategies:
                try:
                    self.factory.reload_strategy(strategy_name)
                    logger.info(f"Hot reloaded strategy: {strategy_name}")
                except Exception as e:
                    logger.error(f"Failed to hot reload {strategy_name}: {e}")

        except Exception as e:
            logger.error(f"Error in file watcher: {e}")


class StrategyRegistry:
    """Enhanced registry for managing strategy classes and metadata"""

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
        """Register a strategy class with metadata"""
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

    def unregister(self, strategy_name: str) -> None:
        """Unregister a strategy"""
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
        """Get strategy class by name"""
        if strategy_name not in self._strategies:
            raise StrategyError(f"Strategy '{strategy_name}' not found in registry")
        return self._strategies[strategy_name]

    def get_metadata(self, strategy_name: str) -> StrategyMetadata:
        """Get strategy metadata by name"""
        if strategy_name not in self._metadata:
            raise StrategyError(f"Metadata for strategy '{strategy_name}' not found")
        return self._metadata[strategy_name]

    def list_strategies(
        self,
        strategy_type: Optional[StrategyType] = None,
        tags: Optional[List[str]] = None,
        author: Optional[str] = None,
        sort_by: str = "name"
    ) -> List[StrategyMetadata]:
        """List registered strategies with optional filtering and sorting"""
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
        """Search strategies by name, description, tags, or author"""
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
        """Get all strategies of a specific type"""
        return [s for s in self._metadata.values() if s.strategy_type == strategy_type]

    def get_recently_updated(self, hours: int = 24) -> List[StrategyMetadata]:
        """Get strategies updated in the last N hours"""
        cutoff_time = time.time() - (hours * 3600)
        return [
            s for s in self._metadata.values()
            if s.updated_at >= cutoff_time
        ]

    def get_load_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get strategy load/unload history"""
        return self._load_history[-limit:]

    def clear_cache(self, strategy_name: Optional[str] = None) -> None:
        """Clear cached strategy instances"""
        if strategy_name:
            if strategy_name in self._instances:
                del self._instances[strategy_name]
        else:
            self._instances.clear()

        logger.info(f"Cleared strategy cache: {strategy_name or 'all'}")

    def _check_dependencies(self, metadata: StrategyMetadata) -> None:
        """Check if strategy dependencies are available"""
        for dep in metadata.dependencies:
            try:
                importlib.import_module(dep)
            except ImportError as e:
                raise StrategyError(f"Missing dependency '{dep}' for strategy {metadata.name}: {e}")

    def get_statistics(self) -> Dict[str, Any]:
        """Get registry statistics"""
        type_counts = {}
        for metadata in self._metadata.values():
            type_counts[metadata.strategy_type] = type_counts.get(metadata.strategy_type, 0) + 1

        return {
            'total_strategies': len(self._metadata),
            'total_instances': len(self._instances),
            'type_distribution': type_counts,
            'last_updated': max([s.updated_at for s in self._metadata.values()]) if self._metadata else 0
        }


class EnhancedStrategyFactory:
    """
    Enhanced Factory for creating and managing strategy instances

    Provides centralized strategy instantiation with validation,
    configuration management, dynamic loading, and hot reload capabilities.
    """

    def __init__(self, registry: Optional[StrategyRegistry] = None):
        self.registry = registry or StrategyRegistry()
        self._loaders: Dict[str, Callable] = {}
        self._hot_reload_enabled = True
        self._watchers: Dict[str, Observer] = {}
        self._load_paths: List[str] = []
        self._plugin_paths: List[str] = []

        # Initialize with built-in loaders
        self._initialize_loaders()

        # Auto-load strategies from configured paths
        self._auto_load_strategies()

        # Setup file watchers for hot reload
        self._setup_file_watchers()

    def _initialize_loaders(self) -> None:
        """Initialize strategy loaders"""
        self._loaders.update({
            'python': self._load_python_strategy,
            'module': self._load_module_strategy,
            'file': self._load_file_strategy,
            'package': self._load_package_strategy,
            'plugin': self._load_plugin_strategy
        })

    def _auto_load_strategies(self) -> None:
        """Automatically load strategies from configured paths"""
        try:
            settings = get_settings()

            # Default strategy paths
            default_paths = [
                'strategies',
                'strategies.technical_indicators',
                'strategies.momentum',
                'strategies.volume',
                'strategies.fundamental_strategies',
                'strategies.portfolio_strategies'
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

    def _setup_file_watchers(self) -> None:
        """Setup file system watchers for hot reload"""
        if not self._hot_reload_enabled:
            return

        try:
            # Create observer for each load path
            for path_str in self._load_paths + self._plugin_paths:
                try:
                    path = Path(path_str)
                    if path.exists() and path.is_dir():
                        observer = Observer()
                        event_handler = StrategyFileWatcher(self)
                        observer.schedule(event_handler, str(path), recursive=True)
                        observer.start()
                        self._watchers[path_str] = observer
                        logger.info(f"Setup file watcher for: {path}")
                except Exception as e:
                    logger.warning(f"Failed to setup watcher for {path_str}: {e}")

        except ImportError:
            logger.warning("watchdog library not installed, hot reload disabled")
            self._hot_reload_enabled = False
        except Exception as e:
            logger.error(f"Failed to setup file watchers: {e}")

    def register_loader(self, loader_type: str, loader_func: Callable) -> None:
        """Register a custom strategy loader"""
        self._loaders[loader_type] = loader_func

    def create_strategy(
        self,
        strategy_name: str,
        config: Dict[str, Any],
        instance_id: Optional[UUID] = None,
        **kwargs
    ) -> BaseStrategy:
        """
        Create a strategy instance

        Args:
            strategy_name: Name of the strategy to create
            config: Strategy configuration parameters
            instance_id: Optional unique instance identifier
            **kwargs: Additional parameters for strategy initialization

        Returns:
            BaseStrategy: Initialized strategy instance

        Raises:
            StrategyError: If strategy creation fails
        """
        try:
            # Get strategy class and metadata
            strategy_class = self.registry.get_strategy_class(strategy_name)
            metadata = self.registry.get_metadata(strategy_name)

            # Validate configuration against metadata
            self._validate_config(config, metadata)

            # Create instance
            instance_id = instance_id or uuid4()
            strategy = strategy_class(
                instance_id=instance_id,
                config=config,
                metadata=metadata,
                **kwargs
            )

            # Cache instance for potential reuse
            cache_key = f"{strategy_name}_{instance_id}"
            self.registry._instances[cache_key] = strategy

            logger.info(f"Created strategy instance: {strategy_name} (ID: {instance_id})")
            return strategy

        except Exception as e:
            logger.error(f"Failed to create strategy {strategy_name}: {e}")
            raise StrategyError(f"Strategy creation failed: {e}") from e

    def create_strategy_from_template(
        self,
        template_name: str,
        overrides: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create strategy configuration from template

        Args:
            template_name: Name of the template
            overrides: Optional configuration overrides

        Returns:
            Dict: Strategy configuration
        """
        templates = {
            'ma_crossover': self._get_ma_crossover_template(),
            'rsi_mean_reversion': self._get_rsi_template(),
            'momentum_breakout': self._get_momentum_template(),
            'portfolio_allocation': self._get_portfolio_template(),
            'bollinger_bands': self._get_bollinger_template(),
            'macd_signal': self._get_macd_template(),
            'volume_price': self._get_volume_template()
        }

        if template_name not in templates:
            raise StrategyError(f"Template '{template_name}' not found")

        template = templates[template_name].copy()

        if overrides:
            template.update(overrides)

        return template

    def load_strategies_from_path(self, path: str) -> None:
        """
        Load strategies from a file path or directory

        Args:
            path: File or directory path containing strategy modules
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
        else:
            # Try to load as module
            try:
                self._load_python_strategy(path)
            except ImportError:
                logger.warning(f"Strategy path not found: {path}")

    def discover_strategies(self, search_paths: Optional[List[str]] = None) -> List[str]:
        """
        Discover available strategies in search paths

        Args:
            search_paths: List of paths to search (uses configured paths if None)

        Returns:
            List[str]: List of discovered strategy module paths
        """
        discovered = []

        if search_paths is None:
            search_paths = self._load_paths + self._plugin_paths

        for path in search_paths:
            try:
                path_obj = Path(path)
                if path_obj.is_dir():
                    for py_file in path_obj.glob('**/*.py'):
                        if (py_file.name != '__init__.py' and
                            not py_file.name.startswith('.')):
                            discovered.append(str(py_file))
            except Exception as e:
                logger.warning(f"Error searching path {path}: {e}")

        return discovered

    def reload_strategy(self, strategy_name: str) -> None:
        """
        Hot reload a strategy module

        Args:
            strategy_name: Name of the strategy to reload
        """
        if not self._hot_reload_enabled:
            raise StrategyError("Hot reload is disabled")

        try:
            metadata = self.registry.get_metadata(strategy_name)

            if metadata.module_path:
                # Reload the module
                module = importlib.import_module(metadata.module_path)
                importlib.reload(module)

                # Re-register the strategy
                if metadata.class_name:
                    strategy_class = getattr(module, metadata.class_name)
                    self.registry.register(strategy_class, metadata)

                # Clear cached instances
                self.registry.clear_cache(strategy_name)

                logger.info(f"Reloaded strategy: {strategy_name}")
            else:
                raise StrategyError(f"No module path for strategy '{strategy_name}'")

        except Exception as e:
            logger.error(f"Failed to reload strategy {strategy_name}: {e}")
            raise StrategyError(f"Strategy reload failed: {e}") from e

    def reload_all_strategies(self) -> Dict[str, bool]:
        """
        Reload all registered strategies

        Returns:
            Dict[str, bool]: Strategy name -> reload success
        """
        results = {}

        for strategy_name in list(self.registry._metadata.keys()):
            try:
                self.reload_strategy(strategy_name)
                results[strategy_name] = True
            except Exception as e:
                logger.error(f"Failed to reload {strategy_name}: {e}")
                results[strategy_name] = False

        return results

    def enable_hot_reload(self) -> None:
        """Enable hot reload functionality"""
        self._hot_reload_enabled = True
        if not self._watchers:
            self._setup_file_watchers()
        logger.info("Hot reload enabled")

    def disable_hot_reload(self) -> None:
        """Disable hot reload functionality"""
        self._hot_reload_enabled = False

        # Stop all watchers
        for observer in self._watchers.values():
            observer.stop()
            observer.join()
        self._watchers.clear()

        logger.info("Hot reload disabled")

    def get_factory_status(self) -> Dict[str, Any]:
        """Get factory status and statistics"""
        return {
            'hot_reload_enabled': self._hot_reload_enabled,
            'active_watchers': len(self._watchers),
            'load_paths': self._load_paths,
            'plugin_paths': self._plugin_paths,
            'registry_stats': self.registry.get_statistics(),
            'available_loaders': list(self._loaders.keys())
        }

    def _validate_config(self, config: Dict[str, Any], metadata: StrategyMetadata) -> None:
        """Validate strategy configuration against metadata"""
        # Check required parameters
        for param_name, param_info in metadata.parameters.items():
            if isinstance(param_info, dict) and param_info.get('required', False):
                if param_name not in config:
                    raise StrategyError(f"Required parameter '{param_name}' missing from config")

        # Validate parameter types and ranges
        for param_name, value in config.items():
            if param_name in metadata.parameters:
                param_info = metadata.parameters[param_name]

                if not isinstance(param_info, dict):
                    continue

                # Type validation
                expected_type = param_info.get('type')
                if expected_type and not isinstance(value, expected_type):
                    raise StrategyError(
                        f"Parameter '{param_name}' must be of type {expected_type.__name__}"
                    )

                # Range validation
                min_value = param_info.get('min')
                max_value = param_info.get('max')

                if min_value is not None and value < min_value:
                    raise StrategyError(
                        f"Parameter '{param_name}' must be >= {min_value}, got {value}"
                    )

                if max_value is not None and value > max_value:
                    raise StrategyError(
                        f"Parameter '{param_name}' must be <= {max_value}, got {value}"
                    )

                # Choice validation
                choices = param_info.get('choices')
                if choices and value not in choices:
                    raise StrategyError(
                        f"Parameter '{param_name}' must be one of {choices}, got {value}"
                    )

    def _load_python_strategy(self, module_path: str, class_name: Optional[str] = None) -> None:
        """Load strategy from Python module"""
        try:
            module = importlib.import_module(module_path)

            if class_name:
                strategy_class = getattr(module, class_name)
            else:
                # Find all BaseStrategy subclasses in module
                strategy_classes = []
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if (issubclass(obj, BaseStrategy) and
                        obj != BaseStrategy and
                        obj.__module__ == module.__name__):
                        strategy_classes.append((name, obj))

                if not strategy_classes:
                    logger.debug(f"No strategy classes found in module {module_path}")
                    return

                # Register all found strategies
                for name, strategy_class in strategy_classes:
                    self._register_strategy_from_class(strategy_class, module_path, name)

        except Exception as e:
            logger.error(f"Failed to load strategy from {module_path}: {e}")
            raise StrategyError(f"Strategy loading failed: {e}") from e

    def _load_module_strategy(self, module_path: str, **kwargs) -> None:
        """Load strategy from module (alias for _load_python_strategy)"""
        self._load_python_strategy(module_path, **kwargs)

    def _load_file_strategy(self, file_path: str, **kwargs) -> None:
        """Load strategy from file"""
        file_obj = Path(file_path)
        if file_obj.suffix != '.py':
            raise StrategyError(f"Cannot load strategy from {file_path}: not a Python file")

        self._load_python_file(file_obj, **kwargs)

    def _load_package_strategy(self, package_path: str, **kwargs) -> None:
        """Load strategies from a package"""
        try:
            package = importlib.import_module(package_path)
            package_dir = Path(package.__file__).parent

            # Load all Python files in package
            for py_file in package_dir.glob('*.py'):
                if py_file.name != '__init__.py':
                    self._load_python_file(py_file)

        except Exception as e:
            raise StrategyError(f"Failed to load package {package_path}: {e}") from e

    def _load_plugin_strategy(self, plugin_path: str, **kwargs) -> None:
        """Load strategy from plugin"""
        # This is a placeholder for plugin loading
        # Could be extended to support entry points, pip packages, etc.
        self._load_python_strategy(plugin_path, **kwargs)

    def _load_python_file(self, file_path: Path, **kwargs) -> None:
        """Load strategy from Python file"""
        import importlib.util

        # Convert path to module name
        module_name = file_path.stem.replace('-', '_')

        # Load module from file
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if not spec or not spec.loader:
            raise StrategyError(f"Cannot create module spec from {file_path}")

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
            raise e

    def _register_strategy_from_class(
        self,
        strategy_class: Type[BaseStrategy],
        module_path: str,
        class_name: str,
        file_path: Optional[str] = None
    ) -> None:
        """Register strategy class with extracted metadata"""
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

    def _get_ma_crossover_template(self) -> Dict[str, Any]:
        """Get moving average crossover template"""
        return {
            'name': 'MA Crossover Strategy',
            'strategy_type': StrategyType.MOMENTUM,
            'description': 'Dual moving average crossover strategy',
            'parameters': {
                'fast_period': {'type': int, 'default': 10, 'min': 1, 'max': 100, 'required': True},
                'slow_period': {'type': int, 'default': 20, 'min': 1, 'max': 200, 'required': True},
                'symbols': {'type': list, 'default': ['AAPL', 'MSFT'], 'required': True}
            },
            'config': {
                'fast_period': 10,
                'slow_period': 20,
                'symbols': ['AAPL', 'MSFT', 'GOOGL'],
                'allocation_per_symbol': 0.3
            }
        }

    def _get_rsi_template(self) -> Dict[str, Any]:
        """Get RSI mean reversion template"""
        return {
            'name': 'RSI Mean Reversion Strategy',
            'strategy_type': StrategyType.MEAN_REVERSION,
            'description': 'RSI-based mean reversion strategy',
            'parameters': {
                'rsi_period': {'type': int, 'default': 14, 'min': 5, 'max': 50, 'required': True},
                'oversold': {'type': float, 'default': 30, 'min': 10, 'max': 40, 'required': True},
                'overbought': {'type': float, 'default': 70, 'min': 60, 'max': 90, 'required': True}
            },
            'config': {
                'rsi_period': 14,
                'oversold': 30,
                'overbought': 70,
                'symbols': ['SPY', 'QQQ']
            }
        }

    def _get_momentum_template(self) -> Dict[str, Any]:
        """Get momentum breakout template"""
        return {
            'name': 'Momentum Breakout Strategy',
            'strategy_type': StrategyType.MOMENTUM,
            'description': 'Price momentum breakout strategy',
            'parameters': {
                'lookback_period': {'type': int, 'default': 20, 'min': 5, 'max': 100, 'required': True},
                'breakout_threshold': {'type': float, 'default': 0.02, 'min': 0.01, 'max': 0.10, 'required': True}
            },
            'config': {
                'lookback_period': 20,
                'breakout_threshold': 0.02,
                'symbols': ['TSLA', 'NVDA', 'AMD']
            }
        }

    def _get_portfolio_template(self) -> Dict[str, Any]:
        """Get portfolio allocation template"""
        return {
            'name': 'Portfolio Allocation Strategy',
            'strategy_type': StrategyType.PORTFOLIO,
            'description': 'Strategic portfolio allocation strategy',
            'parameters': {
                'rebalance_frequency': {'type': str, 'default': 'monthly', 'choices': ['daily', 'weekly', 'monthly']},
                'volatility_target': {'type': float, 'default': 0.15, 'min': 0.05, 'max': 0.30, 'required': True}
            },
            'config': {
                'rebalance_frequency': 'monthly',
                'volatility_target': 0.15,
                'assets': ['SPY', 'BND', 'GLD', 'QQQ'],
                'target_weights': [0.4, 0.3, 0.1, 0.2]
            }
        }

    def _get_bollinger_template(self) -> Dict[str, Any]:
        """Get Bollinger Bands template"""
        return {
            'name': 'Bollinger Bands Strategy',
            'strategy_type': StrategyType.TECHNICAL_ANALYSIS,
            'description': 'Bollinger Bands mean reversion strategy',
            'parameters': {
                'period': {'type': int, 'default': 20, 'min': 10, 'max': 50, 'required': True},
                'std_dev': {'type': float, 'default': 2.0, 'min': 1.0, 'max': 3.0, 'required': True}
            },
            'config': {
                'period': 20,
                'std_dev': 2.0,
                'symbols': ['SPY', 'QQQ']
            }
        }

    def _get_macd_template(self) -> Dict[str, Any]:
        """Get MACD template"""
        return {
            'name': 'MACD Signal Strategy',
            'strategy_type': StrategyType.TECHNICAL_ANALYSIS,
            'description': 'MACD crossover strategy',
            'parameters': {
                'fast_period': {'type': int, 'default': 12, 'min': 5, 'max': 20, 'required': True},
                'slow_period': {'type': int, 'default': 26, 'min': 20, 'max': 50, 'required': True},
                'signal_period': {'type': int, 'default': 9, 'min': 5, 'max': 15, 'required': True}
            },
            'config': {
                'fast_period': 12,
                'slow_period': 26,
                'signal_period': 9,
                'symbols': ['AAPL', 'MSFT']
            }
        }

    def _get_volume_template(self) -> Dict[str, Any]:
        """Get Volume Price template"""
        return {
            'name': 'Volume Price Strategy',
            'strategy_type': StrategyType.VOLUME,
            'description': 'Volume-based price action strategy',
            'parameters': {
                'volume_ma_period': {'type': int, 'default': 20, 'min': 10, 'max': 50, 'required': True},
                'volume_threshold': {'type': float, 'default': 1.5, 'min': 1.0, 'max': 3.0, 'required': True}
            },
            'config': {
                'volume_ma_period': 20,
                'volume_threshold': 1.5,
                'symbols': ['SPY', 'QQQ', 'IWM']
            }
        }

    def __del__(self):
        """Cleanup when factory is destroyed"""
        self.disable_hot_reload()


# Global enhanced strategy factory instance
_enhanced_strategy_factory: Optional[EnhancedStrategyFactory] = None


def get_enhanced_strategy_factory() -> EnhancedStrategyFactory:
    """Get the global enhanced strategy factory instance"""
    global _enhanced_strategy_factory
    if _enhanced_strategy_factory is None:
        _enhanced_strategy_factory = EnhancedStrategyFactory()
    return _enhanced_strategy_factory


def set_enhanced_strategy_factory(factory: EnhancedStrategyFactory) -> None:
    """Set the global enhanced strategy factory instance"""
    global _enhanced_strategy_factory
    _enhanced_strategy_factory = factory


def create_strategy(strategy_name: str, config: Dict[str, Any], **kwargs) -> BaseStrategy:
    """
    Convenience function to create a strategy using the enhanced global factory

    Args:
        strategy_name: Name of the strategy to create
        config: Strategy configuration parameters
        **kwargs: Additional parameters for strategy initialization

    Returns:
        BaseStrategy: Initialized strategy instance
    """
    factory = get_enhanced_strategy_factory()
    return factory.create_strategy(strategy_name, config, **kwargs)