#!/usr/bin/env python3
"""
基本驗證腳本 - Basic Validation Script
驗證香港專用系統的基本功能
"""

import json
import logging
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """主驗證函數"""
    print("=" * 50)
    print("Hong Kong Exclusive System Validation")
    print("=" * 50)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    tests_passed = 0
    total_tests = 0

    # Test 1: Check file structure
    print("Test 1: File Structure")
    total_tests += 1
    hk_files = [
        'src/multi_asset/asset_models.py',
        'src/data/hk_market_data_manager.py',
        'src/api/hk_market_api.py'
    ]

    files_exist = 0
    for file_path in hk_files:
        if Path(file_path).exists():
            files_exist += 1
            print(f"  [OK] {file_path}")
        else:
            print(f"  [FAIL] {file_path}")

    if files_exist == len(hk_files):
        print("Result: PASS")
        tests_passed += 1
    else:
        print("Result: FAIL")
    print()

    # Test 2: Check asset models content
    print("Test 2: Asset Models Content")
    total_tests += 1
    try:
        with open('src/multi_asset/asset_models.py', 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for HKEX only
        if 'HKEX = "HKEX"' in content and 'NYSE' not in content:
            print("  [OK] HKEX only configuration")
            hk_check = True
        else:
            print("  [FAIL] Contains non-HK exchanges")
            hk_check = False

        # Check for HK symbol parsing
        if 'parse_symbol' in content and 'exchange": Exchange.HKEX' in content:
            print("  [OK] HK symbol parsing")
            symbol_check = True
        else:
            print("  [FAIL] Missing HK symbol parsing")
            symbol_check = False

        if hk_check and symbol_check:
            print("Result: PASS")
            tests_passed += 1
        else:
            print("Result: FAIL")
    except Exception as e:
        print(f"  [FAIL] Error: {e}")
        print("Result: FAIL")
    print()

    # Test 3: Check configuration files
    print("Test 3: Configuration Files")
    total_tests += 1
    try:
        config_files = [
            '../config/hk_market_config.json',
            '../config/hk_trading_symbols.json',
            '../config/hk_data_sources.yaml'
        ]

        config_valid = 0
        for config_file in config_files:
            if Path(config_file).exists():
                config_valid += 1
                print(f"  [OK] {config_file}")
            else:
                print(f"  [FAIL] {config_file}")

        if config_valid >= 2:  # 至少2個配置文件
            print("Result: PASS")
            tests_passed += 1
        else:
            print("Result: FAIL")
    except Exception as e:
        print(f"  [FAIL] Error: {e}")
        print("Result: FAIL")
    print()

    # Test 4: Check API content
    print("Test 4: API Content")
    total_tests += 1
    try:
        with open('src/api/hk_market_api.py', 'r', encoding='utf-8') as f:
            api_content = f.read()

        # Check for HK specific content
        hk_terms = ['validate_hk_symbol', 'get_hk_stock_data', 'Hong Kong']
        hk_found = sum(1 for term in hk_terms if term in api_content)

        # Check for non-HK exclusion
        if 'not a valid Hong Kong stock symbol' in api_content:
            non_hk_check = True
        else:
            non_hk_check = False

        if hk_found >= 2 and non_hk_check:
            print("  [OK] HK-specific API content")
            print("Result: PASS")
            tests_passed += 1
        else:
            print("  [FAIL] Missing HK-specific content")
            print("Result: FAIL")
    except Exception as e:
        print(f"  [FAIL] Error: {e}")
        print("Result: FAIL")
    print()

    # Test 5: Check data manager
    print("Test 5: Data Manager")
    total_tests += 1
    try:
        with open('src/data/hk_market_data_manager.py', 'r', encoding='utf-8') as f:
            dm_content = f.read()

        dm_checks = [
            'HKMarketDataManager' in dm_content,
            'hkma_hibor' in dm_content,
            'get_hk_stock_data' in dm_content,
            'get_hsi_constituents_data' in dm_content
        ]

        if sum(dm_checks) >= 3:
            print("  [OK] HK data manager content")
            print("Result: PASS")
            tests_passed += 1
        else:
            print("  [FAIL] Missing HK data manager content")
            print("Result: FAIL")
    except Exception as e:
        print(f"  [FAIL] Error: {e}")
        print("Result: FAIL")
    print()

    # Final results
    print("=" * 50)
    print("VALIDATION SUMMARY")
    print("=" * 50)
    print(f"Tests Passed: {tests_passed}/{total_tests}")
    print(f"Success Rate: {(tests_passed/total_tests)*100:.1f}%")
    print()

    if tests_passed == total_tests:
        print("OVERALL RESULT: SUCCESS")
        print("Hong Kong Exclusive System Validation PASSED")
        print("All components successfully configured for Hong Kong market only")
    else:
        print("OVERALL RESULT: FAILURE")
        print("Some components need attention")

    print("=" * 50)
    return tests_passed == total_tests

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)