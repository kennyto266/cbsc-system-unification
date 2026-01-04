"""
Authentication middleware with MFA support

This module provides enhanced authentication middleware that supports:
- JWT token verification
- MFA requirement checking
- Trusted device verification
- Session management
- Rate limiting
"""

from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
import jwt
import os
import logging

# Database
from src.core.database import get_db

# Models
from src.models.user import User
from src.models.mfa_models import MFASession, MFATrustedDevice, UserSecuritySettings

# Utils
from src.utils.device_fingerprint import get_device_fingerprint

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class AuthenticationError(Exception):
    """Custom authentication error"""
    pass


class MFARequiredError(Exception):
    """MFA verification required"""
    pass


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
    mfa_verified: bool = False,
    device_trusted: bool = False
) -> str:
    """
    Create JWT access token

    Args:
        data: Token payload data
        expires_delta: Token expiration time
        mfa_verified: Whether MFA has been verified
        device_trusted: Whether device is trusted

    Returns:
        str: JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "mfa_verified": mfa_verified,
        "device_trusted": device_trusted
    })

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> dict:
    """
    Verify JWT token and return payload

    Args:
        token: JWT token string

    Returns:
        dict: Token payload

    Raises:
        AuthenticationError: If token is invalid
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token has expired")
    except jwt.JWTError as e:
        raise AuthenticationError(f"Invalid token: {str(e)}")


def check_mfa_requirement(
    user: User,
    db: Session,
    request: Request,
    device_fingerprint: Optional[str] = None
) -> Dict[str, Any]:
    """
    Check if MFA is required for the user and request

    Args:
        user: User object
        db: Database session
        request: FastAPI request object
        device_fingerprint: Device fingerprint

    Returns:
        Dict: MFA check result with requirements
    """
    try:
        # Get user security settings
        security_settings = db.query(UserSecuritySettings).filter(
            UserSecuritySettings.user_id == user.id
        ).first()

        if not security_settings:
            # Create default settings if not exist
            security_settings = UserSecuritySettings(user_id=user.id)
            db.add(security_settings)
            db.commit()

        # Check if MFA is enabled for user
        if not user.mfa_enabled:
            return {
                "mfa_required": False,
                "reason": "MFA not enabled"
            }

        # Check if device is trusted
        if device_fingerprint and security_settings.enable_trusted_devices:
            trusted_device = db.query(MFATrustedDevice).filter(
                MFATrustedDevice.user_id == user.id,
                MFATrustedDevice.device_fingerprint == device_fingerprint,
                MFATrustedDevice.is_active == True
            ).first()

            if trusted_device and not trusted_device.is_expired():
                # Update last used timestamp
                trusted_device.update_last_used(
                    ip_address=request.client.host,
                    user_agent=request.headers.get("user-agent")
                )
                db.commit()

                return {
                    "mfa_required": False,
                    "reason": "Device is trusted"
                }

        # Check if MFA is required based on settings
        # For sensitive operations, MFA is always required
        # For login, check user preference
        sensitive_operations = [
            "/api/strategies/create",
            "/api/strategies/update",
            "/api/strategies/delete",
            "/api/user/change-password",
            "/api/user/update-email",
            "/api/mfa/disable",
            "/api/backtest/run"
        ]

        request_path = request.url.path
        is_sensitive_operation = any(
            request_path.startswith(op) for op in sensitive_operations
        )

        if is_sensitive_operation and security_settings.require_mfa_for_sensitive_operations:
            return {
                "mfa_required": True,
                "reason": "Sensitive operation requires MFA",
                "mfa_type": user.mfa_type
            }

        if security_settings.require_mfa_for_login and request_path == "/api/auth/login":
            return {
                "mfa_required": True,
                "reason": "Login requires MFA",
                "mfa_type": user.mfa_type
            }

        return {
            "mfa_required": False,
            "reason": "MFA not required for this operation"
        }

    except Exception as e:
        logger.error(f"Error checking MFA requirement: {str(e)}")
        # Default to requiring MFA on error for security
        return {
            "mfa_required": True,
            "reason": "Security check failed",
            "mfa_type": user.mfa_type if user.mfa_enabled else None
        }


async def get_current_user_optional(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get current user from token (optional)

    Returns:
        Optional[User]: User object or None if not authenticated
    """
    if not credentials:
        return None

    try:
        # Verify token
        payload = verify_token(credentials.credentials)
        user_id = payload.get("sub")

        if not user_id:
            return None

        # Get user from database
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            return None

        return user

    except AuthenticationError:
        return None
    except Exception as e:
        logger.error(f"Error getting current user: {str(e)}")
        return None


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
    require_mfa: bool = False
) -> User:
    """
    Get current user with authentication

    Args:
        request: FastAPI request object
        credentials: HTTP Authorization credentials
        db: Database session
        require_mfa: Whether to require MFA verification

    Returns:
        User: Authenticated user object

    Raises:
        HTTPException: If authentication fails
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Verify token
        payload = verify_token(credentials.credentials)
        user_id = payload.get("sub")
        mfa_verified = payload.get("mfa_verified", False)
        device_trusted = payload.get("device_trusted", False)

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )

        # Get user from database
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive"
            )

        # Check if account is locked
        if user.locked_until and user.locked_until > datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Account is locked. Please try again later."
            )

        # Get device fingerprint
        device_fingerprint = get_device_fingerprint(request)

        # Check MFA requirement
        if require_mfa:
            mfa_check = check_mfa_requirement(
                user=user,
                db=db,
                request=request,
                device_fingerprint=device_fingerprint
            )

            if mfa_check["mfa_required"]:
                # Check if MFA is already verified in token
                if not mfa_verified and not device_trusted:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail={
                            "error": "MFA verification required",
                            "mfa_type": mfa_check.get("mfa_type"),
                            "reason": mfa_check.get("reason")
                        },
                        headers={"X-MFA-Required": "true"}
                    )

        # Update last login info (only on successful auth)
        if request.url.path == "/api/auth/verify":
            user.last_login_at = datetime.now(timezone.utc)
            user.last_login_ip = request.client.host
            db.commit()

        return user

    except HTTPException:
        raise
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )


async def get_current_user_with_mfa(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current user requiring MFA verification

    This dependency ensures that MFA has been verified for the current session.
    """
    return await get_current_user(
        request=request,
        credentials=credentials,
        db=db,
        require_mfa=True
    )


def require_permissions(required_permissions: List[str]):
    """
    Create dependency that requires specific permissions

    Args:
        required_permissions: List of required permission codes

    Returns:
        Dependency function
    """
    async def permission_dependency(
        current_user: User = Depends(get_current_user)
    ) -> User:
        """Check if user has required permissions"""
        for permission in required_permissions:
            if not current_user.has_permission(permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission required: {permission}"
                )

        return current_user

    return permission_dependency


def require_roles(required_roles: List[str]):
    """
    Create dependency that requires specific roles

    Args:
        required_roles: List of required role names

    Returns:
        Dependency function
    """
    async def role_dependency(
        current_user: User = Depends(get_current_user)
    ) -> User:
        """Check if user has required roles"""
        user_roles = [role.name for role in current_user.roles]

        for role in required_roles:
            if role not in user_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role required: {role}"
                )

        return current_user

    return role_dependency


# Rate limiting utilities
async def check_rate_limit(
    user_id: str,
    action: str,
    limit: int,
    window_minutes: int = 60
) -> bool:
    """
    Check if user has exceeded rate limit for an action

    Args:
        user_id: User ID
        action: Action type
        limit: Maximum allowed actions
        window_minutes: Time window in minutes

    Returns:
        bool: True if rate limit is not exceeded
    """
    # TODO: Implement Redis-based rate limiting
    # For now, always return True
    return True


# Session management utilities
def create_mfa_session(
    user_id: str,
    mfa_type: str,
    db: Session,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    expires_minutes: int = 10
) -> str:
    """
    Create MFA verification session

    Args:
        user_id: User ID
        mfa_type: Type of MFA
        db: Database session
        ip_address: Client IP address
        user_agent: User agent string
        expires_minutes: Session expiration in minutes

    Returns:
        str: Session token
    """
    session_token = f"mfa_{user_id}_{datetime.now(timezone.utc).timestamp()}"

    mfa_session = MFASession(
        user_id=user_id,
        session_token=session_token,
        mfa_type=mfa_type,
        status='pending',
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=expires_minutes),
        ip_address=ip_address,
        user_agent=user_agent
    )

    db.add(mfa_session)
    db.commit()
    db.refresh(mfa_session)

    return session_token