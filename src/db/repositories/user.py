"""
User Repositories

Repository classes for user and session data access.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any

from sqlalchemy import and_, or_, desc

from .base import BaseRepository
from ..models.user import User, UserSession

logger = logging.getLogger(__name__)


class UserRepository(BaseRepository[User]):
    """Repository for User model"""

    def __init__(self, session):
        super().__init__(session, User)

    def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return self.session.query(User).filter(
            User.username == username,
            User.is_deleted == False
        ).first()

    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.session.query(User).filter(
            User.email == email,
            User.is_deleted == False
        ).first()

    def get_active_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all active users"""
        return (
            self.session.query(User)
            .filter(
                and_(
                    User.is_active == True,
                    User.is_deleted == False
                )
            )
            .order_by(desc(User.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_role(
        self,
        role: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """Get users by role"""
        return (
            self.session.query(User)
            .filter(
                and_(
                    User.role == role,
                    User.is_deleted == False
                )
            )
            .order_by(desc(User.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def search_users(
        self,
        keyword: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """Search users by username, email, or full name"""
        return (
            self.session.query(User)
            .filter(
                and_(
                    User.is_deleted == False,
                    or_(
                        User.username.ilike(f"%{keyword}%"),
                        User.email.ilike(f"%{keyword}%"),
                        User.full_name.ilike(f"%{keyword}%")
                    )
                )
            )
            .order_by(desc(User.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_admins(self) -> List[User]:
        """Get all admin users"""
        return self.get_by_role("admin", limit=1000)

    def get_locked_users(self) -> List[User]:
        """Get all locked users"""
        now = datetime.now(timezone.utc)
        return (
            self.session.query(User)
            .filter(
                and_(
                    User.is_deleted == False,
                    User.locked_until > now
                )
            )
            .all()
        )

    def get_users_with_mfa(self) -> List[User]:
        """Get all users with MFA enabled"""
        return (
            self.session.query(User)
            .filter(
                and_(
                    User.mfa_enabled == True,
                    User.is_deleted == False
                )
            )
            .all()
        )

    def get_inactive_users(self, days: int = 30) -> List[User]:
        """Get users who haven't logged in for specified days"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        return (
            self.session.query(User)
            .filter(
                and_(
                    User.is_deleted == False,
                    or_(
                        User.last_login < cutoff_date,
                        User.last_login.is_(None)
                    )
                )
            )
            .all()
        )

    def create_user(self, user_data: Dict[str, Any]) -> User:
        """Create new user with defaults"""
        # Set default values if not provided
        user_data.setdefault("is_active", True)
        user_data.setdefault("email_verified", False)
        user_data.setdefault("role", "viewer")
        user_data.setdefault("login_count", 0)
        user_data.setdefault("failed_login_attempts", 0)

        return self.create(user_data)

    def authenticate(
        self,
        username: str,
        password_hash: str
    ) -> Optional[User]:
        """
        Verify user credentials (password hash comparison)

        Note: Actual password verification should happen at service layer
        """
        user = self.get_by_username(username)
        if user and user.password_hash == password_hash:
            if not user.is_locked:
                user.record_login()
                self.session.commit()
                return user
        return user

    def change_password(
        self,
        user_id: str,
        new_password_hash: str
    ) -> Optional[User]:
        """Change user password"""
        return self.update(user_id, {
            "password_hash": new_password_hash,
            "password_changed_at": datetime.now(timezone.utc)
        })

    def lock_user(self, user_id: str, lock_minutes: int = 30) -> Optional[User]:
        """Lock user account"""
        return self.update(user_id, {
            "locked_until": datetime.now(timezone.utc) + timedelta(minutes=lock_minutes)
        })

    def unlock_user(self, user_id: str) -> Optional[User]:
        """Unlock user account"""
        return self.update(user_id, {
            "locked_until": None,
            "failed_login_attempts": 0
        })

    def deactivate(self, user_id: str) -> Optional[User]:
        """Deactivate user account"""
        return self.update(user_id, {"is_active": False})

    def activate(self, user_id: str) -> Optional[User]:
        """Activate user account"""
        return self.update(user_id, {"is_active": True})

    def update_role(self, user_id: str, new_role: str) -> Optional[User]:
        """Update user role"""
        valid_roles = ["admin", "trader", "analyst", "viewer"]
        if new_role not in valid_roles:
            raise ValueError(f"Invalid role: {new_role}")
        return self.update(user_id, {"role": new_role})


class UserSessionRepository(BaseRepository[UserSession]):
    """Repository for UserSession model"""

    def __init__(self, session):
        super().__init__(session, UserSession)

    def get_by_session_id(self, session_id: str) -> Optional[UserSession]:
        """Get session by session ID"""
        return self.session.query(UserSession).filter(
            UserSession.session_id == session_id
        ).first()

    def get_by_user(
        self,
        user_id: str,
        active_only: bool = True
    ) -> List[UserSession]:
        """Get all sessions for a user"""
        query = self.session.query(UserSession).filter(
            UserSession.user_id == user_id
        )

        if active_only:
            now = datetime.now(timezone.utc)
            query = query.filter(
                and_(
                    UserSession.is_active == True,
                    UserSession.expires_at > now
                )
            )

        return query.order_by(desc(UserSession.created_at)).all()

    def get_active_sessions(self) -> List[UserSession]:
        """Get all active sessions"""
        now = datetime.now(timezone.utc)
        return (
            self.session.query(UserSession)
            .filter(
                and_(
                    UserSession.is_active == True,
                    UserSession.expires_at > now
                )
            )
            .order_by(desc(UserSession.last_activity))
            .all()
        )

    def get_expired_sessions(self) -> List[UserSession]:
        """Get all expired sessions"""
        now = datetime.now(timezone.utc)
        return (
            self.session.query(UserSession)
            .filter(
                UserSession.expires_at <= now
            )
            .all()
        )

    def get_by_device(self, device_id: str) -> List[UserSession]:
        """Get sessions by device ID"""
        return (
            self.session.query(UserSession)
            .filter(UserSession.device_id == device_id)
            .order_by(desc(UserSession.created_at))
            .all()
        )

    def get_by_ip(self, ip_address: str, limit: int = 100) -> List[UserSession]:
        """Get sessions by IP address"""
        return (
            self.session.query(UserSession)
            .filter(UserSession.ip_address == ip_address)
            .order_by(desc(UserSession.created_at))
            .limit(limit)
            .all()
        )

    def create_session(
        self,
        user_id: str,
        session_id: str,
        expires_minutes: int = 60,
        device_info: Dict[str, Any] = None
    ) -> UserSession:
        """Create new user session"""
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)

        session_data = {
            "user_id": user_id,
            "session_id": session_id,
            "expires_at": expires_at,
            "is_active": True
        }

        # Add device info if provided
        if device_info:
            session_data.update({
                "device_id": device_info.get("device_id"),
                "device_name": device_info.get("device_name"),
                "device_type": device_info.get("device_type"),
                "ip_address": device_info.get("ip_address"),
                "user_agent": device_info.get("user_agent"),
                "browser": device_info.get("browser"),
                "os": device_info.get("os")
            })

        return self.create(session_data)

    def refresh_session(
        self,
        session_id: str,
        extend_minutes: int = 30
    ) -> Optional[UserSession]:
        """Refresh session and extend expiry"""
        session = self.get_by_session_id(session_id)
        if session:
            session.refresh(extend_minutes)
            self.session.commit()
            self.session.refresh(session)
        return session

    def revoke_session(self, session_id: str) -> Optional[UserSession]:
        """Revoke a session"""
        session = self.get_by_session_id(session_id)
        if session:
            session.revoke()
            self.session.commit()
            self.session.refresh(session)
        return session

    def revoke_user_sessions(
        self,
        user_id: str,
        exclude_session_id: str = None
    ) -> int:
        """Revoke all sessions for a user"""
        query = self.session.query(UserSession).filter(
            and_(
                UserSession.user_id == user_id,
                UserSession.is_active == True
            )
        )

        if exclude_session_id:
            query = query.filter(UserSession.session_id != exclude_session_id)

        count = query.update({"is_active": False})
        self.session.commit()
        return count

    def revoke_all_sessions(self, user_id: str = None) -> int:
        """Revoke all active sessions (optionally for a user)"""
        query = self.session.query(UserSession).filter(
            UserSession.is_active == True
        )

        if user_id:
            query = query.filter(UserSession.user_id == user_id)

        count = query.update({"is_active": False})
        self.session.commit()
        return count

    def cleanup_expired_sessions(self) -> int:
        """Delete expired sessions older than 7 days"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=7)

        count = self.session.query(UserSession).filter(
            UserSession.expires_at < cutoff_date
        ).delete(synchronize_session=False)

        self.session.commit()
        logger.info(f"Cleaned up {count} expired sessions")
        return count

    def get_session_statistics(self) -> Dict[str, Any]:
        """Get session statistics"""
        now = datetime.now(timezone.utc)

        total_sessions = self.session.query(UserSession).count()
        active_sessions = self.session.query(UserSession).filter(
            and_(
                UserSession.is_active == True,
                UserSession.expires_at > now
            )
        ).count()
        expired_sessions = self.session.query(UserSession).filter(
            UserSession.expires_at <= now
        ).count()

        # Get unique devices
        unique_devices = self.session.query(UserSession.device_id).distinct().count()

        # Get unique users
        unique_users = self.session.query(UserSession.user_id).distinct().count()

        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "expired_sessions": expired_sessions,
            "unique_devices": unique_devices,
            "unique_users": unique_users
        }
