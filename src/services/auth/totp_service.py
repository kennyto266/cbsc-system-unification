"""
TOTP (Time-based One-Time Password) service for Google Authenticator integration

This module handles:
- TOTP secret generation
- QR code generation for enrollment
- TOTP token validation
- Backup codes generation and validation
"""

import os
import secrets
import pyotp
import qrcode
import qrcode.constants
import io
import base64
import json
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List, Tuple
from cryptography.fernet import Fernet
import logging

# Database
from sqlalchemy.orm import Session
from src.core.database import get_db

# Models
from src.models.user import User

# Configuration
from src.core.config import settings

logger = logging.getLogger(__name__)


class TOTPService:
    """TOTP service for Google Authenticator integration"""

    def __init__(self):
        # Encryption key for TOTP secrets
        self.encryption_key = os.getenv("TOTP_ENCRYPTION_KEY", Fernet.generate_key()).encode()
        self.cipher_suite = Fernet(self.encryption_key)

        # TOTP configuration
        self.issuer_name = "CBSC量化交易系統"
        self.totp_digits = 6
        self.totp_period = 30  # seconds
        self.backup_codes_count = 10

        # QR code configuration
        self.qr_box_size = 10
        self.qr_border = 4
        self.qr_error_correction = qrcode.constants.ERROR_CORRECT_M

    def _get_db(self) -> Session:
        """Get database session"""
        return next(get_db())

    def _encrypt_secret(self, secret: str) -> str:
        """Encrypt TOTP secret"""
        encrypted_data = self.cipher_suite.encrypt(secret.encode())
        return base64.b64encode(encrypted_data).decode()

    def _decrypt_secret(self, encrypted_secret: str) -> str:
        """Decrypt TOTP secret"""
        encrypted_data = base64.b64decode(encrypted_secret.encode())
        decrypted_data = self.cipher_suite.decrypt(encrypted_data)
        return decrypted_data.decode()

    def _generate_backup_codes(self, count: int = None) -> List[str]:
        """Generate backup codes"""
        if count is None:
            count = self.backup_codes_count

        codes = []
        for _ in range(count):
            # Generate 8-digit backup code
            code = ''.join([str(secrets.randbelow(10)) for _ in range(8)])
            codes.append(code)

        return codes

    def _generate_qr_code(self, uri: str) -> str:
        """Generate QR code from TOTP URI and return as base64 image"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=self.qr_error_correction,
            box_size=self.qr_box_size,
            border=self.qr_border,
        )
        qr.add_data(uri)
        qr.make(fit=True)

        # Create QR code image
        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.getvalue()).decode()

        return f"data:image/png;base64,{img_base64}"

    def generate_totp_secret(self, user_id: str) -> Dict[str, Any]:
        """Generate new TOTP secret for user"""
        db = self._get_db()
        try:
            # Get user
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"success": False, "error": "用戶不存在"}

            # Generate secret
            secret = pyotp.random_base32()

            # Create TOTP URI for QR code
            totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
                name=user.email,
                issuer_name=self.issuer_name
            )

            # Generate QR code
            qr_code = self._generate_qr_code(totp_uri)

            # Generate backup codes
            backup_codes = self._generate_backup_codes()

            # Encrypt secret for storage
            encrypted_secret = self._encrypt_secret(secret)
            encrypted_backup_codes = self._encrypt_secret(json.dumps(backup_codes))

            # Store temporarily (not enabled yet)
            user.totp_secret_temp = encrypted_secret
            user.totp_backup_codes_temp = encrypted_backup_codes
            db.commit()

            return {
                "success": True,
                "data": {
                    "secret": secret,
                    "qr_code": qr_code,
                    "backup_codes": backup_codes,
                    "manual_entry_key": secret,
                    "issuer": self.issuer_name,
                    "account_name": user.email,
                    "instructions": [
                        "1. 使用 Google Authenticator 應用掃描上方二維碼",
                        "2. 或手動輸入下方的帳戶名稱和金鑰",
                        "3. 請安全保存備用代碼，每個代碼只能使用一次",
                        "4. 啟用後，您需要輸入驗證碼才能登錄"
                    ]
                }
            }

        except Exception as e:
            logger.error(f"Error generating TOTP secret: {str(e)}")
            db.rollback()
            return {"success": False, "error": str(e)}
        finally:
            db.close()

    def verify_totp_setup(self, user_id: str, token: str) -> Dict[str, Any]:
        """Verify TOTP setup and enable MFA for user"""
        db = self._get_db()
        try:
            # Get user
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"success": False, "error": "用戶不存在"}

            # Check if user has temporary TOTP secret
            if not user.totp_secret_temp:
                return {"success": False, "error": "未找到待驗證的 TOTP 設置"}

            # Decrypt secret
            secret = self._decrypt_secret(user.totp_secret_temp)

            # Verify token
            totp = pyotp.TOTP(secret)
            if not totp.verify(token, valid_window=1):
                return {"success": False, "error": "驗證碼錯誤"}

            # Enable TOTP
            user.mfa_secret = user.totp_secret_temp
            user.mfa_backup_codes = user.totp_backup_codes_temp
            user.mfa_enabled = True
            user.mfa_type = "totp"

            # Clear temporary data
            user.totp_secret_temp = None
            user.totp_backup_codes_temp = None

            db.commit()

            return {
                "success": True,
                "message": "TOTP 驗證成功，MFA 已啟用",
                "mfa_enabled": True
            }

        except Exception as e:
            logger.error(f"Error verifying TOTP setup: {str(e)}")
            db.rollback()
            return {"success": False, "error": str(e)}
        finally:
            db.close()

    def verify_totp_token(self, user_id: str, token: str) -> Dict[str, Any]:
        """Verify TOTP token for authentication"""
        db = self._get_db()
        try:
            # Get user
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"success": False, "error": "用戶不存在"}

            # Check if TOTP is enabled
            if not user.mfa_enabled or user.mfa_type != "totp":
                return {"success": False, "error": "TOTP 未啟用"}

            # Decrypt secret
            if not user.mfa_secret:
                return {"success": False, "error": "未找到 TOTP 密鑰"}

            secret = self._decrypt_secret(user.mfa_secret)

            # Verify token
            totp = pyotp.TOTP(secret)
            if not totp.verify(token, valid_window=1):
                return {"success": False, "error": "驗證碼錯誤"}

            return {
                "success": True,
                "message": "TOTP 驗證成功",
                "verified": True
            }

        except Exception as e:
            logger.error(f"Error verifying TOTP token: {str(e)}")
            return {"success": False, "error": str(e)}
        finally:
            db.close()

    def verify_backup_code(self, user_id: str, backup_code: str) -> Dict[str, Any]:
        """Verify backup code and remove it after use"""
        db = self._get_db()
        try:
            # Get user
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"success": False, "error": "用戶不存在"}

            # Check if MFA is enabled
            if not user.mfa_enabled:
                return {"success": False, "error": "MFA 未啟用"}

            # Get backup codes
            if not user.mfa_backup_codes:
                return {"success": False, "error": "未找到備用代碼"}

            backup_codes = json.loads(self._decrypt_secret(user.mfa_backup_codes))

            # Check if backup code is valid
            if backup_code not in backup_codes:
                return {"success": False, "error": "備用代碼錯誤"}

            # Remove used backup code
            backup_codes.remove(backup_code)

            # Update backup codes
            if backup_codes:
                user.mfa_backup_codes = self._encrypt_secret(json.dumps(backup_codes))
            else:
                user.mfa_backup_codes = None
                # Suggest regenerating backup codes
                user.backup_code_regeneration_required = True

            db.commit()

            return {
                "success": True,
                "message": "備用代碼驗證成功",
                "verified": True,
                "remaining_codes": len(backup_codes)
            }

        except Exception as e:
            logger.error(f"Error verifying backup code: {str(e)}")
            db.rollback()
            return {"success": False, "error": str(e)}
        finally:
            db.close()

    def disable_totp(self, user_id: str, token: str = None, backup_code: str = None) -> Dict[str, Any]:
        """Disable TOTP for user (requires verification)"""
        db = self._get_db()
        try:
            # Get user
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"success": False, "error": "用戶不存在"}

            # Verify token or backup code
            if token:
                # Verify TOTP token
                result = self.verify_totp_token(user_id, token)
                if not result["success"]:
                    return {"success": False, "error": "TOTP 驗證失敗"}
            elif backup_code:
                # Verify backup code
                result = self.verify_backup_code(user_id, backup_code)
                if not result["success"]:
                    return {"success": False, "error": "備用代碼驗證失敗"}
            else:
                return {"success": False, "error": "需要提供驗證碼或備用代碼"}

            # Disable TOTP
            user.mfa_enabled = False
            user.mfa_type = None
            user.mfa_secret = None
            user.mfa_backup_codes = None
            user.totp_secret_temp = None
            user.totp_backup_codes_temp = None
            user.backup_code_regeneration_required = False

            db.commit()

            return {
                "success": True,
                "message": "TOTP 已禁用",
                "mfa_disabled": True
            }

        except Exception as e:
            logger.error(f"Error disabling TOTP: {str(e)}")
            db.rollback()
            return {"success": False, "error": str(e)}
        finally:
            db.close()

    def regenerate_backup_codes(self, user_id: str, token: str = None) -> Dict[str, Any]:
        """Regenerate backup codes for user"""
        db = self._get_db()
        try:
            # Get user
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"success": False, "error": "用戶不存在"}

            # Check if TOTP is enabled
            if not user.mfa_enabled or user.mfa_type != "totp":
                return {"success": False, "error": "TOTP 未啟用"}

            # If token is provided, verify it
            if token:
                result = self.verify_totp_token(user_id, token)
                if not result["success"]:
                    return {"success": False, "error": "TOTP 驗證失敗"}

            # Generate new backup codes
            backup_codes = self._generate_backup_codes()

            # Encrypt and store
            user.mfa_backup_codes = self._encrypt_secret(json.dumps(backup_codes))
            user.backup_code_regeneration_required = False

            db.commit()

            return {
                "success": True,
                "message": "備用代碼已重新生成",
                "backup_codes": backup_codes,
                "warning": "請安全保存新的備用代碼"
            }

        except Exception as e:
            logger.error(f"Error regenerating backup codes: {str(e)}")
            db.rollback()
            return {"success": False, "error": str(e)}
        finally:
            db.close()

    def get_totp_status(self, user_id: str) -> Dict[str, Any]:
        """Get TOTP status for user"""
        db = self._get_db()
        try:
            # Get user
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"success": False, "error": "用戶不存在"}

            status = {
                "mfa_enabled": user.mfa_enabled,
                "mfa_type": user.mfa_type,
                "has_backup_codes": bool(user.mfa_backup_codes),
                "backup_code_regeneration_required": user.backup_code_regeneration_required or False,
                "has_pending_setup": bool(user.totp_secret_temp)
            }

            if user.mfa_backup_codes:
                try:
                    backup_codes = json.loads(self._decrypt_secret(user.mfa_backup_codes))
                    status["remaining_backup_codes"] = len(backup_codes)
                except:
                    status["remaining_backup_codes"] = 0

            return {
                "success": True,
                "data": status
            }

        except Exception as e:
            logger.error(f"Error getting TOTP status: {str(e)}")
            return {"success": False, "error": str(e)}
        finally:
            db.close()


# Create singleton instance
totp_service = TOTPService()