#!/usr / bin / env python3
"""
Simplified System - Basic Real - time Server Launcher
简化系统 - 基础实时服务器启动器

基础版本的实时数据流处理系统启动器
Basic version real - time data streaming system launcher
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Optional

# 添加路径
sys.path.append(os.path.dirname(__file__))

# 基础导入，避免可选依赖
from src.streaming.data_stream import get_streamer
from src.streaming.event_processor import get_event_processor
from src.streaming.signal_generator import get_signal_generator
from src.streaming.websocket_server import get_websocket_server


# 配置日志
def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None):
    """设置日志配置"""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        Path(log_file).parent.mkdir(parents = True, exist_ok = True)
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level = getattr(logging, log_level.upper()), format = log_format, handlers = handlers
    )


def load_symbols_config(config_path: Optional[str] = None) -> List[str]:
    """加载股票配置"""
    if not config_path:
        # 默认港股列表
        return [
            "0700.HK",  # 腾讯
            "0941.HK",  # 中国移动
            "1398.HK",  # 工商银行
            "0388.HK",  # 港交所
            "2318.HK",  # 中国平安
            "1299.HK",  # 友邦保险
            "0005.HK",  # 汇丰控股
            "0939.HK",  # 建设银行
            "2628.HK",  # 中国人寿
            "0883.HK",  # 中国海洋石油
        ]

    try:
        with open(config_path, "r", encoding="utf - 8") as f:
            config = json.load(f)
            return config.get("symbols", [])
    except Exception as e:
        logging.error(f"Failed to load symbols config: {e}")
        return []


def create_default_config(config_path: str):
    """创建默认配置文件"""
    default_config = {
        "symbols": ["0700.HK", "0941.HK", "1398.HK", "0388.HK", "2318.HK"],
        "websocket": {"host": "0.0.0.0", "port": 8002},
        "performance": {"max_workers": 10, "update_interval": 5, "batch_size": 100},
    }

    Path(config_path).parent.mkdir(parents = True, exist_ok = True)
    with open(config_path, "w", encoding="utf - 8") as f:
        json.dump(default_config, f, indent = 2, ensure_ascii = False)

    print(f"Default config created: {config_path}")


class BasicRealtimeServer:
    """基础实时服务器"""

    def __init__(self):
        self.data_streamer = get_streamer()
        self.websocket_server = get_websocket_server()
        self.event_processor = get_event_processor()
        self.signal_generator = get_signal_generator()

        self._running = False
        self.start_time = None

    async def start(self, symbols: List[str]):
        """启动基础服务器"""
        if self._running:
            logging.warning("Server is already running")
            return

        try:
            self.start_time = datetime.now()
            self._running = True

            print("Starting Basic Real - time Streaming Server...")
            print(f"Monitoring {len(symbols)} symbols: {', '.join(symbols)}")

            # 注册事件处理器
            self._register_handlers()

            # 启动所有组件
            await self.data_streamer.start_streaming(symbols)
            await self.event_processor.start()
            await self.signal_generator.start()
            await self.websocket_server.start()

            print("Basic Server started successfully!")
            print(
                f"WebSocket server: ws://{self.websocket_server.host}:{self.websocket_server.port}"
            )
            print("Real - time data streaming active")
            print("Signal generation active")

            # 定期状态报告
            while self._running:
                await asyncio.sleep(60)  # 每分钟报告一次

                try:
                    await self._print_status()
                except Exception as e:
                    logging.error(f"Error in status report: {e}")

        except KeyboardInterrupt:
            print("\nReceived keyboard interrupt, shutting down gracefully...")
        except Exception as e:
            logging.error(f"Server error: {e}")
            print(f"Server error: {e}")
        finally:
            await self.stop()

    def _register_handlers(self):
        """注册事件处理器"""

        async def price_handler(event):
            symbol = event.symbol
            price_data = event.data
            print(f"Price Update: {symbol} - ${price_data.get('price', 'N / A')}")

        async def signal_handler(event):
            symbol = event.symbol
            signal_data = event.data
            print(
                f"Signal: {symbol} - {signal_data.get('signal_type', 'N / A')} (confidence: {signal_data.get('confidence', 'N / A')})"
            )

        from src.streaming.event_processor import EventFilter, EventType

        price_filter = EventFilter(event_types={EventType.PRICE_UPDATE})
        signal_filter = EventFilter(event_types={EventType.TECHNICAL_SIGNAL})

        self.event_processor.register_handler(
            "price_updates", price_handler, price_filter, async_handler = True
        )
        self.event_processor.register_handler(
            "signal_updates", signal_handler, signal_filter, async_handler = True
        )

    async def _print_status(self):
        """打印状态信息"""
        try:
            uptime = (datetime.now() - self.start_time).total_seconds()
            streamer_stats = self.data_streamer.get_performance_stats()
            ws_stats = self.websocket_server.get_server_stats()
            active_signals = self.signal_generator.get_active_signals()

            print(f"\nServer Status Report ({uptime:.0f}s uptime)")
            print(f"   Active connections: {ws_stats.get('active_connections', 0)}")
            print(f"   Messages processed: {streamer_stats.get('total_updates', 0)}")
            print(f"   Active signals: {len(active_signals)}")

            if active_signals:
                for symbol, signal in list(active_signals.items())[:3]:  # 显示前3个信号
                    print(
                        f"     {symbol}: {signal.signal_type.value} ({signal.confidence:.2f})"
                    )

        except Exception as e:
            logging.error(f"Error generating status report: {e}")

    async def stop(self):
        """停止服务器"""
        if not self._running:
            return

        self._running = False
        logging.info("Stopping Basic Real - time Server...")

        try:
            await self.data_streamer.stop_streaming()
            await self.event_processor.stop()
            await self.signal_generator.stop()
            await self.websocket_server.stop()
            logging.info("Basic Server stopped")
        except Exception as e:
            logging.error(f"Error stopping server: {e}")


async def run_basic_server(symbols: List[str]):
    """运行基础服务器"""
    server = BasicRealtimeServer()
    await server.start(symbols)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Simplified System Basic Real - time Streaming Server",
        formatter_class = argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start with default symbols
  python start_basic_realtime_server.py

  # Start with custom symbols
  python start_basic_realtime_server.py --symbols 0700.HK,0941.HK,1398.HK

  # Start with config file
  python start_basic_realtime_server.py --config symbols_config.json

  # Create default config file
  python start_basic_realtime_server.py --create - config my_config.json

  # Start with debug logging
  python start_basic_realtime_server.py --log - level DEBUG --log - file server.log
        """,
    )

    parser.add_argument(
        "--symbols", type = str, help="Comma - separated list of stock symbols to monitor"
    )

    parser.add_argument(
        "--config", type = str, help="Path to configuration file (JSON format)"
    )

    parser.add_argument(
        "--create - config",
        type = str,
        help="Create a default configuration file at specified path",
    )

    parser.add_argument(
        "--log - level",
        type = str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Set logging level (default: INFO)",
    )

    parser.add_argument("--log - file", type = str, help="Log file path (optional)")

    args = parser.parse_args()

    # 创建配置文件
    if args.create_config:
        create_default_config(args.create_config)
        return

    # 设置日志
    setup_logging(args.log_level, args.log_file)

    # 加载股票列表
    symbols = None
    if args.symbols:
        symbols = [s.strip().upper() for s in args.symbols.split(",")]
        # 确保.HK后缀
        symbols = [s if s.endswith(".HK") else f"{s}.HK" for s in symbols]
    else:
        symbols = load_symbols_config(args.config)

    if not symbols:
        print("❌ No symbols specified. Use --symbols or provide a config file.")
        sys.exit(1)

    # 运行服务器
    try:
        asyncio.run(run_basic_server(symbols))
    except KeyboardInterrupt:
        print("\nGoodbye!")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # 导入datetime用于状态报告
    from datetime import datetime

    main()
