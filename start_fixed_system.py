#!/usr/bin/env python3
"""
启动修复后的量化交易系统
"""

import os
import sys
import subprocess

# 切换到项目目录
project_dir = r"C:\Users\Penguin8n\.cursor\CODEX 寫量化團隊"
os.chdir(project_dir)

print(f"当前目录: {os.getcwd()}")
print(f"文件存在: {'complete_project_system.py' in os.listdir('.')}")

# 启动系统
try:
    print("正在启动修复后的量化交易系统...")
    subprocess.run([sys.executable, "complete_project_system.py"], check=True)
except subprocess.CalledProcessError as e:
    print(f"启动失败: {e}")
except FileNotFoundError:
    print("找不到 complete_project_system.py 文件")
