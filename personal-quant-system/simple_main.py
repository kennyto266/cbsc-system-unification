"""
个人量化交易系统 - 简化版主应用
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# 创建FastAPI应用
app = FastAPI(
    title="个人量化交易系统",
    description="为个人投资者提供专业级的港股量化分析工具",
    version="1.0.0"
)

# CORS设置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 健康检查端点
@app.get("/")
async def root():
    """根路径"""
    return {"message": "个人量化交易系统运行正常", "status": "healthy"}

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "message": "个人量化交易系统运行正常"}

# 测试API端点
@app.get("/api/test")
async def test_api():
    """测试API"""
    return {
        "success": True,
        "message": "API测试成功",
        "data": {
            "system": "个人量化交易系统",
            "version": "1.0.0",
            "status": "running"
        }
    }

# 模拟股票数据API
@app.get("/api/stocks")
async def get_stocks():
    """获取股票列表"""
    stocks = [
        {"symbol": "0700.HK", "name": "腾讯控股", "sector": "科技", "market_cap": 3000000000000},
        {"symbol": "2800.HK", "name": "盈富基金", "sector": "金融", "market_cap": 100000000000},
        {"symbol": "1299.HK", "name": "友邦保险", "sector": "保险", "market_cap": 800000000000},
        {"symbol": "0941.HK", "name": "中国移动", "sector": "电信", "market_cap": 1200000000000},
        {"symbol": "0388.HK", "name": "香港交易所", "sector": "金融", "market_cap": 400000000000}
    ]
    
    return {
        "success": True,
        "data": stocks,
        "message": "股票列表获取成功"
    }

if __name__ == "__main__":
    print("🚀 启动个人量化交易系统...")
    print("📊 访问地址: http://localhost:8000")
    print("📚 API文档: http://localhost:8000/docs")
    print("🔍 健康检查: http://localhost:8000/health")
    print("=" * 50)
    
    uvicorn.run(
        "simple_main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
