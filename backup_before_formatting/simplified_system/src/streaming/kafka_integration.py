#!/usr/bin/env python3
"""
Simplified System - Kafka Integration
简化系统 - Kafka集成模块

Kafka消息队列集成，支持分布式流处理
Kafka message queue integration for distributed stream processing
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Dict, List, Any, Optional, Callable, Union, Set
from datetime import datetime, timedelta
from dataclasses import asdict, dataclass
from enum import Enum
import aiokafka
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from aiokafka.errors import KafkaError, KafkaTimeoutError

logger = logging.getLogger(__name__)

class KafkaMessageType(Enum):
    """Kafka消息类型枚举"""
    PRICE_UPDATE = "price_update"
    TECHNICAL_SIGNAL = "technical_signal"
    RISK_ALERT = "risk_alert"
    MARKET_EVENT = "market_event"
    SYSTEM_STATUS = "system_status"
    HEARTBEAT = "heartbeat"
    CONTROL_COMMAND = "control_command"

@dataclass
class KafkaMessage:
    """Kafka消息数据结构"""
    message_type: KafkaMessageType
    symbol: Optional[str] = None
    timestamp: datetime = None
    data: Dict[str, Any] = None
    source: Optional[str] = None
    correlation_id: Optional[str] = None
    partition_key: Optional[str] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.data is None:
            self.data = {}

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'message_type': self.message_type.value,
            'symbol': self.symbol,
            'timestamp': self.timestamp.isoformat(),
            'data': self.data,
            'source': self.source,
            'correlation_id': self.correlation_id
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KafkaMessage':
        """从字典创建消息"""
        return cls(
            message_type=KafkaMessageType(data['message_type']),
            symbol=data.get('symbol'),
            timestamp=datetime.fromisoformat(data['timestamp']),
            data=data.get('data', {}),
            source=data.get('source'),
            correlation_id=data.get('correlation_id')
        )

class KafkaTopicManager:
    """Kafka主题管理器"""

    def __init__(self, bootstrap_servers: List[str]):
        self.bootstrap_servers = bootstrap_servers
        self.topics: Dict[str, Dict[str, Any]] = {}

        # 默认主题配置
        self.default_topic_config = {
            'num_partitions': 3,
            'replication_factor': 1,
            'retention_ms': 7 * 24 * 60 * 60 * 1000,  # 7天
            'cleanup_policy': 'delete'
        }

    def register_topic(self,
                      topic_name: str,
                      message_types: Set[KafkaMessageType],
                      config: Optional[Dict[str, Any]] = None) -> None:
        """注册主题"""
        topic_config = {**self.default_topic_config}
        if config:
            topic_config.update(config)

        self.topics[topic_name] = {
            'message_types': message_types,
            'config': topic_config,
            'created_at': datetime.now()
        }

        logger.info(f"Registered Kafka topic: {topic_name}")

    def get_topic_for_message_type(self, message_type: KafkaMessageType) -> Optional[str]:
        """根据消息类型获取主题"""
        for topic_name, topic_info in self.topics.items():
            if message_type in topic_info['message_types']:
                return topic_name
        return None

class KafkaStreamProcessor:
    """
    Kafka流处理器
    提供高性能的分布式消息队列处理
    """

    def __init__(self,
                 bootstrap_servers: List[str],
                 group_id: str,
                 client_id: Optional[str] = None):
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self.client_id = client_id or f"kafka_processor_{uuid.uuid4().hex[:8]}"

        # 组件初始化
        self.topic_manager = KafkaTopicManager(bootstrap_servers)
        self.producer: Optional[AIOKafkaProducer] = None
        self.consumers: Dict[str, AIOKafkaConsumer] = {}
        self.message_handlers: Dict[KafkaMessageType, List[Callable]] = {}

        # 运行状态
        self._running = False
        self._consumer_tasks: List[asyncio.Task] = []

        # 统计信息
        self._stats = {
            'messages_sent': 0,
            'messages_received': 0,
            'messages_failed': 0,
            'start_time': None,
            'last_activity': None
        }

        # 注册默认主题
        self._register_default_topics()

        logger.info(f"Kafka Stream Processor initialized with group_id: {self.group_id}")

    def _register_default_topics(self) -> None:
        """注册默认主题"""
        # 价格更新主题
        self.topic_manager.register_topic(
            "price_updates",
            {KafkaMessageType.PRICE_UPDATE},
            {'num_partitions': 6, 'retention_ms': 24 * 60 * 60 * 1000}  # 1天
        )

        # 技术信号主题
        self.topic_manager.register_topic(
            "technical_signals",
            {KafkaMessageType.TECHNICAL_SIGNAL},
            {'num_partitions': 3, 'retention_ms': 7 * 24 * 60 * 60 * 1000}  # 7天
        )

        # 风险警报主题
        self.topic_manager.register_topic(
            "risk_alerts",
            {KafkaMessageType.RISK_ALERT},
            {'num_partitions': 3, 'retention_ms': 30 * 24 * 60 * 60 * 1000}  # 30天
        )

        # 系统状态主题
        self.topic_manager.register_topic(
            "system_status",
            {KafkaMessageType.SYSTEM_STATUS, KafkaMessageType.HEARTBEAT},
            {'num_partitions': 1, 'retention_ms': 24 * 60 * 60 * 1000}  # 1天
        )

        # 控制命令主题
        self.topic_manager.register_topic(
            "control_commands",
            {KafkaMessageType.CONTROL_COMMAND},
            {'num_partitions': 1}
        )

    async def start(self) -> None:
        """启动Kafka处理器"""
        if self._running:
            logger.warning("Kafka processor is already running")
            return

        self._running = True
        self._stats['start_time'] = datetime.now()

        logger.info("Starting Kafka Stream Processor...")

        try:
            # 初始化生产者
            await self._initialize_producer()

            # 初始化消费者
            await self._initialize_consumers()

            logger.info("Kafka Stream Processor started successfully")

        except Exception as e:
            logger.error(f"Failed to start Kafka processor: {e}")
            await self.stop()
            raise

    async def stop(self) -> None:
        """停止Kafka处理器"""
        if not self._running:
            return

        self._running = False
        logger.info("Stopping Kafka Stream Processor...")

        try:
            # 取消消费者任务
            for task in self._consumer_tasks:
                task.cancel()
            await asyncio.gather(*self._consumer_tasks, return_exceptions=True)
            self._consumer_tasks.clear()

            # 停止消费者
            for consumer in self.consumers.values():
                await consumer.stop()
            self.consumers.clear()

            # 停止生产者
            if self.producer:
                await self.producer.stop()
                self.producer = None

            logger.info("Kafka Stream Processor stopped")

        except Exception as e:
            logger.error(f"Error stopping Kafka processor: {e}")

    async def _initialize_producer(self) -> None:
        """初始化生产者"""
        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            client_id=self.client_id,
            value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None,
            acks='all',  # 等待所有副本确认
            retries=3,
            batch_size=16384,
            linger_ms=10,  # 10ms批处理延迟
            compression_type='gzip',
            max_request_size=10 * 1024 * 1024  # 10MB
        )

        await self.producer.start()
        logger.info("Kafka producer initialized")

    async def _initialize_consumers(self) -> None:
        """初始化消费者"""
        # 为每个注册了处理器的消息类型创建消费者
        message_types_to_consume = set(self.message_handlers.keys())

        for message_type in message_types_to_consume:
            topic_name = self.topic_manager.get_topic_for_message_type(message_type)
            if not topic_name:
                logger.warning(f"No topic found for message type: {message_type}")
                continue

            try:
                consumer = AIOKafkaConsumer(
                    topic_name,
                    bootstrap_servers=self.bootstrap_servers,
                    group_id=self.group_id,
                    client_id=f"{self.client_id}_{topic_name}",
                    value_deserializer=lambda v: json.loads(v.decode('utf-8')),
                    auto_offset_reset='latest',
                    enable_auto_commit=True,
                    auto_commit_interval_ms=1000,
                    session_timeout_ms=30000,
                    heartbeat_interval_ms=3000
                )

                await consumer.start()
                self.consumers[topic_name] = consumer

                # 启动消费者任务
                task = asyncio.create_task(
                    self._consumer_loop(topic_name, consumer),
                    name=f"consumer_{topic_name}"
                )
                self._consumer_tasks.append(task)

                logger.info(f"Started consumer for topic: {topic_name}")

            except Exception as e:
                logger.error(f"Failed to start consumer for {topic_name}: {e}")

    async def _consumer_loop(self, topic_name: str, consumer: AIOKafkaConsumer) -> None:
        """消费者循环"""
        logger.info(f"Consumer loop started for {topic_name}")

        while self._running:
            try:
                # 批量消费消息
                message_batch = await consumer.getmany(timeout_ms=1000)

                for topic_partition, messages in message_batch.items():
                    for message in messages:
                        await self._process_message(message)

            except KafkaTimeoutError:
                continue  # 超时继续循环
            except Exception as e:
                logger.error(f"Error in consumer loop for {topic_name}: {e}")
                await asyncio.sleep(1)  # 错误后短暂休息

        logger.info(f"Consumer loop stopped for {topic_name}")

    async def _process_message(self, message) -> None:
        """处理接收到的消息"""
        try:
            # 解析消息
            message_data = message.value
            kafka_message = KafkaMessage.from_dict(message_data)

            # 更新统计信息
            self._stats['messages_received'] += 1
            self._stats['last_activity'] = datetime.now()

            logger.debug(f"Received message: {kafka_message.message_type.value} from {kafka_message.source}")

            # 调用注册的处理器
            handlers = self.message_handlers.get(kafka_message.message_type, [])
            for handler in handlers:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(kafka_message)
                    else:
                        handler(kafka_message)
                except Exception as e:
                    logger.error(f"Error in message handler: {e}")

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            self._stats['messages_failed'] += 1

    async def send_message(self, message: KafkaMessage) -> bool:
        """
        发送消息

        Args:
            message: 要发送的消息

        Returns:
            bool: 是否成功发送
        """
        if not self.producer:
            raise RuntimeError("Producer not initialized")

        try:
            # 确定目标主题
            topic_name = self.topic_manager.get_topic_for_message_type(message.message_type)
            if not topic_name:
                logger.error(f"No topic configured for message type: {message.message_type}")
                return False

            # 确定分区键
            partition_key = message.partition_key or message.symbol or message.correlation_id

            # 发送消息
            await self.producer.send_and_wait(
                topic=topic_name,
                value=message.to_dict(),
                key=partition_key
            )

            # 更新统计信息
            self._stats['messages_sent'] += 1
            self._stats['last_activity'] = datetime.now()

            logger.debug(f"Sent message to {topic_name}: {message.message_type.value}")
            return True

        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            self._stats['messages_failed'] += 1
            return False

    async def send_batch(self, messages: List[KafkaMessage]) -> int:
        """
        批量发送消息

        Args:
            messages: 消息列表

        Returns:
            int: 成功发送的消息数量
        """
        if not self.producer:
            raise RuntimeError("Producer not initialized")

        sent_count = 0

        try:
            # 按主题分组消息
            messages_by_topic: Dict[str, List[KafkaMessage]] = {}
            for message in messages:
                topic_name = self.topic_manager.get_topic_for_message_type(message.message_type)
                if topic_name:
                    if topic_name not in messages_by_topic:
                        messages_by_topic[topic_name] = []
                    messages_by_topic[topic_name].append(message)

            # 批量发送
            for topic_name, topic_messages in messages_by_topic.items():
                for message in topic_messages:
                    partition_key = message.partition_key or message.symbol or message.correlation_id

                    await self.producer.send(
                        topic=topic_name,
                        value=message.to_dict(),
                        key=partition_key
                    )
                    sent_count += 1

            await self.producer.flush()  # 确保所有消息发送完成

            # 更新统计信息
            self._stats['messages_sent'] += sent_count
            self._stats['last_activity'] = datetime.now()

            logger.info(f"Batch sent {sent_count} messages")
            return sent_count

        except Exception as e:
            logger.error(f"Failed to send batch messages: {e}")
            self._stats['messages_failed'] += len(messages) - sent_count
            return sent_count

    def register_handler(self,
                        message_type: KafkaMessageType,
                        handler: Callable[[KafkaMessage], None]) -> None:
        """
        注册消息处理器

        Args:
            message_type: 消息类型
            handler: 处理函数
        """
        if message_type not in self.message_handlers:
            self.message_handlers[message_type] = []

        self.message_handlers[message_type].append(handler)
        logger.info(f"Registered handler for {message_type.value}")

    def unregister_handler(self,
                          message_type: KafkaMessageType,
                          handler: Callable[[KafkaMessage], None]) -> None:
        """取消注册消息处理器"""
        if message_type in self.message_handlers:
            try:
                self.message_handlers[message_type].remove(handler)
                logger.info(f"Unregistered handler for {message_type.value}")
            except ValueError:
                pass

    def create_message(self,
                      message_type: KafkaMessageType,
                      data: Dict[str, Any],
                      symbol: Optional[str] = None,
                      source: Optional[str] = None,
                      correlation_id: Optional[str] = None,
                      partition_key: Optional[str] = None) -> KafkaMessage:
        """
        创建Kafka消息

        Args:
            message_type: 消息类型
            data: 消息数据
            symbol: 股票代码
            source: 消息源
            correlation_id: 关联ID
            partition_key: 分区键

        Returns:
            KafkaMessage: 创建的消息
        """
        return KafkaMessage(
            message_type=message_type,
            symbol=symbol,
            data=data,
            source=source or self.client_id,
            correlation_id=correlation_id,
            partition_key=partition_key
        )

    async def send_price_update(self,
                               symbol: str,
                               price: float,
                               volume: int = 0,
                               source: Optional[str] = None) -> bool:
        """发送价格更新消息"""
        message = self.create_message(
            KafkaMessageType.PRICE_UPDATE,
            {'price': price, 'volume': volume},
            symbol=symbol,
            source=source
        )
        return await self.send_message(message)

    async def send_technical_signal(self,
                                   symbol: str,
                                   signal_type: str,
                                   signal_value: float,
                                   confidence: float,
                                   source: Optional[str] = None) -> bool:
        """发送技术信号消息"""
        message = self.create_message(
            KafkaMessageType.TECHNICAL_SIGNAL,
            {
                'signal_type': signal_type,
                'signal_value': signal_value,
                'confidence': confidence
            },
            symbol=symbol,
            source=source
        )
        return await self.send_message(message)

    async def send_risk_alert(self,
                             symbol: str,
                             alert_type: str,
                             alert_level: str,
                             message: str,
                             source: Optional[str] = None) -> bool:
        """发送风险警报消息"""
        alert_message = self.create_message(
            KafkaMessageType.RISK_ALERT,
            {
                'alert_type': alert_type,
                'alert_level': alert_level,
                'alert_message': message
            },
            symbol=symbol,
            source=source
        )
        return await self.send_message(alert_message)

    async def send_heartbeat(self, status: Dict[str, Any]) -> bool:
        """发送心跳消息"""
        heartbeat = self.create_message(
            KafkaMessageType.HEARTBEAT,
            {
                'status': status,
                'timestamp': datetime.now().isoformat(),
                'processor_id': self.client_id
            }
        )
        return await self.send_message(heartbeat)

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        uptime = None
        if self._stats['start_time']:
            uptime = (datetime.now() - self._stats['start_time']).total_seconds()

        return {
            **self._stats,
            'uptime_seconds': uptime,
            'group_id': self.group_id,
            'client_id': self.client_id,
            'registered_topics': list(self.topic_manager.topics.keys()),
            'active_consumers': len(self.consumers),
            'registered_handlers': {
                msg_type.value: len(handlers)
                for msg_type, handlers in self.message_handlers.items()
            }
        }

# 全局Kafka流处理器实例
_kafka_processor = None

def get_kafka_processor(bootstrap_servers: List[str], group_id: str) -> KafkaStreamProcessor:
    """获取Kafka流处理器实例"""
    global _kafka_processor
    if _kafka_processor is None:
        _kafka_processor = KafkaStreamProcessor(bootstrap_servers, group_id)
    return _kafka_processor

if __name__ == "__main__":
    async def test_kafka_integration():
        """测试Kafka集成"""
        # 假设本地Kafka运行在默认端口
        bootstrap_servers = ['localhost:9092']
        group_id = f"test_group_{uuid.uuid4().hex[:8]}"

        processor = KafkaStreamProcessor(bootstrap_servers, group_id)

        # 定义测试处理器
        async def price_update_handler(message: KafkaMessage):
            print(f"Received price update: {message.symbol} - ${message.data['price']}")

        async def signal_handler(message: KafkaMessage):
            print(f"Received signal: {message.symbol} - {message.data['signal_type']}")

        # 注册处理器
        processor.register_handler(KafkaMessageType.PRICE_UPDATE, price_update_handler)
        processor.register_handler(KafkaMessageType.TECHNICAL_SIGNAL, signal_handler)

        try:
            # 启动处理器
            await processor.start()

            # 发送测试消息
            await processor.send_price_update("0700.HK", 300.0, 1000)
            await processor.send_technical_signal("0700.HK", "BUY", 0.8, 0.9)
            await processor.send_risk_alert("0700.HK", "VOLATILITY", "HIGH", "High volatility detected")

            # 发送心跳
            await processor.send_heartbeat({"status": "healthy", "cpu": "50%"})

            # 批量发送
            batch_messages = []
            for i in range(5):
                msg = processor.create_message(
                    KafkaMessageType.PRICE_UPDATE,
                    {'price': 300.0 + i, 'volume': 1000 + i * 100},
                    symbol="0700.HK"
                )
                batch_messages.append(msg)

            sent_count = await processor.send_batch(batch_messages)
            print(f"Sent {sent_count} messages in batch")

            # 等待消息处理
            await asyncio.sleep(5)

            # 获取统计信息
            stats = processor.get_stats()
            print(f"Stats: {stats}")

        finally:
            # 停止处理器
            await processor.stop()

    # 运行测试（需要Kafka服务器）
    # asyncio.run(test_kafka_integration())