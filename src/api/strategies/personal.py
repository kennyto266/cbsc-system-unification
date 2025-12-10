"""
用户个性化功能
Personal Features

职责：
- 个人仪表板
- 用户偏好设置
- 策略推荐
- 操作历史
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
import logging

from .services.personal_service import PersonalService
from .repositories.strategy_repository import StrategyRepository
from .repositories.user_repository import UserRepository
from .utils.cache import CacheManager
from .utils.validators import PersonalDataValidator
from .utils.permissions import get_current_user
from .schemas import (
    DashboardResponse, UserPreferences, StrategyControlRequest,
    OperationHistoryResponse, StrategyRecommendations,
    RealTimeUpdate, BaseResponse
)
from .models import User

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter()


# 依赖注入
async def get_personal_service() -> PersonalService:
    """获取个人化服务实例"""
    # 这里应该通过依赖注入容器获取
    strategy_repo = StrategyRepository()
    user_repo = UserRepository()
    cache_manager = CacheManager()
    validator = PersonalDataValidator()
    return PersonalService(strategy_repo, user_repo, cache_manager, validator)


# ============================================================================
# 个人仪表板端点 (Personal Dashboard Endpoints)
# ============================================================================

@router.get("/dashboard", response_model=DashboardResponse)
async def get_personal_dashboard(
    current_user: User = Depends(get_current_user),
    personal_service: PersonalService = Depends(get_personal_service)
):
    """
    获取个人仪表板

    返回用户的个人仪表板数据，包括：
    - 策略统计
    - 收益概览
    - 最佳/最差策略
    - 最近信号
    - 市场概览
    - 性能图表
    """
    try:
        dashboard_data = await personal_service.get_dashboard_data(current_user.id)
        return dashboard_data

    except Exception as e:
        logger.error(f"获取个人仪表板失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取个人仪表板失败: {str(e)}"
        )


# ============================================================================
# 用户偏好设置端点 (User Preferences Endpoints)
# ============================================================================

@router.get("/preferences", response_model=UserPreferences)
async def get_user_preferences(
    current_user: User = Depends(get_current_user),
    personal_service: PersonalService = Depends(get_personal_service)
):
    """
    获取用户偏好设置

    返回用户的个人偏好设置，包括：
    - 默认策略类型
    - 风险承受能力
    - 通知设置
    - 仪表板布局
    - 自动刷新间隔
    """
    try:
        preferences = await personal_service.get_user_preferences(current_user.id)
        return preferences

    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"获取用户偏好设置失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取用户偏好设置失败: {str(e)}"
        )


@router.put("/preferences", response_model=UserPreferences)
async def update_user_preferences(
    preferences: UserPreferences,
    current_user: User = Depends(get_current_user),
    personal_service: PersonalService = Depends(get_personal_service)
):
    """
    更新用户偏好设置

    可以更新的设置包括：
    - 默认策略类型
    - 风险承受能力
    - 通知开关
    - 仪表板布局
    - 自动刷新间隔
    """
    try:
        updated_preferences = await personal_service.update_user_preferences(
            current_user.id,
            preferences
        )
        return updated_preferences

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"更新用户偏好设置失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"更新用户偏好设置失败: {str(e)}"
        )


# ============================================================================
# 策略控制端点 (Strategy Control Endpoints)
# ============================================================================

@router.post("/strategies/{strategy_id}/control", response_model=BaseResponse)
async def control_strategy(
    strategy_id: str,
    request: StrategyControlRequest,
    current_user: User = Depends(get_current_user),
    personal_service: PersonalService = Depends(get_personal_service)
):
    """
    控制策略

    支持的控制操作：
    - enable: 启用策略
    - disable: 禁用策略
    - start: 开始执行
    - stop: 停止执行
    - pause: 暂停执行
    """
    try:
        result = await personal_service.control_strategy(
            current_user.id,
            strategy_id,
            request
        )

        return BaseResponse(
            data=result,
            message=result.get("message", "操作完成")
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=403,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"控制策略失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"控制策略失败: {str(e)}"
        )


@router.get("/strategies/{strategy_id}/history", response_model=OperationHistoryResponse)
async def get_strategy_history(
    strategy_id: str,
    limit: int = Query(50, ge=1, le=200, description="返回数量限制"),
    current_user: User = Depends(get_current_user),
    personal_service: PersonalService = Depends(get_personal_service)
):
    """
    获取策略操作历史

    返回指定策略的操作历史记录，包括：
    - 操作类型
    - 操作时间
    - 操作原因
    - 操作结果
    """
    try:
        history = await personal_service.get_strategy_history(
            current_user.id,
            strategy_id,
            limit
        )
        return history

    except PermissionError as e:
        raise HTTPException(
            status_code=403,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"获取策略历史失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取策略历史失败: {str(e)}"
        )


# ============================================================================
# 策略推荐端点 (Strategy Recommendations Endpoints)
# ============================================================================

@router.get("/recommendations", response_model=StrategyRecommendations)
async def get_strategy_recommendations(
    current_user: User = Depends(get_current_user),
    personal_service: PersonalService = Depends(get_personal_service)
):
    """
    获取策略推荐

    基于用户的历史行为和偏好，推荐适合的策略：
    - 分析现有策略组合
    - 考虑风险偏好
    - 参考市场趋势
    - 提供置信度评分
    """
    try:
        recommendations = await personal_service.get_strategy_recommendations(current_user.id)
        return recommendations

    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"获取策略推荐失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取策略推荐失败: {str(e)}"
        )


# ============================================================================
# 实时数据端点 (Real-time Data Endpoints)
# ============================================================================

@router.get("/realtime-updates", response_model=RealTimeUpdate)
async def get_realtime_updates(
    current_user: User = Depends(get_current_user),
    personal_service: PersonalService = Depends(get_personal_service)
):
    """
    获取实时更新

    返回用户的实时数据更新，包括：
    - 策略状态更新
    - 新信号通知
    - 市场数据变化
    - 个人告警信息
    """
    try:
        updates = await personal_service.get_real_time_updates(current_user.id)
        return updates

    except Exception as e:
        logger.error(f"获取实时更新失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取实时更新失败: {str(e)}"
        )


@router.get("/notifications", response_model=dict)
async def get_user_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False, description="只显示未读通知"),
    current_user: User = Depends(get_current_user)
):
    """
    获取用户通知

    返回用户的通知列表，支持分页和过滤。
    """
    try:
        # 简化实现，实际应该从通知服务获取
        notifications = [
            {
                "id": "notif_1",
                "type": "signal",
                "title": "高置信度信号",
                "message": "您的RSI策略产生了高置信度买入信号",
                "timestamp": "2025-12-10T10:00:00Z",
                "is_read": False,
                "strategy_id": "strategy_123"
            },
            {
                "id": "notif_2",
                "type": "system",
                "title": "系统维护通知",
                "message": "系统将于今晚进行维护",
                "timestamp": "2025-12-10T09:00:00Z",
                "is_read": True,
                "strategy_id": None
            }
        ]

        # 过滤未读通知
        if unread_only:
            notifications = [n for n in notifications if not n["is_read"]]

        # 分页
        start = (page - 1) * page_size
        end = start + page_size
        paginated_notifications = notifications[start:end]

        return {
            "notifications": paginated_notifications,
            "total_count": len(notifications),
            "unread_count": len([n for n in notifications if not n["is_read"]]),
            "page": page,
            "page_size": page_size,
            "total_pages": (len(notifications) + page_size - 1) // page_size
        }

    except Exception as e:
        logger.error(f"获取用户通知失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取用户通知失败: {str(e)}"
        )


@router.post("/notifications/{notification_id}/read", response_model=BaseResponse)
async def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    标记通知为已读

    将指定通知标记为已读状态。
    """
    try:
        # 这里应该调用通知服务更新状态
        # 暂时返回成功响应

        return BaseResponse(
            message="通知已标记为已读"
        )

    except Exception as e:
        logger.error(f"标记通知已读失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"标记通知已读失败: {str(e)}"
        )


# ============================================================================
# 用户统计端点 (User Statistics Endpoints)
# ============================================================================

@router.get("/statistics", response_model=dict)
async def get_user_statistics(
    current_user: User = Depends(get_current_user),
    personal_service: PersonalService = Depends(get_personal_service)
):
    """
    获取用户统计信息

    返回用户的详细统计信息：
    - 策略创建趋势
    - 执行成功率
    - 收益分布
    - 风险分析
    """
    try:
        # 获取用户策略
        strategies = await personal_service.strategy_repo.get_user_strategies(current_user.id)

        # 计算统计数据
        total_strategies = len(strategies)
        active_strategies = len([s for s in strategies if s.is_active])

        # 按类型分组
        strategies_by_type = {}
        for strategy in strategies:
            type_name = strategy.strategy_type.value
            strategies_by_type[type_name] = strategies_by_type.get(type_name, 0) + 1

        # 按风险等级分组
        strategies_by_risk = {}
        for strategy in strategies:
            risk_level = strategy.risk_level.value
            strategies_by_risk[risk_level] = strategies_by_risk.get(risk_level, 0) + 1

        # 计算总收益
        total_return = 0.0
        total_pnl = 0.0
        for strategy in strategies:
            performance = await personal_service.strategy_repo.get_performance(strategy.id)
            if performance:
                total_return += performance.total_return
                total_pnl += performance.daily_pnl

        # 创建趋势数据（简化）
        creation_trend = []
        for i in range(30):
            date = datetime.now() - timedelta(days=i)
            count = len([s for s in strategies if s.created_at.date() == date.date()])
            creation_trend.append({
                "date": date.strftime("%Y-%m-%d"),
                "count": count
            })

        statistics = {
            "overview": {
                "total_strategies": total_strategies,
                "active_strategies": active_strategies,
                "total_return": total_return,
                "total_pnl": total_pnl,
                "success_rate": 0.85,  # 简化值
                "avg_return_per_strategy": total_return / total_strategies if total_strategies > 0 else 0
            },
            "strategies_by_type": strategies_by_type,
            "strategies_by_risk": strategies_by_risk,
            "creation_trend": creation_trend[::-1],  # 按时间正序
            "monthly_performance": [
                {"month": "2025-11", "return": 0.05},
                {"month": "2025-10", "return": 0.03},
                {"month": "2025-09", "return": -0.02}
            ]
        }

        return statistics

    except Exception as e:
        logger.error(f"获取用户统计失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取用户统计失败: {str(e)}"
        )