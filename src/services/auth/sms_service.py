"""
SMS verification service for multi-factor authentication

This module handles:
- SMS OTP generation and validation
- Integration with SMS providers (Twilio, Nexmo, etc.)
- Phone number verification
- Rate limiting for SMS
"""

import os
import secrets
import json
import requests
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
import phonenumbers
from phonenumbers import NumberParseException, PhoneNumberFormat
import logging
import redis

# Database
from sqlalchemy.orm import Session
from src.core.database import get_db

# Models
from src.models.user import User

# Configuration
from src.core.config import settings

logger = logging.getLogger(__name__)


class SMSService:
    """SMS service for OTP verification"""

    def __init__(self):
        # SMS Provider Configuration
        self.sms_provider = os.getenv("SMS_PROVIDER", "twilio").lower()

        # Twilio Configuration
        self.twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.twilio_phone_number = os.getenv("TWILIO_PHONE_NUMBER")

        # Nexmo/Vonage Configuration
        self.nexmo_api_key = os.getenv("NEXMO_API_KEY")
        self.nexmo_api_secret = os.getenv("NEXMO_API_SECRET")
        self.nexmo_from_number = os.getenv("NEXMO_FROM_NUMBER")

        # Aliyun Configuration
        self.aliyun_access_key = os.getenv("ALIYUN_ACCESS_KEY")
        self.aliyun_access_secret = os.getenv("ALIYUN_ACCESS_SECRET")
        self.aliyun_sign_name = os.getenv("ALIYUN_SIGN_NAME")
        self.aliyun_template_code = os.getenv("ALIYUN_SMS_TEMPLATE_CODE")

        # SMS Configuration
        self.otp_length = 6
        self.otp_expire_minutes = 5
        self.max_attempts = 5
        self.sms_rate_limit_per_hour = 10

        # Redis for rate limiting and OTP storage
        self.redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=int(os.getenv("REDIS_DB", 0)),
            decode_responses=True
        )

    def _get_db(self) -> Session:
        """Get database session"""
        return next(get_db())

    def _validate_phone_number(self, phone: str, country_code: str = "TW") -> Dict[str, Any]:
        """Validate and format phone number"""
        try:
            # Parse phone number
            parsed_phone = phonenumbers.parse(phone, country_code)

            # Check if valid
            if not phonenumbers.is_valid_number(parsed_phone):
                return {"valid": False, "error": "無效的電話號碼"}

            # Format to E.164
            formatted_phone = phonenumbers.format_number(
                parsed_phone,
                PhoneNumberFormat.E164
            )

            # Get international format for display
            international_format = phonenumbers.format_number(
                parsed_phone,
                PhoneNumberFormat.INTERNATIONAL
            )

            return {
                "valid": True,
                "formatted": formatted_phone,
                "display": international_format,
                "country_code": phonenumbers.region_code_for_number(parsed_phone)
            }

        except NumberParseException as e:
            return {"valid": False, "error": f"電話號碼格式錯誤: {str(e)}"}
        except Exception as e:
            logger.error(f"Error validating phone number: {str(e)}")
            return {"valid": False, "error": "電話號碼驗證失敗"}

    def _generate_otp_code(self) -> str:
        """Generate OTP code"""
        return ''.join([str(secrets.randbelow(10)) for _ in range(self.otp_length)])

    def _get_rate_limit_key(self, user_id: str, action: str) -> str:
        """Get rate limit key for Redis"""
        return f"sms_rate_limit:{user_id}:{action}"

    def _get_otp_key(self, user_id: str, action: str) -> str:
        """Get OTP storage key for Redis"""
        return f"sms_otp:{user_id}:{action}"

    def _check_rate_limit(self, user_id: str, action: str) -> bool:
        """Check rate limit for SMS sending"""
        try:
            key = self._get_rate_limit_key(user_id, action)
            current_count = self.redis_client.get(key) or 0

            if int(current_count) >= self.sms_rate_limit_per_hour:
                return False

            # Increment counter
            self.redis_client.incr(key)
            self.redis_client.expire(key, 3600)  # 1 hour
            return True

        except Exception as e:
            logger.error(f"Error checking rate limit: {str(e)}")
            # Allow proceeding if Redis fails
            return True

    def _send_sms_twilio(self, to: str, message: str) -> Dict[str, Any]:
        """Send SMS using Twilio"""
        try:
            url = f"https://api.twilio.com/2010-04-01/Accounts/{self.twilio_account_sid}/Messages.json"

            data = {
                "To": to,
                "From": self.twilio_phone_number,
                "Body": message
            }

            response = requests.post(
                url,
                auth=(self.twilio_account_sid, self.twilio_auth_token),
                data=data,
                timeout=10
            )

            if response.status_code == 201:
                return {"success": True, "message_id": response.json().get("sid")}
            else:
                return {
                    "success": False,
                    "error": f"Twilio API error: {response.text}"
                }

        except Exception as e:
            logger.error(f"Error sending SMS via Twilio: {str(e)}")
            return {"success": False, "error": str(e)}

    def _send_sms_nexmo(self, to: str, message: str) -> Dict[str, Any]:
        """Send SMS using Nexmo/Vonage"""
        try:
            url = "https://rest.nexmo.com/sms/json"

            data = {
                "api_key": self.nexmo_api_key,
                "api_secret": self.nexmo_api_secret,
                "from": self.nexmo_from_number,
                "to": to,
                "text": message
            }

            response = requests.post(url, json=data, timeout=10)
            result = response.json()

            if result.get("messages"):
                status = result["messages"][0].get("status")
                if status == "0":
                    return {"success": True, "message_id": result["messages"][0].get("message-id")}
                else:
                    return {
                        "success": False,
                        "error": f"Nexmo error: {result['messages'][0].get('error-text')}"
                    }
            else:
                return {"success": False, "error": "No response from Nexmo"}

        except Exception as e:
            logger.error(f"Error sending SMS via Nexmo: {str(e)}")
            return {"success": False, "error": str(e)}

    def _send_sms_aliyun(self, to: str, otp_code: str) -> Dict[str, Any]:
        """Send SMS using Aliyun SMS Service"""
        try:
            # This is a simplified implementation
            # In production, use the official Aliyun SDK

            import hmac
            import hashlib
            import base64
            from urllib.parse import quote

            # Prepare parameters
            params = {
                "AccessKeyId": self.aliyun_access_key,
                "Action": "SendSms",
                "Format": "JSON",
                "Version": "2017-05-25",
                "SignatureMethod": "HMAC-SHA1",
                "Timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "SignatureVersion": "1.0",
                "SignatureNonce": secrets.token_urlsafe(32),
                "PhoneNumbers": to,
                "SignName": self.aliyun_sign_name,
                "TemplateCode": self.aliyun_template_code,
                "TemplateParam": json.dumps({"code": otp_code})
            }

            # Create signature
            sorted_params = sorted(params.items())
            canonicalized_resource = "/".join(sorted([f"{quote(k, safe='')}" for k, _ in sorted_params]))
            string_to_sign = f"POST&%2F&{quote(canonicalized_resource, safe='')}"

            signature = base64.b64encode(
                hmac.new(
                    f"{self.aliyun_access_secret}&".encode(),
                    string_to_sign.encode(),
                    hashlib.sha1
                ).digest()
            ).decode()

            params["Signature"] = signature

            # Send request
            url = "https://dysmsapi.aliyuncs.com/"
            response = requests.post(url, data=params, timeout=10)
            result = response.json()

            if result.get("Code") == "OK":
                return {"success": True, "message_id": result.get("BizId")}
            else:
                return {
                    "success": False,
                    "error": f"Aliyun SMS error: {result.get('Message', 'Unknown error')}"
                }

        except Exception as e:
            logger.error(f"Error sending SMS via Aliyun: {str(e)}")
            return {"success": False, "error": str(e)}

    def _send_sms(self, to: str, message: str) -> Dict[str, Any]:
        """Send SMS using configured provider"""
        if self.sms_provider == "twilio":
            return self._send_sms_twilio(to, message)
        elif self.sms_provider == "nexmo":
            return self._send_sms_nexmo(to, message)
        elif self.sms_provider == "aliyun":
            # For Aliyun, we need OTP code separately
            return {"success": False, "error": "Use send_otp_aliyun for Aliyun provider"}
        else:
            return {"success": False, "error": f"Unsupported SMS provider: {self.sms_provider}"}

    def send_otp(self, user_id: str, action: str = "login") -> Dict[str, Any]:
        """Send OTP code via SMS"""
        db = self._get_db()
        try:
            # Get user
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"success": False, "error": "用戶不存在"}

            # Check phone number
            if not user.phone:
                return {"success": False, "error": "用戶未設置手機號碼"}

            # Validate phone number
            phone_validation = self._validate_phone_number(user.phone)
            if not phone_validation["valid"]:
                return {"success": False, "error": f"手機號碼無效: {phone_validation['error']}"}

            # Check rate limit
            if not self._check_rate_limit(user_id, action):
                return {"success": False, "error": "短信發送次數過多，請稍後再試"}

            # Generate OTP
            otp_code = self._generate_otp_code()
            expires_at = datetime.now(timezone.utc) + timedelta(minutes=self.otp_expire_minutes)

            # Store OTP in Redis
            otp_key = self._get_otp_key(user_id, action)
            otp_data = {
                "code": otp_code,
                "expires_at": expires_at.isoformat(),
                "attempts": 0
            }
            self.redis_client.setex(
                otp_key,
                timedelta(minutes=self.otp_expire_minutes),
                json.dumps(otp_data)
            )

            # Prepare message based on action
            messages = {
                "login": f"【CBSC】您的登錄驗證碼是: {otp_code}，{self.otp_expire_minutes}分鐘內有效。",
                "register": f"【CBSC】您的註冊驗證碼是: {otp_code}，{self.otp_expire_minutes}分鐘內有效。",
                "reset_password": f"【CBSC】您的密碼重置驗證碼是: {otp_code}，{self.otp_expire_minutes}分鐘內有效。",
                "mfa_enable": f"【CBSC】您的MFA啟用驗證碼是: {otp_code}，{self.otp_expire_minutes}分鐘內有效。",
                "mfa_verify": f"【CBSC】您的操作驗證碼是: {otp_code}，{self.otp_expire_minutes}分鐘內有效。"
            }

            message = messages.get(action, messages["login"])

            # Send SMS
            if self.sms_provider == "aliyun":
                result = self._send_sms_aliyun(phone_validation["formatted"], otp_code)
            else:
                result = self._send_sms(phone_validation["formatted"], message)

            if result["success"]:
                return {
                    "success": True,
                    "message": "驗證碼已發送",
                    "expires_at": expires_at.isoformat(),
                    "phone_display": phone_validation["display"][:3] + "****" + phone_validation["display"][-4:]
                }
            else:
                return {"success": False, "error": f"短信發送失敗: {result['error']}"}

        except Exception as e:
            logger.error(f"Error sending OTP: {str(e)}")
            return {"success": False, "error": str(e)}
        finally:
            db.close()

    def verify_otp(self, user_id: str, otp_code: str, action: str = "login") -> Dict[str, Any]:
        """Verify OTP code"""
        try:
            # Get OTP from Redis
            otp_key = self._get_otp_key(user_id, action)
            otp_data_str = self.redis_client.get(otp_key)

            if not otp_data_str:
                return {"success": False, "error": "驗證碼已過期或不存在"}

            otp_data = json.loads(otp_data_str)

            # Check attempts
            if otp_data["attempts"] >= self.max_attempts:
                self.redis_client.delete(otp_key)
                return {"success": False, "error": "驗證失敗次數過多，請重新獲取驗證碼"}

            # Check expiration
            expires_at = datetime.fromisoformat(otp_data["expires_at"])
            if datetime.now(timezone.utc) > expires_at:
                self.redis_client.delete(otp_key)
                return {"success": False, "error": "驗證碼已過期"}

            # Verify code
            if otp_code != otp_data["code"]:
                # Increment attempts
                otp_data["attempts"] += 1
                self.redis_client.setex(
                    otp_key,
                    timedelta(minutes=self.otp_expire_minutes),
                    json.dumps(otp_data)
                )
                return {"success": False, "error": "驗證碼錯誤"}

            # Clear OTP after successful verification
            self.redis_client.delete(otp_key)

            return {
                "success": True,
                "message": "驗證成功",
                "verified": True
            }

        except Exception as e:
            logger.error(f"Error verifying OTP: {str(e)}")
            return {"success": False, "error": str(e)}

    def enable_sms_mfa(self, user_id: str, otp_code: str) -> Dict[str, Any]:
        """Enable SMS MFA for user"""
        db = self._get_db()
        try:
            # Verify OTP first
            result = self.verify_otp(user_id, otp_code, "mfa_enable")
            if not result["success"]:
                return result

            # Get user
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"success": False, "error": "用戶不存在"}

            # Enable SMS MFA
            user.mfa_enabled = True
            user.mfa_type = "sms"
            db.commit()

            return {
                "success": True,
                "message": "短信驗證已啟用",
                "mfa_enabled": True
            }

        except Exception as e:
            logger.error(f"Error enabling SMS MFA: {str(e)}")
            db.rollback()
            return {"success": False, "error": str(e)}
        finally:
            db.close()

    def disable_sms_mfa(self, user_id: str, otp_code: str) -> Dict[str, Any]:
        """Disable SMS MFA for user"""
        db = self._get_db()
        try:
            # Verify OTP first
            result = self.verify_otp(user_id, otp_code, "mfa_verify")
            if not result["success"]:
                return result

            # Get user
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"success": False, "error": "用戶不存在"}

            # Disable MFA
            user.mfa_enabled = False
            user.mfa_type = None
            db.commit()

            return {
                "success": True,
                "message": "短信驗證已禁用",
                "mfa_disabled": True
            }

        except Exception as e:
            logger.error(f"Error disabling SMS MFA: {str(e)}")
            db.rollback()
            return {"success": False, "error": str(e)}
        finally:
            db.close()

    def update_phone_number(self, user_id: str, new_phone: str, otp_code: str) -> Dict[str, Any]:
        """Update user's phone number with verification"""
        db = self._get_db()
        try:
            # Validate new phone number
            phone_validation = self._validate_phone_number(new_phone)
            if not phone_validation["valid"]:
                return {"success": False, "error": f"手機號碼無效: {phone_validation['error']}"}

            # Verify OTP
            result = self.verify_otp(user_id, otp_code, "update_phone")
            if not result["success"]:
                return result

            # Get user
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"success": False, "error": "用戶不存在"}

            # Update phone number
            user.phone = phone_validation["formatted"]
            db.commit()

            return {
                "success": True,
                "message": "手機號碼更新成功",
                "phone_display": phone_validation["display"]
            }

        except Exception as e:
            logger.error(f"Error updating phone number: {str(e)}")
            db.rollback()
            return {"success": False, "error": str(e)}
        finally:
            db.close()

    def get_sms_status(self, user_id: str) -> Dict[str, Any]:
        """Get SMS verification status for user"""
        db = self._get_db()
        try:
            # Get user
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"success": False, "error": "用戶不存在"}

            # Check if phone is verified
            phone_verified = bool(user.phone)

            # Check rate limits
            login_limit_key = self._get_rate_limit_key(user_id, "login")
            login_count = self.redis_client.get(login_limit_key) or 0

            return {
                "success": True,
                "data": {
                    "mfa_enabled": user.mfa_enabled and user.mfa_type == "sms",
                    "phone_verified": phone_verified,
                    "phone_display": (
                        user.phone[:3] + "****" + user.phone[-4:]
                        if user.phone and len(user.phone) > 7
                        else None
                    ),
                    "remaining_sms_quota": max(0, self.sms_rate_limit_per_hour - int(login_count))
                }
            }

        except Exception as e:
            logger.error(f"Error getting SMS status: {str(e)}")
            return {"success": False, "error": str(e)}
        finally:
            db.close()


# Create singleton instance
sms_service = SMSService()