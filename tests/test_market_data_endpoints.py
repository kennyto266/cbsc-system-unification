"""
Test Market Data Endpoints
Simple test to verify API endpoints work correctly
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.services.market_indicator_service import (
    get_date_range,
    calculate_return_attribution,
    get_mock_data
)


def test_get_date_range():
    """Test date range calculation"""
    print("Testing get_date_range...")

    start_1w, end = get_date_range("1w")
    print(f"  1w: {start_1w} to {end}")

    start_1m, end = get_date_range("1m")
    print(f"  1m: {start_1m} to {end}")

    start_3m, end = get_date_range("3m")
    print(f"  3m: {start_3m} to {end}")

    start_1y, end = get_date_range("1y")
    print(f"  1y: {start_1y} to {end}")

    # Test invalid range
    try:
        get_date_range("invalid")
        print("  [FAIL] Should have raised ValueError for invalid range")
        return False
    except ValueError:
        print("  [PASS] Correctly raises ValueError for invalid range")

    return True


def test_calculate_return_attribution_empty():
    """Test with empty indicators"""
    print("\nTesting calculate_return_attribution with empty data...")

    result = calculate_return_attribution([])

    assert result["total"] == 0.0
    assert len(result["breakdown"]) == 3
    assert all(item["contribution"] == 0.0 for item in result["breakdown"])

    print("  [PASS] Empty data handled correctly")
    return True


def test_calculate_return_attribution_with_data():
    """Test with sample indicators"""
    print("\nTesting calculate_return_attribution with sample data...")

    indicators = [
        {
            'date': '2025-12-20',
            'advance_decline_ratio': 0.44,
            'volume_change_percent': 5.2,
            'sentiment_score': 17.64,
            'breadth_momentum': 0
        },
        {
            'date': '2025-12-21',
            'advance_decline_ratio': 0.55,
            'volume_change_percent': 3.1,
            'sentiment_score': 22.5,
            'breadth_momentum': 0
        }
    ]

    result = calculate_return_attribution(indicators)

    print(f"  Total: {result['total']}")
    print(f"  Breakdown: {result['breakdown']}")

    assert result["total"] > 0
    assert len(result["breakdown"]) == 3

    # Check percentages sum to ~100
    total_pct = sum(item["percentage"] for item in result["breakdown"])
    assert 99 <= total_pct <= 101, f"Percentages sum to {total_pct}, expected ~100"

    print("  [PASS] Calculation successful")
    return True


def test_get_mock_data():
    """Test mock data structure"""
    print("\nTesting get_mock_data...")

    result = get_mock_data()

    assert "return_attribution" in result
    assert "risk_exposure" in result
    assert "correlations" in result
    assert "stress_test" in result

    assert "total" in result["return_attribution"]
    assert "breakdown" in result["return_attribution"]

    assert len(result["stress_test"]) == 4

    print(f"  Mock data has {len(result['stress_test'])} stress test scenarios")
    print("  [PASS] Mock data structure correct")
    return True


def test_import_main_router():
    """Test that router can be imported in main.py"""
    print("\nTesting router import in main.py context...")

    try:
        from src.api.market_data_endpoints import router
        assert router.prefix == "/api/analytics"
        assert router.tags == ["analytics"] or "analytics" in router.tags

        # Check routes exist (full path includes prefix)
        routes = [route.path for route in router.routes]
        print(f"  Available routes: {routes}")

        # Routes include the prefix
        assert "/api/analytics/performance" in routes or "performance" in routes
        assert "/api/analytics/indicators" in routes or "indicators" in routes

        print("  [PASS] Router configured correctly")
        return True
    except Exception as e:
        print(f"  [FAIL] Router import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("Market Data Endpoints Test Suite")
    print("=" * 60)

    tests = [
        test_get_date_range,
        test_calculate_return_attribution_empty,
        test_calculate_return_attribution_with_data,
        test_get_mock_data,
        test_import_main_router,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"  [FAIL] Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)

    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)

    if passed == total:
        print(f"[PASS] All tests passed! ({passed}/{total})")
        return 0
    else:
        print(f"[FAIL] Some tests failed! ({passed}/{total} passed)")
        return 1


if __name__ == "__main__":
    sys.exit(main())
