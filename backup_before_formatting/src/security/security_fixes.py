"""
Security fixes module for quantitative trading system
Addresses security vulnerabilities identified in audit report
"""

import hashlib
import hmac
import logging
import os
import re
import secrets
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse
import json

import pandas as pd

logger = logging.getLogger(__name__)


class SecurityValidator:
    """Security validation utilities for input sanitization and protection"""

    # Security constants
    MAX_SYMBOL_LENGTH = 20
    MAX_FILENAME_LENGTH = 255
    ALLOWED_SYMBOL_PATTERN = re.compile(r'^[A-Z0-9\.]{1,20}$')
    SAFE_FILENAME_PATTERN = re.compile(r'^[a-zA-Z0-9_\-\.]{1,255}$')

    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r"(\b(UNION|SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
        r"(--|#|/\*|\*/)",
        r"(\bOR\b.*=.*\bOR\b)",
        r"(\bAND\b.*=.*\bAND\b)",
        r"('|\"|;|\\)",
    ]

    @classmethod
    def sanitize_sql_input(cls, input_value: str) -> str:
        """
        Sanitize input to prevent SQL injection attacks

        Args:
            input_value: Raw input string

        Returns:
            Sanitized string safe for SQL operations

        Raises:
            ValueError: If input contains potential SQL injection
        """
        if not isinstance(input_value, str):
            raise ValueError("Input must be a string")

        # Convert to uppercase for pattern matching
        upper_input = input_value.upper()

        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, upper_input, re.IGNORECASE):
                logger.warning(f"Potential SQL injection detected: {input_value}")
                raise ValueError(f"Invalid input detected: potentially harmful characters")

        return input_value.strip()

    @classmethod
    def validate_stock_symbol(cls, symbol: str) -> str:
        """
        Validate and sanitize stock symbol input

        Args:
            symbol: Stock symbol to validate

        Returns:
            Validated and normalized symbol

        Raises:
            ValueError: If symbol is invalid
        """
        if not isinstance(symbol, str):
            raise ValueError("Stock symbol must be a string")

        symbol = symbol.strip().upper()

        # Check length
        if len(symbol) > cls.MAX_SYMBOL_LENGTH:
            raise ValueError(f"Stock symbol too long (max {cls.MAX_SYMBOL_LENGTH} characters)")

        # Check pattern
        if not cls.ALLOWED_SYMBOL_PATTERN.match(symbol):
            raise ValueError("Invalid stock symbol format")

        # Sanitize against SQL injection
        return cls.sanitize_sql_input(symbol)

    @classmethod
    def validate_filename(cls, filename: str) -> str:
        """
        Validate filename to prevent path traversal attacks

        Args:
            filename: Filename to validate

        Returns:
            Validated filename

        Raises:
            ValueError: If filename is invalid or contains path traversal
        """
        if not isinstance(filename, str):
            raise ValueError("Filename must be a string")

        filename = filename.strip()

        # Remove path separators
        filename = os.path.basename(filename)

        # Check for path traversal attempts
        if ".." in filename or "/" in filename or "\\" in filename:
            raise ValueError("Path traversal detected in filename")

        # Check length
        if len(filename) > cls.MAX_FILENAME_LENGTH:
            raise ValueError(f"Filename too long (max {cls.MAX_FILENAME_LENGTH} characters)")

        # Check pattern
        if not cls.SAFE_FILENAME_PATTERN.match(filename):
            raise ValueError("Invalid filename format")

        return filename

    @classmethod
    def validate_numeric_input(cls, value: Any, min_val: float = None, max_val: float = None) -> float:
        """
        Validate numeric input parameters

        Args:
            value: Value to validate
            min_val: Minimum allowed value
            max_val: Maximum allowed value

        Returns:
            Validated float value

        Raises:
            ValueError: If value is invalid or out of range
        """
        try:
            float_value = float(value)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid numeric input: {value}")

        if min_val is not None and float_value < min_val:
            raise ValueError(f"Value {float_value} is below minimum {min_val}")

        if max_val is not None and float_value > max_val:
            raise ValueError(f"Value {float_value} is above maximum {max_val}")

        return float_value

    @classmethod
    def sanitize_json_input(cls, json_data: Union[str, Dict, List]) -> Dict:
        """
        Sanitize JSON input data

        Args:
            json_data: JSON data to sanitize (string or parsed object)

        Returns:
            Sanitized dictionary

        Raises:
            ValueError: If JSON is malformed or contains dangerous content
        """
        try:
            if isinstance(json_data, str):
                data = json.loads(json_data)
            else:
                data = json_data

            if not isinstance(data, (dict, list)):
                raise ValueError("JSON must be object or array")

            # Recursively sanitize string values
            def sanitize_strings(obj):
                if isinstance(obj, dict):
                    return {key: sanitize_strings(value) for key, value in obj.items()}
                elif isinstance(obj, list):
                    return [sanitize_strings(item) for item in obj]
                elif isinstance(obj, str):
                    return cls.sanitize_sql_input(obj)
                else:
                    return obj

            return sanitize_strings(data)

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")


class SecureConfigManager:
    """Secure configuration manager with encryption for sensitive data"""

    def __init__(self, config_file: str = None):
        """
        Initialize secure configuration manager

        Args:
            config_file: Path to configuration file
        """
        self.config_file = config_file
        self.config_data = {}
        self.encrypted_fields = ['api_key', 'secret_key', 'password', 'token']

    def _get_encryption_key(self) -> bytes:
        """Get encryption key from environment or generate one"""
        key = os.environ.get('ENCRYPTION_KEY')
        if not key:
            # In production, this should come from a secure key management system
            key = os.environ.get('SECRET_KEY', 'default-secret-key-change-in-production')

        return hashlib.sha256(key.encode()).digest()

    def _encrypt_value(self, value: str) -> str:
        """Encrypt sensitive configuration value"""
        if not value:
            return value

        key = self._get_encryption_key()
        # Simple XOR encryption for demonstration (use proper encryption in production)
        encrypted = ''.join(chr(ord(c) ^ key[i % len(key)]) for i, c in enumerate(value))
        return encrypted.encode('utf-8').hex()

    def _decrypt_value(self, encrypted_value: str) -> str:
        """Decrypt sensitive configuration value"""
        if not encrypted_value:
            return encrypted_value

        try:
            key = self._get_encryption_key()
            encrypted_bytes = bytes.fromhex(encrypted_value)
            decrypted = ''.join(chr(b ^ key[i % len(key)]) for i, b in enumerate(encrypted_bytes))
            return decrypted
        except Exception as e:
            logger.error(f"Failed to decrypt configuration value: {e}")
            return ""

    def set_config(self, key: str, value: Any, is_sensitive: bool = False):
        """
        Set configuration value with optional encryption

        Args:
            key: Configuration key
            value: Configuration value
            is_sensitive: Whether the value contains sensitive information
        """
        if is_sensitive or any(field in key.lower() for field in self.encrypted_fields):
            self.config_data[key] = self._encrypt_value(str(value))
        else:
            self.config_data[key] = value

    def get_config(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value with automatic decryption

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value
        """
        value = self.config_data.get(key, default)

        # Check if this is an encrypted field
        if any(field in key.lower() for field in self.encrypted_fields):
            return self._decrypt_value(value)

        return value

    def load_from_file(self):
        """Load configuration from file"""
        if not self.config_file or not os.path.exists(self.config_file):
            logger.warning(f"Configuration file not found: {self.config_file}")
            return

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config_data = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")

    def save_to_file(self):
        """Save configuration to file"""
        if not self.config_file:
            logger.warning("No configuration file specified")
            return

        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")


class SecureFileOperations:
    """Secure file operations with access control and validation"""

    def __init__(self, base_directory: str = None):
        """
        Initialize secure file operations

        Args:
            base_directory: Base directory for file operations
        """
        self.base_directory = base_directory or os.getcwd()
        self.allowed_extensions = ['.json', '.csv', '.txt', '.log', '.md']
        self.max_file_size = 100 * 1024 * 1024  # 100MB

    def _validate_file_path(self, file_path: str) -> str:
        """
        Validate file path to prevent path traversal attacks

        Args:
            file_path: File path to validate

        Returns:
            Absolute, validated file path

        Raises:
            ValueError: If path is invalid or outside base directory
        """
        if not isinstance(file_path, str):
            raise ValueError("File path must be a string")

        # Normalize path
        file_path = os.path.normpath(file_path)

        # Convert to absolute path
        if not os.path.isabs(file_path):
            file_path = os.path.join(self.base_directory, file_path)
            file_path = os.path.abspath(file_path)

        # Check for path traversal
        if not file_path.startswith(os.path.abspath(self.base_directory)):
            raise ValueError("Path traversal detected - access denied")

        return file_path

    def safe_write_file(self, file_path: str, content: str, validate_content: bool = True):
        """
        Safely write content to file

        Args:
            file_path: Target file path
            content: Content to write
            validate_content: Whether to validate content for security
        """
        try:
            # Validate file path
            safe_path = self._validate_file_path(file_path)

            # Validate file extension
            _, ext = os.path.splitext(safe_path)
            if ext.lower() not in self.allowed_extensions:
                raise ValueError(f"File extension {ext} not allowed")

            # Validate content size
            if len(content.encode('utf-8')) > self.max_file_size:
                raise ValueError("File content too large")

            # Sanitize content if requested
            if validate_content and isinstance(content, str):
                content = SecurityValidator.sanitize_sql_input(content)

            # Write file atomically
            temp_path = safe_path + '.tmp'
            with open(temp_path, 'w', encoding='utf-8') as f:
                f.write(content)

            # Atomic rename
            os.rename(temp_path, safe_path)

            logger.info(f"File written successfully: {safe_path}")

        except Exception as e:
            logger.error(f"Failed to write file {file_path}: {e}")
            raise

    def safe_read_file(self, file_path: str, max_size: int = None) -> str:
        """
        Safely read content from file

        Args:
            file_path: File path to read
            max_size: Maximum file size to read

        Returns:
            File content
        """
        try:
            # Validate file path
            safe_path = self._validate_file_path(file_path)

            # Check file exists
            if not os.path.exists(safe_path):
                raise FileNotFoundError(f"File not found: {safe_path}")

            # Check file size
            file_size = os.path.getsize(safe_path)
            max_allowed = max_size or self.max_file_size
            if file_size > max_allowed:
                raise ValueError(f"File too large: {file_size} bytes")

            # Read file
            with open(safe_path, 'r', encoding='utf-8') as f:
                content = f.read()

            return content

        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            raise


class SecurityLogger:
    """Enhanced security logger for monitoring and audit"""

    def __init__(self, log_file: str = "security.log"):
        """
        Initialize security logger

        Args:
            log_file: Path to security log file
        """
        self.logger = logging.getLogger('security')
        self.logger.setLevel(logging.INFO)

        # Create file handler
        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s - %(funcName)s:%(lineno)d'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def log_security_event(self, event_type: str, details: Dict[str, Any], severity: str = "INFO"):
        """
        Log security event with details

        Args:
            event_type: Type of security event
            details: Event details dictionary
            severity: Log severity level
        """
        message = f"SECURITY_EVENT: {event_type} - {json.dumps(details)}"

        if severity.upper() == "CRITICAL":
            self.logger.critical(message)
        elif severity.upper() == "WARNING":
            self.logger.warning(message)
        else:
            self.logger.info(message)

    def log_authentication_attempt(self, user_id: str, success: bool, ip_address: str = None):
        """Log authentication attempt"""
        details = {
            "user_id": user_id,
            "success": success,
            "ip_address": ip_address,
            "timestamp": pd.Timestamp.now().isoformat()
        }
        self.log_security_event("AUTHENTICATION_ATTEMPT", details)

    def log_access_violation(self, resource: str, user_id: str = None, details: str = None):
        """Log access violation"""
        event_details = {
            "resource": resource,
            "user_id": user_id,
            "details": details,
            "timestamp": pd.Timestamp.now().isoformat()
        }
        self.log_security_event("ACCESS_VIOLATION", event_details, "WARNING")

    def log_sql_injection_attempt(self, input_value: str, user_id: str = None):
        """Log SQL injection attempt"""
        details = {
            "input_value": input_value[:100],  # Truncate for logging
            "user_id": user_id,
            "timestamp": pd.Timestamp.now().isoformat()
        }
        self.log_security_event("SQL_INJECTION_ATTEMPT", details, "CRITICAL")


# Initialize global security components
security_validator = SecurityValidator()
secure_config = SecureConfigManager()
secure_file_ops = SecureFileOperations()
security_logger = SecurityLogger()


def apply_security_patches():
    """
    Apply all security patches to the system
    This function should be called during application startup
    """
    try:
        # Load secure configuration
        secure_config.load_from_file()

        # Initialize security logging
        security_logger.log_security_event("SYSTEM_STARTUP", {
            "status": "success",
            "features": ["input_validation", "secure_config", "file_security", "audit_logging"]
        })

        logger.info("Security patches applied successfully")
        return True

    except Exception as e:
        logger.error(f"Failed to apply security patches: {e}")
        return False


if __name__ == "__main__":
    # Test security functions
    print("Testing Security Module...")

    # Test input validation
    try:
        symbol = security_validator.validate_stock_symbol("0700.HK")
        print(f"Valid symbol: {symbol}")
    except ValueError as e:
        print(f"Validation error: {e}")

    # Test SQL injection prevention
    try:
        malicious_input = "'; DROP TABLE users; --"
        security_validator.sanitize_sql_input(malicious_input)
    except ValueError as e:
        print(f"SQL injection blocked: {e}")

    print("Security module tests completed")