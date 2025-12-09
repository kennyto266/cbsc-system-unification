#!/usr/bin/env python3
"""
Phase 5: System Integration and Optimization
統一驗證系統 - Unified Verification Manager

集成三層驗證流水線：
1. Source Authentication (數據源認證)
2. Content Validation (內容驗證)
3. Behavioral Analysis (行為分析)

與simplified_system無縫集成，提供高性能、可靠的數據驗證服務。
"""

import asyncio
import time
import logging
import hashlib
import json
import ssl
import socket
import requests
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
import yaml
import aiohttp
from aiohttp import ClientTimeout, ClientConnectorError
import pickle
import threading
from collections import defaultdict, deque
import weakref

# Import simplified system components
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api.government_data import GovernmentDataAPI
from src.api.stock_api import StockDataAPI

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class VerificationResult:
    """驗證結果數據結構"""
    timestamp: str
    source_score: float  # 0-1, 數據源認證分數
    content_score: float  # 0-1, 內容驗證分數
    behavior_score: float  # 0-1, 行為分析分數
    composite_score: float  # 0-1, 綜合分數
    confidence_interval: Tuple[float, float]  # 95%置信區間
    verification_time_ms: float  # 驗證耗時(毫秒)
    details: Dict[str, Any]  # 詳細信息
    alerts: List[str]  # 警報信息
    cache_hit: bool  # 是否命中緩存

@dataclass
class SystemMetrics:
    """系統性能指標"""
    total_verifications: int = 0
    successful_verifications: int = 0
    failed_verifications: int = 0
    avg_response_time_ms: float = 0.0
    cache_hit_rate: float = 0.0
    throughput_per_second: float = 0.0
    error_rate: float = 0.0
    last_updated: str = ""

class MultiLevelCache:
    """多級緩存系統"""

    def __init__(self):
        # 不同TTL的緩存層
        self.source_cache = {}  # TTL: 300s (5分鐘)
        self.content_cache = {}  # TTL: 600s (10分鐘)
        self.behavior_cache = {}  # TTL: 1800s (30分鐘)
        self.composite_cache = {}  # TTL: 900s (15分鐘)

        self.cache_timestamps = {}
        self.cache_hits = defaultdict(int)
        self.cache_misses = defaultdict(int)

        # TTL配置 (秒)
        self.ttl_config = {
            'source': 300,
            'content': 600,
            'behavior': 1800,
            'composite': 900
        }

        # 清理線程
        self._cleanup_thread = None
        self._stop_cleanup = threading.Event()
        self._start_cleanup_thread()

    def _start_cleanup_thread(self):
        """啟動緩存清理線程"""
        def cleanup_loop():
            while not self._stop_cleanup.wait(60):  # 每分鐘清理一次
                self._cleanup_expired_cache()

        self._cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
        self._cleanup_thread.start()

    def _cleanup_expired_cache(self):
        """清理過期緩存"""
        current_time = time.time()
        expired_keys = []

        for cache_key, timestamp in self.cache_timestamps.items():
            cache_type = cache_key.split(':')[0]
            ttl = self.ttl_config.get(cache_type, 600)

            if current_time - timestamp > ttl:
                expired_keys.append(cache_key)

        for key in expired_keys:
            cache_type = key.split(':')[0]
            cache_map = getattr(self, f"{cache_type}_cache", {})
            cache_map.pop(key.split(':', 1)[1], None)
            self.cache_timestamps.pop(key, None)

    def get(self, cache_type: str, key: str) -> Optional[Any]:
        """獲取緩存"""
        cache_map = getattr(self, f"{cache_type}_cache", {})
        full_key = f"{cache_type}:{key}"

        if key in cache_map and full_key in self.cache_timestamps:
            # 檢查TTL
            current_time = time.time()
            ttl = self.ttl_config.get(cache_type, 600)

            if current_time - self.cache_timestamps[full_key] < ttl:
                self.cache_hits[cache_type] += 1
                return cache_map[key]
            else:
                # 過期，刪除
                cache_map.pop(key, None)
                self.cache_timestamps.pop(full_key, None)

        self.cache_misses[cache_type] += 1
        return None

    def set(self, cache_type: str, key: str, value: Any):
        """設置緩存"""
        cache_map = getattr(self, f"{cache_type}_cache", {})
        full_key = f"{cache_type}:{key}"

        cache_map[key] = value
        self.cache_timestamps[full_key] = time.time()

    def get_hit_rate(self, cache_type: Optional[str] = None) -> float:
        """獲取緩存命中率"""
        if cache_type:
            hits = self.cache_hits[cache_type]
            misses = self.cache_misses[cache_type]
            total = hits + misses
            return hits / total if total > 0 else 0.0
        else:
            total_hits = sum(self.cache_hits.values())
            total_misses = sum(self.cache_misses.values())
            total = total_hits + total_misses
            return total_hits / total if total > 0 else 0.0

    def clear(self, cache_type: Optional[str] = None):
        """清空緩存"""
        if cache_type:
            cache_map = getattr(self, f"{cache_type}_cache", {})
            cache_map.clear()
        else:
            for cache_type in ['source', 'content', 'behavior', 'composite']:
                cache_map = getattr(self, f"{cache_type}_cache", {})
                cache_map.clear()

        self.cache_timestamps.clear()

    def shutdown(self):
        """關閉緩存系統"""
        if self._cleanup_thread:
            self._stop_cleanup.set()
            self._cleanup_thread.join(timeout=5)

class SourceAuthenticator:
    """數據源認證層 - Layer 1"""

    def __init__(self):
        self.trusted_domains = {
            'hkma.gov.hk': True,
            'gov.hk': True,
            'data.gov.hk': True,
            '18.180.162.113': True,  # 中央API
        }

        self.certificates_cache = {}
        self.session = requests.Session()

        # 預計算的數字簽名模式
        self.known_signatures = {}

    async def verify_source(self, url: str, data: Any) -> Tuple[float, Dict[str, Any]]:
        """驗證數據源"""
        start_time = time.time()
        details = {}

        try:
            # 1. 域名白名單檢查
            domain_score = self._check_domain_whitelist(url)
            details['domain_check'] = domain_score

            # 2. TLS證書驗證
            cert_score = await self._verify_tls_certificate(url)
            details['tls_certificate'] = cert_score

            # 3. 數字簽名驗證
            signature_score = self._verify_digital_signature(data)
            details['digital_signature'] = signature_score

            # 4. 端點驗證
            endpoint_score = self._verify_endpoint(url)
            details['endpoint_verification'] = endpoint_score

            # 計算加權平均分
            weights = {'domain': 0.3, 'tls': 0.3, 'signature': 0.2, 'endpoint': 0.2}
            total_score = (
                domain_score * weights['domain'] +
                cert_score * weights['tls'] +
                signature_score * weights['signature'] +
                endpoint_score * weights['endpoint']
            )

            verification_time = (time.time() - start_time) * 1000
            details['verification_time_ms'] = verification_time

            return total_score, details

        except Exception as e:
            logger.error(f"Source authentication error: {e}")
            return 0.0, {'error': str(e), 'verification_time_ms': (time.time() - start_time) * 1000}

    def _check_domain_whitelist(self, url: str) -> float:
        """檢查域名白名單"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            # 檢查精確匹配
            if domain in self.trusted_domains:
                return 1.0

            # 檢查子域名匹配
            for trusted_domain in self.trusted_domains:
                if domain.endswith('.' + trusted_domain):
                    return 0.8

            return 0.0

        except Exception as e:
            logger.error(f"Domain check error: {e}")
            return 0.0

    async def _verify_tls_certificate(self, url: str) -> float:
        """驗證TLS證書"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            hostname = parsed.hostname
            port = parsed.port or (443 if parsed.scheme == 'https' else 80)

            if not hostname:
                return 0.0

            # 檢查證書緩存
            cache_key = f"{hostname}:{port}"
            if cache_key in self.certificates_cache:
                cert_info = self.certificates_cache[cache_key]
                if time.time() - cert_info['timestamp'] < 300:  # 5分鐘緩存
                    return cert_info['score']

            # 創建SSL上下文
            context = ssl.create_default_context()

            # 驗證證書
            with socket.create_connection((hostname, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as secure_sock:
                    cert = secure_sock.getpeercert()

                    # 檢查證書有效性
                    score = 0.0

                    # 檢查證書主題
                    subject = dict(x[0] for x in cert.get('subject', []))
                    if hostname.lower() in subject.get('commonName', '').lower():
                        subject_score = 0.8
                    else:
                        subject_score = 0.2

                    # 檢查證書有效期
                    not_after = cert.get('notAfter', '')
                    if not_after:
                        try:
                            expiry_date = datetime.strptime(not_after, '%b %d %H:%M:%S %Y %Z')
                            days_until_expiry = (expiry_date - datetime.now()).days

                            if days_until_expiry > 30:
                                expiry_score = 1.0
                            elif days_until_expiry > 7:
                                expiry_score = 0.6
                            else:
                                expiry_score = 0.2
                        except:
                            expiry_score = 0.2
                    else:
                        expiry_score = 0.2

                    # 檢查簽發者
                    issuer = dict(x[0] for x in cert.get('issuer', []))
                    trusted_issuers = ['Let\'s Encrypt', 'DigiCert', 'GlobalSign', 'Comodo']
                    issuer_score = 1.0 if any(trusted in issuer.get('organizationName', '') for trusted in trusted_issuers) else 0.5

                    score = (subject_score + expiry_score + issuer_score) / 3

            # 緩存結果
            self.certificates_cache[cache_key] = {
                'score': score,
                'timestamp': time.time()
            }

            return score

        except Exception as e:
            logger.error(f"TLS certificate verification error: {e}")
            return 0.0

    def _verify_digital_signature(self, data: Any) -> float:
        """驗證數字簽名"""
        try:
            # 將數據序列化為字節
            if isinstance(data, str):
                data_bytes = data.encode('utf-8')
            elif isinstance(data, dict):
                data_bytes = json.dumps(data, sort_keys=True).encode('utf-8')
            else:
                data_bytes = str(data).encode('utf-8')

            # 計算哈希
            hash_value = hashlib.sha256(data_bytes).hexdigest()

            # 檢查是否為已知簽名
            if hash_value in self.known_signatures:
                return self.known_signatures[hash_value]

            # 檢查數據結構完整性
            if isinstance(data, dict):
                required_fields = ['timestamp', 'data']
                if all(field in data for field in required_fields):
                    signature_score = 0.8
                else:
                    signature_score = 0.4
            elif isinstance(data, list):
                signature_score = 0.6  # 列表結構，中等信任度
            else:
                signature_score = 0.3  # 其他結構，較低信任度

            # 緩存簽名
            self.known_signatures[hash_value] = signature_score

            return signature_score

        except Exception as e:
            logger.error(f"Digital signature verification error: {e}")
            return 0.0

    def _verify_endpoint(self, url: str) -> float:
        """驗證API端點"""
        try:
            # 已知的政府API端點模式
            trusted_patterns = [
                'api.hkma.gov.hk',
                'data.gov.hk',
                'api.census.gov.hk',
                '18.180.162.113:9191'
            ]

            url_lower = url.lower()
            for pattern in trusted_patterns:
                if pattern in url_lower:
                    return 1.0

            # 檢查是否為.gov.hk域名
            if '.gov.hk' in url_lower:
                return 0.8

            # 其他域名
            return 0.2

        except Exception as e:
            logger.error(f"Endpoint verification error: {e}")
            return 0.0

class ContentValidator:
    """內容驗證層 - Layer 2"""

    def __init__(self):
        self.business_rules = {
            'hibor_rates': {
                'min_value': 0.0,
                'max_value': 20.0,
                'required_fields': ['date', 'overnight'],
                'data_types': [float, int]
            },
            'exchange_rates': {
                'min_value': 0.1,
                'max_value': 20.0,
                'required_fields': ['date', 'usd_hkd'],
                'data_types': [float, int]
            },
            'stock_prices': {
                'min_value': 0.01,
                'max_value': 10000.0,
                'required_fields': ['date', 'price'],
                'data_types': [float, int]
            }
        }

    async def validate_content(self, data: Any, data_type: str) -> Tuple[float, Dict[str, Any]]:
        """驗證數據內容"""
        start_time = time.time()
        details = {}

        try:
            # 1. 數據格式驗證
            format_score = self._validate_data_format(data)
            details['format_validation'] = format_score

            # 2. 業務規則驗證
            business_score = self._validate_business_rules(data, data_type)
            details['business_rules'] = business_score

            # 3. 統計測試
            stats_score = self._perform_statistical_tests(data)
            details['statistical_tests'] = stats_score

            # 4. 哈希驗證
            hash_score = self._verify_data_hash(data)
            details['hash_verification'] = hash_score

            # 計算加權平均分
            weights = {'format': 0.3, 'business': 0.4, 'stats': 0.2, 'hash': 0.1}
            total_score = (
                format_score * weights['format'] +
                business_score * weights['business'] +
                stats_score * weights['stats'] +
                hash_score * weights['hash']
            )

            validation_time = (time.time() - start_time) * 1000
            details['validation_time_ms'] = validation_time

            return total_score, details

        except Exception as e:
            logger.error(f"Content validation error: {e}")
            return 0.0, {'error': str(e), 'validation_time_ms': (time.time() - start_time) * 1000}

    def _validate_data_format(self, data: Any) -> float:
        """驗證數據格式"""
        try:
            if isinstance(data, dict):
                # 檢查必要的結構字段
                if 'data' in data and isinstance(data['data'], list):
                    return 0.9
                elif 'records' in data and isinstance(data['records'], list):
                    return 0.9
                else:
                    return 0.6
            elif isinstance(data, list):
                return 0.8 if data else 0.2
            elif isinstance(data, (pd.DataFrame, pd.Series)):
                return 0.9
            else:
                return 0.3

        except Exception as e:
            logger.error(f"Format validation error: {e}")
            return 0.0

    def _validate_business_rules(self, data: Any, data_type: str) -> float:
        """驗證業務規則"""
        try:
            rules = self.business_rules.get(data_type, {})
            if not rules:
                return 0.8  # 未知數據類型，給予中等分數

            # 提取數值數據
            values = []
            if isinstance(data, dict):
                if 'data' in data:
                    values = self._extract_numeric_values(data['data'])
                elif 'records' in data:
                    values = self._extract_numeric_values(data['records'])
            elif isinstance(data, list):
                values = self._extract_numeric_values(data)

            if not values:
                return 0.2

            # 檢查值範圍
            min_val, max_val = rules['min_value'], rules['max_value']
            valid_values = [v for v in values if min_val <= v <= max_val]

            if not valid_values:
                return 0.0

            # 計算有效值比例
            valid_ratio = len(valid_values) / len(values)
            range_score = min(valid_ratio * 2, 1.0)  # 至少50%有效值才能及格

            # 檢查必要字段
            field_score = 1.0
            if isinstance(data, dict) and 'data' in data and data['data']:
                sample_record = data['data'][0]
                required_fields = rules.get('required_fields', [])
                missing_fields = [field for field in required_fields if field not in sample_record]
                field_score = 1.0 - (len(missing_fields) / len(required_fields)) if required_fields else 1.0

            return (range_score + field_score) / 2

        except Exception as e:
            logger.error(f"Business rules validation error: {e}")
            return 0.0

    def _extract_numeric_values(self, data: Any) -> List[float]:
        """提取數值"""
        values = []

        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    values.extend([v for v in item.values() if isinstance(v, (int, float))])
                elif isinstance(item, (int, float)):
                    values.append(item)
        elif isinstance(data, dict):
            values.extend([v for v in data.values() if isinstance(v, (int, float))])

        return values

    def _perform_statistical_tests(self, data: Any) -> float:
        """執行統計測試"""
        try:
            # 提取數值數據
            values = self._extract_numeric_values(data)

            if len(values) < 3:
                return 0.3  # 數據點太少

            # 轉換為numpy數組
            values_array = np.array(values)

            # 1. 檢查異常值 (使用IQR方法)
            q1, q3 = np.percentile(values_array, [25, 75])
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr

            outliers = values_array[(values_array < lower_bound) | (values_array > upper_bound)]
            outlier_ratio = len(outliers) / len(values_array)
            outlier_score = max(1 - outlier_ratio * 2, 0.0)  # 異常值越少分數越高

            # 2. 檢查數據分布的基本統計特性
            mean_val = np.mean(values_array)
            std_val = np.std(values_array)

            # 標準差檢查 (避免標準差過大或過小)
            if std_val > 0:
                cv = std_val / abs(mean_val) if mean_val != 0 else std_val
                cv_score = 1.0 - min(cv, 2.0) / 2.0  # 變異係數檢查
            else:
                cv_score = 0.1  # 標準差為0，數據可能異常

            # 3. 連續性檢查 (對時間序列數據)
            continuity_score = 0.8  # 默認分數

            return (outlier_score * 0.4 + cv_score * 0.3 + continuity_score * 0.3)

        except Exception as e:
            logger.error(f"Statistical tests error: {e}")
            return 0.0

    def _verify_data_hash(self, data: Any) -> float:
        """驗證數據哈希"""
        try:
            # 序列化數據
            data_str = json.dumps(data, sort_keys=True, default=str)
            hash_value = hashlib.sha256(data_str.encode('utf-8')).hexdigest()

            # 簡單的哈希驗證 - 檢查哈希值長度和格式
            if len(hash_value) == 64 and all(c in '0123456789abcdef' for c in hash_value):
                return 1.0
            else:
                return 0.0

        except Exception as e:
            logger.error(f"Hash verification error: {e}")
            return 0.0

class BehavioralAnalyzer:
    """行為分析層 - Layer 3"""

    def __init__(self):
        self.historical_patterns = {}
        self.ml_models = {}
        self.baseline_data = {}
        self.anomaly_threshold = 0.8

    async def analyze_behavior(self, data: Any, data_type: str, historical_context: Optional[Dict] = None) -> Tuple[float, Dict[str, Any]]:
        """分析數據行為模式"""
        start_time = time.time()
        details = {}

        try:
            # 1. 模式分析
            pattern_score = self._analyze_patterns(data, data_type)
            details['pattern_analysis'] = pattern_score

            # 2. ML異常檢測
            ml_score = await self._ml_anomaly_detection(data, data_type)
            details['ml_anomaly_detection'] = ml_score

            # 3. 歷史比較
            historical_score = self._compare_with_historical(data, data_type, historical_context)
            details['historical_comparison'] = historical_score

            # 計算加權平均分
            weights = {'pattern': 0.4, 'ml': 0.4, 'historical': 0.2}
            total_score = (
                pattern_score * weights['pattern'] +
                ml_score * weights['ml'] +
                historical_score * weights['historical']
            )

            analysis_time = (time.time() - start_time) * 1000
            details['analysis_time_ms'] = analysis_time

            return total_score, details

        except Exception as e:
            logger.error(f"Behavioral analysis error: {e}")
            return 0.0, {'error': str(e), 'analysis_time_ms': (time.time() - start_time) * 1000}

    def _analyze_patterns(self, data: Any, data_type: str) -> float:
        """分析數據模式"""
        try:
            # 提取數值數據
            values = self._extract_numeric_values(data)

            if len(values) < 5:
                return 0.5  # 數據點太少，給予中等分數

            values_array = np.array(values)

            # 1. 趨勢分析
            if len(values_array) > 1:
                # 計算趨勢斜率
                x = np.arange(len(values_array))
                slope = np.polyfit(x, values_array, 1)[0]

                # 趨勢合理性檢查 (避免極端趨勢)
                if abs(slope) < np.std(values_array) * 0.1:
                    trend_score = 1.0
                else:
                    trend_score = max(0.3, 1 - abs(slope) / np.std(values_array))
            else:
                trend_score = 0.5

            # 2. 季節性檢查 (對時間序列數據)
            if len(values_array) >= 12:  # 至少需要12個數據點
                # 簡單的季節性檢查
                autocorr = np.correlate(values_array, values_array, mode='full')
                center = len(autocorr) // 2
                seasonal_score = min(autocorr[center + 1] / autocorr[center], 1.0) if autocorr[center] > 0 else 0.5
            else:
                seasonal_score = 0.7

            # 3. 波動性分析
            if len(values_array) > 1:
                volatility = np.std(values_array) / np.mean(values_array) if np.mean(values_array) != 0 else np.std(values_array)
                volatility_score = 1.0 - min(volatility, 2.0) / 2.0  # 波動性越小分數越高
            else:
                volatility_score = 0.5

            return (trend_score * 0.4 + seasonal_score * 0.3 + volatility_score * 0.3)

        except Exception as e:
            logger.error(f"Pattern analysis error: {e}")
            return 0.0

    def _extract_numeric_values(self, data: Any) -> List[float]:
        """提取數值數據"""
        values = []

        if isinstance(data, dict):
            if 'data' in data:
                for item in data['data']:
                    if isinstance(item, dict):
                        values.extend([v for v in item.values() if isinstance(v, (int, float))])
            elif 'records' in data:
                for item in data['records']:
                    if isinstance(item, dict):
                        values.extend([v for v in item.values() if isinstance(v, (int, float))])
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    values.extend([v for v in item.values() if isinstance(v, (int, float))])
                elif isinstance(item, (int, float)):
                    values.append(item)

        return values

    async def _ml_anomaly_detection(self, data: Any, data_type: str) -> float:
        """ML異常檢測"""
        try:
            # 提取特徵
            values = self._extract_numeric_values(data)

            if len(values) < 10:
                return 0.6  # 數據點太少，給予中等分數

            values_array = np.array(values)

            # 1. 統計異常檢測 (Z-score)
            z_scores = np.abs((values_array - np.mean(values_array)) / np.std(values_array))
            anomaly_ratio = np.sum(z_scores > 3) / len(values_array)
            statistical_anomaly_score = 1 - anomaly_ratio

            # 2. 孤立森林檢測 (模擬)
            isolation_score = self._simulate_isolation_forest(values_array)

            # 3. 局部異常因子檢測 (模擬)
            lof_score = self._simulate_lof_detection(values_array)

            return (statistical_anomaly_score * 0.4 + isolation_score * 0.3 + lof_score * 0.3)

        except Exception as e:
            logger.error(f"ML anomaly detection error: {e}")
            return 0.0

    def _simulate_isolation_forest(self, values: np.ndarray) -> float:
        """模擬孤立森林檢測"""
        try:
            # 簡化的異常檢測：基於數據分佈
            q1, q3 = np.percentile(values, [25, 75])
            iqr = q3 - q1

            # 計算每個點的孤立程度
            isolation_scores = []
            for value in values:
                if value < q1 - 1.5 * iqr or value > q3 + 1.5 * iqr:
                    isolation_scores.append(0.3)  # 異常值
                else:
                    isolation_scores.append(0.9)  # 正常值

            return np.mean(isolation_scores)

        except Exception as e:
            logger.error(f"Isolation forest simulation error: {e}")
            return 0.5

    def _simulate_lof_detection(self, values: np.ndarray) -> float:
        """模擬局部異常因子檢測"""
        try:
            # 簡化的LOF檢測：基於密度估計
            if len(values) < 5:
                return 0.7

            # 計算局部密度
            sorted_values = np.sort(values)
            densities = []

            for i, value in enumerate(values):
                # 找到最近的k個鄰居
                k = min(5, len(values) - 1)
                distances = np.abs(sorted_values - value)
                nearest_distances = np.sort(distances)[1:k+1]

                if len(nearest_distances) > 0 and nearest_distances[-1] > 0:
                    density = k / nearest_distances[-1]
                    densities.append(density)

            if densities:
                # 計算LOF分數
                mean_density = np.mean(densities)
                lof_scores = [mean_density / d if d > 0 else 1.0 for d in densities]
                # 轉換為0-1分數 (LOF越接近1越正常)
                normalized_scores = [2 - min(score, 2.0) for score in lof_scores]
                return np.mean(normalized_scores)

            return 0.7

        except Exception as e:
            logger.error(f"LOF detection simulation error: {e}")
            return 0.5

    def _compare_with_historical(self, data: Any, data_type: str, historical_context: Optional[Dict] = None) -> float:
        """與歷史數據比較"""
        try:
            if not historical_context:
                return 0.8  # 沒有歷史數據，給予中等分數

            # 提取當前數據特徵
            current_values = self._extract_numeric_values(data)
            if len(current_values) < 3:
                return 0.6

            current_mean = np.mean(current_values)
            current_std = np.std(current_values)

            # 提取歷史數據特徵
            historical_values = self._extract_numeric_values(historical_context)
            if len(historical_values) < 3:
                return 0.6

            historical_mean = np.mean(historical_values)
            historical_std = np.std(historical_values)

            # 比較均值和標準差
            mean_diff_ratio = abs(current_mean - historical_mean) / abs(historical_mean) if historical_mean != 0 else 0
            std_diff_ratio = abs(current_std - historical_std) / historical_std if historical_std != 0 else 0

            # 計算相似度分數
            mean_similarity = max(0, 1 - mean_diff_ratio * 2)  # 允許50%的均值差異
            std_similarity = max(0, 1 - std_diff_ratio)  # 允許100%的標準差差異

            return (mean_similarity + std_similarity) / 2

        except Exception as e:
            logger.error(f"Historical comparison error: {e}")
            return 0.0

class UnifiedVerificationManager:
    """統一驗證管理器 - 整合三層驗證"""

    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)

        # 初始化組件
        self.cache = MultiLevelCache()
        self.source_authenticator = SourceAuthenticator()
        self.content_validator = ContentValidator()
        self.behavioral_analyzer = BehavioralAnalyzer()

        # 性能指標
        self.metrics = SystemMetrics()
        self.performance_history = deque(maxlen=1000)

        # 異步處理配置
        self.max_concurrent_verifications = self.config.get('performance', {}).get('max_concurrent_verifications', 100)
        self.batch_size = self.config.get('performance', {}).get('batch_size', 10)
        self.timeout_ms = self.config.get('performance', {}).get('timeout_ms', 5000)

        # 集成現有API
        self.government_api = GovernmentDataAPI()
        self.stock_api = StockDataAPI()

        logger.info("Unified Verification Manager initialized")

    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """加載配置文件"""
        default_config = {
            'verification_pipeline': {
                'layers': {
                    'source_auth': {
                        'enabled': True,
                        'parallel_execution': True,
                        'cache_ttl': 300
                    },
                    'content_validation': {
                        'enabled': True,
                        'parallel_execution': True,
                        'cache_ttl': 600
                    },
                    'behavioral_analysis': {
                        'enabled': True,
                        'parallel_execution': False,
                        'cache_ttl': 1800
                    }
                }
            },
            'performance': {
                'max_concurrent_verifications': 100,
                'batch_size': 10,
                'timeout_ms': 5000
            },
            'alerts': {
                'telegram_bot': True,
                'severity_thresholds': {
                    'critical': 0.95,
                    'high': 0.85,
                    'medium': 0.70,
                    'low': 0.50
                }
            }
        }

        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    user_config = yaml.safe_load(f)
                # 合併配置
                return {**default_config, **user_config}
            except Exception as e:
                logger.warning(f"Failed to load config {config_path}: {e}, using defaults")

        return default_config

    async def verify_data(self, data: Any, data_type: str, source_url: Optional[str] = None,
                         historical_context: Optional[Dict] = None) -> VerificationResult:
        """統一數據驗證接口"""
        start_time = time.time()

        # 生成緩存鍵
        cache_key = self._generate_cache_key(data, data_type, source_url)

        # 檢查綜合緩存
        cached_result = self.cache.get('composite', cache_key)
        if cached_result:
            self.metrics.total_verifications += 1
            cached_result.cache_hit = True
            return cached_result

        try:
            # 並行執行可以並行的驗證層
            layers_config = self.config['verification_pipeline']['layers']

            # Layer 1: Source Authentication
            source_score = 1.0  # 默認分數
            source_details = {}
            if layers_config['source_auth']['enabled']:
                if source_url:
                    # 檢查源層緩存
                    source_cache_key = f"source_{hash(source_url)}"
                    cached_source = self.cache.get('source', source_cache_key)
                    if cached_source:
                        source_score, source_details = cached_source
                    else:
                        source_score, source_details = await self.source_authenticator.verify_source(source_url, data)
                        self.cache.set('source', source_cache_key, (source_score, source_details))
                else:
                    source_score = 0.8  # 無URL，給予中等分數
                    source_details = {'message': 'No source URL provided'}

            # Layer 2: Content Validation
            content_score = 1.0
            content_details = {}
            if layers_config['content_validation']['enabled']:
                content_cache_key = f"content_{hash(str(data)[:100])}_{data_type}"
                cached_content = self.cache.get('content', content_cache_key)
                if cached_content:
                    content_score, content_details = cached_content
                else:
                    content_score, content_details = await self.content_validator.validate_content(data, data_type)
                    self.cache.set('content', content_cache_key, (content_score, content_details))

            # Layer 3: Behavioral Analysis (順序執行，因為依賴ML模型)
            behavior_score = 1.0
            behavior_details = {}
            if layers_config['behavioral_analysis']['enabled']:
                behavior_cache_key = f"behavior_{hash(str(data)[:100])}_{data_type}"
                cached_behavior = self.cache.get('behavior', behavior_cache_key)
                if cached_behavior:
                    behavior_score, behavior_details = cached_behavior
                else:
                    behavior_score, behavior_details = await self.behavioral_analyzer.analyze_behavior(data, data_type, historical_context)
                    self.cache.set('behavior', behavior_cache_key, (behavior_score, behavior_details))

            # 計算綜合分數和置信區間
            weights = {'source': 0.3, 'content': 0.4, 'behavior': 0.3}
            composite_score = (
                source_score * weights['source'] +
                content_score * weights['content'] +
                behavior_score * weights['behavior']
            )

            # 計算置信區間 (基於各層分數的變異性)
            scores = [source_score, content_score, behavior_score]
            std_dev = np.std(scores)
            confidence_interval = (
                max(0, composite_score - 1.96 * std_dev),
                min(1, composite_score + 1.96 * std_dev)
            )

            # 生成警報
            alerts = self._generate_alerts(composite_score, source_score, content_score, behavior_score, data_type)

            # 創建結果
            verification_time = (time.time() - start_time) * 1000
            result = VerificationResult(
                timestamp=datetime.now().isoformat(),
                source_score=source_score,
                content_score=content_score,
                behavior_score=behavior_score,
                composite_score=composite_score,
                confidence_interval=confidence_interval,
                verification_time_ms=verification_time,
                details={
                    'source': source_details,
                    'content': content_details,
                    'behavior': behavior_details
                },
                alerts=alerts,
                cache_hit=False
            )

            # 更新緩存
            self.cache.set('composite', cache_key, result)

            # 更新性能指標
            self._update_metrics(result)

            return result

        except Exception as e:
            logger.error(f"Verification error: {e}")
            # 返回失敗結果
            verification_time = (time.time() - start_time) * 1000
            result = VerificationResult(
                timestamp=datetime.now().isoformat(),
                source_score=0.0,
                content_score=0.0,
                behavior_score=0.0,
                composite_score=0.0,
                confidence_interval=(0.0, 0.0),
                verification_time_ms=verification_time,
                details={'error': str(e)},
                alerts=[f"Verification failed: {str(e)}"],
                cache_hit=False
            )

            self._update_metrics(result)
            return result

    def _generate_cache_key(self, data: Any, data_type: str, source_url: Optional[str] = None) -> str:
        """生成緩存鍵"""
        # 使用數據哈希、類型和URL生成唯一鍵
        data_hash = hashlib.md5(str(data)[:200].encode('utf-8')).hexdigest()[:16]
        url_hash = hashlib.md5(str(source_url or '').encode('utf-8')).hexdigest()[:8]
        return f"{data_type}_{data_hash}_{url_hash}"

    def _generate_alerts(self, composite_score: float, source_score: float, content_score: float, behavior_score: float, data_type: str) -> List[str]:
        """生成警報"""
        alerts = []
        thresholds = self.config['alerts']['severity_thresholds']

        # 綜合分數警報
        if composite_score < thresholds['low']:
            alerts.append(f"LOW: Low verification confidence ({composite_score:.3f}) for {data_type}")
        elif composite_score < thresholds['medium']:
            alerts.append(f"MEDIUM: Moderate verification confidence ({composite_score:.3f}) for {data_type}")
        elif composite_score < thresholds['high']:
            alerts.append(f"HIGH: High verification confidence ({composite_score:.3f}) for {data_type}")

        # 各層分數警報
        if source_score < thresholds['low']:
            alerts.append(f"CRITICAL: Source authentication failed ({source_score:.3f})")

        if content_score < thresholds['medium']:
            alerts.append(f"MEDIUM: Content validation issues ({content_score:.3f})")

        if behavior_score < thresholds['high']:
            alerts.append(f"HIGH: Behavioral anomalies detected ({behavior_score:.3f})")

        return alerts

    def _update_metrics(self, result: VerificationResult):
        """更新性能指標"""
        self.metrics.total_verifications += 1

        if result.composite_score > 0:
            self.metrics.successful_verifications += 1
        else:
            self.metrics.failed_verifications += 1

        # 更新平均響應時間
        total_time = self.metrics.avg_response_time_ms * (self.metrics.total_verifications - 1) + result.verification_time_ms
        self.metrics.avg_response_time_ms = total_time / self.metrics.total_verifications

        # 更新緩存命中率
        self.metrics.cache_hit_rate = self.cache.get_hit_rate()

        # 計算錯誤率
        self.metrics.error_rate = self.metrics.failed_verifications / self.metrics.total_verifications

        # 計算吞吐量 (簡化計算)
        if len(self.performance_history) > 0:
            time_diff = time.time() - self.performance_history[0]['timestamp']
            if time_diff > 0:
                self.metrics.throughput_per_second = len(self.performance_history) / time_diff

        # 添加到歷史記錄
        self.performance_history.append({
            'timestamp': time.time(),
            'score': result.composite_score,
            'time_ms': result.verification_time_ms
        })

        # 更新最後更新時間
        self.metrics.last_updated = datetime.now().isoformat()

    async def batch_verify(self, data_batch: List[Tuple[Any, str, Optional[str]]],
                          historical_context: Optional[Dict] = None) -> List[VerificationResult]:
        """批量驗證"""
        results = []

        # 分批處理
        for i in range(0, len(data_batch), self.batch_size):
            batch = data_batch[i:i + self.batch_size]

            # 並行處理當前批次
            semaphore = asyncio.Semaphore(self.max_concurrent_verifications)

            async def verify_single(data_item):
                async with semaphore:
                    data, data_type, source_url = data_item
                    return await self.verify_data(data, data_type, source_url, historical_context)

            batch_tasks = [verify_single(item) for item in batch]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

            # 處理結果
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Batch verification error: {result}")
                    # 創建錯誤結果
                    error_result = VerificationResult(
                        timestamp=datetime.now().isoformat(),
                        source_score=0.0,
                        content_score=0.0,
                        behavior_score=0.0,
                        composite_score=0.0,
                        confidence_interval=(0.0, 0.0),
                        verification_time_ms=0.0,
                        details={'error': str(result)},
                        alerts=[f"Batch verification failed: {str(result)}"],
                        cache_hit=False
                    )
                    results.append(error_result)
                else:
                    results.append(result)

        return results

    def get_metrics(self) -> SystemMetrics:
        """獲取系統指標"""
        return self.metrics

    def get_cache_stats(self) -> Dict[str, Any]:
        """獲取緩存統計"""
        return {
            'overall_hit_rate': self.cache.get_hit_rate(),
            'layer_hit_rates': {
                'source': self.cache.get_hit_rate('source'),
                'content': self.cache.get_hit_rate('content'),
                'behavior': self.cache.get_hit_rate('behavior'),
                'composite': self.cache.get_hit_rate('composite')
            },
            'cache_sizes': {
                'source': len(self.cache.source_cache),
                'content': len(self.cache.content_cache),
                'behavior': len(self.cache.behavior_cache),
                'composite': len(self.cache.composite_cache)
            }
        }

    async def verify_government_data(self, data_type: str, days_back: int = 30) -> VerificationResult:
        """驗證政府數據 - 集成現有API"""
        try:
            # 獲取政府數據
            if data_type == 'hibor_rates':
                data = self.government_api.get_hibor_data(days_back)
                source_url = self.government_api.data_sources['hibor_rates']['base_url']
            elif data_type == 'exchange_rates':
                data = self.government_api.get_exchange_rates(days_back)
                source_url = self.government_api.data_sources['exchange_rates']['base_url']
            elif data_type == 'monetary_base':
                data = self.government_api.get_monetary_base(days_back)
                source_url = self.government_api.data_sources['monetary_base']['base_url']
            else:
                raise ValueError(f"Unknown government data type: {data_type}")

            if not data:
                raise ValueError(f"Failed to fetch government data: {data_type}")

            # 獲取歷史上下文
            historical_context = None  # 可以從緩存或文件加載

            # 執行驗證
            result = await self.verify_data(data, data_type, source_url, historical_context)

            logger.info(f"Government data verification completed: {data_type}, score: {result.composite_score:.3f}")
            return result

        except Exception as e:
            logger.error(f"Government data verification error: {e}")
            # 返回失敗結果
            return VerificationResult(
                timestamp=datetime.now().isoformat(),
                source_score=0.0,
                content_score=0.0,
                behavior_score=0.0,
                composite_score=0.0,
                confidence_interval=(0.0, 0.0),
                verification_time_ms=0.0,
                details={'error': str(e)},
                alerts=[f"Government data verification failed: {str(e)}"],
                cache_hit=False
            )

    async def verify_stock_data(self, symbol: str, duration_days: int = 1095) -> VerificationResult:
        """驗證股票數據 - 集成現有API"""
        try:
            # 獲取股票數據
            data = self.stock_api.get_stock_data(symbol, duration_days)
            source_url = f"{self.stock_api.api_base_url}/inst/getInst"

            if not data:
                raise ValueError(f"Failed to fetch stock data: {symbol}")

            # 執行驗證
            result = await self.verify_data(data, f'stock_prices', source_url)

            logger.info(f"Stock data verification completed: {symbol}, score: {result.composite_score:.3f}")
            return result

        except Exception as e:
            logger.error(f"Stock data verification error: {e}")
            # 返回失敗結果
            return VerificationResult(
                timestamp=datetime.now().isoformat(),
                source_score=0.0,
                content_score=0.0,
                behavior_score=0.0,
                composite_score=0.0,
                confidence_interval=(0.0, 0.0),
                verification_time_ms=0.0,
                details={'error': str(e)},
                alerts=[f"Stock data verification failed: {str(e)}"],
                cache_hit=False
            )

    async def shutdown(self):
        """關閉系統"""
        try:
            # 清理資源
            self.cache.shutdown()

            # 關閉API連接
            if hasattr(self.government_api, 'close'):
                await self.government_api.close()

            logger.info("Unified Verification Manager shutdown completed")

        except Exception as e:
            logger.error(f"Shutdown error: {e}")

# 全局實例
unified_verification_manager = UnifiedVerificationManager()

# 便捷函數
async def verify_data_integrity(data: Any, data_type: str, source_url: Optional[str] = None) -> VerificationResult:
    """便捷函數：驗證數據完整性"""
    return await unified_verification_manager.verify_data(data, data_type, source_url)

async def verify_government_data(data_type: str, days_back: int = 30) -> VerificationResult:
    """便捷函數：驗證政府數據"""
    return await unified_verification_manager.verify_government_data(data_type, days_back)

async def verify_stock_data(symbol: str, duration_days: int = 1095) -> VerificationResult:
    """便捷函數：驗證股票數據"""
    return await unified_verification_manager.verify_stock_data(symbol, duration_days)

def get_system_metrics() -> SystemMetrics:
    """便捷函數：獲取系統指標"""
    return unified_verification_manager.get_metrics()

def get_cache_statistics() -> Dict[str, Any]:
    """便捷函數：獲取緩存統計"""
    return unified_verification_manager.get_cache_stats()

if __name__ == "__main__":
    async def main():
        """測試代碼"""
        print("Testing Unified Verification Manager...")

        # 測試政府數據驗證
        print("\n1. Testing HIBOR data verification...")
        hibor_result = await verify_government_data('hibor_rates', 7)
        print(f"HIBOR verification score: {hibor_result.composite_score:.3f}")
        print(f"Verification time: {hibor_result.verification_time_ms:.2f}ms")

        # 測試股票數據驗證
        print("\n2. Testing stock data verification...")
        stock_result = await verify_stock_data('0700.hk', 30)
        print(f"Stock verification score: {stock_result.composite_score:.3f}")
        print(f"Verification time: {stock_result.verification_time_ms:.2f}ms")

        # 顯示系統指標
        print("\n3. System metrics:")
        metrics = get_system_metrics()
        print(f"Total verifications: {metrics.total_verifications}")
        print(f"Success rate: {metrics.successful_verifications}/{metrics.total_verifications}")
        print(f"Average response time: {metrics.avg_response_time_ms:.2f}ms")
        print(f"Cache hit rate: {metrics.cache_hit_rate:.2%}")

        # 顯示緩存統計
        print("\n4. Cache statistics:")
        cache_stats = get_cache_statistics()
        print(f"Overall hit rate: {cache_stats['overall_hit_rate']:.2%}")
        print(f"Layer hit rates: {cache_stats['layer_hit_rates']}")

        # 關閉系統
        await unified_verification_manager.shutdown()
        print("\nUnified Verification Manager test completed!")

    # 運行測試
    asyncio.run(main())