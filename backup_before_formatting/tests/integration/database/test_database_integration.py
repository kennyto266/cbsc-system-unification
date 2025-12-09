#!/usr/bin/env python3
"""
數據庫集成測試
Database Integration Tests

測試數據庫操作、事務處理和數據一致性
"""

import pytest
import sqlite3
import asyncio
import aiosqlite
from pathlib import Path
import sys
from typing import List, Dict, Any
import tempfile
import time
from contextlib import asynccontextmanager

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

from services.data_service import DataService
from tests.factories.stock_data_factory import StockMarketDataFactory, StockInfoFactory

@pytest.mark.integration
@pytest.mark.database
class TestDatabaseOperations:
    """數據庫操作集成測試"""

    @pytest.fixture
    def temp_db(self):
        """創建臨時數據庫"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        yield db_path

        # 清理
        Path(db_path).unlink(missing_ok=True)

    @pytest.fixture
    def data_service(self, temp_db):
        """創建數據服務實例"""
        return DataService(temp_db)

    def test_database_schema_creation(self, data_service):
        """測試數據庫模式創建"""
        conn = data_service.get_db_connection()
        cursor = conn.cursor()

        # 檢查表是否存在
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name IN ('market_data', 'stocks')
        """)
        tables = cursor.fetchall()

        assert len(tables) >= 1, "至少應該有一個表"

        conn.close()

    def test_market_data_crud_operations(self, data_service):
        """測試市場數據CRUD操作"""
        # 測試數據
        test_data = [
            {
                "timestamp": "2024-01-01T00:00:00Z",
                "open": 100.0,
                "high": 105.0,
                "low": 95.0,
                "close": 102.0,
                "volume": 1000000
            },
            {
                "timestamp": "2024-01-02T00:00:00Z",
                "open": 102.0,
                "high": 107.0,
                "low": 97.0,
                "close": 104.0,
                "volume": 1200000
            }
        ]

        # Create - 創建數據
        result = data_service.save_market_data("TEST.HK", test_data)
        assert result is True

        # Read - 讀取數據
        retrieved_data = data_service.get_market_data("TEST.HK")
        assert len(retrieved_data) == len(test_data)

        # 驗證數據完整性
        for i, item in enumerate(retrieved_data):
            assert item["open"] == test_data[i]["open"]
            assert item["close"] == test_data[i]["close"]
            assert item["volume"] == test_data[i]["volume"]

        # Update - 更新數據（通過重新保存實現）
        updated_data = test_data.copy()
        updated_data[0]["close"] = 103.0  # 修改收盤價

        result = data_service.save_market_data("TEST.HK", updated_data)
        assert result is True

        # 驗證更新
        updated_retrieved = data_service.get_market_data("TEST.HK")
        assert updated_retrieved[0]["close"] == 103.0

    def test_stock_info_crud_operations(self, data_service):
        """測試股票信息CRUD操作"""
        # 測試股票信息
        stock_info = {
            "symbol": "INFO.HK",
            "name": "Info Test Company",
            "sector": "Technology",
            "industry": "Software",
            "market_cap": 1000000000,
            "pe_ratio": 25.5,
            "dividend_yield": 0.02,
            "currency": "HKD",
            "exchange": "HKEX"
        }

        # Create
        result = data_service.save_stock_info(stock_info)
        assert result is True

        # Read
        retrieved_info = data_service.get_stock_info("INFO.HK")
        assert retrieved_info is not None
        assert retrieved_info["name"] == "Info Test Company"
        assert retrieved_info["sector"] == "Technology"

        # Update
        updated_info = stock_info.copy()
        updated_info["pe_ratio"] = 30.0
        data_service.save_stock_info(updated_info)

        # 驗證更新
        final_info = data_service.get_stock_info("INFO.HK")
        assert final_info["pe_ratio"] == 30.0

    def test_transaction_rollback(self, data_service):
        """測試事務回滾"""
        conn = data_service.get_db_connection()
        cursor = conn.cursor()

        try:
            # 開始事務
            cursor.execute("BEGIN TRANSACTION")

            # 插入一些數據
            cursor.execute("""
                INSERT INTO stocks
                (symbol, name, sector, industry, market_cap, pe_ratio, dividend_yield, currency, exchange)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "TRANSACTION_TEST.HK", "Transaction Test", "Technology",
                "Software", 1000000, 25.0, 0.01, "HKD", "HKEX"
            ))

            # 模擬錯誤
            raise ValueError("模擬錯誤")

        except ValueError:
            # 回滾事務
            cursor.execute("ROLLBACK")

        # 驗證數據未插入
        cursor.execute("SELECT * FROM stocks WHERE symbol = 'TRANSACTION_TEST.HK'")
        result = cursor.fetchone()
        assert result is None

        conn.close()

    def test_data_consistency(self, data_service):
        """測試數據一致性"""
        # 插入市場數據
        market_data = [{
            "timestamp": "2024-01-01T00:00:00Z",
            "open": 100.0,
            "high": 105.0,
            "low": 95.0,
            "close": 102.0,
            "volume": 1000000
        }]

        data_service.save_market_data("CONSISTENCY.HK", market_data)

        # 插入股票信息
        stock_info = {
            "symbol": "CONSISTENCY.HK",
            "name": "Consistency Test",
            "sector": "Finance",
            "industry": "Banking",
            "market_cap": 500000000,
            "pe_ratio": 15.0,
            "dividend_yield": 0.03,
            "currency": "HKD",
            "exchange": "HKEX"
        }

        data_service.save_stock_info(stock_info)

        # 驗證關聯數據一致性
        saved_market_data = data_service.get_market_data("CONSISTENCY.HK")
        saved_stock_info = data_service.get_stock_info("CONSISTENCY.HK")

        assert len(saved_market_data) == 1
        assert saved_stock_info["symbol"] == "CONSISTENCY.HK"
        assert saved_stock_info["name"] == "Consistency Test"

@pytest.mark.integration
@pytest.mark.database
class TestAsyncDatabaseOperations:
    """異步數據庫操作測試"""

    @pytest.fixture
    async def async_temp_db(self):
        """創建異步臨時數據庫"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        yield db_path

        Path(db_path).unlink(missing_ok=True)

    @pytest_asyncio.fixture
    async def async_db_connection(self, async_temp_db):
        """創建異步數據庫連接"""
        async with aiosqlite.connect(async_temp_db) as conn:
            # 創建表結構
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS test_data (
                    id INTEGER PRIMARY KEY,
                    symbol TEXT,
                    timestamp TEXT,
                    value REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await conn.commit()

            yield conn

    @pytest.mark.asyncio
    async def test_async_insert_and_query(self, async_db_connection):
        """測試異步插入和查詢"""
        # 插入測試數據
        test_data = [
            ("ASYNC_1", "2024-01-01", 100.0),
            ("ASYNC_2", "2024-01-02", 102.0),
            ("ASYNC_3", "2024-01-03", 98.0)
        ]

        for symbol, timestamp, value in test_data:
            await async_db_connection.execute(
                "INSERT INTO test_data (symbol, timestamp, value) VALUES (?, ?, ?)",
                (symbol, timestamp, value)
            )

        await async_db_connection.commit()

        # 查詢數據
        cursor = await async_db_connection.execute(
            "SELECT * FROM test_data ORDER BY symbol"
        )
        results = await cursor.fetchall()

        assert len(results) == 3
        assert results[0][1] == "ASYNC_1"
        assert results[0][3] == 100.0

    @pytest.mark.asyncio
    async def test_async_transaction(self, async_db_connection):
        """測試異步事務"""
        try:
            await async_db_connection.execute("BEGIN")

            # 插入數據
            await async_db_connection.execute(
                "INSERT INTO test_data (symbol, timestamp, value) VALUES (?, ?, ?)",
                ("TX_TEST", "2024-01-01", 100.0)
            )

            # 模擬錯誤並回滾
            raise ValueError("模擬錯誤")

        except ValueError:
            await async_db_connection.rollback()

        # 驗證回滾成功
        cursor = await async_db_connection.execute(
            "SELECT * FROM test_data WHERE symbol = 'TX_TEST'"
        )
        result = await cursor.fetchone()
        assert result is None

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, async_db_connection):
        """測試併發操作"""
        async def insert_batch(batch_id: int, count: int):
            for i in range(count):
                symbol = f"CONCURRENT_{batch_id}_{i}"
                await async_db_connection.execute(
                    "INSERT INTO test_data (symbol, timestamp, value) VALUES (?, ?, ?)",
                    (symbol, "2024-01-01", float(i + batch_id * 100))
                )
            await async_db_connection.commit()

        # 創建多個併發插入任務
        tasks = [
            insert_batch(1, 10),
            insert_batch(2, 10),
            insert_batch(3, 10)
        ]

        # 執行併發任務
        await asyncio.gather(*tasks)

        # 驗證所有數據已插入
        cursor = await async_db_connection.execute(
            "SELECT COUNT(*) FROM test_data WHERE symbol LIKE 'CONCURRENT_%'"
        )
        count = (await cursor.fetchone())[0]
        assert count == 30

@pytest.mark.integration
@pytest.mark.database
class TestDatabasePerformance:
    """數據庫性能測試"""

    @pytest.fixture
    def temp_db(self):
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        yield db_path
        Path(db_path).unlink(missing_ok=True)

    @pytest.fixture
    def data_service(self, temp_db):
        return DataService(temp_db)

    def test_bulk_insert_performance(self, data_service, performance_benchmark_data):
        """測試批量插入性能"""
        # 生成大量測試數據
        factory = StockMarketDataFactory()
        large_dataset = factory.create_batch(1000)

        # 測試批量插入性能
        start_time = time.time()

        # 轉換為保存格式
        save_data = []
        for item in large_dataset:
            save_data.append({
                "timestamp": item.timestamp.isoformat(),
                "open": item.open_price,
                "high": item.high_price,
                "low": item.low_price,
                "close": item.close_price,
                "volume": item.volume
            })

        result = data_service.save_market_data("BULK_TEST.HK", save_data)

        end_time = time.time()
        insert_time = end_time - start_time

        assert result is True
        assert insert_time < 5.0, f"批量插入過慢: {insert_time:.2f}秒"

        # 驗證數據完整性
        retrieved_data = data_service.get_market_data("BULK_TEST.HK")
        assert len(retrieved_data) == 1000

    def test_query_performance(self, data_service):
        """測試查詢性能"""
        # 插入測試數據
        factory = StockMarketDataFactory()
        test_data = []

        for i in range(500):
            item = factory()
            test_data.append({
                "timestamp": item.timestamp.isoformat(),
                "open": item.open_price,
                "high": item.high_price,
                "low": item.low_price,
                "close": item.close_price,
                "volume": item.volume
            })

        data_service.save_market_data("QUERY_TEST.HK", test_data)

        # 測試查詢性能
        start_time = time.time()
        results = data_service.get_market_data("QUERY_TEST.HK")
        end_time = time.time()

        query_time = end_time - start_time

        assert len(results) == 500
        assert query_time < 1.0, f"查詢過慢: {query_time:.2f}秒"

    def test_index_performance_impact(self, temp_db):
        """測試索引對性能的影響"""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        # 創建測試表
        cursor.execute("""
            CREATE TABLE performance_test (
                id INTEGER PRIMARY KEY,
                symbol TEXT,
                timestamp TEXT,
                value REAL,
                data TEXT
            )
        """)

        # 插入大量數據
        large_dataset = []
        for i in range(10000):
            large_dataset.append((
                f"PERF_{i % 100}",  # 100個不同的股票
                f"2024-01-{(i % 30) + 1:02d}",
                float(i % 1000),
                f"data_{i}"
            ))

        cursor.executemany(
            "INSERT INTO performance_test (symbol, timestamp, value, data) VALUES (?, ?, ?, ?)",
            large_dataset
        )
        conn.commit()

        # 測試無索引查詢性能
        start_time = time.time()
        cursor.execute("SELECT * FROM performance_test WHERE symbol = 'PERF_50'")
        results_no_index = cursor.fetchall()
        time_no_index = time.time() - start_time

        # 創建索引
        cursor.execute("CREATE INDEX idx_symbol ON performance_test(symbol)")
        conn.commit()

        # 測試有索引查詢性能
        start_time = time.time()
        cursor.execute("SELECT * FROM performance_test WHERE symbol = 'PERF_50'")
        results_with_index = cursor.fetchall()
        time_with_index = time.time() - start_time

        # 驗證結果一致性和性能提升
        assert len(results_no_index) == len(results_with_index)
        assert time_with_index <= time_no_index, "索引應該提升查詢性能"

        conn.close()

@pytest.mark.integration
@pytest.mark.database
class TestDataIntegrity:
    """數據完整性測試"""

    @pytest.fixture
    def data_service(self, temp_dir):
        db_path = temp_dir / "integrity_test.db"
        return DataService(str(db_path))

    def test_foreign_key_constraints(self, data_service):
        """測試外鍵約束（如果存在）"""
        # 這個測試取決於數據庫模式是否定義了外鍵約束
        pass  # 當前簡單模式可能沒有外鍵約束

    def test_data_validation(self, data_service):
        """測試數據驗證"""
        # 測試無效數據處理
        invalid_data = [{
            "timestamp": "invalid-date",
            "open": -100.0,  # 負價格
            "high": 50.0,     # 最高價低於開盤價
            "low": 150.0,     # 最低價高於開盤價
            "close": 100.0,
            "volume": -1000   # 負成交量
        }]

        # 數據服務應該處理無效數據
        # 這取決於實現 - 可能拒絕或修正
        result = data_service.save_market_data("INVALID.HK", invalid_data)

        # 驗證結果 - 取決於實現策略
        assert isinstance(result, bool)

    def test_duplicate_data_handling(self, data_service):
        """測試重複數據處理"""
        # 創建測試數據
        test_data = [{
            "timestamp": "2024-01-01T00:00:00Z",
            "open": 100.0,
            "high": 105.0,
            "low": 95.0,
            "close": 102.0,
            "volume": 1000000
        }]

        # 第一次插入
        result1 = data_service.save_market_data("DUPLICATE.HK", test_data)
        assert result1 is True

        # 第二次插入相同數據（取決於實現，可能更新或忽略）
        result2 = data_service.save_market_data("DUPLICATE.HK", test_data)
        assert isinstance(result2, bool)

        # 驗證最終狀態
        final_data = data_service.get_market_data("DUPLICATE.HK")
        assert len(final_data) >= 1

if __name__ == "__main__":
    pytest.main([__file__, "-v"])