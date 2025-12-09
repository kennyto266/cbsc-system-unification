"""
訪問控制中間件
為FastAPI應用提供RBAC、ABAC、MFA、會話管理和API訪問控制集成
"""

import json
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import Depends, HTTPException, Request, Response, status
from fastapi.middleware.base import BaseHTTPMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.middleware.base import RequestHandler
from starlette.responses import JSONResponse

from .abac import ABACManager, Context
from .api_access import APIAccessManager
from .mfa import MFAManager
from .rbac import RBACManager
from .session import SessionManager, TokenManager

logger = logging.getLogger(__name__)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """認證中間件"""

    def __init__(
        self,
        app,
        rbac_manager: RBACManager,
        mfa_manager: MFAManager,
        session_manager: SessionManager,
        require_mfa: bool = True,
    ):
        super().__init__(app)
        self.rbac_manager = rbac_manager
        self.mfa_manager = mfa_manager
        self.session_manager = session_manager
        self.require_mfa = require_mfa
        self.security = HTTPBearer(auto_error=False)

    async def dispatch(self, request: Request, call_next):
        """處理認證"""
        start_time = time.time()

        # 跳過公開端點
        if self._is_public_endpoint(request.url.path):
            return await call_next(request)

        # 嘗試認證
        credentials = await self.security(request)
        user = None
        session = None

        if credentials:
            # Bearer token認證
            payload = self.session_manager.token_manager.verify_token(
                credentials.credentials
            )
            if payload:
                user_id = payload.get("user_id")
                session_id = payload.get("session_id")
                if user_id and session_id:
                    session = self.session_manager.get_session(session_id)
                    if session and session.status.value == "active":
                        user = {
                            "user_id": user_id,
                            "session_id": session_id,
                            "roles": self.rbac_manager.get_user_roles(user_id),
                        }
        elif "X - Session - ID" in request.headers:
            # Session ID認證
            session_id = request.headers["X - Session - ID"]
            session = self.session_manager.get_session(session_id)
            if session and session.status.value == "active":
                user = {
                    "user_id": session.user_id,
                    "session_id": session_id,
                    "roles": self.rbac_manager.get_user_roles(session.user_id),
                }

        # 檢查認證
        if not user:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": "unauthorized",
                    "message": "需要認證",
                    "code": "AUTHENTICATION_REQUIRED",
                },
            )

        # 檢查MFA
        if self.require_mfa and not self._is_mfa_exempt(request, user):
            mfa_methods = self.mfa_manager.get_user_mfa_methods(user["user_id"])
            if not mfa_methods:
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={
                        "error": "mfa_required",
                        "message": "需要設置MFA",
                        "code": "MFA_REQUIRED",
                    },
                )

        # 更新會話活動
        if session:
            self.session_manager.update_activity(session.session_id)

        # 將用戶信息附加到請求
        request.state.user = user
        request.state.session = session

        # 處理請求
        response = await call_next(request)

        # 記錄處理時間
        process_time = time.time() - start_time
        response.headers["X - Process - Time"] = str(process_time)

        return response

    def _is_public_endpoint(self, path: str) -> bool:
        """檢查是否為公開端點"""
        public_endpoints = [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/api / v1 / public/",
            "/auth / login",
            "/auth / register",
            "/auth / verify",
        ]
        return any(path.startswith(ep) for ep in public_endpoints)

    def _is_mfa_exempt(self, request: Request, user: Dict[str, Any]) -> bool:
        """檢查是否免除MFA"""
        # 信任設備可以免除MFA
        if "X - Device - ID" in request.headers:
            device_id = request.headers["X - Device - ID"]
            devices = self.mfa_manager.get_user_devices(user["user_id"])
            for device in devices:
                if device.device_id == device_id and device.is_trusted:
                    return True
        return False


class AuthorizationMiddleware(BaseHTTPMiddleware):
    """授權中間件"""

    def __init__(self, app, rbac_manager: RBACManager, abac_manager: ABACManager):
        super().__init__(app)
        self.rbac_manager = rbac_manager
        self.abac_manager = abac_manager

    async def dispatch(self, request: Request, call_next):
        """處理授權"""
        if not hasattr(request.state, "user"):
            return await call_next(request)

        user = request.state.user
        method = request.method
        path = request.url.path

        # RBAC檢查
        if not self._check_rbac(user, method, path):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "error": "forbidden",
                    "message": "權限不足",
                    "code": "INSUFFICIENT_PERMISSION",
                },
            )

        # ABAC檢查
        context = self._build_abac_context(request, user)
        if context:
            abac_result = await self.abac_manager.evaluate_access(context)
            if abac_result.value == "deny":
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={
                        "error": "forbidden",
                        "message": "基於屬性的訪問控制拒絕",
                        "code": "ABAC_DENY",
                    },
                )

        return await call_next(request)

    def _check_rbac(self, user: Dict[str, Any], method: str, path: str) -> bool:
        """RBAC權限檢查"""
        # 簡化的權限檢查邏輯
        # 實際實現中需要根據端點配置權限
        user_roles = user.get("roles", [])
        for role in user_roles:
            role_permissions = self.rbac_manager.hierarchy.get_all_permissions(
                role.name
            )
            role_permissions.update(role.permissions)

            # 檢查必要權限
            required_perm = self._get_required_permission(method, path)
            if required_perm and required_perm in role_permissions:
                return True

        return False

    def _get_required_permission(self, method: str, path: str) -> Optional[str]:
        """獲取請求所需的權限"""
        # 根據路徑和方法映射到權限
        permission_map = {
            ("GET", "/api / v1 / data/"): "data:read",
            ("POST", "/api / v1 / trade / execute"): "trade:execute",
            ("GET", "/api / v1 / portfolio/"): "portfolio:view",
            ("POST", "/api / v1 / portfolio/"): "portfolio:modify",
            ("GET", "/api / v1 / analysis/"): "analysis:view",
            ("POST", "/api / v1 / strategy/"): "strategy:execute",
            ("POST", "/api / v1 / user/"): "user:manage",
        }

        for (m, p), perm in permission_map.items():
            if method == m and path.startswith(p):
                return perm

        return None

    def _build_abac_context(
        self, request: Request, user: Dict[str, Any]
    ) -> Optional[Context]:
        """構建ABAC上下文"""
        try:
            from .abac import AttributeType
            from .abac import Context as ABACContext

            now = datetime.now()
            return ABACContext(
                user_id=user["user_id"],
                user_attributes={
                    "role": user["roles"][0].name if user["roles"] else "guest",
                    "department": user.get("department", "general"),
                    "clearance": user.get("clearance", 1),
                },
                resource=request.url.path,
                resource_attributes={
                    "classification": self._get_resource_classification(
                        request.url.path
                    )
                },
                action=request.method.lower(),
                action_attributes={
                    "risk_level": self._get_action_risk_level(
                        request.method, request.url.path
                    )
                },
                environment="prod",  # 從配置中獲取
                environment_attributes={
                    "hour": now.hour,
                    "day_of_week": now.weekday(),
                    "client_ip": request.client.host,
                    "user_agent": request.headers.get("user - agent", ""),
                },
                timestamp=now,
                request_id=self._generate_request_id(),
            )
        except Exception as e:
            logger.error(f"構建ABAC上下文失敗: {e}")
            return None

    def _get_resource_classification(self, path: str) -> str:
        """獲取資源分類"""
        if "/api / v1 / portfolio" in path or "/api / v1 / trade" in path:
            return "sensitive"
        elif "/api / v1 / analysis" in path:
            return "internal"
        elif "/api / v1 / data / public" in path:
            return "public"
        return "default"

    def _get_action_risk_level(self, method: str, path: str) -> int:
        """獲取操作風險等級"""
        high_risk = ["POST", "PUT", "DELETE"]
        if method in high_risk and ("/trade" in path or "/config" in path):
            return 3
        elif method in high_risk:
            return 2
        return 1

    def _generate_request_id(self) -> str:
        """生成請求ID"""
        return f"{int(time.time())}_{hash(str(time.time()))}"


class APIAccessMiddleware(BaseHTTPMiddleware):
    """API訪問控制中間件"""

    def __init__(self, app, api_access_manager: APIAccessManager):
        super().__init__(app)
        self.api_access_manager = api_access_manager

    async def dispatch(self, request: Request, call_next):
        """處理API訪問控制"""
        # 檢查API密鑰
        api_key = None
        if "X - API - Key" in request.headers:
            api_key_str = request.headers["X - API - Key"]
            api_key = self.api_access_manager.validate_api_key(api_key_str)

        # 檢查端點權限
        has_permission, error_code = self.api_access_manager.check_endpoint_permission(
            request.method,
            request.url.path,
            user_id=(
                request.state.user["user_id"]
                if hasattr(request.state, "user")
                else None
            ),
            api_key=api_key,
        )

        if not has_permission:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "error": "forbidden",
                    "message": "API端點權限不足",
                    "code": error_code,
                },
            )

        # 檢查速率限制
        if api_key:
            is_limited, rate_info = self.api_access_manager.check_rate_limit(
                api_key, request.url.path, request.method, request.client.host
            )

            if is_limited:
                response = JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "rate_limit_exceeded",
                        "message": "請求過於頻繁",
                        "code": "RATE_LIMIT_EXCEEDED",
                        "rate_info": rate_info,
                    },
                )
                response.headers["X - RateLimit - Limit"] = str(rate_info["limit"])
                response.headers["X - RateLimit - Remaining"] = str(rate_info["remaining"])
                response.headers["X - RateLimit - Reset"] = str(rate_info["reset"])
                return response

        # 處理請求
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time

        # 記錄API使用
        if api_key and hasattr(request.state, "user"):
            self.api_access_manager.log_api_usage(
                api_key=api_key,
                user_id=request.state.user["user_id"],
                endpoint=request.url.path,
                method=request.method,
                response_code=response.status_code,
                response_time=process_time,
                client_ip=request.client.host,
                user_agent=request.headers.get("user - agent", ""),
            )

        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """安全頭中間件"""

    async def dispatch(self, request: Request, call_next):
        """添加安全頭"""
        response = await call_next(request)

        # 添加安全頭
        response.headers["X - Content - Type - Options"] = "nosniff"
        response.headers["X - Frame - Options"] = "DENY"
        response.headers["X - XSS - Protection"] = "1; mode=block"
        response.headers["Strict - Transport - Security"] = (
            "max - age=31536000; includeSubDomains"
        )
        response.headers["Content-Security-Policy"] = "default-src 'self'"

        return response


class AccessControlManager:
    """訪問控制管理器 - 整合所有組件"""

    def __init__(
        self,
        rbac_db_path: str = "rbac.db",
        mfa_db_path: str = "mfa.db",
        session_db_path: str = "sessions.db",
        api_db_path: str = "api_access.db",
        abac_policy_path: str = "abac_policies.json",
        redis_url: str = None,
        token_secret: str = None,
    ):
        # 初始化令牌管理器
        token_secret = token_secret or secrets.token_hex(32)
        self.token_manager = TokenManager(token_secret)

        # 初始化各個管理器
        self.rbac_manager = RBACManager(rbac_db_path)
        self.mfa_manager = MFAManager(mfa_db_path)
        self.session_manager = SessionManager(
            session_db_path, redis_url, self.token_manager
        )
        self.api_access_manager = APIAccessManager(api_db_path, redis_url)
        self.abac_manager = ABACManager(abac_policy_path)

        logger.info("訪問控制管理器初始化完成")

    def get_middleware(self):
        """獲取FastAPI中間件列表"""
        return [
            SecurityHeadersMiddleware,
            lambda app: AuthenticationMiddleware(
                app, self.rbac_manager, self.mfa_manager, self.session_manager
            ),
            lambda app: AuthorizationMiddleware(
                app, self.rbac_manager, self.abac_manager
            ),
            lambda app: APIAccessMiddleware(app, self.api_access_manager),
        ]

    def create_access_control_depends(self):
        """創建訪問控制依賴"""
        from fastapi import Depends

        async def get_current_user(request: Request):
            """獲取當前用戶"""
            if not hasattr(request.state, "user"):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="需要認證"
                )
            return request.state.user

        async def require_permission(permission: str):
            """權限依賴"""
            from functools import wraps

            def decorator(func):
                @wraps(func)
                async def wrapper(*args, **kwargs):
                    request = None
                    for arg in args:
                        if isinstance(arg, Request):
                            request = arg
                            break

                    if not request or not hasattr(request.state, "user"):
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED, detail="需要認證"
                        )

                    user = request.state.user
                    user_roles = user.get("roles", [])

                    for role in user_roles:
                        role_permissions = (
                            self.rbac_manager.hierarchy.get_all_permissions(role.name)
                        )
                        role_permissions.update(role.permissions)
                        if permission in role_permissions:
                            return await func(*args, **kwargs)

                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN, detail="權限不足"
                    )

                return wrapper

            return decorator

        return {
            "get_current_user": get_current_user,
            "require_permission": require_permission,
        }

    def get_security_config(self) -> Dict[str, Any]:
        """獲取安全配置"""
        return {
            "rbac": {
                "total_roles": len(self.rbac_manager.get_all_roles()),
                "role_hierarchy": self.rbac_manager.hierarchy.hierarchy,
            },
            "abac": {
                "total_policies": len(self.abac_manager.get_policies()),
                "policy_summary": self.abac_manager.get_policy_summary(),
            },
            "mfa": {"supported_methods": ["totp", "sms", "email", "backup_code"]},
            "session": {
                "idle_timeout": self.session_manager.idle_timeout.total_seconds(),
                "absolute_timeout": self.session_manager.absolute_timeout.total_seconds(),
                "max_concurrent_sessions": self.session_manager.max_concurrent_sessions,
            },
            "api": {
                "total_api_keys": len(self.api_access_manager.get_user_api_keys("*")),
                "endpoint_count": len(self.api_access_manager.endpoint_permissions),
            },
        }


import secrets
from functools import wraps

from fastapi import Depends
