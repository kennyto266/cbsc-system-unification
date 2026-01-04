#!/usr/bin/env python3
"""
Phase 8.1 WebSocket實時推送系統 - 啟動腳本
WebSocket Server Startup Script
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path
from typing import Optional

# Add src to path
sys.path.insert(0, str(Path(__file__) / "src"))

from src.websocket.websocket_server import (
    WebSocketServerConfig,
    RealtimeWebSocketServer,
    create_server
)
from src.websocket.stream_integrations import get_integration_manager, StreamIntegrationConfig, StreamType
from src.websocket.api_integrations import get_api_integration_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('websocket_server.log')
    ]
)

logger = logging.getLogger(__name__)

class WebSocketServerManager:
    """WebSocket服務器管理器"""

    def __init__(self):
        self.server: Optional[RealtimeWebSocketServer] = None
        self.running = False

    async def start(self):
        """啟動WebSocket服務器"""
        try:
            # Create server configuration
            config = WebSocketServerConfig(
                host="0.0.0.0",
                port=8001,
                redis_url="redis://localhost:6379",
                secret_key="quant-websocket-secret-key-2024",
                enable_compression=True,
                max_connections_per_user=10,
                cors_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
                enable_docs=True
            )

            # Create server
            self.server = await create_server(config)
            logger.info("WebSocket server created successfully")

            # Configure stream integrations
            integration_manager = get_integration_manager(self.server.ws_manager)

            # Configure each stream type
            for stream_type in StreamType:
                stream_config = StreamIntegrationConfig(
                    enabled=True,
                    auto_reconnect=True,
                    reconnect_interval=5.0,
                    max_reconnect_attempts=10,
                    buffer_size=1000,
                    batch_size=10,
                    flush_interval=0.1
                )
                integration_manager.configure_integration(stream_type, stream_config)

            # Start all integrations
            await integration_manager.start_all()

            # Configure API integrations
            api_manager = get_api_integration_manager(self.server.ws_manager)
            await api_manager.start_all()

            # Set up signal handlers
            self._setup_signal_handlers()

            self.running = True
            logger.info("WebSocket server started successfully")

            # Start the server
            await self.server.start()

        except Exception as e:
            logger.error(f"Failed to start WebSocket server: {e}")
            raise

    async def stop(self):
        """停止WebSocket服務器"""
        if not self.running:
            return

        logger.info("Stopping WebSocket server...")
        self.running = False

        # Stop integrations
        if self.server:
            api_manager = get_api_integration_manager(self.server.ws_manager)
            await api_manager.stop_all()

            integration_manager = get_integration_manager(self.server.ws_manager)
            await integration_manager.stop_all()

        logger.info("WebSocket server stopped")

    def _setup_signal_handlers(self):
        """設置信號處理器"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}")
            asyncio.create_task(self.stop())

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

async def main():
    """主函數"""
    import argparse

    parser = argparse.ArgumentParser(description="WebSocket Real-time Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8001, help="Port to bind to")
    parser.add_argument("--redis-url", default="redis://localhost:6379", help="Redis URL")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Log level")

    args = parser.parse_args()

    # Configure logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level))

    # Create server manager
    server_manager = WebSocketServerManager()

    try:
        # Start server
        await server_manager.start()

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Server error: {e}")
    finally:
        # Stop server
        await server_manager.stop()

if __name__ == "__main__":
    asyncio.run(main())