"""
企業級安全框架
提供輸入驗證、速率限制和安全防護功能

Author: CBSC Quantitative Trading System
Version: 1.0.0
"""

import re
import time
import bleach
import asyncio
import logging
from typing import Any, Dict, List, Optional, Union, Set
from collections import defaultdict, deque
from datetime import datetime, timedelta
from dataclasses import dataclass

from pydantic import BaseModel, Field, validator
from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware

# 配置日誌
logger = logging.getLogger(__name__)


class SecurityValidationError(Exception):
    """
    安全驗證錯誤

    用於處理各種安全相關的驗證失敗情況
    """
    def __init__(self, message: str, error_code: str = "SECURITY_ERROR", details: Optional[Dict] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(message)


class SecurityValidator:
    """
    企業級輸入安全驗證器

    提供全面的輸入驗證和清理功能，防護XSS、SQL注入等安全威脅
    """

    # 危險模式檢測 - XSS攻擊
    XSS_PATTERNS = [
        r'<script.*?>.*?</script>',
        r'javascript:',
        r'data:',
        r'vbscript:',
        r'on\w+\s*=',
        r'expression\s*\(',
        r'@import',
        r'binding\s*\(',
    ]

    # SQL注入模式檢測
    SQL_INJECTION_PATTERNS = [
        r'union\s+select',
        r'drop\s+table',
        r'truncate\s+table',
        r'delete\s+from',
        r'insert\s+into',
        r'update\s+set',
        r'exec\s*\(',
        r'execute\s*\(',
        r'sp_executesql',
        r'xp_cmdshell',
    ]

    # 命令注入模式檢測
    COMMAND_INJECTION_PATTERNS = [
        r'\|\s*',
        r';\s*',
        r'&&\s*',
        r'\|\|\s*',
        r'`.*?`',
        r'\$\(.*?\)',
        r'<\?.*?\?>',
        r'<%.*?%>',
    ]

    # 路徑遍歷模式檢測
    PATH_TRAVERSAL_PATTERNS = [
        r'\.\./',
        r'\.\.\\',
        r'%2e%2e%2f',
        r'%2e%2e\\',
        r'\.\.\\',
        r'%2e%2e/',
    ]

    @classmethod
    def sanitize_input(cls, value: str, max_length: int = 1000) -> str:
        """
        清理和驗證字符串輸入

        Args:
            value: 原始輸入字符串
            max_length: 最大允許長度

        Returns:
            清理後的安全字符串

        Raises:
            SecurityValidationError: 發現安全威脅時拋出
        """
        if not isinstance(value, str):
            return value

        # 長度檢查
        if len(value) > max_length:
            raise SecurityValidationError(
                f"輸入長度超過限制 ({max_length} 字符)",
                error_code="INPUT_TOO_LONG",
                details={"actual_length": len(value), "max_length": max_length}
            )

        # HTML和CSS清理
        cleaned = bleach.clean(
            value,
            tags=[],  # 不允許任何HTML標籤
            attributes={},
            strip=True,
            strip_comments=True
        )

        # 檢測XSS模式
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, cleaned, re.IGNORECASE | re.MULTILINE):
                logger.warning(f"檢測到XSS攻擊模式: {pattern[:50]}...")
                raise SecurityValidationError(
                    "輸入包含潛在XSS攻擊代碼",
                    error_code="XSS_DETECTED",
                    details={"pattern": pattern[:50]}
                )

        # 檢測SQL注入模式
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, cleaned, re.IGNORECASE | re.MULTILINE):
                logger.warning(f"檢測到SQL注入模式: {pattern[:50]}...")
                raise SecurityValidationError(
                    "輸入包含潛在SQL注入代碼",
                    error_code="SQL_INJECTION_DETECTED",
                    details={"pattern": pattern[:50]}
                )

        # 檢測命令注入模式
        for pattern in cls.COMMAND_INJECTION_PATTERNS:
            if re.search(pattern, cleaned, re.IGNORECASE):
                logger.warning(f"檢測到命令注入模式: {pattern[:50]}...")
                raise SecurityValidationError(
                    "輸入包含潛在命令注入代碼",
                    error_code="COMMAND_INJECTION_DETECTED",
                    details={"pattern": pattern[:50]}
                )

        # 檢測路徑遍歷模式
        for pattern in cls.PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, cleaned, re.IGNORECASE):
                logger.warning(f"檢測到路徑遍歷模式: {pattern[:50]}...")
                raise SecurityValidationError(
                    "輸入包含潛在路徑遍歷攻擊",
                    error_code="PATH_TRAVERSAL_DETECTED",
                    details={"pattern": pattern[:50]}
                )

        return cleaned.strip()

    @classmethod
    def validate_numeric_range(
        cls,
        value: Any,
        min_val: Optional[float] = None,
        max_val: Optional[float] = None,
        param_name: str = "parameter"
    ) -> float:
        """
        驗證數值範圍

        Args:
            value: 要驗證的值
            min_val: 最小值
            max_val: 最大值
            param_name: 參數名稱

        Returns:
            驗證後的數值

        Raises:
            SecurityValidationError: 驗證失敗時拋出
        """
        try:
            numeric_value = float(value)
        except (ValueError, TypeError):
            raise SecurityValidationError(
                f"{param_name}: 無效的數值格式",
                error_code="INVALID_NUMERIC_FORMAT",
                details={"value": str(value), "param_name": param_name}
            )

        if min_val is not None and numeric_value < min_val:
            raise SecurityValidationError(
                f"{param_name}: 數值必須大於等於 {min_val}",
                error_code="VALUE_BELOW_MINIMUM",
                details={
                    "value": numeric_value,
                    "min_value": min_val,
                    "param_name": param_name
                }
            )

        if max_val is not None and numeric_value > max_val:
            raise SecurityValidationError(
                f"{param_name}: 數值必須小於等於 {max_val}",
                error_code="VALUE_ABOVE_MAXIMUM",
                details={
                    "value": numeric_value,
                    "max_value": max_val,
                    "param_name": param_name
                }
            )

        return numeric_value

    @classmethod
    def validate_session_id(cls, session_id: str) -> str:
        """
        驗證會話ID格式

        Args:
            session_id: 會話ID

        Returns:
            驗證後的會話ID

        Raises:
            SecurityValidationError: 格式錯誤時拋出
        """
        if not isinstance(session_id, str):
            raise SecurityValidationError(
                "會話ID必須是字符串",
                error_code="INVALID_SESSION_ID_TYPE"
            )

        # 長度檢查
        if len(session_id) < 8 or len(session_id) > 64:
            raise SecurityValidationError(
                "會話ID長度必須在8-64字符之間",
                error_code="INVALID_SESSION_ID_LENGTH",
                details={"length": len(session_id)}
            )

        # 格式檢查 - 只允許字母數字、連字符和下劃線
        if not re.match(r'^[a-zA-Z0-9_-]+$', session_id):
            raise SecurityValidationError(
                "會話ID只能包含字母、數字、連字符和下劃線",
                error_code="INVALID_SESSION_ID_FORMAT",
                details={"session_id": session_id[:20] + "..." if len(session_id) > 20 else session_id}
            )

        return session_id

    @classmethod
    def validate_parameter_name(cls, param_name: str) -> str:
        """
        驗證參數名稱

        Args:
            param_name: 參數名稱

        Returns:
            驗證後的參數名稱

        Raises:
            SecurityValidationError: 格式錯誤時拋出
        """
        if not isinstance(param_name, str):
            raise SecurityValidationError(
                "參數名稱必須是字符串",
                error_code="INVALID_PARAM_NAME_TYPE"
            )

        # 長度檢查
        if len(param_name) < 1 or len(param_name) > 50:
            raise SecurityValidationError(
                "參數名稱長度必須在1-50字符之間",
                error_code="INVALID_PARAM_NAME_LENGTH",
                details={"length": len(param_name)}
            )

        # 格式檢查 - 只允許字母、數字和下劃線
        if not re.match(r'^[a-zA-Z0-9_]+$', param_name):
            raise SecurityValidationError(
                "參數名稱只能包含字母、數字和下劃線",
                error_code="INVALID_PARAM_NAME_FORMAT",
                details={"param_name": param_name}
            )

        # 保留字檢查
        reserved_words = {
            'admin', 'root', 'system', 'config', 'password', 'token',
            'key', 'secret', 'auth', 'login', 'session', 'cookie'
        }

        if param_name.lower() in reserved_words:
            raise SecurityValidationError(
                f"參數名稱不能使用保留字: {param_name}",
                error_code="RESERVED_WORD_USAGE",
                details={"param_name": param_name}
            )

        return cls.sanitize_input(param_name, max_length=50)


@dataclass
class RateLimitConfig:
    """速率限制配置"""
    count: int  # 允許的請求數量
    window: int  # 時間窗口（秒）
    block_duration: int = 3600  # 超限時的封禁時長（秒）


class RateLimiter:
    """
    企業級速率限制器

    提供用戶和IP級別的速率限制，支持動態封禁和解封
    """

    def __init__(self):
        # 用戶請求記錄 {user_id: deque of timestamps}
        self.user_requests: Dict[str, deque] = defaultdict(deque)
        # IP請求記錄 {ip: deque of timestamps}
        self.ip_requests: Dict[str, deque] = defaultdict(deque)
        # 封禁記錄 {identifier: unban_time}
        self.banned_users: Dict[str, float] = {}
        self.banned_ips: Dict[str, float] = {}

        # 速率限制配置
        self.RATE_LIMITS = {
            'websocket_messages': RateLimitConfig(100, 60, 300),      # 100消息/分鐘
            'api_requests': RateLimitConfig(1000, 3600, 7200),        # 1000請求/小時
            'parameter_updates': RateLimitConfig(50, 60, 300),        # 50更新/分鐘
            'auth_attempts': RateLimitConfig(5, 300, 1800),           # 5登錄嘗試/5分鐘
            'data_exports': RateLimitConfig(10, 3600, 7200),          # 10導出/小時
        }

        # 清理任務
        self._cleanup_task: Optional[asyncio.Task] = None
        self._start_cleanup_task()

    def _start_cleanup_task(self) -> None:
        """啟動清理任務"""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())

    async def _periodic_cleanup(self) -> None:
        """定期清理過期數據"""
        while True:
            try:
                await self._cleanup_expired_records()
                await self._unban_expired_users()
                await asyncio.sleep(60)  # 每分鐘清理一次
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"速率限制清理任務錯誤: {e}")

    async def check_rate_limit(
        self,
        identifier: str,
        limit_type: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> bool:
        """
        檢查速率限制

        Args:
            identifier: 用戶ID或會話ID
            limit_type: 限制類型
            ip_address: IP地址
            user_agent: 用戶代理

        Returns:
            是否允許請求

        Raises:
            HTTPException: 觸發限制時拋出
        """
        current_time = time.time()

        # 檢查封禁狀態
        if identifier in self.banned_users:
            if current_time < self.banned_users[identifier]:
                unban_time = datetime.fromtimestamp(self.banned_users[identifier])
                raise HTTPException(
                    status_code=status.HTTP_423_LOCKED,
                    detail={
                        "error": "用戶已被封禁",
                        "unban_time": unban_time.isoformat(),
                        "reason": "觸發速率限制"
                    }
                )
            else:
                # 自動解封
                del self.banned_users[identifier]

        if ip_address and ip_address in self.banned_ips:
            if current_time < self.banned_ips[ip_address]:
                unban_time = datetime.fromtimestamp(self.banned_ips[ip_address])
                raise HTTPException(
                    status_code=status.HTTP_423_LOCKED,
                    detail={
                        "error": "IP已被封禁",
                        "unban_time": unban_time.isoformat(),
                        "reason": "觸發速率限制"
                    }
                )
            else:
                # 自動解封
                del self.banned_ips[ip_address]

        limit_config = self.RATE_LIMITS.get(limit_type)
        if not limit_config:
            return True

        # 清理過期記錄
        requests = self.user_requests[identifier]
        window_start = current_time - limit_config.window
        while requests and requests[0] < window_start:
            requests.popleft()

        # 檢查限制
        if len(requests) >= limit_config.count:
            # 記錄違規行為
            await self._log_violation(identifier, limit_type, ip_address, user_agent, len(requests))

            # 檢查是否需要封禁
            if len(requests) >= limit_config.count * 2:  # 超過2倍限制
                ban_until = current_time + limit_config.block_duration
                self.banned_users[identifier] = ban_until

                logger.warning(
                    f"用戶 {identifier} 因觸發速率限制被封禁",
                    extra={
                        "identifier": identifier,
                        "limit_type": limit_type,
                        "requests_count": len(requests),
                        "ban_until": ban_until
                    }
                )

                raise HTTPException(
                    status_code=status.HTTP_423_LOCKED,
                    detail={
                        "error": "請求過於頻繁，已被封禁",
                        "unban_time": datetime.fromtimestamp(ban_until).isoformat(),
                        "duration": limit_config.block_duration
                    }
                )

            logger.warning(
                f"用戶 {identifier} 觸發速率限制: {limit_type}",
                extra={
                    "identifier": identifier,
                    "limit_type": limit_type,
                    "requests_count": len(requests),
                    "limit": limit_config.count
                }
            )

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "請求過於頻繁",
                    "limit_type": limit_type,
                    "limit": limit_config.count,
                    "window": limit_config.window,
                    "retry_after": limit_config.window
                }
            )

        # 記錄請求
        requests.append(current_time)
        return True

    async def _log_violation(
        self,
        identifier: str,
        limit_type: str,
        ip_address: Optional[str],
        user_agent: Optional[str],
        requests_count: int
    ) -> None:
        """記錄違規行為"""
        logger.warning(
            f"速率限制違規: {identifier} - {limit_type}",
            extra={
                "identifier": identifier,
                "limit_type": limit_type,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "requests_count": requests_count,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

    async def _cleanup_expired_records(self) -> None:
        """清理過期的請求記錄"""
        current_time = time.time()

        # 清理用戶記錄
        for user_id in list(self.user_requests.keys()):
            requests = self.user_requests[user_id]
            if not requests:
                del self.user_requests[user_id]
                continue

            # 檢查是否有最近的記錄
            if requests[-1] < current_time - 7200:  # 2小時前的記錄
                del self.user_requests[user_id]

    async def _unban_expired_users(self) -> None:
        """解封過期的用戶"""
        current_time = time.time()

        # 解封用戶
        expired_users = [
            user_id for user_id, unban_time in self.banned_users.items()
            if current_time >= unban_time
        ]
        for user_id in expired_users:
            del self.banned_users[user_id]
            logger.info(f"用戶 {user_id} 已自動解封")

        # 解封IP
        expired_ips = [
            ip_addr for ip_addr, unban_time in self.banned_ips.items()
            if current_time >= unban_time
        ]
        for ip_addr in expired_ips:
            del self.banned_ips[ip_addr]
            logger.info(f"IP {ip_addr} 已自動解封")

    def get_stats(self) -> Dict[str, Any]:
        """獲取速率限制統計信息"""
        current_time = time.time()

        return {
            "active_users": len(self.user_requests),
            "banned_users": len(self.banned_users),
            "banned_ips": len(self.banned_ips),
            "total_requests": sum(len(requests) for requests in self.user_requests.values()),
            "cleanup_task_running": self._cleanup_task is not None and not self._cleanup_task.done(),
            "timestamp": current_time
        }


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    速率限制中間件

    自動應用速率限制到所有HTTP請求
    """

    def __init__(self, app, rate_limiter: RateLimiter):
        super().__init__(app)
        self.rate_limiter = rate_limiter

    async def dispatch(self, request: Request, call_next):
        """處理請求"""
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("User-Agent", "")

        # 使用IP地址作為標識符
        identifier = client_ip

        try:
            # 檢查IP速率限制
            await self.rate_limiter.check_rate_limit(
                identifier=identifier,
                limit_type='api_requests',
                ip_address=client_ip,
                user_agent=user_agent
            )

            response = await call_next(request)
            return response

        except HTTPException:
            raise

        except Exception as e:
            logger.error(f"速率限制中間件錯誤: {e}")
            # 在錯誤情況下允許請求通過，避免影響服務可用性
            return await call_next(request)

    def _get_client_ip(self, request: Request) -> str:
        """獲取客戶端真實IP"""
        # 檢查代理頭
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        cf_connecting_ip = request.headers.get("CF-Connecting-IP")
        if cf_connecting_ip:
            return cf_connecting_ip

        return request.client.host or "unknown"


# 全局實例
security_validator = SecurityValidator()
rate_limiter = RateLimiter()