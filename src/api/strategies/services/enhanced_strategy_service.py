"""
增强策略业务服务
Enhanced Strategy Business Service

职责：
- 基于BaseStrategyService的增强版本
- 支持实时更新（WebSocket）
- 高性能批量操作
- 优化的缓存策略
- 完整的错误处理和日志记录
- 支持前端所需的高级功能
"""

from typing import List, Optional, Dict, Any, Union, Callable, AsyncIterator
import logging
from datetime import datetime, timedelta
import asyncio
import json
import time
from dataclasses import dataclass
from enum import Enum

from ..repositories.strategy_repository import StrategyRepository
from ..repositories.user_repository import UserRepository
from ..utils.cache import CacheManager
from ..utils.validators import StrategyValidator
from ..utils.response import APIError, NotFoundError, PermissionError, InternalError
from ..utils.errors import BusinessError, ErrorCode, ErrorLogger, error_reporter
from ..models import (
    Strategy, StrategyType, StrategyStatus, StrategyTemplate,
    StrategyTemplates, DataCompatibilityAdapter
)
from ..schemas import StrategyCreate, StrategyUpdate, StrategyResponse
from .websocket_service import WebSocketService
from .base_business_service import BaseBusinessService

logger = logging.getLogger(__name__)


class BatchOperationType(str, Enum):
    """批量操作类型"""
    ACTIVATE = "activate"
    DEACTIVATE = "deactivate"
    DELETE = "delete"
    UPDATE = "update"
    EXECUTE = "execute"
    STOP = "stop"


@dataclass
class BatchOperationConfig:
    """批量操作配置"""
    batch_size: int = 50  # 批次大小
    max_retries: int = 3  # 最大重试次数
    timeout_per_item: float = 5.0  # 每项超时时间（秒）
    continue_on_error: bool = True  # 出错时是否继续
    progress_callback: Optional[Callable] = None  # 进度回调


@dataclass
class BatchOperationResult:
    """批量操作结果"""
    operation: BatchOperationType
    total: int
    successful: List[str]
    failed: List[Dict[str, Any]]
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    progress: float = 0.0

    def __post_init__(self):
        if self.end_time and self.start_time:
            self.duration = (self.end_time - self.start_time).total_seconds()
        if self.total > 0:
            self.progress = len(self.successful) / self.total


class EnhancedStrategyService(BaseBusinessService):
    """
    增强策略服务类
    提供高性能的策略管理功能，支持批量操作和实时更新
    """

    def __init__(
        self,
        strategy_repo: StrategyRepository,
        user_repo: UserRepository,
        cache_manager: CacheManager,
        validator: StrategyValidator,
        websocket_service: Optional[WebSocketService] = None
    ):
        super().__init__(strategy_repo, user_repo, cache_manager, validator)
        self.websocket_service = websocket_service
        self._active_batches: Dict[str, BatchOperationResult] = {}
        self._lock = asyncio.Lock()

    # ========================================
    # 增强的CRUD操作
    # ========================================

    async def create_strategy_with_validation(
        self,
        request: StrategyCreate,
        user_id: int,
        validate_permissions: bool = True,
        notify_realtime: bool = True
    ) -> StrategyResponse:
        """
        创建策略（增强版）

        Args:
            request: 创建策略请求
            user_id: 用户ID
            validate_permissions: 是否验证权限
            notify_realtime: 是否发送实时通知

        Returns:
            创建的策略响应
        """
        try:
            # 增强验证
            await self._validate_create_request_enhanced(request, user_id, validate_permissions)

            # 检查并发创建
            if await self._check_concurrent_creation(request.name, user_id):
                raise BusinessError(
                    "策略正在创建中，请稍后重试",
                    ErrorCode.CONFLICT,
                    details={"strategy_name": request.name}
                )

            # 生成唯一ID
            strategy_id = await self._generate_unique_strategy_id(request.strategy_type, user_id)

            # 获取模板参数
            parameters = await self._resolve_template_parameters(request)

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
                risk_level=request.risk_level,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

            # 保存到数据库
            strategy = await self.strategy_repo.create_with_transaction(strategy)

            # 优化缓存
            await self._update_cache_after_create(strategy, user_id)

            # 发送实时通知
            if notify_realtime and self.websocket_service:
                await self._notify_strategy_created(strategy)

            # 记录审计日志
            await self._log_strategy_operation("create", strategy_id, user_id)

            logger.info(f"策略创建成功: {strategy_id} by user {user_id}")
            return StrategyResponse.model_validate(strategy)

        except Exception as e:
            ErrorLogger.log_business_error(
                BusinessError(
                    f"创建策略失败: {str(e)}",
                    ErrorCode.STRATEGY_EXECUTION_FAILED,
                    cause=e
                ),
                user_id=user_id
            )
            raise

    async def update_strategy_with_optimistic_lock(
        self,
        strategy_id: str,
        request: StrategyUpdate,
        user_id: Optional[int] = None,
        expected_version: Optional[int] = None
    ) -> StrategyResponse:
        """
        更新策略（支持乐观锁）

        Args:
            strategy_id: 策略ID
            request: 更新请求
            user_id: 用户ID
            expected_version: 期望的版本号

        Returns:
            更新后的策略响应
        """
        try:
            # 获取当前策略（带锁）
            strategy = await self.strategy_repo.get_by_id_with_lock(strategy_id)
            if not strategy:
                raise NotFoundError("策略", strategy_id)

            # 版本检查
            if expected_version is not None and strategy.version != expected_version:
                raise BusinessError(
                    "策略已被其他用户修改，请刷新后重试",
                    ErrorCode.CONFLICT,
                    details={
                        "current_version": strategy.version,
                        "expected_version": expected_version
                    }
                )

            # 权限检查
            await self._check_strategy_permission(strategy, user_id, "update")

            # 验证更新请求
            await self.validator.validate_update_request(request, strategy)

            # 检查名称唯一性
            if request.name and request.name.strip() != strategy.name:
                if await self.strategy_repo.name_exists(request.name.strip(), strategy.user_id):
                    raise BusinessError(
                        f"策略名称已存在: {request.name}",
                        ErrorCode.STRATEGY_ALREADY_EXISTS
                    )

            # 备份原始数据
            original_data = strategy.model_copy()

            # 更新字段
            update_data = request.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                if field in ['name', 'description']:
                    setattr(strategy, field, value.strip())
                else:
                    setattr(strategy, field, value)

            # 更新时间和版本
            strategy.updated_at = datetime.now()
            strategy.version = (strategy.version or 0) + 1

            # 保存更新
            strategy = await self.strategy_repo.update_with_version(strategy)

            # 清除缓存
            await self._clear_strategy_cache_enhanced(strategy_id, strategy.user_id)

            # 发送实时通知
            if self.websocket_service:
                await self._notify_strategy_updated(strategy, original_data)

            # 记录审计日志
            await self._log_strategy_operation(
                "update",
                strategy_id,
                user_id,
                changes=self._calculate_changes(original_data, strategy)
            )

            logger.info(f"策略更新成功: {strategy_id}")
            return StrategyResponse.model_validate(strategy)

        except Exception as e:
            ErrorLogger.log_business_error(
                BusinessError(
                    f"更新策略失败: {str(e)}",
                    ErrorCode.STRATEGY_EXECUTION_FAILED,
                    cause=e,
                    strategy_id=strategy_id
                ),
                user_id=user_id
            )
            raise

    # ========================================
    # 高性能批量操作
    # ========================================

    async def batch_operation_enhanced(
        self,
        strategy_ids: List[str],
        operation: Union[BatchOperationType, str],
        user_id: Optional[int] = None,
        parameters: Optional[Dict[str, Any]] = None,
        config: Optional[BatchOperationConfig] = None
    ) -> BatchOperationResult:
        """
        增强批量操作

        Args:
            strategy_ids: 策略ID列表
            operation: 操作类型
            user_id: 用户ID
            parameters: 操作参数
            config: 批量操作配置

        Returns:
            批量操作结果
        """
        # 转换操作类型
        if isinstance(operation, str):
            try:
                operation = BatchOperationType(operation)
            except ValueError:
                raise BusinessError(
                    f"不支持的操作类型: {operation}",
                    ErrorCode.STRATEGY_INVALID_STATUS
                )

        # 使用默认配置
        config = config or BatchOperationConfig()

        # 创建批量操作结果
        result = BatchOperationResult(
            operation=operation,
            total=len(strategy_ids),
            successful=[],
            failed=[],
            start_time=datetime.now()
        )

        # 分批处理
        batch_size = config.batch_size
        for i in range(0, len(strategy_ids), batch_size):
            batch = strategy_ids[i:i + batch_size]

            # 并发处理当前批次
            await self._process_strategy_batch(
                batch,
                operation,
                user_id,
                parameters,
                config,
                result
            )

            # 更新进度
            if config.progress_callback:
                await config.progress_callback(result.progress, len(result.successful), len(result.failed))

            # 短暂休息避免过载
            await asyncio.sleep(0.1)

        # 完成操作
        result.end_time = datetime.now()

        # 清除相关缓存
        if user_id and result.successful:
            await self._clear_user_cache_batch(user_id, result.successful)

        # 发送批量操作通知
        if self.websocket_service:
            await self._notify_batch_operation_completed(result)

        # 记录审计日志
        await self._log_batch_operation(result, user_id)

        logger.info(f"批量操作完成: {operation.value} - 成功: {len(result.successful)}, 失败: {len(result.failed)}")
        return result

    async def _process_strategy_batch(
        self,
        batch: List[str],
        operation: BatchOperationType,
        user_id: Optional[int],
        parameters: Optional[Dict[str, Any]],
        config: BatchOperationConfig,
        result: BatchOperationResult
    ):
        """处理策略批次"""
        async def process_single_strategy(strategy_id: str) -> Optional[str]:
            """处理单个策略"""
            try:
                # 设置超时
                async with asyncio.timeout(config.timeout_per_item):
                    if operation == BatchOperationType.ACTIVATE:
                        await self._activate_strategy_with_checks(strategy_id, user_id)
                    elif operation == BatchOperationType.DEACTIVATE:
                        await self._deactivate_strategy_with_checks(strategy_id, user_id)
                    elif operation == BatchOperationType.DELETE:
                        await self.delete_strategy_with_dependencies(strategy_id, user_id)
                    elif operation == BatchOperationType.UPDATE:
                        if parameters:
                            await self.update_strategy_with_optimistic_lock(
                                strategy_id,
                                StrategyUpdate(**parameters),
                                user_id
                            )
                    elif operation == BatchOperationType.EXECUTE:
                        # 这里需要执行服务的支持
                        pass
                    elif operation == BatchOperationType.STOP:
                        # 停止策略执行
                        pass

                    return strategy_id

            except Exception as e:
                error_info = {
                    "strategy_id": strategy_id,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
                result.failed.append(error_info)

                # 如果不继续执行错误，抛出异常
                if not config.continue_on_error:
                    raise

                # 记录错误
                ErrorLogger.log_error(e, {"strategy_id": strategy_id}, user_id)

                return None

        # 并发处理批次
        tasks = [process_single_strategy(sid) for sid in batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 收集成功的结果
        for strategy_id in results:
            if strategy_id and isinstance(strategy_id, str):
                result.successful.append(strategy_id)

    # ========================================
    # 实时更新支持
    # ========================================

    async def get_real_time_strategy_updates(
        self,
        user_id: int,
        strategy_ids: Optional[List[str]] = None,
        last_update: Optional[datetime] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        获取策略实时更新

        Args:
            user_id: 用户ID
            strategy_ids: 策略ID列表（可选）
            last_update: 上次更新时间（可选）

        Yields:
            实时更新数据
        """
        # 构建过滤条件
        filters = {"user_id": user_id}
        if strategy_ids:
            filters["strategy_ids"] = strategy_ids

        # 持续监听更新
        while True:
            try:
                # 获取最新更新
                updates = await self._get_strategy_updates(filters, last_update)

                if updates:
                    last_update = datetime.now()
                    yield {
                        "type": "strategy_updates",
                        "timestamp": last_update.isoformat(),
                        "data": updates
                    }

                # 等待下次检查
                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"获取实时更新失败: {e}")
                await asyncio.sleep(5)

    async def subscribe_to_strategy_events(
        self,
        user_id: int,
        websocket,
        strategy_ids: Optional[List[str]] = None
    ):
        """
        订阅策略事件（WebSocket）

        Args:
            user_id: 用户ID
            websocket: WebSocket连接
            strategy_ids: 策略ID列表
        """
        if not self.websocket_service:
            raise BusinessError(
                "WebSocket服务未启用",
                ErrorCode.WEBSOCKET_CONNECTION_FAILED
            )

        # 注册订阅
        subscription_id = await self.websocket_service.subscribe(
            websocket,
            channel="strategy_events",
            filters={"user_id": user_id, "strategy_ids": strategy_ids}
        )

        try:
            # 保持连接活跃
            while True:
                await asyncio.sleep(30)
                # 发送心跳
                await websocket.send_json({"type": "heartbeat"})

        except Exception as e:
            logger.error(f"WebSocket订阅错误: {e}")
        finally:
            # 取消订阅
            await self.websocket_service.unsubscribe(subscription_id)

    # ========================================
    # 增强的查询功能
    # ========================================

    async def search_strategies_advanced(
        self,
        query: str,
        user_id: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: Optional[str] = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        高级策略搜索

        Args:
            query: 搜索关键词
            user_id: 用户ID
            filters: 过滤条件
            sort_by: 排序字段
            sort_order: 排序方向
            page: 页码
            page_size: 每页大小

        Returns:
            搜索结果
        """
        try:
            # 构建搜索条件
            search_conditions = {
                "query": query,
                "filters": filters or {},
                "user_id": user_id,
                "sort_by": sort_by,
                "sort_order": sort_order
            }

            # 检查缓存
            cache_key = f"strategy_search:{hash(json.dumps(search_conditions, sort_keys=True))}"
            cached_result = await self.cache.get(cache_key)
            if cached_result:
                return cached_result

            # 执行搜索
            strategies, total_count = await self.strategy_repo.search_advanced(
                query=query,
                filters=filters,
                user_id=user_id,
                sort_by=sort_by,
                sort_order=sort_order,
                page=page,
                page_size=page_size
            )

            # 计算总页数
            total_pages = (total_count + page_size - 1) // page_size

            result = {
                "strategies": [StrategyResponse.model_validate(s) for s in strategies],
                "total_count": total_count,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "query": query,
                "filters": filters
            }

            # 缓存结果
            await self.cache.set(cache_key, result, ttl=600)  # 10分钟缓存

            return result

        except Exception as e:
            logger.error(f"策略搜索失败: {e}")
            raise BusinessError(
                f"搜索失败: {str(e)}",
                ErrorCode.INTERNAL_SERVER_ERROR,
                cause=e
            )

    async def get_strategy_analytics(
        self,
        strategy_id: str,
        user_id: Optional[int] = None,
        time_range: int = 30
    ) -> Dict[str, Any]:
        """
        获取策略分析数据

        Args:
            strategy_id: 策略ID
            user_id: 用户ID
            time_range: 时间范围（天）

        Returns:
            分析数据
        """
        try:
            # 验证策略存在和权限
            strategy = await self._validate_strategy_access(strategy_id, user_id)

            # 获取分析数据
            analytics = await self.strategy_repo.get_analytics(
                strategy_id,
                time_range=time_range
            )

            # 添加实时数据
            if self.websocket_service:
                analytics["real_time"] = await self._get_real_time_analytics(strategy_id)

            return analytics

        except Exception as e:
            logger.error(f"获取策略分析失败: {e}")
            raise BusinessError(
                f"获取分析数据失败: {str(e)}",
                ErrorCode.INTERNAL_SERVER_ERROR,
                cause=e
            )

    # ========================================
    # 私有辅助方法
    # ========================================

    async def _validate_create_request_enhanced(
        self,
        request: StrategyCreate,
        user_id: int,
        validate_permissions: bool
    ):
        """增强的创建请求验证"""
        # 基础验证
        await self.validator.validate_create_request(request)

        # 权限验证
        if validate_permissions:
            await self._check_user_permissions(user_id, "create_strategy")

        # 风险级别验证
        await self._validate_risk_level(request.risk_level, user_id)

        # 参数合规性检查
        await self._validate_parameters_compliance(request.parameters, request.strategy_type)

    async def _check_concurrent_creation(self, name: str, user_id: int) -> bool:
        """检查并发创建"""
        lock_key = f"strategy_creation:{user_id}:{name}"
        return await self.cache.exists(lock_key)

    async def _generate_unique_strategy_id(
        self,
        strategy_type: StrategyType,
        user_id: int
    ) -> str:
        """生成唯一策略ID"""
        import uuid
        timestamp = int(time.time() * 1000)
        unique_id = str(uuid.uuid4())[:8]
        return f"{strategy_type.value}_{user_id}_{timestamp}_{unique_id}"

    async def _resolve_template_parameters(
        self,
        request: StrategyCreate
    ) -> Dict[str, Any]:
        """解析模板参数"""
        parameters = request.parameters.copy()

        if request.template_id:
            template = StrategyTemplates.get_template(request.template_id)
            if template:
                # 验证参数兼容性
                await self._validate_template_compatibility(parameters, template)
                # 合并默认参数
                parameters = {**template.default_parameters, **parameters}

        return parameters

    async def _validate_template_compatibility(
        self,
        parameters: Dict[str, Any],
        template: StrategyTemplate
    ):
        """验证模板兼容性"""
        adapter = DataCompatibilityAdapter()
        if not adapter.is_compatible(parameters, template.required_parameters):
            raise BusinessError(
                "参数与模板不兼容",
                ErrorCode.STRATEGY_TYPE_MISMATCH,
                details={
                    "template_id": template.id,
                    "required_parameters": template.required_parameters
                }
            )

    async def _update_cache_after_create(self, strategy: Strategy, user_id: int):
        """创建后更新缓存"""
        # 预热相关缓存
        cache_keys = [
            f"strategy:detail:{strategy.id}",
            f"strategies:list:1:20:*:*:{user_id}:*",
            f"strategies:count:{user_id}"
        ]

        for key in cache_keys:
            await self.cache.delete_pattern(key)

    async def _notify_strategy_created(self, strategy: Strategy):
        """通知策略创建"""
        if self.websocket_service:
            await self.websocket_service.broadcast(
                channel="strategy_events",
                message={
                    "type": "strategy_created",
                    "strategy": StrategyResponse.model_validate(strategy).dict(),
                    "timestamp": datetime.now().isoformat()
                }
            )

    async def _notify_strategy_updated(
        self,
        strategy: Strategy,
        original_data: Strategy
    ):
        """通知策略更新"""
        if self.websocket_service:
            await self.websocket_service.broadcast(
                channel="strategy_events",
                message={
                    "type": "strategy_updated",
                    "strategy": StrategyResponse.model_validate(strategy).dict(),
                    "changes": self._calculate_changes(original_data, strategy),
                    "timestamp": datetime.now().isoformat()
                }
            )

    async def _calculate_changes(
        self,
        original: Strategy,
        updated: Strategy
    ) -> Dict[str, Any]:
        """计算变更"""
        changes = {}
        for field in original.__fields__:
            old_value = getattr(original, field)
            new_value = getattr(updated, field)
            if old_value != new_value:
                changes[field] = {
                    "old": old_value,
                    "new": new_value
                }
        return changes

    async def _log_strategy_operation(
        self,
        operation: str,
        strategy_id: str,
        user_id: Optional[int],
        changes: Optional[Dict[str, Any]] = None
    ):
        """记录策略操作日志"""
        # 这里可以集成审计服务
        logger.info(f"策略操作日志: {operation} - {strategy_id} by {user_id}")

    async def _clear_strategy_cache_enhanced(
        self,
        strategy_id: str,
        user_id: int
    ):
        """增强的缓存清理"""
        patterns = [
            f"strategy:detail:{strategy_id}:*",
            f"strategy:performance:{strategy_id}",
            f"strategy:signals:{strategy_id}",
            f"strategies:list:*:*:*:*:{user_id}:*",
            f"strategy_search:*"
        ]

        for pattern in patterns:
            await self.cache.delete_pattern(pattern)

    async def _clear_user_cache_batch(
        self,
        user_id: int,
        strategy_ids: List[str]
    ):
        """批量清理用户缓存"""
        # 清除用户相关缓存
        await self.cache.delete_pattern(f"strategies:list:*:*:*:*:{user_id}:*")

        # 清除特定策略缓存
        for strategy_id in strategy_ids:
            await self._clear_strategy_cache_enhanced(strategy_id, user_id)

    async def _notify_batch_operation_completed(
        self,
        result: BatchOperationResult
    ):
        """通知批量操作完成"""
        if self.websocket_service:
            await self.websocket_service.broadcast(
                channel="strategy_events",
                message={
                    "type": "batch_operation_completed",
                    "result": {
                        "operation": result.operation.value,
                        "total": result.total,
                        "successful": len(result.successful),
                        "failed": len(result.failed),
                        "duration": result.duration
                    },
                    "timestamp": datetime.now().isoformat()
                }
            )

    async def _log_batch_operation(
        self,
        result: BatchOperationResult,
        user_id: Optional[int]
    ):
        """记录批量操作日志"""
        logger.info(f"批量操作: {result.operation.value} - 用户: {user_id} - "
                   f"成功: {len(result.successful)}, 失败: {len(result.failed)}")

    # 其他私有方法...
    async def _check_strategy_permission(
        self,
        strategy: Strategy,
        user_id: Optional[int],
        action: str
    ):
        """检查策略权限"""
        if user_id and strategy.user_id != user_id:
            user = await self.user_repo.get_by_id(user_id)
            if not user or not user.is_admin:
                raise PermissionError(f"无权限{action}策略")

    async def _activate_strategy_with_checks(
        self,
        strategy_id: str,
        user_id: Optional[int]
    ):
        """带检查的激活策略"""
        strategy = await self.strategy_repo.get_by_id(strategy_id)
        if not strategy:
            raise NotFoundError("策略", strategy_id)

        await self._check_strategy_permission(strategy, user_id, "activate")

        if strategy.is_active:
            raise BusinessError(
                "策略已激活",
                ErrorCode.STRATEGY_INVALID_STATUS
            )

        strategy.is_active = True
        strategy.status = StrategyStatus.ACTIVE
        strategy.updated_at = datetime.now()
        await self.strategy_repo.update(strategy)

    async def _deactivate_strategy_with_checks(
        self,
        strategy_id: str,
        user_id: Optional[int]
    ):
        """带检查的停用策略"""
        strategy = await self.strategy_repo.get_by_id(strategy_id)
        if not strategy:
            raise NotFoundError("策略", strategy_id)

        await self._check_strategy_permission(strategy, user_id, "deactivate")

        if await self.strategy_repo.is_running(strategy_id):
            raise BusinessError(
                "无法停用正在运行的策略",
                ErrorCode.STRATEGY_ALREADY_RUNNING
            )

        strategy.is_active = False
        strategy.status = StrategyStatus.INACTIVE
        strategy.updated_at = datetime.now()
        await self.strategy_repo.update(strategy)

    async def delete_strategy_with_dependencies(
        self,
        strategy_id: str,
        user_id: Optional[int]
    ):
        """删除策略及依赖"""
        strategy = await self.strategy_repo.get_by_id(strategy_id)
        if not strategy:
            raise NotFoundError("策略", strategy_id)

        await self._check_strategy_permission(strategy, user_id, "delete")

        if await self.strategy_repo.is_running(strategy_id):
            raise BusinessError(
                "无法删除正在运行的策略",
                ErrorCode.STRATEGY_CANNOT_DELETE
            )

        # 删除策略及相关数据
        await self.strategy_repo.delete_with_dependencies(strategy_id)

    async def _validate_strategy_access(
        self,
        strategy_id: str,
        user_id: Optional[int]
    ) -> Strategy:
        """验证策略访问权限"""
        strategy = await self.strategy_repo.get_by_id(strategy_id)
        if not strategy:
            raise NotFoundError("策略", strategy_id)

        await self._check_strategy_permission(strategy, user_id, "access")

        return strategy

    async def _get_real_time_analytics(self, strategy_id: str) -> Dict[str, Any]:
        """获取实时分析数据"""
        # 从WebSocket服务获取实时数据
        if self.websocket_service:
            return await self.websocket_service.get_strategy_metrics(strategy_id)
        return {}

    async def _get_strategy_updates(
        self,
        filters: Dict[str, Any],
        last_update: Optional[datetime]
    ) -> List[Dict[str, Any]]:
        """获取策略更新"""
        # 从数据库或缓存获取更新
        return await self.strategy_repo.get_updates(filters, last_update)

    async def _check_user_permissions(self, user_id: int, permission: str):
        """检查用户权限"""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("用户", str(user_id))

        # 这里可以集成权限服务
        # if not await self.permission_service.check_permission(user_id, permission):
        #     raise PermissionError(f"无权限执行: {permission}")

    async def _validate_risk_level(self, risk_level: str, user_id: int):
        """验证风险级别"""
        # 检查用户是否允许设置该风险级别
        user = await self.user_repo.get_by_id(user_id)
        if user and not user.can_access_risk_level(risk_level):
            raise PermissionError(f"无权限设置风险级别: {risk_level}")

    async def _validate_parameters_compliance(
        self,
        parameters: Dict[str, Any],
        strategy_type: StrategyType
    ):
        """验证参数合规性"""
        # 检查参数是否符合策略类型要求
        validator = self.validator.get_parameter_validator(strategy_type)
        if validator:
            await validator.validate(parameters)