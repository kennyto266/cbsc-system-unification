"""
User and permission models for team access control
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional, List, Dict, Any
import json
from config.database import Base

# Association table for many-to-many relationship between users and teams
user_teams = Table(
    'user_team_associations',
    Base.metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('user_id', String(100), ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
    Column('team_id', String(100), ForeignKey('teams.id', ondelete='CASCADE'), nullable=False),
    Column('role', String(20), nullable=False, default='member'),  # owner, admin, member
    Column('joined_at', DateTime, nullable=False, default=datetime.utcnow),
    Column('created_at', DateTime, nullable=False, default=datetime.utcnow),
    Column('updated_at', DateTime, nullable=False, default=datetime.utcnow)
)


class User(Base):
    """User model for authentication and user management"""
    __tablename__ = "users"

    id = Column(String(100), primary_key=True)  # User ID from authentication system
    username = Column(String(50), nullable=False, unique=True, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    full_name = Column(String(100), nullable=True)
    avatar_url = Column(String(500), nullable=True)

    # User status and roles
    is_active = Column(Boolean, nullable=False, default=True)
    is_verified = Column(Boolean, nullable=False, default=False)
    role = Column(String(20), nullable=False, default="user")  # user, admin, super_admin

    # User preferences
    preferences = Column(Text, nullable=True)  # JSON string for user preferences
    timezone = Column(String(50), nullable=False, default="UTC")

    # Metadata
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    teams = relationship("Team", secondary=user_teams, back_populates="members")
    owned_teams = relationship("Team", back_populates="owner")
    permissions = relationship("Permission", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id='{self.id}', username='{self.username}', email='{self.email}')>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "avatar_url": self.avatar_url,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "role": self.role,
            "preferences": json.loads(self.preferences) if self.preferences else {},
            "timezone": self.timezone,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def get_preferences(self) -> Dict[str, Any]:
        """Get user preferences as dictionary"""
        try:
            return json.loads(self.preferences) if self.preferences else {}
        except (json.JSONDecodeError, TypeError):
            return {}

    def set_preferences(self, preferences: Dict[str, Any]) -> None:
        """Set user preferences from dictionary"""
        self.preferences = json.dumps(preferences)

    def is_team_member(self, team_id: str) -> bool:
        """Check if user is a member of a team"""
        return any(team.id == team_id for team in self.teams)

    def get_team_role(self, team_id: str) -> Optional[str]:
        """Get user's role in a specific team"""
        for team in self.teams:
            if team.id == team_id:
                # Get the role from the association table
                for assoc in team.user_associations:
                    if assoc.user_id == self.id:
                        return assoc.role
        return None


class Team(Base):
    """Team model for organizing users and shared contexts"""
    __tablename__ = "teams"

    id = Column(String(100), primary_key=True)  # Team ID
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    avatar_url = Column(String(500), nullable=True)

    # Team settings
    is_active = Column(Boolean, nullable=False, default=True)
    is_public = Column(Boolean, nullable=False, default=False)  # Public teams are discoverable
    max_members = Column(Integer, nullable=True)  # Null for unlimited

    # Owner and management
    owner_id = Column(String(100), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    owner = relationship("User", back_populates="owned_teams")
    members = relationship("User", secondary=user_teams, back_populates="teams")
    user_associations = relationship("UserTeamAssociation", back_populates="team", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Team(id='{self.id}', name='{self.name}', owner_id='{self.owner_id}')>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "avatar_url": self.avatar_url,
            "is_active": self.is_active,
            "is_public": self.is_public,
            "max_members": self.max_members,
            "owner_id": self.owner_id,
            "member_count": len(self.members) if self.members else 0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def get_member_count(self) -> int:
        """Get the current number of members"""
        return len(self.members) if self.members else 0

    def can_add_member(self) -> bool:
        """Check if team can accept more members"""
        if not self.max_members:
            return True
        return self.get_member_count() < self.max_members


class UserTeamAssociation(Base):
    """Association model for user-team relationships with additional metadata"""
    __tablename__ = "user_team_association_details"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(100), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    team_id = Column(String(100), ForeignKey('teams.id', ondelete='CASCADE'), nullable=False)

    # Role and permissions
    role = Column(String(20), nullable=False, default='member')  # owner, admin, member
    permissions = Column(Text, nullable=True)  # JSON string for additional permissions

    # Status and metadata
    is_active = Column(Boolean, nullable=False, default=True)
    invited_by_user_id = Column(String(100), nullable=True)  # Who invited this user
    joined_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_active_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    user = relationship("User")
    team = relationship("Team", back_populates="user_associations")

    def __repr__(self):
        return f"<UserTeamAssociation(user_id='{self.user_id}', team_id='{self.team_id}', role='{self.role}')>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "team_id": self.team_id,
            "role": self.role,
            "permissions": json.loads(self.permissions) if self.permissions else {},
            "is_active": self.is_active,
            "invited_by_user_id": self.invited_by_user_id,
            "joined_at": self.joined_at.isoformat() if self.joined_at else None,
            "last_active_at": self.last_active_at.isoformat() if self.last_active_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def get_permissions(self) -> Dict[str, Any]:
        """Get additional permissions as dictionary"""
        try:
            return json.loads(self.permissions) if self.permissions else {}
        except (json.JSONDecodeError, TypeError):
            return {}

    def set_permissions(self, permissions: Dict[str, Any]) -> None:
        """Set additional permissions from dictionary"""
        self.permissions = json.dumps(permissions)

    def can_manage_team(self) -> bool:
        """Check if user can manage the team (owner or admin)"""
        return self.role in ['owner', 'admin']

    def can_invite_members(self) -> bool:
        """Check if user can invite new members"""
        return self.role in ['owner', 'admin']


class Permission(Base):
    """Permission model for granular access control"""
    __tablename__ = "permissions"

    id = Column(String(100), primary_key=True)  # Permission ID
    user_id = Column(String(100), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    resource_type = Column(String(50), nullable=False, index=True)  # context, team, etc.
    resource_id = Column(String(100), nullable=False, index=True)  # ID of the resource

    # Permission details
    permission_type = Column(String(50), nullable=False)  # view, edit, delete, share, manage
    granted_by_user_id = Column(String(100), nullable=False)  # Who granted this permission
    scope = Column(String(20), nullable=False, default="specific")  # specific, team, global

    # Permission constraints
    conditions = Column(Text, nullable=True)  # JSON string for conditional permissions
    expires_at = Column(DateTime, nullable=True)  # Permission expiration

    # Status and metadata
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    granted_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="permissions")

    def __repr__(self):
        return f"<Permission(id='{self.id}', user_id='{self.user_id}', resource='{self.resource_type}:{self.resource_id}', type='{self.permission_type}')>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "permission_type": self.permission_type,
            "granted_by_user_id": self.granted_by_user_id,
            "scope": self.scope,
            "conditions": json.loads(self.conditions) if self.conditions else {},
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "granted_at": self.granted_at.isoformat() if self.granted_at else None,
            "is_expired": self.is_expired()
        }

    def is_expired(self) -> bool:
        """Check if permission has expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at

    def get_conditions(self) -> Dict[str, Any]:
        """Get permission conditions as dictionary"""
        try:
            return json.loads(self.conditions) if self.conditions else {}
        except (json.JSONDecodeError, TypeError):
            return {}

    def set_conditions(self, conditions: Dict[str, Any]) -> None:
        """Set permission conditions from dictionary"""
        self.conditions = json.dumps(conditions)

    def is_valid(self) -> bool:
        """Check if permission is currently valid"""
        return self.is_active and not self.is_expired()