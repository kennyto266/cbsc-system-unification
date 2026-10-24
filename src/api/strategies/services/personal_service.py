"""
用户个性化服务
User Personalization Service

职责：
- 个人仪表板数据
- 用户偏好管理
- 策略推荐
- 操作历史跟踪
"""

from typing import List, Optional, Dict, Any
import logging
from datetime import datetime, timedelta
import json

from .strategy_service import BaseStrategyService
from ..repositories.strategy_repository import StrategyRepository
from ..repositories.user_repository import UserRepository
from ..utils.cache import CacheManager
from ..utils.validators import PersonalDataValidator
from ..models import (
    Strategy, StrategyPerformance, StrategySignal, StrategyExecution,
    User, StrategyType, RiskLevel, SignalType
)
from ..schemas import (
    DashboardResponse, UserPreferences, StrategyControlRequest,
    OperationHistoryResponse, StrategyRecommendations,
    RealTimeUpdate, StrategyResponse
)

logger = logging.getLogger(__name__)


class PersonalService(BaseStrategyService):
    """
    用户个性化服务
    继承BaseStrategyService，扩展个性化功能
    """

    def __init__(
        self,
        strategy_repo: StrategyRepository,
        user_repo: UserRepository,
        cache_manager: CacheManager,
        validator: PersonalDataValidator
    ):
        # 初始化基类
        from ..utils.validators import StrategyValidator
        strategy_validator = StrategyValidator()
        super().__init__(strategy_repo, user_repo, cache_manager, strategy_validator)

        self.validator = validator

    async def get_dashboard_data(self, user_id: int) -> DashboardResponse:
        """
        获取个人仪表板数据

        Args:
            user_id: 用户ID

        Returns:
            仪表板响应数据
        """
        # 尝试从缓存获取
        cache_key = f"dashboard:data:{user_id}"
        cached_data = await self.cache.get(cache_key)
        if cached_data:
            logger.debug(f"从缓存获取仪表板数据: {user_id}")
            return DashboardResponse(**cached_data)

        # 获取用户策略
        strategies = await self.strategy_repo.get_user_strategies(user_id)

        # 计算基础统计数据
        total_strategies = len(strategies)
        active_strategies = len([s for s in strategies if s.is_active])

        # 获取性能数据
        total_return = 0.0
        daily_pnl = 0.0
        best_performing = None
        worst_performing = None

        for strategy in strategies:
            performance = await self.strategy_repo.get_performance(strategy.id)
            if performance:
                total_return += performance.total_return
                daily_pnl += performance.daily_pnl

                # 转换为响应格式用于比较
                strategy_response = StrategyResponse.from_orm(strategy)
                strategy_response.performance_summary = {
                    "total_return": performance.total_return,
                    "daily_pnl": performance.daily_pnl
                }

                # 更新最佳/最差策略
                if best_performing is None or performance.total_return > best_performing.performance_summary["total_return"]:
                    best_performing = strategy_response
                if worst_performing is None or performance.total_return < worst_performing.performance_summary["total_return"]:
                    worst_performing = strategy_response

        # 获取最近信号
        recent_signals = await self._get_recent_user_signals(user_id, limit=10)

        # 获取市场概览
        market_overview = await self._get_market_overview()

        # 获取性能图表数据
        performance_chart = await self._get_performance_chart_data(user_id)

        result = DashboardResponse(
            total_strategies=total_strategies,
            active_strategies=active_strategies,
            total_return=total_return,
            daily_pnl=daily_pnl,
            best_performing=best_performing,
            worst_performing=worst_performing,
            recent_signals=recent_signals,
            market_overview=market_overview,
            performance_chart=performance_chart
        )

        # 缓存结果（较短缓存时间，因为需要实时数据）
        await self.cache.set(cache_key, result.dict(), ttl=60)  # 1分钟缓存

        return result

    async def get_user_preferences(self, user_id: int) -> UserPreferences:
        """
        获取用户偏好设置

        Args:
            user_id: 用户ID

        Returns:
            用户偏好设置
        """
        cache_key = f"preferences:{user_id}"

        # 尝试从缓存获取
        cached_preferences = await self.cache.get(cache_key)
        if cached_preferences:
            return UserPreferences(**cached_preferences)

        # 从数据库获取
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError(f"用户不存在: {user_id}")

        # 解析偏好设置
        preferences = UserPreferences(
            default_strategy_type=user.preferences.get("default_strategy_type") if user.preferences else None,
            risk_tolerance=RiskLevel(user.preferences.get("risk_tolerance", "medium")) if user.preferences else RiskLevel.MEDIUM,
            notification_settings=user.preferences.get("notification_settings", {}) if user.preferences else {},
            dashboard_layout=user.preferences.get("dashboard_layout", {}) if user.preferences else {},
            auto_refresh_interval=user.preferences.get("auto_refresh_interval", 30) if user.preferences else 30
        )

        # 缓存结果
        await self.cache.set(cache_key, preferences.dict(), ttl=3600)  # 1小时缓存

        return preferences

    async def update_user_preferences(
        self,
        user_id: int,
        preferences: UserPreferences
    ) -> UserPreferences:
        """
        更新用户偏好设置

        Args:
            user_id: 用户ID
            preferences: 新的偏好设置

        Returns:
            更新后的偏好设置
        """
        # 验证偏好设置
        await self.validator.validate_preferences(preferences)

        # 获取用户
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError(f"用户不存在: {user_id}")

        # 更新偏好设置
        user.preferences = preferences.dict()
        user = await self.user_repo.update(user)

        # 清除缓存
        cache_key = f"preferences:{user_id}"
        await self.cache.delete(cache_key)

        logger.info(f"更新用户偏好设置: {user_id}")

        return preferences

    async def control_strategy(
        self,
        user_id: int,
        strategy_id: str,
        request: StrategyControlRequest
    ) -> Dict[str, Any]:
        """
        控制策略

        Args:
            user_id: 用户ID
            strategy_id: 策略ID
            request: 控制请求

        Returns:
            控制结果
        """
        # 获取策略
        strategy = await self.strategy_repo.get_by_id(strategy_id)
        if not strategy:
            raise ValueError(f"策略不存在: {strategy_id}")

        # 权限检查
        if strategy.user_id != user_id:
            raise PermissionError(f"无权限控制策略: {strategy_id}")

        # 记录操作历史
        await self._record_operation(user_id, strategy_id, request.action, request.reason)

        # 执行控制操作
        previous_status = strategy.is_active
        success = False
        new_status = previous_status
        message = ""

        try:
            if request.action == "enable":
                strategy.is_active = True
                strategy.status = "active"
                new_status = True
                success = True
                message = "策略已启用"
            elif request.action == "disable":
                # 检查是否正在运行
                if await self.strategy_repo.is_running(strategy_id):
                    raise ValueError("无法禁用正在运行的策略")
                strategy.is_active = False
                strategy.status = "inactive"
                new_status = False
                success = True
                message = "策略已禁用"
            elif request.action == "start":
                # 这里应该调用执行服务启动策略
                success = True
                message = "策略执行已启动"
            elif request.action == "stop":
                # 这里应该调用执行服务停止策略
                success = True
                message = "策略执行已停止"
            elif request.action == "pause":
                # 暂停执行
                success = True
                message = "策略执行已暂停"
            else:
                raise ValueError(f"不支持的操作: {request.action}")

            # 保存更新
            if request.action in ["enable", "disable"]:
                strategy.updated_at = datetime.now()
                await self.strategy_repo.update(strategy)

            # 清除相关缓存
            await self._clear_user_strategy_cache(user_id)

        except Exception as e:
            message = f"操作失败: {str(e)}"
            logger.error(f"控制策略失败: {e}")

        return {
            "strategy_id": strategy_id,
            "success": success,
            "action": request.action,
            "previous_status": previous_status,
            "new_status": new_status,
            "message": message,
            "timestamp": datetime.now(),
            "requires_confirmation": False
        }

    async def get_strategy_history(
        self,
        user_id: int,
        strategy_id: str,
        limit: int = 50
    ) -> OperationHistoryResponse:
        """
        获取策略操作历史

        Args:
            user_id: 用户ID
            strategy_id: 策略ID
            limit: 返回数量限制

        Returns:
            操作历史响应
        """
        # 权限检查
        strategy = await self.strategy_repo.get_by_id(strategy_id)
        if not strategy or strategy.user_id != user_id:
            raise PermissionError(f"无权限查看策略历史: {strategy_id}")

        # 获取操作历史
        operations = await self._get_operation_history(user_id, strategy_id, limit)

        return OperationHistoryResponse(
            strategy_id=strategy_id,
            operations=operations,
            total_count=len(operations),
            has_more=len(operations) >= limit
        )

    async def get_strategy_recommendations(self, user_id: int) -> StrategyRecommendations:
        """
        获取策略推荐

        Args:
            user_id: 用户ID

        Returns:
            策略推荐
        """
        # 获取用户信息
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError(f"用户不存在: {user_id}")

        # 获取用户现有策略
        strategies = await self.strategy_repo.get_user_strategies(user_id)

        # 分析用户偏好
        preferences = await self.get_user_preferences(user_id)

        # 生成推荐
        recommendations = await self._generate_strategy_recommendations(user, strategies, preferences)

        return StrategyRecommendations(
            user_id=user_id,
            recommended_strategies=recommendations["strategies"],
            based_on=recommendations["based_on"],
            confidence_scores=recommendations["confidence_scores"],
            last_updated=datetime.now()
        )

    async def get_real_time_updates(self, user_id: int) -> RealTimeUpdate:
        """
        获取实时更新数据

        Args:
            user_id: 用户ID

        Returns:
            实时更新数据
        """
        # 获取用户策略的最新状态
        strategies = await self.strategy_repo.get_user_strategies(user_id)

        strategy_updates = []
        for strategy in strategies:
            # 获取最新信号
            latest_signal = await self.strategy_repo.get_latest_signal(strategy.id)
            performance = await self.strategy_repo.get_performance(strategy.id)

            update = {
                "strategy_id": strategy.id,
                "name": strategy.name,
                "status": strategy.status.value,
                "is_active": strategy.is_active,
                "last_signal": latest_signal.dict() if latest_signal else None,
                "performance": performance.dict() if performance else None
            }
            strategy_updates.append(update)

        # 获取市场数据
        market_data = await self._get_real_time_market_data()

        # 获取用户相关信号
        signals = await self._get_recent_user_signals(user_id, limit=20)

        # 生成告警
        alerts = await self._generate_user_alerts(user_id)

        return RealTimeUpdate(
            strategy_updates=strategy_updates,
            market_data=market_data,
            signals=signals,
            alerts=alerts
        )

    # 私有辅助方法
    async def _get_recent_user_signals(self, user_id: int, limit: int = 10) -> List[StrategySignal]:
        """获取用户最近的信号"""
        # 获取用户策略
        strategies = await self.strategy_repo.get_user_strategies(user_id)
        strategy_ids = [s.id for s in strategies]

        # 获取最近信号
        return await self.strategy_repo.get_recent_signals_by_strategies(strategy_ids, limit)

    async def _get_market_overview(self) -> Dict[str, Any]:
        """获取市场概览"""
        # 简化实现，实际应该调用市场数据服务
        return {
            "market_status": "open",
            "major_indices": {
                "S&P 500": {"value": 4500.0, "change": "+1.2%"},
                "NASDAQ": {"value": 14000.0, "change": "+0.8%"},
                "DOW": {"value": 35000.0, "change": "+0.5%"}
            },
            "market_sentiment": "bullish",
            "volatility_index": 18.5,
            "last_updated": datetime.now()
        }

    async def _get_performance_chart_data(self, user_id: int) -> List[Dict[str, Any]]:
        """获取性能图表数据"""
        # 获取过去30天的性能数据
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        # 简化实现
        chart_data = []
        current_date = start_date
        cumulative_return = 0.0

        while current_date <= end_date:
            # 模拟性能数据
            daily_return = 0.01 if current_date.day % 2 == 0 else -0.005
            cumulative_return += daily_return

            chart_data.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "value": cumulative_return,
                "daily_return": daily_return
            })

            current_date += timedelta(days=1)

        return chart_data

    async def _record_operation(
        self,
        user_id: int,
        strategy_id: str,
        action: str,
        reason: Optional[str] = None
    ) -> None:
        """记录操作历史"""
        operation = {
            "user_id": user_id,
            "strategy_id": strategy_id,
            "action": action,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        }

        # 这里应该保存到数据库
        # 暂时只记录日志
        logger.info(f"记录操作: {operation}")

    async def _get_operation_history(
        self,
        user_id: int,
        strategy_id: str,
        limit: int
    ) -> List[Dict[str, Any]]:
        """获取操作历史"""
        # 简化实现，实际应该从数据库获取
        return [
            {
                "action": "enable",
                "timestamp": datetime.now().isoformat(),
                "reason": "手动启用"
            },
            {
                "action": "execute",
                "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
                "reason": "定期执行"
            }
        ]

    async def _generate_strategy_recommendations(
        self,
        user: User,
        strategies: List[Strategy],
        preferences: UserPreferences
    ) -> Dict[str, Any]:
        """生成策略推荐"""
        # 分析用户现有策略类型
        existing_types = [s.strategy_type for s in strategies]

        # 推荐新策略类型
        all_types = list(StrategyType)
        recommended_types = [t for t in all_types if t not in existing_types]

        # 生成推荐策略
        recommended_strategies = []
        confidence_scores = {}

        for strategy_type in recommended_types[:3]:  # 推荐3个
            confidence = 0.8  # 简化计算
            recommended_strategies.append({
                "strategy_type": strategy_type.value,
                "name": f"推荐{strategy_type.value}策略",
                "description": f"基于您的偏好推荐的{strategy_type.value}策略",
                "expected_return": 0.15,
                "risk_level": preferences.risk_tolerance.value
            })
            confidence_scores[strategy_type.value] = confidence

        return {
            "strategies": recommended_strategies,
            "based_on": ["用户风险偏好", "现有策略类型", "市场趋势"],
            "confidence_scores": confidence_scores
        }

    async def _get_real_time_market_data(self) -> Dict[str, Any]:
        """获取实时市场数据"""
        return {
            "timestamp": datetime.now(),
            "pairs": {
                "EUR/USD": {"bid": 1.0850, "ask": 1.0852, "change": "+0.1%"},
                "GBP/USD": {"bid": 1.2650, "ask": 1.2653, "change": "-0.2%"},
                "USD/JPY": {"bid": 147.50, "ask": 147.52, "change": "+0.3%"}
            }
        }

    async def _generate_user_alerts(self, user_id: int) -> List[Dict[str, Any]]:
        """生成用户告警"""
        alerts = []
        strategies = await self.strategy_repo.get_user_strategies(user_id)

        for strategy in strategies:
            # 检查是否有新的重要信号
            latest_signal = await self.strategy_repo.get_latest_signal(strategy.id)
            if latest_signal and latest_signal.confidence > 0.8:
                alerts.append({
                    "alert_id": f"alert_{strategy.id}",
                    "strategy_id": strategy.id,
                    "strategy_name": strategy.name,
                    "type": "high_confidence_signal",
                    "message": f"策略 {strategy.name} 产生高置信度信号",
                    "severity": "high",
                    "timestamp": latest_signal.timestamp
                })

        return alerts