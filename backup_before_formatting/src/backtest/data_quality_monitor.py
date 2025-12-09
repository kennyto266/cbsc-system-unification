#!/usr/bin/env python3
"""
數據質量監控和驗證系統 - 確保所有數據的真實性和一致性
Data Quality Monitoring and Validation System - Ensuring authenticity and consistency
"""

import logging
import numpy as np
import pandas as pd
import requests
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import hashlib
from concurrent.futures import ThreadPoolExecutor
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class DataQualityAlert:
    """數據質量警報"""
    severity: str  # 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'
    source: str
    issue_type: str
    description: str
    data_sample: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.now)
    resolution: Optional[str] = None


@dataclass
class DataSourceStatus:
    """數據源狀態"""
    name: str
    url: Optional[str]
    is_active: bool
    last_check: datetime
    response_time: Optional[float]
    data_points: int
    quality_score: float
    alerts: List[DataQualityAlert] = field(default_factory=list)


class RealDataValidator:
    """真實數據驗證器 - 確保數據來自真實來源"""
    
    def __init__(self):
        # 已驗證的真實數據源
        self.authenticated_sources = {
            'central_api': {
                'url': 'http://18.180.162.113:9191/inst/getInst',
                'type': 'stock_price',
                'verification_required': True
            },
            'hkma_hibor': {
                'url': 'https://www.hkma.gov.hk',
                'type': 'interest_rate',
                'verification_required': True
            },
            'census_statistics': {
                'url': 'https://www.censtatd.gov.hk',
                'type': 'economic_data',
                'verification_required': True
            }
        }
        
        # 模擬數據檢測規則
        self.mock_data_patterns = {
            'perfect_sequences': [1, 2, 3, 4, 5],  # 完美的數列
            'repeated_values': 10,  # 連續重複值閾值
            'unnatural_precision': 8,  # 不自然的小數位數
            'linear_patterns': 0.999,  # 線性相關性閾值
            'random_distribution': 'uniform'  # 均勻分佈檢測
        }
    
    def validate_stock_price_authenticity(self, data: pd.DataFrame, symbol: str) -> Dict[str, Any]:
        """驗證股價數據真實性"""
        validation_result = {
            'is_authentic': True,
            'confidence_score': 1.0,
            'alerts': [],
            'data_fingerprint': None
        }
        
        if data.empty:
            validation_result['is_authentic'] = False
            validation_result['alerts'].append(DataQualityAlert(
                severity='CRITICAL',
                source='stock_price',
                issue_type='EMPTY_DATA',
                description=f"No data available for {symbol}"
            ))
            return validation_result
        
        close_prices = data['close'].dropna()
        
        # 檢測模擬數據模式
        
        # 1. 檢測完美線性趨勢（模擬數據特徵）
        if len(close_prices) > 10:
            # 計算價格的線性相關性
            x = np.arange(len(close_prices))
            correlation = np.corrcoef(x, close_prices)[0, 1]
            
            if abs(correlation) > self.mock_data_patterns['linear_patterns']:
                validation_result['is_authentic'] = False
                validation_result['confidence_score'] -= 0.4
                validation_result['alerts'].append(DataQualityAlert(
                    severity='HIGH',
                    source='stock_price',
                    issue_type='LINEAR_PATTERN',
                    description=f"Suspicious linear pattern detected (r={correlation:.4f})",
                    data_sample={'correlation': correlation, 'symbol': symbol}
                ))
        
        # 2. 檢測重複值模式
        consecutive_repeats = 0
        max_consecutive_repeats = 0
        for i in range(1, len(close_prices)):
            if close_prices.iloc[i] == close_prices.iloc[i-1]:
                consecutive_repeats += 1
                max_consecutive_repeats = max(max_consecutive_repeats, consecutive_repeats)
            else:
                consecutive_repeats = 0
        
        if max_consecutive_repeats > self.mock_data_patterns['repeated_values']:
            validation_result['is_authentic'] = False
            validation_result['confidence_score'] -= 0.3
            validation_result['alerts'].append(DataQualityAlert(
                severity='HIGH',
                source='stock_price',
                issue_type='REPEATED_VALUES',
                description=f"Too many consecutive identical values ({max_consecutive_repeats})",
                data_sample={'max_repeats': max_consecutive_repeats, 'symbol': symbol}
            ))
        
        # 3. 檢測不自然的小數位數
        decimal_places = []
        for price in close_prices.head(100):  # 檢查前100個數據點
            if isinstance(price, float):
                decimal_str = str(price).split('.')[1] if '.' in str(price) else ''
                decimal_places.append(len(decimal_str.rstrip('0')))
        
        if decimal_places:
            avg_decimal_places = np.mean(decimal_places)
            if avg_decimal_places > self.mock_data_patterns['unnatural_precision']:
                validation_result['confidence_score'] -= 0.2
                validation_result['alerts'].append(DataQualityAlert(
                    severity='MEDIUM',
                    source='stock_price',
                    issue_type='UNNATURAL_PRECISION',
                    description=f"Unusual decimal precision ({avg_decimal_places:.1f} places)",
                    data_sample={'avg_decimal_places': avg_decimal_places, 'symbol': symbol}
                ))
        
        # 4. 價格合理性檢查
        price_changes = close_prices.pct_change().dropna()
        
        # 檢查是否有異常大的單日變動（可能是模擬數據）
        extreme_changes = (abs(price_changes) > 0.5).sum()  # 單日超過50%變動
        if extreme_changes > len(price_changes) * 0.01:  # 超過1%的數據點
            validation_result['confidence_score'] -= 0.1
            validation_result['alerts'].append(DataQualityAlert(
                severity='MEDIUM',
                source='stock_price',
                issue_type='EXTREME_VOLATILITY',
                description=f"Unusual volatility pattern ({extreme_changes} extreme changes)",
                data_sample={'extreme_changes': extreme_changes, 'symbol': symbol}
            ))
        
        # 5. 生成數據指紋
        validation_result['data_fingerprint'] = self._generate_data_fingerprint(close_prices)
        
        return validation_result
    
    def validate_economic_data_authenticity(self, data: pd.DataFrame, source_type: str) -> Dict[str, Any]:
        """驗證經濟數據真實性"""
        validation_result = {
            'is_authentic': True,
            'confidence_score': 1.0,
            'alerts': [],
            'source_type': source_type
        }
        
        if data.empty:
            validation_result['is_authentic'] = False
            validation_result['alerts'].append(DataQualityAlert(
                severity='CRITICAL',
                source=source_type,
                issue_type='EMPTY_DATA',
                description=f"No economic data available for {source_type}"
            ))
            return validation_result
        
        # 經濟數據特有的驗證規則
        
        # 1. 檢查數據頻率的合理性
        if len(data) > 1:
            time_diffs = data.index.to_series().diff().dt.days.dropna()
            avg_diff = time_diffs.mean()
            
            if source_type == 'hibor':
                # HIBOR應該是每日數據
                if not (0.5 <= avg_diff <= 2.0):
                    validation_result['confidence_score'] -= 0.3
                    validation_result['alerts'].append(DataQualityAlert(
                        severity='MEDIUM',
                        source=source_type,
                        issue_type='INVALID_FREQUENCY',
                        description=f"HIBOR data should be daily, average gap: {avg_diff:.1f} days"
                    ))
            elif source_type in ['gdp', 'trade']:
                # GDP和貿易數據應該是月度或季度
                if not (20 <= avg_diff <= 120):
                    validation_result['confidence_score'] -= 0.3
                    validation_result['alerts'].append(DataQualityAlert(
                        severity='MEDIUM',
                        source=source_type,
                        issue_type='INVALID_FREQUENCY',
                        description=f"Economic data should be monthly/quarterly, average gap: {avg_diff:.1f} days"
                    ))
        
        # 2. 檢查數值範圍的合理性
        numeric_columns = data.select_dtypes(include=[np.number]).columns
        for col in numeric_columns:
            values = data[col].dropna()
            
            if len(values) == 0:
                continue
            
            # 檢查負值
            if source_type in ['hibor', 'rate'] and (values < 0).any():
                validation_result['is_authentic'] = False
                validation_result['alerts'].append(DataQualityAlert(
                    severity='HIGH',
                    source=source_type,
                    issue_type='NEGATIVE_RATES',
                    description=f"Negative interest rates found in {col}"
                ))
            
            # 檢查異常大的數值
            if source_type == 'hibor':
                if (values > 100).any():  # HIBOR超過100%是不現實的
                    validation_result['confidence_score'] -= 0.2
                    validation_result['alerts'].append(DataQualityAlert(
                        severity='MEDIUM',
                        source=source_type,
                        issue_type='UNREALISTIC_VALUES',
                        description=f"Unrealistic HIBOR values (>100%) in {col}"
                    ))
        
        return validation_result
    
    def _generate_data_fingerprint(self, data: pd.Series) -> str:
        """生成數據指紋用於驗證"""
        # 使用數據的統計特徵生成唯一指紋
        features = [
            len(data),
            float(data.mean()),
            float(data.std()),
            float(data.skew()),
            float(data.kurtosis()),
            float(data.min()),
            float(data.max()),
            float(data.quantile(0.25)),
            float(data.quantile(0.75))
        ]
        
        feature_str = json.dumps(features, sort_keys=True)
        fingerprint = hashlib.sha256(feature_str.encode()).hexdigest()[:16]
        
        return fingerprint
    
    async def verify_source_connection(self, source_name: str) -> DataSourceStatus:
        """驗證數據源連接狀態"""
        if source_name not in self.authenticated_sources:
            return DataSourceStatus(
                name=source_name,
                url=None,
                is_active=False,
                last_check=datetime.now(),
                response_time=None,
                data_points=0,
                quality_score=0.0,
                alerts=[DataQualityAlert(
                    severity='HIGH',
                    source=source_name,
                    issue_type='UNKNOWN_SOURCE',
                    description=f"Unknown data source: {source_name}"
                )]
            )
        
        source_config = self.authenticated_sources[source_name]
        status = DataSourceStatus(
            name=source_name,
            url=source_config['url'],
            is_active=False,
            last_check=datetime.now(),
            response_time=None,
            data_points=0,
            quality_score=1.0
        )
        
        try:
            start_time = datetime.now()
            
            if source_name == 'central_api':
                # 測試中央API連接
                response = requests.get(
                    f"{source_config['url']}?symbol=0700.hk&duration=7",
                    timeout=10
                )
                
                status.response_time = (datetime.now() - start_time).total_seconds()
                
                if response.status_code == 200:
                    status.is_active = True
                    data = response.json()
                    
                    # 檢查數據結構
                    if 'data' in data and 'close' in data['data']:
                        close_data = data['data']['close']
                        status.data_points = len(close_data)
                        status.quality_score = 0.9  # 良好質量
                    else:
                        status.quality_score = 0.5
                        status.alerts.append(DataQualityAlert(
                            severity='MEDIUM',
                            source=source_name,
                            issue_type='INVALID_STRUCTURE',
                            description="Unexpected data structure"
                        ))
                else:
                    status.quality_score = 0.0
                    status.alerts.append(DataQualityAlert(
                        severity='HIGH',
                        source=source_name,
                        issue_type='CONNECTION_FAILED',
                        description=f"HTTP {response.status_code}: {response.reason}"
                    ))
            
            elif source_name in ['hkma_hibor', 'census_statistics']:
                # 測試政府網站連接
                response = requests.get(source_config['url'], timeout=10)
                
                status.response_time = (datetime.now() - start_time).total_seconds()
                
                if response.status_code == 200:
                    status.is_active = True
                    status.quality_score = 0.8
                else:
                    status.quality_score = 0.0
                    status.alerts.append(DataQualityAlert(
                        severity='HIGH',
                        source=source_name,
                        issue_type='CONNECTION_FAILED',
                        description=f"HTTP {response.status_code}: {response.reason}"
                    ))
        
        except Exception as e:
            status.quality_score = 0.0
            status.alerts.append(DataQualityAlert(
                severity='HIGH',
                source=source_name,
                issue_type='CONNECTION_ERROR',
                description=f"Connection failed: {str(e)}"
            ))
        
        return status


class ComprehensiveDataQualityMonitor:
    """綜合數據質量監控系統"""
    
    def __init__(self):
        self.validator = RealDataValidator()
        self.monitoring_history = {}
        self.active_alerts = []
        self.quality_reports = {}
        
    async def comprehensive_quality_check(self, 
                                        price_data: pd.DataFrame,
                                        economic_data: Dict[str, pd.DataFrame],
                                        symbol: str = None) -> Dict[str, Any]:
        """執行綜合數據質量檢查"""
        quality_report = {
            'overall_quality_score': 0.0,
            'authenticity_verified': False,
            'data_sources': {},
            'cross_source_consistency': {},
            'alerts': [],
            'recommendations': [],
            'timestamp': datetime.now().isoformat()
        }
        
        # 1. 驗證股價數據真實性
        if not price_data.empty:
            stock_validation = self.validator.validate_stock_price_authenticity(price_data, symbol or 'UNKNOWN')
            quality_report['data_sources']['stock_price'] = stock_validation
            quality_report['alerts'].extend(stock_validation['alerts'])
        
        # 2. 驗證經濟數據真實性
        for source_name, data in economic_data.items():
            if not data.empty:
                econ_validation = self.validator.validate_economic_data_authenticity(data, source_name)
                quality_report['data_sources'][source_name] = econ_validation
                quality_report['alerts'].extend(econ_validation['alerts'])
        
        # 3. 跨數據源一致性檢查
        consistency_result = self._check_cross_source_consistency(price_data, economic_data)
        quality_report['cross_source_consistency'] = consistency_result
        
        # 4. 計算總體質量分數
        individual_scores = []
        for source, validation in quality_report['data_sources'].items():
            if isinstance(validation, dict) and 'confidence_score' in validation:
                individual_scores.append(validation['confidence_score'])
        
        if individual_scores:
            quality_report['overall_quality_score'] = np.mean(individual_scores)
        
        # 5. 驗證真實性
        quality_report['authenticity_verified'] = all(
            v.get('is_authentic', False) 
            for v in quality_report['data_sources'].values() 
            if isinstance(v, dict)
        )
        
        # 6. 生成建議
        quality_report['recommendations'] = self._generate_recommendations(quality_report)
        
        return quality_report
    
    def _check_cross_source_consistency(self, price_data: pd.DataFrame, 
                                      economic_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """檢查跨數據源一致性"""
        consistency_result = {
            'overall_consistency_score': 1.0,
            'time_alignment_issues': [],
            'data_gaps': [],
            'frequency_mismatches': []
        }
        
        if price_data.empty:
            return consistency_result
        
        price_dates = set(price_data.index)
        
        for source_name, econ_df in economic_data.items():
            if econ_df.empty:
                continue
            
            econ_dates = set(econ_df.index)
            
            # 檢查時間對齊
            overlap = price_dates.intersection(econ_dates)
            overlap_ratio = len(overlap) / len(price_dates)
            
            if overlap_ratio < 0.5:
                consistency_result['time_alignment_issues'].append({
                    'source': source_name,
                    'overlap_ratio': overlap_ratio,
                    'price_data_points': len(price_dates),
                    'economic_data_points': len(econ_dates)
                })
                consistency_result['overall_consistency_score'] -= 0.2
            
            # 檢查數據間隔一致性
            if len(econ_df) > 1:
                econ_diffs = econ_df.index.to_series().diff().dt.days.dropna()
                if len(econ_diffs) > 0:
                    econ_frequency = econ_diffs.mode().iloc[0] if not econ_diffs.mode().empty else econ_diffs.mean()
                    
                    # 根據數據源類型檢查頻率合理性
                    if source_name == 'hibor' and econ_frequency > 2:
                        consistency_result['frequency_mismatches'].append({
                            'source': source_name,
                            'expected_frequency': 'daily',
                            'actual_frequency': f'~{econ_frequency:.1f} days'
                        })
                        consistency_result['overall_consistency_score'] -= 0.1
        
        return consistency_result
    
    def _generate_recommendations(self, quality_report: Dict[str, Any]) -> List[str]:
        """基於質量檢查結果生成建議"""
        recommendations = []
        
        # 基於警報生成建議
        critical_alerts = [a for a in quality_report['alerts'] if a.severity == 'CRITICAL']
        if critical_alerts:
            recommendations.append("立即解決關鍵數據質量問題，特別是空數據問題")
        
        # 基於真實性驗證結果
        if not quality_report['authenticity_verified']:
            recommendations.append("加強數據源驗證，確保所有數據來自真實來源")
        
        # 基於總體質量分數
        if quality_report['overall_quality_score'] < 0.7:
            recommendations.append("整體數據質量偏低，建議檢查數據收集和處理流程")
        
        # 基於跨源一致性
        consistency = quality_report['cross_source_consistency']
        if consistency['overall_consistency_score'] < 0.8:
            recommendations.append("改善不同數據源之間的時間對齊和頻率一致性")
        
        # 如果沒有嚴重問題
        if quality_report['overall_quality_score'] > 0.9 and quality_report['authenticity_verified']:
            recommendations.append("數據質量良好，可以進行量化分析")
        
        return recommendations
    
    async def monitor_all_sources(self) -> Dict[str, DataSourceStatus]:
        """監控所有已配置的數據源"""
        monitoring_tasks = []
        
        for source_name in self.validator.authenticated_sources.keys():
            task = self.validator.verify_source_connection(source_name)
            monitoring_tasks.append(task)
        
        source_statuses = await asyncio.gather(*monitoring_tasks, return_exceptions=True)
        
        # 組織結果
        status_dict = {}
        source_names = list(self.validator.authenticated_sources.keys())
        
        for i, status in enumerate(source_statuses):
            if i < len(source_names):
                if isinstance(status, Exception):
                    status_dict[source_names[i]] = DataSourceStatus(
                        name=source_names[i],
                        url=self.validator.authenticated_sources[source_names[i]]['url'],
                        is_active=False,
                        last_check=datetime.now(),
                        response_time=None,
                        data_points=0,
                        quality_score=0.0,
                        alerts=[DataQualityAlert(
                            severity='HIGH',
                            source=source_names[i],
                            issue_type='MONITORING_ERROR',
                            description=f"Monitoring failed: {str(status)}"
                        )]
                    )
                else:
                    status_dict[source_names[i]] = status
        
        return status_dict
    
    def generate_quality_dashboard_data(self) -> Dict[str, Any]:
        """生成質量監控儀表板數據"""
        return {
            'monitoring_summary': {
                'total_sources': len(self.validator.authenticated_sources),
                'active_alerts': len(self.active_alerts),
                'last_check': datetime.now().isoformat()
            },
            'source_statuses': {},  # 需要通過 monitor_all_sources() 填充
            'quality_trends': {},    # 可以添加歷史質量趨勢
            'alert_summary': {
                'critical': len([a for a in self.active_alerts if a.severity == 'CRITICAL']),
                'high': len([a for a in self.active_alerts if a.severity == 'HIGH']),
                'medium': len([a for a in self.active_alerts if a.severity == 'MEDIUM']),
                'low': len([a for a in self.active_alerts if a.severity == 'LOW'])
            }
        }