"""
Strategy Category API v2 Endpoints
策略分類API v2端點實現

Category management endpoints for strategy classification
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status, Path
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from src.dependencies import get_db
from src.services.strategy_service_v2 import StrategyServiceV2
from src.schemas.strategy_schemas import (
    StrategyCategoryCreate,
    StrategyCategoryUpdate,
    StrategyCategoryResponse
)

logger = logging.getLogger(__name__)

# Create router for categories
category_router = APIRouter(prefix="/strategy-categories", tags=["strategy-categories"])


def get_strategy_service(db: AsyncSession) -> StrategyServiceV2:
    """Get strategy service instance with database session"""
    return StrategyServiceV2(db)


@category_router.get(
    "",
    response_model=None,  # Using plain dict response
    summary="List categories",
    description="Retrieve a list of strategy categories with hierarchy support"
)
async def list_categories(
    parent_id: Optional[UUID] = Query(None, description="Filter by parent category"),
    level: Optional[int] = Query(None, ge=0, le=5, description="Filter by category level"),
    is_active: bool = Query(True, description="Filter by active status"),
    include_children: bool = Query(False, description="Include child categories"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of strategy categories

    Args:
        parent_id: Filter by parent category
        level: Filter by category level
        is_active: Filter by active status
        include_children: Include child categories
        db: Database session

    Returns:
        List of strategy categories
    """
    try:
        # Build filters
        filters = {
            "is_active": is_active
        }
        if parent_id:
            filters["parent_id"] = str(parent_id)
        if level is not None:
            filters["level"] = level

        # Get categories
        categories = await strategy_service.list_categories(
            db=db,
            filters=filters,
            include_children=include_children
        )

        return Dict[str, Any](
            categories=[
                StrategyCategoryResponse.from_model(cat) for cat in categories
            ]
        )

    except Exception as e:
        logger.error(f"Failed to list categories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list categories: {str(e)}"
        )


@category_router.get(
    "/tree",
    response_model=List[Dict[str, Any]],
    summary="Get category tree",
    description="Retrieve the full category tree structure"
)
async def get_category_tree(
    is_active: bool = Query(True, description="Filter by active status"),
    max_depth: int = Query(5, ge=1, le=10, description="Maximum tree depth"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get strategy category tree

    Args:
        is_active: Filter by active status
        max_depth: Maximum tree depth
        db: Database session

    Returns:
        Category tree structure
    """
    try:
        # Build filters
        filters = {
            "is_active": is_active
        }

        # Get category tree
        tree = await strategy_service.get_category_tree(
            db=db,
            filters=filters,
            max_depth=max_depth
        )

        return tree

    except Exception as e:
        logger.error(f"Failed to get category tree: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get category tree: {str(e)}"
        )


@category_router.post(
    "",
    response_model=StrategyCategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create category",
    description="Create a new strategy category"
)
async def create_category(
    category_data: StrategyCategoryCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new strategy category

    Args:
        category_data: Category creation data
        db: Database session

    Returns:
        Created category details
    """
    try:
        # Validate parent if provided
        if category_data.parent_id:
            parent = await strategy_service.get_category_by_id(db, category_data.parent_id)
            if not parent:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Parent category not found"
                )

        # Create category
        category = await strategy_service.create_category(
            db=db,
            category_data=category_data
        )

        return StrategyCategoryResponse.from_model(category)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create category: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create category: {str(e)}"
        )


@category_router.get(
    "/{category_id}",
    response_model=StrategyCategoryResponse,
    summary="Get category details",
    description="Retrieve detailed information about a specific category"
)
async def get_category(
    category_id: UUID = Path(..., description="Category UUID"),
    include_children: bool = Query(False, description="Include child categories"),
    include_strategy_count: bool = Query(False, description="Include strategy count"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get category by ID

    Args:
        category_id: Category UUID
        include_children: Include child categories
        include_strategy_count: Include strategy count
        db: Database session

    Returns:
        Category details
    """
    try:
        category = await strategy_service.get_category_by_id(
            db=db,
            category_id=category_id,
            include_children=include_children,
            include_strategy_count=include_strategy_count
        )

        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )

        return StrategyCategoryResponse.from_model(category)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get category {category_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get category: {str(e)}"
        )


@category_router.put(
    "/{category_id}",
    response_model=StrategyCategoryResponse,
    summary="Update category",
    description="Update category information"
)
async def update_category(
    category_data: StrategyCategoryUpdate,
    category_id: UUID = Path(..., description="Category UUID"),
    db: AsyncSession = Depends(get_db)
):
    """
    Update category

    Args:
        category_id: Category UUID
        category_data: Category update data
        db: Database session

    Returns:
        Updated category details
    """
    try:
        # Check if category exists
        existing_category = await strategy_service.get_category_by_id(db, category_id)
        if not existing_category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )

        # Validate new parent if provided
        if category_data.parent_id:
            # Check if setting parent to self
            if category_data.parent_id == category_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Category cannot be its own parent"
                )

            # Check if creating a circular reference
            if await strategy_service.would_create_circular_reference(
                db, category_id, category_data.parent_id
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Circular reference detected in category hierarchy"
                )

            # Check if parent exists
            parent = await strategy_service.get_category_by_id(db, category_data.parent_id)
            if not parent:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Parent category not found"
                )

        # Update category
        category = await strategy_service.update_category(
            db=db,
            category_id=category_id,
            category_data=category_data
        )

        return StrategyCategoryResponse.from_model(category)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update category {category_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update category: {str(e)}"
        )


@category_router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete category",
    description="Delete a category (only if no strategies are assigned)"
)
async def delete_category(
    category_id: UUID = Path(..., description="Category UUID"),
    force: bool = Query(False, description="Force delete (reassign strategies to parent)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete category

    Args:
        category_id: Category UUID
        force: Force delete (reassign strategies to parent)
        db: Database session
    """
    try:
        # Check if category exists
        existing_category = await strategy_service.get_category_by_id(db, category_id)
        if not existing_category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )

        # Check if category has strategies
        strategy_count = await strategy_service.count_strategies_in_category(db, category_id)
        if strategy_count > 0 and not force:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete category with {strategy_count} strategies. Use force=true to reassign strategies to parent"
            )

        # Check if category has children
        children_count = await strategy_service.count_child_categories(db, category_id)
        if children_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete category with {children_count} child categories"
            )

        # Delete category
        success = await strategy_service.delete_category(
            db=db,
            category_id=category_id,
            force=force
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete category"
            )

        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete category {category_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete category: {str(e)}"
        )


@category_router.get(
    "/{category_id}/strategies",
    summary="Get category strategies",
    description="Get all strategies in a specific category"
)
async def get_category_strategies(
    category_id: UUID = Path(..., description="Category UUID"),
    include_children: bool = Query(False, description="Include strategies from child categories"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of records to return"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get strategies in category

    Args:
        category_id: Category UUID
        include_children: Include strategies from child categories
        skip: Number of records to skip
        limit: Number of records to return
        db: Database session

    Returns:
        List of strategies in the category
    """
    try:
        # Check if category exists
        category = await strategy_service.get_category_by_id(db, category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )

        # Get strategies
        strategies = await strategy_service.get_strategies_in_category(
            db=db,
            category_id=category_id,
            include_children=include_children,
            skip=skip,
            limit=limit
        )

        return strategies

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get category strategies {category_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get category strategies: {str(e)}"
        )