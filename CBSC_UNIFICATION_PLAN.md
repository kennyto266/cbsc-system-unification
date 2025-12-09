# 🔄 CBSC模块统一计划

## **📊 当前状况分析**

### **发现的问题**
- **23个cbsc_*.py文件**散布在根目录
- **src目录**已有结构化的CBSC模块
- **功能重复**: Marimo实验文件和正式实现并存

### **现有结构化模块**
```
src/
├── data_adapters/cbsc_adapter.py      # CBSC数据适配器
├── models/cbsc_models.py             # CBSC数据模型
└── risk_management/cbsc_risk.py      # CBSC风险管理
```

### **根目录CBSC文件分类**
1. **Marimo实验文件** (12个): cbsc_*_lab.py, cbsc_*_marimo.py
2. **分析和报告文件** (6个): cbsc_*_analysis.py, cbsc_*_report.py
3. **测试和演示文件** (3个): cbsc_*_test.py, cbsc_*_demo.py
4. **核心实现文件** (2个): 可能包含重要业务逻辑

## **🎯 统一策略**

### **阶段1: 分类和移动**
- **实验文件** → `notebooks/cbsc_experiments/`
- **测试文件** → `tests/cbsc/`
- **报告文件** → `reports/cbsc/`
- **核心文件** → 评估后决定保留或整合

### **阶段2: 功能整合**
- 分析重复代码，提取通用功能
- 将实验性功能迁移到src/模块
- 保持Marimo交互式实验的独立性

### **阶段3: API统一**
- 建立统一的CBSC策略接口
- 标准化数据格式和配置
- 创建工厂模式支持不同策略类型

## **📁 建议的最终结构**

```
src/cbsc/
├── __init__.py                    # 统一入口
├── core.py                        # 核心CBSC功能
├── strategies/
│   ├── __init__.py
│   ├── base_strategy.py           # 基础策略类
│   ├── direct_rsi.py             # 直接RSI策略
│   ├── sentiment_momentum.py     # 情绪动量策略
│   ├── composite_index.py        # 复合指标策略
│   └── volatility_adjusted.py    # 波动率调整策略
├── data/
│   ├── __init__.py
│   ├── processor.py              # 数据处理
│   └── validator.py              # 数据验证
└── utils/
    ├── __init__.py
    ├── indicators.py             # 技术指标
    └── helpers.py                # 工具函数
```

## **⚠️ 注意事项**
1. **保留核心功能**: 确保不破坏现有功能
2. **渐进式迁移**: 分步骤进行，每步验证
3. **配置兼容**: 保持配置文件向后兼容
4. **测试覆盖**: 迁移后添加完整测试

## **🚀 执行计划**
1. **Day 1**: 分析现有文件，识别核心功能
2. **Day 2**: 移动实验文件到notebooks目录
3. **Day 3**: 整合重复的策略实现
4. **Day 4**: 创建统一的CBSC模块
5. **Day 5**: 测试和文档更新