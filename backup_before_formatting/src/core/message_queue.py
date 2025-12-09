"""
消息队列模块 - 基于Redis的异步消息队列
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Callable, Dict, Optional

from pydantic import BaseModel

try:
    import redis.asyncio as redis
except ImportError:
    redis = None


class Message(BaseModel):
    """消息模型"""

    id: str
    type: str
    sender: str
    receiver: Optional[str] = None
    content: Dict[str, Any]
    timestamp: datetime
    ttl: Optional[int] = None
    priority: int = 0


class MessageQueue:
    """基于Redis的异步消息队列"""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.logger = logging.getLogger(__name__)

        # 配置前缀
        self.queue_prefix = "queue:"
        self.channel_prefix = "channel:"
        self.message_prefix = "message:"

    async def initialize(self):
        """初始化Redis连接"""
        if not redis:
            raise RuntimeError("Redis库未安装，请运行: pip install redis")

        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_timeout=5,
                retry_on_timeout=True,
            )

            # 测试连接
            await self.redis_client.ping()
            self.logger.info("Redis连接成功建立")

        except Exception as e:
            self.logger.error(f"Redis连接失败: {e}")
            raise

    async def close(self):
        """关闭Redis连接"""
        if self.redis_client:
            await self.redis_client.close()
            self.logger.info("Redis连接已关闭")

    async def publish_message(
        self,
        message_type: str,
        content: Dict[str, Any],
        sender: str,
        receiver: Optional[str] = None,
        ttl: Optional[int] = None,
        priority: int = 0,
    ) -> str:
        """发布消息"""
        if not self.redis_client:
            raise RuntimeError("消息队列未初始化")

        # 创建消息
        message_id = f"{sender}_{datetime.now().timestamp()}"
        message = Message(
            id=message_id,
            type=message_type,
            sender=sender,
            receiver=receiver,
            content=content,
            timestamp=datetime.now(),
            ttl=ttl,
            priority=priority,
        )

        # 序列化消息
        message_json = message.json()

        try:
            # 使用管道提高性能
            pipe = self.redis_client.pipeline()

            if receiver:
                # 点对点消息 - 使用优先级队列
                queue_name = f"{self.queue_prefix}{receiver}"
                if priority > 0:
                    # 高优先级消息使用不同的队列
                    priority_queue = f"{self.queue_prefix}priority_{receiver}"
                    pipe.lpush(priority_queue, message_json)
                else:
                    pipe.lpush(queue_name, message_json)
                self.logger.debug(f"发送点对点消息到 {receiver}: {message_type}")
            else:
                # 广播消息
                channel_name = f"{self.channel_prefix}{message_type}"
                pipe.publish(channel_name, message_json)
                self.logger.debug(f"广播消息: {message_type}")

            # 设置消息TTL
            if ttl:
                message_key = f"{self.message_prefix}{message_id}"
                pipe.setex(message_key, ttl, message_json)

            # 执行管道操作
            await pipe.execute()

            return message_id

        except Exception as e:
            self.logger.error(f"发布消息失败: {e}")
            raise

    async def subscribe_to_channel(
        self, channel_name: str, agent_id: str, handler: Callable[[Message], None]
    ):
        """订阅频道"""
        if not self.redis_client:
            raise RuntimeError("消息队列未初始化")

        full_channel_name = f"{self.channel_prefix}{channel_name}"

        try:
            pubsub = self.redis_client.pubsub()
            await pubsub.subscribe(full_channel_name)

            self.logger.info(f"Agent {agent_id} 订阅频道: {channel_name}")

            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        message_data = json.loads(message["data"])
                        msg = Message(**message_data)
                        handler(msg)
                    except Exception as e:
                        self.logger.error(f"处理消息失败: {e}")

        except Exception as e:
            self.logger.error(f"订阅频道失败: {e}")
            raise

    async def consume_queue(
        self,
        queue_name: str,
        agent_id: str,
        handler: Callable[[Message], None],
        timeout: int = 1,
    ):
        """消费队列消息"""
        if not self.redis_client:
            raise RuntimeError("消息队列未初始化")

        full_queue_name = f"{self.queue_prefix}{queue_name}"
        priority_queue_name = f"{self.queue_prefix}priority_{queue_name}"

        self.logger.info(f"Agent {agent_id} 开始消费队列: {queue_name}")

        while True:
            try:
                # 优先处理高优先级消息
                priority_message = await self.redis_client.brpop(
                    priority_queue_name, timeout=timeout
                )
                if priority_message:
                    message_data = json.loads(priority_message[1])
                    msg = Message(**message_data)
                    handler(msg)
                    continue

                # 处理普通消息
                message = await self.redis_client.brpop(
                    full_queue_name, timeout=timeout
                )
                if message:
                    message_data = json.loads(message[1])
                    msg = Message(**message_data)
                    handler(msg)

            except Exception as e:
                self.logger.error(f"消费消息失败: {e}")
                await asyncio.sleep(1)  # 错误时等待1秒再重试

    async def get_queue_length(self, queue_name: str) -> int:
        """获取队列长度"""
        if not self.redis_client:
            return 0

        full_queue_name = f"{self.queue_prefix}{queue_name}"
        return await self.redis_client.llen(full_queue_name)

    async def clear_queue(self, queue_name: str):
        """清空队列"""
        if not self.redis_client:
            return

        full_queue_name = f"{self.queue_prefix}{queue_name}"
        priority_queue_name = f"{self.queue_prefix}priority_{queue_name}"

        await self.redis_client.delete(full_queue_name)
        await self.redis_client.delete(priority_queue_name)

        self.logger.info(f"队列已清空: {queue_name}")


# 全局消息队列实例
message_queue = MessageQueue()
