"""
Authentication API Endpoints
FastAPI router for authentication and user management
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from .service import AuthService
from .schemas import (
    UserCreate, UserLogin, UserResponse, Token, TokenRefresh,
    PasswordChange, PasswordReset, PasswordResetConfirm,
    EmailVerification, UserUpdate, PasswordStrengthResult,
    UserDeviceResponse, LoginHistoryResponse, UserListParams,
    RoleCreate, RoleUpdate, RoleResponse, RoleListParams,
    APIResponse, PaginatedResponse
)
from .models import User, UserSession, UserDevice
from .middleware import (
    get_current_user, get_current_user_optional,
    require_admin, require_permissions, rate_limit
)
from .utils import verify_email_token, verify_password_reset_token
from .exceptions import (
    AuthenticationError, AuthorizationError, UserNotFoundError,
    UserAlreadyExistsError, PasswordTooWeakError, EmailVerificationError,
    PasswordResetTokenError, RateLimitExceededError
)
from ..dependencies import get_db

# Initialize router
router = APIRouter(prefix="/api/auth", tags=["authentication"])
security = HTTPBearer()


# Initialize auth service (in production, this would be injected)
def get_auth_service() -> AuthService:
    """Get auth service instance"""
    # In production, this would come from app state
    return AuthService()


# Authentication endpoints
@router.post("/register", response_model=UserResponse)
@rate_limit(requests=5, window=60)  # 5 registrations per minute per IP
async def register(
    user_data: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Register new user
    """
    try:
        user = auth_service.create_user(user_data, db)
        return UserResponse.from_orm(user)
    except UserAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except PasswordTooWeakError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
            headers={"X-Password-Requirements": json.dumps(e.details.get("requirements", {}))}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=Token)
@rate_limit(requests=10, window=60)  # 10 login attempts per minute
async def login(
    user_credentials: UserLogin,
    request: Request,
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    User login
    """
    try:
        # Get client info
        ip_address = auth_service.get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        device_fingerprint = request.headers.get("X-Device-Fingerprint")

        # Authenticate user
        user, session_data = auth_service.authenticate_user(
            user_credentials.username,
            user_credentials.password,
            ip_address,
            user_agent,
            device_fingerprint,
            db
        )

        return Token(**session_data)

    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
            headers={"WWW-Authenticate": "Bearer"}
        )
    except RateLimitExceededError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=e.message,
            headers={"Retry-After": str(e.details.get("retry_after", 60))}
        )


@router.post("/refresh", response_model=Dict[str, Any])
async def refresh_token(
    refresh_data: Dict[str, str] = Body(...),
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Refresh access token
    """
    try:
        refresh_token = refresh_data.get("refresh_token")
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Refresh token required"
            )

        token_data = auth_service.refresh_token(refresh_token, db)
        return token_data

    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message
        )


@router.post("/logout")
async def logout(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    User logout
    """
    try:
        success = auth_service.logout_user(credentials.credentials, db)
        if success:
            return {"message": "Logged out successfully"}
        else:
            return {"message": "Session not found"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user information
    """
    return UserResponse.from_orm(current_user)


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Update current user information
    """
    try:
        updated_user = auth_service.update_user(str(current_user.id), user_update, db)
        return updated_user
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )


# Password management
@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Change user password
    """
    try:
        success = auth_service.change_password(
            current_user,
            password_data.old_password,
            password_data.new_password,
            db
        )

        if success:
            return {"message": "Password changed successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Old password incorrect"
            )

    except PasswordTooWeakError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )


@router.post("/reset-password")
@rate_limit(requests=3, window=300)  # 3 resets per 5 minutes
async def request_password_reset(
    reset_data: PasswordReset,
    request: Request,
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Request password reset
    """
    try:
        auth_service.request_password_reset(
            reset_data.email,
            auth_service.get_client_ip(request),
            db
        )
        return {"message": "Password reset email sent"}
    except UserNotFoundError:
        # Don't reveal if email exists
        return {"message": "Password reset email sent if email exists"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset request failed"
        )


@router.post("/reset-password/confirm")
async def confirm_password_reset(
    reset_data: PasswordResetConfirm,
    request: Request,
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Confirm password reset with token
    """
    try:
        success = auth_service.confirm_password_reset(
            reset_data.token,
            reset_data.new_password,
            auth_service.get_client_ip(request),
            db
        )

        if success:
            return {"message": "Password reset successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )

    except PasswordResetTokenError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed"
        )


# Email verification
@router.post("/verify-email")
async def verify_email(
    verification_data: EmailVerification,
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Verify email address
    """
    try:
        success = auth_service.verify_email(verification_data.token, db)

        if success:
            return {"message": "Email verified successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification token"
            )

    except EmailVerificationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email verification failed"
        )


@router.post("/resend-verification")
@rate_limit(requests=3, window=300)
async def resend_verification_email(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Resend email verification
    """
    if current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified"
        )

    try:
        auth_service._send_verification_email(
            current_user.email,
            str(current_user.id)
        )
        return {"message": "Verification email sent"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email"
        )


# Password strength
@router.post("/validate-password", response_model=PasswordStrengthResult)
async def validate_password(
    password_data: Dict[str, str] = Body(...),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Validate password strength
    """
    password = password_data.get("password", "")
    username = current_user.username if current_user else password_data.get("username", "")
    email = current_user.email if current_user else password_data.get("email", "")

    from .utils import validate_password_strength
    result = validate_password_strength(password, username, email)

    return PasswordStrengthResult(**result)


# Device management
@router.get("/devices", response_model=List[UserDeviceResponse])
async def get_user_devices(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user devices
    """
    try:
        devices = db.query(UserDevice).filter(
            UserDevice.user_id == current_user.id
        ).order_by(UserDevice.last_seen_at.desc()).all()

        return [UserDeviceResponse.from_orm(device) for device in devices]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get devices"
        )


@router.delete("/devices/{device_id}")
async def revoke_device(
    device_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Revoke device access
    """
    try:
        success = auth_service.revoke_device(
            current_user.id,
            UUID(device_id),
            db
        )

        if success:
            return {"message": "Device access revoked"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found"
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke device"
        )


# Login history
@router.get("/login-history", response_model=List[LoginHistoryResponse])
async def get_login_history(
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user login history
    """
    try:
        from .models import LoginHistory
        history = db.query(LoginHistory).filter(
            LoginHistory.user_id == current_user.id
        ).order_by(LoginHistory.created_at.desc()).limit(limit).all()

        return [LoginHistoryResponse.from_orm(record) for record in history]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get login history"
        )


# MFA endpoints (simplified for brevity)
@router.post("/mfa/setup")
async def setup_mfa(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Setup MFA for user
    """
    try:
        mfa_data = auth_service.setup_mfa(current_user, db)
        return mfa_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to setup MFA"
        )


@router.post("/mfa/verify")
async def verify_mfa(
    mfa_data: Dict[str, str] = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Verify MFA token
    """
    try:
        code = mfa_data.get("code")
        if not code or len(code) != 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid MFA code"
            )

        success = auth_service.verify_mfa_token(
            current_user,
            code,
            db
        )

        if success:
            return {"message": "MFA verified successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid MFA code"
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="MFA verification failed"
        )


# Health check
@router.get("/health")
async def health_check(
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Health check for auth service
    """
    return {
        "status": "healthy",
        "service": "authentication",
        "timestamp": datetime.utcnow().isoformat()
    }