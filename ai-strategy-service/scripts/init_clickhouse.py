#!/usr/bin/env python3
"""
Initialize ClickHouse database schema for CBSC Analytics.

This script:
1. Connects to ClickHouse server
2. Creates database and tables
3. Sets up materialized views
4. Verifies installation
"""

import os
import sys
from clickhouse_driver import Client

# ClickHouse configuration
# Use native protocol (port 9000) instead of HTTP (port 8123)
CH_CONFIG = {
    'host': os.getenv('CLICKHOUSE_HOST', 'localhost'),
    'port': 9000,  # Native ClickHouse protocol
    'database': 'analytics',
    'user': os.getenv('CLICKHOUSE_USER', 'default'),
    'password': os.getenv('CLICKHOUSE_PASSWORD', ''),
    'connect_timeout': 30,
    'send_receive_timeout': 300
}


def connect_clickhouse():
    """Connect to ClickHouse server"""
    try:
        # Connect without specifying database first
        config = CH_CONFIG.copy()
        config.pop('database', None)
        client = Client(**config)
        client.execute('SELECT 1')
        print("[OK] Connected to ClickHouse successfully")
        return client
    except Exception as e:
        print(f"[ERROR] Failed to connect to ClickHouse: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure ClickHouse is running: docker compose up -d")
        print("2. Check if port 9000 is accessible")
        print("3. Check environment variables in .env")
        sys.exit(1)


def execute_schema(client, schema_file):
    """Execute SQL schema file"""
    try:
        with open(schema_file, 'r', encoding='utf-8') as f:
            sql = f.read()

        # Split by semicolon and execute each statement
        statements = [s.strip() for s in sql.split(';') if s.strip()]

        for i, statement in enumerate(statements, 1):
            if statement:
                client.execute(statement)
                print(f"[OK] Executed statement {i}/{len(statements)}")

        print(f"\n[OK] Executed {len(statements)} SQL statements")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to execute schema: {e}")
        return False


def verify_tables(client):
    """Verify that all tables were created"""
    expected_tables = [
        'strategy_backtests',
        'strategy_performance',
        'market_data',
        'trades',
        'etl_logs',
        'top_strategies_mv',
        'daily_performance_summary_mv'
    ]

    try:
        # Get existing tables
        result = client.execute("SHOW TABLES FROM analytics")
        existing_tables = [row[0] for row in result]

        print("\n[*] Verification:")
        for table in expected_tables:
            if table in existing_tables:
                print(f"  [OK] {table}")
            else:
                print(f"  [ERROR] {table} - MISSING")

        # Check if all tables exist
        missing = set(expected_tables) - set(existing_tables)
        if missing:
            print(f"\n[WARN]  Missing tables: {missing}")
            return False
        else:
            print("\n[OK] All tables and views created successfully")
            return True
    except Exception as e:
        print(f"[ERROR] Failed to verify tables: {e}")
        return False


def show_table_info(client):
    """Show information about created tables"""
    try:
        tables = ['strategy_backtests', 'strategy_performance', 'market_data', 'trades']

        print("\n[] Table Information:")
        for table in tables:
            try:
                result = client.execute(f"SELECT COUNT(*) FROM analytics.{table}")
                count = result[0][0]
                print(f"  • {table}: {count:,} rows")
            except:
                print(f"  • {table}: Empty")
    except Exception as e:
        print(f"[WARN]  Could not fetch table info: {e}")


def main():
    """Main initialization flow"""
    print("=" * 60)
    print("ClickHouse Schema Initialization")
    print("=" * 60)

    # Show configuration
    print("\n[+] Configuration:")
    print(f"  Host: {CH_CONFIG['host']}")
    print(f"  Database: {CH_CONFIG['database']}")

    # Connect to ClickHouse
    client = connect_clickhouse()

    # Get schema file path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    schema_file = os.path.join(script_dir, 'clickhouse_schema.sql')

    if not os.path.exists(schema_file):
        print(f"[!] Schema file not found: {schema_file}")
        sys.exit(1)

    print(f"\n[*] Schema file: {schema_file}")

    # Execute schema
    if not execute_schema(client, schema_file):
        sys.exit(1)

    # Verify tables
    if not verify_tables(client):
        sys.exit(1)

    # Show table info
    show_table_info(client)

    print("\n" + "=" * 60)
    print("[OK] ClickHouse initialization completed successfully!")
    print("=" * 60)


if __name__ == '__main__':
    main()
