"""
合規監控器
持續監控合規狀態並提供實時報告
"""

import json
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from pydantic import BaseModel, Field

from ..audit.audit_logger import AuditLogger


class ComplianceStatus(str, Enum):
    """合規狀態"""

    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    UNDER_REVIEW = "under_review"
    EXPIRED = "expired"


class ViolationType(str, Enum):
    """違規類型"""

    POLICY_VIOLATION = "policy_violation"
    ACCESS_VIOLATION = "access_violation"
    DATA_VIOLATION = "data_violation"
    RETENTION_VIOLATION = "retention_violation"
    CONSENT_VIOLATION = "consent_violation"
    SECURITY_VIOLATION = "security_violation"


class ComplianceCheck(BaseModel):
    """合規檢查"""

    check_id: str
    name: str
    description: str
    framework: str  # GDPR, PDPA, ISO 27001, etc.
    status: ComplianceStatus
    last_checked: datetime = Field(default_factory=datetime.now)
    next_check: Optional[datetime] = None
    failure_count: int = 0
    last_failure: Optional[datetime] = None
    severity: str = "medium"  # low, medium, high, critical
    remediation_actions: List[str] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)


class ComplianceViolation(BaseModel):
    """合規違規"""

    violation_id: str
    violation_type: ViolationType
    framework: str
    check_id: str
    description: str
    detected_at: datetime = Field(default_factory=datetime.now)
    severity: str
    status: str = "open"  # open, investigating, resolved, closed
    affected_resources: List[str] = Field(default_factory=list)
    detected_by: str
    remediation: Optional[str] = None
    resolved_at: Optional[datetime] = None


class ComplianceMonitor:
    """合規監控器"""

    def __init__(self, audit_logger: AuditLogger = None):
        """
        初始化合規監控器

        Args:
            audit_logger: 審計日誌記錄器
        """
        self.audit_logger = audit_logger or AuditLogger()
        self.checks: Dict[str, ComplianceCheck] = {}
        self.violations: Dict[str, ComplianceViolation] = {}
        self._setup_default_checks()
        self._check_callbacks: List[Callable] = []

    def _setup_default_checks(self):
        """設置默認合規檢查"""
        # GDPR合規檢查
        self.register_check(
            name="GDPR Data Processing Records",
            description="檢查所有數據處理活動是否已記錄",
            framework="GDPR",
            severity="high",
        )

        self.register_check(
            name="GDPR Consent Records",
            description="檢查是否存在有效的同意記錄",
            framework="GDPR",
            severity="high",
        )

        self.register_check(
            name="GDPR Data Subject Rights",
            description="檢查數據主體權利請求的響應時間",
            framework="GDPR",
            severity="medium",
        )

        self.register_check(
            name="GDPR Breach Notification",
            description="檢查是否在72小時內報告數據洩露",
            framework="GDPR",
            severity="critical",
        )

        # PDPA合規檢查
        self.register_check(
            name="PDPA Data Minimization",
            description="檢查數據收集是否遵守最小化原則",
            framework="PDPA",
            severity="high",
        )

        self.register_check(
            name="PDPA Data Accuracy",
            description="檢查個人數據的準確性",
            framework="PDPA",
            severity="medium",
        )

        # ISO 27001合規檢查
        self.register_check(
            name="ISO 27001 Access Control",
            description="檢查訪問控制措施",
            framework="ISO 27001",
            severity="high",
        )

        self.register_check(
            name="ISO 27001 Incident Response",
            description="檢查事件響應程序",
            framework="ISO 27001",
            severity="high",
        )

    def register_check(
        self, name: str, description: str, framework: str, severity: str = "medium"
    ) -> str:
        """
        註冊合規檢查

        Args:
            name: 檢查名稱
            description: 描述
            framework: 合規框架
            severity: 嚴重性

        Returns:
            檢查ID
        """
        check_id = f"{framework}_{name}".replace(" ", "_").lower()

        check = ComplianceCheck(
            check_id=check_id,
            name=name,
            description=description,
            framework=framework,
            status=ComplianceStatus.UNDER_REVIEW,
            severity=severity,
        )

        self.checks[check_id] = check

        # 記錄審計日誌
        self.audit_logger.log(
            event_type="compliance",
            action="compliance_check_registered",
            user_id="system",
            resource="compliance_monitor",
            details={
                "check_id": check_id,
                "framework": framework,
                "severity": severity,
            },
        )

        return check_id

    def run_compliance_check(self, check_id: str, result: Dict[str, Any]) -> bool:
        """
        運行合規檢查

        Args:
            check_id: 檢查ID
            result: 檢查結果

        Returns:
            是否通過
        """
        if check_id not in self.checks:
            return False

        check = self.checks[check_id]
        check.last_checked = datetime.now()
        check.metrics.update(result)

        # 判斷是否通過
        is_compliant = result.get("compliant", False)
        check.status = (
            ComplianceStatus.COMPLIANT
            if is_compliant
            else ComplianceStatus.NON_COMPLIANT
        )

        if not is_compliant:
            check.failure_count += 1
            check.last_failure = datetime.now()

            # 記錄違規
            self._create_violation(check, result.get("message", "合規檢查失敗"))

            # 記錄審計日誌
            self.audit_logger.log(
                event_type="compliance",
                action="compliance_check_failed",
                user_id="system",
                resource="compliance_monitor",
                status="warning" if check.severity in ["low", "medium"] else "error",
                details={
                    "check_id": check_id,
                    "failure_count": check.failure_count,
                    "message": result.get("message"),
                },
                risk_score=50 if check.severity == "medium" else 70,
            )
        else:
            # 記錄審計日誌
            self.audit_logger.log(
                event_type="compliance",
                action="compliance_check_passed",
                user_id="system",
                resource="compliance_monitor",
                details={"check_id": check_id},
            )

        return is_compliant

    def _create_violation(self, check: ComplianceCheck, message: str):
        """創建違規記錄"""
        violation_id = f"V_{datetime.now().strftime('%Y % m % d')}_{len(self.violations)}"

        violation = ComplianceViolation(
            violation_id=violation_id,
            violation_type=ViolationType.POLICY_VIOLATION,
            framework=check.framework,
            check_id=check.check_id,
            description=message,
            severity=check.severity,
            detected_by="compliance_monitor",
        )

        self.violations[violation_id] = violation

    def run_all_checks(self) -> Dict[str, bool]:
        """
        運行所有合規檢查

        Returns:
            檢查結果
        """
        results = {}

        for check_id in self.checks.keys():
            # 這裡可以實現實際的檢查邏輯
            # 簡化示例：隨機決定是否通過
            import random

            is_compliant = random.random() > 0.2  # 80 % 通過率

            results[check_id] = self.run_compliance_check(
                check_id,
                {
                    "compliant": is_compliant,
                    "message": "檢查完成" if is_compliant else "發現合規問題",
                },
            )

        return results

    def get_compliance_score(self, framework: str = None) -> Dict[str, Any]:
        """
        獲取合規評分

        Args:
            framework: 合規框架過濾

        Returns:
            合規評分報告
        """
        # 過濾檢查
        filtered_checks = self.checks.values()
        if framework:
            filtered_checks = [
                c for c in self.checks.values() if c.framework == framework
            ]

        total_checks = len(filtered_checks)
        compliant_checks = len(
            [c for c in filtered_checks if c.status == ComplianceStatus.COMPLIANT]
        )
        non_compliant_checks = len(
            [c for c in filtered_checks if c.status == ComplianceStatus.NON_COMPLIANT]
        )

        compliance_score = (
            (compliant_checks / total_checks * 100) if total_checks > 0 else 0
        )

        # 統計違規
        filtered_violations = self.violations.values()
        if framework:
            filtered_violations = [
                v for v in self.violations.values() if v.framework == framework
            ]

        open_violations = len([v for v in filtered_violations if v.status == "open"])
        high_severity_violations = len(
            [v for v in filtered_violations if v.severity in ["high", "critical"]]
        )

        report = {
            "generated_at": datetime.now().isoformat(),
            "framework": framework or "ALL",
            "compliance_score": round(compliance_score, 2),
            "total_checks": total_checks,
            "compliant_checks": compliant_checks,
            "non_compliant_checks": non_compliant_checks,
            "open_violations": open_violations,
            "high_severity_violations": high_severity_violations,
            "checks": [
                {
                    "check_id": c.check_id,
                    "name": c.name,
                    "status": c.status,
                    "severity": c.severity,
                    "last_checked": c.last_checked.isoformat(),
                }
                for c in filtered_checks
            ],
        }

        return report

    def detect_anomalies(self) -> List[Dict[str, Any]]:
        """
        檢測異常模式

        Returns:
            異常列表
        """
        anomalies = []

        # 檢查失敗率過高的檢查
        for check in self.checks.values():
            if check.failure_count > 5:
                anomalies.append(
                    {
                        "type": "high_failure_rate",
                        "check_id": check.check_id,
                        "description": f"檢查 {check.name} 失敗率過高",
                        "failure_count": check.failure_count,
                        "severity": "high",
                    }
                )

        # 檢查過期的檢查
        for check in self.checks.values():
            if check.next_check and check.next_check < datetime.now():
                anomalies.append(
                    {
                        "type": "overdue_check",
                        "check_id": check.check_id,
                        "description": f"檢查 {check.name} 已過期",
                        "overdue_days": (datetime.now() - check.next_check).days,
                        "severity": "medium",
                    }
                )

        # 記錄審計日誌
        if anomalies:
            self.audit_logger.log(
                event_type="compliance",
                action="anomalies_detected",
                user_id="system",
                resource="compliance_monitor",
                status="warning",
                details={"anomaly_count": len(anomalies)},
            )

        return anomalies

    def generate_compliance_report(self, framework: str = None) -> str:
        """
        生成合規報告

        Args:
            framework: 合規框架

        Returns:
            JSON格式的報告
        """
        compliance_score = self.get_compliance_score(framework)
        anomalies = self.detect_anomalies()

        # 過濾違規
        violations = list(self.violations.values())
        if framework:
            violations = [v for v in violations if v.framework == framework]

        report = {
            "generated_at": datetime.now().isoformat(),
            "framework": framework or "ALL",
            "compliance_score": compliance_score,
            "anomalies": anomalies,
            "violations": [v.dict() for v in violations],
            "recommendations": self._generate_recommendations(
                compliance_score, anomalies
            ),
        }

        return json.dumps(report, indent=2, default=str)

    def _generate_recommendations(
        self, compliance_score: Dict[str, Any], anomalies: List[Dict[str, Any]]
    ) -> List[str]:
        """生成建議"""
        recommendations = []

        # 根據合規評分給出建議
        score = compliance_score.get("compliance_score", 0)

        if score < 50:
            recommendations.append("合規評分過低，建議立即採取補救措施")
        elif score < 80:
            recommendations.append("合規評分有待提高，建議加強合規管理")

        # 根據違規給出建議
        open_violations = compliance_score.get("open_violations", 0)
        if open_violations > 0:
            recommendations.append(
                f"存在 {open_violations} 個未解決的違規，需要立即處理"
            )

        high_severity = compliance_score.get("high_severity_violations", 0)
        if high_severity > 0:
            recommendations.append(f"存在 {high_severity} 個高危違規，建議優先處理")

        # 根據異常給出建議
        high_failure_anomalies = [
            a for a in anomalies if a["type"] == "high_failure_rate"
        ]
        if high_failure_anomalies:
            recommendations.append("檢查失敗率過高，建議審查檢查邏輯和系統配置")

        return recommendations

    def add_check_callback(self, callback: Callable):
        """
        添加檢查回調函數

        Args:
            callback: 回調函數
        """
        self._check_callbacks.append(callback)
