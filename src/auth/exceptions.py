"""
Custom Authentication Exceptions
Specific error types for better error handling and user feedback
"""

from typing import Optional, Dict, Any


class AuthenticationError(Exception):
    """Base authentication error"""
    def __init__(self, message: str, code: str = "AUTH_ERROR", details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.code = code
        self.details = details or {}
        self.status_code = 401
        super().__init__(self.message)


class InvalidCredentialsError(AuthenticationError):
    """Invalid username or password"""
    def __init__(self, message: str = "Invalid username or password"):
        super().__init__(message, "INVALID_CREDENTIALS")


class UserNotFoundError(AuthenticationError):
    """User not found"""
    def __init__(self, message: str = "User not found"):
        super().__init__(message, "USER_NOT_FOUND")
        self.status_code = 404


class UserInactiveError(AuthenticationError):
    """User account is inactive"""
    def __init__(self, message: str = "User account is inactive"):
        super().__init__(message, "USER_INACTIVE")


class UserNotVerifiedError(AuthenticationError):
    """User email not verified"""
    def __init__(self, message: str = "Email not verified"):
        super().__init__(message, "USER_NOT_VERIFIED")


class UserLockedError(AuthenticationError):
    """User account is locked"""
    def __init__(self, message: str = "Account is temporarily locked", locked_until: Optional[str] = None):
        details = {}
        if locked_until:
            details["locked_until"] = locked_until
        super().__init__(message, "USER_LOCKED", details)


class TokenExpiredError(AuthenticationError):
    """Token has expired"""
    def __init__(self, message: str = "Token has expired"):
        super().__init__(message, "TOKEN_EXPIRED")


class TokenInvalidError(AuthenticationError):
    """Token is invalid"""
    def __init__(self, message: str = "Invalid token"):
        super().__init__(message, "TOKEN_INVALID")


class RefreshTokenError(AuthenticationError):
    """Refresh token error"""
    def __init__(self, message: str = "Invalid or expired refresh token"):
        super().__init__(message, "REFRESH_TOKEN_ERROR")


class PasswordTooWeakError(AuthenticationError):
    """Password does not meet strength requirements"""
    def __init__(self, message: str = "Password is too weak", requirements: Optional[Dict[str, bool]] = None):
        details = {}
        if requirements:
            details["requirements"] = requirements
        super().__init__(message, "PASSWORD_TOO_WEAK", details)
        self.status_code = 400


class PasswordAlreadyUsedError(AuthenticationError):
    """Password was previously used"""
    def __init__(self, message: str = "Password was recently used"):
        super().__init__(message, "PASSWORD_ALREADY_USED")
        self.status_code = 400


class PasswordResetTokenError(AuthenticationError):
    """Invalid or expired password reset token"""
    def __init__(self, message: str = "Invalid or expired password reset token"):
        super().__init__(message, "PASSWORD_RESET_TOKEN_ERROR")


class EmailVerificationError(AuthenticationError):
    """Email verification error"""
    def __init__(self, message: str = "Email verification failed"):
        super().__init__(message, "EMAIL_VERIFICATION_ERROR")


class MFATokenError(AuthenticationError):
    """MFA token error"""
    def __init__(self, message: str = "Invalid MFA token"):
        super().__init__(message, "MFA_TOKEN_ERROR")


class MFARequiredError(AuthenticationError):
    """MFA is required for this user"""
    def __init__(self, message: str = "Multi-factor authentication required"):
        super().__init__(message, "MFA_REQUIRED")


class MFANotEnabledError(AuthenticationError):
    """MFA is not enabled for this user"""
    def __init__(self, message: str = "MFA is not enabled"):
        super().__init__(message, "MFA_NOT_ENABLED")


class DeviceNotTrustedError(AuthenticationError):
    """Device is not trusted"""
    def __init__(self, message: str = "Device is not trusted"):
        super().__init__(message, "DEVICE_NOT_TRUSTED")


class DeviceBlockedError(AuthenticationError):
    """Device is blocked"""
    def __init__(self, message: str = "Device is blocked"):
        super().__init__(message, "DEVICE_BLOCKED")


class RateLimitExceededError(AuthenticationError):
    """Rate limit exceeded"""
    def __init__(self, message: str = "Too many requests", retry_after: Optional[int] = None):
        details = {}
        if retry_after:
            details["retry_after"] = retry_after
        super().__init__(message, "RATE_LIMIT_EXCEEDED", details)
        self.status_code = 429


class SessionExpiredError(AuthenticationError):
    """Session has expired"""
    def __init__(self, message: str = "Session has expired"):
        super().__init__(message, "SESSION_EXPIRED")


class SessionRevokedError(AuthenticationError):
    """Session has been revoked"""
    def __init__(self, message: str = "Session has been revoked"):
        super().__init__(message, "SESSION_REVOKED")


class AuthorizationError(Exception):
    """Base authorization error"""
    def __init__(self, message: str, code: str = "AUTHORIZATION_ERROR", details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.code = code
        self.details = details or {}
        self.status_code = 403
        super().__init__(self.message)


class PermissionDeniedError(AuthorizationError):
    """Permission denied"""
    def __init__(self, message: str = "Permission denied", permission: Optional[str] = None):
        details = {}
        if permission:
            details["required_permission"] = permission
        super().__init__(message, "PERMISSION_DENIED", details)


class RoleRequiredError(AuthorizationError):
    """Specific role required"""
    def __init__(self, message: str = "Insufficient role", required_role: Optional[str] = None):
        details = {}
        if required_role:
            details["required_role"] = required_role
        super().__init__(message, "ROLE_REQUIRED", details)


class AdminRequiredError(AuthorizationError):
    """Admin privileges required"""
    def __init__(self, message: str = "Admin privileges required"):
        super().__init__(message, "ADMIN_REQUIRED")


class SuperAdminRequiredError(AuthorizationError):
    """Super admin privileges required"""
    def __init__(self, message: str = "Super admin privileges required"):
        super().__init__(message, "SUPER_ADMIN_REQUIRED")


class ResourceAccessDeniedError(AuthorizationError):
    """Access to specific resource denied"""
    def __init__(self, message: str = "Access to resource denied", resource_id: Optional[str] = None):
        details = {}
        if resource_id:
            details["resource_id"] = resource_id
        super().__init__(message, "RESOURCE_ACCESS_DENIED", details)


class InvalidOperationError(Exception):
    """Invalid operation error"""
    def __init__(self, message: str, code: str = "INVALID_OPERATION", details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.code = code
        self.details = details or {}
        self.status_code = 400
        super().__init__(self.message)


class UserAlreadyExistsError(InvalidOperationError):
    """User already exists"""
    def __init__(self, field: str, value: str):
        message = f"User with {field} '{value}' already exists"
        super().__init__(message, "USER_ALREADY_EXISTS", {"field": field, "value": value})


class RoleAlreadyExistsError(InvalidOperationError):
    """Role already exists"""
    def __init__(self, role_name: str):
        message = f"Role '{role_name}' already exists"
        super().__init__(message, "ROLE_ALREADY_EXISTS", {"role_name": role_name})


class PermissionAlreadyExistsError(InvalidOperationError):
    """Permission already exists"""
    def __init__(self, permission_code: str):
        message = f"Permission '{permission_code}' already exists"
        super().__init__(message, "PERMISSION_ALREADY_EXISTS", {"permission_code": permission_code})


class CannotDeleteSystemRoleError(InvalidOperationError):
    """Cannot delete system role"""
    def __init__(self, role_name: str):
        message = f"Cannot delete system role '{role_name}'"
        super().__init__(message, "CANNOT_DELETE_SYSTEM_ROLE", {"role_name": role_name})


class CannotDeleteSystemPermissionError(InvalidOperationError):
    """Cannot delete system permission"""
    def __init__(self, permission_code: str):
        message = f"Cannot delete system permission '{permission_code}'"
        super().__init__(message, "CANNOT_DELETE_SYSTEM_PERMISSION", {"permission_code": permission_code})


class InvalidRoleAssignmentError(InvalidOperationError):
    """Invalid role assignment"""
    def __init__(self, message: str = "Invalid role assignment"):
        super().__init__(message, "INVALID_ROLE_ASSIGNMENT")


class EmailSendError(Exception):
    """Email sending error"""
    def __init__(self, message: str, recipient: Optional[str] = None):
        self.message = message
        self.recipient = recipient
        self.code = "EMAIL_SEND_ERROR"
        self.status_code = 500
        super().__init__(self.message)


class SMSSendError(Exception):
    """SMS sending error"""
    def __init__(self, message: str, phone: Optional[str] = None):
        self.message = message
        self.phone = phone
        self.code = "SMS_SEND_ERROR"
        self.status_code = 500
        super().__init__(self.message)


class ConfigurationError(Exception):
    """Configuration error"""
    def __init__(self, message: str, config_key: Optional[str] = None):
        self.message = message
        self.config_key = config_key
        self.code = "CONFIG_ERROR"
        self.status_code = 500
        super().__init__(self.message)


class DatabaseError(Exception):
    """Database operation error"""
    def __init__(self, message: str, operation: Optional[str] = None):
        self.message = message
        self.operation = operation
        self.code = "DATABASE_ERROR"
        self.status_code = 500
        super().__init__(self.message)


class ExternalServiceError(Exception):
    """External service error"""
    def __init__(self, service: str, message: str, status_code: int = 502):
        self.service = service
        self.message = message
        self.code = f"{service.upper()}_SERVICE_ERROR"
        self.status_code = status_code
        super().__init__(f"{service} service error: {message}")