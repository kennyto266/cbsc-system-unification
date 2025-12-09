"""
安全系統使用示例
展示如何在港股量化交易系統中使用審計日誌和合規功能
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List

from src.security.audit import AuditConfig, AuditLogger
from src.security.compliance import (
    DataCategory,
    GDPRManager,
    ISO27001Manager,
    PDPAManager,
)
from src.security.dpia import DPIAManager, ProcessingNature
from src.security.incident_response import IncidentManager
from src.security.monitoring import ComplianceMonitor
from src.security.security_integration import SecuritySystem


def example_1_basic_audit_logging():
    """示例1: 基本的審計日誌記錄"""
    print("=" * 60)
    print("示例1: 基本的審計日誌記錄")
    print("=" * 60)

    # 創建審計配置
    config = AuditConfig(
        audit_enabled=True,
        log_level="INFO",
        enable_hash_chain=True,
        enable_encryption=True,
        gdpr_compliance=True,
    )

    # 初始化審計日誌記錄器
    audit_logger = AuditLogger(config)

    # 記錄用戶登錄
    event_id = audit_logger.log(
        event_type="authentication",
        action="login",
        user_id="trader001",
        source_ip="192.168.1.100",
        user_agent="Mozilla / 5.0 (Windows NT 10.0; Win64; x64)",
        details={"method": "password", "mfa_enabled": True, "login_time": "09:30:00"},
        risk_score=10,
    )
    print(f"✅ 記錄用戶登錄，事件ID: {event_id}")

    # 記錄用戶查看投資組合
    audit_logger.log(
        event_type="data_access",
        action="view",
        user_id="trader001",
        resource="portfolio / 0700.HK",
        source_ip="192.168.1.100",
        details={"symbol": "0700.HK", "view_type": "detailed"},
        risk_score=5,
    )
    print("✅ 記錄投資組合查看")

    # 記錄下單
    audit_logger.log(
        event_type="trading",
        action="order_placed",
        user_id="trader001",
        resource="trade / ORD - 2024 - 001",
        source_ip="192.168.1.100",
        details={
            "symbol": "0700.HK",
            "action": "BUY",
            "quantity": 1000,
            "price": 380.50,
            "order_type": "market",
        },
        risk_score=30,
    )
    print("✅ 記錄下單操作")

    # 查詢今天的登錄記錄
    logs = audit_logger.query_logs(
        start_time=datetime.now().replace(hour=0, minute=0, second=0),
        event_type="authentication",
    )
    print(f"✅ 今天登錄次數: {len(logs)}")

    print()


def example_2_gdpr_compliance():
    """示例2: GDPR合規管理"""
    print("=" * 60)
    print("示例2: GDPR合規管理")
    print("=" * 60)

    audit_logger = AuditLogger()
    gdpr = GDPRManager(audit_logger)

    # 註冊數據處理活動
    processing_id = gdpr.register_data_processing(
        purpose="客戶交易記錄管理",
        data_category=DataCategory.FINANCIAL_DATA,
        data_types=["交易ID", "股票代碼", "價格", "數量", "時間"],
        legal_basis="contract",
        retention_period=2555,  # 7年
        recipients=["交易部門", "合規部門", "審計部門"],
    )
    print(f"✅ 註冊數據處理活動，ID: {processing_id}")

    # 記錄客戶同意
    consent_id = gdpr.record_consent(
        subject_id="customer_001",
        purpose="個性化投資建議",
        consent_given=True,
        consent_text="我同意使用我的交易數據來獲得個性化投資建議",
        ip_address="203.0.113.10",
        user_agent="Mozilla / 5.0",
    )
    print(f"✅ 記錄客戶同意，ID: {consent_id}")

    # 處理數據主體權利請求
    request_id = gdpr.create_data_subject_request(
        subject_id="customer_001",
        rights=["access", "portability"],
        details="客戶要求導出其所有交易記錄",
    )
    print(f"✅ 創建數據主體請求，ID: {request_id}")

    # 處理請求
    gdpr.process_data_subject_request(
        request_id=request_id,
        response_data={
            "exported_records": 150,
            "format": "JSON",
            "download_url": "https://secure.example.com / exports / customer_001_20241109.json",
            "expires_at": "2024 - 11 - 16T00:00:00Z",
        },
        notes="已成功導出客戶的所有交易記錄",
    )
    print("✅ 處理數據主體請求完成")

    # 檢查數據保留合規性
    expired_records = gdpr.check_retention_compliance()
    print(f"✅ 檢查數據保留合規性，過期記錄數量: {len(expired_records)}")

    print()


def example_3_incident_response():
    """示例3: 事件響應"""
    print("=" * 60)
    print("示例3: 事件響應")
    print("=" * 60)

    audit_logger = AuditLogger()
    incident_mgr = IncidentManager(audit_logger)

    # 報告可疑的登錄嘗試
    incident_id = incident_mgr.report_incident(
        title="多次失敗的登錄嘗試",
        description="檢測到來自異常IP地址的多次失敗登錄嘗試",
        incident_type="unauthorized_access",
        severity="high",
        reported_by="security_team",
        affected_systems=["login_server", "user_portal"],
        affected_data=["用戶名", "密碼嘗試記錄"],
        indicators=["brute_force_attempt", "suspicious_ip", "unusual_timing"],
    )
    print(f"✅ 報告安全事件，ID: {incident_id}")

    # 更新事件狀態
    incident_mgr.update_incident_status(
        incident_id=incident_id,
        status="investigating",
        actor="security_analyst",
        actions=["分析登錄日誌", "封鎖可疑IP", "通知用戶"],
    )
    print("✅ 更新事件狀態為'調查中'")

    # 遏制措施
    incident_mgr.add_timeline_entry(
        incident_id=incident_id,
        action="ip_blocked",
        description="已封鎖可疑IP地址 198.51.100.23",
        actor="security_analyst",
    )
    print("✅ 添加遏制措施")

    # 檢查通知要求
    requirements = incident_mgr.check_notification_requirements(incident_id)
    print("✅ 檢查通知要求:")
    print(f"   - GDPR通知: {requirements['gdpr_breach_notification']}")
    print(f"   - 監管機構通知: {requirements['supervisory_authority']}")

    # 生成事件報告
    report = incident_mgr.generate_incident_report(incident_id)
    print("✅ 生成事件報告")

    print()


def example_4_dpia():
    """示例4: DPIA隱私影響評估"""
    print("=" * 60)
    print("示例4: DPIA隱私影響評估")
    print("=" * 60)

    audit_logger = AuditLogger()
    dpia_mgr = DPIAManager(audit_logger)

    # 創建DPIA
    dpia_id = dpia_mgr.create_dpia(
        name="AI智能交易推薦系統",
        description="使用機器學習分析客戶交易歷史，提供個性化交易建議",
        processing_nature=[
            ProcessingNature.LARGE_SCALE_PROCESSING,
            ProcessingNature.PROFILING,
            ProcessingNature.AUTOMATED_DECISION,
        ],
        purpose="提供個性化交易建議，提高投資回報",
        legal_basis="legitimate_interest",
        data_types=["交易歷史", "投資偏好", "風險評估", "市場數據"],
        data_sources=["交易系統", "客戶資料庫", "市場數據API"],
        data_subjects=["所有註冊用戶"],
        assessed_by="privacy_officer",
        processors=["AI服務提供商", "雲服務商"],
        third_countries=["US", "SG"],
        data_volume="very_large",
        retention_period="2 years",
    )
    print(f"✅ 創建DPIA，ID: {dpia_id}")

    # 評估風險
    risks = [
        {
            "description": "個人交易數據洩露",
            "level": "high",
            "likelihood": "medium",
            "impact": "high",
        },
        {
            "description": "算法偏見導致不公平推薦",
            "level": "medium",
            "likelihood": "low",
            "impact": "medium",
        },
        {
            "description": "自動化決策錯誤",
            "level": "medium",
            "likelihood": "medium",
            "impact": "high",
        },
    ]
    dpia_mgr.assess_risks(dpia_id, risks)
    print("✅ 完成風險評估")

    # 添加諮詢記錄
    dpia_mgr.add_consultation_record(
        dpia_id=dpia_id,
        stakeholder="客戶代表委員會",
        consultation_type="feedback",
        feedback="客戶對AI推薦系統表示歡迎，但關注數據隱私保護",
        consultation_date=datetime(2024, 1, 15),
    )
    dpia_mgr.add_consultation_record(
        dpia_id=dpia_id,
        stakeholder="合規部門",
        consultation_type="review",
        feedback="建議增加透明度，允許客戶查看推薦邏輯",
        consultation_date=datetime(2024, 1, 20),
    )
    print("✅ 添加利益相關者諮詢記錄")

    # 添加緩解措施
    measure1_id = dpia_mgr.add_mitigation_measure(
        dpia_id=dpia_id,
        description="實施端到端加密保護交易數據",
        effectiveness="high",
        owner="security_team",
        deadline=datetime(2024, 3, 31),
    )
    measure2_id = dpia_mgr.add_mitigation_measure(
        dpia_id=dpia_id,
        description="建立算法審計和偏見檢測機制",
        effectiveness="medium",
        owner="ai_team",
        deadline=datetime(2024, 4, 30),
    )
    measure3_id = dpia_mgr.add_mitigation_measure(
        dpia_id=dpia_id,
        description="提供用戶友好的推薦解釋界面",
        effectiveness="medium",
        owner="ux_team",
        deadline=datetime(2024, 5, 31),
    )
    print("✅ 添加緩解措施")

    # 設置DPO意見
    dpia_mgr.set_dpo_opinion(
        dpia_id=dpia_id,
        opinion="建議批准此DPIA，但要求完成所有緩解措施。建立定期審查機制，特別關注算法公平性和透明度。",
        reviewed_by="data_protection_officer",
    )
    print("✅ 設置DPO意見")

    # 完成DPIA
    dpia_mgr.complete_dpia(
        dpia_id=dpia_id,
        residual_risk="medium",
        approval_status="approved_with_conditions",
    )
    print("✅ 完成DPIA")

    # 生成報告
    report = dpia_mgr.generate_dpia_report(dpia_id)
    print("✅ 生成DPIA報告")

    print()


def example_5_compliance_monitoring():
    """示例5: 合規監控"""
    print("=" * 60)
    print("示例5: 合規監控")
    print("=" * 60)

    audit_logger = AuditLogger()
    monitor = ComplianceMonitor(audit_logger)

    # 運行合規檢查
    print("🔍 運行合規檢查...")
    results = monitor.run_all_checks()
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    print(f"   檢查完成: {passed}/{total} 通過")

    # 獲取合規評分
    gdpr_score = monitor.get_compliance_score("GDPR")
    print(f"\n📊 GDPR合規評分: {gdpr_score['compliance_score']:.2f}%")
    print(f"   合規檢查: {gdpr_score['compliant_checks']}/{gdpr_score['total_checks']}")
    print(f"   開放違規: {gdpr_score['open_violations']}")
    print(f"   高危違規: {gdpr_score['high_severity_violations']}")

    pdpa_score = monitor.get_compliance_score("PDPA")
    print(f"\n📊 PDPA合規評分: {pdpa_score['compliance_score']:.2f}%")
    print(f"   合規檢查: {pdpa_score['compliant_checks']}/{pdpa_score['total_checks']}")

    iso_score = monitor.get_compliance_score("ISO 27001")
    print(f"\n📊 ISO 27001合規評分: {iso_score['compliance_score']:.2f}%")
    print(f"   合規檢查: {iso_score['compliant_checks']}/{iso_score['total_checks']}")

    # 檢測異常
    anomalies = monitor.detect_anomalies()
    if anomalies:
        print(f"\n⚠️  檢測到 {len(anomalies)} 個異常:")
        for anomaly in anomalies:
            print(f"   - {anomaly['type']}: {anomaly['description']}")
    else:
        print("\n✅ 未檢測到異常")

    # 生成報告
    report = monitor.generate_compliance_report("GDPR")
    print("\n✅ 生成GDPR合規報告")

    print()


def example_6_integrated_security_system():
    """示例6: 集成安全系統"""
    print("=" * 60)
    print("示例6: 集成安全系統")
    print("=" * 60)

    # 初始化安全系統
    config = AuditConfig(
        audit_enabled=True,
        enable_encryption=True,
        gdpr_compliance=True,
        pdpa_compliance=True,
        iso27001_compliance=True,
    )
    security = SecuritySystem(config)

    # 記錄用戶登錄
    security.log_user_action(
        user_id="trader001",
        action="login",
        resource="auth / login",
        source_ip="192.168.1.100",
        details={"method": "password", "mfa": True},
    )
    print("✅ 記錄用戶登錄")

    # 記錄API調用
    security.log_api_call(
        method="GET",
        path="/api / portfolio",
        user_id="trader001",
        status_code=200,
        source_ip="192.168.1.100",
        details={"query": "summary"},
    )
    print("✅ 記錄API調用")

    # 記錄交易
    security.log_trade_execution(
        user_id="trader001",
        trade_id="TRD - 2024 - 001",
        symbol="0700.HK",
        action="BUY",
        quantity=1000,
        price=380.50,
    )
    print("✅ 記錄交易執行")

    # 創建安全事件
    incident_id = security.create_incident(
        title="檢測到異常交易模式",
        description="用戶在短時間內進行大量交易",
        incident_type="unusual_activity",
        severity="medium",
        reported_by="automated_detection",
        affected_systems=["trading_engine"],
        affected_data=["交易記錄"],
        indicators=["high_frequency", "large_volume", "rapid_succession"],
    )
    print(f"✅ 創建安全事件，ID: {incident_id}")

    # 運行合規檢查
    results = security.run_compliance_checks()
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    print(f"\n✅ 合規檢查: {passed}/{total} 通過")

    # 獲取合規評分
    scores = {
        "GDPR": security.get_compliance_score("GDPR"),
        "PDPA": security.get_compliance_score("PDPA"),
        "ISO 27001": security.get_compliance_score("ISO 27001"),
    }
    print("\n📊 合規評分:")
    for framework, score in scores.items():
        print(f"   {framework}: {score['compliance_score']:.2f}%")

    # 導出綜合報告
    report = security.export_all_reports()
    print("\n✅ 導出綜合報告:")
    print(f"   開放事件: {report['open_incidents']}")
    print(f"   DPIA數量: {report['dpias_count']}")
    print(f"   違規總數: {report['total_violations']}")
    print(f"   高危檢查: {report['high_risk_checks']}")

    # 驗證審計日誌完整性
    integrity = security.verify_audit_integrity()
    print("\n🔐 審計日誌完整性檢查:")
    print(f"   狀態: {integrity['status']}")
    print(f"   有效文件: {integrity['valid_files']}/{integrity['total_files']}")

    print()


def example_7_data_breach_response():
    """示例7: 數據洩露響應流程"""
    print("=" * 60)
    print("示例7: 數據洩露響應流程")
    print("=" * 60)

    audit_logger = AuditLogger()
    gdpr = GDPRManager(audit_logger)
    incident_mgr = IncidentManager(audit_logger)

    # 步驟1: 檢測數據洩露
    print("🔍 步驟1: 檢測到數據洩露")
    breach_id = gdpr.handle_data_breach(
        breach_type="unauthorized_access",
        affected_data=["客戶姓名", "交易記錄", "聯絡方式"],
        affected_subjects=["customer_001", "customer_002", "customer_003"],
        description="黑客攻擊導致數據庫被未授權訪問",
        mitigation_steps=[
            "立即封鎖攻擊源",
            "修補安全漏洞",
            "通知受影響客戶",
            "加強安全監控",
        ],
    )
    print(f"   事件ID: {breach_id}")

    # 步驟2: 報告安全事件
    print("\n🚨 步驟2: 報告安全事件")
    incident_id = incident_mgr.report_incident(
        title="數據庫未授權訪問",
        description="外部攻擊者未經授權訪問客戶數據",
        incident_type="data_breach",
        severity="critical",
        reported_by="security_team",
        affected_systems=["customer_db", "trading_db"],
        affected_data=["客戶個人信息", "交易記錄"],
        affected_individuals=3,
        indicators=["sql_injection", "data_exfiltration", "malicious_ip"],
    )
    print(f"   事件ID: {incident_id}")

    # 步驟3: 遏制
    print("\n🛡️  步驟3: 遏制事件")
    incident_mgr.update_incident_status(
        incident_id=incident_id,
        status="contained",
        actor="incident_commander",
        actions=["封鎖攻擊源IP", "修復SQL注入漏洞", "重置所有用戶密碼", "啟用額外監控"],
    )
    print("   狀態: 已遏制")

    # 步驟4: 根除
    print("\n🔧 步驟4: 根除威脅")
    incident_mgr.update_incident_status(
        incident_id=incident_id,
        status="eradicating",
        actor="security_team",
        actions=[
            "安裝安全補丁",
            "更新防火牆規則",
            "啟用Web應用防火牆",
            "部署入侵檢測系統",
        ],
    )
    print("   狀態: 根除中")

    # 步驟5: 恢復
    print("\n🔄 步驟5: 恢復系統")
    incident_mgr.update_incident_status(
        incident_id=incident_id,
        status="recovering",
        actor="operations_team",
        actions=["恢復數據庫服務", "驗證系統完整性", "監控異常活動", "恢復客戶服務"],
    )
    print("   狀態: 恢復中")

    # 步驟6: 解決
    print("\n✅ 步驟6: 解決事件")
    incident_mgr.update_incident_status(
        incident_id=incident_id,
        status="resolved",
        actor="incident_commander",
        actions=["完成系統驗證", "更新安全政策", "培訓相關人員", "撰寫事後報告"],
    )
    print("   狀態: 已解決")

    # 檢查GDPR通知要求
    print("\n📋 步驟7: 檢查通知要求")
    requirements = incident_mgr.check_notification_requirements(incident_id)
    print(f"   需要向監管機構報告: {requirements['gdpr_breach_notification']}")
    if requirements["gdpr_breach_notification"]:
        print(f"   通知截止時間: {requirements['deadline_72h']}")
    print(f"   需要通知數據主體: {requirements['data_subjects']}")
    if requirements["data_subjects"]:
        print(f"   通知截止時間: {requirements['deadline_30d']}")

    # 記錄教訓
    print("\n📝 步驟8: 記錄教訓")
    incident_mgr.add_timeline_entry(
        incident_id=incident_id,
        action="lessons_learned",
        description="已編制事後報告，總結事件原因、響應過程和改進措施",
        actor="incident_commander",
    )
    print("   已記錄教訓")

    print()


def main():
    """主函數"""
    print("\n" + "=" * 60)
    print("  港股量化交易系統 - 審計日誌與合規管理示例")
    print("=" * 60 + "\n")

    # 執行所有示例
    example_1_basic_audit_logging()
    example_2_gdpr_compliance()
    example_3_incident_response()
    example_4_dpia()
    example_5_compliance_monitoring()
    example_6_integrated_security_system()
    example_7_data_breach_response()

    print("=" * 60)
    print("  所有示例執行完成!")
    print("=" * 60 + "\n")

    print("📚 查看生成的日誌文件:")
    import os

    log_dir = "/c / Users / Penguin8n / CODEX--/logs / audit"
    if os.path.exists(log_dir):
        log_files = [f for f in os.listdir(log_dir) if f.endswith(".jsonl")]
        if log_files:
            print(f"   {log_dir}/")
            for log_file in log_files:
                file_path = os.path.join(log_dir, log_file)
                size = os.path.getsize(file_path)
                print(f"   - {log_file} ({size} bytes)")
        else:
            print("   (暫無日誌文件)")
    else:
        print("   (日誌目錄不存在)")


if __name__ == "__main__":
    main()
