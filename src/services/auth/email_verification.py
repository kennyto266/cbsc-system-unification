"""
Email verification service for multi-factor authentication

This module handles email verification for:
- User registration
- Login confirmation
- Sensitive operations
"""

import os
import secrets
import smtplib
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
import logging
from jinja2 import Template

# Database
from sqlalchemy.orm import Session
from src.core.database import get_db

# Models
from src.models.user import User

# Configuration
from src.core.config import settings

logger = logging.getLogger(__name__)


class EmailVerificationService:
    """Email verification service for MFA"""

    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.from_email = os.getenv("FROM_EMAIL", "noreply@cbsc.com")
        self.from_name = os.getenv("FROM_NAME", "CBSC量化交易系統")

        # Token expiration times
        self.registration_token_expire = timedelta(hours=24)
        self.login_token_expire = timedelta(minutes=10)
        self.operation_token_expire = timedelta(minutes=15)

        # Rate limiting
        self.max_emails_per_hour = 10
        self.max_attempts_per_day = 5

    def _get_db(self) -> Session:
        """Get database session"""
        return next(get_db())

    def _generate_verification_token(self, length: int = 32) -> str:
        """Generate secure verification token"""
        return secrets.token_urlsafe(length)

    def _generate_otp_code(self, length: int = 6) -> str:
        """Generate numeric OTP code"""
        return ''.join([str(secrets.randbelow(10)) for _ in range(length)])

    def _send_email(self, to_email: str, subject: str, html_content: str, text_content: str = None) -> bool:
        """Send email using SMTP"""
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = formataddr((self.from_name, self.from_email))
            msg["To"] = to_email

            # Attach text and HTML parts
            if text_content:
                text_part = MIMEText(text_content, "plain", "utf-8")
                msg.attach(text_part)

            html_part = MIMEText(html_content, "html", "utf-8")
            msg.attach(html_part)

            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False

    def _render_email_template(self, template_name: str, **kwargs) -> tuple[str, str]:
        """Render email template"""
        templates = {
            "registration_verification": {
                "subject": "驗證您的郵箱地址 - CBSC量化交易系統",
                "text": """
歡迎註冊 CBSC 量化交易系統！

請使用以下驗證碼完成註冊：
驗證碼：{otp_code}

如果您沒有註冊賬戶，請忽略此郵件。
驗證碼將在 {expire_minutes} 分鐘後失效。

CBSC 團隊
                """,
                "html": """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>驗證您的郵箱地址</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #2563eb; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; background: #f9fafb; }
        .otp { font-size: 24px; font-weight: bold; color: #2563eb; text-align: center;
                padding: 20px; background: white; border: 2px dashed #2563eb; margin: 20px 0; }
        .footer { text-align: center; padding: 20px; font-size: 12px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>歡迎註冊 CBSC 量化交易系統</h1>
        </div>
        <div class="content">
            <h2>驗證您的郵箱地址</h2>
            <p>感謝您註冊 CBSC 量化交易系統。請使用以下驗證碼完成郵箱驗證：</p>

            <div class="otp">{otp_code}</div>

            <p><strong>注意事項：</strong></p>
            <ul>
                <li>此驗證碼將在 {expire_minutes} 分鐘後失效</li>
                <li>請勿將此驗證碼分享給他人</li>
                <li>如果您沒有註冊賬戶，請忽略此郵件</li>
            </ul>
        </div>
        <div class="footer">
            <p>此郵件由系統自動發送，請勿回覆。</p>
            <p>© 2025 CBSC 量化交易系統. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
                """
            },
            "login_verification": {
                "subject": "登錄驗證碼 - CBSC量化交易系統",
                "text": """
您的登錄驗證碼是：
{otp_code}

驗證碼將在 {expire_minutes} 分鐘後失效。

如果這不是您本人的操作，請立即修改密碼。
                """,
                "html": """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>登錄驗證</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #dc2626; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; background: #f9fafb; }
        .otp { font-size: 28px; font-weight: bold; color: #dc2626; text-align: center;
                padding: 20px; background: white; border: 2px dashed #dc2626; margin: 20px 0; }
        .warning { background: #fef2f2; border: 1px solid #fecaca; padding: 15px;
                   border-radius: 5px; margin: 20px 0; }
        .footer { text-align: center; padding: 20px; font-size: 12px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>登錄驗證</h1>
        </div>
        <div class="content">
            <h2>您的登錄驗證碼</h2>
            <p>我們檢測到您的賬戶嘗試登錄，請使用以下驗證碼完成驗證：</p>

            <div class="otp">{otp_code}</div>

            <div class="warning">
                <strong>安全提醒：</strong>
                <ul>
                    <li>驗證碼將在 {expire_minutes} 分鐘後失效</li>
                    <li>請勿將此驗證碼分享給任何人</li>
                    <li>如果這不是您本人的操作，請立即聯繫客服</li>
                </ul>
            </div>
        </div>
        <div class="footer">
            <p>© 2025 CBSC 量化交易系統. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
                """
            },
            "operation_verification": {
                "subject": "操作驗證碼 - CBSC量化交易系統",
                "text": """
您正在執行敏感操作，驗證碼：
{otp_code}

操作：{operation}
驗證碼將在 {expire_minutes} 分鐘後失效。

如果這不是您本人的操作，請立即聯繫客服。
                """,
                "html": """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>操作驗證</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #f59e0b; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; background: #f9fafb; }
        .operation { background: #fef3c7; border: 1px solid #fde68a; padding: 15px;
                     border-radius: 5px; margin: 20px 0; font-weight: bold; }
        .otp { font-size: 28px; font-weight: bold; color: #f59e0b; text-align: center;
                padding: 20px; background: white; border: 2px dashed #f59e0b; margin: 20px 0; }
        .footer { text-align: center; padding: 20px; font-size: 12px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>操作驗證</h1>
        </div>
        <div class="content">
            <h2>敏感操作驗證</h2>
            <p>您正在執行以下敏感操作，請使用驗證碼確認：</p>

            <div class="operation">
                操作類型：{operation}
                <br>執行時間：{timestamp}
            </div>

            <div class="otp">{otp_code}</div>

            <p><strong>注意事項：</strong></p>
            <ul>
                <li>驗證碼將在 {expire_minutes} 分鐘後失效</li>
                <li>請確認您本人執行此操作</li>
                <li>如有疑問，請立即聯繫客服</li>
            </ul>
        </div>
        <div class="footer">
            <p>© 2025 CBSC 量化交易系統. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
                """
            }
        }

        template = templates.get(template_name, templates["registration_verification"])

        # Render text content
        text_template = Template(template["text"])
        text_content = text_template.render(**kwargs)

        # Render HTML content
        html_template = Template(template["html"])
        html_content = html_template.render(**kwargs)

        return template["subject"], text_content, html_content

    def send_registration_verification(self, user_id: str) -> Dict[str, Any]:
        """Send email verification for user registration"""
        db = self._get_db()
        try:
            # Get user
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"success": False, "error": "用戶不存在"}

            # Check rate limit
            # TODO: Implement rate limiting using Redis

            # Generate OTP code
            otp_code = self._generate_otp_code()
            expires_at = datetime.now(timezone.utc) + self.registration_token_expire

            # Store verification code
            # TODO: Store in Redis or database with expiration
            user.email_verification_code = otp_code
            user.email_verification_expires = expires_at
            db.commit()

            # Send email
            subject, text_content, html_content = self._render_email_template(
                "registration_verification",
                otp_code=otp_code,
                expire_minutes=int(self.registration_token_expire.total_seconds() / 60),
                user_name=user.display_name or user.username
            )

            success = self._send_email(user.email, subject, html_content, text_content)

            if success:
                return {
                    "success": True,
                    "message": "驗證郵件已發送",
                    "expires_at": expires_at.isoformat()
                }
            else:
                return {"success": False, "error": "郵件發送失敗"}

        except Exception as e:
            logger.error(f"Error sending registration verification: {str(e)}")
            db.rollback()
            return {"success": False, "error": str(e)}
        finally:
            db.close()

    def send_login_verification(self, user_id: str, ip_address: str = None) -> Dict[str, Any]:
        """Send email verification for login"""
        db = self._get_db()
        try:
            # Get user
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"success": False, "error": "用戶不存在"}

            # Check if user has email verification enabled
            if not user.email_verified:
                return {"success": False, "error": "郵箱未驗證"}

            # Generate OTP code
            otp_code = self._generate_otp_code()
            expires_at = datetime.now(timezone.utc) + self.login_token_expire

            # Store verification code
            # TODO: Store in Redis or database with expiration
            user.login_verification_code = otp_code
            user.login_verification_expires = expires_at
            db.commit()

            # Send email
            subject, text_content, html_content = self._render_email_template(
                "login_verification",
                otp_code=otp_code,
                expire_minutes=int(self.login_token_expire.total_seconds() / 60),
                ip_address=ip_address or "未知",
                user_name=user.display_name or user.username
            )

            success = self._send_email(user.email, subject, html_content, text_content)

            if success:
                return {
                    "success": True,
                    "message": "登錄驗證碼已發送",
                    "expires_at": expires_at.isoformat()
                }
            else:
                return {"success": False, "error": "郵件發送失敗"}

        except Exception as e:
            logger.error(f"Error sending login verification: {str(e)}")
            db.rollback()
            return {"success": False, "error": str(e)}
        finally:
            db.close()

    def send_operation_verification(self, user_id: str, operation: str, details: Dict = None) -> Dict[str, Any]:
        """Send email verification for sensitive operations"""
        db = self._get_db()
        try:
            # Get user
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"success": False, "error": "用戶不存在"}

            # Check if user has MFA enabled for operations
            # TODO: Check user MFA preferences

            # Generate OTP code
            otp_code = self._generate_otp_code()
            expires_at = datetime.now(timezone.utc) + self.operation_token_expire

            # Store verification code
            # TODO: Store in Redis or database with operation context
            user.operation_verification_code = otp_code
            user.operation_verification_expires = expires_at
            user.operation_type = operation
            db.commit()

            # Send email
            subject, text_content, html_content = self._render_email_template(
                "operation_verification",
                otp_code=otp_code,
                expire_minutes=int(self.operation_token_expire.total_seconds() / 60),
                operation=operation,
                timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
                user_name=user.display_name or user.username
            )

            success = self._send_email(user.email, subject, html_content, text_content)

            if success:
                return {
                    "success": True,
                    "message": f"{operation}驗證碼已發送",
                    "expires_at": expires_at.isoformat()
                }
            else:
                return {"success": False, "error": "郵件發送失敗"}

        except Exception as e:
            logger.error(f"Error sending operation verification: {str(e)}")
            db.rollback()
            return {"success": False, "error": str(e)}
        finally:
            db.close()

    def verify_email_code(self, user_id: str, code: str, verification_type: str = "registration") -> Dict[str, Any]:
        """Verify email verification code"""
        db = self._get_db()
        try:
            # Get user
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"success": False, "error": "用戶不存在"}

            # Check verification type
            if verification_type == "registration":
                stored_code = user.email_verification_code
                expires_at = user.email_verification_expires
            elif verification_type == "login":
                stored_code = user.login_verification_code
                expires_at = user.login_verification_expires
            elif verification_type == "operation":
                stored_code = user.operation_verification_code
                expires_at = user.operation_verification_expires
            else:
                return {"success": False, "error": "無效的驗證類型"}

            # Verify code
            if not stored_code or not expires_at:
                return {"success": False, "error": "未找到驗證碼"}

            if datetime.now(timezone.utc) > expires_at:
                return {"success": False, "error": "驗證碼已過期"}

            if code != stored_code:
                return {"success": False, "error": "驗證碼錯誤"}

            # Clear verification code
            if verification_type == "registration":
                user.email_verification_code = None
                user.email_verification_expires = None
                user.email_verified = True
            elif verification_type == "login":
                user.login_verification_code = None
                user.login_verification_expires = None
            elif verification_type == "operation":
                user.operation_verification_code = None
                user.operation_verification_expires = None
                user.operation_type = None

            db.commit()

            return {
                "success": True,
                "message": "驗證成功",
                "verified": True
            }

        except Exception as e:
            logger.error(f"Error verifying email code: {str(e)}")
            db.rollback()
            return {"success": False, "error": str(e)}
        finally:
            db.close()


# Create singleton instance
email_verification_service = EmailVerificationService()