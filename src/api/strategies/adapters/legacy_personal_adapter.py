"""
Legacy Personal API Adapter
將舊的個人偏好和儀表板API調用適配到新的個人服務
"""

from typing import Dict, Any, Optional
import logging
from datetime import datetime

from ..services.personal_service import PersonalService

logger = logging.getLogger(__name__)


class LegacyPersonalAdapter:
    """
    適配器模式實現 - 將舊個人API的數據格式轉換為新格式
    """

    def __init__(self, personal_service: PersonalService):
        self.personal_service = personal_service

    async def get_personal_dashboard(
        self,
        user_id: int
    ) -> Dict[str, Any]:
        """
        適配舊的個人儀表板接口
        原接口: GET /api/strategies/personal/dashboard
        """
        try:
            dashboard = await self.personal_service.get_dashboard_data(user_id)

            return {
                "success": True,
                "data": {
                    "user_id": user_id,
                    "total_strategies": dashboard.total_strategies,
                    "active_strategies": dashboard.active_strategies,
                    "total_executions": dashboard.total_executions,
                    "recent_performance": dashboard.recent_performance,
                    "favorite_strategies": dashboard.favorite_strategies,
                    "notifications": dashboard.notifications
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"獲取個人儀表板失敗: {e}")
            return {
                "success": False,
                "error": {
                    "code": "GET_DASHBOARD_FAILED",
                    "message": str(e)
                },
                "timestamp": datetime.utcnow().isoformat()
            }

    async def get_user_preferences(
        self,
        user_id: int
    ) -> Dict[str, Any]:
        """
        適配舊的獲取用戶偏好接口
        原接口: GET /api/strategies/personal/preferences
        """
        try:
            preferences = await self.personal_service.get_preferences(user_id)

            return {
                "success": True,
                "data": {
                    "user_id": user_id,
                    "theme": preferences.theme,
                    "language": preferences.language,
                    "timezone": preferences.timezone,
                    "notifications": preferences.notifications,
                    "risk_tolerance": preferences.risk_tolerance,
                    "default_strategy_type": preferences.default_strategy_type,
                    "auto_save": preferences.auto_save
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"獲取用戶偏好失敗: {e}")
            return {
                "success": False,
                "error": {
                    "code": "GET_PREFERENCES_FAILED",
                    "message": str(e)
                },
                "timestamp": datetime.utcnow().isoformat()
            }

    async def update_user_preferences(
        self,
        user_id: int,
        preferences_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        適配舊的更新用戶偏好接口
        原接口: PUT /api/strategies/personal/preferences
        """
        try:
            # 轉換偏好設置格式
            preferences = self._convert_preferences(preferences_data)

            # 更新偏好
            await self.personal_service.update_preferences(user_id, preferences)

            return {
                "success": True,
                "message": "用戶偏好更新成功",
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"更新用戶偏好失敗: {e}")
            return {
                "success": False,
                "error": {
                    "code": "UPDATE_PREFERENCES_FAILED",
                    "message": str(e)
                },
                "timestamp": datetime.utcnow().isoformat()
            }

    async def control_strategy(
        self,
        strategy_id: str,
        user_id: int,
        control_action: str,
        control_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        適配舊的策略控制接口
        原接口: POST /api/strategies/personal/strategies/{id}/control
        """
        try:
            # 映射控制動作
            action_mapping = {
                "start": "start",
                "stop": "stop",
                "pause": "pause",
                "resume": "resume",
                "reset": "reset"
            }

            action = action_mapping.get(control_action, control_action)

            # 執行控制操作
            result = await self.personal_service.control_strategy(
                strategy_id, user_id, action, control_params or {}
            )

            return {
                "success": True,
                "data": {
                    "strategy_id": strategy_id,
                    "action": action,
                    "status": result.status,
                    "message": result.message
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"控制策略失敗: {e}")
            return {
                "success": False,
                "error": {
                    "code": "CONTROL_STRATEGY_FAILED",
                    "message": str(e)
                },
                "timestamp": datetime.utcnow().isoformat()
            }

    async def get_strategy_recommendations(
        self,
        user_id: int,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        適配舊的獲取策略推薦接口
        原接口: GET /api/strategies/personal/recommendations
        """
        try:
            recommendations = await self.personal_service.get_recommendations(
                user_id, limit
            )

            return {
                "success": True,
                "data": {
                    "user_id": user_id,
                    "recommendations": [
                        {
                            "strategy_id": rec.strategy_id,
                            "strategy_name": rec.strategy_name,
                            "strategy_type": rec.strategy_type,
                            "expected_return": rec.expected_return,
                            "risk_score": rec.risk_score,
                            "match_score": rec.match_score,
                            "reason": rec.reason
                        }
                        for rec in recommendations
                    ]
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"獲取策略推薦失敗: {e}")
            return {
                "success": False,
                "error": {
                    "code": "GET_RECOMMENDATIONS_FAILED",
                    "message": str(e)
                },
                "timestamp": datetime.utcnow().isoformat()
            }

    def _convert_preferences(
        self,
        legacy_prefs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        轉換偏好設置格式
        """
        converted = {}

        if "theme" in legacy_prefs:
            converted["theme"] = legacy_prefs["theme"]
        if "language" in legacy_prefs:
            converted["language"] = legacy_prefs["language"]
        if "timezone" in legacy_prefs:
            converted["timezone"] = legacy_prefs["timezone"]
        if "risk_tolerance" in legacy_prefs:
            converted["risk_tolerance"] = legacy_prefs["risk_tolerance"]
        if "default_strategy_type" in legacy_prefs:
            converted["default_strategy_type"] = legacy_prefs["default_strategy_type"]
        if "auto_save" in legacy_prefs:
            converted["auto_save"] = legacy_prefs["auto_save"]

        # 處理通知設置
        if "notifications" in legacy_prefs:
            notifications = legacy_prefs["notifications"]
            converted["notifications"] = {
                "email": notifications.get("email", True),
                "sms": notifications.get("sms", False),
                "push": notifications.get("push", True),
                "strategy_alerts": notifications.get("strategy_alerts", True),
                "execution_reports": notifications.get("execution_reports", True)
            }

        return converted