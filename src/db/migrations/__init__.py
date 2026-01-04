"""
Database Migrations

Migration system for database schema versioning and updates.
"""

from .001_create_initial_tables import (
    upgrade,
    downgrade,
    run_migration,
    get_migration_version,
    get_migration_description
)

__all__ = [
    "upgrade",
    "downgrade",
    "run_migration",
    "get_migration_version",
    "get_migration_description",
]


MIGRATIONS = [
    {
        "version": "001",
        "name": "create_initial_tables",
        "module": ".001_create_initial_tables",
        "description": "Create initial database tables for CBSC system",
        "applied_at": None
    }
]


class MigrationRunner:
    """Database migration runner"""

    def __init__(self, engine):
        """
        Initialize migration runner.

        Args:
            engine: SQLAlchemy engine instance
        """
        self.engine = engine
        self.logger = logging.getLogger(__name__)

    def get_applied_migrations(self) -> list:
        """Get list of applied migrations from database"""
        from sqlalchemy import text

        try:
            # Check if migrations table exists
            if not self._migrations_table_exists():
                return []

            with self.engine.connect() as conn:
                result = conn.execute(text(
                    "SELECT version FROM schema_migrations ORDER BY applied_at"
                ))
                return [row[0] for row in result]
        except Exception as e:
            self.logger.error(f"Failed to get applied migrations: {e}")
            return []

    def _migrations_table_exists(self) -> bool:
        """Check if migrations table exists"""
        from sqlalchemy import inspect

        inspector = inspect(self.engine)
        return "schema_migrations" in inspector.get_table_names()

    def _create_migrations_table(self):
        """Create migrations tracking table"""
        from sqlalchemy import text, MetaData, Table, Column, String, DateTime

        metadata = MetaData()

        table = Table(
            "schema_migrations",
            metadata,
            Column("version", String(50), primary_key=True),
            Column("name", String(100), nullable=False),
            Column("description", String(500)),
            Column("applied_at", DateTime, nullable=False)
        )

        metadata.create_all(self.engine)
        self.logger.info("Created migrations tracking table")

    def record_migration(self, version: str, name: str, description: str):
        """Record migration as applied"""
        from sqlalchemy import text
        from datetime import timezone

        if not self._migrations_table_exists():
            self._create_migrations_table()

        with self.engine.connect() as conn:
            conn.execute(text(
                """
                INSERT INTO schema_migrations (version, name, description, applied_at)
                VALUES (:version, :name, :description, :applied_at)
                """
            ), {
                "version": version,
                "name": name,
                "description": description,
                "applied_at": datetime.now(timezone.utc)
            })
            conn.commit()

    def remove_migration_record(self, version: str):
        """Remove migration record"""
        from sqlalchemy import text

        with self.engine.connect() as conn:
            conn.execute(text(
                "DELETE FROM schema_migrations WHERE version = :version"
            ), {"version": version})
            conn.commit()

    def upgrade(self, target_version: str = None):
        """
        Run all pending upgrades.

        Args:
            target_version: Target migration version (None for all)
        """
        applied = set(self.get_applied_migrations())

        for migration in MIGRATIONS:
            if migration["version"] in applied:
                self.logger.info(f"Skipping applied migration: {migration['version']}")
                continue

            if target_version and migration["version"] > target_version:
                break

            self.logger.info(f"Applying migration: {migration['version']}")
            self._run_migration(migration["module"], "upgrade")
            self.record_migration(
                migration["version"],
                migration["name"],
                migration["description"]
            )
            migration["applied_at"] = datetime.now(timezone.utc)

    def downgrade(self, target_version: str = None):
        """
        Downgrade migrations.

        Args:
            target_version: Target version to downgrade to
        """
        applied = self.get_applied_migrations()

        if not applied:
            self.logger.warning("No migrations to downgrade")
            return

        # Get migrations to downgrade (in reverse order)
        to_downgrade = []
        for migration in reversed(MIGRATIONS):
            if migration["version"] not in applied:
                continue
            if target_version and migration["version"] <= target_version:
                break
            to_downgrade.append(migration)

        # Run downgrades
        for migration in to_downgrade:
            self.logger.info(f"Downgrading migration: {migration['version']}")
            self._run_migration(migration["module"], "downgrade")
            self.remove_migration_record(migration["version"])
            migration["applied_at"] = None

    def _run_migration(self, module_path: str, direction: str):
        """Run a specific migration"""
        import importlib

        module = importlib.import_module(module_path, package="src.db.migrations")
        run_migration_func = getattr(module, "run_migration", None)

        if run_migration_func:
            run_migration_func(self.engine, direction)
        else:
            raise AttributeError(f"Migration module {module_path} missing run_migration function")

    def status(self) -> dict:
        """Get migration status"""
        applied = set(self.get_applied_migrations())

        pending = []
        for migration in MIGRATIONS:
            if migration["version"] not in applied:
                pending.append(migration)

        return {
            "applied_count": len(applied),
            "pending_count": len(pending),
            "applied_versions": list(applied),
            "pending_versions": [m["version"] for m in pending],
            "current_version": applied[-1] if applied else None
        }

    def create(self, name: str):
        """Create a new migration file (placeholder for future use)"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        version = f"{timestamp}_{name}"
        filename = f"{version}.py"

        self.logger.info(f"Creating migration: {filename}")
        # TODO: Implement migration file generation
        return version


def run_migrations(
    engine,
    direction: str = "upgrade",
    target_version: str = None
):
    """
    Run database migrations.

    Args:
        engine: SQLAlchemy engine instance
        direction: "upgrade" or "downgrade"
        target_version: Target migration version
    """
    runner = MigrationRunner(engine)

    if direction == "upgrade":
        runner.upgrade(target_version)
    elif direction == "downgrade":
        runner.downgrade(target_version)
    else:
        raise ValueError(f"Invalid direction: {direction}")

    # Print status
    status = runner.status()
    logger.info(f"Migration status: {status}")
