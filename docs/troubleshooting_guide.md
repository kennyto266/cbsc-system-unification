# 港股量化交易AI Agent系统 - 故障排除指南

## 概述

本指南提供了港股量化交易AI Agent系统常见问题的诊断和解决方案，帮助用户快速定位和解决问题。

## 系统启动问题

### 问题1：系统无法启动

**症状**：
- 系统启动失败
- 端口被占用
- 服务无法访问

**诊断步骤**：

1. **检查端口占用**
```bash
# Windows
netstat -ano | findstr :8000

# Linux/macOS
netstat -tulpn | grep :8000
lsof -i :8000
```

2. **检查系统日志**
```bash
# 查看系统日志
tail -f logs/trading_system.log

# 查看错误日志
grep ERROR logs/trading_system.log
```

3. **检查依赖服务**
```bash
# 检查PostgreSQL
psql -h localhost -U trading_user -d trading_system

# 检查Redis
redis-cli ping
```

**解决方案**：

1. **释放端口**
```bash
# Windows
taskkill /PID <进程ID> /F

# Linux/macOS
kill -9 <进程ID>
```

2. **重启依赖服务**
```bash
# PostgreSQL
sudo systemctl restart postgresql

# Redis
sudo systemctl restart redis
```

3. **重新启动系统**
```bash
# 使用Docker Compose
docker-compose restart

# 或使用Python
python -m src.integration.system_integration
```

### 问题2：数据库连接失败

**症状**：
- 数据库连接错误
- 认证失败
- 连接超时

**诊断步骤**：

1. **检查数据库状态**
```bash
# PostgreSQL状态
sudo systemctl status postgresql

# 检查连接
psql -h localhost -U trading_user -d trading_system
```

2. **检查配置文件**
```bash
# 检查环境变量
echo $DATABASE_URL

# 检查配置文件
cat .env | grep DATABASE
```

3. **检查网络连接**
```bash
# 测试连接
telnet localhost 5432
```

**解决方案**：

1. **修复数据库配置**
```bash
# 更新.env文件
DATABASE_URL=postgresql://trading_user:password@localhost:5432/trading_system
```

2. **重置数据库密码**
```bash
# 连接到PostgreSQL
psql -U postgres

# 重置密码
ALTER USER trading_user PASSWORD 'new_password';
```

3. **检查防火墙设置**
```bash
# 检查防火墙规则
sudo ufw status
sudo ufw allow 5432
```

### 问题3：Redis连接失败

**症状**：
- Redis连接错误
- 缓存功能异常
- 消息队列失败

**诊断步骤**：

1. **检查Redis状态**
```bash
# Redis状态
sudo systemctl status redis

# 测试连接
redis-cli ping
```

2. **检查Redis配置**
```bash
# 查看Redis配置
redis-cli config get bind
redis-cli config get port
```

**解决方案**：

1. **重启Redis服务**
```bash
sudo systemctl restart redis
```

2. **检查Redis配置**
```bash
# 编辑Redis配置
sudo nano /etc/redis/redis.conf

# 确保绑定到正确地址
bind 127.0.0.1
port 6379
```

## Agent相关问题

### 问题4：Agent无法启动

**症状**：
- Agent状态显示错误
- Agent无响应
- 处理信号失败

**诊断步骤**：

1. **检查Agent日志**
```bash
# 查看Agent日志
tail -f logs/agents/quantitative_analyst.log
```

2. **检查Agent配置**
```bash
# 查看Agent配置
curl http://localhost:8000/agents/quantitative_analyst/config
```

3. **检查依赖服务**
```bash
# 检查数据源
curl http://localhost:8000/data/sources/status
```

**解决方案**：

1. **重启Agent**
```bash
# 停止Agent
curl -X POST http://localhost:8000/agents/quantitative_analyst/stop

# 启动Agent
curl -X POST http://localhost:8000/agents/quantitative_analyst/start
```

2. **检查Agent配置**
```bash
# 更新Agent配置
curl -X PUT http://localhost:8000/agents/quantitative_analyst/config \
  -H "Content-Type: application/json" \
  -d '{"analysis_period": 20, "confidence_threshold": 0.8}'
```

### 问题5：Agent性能问题

**症状**：
- Agent响应缓慢
- 处理信号延迟
- 内存使用过高

**诊断步骤**：

1. **检查系统资源**
```bash
# 查看CPU和内存使用
htop
free -h
```

2. **检查Agent性能指标**
```bash
# 查看Agent性能
curl http://localhost:8000/agents/quantitative_analyst/performance
```

3. **检查日志**
```bash
# 查看性能日志
grep "performance" logs/agents/quantitative_analyst.log
```

**解决方案**：

1. **优化Agent配置**
```bash
# 调整处理间隔
curl -X PUT http://localhost:8000/agents/quantitative_analyst/config \
  -H "Content-Type: application/json" \
  -d '{"update_interval": 120}'
```

2. **增加系统资源**
```bash
# 增加内存限制
docker-compose up -d --scale app=2
```

## 数据源问题

### 问题6：数据源连接失败

**症状**：
- 数据源状态显示断开
- 数据更新失败
- 数据质量异常

**诊断步骤**：

1. **检查数据源状态**
```bash
# 查看数据源状态
curl http://localhost:8000/data/sources/status
```

2. **检查数据路径**
```bash
# 检查数据文件
ls -la /path/to/data/source
```

3. **检查数据格式**
```bash
# 验证数据格式
python scripts/validate_data_format.py
```

**解决方案**：

1. **修复数据路径**
```bash
# 更新数据路径配置
curl -X PUT http://localhost:8000/data/sources/raw_data/config \
  -H "Content-Type: application/json" \
  -d '{"source_path": "/correct/path/to/data"}'
```

2. **重新同步数据**
```bash
# 强制更新数据
curl -X POST http://localhost:8000/data/update
```

### 问题7：数据质量异常

**症状**：
- 数据质量报告显示异常
- 数据缺失或错误
- 数据同步失败

**诊断步骤**：

1. **查看数据质量报告**
```bash
# 获取数据质量报告
curl http://localhost:8000/data/quality/report
```

2. **检查数据完整性**
```bash
# 运行数据质量检查
python scripts/data_quality_check.py
```

**解决方案**：

1. **修复数据问题**
```bash
# 运行数据修复脚本
python scripts/fix_data_issues.py
```

2. **重新导入数据**
```bash
# 重新导入数据
python scripts/import_data.py --force
```

## 策略问题

### 问题8：策略无法启动

**症状**：
- 策略状态显示错误
- 策略无响应
- 回测失败

**诊断步骤**：

1. **检查策略状态**
```bash
# 查看策略状态
curl http://localhost:8000/strategies/strategy_001/status
```

2. **检查策略配置**
```bash
# 查看策略配置
curl http://localhost:8000/strategies/strategy_001/config
```

**解决方案**：

1. **重启策略**
```bash
# 停止策略
curl -X POST http://localhost:8000/strategies/strategy_001/stop

# 启动策略
curl -X POST http://localhost:8000/strategies/strategy_001/start
```

2. **修复策略配置**
```bash
# 更新策略配置
curl -X PUT http://localhost:8000/strategies/strategy_001/config \
  -H "Content-Type: application/json" \
  -d '{"parameters": {"lookback_period": 20, "threshold": 0.02}}'
```

### 问题9：回测失败

**症状**：
- 回测任务失败
- 回测结果异常
- 回测超时

**诊断步骤**：

1. **检查回测状态**
```bash
# 查看回测状态
curl http://localhost:8000/strategies/strategy_001/backtest/status
```

2. **检查回测日志**
```bash
# 查看回测日志
tail -f logs/backtest/strategy_001.log
```

**解决方案**：

1. **重新运行回测**
```bash
# 重新提交回测任务
curl -X POST http://localhost:8000/strategies/backtest \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_id": "strategy_001",
    "start_date": "2023-01-01",
    "end_date": "2023-12-31",
    "initial_capital": 1000000
  }'
```

2. **调整回测参数**
```bash
# 减少回测时间范围
curl -X POST http://localhost:8000/strategies/backtest \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_id": "strategy_001",
    "start_date": "2023-06-01",
    "end_date": "2023-12-31",
    "initial_capital": 1000000
  }'
```

## 性能问题

### 问题10：系统响应缓慢

**症状**：
- API响应时间过长
- 系统卡顿
- 超时错误

**诊断步骤**：

1. **检查系统资源**
```bash
# 查看系统资源使用
htop
iostat -x 1
```

2. **检查数据库性能**
```bash
# 查看数据库连接
psql -c "SELECT * FROM pg_stat_activity;"

# 查看慢查询
psql -c "SELECT query, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"
```

**解决方案**：

1. **优化数据库查询**
```sql
-- 创建索引
CREATE INDEX idx_symbol_timestamp ON market_data(symbol, timestamp);

-- 分析表
ANALYZE market_data;
```

2. **调整系统配置**
```bash
# 增加数据库连接池
curl -X PUT http://localhost:8000/config/database \
  -H "Content-Type: application/json" \
  -d '{"pool_size": 20}'
```

### 问题11：内存使用过高

**症状**：
- 内存使用率持续过高
- 系统变慢
- 内存不足错误

**诊断步骤**：

1. **检查内存使用**
```bash
# 查看内存使用
free -h
ps aux --sort=-%mem | head
```

2. **检查内存泄漏**
```bash
# 查看Python进程内存
ps -o pid,ppid,cmd,%mem,%cpu -p $(pgrep python)
```

**解决方案**：

1. **清理缓存**
```bash
# 清理系统缓存
curl -X POST http://localhost:8000/system/clear_cache
```

2. **重启服务**
```bash
# 重启服务释放内存
docker-compose restart
```

3. **增加内存限制**
```bash
# 增加Docker内存限制
docker-compose up -d --scale app=2
```

## 监控和告警问题

### 问题12：监控数据异常

**症状**：
- 监控指标异常
- 告警不准确
- 监控服务停止

**诊断步骤**：

1. **检查监控服务**
```bash
# 查看监控服务状态
curl http://localhost:8000/monitoring/status
```

2. **检查监控配置**
```bash
# 查看监控配置
curl http://localhost:8000/monitoring/config
```

**解决方案**：

1. **重启监控服务**
```bash
# 重启监控服务
curl -X POST http://localhost:8000/monitoring/restart
```

2. **调整监控阈值**
```bash
# 更新监控阈值
curl -X PUT http://localhost:8000/monitoring/thresholds \
  -H "Content-Type: application/json" \
  -d '{"cpu_threshold": 80, "memory_threshold": 90}'
```

### 问题13：告警不工作

**症状**：
- 告警未触发
- 告警通知失败
- 告警规则错误

**诊断步骤**：

1. **检查告警规则**
```bash
# 查看告警规则
curl http://localhost:8000/alerts/rules
```

2. **检查告警历史**
```bash
# 查看告警历史
curl http://localhost:8000/alerts/history
```

**解决方案**：

1. **修复告警规则**
```bash
# 更新告警规则
curl -X PUT http://localhost:8000/alerts/rules/rule_001 \
  -H "Content-Type: application/json" \
  -d '{"condition": "cpu_usage > 0.8", "severity": "warning"}'
```

2. **测试告警**
```bash
# 触发测试告警
curl -X POST http://localhost:8000/alerts/test
```

## 网络问题

### 问题14：网络连接问题

**症状**：
- 网络连接失败
- 数据传输中断
- 外部服务不可达

**诊断步骤**：

1. **检查网络连接**
```bash
# 测试网络连接
ping google.com
telnet localhost 8000
```

2. **检查防火墙设置**
```bash
# 检查防火墙状态
sudo ufw status
```

**解决方案**：

1. **修复网络配置**
```bash
# 重启网络服务
sudo systemctl restart networking
```

2. **调整防火墙规则**
```bash
# 允许必要端口
sudo ufw allow 8000
sudo ufw allow 5432
sudo ufw allow 6379
```

## 日志分析

### 问题15：日志文件过大

**症状**：
- 日志文件占用大量磁盘空间
- 系统性能下降
- 日志查看困难

**解决方案**：

1. **配置日志轮转**
```bash
# 编辑logrotate配置
sudo nano /etc/logrotate.d/trading_system

# 添加配置
/path/to/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
}
```

2. **清理旧日志**
```bash
# 清理7天前的日志
find logs/ -name "*.log" -mtime +7 -delete
```

### 问题16：日志级别问题

**症状**：
- 日志信息不足
- 日志过于详细
- 调试困难

**解决方案**：

1. **调整日志级别**
```bash
# 更新日志级别
curl -X PUT http://localhost:8000/config/logging \
  -H "Content-Type: application/json" \
  -d '{"level": "DEBUG"}'
```

2. **重启日志服务**
```bash
# 重启日志服务
curl -X POST http://localhost:8000/logging/restart
```

## 紧急恢复

### 问题17：系统完全崩溃

**症状**：
- 系统无法启动
- 所有服务停止
- 数据丢失

**紧急恢复步骤**：

1. **停止所有服务**
```bash
# 停止Docker服务
docker-compose down

# 停止所有Python进程
pkill -f python
```

2. **检查系统状态**
```bash
# 检查磁盘空间
df -h

# 检查内存使用
free -h

# 检查系统负载
uptime
```

3. **恢复数据**
```bash
# 从备份恢复数据库
pg_restore -h localhost -U trading_user -d trading_system backup.sql

# 恢复配置文件
cp config/backup/* config/
```

4. **重新启动系统**
```bash
# 启动依赖服务
sudo systemctl start postgresql
sudo systemctl start redis

# 启动应用
docker-compose up -d
```

## 预防措施

### 定期维护

1. **每日检查**
- 系统状态
- Agent状态
- 数据更新
- 错误日志

2. **每周检查**
- 性能指标
- 磁盘空间
- 数据库性能
- 备份状态

3. **每月检查**
- 系统更新
- 安全补丁
- 配置优化
- 容量规划

### 监控设置

1. **关键指标监控**
- CPU使用率
- 内存使用率
- 磁盘使用率
- 网络连接

2. **业务指标监控**
- 交易成功率
- 策略表现
- 风险水平
- 数据质量

3. **告警设置**
- 资源使用告警
- 错误率告警
- 性能告警
- 业务告警

## 联系支持

### 技术支持

- **邮件支持**：support@your-domain.com
- **电话支持**：+86-xxx-xxxx-xxxx
- **微信支持**：your-wechat-id
- **Telegram支持**：@your-telegram-username

### 紧急联系

- **24小时热线**：+86-xxx-xxxx-xxxx
- **紧急邮箱**：emergency@your-domain.com
- **在线支持**：https://support.your-domain.com

---

**注意**：本故障排除指南基于常见问题编写，如遇到未涵盖的问题，请及时联系技术支持团队。
