#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增強認證中間件
Phase 4: 生產級安全中間件，包含速率限制、IP白名單、輸入驗證等
"""

import time
import hashlib
import secrets
import ipaddress
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional, Callable, Any
from collections import defaultdict, deque
import json

from fastapi import Request, HTTPException, status, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import jwt
import redis.asyncio as redis
from sqlalchemy.orm import Session

import logging
logger = logging.getLogger(__name__)

class SecurityConfig:
    """安全配置類"""

    # 速率限制配置
    RATE_LIMITS = {
        "default": {"requests": 100, "window": 3600},      # 每小時100請求
        "auth": {"requests": 5, "window": 300},            # 每5分鐘5次認證嘗試
        "optimization": {"requests": 20, "window": 3600},  # 每小時20次優化請求
        "upload": {"requests": 10, "window": 3600},        # 每小時10次上傳
    }

    # IP白名單和黑名單
    IP_WHITELIST = []  # 允許的IP範圍，如 ["192.168.1.0/24", "10.0.0.0/8"]
    IP_BLACKLIST = []  # 禁止的IP，如 ["192.168.1.100"]

    # 請求大小限制
    MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10MB

    # 安全標頭
    SECURITY_HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
        "Referrer-Policy": "strict-origin-when-cross-origin",
    }

    # JWT配置
    JWT_ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    REFRESH_TOKEN_EXPIRE_DAYS = 7

    # 會話配置
    MAX_CONCURRENT_SESSIONS = 5
    SESSION_TIMEOUT_MINUTES = 60

    # 密碼策略
    PASSWORD_MIN_LENGTH = 12
    PASSWORD_REQUIRE_UPPERCASE = True
    PASSWORD_REQUIRE_LOWERCASE = True
    PASSWORD_REQUIRE_NUMBERS = True
    PASSWORD_REQUIRE_SYMBOLS = True

    # API密鑰配置
    API_KEY_HEADER = "X-API-Key"
    API_KEY_LENGTH = 32

class RateLimiter:
    """速率限制器"""

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self.memory_store: Dict[str, deque] = defaultdict(deque)
        self.cleanup_interval = 300  # 5分鐘清理一次
        self.last_cleanup = time.time()

    async def is_allowed(
        self,
        key: str,
        limit: int,
        window: int,
        identifier: Optional[str] = None
    ) -> bool:
        """檢查是否允許請求"""
        now = time.time()

        if self.redis_client:
            return await self._redis_rate_limit(key, limit, window, identifier)
        else:
            return self._memory_rate_limit(key, limit, window, now)

    async def _redis_rate_limit(
        self,
        key: str,
        limit: int,
        window: int,
        identifier: Optional[str]
    ) -> bool:
        """Redis實現的速率限制"""
        try:
            current_time = int(time.time())
            redis_key = f"rate_limit:{key}:{identifier or 'global'}:{current_time // window}"

            # 獲取當前計數
            current_count = await self.redis_client.get(redis_key)

            if current_count is None:
                # 首次請求，設置計數和過期時間
                await self.redis_client.setex(redis_key, window, 1)
                return True
            else:
                current_count = int(current_count)
                if current_count >= limit:
                    return False

                # 增加計數
                await self.redis_client.incr(redis_key)
                return True

        except Exception as e:
            logger.error(f"Redis速率限制錯誤: {e}")
            # Redis失敗時使用內存限制
            return self._memory_rate_limit(key, limit, window, time.time())

    def _memory_rate_limit(
        self,
        key: str,
        limit: int,
        window: int,
        now: float
    ) -> bool:
        """內存實現的速率限制"""
        # 定期清理過期記錄
        if now - self.last_cleanup > self.cleanup_interval:
            self._cleanup_expired_records(now)
            self.last_cleanup = now

        request_times = self.memory_store[key]

        # 移除過期的請求記錄
        while request_times and request_times[0] < now - window:
            request_times.popleft()

        # 檢查是否超過限制
        if len(request_times) >= limit:
            return False

        # 添加當前請求
        request_times.append(now)
        return True

    def _cleanup_expired_records(self, now: float):
        """清理過期的記錄"""
        for key in list(self.memory_store.keys()):
            request_times = self.memory_store[key]
            while request_times and request_times[0] < now - self.cleanup_interval:
                request_times.popleft()

            # 如果隊列為空，刪除該key
            if not request_times:
                del self.memory_store[key]

class InputValidator:
    """輸入驗證器"""

    @staticmethod
    def validate_password(password: str) -> List[str]:
        """驗證密碼強度"""
        errors = []

        if len(password) < SecurityConfig.PASSWORD_MIN_LENGTH:
            errors.append(f"密碼長度必須至少{SecurityConfig.PASSWORD_MIN_LENGTH}位")

        if SecurityConfig.PASSWORD_REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
            errors.append("密碼必須包含大寫字母")

        if SecurityConfig.PASSWORD_REQUIRE_LOWERCASE and not any(c.islower() for c in password):
            errors.append("密碼必須包含小寫字母")

        if SecurityConfig.PASSWORD_REQUIRE_NUMBERS and not any(c.isdigit() for c in password):
            errors.append("密碼必須包含數字")

        if SecurityConfig.PASSWORD_REQUIRE_SYMBOLS and not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            errors.append("密碼必須包含特殊字符")

        # 檢查常見弱密碼
        weak_passwords = [
            "password", "123456", "123456789", "qwerty", "abc123",
            "password123", "admin123", "root123", "user123"
        ]
        if password.lower() in weak_passwords:
            errors.append("不能使用常見弱密碼")

        return errors

    @staticmethod
    def sanitize_input(input_data: Any) -> Any:
        """清理輸入數據"""
        if isinstance(input_data, str):
            # 移除潛在的惡意字符
            dangerous_chars = ["<", ">", "&", "\"", "'", "javascript:", "vbscript:", "onload=", "onerror="]
            sanitized = input_data
            for char in dangerous_chars:
                sanitized = sanitized.replace(char, "")
            return sanitized.strip()
        elif isinstance(input_data, dict):
            return {key: InputValidator.sanitize_input(value) for key, value in input_data.items()}
        elif isinstance(input_data, list):
            return [InputValidator.sanitize_input(item) for item in input_data]
        else:
            return input_data

    @staticmethod
    def validate_json_size(json_data: dict, max_size: int = SecurityConfig.MAX_REQUEST_SIZE) -> bool:
        """驗證JSON數據大小"""
        try:
            json_str = json.dumps(json_data)
            return len(json_str.encode('utf-8')) <= max_size
        except:
            return False

class SecurityMiddleware(BaseHTTPMiddleware):
    """安全中間件"""

    def __init__(self, app, redis_client: Optional[redis.Redis] = None):
        super().__init__(app)
        self.rate_limiter = RateLimiter(redis_client)
        self.input_validator = InputValidator()
        self.failed_attempts: Dict[str, int] = defaultdict(int)
        self.blocked_ips: Set[str] = set()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """處理請求"""
        client_ip = self._get_client_ip(request)

        try:
            # 1. IP黑名單檢查
            if self._is_ip_blocked(client_ip):
                return self._block_response("IP地址被封鎖")

            # 2. 速率限制檢查
            if not await self._check_rate_limit(request, client_ip):
                return self._rate_limit_response()

            # 3. 請求大小檢查
            if not await self._check_request_size(request):
                return self._size_limit_response()

            # 4. 輸入驗證和清理
            await self._validate_and_sanitize_request(request)

            # 5. 處理請求
            response = await call_next(request)

            # 6. 添加安全標頭
            self._add_security_headers(response)

            # 7. 記錄成功請求
            await self._log_request(request, response, success=True)

            return response

        except HTTPException as e:
            await self._log_request(request, None, success=False, error=str(e))
            raise
        except Exception as e:
            logger.error(f"安全中間件錯誤: {e}")
            await self._log_request(request, None, success=False, error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="內部服務器錯誤"
            )

    def _get_client_ip(self, request: Request) -> str:
        """獲取客戶端真實IP"""
        # 檢查代理標頭
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # X-Forwarded-For可能包含多個IP，取第一個
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # 使用客戶端IP
        return request.client.host if request.client else "unknown"

    def _is_ip_blocked(self, ip: str) -> bool:
        """檢查IP是否被封鎖"""
        try:
            # 檢查黑名單
            if ip in SecurityConfig.IP_BLACKLIST:
                return True

            # 檢查動態封鎖
            if ip in self.blocked_ips:
                return True

            # 檢查白名單（如果配置了白名單）
            if SecurityConfig.IP_WHITELIST:
                client_ip = ipaddress.ip_address(ip)
                for allowed_range in SecurityConfig.IP_WHITELIST:
                    if client_ip in ipaddress.ip_network(allowed_range):
                        return False
                return True  # 在白名單中但不在允許範圍內

            return False

        except Exception as e:
            logger.error(f"IP檢查錯誤: {e}")
            return True  # 出錯時默認封鎖

    async def _check_rate_limit(self, request: Request, client_ip: str) -> bool:
        """檢查速率限制"""
        # 根據請求路徑確定限制類型
        path = request.url.path
        if "/auth" in path:
            limit_type = "auth"
        elif "/optimize" in path:
            limit_type = "optimization"
        elif "/upload" in path:
            limit_type = "upload"
        else:
            limit_type = "default"

        config = SecurityConfig.RATE_LIMITS.get(limit_type, SecurityConfig.RATE_LIMITS["default"])

        # 檢查全局限制
        if not await self.rate_limiter.is_allowed(
            f"{limit_type}:global",
            config["requests"],
            config["window"]
        ):
            return False

        # 檢查IP限制
        if not await self.rate_limiter.is_allowed(
            f"{limit_type}:ip",
            config["requests"],
            config["window"],
            client_ip
        ):
            return False

        return True

    async def _check_request_size(self, request: Request) -> bool:
        """檢查請求大小"""
        try:
            content_length = request.headers.get("content-length")
            if content_length:
                size = int(content_length)
                return size <= SecurityConfig.MAX_REQUEST_SIZE

            # 對於沒有content-length的請求，讀取部分內容檢查
            if request.method in ["POST", "PUT", "PATCH"]:
                body = await request.body()
                return len(body) <= SecurityConfig.MAX_REQUEST_SIZE

            return True

        except Exception:
            return False

    async def _validate_and_sanitize_request(self, request: Request):
        """驗證和清理請求"""
        # 檢查惡意標頭
        suspicious_headers = ["X-Forwarded-Host", "X-Originating-IP", "X-Remote-IP"]
        for header in suspicious_headers:
            if header in request.headers:
                logger.warning(f"檢測到可疑標頭: {header}")

        # 對於POST/PUT請求，驗證JSON內容
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            if "application/json" in content_type:
                try:
                    # 需要先接收body然後重新設置
                    body = await request.body()
                    if body:
                        json_data = json.loads(body.decode())

                        # 驗證JSON大小
                        if not self.input_validator.validate_json_size(json_data):
                            raise HTTPException(
                                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                                detail="請求數據過大"
                            )

                        # 清理輸入數據
                        sanitized_data = self.input_validator.sanitize_input(json_data)

                        # 將清理後的數據重新設置到請求狀態
                        request.state.sanitized_json = sanitized_data

                except json.JSONDecodeError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="無效的JSON格式"
                    )

    def _add_security_headers(self, response: Response):
        """添加安全標頭"""
        for header, value in SecurityConfig.SECURITY_HEADERS.items():
            response.headers[header] = value

        # 移除敏感的服務器信息
        response.headers.pop("Server", None)

        # 添加CORS標頭（如果需要）
        # response.headers["Access-Control-Allow-Origin"] = "https://yourdomain.com"

    async def _log_request(
        self,
        request: Request,
        response: Optional[Response],
        success: bool,
        error: Optional[str] = None
    ):
        """記錄請求日誌"""
        try:
            log_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "method": request.method,
                "path": request.url.path,
                "client_ip": self._get_client_ip(request),
                "user_agent": request.headers.get("user-agent"),
                "success": success,
                "status_code": response.status_code if response else None,
                "error": error
            }

            if success:
                logger.info(f"請求成功: {json.dumps(log_data)}")
            else:
                logger.warning(f"請求失敗: {json.dumps(log_data)}")

        except Exception as e:
            logger.error(f"記錄請求日誌失敗: {e}")

    def _block_response(self, message: str) -> JSONResponse:
        """封鎖響應"""
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"detail": message}
        )

    def _rate_limit_response(self) -> JSONResponse:
        """速率限制響應"""
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "detail": "請求過於頻繁，請稍後再試",
                "retry_after": 60
            }
        )

    def _size_limit_response(self) -> JSONResponse:
        """大小限制響應"""
        return JSONResponse(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            content={
                "detail": f"請求數據過大，最大允許 {SecurityConfig.MAX_REQUEST_SIZE // (1024*1024)}MB"
            }
        )

class EnhancedJWTAuth:
    """增強JWT認證"""

    def __init__(self, secret_key: str, redis_client: Optional[redis.Redis] = None):
        self.secret_key = secret_key
        self.redis_client = redis_client
        self.token_blacklist: Set[str] = set()

    def create_access_token(
        self,
        data: dict,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """創建訪問令牌"""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=SecurityConfig.ACCESS_TOKEN_EXPIRE_MINUTES)

        # 添加JWT ID用於撤銷
        jti = secrets.token_urlsafe(32)
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "jti": jti,
            "type": "access"
        })

        # 如果有Redis，將令牌ID存儲在Redis中
        if self.redis_client:
            asyncio.create_task(self._store_token_jti(jti, expire))

        return jwt.encode(to_encode, self.secret_key, algorithm=SecurityConfig.JWT_ALGORITHM)

    async def verify_token(self, token: str) -> Optional[dict]:
        """驗證令牌"""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[SecurityConfig.JWT_ALGORITHM]
            )

            # 檢查令牌類型
            if payload.get("type") != "access":
                return None

            # 檢查是否在黑名單中
            jti = payload.get("jti")
            if jti and await self._is_token_revoked(jti):
                return None

            return payload

        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    async def revoke_token(self, token: str) -> bool:
        """撤銷令牌"""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[SecurityConfig.JWT_ALGORITHM],
                options={"verify_exp": False}  # 不驗證過期時間
            )

            jti = payload.get("jti")
            if jti:
                if self.redis_client:
                    # 添加到Redis黑名單
                    await self.redis_client.setex(
                        f"token_blacklist:{jti}",
                        86400,  # 24小時
                        "1"
                    )
                else:
                    # 添加到內存黑名單
                    self.token_blacklist.add(jti)

                return True

        except Exception as e:
            logger.error(f"撤銷令牌失敗: {e}")

        return False

    async def _store_token_jti(self, jti: str, expire: datetime):
        """存儲令牌JTI到Redis"""
        try:
            if self.redis_client:
                ttl = int((expire - datetime.utcnow()).total_seconds())
                await self.redis_client.setex(
                    f"token_jti:{jti}",
                    ttl,
                    "1"
                )
        except Exception as e:
            logger.error(f"存儲令牌JTI失敗: {e}")

    async def _is_token_revoked(self, jti: str) -> bool:
        """檢查令牌是否被撤銷"""
        try:
            if self.redis_client:
                return await self.redis_client.exists(f"token_blacklist:{jti}")
            else:
                return jti in self.token_blacklist
        except Exception as e:
            logger.error(f"檢查令牌撤銷狀態失敗: {e}")
            return True  # 出錯時默認認為已撤銷

# 全局實例（應在應用啟動時初始化）
security_middleware = None
enhanced_auth = None

def init_security_middleware(app, redis_client: Optional[redis.Redis] = None):
    """初始化安全中間件"""
    global security_middleware, enhanced_auth

    from backend.core.config import get_settings
    settings = get_settings()

    security_middleware = SecurityMiddleware(app, redis_client)
    enhanced_auth = EnhancedJWTAuth(settings.SECRET_KEY, redis_client)

    return security_middleware, enhanced_auth

async def get_enhanced_auth():
    """獲取增強認證實例"""
    return enhanced_auth