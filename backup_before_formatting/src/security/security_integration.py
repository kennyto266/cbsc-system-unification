from datetime import datetime
"""
安全系統集成層
整合審計日誌、合規管理、事件響應和監控系統
"""

from fastapi import FastAPI, Request, Response

from .audit import AuditConfig, AuditLogger, AuditMiddleware
from .compliance import GDPRManager, ISO27001Manager, PDPAManager
from .dpia import DPIAManager
from .incident_response import IncidentManager
from .monitoring import ComplianceMonitor


class SecuritySystem:
    """安全系統整合"""

    def __init__(self, config: AuditConfig = None):
        """
        初始化安全系統

        Args:
            config: 審計配置
        """
        self.config = config or AuditConfig()
        self.audit_logger = AuditLogger(self.config)

        # 初始化各個組件
        self.gdpr_manager = GDPRManager(self.audit_logger)
        self.pdpa_manager = PDPAManager(self.audit_logger)
        self.iso27001_manager = ISO27001Manager(self.audit_logger)
        self.incident_manager = IncidentManager(self.audit_logger)
        self.dpia_manager = DPIAManager(self.audit_logger)
        self.compliance_monitor = ComplianceMonitor(self.audit_logger)

    def setup_middleware(self, app: FastAPI):
        """
        設置中間件

        Args:
            app: FastAPI應用
        """
        app.add_middleware(AuditMiddleware, config=self.config)

    def log_user_action(
        self,
        user_id: str,
        action: str,
        resource: str,
        source_ip: str = None,
        user_agent: str = None,
        details: dict = None,
    ):
        """
        記錄用戶操作

        Args:
            user_id: 用戶ID
            action: 操作
            resource: 資源
            source_ip: 源IP
            user_agent: 用戶代理
            details: 詳細信息
        """
        self.audit_logger.log(
            event_type="user_action",
            action=action,
            user_id=user_id,
            resource=resource,
            source_ip=source_ip,
            user_agent=user_agent,
            details=details or {},
        )

    def log_api_call(
        self,
        method: str,
        path: str,
        user_id: str,
        status_code: int,
        source_ip: str = None,
        details: dict = None,
    ):
        """
        記錄API調用

        Args:
            method: HTTP方法
            path: 路徑
            user_id: 用戶ID
            status_code: 狀態碼
            source_ip: 源IP
            details: 詳細信息
        """
        self.audit_logger.log(
            event_type="api_calls",
            action=method,
            user_id=user_id,
            resource=path,
            status="success" if 200 <= status_code < 400 else "failure",
            source_ip=source_ip,
            details=details or {},
        )

    def log_trade_execution(
        self,
        user_id: str,
        trade_id: str,
        symbol: str,
        action: str,
        quantity: float,
        price: float,
        source_ip: str = None,
    ):
        """
        記錄交易執行

        Args:
            user_id: 用戶ID
            trade_id: 交易ID
            symbol: 股票代碼
            action: 動作(BUY / SELL)
            quantity: 數量
            price: 價格
            source_ip: 源IP
        """
        self.audit_logger.log(
            event_type="trading",
            action=action,
            user_id=user_id,
            resource=f"trade/{trade_id}",
            source_ip=source_ip,
            details={
                "trade_id": trade_id,
                "symbol": symbol,
                "quantity": quantity,
                "price": price,
                "amount": quantity * price,
            },
        )

    def create_incident(
        self,
        title: str,
        description: str,
        incident_type: str,
        severity: str,
        reported_by: str,
        **kwargs,
    ) -> str:
        """
        創建安全事件

        Args:
            title: 標題
            description: 描述
            incident_type: 事件類型
            severity: 嚴重性
            reported_by: 報告人
            **kwargs: 其他參數

        Returns:
            事件ID
        """
        return self.incident_manager.report_incident(
            title=title,
            description=description,
            incident_type=incident_type,
            severity=severity,
            reported_by=reported_by,
            **kwargs,
        )

    def run_compliance_checks(self) -> dict:
        """
        運行合規檢查

        Returns:
            檢查結果
        """
        return self.compliance_monitor.run_all_checks()

    def get_compliance_score(self, framework: str = None) -> dict:
        """
        獲取合規評分

        Args:
            framework: 合規框架

        Returns:
            合規評分
        """
        return self.compliance_monitor.get_compliance_score(framework)

    def generate_audit_report(
        self, start_time: str = None, end_time: str = None, event_type: str = None
    ) -> list:
        """
        生成審計報告

        Args:
            start_time: 開始時間
            end_time: 結束時間
            event_type: 事件類型

        Returns:
            審計日誌
        """
        return self.audit_logger.query_logs(
            start_time=start_time, end_time=end_time, event_type=event_type
        )

    def verify_audit_integrity(self) -> dict:
        """
        驗證審計日誌完整性

        Returns:
            驗證報告
        """
        return self.audit_logger.verify_integrity()

    def create_dpia(
        self,
        name: str,
        description: str,
        processing_nature: list,
        purpose: str,
        legal_basis: str,
        data_types: list,
        assessed_by: str,
    ) -> str:
        """
        創建DPIA

        Args:
            name: 名稱
            description: 描述
            processing_nature: 處理性質
            purpose: 目的
            legal_basis: 法律依據
            data_types: 數據類型
            assessed_by: 評估人

        Returns:
            DPIA ID
        """
        return self.dpia_manager.create_dpia(
            name=name,
            description=description,
            processing_nature=processing_nature,
            purpose=purpose,
            legal_basis=legal_basis,
            data_types=data_types,
            data_sources=[],
            data_subjects=[],
            assessed_by=assessed_by,
        )

    def export_all_reports(self) -> dict:
        """
        導出所有報告

        Returns:
            綜合報告
        """
        return {
            "generated_at": (
                self.audit_logger.query_logs()[-1].get("timestamp")
                if self.audit_logger.query_logs()
                else datetime.now().isoformat()
            ),
            "compliance_scores": {
                "gdpr": self.get_compliance_score("GDPR"),
                "pdpa": self.get_compliance_score("PDPA"),
                "iso27001": self.get_compliance_score("ISO 27001"),
            },
            "audit_integrity": self.verify_audit_integrity(),
            "open_incidents": len(
                [
                    i
                    for i in self.incident_manager.incidents.values()
                    if i.status not in ["resolved", "closed"]
                ]
            ),
            "dpias_count": len(self.dpia_manager.dpias),
            "total_violations": len(self.compliance_monitor.violations),
            "high_risk_checks": len(
                [
                    c
                    for c in self.compliance_monitor.checks.values()
                    if c.severity in ["high", "critical"]
                ]
            ),
        }
