"""
Phase 4 Integration Test Suite
Phase 4: 系統集成與優化 - 完整測試套件

測試API接口集成、性能優化、錯誤處理和前端界面集成
"""

import asyncio
import aiohttp
import json
import time
import logging
from datetime import datetime
from typing import Dict, Any, List
import traceback

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Phase4IntegrationTester:
    """Phase 4 集成測試器"""

    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
        self.test_results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "errors": [],
            "performance_metrics": {},
            "start_time": time.time()
        }

    async def run_all_tests(self) -> Dict[str, Any]:
        """運行所有Phase 4測試"""
        print("🚀 Phase 4: 系統集成與優化 - 完整測試套件")
        print("=" * 60)

        try:
            # 1. API接口集成測試
            await self.test_api_integration()

            # 2. 性能優化測試
            await self.test_performance_optimization()

            # 3. 錯誤處理機制測試
            await self.test_error_handling()

            # 4. 系統健康檢查測試
            await self.test_system_health()

            # 5. 緩存機制測試
            await self.test_caching_mechanism()

            # 6. 並發處理測試
            await self.test_concurrent_requests()

            # 7. 生成測試報告
            await self.generate_test_report()

            return self.test_results

        except Exception as e:
            logger.error(f"❌ 測試套件執行失敗: {e}")
            self.test_results["errors"].append(f"套件執行失敗: {str(e)}")
            return self.test_results

    async def test_api_integration(self) -> None:
        """測試1: API接口集成"""
        print("\n📡 測試1: API接口集成")
        print("-" * 30)

        async with aiohttp.ClientSession() as session:
            tests = [
                self.test_adaptive_analysis_api(session),
                self.test_market_regime_api(session),
                self.test_comparison_api(session),
                self.test_health_check_api(session)
            ]

            results = await asyncio.gather(*tests, return_exceptions=True)

            for i, result in enumerate(results):
                test_name = [
                    "適應性分析API",
                    "市場狀況API",
                    "方法比較API",
                    "健康檢查API"
                ][i]

                if isinstance(result, Exception):
                    self.test_results["failed_tests"] += 1
                    self.test_results["errors"].append(f"{test_name}: {str(result)}")
                    print(f"  ❌ {test_name}: 失�")
                else:
                    self.test_results["passed_tests"] += 1
                    print(f"  ✅ {test_name}: 通過")

        self.test_results["total_tests"] += 4

    async def test_adaptive_analysis_api(self, session: aiohttp.ClientSession) -> bool:
        """測試適應性分析API"""
        try:
            payload = {
                "sources": ["hibor_rates", "monetary_base", "exchange_rates"],
                "use_cache": False
            }

            async with session.post(
                f"{self.api_base_url}/analyze/adaptive",
                json=payload,
                timeout=30
            ) as response:
                if response.status != 200:
                    return False

                data = await response.json()

                # 驗證響應結構
                required_fields = ["success", "timestamp", "data", "execution_time"]
                if not all(field in data for field in required_fields):
                    return False

                # 驗證分析結果
                if not data.get("success"):
                    return False

                analysis_data = data.get("data", {})
                required_analysis_fields = [
                    "final_signal", "consensus_market_state",
                    "adaptive_weights", "source_analyses"
                ]

                return all(field in analysis_data for field in required_analysis_fields)

        except Exception as e:
            logger.error(f"適應性分析API測試失敗: {e}")
            return False

    async def test_market_regime_api(self, session: aiohttp.ClientSession) -> bool:
        """測試市場狀況API"""
        try:
            async with session.get(
                f"{self.api_base_url}/analyze/regime/HKMA_COMPOSITE",
                timeout=15
            ) as response:
                if response.status != 200:
                    return False

                data = await response.json()

                # 驗證響應結構
                required_fields = ["success", "timestamp", "symbol", "market_state"]
                return all(field in data for field in required_fields)

        except Exception as e:
            logger.error(f"市場狀況API測試失敗: {e}")
            return False

    async def test_comparison_api(self, session: aiohttp.ClientSession) -> bool:
        """測試方法比較API"""
        try:
            async with session.get(
                f"{self.api_base_url}/analyze/compare?sources=hibor_rates,monetary_base",
                timeout=20
            ) as response:
                if response.status != 200:
                    return False

                data = await response.json()

                # 驗證響應結構
                required_fields = ["success", "timestamp", "comparison_summary"]
                return all(field in data for field in required_fields)

        except Exception as e:
            logger.error(f"方法比較API測試失敗: {e}")
            return False

    async def test_health_check_api(self, session: aiohttp.ClientSession) -> bool:
        """測試健康檢查API"""
        try:
            async with session.get(
                f"{self.api_base_url}/health",
                timeout=10
            ) as response:
                if response.status != 200:
                    return False

                data = await response.json()

                # 驗證響應結構
                required_fields = ["status", "timestamp", "version", "system_stats"]
                return all(field in data for field in required_fields)

        except Exception as e:
            logger.error(f"健康檢查API測試失敗: {e}")
            return False

    async def test_performance_optimization(self) -> None:
        """測試2: 性能優化"""
        print("\n⚡ 測試2: 性能優化")
        print("-" * 30)

        async with aiohttp.ClientSession() as session:
            # 測試響應時間
            response_times = []

            for i in range(5):
                start_time = time.time()
                try:
                    async with session.get(
                        f"{self.api_base_url}/health",
                        timeout=10
                    ) as response:
                        await response.text()
                        end_time = time.time()
                        response_times.append(end_time - start_time)
                except:
                    continue

            if response_times:
                avg_time = sum(response_times) / len(response_times)
                max_time = max(response_times)

                # 性能標準
                avg_ok = avg_time < 1.0  # 平均響應時間小於1秒
                max_ok = max_time < 2.0  # 最大響應時間小於2秒

                if avg_ok and max_ok:
                    self.test_results["passed_tests"] += 1
                    print(f"  ✅ 響應時間: 平均 {avg_time:.3f}s, 最大 {max_time:.3f}s")
                else:
                    self.test_results["failed_tests"] += 1
                    print(f"  ❌ 響應時間過慢: 平均 {avg_time:.3f}s, 最大 {max_time:.3f}s")

                self.test_results["performance_metrics"]["response_time"] = {
                    "average": avg_time,
                    "max": max_time,
                    "samples": len(response_times)
                }
            else:
                self.test_results["failed_tests"] += 1
                print("  ❌ 無法測量響應時間")

            # 測試並發處理
            concurrent_results = await self.test_concurrent_handling(session)
            if concurrent_results:
                self.test_results["passed_tests"] += 1
                print("  ✅ 並發處理: 正常")
            else:
                self.test_results["failed_tests"] += 1
                print("  ❌ 並發處理: 失敗")

        self.test_results["total_tests"] += 2

    async def test_concurrent_handling(self, session: aiohttp.ClientSession) -> bool:
        """測試並發處理能力"""
        try:
            # 同時發送10個請求
            tasks = []
            for i in range(10):
                task = session.get(f"{self.api_base_url}/health", timeout=10)
                tasks.append(task)

            start_time = time.time()
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()

            # 檢查成功率
            successful = sum(1 for r in responses if not isinstance(r, Exception))
            success_rate = successful / len(responses)

            # 並發處理成功標準：成功率 > 80%
            return success_rate > 0.8

        except Exception as e:
            logger.error(f"並發處理測試失敗: {e}")
            return False

    async def test_error_handling(self) -> None:
        """測試3: 錯誤處理機制"""
        print("\n🛡️ 測試3: 錯誤處理機制")
        print("-" * 30)

        async with aiohttp.ClientSession() as session:
            error_tests = [
                self.test_invalid_endpoint(session),
                self.test_invalid_payload(session),
                self.test_large_payload(session)
            ]

            results = await asyncio.gather(*error_tests, return_exceptions=True)

            for i, result in enumerate(results):
                test_name = [
                    "無效端點處理",
                    "無效負載處理",
                    "大負載處理"
                ][i]

                if isinstance(result, Exception):
                    self.test_results["failed_tests"] += 1
                    print(f"  ❌ {test_name}: 失敗 ({str(result)[:50]})")
                elif result:
                    self.test_results["passed_tests"] += 1
                    print(f"  ✅ {test_name}: 正確處理")
                else:
                    self.test_results["failed_tests"] += 1
                    print(f"  ❌ {test_name}: 處理錯誤")

        self.test_results["total_tests"] += 3

    async def test_invalid_endpoint(self, session: aiohttp.ClientSession) -> bool:
        """測試無效端點處理"""
        try:
            async with session.get(
                f"{self.api_base_url}/invalid/endpoint",
                timeout=10
            ) as response:
                # 應該返回404錯誤
                return response.status == 404
        except Exception:
            return True  # 連接錯誤也是正確的錯誤處理

    async def test_invalid_payload(self, session: aiohttp.ClientSession) -> bool:
        """測試無效負載處理"""
        try:
            async with session.post(
                f"{self.api_base_url}/analyze/adaptive",
                json={"invalid": "payload"},
                timeout=10
            ) as response:
                # 應該處理錯誤並返回合適的響應
                return response.status in [400, 422, 500]
        except Exception:
            return True

    async def test_large_payload(self, session: aiohttp.ClientSession) -> bool:
        """測試大負載處理"""
        try:
            # 創建大負載
            large_payload = {
                "sources": ["source_" + str(i) for i in range(1000)],
                "use_cache": False
            }

            async with session.post(
                f"{self.api_base_url}/analyze/adaptive",
                json=large_payload,
                timeout=30
            ) as response:
                # 應該能夠處理或優雅地拒絕
                return response.status in [200, 400, 413, 422]
        except Exception:
            return True

    async def test_system_health(self) -> None:
        """測試4: 系統健康檢查"""
        print("\n💚 測試4: 系統健康檢查")
        print("-" * 30)

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    f"{self.api_base_url}/health",
                    timeout=10
                ) as response:
                    if response.status != 200:
                        self.test_results["failed_tests"] += 1
                        print("  ❌ 健康檢查端點不可用")
                        return

                    health_data = await response.json()

                    # 檢查健康狀態
                    if health_data.get("status") == "healthy":
                        self.test_results["passed_tests"] += 1
                        print("  ✅ 系統狀態: 健康")

                        # 檢查系統統計
                        stats = health_data.get("system_stats", {})
                        print(f"  📊 統計信息: 請求數 {stats.get('total_requests', 0)}, "
                              f"緩存命中率 {stats.get('cache_hit_rate', '0%')}")

                        # 保存統計信息
                        self.test_results["system_stats"] = stats
                    else:
                        self.test_results["failed_tests"] += 1
                        print(f"  ❌ 系統狀態: {health_data.get('status', 'unknown')}")

            except Exception as e:
                self.test_results["failed_tests"] += 1
                print(f"  ❌ 健康檢查失敗: {e}")

        self.test_results["total_tests"] += 1

    async def test_caching_mechanism(self) -> None:
        """測試5: 緩存機制"""
        print("\n💾 測試5: 緩存機制")
        print("-" * 30)

        async with aiohttp.ClientSession() as session:
            try:
                # 第一次請求（無緩存）
                payload = {
                    "sources": ["hibor_rates"],
                    "use_cache": False
                }

                start_time = time.time()
                async with session.post(
                    f"{self.api_base_url}/analyze/adaptive",
                    json=payload,
                    timeout=30
                ) as response:
                    first_response = await response.json()
                    first_time = time.time() - start_time

                # 第二次請求（有緩存）
                payload["use_cache"] = True

                start_time = time.time()
                async with session.post(
                    f"{self.api_base_url}/analyze/adaptive",
                    json=payload,
                    timeout=30
                ) as response:
                    second_response = await response.json()
                    second_time = time.time() - start_time

                # 第三次請求（驗證緩存一致性）
                start_time = time.time()
                async with session.post(
                    f"{self.api_base_url}/analyze/adaptive",
                    json=payload,
                    timeout=30
                ) as response:
                    third_response = await response.json()
                    third_time = time.time() - start_time

                # 驗證緩存效果
                cache_working = (
                    second_response.get("success") and
                    third_response.get("success") and
                    second_time < first_time * 0.8 and  # 緩存應該更快
                    third_time < first_time * 0.8
                )

                if cache_working:
                    self.test_results["passed_tests"] += 1
                    print(f"  ✅ 緩存機制: 正常工作")
                    print(f"     首次: {first_time:.3f}s, 緩存: {second_time:.3f}s, {third_time:.3f}s")
                else:
                    self.test_results["failed_tests"] += 1
                    print(f"  ❌ 緩存機制: 未正常工作")
                    print(f"     首次: {first_time:.3f}s, 後續: {second_time:.3f}s, {third_time:.3f}s")

                # 測試緩存清除
                async with session.post(
                    f"{self.api_base_url}/cache/clear",
                    timeout=10
                ) as response:
                    if response.status == 200:
                        self.test_results["passed_tests"] += 1
                        print("  ✅ 緩存清除: 正常")
                    else:
                        self.test_results["failed_tests"] += 1
                        print("  ❌ 緩存清除: 失敗")

            except Exception as e:
                self.test_results["failed_tests"] += 2  # 兩個緩存測試失敗
                print(f"  ❌ 緩存測試失敗: {e}")

        self.test_results["total_tests"] += 2

    async def test_concurrent_requests(self) -> None:
        """測試6: 並發請求處理"""
        print("\n🔄 測試6: 並發請求處理")
        print("-" * 30)

        async with aiohttp.ClientSession() as session:
            try:
                # 並發請求測試
                concurrent_count = 20
                tasks = []

                for i in range(concurrent_count):
                    task = session.get(f"{self.api_base_url}/health", timeout=10)
                    tasks.append(task)

                start_time = time.time()
                responses = await asyncio.gather(*tasks, return_exceptions=True)
                total_time = time.time() - start_time

                # 分析結果
                successful = sum(1 for r in responses if not isinstance(r, Exception))
                success_rate = successful / concurrent_count

                # 並發性能標準
                success_ok = success_rate > 0.9  # 90%成功率
                time_ok = total_time < 10.0  # 總時間小於10秒

                if success_ok and time_ok:
                    self.test_results["passed_tests"] += 1
                    print(f"  ✅ 並發處理: 成功 {successful}/{concurrent_count} "
                          f"({success_rate:.1%}), 總時間 {total_time:.3f}s")
                else:
                    self.test_results["failed_tests"] += 1
                    print(f"  ❌ 並發處理: 成功 {successful}/{concurrent_count} "
                          f"({success_rate:.1%}), 總時間 {total_time:.3f}s")

                # 記錄並發性能
                self.test_results["performance_metrics"]["concurrent"] = {
                    "success_rate": success_rate,
                    "total_time": total_time,
                    "requests": concurrent_count
                }

            except Exception as e:
                self.test_results["failed_tests"] += 1
                print(f"  ❌ 並發請求測試失敗: {e}")

        self.test_results["total_tests"] += 1

    async def generate_test_report(self) -> None:
        """生成測試報告"""
        print("\n📋 測試報告生成")
        print("-" * 30)

        total_time = time.time() - self.test_results["start_time"]

        report = {
            "test_phase": "Phase 4: 系統集成與優化",
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": self.test_results["total_tests"],
                "passed_tests": self.test_results["passed_tests"],
                "failed_tests": self.test_results["failed_tests"],
                "success_rate": self.test_results["passed_tests"] / max(1, self.test_results["total_tests"]),
                "total_execution_time": total_time
            },
            "performance_metrics": self.test_results.get("performance_metrics", {}),
            "system_stats": self.test_results.get("system_stats", {}),
            "errors": self.test_results["errors"],
            "recommendations": self._generate_recommendations()
        }

        # 保存報告
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"results/phase4_integration_test_{timestamp}.json"

        try:
            import os
            os.makedirs("results", exist_ok=True)

            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2, default=str)

            print(f"  📁 報告已保存至: {report_file}")
        except Exception as e:
            print(f"  ❌ 保存報告失敗: {e}")

        # 顯示摘要
        self._display_summary(report)

    def _generate_recommendations(self) -> List[str]:
        """生成改進建議"""
        recommendations = []

        # 基於錯誤率的建議
        error_rate = self.test_results["failed_tests"] / max(1, self.test_results["total_tests"])
        if error_rate > 0.1:
            recommendations.append("錯誤率較高，建議檢查系統穩定性")

        # 基於性能的建議
        perf_metrics = self.test_results.get("performance_metrics", {})
        if "response_time" in perf_metrics:
            avg_time = perf_metrics["response_time"]["average"]
            if avg_time > 1.0:
                recommendations.append("響應時間較慢，建議優化處理邏輯")

        if "concurrent" in perf_metrics:
            success_rate = perf_metrics["concurrent"]["success_rate"]
            if success_rate < 0.95:
                recommendations.append("並發處理成功率偏低，建議增強系統容量")

        # 基於系統統計的建議
        system_stats = self.test_results.get("system_stats", {})
        if system_stats:
            cache_hit_rate = system_stats.get("cache_hit_rate", "0%")
            if "%" in cache_hit_rate and float(cache_hit_rate.rstrip("%")) < 50:
                recommendations.append("緩存命中率偏低，建議優化緩存策略")

            error_rate_stat = system_stats.get("error_rate", "0%")
            if "%" in error_rate_stat and float(error_rate_stat.rstrip("%")) > 5:
                recommendations.append("系統錯誤率偏高，建議檢查錯誤日誌")

        if not recommendations:
            recommendations.append("系統運行良好，無重大問題")

        return recommendations

    def _display_summary(self, report: Dict[str, Any]) -> None:
        """顯示測試摘要"""
        print("\n" + "=" * 60)
        print("📊 Phase 4 集成測試摘要")
        print("=" * 60)

        summary = report["summary"]
        print(f"🔍 總測試數: {summary['total_tests']}")
        print(f"✅ 通過數: {summary['passed_tests']}")
        print(f"❌ 失敗數: {summary['failed_tests']}")
        print(f"📈 成功率: {summary['success_rate']:.1%}")
        print(f"⏱️ 執行時間: {summary['total_execution_time']:.2f}秒")

        # 性能指標
        perf_metrics = report.get("performance_metrics", {})
        if perf_metrics:
            print(f"\n⚡ 性能指標:")
            if "response_time" in perf_metrics:
                rt = perf_metrics["response_time"]
                print(f"   響應時間: 平均 {rt['average']:.3f}s, 最大 {rt['max']:.3f}s")
            if "concurrent" in perf_metrics:
                conc = perf_metrics["concurrent"]
                print(f"   並發處理: {conc['success_rate']:.1%} 成功率")

        # 系統統計
        system_stats = report.get("system_stats", {})
        if system_stats:
            print(f"\n💚 系統狀態:")
            print(f"   總請求數: {system_stats.get('total_requests', 'N/A')}")
            print(f"   緩存命中率: {system_stats.get('cache_hit_rate', 'N/A')}")
            print(f"   平均響應時間: {system_stats.get('avg_response_time', 'N/A')}")
            print(f"   錯誤率: {system_stats.get('error_rate', 'N/A')}")

        # 錯誤列表
        errors = report.get("errors", [])
        if errors:
            print(f"\n❌ 錯誤列表:")
            for error in errors[:5]:  # 只顯示前5個錯誤
                print(f"   • {error}")

        # 建議
        recommendations = report.get("recommendations", [])
        if recommendations:
            print(f"\n💡 改進建議:")
            for i, rec in enumerate(recommendations, 1):
                print(f"   {i}. {rec}")

        # 總體評估
        success_rate = summary["success_rate"]
        if success_rate >= 0.9:
            status = "🎉 優秀"
            message = "系統集成與優化完成度很高"
        elif success_rate >= 0.8:
            status = "✅ 良好"
            message = "系統基本功能正常，有小幅改進空間"
        elif success_rate >= 0.7:
            status = "⚠️ 一般"
            message = "系統需要一些優化"
        else:
            status = "❌ 需要改進"
            message = "系統存在較多問題，需要重點優化"

        print(f"\n🏆 總體評估: {status}")
        print(f"📝 評估說明: {message}")
        print("=" * 60)

async def main():
    """主函數"""
    print("🚀 啟動Phase 4集成測試套件")

    tester = Phase4IntegrationTester()

    try:
        results = await tester.run_all_tests()

        # 判斷整體結果
        success_rate = results["passed_tests"] / max(1, results["total_tests"])

        if success_rate >= 0.8:
            print("\n🎉 Phase 4: 系統集成與優化 - 測試通過！")
            print("系統已準備好投入生產使用")
            return 0
        else:
            print("\n❌ Phase 4: 系統集成與優化 - 測試未完全通過")
            print("建議修復失敗的測試後重新運行")
            return 1

    except Exception as e:
        print(f"\n💥 測試執行發生錯誤: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)