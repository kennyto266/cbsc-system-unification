#!/usr/bin/env python3
"""
Telegram Bot 测试辅助工具
"""

import os
import sys

def check_bot_configuration():
    """检查Bot配置"""
    print("🤖 Telegram Bot 配置检查")
    print("=" * 50)

    # 检查bot文件
    bot_file = "CODEX--/telegram_bot_fixed.py"
    if os.path.exists(bot_file):
        print(f"✅ Bot文件存在: {bot_file}")

        # 检查关键函数是否存在
        try:
            with open(bot_file, 'r', encoding='utf-8') as f:
                content = f.read()

            if 'handle_mention' in content:
                print("✅ handle_mention 函数存在")
            else:
                print("❌ handle_mention 函数未找到")

            if 'penguin8n8' in content:
                print("✅ 已更新支持 @penguin8n8")
            else:
                print("❌ 未找到 @penguin8n8 支持")

            if 'owner_usernames' in content:
                print("✅ 多用户名支持已配置")
            else:
                print("❌ 多用户名支持未配置")

        except Exception as e:
            print(f"❌ 读取bot文件失败: {e}")
    else:
        print(f"❌ Bot文件不存在: {bot_file}")

def check_environment():
    """检查环境配置"""
    print("\n🔧 环境配置检查")
    print("=" * 50)

    # 检查.env文件
    env_files = ['.env', 'telegram_bot.env']
    for env_file in env_files:
        if os.path.exists(env_file):
            print(f"✅ 配置文件存在: {env_file}")
            try:
                with open(env_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                if 'TELEGRAM_BOT_TOKEN' in content:
                    print(f"   📄 {env_file} 包含 TELEGRAM_BOT_TOKEN")
                if 'OWNER_USERNAME' in content:
                    print(f"   📄 {env_file} 包含 OWNER_USERNAME")
                else:
                    print(f"   ⚠️  {env_file} 未找到 OWNER_USERNAME")
            except Exception as e:
                print(f"   ❌ 读取失败: {e}")
        else:
            print(f"❌ 配置文件不存在: {env_file}")

def show_test_instructions():
    """显示测试说明"""
    print("\n🧪 @penguin8n8 自动回复测试说明")
    print("=" * 50)

    print("1. 启动Bot:")
    print("   cd CODEX--")
    print("   python CODEX--/telegram_bot_fixed.py")
    print()
    print("2. 在Telegram中测试:")
    print("   • 在任何聊天中发送: @penguin8n8 你好")
    print("   • 或发送: @penguin8n8 测试消息")
    print("   • Bot应该回复: '我不在 有事留言'")
    print()
    print("3. 预期行为:")
    print("   ✅ 检测到 @penguin8n8 提及")
    print("   ✅ 发送自动回复")
    print("   ✅ 在日志中记录提及检测")
    print()
    print("4. 故障排除:")
    print("   • 检查Bot是否正常运行")
    print("   • 检查TELEGRAM_BOT_TOKEN是否正确")
    print("   • 查看控制台日志是否有错误信息")

def show_bot_info():
    """显示Bot信息"""
    print("\n📋 Bot信息")
    print("=" * 50)

    print("Bot链接: https://t.me/penguin8n")
    print("Bot名称: @penguin8n")
    print("监控用户名:")
    print("  • @penguin8n (原用户名)")
    print("  • @penguin8n8 (你的用户名)")
    print("  • 环境变量OWNER_USERNAME (如果设置)")
    print()
    print("自动回复内容: '我不在 有事留言'")
    print("支持的消息类型: TEXT + mention实体")

if __name__ == "__main__":
    check_bot_configuration()
    check_environment()
    show_test_instructions()
    show_bot_info()

    print("\n" + "=" * 50)
    print("🚀 准备就绪！现在可以启动Bot进行测试")
    print("=" * 50)