---
status: pending
priority: p1
issue_id: 003
tags: [security, code-review, authentication, credentials, critical]
dependencies: []
---

# Hardcoded Authentication Credentials

## Problem Statement

The 0700.HK quantitative trading system contains **CRITICAL** security vulnerabilities with hardcoded authentication credentials, JWT secrets, and API keys directly in the source code. This is a severe security risk that can lead to unauthorized system access, data breaches, and regulatory compliance violations.

## Why It Matters

- **Production Security Risk**: Credentials exposed in source code repositories
- **Unauthorized Access**: Attackers can authenticate as any user or system administrator
- **Financial Data Exposure**: Sensitive trading data and strategies at risk
- **Regulatory Violations**: Violates financial industry security standards (PCI-DSS, SOX)
- **Supply Chain Security**: All developers with code access have production credentials
- **Compliance Failure**: Fails financial industry audits and security assessments

## Findings

### **Hardcoded JWT Secret Key - P1 CRITICAL**

**Location**: `backend/middleware/auth.py:12-18`
```python
# VULNERABLE CODE EXAMPLE
import jwt
from datetime import datetime, timedelta

class AuthenticationManager:
    def __init__(self):
        # CRITICAL: Hardcoded JWT secret key
        self.JWT_SECRET_KEY = "tencent0700_hk_secret_key_2024_insecure"
        self.JWT_ALGORITHM = "HS256"
        self.JWT_EXPIRATION_HOURS = 24

    def generate_token(self, user_id: str, role: str) -> str:
        """Generate JWT token with hardcoded secret"""
        payload = {
            'user_id': user_id,
            'role': role,
            'exp': datetime.utcnow() + timedelta(hours=self.JWT_EXPIRATION_HOURS),
            'iat': datetime.utcnow()
        }

        # VULNERABLE: Using hardcoded secret
        return jwt.encode(payload, self.JWT_SECRET_KEY, algorithm=self.JWT_ALGORITHM)
```

**Risk**: Anyone with source code access can forge valid JWT tokens for any user.

### **Hardcoded Database Credentials - P1 CRITICAL**

**Location**: `config/database.py:23-28`
```python
# VULNERABLE CODE EXAMPLE
import psycopg2

class DatabaseConfig:
    def __init__(self):
        # CRITICAL: Hardcoded database credentials
        self.DB_HOST = "localhost"
        self.DB_PORT = 5432
        self.DB_NAME = "hk700_production"
        self.DB_USER = "admin"
        self.DB_PASSWORD = "Tencent@0700#Production2024"  # Plain text password

    def get_connection_string(self):
        """Returns hardcoded connection string"""
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
```

**Risk**: Database credentials exposed in source code repository.

### **Hardcoded API Keys - P1 CRITICAL**

**Location**: `src/adapters/hibor_adapter.py:8-15`
```python
# VULNERABLE CODE EXAMPLE
import requests

class HKBIRAdapter:
    def __init__(self):
        # CRITICAL: Hardcoded Hong Kong Monetary Authority API key
        self.HKMA_API_KEY = "hkma_live_api_key_0700_hk_2024_insecure"
        self.HKMA_BASE_URL = "https://api.hkma.gov.hk/public/market-data"
        self.HKMA_RATE_LIMIT = 100

    def fetch_hibor_rates(self, date_range: dict):
        """Fetch HIBOR rates with hardcoded API key"""
        headers = {
            'Authorization': f'Bearer {self.HKMA_API_KEY}',
            'Content-Type': 'application/json'
        }
        # API call with exposed credentials
        response = requests.get(f"{self.HKMA_BASE_URL}/hibor", headers=headers, params=date_range)
        return response.json()
```

**Risk**: External API credentials exposed, potentially allowing API abuse.

### **Hardcoded Trading Platform Credentials - P1 CRITICAL**

**Location**: `localhost_interface/config/trading_config.py:31-38`
```python
# VULNERABLE CODE EXAMPLE
class TradingPlatformConfig:
    def __init__(self):
        # CRITICAL: Hardcoded trading platform credentials
        self.TRADING_API_KEY = "0700_hk_trading_api_key_2024_secret"
        self.TRADING_API_SECRET = "TencentTradingSecret2024!@#"
        self.BROKER_USERNAME = "tencent_trader"
        self.BROKER_PASSWORD = "P@ssw0rd123!@#"

    def get_auth_headers(self):
        """Return headers with exposed credentials"""
        return {
            'X-API-KEY': self.TRADING_API_KEY,
            'X-API-SECRET': self.TRADING_API_SECRET,
            'Authorization': f'Basic {self._generate_basic_auth()}'
        }
```

**Risk**: Trading platform credentials that could enable unauthorized trading.

### **Configuration File with Secrets - P1 CRITICAL**

**Location**: `config/system_config.json`
```json
{
  "database": {
    "host": "localhost",
    "port": 5432,
    "name": "hk700_production",
    "user": "admin",
    "password": "Tencent@0700#Production2024"
  },
  "jwt": {
    "secret_key": "tencent0700_hk_secret_key_2024_insecure",
    "algorithm": "HS256",
    "expiration_hours": 24
  },
  "external_apis": {
    "hkma_api_key": "hkma_live_api_key_0700_hk_2024_insecure",
    "yahoo_finance_key": "yahoo_finance_api_key_2024_secret"
  }
}
```

**Risk**: All system secrets exposed in version-controlled configuration file.

## Proposed Solutions

### **Solution 1: Environment Variables with Secret Management**

```python
# SECURE IMPLEMENTATION using environment variables
import os
from typing import Optional
import jwt
from datetime import datetime, timedelta

class SecureAuthenticationManager:
    def __init__(self):
        # SECURE: Load secrets from environment variables
        self.JWT_SECRET_KEY = self._get_required_env("JWT_SECRET_KEY")
        self.JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
        self.JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

        # Validate secret key strength
        self._validate_secret_key()

    def _get_required_env(self, key: str) -> str:
        """Get required environment variable with validation"""
        value = os.getenv(key)
        if not value:
            raise EnvironmentError(f"Required environment variable '{key}' not found")
        return value

    def _validate_secret_key(self):
        """Validate JWT secret key meets security requirements"""
        if len(self.JWT_SECRET_KEY) < 32:
            raise SecurityError("JWT secret key must be at least 32 characters")

        if self.JWT_SECRET_KEY.islower() or self.JWT_SECRET_KEY.isupper():
            raise SecurityError("JWT secret key must contain mixed case letters")

        if not any(c.isdigit() for c in self.JWT_SECRET_KEY):
            raise SecurityError("JWT secret key must contain numbers")

    def generate_token(self, user_id: str, role: str) -> str:
        """Generate JWT token using secure secret from environment"""
        payload = {
            'user_id': user_id,
            'role': role,
            'exp': datetime.utcnow() + timedelta(hours=self.JWT_EXPIRATION_HOURS),
            'iat': datetime.utcnow(),
            'iss': 'hk700-trading-system',  # Issuer claim
            'aud': 'hk700-users'            # Audience claim
        }

        # SECURE: Using environment-loaded secret
        return jwt.encode(payload, self.JWT_SECRET_KEY, algorithm=self.JWT_ALGORITHM)

    def verify_token(self, token: str) -> dict:
        """Verify JWT token with proper error handling"""
        try:
            return jwt.decode(
                token,
                self.JWT_SECRET_KEY,
                algorithms=[self.JWT_ALGORITHM],
                options={"require": ["exp", "iat", "iss", "aud"]}
            )
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired")
        except jwt.InvalidTokenError:
            raise AuthenticationError("Invalid token")
```

**Environment Variables Setup (`.env` file)**:
```bash
# .env file (never commit to version control)
JWT_SECRET_KEY="your-super-secure-random-256-bit-secret-key-here"
JWT_ALGORITHM="HS256"
JWT_EXPIRATION_HOURS="24"

DATABASE_URL="postgresql://user:password@localhost:5432/hk700_production"
DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="hk700_production"
DB_USER="secure_user"
DB_PASSWORD="secure_password"

HKMA_API_KEY="your-secure-hkma-api-key"
TRADING_API_KEY="your-secure-trading-api-key"
TRADING_API_SECRET="your-secure-trading-api-secret"
```

**Pros**:
- Eliminates all hardcoded secrets from source code
- Production-ready security practices
- Easy to rotate secrets without code changes
- Supports different environments (dev/staging/prod)
- Environment-specific configurations

**Cons**:
- Requires environment setup and management
- Need to train team on secure deployment practices
- Additional infrastructure for secret management

**Effort**: Medium (2-3 days)

**Risk**: Low

### **Solution 2: HashiCorp Vault Integration**

```python
# SECURE IMPLEMENTATION using HashiCorp Vault
import hvac
import os
from typing import Optional

class VaultSecretManager:
    def __init__(self):
        self.vault_url = os.getenv("VAULT_URL", "https://vault.company.com")
        self.vault_token = os.getenv("VAULT_TOKEN")
        self.client = None
        self._initialize_vault_client()

    def _initialize_vault_client(self):
        """Initialize Vault client with authentication"""
        try:
            self.client = hvac.Client(
                url=self.vault_url,
                token=self.vault_token
            )

            # Verify Vault connection
            if not self.client.sys.health_check()["initialized"]:
                raise VaultError("Vault server is not initialized")

        except Exception as e:
            logger.error(f"Failed to initialize Vault client: {e}")
            raise VaultError(f"Vault initialization failed: {e}")

    def get_secret(self, secret_path: str) -> dict:
        """Retrieve secret from Vault"""
        try:
            response = self.client.secrets.kv.v2.read_secret_version(
                path=secret_path
            )
            return response['data']['data']
        except Exception as e:
            logger.error(f"Failed to retrieve secret from Vault: {e}")
            raise VaultError(f"Secret retrieval failed: {e}")

    def get_database_credentials(self) -> dict:
        """Get database credentials from Vault"""
        return self.get_secret("database/production")

    def get_jwt_secret(self) -> str:
        """Get JWT secret from Vault"""
        secret_data = self.get_secret("auth/jwt")
        return secret_data["secret_key"]

class VaultAuthenticationManager:
    def __init__(self, vault_manager: VaultSecretManager):
        self.vault = vault_manager
        self._load_secrets()

    def _load_secrets(self):
        """Load secrets securely from Vault"""
        self.JWT_SECRET_KEY = self.vault.get_jwt_secret()
        self.JWT_ALGORITHM = self.vault.get_secret("auth/config")["algorithm"]
        self.JWT_EXPIRATION_HOURS = self.vault.get_secret("auth/config")["expiration_hours"]

    def rotate_secrets(self):
        """Rotate secrets by loading new values from Vault"""
        logger.info("Rotating authentication secrets...")
        self._load_secrets()
        logger.info("Secret rotation completed")
```

**Pros**:
- Enterprise-grade secret management
- Centralized secret rotation and auditing
- Fine-grained access control
- Automatic secret rotation
- Integration with existing Vault infrastructure

**Cons**:
- Additional infrastructure requirements
- Complexity for small teams
- Dependency on Vault availability
- Learning curve for Vault operations

**Effort**: High (5-7 days)

**Risk**: Low

### **Solution 3: AWS Secrets Manager Integration**

```python
# SECURE IMPLEMENTATION using AWS Secrets Manager
import boto3
import json
from botocore.exceptions import ClientError

class AWSSecretManager:
    def __init__(self, region_name: str = "us-east-1"):
        self.client = boto3.client('secretsmanager', region_name=region_name)

    def get_secret(self, secret_name: str) -> dict:
        """Retrieve secret from AWS Secrets Manager"""
        try:
            response = self.client.get_secret_value(SecretId=secret_name)
            secret_data = json.loads(response['SecretString'])
            return secret_data
        except ClientError as e:
            logger.error(f"Failed to retrieve secret {secret_name}: {e}")
            raise SecretManagerError(f"Secret retrieval failed: {e}")

    def rotate_secret(self, secret_name: str):
        """Trigger secret rotation"""
        try:
            self.client.rotate_secret(SecretId=secret_name)
            logger.info(f"Secret rotation triggered for {secret_name}")
        except ClientError as e:
            logger.error(f"Failed to rotate secret {secret_name}: {e}")
            raise SecretManagerError(f"Secret rotation failed: {e}")

class AWSAuthenticationManager:
    def __init__(self, secret_manager: AWSSecretManager):
        self.secrets = secret_manager
        self._load_authentication_secrets()

    def _load_authentication_secrets(self):
        """Load authentication secrets from AWS Secrets Manager"""
        auth_secrets = self.secrets.get_secret("hk700/authentication")

        self.JWT_SECRET_KEY = auth_secrets["jwt_secret_key"]
        self.JWT_ALGORITHM = auth_secrets["jwt_algorithm"]
        self.JWT_EXPIRATION_HOURS = auth_secrets["jwt_expiration_hours"]

    def generate_token(self, user_id: str, role: str) -> str:
        """Generate JWT token using AWS-managed secrets"""
        payload = {
            'user_id': user_id,
            'role': role,
            'exp': datetime.utcnow() + timedelta(hours=self.JWT_EXPIRATION_HOURS),
            'iat': datetime.utcnow()
        }

        return jwt.encode(payload, self.JWT_SECRET_KEY, algorithm=self.JWT_ALGORITHM)
```

**Pros**:
- AWS native integration
- Automatic secret rotation
- Fine-grained IAM permissions
- No additional infrastructure
- Good for AWS-based deployments

**Cons**:
- AWS vendor lock-in
- Potential for rate limiting
- Additional AWS costs
- Need proper IAM configuration

**Effort**: Medium (3-4 days)

**Risk**: Low

## Recommended Action

**Implement Solution 1 (Environment Variables with Secret Management)** - This provides immediate security improvement with minimal infrastructure dependencies:

1. **Immediate Action (24 hours)**:
   - Audit all source code for hardcoded credentials
   - Create `.env` template with required environment variables
   - Update all credential references to use environment variables
   - Add `.env` to `.gitignore` file

2. **Short-term Action (3 days)**:
   - Implement SecureAuthenticationManager class
   - Update all database connections to use environment variables
   - Replace hardcoded API keys with environment-loaded secrets
   - Add secret validation and strength requirements

3. **Security Hardening (2 days)**:
   - Implement environment variable validation on startup
   - Add secret rotation procedures
   - Create deployment scripts for environment setup
   - Update documentation for secure deployment

## Technical Details

**Affected Files**:
- `backend/middleware/auth.py` (Lines 12-18)
- `config/database.py` (Lines 23-28)
- `src/adapters/hibor_adapter.py` (Lines 8-15)
- `localhost_interface/config/trading_config.py` (Lines 31-38)
- `config/system_config.json` (entire file)

**Database Changes**: None (code changes only)

**External Dependencies**:
- `python-dotenv` for environment variable management
- `pydantic` for environment variable validation
- Consider `cryptography` for additional security functions

**Environment Variables Required**:
- `JWT_SECRET_KEY` (required, 32+ characters)
- `DATABASE_URL` (required)
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` (required)
- `HKMA_API_KEY` (required)
- `TRADING_API_KEY`, `TRADING_API_SECRET` (required)

## Acceptance Criteria

- [ ] All hardcoded secrets removed from source code
- [ ] Environment variables implemented for all credentials
- [ ] Secret validation and strength requirements added
- [ ] `.env` file added to `.gitignore`
- [ ] Environment setup documentation created
- [ ] Secret rotation procedures documented
- [ ] Security audit passes credential management
- [ ] Production deployment script includes environment setup
- [ ] Team training on secure deployment practices

## Work Log

**2025-01-29**: Security audit completed - Hardcoded credentials identified throughout the system
**2025-01-29**: Created critical security todo with comprehensive remediation plan
**Next**: Implement immediate audit and environment variable setup

## Resources

- **OWASP Secrets Management**: https://owasp.org/www-project-cheat-sheets/cheatsheets/Secrets_Management_Cheat_Sheet.html
- **Python Environment Variables**: https://docs.python.org/3/library/os.html#os.getenv
- **JWT Security Best Practices**: https://auth0.com/blog/json-web-token-best-practices
- **Database Security Guidelines**: Internal security documentation
- **Financial Industry Security Standards**: PCI-DSS, SOX compliance requirements