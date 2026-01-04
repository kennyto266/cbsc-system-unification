"""
Market Data Endpoints
Provides performance analytics data from market_indicators table
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import logging

# Use project standard database connection
import psycopg2
from psycopg2.extras import RealDictCursor

# Import service layer functions
from services.market_indicator_service import (
    get_date_range,
    fetch_indicators,
    calculate_return_attribution,
    get_mock_data
)

# Database configuration
DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "cbsc_strategy"
DB_USER = "cbsc_user"
DB_PASSWORD = "cbsc_password"

def get_db_connection():
    """Get raw database connection for custom SQL queries"""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

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
        # Calculate date range using service
        start_date, end_date = get_date_range(time_range)

        # Query market indicators from database
        conn = get_db_connection()

        # Fetch indicators using service
        indicators = fetch_indicators(conn, start_date, end_date)

        # Calculate return attribution using service
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
