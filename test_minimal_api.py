#!/usr/bin/env python3
"""
最简化的API测试
"""

import uvicorn
from fastapi import FastAPI
from datetime import datetime

# 创建最简单的FastAPI应用
app = FastAPI(title="Simple Test API")

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0-test"
    }

@app.get("/api/status")
async def status():
    return {
        "system_health": "operational",
        "last_update": datetime.now().isoformat()
    }

if __name__ == "__main__":
    print("Starting minimal API test...")
    print("Access URL: http://localhost:3003")

    uvicorn.run(app, host="0.0.0.0", port=3003)