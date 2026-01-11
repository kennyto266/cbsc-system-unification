#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database Connection Test
数据库连接测试

Test database connectivity and configuration
测试数据库连接性和配置
"""

import os
import sys
from datetime import datetime

def test_database_configuration():
    """测试数据库配置"""
    print("=" * 60)
    print("DATABASE CONFIGURATION TEST")
    print("=" * 60)

    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("[OK] Environment variables loaded")
    except ImportError:
        print("[WARN] python-dotenv not installed, using os.getenv()")
        load_dotenv = lambda: None

    # Check required environment variables
    required_vars = [
        "POSTGRES_DB",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "DATABASE_URL"
    ]

    print("\n[CONFIGURATION CHECK]")
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values for display
            if "PASSWORD" in var or "SECRET" in var:
                display_value = "*" * min(len(value), 8) + "..."
            else:
                display_value = value
            print(f"  {var}: {display_value}")
        else:
            missing_vars.append(var)
            print(f"  {var}: [MISSING]")

    if missing_vars:
        print(f"\n[ERROR] Missing required environment variables: {', '.join(missing_vars)}")
        return False

    # Parse DATABASE_URL
    db_url = os.getenv("DATABASE_URL", "")
    if db_url:
        try:
            # Parse connection details from URL (basic parsing)
            if "://" in db_url:
                parts = db_url.split("://")
                if len(parts) >= 2:
                    auth_part = parts[1].split("@")[0] if "@" in parts[1] else ""
                    host_part = parts[1].split("@")[1] if "@" in parts[1] else parts[1]

                    if ":" in auth_part:
                        user, password = auth_part.split(":")
                        print(f"  Database User: {user}")
                        print(f"  Database Password: {'*' * min(len(password), 8)}...")

                    if "/" in host_part:
                        host, database = host_part.split("/", 1)
                        print(f"  Database Host: {host}")
                        print(f"  Database Name: {database}")
                    else:
                        print(f"  Database Host: {host_part}")

            print("[OK] Database URL parsed successfully")
        except Exception as e:
            print(f"[WARN] Could not parse DATABASE_URL: {e}")

    return True

def test_database_connectivity():
    """测试数据库连接性"""
    print("\n[CONNECTIVITY TEST]")

    # Test PostgreSQL server availability
    import socket

    host = os.getenv("POSTGRES_HOST", "localhost")
    port = int(os.getenv("POSTGRES_PORT", "5432"))

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)  # 5 second timeout
        result = sock.connect_ex((host, port))
        sock.close()

        if result == 0:
            print(f"  PostgreSQL server is reachable at {host}:{port}")
        else:
            print(f"  [X] Cannot connect to PostgreSQL server at {host}:{port}")
            print("  Please ensure:")
            print("    - PostgreSQL server is running")
            print("    - Host and port are correct")
            print("    - Firewall allows connection")
            return False

    except Exception as e:
        print(f"  [X] Network error: {e}")
        return False

    return True

def test_sqlite_fallback():
    """测试SQLite作为备用方案"""
    print("\n[SQLITE FALLBACK TEST]")

    try:
        import sqlite3
        import tempfile
        import os

        # Create test database
        test_db_path = os.path.join(tempfile.gettempdir(), "test_cbsc.db")

        # Connect to SQLite
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()

        # Test basic query
        cursor.execute("SELECT sqlite_version()")
        version = cursor.fetchone()[0]
        print(f"  SQLite version: {version}")

        # Create test table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_table (
                id INTEGER PRIMARY KEY,
                name TEXT,
                created_at TEXT
            )
        """)

        # Insert test data
        cursor.execute(
            "INSERT INTO test_table (name, created_at) VALUES (?, ?)",
            ("Database Test", datetime.now().isoformat())
        )

        # Query test data
        cursor.execute("SELECT COUNT(*) FROM test_table")
        count = cursor.fetchone()[0]
        print(f"  Test records: {count}")

        conn.close()

        # Clean up
        try:
            os.remove(test_db_path)
        except:
            pass

        print("[OK] SQLite fallback test successful")
        print("  SQLite database can be used as fallback option")
        return True

    except Exception as e:
        print(f"  [X] SQLite test failed: {e}")
        return False

def create_database_config_file():
    """创建数据库配置文件"""
    print("\n[CONFIGURATION FILE CREATION]")

    config_content = f"""# CBSC Strategy API Database Configuration
# Generated on: {datetime.now().isoformat()}

# =============================================================================
# PostgreSQL Database Configuration (Primary)
# =============================================================================
# Connection settings
POSTGRES_HOST={os.getenv("POSTGRES_HOST", "localhost")}
POSTGRES_PORT={os.getenv("POSTGRES_PORT", "5432")}
POSTGRES_DB={os.getenv("POSTGRES_DB", "cbsc_production")}
POSTGRES_USER={os.getenv("POSTGRES_USER", "cbsc_admin")}
POSTGRES_PASSWORD={os.getenv("POSTGRES_PASSWORD", "your_password_here")}

# Full connection URL
DATABASE_URL=postgresql://{os.getenv("POSTGRES_USER", "cbsc_admin")}:{os.getenv("POSTGRES_PASSWORD", "your_password_here")}@{os.getenv("POSTGRES_HOST", "localhost")}:{os.getenv("POSTGRES_PORT", "5432")}/{os.getenv("POSTGRES_DB", "cbsc_production")}

# =============================================================================
# Connection Pool Configuration
# =============================================================================
DB_POOL_SIZE={os.getenv("DB_POOL_SIZE", "20")}
DB_MAX_OVERFLOW={os.getenv("DB_MAX_OVERFLOW", "30")}
DB_POOL_TIMEOUT={os.getenv("DB_POOL_TIMEOUT", "30")}
DB_POOL_RECYCLE={os.getenv("DB_POOL_RECYCLE", "3600")}

# =============================================================================
# SQLite Configuration (Fallback for Development)
# =============================================================================
# SQLite database path for development/testing
SQLITE_DB_PATH=./data/cbsc_dev.db
USE_SQLITE_FALLBACK={os.getenv("USE_SQLITE_FALLBACK", "false")}

# =============================================================================
# Database Schema Settings
# =============================================================================
# Auto-migration settings
AUTO_MIGRATE={os.getenv("AUTO_MIGRATE", "true")}
SCHEMA_VERSION={os.getenv("SCHEMA_VERSION", "1.0")}

# =============================================================================
# Database Backups
# =============================================================================
BACKUP_ENABLED={os.getenv("BACKUP_ENABLED", "false")}
BACKUP_SCHEDULE={os.getenv("BACKUP_SCHEDULE", "0 2 * * *")}
BACKUP_PATH={os.getenv("BACKUP_PATH", "./backups")}
BACKUP_RETENTION_DAYS={os.getenv("BACKUP_RETENTION_DAYS", "30")}
"""

    config_file = "database_config.py"

    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(config_content)
        print(f"[OK] Database configuration file created: {config_file}")
        return True

    except Exception as e:
        print(f"[X] Failed to create config file: {e}")
        return False

def main():
    """主测试函数"""
    print("CBSC STRATEGY API - DATABASE CONNECTION SETUP")
    print(f"Started at: {datetime.now().isoformat()}")

    # Test 1: Configuration
    config_ok = test_database_configuration()

    # Test 2: Connectivity (if configuration is ok)
    connectivity_ok = False
    if config_ok:
        connectivity_ok = test_database_connectivity()

    # Test 3: SQLite fallback
    sqlite_ok = test_sqlite_fallback()

    # Test 4: Create config file
    config_file_ok = create_database_config_file()

    # Summary
    print("\n" + "=" * 60)
    print("DATABASE SETUP SUMMARY")
    print("=" * 60)

    print(f"Configuration: {'[OK] PASS' if config_ok else '[X] FAIL'}")
    print(f"PostgreSQL Connectivity: {'[OK] PASS' if connectivity_ok else '[X] FAIL'}")
    print(f"SQLite Fallback: {'[OK] PASS' if sqlite_ok else '[X] FAIL'}")
    print(f"Config File Creation: {'[OK] PASS' if config_file_ok else '[X] FAIL'}")

    # Recommendations
    print("\n[RECOMMENDATIONS]")

    if not config_ok:
        print("1. Complete your environment configuration in .env file")
        print("2. Set all required database variables")

    if not connectivity_ok:
        print("1. Install PostgreSQL server")
        print("   - Windows: Download from postgresql.org")
        print("   - macOS: brew install postgresql")
        print("   - Linux: apt-get install postgresql postgresql-contrib")
        print("2. Start PostgreSQL service")
        print("   - Windows: Start PostgreSQL service in Services")
        print("   - macOS/Linux: brew services start postgresql")
        print("   - Linux (systemd): sudo systemctl start postgresql")
        print("3. Create database:")
        print("   - sudo -u postgres createdb cbsc_production")
        print("   - sudo -u postgres createuser cbsc_admin")
        print("   - sudo -u postgres psql -c \"ALTER USER cbsc_admin PASSWORD 'your_password';\"")

    if connectivity_ok:
        print("[OK] PostgreSQL connection is ready!")
        print("Next step: Run database migration to create schema")
        print("Command: python database_connection.py")

    if not connectivity_ok and sqlite_ok:
        print("[INFO] SQLite fallback is available for development")
        print("Set USE_SQLITE_FALLBACK=true in .env to use SQLite")

    # Overall result
    overall_success = config_ok and (connectivity_ok or sqlite_ok) and config_file_ok
    print(f"\n{'[SUCCESS] DATABASE SETUP: COMPLETE' if overall_success else '[WARNING] DATABASE SETUP: NEEDS ATTENTION'}")

    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)