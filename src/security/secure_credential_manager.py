"""
Secure Credential Manager - Handles Authentication Information Securely
Created: 2025-11-30
Purpose: Replace hardcoded credentials with secure management system
"""

import os
import json
import logging
import hashlib
import secrets
from typing import Dict, Optional, Any, Union
from dataclasses import dataclass
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

logger = logging.getLogger(__name__)

class CredentialSecurityError(Exception):
    """Credential security related error"""
    pass

@dataclass
class CredentialInfo:
    """Secure credential information"""
    name: str
    value: Optional[str] = None
    encrypted_value: Optional[str] = None
    is_encrypted: bool = True
    last_rotated: Optional[str] = None
    rotation_required: bool = False
    access_log: list = None

    def __post_init__(self):
        if self.access_log is None:
            self.access_log = []

class SecureCredentialManager:
    """Secure credential management system"""

    def __init__(self, master_password: Optional[str] = None):
        """
        Initialize secure credential manager

        Args:
            master_password: Master password for encryption. If None, uses environment variable.
        """
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.credential_store = {}
        self.encrypted_file = Path("config/secure_credentials.enc")
        self.salt_file = Path("config/.salt")

        # Get master password from environment or parameter
        self.master_password = master_password or os.environ.get('CREDENTIAL_MASTER_PASSWORD')

        if not self.master_password:
            # Generate a warning and use environment-based encryption
            self.logger.warning("No master password provided. Using environment-based encryption.")
            self.master_password = self._generate_environment_key()

        # Initialize encryption
        self.cipher_suite = self._initialize_encryption()

        # Load existing credentials
        self._load_credentials()

    def _generate_environment_key(self) -> str:
        """Generate encryption key from environment"""
        # Combine multiple environment factors
        env_string = f"{os.environ.get('USERNAME', '')}{os.environ.get('COMPUTERNAME', '')}{os.environ.get('USERDOMAIN', '')}"
        return hashlib.sha256(env_string.encode()).hexdigest()[:32]

    def _initialize_encryption(self) -> Fernet:
        """Initialize encryption cipher suite"""
        try:
            # Load or generate salt
            if self.salt_file.exists():
                with open(self.salt_file, 'rb') as f:
                    salt = f.read()
            else:
                salt = os.urandom(16)
                with open(self.salt_file, 'wb') as f:
                    f.write(salt)
                # Set file permissions
                os.chmod(self.salt_file, 0o600)

            # Derive key using PBKDF2
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(self.master_password.encode()))
            return Fernet(key)

        except Exception as e:
            self.logger.error(f"Failed to initialize encryption: {e}")
            raise CredentialSecurityError(f"Encryption initialization failed: {e}")

    def _encrypt_value(self, value: str) -> str:
        """Encrypt a credential value"""
        try:
            encrypted_data = self.cipher_suite.encrypt(value.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            self.logger.error(f"Failed to encrypt credential: {e}")
            raise CredentialSecurityError(f"Encryption failed: {e}")

    def _decrypt_value(self, encrypted_value: str) -> str:
        """Decrypt a credential value"""
        try:
            encrypted_data = base64.urlsafe_b64decode(encrypted_value.encode())
            decrypted_data = self.cipher_suite.decrypt(encrypted_data)
            return decrypted_data.decode()
        except Exception as e:
            self.logger.error(f"Failed to decrypt credential: {e}")
            raise CredentialSecurityError(f"Decryption failed: {e}")

    def store_credential(self, name: str, value: str,
                        rotate_immediately: bool = False,
                        require_rotation_days: int = 90) -> bool:
        """
        Store a credential securely

        Args:
            name: Credential name/identifier
            value: Credential value
            rotate_immediately: Whether to mark for immediate rotation
            require_rotation_days: Days before rotation is required
        """
        try:
            # Validate credential name
            if not self._validate_credential_name(name):
                raise CredentialSecurityError(f"Invalid credential name: {name}")

            # Encrypt the value
            encrypted_value = self._encrypt_value(value)

            # Create credential info
            from datetime import datetime, timedelta
            credential = CredentialInfo(
                name=name,
                encrypted_value=encrypted_value,
                is_encrypted=True,
                last_rotated=datetime.now().isoformat(),
                rotation_required=rotate_immediately,
                access_log=[{
                    'action': 'created',
                    'timestamp': datetime.now().isoformat(),
                    'ip': 'localhost'
                }]
            )

            # Store in memory
            self.credential_store[name] = credential

            # Save to encrypted file
            self._save_credentials()

            self.logger.info(f"Credential '{name}' stored securely")
            return True

        except Exception as e:
            self.logger.error(f"Failed to store credential '{name}': {e}")
            return False

    def get_credential(self, name: str, access_reason: str = "System access") -> Optional[str]:
        """
        Retrieve a credential securely

        Args:
            name: Credential name/identifier
            access_reason: Reason for accessing the credential
        """
        try:
            if name not in self.credential_store:
                self.logger.warning(f"Credential '{name}' not found")
                return None

            credential = self.credential_store[name]

            # Check if rotation is required
            if credential.rotation_required:
                self.logger.warning(f"Credential '{name}' requires rotation")

            # Decrypt the value
            value = self._decrypt_value(credential.encrypted_value)

            # Log access
            from datetime import datetime
            credential.access_log.append({
                'action': 'accessed',
                'timestamp': datetime.now().isoformat(),
                'reason': access_reason,
                'ip': 'localhost'
            })

            self.logger.debug(f"Credential '{name}' accessed for: {access_reason}")
            return value

        except Exception as e:
            self.logger.error(f"Failed to retrieve credential '{name}': {e}")
            return None

    def rotate_credential(self, name: str, new_value: str) -> bool:
        """
        Rotate a credential with a new value

        Args:
            name: Credential name/identifier
            new_value: New credential value
        """
        try:
            if name not in self.credential_store:
                self.logger.error(f"Cannot rotate non-existent credential: {name}")
                return False

            # Generate new encrypted value
            new_encrypted = self._encrypt_value(new_value)

            # Update credential
            credential = self.credential_store[name]
            credential.encrypted_value = new_encrypted
            credential.rotation_required = False

            from datetime import datetime
            credential.last_rotated = datetime.now().isoformat()
            credential.access_log.append({
                'action': 'rotated',
                'timestamp': datetime.now().isoformat(),
                'ip': 'localhost'
            })

            # Save updated credentials
            self._save_credentials()

            self.logger.info(f"Credential '{name}' rotated successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to rotate credential '{name}': {e}")
            return False

    def delete_credential(self, name: str) -> bool:
        """Delete a credential securely"""
        try:
            if name not in self.credential_store:
                self.logger.warning(f"Credential '{name}' not found for deletion")
                return False

            del self.credential_store[name]
            self._save_credentials()

            self.logger.info(f"Credential '{name}' deleted securely")
            return True

        except Exception as e:
            self.logger.error(f"Failed to delete credential '{name}': {e}")
            return False

    def list_credentials(self) -> Dict[str, Dict[str, Any]]:
        """List all stored credentials (without values)"""
        return {
            name: {
                'last_rotated': cred.last_rotated,
                'rotation_required': cred.rotation_required,
                'access_count': len(cred.access_log)
            }
            for name, cred in self.credential_store.items()
        }

    def _validate_credential_name(self, name: str) -> bool:
        """Validate credential name for security"""
        import re

        # Allow only alphanumeric characters, underscores, and hyphens
        if not re.match(r'^[a-zA-Z0-9_-]+$', name):
            return False

        # Prevent reserved names
        reserved_names = ['password', 'secret', 'key', 'token', 'admin', 'root']
        if name.lower() in reserved_names:
            return False

        # Minimum length
        if len(name) < 3:
            return False

        return True

    def _load_credentials(self) -> None:
        """Load credentials from encrypted storage"""
        try:
            if self.encrypted_file.exists():
                with open(self.encrypted_file, 'rb') as f:
                    encrypted_data = f.read()

                # Decrypt and parse
                decrypted_data = self.cipher_suite.decrypt(encrypted_data)
                credential_data = json.loads(decrypted_data.decode())

                # Reconstruct credential objects
                for name, data in credential_data.items():
                    credential = CredentialInfo(
                        name=name,
                        encrypted_value=data.get('encrypted_value'),
                        is_encrypted=data.get('is_encrypted', True),
                        last_rotated=data.get('last_rotated'),
                        rotation_required=data.get('rotation_required', False),
                        access_log=data.get('access_log', [])
                    )
                    self.credential_store[name] = credential

                self.logger.info(f"Loaded {len(self.credential_store)} encrypted credentials")

        except Exception as e:
            self.logger.warning(f"Could not load existing credentials: {e}")

    def _save_credentials(self) -> None:
        """Save credentials to encrypted storage"""
        try:
            # Prepare data for storage
            credential_data = {}
            for name, cred in self.credential_store.items():
                credential_data[name] = {
                    'encrypted_value': cred.encrypted_value,
                    'is_encrypted': cred.is_encrypted,
                    'last_rotated': cred.last_rotated,
                    'rotation_required': cred.rotation_required,
                    'access_log': cred.access_log[-10:]  # Keep only last 10 accesses
                }

            # Encrypt and save
            json_data = json.dumps(credential_data, indent=2)
            encrypted_data = self.cipher_suite.encrypt(json_data.encode())

            # Ensure config directory exists
            self.encrypted_file.parent.mkdir(parents=True, exist_ok=True)

            # Save encrypted data
            with open(self.encrypted_file, 'wb') as f:
                f.write(encrypted_data)

            # Set secure permissions
            os.chmod(self.encrypted_file, 0o600)

        except Exception as e:
            self.logger.error(f"Failed to save credentials: {e}")
            raise CredentialSecurityError(f"Failed to save credentials: {e}")

    def generate_secure_token(self, length: int = 32) -> str:
        """Generate a secure random token"""
        return secrets.token_urlsafe(length)

    def check_credential_rotation(self) -> Dict[str, bool]:
        """Check which credentials need rotation"""
        from datetime import datetime, timedelta
        rotation_status = {}

        for name, cred in self.credential_store.items():
            if cred.rotation_required:
                rotation_status[name] = True
                continue

            if cred.last_rotated:
                last_rotation = datetime.fromisoformat(cred.last_rotated)
                days_since_rotation = (datetime.now() - last_rotation).days
                rotation_status[name] = days_since_rotation >= 90  # 90 days rotation
            else:
                rotation_status[name] = True

        return rotation_status

# Global credential manager instance
_credential_manager: Optional[SecureCredentialManager] = None

def get_credential_manager() -> SecureCredentialManager:
    """Get global credential manager instance"""
    global _credential_manager
    if _credential_manager is None:
        _credential_manager = SecureCredentialManager()
    return _credential_manager

# Convenience functions for common operations
def store_telegram_token(token: str) -> bool:
    """Store Telegram bot token securely"""
    manager = get_credential_manager()
    return manager.store_credential("telegram_bot_token", token)

def get_telegram_token() -> Optional[str]:
    """Get Telegram bot token securely"""
    manager = get_credential_manager()
    return manager.get_credential("telegram_bot_token", "Telegram bot authentication")

def store_api_key(api_name: str, api_key: str) -> bool:
    """Store API key securely"""
    manager = get_credential_manager()
    return manager.store_credential(f"{api_name}_api_key", api_key)

def get_api_key(api_name: str) -> Optional[str]:
    """Get API key securely"""
    manager = get_credential_manager()
    return manager.get_credential(f"{api_name}_api_key", f"{api_name} API access")

# Migration utility to move from .env to secure storage
def migrate_from_env() -> bool:
    """Migrate credentials from .env file to secure storage"""
    try:
        env_file = Path(".env")
        if not env_file.exists():
            logger.info("No .env file found for migration")
            return True

        logger.info("Starting credential migration from .env to secure storage...")

        # Read .env file
        with open(env_file, 'r', encoding='utf-8') as f:
            env_content = f.read()

        # Parse and migrate sensitive values
        manager = get_credential_manager()
        migrated_count = 0

        lines = env_content.split('\n')
        for line in lines:
            line = line.strip()
            if '=' in line and not line.startswith('#'):
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()

                # Migrate sensitive credentials
                if 'TELEGRAM_BOT_TOKEN' in key:
                    if manager.store_credential("telegram_bot_token", value):
                        migrated_count += 1
                        logger.info(f"Migrated {key} to secure storage")

                elif 'API_KEY' in key or 'SECRET' in key or 'PASSWORD' in key:
                    cred_name = key.lower().replace(' ', '_')
                    if manager.store_credential(cred_name, value):
                        migrated_count += 1
                        logger.info(f"Migrated {key} to secure storage")

        if migrated_count > 0:
            logger.info(f"Successfully migrated {migrated_count} credentials")
            return True
        else:
            logger.info("No credentials required migration")
            return True

    except Exception as e:
        logger.error(f"Failed to migrate credentials: {e}")
        return False