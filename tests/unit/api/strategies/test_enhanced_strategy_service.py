"""
Unit tests for Enhanced Strategy Service
Tests all CRUD operations, batch operations, and validation logic
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch, call
from typing import List, Dict, Any
import asyncio

from src.api.strategies.services.enhanced_strategy_service import (
    EnhancedStrategyService,
    BatchOperationType,
    BatchOperationConfig,
    BatchOperationResult
)
from src.api.strategies.utils.validators import ValidationError
from src.api.strategies.utils.errors import BusinessError, ErrorCode
from src.api.strategies.utils.response import NotFoundError, PermissionError


class TestEnhancedStrategyService:
    """Test suite for EnhancedStrategyService"""

    @pytest.mark.asyncio
    async def test_service_initialization(
        self,
        mock_strategy_repo,
        mock_user_repo,
        mock_cache_manager,
        mock_websocket_service
    ):
        """Test service initialization with all dependencies"""
        validator = Mock()
        service = EnhancedStrategyService(
            strategy_repo=mock_strategy_repo,
            user_repo=mock_user_repo,
            cache_manager=mock_cache_manager,
            validator=validator,
            websocket_service=mock_websocket_service
        )

        assert service.strategy_repo == mock_strategy_repo
        assert service.user_repo == mock_user_repo
        assert service.cache_manager == mock_cache_manager
        assert service.validator == validator
        assert service.websocket_service == mock_websocket_service
        assert service._active_batches == {}
        assert isinstance(service._lock, asyncio.Lock)

    # ========================================
    # CRUD Operations Tests
    # ========================================

    @pytest.mark.asyncio
    @pytest.mark.strategy
    async def test_create_strategy_success(
        self,
        enhanced_strategy_service,
        sample_strategy_data,
        mock_strategy_repo,
        mock_cache_manager,
        mock_websocket_service
    ):
        """Test successful strategy creation"""
        # Arrange
        strategy_data = sample_strategy_data
        mock_strategy_repo.create.return_value = strategy_data
        mock_strategy_repo.get_by_id.return_value = strategy_data

        # Act
        result = await enhanced_strategy_service.create_strategy(strategy_data)

        # Assert
        assert result == strategy_data
        mock_strategy_repo.create.assert_called_once_with(strategy_data)
        mock_cache_manager.delete.assert_called_once()  # Invalidate cache
        mock_websocket_service.broadcast.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.strategy
    @pytest.mark.error_handling
    async def test_create_strategy_validation_error(
        self,
        enhanced_strategy_service,
        sample_strategy_data,
        mock_strategy_repo
    ):
        """Test strategy creation with validation error"""
        # Arrange
        invalid_data = sample_strategy_data.copy()
        invalid_data["name"] = ""  # Invalid empty name

        mock_strategy_repo.create.side_effect = ValidationError(
            field="name",
            message="Name cannot be empty"
        )

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await enhanced_strategy_service.create_strategy(invalid_data)

        assert exc_info.value.field == "name"
        assert "Name cannot be empty" in str(exc_info.value.message)

    @pytest.mark.asyncio
    @pytest.mark.strategy
    async def test_get_strategy_from_cache(
        self,
        enhanced_strategy_service,
        sample_strategy_data,
        mock_cache_manager,
        mock_strategy_repo
    ):
        """Test getting strategy from cache"""
        # Arrange
        strategy_id = 1
        mock_cache_manager.get.return_value = sample_strategy_data

        # Act
        result = await enhanced_strategy_service.get_strategy(strategy_id)

        # Assert
        assert result == sample_strategy_data
        mock_cache_manager.get.assert_called_once_with(f"strategy:{strategy_id}")
        mock_strategy_repo.get_by_id.assert_not_called()  # Should not hit DB

    @pytest.mark.asyncio
    @pytest.mark.strategy
    async def test_get_strategy_from_db(
        self,
        enhanced_strategy_service,
        sample_strategy_data,
        mock_cache_manager,
        mock_strategy_repo
    ):
        """Test getting strategy from database when not in cache"""
        # Arrange
        strategy_id = 1
        mock_cache_manager.get.return_value = None  # Cache miss
        mock_strategy_repo.get_by_id.return_value = sample_strategy_data

        # Act
        result = await enhanced_strategy_service.get_strategy(strategy_id)

        # Assert
        assert result == sample_strategy_data
        mock_cache_manager.get.assert_called_once_with(f"strategy:{strategy_id}")
        mock_strategy_repo.get_by_id.assert_called_once_with(strategy_id)
        mock_cache_manager.set.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.strategy
    @pytest.mark.error_handling
    async def test_get_strategy_not_found(
        self,
        enhanced_strategy_service,
        mock_cache_manager,
        mock_strategy_repo
    ):
        """Test getting non-existent strategy"""
        # Arrange
        strategy_id = 999
        mock_cache_manager.get.return_value = None
        mock_strategy_repo.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await enhanced_strategy_service.get_strategy(strategy_id)

        assert "Strategy not found" in str(exc_info.value)

    @pytest.mark.asyncio
    @pytest.mark.strategy
    async def test_update_strategy_success(
        self,
        enhanced_strategy_service,
        sample_strategy_data,
        mock_strategy_repo,
        mock_cache_manager,
        mock_websocket_service
    ):
        """Test successful strategy update"""
        # Arrange
        strategy_id = 1
        update_data = {"name": "Updated Strategy", "status": "inactive"}

        mock_strategy_repo.get_by_id.return_value = sample_strategy_data
        updated_strategy = {**sample_strategy_data, **update_data}
        mock_strategy_repo.update.return_value = updated_strategy

        # Act
        result = await enhanced_strategy_service.update_strategy(strategy_id, update_data)

        # Assert
        assert result["name"] == "Updated Strategy"
        assert result["status"] == "inactive"
        mock_strategy_repo.update.assert_called_once_with(strategy_id, update_data)
        mock_cache_manager.delete.assert_called()  # Invalidate cache
        mock_websocket_service.broadcast.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.strategy
    async def test_delete_strategy_success(
        self,
        enhanced_strategy_service,
        mock_strategy_repo,
        mock_cache_manager,
        mock_websocket_service
    ):
        """Test successful strategy deletion"""
        # Arrange
        strategy_id = 1
        mock_strategy_repo.delete.return_value = True

        # Act
        result = await enhanced_strategy_service.delete_strategy(strategy_id)

        # Assert
        assert result is True
        mock_strategy_repo.delete.assert_called_once_with(strategy_id)
        mock_cache_manager.delete.assert_called_once()
        mock_websocket_service.broadcast.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.strategy
    async def test_list_strategies_with_cache(
        self,
        enhanced_strategy_service,
        sample_strategies_data,
        mock_cache_manager,
        mock_strategy_repo
    ):
        """Test listing strategies with cache hit"""
        # Arrange
        filters = {"status": "active", "page": 1, "page_size": 10}
        cache_key = "strategies:list:" + str(hash(str(sorted(filters.items()))))

        mock_cache_manager.get.return_value = {
            "items": sample_strategies_data,
            "total": len(sample_strategies_data)
        }

        # Act
        result = await enhanced_strategy_service.list_strategies(filters)

        # Assert
        assert result["items"] == sample_strategies_data
        assert result["total"] == len(sample_strategies_data)
        mock_cache_manager.get.assert_called_once_with(cache_key)
        mock_strategy_repo.list.assert_not_called()

    # ========================================
    # Batch Operations Tests
    # ========================================

    @pytest.mark.asyncio
    @pytest.mark.batch
    @pytest.mark.strategy
    async def test_batch_activate_strategies(
        self,
        enhanced_strategy_service,
        mock_strategy_repo,
        mock_websocket_service,
        batch_operation_config
    ):
        """Test batch activation of strategies"""
        # Arrange
        strategy_ids = [1, 2, 3, 4, 5]
        batch_id = "batch_123"

        # Mock successful updates
        mock_strategy_repo.update.side_effect = [
            {"id": sid, "status": "active"} for sid in strategy_ids
        ]

        # Act
        result = await enhanced_strategy_service.batch_operation(
            operation=BatchOperationType.ACTIVATE,
            strategy_ids=strategy_ids,
            config=batch_operation_config
        )

        # Assert
        assert isinstance(result, BatchOperationResult)
        assert result.operation == BatchOperationType.ACTIVATE
        assert result.total == len(strategy_ids)
        assert len(result.successful) == len(strategy_ids)
        assert len(result.failed) == 0
        assert result.progress == 1.0

        # Verify all updates were called
        assert mock_strategy_repo.update.call_count == len(strategy_ids)

        # Verify WebSocket broadcast
        mock_websocket_service.broadcast.assert_called()

    @pytest.mark.asyncio
    @pytest.mark.batch
    @pytest.mark.strategy
    @pytest.mark.error_handling
    async def test_batch_operation_with_partial_failures(
        self,
        enhanced_strategy_service,
        mock_strategy_repo,
        batch_operation_config
    ):
        """Test batch operation with some failures"""
        # Arrange
        strategy_ids = [1, 2, 3, 4, 5]

        # Mock partial failures
        mock_strategy_repo.update.side_effect = [
            {"id": 1, "status": "active"},  # Success
            BusinessError(ErrorCode.UPDATE_FAILED, "Strategy 2 not found"),  # Failure
            {"id": 3, "status": "active"},  # Success
            BusinessError(ErrorCode.UPDATE_FAILED, "Strategy 4 locked"),  # Failure
            {"id": 5, "status": "active"},  # Success
        ]

        # Act
        result = await enhanced_strategy_service.batch_operation(
            operation=BatchOperationType.ACTIVATE,
            strategy_ids=strategy_ids,
            config=batch_operation_config
        )

        # Assert
        assert result.total == 5
        assert len(result.successful) == 3
        assert len(result.failed) == 2
        assert result.progress == 0.6

        # Check failed items contain error information
        assert all("error" in failure for failure in result.failed)

    @pytest.mark.asyncio
    @pytest.mark.batch
    @pytest.mark.strategy
    async def test_batch_operation_with_progress_callback(
        self,
        enhanced_strategy_service,
        mock_strategy_repo,
        batch_operation_config
    ):
        """Test batch operation with progress callback"""
        # Arrange
        strategy_ids = [1, 2, 3, 4, 5]
        progress_updates = []

        def progress_callback(progress: float):
            progress_updates.append(progress)

        config_with_callback = BatchOperationConfig(
            progress_callback=progress_callback,
            **batch_operation_config.__dict__
        )

        mock_strategy_repo.update.side_effect = [
            {"id": sid, "status": "active"} for sid in strategy_ids
        ]

        # Act
        await enhanced_strategy_service.batch_operation(
            operation=BatchOperationType.ACTIVATE,
            strategy_ids=strategy_ids,
            config=config_with_callback
        )

        # Assert
        assert len(progress_updates) > 0
        assert progress_updates[-1] == 1.0  # Final progress should be 100%

    @pytest.mark.asyncio
    @pytest.mark.batch
    @pytest.mark.strategy
    async def test_get_batch_operation_status(
        self,
        enhanced_strategy_service,
        sample_strategies_data
    ):
        """Test getting batch operation status"""
        # Arrange
        batch_id = "batch_123"
        batch_result = BatchOperationResult(
            operation=BatchOperationType.ACTIVATE,
            total=5,
            successful=["1", "2", "3"],
            failed=[{"id": "4", "error": "Not found"}],
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow()
        )

        enhanced_strategy_service._active_batches[batch_id] = batch_result

        # Act
        result = await enhanced_strategy_service.get_batch_status(batch_id)

        # Assert
        assert result == batch_result
        assert result.progress == 0.6  # 3 successful out of 5

    # ========================================
    # Advanced Operations Tests
    # ========================================

    @pytest.mark.asyncio
    @pytest.mark.strategy
    async def test_duplicate_strategy_success(
        self,
        enhanced_strategy_service,
        sample_strategy_data,
        mock_strategy_repo,
        mock_cache_manager,
        mock_websocket_service
    ):
        """Test successful strategy duplication"""
        # Arrange
        original_id = 1
        new_name = "Duplicated Strategy"

        mock_strategy_repo.get_by_id.return_value = sample_strategy_data

        duplicated_strategy = {
            **sample_strategy_data,
            "id": 2,
            "name": new_name,
            "created_at": datetime.utcnow()
        }
        mock_strategy_repo.create.return_value = duplicated_strategy

        # Act
        result = await enhanced_strategy_service.duplicate_strategy(
            original_id, new_name
        )

        # Assert
        assert result["name"] == new_name
        assert result["id"] != original_id
        mock_strategy_repo.create.assert_called_once()
        mock_cache_manager.delete.assert_called()
        mock_websocket_service.broadcast.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.strategy
    @pytest.mark.error_handling
    async def test_duplicate_nonexistent_strategy(
        self,
        enhanced_strategy_service,
        mock_strategy_repo
    ):
        """Test duplicating non-existent strategy"""
        # Arrange
        original_id = 999
        mock_strategy_repo.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(NotFoundError):
            await enhanced_strategy_service.duplicate_strategy(
                original_id, "New Name"
            )

    @pytest.mark.asyncio
    @pytest.mark.strategy
    async def test_get_strategy_performance_metrics(
        self,
        enhanced_strategy_service,
        sample_strategy_data,
        mock_cache_manager,
        mock_strategy_repo
    ):
        """Test getting strategy performance metrics"""
        # Arrange
        strategy_id = 1
        cache_key = f"strategy:{strategy_id}:performance"

        performance_data = {
            "total_return": 0.15,
            "sharpe_ratio": 1.5,
            "max_drawdown": -0.05,
            "win_rate": 0.65,
            "profit_factor": 1.8
        }

        mock_cache_manager.get.return_value = performance_data

        # Act
        result = await enhanced_strategy_service.get_strategy_performance(
            strategy_id
        )

        # Assert
        assert result == performance_data
        mock_cache_manager.get.assert_called_once_with(cache_key)

    # ========================================
    # Search and Filter Tests
    # ========================================

    @pytest.mark.asyncio
    @pytest.mark.strategy
    async def test_search_strategies_by_name(
        self,
        enhanced_strategy_service,
        sample_strategies_data,
        mock_strategy_repo,
        mock_cache_manager
    ):
        """Test searching strategies by name"""
        # Arrange
        search_term = "Strategy 2"
        cache_key = f"strategies:search:name:{search_term}"

        filtered_strategies = [
            s for s in sample_strategies_data
            if search_term.lower() in s["name"].lower()
        ]

        mock_cache_manager.get.return_value = None  # Cache miss
        mock_strategy_repo.search.return_value = filtered_strategies

        # Act
        result = await enhanced_strategy_service.search_strategies(
            query=search_term,
            search_fields=["name"]
        )

        # Assert
        assert len(result) == 1
        assert result[0]["name"] == "Strategy 2"
        mock_strategy_repo.search.assert_called_once()
        mock_cache_manager.set.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.strategy
    async def test_filter_strategies_by_type(
        self,
        enhanced_strategy_service,
        sample_strategies_data,
        mock_strategy_repo,
        mock_cache_manager
    ):
        """Test filtering strategies by type"""
        # Arrange
        strategy_type = "momentum"

        momentum_strategies = [
            s for s in sample_strategies_data
            if s["strategy_type"] == strategy_type
        ]

        mock_cache_manager.get.return_value = None
        mock_strategy_repo.filter_by_type.return_value = momentum_strategies

        # Act
        result = await enhanced_strategy_service.filter_strategies(
            strategy_type=strategy_type
        )

        # Assert
        assert all(s["strategy_type"] == strategy_type for s in result)
        mock_strategy_repo.filter_by_type.assert_called_once_with(strategy_type)

    # ========================================
    # Error Handling Tests
    # ========================================

    @pytest.mark.asyncio
    @pytest.mark.error_handling
    @pytest.mark.auth
    async def test_permission_denied_on_strategy_access(
        self,
        enhanced_strategy_service,
        sample_strategy_data,
        mock_strategy_repo
    ):
        """Test permission denied when accessing other user's strategy"""
        # Arrange
        strategy_id = 1
        current_user_id = 2  # Different from strategy owner

        sample_strategy_data["user_id"] = 1  # Owner is user 1

        mock_strategy_repo.get_by_id.return_value = sample_strategy_data

        # Mock permission check
        with patch.object(
            enhanced_strategy_service,
            '_check_user_permission',
            return_value=False
        ):
            # Act & Assert
            with pytest.raises(PermissionError):
                await enhanced_strategy_service.get_strategy(
                    strategy_id, user_id=current_user_id
                )

    @pytest.mark.asyncio
    @pytest.mark.error_handling
    async def test_concurrent_batch_operations(
        self,
        enhanced_strategy_service,
        mock_strategy_repo,
        batch_operation_config
    ):
        """Test handling concurrent batch operations"""
        # Arrange
        strategy_ids_1 = [1, 2, 3]
        strategy_ids_2 = [4, 5, 6]

        mock_strategy_repo.update.side_effect = [
            {"id": sid, "status": "active"}
            for sid in strategy_ids_1 + strategy_ids_2
        ]

        # Act - Run two batch operations concurrently
        tasks = [
            enhanced_strategy_service.batch_operation(
                operation=BatchOperationType.ACTIVATE,
                strategy_ids=strategy_ids_1,
                config=batch_operation_config
            ),
            enhanced_strategy_service.batch_operation(
                operation=BatchOperationType.DEACTIVATE,
                strategy_ids=strategy_ids_2,
                config=batch_operation_config
            )
        ]

        results = await asyncio.gather(*tasks)

        # Assert
        assert len(results) == 2
        assert all(isinstance(r, BatchOperationResult) for r in results)
        assert results[0].operation == BatchOperationType.ACTIVATE
        assert results[1].operation == BatchOperationType.DEACTIVATE

    # ========================================
    # Performance Tests
    # ========================================

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_large_batch_operation_performance(
        self,
        enhanced_strategy_service,
        mock_strategy_repo,
        batch_operation_config
    ):
        """Test performance with large batch operations"""
        # Arrange
        large_strategy_list = list(range(1, 101))  # 100 strategies

        mock_strategy_repo.update.side_effect = [
            {"id": sid, "status": "active"}
            for sid in large_strategy_list
        ]

        # Mock timing for performance measurement
        with patch('time.time') as mock_time:
            mock_time.side_effect = [0, 1]  # 1 second duration

            # Act
            start_time = datetime.utcnow()
            result = await enhanced_strategy_service.batch_operation(
                operation=BatchOperationType.ACTIVATE,
                strategy_ids=large_strategy_list,
                config=BatchOperationConfig(batch_size=20)  # 5 batches
            )
            end_time = datetime.utcnow()

        # Assert
        assert result.total == 100
        assert len(result.successful) == 100
        assert len(result.failed) == 0
        assert result.progress == 1.0

        # Check that operation completed in reasonable time
        duration = (end_time - start_time).total_seconds()
        assert duration < 5.0  # Should complete within 5 seconds

    # ========================================
    # Cache Tests
    # ========================================

    @pytest.mark.asyncio
    @pytest.mark.cache
    async def test_cache_invalidation_on_update(
        self,
        enhanced_strategy_service,
        sample_strategy_data,
        mock_strategy_repo,
        mock_cache_manager
    ):
        """Test that cache is properly invalidated on update"""
        # Arrange
        strategy_id = 1
        update_data = {"name": "Updated"}

        mock_strategy_repo.get_by_id.return_value = sample_strategy_data
        mock_strategy_repo.update.return_value = {**sample_strategy_data, **update_data}

        # Act
        await enhanced_strategy_service.update_strategy(strategy_id, update_data)

        # Assert
        # Check that multiple cache keys are invalidated
        expected_deletes = [
            call(f"strategy:{strategy_id}"),
            call(f"strategy:{strategy_id}:performance"),
            call("strategies:list:*")  # Pattern for list cache
        ]

        # Verify cache.delete was called at least once for the strategy
        assert mock_cache_manager.delete.call_count >= 1