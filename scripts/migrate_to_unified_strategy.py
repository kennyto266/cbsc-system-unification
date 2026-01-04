#!/usr/bin/env python3
"""
Unified Strategy Migration Script
統一策略遷移腳本

Migrates data from multiple strategy tables to unified strategy schema.
整合三個策略管理器的數據遷移腳本

Usage:
    python scripts/migrate_to_unified_strategy.py --dry-run
    python scripts/migrate_to_unified_strategy.py --execute
"""

import asyncio
import argparse
import json
import logging
from datetime import datetime
from typing import Dict, List, Any
from uuid import uuid4

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class UnifiedStrategyMigration:
    """
    Unified Strategy Migration Service
    統一策略遷移服務

    Migrates data from:
    - strategies (legacy table)
    - cbsc_strategies (CBSC specific)
    - personal_strategies (user personalizations)

    To:
    - unified_strategies (new unified table)
    """

    def __init__(self, database_url: str, dry_run: bool = True):
        """
        Initialize migration service

        Args:
            database_url: Database connection URL
            dry_run: If True, don't actually modify data
        """
        self.database_url = database_url
        self.dry_run = dry_run
        self.engine = create_async_engine(database_url, echo=False)
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

        # Statistics tracking
        self.stats = {
            "strategies_migrated": 0,
            "cbsc_strategies_migrated": 0,
            "personal_strategies_migrated": 0,
            "errors": [],
            "start_time": None,
            "end_time": None
        }

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - cleanup"""
        await self.engine.dispose()

    async def run_migration(self):
        """
        Execute the complete migration process
        """
        self.stats["start_time"] = datetime.utcnow()

        logger.info("=" * 60)
        logger.info("Unified Strategy Migration Started")
        logger.info("=" * 60)
        logger.info(f"Mode: {'DRY RUN' if self.dry_run else 'EXECUTE'}")
        logger.info(f"Database: {self.database_url}")
        logger.info("")

        async with self.async_session() as session:
            # Phase 1: Check and create unified_strategies table
            await self._ensure_unified_table_exists(session)

            # Phase 2: Migrate legacy strategies
            await self._migrate_legacy_strategies(session)

            # Phase 3: Migrate CBSC strategies
            await self._migrate_cbsc_strategies(session)

            # Phase 4: Migrate personal strategies
            await self._migrate_personal_strategies(session)

            # Phase 5: Verify and report
            await self._verify_migration(session)

        self.stats["end_time"] = datetime.utcnow()

        # Print summary
        self._print_summary()

    async def _ensure_unified_table_exists(self, session: AsyncSession):
        """
        Check if unified_strategies table exists, create if needed
        """
        logger.info("Phase 1: Checking unified_strategies table...")

        try:
            # Check if table exists
            from sqlalchemy import text
            result = await session.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'unified_strategies'
                );
            """))
            exists = result.scalar()

            if not exists:
                logger.warning("unified_strategies table does not exist")
                logger.info("Creating unified_strategies table...")

                if not self.dry_run:
                    await session.execute(text("""
                        CREATE TABLE unified_strategies (
                            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                            user_id INTEGER NOT NULL REFERENCES users(id),
                            name VARCHAR(255) NOT NULL,
                            description TEXT,
                            strategy_type VARCHAR(50) NOT NULL DEFAULT 'momentum',
                            status VARCHAR(50) NOT NULL DEFAULT 'draft',
                            config JSONB NOT NULL DEFAULT '{}',
                            metadata JSONB DEFAULT '{}',
                            is_public BOOLEAN DEFAULT FALSE,
                            is_template BOOLEAN DEFAULT FALSE,
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                            version INTEGER DEFAULT 1
                        );

                        CREATE INDEX idx_unified_strategies_user_id ON unified_strategies(user_id);
                        CREATE INDEX idx_unified_strategies_type ON unified_strategies(strategy_type);
                        CREATE INDEX idx_unified_strategies_status ON unified_strategies(status);
                    """))
                    await session.commit()

                logger.info("✓ Created unified_strategies table")
            else:
                logger.info("✓ unified_strategies table exists")

        except Exception as e:
            logger.error(f"Failed to ensure table exists: {e}")
            self.stats["errors"].append(str(e))
            raise

    async def _migrate_legacy_strategies(self, session: AsyncSession):
        """
        Migrate data from legacy strategies table
        """
        logger.info("Phase 2: Migrating legacy strategies...")

        try:
            from sqlalchemy import text
            result = await session.execute(text("""
                SELECT COUNT(*) FROM strategies;
            """))
            count = result.scalar()

            if count == 0:
                logger.info("No legacy strategies found")
                return

            logger.info(f"Found {count} legacy strategies")

            # Get all legacy strategies
            result = await session.execute(text("""
                SELECT
                    id, user_id, name, description, strategy_type,
                    status, parameters, risk_level, is_active,
                    created_at, updated_at
                FROM strategies
                ORDER BY created_at;
            """))
            strategies = result.fetchall()

            for strategy in strategies:
                try:
                    strategy_dict = {
                        "id": str(strategy[0]),
                        "user_id": strategy[1],
                        "name": strategy[2],
                        "description": strategy[3],
                        "strategy_type": strategy[4] or "momentum",
                        "status": strategy[5] or "draft",
                        "config": json.loads(strategy[6]) if strategy[6] else {},
                        "metadata": {
                            "risk_level": strategy[7],
                            "is_active": strategy[8],
                            "source": "legacy_strategies"
                        },
                        "created_at": strategy[9],
                        "updated_at": strategy[10]
                    }

                    if not self.dry_run:
                        await session.execute(text("""
                            INSERT INTO unified_strategies (
                                id, user_id, name, description, strategy_type,
                                status, config, metadata, created_at, updated_at
                            ) VALUES (
                                :id, :user_id, :name, :description, :strategy_type,
                                :status, :config, :metadata, :created_at, :updated_at
                            )
                            ON CONFLICT (id) DO NOTHING;
                        """), strategy_dict)

                    self.stats["strategies_migrated"] += 1
                    logger.debug(f"Migrated strategy: {strategy_dict['name']}")

                except Exception as e:
                    logger.error(f"Failed to migrate strategy {strategy[0]}: {e}")
                    self.stats["errors"].append(str(e))

            if not self.dry_run:
                await session.commit()

            logger.info(f"✓ Migrated {self.stats['strategies_migrated']} legacy strategies")

        except Exception as e:
            logger.error(f"Failed to migrate legacy strategies: {e}")
            self.stats["errors"].append(str(e))

    async def _migrate_cbsc_strategies(self, session: AsyncSession):
        """
        Migrate data from cbsc_strategies table
        """
        logger.info("Phase 3: Migrating CBSC strategies...")

        try:
            from sqlalchemy import text
            result = await session.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'cbsc_strategies'
                );
            """))
            exists = result.scalar()

            if not exists:
                logger.info("cbsc_strategies table does not exist, skipping")
                return

            # Get count
            result = await session.execute(text("""
                SELECT COUNT(*) FROM cbsc_strategies;
            """))
            count = result.scalar()

            if count == 0:
                logger.info("No CBSC strategies found")
                return

            logger.info(f"Found {count} CBSC strategies")

            # Get all CBSC strategies
            result = await session.execute(text("""
                SELECT
                    id, user_id, name, description, strategy_type,
                    config, status, created_at, updated_at
                FROM cbsc_strategies
                ORDER BY created_at;
            """))
            strategies = result.fetchall()

            for strategy in strategies:
                try:
                    strategy_dict = {
                        "id": str(strategy[0]),
                        "user_id": strategy[1],
                        "name": strategy[2],
                        "description": strategy[3],
                        "strategy_type": strategy[4] or "momentum",
                        "status": strategy[6] or "draft",
                        "config": json.loads(strategy[5]) if strategy[5] else {},
                        "metadata": {
                            "source": "cbsc_strategies",
                            "is_cbsc_strategy": True
                        },
                        "created_at": strategy[7],
                        "updated_at": strategy[8]
                    }

                    if not self.dry_run:
                        await session.execute(text("""
                            INSERT INTO unified_strategies (
                                id, user_id, name, description, strategy_type,
                                status, config, metadata, created_at, updated_at
                            ) VALUES (
                                :id, :user_id, :name, :description, :strategy_type,
                                :status, :config, :metadata, :created_at, :updated_at
                            )
                            ON CONFLICT (id) DO NOTHING;
                        """), strategy_dict)

                    self.stats["cbsc_strategies_migrated"] += 1
                    logger.debug(f"Migrated CBSC strategy: {strategy_dict['name']}")

                except Exception as e:
                    logger.error(f"Failed to migrate CBSC strategy {strategy[0]}: {e}")
                    self.stats["errors"].append(str(e))

            if not self.dry_run:
                await session.commit()

            logger.info(f"✓ Migrated {self.stats['cbsc_strategies_migrated']} CBSC strategies")

        except Exception as e:
            logger.error(f"Failed to migrate CBSC strategies: {e}")
            self.stats["errors"].append(str(e))

    async def _migrate_personal_strategies(self, session: AsyncSession):
        """
        Migrate data from personal_strategies table
        """
        logger.info("Phase 4: Migrating personal strategies...")

        try:
            from sqlalchemy import text
            result = await session.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'personal_strategies'
                );
            """))
            exists = result.scalar()

            if not exists:
                logger.info("personal_strategies table does not exist, skipping")
                return

            # Get count
            result = await session.execute(text("""
                SELECT COUNT(*) FROM personal_strategies;
            """))
            count = result.scalar()

            if count == 0:
                logger.info("No personal strategies found")
                return

            logger.info(f"Found {count} personal strategies")

            # Get all personal strategies
            result = await session.execute(text("""
                SELECT
                    id, user_id, name, description, strategy_type,
                    config, preferences, status, created_at, updated_at
                FROM personal_strategies
                ORDER BY created_at;
            """))
            strategies = result.fetchall()

            for strategy in strategies:
                try:
                    # Merge config and preferences
                    config = json.loads(strategy[5]) if strategy[5] else {}
                    preferences = json.loads(strategy[6]) if strategy[6] else {}
                    merged_config = {**config, **preferences}

                    strategy_dict = {
                        "id": str(strategy[0]),
                        "user_id": strategy[1],
                        "name": strategy[2],
                        "description": strategy[3],
                        "strategy_type": strategy[4] or "momentum",
                        "status": strategy[7] or "draft",
                        "config": merged_config,
                        "metadata": {
                            "source": "personal_strategies",
                            "is_personal_strategy": True
                        },
                        "created_at": strategy[8],
                        "updated_at": strategy[9]
                    }

                    if not self.dry_run:
                        await session.execute(text("""
                            INSERT INTO unified_strategies (
                                id, user_id, name, description, strategy_type,
                                status, config, metadata, created_at, updated_at
                            ) VALUES (
                                :id, :user_id, :name, :description, :strategy_type,
                                :status, :config, :metadata, :created_at, :updated_at
                            )
                            ON CONFLICT (id) DO NOTHING;
                        """), strategy_dict)

                    self.stats["personal_strategies_migrated"] += 1
                    logger.debug(f"Migrated personal strategy: {strategy_dict['name']}")

                except Exception as e:
                    logger.error(f"Failed to migrate personal strategy {strategy[0]}: {e}")
                    self.stats["errors"].append(str(e))

            if not self.dry_run:
                await session.commit()

            logger.info(f"✓ Migrated {self.stats['personal_strategies_migrated']} personal strategies")

        except Exception as e:
            logger.error(f"Failed to migrate personal strategies: {e}")
            self.stats["errors"].append(str(e))

    async def _verify_migration(self, session: AsyncSession):
        """
        Verify migration and generate report
        """
        logger.info("Phase 5: Verifying migration...")

        try:
            from sqlalchemy import text

            # Count unified strategies
            result = await session.execute(text("""
                SELECT COUNT(*) FROM unified_strategies;
            """))
            total = result.scalar()

            # Count by source
            result = await session.execute(text("""
                SELECT
                    COALESCE(metadata->>'source', 'unknown') as source,
                    COUNT(*) as count
                FROM unified_strategies
                GROUP BY source
                ORDER BY source;
            """))
            by_source = {row[0]: row[1] for row in result.fetchall()}

            # Count by type
            result = await session.execute(text("""
                SELECT strategy_type, COUNT(*) as count
                FROM unified_strategies
                GROUP BY strategy_type
                ORDER BY strategy_type;
            """))
            by_type = {row[0]: row[1] for row in result.fetchall()}

            logger.info("")
            logger.info("Migration Summary:")
            logger.info(f"  Total unified strategies: {total}")
            logger.info(f"  By source:")
            for source, count in by_source.items():
                logger.info(f"    - {source}: {count}")
            logger.info(f"  By type:")
            for stype, count in by_type.items():
                logger.info(f"    - {stype}: {count}")

            if self.stats["errors"]:
                logger.warning(f"  Errors encountered: {len(self.stats['errors'])}")

        except Exception as e:
            logger.error(f"Verification failed: {e}")
            self.stats["errors"].append(str(e))

    def _print_summary(self):
        """Print migration summary"""
        duration = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()

        logger.info("")
        logger.info("=" * 60)
        logger.info("Migration Summary")
        logger.info("=" * 60)
        logger.info(f"Duration: {duration:.2f} seconds")
        logger.info(f"Mode: {'DRY RUN' if self.dry_run else 'EXECUTE'}")
        logger.info("")
        logger.info("Migrated Records:")
        logger.info(f"  - Legacy strategies: {self.stats['strategies_migrated']}")
        logger.info(f"  - CBSC strategies: {self.stats['cbsc_strategies_migrated']}")
        logger.info(f"  - Personal strategies: {self.stats['personal_strategies_migrated']}")
        logger.info(f"  - Total: {self.stats['strategies_migrated'] + self.stats['cbsc_strategies_migrated'] + self.stats['personal_strategies_migrated']}")
        logger.info("")

        if self.stats["errors"]:
            logger.warning(f"Errors: {len(self.stats['errors'])}")
            for error in self.stats["errors"][:5]:  # Show first 5 errors
                logger.warning(f"  - {error}")
        else:
            logger.info("✓ No errors")

        logger.info("=" * 60)


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Unified Strategy Migration Script"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Perform a dry run without modifying data (default)"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute the migration and modify data"
    )
    parser.add_argument(
        "--database-url",
        type=str,
        default="postgresql+asyncpg://user:password@localhost/cbsc",
        help="Database connection URL"
    )

    args = parser.parse_args()

    # If --execute is specified, turn off dry-run
    dry_run = not args.execute

    # Run migration
    async with UnifiedStrategyMigration(
        database_url=args.database_url,
        dry_run=dry_run
    ) as migration:
        await migration.run_migration()


if __name__ == "__main__":
    asyncio.run(main())
