# Archive Directory
# 归档目录

此目录包含从主项目中归档的旧代码和实验性文件。

## 归档原因

这些文件被归档是因为：
- 功能已被Simplified System中的新实现取代
- 重复或过时的代码
- 实验性功能不再维护
- 为简化项目结构

## 归档内容

### Optimizers (优化器文件)
- `massive_optimizer.py` - 大规模参数优化器的早期版本
- `enhanced_optimizer.py` - 增强优化器，功能已集成到新系统
- `comprehensive_optimizer.py` - 综合优化器，功能已重构
- `real_optimizer.py` - 真实数据优化器，已替换为新的实现
- `gpu_optimizer.py` - GPU优化器，简化版已集成到新系统
- `balanced_risk_optimizer.py` - 风险平衡优化器，功能已重构
- `clean_real_optimizer.py` - 清理版真实数据优化器
- `authentic_real_data_optimizer.py` - 真实数据优化器验证版

### Backtest Files (回测文件)
- `test_backtest*.py` - 各种测试回测脚本
- `vectorbt_*.py` - VectorBT实现的重复版本
- `simple_backtest*.py` - 简单回测的多个版本
- `*_backtest_*.py` - 特定回测实现

### Demo and Example Files (演示和示例文件)
- `demo_*.py` - 演示脚本
- `example_*.py` - 示例代码
- `simple_*.py` - 简单实现版本

### Test Files (测试文件)
- `test_*.py` - 单元测试和集成测试
- `*_test.py` - 测试脚本

### Experimental Features (实验性功能)
- `experimental_*.py` - 实验性功能
- `phase*_*.py` - 开发阶段的临时实现

## 恢复指南

如果需要从归档中恢复某个功能：

1. 检查Simplified System是否已有替代实现
2. 如果没有，可以参考归档代码
3. 将相关代码适配到新架构中
4. 更新导入路径和依赖

## 版本信息

归档时间: 2025-11-26
原项目版本: 重构前的复杂版本
新版本: Simplified System (核心文件 ~50个)

---

注意：这些文件仅供参考，不建议直接在生产环境中使用。