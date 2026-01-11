#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simplified API Server for Testing Issue #22
简化的API服务器 - Issue #22测试用途

只启动我们实现的新API架构进行测试
"""

import sys
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add project path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def create_test_app():
    """Create simplified test app with our new API architecture"""
    app = FastAPI(
        title="CBSC Strategy API - Test Server",
        description="Test server for the new unified strategy API architecture",
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

    # Add our new strategy router
    try:
        from api.strategies import router as strategies_router
        app.include_router(strategies_router, prefix="/api/v1", tags=["Strategy Management v1"])
        print("[OK] New strategy router loaded successfully")
    except Exception as e:
        print(f"[FAIL] Failed to load strategy router: {e}")
        # Still return app so we can test basic functionality

    @app.get("/")
    async def root():
        return {
            "message": "CBSC Strategy API - Test Server",
            "status": "running",
            "version": "1.0.0-test",
            "description": "Test server for Issue #22 - API Testing and Deployment"
        }

    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "timestamp": "2025-12-13T10:38:00Z",
            "service": "CBSC Strategy API Test"
        }

    @app.get("/api/version")
    async def api_version():
        return {
            "api_version": "v1.0",
            "implementation": "unified_strategy_architecture",
            "endpoints": "40",
            "issue": "#22 - API Testing and Deployment"
        }

    return app

if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("CBSC STRATEGY API - TEST SERVER")
    print("=" * 60)
    print("Starting test server for Issue #22...")
    print("Server: http://127.0.0.1:3004")
    print("Documentation: http://127.0.0.1:3004/docs")
    print("Health Check: http://127.0.0.1:3004/health")
    print("=" * 60)

    app = create_test_app()

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=3004,
        reload=True,
        log_level="info"
    )