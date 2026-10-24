"""
Main client class for CBSC Trading API SDK
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union, List
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .exceptions import (
    CBSCAPIError,
    AuthenticationError,
    RateLimitError,
    NotFoundError,
    ValidationError,
    ServerError,
    ConnectionError as SDKConnectionError,
    TimeoutError,
)
from .models import (
    TokenRequest,
    TokenResponse,
    RefreshTokenRequest,
    APIResponse,
)
from .version import __version__

logger = logging.getLogger(__name__)


class CBSCClient:
    """
    Main client for interacting with CBSC Trading API
    """

    def __init__(
        self,
        base_url: str = "https://api.cbsc.com",
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        access_token: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        user_agent: Optional[str] = None,
    ):
        """
        Initialize CBSC API client

        Args:
            base_url: Base URL for the API
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret
            access_token: Pre-existing access token
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
            user_agent: Custom user agent string
        """
        self.base_url = base_url.rstrip('/')
        self.client_id = client_id
        self.client_secret = client_secret
        self.timeout = timeout
        self.max_retries = max_retries

        # Set user agent
        if user_agent is None:
            self.user_agent = f"CBSC-Python-SDK/{__version__}"
        else:
            self.user_agent = user_agent

        # Initialize session
        self.session = requests.Session()
        self._setup_session()

        # Token storage
        self._access_token = access_token
        self._token_expires_at: Optional[datetime] = None
        self._refresh_token: Optional[str] = None

        # Initialize API resources (lazy loading to avoid circular imports)
        self._auth = None
        self._users = None
        self._strategies = None
        self._portfolio = None
        self._market_data = None
        self._backtests = None
        self._webhooks = None

        # Auto-authenticate if credentials provided
        if client_id and client_secret and not access_token:
            self._auto_authenticate()

    @property
    def auth(self):
        """Get authentication resource"""
        if self._auth is None:
            from .resources import AuthResource
            self._auth = AuthResource(self)
        return self._auth

    @property
    def users(self):
        """Get users resource"""
        if self._users is None:
            from .resources import UsersResource
            self._users = UsersResource(self)
        return self._users

    @property
    def strategies(self):
        """Get strategies resource"""
        if self._strategies is None:
            from .resources import StrategiesResource
            self._strategies = StrategiesResource(self)
        return self._strategies

    @property
    def portfolio(self):
        """Get portfolio resource"""
        if self._portfolio is None:
            from .resources import PortfolioResource
            self._portfolio = PortfolioResource(self)
        return self._portfolio

    @property
    def market_data(self):
        """Get market data resource"""
        if self._market_data is None:
            from .resources import MarketDataResource
            self._market_data = MarketDataResource(self)
        return self._market_data

    @property
    def backtests(self):
        """Get backtests resource"""
        if self._backtests is None:
            from .resources import BacktestsResource
            self._backtests = BacktestsResource(self)
        return self._backtests

    @property
    def webhooks(self):
        """Get webhooks resource"""
        if self._webhooks is None:
            from .resources import WebhooksResource
            self._webhooks = WebhooksResource(self)
        return self._webhooks

    def _setup_session(self):
        """Setup HTTP session with retry strategy"""
        retry_strategy = Retry(
            total=self.max_retries,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PUT", "DELETE"],
            backoff_factor=1,
            respect_retry_after_header=True,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Set default headers
        self.session.headers.update({
            "User-Agent": self.user_agent,
            "Content-Type": "application/json",
            "Accept": "application/json",
        })

    def _auto_authenticate(self):
        """Automatically authenticate using client credentials"""
        try:
            token_response = self.auth.get_token()
            self._access_token = token_response.access_token
            self._token_expires_at = datetime.utcnow() + timedelta(seconds=token_response.expires_in)
            self._refresh_token = token_response.refresh_token
            logger.info("Auto-authentication successful")
        except Exception as e:
            logger.warning(f"Auto-authentication failed: {e}")

    def _ensure_valid_token(self):
        """Ensure we have a valid access token"""
        if not self._access_token:
            raise AuthenticationError("No access token available")

        if self._token_expires_at and datetime.utcnow() >= self._token_expires_at:
            if self._refresh_token:
                try:
                    token_response = self.auth.refresh_token(self._refresh_token)
                    self._access_token = token_response.access_token
                    self._token_expires_at = datetime.utcnow() + timedelta(seconds=token_response.expires_in)
                    if token_response.refresh_token:
                        self._refresh_token = token_response.refresh_token
                    logger.info("Token refresh successful")
                except Exception as e:
                    logger.error(f"Token refresh failed: {e}")
                    # Try to get new token with client credentials
                    self._auto_authenticate()
            else:
                self._auto_authenticate()

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Union[Dict[str, Any], str]] = None,
        headers: Optional[Dict[str, str]] = None,
        require_auth: bool = True,
    ) -> requests.Response:
        """
        Make HTTP request to API

        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            data: Request data
            headers: Additional headers
            require_auth: Whether authentication is required

        Returns:
            requests.Response object

        Raises:
            Various CBSCAPIError subclasses based on response
        """
        # Ensure we have a valid token if authentication is required
        if require_auth:
            self._ensure_valid_token()
            self.session.headers["Authorization"] = f"Bearer {self._access_token}"

        # Prepare URL
        url = urljoin(self.base_url + "/", endpoint.lstrip('/'))

        # Prepare request data
        json_data = None
        if data and isinstance(data, dict):
            json_data = data
        elif data and isinstance(data, str):
            json_data = json.loads(data)

        # Prepare headers
        request_headers = {}
        if headers:
            request_headers.update(headers)

        try:
            logger.debug(f"Making {method} request to {url}")
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                headers=request_headers,
                timeout=self.timeout,
            )

            # Handle rate limiting
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                raise RateLimitError(
                    message="Rate limit exceeded",
                    retry_after=int(retry_after) if retry_after else None,
                    response_data=response.json() if response.content else None,
                )

            # Handle other HTTP errors
            if response.status_code >= 400:
                self._handle_error_response(response)

            return response

        except requests.exceptions.Timeout:
            raise TimeoutError()
        except requests.exceptions.ConnectionError:
            raise SDKConnectionError()
        except requests.exceptions.RequestException as e:
            raise CBSCAPIError(f"Request failed: {str(e)}")

    def _handle_error_response(self, response: requests.Response):
        """Handle error responses from API"""
        try:
            error_data = response.json() if response.content else {}
            message = error_data.get("detail", error_data.get("message", f"HTTP {response.status_code}"))
        except (ValueError, KeyError):
            message = f"HTTP {response.status_code}"

        if response.status_code == 401:
            raise AuthenticationError(message, error_data)
        elif response.status_code == 404:
            raise NotFoundError(message, error_data)
        elif response.status_code == 422:
            raise ValidationError(message, error_data)
        elif response.status_code >= 500:
            raise ServerError(message, error_data)
        else:
            raise CBSCAPIError(message, response.status_code, error_data)

    def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        require_auth: bool = True,
    ) -> requests.Response:
        """Make GET request"""
        return self._make_request("GET", endpoint, params=params, headers=headers, require_auth=require_auth)

    def post(
        self,
        endpoint: str,
        data: Optional[Union[Dict[str, Any], str]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        require_auth: bool = True,
    ) -> requests.Response:
        """Make POST request"""
        return self._make_request("POST", endpoint, params=params, data=data, headers=headers, require_auth=require_auth)

    def put(
        self,
        endpoint: str,
        data: Optional[Union[Dict[str, Any], str]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        require_auth: bool = True,
    ) -> requests.Response:
        """Make PUT request"""
        return self._make_request("PUT", endpoint, params=params, data=data, headers=headers, require_auth=require_auth)

    def delete(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        require_auth: bool = True,
    ) -> requests.Response:
        """Make DELETE request"""
        return self._make_request("DELETE", endpoint, params=params, headers=headers, require_auth=require_auth)

    def close(self):
        """Close the HTTP session"""
        if self.session:
            self.session.close()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


class AsyncCBSCClient:
    """
    Async client for interacting with CBSC Trading API
    Note: This is a placeholder for future async implementation
    """

    def __init__(self, *args, **kwargs):
        raise NotImplementedError(
            "Async client not yet implemented. Use CBSCClient for synchronous operations."
        )