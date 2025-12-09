#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Export System Test
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
        print("✓ Export manager initialized")

        # Check supported formats
        formats = export_manager.get_supported_formats()
        print(f"✓ Supported formats: {formats}")

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
            print(f"✓ JSON export successful: {result.file_path}")
            print(f"  File size: {result.file_size} bytes")
        else:
            print(f"✗ JSON export failed: {result.error_message}")
            return False

        # Test Excel export
        request = ExportRequest(
            data=pd.DataFrame(test_data),
            format='xlsx',
            filename='test_excel_export'
        )

        result = export_manager.export(request)

        if result.success:
            print(f"✓ Excel export successful: {result.file_path}")
        else:
            print(f"✗ Excel export failed: {result.error_message}")

        # Test CSV export
        request = ExportRequest(
            data=pd.DataFrame(test_data),
            format='csv',
            filename='test_csv_export'
        )

        result = export_manager.export(request)

        if result.success:
            print(f"✓ CSV export successful: {result.file_path}")
        else:
            print(f"✗ CSV export failed: {result.error_message}")

        return True

    except Exception as e:
        print(f"✗ Export manager test failed: {e}")
        logger.error(f"Export manager test failed: {e}")
        return False

def test_html_export():
    """Test HTML export"""
    try:
        from src.export.export_manager import ExportManager, ExportRequest

        print("Testing HTML export...")
        export_manager = ExportManager()

        # Create test backtest data
        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        test_data = {
            'summary': {
                'total_return': 0.156,
                'annual_return': 0.142,
                'sharpe_ratio': 1.23,
                'max_drawdown': -0.085,
                'volatility': 0.186,
                'win_rate': 0.58
            },
            'performance_metrics': {
                'sortino_ratio': 1.67,
                'calmar_ratio': 1.95,
                'profit_factor': 1.34
            },
            'trades': pd.DataFrame([
                {'date': '2023-01-01', 'action': 'BUY', 'price': 450.5, 'quantity': 100},
                {'date': '2023-01-15', 'action': 'SELL', 'price': 475.2, 'quantity': 100}
            ])
        }

        request = ExportRequest(
            data=test_data,
            format='html',
            filename='test_html_export',
            options={'include_charts': False}  # Disable charts for testing
        )

        result = export_manager.export(request)

        if result.success:
            print(f"✓ HTML export successful: {result.file_path}")
            return True
        else:
            print(f"✗ HTML export failed: {result.error_message}")
            return False

    except Exception as e:
        print(f"✗ HTML export test failed: {e}")
        logger.error(f"HTML export test failed: {e}")
        return False

def test_pdf_export():
    """Test PDF export (if available)"""
    try:
        from src.export.export_manager import ExportManager, ExportRequest

        print("Testing PDF export...")
        export_manager = ExportManager()

        # Check if PDF exporter is available
        if export_manager.pdf_exporter is None:
            print("⚠ PDF exporter not available, skipping PDF test")
            return True

        test_data = {
            'title': 'Test Report',
            'content': 'This is a test PDF export.',
            'summary': {
                'total_return': 0.156,
                'sharpe_ratio': 1.23
            }
        }

        request = ExportRequest(
            data=test_data,
            format='pdf',
            filename='test_pdf_export'
        )

        result = export_manager.export(request)

        if result.success:
            print(f"✓ PDF export successful: {result.file_path}")
            return True
        else:
            print(f"✗ PDF export failed: {result.error_message}")
            return False

    except Exception as e:
        print(f"✗ PDF export test failed: {e}")
        logger.error(f"PDF export test failed: {e}")
        return False

def test_batch_export():
    """Test batch export"""
    try:
        from src.export.export_manager import ExportManager, ExportRequest

        print("Testing batch export...")
        export_manager = ExportManager()

        # Create multiple export requests
        requests = []
        for i in range(3):
            test_data = {
                'batch_id': i,
                'data': list(range(10 + i))
            }

            request = ExportRequest(
                data=test_data,
                format='json',
                filename=f'test_batch_{i}'
            )
            requests.append(request)

        # Execute batch export
        results = export_manager.batch_export(requests)

        # Check results
        success_count = sum(1 for r in results if r.success)
        print(f"✓ Batch export: {success_count}/{len(requests)} successful")

        return success_count == len(requests)

    except Exception as e:
        print(f"✗ Batch export test failed: {e}")
        logger.error(f"Batch export test failed: {e}")
        return False

def main():
    """Main test function"""
    print("Simple Export System Test")
    print("=" * 50)

    tests = [
        ("Export Manager", test_export_manager),
        ("HTML Export", test_html_export),
        ("PDF Export", test_pdf_export),
        ("Batch Export", test_batch_export)
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
        print("All tests PASSED! ✓")
        return 0
    else:
        print("Some tests FAILED! ✗")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)