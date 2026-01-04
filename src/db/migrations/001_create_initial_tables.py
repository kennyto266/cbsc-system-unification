"""
Database Migration: 001_create_initial_tables

Initial database schema for CBSC Quantitative Trading System.
Creates all tables for users, strategies, market data, performance, and signals.
"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def upgrade(engine):
    """
    Create all database tables.

    Args:
        engine: SQLAlchemy engine instance
    """
    from ..models import Base

    # Import all models to ensure they're registered with Base
    from ..models.strategy import (
        Strategy,
        StrategyParameter,
        StrategyPerformance,
        StrategySignal
    )
    from ..models.market_data import CBSCMarketData
    from ..models.user import User, UserSession

    # Create all tables
    Base.metadata.create_all(engine)
    logger.info("Database tables created successfully")


def downgrade(engine):
    """
    Drop all database tables.

    Args:
        engine: SQLAlchemy engine instance
    """
    from ..models import Base

    # Drop all tables
    Base.metadata.drop_all(engine)
    logger.info("Database tables dropped successfully")


def get_migration_version() -> str:
    """Get migration version identifier"""
    return "001_create_initial_tables"


def get_migration_description() -> str:
    """Get migration description"""
    return "Create initial database tables for CBSC system"


def run_migration(engine, direction: str = "upgrade"):
    """
    Run migration in specified direction.

    Args:
        engine: SQLAlchemy engine instance
        direction: "upgrade" or "downgrade"
    """
    logger.info(
        f"Running migration {get_migration_version()}: "
        f"{direction} - {get_migration_description()}"
    )

    start_time = datetime.now()

    try:
        if direction == "upgrade":
            upgrade(engine)
        elif direction == "downgrade":
            downgrade(engine)
        else:
            raise ValueError(f"Invalid direction: {direction}")

        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"Migration completed in {elapsed:.2f} seconds")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise


if __name__ == "__main__":
    import sys
    from .connection import DatabaseConnectionManager

    # Parse command line arguments
    direction = sys.argv[1] if len(sys.argv) > 1 else "upgrade"

    # Initialize database connection
    db_url = sys.argv[2] if len(sys.argv) > 2 else "sqlite:///cbsc_trading.db"

    db_manager = DatabaseConnectionManager(database_url=db_url)
    db_manager.create_engine()

    # Run migration
    run_migration(db_manager.engine, direction)
