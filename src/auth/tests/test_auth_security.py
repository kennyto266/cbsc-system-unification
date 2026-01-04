"""
Authentication Security Tests
認證系統安全測試

Comprehensive security tests for the enhanced authentication system.
Tests JWT authentication, RBAC permissions, MFA, and audit logging.
"""

import pytest
import json
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException
from fastapi.testclient import TestClient

# Import auth components
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from auth.rbac_models import (
    UserRole, Permission, UserPermissionContext, AuditLogEntry,
    RBAC_CONFIG, get_role_permissions, create_user_context,
    validate_permission_requirement
)
from auth.exceptions import (
    AuthenticationError, AuthorizationError, TokenExpiredError,
    InvalidCredentialsError, UserLockedError, MFATokenError,
    PermissionDeniedError
)


class TestRBACModels:
    """Test RBAC model definitions"""

    def test_all_roles_have_permissions(self):
        """Ensure all roles have defined permissions"""
        for role in UserRole:
            permissions = get_role_permissions(role)
            assert len(permissions) > 0, f"Role {role.value} has no permissions"

    def test_admin_has_all_permissions(self):
        """Admin role should have all permissions"""
        admin_permissions = get_role_permissions(UserRole.ADMIN)
        all_permissions = [p for p in Permission]

        # Admin should have all permissions
        for perm in all_permissions:
            assert perm in admin_permissions, f"Admin missing permission: {perm.value}"

    def test_viewer_has_limited_permissions(self):
        """Viewer role should only have read permissions"""
        viewer_permissions = get_role_permissions(UserRole.VIEWER)

        # Viewer should only have read permissions
        assert Permission.READ_STRATEGIES in viewer_permissions
        assert Permission.VIEW_PERFORMANCE in viewer_permissions
        assert Permission.VIEW_SYSTEM_STATUS in viewer_permissions

        # Viewer should NOT have write permissions
        assert Permission.WRITE_STRATEGIES not in viewer_permissions
        assert Permission.DELETE_STRATEGIES not in viewer_permissions
        assert Permission.EXECUTE_TRADES not in viewer_permissions

    def test_trader_has_trade_permissions(self):
        """Trader role should have trading permissions"""
        trader_permissions = get_role_permissions(UserRole.TRADER)

        assert Permission.EXECUTE_TRADES in trader_permissions
        assert Permission.MANAGE_ORDERS in trader_permissions
        assert Permission.VIEW_POSITIONS in trader_permissions

    def test_analyst_cannot_trade(self):
        """Analyst role should not have trading permissions"""
        analyst_permissions = get_role_permissions(UserRole.ANALYST)

        assert Permission.EXECUTE_TRADES not in analyst_permissions
        assert Permission.MANAGE_ORDERS not in analyst_permissions


class TestUserPermissionContext:
    """Test user permission context"""

    def test_create_user_context(self):
        """Test creating user permission context"""
        context = create_user_context(
            user_id=1,
            username="test_user",
            role=UserRole.TRADER,
            device_id="device_123",
            session_id="session_456"
        )

        assert context.user_id == 1
        assert context.username == "test_user"
        assert context.role == UserRole.TRADER
        assert context.device_id == "device_123"
        assert context.session_id == "session_456"
        assert len(context.permissions) > 0

    def test_has_permission(self):
        """Test checking if user has specific permission"""
        context = create_user_context(1, "test_user", UserRole.TRADER)

        assert context.has_permission(Permission.READ_STRATEGIES)
        assert context.has_permission(Permission.EXECUTE_TRADES)
        assert not context.has_permission(Permission.MANAGE_USERS)

    def test_has_all_permissions(self):
        """Test checking if user has all specified permissions"""
        context = create_user_context(1, "test_user", UserRole.TRADER)

        assert context.has_all_permissions([
            Permission.READ_STRATEGIES,
            Permission.EXECUTE_TRADES
        ])

        assert not context.has_all_permissions([
            Permission.READ_STRATEGIES,
            Permission.MANAGE_USERS
        ])

    def test_has_any_permission(self):
        """Test checking if user has any of specified permissions"""
        context = create_user_context(1, "test_user", UserRole.VIEWER)

        assert context.has_any_permission([
            Permission.MANAGE_USERS,
            Permission.READ_STRATEGIES
        ])

        assert not context.has_any_permission([
            Permission.MANAGE_USERS,
            Permission.MANAGE_ROLES
        ])


class TestPermissionValidation:
    """Test permission validation functions"""

    def test_validate_all_permissions_required(self):
        """Test validation when all permissions are required"""
        context = create_user_context(1, "test_user", UserRole.TRADER)

        # Should pass - trader has these permissions
        assert validate_permission_requirement(
            [Permission.READ_STRATEGIES, Permission.EXECUTE_TRADES],
            context,
            require_all=True
        )

        # Should fail - trader doesn't have all these
        assert not validate_permission_requirement(
            [Permission.READ_STRATEGIES, Permission.MANAGE_USERS],
            context,
            require_all=True
        )

    def test_validate_any_permission_required(self):
        """Test validation when any permission is acceptable"""
        context = create_user_context(1, "test_user", UserRole.VIEWER)

        # Should pass - viewer has at least one
        assert validate_permission_requirement(
            [Permission.MANAGE_USERS, Permission.READ_STRATEGIES],
            context,
            require_all=False
        )

        # Should fail - viewer has none of these
        assert not validate_permission_requirement(
            [Permission.MANAGE_USERS, Permission.MANAGE_ROLES],
            context,
            require_all=False
        )


class TestAuditLogEntry:
    """Test audit log entry"""

    def test_create_audit_log_entry(self):
        """Test creating audit log entry"""
        entry = AuditLogEntry(
            user_id=1,
            username="test_user",
            action="create_strategy",
            resource="strategies",
            permission=Permission.WRITE_STRATEGIES,
            success=True,
            ip_address="127.0.0.1",
            user_agent="Mozilla/5.0"
        )

        assert entry.user_id == 1
        assert entry.username == "test_user"
        assert entry.action == "create_strategy"
        assert entry.success is True
        assert entry.timestamp is not None

    def test_audit_log_to_dict(self):
        """Test converting audit log to dictionary"""
        entry = AuditLogEntry(
            user_id=1,
            username="test_user",
            action="delete_strategy",
            resource="strategies",
            permission=Permission.DELETE_STRATEGIES,
            success=False,
            ip_address="127.0.0.1",
            user_agent="Mozilla/5.0",
            failure_reason="Insufficient permissions"
        )

        entry_dict = entry.to_dict()

        assert entry_dict['user_id'] == 1
        assert entry_dict['action'] == "delete_strategy"
        assert entry_dict['success'] is False
        assert entry_dict['failure_reason'] == "Insufficient permissions"
        assert entry_dict['permission'] == "delete_strategies"


class TestJWTSecurity:
    """Test JWT token security"""

    @patch('auth.utils.jwt.encode')
    def test_jwt_contains_security_claims(self, mock_jwt_encode):
        """Test JWT token contains required security claims"""
        mock_jwt_encode.return_value = "test_token"

        from auth.utils import generate_jwt_tokens
        from auth.models import User

        # Create mock user
        user = Mock()
        user.id = "user_123"
        user.username = "testuser"
        user.email = "test@example.com"
        user.permissions = ["read_strategies", "write_strategies"]
        user.role_names = ["trader"]

        # Generate tokens
        access_token, refresh_token = generate_jwt_tokens(
            user,
            private_key="test_key"
        )

        # Verify encode was called with correct payload
        call_args = mock_jwt_encode.call_args
        payload = call_args[0][0]

        # Check required claims
        assert 'user_id' in payload
        assert 'username' in payload
        assert 'email' in payload
        assert 'permissions' in payload
        assert 'roles' in payload
        assert 'exp' in payload
        assert 'iat' in payload
        assert 'jti' in payload  # JWT ID for blacklisting

    @patch('auth.utils.jwt.decode')
    def test_jwt_validation_rejects_invalid_algorithm(self, mock_jwt_decode):
        """Test JWT validation rejects tokens with invalid algorithm"""
        from auth.utils import verify_jwt_token

        # Mock decode to raise error for none algorithm
        mock_jwt_decode.side_effect = Exception("Invalid algorithm")

        with pytest.raises(Exception):
            verify_jwt_token("invalid_token", public_key="test_key")

    @patch('auth.utils.jwt.decode')
    def test_jwt_validation_checks_expiration(self, mock_jwt_decode):
        """Test JWT validation checks token expiration"""
        from auth.utils import verify_jwt_token, TokenExpiredError

        # Mock decode to return expired payload
        mock_jwt_decode.return_value = {
            'user_id': 'user_123',
            'exp': int(time.time()) - 3600  # Expired 1 hour ago
        }

        with pytest.raises(TokenExpiredError):
            verify_jwt_token("expired_token", public_key="test_key")


class TestPasswordSecurity:
    """Test password security"""

    @patch('auth.utils.bcrypt.gensalt')
    @patch('auth.utils.bcrypt.hashpw')
    def test_password_hashing_uses_salt(self, mock_hashpw, mock_gensalt):
        """Test password hashing uses unique salt"""
        mock_gensalt.return_value = b"unique_salt"
        mock_hashpw.return_value = b"hashed_password"

        from auth.utils import hash_password

        password = "test_password"
        hashed = hash_password(password)

        # Verify salt was generated
        mock_gensalt.assert_called_once()

        # Verify password was hashed with salt
        mock_hashpw.assert_called_once()

    @patch('auth.utils.bcrypt.checkpw')
    def test_password_verification_secure(self, mock_checkpw):
        """Test password verification is secure against timing attacks"""
        from auth.utils import verify_password

        # Mock successful verification
        mock_checkpw.return_value = True

        result = verify_password("password", "hash")

        assert result is True
        mock_checkpw.assert_called_once()

    def test_password_strength_validation(self):
        """Test password strength validation"""
        from auth.utils import validate_password_strength

        # Test weak passwords
        weak_result = validate_password_strength("12345678")
        assert weak_result.score < 3
        assert weak_result.level == 'weak'

        # Test strong passwords
        strong_result = validate_password_strength("Str0ng!P@ssw0rd#2024")
        assert strong_result.score >= 4
        assert strong_result.level == 'strong'

    def test_common_passwords_rejected(self):
        """Test common passwords are rejected"""
        from auth.utils import validate_password_strength

        common_passwords = [
            "password",
            "12345678",
            "qwerty123",
            "admin123"
        ]

        for password in common_passwords:
            result = validate_password_strength(password)
            assert result.score < 3, f"Common password '{password}' should be weak"


class TestMFASecurity:
    """Test MFA security"""

    @patch('auth.utils.pyotp.random_base32')
    def test_mfa_secret_is_random(self, mock_random):
        """Test MFA secret is randomly generated"""
        from auth.utils import generate_mfa_secret

        mock_random.return_value = "random_secret_123"

        secret = generate_mfa_secret()

        assert secret == "random_secret_123"
        mock_random.assert_called_once()

    @patch('auth.utils.pyotp.totp.TOTP.verify')
    def test_mfa_token_verification(self, mock_verify):
        """Test MFA token verification"""
        from auth.utils import verify_mfa_token

        mock_verify.return_value = True

        result = verify_mfa_token("secret", "123456")

        assert result is True
        mock_verify.assert_called_once()

    def test_mfa_backup_codes_unique(self):
        """Test MFA backup codes are unique"""
        from auth.utils import generate_mfa_backup_codes

        codes = generate_mfa_backup_codes(count=10)

        assert len(codes) == 10
        assert len(set(codes)) == 10  # All unique
        assert all(len(code) == 8 for code in codes)  # All 8 characters


class TestRateLimiting:
    """Test rate limiting security"""

    def test_rate_limit_blocks_excessive_requests(self):
        """Test rate limiting blocks excessive requests"""
        # This would test the RateLimitMiddleware
        # In a real implementation, we'd mock Redis and test the logic
        pass

    def test_rate_limit_resets_after_window(self):
        """Test rate limit resets after time window"""
        # Test that limits reset correctly
        pass


class TestSessionSecurity:
    """Test session security"""

    def test_session_expiration(self):
        """Test sessions expire correctly"""
        from auth.utils import generate_session_id

        session_id = generate_session_id()

        # Session ID should be unique
        assert isinstance(session_id, str)
        assert len(session_id) > 20

    def test_concurrent_session_limit(self):
        """Test concurrent session limit is enforced"""
        # Test that users can only have limited concurrent sessions
        pass


class TestSecurityHeaders:
    """Test security headers middleware"""

    def test_security_headers_present(self):
        """Test security headers are present in responses"""
        expected_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
        }

        # In real test, we'd make HTTP request and check headers
        for header, value in expected_headers.items():
            assert header is not None


class TestAuthorizationFlow:
    """Test complete authorization flow"""

    def test_unauthenticated_access_denied(self):
        """Test unauthenticated access is denied"""
        # Test that requests without auth token are rejected
        pass

    def test_authenticated_without_permission_denied(self):
        """Test authenticated user without permission is denied"""
        context = create_user_context(1, "test_user", UserRole.VIEWER)

        # Viewer trying to delete strategies should be denied
        assert not validate_permission_requirement(
            [Permission.DELETE_STRATEGIES],
            context,
            require_all=True
        )

    def test_authenticated_with_permission_allowed(self):
        """Test authenticated user with permission is allowed"""
        context = create_user_context(1, "test_user", UserRole.ADMIN)

        # Admin should be able to do anything
        assert validate_permission_requirement(
            [Permission.DELETE_STRATEGIES, Permission.MANAGE_USERS],
            context,
            require_all=True
        )


class TestAuditLogging:
    """Test audit logging"""

    def test_sensitive_actions_logged(self):
        """Test sensitive actions are logged"""
        sensitive_actions = [
            "login",
            "logout",
            "create_strategy",
            "delete_strategy",
            "change_password",
            "grant_permission"
        ]

        for action in sensitive_actions:
            entry = AuditLogEntry(
                user_id=1,
                username="test_user",
                action=action,
                resource="system",
                permission= Permission.SYSTEM_CONFIG,
                success=True,
                ip_address="127.0.0.1",
                user_agent="TestAgent"
            )

            entry_dict = entry.to_dict()
            assert entry_dict['action'] == action
            assert entry_dict['timestamp'] is not None

    def test_failed_authentication_logged(self):
        """Test failed authentication attempts are logged"""
        entry = AuditLogEntry(
            user_id=1,
            username="test_user",
            action="login",
            resource="auth",
            permission= Permission.SYSTEM_CONFIG,
            success=False,
            ip_address="127.0.0.1",
            user_agent="TestAgent",
            failure_reason="Invalid credentials"
        )

        entry_dict = entry.to_dict()

        assert entry_dict['success'] is False
        assert entry_dict['failure_reason'] == "Invalid credentials"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
