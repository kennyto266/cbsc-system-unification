# OpenSpec Change Proposal: 启用真实GPU计算功能

## 变更概述

解决GPU非价格回测系统中的核心计算问题，实现真正的GPU加速功能，确保0700.HK回测能够充分利用RTX 5070 Ti的GPU性能。

**Change ID**: `enable-real-gpu-computation`
**创建日期**: 2025-11-24
**优先级**: Critical
**预计工作量**: 3-4天

## 问题描述

### 当前问题
1. **GPU计算失效**: GPU检测正常但实际利用率仅7%
2. **过度CPU回退**: 任何计算错误都立即回退到CPU
3. **数据格式不兼容**: numpy/cupy/pandas数据类型混乱
4. **缺少实际GPU负载**: 系统运行但GPU基本闲置

### 业务影响
- 无法发挥GPU硬件性能优势
- 回测速度远低于预期
- 浪费高端GPU资源
- 用户失去对GPU功能的信任

## 解决方案

### 核心策略
1. **完全重写GPU数据管道**: 确保数据格式完全兼容
2. **实现渐进式降级**: 从GPU→混合→CPU的智能切换
3. **添加GPU性能监控**: 实时验证GPU真正被使用
4. **优化CUDA内核**: 针对量化计算场景优化

### 技术实现

#### Phase 1: 数据标准化 (1天)
```python
# 统一GPU数据接口
class GPUDataPipeline:
    def normalize_for_gpu(self, data) -> cp.ndarray:
        # 完整的数据转换和验证管道
```

#### Phase 2: 计算核心重写 (2天)
```python
# 真正的GPU计算实现
class RealGPUComputation:
    def rsi_gpu_accelerated(self, prices, period):
        # 纯GPU RSI计算，无CPU回退
```

#### Phase 3: 性能验证 (1天)
```python
# GPU性能监控系统
class GPUPerformanceValidator:
    def verify_gpu_usage(self):
        # 确保GPU真正被使用
```

## 验收标准

### 功能性
- [ ] 0700.HK完整回测使用GPU计算
- [ ] 所有技术指标（RSI、MACD等）GPU实现
- [ ] GPU利用率 > 80%
- [ ] 计算速度提升 > 5x

### 性能指标
- [ ] 内存利用率 > 70%
- [ ] CPU回退率 < 5%
- [ ] 错误处理不影响GPU计算
- [ ] 完整的性能报告生成

### 质量保证
- [ ] 详细的GPU性能监控
- [ ] 完整的错误日志和诊断
- [ ] 与CPU结果的一致性验证
- [ ] 向后兼容性保持

## 风险分析

### 技术风险
- **CuPy兼容性**: 可能遇到CuPy版本问题
- **CUDA内存**: 大数据集可能超出GPU内存
- **数值精度**: GPU浮点计算精度差异

### 缓解措施
- 实现完整的错误处理和恢复机制
- 提供分批处理和内存优化
- 进行数值精度对比验证

## 实现计划

### Day 1: 数据管道重构
- 修复数据类型转换问题
- 实现统一的GPU数据接口
- 添加数据验证和预处理

### Day 2: 核心GPU计算
- 重写RSI、MACD等核心指标GPU实现
- 实现真正的CUDA计算管道
- 移除过度的CPU回退机制

### Day 3: 性能优化
- 优化GPU内存使用
- 实现批处理和并行计算
- 添加性能监控和报告

### Day 4: 测试验证
- 完整的0700.HK回测验证
- 性能基准测试
- 文档和使用指南更新

## 成功指标

**Primary**: 0700.HK回测GPU利用率 > 80%，速度提升 > 5x
**Secondary**: 所有技术指标GPU计算正常，完整的性能报告
**Tertiary**: 详细的监控和诊断功能，用户友好的错误提示

## 相关文件

- `gpu_nonprice_0700_backtest.py` - 需要修复的主要文件
- `src/gpu/nonprice_engine.py` - GPU引擎优化
- `simplified_system/src/indicators/gpu_indicators.py` - GPU指标实现
- `openspec/changes/enable-real-gpu-computation/` - 本变更文档

## 审批流程

1. 技术评审：确认技术可行性和实现方案
2. 性能验证：GPU实际使用效果确认
3. 用户验收：0700.HK回测结果验证
4. 生产部署：替换现有GPU计算系统