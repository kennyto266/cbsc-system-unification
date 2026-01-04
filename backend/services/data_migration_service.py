"""
Data Migration Service for CBSC System
Migrates data from file-based storage (JSON/CSV) to PostgreSQL database.
"""

import os
import json
import csv
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from contextlib import asynccontextmanager

from backend.models.unified_models import (
    User, Role, UserRole, Strategy, StrategyConfig, StrategyPerformance,
    Portfolio, Trade, MarketData, TechnicalIndicator, BacktestResult
)


class DataMigrationService:
    """
    Service for migrating data from file storage to PostgreSQL database.
    Supports JSON, CSV file formats with validation and rollback capabilities.
    """

    def __init__(
        self,
        database_url: str,
        data_dir: str = './data',
        backup_dir: str = './backups',
        batch_size: int = 1000
    ):
        """
        Initialize migration service.

        Args:
            database_url: Async PostgreSQL connection URL
            data_dir: Directory containing source data files
            backup_dir: Directory for migration backups
            batch_size: Number of records to process per batch
        """
        self.database_url = database_url
        self.data_dir = Path(data_dir)
        self.backup_dir = Path(backup_dir)
        self.batch_size = batch_size

        # Create directories if they don't exist
        self.data_dir.mkdir(exist_ok=True)
        self.backup_dir.mkdir(exist_ok=True)

        # Initialize database engine
        self.engine = create_async_engine(
            database_url,
            echo=False,
            pool_pre_ping=True
        )
        self.async_session = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

    @asynccontextmanager
    async def get_session(self):
        """Get async database session"""
        async with self.async_session() as session:
            yield session

    # =========================================================================
    # File Reading Utilities
    # =========================================================================

    async def read_json_file(self, filename: str) -> List[Dict[str, Any]]:
        """
        Read JSON file and return parsed data.

        Args:
            filename: Name of the JSON file in data_dir

        Returns:
            List of dictionaries containing parsed data

        Raises:
            FileNotFoundError: If file doesn't exist
            json.JSONDecodeError: If file contains invalid JSON
        """
        file_path = self.data_dir / filename

        if not file_path.exists():
            raise FileNotFoundError(f"Data file not found: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Ensure data is a list
        if isinstance(data, dict):
            data = [data]
        elif not isinstance(data, list):
            raise ValueError(f"Invalid JSON format in {filename}: expected list or dict")

        return data

    async def read_csv_file(self, filename: str) -> List[Dict[str, Any]]:
        """
        Read CSV file and return parsed data.

        Args:
            filename: Name of the CSV file in data_dir

        Returns:
            List of dictionaries containing parsed data

        Raises:
            FileNotFoundError: If file doesn't exist
            csv.Error: If file contains invalid CSV
        """
        file_path = self.data_dir / filename

        if not file_path.exists():
            raise FileNotFoundError(f"Data file not found: {file_path}")

        data = []
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(dict(row))

        return data

    # =========================================================================
    # Data Validation
    # =========================================================================

    def validate_user_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate user data before migration.

        Args:
            data: User data dictionary

        Returns:
            True if valid, raises ValueError if invalid
        """
        required_fields = ['username', 'email', 'hashed_password']
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")

        # Validate email format (basic check)
        if '@' not in data['email']:
            raise ValueError(f"Invalid email format: {data['email']}")

        # Validate username length
        if len(data['username']) > 50:
            raise ValueError(f"Username too long (max 50 chars): {data['username']}")

        return True

    def validate_strategy_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate strategy data before migration.

        Args:
            data: Strategy data dictionary

        Returns:
            True if valid, raises ValueError if invalid
        """
        required_fields = ['user_id', 'name', 'category']
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")

        # Validate status
        valid_statuses = ['draft', 'active', 'paused', 'archived']
        status = data.get('status', 'draft')
        if status not in valid_statuses:
            raise ValueError(f"Invalid strategy status: {status}")

        return True

    # =========================================================================
    # Data Migration Methods
    # =========================================================================

    async def migrate_users(
        self,
        source_file: str = 'users.json',
        create_backup: bool = True
    ) -> Dict[str, int]:
        """
        Migrate user data from JSON/CSV to database.

        Args:
            source_file: Source data filename (JSON or CSV)
            create_backup: Whether to create backup before migration

        Returns:
            Dictionary with migration statistics
        """
        stats = {
            'total': 0,
            'created': 0,
            'updated': 0,
            'failed': 0,
            'errors': []
        }

        try:
            # Determine file type and read data
            if source_file.endswith('.json'):
                users_data = await self.read_json_file(source_file)
            elif source_file.endswith('.csv'):
                users_data = await self.read_csv_file(source_file)
            else:
                raise ValueError(f"Unsupported file format: {source_file}")

            stats['total'] = len(users_data)

            # Create backup if requested
            if create_backup:
                backup_file = self.backup_dir / f"users_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(backup_file, 'w', encoding='utf-8') as f:
                    json.dump(users_data, f, indent=2, default=str)

            async with self.get_session() as session:
                for user_data in users_data:
                    try:
                        # Validate data
                        self.validate_user_data(user_data)

                        # Check if user already exists
                        stmt = select(User).where(
                            (User.username == user_data['username']) |
                            (User.email == user_data['email'])
                        )
                        result = await session.execute(stmt)
                        existing_user = result.scalar_one_or_none()

                        if existing_user:
                            # Update existing user
                            for key, value in user_data.items():
                                if hasattr(existing_user, key):
                                    setattr(existing_user, key, value)
                            stats['updated'] += 1
                        else:
                            # Create new user
                            new_user = User(**user_data)
                            session.add(new_user)
                            stats['created'] += 1

                        # Commit batch
                        if stats['created'] + stats['updated'] % self.batch_size == 0:
                            await session.commit()

                    except Exception as e:
                        stats['failed'] += 1
                        stats['errors'].append({
                            'user': user_data.get('username', 'unknown'),
                            'error': str(e)
                        })

                # Final commit
                await session.commit()

        except Exception as e:
            await session.rollback()
            stats['errors'].append({'fatal': str(e)})
            raise

        return stats

    async def migrate_strategies(
        self,
        source_file: str = 'strategies.json',
        create_backup: bool = True
    ) -> Dict[str, int]:
        """
        Migrate strategy data from JSON/CSV to database.

        Args:
            source_file: Source data filename
            create_backup: Whether to create backup before migration

        Returns:
            Dictionary with migration statistics
        """
        stats = {
            'total': 0,
            'created': 0,
            'updated': 0,
            'failed': 0,
            'errors': []
        }

        try:
            # Read source data
            if source_file.endswith('.json'):
                strategies_data = await self.read_json_file(source_file)
            elif source_file.endswith('.csv'):
                strategies_data = await self.read_csv_file(source_file)
            else:
                raise ValueError(f"Unsupported file format: {source_file}")

            stats['total'] = len(strategies_data)

            # Create backup if requested
            if create_backup:
                backup_file = self.backup_dir / f"strategies_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(backup_file, 'w', encoding='utf-8') as f:
                    json.dump(strategies_data, f, indent=2, default=str)

            async with self.get_session() as session:
                for strategy_data in strategies_data:
                    try:
                        # Validate data
                        self.validate_strategy_data(strategy_data)

                        # Check if strategy exists (by user_id and name)
                        stmt = select(Strategy).where(
                            Strategy.user_id == strategy_data['user_id'],
                            Strategy.name == strategy_data['name']
                        )
                        result = await session.execute(stmt)
                        existing_strategy = result.scalar_one_or_none()

                        if existing_strategy:
                            # Update existing strategy
                            for key, value in strategy_data.items():
                                if hasattr(existing_strategy, key) and key != 'id':
                                    setattr(existing_strategy, key, value)
                            stats['updated'] += 1
                        else:
                            # Create new strategy
                            new_strategy = Strategy(**strategy_data)
                            session.add(new_strategy)
                            stats['created'] += 1

                        # Commit batch
                        if stats['created'] + stats['updated'] % self.batch_size == 0:
                            await session.commit()

                    except Exception as e:
                        stats['failed'] += 1
                        stats['errors'].append({
                            'strategy': strategy_data.get('name', 'unknown'),
                            'error': str(e)
                        })

                # Final commit
                await session.commit()

        except Exception as e:
            await session.rollback()
            stats['errors'].append({'fatal': str(e)})
            raise

        return stats

    async def migrate_market_data(
        self,
        source_file: str = 'market_data.csv',
        create_backup: bool = True
    ) -> Dict[str, int]:
        """
        Migrate market data from CSV to database.

        Args:
            source_file: Source CSV filename
            create_backup: Whether to create backup before migration

        Returns:
            Dictionary with migration statistics
        """
        stats = {
            'total': 0,
            'created': 0,
            'failed': 0,
            'errors': []
        }

        try:
            # Read CSV data
            market_data = await self.read_csv_file(source_file)
            stats['total'] = len(market_data)

            # Create backup if requested
            if create_backup:
                backup_file = self.backup_dir / f"market_data_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                with open(backup_file, 'w', encoding='utf-8', newline='') as f:
                    if market_data:
                        writer = csv.DictWriter(f, fieldnames=market_data[0].keys())
                        writer.writeheader()
                        writer.writerows(market_data)

            async with self.get_session() as session:
                for row in market_data:
                    try:
                        # Convert data types
                        record = {
                            'symbol': row['symbol'],
                            'timestamp': datetime.fromisoformat(row['timestamp']),
                            'open_price': Decimal(row.get('open_price', 0)) if row.get('open_price') else None,
                            'high_price': Decimal(row.get('high_price', 0)) if row.get('high_price') else None,
                            'low_price': Decimal(row.get('low_price', 0)) if row.get('low_price') else None,
                            'close_price': Decimal(row.get('close_price', 0)) if row.get('close_price') else None,
                            'volume': int(row.get('volume', 0)) if row.get('volume') else None,
                        }

                        # Create market data record
                        new_record = MarketData(**record)
                        session.add(new_record)
                        stats['created'] += 1

                        # Commit batch
                        if stats['created'] % self.batch_size == 0:
                            await session.commit()

                    except Exception as e:
                        stats['failed'] += 1
                        stats['errors'].append({
                            'symbol': row.get('symbol', 'unknown'),
                            'error': str(e)
                        })

                # Final commit
                await session.commit()

        except Exception as e:
            await session.rollback()
            stats['errors'].append({'fatal': str(e)})
            raise

        return stats

    # =========================================================================
    # Rollback Methods
    # =========================================================================

    async def rollback_migration(
        self,
        backup_file: str,
        target_table: str
    ) -> Dict[str, Any]:
        """
        Rollback migration from backup file.

        Args:
            backup_file: Backup filename in backup_dir
            target_table: Target table to restore

        Returns:
            Dictionary with rollback statistics
        """
        stats = {
            'restored': 0,
            'errors': []
        }

        backup_path = self.backup_dir / backup_file

        if not backup_path.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")

        try:
            # Read backup data
            if backup_file.endswith('.json'):
                backup_data = await self.read_json_file(backup_file)
            elif backup_file.endswith('.csv'):
                backup_data = await self.read_csv_file(backup_file)
            else:
                raise ValueError(f"Unsupported backup format: {backup_file}")

            async with self.get_session() as session:
                for record in backup_data:
                    try:
                        # Restore record based on target table
                        if target_table == 'users':
                            obj = User(**record)
                        elif target_table == 'strategies':
                            obj = Strategy(**record)
                        elif target_table == 'market_data':
                            obj = MarketData(**record)
                        else:
                            raise ValueError(f"Unsupported target table: {target_table}")

                        session.add(obj)
                        stats['restored'] += 1

                        # Commit batch
                        if stats['restored'] % self.batch_size == 0:
                            await session.commit()

                    except Exception as e:
                        stats['errors'].append({
                            'record': record.get('id', 'unknown'),
                            'error': str(e)
                        })

                # Final commit
                await session.commit()

        except Exception as e:
            await session.rollback()
            stats['errors'].append({'fatal': str(e)})
            raise

        return stats

    # =========================================================================
    # Data Integrity Checks
    # =========================================================================

    async def validate_data_integrity(self) -> Dict[str, Any]:
        """
        Validate data integrity after migration.

        Returns:
            Dictionary with validation results
        """
        results = {
            'users_count': 0,
            'strategies_count': 0,
            'market_data_count': 0,
            'orphaned_strategies': 0,
            'duplicate_emails': 0,
            'duplicate_usernames': 0,
            'issues': []
        }

        async with self.get_session() as session:
            # Count records
            results['users_count'] = (await session.execute(select(User))).scalar() or 0
            results['strategies_count'] = (await session.execute(select(Strategy))).scalar() or 0
            results['market_data_count'] = (await session.execute(select(MarketData))).scalar() or 0

            # Check for orphaned strategies (strategies without valid user_id)
            stmt = select(Strategy).where(Strategy.user_id.not_in(select(User.id)))
            orphaned = await session.execute(stmt)
            results['orphaned_strategies'] = len(orphaned.scalars().all())
            if results['orphaned_strategies'] > 0:
                results['issues'].append(f"Found {results['orphaned_strategies']} orphaned strategies")

            # Check for duplicate emails
            stmt = select(User.email).group_by(User.email).having(User.count() > 1)
            duplicates = await session.execute(stmt)
            results['duplicate_emails'] = len(duplicates.all())
            if results['duplicate_emails'] > 0:
                results['issues'].append(f"Found {results['duplicate_emails']} duplicate email addresses")

            # Check for duplicate usernames
            stmt = select(User.username).group_by(User.username).having(User.count() > 1)
            duplicates = await session.execute(stmt)
            results['duplicate_usernames'] = len(duplicates.all())
            if results['duplicate_usernames'] > 0:
                results['issues'].append(f"Found {results['duplicate_usernames']} duplicate usernames")

        return results

    # =========================================================================
    # Complete Migration Workflow
    # =========================================================================

    async def run_full_migration(
        self,
        migrate_users: bool = True,
        migrate_strategies: bool = True,
        migrate_market_data: bool = True,
        validate_after: bool = True
    ) -> Dict[str, Any]:
        """
        Run complete data migration workflow.

        Args:
            migrate_users: Whether to migrate users
            migrate_strategies: Whether to migrate strategies
            migrate_market_data: Whether to migrate market data
            validate_after: Whether to validate data integrity after migration

        Returns:
            Dictionary with complete migration results
        """
        results = {
            'start_time': datetime.now().isoformat(),
            'users': None,
            'strategies': None,
            'market_data': None,
            'validation': None,
            'end_time': None
        }

        try:
            # Migrate users
            if migrate_users:
                print("Migrating users...")
                results['users'] = await self.migrate_users('users.json')
                print(f"Users migration complete: {results['users']['created']} created, {results['users']['updated']} updated")

            # Migrate strategies
            if migrate_strategies:
                print("Migrating strategies...")
                results['strategies'] = await self.migrate_strategies('strategies.json')
                print(f"Strategies migration complete: {results['strategies']['created']} created, {results['strategies']['updated']} updated")

            # Migrate market data
            if migrate_market_data:
                print("Migrating market data...")
                results['market_data'] = await self.migrate_market_data('market_data.csv')
                print(f"Market data migration complete: {results['market_data']['created']} records created")

            # Validate data integrity
            if validate_after:
                print("Validating data integrity...")
                results['validation'] = await self.validate_data_integrity()
                if results['validation']['issues']:
                    print(f"Validation complete with {len(results['validation']['issues'])} issues")
                else:
                    print("Validation complete - no issues found")

            results['end_time'] = datetime.now().isoformat()

        except Exception as e:
            results['error'] = str(e)
            raise

        return results


# =============================================================================
# CLI Usage Example
# =============================================================================

async def main():
    """
    Example usage of the DataMigrationService.
    """
    # Initialize migration service
    migration_service = DataMigrationService(
        database_url='postgresql+asyncpg://user:password@localhost/cbsc_db',
        data_dir='./data',
        backup_dir='./backups',
        batch_size=1000
    )

    # Run full migration
    results = await migration_service.run_full_migration(
        migrate_users=True,
        migrate_strategies=True,
        migrate_market_data=True,
        validate_after=True
    )

    # Print results
    print("\n=== Migration Results ===")
    print(json.dumps(results, indent=2, default=str))


if __name__ == '__main__':
    asyncio.run(main())
