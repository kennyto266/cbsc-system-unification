#!/usr/bin/env python3
"""
Phase 5: System Integration and Optimization
集成適配器 - Integration Adapter

提供與simplified_system現有API的無縫集成，確保向後兼容性。
通過適配器模式，現有代碼無需修改即可使用新的驗證功能。
"""

import asyncio
import functools
import logging
import time
from typing import Dict, List, Optional, Any, Callable, Union
from datetime import datetime
from pathlib import Path

# Import simplified system components
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api.government_data import GovernmentDataAPI, get_hibor_data, get_hkma_data, get_latest_hibor, government_api
from src.api.stock_api import StockDataAPI, get_stock_data, get_hk_stock_data, get_multiple_stocks, stock_api
from src.verification.unified_verification_manager import (
    UnifiedVerificationManager,
    VerificationResult,
    verify_data_integrity,
    verify_government_data,
    verify_stock_data,
    get_system_metrics,
    get_cache_statistics
)

# Setup logging
logger = logging.getLogger(__name__)

class VerificationEnabledGovernmentAPI(GovernmentDataAPI):
    """啟用驗證功能的政府數據API適配器"""

    def __init__(self, enable_verification: bool = True, auto_verify: bool = False):
        super().__init__()
        self.enable_verification = enable_verification
        self.auto_verify = auto_verify
        self.verification_manager = UnifiedVerificationManager() if enable_verification else None

        logger.info(f"VerificationEnabledGovernmentAPI initialized - Verification: {enable_verification}, Auto-verify: {auto_verify}")

    async def get_hibor_data_with_verification(self, days_back: int = 30) -> Dict[str, Any]:
        """獲取HIBOR數據並進行驗證"""
        if not self.enable_verification:
            return self.get_hibor_data(days_back)

        # 獲取原始數據
        raw_data = self.get_hibor_data(days_back)

        if not raw_data:
            return raw_data

        if self.auto_verify:
            # 自動驗證
            try:
                verification_result = await self.verification_manager.verify_government_data('hibor_rates', days_back)

                # 添加驗證結果到數據
                raw_data['verification'] = {
                    'enabled': True,
                    'composite_score': verification_result.composite_score,
                    'source_score': verification_result.source_score,
                    'content_score': verification_result.content_score,
                    'behavior_score': verification_result.behavior_score,
                    'confidence_interval': verification_result.confidence_interval,
                    'verification_time_ms': verification_result.verification_time_ms,
                    'alerts': verification_result.alerts,
                    'verified_at': verification_result.timestamp,
                    'cache_hit': verification_result.cache_hit
                }

                # 記錄驗證結果
                if verification_result.composite_score < 0.7:
                    logger.warning(f"HIBOR data verification score low: {verification_result.composite_score:.3f}")

                # 如果有嚴重警報，記錄錯誤
                critical_alerts = [alert for alert in verification_result.alerts if 'CRITICAL' in alert]
                if critical_alerts:
                    logger.error(f"HIBOR data critical verification alerts: {critical_alerts}")

            except Exception as e:
                logger.error(f"HIBOR data verification failed: {e}")
                raw_data['verification'] = {
                    'enabled': True,
                    'error': str(e),
                    'verified_at': datetime.now().isoformat()
                }

        return raw_data

    async def get_exchange_rates_with_verification(self, days_back: int = 30) -> Dict[str, Any]:
        """獲取匯率數據並進行驗證"""
        if not self.enable_verification:
            return self.get_exchange_rates(days_back)

        # 獲取原始數據
        raw_data = self.get_exchange_rates(days_back)

        if not raw_data:
            return raw_data

        if self.auto_verify:
            # 自動驗證
            try:
                verification_result = await self.verification_manager.verify_government_data('exchange_rates', days_back)

                # 添加驗證結果到數據
                raw_data['verification'] = {
                    'enabled': True,
                    'composite_score': verification_result.composite_score,
                    'source_score': verification_result.source_score,
                    'content_score': verification_result.content_score,
                    'behavior_score': verification_result.behavior_score,
                    'confidence_interval': verification_result.confidence_interval,
                    'verification_time_ms': verification_result.verification_time_ms,
                    'alerts': verification_result.alerts,
                    'verified_at': verification_result.timestamp,
                    'cache_hit': verification_result.cache_hit
                }

                # 記錄驗證結果
                if verification_result.composite_score < 0.7:
                    logger.warning(f"Exchange rates data verification score low: {verification_result.composite_score:.3f}")

            except Exception as e:
                logger.error(f"Exchange rates data verification failed: {e}")
                raw_data['verification'] = {
                    'enabled': True,
                    'error': str(e),
                    'verified_at': datetime.now().isoformat()
                }

        return raw_data

    async def get_monetary_base_with_verification(self, months_back: int = 12) -> Dict[str, Any]:
        """獲取貨幣基礎數據並進行驗證"""
        if not self.enable_verification:
            return self.get_monetary_base(months_back)

        # 獲取原始數據
        raw_data = self.get_monetary_base(months_back)

        if not raw_data:
            return raw_data

        if self.auto_verify:
            # 自動驗證
            try:
                verification_result = await self.verification_manager.verify_government_data('monetary_base', months_back)

                # 添加驗證結果到數據
                raw_data['verification'] = {
                    'enabled': True,
                    'composite_score': verification_result.composite_score,
                    'source_score': verification_result.source_score,
                    'content_score': verification_result.content_score,
                    'behavior_score': verification_result.behavior_score,
                    'confidence_interval': verification_result.confidence_interval,
                    'verification_time_ms': verification_result.verification_time_ms,
                    'alerts': verification_result.alerts,
                    'verified_at': verification_result.timestamp,
                    'cache_hit': verification_result.cache_hit
                }

                # 記錄驗證結果
                if verification_result.composite_score < 0.7:
                    logger.warning(f"Monetary base data verification score low: {verification_result.composite_score:.3f}")

            except Exception as e:
                logger.error(f"Monetary base data verification failed: {e}")
                raw_data['verification'] = {
                    'enabled': True,
                    'error': str(e),
                    'verified_at': datetime.now().isoformat()
                }

        return raw_data

    # 保持原有方法的向後兼容性
    def get_hibor_data(self, days_back: int = 30) -> Optional[Dict[str, Any]]:
        """保持原有API簽名"""
        return super().get_hibor_data(days_back)

    def get_exchange_rates(self, days_back: int = 30) -> Optional[Dict[str, Any]]:
        """保持原有API簽名"""
        return super().get_exchange_rates(days_back)

    def get_monetary_base(self, months_back: int = 12) -> Optional[Dict[str, Any]]:
        """保持原有API簽名"""
        return super().get_monetary_base(months_back)

    async def verify_current_hibor_data(self) -> VerificationResult:
        """驗證當前HIBOR數據"""
        if not self.enable_verification:
            raise RuntimeError("Verification is not enabled")

        return await self.verification_manager.verify_government_data('hibor_rates', 7)

    async def verify_current_exchange_rates(self) -> VerificationResult:
        """驗證當前匯率數據"""
        if not self.enable_verification:
            raise RuntimeError("Verification is not enabled")

        return await self.verification_manager.verify_government_data('exchange_rates', 7)

    async def shutdown(self):
        """關閉適配器"""
        if self.verification_manager:
            await self.verification_manager.shutdown()

class VerificationEnabledStockAPI(StockDataAPI):
    """啟用驗證功能的股票數據API適配器"""

    def __init__(self, enable_verification: bool = True, auto_verify: bool = False):
        super().__init__()
        self.enable_verification = enable_verification
        self.auto_verify = auto_verify
        self.verification_manager = UnifiedVerificationManager() if enable_verification else None

        logger.info(f"VerificationEnabledStockAPI initialized - Verification: {enable_verification}, Auto-verify: {auto_verify}")

    async def get_stock_data_with_verification(self, symbol: str, duration_days: int = 1095) -> Dict[str, Any]:
        """獲取股票數據並進行驗證"""
        if not self.enable_verification:
            return self.get_stock_data(symbol, duration_days)

        # 獲取原始數據
        raw_data = self.get_stock_data(symbol, duration_days)

        if not raw_data:
            return raw_data

        if self.auto_verify:
            # 自動驗證
            try:
                source_url = f"{self.api_base_url}/inst/getInst"
                verification_result = await self.verification_manager.verify_data(
                    raw_data, f'stock_prices', source_url
                )

                # 添加驗證結果到數據
                raw_data['verification'] = {
                    'enabled': True,
                    'composite_score': verification_result.composite_score,
                    'source_score': verification_result.source_score,
                    'content_score': verification_result.content_score,
                    'behavior_score': verification_result.behavior_score,
                    'confidence_interval': verification_result.confidence_interval,
                    'verification_time_ms': verification_result.verification_time_ms,
                    'alerts': verification_result.alerts,
                    'verified_at': verification_result.timestamp,
                    'cache_hit': verification_result.cache_hit
                }

                # 記錄驗證結果
                if verification_result.composite_score < 0.7:
                    logger.warning(f"Stock data verification score low: {symbol} - {verification_result.composite_score:.3f}")

            except Exception as e:
                logger.error(f"Stock data verification failed: {symbol} - {e}")
                raw_data['verification'] = {
                    'enabled': True,
                    'error': str(e),
                    'verified_at': datetime.now().isoformat()
                }

        return raw_data

    # 保持原有方法的向後兼容性
    def get_stock_data(self, symbol: str, duration_days: int = 1095) -> Optional[Dict[str, Any]]:
        """保持原有API簽名"""
        return super().get_stock_data(symbol, duration_days)

    def get_stock_prices_dataframe(self, symbol: str, duration_days: int = 1095):
        """保持原有API簽名"""
        return super().get_stock_prices_dataframe(symbol, duration_days)

    def get_multiple_stocks(self, symbols: List[str], duration_days: int = 1095):
        """保持原有API簽名"""
        return super().get_multiple_stocks(symbols, duration_days)

    def get_real_time_price(self, symbol: str) -> Optional[float]:
        """保持原有API簽名"""
        return super().get_real_time_price(symbol)

    async def verify_stock_symbol(self, symbol: str, duration_days: int = 1095) -> VerificationResult:
        """驗證指定股票的數據"""
        if not self.enable_verification:
            raise RuntimeError("Verification is not enabled")

        return await self.verification_manager.verify_stock_data(symbol, duration_days)

    async def verify_multiple_stocks(self, symbols: List[str], duration_days: int = 1095) -> List[VerificationResult]:
        """批量驗證多只股票數據"""
        if not self.enable_verification:
            raise RuntimeError("Verification is not enabled")

        data_batch = []
        for symbol in symbols:
            data = self.get_stock_data(symbol, duration_days)
            if data:
                source_url = f"{self.api_base_url}/inst/getInst"
                data_batch.append((data, 'stock_prices', source_url))

        return await self.verification_manager.batch_verify(data_batch)

    async def shutdown(self):
        """關閉適配器"""
        if self.verification_manager:
            await self.verification_manager.shutdown()

class BackwardCompatibilityLayer:
    """向後兼容層 - 確保現有代碼無需修改"""

    def __init__(self):
        self.verification_enabled = False
        self.auto_verification = False

        # 原始API實例
        self.original_government_api = GovernmentDataAPI()
        self.original_stock_api = StockDataAPI()

        # 增強API實例
        self.enhanced_government_api = None
        self.enhanced_stock_api = None

    def enable_verification(self, auto_verify: bool = False):
        """啟用驗證功能"""
        self.verification_enabled = True
        self.auto_verification = auto_verify

        # 創建增強API實例
        self.enhanced_government_api = VerificationEnabledGovernmentAPI(
            enable_verification=True,
            auto_verify=auto_verify
        )
        self.enhanced_stock_api = VerificationEnabledStockAPI(
            enable_verification=True,
            auto_verify=auto_verify
        )

        logger.info(f"Verification enabled - Auto-verify: {auto_verify}")

    def disable_verification(self):
        """禁用驗證功能"""
        self.verification_enabled = False

        if self.enhanced_government_api:
            asyncio.create_task(self.enhanced_government_api.shutdown())
        if self.enhanced_stock_api:
            asyncio.create_task(self.enhanced_stock_api.shutdown())

        self.enhanced_government_api = None
        self.enhanced_stock_api = None

        logger.info("Verification disabled")

    def get_government_api(self):
        """獲取政府數據API實例"""
        if self.verification_enabled and self.enhanced_government_api:
            return self.enhanced_government_api
        return self.original_government_api

    def get_stock_api(self):
        """獲取股票數據API實例"""
        if self.verification_enabled and self.enhanced_stock_api:
            return self.enhanced_stock_api
        return self.original_stock_api

    def is_verification_enabled(self) -> bool:
        """檢查是否啟用驗證"""
        return self.verification_enabled

    async def get_verification_metrics(self) -> Dict[str, Any]:
        """獲取驗證指標"""
        if not self.verification_enabled:
            return {'verification_enabled': False}

        metrics = get_system_metrics()
        cache_stats = get_cache_statistics()

        return {
            'verification_enabled': True,
            'auto_verification': self.auto_verification,
            'system_metrics': {
                'total_verifications': metrics.total_verifications,
                'successful_verifications': metrics.successful_verifications,
                'failed_verifications': metrics.failed_verifications,
                'success_rate': metrics.successful_verifications / metrics.total_verifications if metrics.total_verifications > 0 else 0,
                'avg_response_time_ms': metrics.avg_response_time_ms,
                'cache_hit_rate': metrics.cache_hit_rate,
                'error_rate': metrics.error_rate,
                'throughput_per_second': metrics.throughput_per_second
            },
            'cache_statistics': cache_stats
        }

    async def shutdown(self):
        """關閉兼容層"""
        if self.enhanced_government_api:
            await self.enhanced_government_api.shutdown()
        if self.enhanced_stock_api:
            await self.enhanced_stock_api.shutdown()

# 全局兼容層實例
backward_compatibility = BackwardCompatibilityLayer()

# 裝飾器：為現有函數添加驗證功能
def with_verification(data_type: str, auto_verify: bool = False):
    """裝飾器：為函數添加驗證功能"""
    def decorator(func: Callable):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # 執行原函數
            result = func(*args, **kwargs)

            # 如果結果是協程，等待其完成
            if asyncio.iscoroutine(result):
                result = await result

            if not backward_compatibility.is_verification_enabled() or not auto_verify:
                return result

            try:
                # 獲取驗證管理器
                verification_manager = backward_compatibility.enhanced_government_api.verification_manager

                # 執行驗證
                source_url = kwargs.get('source_url')  # 可以通過參數傳入
                verification_result = await verification_manager.verify_data(result, data_type, source_url)

                # 添加驗證結果
                if isinstance(result, dict):
                    result['verification'] = {
                        'enabled': True,
                        'composite_score': verification_result.composite_score,
                        'alerts': verification_result.alerts,
                        'verified_at': verification_result.timestamp
                    }

            except Exception as e:
                logger.error(f"Verification decorator error: {e}")
                if isinstance(result, dict):
                    result['verification'] = {
                        'enabled': True,
                        'error': str(e),
                        'verified_at': datetime.now().isoformat()
                    }

            return result

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # 同步函數的處理
            result = func(*args, **kwargs)

            if not backward_compatibility.is_verification_enabled() or not auto_verify:
                return result

            # 在新事件循環中運行異步驗證
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                verification_result = loop.run_until_complete(
                    _sync_verify_result(result, data_type)
                )
                loop.close()

                # 添加驗證結果
                if isinstance(result, dict) and verification_result:
                    result['verification'] = {
                        'enabled': True,
                        'composite_score': verification_result.composite_score,
                        'alerts': verification_result.alerts,
                        'verified_at': verification_result.timestamp
                    }

            except Exception as e:
                logger.error(f"Sync verification decorator error: {e}")
                if isinstance(result, dict):
                    result['verification'] = {
                        'enabled': True,
                        'error': str(e),
                        'verified_at': datetime.now().isoformat()
                    }

            return result

        # 根據原函數類型返回適當的包裝器
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator

async def _sync_verify_result(result: Any, data_type: str) -> Optional[VerificationResult]:
    """同步函數的異步驗證輔助函數"""
    try:
        verification_manager = backward_compatibility.enhanced_government_api.verification_manager
        return await verification_manager.verify_data(result, data_type)
    except Exception as e:
        logger.error(f"Sync verification error: {e}")
        return None

# 便捷函數 - 保持與現有代碼的兼容性
def enable_system_verification(auto_verify: bool = False):
    """啟用系統級驗證功能"""
    backward_compatibility.enable_verification(auto_verify)
    logger.info("System-wide verification enabled")

def disable_system_verification():
    """禁用系統級驗證功能"""
    backward_compatibility.disable_verification()
    logger.info("System-wide verification disabled")

def get_enhanced_government_api() -> GovernmentDataAPI:
    """獲取增強的政府數據API"""
    return backward_compatibility.get_government_api()

def get_enhanced_stock_api() -> StockDataAPI:
    """獲取增強的股票數據API"""
    return backward_compatibility.get_stock_api()

# 覆蓋原有全局變量以實現無縫集成
def patch_original_apis():
    """覆蓋原有API實例以實現無縫集成"""
    global government_api, stock_api

    # 保存原有實例的引用
    original_government_api = government_api
    original_stock_api = stock_api

    # 替換為兼容層的實例
    government_api = backward_compatibility.get_government_api()
    stock_api = backward_compatibility.get_stock_api()

    logger.info("Original APIs patched with verification-enabled versions")

# 向後兼容的便捷函數
async def get_hibor_data_verified(days_back: int = 30) -> Dict[str, Any]:
    """獲取已驗證的HIBOR數據"""
    api = get_enhanced_government_api()
    if hasattr(api, 'get_hibor_data_with_verification'):
        return await api.get_hibor_data_with_verification(days_back)
    else:
        # 降級到原始API
        return api.get_hibor_data(days_back)

async def get_stock_data_verified(symbol: str, duration_days: int = 1095) -> Dict[str, Any]:
    """獲取已驗證的股票數據"""
    api = get_enhanced_stock_api()
    if hasattr(api, 'get_stock_data_with_verification'):
        return await api.get_stock_data_with_verification(symbol, duration_days)
    else:
        # 降級到原始API
        return api.get_stock_data(symbol, duration_days)

# 配置管理
class VerificationConfig:
    """驗證配置管理"""

    @staticmethod
    def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
        """加載驗證配置"""
        default_config = {
            'enabled': True,
            'auto_verify': False,
            'government_data': {
                'verify_hibor': True,
                'verify_exchange_rates': True,
                'verify_monetary_base': True
            },
            'stock_data': {
                'verify_single_stock': True,
                'verify_multiple_stocks': True,
                'batch_verification': True
            },
            'performance': {
                'cache_enabled': True,
                'parallel_processing': True,
                'max_concurrent': 50
            },
            'alerts': {
                'telegram_enabled': True,
                'severity_levels': ['CRITICAL', 'HIGH', 'MEDIUM'],
                'alert_thresholds': {
                    'min_score': 0.7,
                    'error_rate': 0.1
                }
            }
        }

        if config_path and Path(config_path).exists():
            try:
                import yaml
                with open(config_path, 'r', encoding='utf-8') as f:
                    user_config = yaml.safe_load(f)
                # 合併配置
                return {**default_config, **user_config}
            except Exception as e:
                logger.warning(f"Failed to load verification config: {e}")

        return default_config

    @staticmethod
    def apply_config(config: Dict[str, Any]):
        """應用驗證配置"""
        if config.get('enabled', True):
            enable_system_verification(config.get('auto_verify', False))
        else:
            disable_system_verification()

        logger.info(f"Verification configuration applied: {config}")

# 全局初始化
def initialize_verification_system(config_path: Optional[str] = None, auto_verify: bool = False):
    """初始化驗證系統"""
    try:
        # 加載配置
        config = VerificationConfig.load_config(config_path)

        # 應用配置
        VerificationConfig.apply_config(config)

        # 如果需要自動驗證且配置中啟用
        if config.get('auto_verify', auto_verify):
            enable_system_verification(True)

        # 可選：自動覆蓋原有API
        if config.get('patch_original_apis', False):
            patch_original_apis()

        logger.info("Verification system initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize verification system: {e}")
        # 初始化失敗時使用禁用模式
        disable_system_verification()

if __name__ == "__main__":
    async def main():
        """測試集成適配器"""
        print("Testing Integration Adapter...")

        # 初始化驗證系統
        initialize_verification_system(auto_verify=True)

        # 測試政府數據API
        print("\n1. Testing Government Data API with verification...")
        gov_api = get_enhanced_government_api()

        if hasattr(gov_api, 'get_hibor_data_with_verification'):
            hibor_data = await gov_api.get_hibor_data_with_verification(7)
            if hibor_data and 'verification' in hibor_data:
                print(f"HIBOR data verification score: {hibor_data['verification']['composite_score']:.3f}")
            else:
                print("HIBOR data retrieved (verification may be disabled)")

        # 測試股票數據API
        print("\n2. Testing Stock Data API with verification...")
        stock_api = get_enhanced_stock_api()

        if hasattr(stock_api, 'get_stock_data_with_verification'):
            stock_data = await stock_api.get_stock_data_with_verification('0700.hk', 30)
            if stock_data and 'verification' in stock_data:
                print(f"Stock data verification score: {stock_data['verification']['composite_score']:.3f}")
            else:
                print("Stock data retrieved (verification may be disabled)")

        # 顯示系統指標
        print("\n3. Verification system metrics:")
        metrics = await backward_compatibility.get_verification_metrics()
        if metrics.get('verification_enabled'):
            sys_metrics = metrics['system_metrics']
            print(f"Total verifications: {sys_metrics['total_verifications']}")
            print(f"Success rate: {sys_metrics['success_rate']:.2%}")
            print(f"Average response time: {sys_metrics['avg_response_time_ms']:.2f}ms")
            print(f"Cache hit rate: {sys_metrics['cache_hit_rate']:.2%}")
        else:
            print("Verification is disabled")

        # 測試向後兼容的便捷函數
        print("\n4. Testing backward compatible functions...")
        try:
            hibor_verified = await get_hibor_data_verified(7)
            print(f"Backward compatible HIBOR function works: {bool(hibor_verified)}")
        except Exception as e:
            print(f"Backward compatible HIBOR function error: {e}")

        # 關閉系統
        await backward_compatibility.shutdown()
        print("\nIntegration Adapter test completed!")

    # 運行測試
    asyncio.run(main())