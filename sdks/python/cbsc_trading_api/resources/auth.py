"""
Authentication resource for CBSC Trading API SDK
"""

from typing import Optional
from ..models import (
    TokenRequest,
    TokenResponse,
    RefreshTokenRequest,
    UserLogin,
    UserCreate,
    User,
)
from ..client import CBSCClient


class AuthResource:
    """Resource for authentication operations"""

    def __init__(self, client: CBSCClient):
        self.client = client

    def get_token(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        grant_type: str = "client_credentials",
        scope: Optional[str] = None,
    ) -> TokenResponse:
        """
        Get access token using OAuth2 client credentials flow

        Args:
            client_id: OAuth2 client ID (overrides client setting)
            client_secret: OAuth2 client secret (overrides client setting)
            grant_type: OAuth2 grant type
            scope: Requested scope

        Returns:
            TokenResponse: Token information
        """
        data = TokenRequest(
            grant_type=grant_type,
            client_id=client_id or self.client.client_id,
            client_secret=client_secret or self.client.client_secret,
            scope=scope,
        )

        response = self.client.post("/api/v1/auth/token", data=data.dict(exclude_none=True), require_auth=False)
        response_data = response.json()

        # Parse token response
        token_response = TokenResponse(**response_data)

        # Update client token if not provided explicitly
        if client_id is None and client_secret is None:
            self.client._access_token = token_response.access_token
            self.client._refresh_token = token_response.refresh_token

        return token_response

    def refresh_token(self, refresh_token: str) -> TokenResponse:
        """
        Refresh access token using refresh token

        Args:
            refresh_token: Refresh token

        Returns:
            TokenResponse: New token information
        """
        data = RefreshTokenRequest(refresh_token=refresh_token)
        response = self.client.post("/api/v1/auth/refresh", data=data.dict(), require_auth=False)
        response_data = response.json()

        return TokenResponse(**response_data)

    def login(self, username: str, password: str) -> TokenResponse:
        """
        User login with username and password

        Args:
            username: Username
            password: Password

        Returns:
            TokenResponse: Token information
        """
        data = UserLogin(username=username, password=password)
        response = self.client.post("/api/v1/auth/login", data=data.dict(), require_auth=False)
        response_data = response.json()

        return TokenResponse(**response_data)

    def register(self, user_data: UserCreate) -> User:
        """
        Register a new user

        Args:
            user_data: User creation data

        Returns:
            User: Created user information
        """
        response = self.client.post("/api/v1/auth/register", data=user_data.dict(), require_auth=False)
        response_data = response.json()

        return User(**response_data)