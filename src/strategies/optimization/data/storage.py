"""Data storage layer using PostgreSQL and InfluxDB"""
import logging
import pandas as pd
from typing import Optional
from datetime import datetime

try:
    import psycopg2
    from psycopg2.extras import execute_values
    from psycopg2 import sql
    HAS_POSTGRES = True
except ImportError:
    HAS_POSTGRES = False

logger = logging.getLogger(__name__)


class DataStorage:
    """Store and retrieve market data using PostgreSQL and InfluxDB"""

    # Whitelist of allowed timeframes to prevent SQL injection
    ALLOWED_TIMEFRAMES = {'minute', 'daily', 'weekly'}

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
        if not HAS_POSTGRES:
            logger.warning("psycopg2 not installed, PostgreSQL features disabled")
            return

        try:
            self.postgres_conn = psycopg2.connect(**self.postgres_config)
            logger.info("Connected to PostgreSQL successfully")
        except Exception as e:
            logger.warning(f"Could not connect to PostgreSQL: {e}")
            self.postgres_conn = None

    def _validate_timeframe(self, timeframe: str) -> bool:
        """
        Validate timeframe parameter to prevent SQL injection

        Args:
            timeframe: Timeframe string to validate

        Returns:
            True if valid, False otherwise
        """
        if timeframe not in self.ALLOWED_TIMEFRAMES:
            logger.error(f"Invalid timeframe: '{timeframe}'. Must be one of {self.ALLOWED_TIMEFRAMES}")
            return False
        return True

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
            logger.error("No PostgreSQL connection available")
            return False

        if not HAS_POSTGRES:
            logger.error("psycopg2 not available")
            return False

        # Validate timeframe to prevent SQL injection
        if not self._validate_timeframe(timeframe):
            return False

        try:
            cursor = self.postgres_conn.cursor()

            # Create table if not exists using safe SQL construction
            table_name = sql.Identifier("market_data", timeframe)
            cursor.execute(sql.SQL("""
                CREATE TABLE IF NOT EXISTS {} (
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
            """).format(table_name))

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
                sql.SQL("""
                INSERT INTO {} (symbol, date, open, high, low, close, volume)
                VALUES %s
                ON CONFLICT (symbol, date) DO UPDATE
                SET open = EXCLUDED.open, high = EXCLUDED.high,
                    low = EXCLUDED.low, close = EXCLUDED.close, volume = EXCLUDED.volume
                """).format(table_name),
                values
            )

            self.postgres_conn.commit()
            cursor.close()

            logger.info(f"Saved {len(values)} records for {symbol} to market_data_{timeframe}")
            return True

        except Exception as e:
            logger.error(f"Error saving data: {e}")
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
            logger.error("No PostgreSQL connection available")
            return None

        if not HAS_POSTGRES:
            logger.error("psycopg2 not available")
            return None

        # Validate timeframe to prevent SQL injection
        if not self._validate_timeframe(timeframe):
            return None

        try:
            cursor = self.postgres_conn.cursor()

            # Build query using safe SQL construction
            table_name = sql.Identifier("market_data", timeframe)
            query = sql.SQL("""
                SELECT date, open, high, low, close, volume
                FROM {}
                WHERE symbol = %s
            """).format(table_name)

            params = [symbol]

            if start_date:
                query = sql.SQL("{query} AND date >= %s").format(query=query)
                params.append(start_date)

            if end_date:
                query = sql.SQL("{query} AND date <= %s").format(query=query)
                params.append(end_date)

            query = sql.SQL("{query} ORDER BY date ASC").format(query=query)

            cursor.execute(query, params)
            rows = cursor.fetchall()
            cursor.close()

            if not rows:
                logger.warning(f"No data found for {symbol} in market_data_{timeframe}")
                return None

            df = pd.DataFrame(rows, columns=['date', 'open', 'high', 'low', 'close', 'volume'])
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)

            logger.info(f"Retrieved {len(df)} records for {symbol} from market_data_{timeframe}")
            return df

        except Exception as e:
            logger.error(f"Error retrieving data: {e}")
            return None

    def __del__(self):
        """Close database connection on delete"""
        if self.postgres_conn:
            try:
                self.postgres_conn.close()
                logger.debug("PostgreSQL connection closed")
            except Exception as e:
                logger.error(f"Error closing connection: {e}")
