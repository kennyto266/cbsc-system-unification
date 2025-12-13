"""
業務服務層
Business Service Layer

統一的業務服務入口，包含：
- BaseBusinessService: 統一的業務服務基類
- 具體業務服務實現
"""

# Base service
from .base_business_service import BaseBusinessService

# Strategy services (existing)
from .strategy_service import BaseStrategyService
from .execution_service import ExecutionService
from .personal_service import PersonalService
from .websocket_service import WebSocketService, websocket_manager, get_websocket_service

# New business services
from .user_service import UserService
from .permission_service import PermissionService
from .audit_service import AuditService

# Cache management
from .cache_manager import CacheManager
from .cache_strategy import get_strategy_for_key

__all__ = [
    # Base service
    "BaseBusinessService",

    # Strategy services
    "BaseStrategyService",
    "ExecutionService",
    "PersonalService",
    "WebSocketService",
    "websocket_manager",
    "get_websocket_service",

    # New business services
    "UserService",
    "PermissionService",
    "AuditService",

    # Cache management
    "CacheManager",
    "get_strategy_for_key"
]