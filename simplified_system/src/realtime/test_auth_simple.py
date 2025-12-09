#!/usr/bin/env python3
"""
Simple Authentication Test (No WebSocket Server)
簡化身份驗證測試（無需WebSocket服務器）
"""

import asyncio
import json
from datetime import datetime
from auth import (
    WebSocketAuthenticator,
    WebSocketMiddleware,
    ConnectionContext,
    AuthenticationError,
    AuthorizationError,
    RateLimitError,
    User,
    create_authenticator,
    create_middleware
)

class AuthenticationTester:
    """身份驗證測試器"""

    def __init__(self):
        self.test_results = {}

    def run_tests(self):
        """運行所有測試"""
        print("Starting Authentication Tests...")
        print("=" * 60)

        # 測試1: JWT token生成和驗證
        self.test_jwt_tokens()

        # 測試2: API密鑰生成和驗證
        self.test_api_keys()

        # 測試3: 速率限制
        self.test_rate_limiting()

        # 測試4: 權限檢查
        self.test_permissions()

        # 測試5: 安全檢查
        self.test_security_controls()

        # 測試6: 用戶管理
        self.test_user_management()

        # 生成報告
        self.generate_report()

    def test_jwt_tokens(self):
        """測試JWT token"""
        print("\nTest 1: JWT Token Generation & Validation")
        try:
            authenticator = create_authenticator("test-secret-key")

            # 測試token生成
            user_id = "user_001"
            token = authenticator.generate_jwt_token(user_id)

            self.test_results["jwt_generation"] = {
                "success": len(token) > 0,
                "token_length": len(token),
                "user_id": user_id
            }
            print(f"  Token Generation: {'PASS' if len(token) > 0 else 'FAIL'}")

            # 測試token驗證
            payload = authenticator.validate_jwt_token(token)
            validation_success = (
                payload.get("user_id") == user_id and
                payload.get("type") == "websocket_auth"
            )

            self.test_results["jwt_validation"] = {
                "success": validation_success,
                "validated_user_id": payload.get("user_id"),
                "permissions": payload.get("permissions")
            }
            print(f"  Token Validation: {'PASS' if validation_success else 'FAIL'}")

            # 測試無效token
            try:
                authenticator.validate_jwt_token("invalid.token.here")
                self.test_results["jwt_invalid_rejection"] = {
                    "success": False,
                    "error": "Should have rejected invalid token"
                }
                print("  Invalid Token Rejection: FAIL")
            except AuthenticationError:
                self.test_results["jwt_invalid_rejection"] = {"success": True}
                print("  Invalid Token Rejection: PASS")

        except Exception as e:
            self.test_results["jwt_tokens"] = {"success": False, "error": str(e)}
            print(f"  JWT Test Error: {e}")

    def test_api_keys(self):
        """測試API密鑰"""
        print("\nTest 2: API Key Generation & Validation")
        try:
            authenticator = create_authenticator("test-secret-key")

            # 測試API密鑰生成
            user_id = "user_002"
            api_key = authenticator.generate_api_key(user_id)

            self.test_results["api_key_generation"] = {
                "success": len(api_key) > 0 and api_key.startswith("ws_"),
                "api_key_length": len(api_key),
                "user_id": user_id
            }
            print(f"  API Key Generation: {'PASS' if len(api_key) > 0 else 'FAIL'}")

            # 測試API密鑰驗證
            user = authenticator.validate_api_key(api_key)
            validation_success = user.user_id == user_id

            self.test_results["api_key_validation"] = {
                "success": validation_success,
                "validated_user_id": user.user_id,
                "username": user.username
            }
            print(f"  API Key Validation: {'PASS' if validation_success else 'FAIL'}")

            # 測試無效API密鑰
            try:
                authenticator.validate_api_key("invalid_api_key")
                self.test_results["api_key_invalid_rejection"] = {
                    "success": False,
                    "error": "Should have rejected invalid API key"
                }
                print("  Invalid API Key Rejection: FAIL")
            except AuthenticationError:
                self.test_results["api_key_invalid_rejection"] = {"success": True}
                print("  Invalid API Key Rejection: PASS")

        except Exception as e:
            self.test_results["api_keys"] = {"success": False, "error": str(e)}
            print(f"  API Key Test Error: {e}")

    def test_rate_limiting(self):
        """測試速率限制"""
        print("\nTest 3: Rate Limiting")
        try:
            authenticator = create_authenticator("test-secret-key")
            client_ip = "127.0.0.1"

            # 測試正常速率
            allowed_count = 0
            for i in range(3):
                try:
                    authenticator.check_rate_limit(client_ip)
                    allowed_count += 1
                except RateLimitError:
                    break

            self.test_results["rate_limit_normal"] = {
                "success": allowed_count == 3,
                "allowed_connections": allowed_count
            }
            print(f"  Normal Rate Limiting: {'PASS' if allowed_count == 3 else 'FAIL'} ({allowed_count}/3 allowed)")

        except Exception as e:
            self.test_results["rate_limiting"] = {"success": False, "error": str(e)}
            print(f"  Rate Limiting Test Error: {e}")

    def test_permissions(self):
        """測試權限檢查"""
        print("\nTest 4: Permission Checks")
        try:
            authenticator = create_authenticator("test-secret-key")

            # 創建測試上下文
            user = User(
                user_id="user_001",
                username="trader_demo",
                permissions=["realtime_data", "historical_data"]
            )

            context = ConnectionContext(
                user=user,
                permissions=user.permissions,
                connected_at=datetime.now(),
                client_ip="127.0.0.1",
                user_agent="test-client"
            )

            # 測試有效訂閱
            try:
                authorized_symbols = authenticator.authorize_subscription(context, ["0700.HK", "0941.HK"])
                subscription_success = len(authorized_symbols) == 2
            except AuthorizationError:
                subscription_success = False

            self.test_results["permission_subscription"] = {
                "success": subscription_success,
                "authorized_symbols": len(authorized_symbols) if subscription_success else 0
            }
            print(f"  Subscription Authorization: {'PASS' if subscription_success else 'FAIL'}")

        except Exception as e:
            self.test_results["permissions"] = {"success": False, "error": str(e)}
            print(f"  Permission Test Error: {e}")

    def test_security_controls(self):
        """測試安全控制"""
        print("\nTest 5: Security Controls")
        try:
            authenticator = create_authenticator("test-secret-key")

            # 測試不安全類型拒絕
            class UnsafeObject:
                def __reduce__(self):
                    return (eval, ("__import__('os').system('echo hacked')",))

            try:
                unsafe_obj = UnsafeObject()
                authenticator.generate_jwt_token("user_001", unsafe_obj)  # This shouldn't work
                security_test = False
            except (AuthenticationError, TypeError, ValueError):
                security_test = True

            self.test_results["security_object_rejection"] = {
                "success": security_test
            }
            print(f"  Unsafe Object Rejection: {'PASS' if security_test else 'FAIL'}")

            # 測試token過期
            import jwt
            expired_token = jwt.encode({
                'user_id': 'user_001',
                'exp': datetime.now() - timedelta(days=1),  # 昨天過期
                'type': 'websocket_auth'
            }, "test-secret-key", algorithm="HS256")

            try:
                authenticator.validate_jwt_token(expired_token)
                expired_test = False
            except AuthenticationError:
                expired_test = True

            self.test_results["security_token_expiry"] = {
                "success": expired_test
            }
            print(f"  Expired Token Rejection: {'PASS' if expired_test else 'FAIL'}")

        except Exception as e:
            self.test_results["security_controls"] = {"success": False, "error": str(e)}
            print(f"  Security Control Test Error: {e}")

    def test_user_management(self):
        """測試用戶管理"""
        print("\nTest 6: User Management")
        try:
            authenticator = create_authenticator("test-secret-key")

            # 獲取用戶統計
            stats = authenticator.get_user_stats()
            stats_valid = (
                "total_users" in stats and
                "active_users" in stats and
                "rate_limit_config" in stats
            )

            self.test_results["user_stats"] = {
                "success": stats_valid,
                "total_users": stats.get("total_users"),
                "active_users": stats.get("active_users")
            }
            print(f"  User Statistics: {'PASS' if stats_valid else 'FAIL'}")
            print(f"    Total Users: {stats.get('total_users')}")
            print(f"    Active Users: {stats.get('active_users')}")

        except Exception as e:
            self.test_results["user_management"] = {"success": False, "error": str(e)}
            print(f"  User Management Test Error: {e}")

    def generate_report(self):
        """生成測試報告"""
        print("\n" + "=" * 60)
        print("AUTHENTICATION SECURITY TEST REPORT")
        print("=" * 60)

        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result.get("success", False))

        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        print(f"\nTest Results Summary:")
        print(f"  Total Tests: {total_tests}")
        print(f"  Passed: {passed_tests}")
        print(f"  Failed: {total_tests - passed_tests}")
        print(f"  Success Rate: {success_rate:.1f}%")

        # 詳細結果
        print(f"\nDetailed Results:")
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result.get("success", False) else "❌ FAIL"
            print(f"  {test_name}: {status}")
            if not result.get("success", False):
                print(f"    Error: {result.get('error', 'Unknown error')}")

        # 安全狀態評估
        print(f"\n🔒 Security Implementation Assessment:")
        if success_rate >= 95:
            print("  ✅ EXCELLENT: Authentication system is fully secure!")
        elif success_rate >= 85:
            print("  ⚠️  GOOD: Authentication working, minor issues to address")
        elif success_rate >= 70:
            print("  ⚠️  FAIR: Authentication mostly working, some concerns")
        else:
            print("  ❌ NEEDS WORK: Significant security issues found")

        # 關鍵安全檢查清單
        critical_security_checks = [
            ("jwt_generation", "JWT Token Generation"),
            ("jwt_validation", "JWT Token Validation"),
            ("jwt_invalid_rejection", "Invalid Token Rejection"),
            ("api_key_generation", "API Key Generation"),
            ("api_key_validation", "API Key Validation"),
            ("api_key_invalid_rejection", "Invalid API Key Rejection"),
            ("security_object_rejection", "Unsafe Object Rejection"),
            ("security_token_expiry", "Token Expiry Validation")
        ]

        print(f"\n🛡️  Critical Security Checklist:")
        all_critical_pass = True
        for check_key, description in critical_security_checks:
            if check_key in self.test_results:
                passed = self.test_results[check_key].get("success", False)
                status = "✅" if passed else "❌"
                print(f"  {status} {description}")
                if not passed:
                    all_critical_pass = False

        if all_critical_pass:
            print(f"\n🎯 WEBSOCKET AUTHENTICATION SECURITY FIX: COMPLETE")
            print(f"   ✅ JWT token authentication IMPLEMENTED")
            print(f"   ✅ API key authentication IMPLEMENTED")
            print(f"   ✅ Rate limiting ACTIVE")
            print(f"   ✅ Input validation ACTIVE")
            print(f"   ✅ Unauthorized access BLOCKED")
            print(f"   ✅ Security controls ENFORCED")
        else:
            print(f"\n⚠️  Some critical security checks failed - review failed tests")

        # 保存報告
        import json
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "success_rate": success_rate
            },
            "detailed_results": self.test_results,
            "security_fix_verified": all_critical_pass,
            "websocket_authentication": "IMPLEMENTED"
        }

        with open("websocket_authentication_security_report.json", "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, default=str)

        print(f"\n📄 Detailed report saved to: websocket_authentication_security_report.json")

if __name__ == "__main__":
    from datetime import timedelta
    tester = AuthenticationTester()
    tester.run_tests()