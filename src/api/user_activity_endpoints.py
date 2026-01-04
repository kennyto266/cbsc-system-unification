"""
用戶活動追蹤API端點
User Activity Tracking API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
import logging
import json
import uuid

from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_
from pydantic import BaseModel, Field

from ..models.user_activity import (
    UserActivity, UserSession, UserBehaviorPattern, UserFeatureUsage,
    UserPersona, UserEngagementMetric,
    UserActivityCreateSchema, UserActivityResponseSchema,
    UserSessionResponseSchema, UserBehaviorPatternResponseSchema,
    UserFeatureUsageResponseSchema, UserPersonaResponseSchema,
    UserEngagementMetricResponseSchema
)
from ..models.user import User
from ..core.database import get_db

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 創建路由器
router = APIRouter(prefix="/api/user/activity", tags=["用戶活動追蹤"])

# 依賴注入
def get_current_user():
    """獲取當前用戶"""
    # 這裡應該從認證中間件獲取當前用戶
    # 暫時返回一個模擬用戶
    pass

def get_client_info(request):
    """獲取客戶端信息"""
    return {
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
        "referrer": request.headers.get("referrer")
    }

# Pydantic模型
class ActivityCreate(BaseModel):
    """創建活動模型"""
    activity_type: str = Field(..., description="活動類型")
    action: str = Field(..., description="操作")
    resource: Optional[str] = Field(None, description="資源")
    resource_id: Optional[str] = Field(None, description="資源ID")
    page_url: Optional[str] = Field(None, description="頁面URL")
    page_title: Optional[str] = Field(None, description="頁面標題")
    page_category: Optional[str] = Field(None, description="頁面分類")
    feature: Optional[str] = Field(None, description="功能")
    module: Optional[str] = Field(None, description="模塊")
    component: Optional[str] = Field(None, description="組件")
    response_time: Optional[float] = Field(None, description="響應時間")
    load_time: Optional[float] = Field(None, description="加載時間")
    status: str = Field("success", description="狀態")
    error_code: Optional[str] = Field(None, description="錯誤代碼")
    error_message: Optional[str] = Field(None, description="錯誤消息")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元數據")
    tags: Optional[List[str]] = Field(None, description="標籤")

class ActivityQuery(BaseModel):
    """活動查詢模型"""
    activity_type: Optional[str] = Field(None, description="活動類型")
    action: Optional[str] = Field(None, description="操作")
    feature: Optional[str] = Field(None, description="功能")
    module: Optional[str] = Field(None, description="模塊")
    status: Optional[str] = Field(None, description="狀態")
    start_date: Optional[datetime] = Field(None, description="開始日期")
    end_date: Optional[datetime] = Field(None, description="結束日期")

# 活動記錄端點
@router.post("/track")
async def track_activity(
    activity: ActivityCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """記錄用戶活動"""
    try:
        # 獲取當前會話（如果存在）
        session_id = None
        active_session = db.query(UserSession).filter(
            UserSession.user_id == current_user.id,
            UserSession.is_active == True
        ).first()

        if active_session:
            session_id = active_session.session_id
            # 更新會話最後活動時間
            active_session.last_activity_at = datetime.now(timezone.utc)

            # 更新會話統計
            if activity.activity_type == "page_view":
                active_session.page_views += 1
            elif activity.activity_type == "click":
                active_session.clicks += 1
            elif activity.activity_type == "api_call":
                active_session.api_calls += 1
            elif activity.status == "error":
                active_session.errors += 1

            db.commit()

        # 創建活動記錄
        new_activity = UserActivity(
            user_id=current_user.id,
            session_id=session_id,
            **activity.dict()
        )

        db.add(new_activity)
        db.commit()

        # 後台任務：更新用戶畫像和行為模式
        background_tasks.add_task(
            update_user_analytics,
            current_user.id,
            activity.dict()
        )

        return {"message": "活動記錄成功", "activity_id": new_activity.id}

    except Exception as e:
        logger.error(f"記錄用戶活動失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="記錄用戶活動失敗"
        )

@router.get("/activities", response_model=List[UserActivityResponseSchema])
async def get_user_activities(
    limit: int = Query(50, le=100, description="限制數量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    activity_type: Optional[str] = Query(None, description="活動類型"),
    start_date: Optional[datetime] = Query(None, description="開始日期"),
    end_date: Optional[datetime] = Query(None, description="結束日期"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """獲取用戶活動列表"""
    try:
        query = db.query(UserActivity).filter(
            UserActivity.user_id == current_user.id
        )

        # 應用過濾器
        if activity_type:
            query = query.filter(UserActivity.activity_type == activity_type)

        if start_date:
            query = query.filter(UserActivity.created_at >= start_date)

        if end_date:
            query = query.filter(UserActivity.created_at <= end_date)

        # 排序和分頁
        activities = query.order_by(desc(UserActivity.created_at))\
                        .offset(offset)\
                        .limit(limit)\
                        .all()

        return activities

    except Exception as e:
        logger.error(f"獲取用戶活動失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取用戶活動失敗"
        )

@router.get("/activities/statistics")
async def get_activity_statistics(
    period: str = Query("7d", description="統計周期: 1d, 7d, 30d, 90d"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """獲取活動統計"""
    try:
        # 計算日期範圍
        now = datetime.now(timezone.utc)
        if period == "1d":
            start_date = now - timedelta(days=1)
        elif period == "7d":
            start_date = now - timedelta(days=7)
        elif period == "30d":
            start_date = now - timedelta(days=30)
        elif period == "90d":
            start_date = now - timedelta(days=90)
        else:
            start_date = now - timedelta(days=7)

        # 基本統計
        total_activities = db.query(func.count(UserActivity.id)).filter(
            UserActivity.user_id == current_user.id,
            UserActivity.created_at >= start_date
        ).scalar()

        # 活動類型統計
        activity_types = db.query(
            UserActivity.activity_type,
            func.count(UserActivity.id).label('count')
        ).filter(
            UserActivity.user_id == current_user.id,
            UserActivity.created_at >= start_date
        ).group_by(UserActivity.activity_type).all()

        # 功能使用統計
        top_features = db.query(
            UserActivity.feature,
            func.count(UserActivity.id).label('count')
        ).filter(
            UserActivity.user_id == current_user.id,
            UserActivity.created_at >= start_date,
            UserActivity.feature.isnot(None)
        ).group_by(UserActivity.feature)\
         .order_by(desc('count'))\
         .limit(10).all()

        # 錯誤統計
        error_count = db.query(func.count(UserActivity.id)).filter(
            UserActivity.user_id == current_user.id,
            UserActivity.created_at >= start_date,
            UserActivity.status == "error"
        ).scalar()

        # 活躍天數
        active_days = db.query(
            func.count(func.distinct(func.date(UserActivity.created_at)))
        ).filter(
            UserActivity.user_id == current_user.id,
            UserActivity.created_at >= start_date
        ).scalar()

        # 平均響應時間
        avg_response_time = db.query(
            func.avg(UserActivity.response_time)
        ).filter(
            UserActivity.user_id == current_user.id,
            UserActivity.created_at >= start_date,
            UserActivity.response_time.isnot(None)
        ).scalar()

        statistics = {
            "period": period,
            "total_activities": total_activities,
            "activity_types": [
                {"type": at[0], "count": at[1]} for at in activity_types
            ],
            "top_features": [
                {"feature": tf[0], "count": tf[1]} for tf in top_features
            ],
            "error_count": error_count,
            "error_rate": round(error_count / max(total_activities, 1) * 100, 2),
            "active_days": active_days,
            "avg_response_time": round(avg_response_time or 0, 2)
        }

        return statistics

    except Exception as e:
        logger.error(f"獲取活動統計失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取活動統計失敗"
        )

# 會話管理端點
@router.post("/sessions/start")
async def start_session(
    session_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """開始新的會話"""
    try:
        # 結束之前的活躍會話
        db.query(UserSession).filter(
            UserSession.user_id == current_user.id,
            UserSession.is_active == True
        ).update({"is_active": False, "ended_at": datetime.now(timezone.utc)})

        # 創建新會話
        new_session = UserSession(
            user_id=current_user.id,
            session_id=str(uuid.uuid4()),
            session_token=str(uuid.uuid4()),
            ip_address=session_data.get("ip_address"),
            user_agent=session_data.get("user_agent"),
            device_type=session_data.get("device_type"),
            browser=session_data.get("browser"),
            browser_version=session_data.get("browser_version"),
            os=session_data.get("os"),
            os_version=session_data.get("os_version"),
            location=session_data.get("location")
        )

        db.add(new_session)
        db.commit()
        db.refresh(new_session)

        return {
            "message": "會話開始成功",
            "session_id": new_session.session_id,
            "session_token": new_session.session_token
        }

    except Exception as e:
        logger.error(f"開始會話失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="開始會話失敗"
        )

@router.post("/sessions/{session_id}/end")
async def end_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """結束會話"""
    try:
        # 獲取會話
        session = db.query(UserSession).filter(
            UserSession.session_id == session_id,
            UserSession.user_id == current_user.id,
            UserSession.is_active == True
        ).first()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="會話不存在或已結束"
            )

        # 計算會話持續時間
        session.ended_at = datetime.now(timezone.utc)
        session.duration = int((session.ended_at - session.started_at).total_seconds())
        session.is_active = False

        db.commit()

        return {
            "message": "會話結束成功",
            "duration": session.duration,
            "page_views": session.page_views,
            "clicks": session.clicks,
            "api_calls": session.api_calls,
            "errors": session.errors
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"結束會話失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="結束會話失敗"
        )

@router.get("/sessions", response_model=List[UserSessionResponseSchema])
async def get_user_sessions(
    limit: int = Query(20, le=50, description="限制數量"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """獲取用戶會話列表"""
    try:
        sessions = db.query(UserSession).filter(
            UserSession.user_id == current_user.id
        ).order_by(desc(UserSession.started_at))\
         .limit(limit)\
         .all()

        return sessions

    except Exception as e:
        logger.error(f"獲取用戶會話失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取用戶會話失敗"
        )

# 功能使用統計端點
@router.get("/features/usage")
async def get_feature_usage(
    period: str = Query("30d", description="統計周期"),
    feature: Optional[str] = Query(None, description="功能名稱"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """獲取功能使用統計"""
    try:
        # 計算日期範圍
        now = datetime.now(timezone.utc)
        if period == "7d":
            start_date = now - timedelta(days=7)
        elif period == "30d":
            start_date = now - timedelta(days=30)
        elif period == "90d":
            start_date = now - timedelta(days=90)
        else:
            start_date = now - timedelta(days=30)

        # 查詢功能使用統計
        query = db.query(UserFeatureUsage).filter(
            UserFeatureUsage.user_id == current_user.id,
            UserFeatureUsage.period_end >= start_date
        )

        if feature:
            query = query.filter(UserFeatureUsage.feature == feature)

        usage_stats = query.order_by(desc(UserFeatureUsage.period_end)).all()

        return usage_stats

    except Exception as e:
        logger.error(f"獲取功能使用統計失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取功能使用統計失敗"
        )

@router.get("/features/popular")
async def get_popular_features(
    period: str = Query("30d", description="統計周期"),
    limit: int = Query(10, le=20, description="限制數量"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """獲取熱門功能"""
    try:
        # 計算日期範圍
        now = datetime.now(timezone.utc)
        if period == "7d":
            start_date = now - timedelta(days=7)
        elif period == "30d":
            start_date = now - timedelta(days=30)
        elif period == "90d":
            start_date = now - timedelta(days=90)
        else:
            start_date = now - timedelta(days=30)

        # 從活動記錄中統計功能使用
        popular_features = db.query(
            UserActivity.feature,
            func.count(UserActivity.id).label('usage_count'),
            func.count(func.distinct(func.date(UserActivity.created_at))).label('unique_days')
        ).filter(
            UserActivity.user_id == current_user.id,
            UserActivity.created_at >= start_date,
            UserActivity.feature.isnot(None)
        ).group_by(UserActivity.feature)\
         .order_by(desc('usage_count'))\
         .limit(limit)\
         .all()

        return [
            {
                "feature": pf[0],
                "usage_count": pf[1],
                "unique_days": pf[2],
                "frequency": round(pf[1] / max(pf[2], 1), 1)
            }
            for pf in popular_features
        ]

    except Exception as e:
        logger.error(f"獲取熱門功能失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取熱門功能失敗"
        )

# 用戶畫像端點
@router.get("/persona", response_model=UserPersonaResponseSchema)
async def get_user_persona(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """獲取用戶畫像"""
    try:
        # 獲取用戶畫像
        persona = db.query(UserPersona).filter(
            UserPersona.user_id == current_user.id
        ).first()

        if not persona:
            # 如果沒有畫像，觸發分析
            background_tasks = BackgroundTasks()
            background_tasks.add_task(generate_user_persona, current_user.id, db)

            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用戶畫像尚未生成，正在分析中..."
            )

        return persona

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取用戶畫像失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取用戶畫像失敗"
        )

@router.post("/persona/generate")
async def generate_user_persona_endpoint(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """生成用戶畫像"""
    try:
        # 後台生成畫像
        background_tasks.add_task(generate_user_persona, current_user.id, db)

        return {"message": "用戶畫像生成已開始，請稍後查看"}

    except Exception as e:
        logger.error(f"生成用戶畫像失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="生成用戶畫像失敗"
        )

# 參與度指標端點
@router.get("/engagement")
async def get_engagement_metrics(
    period: str = Query("30d", description="統計周期"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """獲取用戶參與度指標"""
    try:
        # 計算日期範圍
        now = datetime.now(timezone.utc)
        if period == "7d":
            start_date = now - timedelta(days=7)
        elif period == "30d":
            start_date = now - timedelta(days=30)
        elif period == "90d":
            start_date = now - timedelta(days=90)
        else:
            start_date = now - timedelta(days=30)

        # 獲取參與度指標
        metrics = db.query(UserEngagementMetric).filter(
            UserEngagementMetric.user_id == current_user.id,
            UserEngagementMetric.metric_date >= start_date
        ).order_by(desc(UserEngagementMetric.metric_date)).all()

        # 如果沒有指標，生成默認指標
        if not metrics:
            metrics = [generate_default_engagement_metrics(current_user.id, start_date, now)]

        return metrics

    except Exception as e:
        logger.error(f"獲取參與度指標失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取參與度指標失敗"
        )

# 輔助函數
async def update_user_analytics(user_id: str, activity_data: Dict[str, Any], db: Session):
    """更新用戶分析數據"""
    try:
        # 更新功能使用統計
        if activity_data.get("feature"):
            update_feature_usage(user_id, activity_data["feature"], db)

        # 更新行為模式（異步）
        # 這裡可以添加更複雜的行為模式分析邏輯

    except Exception as e:
        logger.error(f"更新用戶分析失敗: {e}")

def update_feature_usage(user_id: str, feature: str, db: Session):
    """更新功能使用統計"""
    try:
        today = datetime.now(timezone.utc).date()
        period_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
        period_end = period_start + timedelta(days=1)

        # 查找或創建今日功能使用記錄
        usage = db.query(UserFeatureUsage).filter(
            UserFeatureUsage.user_id == user_id,
            UserFeatureUsage.feature == feature,
            UserFeatureUsage.period_type == "daily",
            UserFeatureUsage.period_start == period_start
        ).first()

        if not usage:
            usage = UserFeatureUsage(
                user_id=user_id,
                feature=feature,
                module=feature.split(".")[0] if "." in feature else "unknown",
                period_type="daily",
                period_start=period_start,
                period_end=period_end,
                usage_count=0
            )
            db.add(usage)

        # 更新使用次數
        usage.usage_count += 1
        usage.success_count += 1  # 假設默認成功
        usage.error_count += 0

        if usage.usage_count > 0:
            usage.success_rate = usage.success_count / usage.usage_count

        db.commit()

    except Exception as e:
        logger.error(f"更新功能使用統計失敗: {e}")

async def generate_user_persona(user_id: str, db: Session):
    """生成用戶畫像"""
    try:
        # 獲取最近90天的活動數據
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=90)

        # 統計用戶活動
        total_activities = db.query(func.count(UserActivity.id)).filter(
            UserActivity.user_id == user_id,
            UserActivity.created_at >= start_date
        ).scalar()

        # 獲取使用功能數
        unique_features = db.query(
            func.count(func.distinct(UserActivity.feature))
        ).filter(
            UserActivity.user_id == user_id,
            UserActivity.created_at >= start_date,
            UserActivity.feature.isnot(None)
        ).scalar()

        # 計算活躍天數
        active_days = db.query(
            func.count(func.distinct(func.date(UserActivity.created_at)))
        ).filter(
            UserActivity.user_id == user_id,
            UserActivity.created_at >= start_date
        ).scalar()

        # 獲取最常用的功能
        top_features = db.query(
            UserActivity.feature,
            func.count(UserActivity.id).label('count')
        ).filter(
            UserActivity.user_id == user_id,
            UserActivity.created_at >= start_date,
            UserActivity.feature.isnot(None)
        ).group_by(UserActivity.feature)\
         .order_by(desc('count'))\
         .limit(5)\
         .all()

        # 計算各項指標
        total_days = 90
        activity_rate = active_days / total_days

        # 確定用戶類型
        if activity_rate > 0.8:
            user_type = "expert"
        elif activity_rate > 0.5:
            user_type = "advanced"
        elif activity_rate > 0.2:
            user_type = "intermediate"
        else:
            user_type = "beginner"

        # 確定用戶分類
        features = [f[0] for f in top_features if f[0]]
        if any("trading" in f.lower() or "strategy" in f.lower() for f in features):
            user_category = "trader"
        elif any("analysis" in f.lower() or "report" in f.lower() for f in features):
            user_category = "analyst"
        elif any("api" in f.lower() or "develop" in f.lower() for f in features):
            user_category = "developer"
        else:
            user_category = "general"

        # 計算參與度分數
        engagement_score = min(100, (activity_rate * 50) + (unique_features * 5))

        # 確定活動水平
        if engagement_score > 80:
            activity_level = "high"
        elif engagement_score > 40:
            activity_level = "normal"
        else:
            activity_level = "low"

        # 創建或更新用戶畫像
        persona = db.query(UserPersona).filter(
            UserPersona.user_id == user_id
        ).first()

        if not persona:
            persona = UserPersona(user_id=user_id)
            db.add(persona)

        persona.user_type = user_type
        persona.user_category = user_category
        persona.preferred_features = {"features": features[:5]}
        persona.engagement_score = engagement_score
        persona.activity_level = activity_level
        persona.last_analyzed = end_date

        db.commit()

    except Exception as e:
        logger.error(f"生成用戶畫像失敗: {e}")

def generate_default_engagement_metrics(user_id: str, start_date: datetime, end_date: datetime):
    """生成默認參與度指標"""
    # 這裡應該根據實際數據計算指標
    # 暫時返回默認值
    return UserEngagementMetric(
        user_id=user_id,
        metric_date=start_date,
        period_type="daily",
        active_days=1,
        total_sessions=1,
        avg_session_duration=300.0,
        total_interactions=10,
        features_used=3,
        new_features_tried=0,
        core_feature_usage={},
        reports_generated=0,
        strategies_created=0,
        backtests_run=0,
        shares=0,
        comments=0,
        feedback_given=0,
        error_rate=0.0
    )