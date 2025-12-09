#!/usr/bin/env python3
"""
簡化系統 - 股票數據API核心模塊
優化版本，支持緩存和性能提升
"""

import requests
import json
import time
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd

# Import simplified system configuration
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from config import get_data_source_config, get_performance_config

# Setup logging
logger = logging.getLogger(__name__)

class StockDataAPI:
    """優化的股票數據API接口"""

    def __init__(self):
        # 使用统一配置管理
        data_config = get_data_source_config()
        perf_config = get_performance_config()

        self.api_base_url = data_config.stock_api["base_url"]
        self.request_timeout = data_config.stock_api["timeout"]
        self.endpoint = data_config.stock_api["endpoint"]

        # 缓存配置
        self.cache = {}  # 簡單內存緩存
        self.cache_timeout = data_config.cache["timeout"]

        logger.info(f"Stock API initialized with base URL: {self.api_base_url}")

    def _get_cache_key(self, symbol: str, duration: int) -> str:
        """生成緩存鍵"""
        return f"{symbol}_{duration}"

    def _is_cache_valid(self, cache_key: str) -> bool:
        """檢查緩存是否有效"""
        if cache_key not in self.cache:
            return False

        cached_time = self.cache[cache_key].get('timestamp', 0)
        return (time.time() - cached_time) < self.cache_timeout

    def get_stock_data(self, symbol: str, duration_days: int = 1095) -> Optional[Dict[str, Any]]:
        """
        獲取股票數據 (優化版本，支持緩存)

        Args:
            symbol: 股票代碼 (e.g., "0700.hk")
            duration_days: 數據天數

        Returns:
            股票數據字典
        """
        cache_key = self._get_cache_key(symbol, duration_days)

        # 檢查緩存
        if self._is_cache_valid(cache_key):
            logger.info(f"Using cached data for {symbol}")
            return self.cache[cache_key]['data']

        try:
            url = f"{self.api_base_url}/inst/getInst"
            params = {
                "symbol": symbol.lower(),
                "duration": duration_days
            }

            start_time = time.time()
            response = requests.get(url, params=params, timeout=self.request_timeout)
            response_time = (time.time() - start_time) * 1000

            if response.status_code == 200:
                data = response.json()

                # 驗證數據格式
                if 'data' in data and 'close' in data['data']:
                    close_data = data['data']['close']

                    # 提取關鍵信息
                    dates = list(close_data.keys())
                    prices = list(close_data.values())

                    logger.info(f"Successfully fetched {len(close_data)} records for {symbol}")
                    logger.info(f"Response time: {response_time:.2f}ms")
                    logger.info(f"Date range: {dates[0]} to {dates[-1]}")
                    logger.info(f"Price range: {min(prices):.2f} - {max(prices):.2f}")

                    # 更新緩存
                    self.cache[cache_key] = {
                        'data': data,
                        'timestamp': time.time()
                    }

                    return data
                else:
                    logger.error(f"Invalid data format for {symbol}")
                    return None
            else:
                logger.error(f"HTTP {response.status_code} for {symbol}")
                return None

        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return None

    def get_stock_prices_dataframe(self, symbol: str, duration_days: int = 1095) -> Optional[pd.DataFrame]:
        """
        將股票數據轉換為DataFrame

        Args:
            symbol: 股票代碼
            duration_days: 數據天數

        Returns:
            股票價格DataFrame
        """
        data = self.get_stock_data(symbol, duration_days)
        if not data or 'data' not in data or 'close' not in data['data']:
            return None

        close_data = data['data']['close']

        # 轉換為DataFrame
        df = pd.DataFrame.from_dict(close_data, orient='index', columns=['price'])
        df.index = pd.to_datetime(df.index)
        df.index.name = 'date'
        df = df.sort_index()

        return df

    def get_multiple_stocks(self, symbols: List[str], duration_days: int = 1095) -> Dict[str, Optional[pd.DataFrame]]:
        """
        批量獲取多只股票數據

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
            if df is not None:
                results[symbol] = df
            else:
                logger.warning(f"Failed to fetch data for {symbol}")

        return results

    def get_real_time_price(self, symbol: str) -> Optional[float]:
        """
        獲取實時價格 (短時期數據)

        Args:
            symbol: 股票代碼

        Returns:
            最新價格
        """
        data = self.get_stock_data(symbol, 1)
        if not data or 'data' not in data or 'close' not in data['data']:
            return None

        close_data = data['data']['close']
        if not close_data:
            return None

        # 獲取最新日期的價格
        dates = sorted(close_data.keys())
        latest_date = dates[-1]

        return float(close_data[latest_date])

# Alias for backward compatibility
StockAPI = StockDataAPI

# Factory function
def create_stock_api() -> StockDataAPI:
    """Create a new StockDataAPI instance"""
    return StockDataAPI()

# Global instance
stock_api = StockDataAPI()

# Convenience functions
def get_stock_data(symbol: str, duration_days: int = 1095) -> Optional[Dict[str, Any]]:
    """便捷函數：獲取股票數據"""
    return stock_api.get_stock_data(symbol, duration_days)

def get_hk_stock_data(symbol: str, duration_days: int = 1095) -> Optional[Dict[str, Any]]:
    """便捷函數：獲取港股數據"""
    return stock_api.get_stock_data(symbol, duration_days)

def get_stock_prices_dataframe(symbol: str, duration_days: int = 1095) -> Optional[pd.DataFrame]:
    """便捷函數：獲取股票DataFrame"""
    return stock_api.get_stock_prices_dataframe(symbol, duration_days)

def get_real_time_price(symbol: str) -> Optional[float]:
    """便捷函數：獲取實時價格"""
    return stock_api.get_real_time_price(symbol)

def get_multiple_stocks(symbols: List[str], duration_days: int = 1095) -> Dict[str, Optional[pd.DataFrame]]:
    """便捷函數：獲取多只股票數據"""
    return stock_api.get_multiple_stocks(symbols, duration_days)

if __name__ == "__main__":
    # 測試代碼
    print("Testing Stock API...")

    # 測試單個股票
    data = get_stock_data("0700.hk", 30)
    if data:
        print("Stock data retrieved successfully!")

    # 測試實時價格
    price = get_real_time_price("0700.hk")
    if price:
        print(f"Current price: {price}")

    # 測試DataFrame
    df = get_stock_prices_dataframe("0700.hk", 30)
    if df is not None:
        print(f"DataFrame shape: {df.shape}")
        print(f"Date range: {df.index[0]} to {df.index[-1]}")
        print(f"Price summary: min={df['price'].min():.2f}, max={df['price'].max():.2f}")