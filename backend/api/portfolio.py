"""
投资组合API模块 - 提供投资组合管理相关接口
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from datetime import datetime
import uuid

router = APIRouter()

# 模拟投资组合数据
MOCK_PORTFOLIOS = [
    {
        "id": "portfolio_1",
        "name": "港股核心组合",
        "description": "以腾讯、友邦等港股蓝筹股为核心的投资组合",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-15T10:30:00Z",
        "total_value": 1000000,
        "total_return": 8.5,
        "holdings": [
            {"symbol": "0700.HK", "name": "腾讯控股", "quantity": 100, "average_price": 300, "current_price": 325, "value": 32500, "return": 8.33},
            {"symbol": "1299.HK", "name": "友邦保险", "quantity": 200, "average_price": 80, "current_price": 85, "value": 17000, "return": 6.25},
            {"symbol": "2800.HK", "name": "盈富基金", "quantity": 500, "average_price": 18, "current_price": 19, "value": 9500, "return": 5.56}
        ]
    },
    {
        "id": "portfolio_2", 
        "name": "科技成长组合",
        "description": "专注于科技股的成长型投资组合",
        "created_at": "2024-02-01T00:00:00Z",
        "updated_at": "2024-02-10T14:20:00Z",
        "total_value": 500000,
        "total_return": 12.3,
        "holdings": [
            {"symbol": "0700.HK", "name": "腾讯控股", "quantity": 50, "average_price": 320, "current_price": 325, "value": 16250, "return": 1.56},
            {"symbol": "9988.HK", "name": "阿里巴巴", "quantity": 100, "average_price": 85, "current_price": 95, "value": 9500, "return": 11.76}
        ]
    }
]

@router.get("/portfolios")
async def get_portfolios():
    """获取投资组合列表"""
    return {
        "success": True,
        "data": MOCK_PORTFOLIOS,
        "message": "投资组合列表获取成功",
        "timestamp": datetime.now().isoformat()
    }

@router.get("/portfolios/{portfolio_id}")
async def get_portfolio(portfolio_id: str):
    """获取投资组合详情"""
    portfolio = next((p for p in MOCK_PORTFOLIOS if p["id"] == portfolio_id), None)
    if not portfolio:
        raise HTTPException(status_code=404, detail="投资组合不存在")
    
    return {
        "success": True,
        "data": portfolio,
        "message": "投资组合详情获取成功",
        "timestamp": datetime.now().isoformat()
    }

@router.post("/portfolios")
async def create_portfolio(request: Dict[str, Any]):
    """创建投资组合"""
    try:
        name = request.get("name")
        description = request.get("description", "")
        
        if not name:
            raise HTTPException(status_code=400, detail="投资组合名称不能为空")
        
        # 创建新投资组合
        new_portfolio = {
            "id": f"portfolio_{uuid.uuid4().hex[:8]}",
            "name": name,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "total_value": 0,
            "total_return": 0,
            "holdings": []
        }
        
        MOCK_PORTFOLIOS.append(new_portfolio)
        
        return {
            "success": True,
            "data": new_portfolio,
            "message": "投资组合创建成功",
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建投资组合失败: {str(e)}")

@router.put("/portfolios/{portfolio_id}")
async def update_portfolio(portfolio_id: str, request: Dict[str, Any]):
    """更新投资组合"""
    portfolio = next((p for p in MOCK_PORTFOLIOS if p["id"] == portfolio_id), None)
    if not portfolio:
        raise HTTPException(status_code=404, detail="投资组合不存在")
    
    try:
        # 更新投资组合信息
        if "name" in request:
            portfolio["name"] = request["name"]
        if "description" in request:
            portfolio["description"] = request["description"]
        
        portfolio["updated_at"] = datetime.now().isoformat()
        
        return {
            "success": True,
            "data": portfolio,
            "message": "投资组合更新成功",
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新投资组合失败: {str(e)}")

@router.delete("/portfolios/{portfolio_id}")
async def delete_portfolio(portfolio_id: str):
    """删除投资组合"""
    global MOCK_PORTFOLIOS
    portfolio = next((p for p in MOCK_PORTFOLIOS if p["id"] == portfolio_id), None)
    if not portfolio:
        raise HTTPException(status_code=404, detail="投资组合不存在")
    
    MOCK_PORTFOLIOS = [p for p in MOCK_PORTFOLIOS if p["id"] != portfolio_id]
    
    return {
        "success": True,
        "message": "投资组合删除成功",
        "timestamp": datetime.now().isoformat()
    }

@router.post("/portfolios/{portfolio_id}/holdings")
async def add_holding(portfolio_id: str, request: Dict[str, Any]):
    """添加持仓"""
    portfolio = next((p for p in MOCK_PORTFOLIOS if p["id"] == portfolio_id), None)
    if not portfolio:
        raise HTTPException(status_code=404, detail="投资组合不存在")
    
    try:
        symbol = request.get("symbol")
        quantity = request.get("quantity")
        average_price = request.get("average_price")
        
        if not all([symbol, quantity, average_price]):
            raise HTTPException(status_code=400, detail="缺少必要参数")
        
        # 添加新持仓
        new_holding = {
            "symbol": symbol,
            "name": f"股票{symbol}",  # 实际应该从股票信息API获取
            "quantity": quantity,
            "average_price": average_price,
            "current_price": average_price,  # 实际应该从市场数据获取
            "value": quantity * average_price,
            "return": 0
        }
        
        portfolio["holdings"].append(new_holding)
        portfolio["updated_at"] = datetime.now().isoformat()
        
        return {
            "success": True,
            "data": new_holding,
            "message": "持仓添加成功",
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"添加持仓失败: {str(e)}")

@router.delete("/portfolios/{portfolio_id}/holdings/{symbol}")
async def remove_holding(portfolio_id: str, symbol: str):
    """移除持仓"""
    portfolio = next((p for p in MOCK_PORTFOLIOS if p["id"] == portfolio_id), None)
    if not portfolio:
        raise HTTPException(status_code=404, detail="投资组合不存在")
    
    # 移除指定持仓
    original_length = len(portfolio["holdings"])
    portfolio["holdings"] = [h for h in portfolio["holdings"] if h["symbol"] != symbol]
    
    if len(portfolio["holdings"]) == original_length:
        raise HTTPException(status_code=404, detail="持仓不存在")
    
    portfolio["updated_at"] = datetime.now().isoformat()
    
    return {
        "success": True,
        "message": "持仓移除成功",
        "timestamp": datetime.now().isoformat()
    }
