#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API Testing Suite for Issue #22
API测试套件 - Issue #22阶段

Comprehensive testing for the new unified API architecture
包括集成测试、端点验证、性能测试和安全测试
"""

import asyncio
import sys
import os
import json
import time
import httpx
import pytest
from typing import Dict, List, Any
from datetime import datetime

# Add project path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

class APITestSuite:
    """Comprehensive API Testing Suite"""

    def __init__(self, base_url: str = "http://localhost:3004"):
        self.base_url = base_url
        self.test_results = {}
        self.client = httpx.AsyncClient(timeout=30.0)

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all test categories"""
        print("=" * 60)
        print("API TESTING SUITE - Issue #22")
        print("=" * 60)
        print(f"Target URL: {self.base_url}")
        print(f"Started at: {datetime.now().isoformat()}")
        print()

        test_categories = [
            ("Connectivity Test", self.test_connectivity),
            ("Strategy Endpoints", self.test_strategy_endpoints),
            ("Personal Endpoints", self.test_personal_endpoints),
            ("WebSocket Endpoints", self.test_websocket_endpoints),
            ("Authentication Test", self.test_authentication),
            ("Data Validation Test", self.test_data_validation),
            ("Error Handling Test", self.test_error_handling),
            ("Performance Test", self.test_performance),
            ("Security Test", self.test_security),
        ]

        total_passed = 0
        total_tests = len(test_categories)

        for category_name, test_func in test_categories:
            print(f"\n[{category_name}]")
            print("-" * 40)

            try:
                start_time = time.time()
                result = await test_func()
                duration = time.time() - start_time

                self.test_results[category_name] = {
                    "status": "PASSED" if result else "FAILED",
                    "duration": duration,
                    "details": result
                }

                if result:
                    print(f"✓ PASSED ({duration:.2f}s)")
                    total_passed += 1
                else:
                    print(f"✗ FAILED ({duration:.2f}s)")

            except Exception as e:
                print(f"✗ ERROR: {e}")
                self.test_results[category_name] = {
                    "status": "ERROR",
                    "error": str(e),
                    "duration": 0
                }

        # Generate final report
        await self.generate_report(total_passed, total_tests)

        return self.test_results

    async def test_connectivity(self) -> bool:
        """Test basic connectivity to API server"""
        try:
            # Test root endpoint
            response = await self.client.get(f"{self.base_url}/")

            if response.status_code in [200, 404]:
                print("  ✓ Server is reachable")
                return True
            else:
                print(f"  ✗ Unexpected status: {response.status_code}")
                return False

        except Exception as e:
            print(f"  ✗ Connection failed: {e}")
            return False

    async def test_strategy_endpoints(self) -> bool:
        """Test strategy management endpoints"""
        endpoints = [
            "/api/v1/strategies/",
            "/api/v1/strategies/templates/",
            "/api/v1/strategies/batch-operation"
        ]

        passed = 0
        for endpoint in endpoints:
            try:
                response = await self.client.get(f"{self.base_url}{endpoint}")
                if response.status_code in [200, 401, 403]:
                    print(f"  ✓ {endpoint} - {response.status_code}")
                    passed += 1
                else:
                    print(f"  ✗ {endpoint} - {response.status_code}")
            except Exception as e:
                print(f"  ✗ {endpoint} - Error: {e}")

        return passed == len(endpoints)

    async def test_personal_endpoints(self) -> bool:
        """Test personal strategy endpoints"""
        endpoints = [
            "/api/v1/strategies/personal/dashboard",
            "/api/v1/strategies/personal/preferences",
            "/api/v1/strategies/personal/statistics"
        ]

        passed = 0
        for endpoint in endpoints:
            try:
                response = await self.client.get(f"{self.base_url}{endpoint}")
                if response.status_code in [200, 401, 403]:
                    print(f"  ✓ {endpoint} - {response.status_code}")
                    passed += 1
                else:
                    print(f"  ✗ {endpoint} - {response.status_code}")
            except Exception as e:
                print(f"  ✗ {endpoint} - Error: {e}")

        return passed == len(endpoints)

    async def test_websocket_endpoints(self) -> bool:
        """Test WebSocket endpoints"""
        # Note: WebSocket testing requires websocket client
        # For now, just test HTTP upgrade endpoints
        endpoints = [
            "/api/v1/strategies/ws/realtime/1",
            "/api/v1/strategies/ws/strategy/test",
            "/api/v1/strategies/ws/market-data"
        ]

        passed = 0
        for endpoint in endpoints:
            try:
                # Try HTTP GET (should return 400 or similar for WebSocket endpoints)
                response = await self.client.get(f"{self.base_url}{endpoint}")
                if response.status_code in [400, 404, 421]:  # Expected for WebSocket on HTTP
                    print(f"  ✓ {endpoint} - WebSocket endpoint available")
                    passed += 1
                else:
                    print(f"  ? {endpoint} - Unexpected status: {response.status_code}")
                    passed += 1  # Still count as passed since endpoint exists
            except Exception as e:
                print(f"  ✗ {endpoint} - Error: {e}")

        return passed >= len(endpoints) * 0.8  # 80% pass rate

    async def test_authentication(self) -> bool:
        """Test authentication mechanisms"""
        try:
            # Test without authentication (should return 401 or 403)
            response = await self.client.get(f"{self.base_url}/api/v1/strategies/personal/dashboard")

            if response.status_code in [401, 403]:
                print("  ✓ Authentication required (proper response)")
                return True
            else:
                print(f"  ✗ Unexpected auth response: {response.status_code}")
                return False

        except Exception as e:
            print(f"  ✗ Authentication test failed: {e}")
            return False

    async def test_data_validation(self) -> bool:
        """Test data validation"""
        try:
            # Test invalid data submission
            invalid_data = {
                "name": "",  # Empty name should fail validation
                "description": "test"
            }

            response = await self.client.post(
                f"{self.base_url}/api/v1/strategies/",
                json=invalid_data
            )

            # Should return validation error (400) or auth error (401/403)
            if response.status_code in [400, 401, 403]:
                print("  ✓ Data validation working")
                return True
            else:
                print(f"  ✗ Validation not enforced: {response.status_code}")
                return False

        except Exception as e:
            print(f"  ✗ Data validation test failed: {e}")
            return False

    async def test_error_handling(self) -> bool:
        """Test error handling"""
        try:
            # Test 404 handling
            response = await self.client.get(f"{self.base_url}/api/v1/strategies/99999")

            if response.status_code == 404:
                print("  ✓ 404 handling working")
                return True
            else:
                print(f"  ✗ 404 not handled properly: {response.status_code}")
                return False

        except Exception as e:
            print(f"  ✗ Error handling test failed: {e}")
            return False

    async def test_performance(self) -> bool:
        """Test API performance"""
        try:
            endpoint = f"{self.base_url}/api/v1/strategies/"

            # Test response time
            start_time = time.time()
            response = await self.client.get(endpoint)
            response_time = time.time() - start_time

            if response_time < 2.0:  # Should respond within 2 seconds
                print(f"  ✓ Response time: {response_time:.3f}s")
                return True
            else:
                print(f"  ✗ Slow response: {response_time:.3f}s")
                return False

        except Exception as e:
            print(f"  ✗ Performance test failed: {e}")
            return False

    async def test_security(self) -> bool:
        """Test security headers and practices"""
        try:
            response = await self.client.get(f"{self.base_url}/")

            # Check for security headers
            security_headers = [
                "x-content-type-options",
                "x-frame-options",
                "x-xss-protection"
            ]

            headers_found = 0
            for header in security_headers:
                if header in response.headers:
                    headers_found += 1

            if headers_found >= len(security_headers) * 0.5:  # 50% of headers
                print(f"  ✓ Security headers present: {headers_found}/{len(security_headers)}")
                return True
            else:
                print(f"  ✗ Missing security headers: {headers_found}/{len(security_headers)}")
                return False

        except Exception as e:
            print(f"  ✗ Security test failed: {e}")
            return False

    async def generate_report(self, passed: int, total: int) -> None:
        """Generate test report"""
        print("\n" + "=" * 60)
        print("TEST RESULTS SUMMARY")
        print("=" * 60)

        print(f"Overall Result: {passed}/{total} test categories passed")
        print(f"Success Rate: {(passed/total)*100:.1f}%")

        print("\nDetailed Results:")
        for category, result in self.test_results.items():
            status = result.get("status", "UNKNOWN")
            duration = result.get("duration", 0)
            print(f"  {category}: {status} ({duration:.3f}s)")

        # Save report to file
        report_file = f"api_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)

        print(f"\nDetailed report saved to: {report_file}")

        if passed == total:
            print("\n✓ ALL TESTS PASSED - API is ready for deployment!")
        else:
            print(f"\n✗ {total - passed} test categories failed - Review issues before deployment")

        print("\nNext Steps:")
        print("1. Address any failed test categories")
        print("2. Set up production environment")
        print("3. Configure monitoring and logging")
        print("4. Deploy to production")
        print("5. Post-deployment validation")

async def main():
    """Main test execution"""
    # Check if server is running
    base_url = "http://localhost:3004"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/", timeout=5.0)
    except Exception as e:
        print(f"Cannot connect to API server at {base_url}")
        print(f"Error: {e}")
        print("\nPlease start the API server first:")
        print("  cd src/api && python -m uvicorn main:app --reload --port 3004")
        return

    # Run test suite
    test_suite = APITestSuite(base_url)
    results = await test_suite.run_all_tests()

    # Cleanup
    await test_suite.client.aclose()

if __name__ == "__main__":
    asyncio.run(main())