#!/usr/bin/env python3
"""
部署Telegram量化交易系统Bot
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_dependencies():
    """检查依赖"""
    print("🔍 检查依赖...")
    
    required_packages = [
        'telegram',
        'pandas',
        'numpy',
        'requests',
        'fastapi',
        'uvicorn'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            missing.append(package)
            print(f"❌ {package}")
    
    if missing:
        print(f"\n❌ 缺少依赖: {', '.join(missing)}")
        print("请运行: pip install -r telegram_requirements.txt")
        return False
    
    print("✅ 所有依赖已安装")
    return True

def check_environment():
    """检查环境变量"""
    print("\n🔍 检查环境变量...")
    
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("❌ 未设置 TELEGRAM_BOT_TOKEN")
        print("请设置环境变量或创建 .env 文件")
        return False
    
    print("✅ TELEGRAM_BOT_TOKEN 已设置")
    return True

def check_files():
    """检查必要文件"""
    print("\n🔍 检查必要文件...")
    
    required_files = [
        'telegram_quant_bot.py',
        'complete_project_system.py',
        'telegram_requirements.txt'
    ]
    
    missing = []
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            missing.append(file)
            print(f"❌ {file}")
    
    if missing:
        print(f"\n❌ 缺少文件: {', '.join(missing)}")
        return False
    
    print("✅ 所有必要文件存在")
    return True

def create_env_file():
    """创建环境配置文件"""
    print("\n📝 创建环境配置文件...")
    
    env_file = ".env"
    if os.path.exists(env_file):
        print(f"✅ {env_file} 已存在")
        return True
    
    # 从示例文件复制
    example_file = "telegram_bot.env.example"
    if os.path.exists(example_file):
        shutil.copy(example_file, env_file)
        print(f"✅ 已创建 {env_file} (从 {example_file})")
        print("请编辑 .env 文件并设置正确的配置")
        return True
    else:
        print(f"❌ 找不到 {example_file}")
        return False

def test_system():
    """测试系统"""
    print("\n🧪 测试系统...")
    
    try:
        result = subprocess.run([
            sys.executable, "test_telegram_bot.py"
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ 系统测试通过")
            return True
        else:
            print(f"❌ 系统测试失败: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("❌ 系统测试超时")
        return False
    except Exception as e:
        print(f"❌ 系统测试错误: {e}")
        return False

def main():
    """主部署函数"""
    print("🚀 部署Telegram量化交易系统Bot...\n")
    
    # 检查步骤
    steps = [
        ("检查依赖", check_dependencies),
        ("检查环境变量", check_environment),
        ("检查文件", check_files),
        ("创建环境配置", create_env_file),
        ("测试系统", test_system)
    ]
    
    all_passed = True
    for step_name, step_func in steps:
        if not step_func():
            all_passed = False
            break
    
    print("\n" + "="*50)
    
    if all_passed:
        print("🎉 部署完成！系统准备就绪")
        print("\n📋 启动Bot:")
        print("  python telegram_quant_bot.py")
        print("\n📋 或使用启动脚本:")
        print("  python start_telegram_bot.py")
        print("\n📋 测试Bot功能:")
        print("  python test_telegram_bot.py")
    else:
        print("❌ 部署失败，请解决上述问题后重试")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
