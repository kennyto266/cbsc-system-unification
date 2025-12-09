import logging
import os
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

import requests

logger = logging.getLogger("quant_system")


class DataProvider(ABC):
    """抽象数据提供者"""

    @abstractmethod
    def get_stock_data(self, symbol: str) -> Optional[Dict]:
        pass


class PrimaryDataProvider(DataProvider):
    """主要数据提供者"""

    def __init__(self):
        self.base_url = os.getenv("STOCK_API_BASE_URL", "http://18.180.162.113:9191")
        self.timeout = int(os.getenv("STOCK_API_TIMEOUT", "10"))

    def get_stock_data(self, symbol: str) -> Optional[Dict]:
        try:
            url = f"{self.base_url}/inst / getInst"
            params = {"symbol": symbol}
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Primary API error for {symbol}: {e}")
            return None


class AlphaVantageProvider(DataProvider):
    """Alpha Vantage备用数据提供者"""

    def __init__(self):
        self.api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        self.base_url = "https://www.alphavantage.co / query"

    def get_stock_data(self, symbol: str) -> Optional[Dict]:
        if not self.api_key:
            return None

        try:
            params = {
                "function": "TIME_SERIES_DAILY",
                "symbol": symbol,
                "apikey": self.api_key,
                "outputsize": "compact",
            }
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            # 转换格式以匹配主要API
            if "Time Series (Daily)" in data:
                time_series = data["Time Series (Daily)"]
                latest_date = max(time_series.keys())
                latest_data = time_series[latest_date]

                return {
                    "symbol": symbol,
                    "price": float(latest_data["4. close"]),
                    "volume": int(latest_data["5. volume"]),
                    "change": float(latest_data["4. close"])
                    - float(latest_data["1. open"]),
                    "change_percent": (
                        (float(latest_data["4. close"]) - float(latest_data["1. open"]))
                        / float(latest_data["1. open"])
                    )
                    * 100,
                    "date": latest_date,
                }
            return None
        except Exception as e:
            logger.error(f"Alpha Vantage API error for {symbol}: {e}")
            return None


class DataProviderManager:
    """数据提供者管理器"""

    def __init__(self):
        self.providers = [PrimaryDataProvider(), AlphaVantageProvider()]

    def get_stock_data(self, symbol: str) -> Optional[Dict]:
        """尝试多个数据源获取数据"""
        for provider in self.providers:
            data = provider.get_stock_data(symbol)
            if data:
                logger.info(
                    f"Data retrieved from {provider.__class__.__name__} for {symbol}"
                )
                return data

        logger.warning(f"No data available for {symbol} from any provider")
        return None


# 全局实例
data_manager = DataProviderManager()
