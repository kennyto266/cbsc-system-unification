# 港股量化交易AI Agent系统 - 用户操作手册

## 概述

本手册详细介绍了港股量化交易AI Agent系统的使用方法，包括系统功能、操作流程、配置管理、监控告警等完整内容。该系统提供7个专业AI Agent，集成真实市场数据源，支持完整的量化交易工作流。

## 系统介绍

### 系统架构

港股量化交易AI Agent系统是一个基于人工智能的量化交易平台，集成了多个专业AI Agent，每个Agent负责特定的交易功能：

- **量化分析师Agent**：技术分析、统计建模、机器学习预测
- **量化交易员Agent**：交易信号生成、订单管理、风险控制
- **投资组合经理Agent**：投资组合优化、资产配置、再平衡
- **风险分析师Agent**：风险分析、VaR计算、压力测试
- **数据科学家Agent**：机器学习模型、特征工程、异常检测
- **量化工程师Agent**：系统监控、性能优化、故障诊断
- **研究分析师Agent**：策略研究、因子分析、学术研究

### 核心功能

- **实时数据处理**：集成黑人RAW DATA数据源
- **策略回测**：集成StockBacktest回测引擎
- **AI决策支持**：7个专业AI Agent协作
- **风险管理**：多维度风险控制和监控
- **Telegram集成**：CURSOR CLI项目集成
- **实时监控**：系统状态和性能监控
- **告警通知**：多渠道告警和通知

## 快速开始

### 1. 系统启动

#### 1.1 启动系统

```bash
# 使用Docker Compose（推荐）
docker-compose up -d

# 或使用Python直接启动
python -m src.integration.system_integration
```

#### 1.2 验证系统状态

```bash
# 检查系统健康状态
curl http://localhost:8000/health

# 检查组件状态
curl http://localhost:8000/status

# 查看系统仪表板
# 访问 http://localhost:8000/dashboard
```

### 2. 基本操作

#### 2.1 查看系统状态

在系统仪表板中，您可以查看：

- **系统概览**：整体运行状态
- **Agent状态**：各个AI Agent的运行状态
- **数据源状态**：数据连接和更新状态
- **策略状态**：活跃策略和性能指标
- **风险指标**：当前风险水平和预警

#### 2.2 启动/停止Agent

```bash
# 启动特定Agent
curl -X POST http://localhost:8000/agents/quantitative_analyst/start

# 停止特定Agent
curl -X POST http://localhost:8000/agents/quantitative_analyst/stop

# 重启特定Agent
curl -X POST http://localhost:8000/agents/quantitative_analyst/restart
```

#### 2.3 查看Agent状态

```bash
# 查看所有Agent状态
curl http://localhost:8000/agents/status

# 查看特定Agent状态
curl http://localhost:8000/agents/quantitative_analyst/status

# 查看Agent性能指标
curl http://localhost:8000/agents/quantitative_analyst/performance
```

## 详细功能说明

### 1. 数据管理

#### 1.1 数据源配置

系统集成了三个主要数据源：

- **黑人RAW DATA**：原始市场数据
- **StockBacktest**：回测引擎数据
- **CURSOR CLI**：Telegram Bot数据

#### 1.2 数据查看

```bash
# 查看可用数据源
curl http://localhost:8000/data/sources

# 查看特定数据源状态
curl http://localhost:8000/data/sources/raw_data/status

# 查看数据质量报告
curl http://localhost:8000/data/quality/report
```

#### 1.3 数据更新

```bash
# 手动更新数据
curl -X POST http://localhost:8000/data/update

# 更新特定数据源
curl -X POST http://localhost:8000/data/sources/raw_data/update

# 查看更新历史
curl http://localhost:8000/data/update/history
```

### 2. 策略管理

#### 2.1 策略查看

```bash
# 查看所有策略
curl http://localhost:8000/strategies

# 查看活跃策略
curl http://localhost:8000/strategies/active

# 查看策略详情
curl http://localhost:8000/strategies/strategy_001
```

#### 2.2 策略操作

```bash
# 启动策略
curl -X POST http://localhost:8000/strategies/strategy_001/start

# 停止策略
curl -X POST http://localhost:8000/strategies/strategy_001/stop

# 暂停策略
curl -X POST http://localhost:8000/strategies/strategy_001/pause

# 恢复策略
curl -X POST http://localhost:8000/strategies/strategy_001/resume
```

#### 2.3 策略性能

```bash
# 查看策略性能
curl http://localhost:8000/strategies/strategy_001/performance

# 查看策略回测结果
curl http://localhost:8000/strategies/strategy_001/backtest

# 查看策略风险指标
curl http://localhost:8000/strategies/strategy_001/risk
```

### 3. 风险管理

#### 3.1 风险监控

```bash
# 查看当前风险水平
curl http://localhost:8000/risk/current

# 查看风险历史
curl http://localhost:8000/risk/history

# 查看风险预警
curl http://localhost:8000/risk/alerts
```

#### 3.2 风险控制

```bash
# 设置风险限制
curl -X POST http://localhost:8000/risk/limits \
  -H "Content-Type: application/json" \
  -d '{"max_position_size": 1000000, "risk_limit": 0.1}'

# 查看风险限制
curl http://localhost:8000/risk/limits

# 更新风险限制
curl -X PUT http://localhost:8000/risk/limits \
  -H "Content-Type: application/json" \
  -d '{"max_position_size": 2000000, "risk_limit": 0.15}'
```

#### 3.3 压力测试

```bash
# 运行压力测试
curl -X POST http://localhost:8000/risk/stress_test

# 查看压力测试结果
curl http://localhost:8000/risk/stress_test/results

# 查看历史压力测试
curl http://localhost:8000/risk/stress_test/history
```

### 4. 投资组合管理

#### 4.1 投资组合查看

```bash
# 查看当前投资组合
curl http://localhost:8000/portfolio/current

# 查看投资组合历史
curl http://localhost:8000/portfolio/history

# 查看投资组合性能
curl http://localhost:8000/portfolio/performance
```

#### 4.2 投资组合操作

```bash
# 重新平衡投资组合
curl -X POST http://localhost:8000/portfolio/rebalance

# 优化投资组合
curl -X POST http://localhost:8000/portfolio/optimize

# 查看投资组合建议
curl http://localhost:8000/portfolio/recommendations
```

#### 4.3 资产配置

```bash
# 查看资产配置
curl http://localhost:8000/portfolio/allocation

# 更新资产配置
curl -X POST http://localhost:8000/portfolio/allocation \
  -H "Content-Type: application/json" \
  -d '{"00700.HK": 0.4, "2800.HK": 0.4, "0700.HK": 0.2}'

# 查看配置历史
curl http://localhost:8000/portfolio/allocation/history
```

### 5. 监控和告警

#### 5.1 系统监控

```bash
# 查看系统指标
curl http://localhost:8000/monitoring/metrics

# 查看性能指标
curl http://localhost:8000/monitoring/performance

# 查看资源使用
curl http://localhost:8000/monitoring/resources
```

#### 5.2 告警管理

```bash
# 查看活跃告警
curl http://localhost:8000/alerts/active

# 查看告警历史
curl http://localhost:8000/alerts/history

# 确认告警
curl -X POST http://localhost:8000/alerts/alert_001/acknowledge

# 解决告警
curl -X POST http://localhost:8000/alerts/alert_001/resolve
```

#### 5.3 告警配置

```bash
# 查看告警规则
curl http://localhost:8000/alerts/rules

# 创建告警规则
curl -X POST http://localhost:8000/alerts/rules \
  -H "Content-Type: application/json" \
  -d '{"name": "high_error_rate", "condition": "error_rate > 0.05", "severity": "warning"}'

# 更新告警规则
curl -X PUT http://localhost:8000/alerts/rules/rule_001 \
  -H "Content-Type: application/json" \
  -d '{"name": "high_error_rate", "condition": "error_rate > 0.03", "severity": "critical"}'
```

### 6. Telegram集成

#### 6.1 Telegram Bot使用

系统集成了Telegram Bot，支持以下命令：

- `/start` - 启动Bot
- `/help` - 查看帮助信息
- `/status` - 查看系统状态
- `/agents` - 查看Agent状态
- `/strategies` - 查看策略状态
- `/portfolio` - 查看投资组合
- `/risk` - 查看风险指标
- `/alerts` - 查看告警信息
- `/cursor_query <prompt>` - 查询Cursor AI
- `/wsl_cmd <command>` - 执行WSL命令（管理员）

#### 6.2 通知设置

```bash
# 启用Telegram通知
curl -X POST http://localhost:8000/notifications/telegram/enable

# 禁用Telegram通知
curl -X POST http://localhost:8000/notifications/telegram/disable

# 配置通知规则
curl -X POST http://localhost:8000/notifications/rules \
  -H "Content-Type: application/json" \
  -d '{"type": "risk_alert", "enabled": true, "channels": ["telegram"]}'
```

## 高级功能

### 1. 自定义策略

#### 1.1 策略开发

```python
# 示例：自定义策略
from src.strategy_management.strategy_manager import StrategyManager
from src.agents.real_agents.base_real_agent import BaseRealAgent

class MyCustomStrategy(BaseRealAgent):
    def __init__(self, config):
        super().__init__(config)
        self.name = "My Custom Strategy"
        self.description = "自定义策略示例"
    
    async def analyze_market_data(self, data):
        # 实现策略逻辑
        signal = "BUY"  # 或 "SELL" 或 "HOLD"
        confidence = 0.8
        return {
            "signal": signal,
            "confidence": confidence,
            "reasoning": "基于自定义逻辑的分析"
        }

# 注册策略
strategy_manager = StrategyManager()
await strategy_manager.register_strategy(MyCustomStrategy)
```

#### 1.2 策略回测

```bash
# 运行策略回测
curl -X POST http://localhost:8000/strategies/backtest \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_id": "my_custom_strategy",
    "start_date": "2023-01-01",
    "end_date": "2023-12-31",
    "initial_capital": 1000000
  }'

# 查看回测结果
curl http://localhost:8000/strategies/my_custom_strategy/backtest/results
```

### 2. 机器学习模型

#### 2.1 模型训练

```bash
# 训练新模型
curl -X POST http://localhost:8000/ml/models/train \
  -H "Content-Type: application/json" \
  -d '{
    "model_type": "random_forest",
    "features": ["price", "volume", "rsi", "macd"],
    "target": "price_change",
    "training_data": "2023-01-01:2023-06-30"
  }'

# 查看训练进度
curl http://localhost:8000/ml/models/training/status
```

#### 2.2 模型预测

```bash
# 使用模型预测
curl -X POST http://localhost:8000/ml/models/predict \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": "model_001",
    "features": [300.5, 1000000, 0.6, 0.02]
  }'
```

### 3. 数据分析

#### 3.1 技术指标

```bash
# 计算技术指标
curl -X POST http://localhost:8000/analysis/technical_indicators \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "00700.HK",
    "indicators": ["sma", "ema", "rsi", "macd", "bollinger_bands"],
    "period": 20
  }'
```

#### 3.2 统计分析

```bash
# 统计分析
curl -X POST http://localhost:8000/analysis/statistical \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "00700.HK",
    "analysis_type": "correlation",
    "period": 30
  }'
```

## 配置管理

### 1. 系统配置

#### 1.1 查看配置

```bash
# 查看所有配置
curl http://localhost:8000/config

# 查看特定配置
curl http://localhost:8000/config/database
curl http://localhost:8000/config/redis
curl http://localhost:8000/config/trading
```

#### 1.2 更新配置

```bash
# 更新配置
curl -X PUT http://localhost:8000/config/trading \
  -H "Content-Type: application/json" \
  -d '{
    "max_position_size": 2000000,
    "risk_limit": 0.15,
    "commission_rate": 0.001
  }'
```

### 2. Agent配置

#### 2.1 Agent参数

```bash
# 查看Agent配置
curl http://localhost:8000/agents/quantitative_analyst/config

# 更新Agent配置
curl -X PUT http://localhost:8000/agents/quantitative_analyst/config \
  -H "Content-Type: application/json" \
  -d '{
    "analysis_period": 20,
    "confidence_threshold": 0.8,
    "risk_tolerance": 0.1
  }'
```

### 3. 数据源配置

#### 3.1 数据源设置

```bash
# 查看数据源配置
curl http://localhost:8000/data/sources/config

# 更新数据源配置
curl -X PUT http://localhost:8000/data/sources/raw_data/config \
  -H "Content-Type: application/json" \
  -d '{
    "update_interval": 60,
    "data_retention_days": 365,
    "compression_enabled": true
  }'
```

## 故障排除

### 1. 常见问题

#### 1.1 系统无法启动

**症状**：系统启动失败或无法访问

**检查步骤**：
1. 检查端口是否被占用
2. 检查数据库连接
3. 检查Redis连接
4. 查看系统日志

**解决方案**：
```bash
# 检查端口占用
netstat -tulpn | grep :8000

# 检查数据库连接
psql -h localhost -U trading_user -d trading_system

# 检查Redis连接
redis-cli ping

# 查看系统日志
tail -f logs/trading_system.log
```

#### 1.2 Agent状态异常

**症状**：Agent显示错误状态或无法响应

**检查步骤**：
1. 检查Agent日志
2. 检查依赖服务
3. 检查资源配置
4. 重启Agent

**解决方案**：
```bash
# 查看Agent日志
tail -f logs/agents/quantitative_analyst.log

# 检查Agent状态
curl http://localhost:8000/agents/quantitative_analyst/status

# 重启Agent
curl -X POST http://localhost:8000/agents/quantitative_analyst/restart
```

#### 1.3 数据源连接问题

**症状**：数据源连接失败或数据更新异常

**检查步骤**：
1. 检查数据源路径
2. 检查文件权限
3. 检查网络连接
4. 验证数据格式

**解决方案**：
```bash
# 检查数据源状态
curl http://localhost:8000/data/sources/status

# 验证数据源
python scripts/validate_data_source.py --source all

# 手动更新数据
curl -X POST http://localhost:8000/data/update
```

### 2. 性能问题

#### 2.1 系统响应慢

**症状**：API响应时间过长或系统卡顿

**检查步骤**：
1. 检查CPU使用率
2. 检查内存使用率
3. 检查数据库性能
4. 检查网络延迟

**解决方案**：
```bash
# 查看系统资源
htop
free -h
df -h

# 查看数据库性能
SELECT * FROM pg_stat_activity;

# 优化数据库查询
EXPLAIN ANALYZE SELECT * FROM your_query;
```

#### 2.2 内存使用过高

**症状**：系统内存使用率持续过高

**检查步骤**：
1. 检查内存泄漏
2. 检查缓存大小
3. 检查数据量
4. 检查并发连接

**解决方案**：
```bash
# 查看内存使用
ps aux --sort=-%mem | head

# 清理缓存
curl -X POST http://localhost:8000/system/clear_cache

# 重启服务
docker-compose restart
```

### 3. 数据问题

#### 3.1 数据质量异常

**症状**：数据质量报告显示异常或数据缺失

**检查步骤**：
1. 检查数据源
2. 检查数据格式
3. 检查数据完整性
4. 检查数据更新

**解决方案**：
```bash
# 查看数据质量报告
curl http://localhost:8000/data/quality/report

# 运行数据质量检查
python scripts/data_quality_check.py

# 修复数据问题
python scripts/fix_data_issues.py
```

#### 3.2 数据同步问题

**症状**：数据不同步或更新延迟

**检查步骤**：
1. 检查数据源连接
2. 检查更新频率
3. 检查网络状态
4. 检查系统负载

**解决方案**：
```bash
# 检查数据同步状态
curl http://localhost:8000/data/sync/status

# 手动同步数据
curl -X POST http://localhost:8000/data/sync/force

# 调整同步频率
curl -X PUT http://localhost:8000/data/sync/config \
  -H "Content-Type: application/json" \
  -d '{"interval": 30}'
```

## 最佳实践

### 1. 系统维护

#### 1.1 定期检查

- **每日检查**：系统状态、Agent状态、数据更新
- **每周检查**：性能指标、风险水平、策略表现
- **每月检查**：系统更新、安全补丁、备份恢复

#### 1.2 监控告警

- **设置关键指标告警**：CPU、内存、错误率、响应时间
- **设置业务指标告警**：风险水平、策略表现、数据质量
- **设置系统指标告警**：磁盘空间、网络连接、服务状态

### 2. 风险管理

#### 2.1 风险控制

- **设置合理的风险限制**：最大持仓、风险限额、止损点
- **定期评估风险水平**：VaR计算、压力测试、情景分析
- **建立风险预警机制**：实时监控、自动告警、人工干预

#### 2.2 策略管理

- **策略多样化**：不同策略类型、不同时间周期、不同市场条件
- **策略验证**：回测验证、模拟交易、小资金实盘
- **策略监控**：实时监控、性能跟踪、风险控制

### 3. 数据管理

#### 3.1 数据质量

- **数据验证**：格式检查、完整性检查、一致性检查
- **数据清洗**：异常值处理、缺失值处理、重复值处理
- **数据监控**：质量监控、更新监控、同步监控

#### 3.2 数据安全

- **数据备份**：定期备份、增量备份、异地备份
- **数据加密**：传输加密、存储加密、访问控制
- **数据审计**：访问日志、操作日志、变更日志

## 支持和帮助

### 1. 文档资源

- **API文档**：http://localhost:8000/docs
- **系统文档**：docs/目录
- **代码文档**：代码注释和docstring
- **视频教程**：YouTube频道

### 2. 社区支持

- **GitHub Issues**：问题报告和功能请求
- **Discord社区**：实时交流和讨论
- **Stack Overflow**：技术问题解答
- **Reddit社区**：经验分享和讨论

### 3. 技术支持

- **邮件支持**：support@your-domain.com
- **电话支持**：+86-xxx-xxxx-xxxx
- **微信支持**：your-wechat-id
- **Telegram支持**：@your-telegram-username

### 4. 培训服务

- **在线培训**：系统使用培训
- **现场培训**：定制化培训服务
- **认证考试**：系统管理员认证
- **持续教育**：定期技术更新

---

**注意**：本用户手册基于当前系统版本编写，请根据实际使用情况调整操作步骤。如有问题，请参考故障排除部分或联系技术支持。
