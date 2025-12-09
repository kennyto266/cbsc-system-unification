#!/usr/bin/env python3
"""
簡化系統 - Telegram Bot 啟動器
Simplified System - Telegram Bot Launcher

便捷啟動Telegram量化交易Bot
Convenient launcher for Telegram quantitative trading bot
"""

import os
import sys
import logging
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import telegram
        logger.info("✅ python-telegram-bot installed")
    except ImportError:
        logger.error("❌ python-telegram-bot not installed")
        logger.error("Please install: pip install python-telegram-bot")
        return False

    try:
        import requests
        logger.info("✅ requests installed")
    except ImportError:
        logger.error("❌ requests not installed")
        logger.error("Please install: pip install requests")
        return False

    try:
        import pandas
        logger.info("✅ pandas installed")
    except ImportError:
        logger.error("❌ pandas not installed")
        logger.error("Please install: pip install pandas")
        return False

    try:
        import aiohttp
        logger.info("✅ aiohttp installed")
    except ImportError:
        logger.error("❌ aiohttp not installed")
        logger.error("Please install: pip install aiohttp")
        return False

    try:
        from dotenv import load_dotenv
        logger.info("✅ python-dotenv installed")
    except ImportError:
        logger.error("❌ python-dotenv not installed")
        logger.error("Please install: pip install python-dotenv")
        return False

    return True

def check_environment():
    """Check if required environment variables are set"""
    # Load environment variables from .env file
    try:
        from dotenv import load_dotenv
        load_dotenv()
        logger.info("✅ Environment variables loaded from .env file")
    except Exception as e:
        logger.warning(f"⚠️ Could not load .env file: {e}")

    # Check required environment variables
    required_vars = ['TELEGRAM_BOT_TOKEN']
    missing_vars = []

    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        logger.error("❌ Missing required environment variables:")
        for var in missing_vars:
            logger.error(f"   • {var}")

        logger.error("\nPlease set these environment variables in your .env file or environment:")
        for var in missing_vars:
            logger.error(f"   export {var}=your_value")

        return False

    logger.info("✅ All required environment variables are set")
    return True

def check_modules():
    """Check if our simplified system modules are available"""
    try:
        from src.telegram.telegram_bot import telegram_bot
        logger.info("✅ Telegram bot module available")
    except ImportError as e:
        logger.error(f"❌ Cannot import telegram bot module: {e}")
        return False

    try:
        from src.api.stock_api import stock_api
        logger.info("✅ Stock API module available")
    except ImportError as e:
        logger.error(f"❌ Cannot import stock API module: {e}")
        return False

    try:
        from src.data.government_data import government_collector
        logger.info("✅ Government data module available")
    except ImportError as e:
        logger.error(f"❌ Cannot import government data module: {e}")
        return False

    return True

async def test_connections():
    """Test connections to external APIs"""
    logger.info("🔍 Testing connections...")

    # Test stock API
    try:
        from src.api.stock_api import stock_api
        test_data = stock_api.get_stock_data("0700.HK", 1)
        if test_data:
            logger.info("✅ Stock API connection successful")
        else:
            logger.warning("⚠️ Stock API connection returned no data")
    except Exception as e:
        logger.error(f"❌ Stock API connection failed: {e}")
        return False

    # Test government data collector
    try:
        from src.data.government_data import government_collector
        logger.info(f"✅ Government data collector ready with {len(government_collector.data_sources)} data sources")
    except Exception as e:
        logger.error(f"❌ Government data collector failed: {e}")
        return False

    logger.info("🎯 All connections tested successfully")
    return True

def display_startup_info():
    """Display startup information"""
    print("\n" + "="*60)
    print("🤖 簡化系統 - Telegram量化交易Bot")
    print("Simplified System - Telegram Quantitative Trading Bot")
    print("="*60)
    print("\n📊 功能特性:")
    print("  • 股票技術分析 (RSI, MA, 價格變動)")
    print("  • 香港政府數據 (HIBOR, 匯率, 貨幣基數)")
    print("  • 系統狀態監控")
    print("  • 自動回應功能")
    print("\n🔧 系統狀態:")
    print(f"  • Python版本: {sys.version.split()[0]}")
    print(f"  • 項目路徑: {project_root}")
    print(f"  • Bot狀態: 初始化中...")
    print("\n📋 可用命令:")
    print("  • /start - 歡迎信息")
    print("  • /help - 幫助信息")
    print("  • /analyze <代碼> - 股票技術分析")
    print("  • /govdata - 查看政府數據")
    print("  • /collectgov <source> - 收集數據")
    print("  • /status - 系統狀態")
    print("  • /health - 健康檢查")
    print("\n💡 使用範例:")
    print("  /analyze 0700.HK - 分析騰訊控股")
    print("  /govdata - 查看HIBOR利率")
    print("  /collectgov hibor_rates - 收集HIBOR數據")
    print("\n🔗 數據來源:")
    print("  • 股票數據: http://18.180.162.113:9191")
    print("  • 政府數據: 香港金融管理局API")
    print("\n" + "="*60)
    print("Bot啟動中...\n")

def main():
    """Main function"""
    try:
        # Display startup information
        display_startup_info()

        # Check dependencies
        logger.info("🔍 Checking dependencies...")
        if not check_dependencies():
            logger.error("❌ Dependency check failed. Please install missing packages.")
            sys.exit(1)

        # Check environment
        logger.info("🔍 Checking environment...")
        if not check_environment():
            logger.error("❌ Environment check failed. Please set required environment variables.")
            sys.exit(1)

        # Check modules
        logger.info("🔍 Checking modules...")
        if not check_modules():
            logger.error("❌ Module check failed. Please check your installation.")
            sys.exit(1)

        # Test connections (async)
        logger.info("🔍 Testing connections...")
        try:
            import asyncio
            if not asyncio.run(test_connections()):
                logger.error("❌ Connection tests failed. Please check your network and API endpoints.")
                sys.exit(1)
        except Exception as e:
            logger.error(f"❌ Connection test error: {e}")
            logger.warning("⚠️ Continuing without connection tests...")

        # Start the bot
        logger.info("🚀 Starting Telegram bot...")

        from src.telegram.telegram_bot import telegram_bot

        # Set up signal handlers for graceful shutdown
        import signal

        def signal_handler(signum, frame):
            logger.info(f"🛑 Received signal {signum}, shutting down gracefully...")
            asyncio.create_task(telegram_bot.shutdown())
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Run the bot
        telegram_bot.run()

    except KeyboardInterrupt:
        logger.info("🛑 Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        logger.exception("Full traceback:")
        sys.exit(1)

if __name__ == "__main__":
    main()