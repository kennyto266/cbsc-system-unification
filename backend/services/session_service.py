"""
User Session and Device Management Service
Tracks user sessions, devices, and provides session management capabilities.
"""

import secrets
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum

try:
    from models.unified_models import User, MfaDevice, UserActivity
    from config.api_config import settings
except ImportError:
    # Fallback types
    class settings:
        SESSION_EXPIRE_MINUTES = 60
        REFRESH_TOKEN_EXPIRE_DAYS = 7
        MAX_SESSIONS_PER_USER = 5
        DEVICE_TRACKING_ENABLED = True

logger = logging.getLogger(__name__)


class DeviceType(str, Enum):
    """Device type enumeration"""
    DESKTOP = "desktop"
    MOBILE = "mobile"
    TABLET = "tablet"
    UNKNOWN = "unknown"


class OSFamily(str, Enum):
    """Operating system family"""
    WINDOWS = "windows"
    MACOS = "macos"
    LINUX = "linux"
    ANDROID = "android"
    IOS = "ios"
    UNKNOWN = "unknown"


@dataclass
class DeviceInfo:
    """Device information"""
    user_agent: str
    device_type: DeviceType
    os_family: OSFamily
    browser: str
    ip_address: str
    is_trusted: bool = False
    last_seen: datetime = field(default_factory=datetime.utcnow)


@dataclass
class UserSession:
    """User session data"""
    session_id: str
    user_id: int
    device_info: DeviceInfo
    created_at: datetime
    last_activity: datetime
    expires_at: datetime
    refresh_token: str
    is_active: bool = True


@dataclass
class LoginAttempt:
    """Login attempt tracking"""
    ip_address: str
    username: str
    timestamp: datetime
    success: bool
    device_info: DeviceInfo
    failure_reason: Optional[str] = None


class SessionManager:
    """
    User session and device management service.
    """

    def __init__(self):
        # In-memory storage (use Redis in production)
        self._sessions: Dict[str, UserSession] = {}
        self._user_sessions: Dict[int, List[str]] = {}  # user_id -> [session_ids]
        self._devices: Dict[int, List[DeviceInfo]] = {}  # user_id -> [devices]
        self._login_attempts: Dict[str, List[LoginAttempt]] = {}  # ip -> [attempts]

    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        return secrets.token_urlsafe(32)

    def _parse_user_agent(self, user_agent: str) -> DeviceInfo:
        """Parse user agent string to extract device information"""
        # Basic user agent parsing
        device_type = DeviceType.UNKNOWN
        os_family = OSFamily.UNKNOWN
        browser = "Unknown"

        ua_lower = user_agent.lower()

        # Detect OS
        if "windows" in ua_lower:
            os_family = OSFamily.WINDOWS
        elif "mac os x" in ua_lower or "macintosh" in ua_lower:
            os_family = OSFamily.MACOS
        elif "linux" in ua_lower:
            os_family = OSFamily.LINUX
        elif "android" in ua_lower:
            os_family = OSFamily.ANDROID
            device_type = DeviceType.MOBILE
        elif "iphone" in ua_lower or "ipad" in ua_lower:
            os_family = OSFamily.IOS
            device_type = DeviceType.MOBILE if "iphone" in ua_lower else DeviceType.TABLET

        # Detect device type
        if "mobile" in ua_lower:
            device_type = DeviceType.MOBILE
        elif "tablet" in ua_lower or "ipad" in ua_lower:
            device_type = DeviceType.TABLET
        elif device_type == DeviceType.UNKNOWN:
            device_type = DeviceType.DESKTOP

        # Detect browser
        if "chrome" in ua_lower:
            browser = "Chrome"
        elif "firefox" in ua_lower:
            browser = "Firefox"
        elif "safari" in ua_lower and "chrome" not in ua_lower:
            browser = "Safari"
        elif "edge" in ua_lower:
            browser = "Edge"
        elif "opera" in ua_lower:
            browser = "Opera"

        return DeviceInfo(
            user_agent=user_agent,
            device_type=device_type,
            os_family=os_family,
            browser=browser,
            ip_address="",  # Will be filled by caller
            is_trusted=False
        )

    def _detect_suspicious_activity(
        self,
        user_id: int,
        device_info: DeviceInfo
    ) -> tuple[bool, Optional[str]]:
        """
        Detect suspicious login activity.

        Returns:
            (is_suspicious, reason)
        """
        # Check for new device from unusual location
        user_devices = self._devices.get(user_id, [])

        if user_devices:
            # Check if device is known
            device_hash = self._hash_device(device_info)
            for known_device in user_devices:
                known_hash = self._hash_device(known_device)
                if device_hash == known_hash:
                    return False, None  # Known device, not suspicious

            # New device from existing user
            return True, "New device detected for your account. Please verify."

        return False, None

    def _hash_device(self, device_info: DeviceInfo) -> str:
        """Create device fingerprint hash"""
        device_str = f"{device_info.os_family.value}:{device_info.browser}:{device_info.device_type.value}"
        return hashlib.sha256(device_str.encode()).hexdigest()

    async def create_session(
        self,
        user_id: int,
        ip_address: str,
        user_agent: str,
        remember_me: bool = False
    ) -> Dict[str, Any]:
        """
        Create new user session.

        Args:
            user_id: User ID
            ip_address: Client IP address
            user_agent: User agent string
            remember_me: Whether to extend session

        Returns:
            Session data with tokens
        """
        try:
            # Parse device info
            device_info = self._parse_user_agent(user_agent)
            device_info.ip_address = ip_address

            # Check for suspicious activity
            is_suspicious, reason = self._detect_suspicious_activity(user_id, device_info)

            # Generate session ID and tokens
            session_id = self._generate_session_id()
            access_token = self._generate_session_id()
            refresh_token = self._generate_session_id()

            # Calculate expiry
            now = datetime.utcnow()
            expires_at = now + timedelta(minutes=settings.SESSION_EXPIRE_MINUTES)

            if remember_me:
                expires_at = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

            # Create session
            session = UserSession(
                session_id=session_id,
                user_id=user_id,
                device_info=device_info,
                created_at=now,
                last_activity=now,
                expires_at=expires_at,
                refresh_token=refresh_token
            )

            # Store session
            self._sessions[session_id] = session

            # Track user sessions
            if user_id not in self._user_sessions:
                self._user_sessions[user_id] = []

            self._user_sessions[user_id].append(session_id)

            # Enforce max sessions limit
            if len(self._user_sessions[user_id]) > settings.MAX_SESSIONS_PER_USER:
                # Remove oldest session
                oldest_session_id = self._user_sessions[user_id][0]
                await self.revoke_session(user_id, oldest_session_id)

            # Track device
            if user_id not in self._devices:
                self._devices[user_id] = []

            # Check if device already tracked
            device_hash = self._hash_device(device_info)
            device_exists = False
            for tracked_device in self._devices[user_id]:
                if self._hash_device(tracked_device) == device_hash:
                    tracked_device.last_seen = now
                    device_exists = True
                    break

            if not device_exists:
                self._devices[user_id].append(device_info)

            # Log activity
            await self._log_activity(
                user_id=user_id,
                action="session_created",
                ip_address=ip_address,
                user_agent=user_agent,
                metadata={
                    "session_id": session_id,
                    "device_type": device_info.device_type.value,
                    "os_family": device_info.os_family.value,
                    "browser": device_info.browser
                }
            )

            logger.info(f"Session created for user_id {user_id}: {session_id}")

            return {
                "success": True,
                "data": {
                    "session_id": session_id,
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "expires_at": expires_at.isoformat(),
                    "device_info": {
                        "device_type": device_info.device_type.value,
                        "os_family": device_info.os_family.value,
                        "browser": device_info.browser
                    },
                    "is_suspicious": is_suspicious,
                    "suspicious_reason": reason
                }
            }

        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            return {
                "success": False,
                "error": {
                    "code": "SESSION_CREATE_FAILED",
                    "message": "Failed to create session"
                }
            }

    async def get_session(self, session_id: str) -> Optional[UserSession]:
        """Get session by ID"""
        session = self._sessions.get(session_id)

        if not session:
            return None

        # Check if expired
        if datetime.utcnow() > session.expires_at:
            await self.revoke_session(session.user_id, session_id)
            return None

        # Update last activity
        session.last_activity = datetime.utcnow()

        return session

    async def get_user_sessions(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all active sessions for user"""
        session_ids = self._user_sessions.get(user_id, [])

        sessions = []
        for session_id in session_ids:
            session = await self.get_session(session_id)
            if session:
                sessions.append({
                    "session_id": session.session_id,
                    "created_at": session.created_at.isoformat(),
                    "last_activity": session.last_activity.isoformat(),
                    "expires_at": session.expires_at.isoformat(),
                    "device": {
                        "device_type": session.device_info.device_type.value,
                        "os_family": session.device_info.os_family.value,
                        "browser": session.device_info.browser,
                        "ip_address": session.device_info.ip_address
                    },
                    "is_current": False  # TODO: Track current session
                })

        return sessions

    async def revoke_session(
        self,
        user_id: int,
        session_id: str
    ) -> bool:
        """Revoke specific session"""
        if session_id in self._sessions:
            session = self._sessions[session_id]

            # Verify ownership
            if session.user_id != user_id:
                logger.warning(f"User {user_id} attempted to revoke session {session_id} belonging to user {session.user_id}")
                return False

            # Remove session
            del self._sessions[session_id]

            # Update user sessions list
            if session_id in self._user_sessions.get(user_id, []):
                self._user_sessions[user_id].remove(session_id)

            logger.info(f"Session {session_id} revoked for user {user_id}")
            return True

        return False

    async def revoke_all_sessions(
        self,
        user_id: int,
        except_session_id: Optional[str] = None
    ) -> int:
        """Revoke all sessions for user (optionally except current)"""
        session_ids = self._user_sessions.get(user_id, []).copy()

        count = 0
        for session_id in session_ids:
            if except_session_id and session_id == except_session_id:
                continue

            await self.revoke_session(user_id, session_id)
            count += 1

        logger.info(f"Revoked {count} sessions for user {user_id}")
        return count

    async def refresh_session(
        self,
        refresh_token: str
    ) -> Optional[Dict[str, Any]]:
        """Refresh session using refresh token"""
        # Find session with this refresh token
        for session_id, session in self._sessions.items():
            if session.refresh_token == refresh_token and session.is_active:
                # Check if expired
                if datetime.utcnow() > session.expires_at:
                    await self.revoke_session(session.user_id, session_id)
                    return None

                # Generate new tokens
                new_access_token = self._generate_session_id()
                new_refresh_token = self._generate_session_id()

                # Update session
                session.refresh_token = new_refresh_token
                session.last_activity = datetime.utcnow()

                # Extend expiry
                session.expires_at = datetime.utcnow() + timedelta(
                    days=settings.REFRESH_TOKEN_EXPIRE_DAYS
                )

                logger.info(f"Session {session_id} refreshed for user {session.user_id}")

                return {
                    "success": True,
                    "data": {
                        "session_id": session_id,
                        "access_token": new_access_token,
                        "refresh_token": new_refresh_token,
                        "expires_at": session.expires_at.isoformat()
                    }
                }

        return None

    async def track_login_attempt(
        self,
        ip_address: str,
        username: str,
        success: bool,
        user_agent: str,
        failure_reason: Optional[str] = None
    ) -> None:
        """Track login attempt for security monitoring"""
        device_info = self._parse_user_agent(user_agent)
        device_info.ip_address = ip_address

        attempt = LoginAttempt(
            ip_address=ip_address,
            username=username,
            timestamp=datetime.utcnow(),
            success=success,
            device_info=device_info,
            failure_reason=failure_reason
        )

        # Store by IP
        if ip_address not in self._login_attempts:
            self._login_attempts[ip_address] = []

        self._login_attempts[ip_address].append(attempt)

        # Clean old attempts (keep last 100)
        if len(self._login_attempts[ip_address]) > 100:
            self._login_attempts[ip_address] = self._login_attempts[ip_address][-100:]

        # Check for brute force patterns
        await self._check_brute_force(ip_address)

    async def _check_brute_force(self, ip_address: str) -> None:
        """Check for brute force attack patterns"""
        attempts = self._login_attempts.get(ip_address, [])

        # Count failed attempts in last 15 minutes
        cutoff = datetime.utcnow() - timedelta(minutes=15)
        recent_failures = [
            a for a in attempts
            if a.timestamp > cutoff and not a.success
        ]

        # If more than 5 failed attempts, log warning
        if len(recent_failures) > 5:
            logger.warning(f"Possible brute force attack from {ip_address}: {len(recent_failures)} failed attempts")

            # TODO: Implement IP banning or rate limiting
            # await self._ban_ip_temporarily(ip_address)

    async def _log_activity(
        self,
        user_id: int,
        action: str,
        ip_address: str,
        user_agent: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log user activity (for audit trail)"""
        # TODO: Store in database using UserActivity model
        activity = {
            "user_id": user_id,
            "action": action,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow().isoformat()
        }

        logger.info(f"User activity: {activity}")

    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions"""
        now = datetime.utcnow()
        expired_sessions = []

        for session_id, session in self._sessions.items():
            if now > session.expires_at:
                expired_sessions.append((session_id, session.user_id))

        for session_id, user_id in expired_sessions:
            await self.revoke_session(user_id, session_id)

        return len(expired_sessions)

    def get_user_devices(self, user_id: int) -> List[DeviceInfo]:
        """Get all devices for user"""
        return self._devices.get(user_id, [])


# Global session manager instance
session_manager = SessionManager()


__all__ = [
    'SessionManager',
    'session_manager',
    'UserSession',
    'DeviceInfo',
    'LoginAttempt',
    'DeviceType',
    'OSFamily',
]
