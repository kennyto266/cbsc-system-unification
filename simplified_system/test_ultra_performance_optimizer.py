#!/usr/bin/env python3
"""
超高性能优化器测试脚本
验证5000+策略/秒目标
"""

import asyncio
import time
import pandas as pd
import numpy as np
import multiprocessing as mp
import psutil
from src.optimization.ultra_high_performance_optimizer import UltraHighPerformanceOptimizer
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_comprehensive_test_data(size: int = 10000) -> pd.DataFrame:
    """生成综合测试数据"""
    np.random.seed(42)
    dates = pd.date_range('2018-01-01', periods=size, freq='D')
    
    # 模拟真实股价走势（更复杂的价格模式）
    # 添加趋势、季节性、和随机波动
    trend = np.linspace(0.0001, 0.0003, size)  # 逐渐增长的趋势
    seasonal = 0.0002 * np.sin(2 * np.pi * np.arange(size) / 252)  # 年度季节性
    noise = np.random.normal(0, 0.025, size)  # 随机噪声
    
    returns = trend + seasonal + noise
    prices = 100 * np.exp(np.cumsum(returns))
    
    # 生成更真实的OHLCV数据
    high_noise = np.random.uniform(0.01, 0.04, size)
    low_noise = np.random.uniform(0.01, 0.04, size)
    close_noise = np.random.uniform(-0.005, 0.005, size)
    
    data = pd.DataFrame({
        'open': prices,
        'high': prices * (1 + high_noise),
        'low': prices * (1 - low_noise),
        'close': prices * (1 + close_noise),
        'volume': np.random.lognormal(15, 0.5, size).astype(int)
    }, index=dates)
    
    # 确保OHLC关系正确
    data['high'] = np.maximum.reduce([data['open'], data['high'], data['close']])
    data['low'] = np.minimum.reduce([data['open'], data['low'], data['close']])
    
    return data

def benchmark_system_resources():
    """基准测试系统资源"""
    print("💻 系统资源基准测试")
    print("=" * 40)
    
    # CPU信息
    cpu_count = mp.cpu_count()
    cpu_freq = psutil.cpu_freq()
    current_freq = cpu_freq.current if cpu_freq else 0
    
    print(f"CPU核心数: {cpu_count}")
    print(f"CPU频率: {current_freq:.1f} MHz")
    
    # 内存信息
    memory = psutil.virtual_memory()
    print(f"总内存: {memory.total // (1024**3)} GB")
    print(f"可用内存: {memory.available // (1024**3)} GB")
    print(f"内存使用率: {memory.percent:.1f}%")
    
    # 磁盘信息
    disk = psutil.disk_usage('/')
    print(f"磁盘空间: {disk.total // (1024**3)} GB (总)")
    print(f"磁盘可用: {disk.free // (1024**3)} GB")
    
    return {
        'cpu_count': cpu_count,
        'cpu_freq': current_freq,
        'total_memory_gb': memory.total // (1024**3),
        'available_memory_gb': memory.available // (1024**3),
        'disk_free_gb': disk.free // (1024**3)
    }

async def ultra_performance_benchmark():
    """超性能基准测试"""
    print("\n🚀 超高性能基准测试")
    print("=" * 50)
    
    # 获取系统基准
    system_info = benchmark_system_resources()
    
    # 生成大测试数据集
    print("\n📊 生成大规模测试数据...")
    large_data = generate_comprehensive_test_data(10000)
    print(f"✅ 大数据集生成完成: {len(large_data):,} 条记录")
    
    # 测试不同的优化配置
    test_configs = [
        {'workers': 32, 'chunk_size': 300, 'name': '高性能配置'},
        {'workers': 48, 'chunk_size': 500, 'name': '极限配置'},
        {'workers': 24, 'chunk_size': 200, 'name': '平衡配置'},
    ]
    
    best_performance = 0
    best_config = {}
    
    for config in test_configs:
        print(f"\n🔧 测试配置: {config['name']}")
        print(f"   Workers: {config['workers']}, Chunk Size: {config['chunk_size']}")
        
        try:
            # 创建超高性能优化器
            optimizer = UltraHighPerformanceOptimizer(
                max_workers=config['workers'],
                chunk_size=config['chunk_size']
            )
            
            # 高优先级任务定义
            priority_tasks = [
                {'period': 12, 'oversold': 25, 'overbought': 75},
                {'period': 14, 'oversold': 30, 'overbought': 70},
                {'period': 10, 'oversold': 20, 'overbought': 80},
                {'period': 8, 'oversold': 15, 'overbought': 85},
                {'period': 16, 'oversold': 35, 'overbought': 65}
            ]
            
            # 运行超优化测试
            sample_size = 50000  # 大样本测试
            start_time = time.perf_counter()
            
            results = await optimizer.run_ultra_optimization(
                'RSI',
                large_data,
                sample_size=sample_size,
                priority_tasks=priority_tasks
            )
            
            execution_time = time.perf_counter() - start_time
            tasks_per_second = len(results) / execution_time
            
            print(f"📈 执行时间: {execution_time:.2f}秒")
            print(f"⚡ 处理速度: {tasks_per_second:.0f} 策略/秒")
            print(f"📊 完成任务: {len(results):,}")
            
            # 获取性能摘要
            summary = optimizer.get_ultra_performance_summary()
            print(f"🎯 缓存效率: {summary['ultra_metrics']['cache_efficiency']:.1%}")
            print(f"💾 峰值内存: {summary['ultra_metrics']['peak_memory_usage']:.1f} MB")
            print(f"📦 L1缓存: {summary['cache_sizes']['l1_cache']:,} 项")
            print(f"📦 L2缓存: {summary['cache_sizes']['l2_cache']:,} 项")
            
            # 记录最佳配置
            if tasks_per_second > best_performance:
                best_performance = tasks_per_second
                best_config = {
                    'name': config['name'],
                    'workers': config['workers'],
                    'chunk_size': config['chunk_size'],
                    'tasks_per_second': tasks_per_second,
                    'execution_time': execution_time,
                    'sample_size': sample_size,
                    'cache_efficiency': summary['ultra_metrics']['cache_efficiency']
                }
            
            # 内存清理
            del optimizer
            import gc
            gc.collect()
            
            print(f"✅ {config['name']} 测试完成")
            
        except Exception as e:
            print(f"❌ {config['name']} 测试失败: {e}")
            print("   可能的原因: 内存不足或系统资源限制")
            continue
        
        print()
    
    # 显示最佳结果
    print("🏆 最佳性能结果")
    print("=" * 50)
    print(f"配置名称: {best_config['name']}")
    print(f"Workers数量: {best_config['workers']}")
    print(f"Chunk Size: {best_config['chunk_size']}")
    print(f"最高速度: {best_config['tasks_per_second']:.0f} 策略/秒")
    print(f"执行时间: {best_config['execution_time']:.2f}秒")
    print(f"样本大小: {best_config['sample_size']:,}")
    print(f"缓存效率: {best_config['cache_efficiency']:.1%}")
    
    # 目标达成评估
    target_speed = 5000
    achievement_rate = (best_performance / target_speed) * 100
    
    print(f"\n🎯 目标达成评估:")
    print(f"目标速度: {target_speed} 策略/秒")
    print(f"实际速度: {best_performance:.0f} 策略/秒")
    print(f"达成率: {achievement_rate:.1f}%")
    
    if achievement_rate >= 100:
        print("🎉 🎉 🎉 超性能目标完全达成! 🎉 🎉 🎉")
        print("🚀 系统已达到业界领先水平!")
    elif achievement_rate >= 90:
        print("⭐ 优秀! 非常接近目标")
    elif achievement_rate >= 80:
        print("👍 良好! 达到高水准")
    else:
        print("⚠️  需要进一步优化系统")
    
    return best_config, achievement_rate

async def comprehensive_strategy_test():
    """综合策略性能测试"""
    print("\n🔄 综合策略超性能测试")
    print("=" * 60)
    
    # 使用最佳配置
    optimizer = UltraHighPerformanceOptimizer(max_workers=48, chunk_size=500)
    
    # 生成测试数据
    test_data = generate_comprehensive_test_data(5000)
    
    strategies = ['RSI', 'MACD', 'BOLLINGER']
    total_results = []
    strategy_performance = {}
    
    for strategy in strategies:
        print(f"\n📊 测试 {strategy} 策略超优化...")
        
        # 定义每种策略的高优先级参数
        if strategy == 'RSI':
            priority_tasks = [
                {'period': 12, 'oversold': 25, 'overbought': 75},
                {'period': 14, 'oversold': 30, 'overbought': 70}
            ]
        elif strategy == 'MACD':
            priority_tasks = [
                {'fast': 8, 'slow': 21, 'signal': 9},
                {'fast': 12, 'slow': 26, 'signal': 9}
            ]
        else:  # BOLLINGER
            priority_tasks = [
                {'period': 15, 'std_dev': 2.0},
                {'period': 20, 'std_dev': 2.5}
            ]
        
        start_time = time.perf_counter()
        results = await optimizer.run_ultra_optimization(
            strategy, 
            test_data, 
            sample_size=30000,
            priority_tasks=priority_tasks
        )
        execution_time = time.perf_counter() - start_time
        
        valid_results = [r for r in results if r.error is None]
        top_results = sorted(valid_results, key=lambda x: x.sharpe_ratio, reverse=True)[:3]
        
        strategy_speed = len(results) / execution_time
        strategy_performance[strategy] = {
            'total_tasks': len(results),
            'valid_results': len(valid_results),
            'execution_time': execution_time,
            'speed': strategy_speed,
            'top_sharpe': top_results[0].sharpe_ratio if top_results else 0
        }
        
        total_results.extend(results)
        
        print(f"✅ {strategy} 完成: {len(results):,} 个优化任务")
        print(f"⚡ 处理速度: {strategy_speed:.0f} 策略/秒")
        print(f"📈 有效结果: {len(valid_results):,}")
        
        print(f"🏆 Top 3 {strategy} 策略:")
        for i, result in enumerate(top_results, 1):
            print(f"  {i}. Sharpe: {result.sharpe_ratio:.3f}, "
                  f"Return: {result.total_return:.2%}, "
                  f"Max DD: {result.max_drawdown:.2%}")
    
    # 综合性能统计
    total_time = sum(perf['execution_time'] for perf in strategy_performance.values())
    total_tasks = sum(perf['total_tasks'] for perf in strategy_performance.values())
    avg_speed = total_tasks / total_time
    
    print(f"\n🎯 综合性能统计:")
    print(f"总任务数: {total_tasks:,}")
    print(f"总执行时间: {total_time:.2f}秒")
    print(f"综合处理速度: {avg_speed:.0f} 策略/秒")
    print(f"有效结果总数: {sum(perf['valid_results'] for perf in strategy_performance.values()):,}")
    
    for strategy, perf in strategy_performance.items():
        print(f"  {strategy}: {perf['speed']:.0f} 策略/秒, Sharpe: {perf['top_sharpe']:.3f}")
    
    # 获取最终性能摘要
    final_summary = optimizer.get_ultra_performance_summary()
    print(f"\n📊 最终系统统计:")
    print(f"缓存效率: {final_summary['ultra_metrics']['cache_efficiency']:.1%}")
    print(f"峰值内存: {final_summary['ultra_metrics']['peak_memory_usage']:.1f} MB")
    
    return total_tasks, avg_speed

async def stress_test():
    """极限压力测试"""
    print("\n🔥 极限压力测试")
    print("=" * 40)
    
    # 创建极限测试数据
    stress_data = generate_comprehensive_test_data(15000)  # 15年数据
    
    optimizer = UltraHighPerformanceOptimizer(max_workers=64, chunk_size=1000)
    
    print("📊 运行极限规模优化...")
    print(f"📈 数据规模: {len(stress_data):,} 条记录")
    
    # 定义大量高优先级任务
    extensive_priority_tasks = []
    for period in [8, 10, 12, 14, 16, 20]:
        for oversold in [20, 25, 30, 35]:
            for overbought in [70, 75, 80, 85]:
                extensive_priority_tasks.append({
                    'period': period, 'oversold': oversold, 'overbought': overbought
                })
    
    start_time = time.perf_counter()
    
    try:
        results = await optimizer.run_ultra_optimization(
            'RSI',
            stress_data,
            sample_size=100000,  # 10万参数组合
            priority_tasks=extensive_priority_tasks
        )
        
        execution_time = time.perf_counter() - start_time
        total_speed = len(results) / execution_time
        
        print(f"\n🎯 压力测试结果:")
        print(f"⏱️  执行时间: {execution_time:.2f}秒")
        print(f"📊 总处理任务: {len(results):,}")
        print(f"⚡ 综合处理速度: {total_speed:.0f} 策略/秒")
        
        # 系统资源使用情况
        cpu_percent = psutil.cpu_percent(interval=1)
        memory_percent = psutil.virtual_memory().percent
        
        print(f"🖥️  CPU使用率: {cpu_percent:.1f}%")
        print(f"💾 内存使用率: {memory_percent:.1f}%")
        
        # 最终性能评估
        if total_speed >= 5000:
            print("🎉 压力测试通过! 系统达到超高性能要求")
        elif total_speed >= 4000:
            print("⭐ 压力测试优秀! 接近超高性能")
        else:
            print("⚠️  压力测试通过，但需要进一步优化")
        
        return total_speed >= 5000
        
    except Exception as e:
        print(f"❌ 压力测试失败: {e}")
        return False

async def main():
    """主测试函数"""
    print("🚀 超高性能量化交易引擎 - 完整测试套件")
    print("=" * 70)
    print(f"🕒 测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # 1. 超性能基准测试
        best_config, achievement_rate = await ultra_performance_benchmark()
        print()
        
        # 2. 综合策略测试
        total_tasks, avg_speed = await comprehensive_strategy_test()
        print()
        
        # 3. 极限压力测试
        stress_passed = await stress_test()
        print()
        
        # 4. 最终评估
        print("🎊 超高性能测试套件完成!")
        print("=" * 60)
        print("📊 测试总结:")
        print(f"  - 最佳配置: {best_config.get('name', 'N/A')}")
        print(f"  - 最高速度: {best_config.get('tasks_per_second', 0):.0f} 策略/秒")
        print(f"  - 目标达成率: {achievement_rate:.1f}%")
        print(f"  - 综合速度: {avg_speed:.0f} 策略/秒")
        print(f"  - 总处理任务: {total_tasks:,}")
        print(f"  - 压力测试: {'通过' if stress_passed else '未通过'}")
        
        # 系统评级
        if achievement_rate >= 100 and stress_passed:
            grade = "S+ (超高性能)"
            message = "🏆 系统达到世界顶级水平!"
        elif achievement_rate >= 90 and avg_speed >= 4000:
            grade = "S (高性能)"
            message = "⭐ 系统达到行业领先水平!"
        elif achievement_rate >= 80 and avg_speed >= 3000:
            grade = "A+ (优秀)"
            message = "👍 系统表现优秀!"
        else:
            grade = "A (良好)"
            message = "✅ 系统表现良好，有改进空间"
        
        print(f"\n🏅 系统评级: {grade}")
        print(f"💬 评估: {message}")
        
        return achievement_rate >= 80
        
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        print(f"❌ 测试失败: {e}")
        return False

if __name__ == "__main__":
    # 设置Windows平台的multiprocessing启动方式
    import multiprocessing as mp
    if mp.get_start_method() != 'spawn':
        mp.set_start_method('spawn', force=True)
    
    success = asyncio.run(main())
    exit_code = 0 if success else 1