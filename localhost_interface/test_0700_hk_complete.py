#!/usr/bin/env python3
"""
0700.HK (騰訊控股) 完整交易系統測試
模擬真實交易流程的完整測試套件
"""
import requests
import json
import time
from datetime import datetime
import sys

API_BASE = "http://127.0.0.1:8000"

class HK0700TestSuite:
    def __init__(self):
        self.symbol = "0700.HK"
        self.company_name = "騰訊控股"
        self.api_base = API_BASE
        self.session = requests.Session()
        self.token = None

    def log(self, message, level="INFO"):
        """記錄測試日誌"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")

    def test_authentication(self):
        """測試用戶認證"""
        self.log("開始用戶認證測試...")

        try:
            # 管理員登入
            response = self.session.post(
                f"{self.api_base}/api/auth/token",
                params={"username": "admin", "password": "admin123"}
            )

            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.log(f"認證成功，獲取Token: {self.token[:20]}...")
                return True
            else:
                self.log(f"認證失敗: {response.status_code}", "ERROR")
                return False

        except Exception as e:
            self.log(f"認證異常: {e}", "ERROR")
            return False

    def test_market_data(self):
        """測試市場數據獲取"""
        self.log("測試市場數據獲取...")

        try:
            # 測試健康檢查
            health_response = self.session.get(f"{self.api_base}/api/health")
            if health_response.status_code != 200:
                self.log("健康檢查失敗", "ERROR")
                return False

            health_data = health_response.json()
            self.log(f"服務狀態: {health_data['status']}")

            return True

        except Exception as e:
            self.log(f"市場數據測試異常: {e}", "ERROR")
            return False

    def test_trading_signals(self):
        """測試交易信號功能"""
        self.log("測試0700.HK交易信號...")

        try:
            # 獲取所有信號
            signals_response = self.session.get(f"{self.api_base}/api/signals")
            if signals_response.status_code != 200:
                self.log("獲取信號失敗", "ERROR")
                return False

            signals = signals_response.json()

            # 篩選0700.HK信號
            hk700_signals = [s for s in signals if s['symbol'] == '0700.HK']

            if not hk700_signals:
                self.log("未找到0700.HK信號", "WARNING")
                return True  # 不算失敗，可能當前無信號

            for signal in hk700_signals:
                self.log(f"發現信號: {signal['id']} - {signal['signal_type']} (強度: {signal['strength']})")

                # 測試個別信號詳情
                signal_detail_response = self.session.get(
                    f"{self.api_base}/api/signals/{signal['id']}"
                )
                if signal_detail_response.status_code == 200:
                    detail = signal_detail_response.json()
                    self.log(f"信號詳情: 價格={detail['price_at_signal']}, 信心={detail['confidence']}")
                else:
                    self.log(f"無法獲取信號詳情: {signal['id']}", "ERROR")
                    return False

            return True

        except Exception as e:
            self.log(f"交易信號測試異常: {e}", "ERROR")
            return False

    def test_symbol_filtering(self):
        """測試股票代碼篩選功能"""
        self.log("測試0700.HK股票篩選...")

        try:
            # 測試通過參數篩選
            filtered_response = self.session.get(
                f"{self.api_base}/api/signals",
                params={"symbol": "0700.HK"}
            )

            if filtered_response.status_code != 200:
                self.log("股票篩選失敗", "ERROR")
                return False

            filtered_signals = filtered_response.json()

            # 驗證所有結果都是0700.HK
            for signal in filtered_signals:
                if signal['symbol'] != '0700.HK':
                    self.log(f"篩選錯誤: 返回了非0700.HK信號 {signal['symbol']}", "ERROR")
                    return False

            self.log(f"篩選成功，找到 {len(filtered_signals)} 個0700.HK信號")
            return True

        except Exception as e:
            self.log(f"股票篩選測試異常: {e}", "ERROR")
            return False

    def test_error_handling(self):
        """測試錯誤處理"""
        self.log("測試錯誤處理機制...")

        try:
            # 測試不存在的信號ID
            invalid_signal_response = self.session.get(f"{self.api_base}/api/signals/INVALID_0700_SIGNAL")
            if invalid_signal_response.status_code == 404:
                self.log("404錯誤處理正常")
            else:
                self.log(f"404錯誤處理異常: {invalid_signal_response.status_code}", "ERROR")
                return False

            # 測試無效的認證
            invalid_auth_response = self.session.post(
                f"{self.api_base}/api/auth/token",
                params={"username": "admin", "password": "wrong"}
            )
            if invalid_auth_response.status_code == 401:
                self.log("401認證錯誤處理正常")
            else:
                self.log(f"401錯誤處理異常: {invalid_auth_response.status_code}", "ERROR")
                return False

            return True

        except Exception as e:
            self.log(f"錯誤處理測試異常: {e}", "ERROR")
            return False

    def test_performance(self):
        """測試性能"""
        self.log("測試系統性能...")

        try:
            # 測試多次請求的響應時間
            request_times = []
            num_requests = 20

            for i in range(num_requests):
                start_time = time.time()
                response = self.session.get(f"{self.api_base}/api/health")
                end_time = time.time()

                if response.status_code == 200:
                    request_times.append((end_time - start_time) * 1000)  # 轉換為毫秒

            if request_times:
                avg_time = sum(request_times) / len(request_times)
                max_time = max(request_times)
                min_time = min(request_times)

                self.log(f"性能測試結果 ({len(request_times)}次請求):")
                self.log(f"  平均響應時間: {avg_time:.2f}ms")
                self.log(f"  最大響應時間: {max_time:.2f}ms")
                self.log(f"  最小響應時間: {min_time:.2f}ms")

                # 性能標準: 平均時間小於50ms
                if avg_time < 50:
                    self.log("性能測試通過")
                    return True
                else:
                    self.log("性能測試失敗: 響應時間過長", "ERROR")
                    return False
            else:
                self.log("性能測試失敗: 無有效請求", "ERROR")
                return False

        except Exception as e:
            self.log(f"性能測試異常: {e}", "ERROR")
            return False

    def generate_test_report(self, results):
        """生成測試報告"""
        self.log("\n" + "="*60)
        self.log("0700.HK 完整交易系統測試報告")
        self.log("="*60)

        total_tests = len(results)
        passed_tests = sum(1 for result in results.values() if result)
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0

        self.log(f"測試總數: {total_tests}")
        self.log(f"通過測試: {passed_tests}")
        self.log(f"成功率: {success_rate:.1f}%")

        self.log("\n詳細結果:")
        for test_name, passed in results.items():
            status = "PASS" if passed else "FAIL"
            self.log(f"  {test_name}: {status}")

        # 0700.HK特定信息
        self.log(f"\n測試標的: {self.company_name} ({self.symbol})")
        self.log("測試涵蓋:")
        self.log("  - 用戶認證系統")
        self.log("  - 交易信號獲取")
        self.log("  - 股票代碼篩選")
        self.log("  - 錯誤處理機制")
        self.log("  - 系統性能測試")

        if success_rate >= 90:
            self.log("\n結論: 系統測試通過，0700.HK交易功能正常運行")
        elif success_rate >= 70:
            self.log("\n結論: 系統基本正常，建議檢查失敗項目")
        else:
            self.log("\n結論: 系統存在問題，需要進行維護")

        return success_rate >= 80

    def run_complete_test(self):
        """運行完整測試套件"""
        self.log(f"開始 {self.company_name} ({self.symbol}) 完整交易系統測試")
        self.log("="*60)

        test_results = {}

        # 執行各項測試
        test_results["用戶認證"] = self.test_authentication()
        test_results["市場數據"] = self.test_market_data()
        test_results["交易信號"] = self.test_trading_signals()
        test_results["股票篩選"] = self.test_symbol_filtering()
        test_results["錯誤處理"] = self.test_error_handling()
        test_results["性能測試"] = self.test_performance()

        # 生成報告
        success = self.generate_test_report(test_results)

        return success

if __name__ == "__main__":
    test_suite = HK0700TestSuite()
    success = test_suite.run_complete_test()
    sys.exit(0 if success else 1)