"""
港股量化交易 AI Agent 系统通信协议

定义Agent间通信的标准协议、消息格式、路由机制和广播功能。
确保Agent间通信的标准化、可靠性和可扩展性。
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

from ..core import SystemConfig, SystemConstants
from ..core.message_queue import Message, MessageQueue
from ..models.base import BaseModel, MessageType, SignalType


class ProtocolVersion(str, Enum):
    """协议版本"""

    V1_0 = "1.0"
    V1_1 = "1.1"
    CURRENT = V1_1


class MessagePriority(int, Enum):
    """消息优先级"""

    LOW = 1
    NORMAL = 3
    HIGH = 5
    URGENT = 7
    CRITICAL = 10


class AgentRole(str, Enum):
    """Agent角色"""

    COORDINATOR = "coordinator"
    QUANTITATIVE_ANALYST = "quantitative_analyst"
    QUANTITATIVE_TRADER = "quantitative_trader"
    PORTFOLIO_MANAGER = "portfolio_manager"
    RISK_ANALYST = "risk_analyst"
    DATA_SCIENTIST = "data_scientist"
    QUANTITATIVE_ENGINEER = "quantitative_engineer"
    RESEARCH_ANALYST = "research_analyst"


@dataclass
class ProtocolMessage(BaseModel):
    """协议消息结构"""

    # 消息标识
    message_id: str
    version: ProtocolVersion = ProtocolVersion.CURRENT

    # 路由信息
    sender_id: str
    receiver_id: Optional[str] = None
    broadcast: bool = False

    # 消息内容
    message_type: MessageType
    priority: MessagePriority = MessagePriority.NORMAL
    timestamp: datetime = None

    # 数据载荷
    payload: Dict[str, Any] = None

    # 元数据
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None
    ttl: Optional[int] = None
    retry_count: int = 0
    max_retries: int = 3

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.payload is None:
            self.payload = {}

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProtocolMessage":
        """从字典创建"""
        if "timestamp" in data and isinstance(data["timestamp"], str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)

    def is_expired(self) -> bool:
        """检查消息是否过期"""
        if self.ttl is None:
            return False
        expiry_time = self.timestamp + timedelta(seconds=self.ttl)
        return datetime.now() > expiry_time

    def can_retry(self) -> bool:
        """检查是否可以重试"""
        return self.retry_count < self.max_retries


@dataclass
class RoutingRule(BaseModel):
    """路由规则"""

    pattern: str  # 消息类型模式，支持通配符
    target_agents: List[str]  # 目标Agent ID列表
    priority: MessagePriority = MessagePriority.NORMAL
    conditions: Dict[str, Any] = None  # 路由条件

    def matches(self, message_type: str) -> bool:
        """检查是否匹配消息类型"""
        if "*" in self.pattern:
            # 简单的通配符匹配
            pattern_parts = self.pattern.split("*")
            if len(pattern_parts) == 2:
                prefix, suffix = pattern_parts
                return message_type.startswith(prefix) and message_type.endswith(suffix)
        return self.pattern == message_type


class MessageRouter:
    """消息路由器"""

    def __init__(self):
        self.routing_rules: List[RoutingRule] = []
        self.logger = logging.getLogger("hk_quant_system.protocol.router")

    def add_routing_rule(self, rule: RoutingRule):
        """添加路由规则"""
        self.routing_rules.append(rule)
        self.logger.info(f"添加路由规则: {rule.pattern} -> {rule.target_agents}")

    def remove_routing_rule(self, pattern: str):
        """移除路由规则"""
        self.routing_rules = [
            rule for rule in self.routing_rules if rule.pattern != pattern
        ]
        self.logger.info(f"移除路由规则: {pattern}")

    def route_message(self, message: ProtocolMessage) -> List[str]:
        """路由消息到目标Agent"""
        targets = []

        # 如果是广播消息，返回所有目标
        if message.broadcast:
            for rule in self.routing_rules:
                if rule.matches(message.message_type.value):
                    targets.extend(rule.target_agents)
        else:
            # 点对点消息
            if message.receiver_id:
                targets.append(message.receiver_id)

        return list(set(targets))  # 去重


class AgentProtocol(ABC):
    """Agent通信协议接口"""

    def __init__(self, agent_id: str, message_queue: MessageQueue):
        self.agent_id = agent_id
        self.message_queue = message_queue
        self.router = MessageRouter()
        self.logger = logging.getLogger(f"hk_quant_system.protocol.{agent_id}")

        # 消息处理器
        self.message_handlers: Dict[MessageType, Callable] = {}

        # 统计信息
        self.messages_sent = 0
        self.messages_received = 0
        self.messages_failed = 0

    async def initialize(self):
        """初始化协议"""
        # 注册默认消息处理器
        self.register_handler(MessageType.HEARTBEAT, self._handle_heartbeat)
        self.register_handler(MessageType.CONTROL, self._handle_control)

        # 设置路由规则
        self._setup_default_routing()

        self.logger.info(f"Agent协议初始化完成: {self.agent_id}")

    def register_handler(self, message_type: MessageType, handler: Callable):
        """注册消息处理器"""
        self.message_handlers[message_type] = handler
        self.logger.debug(f"注册消息处理器: {message_type}")

    async def send_message(
        self,
        message_type: MessageType,
        payload: Dict[str, Any],
        receiver_id: Optional[str] = None,
        priority: MessagePriority = MessagePriority.NORMAL,
        ttl: Optional[int] = None,
        correlation_id: Optional[str] = None,
    ) -> str:
        """发送消息"""
        try:
            # 创建协议消息
            protocol_msg = ProtocolMessage(
                message_id=f"{self.agent_id}_{datetime.now().timestamp()}",
                sender_id=self.agent_id,
                receiver_id=receiver_id,
                broadcast=receiver_id is None,
                message_type=message_type,
                priority=priority,
                payload=payload,
                correlation_id=correlation_id,
                ttl=ttl,
            )

            # 路由消息
            targets = self.router.route_message(protocol_msg)

            if not targets and not protocol_msg.broadcast:
                self.logger.warning(f"没有找到消息路由目标: {message_type}")
                return None

            # 发送到消息队列
            message_id = await self.message_queue.publish_message(
                message_type=message_type.value,
                content=protocol_msg.to_dict(),
                sender=self.agent_id,
                receiver=receiver_id,
                priority=priority.value,
                ttl=ttl,
            )

            self.messages_sent += 1
            self.logger.debug(
                f"发送消息: {message_type} -> {receiver_id or 'broadcast'}"
            )

            return message_id

        except Exception as e:
            self.messages_failed += 1
            self.logger.error(f"发送消息失败: {e}")
            raise

    async def send_signal(
        self,
        signal_type: SignalType,
        symbol: str,
        confidence: float,
        reasoning: str,
        target_price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        receiver_id: Optional[str] = None,
    ) -> str:
        """发送交易信号"""
        signal_payload = {
            "signal_type": signal_type.value,
            "symbol": symbol,
            "confidence": confidence,
            "reasoning": reasoning,
            "target_price": target_price,
            "stop_loss": stop_loss,
            "timestamp": datetime.now().isoformat(),
        }

        return await self.send_message(
            message_type=MessageType.SIGNAL,
            payload=signal_payload,
            receiver_id=receiver_id,
            priority=MessagePriority.HIGH,
        )

    async def send_data(
        self, data_type: str, data: Dict[str, Any], receiver_id: Optional[str] = None
    ) -> str:
        """发送数据"""
        data_payload = {
            "data_type": data_type,
            "data": data,
            "timestamp": datetime.now().isoformat(),
        }

        return await self.send_message(
            message_type=MessageType.DATA,
            payload=data_payload,
            receiver_id=receiver_id,
            priority=MessagePriority.NORMAL,
        )

    async def send_control(
        self, command: str, parameters: Dict[str, Any], target_agent: str
    ) -> str:
        """发送控制消息"""
        control_payload = {
            "command": command,
            "parameters": parameters,
            "timestamp": datetime.now().isoformat(),
        }

        return await self.send_message(
            message_type=MessageType.CONTROL,
            payload=control_payload,
            receiver_id=target_agent,
            priority=MessagePriority.URGENT,
        )

    async def broadcast_message(
        self,
        message_type: MessageType,
        payload: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
    ) -> str:
        """广播消息"""
        return await self.send_message(
            message_type=message_type,
            payload=payload,
            receiver_id=None,  # 广播消息
            priority=priority,
        )

    async def handle_incoming_message(self, message: Message):
        """处理接收到的消息"""
        try:
            # 解析协议消息
            protocol_msg = ProtocolMessage.from_dict(message.content)

            # 检查消息是否过期
            if protocol_msg.is_expired():
                self.logger.warning(f"收到过期消息: {protocol_msg.message_id}")
                return

            # 路由到处理器
            if protocol_msg.message_type in self.message_handlers:
                handler = self.message_handlers[protocol_msg.message_type]
                await handler(protocol_msg)
                self.messages_received += 1
            else:
                self.logger.warning(
                    f"没有注册的消息处理器: {protocol_msg.message_type}"
                )

        except Exception as e:
            self.messages_failed += 1
            self.logger.error(f"处理消息失败: {e}")

    async def _handle_heartbeat(self, message: ProtocolMessage):
        """处理心跳消息"""
        self.logger.debug(f"收到心跳: {message.sender_id}")

    async def _handle_control(self, message: ProtocolMessage):
        """处理控制消息"""
        command = message.payload.get("command")
        parameters = message.payload.get("parameters", {})

        self.logger.info(f"收到控制命令: {command} from {message.sender_id}")

        # 可以在这里添加具体的控制命令处理逻辑
        await self._process_control_command(command, parameters, message.sender_id)

    async def _process_control_command(
        self, command: str, parameters: Dict[str, Any], sender_id: str
    ):
        """处理控制命令"""
        # 子类可以重写此方法来实现具体的控制命令处理
        pass

    def _setup_default_routing(self):
        """设置默认路由规则"""
        # 信号消息路由到交易员和投资组合经理
        self.router.add_routing_rule(
            RoutingRule(
                pattern="signal",
                target_agents=["quantitative_trader", "portfolio_manager"],
            )
        )

        # 数据消息路由到分析师
        self.router.add_routing_rule(
            RoutingRule(
                pattern="data",
                target_agents=[
                    "quantitative_analyst",
                    "data_scientist",
                    "research_analyst",
                ],
            )
        )

        # 风险消息路由到风险分析师
        self.router.add_routing_rule(
            RoutingRule(pattern="risk_*", target_agents=["risk_analyst"])
        )

        # 控制消息路由到协调器
        self.router.add_routing_rule(
            RoutingRule(pattern="control", target_agents=["coordinator"])
        )

    def get_protocol_stats(self) -> Dict[str, Any]:
        """获取协议统计信息"""
        return {
            "agent_id": self.agent_id,
            "messages_sent": self.messages_sent,
            "messages_received": self.messages_received,
            "messages_failed": self.messages_failed,
            "success_rate": self.messages_sent
            / max(1, self.messages_sent + self.messages_failed),
            "registered_handlers": list(self.message_handlers.keys()),
            "routing_rules": len(self.router.routing_rules),
        }


class ProtocolManager:
    """协议管理器"""

    def __init__(self, message_queue: MessageQueue):
        self.message_queue = message_queue
        self.protocols: Dict[str, AgentProtocol] = {}
        self.logger = logging.getLogger("hk_quant_system.protocol.manager")

    def register_protocol(self, protocol: AgentProtocol):
        """注册协议"""
        self.protocols[protocol.agent_id] = protocol
        self.logger.info(f"注册Agent协议: {protocol.agent_id}")

    def unregister_protocol(self, agent_id: str):
        """注销协议"""
        if agent_id in self.protocols:
            del self.protocols[agent_id]
            self.logger.info(f"注销Agent协议: {agent_id}")

    async def route_message(self, message: Message):
        """路由消息到相应的协议"""
        try:
            protocol_msg = ProtocolMessage.from_dict(message.content)

            if protocol_msg.receiver_id and protocol_msg.receiver_id in self.protocols:
                protocol = self.protocols[protocol_msg.receiver_id]
                await protocol.handle_incoming_message(message)
            elif protocol_msg.broadcast:
                # 广播消息，发送给所有注册的协议
                for protocol in self.protocols.values():
                    await protocol.handle_incoming_message(message)

        except Exception as e:
            self.logger.error(f"消息路由失败: {e}")

    def get_all_stats(self) -> Dict[str, Any]:
        """获取所有协议的统计信息"""
        stats = {}
        for agent_id, protocol in self.protocols.items():
            stats[agent_id] = protocol.get_protocol_stats()
        return stats


# 导出主要组件
__all__ = [
    "ProtocolVersion",
    "MessagePriority",
    "AgentRole",
    "ProtocolMessage",
    "RoutingRule",
    "MessageRouter",
    "AgentProtocol",
    "ProtocolManager",
]
