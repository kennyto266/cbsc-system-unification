# 统一数据管道 (Unified Data Pipeline)

这个模块实现了价格和非价格数据的统一管理、缓存、验证和同步功能，为CBSC量化交易策略管理系统提供强大的数据基础设施。

## 核心组件

### 1. 统一缓存管理器 (UnifiedCacheManager)
- **L1缓存**: 内存缓存，提供极快的数据访问
- **L2缓存**: Redis缓存，提供持久化存储
- **自动提升**: L2缓存命中自动提升到L1
- **LRU驱逐**: 自动管理内存使用
- **统计监控**: 详细的缓存性能指标

### 2. 数据质量验证器 (DataQualityValidator)
- **全面检查**: 完整性、异常值、新鲜度、一致性等
- **智能评分**: 综合质量评分系统
- **异常检测**: 基于统计学的异常值识别
- **改进建议**: 自动生成数据改进建议

### 3. 数据同步器 (DataSynchronizer)
- **多源同步**: 并发同步多个数据源
- **时间对齐**: 自动对齐不同数据源的时间戳
- **质量保证**: 集成数据质量检查
- **任务管理**: 异步任务调度和监控

### 4. 统一数据管道 (UnifiedDataPipeline)
- **统一接口**: 为所有数据源提供一致的API
- **数据适配**: 可插拔的数据源适配器
- **自动缓存**: 智能缓存策略
- **质量集成**: 内置数据质量验证

### 5. 回测引擎 (UnifiedBacktestEngine)
- **混合策略**: 支持价格和非价格数据混合策略
- **多种信号**: 移动平均、RSI、布林带、情绪指标等
- **性能分析**: 全面的回测性能指标
- **对比分析**: 多策略对比和基准测试

## 快速开始

### 初始化系统

```python
from src.unified import initialize_unified_system
import asyncio

async def main():
    # 初始化统一数据系统
    await initialize_unified_system()
    print("统一数据系统初始化完成")

if __name__ == "__main__":
    asyncio.run(main())
```

### 获取统一数据

```python
from src.unified import (
    unified_data_pipeline, DataRequest, DataSource, DataType
)
from datetime import datetime, timedelta

async def fetch_data():
    # 创建数据请求
    request = DataRequest(
        symbols=['AAPL', 'GOOGL'],
        sources=[DataSource.PRICE, DataSource.HKMA, DataSource.SENTIMENT],
        start_time=datetime.now() - timedelta(days=30),
        end_time=datetime.now(),
        include_quality=True
    )

    # 获取统一数据
    data = await unified_data_pipeline.fetch_unified_data(request)

    for symbol, data_points in data.items():
        print(f"股票 {symbol}: {len(data_points)} 个数据点")
        for point in data_points[:5]:  # 显示前5个数据点
            print(f"  {point.timestamp}: {point.value} ({point.source})")

# 运行示例
asyncio.run(fetch_data())
```

### 运行回测

```python
from src.unified import (
    unified_backtest_engine, StrategyConfig, BacktestConfig, StrategyType
)

async def run_backtest():
    # 配置策略
    strategy_config = StrategyConfig(
        strategy_type=StrategyType.COMBINED,
        name="混合策略",
        parameters={
            'ma_short': 10,
            'ma_long': 30,
            'rsi_period': 14
        },
        signal_weights={
            'price': 0.5,
            'hkma': 0.3,
            'sentiment': 0.2
        }
    )

    # 配置回测
    backtest_config = BacktestConfig(
        initial_capital=1000000,
        commission_rate=0.001,
        slippage_rate=0.0001
    )

    # 运行回测
    result = await unified_backtest_engine.run_backtest(
        symbol="AAPL",
        strategy_config=strategy_config,
        backtest_config=backtest_config,
        start_time=datetime.now() - timedelta(days=90),
        end_time=datetime.now()
    )

    # 显示结果
    print(f"策略: {result.strategy_name}")
    print(f"总收益: {result.total_return:.2%}")
    print(f"夏普比率: {result.sharpe_ratio:.2f}")
    print(f"最大回撤: {result.max_drawdown:.2%}")
    print(f"交易次数: {result.total_trades}")

asyncio.run(run_backtest())
```

### 缓存操作

```python
from src.unified import unified_cache_manager
from datetime import timedelta

async def cache_example():
    # 缓存数据点
    data_point = {
        'symbol': 'AAPL',
        'value': 150.25,
        'timestamp': '2024-01-01T10:00:00Z',
        'source': 'price',
        'metadata': {'provider': 'yahoo'}
    }

    await unified_cache_manager.cache_unified_data_point(
        'AAPL', 'price', data_point['timestamp'], data_point
    )

    # 获取缓存数据
    cached_data = await unified_cache_manager.get_unified_data_point(
        'AAPL', 'price', '2024-01-01T10:00:00Z'
    )

    print(f"缓存数据: {cached_data}")

    # 获取缓存统计
    cache_stats = await unified_cache_manager.get_cache_info()
    print(f"缓存命中率: {cache_stats['total_stats']['hit_rate']:.1f}%")

asyncio.run(cache_example())
```

### 数据质量验证

```python
from src.unified import data_quality_validator

async def quality_check_example():
    # 准备测试数据
    test_data = [
        {
            'timestamp': '2024-01-01T10:00:00Z',
            'symbol': 'AAPL',
            'source': 'price',
            'data_type': 'ohlcv',
            'value': 150.0,
            'metadata': {'volume': 1000000}
        },
        # ... 更多数据点
    ]

    # 执行质量验证
    quality_result = await data_quality_validator.validate_data_quality(
        test_data, 'price', 'AAPL'
    )

    print(f"质量评分: {quality_result.overall_score:.3f}")
    print(f"质量等级: {quality_result.quality_level.name}")
    print(f"检查结果: {len(quality_result.checks)} 项")
    print(f"改进建议: {len(quality_result.recommendations)} 项")

asyncio.run(quality_check_example())
```

## 数据源支持

### 价格数据 (DataSource.PRICE)
- Yahoo Finance
- Alpha Vantage
- 其他实时价格数据源

### HKMA数据 (DataSource.HKMA)
- HIBOR利率
- 货币基础
- 汇率数据
- 银行同业利率

### 情绪数据 (DataSource.SENTIMENT)
- 新闻情绪分析
- 社交媒体情绪
- 分析师评级
- 市场情绪指标

### 另类数据 (DataSource.ALTERNATIVE)
- 卫星图像数据
- 供应链数据
- 信用卡交易数据
- 其他另类数据源

## 配置选项

### 缓存配置
```python
from src.unified import UnifiedCacheManager

cache_manager = UnifiedCacheManager(
    l1_max_size=2000,      # L1缓存大小
    cleanup_interval=300,   # 清理间隔(秒)
    default_ttl=timedelta(minutes=10)  # 默认TTL
)
```

### 质量验证配置
```python
from src.unified import QualityThresholds

thresholds = QualityThresholds(
    completeness_threshold=0.95,  # 95%完整性
    outlier_threshold=3.0,        # 3-sigma异常值
    staleness_threshold=300,      # 5分钟新鲜度
    duplicate_threshold=0.01      # 1%重复阈值
)

validator = DataQualityValidator(thresholds)
```

### 同步配置
```python
from src.unified import DataSyncConfig

sync_config = DataSyncConfig(
    max_concurrent_tasks=15,
    retry_attempts=3,
    batch_size=50,
    timeout_seconds=600,
    enable_quality_check=True
)
```

## 监控和调试

### 获取系统状态
```python
# 缓存状态
cache_stats = await unified_cache_manager.get_cache_info()

# 同步状态
sync_stats = data_synchronizer.get_sync_stats()

# 管道统计
pipeline_stats = unified_data_pipeline.get_pipeline_stats()
```

### 日志记录
系统使用Python的logging模块，可以通过以下方式配置日志级别：

```python
import logging
logging.basicConfig(level=logging.INFO)
```

### 错误处理
所有组件都实现了完善的错误处理和异常管理，确保系统稳定性。

## 测试

运行综合测试：
```bash
cd src/unified
python test_unified_system.py
```

测试包括：
- 缓存管理器功能测试
- 数据质量验证测试
- 数据同步器测试
- 数据管道测试
- 回测引擎测试
- 端到端集成测试

## 性能优化

### 缓存策略
- 热数据自动提升到L1
- 智能TTL管理
- LRU驱逐策略
- 批量操作优化

### 并发处理
- 异步I/O操作
- 线程池执行
- 批量数据获取
- 任务队列管理

### 内存管理
- 对象池技术
- 延迟加载
- 垃圾回收优化
- 内存使用监控

## 扩展性

### 添加新的数据源
1. 实现`DataSourceAdapter`接口
2. 注册到数据管道
3. 配置缓存和验证策略

### 自定义质量检查
1. 扩展`DataQualityValidator`
2. 添加新的检查规则
3. 自定义评分算法

### 自定义信号生成器
1. 实现`SignalGenerator`接口
2. 注册到回测引擎
3. 配置策略参数

## 最佳实践

1. **数据质量优先**: 始终验证数据质量
2. **合理使用缓存**: 根据数据特性设置合适的TTL
3. **监控性能**: 定期检查缓存命中率和同步性能
4. **错误处理**: 实现完善的异常处理和重试机制
5. **测试覆盖**: 确保所有组件都有充分的测试

## 故障排除

### 常见问题

**Q: 缓存连接失败**
A: 检查Redis服务是否运行，配置连接参数

**Q: 数据质量评分过低**
A: 检查数据源质量，调整验证阈值

**Q: 回测结果异常**
A: 验证数据完整性，检查策略参数

**Q: 同步任务失败**
A: 查看任务日志，检查数据源连接

### 调试工具
- 详细日志记录
- 性能监控指标
- 数据质量报告
- 错误追踪信息

## 版本历史

- **v1.0.0**: 初始版本，包含核心功能
- 支持多数据源统一管理
- 实现L1+L2缓存架构
- 提供数据质量验证
- 支持混合策略回测

## 贡献

欢迎提交Issue和Pull Request来改进这个模块。

## 许可证

本项目遵循CBSC项目的许可证条款。