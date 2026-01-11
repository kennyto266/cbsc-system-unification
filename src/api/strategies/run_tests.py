#!/usr/bin/env python3
"""
Strategy Module Test Runner
策略模块测试运行器

This script runs tests for the strategy module in isolation,
avoiding dependency issues with the main project's conftest.py.
这个脚本独立运行策略模块的测试，避免与主项目的conftest.py产生依赖问题。

Usage:
    python run_tests.py              # Run all tests
    python run_tests.py -v           # Verbose output
    python run_tests.py --coverage   # Run with coverage
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path


def run_tests(args):
    """Run tests with the specified options"""
    # Change to the strategy module directory
    strategy_dir = Path(__file__).parent
    os.chdir(strategy_dir)

    # Build pytest command
    cmd = ["python", "-m", "pytest", "tests/"]

    if args.verbose:
        cmd.append("-v")

    if args.coverage:
        cmd.extend([
            "--cov=.",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov"
        ])

    if args.file:
        cmd.append(args.file)

    if args.marker:
        cmd.extend(["-m", args.marker])

    if args.keyword:
        cmd.extend(["-k", args.keyword])

    # Add PYTEST_DISABLE_PLUGIN_AUTOLOAD to avoid loading plugins that might cause issues
    env = os.environ.copy()
    env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"

    print(f"Running command: {' '.join(cmd)}")
    print(f"Working directory: {strategy_dir}")
    print("-" * 50)

    try:
        result = subprocess.run(cmd, env=env, check=False)
        return result.returncode
    except FileNotFoundError:
        print("Error: pytest not found. Please install pytest:")
        print("pip install pytest pytest-asyncio pytest-cov")
        return 1


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Run strategy module tests")

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )

    parser.add_argument(
        "-c", "--coverage",
        action="store_true",
        help="Run with coverage report"
    )

    parser.add_argument(
        "-f", "--file",
        help="Run specific test file"
    )

    parser.add_argument(
        "-m", "--marker",
        help="Run tests with specific marker (e.g., unit, integration)"
    )

    parser.add_argument(
        "-k", "--keyword",
        help="Run tests matching keyword"
    )

    args = parser.parse_args()

    # Check if we're in a virtual environment
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("Warning: Not in a virtual environment. It's recommended to use a virtual environment.")

    # Run tests
    exit_code = run_tests(args)

    if exit_code == 0:
        print("\n[SUCCESS] All tests passed!")
    else:
        print(f"\n[FAILED] Tests failed with exit code {exit_code}")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()