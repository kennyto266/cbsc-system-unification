#!/usr/bin/env python3
"""
设置环境变量

Token 应从 .env 文件或 shell 环境加载，切勿硬编码到源码中。
参见 .env.example 了解所需变量。
"""

import os

# Telegram Bot Token 应来自环境（例如通过 python-dotenv 从 .env 加载）
token = os.environ.get("TELEGRAM_BOT_TOKEN")
if token:
    print(f"✅ TELEGRAM_BOT_TOKEN 已设置 (长度 {len(token)})")
else:
    print("⚠️ 未检测到 TELEGRAM_BOT_TOKEN，请在 .env 或 shell 中设置")
