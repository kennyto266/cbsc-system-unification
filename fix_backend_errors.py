"""
CODEX-- 后端错误快速修复脚本
Quick Fix Script for Backend Syntax Errors
"""

import os
import re

def fix_yfinance_collector():
    """修复 yfinance_collector.py 的异步调用错误"""
    file_path = "src/collectors/yfinance_collector.py"

    if not os.path.exists(file_path):
        print(f"错误: 文件不存在 {file_path}")
        return False

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 检查是否已经修复
    if 'async def fetch_data():' in content:
        print("✅ yfinance_collector.py 已经修复")
        return True

    # 修复: 将 def fetch_data(): 改为 async def fetch_data():
    original = "        def fetch_data():"
    fixed = "        async def fetch_data():"

    if original in content:
        content = content.replace(original, fixed)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("✅ 已修复 yfinance_collector.py (第364行)")
        return True
    else:
        print("⚠️ 未找到需要修复的代码")
        return False


def fix_multiprocess_engine():
    """修复 multiprocess_engine.py 的语法错误"""
    file_path = "src/backtest/multiprocess_engine.py"

    if not os.path.exists(file_path):
        print(f"错误: 文件不存在 {file_path}")
        return False

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 检查第656行
    if len(lines) < 656:
        print(f"错误: 文件行数不足 ({len(lines)} < 656)")
        return False

    line_656 = lines[655]  # 索引从0开始

    # 检查是否已经修复
    if "]))" in line_656 or "])" in line_656:
        print("✅ multiprocess_engine.py 已经修复")
        return True

    # 修复: 添加缺失的闭合括号
    # 原始: returns=pd.Series([equity[i] - equity[i-1] for i in range(1, len(equity))],
    # 修复: returns=pd.Series([equity[i] - equity[i-1] for i in range(1, len(equity))]),
    if "returns=pd.Series" in line_656 and line_656.rstrip().endswith(","):
        lines[655] = line_656.rstrip().rstrip(",") + "),\n"

        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print("✅ 已修复 multiprocess_engine.py (第656行)")
        return True
    else:
        print(f"⚠️ 第656行内容不符合预期: {line_656.strip()}")
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("CODEX-- 后端错误快速修复脚本")
    print("=" * 60)
    print()

    print("修复1: yfinance_collector.py 异步调用错误")
    print("-" * 60)
    result1 = fix_yfinance_collector()
    print()

    print("修复2: multiprocess_engine.py 语法错误")
    print("-" * 60)
    result2 = fix_multiprocess_engine()
    print()

    print("=" * 60)
    if result1 and result2:
        print("✅ 所有错误已修复!")
        print()
        print("下一步:")
        print("1. 测试 Backend API 启动:")
        print("   python -m uvicorn backend.main:app --port 3004")
        print()
        print("2. 测试回测引擎导入:")
        print("   python -c 'from src.backtest.multiprocess_engine import MultiProcessBacktestEngine'")
    else:
        print("⚠️ 部分错误未能自动修复")
        print("请手动检查并修复上述问题")
    print("=" * 60)


if __name__ == "__main__":
    main()
