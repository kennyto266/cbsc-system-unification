"""
Context metadata models for persistent storage
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional, List, Dict, Any
import json
from config.database import Base


class Context(Base):
    """Context metadata model for storing AI-assisted development context"""
    __tablename__ = "contexts"

    id = Column(String(36), primary_key=True)  # UUID for context ID
    title = Column(String(255), nullable=False)  # Context title
    description = Column(Text, nullable=True)  # Context description
    content_hash = Column(String(64), nullable=False, index=True)  # Hash of compressed content
    file_path = Column(String(500), nullable=False)  # Path to compressed file
    file_size = Column(Integer, nullable=False)  # Compressed file size in bytes
    original_size = Column(Integer, nullable=False)  # Original uncompressed size
    compression_ratio = Column(Float, nullable=False)  # Compression ratio achieved

    # Metadata
    user_id = Column(String(100), nullable=False, index=True)  # User who owns this context
    session_id = Column(String(100), nullable=True, index=True)  # Session identifier
    project_path = Column(String(500), nullable=True, index=True)  # Project root directory

    # Visibility and sharing
    visibility = Column(String(20), nullable=False, default="private")  # private, team, public
    auto_save_enabled = Column(Boolean, nullable=False, default=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    last_accessed_at = Column(DateTime, nullable=True, index=True)

    # Relationships
    tags = relationship("ContextTag", back_populates="context", cascade="all, delete-orphan")
    tag_associations = relationship("ContextTagAssociation", back_populates="context", cascade="all, delete-orphan")
    shares = relationship("ContextShare", back_populates="context", cascade="all, delete-orphan")
    access_records = relationship("ContextAccess", back_populates="context", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Context(id='{self.id}', title='{self.title}', user_id='{self.user_id}')>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "content_hash": self.content_hash,
            "file_size": self.file_size,
            "original_size": self.original_size,
            "compression_ratio": self.compression_ratio,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "project_path": self.project_path,
            "visibility": self.visibility,
            "auto_save_enabled": self.auto_save_enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_accessed_at": self.last_accessed_at.isoformat() if self.last_accessed_at else None,
            "tags": [tag.to_dict() for tag in self.tags] if self.tags else [],
            "shares": [share.to_dict() for share in self.shares] if self.shares else []
        }


class ContextTag(Base):
    """Tags for organizing and searching contexts"""
    __tablename__ = "context_tags"

    id = Column(Integer, primary_key=True, autoincrement=True)
    context_id = Column(String(36), ForeignKey("contexts.id", ondelete="CASCADE"), nullable=False)
    tag_name = Column(String(50), nullable=False, index=True)
    tag_value = Column(String(100), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    context = relationship("Context", back_populates="tags")

    def __repr__(self):
        return f"<ContextTag(context_id='{self.context_id}', tag='{self.tag_name}')>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "context_id": self.context_id,
            "tag_name": self.tag_name,
            "tag_value": self.tag_value,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class ContextShare(Base):
    """Shared context records for team collaboration"""
    __tablename__ = "context_shares"

    id = Column(String(36), primary_key=True)  # UUID for share ID
    context_id = Column(String(36), ForeignKey("contexts.id", ondelete="CASCADE"), nullable=False)
    shared_by_user_id = Column(String(100), nullable=False, index=True)
    shared_with_user_id = Column(String(100), nullable=True, index=True)  # Null for public shares
    share_token = Column(String(64), nullable=True, unique=True, index=True)  # For share links

    # Permissions
    permission_level = Column(String(20), nullable=False, default="viewer")  # viewer, editor, owner
    can_edit = Column(Boolean, nullable=False, default=False)
    can_share = Column(Boolean, nullable=False, default=False)
    can_delete = Column(Boolean, nullable=False, default=False)

    # Share settings
    expires_at = Column(DateTime, nullable=True)  # Share expiration
    is_active = Column(Boolean, nullable=False, default=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_accessed_at = Column(DateTime, nullable=True)

    # Relationships
    context = relationship("Context", back_populates="shares")

    def __repr__(self):
        return f"<ContextShare(id='{self.id}', context_id='{self.context_id}', permission='{self.permission_level}')>"

    def is_expired(self) -> bool:
        """Check if share has expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "context_id": self.context_id,
            "shared_by_user_id": self.shared_by_user_id,
            "shared_with_user_id": self.shared_with_user_id,
            "share_token": self.share_token,
            "permission_level": self.permission_level,
            "can_edit": self.can_edit,
            "can_share": self.can_share,
            "can_delete": self.can_delete,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_accessed_at": self.last_accessed_at.isoformat() if self.last_accessed_at else None,
            "is_expired": self.is_expired()
        }


class ContextAccess(Base):
    """Access log for tracking context usage"""
    __tablename__ = "context_access"

    id = Column(Integer, primary_key=True, autoincrement=True)
    context_id = Column(String(36), ForeignKey("contexts.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(100), nullable=False, index=True)
    access_type = Column(String(20), nullable=False)  # view, edit, download, share
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(Text, nullable=True)
    session_id = Column(String(100), nullable=True)

    # Timestamps
    accessed_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Relationships
    context = relationship("Context", back_populates="access_records")

    def __repr__(self):
        return f"<ContextAccess(context_id='{self.context_id}', user_id='{self.user_id}', action='{self.access_type}')>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "context_id": self.context_id,
            "user_id": self.user_id,
            "access_type": self.access_type,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "session_id": self.session_id,
            "accessed_at": self.accessed_at.isoformat() if self.accessed_at else None
        }