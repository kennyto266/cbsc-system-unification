"""
基礎業務服務測試
Base Business Service Tests

測試BaseBusinessService的通用功能
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from src.api.strategies.services.base_business_service import BaseBusinessService
from src.api.strategies.utils.cache import CacheManager
from src.api.strategies.utils.validators import BaseValidator
from src.api.strategies.utils.permissions import PermissionChecker
from src.api.strategies.utils.events import EventBus


# Test concrete implementation
class TestBusinessService(BaseBusinessService):
    """測試用的具體業務服務實現"""

    def get_model_class(self):
        # Return a mock model class
        return MagicMock

    def get_response_schema(self):
        # Return a mock response schema
        return MagicMock


@pytest.fixture
def mock_repository():
    """Mock repository"""
    repo = AsyncMock()
    repo.list_items.return_value = ([], 0)
    repo.get_by_id.return_value = None
    repo.create.return_value = MagicMock()
    repo.update.return_value = None
    repo.delete.return_value = None
    return repo


@pytest.fixture
def mock_cache_manager():
    """Mock cache manager"""
    cache = AsyncMock(spec=CacheManager)
    cache.get.return_value = None
    cache.set.return_value = None
    cache.clear_pattern.return_value = 0
    return cache


@pytest.fixture
def mock_validator():
    """Mock validator"""
    validator = AsyncMock(spec=BaseValidator)
    validator.validate_create_request.return_value = None
    validator.validate_update_request.return_value = None
    return validator


@pytest.fixture
def mock_permission_checker():
    """Mock permission checker"""
    checker = AsyncMock(spec=PermissionChecker)
    checker.check_list_permission.return_value = None
    checker.check_create_permission.return_value = None
    checker.check_view_permission.return_value = None
    checker.check_update_permission.return_value = None
    checker.check_delete_permission.return_value = None
    checker.check_batch_permission.return_value = None
    return checker


@pytest.fixture
def mock_event_bus():
    """Mock event bus"""
    bus = AsyncMock(spec=EventBus)
    bus.emit.return_value = None
    return bus


@pytest.fixture
def business_service(
    mock_repository,
    mock_cache_manager,
    mock_validator,
    mock_permission_checker,
    mock_event_bus
):
    """Create test business service"""
    return TestBusinessService(
        repository=mock_repository,
        cache_manager=mock_cache_manager,
        validator=mock_validator,
        permission_checker=mock_permission_checker,
        event_bus=mock_event_bus,
        cache_prefix="test",
        default_ttl=300
    )


class TestBaseBusinessService:
    """基礎業務服務測試類"""

    @pytest.mark.asyncio
    async def test_list_items_cache_hit(self, business_service, mock_cache_manager):
        """測試列表緩存命中"""
        # Setup
        mock_cache_manager.get.return_value = {
            "items": [],
            "total_count": 0,
            "page": 1,
            "page_size": 20,
            "total_pages": 0
        }

        # Execute
        result = await business_service.list_items(page=1, page_size=20)

        # Verify
        assert result["items"] == []
        assert result["total_count"] == 0
        mock_cache_manager.get.assert_called_once()
        # Repository should not be called when cache hit
        assert business_service.repo.list_items.call_count == 0

    @pytest.mark.asyncio
    async def test_list_items_cache_miss(self, business_service):
        """測試列表緩存未命中"""
        # Setup
        business_service.repo.list_items.return_value = ([], 0)

        # Execute
        result = await business_service.list_items(page=1, page_size=20)

        # Verify
        assert result["items"] == []
        assert result["total_count"] == 0
        assert business_service.repo.list_items.called
        business_service.cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_items_with_filters(self, business_service):
        """測試帶過濾條件的列表"""
        # Setup
        filters = {"status": "active", "type": "premium"}
        business_service.repo.list_items.return_value = ([], 0)

        # Execute
        await business_service.list_items(page=1, page_size=20, filters=filters)

        # Verify
        business_service.repo.list_items.assert_called_with(
            page=1,
            page_size=20,
            filters=filters,
            user_id=None,
            include_deleted=False
        )

    @pytest.mark.asyncio
    async def test_create_item(self, business_service):
        """測試創建項目"""
        # Setup
        request = MagicMock()
        request.dict.return_value = {"name": "test"}

        mock_item = MagicMock()
        mock_item.id = "test_id"
        business_service.repo.create.return_value = mock_item

        # Mock response schema
        mock_response = MagicMock()
        mock_response.model_validate.return_value = {"id": "test_id"}
        business_service.get_response_schema.return_value = mock_response

        # Execute
        result = await business_service.create_item(request, user_id=1)

        # Verify
        assert result == {"id": "test_id"}
        business_service.validator.validate_create_request.assert_called_once_with(request)
        business_service.permission.check_create_permission.assert_called_once_with(1, request.dict())
        business_service.repo.create.assert_called_once()
        business_service.cache.clear_pattern.assert_called()
        business_service.events.emit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_item_with_unique_constraint_check(self, business_service):
        """測試創建項目時的唯一性約束檢查"""
        # Setup
        request = MagicMock()

        # Override _check_unique_constraints
        business_service._check_unique_constraints = AsyncMock()

        # Execute
        await business_service.create_item(request, user_id=1)

        # Verify
        business_service._check_unique_constraints.assert_called_once_with(request, 1)

    @pytest.mark.asyncio
    async def test_get_item_cache_hit(self, business_service, mock_cache_manager):
        """測試獲取項目緩存命中"""
        # Setup
        mock_cache_manager.get.return_value = {"item": {"id": "test_id"}}

        # Execute
        result = await business_service.get_item("test_id", user_id=1)

        # Verify
        assert result["item"]["id"] == "test_id"
        mock_cache_manager.get.assert_called_once()
        # Repository should not be called when cache hit
        assert business_service.repo.get_by_id.call_count == 0

    @pytest.mark.asyncio
    async def test_get_item_not_found(self, business_service):
        """測試獲取不存在的項目"""
        # Setup
        business_service.repo.get_by_id.return_value = None

        # Execute & Verify
        with pytest.raises(ValueError, match="不存在"):
            await business_service.get_item("nonexistent_id")

    @pytest.mark.asyncio
    async def test_update_item(self, business_service):
        """測試更新項目"""
        # Setup
        request = MagicMock()
        request.model_dump.return_value = {"name": "updated"}

        mock_item = MagicMock()
        mock_item.id = "test_id"
        business_service.repo.get_by_id.return_value = mock_item

        # Mock response schema
        mock_response = MagicMock()
        mock_response.model_validate.return_value = {"id": "test_id", "name": "updated"}
        business_service.get_response_schema.return_value = mock_response

        # Execute
        result = await business_service.update_item("test_id", request, user_id=1)

        # Verify
        assert result["id"] == "test_id"
        business_service.validator.validate_update_request.assert_called_once()
        business_service.permission.check_update_permission.assert_called_once()
        business_service.repo.update.assert_called_once()
        business_service.cache.clear_pattern.assert_called()

    @pytest.mark.asyncio
    async def test_delete_item(self, business_service):
        """測試刪除項目"""
        # Setup
        mock_item = MagicMock()
        mock_item.deleted_at = None
        business_service.repo.get_by_id.return_value = mock_item

        # Execute
        await business_service.delete_item("test_id", user_id=1)

        # Verify
        business_service.permission.check_delete_permission.assert_called_once()
        business_service._check_delete_preconditions.assert_called_once_with(mock_item)
        business_service.cache.clear_pattern.assert_called()
        business_service.events.emit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_item_soft_delete(self, business_service):
        """測試軟刪除"""
        # Setup
        mock_item = MagicMock()
        mock_item.deleted_at = None
        business_service.repo.get_by_id.return_value = mock_item

        # Execute
        await business_service.delete_item("test_id", user_id=1)

        # Verify
        assert mock_item.deleted_at is not None
        business_service.repo.update.assert_called_once_with(mock_item)

    @pytest.mark.asyncio
    async def test_batch_operation(self, business_service):
        """測試批量操作"""
        # Setup
        business_service._activate_item = AsyncMock()

        # Execute
        result = await business_service.batch_operation(
            item_ids=["id1", "id2"],
            operation="activate",
            user_id=1
        )

        # Verify
        assert result["total"] == 2
        assert len(result["success"]) == 2
        assert len(result["failed"]) == 0
        assert business_service._activate_item.call_count == 2
        business_service.events.emit.assert_called_once()

    @pytest.mark.asyncio
    async def test_batch_operation_with_failures(self, business_service):
        """測試批量操作失敗"""
        # Setup
        business_service._activate_item = AsyncMock(side_effect=Exception("Test error"))

        # Execute
        result = await business_service.batch_operation(
            item_ids=["id1", "id2"],
            operation="activate",
            user_id=1
        )

        # Verify
        assert result["total"] == 2
        assert len(result["success"]) == 0
        assert len(result["failed"]) == 2
        assert all("error" in failure for failure in result["failed"])

    @pytest.mark.asyncio
    async def test_build_cache_key(self, business_service):
        """測試緩存鍵構建"""
        # Execute
        key = business_service._build_cache_key(
            "test",
            page=1,
            page_size=20,
            filters={"status": "active"},
            user_id=123
        )

        # Verify
        expected = "test:filters:{'status': 'active'}:page:1:page_size:20:user_id:123"
        assert key == expected

    def test_get_create_metadata(self, business_service):
        """測試獲取創建元數據"""
        metadata = business_service._get_create_metadata(user_id=123)

        assert metadata["user_id"] == 123
        assert "created_at" in metadata
        assert "updated_at" in metadata
        assert isinstance(metadata["created_at"], datetime)

    def test_get_update_metadata(self, business_service):
        """測試獲取更新元數據"""
        metadata = business_service._get_update_metadata()

        assert "updated_at" in metadata
        assert isinstance(metadata["updated_at"], datetime)

    @pytest.mark.asyncio
    async def test_activate_item(self, business_service):
        """測試激活項目"""
        # Setup
        mock_item = MagicMock()
        mock_item.is_active = False
        business_service.repo.get_by_id.return_value = mock_item

        # Execute
        await business_service._activate_item("test_id", user_id=1)

        # Verify
        assert mock_item.is_active is True
        business_service.repo.update.assert_called_once_with(mock_item)

    @pytest.mark.asyncio
    async def test_deactivate_item(self, business_service):
        """測試停用項目"""
        # Setup
        mock_item = MagicMock()
        mock_item.is_active = True
        business_service.repo.get_by_id.return_value = mock_item

        # Execute
        await business_service._deactivate_item("test_id", user_id=1)

        # Verify
        assert mock_item.is_active is False
        business_service.repo.update.assert_called_once_with(mock_item)

    @pytest.mark.asyncio
    async def test_archive_item(self, business_service):
        """測試歸檔項目"""
        # Setup
        mock_item = MagicMock()
        mock_item.is_archived = False
        business_service.repo.get_by_id.return_value = mock_item

        # Execute
        await business_service._archive_item("test_id", user_id=1)

        # Verify
        assert mock_item.is_archived is True
        assert mock_item.archived_at is not None
        business_service.repo.update.assert_called_once_with(mock_item)

    @pytest.mark.asyncio
    async def test_custom_operation_not_supported(self, business_service):
        """測試不支持的自定義操作"""
        # Execute & Verify
        with pytest.raises(ValueError, match="不支持的操作"):
            await business_service._custom_operation(
                "test_id",
                "unsupported_operation",
                None,
                1
            )