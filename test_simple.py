#!/usr/bin/env python3
"""
简单测试策略优化功能
"""

import sys
import os
import pandas as pd
import numpy as np

# 设置项目路径
project_path = os.path.join(os.path.expanduser("~"), ".cursor", "CODEX 寫量化團隊")
sys.path.insert(0, project_path)
os.chdir(project_path)

def test_simple():
    """简单测试"""
    try:
        print("🚀 测试策略优化功能...")
        
        # 导入策略优化函数
        from complete_project_system import run_strategy_optimization
        
        # 创建测试数据
        data = []
        for i in range(200):
            data.append({
                'date': f'2023-01-{i+1:02d}',
                'open': 100 + i * 0.1,
                'high': 105 + i * 0.1,
                'low': 95 + i * 0.1,
                'close': 100 + i * 0.1 + np.random.normal(0, 1),
                'volume': 1000
            })
        
        print(f"✅ 测试数据创建成功: {len(data)} 条记录")
        
        # 测试MA策略优化
        print("测试MA策略优化...")
        results = run_strategy_optimization(data, 'ma')
        
        if results:
            print(f"✅ MA策略优化成功: 找到 {len(results)} 个策略")
            print(f"最佳策略: {results[0]['strategy_name']}")
            print(f"Sharpe比率: {results[0]['sharpe_ratio']:.4f}")
            print("🎉 JSON解析错误修复成功！")
            return True
        else:
            print("❌ MA策略优化失败: 没有找到有效策略")
            return False
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_simple()
    if success:
        print("🎉 策略优化功能测试成功！")
    else:
        print("💥 策略优化功能测试失败！")
