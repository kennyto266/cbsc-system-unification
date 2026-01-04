
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
import json
import uvicorn
from datetime import datetime

app = FastAPI(title="CBSC量化策略管理系統", version="2.0.0")

# 添加CORS中間件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 數據模型
class StrategyCreate(BaseModel):
    name: str
    type: str
    description: Optional[str] = None
    parameters: dict = {}

class StrategyResponse(BaseModel):
    id: int
    name: str
    type: str
    description: str
    parameters: dict
    created_at: str
    updated_at: str
    status: str
    performance_metrics: dict

# 數據庫連接
def get_db():
    conn = sqlite3.connect("data/cbsc.db")
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/")
async def root():
    return HTMLResponse("""
    <html>
        <head>
            <title>CBSC量化策略管理系統</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
                .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                h1 { color: #333; text-align: center; }
                .status { background: #e8f5e8; padding: 15px; border-radius: 5px; margin: 20px 0; }
                .api-list { list-style: none; padding: 0; }
                .api-list li { margin: 10px 0; padding: 10px; background: #f8f9fa; border-radius: 5px; }
                .endpoint { font-weight: bold; color: #0066cc; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>CBSC量化策略管理系統</h1>
                <div class="status">
                    <h3>系統狀態: 運行中</h3>
                    <p>版本: 2.0.0 Full | 時間: {timestamp}</p>
                </div>
                <h2>API端點</h2>
                <ul class="api-list">
                    <li><span class="endpoint">GET /api/v1/strategies</span> - 策略列表</li>
                    <li><span class="endpoint">POST /api/v1/strategies</span> - 創建策略</li>
                    <li><span class="endpoint">GET /api/v2/strategies</span> - V2策略列表</li>
                    <li><span class="endpoint">GET /health</span> - 健康檢查</li>
                    <li><span class="endpoint">GET /docs</span> - API文檔</li>
                </ul>
            </div>
        </body>
    </html>
    """.format(timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0-full",
        "services": {
            "api": "running",
            "database": "connected",
            "websocket": "disabled"
        }
    }

@app.get("/api/v1/strategies", response_model=List[StrategyResponse])
async def list_strategies_v1():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM strategies WHERE status = 'active'")
    strategies = cursor.fetchall()
    conn.close()

    return [
        StrategyResponse(
            id=row["id"],
            name=row["name"],
            type=row["type"],
            description=row["description"],
            parameters=json.loads(row["parameters"] or "{}"),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            status=row["status"],
            performance_metrics=json.loads(row["performance_metrics"] or "{}")
        )
        for row in strategies
    ]

@app.post("/api/v1/strategies", response_model=StrategyResponse)
async def create_strategy(strategy: StrategyCreate):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO strategies (name, type, description, parameters, created_at, updated_at, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (strategy.name, strategy.type, strategy.description,
         json.dumps(strategy.parameters), datetime.now(), datetime.now(), "active")
    )

    strategy_id = cursor.lastrowid
    conn.commit()

    # 返回創建的策略
    cursor.execute("SELECT * FROM strategies WHERE id = ?", (strategy_id,))
    row = cursor.fetchone()
    conn.close()

    return StrategyResponse(
        id=row["id"],
        name=row["name"],
        type=row["type"],
        description=row["description"],
        parameters=json.loads(row["parameters"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        status=row["status"],
        performance_metrics=json.loads(row["performance_metrics"] or "{}")
    )

@app.get("/api/v2/strategies")
async def list_strategies_v2():
    # V2 API - 增強功能
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM strategies ORDER BY created_at DESC")
    strategies = cursor.fetchall()
    conn.close()

    return {
        "success": True,
        "data": [
            {
                "id": row["id"],
                "name": row["name"],
                "type": row["type"],
                "status": row["status"],
                "created_at": row["created_at"],
                "performance": json.loads(row["performance_metrics"] or "{}")
            }
            for row in strategies
        ],
        "total": len(strategies),
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3004)
