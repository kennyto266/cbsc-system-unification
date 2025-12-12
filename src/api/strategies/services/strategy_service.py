"""
策略业务服务
Strategy Business Service

职责：
- 策略业务逻辑
- 数据验证和转换
- 权限检查
- 缓存管理
"""

from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from ..repositories.strategy_repository import StrategyRepository
from ..repositories.user_repository import UserRepository
from ..utils.cache import CacheManager
from ..utils.validators import StrategyValidator
from ..models import (
    Strategy, StrategyType, StrategyStatus, StrategyTemplate,
    StrategyTemplates, DataCompatibilityAdapter
)
from ..schemas import StrategyCreate, StrategyUpdate, StrategyResponse

logger = logging.getLogger(__name__)


class BaseStrategyService:
    """
    基础策略服务类
    提供通用的CRUD操作，消除代码重复
    """

    def __init__(
        self,
        strategy_repo: StrategyRepository,
        user_repo: UserRepository,
        cache_manager: CacheManager,
        validator: StrategyValidator
    ):
        self.strategy_repo = strategy_repo
        self.user_repo = user_repo
        self.cache = cache_manager
        self.validator = validator

    async def list_strategies(
        self,
        page: int = 1,
        page_size: int = 20,
        strategy_type: Optional[str] = None,
        status: Optional[str] = None,
        user_id: Optional[int] = None,
        is_active: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        获取策略列表

        Args:
            page: 页码
            page_size: 每页大小
            strategy_type: 策略类型过滤
            status: 状态过滤
            user_id: 用户ID过滤
            is_active: 是否激活过滤

        Returns:
            策略列表响应
        """
        # 缓存键
        cache_key = f"strategies:list:{page}:{page_size}:{strategy_type}:{status}:{user_id}:{is_active}"

        # 尝试从缓存获取
        cached_result = await self.cache.get(cache_key)
        if cached_result:
            logger.debug(f"从缓存获取策略列表: {cache_key}")
            return cached_result

        # 构建过滤条件
        filters = {}
        if strategy_type:
            filters['strategy_type'] = strategy_type
        if status:
            filters['status'] = status
        if is_active is not None:
            filters['is_active'] = is_active

        # 从数据库获取
        strategies, total_count = await self.strategy_repo.list_strategies(
            page=page,
            page_size=page_size,
            filters=filters,
            user_id=user_id
        )

        # 计算总页数
        total_pages = (total_count + page_size - 1) // page_size

        result = {
            "strategies": [StrategyResponse.model_validate(s) for s in strategies],
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }

        # 缓存结果
        await self.cache.set(cache_key, result, ttl=300)  # 5分钟缓存

        return result

    async def create_strategy(self, request: StrategyCreate, user_id: int) -> StrategyResponse:
        """
        创建策略

        Args:
            request: 创建策略请求
            user_id: 用户ID

        Returns:
            创建的策略响应
        """
        # 验证请求
        await self.validator.validate_create_request(request)

        # 检查名称唯一性（在同一用户下）
        if await self.strategy_repo.name_exists(request.name, user_id):
            raise ValueError(f"策略名称已存在: {request.name}")

        # 获取模板参数（如果指定了模板）
        parameters = request.parameters.copy()
        if request.template_id:
            template = StrategyTemplates.get_template(request.template_id)
            if template:
                # 合并模板默认参数
                parameters = {**template.default_parameters, **parameters}

        # 生成策略ID - 使用微秒精度避免重複
        import time
        strategy_id = f"{request.strategy_type.value}_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{int(time.time() * 1000000) % 1000000}"

        # 创建策略对象
        strategy = Strategy(
            id=strategy_id,
            name=request.name.strip(),
            description=request.description.strip(),
            strategy_type=request.strategy_type,
            parameters=parameters,
            user_id=user_id,
            status=StrategyStatus.INACTIVE,
            is_active=False,
            risk_level=request.risk_level
        )

        # 保存到数据库
        strategy = await self.strategy_repo.create(strategy)

        # 清除相关缓存
        await self._clear_user_strategy_cache(user_id)

        logger.info(f"创建策略成功: {strategy.id} by user {user_id}")

        return StrategyResponse.model_validate(strategy)

    async def get_strategy_detail(self, strategy_id: str, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        获取策略详情

        Args:
            strategy_id: 策略ID
            user_id: 用户ID（用于权限检查）

        Returns:
            策略详情响应
        """
        # 缓存键
        cache_key = f"strategy:detail:{strategy_id}:{user_id}"

        # 尝试从缓存获取
        cached_result = await self.cache.get(cache_key)
        if cached_result:
            logger.debug(f"从缓存获取策略详情: {cache_key}")
            return cached_result

        # 从数据库获取
        strategy = await self.strategy_repo.get_by_id(strategy_id)
        if not strategy:
            raise ValueError(f"策略不存在: {strategy_id}")

        # 权限检查
        if user_id and strategy.user_id != user_id:
            user = await self.user_repo.get_by_id(user_id)
            if not user or not user.is_admin:
                raise PermissionError(f"无权限访问策略: {strategy_id}")

        # 获取相关信息
        recent_signals = await self.strategy_repo.get_recent_signals(strategy_id, limit=10)
        performance = await self.strategy_repo.get_performance(strategy_id)
        execution_history = await self.strategy_repo.get_execution_history(strategy_id, limit=5)

        # 转换为响应格式
        strategy_response = StrategyResponse.model_validate(strategy)
        if performance:
            strategy_response.performance_summary = {
                "total_return": performance.total_return,
                "sharpe_ratio": performance.sharpe_ratio,
                "win_rate": performance.win_rate,
                "max_drawdown": performance.max_drawdown
            }

        result = {
            "strategy": strategy_response,
            "recent_signals": recent_signals,
            "performance": performance,
            "execution_history": execution_history
        }

        # 缓存结果
        await self.cache.set(cache_key, result, ttl=600)  # 10分钟缓存

        return result

    async def update_strategy(
        self,
        strategy_id: str,
        request: StrategyUpdate,
        user_id: Optional[int] = None
    ) -> StrategyResponse:
        """
        更新策略

        Args:
            strategy_id: 策略ID
            request: 更新请求
            user_id: 用户ID

        Returns:
            更新后的策略响应
        """
        # 获取现有策略
        strategy = await self.strategy_repo.get_by_id(strategy_id)
        if not strategy:
            raise ValueError(f"策略不存在: {strategy_id}")

        # 权限检查
        if user_id and strategy.user_id != user_id:
            user = await self.user_repo.get_by_id(user_id)
            if not user or not user.is_admin:
                raise PermissionError(f"无权限修改策略: {strategy_id}")

        # 验证更新请求
        await self.validator.validate_update_request(request, strategy)

        # 检查名称唯一性（如果更新了名称）
        if request.name and request.name.strip() != strategy.name:
            if await self.strategy_repo.name_exists(request.name.strip(), strategy.user_id):
                raise ValueError(f"策略名称已存在: {request.name}")

        # 更新字段
        update_data = request.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == 'name':
                setattr(strategy, field, value.strip())
            elif field == 'description':
                setattr(strategy, field, value.strip())
            else:
                setattr(strategy, field, value)

        # 更新时间戳
        strategy.updated_at = datetime.now()

        # 保存更新
        strategy = await self.strategy_repo.update(strategy)

        # 清除相关缓存
        await self._clear_strategy_cache(strategy_id)
        await self._clear_user_strategy_cache(strategy.user_id)

        logger.info(f"更新策略成功: {strategy_id}")

        return StrategyResponse.model_validate(strategy)

    async def delete_strategy(self, strategy_id: str, user_id: Optional[int] = None) -> None:
        """
        删除策略

        Args:
            strategy_id: 策略ID
            user_id: 用户ID
        """
        # 获取策略信息
        strategy = await self.strategy_repo.get_by_id(strategy_id)
        if not strategy:
            raise ValueError(f"策略不存在: {strategy_id}")

        # 权限检查
        if user_id and strategy.user_id != user_id:
            user = await self.user_repo.get_by_id(user_id)
            if not user or not user.is_admin:
                raise PermissionError(f"无权限删除策略: {strategy_id}")

        # 检查是否正在运行
        if await self.strategy_repo.is_running(strategy_id):
            raise ValueError("无法删除正在运行的策略")

        # 删除策略及相关数据
        await self.strategy_repo.delete(strategy_id)

        # 清除相关缓存
        await self._clear_strategy_cache(strategy_id)
        await self._clear_user_strategy_cache(strategy.user_id)

        logger.info(f"删除策略成功: {strategy_id}")

    async def batch_operation(
        self,
        strategy_ids: List[str],
        operation: str,
        user_id: Optional[int] = None,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        批量操作策略

        Args:
            strategy_ids: 策略ID列表
            operation: 操作类型
            user_id: 用户ID
            parameters: 操作参数

        Returns:
            批量操作结果
        """
        results = {
            "success": [],
            "failed": [],
            "total": len(strategy_ids)
        }

        for strategy_id in strategy_ids:
            try:
                if operation == "activate":
                    await self._activate_strategy(strategy_id, user_id)
                elif operation == "deactivate":
                    await self._deactivate_strategy(strategy_id, user_id)
                elif operation == "delete":
                    await self.delete_strategy(strategy_id, user_id)
                else:
                    raise ValueError(f"不支持的操作: {operation}")

                results["success"].append(strategy_id)
            except Exception as e:
                results["failed"].append({
                    "strategy_id": strategy_id,
                    "error": str(e)
                })

        # 清除相关缓存
        if user_id:
            await self._clear_user_strategy_cache(user_id)

        return results

    async def get_templates(self, strategy_type: Optional[StrategyType] = None) -> List[StrategyTemplate]:
        """
        获取策略模板

        Args:
            strategy_type: 策略类型过滤

        Returns:
            策略模板列表
        """
        cache_key = f"templates:list:{strategy_type}"

        # 尝试从缓存获取
        cached_result = await self.cache.get(cache_key)
        if cached_result:
            return cached_result

        # 获取模板
        if strategy_type:
            templates = StrategyTemplates.get_templates_by_type(strategy_type)
        else:
            templates = StrategyTemplates.get_all_templates()

        # 缓存结果
        await self.cache.set(cache_key, templates, ttl=3600)  # 1小时缓存

        return templates

    # 私有辅助方法
    async def _activate_strategy(self, strategy_id: str, user_id: Optional[int] = None) -> None:
        """激活策略"""
        strategy = await self.strategy_repo.get_by_id(strategy_id)
        if not strategy:
            raise ValueError(f"策略不存在: {strategy_id}")

        # 权限检查
        if user_id and strategy.user_id != user_id:
            raise PermissionError(f"无权限激活策略: {strategy_id}")

        strategy.is_active = True
        strategy.status = StrategyStatus.ACTIVE
        strategy.updated_at = datetime.now()
        await self.strategy_repo.update(strategy)

    async def _deactivate_strategy(self, strategy_id: str, user_id: Optional[int] = None) -> None:
        """停用策略"""
        strategy = await self.strategy_repo.get_by_id(strategy_id)
        if not strategy:
            raise ValueError(f"策略不存在: {strategy_id}")

        # 权限检查
        if user_id and strategy.user_id != user_id:
            raise PermissionError(f"无权限停用策略: {strategy_id}")

        # 检查是否正在运行
        if await self.strategy_repo.is_running(strategy_id):
            raise ValueError("无法停用正在运行的策略")

        strategy.is_active = False
        strategy.status = StrategyStatus.INACTIVE
        strategy.updated_at = datetime.now()
        await self.strategy_repo.update(strategy)

    async def _clear_strategy_cache(self, strategy_id: str) -> None:
        """清除策略相关缓存"""
        patterns = [
            f"strategy:detail:{strategy_id}:*",
            f"strategy:performance:{strategy_id}",
            f"strategy:signals:{strategy_id}"
        ]
        for pattern in patterns:
            await self.cache.delete_pattern(pattern)

    async def _clear_user_strategy_cache(self, user_id: int) -> None:
        """清除用户策略相关缓存"""
        pattern = f"strategies:list:*:*:*:*:{user_id}:*"
        await self.cache.delete_pattern(pattern)