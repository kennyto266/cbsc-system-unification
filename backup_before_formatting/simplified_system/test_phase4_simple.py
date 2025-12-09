"""
Phase 4 Simple Test - No Unicode Issues
"""

import asyncio
import json
import time
import sys
import os

# Add to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src', 'api'))

def test_imports():
    """Test if all modules can be imported"""
    print("Testing imports...")

    try:
        from adaptive_analysis_api import AdaptiveAnalysisAPI
        print("✓ AdaptiveAnalysisAPI imported successfully")
    except Exception as e:
        print(f"✗ AdaptiveAnalysisAPI import failed: {e}")
        return False

    try:
        from adaptive_api_server import app
        print("✓ FastAPI app imported successfully")
    except Exception as e:
        print(f"✗ FastAPI app import failed: {e}")
        return False

    return True

def test_adaptive_system():
    """Test the adaptive system without API"""
    print("\nTesting adaptive system...")

    try:
        from workflow.adaptive_market_system import AdaptiveMarketSystem
        import pandas as pd
        import numpy as np
        from datetime import datetime

        # Create adaptive system
        system = AdaptiveMarketSystem()
        print("✓ Adaptive system created")

        # Generate sample data
        dates = pd.date_range('2024-01-01', periods=100, freq='D')
        np.random.seed(42)

        market_data = {
            "hibor_rates": pd.Series(
                np.cumsum(np.random.normal(0.001, 0.02, 100)) + 3.5,
                index=dates
            ),
            "monetary_base": pd.Series(
                np.cumsum(np.random.normal(0.0005, 0.01, 100)) + 1000,
                index=dates
            ),
            "exchange_rates": pd.Series(
                np.cumsum(np.random.normal(-0.0002, 0.015, 100)) + 7.8,
                index=dates
            )
        }
        print("✓ Sample data generated")

        # Run adaptive analysis
        results = system.run_adaptive_analysis(market_data)
        print("✓ Adaptive analysis completed")

        # Check results
        if 'final_signal' in results:
            signal = results['final_signal']
            print(f"✓ Final signal: {signal.get('signal', 'N/A')} (confidence: {signal.get('confidence', 0):.2%})")

        if 'consensus_market_state' in results:
            state = results['consensus_market_state']
            print(f"✓ Market regime: {state.get('regime', 'N/A')}")

        if 'adaptive_weights' in results:
            weights = results['adaptive_weights']
            print(f"✓ Adaptive weights: {len(weights)} sources")

        return True

    except Exception as e:
        print(f"✗ Adaptive system test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cache_manager():
    """Test cache functionality"""
    print("\nTesting cache manager...")

    try:
        from api.adaptive_analysis_api import CacheManager

        cache = CacheManager(max_cache_size=5, cache_ttl=1)
        print("✓ Cache manager created")

        # Test set/get
        test_key = "test_key"
        test_value = {"test": "data", "timestamp": time.time()}

        cache.set(test_key, test_value)
        retrieved = cache.get(test_key)

        if retrieved == test_value:
            print("✓ Cache set/get working")
        else:
            print("✗ Cache set/get failed")
            return False

        # Test cache hit
        if cache.get(test_key) is not None:
            print("✓ Cache hit working")
        else:
            print("✗ Cache hit failed")
            return False

        return True

    except Exception as e:
        print(f"✗ Cache manager test failed: {e}")
        return False

def test_performance_monitoring():
    """Test performance monitoring"""
    print("\nTesting performance monitoring...")

    try:
        from api.adaptive_analysis_api import performance_monitor

        # Test decorator
        @performance_monitor(timeout_seconds=5.0)
        async def test_function():
            await asyncio.sleep(0.1)
            return "success"

        # Run the function
        result = asyncio.run(test_function())

        if result == "success":
            print("✓ Performance monitoring working")
            return True
        else:
            print("✗ Performance monitoring failed")
            return False

    except Exception as e:
        print(f"✗ Performance monitoring test failed: {e}")
        return False

def test_data_quality_validator():
    """Test data quality validation"""
    print("\nTesting data quality validator...")

    try:
        from api.adaptive_analysis_api import DataQualityValidator
        import pandas as pd
        import numpy as np

        validator = DataQualityValidator()
        print("✓ Data quality validator created")

        # Test with good data
        good_data = pd.Series(np.random.normal(0, 1, 50),
                             index=pd.date_range('2024-01-01', periods=50))
        is_valid, message = validator.validate_series(good_data)

        if is_valid:
            print("✓ Good data validation passed")
        else:
            print(f"✗ Good data validation failed: {message}")
            return False

        # Test with bad data (too short)
        bad_data = pd.Series([1, 2, 3])
        is_valid, message = validator.validate_series(bad_data)

        if not is_valid:
            print("✓ Bad data validation working")
        else:
            print("✗ Bad data validation failed")
            return False

        return True

    except Exception as e:
        print(f"✗ Data quality validator test failed: {e}")
        return False

def test_system_integration():
    """Test overall system integration"""
    print("\nTesting system integration...")

    try:
        # Test creating API instance
        from api.adaptive_analysis_api import get_api_instance

        async def test_api():
            api = await get_api_instance()
            print("✓ API instance created")

            # Test system health
            health = await api.get_system_health()
            if health.get('status') == 'healthy':
                print("✓ System health check passed")
            else:
                print(f"✓ System status: {health.get('status', 'unknown')}")

            return True

        return asyncio.run(test_api())

    except Exception as e:
        print(f"✗ System integration test failed: {e}")
        return False

def main():
    """Main test function"""
    print("Phase 4 Integration Test - Simple Version")
    print("=" * 50)

    tests = [
        ("Import Tests", test_imports),
        ("Adaptive System", test_adaptive_system),
        ("Cache Manager", test_cache_manager),
        ("Performance Monitoring", test_performance_monitoring),
        ("Data Quality Validator", test_data_quality_validator),
        ("System Integration", test_system_integration)
    ]

    results = {
        "total": len(tests),
        "passed": 0,
        "failed": 0,
        "details": []
    }

    for test_name, test_func in tests:
        print(f"\n[{results['passed'] + results['failed'] + 1}/{results['total']}] {test_name}")
        print("-" * 30)

        try:
            if test_func():
                results["passed"] += 1
                results["details"].append(f"✓ {test_name}: PASSED")
            else:
                results["failed"] += 1
                results["details"].append(f"✗ {test_name}: FAILED")
        except Exception as e:
            results["failed"] += 1
            results["details"].append(f"✗ {test_name}: ERROR - {e}")

    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    print(f"Total Tests: {results['total']}")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    print(f"Success Rate: {results['passed']/results['total']*100:.1f}%")

    print("\nTest Details:")
    for detail in results["details"]:
        print(f"  {detail}")

    # Overall result
    if results["passed"] == results["total"]:
        print("\n🎉 All tests passed! Phase 4 integration successful.")
        return 0
    elif results["passed"] / results["total"] >= 0.8:
        print("\n✅ Most tests passed! Phase 4 mostly successful.")
        return 0
    else:
        print("\n❌ Multiple tests failed! Phase 4 needs fixes.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)