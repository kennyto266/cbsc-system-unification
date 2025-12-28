"""
Tag models for organizing context with hierarchical tagging system
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional, List, Dict, Any
import json

from config.database import Base


class Tag(Base):
    """Tag model for organizing contexts"""
    __tablename__ = "tags"

    id = Column(String(36), primary_key=True)  # UUID for tag ID
    name = Column(String(100), nullable=False, index=True)  # Tag name
    description = Column(Text, nullable=True)  # Tag description
    color = Column(String(7), nullable=True)  # Hex color code
    category = Column(String(50), nullable=True, index=True)  # Tag category
    parent_id = Column(String(36), ForeignKey("tags.id"), nullable=True)  # Parent tag for hierarchy
    extra_metadata = Column(JSON, nullable=True)  # Additional tag metadata
    is_active = Column(Boolean, nullable=False, default=True)  # Whether tag is active
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Relationships
    parent = relationship("Tag", remote_side=[id], back_populates="children")
    children = relationship("Tag", back_populates="parent")
    context_associations = relationship("ContextTagAssociation", back_populates="tag")
    suggestions = relationship("TagSuggestion", back_populates="tag")

    def __repr__(self):
        return f"<Tag(id='{self.id}', name='{self.name}', category='{self.category}')>"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "color": self.color,
            "category": self.category,
            "parent_id": self.parent_id,
            "extra_metadata": self.extra_metadata,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class ContextTagAssociation(Base):
    """Association between contexts and tags"""
    __tablename__ = "context_tag_associations"

    id = Column(String(36), primary_key=True)  # UUID for association ID
    context_id = Column(String(36), ForeignKey("contexts.id", ondelete="CASCADE"), nullable=False, index=True)
    tag_id = Column(String(36), ForeignKey("tags.id", ondelete="CASCADE"), nullable=False, index=True)
    confidence = Column(Float, nullable=True)  # Tag assignment confidence
    assigned_by = Column(String(100), nullable=True)  # Who assigned this tag
    assigned_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Relationships
    context = relationship("Context", back_populates="tag_associations")
    tag = relationship("Tag", back_populates="context_associations")

    def __repr__(self):
        return f"<ContextTagAssociation(context_id='{self.context_id}', tag_id='{self.tag_id}')>"


class TagSuggestion(Base):
    """Automatic tag suggestions for contexts"""
    __tablename__ = "tag_suggestions"

    id = Column(String(36), primary_key=True)  # UUID for suggestion ID
    context_id = Column(String(36), ForeignKey("contexts.id", ondelete="CASCADE"), nullable=False, index=True)
    tag_id = Column(String(36), ForeignKey("tags.id", ondelete="CASCADE"), nullable=False, index=True)
    confidence_score = Column(Float, nullable=False)  # Confidence score for suggestion
    reason = Column(Text, nullable=True)  # Reason for suggestion
    is_accepted = Column(Boolean, nullable=True)  # Whether suggestion was accepted
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    reviewed_at = Column(DateTime, nullable=True)  # When suggestion was reviewed

    # Relationships
    context = relationship("Context")
    tag = relationship("Tag", back_populates="suggestions")

    def __repr__(self):
        return f"<TagSuggestion(context_id='{self.context_id}', tag_id='{self.tag_id}', confidence={self.confidence_score})>"


class TagRule(Base):
    """Rules for automatic tag assignment"""
    __tablename__ = "tag_rules"

    id = Column(String(36), primary_key=True)  # UUID for rule ID
    name = Column(String(100), nullable=False)  # Rule name
    conditions = Column(JSON, nullable=False)  # Rule conditions as JSON
    target_tag_id = Column(String(36), ForeignKey("tags.id"), nullable=False)  # Tag to assign
    confidence_threshold = Column(Float, nullable=False, default=0.7)  # Minimum confidence
    is_active = Column(Boolean, nullable=False, default=True)  # Whether rule is active
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    target_tag = relationship("Tag")

    def __repr__(self):
        return f"<TagRule(id='{self.id}', name='{self.name}', target_tag_id='{self.target_tag_id}')>"


class TagStats(Base):
    """Usage statistics for tags"""
    __tablename__ = "tag_stats"

    tag_id = Column(String(36), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)
    usage_count = Column(Integer, nullable=False, default=0)  # Total usage count
    last_used = Column(DateTime, nullable=True)  # Last time tag was used
    context_types = Column(JSON, nullable=True)  # Usage by context type
    confidence_avg = Column(Float, nullable=True)  # Average confidence score
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tag = relationship("Tag")

    def __repr__(self):
        return f"<TagStats(tag_id='{self.tag_id}', usage_count={self.usage_count})>"