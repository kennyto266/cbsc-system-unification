"""
PDPA合規管理
實現新加坡個人數據保護法和香港PDPA要求
"""

import json
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .audit_logger import AuditLogger


class ConsentType(str, Enum):
    """同意類型"""

    EXPLICIT = "explicit"
    IMPLIED = "implied"
    EXPRESSED = "expressed"


class PurposeLimitation(str, Enum):
    """目的限制"""

    PRIMARY = "primary"
    SECONDARY = "secondary"


class DataRetention(BaseModel):
    """數據保留政策"""

    purpose: str
    retention_period: int  # 天數
    legal_basis: str
    created_at: datetime = Field(default_factory=datetime.now)


class PDPAData(BaseModel):
    """PDPA數據"""

    subject_id: str
    data_type: str
    purpose: str
    collected_at: datetime = Field(default_factory=datetime.now)
    consent_type: ConsentType
    consent_obtained: bool
    purpose_limitation: PurposeLimitation
    retention_policy: Optional[DataRetention] = None


class PDPARequest(BaseModel):
    """PDPA請求"""

    request_id: str
    subject_id: str
    request_type: str  # access, correction, withdrawal
    status: str = "pending"
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    response_data: Optional[Dict[str, Any]] = None
    verified: bool = False


class PDPAError(Exception):
    """PDPA相關錯誤"""

    pass


class PDPAManager:
    """PDPA合規管理器"""

    def __init__(self, audit_logger: AuditLogger = None):
        """
        初始化PDPA管理器

        Args:
            audit_logger: 審計日誌記錄器
        """
        self.audit_logger = audit_logger or AuditLogger()
        self.data_records: Dict[str, PDPAData] = {}
        self.retention_policies: Dict[str, DataRetention] = {}
        self.requests: Dict[str, PDPARequest] = {}
        self.consent_withdrawals: List[str] = []

    def record_data_collection(
        self,
        subject_id: str,
        data_type: str,
        purpose: str,
        consent_type: ConsentType,
        consent_obtained: bool,
        purpose_limitation: PurposeLimitation = PurposeLimitation.PRIMARY,
    ) -> str:
        """
        記錄數據收集

        Args:
            subject_id: 數據主體ID
            data_type: 數據類型
            purpose: 收集目的
            consent_type: 同意類型
            consent_obtained: 是否獲得同意
            purpose_limitation: 目的限制

        Returns:
            記錄ID
        """
        if not consent_obtained and consent_type == ConsentType.EXPLICIT:
            raise PDPAError("需要明確同意才能收集數據")

        record_id = str(uuid.uuid4())

        pdpa_data = PDPAData(
            subject_id=subject_id,
            data_type=data_type,
            purpose=purpose,
            consent_type=consent_type,
            consent_obtained=consent_obtained,
            purpose_limitation=purpose_limitation,
        )

        self.data_records[record_id] = pdpa_data

        # 記錄審計日誌
        self.audit_logger.log(
            event_type="compliance",
            action="data_collection_recorded",
            user_id=subject_id,
            resource="pdpa_data",
            details={
                "record_id": record_id,
                "data_type": data_type,
                "purpose": purpose,
                "consent_obtained": consent_obtained,
            },
        )

        return record_id

    def verify_consent(
        self, subject_id: str, purpose: str, data_types: List[str]
    ) -> bool:
        """
        驗證同意

        Args:
            subject_id: 數據主體ID
            purpose: 目的
            data_types: 數據類型列表

        Returns:
            是否有有效同意
        """
        for record in self.data_records.values():
            if (
                record.subject_id == subject_id
                and record.purpose == purpose
                and record.data_type in data_types
                and record.consent_obtained
            ):
                return True

        # 記錄審計日誌
        self.audit_logger.log(
            event_type="compliance",
            action="consent_verification_failed",
            user_id=subject_id,
            resource="pdpa_consent",
            status="failure",
            details={"purpose": purpose, "data_types": data_types},
            risk_score=60,
        )

        return False

    def set_retention_policy(
        self, purpose: str, retention_period: int, legal_basis: str
    ) -> str:
        """
        設置數據保留政策

        Args:
            purpose: 目的
            retention_period: 保留期限(天)
            legal_basis: 法律依據

        Returns:
            政策ID
        """
        policy_id = str(uuid.uuid4())

        policy = DataRetention(
            purpose=purpose, retention_period=retention_period, legal_basis=legal_basis
        )

        self.retention_policies[policy_id] = policy

        # 記錄審計日誌
        self.audit_logger.log(
            event_type="compliance",
            action="retention_policy_set",
            user_id="system",
            resource="pdpa_retention",
            details={
                "policy_id": policy_id,
                "purpose": purpose,
                "retention_period_days": retention_period,
            },
        )

        return policy_id

    def apply_retention_policy(self, record_id: str, policy_id: str) -> bool:
        """
        應用保留政策

        Args:
            record_id: 記錄ID
            policy_id: 政策ID

        Returns:
            是否成功
        """
        if record_id not in self.data_records:
            return False

        if policy_id not in self.retention_policies:
            return False

        record = self.data_records[record_id]
        policy = self.retention_policies[policy_id]

        if record.purpose != policy.purpose:
            return False

        record.retention_policy = policy

        # 記錄審計日誌
        self.audit_logger.log(
            event_type="compliance",
            action="retention_policy_applied",
            user_id=record.subject_id,
            resource="pdpa_retention",
            details={
                "record_id": record_id,
                "policy_id": policy_id,
                "purpose": policy.purpose,
            },
        )

        return True

    def create_access_request(self, subject_id: str, requested_data: List[str]) -> str:
        """
        創建數據訪問請求

        Args:
            subject_id: 數據主體ID
            requested_data: 請求的數據類型

        Returns:
            請求ID
        """
        request_id = str(uuid.uuid4())

        request = PDPARequest(
            request_id=request_id,
            subject_id=subject_id,
            request_type="access",
            response_data={"requested_data": requested_data},
        )

        self.requests[request_id] = request

        # 記錄審計日誌
        self.audit_logger.log(
            event_type="compliance",
            action="pdpa_access_request_created",
            user_id=subject_id,
            resource="pdpa_request",
            details={"request_id": request_id, "requested_data": requested_data},
        )

        return request_id

    def create_correction_request(
        self, subject_id: str, data_to_correct: Dict[str, Any]
    ) -> str:
        """
        創建數據更正請求

        Args:
            subject_id: 數據主體ID
            data_to_correct: 需要更正的數據

        Returns:
            請求ID
        """
        request_id = str(uuid.uuid4())

        request = PDPARequest(
            request_id=request_id,
            subject_id=subject_id,
            request_type="correction",
            response_data={"data_to_correct": data_to_correct},
        )

        self.requests[request_id] = request

        # 記錄審計日誌
        self.audit_logger.log(
            event_type="compliance",
            action="pdpa_correction_request_created",
            user_id=subject_id,
            resource="pdpa_request",
            details={"request_id": request_id, "data_to_correct": data_to_correct},
        )

        return request_id

    def withdraw_consent(
        self, subject_id: str, purpose: str, data_types: List[str]
    ) -> bool:
        """
        撤回同意

        Args:
            subject_id: 數據主體ID
            purpose: 目的
            data_types: 數據類型

        Returns:
            是否成功
        """
        # 記錄撤回
        withdrawal_id = str(uuid.uuid4())
        self.consent_withdrawals.append(withdrawal_id)

        # 檢查是否有對應的記錄
        for record_id, record in list(self.data_records.items()):
            if (
                record.subject_id == subject_id
                and record.purpose == purpose
                and record.data_type in data_types
            ):
                # 標記為撤回同意
                record.consent_obtained = False

        # 記錄審計日誌
        self.audit_logger.log(
            event_type="compliance",
            action="consent_withdrawn",
            user_id=subject_id,
            resource="pdpa_consent",
            details={
                "withdrawal_id": withdrawal_id,
                "purpose": purpose,
                "data_types": data_types,
            },
        )

        return True

    def check_data_minimization(self, purpose: str, collected_data: List[str]) -> bool:
        """
        檢查數據最小化

        Args:
            purpose: 目的
            collected_data: 收集的數據

        Returns:
            是否符合數據最小化原則
        """
        # 這裡需要根據業務邏輯驗證
        # 例如：對於簡單的查詢，不需要收集所有個人信息

        # 簡化示例：檢查收集的數據是否超出必要範圍
        essential_data = {
            "account_creation": ["name", "email", "phone"],
            "trading": ["trading_id", "amount", "timestamp"],
            "reporting": ["report_id", "data_summary"],
        }

        if purpose in essential_data:
            excess_data = set(collected_data) - set(essential_data[purpose])
            if excess_data:
                # 記錄審計日誌
                self.audit_logger.log(
                    event_type="compliance",
                    action="data_minimization_violation",
                    user_id="system",
                    resource="pdpa_compliance",
                    status="warning",
                    details={"purpose": purpose, "excess_data": list(excess_data)},
                    risk_score=50,
                )
                return False

        return True

    def validate_data_accuracy(self, subject_id: str, data: Dict[str, Any]) -> bool:
        """
        驗證數據準確性

        Args:
            subject_id: 數據主體ID
            data: 數據

        Returns:
            數據是否準確
        """
        # 這裡需要實現數據驗證邏輯
        # 例如：檢查郵件格式、電話格式等

        errors = []

        # 檢查郵件格式
        if "email" in data:
            email = data["email"]
            if "@" not in email or "." not in email:
                errors.append("無效的郵件格式")

        # 檢查電話格式
        if "phone" in data:
            phone = data["phone"]
            if not phone.startswith("+") and not phone.startswith("0"):
                errors.append("無效的電話格式")

        if errors:
            # 記錄審計日誌
            self.audit_logger.log(
                event_type="compliance",
                action="data_accuracy_validation_failed",
                user_id=subject_id,
                resource="pdpa_compliance",
                status="failure",
                details={"errors": errors},
            )
            return False

        return True

    def export_compliance_report(self) -> str:
        """
        導出PDPA合規報告

        Returns:
            JSON格式的合規報告
        """
        report = {
            "generated_at": datetime.now().isoformat(),
            "compliance_framework": "PDPA",
            "summary": {
                "total_data_records": len(self.data_records),
                "active_requests": len(
                    [r for r in self.requests.values() if r.status == "pending"]
                ),
                "consent_withdrawals": len(self.consent_withdrawals),
                "retention_policies": len(self.retention_policies),
            },
            "data_records": [record.dict() for record in self.data_records.values()],
            "retention_policies": [
                policy.dict() for policy in self.retention_policies.values()
            ],
            "requests": [request.dict() for request in self.requests.values()],
            "consent_withdrawals": self.consent_withdrawals,
        }

        return json.dumps(report, indent=2, default=str)
