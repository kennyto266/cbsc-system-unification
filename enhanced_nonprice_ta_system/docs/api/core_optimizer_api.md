# CoreOptimizerEngine API - 核心优化引擎

## 📖 概述

`CoreOptimizerEngine`是Enhanced Non-Price Technical Analysis System的核心组件，负责策略优化、参数调整和性能评估。该引擎支持32核并行处理，智能缓存和实时性能监控。

## 🏗️ 类结构

```python
class CoreOptimizerEngine:
    """核心优化引擎"""
    
    def __init__(
        self,
        data_manager: Optional[EnhancedDataManager] = None,
        indicator_engine: Optional[EnhancedIndicatorEngine] = None,
        cache_manager: Optional[IntelligentCache] = None,
        performance_monitor: Optional[PerformanceMonitor] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """初始化优化引擎"""
```

## 🚀 核心方法

### 1. 数据获取方法

#### fetch_real_stock_data()
```python
def fetch_real_stock_data(
    self,
    symbol: str = "0700.hk",
    days: int = 365,
    use_cache: bool = True
) -> pd.DataFrame:
    """
    获取真实股票数据
    
    Parameters:
    -----------
    symbol : str, default "0700.hk"
        股票代码 (支持所有港股代码)
    days : int, default 365
        获取天数 (建议252-1095)
    use_cache : bool, default True
        是否使用缓存数据
    
    Returns:
    --------
    pd.DataFrame
        包含OHLCV数据的DataFrame
        - open: 开盘价
        - high: 最高价
        - low: 最低价
        - close: 收盘价
        - volume: 成交量
    """
```

**示例用法:**
```python
from enhanced_nonprice_ta_system import CoreOptimizerEngine

# 创建引擎
engine = CoreOptimizerEngine()

# 获取腾讯3年数据
tencent_data = engine.fetch_real_stock_data("0700.hk", 1095)
print(f"数据行数: {len(tencent_data)}")
print(f"价格范围: {tencent_data['close'].min():.2f} - {tencent_data['close'].max():.2f}")

# 获取港交所1年数据
hkex_data = engine.fetch_real_stock_data("0388.hk", 365)

# 批量获取多只股票
symbols = ["0700.hk", "0941.hk", "1398.hk"]
stock_data = {}
for symbol in symbols:
    stock_data[symbol] = engine.fetch_real_stock_data(symbol, 365)
```

#### fetch_all_government_data()
```python
async def fetch_all_government_data(
    self,
    days: int = 252,
    use_cache: bool = True,
    timeout: int = 30
) -> Dict[str, pd.DataFrame]:
    """
    获取所有政府数据源
    
    Parameters:
    -----------
    days : int, default 252
        获取天数
    use_cache : bool, default True
        是否使用缓存
    timeout : int, default 30
        请求超时时间(秒)
    
    Returns:
    --------
    Dict[str, pd.DataFrame]
        包含所有政府数据的字典
        - 'hibor': HIBOR利率数据
        - 'monetary_base': 货币基础数据
        - 'exchange_rate': 汇率数据
        - 'gdp': GDP数据
        - 'retail_sales': 零售销售数据
        - 'property_market': 物业市场数据
        - 'trade_data': 贸易数据
        - 'unemployment': 失业率数据
        - 'tourism': 旅游数据
    """
```

**示例用法:**
```python
import asyncio
from enhanced_nonprice_ta_system import CoreOptimizerEngine

async def fetch_gov_data_example():
    engine = CoreOptimizerEngine()
    
    # 获取所有政府数据
    gov_data = await engine.fetch_all_government_data(365)
    
    # 查看数据源
    for source, data in gov_data.items():
        print(f"{source}: {len(data)} 条记录")
        if not data.empty:
            print(f"  最新日期: {data.index[-1]}")
    
    # 获取特定数据源
    hibor_data = gov_data['hibor']
    print(f"最新HIBOR利率: {hibor_data['rate'].iloc[-1]:.3f}%")

# 运行异步函数
asyncio.run(fetch_gov_data_example())
```

### 2. 核心优化方法

#### run_enhanced_optimization()
```python
def run_enhanced_optimization(
    self,
    symbol: str = "0700.hk",
    optimization_config: Optional[Dict[str, Any]] = None,
    parallel_cores: int = 32,
    use_cache: bool = True,
    validate_mb_kdj: bool = True
) -> OptimizationResult:
    """
    运行增强优化
    
    Parameters:
    -----------
    symbol : str, default "0700.hk"
        目标股票代码
    optimization_config : dict, optional
        优化配置参数
    parallel_cores : int, default 32
        并行核心数
    use_cache : bool, default True
        是否使用缓存
    validate_mb_kdj : bool, default True
        是否验证MB_KDJ_[10,2]策略
    
    Returns:
    --------
    OptimizationResult
        优化结果对象，包含:
        - top_strategies: 最佳策略列表
        - performance_metrics: 性能指标
        - optimization_time: 优化耗时
        - total_strategies_tested: 总测试策略数
    """
```

**默认优化配置:**
```python
DEFAULT_OPTIMIZATION_CONFIG = {
    'strategies': ['RSI', 'MACD', 'KDJ', 'BOLLINGER', 'CCI'],
    'parameter_ranges': {
        'RSI': {
            'period': range(5, 301),
            'oversold': [20, 25, 30],
            'overbought': [70, 75, 80]
        },
        'MACD': {
            'fast': range(5, 51),
            'slow': range(51, 301),
            'signal': range(5, 21)
        },
        'KDJ': {
            'k_period': range(5, 301),
            'd_period': range(1, 21),
            'j_period': range(1, 21)
        },
        'BOLLINGER': {
            'period': range(5, 301),
            'std_dev': [1.5, 2.0, 2.5, 3.0]
        },
        'CCI': {
            'period': range(5, 301),
            'oversold': [-200, -150, -100],
            'overbought': [100, 150, 200]
        }
    },
    'risk_free_rate': 0.03,  # 3%无风险利率
    'min_trades': 10,       # 最小交易次数
    'max_drawdown_threshold': 0.5  # 最大回撤阈值
}
```

**示例用法:**
```python
from enhanced_nonprice_ta_system import CoreOptimizerEngine

# 创建引擎
engine = CoreOptimizerEngine()

# 运行默认优化
results = engine.run_enhanced_optimization("0700.hk")

# 查看结果
print(f"总测试策略数: {results.total_strategies_tested}")
print(f"优化耗时: {results.optimization_time:.2f}秒")

# 查看前5名策略
print("\\nTop 5 Strategies:")
for i, strategy in enumerate(results.top_strategies[:5], 1):
    print(f"{i}. {strategy.name}")
    print(f"   Sharpe Ratio: {strategy.sharpe_ratio:.3f}")
    print(f"   Total Return: {strategy.total_return:.2%}")
    print(f"   Max Drawdown: {strategy.max_drawdown:.2%}")
    print(f"   Parameters: {strategy.parameters}")
    print()

# 自定义优化配置
custom_config = {
    'strategies': ['RSI', 'MACD'],
    'parameter_ranges': {
        'RSI': {
            'period': range(10, 51),  # 10-50
            'oversold': [25, 30],
            'overbought': [70, 75]
        },
        'MACD': {
            'fast': range(10, 21),   # 10-20
            'slow': range(20, 31),   # 20-30
            'signal': range(8, 13)   # 8-12
        }
    }
}

# 运行自定义优化
custom_results = engine.run_enhanced_optimization(
    "0941.hk",
    optimization_config=custom_config,
    parallel_cores=16
)
```

#### optimize_single_strategy()
```python
def optimize_single_strategy(
    self,
    strategy_type: str,
    stock_data: pd.DataFrame,
    gov_data: Dict[str, pd.DataFrame],
    parameter_space: Dict[str, Any],
    parallel_cores: int = 8
) -> List[StrategyResult]:
    """
    优化单一策略类型
    
    Parameters:
    -----------
    strategy_type : str
        策略类型 ('RSI', 'MACD', 'KDJ', etc.)
    stock_data : pd.DataFrame
        股票数据
    gov_data : dict
        政府数据
    parameter_space : dict
        参数搜索空间
    parallel_cores : int, default 8
        并行核心数
    
    Returns:
    --------
    List[StrategyResult]
        策略结果列表
    """
```

**示例用法:**
```python
# 专门优化KDJ策略
parameter_space = {
    'k_period': range(5, 21),      # 5-20
    'd_period': range(1, 6),       # 1-5
    'j_period': range(1, 6),       # 1-5
    'oversold': [10, 15, 20, 25],  # 超卖阈值
    'overbought': [75, 80, 85, 90] # 超买阈值
}

kdj_results = engine.optimize_single_strategy(
    strategy_type='KDJ',
    stock_data=stock_data,
    gov_data=gov_data,
    parameter_space=parameter_space,
    parallel_cores=16
)

# 找到最佳KDJ策略
best_kdj = max(kdj_results, key=lambda x: x.sharpe_ratio)
print(f"最佳KDJ策略: {best_kdj.parameters}")
print(f"Sharpe Ratio: {best_kdj.sharpe_ratio:.3f}")
```

### 3. MB_KDJ_[10,2]策略验证

#### validate_mb_kdj_strategy()
```python
def validate_mb_kdj_strategy(
    self,
    stock_data: pd.DataFrame,
    gov_data: Dict[str, pd.DataFrame],
    tolerance: float = 0.05
) -> ValidationReport:
    """
    验证MB_KDJ_[10,2]策略性能
    
    Parameters:
    -----------
    stock_data : pd.DataFrame
        股票数据
    gov_data : dict
        政府数据
    tolerance : float, default 0.05
        性能容忍度 (5%)
    
    Returns:
    --------
    ValidationReport
        验证报告，包含:
        - is_valid: 是否通过验证
        - actual_performance: 实际性能
        - expected_performance: 期望性能
        - deviation: 偏差百分比
        - detailed_metrics: 详细指标
    """
```

**期望性能基准:**
```python
MB_KDJ_BENCHMARK = {
    'sharpe_ratio': 3.672,
    'max_drawdown': -9.16,  # -9.16%
    'annual_return': 121.62,  # 121.62%
    'total_trades': 45,
    'win_rate': 0.62
}
```

**示例用法:**
```python
# 验证MB_KDJ策略
validation_report = engine.validate_mb_kdj_strategy(stock_data, gov_data)

if validation_report.is_valid:
    print("✅ MB_KDJ_[10,2]策略验证通过!")
else:
    print("⚠️ MB_KDJ_[10,2]策略性能偏差过大")

print(f"实际Sharpe: {validation_report.actual_performance['sharpe_ratio']:.3f}")
print(f"期望Sharpe: {validation_report.expected_performance['sharpe_ratio']:.3f}")
print(f"偏差: {validation_report.deviation['sharpe_ratio']:.2%}")

# 查看详细指标
for metric, value in validation_report.detailed_metrics.items():
    print(f"{metric}: {value}")
```

### 4. 性能分析和报告

#### generate_performance_report()
```python
def generate_performance_report(
    self,
    results: OptimizationResult,
    output_format: str = "json",
    include_charts: bool = True,
    output_path: Optional[str] = None
) -> str:
    """
    生成性能报告
    
    Parameters:
    -----------
    results : OptimizationResult
        优化结果
    output_format : str, default "json"
        输出格式 ('json', 'html', 'csv', 'xlsx')
    include_charts : bool, default True
        是否包含图表 (仅HTML格式)
    output_path : str, optional
        输出文件路径
    
    Returns:
    --------
    str
        报告内容或文件路径
    """
```

**示例用法:**
```python
# 生成JSON报告
json_report = engine.generate_performance_report(
    results,
    output_format="json",
    output_path="optimization_report_20251125.json"
)

# 生成HTML报告 (包含图表)
html_report = engine.generate_performance_report(
    results,
    output_format="html",
    include_charts=True,
    output_path="optimization_report_20251125.html"
)

# 生成Excel报告
excel_report = engine.generate_performance_report(
    results,
    output_format="xlsx",
    output_path="optimization_report_20251125.xlsx"
)

print(f"报告已生成: {json_report}")
```

#### analyze_performance_bottlenecks()
```python
def analyze_performance_bottlenecks(
    self,
    optimization_results: OptimizationResult
) -> PerformanceAnalysis:
    """
    分析性能瓶颈
    
    Parameters:
    -----------
    optimization_results : OptimizationResult
        优化结果
    
    Returns:
    --------
    PerformanceAnalysis
        性能分析报告，包含:
        - bottlenecks: 瓶颈分析
        - recommendations: 优化建议
        - resource_usage: 资源使用情况
        - efficiency_metrics: 效率指标
    """
```

**示例用法:**
```python
# 分析性能瓶颈
performance_analysis = engine.analyze_performance_bottlenecks(results)

print("性能瓶颈分析:")
for bottleneck in performance_analysis.bottlenecks:
    print(f"- {bottleneck.component}: {bottleneck.description}")
    print(f"  影响: {bottleneck.impact:.2%}")
    print(f"  建议: {bottleneck.recommendation}")

print("\\n优化建议:")
for recommendation in performance_analysis.recommendations:
    print(f"- {recommendation}")
```

## 📊 结果对象

### OptimizationResult
```python
@dataclass
class OptimizationResult:
    """优化结果类"""
    top_strategies: List[StrategyResult]
    performance_metrics: Dict[str, float]
    optimization_time: float
    total_strategies_tested: int
    success_rate: float
    cache_hit_rate: float
    parallel_efficiency: float
    memory_usage_peak: float
    validation_report: Optional[ValidationReport] = None
```

### StrategyResult
```python
@dataclass
class StrategyResult:
    """策略结果类"""
    name: str
    strategy_type: str
    parameters: Dict[str, Any]
    sharpe_ratio: float
    total_return: float
    max_drawdown: float
    annual_return: float
    volatility: float
    total_trades: int
    win_rate: float
    profit_factor: float
    calmar_ratio: float
    sortino_ratio: float
    data_source: str
    execution_time: float
```

## ⚙️ 配置参数

### 引擎配置
```python
ENGINE_CONFIG = {
    # 性能设置
    'parallel_cores': 32,
    'chunk_size': 1000,
    'memory_limit_gb': 8,
    
    # 缓存设置
    'cache_enabled': True,
    'cache_ttl_hours': 24,
    'cache_size_mb': 1024,
    
    # 数据设置
    'data_timeout_seconds': 30,
    'retry_attempts': 3,
    'data_validation_enabled': True,
    
    # 优化设置
    'min_trades_threshold': 10,
    'max_drawdown_threshold': 0.5,
    'risk_free_rate': 0.03,
    
    # 监控设置
    'performance_monitoring': True,
    'logging_level': 'INFO',
    'progress_reporting': True
}
```

## 🚨 错误处理

### 常见错误类型
```python
class CoreOptimizerError(Exception):
    """优化引擎基础异常"""
    pass

class DataFetchError(CoreOptimizerError):
    """数据获取错误"""
    pass

class OptimizationError(CoreOptimizerError):
    """优化过程错误"""
    pass

class StrategyValidationError(CoreOptimizerError):
    """策略验证错误"""
    pass

class PerformanceError(CoreOptimizerError):
    """性能相关错误"""
    pass
```

### 错误处理示例
```python
try:
    results = engine.run_enhanced_optimization("0700.hk")
except DataFetchError as e:
    print(f"数据获取失败: {e}")
    # 使用缓存数据或备用数据源
except OptimizationError as e:
    print(f"优化过程错误: {e}")
    # 减少参数范围或核心数
except PerformanceError as e:
    print(f"性能问题: {e}")
    # 调整内存或并发设置
except Exception as e:
    print(f"未知错误: {e}")
    # 记录错误并退出
```

## 📈 性能优化建议

### 1. 数据优化
- 使用缓存减少重复数据获取
- 批量获取多只股票数据
- 合理设置数据更新频率

### 2. 计算优化
- 根据系统配置调整并行核心数
- 使用适当的参数搜索范围
- 启用智能缓存避免重复计算

### 3. 内存优化
- 设置合理的内存限制
- 定期清理缓存数据
- 使用数据分块处理大数据集

## 📚 相关API
- [EnhancedDataManager API](data_manager_api.md) - 数据管理
- [EnhancedIndicatorEngine API](indicator_engine_api.md) - 指标计算
- [IntelligentCache API](cache_system_api.md) - 缓存系统
- [PerformanceMonitor API](performance_monitor_api.md) - 性能监控

---

**🚀 CoreOptimizerEngine是系统的核心，让您的策略优化更高效、更可靠！**