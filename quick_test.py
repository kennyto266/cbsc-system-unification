#!/usr/bin/env python3
import os
import sys

import requests

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
if not BOT_TOKEN:
    print("❌ 未设置 TELEGRAM_BOT_TOKEN 环境变量")
    sys.exit(1)

try:
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
    response = requests.get(url, timeout=10)
    if response.status_code == 200:
        data = response.json()
        if data.get('ok'):
            print("✅ Bot连接成功!")
            print(f"Bot: @{data['result']['username']}")
            print(f"名称: {data['result']['first_name']}")
        else:
            print(f"❌ API错误: {data.get('description')}")
    else:
        print(f"❌ HTTP错误: {response.status_code}")
except Exception as e:
    print(f"❌ 错误: {e}")