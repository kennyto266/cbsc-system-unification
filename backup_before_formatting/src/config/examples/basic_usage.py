#!/usr / bin / env python3
"""
Basic Configuration Management Examples

This script demonstrates basic usage of the centralized configuration management system.
"""

import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config import ConfigManager, SystemConfig
from src.config.models import DatabaseConfig, TradingConfig


def example_1_basic_usage():
    """Example 1: Basic configuration loading and access."""
    print("=" * 60)
    print("EXAMPLE 1: Basic Configuration Usage")
    print("=" * 60)

    # Initialize configuration manager
    config = ConfigManager(environment="development")

    # Access configuration values
    print("Database Configuration:")
    print(f"  Host: {config.get('database.host')}")
    print(f"  Port: {config.get('database.port')}")
    print(f"  Database: {config.get('database.name')}")
    print(f"  URL: {config.get('database.url')}")

    print("\nTrading Configuration:")
    print(f"  Enabled: {config.get('trading.enabled')}")
    print(f"  Environment: {config.get('trading.environment')}")
    print(f"  Risk Limit: {config.get('trading.risk_limit')}")
    print(f"  Risk - Free Rate: {config.get('trading.risk_free_rate')}")

    # Access typed configuration objects
    print("\nTyped Configuration Access:")
    db_config = config.config.database
    print(f"  Database Pool Size: {db_config.pool_size}")
    print(f"  Database SSL Mode: {db_config.ssl_mode}")

    trading_config = config.config.trading
    print(f"  Max Position Size: {trading_config.max_position_size}")
    print(f"  Max Drawdown: {trading_config.max_drawdown}")


def example_2_environment_specific():
    """Example 2: Environment - specific configurations."""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Environment - Specific Configurations")
    print("=" * 60)

    environments = ["development", "testing", "production"]

    for env in environments:
        print(f"\n{env.upper()} Environment:")
        try:
            config = ConfigManager(environment=env)
            print(f"  Debug: {config.get('system.debug')}")
            print(f"  Database Pool Size: {config.get('database.pool_size')}")
            print(f"  Logging Level: {config.get('logging.level')}")
            print(f"  SSL Enabled: {config.get('security.ssl_enabled')}")
            print(f"  Monitoring Enabled: {config.get('monitoring.enabled')}")
        except Exception as e:
            print(f"  Error loading {env}: {e}")


def example_3_configuration_updates():
    """Example 3: Updating configuration at runtime."""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Runtime Configuration Updates")
    print("=" * 60)

    config = ConfigManager(environment="development")

    print("Original Configuration:")
    print(f"  API Timeout: {config.get('api.timeout')}")
    print(f"  Database Pool Size: {config.get('database.pool_size')}")

    # Update configuration
    updates = {"api.timeout": 45, "database.pool_size": 15, "trading.risk_limit": 0.015}

    print(f"\nUpdating Configuration: {updates}")

    success = config.update_config(updates)
    if success:
        print("✅ Configuration updated successfully")
        print("Updated Configuration:")
        print(f"  API Timeout: {config.get('api.timeout')}")
        print(f"  Database Pool Size: {config.get('database.pool_size')}")
        print(f"  Trading Risk Limit: {config.get('trading.risk_limit')}")
    else:
        print("❌ Failed to update configuration")


def example_4_validation():
    """Example 4: Configuration validation."""
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Configuration Validation")
    print("=" * 60)

    config = ConfigManager(environment="development")

    # Validate current configuration
    is_valid, errors, warnings = config.validate_current_config()

    print(f"Configuration Valid: {is_valid}")

    if errors:
        print(f"\n❌ Validation Errors ({len(errors)}):")
        for error in errors:
            print(f"  - {error}")

    if warnings:
        print(f"\n⚠️ Validation Warnings ({len(warnings)}):")
        for warning in warnings:
            print(f"  - {warning}")

    # Test invalid configuration
    print("\nTesting Invalid Configuration:")
    invalid_config = {
        "database": {
            "port": 70000,  # Invalid port
            "pool_size": -1,  # Invalid pool size
        },
        "trading": {
            "risk_limit": 2.0,  # Invalid risk limit (> 100%)
            "max_drawdown": 3.0,  # Invalid max drawdown (> 100%)
        },
    }

    from src.config.validator import ConfigValidator

    validator = ConfigValidator()
    is_valid, errors, warnings = validator.validate_config(
        invalid_config, "development"
    )

    print(f"Invalid Config Valid: {is_valid}")
    if errors:
        print(f"Expected Errors ({len(errors)}):")
        for error in errors:
            print(f"  - {error}")


def example_5_environment_variables():
    """Example 5: Environment variable overrides."""
    print("\n" + "=" * 60)
    print("EXAMPLE 5: Environment Variable Overrides")
    print("=" * 60)

    # Set some environment variables
    os.environ["QUANT_DATABASE_HOST"] = "env - host.example.com"
    os.environ["QUANT_DATABASE_PORT"] = "9999"
    os.environ["QUANT_API_TIMEOUT"] = "60"
    os.environ["QUANT_TRADING__RISK_LIMIT"] = "0.025"  # Nested config

    config = ConfigManager(environment="development")

    print("Environment Variable Overrides:")
    print(f"  Database Host: {config.get('database.host')}")
    print(f"  Database Port: {config.get('database.port')}")
    print(f"  API Timeout: {config.get('api.timeout')}")
    print(f"  Trading Risk Limit: {config.get('trading.risk_limit')}")

    # Clean up environment variables
    for key in [
        "QUANT_DATABASE_HOST",
        "QUANT_DATABASE_PORT",
        "QUANT_API_TIMEOUT",
        "QUANT_TRADING__RISK_LIMIT",
    ]:
        os.environ.pop(key, None)


def example_6_hot_reload():
    """Example 6: Configuration hot - reload simulation."""
    print("\n" + "=" * 60)
    print("EXAMPLE 6: Configuration Hot - Reload")
    print("=" * 60)

    config = ConfigManager(environment="development")

    # Register a reload callback
    def on_reload(new_config):
        print(f"🔄 Configuration reloaded at {new_config.metadata.loaded_at}")

    config.register_reload_callback("example_callback", on_reload)

    print("Initial API Timeout:", config.get("api.timeout"))

    # Simulate configuration change
    print("Simulating configuration change...")
    config.update_config({"api.timeout": 75})

    print("Updated API Timeout:", config.get("api.timeout"))

    # Manually trigger reload
    print("Triggering manual reload...")
    config.reload_config()


def example_7_backup_and_restore():
    """Example 7: Configuration backup and restore."""
    print("\n" + "=" * 60)
    print("EXAMPLE 7: Configuration Backup and Restore")
    print("=" * 60)

    config = ConfigManager(environment="development")

    # Create backup
    print("Creating configuration backup...")
    config._create_backup()

    # Get current configuration
    original_timeout = config.get("api.timeout")
    print(f"Original API Timeout: {original_timeout}")

    # Modify configuration
    config.update_config({"api.timeout": 999})
    print(f"Modified API Timeout: {config.get('api.timeout')}")

    # List available backups
    backups = config.get_config_history()
    if backups:
        print(f"Available backups: {len(backups)}")
        latest_backup = backups[0]["timestamp"]
        print(f"Latest backup: {latest_backup}")

        # Restore from backup
        print("Restoring from backup...")
        success = config.rollback_to_backup(latest_backup)
        if success:
            print(f"Restored API Timeout: {config.get('api.timeout')}")
        else:
            print("Failed to restore from backup")
    else:
        print("No backups available")


def example_8_export_configuration():
    """Example 8: Export configuration."""
    print("\n" + "=" * 60)
    print("EXAMPLE 8: Export Configuration")
    print("=" * 60)

    config = ConfigManager(environment="development")

    # Export to YAML
    yaml_file = "config_export_example.yaml"
    config.export_config(yaml_file, format="yaml", include_secrets=False)
    print(f"Configuration exported to {yaml_file}")

    # Export to JSON with secrets
    json_file = "config_export_example.json"
    config.export_config(json_file, format="json", include_secrets=True)
    print(f"Configuration exported to {json_file}")

    # Show file sizes
    yaml_path = Path(yaml_file)
    json_path = Path(json_file)

    if yaml_path.exists():
        print(f"YAML file size: {yaml_path.stat().st_size} bytes")
    if json_path.exists():
        print(f"JSON file size: {json_path.stat().st_size} bytes")

    # Clean up
    for file_path in [yaml_path, json_path]:
        if file_path.exists():
            file_path.unlink()


def example_9_context_manager():
    """Example 9: Using configuration manager with context manager."""
    print("\n" + "=" * 60)
    print("EXAMPLE 9: Context Manager Usage")
    print("=" * 60)

    try:
        with ConfigManager(environment="development") as config:
            print("Configuration loaded in context manager")
            print(f"Database Host: {config.get('database.host')}")
            print(f"Trading Enabled: {config.get('trading.enabled')}")
            print(f"System Version: {config.get('system.version')}")

        print("Configuration manager automatically cleaned up")
    except Exception as e:
        print(f"Error in context manager: {e}")


def example_10_custom_configuration():
    """Example 10: Creating custom configuration objects."""
    print("\n" + "=" * 60)
    print("EXAMPLE 10: Custom Configuration Objects")
    print("=" * 60)

    # Create custom database configuration
    db_config = DatabaseConfig(
        host="custom - db.example.com",
        port=5432,
        name="custom_quant",
        user="custom_user",
        password="custom_password",
        pool_size=25,
        ssl_mode="require",
    )

    print("Custom Database Configuration:")
    print(f"  Host: {db_config.host}")
    print(f"  URL: {db_config.url}")
    print(f"  Pool Size: {db_config.pool_size}")
    print(f"  SSL Mode: {db_config.ssl_mode}")

    # Create custom trading configuration
    trading_config = TradingConfig(
        enabled=True,
        environment="PROD",
        max_position_size=500000,
        risk_limit=0.015,
        risk_free_rate=0.04,
        default_sharpe_threshold=1.5,
    )

    print("\nCustom Trading Configuration:")
    print(f"  Environment: {trading_config.environment}")
    print(f"  Max Position: ${trading_config.max_position_size:,.2f}")
    print(f"  Risk Limit: {trading_config.risk_limit:.1%}")
    print(f"  Risk - Free Rate: {trading_config.risk_free_rate:.1%}")


def main():
    """Run all examples."""
    print("🚀 Hong Kong Quantitative Trading System - Configuration Examples")
    print("=" * 80)

    try:
        example_1_basic_usage()
        example_2_environment_specific()
        example_3_configuration_updates()
        example_4_validation()
        example_5_environment_variables()
        example_6_hot_reload()
        example_7_backup_and_restore()
        example_8_export_configuration()
        example_9_context_manager()
        example_10_custom_configuration()

        print("\n" + "=" * 80)
        print("✅ All examples completed successfully!")

    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
