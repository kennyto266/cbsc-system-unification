#!/usr/bin/env python3
import requests

BOT_TOKEN = "7180490983:AAFbkKnDPC1MHAaOGzQA1fOs9FBwSGGonzI"

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