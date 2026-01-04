#!/usr/bin/env python3
"""
Check existing tables in the database (simple version)
檢查數據庫中的現有表 (簡化版本)
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

import psycopg2
from psycopg2.extras import DictCursor

def check_tables():
    """Check existing tables in the database"""

    # Database connection parameters from docker-compose.yml
    db_url = "postgresql://cbsc_user:cbsc_password@localhost:5432/cbsc_strategy"

    print("Checking existing tables...")
    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()

        # List all tables
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)

        tables = cursor.fetchall()
        print("Existing tables:")
        for (table_name,) in tables:
            print(f"  {table_name}")

        # Check if required tables exist
        required_tables = ['users', 'strategies', 'strategy_categories']
        existing_required = []

        for table in required_tables:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = %s
                );
            """, (table,))

            exists = cursor.fetchone()[0]
            if exists:
                existing_required.append(table)
                print(f"[OK] {table} table exists")
            else:
                print(f"[MISSING] {table} table missing")

        cursor.close()
        conn.close()

        return len(existing_required) == len(required_tables)

    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    success = check_tables()
    print(f"All required tables exist: {success}")

    if success:
        print("Ready to execute 003_strategy_management_tables migration.")
    else:
        print("Some required tables are missing!")