"""
RBAC Examples for Strategy API
策略API的RBAC使用示例

展示如何在策略API中應用基於角色的訪問控制。
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime

from ...models.user import User
from ...models.strategy_models_v2 import Strategy
from ...dependencies import (
    get_db, get_current_user,
    permission_required, role_required,
    require_premium, require_verified
)
from ...services.rbac_service import RBACService, get_rbac_service
from ...middleware.auth_middleware import (
    require_permissions, ResourceType, ResourceAction
)

router = APIRouter()


# =============== 策略管理示例 ===============

@router.get("/strategies", response_model=List[dict])
async def list_strategies(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),  # 需要登錄
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """
    獲取策略列表

    權限要求：
    - 所有登錄用戶可以查看自己的策略
    - 策略管理員可以查看所有策略
    - 分析師可以查看所有策略（只讀）
    """
    query = db.query(Strategy)

    # 普通用戶只能看到自己的策略
    if not any(role.name in ['admin', 'super_admin', 'strategy_admin', 'analyst']
               for role in current_user.roles):
        query = query.filter(Strategy.created_by == current_user.id)

    # 應用過濾條件
    if category:
        query = query.filter(Strategy.category == category)

    strategies = query.offset(skip).limit(limit).all()

    # 格式化響應
    strategy_list = []
    for strategy in strategies:
        # 檢查用戶是否有權訪問此策略的詳情
        has_access = await rbac_service.check_permission(
            user=current_user,
            resource_type=ResourceType.STRATEGY,
            action=ResourceAction.READ,
            resource_id=strategy.id
        )

        if has_access.granted:
            strategy_data = {
                "id": strategy.id,
                "name": strategy.name,
                "description": strategy.description,
                "category": strategy.category,
                "status": strategy.status,
                "created_by": strategy.created_by,
                "created_at": strategy.created_at,
                # 根據權限級別決定是否顯示敏感信息
                "parameters": strategy.parameters if has_access.source != "analyst" else None,
                "performance": strategy.performance if has_access.source != "analyst" else None
            }
            strategy_list.append(strategy_data)

    return strategy_list


@router.post("/strategies", response_model=dict)
async def create_strategy(
    strategy_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        permission_required(resource_type="strategy", action="create")
    ),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """
    創建新策略

    權限要求：
    - 需要策略創建權限
    - 高級用戶可以創建更多策略
    """
    # 檢查用戶的策略創建限制
    if not current_user.is_premium:
        # 非高級用戶的策略創建限制
        strategy_count = db.query(Strategy).filter(
            Strategy.created_by == current_user.id
        ).count()

        if strategy_count >= 5:  # 免費用戶最多5個策略
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Free users can create maximum 5 strategies. Upgrade to premium for unlimited strategies."
            )

    # 檢查其他權限條件
    permission_result = await rbac_service.check_permission(
        user=current_user,
        resource_type=ResourceType.STRATEGY,
        action=ResourceAction.CREATE,
        context={
            "category": strategy_data.get("category"),
            "complexity": strategy_data.get("complexity", "basic")
        }
    )

    if not permission_result.granted:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Cannot create strategy: {permission_result.reason}"
        )

    # 創建策略邏輯...
    strategy = Strategy(
        name=strategy_data["name"],
        description=strategy_data.get("description"),
        category=strategy_data.get("category"),
        parameters=strategy_data.get("parameters", {}),
        created_by=current_user.id
    )

    db.add(strategy)
    db.commit()
    db.refresh(strategy)

    return {
        "id": strategy.id,
        "name": strategy.name,
        "message": "Strategy created successfully"
    }


@router.get("/strategies/{strategy_id}", response_model=dict)
async def get_strategy(
    strategy_id: str = Path(..., description="策略ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        permission_required(resource_type="strategy", action="read", resource_id_param="strategy_id")
    )
):
    """
    獲取策略詳情

    權限要求：
    - 策略所有者可以查看完整詳情
    - 策略管理員可以查看所有策略
    - 分析師可以查看但有限制
    """
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found"
        )

    # 檢查是否為策略所有者
    is_owner = strategy.created_by == current_user.id

    # 根據角色和權限決定返回的信息
    response_data = {
        "id": strategy.id,
        "name": strategy.name,
        "description": strategy.description,
        "category": strategy.category,
        "status": strategy.status,
        "created_at": strategy.created_at,
        "updated_at": strategy.updated_at
    }

    # 所有者或管理員可以看到更多信息
    if is_owner or any(role.name in ['admin', 'super_admin', 'strategy_admin']
                       for role in current_user.roles):
        response_data.update({
            "parameters": strategy.parameters,
            "performance": strategy.performance,
            "risk_metrics": strategy.risk_metrics,
            "backtest_results": strategy.backtest_results
        })
    elif any(role.name == 'analyst' for role in current_user.roles):
        # 分析師只能看到部分信息
        response_data.update({
            "performance_summary": strategy.performance.get("summary") if strategy.performance else None,
            "risk_level": strategy.risk_metrics.get("level") if strategy.risk_metrics else None
        })

    return response_data


@router.put("/strategies/{strategy_id}", response_model=dict)
async def update_strategy(
    strategy_id: str = Path(..., description="策略ID"),
    strategy_data: dict = ...,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        permission_required(resource_type="strategy", action="update", resource_id_param="strategy_id")
    )
):
    """
    更新策略

    權限要求：
    - 策略所有者可以更新
    - 策略管理員可以更新任何策略
    """
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found"
        )

    # 更新策略邏輯...
    if "name" in strategy_data:
        strategy.name = strategy_data["name"]
    if "description" in strategy_data:
        strategy.description = strategy_data["description"]
    if "parameters" in strategy_data:
        strategy.parameters = strategy_data["parameters"]

    db.commit()

    return {
        "id": strategy.id,
        "message": "Strategy updated successfully"
    }


@router.delete("/strategies/{strategy_id}", response_model=dict)
async def delete_strategy(
    strategy_id: str = Path(..., description="策略ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        permission_required(resource_type="strategy", action="delete", resource_id_param="strategy_id")
    )
):
    """
    刪除策略

    權限要求：
    - 策略所有者可以刪除
    - 策略管理員可以刪除任何策略
    - 超級管理員可以刪除任何策略
    """
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found"
        )

    # 策略正在運行時不能刪除
    if strategy.status == "running":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete strategy that is currently running"
        )

    db.delete(strategy)
    db.commit()

    return {"message": "Strategy deleted successfully"}


@router.post("/strategies/{strategy_id}/execute", response_model=dict)
async def execute_strategy(
    strategy_id: str = Path(..., description="策略ID"),
    execution_params: dict = ...,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        permission_required(resource_type="strategy", action="execute", resource_id_param="strategy_id")
    ),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """
    執行策略

    權限要求：
    - 策略所有者可以執行
    - 策略管理員可以執行任何策略
    - 需要高級用戶權限才能執行實時交易策略
    """
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found"
        )

    # 檢查是否為實時交易策略
    is_live_trading = execution_params.get("live_trading", False)

    if is_live_trading:
        # 實時交易需要額外權限
        trading_permission = await rbac_service.check_permission(
            user=current_user,
            resource_type=ResourceType.TRADING,
            action=ResourceAction.EXECUTE
        )

        if not trading_permission.granted:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Live trading requires special permissions"
            )

        # 實時交易必須是高級用戶
        if not current_user.is_premium:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Live trading is only available for premium users"
            )

    # 執行策略邏輯...
    execution_id = f"exec_{strategy_id}_{datetime.now().timestamp()}"

    return {
        "execution_id": execution_id,
        "strategy_id": strategy_id,
        "status": "started",
        "message": "Strategy execution started"
    }


# =============== 角色權限示例 ===============

@router.get("/strategies/admin/dashboard", response_model=dict)
async def get_admin_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        role_required(roles=["admin", "super_admin", "strategy_admin"])
    )
):
    """
    獲取管理員儀表板

    權限要求：
    - 需要管理員或策略管理員角色
    """
    # 統計信息
    total_strategies = db.query(Strategy).count()
    active_strategies = db.query(Strategy).filter(Strategy.status == "active").count()

    # 按用戶統計
    user_strategies = db.query(
        Strategy.created_by,
        func.count(Strategy.id).label("count")
    ).group_by(Strategy.created_by).all()

    return {
        "total_strategies": total_strategies,
        "active_strategies": active_strategies,
        "user_strategies": [
            {"user_id": user_id, "strategy_count": count}
            for user_id, count in user_strategies
        ]
    }


@router.post("/strategies/{strategy_id}/approve", response_model=dict)
async def approve_strategy(
    strategy_id: str = Path(..., description="策略ID"),
    approval_data: dict = ...,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        role_required(roles=["admin", "super_admin", "strategy_admin"])
    )
):
    """
    批准策略（管理員功能）

    權限要求：
    - 需要管理員或策略管理員角色
    """
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found"
        )

    # 批准策略邏輯...
    strategy.status = "approved"
    strategy.approved_by = current_user.id
    strategy.approved_at = datetime.utcnow()

    db.commit()

    return {
        "strategy_id": strategy_id,
        "approved_by": current_user.id,
        "message": "Strategy approved successfully"
    }


@router.get("/strategies/analytics", response_model=dict)
async def get_strategy_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        role_required(roles=["admin", "super_admin", "strategy_admin", "analyst"])
    )
):
    """
    獲取策略分析數據

    權限要求：
    - 管理員、策略管理員或分析師角色
    """
    # 分析師只能看到聚合數據，不能看到具體用戶數據
    is_analyst = any(role.name == 'analyst' for role in current_user.roles)

    if is_analyst:
        # 返回匿名化的聚合數據
        analytics = {
            "total_strategies": db.query(Strategy).count(),
            "category_distribution": db.query(
                Strategy.category,
                func.count(Strategy.id).label("count")
            ).group_by(Strategy.category).all(),
            "performance_stats": {
                "avg_return": db.query(func.avg(Strategy.performance["total_return"])).scalar(),
                "best_performing": db.query(Strategy).order_by(
                    Strategy.performance["total_return"].desc()
                ).first().name if db.query(Strategy).first() else None
            }
        }
    else:
        # 管理員可以看到完整數據
        analytics = {
            "total_strategies": db.query(Strategy).count(),
            "user_strategies": db.query(
                Strategy.created_by,
                func.count(Strategy.id).label("count")
            ).group_by(Strategy.created_by).all(),
            "category_distribution": db.query(
                Strategy.category,
                func.count(Strategy.id).label("count")
            ).group_by(Strategy.category).all(),
            "performance_stats": {
                "avg_return": db.query(func.avg(Strategy.performance["total_return"])).scalar(),
                "best_performing": db.query(Strategy).order_by(
                    Strategy.performance["total_return"].desc()
                ).first(),
                "worst_performing": db.query(Strategy).order_by(
                    Strategy.performance["total_return"].asc()
                ).first()
            }
        }

    return analytics


# =============== 高級權限示例 ===============

@router.post("/strategies/batch-operation", response_model=dict)
async def batch_update_strategies(
    operation: dict = ...,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        permission_required(resource_type="strategy", action="update")
    ),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """
    批量更新策略

    權限要求：
    - 需要策略更新權限
    - 批量操作可能需要特殊權限
    """
    # 檢查批量操作權限
    batch_permission = await rbac_service.check_permission(
        user=current_user,
        resource_type=ResourceType.STRATEGY,
        action=ResourceAction.UPDATE,
        context={"batch_operation": True, "count": len(operation.get("strategy_ids", []))}
    )

    if not batch_permission.granted:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Batch operations require special permissions"
        )

    # 執行批量更新邏輯...
    strategy_ids = operation.get("strategy_ids", [])
    updates = operation.get("updates", {})

    # 檢查每個策略的權限
    updated_count = 0
    for strategy_id in strategy_ids:
        strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
        if strategy:
            # 檢查權限
            has_permission = await rbac_service.check_permission(
                user=current_user,
                resource_type=ResourceType.STRATEGY,
                action=ResourceAction.UPDATE,
                resource_id=strategy_id
            )

            if has_permission.granted:
                # 更新策略
                for key, value in updates.items():
                    setattr(strategy, key, value)
                updated_count += 1

    db.commit()

    return {
        "total_strategies": len(strategy_ids),
        "updated_count": updated_count,
        "message": f"Successfully updated {updated_count} strategies"
    }