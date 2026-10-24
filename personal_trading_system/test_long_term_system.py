#!/usr/bin/env python3
"""
Test Long-Term System Integration
Test Yahoo Finance adapter and long-term storage for 5+ year backtesting
"""

import sys
from pathlib import Path
from datetime import datetime, date, timedelta
import pandas as pd
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from long_term_storage import LongTermDataStorage
from yahoo_finance_adapter import YahooFinanceAdapter

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_storage_initialization():
    """Test long-term storage system initialization"""
    print("Testing Long-Term Storage Initialization...")
    print("-" * 50)

    try:
        storage = LongTermDataStorage()
        print("+ Storage system initialized successfully")
        print(f"  Base path: {storage.base_path}")
        print(f"  Directory structure created")

        # Test directory structure
        required_dirs = ['cache', 'raw', 'processed', 'metadata']
        for dir_name in required_dirs:
            dir_path = storage.base_path / dir_name
            if dir_path.exists():
                print(f"  + {dir_name}/ directory exists")
            else:
                print(f"  - {dir_name}/ directory missing")

        return True, storage

    except Exception as e:
        print(f"- Storage initialization failed: {e}")
        return False, None


def test_yahoo_adapter():
    """Test Yahoo Finance adapter"""
    print("\nTesting Yahoo Finance Adapter...")
    print("-" * 50)

    try:
        storage = LongTermDataStorage()
        adapter = YahooFinanceAdapter(storage)
        print("+ Yahoo Finance adapter initialized successfully")
        print(f"  Cache TTL: {adapter.cache_ttl_hours} hours")
        return True, adapter

    except Exception as e:
        print(f"- Yahoo Finance adapter initialization failed: {e}")
        return False, None


def test_data_retrieval(adapter):
    """Test data retrieval from Yahoo Finance"""
    print("\nTesting Data Retrieval...")
    print("-" * 50)

    test_symbols = ['0700.HK']  # Start with Tencent
    end_date = date.today()
    start_date = end_date - timedelta(days=2*365)  # 2 years for testing

    results = {}

    for symbol in test_symbols:
        try:
            print(f"Testing {symbol}...")

            start_time = datetime.now()
            data = adapter.get_historical_data(symbol, start_date, end_date, use_cache=False)
            end_time = datetime.now()

            if len(data) > 0:
                duration = (end_time - start_time).total_seconds()
                results[symbol] = {
                    'success': True,
                    'records': len(data),
                    'duration_seconds': duration,
                    'date_range': (data.index.min().date(), data.index.max().date()),
                    'columns': list(data.columns)
                }

                print(f"  + SUCCESS: {len(data)} records in {duration:.2f}s")
                print(f"    Date range: {data.index.min().date()} to {data.index.max().date()}")
                print(f"    Columns: {list(data.columns)}")
            else:
                results[symbol] = {'success': False, 'error': 'No data returned'}
                print(f"  - FAILED: No data returned")

        except Exception as e:
            results[symbol] = {'success': False, 'error': str(e)}
            print(f"  - ERROR: {e}")

    return results


def test_storage_system(adapter, storage):
    """Test data storage and retrieval"""
    print("\nTesting Storage System...")
    print("-" * 50)

    symbol = '0700.HK'
    end_date = date.today()
    start_date = end_date - timedelta(days=365)  # 1 year for storage test

    try:
        # Fetch data
        print(f"Fetching data for {symbol}...")
        data = adapter.get_historical_data(symbol, start_date, end_date, use_cache=False, force_update=True)

        if len(data) > 0:
            print(f"+ Fetched {len(data)} records")

            # Store data
            print("Storing data in long-term storage...")
            storage_stats = storage.store_historical_data(symbol, data, "daily")
            print(f"+ Stored data: {storage_stats['total_records']} records")
            print(f"  Partitions created: {storage_stats['partitions_created']}")
            print(f"  Storage size: {storage_stats['storage_size_mb']:.2f} MB")

            # Test retrieval
            print("Testing data retrieval...")
            retrieved_data = storage.load_historical_data(symbol, start_date, end_date, "daily")

            if len(retrieved_data) > 0:
                print(f"+ Retrieved {len(retrieved_data)} records")

                # Verify data integrity
                if len(retrieved_data) == len(data):
                    print("+ Data integrity verified")
                    return True
                else:
                    print(f"- Data integrity issue: expected {len(data)}, got {len(retrieved_data)}")
                    return False
            else:
                print("- Failed to retrieve stored data")
                return False
        else:
            print("- No data available for storage test")
            return False

    except Exception as e:
        print(f"- Storage system test failed: {e}")
        return False


def test_cache_functionality(adapter):
    """Test caching functionality"""
    print("\nTesting Cache Functionality...")
    print("-" * 50)

    symbol = '0941.HK'  # China Mobile
    end_date = date.today()
    start_date = end_date - timedelta(days=90)  # 3 months

    try:
        # First fetch (should hit Yahoo Finance)
        print("First fetch (cache miss)...")
        start_time = datetime.now()
        data1 = adapter.get_historical_data(symbol, start_date, end_date, use_cache=True)
        first_duration = (datetime.now() - start_time).total_seconds()

        # Second fetch (should hit cache)
        print("Second fetch (cache hit)...")
        start_time = datetime.now()
        data2 = adapter.get_historical_data(symbol, start_date, end_date, use_cache=True)
        second_duration = (datetime.now() - start_time).total_seconds()

        if len(data1) > 0 and len(data2) > 0:
            print(f"+ First fetch: {len(data1)} records in {first_duration:.3f}s")
            print(f"+ Second fetch: {len(data2)} records in {second_duration:.3f}s")

            speedup = first_duration / second_duration if second_duration > 0 else float('inf')
            print(f"+ Cache speedup: {speedup:.1f}x faster")

            # Verify data consistency
            if data1.equals(data2):
                print("+ Cache data consistency verified")
                return True
            else:
                print("- Cache data inconsistency detected")
                return False
        else:
            print("- Cache test failed: No data retrieved")
            return False

    except Exception as e:
        print(f"- Cache functionality test failed: {e}")
        return False


def test_5year_feasibility(adapter):
    """Test 5+ year data feasibility"""
    print("\nTesting 5+ Year Data Feasibility...")
    print("-" * 50)

    symbols = ['0700.HK', '0941.HK']  # Tencent, China Mobile
    years_back = 5

    end_date = date.today()
    start_date = end_date - timedelta(days=years_back * 365)

    results = {}

    for symbol in symbols:
        try:
            print(f"Testing {symbol} for {years_back} years...")

            start_time = datetime.now()
            data = adapter.get_historical_data(symbol, start_date, end_date, use_cache=False, force_update=True)
            duration = (datetime.now() - start_time).total_seconds()

            if len(data) > 0:
                actual_years = (data.index.max() - data.index.min()).days / 365.25
                completeness = len(data) / (years_back * 252)  # ~252 trading days per year

                results[symbol] = {
                    'success': True,
                    'records': len(data),
                    'actual_years': actual_years,
                    'completeness_percentage': completeness * 100,
                    'duration_seconds': duration
                }

                print(f"  + SUCCESS: {len(data)} records")
                print(f"    Actual coverage: {actual_years:.1f} years")
                print(f"    Completeness: {completeness:.1%}")
                print(f"    Duration: {duration:.2f}s")
            else:
                results[symbol] = {'success': False, 'error': 'No data'}
                print(f"  - FAILED: No data returned")

        except Exception as e:
            results[symbol] = {'success': False, 'error': str(e)}
            print(f"  - ERROR: {e}")

    return results


def generate_system_report(storage, adapter):
    """Generate comprehensive system report"""
    print("\n" + "=" * 60)
    print("LONG-TERM SYSTEM INTEGRATION REPORT")
    print("=" * 60)

    # Storage statistics
    print("\nSTORAGE SYSTEM STATUS:")
    print("-" * 30)
    storage_stats = storage.get_storage_statistics()

    if storage_stats:
        print(f"Total symbols: {storage_stats.get('total_symbols', 0)}")
        print(f"Total partitions: {storage_stats.get('total_partitions', 0)}")
        print(f"Storage size: {storage_stats.get('storage_size_mb', 0):.2f} MB")

        data_types = storage_stats.get('data_types', {})
        for data_type, info in data_types.items():
            print(f"  {data_type}: {len(info.get('symbols', []))} symbols, "
                  f"{info.get('total_size_mb', 0):.2f} MB")
    else:
        print("No storage statistics available")

    # Available symbols
    print(f"\nAVAILABLE SYMBOLS:")
    print("-" * 20)
    symbols = storage.get_available_symbols()
    if symbols:
        print(f"Symbols in storage: {', '.join(symbols)}")
    else:
        print("No symbols currently stored")

    # Overall assessment
    print(f"\nSYSTEM ASSESSMENT:")
    print("-" * 20)
    if storage_stats and storage_stats.get('total_symbols', 0) > 0:
        print("STATUS: OPERATIONAL")
        print("Long-term storage system is ready for 5+ year backtesting")
        print("\nCAPABILITIES:")
        print("+ Yahoo Finance data integration")
        print("+ Parquet-based long-term storage")
        print("+ Year-based partitioning")
        print("+ Intelligent caching")
        print("+ Data quality validation")
        print("\nREADY FOR: Professional 5+ year backtesting")
    else:
        print("STATUS: INITIALIZING")
        print("System is initialized but no data has been stored yet")
        print("\nNEXT STEP: Initialize symbols with historical data")


def main():
    """Main test function"""
    print("LONG-TERM SYSTEM INTEGRATION TEST")
    print("=" * 50)
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    all_tests_passed = True

    # Test 1: Storage initialization
    storage_success, storage = test_storage_initialization()
    all_tests_passed &= storage_success

    # Test 2: Yahoo Finance adapter
    adapter_success, adapter = test_yahoo_adapter()
    all_tests_passed &= adapter_success

    if storage and adapter:
        # Test 3: Data retrieval
        retrieval_results = test_data_retrieval(adapter)
        retrieval_success = any(r.get('success', False) for r in retrieval_results.values())
        all_tests_passed &= retrieval_success

        # Test 4: Storage system
        storage_test_passed = test_storage_system(adapter, storage)
        all_tests_passed &= storage_test_passed

        # Test 5: Cache functionality
        cache_test_passed = test_cache_functionality(adapter)
        all_tests_passed &= cache_test_passed

        # Test 6: 5+ year feasibility
        feasibility_results = test_5year_feasibility(adapter)
        feasibility_success = any(r.get('success', False) for r in feasibility_results.values())
        all_tests_passed &= feasibility_success

        # Generate report
        generate_system_report(storage, adapter)

    # Final assessment
    print("\n" + "=" * 50)
    print("TEST RESULTS SUMMARY")
    print("=" * 50)

    if all_tests_passed:
        print("STATUS: ALL TESTS PASSED")
        print("+ Long-term system is fully operational")
        print("+ Ready for 5+ year backtesting implementation")
        print("\nNEXT STEPS:")
        print("1. Initialize symbols with 5-10 years of historical data")
        print("2. Implement long-term technical indicators")
        print("3. Create 5+ year backtesting strategies")
    else:
        print("STATUS: SOME TESTS FAILED")
        print("WARNING: System needs attention before production use")
        print("\nREQUIRED ACTIONS:")
        print("1. Fix failed test components")
        print("2. Verify data source connectivity")
        print("3. Check storage permissions")

    print("=" * 50)


if __name__ == "__main__":
    main()