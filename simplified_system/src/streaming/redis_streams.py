#!/usr / bin / env python3
"""
Simplified System - Redis Streams Manager
简化系统 - Redis流管理器

高性能Redis流数据管理，支持实时数据持久化和分发
High - performance Redis stream management for real - time data persistence and distribution
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set

import aioredis
import redis.asyncio as redis
from redis.asyncio import ConnectionPool

logger = logging.getLogger(__name__)


class RedisStreamManager:
    """
    Redis流管理器
    提供高性能的实时数据流处理和持久化
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        max_connections: int = 20,
    ):
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.max_connections = max_connections

        # Redis连接
        self._redis: Optional[redis.Redis] = None
        self._connection_pool: Optional[ConnectionPool] = None

        # 流配置
        self.streams: Dict[str, Dict[str, Any]] = {}
        self.consumer_groups: Dict[str, Set[str]] = {}
        self._stream_readers: Dict[str, asyncio.Task] = {}

        # 性能配置
        self.batch_size = 100
        self.read_timeout_ms = 5000
        self.block_timeout_ms = 1000

        # 统计信息
        self._stats = {
            "messages_written": 0,
            "messages_read": 0,
            "streams_created": 0,
            "consumer_groups_created": 0,
            "errors": 0,
            "start_time": None,
        }

        logger.info(f"Redis Stream Manager initialized for {host}:{port}")

    async def connect(self) -> None:
        """连接到Redis"""
        try:
            self._connection_pool = ConnectionPool.from_url(
                f"redis://{self.host}:{self.port}/{self.db}",
                password = self.password,
                max_connections = self.max_connections,
                retry_on_timeout = True,
                socket_keepalive = True,
                socket_keepalive_options={},
            )

            self._redis = redis.Redis(connection_pool = self._connection_pool)

            # 测试连接
            await self._redis.ping()

            self._stats["start_time"] = datetime.now()
            logger.info(f"Connected to Redis at {self.host}:{self.port}")

        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def disconnect(self) -> None:
        """断开Redis连接"""
        if self._stream_readers:
            # 停止所有流读取器
            for task in self._stream_readers.values():
                task.cancel()
            await asyncio.gather(*self._stream_readers.values(), return_exceptions = True)
            self._stream_readers.clear()

        if self._connection_pool:
            await self._connection_pool.disconnect()
            self._connection_pool = None

        if self._redis:
            await self._redis.aclose()
            self._redis = None

        logger.info("Disconnected from Redis")

    async def create_stream(
        self,
        stream_name: str,
        max_length: Optional[int] = None,
        trim_strategy: str = "approx",
    ) -> bool:
        """
        创建Redis流

        Args:
            stream_name: 流名称
            max_length: 最大长度
            trim_strategy: 修剪策略 ("exact" 或 "approx")

        Returns:
            bool: 是否成功创建
        """
        try:
            config = {
                "max_length": max_length,
                "trim_strategy": trim_strategy,
                "created_at": datetime.now(),
                "last_activity": datetime.now(),
            }

            self.streams[stream_name] = config
            self._stats["streams_created"] += 1

            logger.info(f"Created Redis stream: {stream_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to create stream {stream_name}: {e}")
            self._stats["errors"] += 1
            return False

    async def write_message(
        self,
        stream_name: str,
        data: Dict[str, Any],
        message_id: Optional[str] = None,
        max_length: Optional[int] = None,
    ) -> Optional[str]:
        """
        写入消息到流

        Args:
            stream_name: 流名称
            data: 消息数据
            message_id: 消息ID（可选）
            max_length: 最大长度（可选）

        Returns:
            str: 消息ID
        """
        if not self._redis:
            raise RuntimeError("Redis connection not established")

        try:
            # 确保流存在
            if stream_name not in self.streams:
                await self.create_stream(stream_name, max_length)

            # 序列化数据
            serialized_data = {}
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    serialized_data[key] = json.dumps(value, default = str)
                elif isinstance(value, datetime):
                    serialized_data[key] = value.isoformat()
                else:
                    serialized_data[key] = str(value)

            # 写入消息
            kwargs = {"name": stream_name, "values": serialized_data}
            if message_id:
                kwargs["id"] = message_id
            if max_length:
                kwargs["maxlen"] = max_length

            message_id = await self._redis.xadd(**kwargs)

            # 更新统计信息
            self._stats["messages_written"] += 1
            self.streams[stream_name]["last_activity"] = datetime.now()

            logger.debug(f"Written message {message_id} to stream {stream_name}")
            return message_id

        except Exception as e:
            logger.error(f"Failed to write message to {stream_name}: {e}")
            self._stats["errors"] += 1
            return None

    async def write_batch(
        self, stream_name: str, messages: List[Dict[str, Any]]
    ) -> List[Optional[str]]:
        """
        批量写入消息

        Args:
            stream_name: 流名称
            messages: 消息列表

        Returns:
            List[str]: 消息ID列表
        """
        if not self._redis:
            raise RuntimeError("Redis connection not established")

        message_ids = []

        try:
            # 使用pipeline批量写入
            pipe = self._redis.pipeline()

            for data in messages:
                serialized_data = {}
                for key, value in data.items():
                    if isinstance(value, (dict, list)):
                        serialized_data[key] = json.dumps(value, default = str)
                    elif isinstance(value, datetime):
                        serialized_data[key] = value.isoformat()
                    else:
                        serialized_data[key] = str(value)

                pipe.xadd(stream_name, serialized_data)

            # 执行批量操作
            results = await pipe.execute()

            message_ids = results
            self._stats["messages_written"] += len(messages)
            self.streams[stream_name]["last_activity"] = datetime.now()

            logger.info(
                f"Batch written {len(messages)} messages to stream {stream_name}"
            )
            return message_ids

        except Exception as e:
            logger.error(f"Failed to batch write to {stream_name}: {e}")
            self._stats["errors"] += 1
            return message_ids

    async def read_messages(
        self, stream_name: str, count: int = 10, block: bool = True
    ) -> List[Dict[str, Any]]:
        """
        读取消息

        Args:
            stream_name: 流名称
            count: 读取数量
            block: 是否阻塞等待

        Returns:
            List[Dict]: 消息列表
        """
        if not self._redis:
            raise RuntimeError("Redis connection not established")

        try:
            # 构建读取参数
            params = {
                "streams": {stream_name: "$"},  # 从最新消息开始读取
                "count": count,
            }

            if block:
                params["block"] = self.block_timeout_ms

            # 读取消息
            result = await self._redis.xread(**params)

            messages = []
            for stream, msgs in result:
                for message_id, fields in msgs:
                    # 反序列化数据
                    deserialized_data = {}
                    for key, value in fields.items():
                        try:
                            # 尝试解析JSON
                            deserialized_data[key] = json.loads(value)
                        except (json.JSONDecodeError, TypeError):
                            # 如果不是JSON，尝试解析datetime
                            try:
                                deserialized_data[key] = datetime.fromisoformat(value)
                            except ValueError:
                                deserialized_data[key] = value

                    messages.append(
                        {
                            "message_id": message_id,
                            "stream": stream,
                            "data": deserialized_data,
                        }
                    )

            self._stats["messages_read"] += len(messages)
            logger.debug(f"Read {len(messages)} messages from stream {stream_name}")

            return messages

        except Exception as e:
            logger.error(f"Failed to read messages from {stream_name}: {e}")
            self._stats["errors"] += 1
            return []

    async def create_consumer_group(
        self, stream_name: str, group_name: str, start_id: str = "0"
    ) -> bool:
        """
        创建消费者组

        Args:
            stream_name: 流名称
            group_name: 组名称
            start_id: 起始消息ID

        Returns:
            bool: 是否成功创建
        """
        if not self._redis:
            raise RuntimeError("Redis connection not established")

        try:
            await self._redis.xgroup_create(
                name = stream_name,
                groupname = group_name,
                id = start_id,
                mkstream = True,  # 如果流不存在则创建
            )

            # 更新消费者组记录
            if stream_name not in self.consumer_groups:
                self.consumer_groups[stream_name] = set()
            self.consumer_groups[stream_name].add(group_name)

            self._stats["consumer_groups_created"] += 1
            logger.info(f"Created consumer group {group_name} for stream {stream_name}")
            return True

        except Exception as e:
            # 如果组已存在，返回True
            if "BUSYGROUP" in str(e):
                logger.info(
                    f"Consumer group {group_name} already exists for stream {stream_name}"
                )
                return True

            logger.error(f"Failed to create consumer group {group_name}: {e}")
            self._stats["errors"] += 1
            return False

    async def read_from_group(
        self,
        stream_name: str,
        group_name: str,
        consumer_name: str,
        count: int = 10,
        block: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        从消费者组读取消息

        Args:
            stream_name: 流名称
            group_name: 组名称
            consumer_name: 消费者名称
            count: 读取数量
            block: 是否阻塞等待

        Returns:
            List[Dict]: 消息列表
        """
        if not self._redis:
            raise RuntimeError("Redis connection not established")

        try:
            # 构建读取参数
            kwargs = {
                "groupname": group_name,
                "consumername": consumer_name,
                "streams": {stream_name: ">"},  # 从未消费的消息开始
                "count": count,
            }

            if block:
                kwargs["block"] = self.block_timeout_ms

            # 读取消息
            result = await self._redis.xreadgroup(**kwargs)

            messages = []
            for stream, msgs in result:
                for message_id, fields in msgs:
                    # 反序列化数据
                    deserialized_data = {}
                    for key, value in fields.items():
                        try:
                            deserialized_data[key] = json.loads(value)
                        except (json.JSONDecodeError, TypeError):
                            try:
                                deserialized_data[key] = datetime.fromisoformat(value)
                            except ValueError:
                                deserialized_data[key] = value

                    messages.append(
                        {
                            "message_id": message_id,
                            "stream": stream,
                            "group": group_name,
                            "consumer": consumer_name,
                            "data": deserialized_data,
                        }
                    )

            self._stats["messages_read"] += len(messages)
            logger.debug(f"Read {len(messages)} messages from group {group_name}")

            return messages

        except Exception as e:
            logger.error(f"Failed to read from group {group_name}: {e}")
            self._stats["errors"] += 1
            return []

    async def acknowledge_message(
        self, stream_name: str, group_name: str, message_id: str
    ) -> bool:
        """
        确认消息处理完成

        Args:
            stream_name: 流名称
            group_name: 组名称
            message_id: 消息ID

        Returns:
            bool: 是否成功确认
        """
        if not self._redis:
            raise RuntimeError("Redis connection not established")

        try:
            await self._redis.xack(stream_name, group_name, message_id)
            logger.debug(f"Acknowledged message {message_id} in group {group_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to acknowledge message {message_id}: {e}")
            self._stats["errors"] += 1
            return False

    async def get_stream_info(self, stream_name: str) -> Optional[Dict[str, Any]]:
        """
        获取流信息

        Args:
            stream_name: 流名称

        Returns:
            Dict: 流信息
        """
        if not self._redis:
            raise RuntimeError("Redis connection not established")

        try:
            info = await self._redis.xinfo_stream(stream_name)

            # 转换时间戳
            if "last - generated - id" in info:
                # 解析时间戳
                timestamp = int(info["last - generated - id"].split("-")[0]) / 1000
                info["last - generated - time"] = datetime.fromtimestamp(timestamp)

            return info

        except Exception as e:
            logger.error(f"Failed to get stream info for {stream_name}: {e}")
            return None

    async def get_group_info(
        self, stream_name: str, group_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        获取消费者组信息

        Args:
            stream_name: 流名称
            group_name: 组名称

        Returns:
            Dict: 组信息
        """
        if not self._redis:
            raise RuntimeError("Redis connection not established")

        try:
            info = await self._redis.xinfo_groups(stream_name)

            # 查找特定组的信息
            for group in info:
                if group["name"] == group_name:
                    return group

            return None

        except Exception as e:
            logger.error(f"Failed to get group info for {group_name}: {e}")
            return None

    async def delete_stream(self, stream_name: str) -> bool:
        """
        删除流

        Args:
            stream_name: 流名称

        Returns:
            bool: 是否成功删除
        """
        if not self._redis:
            raise RuntimeError("Redis connection not established")

        try:
            await self._redis.delete(stream_name)

            # 清理记录
            self.streams.pop(stream_name, None)
            self.consumer_groups.pop(stream_name, None)

            # 停止流读取器
            if stream_name in self._stream_readers:
                self._stream_readers[stream_name].cancel()
                del self._stream_readers[stream_name]

            logger.info(f"Deleted stream {stream_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete stream {stream_name}: {e}")
            self._stats["errors"] += 1
            return False

    async def start_stream_reader(
        self,
        stream_name: str,
        callback: Callable[[Dict[str, Any]], None],
        consumer_group: Optional[str] = None,
        consumer_name: Optional[str] = None,
    ) -> None:
        """
        启动流读取器

        Args:
            stream_name: 流名称
            callback: 回调函数
            consumer_group: 消费者组名称（可选）
            consumer_name: 消费者名称（可选）
        """
        if stream_name in self._stream_readers:
            logger.warning(f"Stream reader for {stream_name} already exists")
            return

        async def stream_reader():
            logger.info(f"Started stream reader for {stream_name}")

            while True:
                try:
                    if consumer_group and consumer_name:
                        # 使用消费者组读取
                        messages = await self.read_from_group(
                            stream_name,
                            consumer_group,
                            consumer_name,
                            count = self.batch_size,
                            block = True,
                        )

                        # 确认消息
                        for msg in messages:
                            try:
                                await callback(msg)
                                await self.acknowledge_message(
                                    stream_name, consumer_group, msg["message_id"]
                                )
                            except Exception as e:
                                logger.error(
                                    f"Error processing message {msg['message_id']}: {e}"
                                )

                    else:
                        # 直接读取流
                        messages = await self.read_messages(
                            stream_name, count = self.batch_size, block = True
                        )

                        for msg in messages:
                            try:
                                await callback(msg)
                            except Exception as e:
                                logger.error(
                                    f"Error processing message {msg['message_id']}: {e}"
                                )

                except Exception as e:
                    logger.error(f"Error in stream reader for {stream_name}: {e}")
                    await asyncio.sleep(1)  # 错误后短暂休息

        # 启动读取器任务
        self._stream_readers[stream_name] = asyncio.create_task(stream_reader())

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        uptime = None
        if self._stats["start_time"]:
            uptime = (datetime.now() - self._stats["start_time"]).total_seconds()

        return {
            **self._stats,
            "uptime_seconds": uptime,
            "active_streams": len(self.streams),
            "active_consumer_groups": sum(
                len(groups) for groups in self.consumer_groups.values()
            ),
            "active_readers": len(self._stream_readers),
            "streams": list(self.streams.keys()),
            "consumer_groups": {
                stream: list(groups) for stream, groups in self.consumer_groups.items()
            },
        }


# 全局Redis流管理器实例
_redis_stream_manager = None


def get_redis_stream_manager() -> RedisStreamManager:
    """获取全局Redis流管理器实例"""
    global _redis_stream_manager
    if _redis_stream_manager is None:
        _redis_stream_manager = RedisStreamManager()
    return _redis_stream_manager


if __name__ == "__main__":

    async def test_redis_streams():
        """测试Redis流管理器"""
        manager = RedisStreamManager()

        try:
            # 连接Redis
            await manager.connect()

            # 创建流
            stream_name = "test_stream"
            await manager.create_stream(stream_name, max_length = 1000)

            # 写入测试消息
            test_messages = [
                {
                    "type": "price_update",
                    "symbol": "0700.HK",
                    "price": 300.0,
                    "timestamp": datetime.now(),
                },
                {
                    "type": "price_update",
                    "symbol": "0941.HK",
                    "price": 50.0,
                    "timestamp": datetime.now(),
                },
                {
                    "type": "signal",
                    "symbol": "0700.HK",
                    "signal": "BUY",
                    "confidence": 0.8,
                },
            ]

            for msg in test_messages:
                message_id = await manager.write_message(stream_name, msg)
                print(f"Written message: {message_id}")

            # 创建消费者组
            await manager.create_consumer_group(stream_name, "test_group")

            # 读取消息
            messages = await manager.read_messages(stream_name, count = 5, block = False)
            print(f"Read {len(messages)} messages:")
            for msg in messages:
                print(f"  {msg}")

            # 读取消费者组消息
            group_messages = await manager.read_from_group(
                stream_name, "test_group", "test_consumer"
            )
            print(f"Read {len(group_messages)} messages from group:")
            for msg in group_messages:
                print(f"  {msg}")
                await manager.acknowledge_message(
                    stream_name, "test_group", msg["message_id"]
                )

            # 获取流信息
            stream_info = await manager.get_stream_info(stream_name)
            print(f"Stream info: {stream_info}")

            # 获取统计信息
            stats = manager.get_stats()
            print(f"Stats: {stats}")

        finally:
            # 清理
            await manager.delete_stream(stream_name)
            await manager.disconnect()

    # 运行测试
    asyncio.run(test_redis_streams())
