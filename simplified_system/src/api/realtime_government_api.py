#!/usr / bin / env python3
"""
實時香港政府數據API - 獲取最新1000條真實數據
Real - time Hong Kong Government Data API - Fetch latest 1000 real records
"""

import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd
import requests

# Setup logging
logging.basicConfig(
    level = logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class RealTimeGovernmentAPI:
    """實時政府數據API - 直接從香港政府API獲取最新數據"""

    def __init__(self):
        # 真實香港政府API端點
        self.api_endpoints = {
            "hibor_rates": {
                "name": "HIBOR利率",
                "url": "https://api.hkma.gov.hk / public / market - data - and - statistics / monthly - statistical - bulletin / er / ir - er - dhk - daily - ihb",
                "enabled": True,
            },
            "exchange_rates": {
                "name": "匯率數據",
                "url": "https://api.hkma.gov.hk / public / market - data - and - statistics / monthly - statistical - bulletin / er / ir - er - dhk - daily - ex",
                "enabled": True,
            },
            "interbank_liquidity": {
                "name": "銀行同業流動資金",
                "url": "https://api.hkma.gov.hk / public / market - data - and - statistics / daily - monetary - statistics / daily - figures - interbank - liquidity",
                "enabled": True,
            },
            "monetary_base": {
                "name": "貨幣基礎",
                "url": "https://api.hkma.gov.hk / public / market - data - and - statistics / daily - monetary - statistics / daily - figures - monetary - base",
                "enabled": True,
            },
            "efbn_indicative": {
                "name": "外匯基金票据及债券",
                "url": "https://api.hkma.gov.hk / public / market - data - and - statistics / daily - monetary - statistics / efbn - indicative - price",
                "enabled": True,
            },
            "rmb_liquidity": {
                "name": "人民幣流動資金",
                "url": "https://api.hkma.gov.hk / public / market - data - and - statistics / daily - monetary - statistics / usage - rmb - liquidity - fac",
                "enabled": True,
            },
        }

        self.cache = {}
        self.cache_timeout = 1800  # 30分鐘緩存
        self.request_timeout = 45
        self.max_records = 1000  # 最大獲取記錄數

    def fetch_hibor_rates(self, days_back: int = 365) -> Optional[Dict[str, Any]]:
        """獲取最新HIBOR利率數據"""
        cache_key = f"hibor_rates_{days_back}"

        if self._is_cache_valid(cache_key):
            logger.info("Using cached HIBOR data")
            return self.cache[cache_key]["data"]

        try:
            endpoint = self.api_endpoints["hibor_rates"]

            # 計算日期範圍
            end_date = datetime.now()
            start_date = end_date - timedelta(days = days_back)

            # 香港政府API不需要from / to參數，直接獲取最新數據
            # API會返回最近的記錄，然後我們在客戶端進行日期過濾
            params = {}

            logger.info(f"Fetching HIBOR data from {endpoint['url']}")
            logger.info(f"Date range: {params['from']} to {params['to']}")

            # 發送API請求
            response = requests.get(
                endpoint["url"],
                params = params,
                timeout = self.request_timeout,
                headers={
                    "Accept": "application / json",
                    "User - Agent": "Mozilla / 5.0 (Windows NT 10.0; Win64; x64) AppleWebKit / 537.36",
                },
            )

            response.raise_for_status()
            data = response.json()

            # 解析HIBOR數據
            hibor_records = []
            if "records" in data and data["records"]:
                for record in data["records"][: self.max_records]:
                    hibor_record = {
                        "date": record.get("end_of_date", ""),
                        "overnight": self._safe_float(record.get("ir_overnight")),
                        "1_week": self._safe_float(record.get("ir_1w")),
                        "1_month": self._safe_float(record.get("ir_1m")),
                        "2_months": self._safe_float(record.get("ir_2m")),
                        "3_months": self._safe_float(record.get("ir_3m")),
                        "6_months": self._safe_float(record.get("ir_6m")),
                        "12_months": self._safe_float(record.get("ir_12m")),
                    }
                    hibor_records.append(hibor_record)

            result = {
                "success": True,
                "data": hibor_records,
                "source": "HKMA Real - time API",
                "api_url": endpoint["url"],
                "record_count": len(hibor_records),
                "date_range": {
                    "start": params["from"],
                    "end": params["to"],
                    "actual_records": len(hibor_records),
                },
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "collection_time_ms": time.time() * 1000,
            }

            # 更新緩存
            self.cache[cache_key] = {"data": result, "timestamp": time.time()}

            logger.info(
                f"Successfully fetched {len(hibor_records)} HIBOR records from HKMA API"
            )
            return result

        except Exception as e:
            logger.error(f"Error fetching HIBOR data from API: {e}")
            return None

    def fetch_exchange_rates(self, days_back: int = 365) -> Optional[Dict[str, Any]]:
        """獲取最新匯率數據"""
        cache_key = f"exchange_rates_{days_back}"

        if self._is_cache_valid(cache_key):
            logger.info("Using cached exchange rate data")
            return self.cache[cache_key]["data"]

        try:
            endpoint = self.api_endpoints["exchange_rates"]

            # 計算日期範圍
            end_date = datetime.now()
            start_date = end_date - timedelta(days = days_back)

            # 香港政府API不需要from / to參數
            params = {}

            logger.info(f"Fetching exchange rate data from {endpoint['url']}")

            response = requests.get(
                endpoint["url"],
                params = params,
                timeout = self.request_timeout,
                headers={"Accept": "application / json"},
            )

            response.raise_for_status()
            data = response.json()

            # 解析匯率數據
            rate_records = []
            if "records" in data and data["records"]:
                for record in data["records"][: self.max_records]:
                    rate_record = {
                        "date": record.get("end_of_date", ""),
                        "usd_hkd": self._safe_float(record.get("usd_hkd")),
                        "cny_hkd": self._safe_float(record.get("cny_hkd")),
                        "eur_hkd": self._safe_float(record.get("eur_hkd")),
                        "gbp_hkd": self._safe_float(record.get("gbp_hkd")),
                        "jpy_hkd": self._safe_float(record.get("jpy_hkd")),
                        "aud_hkd": self._safe_float(record.get("aud_hkd")),
                    }
                    rate_records.append(rate_record)

            result = {
                "success": True,
                "data": rate_records,
                "source": "HKMA Real - time API",
                "api_url": endpoint["url"],
                "record_count": len(rate_records),
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

            # 更新緩存
            self.cache[cache_key] = {"data": result, "timestamp": time.time()}

            logger.info(
                f"Successfully fetched {len(rate_records)} exchange rate records"
            )
            return result

        except Exception as e:
            logger.error(f"Error fetching exchange rate data from API: {e}")
            return None

    def fetch_monetary_base(self, days_back: int = 365) -> Optional[Dict[str, Any]]:
        """獲取最新貨幣基礎數據"""
        cache_key = f"monetary_base_{days_back}"

        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]["data"]

        try:
            endpoint = self.api_endpoints["monetary_base"]

            end_date = datetime.now()
            start_date = end_date - timedelta(days = days_back)

            # 香港政府API不需要from / to參數
            params = {}

            response = requests.get(
                endpoint["url"],
                params = params,
                timeout = self.request_timeout,
                headers={"Accept": "application / json"},
            )

            response.raise_for_status()
            data = response.json()

            # 解析貨幣基礎數據
            monetary_records = []
            if "records" in data and data["records"]:
                for record in data["records"][: self.max_records]:
                    monetary_record = {
                        "date": record.get("end_of_date", ""),
                        "monetary_base": self._safe_float(record.get("monetary_base")),
                        "m1": self._safe_float(record.get("m1")),
                        "m2": self._safe_float(record.get("m2")),
                        "m3": self._safe_float(record.get("m3")),
                    }
                    monetary_records.append(monetary_record)

            result = {
                "success": True,
                "data": monetary_records,
                "source": "HKMA Real - time API",
                "record_count": len(monetary_records),
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

            self.cache[cache_key] = {"data": result, "timestamp": time.time()}

            logger.info(
                f"Successfully fetched {len(monetary_records)} monetary base records"
            )
            return result

        except Exception as e:
            logger.error(f"Error fetching monetary base data from API: {e}")
            return None

    def fetch_all_data(self, days_back: int = 365) -> Dict[str, Any]:
        """獲取所有政府數據"""
        logger.info(f"Fetching all government data for last {days_back} days")

        results = {
            "fetch_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "days_back": days_back,
            "data_sources": {},
        }

        # 並行獲取各種數據
        data_fetchers = [
            ("hibor_rates", self.fetch_hibor_rates),
            ("exchange_rates", self.fetch_exchange_rates),
            ("monetary_base", self.fetch_monetary_base),
        ]

        for source_name, fetcher in data_fetchers:
            try:
                logger.info(f"Fetching {source_name}...")
                data = fetcher(days_back)
                if data:
                    results["data_sources"][source_name] = {
                        "success": True,
                        "record_count": data.get("record_count", 0),
                        "last_updated": data.get("last_updated"),
                        "data": data.get("data", []),
                    }
                    logger.info(
                        f"✅ {source_name}: {data.get('record_count', 0)} records"
                    )
                else:
                    results["data_sources"][source_name] = {
                        "success": False,
                        "error": "Failed to fetch data",
                    }
                    logger.error(f"❌ {source_name}: Failed to fetch data")
            except Exception as e:
                logger.error(f"❌ {source_name}: Exception - {e}")
                results["data_sources"][source_name] = {
                    "success": False,
                    "error": str(e),
                }

        # 統計總記錄數
        total_records = sum(
            source.get("record_count", 0)
            for source in results["data_sources"].values()
            if source.get("success")
        )

        results["summary"] = {
            "total_sources": len(data_fetchers),
            "successful_sources": len(
                [s for s in results["data_sources"].values() if s.get("success")]
            ),
            "total_records": total_records,
            "max_records_per_source": self.max_records,
        }

        logger.info(
            f"Fetch complete: {results['summary']['successful_sources']}/{results['summary']['total_sources']} sources, {total_records} total records"
        )

        return results

    def save_real_time_data(
        self, data: Dict[str, Any], filename_prefix: str = "realtime_gov_data"
    ):
        """保存實時數據到文件"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{filename_prefix}_{timestamp}.json"
            filepath = Path("simplified_system / data / government") / filename

            # 確保目錄存在
            filepath.parent.mkdir(parents = True, exist_ok = True)

            with open(filepath, "w", encoding="utf - 8") as f:
                json.dump(data, f, ensure_ascii = False, indent = 2)

            logger.info(f"Real - time data saved to: {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"Error saving real - time data: {e}")
            return None

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
realtime_gov_api = RealTimeGovernmentAPI()


# 便捷函數
def get_realtime_hibor(days_back: int = 365) -> Optional[Dict[str, Any]]:
    """獲取實時HIBOR數據"""
    return realtime_gov_api.fetch_hibor_rates(days_back)


def get_realtime_exchange_rates(days_back: int = 365) -> Optional[Dict[str, Any]]:
    """獲取實時匯率數據"""
    return realtime_gov_api.fetch_exchange_rates(days_back)


def get_realtime_all_data(days_back: int = 365) -> Dict[str, Any]:
    """獲取所有實時政府數據"""
    return realtime_gov_api.fetch_all_data(days_back)


if __name__ == "__main__":
    print("Testing Real - time Hong Kong Government Data API...")
    print("=" * 60)

    # 測試獲取所有數據
    all_data = get_realtime_all_data(365)  # 獲取最新一年數據

    print(f"Data Fetch Complete:")
    print(f"   Time: {all_data['fetch_time']}")
    print(f"   Days: {all_data['days_back']}")
    print(
        f"   Sources: {all_data['summary']['successful_sources']}/{all_data['summary']['total_sources']}"
    )
    print(f"   Total Records: {all_data['summary']['total_records']}")

    # 顯示各數據源詳情
    for source_name, source_data in all_data["data_sources"].items():
        if source_data.get("success"):
            print(
                f"   [OK] {source_name}: {source_data.get('record_count', 0)} records"
            )
        else:
            print(
                f"   [FAIL] {source_name}: {source_data.get('error', 'Unknown error')}"
            )

    # 保存數據
    saved_file = realtime_gov_api.save_real_time_data(all_data)
    if saved_file:
        print(f"Data saved to: {saved_file}")

    print("\nUsage Example:")
    print("from realtime_government_api import get_realtime_hibor")
    print("hibor_data = get_realtime_hibor(365)")
    print("print(f'Got {len(hibor_data[\"data\"])} HIBOR records')")
