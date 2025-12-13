#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CBSC Strategy API - External Access Version
Allows connections from any IP address (not just localhost)
"""

import sys
import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Create FastAPI app
app = FastAPI(
    title="CBSC Strategy API - External Access",
    description="API with external network access enabled",
    version="1.0.0-external"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Basic endpoints
@app.get("/")
async def root():
    return {
        "message": "CBSC Strategy API - External Access",
        "status": "running",
        "version": "1.0.0-external",
        "timestamp": datetime.now().isoformat(),
        "access": "external_network_enabled",
        "description": "API accessible from any IP address"
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "CBSC Strategy API External",
        "host_type": "0.0.0.0 (all interfaces)"
    }

@app.get("/api/health")
async def api_health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "CBSC Strategy API External",
        "endpoints": [
            "GET /",
            "GET /health", 
            "GET /api/health",
            "GET /docs",
            "GET /api/v1/strategies/",
            "GET /api/v1/strategies/templates/"
        ]
    }

# Try to load the strategy router
try:
    from api.strategies import router as strategies_router
    app.include_router(strategies_router, prefix="/api/v1", tags=["Strategy Management v1"])
    print("[OK] Strategy router loaded successfully")
except Exception as e:
    print(f"[WARN] Strategy router not available: {e}")

# Create demo endpoints if strategy router fails
@app.get("/api/v1/strategies/")
async def list_strategies():
    """Demo strategy list endpoint"""
    return {
        "strategies": [
            {
                "id": "demo-1",
                "name": "Demo Strategy 1",
                "type": "momentum",
                "status": "active",
                "created_at": datetime.now().isoformat()
            },
            {
                "id": "demo-2", 
                "name": "Demo Strategy 2",
                "type": "mean_reversion",
                "status": "inactive",
                "created_at": datetime.now().isoformat()
            }
        ],
        "total": 2,
        "message": "Demo data - Strategy router not loaded"
    }

@app.get("/api/v1/strategies/templates/")
async def list_templates():
    """Demo strategy templates endpoint"""
    return [
        {
            "id": "template-1",
            "name": "Momentum Strategy Template",
            "type": "momentum",
            "parameters": {
                "period": 14,
                "threshold": 0.02
            }
        },
        {
            "id": "template-2",
            "name": "Mean Reversion Template", 
            "type": "mean_reversion",
            "parameters": {
                "lookback": 20,
                "std_dev": 2.0
            }
        }
    ]

if __name__ == "__main__":
    print("=" * 80)
    print("CBSC Strategy API - External Access Server")
    print("=" * 80)
    print("Starting server with external network access...")
    print("This server will accept connections from any IP address")
    print("Accessible URLs:")
    print("  - Local: http://localhost:3004")
    print("  - Network: http://0.0.0.0:3004")
    print("  - API Docs: http://localhost:3004/docs")
    print("  - Health Check: http://localhost:3004/health")
    print("=" * 80)
    
    # Run on all interfaces (0.0.0.0) to allow external access
    uvicorn.run(
        app,
        host="0.0.0.0",  # Bind to all interfaces
        port=3004,
        reload=False,
        access_log=True
    )