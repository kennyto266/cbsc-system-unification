#!/usr/bin/env python3
"""
簡單的測試服務器
Simple Test Server
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(
    title="CBSC Strategy Management System",
    description="量化交易策略管理系統 API",
    version="2.0.0"
)

# 添加 CORS 中間件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "CBSC Strategy Management System API", "version": "2.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "CBSC API"}

@app.get("/api/v2/strategies")
async def get_strategies():
    return {
        "strategies": [
            {"id": 1, "name": "MA Crossover", "status": "active"},
            {"id": 2, "name": "RSI Strategy", "status": "inactive"}
        ]
    }

if __name__ == "__main__":
    print("Starting CBSC Simple Server on http://localhost:3004")
    uvicorn.run(app, host="0.0.0.0", port=3004)