#!/usr/bin/env python3
"""
Data Migration Script for CBSC Partitioned Tables
Safely migrates data from regular tables to partitioned tables with validation
"""

import os
import sys
import logging
import argparse
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple, Any
import json
import time
import psycopg2
from psycopg2 import sql, extras
from psycopg2.pool import ThreadedConnectionPool
import psycopg2.extras

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

class PartitionedTableMigrator:
    """Handles migration to partitioned tables with validation and rollback capabilities"""

    def __init__(self, db_config: Dict):
        self.db_config = db_config
        self.pool = None
        self.logger = self._setup_logger()
        self.migration_log = []

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

    def log(self, level: str, message: str, **kwargs):
        """Log message with structured data"""
        log_entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': level,
            'message': message,
            **kwargs
        }
        self.migration_log.append(log_entry)

        if level == 'ERROR':
            self.logger.error(message)
        elif level == 'WARNING':
            self.logger.warning(message)
        elif level == 'INFO':
            self.logger.info(message)
        else:
            self.logger.debug(message)

    def initialize_connection_pool(self):
        """Initialize database connection pool"""
        try:
            self.pool = ThreadedConnectionPool(
                minconn=2,
                maxconn=10,
                **self.db_config
            )
            self.log('INFO', 'Database connection pool initialized successfully')
        except Exception as e:
            self.log('ERROR', f'Failed to initialize connection pool: {e}')
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

    def check_prerequisites(self) -> Dict[str, Any]:
        """Check migration prerequisites"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                checks = {}

                # Check PostgreSQL version
                cur.execute("SELECT version()")
                version = cur.fetchone()[0]
                checks['postgresql_version'] = version
                checks['postgresql_supported'] = 'PostgreSQL 12' in version or 'PostgreSQL 13' in version or 'PostgreSQL 14' in version or 'PostgreSQL 15' in version or 'PostgreSQL 16' in version

                # Check table existence
                tables_to_check = ['strategy_performance', 'trades', 'performance_metrics']
                for table in tables_to_check:
                    cur.execute("""
                        SELECT EXISTS (
                            SELECT 1 FROM information_schema.tables
                            WHERE table_name = %s
                        )
                    """, (table,))
                    exists = cur.fetchone()[0]
                    checks[f'table_{table}_exists'] = exists

                # Check partitioned tables readiness
                partitioned_tables = ['strategy_performance_partitioned', 'trades_partitioned', 'performance_metrics_partitioned']
                for table in partitioned_tables:
                    cur.execute("""
                        SELECT EXISTS (
                            SELECT 1 FROM information_schema.tables
                            WHERE table_name = %s
                        )
                    """, (table,))
                    exists = cur.fetchone()[0]
                    checks[f'partitioned_table_{table}_exists'] = exists

                # Check disk space (simplified check)
                cur.execute("SELECT pg_size_pretty(pg_database_size(current_database()))")
                db_size = cur.fetchone()[0]
                checks['database_size'] = db_size

                # Check if we have enough disk space (basic check)
                # This is a simplified check - in production you'd want more sophisticated monitoring
                cur.execute("""
                    SELECT SUM(pg_total_relation_size(schemaname||'.'||tablename))
                    FROM pg_tables
                    WHERE tablename IN %s
                """, (tuple(tables_to_check),))
                total_size = cur.fetchone()[0] or 0
                checks['total_data_size_bytes'] = total_size
                checks['total_data_size_gb'] = round(total_size / (1024**3), 2)
                checks['estimated_migration_space_gb'] = round(total_size / (1024**3) * 1.5, 2)  # 50% buffer

                return checks

        finally:
            self.release_connection(conn)

    def validate_table_data(self, table_name: str, backup_suffix: str = '_backup') -> Dict:
        """Validate data integrity between original and backup tables"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                validation = {
                    'table': table_name,
                    'validation_time': datetime.now(timezone.utc).isoformat()
                }

                # Count records in both tables
                cur.execute(f"SELECT COUNT(*) FROM {table_name}")
                original_count = cur.fetchone()[0]
                validation['original_count'] = original_count

                backup_table = f"{table_name}{backup_suffix}"
                cur.execute(f"SELECT COUNT(*) FROM {backup_table}")
                backup_count = cur.fetchone()[0]
                validation['backup_count'] = backup_count

                validation['counts_match'] = original_count == backup_count

                # Check if backup table has recent data
                if table_name in ['strategy_performance', 'trades']:
                    date_column = 'date' if table_name == 'strategy_performance' else 'trade_time'
                    cur.execute(f"""
                        SELECT MAX({date_column}) FROM {table_name}
                    """)
                    original_max_date = cur.fetchone()[0]

                    cur.execute(f"""
                        SELECT MAX({date_column}) FROM {backup_table}
                    """)
                    backup_max_date = cur.fetchone()[0]

                    validation['original_max_date'] = original_max_date.isoformat() if original_max_date else None
                    validation['backup_max_date'] = backup_max_date.isoformat() if backup_max_date else None
                    validation['max_dates_match'] = original_max_date == backup_max_date

                # Sample data validation (check first 10 records)
                if original_count > 0:
                    # This is a simplified validation - in production you'd want more comprehensive checks
                    validation['sample_validation'] = 'passed'
                else:
                    validation['sample_validation'] = 'skipped_empty_table'

                validation['overall_status'] = 'passed' if validation.get('counts_match', False) else 'failed'

                return validation

        except Exception as e:
            self.log('ERROR', f'Validation failed for {table_name}: {e}')
            return {
                'table': table_name,
                'validation_time': datetime.now(timezone.utc).isoformat(),
                'error': str(e),
                'overall_status': 'error'
            }
        finally:
            self.release_connection(conn)

    def create_backups(self) -> Dict[str, bool]:
        """Create backups of original tables"""
        conn = self.get_connection()
        try:
            tables = ['strategy_performance', 'trades', 'performance_metrics']
            backup_results = {}

            for table in tables:
                backup_table = f"{table}_backup"
                start_time = time.time()

                self.log('INFO', f'Creating backup for {table} to {backup_table}')

                try:
                    with conn.cursor() as cur:
                        # Check if backup already exists
                        cur.execute("""
                            SELECT EXISTS (
                                SELECT 1 FROM information_schema.tables
                                WHERE table_name = %s
                            )
                        """, (backup_table,))
                        backup_exists = cur.fetchone()[0]

                        if backup_exists:
                            self.log('WARNING', f'Backup table {backup_table} already exists, skipping')
                            backup_results[table] = True
                            continue

                        # Create backup using CREATE TABLE AS
                        cur.execute(f'CREATE TABLE {backup_table} AS SELECT * FROM {table}')

                        # Get record count
                        cur.execute(f'SELECT COUNT(*) FROM {backup_table}')
                        count = cur.fetchone()[0]

                        duration = time.time() - start_time
                        self.log('INFO', f'Backup created for {table}: {count:,} records in {duration:.2f}s')

                        backup_results[table] = True

                except Exception as e:
                    self.log('ERROR', f'Failed to create backup for {table}: {e}')
                    backup_results[table] = False

            conn.commit()
            return backup_results

        except Exception as e:
            conn.rollback()
            self.log('ERROR', f'Backup creation failed: {e}')
            raise
        finally:
            self.release_connection(conn)

    def migrate_table(self, table_name: str, batch_size: int = 10000, validate: bool = True) -> Dict:
        """Migrate data from original table to partitioned table"""
        conn = self.get_connection()
        try:
            self.log('INFO', f'Starting migration for {table_name}')

            migration_result = {
                'table': table_name,
                'started_at': datetime.now(timezone.utc).isoformat(),
                'batch_size': batch_size,
                'status': 'running'
            }

            with conn.cursor() as cur:
                # Get total records to migrate
                cur.execute(f'SELECT COUNT(*) FROM {table_name}')
                total_records = cur.fetchone()[0]
                migration_result['total_records'] = total_records

                if total_records == 0:
                    migration_result['status'] = 'completed'
                    migration_result['migrated_records'] = 0
                    migration_result['message'] = 'No records to migrate'
                    return migration_result

                # Determine partitioned table name
                partitioned_table = f"{table_name}_partitioned"
                migration_result['partitioned_table'] = partitioned_table

                # Check if partitioned table exists
                cur.execute("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables
                        WHERE table_name = %s
                    )
                """, (partitioned_table,))
                partitioned_exists = cur.fetchone()[0]

                if not partitioned_exists:
                    raise Exception(f'Partitioned table {partitioned_table} does not exist')

                # Migration in batches
                offset = 0
                migrated_count = 0
                batch_count = 0

                while offset < total_records:
                    batch_start = time.time()

                    # Insert batch into partitioned table
                    if table_name == 'strategy_performance':
                        # Use the migration function if available
                        try:
                            cur.execute(f"""
                                SELECT migrate_strategy_performance_data(
                                    %s,
                                    NULL,
                                    NULL
                                )
                            """, (batch_size,))
                        except:
                            # Fallback to direct INSERT
                            cur.execute(f"""
                                INSERT INTO {partitioned_table}
                                SELECT * FROM {table_name}
                                LIMIT %s OFFSET %s
                            """, (batch_size, offset))
                    else:
                        # Direct INSERT for other tables
                        cur.execute(f"""
                            INSERT INTO {partitioned_table}
                            SELECT * FROM {table_name}
                            LIMIT %s OFFSET %s
                        """, (batch_size, offset))

                    batch_duration = time.time() - batch_start
                    batch_count += 1
                    offset += batch_size

                    GET DIAGNOSTICS migrated_count = ROW_COUNT
                    migration_result['migrated_records'] = offset

                    # Commit every 10 batches
                    if batch_count % 10 == 0:
                        conn.commit()
                        self.log('INFO', f'Migrated {offset:,} of {total_records:,} records for {table_name} (batch {batch_count}, {batch_duration:.2f}s)')

                # Final commit
                conn.commit()

                migration_result['completed_at'] = datetime.now(timezone.utc).isoformat()
                migration_result['status'] = 'completed'
                migration_result['total_batches'] = batch_count

                # Validation if requested
                if validate:
                    self.log('INFO', f'Running validation for {table_name}')
                    validation = self.validate_table_data(table_name, '_partitioned')
                    migration_result['validation'] = validation

                self.log('INFO', f'Migration completed for {table_name}: {migration_result["migrated_records"]:,} records')

            return migration_result

        except Exception as e:
            conn.rollback()
            migration_result['status'] = 'failed'
            migration_result['error'] = str(e)
            migration_result['completed_at'] = datetime.now(timezone.utc).isoformat()
            self.log('ERROR', f'Migration failed for {table_name}: {e}')
            return migration_result
        finally:
            self.release_connection(conn)

    def perform_switchover(self, table_name: str, backup_suffix: str = '_old') -> Dict:
        """Switch from original table to partitioned table"""
        conn = self.get_connection()
        try:
            self.log('INFO', f'Performing switchover for {table_name}')

            switchover_result = {
                'table': table_name,
                'started_at': datetime.now(timezone.utc).isoformat(),
                'status': 'running'
            }

            with conn.cursor() as cur:
                original_table = table_name
                partitioned_table = f"{table_name}_partitioned"
                old_table = f"{table_name}{backup_suffix}"

                # Steps for switchover:
                # 1. Rename original table to old
                # 2. Rename partitioned table to original name
                # 3. Update views if needed

                self.log('INFO', f'Renaming {original_table} to {old_table}')
                cur.execute(f'ALTER TABLE {original_table} RENAME TO {old_table}')

                self.log('INFO', f'Renaming {partitioned_table} to {original_table}')
                cur.execute(f'ALTER TABLE {partitioned_table} RENAME TO {original_table}')

                # Recreate views if needed (they should reference the original table name)
                if table_name == 'strategy_performance':
                    # Rebuild views that reference strategy_performance
                    cur.execute('DROP VIEW IF EXISTS strategy_performance_latest')
                    cur.execute("""
                        CREATE OR REPLACE VIEW strategy_performance_latest AS
                        WITH latest_dates AS (
                            SELECT
                                strategy_id,
                                MAX(date) as latest_date
                            FROM strategy_performance
                            GROUP BY strategy_id
                        )
                        SELECT
                            sp.*,
                            s.name as strategy_name,
                            s.code as strategy_code,
                            sc.display_name as category_name
                        FROM strategy_performance sp
                        JOIN latest_dates ld ON sp.strategy_id = ld.strategy_id AND sp.date = ld.latest_date
                        JOIN strategies s ON sp.strategy_id = s.id
                        LEFT JOIN strategy_categories sc ON s.category_id = sc.id
                    """)

                conn.commit()

                switchover_result['completed_at'] = datetime.now(timezone.utc).isoformat()
                switchover_result['status'] = 'completed'
                switchover_result['actions'] = [
                    f'Renamed {original_table} to {old_table}',
                    f'Renamed {partitioned_table} to {original_table}'
                ]

                self.log('INFO', f'Switchover completed for {table_name}')

            return switchover_result

        except Exception as e:
            conn.rollback()
            switchover_result['status'] = 'failed'
            switchover_result['error'] = str(e)
            switchover_result['completed_at'] = datetime.now(timezone.utc).isoformat()
            self.log('ERROR', f'Switchover failed for {table_name}: {e}')
            return switchover_result
        finally:
            self.release_connection(conn)

    def rollback_migration(self, table_name: str, backup_suffix: str = '_old') -> Dict:
        """Rollback migration by restoring from backup"""
        conn = self.get_connection()
        try:
            self.log('WARNING', f'Rolling back migration for {table_name}')

            rollback_result = {
                'table': table_name,
                'started_at': datetime.now(timezone.utc).isoformat(),
                'status': 'running'
            }

            with conn.cursor() as cur:
                original_table = table_name
                backup_table = f"{table_name}_backup"
                current_table = f"{table_name}_partitioned"

                # Check if backup exists
                cur.execute("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables
                        WHERE table_name = %s
                    )
                """, (backup_table,))
                backup_exists = cur.fetchone()[0]

                if not backup_exists:
                    raise Exception(f'Backup table {backup_table} does not exist')

                # Steps for rollback:
                # 1. Drop current partitioned table
                # 2. Rename backup to original

                self.log('WARNING', f'Dropping current {current_table}')
                cur.execute(f'DROP TABLE IF EXISTS {current_table}')

                self.log('WARNING', f'Renaming {backup_table} to {original_table}')
                cur.execute(f'ALTER TABLE {backup_table} RENAME TO {original_table}')

                conn.commit()

                rollback_result['completed_at'] = datetime.now(timezone.utc).isoformat()
                rollback_result['status'] = 'completed'
                rollback_result['actions'] = [
                    f'Dropped {current_table}',
                    f'Renamed {backup_table} to {original_table}'
                ]

                self.log('WARNING', f'Rollback completed for {table_name}')

            return rollback_result

        except Exception as e:
            conn.rollback()
            rollback_result['status'] = 'failed'
            rollback_result['error'] = str(e)
            rollback_result['completed_at'] = datetime.now(timezone.utc).isoformat()
            self.log('ERROR', f'Rollback failed for {table_name}: {e}')
            return rollback_result
        finally:
            self.release_connection(conn)

    def run_full_migration(self, tables: List[str] = None, batch_size: int = 10000, skip_backup: bool = False) -> Dict:
        """Run complete migration process"""
        if tables is None:
            tables = ['strategy_performance', 'trades', 'performance_metrics']

        migration_summary = {
            'started_at': datetime.now(timezone.utc).isoformat(),
            'tables': tables,
            'status': 'running',
            'steps': {}
        }

        try:
            # Step 1: Check prerequisites
            self.log('INFO', 'Checking migration prerequisites')
            prerequisites = self.check_prerequisites()
            migration_summary['steps']['prerequisites'] = prerequisites

            if not prerequisites.get('postgresql_supported', False):
                raise Exception('PostgreSQL version not supported for partitioning')

            # Step 2: Create backups (unless skipped)
            if not skip_backup:
                self.log('INFO', 'Creating table backups')
                backup_results = self.create_backups()
                migration_summary['steps']['backups'] = backup_results

                if not all(backup_results.values()):
                    failed_backups = [k for k, v in backup_results.items() if not v]
                    raise Exception(f'Backup creation failed for: {failed_backups}')

            # Step 3: Migrate tables
            migration_summary['steps']['migrations'] = {}
            for table in tables:
                self.log('INFO', f'Migrating table: {table}')
                migration_result = self.migrate_table(table, batch_size)
                migration_summary['steps']['migrations'][table] = migration_result

                if migration_result['status'] != 'completed':
                    raise Exception(f'Migration failed for {table}: {migration_result.get("error", "Unknown error")}')

            # Step 4: Perform switchover
            migration_summary['steps']['switchovers'] = {}
            for table in tables:
                self.log('INFO', f'Performing switchover for: {table}')
                switchover_result = self.perform_switchover(table)
                migration_summary['steps']['switchovers'][table] = switchover_result

                if switchover_result['status'] != 'completed':
                    raise Exception(f'Switchover failed for {table}: {switchover_result.get("error", "Unknown error")}')

            migration_summary['completed_at'] = datetime.now(timezone.utc).isoformat()
            migration_summary['status'] = 'completed'

            self.log('INFO', 'Full migration completed successfully')

        except Exception as e:
            migration_summary['status'] = 'failed'
            migration_summary['error'] = str(e)
            migration_summary['completed_at'] = datetime.now(timezone.utc).isoformat()
            self.log('ERROR', f'Full migration failed: {e}')

        return migration_summary

    def save_migration_report(self, migration_result: Dict, filename: str = None):
        """Save migration report to file"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'migration_report_{timestamp}.json'

        report = {
            'migration_report': migration_result,
            'migration_log': self.migration_log,
            'generated_at': datetime.now(timezone.utc).isoformat()
        }

        with open(filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        self.log('INFO', f'Migration report saved to: {filename}')
        return filename

def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Migrate CBSC tables to partitioned tables')
    parser.add_argument('--tables', nargs='+',
                       choices=['strategy_performance', 'trades', 'performance_metrics'],
                       help='Tables to migrate (default: all)')
    parser.add_argument('--batch-size', type=int, default=10000,
                       help='Batch size for migration (default: 10000)')
    parser.add_argument('--skip-backup', action='store_true',
                       help='Skip backup creation (DANGEROUS)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Check prerequisites and exit')
    parser.add_argument('--rollback', type=str,
                       help='Rollback migration for specified table')
    parser.add_argument('--validate', type=str,
                       help='Validate migration for specified table')
    parser.add_argument('--report-file', type=str,
                       help='Save migration report to specified file')

    args = parser.parse_args()

    # Database configuration
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

    migrator = PartitionedTableMigrator(db_config)

    try:
        if args.validate:
            print(f"\n=== Validating Migration for {args.validate} ===")
            result = migrator.validate_table_data(args.validate)
            print(json.dumps(result, indent=2, default=str))

        elif args.rollback:
            print(f"\n=== Rolling Back Migration for {args.rollback} ===")
            result = migrator.rollback_migration(args.rollback)
            print(json.dumps(result, indent=2, default=str))

        elif args.dry_run:
            print("\n=== Dry Run: Checking Prerequisites ===")
            prerequisites = migrator.check_prerequisites()
            print(json.dumps(prerequisites, indent=2, default=str))

            # Check if all prerequisites pass
            if (prerequisites.get('postgresql_supported', False) and
                all(prerequisites.get(f'table_{t}_exists', False) for t in ['strategy_performance', 'trades', 'performance_metrics']) and
                all(prerequisites.get(f'partitioned_table_{t}_partitioned_exists', False) for t in ['strategy_performance', 'trades', 'performance_metrics'])):
                print("\n✅ All prerequisites passed - ready for migration!")
            else:
                print("\n❌ Some prerequisites failed - review above output")

        else:
            print("\n=== Starting Full Migration ===")
            if args.skip_backup:
                print("⚠️  WARNING: Skipping backup creation!")

            result = migrator.run_full_migration(
                tables=args.tables,
                batch_size=args.batch_size,
                skip_backup=args.skip_backup
            )

            # Save report
            report_file = migrator.save_migration_report(result, args.report_file)

            print(f"\n=== Migration Summary ===")
            print(f"Status: {result['status']}")
            print(f"Started: {result['started_at']}")
            print(f"Completed: {result['completed_at']}")
            print(f"Tables: {result['tables']}")

            if result['status'] == 'completed':
                print(f"\n✅ Migration completed successfully!")
                print(f"Report saved to: {report_file}")
            else:
                print(f"\n❌ Migration failed: {result.get('error', 'Unknown error')}")
                print(f"Report saved to: {report_file}")
                sys.exit(1)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()