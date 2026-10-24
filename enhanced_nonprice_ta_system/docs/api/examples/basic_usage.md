# 基础使用示例

## 📖 概述

本文档提供Enhanced Non-Price Technical Analysis System的基础使用示例，帮助您快速上手系统的核心功能。

## 🚀 快速开始

### 1. 环境准备

```python
# 安装依赖
pip install pandas numpy requests aiohttp

# 导入核心模块
from enhanced_nonprice_ta_system import (
    CoreOptimizerEngine,
    EnhancedDataManager,
    EnhancedIndicatorEngine,
    QuickOptimizer
)

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
```

### 2. 简单示例 - 快速优化

```python
# 使用QuickOptimizer进行快速优化
def quick_optimization_example():
    """快速优化示例"""
    print("🚀 开始快速优化...")
    
    # 创建快速优化器
    optimizer = QuickOptimizer()
    
    # 运行优化 (使用默认参数)
    results = optimizer.optimize(
        symbol="0700.hk",  # 腾讯控股
        strategies=['RSI', 'MACD', 'KDJ']
    )
    
    # 显示结果
    print(f"✅ 优化完成!")
    print(f"总测试策略数: {results.total_strategies_tested}")
    print(f"优化耗时: {results.optimization_time:.2f}秒")
    
    # 显示前3名策略
    print("\\n🏆 最佳策略:")
    for i, strategy in enumerate(results.top_strategies[:3], 1):
        print(f"{i}. {strategy.name}")
        print(f"   Sharpe比率: {strategy.sharpe_ratio:.3f}")
        print(f"   总回报率: {strategy.total_return:.2%}")
        print(f"   最大回撤: {strategy.max_drawdown:.2%}")
        print(f"   参数: {strategy.parameters}")

# 运行示例
quick_optimization_example()
```

### 3. 详细示例 - 完整工作流程

```python
def complete_workflow_example():
    """完整工作流程示例"""
    print("🔄 开始完整工作流程...")
    
    # 步骤1: 创建核心组件
    print("\\n📦 步骤1: 初始化系统组件...")
    data_manager = EnhancedDataManager()
    indicator_engine = EnhancedIndicatorEngine()
    optimizer = CoreOptimizerEngine(
        data_manager=data_manager,
        indicator_engine=indicator_engine
    )
    
    # 步骤2: 获取数据
    print("\\n📊 步骤2: 获取数据...")
    
    # 获取股票数据
    stock_data = data_manager.fetch_stock_data("0700.hk", 365)
    print(f"股票数据: {len(stock_data)} 条记录")
    print(f"价格范围: {stock_data['close'].min():.2f} - {stock_data['close'].max():.2f}")
    
    # 获取政府数据
    import asyncio
    
    async def get_gov_data():
        return await data_manager.fetch_all_government_data(365)
    
    gov_data = asyncio.run(get_gov_data())
    print(f"政府数据源: {len(gov_data)} 个")
    for source, data in gov_data.items():
        print(f"  {source}: {len(data)} 条记录")
    
    # 步骤3: 计算技术指标
    print("\\n📈 步骤3: 计算技术指标...")
    
    # 计算RSI
    rsi_14 = indicator_engine.calculate_rsi(stock_data['close'], 14)
    rsi_30 = indicator_engine.calculate_rsi(stock_data['close'], 30)
    print(f"RSI(14) 最新值: {rsi_14.iloc[-1]:.2f}")
    print(f"RSI(30) 最新值: {rsi_30.iloc[-1]:.2f}")
    
    # 计算MACD
    macd_result = indicator_engine.calculate_macd(stock_data['close'])
    print(f"MACD最新值: {macd_result['macd'].iloc[-1]:.4f}")
    print(f"Signal最新值: {macd_result['signal'].iloc[-1]:.4f}")
    
    # 计算KDJ (MB_KDJ_[10,2]策略)
    kdj_result = indicator_engine.calculate_kdj(
        stock_data['high'],
        stock_data['low'],
        stock_data['close'],
        k_period=10, d_period=2, j_period=2
    )
    print(f"MB_KDJ_[10,2] 最新值:")
    print(f"  K: {kdj_result['k'].iloc[-1]:.2f}")
    print(f"  D: {kdj_result['d'].iloc[-1]:.2f}")
    print(f"  J: {kdj_result['j'].iloc[-1]:.2f}")
    
    # 步骤4: 运行优化
    print("\\n⚡ 步骤4: 运行策略优化...")
    
    # 自定义优化配置
    optimization_config = {
        'strategies': ['RSI', 'MACD', 'KDJ'],
        'parameter_ranges': {
            'RSI': {
                'period': range(10, 31),
                'oversold': [25, 30],
                'overbought': [70, 75]
            },
            'MACD': {
                'fast': range(10, 16),
                'slow': range(20, 31),
                'signal': range(8, 13)
            },
            'KDJ': {
                'k_period': range(8, 13),
                'd_period': range(2, 4),
                'j_period': range(2, 4)
            }
        }
    }
    
    results = optimizer.run_enhanced_optimization(
        symbol="0700.hk",
        optimization_config=optimization_config,
        parallel_cores=8  # 使用较少核心以加快演示
    )
    
    # 步骤5: 分析结果
    print("\\n📋 步骤5: 分析优化结果...")
    
    print(f"优化完成统计:")
    print(f"  总测试策略: {results.total_strategies_tested}")
    print(f"  成功率: {results.success_rate:.1%}")
    print(f"  缓存命中率: {results.cache_hit_rate:.1%}")
    print(f"  并行效率: {results.parallel_efficiency:.1%}")
    
    # 显示最佳策略
    print(f"\\n🏆 最佳策略 (前5名):")
    for i, strategy in enumerate(results.top_strategies[:5], 1):
        print(f"{i}. {strategy.name}")
        print(f"   Sharpe比率: {strategy.sharpe_ratio:.3f}")
        print(f"   年化回报: {strategy.annual_return:.2%}")
        print(f"   最大回撤: {strategy.max_drawdown:.2%}")
        print(f"   交易次数: {strategy.total_trades}")
        print(f"   胜率: {strategy.win_rate:.1%}")
        print(f"   数据源: {strategy.data_source}")
        print(f"   参数: {strategy.parameters}")
        print()
    
    # 步骤6: 验证MB_KDJ策略
    print("🔍 步骤6: 验证MB_KDJ_[10,2]策略...")
    
    validation_report = optimizer.validate_mb_kdj_strategy(stock_data, gov_data)
    
    if validation_report.is_valid:
        print("✅ MB_KDJ_[10,2]策略验证通过!")
    else:
        print("⚠️ MB_KDJ_[10,2]策略性能偏差")
    
    print(f"期望Sharpe: {validation_report.expected_performance['sharpe_ratio']:.3f}")
    print(f"实际Sharpe: {validation_report.actual_performance['sharpe_ratio']:.3f}")
    print(f"偏差: {validation_report.deviation['sharpe_ratio']:.2%}")
    
    print("\\n🎉 完整工作流程完成!")

# 运行完整示例
complete_workflow_example()
```

## 🎯 常用使用场景

### 场景1: 单一股票分析

```python
def single_stock_analysis():
    """单一股票深度分析"""
    symbol = "0700.hk"  # 腾讯控股
    
    print(f"🔍 分析股票: {symbol}")
    
    # 创建分析器
    analyzer = QuickOptimizer()
    
    # 获取数据
    stock_data = analyzer.data_manager.fetch_stock_data(symbol, 365)
    
    # 基础统计
    print(f"\\n📊 基础统计:")
    print(f"数据期间: {stock_data.index[0].date()} 至 {stock_data.index[-1].date()}")
    print(f"交易天数: {len(stock_data)}")
    print(f"当前价格: {stock_data['close'].iloc[-1]:.2f}")
    print(f"期间最高: {stock_data['high'].max():.2f}")
    print(f"期间最低: {stock_data['low'].min():.2f}")
    print(f"平均成交量: {stock_data['volume'].mean():,.0f}")
    
    # 技术指标分析
    print(f"\\n📈 技术指标分析:")
    
    # RSI分析
    rsi = analyzer.indicator_engine.calculate_rsi(stock_data['close'], 14)
    latest_rsi = rsi.iloc[-1]
    rsi_signal = "超卖" if latest_rsi < 30 else "超买" if latest_rsi > 70 else "中性"
    print(f"RSI(14): {latest_rsi:.2f} - {rsi_signal}")
    
    # MACD分析
    macd = analyzer.indicator_engine.calculate_macd(stock_data['close'])
    macd_cross = "金叉" if macd['macd'].iloc[-1] > macd['signal'].iloc[-1] else "死叉"
    print(f"MACD: {macd_cross}")
    
    # KDJ分析
    kdj = analyzer.indicator_engine.calculate_kdj(
        stock_data['high'], stock_data['low'], stock_data['close']
    )
    latest_k = kdj['k'].iloc[-1]
    latest_d = kdj['d'].iloc[-1]
    kdj_signal = "买入" if latest_k < 20 and latest_k > latest_d else "卖出" if latest_k > 80 else "观望"
    print(f"KDJ: {kdj_signal}")
    
    # 策略优化
    print(f"\\n⚡ 策略优化:")
    results = analyzer.optimize(symbol, strategies=['RSI', 'MACD', 'KDJ'])
    
    print(f"测试策略数: {results.total_strategies_tested}")
    print(f"最佳策略: {results.top_strategies[0].name}")
    print(f"最佳Sharpe: {results.top_strategies[0].sharpe_ratio:.3f}")

# 运行单一股票分析
single_stock_analysis()
```

### 场景2: 多股票比较

```python
def multi_stock_comparison():
    """多股票比较分析"""
    symbols = ["0700.hk", "0941.hk", "1398.hk"]  # 腾讯、中国移动、工商银行
    
    print(f"📊 比较分析: {', '.join(symbols)}")
    
    # 创建分析器
    analyzer = QuickOptimizer()
    
    # 批量分析
    comparison_results = {}
    
    for symbol in symbols:
        print(f"\\n🔍 分析 {symbol}...")
        
        # 获取数据
        stock_data = analyzer.data_manager.fetch_stock_data(symbol, 252)
        
        # 基础指标
        current_price = stock_data['close'].iloc[-1]
        price_change = (current_price / stock_data['close'].iloc[0] - 1) * 100
        volatility = stock_data['close'].pct_change().std() * np.sqrt(252) * 100
        
        # 快速优化
        results = analyzer.optimize(symbol, strategies=['RSI', 'MACD'])
        best_sharpe = results.top_strategies[0].sharpe_ratio if results.top_strategies else 0
        
        comparison_results[symbol] = {
            'current_price': current_price,
            'price_change_pct': price_change,
            'volatility_pct': volatility,
            'best_sharpe': best_sharpe,
            'data_points': len(stock_data)
        }
    
    # 显示比较结果
    print(f"\\n📋 比较结果:")
    print(f"{'股票':<10} {'当前价格':<10} {'涨跌幅(%)':<10} {'波动率(%)':<10} {'最佳Sharpe':<10} {'数据点数':<10}")
    print("-" * 70)
    
    for symbol, metrics in comparison_results.items():
        print(f"{symbol:<10} {metrics['current_price']:<10.2f} {metrics['price_change_pct']:<10.2f} "
              f"{metrics['volatility_pct']:<10.2f} {metrics['best_sharpe']:<10.3f} {metrics['data_points']:<10}")
    
    # 找出表现最佳
    best_stock = max(comparison_results.keys(), 
                    key=lambda x: comparison_results[x]['best_sharpe'])
    print(f"\\n🏆 最佳股票: {best_stock} (Sharpe: {comparison_results[best_stock]['best_sharpe']:.3f})")

# 运行多股票比较
multi_stock_comparison()
```

### 场景3: 策略回测

```python
def strategy_backtest():
    """策略回测示例"""
    symbol = "0700.hk"
    
    print(f"🔄 策略回测: {symbol}")
    
    # 创建回测器
    data_manager = EnhancedDataManager()
    indicator_engine = EnhancedIndicatorEngine()
    
    # 获取数据
    stock_data = data_manager.fetch_stock_data(symbol, 252)
    gov_data = asyncio.run(data_manager.fetch_all_government_data(252))
    
    # 定义策略
    strategies = {
        'RSI策略': {
            'indicator': 'RSI',
            'params': {'period': 14, 'oversold': 30, 'overbought': 70},
            'signal': lambda rsi: 'BUY' if rsi < 30 else 'SELL' if rsi > 70 else 'HOLD'
        },
        'MACD策略': {
            'indicator': 'MACD',
            'params': {'fast': 12, 'slow': 26, 'signal': 9},
            'signal': lambda macd_dict: 'BUY' if macd_dict['macd'] > macd_dict['signal'] else 'SELL'
        },
        'MB_KDJ策略': {
            'indicator': 'KDJ',
            'params': {'k_period': 10, 'd_period': 2, 'j_period': 2},
            'signal': lambda kdj_dict: 'BUY' if kdj_dict['k'] < 20 and kdj_dict['k'] > kdj_dict['d'] else 'HOLD'
        }
    }
    
    # 运行回测
    backtest_results = {}
    
    for strategy_name, strategy_config in strategies.items():
        print(f"\\n📊 回测 {strategy_name}...")
        
        if strategy_config['indicator'] == 'RSI':
            indicator_values = indicator_engine.calculate_rsi(
                stock_data['close'], strategy_config['params']['period']
            )
        elif strategy_config['indicator'] == 'MACD':
            macd_result = indicator_engine.calculate_macd(
                stock_data['close'],
                strategy_config['params']['fast'],
                strategy_config['params']['slow'],
                strategy_config['params']['signal']
            )
            indicator_values = macd_result
        elif strategy_config['indicator'] == 'KDJ':
            kdj_result = indicator_engine.calculate_kdj(
                stock_data['high'], stock_data['low'], stock_data['close'],
                strategy_config['params']['k_period'],
                strategy_config['params']['d_period'],
                strategy_config['params']['j_period']
            )
            indicator_values = kdj_result
        
        # 简单回测逻辑
        returns = []
        positions = []
        signals = []
        
        for i in range(len(stock_data)):
            if i < 20:  # 前20天不交易
                signals.append('HOLD')
                positions.append(0)
                returns.append(0)
                continue
            
            if strategy_config['indicator'] == 'RSI':
                signal = strategy_config['signal'](indicator_values.iloc[i])
            elif strategy_config['indicator'] == 'MACD':
                signal = strategy_config['signal'](indicator_values)
            elif strategy_config['indicator'] == 'KDJ':
                signal = strategy_config['signal'](indicator_values)
            
            signals.append(signal)
            
            # 简单的仓位管理
            if signal == 'BUY' and (not positions or positions[-1] == 0):
                positions.append(1)  # 满仓
            elif signal == 'SELL' and (not positions or positions[-1] == 1):
                positions.append(0)  # 空仓
            else:
                positions.append(positions[-1] if positions else 0)
            
            # 计算收益
            daily_return = stock_data['close'].pct_change().iloc[i]
            strategy_return = daily_return * positions[-1]
            returns.append(strategy_return)
        
        # 计算策略指标
        returns_array = np.array(returns)
        total_return = (1 + returns_array).prod() - 1
        annual_return = (1 + total_return) ** (252 / len(returns)) - 1
        volatility = returns_array.std() * np.sqrt(252)
        sharpe_ratio = annual_return / volatility if volatility > 0 else 0
        max_drawdown = (np.maximum.accumulate(np.cumprod(1 + returns_array)) - 
                       np.cumprod(1 + returns_array)).max()
        
        backtest_results[strategy_name] = {
            'total_return': total_return,
            'annual_return': annual_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'trades': sum(1 for i in range(1, len(signals)) if signals[i] != signals[i-1])
        }
    
    # 显示回测结果
    print(f"\\n📋 回测结果对比:")
    print(f"{'策略':<12} {'总回报':<10} {'年化回报':<10} {'波动率':<10} {'Sharpe':<8} {'最大回撤':<10} {'交易次数':<8}")
    print("-" * 78)
    
    for strategy_name, results in backtest_results.items():
        print(f"{strategy_name:<12} {results['total_return']:<10.2%} {results['annual_return']:<10.2%} "
              f"{results['volatility']:<10.2%} {results['sharpe_ratio']:<8.3f} "
              f"{results['max_drawdown']:<10.2%} {results['trades']:<8}")
    
    # 找出最佳策略
    best_strategy = max(backtest_results.keys(), 
                      key=lambda x: backtest_results[x]['sharpe_ratio'])
    print(f"\\n🏆 最佳策略: {best_strategy} (Sharpe: {backtest_results[best_strategy]['sharpe_ratio']:.3f})")

# 运行策略回测
strategy_backtest()
```

## 🔧 实用工具函数

### 数据获取工具

```python
def get_stock_data_quick(symbol: str, days: int = 365):
    """快速获取股票数据"""
    data_manager = EnhancedDataManager()
    return data_manager.fetch_stock_data(symbol, days)

def calculate_indicators_batch(data: pd.DataFrame):
    """批量计算技术指标"""
    indicator_engine = EnhancedIndicatorEngine()
    
    indicators = {
        'RSI_14': indicator_engine.calculate_rsi(data['close'], 14),
        'RSI_30': indicator_engine.calculate_rsi(data['close'], 30),
        'MACD': indicator_engine.calculate_macd(data['close']),
        'KDJ': indicator_engine.calculate_kdj(data['high'], data['low'], data['close']),
        'BOLLINGER': indicator_engine.calculate_bollinger_bands(data['close'])
    }
    
    return indicators

def simple_optimization(symbol: str, strategies: list = None):
    """简单优化函数"""
    if strategies is None:
        strategies = ['RSI', 'MACD', 'KDJ']
    
    optimizer = QuickOptimizer()
    return optimizer.optimize(symbol, strategies=strategies)
```

### 结果分析工具

```python
def analyze_optimization_results(results):
    """分析优化结果"""
    if not results or not results.top_strategies:
        print("没有可分析的结果")
        return
    
    print(f"优化结果分析:")
    print(f"总策略数: {results.total_strategies_tested}")
    print(f"优化时间: {results.optimization_time:.2f}秒")
    
    # 按Sharpe排序
    sorted_strategies = sorted(results.top_strategies, key=lambda x: x.sharpe_ratio, reverse=True)
    
    # 统计分析
    sharpe_values = [s.sharpe_ratio for s in results.top_strategies if s.sharpe_ratio > 0]
    if sharpe_values:
        print(f"Sharpe统计:")
        print(f"  平均值: {np.mean(sharpe_values):.3f}")
        print(f"  中位数: {np.median(sharpe_values):.3f}")
        print(f"  标准差: {np.std(sharpe_values):.3f}")
        print(f"  最大值: {np.max(sharpe_values):.3f}")
    
    # 显示前10名
    print(f"\\n前10名策略:")
    for i, strategy in enumerate(sorted_strategies[:10], 1):
        print(f"{i:2d}. {strategy.name:<20} Sharpe:{strategy.sharpe_ratio:6.3f} "
              f"回报:{strategy.total_return:6.2%} 回撤:{strategy.max_drawdown:6.2%}")

# 使用示例
# results = simple_optimization("0700.hk")
# analyze_optimization_results(results)
```

## 📚 下一步学习

完成基础示例后，您可以继续学习：

1. **[高级优化示例](advanced_optimization.md)** - 学习高级优化技术
2. **[自定义指标示例](custom_indicators.md)** - 开发自定义技术指标
3. **[批量处理示例](batch_processing.md)** - 大规模数据处理
4. **[用户指南](../../user_guide/)** - 完整用户手册
5. **[故障排除指南](../../deployment/troubleshooting/)** - 问题解决方案

---

**🚀 开始您的量化交易之旅吧！**