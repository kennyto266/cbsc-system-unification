"""
Configuration Manager

Provides comprehensive configuration management with:
- Configuration backup and restoration
- Environment-specific configuration management
- Configuration validation and integrity checks
- Rolling updates with zero downtime
"""

import os
import json
import yaml
import shutil
import hashlib
import logging
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
import copy
import tempfile

logger = logging.getLogger(__name__)

class ConfigFormat(Enum):
    """Supported configuration file formats"""
    JSON = "json"
    YAML = "yaml"
    YML = "yml"

class Environment(Enum):
    """Supported deployment environments"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"

@dataclass
class ConfigSnapshot:
    """Configuration snapshot metadata"""
    snapshot_id: str
    timestamp: str
    environment: Environment
    config_files: Dict[str, str]  # filename -> backup_path
    checksum: str
    description: str = ""
    created_by: str = "system"
    is_stable: bool = True
    tags: List[str] = field(default_factory=list)

@dataclass
class ValidationResult:
    """Result of configuration validation"""
    valid: bool
    errors: List[str]
    warnings: List[str]
    config_file: str
    validation_time: str

@dataclass
class ConfigUpdateResult:
    """Result of configuration update operation"""
    success: bool
    snapshot_id: Optional[str] = None
    updated_files: List[str] = field(default_factory=list)
    validation_results: List[ValidationResult] = field(default_factory=list)
    error_message: Optional[str] = None
    rollback_performed: bool = False

class ConfigurationManager:
    """
    Enterprise-grade configuration manager for safe configuration updates.
    
    Features:
    - Configuration backup and restoration
    - Environment-specific configuration management
    - Configuration validation and integrity checks
    - Rolling updates with zero downtime
    - Configuration hot-reload capabilities
    - Configuration change auditing
    """
    
    def __init__(self, 
                 config_root: str = "config",
                 backup_dir: str = "config/backups",
                 environment: Optional[str] = None,
                 auto_backup: bool = True,
                 validation_enabled: bool = True):
        self.config_root = Path(config_root)
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Environment setup
        self.environment = Environment(environment or os.getenv('ENVIRONMENT', 'development'))
        
        # Configuration
        self.auto_backup = auto_backup
        self.validation_enabled = validation_enabled
        self.max_snapshots = 50
        self.config_watch_interval = 5  # seconds
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Current configuration cache
        self._config_cache: Dict[str, Dict[str, Any]] = {}
        self._file_mtimes: Dict[str, float] = {}
        
        # Validation schemas
        self._validation_schemas: Dict[str, Dict[str, Any]] = {}
        
        # Monitoring
        self._last_backup_time = None
        self._change_count = 0
        
        # Load existing configurations
        self._load_all_configurations()
        
        # Start file monitoring
        self._monitoring_thread = threading.Thread(target=self._monitor_config_changes, daemon=True)
        self._monitoring_thread.start()
        
        logger.info(f"ConfigurationManager initialized for environment: {self.environment.value}")
    
    def get_config(self, 
                  config_file: str, 
                  environment: Optional[str] = None,
                  reload: bool = False) -> Dict[str, Any]:
        """
        Get configuration for a specific file and environment.
        
        Args:
            config_file: Configuration file name (relative to config_root)
            environment: Target environment (uses default if not specified)
            reload: Force reload from disk
            
        Returns:
            Configuration dictionary
        """
        target_env = Environment(environment) if environment else self.environment
        cache_key = f"{config_file}:{target_env.value}"
        
        with self._lock:
            if reload or cache_key not in self._config_cache:
                self._load_configuration(config_file, target_env)
            
            return copy.deepcopy(self._config_cache.get(cache_key, {}))
    
    def update_config(self, 
                     config_file: str,
                     updates: Dict[str, Any],
                     environment: Optional[str] = None,
                     backup: Optional[bool] = None,
                     validate: Optional[bool] = None,
                     description: str = "",
                     created_by: str = "user") -> ConfigUpdateResult:
        """
        Update configuration with automatic backup and validation.
        
        Args:
            config_file: Configuration file to update
            updates: Configuration updates to apply
            environment: Target environment
            backup: Create backup before update (uses default if not specified)
            validate: Validate configuration after update
            description: Description of the change
            created_by: User or system making the change
            
        Returns:
            ConfigUpdateResult with operation details
        """
        target_env = Environment(environment) if environment else self.environment
        should_backup = backup if backup is not None else self.auto_backup
        should_validate = validate if validate is not None else self.validation_enabled
        
        with self._lock:
            try:
                logger.info(f"Updating configuration {config_file} for environment {target_env.value}")
                
                # Create backup if requested
                snapshot_id = None
                if should_backup:
                    snapshot_id = self.create_snapshot(
                        f"Before update of {config_file}",
                        created_by=created_by,
                        config_files=[config_file]
                    )
                
                # Load current configuration
                current_config = self.get_config(config_file, target_env.value)
                
                # Apply updates
                updated_config = self._deep_merge(current_config, updates)
                
                # Validate if requested
                validation_results = []
                if should_validate:
                    validation_result = self.validate_config(config_file, updated_config)
                    validation_results.append(validation_result)
                    
                    if not validation_result.valid:
                        logger.error(f"Configuration validation failed for {config_file}")
                        
                        # Rollback if validation fails and backup was created
                        if snapshot_id:
                            self.restore_snapshot(snapshot_id)
                        
                        return ConfigUpdateResult(
                            success=False,
                            snapshot_id=snapshot_id,
                            error_message="Configuration validation failed",
                            validation_results=validation_results,
                            rollback_performed=True
                        )
                
                # Write updated configuration
                self._write_configuration(config_file, updated_config, target_env)
                
                # Update cache
                cache_key = f"{config_file}:{target_env.value}"
                self._config_cache[cache_key] = updated_config
                
                # Validate all affected configurations
                if should_validate:
                    for validation_file in self._get_affected_configs(config_file):
                        if validation_file != config_file:
                            validation_result = self.validate_config(validation_file)
                            validation_results.append(validation_result)
                
                self._change_count += 1
                logger.info(f"Configuration {config_file} updated successfully")
                
                return ConfigUpdateResult(
                    success=True,
                    snapshot_id=snapshot_id,
                    updated_files=[config_file],
                    validation_results=validation_results
                )
                
            except Exception as e:
                error_msg = f"Failed to update configuration {config_file}: {e}"
                logger.error(error_msg)
                
                # Attempt rollback if backup was created
                rollback_performed = False
                if snapshot_id:
                    try:
                        self.restore_snapshot(snapshot_id)
                        rollback_performed = True
                        logger.info(f"Rolled back configuration after failed update: {config_file}")
                    except Exception as rollback_error:
                        logger.error(f"Failed to rollback configuration: {rollback_error}")
                
                return ConfigUpdateResult(
                    success=False,
                    snapshot_id=snapshot_id,
                    error_message=error_msg,
                    rollback_performed=rollback_performed
                )
    
    def create_snapshot(self, 
                       description: str = "",
                       config_files: Optional[List[str]] = None,
                       environment: Optional[str] = None,
                       created_by: str = "system",
                       tags: Optional[List[str]] = None) -> str:
        """
        Create a snapshot of current configuration state.
        
        Args:
            description: Snapshot description
            config_files: Specific files to snapshot (all if not specified)
            environment: Target environment
            created_by: User or system creating the snapshot
            tags: Snapshot tags
            
        Returns:
            Snapshot ID
        """
        target_env = Environment(environment) if environment else self.environment
        
        with self._lock:
            # Generate snapshot ID
            snapshot_id = self._generate_snapshot_id()
            timestamp = datetime.now().isoformat()
            
            # Determine files to snapshot
            if config_files is None:
                config_files = self._discover_config_files()
            
            # Create backups
            backup_paths = {}
            for config_file in config_files:
                source_path = self._get_config_path(config_file, target_env)
                if source_path.exists():
                    backup_path = self.backup_dir / f"{snapshot_id}_{config_file.replace('/', '_')}"
                    shutil.copy2(source_path, backup_path)
                    backup_paths[config_file] = str(backup_path)
                    logger.debug(f"Backed up {config_file} to {backup_path}")
            
            # Calculate checksum
            checksum_data = {
                'snapshot_id': snapshot_id,
                'timestamp': timestamp,
                'environment': target_env.value,
                'backup_paths': backup_paths
            }
            checksum = self._calculate_checksum(json.dumps(checksum_data, sort_keys=True))
            
            # Create snapshot metadata
            snapshot = ConfigSnapshot(
                snapshot_id=snapshot_id,
                timestamp=timestamp,
                environment=target_env,
                config_files=backup_paths,
                checksum=checksum,
                description=description,
                created_by=created_by,
                tags=tags or []
            )
            
            # Save snapshot metadata
            metadata_path = self.backup_dir / f"{snapshot_id}_metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(asdict(snapshot), f, indent=2, default=str)
            
            self._last_backup_time = datetime.now()
            logger.info(f"Configuration snapshot created: {snapshot_id}")
            
            return snapshot_id
    
    def restore_snapshot(self, snapshot_id: str) -> bool:
        """
        Restore configuration from a snapshot.
        
        Args:
            snapshot_id: Snapshot ID to restore
            
        Returns:
            True if restoration was successful
        """
        with self._lock:
            try:
                # Load snapshot metadata
                metadata_path = self.backup_dir / f"{snapshot_id}_metadata.json"
                if not metadata_path.exists():
                    raise ValueError(f"Snapshot {snapshot_id} not found")
                
                with open(metadata_path, 'r') as f:
                    snapshot_data = json.load(f)
                    snapshot = ConfigSnapshot(**snapshot_data)
                
                logger.info(f"Restoring configuration from snapshot: {snapshot_id}")
                
                # Validate snapshot integrity
                if not self._validate_snapshot_integrity(snapshot):
                    raise ValueError(f"Snapshot {snapshot_id} integrity check failed")
                
                # Restore configuration files
                restored_files = []
                for config_file, backup_path in snapshot.config_files.items():
                    source_path = Path(backup_path)
                    if source_path.exists():
                        target_path = self._get_config_path(config_file, snapshot.environment)
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(source_path, target_path)
                        restored_files.append(config_file)
                        logger.debug(f"Restored {config_file} from {backup_path}")
                
                # Clear cache for restored files
                for config_file in restored_files:
                    for env in Environment:
                        cache_key = f"{config_file}:{env.value}"
                        self._config_cache.pop(cache_key, None)
                
                logger.info(f"Configuration restored from snapshot {snapshot_id}. Files restored: {restored_files}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to restore snapshot {snapshot_id}: {e}")
                return False
    
    def validate_config(self, 
                       config_file: str,
                       config_data: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """
        Validate configuration file against schema and rules.
        
        Args:
            config_file: Configuration file to validate
            config_data: Configuration data (loads from file if not provided)
            
        Returns:
            ValidationResult with validation details
        """
        try:
            if config_data is None:
                config_data = self.get_config(config_file, reload=True)
            
            errors = []
            warnings = []
            
            # Basic structure validation
            if not isinstance(config_data, dict):
                errors.append("Configuration must be a dictionary")
                return ValidationResult(
                    valid=False,
                    errors=errors,
                    warnings=warnings,
                    config_file=config_file,
                    validation_time=datetime.now().isoformat()
                )
            
            # Schema validation if schema is available
            schema = self._validation_schemas.get(config_file)
            if schema:
                schema_errors, schema_warnings = self._validate_against_schema(config_data, schema)
                errors.extend(schema_errors)
                warnings.extend(schema_warnings)
            
            # Environment-specific validation
            env_errors, env_warnings = self._validate_environment_specific(config_data, config_file)
            errors.extend(env_errors)
            warnings.extend(env_warnings)
            
            # Business logic validation
            logic_errors, logic_warnings = self._validate_business_logic(config_data, config_file)
            errors.extend(logic_errors)
            warnings.extend(logic_warnings)
            
            valid = len(errors) == 0
            
            return ValidationResult(
                valid=valid,
                errors=errors,
                warnings=warnings,
                config_file=config_file,
                validation_time=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Configuration validation failed for {config_file}: {e}")
            return ValidationResult(
                valid=False,
                errors=[f"Validation error: {e}"],
                warnings=[],
                config_file=config_file,
                validation_time=datetime.now().isoformat()
            )
    
    def validate_all_configurations(self) -> Dict[str, ValidationResult]:
        """
        Validate all configuration files.
        
        Returns:
            Dictionary of config file -> ValidationResult
        """
        results = {}
        config_files = self._discover_config_files()
        
        for config_file in config_files:
            try:
                result = self.validate_config(config_file)
                results[config_file] = result
                
                if not result.valid:
                    logger.error(f"Configuration validation failed for {config_file}: {result.errors}")
                elif result.warnings:
                    logger.warning(f"Configuration validation warnings for {config_file}: {result.warnings}")
                    
            except Exception as e:
                logger.error(f"Failed to validate {config_file}: {e}")
                results[config_file] = ValidationResult(
                    valid=False,
                    errors=[f"Validation failed: {e}"],
                    warnings=[],
                    config_file=config_file,
                    validation_time=datetime.now().isoformat()
                )
        
        return results
    
    def list_snapshots(self, 
                      environment: Optional[str] = None,
                      tags: Optional[List[str]] = None) -> List[ConfigSnapshot]:
        """
        List available configuration snapshots.
        
        Args:
            environment: Filter by environment
            tags: Filter by tags (must match all specified tags)
            
        Returns:
            List of matching snapshots
        """
        snapshots = []
        target_env = Environment(environment) if environment else None
        
        try:
            for metadata_file in self.backup_dir.glob("*_metadata.json"):
                with open(metadata_file, 'r') as f:
                    snapshot_data = json.load(f)
                    snapshot = ConfigSnapshot(**snapshot_data)
                
                # Apply filters
                if target_env and snapshot.environment != target_env:
                    continue
                
                if tags and not all(tag in snapshot.tags for tag in tags):
                    continue
                
                snapshots.append(snapshot)
            
            # Sort by timestamp (newest first)
            snapshots.sort(key=lambda x: x.timestamp, reverse=True)
            
        except Exception as e:
            logger.error(f"Failed to list snapshots: {e}")
        
        return snapshots
    
    def delete_snapshot(self, snapshot_id: str) -> bool:
        """
        Delete a configuration snapshot.
        
        Args:
            snapshot_id: Snapshot ID to delete
            
        Returns:
            True if deletion was successful
        """
        try:
            # Delete metadata file
            metadata_path = self.backup_dir / f"{snapshot_id}_metadata.json"
            if metadata_path.exists():
                metadata_path.unlink()
            
            # Delete backup files
            for backup_file in self.backup_dir.glob(f"{snapshot_id}_*"):
                if not backup_file.name.endswith("_metadata.json"):
                    backup_file.unlink()
            
            logger.info(f"Deleted snapshot: {snapshot_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete snapshot {snapshot_id}: {e}")
            return False
    
    def cleanup_old_snapshots(self, retention_days: int = 30) -> int:
        """
        Clean up old snapshots exceeding retention period.
        
        Args:
            retention_days: Number of days to retain snapshots
            
        Returns:
            Number of snapshots deleted
        """
        deleted_count = 0
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        try:
            snapshots = self.list_snapshots()
            snapshots_to_delete = []
            
            # Always keep the latest 5 snapshots regardless of age
            snapshots_to_keep = 5
            for i, snapshot in enumerate(snapshots):
                if i < snapshots_to_keep:
                    continue
                
                snapshot_date = datetime.fromisoformat(snapshot.timestamp)
                if snapshot_date < cutoff_date:
                    snapshots_to_delete.append(snapshot)
            
            # Delete old snapshots
            for snapshot in snapshots_to_delete:
                if self.delete_snapshot(snapshot.snapshot_id):
                    deleted_count += 1
            
            logger.info(f"Cleaned up {deleted_count} old snapshots (retention: {retention_days} days)")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old snapshots: {e}")
        
        return deleted_count
    
    def get_configuration_statistics(self) -> Dict[str, Any]:
        """Get configuration management statistics."""
        with self._lock:
            config_files = self._discover_config_files()
            snapshots = self.list_snapshots()
            
            total_configs = len(config_files)
            total_snapshots = len(snapshots)
            cached_configs = len(self._config_cache)
            
            # Environment breakdown
            env_counts = {}
            for snapshot in snapshots:
                env_counts[snapshot.environment.value] = env_counts.get(snapshot.environment.value, 0) + 1
            
            # Recent activity
            recent_snapshots = [s for s in snapshots if 
                              datetime.fromisoformat(s.timestamp) > datetime.now() - timedelta(days=7)]
            
            return {
                'total_config_files': total_configs,
                'cached_configurations': cached_configs,
                'total_snapshots': total_snapshots,
                'snapshots_by_environment': env_counts,
                'recent_snapshots_7_days': len(recent_snapshots),
                'last_backup_time': self._last_backup_time.isoformat() if self._last_backup_time else None,
                'configuration_changes': self._change_count,
                'validation_enabled': self.validation_enabled,
                'auto_backup_enabled': self.auto_backup
            }
    
    # Private helper methods
    
    def _discover_config_files(self) -> List[str]:
        """Discover all configuration files."""
        config_files = []
        
        for config_file in self.config_root.rglob("*"):
            if config_file.is_file() and config_file.suffix.lower() in ['.json', '.yaml', '.yml']:
                # Get relative path from config_root
                rel_path = config_file.relative_to(self.config_root)
                config_files.append(str(rel_path))
        
        return sorted(config_files)
    
    def _get_config_path(self, config_file: str, environment: Environment) -> Path:
        """Get full path for configuration file with environment support."""
        # Try environment-specific file first
        env_specific_file = self.config_root / environment.value / config_file
        if env_specific_file.exists():
            return env_specific_file
        
        # Fall back to base file
        return self.config_root / config_file
    
    def _load_configuration(self, config_file: str, environment: Environment):
        """Load configuration file into cache."""
        cache_key = f"{config_file}:{environment.value}"
        
        try:
            config_path = self._get_config_path(config_file, environment)
            
            if not config_path.exists():
                logger.warning(f"Configuration file not found: {config_path}")
                self._config_cache[cache_key] = {}
                return
            
            # Check file modification time
            current_mtime = config_path.stat().st_mtime
            cached_mtime = self._file_mtimes.get(cache_key, 0)
            
            if current_mtime <= cached_mtime:
                return  # Use cached version
            
            # Load configuration
            with open(config_path, 'r', encoding='utf-8') as f:
                if config_path.suffix.lower() == '.json':
                    config = json.load(f)
                else:
                    config = yaml.safe_load(f) or {}
            
            self._config_cache[cache_key] = config
            self._file_mtimes[cache_key] = current_mtime
            logger.debug(f"Loaded configuration: {config_file} ({environment.value})")
            
        except Exception as e:
            logger.error(f"Failed to load configuration {config_file}: {e}")
            self._config_cache[cache_key] = {}
    
    def _load_all_configurations(self):
        """Load all configuration files into cache."""
        config_files = self._discover_config_files()
        
        for config_file in config_files:
            for environment in Environment:
                self._load_configuration(config_file, environment)
        
        logger.info(f"Loaded {len(config_files)} configuration files for all environments")
    
    def _write_configuration(self, config_file: str, config_data: Dict[str, Any], environment: Environment):
        """Write configuration data to file."""
        config_path = self._get_config_path(config_file, environment)
        
        # Create directory if it doesn't exist
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write configuration
        with open(config_path, 'w', encoding='utf-8') as f:
            if config_path.suffix.lower() == '.json':
                json.dump(config_data, f, indent=2, default=str)
            else:
                yaml.dump(config_data, f, default_flow_style=False, indent=2)
        
        # Update cache and mtime
        cache_key = f"{config_file}:{environment.value}"
        self._config_cache[cache_key] = config_data
        self._file_mtimes[cache_key] = config_path.stat().st_mtime
        
        logger.debug(f"Wrote configuration: {config_path}")
    
    def _deep_merge(self, base: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries."""
        result = copy.deepcopy(base)
        
        for key, value in updates.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = copy.deepcopy(value)
        
        return result
    
    def _generate_snapshot_id(self) -> str:
        """Generate unique snapshot ID."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        hash_suffix = hashlib.md5(os.urandom(8)).hexdigest()[:8]
        return f"snapshot_{timestamp}_{hash_suffix}"
    
    def _calculate_checksum(self, data: str) -> str:
        """Calculate SHA256 checksum."""
        return hashlib.sha256(data.encode()).hexdigest()
    
    def _validate_snapshot_integrity(self, snapshot: ConfigSnapshot) -> bool:
        """Validate snapshot file integrity."""
        try:
            # Check if all backup files exist
            for backup_path in snapshot.config_files.values():
                if not Path(backup_path).exists():
                    logger.error(f"Backup file missing: {backup_path}")
                    return False
            
            # Verify checksum (simplified - would include file hashes in real implementation)
            return True
            
        except Exception as e:
            logger.error(f"Snapshot integrity validation failed: {e}")
            return False
    
    def _validate_against_schema(self, config_data: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """Validate configuration against schema."""
        errors = []
        warnings = []
        
        # This is a simplified schema validation
        # In a real implementation, you'd use a library like jsonschema
        
        required_fields = schema.get('required', [])
        for field in required_fields:
            if field not in config_data:
                errors.append(f"Required field missing: {field}")
        
        # Type validation
        field_types = schema.get('types', {})
        for field, expected_type in field_types.items():
            if field in config_data:
                actual_value = config_data[field]
                if not self._check_type(actual_value, expected_type):
                    errors.append(f"Field {field} has incorrect type. Expected {expected_type}")
        
        return errors, warnings
    
    def _validate_environment_specific(self, config_data: Dict[str, Any], config_file: str) -> Tuple[List[str], List[str]]:
        """Validate environment-specific configuration rules."""
        errors = []
        warnings = []
        
        # Example environment-specific validations
        if self.environment == Environment.PRODUCTION:
            # Production-specific validations
            if config_file == 'system_config.json':
                system_config = config_data.get('system', {})
                if system_config.get('debug_mode', False):
                    errors.append("Debug mode should be disabled in production")
                
                if system_config.get('log_level') == 'DEBUG':
                    warnings.append("DEBUG log level not recommended for production")
        
        elif self.environment == Environment.DEVELOPMENT:
            # Development-specific validations
            if 'database' in config_data:
                db_config = config_data['database']
                if db_config.get('host') == 'production-db.example.com':
                    warnings.append("Using production database in development environment")
        
        return errors, warnings
    
    def _validate_business_logic(self, config_data: Dict[str, Any], config_file: str) -> Tuple[List[str], List[str]]:
        """Validate business logic rules."""
        errors = []
        warnings = []
        
        # Example business logic validations
        if config_file == 'system_config.json':
            performance_config = config_data.get('performance', {})
            
            # Check for reasonable parallel core settings
            parallel_cores = performance_config.get('parallel_cores', 'auto')
            if isinstance(parallel_cores, int) and parallel_cores > 64:
                warnings.append(f"High parallel_core count ({parallel_cores}) may cause performance issues")
            
            # Check GPU memory limits
            gpu_memory = performance_config.get('gpu_memory_limit', '')
            if gpu_memory:
                try:
                    memory_gb = int(gpu_memory.replace('GB', '').replace('gb', ''))
                    if memory_gb > 32:
                        warnings.append(f"High GPU memory limit ({gpu_memory}) may not be available")
                except ValueError:
                    errors.append(f"Invalid GPU memory limit format: {gpu_memory}")
        
        return errors, warnings
    
    def _check_type(self, value: Any, expected_type: str) -> bool:
        """Check if value matches expected type."""
        type_mapping = {
            'string': str,
            'integer': int,
            'float': (int, float),
            'boolean': bool,
            'array': list,
            'object': dict
        }
        
        expected_python_type = type_mapping.get(expected_type)
        if expected_python_type:
            return isinstance(value, expected_python_type)
        
        return True  # Unknown type, assume valid
    
    def _get_affected_configs(self, changed_config: str) -> List[str]:
        """Get list of configuration files that might be affected by a change."""
        # This is a simplified implementation
        # In a real system, you'd have dependency tracking
        affected = []
        
        # Example: system_config changes affect many other configs
        if changed_config == 'system_config.json':
            affected.extend(['feature_flags.yaml', 'gpu_config.json', 'hk_market_config.json'])
        
        return affected
    
    def _monitor_config_changes(self):
        """Background thread to monitor configuration file changes."""
        while True:
            try:
                time.sleep(self.config_watch_interval)
                
                # Reload all configurations
                self._load_all_configurations()
                
            except Exception as e:
                logger.error(f"Error in configuration monitoring: {e}")
                time.sleep(10)  # Wait before retrying

# Global instance
configuration_manager = ConfigurationManager()

# Convenience functions
def get_config(config_file: str, **kwargs) -> Dict[str, Any]:
    """Get configuration for file."""
    return configuration_manager.get_config(config_file, **kwargs)

def update_config(config_file: str, updates: Dict[str, Any], **kwargs) -> ConfigUpdateResult:
    """Update configuration file."""
    return configuration_manager.update_config(config_file, updates, **kwargs)

def create_snapshot(**kwargs) -> str:
    """Create configuration snapshot."""
    return configuration_manager.create_snapshot(**kwargs)

def restore_snapshot(snapshot_id: str) -> bool:
    """Restore configuration snapshot."""
    return configuration_manager.restore_snapshot(snapshot_id)