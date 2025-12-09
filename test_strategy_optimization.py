#!/usr/bin/env python3
"""
测试策略优化功能
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime

# 添加项目目录到路径
project_dir = os.path.join(os.path.expanduser("~"), ".cursor", "CODEX 寫量化團隊")
sys.path.insert(0, project_dir)
os.chdir(project_dir)

def test_strategy_optimization():
    """测试策略优化功能"""
    try:
        # 导入策略优化函数
        from complete_project_system import run_strategy_optimization, get_stock_data
        
        print("🚀 开始测试策略优化功能...")
        
        # 获取股票数据
        print("正在获取0700.HK数据...")
        data = get_stock_data('0700.HK')
        
        if not data:
            print("❌ 无法获取股票数据")
            return False
        
        print(f"✅ 数据获取成功: {len(data)} 条记录")
        
        # 测试策略优化
        print("开始策略优化...")
        results = run_strategy_optimization(data, 'ma')  # 只测试MA策略
        
        if results:
            print(f"✅ 策略优化成功: 找到 {len(results)} 个策略")
            print("\n📊 最佳策略:")
            for i, strategy in enumerate(results[:5], 1):
                print(f"{i}. {strategy['strategy_name']}")
                print(f"   Sharpe比率: {strategy['sharpe_ratio']}")
                print(f"   年化收益率: {strategy['annual_return']}%")
                print(f"   最大回撤: {strategy['max_drawdown']}%")
                print()
        else:
            print("❌ 策略优化失败: 没有找到有效策略")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_strategy_optimization()
    if success:
        print("🎉 策略优化功能测试成功！")
    else:
        print("💥 策略优化功能测试失败！")
