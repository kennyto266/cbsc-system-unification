#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unified Strategy Tables Migration
統一策略表遷移腳本
Phase 3.2 - 策略表結構統一

This script migrates and unifies the strategy management tables,
integrating the core CBSC strategy management APIs with the
unified strategy service.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import os
import sys
from pathlib import Path
from uuid import uuid4

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text, inspect, MetaData, Table, Column, String, Boolean
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class UnifiedStrategyMigration:
    """
    Migrates and unifies strategy management tables.
    遷移並統一策略管理表。
    """

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = None
        self.async_session = None
        self.metadata = MetaData()

    async def connect(self) -> bool:
        """Connect to database"""
        try:
            self.engine = create_async_engine(
                self.database_url,
                echo=False,
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10
            )

            self.async_session = sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )

            # Test connection
            async with self.engine.begin() as conn:
                await conn.execute(text("SELECT 1"))

            logger.info("✅ Successfully connected to database")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to connect to database: {e}")
            return False

    async def check_existing_tables(self) -> List[str]:
        """Check which tables already exist"""
        try:
            async with self.engine.begin() as conn:
                result = await conn.execute(text("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name IN (
                        'strategies',
                        'strategy_versions',
                        'strategy_instances',
                        'strategy_performance',
                        'backtests',
                        'trades',
                        'strategy_categories'
                    )
                    ORDER BY table_name
                """))
                existing = [row[0] for row in result.fetchall()]
                logger.info(f"Found existing tables: {existing}")
                return existing

        except Exception as e:
            logger.error(f"❌ Error checking existing tables: {e}")
            return []

    async def create_strategy_categories_table(self) -> bool:
        """Create strategy_categories table if not exists"""
        try:
            async with self.engine.begin() as conn:
                await conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS strategy_categories (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        name VARCHAR(100) UNIQUE NOT NULL,
                        description TEXT,
                        parent_id UUID REFERENCES strategy_categories(id),
                        icon VARCHAR(50),
                        color VARCHAR(7),
                        sort_order INTEGER DEFAULT 0,
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    );

                    CREATE INDEX IF NOT EXISTS idx_category_parent ON strategy_categories(parent_id);
                    CREATE INDEX IF NOT EXISTS idx_category_active ON strategy_categories(is_active);

                    COMMENT ON TABLE strategy_categories IS 'Strategy categorization and classification';
                """))
                logger.info("✅ Created strategy_categories table")
                return True

        except Exception as e:
            logger.error(f"❌ Failed to create strategy_categories table: {e}")
            return False

    async def create_strategies_table(self) -> bool:
        """Create or update strategies table"""
        try:
            async with self.engine.begin() as conn:
                # Check if column exists, if not add it
                await conn.execute(text("""
                    -- Add new columns to strategies table if they don't exist
                    DO $$
                    BEGIN
                        -- Add slug column if not exists
                        IF NOT EXISTS (
                            SELECT 1 FROM information_schema.columns
                            WHERE table_name = 'strategies' AND column_name = 'slug'
                        ) THEN
                            ALTER TABLE strategies ADD COLUMN slug VARCHAR(200) UNIQUE NOT NULL DEFAULT '';
                        END IF;

                        -- Add category_id if not exists
                        IF NOT EXISTS (
                            SELECT 1 FROM information_schema.columns
                            WHERE table_name = 'strategies' AND column_name = 'category_id'
                        ) THEN
                            ALTER TABLE strategies ADD COLUMN category_id UUID REFERENCES strategy_categories(id);
                        END IF;

                        -- Add tags array if not exists
                        IF NOT EXISTS (
                            SELECT 1 FROM information_schema.columns
                            WHERE table_name = 'strategies' AND column_name = 'tags'
                        ) THEN
                            ALTER TABLE strategies ADD COLUMN tags TEXT[] DEFAULT '{}';
                        END IF;

                        -- Add is_template if not exists
                        IF NOT EXISTS (
                            SELECT 1 FROM information_schema.columns
                            WHERE table_name = 'strategies' AND column_name = 'is_template'
                        ) THEN
                            ALTER TABLE strategies ADD COLUMN is_template BOOLEAN DEFAULT FALSE;
                        END IF;

                        -- Add featured if not exists
                        IF NOT EXISTS (
                            SELECT 1 FROM information_schema.columns
                            WHERE table_name = 'strategies' AND column_name = 'featured'
                        ) THEN
                            ALTER TABLE strategies ADD COLUMN featured BOOLEAN DEFAULT FALSE;
                        END IF;

                        -- Add usage tracking columns if not exists
                        IF NOT EXISTS (
                            SELECT 1 FROM information_schema.columns
                            WHERE table_name = 'strategies' AND column_name = 'usage_count'
                        ) THEN
                            ALTER TABLE strategies ADD COLUMN usage_count INTEGER DEFAULT 0;
                            ALTER TABLE strategies ADD COLUMN rating FLOAT DEFAULT 0;
                            ALTER TABLE strategies ADD COLUMN rating_count INTEGER DEFAULT 0;
                        END IF;

                        -- Add timeframes and symbols arrays if not exists
                        IF NOT EXISTS (
                            SELECT 1 FROM information_schema.columns
                            WHERE table_name = 'strategies' AND column_name = 'timeframes'
                        ) THEN
                            ALTER TABLE strategies ADD COLUMN timeframes TEXT[] DEFAULT '{}';
                            ALTER TABLE strategies ADD COLUMN symbols TEXT[] DEFAULT '{}';
                            ALTER TABLE strategies ADD COLUMN exchanges TEXT[] DEFAULT '{}';
                            ALTER TABLE strategies ADD COLUMN min_capital FLOAT;
                        END IF;

                        -- Add last_used_at if not exists
                        IF NOT EXISTS (
                            SELECT 1 FROM information_schema.columns
                            WHERE table_name = 'strategies' AND column_name = 'last_used_at'
                        ) THEN
                            ALTER TABLE strategies ADD COLUMN last_used_at TIMESTAMP WITH TIME ZONE;
                        END IF;
                    END $$;

                    -- Create indexes
                    CREATE INDEX IF NOT EXISTS idx_strategy_type ON strategies(strategy_type);
                    CREATE INDEX IF NOT EXISTS idx_strategy_status ON strategies(status);
                    CREATE INDEX IF NOT EXISTS idx_strategy_category ON strategies(category_id);
                    CREATE INDEX IF NOT EXISTS idx_strategy_public ON strategies(is_public);
                    CREATE INDEX IF NOT EXISTS idx_strategy_featured ON strategies(featured);
                    CREATE INDEX IF NOT EXISTS idx_strategy_created ON strategies(created_at);
                    CREATE INDEX IF NOT EXISTS idx_strategy_tags ON strategies USING GIN(tags);

                    COMMENT ON TABLE strategies IS 'Unified strategy table with all CBSC strategy types';
                """))
                logger.info("✅ Updated strategies table with unified schema")
                return True

        except Exception as e:
            logger.error(f"❌ Failed to update strategies table: {e}")
            return False

    async def create_strategy_versions_table(self) -> bool:
        """Create or update strategy_versions table"""
        try:
            async with self.engine.begin() as conn:
                await conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS strategy_versions (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        strategy_id UUID NOT NULL REFERENCES strategies(id) ON DELETE CASCADE,
                        version VARCHAR(20) NOT NULL,
                        changelog TEXT,
                        config JSONB NOT NULL,
                        parameters JSONB,
                        created_by UUID REFERENCES users(id),
                        is_major BOOLEAN DEFAULT FALSE,
                        is_stable BOOLEAN DEFAULT FALSE,
                        benchmark_data JSONB,
                        test_results JSONB,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        UNIQUE(strategy_id, version)
                    );

                    CREATE INDEX IF NOT EXISTS idx_version_strategy ON strategy_versions(strategy_id);
                    CREATE INDEX IF NOT EXISTS idx_version_created ON strategy_versions(created_at);

                    COMMENT ON TABLE strategy_versions IS 'Strategy version history and change tracking';
                """))
                logger.info("✅ Created strategy_versions table")
                return True

        except Exception as e:
            logger.error(f"❌ Failed to create strategy_versions table: {e}")
            return False

    async def create_strategy_instances_table(self) -> bool:
        """Create or update strategy_instances table"""
        try:
            async with self.engine.begin() as conn:
                await conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS strategy_instances (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        strategy_id UUID NOT NULL REFERENCES strategies(id) ON DELETE CASCADE,
                        user_id UUID NOT NULL REFERENCES users(id),
                        name VARCHAR(200) NOT NULL,
                        parameters JSONB,
                        symbols TEXT[],
                        capital_allocation FLOAT,
                        position_sizing JSONB,
                        status VARCHAR(20) DEFAULT 'stopped',
                        last_signal JSONB,
                        current_positions JSONB,
                        start_equity FLOAT,
                        current_equity FLOAT,
                        total_return FLOAT,
                        daily_return FLOAT,
                        risk_settings JSONB,
                        current_drawdown FLOAT,
                        var_95 FLOAT,
                        is_paper_trading BOOLEAN DEFAULT TRUE,
                        auto_trade BOOLEAN DEFAULT FALSE,
                        signal_notifications JSONB,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        started_at TIMESTAMP WITH TIME ZONE,
                        stopped_at TIMESTAMP WITH TIME ZONE,
                        last_signal_at TIMESTAMP WITH TIME ZONE,
                        CHECK(capital_allocation > 0)
                    );

                    CREATE INDEX IF NOT EXISTS idx_instance_strategy ON strategy_instances(strategy_id);
                    CREATE INDEX IF NOT EXISTS idx_instance_user ON strategy_instances(user_id);
                    CREATE INDEX IF NOT EXISTS idx_instance_status ON strategy_instances(status);
                    CREATE INDEX IF NOT EXISTS idx_instance_active ON strategy_instances(is_paper_trading, auto_trade);

                    COMMENT ON TABLE strategy_instances IS 'Running strategy instances with real-time data';
                """))
                logger.info("✅ Created strategy_instances table")
                return True

        except Exception as e:
            logger.error(f"❌ Failed to create strategy_instances table: {e}")
            return False

    async def create_strategy_performance_table(self) -> bool:
        """Create or update strategy_performance table"""
        try:
            async with self.engine.begin() as conn:
                await conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS strategy_performance (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        strategy_id UUID NOT NULL REFERENCES strategies(id) ON DELETE CASCADE,
                        date TIMESTAMP WITH TIME ZONE NOT NULL,
                        daily_return FLOAT,
                        cumulative_return FLOAT,
                        annualized_return FLOAT,
                        volatility FLOAT,
                        max_drawdown FLOAT,
                        current_drawdown FLOAT,
                        sharpe_ratio FLOAT,
                        sortino_ratio FLOAT,
                        calmar_ratio FLOAT,
                        benchmark_return FLOAT,
                        alpha FLOAT,
                        beta FLOAT,
                        tracking_error FLOAT,
                        win_rate FLOAT,
                        profit_factor FLOAT,
                        avg_trade_return FLOAT,
                        trade_count INTEGER,
                        equity FLOAT,
                        exposure FLOAT,
                        leverage FLOAT,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        UNIQUE(strategy_id, date)
                    );

                    CREATE INDEX IF NOT EXISTS idx_performance_strategy ON strategy_performance(strategy_id);
                    CREATE INDEX IF NOT EXISTS idx_performance_date ON strategy_performance(date);
                    CREATE INDEX IF NOT EXISTS idx_performance_returns ON strategy_performance(daily_return, cumulative_return);

                    COMMENT ON TABLE strategy_performance IS 'Historical performance tracking and analytics';
                """))
                logger.info("✅ Created strategy_performance table")
                return True

        except Exception as e:
            logger.error(f"❌ Failed to create strategy_performance table: {e}")
            return False

    async def create_backtests_table(self) -> bool:
        """Create or update backtests table"""
        try:
            async with self.engine.begin() as conn:
                await conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS backtests (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        strategy_id UUID NOT NULL REFERENCES strategies(id) ON DELETE CASCADE,
                        user_id UUID NOT NULL REFERENCES users(id),
                        name VARCHAR(200) NOT NULL,
                        parameters JSONB,
                        symbols TEXT[],
                        start_date TIMESTAMP WITH TIME ZONE NOT NULL,
                        end_date TIMESTAMP WITH TIME ZONE NOT NULL,
                        initial_capital FLOAT DEFAULT 100000,
                        final_equity FLOAT,
                        total_return FLOAT,
                        annualized_return FLOAT,
                        max_drawdown FLOAT,
                        volatility FLOAT,
                        var_95 FLOAT,
                        expected_shortfall FLOAT,
                        sharpe_ratio FLOAT,
                        sortino_ratio FLOAT,
                        calmar_ratio FLOAT,
                        total_trades INTEGER,
                        winning_trades INTEGER,
                        losing_trades INTEGER,
                        win_rate FLOAT,
                        avg_win FLOAT,
                        avg_loss FLOAT,
                        profit_factor FLOAT,
                        benchmark_return FLOAT,
                        alpha FLOAT,
                        beta FLOAT,
                        information_ratio FLOAT,
                        equity_curve JSONB,
                        trade_history JSONB,
                        monthly_returns JSONB,
                        rolling_metrics JSONB,
                        status VARCHAR(20) DEFAULT 'completed',
                        error_message TEXT,
                        computation_time FLOAT,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        CHECK(initial_capital > 0),
                        CHECK(win_rate >= 0 AND win_rate <= 100)
                    );

                    CREATE INDEX IF NOT EXISTS idx_backtest_strategy ON backtests(strategy_id);
                    CREATE INDEX IF NOT EXISTS idx_backtest_user ON backtests(user_id);
                    CREATE INDEX IF NOT EXISTS idx_backtest_dates ON backtests(start_date, end_date);
                    CREATE INDEX IF NOT EXISTS idx_backtest_performance ON backtests(total_return, sharpe_ratio);

                    COMMENT ON TABLE backtests IS 'Backtest results and historical simulation data';
                """))
                logger.info("✅ Created backtests table")
                return True

        except Exception as e:
            logger.error(f"❌ Failed to create backtests table: {e}")
            return False

    async def create_trades_table(self) -> bool:
        """Create or update trades table"""
        try:
            async with self.engine.begin() as conn:
                await conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS trades (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        instance_id UUID NOT NULL REFERENCES strategy_instances(id) ON DELETE CASCADE,
                        backtest_id UUID REFERENCES backtests(id),
                        symbol VARCHAR(20) NOT NULL,
                        direction VARCHAR(10) NOT NULL,
                        quantity FLOAT NOT NULL,
                        entry_price FLOAT NOT NULL,
                        exit_price FLOAT,
                        entry_time TIMESTAMP WITH TIME ZONE NOT NULL,
                        exit_time TIMESTAMP WITH TIME ZONE,
                        duration INTEGER,
                        entry_value FLOAT,
                        exit_value FLOAT,
                        gross_pnl FLOAT,
                        fees FLOAT DEFAULT 0,
                        net_pnl FLOAT,
                        return_pct FLOAT,
                        exit_reason VARCHAR(50),
                        signal_confidence FLOAT,
                        strategy_notes TEXT,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        CHECK(quantity > 0),
                        CHECK(entry_price > 0)
                    );

                    CREATE INDEX IF NOT EXISTS idx_trade_instance ON trades(instance_id);
                    CREATE INDEX IF NOT EXISTS idx_trade_backtest ON trades(backtest_id);
                    CREATE INDEX IF NOT EXISTS idx_trade_symbol ON trades(symbol);
                    CREATE INDEX IF NOT EXISTS idx_trade_times ON trades(entry_time, exit_time);

                    COMMENT ON TABLE trades IS 'Individual trade records for live trading and backtests';
                """))
                logger.info("✅ Created trades table")
                return True

        except Exception as e:
            logger.error(f"❌ Failed to create trades table: {e}")
            return False

    async def insert_default_categories(self) -> bool:
        """Insert default strategy categories"""
        try:
            async with self.engine.begin() as conn:
                # Check if categories already exist
                result = await conn.execute(text(
                    "SELECT COUNT(*) FROM strategy_categories"
                ))
                count = result.scalar()

                if count > 0:
                    logger.info("⏭️  Strategy categories already exist, skipping")
                    return True

                # Insert default categories
                await conn.execute(text("""
                    INSERT INTO strategy_categories (name, description, icon, color, sort_order) VALUES
                    ('Technical Analysis', 'Strategies based on technical indicators and chart patterns', 'trending-up', '#3B82F6', 1),
                    ('Momentum', 'Strategies that capture market momentum and trends', 'zap', '#F59E0B', 2),
                    ('Volume', 'Volume-based trading strategies', 'bar-chart', '#10B981', 3),
                    ('Portfolio', 'Multi-asset portfolio management strategies', 'pie-chart', '#8B5CF6', 4),
                    ('Fundamental', 'Fundamental analysis-based strategies', 'file-text', '#EF4444', 5),
                    ('Combination', 'Hybrid strategies combining multiple approaches', 'layers', '#EC4899', 6),
                    ('Machine Learning', 'AI and ML-based strategies', 'cpu', '#6366F1', 7);
                """))
                logger.info("✅ Inserted default strategy categories")
                return True

        except Exception as e:
            logger.error(f"❌ Failed to insert default categories: {e}")
            return False

    async def verify_migration(self) -> bool:
        """Verify that all tables are created correctly"""
        try:
            async with self.engine.begin() as conn:
                # Check all required tables
                required_tables = [
                    'strategies',
                    'strategy_versions',
                    'strategy_instances',
                    'strategy_performance',
                    'backtests',
                    'trades',
                    'strategy_categories'
                ]

                result = await conn.execute(text("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = ANY(:tables)
                """), {"tables": required_tables})

                existing = {row[0] for row in result.fetchall()}
                missing = set(required_tables) - existing

                if missing:
                    logger.error(f"❌ Missing tables after migration: {missing}")
                    return False

                # Verify indexes
                result = await conn.execute(text("""
                    SELECT COUNT(DISTINCT indexname)
                    FROM pg_indexes
                    WHERE tablename = ANY(:tables)
                """), {"tables": required_tables})

                index_count = result.scalar()
                logger.info(f"✅ Created {index_count} indexes across all tables")

                # Verify foreign keys
                result = await conn.execute(text("""
                    SELECT COUNT(*)
                    FROM information_schema.table_constraints
                    WHERE constraint_type = 'FOREIGN KEY'
                    AND table_name = ANY(:tables)
                """), {"tables": required_tables})

                fk_count = result.scalar()
                logger.info(f"✅ Created {fk_count} foreign key constraints")

                logger.info("✅ All tables verified successfully")
                return True

        except Exception as e:
            logger.error(f"❌ Verification failed: {e}")
            return False

    async def run_migration(self) -> bool:
        """Run the complete migration process"""
        logger.info("Starting unified strategy tables migration...")

        # Connect to database
        if not await self.connect():
            return False

        # Check existing tables
        existing = await self.check_existing_tables()

        # Run migration steps
        success = True

        # Create tables in order
        success &= await self.create_strategy_categories_table()
        success &= await self.create_strategies_table()
        success &= await self.create_strategy_versions_table()
        success &= await self.create_strategy_instances_table()
        success &= await self.create_strategy_performance_table()
        success &= await self.create_backtests_table()
        success &= await self.create_trades_table()

        # Insert default data
        success &= await self.insert_default_categories()

        # Verify migration
        if success:
            success = await self.verify_migration()

        if success:
            logger.info("✅ Unified strategy tables migration completed successfully!")
        else:
            logger.error("❌ Unified strategy tables migration failed!")

        return success

    async def close(self):
        """Close database connection"""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connection closed")


async def main():
    """Main migration function"""
    # Load environment variables
    load_dotenv()

    # Get database URL
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://cbsc:cbsc_password@localhost:5432/cbsc_db"
    )

    # Create and run migration
    migration = UnifiedStrategyMigration(database_url=database_url)

    try:
        success = await migration.run_migration()
        return success
    finally:
        await migration.close()


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
