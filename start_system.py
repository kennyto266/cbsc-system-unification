#!/usr/bin/env python3
"""
启动量化交易系统
"""

import os
import sys

# 切换到正确的目录
project_dir = r"C:\Users\Penguin8n\.cursor\CODEX 寫量化團隊"
os.chdir(project_dir)

# 添加当前目录到Python路径
sys.path.insert(0, project_dir)

# 导入并运行主系统
try:
    import complete_project_system
    print("系统启动成功!")
except Exception as e:
    print(f"系统启动失败: {e}")
    import traceback
    traceback.print_exc()
