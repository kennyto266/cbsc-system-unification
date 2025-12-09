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
from datetime import datetime
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入端点
from api.auth_endpoints import router as auth_router
from api.user_endpoints import router as user_router

# 导入服务
from auth_simple import init_auth_service
from user_profile import init_user_profile_service

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
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # 允许前端域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件
if os.path.exists("uploads"):
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# 包含路由
app.include_router(auth_router)
app.include_router(user_router)

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

        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "checks": {
                "database": {"status": "healthy"},
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

        # 初始化认证服务
        init_auth_service()

        # 初始化用户资料服务
        init_user_profile_service()

        logger.info("✅ CBSC用户管理系统API启动成功")
        logger.info("📚 API文档: http://localhost:3004/docs")
        logger.info("🔍 健康检查: http://localhost:3004/health")

    except Exception as e:
        logger.error(f"❌ 应用启动失败: {e}")
        raise

# 应用关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行"""
    logger.info("正在关闭CBSC用户管理系统API...")

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