"""
Tests for Strategy Category Management Implementation
測試策略分類管理實際實現
"""

import pytest
from datetime import datetime
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from services.strategy_service_v2 import StrategyService
from models.strategy_models_v2 import StrategyCategory, Strategy
from schemas.strategy_schemas import (
    StrategyCategoryCreate, StrategyCategoryUpdate,
    StrategyCategoryResponse, CategoryTreeResponse
)
from core.exceptions import StrategyNotFoundError, StrategyValidationError


class MockUser:
    def __init__(self, is_superuser: bool = False):
        self.id = uuid4()
        self.is_superuser = is_superuser


@pytest.fixture
def mock_db():
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.scalar = AsyncMock()
    session.scalars = AsyncMock()
    session.get = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.delete = AsyncMock()
    return session


@pytest.fixture
def strategy_service(mock_db):
    return StrategyService(mock_db)


@pytest.fixture
def mock_user():
    return MockUser()


@pytest.fixture
def sample_category_data():
    return StrategyCategoryCreate(
        name="技術指標策略",
        slug="technical-indicators",
        description="基於技術指標的交易策略",
        icon="chart-line",
        sort_order=1
    )


class TestStrategyCategoryManagement:
    """測試策略分類管理實際實現"""

    async def test_create_category_success(self, strategy_service, mock_db, sample_category_data, mock_user):
        """測試成功創建分類"""
        # 設置mock返回值
        mock_db.execute.return_value.scalar_one_or_none.return_value = None  # slug不存在
        mock_db.execute.return_value.scalar.return_value = None  # parent_id檢查

        # 模擬創建的category
        created_category = StrategyCategory(
            id=uuid4(),
            name=sample_category_data.name,
            slug=sample_category_data.slug,
            description=sample_category_data.description,
            icon=sample_category_data.icon,
            sort_order=sample_category_data.sort_order,
            created_by=mock_user.id
        )
        mock_db.refresh.side_effect = lambda x: None

        # 執行測試
        result = await strategy_service.create_category(sample_category_data, mock_user.id)

        # 驗證結果
        assert result is not None
        assert result.name == sample_category_data.name
        assert result.slug == sample_category_data.slug
        assert result.created_by == mock_user.id

    async def test_create_category_duplicate_slug(self, strategy_service, mock_db, sample_category_data, mock_user):
        """測試創建重複slug的分類"""
        # 設置mock返回值
        existing_category = StrategyCategory(
            id=uuid4(),
            name="存在的分類",
            slug=sample_category_data.slug
        )
        mock_db.execute.return_value.scalar_one_or_none.return_value = existing_category

        # 執行測試，應該拋出異常
        with pytest.raises(StrategyValidationError, match="already exists"):
            await strategy_service.create_category(sample_category_data, mock_user.id)

    async def test_get_category_tree(self, strategy_service, mock_db):
        """測試獲取分類樹"""
        # 設置mock返回值
        categories = [
            StrategyCategory(
                id=uuid4(),
                name="技術指標",
                slug="technical",
                parent_id=None,
                sort_order=1
            ),
            StrategyCategory(
                id=uuid4(),
                name="動量策略",
                slug="momentum",
                parent_id=None,
                sort_order=2
            ),
            StrategyCategory(
                id=uuid4(),
                name="MACD",
                slug="macd",
                parent_id=categories[0].id,
                sort_order=1
            )
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = categories
        mock_db.execute.return_value = mock_result
        mock_db.execute.return_value.scalar.return_value = 0  # strategy count

        # 執行測試
        tree = await strategy_service.get_category_tree(include_strategy_count=False)

        # 驗證結果
        assert isinstance(tree, list)
        assert len(tree) == 2  # 根級分類數量

    async def test_update_category_success(self, strategy_service, mock_db, mock_user):
        """測試成功更新分類"""
        category_id = uuid4()
        update_data = StrategyCategoryUpdate(
            name="更新的分類名",
            description="更新的描述"
        )

        # 設置mock返回值
        existing_category = StrategyCategory(
            id=category_id,
            name="原分類名",
            slug="original-slug"
        )
        mock_db.get.return_value = existing_category
        mock_db.execute.return_value.scalar_one_or_none.return_value = None  # slug檢查通過
        mock_db.refresh.side_effect = lambda x: None

        # 執行測試
        result = await strategy_service.update_category(category_id, update_data, mock_user.id)

        # 驗證結果
        assert result.id == category_id
        assert result.name == "更新的分類名"
        assert result.description == "更新的描述"

    async def test_delete_category_success(self, strategy_service, mock_db, mock_user):
        """測試成功刪除分類"""
        category_id = uuid4()

        # 設置mock返回值
        existing_category = StrategyCategory(
            id=category_id,
            name="待刪除分類",
            slug="delete-me"
        )
        mock_db.get.return_value = existing_category
        mock_db.execute.return_value.scalar.side_effect = [0, 0]  # 策略數和子分類數都為0

        # 執行測試
        result = await strategy_service.delete_category(category_id, mock_user.id)

        # 驗證結果
        assert result is True

    async def test_delete_category_with_strategies(self, strategy_service, mock_db, mock_user):
        """測試刪除有策略的分類"""
        category_id = uuid4()

        # 設置mock返回值
        existing_category = StrategyCategory(
            id=category_id,
            name="有策略的分類",
            slug="has-strategies"
        )
        mock_db.get.return_value = existing_category
        mock_db.execute.return_value.scalar.side_effect = [5, 0]  # 5個策略，0個子分類

        # 執行測試，應該拋出異常
        with pytest.raises(StrategyValidationError, match="contains 5 strategies"):
            await strategy_service.delete_category(category_id, mock_user.id, force=False)

    async def test_get_categories_with_pagination(self, strategy_service, mock_db):
        """測試分頁獲取分類列表"""
        # 設置mock返回值
        categories = [
            StrategyCategory(id=uuid4(), name="分類1"),
            StrategyCategory(id=uuid4(), name="分類2")
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = categories
        mock_result.scalar.return_value = 2  # 總數
        mock_db.execute.side_effect = [mock_result, mock_result]  # 第一次查詢，第二次計數

        # 執行測試
        result = await strategy_service.get_categories_with_pagination(page=1, page_size=10)

        # 驗證結果
        assert "categories" in result
        assert "pagination" in result
        assert len(result["categories"]) == 2
        assert result["pagination"]["total"] == 2

    async def test_batch_update_categories(self, strategy_service, mock_db, mock_user):
        """測試批量更新分類"""
        category_ids = [uuid4(), uuid4(), uuid4()]
        updates = {
            "is_active": False,
            "sort_order_increment": 10
        }

        # 設置mock返回值
        categories = [
            StrategyCategory(id=category_ids[0], name="分類1", sort_order=1),
            StrategyCategory(id=category_ids[1], name="分類2", sort_order=2),
            StrategyCategory(id=category_ids[2], name="分類3", sort_order=3)
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = categories
        mock_db.execute.return_value = mock_result

        # 執行測試
        result = await strategy_service.batch_update_categories(category_ids, updates, mock_user.id)

        # 驗證結果
        assert len(result) == 3
        assert all(not c.is_active for c in result)

    async def test_move_category(self, strategy_service, mock_db, mock_user):
        """測試移動分類到新的父分類"""
        category_id = uuid4()
        new_parent_id = uuid4()

        # 設置mock返回值
        category = StrategyCategory(id=category_id, name="待移動分類")
        new_parent = StrategyCategory(id=new_parent_id, name="新父分類")

        mock_db.get.side_effect = [category, new_parent]
        mock_db.execute.return_value.scalar_one_or_none.return_value = None  # 無循環檢查
        mock_db.refresh.side_effect = lambda x: None

        # 執行測試
        result = await strategy_service.move_category(category_id, new_parent_id, mock_user.id)

        # 驗證結果
        assert result.id == category_id
        assert result.parent_id == new_parent_id

    async def test_search_categories(self, strategy_service, mock_db):
        """測試搜索分類"""
        query = "技術"

        # 設置mock返回值
        categories = [
            StrategyCategory(id=uuid4(), name="技術指標", description="基於技術指標"),
            StrategyCategory(id=uuid4(), name="高頻技術", description="高頻交易技術")
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = categories
        mock_db.execute.return_value = mock_result

        # 執行測試
        result = await strategy_service.search_categories(query)

        # 驗證結果
        assert len(result) == 2

    async def test_get_category_statistics(self, strategy_service, mock_db):
        """測試獲取分類統計信息"""
        category_id = uuid4()

        # 設置mock返回值
        category = StrategyCategory(id=category_id, name="統計分類")
        mock_db.get.return_value = category

        # 設置統計數據mock
        mock_db.execute.return_value.scalar.side_effect = [
            10,  # 策略總數
            5,   # 活躍策略數
            3,   # 子分類數
            0.15 # 平均年化回報
        ]

        # 執行測試
        result = await strategy_service.get_category_statistics(category_id)

        # 驗證結果
        assert result["category_id"] == category_id
        assert result["total_strategies"] == 10
        assert result["active_strategies"] == 5
        assert result["subcategory_count"] == 3
        assert result["average_annual_return"] == 0.15

    async def test_export_categories(self, strategy_service, mock_db):
        """測試導出分類數據"""
        # 設置mock返回值
        categories = [
            {
                "id": uuid4(),
                "name": "技術指標",
                "slug": "technical",
                "description": "技術指標類策略",
                "created_at": datetime.utcnow()
            },
            {
                "id": uuid4(),
                "name": "動量策略",
                "slug": "momentum",
                "description": "動量類策略",
                "created_at": datetime.utcnow()
            }
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = categories
        mock_db.execute.return_value = mock_result
        mock_db.execute.return_value.scalar.return_value = 0  # strategy count

        # 執行測試
        result = await strategy_service.export_categories(format="json")

        # 驗證結果
        assert "categories" in result
        assert "exported_at" in result
        assert "total_count" in result
        assert len(result["categories"]) == 2

    async def test_import_categories(self, strategy_service, mock_db, mock_user):
        """測試導入分類數據"""
        import_data = [
            {
                "name": "新分類1",
                "slug": "new-category-1",
                "description": "導入的分類1"
            },
            {
                "name": "新分類2",
                "slug": "new-category-2",
                "description": "導入的分類2"
            }
        ]

        # 設置mock返回值
        mock_db.execute.return_value.scalar_one_or_none.return_value = None  # slug不存在

        # 執行測試
        result = await strategy_service.import_categories(import_data, mock_user.id)

        # 驗證結果
        assert len(result) == 2
        assert all(c.created_by == mock_user.id for c in result)