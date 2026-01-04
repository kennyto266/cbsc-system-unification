"""
Enhanced Authentication Service v2
增強版認證服務 v2

Supports MFA, JWT refresh tokens, device management, and enhanced security
支持多因子認證、JWT 刷新令牌、設備管理和增強安全功能
"""

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import jwt
import pyotp
import qrcode
import io
import base64
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List, Tuple
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr, Field
import redis
import json
import uuid
import secrets
import logging
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
import os
from enum import Enum as PyEnum

# Configure logging
logger = logging.getLogger(__name__)

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./user_management.db")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
REFRESH_SECRET_KEY = os.getenv("REFRESH_SECRET_KEY", "your-refresh-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Redis client for token blacklist and refresh tokens
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

# Database models
Base = declarative_base()

class MFAType(str, PyEnum):
    """MFA types"""
    TOTP = "totp"  # Time-based One-Time Password
    EMAIL = "email"  # Email verification
    SMS = "sms"  # SMS verification

class UserMFA(Base):
    """User MFA configuration"""
    __tablename__ = "user_mfa"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    mfa_type = Column(Enum(MFAType), nullable=False)
    secret = Column(String(255))  # TOTP secret
    email = Column(String(255))  # For email MFA
    phone = Column(String(20))  # For SMS MFA
    is_enabled = Column(Boolean, default=False)
    backup_codes = Column(Text)  # JSON array of backup codes
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime)

    # Relationship
    user = relationship("User", back_populates="mfa_settings")

class RefreshToken(Base):
    """Refresh token model"""
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token_id = Column(String(255), unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    device_name = Column(String(100))
    device_fingerprint = Column(String(255))
    expires_at = Column(DateTime, nullable=False)
    is_revoked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime, default=datetime.utcnow)

    # Relationship
    user = relationship("User", back_populates="refresh_tokens")

class LoginAttempt(Base):
    """Login attempt tracking for rate limiting"""
    __tablename__ = "login_attempts"

    id = Column(Integer, primary_key=True, index=True)
    ip_address = Column(String(45), index=True)
    username = Column(String(50), index=True)
    attempt_time = Column(DateTime, default=datetime.utcnow)
    success = Column(Boolean)
    user_agent = Column(Text)
    failure_reason = Column(String(100))

# Pydantic models
class MFASetupRequest(BaseModel):
    """MFA setup request"""
    mfa_type: MFAType
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

class MFASetupResponse(BaseModel):
    """MFA setup response"""
    mfa_type: MFAType
    secret: Optional[str] = None  # TOTP secret
    qr_code: Optional[str] = None  # Base64 encoded QR code
    backup_codes: Optional[List[str]] = None
    message: str

class MFAVerifyRequest(BaseModel):
    """MFA verification request"""
    code: str
    backup_code: Optional[str] = None

class TokenRefreshRequest(BaseModel):
    """Token refresh request"""
    refresh_token: str
    device_fingerprint: str

class TokenResponse(BaseModel):
    """Token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_expires_in: int

class LoginResponse(BaseModel):
    """Login response with MFA challenge"""
    requires_mfa: bool
    mfa_types: Optional[List[MFAType]] = None
    mfa_challenge_token: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: Optional[str] = None
    expires_in: Optional[int] = None
    refresh_expires_in: Optional[int] = None

class UserRegistrationRequest(BaseModel):
    """User registration request"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    confirm_password: str

    def validate_passwords_match(self):
        """Validate passwords match"""
        if self.password != self.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Passwords do not match"
            )

class AuthServiceV2:
    """Enhanced Authentication Service v2"""

    def __init__(self):
        self.engine = create_engine(DATABASE_URL)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v2/auth/login")

    def get_db(self):
        """Get database session"""
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()

    def hash_password(self, password: str) -> str:
        """Hash password using argon2"""
        # Use argon2 for secure password hashing
        ph = PasswordHasher(
            time_cost=2,
            memory_cost=65536,
            parallelism=4,
            hash_len=32,
            salt_len=16
        )
        return ph.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password"""
        try:
            ph = PasswordHasher(
                time_cost=2,
                memory_cost=65536,
                parallelism=4,
                hash_len=32,
                salt_len=16
            )
            return ph.verify(hashed_password, plain_password)
        except VerifyMismatchError:
            return False
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False

    def validate_password_strength(self, password: str) -> Dict[str, Any]:
        """Validate password strength"""
        requirements = {
            'length': len(password) >= 8,
            'uppercase': bool(re.search(r'[A-Z]', password)),
            'lowercase': bool(re.search(r'[a-z]', password)),
            'numbers': bool(re.search(r'\d', password)),
            'special': bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password)),
            'no_common_patterns': not bool(re.search(r'(123456|password|qwerty)', password, re.I))
        }

        score = sum(requirements.values())

        if score <= 2:
            level = 'weak'
            text = 'Weak'
        elif score <= 4:
            level = 'medium'
            text = 'Medium'
        else:
            level = 'strong'
            text = 'Strong'

        return {
            'score': score,
            'level': level,
            'text': text,
            'requirements': requirements
        }

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({
            "exp": expire,
            "type": "access",
            "jti": str(uuid.uuid4())  # Unique token ID
        })

        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    def create_refresh_token(self, user_id: int, device_name: str, device_fingerprint: str) -> Tuple[str, datetime]:
        """Create refresh token"""
        # Generate unique token ID
        token_id = str(uuid.uuid4())

        # Calculate expiration
        expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

        # Store in database
        db = self.SessionLocal()
        try:
            refresh_token = RefreshToken(
                token_id=token_id,
                user_id=user_id,
                device_name=device_name,
                device_fingerprint=device_fingerprint,
                expires_at=expires_at
            )
            db.add(refresh_token)
            db.commit()

            # Create JWT token
            token_data = {
                "sub": str(user_id),
                "type": "refresh",
                "jti": token_id,
                "device_fp": device_fingerprint
            }

            token = jwt.encode(token_data, REFRESH_SECRET_KEY, algorithm=ALGORITHM)
            return token, expires_at

        finally:
            db.close()

    def verify_refresh_token(self, token: str, device_fingerprint: str) -> Optional[Dict]:
        """Verify refresh token"""
        try:
            payload = jwt.decode(token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])

            # Check token type
            if payload.get("type") != "refresh":
                return None

            # Check device fingerprint
            if payload.get("device_fp") != device_fingerprint:
                logger.warning(f"Device fingerprint mismatch for token {payload.get('jti')}")
                return None

            # Check if token exists in database and is not revoked
            token_id = payload.get("jti")
            db = self.SessionLocal()
            try:
                refresh_token = db.query(RefreshToken).filter(
                    RefreshToken.token_id == token_id,
                    RefreshToken.is_revoked == False,
                    RefreshToken.expires_at > datetime.utcnow()
                ).first()

                if not refresh_token:
                    return None

                # Update last used
                refresh_token.last_used = datetime.utcnow()
                db.commit()

                return payload

            finally:
                db.close()

        except jwt.PyJWTError as e:
            logger.error(f"Refresh token verification error: {e}")
            return None

    def revoke_refresh_token(self, token_id: str) -> bool:
        """Revoke refresh token"""
        db = self.SessionLocal()
        try:
            refresh_token = db.query(RefreshToken).filter(
                RefreshToken.token_id == token_id
            ).first()

            if refresh_token:
                refresh_token.is_revoked = True
                db.commit()
                return True

            return False

        except Exception as e:
            logger.error(f"Error revoking refresh token: {e}")
            db.rollback()
            return False
        finally:
            db.close()

    def revoke_all_user_tokens(self, user_id: int) -> bool:
        """Revoke all refresh tokens for a user"""
        db = self.SessionLocal()
        try:
            db.query(RefreshToken).filter(
                RefreshToken.user_id == user_id,
                RefreshToken.is_revoked == False
            ).update({"is_revoked": True})

            db.commit()
            return True

        except Exception as e:
            logger.error(f"Error revoking all tokens for user {user_id}: {e}")
            db.rollback()
            return False
        finally:
            db.close()

    def check_rate_limit(self, ip_address: str, username: str) -> bool:
        """Check rate limiting for login attempts"""
        db = self.SessionLocal()
        try:
            # Count failed attempts in last 15 minutes
            cutoff = datetime.utcnow() - timedelta(minutes=15)
            failed_attempts = db.query(LoginAttempt).filter(
                LoginAttempt.ip_address == ip_address,
                LoginAttempt.attempt_time >= cutoff,
                LoginAttempt.success == False
            ).count()

            # Allow max 5 failed attempts per 15 minutes
            if failed_attempts >= 5:
                logger.warning(f"Rate limit exceeded for IP {ip_address}")
                return False

            # Check per-user limit (max 10 failed attempts per hour)
            cutoff = datetime.utcnow() - timedelta(hours=1)
            user_failed_attempts = db.query(LoginAttempt).filter(
                LoginAttempt.username == username,
                LoginAttempt.attempt_time >= cutoff,
                LoginAttempt.success == False
            ).count()

            if user_failed_attempts >= 10:
                logger.warning(f"Rate limit exceeded for user {username}")
                return False

            return True

        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            return True  # Allow on error
        finally:
            db.close()

    def record_login_attempt(self, ip_address: str, username: str, success: bool, user_agent: str, failure_reason: str = None):
        """Record login attempt for rate limiting"""
        db = self.SessionLocal()
        try:
            attempt = LoginAttempt(
                ip_address=ip_address,
                username=username,
                success=success,
                user_agent=user_agent,
                failure_reason=failure_reason
            )
            db.add(attempt)
            db.commit()

        except Exception as e:
            logger.error(f"Error recording login attempt: {e}")
            db.rollback()
        finally:
            db.close()

    def generate_totp_secret(self) -> str:
        """Generate TOTP secret"""
        return pyotp.random_base32()

    def generate_qr_code(self, secret: str, username: str, issuer: str = "CBSC Quant") -> str:
        """Generate QR code for TOTP setup"""
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=username,
            issuer_name=issuer
        )

        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()

        return f"data:image/png;base64,{img_str}"

    def verify_totp(self, secret: str, token: str) -> bool:
        """Verify TOTP token"""
        try:
            totp = pyotp.TOTP(secret)
            return totp.verify(token, valid_window=1)  # Allow 1 step tolerance
        except Exception as e:
            logger.error(f"TOTP verification error: {e}")
            return False

    def generate_backup_codes(self, count: int = 10) -> List[str]:
        """Generate backup codes"""
        codes = []
        for _ in range(count):
            code = secrets.token_hex(4).upper()
            codes.append(code)
        return codes

    def get_user_mfa_settings(self, user_id: int) -> List[UserMFA]:
        """Get user MFA settings"""
        db = self.SessionLocal()
        try:
            return db.query(UserMFA).filter(
                UserMFA.user_id == user_id,
                UserMFA.is_enabled == True
            ).all()
        finally:
            db.close()

    def generate_mfa_challenge_token(self, user_id: int, mfa_types: List[MFAType]) -> str:
        """Generate temporary MFA challenge token"""
        challenge_data = {
            "sub": str(user_id),
            "mfa_types": [t.value for t in mfa_types],
            "type": "mfa_challenge",
            "exp": datetime.utcnow() + timedelta(minutes=10)
        }

        return jwt.encode(challenge_data, SECRET_KEY, algorithm=ALGORITHM)

    def verify_mfa_challenge_token(self, token: str) -> Optional[Dict]:
        """Verify MFA challenge token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

            if payload.get("type") != "mfa_challenge":
                return None

            return payload

        except jwt.PyJWTError:
            return None

# Import existing User model if needed
# Note: User model should be imported from src.models.user
# from auth_simple import User

# Add relationships to existing User model
# User.mfa_settings = relationship("UserMFA", back_populates="user", cascade="all, delete-orphan")
# User.refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")

# Create tables
# Note: Tables should be created by migrations, not here
# Base.metadata.create_all(bind=create_engine(DATABASE_URL))

# Global instance
auth_service_v2 = AuthServiceV2()