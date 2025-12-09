#!/usr/bin/env python3
"""
高性能优化器测试脚本
验证32核并行处理能力和2000+策略/秒目标
"""

import asyncio
import time
import pandas as pd
import numpy as np
import multiprocessing as mp
from src.optimization.high_performance_optimizer import HighPerformanceOptimizer
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_test_data(size: int = 2000) -> pd.DataFrame:
    """生成测试数据"""
    np.random.seed(42)
    dates = pd.date_range('2020-01-01', periods=size, freq='D')
    
    # 模拟真实股价走势
    returns = np.random.normal(0.0005, 0.02, size)
    prices = 100 * np.exp(np.cumsum(returns))
    
    # 生成OHLCV数据
    high_noise = np.random.uniform(0, 0.03, size)
    low_noise = np.random.uniform(0, 0.03, size)
    
    data = pd.DataFrame({
        'open': prices,
        'high': prices * (1 + high_noise),
        'low': prices * (1 - low_noise),
        'close': prices * (1 + np.random.uniform(-0.01, 0.01, size)),
        'volume': np.random.randint(1000000, 10000000, size)
    }, index=dates)
    
    return data

async def performance_benchmark():
    """性能基准测试"""
    print("🚀 高性能优化器基准测试")
    print("=" * 60)
    
    # 检查系统资源
    cpu_count = mp.cpu_count()
    print(f"💻 系统CPU核心数: {cpu_count}")
    print(f"🎯 目标性能: 2000+ 策略/秒")
    print()
    
    # 生成测试数据
    print("📊 生成测试数据...")
    data = generate_test_data(2000)
    print(f"✅ 测试数据生成完成: {len(data)} 条记录")
    print()
    
    # 测试不同worker数量
    worker_counts = [8, 16, 24, 32]
    chunk_sizes = [50, 100, 200]
    
    best_performance = 0
    best_config = {}
    
    for workers in worker_counts:
        for chunk_size in chunk_sizes:
            print(f"🔧 测试配置: {workers} workers, chunk_size={chunk_size}")
            
            try:
                # 创建优化器
                optimizer = HighPerformanceOptimizer(
                    max_workers=workers,
                    chunk_size=chunk_size
                )
                
                # 运行RSI策略优化测试
                sample_size = 5000  # 适中的样本大小
                start_time = time.time()
                
                results = await optimizer.run_optimization(
                    'RSI', 
                    data, 
                    sample_size=sample_size
                )
                
                execution_time = time.time() - start_time
                tasks_per_second = len(results) / execution_time
                
                print(f"📈 执行时间: {execution_time:.2f}秒")
                print(f"⚡ 处理速度: {tasks_per_second:.1f} 策略/秒")
                print(f"✅ 完成任务: {len(results)}")
                
                # 获取性能摘要
                summary = optimizer.get_performance_summary()
                print(f"🎯 缓存命中率: {summary['metrics']['cache_hit_rate']:.1%}")
                print(f"💾 内存使用: {summary['metrics']['memory_usage']:.1f}%")
                print(f"🖥️  CPU使用: {summary['metrics']['cpu_usage']:.1f}%")
                
                # 记录最佳配置
                if tasks_per_second > best_performance:
                    best_performance = tasks_per_second
                    best_config = {
                        'workers': workers,
                        'chunk_size': chunk_size,
                        'tasks_per_second': tasks_per_second,
                        'execution_time': execution_time
                    }
                
                # 检查是否达到目标
                if tasks_per_second >= 2000:
                    print("🎉 🎉 🎉 已达到目标性能! 🎉 🎉 🎉")
                
                print()
                
            except Exception as e:
                print(f"❌ 测试失败: {e}")
                print()
                continue
    
    # 显示最佳配置
    print("🏆 最佳配置结果")
    print("=" * 40)
    print(f"Workers: {best_config['workers']}")
    print(f"Chunk Size: {best_config['chunk_size']}")
    print(f"最高速度: {best_config['tasks_per_second']:.1f} 策略/秒")
    print(f"执行时间: {best_config['execution_time']:.2f}秒")
    
    if best_performance >= 2000:
        print("✅ 成功达到性能目标!")
    else:
        print(f"⚠️  未达到性能目标，需要优化 (差值: {2000 - best_performance:.1f} 策略/秒)")
    
    return best_config

async def comprehensive_strategy_test():
    """综合策略测试"""
    print("\n🔄 综合策略性能测试")
    print("=" * 50)
    
    # 使用最佳配置
    best_workers = 24
    best_chunk_size = 100
    
    optimizer = HighPerformanceOptimizer(
        max_workers=best_workers,
        chunk_size=best_chunk_size
    )
    
    # 生成测试数据
    data = generate_test_data(2000)
    
    strategies = ['RSI', 'MACD', 'BOLLINGER', 'SMA_CROSS', 'STOCHASTIC']
    total_results = []
    
    for strategy in strategies:
        print(f"\n📊 测试 {strategy} 策略...")
        
        start_time = time.time()
        results = await optimizer.run_optimization(strategy, data, sample_size=2000)
        execution_time = time.time() - start_time
        
        valid_results = [r for r in results if r.error is None]
        top_results = sorted(valid_results, key=lambda x: x.sharpe_ratio, reverse=True)[:3]
        
        print(f"✅ 完成 {len(results)} 个优化任务")
        print(f"⚡ 处理速度: {len(results)/execution_time:.1f} 策略/秒")
        print(f"📈 有效结果: {len(valid_results)}")
        
        print("🏆 Top 3 策略:")
        for i, result in enumerate(top_results, 1):
            print(f"  {i}. Sharpe: {result.sharpe_ratio:.3f}, "
                  f"Return: {result.total_return:.2%}, "
                  f"Max DD: {result.max_drawdown:.2%}")
        
        total_results.extend(results)
    
    # 全局性能统计
    total_time = sum(r.execution_time for r in total_results)
    total_tasks = len(total_results)
    avg_speed = total_tasks / sum([r.execution_time for r in total_results])
    
    print(f"\n🎯 全局性能统计")
    print(f"📊 总任务数: {total_tasks}")
    print(f"⚡ 平均速度: {avg_speed:.1f} 策略/秒")
    print(f"⏱️  总执行时间: {total_time:.2f}秒")
    
    # 获取最终性能摘要
    final_summary = optimizer.get_performance_summary()
    print(f"🎯 最终缓存命中率: {final_summary['metrics']['cache_hit_rate']:.1%}")
    print(f"💾 内存使用: {final_summary['metrics']['memory_usage']:.1f}%")
    
    return total_results

async def stress_test():
    """压力测试"""
    print("\n🔥 系统压力测试")
    print("=" * 40)
    
    # 创建压力测试数据
    large_data = generate_test_data(5000)  # 更大的数据集
    
    optimizer = HighPerformanceOptimizer(max_workers=32, chunk_size=200)
    
    print("📊 运行大规模压力测试...")
    print(f"📈 数据规模: {len(large_data)} 条记录")
    
    # 并行测试多个策略
    strategies = ['RSI', 'MACD', 'BOLLINGER']
    tasks = []
    
    for strategy in strategies:
        task = asyncio.create_task(
            optimizer.run_optimization(strategy, large_data, sample_size=10000)
        )
        tasks.append((strategy, task))
    
    # 等待所有任务完成
    start_time = time.time()
    results_dict = {}
    
    for strategy, task in tasks:
        try:
            results = await task
            results_dict[strategy] = results
            print(f"✅ {strategy} 完成: {len(results)} 个结果")
        except Exception as e:
            print(f"❌ {strategy} 失败: {e}")
    
    total_time = time.time() - start_time
    total_results = sum(len(r) for r in results_dict.values())
    
    print(f"\n🎯 压力测试结果")
    print(f"⏱️  总执行时间: {total_time:.2f}秒")
    print(f"📊 总处理任务: {total_results}")
    print(f"⚡ 综合处理速度: {total_results/total_time:.1f} 策略/秒")
    
    # 系统资源使用情况
    import psutil
    cpu_percent = psutil.cpu_percent()
    memory_percent = psutil.virtual_memory().percent
    
    print(f"🖥️  CPU使用率: {cpu_percent:.1f}%")
    print(f"💾 内存使用率: {memory_percent:.1f}%")
    
    # 最终性能评估
    if total_results/total_time >= 2000:
        print("🎉 压力测试通过! 系统达到生产级性能要求")
    else:
        print("⚠️  压力测试未完全达标，需要进一步优化")

async def main():
    """主测试函数"""
    print("🚀 高性能量化交易系统 - 性能测试套件")
    print("=" * 60)
    print(f"🕒 测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # 1. 性能基准测试
        best_config = await performance_benchmark()
        print()
        
        # 2. 综合策略测试
        await comprehensive_strategy_test()
        print()
        
        # 3. 压力测试
        await stress_test()
        
        print("\n🎊 所有测试完成!")
        print("=" * 40)
        print("📊 测试总结:")
        print(f"  - 最佳配置: {best_config['workers']} workers")
        print(f"  - 最高性能: {best_config['tasks_per_second']:.1f} 策略/秒")
        print(f"  - 系统状态: 生产就绪" if best_config['tasks_per_second'] >= 2000 else "需要优化")
        
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        print(f"❌ 测试失败: {e}")
        raise

if __name__ == "__main__":
    # 设置Windows平台的multiprocessing启动方式
    import multiprocessing as mp
    if mp.get_start_method() != 'spawn':
        mp.set_start_method('spawn', force=True)
    
    asyncio.run(main())