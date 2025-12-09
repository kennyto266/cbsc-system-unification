#!/usr / bin / env python3
"""
Simplified System - Real - time Data Streaming Package
简化系统 - 实时数据流处理包

实时数据处理管道核心模块
Real - time data processing pipeline core modules
"""

from .data_stream import RealTimeDataStreamer, get_streamer
from .event_processor import EventProcessor, get_event_processor
from .signal_generator import SignalGenerator, get_signal_generator
from .websocket_server import WebSocketServer, get_websocket_server

# 可选依赖
try:
    from .kafka_integration import KafkaStreamProcessor, get_kafka_processor

    _KAFKA_AVAILABLE = True
except ImportError:
    _KAFKA_AVAILABLE = False
    KafkaStreamProcessor = None

    def get_kafka_processor(*args, **kwargs):
        raise ImportError("aiokafka is required for Kafka integration")


try:
    from .redis_streams import RedisStreamManager, get_redis_stream_manager

    _REDIS_AVAILABLE = True
except ImportError:
    _REDIS_AVAILABLE = False
    RedisStreamManager = None

    def get_redis_stream_manager(*args, **kwargs):
        raise ImportError("aioredis is required for Redis integration")


__all__ = [
    "RealTimeDataStreamer",
    "get_streamer",
    "EventProcessor",
    "get_event_processor",
    "SignalGenerator",
    "get_signal_generator",
    "WebSocketServer",
    "get_websocket_server",
    "KafkaStreamProcessor",
    "get_kafka_processor",
    "RedisStreamManager",
    "get_redis_stream_manager",
    "_KAFKA_AVAILABLE",
    "_REDIS_AVAILABLE",
]

__version__ = "1.0.0"
__author__ = "Simplified System Team"
