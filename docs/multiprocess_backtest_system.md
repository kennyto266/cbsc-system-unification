# 多进程回测系统文档 (Multiprocess Backtest System Documentation)

## 概述

多进程回测系统是 CBSC 量化交易系统的核心组件，提供真正的高性能并行回测能力。通过利用多 CPU 核心和智能资源管理，显著提升回测效率。

### 核心特性

- ✅ **真正的多进程并行**：使用 `ProcessPoolExecutor`，而非简单的线程池
- ✅ **智能资源管理**：根据系统负载自动调整进程数量
- ✅ **多级并行策略**：支持策略级/符号级/参数级/混合模式
- ✅ **自动容错与恢复**：进程回收机制防止内存泄漏
- ✅ **实时进度监控**：CPU、内存、任务进度的实时跟踪
- ✅ **高性能结果聚合**：统一的性能指标和结果汇总

---

## 架构设计

### 系统架构

```
┌─────────────────────────────────────────────────────┐
│         FastAPI Backend (Port 3007)          │
│              ↓                                 │
│  ┌────────────────────────────────────┐       │
│  │ Multiprocess Backtest API     │       │
│  │  - 任务提交                    │       │
│  │  - 状态查询                  │       │
│  │  - 结果获取                    │       │
│  │  - 性能监控                    │       │
│  └────────────────────────────────────┘       │
│              ↓                                 │
│  ┌────────────────────────────────────┐       │
│  │ MultiprocessBacktestEngine        │       │
│  │                                 │       │
│  │  - DynamicProcessPool            │       │
│  │  - EnhancedBacktestEngine       │       │
│  │  - ParallelProcessor             │       │
│  └────────────────────────────────────┘       │
│              ↓                                 │
│     多进程并行执行                         │
└─────────────────────────────────────────────────────┘
```

### 核心组件

#### 1. MultiprocessBacktestEngine (`src/backtest/multiprocess_engine.py`)

**职责**：多进程回测引擎的统一接口

**核心方法**：

- `run_backtests(configs)`: 执行批量回测
- `_execute_parallel_backtests(configs)`: 根据并行级别分发任务
- `_execute_strategy_level()`: 策略级并行（每个策略一个进程）
- `_execute_symbol_level()`: 符号级并行（每个标的进程）
- `_execute_parameter_level()`: 参数级并行（每组参数一个进程）
- `_execute_hybrid()`: 混合模式（自动选择并行级别）

#### 2. DynamicProcessPool (`src/backtest/parallel/process_pool.py`)

**职责**：动态进程池管理

**核心特性**：

- 自动扩容/缩容（基于队列深度和系统负载）
- 进程回收机制（防止内存泄漏）
- 资源监控（CPU、内存、磁盘 I/O）
- 健康检查（进程心跳、错误率监控）

#### 3. EnhancedBacktestEngine (`src/backtest/enhanced_backtest_engine.py`)

**职责**：增强回测引擎

**核心功能**：

- 风险管理（VaR、最大回撤、杠杆限制）
- 动态调整（波动率目标、仓位缩放）
- 实时监控（风险阈值、调整类型）
- 压力测试（极端场景模拟）
- 蒙特卡洛模拟（蒙特卡洛分析）

#### 4. Multiprocess Backtest API (`src/api/backtest_multiprocess_api.py`)

**职责**：提供 RESTful API 接口

**核心端点**：

- `POST /api/v1/backtest/multiprocess/submit`: 提交多进程回测任务
- `GET /api/v1/backtest/multiprocess/status/{task_id}`: 查询任务状态
- `DELETE /api/v1/backtest/multiprocess/cancel/{task_id}`: 取消任务
- `GET /api/v1/backtest/multiprocess/results/{task_id}`: 获取任务结果
- `GET /api/v1/backtest/multiprocess/performance/{task_id}`: 获取性能指标
- `POST /api/v1/backtest/multiprocess/benchmark`: 性能对比测试
- `GET /api/v1/backtest/multiprocess/health`: 健康检查

---

## API 使用指南

### 1. 提交多进程回测任务

**端点**：`POST /api/v1/backtest/multiprocess/submit`

**请求示例**：

```json
{
  "parallel_level": "strategy",
  "max_workers": -1,
  "max_concurrent": 10,
  "max_memory_gb": 4.0,
  "enable_auto_scaling": true,
  "enable_progress_monitoring": true,
  "save_results": true,
  "output_dir": "backtest_results",
  "backtest_configs": [
    {
      "strategy_id": "strategy_001",
      "strategy_type": "ma_crossover",
      "symbols": ["0700.HK", "0700.HK"],
      "start_date": "2024-01-01",
      "end_date": "2024-12-31",
      "initial_capital": 100000.0,
      "parameters": {
        "short_period": 20,
        "long_period": 50
      }
    },
    {
      "strategy_id": "strategy_002",
      "strategy_type": "rsi_strategy",
      "symbols": ["0700.HK"],
      "start_date": "2024-01-01",
      "end_date": "2024-12-31",
      "initial_capital": 100000.0,
      "parameters": {
        "rsi_period": 14,
        "oversold_level": 30,
        "overbought_level": 70
      }
    }
  ]
}
```

**响应示例**：

```json
{
  "task_id": "550e8400-e29b-41d4-a7c8-8a4",
  "status": "submitted",
  "message": "Task submitted successfully with 2 backtest configurations",
  "parallel_level": "strategy",
  "max_workers": 32,
  "estimated_completion_time": 60.0
}
```

### 2. 查询任务状态

**端点**：`GET /api/v1/backtest/multiprocess/status/{task_id}`

**响应示例**：

```json
{
  "task_id": "550e8400-e29b-41d4-a7c8-8a4",
  "status": "running",
  "total_backtests": 10,
  "completed_backtests": 6,
  "failed_backtests": 0,
  "progress": 0.6,
  "total_execution_time": null,
  "remaining_time": 24.0,
  "results": null
}
```

### 3. 获取任务结果

**端点**：`GET /api/v1/backtest/multiprocess/results/{task_id}`

**响应示例**：

```json
{
  "task_id": "550e8400-e29b-41d4-a7c8-8a4",
  "status": "completed",
  "summary": {
    "total_backtests": 10,
    "completed_backtests": 10,
    "failed_backtests": 0,
    "success_rate": 1.0
  },
  "performance": {
    "parallel_speedup": 3.2,
    "parallel_efficiency": 78.5,
    "total_execution_time": 31.25,
    "average_execution_time": 3.125,
  },
  "system_resources": {
    "peak_memory_gb": 3.8,
    "average_cpu_percent": 85.2,
    "max_cpu_percent": 98.5
  },
  "results": [
    {
      "status": "completed",
      "config": { "strategy_id": "strategy_001", ... },
      "result": {
        "total_return": 15.6,
        "sharpe_ratio": 1.8,
        "max_drawdown": -8.2,
        ...
      }
    }
  ]
}
```

### 4. 性能对比测试

**端点**：`POST /api/v1/backtest/multiprocess/benchmark`

**说明**：对比单进程与多进程的执行性能

**测试场景**：

1. 单进程顺序执行（baseline）
2. 多进程并行执行（2 workers）
3. 多进程完整并行（所有 CPU 核心）

**结果示例**：

```json
{
  "benchmark_type": "parallel_vs_single",
  "results": {
    "single_process": {
      "execution_time": 300.5,
      "backtests_completed": 10
    },
    "multi_process_small": {
      "execution_time": 150.2,
      "backtests_completed": 10,
      "speedup": 2.0,
      "workers": 2
    },
    "multi_process_full": {
      "execution_time": 93.8,
      "backtests_completed": 10,
      "speedup": 3.2,
      "workers": 8
    }
  },
  "conclusion": "Parallel processing provides 3.2x speedup with 8 workers"
}
```

---

## 并行级别选择指南

### STRATEGY_LEVEL（策略级并行）

**适用场景**：

- 多个不同的策略需要回测
- 每个策略独立，不需要共享状态
- 回测配置数量适中（1-20）

**执行方式**：

- 每个策略分配一个独立进程
- 所有策略并行执行

**优势**：

- 隔离性好（一个失败不影响其他）
- 易于调试（单个进程问题易定位）

**示例**：

```python
request = MultiprocessBacktestRequest(
    backtest_configs=[config1, config2, config3],
    parallel_level=ParallelLevel.STRATEGY_LEVEL,
    max_workers=4
)
```

### SYMBOL_LEVEL（符号级并行）

**适用场景**：

- 单一策略，多个交易标的（symbols）
- 每个标的独立回测

**执行方式**：

- 每个标的分配一个独立进程
- 多个标的并行回测同一策略

**优势**：

- 适合多资产组合回测
- 资源利用率高

**示例**：

```python
request = MultiprocessBacktestRequest(
    backtest_configs=[{
        'strategy_id': 'strategy_001',
        'symbols': ['0700.HK', '9988.HK', 'AAPL']
    }],
    parallel_level=ParallelLevel.SYMBOL_LEVEL,
    max_workers=8
)
```

### PARAMETER_LEVEL（参数级并行）

**适用场景**：

- 参数优化场景（网格搜索、贝叶斯优化）
- 细粒度并行（每组参数独立）

**执行方式**：

- 每组参数分配一个独立进程
- 最大并行度

**优势**：

- 最细粒度并行
- 适合参数优化

**示例**：

```python
configs = []
for short_period in [10, 20, 30]:
    for long_period in [50, 60, 90]:
        configs.append({
            'strategy_id': 'strategy_001',
            'parameters': {
                'short_period': short_period,
                'long_period': long_period
            }
        })

request = MultiprocessBacktestRequest(
    backtest_configs=configs,
    parallel_level=ParallelLevel.PARAMETER_LEVEL,
    max_workers=16
)
```

### HYBRID（混合模式）

**适用场景**：

- 混合场景（既有策略差异，又有参数差异）
- 需要系统智能选择

**智能选择规则**：

- 配置数量 < 10：使用 `PARAMETER_LEVEL`（最细粒度）
- 配置数量 10-50：使用 `STRATEGY_LEVEL`（策略级）
- 配置数量 > 50：使用 `SYMBOL_LEVEL`（符号级）

**优势**：

- 自动优化
- 适应不同规模

**示例**：

```python
request = MultiprocessBacktestRequest(
    backtest_configs=configs,
    parallel_level=ParallelLevel.HYBRID,  # 自动选择
    max_workers=-1  # 自动检测 CPU 核心
)
```

---

## 性能优化指南

### 1. 选择合适的并行级别

| 场景               | 推荐级别                       | 理由                 |
| ------------------ | ------------------------------ | -------------------- |
| 少量策略（<10）    | STRATEGY_LEVEL                 | 粒度适中，易于管理   |
| 少量标的（<10）    | SYMBOL_LEVEL                   | 充分利用 I/O 并行    |
| 参数优化（>10 组） | PARAMETER_LEVEL                | 最细粒度，最大化并行 |
| 大规模回测（>50）  | STRATEGY_LEVEL 或 SYMBOL_LEVEL | 平衡开销和并行度     |
| 混合场景           | HYBRID                         | 系统自动优化         |

### 2. 设置进程数量

**自动检测（推荐）**：

```python
request = MultiprocessBacktestRequest(
    max_workers=-1  # 自动检测 CPU 核心数
)
```

**手动设置**：

```python
# 保守设置：保留系统资源
request = MultiprocessBacktestRequest(
    max_workers=max(1, cpu_count - 2)
)

# 激进设置：最大化利用 CPU
request = MultiprocessBacktestRequest(
    max_workers=cpu_count
)

# 内存受限环境
request = MultiprocessBacktestRequest(
    max_workers=int(cpu_count / 2),  # 使用一半核心
    max_memory_gb=2.0  # 限制内存
)
```

### 3. 资源限制

**内存限制**：

```python
request = MultiprocessBacktestRequest(
    max_memory_gb=4.0,  # 每个进程最多使用 4GB
)
```

**并发控制**：

```python
request = MultiprocessBacktestRequest(
    max_concurrent=10,  # 同时最多运行 10 个任务
)
```

### 4. 自动扩容

```python
request = MultiprocessBacktestRequest(
    enable_auto_scaling=True,  # 启用自动扩容
    scaling_check_interval=5.0,  # 每 5 秒检查一次
)
```

**工作原理**：

- 队列深度 > 2x 工作进程数 → 扩容
- CPU 负载 > 80% → 缩容
- 内存使用 > 80% → 缩容

---

## 使用示例

### Python 客户端示例

#### 示例 1：提交批量回测任务

```python
import asyncio
import httpx
from datetime import datetime, date

async def submit_batch_backtest():
    """
    提交批量回测任务
    """
    async with httpx.AsyncClient() as client:
        # 准备回测配置
        configs = [
            {
                "strategy_id": "ma_crossover_20_50",
                "strategy_type": "ma_crossover",
                "symbols": ["0700.HK"],
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
                "initial_capital": 100000.0,
                "parameters": {
                    "short_period": 20,
                    "long_period": 50
                }
            },
            {
                "strategy_id": "rsi_strategy_14_30_70",
                "strategy_type": "rsi_strategy",
                "symbols": ["0700.HK"],
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
                "initial_capital": 100000.0,
                "parameters": {
                    "rsi_period": 14,
                    "oversold_level": 30,
                    "overbought_level": 70
                }
            }
        ]

        # 提交任务
        request_data = {
            "parallel_level": "strategy",
            "max_workers": -1,  # 自动检测
            "enable_auto_scaling": True,
            "save_results": True,
            "backtest_configs": configs
        }

        response = await client.post(
            "http://localhost:3007/api/v1/backtest/multiprocess/submit",
            json=request_data
        )

        result = response.json()
        task_id = result['task_id']

        print(f"任务已提交: {task_id}")

        # 轮询任务状态
        while True:
            status_response = await client.get(
                f"http://localhost:3007/api/v1/backtest/multiprocess/status/{task_id}"
            )
            status_data = status_response.json()

            print(f"状态: {status_data['status']}")
            print(f"进度: {status_data['progress']:.1%}")

            if status_data['status'] in ['completed', 'failed', 'cancelled']:
                break

            await asyncio.sleep(5)  # 每 5 秒查询一次

        # 获取结果
        if status_data['status'] == 'completed':
            results_response = await client.get(
                f"http://localhost:3007/api/v1/backtest/multiprocess/results/{task_id}"
            )
            results_data = results_response.json()

            print("\n任务完成!")
            print(f"总数: {results_data['summary']['total_backtests']}")
            print(f"完成: {results_data['summary']['completed_backtests']}")
            print(f"加速比: {results_data['performance']['parallel_speedup']:.2f}x")

if __name__ == "__main__":
    asyncio.run(submit_batch_backtest())
```

#### 示例 2：参数优化（网格搜索）

```python
import asyncio
import httpx
from itertools import product

async def parameter_optimization():
    """
    参数优化示例：网格搜索
    """
    # 定义参数网格
    short_periods = [10, 15, 20, 25, 30]
    long_periods = [40, 50, 60, 80, 100]

    # 生成所有参数组合
    configs = []
    for short, long in product(short_periods, long_periods):
        configs.append({
            "strategy_id": "ma_crossover_optimization",
            "strategy_type": "ma_crossover",
            "symbols": ["0700.HK"],
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "initial_capital": 100000.0,
            "parameters": {
                "short_period": short,
                "long_period": long
            }
        })

    # 提交参数优化任务
    async with httpx.AsyncClient() as client:
        request_data = {
            "parallel_level": "parameter",  # 参数级并行（最细粒度）
            "max_workers": -1,  # 自动检测
            "backtest_configs": configs
        }

        print(f"提交 {len(configs)} 组参数优化任务...")
        response = await client.post(
            "http://localhost:3007/api/v1/backtest/multiprocess/submit",
            json=request_data
        )

        result = response.json()
        print(f"任务 ID: {result['task_id']}")
        print(f"估计完成时间: {result.get('estimated_completion_time', 'N/A')} 秒")
```

#### 示例 3：性能基准测试

```python
import asyncio
import httpx

async def benchmark_performance():
    """
    性能基准测试示例
    """
    test_config = {
        "strategy_id": "test_strategy",
        "strategy_type": "ma_crossover",
        "symbols": ["0700.HK"],
        "start_date": "2024-01-01",
        "end_date": "2024-06-30",
        "initial_capital": 100000.0,
        "parameters": {
            "short_period": 20,
            "long_period": 50
        }
    }

    async with httpx.AsyncClient() as client:
        request_data = {
            "parallel_level": "strategy",
            "max_workers": -1,  # 自动检测
            "backtest_configs": [test_config]  # 测试一个配置
        }

        print("启动性能基准测试...")
        response = await client.post(
            "http://localhost:3007/api/v1/backtest/multiprocess/benchmark",
            json=request_data
        )

        result = response.json()
        print("\n基准测试结果:")
        print(f"类型: {result['benchmark_type']}")

        for key, value in result['results'].items():
            print(f"\n{key}:")
            if isinstance(value, dict) and 'execution_time' in value:
                print(f"  执行时间: {value['execution_time']:.2f}s")
                if 'speedup' in value:
                    print(f"  加速比: {value['speedup']:.2f}x")

        print(f"\n{result['conclusion']}")
```

### cURL 示例

#### 提交任务

```bash
curl -X POST http://localhost:3007/api/v1/backtest/multiprocess/submit \
  -H "Content-Type: application/json" \
  -d '{
    "parallel_level": "strategy",
    "max_workers": -1,
    "backtest_configs": [
      {
        "strategy_id": "strategy_001",
        "strategy_type": "ma_crossover",
        "symbols": ["0700.HK"],
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "initial_capital": 100000.0,
        "parameters": {
          "short_period": 20,
          "long_period": 50
        }
      }
    ]
  }'
```

#### 查询状态

```bash
curl http://localhost:3007/api/v1/backtest/multiprocess/status/550e8400-e29b-41d4-a7c8-8a4
```

#### 获取结果

```bash
curl http://localhost:3007/api/v1/backtest/multiprocess/results/550e8400-e29b-41d4-a7c8-8a4
```

---

## 性能测试指南

### 运行性能测试

使用提供的测试脚本：

```bash
# 进入项目根目录
cd C:\Users\Penguin8n\CODEX--

# 运行性能测试
python tests/multiprocess_performance_test.py
```

### 测试输出解读

测试脚本会输出以下信息：

#### 1. 单进程执行（baseline）

```
==========================================================
测试 1: 单进程顺序执行 (baseline)
==========================================================
初始资源: CPU=5.0%, Memory=2.1GB
结束资源: CPU=95.2%, Memory=3.8GB
执行时间: 120.5s
完成的回测: 10/10
成功率: 100.0%
```

#### 2. 多进程并行（2 workers）

```
==========================================================
测试 2: 多进程并行执行 (2 workers)
==========================================================
初始资源: CPU=8.0%, Memory=2.1GB
结束资源: CPU=92.5%, Memory=3.9GB
执行时间: 65.3s
完成的回测: 10/10
成功率: 100.0%
并行加速比: 1.85x
并行效率: 92.5%
```

#### 3. 多进程完整并行（所有 CPU 核心）

```
==========================================================
测试 3: 多进程完整并行 (8 workers)
==========================================================
初始资源: CPU=12.0%, Memory=2.1GB
结束资源: CPU=89.3%, Memory=4.1GB
执行时间: 38.7s
完成的回测: 10/10
成功率: 100.0%
并行加速比: 3.11x
并行效率: 78.5%
```

### 性能指标说明

#### 并行加速比 (Parallel Speedup)

```python
speedup = 单进程时间 / 多进程时间

# 理论最大值 = CPU 核心数
# 实际值通常在 2.5x - 4x 之间
```

#### 并行效率 (Parallel Efficiency)

```python
efficiency = (实际加速比 / 理论最大加速比) * 100%

# > 70%: 优秀
# 50-70%: 良好
# 30-50%: 一般
# < 30%: 需要优化
```

---

## 集成到现有系统

### 1. 注册 API 路由

在 `backend/main.py` 中注册多进程回测 API：

```python
from src.api.backtest_multiprocess_api import router as multiprocess_router

app.include_router(multiprocess_router)
```

### 2. 更新前端（Textual）

在 Textual TUI 中添加多进程回测支持：

```python
from textual.widgets import Button, DataTable, ProgressBar
import httpx

class BacktestScreen(Screen):
    def compose(self):
        yield Header("多进程回测")
        yield Button("提交批量回测", id="submit-btn")
        yield DataTable(
            id="backtest-table",
            columns=["任务 ID", "状态", "完成数", "加速比"],
            rows=[]
        )

    async def on_submit_button_pressed(self):
        # 提交回测任务
        configs = self._get_configs_from_ui()
        await self._submit_backtest(configs)

        # 切换到监控界面
        self.app.push_screen("BacktestMonitorScreen")
```

---

## 常见问题

### Q1: 多进程 vs 线程池，哪个更好？

**A**: 多进程明显更好：

**原因**：

- Python GIL（全局解释器锁）限制多线程性能
- I/O 密集型任务可以使用线程
- CPU 密集型任务必须使用进程
- 回测是 CPU 密集型 + 少量 I/O

**性能差异**：

- 多线程：通常 1-2x 加速
- 多进程：2-4x 或更高加速

### Q2: 如何选择 `max_workers`？

**A**: 一般规则：

```python
# 保守设置（保留系统资源）
max_workers = max(1, cpu_count - 2)

# 平衡设置
max_workers = cpu_count

# 激进设置
max_workers = min(cpu_count * 2, 32)
```

**注意事项**：

- 进程数过多会增加上下文切换开销
- 每个进程至少需要 1GB 内存
- 考虑其他系统进程的内存需求

### Q3: 如何监控多进程回测？

**A**: 三种方式：

1. **API 查询**：定期调用 `/status/{task_id}` 端点
2. **WebSocket**：实时推送进度更新（推荐）
3. **日志文件**：查看系统日志

### Q4: 内存不足怎么办？

**A**: 优化策略：

1. **减少并发数**：降低 `max_concurrent`
2. **启用数据分片**：分批处理数据
3. **限制单任务内存**：设置 `max_memory_gb`
4. **禁用自动扩容**：设置 `enable_auto_scaling=False`

### Q5: 如何调试多进程回测？

**A**:

1. **单进程调试**：设置 `max_workers=1`，顺序执行
2. **日志级别**：设置日志级别为 DEBUG
3. **结果验证**：对比多进程与单进程结果
4. **资源监控**：观察 CPU/内存使用情况

---

## 最佳实践

### 1. 数据预处理

```python
# 在提交前预处理数据，减少进程内处理时间
# 例如：过滤无效数据、计算派生指标等
```

### 2. 合理的批次大小

```python
# 根据任务复杂度调整批次大小
简单任务：20-50 个配置
复杂任务：5-10 个配置
```

### 3. 错误处理

```python
# 在回测中捕获异常，避免单个失败影响整体
# 多进程引擎会自动隔离错误
```

### 4. 结果持久化

```python
# 立即保存结果，避免丢失
# 使用数据库或文件系统存储
```

### 5. 资源监控

```python
# 定期检查系统资源
# 在高负载时暂停新任务
```

---

## 技术支持

### 依赖项

```python
# requirements.txt
fastapi>=0.104.0
uvicorn[standard]>=0.30.0
pydantic>=2.0.0
psutil>=5.9.0
pandas>=2.0.0
numpy>=1.24.0
```

### 环境要求

- Python 3.10+
- 4GB+ RAM（推荐 8GB+）
- 多核 CPU（推荐 4 核心以上）
- SSD 存储（提升 I/O 性能）

---

## 版本历史

### v1.0.0 (当前版本)

- ✅ 核心多进程回测引擎
- ✅ 动态进程池管理
- ✅ 四种并行级别支持
- ✅ RESTful API 接口
- ✅ 性能监控与基准测试
- ✅ 完整文档与示例

### 未来计划 (v1.1.0)

- [ ] 集成真实市场数据源（yfinance, akshare）
- [ ] WebSocket 实时进度推送
- [ ] 结果可视化（Textual 图表）
- [ ] 分布式回测（多机器）
- [ ] GPU 加速（Numba, CuPy）

---

## 联系与反馈

如有问题或建议，请联系：

- **Issues**: https://github.com/your-repo/issues
- **文档**: https://github.com/your-repo/wiki
- **讨论**: https://github.com/your-repo/discussions

---

**文档版本**: 1.0.0 **最后更新**: 2025-01-02 **维护者**: CBSC Quant Team
