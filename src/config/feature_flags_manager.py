"""
Feature Flags Manager

Provides runtime feature flag control without restart with:
- Runtime feature flag control without restart
- Emergency disable capabilities for all new features
- Gradual rollout control with percentage-based deployment
- A/B testing support for new features
- Real-time flag status monitoring
"""

import os
import json
import yaml
import logging
import threading
import time
import hashlib
from datetime import datetime, timedelta
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import random

logger = logging.getLogger(__name__)

class FlagType(Enum):
    """Types of feature flags"""
    BOOLEAN = "boolean"
    PERCENTAGE = "percentage"
    WHITELIST = "whitelist"
    CONDITIONAL = "conditional"

class RolloutStrategy(Enum):
    """Feature rollout strategies"""
    IMMEDIATE = "immediate"
    GRADUAL = "gradual"
    SCHEDULED = "scheduled"
    CONDITIONAL = "conditional"

@dataclass
class FeatureFlag:
    """Feature flag definition"""
    name: str
    flag_type: FlagType
    enabled: bool
    value: Any = None
    rollout_percentage: int = 0
    whitelist: List[str] = None
    conditions: Dict[str, Any] = None
    rollout_strategy: RolloutStrategy = RolloutStrategy.IMMEDIATE
    description: str = ""
    tags: List[str] = None
    emergency_disable: bool = False
    last_modified: str = ""
    modified_by: str = "system"
    
    def __post_init__(self):
        if self.whitelist is None:
            self.whitelist = []
        if self.conditions is None:
            self.conditions = {}
        if self.tags is None:
            self.tags = []
        if not self.last_modified:
            self.last_modified = datetime.now().isoformat()

@dataclass
class FlagEvaluationResult:
    """Result of feature flag evaluation"""
    flag_name: str
    enabled: bool
    value: Any
    reason: str
    evaluation_time: float
    context: Dict[str, Any] = None

class FeatureFlagsManager:
    """
    Enterprise-grade feature flags manager for runtime feature control.
    
    Features:
    - Runtime feature flag control without restart
    - Emergency disable capabilities for all new features
    - Gradual rollout control with percentage-based deployment
    - A/B testing support for new features
    - Real-time flag status monitoring
    """
    
    def __init__(self, config_path: str = "config/feature_flags.yaml"):
        self.config_path = Path(config_path)
        self.flags: Dict[str, FeatureFlag] = {}
        self._lock = threading.RLock()
        
        # Hot-reload monitoring
        self._config_mtime = 0
        self._last_reload = time.time()
        self._reload_interval = 5  # Check every 5 seconds
        
        # Evaluation context
        self._default_context = {
            'user_id': None,
            'environment': os.getenv('ENVIRONMENT', 'development'),
            'version': os.getenv('APP_VERSION', '1.0.0'),
            'instance_id': os.getenv('INSTANCE_ID', 'default'),
            'request_id': None,
            'timestamp': datetime.now().isoformat()
        }
        
        # Initialize
        self._load_flags()
        
        # Start background monitoring thread
        self._monitoring_thread = threading.Thread(target=self._monitor_config_changes, daemon=True)
        self._monitoring_thread.start()
        
        logger.info(f"FeatureFlagsManager initialized with config: {config_path}")
    
    def is_enabled(self, 
                  flag_name: str, 
                  context: Optional[Dict[str, Any]] = None,
                  default: bool = False) -> bool:
        """
        Check if a feature flag is enabled for given context.
        
        Args:
            flag_name: Name of the feature flag
            context: Evaluation context (user_id, environment, etc.)
            default: Default value if flag doesn't exist
            
        Returns:
            True if feature is enabled for the context
        """
        result = self.evaluate_flag(flag_name, context, default)
        return result.enabled
    
    def evaluate_flag(self, 
                     flag_name: str, 
                     context: Optional[Dict[str, Any]] = None,
                     default: Any = False) -> FlagEvaluationResult:
        """
        Evaluate a feature flag with detailed result information.
        
        Args:
            flag_name: Name of the feature flag
            context: Evaluation context
            default: Default value if flag doesn't exist
            
        Returns:
            FlagEvaluationResult with evaluation details
        """
        start_time = time.time()
        
        with self._lock:
            # Load latest configuration
            self._check_and_reload()
            
            # Merge context
            eval_context = {**self._default_context}
            if context:
                eval_context.update(context)
            eval_context['timestamp'] = datetime.now().isoformat()
            
            # Get flag
            flag = self.flags.get(flag_name)
            if not flag:
                return FlagEvaluationResult(
                    flag_name=flag_name,
                    enabled=default,
                    value=default,
                    reason=f"Flag not found, using default: {default}",
                    evaluation_time=time.time() - start_time,
                    context=eval_context.copy()
                )
            
            # Emergency disable check
            if flag.emergency_disable:
                logger.warning(f"Emergency disable active for flag: {flag_name}")
                return FlagEvaluationResult(
                    flag_name=flag_name,
                    enabled=False,
                    value=False,
                    reason="Emergency disable activated",
                    evaluation_time=time.time() - start_time,
                    context=eval_context.copy()
                )
            
            # Evaluate based on flag type
            if not flag.enabled:
                enabled = False
                value = False
                reason = "Flag disabled globally"
            elif flag.flag_type == FlagType.BOOLEAN:
                enabled = flag.value if flag.value is not None else flag.enabled
                value = enabled
                reason = "Boolean flag evaluation"
            elif flag.flag_type == FlagType.PERCENTAGE:
                enabled, reason = self._evaluate_percentage_flag(flag, eval_context)
                value = enabled
            elif flag.flag_type == FlagType.WHITELIST:
                enabled, reason = self._evaluate_whitelist_flag(flag, eval_context)
                value = enabled
            elif flag.flag_type == FlagType.CONDITIONAL:
                enabled, value, reason = self._evaluate_conditional_flag(flag, eval_context)
            else:
                enabled = flag.enabled
                value = flag.value
                reason = "Unknown flag type, using default behavior"
            
            return FlagEvaluationResult(
                flag_name=flag_name,
                enabled=enabled,
                value=value,
                reason=reason,
                evaluation_time=time.time() - start_time,
                context=eval_context.copy()
            )
    
    def enable_flag(self, 
                   flag_name: str, 
                   value: Any = True,
                   modified_by: str = "user") -> bool:
        """
        Enable a feature flag.
        
        Args:
            flag_name: Name of the flag to enable
            value: Value to set (for non-boolean flags)
            modified_by: User or system making the change
            
        Returns:
            True if flag was enabled successfully
        """
        with self._lock:
            if flag_name not in self.flags:
                logger.error(f"Flag {flag_name} not found")
                return False
            
            flag = self.flags[flag_name]
            flag.enabled = True
            flag.value = value
            flag.last_modified = datetime.now().isoformat()
            flag.modified_by = modified_by
            
            self._save_flags()
            logger.info(f"Flag {flag_name} enabled by {modified_by}")
            return True
    
    def disable_flag(self, 
                    flag_name: str, 
                    modified_by: str = "user") -> bool:
        """
        Disable a feature flag.
        
        Args:
            flag_name: Name of the flag to disable
            modified_by: User or system making the change
            
        Returns:
            True if flag was disabled successfully
        """
        with self._lock:
            if flag_name not in self.flags:
                logger.error(f"Flag {flag_name} not found")
                return False
            
            flag = self.flags[flag_name]
            flag.enabled = False
            flag.last_modified = datetime.now().isoformat()
            flag.modified_by = modified_by
            
            self._save_flags()
            logger.info(f"Flag {flag_name} disabled by {modified_by}")
            return True
    
    def emergency_disable_all(self, modified_by: str = "emergency_system") -> int:
        """
        Emergency disable all feature flags.
        
        Args:
            modified_by: System or user performing emergency disable
            
        Returns:
            Number of flags that were disabled
        """
        with self._lock:
            disabled_count = 0
            
            for flag_name, flag in self.flags.items():
                if flag.enabled:
                    flag.enabled = False
                    flag.emergency_disable = True
                    flag.last_modified = datetime.now().isoformat()
                    flag.modified_by = modified_by
                    disabled_count += 1
            
            self._save_flags()
            logger.critical(f"EMERGENCY DISABLE ALL FLAGS: {disabled_count} flags disabled by {modified_by}")
            return disabled_count
    
    def set_emergency_disable(self, 
                            flag_name: str, 
                            emergency_disable: bool = True,
                            modified_by: str = "emergency_system") -> bool:
        """
        Set emergency disable status for a specific flag.
        
        Args:
            flag_name: Name of the flag
            emergency_disable: Whether to emergency disable the flag
            modified_by: System or user making the change
            
        Returns:
            True if operation was successful
        """
        with self._lock:
            if flag_name not in self.flags:
                logger.error(f"Flag {flag_name} not found")
                return False
            
            flag = self.flags[flag_name]
            flag.emergency_disable = emergency_disable
            flag.last_modified = datetime.now().isoformat()
            flag.modified_by = modified_by
            
            if emergency_disable:
                flag.enabled = False
            
            self._save_flags()
            
            if emergency_disable:
                logger.critical(f"EMERGENCY DISABLE ACTIVATED for flag: {flag_name} by {modified_by}")
            else:
                logger.info(f"Emergency disable cleared for flag: {flag_name} by {modified_by}")
            
            return True
    
    def create_flag(self, 
                   flag_name: str,
                   flag_type: FlagType,
                   enabled: bool = False,
                   **kwargs) -> bool:
        """
        Create a new feature flag.
        
        Args:
            flag_name: Name of the new flag
            flag_type: Type of the flag
            enabled: Initial enabled state
            **kwargs: Additional flag parameters
            
        Returns:
            True if flag was created successfully
        """
        with self._lock:
            if flag_name in self.flags:
                logger.error(f"Flag {flag_name} already exists")
                return False
            
            flag = FeatureFlag(
                name=flag_name,
                flag_type=flag_type,
                enabled=enabled,
                **kwargs
            )
            
            self.flags[flag_name] = flag
            self._save_flags()
            logger.info(f"Created new flag: {flag_name} ({flag_type.value})")
            return True
    
    def delete_flag(self, flag_name: str) -> bool:
        """
        Delete a feature flag.
        
        Args:
            flag_name: Name of the flag to delete
            
        Returns:
            True if flag was deleted successfully
        """
        with self._lock:
            if flag_name not in self.flags:
                logger.error(f"Flag {flag_name} not found")
                return False
            
            del self.flags[flag_name]
            self._save_flags()
            logger.info(f"Deleted flag: {flag_name}")
            return True
    
    def update_rollout_percentage(self, 
                                 flag_name: str, 
                                 percentage: int,
                                 modified_by: str = "user") -> bool:
        """
        Update rollout percentage for a percentage-based flag.
        
        Args:
            flag_name: Name of the flag
            percentage: New rollout percentage (0-100)
            modified_by: User or system making the change
            
        Returns:
            True if update was successful
        """
        with self._lock:
            if flag_name not in self.flags:
                logger.error(f"Flag {flag_name} not found")
                return False
            
            if not (0 <= percentage <= 100):
                logger.error(f"Percentage must be between 0 and 100, got {percentage}")
                return False
            
            flag = self.flags[flag_name]
            if flag.flag_type != FlagType.PERCENTAGE:
                logger.error(f"Flag {flag_name} is not a percentage-based flag")
                return False
            
            flag.rollout_percentage = percentage
            flag.last_modified = datetime.now().isoformat()
            flag.modified_by = modified_by
            
            self._save_flags()
            logger.info(f"Updated rollout percentage for {flag_name}: {percentage}% by {modified_by}")
            return True
    
    def add_to_whitelist(self, 
                        flag_name: str, 
                        identifiers: List[str],
                        modified_by: str = "user") -> bool:
        """
        Add identifiers to whitelist for a whitelist-based flag.
        
        Args:
            flag_name: Name of the flag
            identifiers: List of identifiers to add
            modified_by: User or system making the change
            
        Returns:
            True if identifiers were added successfully
        """
        with self._lock:
            if flag_name not in self.flags:
                logger.error(f"Flag {flag_name} not found")
                return False
            
            flag = self.flags[flag_name]
            if flag.flag_type != FlagType.WHITELIST:
                logger.error(f"Flag {flag_name} is not a whitelist-based flag")
                return False
            
            for identifier in identifiers:
                if identifier not in flag.whitelist:
                    flag.whitelist.append(identifier)
            
            flag.last_modified = datetime.now().isoformat()
            flag.modified_by = modified_by
            
            self._save_flags()
            logger.info(f"Added {len(identifiers)} identifiers to whitelist for {flag_name} by {modified_by}")
            return True
    
    def remove_from_whitelist(self, 
                             flag_name: str, 
                             identifiers: List[str],
                             modified_by: str = "user") -> bool:
        """
        Remove identifiers from whitelist for a whitelist-based flag.
        
        Args:
            flag_name: Name of the flag
            identifiers: List of identifiers to remove
            modified_by: User or system making the change
            
        Returns:
            True if identifiers were removed successfully
        """
        with self._lock:
            if flag_name not in self.flags:
                logger.error(f"Flag {flag_name} not found")
                return False
            
            flag = self.flags[flag_name]
            if flag.flag_type != FlagType.WHITELIST:
                logger.error(f"Flag {flag_name} is not a whitelist-based flag")
                return False
            
            removed_count = 0
            for identifier in identifiers:
                if identifier in flag.whitelist:
                    flag.whitelist.remove(identifier)
                    removed_count += 1
            
            flag.last_modified = datetime.now().isoformat()
            flag.modified_by = modified_by
            
            self._save_flags()
            logger.info(f"Removed {removed_count} identifiers from whitelist for {flag_name} by {modified_by}")
            return True
    
    def get_all_flags(self) -> Dict[str, FeatureFlag]:
        """Get all feature flags."""
        with self._lock:
            self._check_and_reload()
            return self.flags.copy()
    
    def get_enabled_flags(self) -> Dict[str, FeatureFlag]:
        """Get all enabled feature flags."""
        with self._lock:
            self._check_and_reload()
            return {name: flag for name, flag in self.flags.items() 
                   if flag.enabled and not flag.emergency_disable}
    
    def get_flags_by_tag(self, tag: str) -> Dict[str, FeatureFlag]:
        """Get flags filtered by tag."""
        with self._lock:
            self._check_and_reload()
            return {name: flag for name, flag in self.flags.items() 
                   if tag in flag.tags}
    
    def get_flag_statistics(self) -> Dict[str, Any]:
        """Get statistics about feature flags."""
        with self._lock:
            self._check_and_reload()
            
            total_flags = len(self.flags)
            enabled_flags = sum(1 for flag in self.flags.values() if flag.enabled)
            emergency_disabled = sum(1 for flag in self.flags.values() if flag.emergency_disable)
            
            flags_by_type = {}
            flags_by_strategy = {}
            
            for flag in self.flags.values():
                # Count by type
                flag_type = flag.flag_type.value
                flags_by_type[flag_type] = flags_by_type.get(flag_type, 0) + 1
                
                # Count by strategy
                strategy = flag.rollout_strategy.value
                flags_by_strategy[strategy] = flags_by_strategy.get(strategy, 0) + 1
            
            return {
                'total_flags': total_flags,
                'enabled_flags': enabled_flags,
                'disabled_flags': total_flags - enabled_flags,
                'emergency_disabled': emergency_disabled,
                'flags_by_type': flags_by_type,
                'flags_by_strategy': flags_by_strategy,
                'last_config_reload': self._last_reload,
                'config_file_path': str(self.config_path)
            }
    
    def validate_configuration(self) -> List[str]:
        """
        Validate feature flag configuration.
        
        Returns:
            List of validation errors
        """
        errors = []
        
        with self._lock:
            # Check for duplicate flag names (shouldn't happen with dict)
            flag_names = list(self.flags.keys())
            if len(flag_names) != len(set(flag_names)):
                errors.append("Duplicate flag names found")
            
            # Validate each flag
            for flag_name, flag in self.flags.items():
                # Check required fields
                if not flag.name:
                    errors.append(f"Flag {flag_name}: Missing name")
                
                # Validate percentage flags
                if flag.flag_type == FlagType.PERCENTAGE:
                    if not (0 <= flag.rollout_percentage <= 100):
                        errors.append(f"Flag {flag_name}: Invalid percentage {flag.rollout_percentage}")
                
                # Validate whitelist flags
                if flag.flag_type == FlagType.WHITELIST:
                    if not flag.whitelist:
                        errors.append(f"Flag {flag_name}: Whitelist flag has no whitelist entries")
        
        return errors
    
    # Private methods
    
    def _load_flags(self):
        """Load feature flags from configuration file."""
        try:
            if not self.config_path.exists():
                logger.warning(f"Feature flags config file not found: {self.config_path}")
                self.flags = {}
                return
            
            with open(self.config_path, 'r') as f:
                if self.config_path.suffix.lower() in ['.yaml', '.yml']:
                    config = yaml.safe_load(f)
                else:
                    config = json.load(f)
            
            if not config or 'feature_flags' not in config:
                logger.warning("No feature_flags section found in config")
                self.flags = {}
                return
            
            flags_config = config['feature_flags']
            self.flags = {}
            
            for flag_name, flag_data in flags_config.items():
                try:
                    # Convert flag type string to enum
                    if 'flag_type' in flag_data:
                        flag_data['flag_type'] = FlagType(flag_data['flag_type'])
                    
                    # Convert rollout strategy string to enum
                    if 'rollout_strategy' in flag_data:
                        flag_data['rollout_strategy'] = RolloutStrategy(flag_data['rollout_strategy'])
                    
                    flag = FeatureFlag(name=flag_name, **flag_data)
                    self.flags[flag_name] = flag
                    
                except Exception as e:
                    logger.error(f"Failed to load flag {flag_name}: {e}")
            
            self._config_mtime = self.config_path.stat().st_mtime
            logger.info(f"Loaded {len(self.flags)} feature flags from {self.config_path}")
            
        except Exception as e:
            logger.error(f"Failed to load feature flags config: {e}")
            self.flags = {}
    
    def _save_flags(self):
        """Save feature flags to configuration file."""
        try:
            # Load existing config to preserve other sections
            config = {}
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    if self.config_path.suffix.lower() in ['.yaml', '.yml']:
                        config = yaml.safe_load(f) or {}
                    else:
                        config = json.load(f)
            
            # Update feature flags section
            flags_dict = {}
            for flag_name, flag in self.flags.items():
                flag_data = asdict(flag)
                # Convert enums to strings for serialization
                flag_data['flag_type'] = flag.flag_type.value
                flag_data['rollout_strategy'] = flag.rollout_strategy.value
                flags_dict[flag_name] = flag_data
            
            config['feature_flags'] = flags_dict
            
            # Save to file
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w') as f:
                if self.config_path.suffix.lower() in ['.yaml', '.yml']:
                    yaml.dump(config, f, default_flow_style=False, indent=2)
                else:
                    json.dump(config, f, indent=2)
            
            self._config_mtime = self.config_path.stat().st_mtime
            logger.debug(f"Saved {len(self.flags)} feature flags to {self.config_path}")
            
        except Exception as e:
            logger.error(f"Failed to save feature flags config: {e}")
    
    def _check_and_reload(self):
        """Check if configuration file has changed and reload if necessary."""
        try:
            if not self.config_path.exists():
                return
            
            current_mtime = self.config_path.stat().st_mtime
            if current_mtime > self._config_mtime:
                logger.info("Feature flags configuration changed, reloading...")
                self._load_flags()
                self._last_reload = time.time()
                
        except Exception as e:
            logger.error(f"Failed to check for config changes: {e}")
    
    def _monitor_config_changes(self):
        """Background thread to monitor configuration file changes."""
        while True:
            try:
                time.sleep(self._reload_interval)
                self._check_and_reload()
            except Exception as e:
                logger.error(f"Error in config monitoring: {e}")
                time.sleep(10)  # Wait before retrying
    
    def _evaluate_percentage_flag(self, flag: FeatureFlag, context: Dict[str, Any]) -> Tuple[bool, str]:
        """Evaluate percentage-based feature flag."""
        # Use consistent hash for the same user/instance
        hash_input = f"{flag.name}:{context.get('user_id', 'anonymous')}:{context.get('instance_id', 'default')}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        percentage_score = (hash_value % 100) + 1
        
        enabled = percentage_score <= flag.rollout_percentage
        reason = f"Percentage rollout: {percentage_score}% <= {flag.rollout_percentage}%"
        
        return enabled, reason
    
    def _evaluate_whitelist_flag(self, flag: FeatureFlag, context: Dict[str, Any]) -> Tuple[bool, str]:
        """Evaluate whitelist-based feature flag."""
        user_id = context.get('user_id')
        instance_id = context.get('instance_id')
        environment = context.get('environment')
        
        # Check various identifiers
        identifiers_to_check = []
        if user_id:
            identifiers_to_check.append(f"user:{user_id}")
        if instance_id:
            identifiers_to_check.append(f"instance:{instance_id}")
        if environment:
            identifiers_to_check.append(f"env:{environment}")
        
        enabled = any(identifier in flag.whitelist for identifier in identifiers_to_check)
        
        if enabled:
            reason = f"Whitelist match: {[id for id in identifiers_to_check if id in flag.whitelist]}"
        else:
            reason = f"No whitelist match for: {identifiers_to_check}"
        
        return enabled, reason
    
    def _evaluate_conditional_flag(self, flag: FeatureFlag, context: Dict[str, Any]) -> Tuple[bool, Any, str]:
        """Evaluate conditional feature flag."""
        try:
            # Simple conditional evaluation
            # In a real implementation, this would be more sophisticated
            conditions = flag.conditions
            
            # Time-based conditions
            if 'start_time' in conditions:
                start_time = datetime.fromisoformat(conditions['start_time'])
                if datetime.now() < start_time:
                    return False, flag.value, "Before start time"
            
            if 'end_time' in conditions:
                end_time = datetime.fromisoformat(conditions['end_time'])
                if datetime.now() > end_time:
                    return False, flag.value, "After end time"
            
            # Environment conditions
            if 'environments' in conditions:
                if context.get('environment') not in conditions['environments']:
                    return False, flag.value, f"Environment {context.get('environment')} not in allowed environments"
            
            # Custom conditions (placeholder for more complex logic)
            if 'custom' in conditions:
                # This would be extended with custom condition evaluation
                pass
            
            return True, flag.value, "All conditions met"
            
        except Exception as e:
            logger.error(f"Error evaluating conditional flag {flag.name}: {e}")
            return False, flag.value, f"Error evaluating conditions: {e}"

# Global instance
feature_flags_manager = FeatureFlagsManager()

# Convenience functions
def is_enabled(flag_name: str, **kwargs) -> bool:
    """Check if feature flag is enabled."""
    return feature_flags_manager.is_enabled(flag_name, **kwargs)

def evaluate_flag(flag_name: str, **kwargs) -> FlagEvaluationResult:
    """Evaluate feature flag with detailed result."""
    return feature_flags_manager.evaluate_flag(flag_name, **kwargs)

def enable_flag(flag_name: str, **kwargs) -> bool:
    """Enable a feature flag."""
    return feature_flags_manager.enable_flag(flag_name, **kwargs)

def disable_flag(flag_name: str, **kwargs) -> bool:
    """Disable a feature flag."""
    return feature_flags_manager.disable_flag(flag_name, **kwargs)

def emergency_disable_all(**kwargs) -> int:
    """Emergency disable all feature flags."""
    return feature_flags_manager.emergency_disable_all(**kwargs)