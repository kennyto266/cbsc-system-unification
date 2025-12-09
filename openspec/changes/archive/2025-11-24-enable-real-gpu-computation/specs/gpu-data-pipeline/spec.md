# GPU数据管道技术规范

## 概述

标准化GPU数据管道，确保所有输入数据格式完全兼容GPU计算，消除数据类型不兼容导致的CPU回退问题。

## 接口规范

### 核心接口: `GPUDataValidator`

```python
class GPUDataValidator:
    def __init__(self, gpu_device=0):
        self.device = gpu_device
        self.compatible_dtypes = [
            cp.float32, cp.float64,
            cp.int32, cp.int64
        ]

    def validate_and_convert(self, data: Union[np.ndarray, pd.Series, list]) -> cp.ndarray:
        """
        验证输入数据并转换为CuPy数组

        Args:
            data: 输入数据（支持多种格式）

        Returns:
            cp.ndarray: GPU兼容数组

        Raises:
            ValueError: 数据格式不支持
            RuntimeError: GPU内存不足
        """
```

### 数据类型映射

| 输入类型 | 输出类型 | 转换逻辑 |
|---------|----------|----------|
| `np.ndarray` | `cp.ndarray` | 直接转换 |
| `pd.Series` | `cp.ndarray` | 提取values后转换 |
| `list` | `cp.ndarray` | 先转numpy再转GPU |
| `pd.DataFrame` | `Dict[str, cp.ndarray]` | 列级转换 |

## 技术要求

### 内存连续性
- 所有GPU数组必须内存连续
- 支持`cp.ascontiguousarray()`优化
- 自动检测和修复内存布局

### 数据精度
- 价格数据使用`float32`精度
- 索引数据使用`int32`
- 信号数据使用`float32`

### 错误处理
- 数据维度验证
- GPU内存检查
- 数值范围验证
- 时间序列完整性检查

## 性能指标

- 转换延迟 < 10ms
- 内存开销 < 5%
- 100%数据格式兼容
- 零数据丢失

## 集成要求

与现有系统集成:
- `src/gpu/nonprice_engine.py`
- `simplified_system/src/indicators/gpu_indicators.py`
- `gpu_nonprice_0700_backtest.py`

## 测试规范

### 单元测试
- [ ] 各种输入格式转换测试
- [ ] 错误数据处理测试
- [ ] 内存连续性验证
- [ ] 性能基准测试

### 集成测试
- [ ] 完整数据管道测试
- [ ] 多数据源整合测试
- [ ] 内存压力测试
- [ ] 长时间运行稳定性测试