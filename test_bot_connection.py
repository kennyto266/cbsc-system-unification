#!/usr/bin/env python3
"""
测试Telegram Bot连接
"""

import os
import requests
import json

# 设置Bot Token
BOT_TOKEN = "7180490983:AAFbkKnDPC1MHAaOGzQA1fOs9FBwSGGonzI"
BOT_USERNAME = "penguinai_bot"

def test_bot_connection():
    """测试Bot连接"""
    print(f"🤖 测试Telegram Bot连接...")
    print(f"📱 Bot: @{BOT_USERNAME}")
    print(f"🔑 Token: {BOT_TOKEN[:10]}...")
    
    try:
        # 获取Bot信息
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                bot_info = data.get('result', {})
                print("✅ Bot连接成功!")
                print(f"   ID: {bot_info.get('id')}")
                print(f"   用户名: @{bot_info.get('username')}")
                print(f"   名称: {bot_info.get('first_name')}")
                print(f"   是否Bot: {bot_info.get('is_bot')}")
                return True
            else:
                print(f"❌ API返回错误: {data.get('description')}")
                return False
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 连接错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        return False

def test_bot_commands():
    """测试Bot命令"""
    print(f"\n📋 测试Bot命令...")
    
    try:
        # 获取Bot命令
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMyCommands"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                commands = data.get('result', [])
                print("✅ Bot命令获取成功!")
                print("📋 可用命令:")
                for cmd in commands:
                    print(f"   /{cmd.get('command')} - {cmd.get('description')}")
                return True
            else:
                print(f"❌ 命令获取失败: {data.get('description')}")
                return False
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 命令测试错误: {e}")
        return False

def main():
    """主函数"""
    print("🚀 开始测试Telegram Bot...\n")
    
    # 测试连接
    connection_ok = test_bot_connection()
    
    if connection_ok:
        # 测试命令
        commands_ok = test_bot_commands()
        
        print("\n" + "="*50)
        if connection_ok and commands_ok:
            print("🎉 Bot测试完成! Bot已准备就绪")
            print(f"\n📱 在Telegram中搜索: @{BOT_USERNAME}")
            print("💬 发送 /start 开始使用")
            print("\n📋 可用命令:")
            print("   /analyze <股票代码> - 技术分析")
            print("   /optimize <股票代码> - 策略优化")
            print("   /risk <股票代码> - 风险评估")
            print("   /sentiment <股票代码> - 情绪分析")
            print("   /status - 系统状态")
            print("   /help - 帮助信息")
        else:
            print("❌ Bot测试失败，请检查配置")
    else:
        print("❌ Bot连接失败，请检查Token")

if __name__ == "__main__":
    main()
