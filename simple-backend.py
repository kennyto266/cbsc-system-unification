from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import uvicorn
from typing import Dict, List, Any

# Create FastAPI app
app = FastAPI(
    title="CBSC Strategy Management API",
    description="CBSC量化交易策略管理系統API",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock strategies data matching frontend expectations
MOCK_STRATEGIES = [
    {
        "id": "ma_crossover_001",
        "name": "移動平均線交叉策略",
        "type": "技術分析",
        "status": "活躍",
        "description": "基於移動平均線交叉的量化交易策略",
        "created_at": "2024-01-15T10:00:00Z"
    },
    {
        "id": "rsi_mean_002",
        "name": "RSI均值回歸策略",
        "type": "技術分析",
        "status": "測試中",
        "description": "基於RSI的超買超賣信號進行交易",
        "created_at": "2024-01-20T14:30:00Z"
    },
    {
        "id": "hybrid_003",
        "name": "混合經濟數據策略",
        "type": "基本面",
        "status": "活躍",
        "description": "結合經濟數據和技術指標的複合策略",
        "created_at": "2024-01-25T09:15:00Z"
    }
]

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "CBSC Strategy Management System API",
        "version": "1.0.0",
        "status": "running"
    }

# Health check endpoint - match frontend expectation
@app.get("/api/health")
async def health():
    return {
        "status": "健康",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "message": "系統運行正常"
    }

# Strategies endpoint - matching frontend expectation
@app.get("/api/v1/strategies")
async def get_strategies():
    return {
        "success": True,
        "data": MOCK_STRATEGIES,
        "timestamp": datetime.now().isoformat()
    }

# Dashboard overview endpoint
@app.get("/api/v1/dashboard/overview")
async def get_dashboard_overview():
    return {
        "success": True,
        "data": {
            "performance": {
                "today_return": 0.0234,
                "weekly_return": 0.0567,
                "monthly_return": 0.1234,
                "total_return": 0.4567
            },
            "system_health": {
                "api_status": "正常",
                "database_status": "連接正常",
                "cache_status": "運行中",
                "last_update": datetime.now().isoformat()
            },
            "statistics": {
                "total_trades": 1234,
                "win_rate": 0.654,
                "avg_holding_time": "2.5小時"
            }
        },
        "timestamp": datetime.now().isoformat()
    }

# Economic data endpoint
@app.get("/api/v1/economic-data")
async def get_economic_data():
    return {
        "success": True,
        "data": {
            "GDP": {
                "current": 2.3,
                "change": 0.1,
                "historical": [
                    {"date": "2024-01", "value": 2.1},
                    {"date": "2024-02", "value": 2.2},
                    {"date": "2024-03", "value": 2.3}
                ]
            },
            "CPI": {
                "current": 2.7,
                "change": -0.2,
                "historical": [
                    {"date": "2024-01", "value": 2.9},
                    {"date": "2024-02", "value": 2.8},
                    {"date": "2024-03", "value": 2.7}
                ]
            },
            "PMI": {
                "current": 52.1,
                "change": 1.2,
                "historical": [
                    {"date": "2024-01", "value": 50.9},
                    {"date": "2024-02", "value": 51.5},
                    {"date": "2024-03", "value": 52.1}
                ]
            },
            "Unemployment": {
                "current": 3.8,
                "change": -0.1,
                "historical": [
                    {"date": "2024-01", "value": 3.9},
                    {"date": "2024-02", "value": 3.85},
                    {"date": "2024-03", "value": 3.8}
                ]
            },
            "Trade_Balance": {
                "current": -45.2,
                "change": 2.1,
                "historical": [
                    {"date": "2024-01", "value": -47.3},
                    {"date": "2024-02", "value": -46.8},
                    {"date": "2024-03", "value": -45.2}
                ]
            }
        },
        "timestamp": datetime.now().isoformat()
    }

# Strategy detail endpoint
@app.get("/api/v1/strategies/{strategy_id}")
async def get_strategy(strategy_id: str):
    strategy = next((s for s in MOCK_STRATEGIES if s["id"] == strategy_id), None)
    if strategy:
        return {
            "success": True,
            "data": strategy,
            "timestamp": datetime.now().isoformat()
        }
    else:
        return {
            "success": False,
            "error": "策略未找到",
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    print("啟動CBSC簡化版後端服務...")
    print("API文檔: http://localhost:8001/docs")
    print("健康檢查: http://localhost:8001/api/health")
    uvicorn.run(app, host="0.0.0.0", port=8001)