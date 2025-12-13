#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CBSC Strategy API with Business Logic Implementation
带有业务逻辑实现的CBSC策略API

演示端点的具体业务逻辑实现
Demonstrates concrete business logic implementation for endpoints
"""

import sys
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid

# Add project path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import demo service
from demo_strategy_service import DemoStrategyService

# Pydantic Models
class StrategyCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    type: Optional[str] = "technical"
    parameters: Optional[Dict] = {}
    risk_level: Optional[str] = "medium"

class StrategyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    parameters: Optional[Dict] = None
    risk_level: Optional[str] = None
    status: Optional[str] = None

class BatchOperation(BaseModel):
    strategy_ids: List[str]
    operation: str  # activate, deactivate, delete
    parameters: Optional[Dict] = {}

# Mock User for demo
class MockUser:
    def __init__(self, id: int = 1, username: str = "demo_user"):
        self.id = id
        self.username = username
        self.is_active = True

def get_current_user():
    """Mock current user for demo"""
    return MockUser()

def create_app_with_logic():
    """Create FastAPI app with business logic"""
    app = FastAPI(
        title="CBSC Strategy API - With Business Logic",
        description="CBSC Strategy API with concrete business logic implementation",
        version="1.0.0-demo"
    )

    # Add CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Initialize demo service
    strategy_service = DemoStrategyService()

    @app.get("/")
    async def root():
        return {
            "message": "CBSC Strategy API with Business Logic",
            "status": "running",
            "version": "1.0.0-demo",
            "description": "API with concrete business logic implementation"
        }

    @app.get("/health")
    async def health():
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "CBSC Strategy API with Logic"
        }

    # Strategy Management Endpoints
    @app.get("/api/v1/strategies/")
    async def list_strategies(
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        strategy_type: Optional[str] = Query(None),
        status: Optional[str] = Query(None),
        current_user: MockUser = Depends(get_current_user)
    ):
        """Get strategy list with filtering and pagination"""
        try:
            result = await strategy_service.list_strategies(
                page=page,
                page_size=page_size,
                strategy_type=strategy_type,
                status=status,
                user_id=current_user.id
            )
            return {
                "success": True,
                "data": result,
                "message": f"Found {result['total']} strategies"
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/v1/strategies/", status_code=201)
    async def create_strategy(
        request: StrategyCreate,
        current_user: MockUser = Depends(get_current_user)
    ):
        """Create a new strategy"""
        try:
            strategy = await strategy_service.create_strategy(
                request.dict(), current_user.id
            )
            return {
                "success": True,
                "data": strategy,
                "message": f"Strategy '{strategy['name']}' created successfully"
            }
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/v1/strategies/{strategy_id}")
    async def get_strategy(
        strategy_id: str,
        current_user: MockUser = Depends(get_current_user)
    ):
        """Get strategy details"""
        try:
            result = await strategy_service.get_strategy_detail(strategy_id, current_user.id)
            return {
                "success": True,
                "data": result,
                "message": "Strategy details retrieved successfully"
            }
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.put("/api/v1/strategies/{strategy_id}")
    async def update_strategy(
        strategy_id: str,
        request: StrategyUpdate,
        current_user: MockUser = Depends(get_current_user)
    ):
        """Update strategy"""
        try:
            strategy = await strategy_service.update_strategy(
                strategy_id, request.dict(exclude_unset=True), current_user.id
            )
            return {
                "success": True,
                "data": strategy,
                "message": f"Strategy '{strategy['name']}' updated successfully"
            }
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.delete("/api/v1/strategies/{strategy_id}", status_code=204)
    async def delete_strategy(
        strategy_id: str,
        current_user: MockUser = Depends(get_current_user)
    ):
        """Delete strategy"""
        try:
            await strategy_service.delete_strategy(strategy_id, current_user.id)
            return {"success": True, "message": "Strategy deleted successfully"}
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/v1/strategies/batch-operation")
    async def batch_operation(
        request: BatchOperation,
        current_user: MockUser = Depends(get_current_user)
    ):
        """Batch operation on strategies"""
        try:
            result = await strategy_service.batch_operation(
                request.strategy_ids,
                request.operation,
                current_user.id,
                request.parameters
            )
            return {
                "success": True,
                "data": result,
                "message": f"Batch {request.operation} completed: {result['total_success']} success, {result['total_failed']} failed"
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/v1/strategies/templates/")
    async def get_strategy_templates(
        strategy_type: Optional[str] = Query(None),
        current_user: MockUser = Depends(get_current_user)
    ):
        """Get strategy templates"""
        try:
            templates = await strategy_service.get_templates(strategy_type)
            return {
                "success": True,
                "data": templates,
                "message": f"Found {len(templates)} templates"
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/v1/strategies/templates/{template_id}")
    async def get_strategy_template(template_id: str):
        """Get specific strategy template"""
        try:
            template = await strategy_service.get_template(template_id)
            if not template:
                raise HTTPException(status_code=404, detail="Template not found")
            return {
                "success": True,
                "data": template,
                "message": "Template retrieved successfully"
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/v1/strategies/{strategy_id}/execute")
    async def execute_strategy(
        strategy_id: str,
        parameters: Optional[Dict] = None,
        current_user: MockUser = Depends(get_current_user)
    ):
        """Execute strategy"""
        try:
            execution = await strategy_service.execute_strategy(strategy_id, current_user.id, parameters)
            return {
                "success": True,
                "data": execution,
                "message": f"Strategy execution started: {execution['id']}"
            }
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/v1/strategies/executions/{execution_id}")
    async def get_execution_status(
        execution_id: str,
        current_user: MockUser = Depends(get_current_user)
    ):
        """Get execution status"""
        try:
            execution = await strategy_service.get_execution_status(execution_id, current_user.id)
            return {
                "success": True,
                "data": execution,
                "message": "Execution status retrieved successfully"
            }
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/v1/strategies/health")
    async def api_health():
        """API health check"""
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "CBSC Strategy API with Business Logic",
            "version": "1.0.0-demo",
            "endpoints": "operational"
        }

    @app.get("/api/version")
    async def api_version():
        """API version info"""
        return {
            "api_version": "v1.0-demo",
            "implementation": "with_business_logic",
            "endpoints": "8 active endpoints",
            "description": "CBSC Strategy API with concrete business logic"
        }

    return app

if __name__ == "__main__":
    import uvicorn

    print("=" * 70)
    print("CBSC STRATEGY API - WITH BUSINESS LOGIC")
    print("=" * 70)
    print("Starting API server with concrete business logic implementation...")
    print()
    print("Available endpoints:")
    print("  GET  /api/v1/strategies/                    - List strategies")
    print("  POST /api/v1/strategies/                    - Create strategy")
    print("  GET  /api/v1/strategies/{id}               - Get strategy details")
    print("  PUT  /api/v1/strategies/{id}               - Update strategy")
    print("  DELETE /api/v1/strategies/{id}            - Delete strategy")
    print("  POST /api/v1/strategies/batch-operation     - Batch operations")
    print("  GET  /api/v1/strategies/templates/          - Get templates")
    print("  POST /api/v1/strategies/{id}/execute        - Execute strategy")
    print("  GET  /api/v1/strategies/executions/{id}     - Get execution status")
    print()
    print("Server: http://127.0.0.1:3004")
    print("Docs: http://127.0.0.1:3004/docs")
    print("=" * 70)

    app = create_app_with_logic()

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=3004,
        reload=False,
        log_level="info"
    )