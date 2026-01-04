"""
Authentication API v2 routes.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from middleware.auth import get_current_user, get_current_active_user
from services.auth_service import AuthService
from schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
    UserCreate,
    UserUpdate,
    ChangePasswordRequest
)
from models.user import User

router = APIRouter()


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def login_v2(
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    """
    Authenticate user and return access token.

    - **username**: User username or email
    - **password**: User password
    """
    service = AuthService(db)
    try:
        return await service.login(credentials.username, credentials.password)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_v2(
    user_data: RegisterRequest,
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """
    Register a new user.

    - **username**: Unique username (min 3 characters)
    - **email**: Valid email address
    - **password**: Password (min 8 characters)
    - **full_name**: Optional full name
    """
    import sys
    import traceback
    print(f"DEBUG register_v2: Starting registration...", file=sys.stderr)
    print(f"DEBUG register_v2: Got db session: {db}", file=sys.stderr)
    service = AuthService(db)
    print(f"DEBUG register_v2: AuthService created", file=sys.stderr)
    try:
        print(f"DEBUG register_v2: Creating UserCreate schema...", file=sys.stderr)
        user_create = UserCreate(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name
        )
        print(f"DEBUG register_v2: UserCreate created, calling service.register...", file=sys.stderr)
        user = await service.register(user_create)
        print(f"DEBUG register_v2: User registered, creating response...", file=sys.stderr)
        return UserResponse.model_validate(user)
    except ValueError as e:
        print(f"DEBUG register_v2: ValueError caught: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        print(f"DEBUG register_v2: Unexpected error: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        raise


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token_v2(
    refresh_token: str,
    db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    """Refresh access token using refresh token."""
    service = AuthService(db)
    try:
        return await service.refresh_token(refresh_token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_v2(
    current_user: User = Depends(get_current_active_user)
) -> UserResponse:
    """Get current authenticated user information."""
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
async def update_current_user_v2(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """Update current user information."""
    service = AuthService(db)
    user = await service.update_user(current_user.id, user_data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return UserResponse.model_validate(user)


@router.post("/change-password")
async def change_password_v2(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Change current user password."""
    service = AuthService(db)
    try:
        await service.change_password(
            current_user.id,
            password_data.old_password,
            password_data.new_password
        )
        return {"message": "Password changed successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# OAuth2 compatible endpoint for token generation
@router.post("/token", response_model=TokenResponse)
async def login_oauth2_v2(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    """
    OAuth2 compatible token endpoint.

    This endpoint accepts form data with username and password fields,
    making it compatible with OAuth2 password flow.
    """
    service = AuthService(db)
    try:
        return await service.login(form_data.username, form_data.password)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )
