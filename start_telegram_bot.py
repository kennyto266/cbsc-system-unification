#!/usr/bin/env python3
"""
启动Telegram量化交易系统Bot
"""

import os
import sys
import subprocess

def main():
    print("🤖 启动Telegram量化交易系统Bot...")
    
    # 检查环境变量
    if not os.getenv("TELEGRAM_BOT_TOKEN"):
        print("❌ 错误: 未设置 TELEGRAM_BOT_TOKEN 环境变量")
        print("请先设置环境变量或创建 .env 文件")
        print("示例: export TELEGRAM_BOT_TOKEN='your_bot_token_here'")
        return
    
    # 检查依赖
    try:
        import telegram
        import pandas
        import numpy
        print("✅ 依赖检查通过")
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("请运行: pip install -r requirements.txt")
        return
    
    # 启动Bot
    try:
        print("🚀 启动Bot...")
        subprocess.run([sys.executable, "telegram_quant_bot.py"], check=True)
    except KeyboardInterrupt:
        print("\n👋 Bot已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")

if __name__ == "__main__":
    main()
