#!/usr / bin / env python3
"""
增強版香港政府實時數據API系統
Enhanced Hong Kong Government Real - time Data API System

修復失效端點，增加數據範圍，提高穩定性
Fix broken endpoints, extend data range, improve stability
"""

import logging
import time
from datetime import datetime
from typing import Any, Dict, Optional

import requests

# Setup logging
logging.basicConfig(
    level = logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class EnhancedRealtimeAPI:
    """增強版實時政府數據API系統"""

    def __init__(self):
        # 修復後的香港政府API端點列表
        self.api_endpoints = {
            # 已驗證工作正常的端點
            "interbank_liquidity": {
                "name": "銀行同業流動資金",
                "url": "https://api.hkma.gov.hk / public / market - data - and - statistics / daily - monetary - statistics / daily - figures - interbank - liquidity",
                "category": "daily_monetary",
                "provider": "香港金融管理局",
                "status": "working",
            },
            "monetary_base": {
                "name": "貨幣基礎每日數字",
                "url": "https://api.hkma.gov.hk / public / market - data - and - statistics / daily - monetary - statistics / daily - figures - monetary - base",
                "category": "daily_monetary",
                "provider": "香港金融管理局",
                "status": "working",
            },
            "rmb_liquidity": {
                "name": "人民幣流動資金安排",
                "url": "https://api.hkma.gov.hk / public / market - data - and - statistics / daily - monetary - statistics / usage - rmb - liquidity - fac",
                "category": "daily_monetary",
                "provider": "香港金融管理局",
                "status": "working",
            },
            "economic_statistics": {
                "name": "經濟統計數據",
                "url": "https://api.hkma.gov.hk / public / market - data - and - statistics / monthly - statistical - bulletin / financial / economic - statistics",
                "category": "economic_data",
                "provider": "香港金融管理局",
                "status": "working",
            },
            # 修復後的端點 - 使用正確的URL格式
            "efbn_indicative": {
                "name": "外匯基金票据及债券價格",
                "url": "https://api.hkma.gov.hk / public / market - data - and - statistics / daily - monetary - statistics / efbn - indicative - price",
                "category": "daily_monetary",
                "provider": "香港金融管理局",
                "status": "testing",
                "alternative_urls": [
                    "https://api.hkma.gov.hk / public / market - data - and - statistics / daily - monetary - statistics / efbn - indicative - price?pagesize = 1000",
                    "https://api.hkma.gov.hk / public / market - data - and - statistics / daily - figures - efbn - indicative - price",
                ],
            },
            "efbn_closing": {
                "name": "外匯基金票据及债券收市價",
                "url": "https://api.hkma.gov.hk / public / market - data - and - statistics / daily - monetary - statistics / efbn - closing",
                "category": "daily_monetary",
                "provider": "香港金融管理局",
                "status": "testing",
                "alternative_urls": [
                    "https://api.hkma.gov.hk / public / market - data - and - statistics / daily - monetary - statistics / efbn - closing?pagesize = 1000",
                    "https://api.hkma.gov.hk / public / market - data - and - statistics / daily - figures - efbn - closing",
                ],
            },
            "hibor_rates": {
                "name": "HIBOR利率",
                "url": "https://api.hkma.gov.hk / public / market - data - and - statistics / monthly - statistical - bulletin / er / ir - er - dhk - daily - ihb",
                "category": "market_rates",
                "provider": "香港金融管理局",
                "status": "testing",
                "alternative_urls": [
                    "https://api.hkma.gov.hk / public / market - data - and - statistics / monthly - statistical - bulletin / er - ir / ir - er - dhk - daily - ihb?pagesize = 1000",
                    "https://api.hkma.gov.hk / public / market - data - and - statistics / interest - rates - hibor - daily",
                    "https://api.hkma.gov.hk / public / market - data - and - statistics / market - ir - hibor - daily",
                ],
            },
            "exchange_rates": {
                "name": "匯率數據",
                "url": "https://api.hkma.gov.hk / public / market - data - and - statistics / monthly - statistical - bulletin / er / ir - er - dhk - daily - ex",
                "category": "market_rates",
                "provider": "香港金融管理局",
                "status": "testing",
                "alternative_urls": [
                    "https://api.hkma.gov.hk / public / market - data - and - statistics / monthly - statistical - bulletin / er - ir / ir - er - dhk - daily - ex?pagesize = 1000",
                    "https://api.hkma.gov.hk / public / market - data - and - statistics / exchange - rates - daily",
                ],
            },
            "monetary_base_monthly": {
                "name": "貨幣基礎月度統計",
                "url": "https://api.hkma.gov.hk / public / market - data - and - statistics / monthly - statistical - bulletin / mo / mo - dm - mb",
                "category": "monthly_monetary",
                "provider": "香港金融管理局",
                "status": "testing",
                "alternative_urls": [
                    "https://api.hkma.gov.hk / public / market - data - and - statistics / monthly - statistical - bulletin / mo / mo - dm - mb?pagesize = 1000",
                    "https://api.hkma.gov.hk / public / market - data - and - statistics / monetary - base - monthly",
                ],
            },
            # 新增的穩定數據源
            "interest_rates": {
                "name": "利率統計",
                "url": "https://api.hkma.gov.hk / public / market - data - and - statistics / interest - rates / hkd - interbank - irate - daily",
                "category": "market_rates",
                "provider": "香港金融管理局",
                "status": "stable",
            },
            "monetary_statistics": {
                "name": "貨幣統計",
                "url": "https://api.hkma.gov.hk / public / market - data - and - statistics / monetary - statistics / ms - mb",
                "category": "daily_monetary",
                "provider": "香港金融管理局",
                "status": "stable",
            },
        }

        self.request_timeout = 60
        self.max_records = 1000
        self.cache = {}
        self.cache_timeout = 1800  # 30分鐘緩存
        self.retry_attempts = 3
        self.retry_delay = 2

    def fetch_api_data_with_retry(
        self, url: str, source_name: str, limit: int = 1000
    ) -> Optional[Dict[str, Any]]:
        """帶重試機制的API數據獲取"""

        for attempt in range(self.retry_attempts):
            try:
                logger.info(
                    f"Fetching {source_name} (attempt {attempt + 1}/{self.retry_attempts})"
                )
                logger.info(f"URL: {url}")

                # 發送API請求，增加額外的headers
                response = requests.get(
                    url,
                    timeout = self.request_timeout,
                    headers={
                        "Accept": "application / json",
                        "User - Agent": "Mozilla / 5.0 (compatible; EnhancedQuantSystem / 2.0)",
                        "Accept - Language": "en - US,en;q = 0.9,zh - HK;q = 0.8,zh;q = 0.7",
                        "Cache - Control": "no - cache",
                    },
                )

                logger.info(f"Response Status: {response.status_code}")

                if response.status_code == 200:
                    response.raise_for_status()
                    data = response.json()

                    # 記錄成功的URL
                    logger.info(f"Successfully fetched data from: {url}")
                    return data

                elif response.status_code == 400:
                    logger.warning(
                        f"HTTP 400 for {source_name}, trying alternative URLs if available"
                    )
                    break

                elif response.status_code == 404:
                    logger.warning(f"HTTP 404 for {source_name}, URL may not exist")
                    break

                else:
                    logger.error(
                        f"HTTP Error {response.status_code} for {source_name}: {response.text}"
                    )
                    if attempt < self.retry_attempts - 1:
                        time.sleep(self.retry_delay)
                        continue

            except requests.exceptions.RequestException as e:
                logger.error(f"Request exception for {source_name}: {e}")
                if attempt < self.retry_attempts - 1:
                    time.sleep(self.retry_delay * (attempt + 1))  # 指數退避
                    continue
                break

        return None

    def fetch_api_data(
        self, source_name: str, limit: int = 1000
    ) -> Optional[Dict[str, Any]]:
        """通用API數據獲取函數，支持替代URL嘗試"""
        if source_name not in self.api_endpoints:
            logger.error(f"Unknown data source: {source_name}")
            return None

        endpoint = self.api_endpoints[source_name]
        primary_url = endpoint["url"]

        # 檢查緩存
        cache_key = f"{source_name}_{limit}"
        if self._is_cache_valid(cache_key):
            logger.info(f"Using cached {source_name} data")
            return self.cache[cache_key]["data"]

        # 嘗試主URL
        data = self.fetch_api_data_with_retry(primary_url, source_name, limit)

        # 如果主URL失敗，嘗試替代URL
        if data is None and "alternative_urls" in endpoint:
            for alt_url in endpoint["alternative_urls"]:
                logger.info(f"Trying alternative URL for {source_name}: {alt_url}")
                data = self.fetch_api_data_with_retry(alt_url, source_name, limit)
                if data is not None:
                    break

        if data is None:
            logger.error(f"All attempts failed for {source_name}")
            return None

        # 解析API響應結構
        records = []
        if "result" in data and "records" in data["result"]:
            api_records = data["result"]["records"]
            logger.info(f"Found {len(api_records)} records in API response")

            # 取最新記錄
            recent_records = api_records[:limit]

            for i, record in enumerate(recent_records):
                try:
                    processed_record = self._process_record(record, source_name)
                    if processed_record:
                        processed_record["record_index"] = i
                        processed_record["source"] = source_name
                        records.append(processed_record)
                except Exception as e:
                    logger.warning(
                        f"Error processing record {i} for {source_name}: {e}"
                    )
                    continue

        result = {
            "success": True,
            "data": records,
            "source": {
                "name": endpoint["name"],
                "url": primary_url,
                "category": endpoint["category"],
                "provider": endpoint["provider"],
                "status": endpoint.get("status", "unknown"),
            },
            "metadata": {
                "total_records_available": len(
                    data.get("result", {}).get("records", [])
                ),
                "records_returned": len(records),
                "request_limit": limit,
                "fetch_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "response_size": len(str(data)),
                "api_success": data.get("header", {}).get("success", False),
            },
        }

        # 更新緩存
        self.cache[cache_key] = {"data": result, "timestamp": time.time()}

        logger.info(f"Successfully fetched {len(records)} {endpoint['name']} records")
        return result

    def _process_record(
        self, record: Dict[str, Any], source_name: str
    ) -> Optional[Dict[str, Any]]:
        """處理不同數據源的記錄格式"""
        processed = {
            "date": record.get("end_of_date", record.get("date", "")),
            "raw_data": record,
        }

        # 根據數據源處理特定字段
        if source_name == "monetary_base":
            processed.update(
                {
                    "monetary_base": self._safe_float(record.get("monetary_base")),
                    "m1": self._safe_float(record.get("m1")),
                    "m2": self._safe_float(record.get("m2")),
                    "m3": self._safe_float(record.get("m3")),
                }
            )

        elif source_name == "hibor_rates":
            processed.update(
                {
                    "overnight": self._safe_float(record.get("ir_overnight")),
                    "1_week": self._safe_float(record.get("ir_1w")),
                    "1_month": self._safe_float(record.get("ir_1m")),
                    "3_months": self._safe_float(record.get("ir_3m")),
                    "6_months": self._safe_float(record.get("ir_6m")),
                    "12_months": self._safe_float(record.get("ir_12m")),
                }
            )

        elif source_name == "exchange_rates":
            processed.update(
                {
                    "usd_hkd": self._safe_float(record.get("usd_hkd")),
                    "cny_hkd": self._safe_float(record.get("cny_hkd")),
                    "eur_hkd": self._safe_float(record.get("eur_hkd")),
                    "gbp_hkd": self._safe_float(record.get("gbp_hkd")),
                    "jpy_hkd": self._safe_float(record.get("jpy_hkd")),
                }
            )

        elif source_name == "interbank_liquidity":
            processed.update(
                {
                    "interbank_offer_rate": self._safe_float(
                        record.get("interbank_offer_rate")
                    ),
                    "liquidity_ratio": self._safe_float(record.get("liquidity_ratio")),
                }
            )

        elif source_name == "efbn_indicative":
            processed.update(
                {
                    "efb_7d": self._safe_float(record.get("efb_7d")),
                    "efb_30d": self._safe_float(record.get("efb_30d")),
                    "efb_91d": self._safe_float(record.get("efb_91d")),
                    "efb_182d": self._safe_float(record.get("efb_182d")),
                    "efn_2y": self._safe_float(record.get("efn_2y")),
                }
            )

        elif source_name == "economic_statistics":
            processed.update(
                {
                    "composite_cpi": self._safe_float(record.get("composite_cpi")),
                    "unemploy_rate": self._safe_float(record.get("unemploy_rate")),
                }
            )

        elif source_name == "interest_rates":
            processed.update(
                {
                    "hkd_interbank_rate": self._safe_float(record.get("rate")),
                    "rate_type": record.get("rate_type", "unknown"),
                }
            )

        elif source_name == "monetary_statistics":
            processed.update(
                {
                    "mb_hkd_billions": self._safe_float(record.get("mb_hkd_billions")),
                    "mb_growth_rate": self._safe_float(record.get("mb_growth_rate")),
                }
            )

        return processed

    def _safe_float(self, value) -> Optional[float]:
        """安全轉換為浮點數"""
        if value is None or value == "":
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def _is_cache_valid(self, cache_key: str) -> bool:
        """檢查緩存是否有效"""
        if cache_key not in self.cache:
            return False
        cached_time = self.cache[cache_key].get("timestamp", 0)
        return (time.time() - cached_time) < self.cache_timeout


# 全局實例
enhanced_api = EnhancedRealtimeAPI()


# 便捷函數
def fetch_enhanced_data(
    source_name: str, limit: int = 1000
) -> Optional[Dict[str, Any]]:
    """獲取增強版特定數據源"""
    return enhanced_api.fetch_api_data(source_name, limit)


if __name__ == "__main__":
    print("=" * 80)
    print("Enhanced Hong Kong Government Real - time Data API")
    print("增強版香港政府實時數據API系統")
    print("=" * 80)
    print("Testing enhanced API system...")
    print()

    # 測試單個數據源
    print("=== Testing Individual Sources ===")
    test_sources = ["monetary_base", "hibor_rates", "efbn_indicative"]

    for source in test_sources:
        print(f"\nTesting {source}...")
        data = fetch_enhanced_data(source, 100)
        if data and data.get("success"):
            print(f"[OK] {source}: {len(data.get('data', []))} records")
        else:
            print(f"[FAIL] {source}: Failed")

    print("\n=== USAGE EXAMPLES ===")
    print("from enhanced_realtime_api_fixed import fetch_enhanced_data")
    print()
    print("# Fetch enhanced monetary base data")
    print("monetary_data = fetch_enhanced_data('monetary_base', 1000)")
    print("print(f'Success: {monetary_data[\"success\"]}')")
