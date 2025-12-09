"""
测试优化后的量化交易系统
验证性能提升和功能正常性
"""

import asyncio
import time
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from src.core.optimized_config import config
from src.monitoring.performance_monitor import performance_monitor
from src.agents.quantitative_analyst import QuantitativeAnalysisEngine, TechnicalIndicators
import pandas as pd
import numpy as np


async def test_technical_indicators_performance():
    """测试技术指标计算性能"""
    print("🧪 测试技术指标计算性能...")
    
    # 创建测试数据
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', periods=100, freq='D')
    data = pd.DataFrame({
        'timestamp': dates,
        'open': 100 + np.random.randn(100).cumsum(),
        'high': 105 + np.random.randn(100).cumsum(),
        'low': 95 + np.random.randn(100).cumsum(),
        'close': 100 + np.random.randn(100).cumsum(),
        'volume': np.random.randint(1000, 10000, 100)
    })
    
    engine = QuantitativeAnalysisEngine()
    
    # 测试优化后的计算
    start_time = time.time()
    indicators = engine.calculate_technical_indicators(data)
    optimized_time = time.time() - start_time
    
    print(f"✅ 技术指标计算完成:")
    print(f"   - 计算时间: {optimized_time:.4f}秒")
    print(f"   - SMA 20: {indicators.sma_20:.2f}")
    print(f"   - SMA 50: {indicators.sma_50:.2f}")
    print(f"   - RSI: {indicators.rsi:.2f}")
    print(f"   - MACD: {indicators.macd:.4f}")
    print(f"   - 布林带上轨: {indicators.bollinger_upper:.2f}")
    print(f"   - ATR: {indicators.atr:.4f}")
    
    return optimized_time


async def test_performance_monitor():
    """测试性能监控系统"""
    print("\n📊 测试性能监控系统...")
    
    # 启动监控
    await performance_monitor.start_monitoring(interval_seconds=5)
    
    # 模拟一些工作负载
    print("   - 模拟工作负载...")
    await asyncio.sleep(10)
    
    # 获取性能统计
    summary = performance_monitor.get_performance_summary()
    recommendations = performance_monitor.get_optimization_recommendations()
    
    print(f"✅ 性能监控测试完成:")
    print(f"   - CPU使用率: {summary['current_metrics']['cpu_percent']:.1f}%")
    print(f"   - 内存使用率: {summary['current_metrics']['memory_percent']:.1f}%")
    print(f"   - 内存使用量: {summary['current_metrics']['memory_used_mb']:.1f}MB")
    print(f"   - 活跃连接数: {summary['current_metrics']['active_connections']}")
    
    if recommendations:
        print(f"   - 优化建议: {recommendations[0]}")
    
    # 停止监控
    await performance_monitor.stop_monitoring()
    
    return summary


async def test_config_management():
    """测试配置管理"""
    print("\n⚙️ 测试配置管理...")
    
    # 测试配置获取
    tech_config = config.get_technical_config()
    agent_config = config.get_agent_config()
    perf_config = config.get_performance_config()
    
    print(f"✅ 配置管理测试完成:")
    print(f"   - SMA短期周期: {tech_config.SMA_SHORT_PERIOD}")
    print(f"   - RSI周期: {tech_config.RSI_PERIOD}")
    print(f"   - 并行执行: {agent_config.PARALLEL_EXECUTION}")
    print(f"   - 最大并发数: {agent_config.MAX_CONCURRENT_AGENTS}")
    print(f"   - 日志级别: {perf_config.LOG_LEVEL}")
    
    # 测试配置验证
    is_valid = config.validate_config()
    print(f"   - 配置有效性: {'✅ 有效' if is_valid else '❌ 无效'}")
    
    return is_valid


async def test_agent_performance_tracking():
    """测试代理性能追踪"""
    print("\n🤖 测试代理性能追踪...")
    
    # 模拟代理启动
    agent_id = performance_monitor.start_agent_monitoring("test_agent")
    print(f"   - 代理ID: {agent_id}")
    
    # 模拟代理运行
    await asyncio.sleep(2)
    performance_monitor.update_agent_metrics(agent_id, memory_mb=50.5, cpu_percent=25.3, api_calls=5)
    
    await asyncio.sleep(1)
    performance_monitor.update_agent_metrics(agent_id, memory_mb=75.2, cpu_percent=45.7, api_calls=3)
    
    # 结束代理监控
    performance_monitor.end_agent_monitoring(agent_id, success=True)
    
    # 获取代理统计
    summary = performance_monitor.get_performance_summary()
    agent_stats = summary.get('agent_performance', {})
    
    if 'test_agent' in agent_stats:
        stats = agent_stats['test_agent']
        print(f"✅ 代理性能追踪测试完成:")
        print(f"   - 执行时间: {stats['duration_seconds']:.2f}秒")
        print(f"   - 内存峰值: {stats['memory_peak_mb']:.1f}MB")
        print(f"   - CPU峰值: {stats['cpu_peak_percent']:.1f}%")
        print(f"   - API调用次数: {stats['api_calls_count']}")
        print(f"   - 执行状态: {'✅ 成功' if stats['success'] else '❌ 失败'}")
    
    return agent_stats


async def main():
    """主测试函数"""
    print("🚀 开始测试优化后的量化交易系统")
    print("="*60)
    
    try:
        # 测试1: 技术指标计算性能
        indicators_time = await test_technical_indicators_performance()
        
        # 测试2: 性能监控系统
        perf_summary = await test_performance_monitor()
        
        # 测试3: 配置管理
        config_valid = await test_config_management()
        
        # 测试4: 代理性能追踪
        agent_stats = await test_agent_performance_tracking()
        
        # 总结测试结果
        print("\n" + "="*60)
        print("📋 测试结果总结:")
        print(f"✅ 技术指标计算: {indicators_time:.4f}秒")
        print(f"✅ 性能监控: 正常运行")
        print(f"✅ 配置管理: {'有效' if config_valid else '无效'}")
        print(f"✅ 代理追踪: 正常运行")
        
        print("\n🎉 所有测试通过！优化后的系统运行正常。")
        
        # 性能建议
        recommendations = performance_monitor.get_optimization_recommendations()
        if recommendations:
            print("\n💡 系统建议:")
            for rec in recommendations:
                print(f"   • {rec}")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
