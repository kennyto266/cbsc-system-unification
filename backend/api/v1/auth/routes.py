"""
Authentication API v1 routes - Legacy endpoints for backward compatibility.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from middleware.auth import get_current_active_user
from services.auth_service import AuthService
from schemas.auth import TokenResponse, UserResponse
from models.user import User

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login_v1(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    """
    Legacy v1 login endpoint.

    Compatible with OAuth2 password flow using form data.
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


@router.post("/refresh", response_model=TokenResponse)
async def refresh_v1(
    refresh_token: str,
    db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    """Legacy v1 refresh endpoint."""
    service = AuthService(db)
    try:
        return await service.refresh_token(refresh_token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.get("/me", response_model=UserResponse)
async def get_me_v1(
    current_user: User = Depends(get_current_active_user)
) -> UserResponse:
    """Legacy v1 endpoint to get current user info."""
    return UserResponse.model_validate(current_user)
