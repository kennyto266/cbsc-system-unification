"""
Feature Flags Configuration
功能開關配置 - 控制新功能的漸進式推出
"""

import os
from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class FeatureFlag:
    """功能開關定義"""
    key: str
    description: str
    enabled: bool = False
    rollout_percentage: int = 0


class FeatureFlagManager:
    """
    功能開關管理器
    支持基於環境變量和用戶ID的功能控制
    """

    def __init__(self):
        self.flags = self._load_default_flags()
        self._update_from_env()

    def _load_default_flags(self) -> Dict[str, FeatureFlag]:
        """
        加載默認的功能開關配置
        """
        return {
            # API版本控制
            "USE_V2_API": FeatureFlag(
                key="USE_V2_API",
                description="啟用新的v2 API架構",
                enabled=False,
                rollout_percentage=0
            ),

            # 新策略管理功能
            "USE_NEW_STRATEGY_SERVICE": FeatureFlag(
                key="USE_NEW_STRATEGY_SERVICE",
                description="使用新的策略服務實現",
                enabled=False,
                rollout_percentage=5  # 從5%開始
            ),

            # 實時執行功能
            "ENABLE_REAL_TIME_EXECUTION": FeatureFlag(
                key="ENABLE_REAL_TIME_EXECUTION",
                description="啟用實時策略執行",
                enabled=False,
                rollout_percentage=0
            ),

            # WebSocket v2
            "USE_V2_WEBSOCKET": FeatureFlag(
                key="USE_V2_WEBSOCKET",
                description="使用新的v2 WebSocket連接",
                enabled=False,
                rollout_percentage=10
            ),

            # 緩存優化
            "USE_ENHANCED_CACHE": FeatureFlag(
                key="USE_ENHANCED_CACHE",
                description="使用增強的緩存策略",
                enabled=True,  # 可以默認啟用
                rollout_percentage=100
            ),

            # 權限控制
            "USE_NEW_PERMISSIONS": FeatureFlag(
                key="USE_NEW_PERMISSIONS",
                description="使用新的權限控制系統",
                enabled=False,
                rollout_percentage=20
            ),

            # 監控和分析
            "ENABLE_PERFORMANCE_MONITORING": FeatureFlag(
                key="ENABLE_PERFORMANCE_MONITORING",
                description="啟用性能監控",
                enabled=True,
                rollout_percentage=100
            ),

            # 新的響應格式
            "USE_V2_RESPONSE_FORMAT": FeatureFlag(
                key="USE_V2_RESPONSE_FORMAT",
                description="使用新的v2響應格式",
                enabled=False,
                rollout_percentage=0
            ),

            # 數據庫連接池
            "USE_CONNECTION_POOLING": FeatureFlag(
                key="USE_CONNECTION_POOLING",
                description="使用數據庫連接池",
                enabled=True,
                rollout_percentage=100
            ),

            # 非同步處理
            "USE_ASYNC_PROCESSING": FeatureFlag(
                key="USE_ASYNC_PROCESSING",
                description="使用異步處理",
                enabled=False,
                rollout_percentage=30
            )
        }

    def _update_from_env(self):
        """
        從環境變量更新功能開關
        """
        for key, flag in self.flags.items():
            env_value = os.getenv(key, "").lower()
            if env_value in ("true", "1", "yes", "on"):
                flag.enabled = True
                flag.rollout_percentage = 100
            elif env_value in ("false", "0", "no", "off"):
                flag.enabled = False
                flag.rollout_percentage = 0

            # 檢查是否有特定的滾動百分比
            env_percentage = os.getenv(f"{key}_ROLL_PERCENT")
            if env_percentage and env_percentage.isdigit():
                flag.rollout_percentage = int(env_percentage)

    def is_enabled(
        self,
        flag_key: str,
        user_id: Optional[int] = None,
        force_check: bool = False
    ) -> bool:
        """
        檢查功能開關是否啟用

        Args:
            flag_key: 功能開關鍵名
            user_id: 用戶ID（用於灰度發布）
            force_check: 強制檢查（忽略緩存）
        """
        if flag_key not in self.flags:
            return False

        flag = self.flags[flag_key]

        # 如果功能完全禁用
        if not flag.enabled and flag.rollout_percentage == 0:
            return False

        # 如果功能完全啟用
        if flag.enabled or flag.rollout_percentage == 100:
            return True

        # 如果提供了用戶ID，使用灰度發布邏輯
        if user_id is not None:
            # 簡單的基於用戶ID的哈希分組
            import hashlib
            hash_digest = int(hashlib.md5(f"{user_id}-{flag_key}".encode()).hexdigest(), 16)
            return (hash_digest % 100) < flag.rollout_percentage

        # 默認情況下返回enabled狀態
        return flag.enabled

    def get_rollout_status(self, flag_key: str) -> Dict[str, Any]:
        """
        獲取功能開關的滾動狀態
        """
        if flag_key not in self.flags:
            return {
                "error": f"Feature flag '{flag_key}' not found"
            }

        flag = self.flags[flag_key]
        return {
            "key": flag.key,
            "description": flag.description,
            "enabled": flag.enabled,
            "rollout_percentage": flag.rollout_percentage,
            "status": self._get_status_text(flag)
        }

    def _get_status_text(self, flag: FeatureFlag) -> str:
        """
        獲取狀態描述文本
        """
        if flag.enabled:
            return "完全啟用"
        elif flag.rollout_percentage == 0:
            return "完全禁用"
        else:
            return f"灰度發布 ({flag.rollout_percentage}%)"

    def get_all_flags_status(self) -> Dict[str, Dict[str, Any]]:
        """
        獲取所有功能開關的狀態
        """
        return {
            key: self.get_rollout_status(key)
            for key in self.flags.keys()
        }

    def set_rollout_percentage(
        self,
        flag_key: str,
        percentage: int,
        auto_enable: bool = True
    ):
        """
        設置滾動百分比

        Args:
            flag_key: 功能開關鍵名
            percentage: 滾動百分比 (0-100)
            auto_enable: 是否在百分比>0時自動啟用功能
        """
        if flag_key not in self.flags:
            raise ValueError(f"Feature flag '{flag_key}' not found")

        if not 0 <= percentage <= 100:
            raise ValueError("Percentage must be between 0 and 100")

        flag = self.flags[flag_key]
        flag.rollout_percentage = percentage

        if auto_enable and percentage > 0:
            flag.enabled = True
        elif percentage == 0:
            flag.enabled = False

    def enable_feature(self, flag_key: str):
        """
        完全啟用功能
        """
        self.set_rollout_percentage(flag_key, 100)

    def disable_feature(self, flag_key: str):
        """
        完全禁用功能
        """
        self.set_rollout_percentage(flag_key, 0, auto_enable=False)


# 全局功能開關管理器實例
feature_flags = FeatureFlagManager()


# 便捷函數
def is_feature_enabled(
    flag_key: str,
    user_id: Optional[int] = None
) -> bool:
    """檢查功能是否啟用的便捷函數"""
    return feature_flags.is_enabled(flag_key, user_id)


def get_feature_status(flag_key: str) -> Dict[str, Any]:
    """獲取功能狀態的便捷函數"""
    return feature_flags.get_rollout_status(flag_key)


# 環境檢查函數
def is_development() -> bool:
    """檢查是否為開發環境"""
    return os.getenv("ENVIRONMENT", "development").lower() == "development"


def is_production() -> bool:
    """檢查是否為生產環境"""
    return os.getenv("ENVIRONMENT", "development").lower() == "production"


def is_testing() -> bool:
    """檢查是否為測試環境"""
    return os.getenv("ENVIRONMENT", "development").lower() == "testing"