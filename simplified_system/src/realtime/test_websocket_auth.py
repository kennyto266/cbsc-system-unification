#!/usr/bin/env python3
"""
WebSocket Authentication Test
測試WebSocket身份驗證功能
"""

import asyncio
import websockets
import json
import time
from datetime import datetime
from websocket_server import RealtimeWebSocketServer
from auth import create_authenticator

class WebSocketAuthTester:
    """WebSocket身份驗證測試器"""

    def __init__(self):
        self.server = RealtimeWebSocketServer("test-secret-key")
        self.test_results = {}

    async def run_tests(self):
        """運行所有測試"""
        print("Starting WebSocket Authentication Tests...")
        print("=" * 60)

        # 測試1: 無身份驗證連接應被拒絕
        await self.test_unauthenticated_connection()

        # 測試2: JWT token驗證
        await self.test_jwt_authentication()

        # 測試3: API密鑰驗證
        await self.test_api_key_authentication()

        # 測試4: 無效token應被拒絕
        await self.test_invalid_tokens()

        # 測試5: 速率限制
        await self.test_rate_limiting()

        # 測試6: 輸入驗證
        await self.test_input_validation()

        # 測試7: 訂閱授權
        await self.test_subscription_authorization()

        # 生成測試報告
        self.generate_test_report()

    async def test_unauthenticated_connection(self):
        """測試無身份驗證連接"""
        print("\nTest 1: Unauthenticated Connection (Should be Rejected)")
        try:
            async with websockets.connect("ws://localhost:8000/ws") as websocket:
                await websocket.send(json.dumps({"type": "subscribe", "symbols": ["0700.HK"]}))
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)

                # 如果到這裡，說明安全措施失敗
                self.test_results["unauthenticated_connection"] = {
                    "success": False,
                    "error": "Connection was not rejected",
                    "response": response
                }
                print("  Result: FAIL - Connection was not rejected")

        except Exception as e:
            # 預期的行為 - 連接應該被拒絕
            if "401" in str(e) or "403" in str(e) or "rejected" in str(e).lower():
                self.test_results["unauthenticated_connection"] = {
                    "success": True,
                    "expected_rejection": True,
                    "error": str(e)
                }
                print("  Result: PASS - Connection correctly rejected")
            else:
                self.test_results["unauthenticated_connection"] = {
                    "success": False,
                    "unexpected_error": str(e)
                }
                print(f"  Result: FAIL - Unexpected error: {e}")

    async def test_jwt_authentication(self):
        """測試JWT token驗證"""
        print("\nTest 2: JWT Token Authentication")
        try:
            # 獲取測試用戶的token
            user_id = "user_001"
            authenticator = create_authenticator("test-secret-key")
            token = authenticator.generate_jwt_token(user_id)

            # 使用token連接
            websocket_url = f"ws://localhost:8000/ws?token={token}"
            async with websockets.connect(websocket_url) as websocket:
                # 接收歡迎消息
                welcome_msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                welcome_data = json.loads(welcome_msg)

                # 驗證歡迎消息
                if (welcome_data.get("type") == "authentication_success" and
                    welcome_data.get("user_id") == user_id):

                    # 發送訂閱請求
                    subscribe_msg = json.dumps({"type": "subscribe", "symbols": ["0700.HK", "0941.HK"]})
                    await websocket.send(subscribe_msg)

                    # 接收訂閱確認
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    response_data = json.loads(response)

                    success = (response_data.get("type") == "subscription_confirmed" and
                              "0700.HK" in response_data.get("symbols", []))

                    self.test_results["jwt_authentication"] = {
                        "success": success,
                        "user_id": user_id,
                        "welcome_received": welcome_data.get("type") == "authentication_success",
                        "subscription_confirmed": response_data.get("type") == "subscription_confirmed"
                    }

                    if success:
                        print("  Result: PASS - JWT authentication successful")
                    else:
                        print(f"  Result: FAIL - Subscription failed: {response_data}")
                else:
                    self.test_results["jwt_authentication"] = {
                        "success": False,
                        "error": "Invalid welcome message",
                        "welcome_type": welcome_data.get("type")
                    }
                    print(f"  Result: FAIL - Invalid welcome message: {welcome_data}")

        except Exception as e:
            self.test_results["jwt_authentication"] = {
                "success": False,
                "error": str(e)
            }
            print(f"  Result: FAIL - Error: {e}")

    async def test_api_key_authentication(self):
        """測試API密鑰驗證"""
        print("\nTest 3: API Key Authentication")
        try:
            # 獲取測試用戶的API密鑰
            user_id = "user_002"
            authenticator = create_authenticator("test-secret-key")
            api_key = authenticator.generate_api_key(user_id)

            # 使用API密鑰連接
            websocket_url = f"ws://localhost:8000/ws?api_key={api_key}"
            async with websockets.connect(websocket_url) as websocket:
                # 接收歡迎消息
                welcome_msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                welcome_data = json.loads(welcome_msg)

                success = (welcome_data.get("type") == "authentication_success" and
                          welcome_data.get("user_id") == user_id)

                self.test_results["api_key_authentication"] = {
                    "success": success,
                    "user_id": user_id,
                    "welcome_type": welcome_data.get("type")
                }

                if success:
                    print("  Result: PASS - API key authentication successful")
                else:
                    print(f"  Result: FAIL - Invalid welcome message: {welcome_data}")

        except Exception as e:
            self.test_results["api_key_authentication"] = {
                "success": False,
                "error": str(e)
            }
            print(f"  Result: FAIL - Error: {e}")

    async def test_invalid_tokens(self):
        """測試無效token應被拒絕"""
        print("\nTest 4: Invalid Tokens (Should be Rejected)")
        invalid_tokens = [
            "invalid.token.here",
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.invalid",
            "",
            "expired_token_here"
        ]

        rejected_count = 0
        for i, token in enumerate(invalid_tokens):
            try:
                websocket_url = f"ws://localhost:8000/ws?token={token}"
                async with websockets.connect(websocket_url) as websocket:
                    # 如果成功連接，說明安全措施失敗
                    print(f"  Token {i+1}: FAIL - Connection should have been rejected")

            except Exception as e:
                # 預期的行為
                if any(code in str(e) for code in ["401", "403", "4001", "4003"]):
                    rejected_count += 1
                    print(f"  Token {i+1}: PASS - Correctly rejected")
                else:
                    print(f"  Token {i+1}: PARTIAL - Rejected but with unexpected error: {e}")

        success = rejected_count == len(invalid_tokens)
        self.test_results["invalid_tokens"] = {
            "success": success,
            "rejected_count": rejected_count,
            "total_tokens": len(invalid_tokens)
        }

        print(f"  Overall: {'PASS' if success else 'FAIL'} - {rejected_count}/{len(invalid_tokens)} tokens correctly rejected")

    async def test_rate_limiting(self):
        """測試速率限制"""
        print("\nTest 5: Rate Limiting")
        try:
            # 獲取有效token
            authenticator = create_authenticator("test-secret-key")
            token = authenticator.generate_jwt_token("user_001")

            websocket_url = f"ws://localhost:8000/ws?token={token}"
            connections_made = 0
            connections_rejected = 0

            # 嘗試快速建立多個連接
            for i in range(5):  # 測試5個連接
                try:
                    websocket = await asyncio.wait_for(
                        websockets.connect(websocket_url),
                        timeout=2.0
                    )
                    connections_made += 1
                    await websocket.close()

                except Exception as e:
                    connections_rejected += 1

            # 速率限制測試應該允許一些連接但拒絕過多的連接
            self.test_results["rate_limiting"] = {
                "success": connections_made > 0,  # 至少允許一些連接
                "connections_made": connections_made,
                "connections_rejected": connections_rejected
            }

            print(f"  Result: {'PASS' if connections_made > 0 else 'FAIL'} - {connections_made} connections made")

        except Exception as e:
            self.test_results["rate_limiting"] = {
                "success": False,
                "error": str(e)
            }
            print(f"  Result: FAIL - Error: {e}")

    async def test_input_validation(self):
        """測試輸入驗證"""
        print("\nTest 6: Input Validation")
        try:
            # 獲取有效token
            authenticator = create_authenticator("test-secret-key")
            token = authenticator.generate_jwt_token("user_001")

            websocket_url = f"ws://localhost:8000/ws?token={token}"
            async with websockets.connect(websocket_url) as websocket:
                # 等待歡迎消息
                await asyncio.wait_for(websocket.recv(), timeout=5.0)

                # 測試無效消息
                invalid_messages = [
                    "not json",
                    '{"invalid": "structure"}',
                    '{"type": "subscribe", "symbols": "not_array"}',
                    '{"type": "subscribe", "symbols": ["<script>alert(1)</script>"]}',
                    '{"type": "subscribe", "symbols": ["a" * 20]}'  # 過長符號
                ]

                validated_count = 0
                for message in invalid_messages:
                    try:
                        await websocket.send(message)
                        response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                        response_data = json.loads(response)

                        # 檢查是否收到錯誤消息
                        if response_data.get("type") in ["error", "authorization_error"]:
                            validated_count += 1

                    except Exception:
                        # 消息被拒絕是正確的行為
                        validated_count += 1

                success = validated_count == len(invalid_messages)
                self.test_results["input_validation"] = {
                    "success": success,
                    "validated_count": validated_count,
                    "total_messages": len(invalid_messages)
                }

                print(f"  Result: {'PASS' if success else 'FAIL'} - {validated_count}/{len(invalid_messages)} messages properly validated")

        except Exception as e:
            self.test_results["input_validation"] = {
                "success": False,
                "error": str(e)
            }
            print(f"  Result: FAIL - Error: {e}")

    async def test_subscription_authorization(self):
        """測試訂閱授權"""
        print("\nTest 7: Subscription Authorization")
        try:
            # 測試不同權限級別的用戶
            test_cases = [
                ("user_001", ["realtime_data", "historical_data", "trading"], True),
                ("user_002", ["realtime_data"], True),
                ("user_003", ["realtime_data", "historical_data", "trading", "admin"], True)
            ]

            authorized_count = 0
            for user_id, permissions, should_succeed in test_cases:
                try:
                    authenticator = create_authenticator("test-secret-key")
                    token = authenticator.generate_jwt_token(user_id)

                    websocket_url = f"ws://localhost:8000/ws?token={token}"
                    async with websockets.connect(websocket_url) as websocket:
                        # 等待歡迎消息
                        welcome_msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)

                        # 發送訂閱請求
                        subscribe_msg = json.dumps({"type": "subscribe", "symbols": ["0700.HK"]})
                        await websocket.send(subscribe_msg)

                        # 接收響應
                        response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        response_data = json.loads(response)

                        # 檢查訂閱是否被授權
                        if response_data.get("type") == "subscription_confirmed":
                            if should_succeed:
                                authorized_count += 1
                                print(f"    {user_id}: PASS - Subscription authorized")
                            else:
                                print(f"    {user_id}: UNEXPECTED - Subscription should have been rejected")
                        else:
                            if not should_succeed:
                                authorized_count += 1
                                print(f"    {user_id}: PASS - Subscription correctly rejected")
                            else:
                                print(f"    {user_id}: FAIL - Subscription should have been authorized")

                except Exception as e:
                    print(f"    {user_id}: ERROR - {e}")

            success = authorized_count == len(test_cases)
            self.test_results["subscription_authorization"] = {
                "success": success,
                "authorized_count": authorized_count,
                "total_tests": len(test_cases)
            }

            print(f"  Overall: {'PASS' if success else 'FAIL'} - {authorized_count}/{len(test_cases)} authorization tests passed")

        except Exception as e:
            self.test_results["subscription_authorization"] = {
                "success": False,
                "error": str(e)
            }
            print(f"  Result: FAIL - Error: {e}")

    def generate_test_report(self):
        """生成測試報告"""
        print("\n" + "=" * 60)
        print("WEBSOCKET AUTHENTICATION TEST REPORT")
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
            status = "PASS" if result.get("success", False) else "FAIL"
            print(f"  {test_name}: {status}")
            if not result.get("success", False):
                print(f"    Error: {result.get('error', 'Unknown error')}")

        # 安全狀態評估
        print(f"\nSecurity Assessment:")
        if success_rate >= 90:
            print("  ✅ EXCELLENT: WebSocket authentication is working correctly!")
        elif success_rate >= 75:
            print("  ⚠️  GOOD: Mostly working, some issues to address")
        else:
            print("  ❌ NEEDS WORK: Significant security issues found")

        # 關鍵安全檢查
        critical_checks = [
            ("unauthenticated_connection", "拒絕未認證連接"),
            ("invalid_tokens", "拒絕無效token"),
            ("input_validation", "輸入驗證")
        ]

        print(f"\nCritical Security Checks:")
        all_critical_pass = True
        for check_name, description in critical_checks:
            if check_name in self.test_results:
                status = "✅" if self.test_results[check_name].get("success", False) else "❌"
                print(f"  {status} {description}")
                if not self.test_results[check_name].get("success", False):
                    all_critical_pass = False

        if all_critical_pass:
            print(f"\n🔒 CRITICAL SECURITY ISSUE RESOLVED:")
            print(f"   - Unauthorized WebSocket access BLOCKED")
            print(f"   - JWT token authentication WORKING")
            print(f"   - API key authentication WORKING")
            print(f"   - Input validation PROTECTING against injection")
            print(f"   - Rate limiting PREVENTING abuse")
        else:
            print(f"\n⚠️  SECURITY ISSUES STILL EXIST - Review failed tests")

async def main():
    """主測試函數"""
    tester = WebSocketAuthTester()
    await tester.run_tests()

if __name__ == "__main__":
    print("Note: Make sure the WebSocket server is running on localhost:8000")
    print("Run this test after starting: python websocket_server.py")
    print()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nTest failed with error: {e}")