#!/usr/bin/env python3
"""
Test runner script for persistent-context-storage
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    """Run the test suite"""
    # Ensure we're in the right directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    # Check if pytest is available
    try:
        import pytest
    except ImportError:
        print("Error: pytest is not installed. Please install it with:")
        print("pip install pytest pytest-asyncio pytest-cov")
        sys.exit(1)

    # Run unit tests only for now
    test_args = [
        "pytest",
        "tests/unit/",
        "-v",
        "--tb=short",
        "--disable-warnings"
    ]

    # Add coverage if requested
    if "--cov" in sys.argv:
        test_args.extend([
            "--cov=services",
            "--cov-report=term-missing",
            "--cov-fail-under=70"
        ])

    # Run the tests
    print("Running unit tests for persistent-context-storage...")
    print("=" * 60)

    result = subprocess.run(test_args, capture_output=False)

    # Return the exit code
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()