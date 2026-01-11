"""
Authentication Service Configuration
Environment-specific configuration settings
"""

import os
from typing import Dict, Any, Optional
from pydantic import BaseSettings, Field


class AuthConfig(BaseSettings):
    """Authentication configuration"""

    # Database
    database_url: str = Field(
        default="postgresql://localhost:5432/cbsc",
        env="DATABASE_URL"
    )

    # JWT Settings
    jwt_private_key: Optional[str] = Field(
        default=None,
        env="JWT_PRIVATE_KEY"
    )
    jwt_public_key: Optional[str] = Field(
        default=None,
        env="JWT_PUBLIC_KEY"
    )
    jwt_private_key_path: Optional[str] = Field(
        default=None,
        env="JWT_PRIVATE_KEY_PATH"
    )
    jwt_public_key_path: Optional[str] = Field(
        default=None,
        env="JWT_PUBLIC_KEY_PATH"
    )
    access_token_expire_minutes: int = Field(
        default=30,
        env="ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    refresh_token_expire_days: int = Field(
        default=7,
        env="REFRESH_TOKEN_EXPIRE_DAYS"
    )

    # Email Settings
    smtp_host: Optional[str] = Field(
        default=None,
        env="SMTP_HOST"
    )
    smtp_port: int = Field(
        default=587,
        env="SMTP_PORT"
    )
    smtp_username: Optional[str] = Field(
        default=None,
        env="SMTP_USERNAME"
    )
    smtp_password: Optional[str] = Field(
        default=None,
        env="SMTP_PASSWORD"
    )
    smtp_use_tls: bool = Field(
        default=True,
        env="SMTP_USE_TLS"
    )
    from_email: str = Field(
        default="noreply@cbsc.com",
        env="FROM_EMAIL"
    )

    # Security Settings
    password_min_length: int = Field(
        default=8,
        env="PASSWORD_MIN_LENGTH"
    )
    password_require_uppercase: bool = Field(
        default=True,
        env="PASSWORD_REQUIRE_UPPERCASE"
    )
    password_require_lowercase: bool = Field(
        default=True,
        env="PASSWORD_REQUIRE_LOWERCASE"
    )
    password_require_numbers: bool = Field(
        default=True,
        env="PASSWORD_REQUIRE_NUMBERS"
    )
    password_require_special: bool = Field(
        default=True,
        env="PASSWORD_REQUIRE_SPECIAL"
    )
    password_history_count: int = Field(
        default=5,
        env="PASSWORD_HISTORY_COUNT"
    )
    password_max_age_days: Optional[int] = Field(
        default=None,
        env="PASSWORD_MAX_AGE_DAYS"
    )

    # Lockout Settings
    lockout_attempts: int = Field(
        default=5,
        env="LOCKOUT_ATTEMPTS"
    )
    lockout_minutes: int = Field(
        default=30,
        env="LOCKOUT_MINUTES"
    )
    lockout_max_hours: int = Field(
        default=8,
        env="LOCKOUT_MAX_HOURS"
    )

    # MFA Settings
    mfa_required: bool = Field(
        default=False,
        env="MFA_REQUIRED"
    )
    mfa_issuer: str = Field(
        default="CBSC",
        env="MFA_ISSUER"
    )

    # Rate Limiting
    rate_limit_enabled: bool = Field(
        default=True,
        env="RATE_LIMIT_ENABLED"
    )
    rate_limit_requests_per_minute: int = Field(
        default=60,
        env="RATE_LIMIT_REQUESTS_PER_MINUTE"
    )
    rate_limit_requests_per_hour: int = Field(
        default=1000,
        env="RATE_LIMIT_REQUESTS_PER_HOUR"
    )

    # Redis Settings
    redis_host: str = Field(
        default="localhost",
        env="REDIS_HOST"
    )
    redis_port: int = Field(
        default=6379,
        env="REDIS_PORT"
    )
    redis_db: int = Field(
        default=0,
        env="REDIS_DB"
    )
    redis_password: Optional[str] = Field(
        default=None,
        env="REDIS_PASSWORD"
    )

    # Session Settings
    session_timeout_minutes: int = Field(
        default=30,
        env="SESSION_TIMEOUT_MINUTES"
    )
    max_sessions_per_user: int = Field(
        default=5,
        env="MAX_SESSIONS_PER_USER"
    )

    # Audit Settings
    audit_log_retention_days: int = Field(
        default=365,
        env="AUDIT_LOG_RETENTION_DAYS"
    )
    audit_sensitive_operations: bool = Field(
        default=True,
        env="AUDIT_SENSITIVE_OPERATIONS"
    )

    # CORS Settings
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:8080",
        env="CORS_ORIGINS"
    )
    cors_allow_credentials: bool = Field(
        default=True,
        env="CORS_ALLOW_CREDENTIALS"
    )

    # Security Headers
    security_headers_enabled: bool = Field(
        default=True,
        env="SECURITY_HEADERS_ENABLED"
    )
    hsts_max_age: int = Field(
        default=31536000,
        env="HSTS_MAX_AGE"
    )

    # Development
    debug: bool = Field(
        default=False,
        env="DEBUG"
    )
    testing: bool = Field(
        default=False,
        env="TESTING"
    )

    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def cors_origins_list(self) -> list:
        """Get CORS origins as list"""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def password_policy(self) -> Dict[str, Any]:
        """Get password policy dictionary"""
        return {
            "min_length": self.password_min_length,
            "require_uppercase": self.password_require_uppercase,
            "require_lowercase": self.password_require_lowercase,
            "require_numbers": self.password_require_numbers,
            "require_special": self.password_require_special,
            "prevent_common": True,
            "prevent_username": True,
            "max_age_days": self.password_max_age_days,
            "history_count": self.password_history_count,
            "lockout_attempts": self.lockout_attempts,
            "lockout_minutes": self.lockout_minutes
        }

    @property
    def redis_url(self) -> str:
        """Get Redis connection URL"""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"


# Create global config instance
config = AuthConfig()


def get_config() -> AuthConfig:
    """Get configuration instance"""
    return config


def load_config_from_file(file_path: str) -> AuthConfig:
    """Load configuration from file"""
    if os.path.exists(file_path):
        return AuthConfig(_env_file=file_path)
    return config


def generate_jwt_keys_if_not_exists():
    """Generate JWT keys if they don't exist"""
    if not config.jwt_private_key and not config.jwt_private_key_path:
        # Generate keys and save to files
        from .utils import generate_rsa_keys
        import os

        keys_dir = os.path.join(os.path.dirname(__file__), "keys")
        os.makedirs(keys_dir, exist_ok=True)

        private_key_path = os.path.join(keys_dir, "jwt_private.pem")
        public_key_path = os.path.join(keys_dir, "jwt_public.pem")

        if not os.path.exists(private_key_path):
            private_key, public_key = generate_rsa_keys()

            with open(private_key_path, "w") as f:
                f.write(private_key)
            with open(public_key_path, "w") as f:
                f.write(public_key)

            # Set file permissions
            os.chmod(private_key_path, 0o600)
            os.chmod(public_key_path, 0o644)

            config.jwt_private_key_path = private_key_path
            config.jwt_public_key_path = public_key_path


def validate_config():
    """Validate configuration settings"""
    errors = []

    # Database
    if not config.database_url:
        errors.append("DATABASE_URL is required")

    # JWT
    if not config.jwt_private_key and not config.jwt_private_key_path:
        errors.append("JWT_PRIVATE_KEY or JWT_PRIVATE_KEY_PATH is required")

    # Email (optional but recommended)
    if not config.smtp_host and not config.testing:
        errors.append("SMTP_HOST is recommended for email functionality")

    # Password policy
    if config.password_min_length < 6:
        errors.append("Password minimum length should be at least 6")

    if errors:
        raise ValueError("\n".join(errors))

    return True


# Environment-specific presets
def get_development_config() -> AuthConfig:
    """Get development configuration preset"""
    return AuthConfig(
        debug=True,
        testing=False,
        database_url="postgresql://localhost:5432/cbsc_dev",
        redis_host="localhost",
        cors_origins="http://localhost:3000,http://localhost:8080",
        rate_limit_enabled=False,
        audit_sensitive_operations=False
    )


def get_testing_config() -> AuthConfig:
    """Get testing configuration preset"""
    return AuthConfig(
        debug=True,
        testing=True,
        database_url="sqlite:///:memory:",
        redis_host=None,  # Disable Redis in tests
        cors_origins="*",
        rate_limit_enabled=False,
        mfa_required=False,
        audit_sensitive_operations=False
    )


def get_production_config() -> AuthConfig:
    """Get production configuration preset"""
    return AuthConfig(
        debug=False,
        testing=False,
        password_min_length=12,
        password_max_age_days=90,
        mfa_required=True,
        rate_limit_enabled=True,
        security_headers_enabled=True,
        hsts_max_age=31536000,
        audit_sensitive_operations=True
    )


# Profile-based configuration loading
def load_config(profile: str = None) -> AuthConfig:
    """
    Load configuration based on profile

    Args:
        profile: Configuration profile (development, testing, production)

    Returns:
        AuthConfig instance
    """
    profile = profile or os.getenv("CONFIG_PROFILE", "development")

    if profile == "development":
        return get_development_config()
    elif profile == "testing":
        return get_testing_config()
    elif profile == "production":
        return get_production_config()
    else:
        return config