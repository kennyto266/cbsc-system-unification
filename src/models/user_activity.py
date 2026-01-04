"""
用戶活動追蹤模型

定義用戶行為追蹤、頁面訪問、功能使用統計和用戶畫像相關數據模型。
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON, ForeignKey, Integer, Float
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field

from .unified_base import UnifiedBaseModel, UnifiedSchema

class UserActivity(UnifiedBaseModel):
    """用戶活動記錄模型"""

    __tablename__ = 'user_activities'

    # 關聯用戶
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False, index=True)

    # 活動基本信息
    activity_type = Column(String(50), nullable=False, index=True)  # login, logout, page_view, click, api_call
    action = Column(String(100), nullable=False)  # 具體操作
    resource = Column(String(100), nullable=True)  # 操作的資源
    resource_id = Column(String(36), nullable=True)  # 資源ID

    # 上下文信息
    session_id = Column(String(255), nullable=True, index=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    referrer = Column(String(500), nullable=True)

    # 頁面信息（針對page_view類型）
    page_url = Column(String(500), nullable=True)
    page_title = Column(String(200), nullable=True)
    page_category = Column(String(50), nullable=True)

    # 功能信息
    feature = Column(String(100), nullable=True, index=True)
    module = Column(String(50), nullable=True, index=True)
    component = Column(String(100), nullable=True)

    # 性能信息
    response_time = Column(Float, nullable=True)  # 響應時間（毫秒）
    load_time = Column(Float, nullable=True)  # 頁面加載時間（毫秒）

    # 狀態信息
    status = Column(String(20), default='success', nullable=False)  # success, error, warning
    error_code = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)

    # 額外數據
    json_metadata = Column(JSONB, nullable=True)  # 活動相關的額外數據
    tags = Column(JSONB, nullable=True)  # 標籤

    # 關聯
    user = relationship("User")

class UserSession(UnifiedBaseModel):
    """用戶會話模型"""

    __tablename__ = 'user_sessions'

    # 關聯用戶
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False, index=True)

    # 會話信息
    session_id = Column(String(255), nullable=False, unique=True, index=True)
    session_token = Column(String(255), nullable=False, unique=True)

    # 時間信息
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    last_activity_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    ended_at = Column(DateTime(timezone=True), nullable=True)

    # 會話統計
    duration = Column(Integer, nullable=True)  # 會話持續時間（秒）
    page_views = Column(Integer, default=0, nullable=False)
    clicks = Column(Integer, default=0, nullable=False)
    api_calls = Column(Integer, default=0, nullable=False)
    errors = Column(Integer, default=0, nullable=False)

    # 上下文信息
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    device_type = Column(String(50), nullable=True)  # desktop, mobile, tablet
    browser = Column(String(50), nullable=True)
    browser_version = Column(String(20), nullable=True)
    os = Column(String(50), nullable=True)
    os_version = Column(String(20), nullable=True)
    location = Column(JSONB, nullable=True)  # 地理位置

    # 狀態
    is_active = Column(Boolean, default=True, nullable=False)

    # 關聯
    user = relationship("User")

class UserBehaviorPattern(UnifiedBaseModel):
    """用戶行為模式模型"""

    __tablename__ = 'user_behavior_patterns'

    # 關聯用戶
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False, index=True)

    # 模式信息
    pattern_type = Column(String(50), nullable=False)  # usage_frequency, preferred_features, working_hours
    pattern_name = Column(String(100), nullable=False)
    pattern_value = Column(JSONB, nullable=False)  # 模式數據

    # 統計信息
    confidence = Column(Float, default=0.0, nullable=False)  # 置信度
    frequency = Column(Float, default=0.0, nullable=False)  # 頻率
    last_updated = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # 狀態
    is_active = Column(Boolean, default=True, nullable=False)

    # 關聯
    user = relationship("User")

class UserFeatureUsage(UnifiedBaseModel):
    """用戶功能使用統計模型"""

    __tablename__ = 'user_feature_usage'

    # 關聯用戶
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False, index=True)

    # 功能信息
    feature = Column(String(100), nullable=False, index=True)
    module = Column(String(50), nullable=False, index=True)
    component = Column(String(100), nullable=True)

    # 統計周期
    period_type = Column(String(10), nullable=False)  # hourly, daily, weekly, monthly
    period_start = Column(DateTime(timezone=True), nullable=False, index=True)
    period_end = Column(DateTime(timezone=True), nullable=False)

    # 使用統計
    usage_count = Column(Integer, default=0, nullable=False)
    total_time = Column(Float, default=0.0, nullable=False)  # 總使用時間（秒）
    avg_session_time = Column(Float, default=0.0, nullable=False)  # 平均會話時間

    # 成功率統計
    success_count = Column(Integer, default=0, nullable=False)
    error_count = Column(Integer, default=0, nullable=False)
    success_rate = Column(Float, default=0.0, nullable=False)

    # 額外統計
    unique_days_used = Column(Integer, default=0, nullable=False)
    peak_usage_time = Column(String(5), nullable=True)  # HH:MM
    preferred_devices = Column(JSONB, nullable=True)

    # 關聯
    user = relationship("User")

class UserPersona(UnifiedBaseModel):
    """用戶畫像模型"""

    __tablename__ = 'user_personas'

    # 關聯用戶
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False, unique=True, index=True)

    # 用戶類型
    user_type = Column(String(50), nullable=False)  # beginner, intermediate, advanced, expert
    user_category = Column(String(50), nullable=False)  # trader, analyst, developer, admin

    # 使用偏好
    preferred_features = Column(JSONB, nullable=True)  # 偏好功能列表
    usage_patterns = Column(JSONB, nullable=True)  # 使用模式
    work_schedule = Column(JSONB, nullable=True)  # 工作時間安排

    # 技能水平
    technical_skill_level = Column(Integer, default=0, nullable=False)  # 0-10
    trading_experience = Column(Integer, default=0, nullable=False)  # 年數
    familiarity_score = Column(Float, default=0.0, nullable=False)  # 系統熟悉度

    # 行為特征
    risk_appetite = Column(String(20), default='moderate', nullable=False)  # low, moderate, high
    decision_style = Column(String(20), nullable=True)  # analytical, intuitive, collaborative
    learning_style = Column(String(20), nullable=True)  # visual, auditory, kinesthetic

    # 參與度
    engagement_score = Column(Float, default=0.0, nullable=False)
    activity_level = Column(String(20), default='normal', nullable=False)  # low, normal, high
    retention_score = Column(Float, default=0.0, nullable=False)

    # 預測信息
    churn_risk = Column(Float, default=0.0, nullable=False)  # 流失風險
    upsell_opportunity = Column(Float, default=0.0, nullable=False)  # 銷售機會
    next_actions = Column(JSONB, nullable=True)  # 預測的下一步操作

    # 更新信息
    last_analyzed = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    analysis_version = Column(String(20), default='1.0', nullable=False)

    # 關聯
    user = relationship("User")

class UserEngagementMetric(UnifiedBaseModel):
    """用戶參與度指標模型"""

    __tablename__ = 'user_engagement_metrics'

    # 關聯用戶
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False, index=True)

    # 時間周期
    metric_date = Column(DateTime(timezone=True), nullable=False, index=True)
    period_type = Column(String(10), nullable=False)  # daily, weekly, monthly

    # 活躍度指標
    active_days = Column(Integer, default=0, nullable=False)
    total_sessions = Column(Integer, default=0, nullable=False)
    avg_session_duration = Column(Float, default=0.0, nullable=False)
    total_interactions = Column(Integer, default=0, nullable=False)

    # 功能使用
    features_used = Column(Integer, default=0, nullable=False)
    new_features_tried = Column(Integer, default=0, nullable=False)
    core_feature_usage = Column(JSONB, nullable=True)

    # 內容參與
    reports_generated = Column(Integer, default=0, nullable=False)
    strategies_created = Column(Integer, default=0, nullable=False)
    backtests_run = Column(Integer, default=0, nullable=False)

    # 社交參與
    shares = Column(Integer, default=0, nullable=False)
    comments = Column(Integer, default=0, nullable=False)
    feedback_given = Column(Integer, default=0, nullable=False)

    # 質量指標
    error_rate = Column(Float, default=0.0, nullable=False)
    satisfaction_score = Column(Float, nullable=True)
    net_promoter_score = Column(Integer, nullable=True)

    # 關聯
    user = relationship("User")

# Pydantic Schemas
class UserActivityBaseSchema(UnifiedSchema):
    """用戶活動基礎Schema"""
    activity_type: str = Field(..., description="活動類型")
    action: str = Field(..., description="操作")
    resource: Optional[str] = Field(None, description="資源")
    resource_id: Optional[str] = Field(None, description="資源ID")
    session_id: Optional[str] = Field(None, description="會話ID")
    ip_address: Optional[str] = Field(None, description="IP地址")
    user_agent: Optional[str] = Field(None, description="用戶代理")
    referrer: Optional[str] = Field(None, description="來源頁面")
    page_url: Optional[str] = Field(None, description="頁面URL")
    page_title: Optional[str] = Field(None, description="頁面標題")
    page_category: Optional[str] = Field(None, description="頁面分類")
    feature: Optional[str] = Field(None, description="功能")
    module: Optional[str] = Field(None, description="模塊")
    component: Optional[str] = Field(None, description="組件")
    response_time: Optional[float] = Field(None, description="響應時間")
    load_time: Optional[float] = Field(None, description="加載時間")
    status: str = Field('success', description="狀態")
    error_code: Optional[str] = Field(None, description="錯誤代碼")
    error_message: Optional[str] = Field(None, description="錯誤消息")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元數據")
    tags: Optional[List[str]] = Field(None, description="標籤")

class UserActivityCreateSchema(UserActivityBaseSchema):
    """創建用戶活動Schema"""
    user_id: str = Field(..., description="用戶ID")

class UserActivityResponseSchema(UserActivityBaseSchema):
    """用戶活動響應Schema"""
    id: str
    user_id: str
    created_at: datetime

    class Config:
        from_attributes = True

class UserSessionBaseSchema(UnifiedSchema):
    """用戶會話基礎Schema"""
    session_id: str = Field(..., description="會話ID")
    session_token: str = Field(..., description="會話令牌")
    ip_address: Optional[str] = Field(None, description="IP地址")
    user_agent: Optional[str] = Field(None, description="用戶代理")
    device_type: Optional[str] = Field(None, description="設備類型")
    browser: Optional[str] = Field(None, description="瀏覽器")
    browser_version: Optional[str] = Field(None, description="瀏覽器版本")
    os: Optional[str] = Field(None, description="操作系統")
    os_version: Optional[str] = Field(None, description="操作系統版本")
    location: Optional[Dict[str, Any]] = Field(None, description="地理位置")

class UserSessionResponseSchema(UserSessionBaseSchema):
    """用戶會話響應Schema"""
    id: str
    user_id: str
    started_at: datetime
    last_activity_at: datetime
    ended_at: Optional[datetime]
    duration: Optional[int]
    page_views: int
    clicks: int
    api_calls: int
    errors: int
    is_active: bool

    class Config:
        from_attributes = True

class UserBehaviorPatternBaseSchema(UnifiedSchema):
    """用戶行為模式基礎Schema"""
    pattern_type: str = Field(..., description="模式類型")
    pattern_name: str = Field(..., description="模式名稱")
    pattern_value: Dict[str, Any] = Field(..., description="模式數據")
    confidence: float = Field(0.0, description="置信度")
    frequency: float = Field(0.0, description="頻率")
    is_active: bool = Field(True, description="活躍狀態")

class UserBehaviorPatternResponseSchema(UserBehaviorPatternBaseSchema):
    """用戶行為模式響應Schema"""
    id: str
    user_id: str
    last_updated: datetime

    class Config:
        from_attributes = True

class UserFeatureUsageBaseSchema(UnifiedSchema):
    """用戶功能使用基礎Schema"""
    feature: str = Field(..., description="功能")
    module: str = Field(..., description="模塊")
    component: Optional[str] = Field(None, description="組件")
    period_type: str = Field(..., description="周期類型")
    period_start: datetime = Field(..., description="周期開始")
    period_end: datetime = Field(..., description="周期結束")
    usage_count: int = Field(0, description="使用次數")
    total_time: float = Field(0.0, description="總時間")
    avg_session_time: float = Field(0.0, description="平均會話時間")
    success_count: int = Field(0, description="成功次數")
    error_count: int = Field(0, description="錯誤次數")
    success_rate: float = Field(0.0, description="成功率")
    unique_days_used: int = Field(0, description="使用天數")
    peak_usage_time: Optional[str] = Field(None, description="峰值時間")
    preferred_devices: Optional[Dict[str, Any]] = Field(None, description="偏好設備")

class UserFeatureUsageResponseSchema(UserFeatureUsageBaseSchema):
    """用戶功能使用響應Schema"""
    id: str
    user_id: str

    class Config:
        from_attributes = True

class UserPersonaBaseSchema(UnifiedSchema):
    """用戶畫像基礎Schema"""
    user_type: str = Field(..., description="用戶類型")
    user_category: str = Field(..., description="用戶分類")
    preferred_features: Optional[Dict[str, Any]] = Field(None, description="偏好功能")
    usage_patterns: Optional[Dict[str, Any]] = Field(None, description="使用模式")
    work_schedule: Optional[Dict[str, Any]] = Field(None, description="工作時間")
    technical_skill_level: int = Field(0, description="技術水平")
    trading_experience: int = Field(0, description="交易經驗")
    familiarity_score: float = Field(0.0, description="熟悉度")
    risk_appetite: str = Field('moderate', description="風險偏好")
    decision_style: Optional[str] = Field(None, description="決策風格")
    learning_style: Optional[str] = Field(None, description="學習風格")
    engagement_score: float = Field(0.0, description="參與度")
    activity_level: str = Field('normal', description="活動水平")
    retention_score: float = Field(0.0, description="留存分數")
    churn_risk: float = Field(0.0, description="流失風險")
    upsell_opportunity: float = Field(0.0, description="銷售機會")
    next_actions: Optional[Dict[str, Any]] = Field(None, description="預測操作")

class UserPersonaResponseSchema(UserPersonaBaseSchema):
    """用戶畫像響應Schema"""
    id: str
    user_id: str
    last_analyzed: datetime
    analysis_version: str

    class Config:
        from_attributes = True

class UserEngagementMetricBaseSchema(UnifiedSchema):
    """用戶參與度指標基礎Schema"""
    metric_date: datetime = Field(..., description="指標日期")
    period_type: str = Field(..., description="周期類型")
    active_days: int = Field(0, description="活躍天數")
    total_sessions: int = Field(0, description="總會話數")
    avg_session_duration: float = Field(0.0, description="平均會話時間")
    total_interactions: int = Field(0, description="總互動次數")
    features_used: int = Field(0, description="使用功能數")
    new_features_tried: int = Field(0, description="嘗試新功能數")
    core_feature_usage: Optional[Dict[str, Any]] = Field(None, description="核心功能使用")
    reports_generated: int = Field(0, description="生成報告數")
    strategies_created: int = Field(0, description="創建策略數")
    backtests_run: int = Field(0, description="運行回測數")
    shares: int = Field(0, description="分享次數")
    comments: int = Field(0, description="評論次數")
    feedback_given: int = Field(0, description="反饋次數")
    error_rate: float = Field(0.0, description="錯誤率")
    satisfaction_score: Optional[float] = Field(None, description="滿意度")
    net_promoter_score: Optional[int] = Field(None, description="淨推薦值")

class UserEngagementMetricResponseSchema(UserEngagementMetricBaseSchema):
    """用戶參與度指標響應Schema"""
    id: str
    user_id: str

    class Config:
        from_attributes = True