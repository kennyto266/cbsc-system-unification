# 港股量化分析AI代理团队使用指南

## 概述

港股量化分析AI代理团队是一个基于prompt模板的7个专业AI代理系统，专门针对港股市场设计，追求高Sharpe Ratio (>1.5)的交易策略。每个代理都使用ReAct风格（Reasoning + Acting）的结构化prompt，输出标准化的JSON格式结果。

## 系统架构

### 核心组件

1. **Prompt模板系统** (`hk_prompt_templates.py`)
   - 7个专业代理的prompt模板
   - 标准化的输入/输出格式
   - JSON响应解析和验证

2. **Prompt执行引擎** (`hk_prompt_engine.py`)
   - 支持多种LLM提供商（OpenAI、Claude、Grok等）
   - 异步执行和错误处理
   - 执行统计和性能监控

3. **代理实现** (`hk_prompt_agents.py`)
   - 7个专业代理的具体实现
   - 基于现有代理架构的扩展
   - 消息队列集成

## 7个专业代理

### 1. 基本面分析代理 (Fundamental Analyst)
- **角色**: 分析港股基本面指标
- **功能**: 计算PE比率、ROE、盈利成长率
- **输出**: 低估股票清单、平均PE、Sharpe贡献值、交易建议

### 2. 情绪分析代理 (Sentiment Analyst)
- **角色**: 分析社交媒体和论坛情绪
- **功能**: 量化情绪分数、识别情绪偏差
- **输出**: 情绪分数、平均情绪、Sharpe贡献值、情绪建议

### 3. 新闻分析代理 (News Analyst)
- **角色**: 分析新闻事件对港股的影响
- **功能**: 提取关键事件、计算影响分数
- **输出**: 关键事件、事件数量、Sharpe贡献值、事件建议

### 4. 技术分析代理 (Technical Analyst)
- **角色**: 计算技术指标，生成交易信号
- **功能**: 计算MA、RSI、MACD等技术指标
- **输出**: 交易信号、平均RSI、Sharpe贡献值、技术建议

### 5. 研究辩论代理 (Research Debate)
- **角色**: 整合各代理分析，平衡观点
- **功能**: 模拟Bullish/Bearish辩论，生成平衡观点
- **输出**: 乐观分数、悲观分数、平衡分数、辩论建议

### 6. 交易执行代理 (Trader)
- **角色**: 基于分析结果生成交易订单
- **功能**: 整合信号生成订单，计算仓位大小
- **输出**: 交易订单、预期回报、Sharpe贡献值、执行建议

### 7. 风险管理代理 (Risk Manager)
- **角色**: 计算风险指标，控制风险暴露
- **功能**: 计算VaR、Sharpe比率，设定风险限额
- **输出**: VaR值、Sharpe比率、风险限额、风险建议

## 快速开始

### 1. 安装依赖

```bash
pip install openai anthropic aiohttp pandas numpy
```

### 2. 配置LLM

```python
from src.agents.hk_prompt_engine import HKPromptEngine, LLMConfig, LLMProvider

# 配置OpenAI
llm_config = LLMConfig(
    provider=LLMProvider.OPENAI,
    api_key="your-openai-api-key",
    model="gpt-4",
    max_tokens=2000,
    temperature=0.1
)

# 创建Prompt引擎
prompt_engine = HKPromptEngine(llm_config)
```

### 3. 创建代理

```python
from src.agents.hk_prompt_agents import HKPromptAgentFactory
from src.agents.hk_prompt_templates import AgentType

# 创建单个代理
agent = HKPromptAgentFactory.create_agent(
    AgentType.FUNDAMENTAL_ANALYST,
    config, message_queue, system_config, prompt_engine
)

# 创建所有代理
agents = HKPromptAgentFactory.create_all_agents(
    message_queue, system_config, prompt_engine
)
```

### 4. 执行分析

```python
# 准备市场数据
market_data = [
    {
        "symbol": "0700.HK",
        "timestamp": "2024-01-01T09:30:00",
        "open": 100.0,
        "high": 102.0,
        "low": 98.0,
        "close": 101.0,
        "volume": 1000000
    }
]

# 执行单个代理分析
result = await prompt_engine.execute_prompt(
    AgentType.FUNDAMENTAL_ANALYST, 
    {"market_data": market_data}
)

# 执行代理管道
results = await prompt_engine.execute_agent_pipeline(
    {"market_data": market_data}
)
```

## 配置说明

### LLM提供商配置

支持多种LLM提供商：

- **OpenAI**: GPT-4, GPT-3.5-turbo
- **Claude**: Claude-3-Opus, Claude-3-Sonnet
- **Grok**: Grok-beta
- **本地模型**: 支持自定义API端点

### 代理配置

每个代理可以独立配置：

```json
{
  "analysis_symbols": ["0700.HK", "0005.HK", "0941.HK"],
  "lookback_days": 30,
  "analysis_interval_minutes": 5
}
```

### 风险管理配置

```json
{
  "max_drawdown_percent": 10.0,
  "target_sharpe_ratio": 1.5,
  "var_confidence_level": 0.95,
  "position_size_limit_percent": 20.0
}
```

## 使用示例

### 基本使用

```python
import asyncio
from src.agents.hk_prompt_agents import HKPromptAgentFactory
from src.agents.hk_prompt_templates import AgentType

async def main():
    # 初始化
    prompt_engine = HKPromptEngine(llm_config)
    agents = HKPromptAgentFactory.create_all_agents(message_queue, system_config, prompt_engine)
    
    # 初始化所有代理
    for agent in agents.values():
        await agent.initialize()
    
    # 准备数据
    market_data = create_market_data()
    
    # 执行分析
    results = await prompt_engine.execute_agent_pipeline({"market_data": market_data})
    
    # 处理结果
    for agent_type, result in results.items():
        if result.success:
            print(f"{agent_type.value}: {result.explanation}")
            print(f"数据: {result.parsed_data}")

asyncio.run(main())
```

### 高级使用

```python
# 并行执行多个代理
parallel_agents = [
    AgentType.FUNDAMENTAL_ANALYST,
    AgentType.TECHNICAL_ANALYST,
    AgentType.SENTIMENT_ANALYST
]

results = await prompt_engine.execute_parallel_agents(
    {"market_data": market_data}, 
    parallel_agents
)

# 自定义prompt
custom_prompt = "你是一位专业的港股分析师..."
result = await prompt_engine.execute_prompt(
    AgentType.FUNDAMENTAL_ANALYST,
    {"market_data": market_data},
    custom_prompt
)
```

## 监控和调试

### 执行统计

```python
stats = prompt_engine.get_execution_stats()
print(f"执行次数: {stats['execution_count']}")
print(f"成功率: {stats['success_rate']:.2%}")
print(f"平均执行时间: {stats['avg_execution_time']:.2f}秒")
```

### 日志配置

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### 错误处理

```python
try:
    result = await prompt_engine.execute_prompt(agent_type, input_data)
    if not result.success:
        print(f"执行失败: {result.error}")
except Exception as e:
    print(f"异常: {e}")
```

## 最佳实践

### 1. 数据准备
- 确保市场数据格式正确
- 包含足够的历史数据
- 验证数据质量

### 2. 代理配置
- 根据市场条件调整分析间隔
- 设置合适的回看天数
- 配置风险限额

### 3. 错误处理
- 实现重试机制
- 监控执行统计
- 设置告警阈值

### 4. 性能优化
- 使用并行执行
- 缓存分析结果
- 优化prompt长度

## 故障排除

### 常见问题

1. **LLM连接失败**
   - 检查API密钥
   - 验证网络连接
   - 确认API配额

2. **JSON解析失败**
   - 检查prompt格式
   - 验证输出格式
   - 调整temperature参数

3. **代理初始化失败**
   - 检查依赖项
   - 验证配置参数
   - 查看错误日志

### 调试技巧

1. 启用详细日志
2. 使用测试连接功能
3. 检查执行统计
4. 验证数据格式

## 扩展开发

### 添加新代理

1. 在`AgentType`枚举中添加新类型
2. 在`HKPromptTemplates`中添加prompt模板
3. 创建代理实现类
4. 在工厂类中注册

### 自定义prompt模板

```python
# 创建自定义模板
custom_template = PromptTemplate(
    agent_type=AgentType.CUSTOM,
    role="自定义代理",
    objective="自定义目标",
    tasks=["任务1", "任务2"],
    input_format="自定义输入格式",
    output_format="自定义输出格式",
    reasoning_steps="自定义推理步骤",
    example_output={"key": "value"},
    explanation="自定义解释"
)

# 添加到模板管理器
templates.templates[AgentType.CUSTOM] = custom_template
```

## 许可证

本项目采用MIT许可证。详见LICENSE文件。

## 贡献

欢迎提交Issue和Pull Request来改进项目。

## 联系方式

如有问题或建议，请通过以下方式联系：

- 创建GitHub Issue
- 发送邮件到项目维护者
- 加入项目讨论群
