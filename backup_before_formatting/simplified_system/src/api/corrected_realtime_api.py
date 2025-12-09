#!/usr/bin/env python3
"""
修正版實時香港政府數據API - 基於用戶提供的正確API信息
Corrected Real-time Hong Kong Government Data API
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

class CorrectedRealtimeAPI:
    """修正版實時政府數據API"""

    def __init__(self):
        # 基於用戶提供的正確API端點
        self.api_endpoints = {
            'monetary_base': {
                'name': '貨幣基礎每日數字',
                'url': 'https://api.hkma.gov.hk/public/market-data-and-statistics/daily-monetary-statistics/daily-figures-monetary-base',
                'provider': '香港金融管理局',
                'frequency': '每日',
                'format': 'JSON'
            },
            'hibor_rates': {
                'name': 'HIBOR利率',
                'url': 'https://api.hkma.gov.hk/public/market-data-and-statistics/monthly-statistical-bulletin/er/ir-er-dhk-daily-ihb',
                'provider': '香港金融管理局',
                'frequency': '每日',
                'format': 'JSON'
            },
            'exchange_rates': {
                'name': '匯率數據',
                'url': 'https://api.hkma.gov.hk/public/market-data-and-statistics/monthly-statistical-bulletin/er/ir-er-dhk-daily-ex',
                'provider': '香港金融管理局',
                'frequency': '每日',
                'format': 'JSON'
            }
        }

        self.request_timeout = 60
        self.max_records = 1000

    def fetch_monetary_base(self, limit: int = 1000) -> Optional[Dict[str, Any]]:
        """獲取貨幣基礎每日數字 - 最新1000條記錄"""
        try:
            endpoint = self.api_endpoints['monetary_base']
            url = endpoint['url']

            logger.info(f"Fetching {endpoint['name']} from {endpoint['provider']}")
            logger.info(f"URL: {url}")

            # 發送GET請求 - 不需要參數，API返回所有可用數據
            response = requests.get(
                url,
                timeout=self.request_timeout,
                headers={
                    'Accept': 'application/json',
                    'User-Agent': 'Mozilla/5.0 (compatible; QuantTradingSystem/1.0)'
                }
            )

            logger.info(f"Response Status: {response.status_code}")

            if response.status_code != 200:
                logger.error(f"HTTP Error {response.status_code}: {response.text}")
                return None

            response.raise_for_status()
            data = response.json()

            logger.info(f"Response keys: {list(data.keys())}")

            # 解析數據結構
            records = []
            if 'records' in data:
                logger.info(f"Found {len(data['records'])} records in API response")

                # 取最新記錄（倒序）
                recent_records = data['records'][:limit]

                for i, record in enumerate(recent_records):
                    try:
                        monetary_record = {
                            'date': record.get('end_of_date', record.get('date', '')),
                            'monetary_base': self._safe_float(record.get('monetary_base')),
                            'm1': self._safe_float(record.get('m1')),
                            'm2': self._safe_float(record.get('m2')),
                            'm3': self._safe_float(record.get('m3')),
                            'record_index': i
                        }
                        records.append(monetary_record)
                    except Exception as e:
                        logger.warning(f"Error parsing record {i}: {e}")
                        continue

            result = {
                'success': True,
                'data': records,
                'source': {
                    'provider': endpoint['provider'],
                    'name': endpoint['name'],
                    'url': endpoint['url'],
                    'frequency': endpoint['frequency'],
                    'format': endpoint['format']
                },
                'metadata': {
                    'total_records_available': len(data.get('records', [])),
                    'records_returned': len(records),
                    'request_limit': limit,
                    'fetch_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'response_time_ms': time.time() * 1000
                }
            }

            logger.info(f"Successfully fetched {len(records)} {endpoint['name']} records")
            return result

        except Exception as e:
            logger.error(f"Error fetching {endpoint['name']}: {e}")
            return None

    def fetch_hibor_rates(self, limit: int = 1000) -> Optional[Dict[str, Any]]:
        """獲取HIBOR利率數據 - 最新1000條記錄"""
        try:
            endpoint = self.api_endpoints['hibor_rates']
            url = endpoint['url']

            logger.info(f"Fetching {endpoint['name']} from {endpoint['provider']}")

            response = requests.get(
                url,
                timeout=self.request_timeout,
                headers={'Accept': 'application/json'}
            )

            if response.status_code != 200:
                logger.error(f"HTTP Error {response.status_code}")
                return None

            response.raise_for_status()
            data = response.json()

            records = []
            if 'records' in data:
                recent_records = data['records'][:limit]

                for i, record in enumerate(recent_records):
                    try:
                        hibor_record = {
                            'date': record.get('end_of_date', ''),
                            'overnight': self._safe_float(record.get('ir_overnight')),
                            '1_week': self._safe_float(record.get('ir_1w')),
                            '1_month': self._safe_float(record.get('ir_1m')),
                            '3_months': self._safe_float(record.get('ir_3m')),
                            '6_months': self._safe_float(record.get('ir_6m')),
                            '12_months': self._safe_float(record.get('ir_12m')),
                            'record_index': i
                        }
                        records.append(hibor_record)
                    except Exception as e:
                        logger.warning(f"Error parsing HIBOR record {i}: {e}")
                        continue

            result = {
                'success': True,
                'data': records,
                'source': {
                    'provider': endpoint['provider'],
                    'name': endpoint['name'],
                    'url': endpoint['url']
                },
                'metadata': {
                    'total_records_available': len(data.get('records', [])),
                    'records_returned': len(records),
                    'fetch_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            }

            logger.info(f"Successfully fetched {len(records)} HIBOR records")
            return result

        except Exception as e:
            logger.error(f"Error fetching HIBOR rates: {e}")
            return None

    def fetch_exchange_rates(self, limit: int = 1000) -> Optional[Dict[str, Any]]:
        """獲取匯率數據 - 最新1000條記錄"""
        try:
            endpoint = self.api_endpoints['exchange_rates']
            url = endpoint['url']

            logger.info(f"Fetching {endpoint['name']} from {endpoint['provider']}")

            response = requests.get(
                url,
                timeout=self.request_timeout,
                headers={'Accept': 'application/json'}
            )

            if response.status_code != 200:
                logger.error(f"HTTP Error {response.status_code}")
                return None

            response.raise_for_status()
            data = response.json()

            records = []
            if 'records' in data:
                recent_records = data['records'][:limit]

                for i, record in enumerate(recent_records):
                    try:
                        rate_record = {
                            'date': record.get('end_of_date', ''),
                            'usd_hkd': self._safe_float(record.get('usd_hkd')),
                            'cny_hkd': self._safe_float(record.get('cny_hkd')),
                            'eur_hkd': self._safe_float(record.get('eur_hkd')),
                            'gbp_hkd': self._safe_float(record.get('gbp_hkd')),
                            'jpy_hkd': self._safe_float(record.get('jpy_hkd')),
                            'record_index': i
                        }
                        records.append(rate_record)
                    except Exception as e:
                        logger.warning(f"Error parsing exchange rate record {i}: {e}")
                        continue

            result = {
                'success': True,
                'data': records,
                'source': {
                    'provider': endpoint['provider'],
                    'name': endpoint['name'],
                    'url': endpoint['url']
                },
                'metadata': {
                    'total_records_available': len(data.get('records', [])),
                    'records_returned': len(records),
                    'fetch_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            }

            logger.info(f"Successfully fetched {len(records)} exchange rate records")
            return result

        except Exception as e:
            logger.error(f"Error fetching exchange rates: {e}")
            return None

    def fetch_all_real_data(self, limit: int = 1000) -> Dict[str, Any]:
        """獲取所有真實數據 - 各1000條最新記錄"""
        logger.info("Starting comprehensive real data fetch...")

        results = {
            'fetch_session': {
                'start_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'limit_per_source': limit
            },
            'data_sources': {},
            'summary': {}
        }

        # 依序獲取各種數據
        fetch_functions = [
            ('monetary_base', self.fetch_monetary_base),
            ('hibor_rates', self.fetch_hibor_rates),
            ('exchange_rates', self.fetch_exchange_rates)
        ]

        successful_sources = 0
        total_records = 0

        for source_name, fetch_function in fetch_functions:
            try:
                logger.info(f"Fetching {source_name}...")
                data = fetch_function(limit)

                if data and data.get('success'):
                    results['data_sources'][source_name] = data
                    record_count = len(data.get('data', []))
                    total_records += record_count
                    successful_sources += 1

                    logger.info(f"✅ {source_name}: {record_count} records fetched successfully")

                    # 保存到文件
                    self._save_source_data(source_name, data)

                else:
                    logger.error(f"❌ {source_name}: Failed to fetch data")
                    results['data_sources'][source_name] = {
                        'success': False,
                        'error': 'Fetch failed'
                    }

            except Exception as e:
                logger.error(f"❌ {source_name}: Exception - {e}")
                results['data_sources'][source_name] = {
                    'success': False,
                    'error': str(e)
                }

        # 更新總結
        results['fetch_session']['end_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        results['summary'] = {
            'total_sources': len(fetch_functions),
            'successful_sources': successful_sources,
            'failed_sources': len(fetch_functions) - successful_sources,
            'total_records': total_records,
            'success_rate': f"{(successful_sources/len(fetch_functions)*100):.1f}%"
        }

        logger.info(f"Fetch complete: {successful_sources}/{len(fetch_functions)} sources, {total_records} total records")

        # 保存綜合結果
        self._save_comprehensive_results(results)

        return results

    def _save_source_data(self, source_name: str, data: Dict[str, Any]):
        """保存單個數據源到文件"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{source_name}_real_{timestamp}.json"
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
            filename = f"comprehensive_real_data_{timestamp}.json"
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

# 全局實例
corrected_api = CorrectedRealtimeAPI()

# 便捷函數
def get_real_monetary_base(limit: int = 1000) -> Optional[Dict[str, Any]]:
    """獲取真實貨幣基礎數據"""
    return corrected_api.fetch_monetary_base(limit)

def get_real_hibor_rates(limit: int = 1000) -> Optional[Dict[str, Any]]:
    """獲取真實HIBOR數據"""
    return corrected_api.fetch_hibor_rates(limit)

def get_all_real_data(limit: int = 1000) -> Dict[str, Any]:
    """獲取所有真實數據"""
    return corrected_api.fetch_all_real_data(limit)

if __name__ == "__main__":
    print("=== Corrected Real-time Hong Kong Government Data API ===")
    print("Fetching latest 1000 records from each data source...")
    print()

    # 獲取所有真實數據
    all_data = get_all_real_data(1000)

    # 顯示結果
    print("=== Fetch Results ===")
    print(f"Session: {all_data['fetch_session']['start_time']} - {all_data['fetch_session']['end_time']}")
    print(f"Summary: {all_data['summary']['successful_sources']}/{all_data['summary']['total_sources']} sources successful")
    print(f"Total Records: {all_data['summary']['total_records']}")
    print(f"Success Rate: {all_data['summary']['success_rate']}")
    print()

    # 詳細結果
    for source_name, source_data in all_data['data_sources'].items():
        if source_data.get('success'):
            metadata = source_data.get('metadata', {})
            source_info = source_data.get('source', {})
            print(f"✅ {source_name}:")
            print(f"   Provider: {source_info.get('provider', 'N/A')}")
            print(f"   Records: {metadata.get('records_returned', 0)}/{metadata.get('total_records_available', 0)}")
            if source_data.get('data'):
                print(f"   Date Range: {source_data['data'][0].get('date')} to {source_data['data'][-1].get('date')}")
        else:
            print(f"❌ {source_name}: {source_data.get('error', 'Unknown error')}")
        print()

    print("=== Usage Examples ===")
    print("from corrected_realtime_api import get_real_monetary_base, get_real_hibor_rates")
    print()
    print("# Get 1000 latest monetary base records")
    print("monetary_data = get_real_monetary_base(1000)")
    print("print(f'Got {len(monetary_data[\"data\"])} monetary base records')")
    print()
    print("# Get 1000 latest HIBOR records")
    print("hibor_data = get_real_hibor_rates(1000)")
    print("print(f'Got {len(hibor_data[\"data\"])} HIBOR records')")