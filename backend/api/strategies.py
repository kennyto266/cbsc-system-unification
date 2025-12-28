"""
策略API模块 - 提供策略管理相关接口
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from datetime import datetime
import uuid

from services.webhook_service import WebhookService
from models.webhooks import WebhookEvent

router = APIRouter()

# 初始化Webhook服务
webhook_service = WebhookService()

# 模拟策略数据
MOCK_STRATEGIES = [
    {
        "id": "strategy_1",
        "name": "价值投资策略",
        "description": "基于基本面分析，寻找低估值的优质股票进行长期投资",
        "type": "value",
        "risk_level": "medium",
        "expected_return": 12.5,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-15T10:30:00Z",
        "performance": {
            "total_return": 15.2,
            "annualized_return": 12.5,
            "max_drawdown": -8.3,
            "sharpe_ratio": 1.35,
            "volatility": 12.8
        },
        "rules": [
            {"rule": "P/E比率 < 15", "weight": 0.3},
            {"rule": "股息率 > 3%", "weight": 0.2},
            {"rule": "ROE > 15%", "weight": 0.25},
            {"rule": "负债率 < 50%", "weight": 0.25}
        ]
    },
    {
        "id": "strategy_2",
        "name": "成长股策略",
        "description": "专注于高成长性股票，适合风险承受能力较强的投资者",
        "type": "growth",
        "risk_level": "high",
        "expected_return": 18.5,
        "created_at": "2024-02-01T00:00:00Z",
        "updated_at": "2024-02-10T14:20:00Z",
        "performance": {
            "total_return": 22.8,
            "annualized_return": 18.5,
            "max_drawdown": -15.6,
            "sharpe_ratio": 1.12,
            "volatility": 20.5
        },
        "rules": [
            {"rule": "营收增长率 > 20%", "weight": 0.4},
            {"rule": "净利润增长率 > 25%", "weight": 0.4},
            {"rule": "PEG比率 < 1.5", "weight": 0.2}
        ]
    },
    {
        "id": "strategy_3",
        "name": "均衡配置策略",
        "description": "在价值和成长之间保持平衡，适合稳健型投资者",
        "type": "balanced",
        "risk_level": "medium",
        "expected_return": 10.8,
        "created_at": "2024-03-01T00:00:00Z",
        "updated_at": "2024-03-05T09:15:00Z",
        "performance": {
            "total_return": 11.5,
            "annualized_return": 10.8,
            "max_drawdown": -6.2,
            "sharpe_ratio": 1.45,
            "volatility": 8.9
        },
        "rules": [
            {"rule": "价值股比例: 40%", "weight": 0.4},
            {"rule": "成长股比例: 40%", "weight": 0.4},
            {"rule": "债券比例: 20%", "weight": 0.2}
        ]
    }
]

@router.get("/strategies")
async def get_strategies():
    """获取策略列表"""
    return {
        "success": True,
        "data": MOCK_STRATEGIES,
        "message": "策略列表获取成功",
        "timestamp": datetime.now().isoformat()
    }

@router.get("/strategies/{strategy_id}")
async def get_strategy(strategy_id: str):
    """获取策略详情"""
    strategy = next((s for s in MOCK_STRATEGIES if s["id"] == strategy_id), None)
    if not strategy:
        raise HTTPException(status_code=404, detail="策略不存在")

    return {
        "success": True,
        "data": strategy,
        "message": "策略详情获取成功",
        "timestamp": datetime.now().isoformat()
    }

@router.post("/strategies")
async def create_strategy(request: Dict[str, Any]):
    """创建策略"""
    try:
        name = request.get("name")
        description = request.get("description", "")
        strategy_type = request.get("type", "balanced")
        risk_level = request.get("risk_level", "medium")
        expected_return = request.get("expected_return", 10.0)
        rules = request.get("rules", [])

        if not name:
            raise HTTPException(status_code=400, detail="策略名称不能为空")

        # 创建新策略
        new_strategy = {
            "id": f"strategy_{uuid.uuid4().hex[:8]}",
            "name": name,
            "description": description,
            "type": strategy_type,
            "risk_level": risk_level,
            "expected_return": expected_return,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "performance": {
                "total_return": 0,
                "annualized_return": 0,
                "max_drawdown": 0,
                "sharpe_ratio": 0,
                "volatility": 0
            },
            "rules": rules
        }

        MOCK_STRATEGIES.append(new_strategy)

        # 触发Webhook事件
        try:
            await webhook_service.trigger_event(
                WebhookEvent.STRATEGY_CREATED,
                {
                    "strategy_id": new_strategy["id"],
                    "name": new_strategy["name"],
                    "type": new_strategy["type"],
                    "risk_level": new_strategy["risk_level"],
                    "created_at": new_strategy["created_at"]
                }
            )
        except Exception as webhook_error:
            # Webhook失败不影响主流程，记录日志即可
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"触发策略创建Webhook失败: {webhook_error}")

        return {
            "success": True,
            "data": new_strategy,
            "message": "策略创建成功",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建策略失败: {str(e)}")

@router.put("/strategies/{strategy_id}")
async def update_strategy(strategy_id: str, request: Dict[str, Any]):
    """更新策略"""
    strategy = next((s for s in MOCK_STRATEGIES if s["id"] == strategy_id), None)
    if not strategy:
        raise HTTPException(status_code=404, detail="策略不存在")

    try:
        # 更新策略信息
        if "name" in request:
            strategy["name"] = request["name"]
        if "description" in request:
            strategy["description"] = request["description"]
        if "type" in request:
            strategy["type"] = request["type"]
        if "risk_level" in request:
            strategy["risk_level"] = request["risk_level"]
        if "expected_return" in request:
            strategy["expected_return"] = request["expected_return"]
        if "rules" in request:
            strategy["rules"] = request["rules"]

        strategy["updated_at"] = datetime.now().isoformat()

        # 触发Webhook事件
        try:
            await webhook_service.trigger_event(
                WebhookEvent.STRATEGY_UPDATED,
                {
                    "strategy_id": strategy["id"],
                    "name": strategy["name"],
                    "type": strategy["type"],
                    "risk_level": strategy["risk_level"],
                    "updated_at": strategy["updated_at"]
                }
            )
        except Exception as webhook_error:
            # Webhook失败不影响主流程，记录日志即可
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"触发策略更新Webhook失败: {webhook_error}")

        return {
            "success": True,
            "data": strategy,
            "message": "策略更新成功",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新策略失败: {str(e)}")

@router.delete("/strategies/{strategy_id}")
async def delete_strategy(strategy_id: str):
    """删除策略"""
    global MOCK_STRATEGIES
    strategy = next((s for s in MOCK_STRATEGIES if s["id"] == strategy_id), None)
    if not strategy:
        raise HTTPException(status_code=404, detail="策略不存在")

    MOCK_STRATEGIES = [s for s in MOCK_STRATEGIES if s["id"] != strategy_id]

    # 触发Webhook事件
    try:
        await webhook_service.trigger_event(
            WebhookEvent.STRATEGY_DELETED,
            {
                "strategy_id": strategy_id,
                "name": strategy["name"],
                "deleted_at": datetime.now().isoformat()
            }
        )
    except Exception as webhook_error:
        # Webhook失败不影响主流程，记录日志即可
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"触发策略删除Webhook失败: {webhook_error}")

    return {
        "success": True,
        "message": "策略删除成功",
        "timestamp": datetime.now().isoformat()
    }

@router.post("/strategies/{strategy_id}/backtest")
async def backtest_strategy(strategy_id: str, request: Dict[str, Any]):
    """策略回测"""
    strategy = next((s for s in MOCK_STRATEGIES if s["id"] == strategy_id), None)
    if not strategy:
        raise HTTPException(status_code=404, detail="策略不存在")

    try:
        start_date = request.get("start_date", "2023-01-01")
        end_date = request.get("end_date", "2024-01-01")
        initial_capital = request.get("initial_capital", 100000)

        # 触发回测开始Webhook事件
        try:
            await webhook_service.trigger_event(
                WebhookEvent.STRATEGY_BACKTEST_STARTED,
                {
                    "strategy_id": strategy_id,
                    "strategy_name": strategy["name"],
                    "backtest_period": {
                        "start_date": start_date,
                        "end_date": end_date
                    },
                    "initial_capital": initial_capital,
                    "started_at": datetime.now().isoformat()
                }
            )
        except Exception as webhook_error:
            # Webhook失败不影响主流程，记录日志即可
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"触发策略回测开始Webhook失败: {webhook_error}")

        # 模拟回测结果
        backtest_result = {
            "strategy_id": strategy_id,
            "strategy_name": strategy["name"],
            "backtest_period": {
                "start_date": start_date,
                "end_date": end_date
            },
            "initial_capital": initial_capital,
            "final_capital": initial_capital * (1 + strategy["performance"]["total_return"] / 100),
            "total_return": strategy["performance"]["total_return"],
            "annualized_return": strategy["performance"]["annualized_return"],
            "max_drawdown": strategy["performance"]["max_drawdown"],
            "sharpe_ratio": strategy["performance"]["sharpe_ratio"],
            "volatility": strategy["performance"]["volatility"],
            "win_rate": 0.65,
            "profit_factor": 1.8,
            "trades_count": 42,
            "created_at": datetime.now().isoformat()
        }

        # 触发回测完成Webhook事件
        try:
            await webhook_service.trigger_event(
                WebhookEvent.STRATEGY_BACKTEST_COMPLETED,
                {
                    "strategy_id": strategy_id,
                    "strategy_name": strategy["name"],
                    "backtest_result": {
                        "total_return": backtest_result["total_return"],
                        "annualized_return": backtest_result["annualized_return"],
                        "max_drawdown": backtest_result["max_drawdown"],
                        "sharpe_ratio": backtest_result["sharpe_ratio"],
                        "win_rate": backtest_result["win_rate"],
                        "trades_count": backtest_result["trades_count"]
                    },
                    "completed_at": datetime.now().isoformat()
                }
            )
        except Exception as webhook_error:
            # Webhook失败不影响主流程，记录日志即可
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"触发策略回测完成Webhook失败: {webhook_error}")

        return {
            "success": True,
            "data": backtest_result,
            "message": "策略回测成功",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"策略回测失败: {str(e)}")

@router.get("/strategies/{strategy_id}/performance")
async def get_strategy_performance(strategy_id: str):
    """获取策略绩效"""
    strategy = next((s for s in MOCK_STRATEGIES if s["id"] == strategy_id), None)
    if not strategy:
        raise HTTPException(status_code=404, detail="策略不存在")

    # 模拟历史绩效数据
    performance_data = {
        "strategy_id": strategy_id,
        "strategy_name": strategy["name"],
        "current_performance": strategy["performance"],
        "monthly_returns": [
            {"month": "2024-01", "return": 2.5},
            {"month": "2024-02", "return": -1.2},
            {"month": "2024-03", "return": 3.8},
            {"month": "2024-04", "return": 1.5},
            {"month": "2024-05", "return": 4.2},
            {"month": "2024-06", "return": -0.8}
        ],
        "benchmark_comparison": {
            "strategy_return": 15.2,
            "benchmark_return": 12.8,
            "excess_return": 2.4
        },
        "risk_metrics": {
            "var_95": -2.5,
            "cvar_95": -3.8,
            "beta": 0.95,
            "alpha": 2.4,
            "information_ratio": 0.68
        }
    }

    return {
        "success": True,
        "data": performance_data,
        "message": "策略绩效获取成功",
        "timestamp": datetime.now().isoformat()
    }