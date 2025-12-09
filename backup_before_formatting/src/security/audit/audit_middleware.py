"""
審計中間件
自動記錄HTTP請求和響應的審計日誌
"""

import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse

from .audit_config import AuditConfig
from .audit_logger import AuditLogger


class AuditMiddleware(BaseHTTPMiddleware):
    """審計中間件"""

    def __init__(self, app, config: AuditConfig = None):
        """
        初始化審計中間件

        Args:
            app: FastAPI應用實例
            config: 審計配置
        """
        super().__init__(app)
        self.config = config or AuditConfig()
        self.audit_logger = AuditLogger(self.config)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        處理HTTP請求並記錄審計日誌

        Args:
            request: FastAPI請求對象
            call_next: 下一個處理程序

        Returns:
            HTTP響應
        """
        # 生成關聯ID
        correlation_id = str(uuid.uuid4())

        # 記錄請求開始時間
        start_time = time.time()

        # 獲取客戶端信息
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user - agent", "")

        # 獲取用戶ID（如果已認證）
        user_id = getattr(request.state, "user_id", None)

        # 記錄請求
        request_id = self.audit_logger.log(
            event_type="api_calls",
            action=request.method,
            user_id=user_id,
            resource=str(request.url.path),
            source_ip=client_ip,
            user_agent=user_agent,
            details={
                "method": request.method,
                "path": str(request.url.path),
                "query_params": dict(request.query_params),
                "correlation_id": correlation_id,
                "headers": self._sanitize_headers(dict(request.headers)),
            },
        )

        # 處理請求
        try:
            response = await call_next(request)

            # 計算處理時間
            process_time = time.time() - start_time

            # 記錄響應
            self.audit_logger.log(
                event_type="api_calls",
                action=f"{request.method}_response",
                user_id=user_id,
                resource=str(request.url.path),
                status="success" if response.status_code < 400 else "failure",
                source_ip=client_ip,
                user_agent=user_agent,
                details={
                    "status_code": response.status_code,
                    "process_time": round(process_time, 3),
                    "correlation_id": correlation_id,
                    "request_id": request_id,
                    "response_headers": dict(response.headers),
                },
                risk_score=self._calculate_risk_score(request, response),
            )

            return response

        except Exception as e:
            # 記錄錯誤
            error_time = time.time() - start_time

            self.audit_logger.log(
                event_type="api_calls",
                action=f"{request.method}_error",
                user_id=user_id,
                resource=str(request.url.path),
                status="error",
                source_ip=client_ip,
                user_agent=user_agent,
                details={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "process_time": round(error_time, 3),
                    "correlation_id": correlation_id,
                    "request_id": request_id,
                },
                risk_score=80,
            )

            raise

    def _get_client_ip(self, request: Request) -> str:
        """獲取客戶端真實IP"""
        # 檢查代理頭
        forwarded_for = request.headers.get("x - forwarded - for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("x - real - ip")
        if real_ip:
            return real_ip

        # 從客戶端獲取
        return request.client.host if request.client else "unknown"

    def _sanitize_headers(self, headers: dict) -> dict:
        """清理敏感頭信息"""
        sanitized = {}
        sensitive_keys = {"authorization", "cookie", "x - api - key", "x - auth - token"}

        for key, value in headers.items():
            if key.lower() in sensitive_keys:
                sanitized[key] = "***REDACTED***"
            else:
                sanitized[key] = value

        return sanitized

    def _calculate_risk_score(self, request: Request, response: Response) -> int:
        """
        計算請求風險評分

        Args:
            request: HTTP請求
            response: HTTP響應

        Returns:
            風險評分(0 - 100)
        """
        score = 0

        # 檢查HTTP方法
        if request.method in ["DELETE", "PATCH", "PUT"]:
            score += 30
        elif request.method == "POST":
            score += 20

        # 檢查路徑
        path = str(request.url.path).lower()
        sensitive_paths = ["/admin", "/config", "/user", "/api / auth", "/api / trade"]
        if any(sp in path for sp in sensitive_paths):
            score += 40

        # 檢查狀態碼
        if response.status_code >= 500:
            score += 30
        elif response.status_code >= 400:
            score += 20

        # 檢查查詢參數
        if request.query_params:
            score += 10

        # 檢查請求頭
        content_type = request.headers.get("content - type", "").lower()
        if "json" in content_type:
            score += 5

        # 限制最大分數
        return min(score, 100)


# 裝飾器用於記錄函數調用
def audit_function_call(
    event_type: str, action: str, resource: str = None, user_id_param: str = "user_id"
):
    """
    審計函數調用裝飾器

    Args:
        event_type: 事件類型
        action: 操作
        resource: 資源
        user_id_param: 用戶ID參數名
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            # 獲取審計記錄器
            audit_logger = AuditLogger()

            # 提取參數
            user_id = kwargs.get(user_id_param) or (
                args[list(args).index(kwargs.get(user_id_param))]
                if user_id_param in kwargs
                else None
            )

            resource_name = resource or f"{func.__module__}.{func.__name__}"

            # 記錄函數調用
            audit_logger.log(
                event_type=event_type,
                action=action,
                user_id=user_id,
                resource=resource_name,
                details={
                    "function": func.__name__,
                    "args": str(args)[:200],  # 限制長度
                    "kwargs": str(kwargs)[:200],
                },
            )

            try:
                result = func(*args, **kwargs)

                # 記錄成功
                audit_logger.log(
                    event_type=event_type,
                    action=f"{action}_success",
                    user_id=user_id,
                    resource=resource_name,
                    details={
                        "function": func.__name__,
                        "return_type": type(result).__name__,
                    },
                )

                return result

            except Exception as e:
                # 記錄錯誤
                audit_logger.log(
                    event_type=event_type,
                    action=f"{action}_error",
                    user_id=user_id,
                    resource=resource_name,
                    status="error",
                    details={
                        "function": func.__name__,
                        "error": str(e),
                        "error_type": type(e).__name__,
                    },
                    risk_score=70,
                )

                raise

        return wrapper

    return decorator
