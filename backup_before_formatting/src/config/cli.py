"""
Configuration Management CLI

Command - line interface for managing configuration including validation,
migration, backup, and environment management.
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from .manager import ConfigManager
from .validator import ConfigValidator, ValidationError

logger = logging.getLogger(__name__)


class ConfigCLI:
    """Command - line interface for configuration management."""

    def __init__(self):
        """Initialize the CLI."""
        self.parser = self._setup_parser()
        self.config_manager: Optional[ConfigManager] = None

    def _setup_parser(self) -> argparse.ArgumentParser:
        """Setup command - line argument parser."""
        parser = argparse.ArgumentParser(
            prog="quant - config",
            description="Hong Kong Quantitative Trading System Configuration Management",
        )

        # Global options
        parser.add_argument(
            "--environment",
            "-e",
            choices=["development", "testing", "staging", "production"],
            default="development",
            help="Target environment",
        )
        parser.add_argument(
            "--config - dir", "-c", default="config", help="Configuration directory path"
        )
        parser.add_argument(
            "--verbose", "-v", action="store_true", help="Enable verbose logging"
        )

        # Subcommands
        subparsers = parser.add_subparsers(dest="command", help="Available commands")

        # Validate command
        validate_parser = subparsers.add_parser(
            "validate", help="Validate configuration"
        )
        validate_parser.add_argument(
            "--config - file", help="Specific configuration file to validate"
        )
        validate_parser.add_argument(
            "--strict", action="store_true", help="Fail on warnings"
        )

        # Init command
        init_parser = subparsers.add_parser("init", help="Initialize configuration")
        init_parser.add_argument(
            "--force",
            "-f",
            action="store_true",
            help="Overwrite existing configuration",
        )

        # Show command
        show_parser = subparsers.add_parser("show", help="Show current configuration")
        show_parser.add_argument(
            "--key", "-k", help="Show specific configuration key (e.g., database.host)"
        )
        show_parser.add_argument(
            "--format", choices=["yaml", "json"], default="yaml", help="Output format"
        )
        show_parser.add_argument(
            "--no - secrets", action="store_true", help="Hide sensitive values"
        )

        # Export command
        export_parser = subparsers.add_parser("export", help="Export configuration")
        export_parser.add_argument(
            "--output", "-o", required=True, help="Output file path"
        )
        export_parser.add_argument(
            "--format", choices=["yaml", "json"], default="yaml", help="Export format"
        )
        export_parser.add_argument(
            "--include - secrets", action="store_true", help="Include sensitive values"
        )

        # Set command
        set_parser = subparsers.add_parser("set", help="Set configuration value")
        set_parser.add_argument("key", help="Configuration key (e.g., database.host)")
        set_parser.add_argument("value", help="Configuration value")
        set_parser.add_argument(
            "--persist", action="store_true", help="Persist change to disk"
        )

        # Backup command
        backup_parser = subparsers.add_parser(
            "backup", help="Create configuration backup"
        )
        backup_parser.add_argument("--name", help="Backup name (default: timestamp)")

        # Restore command
        restore_parser = subparsers.add_parser("restore", help="Restore from backup")
        restore_parser.add_argument("timestamp", help="Backup timestamp to restore")

        # List command
        list_parser = subparsers.add_parser("list", help="List configuration backups")
        list_parser.add_argument(
            "--format", choices=["table", "json"], default="table", help="Output format"
        )

        # Migrate command
        migrate_parser = subparsers.add_parser("migrate", help="Migrate configuration")
        migrate_parser.add_argument("from_env", help="Source environment")
        migrate_parser.add_argument("to_env", help="Target environment")
        migrate_parser.add_argument(
            "--dry - run",
            action="store_true",
            help="Show what would be migrated without making changes",
        )

        # Generate - secret command
        secret_parser = subparsers.add_parser(
            "generate - secret", help="Generate secure secret"
        )
        secret_parser.add_argument(
            "--length", type=int, default=32, help="Secret length"
        )
        secret_parser.add_argument(
            "--type",
            choices=["token", "key", "password"],
            default="key",
            help="Secret type",
        )

        # Schema command
        schema_parser = subparsers.add_parser(
            "schema", help="Generate configuration schema"
        )
        schema_parser.add_argument(
            "--environment", help="Target environment for schema"
        )
        schema_parser.add_argument("--output", "-o", help="Output file path")

        return parser

    def run(self, args: Optional[list] = None):
        """Run the CLI with given arguments."""
        parsed_args = self.parser.parse_args(args)

        # Setup logging
        level = logging.DEBUG if parsed_args.verbose else logging.INFO
        logging.basicConfig(
            level=level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        if not parsed_args.command:
            self.parser.print_help()
            return 1

        try:
            # Initialize config manager
            self.config_manager = ConfigManager(
                environment=parsed_args.environment, config_dir=parsed_args.config_dir
            )

            # Execute command
            command_method = getattr(self, f"_cmd_{parsed_args.command}", None)
            if command_method:
                return command_method(parsed_args)
            else:
                print(f"Unknown command: {parsed_args.command}")
                return 1

        except Exception as e:
            logger.error(f"Command failed: {e}")
            if parsed_args.verbose:
                import traceback

                traceback.print_exc()
            return 1

    # Command implementations

    def _cmd_validate(self, args) -> int:
        """Validate configuration command."""
        validator = ConfigValidator()

        if args.config_file:
            # Validate specific file
            path = Path(args.config_file)
            if not path.exists():
                print(f"Error: Configuration file not found: {args.config_file}")
                return 1

            if path.suffix in [".yaml", ".yml"]:
                with open(path, "r") as f:
                    config = yaml.safe_load(f) or {}
            elif path.suffix == ".json":
                with open(path, "r") as f:
                    config = json.load(f) or {}
            else:
                print(f"Error: Unsupported file format: {path.suffix}")
                return 1

            is_valid, errors, warnings = validator.validate_config(
                config, self.config_manager.environment
            )
        else:
            # Validate current configuration
            is_valid, errors, warnings = self.config_manager.validate_current_config()

        # Display results
        if is_valid and (not warnings or not args.strict):
            print("✅ Configuration is valid")
            return 0
        else:
            if errors:
                print("❌ Configuration validation failed:")
                for error in errors:
                    print(f"  - {error}")
            if warnings:
                print("⚠️  Configuration warnings:")
                for warning in warnings:
                    print(f"  - {warning}")
                if args.strict:
                    print("Validation failed due to strict mode")
                    return 1

        return 0 if is_valid else 1

    def _cmd_init(self, args) -> int:
        """Initialize configuration command."""
        config_dir = Path(args.config_dir)
        config_dir.mkdir(parents=True, exist_ok=True)

        # Create configuration files
        files_to_create = [
            ("base.yaml", "base configuration"),
            (
                f"{args.environment}.yaml",
                f"{args.environment} environment configuration",
            ),
            ("local.yaml", "local overrides"),
        ]

        for filename, description in files_to_create:
            file_path = config_dir / filename
            if file_path.exists() and not args.force:
                print(f"⚠️  {description} already exists: {filename}")
                continue

            if filename == "base.yaml":
                # Copy base template
                base_template = (
                    Path(__file__).parent.parent.parent / "config" / "base.yaml"
                )
                if base_template.exists():
                    import shutil

                    shutil.copy2(base_template, file_path)
                    print(f"✅ Created {description}: {filename}")
                else:
                    # Create from schema
                    self.config_manager.loader.create_default_config_file(
                        str(file_path)
                    )
                    print(f"✅ Created {description} from schema: {filename}")
            else:
                # Create empty file or from schema
                if filename.endswith(".yaml") and filename != "base.yaml":
                    self.config_manager.loader.create_default_config_file(
                        str(file_path)
                    )
                    print(f"✅ Created {description} from schema: {filename}")
                else:
                    file_path.write_text("# Local configuration overrides\n")
                    print(f"✅ Created {description}: {filename}")

        print(f"\nConfiguration initialized in: {config_dir}")
        print("Edit the configuration files and run 'quant - config validate' to check.")
        return 0

    def _cmd_show(self, args) -> int:
        """Show configuration command."""
        if args.key:
            value = self.config_manager.get(args.key)
            if value is not None:
                if args.format == "json":
                    print(json.dumps(value, indent=2, default=str))
                else:
                    print(yaml.dump({args.key: value}, default_flow_style=False))
            else:
                print(f"Configuration key not found: {args.key}")
                return 1
        else:
            config_dict = self.config_manager.config.dict()
            if args.no_secrets:
                # Remove sensitive values
                self._sanitize_config_dict(config_dict)

            if args.format == "json":
                print(json.dumps(config_dict, indent=2, default=str))
            else:
                print(yaml.dump(config_dict, default_flow_style=False))

        return 0

    def _cmd_export(self, args) -> int:
        """Export configuration command."""
        self.config_manager.export_config(
            args.output, args.format, args.include_secrets
        )
        print(f"✅ Configuration exported to: {args.output}")
        return 0

    def _cmd_set(self, args) -> int:
        """Set configuration value command."""
        # Parse the value (try to convert to appropriate type)
        try:
            parsed_value = json.loads(args.value)
        except json.JSONDecodeError:
            parsed_value = args.value

        success = self.config_manager.update_config(
            {args.key: parsed_value}, persist=args.persist
        )

        if success:
            print(f"✅ Set {args.key} = {parsed_value}")
            if args.persist:
                print("✅ Configuration persisted to disk")
            return 0
        else:
            print(f"❌ Failed to set {args.key}")
            return 1

    def _cmd_backup(self, args) -> int:
        """Create backup command."""
        self.config_manager._create_backup()
        backup_name = args.name or "latest"
        print(f"✅ Configuration backup created: {backup_name}")
        return 0

    def _cmd_restore(self, args) -> int:
        """Restore from backup command."""
        success = self.config_manager.rollback_to_backup(args.timestamp)

        if success:
            print(f"✅ Configuration restored from backup: {args.timestamp}")
            return 0
        else:
            print(f"❌ Failed to restore from backup: {args.timestamp}")
            return 1

    def _cmd_list(self, args) -> int:
        """List backups command."""
        backups = self.config_manager.get_config_history()

        if not backups:
            print("No configuration backups found")
            return 0

        if args.format == "json":
            print(json.dumps(backups, indent=2, default=str))
        else:
            print("Configuration Backups:")
            print("-" * 60)
            for backup in backups:
                print(f"  {backup['timestamp']} - {backup['file']}")

        return 0

    def _cmd_migrate(self, args) -> int:
        """Migrate configuration command."""
        from_loader = ConfigManager(environment=args.from_env)
        to_loader = ConfigManager(environment=args.to_env)

        from_config = from_loader.config.dict()

        if args.dry_run:
            print(f"Would migrate configuration from {args.from_env} to {args.to_env}:")
            print(yaml.dump(from_config, default_flow_style=False))
            return 0

        # Validate configuration for target environment
        validator = ConfigValidator()
        is_valid, errors, warnings = validator.validate_config(from_config, args.to_env)

        if not is_valid:
            print(f"❌ Configuration validation failed for {args.to_env}:")
            for error in errors:
                print(f"  - {error}")
            return 1

        if warnings:
            print(f"⚠️  Configuration warnings for {args.to_env}:")
            for warning in warnings:
                print(f"  - {warning}")

        # Apply migration
        to_loader.update_config(from_config, persist=True)
        print(f"✅ Configuration migrated from {args.from_env} to {args.to_env}")
        return 0

    def _cmd_generate_secret(self, args) -> int:
        """Generate secure secret command."""
        validator = ConfigValidator()

        secret = validator.generate_secure_secret(args.length)

        if args.type == "token":
            print(f"Generated Token: {secret}")
        elif args.type == "key":
            print(f"Generated Secret Key: {secret}")
        elif args.type == "password":
            is_strong, issues = validator.validate_password_strength(secret)
            if not is_strong:
                print("⚠️  Generated password has strength issues:")
                for issue in issues:
                    print(f"  - {issue}")
            print(f"Generated Password: {secret}")

        return 0

    def _cmd_schema(self, args) -> int:
        """Generate configuration schema command."""
        from .schema import ConfigSchema

        schema = ConfigSchema()
        env = args.environment or self.config_manager.environment
        default_config = schema.get_default_config(env)

        if args.output:
            output_path = Path(args.output)
            if output_path.suffix == ".json":
                with open(output_path, "w") as f:
                    json.dump(default_config, f, indent=2)
            else:
                with open(output_path, "w") as f:
                    yaml.dump(default_config, f, default_flow_style=False, indent=2)
            print(f"✅ Configuration schema generated: {args.output}")
        else:
            print(yaml.dump(default_config, default_flow_style=False, indent=2))

        return 0

    def _sanitize_config_dict(self, config_dict: Dict[str, Any]):
        """Remove sensitive values from configuration dictionary."""
        sensitive_keys = ["password", "secret", "token", "key"]

        def sanitize_recursive(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if any(sensitive in key.lower() for sensitive in sensitive_keys):
                        obj[key] = "***REDACTED***"
                    else:
                        sanitize_recursive(value)
            elif isinstance(obj, list):
                for item in obj:
                    sanitize_recursive(item)

        sanitize_recursive(config_dict)


def main():
    """Main entry point for CLI."""
    cli = ConfigCLI()
    sys.exit(cli.run())
