#!/usr/bin/env python3
"""
企業級測試框架全局配置
Pytest configuration and fixtures for enterprise testing framework
"""

import pytest
import asyncio
import logging
import tempfile
import shutil
from pathlib import Path
from typing import Generator, Dict, Any, AsyncGenerator
import pandas as pd
import numpy as np
from unittest.mock import Mock, AsyncMock
import sqlite3
import json
import time
import os
from datetime import date, timedelta

# Configure logging for tests
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 測試數據常數
TEST_STOCK_DATA = {
    "0700.HK": {
        "2024-01-01": 320.50,
        "2024-01-02": 318.20,
        "2024-01-03": 325.80,
        "2024-01-04": 322.10,
        "2024-01-05": 328.90,
    },
    "0941.HK": {
        "2024-01-01": 45.20,
        "2024-01-02": 44.80,
        "2024-01-03": 46.10,
        "2024-01-04": 45.50,
        "2024-01-05": 47.20,
    }
}

# HIBOR測試數據
TEST_HIBOR_DATA = {
    "date": "2024-01-01",
    "tenor": "Overnight",
    "rate": 3.15
}

# VectorBT測試數據
TEST_VECTORBT_DATA = pd.DataFrame({
    'close': [100, 102, 98, 105, 103, 108, 106, 110, 107, 112],
    'volume': [1000, 1200, 800, 1500, 900, 1800, 1100, 2000, 1300, 2200],
    'open': [99, 101, 103, 97, 106, 102, 109, 105, 111, 106],
    'high': [102, 104, 104, 107, 108, 110, 112, 113, 114, 115],
    'low': [98, 100, 96, 96, 101, 100, 104, 103, 105, 105]
}, index=pd.date_range('2024-01-01', periods=10))

@pytest.fixture(scope="session")
def event_loop():
    """創建事件循環用於異步測試"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def temp_dir() -> Generator[Path, None, None]:
    """臨時目錄fixture"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)

@pytest.fixture(scope="session")
def test_database(temp_dir: Path) -> Generator[str, None, None]:
    """測試數據庫fixture"""
    db_path = temp_dir / "test_quant_system.db"

    # 創建測試數據庫
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # 創建表結構
    cursor.execute("""
        CREATE TABLE market_data (
            symbol TEXT,
            timestamp TEXT,
            open_price REAL,
            high_price REAL,
            low_price REAL,
            close_price REAL,
            volume INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE stocks (
            symbol TEXT PRIMARY KEY,
            name TEXT,
            sector TEXT,
            industry TEXT,
            market_cap INTEGER,
            pe_ratio REAL,
            dividend_yield REAL,
            currency TEXT,
            exchange TEXT
        )
    """)

    # 插入測試數據
    for symbol, prices in TEST_STOCK_DATA.items():
        for date, price in prices.items():
            cursor.execute("""
                INSERT INTO market_data
                (symbol, timestamp, open_price, high_price, low_price, close_price, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (symbol, date, price * 0.98, price * 1.02, price * 0.97, price, 1000))

    conn.commit()
    conn.close()

    yield f"sqlite:///{db_path}"

@pytest.fixture
def mock_stock_api_response():
    """模擬股票API響應"""
    return {
        "data": {
            "close": TEST_STOCK_DATA["0700.HK"]
        },
        "symbol": "0700.HK",
        "timestamp": "2024-01-01T00:00:00Z"
    }

@pytest.fixture
def mock_hibor_response():
    """模擬HIBOR API響應"""
    return {
        "success": True,
        "data": {
            "date": "2024-01-01",
            "tenor": "Overnight",
            "rate": 3.15
        }
    }

@pytest.fixture
def sample_stock_dataframe():
    """創建測試用股票數據DataFrame"""
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    np.random.seed(42)

    # 生成模擬股價數據 (隨機漫步)
    initial_price = 100
    returns = np.random.normal(0.001, 0.02, 100)  # 日回報率
    prices = [initial_price]
    for ret in returns[1:]:
        prices.append(prices[-1] * (1 + ret))

    data = pd.DataFrame({
        'close': prices,
        'volume': np.random.randint(1000, 10000, 100),
        'open': np.array(prices) * np.random.uniform(0.99, 1.01, 100),
        'high': np.array(prices) * np.random.uniform(1.01, 1.05, 100),
        'low': np.array(prices) * np.random.uniform(0.95, 0.99, 100)
    }, index=dates)

    return data

@pytest.fixture
def sample_indicators_data():
    """創建測試用技術指標數據"""
    periods = 20
    dates = pd.date_range('2024-01-01', periods=periods, freq='D')

    return {
        'RSI': pd.Series(np.random.uniform(20, 80, periods), index=dates),
        'MACD': pd.Series(np.random.uniform(-2, 2, periods), index=dates),
        'Signal': pd.Series(np.random.uniform(-1.5, 1.5, periods), index=dates),
        'SMA_20': pd.Series(np.random.uniform(95, 105, periods), index=dates),
        'EMA_12': pd.Series(np.random.uniform(97, 103, periods), index=dates),
        'Upper_Band': pd.Series(np.random.uniform(105, 110, periods), index=dates),
        'Lower_Band': pd.Series(np.random.uniform(90, 95, periods), index=dates),
    }

@pytest.fixture
def mock_telegram_bot():
    """模擬Telegram Bot"""
    bot = Mock()
    bot.send_message = Mock(return_value=True)
    bot.send_document = Mock(return_value=True)
    return bot

@pytest.fixture
def sharpe_test_data():
    """Sharpe比率計算測試數據"""
    returns = np.array([0.01, 0.02, -0.01, 0.03, 0.01, -0.02, 0.02, 0.01, 0.00, 0.02])
    risk_free_rate = 0.03 / 252  # 日無風險利率
    return returns, risk_free_rate

@pytest.fixture
def performance_benchmark_data():
    """性能基準測試數據"""
    return {
        'small_data': pd.Series(np.random.randn(100)),
        'medium_data': pd.Series(np.random.randn(1000)),
        'large_data': pd.Series(np.random.randn(10000)),
        'rsi_period': 14,
        'macd_params': (12, 26, 9)
    }

@pytest.fixture
async def async_client():
    """異步HTTP客戶端fixture"""
    import httpx
    async with httpx.AsyncClient() as client:
        yield client

@pytest.fixture
def mock_external_apis():
    """外部API模擬fixture"""
    class MockAPIs:
        def __init__(self):
            self.hkma_api = Mock()
            self.stock_api = Mock()
            self.telegram_api = Mock()

        def mock_hkma_response(self):
            return {"success": True, "data": TEST_HIBOR_DATA}

        def mock_stock_response(self, symbol):
            return {
                "data": {"close": TEST_STOCK_DATA.get(symbol, {})},
                "symbol": symbol
            }

    return MockAPIs()

# 保留原有的fixture
@pytest.fixture(scope="session")
def test_data():
    """提供測試數據"""
    today = date.today()
    return {
        "valid_task": {
            "title": "測試任務",
            "description": "這是一個測試任務",
            "priority": "P1",
            "estimated_hours": 3,
            "assignee": "測試用戶",
        },
        "valid_sprint": {
            "name": "測試Sprint",
            "goal": "測試Sprint創建",
            "start_date": today.isoformat(),
            "end_date": (today + timedelta(days=14)).isoformat(),
        },
        "task_priorities": ["P0", "P1", "P2"],
        "task_statuses": ["TODO", "IN_PROGRESS", "REVIEW", "DONE", "BLOCKED"],
        "sprint_statuses": ["PLANNING", "ACTIVE", "COMPLETED", "CANCELLED"],
    }

@pytest.fixture
def sample_tasks(test_data):
    """提供多個示例任務"""
    return [
        {"title": f"任務{i}", "priority": "P1", "estimated_hours": 2 + i}
        for i in range(1, 6)
    ]

@pytest.fixture
def sample_sprints(test_data):
    """提供多個示例Sprint"""
    today = date.today()
    return [
        {
            "name": f"Sprint {i}",
            "goal": f"測試Sprint {i}",
            "start_date": today.isoformat(),
            "end_date": (today + timedelta(days=14)).isoformat(),
        }
        for i in range(1, 4)
    ]

# 測試標記定義
def pytest_configure(config):
    """配置pytest標記"""
    config.addinivalue_line(
        "markers", "unit: 標記單元測試"
    )
    config.addinivalue_line(
        "markers", "integration: 標記集成測試"
    )
    config.addinivalue_line(
        "markers", "e2e: 標記端到端測試"
    )
    config.addinivalue_line(
        "markers", "performance: 標記性能測試"
    )
    config.addinivalue_line(
        "markers", "security: 標記安全測試"
    )
    config.addinivalue_line(
        "markers", "slow: 標記慢速測試"
    )
    config.addinivalue_line(
        "markers", "gpu: 標記GPU相關測試"
    )

# 測試收集鉤子
def pytest_collection_modifyitems(config, items):
    """修改測試收集，自動添加標記"""
    for item in items:
        # 根據文件路徑自動添加標記
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
        elif "performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
        elif "security" in str(item.fspath):
            item.add_marker(pytest.mark.security)

# 環境變量設置
@pytest.fixture(autouse=True)
def set_test_environment():
    """設置測試環境變量"""
    original_env = {}
    test_env_vars = {
        "TESTING": "true",
        "DATABASE_URL": "sqlite:///test.db",
        "LOG_LEVEL": "DEBUG",
        "HKMA_API_URL": "https://mock-api.hkma.gov.hk",
        "STOCK_API_URL": "http://mock-stock-api.local"
    }

    # 保存原始環境變量
    for key, value in test_env_vars.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value

    yield

    # 恢復原始環境變量
    for key, original_value in original_env.items():
        if original_value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = original_value