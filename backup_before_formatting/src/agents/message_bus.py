"""
Message Bus Implementation
消息總線實現

提供智能體之間的異步消息通信機制，支持點對點、廣播和
主題訂閱模式。
"""

import asyncio
import time
import uuid
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Set

from ..core.logging import get_logger, log_performance
from ..core.exceptions import AgentError
from .base_agent import AgentMessage, AgentStatus


class MessageBus:
    """
    Central message bus for agent communication.
    智能體通信的中央消息總線。
    """

    def __init__(self, max_queue_size: int = 1000):
        """
        Initialize message bus.

        Args:
            max_queue_size: Maximum queue size per agent
        """
        self.max_queue_size = max_queue_size
        self.logger = get_logger("agents.message_bus")

        # Message queues and routing
        self._queues: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_queue_size))
        self._subscriptions: Dict[str, Set[str]] = defaultdict(set)
        self._message_handlers: Dict[str, Callable] = {}

        # Performance tracking
        self._stats = {
            'messages_sent': 0,
            'messages_delivered': 0,
            'messages_failed': 0,
            'broadcast_messages': 0,
            'subscriptions': 0,
            'active_agents': set(),
            'start_time': datetime.now()
        }

        # Background task for message delivery
        self._delivery_task: Optional[asyncio.Task] = None
        self._running = False

        self.logger.info("Message bus initialized", max_queue_size=max_queue_size)

    async def start(self):
        """Start the message bus."""
        if self._running:
            return

        self._running = True
        self._delivery_task = asyncio.create_task(self._delivery_loop())
        self.logger.info("Message bus started")

    async def stop(self):
        """Stop the message bus."""
        if not self._running:
            return

        self._running = False
        if self._delivery_task:
            self._delivery_task.cancel()
            try:
                await self._delivery_task
            except asyncio.CancelledError:
                pass

        self.logger.info("Message bus stopped")

    @log_performance("send_message")
    async def send_message(self, message: AgentMessage) -> bool:
        """
        Send a message to a specific agent.

        Args:
            message: Message to send

        Returns:
            True if message was queued successfully, False otherwise
        """
        try:
            # Validate message
            if not self._validate_message(message):
                return False

            # Add message to recipient's queue
            self._queues[message.receiver].append(message)
            self._stats['messages_sent'] += 1

            self.logger.debug(
                "Message queued",
                sender=message.sender,
                receiver=message.receiver,
                message_type=message.message_type,
                message_id=message.message_id
            )

            return True

        except Exception as e:
            self._stats['messages_failed'] += 1
            self.logger.error(
                "Failed to send message",
                sender=message.sender,
                receiver=message.receiver,
                error=str(e)
            )
            return False

    @log_performance("broadcast_message")
    async def broadcast_message(
        self,
        message: AgentMessage,
        exclude_senders: Optional[List[str]] = None
    ) -> int:
        """
        Broadcast message to all agents.

        Args:
            message: Message to broadcast
            exclude_senders: List of agent IDs to exclude from broadcast

        Returns:
            Number of agents message was sent to
        """
        try:
            exclude_senders = exclude_senders or []
            exclude_senders.append(message.sender)  # Don't send to self

            sent_count = 0
            for agent_id in self._stats['active_agents']:
                if agent_id not in exclude_senders:
                    broadcast_msg = AgentMessage(
                        message_id=str(uuid.uuid4()),
                        sender=message.sender,
                        receiver=agent_id,
                        message_type=message.message_type,
                        content=message.content,
                        timestamp=message.timestamp,
                        correlation_id=message.correlation_id,
                        priority=message.priority,
                        metadata={**message.metadata, 'broadcast': True}
                    )

                    if await self.send_message(broadcast_msg):
                        sent_count += 1

            self._stats['broadcast_messages'] += 1

            self.logger.info(
                "Message broadcast",
                sender=message.sender,
                message_type=message.message_type,
                sent_to=sent_count,
                excluded=exclude_senders
            )

            return sent_count

        except Exception as e:
            self._stats['messages_failed'] += 1
            self.logger.error(
                "Failed to broadcast message",
                sender=message.sender,
                error=str(e)
            )
            return 0

    async def publish_to_topic(self, topic: str, message: AgentMessage) -> int:
        """
        Publish message to a topic.

        Args:
            topic: Topic name
            message: Message to publish

        Returns:
            Number of subscribers that received the message
        """
        try:
            if topic not in self._subscriptions:
                self.logger.debug("No subscribers for topic", topic=topic)
                return 0

            subscribers = self._subscriptions[topic].copy()
            sent_count = 0

            for subscriber_id in subscribers:
                # Skip if subscriber is not active
                if subscriber_id not in self._stats['active_agents']:
                    continue

                # Don't send to self
                if subscriber_id == message.sender:
                    continue

                topic_message = AgentMessage(
                    message_id=str(uuid.uuid4()),
                    sender=message.sender,
                    receiver=subscriber_id,
                    message_type=f"topic.{topic}",
                    content={
                        'topic': topic,
                        'original_message': message.content
                    },
                    timestamp=message.timestamp,
                    correlation_id=message.correlation_id,
                    priority=message.priority,
                    metadata={**message.metadata, 'topic': topic}
                )

                if await self.send_message(topic_message):
                    sent_count += 1

            self.logger.debug(
                "Message published to topic",
                topic=topic,
                sender=message.sender,
                sent_to=sent_count,
                total_subscribers=len(subscribers)
            )

            return sent_count

        except Exception as e:
            self._stats['messages_failed'] += 1
            self.logger.error(
                "Failed to publish to topic",
                topic=topic,
                error=str(e)
            )
            return 0

    def subscribe_to_topic(self, agent_id: str, topic: str) -> bool:
        """
        Subscribe an agent to a topic.

        Args:
            agent_id: Agent ID to subscribe
            topic: Topic name

        Returns:
            True if subscription was successful, False otherwise
        """
        try:
            if agent_id not in self._stats['active_agents']:
                self.logger.warning(
                    "Cannot subscribe inactive agent",
                    agent_id=agent_id,
                    topic=topic
                )
                return False

            self._subscriptions[topic].add(agent_id)
            self._stats['subscriptions'] += 1

            self.logger.info(
                "Agent subscribed to topic",
                agent_id=agent_id,
                topic=topic
            )

            return True

        except Exception as e:
            self.logger.error(
                "Failed to subscribe to topic",
                agent_id=agent_id,
                topic=topic,
                error=str(e)
            )
            return False

    def unsubscribe_from_topic(self, agent_id: str, topic: str) -> bool:
        """
        Unsubscribe an agent from a topic.

        Args:
            agent_id: Agent ID to unsubscribe
            topic: Topic name

        Returns:
            True if unsubscription was successful, False otherwise
        """
        try:
            if topic in self._subscriptions and agent_id in self._subscriptions[topic]:
                self._subscriptions[topic].remove(agent_id)
                self._stats['subscriptions'] -= 1

                # Remove empty topic
                if not self._subscriptions[topic]:
                    del self._subscriptions[topic]

                self.logger.info(
                    "Agent unsubscribed from topic",
                    agent_id=agent_id,
                    topic=topic
                )
                return True

            return False

        except Exception as e:
            self.logger.error(
                "Failed to unsubscribe from topic",
                agent_id=agent_id,
                topic=topic,
                error=str(e)
            )
            return False

    async def register_agent(self, agent_id: str) -> bool:
        """
        Register an agent with the message bus.

        Args:
            agent_id: Agent ID to register

        Returns:
            True if registration was successful, False otherwise
        """
        try:
            self._stats['active_agents'].add(agent_id)

            # Initialize queue for new agent
            if agent_id not in self._queues:
                self._queues[agent_id] = deque(maxlen=self.max_queue_size)

            self.logger.info("Agent registered", agent_id=agent_id)
            return True

        except Exception as e:
            self.logger.error(
                "Failed to register agent",
                agent_id=agent_id,
                error=str(e)
            )
            return False

    async def unregister_agent(self, agent_id: str) -> bool:
        """
        Unregister an agent from the message bus.

        Args:
            agent_id: Agent ID to unregister

        Returns:
            True if unregistration was successful, False otherwise
        """
        try:
            self._stats['active_agents'].discard(agent_id)

            # Clean up agent's queue
            if agent_id in self._queues:
                del self._queues[agent_id]

            # Remove from all topic subscriptions
            for topic, subscribers in self._subscriptions.items():
                subscribers.discard(agent_id)

            self.logger.info("Agent unregistered", agent_id=agent_id)
            return True

        except Exception as e:
            self.logger.error(
                "Failed to unregister agent",
                agent_id=agent_id,
                error=str(e)
            )
            return False

    async def get_messages(self, agent_id: str, timeout: float = 1.0) -> List[AgentMessage]:
        """
        Get messages for an agent.

        Args:
            agent_id: Agent ID
            timeout: Timeout in seconds

        Returns:
            List of messages
        """
        try:
            messages = []

            if agent_id in self._queues:
                queue = self._queues[agent_id]

                # Get all available messages
                while queue:
                    messages.append(queue.popleft())

            if messages:
                self._stats['messages_delivered'] += len(messages)
                self.logger.debug(
                    "Messages delivered",
                    agent_id=agent_id,
                    count=len(messages)
                )

            return messages

        except Exception as e:
            self.logger.error(
                "Failed to get messages",
                agent_id=agent_id,
                error=str(e)
            )
            return []

    def get_stats(self) -> Dict[str, Any]:
        """
        Get message bus statistics.

        Returns:
            Dictionary with statistics
        """
        uptime = (datetime.now() - self._stats['start_time']).total_seconds()

        return {
            'uptime_seconds': uptime,
            'messages_sent': self._stats['messages_sent'],
            'messages_delivered': self._stats['messages_delivered'],
            'messages_failed': self._stats['messages_failed'],
            'broadcast_messages': self._stats['broadcast_messages'],
            'subscriptions': self._stats['subscriptions'],
            'active_agents': len(self._stats['active_agents']),
            'registered_agents': list(self._stats['active_agents']),
            'topics': list(self._subscriptions.keys()),
            'queue_sizes': {
                agent_id: len(queue) for agent_id, queue in self._queues.items()
            },
            'delivery_rate': (
                self._stats['messages_delivered'] / max(1, self._stats['messages_sent']) * 100
            )
        }

    def _validate_message(self, message: AgentMessage) -> bool:
        """Validate message format and content."""
        if not message.message_id:
            self.logger.warning("Message missing ID")
            return False

        if not message.sender or not message.receiver:
            self.logger.warning("Message missing sender or receiver")
            return False

        if not message.message_type:
            self.logger.warning("Message missing type")
            return False

        # Check if receiver is active
        if message.receiver not in self._stats['active_agents']:
            self.logger.warning(
                "Receiver not active",
                receiver=message.receiver
            )
            return False

        return True

    async def _delivery_loop(self):
        """Background task for message processing."""
        self.logger.info("Message delivery loop started")

        while self._running:
            try:
                # This is a placeholder for any background processing
                # Could be used for message routing, filtering, etc.
                await asyncio.sleep(1)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Message delivery loop error: {e}")
                await asyncio.sleep(5)

        self.logger.info("Message delivery loop stopped")


# Global message bus instance
_message_bus: Optional[MessageBus] = None


def get_message_bus() -> MessageBus:
    """
    Get global message bus instance.

    Returns:
        MessageBus instance
    """
    global _message_bus
    if _message_bus is None:
        _message_bus = MessageBus()
    return _message_bus


def reset_message_bus():
    """Reset global message bus instance."""
    global _message_bus
    _message_bus = None