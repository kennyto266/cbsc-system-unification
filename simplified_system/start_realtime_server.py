#!/usr / bin / env python3
"""
Simplified System - Real - time Server Launcher
简化系统 - 实时服务器启动器

一键启动完整的实时数据流处理系统
One - click launcher for the complete real - time data streaming system
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Optional

sys.path.append(os.path.dirname(__file__))

from src.streaming.realtime_server import get_streaming_server


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
        "redis": {"enabled": False, "host": "localhost", "port": 6379, "db": 0},
        "kafka": {
            "enabled": False,
            "bootstrap_servers": ["localhost:9092"],
            "group_id": "simplified_system",
        },
        "websocket": {"host": "0.0.0.0", "port": 8002},
        "performance": {"max_workers": 10, "update_interval": 5, "batch_size": 100},
    }

    Path(config_path).parent.mkdir(parents = True, exist_ok = True)
    with open(config_path, "w", encoding="utf - 8") as f:
        json.dump(default_config, f, indent = 2, ensure_ascii = False)

    print(f"Default config created: {config_path}")


async def run_server(symbols: List[str], config_file: Optional[str] = None):
    """运行服务器"""
    try:
        # 获取服务器实例
        server = get_streaming_server()

        print("🚀 Starting Simplified System Real - time Streaming Server...")
        print(f"📊 Monitoring {len(symbols)} symbols: {', '.join(symbols)}")

        # 启动服务器
        await server.start(symbols)

        print("✅ Server started successfully!")
        print(
            f"🔗 WebSocket server: ws://{server.websocket_server.host}:{server.websocket_server.port}"
        )
        print("📈 Real - time data streaming active")
        print("🎯 Signal generation active")

        # 定期状态报告
        while server._running:
            await asyncio.sleep(300)  # 每5分钟报告一次

            try:
                status = await server.get_system_status()
                print(
                    f"\n📊 Server Status Report ({status['uptime_seconds']:.0f}s uptime)"
                )
                print(
                    f"   Active connections: {status['components']['websocket_server']['active_connections']}"
                )
                print(f"   Messages processed: {status['stats']['messages_processed']}")
                print(f"   Signals generated: {status['stats']['signals_generated']}")
                print(f"   Errors: {status['stats']['errors_count']}")

                # 显示活跃信号
                active_signals = await server.get_active_signals()
                if active_signals:
                    print(f"   Active signals: {len(active_signals)}")
                    for symbol, signal in active_signals.items():
                        print(
                            f"     {symbol}: {signal.signal_type.value} ({signal.confidence:.2f})"
                        )

            except Exception as e:
                logging.error(f"Error generating status report: {e}")

    except KeyboardInterrupt:
        print("\n🛑 Received keyboard interrupt, shutting down gracefully...")
    except Exception as e:
        logging.error(f"Server error: {e}")
        print(f"❌ Server error: {e}")
    finally:
        if "server" in locals():
            await server.stop()
        print("✅ Server stopped")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Simplified System Real - time Streaming Server",
        formatter_class = argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start with default symbols
  python start_realtime_server.py

  # Start with custom symbols
  python start_realtime_server.py --symbols 0700.HK,0941.HK,1398.HK

  # Start with config file
  python start_realtime_server.py --config symbols_config.json

  # Create default config file
  python start_realtime_server.py --create - config my_config.json

  # Start with debug logging
  python start_realtime_server.py --log - level DEBUG --log - file server.log
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
        asyncio.run(run_server(symbols, args.config))
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
