#!/usr / bin / env python3
"""
Configuration Migration Script

Migrates existing scattered configuration files to the centralized
configuration management system.
"""

import os
import sys
import json
import yaml
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from config.manager import ConfigManager
from config.loader import ConfigLoader
from config.utils import (
    load_env_file, merge_dicts, backup_configuration_file,
    convert_config_format, get_config_file_locations
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ConfigMigration:
    """Configuration migration tool."""

    def __init__(self, environment: str = "development", backup: bool = True):
        """
        Initialize migration tool.

        Args:
            environment: Target environment
            backup: Create backup before migration
        """
        self.environment = environment
        self.backup = backup
        self.migration_log = []
        self.errors = []
        self.warnings = []

        # Paths
        self.root_dir = Path(__file__).parent.parent
        self.old_config_dir = self.root_dir
        self.new_config_dir = self.root_dir / "config"
        self.backup_dir = self.root_dir / "config_migrations" / datetime.now().strftime("%Y % m % d_ % H % M % S")

    def run_full_migration(self) -> bool:
        """
        Run complete configuration migration.

        Returns:
            True if migration was successful
        """
        try:
            logger.info("Starting configuration migration...")

            # 1. Create backup if requested
            if self.backup:
                self._create_backup()

            # 2. Scan for existing configurations
            existing_configs = self._scan_existing_configs()

            # 3. Migrate environment variables
            self._migrate_environment_variables()

            # 4. Migrate Docker configuration
            self._migrate_docker_config()

            # 5. Migrate .env files
            self._migrate_env_files()

            # 6. Migrate existing config files
            self._migrate_config_files(existing_configs)

            # 7. Migrate hardcoded configurations
            self._migrate_hardcoded_configs()

            # 8. Generate new configuration structure
            self._generate_new_config_structure()

            # 9. Validate new configuration
            self._validate_new_config()

            # 10. Generate migration report
            self._generate_migration_report()

            logger.info("Configuration migration completed successfully!")
            return True

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            self.errors.append(f"Migration failed: {e}")
            return False

    def _create_backup(self):
        """Create backup of existing configurations."""
        logger.info("Creating configuration backup...")

        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Backup .env files
        env_files = list(self.root_dir.glob(".env*"))
        for env_file in env_files:
            backup_path = self.backup_dir / env_file.name
            shutil.copy2(env_file, backup_path)
            logger.info(f"Backed up: {env_file}")

        # Backup docker - compose.yml
        docker_file = self.root_dir / "docker - compose.yml"
        if docker_file.exists():
            backup_path = self.backup_dir / "docker - compose.yml"
            shutil.copy2(docker_file, backup_path)
            logger.info(f"Backed up: {docker_file}")

        # Backup any existing config directory
        if self.new_config_dir.exists():
            backup_config_dir = self.backup_dir / "config"
            shutil.copytree(self.new_config_dir, backup_config_dir, dirs_exist_ok=True)
            logger.info(f"Backed up: {self.new_config_dir}")

    def _scan_existing_configs(self) -> Dict[str, List[Path]]:
        """Scan for existing configuration files."""
        logger.info("Scanning for existing configuration files...")

        config_files = {
            'env_files': list(self.root_dir.glob(".env*")),
            'yaml_files': list(self.root_dir.rglob("*.yaml")),
            'yml_files': list(self.root_dir.rglob("*.yml")),
            'json_files': list(self.root_dir.rglob("*.json")),
            'docker_files': [
                self.root_dir / "docker - compose.yml",
                self.root_dir / "Dockerfile"
            ]
        }

        # Filter out irrelevant files
        for category in ['yaml_files', 'yml_files', 'json_files']:
            config_files[category] = [
                f for f in config_files[category]
                if not any(part.startswith('.') for part in f.parts)
                and 'node_modules' not in str(f)
                and '.venv' not in str(f)
                and '__pycache__' not in str(f)
            ]

        # Log findings
        for category, files in config_files.items():
            logger.info(f"Found {len(files)} {category}")
            for file_path in files[:5]:  # Show first 5
                logger.info(f"  - {file_path}")
            if len(files) > 5:
                logger.info(f"  ... and {len(files) - 5} more")

        return config_files

    def _migrate_environment_variables(self):
        """Migrate environment variables to centralized format."""
        logger.info("Migrating environment variables...")

        # Extract relevant environment variables
        env_mappings = {
            # Database
            'DB_HOST': 'database.host',
            'DB_PORT': 'database.port',
            'DB_NAME': 'database.name',
            'DB_USER': 'database.user',
            'DB_PASSWORD': 'database.password',
            'POSTGRES_PASSWORD': 'database.password',

            # Redis
            'REDIS_HOST': 'redis.host',
            'REDIS_PORT': 'redis.port',
            'REDIS_PASSWORD': 'redis.password',
            'REDIS_DB': 'redis.db',

            # API
            'STOCK_API_BASE_URL': 'api.base_url',
            'STOCK_API_URL': 'api.stock_api_url',
            'STOCK_API_TIMEOUT': 'api.stock_api_timeout',

            # Dashboard
            'DASHBOARD_PORT': 'api.port',  # Will be mapped appropriately
            'DASHBOARD_HOST': 'api.host',

            # Telegram
            'TELEGRAM_BOT_TOKEN': 'telegram.token',
            'TG_ALLOWED_USER_IDS': 'telegram.allowed_user_ids',
            'TG_ALLOWED_CHAT_IDS': 'telegram.allowed_chat_ids',
            'BOT_OWNER_USER_ID': 'telegram.bot_owner_user_id',

            # Security
            'SECRET_KEY': 'security.secret_key',
            'JWT_SECRET_KEY': 'security.jwt_secret_key',

            # Logging
            'LOG_LEVEL': 'logging.level',

            # Monitoring
            'GRAFANA_USER': 'monitoring.grafana_user',
            'GRAFANA_PASSWORD': 'monitoring.grafana_password',

            # Trading
            'MAX_WORKERS': 'trading.max_workers',
            'CACHE_TTL': 'redis.cache_ttl',  # Will be mapped appropriately
            'RATE_LIMIT_DEFAULT': 'api.rate_limit',  # Will be mapped appropriately
        }

        migrated_vars = {}
        for env_var, config_path in env_mappings.items():
            value = os.getenv(env_var)
            if value:
                migrated_vars[config_path] = value
                logger.info(f"Migrated {env_var} -> {config_path}")

        if migrated_vars:
            self.migration_log.append({
                'action': 'migrate_env_vars',
                'count': len(migrated_vars),
                'variables': migrated_vars
            })

    def _migrate_docker_config(self):
        """Migrate Docker Compose configuration."""
        logger.info("Migrating Docker configuration...")

        docker_file = self.root_dir / "docker - compose.yml"
        if not docker_file.exists():
            logger.info("No docker - compose.yml found")
            return

        try:
            with open(docker_file, 'r') as f:
                docker_config = yaml.safe_load(f)

            docker_mappings = {}

            # Extract database configuration
            if 'services' in docker_config:
                services = docker_config['services']

                # PostgreSQL service
                if 'postgres' in services:
                    postgres = services['postgres']
                    if 'environment' in postgres:
                        env = postgres['environment']
                        docker_mappings.update({
                            'database.host': 'postgres',
                            'database.port': 5432,
                            'database.name': env.get('POSTGRES_DB', 'quant_system'),
                            'database.user': env.get('POSTGRES_USER', 'quant_user'),
                        })

                # Redis service
                if 'redis' in services:
                    redis = services['redis']
                    docker_mappings.update({
                        'redis.host': 'redis',
                        'redis.port': 6379,
                    })
                    if 'command' in str(redis):
                        # Extract Redis settings from command
                        redis_config = redis.get('command', [])
                        if isinstance(redis_config, list):
                            for cmd in redis_config:
                                if '--requirepass' in cmd:
                                    docker_mappings['redis.password'] = 'REDIS_PASSWORD'
                                if '--maxmemory' in cmd:
                                    memory = cmd.split()[-1] if len(cmd.split()) > 1 else '512mb'
                                    docker_mappings['redis.max_memory'] = memory

                # Grafana service
                if 'grafana' in services:
                    grafana = services['grafana']
                    if 'environment' in grafana:
                        env = grafana['environment']
                        docker_mappings.update({
                            'monitoring.grafana_user': env.get('GF_SECURITY_ADMIN_USER', 'admin'),
                        })

            if docker_mappings:
                self.migration_log.append({
                    'action': 'migrate_docker',
                    'mappings': docker_mappings
                })
                logger.info(f"Migrated {len(docker_mappings)} Docker settings")

        except Exception as e:
            logger.error(f"Failed to migrate Docker config: {e}")
            self.errors.append(f"Docker migration failed: {e}")

    def _migrate_env_files(self):
        """Migrate .env files to centralized configuration."""
        logger.info("Migrating .env files...")

        env_files = list(self.root_dir.glob(".env*"))

        for env_file in env_files:
            if env_file.name.startswith('.env'):
                logger.info(f"Processing {env_file}")

                try:
                    env_vars = load_env_file(str(env_file))

                    if env_vars:
                        self.migration_log.append({
                            'action': 'migrate_env_file',
                            'file': str(env_file),
                            'variables': len(env_vars)
                        })
                        logger.info(f"Migrated {len(env_vars)} variables from {env_file}")

                except Exception as e:
                    logger.error(f"Failed to process {env_file}: {e}")
                    self.errors.append(f"ENV file migration failed: {env_file} - {e}")

    def _migrate_config_files(self, config_files: Dict[str, List[Path]]):
        """Migrate existing configuration files."""
        logger.info("Migrating configuration files...")

        # Look for specific configuration files
        specific_configs = {
            'app_config.yaml': 'main_config',
            'config.py': 'python_config',
            'config.json': 'json_config',
        }

        for config_name, config_type in specific_configs.items():
            config_path = self.root_dir / config_name
            if config_path.exists():
                try:
                    if config_path.suffix in ['.yaml', '.yml']:
                        with open(config_path, 'r') as f:
                            config_data = yaml.safe_load(f) or {}
                    elif config_path.suffix == '.json':
                        with open(config_path, 'r') as f:
                            config_data = json.load(f) or {}
                    elif config_path.suffix == '.py':
                        # Handle Python config files
                        config_data = self._parse_python_config(config_path)
                    else:
                        continue

                    if config_data:
                        self.migration_log.append({
                            'action': 'migrate_config_file',
                            'file': str(config_path),
                            'type': config_type,
                            'keys': len(config_data) if isinstance(config_data, dict) else 0
                        })
                        logger.info(f"Migrated {config_name} ({config_type})")

                except Exception as e:
                    logger.error(f"Failed to migrate {config_path}: {e}")
                    self.errors.append(f"Config file migration failed: {config_path} - {e}")

    def _parse_python_config(self, config_path: Path) -> Dict[str, Any]:
        """Parse Python configuration file."""
        # This is a simplified parser - in practice, you'd want more sophisticated parsing
        config_data = {}

        try:
            with open(config_path, 'r') as f:
                content = f.read()

            # Simple extraction of key - value pairs
            import re

            # Match simple assignments like KEY = "value"
            pattern = r'^([A - Z_][A - Z0 - 9_]*)\s*=\s*[\'"]([^\'"]*)[\'"]'
            matches = re.findall(pattern, content, re.MULTILINE)

            for key, value in matches:
                # Map Python config keys to new structure
                key_mapping = {
                    'DATABASE_URL': 'database.url',
                    'REDIS_URL': 'redis.url',
                    'SECRET_KEY': 'security.secret_key',
                    'DEBUG': 'system.debug',
                }

                mapped_key = key_mapping.get(key, key.lower())
                config_data[mapped_key] = value

        except Exception as e:
            logger.warning(f"Failed to parse Python config {config_path}: {e}")

        return config_data

    def _migrate_hardcoded_configs(self):
        """Scan and report hardcoded configurations in source code."""
        logger.info("Scanning for hardcoded configurations...")

        hardcoded_patterns = {
            r'localhost:\d{4,5}': 'Hardcoded localhost URL',
            r'18\.180\.162\.113': 'Hardcoded API IP address',
            r'[\'"]secret_[a - zA - Z0 - 9]+[\'"]': 'Potential hardcoded secret',
            r'port\s*=\s*\d{4,5}': 'Hardcoded port',
            r'host\s*=\s*[\'"][^\'\"]+[\'"]': 'Hardcoded host',
        }

        source_files = []
        for pattern in ['**/*.py']:
            source_files.extend(self.root_dir.rglob(pattern))

        hardcoded_issues = []

        for source_file in source_files:
            if any(part.startswith('.') for part in source_file.parts):
                continue

            try:
                with open(source_file, 'r', encoding='utf - 8') as f:
                    content = f.read()

                for pattern, description in hardcoded_patterns.items():
                    import re
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        hardcoded_issues.append({
                            'file': str(source_file),
                            'line': content[:match.start()].count('\n') + 1,
                            'pattern': match.group(),
                            'description': description
                        })

            except Exception as e:
                logger.warning(f"Failed to scan {source_file}: {e}")

        if hardcoded_issues:
            self.warnings.append({
                'action': 'hardcoded_configs_found',
                'count': len(hardcoded_issues),
                'issues': hardcoded_issues[:20]  # Limit to first 20
            })
            logger.warning(f"Found {len(hardcoded_issues)} hardcoded configurations")

    def _generate_new_config_structure(self):
        """Generate the new centralized configuration structure."""
        logger.info("Generating new configuration structure...")

        # Create config directory
        self.new_config_dir.mkdir(parents=True, exist_ok=True)

        # Initialize new config manager
        config_manager = ConfigManager(environment=self.environment)

        # Apply migrated configurations
        all_migrations = {}

        for log_entry in self.migration_log:
            if 'variables' in log_entry:
                all_migrations.update(log_entry['variables'])
            elif 'mappings' in log_entry:
                all_migrations.update(log_entry['mappings'])

        if all_migrations:
            # Convert flat keys to nested structure
            nested_config = self._flatten_to_nested(all_migrations)
            success = config_manager.update_config(nested_config)

            if success:
                # Save the migrated configuration
                config_manager.export_config(
                    str(self.new_config_dir / f"{self.environment}.yaml"),
                    format='yaml'
                )
                logger.info("New configuration structure generated")
            else:
                logger.error("Failed to apply migrated configurations")
                self.errors.append("Failed to generate new config structure")

    def _flatten_to_nested(self, flat_config: Dict[str, Any]) -> Dict[str, Any]:
        """Convert flat configuration to nested structure."""
        nested = {}

        for key, value in flat_config.items():
            parts = key.split('.')
            current = nested

            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]

            current[parts[-1]] = value

        return nested

    def _validate_new_config(self):
        """Validate the new configuration."""
        logger.info("Validating new configuration...")

        try:
            config_manager = ConfigManager(environment=self.environment)
            is_valid, errors, warnings = config_manager.validate_current_config()

            if is_valid:
                logger.info("✅ New configuration is valid")
            else:
                logger.error("❌ New configuration validation failed")
                self.errors.extend([f"Validation: {error}" for error in errors])

            if warnings:
                logger.warning("⚠️ Configuration warnings:")
                for warning in warnings:
                    logger.warning(f"  - {warning}")
                self.warnings.append(f"Validation warnings: {len(warnings)}")

        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            self.errors.append(f"Validation error: {e}")

    def _generate_migration_report(self):
        """Generate migration report."""
        report_path = self.backup_dir / "migration_report.json"

        report = {
            'timestamp': datetime.now().isoformat(),
            'environment': self.environment,
            'backup_location': str(self.backup_dir),
            'new_config_location': str(self.new_config_dir),
            'migration_log': self.migration_log,
            'errors': self.errors,
            'warnings': self.warnings,
            'summary': {
                'migrations_applied': len(self.migration_log),
                'errors_count': len(self.errors),
                'warnings_count': len(self.warnings),
                'success': len(self.errors) == 0
            }
        }

        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        # Print summary
        print("\n" + "="*50)
        print("CONFIGURATION MIGRATION REPORT")
        print("="*50)
        print(f"Environment: {self.environment}")
        print(f"Backup location: {self.backup_dir}")
        print(f"Migrations applied: {report['summary']['migrations_applied']}")
        print(f"Errors: {report['summary']['errors_count']}")
        print(f"Warnings: {report['summary']['warnings_count']}")
        print(f"Success: {report['summary']['success']}")
        print("\nDetailed report saved to:", report_path)

        if self.warnings:
            print("\n⚠️ WARNINGS:")
            for warning in self.warnings:
                print(f"  - {warning}")

        if self.errors:
            print("\n❌ ERRORS:")
            for error in self.errors:
                print(f"  - {error}")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Configuration Migration Tool")
    parser.add_argument('--environment', '-e', default='development',
                       choices=['development', 'testing', 'staging', 'production'],
                       help='Target environment')
    parser.add_argument('--no - backup', action='store_true',
                       help='Skip creating backup')

    args = parser.parse_args()

    migration = ConfigMigration(
        environment=args.environment,
        backup=not args.no_backup
    )

    success = migration.run_full_migration()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()