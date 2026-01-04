"""
Authentication API Module
認證 API 模組

Provides v2 authentication endpoints with enhanced security features
提供具有增強安全功能的 v2 認證端點
"""

from .auth_endpoints_v2 import router as auth_v2_router
from .auth_utils import (
    device_fingerprinter,
    security_analyzer,
    password_validator,
    audit_logger
)

__all__ = [
    "auth_v2_router",
    "device_fingerprinter",
    "security_analyzer",
    "password_validator",
    "audit_logger"
]