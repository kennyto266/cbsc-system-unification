#!/usr/bin/env python3
"""
运行修复后的量化交易系统
"""

import os
import sys
import subprocess

# 设置正确的项目目录
project_dir = os.path.join(os.path.expanduser("~"), ".cursor", "CODEX 寫量化團隊")
os.chdir(project_dir)

print(f"当前目录: {os.getcwd()}")
print(f"项目文件存在: {'complete_project_system.py' in os.listdir('.')}")

# 启动修复后的系统
try:
    print("🚀 启动修复后的量化交易系统...")
    print("📊 功能: 技术分析、策略回测、风险评估、市场情绪分析")
    print("🌐 访问地址: http://localhost:8001")
    print("=" * 60)
    
    # 运行系统
    subprocess.run([sys.executable, "complete_project_system.py"], check=True)
    
except subprocess.CalledProcessError as e:
    print(f"❌ 启动失败: {e}")
    print("请检查 complete_project_system.py 文件是否存在")
except FileNotFoundError as e:
    print(f"❌ 文件未找到: {e}")
    print("请确认项目目录和文件路径正确")
except Exception as e:
    print(f"❌ 未知错误: {e}")