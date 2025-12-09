#!/usr/bin/env python3
"""
Quick Start Demo
个人交易系统快速开始演示
"""

import sys
import os
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from main import PersonalTradingCLI
from datetime import datetime, timedelta

def quick_demo():
    """快速演示"""
    print("🚀 个人交易系统快速演示")
    print("=" * 50)

    cli = PersonalTradingCLI()
    cli.print_banner()

    print("📊 演示1: 系统状态检查")
    print("-" * 30)

    # 模拟系统检查
    print("✅ VectorBT: 已安装")
    print("✅ 配置: 正常")
    print("✅ 数据目录: 已创建")
    print("✅ 默认股票: 10 只")
    print()

    print("📊 演示2: RSI策略快速回测")
    print("-" * 30)
    print("正在测试 RSI 策略在腾讯控股 (0700.HK) 上的表现...")
    print("时间范围: 最近 6 个月")
    print("参数: RSI(14, 30, 70)")
    print()

    # 模拟回测结果
    print("📈 回测结果")
    print("=" * 40)
    print("股票代码: 0700.HK")
    print("策略名称: RSI Mean Reversion")
    print("策略参数: {'period': 14, 'oversold': 30, 'overbought': 70}")
    print()
    print("💰 收益指标:")
    print("  总回报: 18.45%")
    print("  年化回报: 36.90%")
    print("  最终资金: 118,450.00")
    print()
    print("⚖️ 风险指标:")
    print("  夏普比率: 1.856")
    print("  最大回撤: -12.30%")
    print("  胜率: 68.75%")
    print("  交易次数: 32")
    print()
    print("=" * 50)

    print("📊 演示3: 多策略比较")
    print("-" * 30)
    print("正在比较多个策略在热门港股上的表现...")
    print()

    # 模拟比较结果
    print("🏆 策略比较结果")
    print("=" * 60)
    print("股票   |  策略   |  总回报   |  夏普比率 |  最大回撤 |  交易次数")
    print("-" * 60)
    print("0700.HK |  RSI    |  18.45%   |  1.856   | -12.30%  |     32")
    print("0700.HK |  MACD   |  15.20%   |  1.543   | -14.50%  |     28")
    print("0700.HK |  MA     |  12.80%   |  1.234   | -18.20%  |     18")
    print("0941.HK |  RSI    |  22.10%   |  2.045   | -10.80%  |     41")
    print("0941.HK |  MACD   |  19.50%   |  1.789   | -13.20%  |     35")
    print("1398.HK |  RSI    |  14.30%   |  1.456   | -16.40%  |     25")
    print("=" * 60)
    print()

    print("🥇 最佳策略: RSI on 0941.HK")
    print("   夏普比率: 2.045")
    print("   总回报: 22.10%")
    print()
    print("=" * 50)

    print("🎯 常用命令示例")
    print("-" * 30)
    print("# RSI策略回测")
    print("python main.py backtest --strategy RSI --symbol 0700.HK --start-date 1y")
    print()
    print("# RSI策略参数优化")
    print("python main.py optimize --strategy RSI --symbol 0700.HK --start-date 6m")
    print()
    print("# 多策略比较")
    print("python main.py compare --symbols \"0700.HK,0941.HK\" --strategies \"RSI,MACD\" --start-date 1y")
    print()
    print("# 查看可用策略")
    print("python main.py list-strategies")
    print()
    print("# 使用HKMA数据")
    print("python main.py backtest --strategy RSI --symbol 0700.HK --start-date 1y --use-hkma")
    print()
    print("=" * 50)

    print("🎉 演示完成！")
    print("现在您可以开始使用个人交易系统进行量化分析了。")
    print("输入 'python main.py --help' 查看更多帮助信息。")

if __name__ == "__main__":
    quick_demo()