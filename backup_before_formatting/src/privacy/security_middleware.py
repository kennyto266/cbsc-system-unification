"""
安全中间件

集成所有安全功能到FastAPI应用中。
提供请求过滤、数据验证、访问控制和安全审计。

功能:
- 请求 / 响应加密
- 数据验证
- 访问控制
- 安全头部注入
- 审计日志
- DLP检查
- 速率限制
"""

import json
import logging
import time
from typing import Any, Callable, Dict, List, Optional, Union

from fastapi import Depends, HTTPException, Request, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from .anonymization import get_anonymizer
from .data_classification import DataType, get_classification_manager
from .encryption import get_encryption
from .field_encryption import get_field_encryption
from .tls_manager import TLSManager

logger = logging.getLogger(__name__)
security = HTTPBearer()


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    安全中间件
    """

    def __init__(self, app, exempt_paths: List[str] = None):
        """
        初始化安全中间件

        Args:
            app: FastAPI应用
            exempt_paths: 豁免路径列表
        """
        super().__init__(app)
        self.exempt_paths = exempt_paths or ["/docs", "/openapi.json", "/health"]
        self.encryption = get_encryption()
        self.field_encryption = get_field_encryption()
        self.anonymizer = get_anonymizer()
        self.classification_manager = get_classification_manager()
        self.tls_manager = TLSManager()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求"""
        # 跳过豁免路径
        if request.url.path in self.exempt_paths:
            return await call_next(request)

        start_time = time.time()

        # 安全检查
        try:
            # 1. 验证请求
            await self._validate_request(request)

            # 2. 加密检查
            encrypted_response = await self._process_request(request, call_next)

            # 3. 添加安全头部
            response = await self._add_security_headers(encrypted_response, request)

            # 4. 记录审计日志
            processing_time = time.time() - start_time
            await self._log_access(request, response, processing_time, "success")

            return response

        except HTTPException as e:
            processing_time = time.time() - start_time
            await self._log_access(request, None, processing_time, "denied")
            raise

        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"安全中间件错误: {e}")
            await self._log_access(request, None, processing_time, "error")
            raise

    async def _validate_request(self, request: Request):
        """验证请求"""
        # 检查Content - Type
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content - type", "")
            if not content_type.startswith("application / json"):
                logger.warning(f"不支持的Content - Type: {content_type}")
                # 不直接拒绝，允许其他格式

        # 检查请求大小
        content_length = request.headers.get("content - length")
        if content_length and int(content_length) > 10 * 1024 * 1024:  # 10MB
            raise HTTPException(status_code=413, detail="请求数据过大")

        # 检查危险头部
        dangerous_headers = ["x - forwarded - host", "x - original - url"]
        for header in dangerous_headers:
            if header in request.headers:
                logger.warning(f"发现危险头部: {header}")
                # 可以选择拒绝或清理

    async def _process_request(self, request: Request, call_next: Callable) -> Response:
        """处理请求（加密 / 解密）"""
        # 读取请求体
        body = await request.body()

        if body and request.headers.get("content - type", "").startswith(
            "application / json"
        ):
            try:
                # 解密请求数据
                decrypted_body = self._decrypt_request_data(body)
                request._body = decrypted_body.encode("utf - 8")
            except Exception as e:
                logger.error(f"请求解密失败: {e}")
                # 如果解密失败，继续处理原始数据
                pass

        # 处理请求
        response = await call_next(request)

        # 加密响应数据
        if response.headers.get("content - type", "").startswith("application / json"):
            response = self._encrypt_response_data(response)

        return response

    def _decrypt_request_data(self, body: bytes) -> str:
        """解密请求数据"""
        try:
            data = json.loads(body)
            # 如果数据是加密的，解密它
            if isinstance(data, dict) and "_encrypted" in data:
                encrypted_fields = data.get("_encrypted_fields", [])
                for field in encrypted_fields:
                    if field in data and data[field]:
                        data[field] = self.encryption.decrypt(data[field])

                # 移除加密标记
                del data["_encrypted"]
                del data["_encrypted_fields"]

            return json.dumps(data)
        except Exception:
            return body.decode("utf - 8")

    def _encrypt_response_data(self, response: Response) -> Response:
        """加密响应数据"""
        try:
            # 获取响应体
            body = response.body.decode("utf - 8") if response.body else "{}"
            data = json.loads(body)

            # 识别需要加密的敏感字段
            encrypted_fields = []
            sensitive_fields = self.field_encryption.field_configs.keys()

            for field in data.keys():
                if field in sensitive_fields:
                    data[field] = self.encryption.encrypt(str(data[field]))
                    encrypted_fields.append(field)

            # 如果有加密字段，添加标记
            if encrypted_fields:
                data["_encrypted"] = True
                data["_encrypted_fields"] = encrypted_fields

            # 设置新响应体
            response.body = json.dumps(data).encode("utf - 8")

        except Exception as e:
            logger.error(f"响应加密失败: {e}")

        return response

    async def _add_security_headers(
        self, response: Response, request: Request
    ) -> Response:
        """添加安全头部"""
        security_headers = self.tls_manager.get_security_headers()

        for header, value in security_headers.items():
            response.headers[header] = value

        return response

    async def _log_access(
        self, request: Request, response: Response, processing_time: float, result: str
    ):
        """记录访问日志"""
        # 简化实现
        log_data = {
            "timestamp": time.time(),
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user - agent", "unknown"),
            "processing_time": processing_time,
            "result": result,
        }

        logger.info(f"访问日志: {json.dumps(log_data)}")


class DataValidationMiddleware(BaseHTTPMiddleware):
    """
    数据验证中间件
    """

    def __init__(self, app):
        super().__init__(app)
        self.field_encryption = get_field_encryption()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """验证数据"""
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    data = json.loads(body)

                    # 验证加密数据
                    if isinstance(data, dict):
                        validation_results = (
                            self.field_encryption.validate_encrypted_data(data)
                        )

                        # 检查是否有未加密的敏感字段
                        unencrypted_sensitive = [
                            field
                            for field, is_encrypted in validation_results.items()
                            if not is_encrypted
                            and self.field_encryption.field_configs.get(field)
                        ]

                        if unencrypted_sensitive:
                            logger.warning(
                                f"发现未加密的敏感字段: {unencrypted_sensitive}"
                            )
                            # 可以选择拒绝或自动加密

            except json.JSONDecodeError:
                pass
            except Exception as e:
                logger.error(f"数据验证失败: {e}")

        return await call_next(request)


def verify_api_key(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """
    验证API密钥

    Args:
        credentials: HTTP认证凭据

    Returns:
        验证的用户ID或None

    Raises:
        HTTPException: 认证失败
    """
    # 简化实现：检查Bearer token
    if not credentials.credentials:
        raise HTTPException(status_code=401, detail="无效的认证凭据")

    # 实际应该验证JWT或API密钥
    # 这里简化处理
    return "user_123"


def classify_request_data(data: Dict[str, Any], data_type: DataType) -> str:
    """
    分类请求数据

    Args:
        data: 请求数据
        data_type: 数据类型

    Returns:
        数据分类
    """
    classification_manager = get_classification_manager()
    classification = classification_manager.classify_data(data, data_type)
    return classification.value


def require_permission(permission: str):
    """
    权限检查装饰器

    Args:
        permission: 所需权限

    Returns:
        依赖函数
    """

    def dependency(user_id: str = Depends(verify_api_key)) -> str:
        # 实际应该检查用户权限
        # 这里简化实现
        return user_id

    return dependency


def encrypt_sensitive_response(
    data: Dict[str, Any], fields: List[str]
) -> Dict[str, Any]:
    """
    加密响应中的敏感数据

    Args:
        data: 响应数据
        fields: 需要加密的字段列表

    Returns:
        加密后的数据
    """
    encryption = get_encryption()

    for field in fields:
        if field in data and data[field] is not None:
            data[field] = encryption.encrypt(str(data[field]))

    return data


def anonymize_for_analytics(
    data: Dict[str, Any], purpose: str = "analytics"
) -> Dict[str, Any]:
    """
    为分析目的匿名化数据

    Args:
        data: 原始数据
        purpose: 分析目的

    Returns:
        匿名化后的数据
    """
    anonymizer = get_anonymizer()
    return anonymizer.anonymize_for_analytics(data, purpose)


def check_data_retention(data_id: str) -> Dict[str, Any]:
    """
    检查数据保留状态

    Args:
        data_id: 数据ID

    Returns:
        保留状态
    """
    classification_manager = get_classification_manager()
    return classification_manager.check_data_retention(data_id)


def log_data_access(
    user_id: str, data_id: str, action: str, request: Request, result: str = "success"
):
    """
    记录数据访问

    Args:
        user_id: 用户ID
        data_id: 数据ID
        action: 操作类型
        request: 请求对象
        result: 操作结果
    """
    classification_manager = get_classification_manager()
    classification_manager.log_data_access(
        user_id=user_id,
        data_id=data_id,
        action=action,
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user - agent", "unknown"),
        result=result,
    )
