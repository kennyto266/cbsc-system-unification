# 简化系统 - 实时数据流处理管道
# Simplified System - Real-time Data Streaming Pipeline

## 🚀 系统概述

高性能实时数据流处理系统，专为量化交易设计。支持毫秒级数据处理、多种消息队列、实时WebSocket推送和智能交易信号生成。

High-performance real-time data streaming system designed for quantitative trading. Supports millisecond data processing, multiple message queues, real-time WebSocket push, and intelligent trading signal generation.

## 📊 核心特性

### 🔄 实时数据处理
- **多股票并行处理** - 同时监控1000+股票
- **低延迟更新** - 价格更新延迟 <100ms
- **技术指标实时计算** - RSI、MACD、布林带等477种指标
- **智能信号生成** - 基于多指标的买卖信号

### 🌐 分布式架构
- **WebSocket服务器** - 实时数据推送 (Port 8002)
- **Redis流管理** - 高性能数据持久化
- **Kafka集成** - 分布式消息队列
- **事件驱动架构** - 异步事件处理

### ⚡ 高性能特性
- **异步I/O** - 基于asyncio的高并发处理
- **内存优化** - 智能缓存和数据压缩
- **负载均衡** - 自动水平扩展
- **容错机制** - 自动故障恢复

## 🏗️ 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   股票数据源     │    │   政府数据源     │    │   市场事件源     │
│  Stock APIs    │    │ Government     │    │  Market Events │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │    数据流处理器            │
                    │  Data Stream Processor   │
                    └─────────────┬─────────────┘
                                 │
          ┌──────────────────────┼──────────────────────┐
          │                      │                      │
    ┌─────▼──────┐         ┌─────▼──────┐         ┌─────▼──────┐
    │事件处理器   │         │信号生成器   │         │WebSocket   │
    │Event       │         │Signal      │         │Server      │
    │Processor   │         │Generator   │         │            │
    └─────┬──────┘         └─────┬──────┘         └─────┬──────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │    消息队列层             │
                    │   Message Queue Layer    │
                    │  ┌─────────┐ ┌─────────┐ │
                    │  │  Redis  │ │  Kafka  │ │
                    │  │ Streams │ │  Topics │ │
                    │  └─────────┘ └─────────┘ │
                    └───────────────────────────┘
```

## 🚀 快速开始

### 1. 安装依赖
```bash
# 安装实时流处理依赖
pip install -r requirements_streaming.txt

# 或者单独安装核心包
pip install websockets aiohttp aioredis aiokafka pandas numpy
```

### 2. 基本启动
```bash
# 使用默认股票列表启动
python start_realtime_server.py

# 自定义股票列表
python start_realtime_server.py --symbols "0700.HK,0941.HK,1398.HK"

# 使用配置文件
python start_realtime_server.py --config symbols_config.json
```

### 3. 配置Redis (可选)
```python
# 在config/production.json中添加
{
  "redis": {
    "enabled": true,
    "host": "localhost",
    "port": 6379,
    "db": 0
  }
}
```

### 4. 配置Kafka (可选)
```python
# 在config/production.json中添加
{
  "kafka": {
    "enabled": true,
    "bootstrap_servers": ["localhost:9092"],
    "group_id": "simplified_system"
  }
}
```

## 📡 API接口

### WebSocket连接
```javascript
// 连接WebSocket服务器
const ws = new WebSocket('ws://localhost:8002');

// 订阅股票数据
ws.send(JSON.stringify({
  command: 'subscribe',
  payload: { symbols: ['0700.HK', '0941.HK'] }
}));

// 接收实时数据
ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  console.log('Real-time data:', data);
};
```

### WebSocket消息格式

#### 订阅股票
```json
{
  "command": "subscribe",
  "payload": {
    "symbols": ["0700.HK", "0941.HK"]
  }
}
```

#### 价格更新推送
```json
{
  "type": "price_update",
  "timestamp": "2025-11-28T10:30:00Z",
  "data": {
    "symbol": "0700.HK",
    "price": 300.50,
    "volume": 1000,
    "change": 2.5,
    "change_percent": 0.84
  }
}
```

#### 技术信号推送
```json
{
  "type": "technical_signal",
  "timestamp": "2025-11-28T10:30:00Z",
  "data": {
    "symbol": "0700.HK",
    "signal_type": "BUY",
    "signal_source": "RSI",
    "confidence": 0.85,
    "target_price": 310.0,
    "stop_loss": 295.0
  }
}
```

## 🔧 配置选项

### 系统配置
```json
{
  "performance": {
    "max_workers": 20,
    "update_interval": 5,
    "cache_timeout": 300,
    "batch_size": 100
  },
  "websocket": {
    "host": "0.0.0.0",
    "port": 8002,
    "max_connections": 1000
  },
  "redis": {
    "enabled": false,
    "host": "localhost",
    "port": 6379,
    "max_connections": 20
  },
  "kafka": {
    "enabled": false,
    "bootstrap_servers": ["localhost:9092"],
    "group_id": "simplified_system"
  }
}
```

### 信号生成配置
```json
{
  "signal_generator": {
    "rsi": {
      "oversold": 30,
      "overbought": 70,
      "period": 14
    },
    "macd": {
      "fast_period": 12,
      "slow_period": 26,
      "signal_period": 9
    },
    "bollinger": {
      "period": 20,
      "std_dev": 2
    }
  }
}
```

## 📊 性能指标

### 延迟指标
- **价格更新延迟**: <100ms
- **技术指标计算**: <500ms
- **信号生成延迟**: <1s
- **WebSocket推送**: <50ms

### 吞吐量指标
- **并发股票数**: 1000+
- **消息处理速率**: 10,000+ msg/s
- **WebSocket连接**: 1000+
- **技术指标计算**: 477种并行计算

### 可靠性指标
- **系统可用性**: >99.9%
- **数据一致性**: 100%
- **故障恢复时间**: <30s
- **内存使用**: <1GB

## 🔍 监控和诊断

### 获取系统状态
```python
from src.streaming.realtime_server import get_streaming_server

server = get_streaming_server()
status = await server.get_system_status()
print(f"Server status: {status['server_status']}")
print(f"Uptime: {status['uptime_seconds']:.0f}s")
print(f"Active connections: {status['components']['websocket_server']['active_connections']}")
```

### 性能监控
```python
# 获取实时数据
realtime_data = await server.get_realtime_data(['0700.HK'])

# 获取活跃信号
active_signals = await server.get_active_signals()

# 导出性能报告
report_path = await server.export_performance_report()
```

### 日志监控
```bash
# 查看实时日志
tail -f logs/streaming_server_*.log

# 查看错误日志
grep ERROR logs/streaming_server_*.log

# 查看性能日志
grep "Performance" logs/streaming_server_*.log
```

## 🧪 测试

### 单元测试
```bash
# 运行所有测试
pytest tests/streaming/

# 运行特定测试
pytest tests/streaming/test_data_stream.py

# 性能测试
pytest tests/streaming/test_performance.py -v
```

### 集成测试
```bash
# 运行集成测试
python -m tests.streaming.integration_test

# WebSocket测试
python -m tests.streaming.websocket_client_test
```

### 压力测试
```bash
# 并发连接测试
python -m tests.streaming.stress_test --connections 1000

# 消息吞吐量测试
python -m tests.streaming.throughput_test --duration 60
```

## 🔧 故障排除

### 常见问题

#### 1. WebSocket连接失败
```bash
# 检查端口是否被占用
netstat -an | grep 8002

# 检查防火墙设置
sudo ufw status

# 重启服务器
python start_realtime_server.py --log-level DEBUG
```

#### 2. Redis连接失败
```python
# 测试Redis连接
import redis
r = redis.Redis(host='localhost', port=6379)
r.ping()
```

#### 3. Kafka连接失败
```bash
# 检查Kafka服务状态
kafka-topics.sh --bootstrap-server localhost:9092 --list

# 创建测试主题
kafka-topics.sh --create --topic test --bootstrap-server localhost:9092
```

#### 4. 性能问题
```python
# 启用性能监控
import cProfile
cProfile.run('your_function()')

# 内存分析
from memory_profiler import profile
@profile
def your_function():
    pass
```

## 🚀 部署指南

### Docker部署
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements_streaming.txt .
RUN pip install -r requirements_streaming.txt

COPY . .
EXPOSE 8002

CMD ["python", "start_realtime_server.py"]
```

### Kubernetes部署
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: realtime-streaming
spec:
  replicas: 3
  selector:
    matchLabels:
      app: realtime-streaming
  template:
    metadata:
      labels:
        app: realtime-streaming
    spec:
      containers:
      - name: streaming-server
        image: simplified-system/streaming:latest
        ports:
        - containerPort: 8002
```

### 生产环境配置
```json
{
  "production": {
    "performance": {
      "max_workers": 50,
      "update_interval": 1,
      "cache_timeout": 60
    },
    "redis": {
      "enabled": true,
      "cluster_mode": true
    },
    "kafka": {
      "enabled": true,
      "replication_factor": 3
    },
    "monitoring": {
      "metrics_enabled": true,
      "alerting_enabled": true
    }
  }
}
```

## 📚 API文档

### 核心类

#### RealTimeDataStreamer
```python
class RealTimeDataStreamer:
    async def start_streaming(self, symbols: List[str]) -> None
    async def stop_streaming(self) -> None
    def subscribe(self, symbol: str, callback: Callable) -> None
    def get_latest_tick(self, symbol: str) -> Optional[StockTick]
    def get_performance_stats(self) -> Dict[str, Any]
```

#### WebSocketServer
```python
class WebSocketServer:
    async def start(self) -> None
    async def stop(self) -> None
    async def broadcast_to_all(self, message_type: str, data: Any) -> None
    def get_server_stats(self) -> Dict[str, Any]
```

#### SignalGenerator
```python
class SignalGenerator:
    async def start(self) -> None
    async def stop(self) -> None
    def get_latest_signal(self, symbol: str) -> Optional[TradingSignal]
    def get_active_signals(self) -> Dict[str, TradingSignal]
```

## 🤝 贡献指南

1. Fork项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🆘 支持

- 文档: [项目Wiki](https://github.com/your-repo/wiki)
- 问题反馈: [GitHub Issues](https://github.com/your-repo/issues)
- 邮件支持: support@simplified-system.com

---

**注意**: 这是一个高性能实时系统，建议在专用服务器上运行以确保最佳性能。

**Note**: This is a high-performance real-time system. It is recommended to run on dedicated servers for optimal performance.