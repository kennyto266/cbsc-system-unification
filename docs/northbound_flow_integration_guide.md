# 港交所北向资金数据整合指南

## 1. 项目概述

本方案提供了一个完整的港交所北向资金数据收集、存储和整合架构，能够：

- 实时/定时收集北向资金数据
- 存储到优化的SQLite数据库
- 与现有量化系统无缝集成
- 生成基于北向资金的技术指标和交易信号
- 支持多个数据源的容错机制

## 2. 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   数据源层      │    │   数据收集层    │    │   数据存储层    │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ • 港交所(HKEX)  │    │ • 定时调度器    │    │ • SQLite数据库  │
│ • 上交所(SSE)   │◄──►│ • 异步爬虫      │◄──►│ • 表结构优化    │
│ • 深交所(SZSE)  │    │ • 错误重试      │    │ • 索引优化      │
│ • 东方财富      │    │ • 速率限制      │    │ • 数据备份      │
│ • Tushare(付费) │    │ • 数据验证      │    │ • 历史归档      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   信号生成层    │    │   策略集成层    │    │   监控告警层    │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ • 技术指标计算  │    │ • 数据适配器    │    │ • 数据质量监控  │
│ • 背离检测      │◄──►│ • 策略信号      │◄──►│ • 异常告警      │
│ • 动量分析      │    │ • 回测支持      │    │ • 性能指标      │
│ • 持仓分析      │    │ • 实时API       │    │ • 日志记录      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 3. 技术栈

### 核心技术
- **Python 3.9+**: 主要开发语言
- **SQLite**: 轻量级数据库，支持全文索引
- **asyncio**: 异步网络请求，提高效率
- **pandas**: 数据处理和分析
- **requests/aiohttp**: HTTP客户端

### 可选增强
- **Redis**: 缓存热点数据
- **PostgreSQL**: 大规模数据存储
- **Selenium**: 渲染JavaScript页面
- **BeautifulSoup4**: HTML解析

## 4. 安装与配置

### 4.1 环境准备

```bash
# 创建虚拟环境
python -m venv venv_northbound
source venv_northbound/bin/activate  # Linux/Mac
# 或
venv_northbound\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements/northbound_requirements.txt
```

### 4.2 依赖文件 (`requirements/northbound_requirements.txt`)

```txt
# 核心依赖
requests>=2.28.0
aiohttp>=3.8.0
pandas>=1.5.0
numpy>=1.23.0

# 数据处理
lxml>=4.9.0
beautifulsoup4>=4.11.0
html5lib>=1.1

# 数据库
sqlite3  # Python内置
redis>=4.3.0  # 可选，用于缓存

# 异步支持
asyncio  # Python内置
aiofiles>=0.8.0

# 工具库
python-dateutil>=2.8.0
pytz>=2022.1
tqdm>=4.64.0

# 监控日志
loguru>=0.6.0

# 付费API（可选）
tushare>=1.2.89  # 需要token
```

### 4.3 配置文件 (`config/northbound_config.json`)

```json
{
  "database": {
    "path": "data/northbound_flow.db",
    "backup_path": "backup/northbound_flow_{date}.db"
  },
  "data_sources": {
    "hkex": {
      "enabled": true,
      "base_url": "https://www.hkex.com.hk",
      "rate_limit": 1,
      "timeout": 30
    },
    "sse": {
      "enabled": true,
      "base_url": "http://query.sse.com.cn",
      "rate_limit": 2,
      "timeout": 30
    },
    "szse": {
      "enabled": true,
      "base_url": "http://www.szse.cn",
      "rate_limit": 2,
      "timeout": 30
    },
    "eastmoney": {
      "enabled": true,
      "base_url": "http://push2.eastmoney.com",
      "rate_limit": 1,
      "timeout": 30
    },
    "tushare": {
      "enabled": false,
      "api_token": "YOUR_TOKEN_HERE",
      "rate_limit": 60,
      "timeout": 30
    }
  },
  "schedule": {
    "update_frequency": "daily",
    "update_time": "16:00",
    "retry_times": 3,
    "retry_delay": 300
  },
  "alerts": {
    "email_enabled": false,
    "webhook_enabled": true,
    "webhook_url": "YOUR_WEBHOOK_URL"
  }
}
```

## 5. 快速开始

### 5.1 初始化数据库

```python
# 运行数据库迁移
python migrations/add_northbound_flow_tables.py
```

### 5.2 手动收集数据

```python
from src.services.northbound_flow_collector import NorthboundDataManager

# 创建管理器
manager = NorthboundDataManager()

# 收集最近7天的数据
import asyncio
from datetime import datetime, timedelta

async def collect_data():
    for i in range(7):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        success = await manager.collect_daily_data(date)
        print(f"{date}: {'成功' if success else '失败'}")

asyncio.run(collect_data())
```

### 5.3 集成到现有系统

```python
from src.adapters.northbound_flow_adapter import NorthboundFlowAdapter

# 创建适配器
adapter = NorthboundFlowAdapter()

# 获取整合后的数据
data = adapter.integrate_northbound_data(
    symbol="1398.HK",  # 工商银行
    start_date="2024-01-01",
    end_date="2024-01-31"
)

# 生成交易信号
from src.adapters.northbound_flow_adapter import NorthboundStrategySignals
signals = NorthboundStrategySignals.generate_signals(data)
```

## 6. 数据源详情

### 6.1 免费数据源

#### 东方财富网（推荐）
- **优点**: 数据稳定、免费、更新及时
- **缺点**: 需要解析特定格式
- **URL**: `http://push2.eastmoney.com/api/qt/kamt.rt.get`

#### 港交所
- **优点**: 官方数据源、最权威
- **缺点**: 可能有反爬虫措施
- **URL**: 需要查找具体API

### 6.2 付费数据源

#### Tushare
- **优点**: 数据质量高、API稳定、历史数据全
- **缺点**: 需要付费
- **Token申请**: https://tushare.pro

## 7. 部署策略

### 7.1 本地部署

```bash
# 1. 克隆代码
git clone <repository>
cd CODEX--

# 2. 安装依赖
pip install -r requirements/northbound_requirements.txt

# 3. 初始化数据库
python migrations/add_northbound_flow_tables.py

# 4. 配置定时任务
python scripts/schedule_northbound_collector.py
```

### 7.2 Docker部署

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements/northbound_requirements.txt .
RUN pip install -r northbound_requirements.txt

COPY . .

CMD ["python", "scripts/schedule_northbound_collector.py"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  northbound-collector:
    build: .
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    environment:
      - PYTHONUNBUFFERED=1
    restart: unless-stopped
```

### 7.3 云端部署（AWS/Azure/阿里云）

1. 使用ECS/Fargate运行定时任务
2. 使用S3/OSS存储备份数据
3. 使用CloudWatch/Monitoring监控运行状态

## 8. 监控与维护

### 8.1 日志配置

```python
import logging
from logging.handlers import RotatingFileHandler

# 配置日志
logger = logging.getLogger('northbound')
logger.setLevel(logging.INFO)

# 文件日志
file_handler = RotatingFileHandler(
    'logs/northbound_flow.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))
logger.addHandler(file_handler)
```

### 8.2 性能监控指标

- 数据收集成功率
- API响应时间
- 数据完整性检查
- 数据库查询性能
- 内存使用情况

### 8.3 告警规则

```python
# 告警条件示例
alerts = {
    "data_collection_failed": {
        "condition": "连续3次收集失败",
        "action": "发送邮件/钉钉通知"
    },
    "api_response_slow": {
        "condition": "响应时间 > 30秒",
        "action": "记录慢查询日志"
    },
    "data_anomaly": {
        "condition": "数据波动超过标准差3倍",
        "action": "人工审核"
    }
}
```

## 9. 最佳实践

### 9.1 数据收集建议

1. **遵守robots.txt**: 尊重网站的爬虫协议
2. **设置合理的延迟**: 避免对服务器造成压力
3. **使用User-Agent**: 标明你的身份
4. **错误重试**: 网络问题时的重试机制
5. **数据验证**: 确保数据的合理性

### 9.2 存储优化

1. **合理设计索引**: 提高查询性能
2. **定期归档**: 将历史数据移至归档表
3. **数据压缩**: 减少存储空间
4. **定期备份**: 防止数据丢失

### 9.3 合规注意事项

1. **数据使用**: 仅用于个人研究，不用于商业用途
2. **版权声明**: 注明数据来源
3. **API限制**: 遵守各平台的API使用条款
4. **隐私保护**: 不收集个人信息

## 10. 故障排除

### 10.1 常见问题

**Q: 数据收集失败**
A: 检查网络连接、API URL是否正确、是否被反爬虫

**Q: 数据不完整**
A: 检查源网站是否更新数据、查看解析逻辑是否正确

**Q: 性能问题**
A: 优化SQL查询、增加索引、使用异步处理

### 10.2 调试模式

```python
# 开启调试日志
logging.basicConfig(level=logging.DEBUG)

# 使用测试数据
manager.collect_daily_data(test_mode=True)
```

## 11. 扩展开发

### 11.1 添加新数据源

1. 在配置文件中添加数据源信息
2. 创建相应的API客户端类
3. 实现数据解析逻辑
4. 注册到管理器中

### 11.2 自定义指标

```python
def custom_indicator(df):
    """自定义指标示例"""
    # 计算北向资金占比
    df['custom_ratio'] = df['total_turnover'] / df['volume']
    return df
```

## 12. 联系与支持

- **项目维护者**: Claude Code Assistant
- **技术支持**: 提交Issue到GitHub仓库
- **更新日志**: 查看CHANGELOG.md

---

*最后更新: 2025-01-16*