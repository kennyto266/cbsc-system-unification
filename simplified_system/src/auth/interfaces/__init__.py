#!/usr / bin / env python3
"""
Authentication System Interfaces
认证系统接口

Core interfaces and abstract base classes for the authentication system
认证系统的核心接口和抽象基类
"""

from .auth_result import AuthResult, AuthStatus, Verdict
from .data_authenticity_manager import DataAuthenticityManager
from .verifier_interface import IVerifier

__all__ = [
    "DataAuthenticityManager",
    "IVerifier",
    "AuthResult",
    "AuthStatus",
    "Verdict",
]
