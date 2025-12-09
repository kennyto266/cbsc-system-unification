"""
T110: 數據主權控制系統

實現用戶完全控制其數據的功能，包括：
- 地理位置數據處理
- 數據保留期限設置
- 數據刪除權
- 數據可攜權
- 同意撤回機制
- 數據使用偏好管理
"""

import hashlib
import json
import logging
import os
import shutil
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..database import get_db_connection


class DataCategory(Enum):
    """數據類別"""

    PERSONAL_INFO = "personal_info"  # 個人信息
    FINANCIAL_DATA = "financial_data"  # 財務數據
    TRADING_HISTORY = "trading_history"  # 交易歷史
    ANALYTICS_DATA = "analytics_data"  # 分析數據
    SYSTEM_LOGS = "system_logs"  # 系統日誌
    PREFERENCES = "preferences"  # 用戶偏好
    COMMUNICATION = "communication"  # 通信記錄


class ConsentStatus(Enum):
    """同意狀態"""

    GRANTED = "granted"  # 已同意
    WITHDRAWN = "withdrawn"  # 已撤回
    EXPIRED = "expired"  # 已過期
    PENDING = "pending"  # 待確認


class DataLocation(Enum):
    """數據存儲位置"""

    LOCAL = "local"  # 本地存儲
    REGION_HK = "region_hk"  # 香港地區
    REGION_CN = "region_cn"  # 中國大陸
    REGION_SG = "region_sg"  # 新加坡
    REGION_US = "region_us"  # 美國
    CLOUD_GLOBAL = "cloud_global"  # 全球雲端


@dataclass
class DataRetentionPolicy:
    """數據保留策略"""

    category: DataCategory
    retention_days: int
    auto_delete: bool
    legal_basis: str
    created_at: datetime


@dataclass
class ConsentRecord:
    """同意記錄"""

    user_id: str
    purpose: str
    category: DataCategory
    status: ConsentStatus
    granted_at: Optional[datetime]
    expires_at: Optional[datetime]
    withdrawn_at: Optional[datetime]
    ip_address: str
    user_agent: str
    version: str  # 隱私政策版本


class DataSovereigntyController:
    """數據主權控制器"""

    def __init__(self, db_path: str = "data / privacy.db"):
        self.db_path = db_path
        self.logger = logging.getLogger("privacy.sovereignty")
        self._init_database()

    def _init_database(self):
        """初始化數據庫"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with get_db_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sovereignty_controls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    category TEXT NOT NULL,
                    preference TEXT NOT NULL,
                    value TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, category, preference)
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS consent_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    purpose TEXT NOT NULL,
                    category TEXT NOT NULL,
                    status TEXT NOT NULL,
                    granted_at TIMESTAMP,
                    expires_at TIMESTAMP,
                    withdrawn_at TIMESTAMP,
                    ip_address TEXT,
                    user_agent TEXT,
                    version TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS data_retention_policies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    category TEXT NOT NULL,
                    retention_days INTEGER NOT NULL,
                    auto_delete BOOLEAN DEFAULT 1,
                    legal_basis TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS data_portability_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    request_type TEXT NOT NULL,
                    format TEXT NOT NULL,
                    status TEXT NOT NULL,
                    file_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    expires_at TIMESTAMP
                )
            """
            )

    def set_data_preference(
        self, user_id: str, category: DataCategory, preference: str, value: Any
    ) -> bool:
        """
        設置用戶數據偏好

        Args:
            user_id: 用戶ID
            category: 數據類別
            preference: 偏好名稱
            value: 偏好值

        Returns:
            bool: 是否成功
        """
        try:
            with get_db_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO sovereignty_controls
                    (user_id, category, preference, value, updated_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                    (user_id, category.value, preference, json.dumps(value)),
                )

            self.logger.info(
                f"用戶 {user_id} 更新數據偏好: {category.value}.{preference}"
            )
            return True

        except Exception as e:
            self.logger.error(f"設置數據偏好失敗: {e}")
            return False

    def get_data_preferences(
        self, user_id: str, category: Optional[DataCategory] = None
    ) -> Dict[str, Any]:
        """
        獲取用戶數據偏好

        Args:
            user_id: 用戶ID
            category: 數據類別（可選）

        Returns:
            Dict: 數據偏好字典
        """
        try:
            with get_db_connection() as conn:
                if category:
                    cursor = conn.execute(
                        """
                        SELECT category, preference, value
                        FROM sovereignty_controls
                        WHERE user_id = ? AND category = ?
                    """,
                        (user_id, category.value),
                    )
                else:
                    cursor = conn.execute(
                        """
                        SELECT category, preference, value
                        FROM sovereignty_controls
                        WHERE user_id = ?
                    """,
                        (user_id,),
                    )

                preferences = {}
                for row in cursor:
                    cat, pref, val = row
                    if cat not in preferences:
                        preferences[cat] = {}
                    preferences[cat][pref] = json.loads(val)

                return preferences

        except Exception as e:
            self.logger.error(f"獲取數據偏好失敗: {e}")
            return {}

    def grant_consent(
        self,
        user_id: str,
        purpose: str,
        category: DataCategory,
        expires_in_days: Optional[int] = None,
        ip_address: str = "",
        user_agent: str = "",
        version: str = "1.0",
    ) -> bool:
        """
        授予同意

        Args:
            user_id: 用戶ID
            purpose: 用途
            category: 數據類別
            expires_in_days: 過期天數
            ip_address: IP地址
            user_agent: 用戶代理
            version: 隱私政策版本

        Returns:
            bool: 是否成功
        """
        try:
            now = datetime.now()
            expires_at = (
                now + timedelta(days=expires_in_days) if expires_in_days else None
            )

            with get_db_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO consent_records
                    (user_id, purpose, category, status, granted_at,
                     expires_at, ip_address, user_agent, version)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        user_id,
                        purpose,
                        category.value,
                        ConsentStatus.GRANTED.value,
                        now,
                        expires_at,
                        ip_address,
                        user_agent,
                        version,
                    ),
                )

            self.logger.info(f"用戶 {user_id} 授予同意: {purpose}")
            return True

        except Exception as e:
            self.logger.error(f"授予同意失敗: {e}")
            return False

    def withdraw_consent(
        self, user_id: str, purpose: str, category: DataCategory
    ) -> bool:
        """
        撤回同意

        Args:
            user_id: 用戶ID
            purpose: 用途
            category: 數據類別

        Returns:
            bool: 是否成功
        """
        try:
            now = datetime.now()

            with get_db_connection() as conn:
                # 查找最新的同意記錄
                cursor = conn.execute(
                    """
                    SELECT id FROM consent_records
                    WHERE user_id = ? AND purpose = ? AND category = ?
                    AND status = ?
                    ORDER BY created_at DESC LIMIT 1
                """,
                    (user_id, purpose, category.value, ConsentStatus.GRANTED.value),
                )

                row = cursor.fetchone()
                if not row:
                    return False

                # 更新為撤回狀態
                conn.execute(
                    """
                    UPDATE consent_records
                    SET status = ?, withdrawn_at = ?
                    WHERE id = ?
                """,
                    (ConsentStatus.WITHDRAWN.value, now, row[0]),
                )

            self.logger.info(f"用戶 {user_id} 撤回同意: {purpose}")
            return True

        except Exception as e:
            self.logger.error(f"撤回同意失敗: {e}")
            return False

    def get_consent_status(
        self, user_id: str, purpose: str, category: DataCategory
    ) -> Optional[ConsentRecord]:
        """
        獲取同意狀態

        Args:
            user_id: 用戶ID
            purpose: 用途
            category: 數據類別

        Returns:
            Optional[ConsentRecord]: 同意記錄
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.execute(
                    """
                    SELECT user_id, purpose, category, status,
                           granted_at, expires_at, withdrawn_at,
                           ip_address, user_agent, version
                    FROM consent_records
                    WHERE user_id = ? AND purpose = ? AND category = ?
                    ORDER BY created_at DESC LIMIT 1
                """,
                    (user_id, purpose, category.value),
                )

                row = cursor.fetchone()
                if not row:
                    return None

                return ConsentRecord(
                    user_id=row[0],
                    purpose=row[1],
                    category=row[2],
                    status=ConsentStatus(row[3]),
                    granted_at=row[4],
                    expires_at=row[5],
                    withdrawn_at=row[6],
                    ip_address=row[7] or "",
                    user_agent=row[8] or "",
                    version=row[9] or "1.0",
                )

        except Exception as e:
            self.logger.error(f"獲取同意狀態失敗: {e}")
            return None

    def set_retention_policy(
        self,
        user_id: str,
        category: DataCategory,
        retention_days: int,
        auto_delete: bool = True,
        legal_basis: str = "user_consent",
    ) -> bool:
        """
        設置數據保留策略

        Args:
            user_id: 用戶ID
            category: 數據類別
            retention_days: 保留天數
            auto_delete: 是否自動刪除
            legal_basis: 法律依據

        Returns:
            bool: 是否成功
        """
        try:
            with get_db_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO data_retention_policies
                    (user_id, category, retention_days, auto_delete, legal_basis, updated_at)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                    (user_id, category.value, retention_days, auto_delete, legal_basis),
                )

            self.logger.info(
                f"用戶 {user_id} 設置保留策略: {category.value} - {retention_days}天"
            )
            return True

        except Exception as e:
            self.logger.error(f"設置保留策略失敗: {e}")
            return False

    def get_retention_policies(self, user_id: str) -> List[DataRetentionPolicy]:
        """
        獲取數據保留策略

        Args:
            user_id: 用戶ID

        Returns:
            List[DataRetentionPolicy]: 保留策略列表
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.execute(
                    """
                    SELECT category, retention_days, auto_delete, legal_basis
                    FROM data_retention_policies
                    WHERE user_id = ?
                """,
                    (user_id,),
                )

                policies = []
                for row in cursor:
                    policies.append(
                        DataRetentionPolicy(
                            category=DataCategory(row[0]),
                            retention_days=row[1],
                            auto_delete=bool(row[2]),
                            legal_basis=row[3],
                            created_at=datetime.now(),
                        )
                    )

                return policies

        except Exception as e:
            self.logger.error(f"獲取保留策略失敗: {e}")
            return []

    def request_data_portability(
        self, user_id: str, request_type: str, format: str = "json"
    ) -> Optional[str]:
        """
        請求數據可攜

        Args:
            user_id: 用戶ID
            request_type: 請求類型 (all, category, specific)
            format: 格式 (json, csv, xml)

        Returns:
            Optional[str]: 請求ID
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO data_portability_requests
                    (user_id, request_type, format, status)
                    VALUES (?, ?, ?, 'pending')
                """,
                    (user_id, request_type, format),
                )

                request_id = cursor.lastrowid
                return str(request_id)

        except Exception as e:
            self.logger.error(f"請求數據可攜失敗: {e}")
            return None

    def process_portability_request(self, request_id: str, user_id: str) -> bool:
        """
        處理數據可攜請求

        Args:
            request_id: 請求ID
            user_id: 用戶ID

        Returns:
            bool: 是否成功
        """
        try:
            with get_db_connection() as conn:
                # 獲取請求信息
                cursor = conn.execute(
                    """
                    SELECT request_type, format
                    FROM data_portability_requests
                    WHERE id = ? AND user_id = ? AND status = 'pending'
                """,
                    (request_id, user_id),
                )

                row = cursor.fetchone()
                if not row:
                    return False

                request_type, format = row

                # 導出用戶數據
                export_data = self._export_user_data(user_id, request_type)

                # 保存導出文件
                export_dir = Path(f"data / exports/{user_id}")
                export_dir.mkdir(parents=True, exist_ok=True)

                timestamp = datetime.now().strftime("%Y % m % d_ % H % M % S")
                file_path = export_dir / f"export_{request_id}_{timestamp}.{format}"

                if format == "json":
                    with open(file_path, "w", encoding="utf - 8") as f:
                        json.dump(
                            export_data, f, ensure_ascii=False, indent=2, default=str
                        )
                elif format == "csv":
                    import pandas as pd

                    pd.DataFrame(export_data).to_csv(file_path, index=False)

                # 更新請求狀態
                expires_at = datetime.now() + timedelta(days=30)
                conn.execute(
                    """
                    UPDATE data_portability_requests
                    SET status = 'completed', file_path = ?, completed_at = CURRENT_TIMESTAMP,
                        expires_at = ?
                    WHERE id = ? AND user_id = ?
                """,
                    (str(file_path), expires_at, request_id, user_id),
                )

            self.logger.info(f"處理數據可攜請求完成: {request_id}")
            return True

        except Exception as e:
            self.logger.error(f"處理數據可攜請求失敗: {e}")
            return False

    def _export_user_data(self, user_id: str, request_type: str) -> Dict[str, Any]:
        """導出用戶數據"""
        export_data = {
            "user_id": user_id,
            "export_time": datetime.now().isoformat(),
            "data": {},
        }

        # 導出偏好設置
        preferences = self.get_data_preferences(user_id)
        export_data["data"]["preferences"] = preferences

        # 導出同意記錄
        with get_db_connection() as conn:
            cursor = conn.execute(
                """
                SELECT purpose, category, status, granted_at, expires_at
                FROM consent_records
                WHERE user_id = ?
            """,
                (user_id,),
            )

            consents = []
            for row in cursor:
                consents.append(
                    {
                        "purpose": row[0],
                        "category": row[1],
                        "status": row[2],
                        "granted_at": row[3],
                        "expires_at": row[4],
                    }
                )
            export_data["data"]["consents"] = consents

        # 導出保留策略
        retention_policies = self.get_retention_policies(user_id)
        export_data["data"]["retention_policies"] = [
            {
                "category": p.category.value,
                "retention_days": p.retention_days,
                "auto_delete": p.auto_delete,
                "legal_basis": p.legal_basis,
            }
            for p in retention_policies
        ]

        return export_data

    def delete_user_data(
        self,
        user_id: str,
        category: Optional[DataCategory] = None,
        verify_password: str = "",
    ) -> bool:
        """
        刪除用戶數據

        Args:
            user_id: 用戶ID
            category: 數據類別（None表示刪除所有）
            verify_password: 密碼驗證

        Returns:
            bool: 是否成功
        """
        try:
            # TODO: 實現密碼驗證
            # if not self._verify_password(user_id, verify_password):
            #     return False

            with get_db_connection() as conn:
                if category:
                    # 刪除特定類別數據
                    conn.execute(
                        """
                        DELETE FROM sovereignty_controls
                        WHERE user_id = ? AND category = ?
                    """,
                        (user_id, category.value),
                    )
                else:
                    # 刪除所有數據
                    conn.execute(
                        "DELETE FROM sovereignty_controls WHERE user_id = ?", (user_id,)
                    )
                    conn.execute(
                        "DELETE FROM consent_records WHERE user_id = ?", (user_id,)
                    )
                    conn.execute(
                        "DELETE FROM data_retention_policies WHERE user_id = ?",
                        (user_id,),
                    )

            # 刪除導出文件
            export_dir = Path(f"data / exports/{user_id}")
            if export_dir.exists() and category is None:
                shutil.rmtree(export_dir)

            self.logger.info(
                f"刪除用戶數據: {user_id}, 類別: {category.value if category else 'all'}"
            )
            return True

        except Exception as e:
            self.logger.error(f"刪除用戶數據失敗: {e}")
            return False

    def get_data_location_preference(self, user_id: str) -> DataLocation:
        """
        獲取數據位置偏好

        Args:
            user_id: 用戶ID

        Returns:
            DataLocation: 數據存儲位置
        """
        preferences = self.get_data_preferences(user_id, DataCategory.PERSONAL_INFO)
        location = preferences.get(DataCategory.PERSONAL_INFO.value, {}).get(
            "data_location"
        )

        if location:
            try:
                return DataLocation(location)
            except ValueError:
                pass

        return DataLocation.REGION_HK  # 默認香港

    def set_data_location_preference(
        self, user_id: str, location: DataLocation
    ) -> bool:
        """
        設置數據位置偏好

        Args:
            user_id: 用戶ID
            location: 數據存儲位置

        Returns:
            bool: 是否成功
        """
        return self.set_data_preference(
            user_id, DataCategory.PERSONAL_INFO, "data_location", location.value
        )
