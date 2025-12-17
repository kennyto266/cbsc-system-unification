"""
CBSC Data API Routes
Provides endpoints for accessing and analyzing CBBC market data
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
import logging

from ...services.cbbc_data_reader import get_cbbc_reader, CBBCDataReader
from ...services.market_sentiment_analyzer import get_sentiment_analyzer, MarketSentimentAnalyzer
from ...auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/cbbc",
    tags=["cbbc"],
    responses={404: {"description": "Not found"}},
)


@router.get("/data/latest")
async def get_latest_cbbc_data(
    current_user: dict = Depends(get_current_user),
    cbbc_reader: CBBCDataReader = Depends(get_cbbc_reader)
):
    """
    Get the latest CBBC data point

    Returns:
        Latest CBBC market data
    """
    try:
        # Ensure data is loaded
        if cbbc_reader._data is None:
            await cbbc_reader.load_data()
            cbbc_reader.preprocess_data()

        # Get latest data point
        latest_data = cbbc_reader._processed_data.iloc[-1]

        return {
            "timestamp": latest_data.name.isoformat() if hasattr(latest_data.name, 'isoformat') else str(latest_data.name),
            "hsif_close": float(latest_data['HSIF_Close']) if pd.notna(latest_data['HSIF_Close']) else None,
            "hsif_return": float(latest_data['HSIF_Return']) if pd.notna(latest_data['HSIF_Return']) else None,
            "bull_price": float(latest_data['Bull_Price']) if pd.notna(latest_data['Bull_Price']) else None,
            "bear_price": float(latest_data['Bear_Price']) if pd.notna(latest_data['Bear_Price']) else None,
            "bull_bear_ratio": float(latest_data['Bull_Bear_Ratio']) if pd.notna(latest_data['Bull_Bear_Ratio']) else None,
            "fear_greed_index": float(latest_data['Fear_Greed_Index']) if pd.notna(latest_data['Fear_Greed_Index']) else None,
            "rsi_signal": float(latest_data['RSI_Signal']) if pd.notna(latest_data['RSI_Signal']) else None,
            "realized_volatility": float(latest_data['Realized_Volatility']) if pd.notna(latest_data['Realized_Volatility']) else None,
            "volume": int(latest_data['Volume']) if pd.notna(latest_data['Volume']) else None
        }

    except Exception as e:
        logger.error(f"Error getting latest CBBC data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve data: {str(e)}")


@router.get("/data/history")
async def get_cbbc_history(
    days: int = Query(default=30, description="Number of days to retrieve"),
    current_user: dict = Depends(get_current_user),
    cbbc_reader: CBBCDataReader = Depends(get_cbbc_reader)
):
    """
    Get historical CBBC data

    Args:
        days: Number of days of historical data to return

    Returns:
        Historical CBBC market data
    """
    try:
        # Ensure data is loaded
        if cbbc_reader._data is None:
            await cbbc_reader.load_data()
            cbbc_reader.preprocess_data()

        # Get historical data
        cutoff_date = datetime.now() - timedelta(days=days)
        historical_data = cbbc_reader._processed_data[cbbc_reader._processed_data.index >= cutoff_date]

        # Convert to list of dictionaries
        data_points = []
        for index, row in historical_data.iterrows():
            data_points.append({
                "date": index.isoformat() if hasattr(index, 'isoformat') else str(index),
                "hsif_close": float(row['HSIF_Close']) if pd.notna(row['HSIF_Close']) else None,
                "hsif_return": float(row['HSIF_Return']) if pd.notna(row['HSIF_Return']) else None,
                "bull_price": float(row['Bull_Price']) if pd.notna(row['Bull_Price']) else None,
                "bear_price": float(row['Bear_Price']) if pd.notna(row['Bear_Price']) else None,
                "bull_bear_ratio": float(row['Bull_Bear_Ratio']) if pd.notna(row['Bull_Bear_Ratio']) else None,
                "fear_greed_index": float(row['Fear_Greed_Index']) if pd.notna(row['Fear_Greed_Index']) else None,
                "rsi_signal": float(row['RSI_Signal']) if pd.notna(row['RSI_Signal']) else None,
                "realized_volatility": float(row['Realized_Volatility']) if pd.notna(row['Realized_Volatility']) else None,
                "volume": int(row['Volume']) if pd.notna(row['Volume']) else None
            })

        return {
            "data_points": data_points,
            "total_records": len(data_points),
            "date_range": {
                "start": data_points[0]["date"] if data_points else None,
                "end": data_points[-1]["date"] if data_points else None
            }
        }

    except Exception as e:
        logger.error(f"Error getting CBBC history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve history: {str(e)}")


@router.get("/sentiment/current")
async def get_current_sentiment(
    current_user: dict = Depends(get_current_user),
    cbbc_reader: CBBCDataReader = Depends(get_cbbc_reader),
    sentiment_analyzer: MarketSentimentAnalyzer = Depends(get_sentiment_analyzer)
):
    """
    Get current market sentiment analysis

    Returns:
        Current market sentiment metrics and level
    """
    try:
        # Ensure data is loaded and processed
        if cbbc_reader._processed_data is None:
            await cbbc_reader.load_data()
            cbbc_reader.preprocess_data()

        # Analyze sentiment
        sentiment_metrics = sentiment_analyzer.analyze_sentiment(cbbc_reader._processed_data)
        sentiment_summary = sentiment_analyzer.get_sentiment_summary(sentiment_metrics)

        return {
            "sentiment_metrics": {
                "fear_greed_score": sentiment_metrics.fear_greed_score,
                "bull_bear_momentum": sentiment_metrics.bull_bear_momentum,
                "volume_profile": sentiment_metrics.volume_profile,
                "volatility_trend": sentiment_metrics.volatility_trend,
                "support_resistance_levels": sentiment_metrics.support_resistance_levels,
                "market_breadth": sentiment_metrics.market_breadth
            },
            "sentiment_summary": sentiment_summary,
            "market_phase": sentiment_analyzer.identify_market_phase(cbbc_reader._processed_data),
            "volatility_regime": sentiment_analyzer.assess_volatility_regime(cbbc_reader._processed_data),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting sentiment analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze sentiment: {str(e)}")


@router.get("/sentiment/recommendation")
async def get_trading_recommendation(
    current_user: dict = Depends(get_current_user),
    cbbc_reader: CBBCDataReader = Depends(get_cbbc_reader),
    sentiment_analyzer: MarketSentimentAnalyzer = Depends(get_sentiment_analyzer)
):
    """
    Get trading recommendation based on sentiment analysis

    Returns:
        Trading recommendation with entry/exit zones
    """
    try:
        # Ensure data is loaded and processed
        if cbbc_reader._processed_data is None:
            await cbbc_reader.load_data()
            cbbc_reader.preprocess_data()

        # Analyze sentiment and generate recommendation
        sentiment_metrics = sentiment_analyzer.analyze_sentiment(cbbc_reader._processed_data)
        recommendation = sentiment_analyzer.generate_trading_recommendation(
            cbbc_reader._processed_data,
            sentiment_metrics
        )

        return {
            "recommendation": {
                "action": recommendation.action,
                "confidence": recommendation.confidence,
                "entry_zone": recommendation.entry_zone,
                "exit_zone": recommendation.exit_zone,
                "stop_loss": recommendation.stop_loss,
                "target_price": recommendation.target_price,
                "position_size": recommendation.position_size,
                "holding_period": recommendation.holding_period
            },
            "rationale": {
                "sentiment_level": sentiment_analyzer.get_current_sentiment_level(sentiment_metrics).value,
                "market_phase": sentiment_analyzer.identify_market_phase(cbbc_reader._processed_data).value,
                "volatility_regime": sentiment_analyzer.assess_volatility_regime(cbbc_reader._processed_data).value
            },
            "generated_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error generating recommendation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate recommendation: {str(e)}")


@router.get("/signals")
async def get_trading_signals(
    current_user: dict = Depends(get_current_user),
    cbbc_reader: CBBCDataReader = Depends(get_cbbc_reader)
):
    """
    Get current trading signals based on CBBC data

    Returns:
        Various trading signals
    """
    try:
        # Ensure data is loaded and processed
        if cbbc_reader._processed_data is None:
            await cbbc_reader.load_data()
            cbbc_reader.preprocess_data()

        # Get signals
        signals = cbbc_reader.get_trading_signals()

        return {
            "signals": signals,
            "market_sentiment": cbbc_reader.calculate_market_sentiment(),
            "risk_metrics": cbbc_reader.get_risk_metrics(),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting trading signals: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get signals: {str(e)}")


@router.get("/risk/metrics")
async def get_risk_metrics(
    current_user: dict = Depends(get_current_user),
    cbbc_reader: CBBCDataReader = Depends(get_cbbc_reader)
):
    """
    Get risk metrics based on CBSC data analysis

    Returns:
        Various risk metrics
    """
    try:
        # Ensure data is loaded and processed
        if cbbc_reader._processed_data is None:
            await cbbc_reader.load_data()
            cbbc_reader.preprocess_data()

        # Get risk metrics
        risk_metrics = cbbc_reader.get_risk_metrics()

        return {
            "risk_metrics": risk_metrics,
            "risk_assessment": {
                "volatility_status": "HIGH" if risk_metrics["annualized_volatility"] > 0.25 else "NORMAL",
                "drawdown_status": "CRITICAL" if risk_metrics["max_drawdown"] < -0.2 else "NORMAL",
                "sharpe_status": "EXCELLENT" if risk_metrics["sharpe_ratio"] > 1.5 else "NEEDS_IMPROVEMENT" if risk_metrics["sharpe_ratio"] < 0.5 else "NORMAL"
            },
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting risk metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get risk metrics: {str(e)}")


@router.post("/data/refresh")
async def refresh_cbbc_data(
    data_path: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    cbbc_reader: CBBCDataReader = Depends(get_cbbc_reader)
):
    """
    Refresh CBBC data with new data file

    Args:
        data_path: Path to new data file (optional)

    Returns:
        Status of data refresh
    """
    try:
        # Update data
        success = await cbbc_reader.update_data(data_path)

        if success:
            # Preprocess new data
            cbbc_reader.preprocess_data()

            return {
                "status": "success",
                "message": "CBBC data refreshed successfully",
                "data_path": data_path or cbbc_reader.data_path,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to refresh CBBC data")

    except Exception as e:
        logger.error(f"Error refreshing CBBC data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to refresh data: {str(e)}")


@router.get("/export/data")
async def export_cbbc_data(
    current_user: dict = Depends(get_current_user),
    cbbc_reader: CBBCDataReader = Depends(get_cbbc_reader)
):
    """
    Export processed CBBC data for use in strategies

    Returns:
        Download link for exported data
    """
    try:
        # Generate export filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_path = f"exports/cbsc_processed_{timestamp}.csv"

        # Export data
        cbbc_reader.export_data_for_strategy(export_path)

        return {
            "status": "success",
            "message": "Data exported successfully",
            "export_path": export_path,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error exporting CBBC data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to export data: {str(e)}")