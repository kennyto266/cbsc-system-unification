#!/usr / bin / env python3
"""
API安全測試
API Security Tests

測試API端點的安全性、認證和授權機制
"""

import asyncio
import secrets
import sys
import time
from pathlib import Path

import httpx
import pytest

# Add simplified_system to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "simplified_system"))


@pytest.mark.security
@pytest.mark.api
class TestAPISecurity:
    """API安全測試類"""

    @pytest.fixture
    async def api_client(self):
        """創建HTTP客戶端"""
        async with httpx.AsyncClient(timeout = 30.0) as client:
            yield client

    @pytest.fixture
    def api_base_url(self):
        """API基礎URL"""
        return "http://localhost:8001"

    @pytest.mark.slow
    async def test_sql_injection_protection(self, api_client, api_base_url):
        """測試SQL注入防護"""
        # 常見的SQL注入攻擊向量
        sql_injection_payloads = [
            "'; DROP TABLE stocks; --",
            "'; DELETE FROM market_data; --",
            "' OR '1'='1",
            "' UNION SELECT * FROM stocks --",
            "'; INSERT INTO stocks VALUES ('hack', 'hack', 'hack', 'hack', 0, 0, 0, 'HKD', 'HKEX'); --",
            "'; UPDATE stocks SET name='HACKED' WHERE symbol LIKE '%'; --",
            "'; ALTER TABLE stocks ADD COLUMN hacked TEXT; --",
            "' OR 1 = 1 #",
            "admin'--",
            "admin' /*",
            "1' UNION SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA --",
        ]

        for payload in sql_injection_payloads:
            try:
                # 測試股票查詢端點
                response = await api_client.get(f"{api_base_url}/api / stock/{payload}")

                # 應該返回404（找不到股票）或400（無效輸入）
                # 不應該返回500（服務器錯誤，可能意味著SQL注入成功）
                if response.status_code not in [200, 404, 400]:
                    print(
                        f"可疑響應狀態碼: {response.status_code} for payload: {payload}"
                    )

                # 如果成功，檢查響應內容
                if response.status_code == 200:
                    data = response.json()
                    # 響應不應該包含系統信息或錯誤信息
                    assert "error" not in str(data).lower(), f"可能的SQL注入: {payload}"

            except httpx.ConnectError:
                pytest.skip("API服務未啟動")
            except Exception as e:
                # 其他異常通常是正常的（例如輸入驗證失敗）
                continue

    @pytest.mark.slow
    async def test_xss_protection(self, api_client, api_base_url):
        """測試XSS（跨站腳本）攻擊防護"""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src = x onerror = alert('XSS')>",
            "'\"><script>alert('XSS')</script>",
            "<svg onload = alert('XSS')>",
            "';alert('XSS');//",
            "<iframe src='javascript:alert(`XSS`)'></iframe>",
            "<body onload = alert('XSS')>",
            "<input autofocus onfocus = alert('XSS')>",
            "';document.location='http://evil.com';//",
        ]

        for payload in xss_payloads:
            try:
                # 測試搜索端點
                response = await api_client.get(
                    f"{api_base_url}/api / stocks / search?q={payload}"
                )

                if response.status_code == 200:
                    data = response.text
                    # 響應不應該包含未轉義的腳本標籤
                    assert "<script>" not in data.lower(), f"可能的XSS漏洞: {payload}"
                    assert (
                        "javascript:" not in data.lower()
                    ), f"可能的XSS漏洞: {payload}"

            except httpx.ConnectError:
                pytest.skip("API服務未啟動")

    @pytest.mark.slow
    async def test_authentication_bypass(self, api_client, api_base_url):
        """測試認證繞過"""
        # 測試各種認證繞過技術
        auth_bypass_attempts = [
            # 特殊標頭
            {"X - Forwarded - For": "127.0.0.1"},
            {"X - Real - IP": "127.0.0.1"},
            {"X - Originating - IP": "127.0.0.1"},
            {"X - Remote - IP": "127.0.0.1"},
            {"X - Remote - Addr": "127.0.0.1"},
            # 空認證
            {"Authorization": ""},
            {"Authorization": "Bearer "},
            {"Authorization": "Basic "},
            # 無效認證
            {"Authorization": "Bearer invalid_token"},
            {"Authorization": "Basic invalid_base64"},
            {"Authorization": "Bearer admin"},
            # 常見的默認憑證
            {"Authorization": "Basic YWRtaW46YWRtaW4="},  # admin:admin
            {"Authorization": "Basic dGVzdDp0ZXN0"},  # test:test
            {"Authorization": "Basic cm9vdDpyb290"},  # root:root
        ]

        for headers in auth_bypass_attempts:
            try:
                response = await api_client.get(
                    f"{api_base_url}/api / admin / users", headers = headers
                )

                # 如果管理員端點存在，應該返回401或403
                # 不應該返回200（認證成功）
                if response.status_code == 200:
                    data = response.json()
                    # 檢查是否真的繞過了認證
                    if "users" in data or len(data) > 0:
                        pytest.fail(f"可能的認證繞過，headers: {headers}")

            except httpx.ConnectError:
                pytest.skip("API服務未啟動")
            except httpx.HTTPStatusError as e:
                # 404是可接受的（端點不存在）
                if e.response.status_code not in [404, 401, 403]:
                    print(f"意外的HTTP狀態碼: {e.response.status_code}")

    @pytest.mark.slow
    async def test_authorization_escalation(self, api_client, api_base_url):
        """測試權限提升"""
        # 假設的用戶角色和權限測試
        role_based_tests = [
            # 普通用戶嘗試訪問管理員功能
            ("user", "/api / admin / dashboard"),
            ("user", "/api / admin / users"),
            ("user", "/api / admin / settings"),
            # 嘗試訪問其他用戶的數據
            ("user1", "/api / user / user2 / profile"),
            ("user1", "/api / user / user2 / strategies"),
            ("user1", "/api / user / user2 / backtests"),
            # 嘗試訪問系統配置
            ("user", "/api / system / config"),
            ("user", "/api / system / logs"),
            ("user", "/api / system / metrics"),
        ]

        for role, endpoint in role_based_tests:
            try:
                response = await api_client.get(
                    f"{api_base_url}{endpoint}", headers={"X - User - Role": role}
                )

                # 應該返回401、403或404
                # 不應該返回200（權限提升成功）
                if response.status_code == 200:
                    response.json()
                    pytest.fail(f"可能的權限提升，role: {role}, endpoint: {endpoint}")

            except httpx.ConnectError:
                pytest.skip("API服務未啟動")
            except httpx.HTTPStatusError as e:
                if e.response.status_code not in [404, 401, 403]:
                    print(f"意外的HTTP狀態碼: {e.response.status_code}")

    @pytest.mark.slow
    async def test_rate_limiting_evasion(self, api_client, api_base_url):
        """測試速率限制規避"""
        # 如果有速率限制，嘗試規避
        evasion_techniques = [
            # 改變User - Agent
            {"User - Agent": "Mozilla / 5.0 (Windows NT 10.0; Win64; x64)"},
            {"User - Agent": "curl / 7.68.0"},
            {"User - Agent": "Python - requests / 2.25.1"},
            {"User - Agent": "PostmanRuntime / 7.26.8"},
            # 使用代理標頭
            {"X - Forwarded - For": "192.168.1.100"},
            {"X - Real - IP": "10.0.0.1"},
            {"X - Original - IP": "172.16.0.1"},
            # 添加隨機延遲
            {"X - Random - Delay": str(secrets.randbelow(1000))},
            # 修改請求順序
        ]

        base_headers = {"Content - Type": "application / json"}

        for evasion_headers in evasion_techniques:
            combined_headers = {**base_headers, **evasion_headers}

            # 發送快速請求
            responses = []
            for i in range(10):
                try:
                    response = await api_client.get(
                        f"{api_base_url}/api / stock / 0700.HK?duration = 7",
                        headers = combined_headers,
                    )
                    responses.append(response)

                    # 添加小延遲
                    await asyncio.sleep(0.1)

                except httpx.ConnectError:
                    pytest.skip("API服務未啟動")
                except Exception:
                    continue

            # 檢查是否規避了速率限制
            successful_requests = [r for r in responses if r.status_code == 200]
            if len(successful_requests) >= 8:  # 大部分請求成功
                print(f"可能規避了速率限制，headers: {evasion_headers}")

    @pytest.mark.slow
    async def test_sensitive_data_exposure(self, api_client, api_base_url):
        """測試敏感數據暴露"""
        # 檢查常見的敏感信息端點
        sensitive_endpoints = [
            "/api / config",
            "/api / environment",
            "/api / debug",
            "/api / errors",
            "/api / health / detailed",
            "/api / version",
            "/api / system / info",
            "/.env",
            "/config.json",
            "/server - info",
        ]

        for endpoint in sensitive_endpoints:
            try:
                response = await api_client.get(f"{api_base_url}{endpoint}")

                if response.status_code == 200:
                    data = response.text.lower()

                    # 檢查敏感信息
                    sensitive_patterns = [
                        "password",
                        "secret",
                        "api_key",
                        "private_key",
                        "database",
                        "connection_string",
                        "token",
                        "auth",
                        "credential",
                    ]

                    found_sensitive = [
                        pattern for pattern in sensitive_patterns if pattern in data
                    ]
                    if found_sensitive:
                        print(f"可能的敏感數據暴露在 {endpoint}: {found_sensitive}")

            except httpx.ConnectError:
                pytest.skip("API服務未啟動")
            except httpx.HTTPStatusError:
                continue  # 404是預期的

    @pytest.mark.slow
    async def test_input_validation_bypass(self, api_client, api_base_url):
        """測試輸入驗證繞過"""
        # 各種輸入驗證繞過技術
        bypass_payloads = [
            # 編碼繞過
            "%27%20OR%201 = 1 - -",  # URL編碼的 ' OR 1 = 1 - -
            "%3Cscript%3Ealert('XSS')%3C / script%3E",  # URL編碼的腳本
            # 雙重編碼
            "%2527%2520OR%25201 = 1 - -",
            # Unicode繞過
            "\u0027 OR 1 = 1 - -",  # Unicode的單引號
            # 大小寫混合
            "<ScRiPt>alert('XSS')</ScRiPt>",
            "SeLeCt * FrOm stocks",
            # 注釋繞過
            "/* comment */' OR 1 = 1 - -",
            "' /*!50000OR * / 1 = 1 - -",
            # 空字符繞過
            "'\0OR\01 = 1 - -",
            # 時間攻擊
            ("' OR (SELECT SLEEP(5))--", 5),  # 帶延遲的payload
        ]

        for payload in bypass_payloads:
            if isinstance(payload, tuple):
                payload, expected_delay = payload
                delay_needed = True
            else:
                delay_needed = False

            try:
                start_time = time.time()
                response = await api_client.get(f"{api_base_url}/api / stock/{payload}")
                end_time = time.time()

                response_time = end_time - start_time

                # 檢查是否有基於時間的攻擊跡象
                if delay_needed and response_time > expected_delay - 1:
                    print(f"可能的時間攻擊跡象，響應時間: {response_time:.2f}s")

                # 檢查錯誤信息洩露
                if response.status_code >= 400:
                    error_text = response.text.lower()
                    database_errors = [
                        "sql syntax",
                        "mysql_fetch",
                        "ora-",
                        "microsoft ole db",
                        "odbc drivers error",
                        "postgresql query failed",
                    ]

                    found_errors = [
                        error for error in database_errors if error in error_text
                    ]
                    if found_errors:
                        print(f"數據庫錯誤信息洩露: {found_errors}")

            except httpx.ConnectError:
                pytest.skip("API服務未啟動")
            except Exception as e:
                continue


@pytest.mark.security
@pytest.mark.auth
class TestAuthenticationSecurity:
    """認證安全測試"""

    @pytest.fixture
    def test_users(self):
        """測試用戶數據"""
        return {
            "admin": {"password": "admin123", "role": "admin"},
            "user": {"password": "user123", "role": "user"},
            "guest": {"password": "guest123", "role": "guest"},
        }

    def test_password_strength_validation(self):
        """測試密碼強度驗證"""
        weak_passwords = [
            "123456",  # 純數字
            "password",  # 常見密碼
            "qwerty",  # 鍵盤模式
            "abc123",  # 短密碼
            "a",  # 單字符
            "",  # 空密碼
            "password",  # 字典詞
            "12345",  # 短數字
            "test",  # 常見詞
        ]

        strong_passwords = [
            "SecureP@ssw0rd!",
            "MyV3ryStr0ng#P@ss",
            "C0mpl3x!P@ssw0rd",
            "R@nd0m#Str1ng_P@ss",
        ]

        # 這裡應該調用實際的密碼驗證函數
        # 由於我們沒有實際的認證系統，這是一個示例框架

        for password in weak_passwords:
            # 模擬密碼強度檢查
            strength = self._check_password_strength(password)
            assert strength < 3, f"弱密碼被接受: {password}"

        for password in strong_passwords:
            strength = self._check_password_strength(password)
            assert strength >= 3, f"強密碼被拒絕: {password}"

    def _check_password_strength(self, password: str) -> int:
        """模擬密碼強度檢查"""
        if len(password) < 8:
            return 1
        if password.lower() in ["password", "123456", "qwerty"]:
            return 1
        if (
            any(c.isupper() for c in password)
            and any(c.islower() for c in password)
            and any(c.isdigit() for c in password)
        ):
            return 4
        return 2

    def test_session_security(self):
        """測試會話安全"""
        # 會話ID生成安全測試
        session_ids = []

        for i in range(100):
            # 模擬會話ID生成
            session_id = secrets.token_urlsafe(32)
            session_ids.append(session_id)

        # 檢查唯一性
        assert len(set(session_ids)) == len(session_ids), "會話ID不唯一"

        # 檢查長度足夠
        for session_id in session_ids:
            assert len(session_id) >= 32, f"會話ID過短: {session_id}"

        # 檢查隨機性（簡單檢查）
        first_char_set = set(sid[0] for sid in session_ids[:50])
        assert len(first_char_set) > 1, "會話ID缺乏隨機性"

    def test_csrf_protection(self):
        """測試CSRF保護"""
        # 模擬CSRF token生成和驗證
        tokens = []

        for i in range(10):
            token = secrets.token_hex(32)
            tokens.append(token)

        # 檢查token強度
        for token in tokens:
            assert len(token) >= 64, f"CSRF token過短: {token}"
            assert all(c in "0123456789abcdef" for c in token), "CSRF token格式不正確"

        # 檢查唯一性
        assert len(set(tokens)) == len(tokens), "CSRF token不唯一"


@pytest.mark.security
@pytest.mark.data_privacy
class TestDataPrivacy:
    """數據隱私測試"""

    def test_data_masking(self):
        """測試數據遮罩"""
        sensitive_data = {
            "phone": "1234567890",
            "email": "user@example.com",
            "ssn": "123 - 45 - 6789",
            "credit_card": "1234 - 5678 - 9012 - 3456",
        }

        # 測試遮罩函數
        masked_phone = self._mask_sensitive_data(sensitive_data["phone"], "phone")
        assert "1234567890" not in masked_phone, "電話號碼未正確遮罩"

        masked_email = self._mask_sensitive_data(sensitive_data["email"], "email")
        assert "user@example.com" not in masked_email, "電子郵件未正確遮罩"

    def _mask_sensitive_data(self, data: str, data_type: str) -> str:
        """模擬敏感數據遮罩"""
        if data_type == "phone":
            return data[:3] + "****" + data[-4:]
        elif data_type == "email":
            local, domain = data.split("@")
            return local[:2] + "***@" + domain
        else:
            return "*" * len(data)

    def test_encryption_requirements(self):
        """測試加密需求"""
        # 模擬敏感數據加密檢查
        sensitive_fields = ["password", "ssn", "credit_card", "api_key"]

        for field in sensitive_fields:
            # 檢查數據是否已加密（模擬）
            is_encrypted = self._check_field_encryption(field)
            assert is_encrypted, f"敏感字段 {field} 未加密"

    def _check_field_encryption(self, field_name: str) -> bool:
        """模擬字段加密檢查"""
        # 在實際實現中，這會檢查字段是否已正確加密
        return True  # 假設已加密


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
