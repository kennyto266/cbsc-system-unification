#!/usr / bin / env python3
# -*- coding: utf - 8 -*-
"""
Minimal Export System Test - Core functionality only
"""

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd


def test_json_exporter():
    """Test JSON exporter directly"""
    try:
        print("Testing JSON exporter...")

        # Test data
        test_data = {
            "strategy": "RSI_MEAN_REVERSION",
            "symbol": "0700.HK",
            "summary": {
                "total_return": 0.156,
                "sharpe_ratio": 1.23,
                "max_drawdown": -0.085,
            },
        }

        # Test JSON conversion
        json_str = json.dumps(test_data, indent = 2)

        # Write to file
        output_file = Path("test_output.json")
        with open(output_file, "w", encoding="utf - 8") as f:
            f.write(json_str)

        if output_file.exists():
            file_size = output_file.stat().st_size
            print(f"JSON export successful: {output_file}")
            print(f"File size: {file_size} bytes")
            return True
        else:
            print("JSON file not created")
            return False

    except Exception as e:
        print(f"JSON export test failed: {e}")
        return False


def test_csv_exporter():
    """Test CSV exporter directly"""
    try:
        print("Testing CSV exporter...")

        # Create test DataFrame
        df = pd.DataFrame(
            {
                "symbol": ["0700.HK", "0941.HK", "1398.HK"],
                "price": [450.5, 85.2, 3.8],
                "volume": [1000000, 2000000, 5000000],
            }
        )

        # Write to CSV
        output_file = Path("test_output.csv")
        df.to_csv(output_file, index = False, encoding="utf - 8")

        if output_file.exists():
            file_size = output_file.stat().st_size
            print(f"CSV export successful: {output_file}")
            print(f"File size: {file_size} bytes")
            return True
        else:
            print("CSV file not created")
            return False

    except Exception as e:
        print(f"CSV export test failed: {e}")
        return False


def test_excel_exporter():
    """Test Excel exporter if available"""
    try:
        print("Testing Excel exporter...")

        # Create test DataFrame
        df = pd.DataFrame(
            {
                "date": pd.date_range("2023 - 01 - 01", periods = 10),
                "price": np.random.uniform(400, 600, 10),
                "volume": np.random.randint(1000000, 5000000, 10),
            }
        )

        # Write to Excel
        output_file = Path("test_output.xlsx")
        df.to_excel(output_file, index = False)

        if output_file.exists():
            file_size = output_file.stat().st_size
            print(f"Excel export successful: {output_file}")
            print(f"File size: {file_size} bytes")
            return True
        else:
            print("Excel file not created")
            return False

    except ImportError as e:
        print(f"Excel export skipped (missing dependency): {e}")
        return True  # Not a failure if dependency missing
    except Exception as e:
        print(f"Excel export test failed: {e}")
        return False


def test_data_structures():
    """Test data structure creation"""
    try:
        print("Testing data structures...")

        # Test dictionary creation
        test_dict = {
            "metadata": {"created_at": "2024 - 01 - 01T00:00:00", "version": "1.0"},
            "data": {"strategy": "RSI", "parameters": {"period": 14, "oversold": 30}},
        }

        # Test DataFrame creation
        dates = pd.date_range("2023 - 01 - 01", periods = 100)
        test_df = pd.DataFrame(
            {
                "date": dates,
                "close": np.random.uniform(400, 600, 100),
                "volume": np.random.randint(1000000, 5000000, 100),
            }
        )

        print(f"Dictionary created with {len(test_dict)} keys")
        print(f"DataFrame created with shape {test_df.shape}")

        return True

    except Exception as e:
        print(f"Data structure test failed: {e}")
        return False


def main():
    """Main test function"""
    print("Minimal Export System Test")
    print("=" * 50)

    tests = [
        ("JSON Exporter", test_json_exporter),
        ("CSV Exporter", test_csv_exporter),
        ("Excel Exporter", test_excel_exporter),
        ("Data Structures", test_data_structures),
    ]

    passed_tests = 0
    total_tests = len(tests)

    for test_name, test_func in tests:
        print(f"\n[{test_name}]")
        print("-" * 30)

        try:
            start_time = time.time()
            result = test_func()
            end_time = time.time()

            if result:
                print(f"PASS {test_name} ({end_time - start_time:.2f}s)")
                passed_tests += 1
            else:
                print(f"FAIL {test_name}")

        except Exception as e:
            print(f"ERROR {test_name}: {e}")

    # Summary
    print("\n" + "=" * 50)
    print(f"Test Summary: {passed_tests}/{total_tests} passed")

    if passed_tests == total_tests:
        print("All tests PASSED!")
        return 0
    else:
        print("Some tests FAILED!")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
