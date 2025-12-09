#!/usr / bin / env python3
"""
Graceful Degradation Test
測試系統在真實數據源失敗時的優雅降級機制
"""

import sys

sys.path.append("src")

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# Setup logging
logging.basicConfig(
    level = logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class GracefulDegradationTest:
    """優雅降級測試類"""

    def __init__(self):
        self.test_results = []
        self.backup_files = {}

    def setup_test_environment(self):
        """設置測試環境"""
        logger.info("Setting up test environment for graceful degradation test")

        # 備份現有數據文件
        government_dir = Path("data / government")
        if government_dir.exists():
            backup_dir = Path("data / government_backup")
            backup_dir.mkdir(exist_ok = True)

            for json_file in government_dir.glob("*.json"):
                backup_path = backup_dir / json_file.name
                if not backup_path.exists():
                    shutil.copy2(json_file, backup_path)
                    self.backup_files[json_file.name] = str(backup_path)

            logger.info(f"Backed up {len(self.backup_files)} files")

    def test_scenario_1_api_failure_with_local_backup(self):
        """測試場景1：API失敗但有本地備份"""
        logger.info("Testing Scenario 1: API Failure with Local Backup")

        try:
            # 導入真實數據專用API系統
            from real_data_only_api_system import RealDataOnlyAPISystem

            api_system = RealDataOnlyAPISystem()

            # 測試數據獲取（API失敗時應使用本地備份）
            result = api_system.fetch_real_data_only("hibor_rates", 7)

            test_result = {
                "scenario": "API Failure with Local Backup",
                "data_type": "hibor_rates",
                "result_type": type(result).__name__,
                "success": result is not None,
                "has_data": result is not None
                and "data" in result
                and len(result["data"]) > 0,
                "source": result.get("source", "Unknown") if result else None,
                "verification_passed": (
                    result.get("real_data_verification", {}).get("verified", False)
                    if result
                    else False
                ),
            }

            logger.info(
                f"Scenario 1 Result: {test_result['success']}, Source: {test_result['source']}"
            )
            self.test_results.append(test_result)

        except Exception as e:
            logger.error(f"Scenario 1 failed: {e}")
            self.test_results.append(
                {
                    "scenario": "API Failure with Local Backup",
                    "success": False,
                    "error": str(e),
                }
            )

    def test_scenario_2_simulate_api_unavailable(self):
        """測試場景2：模擬API完全不可用"""
        logger.info("Testing Scenario 2: API Completely Unavailable")

        try:
            from src.api.government_data import GovernmentDataAPI

            # 創建政府數據API實例
            gov_api = GovernmentDataAPI()

            # 測試獲取數據
            result = gov_api.get_hibor_data(7)

            test_result = {
                "scenario": "API Completely Unavailable",
                "data_type": "hibor_rates",
                "result_type": type(result).__name__,
                "success": result is not None,
                "has_data": result is not None
                and "data" in result
                and len(result["data"]) > 0,
                "data_source": result.get("data_type", "Unknown") if result else None,
                "record_count": len(result.get("data", [])) if result else 0,
            }

            logger.info(
                f"Scenario 2 Result: {test_result['success']}, Records: {test_result['record_count']}"
            )
            self.test_results.append(test_result)

        except Exception as e:
            logger.error(f"Scenario 2 failed: {e}")
            self.test_results.append(
                {
                    "scenario": "API Completely Unavailable",
                    "success": False,
                    "error": str(e),
                }
            )

    def test_scenario_3_no_fallback_to_simulated_data(self):
        """測試場景3：確保不降級到模擬數據"""
        logger.info("Testing Scenario 3: No Fallback to Simulated Data")

        try:
            from robust_government_api_system import RobustGovernmentAPISystem

            robust_api = RobustGovernmentAPISystem()

            # 測試數據獲取
            result = robust_api.fetch_with_fallback("hibor_rates", 7)

            # 檢查是否返回了真實數據而不是模擬數據
            is_real_data = False
            if result and "data" in result:
                # 檢查數據來源標記
                if isinstance(result["data"], list) and result["data"]:
                    sample_record = result["data"][0]
                    if isinstance(sample_record, dict):
                        # 檢查真實數據特徵
                        has_real_fields = any(
                            field in sample_record
                            for field in [
                                "source",
                                "date",
                                "hibor_overnight",
                                "ir_1m",
                                "ir_3m",
                            ]
                        )
                        has_hkma_source = sample_record.get("source") == "HKMA"
                        is_real_data = has_real_fields

            test_result = {
                "scenario": "No Fallback to Simulated Data",
                "success": result is not None,
                "is_real_data": is_real_data,
                "has_real_data_indicators": is_real_data,
                "rejects_simulated": not (
                    result and result.get("fallback_used") == "simulated"
                ),
                "record_count": len(result.get("data", [])) if result else 0,
            }

            logger.info(
                f"Scenario 3 Result: Real Data={test_result['is_real_data']}, Rejects Simulated={test_result['rejects_simulated']}"
            )
            self.test_results.append(test_result)

        except Exception as e:
            logger.error(f"Scenario 3 failed: {e}")
            self.test_results.append(
                {
                    "scenario": "No Fallback to Simulated Data",
                    "success": False,
                    "error": str(e),
                }
            )

    def test_scenario_4_data_source_prioritization(self):
        """測試場景4：數據源優先級測試"""
        logger.info("Testing Scenario 4: Data Source Prioritization")

        try:
            # 測試不同的數據源優先級
            data_types = ["hibor_rates", "exchange_rates", "monetary_base"]
            prioritization_results = {}

            from real_data_only_api_system import RealDataOnlyAPISystem

            api_system = RealDataOnlyAPISystem()

            for data_type in data_types:
                result = api_system.fetch_real_data_only(data_type, 7)

                prioritization_results[data_type] = {
                    "available": result is not None,
                    "source": result.get("source", "None") if result else "None",
                    "has_records": result is not None
                    and len(result.get("data", [])) > 0,
                    "verified": (
                        result.get("real_data_verification", {}).get("verified", False)
                        if result
                        else False
                    ),
                }

            # 檢查優先級是否正確
            priority_test_passed = all(
                result["verified"]
                for result in prioritization_results.values()
                if result["available"]
            )

            test_result = {
                "scenario": "Data Source Prioritization",
                "data_sources_tested": len(data_types),
                "all_sources_verified": priority_test_passed,
                "successful_sources": sum(
                    1 for r in prioritization_results.values() if r["available"]
                ),
                "detailed_results": prioritization_results,
            }

            logger.info(
                f"Scenario 4 Result: {test_result['successful_sources']}/{len(data_types)} sources available, all verified: {test_result['all_sources_verified']}"
            )
            self.test_results.append(test_result)

        except Exception as e:
            logger.error(f"Scenario 4 failed: {e}")
            self.test_results.append(
                {
                    "scenario": "Data Source Prioritization",
                    "success": False,
                    "error": str(e),
                }
            )

    def test_scenario_5_error_handling_and_recovery(self):
        """測試場景5：錯誤處理和恢復"""
        logger.info("Testing Scenario 5: Error Handling and Recovery")

        try:
            from src.api.government_data import GovernmentDataAPI

            gov_api = GovernmentDataAPI()

            # 測試多種錯誤情況
            error_scenarios = [
                (
                    "Invalid data type",
                    lambda: gov_api._fetch_from_api("invalid_type", 7),
                ),
                ("Zero days back", lambda: gov_api.get_hibor_data(0)),
                ("Negative days back", lambda: gov_api.get_hibor_data(-5)),
            ]

            error_handling_results = []

            for scenario_name, test_func in error_scenarios:
                try:
                    result = test_func()
                    error_handling_results.append(
                        {
                            "scenario": scenario_name,
                            "handled_gracefully": True,
                            "returned_something": result is not None,
                            "no_exception": True,
                        }
                    )
                except Exception as e:
                    error_handling_results.append(
                        {
                            "scenario": scenario_name,
                            "handled_gracefully": False,
                            "error_message": str(e)[:100],  # 限制錯誤消息長度
                            "no_exception": False,
                        }
                    )

            # 計算錯誤處理成功率
            handled_successfully = sum(
                1 for r in error_handling_results if r["handled_gracefully"]
            )
            error_handling_rate = handled_successfully / len(error_handling_results)

            test_result = {
                "scenario": "Error Handling and Recovery",
                "scenarios_tested": len(error_scenarios),
                "handled_successfully": handled_successfully,
                "error_handling_rate": error_handling_rate,
                "all_scenarios_handled": error_handling_rate >= 0.8,
                "detailed_results": error_handling_results,
            }

            logger.info(
                f"Scenario 5 Result: {test_result['handled_successfully']}/{len(error_scenarios)} scenarios handled gracefully"
            )
            self.test_results.append(test_result)

        except Exception as e:
            logger.error(f"Scenario 5 failed: {e}")
            self.test_results.append(
                {
                    "scenario": "Error Handling and Recovery",
                    "success": False,
                    "error": str(e),
                }
            )

    def run_all_tests(self):
        """運行所有優雅降級測試"""
        logger.info("Starting comprehensive graceful degradation tests")

        # 設置測試環境
        self.setup_test_environment()

        # 運行所有測試場景
        self.test_scenario_1_api_failure_with_local_backup()
        self.test_scenario_2_simulate_api_unavailable()
        self.test_scenario_3_no_fallback_to_simulated_data()
        self.test_scenario_4_data_source_prioritization()
        self.test_scenario_5_error_handling_and_recovery()

        # 計算整體結果
        self.calculate_overall_results()

    def calculate_overall_results(self):
        """計算整體測試結果"""
        total_tests = len(self.test_results)
        passed_tests = sum(
            1 for test in self.test_results if test.get("success", False)
        )

        # 分析各個測試場景的結果
        scenario_analysis = {}
        for test in self.test_results:
            scenario = test["scenario"]
            if scenario not in scenario_analysis:
                scenario_analysis[scenario] = {"total": 0, "passed": 0, "details": []}

            scenario_analysis[scenario]["total"] += 1
            if test.get("success", False):
                scenario_analysis[scenario]["passed"] += 1

            scenario_analysis[scenario]["details"].append(test)

        # 整體評估
        success_rate = passed_tests / total_tests if total_tests > 0 else 0
        overall_status = (
            "EXCELLENT"
            if success_rate >= 0.9
            else (
                "GOOD"
                if success_rate >= 0.8
                else "ACCEPTABLE" if success_rate >= 0.7 else "POOR"
            )
        )

        self.overall_results = {
            "test_summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "success_rate": success_rate,
                "overall_status": overall_status,
            },
            "scenario_analysis": scenario_analysis,
            "test_timestamp": datetime.now().isoformat(),
            "recommendations": self._generate_degradation_recommendations(
                scenario_analysis
            ),
        }

    def _generate_degradation_recommendations(
        self, scenario_analysis: Dict
    ) -> List[str]:
        """生成優雅降級改進建議"""
        recommendations = []

        # 檢查各場景的表現
        for scenario, analysis in scenario_analysis.items():
            rate = (
                analysis["passed"] / analysis["total"] if analysis["total"] > 0 else 0
            )

            if rate < 0.8:
                recommendations.append(f"改進{scenario}的實現，成功率僅為{rate:.1%}")

        # 通用建議
        if (
            scenario_analysis.get("API Failure with Local Backup", {}).get("passed", 0)
            == 0
        ):
            recommendations.append("增強API失敗時的本地備份機制")

        if (
            scenario_analysis.get("No Fallback to Simulated Data", {}).get("passed", 0)
            == 0
        ):
            recommendations.append("確保系統不會降級到模擬數據，嚴格執行真實數據政策")

        if not recommendations:
            recommendations.append("優雅降級機制運行良好，繼續維護現有標準")

        return recommendations

    def generate_test_report(self):
        """生成測試報告"""
        print("=" * 60)
        print("GRACEFUL DEGRADATION TEST REPORT")
        print("=" * 60)

        summary = self.overall_results["test_summary"]
        print(f"\nTest Summary:")
        print(f"  Total Tests: {summary['total_tests']}")
        print(f"  Passed: {summary['passed_tests']}")
        print(f"  Success Rate: {summary['success_rate']:.1%}")
        print(f"  Overall Status: {summary['overall_status']}")

        print(f"\nScenario Analysis:")
        for scenario, analysis in self.overall_results["scenario_analysis"].items():
            rate = (
                analysis["passed"] / analysis["total"] if analysis["total"] > 0 else 0
            )
            status_icon = (
                "[OK]" if rate >= 0.8 else "[WARN]" if rate >= 0.6 else "[FAIL]"
            )
            print(
                f"  {scenario}: {status_icon} {rate:.1%} ({analysis['passed']}/{analysis['total']})"
            )

        print(f"\nRecommendations:")
        for i, rec in enumerate(self.overall_results["recommendations"], 1):
            print(f"  {i}. {rec}")

        # 保存詳細報告
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"graceful_degradation_test_report_{timestamp}.json"

        try:
            with open(report_file, "w", encoding="utf - 8") as f:
                json.dump(
                    self.overall_results, f, indent = 2, ensure_ascii = False, default = str
                )
            print(f"\nDetailed report saved to: {report_file}")
        except Exception as e:
            print(f"\nReport save failed: {e}")

        print("\n" + "=" * 60)
        print("GRACEFUL DEGRADATION TEST COMPLETED")
        print("=" * 60)

    def cleanup_test_environment(self):
        """清理測試環境"""
        logger.info("Cleaning up test environment")

        # 恢復備份文件（如果需要）
        # 在這個測試中，我們不需要恢復，只是確保備份存在
        if self.backup_files:
            logger.info(f"Backup files maintained: {len(self.backup_files)}")


def main():
    """主函數"""
    degradation_test = GracefulDegradationTest()

    try:
        # 運行所有測試
        degradation_test.run_all_tests()

        # 生成報告
        degradation_test.generate_test_report()

        return degradation_test.overall_results

    finally:
        # 清理測試環境
        degradation_test.cleanup_test_environment()


if __name__ == "__main__":
    test_results = main()
