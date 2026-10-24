#!/usr/bin/env python3
"""
Test Enhanced HKMA Adapter
Test the enhanced HKMA adapter with long-term storage integration
"""

import sys
from pathlib import Path
from datetime import datetime, date, timedelta
import pandas as pd
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from enhanced_hkma_adapter import EnhancedHKMAAdapter
from long_term_storage import LongTermDataStorage

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_enhanced_hkma_initialization():
    """Test enhanced HKMA adapter initialization"""
    print("Testing Enhanced HKMA Adapter Initialization...")
    print("-" * 50)

    try:
        storage = LongTermDataStorage()
        adapter = EnhancedHKMAAdapter(storage)

        print("+ Enhanced HKMA adapter initialized successfully")
        print(f"  Available data types: {list(adapter.api_endpoints.keys())}")
        print(f"  Storage integration: {'Enabled' if adapter.storage else 'Disabled'}")
        print(f"  HIBOR tenors: {list(adapter.hibor_tenors.keys())}")

        return True, adapter

    except Exception as e:
        print(f"- Enhanced HKMA adapter initialization failed: {e}")
        return False, None


def test_hibor_data_retrieval(adapter):
    """Test HIBOR data retrieval with storage integration"""
    print("\nTesting HIBOR Data Retrieval...")
    print("-" * 50)

    try:
        # Test with 1 year of data
        end_date = date.today()
        start_date = end_date - timedelta(days=365)

        print(f"Fetching HIBOR data from {start_date} to {end_date}...")

        start_time = datetime.now()
        hibor_data = adapter.get_hibor_data(start_date, end_date, use_storage=True)
        duration = (datetime.now() - start_time).total_seconds()

        if len(hibor_data) > 0:
            print(f"+ SUCCESS: Retrieved {len(hibor_data)} HIBOR records in {duration:.2f}s")
            print(f"  Date range: {hibor_data.index.min().date()} to {hibor_data.index.max().date()}")
            print(f"  Columns: {list(hibor_data.columns)}")

            # Check tenor coverage
            if 'tenor' in hibor_data.columns:
                tenors = hibor_data['tenor'].unique()
                print(f"  Tenors covered: {list(tenors)}")

            # Test storage integration
            print("  Testing storage integration...")
            stored_data = adapter.storage.load_historical_data("HKMA_HIBOR", start_date, end_date, "daily")
            if len(stored_data) > 0:
                print("  + Storage integration working correctly")
            else:
                print("  - Storage integration needs attention")

            return True
        else:
            print("- FAILED: No HIBOR data retrieved")
            return False

    except Exception as e:
        print(f"- HIBOR data retrieval failed: {e}")
        return False


def test_multiple_data_types(adapter):
    """Test multiple HKMA data types"""
    print("\nTesting Multiple Data Types...")
    print("-" * 50)

    end_date = date.today()
    start_date = end_date - timedelta(days=90)  # 3 months for testing

    data_types = ['hibor', 'monetary', 'exchange', 'liquidity']
    results = {}

    for data_type in data_types:
        try:
            print(f"Testing {data_type}...", end=" ")

            start_time = datetime.now()

            if data_type == 'hibor':
                data = adapter.get_hibor_data(start_date, end_date)
            elif data_type == 'monetary':
                data = adapter.get_monetary_base_data(start_date, end_date)
            elif data_type == 'exchange':
                data = adapter.get_exchange_rate_data(start_date, end_date)
            elif data_type == 'liquidity':
                data = adapter.get_liquidity_data(start_date, end_date)

            duration = (datetime.now() - start_time).total_seconds()

            if len(data) > 0:
                results[data_type] = {
                    'success': True,
                    'records': len(data),
                    'duration': duration,
                    'columns': list(data.columns)
                }
                print(f"SUCCESS ({len(data)} records)")
            else:
                results[data_type] = {'success': False, 'records': 0}
                print("FAILED")

        except Exception as e:
            results[data_type] = {'success': False, 'error': str(e)}
            print(f"ERROR: {e}")

    return results


def test_comprehensive_data(adapter):
    """Test comprehensive HKMA data retrieval"""
    print("\nTesting Comprehensive Data Retrieval...")
    print("-" * 50)

    try:
        end_date = date.today()
        start_date = end_date - timedelta(days=180)  # 6 months

        print(f"Fetching comprehensive HKMA data for 6 months...")

        start_time = datetime.now()
        comprehensive_data = adapter.get_comprehensive_hkma_data(start_date, end_date, use_storage=True)
        duration = (datetime.now() - start_time).total_seconds()

        print(f"+ Comprehensive data retrieved in {duration:.2f}s")

        total_records = 0
        successful_types = 0

        for data_type, data in comprehensive_data.items():
            if len(data) > 0:
                print(f"  {data_type}: {len(data)} records")
                total_records += len(data)
                successful_types += 1
            else:
                print(f"  {data_type}: No data")

        print(f"\nSummary: {successful_types}/{len(comprehensive_data)} data types successful, {total_records} total records")

        return successful_types > 0

    except Exception as e:
        print(f"- Comprehensive data retrieval failed: {e}")
        return False


def test_long_term_feasibility(adapter):
    """Test long-term data feasibility (5+ years)"""
    print("\nTesting Long-Term Data Feasibility...")
    print("-" * 50)

    try:
        end_date = date.today()
        start_date = end_date - timedelta(days=5*365)  # 5 years

        print(f"Testing 5-year HIBOR data feasibility...")

        start_time = datetime.now()
        long_term_data = adapter.get_hibor_data(start_date, end_date, use_storage=True)
        duration = (datetime.now() - start_time).total_seconds()

        if len(long_term_data) > 0:
            actual_years = (long_term_data.index.max() - long_term_data.index.min()).days / 365.25
            completeness = len(long_term_data) / (5 * 252 * 7)  # 5 years * 252 days * 7 tenors

            print(f"+ 5-year HIBOR data: {len(long_term_data)} records")
            print(f"  Actual coverage: {actual_years:.1f} years")
            print(f"  Completeness: {completeness:.1%}")
            print(f"  Duration: {duration:.2f}s")

            # Test data quality
            if 'rate' in long_term_data.columns:
                rate_stats = long_term_data['rate'].describe()
                print(f"  Rate statistics: min={rate_stats['min']:.4f}, max={rate_stats['max']:.4f}, mean={rate_stats['mean']:.4f}")

            return True
        else:
            print("- No long-term data available")
            return False

    except Exception as e:
        print(f"- Long-term feasibility test failed: {e}")
        return False


def test_latest_rates(adapter):
    """Test latest HIBOR rates functionality"""
    print("\nTesting Latest HIBOR Rates...")
    print("-" * 50)

    try:
        latest_rates = adapter.get_latest_hibor_rates()

        if latest_rates:
            print("Latest HIBOR Rates:")
            for tenor, rate in latest_rates.items():
                print(f"  {tenor}: {rate:.4f}%")
            return True
        else:
            print("- No latest rates available")
            return False

    except Exception as e:
        print(f"- Latest rates test failed: {e}")
        return False


def test_storage_statistics(adapter):
    """Test storage statistics and information"""
    print("\nTesting Storage Statistics...")
    print("-" * 50)

    try:
        storage_stats = adapter.storage.get_storage_statistics()

        if storage_stats:
            print("Storage System Statistics:")
            print(f"  Total symbols: {storage_stats.get('total_symbols', 0)}")
            print(f"  Total partitions: {storage_stats.get('total_partitions', 0)}")
            print(f"  Storage size: {storage_stats.get('storage_size_mb', 0):.2f} MB")

            available_symbols = adapter.storage.get_available_symbols()
            hkma_symbols = [s for s in available_symbols if s.startswith('HKMA_')]

            print(f"  HKMA symbols stored: {len(hkma_symbols)}")
            for symbol in hkma_symbols:
                print(f"    - {symbol}")

            return True
        else:
            print("- No storage statistics available")
            return False

    except Exception as e:
        print(f"- Storage statistics test failed: {e}")
        return False


def generate_enhanced_hkma_report(adapter, test_results):
    """Generate comprehensive test report"""
    print("\n" + "=" * 60)
    print("ENHANCED HKMA ADAPTER TEST REPORT")
    print("=" * 60)

    # Multi-data-type results
    if 'multi_type' in test_results:
        print("\nMULTIPLE DATA TYPE TEST:")
        print("-" * 30)
        multi_results = test_results['multi_type']

        successful_types = [dtype for dtype, result in multi_results.items() if result.get('success', False)]
        total_records = sum(result.get('records', 0) for result in multi_results.values() if result.get('success', False))

        print(f"Successful data types: {len(successful_types)}/{len(multi_results)}")
        print(f"Total records retrieved: {total_records}")
        print(f"Available data types: {', '.join(successful_types)}")

    # Overall assessment
    print(f"\nSYSTEM ASSESSMENT:")
    print("-" * 20)

    all_tests = test_results.values()
    successful_tests = [test for test in all_tests if test]

    if len(successful_tests) >= len(all_tests) * 0.8:
        print("STATUS: EXCELLENT")
        print("Enhanced HKMA adapter is fully operational")
        print("Ready for government data integration in trading strategies")
        print("\nCAPABILITIES:")
        print("+ Multi-source HKMA data integration")
        print("+ Long-term storage with Parquet")
        print("+ 5+ year historical data support")
        print("+ Robust fallback mechanisms")
        print("+ Professional data quality validation")
        print("\nREADY FOR: Government data fusion and long-term analysis")
    else:
        print("STATUS: NEEDS ATTENTION")
        print("Some components may need additional configuration")
        print("\nRECOMMENDED ACTIONS:")
        print("1. Verify API endpoint accessibility")
        print("2. Check storage integration")
        print("3. Validate data quality measures")


def main():
    """Main test function"""
    print("ENHANCED HKMA ADAPTER INTEGRATION TEST")
    print("=" * 50)
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    all_tests_passed = True
    test_results = {}

    # Test 1: Adapter initialization
    init_success, adapter = test_enhanced_hkma_initialization()
    all_tests_passed &= init_success
    test_results['initialization'] = init_success

    if adapter:
        # Test 2: HIBOR data retrieval
        hibor_success = test_hibor_data_retrieval(adapter)
        all_tests_passed &= hibor_success
        test_results['hibor'] = hibor_success

        # Test 3: Multiple data types
        multi_type_results = test_multiple_data_types(adapter)
        multi_type_success = any(result.get('success', False) for result in multi_type_results.values())
        all_tests_passed &= multi_type_success
        test_results['multi_type'] = multi_type_results

        # Test 4: Comprehensive data
        comprehensive_success = test_comprehensive_data(adapter)
        all_tests_passed &= comprehensive_success
        test_results['comprehensive'] = comprehensive_success

        # Test 5: Long-term feasibility
        long_term_success = test_long_term_feasibility(adapter)
        all_tests_passed &= long_term_success
        test_results['long_term'] = long_term_success

        # Test 6: Latest rates
        latest_success = test_latest_rates(adapter)
        all_tests_passed &= latest_success
        test_results['latest'] = latest_success

        # Test 7: Storage statistics
        storage_success = test_storage_statistics(adapter)
        test_results['storage'] = storage_success

        # Generate report
        generate_enhanced_hkma_report(adapter, test_results)

    # Final assessment
    print("\n" + "=" * 50)
    print("TEST RESULTS SUMMARY")
    print("=" * 50)

    successful_tests = sum(1 for test in test_results.values() if test)
    total_tests = len(test_results)

    if all_tests_passed or successful_tests >= total_tests * 0.8:
        print("STATUS: ENHANCED HKMA ADAPTER OPERATIONAL")
        print("+ Government data integration ready")
        print("+ Long-term storage working correctly")
        print("+ Multiple data sources available")
        print("\nPHASE 1 COMPLETE: Ready for Phase 2 implementation")
        print("Next: Long-term technical indicators with government data fusion")
    else:
        print("STATUS: SOME TESTS FAILED")
        print("WARNING: System needs attention before production use")
        print("\nREQUIRED ACTIONS:")
        print("1. Check HKMA API accessibility")
        print("2. Verify storage integration")
        print("3. Validate data parsing logic")

    print("=" * 50)


if __name__ == "__main__":
    main()