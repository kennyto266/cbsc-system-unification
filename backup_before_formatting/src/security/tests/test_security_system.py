"""
安全系統測試
驗證審計日誌、合規管理和事件響應功能
"""

import json
from datetime import datetime, timedelta

import pytest

from src.security.audit import AuditConfig, AuditLogger
from src.security.compliance import ConsentType, DataCategory, GDPRManager, PDPAManager
from src.security.dpia import DPIAManager, ProcessingNature
from src.security.incident_response import (
    IncidentManager,
    IncidentSeverity,
    IncidentType,
)
from src.security.monitoring import ComplianceMonitor
from src.security.security_integration import SecuritySystem


class TestAuditLogger:
    """測試審計日誌記錄器"""

    @pytest.fixture
    def audit_logger(self):
        """創建審計日誌記錄器"""
        config = AuditConfig(
            audit_enabled=True,
            log_level="DEBUG",
            enable_hash_chain=True,
            enable_encryption=False,  # 測試時禁用加密
        )
        return AuditLogger(config)

    def test_log_event(self, audit_logger):
        """測試記錄事件"""
        event_id = audit_logger.log(
            event_type="test",
            action="test_action",
            user_id="test_user",
            resource="test / resource",
        )

        assert event_id is not None
        assert len(event_id) > 0

    def test_query_logs(self, audit_logger):
        """測試查詢日誌"""
        # 記錄多個事件
        for i in range(5):
            audit_logger.log(
                event_type="test",
                action=f"action_{i}",
                user_id="test_user",
                resource="test / resource",
            )

        # 查詢日誌
        logs = audit_logger.query_logs(event_type="test")
        assert len(logs) >= 5

    def test_filter_sensitive_data(self, audit_logger):
        """測試過濾敏感數據"""
        sensitive_data = {
            "password": "secret123",
            "api_key": "key_12345",
            "name": "John Doe",
            "safe_field": "public_data",
        }

        # 使用私有方法測試
        filtered = audit_logger._filter_sensitive_data(sensitive_data)

        assert filtered["password"] == "***REDACTED***"
        assert filtered["api_key"] == "***REDACTED***"
        assert filtered["name"] == "John Doe"
        assert filtered["safe_field"] == "public_data"


class TestGDPRManager:
    """測試GDPR管理器"""

    @pytest.fixture
    def gdpr_manager(self):
        """創建GDPR管理器"""
        return GDPRManager()

    def test_register_data_processing(self, gdpr_manager):
        """測試註冊數據處理活動"""
        processing_id = gdpr_manager.register_data_processing(
            purpose="測試目的",
            data_category=DataCategory.PERSONAL_IDENTIFIERS,
            data_types=["姓名", "電郵"],
            legal_basis="consent",
            retention_period=365,
        )

        assert processing_id is not None
        assert processing_id in gdpr_manager.processing_records

    def test_record_consent(self, gdpr_manager):
        """測試記錄同意"""
        consent_id = gdpr_manager.record_consent(
            subject_id="user_123",
            purpose="marketing",
            consent_given=True,
            consent_text="我同意接收營銷郵件",
        )

        assert consent_id is not None
        assert "user_123" in gdpr_manager.consent_records

    def test_create_data_subject_request(self, gdpr_manager):
        """測試創建數據主體請求"""
        request_id = gdpr_manager.create_data_subject_request(
            subject_id="user_123", rights=["access"]
        )

        assert request_id is not None
        assert request_id in gdpr_manager.data_subject_requests


class TestIncidentManager:
    """測試事件管理器"""

    @pytest.fixture
    def incident_manager(self):
        """創建事件管理器"""
        return IncidentManager()

    def test_report_incident(self, incident_manager):
        """測試報告事件"""
        incident_id = incident_manager.report_incident(
            title="測試事件",
            description="測試描述",
            incident_type=IncidentType.UNAUTHORIZED_ACCESS,
            severity=IncidentSeverity.MEDIUM,
            reported_by="test_user",
        )

        assert incident_id is not None
        assert incident_id in incident_manager.incidents
        assert incident_manager.incidents[incident_id].status.value == "new"

    def test_update_incident_status(self, incident_manager):
        """測試更新事件狀態"""
        incident_id = incident_manager.report_incident(
            title="測試事件",
            description="測試描述",
            incident_type=IncidentType.UNAUTHORIZED_ACCESS,
            severity=IncidentSeverity.MEDIUM,
            reported_by="test_user",
        )

        success = incident_manager.update_incident_status(
            incident_id=incident_id,
            status=IncidentStatus.INVESTIGATING,
            actor="analyst",
        )

        assert success is True
        assert incident_manager.incidents[incident_id].status.value == "investigating"


class TestDPIAManager:
    """測試DPIA管理器"""

    @pytest.fixture
    def dpia_manager(self):
        """創建DPIA管理器"""
        return DPIAManager()

    def test_create_dpia(self, dpia_manager):
        """測試創建DPIA"""
        dpia_id = dpia_manager.create_dpia(
            name="測試DPIA",
            description="測試描述",
            processing_nature=[ProcessingNature.LARGE_SCALE_PROCESSING],
            purpose="測試目的",
            legal_basis="legitimate_interest",
            data_types=["個人資料"],
            data_sources=["客戶數據庫"],
            data_subjects=["客戶"],
            assessed_by="privacy_officer",
        )

        assert dpia_id is not None
        assert dpia_id in dpia_manager.dpias

    def test_assess_risks(self, dpia_manager):
        """測試風險評估"""
        dpia_id = dpia_manager.create_dpia(
            name="測試DPIA",
            description="測試描述",
            processing_nature=[ProcessingNature.LARGE_SCALE_PROCESSING],
            purpose="測試目的",
            legal_basis="legitimate_interest",
            data_types=["個人資料"],
            data_sources=["客戶數據庫"],
            data_subjects=["客戶"],
            assessed_by="privacy_officer",
        )

        risks = [
            {
                "description": "數據洩露",
                "level": "high",
                "likelihood": "medium",
                "impact": "high",
            }
        ]

        success = dpia_manager.assess_risks(dpia_id, risks)
        assert success is True
        assert dpia_manager.dpias[dpia_id].risk_assessment is not None


class TestComplianceMonitor:
    """測試合規監控器"""

    @pytest.fixture
    def monitor(self):
        """創建合規監控器"""
        return ComplianceMonitor()

    def test_register_check(self, monitor):
        """測試註冊合規檢查"""
        check_id = monitor.register_check(
            name="測試檢查", description="測試描述", framework="GDPR", severity="high"
        )

        assert check_id in monitor.checks
        assert monitor.checks[check_id].framework == "GDPR"

    def test_run_compliance_check(self, monitor):
        """測試運行合規檢查"""
        check_id = monitor.register_check(
            name="測試檢查", description="測試描述", framework="GDPR", severity="high"
        )

        result = monitor.run_compliance_check(
            check_id, {"compliant": True, "message": "檢查通過"}
        )

        assert result is True
        assert monitor.checks[check_id].status.value == "compliant"

    def test_get_compliance_score(self, monitor):
        """測試獲取合規評分"""
        # 註冊一些檢查
        monitor.register_check("檢查1", "描述1", "GDPR", "high")
        monitor.register_check("檢查2", "描述2", "GDPR", "medium")
        monitor.register_check("檢查3", "描述3", "PDPA", "high")

        score = monitor.get_compliance_score("GDPR")
        assert "compliance_score" in score
        assert "total_checks" in score
        assert score["framework"] == "GDPR"


class TestSecuritySystem:
    """測試安全系統整合"""

    @pytest.fixture
    def security_system(self):
        """創建安全系統"""
        config = AuditConfig(
            audit_enabled=True, enable_encryption=False  # 測試時禁用加密
        )
        return SecuritySystem(config)

    def test_log_user_action(self, security_system):
        """測試記錄用戶操作"""
        security_system.log_user_action(
            user_id="test_user", action="test_action", resource="test / resource"
        )

        # 驗證日誌已記錄
        logs = security_system.audit_logger.query_logs(event_type="user_action")
        assert len(logs) > 0

    def test_log_api_call(self, security_system):
        """測試記錄API調用"""
        security_system.log_api_call(
            method="GET", path="/api / test", user_id="test_user", status_code=200
        )

        logs = security_system.audit_logger.query_logs(event_type="api_calls")
        assert len(logs) > 0

    def test_create_incident(self, security_system):
        """測試創建事件"""
        incident_id = security_system.create_incident(
            title="測試事件",
            description="測試描述",
            incident_type="test",
            severity="medium",
            reported_by="test_user",
        )

        assert incident_id is not None
        assert incident_id in security_system.incident_manager.incidents

    def test_run_compliance_checks(self, security_system):
        """測試運行合規檢查"""
        results = security_system.run_compliance_checks()
        assert isinstance(results, dict)

    def test_export_all_reports(self, security_system):
        """測試導出所有報告"""
        report = security_system.export_all_reports()

        assert "generated_at" in report
        assert "compliance_scores" in report
        assert "audit_integrity" in report
        assert "open_incidents" in report


class TestIntegration:
    """測試集成功能"""

    def test_end_to_end_workflow(self):
        """測試端到端工作流程"""
        # 創建安全系統
        config = AuditConfig(enable_encryption=False)
        security = SecuritySystem(config)

        # 1. 用戶登錄
        security.log_user_action(
            user_id="user_001", action="login", resource="auth / login"
        )

        # 2. 訪問數據
        security.log_api_call(
            method="GET", path="/api / portfolio", user_id="user_001", status_code=200
        )

        # 3. 創建DPIA
        dpia_id = security.create_dpia(
            name="客戶數據分析",
            description="分析客戶交易行為",
            processing_nature=[ProcessingNature.LARGE_SCALE_PROCESSING],
            purpose="提供個性化服務",
            legal_basis="legitimate_interest",
            data_types=["交易記錄", "個人資料"],
            assessed_by="privacy_officer",
        )

        # 4. 創建安全事件
        incident_id = security.create_incident(
            title="可疑活動",
            description="檢測到異常登錄",
            incident_type="unusual_activity",
            severity="medium",
            reported_by="security_team",
        )

        # 5. 運行合規檢查
        results = security.run_compliance_checks()

        # 6. 驗證日誌完整性
        integrity = security.verify_audit_integrity()

        # 驗證結果
        assert dpia_id is not None
        assert incident_id is not None
        assert isinstance(results, dict)
        assert integrity is not None


if __name__ == "__main__":
    # 運行測試
    pytest.main([__file__, "-v"])
