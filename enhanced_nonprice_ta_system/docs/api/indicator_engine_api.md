# EnhancedIndicatorEngine API - 指标计算引擎

## 📖 概述

`EnhancedIndicatorEngine`提供81种技术指标的高性能计算能力，支持多种指标类型、并行计算和智能缓存。集成了香港政府经济数据，实现非价格技术分析。

## 🏗️ 类结构

```python
class EnhancedIndicatorEngine:
    """增强指标计算引擎"""
    
    def __init__(
        self,
        cache_manager: Optional[IntelligentCache] = None,
        performance_monitor: Optional[PerformanceMonitor] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """初始化指标引擎"""
```

## 🚀 核心方法

### 1. 基础技术指标计算

#### calculate_rsi()
```python
def calculate_rsi(
    self,
    prices: pd.Series,
    period: int = 14,
    method: str = 'wilders'
) -> pd.Series:
    """
    计算RSI相对强弱指标
    
    Parameters:
    -----------
    prices : pd.Series
        价格序列
    period : int, default 14
        RSI周期
    method : str, default 'wilders'
        计算方法 ('wilders', 'simple', 'exponential')
    
    Returns:
    --------
    pd.Series
        RSI值序列 (0-100)
    """
```

**示例用法:**
```python
from enhanced_nonprice_ta_system import EnhancedIndicatorEngine

# 创建指标引擎
engine = EnhancedIndicatorEngine()

# 计算腾讯RSI
rsi_14 = engine.calculate_rsi(tencent_data['close'], 14)
rsi_30 = engine.calculate_rsi(tencent_data['close'], 30)

print(f"RSI(14) 最新值: {rsi_14.iloc[-1]:.2f}")
print(f"RSI(30) 最新值: {rsi_30.iloc[-1]:.2f}")

# RSI信号分析
latest_rsi = rsi_14.iloc[-1]
if latest_rsi < 30:
    signal = "超卖"
elif latest_rsi > 70:
    signal = "超买"
else:
    signal = "中性"
print(f"RSI信号: {signal}")
```

#### calculate_macd()
```python
def calculate_macd(
    self,
    prices: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9
) -> Dict[str, pd.Series]:
    """
    计算MACD指标
    
    Parameters:
    -----------
    prices : pd.Series
        价格序列
    fast : int, default 12
        快线周期
    slow : int, default 26
        慢线周期
    signal : int, default 9
        信号线周期
    
    Returns:
    --------
    dict
        包含MACD、Signal、Histogram的字典
    """
```

**示例用法:**
```python
# 计算MACD
macd_result = engine.calculate_macd(
    tencent_data['close'],
    fast=12, slow=26, signal=9
)

macd_line = macd_result['macd']
signal_line = macd_result['signal']
histogram = macd_result['histogram']

# MACD交叉信号分析
latest_macd = macd_line.iloc[-1]
latest_signal = signal_line.iloc[-1]
latest_hist = histogram.iloc[-1]

if latest_macd > latest_signal and latest_hist > 0:
    signal = "金叉买入"
elif latest_macd < latest_signal and latest_hist < 0:
    signal = "死叉卖出"
else:
    signal = "观望"

print(f"MACD最新值: {latest_macd:.4f}")
print(f"Signal最新值: {latest_signal:.4f}")
print(f"Histogram最新值: {latest_hist:.4f}")
print(f"MACD信号: {signal}")
```

#### calculate_kdj()
```python
def calculate_kdj(
    self,
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    k_period: int = 9,
    d_period: int = 3,
    j_period: int = 3
) -> Dict[str, pd.Series]:
    """
    计算KDJ随机指标
    
    Parameters:
    -----------
    high : pd.Series
        最高价序列
    low : pd.Series
        最低价序列
    close : pd.Series
        收盘价序列
    k_period : int, default 9
        K值周期
    d_period : int, default 3
        D值平滑周期
    j_period : int, default 3
        J值周期
    
    Returns:
    --------
    dict
        包含K、D、J值的字典
    """
```

**示例用法:**
```python
# 计算KDJ指标
kdj_result = engine.calculate_kdj(
    tencent_data['high'],
    tencent_data['low'],
    tencent_data['close'],
    k_period=9, d_period=3, j_period=3
)

k_values = kdj_result['k']
d_values = kdj_result['d']
j_values = kdj_result['j']

# KDJ信号分析
latest_k = k_values.iloc[-1]
latest_d = d_values.iloc[-1]
latest_j = j_values.iloc[-1]

if latest_k < 20 and latest_d < 20:
    signal = "超卖区域"
elif latest_k > 80 and latest_d > 80:
    signal = "超买区域"
elif latest_k > latest_d and latest_k < 50:
    signal = "金叉买入"
elif latest_k < latest_d and latest_k > 50:
    signal = "死叉卖出"
else:
    signal = "中性"

print(f"KDJ - K: {latest_k:.2f}, D: {latest_d:.2f}, J: {latest_j:.2f}")
print(f"KDJ信号: {signal}")

# 验证MB_KDJ_[10,2]策略
mb_kdj_result = engine.calculate_kdj(
    tencent_data['high'],
    tencent_data['low'],
    tencent_data['close'],
    k_period=10, d_period=2, j_period=2
)

print(f"MB_KDJ_[10,2] 最新值:")
print(f"K: {mb_kdj_result['k'].iloc[-1]:.2f}")
print(f"D: {mb_kdj_result['d'].iloc[-1]:.2f}")
print(f"J: {mb_kdj_result['j'].iloc[-1]:.2f}")
```

#### calculate_bollinger_bands()
```python
def calculate_bollinger_bands(
    self,
    prices: pd.Series,
    period: int = 20,
    std_dev: float = 2.0
) -> Dict[str, pd.Series]:
    """
    计算布林带指标
    
    Parameters:
    -----------
    prices : pd.Series
        价格序列
    period : int, default 20
        移动平均周期
    std_dev : float, default 2.0
        标准差倍数
    
    Returns:
    --------
    dict
        包含上轨、中轨、下轨的字典
    """
```

**示例用法:**
```python
# 计算布林带
bb_result = engine.calculate_bollinger_bands(
    tencent_data['close'],
    period=20, std_dev=2.0
)

upper_band = bb_result['upper']
middle_band = bb_result['middle']
lower_band = bb_result['lower']

# 布林带信号分析
latest_price = tencent_data['close'].iloc[-1]
latest_upper = upper_band.iloc[-1]
latest_middle = middle_band.iloc[-1]
latest_lower = lower_band.iloc[-1]

band_width = (latest_upper - latest_lower) / latest_middle
percent_b = (latest_price - latest_lower) / (latest_upper - latest_lower)

if percent_b < 0:
    signal = "跌破下轨"
elif percent_b > 1:
    signal = "突破上轨"
elif percent_b < 0.2:
    signal = "接近下轨"
elif percent_b > 0.8:
    signal = "接近上轨"
else:
    signal = "中轨附近"

print(f"布林带分析:")
print(f"价格: {latest_price:.2f}")
print(f"上轨: {latest_upper:.2f}")
print(f"中轨: {latest_middle:.2f}")
print(f"下轨: {latest_lower:.2f}")
print(f"带宽: {band_width:.2%}")
print(f"%B位置: {percent_b:.2%}")
print(f"布林带信号: {signal}")
```

### 2. 政府数据指标计算

#### calculate_hibor_indicators()
```python
def calculate_hibor_indicators(
    self,
    hibor_data: pd.DataFrame,
    windows: Optional[List[int]] = None
) -> Dict[str, pd.Series]:
    """
    计算HIBOR相关指标
    
    Parameters:
    -----------
    hibor_data : pd.DataFrame
        HIBOR利率数据
    windows : list[int], optional
        计算窗口，默认[5, 10, 20, 60]
    
    Returns:
    --------
    dict
        HIBOR指标字典
    """
```

**支持的HIBOR指标:**
```python
HIBOR_INDICATORS = {
    'overnight_rate': '隔夜利率',
    'one_week_rate': '1周利率',
    'one_month_rate': '1月利率',
    'three_month_rate': '3月利率',
    'rate_changes': '利率变化',
    'rate_volatility': '利率波动率',
    'rate_momentum': '利率动量',
    'yield_curve_spread': '收益率曲线利差',
    'hibor_trend': 'HIBOR趋势指标',
    'liquidity_indicator': '流动性指标'
}
```

**示例用法:**
```python
# 获取HIBOR数据
hibor_data = gov_data['hibor']

# 计算HIBOR指标
hibor_indicators = engine.calculate_hibor_indicators(hibor_data)

# 分析HIBOR指标
overnight = hibor_indicators['overnight_rate']
one_month = hibor_indicators['one_month_rate']
rate_changes = hibor_indicators['rate_changes']
volatility = hibor_indicators['rate_volatility']

latest_overnight = overnight.iloc[-1]
latest_one_month = one_month.iloc[-1]
latest_change = rate_changes.iloc[-1]
latest_vol = volatility.iloc[-1]

print(f"HIBOR分析:")
print(f"隔夜利率: {latest_overnight:.3f}%")
print(f"1月利率: {latest_one_month:.3f}%")
print(f"利率变化: {latest_change:+.3f}%")
print(f"利率波动率: {latest_vol:.3%}")

# 流动性信号
if latest_overnight > 3.0:
    liquidity_signal = "紧缩"
elif latest_overnight < 2.0:
    liquidity_signal = "宽松"
else:
    liquidity_signal = "中性"

print(f"流动性信号: {liquidity_signal}")
```

#### calculate_monetary_base_indicators()
```python
def calculate_monetary_base_indicators(
    self,
    monetary_data: pd.DataFrame,
    windows: Optional[List[int]] = None
) -> Dict[str, pd.Series]:
    """
    计算货币基础相关指标
    
    Parameters:
    -----------
    monetary_data : pd.DataFrame
        货币基础数据
    windows : list[int], optional
        计算窗口
    
    Returns:
    --------
    dict
        货币基础指标字典
    """
```

**示例用法:**
```python
# 计算货币基础指标
monetary_indicators = engine.calculate_monetary_base_indicators(
    gov_data['monetary_base']
)

# 分析货币基础
growth_rate = monetary_indicators['growth_rate']
trend = monetary_indicators['trend']
momentum = monetary_indicators['momentum']

latest_growth = growth_rate.iloc[-1]
latest_trend = trend.iloc[-1]
latest_momentum = momentum.iloc[-1]

print(f"货币基础分析:")
print(f"增长率: {latest_growth:.2%}")
print(f"趋势强度: {latest_trend:.2f}")
print(f"动量指标: {latest_momentum:.2f}")

# 货币政策信号
if latest_growth > 0.05:
    monetary_signal = "宽松"
elif latest_growth < -0.02:
    monetary_signal = "紧缩"
else:
    monetary_signal = "稳定"

print(f"货币政策信号: {monetary_signal}")
```

### 3. 复合指标计算

#### calculate_composite_indicators()
```python
def calculate_composite_indicators(
    self,
    stock_data: pd.DataFrame,
    gov_data: Dict[str, pd.DataFrame],
    strategy_name: str = "MB_KDJ_Enhanced"
) -> Dict[str, pd.Series]:
    """
    计算复合指标 (结合股票和政府数据)
    
    Parameters:
    -----------
    stock_data : pd.DataFrame
        股票数据
    gov_data : dict
        政府数据
    strategy_name : str
        策略名称
    
    Returns:
    --------
    dict
        复合指标字典
    """
```

**支持的复合指标:**
```python
COMPOSITE_INDICATORS = {
    'mb_kdj_enhanced': 'MB_KDJ增强版',
    'hibor_rsi_fusion': 'HIBOR-RSI融合指标',
    'monetary_macd': '货币基础MACD',
    'liquidity_bb': '流动性布林带',
    'economic_momentum': '经济动量指标',
    'market_regime': '市场周期指标',
    'risk_adjusted_signals': '风险调整信号',
    'policy_impact': '政策影响指标'
}
```

**示例用法:**
```python
# 计算MB_KDJ增强版指标
composite_indicators = engine.calculate_composite_indicators(
    tencent_data,
    gov_data,
    strategy_name="MB_KDJ_Enhanced"
)

# 分析复合指标
enhanced_kdj = composite_indicators['mb_kdj_enhanced']
liquidity_adjusted = composite_indicators['liquidity_adjusted_signals']
policy_impact = composite_indicators['policy_impact']

print(f"MB_KDJ增强版:")
print(f"增强K值: {enhanced_kdj.iloc[-1]:.2f}")
print(f"流动性调整信号: {liquidity_adjusted.iloc[-1]:.2f}")
print(f"政策影响指标: {policy_impact.iloc[-1]:.2f}")

# 生成交易信号
def generate_composite_signal(indicators):
    """生成复合交易信号"""
    mb_kdj = indicators['mb_kdj_enhanced'].iloc[-1]
    liquidity = indicators['liquidity_adjusted_signals'].iloc[-1]
    policy = indicators['policy_impact'].iloc[-1]
    
    # 综合评分
    score = 0
    if mb_kdj < 20:
        score += 2  # KDJ超卖
    elif mb_kdj > 80:
        score -= 2  # KDJ超买
    
    if liquidity > 0:
        score += 1  # 流动性支持
    
    if policy > 0:
        score += 1  # 政策支持
    
    if score >= 3:
        return "强烈买入"
    elif score >= 1:
        return "买入"
    elif score <= -1:
        return "卖出"
    elif score <= -3:
        return "强烈卖出"
    else:
        return "观望"

signal = generate_composite_signal(composite_indicators)
print(f"复合信号: {signal}")
```

### 4. 批量指标计算

#### calculate_multiple_indicators()
```python
def calculate_multiple_indicators(
    self,
    stock_data: pd.DataFrame,
    gov_data: Optional[Dict[str, pd.DataFrame]] = None,
    indicator_list: Optional[List[str]] = None,
    parallel: bool = True
) -> Dict[str, Dict[str, pd.Series]]:
    """
    批量计算多个指标
    
    Parameters:
    -----------
    stock_data : pd.DataFrame
        股票数据
    gov_data : dict, optional
        政府数据
    indicator_list : list[str], optional
        指标列表
    parallel : bool, default True
        是否并行计算
    
    Returns:
    --------
    dict
        多个指标的计算结果
    """
```

**示例用法:**
```python
# 定义要计算的指标
indicator_list = [
    'RSI_14', 'RSI_30', 'RSI_50',
    'MACD_12_26_9', 'MACD_5_35_5',
    'KDJ_9_3_3', 'KDJ_14_3_3',
    'BOLLINGER_20_2', 'BOLLINGER_10_1.5'
]

# 批量计算
all_indicators = engine.calculate_multiple_indicators(
    tencent_data,
    gov_data,
    indicator_list,
    parallel=True
)

# 查看计算结果
print("批量指标计算结果:")
for indicator_name, indicator_data in all_indicators.items():
    print(f"{indicator_name}: 计算完成")
    if isinstance(indicator_data, dict):
        for sub_indicator, values in indicator_data.items():
            latest_value = values.iloc[-1]
            print(f"  {sub_indicator}: {latest_value:.4f}")
    else:
        latest_value = indicator_data.iloc[-1]
        print(f"  值: {latest_value:.4f}")

# 计算耗时分析
calculation_time = engine.get_last_calculation_time()
print(f"\\n计算耗时: {calculation_time:.2f}秒")
```

### 5. 指标信号生成

#### generate_trading_signals()
```python
def generate_trading_signals(
    self,
    indicators: Dict[str, Any],
    strategy_config: Dict[str, Any]
) -> pd.DataFrame:
    """
    基于指标生成交易信号
    
    Parameters:
    -----------
    indicators : dict
        指标数据
    strategy_config : dict
        策略配置
    
    Returns:
    --------
    pd.DataFrame
        交易信号DataFrame
    """
```

**示例用法:**
```python
# 配置策略参数
strategy_config = {
    'RSI': {
        'oversold': 30,
        'overbought': 70,
        'period': 14
    },
    'MACD': {
        'fast': 12,
        'slow': 26,
        'signal': 9
    },
    'KDJ': {
        'k_period': 10,
        'd_period': 2,
        'oversold': 20,
        'overbought': 80
    },
    'government_weight': 0.3,  # 政府数据权重
    'risk_adjustment': True
}

# 生成交易信号
signals = engine.generate_trading_signals(
    all_indicators,
    strategy_config
)

# 分析信号
print("交易信号分析:")
print(f"总信号数: {len(signals)}")

# 统计信号类型
signal_counts = signals['signal'].value_counts()
for signal_type, count in signal_counts.items():
    print(f"{signal_type}: {count} 次")

# 最新信号
latest_signal = signals.iloc[-1]
print(f"\\n最新信号:")
print(f"日期: {latest_signal['date']}")
print(f"信号: {latest_signal['signal']}")
print(f"强度: {latest_signal['strength']:.2f}")
print(f"置信度: {latest_signal['confidence']:.2f}")
print(f"触发指标: {latest_signal['trigger_indicators']}")
```

### 6. 指标性能分析

#### analyze_indicator_performance()
```python
def analyze_indicator_performance(
    self,
    indicators: Dict[str, pd.Series],
    price_data: pd.Series,
    lookahead_period: int = 10
) -> IndicatorPerformanceReport:
    """
    分析指标性能
    
    Parameters:
    -----------
    indicators : dict
        指标数据
    price_data : pd.Series
        价格数据
    lookahead_period : int, default 10
    前瞻周期
    
    Returns:
    --------
    IndicatorPerformanceReport
        性能分析报告
    """
```

**示例用法:**
```python
# 分析指标性能
performance_report = engine.analyze_indicator_performance(
    {
        'RSI_14': rsi_14,
        'MACD_12_26_9': macd_result['macd'],
        'KDJ_9_3_3': kdj_result['k']
    },
    tencent_data['close'],
    lookahead_period=5
)

print("指标性能分析:")
for indicator_name, perf in performance_report.indicator_performance.items():
    print(f"\\n{indicator_name}:")
    print(f"  预测准确率: {perf['accuracy']:.2%}")
    print(f"  信号有效性: {perf['signal_effectiveness']:.2%}")
    print(f"  平均收益率: {perf['average_return']:.2%}")
    print(f"  夏普比率: {perf['sharpe_ratio']:.3f}")
    print(f"  最大回撤: {perf['max_drawdown']:.2%}")

# 最佳指标推荐
best_indicator = performance_report.get_best_indicator()
print(f"\\n最佳指标: {best_indicator}")
```

## 📊 指标列表

### 趋势指标
```python
TREND_INDICATORS = [
    'SMA',          # 简单移动平均
    'EMA',          # 指数移动平均
    'MACD',         # MACD指标
    'DMI',          # 方向性运动指标
    'ADX',          # 平均方向性运动指标
    'AROON',        # 阿隆指标
    'TRIX',         # 三重指数平滑平均
    'CCI',          # 顺势指标
    'BOP',          # 均势指标
    'TEMA'          # 三重指数移动平均
]
```

### 动量指标
```python
MOMENTUM_INDICATORS = [
    'RSI',          # 相对强弱指标
    'RSI_SMOOTHED', # 平滑RSI
    'STOCHASTIC',   # 随机指标
    'STOCHASTIC_RSI', # RSI随机指标
    'MFI',          # 资金流量指标
    'ULTIMATE',     # 终极指标
    'WILLIAMS_R',   # 威廉指标
    'ROC',          # 变化率指标
    'MOMENTUM',     # 动量指标
    'RATE_OF_CHANGE' # 变化率
]
```

### 波动率指标
```python
VOLATILITY_INDICATORS = [
    'BOLLINGER_BANDS',  # 布林带
    'ATR',              # 平均真实波幅
    'KELTNER_CHANNELS', # 肯特纳通道
    'DONCHIAN_CHANNELS', # 唐奇安通道
    'STANDARD_DEVIATION', # 标准差
    'VOLATILITY_RATIO',  # 波动率比率
    'HISTORICAL_VOLATILITY', # 历史波动率
    'GARCH_VOLATILITY',   # GARCH波动率
    'PARKINSON_VOLATILITY', # 帕金森波动率
    'GARMAN_KLASS_VOLATILITY' # 加曼-克拉斯波动率
]
```

### 成交量指标
```python
VOLUME_INDICATORS = [
    'VOLUME_SMA',        # 成交量移动平均
    'VOLUME_EMA',        # 成交量指数平均
    'ON_BALANCE_VOLUME',  # 能量潮指标
    'VOLUME_PROFILE',     # 成交量分布
    'VOLUME_WEIGHTED_AVERAGE_PRICE', # VWAP
    'ACCUMULATION_DISTRIBUTION', # 累积/派发指标
    'MONEY_FLOW_INDEX',   # 资金流量指标
    'VOLUME_RATE_OF_CHANGE', # 成交量变化率
    'EASE_OF_MOVEMENT',   # 易波度指标
    'VOLUME_OSCILLATOR'   # 成交量震荡指标
]
```

### 政府数据指标
```python
GOVERNMENT_INDICATORS = [
    'HIBOR_RATES',        # HIBOR利率指标
    'MONETARY_BASE',      # 货币基础指标
    'EXCHANGE_RATES',     # 汇率指标
    'LIQUIDITY_INDEX',    # 流动性指标
    'ECONOMIC_MOMENTUM',  # 经济动量指标
    'POLICY_IMPACT',      # 政策影响指标
    'INTEREST_RATE_SPREAD', # 利率差指标
    'INFLATION_INDICATOR',  # 通胀指标
    'CREDIT_CONDITION',     # 信贷条件指标
    'MARKET_REGIME'         # 市场周期指标
]
```

## ⚙️ 配置参数

### 指标引擎配置
```python
INDICATOR_ENGINE_CONFIG = {
    # 计算配置
    'calculation': {
        'precision': 6,           # 计算精度
        'min_periods': 20,        # 最小数据周期
        'parallel_cores': 8,      # 并行核心数
        'batch_size': 1000,       # 批处理大小
        'use_cache': True         # 使用缓存
    },
    
    # RSI配置
    'rsi': {
        'default_period': 14,
        'period_range': (2, 100),
        'oversold_levels': [20, 25, 30],
        'overbought_levels': [70, 75, 80]
    },
    
    # MACD配置
    'macd': {
        'fast_range': (5, 50),
        'slow_range': (20, 200),
        'signal_range': (5, 20),
        'default_params': (12, 26, 9)
    },
    
    # KDJ配置
    'kdj': {
        'k_period_range': (5, 100),
        'd_period_range': (1, 20),
        'j_period_range': (1, 20),
        'default_params': (9, 3, 3)
    },
    
    # 政府数据权重
    'government_weights': {
        'hibor': 0.4,          # HIBOR权重40%
        'monetary_base': 0.3,  # 货币基础权重30%
        'exchange_rate': 0.2,  # 汇率权重20%
        'other': 0.1          # 其他指标权重10%
    }
}
```

## 🚨 错误处理

### 错误类型
```python
class IndicatorCalculationError(Exception):
    """指标计算错误"""
    pass

class InsufficientDataError(Exception):
    """数据不足错误"""
    pass

class InvalidParametersError(Exception):
    """无效参数错误"""
    pass

class CacheError(Exception):
    """缓存错误"""
    pass
```

### 错误处理示例
```python
try:
    # 计算指标
    rsi = engine.calculate_rsi(prices, period=14)
except InsufficientDataError as e:
    print(f"数据不足: {e}")
    # 使用更短的周期
    rsi = engine.calculate_rsi(prices, period=7)
except InvalidParametersError as e:
    print(f"参数错误: {e}")
    # 使用默认参数
    rsi = engine.calculate_rsi(prices, period=14)
except IndicatorCalculationError as e:
    print(f"计算错误: {e}")
    # 使用备用方法
    rsi = engine.calculate_rsi(prices, period=14, method='simple')
```

## 📚 相关API
- [CoreOptimizerEngine API](core_optimizer_api.md) - 核心优化引擎
- [EnhancedDataManager API](data_manager_api.md) - 数据管理
- [IntelligentCache API](cache_system_api.md) - 缓存系统
- [PerformanceMonitor API](performance_monitor_api.md) - 性能监控

---

**🚀 EnhancedIndicatorEngine为您提供强大的技术分析计算能力！**