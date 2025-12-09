"""
事件響應管理器
實現事件檢測、分類、遏制和恢復流程
"""

import json
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, Field

from ..audit.audit_logger import AuditLogger


class IncidentSeverity(str, Enum):
    """事件嚴重性"""

    CRITICAL = "critical"  # 影響核心業務
    HIGH = "high"  # 重大影響
    MEDIUM = "medium"  # 中等影響
    LOW = "low"  # 輕微影響
    INFO = "info"  # 信息性


class IncidentStatus(str, Enum):
    """事件狀態"""

    NEW = "new"
    INVESTIGATING = "investigating"
    CONTAINED = "contained"
    ERADICATING = "eradicating"
    RECOVERING = "recovering"
    RESOLVED = "resolved"
    CLOSED = "closed"


class IncidentType(str, Enum):
    """事件類型"""

    DATA_BREACH = "data_breach"
    MALWARE = "malware"
    PHISHING = "phishing"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    DENIAL_OF_SERVICE = "denial_of_service"
    DATA_LOSS = "data_loss"
    SYSTEM_COMPROMISE = "system_compromise"
    PRIVACY_VIOLATION = "privacy_violation"
    FRAUD = "fraud"
    OTHER = "other"


class Incident(BaseModel):
    """安全事件"""

    incident_id: str
    title: str
    description: str
    incident_type: IncidentType
    severity: IncidentSeverity
    status: IncidentStatus
    discovered_at: datetime = Field(default_factory=datetime.now)
    reported_by: str
    assigned_to: Optional[str] = None
    affected_systems: List[str] = Field(default_factory=list)
    affected_data: Optional[List[str]] = None
    affected_individuals: Optional[int] = None
    indicators: List[str] = Field(default_factory=list)
    timeline: List[Dict[str, Any]] = Field(default_factory=list)
    actions_taken: List[str] = Field(default_factory=list)
    containment_actions: List[str] = Field(default_factory=list)
    eradication_actions: List[str] = Field(default_factory=list)
    recovery_actions: List[str] = Field(default_factory=list)
    lessons_learned: Optional[str] = None
    cost_estimate: Optional[float] = None


class IncidentResponseTeam(BaseModel):
    """事件響應團隊"""

    role: str
    name: str
    email: str
    phone: str
    backup: str


class IncidentManager:
    """事件響應管理器"""

    def __init__(self, audit_logger: AuditLogger = None):
        """
        初始化事件管理器

        Args:
            audit_logger: 審計日誌記錄器
        """
        self.audit_logger = audit_logger or AuditLogger()
        self.incidents: Dict[str, Incident] = {}
        self.response_team: List[IncidentResponseTeam] = [
            IncidentResponseTeam(
                role="Incident Commander",
                name="John Doe",
                email="incident.commander@company.com",
                phone="+852 - XXXX - XXXX",
                backup="backup.ic@company.com",
            ),
            IncidentResponseTeam(
                role="Security Analyst",
                name="Jane Smith",
                email="security.analyst@company.com",
                phone="+852 - XXXX - XXXX",
                backup="security.backup@company.com",
            ),
            IncidentResponseTeam(
                role="Data Protection Officer",
                name="Alice Wong",
                email="dpo@company.com",
                phone="+852 - XXXX - XXXX",
                backup="dpo.backup@company.com",
            ),
        ]

    def report_incident(
        self,
        title: str,
        description: str,
        incident_type: IncidentType,
        severity: IncidentSeverity,
        reported_by: str,
        affected_systems: List[str] = None,
        affected_data: List[str] = None,
        affected_individuals: int = None,
        indicators: List[str] = None,
    ) -> str:
        """
        報告安全事件

        Args:
            title: 事件標題
            description: 事件描述
            incident_type: 事件類型
            severity: 嚴重性
            reported_by: 報告人
            affected_systems: 受影響系統
            affected_data: 受影響數據
            affected_individuals: 受影響人數
            indicators: 指標

        Returns:
            事件ID
        """
        incident_id = str(uuid.uuid4())

        incident = Incident(
            incident_id=incident_id,
            title=title,
            description=description,
            incident_type=incident_type,
            severity=severity,
            status=IncidentStatus.NEW,
            reported_by=reported_by,
            affected_systems=affected_systems or [],
            affected_data=affected_data,
            affected_individuals=affected_individuals,
            indicators=indicators or [],
        )

        self.incidents[incident_id] = incident

        # 添加初始時間線
        self._add_timeline_entry(
            incident_id, "event_reported", f"事件由 {reported_by} 報告", reported_by
        )

        # 記錄審計日誌
        self.audit_logger.log(
            event_type="security",
            action="incident_reported",
            user_id=reported_by,
            resource="incident_response",
            status=(
                "critical"
                if severity in [IncidentSeverity.CRITICAL, IncidentSeverity.HIGH]
                else "warning"
            ),
            details={
                "incident_id": incident_id,
                "title": title,
                "incident_type": incident_type,
                "severity": severity,
                "affected_systems": len(affected_systems) if affected_systems else 0,
                "affected_individuals": affected_individuals,
            },
            risk_score=90 if severity == IncidentSeverity.CRITICAL else 70,
        )

        # 自動分配和通知
        self._auto_assign_incident(incident_id)

        return incident_id

    def _add_timeline_entry(
        self,
        incident_id: str,
        action: str,
        description: str,
        actor: str,
        details: Dict[str, Any] = None,
    ):
        """添加時間線條目"""
        if incident_id not in self.incidents:
            return

        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "description": description,
            "actor": actor,
        }

        if details:
            entry["details"] = details

        self.incidents[incident_id].timeline.append(entry)

    def _auto_assign_incident(self, incident_id: str):
        """自動分配事件"""
        incident = self.incidents[incident_id]

        # 根據嚴重性自動分配
        if incident.severity == IncidentSeverity.CRITICAL:
            assignee = self.response_team[0]  # Incident Commander
        elif incident.incident_type in [
            IncidentType.DATA_BREACH,
            IncidentType.PRIVACY_VIOLATION,
        ]:
            assignee = self.response_team[2]  # DPO
        else:
            assignee = self.response_team[1]  # Security Analyst

        incident.assigned_to = assignee.name

        self._add_timeline_entry(
            incident_id, "incident_assigned", f"事件分配給 {assignee.name}", "system"
        )

    def update_incident_status(
        self,
        incident_id: str,
        status: IncidentStatus,
        actor: str,
        actions: List[str] = None,
    ) -> bool:
        """
        更新事件狀態

        Args:
            incident_id: 事件ID
            status: 新狀態
            actor: 操作人
            actions: 採取的行動

        Returns:
            是否成功
        """
        if incident_id not in self.incidents:
            return False

        incident = self.incidents[incident_id]
        old_status = incident.status
        incident.status = status

        # 根據狀態添加行動
        if actions:
            if status == IncidentStatus.CONTAINED:
                incident.containment_actions.extend(actions)
            elif status == IncidentStatus.ERADICATING:
                incident.eradication_actions.extend(actions)
            elif status == IncidentStatus.RECOVERING:
                incident.recovery_actions.extend(actions)

        # 記錄時間線
        self._add_timeline_entry(
            incident_id,
            "status_update",
            f"狀態從 {old_status} 更新為 {status}",
            actor,
            {"actions": actions},
        )

        # 記錄審計日誌
        self.audit_logger.log(
            event_type="security",
            action="incident_status_updated",
            user_id=actor,
            resource="incident_response",
            details={
                "incident_id": incident_id,
                "old_status": old_status,
                "new_status": status,
                "actions_count": len(actions) if actions else 0,
            },
        )

        return True

    def add_timeline_entry(
        self,
        incident_id: str,
        action: str,
        description: str,
        actor: str,
        details: Dict[str, Any] = None,
    ) -> bool:
        """
        添加時間線條目

        Args:
            incident_id: 事件ID
            action: 行動
            description: 描述
            actor: 操作人
            details: 詳細信息

        Returns:
            是否成功
        """
        if incident_id not in self.incidents:
            return False

        self._add_timeline_entry(incident_id, action, description, actor, details)

        # 記錄審計日誌
        self.audit_logger.log(
            event_type="security",
            action="incident_timeline_added",
            user_id=actor,
            resource="incident_response",
            details={"incident_id": incident_id, "action": action},
        )

        return True

    def check_notification_requirements(self, incident_id: str) -> Dict[str, Any]:
        """
        檢查通知要求

        Args:
            incident_id: 事件ID

        Returns:
            通知要求報告
        """
        if incident_id not in self.incidents:
            return {}

        incident = self.incidents[incident_id]
        requirements = {
            "gdpr_breach_notification": False,
            "pdpa_notification": False,
            "hkma_notification": False,
            "supervisory_authority": False,
            "data_subjects": False,
            "deadline_72h": None,
            "deadline_30d": None,
        }

        # GDPR要求：72小時內通知監管機構
        if incident.incident_type == IncidentType.DATA_BREACH:
            requirements["gdpr_breach_notification"] = True
            requirements["deadline_72h"] = (
                incident.discovered_at + timedelta(hours=72)
            ).isoformat()

            # 如果影響個人權利，需要通知數據主體
            if incident.affected_individuals and incident.affected_individuals > 0:
                requirements["data_subjects"] = True
                requirements["deadline_30d"] = (
                    incident.discovered_at + timedelta(days=30)
                ).isoformat()

        # PDPA要求
        if incident.incident_type == IncidentType.PRIVACY_VIOLATION:
            requirements["pdpa_notification"] = True

        # HKMA要求
        if incident.severity in [IncidentSeverity.CRITICAL, IncidentSeverity.HIGH]:
            requirements["hkma_notification"] = True

        return requirements

    def generate_incident_report(self, incident_id: str) -> str:
        """
        生成事件報告

        Args:
            incident_id: 事件ID

        Returns:
            JSON格式的事件報告
        """
        if incident_id not in self.incidents:
            return "{}"

        incident = self.incidents[incident_id]
        notification_requirements = self.check_notification_requirements(incident_id)

        report = {
            "generated_at": datetime.now().isoformat(),
            "incident": incident.dict(),
            "notification_requirements": notification_requirements,
            "response_team": [member.dict() for member in self.response_team],
            "summary": {
                "total_duration": str(datetime.now() - incident.discovered_at),
                "actions_taken": len(incident.actions_taken),
                "containment_actions": len(incident.containment_actions),
                "eradication_actions": len(incident.eradication_actions),
                "recovery_actions": len(incident.recovery_actions),
            },
        }

        return json.dumps(report, indent=2, default=str)

    def simulate_incident(self) -> str:
        """
        模擬事件演練

        Returns:
            模擬事件ID
        """
        incident_id = self.report_incident(
            title="模擬數據洩露事件",
            description="模擬攻擊者未經授權訪問客戶交易數據",
            incident_type=IncidentType.DATA_BREACH,
            severity=IncidentSeverity.CRITICAL,
            reported_by="system",
            affected_systems=["trading_db", "user_data"],
            affected_data=["trading_records", "user_profiles"],
            affected_individuals=1000,
            indicators=["unusual_db_access", "large_data_export"],
        )

        # 添加模擬時間線
        self._add_timeline_entry(
            incident_id, "threat_detected", "安全監控系統檢測到異常活動", "SIEM"
        )

        self._add_timeline_entry(
            incident_id,
            "initial_assessment",
            "初步評估確認為高危事件",
            "Security Analyst",
        )

        self.update_incident_status(
            incident_id, IncidentStatus.INVESTIGATING, "Incident Commander"
        )

        return incident_id
