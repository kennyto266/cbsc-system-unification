#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Jupyter Notebook Test Script
Check if all necessary dependencies are installed
"""

import sys
import importlib

def check_dependency(module_name, pip_name=None):
    """Check if Python dependency is installed"""
    try:
        importlib.import_module(module_name)
        print(f"[OK] {module_name} - Installed")
        return True
    except ImportError:
        pip_name = pip_name or module_name
        print(f"[FAIL] {module_name} - Not installed (pip install {pip_name})")
        return False

def main():
    print("Checking Jupyter Notebook dependencies...")
    print("=" * 50)

    dependencies = [
        ("pandas", "pandas"),
        ("numpy", "numpy"),
        ("matplotlib", "matplotlib"),
        ("seaborn", "seaborn"),
        ("plotly", "plotly"),
        ("sklearn", "scikit-learn"),
        ("requests", "requests"),
        ("aiohttp", "aiohttp"),
    ]

    failed = []
    for module, pip_name in dependencies:
        if not check_dependency(module, pip_name):
            failed.append(pip_name)

    print("\n" + "=" * 50)

    if failed:
        print(f"[FAIL] Missing {len(failed)} dependencies")
        print(f"[INSTALL] Run: pip install {' '.join(failed)}")
        return False
    else:
        print("[SUCCESS] All dependencies installed!")
        print("[READY] Jupyter Notebook can run normally")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)