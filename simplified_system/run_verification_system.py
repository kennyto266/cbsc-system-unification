#!/usr / bin / env python3
"""
Phase 5: System Integration and Optimization
驗證系統啟動腳本 - Verification System Runner

使用方法:
    python run_verification_system.py [--config CONFIG_FILE] [--dashboard] [--no - telegram]

選項:
    --config CONFIG_FILE  指定配置文件路徑 (默認: verification_config.yaml)
    --dashboard          啟動監控儀表板
    --no - telegram        禁用Telegram警報
    --test               運行系統測試
    --interactive        交互式模式
"""

import argparse
import asyncio
import logging
import signal
import sys
from pathlib import Path

import yaml

# 導入現有API進行測試
from src.api.government_data import get_hibor_data
from src.api.stock_api import get_stock_data

# 導入驗證系統
from src.verification import (
    VerificationSystem,
    get_verification_system,
    start_verification_system,
)

# Setup logging
logging.basicConfig(
    level = logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("verification_system.log"),
    ],
)

logger = logging.getLogger(__name__)


class VerificationSystemRunner:
    """驗證系統運行器"""

    def __init__(self, config_path: str = "verification_config.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.system = None
        self.is_running = False

    def _load_config(self) -> dict:
        """加載配置文件"""
        try:
            if self.config_path.exists():
                with open(self.config_path, "r", encoding="utf - 8") as f:
                    config = yaml.safe_load(f)
                logger.info(f"Configuration loaded from {self.config_path}")
            else:
                logger.warning(
                    f"Config file {self.config_path} not found, using defaults"
                )
                config = {}
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            config = {}

        return config

    async def start(self):
        """啟動驗證系統"""
        try:
            logger.info("🚀 Starting Verification System...")

            # 啟動系統
            self.system = await start_verification_system(self.config)
            self.is_running = True

            # 顯示系統信息
            await self._display_system_info()

            # 設置信號處理
            self._setup_signal_handlers()

            logger.info("✅ Verification System started successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to start Verification System: {e}")
            return False

    async def stop(self):
        """停止驗證系統"""
        if not self.is_running:
            return

        try:
            logger.info("🛑 Stopping Verification System...")

            if self.system:
                await self.system.stop()

            self.is_running = False
            logger.info("✅ Verification System stopped successfully")

        except Exception as e:
            logger.error(f"❌ Error stopping Verification System: {e}")

    async def _display_system_info(self):
        """顯示系統信息"""
        if not self.system:
            return

        status = self.system.get_system_status()

        print("\n" + "=" * 60)
        print("🔍 VERIFICATION SYSTEM STATUS")
        print("=" * 60)
        print(f"✅ Started: {status['is_started']}")
        print(f"⏱️  Uptime: {status['uptime_formatted']}")
        print(f"📊 Operations: {status['operation_count']}")
        print(f"🌐 Dashboard: {status['dashboard_url']}")

        print("\n🔧 Components:")
        for component, is_active in status["components"].items():
            status_icon = "✅" if is_active else "❌"
            print(f"  {status_icon} {component}: {is_active}")

        print("\n📋 Configuration:")
        print(
            f"  🎯 Verification enabled: {self.config.get('verification_config', {}).get('verification_pipeline', {}).get('layers', {}).get('source_auth', {}).get('enabled', False)}"
        )
        print(
            f"  💾 Cache enabled: {self.config.get('cache', {}).get('enable_compression', False)}"
        )
        print(
            f"  🚀 Async processing: {self.config.get('async_processor', {}).get('enable_monitoring', False)}"
        )
        print(
            f"  📱 Telegram alerts: {self.config.get('telegram', {}).get('enabled', False)}"
        )
        print("=" * 60 + "\n")

    def _setup_signal_handlers(self):
        """設置信號處理器"""

        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down...")
            asyncio.create_task(self.stop())

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    async def run_tests(self):
        """運行系統測試"""
        logger.info("🧪 Running system tests...")

        test_results = {
            "government_data": False,
            "stock_data": False,
            "verification": False,
            "cache": False,
            "async_processing": False,
        }

        try:
            # 測試政府數據API
            logger.info("  Testing government data API...")
            try:
                hibor_data = get_hibor_data(7)
                if hibor_data and hibor_data.get("data"):
                    test_results["government_data"] = True
                    logger.info(f"    ✅ HIBOR data: {len(hibor_data['data'])} records")
                else:
                    logger.warning("    ❌ No HIBOR data received")
            except Exception as e:
                logger.error(f"    ❌ Government data error: {e}")

            # 測試股票數據API
            logger.info("  Testing stock data API...")
            try:
                stock_data = get_stock_data("0700.hk", 30)
                if stock_data and stock_data.get("data"):
                    test_results["stock_data"] = True
                    logger.info(f"    ✅ Stock data received")
                else:
                    logger.warning("    ❌ No stock data received")
            except Exception as e:
                logger.error(f"    ❌ Stock data error: {e}")

            # 測試驗證功能
            logger.info("  Testing verification system...")
            try:
                test_data = {
                    "timestamp": "2025 - 01 - 01T00:00:00Z",
                    "data": {"value": 100, "type": "test"},
                    "source": "test_system",
                }

                result = await self.system.verify_data(
                    test_data, "test_data", "http://example.com"
                )

                if result.composite_score > 0:
                    test_results["verification"] = True
                    logger.info(
                        f"    ✅ Verification score: {result.composite_score:.3f}"
                    )
                    logger.info(
                        f"    ⏱️  Verification time: {result.verification_time_ms:.2f}ms"
                    )
                else:
                    logger.warning("    ❌ Verification failed")
            except Exception as e:
                logger.error(f"    ❌ Verification error: {e}")

            # 測試緩存功能
            logger.info("  Testing cache system...")
            try:
                from src.verification import get_cached, set_cached

                # 設置緩存
                set_cached("test_key", "test_value", data_type="test")

                # 獲取緩存
                cached_value = get_cached("test_key", "test")

                if cached_value == "test_value":
                    test_results["cache"] = True
                    logger.info("    ✅ Cache set / get working")
                else:
                    logger.warning("    ❌ Cache not working")
            except Exception as e:
                logger.error(f"    ❌ Cache error: {e}")

            # 測試異步處理
            logger.info("  Testing async processing...")
            try:
                from src.verification import submit_async_task

                def test_function(x):
                    return x * 2

                await submit_async_task(test_function, (5,))
                test_results["async_processing"] = True
                logger.info("    ✅ Async task submitted")
            except Exception as e:
                logger.error(f"    ❌ Async processing error: {e}")

        except Exception as e:
            logger.error(f"Test suite error: {e}")

        # 顯示測試結果
        print("\n" + "=" * 50)
        print("🧪 SYSTEM TEST RESULTS")
        print("=" * 50)

        passed = 0
        total = len(test_results)

        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status}: {test_name.replace('_', ' ').title()}")
            if result:
                passed += 1

        print("=" * 50)
        print(f"📊 Overall: {passed}/{total} tests passed ({passed / total * 100:.1f}%)")
        print("=" * 50 + "\n")

        return passed == total

    async def interactive_mode(self):
        """交互式模式"""
        print("\n🎮 INTERACTIVE MODE")
        print("=" * 40)
        print("Available commands:")
        print("  verify <data_type>     - Test data verification")
        print("  hibor <days>           - Get HIBOR data")
        print("  stock <symbol> <days> - Get stock data")
        print("  status                - Show system status")
        print("  health                - Run health check")
        print("  cache - stats           - Show cache statistics")
        print("  test                  - Run system tests")
        print("  quit                  - Exit")
        print("=" * 40)

        while self.is_running:
            try:
                command = input("\n🔍 > ").strip().split()
                if not command:
                    continue

                cmd = command[0].lower()

                if cmd == "quit" or cmd == "exit":
                    break
                elif cmd == "verify":
                    await self._interactive_verify(command[1:])
                elif cmd == "hibor":
                    await self._interactive_hibor(command[1:])
                elif cmd == "stock":
                    await self._interactive_stock(command[1:])
                elif cmd == "status":
                    await self._interactive_status()
                elif cmd == "health":
                    await self._interactive_health()
                elif cmd == "cache - stats":
                    await self._interactive_cache_stats()
                elif cmd == "test":
                    await self.run_tests()
                else:
                    print(f"Unknown command: {cmd}")

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")

    async def _interactive_verify(self, args):
        """交互式驗證"""
        if not args:
            print("Usage: verify <data_type>")
            return

        data_type = args[0]
        test_data = {
            "timestamp": "2025 - 01 - 01T00:00:00Z",
            "data": {"value": 100, "type": data_type},
            "source": "interactive_test",
        }

        try:
            result = await self.system.verify_data(
                test_data, data_type, "http://interactive.test"
            )
            print(f"✅ Verification completed:")
            print(f"  Score: {result.composite_score:.3f}")
            print(f"  Time: {result.verification_time_ms:.2f}ms")
            print(f"  Alerts: {len(result.alerts)}")
            if result.alerts:
                for alert in result.alerts:
                    print(f"    - {alert}")
        except Exception as e:
            print(f"❌ Verification error: {e}")

    async def _interactive_hibor(self, args):
        """交互式HIBOR數據獲取"""
        days = int(args[0]) if args else 7

        try:
            data = get_hibor_data(days)
            if data and data.get("data"):
                print(f"✅ HIBOR data ({len(data['data'])} records):")
                for record in data["data"][:3]:  # 顯示前3條
                    print(
                        f"  {record.get('date', 'N / A')}: {record.get('overnight', 'N / A')}%"
                    )
            else:
                print("❌ No HIBOR data received")
        except Exception as e:
            print(f"❌ Error: {e}")

    async def _interactive_stock(self, args):
        """交互式股票數據獲取"""
        if not args:
            print("Usage: stock <symbol> [days]")
            return

        symbol = args[0]
        days = int(args[1]) if len(args) > 1 else 30

        try:
            data = get_stock_data(symbol, days)
            if data and data.get("data"):
                print(f"✅ Stock data for {symbol}:")
                close_data = data["data"].get("close", {})
                if close_data:
                    dates = list(close_data.keys())
                    prices = list(close_data.values())
                    print(f"  Records: {len(close_data)}")
                    print(f"  Date range: {dates[0]} to {dates[-1]}")
                    print(f"  Price range: {min(prices):.2f} - {max(prices):.2f}")
            else:
                print("❌ No stock data received")
        except Exception as e:
            print(f"❌ Error: {e}")

    async def _interactive_status(self):
        """交互式狀態顯示"""
        if self.system:
            await self._display_system_info()
        else:
            print("❌ System not started")

    async def _interactive_health(self):
        """交互式健康檢查"""
        if self.system:
            try:
                health = await self.system.run_health_check()
                print(f"📊 Overall Status: {health['overall_status']}")
                for component, status in health["components"].items():
                    status_icon = "✅" if status["status"] == "healthy" else "❌"
                    print(f"  {status_icon} {component}: {status['status']}")
            except Exception as e:
                print(f"❌ Health check error: {e}")
        else:
            print("❌ System not started")

    async def _interactive_cache_stats(self):
        """交互式緩存統計"""
        try:
            from src.verification import get_cache_stats

            stats = get_cache_stats()

            print("💾 Cache Statistics:")
            print(f"  Hit rate: {stats.get('hit_rate', 0):.2%}")
            print(f"  Entries: {stats.get('entries_count', 0)}")
            print(f"  Memory usage: {stats.get('memory_usage_mb', 0):.2f}MB")
            print(f"  Hits: {stats.get('hits', 0)}")
            print(f"  Misses: {stats.get('misses', 0)}")
        except Exception as e:
            print(f"❌ Cache stats error: {e}")


async def main():
    """主函數"""
    parser = argparse.ArgumentParser(description="Verification System Runner")
    parser.add_argument(
        "--config", default="verification_config.yaml", help="Configuration file path"
    )
    parser.add_argument(
        "--dashboard", action="store_true", help="Start monitoring dashboard"
    )
    parser.add_argument(
        "--no - telegram", action="store_true", help="Disable Telegram alerts"
    )
    parser.add_argument("--test", action="store_true", help="Run system tests")
    parser.add_argument("--interactive", action="store_true", help="Interactive mode")

    args = parser.parse_args()

    # 創建運行器
    runner = VerificationSystemRunner(args.config)

    # 修改配置
    if args.no_telegram:
        runner.config["telegram"] = runner.config.get("telegram", {})
        runner.config["telegram"]["enabled"] = False

    try:
        # 啟動系統
        if not await runner.start():
            sys.exit(1)

        # 運行測試
        if args.test:
            success = await runner.run_tests()
            if not success:
                logger.warning("Some tests failed")

        # 交互式模式
        if args.interactive:
            await runner.interactive_mode()
        elif args.dashboard:
            # 啟動儀表板模式
            logger.info("🌐 Monitoring dashboard is running...")
            logger.info("Press Ctrl + C to stop")

            # 保持運行
            try:
                while runner.is_running:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                pass
        else:
            # 默認模式：運行測試後退出
            if not args.test:
                logger.info("Running default system test...")
                await runner.run_tests()

    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        # 停止系統
        await runner.stop()


if __name__ == "__main__":
    # 運行主程序
    asyncio.run(main())
