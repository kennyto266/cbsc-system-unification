#!/usr/bin/env python3
"""
Execute the minimal base tables migration script
執行最小基礎表遷移腳本
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

import psycopg2
from psycopg2.extras import DictCursor

def execute_migration():
    """Execute minimal base tables migration using psycopg2"""

    # Database connection parameters from docker-compose.yml
    db_url = "postgresql://cbsc_user:cbsc_password@localhost:5432/cbsc_strategy"

    print("=" * 60)
    print("CBSC Quant Strategy Management - Minimal Base Tables")
    print("=" * 60)
    print()
    print("Migration: create_minimal_base_tables")
    print("Target: PostgreSQL base tables (users, strategies)")
    print()

    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = False
        cursor = conn.cursor()

        print("Connected to database successfully!")

        # Read and execute the migration script
        migration_file = Path(__file__).parent / "create_minimal_base_tables.sql"

        if not migration_file.exists():
            print(f"Migration file not found: {migration_file}")
            return False

        print(f"Reading migration file: {migration_file}")

        with open(migration_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()

        print("Executing minimal base tables migration script...")

        # Execute the SQL script
        cursor.execute(sql_content)

        conn.commit()
        print("Minimal base tables migration completed successfully!")

        # List created tables
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('users', 'strategies', 'strategy_categories')
            ORDER BY table_name;
        """)

        tables = cursor.fetchall()
        if tables:
            print("\nCreated/Existing tables:")
            for (table_name,) in tables:
                print(f"  {table_name}")
        else:
            print("\nNo tables found")

        return True

    except psycopg2.Error as e:
        print(f"Database error: {e}")
        print("This might be normal if tables already exist.")
        # Don't return False for "already exists" errors
        if "already exists" in str(e).lower():
            return True
        return False

    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

    finally:
        if 'conn' in locals() and conn:
            cursor.close()
            conn.close()
            print("Database connection closed")

if __name__ == "__main__":
    success = execute_migration()

    print()
    print("=" * 60)

    if success:
        print("Minimal base tables migration completed successfully!")
        print("Ready to execute 003_strategy_management_tables migration.")
    else:
        print("Minimal base tables migration failed!")

    print("=" * 60)