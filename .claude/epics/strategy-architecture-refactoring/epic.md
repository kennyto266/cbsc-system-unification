---
name: strategy-architecture-refactoring
status: completed
created: 2025-12-10T14:05:12Z
updated: 2025-12-15T14:30:00Z
progress: 100%
prd: .claude/prds/strategy-architecture-refactoring.md
github: https://github.com/kennyto266/cbsc-system-unification/issues/19
completion-date: 2025-12-15T14:30:00Z
---

# Epic: 策略架构重构技术实施计划

## 📋 Executive Summary

本Epic是对PRD `strategy-architecture-refactoring` 的技术实施方案，通过4个独立阶段的渐进式重构，解决CBSC策略系统的技术债务问题。

**核心目标**：
- ✅ 消除代码重复（30% → <10%）
- ✅ 统一缓存管理（命中率 >80%）
- ✅ 优化数据存储（查询性能 +50%）
- ✅ 规范连接管理（支持10x用户增长）

**实施周期**: 8-12周，分4个Phase独立交付
**风险等级**: 中（通过灰度发布和完整回滚方案控制）

## 🎯 Technical Approach

### 架构设计原则

1. **渐进式重构 (Incremental Refactoring)**
   - 每个Phase独立交付，可独立验证
   - 保持系统持续可用
   - 支持快速回滚

2. **向后兼容 (Backward Compatibility)**
   - API接口保持兼容
   - 使用特性开关（Feature Flags）
   - 双写机制确保数据一致性

3. **可观测性优先 (Observability First)**
   - 每个Phase添加监控指标
   - Prometheus + Grafana仪表板
   - 完整的日志和追踪

4. **测试驱动 (Test-Driven)**
   - 测试覆盖率 >80%
   - 性能基准测试
   - 回归测试全覆盖

### 技术栈选择

```yaml
Backend:
  Framework: FastAPI
  Language: Python 3.8+
  ORM: SQLAlchemy
  Cache: Redis + cachetools (内存)
  WebSocket: FastAPI WebSocket + Socket.IO

Database:
  Primary: PostgreSQL 12+
  Cache: Redis 7+
  Features: 分区表、物化视图、JSONB

Monitoring:
  Metrics: Prometheus
  Visualization: Grafana
  Tracing: Jaeger (可选)
  Logging: Structured JSON logs

Testing:
  Unit: pytest + pytest-cov
  Integration: pytest + httpx
  E2E: Playwright
  Load: Locust
```

### 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                   重构后的架构                               │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ API层 (src/api/strategies/)                                │
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│ │  base.py     │ │ execution.py │ │ personal.py  │        │
│ │  CRUD操作    │ │  策略执行    │ │  个性化功能  │        │
│ └──────────────┘ └──────────────┘ └──────────────┘        │
│         │                │                │                 │
│         └────────────────┴────────────────┘                 │
│                          ↓                                  │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 服务层 (Service Layer)                                      │
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│ │CacheManager  │ │StrategyMgr   │ │ConnectionPool│        │
│ │ L1: 内存     │ │  业务逻辑    │ │ WebSocket   │        │
│ │ L2: Redis    │ │              │ │  连接管理    │        │
│ └──────────────┘ └──────────────┘ └──────────────┘        │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 数据层 (Data Layer)                                         │
│ ┌────────────────────────────────────────────────┐         │
│ │ PostgreSQL (分区表)                             │         │
│ │ ├─ strategy_performance_2025_01 (热数据)       │         │
│ │ ├─ strategy_performance_2024_12 (温数据)       │         │
│ │ ├─ strategy_performance_archive (冷数据)       │         │
│ │ └─ strategy_daily_summary (物化视图)           │         │
│ └────────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

## 📅 Phase Breakdown

### Phase 1: API端点整合 (Week 1-3)

#### 目标
消除三个API文件的代码重复，建立清晰的模块边界。

#### 技术方案

**1. 新的模块结构**
```python
src/api/strategies/
├── __init__.py              # 路由聚合
│   └── router = APIRouter(prefix="/api/strategies")
│
├── base.py                  # 基础CRUD
│   ├── list_strategies()    # GET /strategies
│   ├── get_strategy()       # GET /strategies/{id}
│   ├── create_strategy()    # POST /strategies
│   ├── update_strategy()    # PUT /strategies/{id}
│   └── delete_strategy()    # DELETE /strategies/{id}
│
├── execution.py             # 策略执行引擎
│   ├── execute_strategy()   # POST /strategies/{id}/execute
│   ├── get_execution_status() # GET /strategies/{id}/executions
│   ├── validate_config()    # POST /strategies/{id}/validate
│   └── get_signals()        # GET /strategies/{id}/signals
│
├── personal.py              # 个性化功能
│   ├── get_user_strategies() # GET /personal/strategies
│   ├── get_dashboard_data()  # GET /personal/dashboard
│   ├── set_preferences()     # PUT /personal/preferences
│   └── get_alerts()          # GET /personal/alerts
│
├── websocket.py             # WebSocket处理
│   ├── websocket_endpoint() # WS /ws/strategies
│   ├── handle_subscribe()
│   └── handle_unsubscribe()
│
├── models.py                # 数据模型
│   └── (保留现有models)
│
└── schemas.py               # Pydantic schemas
    ├── StrategyCreate
    ├── StrategyUpdate
    ├── StrategyResponse
    └── ExecutionRequest
```

**2. 迁移策略**

```python
# Step 1: 创建新模块（保留旧文件）
# 标记旧文件为deprecated

# strategy_endpoints.py (保留)
import warnings
warnings.warn(
    "strategy_endpoints.py is deprecated. Use strategies.base instead",
    DeprecationWarning
)
from .strategies.base import *  # 重新导出

# Step 2: 使用Feature Flag控制路由
USE_NEW_STRATEGY_API = os.getenv("USE_NEW_STRATEGY_API", "false") == "true"

if USE_NEW_STRATEGY_API:
    from api.strategies import router as strategy_router
else:
    from api.strategy_endpoints import router as strategy_router

app.include_router(strategy_router)

# Step 3: 灰度发布（5% → 25% → 50% → 100%）
# Step 4: 验证后删除旧文件
```

**3. 代码去重**

```python
# Before: 重复的CRUD代码在3个文件中

# After: 统一的基类
class BaseStrategyService:
    """Base service for strategy operations"""

    def __init__(self, db_session, cache_manager):
        self.db = db_session
        self.cache = cache_manager

    async def get_strategy(self, strategy_id: str) -> Strategy:
        """Get strategy with caching"""
        # 统一的获取逻辑
        cached = await self.cache.get(f"strategy:{strategy_id}")
        if cached:
            return cached

        strategy = await self.db.query(Strategy).filter(...).first()
        await self.cache.set(f"strategy:{strategy_id}", strategy, ttl=300)
        return strategy

# 继承复用
class StrategyExecutionService(BaseStrategyService):
    async def execute(self, strategy_id: str, params: dict):
        strategy = await self.get_strategy(strategy_id)  # 复用基类方法
        # 执行逻辑
```

#### 交付物

- [ ] 新的模块化代码结构（`src/api/strategies/`）
- [ ] 单元测试覆盖率 >80%
- [ ] API文档更新（Swagger/OpenAPI）
- [ ] 迁移指南文档
- [ ] 性能对比报告（重构前后）

#### 验收标准

```yaml
Code Quality:
  - 代码重复率 <15%（目标 <10%）
  - Pylint评分 >8.5/10
  - 所有API端点有测试

Performance:
  - API响应时间不倒退
  - P95 ≤ 200ms

Compatibility:
  - 所有现有API调用正常工作
  - 前端无需修改
```

---

### Phase 2: 缓存策略统一 (Week 4-6)

#### 目标
建立统一的缓存管理层，提升性能和数据一致性。

#### 技术方案

**1. CacheManager设计**

```python
from typing import Optional, Any
from cachetools import TTLCache
import redis.asyncio as redis
import json
from dataclasses import dataclass

@dataclass
class CacheStrategy:
    """Cache strategy configuration"""
    ttl: int                # Time to live in seconds
    level: str              # 'L1' | 'L2' | 'L1+L2'
    serializer: str = 'json' # 'json' | 'pickle'

class CacheManager:
    """Unified cache management"""

    def __init__(self, redis_url: Optional[str] = None):
        # L1: In-memory cache (fast, per-instance)
        self.memory_cache = TTLCache(
            maxsize=1000,
            ttl=60
        )

        # L2: Redis cache (shared, persistent)
        self.redis_client = redis.from_url(redis_url) if redis_url else None

        # Cache strategies for different data types
        self.strategies = {
            'strategy:*': CacheStrategy(ttl=300, level='L2'),      # 5分钟
            'performance:*': CacheStrategy(ttl=30, level='L1'),    # 30秒
            'user:*': CacheStrategy(ttl=60, level='L1+L2'),        # 1分钟
            'config:*': CacheStrategy(ttl=600, level='L2'),        # 10分钟
        }

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache with L1 → L2 fallback"""
        strategy = self._get_strategy(key)

        # Try L1 first
        if 'L1' in strategy.level:
            value = self.memory_cache.get(key)
            if value is not None:
                self._record_hit('L1', key)
                return value

        # Fallback to L2
        if 'L2' in strategy.level and self.redis_client:
            value = await self.redis_client.get(key)
            if value:
                self._record_hit('L2', key)
                deserialized = self._deserialize(value, strategy.serializer)

                # Populate L1 cache
                if 'L1' in strategy.level:
                    self.memory_cache[key] = deserialized

                return deserialized

        self._record_miss(key)
        return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in appropriate cache level(s)"""
        strategy = self._get_strategy(key)
        final_ttl = ttl or strategy.ttl

        # Set in L1
        if 'L1' in strategy.level:
            # TTLCache handles expiration automatically
            self.memory_cache[key] = value

        # Set in L2
        if 'L2' in strategy.level and self.redis_client:
            serialized = self._serialize(value, strategy.serializer)
            await self.redis_client.setex(key, final_ttl, serialized)

    async def delete(self, key: str):
        """Delete from all cache levels"""
        # Delete from L1
        self.memory_cache.pop(key, None)

        # Delete from L2
        if self.redis_client:
            await self.redis_client.delete(key)

    async def clear_pattern(self, pattern: str):
        """Clear all keys matching pattern"""
        # Clear L1
        keys_to_delete = [k for k in self.memory_cache.keys() if self._match_pattern(k, pattern)]
        for key in keys_to_delete:
            del self.memory_cache[key]

        # Clear L2
        if self.redis_client:
            keys = await self.redis_client.keys(pattern)
            if keys:
                await self.redis_client.delete(*keys)

    def _get_strategy(self, key: str) -> CacheStrategy:
        """Get cache strategy for key"""
        for pattern, strategy in self.strategies.items():
            if self._match_pattern(key, pattern):
                return strategy
        return CacheStrategy(ttl=60, level='L1')  # Default

    def _serialize(self, value: Any, method: str) -> str:
        if method == 'json':
            return json.dumps(value, default=str)
        elif method == 'pickle':
            import pickle
            return pickle.dumps(value)
        return str(value)

    def _deserialize(self, value: str, method: str) -> Any:
        if method == 'json':
            return json.loads(value)
        elif method == 'pickle':
            import pickle
            return pickle.loads(value)
        return value

    def _match_pattern(self, key: str, pattern: str) -> bool:
        """Simple pattern matching (supports *)"""
        import re
        regex = pattern.replace('*', '.*')
        return re.match(regex, key) is not None

    # Metrics collection
    def _record_hit(self, level: str, key: str):
        # Increment Prometheus counter
        pass

    def _record_miss(self, key: str):
        # Increment Prometheus counter
        pass

# Global instance
cache_manager = CacheManager(redis_url=settings.REDIS_URL)
```

**2. 集成到现有代码**

```python
# Before: 分散的缓存
class StrategyManager:
    def __init__(self):
        self.performance_cache = {}  # 简单dict
        self.config_cache = {}

# After: 使用统一缓存
class StrategyManager:
    def __init__(self, cache: CacheManager):
        self.cache = cache

    async def get_performance(self, strategy_id: str):
        # 自动使用正确的缓存策略
        perf = await self.cache.get(f"performance:{strategy_id}")
        if not perf:
            perf = await self.db.query(StrategyPerformance).filter(...).first()
            await self.cache.set(f"performance:{strategy_id}", perf)
        return perf
```

**3. 监控指标**

```python
from prometheus_client import Counter, Gauge, Histogram

# Cache metrics
cache_hits = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['level', 'key_prefix']
)

cache_misses = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['key_prefix']
)

cache_memory_bytes = Gauge(
    'cache_memory_bytes',
    'Cache memory usage in bytes',
    ['level']
)

cache_operation_duration = Histogram(
    'cache_operation_duration_seconds',
    'Cache operation duration',
    ['operation', 'level']
)
```

#### 交付物

- [ ] CacheManager实现（`src/services/cache_manager.py`）
- [ ] 集成到所有Manager类
- [ ] Prometheus指标导出
- [ ] Grafana仪表板配置
- [ ] 缓存使用指南文档
- [ ] 性能测试报告

#### 验收标准

```yaml
Performance:
  - 缓存命中率 >75%（目标 >80%）
  - 内存使用 <1GB且稳定
  - 缓存操作延迟 <5ms

Reliability:
  - 无缓存不一致问题
  - Redis故障时自动降级到L1
  - 缓存雪崩防护生效

Monitoring:
  - 所有指标正常导出
  - Grafana仪表板正常显示
  - 告警规则配置完成
```

---

### Phase 3: 性能数据归档 (Week 7-9)

#### 目标
优化时间序列数据存储，提升查询性能。

#### 技术方案

**1. 分区表设计**

```sql
-- 创建分区表
CREATE TABLE strategy_performance (
    id BIGSERIAL,
    strategy_id VARCHAR(36) NOT NULL,
    config_id VARCHAR(36),
    date TIMESTAMPTZ NOT NULL,
    total_return DOUBLE PRECISION NOT NULL,
    daily_return DOUBLE PRECISION,
    cumulative_return DOUBLE PRECISION NOT NULL,
    -- 风险指标
    volatility DOUBLE PRECISION,
    sharpe_ratio DOUBLE PRECISION,
    sortino_ratio DOUBLE PRECISION,
    max_drawdown DOUBLE PRECISION,
    var_95 DOUBLE PRECISION,
    cvar_95 DOUBLE PRECISION,
    -- 交易统计
    total_trades INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    win_rate DOUBLE PRECISION DEFAULT 0.0,
    profit_factor DOUBLE PRECISION,
    -- 持仓信息
    current_positions INTEGER DEFAULT 0,
    open_positions_value DOUBLE PRECISION DEFAULT 0.0,
    cash_balance DOUBLE PRECISION DEFAULT 0.0,
    -- 元数据
    market_conditions JSONB,
    data_quality_score DOUBLE PRECISION DEFAULT 1.0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    -- 分区键
    PRIMARY KEY (id, date)
) PARTITION BY RANGE (date);

-- 创建索引
CREATE INDEX idx_strategy_perf_date ON strategy_performance (strategy_id, date DESC);
CREATE INDEX idx_strategy_perf_created ON strategy_performance (created_at);

-- 自动创建分区的函数
CREATE OR REPLACE FUNCTION create_partition_if_not_exists(
    target_date DATE
) RETURNS VOID AS $$
DECLARE
    partition_name TEXT;
    start_date DATE;
    end_date DATE;
BEGIN
    -- 计算分区名称和范围
    partition_name := 'strategy_performance_' || TO_CHAR(target_date, 'YYYY_MM');
    start_date := DATE_TRUNC('month', target_date);
    end_date := start_date + INTERVAL '1 month';

    -- 检查分区是否存在
    IF NOT EXISTS (
        SELECT 1 FROM pg_class WHERE relname = partition_name
    ) THEN
        -- 创建分区
        EXECUTE format(
            'CREATE TABLE %I PARTITION OF strategy_performance
             FOR VALUES FROM (%L) TO (%L)',
            partition_name, start_date, end_date
        );

        RAISE NOTICE 'Created partition: %', partition_name;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- 自动维护分区的触发器
CREATE OR REPLACE FUNCTION auto_create_partition()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM create_partition_if_not_exists(NEW.date::DATE);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_auto_partition
BEFORE INSERT ON strategy_performance
FOR EACH ROW
EXECUTE FUNCTION auto_create_partition();

-- 提前创建未来3个月的分区
DO $$
DECLARE
    i INTEGER;
BEGIN
    FOR i IN 0..2 LOOP
        PERFORM create_partition_if_not_exists(
            CURRENT_DATE + (i || ' months')::INTERVAL
        );
    END LOOP;
END $$;
```

**2. 数据归档系统**

```sql
-- 创建归档表
CREATE TABLE strategy_performance_archive (
    LIKE strategy_performance INCLUDING ALL
);

-- 添加归档标记
ALTER TABLE strategy_performance_archive
ADD COLUMN archived_at TIMESTAMPTZ DEFAULT NOW();

-- 归档脚本（Python）
```

```python
# scripts/archive_performance_data.py
import asyncio
from datetime import datetime, timedelta
from sqlalchemy import select, delete
from models import StrategyPerformance, StrategyPerformanceArchive

async def archive_old_data(cutoff_days: int = 90):
    """Archive data older than cutoff_days"""
    cutoff_date = datetime.now() - timedelta(days=cutoff_days)

    async with db.begin() as session:
        # Select old data
        stmt = select(StrategyPerformance).where(
            StrategyPerformance.date < cutoff_date
        )
        old_data = await session.execute(stmt)

        archived_count = 0
        for row in old_data.scalars():
            # Copy to archive table
            archive_row = StrategyPerformanceArchive(**row.__dict__)
            session.add(archive_row)
            archived_count += 1

            # Delete from main table
            await session.delete(row)

            # Commit in batches
            if archived_count % 1000 == 0:
                await session.commit()
                print(f"Archived {archived_count} records...")

        await session.commit()
        print(f"✅ Total archived: {archived_count} records")

        # Vacuum to reclaim space
        await session.execute("VACUUM ANALYZE strategy_performance")

if __name__ == "__main__":
    asyncio.run(archive_old_data(cutoff_days=90))
```

**3. 聚合视图（加速查询）**

```sql
-- 每日汇总视图
CREATE MATERIALIZED VIEW strategy_daily_summary AS
SELECT
    strategy_id,
    DATE(date) as summary_date,
    COUNT(*) as record_count,
    AVG(total_return) as avg_return,
    AVG(sharpe_ratio) as avg_sharpe,
    AVG(max_drawdown) as avg_drawdown,
    AVG(win_rate) as avg_win_rate,
    SUM(total_trades) as total_trades,
    MIN(date) as first_record,
    MAX(date) as last_record
FROM strategy_performance
GROUP BY strategy_id, DATE(date);

-- 索引
CREATE INDEX idx_daily_summary_strategy ON strategy_daily_summary (strategy_id, summary_date DESC);

-- 自动刷新（定时任务）
CREATE OR REPLACE FUNCTION refresh_strategy_daily_summary()
RETURNS VOID AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY strategy_daily_summary;
END;
$$ LANGUAGE plpgsql;

-- 每小时刷新
-- 配置在cron或Kubernetes CronJob中
```

**4. 数据迁移脚本**

```python
# scripts/migrate_to_partitioned_table.py
async def migrate_to_partitioned_table():
    """Migrate existing data to partitioned table"""

    # Step 1: Rename old table
    await db.execute("ALTER TABLE strategy_performance RENAME TO strategy_performance_old")

    # Step 2: Create new partitioned table
    # (使用上面的DDL)

    # Step 3: Copy data in batches
    batch_size = 10000
    offset = 0

    while True:
        # Read batch
        stmt = select(StrategyPerformanceOld).offset(offset).limit(batch_size)
        batch = await db.execute(stmt)
        rows = batch.scalars().all()

        if not rows:
            break

        # Insert into new table
        for row in rows:
            new_row = StrategyPerformance(**row.__dict__)
            db.add(new_row)

        await db.commit()
        offset += batch_size
        print(f"Migrated {offset} records...")

    # Step 4: Verify data integrity
    old_count = await db.scalar(select(func.count()).select_from(StrategyPerformanceOld))
    new_count = await db.scalar(select(func.count()).select_from(StrategyPerformance))

    assert old_count == new_count, f"Data mismatch: {old_count} vs {new_count}"

    # Step 5: Drop old table (after confirmation)
    # await db.execute("DROP TABLE strategy_performance_old")

    print(f"✅ Migration complete: {new_count} records")
```

#### 交付物

- [ ] 分区表DDL和迁移脚本
- [ ] 自动归档系统（Python脚本 + Cron）
- [ ] 聚合视图和索引
- [ ] 数据校验工具
- [ ] 查询性能提升报告
- [ ] 运维手册（备份、恢复、维护）

#### 验收标准

```yaml
Data Integrity:
  - 数据零丢失
  - 归档前后数据一致
  - 校验脚本全部通过

Performance:
  - 查询性能提升 >50%
  - 最近30天数据查询 <2秒
  - 聚合视图查询 <1秒

Automation:
  - 分区自动创建
  - 归档脚本定时运行
  - 视图自动刷新

Operations:
  - 完整的备份方案
  - 回滚机制测试通过
  - 监控指标正常
```

---

### Phase 4: WebSocket连接池 (Week 10-12)

#### 目标
统一WebSocket连接管理，提升稳定性和可扩展性。

#### 技术方案

**1. ConnectionPool设计**

```python
from typing import Dict, List, Set
from fastapi import WebSocket, WebSocketDisconnect
import asyncio
import time
from collections import defaultdict
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class ConnectionInfo:
    """WebSocket connection metadata"""
    websocket: WebSocket
    user_id: int
    connected_at: float
    last_heartbeat: float
    subscriptions: Set[str]
    message_count: int = 0

class WebSocketConnectionPool:
    """Unified WebSocket connection pool"""

    def __init__(
        self,
        max_connections_per_user: int = 5,
        max_total_connections: int = 1000,
        heartbeat_interval: int = 30,
        idle_timeout: int = 300
    ):
        self.max_connections_per_user = max_connections_per_user
        self.max_total_connections = max_total_connections
        self.heartbeat_interval = heartbeat_interval
        self.idle_timeout = idle_timeout

        # Connection storage
        self.connections: Dict[str, ConnectionInfo] = {}  # connection_id -> info
        self.user_connections: Dict[int, List[str]] = defaultdict(list)  # user_id -> [connection_ids]

        # Subscription management
        self.subscriptions: Dict[str, Set[str]] = defaultdict(set)  # topic -> {connection_ids}

        # Background tasks
        self._health_check_task = None
        self._cleanup_task = None

    async def start(self):
        """Start background tasks"""
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("WebSocket pool started")

    async def stop(self):
        """Stop background tasks and close all connections"""
        if self._health_check_task:
            self._health_check_task.cancel()
        if self._cleanup_task:
            self._cleanup_task.cancel()

        # Close all connections
        for conn_id in list(self.connections.keys()):
            await self.remove_connection(conn_id, reason="Server shutdown")

        logger.info("WebSocket pool stopped")

    async def add_connection(
        self,
        connection_id: str,
        websocket: WebSocket,
        user_id: int
    ) -> bool:
        """Add a new connection"""

        # Check total connections limit
        if len(self.connections) >= self.max_total_connections:
            logger.warning(f"Total connection limit reached: {self.max_total_connections}")
            return False

        # Check per-user limit
        if len(self.user_connections[user_id]) >= self.max_connections_per_user:
            logger.warning(f"User {user_id} connection limit reached: {self.max_connections_per_user}")
            return False

        # Create connection info
        conn_info = ConnectionInfo(
            websocket=websocket,
            user_id=user_id,
            connected_at=time.time(),
            last_heartbeat=time.time(),
            subscriptions=set()
        )

        # Store connection
        self.connections[connection_id] = conn_info
        self.user_connections[user_id].append(connection_id)

        logger.info(f"Connection added: {connection_id} (user: {user_id})")
        self._update_metrics()

        return True

    async def remove_connection(self, connection_id: str, reason: str = ""):
        """Remove a connection"""
        if connection_id not in self.connections:
            return

        conn_info = self.connections[connection_id]

        # Unsubscribe from all topics
        for topic in conn_info.subscriptions:
            self.subscriptions[topic].discard(connection_id)

        # Remove from user connections
        self.user_connections[conn_info.user_id].remove(connection_id)

        # Close WebSocket
        try:
            await conn_info.websocket.close()
        except Exception as e:
            logger.error(f"Error closing WebSocket: {e}")

        # Remove connection info
        del self.connections[connection_id]

        logger.info(f"Connection removed: {connection_id} (reason: {reason})")
        self._update_metrics()

    async def subscribe(self, connection_id: str, topic: str):
        """Subscribe connection to topic"""
        if connection_id not in self.connections:
            return False

        self.connections[connection_id].subscriptions.add(topic)
        self.subscriptions[topic].add(connection_id)

        logger.debug(f"Connection {connection_id} subscribed to {topic}")
        return True

    async def unsubscribe(self, connection_id: str, topic: str):
        """Unsubscribe connection from topic"""
        if connection_id not in self.connections:
            return False

        self.connections[connection_id].subscriptions.discard(topic)
        self.subscriptions[topic].discard(connection_id)

        logger.debug(f"Connection {connection_id} unsubscribed from {topic}")
        return True

    async def broadcast(self, topic: str, message: dict):
        """Broadcast message to all subscribers"""
        if topic not in self.subscriptions:
            return 0

        sent_count = 0
        failed_connections = []

        for connection_id in self.subscriptions[topic]:
            if connection_id not in self.connections:
                continue

            try:
                await self.connections[connection_id].websocket.send_json(message)
                self.connections[connection_id].message_count += 1
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to send to {connection_id}: {e}")
                failed_connections.append(connection_id)

        # Clean up failed connections
        for conn_id in failed_connections:
            await self.remove_connection(conn_id, reason="Send failed")

        return sent_count

    async def send_to_user(self, user_id: int, message: dict):
        """Send message to all connections of a user"""
        if user_id not in self.user_connections:
            return 0

        sent_count = 0
        for connection_id in self.user_connections[user_id]:
            if connection_id not in self.connections:
                continue

            try:
                await self.connections[connection_id].websocket.send_json(message)
                self.connections[connection_id].message_count += 1
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to send to user {user_id}: {e}")

        return sent_count

    async def send_to_connection(self, connection_id: str, message: dict):
        """Send message to specific connection"""
        if connection_id not in self.connections:
            return False

        try:
            await self.connections[connection_id].websocket.send_json(message)
            self.connections[connection_id].message_count += 1
            return True
        except Exception as e:
            logger.error(f"Failed to send to {connection_id}: {e}")
            await self.remove_connection(connection_id, reason="Send failed")
            return False

    async def heartbeat(self, connection_id: str):
        """Update connection heartbeat"""
        if connection_id in self.connections:
            self.connections[connection_id].last_heartbeat = time.time()

    async def _health_check_loop(self):
        """Background task: health check"""
        while True:
            try:
                await asyncio.sleep(self.heartbeat_interval)

                current_time = time.time()
                idle_connections = []

                for conn_id, conn_info in self.connections.items():
                    # Check idle timeout
                    idle_time = current_time - conn_info.last_heartbeat
                    if idle_time > self.idle_timeout:
                        idle_connections.append(conn_id)
                    # Send heartbeat
                    else:
                        try:
                            await conn_info.websocket.send_json({"type": "heartbeat"})
                        except Exception:
                            idle_connections.append(conn_id)

                # Remove idle connections
                for conn_id in idle_connections:
                    await self.remove_connection(conn_id, reason="Idle timeout")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")

    async def _cleanup_loop(self):
        """Background task: cleanup orphaned subscriptions"""
        while True:
            try:
                await asyncio.sleep(300)  # Every 5 minutes

                # Clean up empty subscription topics
                empty_topics = [
                    topic for topic, conn_ids in self.subscriptions.items()
                    if not conn_ids
                ]
                for topic in empty_topics:
                    del self.subscriptions[topic]

                logger.debug(f"Cleaned up {len(empty_topics)} empty subscription topics")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup error: {e}")

    def _update_metrics(self):
        """Update Prometheus metrics"""
        from prometheus_client import Gauge

        # Update connection count metrics
        websocket_connections_gauge.set(len(self.connections))

        # Update per-user metrics
        for user_id, conn_ids in self.user_connections.items():
            websocket_user_connections_gauge.labels(user_id=user_id).set(len(conn_ids))

    def get_stats(self) -> dict:
        """Get connection pool statistics"""
        return {
            "total_connections": len(self.connections),
            "total_users": len(self.user_connections),
            "total_subscriptions": len(self.subscriptions),
            "max_connections_per_user": self.max_connections_per_user,
            "max_total_connections": self.max_total_connections,
            "utilization": len(self.connections) / self.max_total_connections * 100
        }

# Global instance
connection_pool = WebSocketConnectionPool(
    max_connections_per_user=5,
    max_total_connections=1000,
    heartbeat_interval=30,
    idle_timeout=300
)
```

**2. FastAPI集成**

```python
# src/api/strategies/websocket.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from api.dependencies import get_current_user
import uuid

router = APIRouter()

@router.websocket("/ws/strategies")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
):
    """WebSocket endpoint for strategy updates"""

    # Authenticate
    try:
        user = await authenticate_websocket(token)
    except Exception as e:
        await websocket.close(code=1008, reason="Authentication failed")
        return

    # Accept connection
    await websocket.accept()

    # Generate connection ID
    connection_id = f"ws_{user.id}_{uuid.uuid4().hex[:8]}"

    # Add to pool
    success = await connection_pool.add_connection(
        connection_id=connection_id,
        websocket=websocket,
        user_id=user.id
    )

    if not success:
        await websocket.close(code=1008, reason="Connection limit reached")
        return

    try:
        # Send welcome message
        await websocket.send_json({
            "type": "welcome",
            "connection_id": connection_id,
            "user_id": user.id
        })

        # Handle messages
        async for message in websocket.iter_json():
            await handle_websocket_message(connection_id, message)

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {connection_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await connection_pool.remove_connection(connection_id)

async def handle_websocket_message(connection_id: str, message: dict):
    """Handle incoming WebSocket message"""
    msg_type = message.get("type")

    if msg_type == "subscribe":
        topic = message.get("topic")
        await connection_pool.subscribe(connection_id, topic)
        await connection_pool.send_to_connection(connection_id, {
            "type": "subscribed",
            "topic": topic
        })

    elif msg_type == "unsubscribe":
        topic = message.get("topic")
        await connection_pool.unsubscribe(connection_id, topic)
        await connection_pool.send_to_connection(connection_id, {
            "type": "unsubscribed",
            "topic": topic
        })

    elif msg_type == "heartbeat":
        await connection_pool.heartbeat(connection_id)
        await connection_pool.send_to_connection(connection_id, {
            "type": "heartbeat_ack"
        })

    else:
        logger.warning(f"Unknown message type: {msg_type}")
```

**3. 监控指标**

```python
from prometheus_client import Gauge, Counter, Histogram

# Connection metrics
websocket_connections_gauge = Gauge(
    'websocket_connections_active',
    'Number of active WebSocket connections'
)

websocket_user_connections_gauge = Gauge(
    'websocket_user_connections',
    'Number of connections per user',
    ['user_id']
)

websocket_messages_total = Counter(
    'websocket_messages_total',
    'Total WebSocket messages',
    ['direction', 'type']
)

websocket_message_duration = Histogram(
    'websocket_message_duration_seconds',
    'WebSocket message processing duration'
)

websocket_connection_duration = Histogram(
    'websocket_connection_duration_seconds',
    'WebSocket connection duration'
)
```

#### 交付物

- [ ] WebSocketConnectionPool实现
- [ ] FastAPI WebSocket集成
- [ ] 压力测试报告（1000+连接）
- [ ] 稳定性测试报告（24小时）
- [ ] Prometheus监控仪表板
- [ ] WebSocket最佳实践文档

#### 验收标准

```yaml
Functionality:
  - 连接限制生效（5/用户，1000总计）
  - 订阅/取消订阅正常
  - 广播和单播正常
  - 心跳机制正常

Performance:
  - 消息延迟 <100ms (P95)
  - 支持1000+并发连接
  - 内存使用 <500MB（1000连接）

Reliability:
  - 连接稳定性 >99.9%
  - 自动清理空闲连接
  - 异常连接自动移除
  - 断线重连成功率 >95%

Monitoring:
  - 所有指标正常导出
  - Grafana仪表板正常
  - 告警规则配置完成
```

## 🧪 Testing Strategy

### 测试金字塔

```
        /\
       /E2E\          10% - 端到端测试
      /------\        - 关键用户流程
     /Integ.  \       20% - 集成测试
    /----------\      - API端点、数据库、缓存
   /   Unit     \     70% - 单元测试
  /--------------\    - 业务逻辑、工具函数
```

### 单元测试

```python
# tests/test_cache_manager.py
import pytest
from services.cache_manager import CacheManager

@pytest.fixture
async def cache_manager():
    """Test fixture for cache manager"""
    cm = CacheManager(redis_url=None)  # 只使用内存缓存
    yield cm
    # Cleanup
    cm.memory_cache.clear()

@pytest.mark.asyncio
async def test_cache_set_and_get(cache_manager):
    """Test basic cache set and get"""
    await cache_manager.set("test:key1", "value1")
    value = await cache_manager.get("test:key1")
    assert value == "value1"

@pytest.mark.asyncio
async def test_cache_expiration(cache_manager):
    """Test cache TTL expiration"""
    await cache_manager.set("test:key2", "value2", ttl=1)
    await asyncio.sleep(2)
    value = await cache_manager.get("test:key2")
    assert value is None

@pytest.mark.asyncio
async def test_cache_pattern_clear(cache_manager):
    """Test clearing cache by pattern"""
    await cache_manager.set("test:key1", "value1")
    await cache_manager.set("test:key2", "value2")
    await cache_manager.set("other:key3", "value3")

    await cache_manager.clear_pattern("test:*")

    assert await cache_manager.get("test:key1") is None
    assert await cache_manager.get("test:key2") is None
    assert await cache_manager.get("other:key3") == "value3"
```

### 集成测试

```python
# tests/test_api_integration.py
from httpx import AsyncClient
from main import app

@pytest.mark.asyncio
async def test_create_strategy_with_cache():
    """Test strategy creation with cache integration"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create strategy
        response = await client.post("/api/strategies", json={
            "name": "Test Strategy",
            "code": "test_001",
            "strategy_type": "technical",
            "default_parameters": {"param1": 10}
        })

        assert response.status_code == 201
        strategy_id = response.json()["id"]

        # Get strategy (should hit cache on second call)
        response1 = await client.get(f"/api/strategies/{strategy_id}")
        response2 = await client.get(f"/api/strategies/{strategy_id}")

        assert response1.json() == response2.json()
        # Verify cache hit in metrics
```

### E2E测试

```python
# tests/test_e2e_websocket.py
from playwright.async_api import async_playwright

@pytest.mark.asyncio
async def test_websocket_real_time_updates():
    """Test real-time updates via WebSocket"""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # Navigate to dashboard
        await page.goto("http://localhost:3000/dashboard")

        # Login
        await page.fill("#username", "testuser")
        await page.fill("#password", "testpass")
        await page.click("#login-btn")

        # Wait for WebSocket connection
        await page.wait_for_selector(".ws-connected")

        # Trigger strategy update (via API)
        async with AsyncClient(base_url="http://localhost:3004") as client:
            await client.post("/api/strategies/stg_001/execute")

        # Verify dashboard updates
        await page.wait_for_selector(".strategy-updated", timeout=5000)

        await browser.close()
```

### 性能测试

```python
# tests/test_performance.py
from locust import HttpUser, task, between

class StrategyAPIUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def list_strategies(self):
        """List strategies (most common operation)"""
        self.client.get("/api/strategies")

    @task(2)
    def get_strategy(self):
        """Get specific strategy"""
        self.client.get(f"/api/strategies/stg_{random.randint(1, 100)}")

    @task(1)
    def create_strategy(self):
        """Create new strategy"""
        self.client.post("/api/strategies", json={
            "name": f"Strategy {uuid.uuid4().hex[:8]}",
            "code": uuid.uuid4().hex[:12],
            "strategy_type": "technical"
        })

# Run: locust -f tests/test_performance.py --host=http://localhost:3004
```

### 测试覆盖率目标

```yaml
Overall: >80%

By Module:
  cache_manager.py: >90%
  strategies/base.py: >85%
  strategies/execution.py: >80%
  connection_pool.py: >85%

Critical Paths:
  - Strategy CRUD: 100%
  - Cache operations: 100%
  - WebSocket handling: >90%
  - Data migration: 100%
```

## 📊 Monitoring & Metrics

### Prometheus指标

```yaml
# API性能
api_request_duration_seconds{endpoint, method, status}
api_requests_total{endpoint, method, status}
api_errors_total{endpoint, error_type}

# 缓存性能
cache_hits_total{level, key_prefix}
cache_misses_total{key_prefix}
cache_hit_rate{level}
cache_memory_bytes{level}
cache_operation_duration_seconds{operation, level}

# WebSocket
websocket_connections_active
websocket_user_connections{user_id}
websocket_messages_total{direction, type}
websocket_message_duration_seconds
websocket_connection_duration_seconds

# 数据库
db_query_duration_seconds{query_type, table}
db_connection_pool_size{status}
db_slow_queries_total

# 业务指标
strategy_count{status}
strategy_execution_total{strategy_type}
strategy_performance_records_total
```

### Grafana仪表板

**1. 系统概览**
- 总请求数、错误率、响应时间
- 缓存命中率、内存使用
- WebSocket连接数
- 数据库性能

**2. Phase-specific仪表板**
- Phase 1: API重组前后对比
- Phase 2: 缓存性能分析
- Phase 3: 数据库查询性能
- Phase 4: WebSocket连接监控

### 告警规则

```yaml
# Critical (P0)
- alert: APIErrorRateHigh
  expr: rate(api_errors_total[5m]) > 0.05
  severity: critical

- alert: CacheHitRateLow
  expr: cache_hit_rate < 0.5
  severity: critical

- alert: WebSocketConnectionsExhausted
  expr: websocket_connections_active > 950
  severity: critical

# Warning (P1)
- alert: SlowQueries
  expr: db_query_duration_seconds{quantile="0.95"} > 1
  severity: warning

- alert: MemoryUsageHigh
  expr: cache_memory_bytes{level="L1"} > 1073741824
  severity: warning
```

## 🚀 Deployment Strategy

### 灰度发布流程

```yaml
Phase 1-4 通用流程:

Step 1: 内部测试环境 (1天)
  - 部署到测试环境
  - 内部团队验证
  - 性能基准测试
  - 回归测试

Step 2: 金丝雀发布 (2天)
  - 5%生产流量
  - 监控关键指标24小时
  - 无异常继续

Step 3: 灰度扩大 (3天)
  - 25% → 50% → 100%
  - 每阶段观察24小时
  - 任何问题立即回滚

Step 4: 全量上线 (1天)
  - 100%流量切换
  - 持续监控48小时
  - 清理旧代码
```

### Feature Flags

```python
# 使用环境变量控制特性
USE_NEW_STRATEGY_API = os.getenv("USE_NEW_STRATEGY_API", "false") == "true"
USE_CACHE_MANAGER = os.getenv("USE_CACHE_MANAGER", "false") == "true"
USE_PARTITIONED_TABLE = os.getenv("USE_PARTITIONED_TABLE", "false") == "true"
USE_CONNECTION_POOL = os.getenv("USE_CONNECTION_POOL", "false") == "true"

# 或使用配置管理工具（推荐）
from config import feature_flags

if feature_flags.is_enabled("cache_manager"):
    cache = cache_manager
else:
    cache = legacy_cache
```

### 回滚方案

```bash
# 快速回滚 (<5分钟)
# 方法1: Feature Flag
curl -X POST http://localhost:8000/api/admin/feature-flags \
  -d '{"use_new_strategy_api": false}'

# 方法2: 容器回滚
kubectl rollout undo deployment/strategy-api

# 方法3: 负载均衡切换
# 切换流量到旧版本实例
```

## 📝 Documentation Requirements

### 开发文档

- [ ] 架构设计文档（ADR - Architecture Decision Records）
- [ ] API文档（OpenAPI/Swagger）
- [ ] 数据库设计文档（ER图、分区策略）
- [ ] 缓存策略文档
- [ ] WebSocket协议文档
- [ ] 代码注释（docstrings）

### 运维文档

- [ ] 部署指南
- [ ] 监控指南（指标说明、仪表板使用）
- [ ] 故障处理手册
- [ ] 数据备份和恢复
- [ ] 性能调优指南
- [ ] 常见问题FAQ

### 用户文档

- [ ] API迁移指南（给前端团队）
- [ ] WebSocket使用指南
- [ ] 最佳实践文档
- [ ] Changelog（版本变更记录）

## ✅ Acceptance Criteria

### Phase 1完成标准

```yaml
Code Quality:
  - ✅ 代码重复率 <15%
  - ✅ 测试覆盖率 >80%
  - ✅ Pylint评分 >8.5/10
  - ✅ 所有API文档更新

Performance:
  - ✅ API响应时间不倒退
  - ✅ P95响应时间 ≤ 200ms

Compatibility:
  - ✅ 所有现有API正常工作
  - ✅ 前端无需修改
  - ✅ 回归测试全部通过
```

### Phase 2完成标准

```yaml
Performance:
  - ✅ 缓存命中率 >75%
  - ✅ 内存使用 <1GB且稳定
  - ✅ 缓存操作延迟 <5ms

Reliability:
  - ✅ 无缓存不一致问题
  - ✅ Redis故障自动降级
  - ✅ 运行48小时无异常

Monitoring:
  - ✅ 所有指标正常导出
  - ✅ Grafana仪表板正常
  - ✅ 告警触发测试通过
```

### Phase 3完成标准

```yaml
Data Integrity:
  - ✅ 数据零丢失
  - ✅ 迁移前后数据一致
  - ✅ 校验脚本全部通过

Performance:
  - ✅ 查询性能提升 >50%
  - ✅ 30天数据查询 <2秒
  - ✅ 聚合视图查询 <1秒

Automation:
  - ✅ 分区自动创建
  - ✅ 归档脚本定时运行
  - ✅ 视图自动刷新
```

### Phase 4完成标准

```yaml
Functionality:
  - ✅ 连接限制生效
  - ✅ 订阅系统正常
  - ✅ 广播功能正常

Performance:
  - ✅ 消息延迟 <100ms (P95)
  - ✅ 支持1000+并发连接
  - ✅ 内存使用 <500MB

Reliability:
  - ✅ 连接稳定性 >99.9%
  - ✅ 24小时压力测试通过
  - ✅ 断线重连成功率 >95%
```

### 整体完成标准

```yaml
Code Quality:
  - ✅ 代码重复率 <10%
  - ✅ 测试覆盖率 >80%
  - ✅ SonarQube评级 A+
  - ✅ 技术债务显著降低

Performance:
  - ✅ API响应时间 <150ms (P95)
  - ✅ 数据库查询 减少50%
  - ✅ 缓存命中率 >80%
  - ✅ WebSocket延迟 <100ms

Stability:
  - ✅ 系统可用性 >99.9%
  - ✅ 生产事故 0次
  - ✅ 回滚次数 0次
  - ✅ 数据零丢失

Documentation:
  - ✅ 所有文档完整更新
  - ✅ API文档100%覆盖
  - ✅ 运维手册完整
  - ✅ 新人可自主上手
```

## 🎯 Success Metrics

### 开发效率指标

| 指标 | 基线 | 目标 | 测量方式 |
|-----|------|------|---------|
| 开发速度 | 1x | 1.5x | Sprint速度 |
| Bug修复时间 | 2天 | <1天 | JIRA统计 |
| 代码审查时间 | 2小时 | <1小时 | GitHub PR |
| 新人上手时间 | 2周 | 1周 | 培训反馈 |

### 系统性能指标

| 指标 | 基线 | 目标 | 实际 |
|-----|------|------|------|
| API响应时间(P95) | 200ms | <150ms | - |
| 缓存命中率 | N/A | >80% | - |
| 数据库查询时间 | 500ms | <250ms | - |
| WebSocket延迟 | 150ms | <100ms | - |

### 业务影响指标

| 指标 | 基线 | 目标 | 实际 |
|-----|------|------|------|
| 生产事故率 | 2次/月 | <1次/月 | - |
| 用户满意度 | 85% | >90% | - |
| 系统可用性 | 99.5% | >99.9% | - |
| 支持的用户数 | 100 | 1000+ | - |

## 🔗 Dependencies

### 外部依赖

1. **Redis服务** (Phase 2)
   - 版本: Redis 7+
   - 责任方: 运维团队
   - 时间要求: Week 4前部署
   - 备选方案: 纯内存缓存

2. **PostgreSQL权限** (Phase 3)
   - 权限: 创建分区表
   - 责任方: DBA团队
   - 时间要求: Week 7前授权

3. **监控基础设施** (All Phases)
   - Prometheus + Grafana
   - 责任方: 运维团队
   - 状态: 已就绪

### 内部依赖

1. **认证系统稳定**
   - 当前状态: 稳定
   - 风险: 低

2. **测试环境完整**
   - 需要: 数据库、Redis、完整数据
   - 状态: 待准备
   - 时间: Week 1前就绪

3. **前端团队协作**
   - 需求: API变更通知
   - 频率: 每Phase结束前
   - 沟通: API文档 + Review会议

## ⚠️ Risks & Mitigation

### 高风险（High）

**R1: 数据迁移失败**
- 影响: 数据丢失，系统不可用
- 概率: 中（20%）
- 缓解:
  - 完整备份
  - 分批迁移
  - 双写验证
  - 回滚方案

**R2: 性能倒退**
- 影响: 用户体验下降
- 概率: 中（15%）
- 缓解:
  - 性能基准测试
  - A/B测试
  - 灰度发布
  - 性能监控

### 中风险（Medium）

**R3: API不兼容**
- 影响: 前端功能异常
- 概率: 中（25%）
- 缓解:
  - 契约测试
  - 版本化API
  - 前后端联调
  - 灰度发布

**R4: 缓存策略不当**
- 影响: 数据不一致
- 概率: 低（10%）
- 缓解:
  - 动态TTL调整
  - 缓存预热
  - 熔断器
  - 版本控制

### 低风险（Low）

**R5: 测试覆盖不足**
- 影响: 生产bug
- 概率: 低（5%）
- 缓解:
  - Code review
  - 覆盖率目标
  - QA团队测试

## 📅 Timeline

```
Week 1-3:   Phase 1 - API端点整合
Week 4-6:   Phase 2 - 缓存策略统一
Week 7-9:   Phase 3 - 性能数据归档
Week 10-12: Phase 4 - WebSocket连接池

Total: 8-12 weeks
```

### 关键里程碑

- ✅ Week 3:  Phase 1完成，代码重复率<15%
- ✅ Week 6:  Phase 2完成，缓存命中率>75%
- ✅ Week 9:  Phase 3完成，查询性能+50%
- ✅ Week 12: Phase 4完成，连接管理稳定

## Tasks Created
- [ ] #20 - API模块结构设计与分析 (parallel: true)
- [ ] #21 - API模块重构实施 (parallel: true)
- [ ] #22 - API测试与灰度发布 (parallel: false)
- [ ] #23 - CacheManager核心实现 (parallel: true)
- [ ] #24 - 缓存集成与监控 (parallel: false)
- [ ] #25 - 数据库分区与归档系统 (parallel: true)
- [ ] #26 - WebSocket连接池实现 (parallel: true)
- [ ] #27 - WebSocket压力测试与监控 (parallel: false)

Total tasks: 8
Parallel tasks: 5
Sequential tasks: 3
Estimated total effort: 280 hours (35 days)

## Phase到任务映射

### Phase 1: API端点整合 (Week 1-3)
- Task #20: API模块结构设计与分析
- Task #21: API模块重构实施
- Task #22: API测试与灰度发布

### Phase 2: 缓存策略统一 (Week 4-6)
- Task #23: CacheManager核心实现
- Task #24: 缓存集成与监控

### Phase 3: 性能数据归档 (Week 7-9)
- Task #25: 数据库分区与归档系统

### Phase 4: WebSocket连接池 (Week 10-12)
- Task #26: WebSocket连接池实现
- Task #27: WebSocket压力测试与监控

## 🔄 Next Steps

1. **团队Review** - 评审本Epic和任务分解
2. **资源分配** - 确认开发人员和时间
3. **环境准备** - 准备测试环境和依赖
4. **启动Task 001** - 开始API模块结构设计与分析

---

**Epic状态**: 待启动
**优先级**: 高
**预估工作量**: 8-12周
**风险等级**: 中（可控）

**下一步**: 执行 `/pm:epic-decompose strategy-architecture-refactoring` 拆分为具体任务
