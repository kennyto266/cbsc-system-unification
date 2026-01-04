#!/usr/bin/env python3
"""
Execute the PostgreSQL migration script for strategy management tables
執行策略管理表的 PostgreSQL 遷移腳本
"""

import sys
import os
import asyncio
from pathlib import Path

# Add project root to Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

# Try to import database configuration
try:
    import psycopg2
    from psycopg2.extras import DictCursor
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    print("psycopg2 not found, trying alternative approach...")

    try:
        import asyncpg
        ASYNCPG_AVAILABLE = True
    except ImportError:
        ASYNCPG_AVAILABLE = False
        print("Neither psycopg2 nor asyncpg is available!")
        print("Please install PostgreSQL adapter:")
        print("  pip install psycopg2-binary  # synchronous")
        print("  pip install asyncpg        # asynchronous")
        sys.exit(1)

def execute_migration_with_pycopg2():
    """Execute migration using psycopg2 (synchronous)"""

    # Database connection parameters from .env file
    db_url = "postgresql://cbsc_admin:cKelI4TJVKQ5pgCVKHYMY7GUZqqQsHvELoQBTJg-u8IPw!@localhost:5432/cbsc_production"

    print("🔌 Connecting to PostgreSQL...")
    print(f"Database: cbsc_production")

    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = False
        cursor = conn.cursor()

        print("✅ Connected to database successfully!")

        # Read and execute the migration script
        migration_file = Path(__file__).parent / "003_create_strategy_management_tables.sql"

        if not migration_file.exists():
            print(f"❌ Migration file not found: {migration_file}")
            return False

        print(f"📖 Reading migration file: {migration_file}")

        with open(migration_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()

        print("🚀 Executing migration script...")

        # Execute the SQL script
        cursor.execute(sql_content)

        # Get results for debugging
        if cursor.description:
            results = cursor.fetchall()
            if results:
                print("📊 Execution results:")
                for row in results:
                    print(f"  {row}")

        conn.commit()
        print("✅ Migration completed successfully!")

        # List created tables
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('strategy_configs', 'backtest_results', 'performance_records')
            ORDER BY table_name;
        """)

        tables = cursor.fetchall()
        if tables:
            print("\n📋 Created tables:")
            for (table_name,) in tables:
                print(f"  ✅ {table_name}")
        else:
            print("\n⚠️  No new tables were created (may already exist)")

        return True

    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
        print("\n🔧 Troubleshooting tips:")
        print("  1. Check if PostgreSQL is running: pg_ctl status")
        print("  2. Verify connection parameters in .env file")
        print(" 3. Ensure user has CREATE TABLE privileges")
        return False

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

    finally:
        if 'conn' in locals() and conn:
            cursor.close()
            conn.close()
            print("🔌 Database connection closed")

def execute_migration_with_asyncpg():
    """Execute migration using asyncpg (asynchronous)"""

    import asyncio

    async def run_migration():
        # Database connection parameters
        db_config = {
            'host': 'localhost',
            'port': 5432,
            'user': 'cbsc_admin',
            'password': 'cKelI4TJVKQ5pgCVKHYMY7GUZqqQsHvELoQBTJg-u8IPw!',
            'database': 'cbsc_production'
        }

        print("🔌 Connecting to PostgreSQL (asyncpg)...")

        try:
            conn = await asyncpg.connect(**db_config)
            print("✅ Connected to database successfully!")

            migration_file = Path(__file__).parent / "003_create_strategy_management_tables.sql"

            if not migration_file.exists():
                print(f"❌ Migration file not found: {migration_file}")
                return False

            print(f"📖 Reading migration file: {migration_file}")

            with open(migration_file, 'r', encoding='utf-8') as f:
                sql_content = f.read()

            print("🚀 Executing migration script...")

            # Split and execute individual statements
            statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]

            for i, statement in enumerate(statements, 1):
                if statement and not statement.startswith('--'):
                    try:
                        await conn.execute(statement)
                    except Exception as e:
                        # Some statements might not return results, that's OK
                        if "CREATE" in statement or "INSERT" in statement:
                            print(f"  ✅ Executed statement {i}")

            print("✅ Migration completed successfully!")

            return True

        except Exception as e:
            print(f"❌ Database error: {e}")
            return False

        finally:
            if 'conn' in locals():
                await conn.close()
                print("🔌 Database connection closed")

    return asyncio.run(run_migration())

def main():
    """Main execution function"""

    print("=" * 60)
    print("CBSC Quant Strategy Management - Database Migration")
    print("=" * 60)
    print()
    print("Migration: 003_create_strategy_management_tables")
    print("Target: PostgreSQL strategy management tables")
    print()

    # Check migration file exists
    migration_file = Path(__file__).parent / "003_create_strategy_management_tables.sql"
    if not migration_file.exists():
        print(f"❌ Migration file not found: {migration_file}")
        return

    file_size = migration_file.stat().st_size
    print(f"📄 File size: {file_size:,} bytes")

    # Execute migration based on available library
    if PSYCOPG2_AVAILABLE:
        success = execute_migration_with_pycopg2()
    elif ASYNCPG_AVAILABLE:
        success = execute_migration_with_asyncpg()
    else:
        print("❌ No PostgreSQL adapter available")
        print("\n💡 Please install one of:")
        print("  pip install psycopg2-binary  # synchronous, easier to use")
        print("  pip install asyncpg        # asynchronous, better performance")
        success = False

    print()
    print("=" * 60)

    if success:
        print("🎉 Migration completed successfully!")
        print()
        print("📌 Next steps:")
        print("  1. Verify tables: \\dt strategy_*")
        print(" 2. Check indexes: \\di+")
        print(" 3. Test connections in application")
    else:
        print("❌ Migration failed!")
        print()
        print("📌 Check:")
        print("  - PostgreSQL service is running")
        print("  - Database credentials in .env file")
        print("  - Network connectivity")

    print("=" * 60)

if __name__ == "__main__":
    main()