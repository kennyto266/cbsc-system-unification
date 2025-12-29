"""
HKEX Test Data Fixtures

Provides sample market data records and helper functions for testing
the complete data flow: HKEX Crawler → PostgreSQL → FastAPI API → Response.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

# =============================================================================
# Sample Market Data Records
# =============================================================================

SAMPLE_RAW_DATA_RECORDS = [
    {
        "date": "2025-12-20",
        "trading_volume": 8273,
        "advanced_stocks": 3094,
        "declined_stocks": 7016,
        "unchanged_stocks": 3625,
        "turnover_hkd": 328118569834,
        "deals": 4827115,
        "morning_close": 25460.16,
        "afternoon_close": 25496.55,
        "change_value": -120.87,
        "change_percent": -0.47
    },
    {
        "date": "2025-12-21",
        "trading_volume": 8500,
        "advanced_stocks": 3500,
        "declined_stocks": 6800,
        "unchanged_stocks": 3700,
        "turnover_hkd": 340000000000,
        "deals": 4900000,
        "morning_close": 25500.00,
        "afternoon_close": 25550.00,
        "change_value": 53.45,
        "change_percent": 0.21
    },
    {
        "date": "2025-12-22",
        "trading_volume": 8100,
        "advanced_stocks": 2800,
        "declined_stocks": 7500,
        "unchanged_stocks": 3500,
        "turnover_hkd": 310000000000,
        "deals": 4700000,
        "morning_close": 25300.00,
        "afternoon_close": 25350.00,
        "change_value": -200.00,
        "change_percent": -0.78
    },
    {
        "date": "2025-12-23",
        "trading_volume": 8400,
        "advanced_stocks": 4000,
        "declined_stocks": 6500,
        "unchanged_stocks": 3800,
        "turnover_hkd": 350000000000,
        "deals": 5000000,
        "morning_close": 25600.00,
        "afternoon_close": 25650.00,
        "change_value": 300.00,
        "change_percent": 1.18
    },
]


# Expected calculated indicators for the sample data above
# advance_decline_ratio = advanced / declined
# volume_change_percent = (turnover - prev_turnover) / prev_turnover * 100
# sentiment_score = (ratio * 20) + (volume_change * 0.5) + (breadth * 10)
# breadth_momentum = (advanced - declined) / total * 100
EXPECTED_INDICATORS_RECORDS = [
    {
        "date": "2025-12-20",
        "advance_decline_ratio": 0.44,  # 3094 / 7016 ≈ 0.44
        "volume_change_percent": None,  # First day, no previous data
        "sentiment_score": 17.64,  # Calculated by trigger
        "breadth_momentum": -47.76  # (3094 - 7016) / 10735 * 100
    },
    {
        "date": "2025-12-21",
        "advance_decline_ratio": 0.51,  # 3500 / 6800 ≈ 0.51
        "volume_change_percent": 3.63,  # (340B - 328.1B) / 328.1B * 100
        "sentiment_score": 22.5,
        "breadth_momentum": -38.82
    },
    {
        "date": "2025-12-22",
        "advance_decline_ratio": 0.37,  # 2800 / 7500 ≈ 0.37
        "volume_change_percent": -8.82,  # (310B - 340B) / 340B * 100
        "sentiment_score": 12.5,
        "breadth_momentum": -57.41
    },
    {
        "date": "2025-12-23",
        "advance_decline_ratio": 0.62,  # 4000 / 6500 ≈ 0.62
        "volume_change_percent": 12.90,  # (350B - 310B) / 310B * 100
        "sentiment_score": 28.0,
        "breadth_momentum": -29.76
    },
]


# =============================================================================
# Helper Functions
# =============================================================================

def insert_test_raw_data(conn, records: List[Dict[str, Any]] = None) -> bool:
    """
    Insert test data into hkex_raw_data table.

    Args:
        conn: Database connection object
        records: List of raw data records (defaults to SAMPLE_RAW_DATA_RECORDS)

    Returns:
        True if successful, False otherwise
    """
    if records is None:
        records = SAMPLE_RAW_DATA_RECORDS

    try:
        cursor = conn.cursor()

        for record in records:
            query = """
                INSERT INTO hkex_raw_data (
                    date, trading_volume, advanced_stocks, declined_stocks,
                    unchanged_stocks, turnover_hkd, deals, morning_close,
                    afternoon_close, change_value, change_percent
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (date) DO UPDATE SET
                    trading_volume = EXCLUDED.trading_volume,
                    advanced_stocks = EXCLUDED.advanced_stocks,
                    declined_stocks = EXCLUDED.declined_stocks,
                    unchanged_stocks = EXCLUDED.unchanged_stocks,
                    turnover_hkd = EXCLUDED.turnover_hkd,
                    deals = EXCLUDED.deals,
                    morning_close = EXCLUDED.morning_close,
                    afternoon_close = EXCLUDED.afternoon_close,
                    change_value = EXCLUDED.change_value,
                    change_percent = EXCLUDED.change_percent
            """
            cursor.execute(query, (
                record["date"],
                record["trading_volume"],
                record["advanced_stocks"],
                record["declined_stocks"],
                record["unchanged_stocks"],
                record["turnover_hkd"],
                record["deals"],
                record["morning_close"],
                record["afternoon_close"],
                record["change_value"],
                record["change_percent"]
            ))

        conn.commit()
        cursor.close()
        return True

    except Exception as e:
        print(f"Error inserting test data: {e}")
        conn.rollback()
        return False


def verify_indicators_calculated(conn, expected_count: int = None) -> List[Dict]:
    """
    Verify that market_indicators table was populated by trigger.

    Args:
        conn: Database connection object
        expected_count: Expected number of indicator records

    Returns:
        List of indicator records from database
    """
    from psycopg2.extras import RealDictCursor

    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        query = """
            SELECT
                date,
                advance_decline_ratio,
                volume_change_percent,
                sentiment_score,
                breadth_momentum,
                updated_at
            FROM market_indicators
            ORDER BY date ASC
        """
        cursor.execute(query)
        indicators = [dict(row) for row in cursor.fetchall()]
        cursor.close()

        if expected_count is not None:
            assert len(indicators) == expected_count, \
                f"Expected {expected_count} indicators, got {len(indicators)}"

        return indicators

    except Exception as e:
        print(f"Error verifying indicators: {e}")
        return []


def cleanup_test_data(conn, dates: List[str] = None) -> bool:
    """
    Clean up test data from both tables.

    Args:
        conn: Database connection object
        dates: List of date strings to delete (defaults to all sample dates)

    Returns:
        True if successful, False otherwise
    """
    if dates is None:
        dates = [r["date"] for r in SAMPLE_RAW_DATA_RECORDS]

    try:
        cursor = conn.cursor()

        # Delete from market_indicators first (due to foreign key if exists)
        for date in dates:
            cursor.execute("DELETE FROM market_indicators WHERE date = %s", (date,))

        # Delete from hkex_raw_data
        for date in dates:
            cursor.execute("DELETE FROM hkex_raw_data WHERE date = %s", (date,))

        conn.commit()
        cursor.close()
        return True

    except Exception as e:
        print(f"Error cleaning up test data: {e}")
        conn.rollback()
        return False


def get_expected_indicator_for_date(date_str: str) -> Optional[Dict[str, Any]]:
    """
    Get expected indicator values for a specific date.

    Args:
        date_str: Date string in YYYY-MM-DD format

    Returns:
        Expected indicator dict or None if not found
    """
    for indicator in EXPECTED_INDICATORS_RECORDS:
        if indicator["date"] == date_str:
            return indicator
    return None


def compare_indicators(actual: Dict, expected: Dict, tolerance: float = 0.1) -> bool:
    """
    Compare actual vs expected indicator values.

    Args:
        actual: Actual indicator dict from database
        expected: Expected indicator dict
        tolerance: Acceptable difference for floating point values

    Returns:
        True if values match within tolerance
    """
    # Convert date objects to strings for comparison
    if hasattr(actual.get('date'), 'isoformat'):
        actual_date = actual['date'].isoformat()[:10]
    else:
        actual_date = str(actual.get('date', ''))[:10]

    if actual_date != expected.get('date'):
        print(f"Date mismatch: {actual_date} vs {expected.get('date')}")
        return False

    # Compare numeric values with tolerance
    numeric_fields = [
        'advance_decline_ratio',
        'volume_change_percent',
        'sentiment_score',
        'breadth_momentum'
    ]

    for field in numeric_fields:
        actual_val = actual.get(field)
        expected_val = expected.get(field)

        # Handle None values
        if actual_val is None and expected_val is None:
            continue
        if actual_val is None or expected_val is None:
            print(f"{field}: One value is None (actual={actual_val}, expected={expected_val})")
            return False

        # Compare with tolerance
        if abs(actual_val - expected_val) > tolerance:
            print(f"{field}: Value mismatch (actual={actual_val}, expected={expected_val})")
            return False

    return True


def generate_date_range_records(start_date: str, days: int) -> List[Dict[str, Any]]:
    """
    Generate sample records for a date range.

    Args:
        start_date: Start date in YYYY-MM-DD format
        days: Number of days to generate

    Returns:
        List of raw data records
    """
    records = []
    base_date = datetime.strptime(start_date, "%Y-%m-%d")

    for i in range(days):
        current_date = base_date + timedelta(days=i)

        # Generate varying values
        advanced = 2500 + (i * 100) % 2000
        declined = 6000 - (i * 50) % 2000
        unchanged = 3000 + (i * 20) % 1000

        record = {
            "date": current_date.strftime("%Y-%m-%d"),
            "trading_volume": 8000 + i * 10,
            "advanced_stocks": advanced,
            "declined_stocks": declined,
            "unchanged_stocks": unchanged,
            "turnover_hkd": 320000000000 + i * 1000000000,
            "deals": 4800000 + i * 10000,
            "morning_close": 25000.0 + i * 10,
            "afternoon_close": 25050.0 + i * 10,
            "change_value": -100 + i * 20,
            "change_percent": -0.4 + i * 0.08
        }
        records.append(record)

    return records


# =============================================================================
# Test Database Setup
# =============================================================================

def setup_test_database(conn):
    """
    Set up test database schema if not exists.

    This creates the necessary tables and triggers for testing.
    Call this before running integration tests.

    Args:
        conn: Database connection object

    Returns:
        True if setup successful
    """
    try:
        cursor = conn.cursor()

        # Check if tables exist
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'hkex_raw_data'
            );
        """)
        raw_exists = cursor.fetchone()[0]

        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'market_indicators'
            );
        """)
        indicators_exist = cursor.fetchone()[0]

        if not raw_exists or not indicators_exist:
            print("Warning: Test database tables not found. "
                  "Please run database migrations first.")
            return False

        # Check if trigger exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM pg_trigger
                WHERE tgname = 'calculate_indicators_trigger'
            );
        """)
        trigger_exists = cursor.fetchone()[0]

        if not trigger_exists:
            print("Warning: calculate_indicators trigger not found. "
                  "Indicator auto-calculation may not work.")

        cursor.close()
        return True

    except Exception as e:
        print(f"Error setting up test database: {e}")
        return False


# =============================================================================
# API Response Validators
# =============================================================================

def validate_performance_response(response: Dict) -> bool:
    """
    Validate performance analytics API response structure.

    Args:
        response: API response dictionary

    Returns:
        True if response structure is valid
    """
    required_keys = ["return_attribution", "risk_exposure", "correlations", "stress_test"]

    # Check top-level keys
    for key in required_keys:
        if key not in response:
            print(f"Missing required key: {key}")
            return False

    # Check return_attribution structure
    attribution = response["return_attribution"]
    if "total" not in attribution or "breakdown" not in attribution:
        print("Invalid return_attribution structure")
        return False

    if len(attribution["breakdown"]) != 3:
        print(f"Expected 3 breakdown items, got {len(attribution['breakdown'])}")
        return False

    # Check breakdown items
    for item in attribution["breakdown"]:
        if not all(k in item for k in ["indicator", "contribution", "percentage"]):
            print("Invalid breakdown item structure")
            return False

    # Check stress_test scenarios
    stress_test = response["stress_test"]
    if not isinstance(stress_test, list) or len(stress_test) != 4:
        print(f"Expected 4 stress test scenarios, got {len(stress_test)}")
        return False

    return True


def validate_indicators_response(response: Dict) -> bool:
    """
    Validate market indicators API response structure.

    Args:
        response: API response dictionary

    Returns:
        True if response structure is valid
    """
    if "data" not in response or "count" not in response:
        print("Missing 'data' or 'count' in response")
        return False

    if not isinstance(response["data"], list):
        print("'data' should be a list")
        return False

    if response["count"] != len(response["data"]):
        print(f"Count mismatch: expected {response['count']}, got {len(response['data'])}")
        return False

    # Check indicator structure if data exists
    if response["data"]:
        for item in response["data"]:
            required_fields = [
                "date", "advance_decline_ratio", "volume_change_percent",
                "sentiment_score", "breadth_momentum"
            ]
            for field in required_fields:
                if field not in item:
                    print(f"Missing field in indicator: {field}")
                    return False

    return True
