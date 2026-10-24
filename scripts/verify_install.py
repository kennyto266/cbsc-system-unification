#!/usr/bin/env python3
"""
CBSC Strategy Workflow Installation Verification Script

This script verifies that the installation is correct and all components are working.
It checks package imports, configuration files, and runs basic functionality tests.
"""

import sys
import os
from pathlib import Path
from typing import List, Tuple
import importlib

# ANSI colors for terminal output
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

def print_header(text: str) -> None:
    """Print a formatted header."""
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.BLUE}{Colors.BOLD}{text.center(60)}{Colors.RESET}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'=' * 60}{Colors.RESET}\n")

def print_success(text: str) -> None:
    """Print a success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")

def print_error(text: str) -> None:
    """Print an error message."""
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")

def print_warning(text: str) -> None:
    """Print a warning message."""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.RESET}")

def print_info(text: str) -> None:
    """Print an info message."""
    print(f"  {text}")

class InstallationVerifier:
    """Verifies the CBSC Strategy Workflow installation."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.failures: List[str] = []
        self.warnings: List[str] = []

    def check_python_version(self) -> bool:
        """Check Python version requirement."""
        print_header("Checking Python Version")

        version = sys.version_info
        version_str = f"{version.major}.{version.minor}.{version.micro}"

        print_info(f"Detected Python {version_str}")

        if version.major < 3 or (version.major == 3 and version.minor < 10):
            print_error(f"Python 3.10+ required, found {version_str}")
            self.failures.append("Python version < 3.10")
            return False

        print_success(f"Python version OK ({version_str} >= 3.10)")
        return True

    def check_package_imports(self) -> bool:
        """Check that core packages can be imported."""
        print_header("Checking Package Imports")

        # Required packages
        required_packages = [
            "pandas",
            "numpy",
            "matplotlib",
            "plotly",
            "scipy",
            "sklearn",
            "yaml",
            "jupyter",
        ]

        # Optional packages
        optional_packages = [
            "talib",
            "quantstats",
            "tensorflow",
            "torch",
        ]

        all_ok = True

        for package in required_packages:
            try:
                importlib.import_module(package)
                print_success(f"{package}")
            except ImportError as e:
                print_error(f"{package} - {e}")
                self.failures.append(f"Missing required package: {package}")
                all_ok = False

        for package in optional_packages:
            try:
                importlib.import_module(package)
                print_success(f"{package} (optional)")
            except ImportError:
                print_warning(f"{package} (optional, not installed)")
                self.warnings.append(f"Optional package not installed: {package}")

        if all_ok:
            print_success("All required packages importable")

        return all_ok

    def check_cbsc_package(self) -> bool:
        """Check CBSC Strategy package structure."""
        print_header("Checking CBSC Strategy Package")

        package_ok = True

        # Check if package can be imported
        try:
            import cbsc_strategy
            print_success("cbsc_strategy package importable")

            # Get package version
            if hasattr(cbsc_strategy, "__version__"):
                print_info(f"Version: {cbsc_strategy.__version__}")

        except ImportError as e:
            print_error(f"Cannot import cbsc_strategy: {e}")
            self.failures.append("CBSC Strategy package not importable")
            return False

        # Check core modules
        core_modules = [
            "cbsc_strategy.core",
            "cbsc_strategy.indicators",
            "cbsc_strategy.backtest",
            "cbsc_strategy.data",
        ]

        for module in core_modules:
            try:
                importlib.import_module(module)
                print_success(f"{module}")
            except ImportError:
                print_warning(f"{module} not found")
                self.warnings.append(f"Core module not found: {module}")

        return package_ok

    def check_configuration_files(self) -> bool:
        """Check configuration files."""
        print_header("Checking Configuration Files")

        config_ok = True

        # Check for .env file
        if (self.project_root / ".env").exists():
            print_success(".env file exists")
        else:
            print_warning(".env file not found (copy from .env.template)")
            self.warnings.append(".env file missing")

        # Check for config directory
        config_dir = self.project_root / "config"
        if config_dir.exists():
            print_success("config/ directory exists")

            # Check for config.yaml
            if (config_dir / "config.yaml").exists():
                print_success("config/config.yaml exists")
            elif (config_dir / "config.template.yaml").exists():
                print_warning("config/config.yaml not found (template exists)")
                self.warnings.append("config.yaml not created from template")
        else:
            print_warning("config/ directory not found")
            self.warnings.append("config directory missing")

        return config_ok

    def check_directories(self) -> bool:
        """Check required directories."""
        print_header("Checking Project Directories")

        required_dirs = [
            "data/cache",
            "data/raw",
            "data/processed",
            "logs",
            "notebooks",
            "tests",
        ]

        all_exist = True

        for dir_path in required_dirs:
            full_path = self.project_root / dir_path
            if full_path.exists():
                print_success(f"{dir_path}/")
            else:
                print_warning(f"{dir_path}/ not found")
                self.warnings.append(f"Directory not found: {dir_path}")
                all_exist = False

        return all_exist

    def test_basic_functionality(self) -> bool:
        """Test basic functionality."""
        print_header("Testing Basic Functionality")

        try:
            # Test pandas
            import pandas as pd
            df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
            print_success("pandas: DataFrame creation")

            # Test numpy
            import numpy as np
            arr = np.array([1, 2, 3])
            print_success("numpy: Array creation")

            # Test matplotlib (non-interactive backend)
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots()
            ax.plot([1, 2, 3], [1, 2, 3])
            plt.close(fig)
            print_success("matplotlib: Plot creation")

            # Test YAML
            import yaml
            test_data = yaml.safe_dump({"test": "value"})
            print_success("yaml: Serialization")

            print_success("Basic functionality tests passed")
            return True

        except Exception as e:
            print_error(f"Functionality test failed: {e}")
            self.failures.append(f"Functionality test error: {e}")
            return False

    def print_summary(self) -> int:
        """Print verification summary."""
        print_header("Verification Summary")

        if not self.failures:
            print_success("All critical checks passed!")
            if self.warnings:
                print(f"\n{Colors.YELLOW}Warnings:{Colors.RESET}")
                for warning in self.warnings:
                    print_info(f"• {warning}")
            print(f"\n{Colors.GREEN}{Colors.BOLD}Installation verified successfully!{Colors.RESET}")
            return 0
        else:
            print_error("Some checks failed!")
            print(f"\n{Colors.RED}Errors:{Colors.RESET}")
            for failure in self.failures:
                print_info(f"• {failure}")

            if self.warnings:
                print(f"\n{Colors.YELLOW}Warnings:{Colors.RESET}")
                for warning in self.warnings:
                    print_info(f"• {warning}")

            print(f"\n{Colors.RED}{Colors.BOLD}Installation verification failed!{Colors.RESET}")
            print("\nPlease fix the errors above and run this script again.")
            return 1

    def run(self) -> int:
        """Run all verification checks."""
        print(f"{Colors.BLUE}{Colors.BOLD}CBSC Strategy Workflow Installation Verification{Colors.RESET}")

        # Run checks
        self.check_python_version()
        self.check_package_imports()
        self.check_cbsc_package()
        self.check_configuration_files()
        self.check_directories()
        self.test_basic_functionality()

        # Print summary and return exit code
        return self.print_summary()

def main():
    """Main entry point."""
    verifier = InstallationVerifier()
    exit_code = verifier.run()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
