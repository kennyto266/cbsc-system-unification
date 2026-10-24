"""
个人策略管理API端点
Personal Strategy Management API Endpoints

Task #002: API接口集成和數據獲取
提供完整的个人策略管理REST API接口，包括策略CRUD、实时数据、性能分析等功能
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
import asyncio
from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi import status
from pydantic import BaseModel

# 导入现有的策略管理模块
from .strategy_management_api import (
    Strategy, StrategySignal, StrategyPerformance, StrategyType,
    SignalType, StrategyStatus, RiskLevel, StrategyExecutionRequest,
    StrategyExecutionResult, CreateStrategyRequest, UpdateStrategyRequest,
    StrategyListResponse, StrategyDetailResponse, BatchStrategyOperation,
    StrategyOptimizationRequest, StrategyOptimizationResult,
    CBSCStrategyTemplate, StrategyTemplates, DataCompatibilityAdapter
)

# 导入认证模块
from auth_simple import User

logger = logging.getLogger(__name__)

# 创建API路由器
router = APIRouter(prefix="/api/personal-strategies", tags=["个人策略管理"])

# ============================================================================
# 数据模型 (Data Models)
# ============================================================================

class PersonalStrategySummary(BaseModel):
    """个人策略摘要"""
    strategy_id: str
    name: str
    strategy_type: StrategyType
    status: StrategyStatus
    is_active: bool
    current_return: float
    daily_pnl: float
    risk_level: str
    last_updated: datetime
    created_at: datetime

class StrategyMetricsResponse(BaseModel):
    """策略指标响应"""
    strategy_id: str
    performance: StrategyPerformance
    recent_signals: List[StrategySignal]
    execution_history: List[StrategyExecutionResult]
    risk_metrics: Dict[str, float]
    market_conditions: Dict[str, Any]

class PersonalDashboardData(BaseModel):
    """个人仪表板数据"""
    total_strategies: int
    active_strategies: int
    total_return: float
    daily_pnl: float
    best_performing: PersonalStrategySummary
    worst_performing: PersonalStrategySummary
    recent_signals: List[StrategySignal]
    market_overview: Dict[str, Any]

class RealTimeDataUpdate(BaseModel):
    """实时数据更新"""
    timestamp: datetime
    strategy_updates: List[PersonalStrategySummary]
    market_data: Dict[str, Any]
    signals: List[StrategySignal]
    alerts: List[Dict[str, Any]]

class StrategyAlert(BaseModel):
    """策略告警"""
    alert_id: str
    strategy_id: str
    alert_type: str
    severity: str
    message: str
    timestamp: datetime
    is_read: bool

class UserPreferences(BaseModel):
    """用户偏好设置"""
    default_strategy_type: Optional[StrategyType] = None
    risk_tolerance: str = "medium"
    notification_settings: Dict[str, bool]
    dashboard_layout: Dict[str, Any]
    auto_refresh_interval: int = 30

# ============================================================================
# 全局状态管理 (Global State Management)
# ============================================================================

class PersonalStrategyManager:
    """个人策略管理器"""

    def __init__(self):
        self.user_strategies: Dict[int, Dict[str, Strategy]] = {}  # user_id -> strategies
        self.user_performances: Dict[int, Dict[str, StrategyPerformance]] = {}
        self.user_signals: Dict[int, List[StrategySignal]] = {}
        self.user_alerts: Dict[int, List[StrategyAlert]] = {}
        self.user_preferences: Dict[int, UserPreferences] = {}
        self.websocket_connections: Dict[int, List[WebSocket]] = {}

    async def get_user_strategies(self, user_id: int) -> Dict[str, Strategy]:
        """获取用户的策略"""
        if user_id not in self.user_strategies:
            self.user_strategies[user_id] = {}
        return self.user_strategies[user_id]

    async def add_strategy_to_user(self, user_id: int, strategy: Strategy):
        """为用户添加策略"""
        if user_id not in self.user_strategies:
            self.user_strategies[user_id] = {}
        self.user_strategies[user_id][strategy.id] = strategy

        # 添加初始性能数据
        if user_id not in self.user_performances:
            self.user_performances[user_id] = {}

        performance = StrategyPerformance(
            strategy_type=strategy.strategy_type,
            total_return=0.0,
            annual_return=0.0,
            sharpe_ratio=0.0,
            max_drawdown=0.0,
            win_rate=0.0,
            profit_factor=0.0,
            calmar_ratio=0.0,
            total_trades=0,
            profit_trades=0,
            avg_profit=0.0,
            avg_loss=0.0,
            last_updated=datetime.now()
        )
        self.user_performances[user_id][strategy.id] = performance

    async def remove_user_strategy(self, user_id: int, strategy_id: str):
        """删除用户策略"""
        if user_id in self.user_strategies and strategy_id in self.user_strategies[user_id]:
            del self.user_strategies[user_id][strategy_id]
        if user_id in self.user_performances and strategy_id in self.user_performances[user_id]:
            del self.user_performances[user_id][strategy_id]

    async def get_user_dashboard_data(self, user_id: int) -> PersonalDashboardData:
        """获取用户仪表板数据"""
        strategies = await self.get_user_strategies(user_id)
        performances = self.user_performances.get(user_id, {})
        signals = self.user_signals.get(user_id, [])

        # 计算汇总数据
        total_strategies = len(strategies)
        active_strategies = sum(1 for s in strategies.values() if s.is_active)
        total_return = sum(p.total_return for p in performances.values())
        daily_pnl = sum(p.daily_pnl for p in performances.values() if hasattr(p, 'daily_pnl'))

        # 找出最佳和最差表现策略
        strategy_summaries = []
        for strategy_id, strategy in strategies.items():
            performance = performances.get(strategy_id)
            if performance:
                summary = PersonalStrategySummary(
                    strategy_id=strategy_id,
                    name=strategy.name,
                    strategy_type=strategy.strategy_type,
                    status=strategy.status,
                    is_active=strategy.is_active,
                    current_return=performance.total_return,
                    daily_pnl=getattr(performance, 'daily_pnl', 0.0),
                    risk_level=getattr(strategy, 'risk_level', 'medium'),
                    last_updated=performance.last_updated,
                    created_at=strategy.created_at
                )
                strategy_summaries.append(summary)

        # 排序找出最佳和最差
        best_performing = max(strategy_summaries, key=lambda x: x.current_return) if strategy_summaries else None
        worst_performing = min(strategy_summaries, key=lambda x: x.current_return) if strategy_summaries else None

        # 获取最近的信号
        recent_signals = sorted(signals, key=lambda x: x.timestamp, reverse=True)[:10]

        # 模拟市场概览
        market_overview = {
            "market_status": "open",
            "index_change": 0.025,
            "volatility_index": 18.5,
            "sector_performance": {
                "technology": 0.032,
                "finance": 0.018,
                "healthcare": 0.012,
                "energy": -0.008
            }
        }

        return PersonalDashboardData(
            total_strategies=total_strategies,
            active_strategies=active_strategies,
            total_return=total_return,
            daily_pnl=daily_pnl,
            best_performing=best_performing,
            worst_performing=worst_performing,
            recent_signals=recent_signals,
            market_overview=market_overview
        )

# 全局个人策略管理器实例
personal_strategy_manager = PersonalStrategyManager()

# ============================================================================
# 依赖注入 (Dependency Injection)
# ============================================================================

def get_current_user():
    """获取当前用户"""
    from auth_simple import auth_service
    return auth_service.get_current_user

async def get_personal_strategy_manager() -> PersonalStrategyManager:
    """获取个人策略管理器实例"""
    return personal_strategy_manager

# ============================================================================
# 个人策略管理API (Personal Strategy Management API)
# ============================================================================

@router.get("/dashboard", response_model=PersonalDashboardData)
async def get_personal_dashboard(
    current_user: User = Depends(get_current_user()),
    manager: PersonalStrategyManager = Depends(get_personal_strategy_manager)
):
    """
    获取个人策略仪表板数据

    - **current_user**: 当前登录用户
    """
    try:
        dashboard_data = await manager.get_user_dashboard_data(current_user.id)
        return dashboard_data

    except Exception as e:
        logger.error(f"获取个人仪表板数据失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取仪表板数据失败: {str(e)}"
        )

@router.get("/strategies", response_model=StrategyListResponse)
async def get_personal_strategies(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    strategy_type: Optional[StrategyType] = Query(None, description="策略类型过滤"),
    status: Optional[StrategyStatus] = Query(None, description="状态过滤"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    current_user: User = Depends(get_current_user()),
    manager: PersonalStrategyManager = Depends(get_personal_strategy_manager)
) -> StrategyListResponse:
    """
    获取个人策略列表

    - **page**: 页码，从1开始
    - **page_size**: 每页大小，最大100
    - **strategy_type**: 策略类型过滤
    - **status**: 状态过滤
    - **is_active**: 是否激活过滤
    """
    try:
        # 获取用户策略
        user_strategies = await manager.get_user_strategies(current_user.id)
        strategies = list(user_strategies.values())

        # 应用过滤条件
        if strategy_type:
            strategies = [s for s in strategies if s.strategy_type == strategy_type]

        if status:
            strategies = [s for s in strategies if s.status == status]

        if is_active is not None:
            strategies = [s for s in strategies if s.is_active == is_active]

        # 分页
        total_count = len(strategies)
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        paginated_strategies = strategies[start_index:end_index]

        return StrategyListResponse(
            strategies=paginated_strategies,
            total_count=total_count,
            page=page,
            page_size=page_size
        )

    except Exception as e:
        logger.error(f"获取个人策略列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取策略列表失败: {str(e)}"
        )

@router.post("/strategies", response_model=Strategy, status_code=status.HTTP_201_CREATED)
async def create_personal_strategy(
    request: CreateStrategyRequest,
    current_user: User = Depends(get_current_user()),
    manager: PersonalStrategyManager = Depends(get_personal_strategy_manager)
) -> Strategy:
    """
    创建新的个人策略

    - **name**: 策略名称 (1-100字符)
    - **description**: 策略描述 (1-500字符)
    - **strategy_type**: 策略类型
    - **parameters**: 策略参数
    - **template_id**: 可选，基于模板创建
    """
    try:
        # 获取用户现有策略
        user_strategies = await manager.get_user_strategies(current_user.id)

        # 验证策略名称唯一性
        for strategy in user_strategies.values():
            if strategy.name == request.name:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"策略名称已存在: {request.name}"
                )

        # 生成策略ID
        strategy_id = f"personal_{current_user.id}_{request.strategy_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 创建策略
        strategy = Strategy(
            id=strategy_id,
            name=request.name,
            description=request.description,
            strategy_type=request.strategy_type,
            parameters=request.parameters,
            is_active=False  # 新创建的策略默认不激活
        )

        # 添加到用户策略
        await manager.add_strategy_to_user(current_user.id, strategy)

        logger.info(f"用户 {current_user.id} 创建策略成功: {strategy_id} - {strategy.name}")
        return strategy

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建个人策略失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建策略失败: {str(e)}"
        )

@router.get("/strategies/{strategy_id}", response_model=StrategyDetailResponse)
async def get_personal_strategy_detail(
    strategy_id: str,
    current_user: User = Depends(get_current_user()),
    manager: PersonalStrategyManager = Depends(get_personal_strategy_manager)
) -> StrategyDetailResponse:
    """
    获取个人策略详情

    - **strategy_id**: 策略ID
    """
    try:
        # 获取用户策略
        user_strategies = await manager.get_user_strategies(current_user.id)

        if strategy_id not in user_strategies:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"策略不存在: {strategy_id}"
            )

        strategy = user_strategies[strategy_id]

        # 获取性能数据
        performances = manager.user_performances.get(current_user.id, {})
        performance = performances.get(strategy_id)

        # 获取最近的信号
        user_signals = manager.user_signals.get(current_user.id, [])
        recent_signals = [
            signal for signal in user_signals[-50:]
            if hasattr(signal, 'strategy_type') and signal.strategy_type == strategy.strategy_type
        ]

        return StrategyDetailResponse(
            strategy=strategy,
            recent_signals=recent_signals,
            performance=performance,
            execution_history=[]  # 暂时为空
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取个人策略详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取策略详情失败: {str(e)}"
        )

@router.put("/strategies/{strategy_id}", response_model=Strategy)
async def update_personal_strategy(
    strategy_id: str,
    request: UpdateStrategyRequest,
    current_user: User = Depends(get_current_user()),
    manager: PersonalStrategyManager = Depends(get_personal_strategy_manager)
) -> Strategy:
    """
    更新个人策略

    - **strategy_id**: 策略ID
    - **name**: 可选，策略名称
    - **description**: 可选，策略描述
    - **parameters**: 可选，策略参数
    - **status**: 可选，策略状态
    - **is_active**: 可选，是否激活
    """
    try:
        # 获取用户策略
        user_strategies = await manager.get_user_strategies(current_user.id)

        if strategy_id not in user_strategies:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"策略不存在: {strategy_id}"
            )

        strategy = user_strategies[strategy_id]

        # 更新策略字段
        if request.name is not None:
            strategy.name = request.name

        if request.description is not None:
            strategy.description = request.description

        if request.parameters is not None:
            strategy.parameters = request.parameters

        if request.status is not None:
            strategy.status = request.status

        if request.is_active is not None:
            strategy.is_active = request.is_active

        strategy.updated_at = datetime.now()

        logger.info(f"用户 {current_user.id} 更新策略成功: {strategy_id}")
        return strategy

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新个人策略失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新策略失败: {str(e)}"
        )

@router.delete("/strategies/{strategy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_personal_strategy(
    strategy_id: str,
    current_user: User = Depends(get_current_user()),
    manager: PersonalStrategyManager = Depends(get_personal_strategy_manager)
):
    """
    删除个人策略

    - **strategy_id**: 策略ID
    """
    try:
        # 获取用户策略
        user_strategies = await manager.get_user_strategies(current_user.id)

        if strategy_id not in user_strategies:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"策略不存在: {strategy_id}"
            )

        # 删除策略
        await manager.remove_user_strategy(current_user.id, strategy_id)

        logger.info(f"用户 {current_user.id} 删除策略成功: {strategy_id}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除个人策略失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除策略失败: {str(e)}"
        )

# ============================================================================
# 策略性能和分析API (Strategy Performance & Analytics API)
# ============================================================================

@router.get("/strategies/{strategy_id}/metrics", response_model=StrategyMetricsResponse)
async def get_strategy_metrics(
    strategy_id: str,
    time_range: int = Query(30, ge=1, le=365, description="时间范围（天）"),
    current_user: User = Depends(get_current_user()),
    manager: PersonalStrategyManager = Depends(get_personal_strategy_manager)
) -> StrategyMetricsResponse:
    """
    获取策略性能指标

    - **strategy_id**: 策略ID
    - **time_range**: 时间范围（天）
    """
    try:
        # 获取用户策略
        user_strategies = await manager.get_user_strategies(current_user.id)

        if strategy_id not in user_strategies:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"策略不存在: {strategy_id}"
            )

        strategy = user_strategies[strategy_id]

        # 获取性能数据
        performances = manager.user_performances.get(current_user.id, {})
        performance = performances.get(strategy_id)

        if not performance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"策略性能数据不存在: {strategy_id}"
            )

        # 获取最近的信号
        user_signals = manager.user_signals.get(current_user.id, [])
        recent_signals = [
            signal for signal in user_signals[-100:]
            if hasattr(signal, 'strategy_type') and signal.strategy_type == strategy.strategy_type
        ]

        # 计算风险指标
        risk_metrics = {
            "var_95": abs(performance.max_drawdown) * 1.5,
            "volatility": 0.15,
            "beta": 1.1,
            "correlation_to_market": 0.75,
            "tracking_error": 0.08
        }

        # 模拟市场条件
        market_conditions = {
            "market_regime": "bull",
            "volatility_regime": "normal",
            "sector_trend": "positive",
            "liquidity_conditions": "good"
        }

        return StrategyMetricsResponse(
            strategy_id=strategy_id,
            performance=performance,
            recent_signals=recent_signals,
            execution_history=[],  # 暂时为空
            risk_metrics=risk_metrics,
            market_conditions=market_conditions
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取策略性能指标失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取性能指标失败: {str(e)}"
        )

# ============================================================================
# 实时数据WebSocket (Real-time Data WebSocket)
# ============================================================================

@router.websocket("/ws/{user_id}")
async def websocket_realtime_data(
    websocket: WebSocket,
    user_id: int,
    manager: PersonalStrategyManager = Depends(get_personal_strategy_manager)
):
    """WebSocket实时数据推送"""
    await websocket.accept()

    # 添加到连接池
    if user_id not in manager.websocket_connections:
        manager.websocket_connections[user_id] = []
    manager.websocket_connections[user_id].append(websocket)

    logger.info(f"用户 {user_id} WebSocket连接已建立")

    try:
        # 发送初始数据
        dashboard_data = await manager.get_user_dashboard_data(user_id)
        await websocket.send_json({
            "type": "dashboard_update",
            "data": dashboard_data.dict()
        })

        # 保持连接并定期发送更新
        while True:
            await asyncio.sleep(10)  # 每10秒更新一次

            # 模拟实时数据更新
            update_data = RealTimeDataUpdate(
                timestamp=datetime.now(),
                strategy_updates=[],  # 这里可以添加策略更新
                market_data={
                    "market_status": "open",
                    "last_update": datetime.now().isoformat(),
                    "indices": {
                        "hsi": {"value": 18500, "change": 0.025},
                        "hsi_futures": {"value": 18600, "change": 0.028}
                    }
                },
                signals=[],  # 这里可以添加新信号
                alerts=[]  # 这里可以添加告警
            )

            await websocket.send_json({
                "type": "realtime_update",
                "data": update_data.dict()
            })

    except WebSocketDisconnect:
        logger.info(f"用户 {user_id} WebSocket连接已断开")
    except Exception as e:
        logger.error(f"WebSocket连接错误: {e}")
    finally:
        # 从连接池中移除
        if user_id in manager.websocket_connections:
            if websocket in manager.websocket_connections[user_id]:
                manager.websocket_connections[user_id].remove(websocket)

# ============================================================================
# 用户偏好设置API (User Preferences API)
# ============================================================================

@router.get("/preferences", response_model=UserPreferences)
async def get_user_preferences(
    current_user: User = Depends(get_current_user()),
    manager: PersonalStrategyManager = Depends(get_personal_strategy_manager)
):
    """获取用户偏好设置"""
    try:
        preferences = manager.user_preferences.get(current_user.id)

        if not preferences:
            # 创建默认偏好设置
            preferences = UserPreferences(
                risk_tolerance="medium",
                notification_settings={
                    "email_notifications": True,
                    "browser_notifications": True,
                    "strategy_alerts": True,
                    "performance_reports": False
                },
                dashboard_layout={
                    "layout": "grid",
                    "widgets": ["performance", "signals", "positions", "risk"]
                },
                auto_refresh_interval=30
            )
            manager.user_preferences[current_user.id] = preferences

        return preferences

    except Exception as e:
        logger.error(f"获取用户偏好设置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取偏好设置失败: {str(e)}"
        )

@router.put("/preferences")
async def update_user_preferences(
    preferences: UserPreferences,
    current_user: User = Depends(get_current_user()),
    manager: PersonalStrategyManager = Depends(get_personal_strategy_manager)
):
    """更新用户偏好设置"""
    try:
        manager.user_preferences[current_user.id] = preferences
        return {"message": "用户偏好设置更新成功"}

    except Exception as e:
        logger.error(f"更新用户偏好设置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新偏好设置失败: {str(e)}"
        )

# ============================================================================
# 策略控制API (Strategy Control API)
# ============================================================================

class StrategyControlRequest(BaseModel):
    """策略控制请求"""
    action: str  # 'enable', 'disable', 'start', 'stop', 'pause'
    reason: Optional[str] = None
    confirm: bool = False

class BatchStrategyControlRequest(BaseModel):
    """批量策略控制请求"""
    strategy_ids: List[str]
    action: str  # 'enable', 'disable', 'start', 'stop', 'pause'
    reason: Optional[str] = None
    confirm: bool = False

class StrategyControlResult(BaseModel):
    """策略控制结果"""
    strategy_id: str
    success: bool
    action: str
    previous_status: bool
    new_status: bool
    message: str
    timestamp: datetime
    requires_confirmation: bool = False

class BatchStrategyControlResult(BaseModel):
    """批量策略控制结果"""
    total_count: int
    success_count: int
    failure_count: int
    results: List[StrategyControlResult]
    batch_id: str
    timestamp: datetime

class StrategyOperationLog(BaseModel):
    """策略操作日志"""
    log_id: str
    user_id: int
    strategy_id: str
    action: str
    previous_status: Optional[bool]
    new_status: Optional[bool]
    reason: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    timestamp: datetime
    success: bool
    error_message: Optional[str] = None

@router.post("/strategies/{strategy_id}/control", response_model=StrategyControlResult)
async def control_strategy(
    strategy_id: str,
    request: StrategyControlRequest,
    current_user: User = Depends(get_current_user()),
    manager: PersonalStrategyManager = Depends(get_personal_strategy_manager)
) -> StrategyControlResult:
    """
    控制单个策略的启用/禁用状态

    - **strategy_id**: 策略ID
    - **action**: 操作类型 ('enable', 'disable', 'start', 'stop', 'pause')
    - **reason**: 可选，操作原因
    - **confirm**: 是否确认操作（用于危险操作）
    """
    try:
        # 获取用户策略
        user_strategies = await manager.get_user_strategies(current_user.id)

        if strategy_id not in user_strategies:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"策略不存在: {strategy_id}"
            )

        strategy = user_strategies[strategy_id]
        previous_status = strategy.is_active

        # 验证操作
        valid_actions = ['enable', 'disable', 'start', 'stop', 'pause']
        if request.action not in valid_actions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的操作类型: {request.action}. 支持的操作: {valid_actions}"
            )

        # 安全检查 - 某些操作需要确认
        dangerous_actions = ['stop', 'disable']
        if request.action in dangerous_actions and not request.confirm:
            return StrategyControlResult(
                strategy_id=strategy_id,
                success=False,
                action=request.action,
                previous_status=previous_status,
                new_status=previous_status,
                message=f"操作 '{request.action}' 需要确认。请设置 confirm=true。",
                timestamp=datetime.now(),
                requires_confirmation=True
            )

        # 执行操作
        new_status = previous_status
        action_performed = request.action

        if request.action in ['enable', 'start']:
            new_status = True
            strategy.is_active = True
            strategy.status = StrategyStatus.ACTIVE
        elif request.action in ['disable', 'stop', 'pause']:
            new_status = False
            strategy.is_active = False
            if request.action in ['stop', 'pause']:
                strategy.status = StrategyStatus.PAUSED if request.action == 'pause' else StrategyStatus.INACTIVE

        # 更新时间戳
        strategy.updated_at = datetime.now()

        # 记录操作日志
        log_entry = StrategyOperationLog(
            log_id=f"log_{current_user.id}_{strategy_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            user_id=current_user.id,
            strategy_id=strategy_id,
            action=request.action,
            previous_status=previous_status,
            new_status=new_status,
            reason=request.reason,
            timestamp=datetime.now(),
            success=True
        )

        # 添加到日志（实际应用中应该持久化到数据库）
        if not hasattr(manager, 'operation_logs'):
            manager.operation_logs = {}
        if current_user.id not in manager.operation_logs:
            manager.operation_logs[current_user.id] = []
        manager.operation_logs[current_user.id].append(log_entry)

        # 通过WebSocket推送状态更新
        await _broadcast_strategy_update(manager, current_user.id, {
            "type": "strategy_status_changed",
            "strategy_id": strategy_id,
            "action": request.action,
            "previous_status": previous_status,
            "new_status": new_status,
            "timestamp": datetime.now().isoformat()
        })

        logger.info(f"用户 {current_user.id} 成功执行策略操作: {strategy_id} - {request.action}")

        return StrategyControlResult(
            strategy_id=strategy_id,
            success=True,
            action=request.action,
            previous_status=previous_status,
            new_status=new_status,
            message=f"策略 '{strategy.name}' 已成功{action_performed}" +
                   (f"。原因: {request.reason}" if request.reason else ""),
            timestamp=datetime.now()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"控制策略失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"控制策略失败: {str(e)}"
        )

@router.post("/strategies/batch-control", response_model=BatchStrategyControlResult)
async def batch_control_strategies(
    request: BatchStrategyControlRequest,
    current_user: User = Depends(get_current_user()),
    manager: PersonalStrategyManager = Depends(get_personal_strategy_manager)
) -> BatchStrategyControlResult:
    """
    批量控制策略状态

    - **strategy_ids**: 策略ID列表
    - **action**: 操作类型 ('enable', 'disable', 'start', 'stop', 'pause')
    - **reason**: 可选，操作原因
    - **confirm**: 是否确认操作
    """
    try:
        # 验证请求
        if not request.strategy_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="策略ID列表不能为空"
            )

        if len(request.strategy_ids) > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="批量操作最多支持100个策略"
            )

        # 生成批次ID
        batch_id = f"batch_{current_user.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        results = []
        success_count = 0
        failure_count = 0

        # 获取用户策略
        user_strategies = await manager.get_user_strategies(current_user.id)

        # 批量处理每个策略
        for strategy_id in request.strategy_ids:
            try:
                if strategy_id not in user_strategies:
                    results.append(StrategyControlResult(
                        strategy_id=strategy_id,
                        success=False,
                        action=request.action,
                        previous_status=None,
                        new_status=None,
                        message=f"策略不存在: {strategy_id}",
                        timestamp=datetime.now()
                    ))
                    failure_count += 1
                    continue

                strategy = user_strategies[strategy_id]
                previous_status = strategy.is_active

                # 执行操作
                new_status = previous_status
                if request.action in ['enable', 'start']:
                    new_status = True
                    strategy.is_active = True
                    strategy.status = StrategyStatus.ACTIVE
                elif request.action in ['disable', 'stop', 'pause']:
                    new_status = False
                    strategy.is_active = False
                    if request.action == 'pause':
                        strategy.status = StrategyStatus.PAUSED
                    else:
                        strategy.status = StrategyStatus.INACTIVE

                strategy.updated_at = datetime.now()

                # 记录操作日志
                log_entry = StrategyOperationLog(
                    log_id=f"log_{current_user.id}_{strategy_id}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
                    user_id=current_user.id,
                    strategy_id=strategy_id,
                    action=f"batch_{request.action}",
                    previous_status=previous_status,
                    new_status=new_status,
                    reason=request.reason,
                    timestamp=datetime.now(),
                    success=True
                )

                if not hasattr(manager, 'operation_logs'):
                    manager.operation_logs = {}
                if current_user.id not in manager.operation_logs:
                    manager.operation_logs[current_user.id] = []
                manager.operation_logs[current_user.id].append(log_entry)

                results.append(StrategyControlResult(
                    strategy_id=strategy_id,
                    success=True,
                    action=request.action,
                    previous_status=previous_status,
                    new_status=new_status,
                    message=f"策略 '{strategy.name}' 已成功{request.action}",
                    timestamp=datetime.now()
                ))
                success_count += 1

            except Exception as e:
                results.append(StrategyControlResult(
                    strategy_id=strategy_id,
                    success=False,
                    action=request.action,
                    previous_status=None,
                    new_status=None,
                    message=f"操作失败: {str(e)}",
                    timestamp=datetime.now()
                ))
                failure_count += 1

        # 批量广播更新
        await _broadcast_strategy_update(manager, current_user.id, {
            "type": "batch_strategy_status_changed",
            "batch_id": batch_id,
            "action": request.action,
            "success_count": success_count,
            "failure_count": failure_count,
            "timestamp": datetime.now().isoformat()
        })

        logger.info(f"用户 {current_user.id} 批量操作完成: {request.action} - 成功 {success_count}/{len(request.strategy_ids)}")

        return BatchStrategyControlResult(
            total_count=len(request.strategy_ids),
            success_count=success_count,
            failure_count=failure_count,
            results=results,
            batch_id=batch_id,
            timestamp=datetime.now()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量控制策略失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量控制策略失败: {str(e)}"
        )

@router.get("/strategies/{strategy_id}/operation-history")
async def get_strategy_operation_history(
    strategy_id: str,
    limit: int = Query(50, ge=1, le=200, description="返回记录数限制"),
    current_user: User = Depends(get_current_user()),
    manager: PersonalStrategyManager = Depends(get_personal_strategy_manager)
):
    """
    获取策略操作历史

    - **strategy_id**: 策略ID
    - **limit**: 返回记录数限制
    """
    try:
        # 验证策略存在
        user_strategies = await manager.get_user_strategies(current_user.id)
        if strategy_id not in user_strategies:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"策略不存在: {strategy_id}"
            )

        # 获取操作日志
        logs = []
        if hasattr(manager, 'operation_logs') and current_user.id in manager.operation_logs:
            user_logs = manager.operation_logs[current_user.id]
            # 过滤该策略的日志
            strategy_logs = [log for log in user_logs if log.strategy_id == strategy_id]
            # 按时间倒序排列
            strategy_logs.sort(key=lambda x: x.timestamp, reverse=True)
            # 应用限制
            logs = strategy_logs[:limit]

        return {
            "strategy_id": strategy_id,
            "total_logs": len(logs),
            "logs": [
                {
                    "log_id": log.log_id,
                    "action": log.action,
                    "previous_status": log.previous_status,
                    "new_status": log.new_status,
                    "reason": log.reason,
                    "timestamp": log.timestamp,
                    "success": log.success,
                    "error_message": log.error_message
                }
                for log in logs
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取策略操作历史失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取操作历史失败: {str(e)}"
        )

# ============================================================================
# 辅助函数 (Helper Functions)
# ============================================================================

async def _broadcast_strategy_update(manager: PersonalStrategyManager, user_id: int, update_data: dict):
    """通过WebSocket广播策略更新"""
    if user_id in manager.websocket_connections:
        disconnected = []
        for websocket in manager.websocket_connections[user_id]:
            try:
                await websocket.send_json(update_data)
            except Exception as e:
                logger.error(f"WebSocket发送更新失败: {e}")
                disconnected.append(websocket)

        # 清理断开的连接
        for ws in disconnected:
            manager.websocket_connections[user_id].remove(ws)

# ============================================================================
# 导出的函数和类 (Exports)
# ============================================================================

__all__ = [
    "router",
    "PersonalStrategyManager",
    "PersonalStrategySummary",
    "StrategyMetricsResponse",
    "PersonalDashboardData",
    "RealTimeDataUpdate",
    "StrategyAlert",
    "UserPreferences",
    "StrategyControlRequest",
    "BatchStrategyControlRequest",
    "StrategyControlResult",
    "BatchStrategyControlResult",
    "StrategyOperationLog"
]