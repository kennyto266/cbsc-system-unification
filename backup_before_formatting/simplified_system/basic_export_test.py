#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Basic Export System Test - No Unicode
"""

import sys
import os
import json
import time
import logging
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_export_manager():
    """Test Export Manager"""
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from src.export.export_manager import ExportManager, ExportRequest

        print("Testing Export Manager...")

        # Initialize export manager
        export_manager = ExportManager()
        print("Export manager initialized successfully")

        # Check supported formats
        formats = export_manager.get_supported_formats()
        print(f"Supported formats: {formats}")

        # Test data
        test_data = {
            'strategy': 'RSI_MEAN_REVERSION',
            'symbol': '0700.HK',
            'summary': {
                'total_return': 0.156,
                'sharpe_ratio': 1.23,
                'max_drawdown': -0.085
            }
        }

        # Test JSON export
        request = ExportRequest(
            data=test_data,
            format='json',
            filename='test_export'
        )

        result = export_manager.export(request)

        if result.success:
            print(f"JSON export successful: {result.file_path}")
            print(f"File size: {result.file_size} bytes")

            # Verify file exists
            if Path(result.file_path).exists():
                print("File exists on disk")
            else:
                print("Warning: File not found on disk")

            return True
        else:
            print(f"JSON export failed: {result.error_message}")
            return False

    except Exception as e:
        print(f"Export manager test failed: {e}")
        logger.error(f"Export manager test failed: {e}")
        return False

def test_excel_export():
    """Test Excel export"""
    try:
        from src.export.export_manager import ExportManager, ExportRequest

        print("Testing Excel export...")
        export_manager = ExportManager()

        # Create test DataFrame
        df = pd.DataFrame({
            'date': pd.date_range('2023-01-01', periods=10),
            'price': np.random.uniform(400, 600, 10),
            'volume': np.random.randint(1000000, 5000000, 10)
        })

        request = ExportRequest(
            data=df,
            format='xlsx',
            filename='test_excel_export'
        )

        result = export_manager.export(request)

        if result.success:
            print(f"Excel export successful: {result.file_path}")

            # Verify file exists
            if Path(result.file_path).exists():
                print("Excel file exists on disk")
            else:
                print("Warning: Excel file not found on disk")

            return True
        else:
            print(f"Excel export failed: {result.error_message}")
            return False

    except Exception as e:
        print(f"Excel export test failed: {e}")
        logger.error(f"Excel export test failed: {e}")
        return False

def test_csv_export():
    """Test CSV export"""
    try:
        from src.export.export_manager import ExportManager, ExportRequest

        print("Testing CSV export...")
        export_manager = ExportManager()

        # Create test DataFrame
        df = pd.DataFrame({
            'symbol': ['0700.HK', '0941.HK', '1398.HK'],
            'price': [450.5, 85.2, 3.8],
            'volume': [1000000, 2000000, 5000000]
        })

        request = ExportRequest(
            data=df,
            format='csv',
            filename='test_csv_export'
        )

        result = export_manager.export(request)

        if result.success:
            print(f"CSV export successful: {result.file_path}")

            # Verify file exists
            if Path(result.file_path).exists():
                print("CSV file exists on disk")
            else:
                print("Warning: CSV file not found on disk")

            return True
        else:
            print(f"CSV export failed: {result.error_message}")
            return False

    except Exception as e:
        print(f"CSV export test failed: {e}")
        logger.error(f"CSV export test failed: {e}")
        return False

def main():
    """Main test function"""
    print("Basic Export System Test")
    print("=" * 50)

    tests = [
        ("Export Manager", test_export_manager),
        ("Excel Export", test_excel_export),
        ("CSV Export", test_csv_export)
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