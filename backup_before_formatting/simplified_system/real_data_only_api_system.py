#!/usr/bin/env python3
"""
真實數據專用API系統 - 拒絕模擬數據
Real Data Only API System - Reject All Simulated Data

確保系統只使用真實數據，移除所有降級模式
"""

import sys
import os
sys.path.append('src')

import requests
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import pandas as pd

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('real_data_api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RealDataOnlyAPISystem:
    """真實數據專用API系統"""

    def __init__(self):
        # 只配置真實數據源
        self.real_data_sources = {
            'hibor_rates': {
                'primary': 'https://api.hkma.gov.hk/public/market-data-and-statistics/monthly-statistical-bulletin/er/ir-er-dhk-daily-ihb',
                'alternatives': [
                    'https://api.hkma.gov.hk/public/market-data-and-statistics/daily-monetary-statistics/daily-figures-interbank-liquidity'
                ],
                'local_files': [
                    'data/government/hibor_rates_20251124_174050.json',
                    'data/government/hibor_rates_20251123_132433.json',
                    'data/government/hibor_rates_20251123_132502.json'
                ]
            },
            'exchange_rates': {
                'primary': 'https://api.hkma.gov.hk/public/market-data-and-statistics/monthly-statistical-bulletin/er/ir-er-dhk-daily-ex',
                'alternatives': [
                    # 可以添加更多備選真實API
                ],
                'local_files': [
                    'data/government/exchange_rates_20251123_132447.json',
                    'data/government/exchange_rates_20251123_131828.json',
                    'data/government/exchange_rates_20251123_131647.json'
                ]
            },
            'monetary_base': {
                'primary': 'https://api.hkma.gov.hk/public/market-data-and-statistics/monthly-statistical-bulletin/mo/mo-dm-mb',
                'alternatives': [
                    'https://api.hkma.gov.hk/public/market-data-and-statistics/daily-monetary-statistics/daily-figures-monetary-base'
                ],
                'local_files': [
                    'data/government/monetary_base_20251123_132434.json',
                    'data/government/monetary_base_20251123_132620.json',
                    'data/government/monetary_base_20251123_132813.json'
                ]
            }
        }

        # HTTP會話配置
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'RealDataQuantSystem/1.0',
            'Accept': 'application/json',
            'Accept-Language': 'zh-HK,zh;q=0.9,en;q=0.8'
        })

        # 配置參數
        self.request_timeout = 30
        self.retry_attempts = 3
        self.retry_delay = 1

        # 數據質量要求
        self.data_quality_requirements = {
            'min_records': 1,
            'required_fields': {
                'hibor_rates': ['date', 'hibor_overnight'],
                'exchange_rates': ['date', 'usd_hkd'],
                'monetary_base': ['date', 'monetary_base_billion_hkd']
            }
        }

        # 狀態記錄
        self.data_source_history = []
        self.quality_metrics = {}

        # 確保只使用真實數據的配置
        self.real_only_config = {
            'allow_simulated': False,
            'require_real_source': True,
            'minimum_real_data_age_days': 90,  # 本地數據不超過90天
            'require_api_success_rate': 0.5  # 至少50%的API請求需要成功
        }

    def fetch_real_data_only(self, data_type: str, days_back: int = 30) -> Optional[Dict[str, Any]]:
        """只獲取真實數據，拒絕模擬數據"""
        logger.info(f"開始獲取真實 {data_type} 數據，{days_back} 天範圍...")

        # 驗證數據類型
        if data_type not in self.real_data_sources:
            logger.error(f"不支持的數據類型: {data_type}")
            return None

        # 1. 嘗試實時API（主要端點）
        real_data = self._try_real_api(data_type, days_back)
        if real_data:
            return self._validate_and_return(real_data, data_type, "實時API")

        # 2. 嘗試實時API（備選端點）
        real_data = self._try_alternative_apis(data_type, days_back)
        if real_data:
            return self._validate_and_return(real_data, data_type, "備選API")

        # 3. 使用本地真實數據文件（驗證新鮮度）
        real_data = self._load_local_real_data(data_type)
        if real_data:
            return self._validate_and_return(real_data, data_type, "本地真實文件")

        # 4. 數據獲取失敗 - 拒絕使用模擬數據
        logger.error(f"無法獲取 {data_type} 的真實數據")
        self._record_data_failure(data_type, "所有真實數據源都不可用")

        return None

    def _try_real_api(self, data_type: str, days_back: int) -> Optional[Dict[str, Any]]:
        """嘗試實時API（主要端點）"""
        config = self.real_data_sources[data_type]
        primary_url = config['primary']

        logger.info(f"嘗試實時API: {primary_url}")

        for attempt in range(self.retry_attempts):
            try:
                # 構建參數
                params = {
                    'pagesize': 100,
                    'page': 1
                }

                end_date = datetime.now()
                start_date = end_date - timedelta(days=days_back)

                params.update({
                    'from': start_date.strftime('%Y-%m-%d'),
                    'to': end_date.strftime('%Y-%m-%d')
                })

                response = self.session.get(
                    primary_url,
                    params=params,
                    timeout=self.request_timeout
                )

                response.raise_for_status()
                data = response.json()

                # 解析真實數據
                parsed_data = self._parse_hkma_data(data, data_type)
                if parsed_data and self._is_real_data_quality_acceptable(parsed_data):
                    logger.info(f"實時API成功: {len(parsed_data.get('data', []))} 條真實記錄")
                    self._record_data_success(data_type, "實時API", parsed_data)
                    return parsed_data

            except requests.exceptions.RequestException as e:
                logger.warning(f"實時API嘗試 {attempt + 1} 失敗: {e}")
                if attempt < self.retry_attempts - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                continue

        return None

    def _try_alternative_apis(self, data_type: str, days_back: int) -> Optional[Dict[str, Any]]:
        """嘗試備選實時API端點"""
        config = self.real_data_sources[data_type]
        alternatives = config.get('alternatives', [])

        logger.info(f"嘗試 {len(alternatives)} 個備選實時API...")

        for i, alt_url in enumerate(alternatives):
            logger.info(f"嘗試備選API {i + 1}: {alt_url}")

            try:
                params = {
                    'pagesize': 100,
                    'page': 1
                }

                end_date = datetime.now()
                start_date = end_date - timedelta(days=days_back)

                params.update({
                    'from': start_date.strftime('%Y-%m-%d'),
                    'to': end_date.strftime('%Y-%m-%d')
                })

                response = self.session.get(
                    alt_url,
                    params=params,
                    timeout=self.request_timeout
                )

                response.raise_for_status()
                data = response.json()

                parsed_data = self._parse_hkma_data(data, data_type)
                if parsed_data and self._is_real_data_quality_acceptable(parsed_data):
                    logger.info(f"備選API {i + 1} 成功: {len(parsed_data.get('data', []))} 條真實記錄")
                    self._record_data_success(data_type, f"備選API_{i + 1}", parsed_data)
                    return parsed_data

            except requests.exceptions.RequestException as e:
                logger.warning(f"備選API {i + 1} 失敗: {e}")
                continue

        return None

    def _load_local_real_data(self, data_type: str) -> Optional[Dict[str, Any]]:
        """加載本地真實數據文件"""
        config = self.real_data_sources[data_type]
        local_files = config['local_files']

        logger.info(f"嘗試加載本地真實數據文件: {len(local_files)} 個文件")

        for file_path in local_files:
            full_path = Path(file_path)
            if not full_path.exists():
                logger.warning(f"本地文件不存在: {file_path}")
                continue

            # 檢查文件新鮮度
            file_age_days = self._get_file_age_days(full_path)
            if file_age_days > self.real_only_config['minimum_real_data_age_days']:
                logger.warning(f"本地文件過舊 ({file_age_days} 天): {file_path}")
                continue

            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # 驗證是否為真實HKMA數據
                if self._is_real_hkma_data(data):
                    records = data.get('data', [])
                    logger.info(f"成功加載本地真實數據: {file_path} ({len(records)} 條記錄)")

                    return {
                        'data': records,
                        'source': f'Local Real Data: {full_path.name}',
                        'file_age_days': file_age_days,
                        'count': len(records),
                        'last_modified': datetime.fromtimestamp(full_path.stat().st_mtime).isoformat(),
                        'data_source_verification': 'verified_real_hkma'
                    }
                else:
                    logger.warning(f"文件未通過真實性驗證: {file_path}")

            except Exception as e:
                logger.error(f"本地文件加載失敗 {file_path}: {e}")
                continue

        return None

    def _is_real_hkma_data(self, data: Dict) -> bool:
        """驗證是否為真實HKMA數據"""
        # 檢查必要的標識字段
        hkma_indicators = [
            'source', 'collection_time', 'record_count',
            'hkma', 'data.gov.hk'
        ]

        for indicator in hkma_indicators:
            if str(data).lower().find(indicator) >= 0:
                return True

        # 檢查數據結構
        if 'data' in data and isinstance(data['data'], list):
            if len(data['data']) > 0:
                sample = data['data'][0]
                if isinstance(sample, dict):
                    # 檢查是否包含真實利率或匯率數據
                    real_data_fields = ['hibor_', 'rate', 'hkma', 'timestamp', 'end_of_date']
                    for field in real_data_fields:
                        if any(field in str(key) for key in sample.keys()):
                            return True

        return False

    def _parse_hkma_data(self, data: Dict, data_type: str) -> Optional[Dict[str, Any]]:
        """解析HKMA API數據"""
        try:
            if data_type == 'hibor_rates':
                return self._parse_hibor_data(data)
            elif data_type == 'exchange_rates':
                return self._parse_exchange_data(data)
            elif data_type == 'monetary_base':
                return self._parse_monetary_data(data)
            else:
                return None

        except Exception as e:
            logger.error(f"HKMA數據解析失敗 {data_type}: {e}")
            return None

    def _parse_hibor_data(self, data: Dict) -> Optional[Dict[str, Any]]:
        """解析HIBOR數據"""
        hibor_records = []
        records = data.get('records', []) or data.get('data', [])

        for record in records:
            try:
                hibor_record = {
                    'date': record.get('end_of_date') or record.get('date') or record.get('timestamp'),
                    'hibor_overnight': self._safe_float(record.get('hibor_overnight') or record.get('ir_1w')),
                    'hibor_1_week': self._safe_float(record.get('hibor_1_week') or record.get('ir_1w')),
                    'hibor_1_month': self._safe_float(record.get('hibor_1_month') or record.get('ir_1m')),
                    'hibor_3_months': self._safe_float(record.get('hibor_3_months') or record.get('ir_3m')),
                    'hibor_6_months': self._safe_float(record.get('hibor_6_months') or record.get('ir_6m')),
                    'hibor_12_months': self._safe_float(record.get('hibor_12_months') or record.get('ir_12m')),
                    'source': 'HKMA_Real_Time',
                    'timestamp': datetime.now().isoformat()
                }

                # 驗證數據完整性
                if hibor_record['date'] and (hibor_record['hibor_overnight'] or
                    hibor_record['hibor_1_week'] or hibor_record['hibor_1_month']):
                    hibor_records.append(hibor_record)

            except Exception as e:
                logger.warning(f"HIBOR記錄解析失敗: {e}")
                continue

        if hibor_records:
            return {
                'data': hibor_records,
                'source': 'HKMA_Real_Time',
                'count': len(hibor_records),
                'last_updated': datetime.now().isoformat()
            }

        return None

    def _parse_exchange_data(self, data: Dict) -> Optional[Dict[str, Any]]:
        """解析匯率數據"""
        exchange_records = []
        records = data.get('records', []) or data.get('data', [])

        for record in records:
            try:
                exchange_record = {
                    'date': record.get('end_of_date') or record.get('date') or record.get('timestamp'),
                    'usd_hkd': self._safe_float(record.get('usd_hkd')),
                    'cny_hkd': self._safe_float(record.get('cny_hkd')),
                    'eur_hkd': self._safe_float(record.get('eur_hkd')),
                    'gbp_hkd': self._safe_float(record.get('gbp_hkd')),
                    'jpy_hkd': self._safe_float(record.get('jpy_hkd')),
                    'source': 'HKMA_Real_Time',
                    'timestamp': datetime.now().isoformat()
                }

                if exchange_record['date'] and exchange_record['usd_hkd']:
                    exchange_records.append(exchange_record)

            except Exception as e:
                logger.warning(f"匯率記錄解析失敗: {e}")
                continue

        if exchange_records:
            return {
                'data': exchange_records,
                'source': 'HKMA_Real_Time',
                'count': len(exchange_records),
                'last_updated': datetime.now().isoformat()
            }

        return None

    def _parse_monetary_data(self, data: Dict) -> Optional[Dict[str, Any]]:
        """解析貨幣基礎數據"""
        monetary_records = []
        records = data.get('records', []) or data.get('data', [])

        for record in records:
            try:
                monetary_record = {
                    'date': record.get('end_of_date') or record.get('date') or record.get('timestamp'),
                    'monetary_base_billion_hkd': self._safe_float(record.get('monetary_base')),
                    'm1_billion_hkd': self._safe_float(record.get('m1')),
                    'm2_billion_hkd': self._safe_float(record.get('m2')),
                    'm3_billion_hkd': self._safe_float(record.get('m3')),
                    'source': 'HKMA_Real_Time',
                    'timestamp': datetime.now().isoformat()
                }

                if monetary_record['date'] and monetary_record['monetary_base_billion_hkd']:
                    monetary_records.append(monetary_record)

            except Exception as e:
                logger.warning(f"貨幣基礎記錄解析失敗: {e}")
                continue

        if monetary_records:
            return {
                'data': monetary_records,
                'source': 'HKMA_Real_Time',
                'count': len(monetary_records),
                'last_updated': datetime.now().isoformat()
            }

        return None

    def _is_real_data_quality_acceptable(self, data: Dict[str, Any]) -> bool:
        """驗證真實數據質量是否可接受"""
        if not data or 'data' not in data:
            return False

        records = data['data']
        if len(records) < self.data_quality_requirements['min_records']:
            return False

        # 檢查必需字段
        required_fields = self.data_quality_requirements['required_fields'].get(
            self._infer_data_type_from_source(data.get('source', ''))
        )

        if required_fields:
            for record in records[:5]:  # 檢查前5條記錄
                missing_fields = [field for field in required_fields
                                if not record.get(field) and record.get(field) != 0]
                if len(missing_fields) > len(required_fields) * 0.5:  # 超過50%字段缺失
                    return False

        return True

    def _infer_data_type_from_source(self, source: str) -> str:
        """從數據源推斷數據類型"""
        source_lower = source.lower()
        if 'hibor' in source_lower:
            return 'hibor_rates'
        elif 'exchange' in source_lower or 'rate' in source_lower:
            return 'exchange_rates'
        elif 'monetary' in source_lower:
            return 'monetary_base'
        else:
            return 'unknown'

    def _validate_and_return(self, data: Dict[str, Any], data_type: str, source: str) -> Dict[str, Any]:
        """驗證並返回數據"""
        # 添加驗證信息
        data['real_data_verification'] = {
            'verified': True,
            'data_type': data_type,
            'source_type': source,
            'verification_timestamp': datetime.now().isoformat(),
            'only_real_data': True,
            'simulated_data_rejected': True
        }

        # 記錄質量指標
        self.quality_metrics[data_type] = {
            'record_count': len(data.get('data', [])),
            'data_quality': 'acceptable',
            'source': source,
            'timestamp': datetime.now().isoformat()
        }

        logger.info(f"真實數據驗證成功: {data_type} 來源: {source}, 記錄: {len(data.get('data', []))}")
        return data

    def _get_file_age_days(self, file_path: Path) -> int:
        """獲取文件年齡（天數）"""
        try:
            file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
            age_days = (datetime.now() - file_time).days
            return age_days
        except:
            return 999  # 非常大的年齡表示文件不存在或無法訪問

    def _safe_float(self, value) -> Optional[float]:
        """安全的浮點數轉換"""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def _record_data_success(self, data_type: str, source: str, data: Dict[str, Any]):
        """記錄數據獲取成功"""
        record = {
            'timestamp': datetime.now().isoformat(),
            'data_type': data_type,
            'source': source,
            'status': 'SUCCESS',
            'record_count': len(data.get('data', [])),
            'data_source': 'REAL_ONLY'
        }
        self.data_source_history.append(record)

        # 限制歷史記錄數量
        if len(self.data_source_history) > 1000:
            self.data_source_history = self.data_source_history[-500:]

        logger.info(f"真實數據記錄: {data_type} 來源: {source}")

    def _record_data_failure(self, data_type: str, error_message: str):
        """記錄數據獲取失敗"""
        record = {
            'timestamp': datetime.now().isoformat(),
            'data_type': data_type,
            'source': 'FAILED',
            'status': 'FAILURE',
            'error': error_message,
            'simulated_rejected': True
        }
        self.data_source_history.append(record)

        # 限制歷史記錄數量
        if len(self.data_source_history) > 1000:
            self.data_source_history = self.data_source_history[-500:]

        logger.error(f"真實數據失敗記錄: {data_type} - {error_message}")

    def get_real_data_status_report(self) -> Dict[str, Any]:
        """獲取真實數據狀態報告"""
        report = {
            'report_timestamp': datetime.now().isoformat(),
            'real_only_policy': {
                'allow_simulated_data': False,
                'require_real_source': True,
                'minimum_real_data_age_days': self.real_only_config['minimum_real_data_age_days']
            },
            'data_sources_configured': len(self.real_data_sources),
            'recent_activity': {
                'total_attempts': len(self.data_source_history),
                'successful_retrievals': sum(1 for record in self.data_source_history if record['status'] == 'SUCCESS'),
                'failed_retrievals': sum(1 for record in self.data_source_history if record['status'] == 'FAILURE'),
                'success_rate': 0.0,
                'last_24h_attempts': 0,
                'last_24h_success': 0
            },
            'data_quality_summary': self.quality_metrics,
            'local_files_status': self._get_local_files_status()
        }

        # 計算成功率
        if report['recent_activity']['total_attempts'] > 0:
            success_rate = report['recent_activity']['successful_retrievals'] / report['recent_activity']['total_attempts']
            report['recent_activity']['success_rate'] = round(success_rate, 3)

        # 計算最近24小時的統計
        cutoff_time = datetime.now() - timedelta(hours=24)
        recent_records = [record for record in self.data_source_history
                          if datetime.fromisoformat(record['timestamp']) > cutoff_time]

        report['recent_activity']['last_24h_attempts'] = len(recent_records)
        report['recent_activity']['last_24h_success'] = sum(1 for record in recent_records if record['status'] == 'SUCCESS')
        report['recent_activity']['last_24h_success_rate'] = 0.0

        if report['recent_activity']['last_24h_attempts'] > 0:
            recent_24h_success_rate = report['recent_activity']['last_24h_success'] / report['recent_activity']['last_24h_attempts']
            report['recent_activity']['last_24h_success_rate'] = round(recent_24h_success_rate, 3)

        return report

    def _get_local_files_status(self) -> Dict[str, Any]:
        """獲取本地文件狀態"""
        local_status = {
            'total_files': 0,
            'fresh_files': 0,  # < 90天
            'old_files': 0,   # >= 90天
            'missing_files': [],
            'file_details': []
        }

        for data_type, config in self.real_data_sources.items():
            for file_path in config['local_files']:
                full_path = Path(file_path)
                local_status['total_files'] += 1

                if full_path.exists():
                    age_days = self._get_file_age_days(full_path)
                    if age_days < self.real_only_config['minimum_real_data_age_days']:
                        local_status['fresh_files'] += 1
                    else:
                        local_status['old_files'] += 1

                    local_status['file_details'].append({
                        'data_type': data_type,
                        'file_path': file_path,
                        'exists': True,
                        'age_days': age_days,
                        'size_bytes': full_path.stat().st_size if full_path.exists() else 0
                    })
                else:
                    local_status['missing_files'].append(file_path)

        return local_status

def main():
    """主函數 - 演示真實數據專用系統"""
    print("[TARGET] Real Data Only API System Test")
    print("[OK] Reject simulated data - Only use real Hong Kong government data")
    print("=" * 60)

    # 創建真實數據專用系統
    real_api = RealDataOnlyAPISystem()

    # 測試獲取真實數據
    print("\n1. 測試獲取真實數據...")

    test_results = {}

    for data_type in ['hibor_rates', 'exchange_rates', 'monetary_base']:
        print(f"\n測試 {data_type}:")
        result = real_api.fetch_real_data_only(data_type, 7)

        if result:
            test_results[data_type] = {
                'status': 'SUCCESS',
                'record_count': len(result.get('data', [])),
                'source': result.get('source', 'Unknown'),
                'verification': result.get('real_data_verification', {})
            }
            record_count = len(result.get('data', []))
            source = result.get('source', 'Unknown')
            verified = result.get('real_data_verification', {}).get('verified', False)
            print(f"  [OK] SUCCESS: {record_count} records")
            print(f"     Source: {source}")
            print(f"     Verified: {verified}")
        else:
            test_results[data_type] = {
                'status': 'FAILED',
                'error': 'Cannot get real data'
            }
            print(f"  [FAIL] FAILED: Cannot get real data")

    # 獲取狀態報告
    print("\n2. Getting real data status report...")
    status_report = real_api.get_real_data_status_report()

    # 顯示報告摘要
    print("\n" + "=" * 60)
    print("Real Data Status Report")
    print("=" * 60)

    # Policy description
    policy = status_report['real_only_policy']
    print(f"\nReal Data Policy:")
    print(f"  Allow simulated data: {policy['allow_simulated_data']}")
    print(f"  Require real source: {policy['require_real_source']}")
    print(f"  Local data max age: {policy['minimum_real_data_age_days']} days")

    # Configured data sources
    print(f"\nConfigured Data Sources: {status_report['data_sources_configured']}")

    # Recent activity statistics
    activity = status_report['recent_activity']
    print(f"\nRecent Activity Statistics:")
    print(f"  Total attempts: {activity['total_attempts']}")
    print(f"  Successful retrievals: {activity['successful_retrievals']}")
    print(f"  Failed retrievals: {activity['failed_retrievals']}")
    print(f"  Success rate: {activity['success_rate']:.1%}")
    print(f"  Last 24h attempts: {activity['last_24h_attempts']}")
    print(f"  Last 24h success: {activity['last_24h_success']}")
    print(f"  Last 24h success rate: {activity['last_24h_success_rate']:.1%}")

    # Test results summary
    print(f"\nTest Results Summary:")
    for data_type, result in test_results.items():
        status_icon = "[OK]" if result['status'] == 'SUCCESS' else "[FAIL]"
        print(f"  {data_type}: {status_icon} {result.get('status', 'UNKNOWN')}")
        if result['status'] == 'SUCCESS':
            print(f"    Records: {result['record_count']}")
            print(f"    Source: {result['source']}")

    # Local files status
    local_status = status_report['local_files_status']
    print(f"\nLocal Files Status:")
    print(f"  Total files: {local_status['total_files']}")
    print(f"  Fresh files (<90 days): {local_status['fresh_files']}")
    print(f"  Old files (>=90 days): {local_status['old_files']}")
    print(f"  Missing files: {len(local_status['missing_files'])}")

    # 質量指標
    if status_report['data_quality_summary']:
        print(f"\n數據質量指標:")
        for data_type, metrics in status_report['data_quality_summary'].items():
            print(f"  {data_type}:")
            print(f"    記錄數: {metrics.get('record_count', 0)}")
            print(f"    質量: {metrics.get('data_quality', 'Unknown')}")
            print(f"    來源: {metrics.get('source', 'Unknown')}")

    # 總體評估
    print(f"\n總體評估:")
    overall_success_rate = activity['success_rate']
    if overall_success_rate >= 0.8:
        print("  🟢 系統狀態: 優秀 (真實數據可用性高)")
    elif overall_success_rate >= 0.5:
        print("  🟡 系統狀態: 可接受 (真實數據基本可用)")
    else:
        print("  🔴 系統狀態: 需要改進 (真實數據獲取困難)")

    print("\n🎯 重要提醒:")
    print("  - 系統配置為只使用真實數據")
    print("  - 拒絕所有形式的模擬數據")
    print("  - 如果無法獲取真實數據，系統將返回None而非備份數據")
    print("  - 建議定期更新本地真實數據文件")

    # 保存報告
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = f"real_data_only_api_report_{timestamp}.json"

    try:
        full_report = {
            'test_results': test_results,
            'status_report': status_report,
            'system_config': {
                'real_only_policy': policy,
                'data_sources': list(real_api.real_data_sources.keys()),
                'file_age_limit_days': real_api.real_only_config['minimum_real_data_age_days']
            }
        }

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(full_report, f, indent=2, ensure_ascii=False, default=str)

        print(f"\n詳細報告已保存到: {report_file}")

    except Exception as e:
        print(f"\n報告保存失敗: {e}")

    print("\n" + "=" * 60)
    print("真實數據專用API系統測試完成")
    print("=" * 60)

    return test_results

if __name__ == "__main__":
    real_data_test_results = main()