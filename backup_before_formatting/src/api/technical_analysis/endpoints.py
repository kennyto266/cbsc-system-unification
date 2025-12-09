"""
技術分析API端點
Technical Analysis API Endpoints
"""

import logging
import time
from datetime import date, datetime, timedelta
from typing import Any, Dict

import psutil
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query

from .engine import NonPriceDataProcessor, ResponseFormatter, TechnicalIndicatorEngine
from .models import (
    BatchRequest,
    BollingerBandsRequest,
    BollingerBandsResponse,
    DataSourceType,
    DateRange,
    ErrorResponse,
    HealthCheckResponse,
    IndicatorType,
    MACDRequest,
    MACDResponse,
    RSIRequest,
    RSIResponse,
)

logger = logging.getLogger(__name__)

# 創建路由器
router = APIRouter(prefix="/api/technical/non-price", tags=["Technical Analysis"])

# 初始化組件
engine = TechnicalIndicatorEngine()
data_processor = NonPriceDataProcessor()
response_formatter = ResponseFormatter()

# 系統啟動時間（用於健康檢查）
start_time = time.time()


@router.post("/rsi", response_model=RSIResponse, responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}})
async def calculate_rsi(request: RSIRequest):
    """計算RSI相對強弱指標"""
    try:
        logger.info(f"RSI calculation request for {request.data_source}")

        # 驗證請求
        _validate_rsi_request(request)

        # 計算RSI
        result = await engine.calculate_rsi(request)

        logger.info(f"RSI calculation completed successfully for {request.data_source}")
        return result

    except ValueError as e:
        logger.warning(f"RSI validation error: {e}")
        raise HTTPException(status_code=400, detail=response_formatter.format_error_response(
            "VALIDATION_ERROR", str(e),
            available_sources=[s.value for s in DataSourceType],
            valid_ranges={
                "period": {"min": 2, "max": 100},
                "overbought_threshold": {"min": 50, "max": 100},
                "oversold_threshold": {"min": 0, "max": 50}
            }
        ))
    except Exception as e:
        logger.error(f"RSI calculation error: {e}")
        raise HTTPException(status_code=500, detail=response_formatter.format_error_response(
            "CALCULATION_ERROR", str(e)
        ))


@router.post("/macd", response_model=MACDResponse, responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}})
async def calculate_macd(request: MACDRequest):
    """計算MACD指標"""
    try:
        logger.info(f"MACD calculation request for {request.data_source}")

        # 驗證請求
        _validate_macd_request(request)

        # 計算MACD
        result = await engine.calculate_macd(request)

        logger.info(f"MACD calculation completed successfully for {request.data_source}")
        return result

    except ValueError as e:
        logger.warning(f"MACD validation error: {e}")
        raise HTTPException(status_code=400, detail=response_formatter.format_error_response(
            "VALIDATION_ERROR", str(e),
            available_sources=[s.value for s in DataSourceType],
            valid_ranges={
                "fast_period": {"min": 1, "max": 50},
                "slow_period": {"min": 1, "max": 100},
                "signal_period": {"min": 1, "max": 50}
            }
        ))
    except Exception as e:
        logger.error(f"MACD calculation error: {e}")
        raise HTTPException(status_code=500, detail=response_formatter.format_error_response(
            "CALCULATION_ERROR", str(e)
        ))


@router.post("/bollinger-bands", response_model=BollingerBandsResponse, responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}})
async def calculate_bollinger_bands(request: BollingerBandsRequest):
    """計算Bollinger Bands布林帶"""
    try:
        logger.info(f"Bollinger Bands calculation request for {request.data_source}")

        # 驗證請求
        _validate_bb_request(request)

        # 計算Bollinger Bands
        result = await engine.calculate_bollinger_bands(request)

        logger.info(f"Bollinger Bands calculation completed successfully for {request.data_source}")
        return result

    except ValueError as e:
        logger.warning(f"Bollinger Bands validation error: {e}")
        raise HTTPException(status_code=400, detail=response_formatter.format_error_response(
            "VALIDATION_ERROR", str(e),
            available_sources=[s.value for s in DataSourceType],
            valid_ranges={
                "period": {"min": 5, "max": 200},
                "std_dev_multiplier": {"min": 0.5, "max": 4.0}
            }
        ))
    except Exception as e:
        logger.error(f"Bollinger Bands calculation error: {e}")
        raise HTTPException(status_code=500, detail=response_formatter.format_error_response(
            "CALCULATION_ERROR", str(e)
        ))


@router.post("/batch", responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}})
async def calculate_batch(request: BatchRequest, background_tasks: BackgroundTasks):
    """批量計算多個技術指標"""
    try:
        logger.info(f"Batch calculation request for {request.data_source} with {len(request.indicators)} indicators")

        # 驗證請求
        _validate_batch_request(request)

        # 批量計算
        result = await engine.calculate_batch(request)

        logger.info(f"Batch calculation completed successfully for {request.data_source}")
        return result

    except ValueError as e:
        logger.warning(f"Batch validation error: {e}")
        raise HTTPException(status_code=400, detail=response_formatter.format_error_response(
            "VALIDATION_ERROR", str(e),
            available_sources=[s.value for s in DataSourceType]
        ))
    except Exception as e:
        logger.error(f"Batch calculation error: {e}")
        raise HTTPException(status_code=500, detail=response_formatter.format_error_response(
            "CALCULATION_ERROR", str(e)
        ))


@router.get("/data-sources", response_model=Dict[str, Any])
async def get_data_sources():
    """獲取可用的非價格數據源列表"""
    try:
        logger.info("Getting available data sources")

        sources = data_processor.get_available_sources()

        response_data = {
            "available_sources": sources,
            "total_sources": len(sources),
            "last_updated": datetime.now()
        }

        logger.info(f"Returned {len(sources)} available data sources")
        return response_data

    except Exception as e:
        logger.error(f"Error getting data sources: {e}")
        raise HTTPException(status_code=500, detail=response_formatter.format_error_response(
            "DATA_SOURCES_ERROR", str(e)
        ))


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """API健康檢查"""
    try:
        uptime = time.time() - start_time

        # 獲取系統信息
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()

        # 檢查各組件狀態
        available_indicators = [t.value for t in IndicatorType]
        available_data_sources = [s.value for s in DataSourceType]

        system_status = {
            "cpu_usage_percent": cpu_percent,
            "memory_usage_percent": memory.percent,
            "available_memory_gb": memory.available / (1024**3),
            "disk_usage_percent": psutil.disk_usage('/').percent,
            "cache_status": "active" if len(engine.cache) > 0 else "empty",
            "cached_items": len(engine.cache)
        }

        response = HealthCheckResponse(
            status="healthy",
            version="1.0.0",
            uptime_seconds=uptime,
            available_indicators=[IndicatorType(t) for t in available_indicators],
            available_data_sources=[DataSourceType(s) for s in available_data_sources],
            system_status=system_status
        )

        return response

    except Exception as e:
        logger.error(f"Health check error: {e}")
        return HealthCheckResponse(
            status="unhealthy",
            version="1.0.0",
            uptime_seconds=0,
            available_indicators=[],
            available_data_sources=[],
            system_status={"error": str(e)}
        )


@router.get("/indicators")
async def get_available_indicators():
    """獲取支持的技術指標列表"""
    try:
        indicators = [
            {
                "name": "RSI",
                "description": "Relative Strength Index - 相對強弱指標",
                "parameters": [
                    {"name": "period", "type": "integer", "default": 14, "range": [2, 100]},
                    {"name": "overbought_threshold", "type": "float", "default": 70, "range": [50, 100]},
                    {"name": "oversold_threshold", "type": "float", "default": 30, "range": [0, 50]}
                ]
            },
            {
                "name": "MACD",
                "description": "Moving Average Convergence Divergence - 移動平均收斂發散指標",
                "parameters": [
                    {"name": "fast_period", "type": "integer", "default": 12, "range": [1, 50]},
                    {"name": "slow_period", "type": "integer", "default": 26, "range": [1, 100]},
                    {"name": "signal_period", "type": "integer", "default": 9, "range": [1, 50]}
                ]
            },
            {
                "name": "BollingerBands",
                "description": "Bollinger Bands - 布林帶",
                "parameters": [
                    {"name": "period", "type": "integer", "default": 20, "range": [5, 200]},
                    {"name": "std_dev_multiplier", "type": "float", "default": 2.0, "range": [0.5, 4.0]}
                ]
            }
        ]

        return response_formatter.format_success_response(
            indicators,
            meta={
                "total_indicators": len(indicators),
                "last_updated": datetime.now().isoformat()
            }
        )

    except Exception as e:
        logger.error(f"Error getting indicators: {e}")
        raise HTTPException(status_code=500, detail=response_formatter.format_error_response(
            "INDICATORS_ERROR", str(e)
        ))


@router.get("/test/{data_source}")
async def test_data_source(data_source: str, days: int = Query(30, ge=1, le=365)):
    """測試指定數據源的可用性"""
    try:
        # 驗證數據源
        try:
            source_type = DataSourceType(data_source)
        except ValueError:
            raise HTTPException(status_code=404, detail=response_formatter.format_error_response(
                "INVALID_DATA_SOURCE", f"Data source '{data_source}' not supported",
                available_sources=[s.value for s in DataSourceType],
                suggestions=["Use GET /api/technical/non-price/data-sources to see all available sources"]
            ))

        # 生成測試日期範圍
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        test_date_range = DateRange(start_date=start_date, end_date=end_date)

        # 嘗試獲取數據
        test_start = time.time()
        data = await engine.fetch_data(source_type, test_date_range)
        fetch_time = time.time() - test_start

        if data.empty:
            return response_formatter.format_success_response({
                "data_source": data_source,
                "status": "no_data",
                "message": f"No data available for {data_source} in the specified date range",
                "fetch_time_seconds": round(fetch_time, 3)
            })

        # 評估數據質量
        quality = engine.assess_data_quality(data)

        test_result = {
            "data_source": data_source,
            "status": "success",
            "data_points": len(data),
            "date_range": {
                "start": data.index.min().date().isoformat(),
                "end": data.index.max().date().isoformat()
            },
            "data_sample": {
                "latest_value": float(data.iloc[-1]) if len(data) > 0 else None,
                "min_value": float(data.min()),
                "max_value": float(data.max()),
                "mean_value": float(data.mean())
            },
            "fetch_time_seconds": round(fetch_time, 3),
            "quality_metrics": {
                "completeness": round(quality.completeness, 3),
                "timeliness": round(quality.timeliness, 3),
                "consistency": round(quality.consistency, 3),
                "quality_score": round(quality.quality_score, 3),
                "missing_values": quality.missing_values,
                "outliers": quality.outliers
            }
        }

        return response_formatter.format_success_response(test_result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing data source {data_source}: {e}")
        raise HTTPException(status_code=500, detail=response_formatter.format_error_response(
            "DATA_SOURCE_TEST_ERROR", str(e)
        ))


# 請求驗證函數
def _validate_rsi_request(request: RSIRequest):
    """驗證RSI請求參數"""
    if not isinstance(request.period, int) or request.period < 2 or request.period > 100:
        raise ValueError("RSI period must be between 2 and 100")

    if request.overbought_threshold <= request.oversold_threshold:
        raise ValueError("Overbought threshold must be greater than oversold threshold")

    if request.overbought_threshold < 50 or request.overbought_threshold > 100:
        raise ValueError("Overbought threshold must be between 50 and 100")

    if request.oversold_threshold < 0 or request.oversold_threshold > 50:
        raise ValueError("Oversold threshold must be between 0 and 50")


def _validate_macd_request(request: MACDRequest):
    """驗證MACD請求參數"""
    if request.fast_period >= request.slow_period:
        raise ValueError("Fast period must be less than slow period")

    if request.signal_period >= request.slow_period:
        raise ValueError("Signal period must be less than slow period")

    if not (1 <= request.fast_period <= 50):
        raise ValueError("Fast period must be between 1 and 50")

    if not (1 <= request.slow_period <= 100):
        raise ValueError("Slow period must be between 1 and 100")

    if not (1 <= request.signal_period <= 50):
        raise ValueError("Signal period must be between 1 and 50")


def _validate_bb_request(request: BollingerBandsRequest):
    """驗證Bollinger Bands請求參數"""
    if not (5 <= request.period <= 200):
        raise ValueError("Period must be between 5 and 200")

    if not (0.5 <= request.std_dev_multiplier <= 4.0):
        raise ValueError("Standard deviation multiplier must be between 0.5 and 4.0")


def _validate_batch_request(request: BatchRequest):
    """驗證批量請求參數"""
    if not request.indicators:
        raise ValueError("At least one indicator must be specified")

    if len(request.indicators) > 10:
        raise ValueError("Maximum 10 indicators allowed per batch request")

    # 驗證每個指標配置
    for i, indicator in enumerate(request.indicators):
        if indicator.type not in [IndicatorType.RSI, IndicatorType.MACD, IndicatorType.BOLLINGER_BANDS]:
            raise ValueError(f"Unsupported indicator type: {indicator.type} at index {i}")

        # 根據指標類型驗證參數
        if indicator.type == IndicatorType.RSI:
            period = indicator.parameters.get('period', 14)
            if not isinstance(period, int) or period < 2 or period > 100:
                raise ValueError(f"Invalid RSI period: {period} at index {i}")

        elif indicator.type == IndicatorType.MACD:
            fast = indicator.parameters.get('fast_period', 12)
            slow = indicator.parameters.get('slow_period', 26)
            signal = indicator.parameters.get('signal_period', 9)

            if fast >= slow:
                raise ValueError(f"MACD fast period must be less than slow period at index {i}")
            if signal >= slow:
                raise ValueError(f"MACD signal period must be less than slow period at index {i}")

        elif indicator.type == IndicatorType.BOLLINGER_BANDS:
            period = indicator.parameters.get('period', 20)
            std_dev = indicator.parameters.get('std_dev_multiplier', 2.0)

            if not isinstance(period, int) or period < 5 or period > 200:
                raise ValueError(f"Invalid Bollinger Bands period: {period} at index {i}")
            if not isinstance(std_dev, (int, float)) or std_dev < 0.5 or std_dev > 4.0:
                raise ValueError(f"Invalid standard deviation multiplier: {std_dev} at index {i}")


# 註：異常處理器需要在主應用中定義，而不是在路由器中
