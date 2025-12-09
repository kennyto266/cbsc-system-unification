# EnhancedErrorHandler API - 错误处理系统

## 📖 概述

`EnhancedErrorHandler`提供智能错误分类、自动恢复机制、后备数据生成和系统健康评估，确保系统在各种异常情况下保持稳定运行。

## 🏗️ 类结构

```python
class EnhancedErrorHandler:
    """增强错误处理系统"""
    
    def __init__(
        self,
        retry_attempts: int = 3,
        fallback_enabled: bool = True,
        error_logging: bool = True,
        health_monitoring: bool = True
    ):
        """初始化错误处理器"""
```

## 🚀 核心方法

### 1. 错误捕获和处理

#### handle_error()
```python
def handle_error(
    self,
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    recovery_strategy: Optional[str] = None
) -> ErrorHandlingResult:
    """
    处理错误
    
    Parameters:
    -----------
    error : Exception
        异常对象
    context : dict, optional
        错误上下文信息
    recovery_strategy : str, optional
        恢复策略
    
    Returns:
    --------
    ErrorHandlingResult
        错误处理结果
    
    Example:
    --------
    try:
        result = risky_operation()
    except Exception as e:
        handling_result = error_handler.handle_error(
            e,
            context={'operation': 'data_fetch', 'symbol': '0700.hk'},
            recovery_strategy='retry_with_fallback'
        )
        
        if handling_result.recovered:
            result = handling_result.result
        else:
            logger.error(f"操作失败: {handling_result.message}")
    """
```

**示例用法:**
```python
from enhanced_nonprice_ta_system import EnhancedErrorHandler

# 创建错误处理器
error_handler = EnhancedErrorHandler(
    retry_attempts=3,
    fallback_enabled=True,
    error_logging=True
)

def safe_data_fetch(symbol: str, days: int):
    """安全的数据获取函数"""
    context = {
        'operation': 'fetch_stock_data',
        'symbol': symbol,
        'days': days,
        'timestamp': datetime.now().isoformat()
    }
    
    try:
        # 模拟可能失败的操作
        if symbol == "INVALID":
            raise ValueError(f"无效股票代码: {symbol}")
        
        # 模拟网络超时
        if np.random.random() < 0.1:  # 10%概率失败
            raise TimeoutError("网络请求超时")
        
        # 返回模拟数据
        return pd.DataFrame({
            'date': pd.date_range('2023-01-01', periods=days),
            'close': np.random.uniform(100, 500, days)
        }).set_index('date')
        
    except Exception as e:
        # 使用错误处理器
        result = error_handler.handle_error(
            error=e,
            context=context,
            recovery_strategy='auto'
        )
        
        if result.recovered:
            print(f"✅ 错误已恢复: {result.message}")
            return result.result
        else:
            print(f"❌ 错误处理失败: {result.message}")
            # 使用后备数据
            return error_handler.generate_fallback_data('stock', context)

# 测试错误处理
try:
    # 正常情况
    data = safe_data_fetch("0700.hk", 365)
    print(f"获取数据成功: {len(data)} 条记录")
    
    # 错误情况1 - 无效股票代码
    invalid_data = safe_data_fetch("INVALID", 365)
    print(f"后备数据: {len(invalid_data)} 条记录")
    
    # 错误情况2 - 网络超时
    for i in range(5):
        timeout_data = safe_data_fetch("0388.hk", 365)
        print(f"第{i+1}次尝试: {'成功' if len(timeout_data) > 0 else '失败'}")
        
except Exception as e:
    print(f"未处理的异常: {e}")
```

#### classify_error()
```python
def classify_error(self, error: Exception) -> ErrorClassification:
    """
    分类错误
    
    Parameters:
    -----------
    error : Exception
        异常对象
    
    Returns:
    --------
    ErrorClassification
        错误分类结果
    
    Example:
    --------
    classification = error_handler.classify_error(error)
    
    print(f"错误类型: {classification.category}")
    print(f"严重程度: {classification.severity}")
    print(f"建议恢复策略: {classification.recommended_strategy}")
    """
```

**示例用法:**
```python
# 测试不同类型错误的分类
test_errors = [
    ValueError("无效参数"),
    TimeoutError("连接超时"),
    ConnectionError("网络连接失败"),
    MemoryError("内存不足"),
    FileNotFoundError("文件未找到"),
    KeyError("键不存在"),
    RuntimeError("运行时错误")
]

print("🔍 错误分类测试:")
for error in test_errors:
    classification = error_handler.classify_error(error)
    
    severity_icon = "🔴" if classification.severity == "critical" else "🟡" if classification.severity == "high" else "🟢"
    print(f"{severity_icon} {type(error).__name__}: {classification.category}")
    print(f"   严重程度: {classification.severity}")
    print(f"   恢复策略: {classification.recommended_strategy}")
    print(f"   预期成功率: {classification.expected_recovery_rate:.1%}")
    print(f"   影响范围: {classification.impact_scope}")
    print()
```

### 2. 自动恢复机制

#### auto_recovery()
```python
def auto_recovery(
    self,
    error: Exception,
    failed_operation: Callable,
    operation_args: tuple = (),
    operation_kwargs: dict = None,
    context: Optional[Dict[str, Any]] = None
) -> RecoveryResult:
    """
    自动恢复
    
    Parameters:
    -----------
    error : Exception
        发生的错误
    failed_operation : callable
        失败的操作
    operation_args : tuple, optional
        操作参数
    operation_kwargs : dict, optional
        操作关键字参数
    context : dict, optional
        操作上下文
    
    Returns:
    --------
    RecoveryResult
        恢复结果
    
    Example:
    --------
    def fetch_data():
        return api.get_data()
    
    recovery_result = error_handler.auto_recovery(
        error=TimeoutError("超时"),
        failed_operation=fetch_data,
        context={'component': 'data_fetcher'}
    )
    
    if recovery_result.success:
        data = recovery_result.result
    """
```

**示例用法:**
```python
import requests
import time

def unreliable_api_call(url: str, max_retries: int = 3):
    """不可靠的API调用，用于测试"""
    attempt = 0
    last_error = None
    
    while attempt < max_retries:
        attempt += 1
        try:
            # 模拟API调用
            if np.random.random() < 0.3:  # 30%概率失败
                raise requests.RequestException(f"模拟网络错误 (尝试 {attempt})")
            
            # 模拟成功响应
            time.sleep(np.random.uniform(0.1, 0.5))  # 模拟网络延迟
            return {"status": "success", "data": "sample_data", "attempt": attempt}
            
        except Exception as e:
            last_error = e
            if attempt < max_retries:
                wait_time = 2 ** attempt  # 指数退避
                print(f"第{attempt}次尝试失败，{wait_time}秒后重试: {e}")
                time.sleep(wait_time)
            else:
                raise e
    
    raise last_error

# 使用自动恢复机制
def api_call_with_recovery(url: str):
    """带自动恢复的API调用"""
    context = {
        'url': url,
        'timestamp': datetime.now().isoformat(),
        'component': 'api_client'
    }
    
    try:
        # 首次尝试
        return unreliable_api_call(url)
    except Exception as e:
        print(f"首次尝试失败: {e}")
        
        # 使用自动恢复
        recovery_result = error_handler.auto_recovery(
            error=e,
            failed_operation=unreliable_api_call,
            operation_args=(url,),
            context=context
        )
        
        if recovery_result.success:
            print(f"✅ 恢复成功: {recovery_result.message}")
            print(f"恢复尝试: {recovery_result.recovery_attempts}")
            print(f"总耗时: {recovery_result.total_time:.2f}秒")
            return recovery_result.result
        else:
            print(f"❌ 恢复失败: {recovery_result.message}")
            raise Exception("所有恢复尝试均失败")

# 测试自动恢复
print("🔄 自动恢复测试:")
test_urls = ["https://api.example.com/data1", "https://api.example.com/data2"]

for i, url in enumerate(test_urls, 1):
    try:
        print(f"\\n测试 {i}: {url}")
        result = api_call_with_recovery(url)
        print(f"API调用成功: {result}")
    except Exception as e:
        print(f"API调用失败: {e}")
```

#### circuit_breaker()
```python
def circuit_breaker(
    self,
    operation: Callable,
    failure_threshold: int = 5,
    timeout: int = 60,
    context: Optional[Dict[str, Any]] = None
) -> Callable:
    """
    熔断器装饰器
    
    Parameters:
    -----------
    operation : callable
        要保护的操作
    failure_threshold : int, default 5
        失败阈值
    timeout : int, default 60
        超时时间(秒)
    context : dict, optional
        上下文信息
    
    Returns:
    --------
    callable
        被装饰的函数
    
    Example:
    --------
    @error_handler.circuit_breaker(failure_threshold=3, timeout=30)
    def external_api_call():
        return api.get_data()
    """
```

**示例用法:**
```python
# 创建带熔断器的API客户端
class ExternalAPIClient:
    def __init__(self):
        self.call_count = 0
        self.failure_count = 0
    
    @error_handler.circuit_breaker(
        failure_threshold=3,  # 3次失败后熔断
        timeout=10,           # 10秒后重试
        context={'component': 'external_api'}
    )
    def fetch_data(self, endpoint: str):
        """带熔断器的数据获取"""
        self.call_count += 1
        
        # 模拟API调用
        if np.random.random() < 0.4:  # 40%失败率
            self.failure_count += 1
            raise ConnectionError(f"API连接失败 (调用 {self.call_count})")
        
        return {"data": f"sample_data_from_{endpoint}", "call": self.call_count}

# 测试熔断器
api_client = ExternalAPIClient()

print("🔌 熔断器测试:")
print("模拟连续API调用失败...")

for i in range(10):
    try:
        result = api_client.fetch_data(f"endpoint_{i}")
        print(f"✅ 调用 {i+1}: 成功 - {result}")
    except Exception as e:
        print(f"❌ 调用 {i+1}: 失败 - {e}")
    
    time.sleep(0.5)  # 短暂延迟

print(f"\\n统计:")
print(f"总调用次数: {api_client.call_count}")
print(f"失败次数: {api_client.failure_count}")
print(f"成功率: {(api_client.call_count - api_client.failure_count) / api_client.call_count:.1%}")
```

### 3. 后备数据生成

#### generate_fallback_data()
```python
def generate_fallback_data(
    self,
    data_type: str,
    context: Dict[str, Any],
    quality_level: str = 'medium'
) -> Any:
    """
    生成后备数据
    
    Parameters:
    -----------
    data_type : str
        数据类型 ('stock', 'government', 'indicator', etc.)
    context : dict
        数据上下文
    quality_level : str, default 'medium'
        数据质量级别 ('low', 'medium', 'high')
    
    Returns:
    --------
    any
        生成的后备数据
    
    Example:
    --------
    # 生成股票后备数据
    fallback_stock = error_handler.generate_fallback_data(
        data_type='stock',
        context={'symbol': '0700.hk', 'days': 365},
        quality_level='high'
    )
    """
```

**示例用法:**
```python
# 测试后备数据生成
print("📊 后备数据生成测试:")

# 生成股票后备数据
stock_context = {
    'symbol': '0700.hk',
    'days': 252,
    'start_date': '2023-01-01',
    'end_date': '2023-12-31'
}

fallback_stock_data = error_handler.generate_fallback_data(
    data_type='stock',
    context=stock_context,
    quality_level='high'
)

print(f"\\n股票后备数据:")
print(f"数据点数: {len(fallback_stock_data)}")
print(f"价格范围: {fallback_stock_data['close'].min():.2f} - {fallback_stock_data['close'].max():.2f}")
print(f"平均价格: {fallback_stock_data['close'].mean():.2f}")
print(f"数据质量: 高")

# 生成政府数据后备
gov_context = {
    'source': 'hibor',
    'days': 365,
    'start_date': '2023-01-01'
}

fallback_gov_data = error_handler.generate_fallback_data(
    data_type='government',
    context=gov_context,
    quality_level='medium'
)

print(f"\\n政府数据后备:")
for column in fallback_gov_data.columns:
    print(f"{column}: {len(fallback_gov_data[column])} 条记录")
    latest_value = fallback_gov_data[column].iloc[-1]
    print(f"  最新值: {latest_value:.4f}")

# 生成指标后备数据
indicator_context = {
    'indicator_type': 'RSI',
    'period': 14,
    'data_points': 252
}

fallback_indicator = error_handler.generate_fallback_data(
    data_type='indicator',
    context=indicator_context,
    quality_level='medium'
)

print(f"\\nRSI指标后备数据:")
print(f"数据点数: {len(fallback_indicator)}")
print(f"范围: {fallback_indicator.min():.2f} - {fallback_indicator.max():.2f}")
print(f"平均值: {fallback_indicator.mean():.2f}")
```

#### validate_fallback_data()
```python
def validate_fallback_data(
    self,
    data: Any,
    data_type: str,
    context: Dict[str, Any]
) -> ValidationReport:
    """
    验证后备数据质量
    
    Parameters:
    -----------
    data : any
        要验证的数据
    data_type : str
        数据类型
    context : dict
        数据上下文
    
    Returns:
    --------
    ValidationReport
        验证报告
    
    Example:
    --------
    report = error_handler.validate_fallback_data(
        fallback_data,
        'stock',
        {'symbol': '0700.hk'}
    )
    
    if report.is_valid:
        print("后备数据质量合格")
    else:
        print(f"数据质量问题: {report.issues}")
    """
```

**示例用法:**
```python
# 验证后备数据质量
validation_report = error_handler.validate_fallback_data(
    fallback_stock_data,
    'stock',
    stock_context
)

print(f"\\n🔍 后备数据验证:")
print(f"数据有效性: {'✅ 有效' if validation_report.is_valid else '❌ 无效'}")
print(f"质量评分: {validation_report.quality_score:.1f}/10")

if validation_report.warnings:
    print(f"\\n⚠️ 警告:")
    for warning in validation_report.warnings:
        print(f"  - {warning}")

if validation_report.issues:
    print(f"\\n❌ 问题:")
    for issue in validation_report.issues:
        print(f"  - {issue}")

# 数据质量详情
quality_metrics = validation_report.quality_metrics
print(f"\\n📊 质量指标:")
for metric, value in quality_metrics.items():
    print(f"  {metric}: {value}")
```

### 4. 系统健康监控

#### check_system_health()
```python
def check_system_health(
    self,
    components: Optional[List[str]] = None
) -> SystemHealthReport:
    """
    检查系统健康状态
    
    Parameters:
    -----------
    components : list[str], optional
        要检查的组件列表
    
    Returns:
    --------
    SystemHealthReport
        系统健康报告
    
    Example:
    --------
    health_report = error_handler.check_system_health(
        components=['data_manager', 'cache', 'optimizer']
    )
    
    print(f"总体健康评分: {health_report.overall_score:.1f}/10")
    """
```

**示例用法:**
```python
# 检查系统健康状态
health_report = error_handler.check_system_health()

print(f"🏥 系统健康检查报告:")
print(f"检查时间: {health_report.check_time}")
print(f"总体健康评分: {health_report.overall_score:.1f}/10")

# 健康等级
if health_report.overall_score >= 8:
    health_status = "🟢 优秀"
elif health_report.overall_score >= 6:
    health_status = "🟡 良好"
elif health_report.overall_score >= 4:
    health_status = "🟠 一般"
else:
    health_status = "🔴 需要关注"

print(f"健康状态: {health_status}")

# 组件健康详情
print(f"\\n🏗️ 组件健康详情:")
for component_name, component_health in health_report.component_health.items():
    status_icon = "✅" if component_health.is_healthy else "❌"
    print(f"{status_icon} {component_name}: {component_health.score:.1f}/10")
    
    if component_health.issues:
        for issue in component_health.issues:
            print(f"    ⚠️ {issue}")
    
    if component_health.metrics:
        for metric_name, metric_value in component_health.metrics.items():
            print(f"    📊 {metric_name}: {metric_value}")

# 健康建议
if health_report.recommendations:
    print(f"\\n💡 健康建议:")
    for rec in health_report.recommendations:
        print(f"  - {rec}")
```

#### get_error_statistics()
```python
def get_error_statistics(
    self,
    time_range: Optional[TimeRange] = None,
    category: Optional[str] = None
) -> ErrorStatistics:
    """
    获取错误统计信息
    
    Parameters:
    -----------
    time_range : TimeRange, optional
        统计时间范围
    category : str, optional
        错误类别过滤
    
    Returns:
    --------
    ErrorStatistics
        错误统计信息
    
    Example:
    --------
    stats = error_handler.get_error_statistics()
    
    print(f"总错误数: {stats.total_errors}")
    print(f"恢复成功率: {stats.recovery_success_rate:.1%}")
    """
```

**示例用法:**
```python
# 获取错误统计
error_stats = error_handler.get_error_statistics()

print(f"📈 错误统计报告:")
print(f"统计时间范围: {error_stats.time_range}")
print(f"总错误数: {error_stats.total_errors:,}")
print(f"错误分类: {len(error_stats.error_categories)} 种")

# 按类别统计
print(f"\\n📊 错误类别分布:")
for category, count in error_stats.error_categories.items():
    percentage = count / error_stats.total_errors * 100
    print(f"  {category}: {count} ({percentage:.1f}%)")

# 恢复统计
print(f"\\n🔄 恢复统计:")
print(f"恢复尝试: {error_stats.recovery_attempts:,}")
print(f"恢复成功: {error_stats.recovery_successes:,}")
print(f"恢复成功率: {error_stats.recovery_success_rate:.1%}")
print(f"平均恢复时间: {error_stats.avg_recovery_time_ms:.1f}ms")

# 严重程度分布
print(f"\\n⚠️ 严重程度分布:")
for severity, count in error_stats.severity_distribution.items():
    percentage = count / error_stats.total_errors * 100
    severity_icon = "🔴" if severity == "critical" else "🟡" if severity == "high" else "🟢"
    print(f"  {severity_icon} {severity}: {count} ({percentage:.1f}%)")

# 最近错误趋势
if error_stats.recent_trend:
    print(f"\\n📉 最近趋势:")
    print(f"趋势方向: {error_stats.recent_trend.direction}")
    print(f"变化率: {error_stats.recent_trend.change_rate:+.1%}")
    print(f"置信度: {error_stats.recent_trend.confidence:.1%}")
```

### 5. 错误报告和分析

#### generate_error_report()
```python
def generate_error_report(
    self,
    time_range: Optional[TimeRange] = None,
    format: str = 'html',
    include_recommendations: bool = True
) -> str:
    """
    生成错误分析报告
    
    Parameters:
    -----------
    time_range : TimeRange, optional
        报告时间范围
    format : str, default 'html'
        报告格式 ('html', 'pdf', 'json')
    include_recommendations : bool, default True
        是否包含改进建议
    
    Returns:
    --------
    str
        报告内容或文件路径
    
    Example:
    --------
    report_path = error_handler.generate_error_report(
        format='html',
        include_recommendations=True
    )
    """
```

**示例用法:**
```python
# 生成错误分析报告
from datetime import datetime, timedelta

end_time = datetime.now()
start_time = end_time - timedelta(hours=24)
time_range = TimeRange(start=start_time, end=end_time)

report_path = error_handler.generate_error_report(
    time_range=time_range,
    format='html',
    include_recommendations=True
)

print(f"📋 错误分析报告已生成: {report_path}")

# 获取JSON格式的摘要
json_summary = error_handler.generate_error_report(
    time_range=time_range,
    format='json',
    include_recommendations=True
)

# 解析摘要数据
import json
summary_data = json.loads(json_summary)

print(f"\\n📊 24小时错误摘要:")
print(f"总错误数: {summary_data['summary']['total_errors']}")
print(f"恢复成功率: {summary_data['summary']['recovery_success_rate']:.1%}")
print(f"最常见错误: {summary_data['summary']['most_common_error']}")
print(f"系统健康评分: {summary_data['summary']['health_score']:.1f}/10")

if summary_data['recommendations']:
    print(f"\\n💡 改进建议:")
    for rec in summary_data['recommendations'][:3]:  # 显示前3条建议
        print(f"  - {rec}")
```

## 📊 错误处理对象

### ErrorClassification
```python
@dataclass
class ErrorClassification:
    """错误分类"""
    category: str
    severity: str
    recommended_strategy: str
    expected_recovery_rate: float
    impact_scope: str
    auto_recovery_possible: bool
```

### RecoveryResult
```python
@dataclass
class RecoveryResult:
    """恢复结果"""
    success: bool
    result: Any
    recovery_attempts: int
    total_time: float
    strategy_used: str
    message: str
```

### SystemHealthReport
```python
@dataclass
class SystemHealthReport:
    """系统健康报告"""
    overall_score: float
    component_health: Dict[str, ComponentHealth]
    check_time: datetime
    recommendations: List[str]
    issues: List[str]
```

## ⚙️ 配置参数

### 错误处理配置
```python
ERROR_HANDLER_CONFIG = {
    # 基础配置
    'basic': {
        'retry_attempts': 3,          # 重试次数
        'retry_delay_seconds': 1,     # 重试延迟
        'fallback_enabled': True,     # 启用后备机制
        'error_logging': True,        # 启用错误日志
        'health_monitoring': True     # 启用健康监控
    },
    
    # 熔断器配置
    'circuit_breaker': {
        'failure_threshold': 5,       # 失败阈值
        'timeout_seconds': 60,        # 超时时间
        'half_open_max_calls': 3,     # 半开状态最大调用数
        'success_threshold': 2        # 成功阈值
    },
    
    # 后备数据配置
    'fallback_data': {
        'quality_level': 'medium',    # 默认质量级别
        'cache_fallback_data': True,  # 缓存后备数据
        'validate_fallback': True,    # 验证后备数据
        'max_fallback_age_hours': 24  # 后备数据最大年龄
    },
    
    # 健康监控配置
    'health_monitoring': {
        'check_interval_seconds': 60,  # 检查间隔
        'component_timeout': 10,       # 组件检查超时
        'health_threshold': 0.8,       # 健康阈值
        'alert_on_failure': True       # 失败时警报
    }
}
```

## 🚨 错误处理策略

### 错误类别和恢复策略
```python
ERROR_RECOVERY_STRATEGIES = {
    # 网络相关错误
    'network_errors': {
        'retry_with_backoff': '指数退避重试',
        'switch_endpoint': '切换端点',
        'use_cache': '使用缓存数据',
        'fallback_data': '生成后备数据'
    },
    
    # 数据相关错误
    'data_errors': {
        'validate_and_clean': '验证和清理数据',
        'use_alternative_source': '使用备用数据源',
        'interpolate_missing': '插值填充缺失数据',
        'generate_synthetic': '生成合成数据'
    },
    
    # 计算相关错误
    'computation_errors': {
        'reduce_precision': '降低精度',
        'simplify_algorithm': '简化算法',
        'use_approximation': '使用近似计算',
        'skip_operation': '跳过操作'
    },
    
    # 系统资源错误
    'resource_errors': {
        'free_memory': '释放内存',
        'reduce_concurrency': '减少并发',
        'pause_operations': '暂停操作',
        'graceful_degradation': '优雅降级'
    }
}
```

## 📚 相关API
- [CoreOptimizerEngine API](core_optimizer_api.md) - 核心优化引擎
- [EnhancedDataManager API](data_manager_api.md) - 数据管理
- [EnhancedIndicatorEngine API](indicator_engine_api.md) - 指标计算
- [PerformanceMonitor API](performance_monitor_api.md) - 性能监控

---

**🚀 EnhancedErrorHandler确保您的系统在任何情况下都能稳定运行！**