#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup Test Environment for Issue #22
设置测试环境 - Issue #22阶段

Install dependencies and prepare for API testing
安装依赖并准备API测试
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Run command and display result"""
    print(f"\n[{description}]")
    print(f"Running: {command}")

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            print("✓ Success")
            if result.stdout:
                print(f"Output: {result.stdout[:200]}...")
        else:
            print("✗ Failed")
            if result.stderr:
                print(f"Error: {result.stderr[:200]}...")

        return result.returncode == 0

    except subprocess.TimeoutExpired:
        print("✗ Timeout (60s)")
        return False
    except Exception as e:
        print(f"✗ Exception: {e}")
        return False

def check_python_version():
    """Check Python version compatibility"""
    print("Checking Python version...")
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")

    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("✗ Python 3.8+ is required")
        return False
    else:
        print("✓ Python version is compatible")
        return True

def check_project_structure():
    """Check project structure"""
    print("\nChecking project structure...")

    required_dirs = [
        "src",
        "src/api",
        "src/api/strategies",
        "src/api/strategies/services",
        "src/api/strategies/utils",
        "src/api/strategies/repositories"
    ]

    all_exist = True
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"  ✓ {dir_path}")
        else:
            print(f"  ✗ {dir_path} - Missing")
            all_exist = False

    return all_exist

def main():
    """Main setup process"""
    print("=" * 60)
    print("SETUP TEST ENVIRONMENT - Issue #22")
    print("=" * 60)

    # Check prerequisites
    if not check_python_version():
        sys.exit(1)

    if not check_project_structure():
        print("\n✗ Project structure incomplete")
        print("Please ensure all required directories exist")
        sys.exit(1)

    print("\n✓ Project structure is valid")

    # Install dependencies
    dependencies = [
        ("pip install --upgrade pip", "Upgrade pip"),
        ("pip install httpx", "Install HTTP client for testing"),
        ("pip install pytest", "Install testing framework"),
        ("pip install pytest-asyncio", "Install async testing support"),
        ("pip install pydantic", "Install data validation library"),
        ("pip install fastapi", "Install FastAPI framework"),
    ]

    success_count = 0
    for command, description in dependencies:
        if run_command(command, description):
            success_count += 1

    print(f"\n{'='*60}")
    print(f"SETUP COMPLETE: {success_count}/{len(dependencies)} tasks completed")

    if success_count == len(dependencies):
        print("✓ All dependencies installed successfully")
        print("\nNext steps:")
        print("1. Start the API server: cd src/api && python -m uvicorn main:app --reload --port 3004")
        print("2. Run the test suite: python test_api_suite.py")
        print("3. Review test results and address any issues")
        print("4. Proceed with deployment preparation")
    else:
        print("✗ Some dependencies failed to install")
        print("Please resolve the issues above before proceeding")

    print(f"{'='*60}")

if __name__ == "__main__":
    main()