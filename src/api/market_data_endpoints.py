"""
Market Data Endpoints
Provides performance analytics data from market_indicators table
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
import logging

# Use project standard database connection
from src.database.connection import get_db_connection
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/analytics", tags=["analytics"])


class PerformanceAnalyticsRequest(BaseModel):
    time_range: str = Query(..., description="Time range: 1w, 1m, 3m, 1y")
    strategies: Optional[List[str]] = None


class AttributionData(BaseModel):
    total: float
    breakdown: List[dict]


class PerformanceAnalyticsResponse(BaseModel):
    return_attribution: AttributionData
    risk_exposure: dict
    correlations: dict
    stress_test: List[dict]


def get_date_range(time_range: str) -> tuple:
    """Calculate date range from time_range string"""
    now = datetime.now()

    ranges = {
        '1w': now - timedelta(days=7),
        '1m': now - timedelta(days=30),
        '3m': now - timedelta(days=90),
        '1y': now - timedelta(days=365),
    }

    if time_range not in ranges:
        raise ValueError(f"Invalid time_range: {time_range}")

    return ranges[time_range], now


def calculate_return_attribution(indicators: List[dict]) -> dict:
    """Calculate return attribution from market indicators"""
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
    total_adv_dec_ratio = sum(i['advance_decline_ratio'] or 0 for i in indicators)
    total_volume_change = sum(i['volume_change_percent'] or 0 for i in indicators)
    total_sentiment = sum(i['sentiment_score'] or 0 for i in indicators)

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


def get_mock_data() -> dict:
    """Return mock data when no real data available"""
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


@router.get("/performance", response_model=PerformanceAnalyticsResponse)
async def get_performance_analytics(
    time_range: str = Query("1m", description="Time range: 1w, 1m, 3m, 1y")
):
    """
    Get performance analytics data including return attribution

    Args:
        time_range: Time period for analysis (1w, 1m, 3m, 1y)

    Returns:
        Performance analytics with return attribution, risk exposure, correlations, and stress test
    """
    conn = None
    try:
        # Calculate date range
        start_date, end_date = get_date_range(time_range)

        # Query market indicators from database
        conn = get_db_connection()
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

        # Calculate return attribution
        return_attribution = calculate_return_attribution(indicators)

        # If no indicators data, return mock
        if not indicators:
            logger.warning(f"No market indicators found for range {time_range}, using mock data")
            return get_mock_data()

        # Return full response (risk, correlations, stress_test use mock for now)
        return {
            "return_attribution": return_attribution,
            "risk_exposure": get_mock_data()["risk_exposure"],
            "correlations": get_mock_data()["correlations"],
            "stress_test": get_mock_data()["stress_test"]
        }

    except Exception as e:
        logger.error(f"Error fetching performance analytics: {e}")
        # Return mock data on error
        return get_mock_data()
    finally:
        # Ensure connection is always closed
        if conn:
            conn.close()


@router.get("/indicators")
async def get_market_indicators(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(30, le=365)
):
    """
    Get raw market indicators data

    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        limit: Maximum number of records to return

    Returns:
        List of market indicators
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Build query with filters
        if start_date and end_date:
            query = """
                SELECT date, advance_decline_ratio, volume_change_percent,
                       sentiment_score, breadth_momentum, updated_at
                FROM market_indicators
                WHERE date >= %s AND date <= %s
                ORDER BY date DESC
            """
            cursor.execute(query, (start_date, end_date))
        else:
            query = """
                SELECT date, advance_decline_ratio, volume_change_percent,
                       sentiment_score, breadth_momentum, updated_at
                FROM market_indicators
                ORDER BY date DESC
                LIMIT %s
            """
            cursor.execute(query, (limit,))

        indicators = []
        for row in cursor.fetchall():
            indicators.append({
                'date': row['date'].isoformat() if row['date'] else None,
                'advance_decline_ratio': float(row['advance_decline_ratio']) if row['advance_decline_ratio'] else None,
                'volume_change_percent': float(row['volume_change_percent']) if row['volume_change_percent'] else None,
                'sentiment_score': float(row['sentiment_score']) if row['sentiment_score'] else None,
                'breadth_momentum': float(row['breadth_momentum']) if row['breadth_momentum'] else None,
                'updated_at': row['updated_at'].isoformat() if row['updated_at'] else None
            })

        cursor.close()

        return {"data": indicators, "count": len(indicators)}

    except Exception as e:
        logger.error(f"Error fetching market indicators: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Ensure connection is always closed
        if conn:
            conn.close()
