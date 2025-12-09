"""
GDPR合規管理
實現歐盟通用數據保護條例的所有要求
"""

import json
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .audit_logger import AuditLogger


class DataSubjectRights(str, Enum):
    """數據主體權利"""

    ACCESS = "access"
    RECTIFICATION = "rectification"
    ERASURE = "erasure"
    PORTABILITY = "portability"
    RESTRICTION = "restriction"
    OBJECTION = "objection"
    WITHDRAW_CONSENT = "withdraw_consent"


class DataCategory(str, Enum):
    """數據類別"""

    PERSONAL_IDENTIFIERS = "personal_identifiers"
    FINANCIAL_DATA = "financial_data"
    TRADING_DATA = "trading_data"
    BEHAVIORAL_DATA = "behavioral_data"
    TECHNICAL_DATA = "technical_data"


class DataProcessingRecord(BaseModel):
    """數據處理記錄"""

    processing_id: str
    purpose: str
    data_category: DataCategory
    data_types: List[str]
    legal_basis: str
    retention_period: int  # 天數
    recipients: List[str]
    third_country_transfers: bool
    safeguards: Optional[List[str]] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None


class DataSubjectRequest(BaseModel):
    """數據主體請求"""

    request_id: str
    subject_id: str
    rights: List[DataSubjectRights]
    status: str = "pending"
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    response_data: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


class GDPRManager:
    """GDPR合規管理器"""

    def __init__(self, audit_logger: AuditLogger = None):
        """
        初始化GDPR管理器

        Args:
            audit_logger: 審計日誌記錄器
        """
        self.audit_logger = audit_logger or AuditLogger()
        self.processing_records: Dict[str, DataProcessingRecord] = {}
        self.data_subject_requests: Dict[str, DataSubjectRequest] = {}
        self.consent_records: Dict[str, List[Dict]] = {}

    def register_data_processing(
        self,
        purpose: str,
        data_category: DataCategory,
        data_types: List[str],
        legal_basis: str,
        retention_period: int,
        recipients: List[str] = None,
        third_country_transfers: bool = False,
        safeguards: List[str] = None,
    ) -> str:
        """
        註冊數據處理活動

        Args:
            purpose: 處理目的
            data_category: 數據類別
            data_types: 數據類型列表
            legal_basis: 法律依據
            retention_period: 保留期限(天)
            recipients: 接收者列表
            third_country_transfers: 是否向第三國傳輸
            safeguards: 保障措施

        Returns:
            處理記錄ID
        """
        processing_id = str(uuid.uuid4())

        record = DataProcessingRecord(
            processing_id=processing_id,
            purpose=purpose,
            data_category=data_category,
            data_types=data_types,
            legal_basis=legal_basis,
            retention_period=retention_period,
            recipients=recipients or [],
            third_country_transfers=third_country_transfers,
            safeguards=safeguards,
        )

        self.processing_records[processing_id] = record

        # 記錄審計日誌
        self.audit_logger.log(
            event_type="compliance",
            action="data_processing_registered",
            user_id="system",
            resource="gdpr_processor",
            details={
                "processing_id": processing_id,
                "purpose": purpose,
                "data_category": data_category,
                "legal_basis": legal_basis,
            },
        )

        return processing_id

    def record_consent(
        self,
        subject_id: str,
        purpose: str,
        consent_given: bool,
        consent_text: str,
        ip_address: str = None,
        user_agent: str = None,
    ) -> str:
        """
        記錄同意

        Args:
            subject_id: 數據主體ID
            purpose: 同意目的
            consent_given: 是否給予同意
            consent_text: 同意文本
            ip_address: IP地址
            user_agent: 用戶代理

        Returns:
            同意記錄ID
        """
        consent_id = str(uuid.uuid4())

        if subject_id not in self.consent_records:
            self.consent_records[subject_id] = []

        consent_record = {
            "consent_id": consent_id,
            "subject_id": subject_id,
            "purpose": purpose,
            "consent_given": consent_given,
            "consent_text": consent_text,
            "timestamp": datetime.now().isoformat(),
            "ip_address": ip_address or "unknown",
            "user_agent": user_agent or "",
        }

        self.consent_records[subject_id].append(consent_record)

        # 記錄審計日誌
        self.audit_logger.log(
            event_type="compliance",
            action="consent_recorded",
            user_id=subject_id,
            resource="gdpr_consent",
            details={
                "consent_id": consent_id,
                "purpose": purpose,
                "consent_given": consent_given,
            },
        )

        return consent_id

    def create_data_subject_request(
        self, subject_id: str, rights: List[DataSubjectRights], details: str = None
    ) -> str:
        """
        創建數據主體權利請求

        Args:
            subject_id: 數據主體ID
            rights: 請求的權利
            details: 詳細信息

        Returns:
            請求ID
        """
        request_id = str(uuid.uuid4())

        request = DataSubjectRequest(
            request_id=request_id, subject_id=subject_id, rights=rights, notes=details
        )

        self.data_subject_requests[request_id] = request

        # 記錄審計日誌
        self.audit_logger.log(
            event_type="compliance",
            action="data_subject_request_created",
            user_id=subject_id,
            resource="gdpr_request",
            details={"request_id": request_id, "rights": [r.value for r in rights]},
        )

        return request_id

    def process_data_subject_request(
        self, request_id: str, response_data: Dict[str, Any], notes: str = None
    ) -> bool:
        """
        處理數據主體請求

        Args:
            request_id: 請求ID
            response_data: 響應數據
            notes: 備註

        Returns:
            是否成功
        """
        if request_id not in self.data_subject_requests:
            return False

        request = self.data_subject_requests[request_id]
        request.status = "completed"
        request.completed_at = datetime.now()
        request.response_data = response_data
        if notes:
            request.notes = notes

        # 記錄審計日誌
        self.audit_logger.log(
            event_type="compliance",
            action="data_subject_request_processed",
            user_id=request.subject_id,
            resource="gdpr_request",
            details={
                "request_id": request_id,
                "status": "completed",
                "rights": [r.value for r in request.rights],
            },
        )

        return True

    def handle_data_breach(
        self,
        breach_type: str,
        affected_data: List[str],
        affected_subjects: List[str],
        description: str,
        mitigation_steps: List[str],
    ) -> str:
        """
        處理數據洩露

        Args:
            breach_type: 洩露類型
            affected_data: 受影響的數據
            affected_subjects: 受影響的主體
            description: 描述
            mitigation_steps: 緩解步驟

        Returns:
            事件ID
        """
        breach_id = str(uuid.uuid4())

        # 記錄審計日誌
        self.audit_logger.log(
            event_type="security",
            action="data_breach_detected",
            user_id="system",
            resource="gdpr_breach",
            status="critical",
            details={
                "breach_id": breach_id,
                "breach_type": breach_type,
                "affected_data": affected_data,
                "affected_subjects_count": len(affected_subjects),
                "description": description,
                "mitigation_steps": mitigation_steps,
                "report_required": True,
                "notification_deadline": (
                    datetime.now() + timedelta(hours=72)
                ).isoformat(),
            },
            risk_score=100,
        )

        # GDPR要求：72小時內向監管機構報告
        return breach_id

    def check_retention_compliance(self) -> List[Dict[str, Any]]:
        """
        檢查數據保留合規性

        Returns:
            需要刪除的數據記錄
        """
        to_delete = []
        current_time = datetime.now()

        for processing_id, record in self.processing_records.items():
            # 計算是否超過保留期限
            # 這裡需要根據實際創建時間計算
            # 簡化示例：檢查記錄中的創建時間
            created_at = record.created_at
            retention_end = created_at + timedelta(days=record.retention_period)

            if current_time > retention_end:
                to_delete.append(
                    {
                        "processing_id": processing_id,
                        "purpose": record.purpose,
                        "retention_expired": True,
                        "expired_days": (current_time - retention_end).days,
                    }
                )

        # 記錄審計日誌
        self.audit_logger.log(
            event_type="compliance",
            action="retention_compliance_check",
            user_id="system",
            resource="gdpr_compliance",
            details={"records_to_delete": len(to_delete)},
        )

        return to_delete

    def export_processing_activities(self) -> str:
        """
        導出所有處理活動記錄

        Returns:
            JSON格式的處理活動記錄
        """
        activities = {
            "generated_at": datetime.now().isoformat(),
            "total_activities": len(self.processing_records),
            "activities": [
                record.dict() for record in self.processing_records.values()
            ],
            "data_subject_requests": [
                request.dict() for request in self.data_subject_requests.values()
            ],
            "consent_records": self.consent_records,
        }

        return json.dumps(activities, indent=2, default=str)

    def get_dpo_contact(self) -> Dict[str, str]:
        """
        獲取數據保護官聯絡信息

        Returns:
            DPO聯絡信息
        """
        return {
            "name": "Data Protection Officer",
            "email": "dpo@company.com",
            "phone": "+852 - XXXX - XXXX",
            "address": "Hong Kong Office",
            "role": "Data Protection Officer",
        }
