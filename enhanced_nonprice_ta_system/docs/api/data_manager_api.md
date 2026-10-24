# EnhancedDataManager API - 数据管理器

## 📖 概述

`EnhancedDataManager`负责管理所有数据源，包括股票数据和香港政府经济数据。提供统一的数据获取接口、数据质量验证、缓存管理和后备机制。

## 🏗️ 类结构

```python
class EnhancedDataManager:
    """增强数据管理器"""
    
    def __init__(
        self,
        cache_manager: Optional[IntelligentCache] = None,
        performance_monitor: Optional[PerformanceMonitor] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """初始化数据管理器"""
```

## 🚀 核心方法

### 1. 股票数据管理

#### fetch_stock_data()
```python
def fetch_stock_data(
    self,
    symbol: str,
    days: int = 365,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    use_cache: bool = True,
    validate_data: bool = True,
    timeout: int = 30
) -> pd.DataFrame:
    """
    获取股票数据
    
    Parameters:
    -----------
    symbol : str
        股票代码 (支持所有港股代码，如 "0700.hk", "0388.hk")
    days : int, default 365
        获取天数
    start_date : str, optional
        开始日期 (YYYY-MM-DD格式)
    end_date : str, optional
        结束日期 (YYYY-MM-DD格式)
    use_cache : bool, default True
        是否使用缓存
    validate_data : bool, default True
        是否验证数据质量
    timeout : int, default 30
        请求超时时间(秒)
    
    Returns:
    --------
    pd.DataFrame
        股票OHLCV数据
        - open: 开盘价
        - high: 最高价
        - low: 最低价
        - close: 收盘价
        - volume: 成交量
        - adj_close: 复权收盘价 (如果有)
    
    Raises:
    -------
    DataFetchError: 数据获取失败
    DataValidationError: 数据验证失败
    """
```

**示例用法:**
```python
from enhanced_nonprice_ta_system import EnhancedDataManager

# 创建数据管理器
data_manager = EnhancedDataManager()

# 基础用法 - 获取腾讯1年数据
tencent_data = data_manager.fetch_stock_data("0700.hk", 365)
print(f"腾讯数据: {len(tencent_data)} 条记录")
print(f"价格范围: {tencent_data['close'].min():.2f} - {tencent_data['close'].max():.2f}")

# 指定日期范围
hkex_data = data_manager.fetch_stock_data(
    symbol="0388.hk",
    start_date="2024-01-01",
    end_date="2024-12-31"
)

# 批量获取多只股票
symbols = ["0700.hk", "0941.hk", "1398.hk", "3988.hk"]
all_stock_data = {}
for symbol in symbols:
    try:
        data = data_manager.fetch_stock_data(symbol, 252)
        all_stock_data[symbol] = data
        print(f"{symbol}: 获取成功，{len(data)} 条记录")
    except DataFetchError as e:
        print(f"{symbol}: 获取失败 - {e}")
```

#### get_multiple_stocks()
```python
def get_multiple_stocks(
    self,
    symbols: List[str],
    days: int = 365,
    parallel: bool = True,
    max_workers: int = 8
) -> Dict[str, pd.DataFrame]:
    """
    批量获取多只股票数据
    
    Parameters:
    -----------
    symbols : list[str]
        股票代码列表
    days : int, default 365
        获取天数
    parallel : bool, default True
        是否并行获取
    max_workers : int, default 8
        最大并发数
    
    Returns:
    --------
    dict[str, pd.DataFrame]
        股票数据字典
    """
```

**示例用法:**
```python
# 定义HSI成分股
hsi_stocks = [
    "0700.hk",  # 腾讯
    "0941.hk",  # 中国移动
    "1299.hk",  # 友邦保险
    "2318.hk",  # 中国平安
    "0005.hk",  # 汇丰控股
    "0388.hk",  # 港交所
    "1398.hk",  # 工商银行
    "3988.hk",  # 中国银行
]

# 批量获取
stock_data_dict = data_manager.get_multiple_stocks(hsi_stocks, 252, parallel=True)

# 统计信息
print(f"成功获取 {len(stock_data_dict)} 只股票数据")
for symbol, data in stock_data_dict.items():
    print(f"{symbol}: {len(data)} 条记录，最新价格 {data['close'].iloc[-1]:.2f}")
```

#### validate_stock_data()
```python
def validate_stock_data(
    self,
    data: pd.DataFrame,
    symbol: str,
    strict_mode: bool = False
) -> DataValidationReport:
    """
    验证股票数据质量
    
    Parameters:
    -----------
    data : pd.DataFrame
        待验证的数据
    symbol : str
        股票代码
    strict_mode : bool, default False
        严格模式验证
    
    Returns:
    --------
    DataValidationReport
        验证报告
    """
```

**验证规则:**
```python
VALIDATION_RULES = {
    'price_positive': '所有价格必须为正数',
    'volume_non_negative': '成交量不能为负',
    'high_ge_low': '最高价必须 >= 最低价',
    'close_within_high_low': '收盘价必须在高低价范围内',
    'date_ascending': '日期必须升序排列',
    'no_duplicates': '不能有重复日期',
    'sufficient_data': '数据量必须足够',
    'reasonable_price_range': '价格变化必须在合理范围内',
    'volume_reasonable': '成交量不能异常',
    'no_gaps': '不能有数据缺口 (严格模式)'
}
```

**示例用法:**
```python
# 验证数据质量
validation_report = data_manager.validate_stock_data(tencent_data, "0700.hk")

if validation_report.is_valid:
    print("✅ 数据质量验证通过")
else:
    print("⚠️ 数据质量问题:")
    for issue in validation_report.issues:
        print(f"  - {issue}")
    
    # 查看详细统计
    stats = validation_report.statistics
    print(f"数据统计: {len(stats)} 条记录")
    print(f"价格范围: {stats['price_min']:.2f} - {stats['price_max']:.2f}")
    print(f"成交量范围: {stats['volume_min']} - {stats['volume_max']}")
```

### 2. 政府数据管理

#### fetch_government_data()
```python
async def fetch_government_data(
    self,
    data_source: str,
    days: int = 252,
    use_cache: bool = True,
    timeout: int = 30
) -> pd.DataFrame:
    """
    获取特定政府数据源
    
    Parameters:
    -----------
    data_source : str
        数据源代码 (详见下文)
    days : int, default 252
        获取天数
    use_cache : bool, default True
        是否使用缓存
    timeout : int, default 30
        请求超时时间(秒)
    
    Returns:
    --------
    pd.DataFrame
        政府数据
    
    Raises:
    -------
    DataFetchError: 数据获取失败
    InvalidDataSourceError: 无效的数据源
    """
```

**支持的政府数据源:**
```python
GOVERNMENT_DATA_SOURCES = {
    'hibor': {
        'name': 'HIBOR利率数据',
        'description': '香港银行同业拆借利率',
        'priority': 'highest',
        'update_frequency': 'daily',
        'url': 'https://api.hkma.gov.hk/public/market-data-and-statistics/monthly-statistical-bulletin/er/ir-er-dhk-daily-ihb'
    },
    'monetary_base': {
        'name': '货币基础数据',
        'description': '香港货币基础统计',
        'priority': 'high',
        'update_frequency': 'daily',
        'url': 'https://api.hkma.gov.hk/public/market-data-and-statistics/monthly-statistical-bulletin/mo/mo-dm-mb'
    },
    'exchange_rate': {
        'name': '汇率数据',
        'description': '港币汇率',
        'priority': 'high',
        'update_frequency': 'daily',
        'url': 'https://api.hkma.gov.hk/public/market-data-and-statistics/monthly-statistical-bulletin/er/ir-er-dhk-daily-ex'
    },
    'liquidity': {
        'name': '银行同业流动资金',
        'description': '银行体系流动资金',
        'priority': 'medium',
        'update_frequency': 'daily',
        'url': 'https://api.hkma.gov.hk/public/market-data-and-statistics/daily-monetary-statistics/daily-figures-interbank-liquidity'
    },
    'efbn': {
        'name': '外汇基金票据及债券',
        'description': 'EFBN indicative price',
        'priority': 'medium',
        'update_frequency': 'daily',
        'url': 'https://api.hkma.gov.hk/public/market-data-and-statistics/daily-monetary-statistics/efbn-indicative-price'
    },
    'rmb_liquidity': {
        'name': '人民币流动资金',
        'description': '人民币流动性安排',
        'priority': 'low',
        'update_frequency': 'daily',
        'url': 'https://api.hkma.gov.hk/public/market-data-and-statistics/daily-monetary-statistics/usage-rmb-liquidity-fac'
    }
}
```

**示例用法:**
```python
import asyncio
from enhanced_nonprice_ta_system import EnhancedDataManager

async def fetch_gov_example():
    data_manager = EnhancedDataManager()
    
    # 获取HIBOR数据
    hibor_data = await data_manager.fetch_government_data('hibor', 365)
    print(f"HIBOR数据: {len(hibor_data)} 条记录")
    print(f"最新隔夜利率: {hibor_data['overnight'].iloc[-1]:.3f}%")
    
    # 获取货币基础数据
    monetary_data = await data_manager.fetch_government_data('monetary_base', 365)
    print(f"货币基础: {len(monetary_data)} 条记录")
    print(f"最新货币基础: {monetary_data['monetary_base'].iloc[-1]:,.0f} HKD")
    
    # 获取汇率数据
    exchange_data = await data_manager.fetch_government_data('exchange_rate', 365)
    print(f"汇率数据: {len(exchange_data)} 条记录")
    print(f"最新USD/HKD: {exchange_data['usd_hkd'].iloc[-1]:.4f}")

# 运行示例
asyncio.run(fetch_gov_example())
```

#### fetch_all_government_data()
```python
async def fetch_all_government_data(
    self,
    days: int = 252,
    priority_sources: Optional[List[str]] = None,
    fallback_enabled: bool = True,
    parallel: bool = True
) -> Dict[str, pd.DataFrame]:
    """
    获取所有政府数据源
    
    Parameters:
    -----------
    days : int, default 252
        获取天数
    priority_sources : list[str], optional
        优先获取的数据源列表
    fallback_enabled : bool, default True
        是否启用后备机制
    parallel : bool, default True
        是否并行获取
    
    Returns:
    --------
    dict[str, pd.DataFrame]
        所有政府数据的字典
    """
```

**示例用法:**
```python
async def fetch_all_gov_data():
    data_manager = EnhancedDataManager()
    
    # 设置优先数据源
    priority_sources = ['hibor', 'monetary_base', 'exchange_rate']
    
    # 获取所有数据
    all_gov_data = await data_manager.fetch_all_government_data(
        days=365,
        priority_sources=priority_sources,
        parallel=True
    )
    
    # 统计获取结果
    print("政府数据获取结果:")
    for source, data in all_gov_data.items():
        status = "✅" if not data.empty else "❌"
        print(f"{status} {source}: {len(data)} 条记录")
    
    return all_gov_data

# 执行并获取数据
gov_data = asyncio.run(fetch_all_gov_data())
```

#### get_latest_government_data()
```python
async def get_latest_government_data(
    self,
    sources: Optional[List[str]] = None
) -> Dict[str, Dict[str, Any]]:
    """
    获取最新的政府数据
    
    Parameters:
    -----------
    sources : list[str], optional
        指定数据源，默认获取所有源
    
    Returns:
    --------
    dict[str, dict]
        最新数据字典
    """
```

**示例用法:**
```python
async def get_latest_data():
    data_manager = EnhancedDataManager()
    
    # 获取最新关键数据
    latest_data = await data_manager.get_latest_government_data([
        'hibor', 'monetary_base', 'exchange_rate'
    ])
    
    print("最新经济指标:")
    for source, data in latest_data.items():
        print(f"\\n{source}:")
        for key, value in data.items():
            print(f"  {key}: {value}")

asyncio.run(get_latest_data())
```

### 3. 数据预处理和对齐

#### align_data_sources()
```python
def align_data_sources(
    self,
    stock_data: pd.DataFrame,
    gov_data: Dict[str, pd.DataFrame],
    method: str = 'forward_fill',
    interpolation: str = 'linear'
) -> AlignedData:
    """
    对齐多个数据源
    
    Parameters:
    -----------
    stock_data : pd.DataFrame
        股票数据
    gov_data : dict
        政府数据字典
    method : str, default 'forward_fill'
        数据对齐方法 ('forward_fill', 'backward_fill', 'interpolate')
    interpolation : str, default 'linear'
        插值方法 ('linear', 'polynomial', 'spline')
    
    Returns:
    --------
    AlignedData
        对齐后的数据对象
    """
```

**示例用法:**
```python
# 对齐数据源
aligned_data = data_manager.align_data_sources(
    stock_data=tencent_data,
    gov_data=gov_data,
    method='forward_fill'
)

# 查看对齐结果
print(f"对齐后数据范围: {aligned_data.start_date} 到 {aligned_data.end_date}")
print(f"总记录数: {len(aligned_data.merged_data)}")

# 查看数据完整性
completeness = aligned_data.completeness_report
print("\\n数据完整性报告:")
for source, info in completeness.items():
    print(f"{source}: {info['completeness']:.1%} 完整")
    print(f"  缺失: {info['missing_count']} 条")
    print(f"  方法: {info['fill_method']}")
```

#### calculate_derived_indicators()
```python
def calculate_derived_indicators(
    self,
    aligned_data: AlignedData,
    indicators: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    计算衍生指标
    
    Parameters:
    -----------
    aligned_data : AlignedData
        对齐后的数据
    indicators : list[str], optional
        要计算的指标列表
    
    Returns:
    --------
    pd.DataFrame
        包含衍生指标的数据
    """
```

**支持的衍生指标:**
```python
DERIVED_INDICATORS = {
    'hibor_change': 'HIBOR变化率',
    'monetary_base_growth': '货币基础增长率',
    'exchange_rate_volatility': '汇率波动率',
    'liquidity_index': '流动性指数',
    'economic_momentum': '经济动量指标',
    'interest_rate_spread': '利率差',
    'inflation_indicator': '通胀指标',
    'credit_condition': '信贷条件指标'
}
```

**示例用法:**
```python
# 计算衍生指标
derived_data = data_manager.calculate_derived_indicators(
    aligned_data,
    indicators=['hibor_change', 'monetary_base_growth', 'liquidity_index']
)

# 查看衍生指标
print("衍生指标:")
for col in derived_data.columns:
    if col not in aligned_data.merged_data.columns:
        latest_value = derived_data[col].iloc[-1]
        print(f"{col}: {latest_value:.4f}")
```

### 4. 缓存和性能管理

#### get_cache_status()
```python
def get_cache_status(self) -> CacheStatus:
    """
    获取缓存状态
    
    Returns:
    --------
    CacheStatus
        缓存状态信息
    """
```

**示例用法:**
```python
# 查看缓存状态
cache_status = data_manager.get_cache_status()

print("缓存状态:")
print(f"内存缓存大小: {cache_status.memory_cache_size_mb:.1f} MB")
print(f"磁盘缓存大小: {cache_status.disk_cache_size_mb:.1f} MB")
print(f"内存缓存命中率: {cache_status.memory_hit_rate:.1%}")
print(f"磁盘缓存命中率: {cache_status.disk_hit_rate:.1%}")

# 查看各数据源的缓存情况
for source, info in cache_status.source_cache_info.items():
    print(f"{source}: {info['entries']} 条记录，更新于 {info['last_update']}")
```

#### clear_cache()
```python
def clear_cache(
    self,
    data_sources: Optional[List[str]] = None,
    older_than: Optional[int] = None
) -> int:
    """
    清理缓存
    
    Parameters:
    -----------
    data_sources : list[str], optional
        要清理的数据源，默认清理所有
    older_than : int, optional
        清理多少小时前的数据
    
    Returns:
    --------
    int
        清理的条目数
    """
```

**示例用法:**
```python
# 清理特定数据源的缓存
cleared_count = data_manager.clear_cache(data_sources=['hibor', 'monetary_base'])
print(f"清理了 {cleared_count} 条缓存记录")

# 清理24小时前的所有缓存
old_count = data_manager.clear_cache(older_than=24)
print(f"清理了 {old_count} 条过期缓存")
```

### 5. 数据质量监控

#### get_data_quality_report()
```python
def get_data_quality_report(
    self,
    include_stocks: bool = True,
    include_government: bool = True,
    period_days: int = 30
) -> DataQualityReport:
    """
    获取数据质量报告
    
    Parameters:
    -----------
    include_stocks : bool, default True
        包括股票数据
    include_government : bool, default True
        包括政府数据
    period_days : int, default 30
        分析周期(天)
    
    Returns:
    --------
    DataQualityReport
        数据质量报告
    """
```

**示例用法:**
```python
# 获取数据质量报告
quality_report = data_manager.get_data_quality_report()

print("数据质量报告:")
print(f"总体评分: {quality_report.overall_score:.1f}/10")
print(f"股票数据质量: {quality_report.stock_quality:.1f}/10")
print(f"政府数据质量: {quality_report.gov_quality:.1f}/10")

# 查看问题和建议
if quality_report.issues:
    print("\\n发现的问题:")
    for issue in quality_report.issues:
        print(f"- {issue}")

if quality_report.recommendations:
    print("\\n改进建议:")
    for rec in quality_report.recommendations:
        print(f"- {rec}")
```

## 📊 数据对象

### AlignedData
```python
@dataclass
class AlignedData:
    """对齐数据对象"""
    merged_data: pd.DataFrame
    start_date: str
    end_date: str
    total_records: int
    completeness_report: Dict[str, Any]
    alignment_method: str
    original_sources: Dict[str, pd.DataFrame]
```

### DataValidationReport
```python
@dataclass
class DataValidationReport:
    """数据验证报告"""
    is_valid: bool
    issues: List[str]
    warnings: List[str]
    statistics: Dict[str, Any]
    validation_time: datetime
    data_source: str
```

### CacheStatus
```python
@dataclass
class CacheStatus:
    """缓存状态"""
    memory_cache_size_mb: float
    disk_cache_size_mb: float
    memory_hit_rate: float
    disk_hit_rate: float
    total_entries: int
    source_cache_info: Dict[str, Dict[str, Any]]
```

## ⚙️ 配置参数

### 数据管理器配置
```python
DATA_MANAGER_CONFIG = {
    # 股票数据配置
    'stock_data': {
        'default_days': 365,
        'max_days': 3650,  # 最大10年
        'cache_ttl_hours': 24,
        'validation_enabled': True,
        'strict_validation': False
    },
    
    # 政府数据配置
    'government_data': {
        'default_days': 252,
        'max_retries': 3,
        'timeout_seconds': 30,
        'parallel_requests': True,
        'cache_ttl_hours': 168,  # 7天
        'fallback_enabled': True
    },
    
    # 数据质量配置
    'data_quality': {
        'min_data_points': 100,
        'max_price_change_pct': 50,  # 单日最大价格变化
        'max_volume_change_pct': 1000,  # 单日最大成交量变化
        'gap_tolerance_days': 5,
        'outlier_detection': True
    },
    
    # 性能配置
    'performance': {
        'max_concurrent_requests': 8,
        'batch_size': 1000,
        'memory_limit_mb': 2048,
        'enable_compression': True
    }
}
```

## 🚨 错误处理

### 错误类型
```python
class DataFetchError(Exception):
    """数据获取错误"""
    pass

class DataValidationError(Exception):
    """数据验证错误"""
    pass

class InvalidDataSourceError(Exception):
    """无效数据源错误"""
    pass

class CacheError(Exception):
    """缓存错误"""
    pass

class DataAlignmentError(Exception):
    """数据对齐错误"""
    pass
```

### 错误处理示例
```python
try:
    # 获取股票数据
    stock_data = data_manager.fetch_stock_data("0700.hk", 365)
except DataFetchError as e:
    print(f"股票数据获取失败: {e}")
    # 尝试使用备用数据源
    stock_data = data_manager.fetch_stock_data("0700.hk", 365, use_cache=True)

try:
    # 获取政府数据
    gov_data = await data_manager.fetch_government_data('hibor', 365)
except InvalidDataSourceError as e:
    print(f"无效数据源: {e}")
    # 使用默认数据源
    gov_data = await data_manager.fetch_government_data('monetary_base', 365)
```

## 📚 相关API
- [CoreOptimizerEngine API](core_optimizer_api.md) - 核心优化引擎
- [EnhancedIndicatorEngine API](indicator_engine_api.md) - 指标计算
- [IntelligentCache API](cache_system_api.md) - 缓存系统
- [PerformanceMonitor API](performance_monitor_api.md) - 性能监控

---

**🚀 EnhancedDataManager为您提供可靠、高效的数据管理服务！**