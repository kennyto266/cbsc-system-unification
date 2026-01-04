#!/usr/bin/env python3
"""
Execute the 001 base tables migration script
執行基礎表遷移腳本
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

import psycopg2
from psycopg2.extras import DictCursor

def execute_migration():
    """Execute 001 base tables migration using psycopg2"""

    # Database connection parameters from docker-compose.yml
    db_url = "postgresql://cbsc_user:cbsc_password@localhost:5432/cbsc_strategy"

    print("=" * 60)
    print("CBSC Quant Strategy Management - Base Tables Migration")
    print("=" * 60)
    print()
    print("Migration: 001_create_base_tables")
    print("Target: PostgreSQL base tables (users, strategies)")
    print()

    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = False
        cursor = conn.cursor()

        print("Connected to database successfully!")

        # Read and execute the migration script
        migration_file = Path(__file__).parent / "001_create_base_tables.sql"

        if not migration_file.exists():
            print(f"Migration file not found: {migration_file}")
            return False

        print(f"Reading migration file: {migration_file}")

        with open(migration_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()

        print("Executing base tables migration script...")

        # Execute the SQL script
        cursor.execute(sql_content)

        conn.commit()
        print("Base tables migration completed successfully!")

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
            print("\nCreated tables:")
            for (table_name,) in tables:
                print(f"  {table_name}")
        else:
            print("\nNo new tables were created (may already exist)")

        return True

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
            print("Database connection closed")

if __name__ == "__main__":
    success = execute_migration()

    print()
    print("=" * 60)

    if success:
        print("Base tables migration completed successfully!")
        print("Ready to execute 002_market_data_tables migration.")
    else:
        print("Base tables migration failed!")

    print("=" * 60)