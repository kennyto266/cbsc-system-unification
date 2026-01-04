"""
Authentication service - handles user authentication and token management.
"""

from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import timedelta

from models.user import User
from schemas.auth import UserCreate, UserUpdate, TokenResponse
from core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token
)
from core.config import settings

# Debug: print which module's get_password_hash is being used
import sys
print(f"DEBUG auth_service: get_password_hash module: {get_password_hash.__module__}", file=sys.stderr)
print(f"DEBUG auth_service: get_password_hash function: {get_password_hash}", file=sys.stderr)


class AuthService:
    """Authentication business logic service"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(
        self,
        user_data: UserCreate
    ) -> User:
        """
        Register a new user.

        Args:
            user_data: User creation data

        Returns:
            Created user object

        Raises:
            ValueError: If username or email already exists
        """
        # Check if username exists
        result = await self.db.execute(
            select(User).where(User.username == user_data.username)
        )
        if result.scalar_one_or_none():
            raise ValueError("Username already exists")

        # Check if email exists
        result = await self.db.execute(
            select(User).where(User.email == user_data.email)
        )
        if result.scalar_one_or_none():
            raise ValueError("Email already exists")

        # Create new user
        import sys
        print(f"DEBUG register: Hashing password...", file=sys.stderr)
        hashed_password = get_password_hash(user_data.password)
        print(f"DEBUG register: Creating user object...", file=sys.stderr)
        user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            is_active=user_data.is_active
        )

        print(f"DEBUG register: Adding to session...", file=sys.stderr)
        self.db.add(user)
        print(f"DEBUG register: Committing to database...", file=sys.stderr)
        await self.db.commit()
        print(f"DEBUG register: Refreshing user object...", file=sys.stderr)
        await self.db.refresh(user)
        print(f"DEBUG register: User created successfully: {user.id}", file=sys.stderr)

        return user

    async def login(
        self,
        username: str,
        password: str
    ) -> TokenResponse:
        """
        Authenticate user and return tokens.

        Args:
            username: Username or email
            password: Plain password

        Returns:
            Token response with access and refresh tokens

        Raises:
            ValueError: If credentials are invalid or user is inactive
        """
        # Find user by username or email
        result = await self.db.execute(
            select(User).where(
                (User.username == username) | (User.email == username)
            )
        )
        user = result.scalar_one_or_none()

        # Verify user exists and password is correct
        if not user or not verify_password(password, user.hashed_password):
            raise ValueError("Invalid credentials")

        # Check if user is active
        if not user.is_active:
            raise ValueError("User account is inactive")

        # Create tokens
        token_data = {"sub": str(user.id), "username": user.username}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Get user by ID.

        Args:
            user_id: User ID

        Returns:
            User object or None
        """
        return await self.db.get(User, user_id)

    async def update_user(
        self,
        user_id: int,
        user_data: UserUpdate
    ) -> Optional[User]:
        """
        Update user information.

        Args:
            user_id: User ID
            user_data: Update data

        Returns:
            Updated user object or None
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            return None

        # Update fields
        if user_data.email is not None:
            user.email = user_data.email
        if user_data.full_name is not None:
            user.full_name = user_data.full_name
        if user_data.password is not None:
            user.hashed_password = get_password_hash(user_data.password)
        if user_data.is_active is not None:
            user.is_active = user_data.is_active

        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def change_password(
        self,
        user_id: int,
        old_password: str,
        new_password: str
    ) -> bool:
        """
        Change user password.

        Args:
            user_id: User ID
            old_password: Current password
            new_password: New password

        Returns:
            True if successful

        Raises:
            ValueError: If old password is incorrect
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        if not verify_password(old_password, user.hashed_password):
            raise ValueError("Incorrect password")

        user.hashed_password = get_password_hash(new_password)
        await self.db.commit()

        return True

    async def refresh_token(
        self,
        refresh_token: str
    ) -> TokenResponse:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Refresh token

        Returns:
            New token response

        Raises:
            ValueError: If token is invalid
        """
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise ValueError("Invalid refresh token")

        user_id = payload.get("sub")
        user = await self.get_user_by_id(int(user_id))

        if not user or not user.is_active:
            raise ValueError("Invalid refresh token")

        # Create new tokens
        token_data = {"sub": str(user.id), "username": user.username}
        access_token = create_access_token(token_data)
        new_refresh_token = create_refresh_token(token_data)

        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
