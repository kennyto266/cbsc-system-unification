"""
數據保護影響評估(DPIA)管理器
實現GDPR第35條要求的DPIA流程
"""

import json
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from ..audit.audit_logger import AuditLogger


class ProcessingNature(str, Enum):
    """處理性質"""

    SYSTEMATIC_MONITORING = "systematic_monitoring"
    LARGE_SCALE_PROCESSING = "large_scale_processing"
    SPECIAL_CATEGORIES = "special_categories"
    PUBLIC_AREA_MONITORING = "public_area_monitoring"
    INNOVATIVE_TECHNOLOGY = "innovative_technology"
    PROFILING = "profiling"
    AUTOMATED_DECISION = "automated_decision"
    VULNERABLE_SUBJECTS = "vulnerable_subjects"
    DATA_MATCHING = "data_matching"
    NEW_PURPOSE = "new_purpose"


class RiskLevel(str, Enum):
    """風險級別"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class MitigationMeasure(BaseModel):
    """緩解措施"""

    measure_id: str
    description: str
    effectiveness: str  # high, medium, low
    status: str  # planned, implemented, verified
    owner: str
    deadline: Optional[datetime] = None


class DPIA(BaseModel):
    """數據保護影響評估"""

    dpia_id: str
    name: str
    description: str
    processing_nature: List[ProcessingNature]
    purpose: str
    legal_basis: str
    data_types: List[str]
    data_sources: List[str]
    data_subjects: List[str]
    processors: List[str]
    third_countries: List[str]
    data_volume: str  # small, medium, large, very_large
    retention_period: str
    created_at: datetime = Field(default_factory=datetime.now)
    assessed_by: str
    reviewed_by: Optional[str] = None
    status: str = "draft"  # draft, in_progress, completed, approved, rejected
    completion_date: Optional[datetime] = None
    risk_assessment: Optional[Dict[str, Any]] = None
    consultation_records: List[Dict[str, Any]] = Field(default_factory=list)
    mitigation_measures: List[MitigationMeasure] = Field(default_factory=list)
    dpo_opinion: Optional[str] = None
    residual_risk: Optional[RiskLevel] = None
    approval_status: Optional[str] = None


class DPIAManager:
    """DPIA管理器"""

    def __init__(self, audit_logger: AuditLogger = None):
        """
        初始化DPIA管理器

        Args:
            audit_logger: 審計日誌記錄器
        """
        self.audit_logger = audit_logger or AuditLogger()
        self.dpias: Dict[str, DPIA] = {}

    def create_dpia(
        self,
        name: str,
        description: str,
        processing_nature: List[ProcessingNature],
        purpose: str,
        legal_basis: str,
        data_types: List[str],
        data_sources: List[str],
        data_subjects: List[str],
        assessed_by: str,
        processors: List[str] = None,
        third_countries: List[str] = None,
        data_volume: str = "medium",
        retention_period: str = "1 year",
    ) -> str:
        """
        創建DPIA

        Args:
            name: DPIA名稱
            description: 描述
            processing_nature: 處理性質
            purpose: 目的
            legal_basis: 法律依據
            data_types: 數據類型
            data_sources: 數據源
            data_subjects: 數據主體
            assessed_by: 評估人
            processors: 處理者
            third_countries: 第三國
            data_volume: 數據量
            retention_period: 保留期限

        Returns:
            DPIA ID
        """
        dpia_id = str(uuid.uuid4())

        dpia = DPIA(
            dpia_id=dpia_id,
            name=name,
            description=description,
            processing_nature=processing_nature,
            purpose=purpose,
            legal_basis=legal_basis,
            data_types=data_types,
            data_sources=data_sources,
            data_subjects=data_subjects,
            assessed_by=assessed_by,
            processors=processors or [],
            third_countries=third_countries or [],
            data_volume=data_volume,
            retention_period=retention_period,
        )

        self.dpias[dpia_id] = dpia

        # 記錄審計日誌
        self.audit_logger.log(
            event_type="compliance",
            action="dpia_created",
            user_id=assessed_by,
            resource="dpia",
            details={
                "dpia_id": dpia_id,
                "name": name,
                "processing_nature": [n.value for n in processing_nature],
                "data_volume": data_volume,
            },
        )

        return dpia_id

    def assess_risks(self, dpia_id: str, risks: List[Dict[str, Any]]) -> bool:
        """
        評估風險

        Args:
            dpia_id: DPIA ID
            risks: 風險列表

        Returns:
            是否成功
        """
        if dpia_id not in self.dpias:
            return False

        dpia = self.dpias[dpia_id]

        # 計算整體風險級別
        risk_levels = [r.get("level", "low") for r in risks]
        if "very_high" in risk_levels:
            overall_risk = RiskLevel.VERY_HIGH
        elif "high" in risk_levels:
            overall_risk = RiskLevel.HIGH
        elif "medium" in risk_levels:
            overall_risk = RiskLevel.MEDIUM
        else:
            overall_risk = RiskLevel.LOW

        dpia.risk_assessment = {
            "risks": risks,
            "overall_risk": overall_risk,
            "risk_score": self._calculate_risk_score(risks),
            "assessed_at": datetime.now().isoformat(),
        }

        # 如果風險過高，記錄審計日誌
        if overall_risk in [RiskLevel.HIGH, RiskLevel.VERY_HIGH]:
            self.audit_logger.log(
                event_type="compliance",
                action="dpia_high_risk_detected",
                user_id=dpia.assessed_by,
                resource="dpia",
                status="warning",
                details={
                    "dpia_id": dpia_id,
                    "overall_risk": overall_risk,
                    "risk_count": len(risks),
                },
                risk_score=60 if overall_risk == RiskLevel.HIGH else 80,
            )

        return True

    def _calculate_risk_score(self, risks: List[Dict[str, Any]]) -> int:
        """計算風險評分"""
        score_mapping = {"low": 1, "medium": 2, "high": 3, "very_high": 4}
        total_score = sum(score_mapping.get(r.get("level", "low"), 1) for r in risks)
        return min(total_score, 100)

    def add_consultation_record(
        self,
        dpia_id: str,
        stakeholder: str,
        consultation_type: str,
        feedback: str,
        consultation_date: datetime = None,
    ) -> bool:
        """
        添加諮詢記錄

        Args:
            dpia_id: DPIA ID
            stakeholder: 利益相關者
            consultation_type: 諮詢類型
            feedback: 反饋
            consultation_date: 諮詢日期

        Returns:
            是否成功
        """
        if dpia_id not in self.dpias:
            return False

        record = {
            "stakeholder": stakeholder,
            "consultation_type": consultation_type,
            "feedback": feedback,
            "date": (consultation_date or datetime.now()).isoformat(),
        }

        self.dpias[dpia_id].consultation_records.append(record)

        # 記錄審計日誌
        self.audit_logger.log(
            event_type="compliance",
            action="dpia_consultation_added",
            user_id=self.dpias[dpia_id].assessed_by,
            resource="dpia",
            details={
                "dpia_id": dpia_id,
                "stakeholder": stakeholder,
                "consultation_type": consultation_type,
            },
        )

        return True

    def add_mitigation_measure(
        self,
        dpia_id: str,
        description: str,
        effectiveness: str,
        owner: str,
        deadline: datetime = None,
    ) -> str:
        """
        添加緩解措施

        Args:
            dpia_id: DPIA ID
            description: 描述
            effectiveness: 有效性
            owner: 負責人
            deadline: 截止日期

        Returns:
            措施ID
        """
        if dpia_id not in self.dpias:
            return ""

        measure_id = str(uuid.uuid4())

        measure = MitigationMeasure(
            measure_id=measure_id,
            description=description,
            effectiveness=effectiveness,
            status="planned",
            owner=owner,
            deadline=deadline,
        )

        self.dpias[dpia_id].mitigation_measures.append(measure)

        # 記錄審計日誌
        self.audit_logger.log(
            event_type="compliance",
            action="dpia_mitigation_added",
            user_id=owner,
            resource="dpia",
            details={
                "dpia_id": dpia_id,
                "measure_id": measure_id,
                "effectiveness": effectiveness,
            },
        )

        return measure_id

    def update_mitigation_status(
        self, dpia_id: str, measure_id: str, status: str
    ) -> bool:
        """
        更新緩解措施狀態

        Args:
            dpia_id: DPIA ID
            measure_id: 措施ID
            status: 新狀態

        Returns:
            是否成功
        """
        if dpia_id not in self.dpias:
            return False

        dpia = self.dpias[dpia_id]

        for measure in dpia.mitigation_measures:
            if measure.measure_id == measure_id:
                measure.status = status

                # 記錄審計日誌
                self.audit_logger.log(
                    event_type="compliance",
                    action="dpia_mitigation_updated",
                    user_id=measure.owner,
                    resource="dpia",
                    details={
                        "dpia_id": dpia_id,
                        "measure_id": measure_id,
                        "new_status": status,
                    },
                )

                return True

        return False

    def set_dpo_opinion(self, dpia_id: str, opinion: str, reviewed_by: str) -> bool:
        """
        設置DPO意見

        Args:
            dpia_id: DPIA ID
            opinion: 意見
            reviewed_by: 審查人

        Returns:
            是否成功
        """
        if dpia_id not in self.dpias:
            return False

        dpia = self.dpias[dpia_id]
        dpia.dpo_opinion = opinion
        dpia.reviewed_by = reviewed_by

        # 記錄審計日誌
        self.audit_logger.log(
            event_type="compliance",
            action="dpia_dpo_opinion_added",
            user_id=reviewed_by,
            resource="dpia",
            details={"dpia_id": dpia_id, "opinion_length": len(opinion)},
        )

        return True

    def complete_dpia(
        self, dpia_id: str, residual_risk: RiskLevel, approval_status: str
    ) -> bool:
        """
        完成DPIA

        Args:
            dpia_id: DPIA ID
            residual_risk: 剩餘風險
            approval_status: 批准狀態

        Returns:
            是否成功
        """
        if dpia_id not in self.dpias:
            return False

        dpia = self.dpias[dpia_id]
        dpia.status = "completed"
        dpia.completion_date = datetime.now()
        dpia.residual_risk = residual_risk
        dpia.approval_status = approval_status

        # 記錄審計日誌
        self.audit_logger.log(
            event_type="compliance",
            action="dpia_completed",
            user_id=dpia.assessed_by,
            resource="dpia",
            details={
                "dpia_id": dpia_id,
                "residual_risk": residual_risk,
                "approval_status": approval_status,
            },
        )

        return True

    def generate_dpia_report(self, dpia_id: str) -> str:
        """
        生成DPIA報告

        Args:
            dpia_id: DPIA ID

        Returns:
            JSON格式的報告
        """
        if dpia_id not in self.dpias:
            return "{}"

        dpia = self.dpias[dpia_id]

        # 計算緩解措施實施率
        total_measures = len(dpia.mitigation_measures)
        implemented_measures = len(
            [m for m in dpia.mitigation_measures if m.status == "implemented"]
        )
        implementation_rate = (
            implemented_measures / total_measures * 100 if total_measures > 0 else 0
        )

        report = {
            "generated_at": datetime.now().isoformat(),
            "dpia": dpia.dict(),
            "summary": {
                "status": dpia.status,
                "risk_level": (
                    dpia.risk_assessment.get("overall_risk")
                    if dpia.risk_assessment
                    else "not_assessed"
                ),
                "residual_risk": dpia.residual_risk,
                "consultation_count": len(dpia.consultation_records),
                "mitigation_measures_count": total_measures,
                "mitigation_implementation_rate": round(implementation_rate, 2),
                "approval_status": dpia.approval_status,
            },
            "recommendations": self._generate_recommendations(dpia),
        }

        return json.dumps(report, indent=2, default=str)

    def _generate_recommendations(self, dpia: DPIA) -> List[str]:
        """生成建議"""
        recommendations = []

        # 檢查風險級別
        if dpia.risk_assessment and dpia.risk_assessment.get("overall_risk") in [
            "high",
            "very_high",
        ]:
            recommendations.append("建議實施額外的技術和組織措施來降低風險")

        # 檢查諮詢記錄
        if len(dpia.consultation_records) < 2:
            recommendations.append("建議增加與利益相關者的諮詢")

        # 檢查緩解措施
        if dpia.mitigation_measures:
            incomplete = [
                m for m in dpia.mitigation_measures if m.status != "implemented"
            ]
            if incomplete:
                recommendations.append(f"完成 {len(incomplete)} 個未實施的緩解措施")

        return recommendations

    def list_dpias(self, status: str = None) -> List[Dict[str, Any]]:
        """
        列出DPIA

        Args:
            status: 狀態過濾

        Returns:
            DPIA列表
        """
        dpia_list = [dpia.dict() for dpia in self.dpias.values()]

        if status:
            dpia_list = [d for d in dpia_list if d["status"] == status]

        return dpia_list
