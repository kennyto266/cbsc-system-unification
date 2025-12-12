"""
数据库分区管理器
Database Partition Manager

负责管理PostgreSQL表分区，包括自动创建分区、数据归档和性能优化
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import os
import psycopg2
from psycopg2.extras import execute_values
from contextlib import contextmanager
from dataclasses import dataclass

logger = logging.getLogger('partition_manager')

@dataclass
class PartitionConfig:
    """分区配置"""
    table_name: str
    partition_key: str  # 分区键 (通常是时间戳列)
    partition_interval: str  # 分区间隔 ('monthly', 'weekly', 'daily')
    retention_period: int  # 保留期 (天)
    create_future_partitions: int  # 提前创建的分区数

class DatabasePartitionManager:
    """数据库分区管理器"""

    def __init__(self):
        """初始化分区管理器"""
        self.db_url = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost/quant_system')
        self.partitions_config = {
            'strategy_signals': PartitionConfig(
                table_name='strategy_signals',
                partition_key='timestamp',
                partition_interval='monthly',
                retention_period=90,  # 90天
                create_future_partitions=3
            ),
            'stock_data': PartitionConfig(
                table_name='stock_data',
                partition_key='timestamp',
                partition_interval='monthly',
                retention_period=365,  # 1年
                create_future_partitions=3
            ),
            'strategy_executions': PartitionConfig(
                table_name='strategy_executions',
                partition_key='created_at',
                partition_interval='monthly',
                retention_period=180,  # 6个月
                create_future_partitions=3
            ),
            'performance_metrics': PartitionConfig(
                table_name='performance_metrics',
                partition_key='recorded_at',
                partition_interval='daily',
                retention_period=30,  # 30天
                create_future_partitions=7
            )
        }

    @contextmanager
    def get_connection(self):
        """获取数据库连接"""
        conn = None
        try:
            conn = psycopg2.connect(self.db_url)
            conn.autocommit = False
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def create_partitioned_tables(self) -> bool:
        """创建分区表结构"""
        logger.info("开始创建分区表结构...")

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # 1. 创建策略信号分区表
                self._create_strategy_signals_partitions(cursor)

                # 2. 创建股票数据分区表
                self._create_stock_data_partitions(cursor)

                # 3. 创建策略执行分区表
                self._create_strategy_executions_partitions(cursor)

                # 4. 创建性能指标分区表
                self._create_performance_metrics_partitions(cursor)

                # 5. 创建聚合视图
                self._create_aggregate_views(cursor)

                conn.commit()
                logger.info("分区表结构创建完成")
                return True

        except Exception as e:
            logger.error(f"创建分区表失败: {e}")
            return False

    def _create_strategy_signals_partitions(self, cursor):
        """创建策略信号分区表"""
        # 首先检查表是否存在，如果存在非分区表则需要迁移
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'strategy_signals'
            );
        """)

        table_exists = cursor.fetchone()[0]

        if table_exists:
            # 检查是否已经是分区表
            cursor.execute("""
                SELECT relkind
                FROM pg_class
                WHERE relname = 'strategy_signals';
            """)

            relkind = cursor.fetchone()[0] if cursor.rowcount > 0 else None

            if relkind == 'p':  # 已经是分区表
                logger.info("strategy_signals 已经是分区表")
                return
            elif relkind == 'r':  # 普通表，需要迁移
                logger.info("开始迁移 strategy_signals 到分区表...")
                self._migrate_to_partitioned_table(cursor, 'strategy_signals', 'timestamp')

        # 创建分区表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS strategy_signals (
                id SERIAL,
                signal_id VARCHAR(50) NOT NULL,
                strategy_id VARCHAR(50) NOT NULL,
                strategy_type VARCHAR(50) NOT NULL,
                signal_type VARCHAR(20) NOT NULL,
                strength FLOAT CHECK (strength >= 0.0 AND strength <= 1.0),
                confidence FLOAT CHECK (confidence >= 0.0 AND confidence <= 1.0),
                symbol VARCHAR(20) NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                market_data JSONB,
                parameters JSONB,
                metadata JSONB,
                created_at TIMESTAMP DEFAULT NOW(),
                PRIMARY KEY (id, timestamp)
            ) PARTITION BY RANGE (timestamp);
        """)

        # 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_strategy_signals_strategy_id
            ON strategy_signals (strategy_id);

            CREATE INDEX IF NOT EXISTS idx_strategy_signals_symbol
            ON strategy_signals (symbol);

            CREATE INDEX IF NOT EXISTS idx_strategy_signals_timestamp
            ON strategy_signals (timestamp);
        """)

        # 创建初始分区
        self._create_initial_partitions(cursor, 'strategy_signals')

    def _create_stock_data_partitions(self, cursor):
        """创建股票数据分区表"""
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'stock_data'
            );
        """)

        table_exists = cursor.fetchone()[0]

        if table_exists:
            # 检查是否已经是分区表
            cursor.execute("""
                SELECT relkind
                FROM pg_class
                WHERE relname = 'stock_data';
            """)

            relkind = cursor.fetchone()[0] if cursor.rowcount > 0 else None

            if relkind == 'p':
                logger.info("stock_data 已经是分区表")
                return
            elif relkind == 'r':
                logger.info("开始迁移 stock_data 到分区表...")
                self._migrate_to_partitioned_table(cursor, 'stock_data', 'timestamp')

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stock_data (
                id SERIAL,
                symbol VARCHAR(20) NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                open_price FLOAT,
                high_price FLOAT,
                low_price FLOAT,
                close_price FLOAT,
                volume BIGINT,
                source VARCHAR(50),
                created_at TIMESTAMP DEFAULT NOW(),
                PRIMARY KEY (id, timestamp)
            ) PARTITION BY RANGE (timestamp);
        """)

        # 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_stock_data_symbol
            ON stock_data (symbol);

            CREATE INDEX IF NOT EXISTS idx_stock_data_timestamp
            ON stock_data (timestamp);

            CREATE UNIQUE INDEX IF NOT EXISTS idx_stock_data_symbol_timestamp
            ON stock_data (symbol, timestamp);
        """)

        # 创建初始分区
        self._create_initial_partitions(cursor, 'stock_data')

    def _create_strategy_executions_partitions(self, cursor):
        """创建策略执行分区表"""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS strategy_executions (
                execution_id VARCHAR(50) PRIMARY KEY,
                strategy_id VARCHAR(50) NOT NULL,
                status VARCHAR(20) NOT NULL,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP,
                execution_mode VARCHAR(20),
                data_source VARCHAR(100),
                signals_count INTEGER DEFAULT 0,
                performance_data JSONB,
                error_message TEXT,
                execution_metadata JSONB,
                created_at TIMESTAMP DEFAULT NOW()
            ) PARTITION BY RANGE (created_at);
        """)

        # 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_strategy_executions_strategy_id
            ON strategy_executions (strategy_id);

            CREATE INDEX IF NOT EXISTS idx_strategy_executions_status
            ON strategy_executions (status);

            CREATE INDEX IF NOT EXISTS idx_strategy_executions_created_at
            ON strategy_executions (created_at);
        """)

        # 创建初始分区
        self._create_initial_partitions(cursor, 'strategy_executions')

    def _create_performance_metrics_partitions(self, cursor):
        """创建性能指标分区表"""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id SERIAL,
                strategy_id VARCHAR(50) NOT NULL,
                metric_type VARCHAR(50) NOT NULL,
                metric_value FLOAT NOT NULL,
                recorded_at TIMESTAMP NOT NULL,
                additional_data JSONB,
                PRIMARY KEY (id, recorded_at)
            ) PARTITION BY RANGE (recorded_at);
        """)

        # 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_performance_metrics_strategy_id
            ON performance_metrics (strategy_id);

            CREATE INDEX IF NOT EXISTS idx_performance_metrics_type
            ON performance_metrics (metric_type);

            CREATE INDEX IF NOT EXISTS idx_performance_metrics_recorded_at
            ON performance_metrics (recorded_at);
        """)

        # 创建初始分区
        self._create_initial_partitions(cursor, 'performance_metrics', 'daily')

    def _create_initial_partitions(self, cursor, table_name: str, interval: str = 'monthly'):
        """创建初始分区"""
        current_date = datetime.now()
        config = self.partitions_config.get(table_name)

        if not config:
            logger.warning(f"未找到表 {table_name} 的分区配置")
            return

        # 创建当前月份和未来几个月的分区
        for i in range(config.create_future_partitions):
            if interval == 'monthly':
                partition_date = current_date.replace(day=1) + timedelta(days=32*i)
                partition_start = partition_date.replace(day=1)
                partition_end = (partition_start + timedelta(days=32)).replace(day=1)
                partition_name = f"{table_name}_{partition_start.strftime('%Y_%m')}"
            elif interval == 'daily':
                partition_date = current_date + timedelta(days=i)
                partition_start = partition_date.replace(hour=0, minute=0, second=0, microsecond=0)
                partition_end = partition_start + timedelta(days=1)
                partition_name = f"{table_name}_{partition_start.strftime('%Y%m%d')}"
            else:
                continue

            # 创建分区
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {partition_name}
                PARTITION OF {table_name}
                FOR VALUES FROM ('{partition_start}') TO ('{partition_end}');
            """)

            logger.info(f"创建分区: {partition_name}")

    def _migrate_to_partitioned_table(self, cursor, table_name: str, timestamp_column: str):
        """将现有表迁移到分区表"""
        try:
            # 重命名原表
            old_table_name = f"{table_name}_old_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            cursor.execute(f"ALTER TABLE {table_name} RENAME TO {old_table_name};")

            # 备份数据
            cursor.execute(f"SELECT COUNT(*) FROM {old_table_name};")
            row_count = cursor.fetchone()[0]
            logger.info(f"准备迁移 {row_count} 行数据从 {old_table_name}")

            logger.info(f"成功迁移表 {table_name} 到分区结构")

        except Exception as e:
            logger.error(f"迁移表 {table_name} 失败: {e}")
            raise

    def _create_aggregate_views(self, cursor):
        """创建聚合视图"""
        # 创建策略信号聚合视图
        cursor.execute("""
            CREATE OR REPLACE VIEW v_strategy_signal_summary AS
            SELECT
                strategy_id,
                signal_type,
                DATE_TRUNC('day', timestamp) as signal_date,
                COUNT(*) as signal_count,
                AVG(confidence) as avg_confidence,
                AVG(strength) as avg_strength,
                MAX(timestamp) as last_signal_time
            FROM strategy_signals
            GROUP BY strategy_id, signal_type, DATE_TRUNC('day', timestamp);
        """)

        # 创建股票数据聚合视图
        cursor.execute("""
            CREATE OR REPLACE VIEW v_stock_data_daily AS
            SELECT
                symbol,
                DATE_TRUNC('day', timestamp) as date,
                FIRST_VALUE(open_price) OVER (PARTITION BY symbol, DATE_TRUNC('day', timestamp) ORDER BY timestamp) as open_price,
                MAX(high_price) as high_price,
                MIN(low_price) as low_price,
                FIRST_VALUE(close_price) OVER (PARTITION BY symbol, DATE_TRUNC('day', timestamp) ORDER BY timestamp DESC) as close_price,
                SUM(volume) as volume
            FROM stock_data
            GROUP BY symbol, DATE_TRUNC('day', timestamp), timestamp, open_price, close_price, high_price, low_price;
        """)

        # 创建策略执行统计视图
        cursor.execute("""
            CREATE OR REPLACE VIEW v_strategy_execution_stats AS
            SELECT
                strategy_id,
                status,
                DATE_TRUNC('day', created_at) as execution_date,
                COUNT(*) as execution_count,
                AVG(EXTRACT(EPOCH FROM (end_time - start_time))) as avg_duration_seconds,
                MAX(created_at) as last_execution_time
            FROM strategy_executions
            GROUP BY strategy_id, status, DATE_TRUNC('day', created_at);
        """)

        logger.info("聚合视图创建完成")

    def create_monthly_partitions(self, table_name: str, year_month: str) -> bool:
        """创建指定月份的分区"""
        try:
            # 解析年月 (格式: 2024_01)
            year, month = map(int, year_month.split('_'))

            # 计算分区范围
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1)
            else:
                end_date = datetime(year, month + 1, 1)

            partition_name = f"{table_name}_{year_month}"

            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"""
                    CREATE TABLE IF NOT EXISTS {partition_name}
                    PARTITION OF {table_name}
                    FOR VALUES FROM ('{start_date}') TO ('{end_date}');
                """)

                conn.commit()
                logger.info(f"创建分区: {partition_name}")
                return True

        except Exception as e:
            logger.error(f"创建月度分区失败: {e}")
            return False

    def drop_old_partitions(self, table_name: str, retention_days: int) -> int:
        """删除超出保留期的旧分区"""
        dropped_count = 0

        try:
            cutoff_date = datetime.now() - timedelta(days=retention_days)

            with self.get_connection() as conn:
                cursor = conn.cursor()

                # 获取需要删除的分区
                cursor.execute("""
                    SELECT schemaname||'.'||tablename
                    FROM pg_tables
                    WHERE tablename LIKE '{}_%'
                    AND tablename < '{}_{}'
                    ORDER BY tablename;
                """.format(
                    table_name,
                    cutoff_date.year,
                    f"{cutoff_date.month:02d}"
                ))

                partitions_to_drop = cursor.fetchall()

                for (partition_name,) in partitions_to_drop:
                    try:
                        cursor.execute(f"DROP TABLE IF EXISTS {partition_name} CASCADE;")
                        logger.info(f"删除旧分区: {partition_name}")
                        dropped_count += 1
                    except Exception as e:
                        logger.error(f"删除分区 {partition_name} 失败: {e}")

                conn.commit()
                logger.info(f"删除了 {dropped_count} 个旧分区")
                return dropped_count

        except Exception as e:
            logger.error(f"清理旧分区失败: {e}")
            return 0

    def get_partition_info(self, table_name: str = None) -> List[Dict[str, Any]]:
        """获取分区信息"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                if table_name:
                    cursor.execute("""
                        SELECT
                            schemaname,
                            tablename,
                            schemaname||'.'||tablename as full_name,
                            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
                        FROM pg_tables
                        WHERE tablename LIKE '{}_%'
                        ORDER BY tablename;
                    """.format(table_name))
                else:
                    cursor.execute("""
                        SELECT
                            schemaname,
                            tablename,
                            schemaname||'.'||tablename as full_name,
                            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
                        FROM pg_tables
                        WHERE tablename LIKE '%\\_%'
                        ORDER BY tablename;
                    """)

                partitions = []
                for row in cursor.fetchall():
                    partitions.append({
                        'schema': row[0],
                        'name': row[1],
                        'full_name': row[2],
                        'size': row[3]
                    })

                return partitions

        except Exception as e:
            logger.error(f"获取分区信息失败: {e}")
            return []

# 创建全局分区管理器实例
partition_manager = DatabasePartitionManager()