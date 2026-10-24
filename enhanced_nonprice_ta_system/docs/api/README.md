# Enhanced Non-Price TA System - API文档

## 📖 API文档概述

Enhanced Non-Price Technical Analysis System提供完整的API接口，支持所有技术分析功能。本文档详细描述了所有API接口的使用方法、参数说明和示例代码。

## 🏗️ API架构概览

### 核心组件架构
```
Enhanced Non-Price TA System
├── CoreOptimizerEngine      # 核心优化引擎
├── EnhancedDataManager      # 数据管理器
├── EnhancedIndicatorEngine  # 指标计算引擎
├── IntelligentCache         # 智能缓存系统
├── PerformanceMonitor       # 性能监控系统
└── EnhancedErrorHandler     # 错误处理系统
```

### API层次结构
```
API Layer
├── High Level APIs         # 高级API (便于使用)
│   ├── QuickOptimizer     # 快速优化
│   ├── SimpleBacktest     # 简单回测
│   └── BasicAnalysis      # 基础分析
├── Core APIs              # 核心API (功能完整)
│   ├── OptimizationEngine # 优化引擎
│   ├── IndicatorEngine    # 指标引擎
│   └── DataManager        # 数据管理
└── Low Level APIs         # 底层API (高级控制)
    ├── CacheManager       # 缓存管理
    ├── PerformanceMonitor # 性能监控
    └── ErrorHandler       # 错误处理
```

## 📚 API文档目录

### 🔧 核心API文档
- [CoreOptimizerEngine API](core_optimizer_api.md) - 核心优化引擎接口
- [EnhancedDataManager API](data_manager_api.md) - 数据管理器接口
- [EnhancedIndicatorEngine API](indicator_engine_api.md) - 指标计算引擎接口
- [IntelligentCache API](cache_system_api.md) - 智能缓存系统接口
- [PerformanceMonitor API](performance_monitor_api.md) - 性能监控系统接口
- [EnhancedErrorHandler API](error_handler_api.md) - 错误处理系统接口

### 📖 使用示例和教程
- [基础使用示例](examples/basic_usage.md) - 快速入门示例
- [高级优化示例](examples/advanced_optimization.md) - 高级优化技术
- [自定义指标示例](examples/custom_indicators.md) - 自定义指标开发
- [批量处理示例](examples/batch_processing.md) - 批量数据处理

## 🚀 快速开始

### 1. 基础使用 - 快速优化
```python
from enhanced_nonprice_ta_system import QuickOptimizer

# 创建快速优化器
optimizer = QuickOptimizer()

# 运行快速优化 (使用默认参数)
results = optimizer.optimize('0700.hk', strategies=['RSI', 'MACD', 'KDJ'])

# 获取最佳策略
best_strategy = results.get_best_strategy()
print(f"最佳策略: {best_strategy.name}, Sharpe: {best_strategy.sharpe_ratio:.3f}")
```

### 2. 核心API使用 - 完整控制
```python
from enhanced_nonprice_ta_system import (
    EnhancedOptimizerEngine,
    EnhancedDataManager,
    EnhancedIndicatorEngine
)

# 创建核心组件
data_manager = EnhancedDataManager()
indicator_engine = EnhancedIndicatorEngine()
optimizer = EnhancedOptimizerEngine(
    data_manager=data_manager,
    indicator_engine=indicator_engine
)

# 获取数据
data = data_manager.fetch_stock_data('0700.hk', 365)
gov_data = await data_manager.fetch_all_government_data()

# 自定义优化参数
optimization_config = {
    'strategies': ['RSI', 'MACD', 'KDJ', 'BOLLINGER'],
    'parameter_ranges': {
        'RSI': {'period': range(10, 51)},
        'MACD': {'fast': range(10, 21), 'slow': range(20, 31)},
        'KDJ': {'k_period': range(5, 21), 'd_period': range(2, 6)}
    },
    'parallel_cores': 16,
    'use_cache': True
}

# 运行优化
results = optimizer.run_optimization(data, gov_data, optimization_config)

# 详细结果分析
for strategy in results.top_strategies:
    print(f"{strategy.name}: Sharpe={strategy.sharpe_ratio:.3f}, "
          f"Return={strategy.total_return:.2%}, "
          f"Drawdown={strategy.max_drawdown:.2%}")
```

### 3. 高级用法 - 自定义指标和策略
```python
from enhanced_nonprice_ta_system import EnhancedIndicatorEngine
from enhanced_nonprice_ta_system.core import StrategyBuilder

# 创建指标引擎
indicator_engine = EnhancedIndicatorEngine()

# 自定义指标计算
def custom_enhanced_rsi(data, period=14, threshold=0.7):
    """增强RSI指标，结合政府数据"""
    base_rsi = indicator_engine.calculate_rsi(data['close'], period)
    # 获取政府数据
    hibor = indicator_engine.get_hibor_data()
    # 结合政府数据调整RSI信号
    adjusted_rsi = base_rsi * (1 + hibor['rate'] * threshold)
    return adjusted_rsi

# 使用StrategyBuilder创建自定义策略
strategy_builder = StrategyBuilder()

# 创建基于增强RSI的策略
strategy = strategy_builder.create_strategy(
    name='Enhanced_RSI_With_Gov_Data',
    indicators=[custom_enhanced_rsi],
    buy_signal=lambda signals: signals['custom_rsi'] < 30,
    sell_signal=lambda signals: signals['custom_rsi'] > 70,
    risk_management={
        'stop_loss': 0.05,  # 5%止损
        'take_profit': 0.15,  # 15%止盈
        'position_size': 0.3  # 30%仓位
    }
)

# 运行回测
backtest_results = strategy.backtest(data, gov_data)
print(f"策略结果: Sharpe={backtest_results.sharpe_ratio:.3f}")
```

## 🎯 API特性概览

### 🚀 性能特性
- **32核并行处理**: 充分利用多核CPU进行并行计算
- **智能缓存系统**: L1内存缓存 + L2磁盘缓存，显著提升性能
- **内存优化**: 高效的内存管理，支持大规模数据处理
- **实时监控**: 性能监控和瓶颈分析

### 🔧 功能特性
- **81种技术指标**: 覆盖RSI、MACD、KDJ、布林带等主流指标
- **9个政府数据源**: HIBOR、货币基础、GDP等经济数据集成
- **策略优化**: 自动参数优化和策略组合
- **风险管理**: 完整的止损、止盈和仓位管理

### 🛡️ 可靠性特性
- **错误处理**: 智能错误分类和自动恢复
- **数据验证**: 多层数据质量检查
- **后备机制**: 数据源故障自动切换
- **系统监控**: 实时健康状态监控

### 📊 易用性特性
- **分层API**: 从简单到复杂的多层次API设计
- **详细文档**: 完整的API文档和使用示例
- **类型提示**: 完整的类型提示支持
- **异常处理**: 清晰的错误信息和处理建议

## 📖 API使用指南

### 🔰 初学者建议
1. 从[QuickOptimizer](examples/basic_usage.md#quick-optimizer)开始
2. 学习[基础优化概念](../user_guide/tutorials/beginner/basic_concepts.md)
3. 尝试[简单策略示例](examples/basic_usage.md#simple-strategies)

### 👨‍💻 开发者建议
1. 查看[核心API文档](core_optimizer_api.md)
2. 了解[系统架构](../developer/architecture/system_architecture.md)
3. 学习[自定义开发](../developer/extending/)

### 🚀 高级用户建议
1. 研究[高级优化技术](examples/advanced_optimization.md)
2. 开发[自定义指标](examples/custom_indicators.md)
3. 优化[系统性能](../developer/api_internals/performance_analysis.md)

## 🔗 相关资源

### 📚 学习资源
- [用户指南](../user_guide/) - 完整用户手册
- [教程集合](../user_guide/tutorials/) - 分级教程
- [最佳实践](../user_guide/best_practices/) - 使用建议

### 🛠️ 开发资源
- [开发者文档](../developer/) - 开发相关文档
- [架构设计](../developer/architecture/) - 系统架构说明
- [贡献指南](../developer/contributing/) - 贡献代码指南

### 🚀 部署资源
- [部署指南](../deployment/) - 部署相关文档
- [配置参考](../deployment/configuration/) - 配置参数说明
- [故障排除](../deployment/troubleshooting/) - 问题解决方案

## 📞 技术支持

如果您在使用API时遇到问题，可以：
1. 查看[常见问题](../deployment/troubleshooting/common_issues.md)
2. 阅读[错误代码参考](../deployment/troubleshooting/error_codes.md)
3. 提交Issue到项目仓库
4. 联系技术支持团队

---

**🚀 开始探索Enhanced Non-Price TA System的强大API功能！**