import sys
import os
import pandas as pd
import numpy as np

# 设置路径
project_path = "C:/Users/Penguin8n/.cursor/CODEX 寫量化團隊"
sys.path.insert(0, project_path)
os.chdir(project_path)

print("🚀 开始验证策略优化功能...")

try:
    # 导入策略函数
    from complete_project_system import run_strategy_optimization
    print("✅ 策略优化函数导入成功")
    
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
        print(f"年化收益率: {results[0]['annual_return']:.2f}%")
        print(f"最大回撤: {results[0]['max_drawdown']:.2f}%")
        print("🎉 策略优化功能验证成功！")
    else:
        print("❌ MA策略优化失败: 没有找到有效策略")
    
    # 测试全部策略优化
    print("\n测试全部策略优化...")
    all_results = run_strategy_optimization(data, 'all')
    
    if all_results:
        print(f"✅ 全部策略优化成功: 找到 {len(all_results)} 个策略")
        print(f"最佳策略: {all_results[0]['strategy_name']}")
        print(f"最佳Sharpe比率: {all_results[0]['sharpe_ratio']:.4f}")
    else:
        print("❌ 全部策略优化失败")
    
except Exception as e:
    print(f"❌ 验证失败: {e}")
    import traceback
    traceback.print_exc()
