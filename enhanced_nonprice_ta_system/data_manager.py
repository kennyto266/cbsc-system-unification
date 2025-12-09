#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Enhanced Data Manager
增強數據源管理器 - 基於OpenSpec enhance-nonprice-ta-system提案

管理所有數據源，提供統一接口、緩存、錯誤處理等功能
保持所有9個香港政府數據源的完整功能
"""

import requests
import json
import time
import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import pandas as pd

# Import enhanced components
from .intelligent_cache import IntelligentCache, CacheConfig
from .error_handler import EnhancedErrorHandler, ErrorSeverity, ErrorCategory

@dataclass
class DataSourceConfig:
    """數據源配置"""
    code: str
    name: str
    description: str
    update_frequency: str  # daily, weekly, monthly, quarterly
    priority: int  # 1-10, 10為最高
    enabled: bool = True
    api_endpoint: Optional[str] = None
    fallback_enabled: bool = True
    cache_ttl_seconds: int = 3600

@dataclass
class StockDataConfig:
    """股票數據配置"""
    base_url: str = "http://18.180.162.113:9191/inst/getInst"
    default_duration: int = 365
    timeout_seconds: int = 30
    retry_attempts: int = 3
    symbols: List[str] = field(default_factory=lambda: ["0700.hk"])

class EnhancedDataManager:
    """
    增強數據源管理器
    統一管理所有數據源，提供高性能、高可靠性的數據接入
    """

    def __init__(self,
                 cache_config: Optional[CacheConfig] = None,
                 stock_config: Optional[StockDataConfig] = None):
        self.stock_config = stock_config or StockDataConfig()
        self.cache_config = cache_config or CacheConfig()

        # Initialize enhanced components
        self.cache_system = IntelligentCache(self.cache_config)
        self.error_handler = EnhancedErrorHandler()

        # Setup logging
        self.logger = logging.getLogger('EnhancedDataManager')
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

        # PRESERVE: 保持所有9個香港政府非價格數據源
        self.data_sources = self._initialize_data_sources()

        # 數據存儲
        self.stock_data: Dict[str, Dict[str, Any]] = {}
        self.gov_data: Dict[str, List[float]] = {}

        # 數據質量統計
        self.data_quality_stats: Dict[str, Dict[str, Any]] = {}

        self.logger.info(f"[INIT] 增強數據源管理器初始化")
        self.logger.info(f"[INIT] 政府數據源: {len(self.data_sources)} 個")
        self.logger.info(f"[INIT] 緩存系統: 啟用")
        self.logger.info(f"[INIT] 錯誤處理: 啟用")

    def _initialize_data_sources(self) -> Dict[str, DataSourceConfig]:
        """初始化所有數據源配置"""
        sources = {
            'HB': DataSourceConfig(
                code='HB',
                name='HIBOR利率數據',
                description='香港銀行同業拆放利率',
                update_frequency='daily',
                priority=10,  # 最高優先級
                cache_ttl_seconds=1800  # 30分鐘
            ),
            'MB': DataSourceConfig(
                code='MB',
                name='貨幣基礎數據',
                description='香港貨幣基礎統計',
                update_frequency='daily',
                priority=9,
                cache_ttl_seconds=3600  # 1小時
            ),
            'GD': DataSourceConfig(
                code='GD',
                name='GDP數據',
                description='本地生產總值',
                update_frequency='quarterly',
                priority=8,
                cache_ttl_seconds=86400  # 24小時
            ),
            'RT': DataSourceConfig(
                code='RT',
                name='零售銷售數據',
                description='零售業銷售額統計',
                update_frequency='monthly',
                priority=7,
                cache_ttl_seconds=7200  # 2小時
            ),
            'PT': DataSourceConfig(
                code='PT',
                name='物業市場數據',
                description='物業市場統計數據',
                update_frequency='monthly',
                priority=6,
                cache_ttl_seconds=7200  # 2小時
            ),
            'TR': DataSourceConfig(
                code='TR',
                name='貿易數據',
                description='進出口貿易統計',
                update_frequency='monthly',
                priority=6,
                cache_ttl_seconds=7200  # 2小時
            ),
            'TS': DataSourceConfig(
                code='TS',
                name='旅遊數據',
                description='旅遊業統計數據',
                update_frequency='monthly',
                priority=5,
                cache_ttl_seconds=10800  # 3小時
            ),
            'CP': DataSourceConfig(
                code='CP',
                name='CPI通脹數據',
                description='消費物價指數',
                update_frequency='monthly',
                priority=7,
                cache_ttl_seconds=3600  # 1小時
            ),
            'UE': DataSourceConfig(
                code='UE',
                name='失業率數據',
                description='失業率統計',
                update_frequency='monthly',
                priority=6,
                cache_ttl_seconds=3600  # 1小時
            )
        }

        # Sort by priority
        return dict(sorted(sources.items(), key=lambda x: x[1].priority, reverse=True))

    def fetch_stock_data(self, symbol: str = "0700.hk", duration: int = None) -> bool:
        """
        獲取股票數據
        PRESERVE: 保持原有邏輯，添加增強功能
        """
        if duration is None:
            duration = self.stock_config.default_duration

        cache_key = f"stock_data_{symbol}_{duration}"

        # 檢查緩存
        cached_data = self.cache_system.get(cache_key)
        if cached_data:
            self.stock_data[symbol] = cached_data
            self.logger.info(f"[CACHE] 使用緩存股票數據: {symbol}")
            return True

        def fallback_action():
            """後備行動"""
            # 生成基於歷史數據的後備數據
            fallback_data = self._generate_stock_fallback_data(symbol, duration)
            self.stock_data[symbol] = fallback_data

        with self.error_handler.handle_api_errors(f"fetch_stock_data_{symbol}", fallback_action):
            self.logger.info(f"[API] 獲取真實{symbol}價格數據...")

            params = {"symbol": symbol.lower(), "duration": duration}
            response = requests.get(
                self.stock_config.base_url,
                params=params,
                timeout=self.stock_config.timeout_seconds
            )
            response.raise_for_status()
            data = response.json()

            if 'data' in data and 'close' in data['data']:
                close_data = data['data']['close']
                stock_data = {
                    'dates': list(close_data.keys()),
                    'close': list(close_data.values()),
                    'symbol': symbol,
                    'duration': duration,
                    'fetch_time': time.time(),
                    'source': 'central_api'
                }

                self.stock_data[symbol] = stock_data

                # 緩存結果
                self.cache_system.set(cache_key, stock_data)

                self.logger.info(f"[API] 成功獲取 {symbol}: {len(stock_data['close'])} 條真實價格記錄")

                # 記錄數據質量
                self._record_data_quality('stock', symbol, stock_data)

                return True
            else:
                raise ValueError("API數據格式不正確")

    def _generate_stock_fallback_data(self, symbol: str, duration: int) -> Dict[str, Any]:
        """生成股票後備數據"""
        self.logger.warning(f"[FALLBACK] 為 {symbol} 生成後備數據")

        # 基於騰訊歷史價格區間的後備數據
        import numpy as np

        dates = pd.date_range(end=datetime.now(), periods=duration, freq='D')

        # 生成合理的股價走势 (基於騰訊歷史範圍 252.45 - 677.50)
        base_price = 450.0  # 中間價
        volatility = 0.03   # 日波動率

        returns = np.random.normal(0, volatility, duration)
        prices = [base_price]

        for i in range(1, duration):
            new_price = prices[-1] * (1 + returns[i])
            prices.append(max(new_price, 1.0))  # 確保價格為正

        return {
            'dates': [d.strftime('%Y-%m-%d') for d in dates],
            'close': prices,
            'symbol': symbol,
            'duration': duration,
            'fetch_time': time.time(),
            'source': 'fallback_generator'
        }

    async def fetch_all_government_data(self, data_length: int = 252) -> bool:
        """
        獲取所有政府數據
        PRESERVE: 保持原有HKMA API集成，添加增強功能
        """
        self.logger.info("[GOV] 開始獲取香港政府非價格數據源...")

        # 按優先級排序的數據源
        sorted_sources = sorted(
            self.data_sources.items(),
            key=lambda x: x[1].priority,
            reverse=True
        )

        # 並行獲取高優先級數據源
        high_priority_tasks = []
        low_priority_tasks = []

        for source_code, config in sorted_sources:
            if config.priority >= 7:  # 高優先級 (HB, MB, GD, CP)
                high_priority_tasks.append(self._fetch_single_gov_source(source_code, config, data_length))
            else:  # 低優先級
                low_priority_tasks.append(self._fetch_single_gov_source(source_code, config, data_length))

        # 首先獲取高優先級數據
        if high_priority_tasks:
            high_priority_results = await asyncio.gather(*high_priority_tasks, return_exceptions=True)
            self._process_gov_results(high_priority_results, [s[0] for s in sorted_sources if s[1].priority >= 7])

        # 然後獲取低優先級數據
        if low_priority_tasks:
            low_priority_results = await asyncio.gather(*low_priority_tasks, return_exceptions=True)
            self._process_gov_results(low_priority_results, [s[0] for s in sorted_sources if s[1].priority < 7])

        success_count = len([code for code in self.gov_data.keys() if self.gov_data[code]])
        total_count = len(self.data_sources)

        self.logger.info(f"[GOV] [COMPLETE] 成功獲取 {success_count}/{total_count} 個數據源")

        # 數據質量檢查
        self._validate_all_gov_data()

        return success_count > 0

    async def _fetch_single_gov_source(self, source_code: str, config: DataSourceConfig, data_length: int):
        """獲取單個政府數據源"""
        cache_key = f"gov_data_{source_code}_{data_length}"

        # 檢查緩存
        cached_data = self.cache_system.get(cache_key)
        if cached_data:
            return source_code, cached_data, True

        try:
            # Import real HKMA data integration
            from hkma_data_integration import get_hkma_data_for_optimizer

            # 獲取真實數據
            real_data = await get_hkma_data_for_optimizer({source_code: config.name}, data_length)

            if source_code in real_data:
                data = real_data[source_code]
                self.cache_system.set(cache_key, data)
                return source_code, data, True
            else:
                raise ValueError(f"數據源 {source_code} 未返回數據")

        except Exception as e:
            self.error_handler.record_error(
                e,
                severity=ErrorSeverity.MEDIUM,
                category=ErrorCategory.API_ERROR,
                context={'source_code': source_code, 'data_length': data_length}
            )

            # 使用後備數據
            if config.fallback_enabled:
                fallback_data = self._generate_gov_fallback_data(source_code, data_length)
                self.cache_system.set(cache_key, fallback_data)
                return source_code, fallback_data, False
            else:
                return source_code, None, False

    def _generate_gov_fallback_data(self, source_code: str, data_length: int) -> List[float]:
        """
        生成政府數據後備數據
        PRESERVE: 完全保持原有後備數據邏輯
        """
        self.logger.warning(f"[FALLBACK] 為 {source_code} 生成後備數據")

        # 基於真實歷史平均值的後備配置 (保持原有邏輯)
        fallback_configs = {
            'HB': [3.5] * data_length,  # HIBOR利率
            'MB': [2000000] * data_length,  # 貨幣基礎
            'GD': [100] * data_length,  # GDP
            'RT': [120] * data_length,  # 零售
            'PT': [180] * data_length,  # 物業
            'TR': [400] * data_length,  # 貿易
            'TS': [30000] * data_length,  # 旅遊
            'CP': [105] * data_length,  # CPI
            'UE': [3.2] * data_length   # 失業率
        }

        return fallback_configs.get(source_code, [100.0] * data_length)

    def _process_gov_results(self, results: List[Tuple], source_codes: List[str]):
        """處理政府數據獲取結果"""
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"[GOV] 數據源 {source_codes[i]} 獲取失敗: {result}")
                continue

            source_code, data, success = result
            if data is not None:
                self.gov_data[source_code] = data

                # 記錄數據質量
                self._record_data_quality('gov', source_code, data)

                status = "真實數據" if success else "後備數據"
                self.logger.info(f"[GOV] [OK] {source_code} ({self.data_sources[source_code].name}): "
                               f"{len(data)} 條記錄 ({status})")

    def _record_data_quality(self, data_type: str, source: str, data: Union[List, Dict]):
        """記錄數據質量統計"""
        if source not in self.data_quality_stats:
            self.data_quality_stats[source] = {
                'fetch_count': 0,
                'success_count': 0,
                'cache_hits': 0,
                'fallback_count': 0,
                'last_fetch_time': None,
                'data_integrity_score': 100.0
            }

        stats = self.data_quality_stats[source]
        stats['fetch_count'] += 1
        stats['last_fetch_time'] = time.time()

        if isinstance(data, dict) and data.get('source') == 'central_api':
            stats['success_count'] += 1
        elif isinstance(data, list) and len(data) > 0:
            stats['success_count'] += 1

    def _validate_all_gov_data(self):
        """驗證所有政府數據質量"""
        for source_code, data in self.gov_data.items():
            if not self.error_handler.validate_data_integrity(
                data,
                f"gov_{source_code}",
                self._get_expected_range(source_code)
            ):
                self.logger.warning(f"[QUALITY] 數據源 {source_code} 質量檢查失敗")

    def _get_expected_range(self, source_code: str) -> Optional[Tuple[float, float]]:
        """獲取數據源的預期範圍"""
        ranges = {
            'HB': (0.5, 10.0),      # HIBOR利率範圍
            'MB': (1000000, 5000000),  # 貨幣基礎範圍
            'GD': (50, 200),         # GDP指數範圍
            'RT': (80, 200),         # 零售指數範圍
            'PT': (100, 300),        # 物業指數範圍
            'TR': (200, 800),        # 貿易指數範圍
            'TS': (10000, 50000),    # 旅遊指數範圍
            'CP': (90, 120),         # CPI範圍
            'UE': (1.0, 8.0)         # 失業率範圍
        }
        return ranges.get(source_code)

    def get_data_summary(self) -> Dict[str, Any]:
        """獲取數據摘要"""
        return {
            'stock_data_count': len(self.stock_data),
            'gov_data_count': len(self.gov_data),
            'data_sources': {
                code: {
                    'name': config.name,
                    'enabled': config.enabled,
                    'priority': config.priority,
                    'has_data': code in self.gov_data and len(self.gov_data[code]) > 0
                }
                for code, config in self.data_sources.items()
            },
            'data_quality': self.data_quality_stats,
            'cache_stats': self.cache_system.get_cache_statistics(),
            'error_summary': self.error_handler.get_error_summary()
        }

    def refresh_data(self, force_refresh: bool = False) -> bool:
        """刷新數據"""
        self.logger.info("[REFRESH] 開始數據刷新...")

        if force_refresh:
            self.cache_system.clear()
            self.logger.info("[REFRESH] 已清空緩存")

        success = True

        # 刷新股票數據
        for symbol in self.stock_config.symbols:
            if not self.fetch_stock_data(symbol):
                success = False

        # 刷新政府數據 (異步)
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            gov_success = loop.run_until_complete(self.fetch_all_government_data())
            success = success and gov_success
            loop.close()
        except Exception as e:
            self.error_handler.record_error(
                e,
                severity=ErrorSeverity.HIGH,
                category=ErrorCategory.SYSTEM_ERROR,
                context={'operation': 'refresh_gov_data'}
            )
            success = False

        status = "成功" if success else "部分失敗"
        self.logger.info(f"[REFRESH] 數據刷新完成: {status}")

        return success

    def export_data_report(self, filename: Optional[str] = None) -> str:
        """導出數據質量報告"""
        import time

        if not filename:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"data_quality_report_{timestamp}.json"

        report = {
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
            'data_summary': self.get_data_summary(),
            'data_sources_detail': {
                code: {
                    'config': {
                        'name': config.name,
                        'description': config.description,
                        'update_frequency': config.update_frequency,
                        'priority': config.priority,
                        'enabled': config.enabled
                    },
                    'status': 'available' if code in self.gov_data else 'unavailable',
                    'quality_stats': self.data_quality_stats.get(code, {})
                }
                for code, config in self.data_sources.items()
            }
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        self.logger.info(f"數據質量報告已導出: {filename}")
        return filename