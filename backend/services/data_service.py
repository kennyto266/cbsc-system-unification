"""
数据服务模块 - 处理股票数据获取和存储
"""

import yfinance as yf
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class DataService:
    """数据服务类"""
    
    def __init__(self, db_path: str = "data/quant_system.db"):
        self.db_path = db_path
    
    def get_db_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def fetch_stock_data(self, symbol: str, period: str = "1mo", interval: str = "1d") -> List[Dict[str, Any]]:
        """获取股票数据"""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period, interval=interval)
            
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
            logger.error(f"获取股票数据失败 {symbol}: {e}")
            return []
    
    def save_market_data(self, symbol: str, data: List[Dict[str, Any]]) -> bool:
        """保存市场数据到数据库"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
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
            logger.info(f"成功保存 {symbol} 的市场数据")
            return True
            
        except Exception as e:
            logger.error(f"保存市场数据失败 {symbol}: {e}")
            return False
    
    def get_market_data(self, symbol: str, start_date: Optional[str] = None, 
                       end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """从数据库获取市场数据"""
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
            logger.error(f"获取市场数据失败 {symbol}: {e}")
            return []
    
    def fetch_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """获取股票基本信息"""
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
            logger.error(f"获取股票信息失败 {symbol}: {e}")
            return None
    
    def save_stock_info(self, stock_info: Dict[str, Any]) -> bool:
        """保存股票信息到数据库"""
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
            logger.error(f"保存股票信息失败 {stock_info['symbol']}: {e}")
            return False
    
    def get_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """从数据库获取股票信息"""
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
            logger.error(f"获取股票信息失败 {symbol}: {e}")
            return None
    
    def search_stocks(self, query: str) -> List[Dict[str, Any]]:
        """搜索股票"""
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
            logger.error(f"搜索股票失败: {e}")
            return []
    
    def get_popular_stocks(self) -> List[Dict[str, Any]]:
        """获取热门股票列表"""
        popular_symbols = ["0700.HK", "2800.HK", "1299.HK", "0941.HK", "0388.HK"]
        stocks = []
        
        for symbol in popular_symbols:
            stock_info = self.get_stock_info(symbol)
            if stock_info:
                stocks.append(stock_info)
            else:
                # 如果数据库中没有，则从API获取
                stock_info = self.fetch_stock_info(symbol)
                if stock_info:
                    stocks.append(stock_info)
        
        return stocks
    
    def update_stock_data(self, symbol: str) -> bool:
        """更新股票数据"""
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
            logger.error(f"更新股票数据失败 {symbol}: {e}")
            return False
    
    def get_data_summary(self) -> Dict[str, Any]:
        """获取数据摘要"""
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
            logger.error(f"获取数据摘要失败: {e}")
            return {
                "stock_count": 0,
                "data_count": 0,
                "last_update": None
            }
