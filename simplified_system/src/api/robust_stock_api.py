#!/usr/bin/env python3
"""
強化的股票數據API - 多數據源支持
Robust Stock API - Multi-Source Support with High Availability

向後兼容的API接口，內置多數據源和故障轉移功能
"""

import asyncio
import logging
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
import pandas as pd

# Import from our multi-source system
from .multi_source_data_manager import (
    MultiSourceDataManager, get_data_manager, get_stock_data_robust,
    DataFetchResult, DataSourceStatus
)
from .data_source_monitor import get_monitor
from config.config_manager import get_data_source_config

# Setup logging
logger = logging.getLogger(__name__)

class RobustStockAPI:
    """
    強化的股票數據API接口
    提供向後兼容性和高可用性
    """

    def __init__(self, auto_start: bool = True):
        """
        初始化強化API

        Args:
            auto_start: 是否自動啟動多數據源管理器
        """
        self._data_manager: Optional[MultiSourceDataManager] = None
        self._initialized = False
        self._config = get_data_source_config()

        if auto_start:
            asyncio.create_task(self._ensure_initialized())

        logger.info("Robust Stock API initialized")

    async def _ensure_initialized(self):
        """確保組件已初始化"""
        if not self._initialized:
            try:
                self._data_manager = await get_data_manager()
                self._initialized = True
                logger.info("Multi-source data manager initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize multi-source manager: {e}")

    async def _get_data_manager(self) -> MultiSourceDataManager:
        """獲取數據管理器實例"""
        if not self._initialized:
            await self._ensure_initialized()
        return self._data_manager

    def get_stock_data(
        self, symbol: str, duration_days: int = 1095
    ) -> Optional[Dict[str, Any]]:
        """
        獲取股票數據 - 向後兼容接口

        Args:
            symbol: 股票代碼 (e.g., "0700.hk")
            duration_days: 數據天數

        Returns:
            股票數據字典或None
        """
        try:
            # Run async function in sync context
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're in an async context, create a task
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(self._get_stock_data_sync, symbol, duration_days)
                    result = future.result(timeout=60)
            else:
                # If we're in a sync context, run the coroutine
                result = loop.run_until_complete(self._get_stock_data_async(symbol, duration_days))

            return self._extract_legacy_data(result)

        except Exception as e:
            logger.error(f"Error in get_stock_data for {symbol}: {e}")
            return None

    async def _get_stock_data_async(self, symbol: str, duration_days: int) -> DataFetchResult:
        """異步版本的數據獲取"""
        await self._ensure_initialized()
        return await self._data_manager.get_stock_data(symbol, duration_days)

    def _get_stock_data_sync(self, symbol: str, duration_days: int) -> DataFetchResult:
        """同步版本的數據獲取"""
        # Create new event loop for this call
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self._get_stock_data_async(symbol, duration_days))
        finally:
            loop.close()

    def _extract_legacy_data(self, result: DataFetchResult) -> Optional[Dict[str, Any]]:
        """從新格式提取舊格式的數據"""
        if not result or not result.success or not result.data:
            return None

        # 如果是緩存數據或直接可用的數據，直接返回
        if result.cached or isinstance(result.data, dict):
            return result.data

        return None

    def get_stock_prices_dataframe(
        self, symbol: str, duration_days: int = 1095
    ) -> Optional[pd.DataFrame]:
        """
        將股票數據轉換為DataFrame - 向後兼容接口

        Args:
            symbol: 股票代碼
            duration_days: 數據天數

        Returns:
            股票價格DataFrame或None
        """
        data = self.get_stock_data(symbol, duration_days)
        if not data:
            return None

        try:
            # 嘗試不同的數據格式提取價格數據
            price_data = None

            # 格式1: 中央API格式
            if "data" in data and "close" in data["data"]:
                close_data = data["data"]["close"]
                if isinstance(close_data, dict):
                    df = pd.DataFrame.from_dict(close_data, orient="index", columns=["price"])
                    df.index = pd.to_datetime(df.index)
                    df.index.name = "date"
                    return df.sort_index()

            # 格式2: 時序數據格式
            elif "Time Series (Daily)" in data:
                time_series = data["Time Series (Daily)"]
                prices = []
                dates = []
                for date_str, values in time_series.items():
                    dates.append(date_str)
                    prices.append(float(values["4. close"]))

                df = pd.DataFrame({
                    "date": pd.to_datetime(dates),
                    "price": prices
                }).set_index("date")
                return df.sort_index()

            # 格式3: 簡單價格列表
            elif "prices" in data:
                prices = data["prices"]
                if "dates" in data:
                    df = pd.DataFrame({
                        "date": pd.to_datetime(data["dates"]),
                        "price": prices
                    }).set_index("date")
                else:
                    # 使用最新日期開始向後推
                    end_date = datetime.now()
                    dates = pd.date_range(
                        end=end_date,
                        periods=len(prices),
                        freq="D"
                    )
                    df = pd.DataFrame({
                        "date": dates,
                        "price": prices
                    }).set_index("date")
                return df.sort_index()

            else:
                logger.warning(f"Unknown data format for {symbol}")
                return None

        except Exception as e:
            logger.error(f"Error converting to DataFrame for {symbol}: {e}")
            return None

    def get_multiple_stocks(
        self, symbols: List[str], duration_days: int = 1095
    ) -> Dict[str, Optional[pd.DataFrame]]:
        """
        批量獲取多只股票數據 - 向後兼容接口

        Args:
            symbols: 股票代碼列表
            duration_days: 數據天數

        Returns:
            股票數據字典 {symbol: DataFrame}
        """
        results = {}

        for symbol in symbols:
            logger.info(f"Fetching data for {symbol}...")
            df = self.get_stock_prices_dataframe(symbol, duration_days)
            results[symbol] = df

            if df is None:
                logger.warning(f"Failed to fetch data for {symbol}")
            else:
                logger.info(f"Successfully fetched {len(df)} records for {symbol}")

        return results

    def get_real_time_price(self, symbol: str) -> Optional[float]:
        """
        獲取實時價格 - 向後兼容接口

        Args:
            symbol: 股票代碼

        Returns:
            最新價格或None
        """
        try:
            data = self.get_stock_data(symbol, 1)
            if not data:
                return None

            # 嘗試不同格式提取最新價格
            if "data" in data and "close" in data["data"]:
                close_data = data["data"]["close"]
                if close_data and isinstance(close_data, dict):
                    latest_date = sorted(close_data.keys())[-1]
                    return float(close_data[latest_date])

            elif "Time Series (Daily)" in data:
                time_series = data["Time Series (Daily)"]
                latest_date = sorted(time_series.keys())[-1]
                return float(time_series[latest_date]["4. close"])

            elif "prices" in data:
                prices = data["prices"]
                if prices:
                    return float(prices[-1])

            return None

        except Exception as e:
            logger.error(f"Error getting real-time price for {symbol}: {e}")
            return None

    def get_system_status(self) -> Dict[str, Any]:
        """
        獲取系統狀態

        Returns:
            系統狀態信息
        """
        try:
            if self._initialized and self._data_manager:
                status = self._data_manager.get_system_status()
            else:
                status = {
                    "status": "initializing",
                    "message": "Multi-source manager not yet initialized"
                }

            # 添加配置信息
            config = get_data_source_config()
            status["configuration"] = {
                "total_sources": len(config.data_sources),
                "enabled_sources": len(config.get_enabled_sources()),
                "cache_enabled": config.cache_config.memory_ttl > 0,
                "monitoring_enabled": config.monitoring_config.auto_failover
            }

            return status

        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def get_data_source_health(self) -> Dict[str, Any]:
        """
        獲取數據源健康狀態

        Returns:
            數據源健康信息
        """
        try:
            if self._initialized and self._data_manager:
                health_data = self._data_manager.get_data_source_health()
                return {
                    name: {
                        "status": health.status.value,
                        "response_time": health.response_time,
                        "success_rate": health.success_rate,
                        "last_check": health.last_check.isoformat(),
                        "data_quality_score": health.data_quality_score
                    }
                    for name, health in health_data.items()
                }
            else:
                return {
                    "status": "initializing",
                    "message": "Health monitoring not yet available"
                }

        except Exception as e:
            logger.error(f"Error getting health status: {e}")
            return {"error": str(e)}

    async def get_monitoring_dashboard(self) -> Dict[str, Any]:
        """
        獲取監控儀表板數據

        Returns:
            監控儀表板信息
        """
        try:
            monitor = await get_monitor()
            return monitor.get_monitoring_dashboard()

        except Exception as e:
            logger.error(f"Error getting monitoring dashboard: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def enable_data_source(self, source_name: str):
        """啟用指定的數據源"""
        try:
            config = get_data_source_config()
            config.enable_data_source(source_name)
            logger.info(f"Enabled data source: {source_name}")
            return True

        except Exception as e:
            logger.error(f"Error enabling data source {source_name}: {e}")
            return False

    def disable_data_source(self, source_name: str):
        """禁用指定的數據源"""
        try:
            config = get_data_source_config()
            config.disable_data_source(source_name)
            logger.info(f"Disabled data source: {source_name}")
            return True

        except Exception as e:
            logger.error(f"Error disabling data source {source_name}: {e}")
            return False

    def clear_cache(self):
        """清理緩存"""
        try:
            if self._initialized and self._data_manager:
                self._data_manager.cache_manager.clear_expired()
                logger.info("Cache cleared successfully")
                return True
            else:
                logger.warning("Cache manager not initialized")
                return False

        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False

    def force_health_check(self, source_name: str = None):
        """強制執行健康檢查"""
        try:
            if self._initialized and self._data_manager:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Schedule the health check
                    asyncio.create_task(self._data_manager.force_health_check(source_name))
                else:
                    # Run immediately
                    loop.run_until_complete(self._data_manager.force_health_check(source_name))
                logger.info(f"Health check forced for {source_name or 'all sources'}")
                return True
            else:
                logger.warning("Health monitoring not initialized")
                return False

        except Exception as e:
            logger.error(f"Error forcing health check: {e}")
            return False

# 向後兼容的全局實例
robust_stock_api = RobustStockAPI()

# 向後兼容的便捷函數
def get_stock_data(symbol: str, duration_days: int = 1095) -> Optional[Dict[str, Any]]:
    """獲取股票數據 - 向後兼容"""
    return robust_stock_api.get_stock_data(symbol, duration_days)

def get_hk_stock_data(symbol: str, duration_days: int = 1095) -> Optional[Dict[str, Any]]:
    """獲取港股數據 - 向後兼容"""
    return get_stock_data(symbol, duration_days)

def get_stock_prices_dataframe(symbol: str, duration_days: int = 1095) -> Optional[pd.DataFrame]:
    """獲取股票DataFrame - 向後兼容"""
    return robust_stock_api.get_stock_prices_dataframe(symbol, duration_days)

def get_real_time_price(symbol: str) -> Optional[float]:
    """獲取實時價格 - 向後兼容"""
    return robust_stock_api.get_real_time_price(symbol)

def get_multiple_stocks(symbols: List[str], duration_days: int = 1095) -> Dict[str, Optional[pd.DataFrame]]:
    """獲取多只股票數據 - 向後兼容"""
    return robust_stock_api.get_multiple_stocks(symbols, duration_days)

# 新增的高級功能函數
def get_system_status() -> Dict[str, Any]:
    """獲取系統狀態"""
    return robust_stock_api.get_system_status()

def get_data_source_health() -> Dict[str, Any]:
    """獲取數據源健康狀態"""
    return robust_stock_api.get_data_source_health()

async def get_monitoring_dashboard() -> Dict[str, Any]:
    """獲取監控儀表板"""
    return await robust_stock_api.get_monitoring_dashboard()

def enable_data_source(source_name: str) -> bool:
    """啟用數據源"""
    return robust_stock_api.enable_data_source(source_name)

def disable_data_source(source_name: str) -> bool:
    """禁用數據源"""
    return robust_stock_api.disable_data_source(source_name)

def clear_cache() -> bool:
    """清理緩存"""
    return robust_stock_api.clear_cache()

def force_health_check(source_name: str = None) -> bool:
    """強制健康檢查"""
    return robust_stock_api.force_health_check(source_name)

# 測試代碼
if __name__ == "__main__":
    import asyncio

    async def test_robust_api():
        """測試強化API"""
        print("=== 測試強化股票API ===")

        # 測試單個股票數據
        print("\n1. 測試單個股票數據...")
        data = get_stock_data("0700.hk", 30)
        if data:
            print("✅ 成功獲取股票數據")
            print(f"數據字段: {list(data.keys())}")
        else:
            print("❌ 獲取股票數據失敗")

        # 測試DataFrame
        print("\n2. 測試DataFrame轉換...")
        df = get_stock_prices_dataframe("0700.hk", 30)
        if df is not None:
            print(f"✅ 成功轉換為DataFrame，形狀: {df.shape}")
            print(f"日期範圍: {df.index[0]} 至 {df.index[-1]}")
        else:
            print("❌ DataFrame轉換失敗")

        # 測試系統狀態
        print("\n3. 測試系統狀態...")
        status = get_system_status()
        print(f"✅ 系統狀態: {status.get('status', 'unknown')}")

        # 測試數據源健康
        print("\n4. 測試數據源健康...")
        health = get_data_source_health()
        print(f"✅ 監控的數據源數量: {len(health)}")

        # 測試監控儀表板
        print("\n5. 測試監控儀表板...")
        dashboard = await get_monitoring_dashboard()
        if "summary" in dashboard:
            print(f"✅ 儀表板數據獲取成功")
            summary = dashboard["summary"]
            print(f"總數據源: {summary.get('total_sources', 0)}")
            print(f"健康數據源: {summary.get('healthy_sources', 0)}")

        print("\n=== 測試完成 ===")

    # 運行測試
    asyncio.run(test_robust_api())