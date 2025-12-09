#!/usr/bin/env python3
"""
香港政府數據源集成 - 簡化系統核心模塊
Hong Kong Government Data Sources Integration - Simplified System Core Module

優化版本，支持高性能緩存和批量處理
Optimized version with high-performance caching and batch processing
"""

import asyncio
import json
import logging
import time
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
import aiohttp
from dataclasses import dataclass, asdict

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class GovernmentDataConfig:
    """政府數據源配置"""
    name: str
    url: str
    data_type: str  # 'hibor', 'exchange_rate', 'monetary_base', etc.
    refresh_interval: str = "daily"
    priority: int = 1  # 1=high, 2=medium, 3=low

@dataclass
class DataCollectionResult:
    """數據收集結果"""
    source_name: str
    success: bool
    record_count: int
    collection_time: datetime
    error_message: Optional[str] = None
    data_quality_score: Optional[float] = None
    file_path: Optional[str] = None

class GovernmentDataCollector:
    """
    香港政府數據收集器
    專注於高質量的官方數據源集成
    """

    def __init__(self):
        self.data_sources = self._initialize_data_sources()
        self.cache = {}
        self.cache_timeout = 1800  # 30 minutes cache
        self.data_storage_path = Path("data/government")
        self.data_storage_path.mkdir(parents=True, exist_ok=True)
        self.session = None

    def _initialize_data_sources(self) -> List[GovernmentDataConfig]:
        """初始化香港政府數據源配置"""
        return [
            # HIBOR利率數據 (最高優先級)
            GovernmentDataConfig(
                name="hibor_rates",
                url="https://api.hkma.gov.hk/public/market-data-and-statistics/monthly-statistical-bulletin/er-ir/hk-interbank-ir-daily",
                data_type="hibor",
                refresh_interval="daily",
                priority=1
            ),

            # 匯率數據 (高優先級)
            GovernmentDataConfig(
                name="exchange_rates",
                url="https://api.hkma.gov.hk/public/market-data-and-statistics/monthly-statistical-bulletin/er-ir/er-eeri-daily",
                data_type="exchange_rate",
                refresh_interval="daily",
                priority=1
            ),

            # 貨幣基礎 (高優先級)
            GovernmentDataConfig(
                name="monetary_base",
                url="https://api.hkma.gov.hk/public/market-data-and-statistics/daily-monetary-statistics/daily-figures-monetary-base",
                data_type="monetary_base",
                refresh_interval="daily",
                priority=1
            ),

            # 銀行同業流動資金 (中優先級)
            GovernmentDataConfig(
                name="interbank_liquidity",
                url="https://api.hkma.gov.hk/public/market-data-and-statistics/daily-monetary-statistics/daily-figures-interbank-liquidity",
                data_type="liquidity",
                refresh_interval="daily",
                priority=2
            ),

            # 外汇基金票据及债券 (中優先級)
            GovernmentDataConfig(
                name="efbn_indicative",
                url="https://api.hkma.gov.hk/public/market-data-and-statistics/monthly-statistical-bulletin/efbn/efbn-yield-daily",
                data_type="efbn",
                refresh_interval="daily",
                priority=2
            ),

            # 人民币流動資金 (低優先級)
            GovernmentDataConfig(
                name="rmb_liquidity",
                url="https://api.hkma.gov.hk/public/market-data-and-statistics/daily-monetary-statistics/usage-rmb-liquidity-fac",
                data_type="rmb",
                refresh_interval="daily",
                priority=3
            )
        ]

    def _get_cache_key(self, source_name: str) -> str:
        """生成緩存鍵"""
        return f"gov_data_{source_name}"

    def _is_cache_valid(self, cache_key: str) -> bool:
        """檢查緩存是否有效"""
        if cache_key not in self.cache:
            return False

        cached_time = self.cache[cache_key].get('timestamp', 0)
        return (time.time() - cached_time) < self.cache_timeout

    async def _get_session(self) -> aiohttp.ClientSession:
        """獲取或創建HTTP會話"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            headers = {
                'User-Agent': 'HK-Quant-Government-Data-Collector/2.0',
                'Accept': 'application/json',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive'
            }
            self.session = aiohttp.ClientSession(timeout=timeout, headers=headers)
        return self.session

    async def collect_hkma_data(self, source_config: GovernmentDataConfig) -> DataCollectionResult:
        """
        收集HKMA數據
        基於已驗證的API端點和數據格式
        """
        cache_key = self._get_cache_key(source_config.name)

        # 檢查緩存
        if self._is_cache_valid(cache_key):
            logger.info(f"Using cached data for {source_config.name}")
            cached_result = self.cache[cache_key]['data']
            return cached_result

        start_time = time.time()
        result = DataCollectionResult(
            source_name=source_config.name,
            success=False,
            record_count=0,
            collection_time=datetime.now()
        )

        try:
            session = await self._get_session()

            # 根據數據類型設置API參數
            params = {}
            if source_config.data_type == "hibor":
                params = {"segment": "hibor.fixing"}
                logger.info(f"Fetching HIBOR data from HKMA API")
            elif source_config.data_type == "exchange_rate":
                logger.info(f"Fetching exchange rate data from HKMA API")
            else:
                params = {"offset": "0", "pagesize": "500"}
                logger.info(f"Fetching {source_config.data_type} data from HKMA API (max 500 records)")

            # 發送API請求
            async with session.get(source_config.url, params=params) as response:
                response.raise_for_status()
                response_time = (time.time() - start_time) * 1000

                logger.info(f"HKMA API response time: {response_time:.2f}ms")

                data = await response.json()

                # 解析HKMA API響應格式
                records = self._parse_hkma_response(data, source_config.data_type)

                if records:
                    # 數據質量評估
                    quality_score = self._assess_data_quality(records, source_config.data_type)

                    # 保存數據
                    file_path = await self._save_data(records, source_config.name)

                    result.success = True
                    result.record_count = len(records)
                    result.data_quality_score = quality_score
                    result.file_path = str(file_path)

                    logger.info(f"✅ {source_config.name}: {len(records)} records, quality: {quality_score:.2f}")

                    # 更新緩存
                    self.cache[cache_key] = {
                        'data': result,
                        'timestamp': time.time()
                    }

                else:
                    result.error_message = "No valid data returned from HKMA API"
                    logger.warning(f"⚠️ {source_config.name}: No valid data")

        except aiohttp.ClientError as e:
            result.error_message = f"Network error: {str(e)}"
            logger.error(f"❌ {source_config.name} network error: {e}")
        except json.JSONDecodeError as e:
            result.error_message = f"JSON parsing error: {str(e)}"
            logger.error(f"❌ {source_config.name} JSON error: {e}")
        except Exception as e:
            result.error_message = f"Unexpected error: {str(e)}"
            logger.error(f"❌ {source_config.name} unexpected error: {e}")

        return result

    def _parse_hkma_response(self, data: Dict[str, Any], data_type: str) -> List[Dict[str, Any]]:
        """
        解析HKMA API響應
        支持多種HKMA API響應格式
        """
        records = []

        try:
            # HKMA API可能返回不同的格式
            if "result" in data and "records" in data["result"]:
                records = data["result"]["records"]
                logger.info(f"Parsed result.records format: {len(records)} records")
            elif "datas" in data and "records" in data["datas"]:
                records = data["datas"]["records"]
                logger.info(f"Parsed datas.records format: {len(records)} records")
            elif "records" in data:
                records = data["records"]
                logger.info(f"Parsed direct records format: {len(records)} records")
            else:
                logger.warning(f"Unknown HKMA API response format for {data_type}")
                logger.debug(f"Response keys: {list(data.keys())}")
                return []

            # 根據數據類型進行字段標準化
            if data_type == "hibor" and records:
                for record in records:
                    # 標準化HIBOR字段名
                    if 'end_of_day' in record:
                        record['date'] = record.pop('end_of_day')
                    if 'ir_overnight' in record:
                        record['hibor_overnight'] = record.pop('ir_overnight')
                    record['data_type'] = 'hibor'
                    record['source'] = 'HKMA'

            elif data_type == "exchange_rate" and records:
                for record in records:
                    # 標準化匯率字段名
                    if 'end_of_day' in record:
                        record['date'] = record.pop('end_of_day')
                    if 'usd' in record:
                        record['hkd_usd_rate'] = record.pop('usd')
                    if 'cny' in record:
                        record['hkd_cny_rate'] = record.pop('cny')
                    record['data_type'] = 'exchange_rate'
                    record['source'] = 'HKMA'

            else:
                # 為其他數據類型添加通用字段
                for record in records:
                    record['data_type'] = data_type
                    record['source'] = 'HKMA'

            logger.info(f"Processed {len(records)} {data_type} records")
            return records

        except Exception as e:
            logger.error(f"Error parsing HKMA response for {data_type}: {e}")
            return []

    def _assess_data_quality(self, records: List[Dict[str, Any]], data_type: str) -> float:
        """
        評估數據質量
        返回0.0-1.0之間的質量評分
        """
        if not records:
            return 0.0

        try:
            quality_factors = []

            # 完整性檢查
            required_fields = ['date'] if data_type in ['hibor', 'exchange_rate'] else []
            completeness_score = 0.0

            if required_fields:
                complete_records = sum(
                    1 for record in records
                    if all(record.get(field) for field in required_fields)
                )
                completeness_score = complete_records / len(records)
            else:
                completeness_score = 1.0  # 無特殊字段要求

            quality_factors.append(completeness_score)

            # 及時性檢查 (最近7天的數據)
            try:
                recent_date = datetime.now() - timedelta(days=7)
                recent_records = 0

                for record in records:
                    date_str = record.get('date', '')
                    if date_str:
                        try:
                            record_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                            if record_date.date() >= recent_date.date():
                                recent_records += 1
                        except:
                            continue

                timeliness_score = min(recent_records / max(len(records), 1), 1.0)
                quality_factors.append(timeliness_score)
            except:
                quality_factors.append(0.5)  # 默認值

            # 數據一致性檢查
            if data_type == "hibor":
                # HIBOR利率應該在合理範圍內 (0-10%)
                valid_hibor = 0
                for record in records:
                    for key, value in record.items():
                        if 'hibor' in key.lower() and isinstance(value, (int, float)):
                            if 0 <= value <= 10:
                                valid_hibor += 1

                if any('hibor' in key.lower() for record in records for key in record.keys()):
                    consistency_score = valid_hibor / max(
                        sum(1 for record in records for key in record.keys() if 'hibor' in key.lower()), 1
                    )
                else:
                    consistency_score = 1.0
                quality_factors.append(consistency_score)

            elif data_type == "exchange_rate":
                # 匯率應該在合理範圍內
                valid_rates = 0
                total_rates = 0

                for record in records:
                    for key, value in record.items():
                        if ('rate' in key.lower() or 'usd' in key.lower() or 'cny' in key.lower()) \
                           and isinstance(value, (int, float)):
                            total_rates += 1
                            if 0.1 <= value <= 20:  # 合理匯率範圍
                                valid_rates += 1

                consistency_score = valid_rates / max(total_rates, 1)
                quality_factors.append(consistency_score)
            else:
                quality_factors.append(1.0)  # 其他數據類型默認良好

            # 計算總體質量評分
            overall_score = sum(quality_factors) / len(quality_factors)

            logger.info(f"Data quality assessment for {data_type}: {overall_score:.3f}")
            return round(overall_score, 3)

        except Exception as e:
            logger.error(f"Error assessing data quality for {data_type}: {e}")
            return 0.5  # 默認中等質量

    async def _save_data(self, records: List[Dict[str, Any]], source_name: str) -> Path:
        """
        保存數據到文件
        同時保存JSON和CSV格式
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 保存JSON格式
        json_filename = f"{source_name}_{timestamp}.json"
        json_filepath = self.data_storage_path / json_filename

        json_data = {
            "source": source_name,
            "collection_time": datetime.now().isoformat(),
            "record_count": len(records),
            "data": records
        }

        with open(json_filepath, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2, default=str)

        # 保存CSV格式
        if records:
            csv_filename = f"{source_name}_{timestamp}.csv"
            csv_filepath = self.data_storage_path / csv_filename

            df = pd.DataFrame(records)
            df.to_csv(csv_filepath, index=False, encoding='utf-8')

            logger.info(f"Data saved: {json_filepath}, {csv_filepath}")
        else:
            logger.info(f"Data saved: {json_filepath} (no records)")

        return json_filepath

    async def collect_all_data(self) -> List[DataCollectionResult]:
        """
        收集所有政府數據源
        按優先級順序執行
        """
        logger.info("🚀 Starting Hong Kong government data collection")

        # 按優先級排序
        sorted_sources = sorted(self.data_sources, key=lambda x: x.priority)

        results = []

        for source_config in sorted_sources:
            logger.info(f"Collecting data from {source_config.name} (priority: {source_config.priority})")

            result = await self.collect_hkma_data(source_config)
            results.append(result)

            # 在請求之間添加延遲以避免過於頻繁
            await asyncio.sleep(0.5)

        # 生成收集報告
        self._generate_collection_report(results)

        return results

    def _generate_collection_report(self, results: List[DataCollectionResult]):
        """生成數據收集報告"""
        successful_collections = [r for r in results if r.success]
        total_records = sum(r.record_count for r in successful_collections)
        average_quality = sum(r.data_quality_score or 0 for r in successful_collections) / len(successful_collections) if successful_collections else 0

        report = {
            "collection_time": datetime.now().isoformat(),
            "total_sources": len(results),
            "successful_collections": len(successful_collections),
            "total_records": total_records,
            "average_quality_score": round(average_quality, 3),
            "sources": [
                {
                    "name": r.source_name,
                    "success": r.success,
                    "record_count": r.record_count,
                    "quality_score": r.data_quality_score,
                    "error_message": r.error_message
                }
                for r in results
            ]
        }

        # 保存報告
        report_filename = f"government_data_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path = self.data_storage_path / report_filename

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)

        logger.info(f"📊 Collection completed: {len(successful_collections)}/{len(results)} successful, {total_records} total records")
        logger.info(f"📄 Report saved: {report_path}")

    async def get_latest_data(self, source_name: str, limit: int = 10) -> Optional[Dict[str, Any]]:
        """
        獲取指定數據源的最新數據
        優先使用緩存，其次使用本地文件
        """
        # 檢查緩存
        cache_key = self._get_cache_key(source_name)
        if self._is_cache_valid(cache_key):
            logger.info(f"Returning cached data for {source_name}")
            cached_data = self.cache[cache_key]['data']
            if cached_data.success and cached_data.file_path:
                with open(cached_data.file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    records = data.get('data', [])[-limit:] if limit > 0 else data.get('data', [])
                    return {
                        "source": source_name,
                        "cached": True,
                        "total_records": len(records),
                        "records": records
                    }

        # 從本地文件查找最新數據
        try:
            data_files = list(self.data_storage_path.glob(f"{source_name}_*.json"))
            if not data_files:
                return None

            # 按修改時間排序，獲取最新的
            latest_file = max(data_files, key=lambda x: x.stat().st_mtime)

            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                records = data.get('data', [])[-limit:] if limit > 0 else data.get('data', [])

                return {
                    "source": source_name,
                    "collection_time": data.get('collection_time'),
                    "total_records": data.get('record_count', 0),
                    "records": records,
                    "file_path": str(latest_file)
                }

        except Exception as e:
            logger.error(f"Error reading latest data for {source_name}: {e}")
            return None

    async def close(self):
        """關閉HTTP會話"""
        if self.session and not self.session.closed:
            await self.session.close()

# Global instance
government_collector = GovernmentDataCollector()

# Convenience functions
async def collect_hkma_data(source_name: str) -> Optional[DataCollectionResult]:
    """便捷函數：收集特定HKMA數據源"""
    for source_config in government_collector.data_sources:
        if source_config.name == source_name:
            return await government_collector.collect_hkma_data(source_config)
    return None

async def collect_all_government_data() -> List[DataCollectionResult]:
    """便捷函數：收集所有政府數據"""
    return await government_collector.collect_all_data()

async def get_latest_government_data(source_name: str, limit: int = 10) -> Optional[Dict[str, Any]]:
    """便捷函數：獲取最新政府數據"""
    return await government_collector.get_latest_data(source_name, limit)

if __name__ == "__main__":
    async def main():
        """測試代碼"""
        print("Testing Hong Kong Government Data Collector...")

        # 測試單個數據源
        print("\n1. Testing HIBOR data collection...")
        hibor_result = await collect_hkma_data("hibor_rates")
        if hibor_result and hibor_result.success:
            print(f"✅ HIBOR: {hibor_result.record_count} records, quality: {hibor_result.data_quality_score:.3f}")
        else:
            print(f"❌ HIBOR failed: {hibor_result.error_message if hibor_result else 'Unknown error'}")

        # 測試獲取最新數據
        print("\n2. Testing latest data retrieval...")
        latest_data = await get_latest_government_data("hibor_rates", 5)
        if latest_data:
            print(f"✅ Latest HIBOR data: {latest_data['total_records']} records")
            if latest_data['records']:
                print(f"Sample record: {latest_data['records'][0]}")
        else:
            print("❌ No latest data available")

        # 測試收集所有數據
        print("\n3. Testing all data collection...")
        all_results = await collect_all_government_data()
        successful = sum(1 for r in all_results if r.success)
        total_records = sum(r.record_count for r in all_results if r.success)
        print(f"✅ All data: {successful}/{len(all_results)} successful, {total_records} total records")

        # 清理
        await government_collector.close()
        print("\n✅ Test completed successfully!")

    # 運行測試
    asyncio.run(main())