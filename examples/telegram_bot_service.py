import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 确保可以从项目根目录导入 src/*
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.telegram.bot_interface import UserRole
from src.telegram.integration_manager import IntegrationManager


async def main():
    # 优先从指定路径加载 .env
    env_path = os.environ.get("ENV_PATH", "config/bot.env")
    if os.path.exists(env_path):
        load_dotenv(env_path)
    else:
        load_dotenv()

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    admin_id = int(os.getenv("TELEGRAM_ADMIN_CHAT_ID", "0"))
    cursor_cli_path = os.getenv("CURSOR_CLI_PROJECT_PATH", "C:\\Users\\Penguin8n\\Desktop\\CURSOR CLI")
    cursor_api_key = os.getenv("CURSOR_API_KEY")

    # Build config dict per current IntegrationManager signature
    config: dict = {
        'cursor_cli_path': cursor_cli_path,
        'bot_token': bot_token or "",
        'cursor_api_key': cursor_api_key or "",
        'allowed_user_ids': [admin_id] if admin_id else None,
        'allowed_chat_ids': [admin_id] if admin_id else None,
        'command_timeout': 60,
        'max_message_length': 6000,
        'enable_trading_signals': True,
        'enable_system_monitoring': True,
        'enable_cursor_commands': False
    }

    manager = IntegrationManager(config=config)
    print("Starting Telegram Bot service (press Ctrl+C to stop)...")
    try:
        ok = await manager.initialize()
        if not ok:
            print("Failed to initialize IntegrationManager")
            return
        # Keep running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\nService stopped by user.")


if __name__ == "__main__":
    asyncio.run(main())


