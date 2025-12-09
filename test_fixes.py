#!/usr/bin/env python3
"""
测试修复后的系统
"""

import os
import sys
import subprocess

# 切换到项目目录
project_dir = os.path.join(os.path.expanduser("~"), ".cursor", "CODEX 寫量化團隊")
os.chdir(project_dir)

print(f"当前目录: {os.getcwd()}")
print(f"文件存在: {'complete_project_system.py' in os.listdir('.')}")

# 测试语法
try:
    print("检查Python语法...")
    with open('complete_project_system.py', 'r', encoding='utf-8') as f:
        code = f.read()
    compile(code, 'complete_project_system.py', 'exec')
    print("✅ 语法检查通过")
except Exception as e:
    print(f"❌ 语法错误: {e}")
    sys.exit(1)

# 启动系统
try:
    print("🚀 启动修复后的系统...")
    subprocess.run([sys.executable, "complete_project_system.py"], check=True)
except KeyboardInterrupt:
    print("系统已停止")
except Exception as e:
    print(f"❌ 启动失败: {e}")
