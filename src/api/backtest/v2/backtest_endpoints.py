"""
Backtest API Endpoints v2.0
RESTful API endpoints for backtest management
Phase 5.1 - 實施回測引擎集成
"""

from datetime import datetime, date
from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from sqlalchemy.orm import Session

from ...database import get_db
from ...services.backtest_service_v2 import BacktestServiceV2
from ...models.backtest_models_v2 import (
    Backtest as BacktestModel, BacktestStatus, BacktestMode
)
from ...core.auth import get_current_user
from ...models.user import User
from ...api.schemas.backtest_schemas import (
    BacktestCreate, BacktestResponse, BacktestUpdate,
    BacktestComparisonRequest, BacktestComparisonResponse,
    BacktestProgressResponse, BacktestListResponse
)

router = APIRouter(prefix="/backtest", tags=["backtest"])


def get_backtest_service(db: Session = Depends(get_db)) -> BacktestServiceV2:
    """Get backtest service instance"""
    return BacktestServiceV2(db)


@router.post("/", response_model=BacktestResponse, status_code=status.HTTP_201_CREATED)
async def create_backtest(
    backtest_data: BacktestCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    backtest_service: BacktestServiceV2 = Depends(get_backtest_service)
):
    """Create and run backtest"""
    try:
        # Create backtest record
        backtest = BacktestModel(
            name=backtest_data.name,
            strategy_id=backtest_data.strategy_id,
            user_id=current_user.id,
            symbols=backtest_data.symbols,
            start_date=backtest_data.start_date,
            end_date=backtest_data.end_date,
            initial_capital=backtest_data.initial_capital,
            parameters=backtest_data.parameters or {},
            status=BacktestStatus.PENDING
        )

        backtest_service.db.add(backtest)
        backtest_service.db.commit()
        backtest_service.db.refresh(backtest)

        # Run backtest in background
        background_tasks.add_task(
            run_backtest_background,
            backtest.id
        )

        return BacktestResponse.from_orm(backtest)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=List[BacktestResponse])
async def list_backtests(
    strategy_id: Optional[UUID] = Query(None, description="Filter by strategy ID"),
    status: Optional[BacktestStatus] = Query(None, description="Filter by status"),
    symbols: Optional[List[str]] = Query(None, description="Filter by symbols"),
    start_date_after: Optional[date] = Query(None, description="Filter by start date (after)"),
    start_date_before: Optional[date] = Query(None, description="Filter by start date (before)"),
    min_return: Optional[float] = Query(None, ge=-1, description="Minimum return"),
    max_drawdown: Optional[float] = Query(None, ge=0, le=1, description="Maximum drawdown"),
    min_sharpe: Optional[float] = Query(None, description="Minimum Sharpe ratio"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    current_user: User = Depends(get_current_user),
    backtest_service: BacktestServiceV2 = Depends(get_backtest_service)
):
    """List user's backtests"""
    try:
        backtests = backtest_service.get_backtests(
            user_id=current_user.id,
            strategy_id=strategy_id,
            status=status,
            symbols=symbols,
            start_date_after=start_date_after,
            start_date_before=start_date_before,
            min_return=min_return,
            max_drawdown=max_drawdown,
            min_sharpe=min_sharpe,
            limit=limit
        )

        return [BacktestResponse.from_orm(bt) for bt in backtests]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{backtest_id}", response_model=Dict[str, Any])
async def get_backtest(
    backtest_id: UUID,
    detailed: bool = Query(False, description="Include detailed results"),
    current_user: User = Depends(get_current_user),
    backtest_service: BacktestServiceV2 = Depends(get_backtest_service)
):
    """Get backtest details"""
    try:
        # Check access
        backtest = backtest_service.db.query(BacktestModel).filter(
            BacktestModel.id == backtest_id
        ).first()

        if not backtest:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Backtest not found"
            )

        # Check ownership
        if backtest.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        # Get detailed results
        results = backtest_service.get_backtest_results(backtest_id, detailed)

        return results

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/{backtest_id}", response_model=BacktestResponse)
async def update_backtest(
    backtest_id: UUID,
    update_data: BacktestUpdate,
    current_user: User = Depends(get_current_user),
    backtest_service: BacktestServiceV2 = Depends(get_backtest_service)
):
    """Update backtest configuration"""
    try:
        # Get backtest
        backtest = backtest_service.db.query(BacktestModel).filter(
            BacktestModel.id == backtest_id
        ).first()

        if not backtest:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Backtest not found"
            )

        # Check ownership
        if backtest.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        # Can only update pending backtests
        if backtest.status != BacktestStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only update pending backtests"
            )

        # Apply updates
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(backtest, field, value)

        backtest_service.db.commit()
        backtest_service.db.refresh(backtest)

        return BacktestResponse.from_orm(backtest)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{backtest_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_backtest(
    backtest_id: UUID,
    current_user: User = Depends(get_current_user),
    backtest_service: BacktestServiceV2 = Depends(get_backtest_service)
):
    """Delete backtest"""
    try:
        # Get backtest
        backtest = backtest_service.db.query(BacktestModel).filter(
            BacktestModel.id == backtest_id
        ).first()

        if not backtest:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Backtest not found"
            )

        # Check ownership
        if backtest.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        # Stop running backtest first
        if backtest.status == BacktestStatus.RUNNING:
            backtest_service.stop_backtest(backtest_id)

        # Delete backtest
        backtest_service.db.delete(backtest)
        backtest_service.db.commit()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{backtest_id}/run", status_code=status.HTTP_202_ACCEPTED)
async def run_backtest(
    backtest_id: UUID,
    data_source: Optional[Dict[str, Any]] = None,
    current_user: User = Depends(get_current_user),
    backtest_service: BacktestServiceV2 = Depends(get_backtest_service)
):
    """Run backtest"""
    try:
        # Check access
        backtest = backtest_service.db.query(BacktestModel).filter(
            BacktestModel.id == backtest_id
        ).first()

        if not backtest:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Backtest not found"
            )

        # Check ownership
        if backtest.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        # Can only run pending or failed backtests
        if backtest.status not in [BacktestStatus.PENDING, BacktestStatus.FAILED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Backtest must be in pending or failed status"
            )

        # Run backtest
        result = await backtest_service.run_backtest(backtest_id, data_source)

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{backtest_id}/stop", status_code=status.HTTP_200_OK)
async def stop_backtest(
    backtest_id: UUID,
    current_user: User = Depends(get_current_user),
    backtest_service: BacktestServiceV2 = Depends(get_backtest_service)
):
    """Stop running backtest"""
    try:
        # Check access
        backtest = backtest_service.db.query(BacktestModel).filter(
            BacktestModel.id == backtest_id
        ).first()

        if not backtest:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Backtest not found"
            )

        # Check ownership
        if backtest.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        # Stop backtest
        success = backtest_service.stop_backtest(backtest_id)

        if success:
            return {"message": "Backtest stopped successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Backtest is not running"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{backtest_id}/progress", response_model=BacktestProgressResponse)
async def get_backtest_progress(
    backtest_id: UUID,
    current_user: User = Depends(get_current_user),
    backtest_service: BacktestServiceV2 = Depends(get_backtest_service)
):
    """Get backtest progress"""
    try:
        # Check access
        backtest = backtest_service.db.query(BacktestModel).filter(
            BacktestModel.id == backtest_id
        ).first()

        if not backtest:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Backtest not found"
            )

        # Check ownership
        if backtest.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        # Estimate progress
        progress = backtest_service._estimate_progress(backtest)

        return BacktestProgressResponse(
            backtest_id=backtest_id,
            status=backtest.status,
            progress=progress,
            start_time=backtest.start_time,
            end_time=backtest.end_time,
            error_message=backtest.error_message
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/running", response_model=List[BacktestProgressResponse])
async def get_running_backtests(
    current_user: User = Depends(get_current_user),
    backtest_service: BacktestServiceV2 = Depends(get_backtest_service)
):
    """Get currently running backtests"""
    try:
        running_backtests = backtest_service.get_running_backtests()

        # Filter by user
        user_backtests = []
        for bt_info in running_backtests:
            # Check ownership
            backtest = backtest_service.db.query(BacktestModel).filter(
                BacktestModel.id == UUID(bt_info['backtest_id']),
                BacktestModel.user_id == current_user.id
            ).first()

            if backtest:
                user_backtests.append(BacktestProgressResponse(
                    backtest_id=backtest.id,
                    name=backtest.name,
                    status=backtest.status,
                    progress=bt_info['progress'],
                    start_time=backtest.start_time,
                    end_time=backtest.end_time,
                    error_message=backtest.error_message
                ))

        return user_backtests

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/compare", response_model=BacktestComparisonResponse)
async def compare_backtests(
    request: BacktestComparisonRequest,
    current_user: User = Depends(get_current_user),
    backtest_service: BacktestServiceV2 = Depends(get_backtest_service)
):
    """Compare multiple backtests"""
    try:
        # Verify ownership of all backtests
        backtest_models = backtest_service.db.query(BacktestModel).filter(
            BacktestModel.id.in_(request.backtest_ids),
            BacktestModel.user_id == current_user.id
        ).all()

        if len(backtest_models) != len(request.backtest_ids):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied for one or more backtests"
            )

        # Compare backtests
        comparison = backtest_service.compare_backtests(request.backtest_ids)

        return BacktestComparisonResponse(
            backtest_ids=request.backtest_ids,
            comparison=comparison['comparison'],
            individual_results=comparison['individual_results']
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/analytics/summary")
async def get_backtest_analytics(
    strategy_id: Optional[UUID] = Query(None, description="Filter by strategy ID"),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user),
    backtest_service: BacktestServiceV2 = Depends(get_backtest_service)
):
    """Get backtest analytics summary"""
    try:
        # Get user's backtests
        backtests = backtest_service.get_backtests(
            user_id=current_user.id,
            strategy_id=strategy_id,
            limit=None
        )

        if not backtests:
            return {
                'total_backtests': 0,
                'completed': 0,
                'running': 0,
                'failed': 0,
                'average_return': 0,
                'best_backtest': None,
                'recent_trends': []
            }

        # Calculate analytics
        total = len(backtests)
        completed = sum(1 for bt in backtests if bt.status == BacktestStatus.COMPLETED)
        running = sum(1 for bt in backtests if bt.status == BacktestStatus.RUNNING)
        failed = sum(1 for bt in backtests if bt.status == BacktestStatus.FAILED)

        # Performance metrics
        completed_backtests = [bt for bt in backtests if bt.status == BacktestStatus.COMPLETED]
        returns = [bt.total_return for bt in completed_backtests if bt.total_return is not None]
        avg_return = sum(returns) / len(returns) if returns else 0

        # Best backtest
        best_backtest = None
        if completed_backtests:
            best_bt = max(completed_backtests, key=lambda x: x.total_return or 0)
            best_backtest = {
                'id': str(best_bt.id),
                'name': best_bt.name,
                'total_return': best_bt.total_return,
                'sharpe_ratio': best_bt.sharpe_ratio
            }

        # Recent trends
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        recent_backtests = [bt for bt in backtests if bt.created_at >= cutoff_date]
        recent_trends = []
        for bt in recent_backtests[-10:]:  # Last 10 backtests
            recent_trends.append({
                'id': str(bt.id),
                'name': bt.name,
                'created_at': bt.created_at.isoformat(),
                'status': bt.status,
                'total_return': bt.total_return
            })

        return {
            'total_backtests': total,
            'completed': completed,
            'running': running,
            'failed': failed,
            'average_return': avg_return,
            'best_backtest': best_backtest,
            'recent_trends': recent_trends
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# Background task function
async def run_backtest_background(backtest_id: UUID):
    """Background task to run backtest"""
    from ...database import SessionLocal

    db = SessionLocal()
    try:
        backtest_service = BacktestServiceV2(db)
        await backtest_service.run_backtest(backtest_id)
    except Exception as e:
        logger.error(f"Background backtest failed: {e}")
    finally:
        db.close()