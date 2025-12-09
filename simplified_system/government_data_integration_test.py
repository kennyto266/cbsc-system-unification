#!/usr / bin / env python3
"""
政府数据集成测试 - 验证8个修复版数据源的集成
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Any, Dict

import requests


class GovernmentDataIntegrationTest:
    """政府数据集成测试"""

    def __init__(self):
        # 使用修复版爬虫的完整8个数据源配置
        self.data_sources = [
            {
                "name": "hkd_forward_exchange_daily",
                "title": "港元遠期匯率",
                "api_endpoint": "https://api.hkma.gov.hk / public / market - data - and - statistics / monthly - statistical - bulletin / er - ir / hkd - fer - daily",
                "description": "每日港元遠期匯率數字",
                "data_type": "forward_exchange_rates",
                "extra_params": {},
            },
            {
                "name": "monetary_base_daily",
                "title": "貨幣基礎",
                "api_endpoint": "https://api.hkma.gov.hk / public / market - data - and - statistics / daily - monetary - statistics / daily - figures - monetary - base",
                "description": "每日貨幣基礎數字",
                "data_type": "monetary_base",
                "extra_params": {},
            },
            {
                "name": "market_operation_daily",
                "title": "市場操作",
                "api_endpoint": "https://api.hkma.gov.hk / public / market - data - and - statistics / daily - monetary - statistics / daily - figures - monetary - base",
                "description": "每日貨幣市場操作數字",
                "data_type": "market_operations",
                "extra_params": {},
            },
            {
                "name": "efbn_yield_daily",
                "title": "外匯基金票據及債券收益率",
                "api_endpoint": "https://api.hkma.gov.hk / public / market - data - and - statistics / daily - monetary - statistics / efbn - indicative - price",
                "description": "每日外匯基金票據及債券收益率數字",
                "data_type": "efbn_yields",
                "extra_params": {"segment": "IndicativePrice"},  # 修复参数
            },
            {
                "name": "hk_interbank_ir_daily",
                "title": "香港銀行同業拆息",
                "api_endpoint": "https://api.hkma.gov.hk / public / market - data - and - statistics / monthly - statistical - bulletin / er - ir / hk - interbank - ir - daily",
                "description": "每日香港銀行同業拆息數字",
                "data_type": "hibor_rates",
                "extra_params": {},
            },
            {
                "name": "discount_window_rates_daily",
                "title": "貼現窗利率",
                "api_endpoint": "https://api.hkma.gov.hk / public / market - data - and - statistics / daily - monetary - statistics / daily - figures - interbank - liquidity",
                "description": "每日貼現窗及流動資金調節窗利率數字",
                "data_type": "discount_window_rates",
                "extra_params": {},
            },
            {
                "name": "exchange_rates_daily",
                "title": "匯率及港匯指數",
                "api_endpoint": "https://api.hkma.gov.hk / public / market - data - and - statistics / monthly - statistical - bulletin / er - ir / er - eeri - daily",
                "description": "每日匯率及港匯指數數字",
                "data_type": "exchange_rates",
                "extra_params": {},
            },
            {
                "name": "institutional_bond_daily",
                "title": "機構債券",
                "api_endpoint": "https://api.hkma.gov.hk / public / market - data - and - statistics / daily - monetary - statistics / efbn - closing",
                "description": "每日機構債券發行計劃下政府債券的價格及收益率數字",
                "data_type": "institutional_bonds",
                "extra_params": {"segment": "Bills"},  # 修复参数
            },
        ]

        self.test_results = {}

    async def test_single_api(self, source: Dict[str, Any]) -> Dict[str, Any]:
        """测试单个API"""
        print(f"Testing {source['name']}: {source['title']}")
        start_time = time.time()

        try:
            # 基础参数
            params = {
                "lang": "en",
                "limit": "5",  # 减少数据量用于测试
                "from": (datetime.now() - timedelta(days = 30)).strftime("%Y-%m-%d"),
            }

            # 添加额外参数（如segment）
            if source.get("extra_params"):
                params.update(source["extra_params"])
                print(f"  - Using extra params: {source['extra_params']}")

            # 发送请求
            response = requests.get(
                source["api_endpoint"],
                params = params,
                timeout = 30,
                headers={"Accept": "application / json"},
            )

            execution_time = time.time() - start_time

            if response.status_code == 200:
                data = response.json()

                # 计算记录数
                record_count = self._count_records(data)

                print(
                    f"  [+] SUCCESS - {record_count} records in {execution_time:.2f}s"
                )

                return {
                    "status": "success",
                    "status_code": response.status_code,
                    "record_count": record_count,
                    "execution_time": execution_time,
                    "params_used": params,
                    "data_sample": (
                        data
                        if record_count <= 2
                        else {
                            "records_sample": data.get("result", {}).get("records", [])[
                                :2
                            ]
                        }
                    ),
                }
            else:
                error_text = response.text[:200]
                print(f"  [-] FAILED - HTTP {response.status_code}: {error_text}")

                return {
                    "status": "error",
                    "status_code": response.status_code,
                    "error": f"HTTP {response.status_code}: {error_text}",
                    "execution_time": execution_time,
                    "params_used": params,
                }

        except Exception as e:
            execution_time = time.time() - start_time
            print(f"  [!] EXCEPTION - {str(e)} in {execution_time:.2f}s")

            return {
                "status": "exception",
                "error": str(e),
                "execution_time": execution_time,
                "params_used": params,
            }

    def _count_records(self, data: Dict) -> int:
        """计算记录数量"""
        try:
            if isinstance(data, dict):
                if "result" in data:
                    result = data["result"]
                    if isinstance(result, dict) and "records" in result:
                        return len(result["records"])
                    elif isinstance(result, list):
                        return len(result)
                elif "records" in data:
                    return len(data["records"])
                elif "data" in data:
                    return len(data["data"])
                else:
                    return 1
            elif isinstance(data, list):
                return len(data)
            else:
                return 1
        except Exception:
            return 0

    async def run_all_tests(self) -> Dict[str, Any]:
        """运行所有API测试"""
        print("=" * 80)
        print("GOVERNMENT DATA INTEGRATION TEST - 8 DATA SOURCES")
        print("=" * 80)

        start_time = time.time()
        results = {}

        # 并发测试所有API
        tasks = [self.test_single_api(source) for source in self.data_sources]
        test_results = await asyncio.gather(*tasks, return_exceptions = True)

        # 处理结果
        for i, (source, result) in enumerate(zip(self.data_sources, test_results)):
            if isinstance(result, Exception):
                print(f"\nException for {source['name']}: {str(result)}")
                results[source["name"]] = {
                    "status": "exception",
                    "error": str(result),
                    "execution_time": 0,
                }
            else:
                results[source["name"]] = result
                # 添加源信息
                results[source["name"]]["source_info"] = {
                    "name": source["name"],
                    "title": source["title"],
                    "data_type": source["data_type"],
                    "api_endpoint": source["api_endpoint"],
                }

        # 统计结果
        total_time = time.time() - start_time
        successful = sum(1 for r in results.values() if r.get("status") == "success")
        failed = len(results) - successful
        total_records = sum(r.get("record_count", 0) for r in results.values())

        # 详细统计
        status_distribution = {}
        for result in results.values():
            status = result.get("status", "unknown")
            status_distribution[status] = status_distribution.get(status, 0) + 1

        # 生成综合报告
        report = {
            "test_info": {
                "timestamp": datetime.now().isoformat(),
                "total_execution_time": total_time,
                "total_data_sources": len(self.data_sources),
            },
            "results_summary": {
                "successful_sources": successful,
                "failed_sources": failed,
                "success_rate": successful / len(self.data_sources) * 100,
                "total_records_collected": total_records,
                "status_distribution": status_distribution,
            },
            "detailed_results": results,
            "data_sources_config": [
                {
                    "name": src["name"],
                    "title": src["title"],
                    "data_type": src["data_type"],
                    "endpoint": src["api_endpoint"],
                    "extra_params": src.get("extra_params", {}),
                }
                for src in self.data_sources
            ],
        }

        # 打印摘要
        print("\n" + "=" * 80)
        print("INTEGRATION TEST SUMMARY")
        print("=" * 80)
        print(f"Total Data Sources: {len(self.data_sources)}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {successful / len(self.data_sources) * 100:.1f}%")
        print(f"Total Records: {total_records}")
        print(f"Execution Time: {total_time:.2f}s")
        print(f"Avg Time per Source: {total_time / len(self.data_sources):.2f}s")

        if successful == len(self.data_sources):
            print("\n * ** PERFECT INTEGRATION! All 8 data sources working correctly.")
            print(
                "[+] System ready for quantitative trading with real government data."
            )
        elif successful >= 6:
            print(
                f"\n[+] GOOD INTEGRATION! {successful}/{len(self.data_sources)} sources working."
            )
            print("[!] Consider fixing failed sources for full coverage.")
        else:
            print(
                f"\n[!] INTEGRATION ISSUES! Only {successful}/{len(self.data_sources)} sources working."
            )
            print("[!] Requires immediate attention.")

        return report

    def save_report(self, report: Dict[str, Any]) -> str:
        """保存测试报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"government_data_integration_report_{timestamp}.json"

        with open(report_file, "w", encoding="utf - 8") as f:
            json.dump(report, f, indent = 2, ensure_ascii = False)

        print(f"\nDetailed report saved to: {report_file}")
        return report_file


async def main():
    """主函数"""
    tester = GovernmentDataIntegrationTest()

    # 运行集成测试
    report = await tester.run_all_tests()

    # 保存报告
    report_file = tester.save_report(report)

    return report, report_file


if __name__ == "__main__":
    report, report_file = asyncio.run(main())
    print(f"\nGovernment data integration test completed!")
    print(f"Report file: {report_file}")
