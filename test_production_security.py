"""
生產級安全測試驗證
測試企業級安全框架的各個組件

測試覆蓋範圍:
- 輸入驗證和清理
- 速率限制功能
- XSS/SQL注入防護
- 會話管理和連接安全
- 錯誤處理和資源管理

Usage:
    python test_production_security.py

Author: CBSC Quantitative Trading System
Version: 1.0.0
"""

import asyncio
import json
import logging
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# 添加項目根目錄到Python路徑
sys.path.insert(0, str(Path(__file__).parent))

from src.security.enterprise_security import (
    SecurityValidator, SecurityValidationError, RateLimiter
)
from src.api.production_parameter_controls import (
    SecureParameterUpdate, ParameterConfigValidator, ParameterCalculationError
)
from src.websocket.production_websocket_manager import ProductionWebSocketManager

# 配置測試日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class SecurityTestSuite:
    """
    安全測試套件

    提供全面的安全功能測試
    """

    def __init__(self):
        self.test_results = []
        self.passed_tests = 0
        self.failed_tests = 0

    def run_test(self, test_name: str, test_func) -> bool:
        """
        運行單個測試

        Args:
            test_name: 測試名稱
            test_func: 測試函數

        Returns:
            是否通過
        """
        try:
            logger.info(f"🧪 運行測試: {test_name}")
            start_time = time.time()

            test_func()

            duration = time.time() - start_time
            self.test_results.append({
                "name": test_name,
                "status": "PASSED",
                "duration": duration,
                "timestamp": datetime.utcnow().isoformat()
            })
            self.passed_tests += 1

            logger.info(f"✅ {test_name} - 通過 ({duration:.3f}s)")
            return True

        except Exception as e:
            duration = time.time() - start_time
            self.test_results.append({
                "name": test_name,
                "status": "FAILED",
                "error": str(e),
                "duration": duration,
                "timestamp": datetime.utcnow().isoformat()
            })
            self.failed_tests += 1

            logger.error(f"❌ {test_name} - 失敗: {str(e)}")
            return False

    def test_input_validation_xss(self):
        """測試XSS攻擊防護"""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "<svg onload=alert('xss')>",
            "'\"><script>alert('xss')</script>",
            "data:text/html,<script>alert('xss')</script>"
        ]

        for payload in xss_payloads:
            with self.assertRaises(SecurityValidationError):
                SecurityValidator.sanitize_input(payload)

    def test_input_validation_sql_injection(self):
        """測試SQL注入防護"""
        sql_payloads = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "UNION SELECT * FROM users",
            "'; INSERT INTO users VALUES('hacker','password'); --",
            "1'; EXEC xp_cmdshell('dir'); --"
        ]

        for payload in sql_payloads:
            with self.assertRaises(SecurityValidationError):
                SecurityValidator.sanitize_input(payload)

    def test_parameter_validation_ranges(self):
        """測試參數範圍驗證"""
        # 測試有效參數
        valid_rsi = ParameterConfigValidator.validate_parameter(
            'rsi_period', 14
        )
        self.assertEqual(valid_rsi, 14)

        # 測試超出範圍的參數
        with self.assertRaises(Exception):
            ParameterConfigValidator.validate_parameter(
                'rsi_period', 100  # 超出最大值50
            )

    def test_parameter_dependencies(self):
        """測試參數依賴關係驗證"""
        # 測試有效的依賴關係
        params = {'ma_short': 10, 'ma_long': 30}
        validated = ParameterConfigValidator.validate_all_parameters(params)
        self.assertEqual(validated['ma_long'], 30)

        # 測試無效的依賴關係
        params = {'ma_short': 20, 'ma_long': 10}  # ma_long應該大於ma_short
        with self.assertRaises(Exception):
            ParameterConfigValidator.validate_all_parameters(params)

    async def test_rate_limiting(self):
        """測試速率限制功能"""
        rate_limiter = RateLimiter()
        test_user_id = "test_user_security"

        # 正常請求應該通過
        for i in range(10):
            result = await rate_limiter.check_rate_limit(
                test_user_id, 'parameter_updates'
            )
            self.assertTrue(result)

        # 測試超限處理
        # 模擬快速請求超過限制
        for i in range(100):
            try:
                await rate_limiter.check_rate_limit(
                    test_user_id, 'parameter_updates'
                )
            except Exception:
                # 預期會拋出HTTPException
                break
        else:
            self.fail("速率限制未生效")

    async def test_websocket_security(self):
        """測試WebSocket安全功能"""
        ws_manager = ProductionWebSocketManager()
        test_session_id = "test_session_security"

        # 測試會話ID驗證
        with self.assertRaises(Exception):
            await ws_manager.connect(None, "")  # 空會話ID

        with self.assertRaises(Exception):
            await ws_manager.connect(None, "<script>alert('xss')</script>")  # XSS攻擊

    def test_parameter_update_model_validation(self):
        """測試參數更新模型驗證"""
        # 測試有效數據
        valid_data = {
            "session_id": "valid_session_123",
            "parameter_name": "rsi_period",
            "value": 14,
            "user_id": "test_user"
        }
        parameter_update = SecureParameterUpdate(**valid_data)
        self.assertEqual(parameter_update.session_id, "valid_session_123")

        # 測試無效數據
        invalid_data = {
            "session_id": "",  # 空會話ID
            "parameter_name": "rsi_period",
            "value": 14
        }
        with self.assertRaises(Exception):
            SecureParameterUpdate(**invalid_data)

    def test_error_handling(self):
        """測試錯誤處理機制"""
        # 測試SecurityValidationError
        try:
            raise SecurityValidationError(
                "測試錯誤",
                error_code="TEST_ERROR",
                details={"test": True}
            )
        except SecurityValidationError as e:
            self.assertEqual(e.error_code, "TEST_ERROR")
            self.assertTrue(e.details["test"])

        # 測試ParameterCalculationError
        try:
            raise ParameterCalculationError(
                "計算錯誤",
                error_details={"calculation": "failed"}
            )
        except ParameterCalculationError as e:
            self.assertEqual(e.message, "計算錯誤")
            self.assertEqual(e.error_details["calculation"], "failed")

    def assertRaises(self, exception_class):
        """簡化的assertRaises實現"""
        class _AssertRaisesContext:
            def __init__(self, exception_class):
                self.exception_class = exception_class
                self.exception = None

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                if exc_type is None:
                    raise AssertionError(f"{self.exception_class.__name__} 未被拋出")
                if not issubclass(exc_type, self.exception_class):
                    raise AssertionError(f"拋出了 {exc_type.__name__}，但期望 {self.exception_class.__name__}")
                self.exception = exc_val
                return True  # 抑制異常

        return _AssertRaisesContext(exception_class)

    def run_all_tests(self) -> Dict[str, Any]:
        """
        運行所有測試

        Returns:
            測試結果匯總
        """
        logger.info("🚀 開始運行生產級安全測試套件")
        logger.info("=" * 60)

        # 輸入驗證測試
        self.run_test("XSS攻擊防護", self.test_input_validation_xss)
        self.run_test("SQL注入防護", self.test_input_validation_sql_injection)

        # 參數驗證測試
        self.run_test("參數範圍驗證", self.test_parameter_validation_ranges)
        self.run_test("參數依賴關係驗證", self.test_parameter_dependencies)

        # 模型驗證測試
        self.run_test("參數更新模型驗證", self.test_parameter_update_model_validation)

        # 錯誤處理測試
        self.run_test("錯誤處理機制", self.test_error_handling)

        # 異步測試
        async def run_async_tests():
            await self.run_test("速率限制功能", self.test_rate_limiting)
            await self.run_test("WebSocket安全功能", self.test_websocket_security)

        # 運行異步測試
        asyncio.run(run_async_tests())

        # 生成測試報告
        report = {
            "summary": {
                "total_tests": self.passed_tests + self.failed_tests,
                "passed_tests": self.passed_tests,
                "failed_tests": self.failed_tests,
                "success_rate": (self.passed_tests / (self.passed_tests + self.failed_tests)) * 100 if (self.passed_tests + self.failed_tests) > 0 else 0
            },
            "results": self.test_results,
            "timestamp": datetime.utcnow().isoformat()
        }

        # 打印測試結果
        self.print_test_report(report)

        return report

    def print_test_report(self, report: Dict[str, Any]) -> None:
        """打印測試報告"""
        summary = report["summary"]

        logger.info("=" * 60)
        logger.info("📊 測試結果匯總")
        logger.info("=" * 60)
        logger.info(f"總測試數: {summary['total_tests']}")
        logger.info(f"通過測試: {summary['passed_tests']}")
        logger.info(f"失敗測試: {summary['failed_tests']}")
        logger.info(f"成功率: {summary['success_rate']:.1f}%")

        if summary["failed_tests"] > 0:
            logger.info("\n❌ 失敗的測試:")
            for result in report["results"]:
                if result["status"] == "FAILED":
                    logger.info(f"  - {result['name']}: {result['error']}")

        logger.info("=" * 60)

        # 判斷整體測試結果
        if summary["success_rate"] >= 95:
            logger.info("🎉 測試套件通過！系統安全性驗證成功")
        elif summary["success_rate"] >= 80:
            logger.warning("⚠️  測試套件部分通過，建議檢查失敗項")
        else:
            logger.error("❌ 測試套件失敗，系統存在安全隱患")


async def test_real_world_scenario():
    """
    測試真實世界場景
    """
    logger.info("🌍 開始真實世界場景測試")

    rate_limiter = RateLimiter()

    # 模擬多個用戶同時訪問
    users = [f"user_{i}" for i in range(10)]

    for user in users:
        # 每個用戶發送一些正常請求
        for i in range(5):
            try:
                await rate_limiter.check_rate_limit(user, 'parameter_updates')
                logger.info(f"用戶 {user} 正常請求 {i+1}")
            except Exception as e:
                logger.warning(f"用戶 {user} 請求被限制: {str(e)}")

    # 模擬攻擊者快速請求
    attacker = "attacker_user"
    blocked_requests = 0

    for i in range(100):
        try:
            await rate_limiter.check_rate_limit(attacker, 'parameter_updates')
        except Exception as e:
            blocked_requests += 1
            if blocked_requests == 1:  # 只記錄第一次被阻塞
                logger.info(f"攻擊者請求被成功阻擋: {str(e)}")

    logger.info(f"🛡️ 攻擊者總共被阻擋 {blocked_requests} 次請求")


def main():
    """
    主函數 - 運行所有安全測試
    """
    print("🔒 CBSC 生產級安全測試")
    print("=" * 50)
    print("🧪 測試範圍:")
    print("  ✅ 輸入驗證和清理")
    print("  ✅ XSS/SQL注入防護")
    print("  ✅ 參數範圍和依賴驗證")
    print("  ✅ 速率限制功能")
    print("  ✅ WebSocket安全")
    print("  ✅ 錯誤處理機制")
    print("=" * 50)
    print()

    try:
        # 運行測試套件
        test_suite = SecurityTestSuite()
        report = test_suite.run_all_tests()

        # 運行真實世界場景測試
        print("\n" + "=" * 50)
        asyncio.run(test_real_world_scenario())

        # 生成最終報告
        print("\n" + "=" * 50)
        print("📋 最終安全評估")
        print("=" * 50)

        success_rate = report["summary"]["success_rate"]
        if success_rate >= 95:
            print("🏆 安全等級: A+ (優秀)")
            print("✅ 系統通過企業級安全標準")
            print("🚀 可以部署到生產環境")
        elif success_rate >= 80:
            print("🥈 安全等級: B (良好)")
            print("⚠️  系統基本安全，建議優化失敗項")
            print("🔧 可部署到測試環境")
        else:
            print("🥉 安全等級: C (需要改進)")
            print("❌ 系統存在安全隱患")
            print("🚫 不建議部署，需要修復問題")

        # 保存測試報告
        report_file = Path("security_test_report.json")
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"\n📄 詳細測試報告已保存到: {report_file}")

    except Exception as e:
        print(f"❌ 測試執行失敗: {str(e)}")
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())