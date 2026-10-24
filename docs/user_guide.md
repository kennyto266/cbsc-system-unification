# 港股量化交易 AI Agent 系统 - 用户指南

## 系统概述

港股量化交易 AI Agent 系统是一个基于人工智能的量化交易平台，专为香港股票市场设计。系统采用多Agent架构，通过7个专业AI Agent协同工作，实现高Sharpe比率的量化交易策略。

### 核心特性

- **多Agent协作**: 7个专业AI Agent各司其职，协同工作
- **实时交易**: 支持高频交易和毫秒级响应
- **风险管理**: 全面的风险控制和监控机制
- **策略研究**: 基于学术研究的策略开发和验证
- **系统监控**: 实时性能监控和故障恢复
- **可扩展性**: 支持大规模并发处理

## 系统架构

### AI Agent 架构

```
┌─────────────────────────────────────────────────────────────┐
│                    港股量化交易 AI Agent 系统                    │
├─────────────────────────────────────────────────────────────┤
│  Agent协调器 (Agent Coordinator)                              │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
│  │量化分析师Agent│ │量化交易员Agent│ │投资组合经理Agent│ │风险分析师Agent│ │
│  │             │ │             │ │             │ │             │ │
│  │• 数学建模    │ │• 信号识别    │ │• 资产配置    │ │• VaR计算    │ │
│  │• 统计分析    │ │• 订单执行    │ │• 再平衡      │ │• 压力测试    │ │
│  │• 蒙特卡罗    │ │• 高频交易    │ │• 风险预算    │ │• 对冲策略    │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                │
│  │数据科学家Agent│ │量化工程师Agent│ │研究分析师Agent│                │
│  │             │ │             │ │             │                │
│  │• 机器学习    │ │• 系统监控    │ │• 文献研究    │                │
│  │• 特征工程    │ │• 性能优化    │ │• 假设测试    │                │
│  │• 异常检测    │ │• 故障恢复    │ │• 回测验证    │                │
│  └─────────────┘ └─────────────┘ └─────────────┘                │
├─────────────────────────────────────────────────────────────┤
│                    消息队列系统 (Redis)                        │
├─────────────────────────────────────────────────────────────┤
│                    数据存储层                                 │
└─────────────────────────────────────────────────────────────┘
```

### 核心组件

1. **消息队列系统**: 基于Redis的异步消息传递
2. **数据模型**: 标准化的市场数据、交易信号、投资组合等模型
3. **通信协议**: Agent间标准化的通信协议
4. **监控系统**: 实时性能监控和告警系统

## 安装和配置

### 系统要求

- Python 3.8+
- Redis 6.0+
- 8GB+ RAM
- 多核CPU (推荐4核+)

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd hk-quant-ai-agents
```

2. **创建虚拟环境**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **配置Redis**
```bash
# 启动Redis服务器
redis-server

# 验证Redis连接
redis-cli ping
```

5. **配置环境变量**
```bash
cp env.example .env
# 编辑.env文件，配置Redis连接等参数
```

### 配置文件

#### .env 配置
```env
# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# 系统配置
SYSTEM_LOG_LEVEL=INFO
SYSTEM_MAX_AGENTS=100
SYSTEM_HEARTBEAT_INTERVAL=30

# 交易配置
TRADING_INITIAL_CAPITAL=1000000
TRADING_TRANSACTION_COST=0.001
TRADING_SLIPPAGE=0.0005

# 风险配置
RISK_MAX_POSITION_SIZE=0.1
RISK_MAX_LEVERAGE=1.0
RISK_VAR_CONFIDENCE=0.95
```

## 快速开始

### 1. 启动系统

```python
from src.agents.coordinator import AgentCoordinator
from src.core.message_queue import MessageQueue

async def main():
    # 初始化消息队列
    message_queue = MessageQueue()
    await message_queue.initialize()
    
    # 创建Agent协调器
    coordinator = AgentCoordinator(message_queue)
    await coordinator.initialize()
    
    # 启动所有Agent
    await coordinator.start_all_agents()
    
    print("港股量化交易 AI Agent 系统已启动")

if __name__ == "__main__":
    asyncio.run(main())
```

### 2. 发送市场数据

```python
from src.models.base import MarketData
from src.core.message_queue import MessageQueue

async def send_market_data():
    message_queue = MessageQueue()
    await message_queue.initialize()
    
    # 创建市场数据
    market_data = MarketData(
        symbol="2800.HK",
        timestamp=datetime.now(),
        open_price=25.50,
        high_price=25.80,
        low_price=25.40,
        close_price=25.70,
        volume=1000000,
        vwap=25.60
    )
    
    # 发送消息
    message = Message(
        sender_id="market_data_source",
        receiver_id="quant_analyst_001",
        message_type="MARKET_DATA",
        payload=market_data.dict(),
        timestamp=datetime.now(),
        priority="NORMAL"
    )
    
    await message_queue.publish_message(message)
    print("市场数据已发送")
```

### 3. 监控系统状态

```python
async def monitor_system():
    coordinator = AgentCoordinator(message_queue)
    
    # 获取所有Agent状态
    statuses = await coordinator.get_all_agent_statuses()
    
    for agent_id, status in statuses.items():
        print(f"Agent {agent_id}: {status['status']}")
```

## Agent 详细说明

### 1. 量化分析师Agent (Quantitative Analyst)

**职责**: 开发数学模型、统计分析和策略研究

**主要功能**:
- 技术指标计算 (SMA, EMA, RSI, MACD等)
- 波动率预测
- 蒙特卡罗模拟
- 统计建模

**使用示例**:
```python
# 发送分析请求
message = Message(
    sender_id="user",
    receiver_id="quant_analyst_001",
    message_type="ANALYSIS_REQUEST",
    payload={
        "symbol": "2800.HK",
        "analysis_type": "volatility_prediction",
        "period": "30d"
    },
    timestamp=datetime.now(),
    priority="NORMAL"
)
```

### 2. 量化交易员Agent (Quantitative Trader)

**职责**: 识别交易机会和执行交易订单

**主要功能**:
- 交易信号识别
- 订单执行
- 高频交易
- 交易优化

**使用示例**:
```python
# 发送交易信号
trading_signal = TradingSignal(
    symbol="2800.HK",
    signal_type="BUY",
    strength=0.8,
    price=25.70,
    timestamp=datetime.now(),
    confidence=0.85,
    reasoning="动量指标显示买入信号"
)

message = Message(
    sender_id="quant_analyst_001",
    receiver_id="quant_trader_001",
    message_type="TRADING_SIGNAL",
    payload=trading_signal.dict(),
    timestamp=datetime.now(),
    priority="HIGH"
)
```

### 3. 投资组合经理Agent (Portfolio Manager)

**职责**: 投资组合构建和管理

**主要功能**:
- 资产配置
- 投资组合再平衡
- 风险预算管理
- 绩效监控

**使用示例**:
```python
# 发送再平衡请求
message = Message(
    sender_id="system",
    receiver_id="portfolio_manager_001",
    message_type="REBALANCE_REQUEST",
    payload={
        "target_allocation": {"2800.HK": 0.6, "0700.HK": 0.4},
        "rebalance_threshold": 0.05
    },
    timestamp=datetime.now(),
    priority="NORMAL"
)
```

### 4. 风险分析师Agent (Risk Analyst)

**职责**: 风险管理和控制

**主要功能**:
- VaR计算
- 压力测试
- 对冲策略
- 风险监控

**使用示例**:
```python
# 发送风险评估请求
message = Message(
    sender_id="portfolio_manager_001",
    receiver_id="risk_analyst_001",
    message_type="RISK_ASSESSMENT",
    payload={
        "portfolio": current_portfolio.dict(),
        "risk_metrics": ["var_95", "max_drawdown", "beta"]
    },
    timestamp=datetime.now(),
    priority="HIGH"
)
```

### 5. 数据科学家Agent (Data Scientist)

**职责**: 数据分析和机器学习

**主要功能**:
- 特征工程
- 机器学习模型训练
- 异常检测
- 数据预处理

**使用示例**:
```python
# 发送特征工程请求
message = Message(
    sender_id="quant_analyst_001",
    receiver_id="data_scientist_001",
    message_type="FEATURE_ENGINEERING",
    payload={
        "raw_data": market_data.dict(),
        "features": ["returns", "volatility", "volume_ratio"]
    },
    timestamp=datetime.now(),
    priority="NORMAL"
)
```

### 6. 量化工程师Agent (Quantitative Engineer)

**职责**: 系统运维和监控

**主要功能**:
- 系统监控
- 性能优化
- 故障恢复
- 部署管理

**使用示例**:
```python
# 发送系统监控请求
message = Message(
    sender_id="system",
    receiver_id="quant_engineer_001",
    message_type="CONTROL",
    payload={
        "command": "collect_metrics",
        "parameters": {}
    },
    timestamp=datetime.now(),
    priority="NORMAL"
)
```

### 7. 研究分析师Agent (Research Analyst)

**职责**: 策略研究和验证

**主要功能**:
- 学术文献研究
- 策略假设测试
- 回测验证
- 研究报告生成

**使用示例**:
```python
# 发送研究请求
message = Message(
    sender_id="user",
    receiver_id="research_analyst_001",
    message_type="CONTROL",
    payload={
        "command": "start_research",
        "parameters": {
            "research_type": "strategy_hypothesis",
            "focus_area": "momentum_strategies"
        }
    },
    timestamp=datetime.now(),
    priority="NORMAL"
)
```

## 消息类型和协议

### 消息类型

| 消息类型 | 描述 | 优先级 |
|---------|------|--------|
| MARKET_DATA | 市场数据 | NORMAL |
| TRADING_SIGNAL | 交易信号 | HIGH |
| TRADE_INSTRUCTION | 交易指令 | URGENT |
| PORTFOLIO_UPDATE | 投资组合更新 | NORMAL |
| RISK_ALERT | 风险告警 | URGENT |
| CONTROL | 控制命令 | NORMAL |
| ERROR | 错误消息 | URGENT |

### 消息格式

```python
{
    "id": "unique_message_id",
    "sender_id": "sender_agent_id",
    "receiver_id": "receiver_agent_id",
    "message_type": "MESSAGE_TYPE",
    "payload": {
        # 消息内容
    },
    "timestamp": "2024-01-01T00:00:00Z",
    "priority": "NORMAL|HIGH|URGENT"
}
```

## 监控和运维

### 系统监控

系统提供实时监控界面，可通过WebSocket访问：

```python
# 连接到监控WebSocket
import websocket

def on_message(ws, message):
    data = json.loads(message)
    print(f"系统状态: {data}")

ws = websocket.WebSocketApp("ws://localhost:8080/ws")
ws.on_message = on_message
ws.run_forever()
```

### 性能指标

- **吞吐量**: 消息处理速度 (msg/s)
- **延迟**: 消息处理延迟 (ms)
- **错误率**: 消息处理错误率 (%)
- **资源使用**: CPU、内存使用率

### 告警配置

```python
# 配置告警阈值
alert_config = {
    "cpu_threshold": 85.0,      # CPU使用率阈值
    "memory_threshold": 80.0,   # 内存使用率阈值
    "error_rate_threshold": 5.0, # 错误率阈值
    "latency_threshold": 100.0   # 延迟阈值(ms)
}
```

## 故障排除

### 常见问题

1. **Redis连接失败**
   ```
   解决方案: 检查Redis服务是否启动，验证连接配置
   ```

2. **Agent启动失败**
   ```
   解决方案: 检查Agent配置，验证依赖包安装
   ```

3. **消息处理延迟**
   ```
   解决方案: 检查系统资源使用，优化消息队列配置
   ```

4. **内存使用过高**
   ```
   解决方案: 调整垃圾回收策略，优化数据缓存
   ```

### 日志分析

系统日志位于 `logs/` 目录：

```bash
# 查看系统日志
tail -f logs/system.log

# 查看特定Agent日志
tail -f logs/quant_analyst.log

# 查看错误日志
grep "ERROR" logs/*.log
```

### 性能调优

1. **消息队列优化**
   ```python
   # 调整Redis配置
   redis_config = {
       "max_connections": 100,
       "socket_timeout": 5,
       "socket_connect_timeout": 5
   }
   ```

2. **Agent并发优化**
   ```python
   # 调整并发处理数量
   agent_config = {
       "max_concurrent_messages": 100,
       "message_batch_size": 10
   }
   ```

## 扩展开发

### 自定义Agent

```python
from src.agents.base_agent import BaseAgent, AgentConfig

class CustomAgent(BaseAgent):
    def __init__(self, config: AgentConfig, message_queue: MessageQueue):
        super().__init__(config, message_queue)
    
    async def initialize(self) -> bool:
        # 初始化逻辑
        return True
    
    async def process_message(self, message: Message) -> bool:
        # 消息处理逻辑
        return True
    
    async def cleanup(self):
        # 清理逻辑
        pass
```

### 自定义消息类型

```python
from src.models.base import BaseModel

class CustomMessage(BaseModel):
    custom_field: str
    custom_data: Dict[str, Any]
```

### 插件系统

```python
# 创建策略插件
class MomentumStrategy:
    def __init__(self):
        self.name = "momentum_strategy"
    
    def generate_signal(self, data: MarketData) -> TradingSignal:
        # 策略逻辑
        pass
```

## API 参考

### 核心API

#### MessageQueue
```python
class MessageQueue:
    async def initialize(self) -> bool
    async def publish_message(self, message: Message) -> bool
    async def subscribe(self, agent_id: str, message_types: List[str])
    async def cleanup(self)
```

#### AgentCoordinator
```python
class AgentCoordinator:
    async def register_agent(self, agent_id: str, agent_type: str) -> bool
    async def start_agent(self, agent_id: str) -> bool
    async def stop_agent(self, agent_id: str) -> bool
    async def get_all_agent_statuses(self) -> Dict[str, Dict]
```

#### BaseAgent
```python
class BaseAgent:
    async def initialize(self) -> bool
    async def process_message(self, message: Message) -> bool
    async def cleanup(self)
    def get_agent_info(self) -> Dict[str, Any]
```

### 数据模型API

#### MarketData
```python
class MarketData(BaseModel):
    symbol: str
    timestamp: datetime
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: int
    vwap: float
```

#### TradingSignal
```python
class TradingSignal(BaseModel):
    symbol: str
    signal_type: str  # BUY, SELL, HOLD
    strength: float   # 0.0 - 1.0
    price: float
    timestamp: datetime
    confidence: float
    reasoning: str
```

## 最佳实践

### 1. 消息设计
- 使用标准化的消息格式
- 合理设置消息优先级
- 避免过大的消息负载

### 2. 错误处理
- 实现完整的错误处理机制
- 使用重试机制处理临时故障
- 记录详细的错误日志

### 3. 性能优化
- 使用异步处理提高并发性能
- 合理配置消息队列参数
- 定期清理无用数据

### 4. 安全考虑
- 验证所有输入数据
- 使用安全的通信协议
- 定期更新依赖包

### 5. 监控和维护
- 设置完善的监控指标
- 定期进行系统健康检查
- 制定故障恢复计划

## 支持和贡献

### 获取帮助

- 查看系统日志
- 检查配置参数
- 参考API文档
- 联系技术支持

### 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 创建 Pull Request

### 许可证

本项目采用 MIT 许可证，详见 LICENSE 文件。

---

**港股量化交易 AI Agent 系统** - 让AI驱动您的量化交易策略
