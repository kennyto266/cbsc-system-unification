"""
User API v2 Endpoints Tests
用戶 API v2 端點測試

測試用戶管理相關的 API 端點
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from .....main import app

client = TestClient(app)


class TestUserEndpoints:
    """用戶端點測試類"""

    @pytest.fixture
    def mock_user(self):
        """模擬用戶數據"""
        return {
            "id": "test-user-id",
            "username": "testuser",
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "display_name": "Test User",
            "avatar_url": None,
            "phone": "+1234567890",
            "timezone": "UTC",
            "language": "en",
            "theme": "light",
            "is_active": True,
            "is_verified": True,
            "is_premium": False,
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": "2025-01-01T00:00:00Z",
            "last_login_at": None
        }

    @pytest.fixture
    def auth_headers(self):
        """認證頭部"""
        return {"Authorization": "Bearer test-token"}

    @patch('src.api.users.v2.user_endpoints.get_current_user')
    @patch('src.api.users.v2.user_endpoints.UserServiceV2')
    def test_get_user_profile_success(
        self,
        mock_user_service,
        mock_get_current_user,
        mock_user,
        auth_headers
    ):
        """測試成功獲取用戶資料"""
        # Setup mocks
        mock_current_user = Mock()
        mock_current_user.id = mock_user["id"]
        mock_get_current_user.return_value = mock_current_user

        mock_service_instance = Mock()
        mock_service_instance.get_user_profile.return_value = mock_user
        mock_user_service.return_value = mock_service_instance

        # Make request
        response = client.get("/api/v2/users/profile", headers=auth_headers)

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == mock_user["id"]
        assert data["data"]["username"] == mock_user["username"]
        assert data["message"] == "成功獲取用戶資料"

    @patch('src.api.users.v2.user_endpoints.get_current_user')
    @patch('src.api.users.v2.user_endpoints.UserServiceV2')
    def test_update_user_profile_success(
        self,
        mock_user_service,
        mock_get_current_user,
        mock_user,
        auth_headers
    ):
        """測試成功更新用戶資料"""
        # Setup mocks
        mock_current_user = Mock()
        mock_current_user.id = mock_user["id"]
        mock_get_current_user.return_value = mock_current_user

        updated_user = mock_user.copy()
        updated_user["first_name"] = "Updated"

        mock_service_instance = Mock()
        mock_service_instance.update_user_profile.return_value = updated_user
        mock_user_service.return_value = mock_service_instance

        # Request data
        update_data = {
            "first_name": "Updated",
            "phone": "+0987654321"
        }

        # Make request
        response = client.put(
            "/api/v2/users/profile",
            json=update_data,
            headers=auth_headers
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["first_name"] == "Updated"
        assert data["message"] == "用戶資料更新成功"

    @patch('src.api.users.v2.user_endpoints.get_current_user')
    @patch('src.api.users.v2.user_endpoints.UserServiceV2')
    def test_change_password_success(
        self,
        mock_user_service,
        mock_get_current_user,
        mock_user,
        auth_headers
    ):
        """測試成功更改密碼"""
        # Setup mocks
        mock_current_user = Mock()
        mock_current_user.id = mock_user["id"]
        mock_get_current_user.return_value = mock_current_user

        mock_service_instance = Mock()
        mock_service_instance.change_password.return_value = True
        mock_user_service.return_value = mock_service_instance

        # Request data
        password_data = {
            "current_password": "oldpassword123",
            "new_password": "newpassword456",
            "confirm_password": "newpassword456"
        }

        # Make request
        response = client.post(
            "/api/v2/users/change-password",
            json=password_data,
            headers=auth_headers
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "密碼更改成功"

    @patch('src.api.users.v2.user_endpoints.UserServiceV2')
    def test_request_password_reset_success(
        self,
        mock_user_service
    ):
        """測試成功請求密碼重置"""
        # Setup mock
        mock_service_instance = Mock()
        mock_service_instance.request_password_reset.return_value = True
        mock_user_service.return_value = mock_service_instance

        # Request data
        reset_request = {
            "email": "test@example.com"
        }

        # Make request
        response = client.post(
            "/api/v2/users/request-password-reset",
            json=reset_request
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "如果郵箱存在，重置鏈接已發送"

    @patch('src.api.users.v2.user_endpoints.get_current_user')
    @patch('src.api.users.v2.user_endpoints.UserServiceV2')
    def test_get_mfa_settings_success(
        self,
        mock_user_service,
        mock_get_current_user,
        mock_user,
        auth_headers
    ):
        """測試成功獲取 MFA 設置"""
        # Setup mocks
        mock_current_user = Mock()
        mock_current_user.id = mock_user["id"]
        mock_get_current_user.return_value = mock_current_user

        mfa_settings = {
            "mfa_enabled": False,
            "mfa_methods": [],
            "totp_enabled": False,
            "sms_enabled": False,
            "email_enabled": False,
            "phone_number": None,
            "backup_codes_count": 0,
            "last_mfa_used": None
        }

        mock_service_instance = Mock()
        mock_service_instance.get_mfa_settings.return_value = mfa_settings
        mock_user_service.return_value = mock_service_instance

        # Make request
        response = client.get("/api/v2/users/mfa-settings", headers=auth_headers)

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["mfa_enabled"] is False
        assert data["message"] == "成功獲取 MFA 設置"

    @patch('src.api.users.v2.user_endpoints.get_current_user')
    @patch('src.api.users.v2.user_endpoints.UserServiceV2')
    def test_get_user_preferences_success(
        self,
        mock_user_service,
        mock_get_current_user,
        mock_user,
        auth_headers
    ):
        """測試成功獲取用戶偏好設置"""
        # Setup mocks
        mock_current_user = Mock()
        mock_current_user.id = mock_user["id"]
        mock_get_current_user.return_value = mock_current_user

        preferences = {
            "notifications": {
                "email_enabled": True,
                "sms_enabled": False,
                "push_enabled": True,
                "browser_enabled": True,
                "strategy_alerts": True,
                "performance_reports": True,
                "system_updates": True,
                "security_alerts": True,
                "marketing_emails": False
            },
            "dashboard": {
                "default_layout": "grid",
                "show_welcome": True,
                "default_timeframe": "1D",
                "auto_refresh": True,
                "refresh_interval": 30,
                "visible_widgets": [],
                "widget_configurations": {}
            },
            "api": {
                "api_key_enabled": False,
                "api_keys": [],
                "rate_limit_per_hour": 100,
                "ip_whitelist": [],
                "webhook_url": None
            }
        }

        mock_service_instance = Mock()
        mock_service_instance.get_user_preferences.return_value = preferences
        mock_user_service.return_value = mock_service_instance

        # Make request
        response = client.get("/api/v2/users/preferences", headers=auth_headers)

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["notifications"]["email_enabled"] is True
        assert data["message"] == "成功獲取用戶偏好設置"

    def test_unauthorized_access(self):
        """測試未授權訪問"""
        # Make request without auth headers
        response = client.get("/api/v2/users/profile")

        # Assertions
        assert response.status_code == 401

    def test_api_version_endpoint(self):
        """測試 API 版本端點"""
        response = client.get("/api/v2/version")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["version"] == "2.0.0"
        assert data["name"] == "User Management API"

    def test_health_check_endpoint(self):
        """測試健康檢查端點"""
        response = client.get("/api/v2/health")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "2.0.0"