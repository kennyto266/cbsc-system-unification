#!/usr/bin/env python3
"""
ETL Sync Pipeline - PostgreSQL to ClickHouse

This script synchronizes data from PostgreSQL (source) to ClickHouse (target)
for high-performance analytics queries.
"""

import os
import sys
import time
import logging
from datetime import datetime, timedelta
from typing import List, Tuple, Optional
import psycopg2
from clickhouse_driver import Client

# Import configuration
try:
    from etl_config import (
        PG_CONFIG, CH_CONFIG, TABLE_MAPPINGS,
        SYNC_INTERVAL_SECONDS, BATCH_SIZE, MAX_RETRIES,
        RETRY_DELAY_SECONDS, LOG_TABLE
    )
except ImportError:
    print("❌ Failed to import etl_config.py")
    print("Ensure you're running this script from the scripts/ directory")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ETLSync:
    """Main ETL synchronization class"""

    def __init__(self):
        """Initialize ETL sync instance"""
        self.pg_conn = None
        self.ch_client = None

    def connect(self):
        """Establish database connections"""
        try:
            # Connect to PostgreSQL
            self.pg_conn = psycopg2.connect(**PG_CONFIG)
            logger.info("✅ Connected to PostgreSQL")

            # Connect to ClickHouse
            self.ch_client = Client(**CH_CONFIG)
            self.ch_client.execute('SELECT 1')
            logger.info("✅ Connected to ClickHouse")

            return True
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            return False

    def disconnect(self):
        """Close database connections"""
        if self.pg_conn:
            self.pg_conn.close()
            logger.info("✅ Disconnected from PostgreSQL")
        if self.ch_client:
            self.ch_client.disconnect()
            logger.info("✅ Disconnected from ClickHouse")

    def get_last_sync_time(self, table_name: str) -> datetime:
        """Get the last successful sync timestamp from ETL logs"""
        try:
            query = f"""
            SELECT max(timestamp) as last_sync
            FROM {LOG_TABLE}
            WHERE target_table = '{table_name}' AND status = 'success'
            """

            result = self.ch_client.execute(query)
            if result and result[0][0]:
                return result[0][0]
            else:
                # Default to 1 hour ago if no previous sync
                return datetime.now() - timedelta(hours=1)
        except Exception as e:
            logger.warning(f"Could not get last sync time: {e}")
            return datetime.now() - timedelta(hours=1)

    def fetch_postgres_data(
        self,
        table_name: str,
        since: datetime
    ) -> List[Tuple]:
        """Fetch incremental data from PostgreSQL"""
        try:
            config = TABLE_MAPPINGS[table_name]
            source_table = config['source_table']
            timestamp_col = config['timestamp_column']

            query = f"""
            SELECT * FROM {source_table}
            WHERE {timestamp_col} >= %s
            ORDER BY {timestamp_col}
            LIMIT {BATCH_SIZE}
            """

            with self.pg_conn.cursor() as cursor:
                cursor.execute(query, (since,))
                results = cursor.fetchall()

                # Get column names
                col_names = [desc[0] for desc in cursor.description]

            logger.info(f"Fetched {len(results)} records from {source_table}")
            return results, col_names

        except Exception as e:
            logger.error(f"Failed to fetch from PostgreSQL: {e}")
            return [], []

    def transform_row(self, row: Tuple, col_names: List[str]) -> Tuple:
        """Transform a row for ClickHouse insertion"""
        try:
            # Convert datetime objects to strings
            transformed = []
            for i, value in enumerate(row):
                if isinstance(value, datetime):
                    transformed.append(value.strftime('%Y-%m-%d %H:%M:%S'))
                elif value is None:
                    transformed.append(0 if col_names[i].startswith(('is_', 'has_')) else None)
                else:
                    transformed.append(value)
            return tuple(transformed)
        except Exception as e:
            logger.error(f"Failed to transform row: {e}")
            return row

    def insert_clickhouse(
        self,
        table_name: str,
        data: List[Tuple],
        col_names: List[str]
    ) -> int:
        """Insert data into ClickHouse"""
        if not data:
            return 0

        try:
            # Transform data
            transformed_data = [self.transform_row(row, col_names) for row in data]

            # Insert into ClickHouse
            insert_query = f'INSERT INTO {table_name} ({", ".join(col_names)}) VALUES'
            self.ch_client.execute(insert_query, transformed_data)

            logger.info(f"Inserted {len(transformed_data)} records into {table_name}")
            return len(transformed_data)

        except Exception as e:
            logger.error(f"Failed to insert into ClickHouse: {e}")
            return 0

    def log_sync_operation(
        self,
        source_table: str,
        target_table: str,
        status: str,
        records_processed: int,
        records_failed: int = 0,
        error_message: str = "",
        duration: float = 0.0
    ):
        """Log ETL operation to ClickHouse"""
        try:
            query = f"""
            INSERT INTO {LOG_TABLE} (
                id, timestamp, source_table, target_table, status,
                records_processed, records_failed, error_message, sync_duration_seconds
            ) VALUES
            """

            # Generate unique ID
            log_id = int(datetime.now().timestamp() * 1000000)

            self.ch_client.execute(query, [(
                log_id,
                datetime.now(),
                source_table,
                target_table,
                status,
                records_processed,
                records_failed,
                error_message,
                duration
            )])

        except Exception as e:
            logger.error(f"Failed to log sync operation: {e}")

    def sync_table(self, table_name: str) -> bool:
        """Sync a single table from PostgreSQL to ClickHouse"""
        logger.info(f"\n{'='*60}")
        logger.info(f"Syncing table: {table_name}")
        logger.info(f"{'='*60}")

        start_time = time.time()
        config = TABLE_MAPPINGS[table_name]

        # Get last sync time
        last_sync = self.get_last_sync_time(table_name)
        logger.info(f"Last sync: {last_sync}")

        # Fetch data from PostgreSQL
        data, col_names = self.fetch_postgres_data(table_name, last_sync)

        if not data:
            logger.info(f"No new data to sync for {table_name}")
            self.log_sync_operation(
                source_table=config['source_table'],
                target_table=config['target_table'],
                status='success',
                records_processed=0,
                duration=time.time() - start_time
            )
            return True

        # Insert into ClickHouse
        inserted = self.insert_clickhouse(config['target_table'], data, col_names)

        duration = time.time() - start_time

        # Log result
        if inserted > 0:
            self.log_sync_operation(
                source_table=config['source_table'],
                target_table=config['target_table'],
                status='success',
                records_processed=inserted,
                duration=duration
            )
            logger.info(f"✅ Synced {inserted} records in {duration:.2f}s")
            return True
        else:
            self.log_sync_operation(
                source_table=config['source_table'],
                target_table=config['target_table'],
                status='failed',
                records_processed=len(data),
                records_failed=len(data),
                error_message="Failed to insert records",
                duration=duration
            )
            logger.error(f"❌ Failed to sync {table_name}")
            return False

    def run_sync(self) -> bool:
        """Run full sync cycle across all tables"""
        logger.info("\n" + "="*60)
        logger.info("Starting ETL Sync Cycle")
        logger.info("="*60)

        if not self.connect():
            return False

        success_count = 0
        total_tables = len(TABLE_MAPPINGS)

        try:
            for table_name in TABLE_MAPPINGS.keys():
                if self.sync_table(table_name):
                    success_count += 1
                else:
                    logger.warning(f"Table {table_name} sync failed, continuing...")

        finally:
            self.disconnect()

        logger.info("\n" + "="*60)
        logger.info(f"Sync Cycle Complete: {success_count}/{total_tables} tables successful")
        logger.info("="*60)

        return success_count == total_tables

    def run_continuous(self):
        """Run continuous sync loop"""
        logger.info(f"Starting continuous ETL sync (interval: {SYNC_INTERVAL_SECONDS}s)")
        logger.info("Press Ctrl+C to stop")

        try:
            while True:
                self.run_sync()
                logger.info(f"\n⏳ Waiting {SYNC_INTERVAL_SECONDS}s until next sync...")
                time.sleep(SYNC_INTERVAL_SECONDS)
        except KeyboardInterrupt:
            logger.info("\n👋 ETL sync stopped by user")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='ETL Sync from PostgreSQL to ClickHouse')
    parser.add_argument(
        '--once',
        action='store_true',
        help='Run sync once and exit'
    )
    args = parser.parse_args()

    etl = ETLSync()

    if args.once:
        success = etl.run_sync()
        sys.exit(0 if success else 1)
    else:
        etl.run_continuous()


if __name__ == '__main__':
    main()
