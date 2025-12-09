"""
Security Configuration Module
Centralized security settings and policies for the quantitative trading system
"""

import os
from typing import Dict, List, Any
import secrets


class SecurityConfig:
    """Centralized security configuration management"""

    # Security constants
    DEFAULT_RISK_FREE_RATE = 0.03  # 3% annual risk-free rate
    DEFAULT_TRADING_DAYS = 252     # Trading days per year

    # Input validation limits
    MAX_SYMBOL_LENGTH = 20
    MAX_FILENAME_LENGTH = 255
    MAX_STRING_INPUT_LENGTH = 1000
    MAX_JSON_INPUT_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_FILE_SIZE = 100 * 1024 * 1024       # 100MB

    # Allowed file extensions for secure file operations
    ALLOWED_FILE_EXTENSIONS = [
        '.json', '.csv', '.txt', '.log', '.md',
        '.yaml', '.yml', '.xml', '.html', '.pdf'
    ]

    # SQL injection detection patterns
    SQL_INJECTION_PATTERNS = [
        r"(?i)(union|select|insert|update|delete|drop|create|alter|exec|execute)\b",
        r"(--|#|/\*|\*/)",
        r"(?i)\bor\b.*=.*\bor\b",
        r"(?i)\band\b.*=.*\band\b",
        r"['\";\\]",
        r"(?i)(script|javascript|vbscript|onload|onerror)",
    ]

    # Stock symbol validation patterns
    STOCK_SYMBOL_PATTERN = r'^[A-Z0-9\.]{1,20}$'
    SAFE_FILENAME_PATTERN = r'^[a-zA-Z0-9_\-\.]{1,255}$'

    # Security headers
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
    }

    # Rate limiting
    RATE_LIMIT_REQUESTS = 100    # requests per minute
    RATE_LIMIT_WINDOW = 60       # seconds
    RATE_LIMIT_BLOCK_TIME = 300  # seconds (5 minutes)

    # Password policies
    PASSWORD_MIN_LENGTH = 12
    PASSWORD_REQUIRE_UPPERCASE = True
    PASSWORD_REQUIRE_LOWERCASE = True
    PASSWORD_REQUIRE_NUMBERS = True
    PASSWORD_REQUIRE_SYMBOLS = True
    PASSWORD_MAX_AGE_DAYS = 90

    # Session management
    SESSION_TIMEOUT_MINUTES = 30
    MAX_CONCURRENT_SESSIONS = 3
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True

    # Encryption settings
    ENCRYPTION_ALGORITHM = 'AES-256-GCM'
    KEY_DERIVATION_ITERATIONS = 100000
    SALT_LENGTH = 32

    # Logging settings
    SECURITY_LOG_LEVEL = 'INFO'
    SECURITY_LOG_FILE = 'security.log'
    SECURITY_LOG_MAX_SIZE = 10 * 1024 * 1024  # 10MB
    SECURITY_LOG_BACKUP_COUNT = 5

    # API security
    API_RATE_LIMIT = 1000  # requests per hour
    API_TIMEOUT_SECONDS = 30
    API_MAX_PAYLOAD_SIZE = 5 * 1024 * 1024  # 5MB

    # Network security
    ALLOWED_IP_RANGES = []  # Empty means allow all, add specific ranges for production
    BLOCKED_IP_RANGES = [
        # Add known malicious IP ranges here
    ]

    # Database security
    DB_CONNECTION_TIMEOUT = 30
    DB_QUERY_TIMEOUT = 60
    DB_MAX_CONNECTIONS = 100

    @classmethod
    def get_encryption_key(cls) -> bytes:
        """
        Get encryption key from environment or generate a secure one

        Returns:
            Encryption key as bytes
        """
        # Try to get from environment first
        key = os.environ.get('ENCRYPTION_KEY')
        if key:
            return key.encode()

        # Fallback to SECRET_KEY
        secret = os.environ.get('SECRET_KEY')
        if secret:
            return secret.encode()

        # Generate a new key (warning: this will change on every restart)
        # In production, always set ENCRYPTION_KEY environment variable
        import hashlib
        return hashlib.sha256(secrets.token_bytes(32)).digest()

    @classmethod
    def get_database_config(cls) -> Dict[str, Any]:
        """
        Get secure database configuration

        Returns:
            Database configuration dictionary
        """
        return {
            'timeout': cls.DB_CONNECTION_TIMEOUT,
            'query_timeout': cls.DB_QUERY_TIMEOUT,
            'max_connections': cls.DB_MAX_CONNECTIONS,
            'ssl_mode': 'require',  # Enforce SSL in production
            'encrypt': True,
        }

    @classmethod
    def get_api_config(cls) -> Dict[str, Any]:
        """
        Get secure API configuration

        Returns:
            API configuration dictionary
        """
        return {
            'rate_limit': cls.API_RATE_LIMIT,
            'timeout': cls.API_TIMEOUT_SECONDS,
            'max_payload_size': cls.API_MAX_PAYLOAD_SIZE,
            'require_auth': True,
            'enable_cors': False,  # Disable CORS unless specifically needed
        }

    @classmethod
    def validate_security_headers(cls) -> Dict[str, str]:
        """
        Get security headers for web responses

        Returns:
            Security headers dictionary
        """
        return cls.SECURITY_HEADERS.copy()

    @classmethod
    def is_password_strong(cls, password: str) -> tuple[bool, List[str]]:
        """
        Validate password strength

        Args:
            password: Password to validate

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []

        if len(password) < cls.PASSWORD_MIN_LENGTH:
            issues.append(f"Password must be at least {cls.PASSWORD_MIN_LENGTH} characters long")

        if cls.PASSWORD_REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
            issues.append("Password must contain at least one uppercase letter")

        if cls.PASSWORD_REQUIRE_LOWERCASE and not any(c.islower() for c in password):
            issues.append("Password must contain at least one lowercase letter")

        if cls.PASSWORD_REQUIRE_NUMBERS and not any(c.isdigit() for c in password):
            issues.append("Password must contain at least one number")

        if cls.PASSWORD_REQUIRE_SYMBOLS and not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            issues.append("Password must contain at least one special character")

        # Check for common weak passwords
        weak_passwords = [
            'password', '123456', 'qwerty', 'admin', 'letmein',
            'welcome', 'monkey', 'dragon', 'master', 'sunshine'
        ]
        if password.lower() in weak_passwords:
            issues.append("Password is too common and weak")

        return len(issues) == 0, issues

    @classmethod
    def get_environment_specific_config(cls) -> Dict[str, Any]:
        """
        Get environment-specific security configuration

        Returns:
            Environment-specific configuration
        """
        env = os.environ.get('ENVIRONMENT', 'development').lower()

        if env == 'production':
            return {
                'debug': False,
                'log_level': 'WARNING',
                'require_https': True,
                'session_secure': True,
                'api_rate_limit': cls.API_RATE_LIMIT // 2,  # Stricter in production
                'enable_monitoring': True,
                'enable_alerts': True,
            }
        elif env == 'staging':
            return {
                'debug': False,
                'log_level': 'INFO',
                'require_https': True,
                'session_secure': True,
                'api_rate_limit': cls.API_RATE_LIMIT,
                'enable_monitoring': True,
                'enable_alerts': False,
            }
        else:  # development
            return {
                'debug': True,
                'log_level': 'DEBUG',
                'require_https': False,
                'session_secure': False,
                'api_rate_limit': cls.API_RATE_LIMIT * 2,  # More lenient in development
                'enable_monitoring': False,
                'enable_alerts': False,
            }


# Global security configuration instance
security_config = SecurityConfig()


def get_security_config() -> SecurityConfig:
    """
    Get global security configuration instance

    Returns:
        SecurityConfig instance
    """
    return security_config


def validate_environment() -> Dict[str, Any]:
    """
    Validate that required security environment variables are set

    Returns:
        Validation results
    """
    required_vars = ['SECRET_KEY']
    recommended_vars = ['ENCRYPTION_KEY', 'DATABASE_URL', 'REDIS_URL']

    results = {
        'valid': True,
        'missing_required': [],
        'missing_recommended': [],
        'warnings': []
    }

    # Check required variables
    for var in required_vars:
        if not os.environ.get(var):
            results['missing_required'].append(var)
            results['valid'] = False

    # Check recommended variables
    for var in recommended_vars:
        if not os.environ.get(var):
            results['missing_recommended'].append(var)

    # Check environment
    env = os.environ.get('ENVIRONMENT', 'development').lower()
    if env == 'production':
        if not os.environ.get('ENCRYPTION_KEY'):
            results['warnings'].append("ENCRYPTION_KEY not set in production environment")
        if not os.environ.get('DATABASE_URL') or 'localhost' in os.environ.get('DATABASE_URL', ''):
            results['warnings'].append("Using localhost database in production environment")

    return results


if __name__ == "__main__":
    print("🔒 Security Configuration Test")

    # Test environment validation
    env_validation = validate_environment()
    print(f"\nEnvironment Validation:")
    print(f"  Valid: {'✅' if env_validation['valid'] else '❌'}")
    if env_validation['missing_required']:
        print(f"  Missing Required: {env_validation['missing_required']}")
    if env_validation['missing_recommended']:
        print(f"  Missing Recommended: {env_validation['missing_recommended']}")
    if env_validation['warnings']:
        print(f"  Warnings: {env_validation['warnings']}")

    # Test password validation
    print(f"\nPassword Validation Tests:")
    test_passwords = [
        'weak', 'strongPassword123!', 'PASSWORD', '12345678', 'ComplexPass123!'
    ]

    for password in test_passwords:
        is_strong, issues = SecurityConfig.is_password_strong(password)
        status = '✅' if is_strong else '❌'
        print(f"  '{password}': {status}")
        if issues:
            for issue in issues:
                print(f"    - {issue}")

    # Test encryption key generation
    print(f"\nEncryption Key Test:")
    key = SecurityConfig.get_encryption_key()
    print(f"  Key length: {len(key)} bytes")
    print(f"  Key available: {'✅' if key else '❌'}")

    print(f"\n🎉 Security configuration test completed!")