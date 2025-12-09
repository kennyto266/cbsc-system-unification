"""
技術分析API主應用程序
Technical Analysis API Main Application
"""

import logging
import time
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .endpoints import router
from .engine import NonPriceDataProcessor, ResponseFormatter, TechnicalIndicatorEngine

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 全局變量
engine_instance = None
data_processor_instance = None
response_formatter_instance = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用程序生命週期管理"""
    global engine_instance, data_processor_instance, response_formatter_instance

    # 啟動時初始化
    logger.info("Starting Technical Analysis API...")
    try:
        engine_instance = TechnicalIndicatorEngine()
        data_processor_instance = NonPriceDataProcessor()
        response_formatter_instance = ResponseFormatter()
        logger.info("Technical Analysis API components initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize API components: {e}")
        raise

    yield

    # 關閉時清理
    logger.info("Shutting down Technical Analysis API...")
    # 清理緩存等資源
    if engine_instance:
        engine_instance.cache.clear()
    logger.info("Technical Analysis API shutdown complete")


# 創建FastAPI應用
app = FastAPI(
    title="非價格數據技術分析API",
    title_en="Non-Price Data Technical Analysis API",
    description="將香港政府非價格經濟數據轉換為技術分析指標的API服務",
    description_en="API service for converting Hong Kong government non-price economic data to technical analysis indicators",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# 添加CORS中間件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生產環境中應該限制具體域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 添加技術分析路由
app.include_router(router)


@app.get("/", tags=["Root"])
async def root():
    """API根端點"""
    return {
        "message": "非價格數據技術分析API",
        "message_en": "Non-Price Data Technical Analysis API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "technical_analysis": "/api/technical/non-price",
            "documentation": "/docs",
            "health_check": "/api/technical/non-price/health",
            "data_sources": "/api/technical/non-price/data-sources"
        },
        "supported_indicators": ["RSI", "MACD", "BollingerBands"],
        "supported_data_sources": [
            "hibor_overnight",
            "monetary_base",
            "gdp_growth",
            "unemployment_rate"
        ]
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """基本健康檢查端點"""
    try:
        global engine_instance
        if not engine_instance:
            raise HTTPException(status_code=503, detail="Service not initialized")

        return {
            "status": "healthy",
            "service": "technical-analysis-api",
            "version": "1.0.0",
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service unavailable: {e}")


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """HTTP異常處理器"""
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """通用異常處理器"""
    logger.error(f"Unhandled exception: {type(exc).__name__}: {exc}")

    formatter = ResponseFormatter()
    return JSONResponse(
        status_code=500,
        content=formatter.format_error_response(
            "INTERNAL_SERVER_ERROR",
            "An unexpected error occurred",
            suggestions=["Please try again later", "Contact support if the problem persists"]
        )
    )


# 啟動函數
def run_server(host: str = "0.0.0.0", port: int = 8003, debug: bool = False):
    """運行技術分析API服務器"""
    logger.info(f"Starting Technical Analysis API server on {host}:{port}")

    config = uvicorn.Config(
        app=app,
        host=host,
        port=port,
        log_level="info" if not debug else "debug",
        reload=debug,
        access_log=True
    )

    server = uvicorn.Server(config)
    server.run()


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="非價格數據技術分析API服務器")
    parser.add_argument("--host", default="0.0.0.0", help="服務器主機地址")
    parser.add_argument("--port", type=int, default=8003, help="服務器端口")
    parser.add_argument("--debug", action="store_true", help="啟用調試模式")

    args = parser.parse_args()

    try:
        run_server(host=args.host, port=args.port, debug=args.debug)
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server failed to start: {e}")
        sys.exit(1)
