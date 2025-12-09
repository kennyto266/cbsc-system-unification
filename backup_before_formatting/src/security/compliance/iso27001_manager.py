"""
ISO 27001信息安全管理
實現ISO 27001:2013標準的控制措施
"""

import json
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .audit_logger import AuditLogger


class ControlCategory(str, Enum):
    """控制類別"""

    INFORMATION_SECURITY_POLICIES = "A.5"
    ORGANIZATION_OF_INFORMATION_SECURITY = "A.6"
    HUMAN_RESOURCE_SECURITY = "A.7"
    ASSET_MANAGEMENT = "A.8"
    ACCESS_CONTROL = "A.9"
    CRYPTOGRAPHY = "A.10"
    PHYSICAL_AND_ENVIRONMENTAL = "A.11"
    OPERATIONS_SECURITY = "A.12"
    COMMUNICATIONS_SECURITY = "A.13"
    SYSTEM_ACQUISITION = "A.14"
    SUPPLIER_RELATIONSHIPS = "A.15"
    INCIDENT_MANAGEMENT = "A.16"
    INFORMATION_SECURITY_ASPECTS = "A.17"
    COMPLIANCE = "A.18"


class ControlStatus(str, Enum):
    """控制狀態"""

    IMPLEMENTED = "implemented"
    PARTIAL = "partial"
    NOT_IMPLEMENTED = "not_implemented"
    NOT_APPLICABLE = "not_applicable"


class SecurityControl(BaseModel):
    """安全控制措施"""

    control_id: str
    category: ControlCategory
    title: str
    description: str
    status: ControlStatus
    implementation_details: Optional[str] = None
    evidence: Optional[List[str]] = None
    owner: str
    last_reviewed: datetime = Field(default_factory=datetime.now)
    next_review: Optional[datetime] = None
    risk_level: str = "medium"  # low, medium, high


class RiskAssessment(BaseModel):
    """風險評估"""

    assessment_id: str
    asset: str
    threat: str
    vulnerability: str
    impact: str  # low, medium, high, critical
    likelihood: str  # low, medium, high
    risk_level: str  # low, medium, high, critical
    treatment: str  # avoid, mitigate, transfer, accept
    owner: str
    created_at: datetime = Field(default_factory=datetime.now)
    review_date: Optional[datetime] = None


class ISO27001Manager:
    """ISO 27001合規管理器"""

    def __init__(self, audit_logger: AuditLogger = None):
        """
        初始化ISO 27001管理器

        Args:
            audit_logger: 審計日誌記錄器
        """
        self.audit_logger = audit_logger or AuditLogger()
        self.controls: Dict[str, SecurityControl] = {}
        self.risk_assessments: Dict[str, RiskAssessment] = {}
        self._initialize_controls()

    def _initialize_controls(self):
        """初始化標準控制措施"""
        # A.5 信息安全政策
        self.controls["A.5.1.1"] = SecurityControl(
            control_id="A.5.1.1",
            category=ControlCategory.INFORMATION_SECURITY_POLICIES,
            title="信息安全政策",
            description="制定信息安全政策",
            status=ControlStatus.PARTIAL,
            owner="CISO",
            risk_level="high",
        )

        # A.9 訪問控制
        self.controls["A.9.1.1"] = SecurityControl(
            control_id="A.9.1.1",
            category=ControlCategory.ACCESS_CONTROL,
            title="訪問控制政策",
            description="建立訪問控制政策",
            status=ControlStatus.IMPLEMENTED,
            owner="Security Team",
            risk_level="high",
        )

        # A.12 運營安全
        self.controls["A.12.1.1"] = SecurityControl(
            control_id="A.12.1.1",
            category=ControlCategory.OPERATIONS_SECURITY,
            title="操作程序",
            description="建立操作程序和責任",
            status=ControlStatus.IMPLEMENTED,
            owner="Operations Team",
            risk_level="high",
        )

        # A.16 信息安全事件管理
        self.controls["A.16.1.1"] = SecurityControl(
            control_id="A.16.1.1",
            category=ControlCategory.INCIDENT_MANAGEMENT,
            title="事件管理責任和程序",
            description="建立信息安全事件管理責任和程序",
            status=ControlStatus.PARTIAL,
            owner="Incident Response Team",
            risk_level="high",
        )

    def add_control(
        self,
        control_id: str,
        category: ControlCategory,
        title: str,
        description: str,
        status: ControlStatus,
        owner: str,
        risk_level: str = "medium",
        implementation_details: str = None,
    ) -> bool:
        """
        添加安全控制措施

        Args:
            control_id: 控制ID
            category: 控制類別
            title: 標題
            description: 描述
            status: 狀態
            owner: 負責人
            risk_level: 風險級別
            implementation_details: 實施細節

        Returns:
            是否成功
        """
        control = SecurityControl(
            control_id=control_id,
            category=category,
            title=title,
            description=description,
            status=status,
            owner=owner,
            risk_level=risk_level,
            implementation_details=implementation_details,
        )

        self.controls[control_id] = control

        # 記錄審計日誌
        self.audit_logger.log(
            event_type="compliance",
            action="iso27001_control_added",
            user_id="system",
            resource="iso27001_controls",
            details={"control_id": control_id, "category": category, "status": status},
        )

        return True

    def update_control_status(
        self, control_id: str, status: ControlStatus, evidence: List[str] = None
    ) -> bool:
        """
        更新控制措施狀態

        Args:
            control_id: 控制ID
            status: 新狀態
            evidence: 證據

        Returns:
            是否成功
        """
        if control_id not in self.controls:
            return False

        control = self.controls[control_id]
        control.status = status
        control.last_reviewed = datetime.now()

        if evidence:
            control.evidence = evidence

        # 記錄審計日誌
        self.audit_logger.log(
            event_type="compliance",
            action="iso27001_control_updated",
            user_id="system",
            resource="iso27001_controls",
            details={
                "control_id": control_id,
                "status": status,
                "evidence_count": len(evidence) if evidence else 0,
            },
        )

        return True

    def conduct_risk_assessment(
        self,
        asset: str,
        threat: str,
        vulnerability: str,
        impact: str,
        likelihood: str,
        treatment: str,
        owner: str,
        review_date: datetime = None,
    ) -> str:
        """
        進行風險評估

        Args:
            asset: 資產
            threat: 威脅
            vulnerability: 漏洞
            impact: 影響
            likelihood: 可能性
            treatment: 處理方式
            owner: 負責人
            review_date: 審查日期

        Returns:
            評估ID
        """
        assessment_id = (
            f"RA_{datetime.now().strftime('%Y % m % d')}_{len(self.risk_assessments)}"
        )

        # 計算風險級別
        impact_score = {"low": 1, "medium": 2, "high": 3, "critical": 4}[impact]
        likelihood_score = {"low": 1, "medium": 2, "high": 3}[likelihood]
        risk_score = impact_score * likelihood_score

        if risk_score <= 2:
            risk_level = "low"
        elif risk_score <= 6:
            risk_level = "medium"
        elif risk_score <= 9:
            risk_level = "high"
        else:
            risk_level = "critical"

        assessment = RiskAssessment(
            assessment_id=assessment_id,
            asset=asset,
            threat=threat,
            vulnerability=vulnerability,
            impact=impact,
            likelihood=likelihood,
            risk_level=risk_level,
            treatment=treatment,
            owner=owner,
            review_date=review_date,
        )

        self.risk_assessments[assessment_id] = assessment

        # 記錄審計日誌
        self.audit_logger.log(
            event_type="compliance",
            action="risk_assessment_conducted",
            user_id=owner,
            resource="iso27001_risk",
            details={
                "assessment_id": assessment_id,
                "asset": asset,
                "risk_level": risk_level,
                "treatment": treatment,
            },
            risk_score=60 if risk_level in ["high", "critical"] else 30,
        )

        return assessment_id

    def get_compliance_score(self) -> Dict[str, Any]:
        """
        獲取合規評分

        Returns:
            合規評分報告
        """
        total_controls = len(self.controls)
        implemented = len(
            [c for c in self.controls.values() if c.status == ControlStatus.IMPLEMENTED]
        )
        partial = len(
            [c for c in self.controls.values() if c.status == ControlStatus.PARTIAL]
        )
        not_implemented = len(
            [
                c
                for c in self.controls.values()
                if c.status == ControlStatus.NOT_IMPLEMENTED
            ]
        )

        compliance_score = (implemented + partial * 0.5) / total_controls * 100

        # 按類別統計
        by_category = {}
        for category in ControlCategory:
            category_controls = [
                c for c in self.controls.values() if c.category == category
            ]
            if category_controls:
                implemented_count = len(
                    [
                        c
                        for c in category_controls
                        if c.status == ControlStatus.IMPLEMENTED
                    ]
                )
                by_category[category] = {
                    "total": len(category_controls),
                    "implemented": implemented_count,
                    "compliance_rate": implemented_count / len(category_controls) * 100,
                }

        report = {
            "generated_at": datetime.now().isoformat(),
            "total_controls": total_controls,
            "implemented": implemented,
            "partial": partial,
            "not_implemented": not_implemented,
            "compliance_score": round(compliance_score, 2),
            "by_category": by_category,
            "risk_assessments_count": len(self.risk_assessments),
            "high_risk_assets": len(
                [
                    ra
                    for ra in self.risk_assessments.values()
                    if ra.risk_level in ["high", "critical"]
                ]
            ),
        }

        return report

    def generate_audit_report(self) -> str:
        """
        生成審計報告

        Returns:
            JSON格式的審計報告
        """
        report = {
            "generated_at": datetime.now().isoformat(),
            "standard": "ISO 27001:2013",
            "organization": "Hong Kong Quantitative Trading System",
            "compliance_score": self.get_compliance_score(),
            "controls": [control.dict() for control in self.controls.values()],
            "risk_assessments": [ra.dict() for ra in self.risk_assessments.values()],
            "recommendations": self._generate_recommendations(),
        }

        return json.dumps(report, indent=2, default=str)

    def _generate_recommendations(self) -> List[str]:
        """生成改進建議"""
        recommendations = []

        # 檢查未實施的控制
        not_implemented = [
            c
            for c in self.controls.values()
            if c.status == ControlStatus.NOT_IMPLEMENTED
        ]

        if not_implemented:
            recommendations.append(
                f"優先實施 {len(not_implemented)} 個未實施的控制措施"
            )

        # 檢查高風險資產
        high_risk = [
            ra
            for ra in self.risk_assessments.values()
            if ra.risk_level in ["high", "critical"]
        ]

        if high_risk:
            recommendations.append(f"對 {len(high_risk)} 個高風險資產進行風險緩解")

        # 檢查過期的審查
        now = datetime.now()
        overdue = [
            c for c in self.controls.values() if c.next_review and c.next_review < now
        ]

        if overdue:
            recommendations.append(f"更新 {len(overdue)} 個過期的控制措施審查")

        return recommendations
