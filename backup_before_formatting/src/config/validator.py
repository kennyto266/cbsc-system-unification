"""
Configuration Validator

Comprehensive validation system for configuration values with type checking,
business logic validation, and security validation.
"""

import hashlib
import ipaddress
import re
import secrets
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from urllib.parse import urlparse


class ValidationError:
    """Configuration validation error."""

    def __init__(self, field: str, message: str, value: Any = None):
        self.field = field
        self.message = message
        self.value = value

    def __str__(self):
        return f'Validation Error in "{self.field}": {self.message}'

    def __repr__(self):
        return f"ValidationError(field='{self.field}', message='{self.message}')"


class ConfigValidator:
    """
    Comprehensive configuration validator with type checking and business rules.
    """

    def __init__(self):
        """Initialize the validator."""
        self.errors: List[ValidationError] = []
        self.warnings: List[ValidationError] = []

    def validate_config(
        self, config: Dict[str, Any], environment: str = "development"
    ) -> Tuple[bool, List[ValidationError], List[ValidationError]]:
        """
        Validate complete configuration.

        Args:
            config: Configuration dictionary
            environment: Target environment

        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        self.errors = []
        self.warnings = []

        # Core validation sections
        self._validate_system_config(config.get("system", {}))
        self._validate_database_config(config.get("database", {}))
        self._validate_redis_config(config.get("redis", {}))
        self._validate_api_config(config.get("api", {}))
        self._validate_trading_config(config.get("trading", {}))
        self._validate_monitoring_config(config.get("monitoring", {}))
        self._validate_security_config(config.get("security", {}), environment)
        self._validate_logging_config(config.get("logging", {}))

        # Environment - specific validations
        self._validate_environment_specific(config, environment)

        return len(self.errors) == 0, self.errors, self.warnings

    def _validate_system_config(self, config: Dict[str, Any]):
        """Validate system configuration."""
        if not config:
            self.errors.append(
                ValidationError("system", "System configuration is required")
            )
            return

        # Environment validation
        valid_envs = ["development", "testing", "staging", "production"]
        if config.get("environment") not in valid_envs:
            self.errors.append(
                ValidationError(
                    "system.environment",
                    f"Environment must be one of: {valid_envs}",
                    config.get("environment"),
                )
            )

        # Version format validation
        version = config.get("version", "")
        if version and not re.match(r"^\d+\.\d+\.\d+", version):
            self.errors.append(
                ValidationError(
                    "system.version", "Version must be in format x.y.z", version
                )
            )

    def _validate_database_config(self, config: Dict[str, Any]):
        """Validate database configuration."""
        if not config:
            self.errors.append(
                ValidationError("database", "Database configuration is required")
            )
            return

        # Host validation
        host = config.get("host", "")
        if not host:
            self.errors.append(
                ValidationError("database.host", "Database host is required")
            )

        # Port validation
        port = config.get("port", 0)
        if not isinstance(port, int) or not (1 <= port <= 65535):
            self.errors.append(
                ValidationError(
                    "database.port", "Port must be between 1 and 65535", port
                )
            )

        # Connection pool validation
        pool_size = config.get("pool_size", 0)
        if not isinstance(pool_size, int) or pool_size <= 0:
            self.errors.append(
                ValidationError(
                    "database.pool_size",
                    "Pool size must be a positive integer",
                    pool_size,
                )
            )

        max_overflow = config.get("max_overflow", 0)
        if not isinstance(max_overflow, int) or max_overflow < 0:
            self.errors.append(
                ValidationError(
                    "database.max_overflow",
                    "Max overflow must be a non - negative integer",
                    max_overflow,
                )
            )

    def _validate_redis_config(self, config: Dict[str, Any]):
        """Validate Redis configuration."""
        if not config:
            self.errors.append(
                ValidationError("redis", "Redis configuration is required")
            )
            return

        # Port validation
        port = config.get("port", 0)
        if not isinstance(port, int) or not (1 <= port <= 65535):
            self.errors.append(
                ValidationError("redis.port", "Port must be between 1 and 65535", port)
            )

        # Database number validation
        db = config.get("db", -1)
        if not isinstance(db, int) or not (0 <= db <= 15):
            self.errors.append(
                ValidationError("redis.db", "Redis DB must be between 0 and 15", db)
            )

        # Memory validation
        max_memory = config.get("max_memory", "")
        if max_memory and not self._validate_memory_size(max_memory):
            self.errors.append(
                ValidationError(
                    "redis.max_memory",
                    "Invalid memory size format (e.g., 512mb, 1gb)",
                    max_memory,
                )
            )

    def _validate_api_config(self, config: Dict[str, Any]):
        """Validate API configuration."""
        if not config:
            self.errors.append(ValidationError("api", "API configuration is required"))
            return

        # Base URL validation
        base_url = config.get("base_url", "")
        if base_url and not self._is_valid_url(base_url):
            self.errors.append(
                ValidationError("api.base_url", "Invalid URL format", base_url)
            )

        # Timeout validation
        timeout = config.get("timeout", 0)
        if not isinstance(timeout, int) or timeout <= 0:
            self.errors.append(
                ValidationError(
                    "api.timeout", "Timeout must be a positive integer", timeout
                )
            )

        # Rate limiting validation
        rate_limit = config.get("rate_limit", 0)
        if not isinstance(rate_limit, int) or rate_limit <= 0:
            self.errors.append(
                ValidationError(
                    "api.rate_limit",
                    "Rate limit must be a positive integer",
                    rate_limit,
                )
            )

    def _validate_trading_config(self, config: Dict[str, Any]):
        """Validate trading configuration."""
        if not config:
            self.errors.append(
                ValidationError("trading", "Trading configuration is required")
            )
            return

        # Risk limit validation
        risk_limit = config.get("risk_limit", 0)
        if not isinstance(risk_limit, (int, float)) or not (0 < risk_limit <= 1):
            self.errors.append(
                ValidationError(
                    "trading.risk_limit",
                    "Risk limit must be between 0 and 1",
                    risk_limit,
                )
            )

        # Max drawdown validation
        max_drawdown = config.get("max_drawdown", 0)
        if not isinstance(max_drawdown, (int, float)) or not (0 < max_drawdown <= 1):
            self.errors.append(
                ValidationError(
                    "trading.max_drawdown",
                    "Max drawdown must be between 0 and 1",
                    max_drawdown,
                )
            )

        # Risk - free rate validation
        risk_free_rate = config.get("risk_free_rate", 0)
        if not isinstance(risk_free_rate, (int, float)) or not (
            0 <= risk_free_rate <= 0.2
        ):
            self.errors.append(
                ValidationError(
                    "trading.risk_free_rate",
                    "Risk - free rate must be between 0 and 0.2 (20%)",
                    risk_free_rate,
                )
            )

        # Trading hours validation
        time_fields = ["market_open", "market_close", "lunch_start", "lunch_end"]
        for field in time_fields:
            time_value = config.get(field, "")
            if time_value and not re.match(r"^\d{2}:\d{2}$", time_value):
                self.errors.append(
                    ValidationError(
                        f"trading.{field}", "Time must be in HH:MM format", time_value
                    )
                )

    def _validate_monitoring_config(self, config: Dict[str, Any]):
        """Validate monitoring configuration."""
        if not config:
            return  # Monitoring is optional

        # Port validations
        port_fields = {
            "prometheus_port": "Prometheus",
            "grafana_port": "Grafana",
            "alertmanager_port": "AlertManager",
            "jaeger_port": "Jaeger",
        }

        for field, service in port_fields.items():
            port = config.get(field, 0)
            if port and not isinstance(port, int) or not (1 <= port <= 65535):
                self.errors.append(
                    ValidationError(
                        f"monitoring.{field}",
                        f"{service} port must be between 1 and 65535",
                        port,
                    )
                )

    def _validate_security_config(self, config: Dict[str, Any], environment: str):
        """Validate security configuration."""
        if not config:
            self.errors.append(
                ValidationError("security", "Security configuration is required")
            )
            return

        # Secret key validation
        secret_key = config.get("secret_key", "")
        if not secret_key:
            self.errors.append(
                ValidationError("security.secret_key", "Secret key is required")
            )
        elif len(secret_key) < 32:
            self.errors.append(
                ValidationError(
                    "security.secret_key",
                    "Secret key must be at least 32 characters long",
                )
            )

        # JWT secret validation
        jwt_secret = config.get("jwt_secret_key", "")
        if not jwt_secret:
            self.errors.append(
                ValidationError("security.jwt_secret_key", "JWT secret key is required")
            )
        elif len(jwt_secret) < 32:
            self.errors.append(
                ValidationError(
                    "security.jwt_secret_key",
                    "JWT secret key must be at least 32 characters long",
                )
            )

        # SSL validation for production
        if environment == "production":
            if not config.get("ssl_enabled", False):
                self.warnings.append(
                    ValidationError(
                        "security.ssl_enabled", "SSL should be enabled in production"
                    )
                )

            ssl_cert = config.get("ssl_cert_path", "")
            ssl_key = config.get("ssl_key_path", "")
            if config.get("ssl_enabled") and (not ssl_cert or not ssl_key):
                self.errors.append(
                    ValidationError(
                        "security.ssl",
                        "SSL certificate and key paths are required when SSL is enabled",
                    )
                )

        # IP address validation
        for ip_field in ["allowed_ips", "blocked_ips"]:
            ips = config.get(ip_field, [])
            if ips and not isinstance(ips, list):
                self.errors.append(
                    ValidationError(
                        f"security.{ip_field}", "IP lists must be arrays", ips
                    )
                )
            else:
                for ip in ips:
                    if not self._is_valid_ip(ip):
                        self.errors.append(
                            ValidationError(
                                f"security.{ip_field}", f"Invalid IP address: {ip}", ip
                            )
                        )

    def _validate_logging_config(self, config: Dict[str, Any]):
        """Validate logging configuration."""
        if not config:
            return

        # Log level validation
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        level = config.get("level", "")
        if level and level not in valid_levels:
            self.errors.append(
                ValidationError(
                    "logging.level", f"Log level must be one of: {valid_levels}", level
                )
            )

        # File path validation
        file_path = config.get("file_path", "")
        if file_path:
            try:
                path = Path(file_path)
                # Ensure the parent directory can be created
                path.parent.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                self.errors.append(
                    ValidationError(
                        "logging.file_path", f"Invalid log file path: {e}", file_path
                    )
                )

    def _validate_environment_specific(self, config: Dict[str, Any], environment: str):
        """Environment - specific validations."""
        if environment == "production":
            # Production environment specific checks
            if config.get("system", {}).get("debug", False):
                self.warnings.append(
                    ValidationError(
                        "system.debug", "Debug mode should be disabled in production"
                    )
                )

        elif environment == "development":
            # Development environment specific checks
            if not config.get("system", {}).get("debug", False):
                self.warnings.append(
                    ValidationError(
                        "system.debug", "Debug mode should be enabled in development"
                    )
                )

    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False

    def _is_valid_ip(self, ip: str) -> bool:
        """Check if IP address is valid."""
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False

    def _validate_memory_size(self, size_str: str) -> bool:
        """Validate memory size format (e.g., 512mb, 1gb)."""
        pattern = r"^\d+[KMG]B$"
        return bool(re.match(pattern, size_str, re.IGNORECASE))

    def generate_secure_secret(self, length: int = 32) -> str:
        """Generate cryptographically secure secret."""
        return secrets.token_urlsafe(length)

    def validate_password_strength(self, password: str) -> Tuple[bool, List[str]]:
        """
        Validate password strength.

        Args:
            password: Password to validate

        Returns:
            Tuple of (is_strong, list_of_issues)
        """
        issues = []

        if len(password) < 12:
            issues.append("Password must be at least 12 characters long")

        if not re.search(r"[A - Z]", password):
            issues.append("Password must contain uppercase letters")

        if not re.search(r"[a - z]", password):
            issues.append("Password must contain lowercase letters")

        if not re.search(r"\d", password):
            issues.append("Password must contain numbers")

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            issues.append("Password must contain special characters")

        return len(issues) == 0, issues
