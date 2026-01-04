"""
用戶偏好管理模型

定義用戶偏好設置、界面配置、通知偏好等相關數據模型。
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field, validator

from .unified_base import UnifiedBaseModel, UnifiedSchema

class UserPreference(UnifiedBaseModel):
    """用戶偏好設置模型"""

    __tablename__ = 'user_preferences'

    # 關聯用戶
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False, unique=True, index=True)

    # 界面偏好
    theme = Column(String(20), default='light', nullable=False)  # light, dark, auto
    primary_color = Column(String(7), default='#3B82F6', nullable=False)  # hex color
    accent_color = Column(String(7), default='#10B981', nullable=False)
    font_size = Column(String(10), default='medium', nullable=False)  # small, medium, large
    font_family = Column(String(50), default='Inter', nullable=False)
    sidebar_collapsed = Column(Boolean, default=False, nullable=False)

    # 語言和地區
    language = Column(String(10), default='zh-TW', nullable=False)
    timezone = Column(String(50), default='Asia/Taipei', nullable=False)
    date_format = Column(String(20), default='YYYY-MM-DD', nullable=False)
    time_format = Column(String(10), default='24h', nullable=False)  # 12h, 24h
    number_format = Column(String(10), default='1,234.56', nullable=False)
    currency = Column(String(3), default='TWD', nullable=False)

    # 儀表板偏好
    default_dashboard = Column(String(50), default='overview', nullable=False)
    widget_layout = Column(JSONB, nullable=True)  # 儀表板小部件佈局
    refresh_interval = Column(Integer, default=30, nullable=False)  # 秒
    auto_refresh_enabled = Column(Boolean, default=True, nullable=False)

    # 表格偏好
    table_page_size = Column(Integer, default=20, nullable=False)
    table_density = Column(String(10), default='medium', nullable=False)  # compact, medium, comfortable
    table_pagination_enabled = Column(Boolean, default=True, nullable=False)

    # 關聯
    user = relationship("User", back_populates="preferences")
    notification_preferences = relationship("NotificationPreference", back_populates="user_preference", cascade="all, delete-orphan")

class NotificationPreference(UnifiedBaseModel):
    """通知偏好設置模型"""

    __tablename__ = 'notification_preferences'

    # 關聯用戶偏好
    user_preference_id = Column(String(36), ForeignKey('user_preferences.id'), nullable=False, index=True)

    # 通知類型
    notification_type = Column(String(50), nullable=False)  # email, sms, push, in_app

    # 通知分類
    category = Column(String(50), nullable=False)  # system, strategy, trading, risk, report

    # 通知設置
    enabled = Column(Boolean, default=True, nullable=False)

    # 通知頻率
    frequency = Column(String(20), default='immediate', nullable=False)  # immediate, hourly, daily, weekly

    # 通知時間窗口（用於digest類通知）
    digest_time = Column(String(5), default='09:00', nullable=False)  # HH:MM
    digest_timezone = Column(String(50), default='Asia/Taipei', nullable=False)

    # 通知渠道設置
    email_enabled = Column(Boolean, default=True, nullable=False)
    sms_enabled = Column(Boolean, default=False, nullable=False)
    push_enabled = Column(Boolean, default=True, nullable=False)
    in_app_enabled = Column(Boolean, default=True, nullable=False)

    # 通知過濾
    min_severity = Column(String(10), default='info', nullable=False)  # debug, info, warning, error, critical
    max_frequency_per_hour = Column(Integer, default=10, nullable=False)

    # 額外設置
    settings = Column(JSONB, nullable=True)  # 通知類型特定的設置

    # 關聯
    user_preference = relationship("UserPreference", back_populates="notification_preferences")

class UserWidget(UnifiedBaseModel):
    """用戶自定義小部件模型"""

    __tablename__ = 'user_widgets'

    # 關聯用戶
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False, index=True)

    # 小部件信息
    widget_id = Column(String(100), nullable=False)  # 小部件類型ID
    widget_name = Column(String(100), nullable=False)  # 自定義名稱
    widget_type = Column(String(50), nullable=False)  # chart, table, metric, alert

    # 位置和大小
    dashboard = Column(String(50), default='main', nullable=False)
    position_x = Column(Integer, default=0, nullable=False)
    position_y = Column(Integer, default=0, nullable=False)
    width = Column(Integer, default=4, nullable=False)  # grid units
    height = Column(Integer, default=3, nullable=False)

    # 配置
    config = Column(JSONB, nullable=True)  # 小部件特定配置
    data_source = Column(JSONB, nullable=True)  # 數據源配置
    refresh_interval = Column(Integer, default=30, nullable=False)

    # 狀態
    is_visible = Column(Boolean, default=True, nullable=False)
    is_collapsed = Column(Boolean, default=False, nullable=False)

    # 排序
    sort_order = Column(Integer, default=0, nullable=False)

    # 關聯
    user = relationship("User")

class UserShortcut(UnifiedBaseModel):
    """用戶快捷方式模型"""

    __tablename__ = 'user_shortcuts'

    # 關聯用戶
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False, index=True)

    # 快捷方式信息
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    url = Column(String(500), nullable=False)
    icon = Column(String(100), nullable=True)

    # 分類
    category = Column(String(50), default='custom', nullable=False)

    # 狀態
    is_visible = Column(Boolean, default=True, nullable=False)
    opens_in_new_tab = Column(Boolean, default=False, nullable=False)

    # 排序
    sort_order = Column(Integer, default=0, nullable=False)

    # 關聯
    user = relationship("User")

# Pydantic Schemas
class UserPreferenceBaseSchema(UnifiedSchema):
    """用戶偏好基礎Schema"""
    theme: str = Field('light', description="主題")
    primary_color: str = Field('#3B82F6', description="主要顏色")
    accent_color: str = Field('#10B981', description="強調顏色")
    font_size: str = Field('medium', description="字體大小")
    font_family: str = Field('Inter', description="字體")
    sidebar_collapsed: bool = Field(False, description="側邊欄折疊")
    language: str = Field('zh-TW', description="語言")
    timezone: str = Field('Asia/Taipei', description="時區")
    date_format: str = Field('YYYY-MM-DD', description="日期格式")
    time_format: str = Field('24h', description="時間格式")
    number_format: str = Field('1,234.56', description="數字格式")
    currency: str = Field('TWD', description="貨幣")
    default_dashboard: str = Field('overview', description="默認儀表板")
    widget_layout: Optional[Dict[str, Any]] = Field(None, description="小部件佈局")
    refresh_interval: int = Field(30, description="刷新間隔（秒）")
    auto_refresh_enabled: bool = Field(True, description="自動刷新")
    table_page_size: int = Field(20, description="表格頁面大小")
    table_density: str = Field('medium', description="表格密度")
    table_pagination_enabled: bool = Field(True, description="表格分頁")

class UserPreferenceUpdateSchema(UserPreferenceBaseSchema):
    """更新用戶偏好Schema"""
    pass

class UserPreferenceResponseSchema(UserPreferenceBaseSchema):
    """用戶偏好響應Schema"""
    user_id: str

    class Config:
        from_attributes = True

class NotificationPreferenceBaseSchema(UnifiedSchema):
    """通知偏好基礎Schema"""
    notification_type: str = Field(..., description="通知類型")
    category: str = Field(..., description="通知分類")
    enabled: bool = Field(True, description="啟用通知")
    frequency: str = Field('immediate', description="通知頻率")
    digest_time: str = Field('09:00', description="摘要時間")
    digest_timezone: str = Field('Asia/Taipei', description="摘要時區")
    email_enabled: bool = Field(True, description="郵件通知")
    sms_enabled: bool = Field(False, description="短信通知")
    push_enabled: bool = Field(True, description="推送通知")
    in_app_enabled: bool = Field(True, description="應用內通知")
    min_severity: str = Field('info', description="最小嚴重級別")
    max_frequency_per_hour: int = Field(10, description="每小時最大頻率")
    settings: Optional[Dict[str, Any]] = Field(None, description="額外設置")

class NotificationPreferenceCreateSchema(NotificationPreferenceBaseSchema):
    """創建通知偏好Schema"""
    pass

class NotificationPreferenceUpdateSchema(UnifiedSchema):
    """更新通知偏好Schema"""
    enabled: Optional[bool] = None
    frequency: Optional[str] = None
    digest_time: Optional[str] = None
    email_enabled: Optional[bool] = None
    sms_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None
    in_app_enabled: Optional[bool] = None
    min_severity: Optional[str] = None
    max_frequency_per_hour: Optional[int] = None
    settings: Optional[Dict[str, Any]] = None

class NotificationPreferenceResponseSchema(NotificationPreferenceBaseSchema):
    """通知偏好響應Schema"""
    id: str
    user_preference_id: str

    class Config:
        from_attributes = True

class UserWidgetBaseSchema(UnifiedSchema):
    """用戶小部件基礎Schema"""
    widget_id: str = Field(..., description="小部件ID")
    widget_name: str = Field(..., description="小部件名稱")
    widget_type: str = Field(..., description="小部件類型")
    dashboard: str = Field('main', description="儀表板")
    position_x: int = Field(0, description="X位置")
    position_y: int = Field(0, description="Y位置")
    width: int = Field(4, description="寬度")
    height: int = Field(3, description="高度")
    config: Optional[Dict[str, Any]] = Field(None, description="配置")
    data_source: Optional[Dict[str, Any]] = Field(None, description="數據源")
    refresh_interval: int = Field(30, description="刷新間隔")
    is_visible: bool = Field(True, description="可見")
    is_collapsed: bool = Field(False, description="折疊")
    sort_order: int = Field(0, description="排序")

class UserWidgetCreateSchema(UserWidgetBaseSchema):
    """創建用戶小部件Schema"""
    pass

class UserWidgetUpdateSchema(UnifiedSchema):
    """更新用戶小部件Schema"""
    widget_name: Optional[str] = None
    position_x: Optional[int] = None
    position_y: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    config: Optional[Dict[str, Any]] = None
    data_source: Optional[Dict[str, Any]] = None
    refresh_interval: Optional[int] = None
    is_visible: Optional[bool] = None
    is_collapsed: Optional[bool] = None
    sort_order: Optional[int] = None

class UserWidgetResponseSchema(UserWidgetBaseSchema):
    """用戶小部件響應Schema"""
    id: str
    user_id: str

    class Config:
        from_attributes = True

class UserShortcutBaseSchema(UnifiedSchema):
    """用戶快捷方式基礎Schema"""
    name: str = Field(..., description="名稱")
    description: Optional[str] = Field(None, description="描述")
    url: str = Field(..., description="URL")
    icon: Optional[str] = Field(None, description="圖標")
    category: str = Field('custom', description="分類")
    is_visible: bool = Field(True, description="可見")
    opens_in_new_tab: bool = Field(False, description="新標籤頁打開")
    sort_order: int = Field(0, description="排序")

class UserShortcutCreateSchema(UserShortcutBaseSchema):
    """創建用戶快捷方式Schema"""
    pass

class UserShortcutUpdateSchema(UnifiedSchema):
    """更新用戶快捷方式Schema"""
    name: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    icon: Optional[str] = None
    category: Optional[str] = None
    is_visible: Optional[bool] = None
    opens_in_new_tab: Optional[bool] = None
    sort_order: Optional[int] = None

class UserShortcutResponseSchema(UserShortcutBaseSchema):
    """用戶快捷方式響應Schema"""
    id: str
    user_id: str

    class Config:
        from_attributes = True