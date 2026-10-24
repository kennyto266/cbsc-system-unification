"""
Webhook服务模块 - 处理Webhook管理和事件分发
"""

import json
import hashlib
import hmac
import uuid
from typing import List, Dict, Any, Optional, Union
import logging
from datetime import datetime, timedelta
import asyncio
from decimal import Decimal

try:
    from svix.api import Svix, SvixOptions
    from svix.exceptions import HttpError as SvixHttpError
except ImportError:
    Svix = None
    SvixOptions = None
    SvixHttpError = None

import httpx
from models.webhooks import (
    WebhookEndpoint, WebhookEndpointCreate, WebhookEndpointUpdate,
    WebhookDelivery, WebhookDeliveryStatus, WebhookEventPayload,
    WebhookRetryConfig, WebhookStats, WebhookEvent, WebhookStatus
)
from config.api_config import get_svix_config, get_api_settings

logger = logging.getLogger(__name__)


class WebhookService:
    """Webhook服务类"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.settings = get_api_settings()
        self._svix_client = None
        self._endpoints_cache = {}  # 简单的内存缓存
        self._delivery_cache = {}  # 投递记录缓存

        # 初始化Svix客户端
        self._init_svix_client()

    def _init_svix_client(self):
        """初始化Svix客户端"""
        try:
            if Svix is None:
                self.logger.warning("Svix库未安装，使用内置Webhook实现")
                return

            svix_config = get_svix_config()
            if not svix_config.get("auth_token"):
                self.logger.warning("Svix认证令牌未配置，使用内置Webhook实现")
                return

            options = SvixOptions(
                server_url=svix_config.get("server_url", "http://localhost:8071")
            )
            self._svix_client = Svix(
                auth_token=svix_config["auth_token"],
                options=options
            )
            self.logger.info("Svix客户端初始化成功")

        except Exception as e:
            self.logger.error(f"Svix客户端初始化失败: {e}")
            self._svix_client = None

    async def create_endpoint(self, endpoint_data: WebhookEndpointCreate) -> WebhookEndpoint:
        """创建Webhook端点"""
        try:
            endpoint_id = str(uuid.uuid4())
            secret = self._generate_secret()

            # 使用Svix创建端点
            if self._svix_client:
                svix_endpoint = await self._create_svix_endpoint(endpoint_data, endpoint_id)
                endpoint_id = svix_endpoint.id

            # 创建本地端点记录
            endpoint = WebhookEndpoint(
                id=endpoint_id,
                url=endpoint_data.url,
                description=endpoint_data.description,
                events=endpoint_data.events,
                secret=secret,
                status=WebhookStatus.ACTIVE,
                headers=endpoint_data.headers,
                timeout=endpoint_data.timeout,
                retry_config=WebhookRetryConfig().dict()
            )

            # 缓存端点
            self._endpoints_cache[endpoint_id] = endpoint

            self.logger.info(f"Webhook端点创建成功: {endpoint_id}")
            return endpoint

        except Exception as e:
            self.logger.error(f"创建Webhook端点失败: {e}")
            raise RuntimeError(f"创建Webhook端点失败: {e}")

    async def _create_svix_endpoint(self, endpoint_data: WebhookEndpointCreate, endpoint_id: str):
        """在Svix中创建端点"""
        try:
            endpoint_in = {
                "url": endpoint_data.url,
                "description": endpoint_data.description or "",
                "version": 1,
                "secret": self._generate_secret(),
                "filterTypes": [event.value for event in endpoint_data.events]
            }

            # 创建应用（如果不存在）
            app_id = "cbsc-trading-platform"
            try:
                await self._svix_client.application.get(app_id)
            except SvixHttpError as e:
                if e.status_code == 404:
                    await self._svix_client.application.create({
                        "name": "CBSC Trading Platform",
                        "uid": app_id
                    })

            return await self._svix_client.endpoint.create(app_id, endpoint_in)

        except Exception as e:
            self.logger.error(f"Svix端点创建失败: {e}")
            raise

    async def update_endpoint(self, endpoint_id: str, update_data: WebhookEndpointUpdate) -> Optional[WebhookEndpoint]:
        """更新Webhook端点"""
        try:
            endpoint = self._endpoints_cache.get(endpoint_id)
            if not endpoint:
                raise ValueError(f"Webhook端点不存在: {endpoint_id}")

            # 更新字段
            update_dict = update_data.dict(exclude_unset=True)
            for field, value in update_dict.items():
                if hasattr(endpoint, field):
                    setattr(endpoint, field, value)

            endpoint.updated_at = datetime.now()

            # 使用Svix更新端点
            if self._svix_client:
                await self._update_svix_endpoint(endpoint_id, update_data)

            # 更新缓存
            self._endpoints_cache[endpoint_id] = endpoint

            self.logger.info(f"Webhook端点更新成功: {endpoint_id}")
            return endpoint

        except Exception as e:
            self.logger.error(f"更新Webhook端点失败: {e}")
            raise RuntimeError(f"更新Webhook端点失败: {e}")

    async def _update_svix_endpoint(self, endpoint_id: str, update_data: WebhookEndpointUpdate):
        """在Svix中更新端点"""
        try:
            app_id = "cbsc-trading-platform"
            endpoint_patch = {}

            if update_data.url:
                endpoint_patch["url"] = update_data.url
            if update_data.description is not None:
                endpoint_patch["description"] = update_data.description
            if update_data.events:
                endpoint_patch["filterTypes"] = [event.value for event in update_data.events]

            if endpoint_patch:
                await self._svix_client.endpoint.patch(app_id, endpoint_id, endpoint_patch)

        except Exception as e:
            self.logger.error(f"Svix端点更新失败: {e}")
            raise

    async def delete_endpoint(self, endpoint_id: str) -> bool:
        """删除Webhook端点"""
        try:
            # 使用Svix删除端点
            if self._svix_client:
                app_id = "cbsc-trading-platform"
                await self._svix_client.endpoint.delete(app_id, endpoint_id)

            # 从缓存中删除
            if endpoint_id in self._endpoints_cache:
                del self._endpoints_cache[endpoint_id]

            self.logger.info(f"Webhook端点删除成功: {endpoint_id}")
            return True

        except Exception as e:
            self.logger.error(f"删除Webhook端点失败: {e}")
            return False

    async def get_endpoint(self, endpoint_id: str) -> Optional[WebhookEndpoint]:
        """获取Webhook端点"""
        return self._endpoints_cache.get(endpoint_id)

    async def list_endpoints(self) -> List[WebhookEndpoint]:
        """列出所有Webhook端点"""
        return list(self._endpoints_cache.values())

    async def trigger_event(self, event_type: WebhookEvent, data: Dict[str, Any]) -> List[WebhookDelivery]:
        """触发Webhook事件"""
        try:
            # 查找订阅此事件的端点
            endpoints = [
                endpoint for endpoint in self._endpoints_cache.values()
                if endpoint.status == WebhookStatus.ACTIVE and event_type in endpoint.events
            ]

            if not endpoints:
                self.logger.info(f"没有端点订阅事件: {event_type}")
                return []

            # 创建事件负载
            payload = WebhookEventPayload(
                event_id=str(uuid.uuid4()),
                event_type=event_type,
                timestamp=datetime.now(),
                data=data
            )

            # 并发发送Webhook
            deliveries = []
            tasks = []

            for endpoint in endpoints:
                delivery = WebhookDelivery(
                    id=str(uuid.uuid4()),
                    endpoint_id=endpoint.id,
                    event_type=event_type,
                    event_data=payload.dict(),
                    status=WebhookDeliveryStatus.PENDING,
                    attempt=1,
                    max_attempts=endpoint.retry_config.get("max_attempts", 3) if endpoint.retry_config else 3
                )
                deliveries.append(delivery)
                tasks.append(self._send_webhook(endpoint, delivery))

            # 并发执行
            await asyncio.gather(*tasks, return_exceptions=True)

            self.logger.info(f"Webhook事件触发成功: {event_type}, 端点数: {len(endpoints)}")
            return deliveries

        except Exception as e:
            self.logger.error(f"触发Webhook事件失败: {e}")
            return []

    async def _send_webhook(self, endpoint: WebhookEndpoint, delivery: WebhookDelivery) -> bool:
        """发送Webhook请求"""
        try:
            # 使用Svix发送事件
            if self._svix_client:
                return await self._send_svix_event(endpoint, delivery)

            # 使用内置HTTP客户端发送
            return await self._send_http_webhook(endpoint, delivery)

        except Exception as e:
            self.logger.error(f"发送Webhook失败: {e}")
            delivery.status = WebhookDeliveryStatus.FAILED
            delivery.error_message = str(e)
            return False

    async def _send_svix_event(self, endpoint: WebhookEndpoint, delivery: WebhookDelivery) -> bool:
        """使用Svix发送事件"""
        try:
            app_id = "cbsc-trading-platform"

            event_out = {
                "eventType": delivery.event_type.value,
                "eventId": delivery.event_data["event_id"],
                "timestamp": delivery.event_data["timestamp"].isoformat(),
                "payload": delivery.event_data["data"]
            }

            await self._svix_client.message.create(app_id, event_out)

            delivery.status = WebhookDeliveryStatus.SUCCESS
            delivery.response_status = 200
            delivery.delivered_at = datetime.now()

            # 更新端点统计
            endpoint.delivery_count += 1
            endpoint.last_triggered = datetime.now()

            return True

        except Exception as e:
            self.logger.error(f"Svix事件发送失败: {e}")
            delivery.status = WebhookDeliveryStatus.FAILED
            delivery.error_message = str(e)
            endpoint.failure_count += 1
            return False

    async def _send_http_webhook(self, endpoint: WebhookEndpoint, delivery: WebhookDelivery) -> bool:
        """使用HTTP客户端发送Webhook"""
        try:
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "CBSC-Webhook/1.0",
                "X-Webhook-Event": delivery.event_type.value,
                "X-Webhook-ID": delivery.event_data["event_id"]
            }

            # 添加自定义头部
            if endpoint.headers:
                headers.update(endpoint.headers)

            # 添加签名
            if endpoint.secret:
                signature = self._generate_signature(
                    endpoint.secret,
                    json.dumps(delivery.event_data, sort_keys=True)
                )
                headers["X-Webhook-Signature"] = f"sha256={signature}"

            # 发送HTTP请求
            async with httpx.AsyncClient(timeout=endpoint.timeout) as client:
                response = await client.post(
                    endpoint.url,
                    json=delivery.event_data,
                    headers=headers
                )

                delivery.response_status = response.status_code
                delivery.response_body = response.text[:1000]  # 限制响应体大小

                if 200 <= response.status_code < 300:
                    delivery.status = WebhookDeliveryStatus.SUCCESS
                    delivery.delivered_at = datetime.now()
                    endpoint.delivery_count += 1
                    endpoint.last_triggered = datetime.now()
                    return True
                else:
                    # 检查是否需要重试
                    retry_config = endpoint.retry_config or WebhookRetryConfig()
                    if (response.status_code in retry_config.retryable_status_codes and
                        delivery.attempt < delivery.max_attempts):
                        delivery.status = WebhookDeliveryStatus.RETRYING
                        # 安排重试
                        await self._schedule_retry(endpoint, delivery)
                    else:
                        delivery.status = WebhookDeliveryStatus.FAILED
                        endpoint.failure_count += 1

                    return False

        except httpx.TimeoutException:
            delivery.status = WebhookDeliveryStatus.FAILED
            delivery.error_message = "请求超时"
            endpoint.failure_count += 1
            return False
        except Exception as e:
            delivery.status = WebhookDeliveryStatus.FAILED
            delivery.error_message = str(e)
            endpoint.failure_count += 1
            return False

    async def _schedule_retry(self, endpoint: WebhookEndpoint, delivery: WebhookDelivery):
        """安排重试"""
        try:
            retry_config = endpoint.retry_config or WebhookRetryConfig()

            # 计算延迟时间
            delay = min(
                retry_config.initial_delay * (retry_config.backoff_multiplier ** (delivery.attempt - 1)),
                retry_config.max_delay
            )

            delivery.next_retry_at = datetime.now() + timedelta(seconds=delay)

            # 在实际实现中，这里应该使用任务队列或调度器
            # 这里简化处理，直接执行重试
            await asyncio.sleep(delay)

            delivery.attempt += 1
            await self._send_webhook(endpoint, delivery)

        except Exception as e:
            self.logger.error(f"安排重试失败: {e}")
            delivery.status = WebhookDeliveryStatus.FAILED
            delivery.error_message = f"重试失败: {e}"

    def _generate_secret(self) -> str:
        """生成Webhook签名密钥"""
        import secrets
        return secrets.token_urlsafe(32)

    def _generate_signature(self, secret: str, payload: str) -> str:
        """生成Webhook签名"""
        return hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()

    async def verify_webhook_signature(self, payload: str, signature: str, secret: str) -> bool:
        """验证Webhook签名"""
        try:
            expected_signature = self._generate_signature(secret, payload)
            return hmac.compare_digest(expected_signature, signature.replace("sha256=", ""))
        except Exception as e:
            self.logger.error(f"验证Webhook签名失败: {e}")
            return False

    async def get_delivery_stats(self, endpoint_id: str) -> Optional[WebhookStats]:
        """获取Webhook投递统计"""
        try:
            endpoint = self._endpoints_cache.get(endpoint_id)
            if not endpoint:
                return None

            # 计算统计数据
            deliveries = [
                delivery for delivery in self._delivery_cache.values()
                if delivery.endpoint_id == endpoint_id
            ]

            total_deliveries = len(deliveries)
            successful_deliveries = len([
                d for d in deliveries if d.status == WebhookDeliveryStatus.SUCCESS
            ])
            failed_deliveries = len([
                d for d in deliveries if d.status == WebhookDeliveryStatus.FAILED
            ])
            pending_deliveries = len([
                d for d in deliveries if d.status == WebhookDeliveryStatus.PENDING
            ])

            success_rate = (successful_deliveries / total_deliveries * 100) if total_deliveries > 0 else 0

            # 计算平均响应时间
            response_times = [
                d.response_body for d in deliveries
                if d.response_status and 200 <= d.response_status < 300
            ]
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0

            # 获取最后时间
            last_delivery = max(deliveries, key=lambda d: d.created_at) if deliveries else None
            last_success = max(
                [d for d in deliveries if d.status == WebhookDeliveryStatus.SUCCESS],
                key=lambda d: d.delivered_at or d.created_at,
                default=None
            )
            last_failure = max(
                [d for d in deliveries if d.status == WebhookDeliveryStatus.FAILED],
                key=lambda d: d.created_at,
                default=None
            )

            return WebhookStats(
                endpoint_id=endpoint_id,
                total_deliveries=total_deliveries,
                successful_deliveries=successful_deliveries,
                failed_deliveries=failed_deliveries,
                pending_deliveries=pending_deliveries,
                success_rate=round(success_rate, 2),
                average_response_time=round(avg_response_time, 2),
                last_delivery_time=last_delivery.created_at if last_delivery else None,
                last_success_time=last_success.delivered_at if last_success else None,
                last_failure_time=last_failure.created_at if last_failure else None
            )

        except Exception as e:
            self.logger.error(f"获取Webhook统计失败: {e}")
            return None

    async def test_endpoint(self, endpoint_id: str) -> Dict[str, Any]:
        """测试Webhook端点"""
        try:
            endpoint = self._endpoints_cache.get(endpoint_id)
            if not endpoint:
                raise ValueError(f"Webhook端点不存在: {endpoint_id}")

            # 创建测试事件
            test_event = {
                "event_id": str(uuid.uuid4()),
                "event_type": "system.test",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "test": True,
                    "message": "这是一个测试事件",
                    "endpoint_id": endpoint_id
                }
            }

            # 发送测试事件
            delivery = WebhookDelivery(
                id=str(uuid.uuid4()),
                endpoint_id=endpoint_id,
                event_type=WebhookEvent.SYSTEM_ERROR,  # 使用系统事件类型
                event_data=test_event,
                status=WebhookDeliveryStatus.PENDING,
                attempt=1,
                max_attempts=1
            )

            success = await self._send_webhook(endpoint, delivery)

            return {
                "success": success,
                "delivery_id": delivery.id,
                "status": delivery.status.value,
                "response_status": delivery.response_status,
                "response_body": delivery.response_body,
                "error_message": delivery.error_message,
                "timestamp": delivery.created_at.isoformat()
            }

        except Exception as e:
            self.logger.error(f"测试Webhook端点失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def get_delivery_history(self, endpoint_id: str, limit: int = 50) -> List[WebhookDelivery]:
        """获取Webhook投递历史"""
        try:
            deliveries = [
                delivery for delivery in self._delivery_cache.values()
                if delivery.endpoint_id == endpoint_id
            ]

            # 按时间倒序排列
            deliveries.sort(key=lambda d: d.created_at, reverse=True)

            return deliveries[:limit]

        except Exception as e:
            self.logger.error(f"获取投递历史失败: {e}")
            return []

    async def retry_failed_delivery(self, delivery_id: str) -> bool:
        """重试失败的投递"""
        try:
            delivery = self._delivery_cache.get(delivery_id)
            if not delivery:
                raise ValueError(f"投递记录不存在: {delivery_id}")

            if delivery.status != WebhookDeliveryStatus.FAILED:
                raise ValueError(f"只能重试失败的投递，当前状态: {delivery.status}")

            endpoint = self._endpoints_cache.get(delivery.endpoint_id)
            if not endpoint:
                raise ValueError(f"Webhook端点不存在: {delivery.endpoint_id}")

            delivery.status = WebhookDeliveryStatus.PENDING
            delivery.attempt += 1
            delivery.error_message = None

            return await self._send_webhook(endpoint, delivery)

        except Exception as e:
            self.logger.error(f"重试投递失败: {e}")
            return False