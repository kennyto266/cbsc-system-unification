"""
Configuration Loader

Handles loading configuration from multiple sources including files,
environment variables, command line arguments, and remote configuration services.
"""

import argparse
import json
import logging
import os
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml

# Optional hot - reload dependencies
try:
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer

    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    Observer = None
    FileSystemEventHandler = object


class ConfigFileHandler(FileSystemEventHandler):
    """File system event handler for configuration hot - reload."""

    def __init__(self, config_loader: "ConfigLoader"):
        if WATCHDOG_AVAILABLE:
            super().__init__()
        self.config_loader = config_loader
        self.last_reload = {}

    def on_modified(self, event):
        """Handle file modification events."""
        if not WATCHDOG_AVAILABLE or event.is_directory:
            return

        file_path = Path(event.src_path)
        if file_path.suffix in [".yaml", ".yml", ".json"]:
            # Debounce rapid file changes
            current_time = time.time()
            if file_path in self.last_reload:
                if current_time - self.last_reload[file_path] < 1.0:
                    return

            self.last_reload[file_path] = current_time
            logger.info(f"Configuration file modified: {file_path}")
            self.config_loader.reload_config()


logger = logging.getLogger(__name__)


@dataclass
class ConfigSource:
    """Configuration source definition."""

    name: str
    path: str
    format: str  # 'yaml', 'json', 'env', 'remote'
    priority: int  # Higher number = higher priority
    required: bool = True
    hot_reload: bool = False


class ConfigLoader:
    """
    Configuration loader with support for multiple sources and hot - reloading.
    """

    def __init__(self):
        """Initialize the configuration loader."""
        self.sources: List[ConfigSource] = []
        self.config_cache: Dict[str, Any] = {}
        self.observers: List[Observer] = []
        self.reload_callbacks: List[callable] = []
        self._lock = threading.Lock()

    def add_source(self, source: ConfigSource):
        """
        Add a configuration source.

        Args:
            source: Configuration source definition
        """
        self.sources.append(source)
        # Sort sources by priority (highest first)
        self.sources.sort(key=lambda x: x.priority, reverse=True)

    def add_file_source(
        self,
        file_path: str,
        priority: int = 100,
        required: bool = True,
        hot_reload: bool = False,
    ):
        """
        Add file configuration source.

        Args:
            file_path: Path to configuration file
            priority: Source priority
            required: Whether source is required
            hot_reload: Enable hot - reload for this file
        """
        path = Path(file_path)
        if not path.exists():
            if required:
                raise FileNotFoundError(
                    f"Required configuration file not found: {file_path}"
                )
            else:
                logger.warning(f"Optional configuration file not found: {file_path}")
                return

        format_type = path.suffix[1:] if path.suffix else "yaml"
        source = ConfigSource(
            name=f"file_{path.name}",
            path=str(path),
            format=format_type,
            priority=priority,
            required=required,
            hot_reload=hot_reload,
        )

        self.add_source(source)

        if hot_reload:
            if not WATCHDOG_AVAILABLE:
                logger.warning(
                    "Hot - reload requires 'watchdog' package. Install with: pip install watchdog"
                )
            else:
                self._setup_hot_reload(path)

    def add_env_source(self, prefix: str = "QUANT_", priority: int = 200):
        """
        Add environment variable source.

        Args:
            prefix: Environment variable prefix
            priority: Source priority
        """
        source = ConfigSource(
            name="environment",
            path=prefix,
            format="env",
            priority=priority,
            required=False,
            hot_reload=False,
        )
        self.add_source(source)

    def load_config(self) -> Dict[str, Any]:
        """
        Load configuration from all sources.

        Returns:
            Merged configuration dictionary
        """
        config = {}

        for source in self.sources:
            try:
                if source.format in ["yaml", "yml"]:
                    source_config = self._load_yaml_file(source.path)
                elif source.format == "json":
                    source_config = self._load_json_file(source.path)
                elif source.format == "env":
                    source_config = self._load_env_vars(source.path)
                elif source.format == "remote":
                    source_config = self._load_remote_config(source.path)
                else:
                    logger.warning(f"Unsupported configuration format: {source.format}")
                    continue

                if source_config:
                    config = self._merge_configs(config, source_config)
                    logger.debug(f"Loaded configuration from {source.name}")

            except Exception as e:
                if source.required:
                    raise RuntimeError(
                        f"Failed to load required configuration from {source.name}: {e}"
                    )
                else:
                    logger.warning(
                        f"Failed to load optional configuration from {source.name}: {e}"
                    )

        with self._lock:
            self.config_cache = config

        return config

    def reload_config(self) -> Dict[str, Any]:
        """
        Reload configuration from all sources.

        Returns:
            Reloaded configuration dictionary
        """
        logger.info("Reloading configuration...")
        config = self.load_config()

        # Call reload callbacks
        for callback in self.reload_callbacks:
            try:
                callback(config)
            except Exception as e:
                logger.error(f"Error in configuration reload callback: {e}")

        return config

    def add_reload_callback(self, callback: callable):
        """
        Add callback function to be called on configuration reload.

        Args:
            callback: Function to call on reload
        """
        self.reload_callbacks.append(callback)

    def _load_yaml_file(self, file_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        with open(file_path, "r", encoding="utf - 8") as f:
            return yaml.safe_load(f) or {}

    def _load_json_file(self, file_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        with open(file_path, "r", encoding="utf - 8") as f:
            return json.load(f) or {}

    def _load_env_vars(self, prefix: str) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        config = {}
        prefix_len = len(prefix)

        for key, value in os.environ.items():
            if key.startswith(prefix):
                # Convert environment variable name to nested dict path
                config_key = key[prefix_len:].lower()

                # Handle nested keys with underscores
                key_parts = config_key.split("__")
                current = config

                for part in key_parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]

                # Try to convert value to appropriate type
                current[key_parts[-1]] = self._convert_env_value(value)

        return config

    def _load_remote_config(self, url: str) -> Dict[str, Any]:
        """Load configuration from remote source."""
        # This would integrate with etcd, Consul, or other config services
        # For now, return empty dict
        logger.warning(f"Remote configuration not implemented: {url}")
        return {}

    def _convert_env_value(self, value: str) -> Any:
        """Convert environment variable string to appropriate type."""
        # Boolean conversion
        if value.lower() in ("true", "yes", "1", "on"):
            return True
        elif value.lower() in ("false", "no", "0", "off"):
            return False

        # Integer conversion
        try:
            return int(value)
        except ValueError:
            pass

        # Float conversion
        try:
            return float(value)
        except ValueError:
            pass

        # JSON conversion
        try:
            return json.loads(value)
        except ValueError:
            pass

        # Default to string
        return value

    def _merge_configs(
        self, base: Dict[str, Any], override: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge two configuration dictionaries.

        Args:
            base: Base configuration
            override: Override configuration

        Returns:
            Merged configuration
        """
        result = base.copy()

        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value

        return result

    def _setup_hot_reload(self, file_path: Path):
        """Setup file watcher for hot - reload."""
        if not WATCHDOG_AVAILABLE:
            logger.warning("Cannot setup hot - reload: 'watchdog' package not available")
            return

        observer = Observer()
        handler = ConfigFileHandler(self)

        # Watch the directory containing the file
        observer.schedule(handler, str(file_path.parent), recursive=False)
        observer.start()
        self.observers.append(observer)

        logger.info(f"Hot - reload enabled for: {file_path}")

    def stop_hot_reload(self):
        """Stop all hot - reload observers."""
        for observer in self.observers:
            observer.stop()
            observer.join()
        self.observers = []

    def save_config(self, config: Dict[str, Any], file_path: str, format: str = "yaml"):
        """
        Save configuration to file.

        Args:
            config: Configuration to save
            file_path: Output file path
            format: File format ('yaml' or 'json')
        """
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf - 8") as f:
            if format == "yaml":
                yaml.dump(config, f, default_flow_style=False, indent=2)
            elif format == "json":
                json.dump(config, f, indent=2)
            else:
                raise ValueError(f"Unsupported format: {format}")

        logger.info(f"Configuration saved to: {file_path}")

    def create_default_config_file(
        self, file_path: str, environment: str = "development"
    ):
        """
        Create a default configuration file.

        Args:
            file_path: Output file path
            environment: Target environment
        """
        from .schema import ConfigSchema

        schema = ConfigSchema()
        default_config = schema.get_default_config(environment)

        self.save_config(default_config, file_path)


class ConfigFactory:
    """
    Factory for creating pre - configured ConfigLoader instances.
    """

    @staticmethod
    def create_default_loader(environment: str = None) -> ConfigLoader:
        """
        Create default configuration loader with standard sources.

        Args:
            environment: Target environment (auto - detected if None)

        Returns:
            Configured ConfigLoader instance
        """
        if environment is None:
            environment = os.getenv(
                "QUANT_ENV", os.getenv("ENVIRONMENT", "development")
            )

        loader = ConfigLoader()

        # Add file sources in order of priority (low to high)
        config_files = [
            ("config / base.yaml", 100),
            (f"config/{environment}.yaml", 200),
            ("config / local.yaml", 300),
            ("config / override.yaml", 400),
        ]

        for file_path, priority in config_files:
            if Path(file_path).exists():
                loader.add_file_source(file_path, priority, required=False)

        # Add environment variables with highest priority
        loader.add_env_source(priority=500)

        # Add command line arguments
        loader.add_source(
            ConfigSource(
                name="command_line",
                path="args",
                format="cli",
                priority=600,
                required=False,
                hot_reload=False,
            )
        )

        return loader

    @staticmethod
    def create_production_loader() -> ConfigLoader:
        """Create configuration loader optimized for production."""
        loader = ConfigLoader()

        # Production file sources
        config_files = [
            ("config / production.yaml", 200),
            ("config / secrets.yaml", 300),
            ("config / override.yaml", 400),
        ]

        for file_path, priority in config_files:
            loader.add_file_source(file_path, priority, required=True)

        # Environment variables (primary in production)
        loader.add_env_source(priority=500)

        return loader

    @staticmethod
    def create_development_loader() -> ConfigLoader:
        """Create configuration loader optimized for development."""
        loader = ConfigLoader()

        # Development file sources with hot - reload
        config_files = [
            ("config / base.yaml", 100),
            ("config / development.yaml", 200),
            ("config / local.yaml", 300),
        ]

        for file_path, priority in config_files:
            if Path(file_path).exists():
                loader.add_file_source(
                    file_path, priority, required=False, hot_reload=True
                )

        # Environment variables for development overrides
        loader.add_env_source(priority=400)

        return loader
