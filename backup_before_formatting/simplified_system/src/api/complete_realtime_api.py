#!/usr/bin/env python3
"""
完整的香港政府實時數據API系統
Complete Hong Kong Government Real-time Data API System

基於用戶提供的真實API端點，獲取最新1000條記錄
Based on user-provided real API endpoints to fetch latest 1000 records
"""

import requests
import json
import time
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CompleteRealtimeAPI:
    """完整的實時政府數據API系統"""

    def __init__(self):
        # 完整的香港政府API端點列表
        self.api_endpoints = {
            # 每日數據端點 (6個)
            'interbank_liquidity': {
                'name': '銀行同業流動資金',
                'url': 'https://api.hkma.gov.hk/public/market-data-and-statistics/daily-monetary-statistics/daily-figures-interbank-liquidity',
                'category': 'daily_monetary',
                'provider': '香港金融管理局'
            },
            'monetary_base': {
                'name': '貨幣基礎每日數字',
                'url': 'https://api.hkma.gov.hk/public/market-data-and-statistics/daily-monetary-statistics/daily-figures-monetary-base',
                'category': 'daily_monetary',
                'provider': '香港金融管理局'
            },
            'rmb_liquidity': {
                'name': '人民幣流動資金安排',
                'url': 'https://api.hkma.gov.hk/public/market-data-and-statistics/daily-monetary-statistics/usage-rmb-liquidity-fac',
                'category': 'daily_monetary',
                'provider': '香港金融管理局'
            },
            'efbn_indicative': {
                'name': '外匯基金票据及债券價格',
                'url': 'https://api.hkma.gov.hk/public/market-data-and-statistics/daily-monetary-statistics/efbn-indicative-price',
                'category': 'daily_monetary',
                'provider': '香港金融管理局'
            },
            'efbn_closing': {
                'name': '外匯基金票据及债券收市價',
                'url': 'https://api.hkma.gov.hk/public/market-data-and-statistics/daily-monetary-statistics/efbn-closing',
                'category': 'daily_monetary',
                'provider': '香港金融管理局'
            },

            # HIBOR和匯率數據
            'hibor_rates': {
                'name': 'HIBOR利率',
                'url': 'https://api.hkma.gov.hk/public/market-data-and-statistics/monthly-statistical-bulletin/er/ir-er-dhk-daily-ihb',
                'category': 'market_rates',
                'provider': '香港金融管理局'
            },
            'exchange_rates': {
                'name': '匯率數據',
                'url': 'https://api.hkma.gov.hk/public/market-data-and-statistics/monthly-statistical-bulletin/er/ir-er-dhk-daily-ex',
                'category': 'market_rates',
                'provider': '香港金融管理局'
            },

            # 貨幣基礎月度數據
            'monetary_base_monthly': {
                'name': '貨幣基礎月度統計',
                'url': 'https://api.hkma.gov.hk/public/market-data-and-statistics/monthly-statistical-bulletin/mo/mo-dm-mb',
                'category': 'monthly_monetary',
                'provider': '香港金融管理局'
            },

            # 經濟數據
            'economic_statistics': {
                'name': '經濟統計數據',
                'url': 'https://api.hkma.gov.hk/public/market-data-and-statistics/monthly-statistical-bulletin/financial/economic-statistics',
                'category': 'economic_data',
                'provider': '香港金融管理局'
            }
        }

        self.request_timeout = 60
        self.max_records = 1000
        self.cache = {}
        self.cache_timeout = 1800  # 30分鐘緩存

    def fetch_api_data(self, source_name: str, limit: int = 1000) -> Optional[Dict[str, Any]]:
        """通用API數據獲取函數"""
        if source_name not in self.api_endpoints:
            logger.error(f"Unknown data source: {source_name}")
            return None

        endpoint = self.api_endpoints[source_name]
        url = endpoint['url']

        # 檢查緩存
        cache_key = f"{source_name}_{limit}"
        if self._is_cache_valid(cache_key):
            logger.info(f"Using cached {source_name} data")
            return self.cache[cache_key]['data']

        try:
            logger.info(f"Fetching {endpoint['name']} from {endpoint['provider']}")
            logger.info(f"URL: {url}")

            # 發送API請求
            response = requests.get(
                url,
                timeout=self.request_timeout,
                headers={
                    'Accept': 'application/json',
                    'User-Agent': 'Mozilla/5.0 (compatible; QuantTradingSystem/1.0)'
                }
            )

            if response.status_code != 200:
                logger.error(f"HTTP Error {response.status_code} for {source_name}")
                return None

            response.raise_for_status()
            data = response.json()

            # 解析API響應結構
            # 結構: {'header': {...}, 'result': {'datasize': N, 'records': [...]}}
            records = []
            if 'result' in data and 'records' in data['result']:
                api_records = data['result']['records']
                logger.info(f"Found {len(api_records)} records in API response")

                # 取最新記錄
                recent_records = api_records[:limit]

                for i, record in enumerate(recent_records):
                    try:
                        processed_record = self._process_record(record, source_name)
                        if processed_record:
                            processed_record['record_index'] = i
                            processed_record['source'] = source_name
                            records.append(processed_record)
                    except Exception as e:
                        logger.warning(f"Error processing record {i} for {source_name}: {e}")
                        continue

            result = {
                'success': True,
                'data': records,
                'source': {
                    'name': endpoint['name'],
                    'url': endpoint['url'],
                    'category': endpoint['category'],
                    'provider': endpoint['provider']
                },
                'metadata': {
                    'total_records_available': len(data.get('result', {}).get('records', [])),
                    'records_returned': len(records),
                    'request_limit': limit,
                    'fetch_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'response_size': len(str(data)),
                    'api_success': data.get('header', {}).get('success', False)
                }
            }

            # 更新緩存
            self.cache[cache_key] = {
                'data': result,
                'timestamp': time.time()
            }

            logger.info(f"Successfully fetched {len(records)} {endpoint['name']} records")
            return result

        except Exception as e:
            logger.error(f"Error fetching {source_name}: {e}")
            return None

    def _process_record(self, record: Dict[str, Any], source_name: str) -> Optional[Dict[str, Any]]:
        """處理不同數據源的記錄格式"""
        processed = {
            'date': record.get('end_of_date', record.get('date', '')),
            'raw_data': record
        }

        # 根據數據源處理特定字段
        if source_name == 'monetary_base':
            processed.update({
                'monetary_base': self._safe_float(record.get('monetary_base')),
                'm1': self._safe_float(record.get('m1')),
                'm2': self._safe_float(record.get('m2')),
                'm3': self._safe_float(record.get('m3'))
            })

        elif source_name == 'hibor_rates':
            processed.update({
                'overnight': self._safe_float(record.get('ir_overnight')),
                '1_week': self._safe_float(record.get('ir_1w')),
                '1_month': self._safe_float(record.get('ir_1m')),
                '3_months': self._safe_float(record.get('ir_3m')),
                '6_months': self._safe_float(record.get('ir_6m')),
                '12_months': self._safe_float(record.get('ir_12m'))
            })

        elif source_name == 'exchange_rates':
            processed.update({
                'usd_hkd': self._safe_float(record.get('usd_hkd')),
                'cny_hkd': self._safe_float(record.get('cny_hkd')),
                'eur_hkd': self._safe_float(record.get('eur_hkd')),
                'gbp_hkd': self._safe_float(record.get('gbp_hkd')),
                'jpy_hkd': self._safe_float(record.get('jpy_hkd'))
            })

        elif source_name == 'interbank_liquidity':
            processed.update({
                'interbank_offer_rate': self._safe_float(record.get('interbank_offer_rate')),
                'liquidity_ratio': self._safe_float(record.get('liquidity_ratio'))
            })

        elif source_name == 'efbn_indicative':
            processed.update({
                'efb_7d': self._safe_float(record.get('efb_7d')),
                'efb_30d': self._safe_float(record.get('efb_30d')),
                'efb_91d': self._safe_float(record.get('efb_91d')),
                'efb_182d': self._safe_float(record.get('efb_182d')),
                'efn_2y': self._safe_float(record.get('efn_2y'))
            })

        elif source_name == 'economic_statistics':
            processed.update({
                'composite_cpi': self._safe_float(record.get('composite_cpi')),
                'unemploy_rate': self._safe_float(record.get('unemploy_rate'))
            })

        return processed

    def fetch_all_sources(self, limit: int = 1000) -> Dict[str, Any]:
        """獲取所有數據源的最新數據"""
        logger.info(f"Starting comprehensive fetch - {limit} records per source")

        results = {
            'fetch_session': {
                'start_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'limit_per_source': limit,
                'total_sources': len(self.api_endpoints)
            },
            'data_sources': {},
            'summary': {}
        }

        successful_sources = 0
        total_records = 0
        categories_summary = {}

        # 依序獲取所有數據源
        for source_name in self.api_endpoints.keys():
            try:
                logger.info(f"Fetching {source_name}...")
                data = self.fetch_api_data(source_name, limit)

                if data and data.get('success'):
                    results['data_sources'][source_name] = data
                    record_count = len(data.get('data', []))
                    total_records += record_count
                    successful_sources += 1

                    # 按類別統計
                    category = self.api_endpoints[source_name]['category']
                    if category not in categories_summary:
                        categories_summary[category] = {'count': 0, 'records': 0}
                    categories_summary[category]['count'] += 1
                    categories_summary[category]['records'] += record_count

                    logger.info(f"[OK] {source_name}: {record_count} records")

                    # 保存到單獨文件
                    self._save_source_data(source_name, data)

                else:
                    logger.error(f"[FAIL] {source_name}: Failed to fetch")
                    results['data_sources'][source_name] = {
                        'success': False,
                        'error': 'Fetch failed'
                    }

                # 添加延遲避免過於頻繁請求
                time.sleep(0.5)

            except Exception as e:
                logger.error(f"[FAIL] {source_name}: Exception - {e}")
                results['data_sources'][source_name] = {
                    'success': False,
                    'error': str(e)
                }

        # 更新總結
        results['fetch_session']['end_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        results['summary'] = {
            'successful_sources': successful_sources,
            'failed_sources': len(self.api_endpoints) - successful_sources,
            'total_records': total_records,
            'success_rate': f"{(successful_sources/len(self.api_endpoints)*100):.1f}%",
            'categories_summary': categories_summary
        }

        logger.info(f"Fetch complete: {successful_sources}/{len(self.api_endpoints)} sources, {total_records} total records")

        # 保存綜合結果
        self._save_comprehensive_results(results)

        return results

    def get_latest_records(self, source_name: str, count: int = 10) -> Optional[List[Dict[str, Any]]]:
        """獲取指定數據源的最新記錄"""
        data = self.fetch_api_data(source_name, count)
        if data and data.get('success'):
            return data.get('data', [])
        return None

    def _save_source_data(self, source_name: str, data: Dict[str, Any]):
        """保存單個數據源到文件"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{source_name}_latest_{timestamp}.json"
            filepath = Path("simplified_system/data/government") / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info(f"Saved {source_name} data to: {filepath}")

        except Exception as e:
            logger.error(f"Error saving {source_name} data: {e}")

    def _save_comprehensive_results(self, results: Dict[str, Any]):
        """保存綜合結果到文件"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"comprehensive_government_data_{timestamp}.json"
            filepath = Path("simplified_system/data/government") / filename

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)

            logger.info(f"Saved comprehensive results to: {filepath}")

        except Exception as e:
            logger.error(f"Error saving comprehensive results: {e}")

    def _safe_float(self, value) -> Optional[float]:
        """安全轉換為浮點數"""
        if value is None or value == '':
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def _is_cache_valid(self, cache_key: str) -> bool:
        """檢查緩存是否有效"""
        if cache_key not in self.cache:
            return False
        cached_time = self.cache[cache_key].get('timestamp', 0)
        return (time.time() - cached_time) < self.cache_timeout

# 全局實例
complete_api = CompleteRealtimeAPI()

# 便捷函數
def get_monetary_base(limit: int = 1000) -> Optional[Dict[str, Any]]:
    """獲取貨幣基礎數據"""
    return complete_api.fetch_api_data('monetary_base', limit)

def get_hibor_rates(limit: int = 1000) -> Optional[Dict[str, Any]]:
    """獲取HIBOR利率數據"""
    return complete_api.fetch_api_data('hibor_rates', limit)

def get_exchange_rates(limit: int = 1000) -> Optional[Dict[str, Any]]:
    """獲取匯率數據"""
    return complete_api.fetch_api_data('exchange_rates', limit)

def get_all_government_data(limit: int = 1000) -> Dict[str, Any]:
    """獲取所有政府數據"""
    return complete_api.fetch_all_sources(limit)

if __name__ == "__main__":
    print("=" * 80)
    print("Complete Hong Kong Government Real-time Data API")
    print("=" * 80)
    print("Fetching latest data from all confirmed real API endpoints...")
    print()

    # 獲取所有數據
    all_data = get_all_government_data(1000)

    # 顯示結果
    print("=== FETCH RESULTS ===")
    summary = all_data['summary']
    print(f"Session: {all_data['fetch_session']['start_time']} - {all_data['fetch_session']['end_time']}")
    print(f"Success Rate: {summary['success_rate']} ({summary['successful_sources']}/{summary['total_sources']})")
    print(f"Total Records: {summary['total_records']}")
    print()

    # 按類別顯示
    print("=== BY CATEGORY ===")
    for category, cat_data in summary.get('categories_summary', {}).items():
        print(f"{category}: {cat_data['count']} sources, {cat_data['records']} records")
    print()

    # 詳細結果
    print("=== DETAILED RESULTS ===")
    for source_name, source_data in all_data['data_sources'].items():
        if source_data.get('success'):
            metadata = source_data.get('metadata', {})
            source_info = source_data.get('source', {})
            records = source_data.get('data', [])

            print(f"[OK] {source_name}:")
            print(f"   Name: {source_info.get('name')}")
            print(f"   Category: {source_info.get('category')}")
            print(f"   Records: {len(records)}")
            if records:
                print(f"   Date Range: {records[0].get('date')} to {records[-1].get('date')}")
                print(f"   Latest Record Sample: {list(records[0].keys())}")
        else:
            print(f"[FAIL] {source_name}: {source_data.get('error', 'Unknown error')}")
        print()

    print("=== USAGE EXAMPLES ===")
    print("from complete_realtime_api import get_monetary_base, get_hibor_rates, get_all_government_data")
    print()
    print("# Get 1000 latest monetary base records")
    print("monetary_data = get_monetary_base(1000)")
    print("print(f'Got {len(monetary_data[\"data\"])} monetary base records')")
    print()
    print("# Get 500 latest HIBOR rates")
    print("hibor_data = get_hibor_rates(500)")
    print("print(f'Got {len(hibor_data[\"data\"])} HIBOR records')")
    print()
    print("# Get all government data")
    print("all_data = get_all_government_data(1000)")
    print("print(f'Success: {all_data[\"summary\"][\"success_rate\"]}')")