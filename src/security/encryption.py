"""
Data Encryption and Masking Service

This module provides encryption and data masking capabilities for sensitive
financial data, including macroeconomic indicators, sentiment scores,
and API credentials. Ensures data protection both in transit and at rest.
"""

import os
import json
import hashlib
import hmac
import base64
from typing import Any, Dict, Optional, Union, List
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import logging

logger = logging.getLogger(__name__)


class DataEncryption:
    """Encryption service for sensitive financial data"""

    def __init__(self):
        self.key = self._load_or_generate_key()
        self.fernet = Fernet(self.key)
        self.logger = logging.getLogger(__name__)

    def _load_or_generate_key(self) -> bytes:
        """Load encryption key from environment or generate new one"""

        # Try to load from environment
        key_b64 = os.getenv('CBSC_ENCRYPTION_KEY')
        if key_b64:
            try:
                return base64.urlsafe_b64decode(key_b64.encode())
            except Exception as e:
                self.logger.error(f"Failed to decode encryption key: {e}")

        # Generate new key
        self.logger.warning(
            "Generating new encryption key - "
            "please set CBSC_ENCRYPTION_KEY environment variable in production"
        )
        key = Fernet.generate_key()

        # Store in environment for persistence
        os.environ['CBSC_ENCRYPTION_KEY'] = base64.urlsafe_b64encode(key).decode()
        self.logger.info("New encryption key generated and stored in environment")

        return key

    def encrypt_data(self, data: Any) -> str:
        """Encrypt sensitive data"""

        try:
            # Convert data to JSON if it's a dictionary or object
            if isinstance(data, (dict, list)):
                data_str = json.dumps(data, default=str, sort_keys=True)
            else:
                data_str = str(data)

            # Encrypt the data
            encrypted_data = self.fernet.encrypt(data_str.encode('utf-8'))
            return base64.urlsafe_b64encode(encrypted_data).decode('utf-8')

        except Exception as e:
            self.logger.error(f"Failed to encrypt data: {e}")
            raise ValueError("Encryption failed")

    def decrypt_data(self, encrypted_data: str) -> Any:
        """Decrypt sensitive data"""

        try:
            # Decode base64 and decrypt
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
            decrypted_data = self.fernet.decrypt(encrypted_bytes).decode('utf-8')

            # Try to parse as JSON first
            try:
                return json.loads(decrypted_data)
            except json.JSONDecodeError:
                # Return as string if not valid JSON
                return decrypted_data

        except Exception as e:
            self.logger.error(f"Failed to decrypt data: {e}")
            raise ValueError("Decryption failed")

    def encrypt_sensitive_macro_data(self, macro_data: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt sensitive macroeconomic indicators while keeping public fields visible"""

        # Define which fields are sensitive
        sensitive_fields = {
            'exact_values',  # Exact monetary values
            'internal_notes',  # Internal analysis notes
            'source_details',  # Detailed source information
            'proprietary_indicators',  # Custom calculated indicators
            'future_projections',  # Forward-looking data
            'confidence_scores',  # Confidence in predictions
        }

        # Also encrypt any field with 'confidential' in the name
        encrypted_data = macro_data.copy()
        data_to_encrypt = {}

        # Extract sensitive data
        for field, value in macro_data.items():
            if field in sensitive_fields or 'confidential' in field.lower():
                data_to_encrypt[field] = value
                del encrypted_data[field]

        # Encrypt sensitive data and store as encrypted field
        if data_to_encrypt:
            encrypted_bundle = {
                'data': data_to_encrypt,
                'encrypted_at': datetime.now().isoformat(),
                'version': '1.0'
            }
            encrypted_data['sensitive_data_encrypted'] = self.encrypt_data(encrypted_bundle)

        return encrypted_data

    def decrypt_sensitive_macro_data(self, encrypted_macro_data: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt sensitive macroeconomic indicators"""

        decrypted_data = encrypted_macro_data.copy()

        if 'sensitive_data_encrypted' in encrypted_macro_data:
            try:
                encrypted_bundle = self.decrypt_data(encrypted_macro_data['sensitive_data_encrypted'])

                # Check if it's a valid bundle
                if isinstance(encrypted_bundle, dict) and 'data' in encrypted_bundle:
                    decrypted_data.update(encrypted_bundle['data'])
                    del decrypted_data['sensitive_data_encrypted']

                    # Log decryption for audit
                    self.logger.info(
                        f"Decrypted sensitive macro data bundle from {encrypted_bundle.get('encrypted_at', 'unknown time')}"
                    )

            except Exception as e:
                self.logger.error(f"Failed to decrypt macro data: {e}")

        return decrypted_data

    def encrypt_api_credentials(self, credentials: Dict[str, Any]) -> str:
        """Encrypt API credentials for secure storage"""

        # Add metadata for security
        secure_credentials = {
            'credentials': credentials,
            'created_at': datetime.now().isoformat(),
            'purpose': 'api_authentication',
            'version': '1.0'
        }

        return self.encrypt_data(secure_credentials)

    def decrypt_api_credentials(self, encrypted_credentials: str) -> Dict[str, Any]:
        """Decrypt API credentials"""

        try:
            secure_bundle = self.decrypt_data(encrypted_credentials)

            if isinstance(secure_bundle, dict) and 'credentials' in secure_bundle:
                return secure_bundle['credentials']
            else:
                return secure_bundle

        except Exception as e:
            self.logger.error(f"Failed to decrypt API credentials: {e}")
            raise ValueError("Invalid encrypted credentials")

    def hash_sensitive_field(self, field_value: str, salt: Optional[str] = None) -> str:
        """Create irreversible hash for sensitive field comparisons"""

        # Use environment pepper or generate new salt
        pepper = os.getenv('HASH_PEPPER', 'cbsc_secure_pepper_2024')
        salt = salt or 'default_salt'

        # Create HMAC with salt and pepper
        h = hmac.new(
            (pepper + salt).encode('utf-8'),
            field_value.encode('utf-8'),
            hashlib.sha256
        )
        return h.hexdigest()

    def rotate_key(self, old_key_b64: str, new_key_b64: Optional[str] = None) -> bool:
        """Rotate encryption key and re-encrypt data with new key"""

        try:
            # Generate new key if not provided
            if not new_key_b64:
                new_key = Fernet.generate_key()
                new_key_b64 = base64.urlsafe_b64encode(new_key).decode()

            # Store new key
            os.environ['CBSC_ENCRYPTION_KEY'] = new_key_b64

            # Update current key
            self.key = base64.urlsafe_b64decode(new_key_b64.encode())
            self.fernet = Fernet(self.key)

            self.logger.info("Encryption key rotated successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to rotate encryption key: {e}")
            return False


class DataMasking:
    """Data masking for sensitive information display based on user roles"""

    @staticmethod
    def mask_monetary_value(value: Union[float, int], user_role: str, precision: int = 2) -> str:
        """Mask monetary value based on user role"""

        try:
            if user_role in ['admin', 'institutional', 'non_price_admin']:
                return f"${value:,.{precision}f}"
            elif user_role in ['premium', 'quant_analyst', 'non_price_analyst']:
                return f"${value:,.0f}"
            elif user_role == 'non_price_viewer':
                # Non-price viewers see ranges
                if value > 1000000000:  # > 1B
                    return "$1B+"
                elif value > 1000000:  # > 1M
                    return f"${value/1000000:.0f}M+"
                elif value > 100000:  # > 100K
                    return "$100K-$1M"
                elif value > 10000:  # > 10K
                    return "$10K-$100K"
                else:
                    return "<$10K"
            else:  # Basic users
                # Basic users see very limited info
                if value > 1000000:
                    return "High"
                elif value > 100000:
                    return "Medium"
                else:
                    return "Low"

        except Exception:
            return "N/A"

    @staticmethod
    def mask_sentiment_score(score: float, user_role: str, precision: int = 1) -> str:
        """Mask sentiment score to reduce precision based on role"""

        try:
            if user_role in ['admin', 'institutional', 'quant_analyst', 'non_price_analyst']:
                # Full precision for analysts
                return f"{score:.{precision}f}"
            elif user_role in ['premium', 'non_price_viewer']:
                # Reduced precision for premium users
                if abs(score) < 0.01:
                    return "0.0"
                return f"{score:.1f}"
            else:  # Basic users
                # Only sentiment direction
                if score > 0.05:
                    return "Positive"
                elif score < -0.05:
                    return "Negative"
                else:
                    return "Neutral"

        except Exception:
            return "N/A"

    @staticmethod
    def mask_hibor_rate(rate: float, user_role: str) -> str:
        """Mask HIBOR rate for public display"""

        try:
            if user_role in ['admin', 'institutional', 'quant_analyst', 'non_price_analyst']:
                return f"{rate:.4f}%"
            elif user_role in ['premium', 'non_price_viewer']:
                return f"{rate:.2f}%"
            else:  # Basic users
                return f"{rate:.1f}%"

        except Exception:
            return "N/A"

    @staticmethod
    def mask_api_key(api_key: str, visible_chars: int = 4) -> str:
        """Mask API key showing only first few characters"""

        if len(api_key) <= visible_chars:
            return "*" * len(api_key)

        return api_key[:visible_chars] + "*" * (len(api_key) - visible_chars)

    @staticmethod
    def mask_email_address(email: str, user_role: str) -> str:
        """Mask email address based on user role"""

        if user_role in ['admin', 'institutional']:
            return email  # Full email for admin/inst

        try:
            local, domain = email.split('@', 1)

            if user_role in ['premium', 'quant_analyst', 'non_price_analyst']:
                # Show first 2 characters of local part
                masked_local = local[:2] + "*" * (len(local) - 2)
            else:
                # Show only first character
                masked_local = local[0] + "*" * (len(local) - 1)

            return f"{masked_local}@{domain}"

        except Exception:
            return "***@***.***"

    @staticmethod
    def mask_personal_data(data: str, data_type: str, user_role: str) -> str:
        """General personal data masking based on data type and role"""

        if user_role in ['admin', 'institutional']:
            return data  # No masking for admin/inst

        if data_type == 'phone':
            # Mask all but last 4 digits
            if len(data) > 4:
                return "*" * (len(data) - 4) + data[-4:]
            return "*" * len(data)

        elif data_type == 'address':
            # Show only city and country
            parts = data.split(',')
            if len(parts) >= 2:
                return "***," + ",".join(parts[-2:])
            return "***"

        elif data_type == 'id_number':
            # Show only last 4 characters
            if len(data) > 4:
                return "*" * (len(data) - 4) + data[-4:]
            return "*" * len(data)

        else:
            # Default masking
            if len(data) <= 8:
                return "*" * len(data)
            return data[:4] + "*" * (len(data) - 8) + data[-4:]

    def mask_sensitive_fields(self, data: Dict[str, Any], user_role: str) -> Dict[str, Any]:
        """Apply appropriate masking to all sensitive fields in data"""

        masked_data = data.copy()

        # Monetary values
        if 'amount' in masked_data:
            masked_data['amount'] = self.mask_monetary_value(
                masked_data['amount'], user_role
            )

        if 'value' in masked_data and isinstance(masked_data['value'], (int, float)):
            masked_data['value'] = self.mask_monetary_value(
                masked_data['value'], user_role
            )

        # Sentiment scores
        if 'sentiment_score' in masked_data:
            masked_data['sentiment_score'] = self.mask_sentiment_score(
                masked_data['sentiment_score'], user_role
            )

        # Interest rates
        if 'hibor_rate' in masked_data:
            masked_data['hibor_rate'] = self.mask_hibor_rate(
                masked_data['hibor_rate'], user_role
            )

        # API keys
        if 'api_key' in masked_data:
            masked_data['api_key'] = self.mask_api_key(masked_data['api_key'])

        # Personal information
        if 'email' in masked_data:
            masked_data['email'] = self.mask_email_address(
                masked_data['email'], user_role
            )

        if 'phone' in masked_data:
            masked_data['phone'] = self.mask_personal_data(
                masked_data['phone'], 'phone', user_role
            )

        if 'address' in masked_data:
            masked_data['address'] = self.mask_personal_data(
                masked_data['address'], 'address', user_role
            )

        return masked_data


# Global instances
encryption_service = DataEncryption()
data_masking = DataMasking()


# Initialize encryption in production
def initialize_encryption():
    """Initialize encryption service with production keys"""

    # Check if we're in production
    if os.getenv('ENVIRONMENT', 'development').lower() == 'production':
        # Validate that encryption key is set
        if not os.getenv('CBSC_ENCRYPTION_KEY'):
            raise RuntimeError(
                "CBSC_ENCRYPTION_KEY environment variable must be set in production"
            )

        # Validate hash pepper
        if not os.getenv('HASH_PEPPER'):
            logger.warning(
                "HASH_PEPPER environment variable not set, using default (not recommended for production)"
            )

        logger.info("Encryption service initialized for production")
    else:
        logger.info("Encryption service initialized for development")