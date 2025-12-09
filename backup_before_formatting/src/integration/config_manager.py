"""Configuration management for Hong Kong quantitative trading system.

This module provides comprehensive configuration management capabilities including
configuration loading, validation, environment management, and hot reloading.
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

import yaml
from pydantic import BaseModel, Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class ConfigValidationError(Exception):
    """Configuration validation error."""

    pass


class EnvironmentConfig(BaseModel):
    """Environment configuration."""

    name: str = Field(..., description="Environment name")
    debug: bool = Field(False, description="Debug mode")
    log_level: str = Field("INFO", description="Log level")
    data_path: str = Field(..., description="Data directory path")
    temp_path: str = Field(..., description="Temporary directory path")
    cache_path: str = Field(..., description="Cache directory path")


class DatabaseConfig(BaseModel):
    """Database configuration."""

    host: str = Field(..., description="Database host")
    port: int = Field(5432, description="Database port")
    name: str = Field(..., description="Database name")
    username: str = Field(..., description="Database username")
    password: str = Field(..., description="Database password")
    pool_size: int = Field(10, description="Connection pool size")
    max_overflow: int = Field(20, description="Max overflow connections")
    echo: bool = Field(False, description="Echo SQL queries")


class RedisConfig(BaseModel):
    """Redis configuration."""

    host: str = Field("localhost", description="Redis host")
    port: int = Field(6379, description="Redis port")
    password: Optional[str] = Field(None, description="Redis password")
    db: int = Field(0, description="Redis database number")
    max_connections: int = Field(10, description="Max connections")
    socket_timeout: int = Field(5, description="Socket timeout")
    socket_connect_timeout: int = Field(5, description="Socket connect timeout")


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: str = Field("INFO", description="Log level")
    format: str = Field(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s", description="Log format"
    )
    file_path: Optional[str] = Field(None, description="Log file path")
    max_file_size: int = Field(
        10 * 1024 * 1024, description="Max log file size (bytes)"
    )
    backup_count: int = Field(5, description="Number of backup files")
    console_output: bool = Field(True, description="Enable console output")


class SystemConfig(BaseModel):
    """System configuration."""

    system_id: str = Field(..., description="System identifier")
    system_name: str = Field(..., description="System name")
    version: str = Field("1.0.0", description="System version")
    environment: str = Field("development", description="Environment")
    timezone: str = Field("UTC", description="System timezone")
    max_workers: int = Field(4, description="Maximum worker threads")
    enable_metrics: bool = Field(True, description="Enable metrics collection")
    enable_tracing: bool = Field(False, description="Enable distributed tracing")


class TradingConfig(BaseModel):
    """Trading configuration."""

    market_hours: Dict[str, str] = Field(
        default_factory=dict, description="Market hours"
    )
    trading_symbols: List[str] = Field(
        default_factory=list, description="Trading symbols"
    )
    max_position_size: float = Field(1000000.0, description="Maximum position size")
    risk_limit: float = Field(0.1, description="Risk limit")
    commission_rate: float = Field(0.001, description="Commission rate")
    slippage_rate: float = Field(0.0005, description="Slippage rate")


class AgentConfig(BaseModel):
    """AI Agent configuration."""

    enabled_agents: List[str] = Field(
        default_factory=list, description="Enabled agents"
    )
    agent_timeout: int = Field(300, description="Agent timeout (seconds)")
    max_concurrent_agents: int = Field(10, description="Max concurrent agents")
    agent_retry_attempts: int = Field(3, description="Agent retry attempts")
    agent_retry_delay: int = Field(5, description="Agent retry delay (seconds)")


class ConfigManager:
    """Configuration manager for the trading system."""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "config"
        self.logger = logging.getLogger(__name__)

        # Configuration storage
        self.config: Dict[str, Any] = {}
        self.config_files: Dict[str, str] = {}
        self.config_schemas: Dict[str, BaseModel] = {}

        # Configuration watchers
        self.watchers: List[Callable] = []
        self.watch_tasks: List[asyncio.Task] = []

        # Statistics
        self.stats = {
            "config_loads": 0,
            "config_validations": 0,
            "config_errors": 0,
            "hot_reloads": 0,
            "start_time": None,
        }

        # Initialize configuration schemas
        self._initialize_schemas()

    def _initialize_schemas(self) -> None:
        """Initialize configuration schemas."""
        try:
            self.config_schemas = {
                "environment": EnvironmentConfig,
                "database": DatabaseConfig,
                "redis": RedisConfig,
                "logging": LoggingConfig,
                "system": SystemConfig,
                "trading": TradingConfig,
                "agent": AgentConfig,
            }

            self.logger.info(
                f"Initialized {len(self.config_schemas)} configuration schemas"
            )

        except Exception as e:
            self.logger.error(f"Error initializing configuration schemas: {e}")

    async def initialize(self) -> bool:
        """Initialize the configuration manager."""
        try:
            self.logger.info("Initializing configuration manager...")

            # Create config directory if it doesn't exist
            config_dir = Path(self.config_path)
            config_dir.mkdir(parents=True, exist_ok=True)

            # Load default configurations
            await self._load_default_configurations()

            # Load environment - specific configurations
            await self._load_environment_configurations()

            # Validate all configurations
            await self._validate_all_configurations()

            # Start configuration watchers
            await self._start_configuration_watchers()

            self.stats["start_time"] = datetime.now()
            self.logger.info("Configuration manager initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize configuration manager: {e}")
            return False

    async def _load_default_configurations(self) -> None:
        """Load default configurations."""
        try:
            # Default configurations
            default_configs = {
                "environment": {
                    "name": "development",
                    "debug": True,
                    "log_level": "DEBUG",
                    "data_path": "./data",
                    "temp_path": "./temp",
                    "cache_path": "./cache",
                },
                "database": {
                    "host": "localhost",
                    "port": 5432,
                    "name": "trading_db",
                    "username": "trading_user",
                    "password": "trading_pass",
                    "pool_size": 10,
                    "max_overflow": 20,
                    "echo": False,
                },
                "redis": {
                    "host": "localhost",
                    "port": 6379,
                    "password": None,
                    "db": 0,
                    "max_connections": 10,
                    "socket_timeout": 5,
                    "socket_connect_timeout": 5,
                },
                "logging": {
                    "level": "INFO",
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    "file_path": "./logs / trading_system.log",
                    "max_file_size": 10 * 1024 * 1024,
                    "backup_count": 5,
                    "console_output": True,
                },
                "system": {
                    "system_id": "trading_system_001",
                    "system_name": "Hong Kong Quantitative Trading System",
                    "version": "1.0.0",
                    "environment": "development",
                    "timezone": "UTC",
                    "max_workers": 4,
                    "enable_metrics": True,
                    "enable_tracing": False,
                },
                "trading": {
                    "market_hours": {"open": "09:30", "close": "16:00"},
                    "trading_symbols": ["00700.HK", "2800.HK", "0700.HK"],
                    "max_position_size": 1000000.0,
                    "risk_limit": 0.1,
                    "commission_rate": 0.001,
                    "slippage_rate": 0.0005,
                },
                "agent": {
                    "enabled_agents": [
                        "quantitative_analyst",
                        "quantitative_trader",
                        "portfolio_manager",
                        "risk_analyst",
                        "data_scientist",
                        "quantitative_engineer",
                        "research_analyst",
                    ],
                    "agent_timeout": 300,
                    "max_concurrent_agents": 10,
                    "agent_retry_attempts": 3,
                    "agent_retry_delay": 5,
                },
            }

            # Load each configuration
            for config_name, config_data in default_configs.items():
                await self._load_configuration(config_name, config_data)

            self.logger.info("Default configurations loaded")

        except Exception as e:
            self.logger.error(f"Error loading default configurations: {e}")

    async def _load_environment_configurations(self) -> None:
        """Load environment - specific configurations."""
        try:
            # Get environment from system
            environment = os.getenv("TRADING_ENV", "development")

            # Load environment - specific config files
            env_config_files = [
                f"{self.config_path}/config_{environment}.yaml",
                f"{self.config_path}/config_{environment}.json",
                f"{self.config_path}/config_{environment}.yml",
            ]

            for config_file in env_config_files:
                if os.path.exists(config_file):
                    await self._load_configuration_file(config_file)
                    break

            # Load environment variables
            await self._load_environment_variables()

            self.logger.info(f"Environment configurations loaded for: {environment}")

        except Exception as e:
            self.logger.error(f"Error loading environment configurations: {e}")

    async def _load_configuration_file(self, file_path: str) -> None:
        """Load configuration from file."""
        try:
            file_path_obj = Path(file_path)

            if not file_path_obj.exists():
                self.logger.warning(f"Configuration file not found: {file_path}")
                return

            # Determine file type
            if file_path.endswith(".yaml") or file_path.endswith(".yml"):
                with open(file_path, "r", encoding="utf - 8") as f:
                    config_data = yaml.safe_load(f)
            elif file_path.endswith(".json"):
                with open(file_path, "r", encoding="utf - 8") as f:
                    config_data = json.load(f)
            else:
                self.logger.warning(
                    f"Unsupported configuration file format: {file_path}"
                )
                return

            # Load configurations
            if isinstance(config_data, dict):
                for config_name, config_values in config_data.items():
                    await self._load_configuration(config_name, config_values)

            self.config_files[file_path] = file_path
            self.logger.info(f"Configuration file loaded: {file_path}")

        except Exception as e:
            self.logger.error(f"Error loading configuration file {file_path}: {e}")

    async def _load_environment_variables(self) -> None:
        """Load configuration from environment variables."""
        try:
            # Environment variable mappings
            env_mappings = {
                "TRADING_DB_HOST": ("database", "host"),
                "TRADING_DB_PORT": ("database", "port"),
                "TRADING_DB_NAME": ("database", "name"),
                "TRADING_DB_USERNAME": ("database", "username"),
                "TRADING_DB_PASSWORD": ("database", "password"),
                "TRADING_REDIS_HOST": ("redis", "host"),
                "TRADING_REDIS_PORT": ("redis", "port"),
                "TRADING_REDIS_PASSWORD": ("redis", "password"),
                "TRADING_LOG_LEVEL": ("logging", "level"),
                "TRADING_ENV": ("environment", "name"),
                "TRADING_DEBUG": ("environment", "debug"),
                "TRADING_SYSTEM_ID": ("system", "system_id"),
                "TRADING_SYSTEM_NAME": ("system", "system_name"),
                "TRADING_VERSION": ("system", "version"),
            }

            # Load environment variables
            for env_var, (config_section, config_key) in env_mappings.items():
                env_value = os.getenv(env_var)
                if env_value is not None:
                    # Convert value to appropriate type
                    converted_value = self._convert_env_value(env_value)

                    # Update configuration
                    if config_section not in self.config:
                        self.config[config_section] = {}
                    self.config[config_section][config_key] = converted_value

            self.logger.info("Environment variables loaded")

        except Exception as e:
            self.logger.error(f"Error loading environment variables: {e}")

    def _convert_env_value(self, value: str) -> Any:
        """Convert environment variable value to appropriate type."""
        try:
            # Try to convert to boolean
            if value.lower() in ("true", "false"):
                return value.lower() == "true"

            # Try to convert to integer
            if value.isdigit():
                return int(value)

            # Try to convert to float
            try:
                return float(value)
            except ValueError:
                pass

            # Return as string
            return value

        except Exception as e:
            self.logger.error(f"Error converting environment value: {e}")
            return value

    async def _load_configuration(
        self, config_name: str, config_data: Dict[str, Any]
    ) -> None:
        """Load a specific configuration."""
        try:
            # Merge with existing configuration
            if config_name in self.config:
                self.config[config_name].update(config_data)
            else:
                self.config[config_name] = config_data

            self.stats["config_loads"] += 1
            self.logger.debug(f"Configuration loaded: {config_name}")

        except Exception as e:
            self.logger.error(f"Error loading configuration {config_name}: {e}")

    async def _validate_all_configurations(self) -> None:
        """Validate all configurations."""
        try:
            for config_name, config_data in self.config.items():
                await self._validate_configuration(config_name, config_data)

            self.logger.info("All configurations validated successfully")

        except Exception as e:
            self.logger.error(f"Error validating configurations: {e}")
            raise ConfigValidationError(f"Configuration validation failed: {e}")

    async def _validate_configuration(
        self, config_name: str, config_data: Dict[str, Any]
    ) -> None:
        """Validate a specific configuration."""
        try:
            if config_name not in self.config_schemas:
                self.logger.warning(f"No schema found for configuration: {config_name}")
                return

            # Get schema
            schema = self.config_schemas[config_name]

            # Validate configuration
            try:
                validated_config = schema(**config_data)
                self.config[config_name] = validated_config.model_dump()
                self.stats["config_validations"] += 1

            except ValidationError as e:
                self.stats["config_errors"] += 1
                self.logger.error(
                    f"Configuration validation failed for {config_name}: {e}"
                )
                raise ConfigValidationError(
                    f"Configuration validation failed for {config_name}: {e}"
                )

        except Exception as e:
            self.logger.error(f"Error validating configuration {config_name}: {e}")
            raise

    async def _start_configuration_watchers(self) -> None:
        """Start configuration file watchers."""
        try:
            # Watch configuration files for changes
            for file_path in self.config_files.values():
                if os.path.exists(file_path):
                    watch_task = asyncio.create_task(
                        self._watch_configuration_file(file_path)
                    )
                    self.watch_tasks.append(watch_task)

            self.logger.info(f"Started {len(self.watch_tasks)} configuration watchers")

        except Exception as e:
            self.logger.error(f"Error starting configuration watchers: {e}")

    async def _watch_configuration_file(self, file_path: str) -> None:
        """Watch a configuration file for changes."""
        try:
            last_modified = os.path.getmtime(file_path)

            while True:
                try:
                    # Check if file was modified
                    current_modified = os.path.getmtime(file_path)

                    if current_modified > last_modified:
                        self.logger.info(f"Configuration file changed: {file_path}")

                        # Reload configuration
                        await self._reload_configuration_file(file_path)

                        # Notify watchers
                        await self._notify_configuration_watchers(file_path)

                        last_modified = current_modified
                        self.stats["hot_reloads"] += 1

                    # Wait before next check
                    await asyncio.sleep(1)

                except FileNotFoundError:
                    # File was deleted, stop watching
                    self.logger.warning(f"Configuration file deleted: {file_path}")
                    break
                except Exception as e:
                    self.logger.error(
                        f"Error watching configuration file {file_path}: {e}"
                    )
                    await asyncio.sleep(5)

        except Exception as e:
            self.logger.error(
                f"Error in configuration file watcher for {file_path}: {e}"
            )

    async def _reload_configuration_file(self, file_path: str) -> None:
        """Reload a configuration file."""
        try:
            # Reload the file
            await self._load_configuration_file(file_path)

            # Re - validate configurations
            await self._validate_all_configurations()

            self.logger.info(f"Configuration file reloaded: {file_path}")

        except Exception as e:
            self.logger.error(f"Error reloading configuration file {file_path}: {e}")

    async def _notify_configuration_watchers(self, file_path: str) -> None:
        """Notify configuration watchers of changes."""
        try:
            for watcher in self.watchers:
                try:
                    await watcher(file_path, self.config)
                except Exception as e:
                    self.logger.error(f"Error in configuration watcher: {e}")

        except Exception as e:
            self.logger.error(f"Error notifying configuration watchers: {e}")

    # Public methods
    def get_config(self, config_name: str, key: Optional[str] = None) -> Any:
        """Get configuration value."""
        try:
            if config_name not in self.config:
                return None

            config_data = self.config[config_name]

            if key is None:
                return config_data

            if isinstance(config_data, dict):
                return config_data.get(key)

            return None

        except Exception as e:
            self.logger.error(f"Error getting configuration {config_name}.{key}: {e}")
            return None

    def set_config(self, config_name: str, key: str, value: Any) -> None:
        """Set configuration value."""
        try:
            if config_name not in self.config:
                self.config[config_name] = {}

            self.config[config_name][key] = value

            self.logger.debug(f"Configuration set: {config_name}.{key} = {value}")

        except Exception as e:
            self.logger.error(f"Error setting configuration {config_name}.{key}: {e}")

    def add_configuration_watcher(self, watcher: Callable) -> None:
        """Add configuration watcher."""
        self.watchers.append(watcher)

    def remove_configuration_watcher(self, watcher: Callable) -> None:
        """Remove configuration watcher."""
        if watcher in self.watchers:
            self.watchers.remove(watcher)

    def get_all_configurations(self) -> Dict[str, Any]:
        """Get all configurations."""
        return self.config.copy()

    def get_configuration_schema(self, config_name: str) -> Optional[BaseModel]:
        """Get configuration schema."""
        return self.config_schemas.get(config_name)

    def get_statistics(self) -> Dict[str, Any]:
        """Get configuration manager statistics."""
        uptime = None
        if self.stats["start_time"]:
            uptime = (datetime.now() - self.stats["start_time"]).total_seconds()

        return {
            "uptime_seconds": uptime,
            "total_configurations": len(self.config),
            "watched_files": len(self.config_files),
            "active_watchers": len(self.watchers),
            "stats": self.stats.copy(),
        }

    async def save_configuration(
        self, config_name: str, file_path: Optional[str] = None
    ) -> bool:
        """Save configuration to file."""
        try:
            if config_name not in self.config:
                self.logger.error(f"Configuration not found: {config_name}")
                return False

            # Determine file path
            if file_path is None:
                file_path = f"{self.config_path}/{config_name}.yaml"

            # Save configuration
            with open(file_path, "w", encoding="utf - 8") as f:
                yaml.dump(
                    self.config[config_name], f, default_flow_style=False, indent=2
                )

            self.logger.info(f"Configuration saved: {file_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error saving configuration {config_name}: {e}")
            return False

    async def shutdown(self) -> None:
        """Shutdown the configuration manager."""
        try:
            self.logger.info("Shutting down configuration manager...")

            # Cancel all watch tasks
            for task in self.watch_tasks:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

            self.watch_tasks.clear()
            self.watchers.clear()

            self.logger.info("Configuration manager shutdown completed")

        except Exception as e:
            self.logger.error(f"Error during configuration manager shutdown: {e}")
