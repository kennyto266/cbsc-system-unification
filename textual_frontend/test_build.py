#!/usr/bin/env python3
"""
Textual TUI Build Verification Test
====================================

This script verifies that the Textual TUI application
builds successfully and all accessibility features are in place.
"""

import sys
import os

# Change to script directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test all module imports"""
    print("Testing imports...")
    try:
        from screens.main_screen import MainScreen
        from screens.strategies_screen import StrategyScreen, EditStrategyScreen, ConfirmScreen
        from screens.backtest_screen import BacktestScreen
        from screens.results_screen import ResultsScreen
        from screens.progress_screen import ProgressScreen
        from screens.config_screen import ConfigScreen
        from services.api_client import APIClient
        from utils.logger import TUILogger
        from main import TradingApp
        return True, "All imports successful"
    except Exception as e:
        return False, f"Import failed: {e}"

def test_accessibility():
    """Test accessibility features"""
    print("\nTesting accessibility features...")
    from screens.main_screen import MainScreen
    from screens.strategies_screen import StrategyScreen, EditStrategyScreen, ConfirmScreen
    from screens.backtest_screen import BacktestScreen
    from screens.results_screen import ResultsScreen
    from screens.progress_screen import ProgressScreen
    from screens.config_screen import ConfigScreen

    screens = [
        MainScreen, StrategyScreen, EditStrategyScreen, ConfirmScreen,
        BacktestScreen, ResultsScreen, ProgressScreen, ConfigScreen
    ]

    results = []
    for screen in screens:
        has_desc = hasattr(screen, 'SCREEN_DESCRIPTION')
        results.append((screen.__name__, has_desc))

    all_pass = all(r[1] for r in results)
    return all_pass, results

def test_bindings():
    """Test keyboard bindings"""
    print("\nTesting keyboard bindings...")
    from screens.main_screen import MainScreen
    from screens.strategies_screen import EditStrategyScreen
    from screens.config_screen import ConfigScreen

    results = []

    # Check help bindings
    has_main_help = any('show_help' in str(b) for b in MainScreen.BINDINGS)
    results.append(("MainScreen help binding", has_main_help))

    has_field_help = any('field_help' in str(b) for b in EditStrategyScreen.BINDINGS)
    results.append(("EditStrategyScreen field_help binding", has_field_help))

    has_config_help = any('field_help' in str(b) for b in ConfigScreen.BINDINGS)
    results.append(("ConfigScreen field_help binding", has_config_help))

    all_pass = all(r[1] for r in results)
    return all_pass, results

def test_api_client():
    """Test API client"""
    print("\nTesting API client...")
    try:
        from services.api_client import APIClient
        client = APIClient()
        return True, f"APIClient initialized (base_url: {client.base_url})"
    except Exception as e:
        return False, f"APIClient failed: {e}"

def main():
    """Run all tests"""
    print("="*60)
    print("Textual TUI Build Verification")
    print("="*60)

    tests = [
        ("Module Imports", test_imports),
        ("Accessibility Features", test_accessibility),
        ("Keyboard Bindings", test_bindings),
        ("API Client", test_api_client),
    ]

    all_passed = True
    for name, test_func in tests:
        try:
            passed, result = test_func()
            if passed:
                print(f"[PASS] {name}")
            else:
                print(f"[FAIL] {name}")
                all_passed = False
                if isinstance(result, list):
                    for item in result:
                        status = "PASS" if item[1] else "FAIL"
                        print(f"  - {item[0]}: {status}")
                else:
                    print(f"  {result}")
        except Exception as e:
            print(f"[ERROR] {name}: {e}")
            all_passed = False

    print("\n" + "="*60)
    if all_passed:
        print("BUILD SUCCESS: All tests passed!")
        print("The Textual TUI application is ready to use.")
        print("\nTo run the application:")
        print("  python main.py")
        print("  or")
        print("  python run.py")
        return 0
    else:
        print("BUILD FAILED: Some tests did not pass.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
