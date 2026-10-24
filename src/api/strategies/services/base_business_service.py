"""
統一業務服務基類
Base Business Service

基於BaseStrategyService的成功實踐，創建通用業務服務基類，
提供標準化的CRUD操作、權限管理、緓存支持等功能。

職責：
- 通用CRUD操作模式
- 統一的權限檢查機制
- 標準化的緩存管理
- 批量操作支持
- 事件通知機制
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Type, TypeVar, Generic
import logging
from datetime import datetime
from pydantic import BaseModel

from ..utils.cache import CacheManager
from ..utils.validators import BaseValidator
from ..utils.permissions import PermissionChecker
from ..utils.events import EventBus

logger = logging.getLogger(__name__)

# Generic type for models and schemas
ModelType = TypeVar('ModelType')
CreateType = TypeVar('CreateType', bound=BaseModel)
UpdateType = TypeVar('UpdateType', bound=BaseModel)
ResponseType = TypeVar('ResponseType', bound=BaseModel)


class BaseBusinessService(Generic[ModelType, CreateType, UpdateType, ResponseType], ABC):
    """
    統一業務服務基類

    提供標準化的業務服務操作模式，包括：
    - CRUD操作
    - 權限控制
    - 緩存管理
    - 批量處理
    - 事件觸發
    """

    def __init__(
        self,
        repository,  # Repository實例
        cache_manager: CacheManager,
        validator: BaseValidator,
        permission_checker: PermissionChecker,
        event_bus: EventBus,
        cache_prefix: str,
        default_ttl: int = 300
    ):
        """
        初始化業務服務

        Args:
            repository: 數據訪問層實例
            cache_manager: 緩存管理器
            validator: 數據驗證器
            permission_checker: 權限檢查器
            event_bus: 事件總線
            cache_prefix: 緩存鍵前綴
            default_ttl: 默認緩存TTL（秒）
        """
        self.repo = repository
        self.cache = cache_manager
        self.validator = validator
        self.permission = permission_checker
        self.events = event_bus
        self.cache_prefix = cache_prefix
        self.default_ttl = default_ttl

    async def list_items(
        self,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None,
        include_deleted: bool = False
    ) -> Dict[str, Any]:
        """
        獲取項目列表

        Args:
            page: 頁碼
            page_size: 每頁大小
            filters: 過濾條件
            user_id: 用戶ID（用於權限和緩存）
            include_deleted: 是否包含已刪除項目

        Returns:
            分頁列表響應
        """
        # 構建緩存鍵
        cache_key = self._build_cache_key(
            "list", page=page, page_size=page_size,
            filters=filters, user_id=user_id, include_deleted=include_deleted
        )

        # 嘗試從緩存獲取
        cached_result = await self.cache.get(cache_key)
        if cached_result:
            logger.debug(f"從緩存獲取列表: {cache_key}")
            return cached_result

        # 權限檢查 - 列表查看權限
        if user_id:
            await self.permission.check_list_permission(user_id)

        # 從數據庫獲取
        items, total_count = await self.repo.list_items(
            page=page,
            page_size=page_size,
            filters=filters or {},
            user_id=user_id,
            include_deleted=include_deleted
        )

        # 計算總頁數
        total_pages = (total_count + page_size - 1) // page_size

        # 轉換為響應格式
        response_schema = self.get_response_schema()
        result = {
            "items": [response_schema.model_validate(item) for item in items],
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }

        # 緩存結果
        await self.cache.set(cache_key, result, ttl=self.default_ttl)

        # 觸發事件
        await self.events.emit("items_listed", {
            "service": self.__class__.__name__,
            "user_id": user_id,
            "count": len(items)
        })

        return result

    async def create_item(self, request: CreateType, user_id: int) -> ResponseType:
        """
        創建新項目

        Args:
            request: 創建請求數據
            user_id: 用戶ID

        Returns:
            創建的項目響應
        """
        # 驗證請求
        await self.validator.validate_create_request(request)

        # 權限檢查
        await self.permission.check_create_permission(user_id, request.dict())

        # 檢查唯一性約束（如果有）
        await self._check_unique_constraints(request, user_id)

        # 創建模型實例
        model_class = self.get_model_class()
        item_data = request.model_dump()
        item_data.update(self._get_create_metadata(user_id))
        item = model_class(**item_data)

        # 保存到數據庫
        item = await self.repo.create(item)

        # 清除相關緩存
        await self._clear_list_cache(user_id)

        # 轉換為響應格式
        response_schema = self.get_response_schema()
        response = response_schema.model_validate(item)

        # 觸發事件
        await self.events.emit("item_created", {
            "service": self.__class__.__name__,
            "item_id": item.id,
            "user_id": user_id,
            "item_data": response.model_dump()
        })

        logger.info(f"創建{self.__class__.__name__}成功: {item.id} by user {user_id}")

        return response

    async def get_item(
        self,
        item_id: str,
        user_id: Optional[int] = None,
        include_related: bool = True
    ) -> Dict[str, Any]:
        """
        獲取項目詳情

        Args:
            item_id: 項目ID
            user_id: 用戶ID（用於權限檢查）
            include_related: 是否包含相關信息

        Returns:
            項目詳情響應
        """
        # 構建緩存鍵
        cache_key = self._build_cache_key(
            "detail", item_id=item_id, user_id=user_id, include_related=include_related
        )

        # 嘗試從緩存獲取
        cached_result = await self.cache.get(cache_key)
        if cached_result:
            logger.debug(f"從緩存獲取詳情: {cache_key}")
            return cached_result

        # 從數據庫獲取
        item = await self.repo.get_by_id(item_id, include_deleted=False)
        if not item:
            raise ValueError(f"{self.__class__.__name__}不存在: {item_id}")

        # 權限檢查
        if user_id:
            await self.permission.check_view_permission(user_id, item)

        # 獲取相關信息
        related_data = {}
        if include_related:
            related_data = await self._get_related_data(item, user_id)

        # 轉換為響應格式
        response_schema = self.get_response_schema()
        response = response_schema.model_validate(item)

        result = {
            "item": response,
            **related_data
        }

        # 緩存結果
        await self.cache.set(cache_key, result, ttl=self.default_ttl * 2)

        return result

    async def update_item(
        self,
        item_id: str,
        request: UpdateType,
        user_id: Optional[int] = None
    ) -> ResponseType:
        """
        更新項目

        Args:
            item_id: 項目ID
            request: 更新請求
            user_id: 用戶ID

        Returns:
            更新後的項目響應
        """
        # 獲取現有項目
        item = await self.repo.get_by_id(item_id, include_deleted=False)
        if not item:
            raise ValueError(f"{self.__class__.__name__}不存在: {item_id}")

        # 權限檢查
        if user_id:
            await self.permission.check_update_permission(user_id, item)

        # 驗證更新請求
        await self.validator.validate_update_request(request, item)

        # 檢查唯一性約束（如果有）
        await self._check_unique_constraints_on_update(request, item)

        # 更新字段
        update_data = request.model_dump(exclude_unset=True)
        update_data.update(self._get_update_metadata())

        for field, value in update_data.items():
            setattr(item, field, value)

        # 保存更新
        item = await self.repo.update(item)

        # 清除相關緩存
        await self._clear_item_cache(item_id)
        await self._clear_list_cache(item.user_id if hasattr(item, 'user_id') else user_id)

        # 轉換為響應格式
        response_schema = self.get_response_schema()
        response = response_schema.model_validate(item)

        # 觸發事件
        await self.events.emit("item_updated", {
            "service": self.__class__.__name__,
            "item_id": item_id,
            "user_id": user_id,
            "updated_fields": list(update_data.keys())
        })

        logger.info(f"更新{self.__class__.__name__}成功: {item_id}")

        return response

    async def delete_item(self, item_id: str, user_id: Optional[int] = None) -> None:
        """
        刪除項目

        Args:
            item_id: 項目ID
            user_id: 用戶ID
        """
        # 獲取項目信息
        item = await self.repo.get_by_id(item_id, include_deleted=False)
        if not item:
            raise ValueError(f"{self.__class__.__name__}不存在: {item_id}")

        # 權限檢查
        if user_id:
            await self.permission.check_delete_permission(user_id, item)

        # 檢查刪除前置條件
        await self._check_delete_preconditions(item)

        # 軟刪除（推薦）或硬刪除
        if hasattr(item, 'deleted_at'):
            # 軟刪除
            item.deleted_at = datetime.now()
            await self.repo.update(item)
        else:
            # 硬刪除
            await self.repo.delete(item_id)

        # 清除相關緩存
        await self._clear_item_cache(item_id)
        await self._clear_list_cache(item.user_id if hasattr(item, 'user_id') else user_id)

        # 觸發事件
        await self.events.emit("item_deleted", {
            "service": self.__class__.__name__,
            "item_id": item_id,
            "user_id": user_id
        })

        logger.info(f"刪除{self.__class__.__name__}成功: {item_id}")

    async def batch_operation(
        self,
        item_ids: List[str],
        operation: str,
        user_id: Optional[int] = None,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        批量操作項目

        Args:
            item_ids: 項目ID列表
            operation: 操作類型
            user_id: 用戶ID
            parameters: 操作參數

        Returns:
            批量操作結果
        """
        # 權限檢查
        if user_id:
            await self.permission.check_batch_permission(user_id, operation)

        results = {
            "success": [],
            "failed": [],
            "total": len(item_ids)
        }

        for item_id in item_ids:
            try:
                if operation == "activate":
                    await self._activate_item(item_id, user_id)
                elif operation == "deactivate":
                    await self._deactivate_item(item_id, user_id)
                elif operation == "delete":
                    await self.delete_item(item_id, user_id)
                elif operation == "archive":
                    await self._archive_item(item_id, user_id)
                else:
                    # 自定義操作
                    await self._custom_operation(item_id, operation, parameters, user_id)

                results["success"].append(item_id)
            except Exception as e:
                results["failed"].append({
                    "item_id": item_id,
                    "error": str(e)
                })

        # 清除相關緩存
        if user_id:
            await self._clear_list_cache(user_id)

        # 觸發事件
        await self.events.emit("batch_operation_completed", {
            "service": self.__class__.__name__,
            "operation": operation,
            "user_id": user_id,
            "success_count": len(results["success"]),
            "failed_count": len(results["failed"])
        })

        return results

    # 抽象方法 - 子類必須實現
    @abstractmethod
    def get_model_class(self) -> Type[ModelType]:
        """獲取模型類"""
        pass

    @abstractmethod
    def get_response_schema(self) -> Type[ResponseType]:
        """獲取響應模式類"""
        pass

    # 輔助方法
    def _build_cache_key(self, operation: str, **kwargs) -> str:
        """構建緩存鍵"""
        parts = [self.cache_prefix, operation]
        for key, value in sorted(kwargs.items()):
            if value is not None:
                parts.append(f"{key}:{value}")
        return ":".join(parts)

    async def _clear_item_cache(self, item_id: str) -> None:
        """清除項目相關緩存"""
        patterns = [
            f"{self.cache_prefix}:detail:{item_id}:*",
            f"{self.cache_prefix}:related:{item_id}:*"
        ]
        for pattern in patterns:
            await self.cache.clear_pattern(pattern)

    async def _clear_list_cache(self, user_id: Optional[int]) -> None:
        """清除列表相關緩存"""
        pattern = f"{self.cache_prefix}:list:*:*:*:{user_id}:*"
        await self.cache.clear_pattern(pattern)

    def _get_create_metadata(self, user_id: int) -> Dict[str, Any]:
        """獲取創建元數據"""
        return {
            "user_id": user_id,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }

    def _get_update_metadata(self) -> Dict[str, Any]:
        """獲取更新元數據"""
        return {
            "updated_at": datetime.now()
        }

    # 可選重寫方法
    async def _check_unique_constraints(self, request: CreateType, user_id: int) -> None:
        """檢查唯一性約束"""
        pass  # 子類可重寫實現具體邏輯

    async def _check_unique_constraints_on_update(
        self,
        request: UpdateType,
        item: ModelType
    ) -> None:
        """檢查更新時的唯一性約束"""
        pass  # 子類可重寫實現具體邏輯

    async def _get_related_data(self, item: ModelType, user_id: Optional[int]) -> Dict[str, Any]:
        """獲取相關數據"""
        return {}  # 子類可重寫返回相關信息

    async def _check_delete_preconditions(self, item: ModelType) -> None:
        """檢查刪除前置條件"""
        pass  # 子類可重寫實現檢查邏輯

    async def _activate_item(self, item_id: str, user_id: Optional[int]) -> None:
        """激活項目"""
        item = await self.repo.get_by_id(item_id)
        if hasattr(item, 'is_active'):
            item.is_active = True
            item.updated_at = datetime.now()
            await self.repo.update(item)

    async def _deactivate_item(self, item_id: str, user_id: Optional[int]) -> None:
        """停用項目"""
        item = await self.repo.get_by_id(item_id)
        if hasattr(item, 'is_active'):
            item.is_active = False
            item.updated_at = datetime.now()
            await self.repo.update(item)

    async def _archive_item(self, item_id: str, user_id: Optional[int]) -> None:
        """歸檔項目"""
        item = await self.repo.get_by_id(item_id)
        if hasattr(item, 'is_archived'):
            item.is_archived = True
            item.archived_at = datetime.now()
            item.updated_at = datetime.now()
            await self.repo.update(item)

    async def _custom_operation(
        self,
        item_id: str,
        operation: str,
        parameters: Optional[Dict[str, Any]],
        user_id: Optional[int]
    ) -> None:
        """自定義操作"""
        raise ValueError(f"不支持的操作: {operation}")