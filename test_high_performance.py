#!/usr/bin/env python3
"""
测试高计算量策略优化
"""

import pandas as pd
import numpy as np
import time

def create_test_data():
    """创建测试数据"""
    data = []
    for i in range(500):  # 500条数据
        data.append({
            'date': f'2023-01-{i+1:02d}',
            'open': 100 + i * 0.1 + np.random.normal(0, 1),
            'high': 105 + i * 0.1 + np.random.normal(0, 1),
            'low': 95 + i * 0.1 + np.random.normal(0, 1),
            'close': 100 + i * 0.1 + np.random.normal(0, 1),
            'volume': 1000 + np.random.randint(0, 500)
        })
    return data

def test_ma_optimization():
    """测试MA策略优化"""
    print("🚀 开始高计算量MA策略优化测试...")
    
    data = create_test_data()
    df = pd.DataFrame(data)
    
    start_time = time.time()
    results = []
    
    # 高计算量MA策略优化
    ma_tasks = 0
    for short in range(3, 21, 1):  # 3-20, 步长1
        for long in range(10, 51, 2):  # 10-50, 步长2
            if short < long:
                ma_tasks += 1
                # 简化的策略计算
                df['ma_short'] = df['close'].rolling(window=short).mean()
                df['ma_long'] = df['close'].rolling(window=long).mean()
                df['signal'] = 0
                df.loc[df['ma_short'] > df['ma_long'], 'signal'] = 1
                df.loc[df['ma_short'] <= df['ma_long'], 'signal'] = 0
                
                # 计算简单性能指标
                returns = df['close'].pct_change()
                strategy_returns = returns * df['signal'].shift(1)
                total_return = (1 + strategy_returns).prod() - 1
                sharpe_ratio = strategy_returns.mean() / strategy_returns.std() * np.sqrt(252) if strategy_returns.std() > 0 else 0
                
                results.append({
                    'strategy_name': f'MA({short},{long})',
                    'total_return': round(float(total_return), 4),
                    'sharpe_ratio': round(float(sharpe_ratio), 4),
                    'short': short,
                    'long': long
                })
    
    elapsed_time = time.time() - start_time
    results = sorted(results, key=lambda x: x['sharpe_ratio'], reverse=True)
    
    print(f"✅ MA策略优化完成!")
    print(f"📊 总任务数: {ma_tasks}")
    print(f"⏱️ 耗时: {elapsed_time:.2f}秒")
    print(f"🏆 最佳策略: {results[0]['strategy_name']} (Sharpe: {results[0]['sharpe_ratio']})")
    print(f"📈 前5名策略:")
    for i, result in enumerate(results[:5]):
        print(f"  {i+1}. {result['strategy_name']}: Sharpe={result['sharpe_ratio']:.4f}, Return={result['total_return']:.4f}")

if __name__ == "__main__":
    test_ma_optimization()
