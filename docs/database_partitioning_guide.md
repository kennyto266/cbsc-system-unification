# CBSC 数据库分区与归档系统运维指南

## 概述

本文档描述了CBSC量化交易系统数据库分区与归档系统的运维管理，包括分区表的创建、维护、监控和故障排除。

## 系统架构

### 分区策略

系统采用按时间范围的分区策略，主要针对以下时间序列表：

1. **strategy_performance** - 策略性能数据（按月分区）
2. **trades** - 交易记录（按月分区）
3. **performance_metrics** - 性能指标（按月分区）

### 数据分层策略

- **热数据 (0-30天)**: 存储在主表，支持实时查询
- **温数据 (30-90天)**: 存储在当前分区，查询性能良好
- **冷数据 (90天+)**: 归档到归档表，定期清理

## 分区表结构

### 命名规范

```
{table_name}_y{year}_m{month}
例如: strategy_performance_y2024_m12
```

### 自动分区创建

系统自动创建未来6个月的分区，确保不会出现分区缺失。

## 安装与配置

### 环境要求

- PostgreSQL 12+ (推荐 14+)
- 足够的磁盘空间 (建议为当前数据大小的2倍)
- 数据库超级用户权限用于初始配置

### 初始化步骤

1. **执行分区迁移脚本**

```bash
# 连接数据库
psql -h localhost -U postgres -d cbsc

# 执行分区创建脚本
\i migrations/partitions/001_strategy_performance_partitioned.sql
\i migrations/partitions/002_trades_partitioned.sql
\i migrations/partitions/003_performance_metrics_partitioned.sql
\i migrations/partitions/004_aggregate_views.sql
\i migrations/partitions/partition_management_functions.sql
```

2. **设置环境变量**

```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=cbsc
export DB_USER=cbsc_app
export DB_PASSWORD=your_password
```

3. **执行数据迁移**

```bash
# 运行迁移脚本
python scripts/migrate/migrate_to_partitioned.py --dry-run
python scripts/migrate/migrate_to_partitioned.py
```

## 日常运维

### 1. 分区监控

#### 检查分区状态

```sql
-- 查看分区统计信息
SELECT * FROM get_partition_statistics();

-- 检查分区健康状态
SELECT * FROM check_partition_health();
```

#### 监控查询

```sql
-- 查看分区大小
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
    pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
FROM pg_tables
WHERE tablename LIKE '%strategy_performance%'
   OR tablename LIKE '%trades%'
   OR tablename LIKE '%performance_metrics%'
ORDER BY size_bytes DESC;

-- 查看分区数据分布
SELECT
    'strategy_performance' as table_name,
    date_trunc('month', date) as partition_month,
    COUNT(*) as record_count,
    MIN(date) as min_date,
    MAX(date) as max_date
FROM strategy_performance
GROUP BY date_trunc('month', date)
ORDER BY partition_month DESC;
```

### 2. 自动分区管理

#### 创建未来分区

```sql
-- 创建未来6个月的分区
SELECT * FROM create_partitions_for_month(CURRENT_DATE, 6);
```

#### 清理旧分区

```sql
-- 查看将要删除的分区（干运行）
SELECT * FROM drop_old_partitions(24, true);

-- 实际删除24个月前的分区
SELECT * FROM drop_old_partitions(24, false);
```

### 3. 数据归档

#### 手动归档

```bash
# 归档90天前的数据
python scripts/archive/archive_performance_data.py --archive-days 90

# 查看归档统计
python scripts/archive/archive_performance_data.py --stats
```

#### 定时归档（Cron）

```bash
# 每周日凌晨2点执行归档
0 2 * * 0 /usr/bin/python3 /path/to/cbsc/scripts/archive/archive_performance_data.py --archive-days 90
```

### 4. 物化视图刷新

#### 手动刷新

```sql
-- 刷新所有性能相关物化视图
SELECT * FROM refresh_performance_views();

-- 刷新特定视图
SELECT * FROM refresh_materialized_view('strategy_daily_performance_summary');
```

#### 自动刷新（Cron）

```bash
# 每小时刷新物化视图
0 * * * * psql -h localhost -U cbsc_app -d cbsc -c "SELECT * FROM refresh_performance_views();"
```

## 性能优化

### 1. 查询优化

#### 分区裁剪

确保查询使用分区键进行过滤：

```sql
-- 好的查询（使用分区键）
SELECT * FROM strategy_performance
WHERE date >= '2024-01-01' AND date < '2024-02-01';

-- 不好的查询（无法使用分区裁剪）
SELECT * FROM strategy_performance
WHERE created_at >= '2024-01-01';
```

#### 索引使用

```sql
-- 检查索引使用情况
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE tablename LIKE '%strategy_performance%'
ORDER BY idx_scan DESC;
```

### 2. 维护操作

#### 分析和清理

```sql
-- 分析分区表统计信息
SELECT * FROM maintain_partitions(true, false, false, '%strategy_performance%');

-- 清理和压缩
SELECT * FROM maintain_partitions(false, true, false, '%strategy_performance%');

-- 完整清理（包括VACUUM FULL - 需要锁表）
SELECT * FROM maintain_partitions(true, true, true, '%strategy_performance%');
```

## 监控和告警

### 1. 关键指标

#### 分区监控指标

```sql
-- 分区数量监控
SELECT
    COUNT(*) as total_partitions,
    COUNT(DISTINCT DATE_PART('year', SUBSTRING(tablename FROM '......$')::DATE)) as years_covered
FROM pg_tables
WHERE tablename LIKE 'strategy_performance_y%';
```

#### 性能监控指标

```sql
-- 查询性能监控
SELECT
    query,
    calls,
    total_exec_time,
    mean_exec_time,
    rows
FROM pg_stat_statements
WHERE query LIKE '%strategy_performance%'
ORDER BY total_exec_time DESC
LIMIT 10;
```

### 2. 告警设置

#### 分区缺失告警

```sql
-- 检查缺失的分区
WITH expected_partitions AS (
    SELECT
        'strategy_performance_y' || EXTRACT(YEAR FROM date) || '_m' || LPAD(EXTRACT(MONTH FROM date)::TEXT, 2, '0') as partition_name
    FROM generate_series(CURRENT_DATE, CURRENT_DATE + INTERVAL '6 months', INTERVAL '1 month') as date
)
SELECT ep.partition_name as missing_partition
FROM expected_partitions ep
LEFT JOIN pg_tables pt ON ep.partition_name = pt.tablename
WHERE pt.tablename IS NULL;
```

#### 磁盘空间告警

```bash
# 检查磁盘使用
df -h /var/lib/postgresql/data

# 检查数据库大小
psql -c "SELECT pg_size_pretty(pg_database_size('cbsc'));"
```

## 故障排除

### 1. 常见问题

#### 分区创建失败

**问题**: 新数据插入时分区不存在
**解决**: 手动创建缺失的分区

```sql
-- 手动创建特定月份的分区
SELECT create_partitions_for_month('2024-12-01', 1);
```

#### 查询性能下降

**问题**: 查询变慢
**排查步骤**:

1. 检查查询是否使用分区键
2. 更新表统计信息: `ANALYZE strategy_performance;`
3. 检查索引是否正常: `\d+ strategy_performance_y2024_m12`
4. 查看执行计划: `EXPLAIN ANALYZE SELECT ...`

#### 归档失败

**问题**: 数据归档中断
**排查步骤**:

1. 检查磁盘空间
2. 检查数据库连接
3. 查看归档日志: `tail -f /var/log/cbsc/archive.log`

### 2. 紧急恢复

#### 回滚迁移

```bash
# 回滚特定表
python scripts/migrate/migrate_to_partitioned.py --rollback strategy_performance

# 验证回滚
python scripts/migrate/migrate_to_partitioned.py --validate strategy_performance
```

#### 从备份恢复

```sql
-- 如果有物理备份
-- 停止PostgreSQL服务
systemctl stop postgresql

-- 恢复数据文件
cp -r /backup/cbsc/* /var/lib/postgresql/data/

-- 启动PostgreSQL服务
systemctl start postgresql
```

## 定期任务

### 每日任务

1. **检查分区健康状态**
   ```sql
   SELECT * FROM check_partition_health();
   ```

2. **刷新物化视图**
   ```bash
   psql -c "SELECT * FROM refresh_performance_views();"
   ```

3. **监控系统性能**
   ```bash
   python scripts/migrate/performance_test.py --table-suffix ""
   ```

### 每周任务

1. **数据归档**
   ```bash
   python scripts/archive/archive_performance_data.py --archive-days 90
   ```

2. **清理旧分区**
   ```sql
   SELECT * FROM drop_old_partitions(12, false); -- 保留12个月
   ```

### 每月任务

1. **创建未来分区**
   ```sql
   SELECT * FROM create_partitions_for_month(CURRENT_DATE, 6);
   ```

2. **表维护**
   ```sql
   SELECT * FROM maintain_partitions(true, true, false);
   ```

## 性能基准

### 预期性能提升

- 时间范围查询: 50-80% 性能提升
- 聚合查询: 60-90% 性能提升
- 数据加载: 30-50% 性能提升
- 存储效率: 20-40% 空间节省

### 基准测试

运行性能测试脚本验证改进：

```bash
python scripts/migrate/performance_test.py --comparison
```

## 最佳实践

### 1. 查询设计

- 总是包含分区键（日期字段）在WHERE条件中
- 使用物化视图进行复杂聚合查询
- 避免跨分区的JOIN操作

### 2. 分区管理

- 定期检查分区健康状态
- 提前创建未来分区
- 及时清理旧分区

### 3. 监控和告警

- 设置磁盘空间监控告警
- 监控查询性能变化
- 定期运行健康检查

## 联系信息

- **数据库管理员**: dba@cbsc.com
- **开发团队**: dev@cbsc.com
- **运维支持**: ops@cbsc.com

---

*文档版本: 1.0*
*最后更新: 2025-12-11*
*维护者: CBSC 数据库团队*