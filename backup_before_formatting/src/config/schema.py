"""
Configuration Schema Definition

Central schema definition for all configuration structures and validation rules.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml


class ConfigSchema:
    """
    Central configuration schema with validation rules and inheritance structure.
    """

    # Base schema that applies to all environments
    BASE_SCHEMA = {
        "system": {
            "name": "string",
            "version": "string",
            "environment": "enum[development,testing,staging,production]",
            "debug": "boolean",
        },
        "database": {
            "host": "string",
            "port": "integer",
            "name": "string",
            "user": "string",
            "password": "string|secret",
            "ssl_mode": "string",
            "pool_size": "integer",
            "max_overflow": "integer",
            "echo": "boolean",
        },
        "redis": {
            "host": "string",
            "port": "integer",
            "db": "integer",
            "password": "string|secret",
            "max_connections": "integer",
            "max_memory": "string",
            "max_memory_policy": "string",
        },
        "api": {
            "base_url": "string|url",
            "timeout": "integer",
            "max_retries": "integer",
            "rate_limit": "integer",
            "chunk_size": "integer",
        },
        "trading": {
            "enabled": "boolean",
            "environment": "string",
            "max_position_size": "number",
            "risk_limit": "number",
            "max_drawdown": "number",
            "futu_host": "string",
            "futu_port": "integer",
            "default_sharpe_threshold": "number",
            "risk_free_rate": "number",
        },
        "monitoring": {
            "enabled": "boolean",
            "prometheus_port": "integer",
            "grafana_port": "integer",
            "alertmanager_port": "integer",
            "jaeger_port": "integer",
        },
        "security": {
            "secret_key": "string|secret",
            "jwt_secret_key": "string|secret",
            "jwt_algorithm": "string",
            "ssl_enabled": "boolean",
            "rate_limit_enabled": "boolean",
        },
        "logging": {
            "level": "enum[DEBUG,INFO,WARNING,ERROR,CRITICAL]",
            "format": "string",
            "file_path": "string",
            "json_enabled": "boolean",
        },
    }

    # Environment - specific overrides
    ENVIRONMENT_OVERRIDES = {
        "development": {
            "debug": True,
            "database": {"echo": True, "pool_size": 5},
            "logging": {"level": "DEBUG"},
            "trading": {"environment": "SIMULATE"},
        },
        "testing": {
            "debug": True,
            "database": {"name": "quant_test", "pool_size": 2},
            "redis": {"db": 1},
            "logging": {"level": "DEBUG", "file_path": "logs / test.log"},
        },
        "staging": {
            "debug": False,
            "database": {"pool_size": 10},
            "logging": {"level": "INFO"},
            "monitoring": {"enabled": True},
        },
        "production": {
            "debug": False,
            "database": {"pool_size": 50, "ssl_mode": "require"},
            "redis": {"max_memory": "1gb"},
            "logging": {"level": "WARNING", "json_enabled": True},
            "security": {"ssl_enabled": True, "rate_limit_enabled": True},
            "monitoring": {"enabled": True},
        },
    }

    # Validation rules
    VALIDATION_RULES = {
        "port_range": {
            "min": 1,
            "max": 65535,
            "message": "Port must be between 1 and 65535",
        },
        "positive_integer": {"min": 1, "message": "Value must be a positive integer"},
        "url_format": {"pattern": r"^https?://.+", "message": "Must be a valid URL"},
        "email_format": {
            "pattern": r"^[a - zA - Z0 - 9._%+-]+@[a - zA - Z0 - 9.-]+\.[a - zA - Z]{2,}$",
            "message": "Must be a valid email address",
        },
        "secret_strength": {
            "min_length": 32,
            "require_special": True,
            "require_numbers": True,
            "message": "Secret must be at least 32 characters with special chars and numbers",
        },
    }

    def __init__(self) -> None:
        """Initialize the configuration schema."""
        self.schema = self.BASE_SCHEMA
        self.overrides = self.ENVIRONMENT_OVERRIDES
        self.validation_rules = self.VALIDATION_RULES

    def get_schema_for_environment(self, environment: str) -> Dict[str, Any]:
        """
        Get configuration schema for a specific environment.

        Args:
            environment: Target environment name

        Returns:
            Environment - specific schema dictionary
        """
        base_schema = self.BASE_SCHEMA.copy()
        overrides: Dict[str, Any] = self.ENVIRONMENT_OVERRIDES.get(environment, {})

        # Apply environment - specific overrides
        for key, value in overrides.items():
            if isinstance(value, dict) and key in base_schema:
                base_schema[key].update(value)
            else:
                base_schema[key] = value

        return base_schema

    def validate_field(
        self, field_path: str, value: Any, rule: Optional[str] = None
    ) -> tuple[bool, str]:
        """
        Validate a single configuration field.

        Args:
            field_path: Dot - separated field path (e.g., 'database.port')
            value: Value to validate
            rule: Specific validation rule to apply

        Returns:
            Tuple of (is_valid, error_message)
        """
        if rule and rule in self.validation_rules:
            rule_config: Dict[str, Any] = self.validation_rules[rule]

            if rule == "port_range":
                if not isinstance(value, int) or not (1 <= value <= 65535):
                    return False, rule_config["message"]

            elif rule == "positive_integer":
                if not isinstance(value, int) or value <= 0:
                    return False, rule_config["message"]

            elif rule == "url_format":
                import re

                if not isinstance(value, str) or not re.match(
                    rule_config["pattern"], value
                ):
                    return False, rule_config["message"]

            elif rule == "secret_strength":
                if not isinstance(value, str) or len(value) < rule_config["min_length"]:
                    return False, rule_config["message"]

        return True, ""

    def get_default_config(self, environment: str = "development") -> Dict[str, Any]:
        """
        Get default configuration for an environment.

        Args:
            environment: Target environment

        Returns:
            Default configuration dictionary
        """
        schema = self.get_schema_for_environment(environment)
        defaults: Dict[str, Any] = {}

        for key, value in schema.items():
            if isinstance(value, dict):
                defaults[key] = {}
                for subkey, subvalue in value.items():
                    if isinstance(subvalue, str) and "|" in subvalue:
                        # Handle type specifications like "string|secret"
                        field_type = subvalue.split("|")[0]
                        defaults[key][subkey] = self._get_default_for_type(field_type)
                    elif subvalue.startswith("enum["):
                        # Handle enum specifications
                        enum_values = subvalue[5:-1].split(",")
                        defaults[key][subkey] = enum_values[0]
                    else:
                        defaults[key][subkey] = self._get_default_for_type(subvalue)
            else:
                if isinstance(value, str) and "|" in value:
                    field_type = value.split("|")[0]
                    defaults[key] = self._get_default_for_type(field_type)
                elif value.startswith("enum["):
                    enum_values = value[5:-1].split(",")
                    defaults[key] = enum_values[0]
                else:
                    defaults[key] = self._get_default_for_type(value)

        return defaults

    def _get_default_for_type(self, field_type: str) -> Any:
        """Get default value for a field type."""
        type_defaults = {
            "string": "",
            "integer": 0,
            "number": 0.0,
            "boolean": False,
            "url": "http://localhost",
            "secret": "",
            "enum": "",
        }
        return type_defaults.get(field_type, "")

    def validate_config_structure(
        self, config: Dict[str, Any], environment: str
    ) -> List[str]:
        """
        Validate complete configuration structure against schema.

        Args:
            config: Configuration dictionary
            environment: Target environment

        Returns:
            List of validation errors
        """
        schema = self.get_schema_for_environment(environment)
        errors: List[str] = []

        def validate_recursive(config_part: Dict, schema_part: Dict, path: str = "") -> None:
            for key, schema_value in schema_part.items():
                current_path = f"{path}.{key}" if path else key

                if key not in config_part:
                    errors.append(f"Missing required field: {current_path}")
                    continue

                config_value = config_part[key]

                if isinstance(schema_value, dict):
                    if not isinstance(config_value, dict):
                        errors.append(f"Field {current_path} should be a dictionary")
                    else:
                        validate_recursive(config_value, schema_value, current_path)

        validate_recursive(config, schema)
        return errors

    def save_schema_template(self, file_path: str, environment: str = "development") -> None:
        """
        Save schema template as YAML file.

        Args:
            file_path: Output file path
            environment: Target environment
        """
        default_config = self.get_default_config(environment)

        with open(file_path, "w") as f:
            yaml.dump(default_config, f, default_flow_style=False, indent=2)

    def load_schema_template(self, file_path: str) -> Dict[str, Any]:
        """
        Load schema template from file.

        Args:
            file_path: Input file path

        Returns:
            Loaded configuration dictionary
        """
        with open(file_path, "r") as f:
            if file_path.endswith(".json"):
                return json.load(f)
            else:
                return yaml.safe_load(f)
