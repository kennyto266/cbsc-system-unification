#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database Connection Setup
数据库连接设置

PostgreSQL database connection configuration and testing
PostgreSQL数据库连接配置和测试
"""

import os
import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime
import asyncpg  # asyncpg for async PostgreSQL connection

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseConnection:
    """PostgreSQL数据库连接管理器"""

    def __init__(self):
        self.connection = None
        self.config = {
            "host": os.getenv("POSTGRES_HOST", "localhost"),
            "port": os.getenv("POSTGRES_PORT", "5432"),
            "database": os.getenv("POSTGRES_DB", "cbsc_production"),
            "user": os.getenv("POSTGRES_USER", "cbsc_admin"),
            "password": os.getenv("POSTGRES_PASSWORD", ""),
            "min_size": int(os.getenv("DB_POOL_MIN_SIZE", "5")),
            "max_size": int(os.getenv("DB_POOL_SIZE", "20")),
            "command_timeout": int(os.getenv("DB_POOL_TIMEOUT", "30"))
        }

    async def connect(self) -> bool:
        """建立数据库连接"""
        try:
            logger.info("Connecting to PostgreSQL database...")
            logger.info(f"Host: {self.config['host']}, Port: {self.config['port']}")
            logger.info(f"Database: {self.config['database']}, User: {self.config['user']}")

            # Test connection first
            test_conn = await asyncpg.connect(
                host=self.config["host"],
                port=self.config["port"],
                database=self.config["database"],
                user=self.config["user"],
                password=self.config["password"]
            )

            # Test basic query
            result = await test_conn.fetchval("SELECT version()")
            logger.info(f"PostgreSQL version: {result}")
            await test_conn.close()

            logger.info("✅ Database connection successful!")
            return True

        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False

    async def create_pool(self) -> bool:
        """创建连接池"""
        try:
            logger.info("Creating connection pool...")

            self.connection = await asyncpg.create_pool(
                host=self.config["host"],
                port=self.config["port"],
                database=self.config["database"],
                user=self.config["user"],
                password=self.config["password"],
                min_size=self.config["min_size"],
                max_size=self.config["max_size"],
                command_timeout=self.config["command_timeout"]
            )

            logger.info(f"✅ Connection pool created successfully!")
            logger.info(f"Pool size: {self.config['min_size']} - {self.config['max_size']}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to create connection pool: {e}")
            return False

    async def close(self):
        """关闭数据库连接"""
        if self.connection:
            await self.connection.close()
            logger.info("Database connection closed")

    async def test_query(self) -> Dict[str, Any]:
        """测试数据库查询"""
        try:
            if not self.connection:
                return {"error": "Database not connected"}

            async with self.connection.acquire() as conn:
                # Test basic query
                result = await conn.fetchrow(
                    "SELECT version() as version, now() as current_time"
                )

                # Test table existence
                tables = await conn.fetch(
                    """
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                    LIMIT 10
                """
                )

                return {
                    "status": "connected",
                    "postgresql_version": str(result["version"]),
                    "current_time": str(result["current_time"]),
                    "tables_count": len(tables),
                    "tables": [table["table_name"] for table in tables]
                }

        except Exception as e:
            logger.error(f"❌ Test query failed: {e}")
            return {"error": str(e)}

class DatabaseSchemaManager:
    """数据库架构管理器"""

    def __init__(self, db_connection: DatabaseConnection):
        self.db = db_connection

    async def initialize_schema(self) -> bool:
        """初始化数据库架构"""
        try:
            logger.info("Initializing database schema...")

            if not self.db.connection:
                return False

            async with self.db.connection.acquire() as conn:
                # Create extensions
                await self._create_extensions(conn)

                # Create tables
                await self._create_tables(conn)

                # Create indexes
                await self._create_indexes(conn)

                # Insert initial data
                await self._insert_initial_data(conn)

            logger.info("✅ Database schema initialized successfully!")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize schema: {e}")
            return False

    async def _create_extensions(self, conn):
        """创建PostgreSQL扩展"""
        extensions = [
            "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"",
            "CREATE EXTENSION IF NOT EXISTS \"pg_trgm\"",
            "CREATE EXTENSION IF NOT EXISTS \"btree_gin\""
        ]

        for ext in extensions:
            await conn.execute(ext)
            logger.info(f"Created extension: {ext}")

    async def _create_tables(self, conn):
        """创建数据表"""

        # Users table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                is_admin BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)

        # Strategies table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS strategies (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                strategy_type VARCHAR(50) NOT NULL,
                status VARCHAR(20) DEFAULT 'inactive',
                risk_level VARCHAR(20) DEFAULT 'medium',
                parameters JSONB DEFAULT '{}',
                is_active BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                created_by INTEGER REFERENCES users(id)
            )
        """)

        # Strategy executions table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS strategy_executions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                strategy_id UUID REFERENCES strategies(id) ON DELETE CASCADE,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                status VARCHAR(20) DEFAULT 'pending',
                start_time TIMESTAMP WITH TIME ZONE,
                end_time TIMESTAMP WITH TIME ZONE,
                parameters JSONB DEFAULT '{}',
                signals_generated INTEGER DEFAULT 0,
                return_rate DECIMAL(10, 6) DEFAULT 0,
                performance_data JSONB DEFAULT '{}',
                error_message TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)

        # Strategy signals table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS strategy_signals (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                execution_id UUID REFERENCES strategy_executions(id) ON DELETE CASCADE,
                strategy_id UUID REFERENCES strategies(id) ON DELETE CASCADE,
                signal_type VARCHAR(20) NOT NULL,
                price DECIMAL(15, 8),
                quantity DECIMAL(15, 8),
                confidence DECIMAL(5, 4),
                timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                metadata JSONB DEFAULT '{}'
            )
        """)

        # Strategy templates table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS strategy_templates (
                id VARCHAR(50) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                strategy_type VARCHAR(50) NOT NULL,
                default_parameters JSONB DEFAULT '{}',
                risk_level VARCHAR(20) DEFAULT 'medium',
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)

        logger.info("Created all database tables")

    async def _create_indexes(self, conn):
        """创建索引"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_strategies_user_id ON strategies(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_strategies_status ON strategies(status)",
            "CREATE INDEX IF NOT EXISTS idx_strategies_type ON strategies(strategy_type)",
            "CREATE INDEX IF NOT EXISTS idx_executions_strategy_id ON strategy_executions(strategy_id)",
            "CREATE INDEX IF NOT EXISTS idx_executions_status ON strategy_executions(status)",
            "CREATE INDEX IF NOT EXISTS idx_signals_execution_id ON strategy_signals(execution_id)",
            "CREATE INDEX IF NOT EXISTS idx_signals_timestamp ON strategy_signals(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
            "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)"
        ]

        for index in indexes:
            await conn.execute(index)
            logger.info(f"Created index: {index}")

    async def _insert_initial_data(self, conn):
        """插入初始数据"""
        # Insert strategy templates
        templates = [
            {
                "id": "ma_cross",
                "name": "移动平均线交叉策略",
                "description": "基于短期和长期移动平均线交叉的买卖信号策略",
                "strategy_type": "technical",
                "default_parameters": {"short_period": 10, "long_period": 20, "symbol": "BTC/USDT"},
                "risk_level": "medium"
            },
            {
                "id": "rsi_oversold",
                "name": "RSI超卖反弹策略",
                "description": "基于RSI指标的超卖反弹买入策略",
                "strategy_type": "technical",
                "default_parameters": {"rsi_period": 14, "oversold_threshold": 30, "overbought_threshold": 70, "symbol": "ETH/USDT"},
                "risk_level": "high"
            },
            {
                "id": "grid_trading",
                "name": "网格交易策略",
                "description": "在价格区间内自动低买高卖的网格策略",
                "strategy_type": "quantitative",
                "default_parameters": {"grid_count": 20, "price_range": "0.9-1.1", "base_amount": 100, "symbol": "BNB/USDT"},
                "risk_level": "low"
            }
        ]

        for template in templates:
            await conn.execute("""
                INSERT INTO strategy_templates
                (id, name, description, strategy_type, default_parameters, risk_level)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (id) DO NOTHING
            """, template.values())

        logger.info(f"Inserted {len(templates)} strategy templates")

async def main():
    """主函数 - 测试数据库连接"""
    print("=" * 70)
    print("CBSC DATABASE CONNECTION SETUP")
    print("=" * 70)

    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()

    # Check configuration
    if not os.getenv("POSTGRES_PASSWORD"):
        print("❌ POSTGRES_PASSWORD not found in environment variables")
        print("Please check your .env file")
        return

    # Create database connection
    db = DatabaseConnection()

    # Test connection
    if not await db.connect():
        print("❌ Database connection failed. Please check:")
        print("  - PostgreSQL server is running")
        print("  - Connection details are correct in .env file")
        print("  - Database exists")
        return

    # Create connection pool
    if not await db.create_pool():
        print("❌ Failed to create connection pool")
        return

    # Test queries
    test_result = await db.test_query()
    if "error" in test_result:
        print(f"❌ Database test failed: {test_result['error']}")
        return

    print("✅ Database test results:")
    print(f"  PostgreSQL Version: {test_result['postgresql_version']}")
    print(f"  Current Time: {test_result['current_time']}")
    print(f"  Tables Found: {test_result['tables_count']}")
    if test_result['tables']:
        print(f"  Available Tables: {', '.join(test_result['tables'][:5])}")
        if len(test_result['tables']) > 5:
            print(f"    and {len(test_result['tables']) - 5} more...")

    # Initialize schema
    schema_manager = DatabaseSchemaManager(db)
    if await schema_manager.initialize_schema():
        print("✅ Database setup completed successfully!")
        print()
        print("🎉 PostgreSQL database is now ready for CBSC Strategy API!")
    else:
        print("❌ Database schema initialization failed")

    # Cleanup
    await db.close()

if __name__ == "__main__":
    asyncio.run(main())