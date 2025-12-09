#!/usr/bin/env python3
"""
测试策略优化修复
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 添加项目目录到路径
project_dir = os.path.join(os.path.expanduser("~"), ".cursor", "CODEX 寫量化團隊")
sys.path.insert(0, project_dir)
os.chdir(project_dir)

def create_test_data():
    """创建测试数据"""
    dates = pd.date_range(start='2023-01-01', end='2024-01-01', freq='D')
    np.random.seed(42)
    
    # 生成模拟股价数据
    price = 100
    prices = []
    for i in range(len(dates)):
        price += np.random.normal(0, 2)
        prices.append(max(price, 1))  # 确保价格为正
    
    data = []
    for i, date in enumerate(dates):
        data.append({
            'date': date.strftime('%Y-%m-%d'),
            'open': prices[i] + np.random.normal(0, 0.5),
            'high': prices[i] + abs(np.random.normal(0, 1)),
            'low': prices[i] - abs(np.random.normal(0, 1)),
            'close': prices[i],
            'volume': np.random.randint(1000, 10000)
        })
    
    return data

def test_strategy_optimization():
    """测试策略优化功能"""
    try:
        print("🚀 开始测试策略优化功能...")
        
        # 创建测试数据
        print("创建测试数据...")
        data = create_test_data()
        print(f"✅ 测试数据创建成功: {len(data)} 条记录")
        
        # 导入策略优化函数
        from complete_project_system import run_strategy_optimization
        
        # 测试MA策略优化
        print("测试MA策略优化...")
        results = run_strategy_optimization(data, 'ma')
        
        if results:
            print(f"✅ MA策略优化成功: 找到 {len(results)} 个策略")
            print("\n📊 最佳策略:")
            for i, strategy in enumerate(results[:3], 1):
                print(f"{i}. {strategy['strategy_name']}")
                print(f"   Sharpe比率: {strategy['sharpe_ratio']:.4f}")
                print(f"   年化收益率: {strategy['annual_return']:.2f}%")
                print(f"   最大回撤: {strategy['max_drawdown']:.2f}%")
                print()
        else:
            print("❌ MA策略优化失败: 没有找到有效策略")
            return False
        
        # 测试全部策略优化
        print("测试全部策略优化...")
        all_results = run_strategy_optimization(data, 'all')
        
        if all_results:
            print(f"✅ 全部策略优化成功: 找到 {len(all_results)} 个策略")
            print(f"最佳策略: {all_results[0]['strategy_name']}")
            print(f"最佳Sharpe比率: {all_results[0]['sharpe_ratio']:.4f}")
        else:
            print("❌ 全部策略优化失败")
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
