"""
T111: 透明度報告生成系統

實現實時透明度報告生成功能，包括：
- 數據使用情況統計
- 第三方共享報告
- 隱私事件歷史
- 合規狀態概覽
- 多格式導出 (PDF / HTML / JSON)
- 實時監控儀表板
"""

import json
import logging
import os
import statistics
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .access_tracking import AccessEvent, AccessStatus, AccessType
from .sovereignty_controls import ConsentStatus, DataCategory, DataSovereigntyController


class ReportFormat(Enum):
    """報告格式"""

    JSON = "json"
    HTML = "html"
    PDF = "pdf"
    CSV = "csv"


class ComplianceStatus(Enum):
    """合規狀態"""

    COMPLIANT = "compliant"  # 合規
    NON_COMPLIANT = "non_compliant"  # 不合規
    WARNING = "warning"  # 警告
    PENDING = "pending"  # 待審核


@dataclass
class DataUsageStats:
    """數據使用統計"""

    category: DataCategory
    total_accesses: int
    unique_users: int
    read_operations: int
    write_operations: int
    last_access: Optional[datetime]
    retention_compliant: bool
    data_volume_mb: float


@dataclass
class ThirdPartyShare:
    """第三方共享記錄"""

    partner_name: str
    data_categories: List[DataCategory]
    purpose: str
    legal_basis: str
    shared_at: datetime
    is_active: bool
    data_volume: float  # MB
    compliance_checked: bool


@dataclass
class PrivacyEvent:
    """隱私事件"""

    event_id: str
    event_type: str
    severity: str  # low, medium, high, critical
    description: str
    occurred_at: datetime
    affected_users: int
    resolved: bool
    resolution_notes: Optional[str]


@dataclass
class ComplianceCheck:
    """合規檢查結果"""

    regulation: str  # GDPR, PDPA, etc.
    requirement: str
    status: ComplianceStatus
    checked_at: datetime
    details: str
    action_required: Optional[str]


class TransparencyReportGenerator:
    """透明度報告生成器"""

    def __init__(self, sovereignty_controller: DataSovereigntyController):
        self.sovereignty = sovereignty_controller
        self.logger = logging.getLogger("privacy.transparency")

    def generate_overall_report(
        self, user_id: str = None, format: ReportFormat = ReportFormat.HTML
    ) -> Dict[str, Any]:
        """
        生成總體透明度報告

        Args:
            user_id: 用戶ID (None表示全系統報告)
            format: 報告格式

        Returns:
            Dict: 報告數據
        """
        report = {
            "report_id": f"TR_{datetime.now().strftime('%Y % m % d_ % H % M % S')}",
            "generated_at": datetime.now().isoformat(),
            "report_type": "overall" if not user_id else "user_specific",
            "user_id": user_id,
            "data_usage": {},
            "third_party_shares": [],
            "privacy_events": [],
            "compliance_status": {},
            "recommendations": [],
        }

        # 數據使用統計
        report["data_usage"] = self._generate_data_usage_stats(user_id)

        # 第三方共享
        report["third_party_shares"] = self._generate_third_party_share_report()

        # 隱私事件
        report["privacy_events"] = self._generate_privacy_events_report()

        # 合規狀態
        report["compliance_status"] = self._generate_compliance_report()

        # 建議
        report["recommendations"] = self._generate_recommendations(report)

        # 格式化輸出
        if format == ReportFormat.JSON:
            return report
        elif format == ReportFormat.HTML:
            return self._format_as_html(report)
        elif format == ReportFormat.PDF:
            return self._format_as_pdf(report)
        else:
            return report

    def _generate_data_usage_stats(self, user_id: Optional[str]) -> Dict[str, Any]:
        """生成數據使用統計"""
        stats = {}

        for category in DataCategory:
            # 模擬數據使用統計
            # 在實際實現中，應該從數據庫查詢真實的訪問記錄
            total_accesses = self._count_category_accesses(category, user_id)
            unique_users = self._count_unique_users(category, user_id)
            read_ops = self._count_operation_type(category, AccessType.READ, user_id)
            write_ops = self._count_operation_type(category, AccessType.WRITE, user_id)
            last_access = self._get_last_access_time(category, user_id)

            # 檢查保留合規性
            retention_policies = self.sovereignty.get_retention_policies(user_id or "")
            retention_compliant = self._check_retention_compliance(
                category, retention_policies
            )

            stats[category.value] = asdict(
                DataUsageStats(
                    category=category,
                    total_accesses=total_accesses,
                    unique_users=unique_users,
                    read_operations=read_ops,
                    write_operations=write_ops,
                    last_access=last_access,
                    retention_compliant=retention_compliant,
                    data_volume=total_accesses * 0.5,  # 模擬數據量 (MB)
                )
            )

        return stats

    def _count_category_accesses(
        self, category: DataCategory, user_id: Optional[str]
    ) -> int:
        """計算類別訪問次數"""
        # TODO: 從 access_tracking 查詢真實數據
        # 這裡返回模擬數據
        import random

        return random.randint(100, 10000)

    def _count_unique_users(
        self, category: DataCategory, user_id: Optional[str]
    ) -> int:
        """計算唯一用戶數"""
        # TODO: 從 access_tracking 查詢真實數據
        import random

        return random.randint(50, 500)

    def _count_operation_type(
        self, category: DataCategory, op_type: AccessType, user_id: Optional[str]
    ) -> int:
        """計算操作類型次數"""
        # TODO: 從 access_tracking 查詢真實數據
        import random

        if op_type == AccessType.READ:
            return random.randint(50, 5000)
        else:
            return random.randint(10, 1000)

    def _get_last_access_time(
        self, category: DataCategory, user_id: Optional[str]
    ) -> Optional[datetime]:
        """獲取最後訪問時間"""
        # TODO: 從 access_tracking 查詢真實數據
        import random

        if random.random() > 0.2:  # 80 % 概率有訪問記錄
            return datetime.now() - timedelta(days=random.randint(0, 30))
        return None

    def _check_retention_compliance(
        self, category: DataCategory, policies: List
    ) -> bool:
        """檢查保留合規性"""
        if not policies:
            return True

        for policy in policies:
            if policy.category == category:
                return True  # 簡化邏輯

        return False

    def _generate_third_party_share_report(self) -> List[Dict[str, Any]]:
        """生成第三方共享報告"""
        # 模擬第三方共享數據
        shares = []

        # 模擬一些共享記錄
        mock_shares = [
            {
                "partner_name": "香港金融管理局",
                "data_categories": [DataCategory.FINANCIAL_DATA],
                "purpose": "監管合規",
                "legal_basis": "法律義務",
                "shared_at": datetime.now() - timedelta(days=5),
                "is_active": True,
                "data_volume": 150.5,
                "compliance_checked": True,
            },
            {
                "partner_name": "交易結算系統",
                "data_categories": [DataCategory.TRADING_HISTORY],
                "purpose": "交易處理",
                "legal_basis": "合同履行",
                "shared_at": datetime.now() - timedelta(days=2),
                "is_active": True,
                "data_volume": 320.8,
                "compliance_checked": True,
            },
        ]

        for share_data in mock_shares:
            shares.append(asdict(ThirdPartyShare(**share_data)))

        return shares

    def _generate_privacy_events_report(self) -> List[Dict[str, Any]]:
        """生成隱私事件報告"""
        events = []

        # 模擬隱私事件
        mock_events = [
            {
                "event_id": "PE - 2024 - 001",
                "event_type": "data_breach",
                "severity": "high",
                "description": "檢測到未授權的數據訪問嘗試",
                "occurred_at": datetime.now() - timedelta(days=7),
                "affected_users": 5,
                "resolved": True,
                "resolution_notes": "已加強訪問控制，通知受影響用戶",
            },
            {
                "event_id": "PE - 2024 - 002",
                "event_type": "consent_expired",
                "severity": "medium",
                "description": "部分用戶同意已過期",
                "occurred_at": datetime.now() - timedelta(days=3),
                "affected_users": 23,
                "resolved": False,
                "resolution_notes": None,
            },
        ]

        for event_data in mock_events:
            events.append(asdict(PrivacyEvent(**event_data)))

        return events

    def _generate_compliance_report(self) -> Dict[str, Dict[str, Any]]:
        """生成合規狀態報告"""
        compliance = {}

        # 模擬合規檢查
        regulations = ["GDPR", "PDPA", "HKMA指引", "證監會規定"]

        for regulation in regulations:
            checks = []

            # 為每個法規生成檢查項目
            if regulation == "GDPR":
                checks = [
                    {
                        "requirement": "數據主體權利",
                        "status": ComplianceStatus.COMPLIANT,
                        "details": "所有數據主體權利已正確實施",
                        "action_required": None,
                    },
                    {
                        "requirement": "同意管理",
                        "status": ComplianceStatus.WARNING,
                        "details": "5 % 用戶同意已過期未更新",
                        "action_required": "通知用戶更新同意",
                    },
                ]
            elif regulation == "PDPA":
                checks = [
                    {
                        "requirement": "數據收集通知",
                        "status": ComplianceStatus.COMPLIANT,
                        "details": "已提供清晰的數據收集通知",
                        "action_required": None,
                    },
                    {
                        "requirement": "安全措施",
                        "status": ComplianceStatus.COMPLIANT,
                        "details": "已實施適當的安全措施",
                        "action_required": None,
                    },
                ]

            compliance[regulation] = {
                "overall_status": self._calculate_overall_status(checks),
                "checks": [
                    asdict(
                        ComplianceCheck(
                            regulation=regulation, **check, checked_at=datetime.now()
                        )
                    )
                    for check in checks
                ],
            }

        return compliance

    def _calculate_overall_status(self, checks: List[Dict]) -> ComplianceStatus:
        """計算整體合規狀態"""
        if any(c["status"] == ComplianceStatus.NON_COMPLIANT for c in checks):
            return ComplianceStatus.NON_COMPLIANT
        elif any(c["status"] == ComplianceStatus.WARNING for c in checks):
            return ComplianceStatus.WARNING
        else:
            return ComplianceStatus.COMPLIANT

    def _generate_recommendations(self, report: Dict[str, Any]) -> List[str]:
        """生成改進建議"""
        recommendations = []

        # 檢查合規警告
        for regulation, data in report.get("compliance_status", {}).items():
            if data["overall_status"] in [
                ComplianceStatus.NON_COMPLIANT,
                ComplianceStatus.WARNING,
            ]:
                recommendations.append(
                    f"解決 {regulation} 合規問題：{data['checks'][0]['action_required']}"
                )

        # 檢查數據使用
        for category, stats in report.get("data_usage", {}).items():
            if not stats.get("retention_compliant", True):
                recommendations.append(f"更新 {category} 數據保留策略以符合規定")

        # 檢查隱私事件
        unresolved_events = [
            e for e in report.get("privacy_events", []) if not e.get("resolved", False)
        ]
        if unresolved_events:
            recommendations.append(f"處理 {len(unresolved_events)} 個未解決的隱私事件")

        # 檢查第三方共享
        inactive_shares = [
            s
            for s in report.get("third_party_shares", [])
            if not s.get("is_active", True)
        ]
        if inactive_shares:
            recommendations.append(
                f"審查 {len(inactive_shares)} 個非活躍第三方共享協議"
            )

        return recommendations

    def _format_as_html(self, report: Dict[str, Any]) -> str:
        """格式化為HTML"""
        html = """
        <!DOCTYPE html>
        <html lang="zh - CN">
        <head>
            <meta charset="UTF - 8">
            <meta name="viewport" content="width=device - width, initial - scale=1.0">
            <title>透明度報告 - {report['report_id']}</title>
            <style>
                body {{ font - family: 'Segoe UI', sans - serif; margin: 40px; color: #333; }}
                h1 {{ color: #2c3e50; border - bottom: 3px solid #3498db; padding - bottom: 10px; }}
                h2 {{ color: #34495e; margin - top: 30px; }}
                .metric {{ background: #f8f9fa; padding: 15px; margin: 10px 0; border - left: 4px solid #3498db; }}
                .status - compliant {{ color: #27ae60; font - weight: bold; }}
                .status - warning {{ color: #f39c12; font - weight: bold; }}
                .status - non - compliant {{ color: #e74c3c; font - weight: bold; }}
                .table {{ width: 100%; border - collapse: collapse; margin: 20px 0; }}
                .table th, .table td {{ border: 1px solid #ddd; padding: 12px; text - align: left; }}
                .table th {{ background - color: #3498db; color: white; }}
                .recommendation {{ background: #fff3cd; border - left: 4px solid #ffc107; padding: 10px; margin: 5px 0; }}
            </style>
        </head>
        <body>
            <h1>隱私透明度報告</h1>
            <p><strong>報告ID:</strong> {report['report_id']}</p>
            <p><strong>生成時間:</strong> {report['generated_at']}</p>
            <p><strong>類型:</strong> {"用戶特定報告" if report['user_id'] else "全系統報告"}</p>

            <h2>📊 數據使用概況</h2>
        """

        # 數據使用表格
        html += '<table class="table"><thead><tr><th>數據類別</th><th>總訪問次數</th><th>唯一用戶</th><th>讀取操作</th><th>寫入操作</th><th>保留合規</th></tr></thead><tbody>'
        for category, stats in report.get("data_usage", {}).items():
            status_class = (
                "status - compliant"
                if stats.get("retention_compliant")
                else "status - warning"
            )
            status_text = "✓ 合規" if stats.get("retention_compliant") else "⚠ 需要審查"
            html += f"<tr><td>{category}</td><td>{stats['total_accesses']}</td><td>{stats['unique_users']}</td><td>{stats['read_operations']}</td><td>{stats['write_operations']}</td><td class='{status_class}'>{status_text}</td></tr>"
        html += "</tbody></table>"

        # 第三方共享
        html += '<h2>🤝 第三方數據共享</h2><table class="table"><thead><tr><th>合作夥伴</th><th>數據類別</th><th>目的</th><th>法律依據</th><th>狀態</th></tr></thead><tbody>'
        for share in report.get("third_party_shares", []):
            status_text = "✓ 活躍" if share["is_active"] else "⚠ 非活躍"
            html += f"<tr><td>{share['partner_name']}</td><td>{', '.join([c.value for c in share['data_categories']])}</td><td>{share['purpose']}</td><td>{share['legal_basis']}</td><td>{status_text}</td></tr>"
        html += "</tbody></table>"

        # 隱私事件
        html += '<h2>⚠️ 隱私事件</h2><table class="table"><thead><tr><th>事件ID</th><th>類型</th><th>嚴重程度</th><th>描述</th><th>狀態</th></tr></thead><tbody>'
        for event in report.get("privacy_events", []):
            resolved_text = "✓ 已解決" if event["resolved"] else "⚠ 未解決"
            html += f"<tr><td>{event['event_id']}</td><td>{event['event_type']}</td><td>{event['severity']}</td><td>{event['description']}</td><td>{resolved_text}</td></tr>"
        html += "</tbody></table>"

        # 合規狀態
        html += "<h2>✅ 合規狀態</h2>"
        for regulation, data in report.get("compliance_status", {}).items():
            status_class = f"status-{data['overall_status'].value}"
            html += f'<div class="metric"><h3>{regulation}</h3><p class="{status_class}">整體狀態: {data["overall_status"].value.upper()}</p></div>'

        # 建議
        if report.get("recommendations"):
            html += "<h2>💡 改進建議</h2>"
            for rec in report["recommendations"]:
                html += f'<div class="recommendation">• {rec}</div>'

        html += """
            <hr>
            <p style="color: #7f8c8d; font - size: 12px;">
                報告生成於 {report['generated_at']} |
                <a href="#">查看詳細數據</a> |
                <a href="#">導出PDF版本</a>
            </p>
        </body>
        </html>
        """

        return html

    def _format_as_pdf(self, report: Dict[str, Any]) -> str:
        """格式化為PDF (返回HTML，實際PDF轉換由前端處理)"""
        # 簡化實現，返回HTML供前端轉換
        return self._format_as_html(report)

    def get_real_time_dashboard(self) -> Dict[str, Any]:
        """獲取實時監控儀表板數據"""
        return {
            "timestamp": datetime.now().isoformat(),
            "active_users": 1234,  # 模擬數據
            "data_requests_last_hour": 5678,
            "consents_granted_today": 89,
            "consents_withdrawn_today": 12,
            "privacy_events_last_30_days": 3,
            "compliance_score": 92.5,  # 百分比
            "data_volume_gb_today": 45.6,
            "third_party_shares_active": 15,
            "retention_policies_active": 8,
            "data_portability_requests_pending": 2,
        }

    def export_report(
        self, report: Dict[str, Any], format: ReportFormat, output_path: str
    ) -> bool:
        """
        導出報告

        Args:
            report: 報告數據
            format: 格式
            output_path: 輸出路徑

        Returns:
            bool: 是否成功
        """
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            if format == ReportFormat.JSON:
                with open(output_path, "w", encoding="utf - 8") as f:
                    json.dump(report, f, ensure_ascii=False, indent=2, default=str)
            elif format == ReportFormat.HTML:
                html = self._format_as_html(report)
                with open(output_path, "w", encoding="utf - 8") as f:
                    f.write(html)
            elif format == ReportFormat.CSV:
                import pandas as pd

                # 導出數據使用統計為CSV
                df = pd.DataFrame(report.get("data_usage", {}).values())
                df.to_csv(output_path, index=False)

            self.logger.info(f"報告已導出: {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"導出報告失敗: {e}")
            return False
