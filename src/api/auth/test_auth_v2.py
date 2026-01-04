"""
Test Authentication API v2
測試認證 API v2

Test suite for the enhanced authentication endpoints
增強認證端點的測試套件
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import jwt
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import application and modules
from main import app
from auth_simple import User, Base
from src.services.auth_service_v2 import auth_service_v2, MFAType as ServiceMFAType
from src.schemas.auth_schemas import MFAType

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_auth.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

# Override database dependency
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# Mock Redis for testing
class MockRedis:
    def __init__(self):
        self.data = {}

    def get(self, key):
        return self.data.get(key)

    def set(self, key, value, ex=None):
        self.data[key] = value
        return True

    def setex(self, key, time, value):
        self.data[key] = value
        return True

    def delete(self, key):
        return self.data.pop(key, None)

    def exists(self, key):
        return key in self.data

    def zadd(self, key, mapping):
        if key not in self.data:
            self.data[key] = {}
        self.data[key].update(mapping)
        return len(mapping)

    def zcard(self, key):
        return len(self.data.get(key, {}))

    def zremrangebyscore(self, key, min, max):
        if key in self.data:
            self.data[key] = {
                k: v for k, v in self.data[key].items()
                if not (min <= v <= max)
            }
        return 0

    def zrange(self, key, start, end, withscores=False):
        items = list(self.data.get(key, {}).items())
        items.sort(key=lambda x: x[1])
        items = items[start:end+1]
        if withscores:
            return items
        return [k for k, v in items]

    def expire(self, key, seconds):
        # Mock implementation - doesn't actually expire
        return True

# Create test client
client = TestClient(app)

# Setup test data
@pytest.fixture
def test_db():
    """Create test database session"""
    db = TestingSessionLocal()
    try:
        # Create test user
        test_user = User(
            username="testuser",
            email="test@example.com",
            password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6ukx.LFvO6",  # 'password123'
            is_active=True,
            is_verified=True
        )
        db.add(test_user)
        db.commit()

        yield db
    finally:
        db.close()
        # Clean up
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    return MockRedis()

@pytest.fixture
def auth_headers():
    """Get authorization headers for test user"""
    login_data = {
        "username": "testuser",
        "password": "password123",
        "device_fingerprint": "test-device-123"
    }
    response = client.post("/api/v2/auth/login", json=login_data)
    token = response.json()["token_info"]["access_token"]
    return {"Authorization": f"Bearer {token}"}

class TestLogin:
    """Test login endpoints"""

    def test_login_success(self, test_db):
        """Test successful login without MFA"""
        login_data = {
            "username": "testuser",
            "password": "password123",
            "device_fingerprint": "test-device-123"
        }
        response = client.post("/api/v2/auth/login", json=login_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["requires_mfa"] is False
        assert "token_info" in data
        assert "access_token" in data["token_info"]
        assert "refresh_token" in data["token_info"]

    def test_login_with_mfa(self, test_db):
        """Test login with MFA enabled"""
        # Setup MFA for user
        mfa = auth_service_v2.UserMFA(
            user_id=1,
            mfa_type=ServiceMFAType.TOTP,
            secret="JBSWY3DPEHPK3PXP",  # Test secret
            is_enabled=True,
            backup_codes='["ABCD1234", "EFGH5678"]'
        )
        test_db.add(mfa)
        test_db.commit()

        login_data = {
            "username": "testuser",
            "password": "password123",
            "device_fingerprint": "test-device-123"
        }
        response = client.post("/api/v2/auth/login", json=login_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["requires_mfa"] is True
        assert "mfa_challenge_token" in data
        assert MFAType.TOTP in data["mfa_types"]

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        login_data = {
            "username": "testuser",
            "password": "wrongpassword",
            "device_fingerprint": "test-device-123"
        }
        response = client.post("/api/v2/auth/login", json=login_data)

        assert response.status_code == 401
        assert "Invalid username or password" in response.json()["detail"]

    def test_login_rate_limiting(self):
        """Test rate limiting on login attempts"""
        login_data = {
            "username": "testuser",
            "password": "wrongpassword",
            "device_fingerprint": "test-device-123"
        }

        # Make multiple failed attempts
        for _ in range(6):
            response = client.post("/api/v2/auth/login", json=login_data)

        # Should be rate limited
        assert response.status_code == 429
        assert "Too many login attempts" in response.json()["detail"]

class TestMFA:
    """Test MFA endpoints"""

    def test_setup_mfa_totp(self, auth_headers):
        """Test MFA setup for TOTP"""
        setup_data = {
            "mfa_type": MFAType.TOTP
        }
        response = client.post("/api/v2/auth/mfa/setup", json=setup_data, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["mfa_type"] == MFAType.TOTP
        assert "secret" in data
        assert "qr_code" in data
        assert "backup_codes" in data

    def test_verify_mfa_totp(self, test_db, mock_redis):
        """Test MFA verification with TOTP"""
        # Setup MFA first
        mfa = auth_service_v2.UserMFA(
            user_id=1,
            mfa_type=ServiceMFAType.TOTP,
            secret="JBSWY3DPEHPK3PXP",
            is_enabled=True
        )
        test_db.add(mfa)
        test_db.commit()

        # Get MFA challenge token
        login_data = {
            "username": "testuser",
            "password": "password123",
            "device_fingerprint": "test-device-123"
        }
        login_response = client.post("/api/v2/auth/login", json=login_data)
        challenge_token = login_response.json()["mfa_challenge_token"]

        # Verify MFA (using pyotp to generate valid code)
        import pyotp
        totp = pyotp.TOTP("JBSWY3DPEHPK3PXP")
        code = totp.now()

        verify_data = {
            "mfa_challenge_token": challenge_token,
            "code": code
        }

        with patch('src.services.auth_service_v2.redis_client', mock_redis):
            response = client.post("/api/v2/auth/mfa/verify", json=verify_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["requires_mfa"] is False
        assert "token_info" in data

    def test_verify_mfa_backup_code(self, test_db, mock_redis):
        """Test MFA verification with backup code"""
        # Setup MFA with backup codes
        backup_codes = json.dumps(["ABCD1234", "EFGH5678"])
        mfa = auth_service_v2.UserMFA(
            user_id=1,
            mfa_type=ServiceMFAType.TOTP,
            secret="JBSWY3DPEHPK3PXP",
            backup_codes=backup_codes,
            is_enabled=True
        )
        test_db.add(mfa)
        test_db.commit()

        # Get MFA challenge token
        login_data = {
            "username": "testuser",
            "password": "password123",
            "device_fingerprint": "test-device-123"
        }
        login_response = client.post("/api/v2/auth/login", json=login_data)
        challenge_token = login_response.json()["mfa_challenge_token"]

        # Verify with backup code
        verify_data = {
            "mfa_challenge_token": challenge_token,
            "backup_code": "ABCD1234"
        }

        with patch('src.services.auth_service_v2.redis_client', mock_redis):
            response = client.post("/api/v2/auth/mfa/verify", json=verify_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

class TestTokenRefresh:
    """Test token refresh endpoints"""

    def test_refresh_token_success(self, test_db, mock_redis):
        """Test successful token refresh"""
        # Login first to get refresh token
        login_data = {
            "username": "testuser",
            "password": "password123",
            "device_fingerprint": "test-device-123"
        }
        login_response = client.post("/api/v2/auth/login", json=login_data)
        refresh_token = login_response.json()["token_info"]["refresh_token"]

        refresh_data = {
            "refresh_token": refresh_token,
            "device_fingerprint": "test-device-123"
        }

        with patch('src.services.auth_service_v2.redis_client', mock_redis):
            response = client.post("/api/v2/auth/refresh", json=refresh_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "token_info" in data
        assert "access_token" in data["token_info"]
        assert "refresh_token" in data["token_info"]

    def test_refresh_token_invalid(self, mock_redis):
        """Test refresh with invalid token"""
        refresh_data = {
            "refresh_token": "invalid-token",
            "device_fingerprint": "test-device-123"
        }

        with patch('src.services.auth_service_v2.redis_client', mock_redis):
            response = client.post("/api/v2/auth/refresh", json=refresh_data)

        assert response.status_code == 401
        assert "Invalid or expired refresh token" in response.json()["detail"]

class TestLogout:
    """Test logout endpoints"""

    def test_logout_success(self, auth_headers, mock_redis):
        """Test successful logout"""
        with patch('src.services.auth_service_v2.redis_client', mock_redis):
            response = client.post("/api/v2/auth/logout", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Logged out successfully" in data["message"]

class TestPasswordChange:
    """Test password change endpoints"""

    def test_change_password_success(self, auth_headers):
        """Test successful password change"""
        password_data = {
            "old_password": "password123",
            "new_password": "newpassword456",
            "confirm_password": "newpassword456"
        }
        response = client.post("/api/v2/auth/change-password", json=password_data, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_change_password_wrong_old(self, auth_headers):
        """Test password change with wrong old password"""
        password_data = {
            "old_password": "wrongpassword",
            "new_password": "newpassword456",
            "confirm_password": "newpassword456"
        }
        response = client.post("/api/v2/auth/change-password", json=password_data, headers=auth_headers)

        assert response.status_code == 400
        assert "Current password is incorrect" in response.json()["detail"]

    def test_change_password_weak(self, auth_headers):
        """Test password change with weak password"""
        password_data = {
            "old_password": "password123",
            "new_password": "weak",
            "confirm_password": "weak"
        }
        response = client.post("/api/v2/auth/change-password", json=password_data, headers=auth_headers)

        assert response.status_code == 400
        assert "Password is too weak" in response.json()["detail"]

class TestRegistration:
    """Test registration endpoints"""

    def test_register_success(self):
        """Test successful user registration"""
        reg_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "StrongPass123!",
            "confirm_password": "StrongPass123!",
            "accept_terms": True
        }
        response = client.post("/api/v2/auth/register", json=reg_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["user_id"] is not None

    def test_register_username_exists(self):
        """Test registration with existing username"""
        reg_data = {
            "username": "testuser",
            "email": "another@example.com",
            "password": "StrongPass123!",
            "confirm_password": "StrongPass123!",
            "accept_terms": True
        }
        response = client.post("/api/v2/auth/register", json=reg_data)

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    def test_register_weak_password(self):
        """Test registration with weak password"""
        reg_data = {
            "username": "weakuser",
            "email": "weak@example.com",
            "password": "weak",
            "confirm_password": "weak",
            "accept_terms": True
        }
        response = client.post("/api/v2/auth/register", json=reg_data)

        assert response.status_code == 422  # Validation error

class TestProfile:
    """Test profile endpoints"""

    def test_get_profile(self, auth_headers):
        """Test get user profile"""
        response = client.get("/api/v2/auth/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["username"] == "testuser"
        assert "mfa_summary" in data

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])