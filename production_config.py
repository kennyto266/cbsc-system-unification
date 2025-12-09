#!/usr/bin/env python3
"""
Production Configuration for Refactored System
生產環境配置文件
"""

PRODUCTION_CONFIG = {
    "optimization": {
        "max_workers": 16,
        "max_combinations": 1000,
        "risk_free_rate": 0.03,
        "target_strategies": None,  # None means all strategies
        "target_data_sources": None,  # None means all data sources
        "cache_enabled": True,
        "cache_ttl": 3600  # 1 hour
    },

    "data_sources": {
        "central_api": {
            "base_url": "http://18.180.162.113:9191",
            "endpoint": "/inst/getInst",
            "timeout": 30,
            "retry_attempts": 3,
            "retry_delay": 1.0
        },

        "government_data": {
            "hibor_path": "production_data/government/hibor_data.json",
            "hkma_path": "production_data/government/hkma_data.csv",
            "unified_data_path": "production_data/government/unified_data.csv",
            "fallback_enabled": True
        },

        "stock_data": {
            "default_duration": 1095,  # 3 years
            "cache_enabled": True,
            "validate_data": True,
            "min_data_points": 100
        }
    },

    "results": {
        "output_dir": "production_data/results/",
        "backup_enabled": True,
        "backup_dir": "production_data/backups/",
        "save_intermediate": False,
        "format": "json",
        "compression": False
    },

    "monitoring": {
        "log_level": "INFO",
        "log_file": "production_data/logs/production.log",
        "metrics_enabled": True,
        "performance_tracking": True,
        "error_alerting": True
    },

    "quality_assurance": {
        "sharpe_ratio_validation": True,
        "sharpe_expected_range": (0.5, 3.0),
        "min_data_quality_score": 0.8,
        "max_drawdown_threshold": -0.5,
        "require_minimum_trades": 10
    },

    "system": {
        "environment": "production",
        "debug_mode": False,
        "concurrent_optimizations": False,
        "memory_limit_mb": 4096,
        "cpu_limit_percent": 80
    }
}


class ProductionDataValidator:
    """Production data quality validator"""

    @staticmethod
    def validate_sharpe_ratio(sharpe_ratio: float) -> bool:
        """Validate Sharpe ratio is in expected range"""
        min_sharpe, max_sharpe = PRODUCTION_CONFIG["quality_assurance"]["sharpe_expected_range"]
        return min_sharpe <= sharpe_ratio <= max_sharpe

    @staticmethod
    def validate_strategy_results(results: dict) -> bool:
        """Validate strategy results meet quality standards"""
        required_fields = ['strategy_id', 'sharpe_ratio', 'total_return', 'max_drawdown']
        return all(field in results for field in required_fields)

    @staticmethod
    def validate_data_quality(data_points: int, min_required: int = 100) -> bool:
        """Validate sufficient data points for analysis"""
        return data_points >= min_required


class ProductionErrorHandler:
    """Production error handling and recovery"""

    @staticmethod
    def handle_api_error(error: Exception, retry_count: int = 0) -> bool:
        """Handle API connectivity errors"""
        if retry_count < PRODUCTION_CONFIG["data_sources"]["central_api"]["retry_attempts"]:
            import time
            time.sleep(PRODUCTION_CONFIG["data_sources"]["central_api"]["retry_delay"])
            return True  # Retry
        return False  # Give up

    @staticmethod
    def handle_data_error(error: Exception, data_source: str) -> None:
        """Handle data fetching errors"""
        import logging
        logging.error(f"Data error in {data_source}: {error}")

        # Enable fallback data if available
        if PRODUCTION_CONFIG["data_sources"]["government_data"]["fallback_enabled"]:
            logging.info(f"Attempting fallback data for {data_source}")


def get_production_config():
    """Get production configuration"""
    return PRODUCTION_CONFIG


def validate_production_environment():
    """Validate production environment is ready"""
    import os
    from pathlib import Path

    issues = []

    # Check required directories
    required_dirs = [
        "production_data/stock",
        "production_data/government",
        "production_data/results",
        "production_data/logs",
        "production_data/backups"
    ]

    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            issues.append(f"Missing directory: {dir_path}")

    # Check configuration validity
    if PRODUCTION_CONFIG["optimization"]["max_workers"] < 1:
        issues.append("Invalid max_workers configuration")

    if PRODUCTION_CONFIG["optimization"]["risk_free_rate"] < 0:
        issues.append("Invalid risk_free_rate configuration")

    return issues


if __name__ == "__main__":
    # Validate production environment
    issues = validate_production_environment()

    if issues:
        print("Production Environment Issues:")
        for issue in issues:
            print(f"  - {issue}")
        exit(1)
    else:
        print("[OK] Production environment is ready")
        print(f"Configuration loaded with {len(PRODUCTION_CONFIG)} sections")