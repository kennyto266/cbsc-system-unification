#!/usr/bin/env python3
"""
Security Fixes Deployment Script
Automatically deploys and validates security fixes for the quantitative trading system
"""

import os
import sys
import logging
import json
from datetime import datetime
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.security.security_fixes import apply_security_patches
from src.security.security_config import validate_environment, get_security_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SecurityDeploymentManager:
    """Manages the deployment of security fixes"""

    def __init__(self):
        self.deployment_log = []
        self.errors = []
        self.warnings = []

    def log_deployment_step(self, step: str, status: str, details: str = None):
        """Log a deployment step"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'step': step,
            'status': status,
            'details': details
        }
        self.deployment_log.append(entry)

        status_icon = "✅" if status == "SUCCESS" else "❌" if status == "ERROR" else "⚠️"
        logger.info(f"{status_icon} {step}")
        if details:
            logger.info(f"   {details}")

    def check_prerequisites(self) -> bool:
        """Check deployment prerequisites"""
        self.log_deployment_step("Checking Prerequisites", "STARTED")

        try:
            # Check Python version
            if sys.version_info < (3, 8):
                self.errors.append("Python 3.8+ required")
                self.log_deployment_step("Python Version Check", "ERROR", f"Found {sys.version}")
                return False

            # Check required directories
            required_dirs = [
                "src/security",
                "simplified_system/src/backtest",
                "tests/framework"
            ]

            for dir_path in required_dirs:
                if not os.path.exists(dir_path):
                    self.errors.append(f"Required directory missing: {dir_path}")
                    self.log_deployment_step("Directory Check", "ERROR", f"Missing {dir_path}")
                    return False

            # Validate environment
            env_validation = validate_environment()
            if not env_validation['valid']:
                self.errors.extend(env_validation['missing_required'])
                self.log_deployment_step("Environment Validation", "ERROR",
                                       f"Missing: {env_validation['missing_required']}")
                return False

            if env_validation['missing_recommended']:
                self.warnings.extend(env_validation['missing_recommended'])
                self.log_deployment_step("Environment Validation", "WARNING",
                                       f"Missing recommended: {env_validation['missing_recommended']}")

            self.log_deployment_step("Checking Prerequisites", "SUCCESS")
            return True

        except Exception as e:
            self.errors.append(f"Prerequisites check failed: {e}")
            self.log_deployment_step("Checking Prerequisites", "ERROR", str(e))
            return False

    def validate_syntax_fixes(self) -> bool:
        """Validate that syntax errors have been fixed"""
        self.log_deployment_step("Validating Syntax Fixes", "STARTED")

        try:
            # Test the previously problematic file
            import tests.framework.utils

            # Test the SecurityValidator class
            from src.security.security_fixes import SecurityValidator

            # Test basic validation
            symbol = SecurityValidator.validate_stock_symbol("0700.HK")
            if symbol != "0700.HK":
                self.errors.append("Stock symbol validation failed")
                return False

            self.log_deployment_step("Validating Syntax Fixes", "SUCCESS")
            return True

        except Exception as e:
            self.errors.append(f"Syntax validation failed: {e}")
            self.log_deployment_step("Validating Syntax Fixes", "ERROR", str(e))
            return False

    def test_security_features(self) -> bool:
        """Test core security features"""
        self.log_deployment_step("Testing Security Features", "STARTED")

        try:
            from src.security.security_fixes import (
                SecurityValidator, SecureConfigManager,
                SecureFileOperations, SecurityLogger
            )

            # Test SQL injection protection
            try:
                SecurityValidator.sanitize_sql_input("'; DROP TABLE users; --")
                self.errors.append("SQL injection protection not working")
                return False
            except ValueError:
                pass  # Expected behavior

            # Test filename validation
            try:
                SecurityValidator.validate_filename("../../../etc/passwd")
                self.errors.append("Path traversal protection not working")
                return False
            except ValueError:
                pass  # Expected behavior

            # Test stock symbol validation
            try:
                SecurityValidator.validate_stock_symbol("'; SELECT * FROM users; --")
                self.errors.append("Stock symbol injection protection not working")
                return False
            except ValueError:
                pass  # Expected behavior

            self.log_deployment_step("Testing Security Features", "SUCCESS")
            return True

        except Exception as e:
            self.errors.append(f"Security feature test failed: {e}")
            self.log_deployment_step("Testing Security Features", "ERROR", str(e))
            return False

    def validate_sharpe_calculation(self) -> bool:
        """Validate Sharpe ratio calculation fixes"""
        self.log_deployment_step("Validating Sharpe Calculation", "STARTED")

        try:
            import numpy as np

            # Test the standardized Sharpe calculator
            calculator_path = project_root / "simplified_system" / "src" / "backtest" / "standardized_sharpe_calculator.py"
            if not calculator_path.exists():
                self.errors.append("Standardized Sharpe calculator not found")
                return False

            # Import and test the calculator
            sys.path.insert(0, str(project_root / "simplified_system"))
            from src.backtest.standardized_sharpe_calculator import StandardizedSharpeCalculator

            # Test with sample data
            np.random.seed(42)
            test_returns = np.random.normal(0.001, 0.02, 252)

            calculator = StandardizedSharpeCalculator()
            result = calculator.calculate_sharpe_ratio(test_returns, 'standard')

            # Validate results
            if not isinstance(result, dict) or 'sharpe_ratio' not in result:
                self.errors.append("Sharpe calculator returning invalid format")
                return False

            if abs(result['sharpe_ratio']) > 10:  # Unrealistic Sharpe ratio
                self.errors.append(f"Unrealistic Sharpe ratio: {result['sharpe_ratio']}")
                return False

            self.log_deployment_step("Validating Sharpe Calculation", "SUCCESS",
                                   f"Sharpe: {result['sharpe_ratio']:.3f}")
            return True

        except Exception as e:
            self.errors.append(f"Sharpe calculation validation failed: {e}")
            self.log_deployment_step("Validating Sharpe Calculation", "ERROR", str(e))
            return False

    def apply_security_patches(self) -> bool:
        """Apply security patches to the system"""
        self.log_deployment_step("Applying Security Patches", "STARTED")

        try:
            # Apply patches from the security fixes module
            success = apply_security_patches()
            if not success:
                self.errors.append("Failed to apply security patches")
                return False

            self.log_deployment_step("Applying Security Patches", "SUCCESS")
            return True

        except Exception as e:
            self.errors.append(f"Security patch application failed: {e}")
            self.log_deployment_step("Applying Security Patches", "ERROR", str(e))
            return False

    def generate_deployment_report(self) -> dict:
        """Generate deployment report"""
        config = get_security_config()
        env_validation = validate_environment()

        report = {
            'deployment_timestamp': datetime.now().isoformat(),
            'status': 'SUCCESS' if not self.errors else 'FAILED',
            'deployment_log': self.deployment_log,
            'errors': self.errors,
            'warnings': self.warnings,
            'security_config': {
                'risk_free_rate': config.DEFAULT_RISK_FREE_RATE,
                'trading_days': config.DEFAULT_TRADING_DAYS,
                'max_file_size': config.MAX_FILE_SIZE,
                'allowed_extensions': config.ALLOWED_FILE_EXTENSIONS
            },
            'environment_validation': env_validation
        }

        return report

    def save_deployment_report(self, report: dict):
        """Save deployment report to file"""
        report_file = project_root / f"security_deployment_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)

            logger.info(f"📄 Deployment report saved: {report_file}")

        except Exception as e:
            logger.error(f"Failed to save deployment report: {e}")

    def run_deployment(self) -> bool:
        """Run the complete deployment process"""
        logger.info("🚀 Starting Security Fixes Deployment")

        steps = [
            self.check_prerequisites,
            self.validate_syntax_fixes,
            self.test_security_features,
            self.validate_sharpe_calculation,
            self.apply_security_patches
        ]

        for step in steps:
            if not step():
                logger.error(f"❌ Deployment failed at step: {step.__name__}")
                return False

        logger.info("🎉 Security fixes deployment completed successfully!")
        return True


def main():
    """Main deployment function"""
    print("🔒 Quantitative Trading System Security Fixes Deployment")
    print("=" * 60)

    deployment_manager = SecurityDeploymentManager()

    try:
        # Run deployment
        success = deployment_manager.run_deployment()

        # Generate and save report
        report = deployment_manager.generate_deployment_report()
        deployment_manager.save_deployment_report(report)

        # Print summary
        print("\n" + "=" * 60)
        print("DEPLOYMENT SUMMARY")
        print("=" * 60)
        print(f"Status: {'✅ SUCCESS' if success else '❌ FAILED'}")
        print(f"Steps completed: {len(deployment_manager.deployment_log)}")
        print(f"Errors: {len(deployment_manager.errors)}")
        print(f"Warnings: {len(deployment_manager.warnings)}")

        if deployment_manager.errors:
            print("\n❌ ERRORS:")
            for error in deployment_manager.errors:
                print(f"  - {error}")

        if deployment_manager.warnings:
            print("\n⚠️ WARNINGS:")
            for warning in deployment_manager.warnings:
                print(f"  - {warning}")

        if success:
            print("\n🎉 All security fixes have been successfully deployed!")
            print("The system is now secured against the identified vulnerabilities.")
        else:
            print("\n❌ Deployment failed. Please review the errors above.")
            return 1

    except Exception as e:
        logger.error(f"Deployment failed with exception: {e}", exc_info=True)
        print(f"\n❌ Critical error during deployment: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())