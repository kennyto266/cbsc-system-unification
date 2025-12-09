#!/usr/bin/env python3
"""
直接测试策略优化功能
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 设置项目路径
project_path = r"C:\Users\Penguin8n\.cursor\CODEX 寫量化團隊"
sys.path.insert(0, project_path)
os.chdir(project_path)

def create_test_data():
    """创建测试数据"""
    print("创建测试数据...")
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
    
    print(f"✅ 测试数据创建成功: {len(data)} 条记录")
    return data

def test_strategy_functions():
    """测试策略函数"""
    try:
        print("🚀 开始测试策略优化功能...")
        
        # 导入策略函数
        from complete_project_system import (
            run_strategy_optimization,
            run_ma_strategy,
            run_rsi_strategy,
            run_macd_strategy,
            run_bollinger_strategy,
            calculate_strategy_performance
        )
        print("✅ 策略函数导入成功")
        
        # 创建测试数据
        data = create_test_data()
        df = pd.DataFrame(data)
        
        # 测试单个策略函数
        print("\n测试MA策略...")
        ma_result = run_ma_strategy(df, 10, 30)
        if ma_result:
            print(f"✅ MA策略测试成功: {ma_result['strategy_name']}")
            print(f"   Sharpe比率: {ma_result['sharpe_ratio']:.4f}")
        else:
            print("❌ MA策略测试失败")
        
        print("\n测试RSI策略...")
        rsi_result = run_rsi_strategy(df, 30, 70)
        if rsi_result:
            print(f"✅ RSI策略测试成功: {rsi_result['strategy_name']}")
            print(f"   Sharpe比率: {rsi_result['sharpe_ratio']:.4f}")
        else:
            print("❌ RSI策略测试失败")
        
        print("\n测试MACD策略...")
        macd_result = run_macd_strategy(df)
        if macd_result:
            print(f"✅ MACD策略测试成功: {macd_result['strategy_name']}")
            print(f"   Sharpe比率: {macd_result['sharpe_ratio']:.4f}")
        else:
            print("❌ MACD策略测试失败")
        
        print("\n测试布林带策略...")
        bb_result = run_bollinger_strategy(df)
        if bb_result:
            print(f"✅ 布林带策略测试成功: {bb_result['strategy_name']}")
            print(f"   Sharpe比率: {bb_result['sharpe_ratio']:.4f}")
        else:
            print("❌ 布林带策略测试失败")
        
        # 测试策略优化
        print("\n测试策略优化...")
        results = run_strategy_optimization(data, 'ma')
        
        if results:
            print(f"✅ 策略优化测试成功: 找到 {len(results)} 个策略")
            print("\n📊 最佳策略:")
            for i, strategy in enumerate(results[:3], 1):
                print(f"{i}. {strategy['strategy_name']}")
                print(f"   Sharpe比率: {strategy['sharpe_ratio']:.4f}")
                print(f"   年化收益率: {strategy['annual_return']:.2f}%")
                print(f"   最大回撤: {strategy['max_drawdown']:.2f}%")
                print()
        else:
            print("❌ 策略优化测试失败: 没有找到有效策略")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_strategy_functions()
    if success:
        print("🎉 策略优化功能测试成功！")
    else:
        print("💥 策略优化功能测试失败！")
