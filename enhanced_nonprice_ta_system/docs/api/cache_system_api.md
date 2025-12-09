# IntelligentCache API - 智能缓存系统

## 📖 概述

`IntelligentCache`提供多级缓存架构，包括L1内存缓存和L2磁盘缓存，支持智能淘汰策略、压缩存储和统计报告，显著提升系统性能。

## 🏗️ 类结构

```python
class IntelligentCache:
    """智能多级缓存系统"""
    
    def __init__(
        self,
        memory_limit_mb: int = 1024,
        disk_limit_gb: float = 10.0,
        compression_enabled: bool = True,
        eviction_policy: str = 'lru'
    ):
        """初始化缓存系统"""
```

## 🏛️ 缓存架构

```
IntelligentCache Architecture
┌─────────────────────────────────────┐
│           Application Layer         │
├─────────────────────────────────────┤
│          L1 Memory Cache            │  ← 快速访问
│  - Redis-style in-memory storage   │  - <1ms 访问时间
│  - LRU eviction policy             │  - 1GB 默认限制
│  - Hot data storage                │  - 高命中率
├─────────────────────────────────────┤
│          L2 Disk Cache              │  ← 持久化存储
│  - File-based persistence          │  - ~10ms 访问时间
│  - Compressed storage              │  - 10GB 默认限制
│  - Warm data storage               │  - 跨会话持久
├─────────────────────────────────────┤
│        External Data Sources        │  ← 原始数据源
│  - Stock APIs                      │  - 100ms+ 延迟
│  - Government APIs                 │  - 网络依赖
│  - Database connections            │  - 费用敏感
└─────────────────────────────────────┘
```

## 🚀 核心方法

### 1. 缓存基本操作

#### get()
```python
def get(
    self,
    key: str,
    default: Any = None,
    tier: Optional[str] = None
) -> Any:
    """
    获取缓存数据
    
    Parameters:
    -----------
    key : str
        缓存键
    default : any, optional
        默认值
    tier : str, optional
        指定缓存层级 ('memory', 'disk')
    
    Returns:
    --------
    any
        缓存数据或默认值
    
    Example:
    --------
    # 从缓存获取数据 (自动查找L1和L2)
    data = cache.get("0700.hk_365days")
    
    # 只从内存缓存获取
    data = cache.get("0700.hk_365days", tier="memory")
    
    # 使用默认值
    data = cache.get("missing_key", default={"empty": True})
    """
```

#### set()
```python
def set(
    self,
    key: str,
    value: Any,
    ttl: Optional[int] = None,
    tier: str = 'auto',
    compress: bool = True
) -> bool:
    """
    设置缓存数据
    
    Parameters:
    -----------
    key : str
        缓存键
    value : any
        缓存值
    ttl : int, optional
        生存时间(秒)，None表示永不过期
    tier : str, default 'auto'
        存储层级 ('memory', 'disk', 'auto')
    compress : bool, default True
        是否压缩存储
    
    Returns:
    --------
    bool
        设置是否成功
    
    Example:
    --------
    # 自动选择存储层级
    cache.set("tencent_data", stock_data, ttl=3600)
    
    # 强制存储到内存
    cache.set("hot_data", calculation_result, tier="memory")
    
    # 存储到磁盘并设置TTL
    cache.set("large_dataset", big_data, ttl=86400, tier="disk")
    """
```

#### delete()
```python
def delete(self, key: str) -> bool:
    """
    删除缓存数据
    
    Parameters:
    -----------
    key : str
        缓存键
    
    Returns:
    --------
    bool
        删除是否成功
    
    Example:
    --------
    cache.delete("0700.hk_365days")
    """
```

### 2. 批量操作

#### mget()
```python
def mget(
    self,
    keys: List[str],
    default: Any = None
) -> Dict[str, Any]:
    """
    批量获取缓存数据
    
    Parameters:
    -----------
    keys : list[str]
        缓存键列表
    default : any, optional
        默认值
    
    Returns:
    --------
    dict
        键值对字典
    
    Example:
    --------
    keys = ["0700.hk", "0941.hk", "1398.hk"]
    stock_data_dict = cache.mget(keys)
    
    for symbol, data in stock_data_dict.items():
        if data is not None:
            print(f"{symbol}: {len(data)} records")
    """
```

#### mset()
```python
def mset(
    self,
    mapping: Dict[str, Any],
    ttl: Optional[int] = None,
    tier: str = 'auto'
) -> int:
    """
    批量设置缓存数据
    
    Parameters:
    -----------
    mapping : dict
        键值对字典
    ttl : int, optional
        生存时间
    tier : str, default 'auto'
        存储层级
    
    Returns:
    --------
    int
        成功设置的数量
    
    Example:
    --------
    data_batch = {
        "0700.hk": tencent_data,
        "0941.hk": china_mobile_data,
        "1398.hk": icbc_data
    }
    count = cache.mset(data_batch, ttl=3600)
    print(f"成功缓存 {count} 个股票数据")
    """
```

### 3. 缓存装饰器

#### cached()
```python
def cached(
    self,
    key_prefix: str = "",
    ttl: Optional[int] = None,
    tier: str = 'auto',
    key_generator: Optional[Callable] = None
):
    """
    缓存装饰器
    
    Parameters:
    -----------
    key_prefix : str, default ""
        键前缀
    ttl : int, optional
        生存时间
    tier : str, default 'auto'
        存储层级
    key_generator : callable, optional
        自定义键生成器
    
    Example:
    --------
    @cache.cached("calculate_rsi", ttl=3600)
    def calculate_rsi(prices, period=14):
        # 复杂的RSI计算
        return rsi_values
    
    # 使用自定义键生成器
    @cache.cached(key_generator=lambda f, *args, **kwargs: f"rsi_{len(args[0])}_{args[1]}")
    def custom_rsi(data, period):
        pass
    """
```

**装饰器使用示例:**
```python
# 缓存指标计算
@cache.cached("indicator_rsi", ttl=1800)  # 30分钟
def calculate_rsi_with_cache(prices: pd.Series, period: int = 14) -> pd.Series:
    """带缓存的RSI计算"""
    # 模拟复杂计算
    time.sleep(0.1)  # 模拟计算时间
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# 缓存数据获取
@cache.cached("stock_data", ttl=3600)  # 1小时
def get_stock_data_with_cache(symbol: str, days: int) -> pd.DataFrame:
    """带缓存的股票数据获取"""
    # 模拟API调用
    time.sleep(0.5)  # 模拟网络延迟
    return pd.DataFrame()  # 实际数据获取逻辑

# 使用示例
import time

# 第一次调用 - 执行计算并缓存
start = time.time()
rsi1 = calculate_rsi_with_cache(tencent_data['close'], 14)
first_call_time = time.time() - start

# 第二次调用 - 从缓存获取
start = time.time()
rsi2 = calculate_rsi_with_cache(tencent_data['close'], 14)
second_call_time = time.time() - start

print(f"第一次调用时间: {first_call_time:.3f}秒")
print(f"第二次调用时间: {second_call_time:.3f}秒")
print(f"性能提升: {first_call_time/second_call_time:.1f}x")
```

### 4. 缓存统计和监控

#### get_stats()
```python
def get_stats(self, detailed: bool = False) -> CacheStats:
    """
    获取缓存统计信息
    
    Parameters:
    -----------
    detailed : bool, default False
        是否获取详细信息
    
    Returns:
    --------
    CacheStats
        缓存统计对象
    
    Example:
    --------
    stats = cache.get_stats(detailed=True)
    
    print(f"内存缓存: {stats.memory_usage_mb:.1f}MB")
    print(f"磁盘缓存: {stats.disk_usage_gb:.1f}GB")
    print(f"总命中率: {stats.overall_hit_rate:.1%}")
    print(f"内存命中率: {stats.memory_hit_rate:.1%}")
    print(f"磁盘命中率: {stats.disk_hit_rate:.1%}")
    """
```

**示例用法:**
```python
# 获取缓存统计
stats = cache.get_stats(detailed=True)

print("📊 缓存统计报告:")
print(f"=" * 50)
print(f"🧠 内存缓存:")
print(f"  使用量: {stats.memory_usage_mb:.1f}MB / {stats.memory_limit_mb:.1f}MB")
print(f"  命中率: {stats.memory_hit_rate:.1%}")
print(f"  项目数: {stats.memory_items:,}")
print(f"  命中次数: {stats.memory_hits:,}")
print(f"  未命中次数: {stats.memory_misses:,}")

print(f"\\n💾 磁盘缓存:")
print(f"  使用量: {stats.disk_usage_gb:.2f}GB / {stats.disk_limit_gb:.1f}GB")
print(f"  命中率: {stats.disk_hit_rate:.1%}")
print(f"  项目数: {stats.disk_items:,}")
print(f"  命中次数: {stats.disk_hits:,}")
print(f"  未命中次数: {stats.disk_misses:,}")

print(f"\\n🎯 总体性能:")
print(f"  总命中率: {stats.overall_hit_rate:.1%}")
print(f"  总请求次数: {stats.total_requests:,}")
print(f"  总命中次数: {stats.total_hits:,}")
print(f"  平均访问时间: {stats.avg_access_time_ms:.2f}ms")

if detailed:
    print(f"\\n📈 详细统计:")
    print(f"  淘汰次数: {stats.evictions:,}")
    print(f"  压缩率: {stats.compression_ratio:.1%}")
    print(f"  最热键: {stats.hottest_key}")
    print(f"  最大值: {stats.largest_item_size_mb:.1f}MB")

# 获取历史趋势
if stats.history:
    print(f"\\n📉 命中率趋势 (最近10次):")
    for i, hit_rate in enumerate(stats.history[-10:], 1):
        print(f"  第{i}次: {hit_rate:.1%}")
```

#### get_hot_keys()
```python
def get_hot_keys(
    self,
    limit: int = 10,
    min_access_count: int = 5
) -> List[HotKeyInfo]:
    """
    获取热点键
    
    Parameters:
    -----------
    limit : int, default 10
        返回数量限制
    min_access_count : int, default 5
        最小访问次数
    
    Returns:
    --------
    list[HotKeyInfo]
        热点键信息列表
    
    Example:
    --------
    hot_keys = cache.get_hot_keys(limit=5)
    for key_info in hot_keys:
        print(f"{key_info.key}: {key_info.access_count} 次, "
              f"{key_info.last_access}")
    """
```

**示例用法:**
```python
# 获取热点键分析
hot_keys = cache.get_hot_keys(limit=5)

print("🔥 热点键分析:")
for i, key_info in enumerate(hot_keys, 1):
    print(f"{i}. {key_info.key}")
    print(f"   访问次数: {key_info.access_count:,}")
    print(f"   大小: {key_info.size_mb:.2f}MB")
    print(f"   命中率: {key_info.hit_rate:.1%}")
    print(f"   最后访问: {key_info.last_access}")
    print(f"   存储层级: {key_info.tier}")
    print()
```

### 5. 缓存管理和维护

#### clear()
```python
def clear(
    self,
    tier: Optional[str] = None,
    pattern: Optional[str] = None,
    older_than: Optional[int] = None
) -> int:
    """
    清理缓存
    
    Parameters:
    -----------
    tier : str, optional
        指定层级 ('memory', 'disk')
    pattern : str, optional
        键模式 (支持通配符)
    older_than : int, optional
        清理多少秒前的数据
    
    Returns:
    --------
    int
        清理的项目数
    
    Example:
    --------
    # 清理所有缓存
    count = cache.clear()
    
    # 只清理内存缓存
    count = cache.clear(tier="memory")
    
    # 清理匹配模式的键
    count = cache.clear(pattern="*_temp_*")
    
    # 清理过期数据
    count = cache.clear(older_than=3600)  # 1小时前
    """
```

**示例用法:**
```python
# 清理不同类型的缓存
print("🧹 缓存清理操作:")

# 清理临时数据
temp_count = cache.clear(pattern="*_temp_*")
print(f"清理临时数据: {temp_count} 项")

# 清理过期的股票数据
old_stock_count = cache.clear(pattern="stock_data_*", older_than=86400)
print(f"清理过期股票数据: {old_stock_count} 项")

# 清理内存缓存以释放内存
memory_count = cache.clear(tier="memory")
print(f"清理内存缓存: {memory_count} 项")

# 清理所有缓存
total_count = cache.clear()
print(f"清理所有缓存: {total_count} 项")
```

#### optimize()
```python
def optimize(self) -> OptimizationReport:
    """
    优化缓存性能
    
    Returns:
    --------
    OptimizationReport
        优化报告
    
    Example:
    --------
    report = cache.optimize()
    print(f"优化后释放空间: {report.freed_space_mb:.1f}MB")
    print(f"性能提升: {report.performance_improvement:.1%}")
    """
```

**示例用法:**
```python
# 执行缓存优化
print("⚡ 开始缓存优化...")
start_time = time.time()

optimization_report = cache.optimize()

end_time = time.time()

print("✅ 缓存优化完成:")
print(f"优化耗时: {end_time - start_time:.2f}秒")
print(f"释放空间: {optimization_report.freed_space_mb:.1f}MB")
print(f"压缩项目: {optimization_report.compressed_items:,} 个")
print(f"移动项目: {optimization_report.moved_items:,} 个")
print(f"性能提升: {optimization_report.performance_improvement:.1%}")

if optimization_report.recommendations:
    print("\\n💡 优化建议:")
    for rec in optimization_report.recommendations:
        print(f"  - {rec}")
```

### 6. 缓存预热

#### warmup()
```python
def warmup(
    self,
    data_sources: List[str],
    keys: Optional[List[str]] = None,
    parallel: bool = True
) -> WarmupReport:
    """
    缓存预热
    
    Parameters:
    -----------
    data_sources : list[str]
        数据源列表
    keys : list[str], optional
        预热键列表
    parallel : bool, default True
        是否并行预热
    
    Returns:
    --------
    WarmupReport
        预热报告
    
    Example:
    --------
    # 预热股票数据
    report = cache.warmup(["stock_data"], ["0700.hk", "0941.hk"])
    
    # 预热所有数据源
    report = cache.warmup(["all"])
    """
```

**示例用法:**
```python
# 缓存预热
print("🔥 开始缓存预热...")

# 定义预热数据
warmup_keys = [
    "stock_data_0700.hk_365",
    "stock_data_0941.hk_365", 
    "stock_data_1398.hk_365",
    "government_hibor_365",
    "government_monetary_base_365"
]

# 执行预热
warmup_report = cache.warmup(
    data_sources=["stock_data", "government_data"],
    keys=warmup_keys,
    parallel=True
)

print("✅ 预热完成:")
print(f"成功预热: {warmup_report.success_count}/{warmup_report.total_count}")
print(f"预热耗时: {warmup_report.duration_seconds:.2f}秒")
print(f"预热数据量: {warmup_report.total_size_mb:.1f}MB")

if warmup_report.failed_keys:
    print("\\n⚠️ 预热失败的键:")
    for failed_key in warmup_report.failed_keys:
        print(f"  - {failed_key}")
```

## 📊 缓存对象

### CacheStats
```python
@dataclass
class CacheStats:
    """缓存统计信息"""
    # 内存统计
    memory_usage_mb: float
    memory_limit_mb: float
    memory_items: int
    memory_hits: int
    memory_misses: int
    memory_hit_rate: float
    
    # 磁盘统计
    disk_usage_gb: float
    disk_limit_gb: float
    disk_items: int
    disk_hits: int
    disk_misses: int
    disk_hit_rate: float
    
    # 总体统计
    total_requests: int
    total_hits: int
    overall_hit_rate: float
    avg_access_time_ms: float
    
    # 详细统计
    evictions: int
    compression_ratio: float
    hottest_key: Optional[str]
    largest_item_size_mb: float
    
    # 历史数据
    history: List[float]
```

### HotKeyInfo
```python
@dataclass
class HotKeyInfo:
    """热点键信息"""
    key: str
    access_count: int
    hit_rate: float
    size_mb: float
    last_access: datetime
    tier: str
    created_at: datetime
```

## ⚙️ 配置参数

### 缓存配置
```python
CACHE_CONFIG = {
    # 内存缓存配置
    'memory_cache': {
        'limit_mb': 1024,          # 1GB内存限制
        'max_items': 10000,        # 最大项目数
        'eviction_policy': 'lru',  # LRU淘汰策略
        'cleanup_interval': 300,   # 5分钟清理间隔
        'compression_threshold': 10240  # 10KB以上压缩
    },
    
    # 磁盘缓存配置
    'disk_cache': {
        'limit_gb': 10.0,          # 10GB磁盘限制
        'directory': './cache',    # 缓存目录
        'compression': True,       # 启用压缩
        'encryption': False,       # 禁用加密
        'cleanup_interval': 3600   # 1小时清理间隔
    },
    
    # 性能配置
    'performance': {
        'batch_size': 1000,        # 批处理大小
        'parallel_workers': 4,     # 并行工作线程
        'async_operations': True,  # 启用异步操作
        'preload_enabled': True    # 启用预加载
    },
    
    # 监控配置
    'monitoring': {
        'stats_enabled': True,     # 启用统计
        'history_size': 1000,      # 历史记录大小
        'hot_keys_limit': 100,     # 热点键限制
        'performance_logging': True # 启用性能日志
    }
}
```

## 🚨 错误处理

### 错误类型
```python
class CacheError(Exception):
    """缓存基础异常"""
    pass

class MemoryCacheError(CacheError):
    """内存缓存错误"""
    pass

class DiskCacheError(CacheError):
    """磁盘缓存错误"""
    pass

class CacheFullError(CacheError):
    """缓存已满错误"""
    pass

class CacheKeyError(CacheError):
    """缓存键错误"""
    pass
```

### 错误处理示例
```python
try:
    # 设置大缓存项
    cache.set("large_data", big_data, ttl=3600)
except CacheFullError:
    print("缓存已满，尝试清理旧数据")
    cache.clear(older_than=3600)
    cache.set("large_data", big_data, ttl=3600)
except DiskCacheError as e:
    print(f"磁盘缓存错误: {e}")
    # 降级到内存缓存
    cache.set("large_data", big_data, tier="memory", ttl=1800)
```

## 📈 性能基准

### 缓存性能对比
```python
# 性能测试示例
import time

def cache_performance_test():
    """缓存性能测试"""
    # 测试数据
    test_data = {"large_dataset": list(range(100000))}
    
    # 测试无缓存性能
    start = time.time()
    for _ in range(100):
        # 模拟复杂操作
        result = expensive_operation(test_data)
    no_cache_time = time.time() - start
    
    # 测试缓存性能
    @cache.cached("expensive_op", ttl=300)
    def cached_operation(data):
        return expensive_operation(data)
    
    start = time.time()
    for _ in range(100):
        result = cached_operation(test_data)
    cache_time = time.time() - start
    
    print(f"无缓存时间: {no_cache_time:.3f}秒")
    print(f"缓存时间: {cache_time:.3f}秒")
    print(f"性能提升: {no_cache_time/cache_time:.1f}x")

cache_performance_test()
```

### 缓存命中率分析
```python
def analyze_cache_performance():
    """分析缓存性能"""
    stats = cache.get_stats(detailed=True)
    
    # 命中率分析
    if stats.overall_hit_rate > 0.8:
        print("✅ 缓存性能优秀")
    elif stats.overall_hit_rate > 0.6:
        print("⚠️ 缓存性能良好")
    else:
        print("❌ 缓存性能需要优化")
    
    # 内存使用分析
    memory_usage_ratio = stats.memory_usage_mb / stats.memory_limit_mb
    if memory_usage_ratio > 0.9:
        print("⚠️ 内存缓存接近满载")
    elif memory_usage_ratio < 0.3:
        print("💡 内存缓存使用率较低，可考虑增加限制")
    
    # 磁盘使用分析
    disk_usage_ratio = stats.disk_usage_gb / stats.disk_limit_gb
    if disk_usage_ratio > 0.9:
        print("⚠️ 磁盘缓存接近满载")

analyze_cache_performance()
```

## 📚 相关API
- [CoreOptimizerEngine API](core_optimizer_api.md) - 核心优化引擎
- [EnhancedDataManager API](data_manager_api.md) - 数据管理
- [EnhancedIndicatorEngine API](indicator_engine_api.md) - 指标计算
- [PerformanceMonitor API](performance_monitor_api.md) - 性能监控

---

**🚀 IntelligentCache让您的系统性能飞跃提升！**