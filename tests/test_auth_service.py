"""
Authentication Service Unit Tests
Comprehensive test suite for authentication functionality
"""

import pytest
import json
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4

from src.auth.service import AuthService
from src.auth.models import User, Role, Permission, UserRole, UserSession
from src.auth.schemas import UserCreate, UserLogin, PasswordChange
from src.auth.exceptions import (
    InvalidCredentialsError, UserNotFoundError, UserInactiveError,
    UserLockedError, PasswordTooWeakError, TokenExpiredError
)
from src.auth.utils import (
    hash_password, verify_password, generate_jwt_tokens,
    verify_jwt_token, validate_password_strength
)


class TestAuthService:
    """Test cases for AuthService"""

    @pytest.fixture
    def auth_service(self):
        """Create auth service for testing"""
        # Use in-memory SQLite for testing
        service = AuthService(database_url="sqlite:///:memory:")
        return service

    @pytest.fixture
    def test_user_data(self):
        """Test user data"""
        return UserCreate(
            username="testuser",
            email="test@cbsc.com",
            password="TestPass123!@#",
            confirm_password="TestPass123!@#",
            first_name="Test",
            last_name="User"
        )

    @pytest.fixture
    def db_session(self, auth_service):
        """Create database session"""
        db = auth_service.get_db()
        try:
            yield db
        finally:
            db.close()

    def test_create_user_success(self, auth_service, test_user_data, db_session):
        """Test successful user creation"""
        user = auth_service.create_user(test_user_data, db_session)

        assert user.username == test_user_data.username
        assert user.email == test_user_data.email
        assert user.is_active is True
        assert user.is_verified is False
        assert user.failed_login_attempts == 0

    def test_create_user_duplicate_username(self, auth_service, test_user_data, db_session):
        """Test user creation with duplicate username"""
        # Create first user
        auth_service.create_user(test_user_data, db_session)

        # Try to create with same username
        with pytest.raises(Exception):  # UserAlreadyExistsError
            auth_service.create_user(test_user_data, db_session)

    def test_create_user_weak_password(self, auth_service, test_user_data, db_session):
        """Test user creation with weak password"""
        test_user_data.password = "weak"
        test_user_data.confirm_password = "weak"

        with pytest.raises(PasswordTooWeakError):
            auth_service.create_user(test_user_data, db_session)

    def test_authenticate_user_success(self, auth_service, test_user_data, db_session):
        """Test successful user authentication"""
        # Create user
        user = auth_service.create_user(test_user_data, db_session)

        # Authenticate
        auth_user, session_data = auth_service.authenticate_user(
            test_user_data.username,
            test_user_data.password,
            "127.0.0.1",
            "Mozilla/5.0"
        )

        assert auth_user.id == user.id
        assert auth_user.username == user.username
        assert "access_token" in session_data
        assert "refresh_token" in session_data
        assert session_data["user"].username == user.username

    def test_authenticate_user_invalid_password(self, auth_service, test_user_data, db_session):
        """Test authentication with invalid password"""
        # Create user
        auth_service.create_user(test_user_data, db_session)

        # Try to authenticate with wrong password
        with pytest.raises(InvalidCredentialsError):
            auth_service.authenticate_user(
                test_user_data.username,
                "wrongpassword",
                "127.0.0.1"
            )

    def test_authenticate_user_not_found(self, auth_service):
        """Test authentication with non-existent user"""
        with pytest.raises(InvalidCredentialsError):
            auth_service.authenticate_user(
                "nonexistent",
                "password",
                "127.0.0.1"
            )

    def test_authenticate_user_account_locked(self, auth_service, test_user_data, db_session):
        """Test authentication with locked account"""
        # Create user
        user = auth_service.create_user(test_user_data, db_session)

        # Lock account
        user.failed_login_attempts = 5
        user.locked_until = datetime.utcnow() + timedelta(minutes=30)
        db_session.commit()

        # Try to authenticate
        with pytest.raises(UserLockedError):
            auth_service.authenticate_user(
                test_user_data.username,
                test_user_data.password,
                "127.0.0.1"
            )

    def test_authenticate_user_inactive(self, auth_service, test_user_data, db_session):
        """Test authentication with inactive user"""
        # Create user
        user = auth_service.create_user(test_user_data, db_session)

        # Deactivate user
        user.is_active = False
        db_session.commit()

        # Try to authenticate
        with pytest.raises(UserInactiveError):
            auth_service.authenticate_user(
                test_user_data.username,
                test_user_data.password,
                "127.0.0.1"
            )

    def test_refresh_token_success(self, auth_service, test_user_data, db_session):
        """Test successful token refresh"""
        # Create and authenticate user
        auth_service.create_user(test_user_data, db_session)
        _, session_data = auth_service.authenticate_user(
            test_user_data.username,
            test_user_data.password,
            "127.0.0.1"
        )

        # Refresh token
        refresh_data = {
            "refresh_token": session_data["refresh_token"]
        }
        new_tokens = auth_service.refresh_token(
            session_data["refresh_token"],
            db_session
        )

        assert "access_token" in new_tokens
        assert "refresh_token" in new_tokens
        assert new_tokens["access_token"] != session_data["access_token"]

    def test_change_password_success(self, auth_service, test_user_data, db_session):
        """Test successful password change"""
        # Create user
        user = auth_service.create_user(test_user_data, db_session)

        # Change password
        success = auth_service.change_password(
            user,
            test_user_data.password,
            "NewPass123!@#",
            db_session
        )

        assert success is True

        # Verify new password works
        auth_user, _ = auth_service.authenticate_user(
            test_user_data.username,
            "NewPass123!@#",
            "127.0.0.1"
        )
        assert auth_user.id == user.id

    def test_change_password_wrong_old(self, auth_service, test_user_data, db_session):
        """Test password change with wrong old password"""
        # Create user
        user = auth_service.create_user(test_user_data, db_session)

        # Try to change with wrong old password
        success = auth_service.change_password(
            user,
            "wrongoldpassword",
            "NewPass123!@#",
            db_session
        )

        assert success is False


class TestPasswordUtils:
    """Test password utility functions"""

    def test_hash_password(self):
        """Test password hashing"""
        password = "TestPass123!@#"
        hashed = hash_password(password)

        assert hashed != password
        assert isinstance(hashed, str)

    def test_verify_password(self):
        """Test password verification"""
        password = "TestPass123!@#"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True
        assert verify_password("wrongpassword", hashed) is False

    def test_generate_jwt_tokens(self):
        """Test JWT token generation"""
        user_id = str(uuid4())
        username = "testuser"
        permissions = ["user.read", "user.update"]
        roles = ["trader"]

        # Generate keys for testing
        from src.auth.utils import generate_rsa_keys
        private_key, public_key = generate_rsa_keys()

        access_token, refresh_token, payload = generate_jwt_tokens(
            user_id,
            username,
            private_key,
            permissions,
            roles
        )

        assert isinstance(access_token, str)
        assert isinstance(refresh_token, str)
        assert payload["sub"] == username
        assert payload["user_id"] == user_id
        assert payload["permissions"] == permissions
        assert payload["roles"] == roles

    def test_verify_jwt_token(self):
        """Test JWT token verification"""
        user_id = str(uuid4())
        username = "testuser"

        # Generate keys for testing
        from src.auth.utils import generate_rsa_keys
        private_key, public_key = generate_rsa_keys()

        # Generate token
        access_token, _, _ = generate_jwt_tokens(user_id, username, private_key)

        # Verify token
        payload = verify_jwt_token(access_token, public_key)

        assert payload["sub"] == username
        assert payload["user_id"] == user_id

    def test_validate_password_strength(self):
        """Test password strength validation"""
        # Strong password
        result = validate_password_strength("StrongPass123!@#", "testuser", "test@example.com")
        assert result["is_valid"] is True
        assert result["strength"] in ["good", "strong"]

        # Weak password
        result = validate_password_strength("weak", "testuser", "test@example.com")
        assert result["is_valid"] is False
        assert result["strength"] == "weak"

        # Password same as username
        result = validate_password_strength("testuser", "testuser")
        assert result["requirements"]["not_username"] is False


class TestAuthAPI:
    """Test authentication API endpoints"""

    @pytest.fixture
    def client(self):
        """Create FastAPI test client"""
        from fastapi.testclient import TestClient
        from src.auth_service_main import create_app

        app = create_app()
        return TestClient(app)

    @pytest.fixture
    def auth_headers(self, client):
        """Get authentication headers"""
        # Register user
        register_data = {
            "username": "testuser",
            "email": "test@cbsc.com",
            "password": "TestPass123!@#",
            "confirm_password": "TestPass123!@#",
            "first_name": "Test",
            "last_name": "User"
        }
        client.post("/api/auth/register", json=register_data)

        # Login
        login_data = {
            "username": "testuser",
            "password": "TestPass123!@#"
        }
        response = client.post("/api/auth/login", json=login_data)
        token = response.json()["access_token"]

        return {"Authorization": f"Bearer {token}"}

    def test_register_user(self, client):
        """Test user registration endpoint"""
        register_data = {
            "username": "newuser",
            "email": "newuser@cbsc.com",
            "password": "NewPass123!@#",
            "confirm_password": "NewPass123!@#",
            "first_name": "New",
            "last_name": "User"
        }

        response = client.post("/api/auth/register", json=register_data)

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@cbsc.com"
        assert "password_hash" not in data

    def test_register_user_weak_password(self, client):
        """Test registration with weak password"""
        register_data = {
            "username": "newuser",
            "email": "newuser@cbsc.com",
            "password": "weak",
            "confirm_password": "weak"
        }

        response = client.post("/api/auth/register", json=register_data)

        assert response.status_code == 400

    def test_login_user(self, client):
        """Test user login endpoint"""
        # Register first
        register_data = {
            "username": "loginuser",
            "email": "login@cbsc.com",
            "password": "LoginPass123!@#",
            "confirm_password": "LoginPass123!@#"
        }
        client.post("/api/auth/register", json=register_data)

        # Login
        login_data = {
            "username": "loginuser",
            "password": "LoginPass123!@#"
        }
        response = client.post("/api/auth/login", json=login_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials"""
        login_data = {
            "username": "nonexistent",
            "password": "wrongpassword"
        }
        response = client.post("/api/auth/login", json=login_data)

        assert response.status_code == 401

    def test_get_current_user(self, client, auth_headers):
        """Test getting current user info"""
        response = client.get("/api/auth/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"

    def test_get_current_user_unauthorized(self, client):
        """Test getting current user without auth"""
        response = client.get("/api/auth/me")

        assert response.status_code == 401

    def test_logout_user(self, client, auth_headers):
        """Test user logout"""
        response = client.post("/api/auth/logout", headers=auth_headers)

        assert response.status_code == 200
        assert response.json()["message"] == "Logged out successfully"

    def test_change_password(self, client, auth_headers):
        """Test password change"""
        password_data = {
            "old_password": "TestPass123!@#",
            "new_password": "NewPass456!@#",
            "confirm_password": "NewPass456!@#"
        }
        response = client.post("/api/auth/change-password", json=password_data, headers=auth_headers)

        assert response.status_code == 200

    def test_validate_password(self, client):
        """Test password validation endpoint"""
        password_data = {
            "password": "StrongPass123!@#"
        }
        response = client.post("/api/auth/validate-password", json=password_data)

        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True

    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/api/auth/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestSecurityFeatures:
    """Test security features"""

    def test_rate_limiting(self, client):
        """Test rate limiting functionality"""
        # Make multiple login attempts quickly
        login_data = {
            "username": "test",
            "password": "wrong"
        }

        # First few attempts should work
        for _ in range(10):
            response = client.post("/api/auth/login", json=login_data)
            assert response.status_code in [401, 429]

        # Eventually should be rate limited
        response = client.post("/api/auth/login", json=login_data)
        assert response.status_code == 429
        assert "rate limit" in response.json()["detail"].lower()

    def test_account_lockout(self, client):
        """Test account lockout after failed attempts"""
        # Register user
        register_data = {
            "username": "lockoutuser",
            "email": "lockout@cbsc.com",
            "password": "LockoutPass123!@#",
            "confirm_password": "LockoutPass123!@#"
        }
        client.post("/api/auth/register", json=register_data)

        # Make failed login attempts
        login_data = {
            "username": "lockoutuser",
            "password": "wrongpassword"
        }

        # Make multiple failed attempts
        for _ in range(5):
            response = client.post("/api/auth/login", json=login_data)
            assert response.status_code == 401

        # Next attempt should say account is locked
        response = client.post("/api/auth/login", json=login_data)
        assert response.status_code == 401
        assert "locked" in response.json()["detail"].lower()

    def test_jwt_token_expiration(self):
        """Test JWT token expiration"""
        from src.auth.utils import generate_rsa_keys, generate_jwt_tokens, verify_jwt_token

        user_id = str(uuid4())
        username = "testuser"
        private_key, public_key = generate_rsa_keys()

        # Generate expired token
        with patch('src.auth.utils.datetime') as mock_datetime:
            # Set initial time
            now = datetime.utcnow()
            mock_datetime.utcnow.return_value = now

            access_token, _, _ = generate_jwt_tokens(user_id, username, private_key)

            # Fast forward time
            mock_datetime.utcnow.return_value = now + timedelta(minutes=31)

            # Token should be expired
            with pytest.raises(Exception):  # TokenExpiredError
                verify_jwt_token(access_token, public_key)

    def test_mfa_setup(self):
        """Test MFA setup functionality"""
        from src.auth.utils import generate_mfa_secret, generate_mfa_qr_code, verify_mfa_token

        # Generate MFA secret
        secret = generate_mfa_secret()
        assert isinstance(secret, str)
        assert len(secret) > 0

        # Generate QR code
        qr_code = generate_mfa_qr_code("test@cbsc.com", secret)
        assert isinstance(qr_code, str)
        assert qr_code.startswith("data:image/png;base64,")

        # Test MFA token verification (would need actual token in real test)
        # This is a simplified test
        assert verify_mfa_token(secret, "123456") is False  # Random token won't match


# Integration tests
class TestIntegration:
    """Integration tests for complete workflows"""

    def test_user_lifecycle(self, auth_service, db_session):
        """Test complete user lifecycle"""
        # Create user
        user_data = UserCreate(
            username="lifecycle",
            email="lifecycle@cbsc.com",
            password="LifePass123!@#",
            confirm_password="LifePass123!@#"
        )
        user = auth_service.create_user(user_data, db_session)

        # Authenticate
        auth_user, session_data = auth_service.authenticate_user(
            user.username,
            "LifePass123!@#",
            "127.0.0.1"
        )
        assert auth_user.id == user.id

        # Change password
        auth_service.change_password(
            auth_user,
            "LifePass123!@#",
            "NewPass456!@#",
            db_session
        )

        # Login with new password
        auth_user2, _ = auth_service.authenticate_user(
            user.username,
            "NewPass456!@#",
            "127.0.0.1"
        )
        assert auth_user2.id == user.id

        # Logout
        success = auth_service.logout_user(session_data["session_token"], db_session)
        assert success is True

    def test_role_based_access(self, auth_service, db_session):
        """Test role-based access control"""
        # This would test RBAC functionality
        # Implementation depends on specific RBAC requirements
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])