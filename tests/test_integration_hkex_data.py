"""
Comprehensive Integration Tests for HKEX Data Flow

Tests the complete data pipeline:
    HKEX Crawler → PostgreSQL Database → FastAPI API → Response

This test suite verifies:
1. Database Schema (tables, triggers, indexes)
2. Data Insertion Flow (raw data → trigger → indicators)
3. API Endpoints (performance, indicators)
4. Service Layer Integration (fetch, calculate, date ranges)

Run with:
    python -m pytest tests/test_integration_hkex_data.py -v
    pytest tests/test_integration_hkex_data.py -v --tb=short
"""
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import fixtures
from tests.fixtures.hkex_test_data import (
    SAMPLE_RAW_DATA_RECORDS,
    EXPECTED_INDICATORS_RECORDS,
    insert_test_raw_data,
    verify_indicators_calculated,
    cleanup_test_data,
    get_expected_indicator_for_date,
    compare_indicators,
    generate_date_range_records,
    setup_test_database,
    validate_performance_response,
    validate_indicators_response,
)

# Import service layer
from src.services.market_indicator_service import (
    get_date_range,
    fetch_indicators,
    calculate_return_attribution,
    get_mock_data,
    TIME_RANGES,
)


# =============================================================================
# Test Database Configuration
# =============================================================================

@pytest.fixture(scope="module")
def db_connection():
    """
    Create database connection for integration tests.

    Requires DATABASE_URL environment variable or uses test database.
    Tests are skipped if database is not available.
    """
    try:
        from src.database.connection import get_db_connection

        conn = get_db_connection()

        # Verify database is set up
        if not setup_test_database(conn):
            pytest.skip("Test database schema not set up")

        yield conn

        # Cleanup: Close connection
        conn.close()

    except Exception as e:
        pytest.skip(f"Database connection failed: {e}")


@pytest.fixture(autouse=True)
def cleanup_before_and_after(db_connection):
    """
    Automatically cleanup test data before and after each test.
    """
    # Cleanup before test
    dates = [r["date"] for r in SAMPLE_RAW_DATA_RECORDS]
    cleanup_test_data(db_connection, dates)

    yield

    # Cleanup after test
    cleanup_test_data(db_connection, dates)


# =============================================================================
# 1. Test Database Schema
# =============================================================================

class TestDatabaseSchema:
    """Test database schema validation"""

    @pytest.mark.database
    def test_hkex_raw_data_table_exists(self, db_connection):
        """Verify hkex_raw_data table exists with correct columns"""
        cursor = db_connection.cursor()

        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'hkex_raw_data'
            ORDER BY ordinal_position;
        """)

        columns = {row[0]: row[1] for row in cursor.fetchall()}
        cursor.close()

        # Verify required columns exist
        required_columns = [
            'id', 'date', 'trading_volume', 'advanced_stocks',
            'declined_stocks', 'unchanged_stocks', 'turnover_hkd',
            'deals', 'morning_close', 'afternoon_close',
            'change_value', 'change_percent', 'created_at'
        ]

        for col in required_columns:
            assert col in columns, f"Missing column: {col}"

    @pytest.mark.database
    def test_market_indicators_table_exists(self, db_connection):
        """Verify market_indicators table exists with correct columns"""
        cursor = db_connection.cursor()

        cursor.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'market_indicators'
            ORDER BY ordinal_position;
        """)

        columns = [row[0] for row in cursor.fetchall()]
        cursor.close()

        # Verify required columns exist
        required_columns = [
            'id', 'date', 'advance_decline_ratio', 'volume_change_percent',
            'sentiment_score', 'breadth_momentum', 'created_at', 'updated_at'
        ]

        for col in required_columns:
            assert col in columns, f"Missing column: {col}"

    @pytest.mark.database
    def test_trigger_function_exists(self, db_connection):
        """Verify calculate_indicators trigger function exists"""
        cursor = db_connection.cursor()

        # Check for trigger function
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM pg_proc
                WHERE proname = 'calculate_indicators'
            );
        """)

        function_exists = cursor.fetchone()[0]
        cursor.close()

        assert function_exists, "calculate_indicators function not found"

    @pytest.mark.database
    def test_date_indexes_exist(self, db_connection):
        """Verify indexes exist on date columns for performance"""
        cursor = db_connection.cursor()

        # Check for indexes on hkex_raw_data.date
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE tablename = 'hkex_raw_data'
                AND indexdef LIKE '%date%'
            );
        """)
        raw_index_exists = cursor.fetchone()[0]

        # Check for indexes on market_indicators.date
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE tablename = 'market_indicators'
                AND indexdef LIKE '%date%'
            );
        """)
        indicators_index_exists = cursor.fetchone()[0]

        cursor.close()

        # At least one table should have a date index
        assert raw_index_exists or indicators_index_exists, \
            "No date indexes found on tables"


# =============================================================================
# 2. Test Data Insertion Flow
# =============================================================================

class TestDataInsertionFlow:
    """Test data insertion and trigger-based calculation"""

    @pytest.mark.database
    def test_insert_raw_data(self, db_connection):
        """Test inserting raw data into hkex_raw_data"""
        result = insert_test_raw_data(db_connection)

        assert result is True, "Failed to insert test data"

        # Verify data was inserted
        cursor = db_connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM hkex_raw_data")
        count = cursor.fetchone()[0]
        cursor.close()

        assert count == len(SAMPLE_RAW_DATA_RECORDS), \
            f"Expected {len(SAMPLE_RAW_DATA_RECORDS)} records, got {count}"

    @pytest.mark.database
    def test_trigger_auto_calculates_indicators(self, db_connection):
        """Verify trigger automatically calculates market_indicators"""
        # Insert test data
        insert_test_raw_data(db_connection)

        # Give trigger time to process (usually instant, but wait a bit)
        import time
        time.sleep(0.1)

        # Verify indicators were calculated
        indicators = verify_indicators_calculated(
            db_connection,
            expected_count=len(SAMPLE_RAW_DATA_RECORDS)
        )

        assert len(indicators) == len(SAMPLE_RAW_DATA_RECORDS), \
            f"Expected {len(SAMPLE_RAW_DATA_RECORDS)} indicators, got {len(indicators)}"

    @pytest.mark.database
    def test_calculated_values_are_correct(self, db_connection):
        """Verify trigger calculates correct indicator values"""
        # Insert test data
        insert_test_raw_data(db_connection)

        import time
        time.sleep(0.1)

        # Get calculated indicators
        actual_indicators = verify_indicators_calculated(db_connection)

        # Compare with expected values
        for actual in actual_indicators:
            # Get date string
            if hasattr(actual['date'], 'isoformat'):
                date_str = actual['date'].isoformat()[:10]
            else:
                date_str = str(actual['date'])[:10]

            expected = get_expected_indicator_for_date(date_str)

            if expected:
                # Compare with tolerance for floating point
                match = compare_indicators(actual, expected, tolerance=1.0)
                assert match, \
                    f"Indicator values don't match for {date_str}"

    @pytest.mark.database
    def test_upsert_handling(self, db_connection):
        """Test ON CONFLICT handling (upsert)"""
        # Insert same data twice
        insert_test_raw_data(db_connection)
        insert_test_raw_data(db_connection)

        import time
        time.sleep(0.1)

        # Should only have one record per date
        cursor = db_connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM hkex_raw_data")
        raw_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM market_indicators")
        indicators_count = cursor.fetchone()[0]
        cursor.close()

        assert raw_count == len(SAMPLE_RAW_DATA_RECORDS), \
            f"Expected {len(SAMPLE_RAW_DATA_RECORDS)} raw records after upsert"

        assert indicators_count == len(SAMPLE_RAW_DATA_RECORDS), \
            f"Expected {len(SAMPLE_RAW_DATA_RECORDS)} indicators after upsert"

    @pytest.mark.database
    def test_large_dataset_insertion(self, db_connection):
        """Test inserting a larger dataset"""
        # Generate 30 days of data
        large_dataset = generate_date_range_records("2025-11-20", 30)

        dates = [r["date"] for r in large_dataset]
        cleanup_test_data(db_connection, dates)

        # Insert all records
        result = insert_test_raw_data(db_connection, large_dataset)
        assert result is True, "Failed to insert large dataset"

        import time
        time.sleep(0.1)

        # Verify all indicators calculated
        indicators = verify_indicators_calculated(db_connection)
        assert len(indicators) == 30, \
            f"Expected 30 indicators, got {len(indicators)}"

        # Cleanup
        cleanup_test_data(db_connection, dates)


# =============================================================================
# 3. Test API Endpoints
# =============================================================================

class TestAPIEndpoints:
    """Test FastAPI endpoints with real database"""

    @pytest.mark.database
    @pytest.mark.api
    def test_performance_endpoint_with_data(self, db_connection):
        """Test GET /api/analytics/performance with real data"""
        # Setup test data
        insert_test_raw_data(db_connection)

        import time
        time.sleep(0.1)

        # Mock the endpoint call
        # In a real scenario, you'd use TestClient from FastAPI
        # Here we test the service layer directly
        start_date, end_date = get_date_range("1w")

        indicators = fetch_indicators(db_connection, start_date, end_date)

        # Should have data
        assert len(indicators) > 0, "No indicators returned"

        # Calculate attribution
        attribution = calculate_return_attribution(indicators)

        # Verify structure
        assert "total" in attribution
        assert "breakdown" in attribution
        assert len(attribution["breakdown"]) == 3

    @pytest.mark.database
    @pytest.mark.api
    def test_performance_endpoint_empty_database(self, db_connection):
        """Test graceful degradation when database is empty"""
        # Ensure no data
        dates = [r["date"] for r in SAMPLE_RAW_DATA_RECORDS]
        cleanup_test_data(db_connection, dates)

        import time
        time.sleep(0.1)

        # Mock endpoint call with empty database
        start_date, end_date = get_date_range("1w")
        indicators = fetch_indicators(db_connection, start_date, end_date)

        # Should return empty list
        assert indicators == [], "Expected empty indicators list"

        # Service should return mock data
        mock_data = get_mock_data()
        assert "return_attribution" in mock_data
        assert "risk_exposure" in mock_data

    @pytest.mark.database
    @pytest.mark.api
    def test_indicators_endpoint_with_filters(self, db_connection):
        """Test GET /api/analytics/indicators with date filters"""
        # Insert test data
        insert_test_raw_data(db_connection)

        import time
        time.sleep(0.1)

        # Query with specific date range
        from psycopg2.extras import RealDictCursor

        cursor = db_connection.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""
            SELECT date, advance_decline_ratio, volume_change_percent,
                   sentiment_score, breadth_momentum
            FROM market_indicators
            WHERE date >= %s AND date <= %s
            ORDER BY date DESC
        """, ("2025-12-20", "2025-12-22"))

        results = cursor.fetchall()
        cursor.close()

        assert len(results) == 3, f"Expected 3 results, got {len(results)}"

    @pytest.mark.database
    @pytest.mark.api
    def test_indicators_response_structure(self, db_connection):
        """Verify API response structure matches expected format"""
        # Insert test data
        insert_test_raw_data(db_connection)

        import time
        time.sleep(0.1)

        # Get indicators
        start_date, end_date = get_date_range("1m")
        indicators = fetch_indicators(db_connection, start_date, end_date)

        # Build mock response
        response = {"data": indicators, "count": len(indicators)}

        # Validate structure
        assert validate_indicators_response(response), \
            "Indicators response structure validation failed"

    @pytest.mark.database
    @pytest.mark.api
    def test_performance_response_structure(self, db_connection):
        """Verify performance response structure"""
        # Insert test data
        insert_test_raw_data(db_connection)

        import time
        time.sleep(0.1)

        # Build mock performance response
        indicators = fetch_indicators(db_connection, *get_date_range("1w"))
        attribution = calculate_return_attribution(indicators)

        response = {
            "return_attribution": attribution,
            "risk_exposure": get_mock_data()["risk_exposure"],
            "correlations": get_mock_data()["correlations"],
            "stress_test": get_mock_data()["stress_test"]
        }

        # Validate structure
        assert validate_performance_response(response), \
            "Performance response structure validation failed"


# =============================================================================
# 4. Test Service Layer Integration
# =============================================================================

class TestServiceLayerIntegration:
    """Test service layer with real database connection"""

    @pytest.mark.database
    def test_fetch_indicators_with_real_db(self, db_connection):
        """Test fetch_indicators with real database connection"""
        # Setup data
        insert_test_raw_data(db_connection)

        import time
        time.sleep(0.1)

        # Fetch indicators
        start_date = datetime(2025, 12, 1)
        end_date = datetime(2025, 12, 31)

        indicators = fetch_indicators(db_connection, start_date, end_date)

        assert len(indicators) > 0, "No indicators fetched"

        # Verify structure
        for ind in indicators:
            assert "date" in ind
            assert "advance_decline_ratio" in ind
            assert "volume_change_percent" in ind
            assert "sentiment_score" in ind
            assert "breadth_momentum" in ind

    @pytest.mark.database
    def test_calculate_return_attribution_with_real_data(self, db_connection):
        """Test calculate_return_attribution with real data"""
        # Setup data
        insert_test_raw_data(db_connection)

        import time
        time.sleep(0.1)

        # Fetch and calculate
        indicators = fetch_indicators(
            db_connection,
            datetime(2025, 12, 1),
            datetime(2025, 12, 31)
        )

        attribution = calculate_return_attribution(indicators)

        # Verify calculation
        assert attribution["total"] >= 0

        # Verify breakdown
        total_percentage = sum(item["percentage"] for item in attribution["breakdown"])
        assert 99 <= total_percentage <= 101, \
            f"Percentages should sum to ~100, got {total_percentage}"

    @pytest.mark.database
    def test_date_range_calculations(self):
        """Test date range calculation for all supported ranges"""
        now = datetime.now()

        for range_key, days in TIME_RANGES.items():
            start, end = get_date_range(range_key)

            assert isinstance(start, datetime)
            assert isinstance(end, datetime)
            assert start <= end

            # Check approximate duration
            duration = (end - start).days
            assert abs(duration - days) <= 1, \
                f"Date range {range_key} duration off: expected ~{days}, got {duration}"

    @pytest.mark.database
    def test_fetch_indicators_empty_result(self, db_connection):
        """Test fetch_indicators returns empty list when no data"""
        # Ensure clean state
        dates = [r["date"] for r in SAMPLE_RAW_DATA_RECORDS]
        cleanup_test_data(db_connection, dates)

        import time
        time.sleep(0.1)

        # Fetch from empty table
        indicators = fetch_indicators(
            db_connection,
            datetime(2025, 12, 1),
            datetime(2025, 12, 31)
        )

        assert indicators == [], "Expected empty list for no data"

    @pytest.mark.database
    def test_date_boundary_conditions(self, db_connection):
        """Test date range queries at boundaries"""
        # Insert test data
        insert_test_raw_data(db_connection)

        import time
        time.sleep(0.1)

        # Query exact date range
        indicators = fetch_indicators(
            db_connection,
            datetime(2025, 12, 20),
            datetime(2025, 12, 20)
        )

        # Should get exactly one record
        assert len(indicators) == 1, f"Expected 1 record, got {len(indicators)}"

    @pytest.mark.database
    def test_service_layer_error_handling(self, db_connection):
        """Test service layer handles database errors gracefully"""
        # Close connection to simulate error
        db_connection.close()

        # Should raise exception when using closed connection
        with pytest.raises(Exception):
            fetch_indicators(
                db_connection,
                datetime(2025, 12, 1),
                datetime(2025, 12, 31)
            )


# =============================================================================
# 5. End-to-End Workflow Tests
# =============================================================================

class TestEndToEndWorkflow:
    """Test complete workflows from insert to API response"""

    @pytest.mark.database
    def test_complete_data_pipeline(self, db_connection):
        """Test complete flow: insert → trigger → fetch → calculate"""
        # 1. Insert raw data
        assert insert_test_raw_data(db_connection)

        # 2. Wait for trigger
        import time
        time.sleep(0.1)

        # 3. Verify indicators calculated
        indicators = verify_indicators_calculated(db_connection)
        assert len(indicators) == len(SAMPLE_RAW_DATA_RECORDS)

        # 4. Fetch via service layer
        fetched = fetch_indicators(
            db_connection,
            datetime(2025, 12, 1),
            datetime(2025, 12, 31)
        )
        assert len(fetched) == len(indicators)

        # 5. Calculate attribution
        attribution = calculate_return_attribution(fetched)
        assert attribution["total"] > 0

    @pytest.mark.database
    def test_workflow_with_cleanup(self, db_connection):
        """Test workflow including cleanup between runs"""
        # First run
        insert_test_raw_data(db_connection)
        time.sleep(0.1)
        indicators_1 = verify_indicators_calculated(db_connection)

        # Cleanup
        dates = [r["date"] for r in SAMPLE_RAW_DATA_RECORDS]
        cleanup_test_data(db_connection, dates)
        time.sleep(0.1)

        # Verify clean
        indicators_after_cleanup = verify_indicators_calculated(db_connection)
        assert len(indicators_after_cleanup) == 0

        # Second run (should work same as first)
        insert_test_raw_data(db_connection)
        time.sleep(0.1)
        indicators_2 = verify_indicators_calculated(db_connection)

        assert len(indicators_2) == len(indicators_1)

    @pytest.mark.database
    def test_concurrent_insert_simulation(self, db_connection):
        """Test inserting data in quick succession"""
        # Insert records one by one (simulating concurrent crawler)
        for record in SAMPLE_RAW_DATA_RECORDS:
            insert_test_raw_data(db_connection, [record])

        time.sleep(0.2)  # Give trigger time to process all

        # Verify all indicators calculated
        indicators = verify_indicators_calculated(db_connection)
        assert len(indicators) == len(SAMPLE_RAW_DATA_RECORDS)

        # Verify no duplicates
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT date, COUNT(*) as count
            FROM market_indicators
            GROUP BY date
            HAVING COUNT(*) > 1;
        """)
        duplicates = cursor.fetchall()
        cursor.close()

        assert len(duplicates) == 0, f"Found duplicate dates: {duplicates}"


# =============================================================================
# 6. Performance Tests
# =============================================================================

class TestPerformance:
    """Basic performance tests for data operations"""

    @pytest.mark.database
    @pytest.mark.slow
    def test_bulk_insert_performance(self, db_connection):
        """Test performance of bulk data insertion"""
        import time

        # Generate 100 records
        large_dataset = generate_date_range_records("2025-09-01", 100)
        dates = [r["date"] for r in large_dataset]

        # Cleanup first
        cleanup_test_data(db_connection, dates)

        # Measure insert time
        start_time = time.time()
        insert_test_raw_data(db_connection, large_dataset)
        insert_duration = time.time() - start_time

        # Wait for trigger
        time.sleep(0.5)

        # Verify
        indicators = verify_indicators_calculated(db_connection)

        # Cleanup
        cleanup_test_data(db_connection, dates)

        # Assertions
        assert len(indicators) == 100
        assert insert_duration < 10, \
            f"Bulk insert took {insert_duration:.2f}s, expected < 10s"

    @pytest.mark.database
    def test_query_performance(self, db_connection):
        """Test performance of date range queries"""
        import time

        # Insert data
        large_dataset = generate_date_range_records("2025-09-01", 50)
        dates = [r["date"] for r in large_dataset]
        cleanup_test_data(db_connection, dates)
        insert_test_raw_data(db_connection, large_dataset)

        time.sleep(0.2)

        # Measure query time
        start_time = time.time()
        indicators = fetch_indicators(
            db_connection,
            datetime(2025, 9, 1),
            datetime(2025, 10, 20)
        )
        query_duration = time.time() - start_time

        # Cleanup
        cleanup_test_data(db_connection, dates)

        # Assertions
        assert len(indicators) == 50
        assert query_duration < 1, \
            f"Query took {query_duration:.3f}s, expected < 1s"


# =============================================================================
# Test Run Configuration
# =============================================================================

if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short", "-m", "database or api"])
