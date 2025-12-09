# PerformanceMonitor API - 性能监控系统

## 📖 概述

`PerformanceMonitor`提供实时性能监控、瓶颈分析、资源使用统计和性能优化建议，帮助您最大化系统性能和资源利用率。

## 🏗️ 类结构

```python
class PerformanceMonitor:
    """性能监控系统"""
    
    def __init__(
        self,
        monitoring_interval: float = 1.0,
        history_size: int = 1000,
        alert_thresholds: Optional[Dict[str, float]] = None,
        enable_logging: bool = True
    ):
        """初始化性能监控"""
```

## 🚀 核心方法

### 1. 基础监控功能

#### start_monitoring()
```python
def start_monitoring(
    self,
    components: Optional[List[str]] = None,
    interval: Optional[float] = None
) -> None:
    """
    开始性能监控
    
    Parameters:
    -----------
    components : list[str], optional
        要监控的组件，默认监控所有
    interval : float, optional
        监控间隔(秒)，默认使用初始化值
    
    Example:
    --------
    # 开始监控所有组件
    monitor.start_monitoring()
    
    # 只监控特定组件
    monitor.start_monitoring(['cpu', 'memory', 'optimization'])
    
    # 自定义监控间隔
    monitor.start_monitoring(interval=0.5)
    """
```

#### stop_monitoring()
```python
def stop_monitoring(self) -> None:
    """
    停止性能监控
    
    Example:
    --------
    monitor.stop_monitoring()
    """
```

#### get_current_metrics()
```python
def get_current_metrics(self) -> CurrentMetrics:
    """
    获取当前性能指标
    
    Returns:
    --------
    CurrentMetrics
        当前性能指标对象
    
    Example:
    --------
    metrics = monitor.get_current_metrics()
    
    print(f"CPU使用率: {metrics.cpu_percent:.1f}%")
    print(f"内存使用率: {metrics.memory_percent:.1f}%")
    print(f"活跃线程数: {metrics.active_threads}")
    print(f"优化器吞吐量: {metrics.optimizer_throughput:.1f} ops/s")
    """
```

**示例用法:**
```python
from enhanced_nonprice_ta_system import PerformanceMonitor

# 创建性能监控器
monitor = PerformanceMonitor(
    monitoring_interval=1.0,
    history_size=1000,
    enable_logging=True
)

# 开始监控
monitor.start_monitoring()

# 获取当前指标
metrics = monitor.get_current_metrics()

print("📊 当前系统性能:")
print(f"=" * 40)
print(f"💻 CPU使用率: {metrics.cpu_percent:.1f}%")
print(f"🧠 内存使用率: {metrics.memory_percent:.1f}%")
print(f"💾 内存使用量: {metrics.memory_used_mb:.1f}MB")
print(f"🧵 活跃线程数: {metrics.active_threads}")
print(f"📈 优化器吞吐量: {metrics.optimizer_throughput:.1f} ops/s")
print(f"🗄️ 缓存命中率: {metrics.cache_hit_rate:.1%}")
print(f"⏱️ 平均响应时间: {metrics.avg_response_time_ms:.2f}ms")
print(f"🔄 API调用次数: {metrics.api_calls_total:,}")
print(f"⚠️ 错误率: {metrics.error_rate:.2%}")

# 获取组件级别指标
if metrics.component_metrics:
    print(f"\\n🏗️ 组件性能:")
    for component, comp_metrics in metrics.component_metrics.items():
        print(f"  {component}:")
        print(f"    吞吐量: {comp_metrics.throughput:.1f} ops/s")
        print(f"    延迟: {comp_metrics.latency_ms:.2f}ms")
        print(f"    错误率: {comp_metrics.error_rate:.2%}")

# 停止监控
monitor.stop_monitoring()
```

### 2. 性能历史分析

#### get_performance_history()
```python
def get_performance_history(
    self,
    metric: str,
    time_range: Optional[TimeRange] = None,
    interval: Optional[str] = None
) -> pd.DataFrame:
    """
    获取性能历史数据
    
    Parameters:
    -----------
    metric : str
        指标名称
    time_range : TimeRange, optional
        时间范围
    interval : str, optional
        聚合间隔 ('1m', '5m', '1h', '1d')
    
    Returns:
    --------
    pd.DataFrame
        历史性能数据
    
    Example:
    --------
    # 获取CPU使用率历史
    cpu_history = monitor.get_performance_history('cpu_percent')
    
    # 获取最近1小时的内存使用
    from datetime import datetime, timedelta
    time_range = TimeRange(
        start=datetime.now() - timedelta(hours=1),
        end=datetime.now()
    )
    memory_history = monitor.get_performance_history(
        'memory_percent', 
        time_range=time_range,
        interval='5m'
    )
    """
```

**示例用法:**
```python
from datetime import datetime, timedelta
from enhanced_nonprice_ta_system import PerformanceMonitor, TimeRange

# 获取性能历史数据
end_time = datetime.now()
start_time = end_time - timedelta(hours=2)
time_range = TimeRange(start=start_time, end=end_time)

# 获取CPU使用率历史
cpu_history = monitor.get_performance_history(
    'cpu_percent',
    time_range=time_range,
    interval='5m'
)

# 获取内存使用率历史
memory_history = monitor.get_performance_history(
    'memory_percent',
    time_range=time_range,
    interval='5m'
)

# 获取优化器吞吐量历史
throughput_history = monitor.get_performance_history(
    'optimizer_throughput',
    time_range=time_range,
    interval='5m'
)

print("📈 性能历史分析:")
print(f"CPU使用率 - 平均: {cpu_history['value'].mean():.1f}%, "
      f"最高: {cpu_history['value'].max():.1f}%, "
      f"最低: {cpu_history['value'].min():.1f}%")

print(f"内存使用率 - 平均: {memory_history['value'].mean():.1f}%, "
      f"最高: {memory_history['value'].max():.1f}%, "
      f"最低: {memory_history['value'].min():.1f}%")

print(f"优化器吞吐量 - 平均: {throughput_history['value'].mean():.1f} ops/s, "
      f"最高: {throughput_history['value'].max():.1f} ops/s")
```

#### analyze_performance_trends()
```python
def analyze_performance_trends(
    self,
    time_range: Optional[TimeRange] = None
) -> TrendAnalysis:
    """
    分析性能趋势
    
    Parameters:
    -----------
    time_range : TimeRange, optional
        分析时间范围
    
    Returns:
    --------
    TrendAnalysis
        趋势分析结果
    
    Example:
    --------
    trends = monitor.analyze_performance_trends()
    
    for metric, trend in trends.trends.items():
        print(f"{metric}: {trend.direction} ({trend.change_percentage:+.1%})")
    """
```

**示例用法:**
```python
# 分析性能趋势
trend_analysis = monitor.analyze_performance_trends()

print("📊 性能趋势分析:")
for metric, trend in trend_analysis.trends.items():
    direction_icon = "📈" if trend.direction == "increasing" else "📉" if trend.direction == "decreasing" else "➡️"
    print(f"{direction_icon} {metric}: {trend.change_percentage:+.1%}")
    print(f"   趋势强度: {trend.strength:.1f}")
    print(f"   置信度: {trend.confidence:.1%}")

# 获取性能预测
predictions = trend_analysis.predictions
print("\\n🔮 性能预测:")
for metric, prediction in predictions.items():
    print(f"{metric}: {prediction.predicted_value:.2f} (置信度: {prediction.confidence:.1%})")

# 获取异常检测
anomalies = trend_analysis.anomalies
if anomalies:
    print("\\n⚠️ 性能异常:")
    for anomaly in anomalies:
        print(f"  {anomaly.metric}: {anomaly.value} (正常范围: {anomaly.expected_range})")
        print(f"  时间: {anomaly.timestamp}")
```

### 3. 瓶颈分析

#### identify_bottlenecks()
```python
def identify_bottlenecks(
    self,
    analysis_depth: str = 'standard'
) -> BottleneckAnalysis:
    """
    识别性能瓶颈
    
    Parameters:
    -----------
    analysis_depth : str, default 'standard'
        分析深度 ('quick', 'standard', 'deep')
    
    Returns:
    --------
    BottleneckAnalysis
        瓶颈分析结果
    
    Example:
    --------
    bottlenecks = monitor.identify_bottlenecks('deep')
    
    for bottleneck in bottlenecks.identified_bottlenecks:
        print(f"瓶颈: {bottleneck.component}")
        print(f"影响: {bottleneck.impact_percentage:.1%}")
        print(f"建议: {bottleneck.recommendation}")
    """
```

**示例用法:**
```python
# 识别性能瓶颈
bottleneck_analysis = monitor.identify_bottlenecks(analysis_depth='deep')

print("🔍 瓶颈分析结果:")
print(f"分析耗时: {bottleneck_analysis.analysis_time:.2f}秒")

# 显示发现的瓶颈
if bottleneck_analysis.identified_bottlenecks:
    print(f"\\n⚠️ 发现 {len(bottleneck_analysis.identified_bottlenecks)} 个瓶颈:")
    
    for i, bottleneck in enumerate(bottleneck_analysis.identified_bottlenecks, 1):
        print(f"\\n{i}. {bottleneck.component} - {bottleneck.severity}")
        print(f"   描述: {bottleneck.description}")
        print(f"   影响: {bottleneck.impact_percentage:.1%}")
        print(f"   当前值: {bottleneck.current_value}")
        print(f"   期望值: {bottleneck.expected_value}")
        print(f"   建议: {bottleneck.recommendation}")
        
        if bottleneck.solutions:
            print(f"   解决方案:")
            for solution in bottleneck.solutions:
                print(f"     - {solution}")
else:
    print("✅ 未发现明显瓶颈")

# 显示优化机会
optimization_opportunities = bottleneck_analysis.optimization_opportunities
if optimization_opportunities:
    print(f"\\n💡 优化机会:")
    for opportunity in optimization_opportunities:
        print(f"  {opportunity.component}: +{opportunity.potential_improvement:.1%}")
```

#### profile_component()
```python
def profile_component(
    self,
    component_name: str,
    duration: int = 60
) -> ComponentProfile:
    """
    组件性能分析
    
    Parameters:
    -----------
    component_name : str
        组件名称
    duration : int, default 60
        分析时长(秒)
    
    Returns:
    --------
    ComponentProfile
        组件性能档案
    
    Example:
    --------
    profile = monitor.profile_component('optimizer', duration=300)
    
    print(f"组件: {profile.component_name}")
    print(f"总执行时间: {profile.total_execution_time:.2f}秒")
    print(f"平均吞吐量: {profile.avg_throughput:.1f} ops/s")
    """
```

**示例用法:**
```python
# 分析优化器组件性能
print("🔬 开始组件性能分析...")
optimizer_profile = monitor.profile_component('optimizer', duration=30)

print(f"📊 {optimizer_profile.component_name} 性能档案:")
print(f"分析时长: {optimizer_profile.analysis_duration:.1f}秒")
print(f"总操作次数: {optimizer_profile.total_operations:,}")
print(f"总执行时间: {optimizer_profile.total_execution_time:.2f}秒")
print(f"平均吞吐量: {optimizer_profile.avg_throughput:.1f} ops/s")
print(f"峰值吞吐量: {optimizer_profile.peak_throughput:.1f} ops/s")
print(f"平均延迟: {optimizer_profile.avg_latency_ms:.2f}ms")
print(f"P95延迟: {optimizer_profile.p95_latency_ms:.2f}ms")
print(f"P99延迟: {optimizer_profile.p99_latency_ms:.2f}ms")

# 显示函数级别性能
if optimizer_profile.function_profiles:
    print(f"\\n🔧 函数性能分析:")
    sorted_functions = sorted(
        optimizer_profile.function_profiles.items(),
        key=lambda x: x[1].total_time,
        reverse=True
    )
    
    for func_name, func_profile in sorted_functions[:5]:
        print(f"  {func_name}:")
        print(f"    调用次数: {func_profile.call_count:,}")
        print(f"    总时间: {func_profile.total_time:.2f}秒")
        print(f"    平均时间: {func_profile.avg_time_ms:.2f}ms")
        print(f"    占比: {func_profile.percentage:.1%}")
```

### 4. 实时警报

#### setup_alerts()
```python
def setup_alerts(
    self,
    alert_rules: List[AlertRule],
    notification_channels: Optional[List[NotificationChannel]] = None
) -> None:
    """
    设置性能警报
    
    Parameters:
    -----------
    alert_rules : list[AlertRule]
        警报规则列表
    notification_channels : list[NotificationChannel], optional
        通知渠道
    
    Example:
    --------
    rules = [
        AlertRule(
            name="high_cpu",
            metric="cpu_percent",
            condition="gt",
            threshold=80,
            duration=300
        )
    ]
    monitor.setup_alerts(rules)
    """
```

**示例用法:**
```python
from enhanced_nonprice_ta_system import AlertRule, AlertCondition, NotificationChannel

# 定义警报规则
alert_rules = [
    AlertRule(
        name="high_cpu_usage",
        metric="cpu_percent",
        condition=AlertCondition.GREATER_THAN,
        threshold=80.0,
        duration=300,  # 5分钟
        severity="warning"
    ),
    AlertRule(
        name="high_memory_usage", 
        metric="memory_percent",
        condition=AlertCondition.GREATER_THAN,
        threshold=85.0,
        duration=180,  # 3分钟
        severity="critical"
    ),
    AlertRule(
        name="low_throughput",
        metric="optimizer_throughput",
        condition=AlertCondition.LESS_THAN,
        threshold=100.0,
        duration=600,  # 10分钟
        severity="warning"
    ),
    AlertRule(
        name="high_error_rate",
        metric="error_rate",
        condition=AlertCondition.GREATER_THAN,
        threshold=5.0,
        duration=120,  # 2分钟
        severity="critical"
    )
]

# 设置通知渠道
notification_channels = [
    NotificationChannel(
        name="console",
        type="console",
        enabled=True
    ),
    NotificationChannel(
        name="log_file",
        type="file",
        config={"file_path": "performance_alerts.log"}
    )
]

# 设置警报
monitor.setup_alerts(alert_rules, notification_channels)

print("🚨 警报系统已激活:")
print(f"  规则数量: {len(alert_rules)}")
print(f"  通知渠道: {len(notification_channels)}")
```

#### get_alerts()
```python
def get_alerts(
    self,
    severity: Optional[str] = None,
    time_range: Optional[TimeRange] = None,
    active_only: bool = False
) -> List[Alert]:
    """
    获取警报记录
    
    Parameters:
    -----------
    severity : str, optional
        严重程度过滤
    time_range : TimeRange, optional
        时间范围过滤
    active_only : bool, default False
        只获取活跃警报
    
    Returns:
    --------
    list[Alert]
        警报列表
    
    Example:
    --------
    # 获取所有活跃警报
    active_alerts = monitor.get_alerts(active_only=True)
    
    # 获取关键警报
    critical_alerts = monitor.get_alerts(severity="critical")
    """
```

**示例用法:**
```python
# 获取警报记录
all_alerts = monitor.get_alerts()
active_alerts = monitor.get_alerts(active_only=True)
critical_alerts = monitor.get_alerts(severity="critical")

print("🚨 警报状态:")
print(f"总警报数: {len(all_alerts)}")
print(f"活跃警报: {len(active_alerts)}")
print(f"关键警报: {len(critical_alerts)}")

# 显示活跃警报
if active_alerts:
    print(f"\\n🔴 活跃警报:")
    for alert in active_alerts:
        severity_icon = "🔴" if alert.severity == "critical" else "🟡" if alert.severity == "warning" else "🟢"
        print(f"{severity_icon} {alert.name}")
        print(f"   指标: {alert.metric} = {alert.current_value}")
        print(f"  阈值: {alert.threshold}")
        print(f"  持续时间: {alert.duration_seconds}秒")
        print(f"  触发时间: {alert.triggered_at}")
else:
    print("✅ 无活跃警报")

# 显示最近警报
if all_alerts:
    print(f"\\n📋 最近警报 (最后5条):")
    recent_alerts = sorted(all_alerts, key=lambda x: x.triggered_at, reverse=True)[:5]
    for alert in recent_alerts:
        status = "🟢" if alert.resolved else "🔴"
        print(f"{status} {alert.name} - {alert.triggered_at}")
```

### 5. 性能报告

#### generate_performance_report()
```python
def generate_performance_report(
    self,
    time_range: Optional[TimeRange] = None,
    format: str = 'html',
    include_charts: bool = True,
    output_path: Optional[str] = None
) -> str:
    """
    生成性能报告
    
    Parameters:
    -----------
    time_range : TimeRange, optional
        报告时间范围
    format : str, default 'html'
        报告格式 ('html', 'pdf', 'json', 'csv')
    include_charts : bool, default True
        是否包含图表
    output_path : str, optional
        输出文件路径
    
    Returns:
    --------
    str
        报告内容或文件路径
    
    Example:
    --------
    # 生成HTML性能报告
    report_path = monitor.generate_performance_report(
        format='html',
        include_charts=True,
        output_path='performance_report.html'
    )
    """
```

**示例用法:**
```python
from datetime import datetime, timedelta

# 定义报告时间范围
end_time = datetime.now()
start_time = end_time - timedelta(hours=24)
time_range = TimeRange(start=start_time, end=end_time)

# 生成性能报告
report_path = monitor.generate_performance_report(
    time_range=time_range,
    format='html',
    include_charts=True,
    output_path=f'performance_report_{end_time.strftime("%Y%m%d_%H%M%S")}.html'
)

print(f"📊 性能报告已生成: {report_path}")

# 生成JSON格式报告用于API
json_report = monitor.generate_performance_report(
    time_range=time_range,
    format='json',
    include_charts=False
)

# 解析JSON报告获取关键指标
import json
report_data = json.loads(json_report)

print(f"\\n📈 报告摘要 (24小时):")
print(f"平均CPU使用率: {report_data['summary']['avg_cpu_percent']:.1f}%")
print(f"平均内存使用率: {report_data['summary']['avg_memory_percent']:.1f}%")
print(f"总优化操作: {report_data['summary']['total_optimizations']:,}")
print(f"平均吞吐量: {report_data['summary']['avg_throughput']:.1f} ops/s")
print(f"总警报数: {report_data['summary']['total_alerts']}")
```

### 6. 性能优化建议

#### get_optimization_recommendations()
```python
def get_optimization_recommendations(
    self,
    focus_areas: Optional[List[str]] = None
) -> OptimizationRecommendations:
    """
    获取性能优化建议
    
    Parameters:
    -----------
    focus_areas : list[str], optional
        重点关注区域
    
    Returns:
    --------
    OptimizationRecommendations
        优化建议集合
    
    Example:
    --------
    recommendations = monitor.get_optimization_recommendations(
        focus_areas=['cpu', 'memory', 'io']
    )
    
    for rec in recommendations.recommendations:
        print(f"{rec.category}: {rec.description}")
        print(f"预期改善: {rec.expected_improvement:.1%}")
    """
```

**示例用法:**
```python
# 获取性能优化建议
recommendations = monitor.get_optimization_recommendations(
    focus_areas=['cpu', 'memory', 'cache', 'optimization']
)

print("💡 性能优化建议:")
print(f"分析时间: {recommendations.analysis_time:.2f}秒")
print(f"建议数量: {len(recommendations.recommendations)}")

# 按优先级分组建议
high_priority = []
medium_priority = []
low_priority = []

for rec in recommendations.recommendations:
    if rec.priority == "high":
        high_priority.append(rec)
    elif rec.priority == "medium":
        medium_priority.append(rec)
    else:
        low_priority.append(rec)

# 显示高优先级建议
if high_priority:
    print(f"\\n🔴 高优先级建议:")
    for rec in high_priority:
        print(f"  {rec.title}")
        print(f"  描述: {rec.description}")
        print(f"  预期改善: {rec.expected_improvement:.1%}")
        print(f"  实施难度: {rec.implementation_difficulty}")
        print(f"  代码示例: {rec.code_example[:100]}...")

# 显示中等优先级建议
if medium_priority:
    print(f"\\n🟡 中等优先级建议:")
    for rec in medium_priority:
        print(f"  {rec.title}: {rec.description}")

# 显示低优先级建议
if low_priority:
    print(f"\\n🟢 低优先级建议:")
    for rec in low_priority:
        print(f"  {rec.title}: {rec.description}")

# 总体潜力分析
total_potential = sum(rec.expected_improvement for rec in recommendations.recommendations)
print(f"\\n📊 总体优化潜力: {total_potential:.1%}")
```

## 📊 监控对象

### CurrentMetrics
```python
@dataclass
class CurrentMetrics:
    """当前性能指标"""
    # 系统指标
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    active_threads: int
    
    # 应用指标
    optimizer_throughput: float
    cache_hit_rate: float
    avg_response_time_ms: float
    api_calls_total: int
    error_rate: float
    
    # 组件指标
    component_metrics: Dict[str, ComponentMetrics]
    
    # 时间戳
    timestamp: datetime
```

### TrendAnalysis
```python
@dataclass
class TrendAnalysis:
    """趋势分析结果"""
    trends: Dict[str, Trend]
    predictions: Dict[str, Prediction]
    anomalies: List[Anomaly]
    confidence_score: float
    analysis_period: TimeRange
```

### BottleneckAnalysis
```python
@dataclass
class BottleneckAnalysis:
    """瓶颈分析结果"""
    identified_bottlenecks: List[Bottleneck]
    optimization_opportunities: List[Opportunity]
    analysis_time: float
    analysis_depth: str
    confidence_level: float
```

## ⚙️ 配置参数

### 监控配置
```python
PERFORMANCE_MONITOR_CONFIG = {
    # 基础配置
    'monitoring': {
        'interval_seconds': 1.0,      # 监控间隔
        'history_size': 1000,         # 历史数据大小
        'enable_logging': True,       # 启用日志
        'log_level': 'INFO'           # 日志级别
    },
    
    # 性能阈值
    'thresholds': {
        'cpu_warning': 70.0,          # CPU警告阈值
        'cpu_critical': 90.0,         # CPU关键阈值
        'memory_warning': 75.0,       # 内存警告阈值
        'memory_critical': 90.0,      # 内存关键阈值
        'throughput_warning': 100.0,  # 吞吐量警告阈值
        'error_rate_critical': 5.0    # 错误率关键阈值
    },
    
    # 警报配置
    'alerts': {
        'enabled': True,              # 启用警报
        'cooldown_seconds': 300,      # 警报冷却时间
        'max_alerts_per_hour': 10,    # 每小时最大警报数
        'notification_channels': ['console', 'log']  # 通知渠道
    },
    
    # 报告配置
    'reporting': {
        'auto_generate': True,        # 自动生成报告
        'schedule_hours': 24,         # 报告生成间隔
        'keep_days': 30,              # 报告保留天数
        'include_charts': True        # 包含图表
    }
}
```

## 🚨 错误处理

### 错误类型
```python
class PerformanceMonitorError(Exception):
    """性能监控基础异常"""
    pass

class MonitoringError(PerformanceMonitorError):
    """监控过程错误"""
    pass

class AnalysisError(PerformanceMonitorError):
    """分析过程错误"""
    pass

class AlertError(PerformanceMonitorError):
    """警报系统错误"""
    pass
```

### 错误处理示例
```python
try:
    # 开始监控
    monitor.start_monitoring()
except MonitoringError as e:
    print(f"监控启动失败: {e}")
    # 使用默认设置启动
    monitor.start_monitoring(components=['cpu', 'memory'])

try:
    # 生成报告
    report_path = monitor.generate_performance_report(format='html')
except AnalysisError as e:
    print(f"报告生成失败: {e}")
    # 使用JSON格式重试
    report_path = monitor.generate_performance_report(format='json')
```

## 📚 相关API
- [CoreOptimizerEngine API](core_optimizer_api.md) - 核心优化引擎
- [EnhancedDataManager API](data_manager_api.md) - 数据管理
- [EnhancedIndicatorEngine API](indicator_engine_api.md) - 指标计算
- [IntelligentCache API](cache_system_api.md) - 缓存系统

---

**🚀 PerformanceMonitor让您的系统性能尽在掌握！**