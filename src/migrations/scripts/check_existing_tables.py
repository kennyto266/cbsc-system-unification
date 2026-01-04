#!/usr/bin/env python3
"""
Check existing tables in the database
檢查數據庫中的現有表
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

    print("=" * 60)
    print("CBSC Quant Strategy Management - Check Existing Tables")
    print("=" * 60)
    print()

    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()

        print("Connected to database successfully!")

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
                print(f"\n✅ {table} table exists")
            else:
                print(f"\n❌ {table} table missing")

        # If required tables exist, check their structure
        if existing_required:
            print(f"\nChecking structure of existing tables...")
            for table in existing_required:
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                    AND table_name = %s
                    ORDER BY ordinal_position;
                """, (table,))

                columns = cursor.fetchall()
                print(f"\n{table} columns:")
                for col_name, data_type, is_nullable, col_default in columns:
                    print(f"  {col_name}: {data_type} (nullable: {is_nullable}, default: {col_default})")

        return len(existing_required) == len(required_tables)

    except psycopg2.Error as e:
        print(f"Database error: {e}")
        return False

    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

    finally:
        if 'conn' in locals() and conn:
            cursor.close()
            conn.close()

if __name__ == "__main__":
    success = check_tables()

    print()
    print("=" * 60)

    if success:
        print("All required tables exist!")
        print("Ready to execute 003_strategy_management_tables migration.")
    else:
        print("Some required tables are missing!")

    print("=" * 60)