"""
Password Reset and Email Verification Service
Handles password reset flows, email verification, and account security.
"""

import secrets
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import ssl
from smtplib import SMTP
from dataclasses import dataclass

try:
    from models.unified_models import User
    from config.api_config import settings
except ImportError:
    # Fallback configuration
    class settings:
        SMTP_HOST = "smtp.gmail.com"
        SMTP_PORT = 587
        SMTP_USER = ""
        SMTP_PASSWORD = ""
        SMTP_FROM_EMAIL = "noreply@cbsc.com"
        SMTP_FROM_NAME = "CBSC Trading System"
        SMTP_USE_TLS = True

        PASSWORD_RESET_TOKEN_EXPIRE_HOURS = 1
        EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS = 24
        FRONTEND_URL = "http://localhost:3000"

logger = logging.getLogger(__name__)


@dataclass
class PasswordResetToken:
    """Password reset token data"""
    token: str
    user_id: int
    expires_at: datetime
    created_at: datetime
    is_used: bool = False


@dataclass
class EmailVerificationToken:
    """Email verification token data"""
    token: str
    email: str
    user_id: Optional[int]
    expires_at: datetime
    created_at: datetime
    is_verified: bool = False


class PasswordResetService:
    """
    Password Reset and Email Verification Service
    """

    def __init__(self):
        # In production, store tokens in Redis or database
        self._reset_tokens: Dict[str, PasswordResetToken] = {}
        self._verification_tokens: Dict[str, EmailVerificationToken] = {}
        self._rate_limit: Dict[str, List[datetime]] = {}

    def _generate_secure_token(self, length: int = 64) -> str:
        """Generate cryptographically secure token"""
        return secrets.token_urlsafe(length)

    def _hash_token(self, token: str) -> str:
        """Hash token for storage"""
        return hashlib.sha256(token.encode()).hexdigest()

    def _check_rate_limit(self, identifier: str, max_requests: int = 3, window_minutes: int = 60) -> bool:
        """
        Check rate limit for password reset/verification requests.

        Args:
            identifier: Email or IP address
            max_requests: Maximum requests allowed
            window_minutes: Time window in minutes

        Returns:
            True if request is allowed, False if rate limited
        """
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=window_minutes)

        if identifier not in self._rate_limit:
            self._rate_limit[identifier] = []

        # Clean old requests
        self._rate_limit[identifier] = [
            req_time for req_time in self._rate_limit[identifier]
            if req_time > window_start
        ]

        # Check limit
        if len(self._rate_limit[identifier]) >= max_requests:
            logger.warning(f"Rate limit exceeded for {identifier}")
            return False

        # Add current request
        self._rate_limit[identifier].append(now)
        return True

    async def send_password_reset_email(
        self,
        email: str,
        user_id: int,
        username: str
    ) -> Dict[str, Any]:
        """
        Send password reset email to user.

        Args:
            email: User email address
            user_id: User ID
            username: Username

        Returns:
            Response with token (for testing) or error
        """
        try:
            # Check rate limit
            if not self._check_rate_limit(email, max_requests=3, window_minutes=60):
                return {
                    "success": False,
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "Too many password reset requests. Please try again later.",
                        "retry_after": 3600  # seconds
                    }
                }

            # Generate reset token
            reset_token = self._generate_secure_token()
            token_hash = self._hash_token(reset_token)

            # Store token
            expires_at = datetime.utcnow() + timedelta(
                hours=settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS
            )

            self._reset_tokens[token_hash] = PasswordResetToken(
                token=token_hash,
                user_id=user_id,
                expires_at=expires_at,
                created_at=datetime.utcnow()
            )

            # Create reset link
            reset_link = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"

            # Send email
            await self._send_email(
                to_email=email,
                subject="Password Reset Request - CBSC Trading System",
                template="password_reset",
                context={
                    "username": username,
                    "reset_link": reset_link,
                    "expires_hours": settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS
                }
            )

            logger.info(f"Password reset email sent to {email}")

            return {
                "success": True,
                "data": {
                    "message": "Password reset email sent successfully",
                    "expires_at": expires_at.isoformat(),
                    # Only return token in development for testing
                    "token": reset_token if settings.DEBUG else None
                }
            }

        except Exception as e:
            logger.error(f"Failed to send password reset email: {e}")
            return {
                "success": False,
                "error": {
                    "code": "EMAIL_SEND_FAILED",
                    "message": "Failed to send password reset email"
                }
            }

    async def verify_password_reset_token(
        self,
        token: str
    ) -> Dict[str, Any]:
        """
        Verify password reset token.

        Args:
            token: Reset token from email

        Returns:
            Verification result
        """
        try:
            token_hash = self._hash_token(token)

            if token_hash not in self._reset_tokens:
                return {
                    "success": False,
                    "error": {
                        "code": "INVALID_TOKEN",
                        "message": "Invalid or expired reset token"
                    }
                }

            reset_token_data = self._reset_tokens[token_hash]

            # Check if token is expired
            if datetime.utcnow() > reset_token_data.expires_at:
                del self._reset_tokens[token_hash]
                return {
                    "success": False,
                    "error": {
                        "code": "TOKEN_EXPIRED",
                        "message": "Reset token has expired. Please request a new one."
                    }
                }

            # Check if token is already used
            if reset_token_data.is_used:
                return {
                    "success": False,
                    "error": {
                        "code": "TOKEN_ALREADY_USED",
                        "message": "This reset token has already been used."
                    }
                }

            return {
                "success": True,
                "data": {
                    "user_id": reset_token_data.user_id,
                    "valid": True
                }
            }

        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            return {
                "success": False,
                "error": {
                    "code": "VERIFICATION_FAILED",
                    "message": "Failed to verify reset token"
                }
            }

    async def reset_password(
        self,
        token: str,
        new_password: str
    ) -> Dict[str, Any]:
        """
        Reset user password using valid token.

        Args:
            token: Reset token from email
            new_password: New password

        Returns:
            Password reset result
        """
        try:
            # Verify token
            verification = await self.verify_password_reset_token(token)
            if not verification["success"]:
                return verification

            token_hash = self._hash_token(token)
            reset_token_data = self._reset_tokens[token_hash]

            # Hash new password (using auth module)
            from utils.auth import hash_password
            password_hash = hash_password(new_password)

            # TODO: Update user password in database
            # await user_service.update_password(reset_token_data.user_id, password_hash)

            # Mark token as used
            reset_token_data.is_used = True

            # Clean up old tokens
            await self._cleanup_expired_tokens()

            logger.info(f"Password reset successful for user_id {reset_token_data.user_id}")

            return {
                "success": True,
                "data": {
                    "message": "Password reset successfully"
                }
            }

        except Exception as e:
            logger.error(f"Password reset failed: {e}")
            return {
                "success": False,
                "error": {
                    "code": "RESET_FAILED",
                    "message": "Failed to reset password"
                }
            }

    async def send_email_verification(
        self,
        email: str,
        user_id: Optional[int],
        username: str
    ) -> Dict[str, Any]:
        """
        Send email verification link.

        Args:
            email: User email
            user_id: User ID (optional for new users)
            username: Username

        Returns:
            Response with verification status
        """
        try:
            # Generate verification token
            verification_token = self._generate_secure_token()
            token_hash = self._hash_token(verification_token)

            # Store token
            expires_at = datetime.utcnow() + timedelta(
                hours=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS
            )

            self._verification_tokens[token_hash] = EmailVerificationToken(
                token=token_hash,
                email=email,
                user_id=user_id,
                expires_at=expires_at,
                created_at=datetime.utcnow()
            )

            # Create verification link
            verification_link = f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"

            # Send email
            await self._send_email(
                to_email=email,
                subject="Verify Your Email - CBSC Trading System",
                template="email_verification",
                context={
                    "username": username,
                    "verification_link": verification_link,
                    "expires_hours": settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS
                }
            )

            logger.info(f"Verification email sent to {email}")

            return {
                "success": True,
                "data": {
                    "message": "Verification email sent successfully",
                    "expires_at": expires_at.isoformat()
                }
            }

        except Exception as e:
            logger.error(f"Failed to send verification email: {e}")
            return {
                "success": False,
                "error": {
                    "code": "EMAIL_SEND_FAILED",
                    "message": "Failed to send verification email"
                }
            }

    async def verify_email(
        self,
        token: str
    ) -> Dict[str, Any]:
        """
        Verify email address using token.

        Args:
            token: Verification token from email

        Returns:
            Verification result
        """
        try:
            token_hash = self._hash_token(token)

            if token_hash not in self._verification_tokens:
                return {
                    "success": False,
                    "error": {
                        "code": "INVALID_TOKEN",
                        "message": "Invalid or expired verification token"
                    }
                }

            verification_data = self._verification_tokens[token_hash]

            # Check if expired
            if datetime.utcnow() > verification_data.expires_at:
                del self._verification_tokens[token_hash]
                return {
                    "success": False,
                    "error": {
                        "code": "TOKEN_EXPIRED",
                        "message": "Verification token has expired"
                    }
                }

            # Check if already verified
            if verification_data.is_verified:
                return {
                    "success": False,
                    "error": {
                        "code": "ALREADY_VERIFIED",
                        "message": "Email has already been verified"
                    }
                }

            # TODO: Update user email_verified status in database
            # await user_service.verify_email(verification_data.user_id)

            verification_data.is_verified = True

            logger.info(f"Email verified successfully for {verification_data.email}")

            return {
                "success": True,
                "data": {
                    "message": "Email verified successfully"
                }
            }

        except Exception as e:
            logger.error(f"Email verification failed: {e}")
            return {
                "success": False,
                "error": {
                    "code": "VERIFICATION_FAILED",
                    "message": "Failed to verify email"
                }
            }

    async def _send_email(
        self,
        to_email: str,
        subject: str,
        template: str,
        context: Dict[str, Any]
    ) -> bool:
        """
        Send email using SMTP.

        Args:
            to_email: Recipient email
            subject: Email subject
            template: Template name
            context: Template context

        Returns:
            True if email sent successfully
        """
        try:
            # Render email template
            body = self._render_email_template(template, context)

            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
            message["To"] = to_email

            # Attach HTML body
            html_part = MIMEText(body, "html")
            message.attach(html_part)

            # Send email
            if settings.SMTP_USE_TLS:
                context = ssl.create_default_context()
                with SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                    server.starttls(context=context)
                    if settings.SMTP_USER and settings.SMTP_PASSWORD:
                        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    server.send_message(message)
            else:
                with SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                    if settings.SMTP_USER and settings.SMTP_PASSWORD:
                        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    server.send_message(message)

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            raise

    def _render_email_template(self, template: str, context: Dict[str, Any]) -> str:
        """Render email template with context"""
        templates = {
            "password_reset": """
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #3b82f6; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 30px; background: #f9fafb; }}
        .button {{ display: inline-block; padding: 12px 30px; background: #3b82f6; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
        .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>CBSC Trading System</h1>
        </div>
        <div class="content">
            <h2>Password Reset Request</h2>
            <p>Hi {username},</p>
            <p>We received a request to reset your password. Click the button below to reset it:</p>
            <center><a href="{reset_link}" class="button">Reset Password</a></center>
            <p>Or copy and paste this link into your browser:</p>
            <p style="word-break: break-all;">{reset_link}</p>
            <p><strong>This link will expire in {expires_hours} hours.</strong></p>
            <p>If you didn't request this, please ignore this email.</p>
        </div>
        <div class="footer">
            <p>&copy; 2025 CBSC Trading System. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
            """,

            "email_verification": """
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #10b981; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 30px; background: #f9fafb; }}
        .button {{ display: inline-block; padding: 12px 30px; background: #10b981; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
        .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>CBSC Trading System</h1>
        </div>
        <div class="content">
            <h2>Verify Your Email</h2>
            <p>Hi {username},</p>
            <p>Thank you for registering! Please verify your email address by clicking the button below:</p>
            <center><a href="{verification_link}" class="button">Verify Email</a></center>
            <p>Or copy and paste this link into your browser:</p>
            <p style="word-break: break-all;">{verification_link}</p>
            <p><strong>This link will expire in {expires_hours} hours.</strong></p>
        </div>
        <div class="footer">
            <p>&copy; 2025 CBSC Trading System. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
            """
        }

        template_str = templates.get(template, "")
        return template_str.format(**context)

    async def _cleanup_expired_tokens(self) -> None:
        """Clean up expired tokens"""
        now = datetime.utcnow()

        # Clean up reset tokens
        expired_reset = [
            token_hash for token_hash, token_data in self._reset_tokens.items()
            if now > token_data.expires_at
        ]
        for token_hash in expired_reset:
            del self._reset_tokens[token_hash]

        # Clean up verification tokens
        expired_verification = [
            token_hash for token_hash, token_data in self._verification_tokens.items()
            if now > token_data.expires_at
        ]
        for token_hash in expired_verification:
            del self._verification_tokens[token_hash]

        logger.debug(f"Cleaned up {len(expired_reset)} expired reset tokens and {len(expired_verification)} expired verification tokens")


# Global password reset service instance
password_reset_service = PasswordResetService()


__all__ = [
    'PasswordResetService',
    'password_reset_service',
    'PasswordResetToken',
    'EmailVerificationToken',
]
