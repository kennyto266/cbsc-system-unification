"""
Market Indicator Service

Service layer for market indicator calculations and data retrieval.
Extracted from API endpoints for better testability and reusability.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


# Supported time ranges for date calculations
TIME_RANGES = {
    '1w': 7,    # 7 days
    '1m': 30,   # 30 days
    '3m': 90,   # 90 days
    '1y': 365,  # 365 days
}


def get_date_range(time_range: str) -> Tuple[datetime, datetime]:
    """
    Calculate date range from time_range string.

    Args:
        time_range: Time range identifier ('1w', '1m', '3m', '1y')

    Returns:
        Tuple of (start_date, end_date) as datetime objects

    Raises:
        ValueError: If time_range is not supported
    """
    if time_range not in TIME_RANGES:
        raise ValueError(
            f"Invalid time_range: {time_range}. "
            f"Supported values: {list(TIME_RANGES.keys())}"
        )

    now = datetime.now()
    days = TIME_RANGES[time_range]
    start_date = now - timedelta(days=days)

    return start_date, now


def fetch_indicators(conn, start_date: datetime, end_date: datetime) -> List[Dict]:
    """
    Fetch market indicators from database.

    Args:
        conn: Database connection object
        start_date: Start date for query
        end_date: End date for query

    Returns:
        List of indicator dictionaries with keys:
        - date: ISO format date string
        - advance_decline_ratio: Float ratio or None
        - volume_change_percent: Float percentage or None
        - sentiment_score: Float score or None
        - breadth_momentum: Float momentum or None

    Raises:
        Exception: If database query fails
    """
    from psycopg2.extras import RealDictCursor

    cursor = conn.cursor(cursor_factory=RealDictCursor)

    query = """
        SELECT
            date,
            advance_decline_ratio,
            volume_change_percent,
            sentiment_score,
            breadth_momentum
        FROM market_indicators
        WHERE date >= %s AND date <= %s
        ORDER BY date ASC
    """

    cursor.execute(query, (start_date, end_date))
    indicators = []

    for row in cursor.fetchall():
        indicators.append({
            'date': row['date'].isoformat() if row['date'] else None,
            'advance_decline_ratio': float(row['advance_decline_ratio']) if row['advance_decline_ratio'] else None,
            'volume_change_percent': float(row['volume_change_percent']) if row['volume_change_percent'] else None,
            'sentiment_score': float(row['sentiment_score']) if row['sentiment_score'] else None,
            'breadth_momentum': float(row['breadth_momentum']) if row['breadth_momentum'] else None
        })

    cursor.close()
    return indicators


def calculate_return_attribution(indicators: List[Dict]) -> Dict:
    """
    Calculate return attribution from market indicators.

    Computes weighted contributions from:
    - Advance/decline ratio (40% weight)
    - Volume change (30% weight)
    - Sentiment score/breadth (30% weight)

    Args:
        indicators: List of indicator dictionaries

    Returns:
        Dictionary with:
        - total: Total attribution score
        - breakdown: List of attribution by category with:
          - indicator: Category name
          - contribution: Weighted contribution
          - percentage: Percentage of total
    """
    # Handle empty data
    if not indicators:
        return {
            "total": 0.0,
            "breakdown": [
                {"indicator": "市場漲跌情緒", "contribution": 0.0, "percentage": 0.0},
                {"indicator": "成交量活躍度", "contribution": 0.0, "percentage": 0.0},
                {"indicator": "市場廣度", "contribution": 0.0, "percentage": 0.0},
            ]
        }

    # Aggregate indicators
    total_adv_dec_ratio = sum(i.get('advance_decline_ratio') or 0 for i in indicators)
    total_volume_change = sum(i.get('volume_change_percent') or 0 for i in indicators)
    total_sentiment = sum(i.get('sentiment_score') or 0 for i in indicators)

    count = len(indicators)
    avg_ratio = total_adv_dec_ratio / count if count else 0
    avg_volume = total_volume_change / count if count else 0
    avg_sentiment = total_sentiment / count if count else 0

    # Calculate contributions (weighted)
    contribution_ratio = avg_ratio * 0.4
    contribution_volume = avg_volume * 0.3
    contribution_breadth = (avg_sentiment / 100) * 0.3 * 100

    total = contribution_ratio + contribution_volume + contribution_breadth

    return {
        "total": round(total, 2),
        "breakdown": [
            {
                "indicator": "市場漲跌情緒",
                "contribution": round(contribution_ratio, 2),
                "percentage": round((contribution_ratio / total * 100) if total else 0, 1)
            },
            {
                "indicator": "成交量活躍度",
                "contribution": round(contribution_volume, 2),
                "percentage": round((contribution_volume / total * 100) if total else 0, 1)
            },
            {
                "indicator": "市場廣度",
                "contribution": round(contribution_breadth, 2),
                "percentage": round((contribution_breadth / total * 100) if total else 0, 1)
            },
        ]
    }


def get_mock_data() -> Dict:
    """
    Return mock performance analytics data when no real data available.

    Used as fallback when database is unavailable or returns no data.

    Returns:
        Dictionary with mock analytics data including:
        - return_attribution: Attribution breakdown
        - risk_exposure: Risk metrics by category
        - correlations: Correlation matrix and strategies
        - stress_test: Stress test scenarios
    """
    return {
        "return_attribution": {
            "total": 5.23,
            "breakdown": [
                {"indicator": "市場漲跌情緒", "contribution": 2.1, "percentage": 40.2},
                {"indicator": "成交量活躍度", "contribution": 1.5, "percentage": 28.7},
                {"indicator": "市場廣度", "contribution": 1.6, "percentage": 30.6}
            ]
        },
        "risk_exposure": {
            "systematic": 0.65,
            "interestRate": 0.72,
            "liquidity": 0.45,
            "economicGrowth": 0.58,
            "fx": 0.38
        },
        "correlations": {
            "matrix": [[1.0, 0.3, 0.5], [0.3, 1.0, 0.4], [0.5, 0.4, 1.0]],
            "strategies": ["策略A", "策略B", "策略C"]
        },
        "stress_test": [
            {"scenario": "基準", "expectedReturn": 8.5, "maxDrawdown": -12.3, "sharpeRatio": 1.2},
            {"scenario": "利率+200bp", "expectedReturn": 6.2, "maxDrawdown": -15.8, "sharpeRatio": 0.9},
            {"scenario": "經濟衰退", "expectedReturn": -3.4, "maxDrawdown": -25.1, "sharpeRatio": -0.5},
            {"scenario": "市場崩盤", "expectedReturn": -15.2, "maxDrawdown": -40.5, "sharpeRatio": -1.2}
        ]
    }
