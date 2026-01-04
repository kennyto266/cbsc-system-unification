#!/usr/bin/env python3
"""
Create base tables directly using Python
直接使用Python創建基礎表
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

import psycopg2
from psycopg2.extras import DictCursor

def create_base_tables():
    """Create base tables directly"""

    # Database connection parameters from docker-compose.yml
    db_url = "postgresql://cbsc_user:cbsc_password@localhost:5432/cbsc_strategy"

    print("Creating base tables directly...")

    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()

        # Enable UUID extension
        try:
            cursor.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";")
            print("UUID extension enabled")
        except Exception as e:
            print(f"UUID extension error (may already exist): {e}")

        # Create users table
        users_sql = """
        CREATE TABLE IF NOT EXISTS users (
            id VARCHAR(36) PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            display_name VARCHAR(100),
            is_active BOOLEAN DEFAULT TRUE NOT NULL,
            email_verified BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
        );
        """
        cursor.execute(users_sql)
        print("Users table created")

        # Create strategies table
        strategies_sql = """
        CREATE TABLE IF NOT EXISTS strategies (
            id VARCHAR(36) PRIMARY KEY,
            name VARCHAR(200) NOT NULL,
            code VARCHAR(100) UNIQUE NOT NULL,
            description TEXT,
            strategy_type VARCHAR(50) NOT NULL,
            version VARCHAR(20) DEFAULT '1.0.0' NOT NULL,
            is_active BOOLEAN DEFAULT TRUE NOT NULL,
            is_system BOOLEAN DEFAULT FALSE NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
            is_deleted BOOLEAN DEFAULT FALSE NOT NULL
        );
        """
        cursor.execute(strategies_sql)
        print("Strategies table created")

        # Create strategy_categories table
        categories_sql = """
        CREATE TABLE IF NOT EXISTS strategy_categories (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) UNIQUE NOT NULL,
            display_name VARCHAR(200) NOT NULL,
            description TEXT,
            level INTEGER DEFAULT 1 NOT NULL,
            is_active BOOLEAN DEFAULT TRUE NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
        );
        """
        cursor.execute(categories_sql)
        print("Strategy categories table created")

        # Insert default categories
        insert_categories = """
        INSERT INTO strategy_categories (name, display_name, description, level) VALUES
            ('technical_indicators', 'Technical Indicators', 'Strategies based on technical analysis indicators', 1),
            ('momentum', 'Momentum Strategies', 'Strategies that exploit market momentum', 1),
            ('mean_reversion', 'Mean Reversion', 'Strategies that bet on price reversion to mean', 1)
        ON CONFLICT (name) DO NOTHING;
        """
        cursor.execute(insert_categories)
        print("Default categories inserted")

        # Create indexes
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);",
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);",
            "CREATE INDEX IF NOT EXISTS idx_strategies_code ON strategies(code);",
            "CREATE INDEX IF NOT EXISTS idx_strategies_type ON strategies(strategy_type);",
            "CREATE INDEX IF NOT EXISTS idx_strategies_active ON strategies(is_active, is_deleted);"
        ]

        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
            except Exception:
                pass  # Index may already exist

        print("Indexes created")

        # Insert sample data
        sample_user = """
        INSERT INTO users (id, username, email, password_hash, display_name)
        VALUES ('admin-001', 'admin', 'admin@cbsc.com', 'hashed_password', 'System Administrator')
        ON CONFLICT (id) DO NOTHING;
        """
        cursor.execute(sample_user)
        print("Sample user inserted")

        sample_strategy = """
        INSERT INTO strategies (id, name, code, description, strategy_type)
        VALUES ('strategy-001', 'MA Crossover', 'ma_crossover', 'Moving Average Crossover Strategy', 'technical_indicators')
        ON CONFLICT (id) DO NOTHING;
        """
        cursor.execute(sample_strategy)
        print("Sample strategy inserted")

        conn.commit()
        print("Base tables created successfully!")

        cursor.close()
        conn.close()

        return True

    except Exception as e:
        print(f"Error creating base tables: {e}")
        return False

if __name__ == "__main__":
    success = create_base_tables()
    print(f"Base tables creation: {success}")

    if success:
        print("Ready to execute 003_strategy_management_tables migration.")
    else:
        print("Failed to create base tables!")