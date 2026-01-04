# Simplified System 项目知识库

**Generated:** 2025-01-03 **System:** 简化量化系统 (Alpha Factors + VectorBT)

## OVERVIEW

轻量级量化交易系统，专注于Alpha因子挖掘、VectorBT回测和实时仪表板。简化的架构便于快速原型开发和策略验证。

## STRUCTURE

```
simplified_system/
├── 📊 Alpha因子系统
│   └── src/alpha/                                  # Alpha因子引擎
│       ├── alpha_factors/                            # 因子定义
│       ├── factor_analyzer/                          # 因子分析器
│       ├── factor_engine/                            # 因子计算引擎
│       └── factor_portfolio/                         # 投资组合构建
├── 📈 回测引擎
│   └── notebooks/                                  # VectorBT notebooks
├── 🎯 仪表板
│   └── src/                                       # Streamlit/Vite仪表板
├── 🗄️ 数据
│   ├── data/                                       # 数据存储
│   └── models/                                     # 数据模型
├── 🔧 配置
│   └── config/                                     # 配置文件
├── 🧪 测试
│   └── tests/                                      # 测试套件
├── 📚 文档
│   └── docs/                                       # 文档目录
└── 📦 部署
    └── kubernetes/                                 # K8s配置
```

## WHERE TO LOOK

| Task          | Location                     | Notes                 |
| ------------- | ---------------------------- | --------------------- |
| Alpha因子定义 | `src/alpha/alpha_factors/`   | 因子实现和计算逻辑    |
| 因子分析      | `src/alpha/factor_analyzer/` | 因子有效性分析        |
| 因子回测      | `notebooks/`                 | VectorBT回测notebooks |
| 实时仪表板    | `src/` 或根目录Python文件    | Streamlit/Vite界面    |
| 数据配置      | `config/`                    | 数据源、参数配置      |
| API监控       | `api_maintenance_monitor.py` | API健康检查           |
| 测试          | `tests/`                     | pytest测试套件        |

## CONVENTIONS

**架构设计：**

- Alpha因子：使用pandas和numpy计算，基于OHLCV数据
- 回测框架：VectorBT (向量化回测)
- 仪表板：Streamlit (快速原型) 或 Vite (生产)
- 配置管理：JSON/YAML格式

**代码风格：**

- Python 3.10+，类型提示优先
- 函数式设计，纯函数优先
- 模块化：每个因子独立文件
- 数据验证：使用Pydantic模型

## ANTI-PATTERNS (THIS PROJECT)

- ❌ **不要**在主线程执行大规模回测 - 使用VectorBT向量化操作
- ❌ **不要**硬编码因子参数 - 使用配置文件
- ❌ **不要**忽略数据质量检查 - 必须验证数据完整性
- ❌ **不要**使用全局变量 - 使用依赖注入或配置对象

## UNIQUE STYLES

**Alpha因子流程：**

1. 因子定义：`src/alpha/alpha_factors/` - 基于价格/成交量/技术指标
2. 因子计算：`src/alpha/factor_engine/` - 批量计算多股票因子
3. 因子分析：`src/alpha/factor_analyzer/` - IC/IR统计，分组回测
4. 投资组合：`src/alpha/factor_portfolio/` - 多因子组合优化

**回测流程：**

```python
# VectorBT快速回测
import vectorbt as vbt
import pandas as pd

price_data = pd.DataFrame(...)
signals = generate_signals(price_data)
portfolio = vbt.Portfolio.from_signals(
    price_data,
    entries=signals['buy'],
    exits=signals['sell'],
    freq='1D'
)
stats = portfolio.stats()
```

**数据管道：**

- 数据源：支持本地CSV、数据库、API
- 数据清洗：缺失值处理、异常值检测
- 数据缓存：避免重复计算

## COMMANDS

```bash
# Alpha因子演示
python advanced_alpha_factor_demo.py

# 因子优化
python advanced_alpha_factor_demo.py --optimize

# API监控
python api_maintenance_monitor.py

# 启动仪表板
streamlit run src/dashboard.py

# 运行测试
pytest tests/ -v

# 运行特定notebook
jupyter notebook notebooks/alpha_factor_backtest.ipynb
```

## NOTES

**关键依赖：**

- VectorBT：向量化回测引擎
- Pandas/NumPy：数据计算
- Streamlit：快速原型仪表板
- Pydantic：数据验证

**数据文件位置：**

- 原始数据：`data/`
- 配置文件：`config/`
- 回测结果：`optimization_results/`
- 报告：根目录`*_REPORT.md`

**性能优化：**

- 使用向量化操作（VectorBT, NumPy）
- 批量计算多股票因子
- 数据缓存避免重复计算

**与主系统(CODEX--)关系：**

- simplified_system是CODEX--的轻量版本
- 专注于Alpha因子挖掘，而非完整交易系统
- 适合快速原型和策略验证
- 可复用CODEX--的数据源和API
