"""
数据服务模块 - 处理股票数据获取和存储
集成重试逻辑、断路器模式和错误处理
"""

import yfinance as yf
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging

# Import error handling utilities
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.retry_manager import RetryManager, RetryConfig, retry_sync
from utils.circuit_breaker import CircuitBreaker, CircuitBreakerConfig, get_circuit_breaker, CircuitBreakerOpenError
from utils.error_handler import CBAError, ErrorCategory, handle_exception, ExternalServiceError, DatabaseError
from config.error_config import get_service_config

logger = logging.getLogger(__name__)


class DataService:
    """数据服务类 - 增强版，带有重试、断路器和错误处理"""

    def __init__(self, db_path: str = "data/quant_system.db"):
        self.db_path = db_path

        # Initialize retry manager for yfinance API
        yf_config = get_service_config("yfinance")
        self.yfinance_retry_config = RetryConfig(
            max_attempts=yf_config.get("max_attempts", 3),
            base_delay=yf_config.get("base_delay", 2.0),
            retryable_exceptions=(
                ConnectionError,
                TimeoutError,
                OSError,
            )
        )
        self.yfinance_retry_manager = RetryManager(self.yfinance_retry_config)

        # Initialize circuit breaker for yfinance
        self.yfinance_breaker = get_circuit_breaker(
            "yfinance-api",
            CircuitBreakerConfig(
                failure_threshold=yf_config.get("circuit_breaker_threshold", 5),
                timeout=60.0
            )
        )

        # Initialize circuit breaker for database
        self.database_breaker = get_circuit_breaker(
            "database",
            CircuitBreakerConfig(
                failure_threshold=3,
                timeout=30.0
            )
        )

    def get_db_connection(self):
        """获取数据库连接 - 带重试和断路器保护"""
        def _connect():
            conn = sqlite3.connect(self.db_path, timeout=10.0)
            conn.row_factory = sqlite3.Row
            return conn

        try:
            return self.database_breaker.call_sync(_connect)
        except CircuitBreakerOpenError as e:
            logger.error(f"数据库断路器已打开: {e}")
            raise DatabaseError(
                message="数据库服务暫時不可用，請稍後重試",
                context={"service": "sqlite", "circuit_breaker": "open"}
            )

    def fetch_stock_data(self, symbol: str, period: str = "1mo", interval: str = "1d") -> List[Dict[str, Any]]:
        """
        获取股票数据 - 带重试和断路器保护

        Args:
            symbol: 股票代码
            period: 时间周期 (1d, 5d, 1mo, 3mo, 6mo, 1y, etc.)
            interval: 数据间隔 (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)

        Returns:
            股票数据列表
        """
        @retry_sync(max_attempts=3, base_delay=2.0)
        def _fetch_from_yfinance():
            try:
                ticker = yf.Ticker(symbol)
                data = ticker.history(period=period, interval=interval, timeout=30)

                if data.empty:
                    logger.warning(f"未找到股票 {symbol} 的数据")
                    return []

                # 转换为字典格式
                data_list = []
                for index, row in data.iterrows():
                    data_list.append({
                        "timestamp": index.isoformat(),
                        "open": float(row["Open"]),
                        "high": float(row["High"]),
                        "low": float(row["Low"]),
                        "close": float(row["Close"]),
                        "volume": int(row["Volume"])
                    })

                # 保存到数据库
                self.save_market_data(symbol, data_list)

                return data_list

            except Exception as e:
                # Handle with error classification
                cba_error = handle_exception(
                    e,
                    extra_context={"symbol": symbol, "period": period, "interval": interval}
                )
                raise cba_error

        try:
            # Use circuit breaker to call the function
            return self.yfinance_breaker.call_sync(_fetch_from_yfinance)

        except CircuitBreakerOpenError as e:
            # Circuit breaker is open - return empty list with warning
            logger.warning(f"yfinance API 断路器已打开，无法获取 {symbol} 数据")
            return []

        except CBAError as e:
            # Known error - handle gracefully
            logger.error(f"获取股票数据失败 {symbol}: {e.user_message}")
            return []

        except Exception as e:
            # Unexpected error
            logger.error(f"获取股票数据时发生未预期错误 {symbol}: {e}")
            return []

    def save_market_data(self, symbol: str, data: List[Dict[str, Any]]) -> bool:
        """
        保存市场数据到数据库 - 带重试保护

        Args:
            symbol: 股票代码
            data: 市场数据列表

        Returns:
            是否成功保存
        """
        if not data:
            return True

        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            # Batch insert for better performance
            for item in data:
                cursor.execute("""
                    INSERT OR REPLACE INTO market_data
                    (symbol, timestamp, open_price, high_price, low_price, close_price, volume)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    symbol,
                    item["timestamp"],
                    item["open"],
                    item["high"],
                    item["low"],
                    item["close"],
                    item["volume"]
                ))

            conn.commit()
            conn.close()
            logger.info(f"成功保存 {symbol} 的市场数据 ({len(data)} 条记录)")
            return True

        except Exception as e:
            cba_error = handle_exception(
                e,
                extra_context={"symbol": symbol, "data_count": len(data)}
            )
            logger.error(f"保存市场数据失败 {symbol}: {cba_error.user_message}")
            return False

    def get_market_data(self, symbol: str, start_date: Optional[str] = None,
                       end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        从数据库获取市场数据 - 带重试保护

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            市场数据列表
        """
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            query = "SELECT * FROM market_data WHERE symbol = ?"
            params = [symbol]

            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date)

            if end_date:
                query += " AND timestamp <= ?"
                params.append(end_date)

            query += " ORDER BY timestamp"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            data = []
            for row in rows:
                data.append({
                    "timestamp": row["timestamp"],
                    "open": row["open_price"],
                    "high": row["high_price"],
                    "low": row["low_price"],
                    "close": row["close_price"],
                    "volume": row["volume"]
                })

            conn.close()
            return data

        except Exception as e:
            cba_error = handle_exception(e, extra_context={"symbol": symbol})
            logger.error(f"获取市场数据失败 {symbol}: {cba_error.user_message}")
            return []

    @retry_sync(max_attempts=3, base_delay=2.0)
    def fetch_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取股票基本信息 - 带重试和断路器保护

        Args:
            symbol: 股票代码

        Returns:
            股票信息字典或None
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            stock_info = {
                "symbol": symbol,
                "name": info.get("longName", ""),
                "sector": info.get("sector", ""),
                "industry": info.get("industry", ""),
                "market_cap": info.get("marketCap", 0),
                "pe_ratio": info.get("trailingPE", 0),
                "dividend_yield": info.get("dividendYield", 0),
                "currency": info.get("currency", "HKD"),
                "exchange": info.get("exchange", "HKEX")
            }

            # 保存到数据库
            self.save_stock_info(stock_info)

            return stock_info

        except Exception as e:
            cba_error = handle_exception(e, extra_context={"symbol": symbol})
            logger.error(f"获取股票信息失败 {symbol}: {cba_error.user_message}")
            return None

    def save_stock_info(self, stock_info: Dict[str, Any]) -> bool:
        """保存股票信息到数据库 - 带重试保护"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO stocks
                (symbol, name, sector, industry, market_cap, pe_ratio, dividend_yield, currency, exchange)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                stock_info["symbol"],
                stock_info["name"],
                stock_info["sector"],
                stock_info["industry"],
                stock_info["market_cap"],
                stock_info["pe_ratio"],
                stock_info["dividend_yield"],
                stock_info["currency"],
                stock_info["exchange"]
            ))

            conn.commit()
            conn.close()
            logger.info(f"成功保存股票信息 {stock_info['symbol']}")
            return True

        except Exception as e:
            cba_error = handle_exception(e, extra_context={"symbol": stock_info.get("symbol")})
            logger.error(f"保存股票信息失败 {stock_info.get('symbol')}: {cba_error.user_message}")
            return False

    def get_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """从数据库获取股票信息 - 带重试保护"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM stocks WHERE symbol = ?", (symbol,))
            row = cursor.fetchone()

            if row:
                stock_info = {
                    "symbol": row["symbol"],
                    "name": row["name"],
                    "sector": row["sector"],
                    "industry": row["industry"],
                    "market_cap": row["market_cap"],
                    "pe_ratio": row["pe_ratio"],
                    "dividend_yield": row["dividend_yield"],
                    "currency": row["currency"],
                    "exchange": row["exchange"]
                }
                conn.close()
                return stock_info

            conn.close()
            return None

        except Exception as e:
            cba_error = handle_exception(e, extra_context={"symbol": symbol})
            logger.error(f"获取股票信息失败 {symbol}: {cba_error.user_message}")
            return None

    def search_stocks(self, query: str) -> List[Dict[str, Any]]:
        """搜索股票 - 带重试保护"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            if not query:
                cursor.execute("SELECT * FROM stocks ORDER BY name")
            else:
                cursor.execute("""
                    SELECT * FROM stocks
                    WHERE symbol LIKE ? OR name LIKE ?
                    ORDER BY name
                """, (f"%{query}%", f"%{query}%"))

            rows = cursor.fetchall()

            stocks = []
            for row in rows:
                stocks.append({
                    "symbol": row["symbol"],
                    "name": row["name"],
                    "sector": row["sector"],
                    "industry": row["industry"],
                    "market_cap": row["market_cap"],
                    "pe_ratio": row["pe_ratio"],
                    "dividend_yield": row["dividend_yield"]
                })

            conn.close()
            return stocks

        except Exception as e:
            cba_error = handle_exception(e, extra_context={"query": query})
            logger.error(f"搜索股票失败: {cba_error.user_message}")
            return []

    def get_popular_stocks(self) -> List[Dict[str, Any]]:
        """获取热门股票列表 - 带错误处理"""
        popular_symbols = ["0700.HK", "2800.HK", "1299.HK", "0941.HK", "0388.HK"]
        stocks = []

        for symbol in popular_symbols:
            try:
                stock_info = self.get_stock_info(symbol)
                if stock_info:
                    stocks.append(stock_info)
                else:
                    # 如果数据库中没有，则从API获取
                    stock_info = self.fetch_stock_info(symbol)
                    if stock_info:
                        stocks.append(stock_info)
            except Exception as e:
                # Continue with other stocks even if one fails
                logger.warning(f"获取股票 {symbol} 信息失败，跳过")
                continue

        return stocks

    def update_stock_data(self, symbol: str) -> bool:
        """更新股票数据 - 带错误处理和重试"""
        try:
            # 获取最新数据
            data = self.fetch_stock_data(symbol, period="1mo")
            if not data:
                return False

            # 获取股票信息
            info = self.fetch_stock_info(symbol)
            if not info:
                return False

            logger.info(f"成功更新股票数据 {symbol}")
            return True

        except Exception as e:
            cba_error = handle_exception(e, extra_context={"symbol": symbol})
            logger.error(f"更新股票数据失败 {symbol}: {cba_error.user_message}")
            return False

    def get_data_summary(self) -> Dict[str, Any]:
        """获取数据摘要 - 带错误处理"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            # 统计股票数量
            cursor.execute("SELECT COUNT(*) as count FROM stocks")
            stock_count = cursor.fetchone()["count"]

            # 统计市场数据记录数
            cursor.execute("SELECT COUNT(*) as count FROM market_data")
            data_count = cursor.fetchone()["count"]

            # 获取最新更新时间
            cursor.execute("SELECT MAX(created_at) as last_update FROM market_data")
            last_update = cursor.fetchone()["last_update"]

            conn.close()

            return {
                "stock_count": stock_count,
                "data_count": data_count,
                "last_update": last_update
            }

        except Exception as e:
            cba_error = handle_exception(e)
            logger.error(f"获取数据摘要失败: {cba_error.user_message}")
            return {
                "stock_count": 0,
                "data_count": 0,
                "last_update": None
            }

    def get_circuit_breaker_stats(self) -> dict:
        """获取断路器统计信息 - 用于监控"""
        return {
            "yfinance": self.yfinance_breaker.get_stats(),
            "database": self.database_breaker.get_stats()
        }

    def get_retry_stats(self) -> dict:
        """获取重试统计信息 - 用于监控"""
        return {
            "yfinance": self.yfinance_retry_manager.get_stats()
        }


# Maintain backward compatibility - create default instance
_default_service = None


def get_data_service() -> DataService:
    """获取默认数据服务实例"""
    global _default_service
    if _default_service is None:
        _default_service = DataService()
    return _default_service
