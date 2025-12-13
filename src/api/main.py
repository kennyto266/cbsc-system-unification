"""
用户管理系统API主程序
User Management System API Main Application
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import logging
import os
import asyncio
from datetime import datetime
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入端点
from api.auth_endpoints import router as auth_router
from api.user_endpoints import router as user_router
from api.personal_strategy_endpoints import router as personal_strategy_router
from api.cbsc_strategy_api import router as cbsc_strategy_router
from api.unified_strategy_endpoints import router as unified_strategy_router
from api.websocket_server import websocket_router
from api.non_price_endpoints import router as non_price_router

# 导入新的统一策略架构 (Issue #20/21 实现)
from api.strategies import router as new_strategies_router

# 导入服务
from auth_simple import init_auth_service
from user_profile import init_user_profile_service
from api.cache_service import cache_service
from api.middleware import setup_middleware
from api.websocket_server import get_websocket_manager
from api.unified_strategy_service import init_unified_strategy_manager
from api.strategy_execution_engine import initialize_execution_engine, shutdown_execution_engine

# 导入监控模块
try:
    from monitoring.metrics import MetricsMiddleware, initialize_metrics, metrics_endpoint
    MONITORING_ENABLED = True
except ImportError:
    MONITORING_ENABLED = False
    logger.warning("Monitoring module not available, metrics disabled")

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="CBSC 用户管理系统 API",
    description="为个人独立使用优化的用户管理API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8888",  # 允许Dashboard连接
        "http://127.0.0.1:8888"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加监控中间件
if MONITORING_ENABLED:
    app.add_middleware(MetricsMiddleware)
    logger.info("Prometheus metrics middleware enabled")

# 挂载静态文件
if os.path.exists("uploads"):
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# 包含路由
app.include_router(auth_router)
app.include_router(user_router)

# 新的统一策略架构路由 (v1.0) - Issue #20/21 实现
app.include_router(new_strategies_router, prefix="/api/v1", tags=["策略管理v1"])

# 保留旧路由用于向后兼容 (v0.x) - 逐步废弃
app.include_router(personal_strategy_router, tags=["策略管理v0-个人"])
app.include_router(cbsc_strategy_router, tags=["策略管理v0-CBSC"])
app.include_router(unified_strategy_router, tags=["策略管理v0-统一"])
app.include_router(websocket_router)
app.include_router(non_price_router)

# 全局异常处理器
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理"""
    logger.error(f"全局异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "服务器内部错误"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP异常处理"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": "HTTP_ERROR",
                "message": exc.detail
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    )

# 根路径
@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "CBSC 用户管理系统 API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat()
    }

# 健康检查
@app.get("/health")
async def health_check():
    """健康检查端点"""
    try:
        # 检查数据库连接
        from auth_simple import auth_service
        db = next(auth_service.get_db())
        db.execute("SELECT 1")
        db.close()

        # 检查缓存服务
        cache_status = await cache_service.get_cache_info()

        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "checks": {
                "database": {"status": "healthy"},
                "cache": cache_status,
                "api": {"status": "healthy"}
            }
        }
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
        )

# Prometheus指标端点
if MONITORING_ENABLED:
    @app.get("/metrics")
    async def metrics():
        """Prometheus metrics endpoint"""
        return await metrics_endpoint()

# 准备性检查
@app.get("/ready")
async def readiness_check():
    """就绪检查"""
    try:
        from auth_simple import auth_service
        # 检查认证服务是否正常
        return {"status": "ready"}
    except Exception as e:
        raise HTTPException(status_code=503, detail="服务未就绪")

# 存活检查
@app.get("/live")
async def liveness_check():
    """存活检查"""
    return {"status": "alive"}

# 应用启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    logger.info("正在启动CBSC用户管理系统API...")

    try:
        # 创建必要的目录
        os.makedirs("logs", exist_ok=True)
        os.makedirs("uploads", exist_ok=True)

        # 初始化缓存服务
        cache_success = await cache_service.initialize()
        if cache_success:
            logger.info("✅ 缓存服务初始化成功")
        else:
            logger.warning("⚠️ 缓存服务初始化失败，将继续运行但性能可能受影响")

        # 初始化认证服务
        init_auth_service()

        # 初始化用户资料服务
        init_user_profile_service()

        # 初始化统一策略管理器
        init_unified_strategy_manager()
        logger.info("✅ 统一策略管理器初始化成功")

        # 初始化策略执行引擎
        await initialize_execution_engine()
        logger.info("✅ 策略执行引擎初始化成功")

        # 设置中间件
        setup_middleware(app)

        # 启动WebSocket数据模拟
        ws_manager = get_websocket_manager()
        asyncio.create_task(ws_manager.start_data_simulation())
        logger.info("✅ WebSocket实时数据模拟已启动")

        logger.info("✅ CBSC用户管理系统API启动成功")
        logger.info("📚 API文档: http://localhost:3004/docs")
        logger.info("🔍 健康检查: http://localhost:3004/health")

        # 新的统一架构API (Issue #20/21 实现)
        logger.info("🚀 新统一策略管理API v1.0: http://localhost:3004/api/v1/strategies")
        logger.info("📊 个人策略API v1.0: http://localhost:3004/api/v1/strategies/personal")
        logger.info("⚡ 策略执行API v1.0: http://localhost:3004/api/v1/strategies/execution")
        logger.info("🔌 WebSocket v1.0: ws://localhost:3004/api/v1/ws/strategies")

        # 旧版本API (向后兼容，逐步废弃)
        logger.info("📊 个人策略管理API v0.x: http://localhost:3004/api/personal-strategies")
        logger.info("🧠 CBSC策略管理API v0.x: http://localhost:3004/api/strategies")
        logger.info("🔌 WebSocket端点 v0.x: ws://localhost:3004/ws/strategies")
        logger.info("🏛️ 非价格策略API: http://localhost:3004/api/non-price")
        logger.info("📈 HKMA宏观数据: http://localhost:3004/api/non-price/hkma")
        logger.info("💭 情绪分析API: http://localhost:3004/api/non-price/sentiment")

    except Exception as e:
        logger.error(f"❌ 应用启动失败: {e}")
        raise

# 应用关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行"""
    logger.info("正在关闭CBSC用户管理系统API...")

    try:
        # 停止WebSocket数据模拟
        ws_manager = get_websocket_manager()
        ws_manager.stop_data_simulation()
        logger.info("✅ WebSocket数据模拟已停止")

        # 关闭策略执行引擎
        await shutdown_execution_engine()
        logger.info("✅ 策略执行引擎已关闭")

        # 关闭缓存服务
        await cache_service.close()
        logger.info("✅ 缓存服务已关闭")

    except Exception as e:
        logger.error(f"❌ 关闭服务失败: {e}")

# 中间件：请求日志
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录请求日志"""
    start_time = datetime.utcnow()

    # 记录请求信息
    logger.info(f"请求: {request.method} {request.url.path}")

    # 处理请求
    response = await call_next(request)

    # 计算处理时间
    process_time = (datetime.utcnow() - start_time).total_seconds()

    # 记录响应信息
    logger.info(f"响应: {response.status_code} - {process_time:.3f}s")

    # 添加处理时间到响应头
    response.headers["X-Process-Time"] = str(process_time)

    return response

# 开发服务器启动
if __name__ == "__main__":
    try:
        logger.info("🚀 启动开发服务器...")

        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=3004,
            reload=True,
            log_level="info",
            access_log=True
        )

    except KeyboardInterrupt:
        logger.info("👋 收到中断信号，正在关闭服务器...")
    except Exception as e:
        logger.error(f"❌ 服务器启动失败: {e}")
        sys.exit(1)