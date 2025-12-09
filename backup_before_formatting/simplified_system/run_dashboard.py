#!/usr/bin/env python3
"""
仪表板快速启动脚本
Dashboard Quick Start Script

快速启动量化交易仪表板的便捷脚本
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """主函数"""
    print("启动量化交易仪表板...")
    print("Starting Quantitative Trading Dashboard...")

    try:
        from src.dashboard import run_dashboard

        # 启动仪表板
        run_dashboard(
            debug=True,  # 开发模式
            port=8050,   # 端口
            host='127.0.0.1'  # 主机
        )

    except ImportError as e:
        print(f"导入错误: {e}")
        print("请确保安装了所需的依赖包:")
        print("pip install dash dash-bootstrap-components plotly pandas numpy")
        return 1

    except Exception as e:
        print(f"启动错误: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())