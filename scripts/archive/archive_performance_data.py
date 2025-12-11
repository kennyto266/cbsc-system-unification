#!/usr/bin/env python3
"""
Data Archiving Script for CBSC Strategy Performance Data
Implements tiered storage strategy: Hot (0-30 days), Warm (30-90 days), Cold (90+ days)
"""

import os
import sys
import logging
import argparse
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
import json
import psycopg2
from psycopg2 import sql, extras
from psycopg2.pool import ThreadedConnectionPool

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

class PerformanceDataArchiver:
    """Archive and manage strategy performance data with tiered storage strategy"""

    def __init__(self, db_config: Dict):
        self.db_config = db_config
        self.pool = None
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def initialize_connection_pool(self):
        """Initialize database connection pool"""
        try:
            self.pool = ThreadedConnectionPool(
                minconn=2,
                maxconn=10,
                **self.db_config
            )
            self.logger.info("Database connection pool initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize connection pool: {e}")
            raise

    def get_connection(self):
        """Get connection from pool"""
        if not self.pool:
            self.initialize_connection_pool()
        return self.pool.getconn()

    def release_connection(self, conn):
        """Release connection back to pool"""
        if self.pool:
            self.pool.putconn(conn)

    def get_data_tier_info(self) -> Dict:
        """Get information about data tiers"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                # Hot data (0-30 days)
                cur.execute("""
                    SELECT
                        COUNT(*) as record_count,
                        COUNT(DISTINCT strategy_id) as strategy_count,
                        MIN(date) as min_date,
                        MAX(date) as max_date
                    FROM strategy_performance
                    WHERE date >= CURRENT_DATE - INTERVAL '30 days'
                """)
                hot_data = cur.fetchone()

                # Warm data (30-90 days)
                cur.execute("""
                    SELECT
                        COUNT(*) as record_count,
                        COUNT(DISTINCT strategy_id) as strategy_count,
                        MIN(date) as min_date,
                        MAX(date) as max_date
                    FROM strategy_performance
                    WHERE date >= CURRENT_DATE - INTERVAL '90 days'
                    AND date < CURRENT_DATE - INTERVAL '30 days'
                """)
                warm_data = cur.fetchone()

                # Cold data (90+ days)
                cur.execute("""
                    SELECT
                        COUNT(*) as record_count,
                        COUNT(DISTINCT strategy_id) as strategy_count,
                        MIN(date) as min_date,
                        MAX(date) as max_date
                    FROM strategy_performance
                    WHERE date < CURRENT_DATE - INTERVAL '90 days'
                """)
                cold_data = cur.fetchone()

                return {
                    'hot': {
                        'record_count': hot_data[0],
                        'strategy_count': hot_data[1],
                        'date_range': f"{hot_data[2]} to {hot_data[3]}" if hot_data[2] else None
                    },
                    'warm': {
                        'record_count': warm_data[0],
                        'strategy_count': warm_data[1],
                        'date_range': f"{warm_data[2]} to {warm_data[3]}" if warm_data[2] else None
                    },
                    'cold': {
                        'record_count': cold_data[0],
                        'strategy_count': cold_data[1],
                        'date_range': f"{cold_data[2]} to {cold_data[3]}" if cold_data[2] else None
                    }
                }
        finally:
            self.release_connection(conn)

    def archive_old_data(self, days_to_keep: int = 90, batch_size: int = 10000) -> Dict:
        """Archive data older than specified days"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)

        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                # Check if archive table exists
                cur.execute("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables
                        WHERE table_name = 'strategy_performance_archive'
                    )
                """)
                archive_exists = cur.fetchone()[0]

                if not archive_exists:
                    self.logger.info("Creating archive table")
                    cur.execute("""
                        CREATE TABLE strategy_performance_archive (
                            LIKE strategy_performance INCLUDING ALL
                        )
                    """)

                    # Create indexes for archive table
                    cur.execute("""
                        CREATE INDEX idx_archive_strategy_date
                        ON strategy_performance_archive (strategy_id, date);
                        CREATE INDEX idx_archive_date
                        ON strategy_performance_archive (date);
                    """)

                # Get total records to archive
                cur.execute("""
                    SELECT COUNT(*) FROM strategy_performance
                    WHERE date < %s
                """, (cutoff_date.date(),))
                total_records = cur.fetchone()[0]

                if total_records == 0:
                    self.logger.info("No records to archive")
                    return {
                        'archived_count': 0,
                        'total_to_archive': 0,
                        'cutoff_date': cutoff_date.date().isoformat()
                    }

                self.logger.info(f"Found {total_records} records to archive (older than {cutoff_date.date()})")

                # Archive data in batches
                archived_count = 0
                offset = 0

                while offset < total_records:
                    # Move batch to archive
                    cur.execute("""
                        WITH batch AS (
                            SELECT ctid FROM strategy_performance
                            WHERE date < %s
                            ORDER BY date
                            LIMIT %s OFFSET %s
                        )
                        INSERT INTO strategy_performance_archive
                        SELECT * FROM strategy_performance
                        WHERE ctid IN (SELECT ctid FROM batch)
                        RETURNING id
                    """, (cutoff_date.date(), batch_size, offset))

                    batch_archived = len(cur.fetchall())
                    archived_count += batch_archived

                    # Delete archived records from main table
                    cur.execute("""
                        DELETE FROM strategy_performance
                        WHERE ctid IN (
                            SELECT ctid FROM strategy_performance
                            WHERE date < %s
                            ORDER BY date
                            LIMIT %s OFFSET %s
                        )
                    """, (cutoff_date.date(), batch_size, offset))

                    offset += batch_archived
                    conn.commit()

                    if offset % (batch_size * 10) == 0:
                        self.logger.info(f"Archived {archived_count:,} of {total_records:,} records")

                self.logger.info(f"Archive complete. Moved {archived_count:,} records to archive table")

                # Update statistics
                cur.execute("ANALYZE strategy_performance")
                cur.execute("ANALYZE strategy_performance_archive")

                return {
                    'archived_count': archived_count,
                    'total_to_archive': total_records,
                    'cutoff_date': cutoff_date.date().isoformat(),
                    'batches_processed': offset // batch_size
                }

        except Exception as e:
            conn.rollback()
            self.logger.error(f"Error during archiving: {e}")
            raise
        finally:
            self.release_connection(conn)

    def cleanup_old_partitions(self, months_to_keep: int = 24) -> Dict:
        """Drop old partitions beyond retention period"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                # Get list of old partitions
                cur.execute("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name LIKE 'strategy_performance_%'
                    AND table_name != 'strategy_performance_archive'
                """)

                partitions = [row[0] for row in cur.fetchall()]

                cutoff_date = datetime.now() - timedelta(days=months_to_keep * 30)
                partitions_to_drop = []

                for partition in partitions:
                    try:
                        # Extract date from partition name
                        # Format: strategy_performance_y2024_m01
                        year_part = partition.split('_')[2][1:]  # Remove 'y'
                        month_part = partition.split('_')[3][1:]  # Remove 'm'

                        partition_date = datetime.strptime(f"{year_part}-{month_part}", "%Y-%m")

                        if partition_date < cutoff_date:
                            partitions_to_drop.append(partition)

                    except (IndexError, ValueError):
                        self.logger.warning(f"Could not parse date from partition: {partition}")

                # Drop old partitions
                dropped_count = 0
                for partition in partitions_to_drop:
                    try:
                        cur.execute(f'DROP TABLE IF EXISTS {partition} CASCADE')
                        self.logger.info(f"Dropped partition: {partition}")
                        dropped_count += 1
                    except Exception as e:
                        self.logger.error(f"Failed to drop partition {partition}: {e}")

                conn.commit()

                return {
                    'partitions_analyzed': len(partitions),
                    'partitions_dropped': dropped_count,
                    'partitions_to_drop': partitions_to_drop,
                    'cutoff_date': cutoff_date.date().isoformat()
                }

        except Exception as e:
            conn.rollback()
            self.logger.error(f"Error during partition cleanup: {e}")
            raise
        finally:
            self.release_connection(conn)

    def create_aggregate_tables(self) -> Dict:
        """Create and populate aggregate tables for faster queries"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                # Create daily summary table if it doesn't exist
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS strategy_daily_summary (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        strategy_id UUID NOT NULL,
                        date DATE NOT NULL,
                        total_return DECIMAL(15,6),
                        daily_return DECIMAL(10,6),
                        volatility DECIMAL(10,6),
                        sharpe_ratio DECIMAL(8,4),
                        max_drawdown DECIMAL(10,6),
                        win_rate DECIMAL(5,4),
                        total_trades INTEGER,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        UNIQUE(strategy_id, date)
                    )
                """)

                # Create indexes
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_daily_summary_strategy_date
                    ON strategy_daily_summary (strategy_id, date);
                    CREATE INDEX IF NOT EXISTS idx_daily_summary_date
                    ON strategy_daily_summary (date);
                """)

                # Populate aggregate data for the last 30 days
                cur.execute("""
                    INSERT INTO strategy_daily_summary (
                        strategy_id, date, total_return, daily_return, volatility,
                        sharpe_ratio, max_drawdown, win_rate, total_trades
                    )
                    SELECT
                        strategy_id,
                        date,
                        AVG(total_return) as total_return,
                        AVG(daily_return) as daily_return,
                        AVG(volatility) as volatility,
                        AVG(sharpe_ratio) as sharpe_ratio,
                        AVG(max_drawdown) as max_drawdown,
                        AVG(win_rate) as win_rate,
                        SUM(total_trades) as total_trades
                    FROM strategy_performance
                    WHERE date >= CURRENT_DATE - INTERVAL '30 days'
                    GROUP BY strategy_id, date
                    ON CONFLICT (strategy_id, date) DO UPDATE SET
                        total_return = EXCLUDED.total_return,
                        daily_return = EXCLUDED.daily_return,
                        volatility = EXCLUDED.volatility,
                        sharpe_ratio = EXCLUDED.sharpe_ratio,
                        max_drawdown = EXCLUDED.max_drawdown,
                        win_rate = EXCLUDED.win_rate,
                        total_trades = EXCLUDED.total_trades,
                        created_at = NOW()
                """)

                # Get statistics
                cur.execute("SELECT COUNT(*) FROM strategy_daily_summary")
                summary_count = cur.fetchone()[0]

                cur.execute("SELECT COUNT(*) FROM strategy_performance WHERE date >= CURRENT_DATE - INTERVAL '30 days'")
                detail_count = cur.fetchone()[0]

                conn.commit()

                return {
                    'summary_records': summary_count,
                    'detail_records_last_30d': detail_count,
                    'compression_ratio': round(summary_count / max(detail_count, 1) * 100, 2)
                }

        except Exception as e:
            conn.rollback()
            self.logger.error(f"Error creating aggregate tables: {e}")
            raise
        finally:
            self.release_connection(conn)

    def get_archive_statistics(self) -> Dict:
        """Get comprehensive archive statistics"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                stats = {}

                # Main table statistics
                cur.execute("""
                    SELECT
                        COUNT(*) as total_records,
                        COUNT(DISTINCT strategy_id) as strategies,
                        MIN(date) as earliest_date,
                        MAX(date) as latest_date,
                        pg_total_relation_size('strategy_performance') as size_bytes
                    FROM strategy_performance
                """)
                main_stats = cur.fetchone()
                stats['main_table'] = {
                    'records': main_stats[0],
                    'strategies': main_stats[1],
                    'date_range': f"{main_stats[2]} to {main_stats[3]}" if main_stats[2] else None,
                    'size_mb': round(main_stats[4] / 1024 / 1024, 2) if main_stats[4] else 0
                }

                # Archive table statistics
                cur.execute("""
                    SELECT
                        COUNT(*) as total_records,
                        COUNT(DISTINCT strategy_id) as strategies,
                        MIN(date) as earliest_date,
                        MAX(date) as latest_date,
                        pg_total_relation_size('strategy_performance_archive') as size_bytes
                    FROM strategy_performance_archive
                """)
                archive_stats = cur.fetchone()
                stats['archive_table'] = {
                    'records': archive_stats[0] or 0,
                    'strategies': archive_stats[1] or 0,
                    'date_range': f"{archive_stats[2]} to {archive_stats[3]}" if archive_stats[2] else None,
                    'size_mb': round(archive_stats[4] / 1024 / 1024, 2) if archive_stats[4] else 0
                }

                # Daily summary statistics
                cur.execute("""
                    SELECT
                        COUNT(*) as total_records,
                        MIN(date) as earliest_date,
                        MAX(date) as latest_date,
                        pg_total_relation_size('strategy_daily_summary') as size_bytes
                    FROM strategy_daily_summary
                """)
                summary_stats = cur.fetchone()
                stats['summary_table'] = {
                    'records': summary_stats[0],
                    'date_range': f"{summary_stats[1]} to {summary_stats[2]}" if summary_stats[1] else None,
                    'size_mb': round(summary_stats[3] / 1024 / 1024, 2) if summary_stats[3] else 0
                }

                # Partition information
                cur.execute("""
                    SELECT
                        COUNT(*) as partition_count,
                        SUM(pg_total_relation_size(schemaname||'.'||tablename)) as total_size
                    FROM pg_tables
                    WHERE tablename LIKE 'strategy_performance_%'
                    AND tablename != 'strategy_performance_archive'
                """)
                partition_stats = cur.fetchone()
                stats['partitions'] = {
                    'count': partition_stats[0],
                    'total_size_mb': round(partition_stats[1] / 1024 / 1024, 2) if partition_stats[1] else 0
                }

                # Data tier information
                stats['tiers'] = self.get_data_tier_info()

                return stats

        finally:
            self.release_connection(conn)

def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Archive CBSC strategy performance data')
    parser.add_argument('--archive-days', type=int, default=90,
                       help='Archive data older than this many days (default: 90)')
    parser.add_argument('--cleanup-months', type=int, default=24,
                       help='Keep partitions for this many months (default: 24)')
    parser.add_argument('--batch-size', type=int, default=10000,
                       help='Batch size for archiving (default: 10000)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be done without executing')
    parser.add_argument('--create-aggregates', action='store_true',
                       help='Create aggregate tables for faster queries')
    parser.add_argument('--stats', action='store_true',
                       help='Show archive statistics')

    args = parser.parse_args()

    # Database configuration - should be loaded from environment or config file
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': os.getenv('DB_NAME', 'cbsc'),
        'user': os.getenv('DB_USER', 'cbsc_app'),
        'password': os.getenv('DB_PASSWORD')
    }

    if not db_config['password']:
        print("Error: DB_PASSWORD environment variable is required")
        sys.exit(1)

    archiver = PerformanceDataArchiver(db_config)

    try:
        if args.stats:
            print("\n=== Archive Statistics ===")
            stats = archiver.get_archive_statistics()
            print(json.dumps(stats, indent=2, default=str))

            print("\n=== Data Tier Information ===")
            tier_info = archiver.get_data_tier_info()
            print(json.dumps(tier_info, indent=2, default=str))

        if args.create_aggregates:
            print("\n=== Creating Aggregate Tables ===")
            result = archiver.create_aggregate_tables()
            print(f"Created {result['summary_records']} summary records")
            print(f"From {result['detail_records_last_30d']} detail records")
            print(f"Compression ratio: {result['compression_ratio']}%")

        if args.archive_days or args.cleanup_months:
            print("\n=== Archive Operations ===")

            if args.dry_run:
                print("DRY RUN MODE - No changes will be made")

            if args.archive_days:
                print(f"\nArchiving data older than {args.archive_days} days...")
                if not args.dry_run:
                    result = archiver.archive_old_data(args.archive_days, args.batch_size)
                    print(f"Archived {result['archived_count']:,} records")
                    print(f"Total to archive: {result['total_to_archive']:,}")
                else:
                    print("Would archive old data (dry run)")

            if args.cleanup_months:
                print(f"\nCleaning up partitions older than {args.cleanup_months} months...")
                if not args.dry_run:
                    result = archiver.cleanup_old_partitions(args.cleanup_months)
                    print(f"Dropped {result['partitions_dropped']} of {result['partitions_analyzed']} partitions")
                    if result['partitions_to_drop']:
                        print(f"Partitions dropped: {result['partitions_to_drop']}")
                else:
                    print("Would drop old partitions (dry run)")

        print("\nArchive operations completed successfully!")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()