#!/usr/bin/env python3
"""
启动量化交易系统服务器
"""

import os
import sys
import subprocess

def start_server():
    """启动服务器"""
    try:
        # 切换到项目目录
        project_dir = os.path.join(os.path.expanduser("~"), ".cursor", "CODEX 寫量化團隊")
        os.chdir(project_dir)
        
        print(f"当前目录: {os.getcwd()}")
        print("启动量化交易系统...")
        
        # 启动服务器
        subprocess.run([sys.executable, "complete_project_system.py"])
        
    except Exception as e:
        print(f"启动失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    start_server()
