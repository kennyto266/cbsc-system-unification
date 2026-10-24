"""
个人量化交易系统 - 主应用入口
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os

# 导入API模块
from backend.api import data, analysis, backtest, portfolio

# 创建FastAPI应用
app = FastAPI(
    title="个人量化交易系统",
    description="为个人投资者提供专业级的港股量化分析工具",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS设置 - 允许前端访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境需要限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件服务
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# 注册API路由
app.include_router(data.router, prefix="/api/data", tags=["数据"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["分析"])
app.include_router(backtest.router, prefix="/api/backtest", tags=["回测"])
app.include_router(portfolio.router, prefix="/api/portfolio", tags=["投资组合"])

# 根路径 - 返回前端页面
@app.get("/")
async def read_index():
    """返回主页面"""
    return FileResponse("frontend/index.html")

# 健康检查端点
@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "message": "个人量化交易系统运行正常"}

# API信息端点
@app.get("/api/info")
async def api_info():
    """API信息"""
    return {
        "name": "个人量化交易系统API",
        "version": "1.0.0",
        "description": "为个人投资者提供港股量化分析服务",
        "endpoints": {
            "data": "/api/data/*",
            "analysis": "/api/analysis/*",
            "backtest": "/api/backtest/*",
            "portfolio": "/api/portfolio/*"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # 开发模式，代码变更自动重载
        log_level="info"
    )
