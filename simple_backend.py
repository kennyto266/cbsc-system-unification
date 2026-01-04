"""
Simplified backend for VectorBT real data backtesting
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import uvicorn

# Import vectorbt API router directly
from src.api.vectorbt_simple_api import router as vectorbt_router

# Create simple FastAPI app
app = FastAPI(
    title="CBSC VectorBT Backtest API",
    description="Real Market Data Backtesting",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3005",
        "http://localhost:8888",
        "http://192.168.1.5:3000",
        "http://192.168.1.5:3006",
        "http://127.0.0.1:3000",
        "null"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include VectorBT router
app.include_router(vectorbt_router, tags=["VectorBT"])

@app.get("/")
async def root():
    return {
        "message": "CBSC VectorBT Backtest API",
        "version": "2.0.0",
        "status": "running",
        "features": {
            "real_market_data": True,
            "data_source": "Yahoo Finance",
            "backtest_engine": "VectorBT 0.28.2"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "VectorBT Backtest API",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    print("=" * 60)
    print("Starting CBSC VectorBT Backtest API")
    print("Real Market Data Backtesting with Yahoo Finance")
    print("=" * 60)
    print("Server: http://0.0.0.0:8002")
    print("API Docs: http://0.0.0.0:8002/docs")
    print("=" * 60)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8003,
        log_level="info"
    )
