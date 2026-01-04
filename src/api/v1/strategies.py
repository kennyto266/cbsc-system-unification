"""
Strategies API Routes
策略 API 路由

Strategy management endpoints
策略管理端點
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from core.logging import logger

router = APIRouter()


class StrategyBase(BaseModel):
    """Base strategy model"""
    name: str
    description: str
    strategy_type: str
    is_active: bool = True


class StrategyCreate(StrategyBase):
    """Strategy creation model"""
    pass


class StrategyUpdate(BaseModel):
    """Strategy update model"""
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class Strategy(StrategyBase):
    """Strategy response model"""
    id: int
    created_at: datetime
    updated_at: datetime
    performance: Optional[dict] = None

    class Config:
        from_attributes = True


class PaginatedStrategies(BaseModel):
    """Paginated strategies response model"""
    items: List[Strategy]
    total: int
    page: int
    page_size: int
    total_pages: int


# Mock data storage
mock_strategies = [
    {
        "id": 1,
        "name": "Moving Average Crossover",
        "description": "Strategy based on moving average crossover signals",
        "strategy_type": "technical",
        "is_active": True,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "performance": {
            "total_return": 0.15,
            "sharpe_ratio": 1.2,
            "max_drawdown": -0.08
        }
    },
    {
        "id": 2,
        "name": "RSI Mean Reversion",
        "description": "Strategy using RSI overbought/oversold signals",
        "strategy_type": "technical",
        "is_active": True,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "performance": {
            "total_return": 0.12,
            "sharpe_ratio": 1.0,
            "max_drawdown": -0.06
        }
    }
]


@router.get("/", response_model=PaginatedStrategies)
async def get_strategies(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    strategy_type: Optional[str] = Query(None)
):
    """
    Get all strategies with pagination and filtering
    獲取所有策略，支持分頁和過濾
    """
    logger.info(f"Getting strategies - page: {page}, page_size: {page_size}")

    # Filter strategies
    filtered_strategies = mock_strategies
    if search:
        filtered_strategies = [
            s for s in filtered_strategies
            if search.lower() in s["name"].lower() or search.lower() in s["description"].lower()
        ]
    if strategy_type:
        filtered_strategies = [
            s for s in filtered_strategies
            if s["strategy_type"] == strategy_type
        ]

    # Pagination
    total = len(filtered_strategies)
    start = (page - 1) * page_size
    end = start + page_size
    items = filtered_strategies[start:end]

    total_pages = (total + page_size - 1) // page_size

    return PaginatedStrategies(
        items=[Strategy(**item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/{strategy_id}", response_model=Strategy)
async def get_strategy(strategy_id: int):
    """
    Get a specific strategy by ID
    根據ID獲取特定策略
    """
    logger.info(f"Getting strategy: {strategy_id}")

    strategy = next((s for s in mock_strategies if s["id"] == strategy_id), None)
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    return Strategy(**strategy)


@router.post("/", response_model=Strategy)
async def create_strategy(strategy: StrategyCreate):
    """
    Create a new strategy
    創建新策略
    """
    logger.info(f"Creating strategy: {strategy.name}")

    new_id = max(s["id"] for s in mock_strategies) + 1
    new_strategy = {
        "id": new_id,
        **strategy.dict(),
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "performance": None
    }

    mock_strategies.append(new_strategy)
    return Strategy(**new_strategy)


@router.put("/{strategy_id}", response_model=Strategy)
async def update_strategy(strategy_id: int, strategy: StrategyUpdate):
    """
    Update an existing strategy
    更新現有策略
    """
    logger.info(f"Updating strategy: {strategy_id}")

    strategy_index = next((i for i, s in enumerate(mock_strategies) if s["id"] == strategy_id), None)
    if strategy_index is None:
        raise HTTPException(status_code=404, detail="Strategy not found")

    # Update strategy
    for field, value in strategy.dict(exclude_unset=True).items():
        mock_strategies[strategy_index][field] = value
    mock_strategies[strategy_index]["updated_at"] = datetime.now()

    return Strategy(**mock_strategies[strategy_index])


@router.delete("/{strategy_id}")
async def delete_strategy(strategy_id: int):
    """
    Delete a strategy
    刪除策略
    """
    logger.info(f"Deleting strategy: {strategy_id}")

    strategy_index = next((i for i, s in enumerate(mock_strategies) if s["id"] == strategy_id), None)
    if strategy_index is None:
        raise HTTPException(status_code=404, detail="Strategy not found")

    mock_strategies.pop(strategy_index)
    return {"success": True, "message": "Strategy deleted successfully"}


@router.post("/{strategy_id}/execute")
async def execute_strategy(strategy_id: int):
    """
    Execute a strategy
    執行策略
    """
    logger.info(f"Executing strategy: {strategy_id}")

    strategy = next((s for s in mock_strategies if s["id"] == strategy_id), None)
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    if not strategy["is_active"]:
        raise HTTPException(status_code=400, detail="Strategy is not active")

    # TODO: Implement actual strategy execution logic
    return {
        "success": True,
        "message": f"Strategy '{strategy['name']}' execution started",
        "execution_id": f"exec_{datetime.now().timestamp()}"
    }