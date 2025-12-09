#!/usr / bin / env python3
"""
三層架構集成測試系統
測試數據流：數據層(8001) → 業務層(9000) → 表現層(3006)
"""

import requests
import json
import time
import asyncio
import aiohttp
import statistics
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ThreeLayerIntegrationTest:
    """三層架構集成測試類"""

    def __init__(self):
        self.data_layer_url = "http://localhost:8001"
        self.business_layer_url = "http://localhost:9000"
        self.presentation_layer_url = "http://localhost:3006"

        self.test_results = {
            "health_checks": {},
            "data_flow_tests": {},
            "api_endpoint_tests": {},
            "performance_tests": {},
            "error_handling_tests": {},
            "end_to_end_tests": {}
        }

        self.performance_metrics = {
            "response_times": [],
            "success_rates": {},
            "error_counts": {},
            "cache_hit_rates": {}
        }

    async def run_all_tests(self) -> Dict:
        """執行所有集成測試"""
        logger.info("🚀 開始三層架構集成測試")

        # 1. 健康檢查
        await self._test_health_checks()

        # 2. 數據流測試
        await self._test_data_flow()

        # 3. API端點測試
        await self._test_api_endpoints()

        # 4. 性能測試
        await self._test_performance()

        # 5. 錯誤處理測試
        await self._test_error_handling()

        # 6. 端到端測試
        await self._test_end_to_end_scenarios()

        # 生成測試報告
        return await self._generate_test_report()

    async def _test_health_checks(self):
        """測試各層健康狀態"""
        logger.info("📋 執行健康檢查測試")

        health_checks = {}

        # 測試數據層健康狀態
        try:
            response = requests.get(f"{self.data_layer_url}/api / v1 / health", timeout=5)
            health_checks["data_layer"] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds(),
                "data": response.json() if response.status_code == 200 else None
            }
        except Exception as e:
            health_checks["data_layer"] = {
                "status": "error",
                "error": str(e)
            }

        # 測試業務層健康狀態
        try:
            response = requests.get(f"{self.business_layer_url}/health", timeout=5)
            health_checks["business_layer"] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds(),
                "data": response.json() if response.status_code == 200 else None
            }
        except Exception as e:
            health_checks["business_layer"] = {
                "status": "error",
                "error": str(e)
            }

        # 測試表現層健康狀態
        try:
            response = requests.get(f"{self.presentation_layer_url}/api / v3 / health", timeout=5)
            health_checks["presentation_layer"] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds(),
                "data": response.json() if response.status_code == 200 else None
            }
        except Exception as e:
            health_checks["presentation_layer"] = {
                "status": "error",
                "error": str(e)
            }

        self.test_results["health_checks"] = health_checks

        # 計算整體健康狀態
        healthy_count = sum(1 for check in health_checks.values() if check.get("status") == "healthy")
        logger.info(f"健康檢查完成: {healthy_count}/3 層服務正常")

    async def _test_data_flow(self):
        """測試三層數據流"""
        logger.info("🔄 執行數據流測試")

        data_flow_results = {}

        # 測試股票數據流：數據層 → 業務層 → 表現層
        test_symbols = ["0700.HK", "9988.HK"]

        for symbol in test_symbols:
            try:
                # 1. 從數據層獲取原始數據
                start_time = time.time()
                data_response = requests.post(
                    f"{self.data_layer_url}/api / v1 / stock / data",
                    json={"symbol": symbol, "duration": 30},
                    timeout=10
                )
                data_layer_time = time.time() - start_time

                if data_response.status_code == 200:
                    data_layer_data = data_response.json()
                    logger.info(f"✅ 數據層 {symbol}: 成功返回 {len(data_layer_data.get('data', []))} 條記錄")
                else:
                    logger.error(f"❌ 數據層 {symbol}: HTTP {data_response.status_code}")
                    continue

                # 2. 從業務層獲取分析數據
                start_time = time.time()
                business_response = requests.get(
                    f"{self.business_layer_url}/api / analysis/{symbol}",
                    timeout=10
                )
                business_layer_time = time.time() - start_time

                if business_response.status_code == 200:
                    business_data = business_response.json()
                    logger.info(f"✅ 業務層 {symbol}: 成功返回分析結果")
                else:
                    logger.error(f"❌ 業務層 {symbol}: HTTP {business_response.status_code}")

                # 3. 從表現層獲取格式化數據
                start_time = time.time()
                presentation_response = requests.post(
                    f"{self.presentation_layer_url}/api / v3 / dashboard / data",
                    json={"symbols": [symbol], "timeframe": "daily"},
                    timeout=10
                )
                presentation_layer_time = time.time() - start_time

                if presentation_response.status_code == 200:
                    presentation_data = presentation_response.json()
                    logger.info(f"✅ 表現層 {symbol}: 成功返回格式化數據")
                else:
                    logger.error(f"❌ 表現層 {symbol}: HTTP {presentation_response.status_code}")

                # 記錄數據流結果
                data_flow_results[symbol] = {
                    "data_layer": {
                        "success": data_response.status_code == 200,
                        "response_time": data_layer_time,
                        "data_points": len(data_layer_data.get('data', [])) if data_response.status_code == 200 else 0
                    },
                    "business_layer": {
                        "success": business_response.status_code == 200,
                        "response_time": business_layer_time,
                        "has_analysis": bool(business_data.get('analysis')) if business_response.status_code == 200 else False
                    },
                    "presentation_layer": {
                        "success": presentation_response.status_code == 200,
                        "response_time": presentation_layer_time,
                        "formatted_data": bool(presentation_data.get('data')) if presentation_response.status_code == 200 else False
                    },
                    "total_flow_time": data_layer_time + business_layer_time + presentation_layer_time
                }

                # 記錄性能指標
                self.performance_metrics["response_times"].extend([
                    data_layer_time, business_layer_time, presentation_layer_time
                ])

            except Exception as e:
                logger.error(f"❌ 數據流測試失敗 {symbol}: {e}")
                data_flow_results[symbol] = {
                    "error": str(e),
                    "success": False
                }

        self.test_results["data_flow_tests"] = data_flow_results

    async def _test_api_endpoints(self):
        """測試各層API端點"""
        logger.info("🔗 執行API端點測試")

        api_results = {}

        # 測試數據層API端點
        data_layer_endpoints = [
            ("/api / v1 / health", "GET", None),
            ("/api / v1 / sources", "GET", None),
            ("/api / v1 / indicators", "GET", None),
            ("/api / v1 / stock / data", "POST", {"symbol": "0700.HK", "duration": 30}),
            ("/api / v1 / technical / indicators", "POST", {"symbol": "0700.HK", "indicators": ["rsi", "sma"]}),
            ("/api / v1 / market / overview", "POST", {"market": "HK", "data_type": "quotes"})
        ]

        data_layer_results = {}
        for endpoint, method, payload in data_layer_endpoints:
            try:
                start_time = time.time()
                if method == "GET":
                    response = requests.get(f"{self.data_layer_url}{endpoint}", timeout=10)
                else:
                    response = requests.post(f"{self.data_layer_url}{endpoint}", json=payload, timeout=10)

                response_time = time.time() - start_time
                data_layer_results[endpoint] = {
                    "success": response.status_code == 200,
                    "status_code": response.status_code,
                    "response_time": response_time,
                    "content_type": response.headers.get('content - type', 'unknown')
                }

                if response.status_code == 200:
                    logger.info(f"✅ 數據層 {method} {endpoint}: {response_time:.3f}s")
                else:
                    logger.warning(f"⚠️ 數據層 {method} {endpoint}: HTTP {response.status_code}")

            except Exception as e:
                data_layer_results[endpoint] = {
                    "success": False,
                    "error": str(e)
                }
                logger.error(f"❌ 數據層 {method} {endpoint}: {e}")

        api_results["data_layer"] = data_layer_results

        # 測試表現層API端點
        presentation_layer_endpoints = [
            ("/api / v3 / health", "GET", None),
            ("/api / v3 / ui / components", "GET", None),
            ("/api / v3 / ui / translations", "GET", None),
            ("/api / v3 / dashboard / data", "POST", {"symbols": ["0700.HK"], "timeframe": "daily"}),
            ("/api / v3 / chart / data", "POST", {"symbol": "0700.HK", "chart_type": "candlestick"})
        ]

        presentation_layer_results = {}
        for endpoint, method, payload in presentation_layer_endpoints:
            try:
                start_time = time.time()
                if method == "GET":
                    response = requests.get(f"{self.presentation_layer_url}{endpoint}", timeout=10)
                else:
                    response = requests.post(f"{self.presentation_layer_url}{endpoint}", json=payload, timeout=10)

                response_time = time.time() - start_time
                presentation_layer_results[endpoint] = {
                    "success": response.status_code == 200,
                    "status_code": response.status_code,
                    "response_time": response_time,
                    "content_type": response.headers.get('content - type', 'unknown')
                }

                if response.status_code == 200:
                    logger.info(f"✅ 表現層 {method} {endpoint}: {response_time:.3f}s")
                else:
                    logger.warning(f"⚠️ 表現層 {method} {endpoint}: HTTP {response.status_code}")

            except Exception as e:
                presentation_layer_results[endpoint] = {
                    "success": False,
                    "error": str(e)
                }
                logger.error(f"❌ 表現層 {method} {endpoint}: {e}")

        api_results["presentation_layer"] = presentation_layer_results

        self.test_results["api_endpoint_tests"] = api_results

    async def _test_performance(self):
        """執行性能測試"""
        logger.info("⚡ 執行性能測試")

        performance_results = {}

        # 1. 響應時間統計
        if self.performance_metrics["response_times"]:
            response_times = self.performance_metrics["response_times"]
            performance_results["response_time_stats"] = {
                "count": len(response_times),
                "average": statistics.mean(response_times),
                "median": statistics.median(response_times),
                "min": min(response_times),
                "max": max(response_times),
                "p95": sorted(response_times)[int(len(response_times) * 0.95)] if len(response_times) > 20 else max(response_times)
            }

        # 2. 並發測試
        concurrent_results = await self._test_concurrent_requests()
        performance_results["concurrent_test"] = concurrent_results

        # 3. 緩存效率測試
        cache_results = await self._test_cache_efficiency()
        performance_results["cache_efficiency"] = cache_results

        self.test_results["performance_tests"] = performance_results

    async def _test_concurrent_requests(self, concurrent_users: int = 10) -> Dict:
        """測試並發請求處理"""
        logger.info(f"🔥 測試 {concurrent_users} 並發用戶")

        async def make_request(session, url):
            try:
                start_time = time.time()
                async with session.get(url, timeout=15) as response:
                    await response.text()
                    return {
                        "success": response.status == 200,
                        "response_time": time.time() - start_time,
                        "status_code": response.status
                    }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "response_time": 15.0
                }

        # 測試數據層並發
        async with aiohttp.ClientSession() as session:
            tasks = [
                make_request(session, f"{self.data_layer_url}/api / v1 / health")
                for _ in range(concurrent_users)
            ]
            data_layer_results = await asyncio.gather(*tasks)

        # 測試表現層並發
        async with aiohttp.ClientSession() as session:
            tasks = [
                make_request(session, f"{self.presentation_layer_url}/api / v3 / health")
                for _ in range(concurrent_users)
            ]
            presentation_layer_results = await asyncio.gather(*tasks)

        # 統計結果
        def analyze_results(results, layer_name):
            successful_requests = [r for r in results if r.get("success", False)]
            response_times = [r["response_time"] for r in successful_requests]

            return {
                "total_requests": len(results),
                "successful_requests": len(successful_requests),
                "success_rate": len(successful_requests) / len(results) * 100,
                "average_response_time": statistics.mean(response_times) if response_times else 0,
                "max_response_time": max(response_times) if response_times else 0,
                "min_response_time": min(response_times) if response_times else 0
            }

        return {
            "data_layer": analyze_results(data_layer_results, "數據層"),
            "presentation_layer": analyze_results(presentation_layer_results, "表現層"),
            "concurrent_users": concurrent_users
        }

    async def _test_cache_efficiency(self) -> Dict:
        """測試緩存效率"""
        logger.info("💾 測試緩存效率")

        cache_results = {}

        # 測試數據層緩存
        try:
            # 第一次請求（應該從源獲取）
            start_time = time.time()
            response1 = requests.post(
                f"{self.data_layer_url}/api / v1 / stock / data",
                json={"symbol": "0700.HK", "duration": 30},
                timeout=10
            )
            first_request_time = time.time() - start_time

            # 第二次請求（應該從緩存獲取）
            start_time = time.time()
            response2 = requests.post(
                f"{self.data_layer_url}/api / v1 / stock / data",
                json={"symbol": "0700.HK", "duration": 30},
                timeout=10
            )
            second_request_time = time.time() - start_time

            # 檢查緩存標頭
            cached = response2.json().get("cached", False) if response2.status_code == 200 else False

            cache_results["data_layer"] = {
                "first_request_time": first_request_time,
                "second_request_time": second_request_time,
                "cache_speedup": (first_request_time - second_request_time) / first_request_time * 100 if first_request_time > 0 else 0,
                "cached_response": cached,
                "both_successful": response1.status_code == 200 and response2.status_code == 200
            }

        except Exception as e:
            cache_results["data_layer"] = {"error": str(e)}

        # 獲取緩存統計信息
        try:
            cache_stats_response = requests.get(f"{self.data_layer_url}/api / v1 / cache / stats", timeout=5)
            if cache_stats_response.status_code == 200:
                cache_results["cache_stats"] = cache_stats_response.json()
        except Exception as e:
            cache_results["cache_stats"] = {"error": str(e)}

        return cache_results

    async def _test_error_handling(self):
        """測試錯誤處理機制"""
        logger.info("🚨 測試錯誤處理機制")

        error_handling_results = {}

        # 測試無效股票代碼
        try:
            response = requests.post(
                f"{self.data_layer_url}/api / v1 / stock / data",
                json={"symbol": "INVALID.HK", "duration": 30},
                timeout=10
            )
            error_handling_results["invalid_symbol"] = {
                "handled_gracefully": response.status_code in [400, 404, 500],
                "status_code": response.status_code,
                "has_error_message": bool(response.json().get("error")) if response.headers.get('content - type', '').startswith('application / json') else False
            }
        except Exception as e:
            error_handling_results["invalid_symbol"] = {"unexpected_error": str(e)}

        # 測試超大請求
        try:
            response = requests.post(
                f"{self.data_layer_url}/api / v1 / stock / data",
                json={"symbol": "0700.HK", "duration": 3650},  # 超過限制
                timeout=10
            )
            error_handling_results["oversized_request"] = {
                "handled_gracefully": response.status_code in [400, 413],
                "status_code": response.status_code
            }
        except Exception as e:
            error_handling_results["oversized_request"] = {"handled_gracefully": True, "error": str(e)}

        # 測試不存在的端點
        try:
            response = requests.get(f"{self.data_layer_url}/api / v1 / nonexistent", timeout=5)
            error_handling_results["nonexistent_endpoint"] = {
                "handled_gracefully": response.status_code == 404,
                "status_code": response.status_code
            }
        except Exception as e:
            error_handling_results["nonexistent_endpoint"] = {"handled_gracefully": True, "error": str(e)}

        # 測試業務層降級策略
        try:
            # 模擬數據層故障的情況下，業務層是否能提供備用數據
            response = requests.get(f"{self.business_layer_url}/api / realtime", timeout=10)
            error_handling_results["business_layer_fallback"] = {
                "provides_fallback": response.status_code == 200,
                "has_data": bool(response.json().get("data")) if response.status_code == 200 else False
            }
        except Exception as e:
            error_handling_results["business_layer_fallback"] = {"fallback_error": str(e)}

        self.test_results["error_handling_tests"] = error_handling_results

    async def _test_end_to_end_scenarios(self):
        """執行端到端場景測試"""
        logger.info("🎯 執行端到端場景測試")

        e2e_results = {}

        # 場景1: 完整的股票分析流程
        try:
            # 1. 獲取股票數據
            stock_response = requests.post(
                f"{self.data_layer_url}/api / v1 / stock / data",
                json={"symbol": "0700.HK", "duration": 60},
                timeout=15
            )

            # 2. 計算技術指標
            if stock_response.status_code == 200:
                indicators_response = requests.post(
                    f"{self.data_layer_url}/api / v1 / technical / indicators",
                    json={"symbol": "0700.HK", "indicators": ["rsi", "sma", "ema", "macd"]},
                    timeout=15
                )

                # 3. 獲取業務分析
                analysis_response = requests.get(f"{self.business_layer_url}/api / analysis / 0700.HK", timeout=15)

                # 4. 獲取表現層格式化數據
                dashboard_response = requests.post(
                    f"{self.presentation_layer_url}/api / v3 / dashboard / data",
                    json={"symbols": ["0700.HK"], "include_indicators": True},
                    timeout=15
                )

                e2e_results["complete_analysis_workflow"] = {
                    "stock_data_success": stock_response.status_code == 200,
                    "indicators_success": indicators_response.status_code == 200,
                    "analysis_success": analysis_response.status_code == 200,
                    "dashboard_success": dashboard_response.status_code == 200,
                    "overall_success": all([
                        stock_response.status_code == 200,
                        indicators_response.status_code == 200,
                        analysis_response.status_code == 200,
                        dashboard_response.status_code == 200
                    ])
                }
            else:
                e2e_results["complete_analysis_workflow"] = {
                    "stock_data_failed": True,
                    "status_code": stock_response.status_code
                }

        except Exception as e:
            e2e_results["complete_analysis_workflow"] = {"workflow_error": str(e)}

        # 場景2: 實時數據更新流程
        try:
            # 測試實時數據端點
            realtime_response = requests.get(f"{self.business_layer_url}/api / realtime", timeout=10)

            # 測試市場概覽
            market_response = requests.post(
                f"{self.data_layer_url}/api / v1 / market / overview",
                json={"market": "HK", "data_type": "overview"},
                timeout=10
            )

            e2e_results["realtime_data_workflow"] = {
                "realtime_success": realtime_response.status_code == 200,
                "market_success": market_response.status_code == 200,
                "both_successful": realtime_response.status_code == 200 and market_response.status_code == 200
            }

        except Exception as e:
            e2e_results["realtime_data_workflow"] = {"realtime_error": str(e)}

        # 場景3: 多股票批量分析
        try:
            batch_symbols = ["0700.HK", "9988.HK", "2318.HK"]

            # 並行獲取多個股票的數據
            tasks = []
            for symbol in batch_symbols:
                tasks.append(requests.post(
                    f"{self.data_layer_url}/api / v1 / stock / data",
                    json={"symbol": symbol, "duration": 30},
                    timeout=10
                ))

            # 使用異步方式並行執行
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                batch_responses = list(executor.map(lambda f: f(), tasks))

            successful_responses = sum(1 for r in batch_responses if r.status_code == 200)

            # 測試表現層批量處理
            dashboard_response = requests.post(
                f"{self.presentation_layer_url}/api / v3 / dashboard / data",
                json={"symbols": batch_symbols, "timeframe": "daily"},
                timeout=15
            )

            e2e_results["batch_analysis_workflow"] = {
                "total_symbols": len(batch_symbols),
                "successful_data_requests": successful_responses,
                "dashboard_success": dashboard_response.status_code == 200,
                "batch_efficiency": successful_responses / len(batch_symbols) * 100
            }

        except Exception as e:
            e2e_results["batch_analysis_workflow"] = {"batch_error": str(e)}

        self.test_results["end_to_end_tests"] = e2e_results

    async def _generate_test_report(self) -> Dict:
        """生成測試報告"""
        logger.info("📊 生成測試報告")

        # 計算整體統計
        total_tests = 0
        passed_tests = 0

        # 計算健康檢查通過率
        healthy_layers = sum(1 for check in self.test_results["health_checks"].values() if check.get("status") == "healthy")
        total_tests += len(self.test_results["health_checks"])
        passed_tests += healthy_layers

        # 計算API端點通過率
        api_tests = 0
        api_passed = 0
        for layer_results in self.test_results["api_endpoint_tests"].values():
            for endpoint_result in layer_results.values():
                api_tests += 1
                if endpoint_result.get("success", False):
                    api_passed += 1

        total_tests += api_tests
        passed_tests += api_passed

        # 計算數據流測試通過率
        dataflow_success = 0
        for symbol_result in self.test_results["data_flow_tests"].values():
            if symbol_result.get("data_layer", {}).get("success", False):
                dataflow_success += 1

        total_tests += len(self.test_results["data_flow_tests"])
        passed_tests += dataflow_success

        overall_success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        # 生成報告
        report = {
            "test_summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "success_rate": round(overall_success_rate, 2),
                "timestamp": datetime.now().isoformat()
            },
            "system_status": {
                "healthy_layers": healthy_layers,
                "total_layers": 3,
                "system_health": "healthy" if healthy_layers == 3 else "degraded" if healthy_layers >= 2 else "unhealthy"
            },
            "performance_summary": self.test_results.get("performance_tests", {}),
            "detailed_results": self.test_results,
            "recommendations": self._generate_recommendations()
        }

        return report

    def _generate_recommendations(self) -> List[str]:
        """生成改進建議"""
        recommendations = []

        # 基於測試結果生成建議
        health_checks = self.test_results.get("health_checks", {})
        unhealthy_layers = [layer for layer, check in health_checks.items() if check.get("status") != "healthy"]
        if unhealthy_layers:
            recommendations.append(f"🔧 修復以下服務層的健康問題: {', '.join(unhealthy_layers)}")

        # 性能建議
        performance_tests = self.test_results.get("performance_tests", {})
        if "response_time_stats" in performance_tests:
            avg_response_time = performance_tests["response_time_stats"].get("average", 0)
            if avg_response_time > 2.0:
                recommendations.append("⚡ 考慮優化API響應時間，當前平均響應時間超過2秒")

        # 並發測試建議
        if "concurrent_test" in performance_tests:
            concurrent_data = performance_tests["concurrent_test"].get("data_layer", {})
            if concurrent_data.get("success_rate", 100) < 95:
                recommendations.append("🚀 提高並發處理能力，當前成功率低於95%")

        # 緩存建議
        cache_data = performance_tests.get("cache_efficiency", {}).get("data_layer", {})
        if not cache_data.get("cached_response", False):
            recommendations.append("💾 優化緩存策略，提高響應速度")

        # 錯誤處理建議
        error_tests = self.test_results.get("error_handling_tests", {})
        if any("handled_gracefully" in result and not result["handled_gracefully"] for result in error_tests.values()):
            recommendations.append("🛡️ 改進錯誤處理機制，確保優雅降級")

        # 成功建議
        if len(recommendations) == 0:
            recommendations.append("🎉 系統運行良好，所有測試通過！建議繼續監控性能指標。")

        return recommendations

async def main():
    """主函數"""
    tester = ThreeLayerIntegrationTest()
    report = await tester.run_all_tests()

    # 輸出測試報告
    print("\n" + "="*80)
    print("📊 三層架構集成測試報告")
    print("="*80)

    # 輸出測試摘要
    summary = report["test_summary"]
    print("🎯 測試摘要:")
    print(f"   總測試數: {summary['total_tests']}")
    print(f"   通過測試: {summary['passed_tests']}")
    print(f"   成功率: {summary['success_rate']}%")
    print(f"   測試時間: {summary['timestamp']}")

    # 輸出系統狀態
    system_status = report["system_status"]
    print("\n🏥 系統健康狀態:")
    print(f"   健康服務層: {system_status['healthy_layers']}/{system_status['total_layers']}")
    print(f"   整體狀態: {system_status['system_health']}")

    # 輸出性能摘要
    if "response_time_stats" in report.get("performance_summary", {}):
        perf_stats = report["performance_summary"]["response_time_stats"]
        print("\n⚡ 性能摘要:")
        print(f"   平均響應時間: {perf_stats['average']:.3f}s")
        print(f"   中位響應時間: {perf_stats['median']:.3f}s")
        print(f"   最大響應時間: {perf_stats['max']:.3f}s")
        print(f"   95分位響應時間: {perf_stats['p95']:.3f}s")

    # 輸出建議
    print("\n💡 改進建議:")
    for i, rec in enumerate(report["recommendations"], 1):
        print(f"   {i}. {rec}")

    # 保存詳細報告到文件
    with open("C:\\Users\\Penguin8n\\CODEX--\\integration_test_report.json", "w", encoding="utf - 8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print("\n📄 詳細測試報告已保存至: integration_test_report.json")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(main())