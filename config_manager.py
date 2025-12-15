#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration Manager for CBSC Strategy API
CBSC策略API配置管理器

Production environment configuration setup and validation
生产环境配置设置和验证
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import secrets
import hashlib

class ConfigurationManager:
    """Configuration Manager for production deployment"""

    def __init__(self, env_file: str = ".env"):
        self.env_file = env_file
        self.env_example_file = ".env.example"
        self.required_vars = {
            "production": [
                "ENVIRONMENT",
                "DATABASE_URL",
                "JWT_SECRET",
                "POSTGRES_DB",
                "POSTGRES_USER",
                "POSTGRES_PASSWORD",
                "REDIS_URL"
            ],
            "development": [
                "ENVIRONMENT",
                "DATABASE_URL",
                "REDIS_URL"
            ]
        }

    def generate_secure_key(self, length: int = 64) -> str:
        """Generate secure random key"""
        return secrets.token_urlsafe(length)

    def hash_password(self, password: str) -> str:
        """Hash password for storage"""
        return hashlib.sha256(password.encode()).hexdigest()

    def create_production_env(self, override_existing: bool = False) -> bool:
        """Create production environment file"""
        if os.path.exists(self.env_file) and not override_existing:
            print(f"[WARN] {self.env_file} already exists. Use override_existing=True to overwrite.")
            return False

        print("Creating production environment configuration...")

        # Generate secure values
        jwt_secret = self.generate_secure_key(64)
        session_secret = self.generate_secure_key(64)
        postgres_password = self.generate_secure_key(32) + "Pw!"
        redis_password = self.generate_secure_key(32)

        # Production environment content
        production_config = f"""# CBSC Strategy API Production Environment Configuration
# Generated on: {os.popen('date').read().strip()}
# Environment: production

# =============================================================================
# Application Environment
# =============================================================================
ENVIRONMENT=production
LOG_LEVEL=INFO
DEBUG=false

# =============================================================================
# Database Configuration
# =============================================================================
POSTGRES_DB=cbsc_production
POSTGRES_USER=cbsc_admin
POSTGRES_PASSWORD={postgres_password}
DATABASE_URL=postgresql://cbsc_admin:{postgres_password}@localhost:5432/cbsc_production

# Database Pool Configuration
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600

# =============================================================================
# Cache Configuration
# =============================================================================
REDIS_URL=redis://localhost:6379
REDIS_PASSWORD={redis_password}
CACHE_TTL=3600
CACHE_PREFIX=cbsc_prod
CACHE_MAX_SIZE=1000

# =============================================================================
# Security Configuration
# =============================================================================
JWT_SECRET={jwt_secret}
JWT_ALGORITHM=HS256
TOKEN_EXPIRE_MINUTES=1440
SESSION_SECRET={session_secret}
SESSION_TIMEOUT=3600

# =============================================================================
# API Configuration
# =============================================================================
API_HOST=0.0.0.0
API_PORT=3004
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Rate Limiting
RATE_LIMIT_ENABLED=true
MAX_REQUESTS_PER_IP=1000
RATE_LIMIT_WINDOW=60

# =============================================================================
# Monitoring Configuration
# =============================================================================
GRAFANA_PASSWORD={self.generate_secure_key(16)}
PROMETHEUS_RETENTION=30d

# =============================================================================
# Performance Configuration
# =============================================================================
WORKERS=4
WORKER_CONNECTIONS=1000
MAX_REQUESTS=10000
KEEP_ALIVE=2

# =============================================================================
# SSL/TLS Configuration
# =============================================================================
SSL_ENABLED=false
# SSL_CERT_PATH=/app/ssl/cert.pem
# SSL_KEY_PATH=/app/ssl/key.pem

# =============================================================================
# Logging Configuration
# =============================================================================
LOG_FORMAT=json
LOG_FILE_PATH=/app/logs/app.log
LOG_MAX_SIZE=100MB
LOG_BACKUP_COUNT=10

# =============================================================================
# Email Configuration (Optional)
# =============================================================================
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_TLS=true
FROM_EMAIL=noreply@yourdomain.com
FROM_NAME=CBSC Strategy API

# =============================================================================
# External Services
# =============================================================================
FRONTEND_URL=https://yourdomain.com
WEBHOOK_URL=https://hooks.slack.com/your/slack/webhook
NOTIFICATION_EMAIL=admin@yourdomain.com
"""

        # Write to file
        with open(self.env_file, 'w', encoding='utf-8') as f:
            f.write(production_config)

        print(f"[OK] Production environment file created: {self.env_file}")
        print("\n[IMPORTANT] Security Configuration Generated:")
        print(f"  JWT Secret: {jwt_secret[:16]}...")
        print(f"  Session Secret: {session_secret[:16]}...")
        print(f"  PostgreSQL Password: {postgres_password[:8]}...")
        print(f"  Redis Password: {redis_password[:8]}...")
        print("\n[SECURITY] Store these secrets securely!")

        return True

    def create_development_env(self, override_existing: bool = False) -> bool:
        """Create development environment file"""
        dev_env_file = ".env.development"

        if os.path.exists(dev_env_file) and not override_existing:
            print(f"[WARN] {dev_env_file} already exists. Use override_existing=True to overwrite.")
            return False

        print("Creating development environment configuration...")

        dev_config = f"""# CBSC Strategy API Development Environment Configuration
# Generated on: {os.popen('date').read().strip()}

# =============================================================================
# Application Environment
# =============================================================================
ENVIRONMENT=development
LOG_LEVEL=DEBUG
DEBUG=true

# =============================================================================
# Database Configuration (Development)
# =============================================================================
POSTGRES_DB=cbsc_development
POSTGRES_USER=cbsc_dev
POSTGRES_PASSWORD=dev_password_123
DATABASE_URL=postgresql://cbsc_dev:dev_password_123@localhost:5432/cbsc_development

# =============================================================================
# Cache Configuration (Development)
# =============================================================================
REDIS_URL=redis://localhost:6379
CACHE_TTL=1800
CACHE_PREFIX=cbsc_dev
CACHE_MAX_SIZE=500

# =============================================================================
# Security Configuration (Development - Less Secure!)
# =============================================================================
JWT_SECRET=dev_jwt_secret_change_in_production_123456
JWT_ALGORITHM=HS256
TOKEN_EXPIRE_MINUTES=480
SESSION_SECRET=dev_session_secret_change_in_production

# =============================================================================
# API Configuration
# =============================================================================
API_HOST=127.0.0.1
API_PORT=3004
CORS_ORIGINS=http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000,http://127.0.0.1:3001

# Rate Limiting (Disabled for development)
RATE_LIMIT_ENABLED=false

# =============================================================================
# Logging Configuration
# =============================================================================
LOG_FORMAT=console
LOG_FILE_PATH=logs/app.log

# =============================================================================
# Development Services
# =============================================================================
FRONTEND_URL=http://localhost:3000
"""

        # Write to file
        with open(dev_env_file, 'w', encoding='utf-8') as f:
            f.write(dev_config)

        print(f"[OK] Development environment file created: {dev_env_file}")
        return True

    def validate_configuration(self, environment: str = "production") -> Dict[str, Any]:
        """Validate environment configuration"""
        print(f"Validating {environment} environment configuration...")

        if not os.path.exists(self.env_file):
            return {
                "status": "error",
                "message": f"{self.env_file} not found"
            }

        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv(self.env_file)

        required = self.required_vars.get(environment, [])
        missing = []
        warnings = []

        for var in required:
            value = os.getenv(var)
            if not value:
                missing.append(var)
            elif "password" in var.lower() and len(value) < 16:
                warnings.append(f"{var} - Password too short (should be at least 16 characters)")
            elif "secret" in var.lower() and len(value) < 32:
                warnings.append(f"{var} - Secret too short (should be at least 32 characters)")

        # Check additional security items
        security_checks = {
            "JWT_SECRET": os.getenv("JWT_SECRET"),
            "SESSION_SECRET": os.getenv("SESSION_SECRET"),
            "POSTGRES_PASSWORD": os.getenv("POSTGRES_PASSWORD")
        }

        insecure_defaults = ["dev", "test", "example", "change", "default"]
        for key, value in security_checks.items():
            if value and any(default in value.lower() for default in insecure_defaults):
                missing.append(f"{key} - Using insecure default value")

        if missing:
            return {
                "status": "error",
                "message": "Missing or insecure configuration variables",
                "missing": missing,
                "warnings": warnings
            }

        if warnings:
            return {
                "status": "warning",
                "message": "Configuration has security warnings",
                "warnings": warnings
            }

        return {
            "status": "success",
            "message": "Configuration is valid",
            "environment": environment
        }

    def show_configuration_summary(self) -> None:
        """Show current configuration summary"""
        if not os.path.exists(self.env_file):
            print(f"[ERROR] {self.env_file} not found")
            return

        from dotenv import load_dotenv
        load_dotenv(self.env_file)

        print("\n" + "=" * 60)
        print("CURRENT CONFIGURATION SUMMARY")
        print("=" * 60)

        print(f"Environment: {os.getenv('ENVIRONMENT', 'Not set')}")
        print(f"API Host: {os.getenv('API_HOST', 'Not set')}")
        print(f"API Port: {os.getenv('API_PORT', 'Not set')}")
        print(f"Database URL: {os.getenv('DATABASE_URL', 'Not set')[:50]}...")
        print(f"Redis URL: {os.getenv('REDIS_URL', 'Not set')}")
        print(f"CORS Origins: {os.getenv('CORS_ORIGINS', 'Not set')}")
        print(f"Log Level: {os.getenv('LOG_LEVEL', 'Not set')}")
        print(f"Rate Limiting: {os.getenv('RATE_LIMIT_ENABLED', 'Not set')}")
        print(f"Workers: {os.getenv('WORKERS', 'Not set')}")
        print("=" * 60)

def main():
    """Main configuration manager"""
    print("=" * 60)
    print("CBSC STRATEGY API CONFIGURATION MANAGER")
    print("=" * 60)

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python config_manager.py <command> [options]")
        print()
        print("Commands:")
        print("  create-prod     Create production environment file")
        print("  create-dev      Create development environment file")
        print("  validate-prod   Validate production configuration")
        print("  validate-dev    Validate development configuration")
        print("  summary         Show current configuration summary")
        print()
        print("Options:")
        print("  --override      Override existing files")
        sys.exit(1)

    command = sys.argv[1]
    config_manager = ConfigurationManager()

    if command == "create-prod":
        override = "--override" in sys.argv
        success = config_manager.create_production_env(override)
        if success:
            print("\n[INFO] Next steps:")
            print("1. Review the generated .env file")
            print("2. Update database and Redis connection details")
            print("3. Set your domain and external service URLs")
            print("4. Run validation: python config_manager.py validate-prod")

    elif command == "create-dev":
        override = "--override" in sys.argv
        success = config_manager.create_development_env(override)
        if success:
            print("\n[INFO] Development environment ready!")
            print("To use: cp .env.development .env")

    elif command == "validate-prod":
        result = config_manager.validate_configuration("production")

        if result["status"] == "success":
            print(f"[OK] {result['message']}")
        elif result["status"] == "warning":
            print(f"[WARN] {result['message']}")
            for warning in result.get("warnings", []):
                print(f"  - {warning}")
        else:
            print(f"[ERROR] {result['message']}")
            for item in result.get("missing", []):
                print(f"  - {item}")

    elif command == "validate-dev":
        result = config_manager.validate_configuration("development")

        if result["status"] == "success":
            print(f"[OK] {result['message']}")
        elif result["status"] == "warning":
            print(f"[WARN] {result['message']}")
            for warning in result.get("warnings", []):
                print(f"  - {warning}")
        else:
            print(f"[ERROR] {result['message']}")
            for item in result.get("missing", []):
                print(f"  - {item}")

    elif command == "summary":
        config_manager.show_configuration_summary()

    else:
        print(f"[ERROR] Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()