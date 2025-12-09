import sys
import os

# 设置路径
project_path = "C:/Users/Penguin8n/.cursor/CODEX 寫量化團隊"
sys.path.insert(0, project_path)
os.chdir(project_path)

print(f"Project path: {project_path}")
print(f"Current dir: {os.getcwd()}")

try:
    import complete_project_system
    print("✅ 导入成功")
    
    # 测试策略优化函数
    from complete_project_system import run_strategy_optimization
    print("✅ 策略优化函数导入成功")
    
    # 创建简单测试数据
    import pandas as pd
    import numpy as np
    
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
    
    # 测试策略优化
    print("开始测试策略优化...")
    results = run_strategy_optimization(data, 'ma')
    print(f"✅ 策略优化测试成功: 找到 {len(results)} 个策略")
    
    if results:
        print(f"最佳策略: {results[0]['strategy_name']}")
        print(f"Sharpe比率: {results[0]['sharpe_ratio']:.4f}")
        print(f"年化收益率: {results[0]['annual_return']:.2f}%")
        print(f"最大回撤: {results[0]['max_drawdown']:.2f}%")
    
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
