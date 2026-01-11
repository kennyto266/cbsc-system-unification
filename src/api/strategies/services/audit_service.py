"""
審計日誌服務
Audit Log Service

基於BaseBusinessService實現的審計日誌服務，
記錄和追蹤系統中所有重要操作。

職責：
- 操作日誌記錄
- 審計事件管理
- 合規報告生成
- 日誌查詢和分析
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
from enum import Enum
import json

from .base_business_service import BaseBusinessService
from ..models.audit import (
    AuditLog, AuditEventType, AuditSeverity,
    AuditFilter, AuditReport
)
from ..schemas.audit import (
    AuditLogCreate, AuditLogResponse,
    AuditReportResponse
)
from ..utils.validators import AuditValidator
from ..utils.permissions import AuditPermissionChecker
from ..utils.events import EventBus
from ..utils.cache import CacheManager
from ..repositories.audit_repository import AuditRepository

logger = logging.getLogger(__name__)


class AuditService(BaseBusinessService[AuditLog, AuditLogCreate, None, AuditLogResponse]):
    """
    審計日誌服務

    提供完整的審計功能，包括：
    - 操作日誌記錄
    - 事件追蹤
    - 合規報告
    - 日誌分析
    """

    def __init__(
        self,
        audit_repo: AuditRepository,
        cache_manager: CacheManager,
        validator: AuditValidator,
        permission_checker: AuditPermissionChecker,
        event_bus: EventBus
    ):
        super().__init__(
            repository=audit_repo,
            cache_manager=cache_manager,
            validator=validator,
            permission_checker=permission_checker,
            event_bus=event_bus,
            cache_prefix="audit",
            default_ttl=900  # 15分鐘緩存
        )
        self.audit_repo = audit_repo

    def get_model_class(self):
        """獲取審計日誌模型類"""
        return AuditLog

    def get_response_schema(self):
        """獲取審計日誌響應模式類"""
        return AuditLogResponse

    async def log_event(
        self,
        event_type: AuditEventType,
        user_id: Optional[str],
        resource_type: str,
        resource_id: Optional[str],
        action: str,
        details: Optional[Dict[str, Any]] = None,
        severity: AuditSeverity = AuditSeverity.INFO,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> AuditLogResponse:
        """
        記錄審計事件

        Args:
            event_type: 事件類型
            user_id: 用戶ID
            resource_type: 資源類型
            resource_id: 資源ID
            action: 執行的操作
            details: 事件詳情
            severity: 事件嚴重程度
            ip_address: IP地址
            user_agent: 用戶代理
            session_id: 會話ID

        Returns:
            創建的審計日誌響應
        """
        # 創建審計日誌
        audit_log = AuditLog(
            id=f"audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(str(details)) % 1000000}",
            event_type=event_type,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            details=details or {},
            severity=severity,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            timestamp=datetime.now()
        )

        # 保存到數據庫
        audit_log = await self.audit_repo.create(audit_log)

        # 轉換為響應格式
        response = AuditLogResponse.model_validate(audit_log)

        # 觸發審計事件
        await self.events.emit("audit_event_logged", {
            "event_type": event_type.value,
            "user_id": user_id,
            "resource_type": resource_type,
            "action": action,
            "severity": severity.value
        })

        # 如果是高嚴重程度事件，觸發告警
        if severity in [AuditSeverity.HIGH, AuditSeverity.CRITICAL]:
            await self.events.emit("security_alert", {
                "event_type": event_type.value,
                "severity": severity.value,
                "details": details,
                "user_id": user_id,
                "ip_address": ip_address
            })

        return response

    async def search_audit_logs(
        self,
        filters: AuditFilter,
        page: int = 1,
        page_size: int = 50,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        搜索審計日誌

        Args:
            filters: 搜索過濾條件
            page: 頁碼
            page_size: 每頁大小
            user_id: 查詢者ID（用於權限檢查）

        Returns:
            審計日誌列表
        """
        # 權限檢查
        if user_id:
            await self.permission.check_search_permission(user_id, filters)

        # 構建緩存鍵
        cache_key = f"audit:search:{hash(str(filters.dict()))}:{page}:{page_size}:{user_id}"

        # 嘗試從緩存獲取
        cached_result = await self.cache.get(cache_key)
        if cached_result:
            return cached_result

        # 執行搜索
        logs, total_count = await self.audit_repo.search_logs(
            filters=filters,
            page=page,
            page_size=page_size
        )

        # 計算總頁數
        total_pages = (total_count + page_size - 1) // page_size

        # 轉換為響應格式
        result = {
            "logs": [AuditLogResponse.model_validate(log) for log in logs],
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "filters": filters.dict()
        }

        # 緩存結果（搜索結果緩存時間較短）
        await self.cache.set(cache_key, result, ttl=120)  # 2分鐘緩存

        return result

    async def generate_compliance_report(
        self,
        report_type: str,
        start_date: datetime,
        end_date: datetime,
        filters: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> AuditReportResponse:
        """
        生成合規報告

        Args:
            report_type: 報告類型
            start_date: 開始日期
            end_date: 結束日期
            filters: 額外過濾條件
            user_id: 請求者ID

        Returns:
            合規報告響應
        """
        # 權限檢查
        if user_id:
            await self.permission.check_report_permission(user_id, report_type)

        # 構建緩存鍵
        cache_key = f"audit:report:{report_type}:{start_date}:{end_date}:{hash(str(filters))}"

        # 嘗試從緩存獲取
        cached_report = await self.cache.get(cache_key)
        if cached_report:
            return cached_report

        # 生成報告
        report_data = await self.audit_repo.generate_report(
            report_type=report_type,
            start_date=start_date,
            end_date=end_date,
            filters=filters or {}
        )

        # 創建報告對象
        report = AuditReport(
            id=f"report_{report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            report_type=report_type,
            start_date=start_date,
            end_date=end_date,
            generated_at=datetime.now(),
            generated_by=user_id,
            data=report_data
        )

        # 保存報告
        report = await self.audit_repo.create_report(report)

        # 轉換為響應格式
        response = AuditReportResponse.model_validate(report)

        # 緩存報告
        await self.cache.set(cache_key, response, ttl=3600)  # 1小時緩存

        # 觸發事件
        await self.events.emit("compliance_report_generated", {
            "report_type": report_type,
            "generated_by": user_id,
            "start_date": start_date,
            end_date=end_date
        })

        return response

    async def get_user_activity_summary(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        獲取用戶活動摘要

        Args:
            user_id: 用戶ID
            days: 統計天數

        Returns:
            活動摘要
        """
        # 檢查緩存
        cache_key = f"audit:user_summary:{user_id}:{days}"
        cached_summary = await self.cache.get(cache_key)
        if cached_summary:
            return cached_summary

        # 計算日期範圍
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # 獲取活動數據
        summary = await self.audit_repo.get_user_activity_summary(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date
        )

        # 緩存結果
        await self.cache.set(cache_key, summary, ttl=600)  # 10分鐘緩存

        return summary

    async def detect_anomalous_activities(
        self,
        time_window: int = 24,  # 小時
        threshold: float = 2.0  # 標準差閾值
    ) -> List[Dict[str, Any]]:
        """
        檢測異常活動

        Args:
            time_window: 時間窗口（小時）
            threshold: 異常檢測閾值

        Returns:
            異常活動列表
        """
        # 檢查緩存
        cache_key = f"audit:anomalies:{time_window}:{threshold}"
        cached_anomalies = await self.cache.get(cache_key)
        if cached_anomalies:
            return cached_anomalies

        # 執行異常檢測
        anomalies = await self.audit_repo.detect_anomalies(
            time_window=time_window,
            threshold=threshold
        )

        # 緩存結果
        await self.cache.set(cache_key, anomalies, ttl=300)  # 5分鐘緩存

        # 如果發現異常，觸發告警
        if anomalies:
            await self.events.emit("anomalous_activities_detected", {
                "count": len(anomalies),
                "time_window": time_window,
                "threshold": threshold
            })

        return anomalies

    async def get_resource_access_history(
        self,
        resource_type: str,
        resource_id: str,
        days: int = 30
    ) -> List[AuditLogResponse]:
        """
        獲取資源訪問歷史

        Args:
            resource_type: 資源類型
            resource_id: 資源ID
            days: 查詢天數

        Returns:
            訪問歷史列表
        """
        # 檢查緩存
        cache_key = f"audit:resource_history:{resource_type}:{resource_id}:{days}"
        cached_history = await self.cache.get(cache_key)
        if cached_history:
            return cached_history

        # 計算日期範圍
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # 獲取訪問歷史
        history = await self.audit_repo.get_resource_access_history(
            resource_type=resource_type,
            resource_id=resource_id,
            start_date=start_date,
            end_date=end_date
        )

        # 轉換為響應格式
        response = [AuditLogResponse.model_validate(log) for log in history]

        # 緩存結果
        await self.cache.set(cache_key, response, ttl=300)  # 5分鐘緩存

        return response

    async def export_audit_logs(
        self,
        filters: AuditFilter,
        format: str = "csv",
        user_id: Optional[str] = None
    ) -> str:
        """
        導出審計日誌

        Args:
            filters: 導出過濾條件
            format: 導出格式 (csv, json, excel)
            user_id: 請求者ID

        Returns:
            導出文件路徑
        """
        # 權限檢查
        if user_id:
            await self.permission.check_export_permission(user_id)

        # 生成導出文件
        file_path = await self.audit_repo.export_logs(
            filters=filters,
            format=format
        )

        # 記錄導出操作
        await self.log_event(
            event_type=AuditEventType.DATA_EXPORT,
            user_id=user_id,
            resource_type="audit_logs",
            action="export",
            details={
                "filters": filters.dict(),
                "format": format,
                "file_path": file_path
            },
            severity=AuditSeverity.INFO
        )

        # 觸發事件
        await self.events.emit("audit_logs_exported", {
            "exported_by": user_id,
            "format": format,
            "file_path": file_path
        })

        return file_path

    async def cleanup_old_logs(self, retention_days: int = 365) -> Dict[str, Any]:
        """
        清理舊日誌

        Args:
            retention_days: 保留天數

        Returns:
            清理統計信息
        """
        # 權限檢查 - 需要管理員權限
        # await self.permission.check_admin_permission(user_id)

        # 執行清理
        cleanup_stats = await self.audit_repo.cleanup_old_logs(retention_days)

        # 記錄清理操作
        await self.log_event(
            event_type=AuditEventType.SYSTEM_MAINTENANCE,
            user_id=None,  # 系統操作
            resource_type="audit_logs",
            action="cleanup",
            details=cleanup_stats,
            severity=AuditSeverity.INFO
        )

        # 清除緩存
        patterns = [
            "audit:*",
            "audit:search:*",
            "audit:report:*"
        ]
        for pattern in patterns:
            await self.cache.clear_pattern(pattern)

        return cleanup_stats

    # 重寫基類方法
    async def _check_unique_constraints(self, request: AuditLogCreate, user_id: int) -> None:
        """審計日誌不需要唯一性檢查"""
        pass

    async def _get_related_data(self, item: AuditLog, user_id: Optional[int]) -> Dict[str, Any]:
        """獲取審計日誌相關數據"""
        related_data = {}

        # 如果是用戶相關事件，獲取用戶信息
        if item.user_id:
            try:
                user = await self.audit_repo.get_user_by_id(item.user_id)
                if user:
                    related_data["user"] = {
                        "username": user.username,
                        "email": user.email
                    }
            except:
                pass  # 用戶可能已被刪除

        # 獲取相關資源信息（如果可能）
        if item.resource_id:
            related_data["resource_info"] = await self._get_resource_info(
                item.resource_type,
                item.resource_id
            )

        return related_data

    async def _get_resource_info(self, resource_type: str, resource_id: str) -> Dict[str, Any]:
        """獲取資源信息"""
        # 根據資源類型獲取相關信息
        # 這裡可以根據需要實現具體的資源信息獲取邏輯
        return {
            "type": resource_type,
            "id": resource_id
        }