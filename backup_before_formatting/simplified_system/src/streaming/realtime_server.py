#!/usr/bin/env python3
"""
Simplified System - Real-time Streaming Server
简化系统 - 实时流处理服务器

统一的实时数据流服务器，整合所有流处理组件
Unified real-time data streaming server integrating all streaming components
"""

import asyncio
import logging
import signal
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

from .data_stream import RealTimeDataStreamer, get_streamer
from .websocket_server import WebSocketServer, get_websocket_server
from .event_processor import EventProcessor, get_event_processor
from .signal_generator import SignalGenerator, get_signal_generator
from .redis_streams import RedisStreamManager, get_redis_stream_manager
from .kafka_integration import KafkaStreamProcessor, get_kafka_processor
from ..config import get_config_manager

logger = logging.getLogger(__name__)

class RealTimeStreamingServer:
    """
    实时流处理服务器
    整合所有实时数据处理组件，提供统一的流处理服务
    """

    def __init__(self, config_path: Optional[str] = None):
        # 加载配置
        self.config_manager = get_config_manager()
        self.config = self.config_manager.system

        # 核心组件
        self.data_streamer = get_streamer()
        self.websocket_server = get_websocket_server()
        self.event_processor = get_event_processor()
        self.signal_generator = get_signal_generator()

        # 可选组件
        self.redis_manager = None
        self.kafka_processor = None

        # 运行状态
        self._running = False
        self._shutdown_event = asyncio.Event()

        # 监控统计
        self.start_time = None
        self._stats = {
            'server_uptime': 0,
            'total_connections': 0,
            'messages_processed': 0,
            'signals_generated': 0,
            'errors_count': 0
        }

        logger.info("Real-time Streaming Server initialized")

    async def initialize(self) -> None:
        """初始化所有组件"""
        logger.info("Initializing Real-time Streaming Server components...")

        try:
            # 初始化Redis（如果配置启用）
            if self._is_redis_enabled():
                await self._initialize_redis()

            # 初始化Kafka（如果配置启用）
            if self._is_kafka_enabled():
                await self._initialize_kafka()

            # 注册事件处理器
            await self._register_event_handlers()

            # 注册WebSocket事件监听器
            await self._register_websocket_listeners()

            logger.info("All components initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            raise

    def _is_redis_enabled(self) -> bool:
        """检查是否启用Redis"""
        redis_config = getattr(self.config, 'redis', {})
        return redis_config.get('enabled', False)

    def _is_kafka_enabled(self) -> bool:
        """检查是否启用Kafka"""
        kafka_config = getattr(self.config, 'kafka', {})
        return kafka_config.get('enabled', False)

    async def _initialize_redis(self) -> None:
        """初始化Redis流管理器"""
        try:
            redis_config = getattr(self.config, 'redis', {})
            self.redis_manager = RedisStreamManager(
                host=redis_config.get('host', 'localhost'),
                port=redis_config.get('port', 6379),
                db=redis_config.get('db', 0),
                password=redis_config.get('password')
            )

            await self.redis_manager.connect()

            # 创建默认流
            await self.redis_manager.create_stream("price_updates", max_length=10000)
            await self.redis_manager.create_stream("trading_signals", max_length=5000)
            await self.redis_manager.create_stream("market_events", max_length=2000)

            logger.info("Redis streams initialized")

        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            raise

    async def _initialize_kafka(self) -> None:
        """初始化Kafka流处理器"""
        try:
            kafka_config = getattr(self.config, 'kafka', {})
            bootstrap_servers = kafka_config.get('bootstrap_servers', ['localhost:9092'])
            group_id = kafka_config.get('group_id', 'simplified_system')

            self.kafka_processor = KafkaStreamProcessor(
                bootstrap_servers=bootstrap_servers,
                group_id=group_id,
                client_id=f"streaming_server_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )

            await self.kafka_processor.start()

            logger.info("Kafka processor initialized")

        except Exception as e:
            logger.error(f"Failed to initialize Kafka: {e}")
            raise

    async def _register_event_handlers(self) -> None:
        """注册事件处理器"""
        # 价格更新事件处理器
        async def handle_price_update(event):
            try:
                symbol = event.symbol
                price_data = event.data

                # 发送到Redis（如果启用）
                if self.redis_manager:
                    await self.redis_manager.write_message(
                        "price_updates",
                        {
                            'symbol': symbol,
                            'price': price_data.get('price'),
                            'volume': price_data.get('volume', 0),
                            'timestamp': event.timestamp.isoformat(),
                            'source': event.source
                        }
                    )

                # 发送到Kafka（如果启用）
                if self.kafka_processor:
                    await self.kafka_processor.send_price_update(
                        symbol,
                        price_data.get('price'),
                        price_data.get('volume', 0),
                        event.source
                    )

                self._stats['messages_processed'] += 1

            except Exception as e:
                logger.error(f"Error handling price update event: {e}")
                self._stats['errors_count'] += 1

        # 技术信号事件处理器
        async def handle_technical_signal(event):
            try:
                symbol = event.symbol
                signal_data = event.data

                # 发送到Redis
                if self.redis_manager:
                    await self.redis_manager.write_message(
                        "trading_signals",
                        {
                            'symbol': symbol,
                            'signal_type': signal_data.get('signal_type'),
                            'signal_value': signal_data.get('signal_value'),
                            'confidence': signal_data.get('confidence'),
                            'timestamp': event.timestamp.isoformat(),
                            'source': event.source
                        }
                    )

                # 发送到Kafka
                if self.kafka_processor:
                    await self.kafka_processor.send_technical_signal(
                        symbol,
                        signal_data.get('signal_type'),
                        signal_data.get('signal_value'),
                        signal_data.get('confidence'),
                        event.source
                    )

                self._stats['signals_generated'] += 1

            except Exception as e:
                logger.error(f"Error handling technical signal event: {e}")
                self._stats['errors_count'] += 1

        # 注册处理器
        self.event_processor.register_handler("price_updates", handle_price_update, async_handler=True)
        self.event_processor.register_handler("technical_signals", handle_technical_signal, async_handler=True)

        logger.info("Event handlers registered")

    async def _register_websocket_listeners(self) -> None:
        """注册WebSocket事件监听器"""
        # 订阅实时数据更新
        symbols = ["0700.HK", "0941.HK", "1398.HK", "0388.HK"]  # 默认监控股票

        for symbol in symbols:
            self.data_streamer.subscribe(symbol, self._on_price_update)

        logger.info(f"WebSocket listeners registered for {len(symbols)} symbols")

    async def _on_price_update(self, data: Dict[str, Any]) -> None:
        """价格更新回调"""
        try:
            # 创建事件并发布
            symbol = data.get('symbol', 'UNKNOWN')
            price = data.get('price', 0.0)
            volume = data.get('volume', 0)

            await self.event_processor.publish_price_update(
                symbol=symbol,
                price=price,
                volume=volume,
                source="data_streamer"
            )

        except Exception as e:
            logger.error(f"Error in price update callback: {e}")
            self._stats['errors_count'] += 1

    async def start(self, symbols: List[str] = None) -> None:
        """启动实时流处理服务器"""
        if self._running:
            logger.warning("Server is already running")
            return

        logger.info("Starting Real-time Streaming Server...")

        try:
            # 记录启动时间
            self.start_time = datetime.now()

            # 初始化组件
            await self.initialize()

            # 启动核心组件
            await self.data_streamer.start_streaming(symbols or ["0700.HK", "0941.HK", "1398.HK"])
            await self.event_processor.start()
            await self.signal_generator.start()
            await self.websocket_server.start()

            self._running = True

            # 设置信号处理器
            self._setup_signal_handlers()

            logger.info("Real-time Streaming Server started successfully")
            logger.info(f"WebSocket server available at ws://{self.websocket_server.host}:{self.websocket_server.port}")

            # 等待关闭信号
            await self._shutdown_event.wait()

        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            await self.stop()
            raise

    async def stop(self) -> None:
        """停止实时流处理服务器"""
        if not self._running:
            return

        logger.info("Stopping Real-time Streaming Server...")

        self._running = False
        self._shutdown_event.set()

        try:
            # 停止所有组件
            await self.data_streamer.stop_streaming()
            await self.event_processor.stop()
            await self.signal_generator.stop()
            await self.websocket_server.stop()

            # 停止可选组件
            if self.redis_manager:
                await self.redis_manager.disconnect()
            if self.kafka_processor:
                await self.kafka_processor.stop()

            logger.info("Real-time Streaming Server stopped")

        except Exception as e:
            logger.error(f"Error stopping server: {e}")

    def _setup_signal_handlers(self) -> None:
        """设置信号处理器"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down...")
            asyncio.create_task(self.stop())

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    async def add_symbol(self, symbol: str) -> None:
        """动态添加监控股票"""
        await self.data_streamer.add_symbol(symbol)
        self.data_streamer.subscribe(symbol, self._on_price_update)
        logger.info(f"Added symbol to monitoring: {symbol}")

    async def remove_symbol(self, symbol: str) -> None:
        """动态移除监控股票"""
        await self.data_streamer.remove_symbol(symbol)
        logger.info(f"Removed symbol from monitoring: {symbol}")

    async def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        uptime = 0
        if self.start_time:
            uptime = (datetime.now() - self.start_time).total_seconds()

        status = {
            'server_status': 'running' if self._running else 'stopped',
            'uptime_seconds': uptime,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'stats': self._stats.copy(),
            'components': {
                'data_streamer': self.data_streamer.get_performance_stats() if self.data_streamer else None,
                'websocket_server': self.websocket_server.get_server_stats() if self.websocket_server else None,
                'event_processor': self.event_processor.get_stats() if self.event_processor else None,
                'signal_generator': self.signal_generator.get_statistics() if self.signal_generator else None,
                'redis_manager': self.redis_manager.get_stats() if self.redis_manager else None,
                'kafka_processor': self.kafka_processor.get_stats() if self.kafka_processor else None
            }
        }

        return status

    async def get_active_signals(self) -> Dict[str, Any]:
        """获取活跃信号"""
        return self.signal_generator.get_active_signals()

    async def get_realtime_data(self, symbols: List[str] = None) -> Dict[str, Any]:
        """获取实时数据"""
        if not symbols:
            return self.data_streamer.get_all_latest_data()

        result = {}
        for symbol in symbols:
            symbol_data = {}

            # 获取价格数据
            tick = self.data_streamer.get_latest_tick(symbol)
            if tick:
                symbol_data['tick'] = tick.to_dict()

            # 获取技术指标
            indicators = self.data_streamer.get_latest_indicators(symbol)
            if indicators:
                symbol_data['indicators'] = {
                    'rsi': indicators.rsi,
                    'macd': indicators.macd,
                    'macd_signal': indicators.macd_signal,
                    'bollinger_upper': indicators.bollinger_upper,
                    'bollinger_lower': indicators.bollinger_lower,
                    'sma_20': indicators.sma_20,
                    'ema_12': indicators.ema_12
                }

            # 获取最新信号
            signal = self.signal_generator.get_latest_signal(symbol)
            if signal:
                symbol_data['signal'] = signal.to_dict()

            if symbol_data:
                result[symbol] = symbol_data

        return result

    async def export_performance_report(self, output_path: str = None) -> str:
        """导出性能报告"""
        try:
            system_status = await self.get_system_status()

            report = {
                'report_type': 'realtime_streaming_performance',
                'generated_at': datetime.now().isoformat(),
                'system_status': system_status,
                'active_signals': await self.get_active_signals(),
                'configuration': {
                    'redis_enabled': self._is_redis_enabled(),
                    'kafka_enabled': self._is_kafka_enabled(),
                    'websocket_port': self.websocket_server.port if self.websocket_server else None
                }
            }

            if not output_path:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_path = f"realtime_streaming_report_{timestamp}.json"

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)

            logger.info(f"Performance report exported to: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Failed to export performance report: {e}")
            raise

# 全局服务器实例
_streaming_server = None

def get_streaming_server() -> RealTimeStreamingServer:
    """获取全局流处理服务器实例"""
    global _streaming_server
    if _streaming_server is None:
        _streaming_server = RealTimeStreamingServer()
    return _streaming_server

if __name__ == "__main__":
    async def main():
        """主函数"""
        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # 创建并启动服务器
        server = RealTimeStreamingServer()

        # 监控的股票列表
        symbols = ["0700.HK", "0941.HK", "1398.HK", "0388.HK", "2318.HK"]

        try:
            await server.start(symbols)

            # 定期打印状态
            while server._running:
                await asyncio.sleep(60)  # 每分钟打印一次状态

                status = await server.get_system_status()
                logger.info(f"Server status: {status['server_status']}, "
                           f"Uptime: {status['uptime_seconds']:.0f}s, "
                           f"Connections: {status['components']['websocket_server']['active_connections']}")

        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt, shutting down...")
        except Exception as e:
            logger.error(f"Server error: {e}")
        finally:
            await server.stop()

    # 运行服务器
    asyncio.run(main())