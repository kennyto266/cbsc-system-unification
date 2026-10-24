# GPU计算核心技术规范

## 概述

实现真正的GPU技术指标计算，确保RSI、MACD等核心指标100%在GPU上执行，消除CPU回退机制。

## 核心设计原则

1. **纯GPU计算**: 所有计算逻辑在GPU上完成
2. **向量化优先**: 使用CuPy向量化操作
3. **内存高效**: 优化GPU内存使用模式
4. **容错设计**: 处理GPU计算特有问题

## RSI GPU实现规范

### 接口定义
```python
def calculate_rsi_gpu(prices_gpu: cp.ndarray, period: int) -> cp.ndarray:
    """
    GPU加速RSI计算

    Args:
        prices_gpu: GPU上的价格数组 (N, float32)
        period: RSI周期 (1-300)

    Returns:
        cp.ndarray: RSI值数组 (N, float32, range 0-100)

    Raises:
        ValueError: 参数无效
        RuntimeError: GPU计算失败
    """
```

### 实现要求
```python
def calculate_rsi_gpu(prices_gpu, period):
    # 1. 输入验证
    if len(prices_gpu) < period:
        return cp.full(len(prices_gpu), 50.0, dtype=cp.float32)

    # 2. 计算价格变化 - 纯GPU操作
    delta = cp.diff(prices_gpu, prepend=cp.array([prices_gpu[0]]))

    # 3. 分离涨跌 - 向量化操作
    gain = cp.where(delta > 0, delta, 0.0, dtype=cp.float32)
    loss = cp.where(delta < 0, -delta, 0.0, dtype=cp.float32)

    # 4. GPU移动平均计算 - 优化版本
    avg_gain = gpu_moving_average(gain, period)
    avg_loss = gpu_moving_average(loss, period)

    # 5. RS计算 - 避免除零
    rs = avg_gain / cp.where(avg_loss == 0, 1e-10, avg_loss)

    # 6. RSI计算 - 向量化公式
    rsi = 100 - (100 / (1 + rs))

    # 7. 结果标准化
    rsi = cp.clip(rsi, 0, 100)

    return rsi
```

### 性能优化
- 使用`cp.cumsum`替代`cp.convolve`
- 避免不必要的内存分配
- 利用GPU并行计算优势
- 内存访问模式优化

## MACD GPU实现规范

### 接口定义
```python
def calculate_macd_gpu(prices_gpu: cp.ndarray,
                      fast_period: int,
                      slow_period: int,
                      signal_period: int) -> Tuple[cp.ndarray, cp.ndarray, cp.ndarray]:
    """
    GPU加速MACD计算

    Returns:
        macd_line: MACD线
        signal_line: 信号线
        histogram: 柱状图
    """
```

### EMA计算优化
```python
def gpu_ema(data_gpu: cp.ndarray, period: int) -> cp.ndarray:
    """GPU优化EMA计算"""
    alpha = 2.0 / (period + 1)
    ema = cp.zeros_like(data_gpu, dtype=cp.float32)
    ema[0] = data_gpu[0]

    # 使用递归向量化计算
    for i in range(1, len(data_gpu)):
        ema[i] = alpha * data_gpu[i] + (1 - alpha) * ema[i-1]

    return ema
```

## 高级指标实现

### KDJ GPU实现
```python
def calculate_kdj_gpu(high_gpu: cp.ndarray,
                     low_gpu: cp.ndarray,
                     close_gpu: cp.ndarray,
                     k_period: int,
                     d_period: int) -> Tuple[cp.ndarray, cp.ndarray, cp.ndarray]:
    """GPU加速KDJ指标计算"""

    # RSV计算 - 完全向量化
    lowest_low = gpu_rolling_min(low_gpu, k_period)
    highest_high = gpu_rolling_max(high_gpu, k_period)

    rsv = cp.where(highest_high == lowest_high,
                   50.0,
                   100 * (close_gpu - lowest_low) / (highest_high - lowest_low))

    # K值计算 - EMA平滑
    k_values = gpu_ema(rsv, d_period)

    # D值计算 - K的EMA
    d_values = gpu_ema(k_values, d_period)

    # J值计算
    j_values = 3 * k_values - 2 * d_values

    return k_values, d_values, j_values
```

## 内存管理规范

### 批处理优化
```python
def batch_calculate_rsi_gpu(prices_batch: List[cp.ndarray],
                           period: int) -> List[cp.ndarray]:
    """批量RSI计算优化GPU内存使用"""

    # 堆叠为2D数组
    stacked_prices = cp.stack(prices_batch)

    # 批量计算
    batch_delta = cp.diff(stacked_prices, axis=1, prepend=stacked_prices[:, :1])
    batch_gain = cp.where(batch_delta > 0, batch_delta, 0.0)
    batch_loss = cp.where(batch_delta < 0, -batch_delta, 0.0)

    # ... 批量计算逻辑

    # 分离结果
    results = cp.split(batch_rsi, len(prices_batch))
    return results
```

### 内存清理策略
- 计算完成后立即清理临时数组
- 使用`cp.get_default_memory_pool().free_all_blocks()`
- 监控GPU内存使用情况
- 实现内存不足时的降级策略

## 性能基准

### 目标性能指标
- RSI计算: > 10x CPU速度
- MACD计算: > 8x CPU速度
- KDJ计算: > 12x CPU速度
- 内存使用: < 50% 同等CPU计算

### 基准测试规范
```python
def benchmark_gpu_rsi(prices_cpu, period=14):
    """RSI性能基准测试"""

    # CPU基准
    start = time.time()
    rsi_cpu = calculate_rsi_cpu(prices_cpu, period)
    cpu_time = time.time() - start

    # GPU测试
    prices_gpu = cp.asarray(prices_cpu)
    start = time.time()
    rsi_gpu = calculate_rsi_gpu(prices_gpu, period)
    gpu_time = time.time() - start

    # 性能计算
    speedup = cpu_time / gpu_time
    accuracy = cp.mean(cp.abs(rsi_gpu - rsi_cpu) < 0.01)

    return {
        'speedup': speedup,
        'accuracy': accuracy,
        'cpu_time': cpu_time,
        'gpu_time': gpu_time
    }
```

## 错误处理规范

### GPU特有错误处理
- CUDA运行时错误处理
- GPU内存不足处理
- 数值溢出检测
- 设备同步问题

### 容错机制
- 自动重试机制
- 降级到较小批次
- 最终CPU回退（仅作为最后手段）

## 集成规范

### 与现有系统集成
- 替换`gpu_nonprice_0700_backtest.py`中的计算方法
- 更新`simplified_system/src/indicators/gpu_indicators.py`
- 优化`src/gpu/nonprice_engine.py`

### 向后兼容性
- 保持相同函数签名
- 输出结果格式一致
- 错误处理兼容

## 验收标准

### 功能性要求
- [ ] 所有技术指标GPU实现完成
- [ ] 计算精度误差 < 0.01
- [ ] 性能提升 > 5x
- [ ] 内存使用高效

### 可靠性要求
- [ ] 零CPU回退（除非GPU不可用）
- [ ] 完整的错误处理
- [ ] 内存泄漏防护
- [ ] 长时间运行稳定

### 性能要求
- [ ] GPU利用率 > 80%
- [ ] 计算延迟 < 100ms
- [ ] 支持大数据集（> 1M数据点）
- [ ] 批处理优化有效