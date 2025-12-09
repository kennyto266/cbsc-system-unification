#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Emergency Server Fix - Working FastAPI Server
Use this as a temporary working server while fixing main applications
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="CBSC Emergency Server",
    description="Working FastAPI server for testing",
    version="1.0.0"
)

# Add CORS with safe settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000", "http://localhost:8001",
                   "http://127.0.0.1:3000", "http://127.0.0.1:8000", "http://127.0.0.1:8001"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Simple data models
class ParameterUpdate(BaseModel):
    parameter_name: str = Field(..., min_length=1, max_length=50)
    value: float = Field(..., ge=0, le=100)
    user_id: str = Field(..., min_length=1, max_length=50)

# Safe parameter storage
current_parameters = {
    "rsi_period": {"value": 14.0, "min": 2.0, "max": 50.0, "unit": "periods"},
    "macd_fast": {"value": 12.0, "min": 5.0, "max": 20.0, "unit": "periods"},
    "macd_slow": {"value": 26.0, "min": 20.0, "max": 50.0, "unit": "periods"},
    "bollinger_period": {"value": 20.0, "min": 10.0, "max": 50.0, "unit": "periods"},
    "sentiment_threshold": {"value": 0.6, "min": 0.0, "max": 1.0, "unit": "ratio"},
    "risk_tolerance": {"value": 50.0, "min": 0.0, "max": 100.0, "unit": "percent"},
    "allocation_percentage": {"value": 60.0, "min": 10.0, "max": 100.0, "unit": "percent"}
}

parameter_history = []

# Error handling middleware
@app.middleware("http")
async def error_handling_middleware(request, call_next):
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        logger.error(f"Unhandled error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "type": "server_error",
                "timestamp": datetime.now().isoformat()
            }
        )

# API Endpoints
@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    """Simple dashboard"""
    return """
<!DOCTYPE html>
<html>
<head>
    <title>CBSC Emergency Server</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .status { padding: 20px; background: #e8f5e8; border-radius: 5px; margin: 20px 0; }
        .endpoint { margin: 10px 0; padding: 10px; background: #f8f9fa; border-left: 4px solid #007bff; }
        h1 { color: #333; }
        .test-btn { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin: 5px; }
        .test-btn:hover { background: #0056b3; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚨 CBSC Emergency Server</h1>
        <div class="status">
            <h3>✅ Server Status: RUNNING</h3>
            <p>This is a working FastAPI server for testing while fixing the main application.</p>
        </div>

        <h2>📡 Available Endpoints</h2>
        <div class="endpoint">GET /api/health - Health check</div>
        <div class="endpoint">GET /api/parameters/current - Current parameters</div>
        <div class="endpoint">POST /api/parameters/update - Update parameter</div>
        <div class="endpoint">GET /api/system/stats - System statistics</div>
        <div class="endpoint">GET /docs - API documentation</div>

        <h2>🧪 Quick Tests</h2>
        <button class="test-btn" onclick="testHealth()">Test Health</button>
        <button class="test-btn" onclick="testParameters()">Test Parameters</button>
        <button class="test-btn" onclick="testUpdate()">Test Update</button>

        <div id="results" style="margin-top: 20px; padding: 20px; background: #f8f9fa; border-radius: 5px; display: none;">
            <h3>Test Results:</h3>
            <pre id="result-content"></pre>
        </div>
    </div>

    <script>
        function showResults(content) {
            document.getElementById('results').style.display = 'block';
            document.getElementById('result-content').textContent = content;
        }

        async function testHealth() {
            try {
                const response = await fetch('/api/health');
                const data = await response.json();
                showResults('Health Check - Status: ' + response.status + '\\n' + JSON.stringify(data, null, 2));
            } catch (error) {
                showResults('Health Check Error: ' + error.message);
            }
        }

        async function testParameters() {
            try {
                const response = await fetch('/api/parameters/current');
                const data = await response.json();
                showResults('Parameters Check - Status: ' + response.status + '\\n' + JSON.stringify(data, null, 2));
            } catch (error) {
                showResults('Parameters Check Error: ' + error.message);
            }
        }

        async function testUpdate() {
            try {
                const response = await fetch('/api/parameters/update', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        parameter_name: 'rsi_period',
                        value: 15,
                        user_id: 'test_user'
                    })
                });
                const data = await response.json();
                showResults('Update Test - Status: ' + response.status + '\\n' + JSON.stringify(data, null, 2));
            } catch (error) {
                showResults('Update Test Error: ' + error.message);
            }
        }
    </script>
</body>
</html>
"""

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "server": "CBSC Emergency Server",
        "version": "1.0.0",
        "features": {
            "cors_enabled": True,
            "error_handling": True,
            "parameter_management": True,
            "security_validation": "basic"
        }
    }

@app.get("/api/parameters/current")
async def get_current_parameters():
    """Get current parameters"""
    return {
        "parameters": current_parameters,
        "timestamp": datetime.now().isoformat(),
        "count": len(current_parameters)
    }

@app.post("/api/parameters/update")
async def update_parameter(parameter_update: ParameterUpdate):
    """Update parameter with basic validation"""
    try:
        # Validate parameter exists
        if parameter_update.parameter_name not in current_parameters:
            raise HTTPException(status_code=400, detail="Invalid parameter name")

        # Check value range
        param_config = current_parameters[parameter_update.parameter_name]
        if not (param_config["min"] <= parameter_update.value <= param_config["max"]):
            raise HTTPException(
                status_code=400,
                detail=f"Value {parameter_update.value} out of range [{param_config['min']}, {param_config['max']}]"
            )

        # Update parameter
        old_value = param_config["value"]
        param_config["value"] = parameter_update.value

        # Record update
        update_record = {
            "parameter_name": parameter_update.parameter_name,
            "old_value": old_value,
            "new_value": parameter_update.value,
            "timestamp": datetime.now().isoformat(),
            "user_id": parameter_update.user_id
        }
        parameter_history.append(update_record)

        logger.info(f"Parameter updated: {parameter_update.parameter_name} = {parameter_update.value}")

        return {
            "status": "success",
            "message": "Parameter updated successfully",
            "parameter": parameter_update.parameter_name,
            "old_value": old_value,
            "new_value": parameter_update.value,
            "timestamp": update_record["timestamp"]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating parameter: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/system/stats")
async def get_system_stats():
    """Get system statistics"""
    return {
        "server": {
            "uptime_seconds": time.time(),
            "timestamp": datetime.now().isoformat()
        },
        "parameters": {
            "total_count": len(current_parameters),
            "update_history_count": len(parameter_history)
        },
        "status": "operational"
    }

@app.get("/test")
async def test_endpoint():
    """Simple test endpoint"""
    return {"message": "Test successful", "timestamp": datetime.now().isoformat()}

def main():
    """Run the emergency server"""
    print("🚨 CBSC Emergency Server Starting...")
    print("=" * 50)
    print("This is a minimal working FastAPI server")
    print("Use it for testing while fixing the main application")
    print("=" * 50)
    print("📡 Server will be available at: http://localhost:8001")
    print("📚 API docs at: http://localhost:8001/docs")
    print("🏠 Dashboard at: http://localhost:8001/")
    print("🧪 Quick test: http://localhost:8001/test")
    print("=" * 50)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )

if __name__ == "__main__":
    main()