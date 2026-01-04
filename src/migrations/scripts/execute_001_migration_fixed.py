#!/usr/bin/env python3
"""
Execute the 001 base tables migration script with PostgreSQL 15 compatibility
執行基礎表遷移腳本 (PostgreSQL 15 兼容版本)
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

import psycopg2
from psycopg2.extras import DictCursor

def execute_migration():
    """Execute 001 base tables migration using psycopg2 with error handling for types"""

    # Database connection parameters from docker-compose.yml
    db_url = "postgresql://cbsc_user:cbsc_password@localhost:5432/cbsc_strategy"

    print("=" * 60)
    print("CBSC Quant Strategy Management - Base Tables Migration")
    print("=" * 60)
    print()
    print("Migration: 001_create_base_tables (Fixed)")
    print("Target: PostgreSQL base tables (users, strategies)")
    print()

    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = False
        cursor = conn.cursor()

        print("Connected to database successfully!")

        # Read and execute the migration script with type handling
        migration_file = Path(__file__).parent / "001_create_base_tables.sql"

        if not migration_file.exists():
            print(f"Migration file not found: {migration_file}")
            return False

        print(f"Reading migration file: {migration_file}")

        with open(migration_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()

        print("Executing base tables migration script...")

        # Split the SQL into individual statements and handle types specially
        statements = sql_content.split(';')

        for statement in statements:
            statement = statement.strip()
            if not statement or statement.startswith('--'):
                continue

            try:
                # Handle CREATE TYPE statements without IF NOT EXISTS
                if 'CREATE TYPE IF NOT EXISTS' in statement:
                    # Extract type name and definition
                    type_match = statement.replace('CREATE TYPE IF NOT EXISTS', 'CREATE TYPE').strip()
                    # Check if type exists first
                    type_name = type_match.split()[2]
                    cursor.execute("""
                        SELECT typname FROM pg_type
                        WHERE typname = %s AND typtype = 'e'
                    """, (type_name,))

                    if cursor.fetchone() is None:
                        cursor.execute(statement.replace('CREATE TYPE IF NOT EXISTS', 'CREATE TYPE'))
                        print(f"  Created type: {type_name}")
                    else:
                        print(f"  Type already exists: {type_name}")
                else:
                    # Execute regular statements
                    cursor.execute(statement)

            except psycopg2.Error as e:
                # Ignore "already exists" errors for types and extensions
                if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                    print(f"  Object already exists, continuing...")
                    continue
                else:
                    raise e

        conn.commit()
        print("Base tables migration completed successfully!")

        # List created tables
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('users', 'strategies', 'strategy_categories', 'roles', 'user_roles')
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
        print("Ready to execute 003_strategy_management_tables migration.")
    else:
        print("Base tables migration failed!")

    print("=" * 60)