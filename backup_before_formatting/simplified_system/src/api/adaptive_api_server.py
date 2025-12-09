"""
FastAPI服務器 - 適應性分析API
Production-Grade Adaptive Analysis API Server

提供RESTful API接口，支持適應性市場分析、市場狀況檢測等功能
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import asyncio
import logging
from datetime import datetime
import traceback

# 導入適應性分析API
from adaptive_analysis_api import (
    analyze_market_adaptive,
    get_market_regime,
    compare_methods,
    system_health,
    get_api_instance
)

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 創建FastAPI應用
app = FastAPI(
    title="Adaptive Analysis API",
    description="適應性市場分析系統 - 生產級別API服務",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS中間件配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生產環境中應該限制具體域名
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# 請求/響應模型
class AdaptiveAnalysisRequest(BaseModel):
    sources: Optional[List[str]] = Field(
        None,
        description="指定分析的數據源列表，為空則使用所有可用源",
        example=["hibor_rates", "monetary_base", "exchange_rates"]
    )
    use_cache: bool = Field(
        True,
        description="是否使用緩存結果"
    )

class AdaptiveAnalysisResponse(BaseModel):
    success: bool
    timestamp: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None

class MarketRegimeResponse(BaseModel):
    success: bool
    timestamp: str
    symbol: str
    market_state: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class ComparisonResponse(BaseModel):
    success: bool
    timestamp: str
    comparison_summary: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class SystemHealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    system_stats: Dict[str, Any]

# 啟動事件
@app.on_event("startup")
async def startup_event():
    """API服務啟動時初始化"""
    logger.info("🚀 Starting Adaptive Analysis API Server...")

    # 預熱API實例
    try:
        await get_api_instance()
        logger.info("✅ API instance initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize API instance: {e}")
        raise

# 關閉事件
@app.on_event("shutdown")
async def shutdown_event():
    """API服務關閉時清理"""
    logger.info("🔄 Shutting down Adaptive Analysis API Server...")

    try:
        api_instance = await get_api_instance()
        await api_instance.shutdown()
        logger.info("✅ API server shut down successfully")
    except Exception as e:
        logger.error(f"❌ Error during shutdown: {e}")

# API端點

@app.get("/", response_model=Dict[str, Any])
async def root():
    """根端點 - API信息"""
    return {
        "name": "Adaptive Analysis API",
        "version": "1.0.0",
        "description": "適應性市場分析系統API",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "adaptive_analysis": "/analyze/adaptive",
            "market_regime": "/analyze/regime/{symbol}",
            "compare_methods": "/analyze/compare",
            "health": "/health",
            "docs": "/docs"
        }
    }

@app.get("/health", response_model=SystemHealthResponse)
async def health_check():
    """系統健康檢查端點"""
    try:
        health_data = await system_health()
        return SystemHealthResponse(
            status=health_data.get("status", "unknown"),
            timestamp=health_data.get("timestamp", datetime.now().isoformat()),
            version=health_data.get("version", "1.0.0"),
            system_stats=health_data.get("system_stats", {})
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@app.post("/analyze/adaptive", response_model=AdaptiveAnalysisResponse)
async def adaptive_analysis_endpoint(
    request: AdaptiveAnalysisRequest,
    background_tasks: BackgroundTasks
):
    """
    適應性市場分析端點

    主要功能：
    - 市場狀況檢測
    - 動態參數調整
    - 適應性權重分配
    - 交易信號生成
    """
    start_time = datetime.now()

    try:
        # 執行適應性分析
        logger.info(f"🔍 Starting adaptive analysis for sources: {request.sources}")

        result = await analyze_market_adaptive(
            sources=request.sources,
            use_cache=request.use_cache
        )

        # 檢查是否有錯誤
        if result.get("error"):
            execution_time = (datetime.now() - start_time).total_seconds()
            return AdaptiveAnalysisResponse(
                success=False,
                timestamp=datetime.now().isoformat(),
                error=result.get("message", "Unknown error"),
                execution_time=execution_time
            )

        # 成功響應
        execution_time = (datetime.now() - start_time).total_seconds()

        # 添加後台任務記錄使用統計
        background_tasks.add_task(log_usage_stats, "adaptive_analysis", execution_time, True)

        return AdaptiveAnalysisResponse(
            success=True,
            timestamp=datetime.now().isoformat(),
            data=result,
            execution_time=execution_time
        )

    except Exception as e:
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.error(f"❌ Adaptive analysis failed: {e}")
        logger.error(traceback.format_exc())

        # 記錄錯誤統計
        background_tasks.add_task(log_usage_stats, "adaptive_analysis", execution_time, False)

        raise HTTPException(
            status_code=500,
            detail=f"Adaptive analysis failed: {str(e)}"
        )

@app.get("/analyze/regime/{symbol}", response_model=MarketRegimeResponse)
async def market_regime_endpoint(
    symbol: str = Path(..., description="分析標的符號", example="HKMA_COMPOSITE")
):
    """
    市場狀況分析端點

    功能：
    - 檢測當前市場狀況（牛市/熊市/震盪等）
    - 評估市場風險
    - 生成狀況相關建議
    """
    try:
        logger.info(f"📊 Analyzing market regime for: {symbol}")

        result = await get_market_regime(symbol)

        if result.get("error"):
            return MarketRegimeResponse(
                success=False,
                timestamp=datetime.now().isoformat(),
                symbol=symbol,
                error=result.get("message", "Unknown error")
            )

        return MarketRegimeResponse(
            success=True,
            timestamp=result.get("timestamp", datetime.now().isoformat()),
            symbol=result.get("symbol", symbol),
            market_state=result
        )

    except Exception as e:
        logger.error(f"❌ Market regime analysis failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Market regime analysis failed: {str(e)}"
        )

@app.get("/analyze/compare", response_model=ComparisonResponse)
async def comparison_endpoint(
    sources: Optional[str] = Query(
        None,
        description="逗號分隔的數據源列表，如：hibor_rates,monetary_base",
        example="hibor_rates,monetary_base,exchange_rates"
    )
):
    """
    方法比較端點

    功能：
    - 比較適應性系統 vs 傳統固定參數方法
    - 計算性能改進幅度
    - 提供詳細比較報告
    """
    try:
        # 解析sources參數
        source_list = None
        if sources:
            source_list = [s.strip() for s in sources.split(",") if s.strip()]

        logger.info(f"🔄 Comparing adaptive vs traditional methods for: {source_list or 'all sources'}")

        result = await compare_methods(source_list)

        if result.get("error"):
            return ComparisonResponse(
                success=False,
                timestamp=datetime.now().isoformat(),
                error=result.get("message", "Unknown error")
            )

        return ComparisonResponse(
            success=True,
            timestamp=result.get("timestamp", datetime.now().isoformat()),
            comparison_summary=result
        )

    except Exception as e:
        logger.error(f"❌ Comparison analysis failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Comparison analysis failed: {str(e)}"
        )

@app.post("/cache/clear")
async def clear_cache_endpoint():
    """清除緩存端點"""
    try:
        api_instance = await get_api_instance()
        api_instance.clear_cache()

        return {
            "success": True,
            "message": "Cache cleared successfully",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ Cache clear failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Cache clear failed: {str(e)}"
        )

@app.get("/stats")
async def get_usage_stats():
    """獲取使用統計端點"""
    try:
        health_data = await system_health()
        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "statistics": health_data.get("system_stats", {}),
            "api_info": {
                "version": "1.0.0",
                "endpoints": 5,
                "features": [
                    "adaptive_market_analysis",
                    "market_regime_detection",
                    "method_comparison",
                    "performance_monitoring",
                    "caching",
                    "error_handling"
                ]
            }
        }

    except Exception as e:
        logger.error(f"❌ Stats retrieval failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Stats retrieval failed: {str(e)}"
        )

async def log_usage_stats(endpoint: str, execution_time: float, success: bool):
    """記錄使用統計（後台任務）"""
    try:
        logger.info(f"📊 Usage: {endpoint} | Time: {execution_time:.3f}s | Success: {success}")
        # 在實際生產環境中，這裡可以記錄到數據庫或監控系統

    except Exception as e:
        logger.warning(f"Failed to log usage stats: {e}")

# 全局異常處理器
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局異常處理器"""
    logger.error(f"❌ Global exception: {exc}")
    logger.error(traceback.format_exc())

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "message": str(exc) if len(str(exc)) < 100 else "Error occurred",
            "timestamp": datetime.now().isoformat()
        }
    )

# 中間件：請求日誌
@app.middleware("http")
async def log_requests(request, call_next):
    """請求日誌中間件"""
    start_time = datetime.now()

    # 記錄請求
    logger.info(f"📥 {request.method} {request.url.path}")

    # 處理請求
    response = await call_next(request)

    # 計算執行時間
    process_time = (datetime.now() - start_time).total_seconds()

    # 記錄響應
    logger.info(f"📤 {request.method} {request.url.path} - "
               f"Status: {response.status_code} - Time: {process_time:.3f}s")

    # 添加響應頭
    response.headers["X-Process-Time"] = str(process_time)
    response.headers["X-API-Version"] = "1.0.0"

    return response

# 運行服務器（開發模式）
if __name__ == "__main__":
    import uvicorn

    print("🚀 Starting Adaptive Analysis API Server")
    print("=" * 50)
    print("📍 API Documentation: http://localhost:8000/docs")
    print("📍 Health Check: http://localhost:8000/health")
    print("📊 Adaptive Analysis: POST http://localhost:8000/analyze/adaptive")
    print("=" * 50)

    uvicorn.run(
        "adaptive_api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )