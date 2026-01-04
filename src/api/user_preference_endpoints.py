"""
用戶偏好管理API端點
User Preference Management API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import logging

from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from ..models.user_preferences import (
    UserPreference, NotificationPreference, UserWidget, UserShortcut,
    UserPreferenceResponseSchema, UserPreferenceUpdateSchema,
    NotificationPreferenceCreateSchema, NotificationPreferenceUpdateSchema, NotificationPreferenceResponseSchema,
    UserWidgetCreateSchema, UserWidgetUpdateSchema, UserWidgetResponseSchema,
    UserShortcutCreateSchema, UserShortcutUpdateSchema, UserShortcutResponseSchema
)
from ..models.user import User
from ..core.database import get_db

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 創建路由器
router = APIRouter(prefix="/api/user/preferences", tags=["用戶偏好管理"])

# 依賴注入
def get_current_user():
    """獲取當前用戶"""
    # 這裡應該從認證中間件獲取當前用戶
    # 暫時返回一個模擬用戶
    pass

# Pydantic模型
class ThemeSettings(BaseModel):
    """主題設置模型"""
    theme: str = Field("light", description="主題模式")
    primary_color: str = Field("#3B82F6", description="主要顏色")
    accent_color: str = Field("#10B981", description="強調顏色")
    font_size: str = Field("medium", description="字體大小")
    font_family: str = Field("Inter", description="字體")

class LanguageSettings(BaseModel):
    """語言設置模型"""
    language: str = Field("zh-TW", description="語言")
    timezone: str = Field("Asia/Taipei", description="時區")
    date_format: str = Field("YYYY-MM-DD", description="日期格式")
    time_format: str = Field("24h", description="時間格式")
    number_format: str = Field("1,234.56", description="數字格式")
    currency: str = Field("TWD", description="貨幣")

class DashboardSettings(BaseModel):
    """儀表板設置模型"""
    default_dashboard: str = Field("overview", description="默認儀表板")
    widget_layout: Optional[Dict[str, Any]] = Field(None, description="小部件佈局")
    refresh_interval: int = Field(30, description="刷新間隔（秒）")
    auto_refresh_enabled: bool = Field(True, description="自動刷新")
    sidebar_collapsed: bool = Field(False, description="側邊欄折疊")

class TableSettings(BaseModel):
    """表格設置模型"""
    page_size: int = Field(20, description="頁面大小")
    density: str = Field("medium", description="密度")
    pagination_enabled: bool = Field(True, description="分頁啟用")

# 用戶偏好端點
@router.get("/me", response_model=UserPreferenceResponseSchema)
async def get_user_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """獲取當前用戶偏好設置"""
    try:
        # 查找用戶偏好
        preferences = db.query(UserPreference).filter(
            UserPreference.user_id == current_user.id
        ).first()

        if not preferences:
            # 創建默認偏好
            preferences = UserPreference(user_id=current_user.id)
            db.add(preferences)
            db.commit()
            db.refresh(preferences)

        return preferences

    except Exception as e:
        logger.error(f"獲取用戶偏好失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取用戶偏好失敗"
        )

@router.put("/me", response_model=UserPreferenceResponseSchema)
async def update_user_preferences(
    preferences_update: UserPreferenceUpdateSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新用戶偏好設置"""
    try:
        # 獲取現有偏好
        preferences = db.query(UserPreference).filter(
            UserPreference.user_id == current_user.id
        ).first()

        if not preferences:
            preferences = UserPreference(user_id=current_user.id)
            db.add(preferences)

        # 更新字段
        update_data = preferences_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(preferences, field):
                setattr(preferences, field, value)

        db.commit()
        db.refresh(preferences)

        return preferences

    except Exception as e:
        logger.error(f"更新用戶偏好失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新用戶偏好失敗"
        )

@router.patch("/theme")
async def update_theme_settings(
    theme_settings: ThemeSettings,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新主題設置"""
    try:
        preferences = db.query(UserPreference).filter(
            UserPreference.user_id == current_user.id
        ).first()

        if not preferences:
            preferences = UserPreference(user_id=current_user.id)
            db.add(preferences)

        # 更新主題相關設置
        preferences.theme = theme_settings.theme
        preferences.primary_color = theme_settings.primary_color
        preferences.accent_color = theme_settings.accent_color
        preferences.font_size = theme_settings.font_size
        preferences.font_family = theme_settings.font_family

        db.commit()

        return {"message": "主題設置更新成功"}

    except Exception as e:
        logger.error(f"更新主題設置失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新主題設置失敗"
        )

@router.patch("/language")
async def update_language_settings(
    language_settings: LanguageSettings,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新語言設置"""
    try:
        preferences = db.query(UserPreference).filter(
            UserPreference.user_id == current_user.id
        ).first()

        if not preferences:
            preferences = UserPreference(user_id=current_user.id)
            db.add(preferences)

        # 更新語言相關設置
        preferences.language = language_settings.language
        preferences.timezone = language_settings.timezone
        preferences.date_format = language_settings.date_format
        preferences.time_format = language_settings.time_format
        preferences.number_format = language_settings.number_format
        preferences.currency = language_settings.currency

        db.commit()

        return {"message": "語言設置更新成功"}

    except Exception as e:
        logger.error(f"更新語言設置失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新語言設置失敗"
        )

@router.patch("/dashboard")
async def update_dashboard_settings(
    dashboard_settings: DashboardSettings,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新儀表板設置"""
    try:
        preferences = db.query(UserPreference).filter(
            UserPreference.user_id == current_user.id
        ).first()

        if not preferences:
            preferences = UserPreference(user_id=current_user.id)
            db.add(preferences)

        # 更新儀表板相關設置
        preferences.default_dashboard = dashboard_settings.default_dashboard
        preferences.widget_layout = dashboard_settings.widget_layout
        preferences.refresh_interval = dashboard_settings.refresh_interval
        preferences.auto_refresh_enabled = dashboard_settings.auto_refresh_enabled
        preferences.sidebar_collapsed = dashboard_settings.sidebar_collapsed

        db.commit()

        return {"message": "儀表板設置更新成功"}

    except Exception as e:
        logger.error(f"更新儀表板設置失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新儀表板設置失敗"
        )

@router.patch("/table")
async def update_table_settings(
    table_settings: TableSettings,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新表格設置"""
    try:
        preferences = db.query(UserPreference).filter(
            UserPreference.user_id == current_user.id
        ).first()

        if not preferences:
            preferences = UserPreference(user_id=current_user.id)
            db.add(preferences)

        # 更新表格相關設置
        preferences.table_page_size = table_settings.page_size
        preferences.table_density = table_settings.density
        preferences.table_pagination_enabled = table_settings.pagination_enabled

        db.commit()

        return {"message": "表格設置更新成功"}

    except Exception as e:
        logger.error(f"更新表格設置失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新表格設置失敗"
        )

# 通知偏好端點
@router.get("/notifications", response_model=List[NotificationPreferenceResponseSchema])
async def get_notification_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """獲取通知偏好設置"""
    try:
        # 獲取用戶偏好
        user_pref = db.query(UserPreference).filter(
            UserPreference.user_id == current_user.id
        ).first()

        if not user_pref:
            # 創建默認偏好
            user_pref = UserPreference(user_id=current_user.id)
            db.add(user_pref)
            db.commit()
            db.refresh(user_pref)

        # 獲取通知偏好
        notifications = db.query(NotificationPreference).filter(
            NotificationPreference.user_preference_id == user_pref.id
        ).all()

        return notifications

    except Exception as e:
        logger.error(f"獲取通知偏好失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取通知偏好失敗"
        )

@router.post("/notifications", response_model=NotificationPreferenceResponseSchema)
async def create_notification_preference(
    notification: NotificationPreferenceCreateSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """創建通知偏好設置"""
    try:
        # 獲取用戶偏好
        user_pref = db.query(UserPreference).filter(
            UserPreference.user_id == current_user.id
        ).first()

        if not user_pref:
            user_pref = UserPreference(user_id=current_user.id)
            db.add(user_pref)
            db.commit()
            db.refresh(user_pref)

        # 檢查是否已存在相同類型和分類的通知偏好
        existing = db.query(NotificationPreference).filter(
            NotificationPreference.user_preference_id == user_pref.id,
            NotificationPreference.notification_type == notification.notification_type,
            NotificationPreference.category == notification.category
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="該通知偏好已存在"
            )

        # 創建新通知偏好
        new_notification = NotificationPreference(
            user_preference_id=user_pref.id,
            **notification.dict()
        )

        db.add(new_notification)
        db.commit()
        db.refresh(new_notification)

        return new_notification

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"創建通知偏好失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="創建通知偏好失敗"
        )

@router.put("/notifications/{notification_id}", response_model=NotificationPreferenceResponseSchema)
async def update_notification_preference(
    notification_id: str,
    notification_update: NotificationPreferenceUpdateSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新通知偏好設置"""
    try:
        # 獲取通知偏好
        notification = db.query(NotificationPreference).filter(
            NotificationPreference.id == notification_id
        ).first()

        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="通知偏好不存在"
            )

        # 驗證權限
        user_pref = db.query(UserPreference).filter(
            UserPreference.id == notification.user_preference_id,
            UserPreference.user_id == current_user.id
        ).first()

        if not user_pref:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="無權限修改此通知偏好"
            )

        # 更新字段
        update_data = notification_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(notification, field):
                setattr(notification, field, value)

        db.commit()
        db.refresh(notification)

        return notification

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新通知偏好失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新通知偏好失敗"
        )

@router.delete("/notifications/{notification_id}")
async def delete_notification_preference(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """刪除通知偏好設置"""
    try:
        # 獲取通知偏好
        notification = db.query(NotificationPreference).filter(
            NotificationPreference.id == notification_id
        ).first()

        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="通知偏好不存在"
            )

        # 驗證權限
        user_pref = db.query(UserPreference).filter(
            UserPreference.id == notification.user_preference_id,
            UserPreference.user_id == current_user.id
        ).first()

        if not user_pref:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="無權限刪除此通知偏好"
            )

        # 刪除通知偏好
        db.delete(notification)
        db.commit()

        return {"message": "通知偏好刪除成功"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"刪除通知偏好失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="刪除通知偏好失敗"
        )

# 用戶小部件端點
@router.get("/widgets", response_model=List[UserWidgetResponseSchema])
async def get_user_widgets(
    dashboard: Optional[str] = Query(None, description="儀表板名稱"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """獲取用戶小部件列表"""
    try:
        query = db.query(UserWidget).filter(
            UserWidget.user_id == current_user.id
        )

        if dashboard:
            query = query.filter(UserWidget.dashboard == dashboard)

        widgets = query.order_by(UserWidget.sort_order).all()

        return widgets

    except Exception as e:
        logger.error(f"獲取用戶小部件失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取用戶小部件失敗"
        )

@router.post("/widgets", response_model=UserWidgetResponseSchema)
async def create_user_widget(
    widget: UserWidgetCreateSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """創建用戶小部件"""
    try:
        # 計算排序順序
        max_order = db.query(UserWidget).filter(
            UserWidget.user_id == current_user.id,
            UserWidget.dashboard == widget.dashboard
        ).count()

        new_widget = UserWidget(
            user_id=current_user.id,
            sort_order=max_order,
            **widget.dict()
        )

        db.add(new_widget)
        db.commit()
        db.refresh(new_widget)

        return new_widget

    except Exception as e:
        logger.error(f"創建用戶小部件失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="創建用戶小部件失敗"
        )

@router.put("/widgets/{widget_id}", response_model=UserWidgetResponseSchema)
async def update_user_widget(
    widget_id: str,
    widget_update: UserWidgetUpdateSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新用戶小部件"""
    try:
        # 獲取小部件
        widget = db.query(UserWidget).filter(
            UserWidget.id == widget_id,
            UserWidget.user_id == current_user.id
        ).first()

        if not widget:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="小部件不存在"
            )

        # 更新字段
        update_data = widget_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(widget, field):
                setattr(widget, field, value)

        db.commit()
        db.refresh(widget)

        return widget

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新用戶小部件失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新用戶小部件失敗"
        )

@router.delete("/widgets/{widget_id}")
async def delete_user_widget(
    widget_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """刪除用戶小部件"""
    try:
        # 獲取小部件
        widget = db.query(UserWidget).filter(
            UserWidget.id == widget_id,
            UserWidget.user_id == current_user.id
        ).first()

        if not widget:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="小部件不存在"
            )

        # 刪除小部件
        db.delete(widget)
        db.commit()

        return {"message": "小部件刪除成功"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"刪除用戶小部件失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="刪除用戶小部件失敗"
        )

@router.put("/widgets/{widget_id}/position")
async def update_widget_position(
    widget_id: str,
    position_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新小部件位置"""
    try:
        # 獲取小部件
        widget = db.query(UserWidget).filter(
            UserWidget.id == widget_id,
            UserWidget.user_id == current_user.id
        ).first()

        if not widget:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="小部件不存在"
            )

        # 更新位置
        if 'position_x' in position_data:
            widget.position_x = position_data['position_x']
        if 'position_y' in position_data:
            widget.position_y = position_data['position_y']
        if 'width' in position_data:
            widget.width = position_data['width']
        if 'height' in position_data:
            widget.height = position_data['height']
        if 'sort_order' in position_data:
            widget.sort_order = position_data['sort_order']

        db.commit()

        return {"message": "小部件位置更新成功"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新小部件位置失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新小部件位置失敗"
        )

# 用戶快捷方式端點
@router.get("/shortcuts", response_model=List[UserShortcutResponseSchema])
async def get_user_shortcuts(
    category: Optional[str] = Query(None, description="分類"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """獲取用戶快捷方式列表"""
    try:
        query = db.query(UserShortcut).filter(
            UserShortcut.user_id == current_user.id
        )

        if category:
            query = query.filter(UserShortcut.category == category)

        shortcuts = query.order_by(UserShortcut.sort_order).all()

        return shortcuts

    except Exception as e:
        logger.error(f"獲取用戶快捷方式失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取用戶快捷方式失敗"
        )

@router.post("/shortcuts", response_model=UserShortcutResponseSchema)
async def create_user_shortcut(
    shortcut: UserShortcutCreateSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """創建用戶快捷方式"""
    try:
        # 計算排序順序
        max_order = db.query(UserShortcut).filter(
            UserShortcut.user_id == current_user.id,
            UserShortcut.category == shortcut.category
        ).count()

        new_shortcut = UserShortcut(
            user_id=current_user.id,
            sort_order=max_order,
            **shortcut.dict()
        )

        db.add(new_shortcut)
        db.commit()
        db.refresh(new_shortcut)

        return new_shortcut

    except Exception as e:
        logger.error(f"創建用戶快捷方式失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="創建用戶快捷方式失敗"
        )

@router.put("/shortcuts/{shortcut_id}", response_model=UserShortcutResponseSchema)
async def update_user_shortcut(
    shortcut_id: str,
    shortcut_update: UserShortcutUpdateSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新用戶快捷方式"""
    try:
        # 獲取快捷方式
        shortcut = db.query(UserShortcut).filter(
            UserShortcut.id == shortcut_id,
            UserShortcut.user_id == current_user.id
        ).first()

        if not shortcut:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="快捷方式不存在"
            )

        # 更新字段
        update_data = shortcut_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(shortcut, field):
                setattr(shortcut, field, value)

        db.commit()
        db.refresh(shortcut)

        return shortcut

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新用戶快捷方式失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新用戶快捷方式失敗"
        )

@router.delete("/shortcuts/{shortcut_id}")
async def delete_user_shortcut(
    shortcut_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """刪除用戶快捷方式"""
    try:
        # 獲取快捷方式
        shortcut = db.query(UserShortcut).filter(
            UserShortcut.id == shortcut_id,
            UserShortcut.user_id == current_user.id
        ).first()

        if not shortcut:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="快捷方式不存在"
            )

        # 刪除快捷方式
        db.delete(shortcut)
        db.commit()

        return {"message": "快捷方式刪除成功"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"刪除用戶快捷方式失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="刪除用戶快捷方式失敗"
        )

@router.put("/shortcuts/reorder")
async def reorder_user_shortcuts(
    reorder_data: Dict[str, List[Dict[str, Any]]],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """重新排序用戶快捷方式"""
    try:
        # 更新每個快捷方式的排序
        for category, shortcuts in reorder_data.items():
            for index, shortcut_data in enumerate(shortcuts):
                shortcut_id = shortcut_data.get('id')
                if shortcut_id:
                    shortcut = db.query(UserShortcut).filter(
                        UserShortcut.id == shortcut_id,
                        UserShortcut.user_id == current_user.id
                    ).first()

                    if shortcut:
                        shortcut.sort_order = index

        db.commit()

        return {"message": "快捷方式排序更新成功"}

    except Exception as e:
        logger.error(f"重新排序快捷方式失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="重新排序快捷方式失敗"
        )

# 預設配置端點
@router.get("/presets/themes")
async def get_theme_presets():
    """獲取主題預設"""
    presets = {
        "light": {
            "name": "淺色主題",
            "primary_color": "#3B82F6",
            "accent_color": "#10B981",
            "background": "#FFFFFF",
            "surface": "#F9FAFB",
            "text": "#111827"
        },
        "dark": {
            "name": "深色主題",
            "primary_color": "#60A5FA",
            "accent_color": "#34D399",
            "background": "#111827",
            "surface": "#1F2937",
            "text": "#F9FAFB"
        },
        "blue": {
            "name": "藍色主題",
            "primary_color": "#2563EB",
            "accent_color": "#0EA5E9",
            "background": "#F0F9FF",
            "surface": "#E0F2FE",
            "text": "#0C4A6E"
        },
        "green": {
            "name": "綠色主題",
            "primary_color": "#059669",
            "accent_color": "#10B981",
            "background": "#F0FDF4",
            "surface": "#DCFCE7",
            "text": "#064E3B"
        }
    }

    return {"presets": presets}

@router.get("/presets/languages")
async def get_language_presets():
    """獲取語言預設"""
    presets = {
        "zh-TW": {
            "name": "繁體中文",
            "timezone": "Asia/Taipei",
            "date_format": "YYYY-MM-DD",
            "time_format": "24h",
            "currency": "TWD"
        },
        "zh-CN": {
            "name": "简体中文",
            "timezone": "Asia/Shanghai",
            "date_format": "YYYY-MM-DD",
            "time_format": "24h",
            "currency": "CNY"
        },
        "en-US": {
            "name": "English (US)",
            "timezone": "America/New_York",
            "date_format": "MM/DD/YYYY",
            "time_format": "12h",
            "currency": "USD"
        },
        "ja-JP": {
            "name": "日本語",
            "timezone": "Asia/Tokyo",
            "date_format": "YYYY/MM/DD",
            "time_format": "24h",
            "currency": "JPY"
        }
    }

    return {"presets": presets}