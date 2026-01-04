"""
Authentication API v2 Endpoints
認證 API v2 端點實現

Provides enhanced authentication with MFA, JWT refresh tokens, and security features
提供增強的認證功能，包括多因子認證、JWT 刷新令牌和安全功能
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordBearer
from typing import List, Optional
from datetime import datetime, timedelta
import logging
import hashlib

from src.schemas.auth_schemas import (
    UserLogin, UserRegistration, PasswordReset, PasswordResetConfirm,
    PasswordChange, TokenRefresh, MFASetupRequest, MFAVerifyRequest,
    MFADisableRequest, LoginResponse, RegisterResponse, TokenRefreshResponse,
    LogoutResponse, MFASetupResponse, UserProfile, PasswordStrength,
    MFAType, AuthResponse, SessionInfo
)
from src.services.auth_service_v2 import auth_service_v2, MFAType as ServiceMFAType

# Import existing models
from auth_simple import User, auth_service

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v2/auth", tags=["authentication"])

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v2/auth/login")

# Dependencies
def get_db():
    """Get database session"""
    return auth_service.get_db()

def get_current_user(token: str = Depends(oauth2_scheme)):
    """Get current authenticated user"""
    return auth_service.get_current_user(token)

def get_current_active_user(current_user: User = Depends(get_current_user)):
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user

def get_device_fingerprint(request: Request) -> str:
    """Extract device fingerprint from request"""
    # Create fingerprint from user agent and other headers
    user_agent = request.headers.get("user-agent", "")
    accept_lang = request.headers.get("accept-language", "")
    accept_encoding = request.headers.get("accept-encoding", "")

    fingerprint_data = f"{user_agent}-{accept_lang}-{accept_encoding}"
    return hashlib.sha256(fingerprint_data.encode()).hexdigest()

# Helper functions
def create_token_response(user: User, device_name: str, device_fingerprint: str) -> dict:
    """Create complete token response"""
    # Create access token
    access_token = auth_service.create_access_token(
        data={"sub": str(user.id), "username": user.username}
    )

    # Create refresh token
    refresh_token, expires_at = auth_service_v2.create_refresh_token(
        user.id, device_name, device_fingerprint
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": 1800,  # 30 minutes
        "refresh_expires_in": int((expires_at - datetime.utcnow()).total_seconds())
    }

# Endpoints

@router.post("/login", response_model=LoginResponse)
async def login(
    user_credentials: UserLogin,
    request: Request,
    db=Depends(get_db)
):
    """
    User login with MFA support
    支持多因子認證的用戶登入
    """
    try:
        # Extract client information
        client_ip = request.client.host
        user_agent = request.headers.get("user-agent", "")
        device_fingerprint = user_credentials.device_fingerprint or get_device_fingerprint(request)
        device_name = user_credentials.device_name or f"Device-{device_fingerprint[:8]}"

        # Check rate limiting
        if not auth_service_v2.check_rate_limit(client_ip, user_credentials.username):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many login attempts. Please try again later."
            )

        # Authenticate user
        user = auth_service.authenticate_user(
            user_credentials.username,
            user_credentials.password,
            db
        )

        if not user:
            # Record failed attempt
            auth_service_v2.record_login_attempt(
                client_ip, user_credentials.username, False,
                user_agent, "Invalid credentials"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check if user is active
        if not user.is_active:
            auth_service_v2.record_login_attempt(
                client_ip, user.username, False,
                user_agent, "Account disabled"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Account is disabled"
            )

        # Get user MFA settings
        mfa_settings = auth_service_v2.get_user_mfa_settings(user.id)

        if mfa_settings:
            # MFA is configured - generate challenge token
            mfa_types = [MFAType(m.mfa_type.value) for m in mfa_settings]
            challenge_token = auth_service_v2.generate_mfa_challenge_token(
                user.id, [ServiceMFAType(m.value) for m in mfa_types]
            )

            # Record successful authentication (first step)
            auth_service_v2.record_login_attempt(
                client_ip, user.username, True,
                user_agent, "First factor authenticated"
            )

            return LoginResponse(
                success=True,
                message="Please complete MFA verification",
                requires_mfa=True,
                mfa_types=mfa_types,
                mfa_challenge_token=challenge_token
            )
        else:
            # No MFA - complete login
            auth_service_v2.record_login_attempt(
                client_ip, user.username, True,
                user_agent, "Login successful"
            )

            token_info = create_token_response(user, device_name, device_fingerprint)

            # Record login history
            auth_service.record_login_history(user, True, client_ip, user_agent)

            return LoginResponse(
                success=True,
                message="Login successful",
                requires_mfa=False,
                token_info=token_info
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed. Please try again."
        )

@router.post("/mfa/verify", response_model=LoginResponse)
async def verify_mfa(
    mfa_data: MFAVerifyRequest,
    request: Request,
    db=Depends(get_db)
):
    """
    Verify MFA and complete login
    驗證多因子認證並完成登入
    """
    try:
        # Verify MFA challenge token
        challenge_payload = auth_service_v2.verify_mfa_challenge_token(mfa_data.mfa_challenge_token)
        if not challenge_payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired MFA challenge"
            )

        user_id = int(challenge_payload["sub"])
        mfa_types = [MFAType(t) for t in challenge_payload["mfa_types"]]

        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        # Get device information
        device_fingerprint = get_device_fingerprint(request)
        device_name = f"Device-{device_fingerprint[:8]}"
        client_ip = request.client.host
        user_agent = request.headers.get("user-agent", "")

        # Verify MFA code or backup code
        mfa_verified = False
        mfa_settings = auth_service_v2.get_user_mfa_settings(user.id)

        for mfa_setting in mfa_settings:
            if MFAType(mfa_setting.mfa_type.value) in mfa_types:
                # Try TOTP verification
                if mfa_setting.mfa_type == ServiceMFAType.TOTP:
                    if mfa_data.code:
                        mfa_verified = auth_service_v2.verify_totp(
                            mfa_setting.secret, mfa_data.code
                        )
                        if mfa_verified:
                            break

                    # Try backup code
                    elif mfa_data.backup_code:
                        backup_codes = json.loads(mfa_setting.backup_codes or "[]")
                        if mfa_data.backup_code in backup_codes:
                            backup_codes.remove(mfa_data.backup_code)
                            mfa_setting.backup_codes = json.dumps(backup_codes)
                            db.commit()
                            mfa_verified = True
                            break

                # TODO: Implement email and SMS MFA verification
                elif mfa_setting.mfa_type in [ServiceMFAType.EMAIL, ServiceMFAType.SMS]:
                    # Implementation for email/SMS MFA would go here
                    pass

        if not mfa_verified:
            auth_service_v2.record_login_attempt(
                client_ip, user.username, False,
                user_agent, "MFA verification failed"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid MFA code"
            )

        # MFA verified - complete login
        auth_service_v2.record_login_attempt(
            client_ip, user.username, True,
            user_agent, "MFA verification successful"
        )

        token_info = create_token_response(user, device_name, device_fingerprint)

        # Update MFA last used
        mfa_setting.last_used = datetime.utcnow()
        db.commit()

        # Record login history
        auth_service.record_login_history(user, True, client_ip, user_agent)

        return LoginResponse(
            success=True,
            message="Login successful",
            requires_mfa=False,
            token_info=token_info
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"MFA verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="MFA verification failed"
        )

@router.post("/register", response_model=RegisterResponse)
async def register(
    user_data: UserRegistration,
    request: Request,
    db=Depends(get_db)
):
    """
    User registration
    用戶註冊
    """
    try:
        # Validate terms acceptance
        if not user_data.accept_terms:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You must accept the terms and conditions"
            )

        # Check if username already exists
        existing_user = db.query(User).filter(
            (User.username == user_data.username) |
            (User.email == user_data.email)
        ).first()

        if existing_user:
            field = "username" if existing_user.username == user_data.username else "email"
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"This {field} is already registered"
            )

        # Create new user
        hashed_password = auth_service.hash_password(user_data.password)

        new_user = User(
            username=user_data.username,
            email=user_data.email,
            password_hash=hashed_password,
            is_active=True,  # Or False if email verification is required
            created_at=datetime.utcnow()
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # TODO: Send verification email if needed

        client_ip = request.client.host
        user_agent = request.headers.get("user-agent", "")

        logger.info(f"New user registered: {new_user.username} from {client_ip}")

        return RegisterResponse(
            success=True,
            message="Registration successful. Please check your email to verify your account.",
            user_id=new_user.id,
            email_verification_required=True  # Set based on your requirements
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again."
        )

@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_token(
    refresh_data: TokenRefresh,
    request: Request
):
    """
    Refresh access token
    刷新訪問令牌
    """
    try:
        # Verify refresh token
        payload = auth_service_v2.verify_refresh_token(
            refresh_data.refresh_token,
            refresh_data.device_fingerprint
        )

        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )

        user_id = int(payload["sub"])
        token_id = payload["jti"]

        # Get user
        db = next(get_db())
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user or not user.is_active:
                # Revoke the token if user doesn't exist or is inactive
                auth_service_v2.revoke_refresh_token(token_id)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found or inactive"
                )

            # Create new access token
            access_token = auth_service.create_access_token(
                data={"sub": str(user.id), "username": user.username}
            )

            # Create new refresh token (rotate tokens)
            device_name = request.headers.get("X-Device-Name", "Unknown Device")
            new_refresh_token, expires_at = auth_service_v2.create_refresh_token(
                user_id, device_name, refresh_data.device_fingerprint
            )

            # Revoke old refresh token
            auth_service_v2.revoke_refresh_token(token_id)

            token_info = {
                "access_token": access_token,
                "refresh_token": new_refresh_token,
                "token_type": "bearer",
                "expires_in": 1800,
                "refresh_expires_in": int((expires_at - datetime.utcnow()).total_seconds())
            }

            return TokenRefreshResponse(
                success=True,
                message="Token refreshed successfully",
                token_info=token_info
            )

        finally:
            db.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )

@router.post("/logout", response_model=LogoutResponse)
async def logout(
    current_user: User = Depends(get_current_active_user),
    request: Request = None
):
    """
    Secure logout with token revocation
    安全登出並撤銷令牌
    """
    try:
        # Get token from Authorization header
        authorization = request.headers.get("authorization")
        revoked_count = 0

        if authorization and authorization.startswith("Bearer "):
            token = authorization[7:]
            try:
                # Decode token to get user ID
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                user_id = int(payload.get("sub"))
                jti = payload.get("jti")

                # Revoke all refresh tokens for this user
                revoked_count = auth_service_v2.revoke_all_user_tokens(user_id)

                # Optionally, add access token to blacklist in Redis
                redis_key = f"blacklist:access:{jti}"
                redis_client.setex(
                    redis_key,
                    timedelta(minutes=30),  # Token expiration time
                    "1"
                )

            except jwt.PyJWTError:
                pass  # Token invalid, but still logout

        logger.info(f"User {current_user.username} logged out successfully")

        return LogoutResponse(
            success=True,
            message="Logged out successfully",
            revoked_tokens_count=revoked_count
        )

    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )

@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    """
    Change user password
    修改用戶密碼
    """
    try:
        # Verify old password
        if not auth_service.verify_password(password_data.old_password, current_user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )

        # Validate new password strength
        strength = auth_service.validate_password_strength(password_data.new_password)
        if strength['score'] < 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Password is too weak (score: {strength['score']}/6)"
            )

        # Update password
        current_user.password_hash = auth_service.hash_password(password_data.new_password)
        current_user.updated_at = datetime.utcnow()

        db.commit()

        # Revoke all refresh tokens (force re-login on all devices)
        auth_service_v2.revoke_all_user_tokens(current_user.id)

        logger.info(f"User {current_user.username} changed password successfully")

        return AuthResponse(
            success=True,
            message="Password changed successfully. You will need to login again on all devices."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change error: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )

@router.post("/mfa/setup", response_model=MFASetupResponse)
async def setup_mfa(
    mfa_setup: MFASetupRequest,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    """
    Setup MFA for user
    為用戶設置多因子認證
    """
    try:
        # Check if MFA type already exists
        existing_mfa = db.query(auth_service_v2.UserMFA).filter(
            auth_service_v2.UserMFA.user_id == current_user.id,
            auth_service_v2.UserMFA.mfa_type == ServiceMFAType(mfa_setup.mfa_type.value)
        ).first()

        if existing_mfa and existing_mfa.is_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"MFA type {mfa_setup.mfa_type.value} is already enabled"
            )

        # Create MFA setup
        if mfa_setup.mfa_type == MFAType.TOTP:
            secret = auth_service_v2.generate_totp_secret()
            qr_code = auth_service_v2.generate_qr_code(
                secret, current_user.username, "CBSC Quant"
            )
            backup_codes = auth_service_v2.generate_backup_codes()

            # Save MFA settings (not enabled yet)
            if existing_mfa:
                existing_mfa.secret = secret
                existing_mfa.backup_codes = json.dumps(backup_codes)
            else:
                new_mfa = auth_service_v2.UserMFA(
                    user_id=current_user.id,
                    mfa_type=ServiceMFAType.TOTP,
                    secret=secret,
                    backup_codes=json.dumps(backup_codes),
                    is_enabled=False
                )
                db.add(new_mfa)

            db.commit()

            return MFASetupResponse(
                success=True,
                message="TOTP MFA setup initiated. Please scan QR code and verify to enable.",
                mfa_type=mfa_setup.mfa_type,
                secret=secret,
                qr_code=qr_code,
                backup_codes=backup_codes,
                setup_instructions={
                    "step1": "Scan the QR code with your authenticator app",
                    "step2": "Enter the verification code to enable MFA",
                    "step3": "Save backup codes in a secure location"
                }
            )

        # TODO: Implement email and SMS MFA setup
        elif mfa_setup.mfa_type in [MFAType.EMAIL, MFAType.SMS]:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Email/SMS MFA not yet implemented"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"MFA setup error: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="MFA setup failed"
        )

@router.get("/me", response_model=UserProfile)
async def get_profile(current_user: User = Depends(get_current_active_user)):
    """
    Get current user profile
    獲取當前用戶資料
    """
    # Get MFA settings
    mfa_settings = auth_service_v2.get_user_mfa_settings(current_user.id)
    mfa_enabled = len(mfa_settings) > 0

    return UserProfile(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        full_name=None,  # Add if you have full_name field
        is_active=current_user.is_active,
        is_verified=True,  # Add if you have verification field
        created_at=current_user.created_at,
        last_login=current_user.last_login,
        mfa_summary=MFASummary(
            mfa_enabled=mfa_enabled,
            mfa_types=[MFAType(m.mfa_type.value) for m in mfa_settings],
            last_used=mfa_settings[0].last_used if mfa_settings else None
        )
    )

# Import jwt for token operations
import jwt
from jose import jwt as jose_jwt

# Add missing import for redis_client
try:
    from services.redis_client import redis_client
except ImportError:
    # Fallback if no redis client
    redis_client = None

# Add missing import for json
import json