"""
T107: 隐私合规报告系统

实现隐私合规报告功能，包括：
- 自动化隐私合规报告
- GDPR / CCPA合规检查
- 数据保留策略验证
- 第三方数据传输审计
- 报告导出(PDF / HTML)
"""

import base64
import csv
import hashlib
import json
import logging
import sqlite3
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from jinja2 import Template


class ComplianceStandard(Enum):
    """合规标准"""

    GDPR = "gdpr"
    CCPA = "ccpa"
    PIPEDA = "pipeda"
    LGPD = "lgpd"


class DataCategory(Enum):
    """数据类型"""

    PERSONAL = "personal"
    SENSITIVE = "sensitive"
    FINANCIAL = "financial"
    HEALTH = "health"
    BEHAVIORAL = "behavioral"
    TECHNICAL = "technical"


class DataSubjectRights(Enum):
    """数据主体权利"""

    ACCESS = "access"
    RECTIFICATION = "rectification"
    ERASURE = "erasure"
    PORTABILITY = "portability"
    RESTRICTION = "restriction"
    OBJECTION = "objection"
    AUTOMATED_DECISION = "automated_decision"


class ComplianceFinding:
    """合规发现"""

    def __init__(
        self,
        standard: ComplianceStandard,
        requirement: str,
        status: str,  # compliant, non_compliant, partial, not_applicable
        description: str,
        evidence: Optional[List[str]] = None,
        risk_level: str = "low",  # low, medium, high, critical
        recommendation: Optional[str] = None,
    ):
        self.timestamp = datetime.utcnow()
        self.standard = standard
        self.requirement = requirement
        self.status = status
        self.description = description
        self.evidence = evidence or []
        self.risk_level = risk_level
        self.recommendation = recommendation

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "standard": self.standard.value,
            "requirement": self.requirement,
            "status": self.status,
            "description": self.description,
            "evidence": self.evidence,
            "risk_level": self.risk_level,
            "recommendation": self.recommendation,
        }


class ComplianceReport:
    """合规报告"""

    def __init__(
        self, standard: ComplianceStandard, start_date: datetime, end_date: datetime
    ):
        self.report_id = self._generate_report_id()
        self.timestamp = datetime.utcnow()
        self.standard = standard
        self.start_date = start_date
        self.end_date = end_date
        self.findings: List[ComplianceFinding] = []
        self.metadata: Dict[str, Any] = {}

    def add_finding(self, finding: ComplianceFinding):
        """添加合规发现"""
        self.findings.append(finding)

    def add_metadata(self, key: str, value: Any):
        """添加元数据"""
        self.metadata[key] = value

    def get_summary(self) -> Dict[str, Any]:
        """获取报告摘要"""
        if not self.findings:
            return {}

        status_counts = defaultdict(int)
        risk_counts = defaultdict(int)

        for finding in self.findings:
            status_counts[finding.status] += 1
            risk_counts[finding.risk_level] += 1

        return {
            "total_findings": len(self.findings),
            "by_status": dict(status_counts),
            "by_risk": dict(risk_counts),
            "compliant": status_counts.get("compliant", 0),
            "non_compliant": status_counts.get("non_compliant", 0),
            "partial": status_counts.get("partial", 0),
            "critical_risks": risk_counts.get("critical", 0),
            "high_risks": risk_counts.get("high", 0),
        }

    def _generate_report_id(self) -> str:
        """生成报告ID"""
        content = f"{datetime.utcnow().isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]


class GDPRComplianceChecker:
    """GDPR合规检查器"""

    def __init__(
        self, audit_logger, access_tracker, db_path: str = "logs / compliance_gdpr.db"
    ):
        self.audit_logger = audit_logger
        self.access_tracker = access_tracker
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        self.logger = logging.getLogger("hk_quant_system.compliance.gdpr")

    def _init_database(self):
        """初始化数据库"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS gdpr_compliance (
                    report_id TEXT,
                    timestamp TEXT,
                    requirement TEXT,
                    status TEXT,
                    description TEXT,
                    evidence TEXT,
                    risk_level TEXT,
                    recommendation TEXT
                )
            """
            )
            conn.commit()

    def check_all_requirements(
        self, start_date: datetime, end_date: datetime
    ) -> ComplianceReport:
        """
        检查所有GDPR要求

        Args:
            start_date: 检查开始日期
            end_date: 检查结束日期

        Returns:
            合规报告
        """
        report = ComplianceReport(ComplianceStandard.GDPR, start_date, end_date)

        # 检查各类合规要求
        report.add_finding(self._check_lawful_basis(start_date, end_date))
        report.add_finding(self._check_data_subject_rights(start_date, end_date))
        report.add_finding(self._check_data_protection_by_design(start_date, end_date))
        report.add_finding(self._check_data_breach_notification(start_date, end_date))
        report.add_finding(self._check_data_retention(start_date, end_date))
        report.add_finding(self._check_dpia(start_date, end_date))
        report.add_finding(self._check_records_of_processing(start_date, end_date))
        report.add_finding(self._check_data_transfer(start_date, end_date))

        return report

    def _check_lawful_basis(
        self, start_date: datetime, end_date: datetime
    ) -> ComplianceFinding:
        """检查合法依据"""
        # 检查是否有合法依据记录
        lawful_basis_events = self.audit_logger.query_logs(
            start_time=start_date,
            end_time=end_date,
            category="lawful_basis",
            limit=1000,
        )

        if len(lawful_basis_events) > 0:
            return ComplianceFinding(
                standard=ComplianceStandard.GDPR,
                requirement="Article 6 - Lawfulness of processing",
                status="compliant",
                description=f"Found {len(lawful_basis_events)} lawful basis records",
                evidence=[e["event_id"] for e in lawful_basis_events],
                risk_level="low",
            )
        else:
            return ComplianceFinding(
                standard=ComplianceStandard.GDPR,
                requirement="Article 6 - Lawfulness of processing",
                status="non_compliant",
                description="No lawful basis records found",
                risk_level="high",
                recommendation="Record the lawful basis for each data processing activity",
            )

    def _check_data_subject_rights(
        self, start_date: datetime, end_date: datetime
    ) -> ComplianceFinding:
        """检查数据主体权利"""
        # 检查数据主体权利请求
        rights_events = self.audit_logger.query_logs(
            start_time=start_date,
            end_time=end_date,
            category="data_subject_rights",
            limit=1000,
        )

        # 检查响应时效
        avg_response_time = 0
        if rights_events:
            response_times = []
            for event in rights_events:
                try:
                    details = json.loads(event.get("details", "{}"))
                    if "response_time" in details:
                        response_times.append(details["response_time"])
                except (json.JSONDecodeError, TypeError):
                    pass
            if response_times:
                avg_response_time = sum(response_times) / len(response_times)

        if len(rights_events) > 0 and avg_response_time <= 30:  # 30天
            return ComplianceFinding(
                standard=ComplianceStandard.GDPR,
                requirement="Article 12 - 22 - Data subject rights",
                status="compliant",
                description=f"Processed {len(rights_events)} rights requests with avg response time of {avg_response_time} days",
                evidence=[e["event_id"] for e in rights_events],
                risk_level="low",
            )
        else:
            return ComplianceFinding(
                standard=ComplianceStandard.GDPR,
                requirement="Article 12 - 22 - Data subject rights",
                status="partial",
                description="Data subject rights process needs improvement",
                risk_level="medium",
                recommendation="Implement automated process for data subject rights requests",
            )

    def _check_data_protection_by_design(
        self, start_date: datetime, end_date: datetime
    ) -> ComplianceFinding:
        """检查数据保护设计"""
        # 检查隐私设计实施
        design_events = self.audit_logger.query_logs(
            start_time=start_date,
            end_time=end_date,
            category="privacy_by_design",
            limit=1000,
        )

        if len(design_events) >= 5:  # 至少5个隐私设计实施
            return ComplianceFinding(
                standard=ComplianceStandard.GDPR,
                requirement="Article 25 - Data protection by design",
                status="compliant",
                description=f"Found {len(design_events)} privacy by design implementations",
                evidence=[e["event_id"] for e in design_events],
                risk_level="low",
            )
        else:
            return ComplianceFinding(
                standard=ComplianceStandard.GDPR,
                requirement="Article 25 - Data protection by design",
                status="partial",
                description="Insufficient privacy by design implementations",
                risk_level="medium",
                recommendation="Implement more privacy by design measures",
            )

    def _check_data_breach_notification(
        self, start_date: datetime, end_date: datetime
    ) -> ComplianceFinding:
        """检查数据泄露通知"""
        # 检查数据泄露记录
        breach_events = self.audit_logger.query_logs(
            start_time=start_date, end_time=end_date, category="data_breach", limit=1000
        )

        # 检查通知时效
        notification_compliant = True
        for event in breach_events:
            if "notification_time" in event.get("details", {}):
                if event["details"]["notification_time"] > 72:  # 72小时
                    notification_compliant = False
                    break

        if len(breach_events) == 0:
            return ComplianceFinding(
                standard=ComplianceStandard.GDPR,
                requirement="Article 33 - 34 - Data breach notification",
                status="compliant",
                description="No data breaches detected",
                risk_level="low",
            )
        elif notification_compliant:
            return ComplianceFinding(
                standard=ComplianceStandard.GDPR,
                requirement="Article 33 - 34 - Data breach notification",
                status="compliant",
                description=f"Detected {len(breach_events)} breaches, all notified within 72 hours",
                evidence=[e["event_id"] for e in breach_events],
                risk_level="medium",
            )
        else:
            return ComplianceFinding(
                standard=ComplianceStandard.GDPR,
                requirement="Article 33 - 34 - Data breach notification",
                status="non_compliant",
                description="Data breach notifications not within required timeframe",
                evidence=[e["event_id"] for e in breach_events],
                risk_level="critical",
                recommendation="Implement automated breach detection and notification system",
            )

    def _check_data_retention(
        self, start_date: datetime, end_date: datetime
    ) -> ComplianceFinding:
        """检查数据保留"""
        # 检查数据保留策略
        retention_events = self.audit_logger.query_logs(
            start_time=start_date,
            end_time=end_date,
            category="data_retention",
            limit=1000,
        )

        # 检查是否有数据超过保留期
        violations = 0
        for event in retention_events:
            if event.get("details", {}).get("exceeded_retention_period"):
                violations += 1

        if violations == 0 and len(retention_events) > 0:
            return ComplianceFinding(
                standard=ComplianceStandard.GDPR,
                requirement="Article 5(1)(e) - Data retention",
                status="compliant",
                description="Data retention policy implemented, no violations found",
                evidence=[e["event_id"] for e in retention_events],
                risk_level="low",
            )
        elif violations > 0:
            return ComplianceFinding(
                standard=ComplianceStandard.GDPR,
                requirement="Article 5(1)(e) - Data retention",
                status="non_compliant",
                description=f"Found {violations} data retention violations",
                risk_level="high",
                recommendation="Implement automated data deletion based on retention policy",
            )
        else:
            return ComplianceFinding(
                standard=ComplianceStandard.GDPR,
                requirement="Article 5(1)(e) - Data retention",
                status="partial",
                description="No data retention records found",
                risk_level="medium",
                recommendation="Document and implement data retention policy",
            )

    def _check_dpia(
        self, start_date: datetime, end_date: datetime
    ) -> ComplianceFinding:
        """检查DPIA (Data Protection Impact Assessment)"""
        # 检查DPIA记录
        dpia_events = self.audit_logger.query_logs(
            start_time=start_date, end_time=end_date, category="dpia", limit=1000
        )

        if len(dpia_events) > 0:
            return ComplianceFinding(
                standard=ComplianceStandard.GDPR,
                requirement="Article 35 - Data protection impact assessment",
                status="compliant",
                description=f"Found {len(dpia_events)} DPIA records",
                evidence=[e["event_id"] for e in dpia_events],
                risk_level="low",
            )
        else:
            return ComplianceFinding(
                standard=ComplianceStandard.GDPR,
                requirement="Article 35 - Data protection impact assessment",
                status="partial",
                description="No DPIA records found",
                risk_level="medium",
                recommendation="Conduct DPIA for high - risk processing activities",
            )

    def _check_records_of_processing(
        self, start_date: datetime, end_date: datetime
    ) -> ComplianceFinding:
        """检查处理记录"""
        # 检查RoPA记录
        ropa_events = self.audit_logger.query_logs(
            start_time=start_date,
            end_time=end_date,
            category="records_of_processing",
            limit=1000,
        )

        if len(ropa_events) >= 10:  # 至少10个处理记录
            return ComplianceFinding(
                standard=ComplianceStandard.GDPR,
                requirement="Article 30 - Records of processing activities",
                status="compliant",
                description=f"Found {len(ropa_events)} processing records",
                evidence=[e["event_id"] for e in ropa_events],
                risk_level="low",
            )
        else:
            return ComplianceFinding(
                standard=ComplianceStandard.GDPR,
                requirement="Article 30 - Records of processing activities",
                status="partial",
                description="Insufficient processing records",
                risk_level="medium",
                recommendation="Maintain comprehensive records of all processing activities",
            )

    def _check_data_transfer(
        self, start_date: datetime, end_date: datetime
    ) -> ComplianceFinding:
        """检查数据传输"""
        # 检查国际数据传输
        transfer_events = self.audit_logger.query_logs(
            start_time=start_date,
            end_time=end_date,
            category="data_transfer",
            limit=1000,
        )

        # 检查是否有适当的保障措施
        compliant_transfers = 0
        for event in transfer_events:
            if event.get("details", {}).get("safeguards"):
                compliant_transfers += 1

        if len(transfer_events) == 0:
            return ComplianceFinding(
                standard=ComplianceStandard.GDPR,
                requirement="Chapter V - International transfers",
                status="compliant",
                description="No international data transfers detected",
                risk_level="low",
            )
        elif compliant_transfers == len(transfer_events):
            return ComplianceFinding(
                standard=ComplianceStandard.GDPR,
                requirement="Chapter V - International transfers",
                status="compliant",
                description=f"All {len(transfer_events)} international transfers have appropriate safeguards",
                evidence=[e["event_id"] for e in transfer_events],
                risk_level="low",
            )
        else:
            return ComplianceFinding(
                standard=ComplianceStandard.GDPR,
                requirement="Chapter V - International transfers",
                status="non_compliant",
                description=f"Only {compliant_transfers} out of {len(transfer_events)} transfers have safeguards",
                risk_level="high",
                recommendation="Implement appropriate safeguards for all international transfers",
            )


class CCPAComplianceChecker:
    """CCPA合规检查器"""

    def __init__(
        self, audit_logger, access_tracker, db_path: str = "logs / compliance_ccpa.db"
    ):
        self.audit_logger = audit_logger
        self.access_tracker = access_tracker
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        self.logger = logging.getLogger("hk_quant_system.compliance.ccpa")

    def _init_database(self):
        """初始化数据库"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS ccpa_compliance (
                    report_id TEXT,
                    timestamp TEXT,
                    requirement TEXT,
                    status TEXT,
                    description TEXT,
                    evidence TEXT,
                    risk_level TEXT,
                    recommendation TEXT
                )
            """
            )
            conn.commit()

    def check_all_requirements(
        self, start_date: datetime, end_date: datetime
    ) -> ComplianceReport:
        """
        检查所有CCPA要求

        Args:
            start_date: 检查开始日期
            end_date: 检查结束日期

        Returns:
            合规报告
        """
        report = ComplianceReport(ComplianceStandard.CCPA, start_date, end_date)

        # 检查各类合规要求
        report.add_finding(self._check_consumer_rights(start_date, end_date))
        report.add_finding(self._check_privacy_notice(start_date, end_date))
        report.add_finding(self._check_do_not_sell(start_date, end_date))
        report.add_finding(self._check_verification_process(start_date, end_date))
        report.add_finding(self._check_third_party_sharing(start_date, end_date))

        return report

    def _check_consumer_rights(
        self, start_date: datetime, end_date: datetime
    ) -> ComplianceFinding:
        """检查消费者权利"""
        # 检查消费者权利请求
        rights_events = self.audit_logger.query_logs(
            start_time=start_date,
            end_time=end_date,
            category="ccpa_consumer_rights",
            limit=1000,
        )

        if len(rights_events) > 0:
            return ComplianceFinding(
                standard=ComplianceStandard.CCPA,
                requirement="CCPA 1798.100 - 1798.150 - Consumer Rights",
                status="compliant",
                description=f"Processed {len(rights_events)} consumer rights requests",
                evidence=[e["event_id"] for e in rights_events],
                risk_level="low",
            )
        else:
            return ComplianceFinding(
                standard=ComplianceStandard.CCPA,
                requirement="CCPA 1798.100 - 1798.150 - Consumer Rights",
                status="partial",
                description="No consumer rights requests processed",
                risk_level="medium",
                recommendation="Implement consumer rights handling process",
            )

    def _check_privacy_notice(
        self, start_date: datetime, end_date: datetime
    ) -> ComplianceFinding:
        """检查隐私通知"""
        # 检查隐私通知更新
        notice_events = self.audit_logger.query_logs(
            start_time=start_date,
            end_time=end_date,
            category="privacy_notice",
            limit=1000,
        )

        if len(notice_events) > 0:
            return ComplianceFinding(
                standard=ComplianceStandard.CCPA,
                requirement="CCPA 1798.130 - Privacy Notice",
                status="compliant",
                description="Privacy notice is available and up to date",
                evidence=[e["event_id"] for e in notice_events],
                risk_level="low",
            )
        else:
            return ComplianceFinding(
                standard=ComplianceStandard.CCPA,
                requirement="CCPA 1798.130 - Privacy Notice",
                status="non_compliant",
                description="Privacy notice not found",
                risk_level="high",
                recommendation="Publish comprehensive privacy notice",
            )

    def _check_do_not_sell(
        self, start_date: datetime, end_date: datetime
    ) -> ComplianceFinding:
        """检查不要出售选项"""
        # 检查Do Not Sell机制
        dns_events = self.audit_logger.query_logs(
            start_time=start_date, end_time=end_date, category="do_not_sell", limit=1000
        )

        if len(dns_events) > 0:
            return ComplianceFinding(
                standard=ComplianceStandard.CCPA,
                requirement="CCPA 1798.120 - Do Not Sell",
                status="compliant",
                description="Do Not Sell mechanism is implemented",
                evidence=[e["event_id"] for e in dns_events],
                risk_level="low",
            )
        else:
            return ComplianceFinding(
                standard=ComplianceStandard.CCPA,
                requirement="CCPA 1798.120 - Do Not Sell",
                status="non_compliant",
                description="Do Not Sell mechanism not found",
                risk_level="high",
                recommendation="Implement Do Not Sell mechanism",
            )

    def _check_verification_process(
        self, start_date: datetime, end_date: datetime
    ) -> ComplianceFinding:
        """检查验证流程"""
        # 检查身份验证
        verify_events = self.audit_logger.query_logs(
            start_time=start_date,
            end_time=end_date,
            category="identity_verification",
            limit=1000,
        )

        if len(verify_events) > 0:
            return ComplianceFinding(
                standard=ComplianceStandard.CCPA,
                requirement="CCPA 1798.140(t) - Verification",
                status="compliant",
                description="Identity verification process implemented",
                evidence=[e["event_id"] for e in verify_events],
                risk_level="low",
            )
        else:
            return ComplianceFinding(
                standard=ComplianceStandard.CCPA,
                requirement="CCPA 1798.140(t) - Verification",
                status="partial",
                description="No identity verification records found",
                risk_level="medium",
                recommendation="Implement consumer identity verification process",
            )

    def _check_third_party_sharing(
        self, start_date: datetime, end_date: datetime
    ) -> ComplianceFinding:
        """检查第三方共享"""
        # 检查第三方数据共享
        sharing_events = self.audit_logger.query_logs(
            start_time=start_date,
            end_time=end_date,
            category="third_party_sharing",
            limit=1000,
        )

        if len(sharing_events) == 0:
            return ComplianceFinding(
                standard=ComplianceStandard.CCPA,
                requirement="CCPA 1798.115 - Third Party Sharing",
                status="compliant",
                description="No third party data sharing detected",
                risk_level="low",
            )
        else:
            # 检查是否有适当协议
            compliant_sharing = sum(
                1 for e in sharing_events if e.get("details", {}).get("has_agreement")
            )
            if compliant_sharing == len(sharing_events):
                return ComplianceFinding(
                    standard=ComplianceStandard.CCPA,
                    requirement="CCPA 1798.115 - Third Party Sharing",
                    status="compliant",
                    description=f"All {len(sharing_events)} third party sharing have proper agreements",
                    evidence=[e["event_id"] for e in sharing_events],
                    risk_level="low",
                )
            else:
                return ComplianceFinding(
                    standard=ComplianceStandard.CCPA,
                    requirement="CCPA 1798.115 - Third Party Sharing",
                    status="non_compliant",
                    description="Some third party sharing lacks proper agreements",
                    risk_level="high",
                    recommendation="Execute proper agreements with all third parties",
                )


class ComplianceReporter:
    """合规报告生成器"""

    def __init__(
        self, audit_logger, access_tracker, templates_dir: str = "templates / compliance"
    ):
        self.audit_logger = audit_logger
        self.access_tracker = access_tracker
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(parents=True, exist_ok=True)

        # 初始化检查器
        self.gdpr_checker = GDPRComplianceChecker(audit_logger, access_tracker)
        self.ccpa_checker = CCPAComplianceChecker(audit_logger, access_tracker)

        self.logger = logging.getLogger("hk_quant_system.compliance.reporter")

    def generate_compliance_report(
        self,
        standards: List[ComplianceStandard],
        start_date: datetime,
        end_date: datetime,
    ) -> ComplianceReport:
        """
        生成合规报告

        Args:
            standards: 合规标准列表
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            合规报告
        """
        all_findings = []

        for standard in standards:
            if standard == ComplianceStandard.GDPR:
                report = self.gdpr_checker.check_all_requirements(start_date, end_date)
            elif standard == ComplianceStandard.CCPA:
                report = self.ccpa_checker.check_all_requirements(start_date, end_date)
            else:
                continue

            all_findings.extend(report.findings)

        # 合并所有发现
        combined_report = ComplianceReport(
            standard=ComplianceStandard.GDPR,  # 使用任意标准
            start_date=start_date,
            end_date=end_date,
        )
        combined_report.findings = all_findings

        return combined_report

    def export_report_json(self, report: ComplianceReport, output_path: str) -> str:
        """
        导出JSON格式报告

        Args:
            report: 合规报告
            output_path: 输出路径

        Returns:
            输出文件路径
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        report_data = {
            "report_id": report.report_id,
            "timestamp": report.timestamp.isoformat(),
            "standard": report.standard.value,
            "start_date": report.start_date.isoformat(),
            "end_date": report.end_date.isoformat(),
            "summary": report.get_summary(),
            "findings": [finding.to_dict() for finding in report.findings],
            "metadata": report.metadata,
        }

        with open(output_path, "w", encoding="utf - 8") as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)

        return str(output_path)

    def export_report_csv(self, report: ComplianceReport, output_path: str) -> str:
        """
        导出CSV格式报告

        Args:
            report: 合规报告
            output_path: 输出路径

        Returns:
            输出文件路径
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", newline="", encoding="utf - 8") as f:
            writer = csv.writer(f)

            # 写入标题
            writer.writerow(
                [
                    "Timestamp",
                    "Standard",
                    "Requirement",
                    "Status",
                    "Risk Level",
                    "Description",
                    "Recommendation",
                ]
            )

            # 写入数据
            for finding in report.findings:
                writer.writerow(
                    [
                        finding.timestamp.isoformat(),
                        finding.standard.value,
                        finding.requirement,
                        finding.status,
                        finding.risk_level,
                        finding.description,
                        finding.recommendation or "",
                    ]
                )

        return str(output_path)

    def generate_html_report(self, report: ComplianceReport, output_path: str) -> str:
        """
        生成HTML格式报告

        Args:
            report: 合规报告
            output_path: 输出路径

        Returns:
            输出文件路径
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # HTML模板
        html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>{{ report.standard.value.upper() }} Compliance Report</title>
    <style>
        body { font - family: Arial, sans - serif; margin: 20px; }
        h1 { color: #333; }
        h2 { color: #666; }
        .summary { background: #f0f0f0; padding: 15px; border - radius: 5px; }
        .finding { margin: 10px 0; padding: 10px; border - left: 4px solid #ccc; }
        .finding.compliant { border - color: #4CAF50; background: #E8F5E9; }
        .finding.non_compliant { border - color: #F44336; background: #FFEBEE; }
        .finding.partial { border - color: #FF9800; background: #FFF3E0; }
        .risk - low { color: #4CAF50; }
        .risk - medium { color: #FF9800; }
        .risk - high { color: #F44336; }
        .risk - critical { color: #B71C1C; }
        table { width: 100%; border - collapse: collapse; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text - align: left; }
        th { background - color: #f2f2f2; }
    </style>
</head>
<body>
    <h1>{{ report.standard.value.upper() }} Compliance Report</h1>

    <div class="summary">
        <h2>Report Summary</h2>
        <p><strong>Report ID:</strong> {{ report.report_id }}</p>
        <p><strong>Generated:</strong> {{ report.timestamp }}</p>
        <p><strong>Period:</strong> {{ report.start_date }} to {{ report.end_date }}</p>
        <p><strong>Total Findings:</strong> {{ summary.total_findings }}</p>
        <p><strong>Compliance Rate:</strong> {{ "%.1f"|format((summary.compliant / summary.total_findings * 100) if summary.total_findings > 0 else 0) }}%</p>
    </div>

    <h2>Findings by Status</h2>
    <table>
        <tr><th>Status</th><th>Count</th></tr>
        {% for status, count in summary.by_status.items() %}
        <tr><td>{{ status }}</td><td>{{ count }}</td></tr>
        {% endfor %}
    </table>

    <h2>Findings by Risk Level</h2>
    <table>
        <tr><th>Risk Level</th><th>Count</th></tr>
        {% for risk, count in summary.by_risk.items() %}
        <tr><td class="risk-{{ risk }}">{{ risk }}</td><td>{{ count }}</td></tr>
        {% endfor %}
    </table>

    <h2>Detailed Findings</h2>
    {% for finding in report.findings %}
    <div class="finding {{ finding.status }}">
        <h3>{{ finding.requirement }}</h3>
        <p><strong>Status:</strong> {{ finding.status }}</p>
        <p><strong>Risk Level:</strong> <span class="risk-{{ finding.risk_level }}">{{ finding.risk_level }}</span></p>
        <p><strong>Description:</strong> {{ finding.description }}</p>
        {% if finding.recommendation %}
        <p><strong>Recommendation:</strong> {{ finding.recommendation }}</p>
        {% endif %}
    </div>
    {% endfor %}
</body>
</html>
        """

        template = Template(html_template)
        html_content = template.render(report=report, summary=report.get_summary())

        with open(output_path, "w", encoding="utf - 8") as f:
            f.write(html_content)

        return str(output_path)


# 便捷函数
def create_compliance_reporter(**kwargs) -> ComplianceReporter:
    """创建合规报告生成器"""
    return ComplianceReporter(**kwargs)
