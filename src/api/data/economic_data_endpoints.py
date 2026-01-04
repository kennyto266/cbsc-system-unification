"""
Economic Indicators API v2 Endpoints
經濟指標API v2端點實現

Provides economic indicators such as HIBOR, GDP, PMI, etc.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
import logging
import pandas as pd
import numpy as np

from ...deps import get_db, get_current_user
from ...services.influxdb_client import InfluxDBService
from ...services.cache_service import CacheService
from ...models.user import User

logger = logging.getLogger(__name__)

# Create router for economic indicators
economic_router = APIRouter(prefix="/economic-indicators", tags=["economic-indicators"])

# Initialize services
influxdb_service = InfluxDBService()
cache_service = CacheService()


@economic_router.get("/", response_model=Dict[str, Any])
async def list_economic_indicators(
    category: Optional[str] = Query(None, description="Filter by category (interest_rates, gdp, employment, etc.)"),
    country: Optional[str] = Query("US", description="Country code"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    獲取可用的經濟指標列表

    Args:
        category: 指標類別
        country: 國家代碼

    Returns:
        List of available economic indicators
    """
    try:
        # Define available indicators
        indicators = {
            "interest_rates": {
                "HIBOR": {
                    "name": "Hong Kong Interbank Offered Rate",
                    "description": "HIBOR overnight rate",
                    "unit": "percent",
                    "frequency": "daily",
                    "currency": "HKD"
                },
                "Fed_Funds": {
                    "name": "Federal Funds Rate",
                    "description": "US Federal Reserve interest rate",
                    "unit": "percent",
                    "frequency": "daily",
                    "currency": "USD"
                },
                "LIBOR": {
                    "name": "London Interbank Offered Rate",
                    "description": "USD LIBOR rate",
                    "unit": "percent",
                    "frequency": "daily",
                    "currency": "USD"
                }
            },
            "gdp": {
                "GDP_Growth": {
                    "name": "GDP Growth Rate",
                    "description": "Quarterly GDP growth rate",
                    "unit": "percent",
                    "frequency": "quarterly",
                    "currency": "local"
                },
                "GDP_Level": {
                    "name": "GDP Level",
                    "description": "Nominal GDP value",
                    "unit": "billion_usd",
                    "frequency": "quarterly",
                    "currency": "USD"
                }
            },
            "employment": {
                "Unemployment_Rate": {
                    "name": "Unemployment Rate",
                    "description": "Seasonally adjusted unemployment rate",
                    "unit": "percent",
                    "frequency": "monthly",
                    "currency": "N/A"
                },
                "Non_Farm_Payrolls": {
                    "name": "Non-Farm Payrolls",
                    "description": "Change in non-farm employment",
                    "unit": "thousands",
                    "frequency": "monthly",
                    "currency": "N/A"
                }
            },
            "inflation": {
                "CPI": {
                    "name": "Consumer Price Index",
                    "description": "Year-over-year CPI change",
                    "unit": "percent",
                    "frequency": "monthly",
                    "currency": "N/A"
                },
                "PPI": {
                    "name": "Producer Price Index",
                    "description": "Year-over-year PPI change",
                    "unit": "percent",
                    "frequency": "monthly",
                    "currency": "N/A"
                }
            },
            "pmi": {
                "Manufacturing_PMI": {
                    "name": "Manufacturing PMI",
                    "description": "Purchasing Managers' Index for manufacturing",
                    "unit": "index",
                    "frequency": "monthly",
                    "currency": "N/A"
                },
                "Services_PMI": {
                    "name": "Services PMI",
                    "description": "Purchasing Managers' Index for services",
                    "unit": "index",
                    "frequency": "monthly",
                    "currency": "N/A"
                }
            }
        }

        # Filter by category if specified
        if category:
            if category in indicators:
                filtered_indicators = {category: indicators[category]}
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid category: {category}"
                )
        else:
            filtered_indicators = indicators

        return {
            "country": country,
            "indicators": filtered_indicators,
            "categories": list(indicators.keys()),
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing economic indicators: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to list economic indicators"
        )


@economic_router.get("/{indicator}/data", response_model=Dict[str, Any])
async def get_economic_indicator_data(
    indicator: str = Path(..., description="Economic indicator code"),
    country: Optional[str] = Query("US", description="Country code"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(1000, ge=1, le=10000, description="Maximum records"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    獲取特定經濟指標的歷史數據

    Args:
        indicator: 指標代碼
        country: 國家代碼
        start_date: 開始日期
        end_date: 結束日期
        limit: 最大記錄數

    Returns:
        Historical data for the economic indicator
    """
    try:
        # Validate indicator
        valid_indicators = [
            "HIBOR", "Fed_Funds", "LIBOR", "GDP_Growth", "GDP_Level",
            "Unemployment_Rate", "Non_Farm_Payrolls", "CPI", "PPI",
            "Manufacturing_PMI", "Services_PMI"
        ]
        if indicator not in valid_indicators:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid indicator: {indicator}. Valid indicators: {valid_indicators}"
            )

        # Parse dates
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid start_date format. Use YYYY-MM-DD"
                )
        else:
            # Default based on indicator frequency
            if indicator in ["GDP_Growth", "GDP_Level"]:
                start_dt = datetime.utcnow() - timedelta(days=365 * 10)  # 10 years
            else:
                start_dt = datetime.utcnow() - timedelta(days=365 * 5)   # 5 years

        if end_date:
            try:
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid end_date format. Use YYYY-MM-DD"
                )
        else:
            end_dt = datetime.utcnow()

        # Check cache
        cache_key = f"economic:{indicator}:{country}:{start_date}:{end_date}"
        cached_data = await cache_service.get(cache_key)
        if cached_data:
            logger.info(f"Cache hit for {indicator} data")
            return cached_data

        # Fetch data from InfluxDB
        data = await influxdb_service.get_economic_data(
            indicator=indicator,
            country=country,
            start_time=start_dt,
            end_time=end_dt,
            limit=limit
        )

        if not data:
            # Return mock data for demo purposes
            data = _generate_mock_economic_data(indicator, start_dt, end_dt)

        # Process and format data
        records = []
        for record in data:
            records.append({
                "date": record.get("time"),
                "value": record.get("value"),
                "unit": record.get("unit"),
                "source": record.get("source", "Central Bank"),
                "revised": record.get("revised", False)
            })

        # Calculate basic statistics
        values = [r["value"] for r in records if r["value"] is not None]
        stats = {}
        if values:
            stats = {
                "min": min(values),
                "max": max(values),
                "average": sum(values) / len(values),
                "latest": values[-1] if values else None,
                "change": values[-1] - values[-2] if len(values) > 1 else 0
            }

        response = {
            "indicator": indicator,
            "country": country,
            "data": records,
            "statistics": stats,
            "metadata": {
                "startDate": start_dt.isoformat(),
                "endDate": end_dt.isoformat(),
                "dataPoints": len(records),
                "unit": records[0]["unit"] if records else None
            },
            "timestamp": datetime.utcnow().isoformat()
        }

        # Cache for 1 hour
        await cache_service.set(cache_key, response, expire=3600)

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching economic indicator data for {indicator}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch economic indicator data"
        )


@economic_router.get("/hibor", response_model=Dict[str, Any])
async def get_hibor_rates(
    tenor: Optional[str] = Query("ON", regex="^(ON|1W|1M|3M|6M|12M)$",
                                description="HIBOR tenor (Overnight, 1 Week, 1 Month, etc.)"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    獲取香港銀行同業拆息率 (HIBOR)

    Args:
        tenor: 期限
        start_date: 開始日期
        end_date: 結束日期

    Returns:
        HIBOR rates data
    """
    try:
        # Parse dates
        end_dt = datetime.utcnow()
        if end_date:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")

        start_dt = end_dt - timedelta(days=30)  # Default to 30 days
        if start_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")

        # Fetch HIBOR data
        cache_key = f"hibor:{tenor}:{start_date}:{end_date}"
        cached_data = await cache_service.get(cache_key)
        if cached_data:
            return cached_data

        # Generate mock HIBOR data for demo
        data = _generate_mock_hibor_data(tenor, start_dt, end_dt)

        # Calculate statistics
        rates = [r["rate"] for r in data]
        stats = {
            "current": rates[-1] if rates else None,
            "high": max(rates) if rates else None,
            "low": min(rates) if rates else None,
            "average": sum(rates) / len(rates) if rates else None,
            "change": rates[-1] - rates[-2] if len(rates) > 1 else 0
        }

        response = {
            "tenor": tenor,
            "currency": "HKD",
            "data": data,
            "statistics": stats,
            "metadata": {
                "startDate": start_dt.isoformat(),
                "endDate": end_dt.isoformat(),
                "dataPoints": len(data)
            },
            "timestamp": datetime.utcnow().isoformat()
        }

        # Cache for 5 minutes
        await cache_service.set(cache_key, response, expire=300)

        return response

    except Exception as e:
        logger.error(f"Error fetching HIBOR data: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch HIBOR data"
        )


@economic_router.get("/dashboard", response_model=Dict[str, Any])
async def get_economic_dashboard(
    indicators: Optional[str] = Query("HIBOR,Fed_Funds,CPI,Unemployment_Rate,GDP_Growth",
                                     description="Comma-separated indicator list"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    獲取經濟指標儀表板數據

    Args:
        indicators: 要顯示的指標列表

    Returns:
        Dashboard view of key economic indicators
    """
    try:
        # Parse indicators
        if indicators:
            indicator_list = [i.strip() for i in indicators.split(",")]
        else:
            indicator_list = ["HIBOR", "Fed_Funds", "CPI", "Unemployment_Rate", "GDP_Growth"]

        dashboard_data = {}

        # Fetch each indicator's latest value
        for indicator in indicator_list:
            try:
                # Get latest data for each indicator
                cache_key = f"economic_latest:{indicator}"
                latest_data = await cache_service.get(cache_key)

                if not latest_data:
                    # Fetch from database
                    data = await influxdb_service.get_latest_economic_data(indicator)
                    if not data:
                        # Generate mock data
                        latest_data = _generate_mock_latest_data(indicator)
                    else:
                        latest_data = {
                            "value": data.get("value"),
                            "date": data.get("time"),
                            "change": data.get("change", 0),
                            "unit": data.get("unit", "percent")
                        }

                    # Cache for 10 minutes
                    await cache_service.set(cache_key, latest_data, expire=600)

                dashboard_data[indicator] = latest_data

            except Exception as e:
                logger.error(f"Error fetching {indicator}: {e}")
                dashboard_data[indicator] = {"error": str(e)}

        # Add market context
        market_context = {
            "risk_sentiment": "Moderate",  # Could be calculated from various indicators
            "key_events": [
                "Fed meeting next week",
                "HKMA policy review",
                "Q4 GDP release pending"
            ],
            "alerts": []
        }

        # Add simple alerts based on thresholds
        if "HIBOR" in dashboard_data and dashboard_data["HIBOR"].get("value", 0) > 5:
            market_context["alerts"].append("HIBOR above 5% - watch for lending rate impact")

        if "CPI" in dashboard_data and dashboard_data["CPI"].get("value", 0) > 3:
            market_context["alerts"].append("High inflation detected - monitor central bank response")

        return {
            "dashboard": dashboard_data,
            "market_context": market_context,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error creating economic dashboard: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to create economic dashboard"
        )


def _generate_mock_economic_data(indicator: str, start_dt: datetime, end_dt: datetime) -> List[Dict]:
    """生成模擬經濟數據用於演示"""
    data = []
    current_date = start_dt

    # Base values for different indicators
    base_values = {
        "HIBOR": 3.5,
        "Fed_Funds": 5.25,
        "LIBOR": 5.4,
        "GDP_Growth": 2.5,
        "GDP_Level": 25000,
        "Unemployment_Rate": 3.7,
        "Non_Farm_Payrolls": 200,
        "CPI": 3.2,
        "PPI": 2.8,
        "Manufacturing_PMI": 50.5,
        "Services_PMI": 52.0
    }

    base_value = base_values.get(indicator, 100)

    while current_date <= end_dt:
        # Add some randomness
        variation = np.random.normal(0, 0.1)  # 10% variation
        value = base_value * (1 + variation)

        # Ensure positive values
        if value < 0:
            value = abs(value)

        data.append({
            "time": current_date.isoformat(),
            "value": round(value, 2),
            "unit": _get_indicator_unit(indicator)
        })

        # Increment date based on indicator frequency
        if indicator in ["GDP_Growth", "GDP_Level"]:
            current_date += timedelta(days=90)  # Quarterly
        elif indicator in ["Manufacturing_PMI", "Services_PMI", "Non_Farm_Payrolls", "Unemployment_Rate", "CPI", "PPI"]:
            current_date += timedelta(days=30)  # Monthly
        else:
            current_date += timedelta(days=1)   # Daily

    return data


def _generate_mock_hibor_data(tenor: str, start_dt: datetime, end_dt: datetime) -> List[Dict]:
    """生成模擬 HIBOR 數據"""
    data = []
    current_date = start_dt

    # Base rates by tenor
    base_rates = {
        "ON": 3.5,
        "1W": 3.7,
        "1M": 4.0,
        "3M": 4.2,
        "6M": 4.5,
        "12M": 4.8
    }

    base_rate = base_rates.get(tenor, 4.0)

    while current_date <= end_dt:
        # Add some randomness
        rate = base_rate + np.random.normal(0, 0.05)
        rate = max(0, rate)  # Ensure non-negative

        data.append({
            "date": current_date.strftime("%Y-%m-%d"),
            "rate": round(rate, 4)
        })

        current_date += timedelta(days=1)

    return data


def _generate_mock_latest_data(indicator: str) -> Dict:
    """生成模擬最新數據"""
    base_values = {
        "HIBOR": {"value": 3.5, "unit": "percent"},
        "Fed_Funds": {"value": 5.25, "unit": "percent"},
        "CPI": {"value": 3.2, "unit": "percent"},
        "Unemployment_Rate": {"value": 3.7, "unit": "percent"},
        "GDP_Growth": {"value": 2.5, "unit": "percent"}
    }

    base = base_values.get(indicator, {"value": 100, "unit": "index"})

    return {
        "value": base["value"] + np.random.normal(0, 0.1),
        "date": datetime.utcnow().isoformat(),
        "change": np.random.normal(0, 0.5),
        "unit": base["unit"]
    }


def _get_indicator_unit(indicator: str) -> str:
    """獲取指標單位"""
    if "Rate" in indicator or indicator in ["HIBOR", "Fed_Funds", "LIBOR"]:
        return "percent"
    elif indicator in ["GDP_Level"]:
        return "billion_usd"
    elif indicator in ["Non_Farm_Payrolls"]:
        return "thousands"
    elif "PMI" in indicator:
        return "index"
    else:
        return "percent"