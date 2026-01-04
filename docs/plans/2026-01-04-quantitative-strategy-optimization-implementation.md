# 高 SR-MDD 量化交易策略優化系統實施計劃

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**目標:** 構建個人使用的純數據驅動量化策略優化系統，自動發現並維持高夏普比率、低最大回撤的策略組合。

**架構:** 多時間框架並行處理（分鐘/日/週）→ 多維數據融合（價格+基本面+另類）→ 自適應優化引擎（貝葉斯/遺傳算法）→ 多策略動態組合 → 嚴格回測驗證 → 實盤監控。

**技術棧:**
- 數據源: Yahoo Finance API, HKEX database
- 優化: scikit-optimize, DEAP, Optuna
- 回測: VectorBT, Backtrader
- 特徵: TA-Lib, pandas, numpy
- 存儲: PostgreSQL, InfluxDB, Redis
- 部署: 本地 Docker, Futu API

---

## Phase 1: 數據層基礎設施 (2-3週)

### Task 1: 創建優化系統項目結構

**Files:**
- Create: `src/strategies/optimization/__init__.py`
- Create: `src/strategies/optimization/data/__init__.py`
- Create: `src/strategies/optimization/data/fetchers.py`
- Create: `src/strategies/optimization/data/storage.py`
- Create: `src/strategies/optimization/features/__init__.py`
- Create: `src/strategies/optimization/optimizers/__init__.py`
- Create: `src/strategies/optimization/backtest/__init__.py`
- Test: `tests/strategies/optimization/test_data_fetchers.py`

**Step 1: Write the failing test**

```python
# tests/strategies/optimization/test_data_fetchers.py
import pytest
from src.strategies.optimization.data.fetchers import YahooFinanceFetcher

def test_yahoo_fetcher_initialization():
    """Test Yahoo Finance fetcher can be initialized"""
    fetcher = YahooFinanceFetcher()
    assert fetcher is not None
    assert fetcher.base_url == "https://query1.finance.yahoo.com"

def test_yahoo_fetcher_fetch_single_ticker():
    """Test fetching single ticker data"""
    fetcher = YahooFinanceFetcher()
    data = fetcher.fetch("AAPL", period="1mo")
    assert data is not None
    assert len(data) > 0
    assert "close" in data.columns
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/strategies/optimization/test_data_fetchers.py -v`

Expected: FAIL with "ModuleNotFoundError: No module named 'src.strategies.optimization'"

**Step 3: Write minimal implementation**

```python
# src/strategies/optimization/__init__.py
"""Strategy optimization module for finding high SR/low MDD strategies"""

__version__ = "0.1.0"

# src/strategies/optimization/data/__init__.py
"""Data fetching and storage layer for optimization"""

# src/strategies/optimization/features/__init__.py
"""Feature engineering for optimization"""

# src/strategies/optimization/optimizers/__init__.py
"""Optimization algorithms (Bayesian, Genetic, etc.)"""

# src/strategies/optimization/backtest/__init__.py
"""Backtesting engine for validation"""

# src/strategies/optimization/data/fetchers.py
import yfinance as yf
import pandas as pd
from typing import Optional, Dict, Any

class YahooFinanceFetcher:
    """Fetch stock data from Yahoo Finance API"""

    def __init__(self):
        self.base_url = "https://query1.finance.yahoo.com"

    def fetch(self, ticker: str, period: str = "1mo") -> Optional[pd.DataFrame]:
        """
        Fetch OHLCV data for a ticker

        Args:
            ticker: Stock symbol (e.g., 'AAPL')
            period: Time period ('1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max')

        Returns:
            DataFrame with OHLCV data or None if failed
        """
        try:
            stock = yf.Ticker(ticker)
            data = stock.history(period=period)

            if data.empty:
                return None

            # Standardize column names
            data.columns = [col.lower().replace(' ', '_') for col in data.columns]

            return data

        except Exception as e:
            print(f"Error fetching {ticker}: {e}")
            return None

# src/strategies/optimization/data/storage.py
"""Data storage layer using PostgreSQL and InfluxDB"""
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/strategies/optimization/test_data_fetchers.py -v`

Expected: PASS (2 tests)

**Step 5: Commit**

```bash
git add src/strategies/optimization/ tests/strategies/optimization/
git commit -m "feat: create optimization system project structure and Yahoo Finance fetcher"
```

---

### Task 2: 實現 HKEX 數據整合

**Files:**
- Modify: `src/strategies/optimization/data/fetchers.py`
- Test: `tests/strategies/optimization/test_data_fetchers.py`

**Step 1: Write the failing test**

```python
# Add to tests/strategies/optimization/test_data_fetchers.py
from src.strategies.optimization.data.fetchers import HKEXFetcher

def test_hkex_fetcher_initialization():
    """Test HKEX fetcher can be initialized"""
    fetcher = HKEXFetcher()
    assert fetcher is not None
    assert hasattr(fetcher, 'db_connection')

def test_hkex_fetcher_get_stock_list():
    """Test getting stock list from HKEX"""
    fetcher = HKEXFetcher()
    stocks = fetcher.get_stock_list()
    assert stocks is not None
    assert len(stocks) > 0
    assert isinstance(stocks[0], dict)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/strategies/optimization/test_data_fetchers.py::test_hkex_fetcher_initialization -v`

Expected: FAIL with "cannot import 'HKEXFetcher'"

**Step 3: Write minimal implementation**

```python
# Add to src/strategies/optimization/data/fetchers.py
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

from src.api.market_data_endpoints import get_stock_list

class HKEXFetcher:
    """Fetch market data from existing HKEX database"""

    def __init__(self):
        """Initialize HKEX fetcher with existing database connection"""
        self.db_connection = None  # Will use existing connection from src/api
        self.base_url = "http://localhost:3007/api/market"

    def get_stock_list(self) -> Optional[list]:
        """
        Get list of available stocks from HKEX

        Returns:
            List of stock dictionaries or None if failed
        """
        try:
            # Use existing API endpoint
            import requests
            response = requests.get(f"{self.base_url}/stocks", timeout=10)

            if response.status_code == 200:
                return response.json().get('stocks', [])

            return None

        except Exception as e:
            print(f"Error getting HKEX stock list: {e}")
            return None

    def fetch(self, symbol: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """
        Fetch historical data for HKEX stock

        Args:
            symbol: Stock symbol (e.g., '0700.HK')
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            DataFrame with OHLCV data or None if failed
        """
        try:
            import requests
            params = {
                'symbol': symbol,
                'start': start_date,
                'end': end_date
            }
            response = requests.get(f"{self.base_url}/history", params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                df = pd.DataFrame(data['prices'])
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                return df

            return None

        except Exception as e:
            print(f"Error fetching HKEX data for {symbol}: {e}")
            return None
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/strategies/optimization/test_data_fetchers.py::test_hkex_fetcher_initialization -v`

Expected: PASS

**Step 5: Commit**

```bash
git add src/strategies/optimization/data/fetchers.py tests/strategies/optimization/test_data_fetchers.py
git commit -m "feat: add HKEX data fetcher integration"
```

---

### Task 3: 實現數據存儲層

**Files:**
- Modify: `src/strategies/optimization/data/storage.py`
- Test: `tests/strategies/optimization/test_data_storage.py`

**Step 1: Write the failing test**

```python
# tests/strategies/optimization/test_data_storage.py
import pytest
import pandas as pd
from datetime import datetime, timedelta
from src.strategies.optimization.data.storage import DataStorage

def test_data_storage_save_and_retrieve():
    """Test saving and retrieving market data"""
    storage = DataStorage()

    # Create sample data
    dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
    data = pd.DataFrame({
        'open': range(100),
        'high': range(100, 200),
        'low': range(50, 150),
        'close': range(75, 175),
        'volume': range(1000, 1100)
    }, index=dates)

    # Save data
    storage.save('TEST', data, 'daily')

    # Retrieve data
    retrieved = storage.get('TEST', 'daily')

    assert retrieved is not None
    assert len(retrieved) == 100
    assert 'close' in retrieved.columns
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/strategies/optimization/test_data_storage.py -v`

Expected: FAIL with "cannot import 'DataStorage'"

**Step 3: Write minimal implementation**

```python
# src/strategies/optimization/data/storage.py
import pandas as pd
from typing import Optional
from datetime import datetime
import psycopg2
from psycopg2.extras import execute_values
import json

class DataStorage:
    """Store and retrieve market data using PostgreSQL and InfluxDB"""

    def __init__(self, postgres_config: dict = None, influx_config: dict = None):
        """
        Initialize data storage

        Args:
            postgres_config: PostgreSQL connection config
            influx_config: InfluxDB connection config
        """
        self.postgres_config = postgres_config or {
            'host': 'localhost',
            'port': 5432,
            'database': 'cbsc',
            'user': 'postgres',
            'password': 'postgres'
        }

        self.influx_config = influx_config or {
            'host': 'localhost',
            'port': 8086,
            'database': 'market_data'
        }

        self.postgres_conn = None
        self._connect_postgres()

    def _connect_postgres(self):
        """Establish PostgreSQL connection"""
        try:
            self.postgres_conn = psycopg2.connect(**self.postgres_config)
        except Exception as e:
            print(f"Warning: Could not connect to PostgreSQL: {e}")
            self.postgres_conn = None

    def save(self, symbol: str, data: pd.DataFrame, timeframe: str) -> bool:
        """
        Save market data to storage

        Args:
            symbol: Stock symbol
            data: DataFrame with OHLCV data
            timeframe: Timeframe ('minute', 'daily', 'weekly')

        Returns:
            True if successful, False otherwise
        """
        if self.postgres_conn is None:
            print("No PostgreSQL connection available")
            return False

        try:
            cursor = self.postgres_conn.cursor()

            # Create table if not exists
            table_name = f"market_data_{timeframe}"
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(20) NOT NULL,
                    date DATE NOT NULL,
                    open DECIMAL(15, 4),
                    high DECIMAL(15, 4),
                    low DECIMAL(15, 4),
                    close DECIMAL(15, 4),
                    volume BIGINT,
                    created_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(symbol, date)
                )
            """)

            # Insert data
            values = []
            for date, row in data.iterrows():
                values.append((
                    symbol,
                    date.strftime('%Y-%m-%d'),
                    float(row.get('open', 0)),
                    float(row.get('high', 0)),
                    float(row.get('low', 0)),
                    float(row.get('close', 0)),
                    int(row.get('volume', 0))
                ))

            execute_values(
                cursor,
                f"""
                INSERT INTO {table_name} (symbol, date, open, high, low, close, volume)
                VALUES %s
                ON CONFLICT (symbol, date) DO UPDATE
                SET open = EXCLUDED.open, high = EXCLUDED.high,
                    low = EXCLUDED.low, close = EXCLUDED.close, volume = EXCLUDED.volume
                """,
                values
            )

            self.postgres_conn.commit()
            cursor.close()

            return True

        except Exception as e:
            print(f"Error saving data: {e}")
            if self.postgres_conn:
                self.postgres_conn.rollback()
            return False

    def get(self, symbol: str, timeframe: str,
            start_date: str = None, end_date: str = None) -> Optional[pd.DataFrame]:
        """
        Retrieve market data from storage

        Args:
            symbol: Stock symbol
            timeframe: Timeframe ('minute', 'daily', 'weekly')
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            DataFrame with OHLCV data or None if failed
        """
        if self.postgres_conn is None:
            return None

        try:
            cursor = self.postgres_conn.cursor()

            table_name = f"market_data_{timeframe}"
            query = f"""
                SELECT date, open, high, low, close, volume
                FROM {table_name}
                WHERE symbol = %s
            """
            params = [symbol]

            if start_date:
                query += " AND date >= %s"
                params.append(start_date)

            if end_date:
                query += " AND date <= %s"
                params.append(end_date)

            query += " ORDER BY date ASC"

            cursor.execute(query, params)
            rows = cursor.fetchall()
            cursor.close()

            if not rows:
                return None

            df = pd.DataFrame(rows, columns=['date', 'open', 'high', 'low', 'close', 'volume'])
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)

            return df

        except Exception as e:
            print(f"Error retrieving data: {e}")
            return None

    def __del__(self):
        """Close database connection on delete"""
        if self.postgres_conn:
            self.postgres_conn.close()
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/strategies/optimization/test_data_storage.py -v`

Expected: PASS

**Step 5: Commit**

```bash
git add src/strategies/optimization/data/storage.py tests/strategies/optimization/test_data_storage.py
git commit -m "feat: implement data storage layer with PostgreSQL"
```

---

### Task 4: 實現 TA-Lib 技術指標計算

**Files:**
- Create: `src/strategies/optimization/features/technical.py`
- Test: `tests/strategies/optimization/test_technical_features.py`

**Step 1: Write the failing test**

```python
# tests/strategies/optimization/test_technical_features.py
import pytest
import pandas as pd
import numpy as np
from src.strategies.optimization.features.technical import TechnicalIndicators

def test_sma_calculation():
    """Test Simple Moving Average calculation"""
    # Create sample data
    data = pd.DataFrame({
        'close': np.random.randn(100).cumsum() + 100
    })

    indicators = TechnicalIndicators()
    sma = indicators.sma(data['close'], period=20)

    assert sma is not None
    assert len(sma) == len(data)
    assert sma.isna().sum() == 20  # First 20 values are NaN

def test_rsi_calculation():
    """Test RSI calculation"""
    data = pd.DataFrame({
        'close': np.random.randn(100).cumsum() + 100
    })

    indicators = TechnicalIndicators()
    rsi = indicators.rsi(data['close'], period=14)

    assert rsi is not None
    assert rsi.min() >= 0
    assert rsi.max() <= 100
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/strategies/optimization/test_technical_features.py -v`

Expected: FAIL with "cannot import 'TechnicalIndicators'"

**Step 3: Write minimal implementation**

```python
# src/strategies/optimization/features/technical.py
import pandas as pd
import numpy as np
from typing import Optional

try:
    import talib
    HAS_TALIB = True
except ImportError:
    HAS_TALIB = False
    print("Warning: TA-Lib not installed, using pure Python implementations")

class TechnicalIndicators:
    """Calculate technical indicators using TA-Lib or pure Python"""

    def __init__(self):
        """Initialize technical indicators calculator"""
        self.use_talib = HAS_TALIB

    def sma(self, series: pd.Series, period: int = 20) -> pd.Series:
        """
        Calculate Simple Moving Average

        Args:
            series: Price series
            period: Moving average period

        Returns:
            Series with SMA values
        """
        if self.use_talib:
            return pd.Series(talib.SMA(series.values, timeperiod=period), index=series.index)
        else:
            return series.rolling(window=period).mean()

    def ema(self, series: pd.Series, period: int = 20) -> pd.Series:
        """Calculate Exponential Moving Average"""
        if self.use_talib:
            return pd.Series(talib.EMA(series.values, timeperiod=period), index=series.index)
        else:
            return series.ewm(span=period, adjust=False).mean()

    def rsi(self, series: pd.Series, period: int = 14) -> pd.Series:
        """
        Calculate Relative Strength Index

        Args:
            series: Price series
            period: RSI period

        Returns:
            Series with RSI values (0-100)
        """
        if self.use_talib:
            return pd.Series(talib.RSI(series.values, timeperiod=period), index=series.index)
        else:
            # Pure Python implementation
            delta = series.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))

            return rsi

    def bollinger_bands(self, series: pd.Series, period: int = 20,
                       std_dev: float = 2.0) -> pd.DataFrame:
        """
        Calculate Bollinger Bands

        Returns:
            DataFrame with 'upper', 'middle', 'lower' columns
        """
        sma = self.sma(series, period)
        std = series.rolling(window=period).std()

        return pd.DataFrame({
            'upper': sma + (std * std_dev),
            'middle': sma,
            'lower': sma - (std * std_dev)
        }, index=series.index)

    def macd(self, series: pd.Series, fast: int = 12, slow: int = 26,
             signal: int = 9) -> pd.DataFrame:
        """
        Calculate MACD (Moving Average Convergence Divergence)

        Returns:
            DataFrame with 'macd', 'signal', 'histogram' columns
        """
        ema_fast = self.ema(series, fast)
        ema_slow = self.ema(series, slow)

        macd_line = ema_fast - ema_slow
        signal_line = self.ema(macd_line, signal)
        histogram = macd_line - signal_line

        return pd.DataFrame({
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }, index=series.index)

    def atr(self, high: pd.Series, low: pd.Series, close: pd.Series,
            period: int = 14) -> pd.Series:
        """Calculate Average True Range"""
        if self.use_talib:
            return pd.Series(
                talib.ATR(high.values, low.values, close.values, timeperiod=period),
                index=close.index
            )
        else:
            high_low = high - low
            high_close = np.abs(high - close.shift())
            low_close = np.abs(low - close.shift())

            tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            return tr.rolling(window=period).mean()

    def stoch(self, high: pd.Series, low: pd.Series, close: pd.Series,
              k_period: int = 14, d_period: int = 3) -> pd.DataFrame:
        """
        Calculate Stochastic Oscillator

        Returns:
            DataFrame with 'k', 'd' columns
        """
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()

        k = 100 * (close - lowest_low) / (highest_high - lowest_low)
        d = k.rolling(window=d_period).mean()

        return pd.DataFrame({'k': k, 'd': d}, index=close.index)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/strategies/optimization/test_technical_features.py -v`

Expected: PASS

**Step 5: Commit**

```bash
git add src/strategies/optimization/features/technical.py tests/strategies/optimization/test_technical_features.py
git commit -m "feat: implement technical indicators calculator"
```

---

### Task 5: 實現特徵工程管道

**Files:**
- Create: `src/strategies/optimization/features/engine.py`
- Test: `tests/strategies/optimization/test_feature_engine.py`

**Step 1: Write the failing test**

```python
# tests/strategies/optimization/test_feature_engine.py
import pytest
import pandas as pd
import numpy as np
from src.strategies.optimization.features.engine import FeatureEngine

def test_feature_engine_initialization():
    """Test feature engine can be initialized"""
    engine = FeatureEngine()
    assert engine is not None
    assert hasattr(engine, 'technical')

def test_feature_engine_create_features():
    """Test creating all features from OHLCV data"""
    # Create sample OHLCV data
    data = pd.DataFrame({
        'open': np.random.randn(100).cumsum() + 100,
        'high': np.random.randn(100).cumsum() + 105,
        'low': np.random.randn(100).cumsum() + 95,
        'close': np.random.randn(100).cumsum() + 100,
        'volume': np.random.randint(1000, 10000, 100)
    })

    engine = FeatureEngine()
    features = engine.create_features(data)

    assert features is not None
    assert len(features) == len(data)
    # Check for expected features
    expected_cols = ['sma_20', 'rsi_14', 'returns_1d', 'volatility_20d']
    for col in expected_cols:
        assert col in features.columns
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/strategies/optimization/test_feature_engine.py -v`

Expected: FAIL with "cannot import 'FeatureEngine'"

**Step 3: Write minimal implementation**

```python
# src/strategies/optimization/features/engine.py
import pandas as pd
import numpy as np
from typing import Optional, List
from .technical import TechnicalIndicators

class FeatureEngine:
    """Comprehensive feature engineering for trading strategies"""

    def __init__(self):
        """Initialize feature engine"""
        self.technical = TechnicalIndicators()

    def create_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Create comprehensive features from OHLCV data

        Args:
            data: DataFrame with OHLCV columns

        Returns:
            DataFrame with engineered features
        """
        features = data.copy()

        # Technical indicators
        features = self._add_technical_features(features)

        # Price features
        features = self._add_price_features(features)

        # Volume features
        features = self._add_volume_features(features)

        # Statistical features
        features = self._add_statistical_features(features)

        return features

    def _add_technical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicator features"""
        # Moving averages
        df['sma_20'] = self.technical.sma(df['close'], 20)
        df['sma_50'] = self.technical.sma(df['close'], 50)
        df['ema_12'] = self.technical.ema(df['close'], 12)
        df['ema_26'] = self.technical.ema(df['close'], 26)

        # RSI
        df['rsi_14'] = self.technical.rsi(df['close'], 14)

        # MACD
        macd = self.technical.macd(df['close'])
        df['macd'] = macd['macd']
        df['macd_signal'] = macd['signal']
        df['macd_hist'] = macd['histogram']

        # Bollinger Bands
        bb = self.technical.bollinger_bands(df['close'])
        df['bb_upper'] = bb['upper']
        df['bb_middle'] = bb['middle']
        df['bb_lower'] = bb['lower']
        df['bb_width'] = (bb['upper'] - bb['lower']) / bb['middle']

        # ATR
        df['atr_14'] = self.technical.atr(df['high'], df['low'], df['close'], 14)

        # Stochastic
        stoch = self.technical.stoch(df['high'], df['low'], df['close'])
        df['stoch_k'] = stoch['k']
        df['stoch_d'] = stoch['d']

        return df

    def _add_price_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add price-based features"""
        # Returns
        df['returns_1d'] = df['close'].pct_change(1)
        df['returns_5d'] = df['close'].pct_change(5)
        df['returns_20d'] = df['close'].pct_change(20)

        # Log returns
        df['log_returns_1d'] = np.log(df['close'] / df['close'].shift(1))

        # Price position in range
        df['price_position'] = (df['close'] - df['low']) / (df['high'] - df['low'])

        # Gap
        df['gap'] = (df['open'] - df['close'].shift(1)) / df['close'].shift(1)

        return df

    def _add_volume_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add volume-based features"""
        # Volume moving averages
        df['volume_sma_20'] = df['volume'].rolling(20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma_20']

        # Volume change
        df['volume_change'] = df['volume'].pct_change(1)

        # Price-volume trend
        df['pvt'] = (df['close'].pct_change() * df['volume']).cumsum()

        return df

    def _add_statistical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add statistical features"""
        # Rolling volatility
        df['volatility_20d'] = df['returns_1d'].rolling(20).std()

        # Rolling skewness and kurtosis
        df['skew_20d'] = df['returns_1d'].rolling(20).skew()
        df['kurtosis_20d'] = df['returns_1d'].rolling(20).kurt()

        # Z-score
        rolling_mean = df['close'].rolling(20).mean()
        rolling_std = df['close'].rolling(20).std()
        df['zscore_20d'] = (df['close'] - rolling_mean) / rolling_std

        return df

    def select_features(self, features: pd.DataFrame,
                       method: str = 'variance',
                       threshold: float = 0.01) -> List[str]:
        """
        Select important features using various methods

        Args:
            features: DataFrame with all features
            method: Selection method ('variance', 'correlation', 'all')
            threshold: Threshold for selection

        Returns:
            List of selected feature names
        """
        if method == 'all':
            return features.columns.tolist()

        # Remove columns with low variance
        if method == 'variance':
            variances = features.var()
            selected = variances[variances > threshold].index.tolist()
            return selected

        # Remove highly correlated features
        if method == 'correlation':
            corr_matrix = features.corr().abs()
            upper_triangle = corr_matrix.where(
                np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
            )

            to_drop = [column for column in upper_triangle.columns
                       if any(upper_triangle[column] > threshold)]

            selected = [col for col in features.columns if col not in to_drop]
            return selected

        return features.columns.tolist()
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/strategies/optimization/test_feature_engine.py -v`

Expected: PASS

**Step 5: Commit**

```bash
git add src/strategies/optimization/features/engine.py tests/strategies/optimization/test_feature_engine.py
git commit -m "feat: implement feature engineering pipeline"
```

---

## Phase 2: 優化引擎 (3-4週)

### Task 6: 實現目標函數

**Files:**
- Create: `src/strategies/optimization/optimizers/objective.py`
- Test: `tests/strategies/optimization/test_objective.py`

**Step 1: Write the failing test**

```python
# tests/strategies/optimization/test_objective.py
import pytest
import pandas as pd
import numpy as np
from src.strategies.optimization.optimizers.objective import ObjectiveFunction

def test_objective_function_initialization():
    """Test objective function can be initialized"""
    obj = ObjectiveFunction()
    assert obj is not None
    assert obj.alpha == 0.5  # Default SR weight
    assert obj.beta == 0.3   # Default MDD weight

def test_objective_function_calculate_score():
    """Test calculating optimization score"""
    # Create sample returns
    returns = pd.Series(np.random.randn(252) * 0.02)  # Daily returns

    obj = ObjectiveFunction()
    score = obj.calculate_score(returns)

    assert score is not None
    assert isinstance(score, (int, float))

def test_objective_function_custom_weights():
    """Test objective function with custom weights"""
    obj = ObjectiveFunction(alpha=0.7, beta=0.2, gamma=0.1)

    assert obj.alpha == 0.7
    assert obj.beta == 0.2
    assert obj.gamma == 0.1
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/strategies/optimization/test_objective.py -v`

Expected: FAIL with "cannot import 'ObjectiveFunction'"

**Step 3: Write minimal implementation**

```python
# src/strategies/optimization/optimizers/objective.py
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional

class ObjectiveFunction:
    """
    Objective function for strategy optimization

    Score = α × Sharpe Ratio - β × Max Drawdown + γ × Calmar Ratio
    """

    def __init__(self, alpha: float = 0.5, beta: float = 0.3, gamma: float = 0.2,
                 risk_free_rate: float = 0.02):
        """
        Initialize objective function

        Args:
            alpha: Weight for Sharpe Ratio (default: 0.5)
            beta: Weight for Max Drawdown (default: 0.3)
            gamma: Weight for Calmar Ratio (default: 0.2)
            risk_free_rate: Annual risk-free rate (default: 0.02)
        """
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.risk_free_rate = risk_free_rate

    def calculate_score(self, returns: pd.Series) -> float:
        """
        Calculate composite optimization score

        Args:
            returns: Series of returns (daily or needs annualization)

        Returns:
            Composite score (higher is better)
        """
        # Calculate metrics
        sharpe = self._calculate_sharpe_ratio(returns)
        mdd = self._calculate_max_drawdown(returns)
        calmar = self._calculate_calmar_ratio(returns, mdd)

        # Handle edge cases
        if np.isnan(sharpe) or np.isinf(sharpe):
            sharpe = 0.0
        if np.isnan(mdd) or mdd == 0:
            mdd = 0.0001  # Avoid division by zero
        if np.isnan(calmar) or np.isinf(calmar):
            calmar = 0.0

        # Calculate composite score
        score = (
            self.alpha * sharpe
            - self.beta * abs(mdd)
            + self.gamma * calmar
        )

        return float(score)

    def _calculate_sharpe_ratio(self, returns: pd.Series) -> float:
        """Calculate annualized Sharpe Ratio"""
        if len(returns) < 2:
            return 0.0

        # Annualize (assuming daily returns)
        mean_return = returns.mean() * 252
        std_return = returns.std() * np.sqrt(252)

        if std_return == 0:
            return 0.0

        sharpe = (mean_return - self.risk_free_rate) / std_return
        return sharpe

    def _calculate_max_drawdown(self, returns: pd.Series) -> float:
        """Calculate Maximum Drawdown"""
        if len(returns) < 2:
            return 0.0

        # Calculate cumulative returns
        cumulative = (1 + returns).cumprod()

        # Calculate running maximum
        running_max = cumulative.expanding().max()

        # Calculate drawdown
        drawdown = (cumulative - running_max) / running_max

        # Maximum drawdown
        mdd = drawdown.min()

        return float(mdd)

    def _calculate_calmar_ratio(self, returns: pd.Series,
                               mdd: float = None) -> float:
        """Calculate Calmar Ratio (annual return / abs(max drawdown))"""
        if len(returns) < 2:
            return 0.0

        # Annualized return
        annual_return = (1 + returns.mean()) ** 252 - 1

        # Use provided MDD or calculate
        if mdd is None:
            mdd = self._calculate_max_drawdown(returns)

        if abs(mdd) < 0.0001:  # Avoid division by zero
            return 0.0

        calmar = annual_return / abs(mdd)
        return float(calmar)

    def calculate_metrics(self, returns: pd.Series) -> Dict[str, float]:
        """
        Calculate all individual metrics

        Returns:
            Dictionary with Sharpe, MDD, Calmar, and composite score
        """
        sharpe = self._calculate_sharpe_ratio(returns)
        mdd = self._calculate_max_drawdown(returns)
        calmar = self._calculate_calmar_ratio(returns, mdd)
        score = self.calculate_score(returns)

        return {
            'sharpe_ratio': float(sharpe) if not np.isnan(sharpe) else 0.0,
            'max_drawdown': float(mdd) if not np.isnan(mdd) else 0.0,
            'calmar_ratio': float(calmar) if not np.isnan(calmar) else 0.0,
            'composite_score': float(score) if not np.isnan(score) else 0.0,
            'total_return': float(((1 + returns).prod() - 1)) if not np.isnan(returns.sum()) else 0.0,
            'win_rate': float((returns > 0).sum() / len(returns)) if len(returns) > 0 else 0.0
        }
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/strategies/optimization/test_objective.py -v`

Expected: PASS

**Step 5: Commit**

```bash
git add src/strategies/optimization/optimizers/objective.py tests/strategies/optimization/test_objective.py
git commit -m "feat: implement objective function for optimization"
```

---

### Task 7: 實現貝葉斯優化器

**Files:**
- Create: `src/strategies/optimization/optimizers/bayesian.py`
- Test: `tests/strategies/optimization/test_bayesian_optimizer.py`

**Step 1: Write the failing test**

```python
# tests/strategies/optimization/test_bayesian_optimizer.py
import pytest
import pandas as pd
import numpy as np
from src.strategies.optimization.optimizers.bayesian import BayesianOptimizer

def test_bayesian_optimizer_initialization():
    """Test Bayesian optimizer can be initialized"""
    optimizer = BayesianOptimizer()
    assert optimizer is not None
    assert hasattr(optimizer, 'n_calls')

def test_bayesian_optimize_simple_parameters():
    """Test optimizing simple parameters"""
    # Define search space
    param_space = {
        'ma_short': (5, 20),
        'ma_long': (20, 50)
    }

    # Mock objective function
    def mock_objective(params):
        ma_short = int(params['ma_short'])
        ma_long = int(params['ma_long'])
        # Simple objective: prefer ma_short=10, ma_long=30
        score = -abs(ma_short - 10) - abs(ma_long - 30)
        return score

    optimizer = BayesianOptimizer(n_calls=10)
    best_params, best_score = optimizer.optimize(
        param_space, mock_objective
    )

    assert best_params is not None
    assert 'ma_short' in best_params
    assert 'ma_long' in best_params
    assert best_score is not None
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/strategies/optimization/test_bayesian_optimizer.py -v`

Expected: FAIL with "cannot import 'BayesianOptimizer'"

**Step 3: Write minimal implementation**

```python
# src/strategies/optimization/optimizers/bayesian.py
import numpy as np
from typing import Dict, Callable, Any, Tuple, List
from skopt import gp_minimize
from skopt.space import Real, Integer
from skopt.utils import use_named_args

class BayesianOptimizer:
    """
    Bayesian optimization using Gaussian Process

    Efficiently searches high-dimensional parameter spaces
    for optimal trading strategy parameters.
    """

    def __init__(self, n_calls: int = 50, n_random_starts: int = 10,
                 random_state: int = None):
        """
        Initialize Bayesian optimizer

        Args:
            n_calls: Number of optimization iterations
            n_random_starts: Number of random initial points
            random_state: Random seed for reproducibility
        """
        self.n_calls = n_calls
        self.n_random_starts = n_random_starts
        self.random_state = random_state
        self.optimization_result = None

    def optimize(self, param_space: Dict[str, Tuple],
                 objective_func: Callable) -> Tuple[Dict[str, Any], float]:
        """
        Optimize parameters using Bayesian optimization

        Args:
            param_space: Dictionary of parameter names and ranges
                        e.g., {'ma_short': (5, 20), 'ma_long': (20, 50)}
            objective_func: Function to maximize (takes dict, returns score)

        Returns:
            Tuple of (best_parameters, best_score)
        """
        # Convert parameter space to skopt format
        dimensions = []
        param_names = list(param_space.keys())

        for name in param_names:
            min_val, max_val = param_space[name]

            # Check if parameter should be integer
            if isinstance(min_val, int) and isinstance(max_val, int):
                dimensions.append(Integer(min_val, max_val, name=name))
            else:
                dimensions.append(Real(min_val, max_val, name=name))

        # Define objective wrapper for skopt
        @use_named_args(dimensions=dimensions)
        def objective_wrapper(**params):
            # skopt minimizes, so negate our objective (which we want to maximize)
            score = objective_func(params)
            return -score

        # Run optimization
        result = gp_minimize(
            func=objective_wrapper,
            dimensions=dimensions,
            n_calls=self.n_calls,
            n_initial_points=self.n_random_starts,
            random_state=self.random_state,
            verbose=False
        )

        self.optimization_result = result

        # Extract best parameters
        best_params = dict(zip(param_names, result.x))
        best_score = -result.fun  # Convert back to maximization

        return best_params, float(best_score)

    def get_optimization_history(self) -> Dict[str, List]:
        """
        Get optimization history

        Returns:
            Dictionary with iteration scores and parameters
        """
        if self.optimization_result is None:
            return {'scores': [], 'params': []}

        return {
            'scores': [-float(s) for s in self.optimization_result.func_vals],
            'params': self.optimization_result.x_iters
        }
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/strategies/optimization/test_bayesian_optimizer.py -v`

Expected: PASS

**Step 5: Commit**

```bash
git add src/strategies/optimization/optimizers/bayesian.py tests/strategies/optimization/test_bayesian_optimizer.py
git commit -m "feat: implement Bayesian optimization engine"
```

---

### Task 8: 實現回測引擎

**Files:**
- Create: `src/strategies/optimization/backtest/engine.py`
- Test: `tests/strategies/optimization/test_backtest_engine.py`

**Step 1: Write the failing test**

```python
# tests/strategies/optimization/test_backtest_engine.py
import pytest
import pandas as pd
import numpy as np
from src.strategies.optimization.backtest.engine import BacktestEngine

def test_backtest_engine_initialization():
    """Test backtest engine can be initialized"""
    engine = BacktestEngine()
    assert engine is not None
    assert hasattr(engine, 'commission')

def test_backtest_simple_ma_strategy():
    """Test backtesting simple moving average strategy"""
    # Create sample price data
    np.random.seed(42)
    prices = pd.Series(100 + np.random.randn(100).cumsum())

    engine = BacktestEngine(initial_capital=10000, commission=0.001)

    # Define strategy: simple MA crossover
    def strategy(data):
        if len(data) < 20:
            return 0  # Hold

        short_ma = data['close'].iloc[-5:].mean()
        long_ma = data['close'].iloc[-20:].mean()

        if short_ma > long_ma:
            return 1  # Buy
        elif short_ma < long_ma:
            return -1  # Sell
        else:
            return 0  # Hold

    # Run backtest
    results = engine.run(prices.to_frame('close'), strategy)

    assert results is not None
    assert 'returns' in results
    assert 'total_return' in results
    assert 'sharpe_ratio' in results
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/strategies/optimization/test_backtest_engine.py -v`

Expected: FAIL with "cannot import 'BacktestEngine'"

**Step 3: Write minimal implementation**

```python
# src/strategies/optimization/backtest/engine.py
import pandas as pd
import numpy as np
from typing import Callable, Dict, Any

class BacktestEngine:
    """
    Simple vectorized backtest engine for strategy optimization

    Supports:
    - Single asset backtesting
    - Transaction costs
    - Long/short positions
    """

    def __init__(self, initial_capital: float = 10000,
                 commission: float = 0.001,
                 slippage: float = 0.0001):
        """
        Initialize backtest engine

        Args:
            initial_capital: Starting capital
            commission: Commission rate (default: 0.1%)
            slippage: Slippage per trade (default: 0.01%)
        """
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage

    def run(self, data: pd.DataFrame,
            strategy: Callable) -> Dict[str, Any]:
        """
        Run backtest with given strategy

        Args:
            data: DataFrame with OHLCV data
            strategy: Function that takes data window and returns position (-1, 0, 1)

        Returns:
            Dictionary with backtest results
        """
        # Generate signals
        signals = self._generate_signals(data, strategy)

        # Calculate returns
        returns = self._calculate_returns(data, signals)

        # Calculate metrics
        metrics = self._calculate_metrics(returns, data['close'])

        return metrics

    def _generate_signals(self, data: pd.DataFrame,
                         strategy: Callable) -> pd.Series:
        """Generate trading signals using strategy"""
        signals = pd.Series(0, index=data.index)

        # Rolling window strategy application
        window_size = 50  # Adjust based on strategy needs

        for i in range(window_size, len(data)):
            window = data.iloc[i-window_size:i]
            signal = strategy(window)
            signals.iloc[i] = signal

        return signals

    def _calculate_returns(self, data: pd.DataFrame,
                          signals: pd.Series) -> pd.Series:
        """Calculate returns from signals"""
        # Calculate price returns
        price_returns = data['close'].pct_change()

        # Apply signals with lag (trade at next open)
        position = signals.shift(1)

        # Calculate strategy returns
        strategy_returns = position * price_returns

        # Subtract transaction costs
        trades = position.diff().abs()
        transaction_costs = trades * (self.commission + self.slippage)

        net_returns = strategy_returns - transaction_costs

        return net_returns.fillna(0)

    def _calculate_metrics(self, returns: pd.Series,
                          prices: pd.Series) -> Dict[str, Any]:
        """Calculate backtest performance metrics"""
        # Total return
        total_return = (1 + returns).prod() - 1

        # Annualized return
        n_days = len(returns)
        annual_return = (1 + total_return) ** (252 / n_days) - 1

        # Volatility
        annual_vol = returns.std() * np.sqrt(252)

        # Sharpe Ratio
        risk_free_rate = 0.02
        sharpe_ratio = (annual_return - risk_free_rate) / annual_vol if annual_vol > 0 else 0

        # Maximum Drawdown
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()

        # Calmar Ratio
        calmar_ratio = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0

        # Win Rate
        win_rate = (returns > 0).sum() / len(returns) if len(returns) > 0 else 0

        return {
            'returns': returns,
            'total_return': float(total_return),
            'annual_return': float(annual_return),
            'volatility': float(annual_vol),
            'sharpe_ratio': float(sharpe_ratio),
            'max_drawdown': float(max_drawdown),
            'calmar_ratio': float(calmar_ratio),
            'win_rate': float(win_rate),
            'n_trades': int((returns != 0).sum())
        }
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/strategies/optimization/test_backtest_engine.py -v`

Expected: PASS

**Step 5: Commit**

```bash
git add src/strategies/optimization/backtest/engine.py tests/strategies/optimization/test_backtest_engine.py
git commit -m "feat: implement backtest engine"
```

---

## Phase 3: 策略實現 (4-6週)

### Task 9: 實現趨勢跟蹤策略

**Files:**
- Create: `src/strategies/optimization/strategies/trend_following.py`
- Test: `tests/strategies/optimization/test_trend_following.py`

**Step 1: Write the failing test**

```python
# tests/strategies/optimization/test_trend_following.py
import pytest
import pandas as pd
import numpy as np
from src.strategies.optimization.strategies.trend_following import (
    MAStrategy,
    BollingerBandsStrategy,
    DonchianChannelStrategy
)

def test_ma_strategy_initialization():
    """Test MA strategy can be initialized"""
    strategy = MAStrategy()
    assert strategy is not None
    assert hasattr(strategy, 'generate_signals')

def test_ma_strategy_generate_signals():
    """Test MA crossover signal generation"""
    # Create sample data
    np.random.seed(42)
    data = pd.DataFrame({
        'close': 100 + np.random.randn(100).cumsum()
    })

    strategy = MAStrategy(fast_period=10, slow_period=20)
    signals = strategy.generate_signals(data)

    assert signals is not None
    assert len(signals) == len(data)
    assert signals.dtype == np.int64
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/strategies/optimization/test_trend_following.py -v`

Expected: FAIL with "cannot import"

**Step 3: Write minimal implementation**

```python
# src/strategies/optimization/strategies/trend_following.py
import pandas as pd
import numpy as np
from typing import Dict, Any

class MAStrategy:
    """
    Moving Average Crossover Strategy

    Goes long when fast MA crosses above slow MA
    Goes short when fast MA crosses below slow MA
    """

    def __init__(self, fast_period: int = 10, slow_period: int = 20):
        """
        Initialize MA strategy

        Args:
            fast_period: Fast MA period
            slow_period: Slow MA period
        """
        self.fast_period = fast_period
        self.slow_period = slow_period

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals

        Args:
            data: DataFrame with 'close' column

        Returns:
            Series of signals (-1, 0, 1)
        """
        close = data['close']

        # Calculate moving averages
        fast_ma = close.rolling(window=self.fast_period).mean()
        slow_ma = close.rolling(window=self.slow_period).mean()

        # Generate signals
        signals = pd.Series(0, index=data.index)

        # Long when fast MA > slow MA
        signals[fast_ma > slow_ma] = 1

        # Short when fast MA < slow MA
        signals[fast_ma < slow_ma] = -1

        return signals


class BollingerBandsStrategy:
    """
    Bollinger Bands Breakout Strategy

    Goes long when price breaks above upper band
    Goes short when price breaks below lower band
    """

    def __init__(self, period: int = 20, std_dev: float = 2.0):
        """
        Initialize Bollinger Bands strategy

        Args:
            period: MA period for bands
            std_dev: Number of standard deviations
        """
        self.period = period
        self.std_dev = std_dev

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Generate trading signals based on Bollinger Bands"""
        close = data['close']

        # Calculate bands
        sma = close.rolling(window=self.period).mean()
        std = close.rolling(window=self.period).std()

        upper_band = sma + (std * self.std_dev)
        lower_band = sma - (std * self.std_dev)

        # Generate signals
        signals = pd.Series(0, index=data.index)

        # Long when price breaks above upper band
        signals[close > upper_band] = 1

        # Short when price breaks below lower band
        signals[close < lower_band] = -1

        return signals


class DonchianChannelStrategy:
    """
    Donchian Channel Breakout Strategy

    Goes long when price breaks above N-day high
    Goes short when price breaks below N-day low
    """

    def __init__(self, period: int = 20):
        """
        Initialize Donchian Channel strategy

        Args:
            period: Lookback period for channel
        """
        self.period = period

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Generate trading signals based on Donchian Channel"""
        high = data['high'] if 'high' in data.columns else data['close']
        low = data['low'] if 'low' in data.columns else data['close']
        close = data['close']

        # Calculate channels
        upper_channel = high.rolling(window=self.period).max()
        lower_channel = low.rolling(window=self.period).min()

        # Generate signals
        signals = pd.Series(0, index=data.index)

        # Long when price breaks above upper channel
        signals[close > upper_channel.shift(1)] = 1

        # Short when price breaks below lower channel
        signals[close < lower_channel.shift(1)] = -1

        return signals
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/strategies/optimization/test_trend_following.py -v`

Expected: PASS

**Step 5: Commit**

```bash
git add src/strategies/optimization/strategies/ tests/strategies/optimization/test_trend_following.py
git commit -m "feat: implement trend following strategies"
```

---

### Task 10: 實現均值回歸策略

**Files:**
- Create: `src/strategies/optimization/strategies/mean_reversion.py`
- Test: `tests/strategies/optimization/test_mean_reversion.py`

**Step 1: Write the failing test**

```python
# tests/strategies/optimization/test_mean_reversion.py
import pytest
import pandas as pd
import numpy as np
from src.strategies.optimization.strategies.mean_reversion import (
    RSIMeanReversionStrategy,
    ZScoreStrategy
)

def test_rsi_strategy_initialization():
    """Test RSI mean reversion strategy"""
    strategy = RSIMeanReversionStrategy()
    assert strategy is not None

def test_rsi_strategy_signals():
    """Test RSI signal generation"""
    np.random.seed(42)
    data = pd.DataFrame({
        'close': 100 + np.random.randn(100).cumsum()
    })

    strategy = RSIMeanReversionStrategy(rsi_period=14, oversold=30, overbought=70)
    signals = strategy.generate_signals(data)

    assert signals is not None
    assert len(signals) == len(data)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/strategies/optimization/test_mean_reversion.py -v`

Expected: FAIL with "cannot import"

**Step 3: Write minimal implementation**

```python
# src/strategies/optimization/strategies/mean_reversion.py
import pandas as pd
import numpy as np
from typing import Dict, Any

class RSIMeanReversionStrategy:
    """
    RSI Mean Reversion Strategy

    Buys when RSI is oversold (e.g., < 30)
    Sells when RSI is overbought (e.g., > 70)
    """

    def __init__(self, rsi_period: int = 14,
                 oversold: float = 30,
                 overbought: float = 70):
        """
        Initialize RSI mean reversion strategy

        Args:
            rsi_period: RSI calculation period
            oversold: RSI level considered oversold
            overbought: RSI level considered overbought
        """
        self.rsi_period = rsi_period
        self.oversold = oversold
        self.overbought = overbought

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Generate trading signals based on RSI"""
        close = data['close']

        # Calculate RSI
        rsi = self._calculate_rsi(close, self.rsi_period)

        # Generate signals
        signals = pd.Series(0, index=data.index)

        # Buy when RSI crosses above oversold
        buy_signals = (rsi > self.oversold) & (rsi.shift(1) <= self.oversold)
        signals[buy_signals] = 1

        # Sell when RSI crosses below overbought
        sell_signals = (rsi < self.overbought) & (rsi.shift(1) >= self.overbought)
        signals[sell_signals] = -1

        return signals

    def _calculate_rsi(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        return rsi


class ZScoreStrategy:
    """
    Z-Score Mean Reversion Strategy

    Buys when price is more than N standard deviations below mean
    Sells when price is more than N standard deviations above mean
    """

    def __init__(self, period: int = 20, threshold: float = 2.0):
        """
        Initialize Z-Score strategy

        Args:
            period: Lookback period for mean/std
            threshold: Number of standard deviations for entry
        """
        self.period = period
        self.threshold = threshold

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Generate trading signals based on Z-score"""
        close = data['close']

        # Calculate rolling statistics
        rolling_mean = close.rolling(window=self.period).mean()
        rolling_std = close.rolling(window=self.period).std()

        # Calculate Z-score
        zscore = (close - rolling_mean) / rolling_std

        # Generate signals
        signals = pd.Series(0, index=data.index)

        # Buy when Z-score < -threshold
        signals[zscore < -self.threshold] = 1

        # Sell when Z-score > threshold
        signals[zscore > self.threshold] = -1

        return signals


class PairsTradingStrategy:
    """
    Pairs Trading Strategy (Statistical Arbitrage)

    Trades two correlated assets based on mean reversion of spread
    """

    def __init__(self, entry_threshold: float = 2.0,
                 exit_threshold: float = 0.5,
                 lookback: int = 30):
        """
        Initialize pairs trading strategy

        Args:
            entry_threshold: Z-score for entry
            exit_threshold: Z-score for exit
            lookback: Period for calculating spread statistics
        """
        self.entry_threshold = entry_threshold
        self.exit_threshold = exit_threshold
        self.lookback = lookback

    def generate_signals(self, asset1: pd.Series, asset2: pd.Series,
                        hedge_ratio: float = 1.0) -> pd.Dict[str, pd.Series]:
        """
        Generate pairs trading signals

        Args:
            asset1: Prices of first asset
            asset2: Prices of second asset
            hedge_ratio: Ratio for position sizing

        Returns:
            Dictionary with signals for both assets
        """
        # Calculate spread
        spread = asset1 - hedge_ratio * asset2

        # Calculate Z-score of spread
        spread_mean = spread.rolling(window=self.lookback).mean()
        spread_std = spread.rolling(window=self.lookback).std()
        spread_zscore = (spread - spread_mean) / spread_std

        # Generate signals
        signals_asset1 = pd.Series(0, index=asset1.index)
        signals_asset2 = pd.Series(0, index=asset2.index)

        # Entry: Long spread (long asset1, short asset2)
        long_spread = spread_zscore < -self.entry_threshold
        signals_asset1[long_spread] = 1
        signals_asset2[long_spread] = -1

        # Entry: Short spread (short asset1, long asset2)
        short_spread = spread_zscore > self.entry_threshold
        signals_asset1[short_spread] = -1
        signals_asset2[short_spread] = 1

        # Exit when spread reverts
        exit_signal = spread_zscore.abs() < self.exit_threshold
        signals_asset1[exit_signal] = 0
        signals_asset2[exit_signal] = 0

        return {
            'asset1': signals_asset1,
            'asset2': signals_asset2,
            'spread_zscore': spread_zscore
        }
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/strategies/optimization/test_mean_reversion.py -v`

Expected: PASS

**Step 5: Commit**

```bash
git add src/strategies/optimization/strategies/mean_reversion.py tests/strategies/optimization/test_mean_reversion.py
git commit -m "feat: implement mean reversion strategies"
```

---

## Phase 4: 組合管理與監控 (2-3週)

### Task 11: 實現動態權重分配

**Files:**
- Create: `src/strategies/optimization/portfolio/weights.py`
- Test: `tests/strategies/optimization/test_portfolio_weights.py`

**Step 1: Write the failing test**

```python
# tests/strategies/optimization/test_portfolio_weights.py
import pytest
import pandas as pd
import numpy as np
from src.strategies.optimization.portfolio.weights import (
    EqualWeightAllocator,
    RiskParityAllocator
)

def test_equal_weight_allocator():
    """Test equal weight allocation"""
    allocator = EqualWeightAllocator()

    strategies = ['MA_Crossover', 'RSI_MeanReversion', 'Bollinger_Bands']
    weights = allocator.allocate(strategies)

    assert len(weights) == len(strategies)
    assert all(w == 1/len(strategies) for w in weights.values())
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/strategies/optimization/test_portfolio_weights.py -v`

Expected: FAIL with "cannot import"

**Step 3: Write minimal implementation**

```python
# src/strategies/optimization/portfolio/weights.py
import pandas as pd
import numpy as np
from typing import Dict, List, Optional

class EqualWeightAllocator:
    """Allocate equal weights to all strategies"""

    def allocate(self, strategies: List[str]) -> Dict[str, float]:
        """
        Allocate equal weights

        Args:
            strategies: List of strategy names

        Returns:
            Dictionary mapping strategy names to weights
        """
        n_strategies = len(strategies)
        weight = 1.0 / n_strategies

        return {strategy: weight for strategy in strategies}


class RiskParityAllocator:
    """
    Risk Parity Allocation

    Allocates weights so each strategy contributes equal risk to portfolio
    """

    def __init__(self, target_volatility: float = 0.15):
        """
        Initialize risk parity allocator

        Args:
            target_volatility: Target portfolio volatility
        """
        self.target_volatility = target_volatility

    def allocate(self, strategies: List[str],
                returns: pd.DataFrame) -> Dict[str, float]:
        """
        Allocate weights using risk parity

        Args:
            strategies: List of strategy names
            returns: DataFrame with historical returns for each strategy

        Returns:
            Dictionary mapping strategy names to weights
        """
        # Calculate covariance matrix
        cov_matrix = returns.cov()

        # Calculate volatilities
        volatilities = np.sqrt(np.diag(cov_matrix))

        # Risk parity weights (inverse volatility)
        weights = 1.0 / volatilities
        weights = weights / weights.sum()  # Normalize

        # Scale to target volatility
        portfolio_vol = np.sqrt(weights.T @ cov_matrix @ weights)
        scale_factor = self.target_volatility / portfolio_vol
        weights = weights * scale_factor

        return dict(zip(strategies, weights))


class KellyAllocator:
    """
    Kelly Criterion Allocation

    Maximizes long-term growth rate based on expected returns and variance
    """

    def __init__(self, Kelly_fraction: float = 0.25):
        """
        Initialize Kelly allocator

        Args:
            Kelly_fraction: Fraction of full Kelly to use (for safety)
        """
        self.kelly_fraction = Kelly_fraction

    def allocate(self, strategies: List[str],
                returns: pd.DataFrame) -> Dict[str, float]:
        """
        Allocate weights using Kelly criterion

        Args:
            strategies: List of strategy names
            returns: DataFrame with historical returns

        Returns:
            Dictionary mapping strategy names to weights
        """
        weights = {}

        for strategy in strategies:
            strategy_returns = returns[strategy]

            # Expected return and variance
            mu = strategy_returns.mean()
            sigma2 = strategy_returns.var()

            # Kelly weight (fraction = mu / sigma2)
            if sigma2 > 0:
                kelly_weight = (mu / sigma2) * self.kelly_fraction
                # Cap at 1.0 (no leverage)
                weights[strategy] = max(0, min(kelly_weight, 1.0))
            else:
                weights[strategy] = 0.0

        # Normalize if total exceeds 1.0
        total_weight = sum(weights.values())
        if total_weight > 1.0:
            weights = {k: v / total_weight for k, v in weights.items()}

        return weights
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/strategies/optimization/test_portfolio_weights.py -v`

Expected: PASS

**Step 5: Commit**

```bash
git add src/strategies/optimization/portfolio/ tests/strategies/optimization/test_portfolio_weights.py
git commit -m "feat: implement portfolio weight allocation methods"
```

---

## 依賴安裝說明

在開始實施前，請確保安裝以下依賴：

```bash
# Python packages
pip install yfinance scikit-optimize talib pandas numpy psycopg2-binary influxdb-client

# If TA-Lib installation fails on Windows:
pip install ta-lib  # May need pre-compiled wheel
```

---

## 總結

本計劃涵蓋了量化策略優化系統的完整實施：

**Phase 1: 數據層 (Tasks 1-5)**
- 項目結構和 Yahoo Finance 數據獲取
- HKEX 數據整合
- PostgreSQL 數據存儲
- TA-Lib 技術指標
- 完整特徵工程管道

**Phase 2: 優化引擎 (Tasks 6-8)**
- SR/MDD 綜合目標函數
- 貝葉斯優化器
- 向量化回測引擎

**Phase 3: 策略實現 (Tasks 9-10)**
- 趨勢跟蹤策略（MA, 布林帶, 唐奇安通道）
- 均值回歸策略（RSI, Z-Score, 配對交易）

**Phase 4: 組合管理 (Task 11)**
- 動態權重分配（等權, 風險平價, Kelly）

**總計: 11 個核心任務，預計 11-16 週完成**
