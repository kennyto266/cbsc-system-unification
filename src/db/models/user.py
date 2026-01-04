"""
User ORM Models

Database models for user authentication and session management.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, List

import sqlalchemy
from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, Text, Float,
    ForeignKey, Index, CheckConstraint
)
from sqlalchemy.orm import relationship

from .base import BaseModel, SoftDeleteMixin


class User(BaseModel, SoftDeleteMixin):
    """User ORM model"""
    __tablename__ = "users"

    # Core authentication fields
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    # User role and status
    role = Column(String(20), nullable=False, default='viewer')
    is_active = Column(Boolean, default=True, nullable=False)
    email_verified = Column(Boolean, default=False, nullable=False)

    # Profile fields
    full_name = Column(String(100))
    phone = Column(String(20))
    avatar_url = Column(String(500))
    bio = Column(Text)
    timezone = Column(String(50), default='UTC')
    language = Column(String(10), default='en')

    # Security fields
    last_login = Column(DateTime(timezone=True))
    login_count = Column(Integer, default=0, nullable=False)
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime(timezone=True))
    password_changed_at = Column(DateTime(timezone=True))
    mfa_enabled = Column(Boolean, default=False)
    mfa_secret = Column(String(100))  # TOTP secret

    # Preferences
    preferences = Column(sqlalchemy.JSON)  # User preferences
    notification_settings = Column(sqlalchemy.JSON)  # Notification config

    # Relationships
    strategies = relationship(
        "Strategy",
        back_populates="creator",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    sessions = relationship(
        "UserSession",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )

    # Constraints and indexes
    __table_args__ = (
        Index('idx_user_active', 'is_active'),
        Index('idx_user_role', 'role'),
        Index('idx_user_email_verified', 'email_verified'),
        CheckConstraint('role IN ("admin", "trader", "analyst", "viewer")', name='ck_user_role'),
        CheckConstraint('failed_login_attempts >= 0', name='ck_failed_attempts'),
    )

    @property
    def is_locked(self) -> bool:
        """Check if account is locked"""
        if self.locked_until:
            return datetime.now(timezone.utc) < self.locked_until
        return False

    @property
    def is_admin(self) -> bool:
        """Check if user is admin"""
        return self.role == 'admin'

    @property
    def can_trade(self) -> bool:
        """Check if user can execute trades"""
        return self.role in ['admin', 'trader'] and self.is_active and not self.is_locked

    @property
    def active_sessions(self) -> List:
        """Get all active sessions"""
        return self.sessions.filter(
            UserSession.is_active == True,
            UserSession.expires_at > datetime.now(timezone.utc)
        ).all()

    def record_login(self):
        """Record successful login"""
        self.last_login = datetime.now(timezone.utc)
        self.login_count += 1
        self.failed_login_attempts = 0
        self.locked_until = None

    def record_failed_login(self, max_attempts: int = 5, lock_minutes: int = 30):
        """Record failed login attempt"""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= max_attempts:
            self.locked_until = datetime.now(timezone.utc) + timedelta(minutes=lock_minutes)

    def change_password(self, new_hash: str):
        """Change user password"""
        self.password_hash = new_hash
        self.password_changed_at = datetime.now(timezone.utc)

    def revoke_sessions(self, exclude_session_id: Optional[str] = None):
        """Revoke all user sessions except optionally one"""
        sessions = self.sessions.filter(
            UserSession.is_active == True
        )
        if exclude_session_id:
            sessions = sessions.filter(UserSession.session_id != exclude_session_id)
        sessions.update({UserSession.is_active: False})

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"


class UserSession(BaseModel):
    """User Session ORM model"""
    __tablename__ = "user_sessions"

    # Core fields
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    session_id = Column(String(100), unique=True, nullable=False, index=True)

    # Device information
    device_id = Column(String(100))
    device_name = Column(String(100))
    device_type = Column(String(50))  # desktop, mobile, tablet

    # Network information
    ip_address = Column(String(45))  # Support IPv6
    user_agent = Column(Text)
    browser = Column(String(50))
    os = Column(String(50))

    # Geolocation (optional)
    country = Column(String(100))
    city = Column(String(100))
    latitude = Column(sqlalchemy.Float)
    longitude = Column(sqlalchemy.Float)

    # Session lifecycle
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_activity = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Security metadata
    login_method = Column(String(20))  # password, oauth, mfa
    mfa_verified = Column(Boolean, default=False)
    trusted = Column(Boolean, default=False)

    # Session data
    session_data = Column(sqlalchemy.JSON)

    # Relationships
    user = relationship("User", back_populates="sessions")

    # Constraints and indexes
    __table_args__ = (
        Index('idx_session_user_active', 'user_id', 'is_active'),
        Index('idx_session_expires', 'expires_at'),
        Index('idx_session_device', 'device_id'),
        CheckConstraint('expires_at > created_at', name='ck_session_expiry'),
    )

    @property
    def is_expired(self) -> bool:
        """Check if session is expired"""
        return datetime.now(timezone.utc) > self.expires_at

    @property
    def age_minutes(self) -> float:
        """Get session age in minutes"""
        return (datetime.now(timezone.utc) - self.created_at).total_seconds() / 60

    @property
    def idle_minutes(self) -> float:
        """Get session idle time in minutes"""
        return (datetime.now(timezone.utc) - self.last_activity).total_seconds() / 60

    def refresh(self, extend_minutes: int = 30):
        """Refresh session and extend expiry"""
        self.last_activity = datetime.now(timezone.utc)
        self.expires_at = datetime.now(timezone.utc) + timedelta(minutes=extend_minutes)

    def revoke(self):
        """Revoke session"""
        self.is_active = False

    def __repr__(self):
        return (
            f"<UserSession(id={self.id}, user_id={self.user_id}, "
            f"is_active={self.is_active}, expires_at={self.expires_at})>"
        )
