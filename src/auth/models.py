"""
Authentication Database Models
Based on unified database schema with enhanced security features
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column, String, Boolean, Integer, DateTime, Text, ForeignKey,
    Index, CheckConstraint, UniqueConstraint, JSON, Float
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Session
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

class User(Base):
    """Enhanced User model with comprehensive security features"""
    __tablename__ = "users"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Basic information
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    # Profile information
    first_name = Column(String(100))
    last_name = Column(String(100))
    display_name = Column(String(200))
    avatar_url = Column(String(500))
    phone = Column(String(20))

    # Status flags
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_premium = Column(Boolean, default=False, nullable=False)

    # Security features
    mfa_enabled = Column(Boolean, default=False, nullable=False)
    mfa_secret = Column(String(32))
    mfa_backup_codes = Column(JSONB)  # Store backup codes
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(TIMESTAMP(timezone=True))
    password_changed_at = Column(TIMESTAMP(timezone=True), default=func.now())
    email_verified_at = Column(TIMESTAMP(timezone=True))

    # Session tracking
    last_login_at = Column(TIMESTAMP(timezone=True))
    last_login_ip = Column(String(45))
    last_device_used = Column(String(100))

    # Preferences
    timezone = Column(String(50), default='UTC', nullable=False)
    language = Column(String(10), default='en', nullable=False)
    theme = Column(String(20), default='light', nullable=False)
    notifications = Column(JSONB)  # User notification preferences

    # Audit fields
    created_at = Column(TIMESTAMP(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    updated_by = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(TIMESTAMP(timezone=True))
    deleted_by = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    version = Column(Integer, default=1, nullable=False)

    # Additional fields
    metadata = Column(JSONB)
    notes = Column(Text)

    # Relationships
    roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    devices = relationship("UserDevice", back_populates="user", cascade="all, delete-orphan")
    login_history = relationship("LoginHistory", back_populates="user", cascade="all, delete-orphan")
    password_history = relationship("PasswordHistory", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")

    # Self-referential relationships
    created_by_user = relationship("User", foreign_keys=[created_by], remote_side=[id])
    updated_by_user = relationship("User", foreign_keys=[updated_by], remote_side=[id])
    deleted_by_user = relationship("User", foreign_keys=[deleted_by], remote_side=[id])

    # Constraints
    __table_args__ = (
        Index('idx_users_active_deleted', 'is_active', 'is_deleted'),
        Index('idx_users_last_login', 'last_login_at'),
        CheckConstraint('failed_login_attempts >= 0', name='check_failed_attempts'),
        CheckConstraint('version > 0', name='check_version_positive'),
    )

    @property
    def full_name(self) -> Optional[str]:
        """Get user's full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.display_name or self.username

    @property
    def is_locked(self) -> bool:
        """Check if user account is locked"""
        if self.locked_until:
            return datetime.utcnow() < self.locked_until.replace(tzinfo=None)
        return False

    @property
    def permissions(self) -> List[str]:
        """Get all user permissions through roles"""
        permissions = set()
        for user_role in self.roles:
            if user_role.is_active and (not user_role.expires_at or user_role.expires_at > datetime.utcnow()):
                for role_permission in user_role.role.permissions:
                    if role_permission.permission.is_active:
                        permissions.add(role_permission.permission.code)
        return list(permissions)

    @property
    def role_names(self) -> List[str]:
        """Get all user role names"""
        roles = []
        for user_role in self.roles:
            if user_role.is_active and (not user_role.expires_at or user_role.expires_at > datetime.utcnow()):
                roles.append(user_role.role.name)
        return roles


class Role(Base):
    """Role model for RBAC"""
    __tablename__ = "roles"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Basic information
    name = Column(String(50), unique=True, nullable=False)
    display_name = Column(String(200), nullable=False)
    description = Column(Text)

    # Status and hierarchy
    is_active = Column(Boolean, default=True, nullable=False)
    is_system_role = Column(Boolean, default=False, nullable=False)
    level = Column(Integer, default=0, nullable=False)  # Hierarchy level

    # Audit fields
    created_at = Column(TIMESTAMP(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    updated_by = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(TIMESTAMP(timezone=True))
    deleted_by = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    version = Column(Integer, default=1, nullable=False)

    # Additional fields
    metadata = Column(JSONB)
    notes = Column(Text)

    # Relationships
    users = relationship("UserRole", back_populates="role", cascade="all, delete-orphan")
    permissions = relationship("RolePermission", back_populates="role", cascade="all, delete-orphan")

    # Self-referential relationships
    created_by_user = relationship("User", foreign_keys=[created_by], remote_side=[id])
    updated_by_user = relationship("User", foreign_keys=[updated_by], remote_side=[id])
    deleted_by_user = relationship("User", foreign_keys=[deleted_by], remote_side=[id])

    # Constraints
    __table_args__ = (
        CheckConstraint('level >= 0', name='check_role_level'),
        CheckConstraint('version > 0', name='check_role_version'),
    )


class Permission(Base):
    """Permission model for fine-grained access control"""
    __tablename__ = "permissions"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Permission identification
    code = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)

    # Permission categorization
    category = Column(String(50), nullable=False)  # e.g., user, strategy, portfolio
    resource = Column(String(50), nullable=False)  # e.g., user, strategy
    action = Column(String(50), nullable=False)    # e.g., create, read, update, delete

    # Hierarchy and status
    level = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_system_permission = Column(Boolean, default=False, nullable=False)

    # Audit fields
    created_at = Column(TIMESTAMP(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    updated_by = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(TIMESTAMP(timezone=True))
    deleted_by = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    version = Column(Integer, default=1, nullable=False)

    # Additional fields
    metadata = Column(JSONB)
    notes = Column(Text)

    # Relationships
    roles = relationship("RolePermission", back_populates="permission", cascade="all, delete-orphan")

    # Self-referential relationships
    created_by_user = relationship("User", foreign_keys=[created_by], remote_side=[id])
    updated_by_user = relationship("User", foreign_keys=[updated_by], remote_side=[id])
    deleted_by_user = relationship("User", foreign_keys=[deleted_by], remote_side=[id])

    # Constraints
    __table_args__ = (
        Index('idx_permissions_category', 'category', 'resource', 'action'),
        CheckConstraint('level >= 0', name='check_permission_level'),
        CheckConstraint('version > 0', name='check_permission_version'),
    )


class UserRole(Base):
    """Many-to-many relationship between users and roles"""
    __tablename__ = "user_roles"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    role_id = Column(UUID(as_uuid=True), ForeignKey('roles.id'), nullable=False)

    # Assignment details
    assigned_by = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    assigned_at = Column(TIMESTAMP(timezone=True), default=func.now(), nullable=False)
    expires_at = Column(TIMESTAMP(timezone=True))  # Optional expiry
    is_active = Column(Boolean, default=True, nullable=False)

    # Additional fields
    notes = Column(Text)

    # Audit fields
    created_at = Column(TIMESTAMP(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    updated_by = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(TIMESTAMP(timezone=True))
    deleted_by = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    version = Column(Integer, default=1, nullable=False)

    # Metadata
    metadata = Column(JSONB)

    # Relationships
    user = relationship("User", back_populates="roles")
    role = relationship("Role", back_populates="users")

    # Self-referential relationships
    assigned_by_user = relationship("User", foreign_keys=[assigned_by], remote_side=[id])
    created_by_user = relationship("User", foreign_keys=[created_by], remote_side=[id])
    updated_by_user = relationship("User", foreign_keys=[updated_by], remote_side=[id])
    deleted_by_user = relationship("User", foreign_keys=[deleted_by], remote_side=[id])

    # Constraints
    __table_args__ = (
        PrimaryKeyConstraint('user_id', 'role_id'),
        CheckConstraint('version > 0', name='check_user_role_version'),
    )


class RolePermission(Base):
    """Many-to-many relationship between roles and permissions"""
    __tablename__ = "role_permissions"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    role_id = Column(UUID(as_uuid=True), ForeignKey('roles.id'), nullable=False)
    permission_id = Column(UUID(as_uuid=True), ForeignKey('permissions.id'), nullable=False)

    # Grant details
    granted_by = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    granted_at = Column(TIMESTAMP(timezone=True), default=func.now(), nullable=False)

    # Audit fields
    created_at = Column(TIMESTAMP(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    updated_by = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(TIMESTAMP(timezone=True))
    deleted_by = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    version = Column(Integer, default=1, nullable=False)

    # Metadata
    metadata = Column(JSONB)

    # Relationships
    role = relationship("Role", back_populates="permissions")
    permission = relationship("Permission", back_populates="roles")

    # Self-referential relationships
    granted_by_user = relationship("User", foreign_keys=[granted_by], remote_side=[id])
    created_by_user = relationship("User", foreign_keys=[created_by], remote_side=[id])
    updated_by_user = relationship("User", foreign_keys=[updated_by], remote_side=[id])
    deleted_by_user = relationship("User", foreign_keys=[deleted_by], remote_side=[id])

    # Constraints
    __table_args__ = (
        PrimaryKeyConstraint('role_id', 'permission_id'),
        CheckConstraint('version > 0', name='check_role_permission_version'),
    )


class UserSession(Base):
    """User session management for tracking active sessions"""
    __tablename__ = "user_sessions"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Session information
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    refresh_token = Column(String(255), unique=True, nullable=False)

    # Device and location
    device_id = Column(UUID(as_uuid=True), ForeignKey('user_devices.id'))
    ip_address = Column(String(45))
    user_agent = Column(Text)
    location = Column(String(100))

    # Session lifecycle
    created_at = Column(TIMESTAMP(timezone=True), default=func.now(), nullable=False)
    last_accessed_at = Column(TIMESTAMP(timezone=True), default=func.now(), nullable=False)
    expires_at = Column(TIMESTAMP(timezone=True), nullable=False)
    revoked_at = Column(TIMESTAMP(timezone=True))
    is_active = Column(Boolean, default=True, nullable=False)

    # Security flags
    is_trusted = Column(Boolean, default=False)
    mfa_verified = Column(Boolean, default=False)

    # Relationships
    user = relationship("User", back_populates="sessions")
    device = relationship("UserDevice")

    # Constraints
    __table_args__ = (
        Index('idx_sessions_user_active', 'user_id', 'is_active'),
        Index('idx_sessions_token', 'session_token'),
        Index('idx_sessions_expires', 'expires_at'),
    )


class UserDevice(Base):
    """User device tracking for security"""
    __tablename__ = "user_devices"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Device information
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    device_name = Column(String(100), nullable=False)
    device_type = Column(String(50))  # desktop, mobile, tablet
    device_fingerprint = Column(String(255))  # Unique device identifier
    platform = Column(String(50))  # iOS, Android, Windows, macOS, Linux
    browser = Column(String(50))
    browser_version = Column(String(20))

    # Network information
    last_ip = Column(String(45))
    last_location = Column(String(100))

    # Usage tracking
    first_seen_at = Column(TIMESTAMP(timezone=True), default=func.now(), nullable=False)
    last_seen_at = Column(TIMESTAMP(timezone=True), default=func.now(), nullable=False)
    usage_count = Column(Integer, default=0, nullable=False)

    # Security flags
    is_trusted = Column(Boolean, default=False)
    is_blocked = Column(Boolean, default=False)
    blocked_reason = Column(String(100))

    # Relationships
    user = relationship("User", back_populates="devices")
    sessions = relationship("UserSession", backref="user_device")

    # Constraints
    __table_args__ = (
        Index('idx_devices_user', 'user_id'),
        Index('idx_devices_fingerprint', 'device_fingerprint'),
        UniqueConstraint('user_id', 'device_fingerprint', name='unique_user_device_fingerprint'),
        CheckConstraint('usage_count >= 0', name='check_usage_count'),
    )


class LoginHistory(Base):
    """Login history for audit and security monitoring"""
    __tablename__ = "login_history"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Login attempt information
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    username = Column(String(50))  # Store username even if user doesn't exist
    ip_address = Column(String(45))
    user_agent = Column(Text)
    device_info = Column(JSONB)
    location = Column(String(100))

    # Attempt details
    success = Column(Boolean, default=True, nullable=False)
    failure_reason = Column(String(100))
    login_method = Column(String(20), default='password')  # password, oauth, sso

    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), default=func.now(), nullable=False)

    # Additional data
    metadata = Column(JSONB)

    # Relationships
    user = relationship("User", back_populates="login_history")

    # Constraints
    __table_args__ = (
        Index('idx_login_history_user', 'user_id'),
        Index('idx_login_history_created', 'created_at'),
        Index('idx_login_history_ip', 'ip_address'),
    )


class PasswordHistory(Base):
    """Password history for preventing reuse"""
    __tablename__ = "password_history"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Password information
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    password_hash = Column(String(255), nullable=False)

    # Change details
    changed_at = Column(TIMESTAMP(timezone=True), default=func.now(), nullable=False)
    changed_by = Column(UUID(as_uuid=True), ForeignKey('users.id'))  # Self or admin
    change_method = Column(String(20))  # self, admin, reset
    ip_address = Column(String(45))

    # Relationships
    user = relationship("User", back_populates="password_history")

    # Constraints
    __table_args__ = (
        Index('idx_password_history_user', 'user_id'),
        Index('idx_password_history_date', 'user_id', 'changed_at'),
    )


class AuditLog(Base):
    """Comprehensive audit logging for security compliance"""
    __tablename__ = "audit_logs"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Action information
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    action = Column(String(100), nullable=False)  # login, logout, create, update, delete
    resource_type = Column(String(50))  # user, role, permission, strategy
    resource_id = Column(UUID(as_uuid=True))

    # Request details
    endpoint = Column(String(255))
    method = Column(String(10))
    ip_address = Column(String(45))
    user_agent = Column(Text)

    # Result details
    status = Column(String(20))  # success, failure, error
    status_code = Column(Integer)
    error_message = Column(Text)

    # Data changes (for audit)
    old_values = Column(JSONB)
    new_values = Column(JSONB)
    sensitive_fields = Column(JSONB)  # List of fields that were masked

    # Metadata
    session_id = Column(UUID(as_uuid=True))
    request_id = Column(String(100))  # For request tracing
    correlation_id = Column(String(100))  # For cross-service tracing

    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), default=func.now(), nullable=False)

    # Additional data
    metadata = Column(JSONB)

    # Relationships
    user = relationship("User", back_populates="audit_logs")

    # Constraints
    __table_args__ = (
        Index('idx_audit_user', 'user_id'),
        Index('idx_audit_created', 'created_at'),
        Index('idx_audit_action', 'action'),
        Index('idx_audit_resource', 'resource_type', 'resource_id'),
        Index('idx_audit_status', 'status'),
    )