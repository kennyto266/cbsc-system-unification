#!/usr / bin / env python3
"""
香港政府金融数据爬虫系统
基于data.gov.hk的真实API数据源
使用requests + BeautifulSoup实现网页爬虫
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

import aiohttp
import requests

# Setup logging
logging.basicConfig(
    level = logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("hk_gov_data_crawler.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


@dataclass
class DataSource:
    """数据源配置"""

    name: str
    title: str
    url: str
    api_endpoint: str
    description: str
    data_type: str
    update_frequency: str


class HKGovDataCrawler:
    """香港政府数据爬虫"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User - Agent": "Mozilla / 5.0 (compatible; QuantSystem / 1.0)",
                "Accept": "application / json, text / plain, */*",
                "Accept - Language": "zh - TW,zh;q = 0.9,en;q = 0.8",
                "Connection": "keep - alive",
            }
        )

        # 基于MCP发现的8个HKMA每日金融数据集
        self.data_sources = [
            DataSource(
                name="hkd_forward_exchange_daily",
                title="市場數據與統計資料 - 金融數據月報 - 匯率及利率 - 港元遠期匯率 - 每日數字",
                url="https://data.gov.hk / tc - data / dataset / hk - hkma - t06 - t060203hkd - fer - daily",
                api_endpoint="https://api.hkma.gov.hk / public / market - data - and - statistics / monthly - statistical - bulletin / er - ir / hkd - fer - daily",
                description="此應用程式介面提供毎日的港元遠期匯率的數字",
                data_type="forward_exchange_rates",
                update_frequency="每月",
            ),
            DataSource(
                name="monetary_base_daily",
                title="市場數據與統計資料 - 金融數據月報 - 貨幣市場操作 - 貨幣基礎 - 每日數字",
                url="https://data.gov.hk / tc - data / dataset / hk - hkma - t07 - t070202monetary - base - daily",
                api_endpoint="https://api.hkma.gov.hk / public / market - data - and - statistics / daily - monetary - statistics / daily - figures - monetary - base",
                description="此應用程式介面提供毎日的貨幣基礎的數字",
                data_type="monetary_base",
                update_frequency="每月",
            ),
            DataSource(
                name="market_operation_daily",
                title="市場數據與統計資料 - 金融數據月報 - 貨幣市場操作 - 市場操作 - 每日數字",
                url="https://data.gov.hk / tc - data / dataset / hk - hkma - t07 - t070102market - operation - daily",
                api_endpoint="https://api.hkma.gov.hk / public / market - data - and - statistics / daily - monetary - statistics / daily - figures - monetary - base",
                description="此應用程式介面提供每日的貨幣市場操作的數字",
                data_type="market_operations",
                update_frequency="每月",
            ),
            DataSource(
                name="efbn_yield_daily",
                title="市場數據與統計資料 - 金融數據月報 - 外匯基金票據及債券 - 外匯基金票據及債券收益率 - 每日數字",
                url="https://data.gov.hk / tc - data / dataset / hk - hkma - t05 - t050303efbn - yield - daily",
                api_endpoint="https://api.hkma.gov.hk / public / market - data - and - statistics / daily - monetary - statistics / efbn - indicative - price",
                description="此應用程式介面提供每日的外匯基金票據及債券收益率的數字",
                data_type="efbn_yields",
                update_frequency="每月",
            ),
            DataSource(
                name="hk_interbank_ir_daily",
                title="市場數據與統計資料 - 金融數據月報 - 匯率及利率 - 香港銀行同業拆息 - 每日數字",
                url="https://data.gov.hk / tc - data / dataset / hk - hkma - t06 - t060303hk - interbank - ir - daily",
                api_endpoint="https://api.hkma.gov.hk / public / market - data - and - statistics / monthly - statistical - bulletin / er - ir / hk - interbank - ir - daily",
                description="此應用程式介面提供毎日的香港銀行同業拆息的數字",
                data_type="hibor_rates",
                update_frequency="每月",
            ),
            DataSource(
                name="discount_window_rates_daily",
                title="市場數據與統計資料 - 金融數據月報 - 貨幣市場操作 - 貼現窗及流動資金調節窗利率 - 每日數字",
                url="https://data.gov.hk / tc - data / dataset / hk - hkma - t07 - t070303disc - win - liquid - adj - win - rates - daily",
                api_endpoint="https://api.hkma.gov.hk / public / market - data - and - statistics / daily - monetary - statistics / daily - figures - interbank - liquidity",
                description="此應用程式介面提供毎日的貼現窗及流動資金調節窗利率的數字",
                data_type="discount_window_rates",
                update_frequency="每月",
            ),
            DataSource(
                name="exchange_rates_daily",
                title="市場數據與統計資料 - 金融數據月報 - 匯率及利率 - 匯率及港匯指數 - 每日數字",
                url="https://data.gov.hk / tc - data / dataset / hk - hkma - t06 - t060103er - eeri - daily",
                api_endpoint="https://api.hkma.gov.hk / public / market - data - and - statistics / monthly - statistical - bulletin / er - ir / er - eeri - daily",
                description="此應用程式介面提供每日的匯率及港匯指數的數字",
                data_type="exchange_rates",
                update_frequency="每月",
            ),
            DataSource(
                name="institutional_bond_daily",
                title="市場數據與統計資料 - 金融數據月報 - 政府債券計劃 - 機構債券發行計劃下政府債券的價格及收益率 - 每日數字",
                url="https://data.gov.hk / tc - data / dataset / hk - hkma - t09 - t090403instit - bond - price - yield - daily",
                api_endpoint="https://api.hkma.gov.hk / public / market - data - and - statistics / daily - monetary - statistics / efbn - closing",
                description="此應用程式介面提供毎日的機構債券發行計劃下政府債券的價格及收益率的數字",
                data_type="institutional_bonds",
                update_frequency="每月",
            ),
        ]

        self.data_cache = {}
        self.cache_dir = Path("data / government")
        self.cache_dir.mkdir(parents = True, exist_ok = True)

    async def fetch_data_from_api(self, source: DataSource) -> Dict[str, Any]:
        """从API获取数据"""
        logger.info(f"Fetching data from {source.name}...")

        try:
            # 添加API参数
            params = {
                "lang": "en",
                "limit": "1000",  # 获取更多数据
                "from": (datetime.now() - timedelta(days = 365)).strftime(
                    "%Y-%m-%d"
                ),  # 最近一年数据
            }

            async with aiohttp.ClientSession(
                timeout = aiohttp.ClientTimeout(total = 30)
            ) as session:
                async with session.get(source.api_endpoint, params = params) as response:
                    if response.status == 200:
                        data = await response.json()

                        result = {
                            "source": source.name,
                            "title": source.title,
                            "api_url": source.api_endpoint,
                            "description": source.description,
                            "data_type": source.data_type,
                            "collection_time": datetime.now().isoformat(),
                            "status": "success",
                            "record_count": self._count_records(data),
                            "data": data,
                        }

                        logger.info(
                            f"Successfully fetched {result['record_count']} records from {source.name}"
                        )
                        return result
                    else:
                        error_text = await response.text()
                        logger.error(
                            f"API error for {source.name}: {response.status} - {error_text[:200]}"
                        )
                        return {
                            "source": source.name,
                            "status": "error",
                            "error": f"HTTP {response.status}: {error_text[:200]}",
                            "collection_time": datetime.now().isoformat(),
                        }

        except Exception as e:
            logger.error(f"Exception fetching data from {source.name}: {str(e)}")
            return {
                "source": source.name,
                "status": "error",
                "error": str(e),
                "collection_time": datetime.now().isoformat(),
            }

    def _count_records(self, data: Dict) -> int:
        """计算记录数量"""
        try:
            # HKMA API通常返回 {"header": {...}, "result": [...]} 格式
            if isinstance(data, dict):
                if "result" in data and isinstance(data["result"], list):
                    return len(data["result"])
                elif "records" in data and isinstance(data["records"], list):
                    return len(data["records"])
                elif "data" in data and isinstance(data["data"], list):
                    return len(data["data"])
                else:
                    return 1  # 单个记录
            elif isinstance(data, list):
                return len(data)
            else:
                return 1
        except Exception:
            return 0

    async def fetch_all_data(self) -> List[Dict[str, Any]]:
        """获取所有数据源的数据"""
        logger.info("Starting to fetch all HK government financial data...")

        results = []

        # 并发获取所有数据
        tasks = [self.fetch_data_from_api(source) for source in self.data_sources]
        results = await asyncio.gather(*tasks, return_exceptions = True)

        # 处理异常
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(
                    f"Exception for {self.data_sources[i].name}: {str(result)}"
                )
                processed_results.append(
                    {
                        "source": self.data_sources[i].name,
                        "status": "error",
                        "error": str(result),
                        "collection_time": datetime.now().isoformat(),
                    }
                )
            else:
                processed_results.append(result)

        # 统计结果
        successful = sum(1 for r in processed_results if r.get("status") == "success")
        total_records = sum(r.get("record_count", 0) for r in processed_results)

        logger.info(
            f"Data collection completed: {successful}/{len(self.data_sources)} successful, {total_records} total records"
        )

        return processed_results

    def save_data_to_files(self, results: List[Dict[str, Any]]) -> None:
        """保存数据到文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 保存完整结果
        full_result_file = self.cache_dir / f"hk_gov_financial_data_{timestamp}.json"
        with open(full_result_file, "w", encoding="utf - 8") as f:
            json.dump(
                {
                    "collection_info": {
                        "timestamp": datetime.now().isoformat(),
                        "total_sources": len(self.data_sources),
                        "successful_sources": sum(
                            1 for r in results if r.get("status") == "success"
                        ),
                        "total_records": sum(r.get("record_count", 0) for r in results),
                    },
                    "sources": [
                        {
                            "name": source.name,
                            "title": source.title,
                            "api_endpoint": source.api_endpoint,
                            "data_type": source.data_type,
                        }
                        for source in self.data_sources
                    ],
                    "results": results,
                },
                f,
                indent = 2,
                ensure_ascii = False,
            )

        logger.info(f"Full results saved to: {full_result_file}")

        # 保存各个数据源的单独文件
        for result in results:
            if result.get("status") == "success":
                source_file = self.cache_dir / f"{result['source']}_{timestamp}.json"
                with open(source_file, "w", encoding="utf - 8") as f:
                    json.dump(result, f, indent = 2, ensure_ascii = False)
                logger.info(f"Source data saved to: {source_file}")

    def generate_summary_report(self, results: List[Dict[str, Any]]) -> str:
        """生成汇总报告"""
        successful_sources = [r for r in results if r.get("status") == "success"]
        failed_sources = [r for r in results if r.get("status") != "success"]

        report = f"""
# 香港政府金融数据爬虫报告
**采集时间 * *: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📊 采集结果汇总
- **数据源总数 * *: {len(self.data_sources)}
- **成功采集 * *: {len(successful_sources)}
- **失败采集 * *: {len(failed_sources)}
- **成功率 * *: {len(successful_sources)/len(self.data_sources)*100:.1f}%
- **总记录数 * *: {sum(r.get('record_count', 0) for r in results)}

## ✅ 成功数据源
"""

        for result in successful_sources:
            report += f"""
### {result['source']}
- **数据类型 * *: {result.get('data_type', 'N / A')}
- **记录数量 * *: {result.get('record_count', 0)}
- **API端点 * *: {result.get('api_url', 'N / A')}
- **采集时间 * *: {result.get('collection_time', 'N / A')}
"""

        if failed_sources:
            report += "\n## ❌ 失败数据源\n"
            for result in failed_sources:
                report += f"""
### {result['source']}
- **错误信息 * *: {result.get('error', 'Unknown error')}
- **采集时间 * *: {result.get('collection_time', 'N / A')}
"""

        report += f"""
## 📁 数据文件位置
- **完整结果 * *: data / government / hk_gov_financial_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json
- **分数据源文件 * *: data / government/[source_name]_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json

## 🔄 下次建议采集时间
{datetime.now() + timedelta(hours = 24):strftime('%Y-%m-%d %H:%M:%S')}
"""

        return report

    async def run_daily_collection(self) -> Dict[str, Any]:
        """执行每日数据采集"""
        start_time = time.time()

        logger.info("Starting daily HK government financial data collection")

        # 获取所有数据
        results = await self.fetch_all_data()

        # 保存到文件
        self.save_data_to_files(results)

        # 生成报告
        report = self.generate_summary_report(results)

        # 保存报告
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.cache_dir / f"collection_report_{timestamp}.md"
        with open(report_file, "w", encoding="utf - 8") as f:
            f.write(report)

        execution_time = time.time() - start_time

        summary = {
            "execution_time": execution_time,
            "total_sources": len(self.data_sources),
            "successful_sources": len(
                [r for r in results if r.get("status") == "success"]
            ),
            "total_records": sum(r.get("record_count", 0) for r in results),
            "success_rate": len([r for r in results if r.get("status") == "success"])
            / len(self.data_sources),
            "report_file": str(report_file),
            "timestamp": datetime.now().isoformat(),
        }

        logger.info(
            f"Daily collection completed in {execution_time:.2f}s: {summary['successful_sources']}/{summary['total_sources']} successful"
        )

        return {"summary": summary, "detailed_results": results, "report": report}


async def main():
    """主函数"""
    print("HK Government Financial Data Crawler")
    print("=" * 50)

    crawler = HKGovDataCrawler()

    try:
        # 执行数据采集
        result = await crawler.run_daily_collection()

        print(f"\nCollection Complete!")
        print(f"- Execution Time: {result['summary']['execution_time']:.2f}s")
        print(
            f"- Successful Sources: {result['summary']['successful_sources']}/{result['summary']['total_sources']}"
        )
        print(f"- Success Rate: {result['summary']['success_rate']:.1%}")
        print(f"- Total Records: {result['summary']['total_records']}")
        print(f"- Report File: {result['summary']['report_file']}")

        print(f"\n" + "=" * 50)
        print("HK Government Financial Data Collection Complete")

        return result

    except Exception as e:
        logger.error(f"Fatal error in main execution: {e}")
        print(f"Execution Failed: {str(e)}")
        return None


if __name__ == "__main__":
    # 运行异步主函数
    result = asyncio.run(main())
