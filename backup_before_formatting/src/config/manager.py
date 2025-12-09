"""
Configuration Manager

Central configuration management system that coordinates loading, validation,
caching, hot - reloading, and distribution of configuration across the system.
"""

import asyncio
import hashlib
import json
import logging
import os
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Union

from .loader import ConfigFactory, ConfigLoader
from .models import SystemConfig
from .schema import ConfigSchema
from .validator import ConfigValidator, ValidationError

logger = logging.getLogger(__name__)


@dataclass
class ConfigMetadata:
    """Configuration metadata for tracking and auditing."""

    version: str
    environment: str
    loaded_at: datetime
    source_hash: str
    validation_errors: int
    validation_warnings: int
    last_modified: Optional[datetime] = None
    loaded_by: str = "system"


class ConfigManager:
    """
    Central configuration management system.

    Features:
    - Hierarchical configuration with inheritance
    - Environment - specific configurations
    - Hot - reload capabilities
    - Type validation and security
    - Configuration backup and rollback
    - Audit trail and monitoring
    """

    def __init__(self, environment: Optional[str] = None, config_dir: str = "config"):
        """
        Initialize the configuration manager.

        Args:
            environment: Target environment (auto - detected if None)
            config_dir: Configuration directory path
        """
        self.environment = environment or os.getenv("QUANT_ENV", "development")
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Core components
        self.loader = ConfigFactory.create_default_loader(self.environment)
        self.validator = ConfigValidator()
        self.schema = ConfigSchema()

        # Configuration cache and metadata
        self._config: Optional[SystemConfig] = None
        self._metadata: Optional[ConfigMetadata] = None
        self._config_hash: Optional[str] = None
        self._lock = threading.RLock()

        # Backup and rollback
        self._backup_dir = self.config_dir / "backups"
        self._backup_dir.mkdir(exist_ok=True)
        self._max_backups = 10

        # Hot - reload monitoring
        self._reload_callbacks: Dict[str, Callable] = {}
        self._monitoring_active = False
        self._monitor_thread: Optional[threading.Thread] = None

        # Load initial configuration
        self.reload_config()

    @property
    def config(self) -> SystemConfig:
        """Get current configuration."""
        if self._config is None:
            self.reload_config()
        return self._config

    @property
    def metadata(self) -> ConfigMetadata:
        """Get configuration metadata."""
        if self._metadata is None:
            self._create_metadata()
        return self._metadata

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key path.

        Args:
            key: Dot - separated key path (e.g., 'database.host')
            default: Default value if key not found

        Returns:
            Configuration value
        """
        try:
            keys = key.split(".")
            value = self.config

            for k in keys:
                if hasattr(value, k):
                    value = getattr(value, k)
                elif isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default

            return value
        except Exception:
            return default

    def reload_config(self) -> bool:
        """
        Reload configuration from all sources.

        Returns:
            True if reload was successful
        """
        try:
            with self._lock:
                # Load raw configuration
                raw_config = self.loader.load_config()

                # Validate configuration
                is_valid, errors, warnings = self.validator.validate_config(
                    raw_config, self.environment
                )

                if not is_valid:
                    logger.error(f"Configuration validation failed: {errors}")
                    # Create backup of current config if it exists
                    if self._config:
                        self._create_backup()
                    raise ValueError(f"Invalid configuration: {errors}")

                if warnings:
                    logger.warning(f"Configuration warnings: {warnings}")

                # Convert to typed configuration
                self._config = SystemConfig(**raw_config)

                # Update metadata
                self._create_metadata(raw_config, errors, warnings)

                # Calculate new hash
                self._config_hash = self._calculate_config_hash(raw_config)

                logger.info(
                    f"Configuration reloaded successfully for {self.environment}"
                )
                return True

        except Exception as e:
            logger.error(f"Failed to reload configuration: {e}")
            # Attempt to restore from backup if available
            if self._restore_from_backup():
                logger.info("Configuration restored from backup")
                return True
            return False

    def validate_current_config(self) -> tuple[bool, list, list]:
        """
        Validate current configuration.

        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        if self._config is None:
            return False, ["Configuration not loaded"], []

        raw_config = self.config.dict()
        return self.validator.validate_config(raw_config, self.environment)

    def update_config(self, updates: Dict[str, Any], persist: bool = False) -> bool:
        """
        Update configuration with new values.

        Args:
            updates: Configuration updates
            persist: Whether to persist changes to disk

        Returns:
            True if update was successful
        """
        try:
            with self._lock:
                # Create backup before update
                self._create_backup()

                # Apply updates to raw config
                raw_config = self.config.dict()
                self._apply_updates(raw_config, updates)

                # Validate updated configuration
                is_valid, errors, warnings = self.validator.validate_config(
                    raw_config, self.environment
                )

                if not is_valid:
                    logger.error(f"Configuration update validation failed: {errors}")
                    return False

                # Update configuration
                self._config = SystemConfig(**raw_config)
                self._create_metadata(raw_config, errors, warnings)

                # Persist changes if requested
                if persist:
                    self._persist_config(raw_config)

                logger.info("Configuration updated successfully")
                return True

        except Exception as e:
            logger.error(f"Failed to update configuration: {e}")
            return False

    def register_reload_callback(
        self, name: str, callback: Callable[[SystemConfig], None]
    ):
        """
        Register callback for configuration reload events.

        Args:
            name: Callback name
            callback: Callback function
        """
        self._reload_callbacks[name] = callback
        logger.debug(f"Registered reload callback: {name}")

    def unregister_reload_callback(self, name: str):
        """
        Unregister configuration reload callback.

        Args:
            name: Callback name to remove
        """
        if name in self._reload_callbacks:
            del self._reload_callbacks[name]
            logger.debug(f"Unregistered reload callback: {name}")

    def start_monitoring(self, interval: int = 30):
        """
        Start configuration monitoring for external changes.

        Args:
            interval: Monitoring interval in seconds
        """
        if self._monitoring_active:
            return

        self._monitoring_active = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_config_changes, args=(interval,), daemon=True
        )
        self._monitor_thread.start()
        logger.info("Configuration monitoring started")

    def stop_monitoring(self):
        """Stop configuration monitoring."""
        self._monitoring_active = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        logger.info("Configuration monitoring stopped")

    def get_config_history(self) -> list:
        """Get list of available configuration backups."""
        backups = []
        for backup_file in self._backup_dir.glob("config_backup_*.json"):
            timestamp = backup_file.stem.split("_")[-1]
            backups.append(
                {
                    "timestamp": timestamp,
                    "file": str(backup_file),
                    "created_at": datetime.fromisoformat(timestamp),
                }
            )

        return sorted(backups, key=lambda x: x["created_at"], reverse=True)

    def rollback_to_backup(self, backup_timestamp: str) -> bool:
        """
        Rollback configuration to a specific backup.

        Args:
            backup_timestamp: Backup timestamp to restore

        Returns:
            True if rollback was successful
        """
        backup_file = self._backup_dir / f"config_backup_{backup_timestamp}.json"

        if not backup_file.exists():
            logger.error(f"Backup file not found: {backup_file}")
            return False

        try:
            with open(backup_file, "r") as f:
                backup_config = json.load(f)

            # Validate backup configuration
            is_valid, errors, warnings = self.validator.validate_config(
                backup_config, self.environment
            )

            if not is_valid:
                logger.error(f"Backup configuration validation failed: {errors}")
                return False

            # Create backup of current config before rollback
            self._create_backup()

            # Restore configuration
            self._config = SystemConfig(**backup_config)
            self._create_metadata(backup_config, errors, warnings)

            logger.info(f"Configuration rolled back to backup: {backup_timestamp}")
            return True

        except Exception as e:
            logger.error(f"Failed to rollback configuration: {e}")
            return False

    def export_config(
        self, file_path: str, format: str = "yaml", include_secrets: bool = False
    ):
        """
        Export current configuration to file.

        Args:
            file_path: Output file path
            format: Export format ('yaml' or 'json')
            include_secrets: Whether to include sensitive values
        """
        config_dict = self.config.dict()

        if not include_secrets:
            config_dict = self._sanitize_config(config_dict)

        self.loader.save_config(config_dict, file_path, format)
        logger.info(f"Configuration exported to: {file_path}")

    def get_environment_info(self) -> Dict[str, Any]:
        """Get environment and system information."""
        return {
            "environment": self.environment,
            "config_version": self.metadata.version,
            "loaded_at": self.metadata.loaded_at.isoformat(),
            "source_hash": self.metadata.source_hash,
            "validation_errors": self.metadata.validation_errors,
            "validation_warnings": self.metadata.validation_warnings,
            "config_dir": str(self.config_dir),
            "monitoring_active": self._monitoring_active,
        }

    # Private methods

    def _create_metadata(
        self,
        raw_config: Optional[Dict[str, Any]] = None,
        errors: list = None,
        warnings: list = None,
    ):
        """Create configuration metadata."""
        if raw_config is None:
            raw_config = self.config.dict() if self.config else {}

        self._metadata = ConfigMetadata(
            version=raw_config.get("system", {}).get("version", "1.0.0"),
            environment=self.environment,
            loaded_at=datetime.now(),
            source_hash=self._calculate_config_hash(raw_config),
            validation_errors=len(errors or []),
            validation_warnings=len(warnings or []),
            loaded_by="system",
        )

    def _calculate_config_hash(self, config: Dict[str, Any]) -> str:
        """Calculate hash of configuration content."""
        config_str = json.dumps(config, sort_keys=True, default=str)
        return hashlib.sha256(config_str.encode()).hexdigest()[:16]

    def _apply_updates(self, config: Dict[str, Any], updates: Dict[str, Any]):
        """Apply updates to configuration dictionary."""
        for key, value in updates.items():
            if "." in key:
                keys = key.split(".")
                current = config
                for k in keys[:-1]:
                    if k not in current:
                        current[k] = {}
                    current = current[k]
                current[keys[-1]] = value
            else:
                config[key] = value

    def _persist_config(self, config: Dict[str, Any]):
        """Persist configuration to disk."""
        override_file = self.config_dir / "override.yaml"
        self.loader.save_config(config, str(override_file))

    def _sanitize_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive values from configuration."""
        sensitive_keys = ["password", "secret", "token", "key"]
        sanitized = config.copy()

        def sanitize_recursive(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if any(sensitive in key.lower() for sensitive in sensitive_keys):
                        obj[key] = "***REDACTED***"
                    else:
                        sanitize_recursive(value)
            elif isinstance(obj, list):
                for item in obj:
                    sanitize_recursive(item)

        sanitize_recursive(sanitized)
        return sanitized

    def _create_backup(self):
        """Create backup of current configuration."""
        if not self._config:
            return

        timestamp = datetime.now().isoformat()
        backup_file = self._backup_dir / f"config_backup_{timestamp}.json"

        with open(backup_file, "w") as f:
            json.dump(self.config.dict(), f, indent=2, default=str)

        # Cleanup old backups
        self._cleanup_old_backups()

        logger.debug(f"Configuration backup created: {backup_file}")

    def _cleanup_old_backups(self):
        """Remove old backups, keeping only the most recent ones."""
        backups = sorted(
            self._backup_dir.glob("config_backup_*.json"),
            key=lambda x: x.stat().st_mtime,
            reverse=True,
        )

        for backup in backups[self._max_backups :]:
            backup.unlink()
            logger.debug(f"Removed old backup: {backup}")

    def _restore_from_backup(self) -> bool:
        """Restore configuration from most recent backup."""
        backups = sorted(
            self._backup_dir.glob("config_backup_*.json"),
            key=lambda x: x.stat().st_mtime,
            reverse=True,
        )

        if not backups:
            return False

        latest_backup = backups[0]
        timestamp = latest_backup.stem.split("_")[-1]

        return self.rollback_to_backup(timestamp)

    def _monitor_config_changes(self, interval: int):
        """Monitor configuration for external changes."""
        logger.debug("Configuration monitoring thread started")

        while self._monitoring_active:
            try:
                time.sleep(interval)

                # Check for changes by comparing hash
                if self._config and self.loader:
                    raw_config = self.loader.load_config()
                    current_hash = self._calculate_config_hash(raw_config)

                    if current_hash != self._config_hash:
                        logger.info("Configuration change detected, reloading...")
                        self.reload_config()

                        # Call reload callbacks
                        for name, callback in self._reload_callbacks.items():
                            try:
                                callback(self._config)
                            except Exception as e:
                                logger.error(f"Error in reload callback {name}: {e}")

            except Exception as e:
                logger.error(f"Error in configuration monitoring: {e}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop_monitoring()
        self.loader.stop_hot_reload()
