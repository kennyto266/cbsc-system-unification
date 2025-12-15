"""
聚合视图管理器
Aggregate View Manager

负责创建和管理数据库聚合视图以提升查询性能
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import psycopg2
from psycopg2.extras import execute_values
from contextlib import contextmanager

logger = logging.getLogger('view_manager')

class AggregateViewManager:
    """聚合视图管理器"""

    def __init__(self, db_url: str):
        """初始化视图管理器"""
        self.db_url = db_url

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

    def create_all_views(self) -> bool:
        """创建所有聚合视图"""
        logger.info("开始创建聚合视图...")

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # 创建策略信号聚合视图
                self._create_strategy_signal_views(cursor)

                # 创建股票数据聚合视图
                self._create_stock_data_views(cursor)

                # 创建策略执行聚合视图
                self._create_strategy_execution_views(cursor)

                # 创建性能指标聚合视图
                self._create_performance_metric_views(cursor)

                # 创建综合分析视图
                self._create_analytical_views(cursor)

                conn.commit()
                logger.info("聚合视图创建完成")
                return True

        except Exception as e:
            logger.error(f"创建聚合视图失败: {e}")
            return False

    def _create_strategy_signal_views(self, cursor):
        """创建策略信号聚合视图"""

        # 按日汇总的策略信号视图
        cursor.execute("""
            CREATE OR REPLACE VIEW v_strategy_signals_daily AS
            SELECT
                strategy_id,
                strategy_type,
                DATE_TRUNC('day', timestamp) as signal_date,
                symbol,
                COUNT(*) as total_signals,
                COUNT(CASE WHEN signal_type = 'BUY' THEN 1 END) as buy_signals,
                COUNT(CASE WHEN signal_type = 'SELL' THEN 1 END) as sell_signals,
                COUNT(CASE WHEN signal_type = 'HOLD' THEN 1 END) as hold_signals,
                AVG(confidence) as avg_confidence,
                AVG(strength) as avg_strength,
                MAX(confidence) as max_confidence,
                MIN(confidence) as min_confidence,
                MAX(timestamp) as last_signal_time
            FROM strategy_signals
            GROUP BY strategy_id, strategy_type, DATE_TRUNC('day', timestamp), symbol
            ORDER BY signal_date DESC, total_signals DESC;
        """)

        # 按周汇总的策略信号视图
        cursor.execute("""
            CREATE OR REPLACE VIEW v_strategy_signals_weekly AS
            SELECT
                strategy_id,
                strategy_type,
                DATE_TRUNC('week', timestamp) as week_start,
                COUNT(*) as total_signals,
                COUNT(CASE WHEN signal_type = 'BUY' THEN 1 END) as buy_signals,
                COUNT(CASE WHEN signal_type = 'SELL' THEN 1 END) as sell_signals,
                COUNT(CASE WHEN signal_type = 'HOLD' THEN 1 END) as hold_signals,
                AVG(confidence) as avg_confidence,
                AVG(strength) as avg_strength,
                MAX(timestamp) as last_signal_time,
                COUNT(DISTINCT symbol) as unique_symbols
            FROM strategy_signals
            GROUP BY strategy_id, strategy_type, DATE_TRUNC('week', timestamp)
            ORDER BY week_start DESC, total_signals DESC;
        """)

        # 按月汇总的策略信号视图
        cursor.execute("""
            CREATE OR REPLACE VIEW v_strategy_signals_monthly AS
            SELECT
                strategy_id,
                strategy_type,
                DATE_TRUNC('month', timestamp) as month_start,
                COUNT(*) as total_signals,
                COUNT(CASE WHEN signal_type = 'BUY' THEN 1 END) as buy_signals,
                COUNT(CASE WHEN signal_type = 'SELL' THEN 1 END) as sell_signals,
                COUNT(CASE WHEN signal_type = 'HOLD' THEN 1 END) as hold_signals,
                AVG(confidence) as avg_confidence,
                AVG(strength) as avg_strength,
                MAX(timestamp) as last_signal_time,
                COUNT(DISTINCT symbol) as unique_symbols
            FROM strategy_signals
            GROUP BY strategy_id, strategy_type, DATE_TRUNC('month', timestamp)
            ORDER BY month_start DESC, total_signals DESC;
        """)

        # 策略信号性能视图
        cursor.execute("""
            CREATE OR REPLACE VIEW v_strategy_signal_performance AS
            SELECT
                ss.strategy_id,
                s.name as strategy_name,
                ss.strategy_type,
                COUNT(*) as total_signals,
                COUNT(CASE WHEN ss.signal_type = 'BUY' THEN 1 END) as buy_signals,
                COUNT(CASE WHEN ss.signal_type = 'SELL' THEN 1 END) as sell_signals,
                AVG(ss.confidence) as avg_confidence,
                AVG(ss.strength) as avg_strength,
                MAX(ss.timestamp) as last_signal_time,
                COUNT(DISTINCT ss.symbol) as coverage_symbols,
                -- 计算信号质量分数
                (AVG(ss.confidence) * 0.6 + AVG(ss.strength) * 0.4) as quality_score
            FROM strategy_signals ss
            LEFT JOIN strategies s ON ss.strategy_id = s.id
            GROUP BY ss.strategy_id, s.name, ss.strategy_type
            HAVING COUNT(*) > 0
            ORDER BY quality_score DESC, total_signals DESC;
        """)

        logger.info("策略信号聚合视图创建完成")

    def _create_stock_data_views(self, cursor):
        """创建股票数据聚合视图"""

        # 日线数据视图
        cursor.execute("""
            CREATE OR REPLACE VIEW v_stock_data_daily AS
            SELECT
                symbol,
                DATE_TRUNC('day', timestamp) as date,
                FIRST_VALUE(open_price) OVER (PARTITION BY symbol, DATE_TRUNC('day', timestamp) ORDER BY timestamp) as open_price,
                MAX(high_price) as high_price,
                MIN(low_price) as low_price,
                FIRST_VALUE(close_price) OVER (PARTITION BY symbol, DATE_TRUNC('day', timestamp) ORDER BY timestamp DESC) as close_price,
                SUM(volume) as volume,
                COUNT(*) as data_points,
                MAX(timestamp) as last_update
            FROM stock_data
            GROUP BY symbol, DATE_TRUNC('day', timestamp), timestamp, open_price, close_price, high_price, low_price
            ORDER BY symbol, date DESC;
        """)

        # 周线数据视图
        cursor.execute("""
            CREATE OR REPLACE VIEW v_stock_data_weekly AS
            SELECT
                symbol,
                DATE_TRUNC('week', timestamp) as week_start,
                MIN(open_price) as open_price,
                MAX(high_price) as high_price,
                MIN(low_price) as low_price,
                MAX(close_price) as close_price,
                SUM(volume) as volume,
                COUNT(*) as data_points
            FROM stock_data
            GROUP BY symbol, DATE_TRUNC('week', timestamp)
            ORDER BY symbol, week_start DESC;
        """)

        # 月线数据视图
        cursor.execute("""
            CREATE OR REPLACE VIEW v_stock_data_monthly AS
            SELECT
                symbol,
                DATE_TRUNC('month', timestamp) as month_start,
                MIN(open_price) as open_price,
                MAX(high_price) as high_price,
                MIN(low_price) as low_price,
                MAX(close_price) as close_price,
                SUM(volume) as volume,
                COUNT(*) as data_points
            FROM stock_data
            GROUP BY symbol, DATE_TRUNC('month', timestamp)
            ORDER BY symbol, month_start DESC;
        """)

        # 股票数据统计视图
        cursor.execute("""
            CREATE OR REPLACE VIEW v_stock_data_stats AS
            SELECT
                symbol,
                COUNT(*) as total_records,
                MIN(timestamp) as first_record,
                MAX(timestamp) as last_record,
                AVG(CASE WHEN volume > 0 THEN close_price END) as avg_price,
                MAX(close_price) as max_price,
                MIN(close_price) as min_price,
                SUM(volume) as total_volume,
                COUNT(DISTINCT DATE_TRUNC('day', timestamp)) as trading_days
            FROM stock_data
            GROUP BY symbol
            ORDER BY total_records DESC;
        """)

        logger.info("股票数据聚合视图创建完成")

    def _create_strategy_execution_views(self, cursor):
        """创建策略执行聚合视图"""

        # 每日执行统计视图
        cursor.execute("""
            CREATE OR REPLACE VIEW v_strategy_executions_daily AS
            SELECT
                strategy_id,
                execution_mode,
                DATE_TRUNC('day', created_at) as execution_date,
                COUNT(*) as execution_count,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as successful_executions,
                COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_executions,
                COUNT(CASE WHEN status = 'running' THEN 1 END) as running_executions,
                AVG(EXTRACT(EPOCH FROM (end_time - start_time))) as avg_duration_seconds,
                MAX(EXTRACT(EPOCH FROM (end_time - start_time))) as max_duration_seconds,
                MIN(EXTRACT(EPOCH FROM (end_time - start_time))) as min_duration_seconds,
                SUM(signals_count) as total_signals_generated
            FROM strategy_executions
            GROUP BY strategy_id, execution_mode, DATE_TRUNC('day', created_at)
            ORDER BY execution_date DESC, execution_count DESC;
        """)

        # 策略执行性能视图
        cursor.execute("""
            CREATE OR REPLACE VIEW v_strategy_execution_performance AS
            SELECT
                se.strategy_id,
                s.name as strategy_name,
                se.execution_mode,
                COUNT(*) as total_executions,
                COUNT(CASE WHEN se.status = 'completed' THEN 1 END) as successful_executions,
                COUNT(CASE WHEN se.status = 'failed' THEN 1 END) as failed_executions,
                ROUND(
                    COUNT(CASE WHEN se.status = 'completed' THEN 1 END) * 100.0 /
                    NULLIF(COUNT(*), 0), 2
                ) as success_rate,
                AVG(EXTRACT(EPOCH FROM (se.end_time - se.start_time))) as avg_duration_seconds,
                MAX(se.created_at) as last_execution,
                AVG(se.signals_count) as avg_signals_per_execution
            FROM strategy_executions se
            LEFT JOIN strategies s ON se.strategy_id = s.id
            GROUP BY se.strategy_id, s.name, se.execution_mode
            ORDER BY success_rate DESC, total_executions DESC;
        """)

        logger.info("策略执行聚合视图创建完成")

    def _create_performance_metric_views(self, cursor):
        """创建性能指标聚合视图"""

        # 每日性能指标视图
        cursor.execute("""
            CREATE OR REPLACE VIEW v_performance_metrics_daily AS
            SELECT
                strategy_id,
                metric_type,
                DATE_TRUNC('day', recorded_at) as metric_date,
                COUNT(*) as measurement_count,
                AVG(metric_value) as avg_value,
                MAX(metric_value) as max_value,
                MIN(metric_value) as min_value,
                STDDEV(metric_value) as stddev_value,
                MAX(recorded_at) as last_measurement
            FROM performance_metrics
            GROUP BY strategy_id, metric_type, DATE_TRUNC('day', recorded_at)
            ORDER BY metric_date DESC, strategy_id, metric_type;
        """)

        # 性能指标趋势视图
        cursor.execute("""
            CREATE OR REPLACE VIEW v_performance_metrics_trend AS
            SELECT
                strategy_id,
                metric_type,
                DATE_TRUNC('month', recorded_at) as month_start,
                AVG(metric_value) as monthly_avg,
                MIN(metric_value) as monthly_min,
                MAX(metric_value) as monthly_max,
                COUNT(*) as measurements_count,
                -- 计算环比变化
                LAG(AVG(metric_value)) OVER (
                    PARTITION BY strategy_id, metric_type
                    ORDER BY DATE_TRUNC('month', recorded_at)
                ) as prev_month_avg
            FROM performance_metrics
            GROUP BY strategy_id, metric_type, DATE_TRUNC('month', recorded_at)
            ORDER BY month_start DESC;
        """)

        logger.info("性能指标聚合视图创建完成")

    def _create_analytical_views(self, cursor):
        """创建综合分析视图"""

        # 策略综合表现视图
        cursor.execute("""
            CREATE OR REPLACE VIEW v_strategy_overview AS
            SELECT DISTINCT
                s.id as strategy_id,
                s.name as strategy_name,
                s.strategy_type,
                s.status,
                s.created_at as strategy_created,
                s.last_executed,
                -- 最近信号统计
                (SELECT COUNT(*) FROM strategy_signals ss WHERE ss.strategy_id = s.id
                 AND ss.timestamp > NOW() - INTERVAL '30 days') as signals_last_30_days,
                -- 最近执行统计
                (SELECT COUNT(*) FROM strategy_executions se WHERE se.strategy_id = s.id
                 AND se.created_at > NOW() - INTERVAL '30 days') as executions_last_30_days,
                -- 平均信号置信度
                (SELECT AVG(confidence) FROM strategy_signals ss WHERE ss.strategy_id = s.id
                 AND ss.timestamp > NOW() - INTERVAL '30 days') as avg_confidence_30_days
            FROM strategies s
            ORDER BY s.last_executed DESC NULLS LAST;
        """)

        # 市场信号热力图视图
        cursor.execute("""
            CREATE OR REPLACE VIEW v_market_signal_heatmap AS
            SELECT
                symbol,
                DATE_TRUNC('day', timestamp) as signal_date,
                COUNT(CASE WHEN signal_type = 'BUY' THEN 1 END) as buy_intensity,
                COUNT(CASE WHEN signal_type = 'SELL' THEN 1 END) as sell_intensity,
                COUNT(CASE WHEN signal_type = 'HOLD' THEN 1 END) as hold_intensity,
                COUNT(*) as total_signals,
                AVG(confidence) as avg_confidence,
                -- 计算信号强度指数
                (COUNT(CASE WHEN signal_type = 'BUY' THEN 1 END) * 1.0 +
                 COUNT(CASE WHEN signal_type = 'SELL' THEN 1 END) * -1.0 +
                 COUNT(CASE WHEN signal_type = 'HOLD' THEN 1 END) * 0.0) /
                NULLIF(COUNT(*), 0) as signal_strength_index
            FROM strategy_signals
            WHERE timestamp > NOW() - INTERVAL '7 days'
            GROUP BY symbol, DATE_TRUNC('day', timestamp)
            ORDER BY signal_date DESC, total_signals DESC;
        """)

        logger.info("综合分析视图创建完成")

    def refresh_materialized_views(self) -> bool:
        """刷新物化视图"""
        logger.info("开始刷新物化视图...")

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # 获取所有物化视图
                cursor.execute("""
                    SELECT schemaname, matviewname
                    FROM pg_matviews
                    WHERE schemaname = 'public';
                """)

                matviews = cursor.fetchall()

                for schema, view_name in matviews:
                    try:
                        cursor.execute(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {view_name}")
                        logger.info(f"✅ 刷新物化视图: {view_name}")
                    except Exception as e:
                        logger.warning(f"刷新物化视图失败 {view_name}: {e}")

                conn.commit()
                logger.info("物化视图刷新完成")
                return True

        except Exception as e:
            logger.error(f"刷新物化视图失败: {e}")
            return False

    def get_view_usage_stats(self) -> List[Dict[str, Any]]:
        """获取视图使用统计"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # 获取视图访问统计 (需要pg_stat_statements扩展)
                cursor.execute("""
                    SELECT
                        schemaname,
                        viewname,
                        pg_size_pretty(pg_total_relation_size(schemaname||'.'||viewname)) as size
                    FROM pg_views
                    WHERE schemaname = 'public'
                    ORDER BY viewname;
                """)

                views = []
                for row in cursor.fetchall():
                    views.append({
                        'schema': row[0],
                        'name': row[1],
                        'size': row[2]
                    })

                return views

        except Exception as e:
            logger.error(f"获取视图使用统计失败: {e}")
            return []

    def create_performance_indexes(self) -> bool:
        """创建视图性能优化索引"""
        logger.info("开始创建视图性能索引...")

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # 为策略信号表创建索引
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_strategy_signals_composite
                    ON strategy_signals (strategy_id, timestamp DESC, signal_type);

                    CREATE INDEX IF NOT EXISTS idx_strategy_signals_symbol_time
                    ON strategy_signals (symbol, timestamp DESC);
                """)

                # 为股票数据表创建索引
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_stock_data_symbol_time_composite
                    ON stock_data (symbol, timestamp DESC);

                    CREATE INDEX IF NOT EXISTS idx_stock_data_time_desc
                    ON stock_data (timestamp DESC);
                """)

                # 为策略执行表创建索引
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_strategy_executions_strategy_time
                    ON strategy_executions (strategy_id, created_at DESC);

                    CREATE INDEX IF NOT EXISTS idx_strategy_executions_status_time
                    ON strategy_executions (status, created_at DESC);
                """)

                # 为性能指标表创建索引
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_performance_metrics_strategy_type_time
                    ON performance_metrics (strategy_id, metric_type, recorded_at DESC);
                """)

                conn.commit()
                logger.info("视图性能索引创建完成")
                return True

        except Exception as e:
            logger.error(f"创建视图性能索引失败: {e}")
            return False