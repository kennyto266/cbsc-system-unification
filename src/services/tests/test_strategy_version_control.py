"""
Tests for Strategy Version Control Service
Test-driven development for strategy version management
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any, List
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
import json

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.strategy_version_control import (
    StrategyVersionControl, VersionStatus, ChangeType
)
from models.strategy_models_v2 import (
    Strategy, StrategyVersion, StrategyChangeLog
)
from schemas.strategy_schemas import (
    StrategyVersionCreate, StrategyComparisonResult
)
from core.exceptions import (
    StrategyError, StrategyNotFoundError, StrategyValidationError
)


# Mock User for testing
class MockUser:
    def __init__(self, is_superuser: bool = False):
        self.id = uuid4()
        self.is_superuser = is_superuser
        self.email = "test@example.com"


@pytest.fixture
def mock_db():
    """Mock database session"""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.scalar = AsyncMock()
    session.scalars = AsyncMock()
    session.get = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.delete = AsyncMock()
    session.flush = AsyncMock()
    return session


@pytest.fixture
def version_control(mock_db):
    """Version control service fixture"""
    return StrategyVersionControl(mock_db)


@pytest.fixture
def sample_strategy():
    """Sample strategy"""
    return Strategy(
        id=uuid4(),
        name="Test Strategy",
        slug="test-strategy",
        config={"param1": "value1", "param2": 100},
        author_id=uuid4(),
        created_at=datetime.utcnow()
    )


@pytest.fixture
def sample_version():
    """Sample strategy version"""
    return StrategyVersion(
        id=uuid4(),
        strategy_id=uuid4(),
        version_number="1.0.0",
        config={"param1": "value1", "param2": 100, "param3": True},
        description="Initial version",
        status=VersionStatus.DRAFT,
        author_id=uuid4(),
        changes={"change_type": "create"},
        created_at=datetime.utcnow()
    )


@pytest.fixture
def sample_config():
    """Sample strategy configuration"""
    return {
        "fast_period": 10,
        "slow_period": 20,
        "symbols": ["AAPL", "MSFT"],
        "risk_level": "medium",
        "allocation": 0.1
    }


@pytest.fixture
def mock_user():
    """Mock user fixture"""
    return MockUser()


class TestStrategyVersionControl:
    """Test strategy version control functionality"""

    async def test_create_version_success(self, version_control, mock_db, sample_strategy, sample_config, mock_user):
        """Test successful version creation"""
        # Mock database responses
        mock_db.get.return_value = sample_strategy
        mock_db.execute.return_value.scalar_one_or_none.return_value = None
        mock_db.execute.return_value.scalar.return_value = 1  # Current config exists

        with patch.object(version_control, '_generate_version_number', return_value="1.0.0"):
            version = await version_control.create_version(
                strategy_id=sample_strategy.id,
                config=sample_config,
                description="Initial version",
                author_id=mock_user.id
            )

        assert version.strategy_id == sample_strategy.id
        assert version.version_number == "1.0.0"
        assert version.config == sample_config
        assert version.status == VersionStatus.DRAFT

    async def test_create_version_duplicate_number(self, version_control, mock_db, sample_strategy, sample_config):
        """Test version creation with duplicate number"""
        # Mock existing version
        existing_version = StrategyVersion(
            id=uuid4(),
            version_number="1.0.0"
        )
        mock_db.get.return_value = sample_strategy
        mock_db.execute.return_value.scalar_one_or_none.return_value = existing_version

        with pytest.raises(StrategyValidationError, match="already exists"):
            await version_control.create_version(
                strategy_id=sample_strategy.id,
                config=sample_config,
                version_number="1.0.0"
            )

    async def test_create_version_nonexistent_strategy(self, version_control, mock_db, sample_config):
        """Test version creation for non-existent strategy"""
        mock_db.get.return_value = None

        with pytest.raises(StrategyNotFoundError, match="not found"):
            await version_control.create_version(
                strategy_id=uuid4(),
                config=sample_config
            )

    async def test_get_version_success(self, version_control, mock_db, sample_version):
        """Test getting version by ID"""
        mock_db.get.return_value = sample_version

        version = await version_control.get_version(sample_version.id)

        assert version.id == sample_version.id
        assert version.version_number == sample_version.version_number

    async def test_get_version_not_found(self, version_control, mock_db):
        """Test getting non-existent version"""
        mock_db.get.return_value = None

        with pytest.raises(StrategyNotFoundError, match="not found"):
            await version_control.get_version(uuid4())

    async def test_get_version_by_number(self, version_control, mock_db, sample_strategy, sample_version):
        """Test getting version by version number"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_version
        mock_db.execute.return_value = mock_result

        version = await version_control.get_version_by_number(
            sample_strategy.id,
            "1.0.0"
        )

        assert version.version_number == "1.0.0"

    async def test_list_versions(self, version_control, mock_db, sample_strategy):
        """Test listing strategy versions"""
        versions = [
            StrategyVersion(id=uuid4(), version_number="1.0.0", strategy_id=sample_strategy.id),
            StrategyVersion(id=uuid4(), version_number="1.1.0", strategy_id=sample_strategy.id),
            StrategyVersion(id=uuid4(), version_number="2.0.0", strategy_id=sample_strategy.id)
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = versions
        mock_db.execute.return_value = mock_result

        result = await version_control.list_versions(sample_strategy.id)

        assert len(result) == 3

    async def test_list_versions_with_filters(self, version_control, mock_db, sample_strategy):
        """Test listing versions with filters"""
        versions = [
            StrategyVersion(
                id=uuid4(),
                version_number="1.0.0",
                strategy_id=sample_strategy.id,
                status=VersionStatus.PUBLISHED,
                author_id=uuid4()
            )
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = versions
        mock_db.execute.return_value = mock_result

        # Test with status filter
        result = await version_control.list_versions(
            sample_strategy.id,
            status=VersionStatus.PUBLISHED
        )
        assert len(result) == 1
        assert result[0].status == VersionStatus.PUBLISHED

    async def test_get_latest_version(self, version_control, mock_db, sample_strategy):
        """Test getting latest version"""
        latest_version = StrategyVersion(
            id=uuid4(),
            version_number="2.0.0",
            strategy_id=sample_strategy.id,
            status=VersionStatus.PUBLISHED
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = latest_version
        mock_db.execute.return_value = mock_result

        result = await version_control.get_latest_version(sample_strategy.id)

        assert result.version_number == "2.0.0"

    async def test_get_latest_published_version(self, version_control, mock_db, sample_strategy):
        """Test getting latest published version"""
        latest_version = StrategyVersion(
            id=uuid4(),
            version_number="1.5.0",
            strategy_id=sample_strategy.id,
            status=VersionStatus.PUBLISHED
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = latest_version
        mock_db.execute.return_value = mock_result

        result = await version_control.get_latest_version(sample_strategy.id, published_only=True)

        assert result.status == VersionStatus.PUBLISHED

    async def test_update_version_status(self, version_control, mock_db, sample_version, mock_user):
        """Test updating version status"""
        mock_db.get.return_value = sample_version

        version = await version_control.update_version_status(
            sample_version.id,
            VersionStatus.PUBLISHED,
            author_id=mock_user.id,
            notes="Ready for production"
        )

        assert version.status == VersionStatus.PUBLISHED

    async def test_update_version_status_invalid_transition(self, version_control, mock_db, sample_version):
        """Test invalid status transition"""
        sample_version.status = VersionStatus.ARCHIVED
        mock_db.get.return_value = sample_version

        with pytest.raises(StrategyValidationError, match="Invalid status transition"):
            await version_control.update_version_status(
                sample_version.id,
                VersionStatus.DRAFT
            )

    async def test_compare_versions(self, version_control, mock_db):
        """Test comparing two versions"""
        version1 = StrategyVersion(
            id=uuid4(),
            strategy_id=uuid4(),
            version_number="1.0.0",
            config={"param1": "value1", "param2": 100}
        )
        version2 = StrategyVersion(
            id=uuid4(),
            strategy_id=uuid4(),
            version_number="1.1.0",
            config={"param1": "value1", "param2": 200, "param3": True}
        )

        mock_db.get.side_effect = [version1, version2]

        result = await version_control.compare_versions(version1.id, version2.id)

        assert isinstance(result, StrategyComparisonResult)
        assert result.version1_number == "1.0.0"
        assert result.version2_number == "1.1.0"
        assert result.has_changes is True

    async def test_rollback_to_version(self, version_control, mock_db, sample_strategy, sample_version, mock_user):
        """Test rollback to previous version"""
        current_version = StrategyVersion(
            id=uuid4(),
            strategy_id=sample_strategy.id,
            version_number="2.0.0",
            config={"param1": "new_value", "param2": 999}
        )

        mock_db.get.side_effect = [sample_version, current_version, sample_strategy]
        mock_db.execute.return_value.scalar_one_or_none.return_value = None

        with patch.object(version_control, '_generate_version_number', return_value="2.1.0"):
            rollback_version = await version_control.rollback_to_version(
                sample_strategy.id,
                sample_version.id,
                author_id=mock_user.id,
                reason="Bug fix rollback"
            )

        assert rollback_version.config == sample_version.config
        assert "rollback" in rollback_version.description.lower()

    async def test_rollback_wrong_strategy(self, version_control, mock_db, sample_version, mock_user):
        """Test rollback with version from different strategy"""
        mock_db.get.return_value = sample_version

        with pytest.raises(StrategyValidationError, match="does not belong to strategy"):
            await version_control.rollback_to_version(
                uuid4(),  # Different strategy ID
                sample_version.id,
                author_id=mock_user.id
            )

    async def test_branch_version(self, version_control, mock_db, sample_version, mock_user):
        """Test creating branch from version"""
        mock_db.get.return_value = sample_version

        with patch.object(version_control, '_generate_version_number', return_value="1.0.1"):
            branch_version = await version_control.branch_version(
                source_version_id=sample_version.id,
                new_version_number="1.0.1-branch",
                author_id=mock_user.id
            )

        assert branch_version.version_number == "1.0.1-branch"
        assert branch_version.parent_version_id == sample_version.id

    async def test_merge_versions(self, version_control, mock_db, sample_strategy, mock_user):
        """Test merging two versions"""
        version1 = StrategyVersion(
            id=uuid4(),
            strategy_id=sample_strategy.id,
            version_number="1.0.0",
            config={"param1": "value1", "param2": 100}
        )
        version2 = StrategyVersion(
            id=uuid4(),
            strategy_id=sample_strategy.id,
            version_number="1.1.0",
            config={"param1": "value2", "param3": True}
        )

        mock_db.get.side_effect = [version1, version2]

        merge_config = {
            "param1": "value1",
            "param2": 100,
            "param3": True
        }

        with patch.object(version_control, '_generate_version_number', return_value="2.0.0"):
            merge_version = await version_control.merge_versions(
                strategy_id=sample_strategy.id,
                source_version_id=version1.id,
                target_version_id=version2.id,
                merge_config=merge_config,
                author_id=mock_user.id
            )

        assert merge_version.config == merge_config
        assert "merge" in merge_version.description.lower()

    async def test_get_change_history(self, version_control, mock_db, sample_strategy):
        """Test getting change history"""
        change_logs = [
            StrategyChangeLog(
                id=uuid4(),
                strategy_id=sample_strategy.id,
                change_type=ChangeType.CREATE,
                description="Initial version"
            ),
            StrategyChangeLog(
                id=uuid4(),
                strategy_id=sample_strategy.id,
                change_type=ChangeType.UPDATE,
                description="Updated parameters"
            )
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = change_logs
        mock_db.execute.return_value = mock_result

        history = await version_control.get_change_history(sample_strategy.id)

        assert len(history) == 2
        assert history[0].change_type == ChangeType.CREATE
        assert history[1].change_type == ChangeType.UPDATE

    async def test_get_version_tree(self, version_control, mock_db, sample_strategy):
        """Test getting version tree"""
        version1 = StrategyVersion(
            id=uuid4(),
            strategy_id=sample_strategy.id,
            version_number="1.0.0",
            parent_version_id=None
        )
        version2 = StrategyVersion(
            id=uuid4(),
            strategy_id=sample_strategy.id,
            version_number="1.1.0",
            parent_version_id=version1.id
        )
        version3 = StrategyVersion(
            id=uuid4(),
            strategy_id=sample_strategy.id,
            version_number="2.0.0",
            parent_version_id=version2.id
        )

        versions = [version1, version2, version3]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = versions
        mock_db.execute.return_value = mock_result

        tree = await version_control.get_version_tree(sample_strategy.id)

        assert tree["strategy_id"] == sample_strategy.id
        assert len(tree["versions"]) == 3
        assert len(tree["relationships"]) == 2

    async def test_generate_version_number_new_strategy(self, version_control):
        """Test generating version number for new strategy"""
        # Mock no existing versions
        with patch.object(version_control, 'get_latest_version', return_value=None):
            version_number = await version_control._generate_version_number(uuid4())
            assert version_number == "1.0.0"

    async def test_generate_version_number_increment_patch(self, version_control):
        """Test generating version number with patch increment"""
        # Mock existing version
        latest_version = MagicMock()
        latest_version.version_number = "1.2.3"

        with patch.object(version_control, 'get_latest_version', return_value=latest_version):
            version_number = await version_control._generate_version_number(uuid4())
            assert version_number == "1.2.4"

    async def test_calculate_changes_create(self, version_control, sample_config):
        """Test calculating changes for create operation"""
        changes = version_control._calculate_changes(
            {},
            sample_config,
            ChangeType.CREATE
        )

        assert changes["change_type"] == "create"
        assert "timestamp" in changes

    async def test_calculate_changes_update(self, version_control, sample_config):
        """Test calculating changes for update operation"""
        old_config = {"param1": "value1", "param2": 100}
        new_config = {"param1": "value1", "param2": 200, "param3": True}

        changes = version_control._calculate_changes(
            old_config,
            new_config,
            ChangeType.UPDATE
        )

        assert changes["change_type"] == "update"
        assert "details" in changes
        assert changes["details"]["added"]["param3"] is True
        assert changes["details"]["modified"]["param2"]["old"] == 100
        assert changes["details"]["modified"]["param2"]["new"] == 200

    async def test_calculate_differences(self, version_control):
        """Test calculating detailed differences"""
        config1 = {"param1": "value1", "param2": 100}
        config2 = {"param1": "value2", "param3": True}

        differences = version_control._calculate_differences(config1, config2)

        assert len(differences) == 3

        # Check added
        added = [d for d in differences if d["type"] == "added"]
        assert len(added) == 1
        assert added[0]["key"] == "param3"

        # Check removed
        removed = [d for d in differences if d["type"] == "removed"]
        assert len(removed) == 1
        assert removed[0]["key"] == "param2"

        # Check modified
        modified = [d for d in differences if d["type"] == "modified"]
        assert len(modified) == 1
        assert modified[0]["key"] == "param1"

    def test_is_valid_status_transition(self, version_control):
        """Test valid status transitions"""
        # Valid transitions
        assert version_control._is_valid_status_transition(
            VersionStatus.DRAFT, VersionStatus.REVIEW
        ) is True
        assert version_control._is_valid_status_transition(
            VersionStatus.APPROVED, VersionStatus.PUBLISHED
        ) is True

        # Invalid transitions
        assert version_control._is_valid_status_transition(
            VersionStatus.ARCHIVED, VersionStatus.DRAFT
        ) is False

    def test_generate_diff_text(self, version_control, sample_config):
        """Test generating diff text"""
        config1 = {"param1": "value1", "param2": 100}
        config2 = {"param1": "value2", "param2": 200}

        diff_text = version_control._generate_diff_text(config1, config2)

        assert isinstance(diff_text, str)
        assert "--- version1" in diff_text
        assert "+++ version2" in diff_text
        assert "-value1" in diff_text
        assert "+value2" in diff_text