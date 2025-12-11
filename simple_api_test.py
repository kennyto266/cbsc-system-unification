#!/usr/bin/env python3
"""
Simple API Server Test
简单的API服务器测试脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from datetime import datetime

app = FastAPI(
    title="Simple Test API",
    description="Simple test API for functionality verification",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "Simple Test API is running",
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "checks": {
            "database": {"status": "healthy"},
            "api": {"status": "healthy"}
        }
    }

@app.get("/api/personal-strategies/dashboard")
async def dashboard_test():
    return {
        "total_strategies": 5,
        "active_strategies": 3,
        "total_return": 0.15,
        "daily_pnl": 0.025,
        "best_performing": {
            "strategy_id": "test_strategy_1",
            "name": "Test Strategy",
            "current_return": 0.20
        },
        "recent_signals": [],
        "market_overview": {
            "market_status": "open",
            "index_change": 0.025
        }
    }

if __name__ == "__main__":
    print("Starting Simple Test API Server...")
    print("Access: http://localhost:3004")
    print("Docs: http://localhost:3004/docs")

    uvicorn.run(
        "simple_api_test:app",
        host="0.0.0.0",
        port=3004,
        reload=False,
        log_level="info"
    )