#!/usr / bin / env python3
"""
後端數據服務單元測試
Unit tests for Backend Data Service
"""

import sqlite3
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd
import pytest

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

from services.data_service import DataService


class TestDataService:
    """數據服務測試類"""

    @pytest.fixture
    def data_service(self, temp_dir):
        """創建數據服務fixture"""
        db_path = temp_dir / "test.db"
        return DataService(str(db_path))

    @pytest.fixture
    def mock_ticker(self):
        """模擬yfinance Ticker對象"""
        mock_ticker = Mock()

        # 模擬歷史數據
        mock_history_data = pd.DataFrame(
            {
                "Open": [100.0, 101.5, 99.8, 102.3, 103.1],
                "High": [101.8, 102.0, 100.5, 103.0, 104.2],
                "Low": [99.5, 100.8, 99.0, 101.9, 102.8],
                "Close": [101.5, 99.8, 102.3, 103.1, 104.0],
                "Volume": [1000000, 1200000, 800000, 1500000, 900000],
            },
            index = pd.date_range("2024 - 01 - 01", periods = 5, freq="D"),
        )

        # 模擬股票信息
        mock_info = {
            "longName": "Test Company Limited",
            "sector": "Technology",
            "industry": "Software",
            "marketCap": 1000000000000,
            "trailingPE": 25.5,
            "dividendYield": 0.02,
            "currency": "HKD",
            "exchange": "HKEX",
        }

        mock_ticker.history.return_value = mock_history_data
        mock_ticker.info = mock_info

        return mock_ticker

    def test_init(self, data_service):
        """測試數據服務初始化"""
        assert data_service.db_path is not None
        assert Path(data_service.db_path).exists()

    def test_get_db_connection(self, data_service):
        """測試數據庫連接獲取"""
        conn = data_service.get_db_connection()
        assert conn is not None

        # 檢查連接屬性
        assert hasattr(conn, "cursor")
        assert conn.row_factory == sqlite3.Row

        conn.close()

    @patch("yfinance.Ticker")
    def test_fetch_stock_data_success(
        self, mock_ticker_class, data_service, mock_ticker
    ):
        """測試成功獲取股票數據"""
        mock_ticker_class.return_value = mock_ticker

        result = data_service.fetch_stock_data("0700.HK", "1mo", "1d")

        assert isinstance(result, list)
        assert len(result) == 5  # 5天的數據

        # 檢查數據格式
        first_item = result[0]
        assert "timestamp" in first_item
        assert "open" in first_item
        assert "high" in first_item
        assert "low" in first_item
        assert "close" in first_item
        assert "volume" in first_item

        # 檢查數據類型
        assert isinstance(first_item["open"], (int, float))
        assert isinstance(first_item["volume"], int)

    @patch("yfinance.Ticker")
    def test_fetch_stock_data_empty_response(self, mock_ticker_class, data_service):
        """測試空響應處理"""
        mock_ticker = Mock()
        mock_ticker.history.return_value = pd.DataFrame()  # 空DataFrame
        mock_ticker_class.return_value = mock_ticker

        result = data_service.fetch_stock_data("INVALID.HK", "1mo", "1d")

        assert result == []

    @patch("yfinance.Ticker")
    def test_fetch_stock_data_exception(self, mock_ticker_class, data_service):
        """測試異常處理"""
        mock_ticker_class.side_effect = Exception("Network error")

        result = data_service.fetch_stock_data("0700.HK", "1mo", "1d")

        assert result == []

    @patch("yfinance.Ticker")
    def test_save_market_data(self, mock_ticker_class, data_service, mock_ticker):
        """測試市場數據保存"""
        mock_ticker_class.return_value = mock_ticker

        # 先獲取數據
        data = data_service.fetch_stock_data("0700.HK", "1mo", "1d")

        # 保存數據
        result = data_service.save_market_data("0700.HK", data)
        assert result is True

        # 驗證數據已保存
        saved_data = data_service.get_market_data("0700.HK")
        assert len(saved_data) == len(data)

    def test_save_market_data_empty(self, data_service):
        """測試保存空數據"""
        result = data_service.save_market_data("0700.HK", [])
        assert result is True  # 空數據應該成功保存

    def test_get_market_data_no_filter(self, data_service):
        """測試獲取市場數據（無過濾）"""
        # 先插入測試數據
        test_data = [
            {
                "timestamp": "2024 - 01 - 01T00:00:00Z",
                "open": 100.0,
                "high": 105.0,
                "low": 95.0,
                "close": 102.0,
                "volume": 1000000,
            }
        ]

        data_service.save_market_data("TEST.HK", test_data)

        result = data_service.get_market_data("TEST.HK")

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["symbol"] == "TEST.HK"

    def test_get_market_data_with_date_filter(self, data_service):
        """測試獲取市場數據（日期過濾）"""
        # 插入多天數據
        test_data = [
            {
                "timestamp": "2024 - 01 - 01T00:00:00Z",
                "open": 100.0,
                "high": 105.0,
                "low": 95.0,
                "close": 102.0,
                "volume": 1000000,
            },
            {
                "timestamp": "2024 - 01 - 02T00:00:00Z",
                "open": 102.0,
                "high": 107.0,
                "low": 97.0,
                "close": 104.0,
                "volume": 1200000,
            },
            {
                "timestamp": "2024 - 01 - 03T00:00:00Z",
                "open": 104.0,
                "high": 109.0,
                "low": 99.0,
                "close": 106.0,
                "volume": 800000,
            },
        ]

        data_service.save_market_data("TEST.HK", test_data)

        # 測試開始日期過濾
        result = data_service.get_market_data("TEST.HK", start_date="2024 - 01 - 02")
        assert len(result) == 2  # 1月2日和1月3日的數據

        # 測試結束日期過濾
        result = data_service.get_market_data("TEST.HK", end_date="2024 - 01 - 02")
        assert len(result) == 2  # 1月1日和1月2日的數據

        # 測試日期範圍過濾
        result = data_service.get_market_data(
            "TEST.HK", start_date="2024 - 01 - 02", end_date="2024 - 01 - 02"
        )
        assert len(result) == 1  # 只有1月2日的數據

    @patch("yfinance.Ticker")
    def test_fetch_stock_info_success(
        self, mock_ticker_class, data_service, mock_ticker
    ):
        """測試成功獲取股票信息"""
        mock_ticker_class.return_value = mock_ticker

        result = data_service.fetch_stock_info("0700.HK")

        assert result is not None
        assert result["symbol"] == "0700.HK"
        assert result["name"] == "Test Company Limited"
        assert result["sector"] == "Technology"
        assert result["industry"] == "Software"
        assert result["market_cap"] == 1000000000000
        assert result["pe_ratio"] == 25.5
        assert result["dividend_yield"] == 0.02
        assert result["currency"] == "HKD"
        assert result["exchange"] == "HKEX"

    @patch("yfinance.Ticker")
    def test_fetch_stock_info_exception(self, mock_ticker_class, data_service):
        """測試股票信息獲取異常處理"""
        mock_ticker_class.side_effect = Exception("Network error")

        result = data_service.fetch_stock_info("0700.HK")

        assert result is None

    def test_save_and_get_stock_info(self, data_service):
        """測試股票信息保存和獲取"""
        stock_info = {
            "symbol": "TEST.HK",
            "name": "Test Company",
            "sector": "Finance",
            "industry": "Banking",
            "market_cap": 500000000000,
            "pe_ratio": 15.2,
            "dividend_yield": 0.03,
            "currency": "HKD",
            "exchange": "HKEX",
        }

        # 保存股票信息
        save_result = data_service.save_stock_info(stock_info)
        assert save_result is True

        # 獲取股票信息
        retrieved_info = data_service.get_stock_info("TEST.HK")

        assert retrieved_info is not None
        assert retrieved_info["symbol"] == "TEST.HK"
        assert retrieved_info["name"] == "Test Company"
        assert retrieved_info["sector"] == "Finance"

    def test_get_nonexistent_stock_info(self, data_service):
        """測試獲取不存在的股票信息"""
        result = data_service.get_stock_info("NONEXISTENT.HK")
        assert result is None

    def test_search_stocks_empty_query(self, data_service):
        """測試空查詢股票搜索"""
        # 先插入一些測試數據
        stock_info = {
            "symbol": "TEST.HK",
            "name": "Test Company",
            "sector": "Finance",
            "industry": "Banking",
            "market_cap": 500000000000,
            "pe_ratio": 15.2,
            "dividend_yield": 0.03,
            "currency": "HKD",
            "exchange": "HKEX",
        }
        data_service.save_stock_info(stock_info)

        result = data_service.search_stocks("")
        assert isinstance(result, list)
        # 應該返回所有股票
        assert len(result) >= 1

    def test_search_stocks_by_symbol(self, data_service):
        """測試按股票代碼搜索"""
        # 插入測試數據
        stock_info = {
            "symbol": "TENCENT.HK",
            "name": "Tencent Holdings",
            "sector": "Technology",
            "industry": "Software",
            "market_cap": 3000000000000,
            "pe_ratio": 30.5,
            "dividend_yield": 0.01,
            "currency": "HKD",
            "exchange": "HKEX",
        }
        data_service.save_stock_info(stock_info)

        result = data_service.search_stocks("TENCENT")
        assert isinstance(result, list)
        if len(result) > 0:
            assert "TENCENT" in result[0]["symbol"]

    def test_search_stocks_by_name(self, data_service):
        """測試按股票名稱搜索"""
        # 插入測試數據
        stock_info = {
            "symbol": "TECH.HK",
            "name": "Technology Company",
            "sector": "Technology",
            "industry": "Software",
            "market_cap": 1000000000000,
            "pe_ratio": 25.0,
            "dividend_yield": 0.015,
            "currency": "HKD",
            "exchange": "HKEX",
        }
        data_service.save_stock_info(stock_info)

        result = data_service.search_stocks("Technology")
        assert isinstance(result, list)
        if len(result) > 0:
            assert "Technology" in result[0]["name"]

    @patch("yfinance.Ticker")
    def test_get_popular_stocks(self, mock_ticker_class, data_service, mock_ticker):
        """測試獲取熱門股票"""
        mock_ticker_class.return_value = mock_ticker

        result = data_service.get_popular_stocks()

        assert isinstance(result, list)
        # 應該返回一些熱門股票
        assert len(result) > 0

        # 檢查返回的股票信息格式
        if len(result) > 0:
            stock = result[0]
            assert "symbol" in stock
            assert "name" in stock

    def test_get_data_summary(self, data_service):
        """測試獲取數據摘要"""
        # 插入一些測試數據
        stock_info = {
            "symbol": "TEST.HK",
            "name": "Test Company",
            "sector": "Finance",
            "industry": "Banking",
            "market_cap": 500000000000,
            "pe_ratio": 15.2,
            "dividend_yield": 0.03,
            "currency": "HKD",
            "exchange": "HKEX",
        }
        data_service.save_stock_info(stock_info)

        test_data = [
            {
                "timestamp": "2024 - 01 - 01T00:00:00Z",
                "open": 100.0,
                "high": 105.0,
                "low": 95.0,
                "close": 102.0,
                "volume": 1000000,
            }
        ]
        data_service.save_market_data("TEST.HK", test_data)

        summary = data_service.get_data_summary()

        assert isinstance(summary, dict)
        assert "stock_count" in summary
        assert "data_count" in summary
        assert "last_update" in summary

        assert summary["stock_count"] >= 1
        assert summary["data_count"] >= 1


@pytest.mark.database
class TestDataServiceDatabaseOperations:
    """數據庫操作專用測試"""

    @pytest.fixture
    def data_service(self, temp_dir):
        return DataService(str(temp_dir / "test.db"))

    def test_database_initialization(self, data_service):
        """測試數據庫初始化"""
        conn = data_service.get_db_connection()

        # 檢查表是否存在
        cursor = conn.cursor()

        # 檢查market_data表
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='market_data'"
        )
        assert cursor.fetchone() is not None

        # 檢查stocks表
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='stocks'"
        )
        assert cursor.fetchone() is not None

        conn.close()

    def test_database_connection_closing(self, data_service):
        """測試數據庫連接關閉"""
        conn = data_service.get_db_connection()

        # 連接應該是活的
        assert conn is not None

        # 關閉連接後不應該能執行查詢
        conn.close()

        with pytest.raises(sqlite3.ProgrammingError):
            conn.execute("SELECT 1")

    def test_concurrent_access(self, data_service):
        """測試並發數據庫訪問"""
        import threading

        results = []

        def insert_data(thread_id):
            stock_info = {
                "symbol": f"THREAD_{thread_id}.HK",
                "name": f"Thread {thread_id} Company",
                "sector": "Technology",
                "industry": "Software",
                "market_cap": 1000000000,
                "pe_ratio": 20.0,
                "dividend_yield": 0.02,
                "currency": "HKD",
                "exchange": "HKEX",
            }

            try:
                result = data_service.save_stock_info(stock_info)
                results.append(result)
            except Exception as e:
                results.append(False)

        # 創建多個線程
        threads = []
        for i in range(5):
            thread = threading.Thread(target = insert_data, args=(i,))
            threads.append(thread)
            thread.start()

        # 等待所有線程完成
        for thread in threads:
            thread.join()

        # 檢查結果
        assert len(results) == 5
        assert all(results)  # 所有操作都應該成功


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
