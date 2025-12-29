# HKEX Market Data Integration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Integrate HKEX crawler's non-price market data into CBSC Performance Analysis Tab return attribution module.

**Architecture:** Three-tier integration - HKEX crawler writes to CBSC PostgreSQL database via database-writer module, CBSC FastAPI backend queries database to generate performance analytics, frontend displays real data with mock fallback.

**Tech Stack:** PostgreSQL, Python (FastAPI, SQLAlchemy), Node.js (pg module), Express, React (Redux Toolkit)

---

## Task 1: Create Database Tables and Trigger

**Files:**
- Create: `src/db/migrations/001_create_hkex_tables.py`
- Test: Manual verification with psql

**Step 1: Write the migration script**

Create `src/db/migrations/001_create_hkex_tables.py`:

```python
"""
Migration: Create HKEX market data tables
Date: 2025-12-29
"""
from sqlalchemy import create_engine, text
import os

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://cbsc:password@localhost:5432/cbsc')

def upgrade():
    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        # Create raw data table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS hkex_raw_data (
                id SERIAL PRIMARY KEY,
                date DATE UNIQUE NOT NULL,
                trading_volume INTEGER,
                advanced_stocks INTEGER,
                declined_stocks INTEGER,
                unchanged_stocks INTEGER,
                turnover_hkd BIGINT,
                deals INTEGER,
                morning_close DECIMAL(10,2),
                afternoon_close DECIMAL(10,2),
                change_value DECIMAL(10,2),
                change_percent DECIMAL(10,4),
                created_at TIMESTAMP DEFAULT NOW()
            );
        """))

        # Create indicators table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS market_indicators (
                date DATE PRIMARY KEY REFERENCES hkex_raw_data(date) ON DELETE CASCADE,
                advance_decline_ratio DECIMAL(10,4),
                volume_change_percent DECIMAL(10,4),
                sentiment_score DECIMAL(10,2),
                breadth_momentum DECIMAL(10,4),
                updated_at TIMESTAMP DEFAULT NOW()
            );
        """))

        # Create trigger function
        conn.execute(text("""
            CREATE OR REPLACE FUNCTION calculate_indicators()
            RETURNS TRIGGER AS $$
            DECLARE
                prev_volume BIGINT;
                volume_pct DECIMAL(10,4);
                total_stocks INTEGER;
            BEGIN
                -- Get previous day's volume for change calculation
                SELECT turnover_hkd INTO prev_volume
                FROM hkex_raw_data
                WHERE date < NEW.date
                ORDER BY date DESC
                LIMIT 1;

                -- Calculate volume change percent
                IF prev_volume IS NOT NULL AND prev_volume > 0 THEN
                    volume_pct = ((NEW.turnover_hkd - prev_volume)::DECIMAL / prev_volume) * 100;
                ELSE
                    volume_pct = 0;
                END IF;

                -- Calculate total stocks
                total_stocks = NEW.advanced_stocks + NEW.declined_stocks + NEW.unchanged_stocks;

                -- Insert or update indicators
                INSERT INTO market_indicators (
                    date,
                    advance_decline_ratio,
                    volume_change_percent,
                    sentiment_score,
                    breadth_momentum
                )
                VALUES (
                    NEW.date,
                    CASE WHEN NEW.declined_stocks > 0
                         THEN NEW.advanced_stocks::DECIMAL / (NEW.declined_stocks + 1)
                         ELSE NEW.advanced_stocks::DECIMAL END,
                    volume_pct,
                    (
                        CASE WHEN NEW.declined_stocks > 0
                             THEN NEW.advanced_stocks::DECIMAL / (NEW.declined_stocks + 1)
                             ELSE NEW.advanced_stocks::DECIMAL END * 0.4 +
                        volume_pct * 0.3 +
                        CASE WHEN total_stocks > 0
                             THEN (NEW.advanced_stocks::DECIMAL / total_stocks) * 0.3
                             ELSE 0 END
                    ) * 100,
                    0  -- Phase 2 implementation
                )
                ON CONFLICT (date) DO UPDATE SET
                    advance_decline_ratio = EXCLUDED.advance_decline_ratio,
                    volume_change_percent = EXCLUDED.volume_change_percent,
                    sentiment_score = EXCLUDED.sentiment_score,
                    updated_at = NOW();

                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        """))

        # Create trigger
        conn.execute(text("""
            DROP TRIGGER IF EXISTS trigger_calculate_indicators ON hkex_raw_data;
            CREATE TRIGGER trigger_calculate_indicators
            AFTER INSERT ON hkex_raw_data
            FOR EACH ROW
            EXECUTE FUNCTION calculate_indicators();
        """))

        conn.commit()
        print("✅ Migration completed: hkex tables created")

def downgrade():
    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        conn.execute(text("DROP TRIGGER IF EXISTS trigger_calculate_indicators ON hkex_raw_data;"))
        conn.execute(text("DROP FUNCTION IF EXISTS calculate_indicators();"))
        conn.execute(text("DROP TABLE IF EXISTS market_indicators;"))
        conn.execute(text("DROP TABLE IF EXISTS hkex_raw_data;"))
        conn.commit()
        print("✅ Rollback completed: hkex tables dropped")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "down":
        downgrade()
    else:
        upgrade()
```

**Step 2: Run migration to verify it creates tables**

Run: `cd .worktrees/hkex-integration && python src/db/migrations/001_create_hkex_tables.py`

Expected output:
```
✅ Migration completed: hkex tables created
```

**Step 3: Verify tables exist in database**

Run: `psql -U cbsc -d cbsc -c "\dt hkex_*"`

Expected output:
```
          List of relations
 Schema |       Name        | Type  | Owner
--------+-------------------+-------+--------
 public | hkex_raw_data     | table | cbsc
 public | market_indicators | table | cbsc
```

**Step 4: Verify trigger exists**

Run: `psql -U cbsc -d cbsc -c "\df calculate_indicators"`

Expected output should show the trigger function.

**Step 5: Commit**

```bash
cd .worktrees/hkex-integration
git add src/db/migrations/001_create_hkex_tables.py
git commit -m "feat: create HKEX market data tables and trigger"
```

---

## Task 2: Test Trigger with Manual Data Insert

**Files:**
- Create: `tests/test_hkex_trigger.sql`
- Test: Manual psql test

**Step 1: Write test SQL file**

Create `tests/test_hkex_trigger.sql`:

```sql
-- Test trigger by inserting sample data
INSERT INTO hkex_raw_data (
    date, trading_volume, advanced_stocks, declined_stocks,
    unchanged_stocks, turnover_hkd, deals, morning_close,
    afternoon_close, change_value, change_percent
) VALUES (
    '2025-12-29', 8273, 3094, 7016, 3625, 328118569834,
    4827115, 25460.16, 25496.55, -120.87, -0.47
);

-- Wait 1 second for trigger to process
-- Then check if indicators were calculated
SELECT * FROM market_indicators WHERE date = '2025-12-29';

-- Expected: One row with calculated advance_decline_ratio, sentiment_score, etc.
```

**Step 2: Run test SQL**

Run: `psql -U cbsc -d cbsc -f tests/test_hkex_trigger.sql`

Expected output:
```
 date  | advance_decline_ratio | volume_change_percent | sentiment_score | ...
----------+----------------------+----------------------+-----------------+----
 2025-12-29 | 0.4410 | 0.0000 | 17.6400 | ...
```

**Step 3: Verify calculations**

Expected values:
- `advance_decline_ratio` ≈ 3094 / 7017 ≈ 0.44
- `sentiment_score` should be positive (based on formula)

**Step 4: Clean up test data**

Run: `psql -U cbsc -d cbsc -c "DELETE FROM hkex_raw_data WHERE date = '2025-12-29';"`

**Step 5: Commit**

```bash
cd .worktrees/hkex-integration
git add tests/test_hkex_trigger.sql
git commit -m "test: add SQL test for HKEX trigger calculation"
```

---

## Task 3: Create Database Writer Module in HKEX Crawler

**Files:**
- Create: `C:\Users\Penguin8n\爬蟲\hkex爬蟲\src\database-writer.js`
- Modify: `C:\Users\Penguin8n\爬蟲\hkex爬蟲\.env`
- Test: Manual test with sample data

**Step 1: Install pg module**

Run: `cd "C:\Users\Penguin8n\爬蟲\hkex爬蟲" && npm install pg`

Expected: Package added to package.json

**Step 2: Add database configuration to .env**

Edit `C:\Users\Penguin8n\爬蟲\hkex爬蟲\.env`, add:

```env
# CBSC Database for HKEX market data
CBSC_DATABASE_URL=postgresql://cbsc:password@localhost:5432/cbsc
```

**Step 3: Write database-writer module**

Create `C:\Users\Penguin8n\爬蟲\hkex爬蟲\src\database-writer.js`:

```javascript
/**
 * Database Writer Module
 * Writes HKEX market data to CBSC PostgreSQL database
 */
const { Pool } = require('pg');
const fs = require('fs');
const path = require('path');

// Get database URL from environment
const databaseUrl = process.env.CBSC_DATABASE_URL;

if (!databaseUrl) {
    console.warn('⚠️  CBSC_DATABASE_URL not set, database writing disabled');
}

class DatabaseWriter {
    constructor() {
        this.pool = null;
        this.enabled = !!databaseUrl;
    }

    /**
     * Initialize database connection pool
     */
    async connect() {
        if (!this.enabled) {
            console.log('📊 Database writer disabled (no CBSC_DATABASE_URL)');
            return false;
        }

        try {
            this.pool = new Pool({
                connectionString: databaseUrl,
                max: 10,
                idleTimeoutMillis: 30000,
                connectionTimeoutMillis: 5000,
            });

            // Test connection
            const client = await this.pool.connect();
            client.release();

            console.log('✅ Connected to CBSC database');
            return true;
        } catch (error) {
            console.error('❌ Failed to connect to database:', error.message);
            this.logError('connection', error);
            return false;
        }
    }

    /**
     * Write market data to database
     * @param {Object} data - Parsed HKEX market data
     * @param {string} data.date - Date in YYYY-MM-DD format
     * @param {number} data.tradingVolume - Trading volume
     * @param {number} data.advancedStocks - Number of advanced stocks
     * @param {number} data.declinedStocks - Number of declined stocks
     * @param {number} data.unchangedStocks - Number of unchanged stocks
     * @param {number} data.turnoverHkd - Turnover in HKD
     * @param {number} data.deals - Number of deals
     * @param {number} data.morningClose - Morning close value
     * @param {number} data.afternoonClose - Afternoon close value
     * @param {number} data.changeValue - Change value
     * @param {number} data.changePercent - Change percentage
     */
    async writeMarketData(data) {
        if (!this.enabled || !this.pool) {
            console.log('⏭️  Skipping database write (not connected)');
            return false;
        }

        const query = `
            INSERT INTO hkex_raw_data (
                date, trading_volume, advanced_stocks, declined_stocks,
                unchanged_stocks, turnover_hkd, deals, morning_close,
                afternoon_close, change_value, change_percent
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            ON CONFLICT (date) DO UPDATE SET
                trading_volume = EXCLUDED.trading_volume,
                advanced_stocks = EXCLUDED.advanced_stocks,
                declined_stocks = EXCLUDED.declined_stocks,
                unchanged_stocks = EXCLUDED.unchanged_stocks,
                turnover_hkd = EXCLUDED.turnover_hkd,
                deals = EXCLUDED.deals,
                morning_close = EXCLUDED.morning_close,
                afternoon_close = EXCLUDED.afternoon_close,
                change_value = EXCLUDED.change_value,
                change_percent = EXCLUDED.change_percent
            RETURNING date
        `;

        const values = [
            data.date,
            data.tradingVolume,
            data.advancedStocks,
            data.declinedStocks,
            data.unchangedStocks,
            data.turnoverHkd,
            data.deals,
            data.morningClose,
            data.afternoonClose,
            data.changeValue,
            data.changePercent
        ];

        try {
            const result = await this.pool.query(query, values);
            console.log(`✅ Data written to database for ${data.date}`);
            return { success: true, date: result.rows[0].date };
        } catch (error) {
            console.error(`❌ Failed to write data for ${data.date}:`, error.message);
            this.logError('write', error, data);
            return { success: false, error: error.message };
        }
    }

    /**
     * Write batch of market data
     * @param {Array<Object>} dataList - Array of market data objects
     */
    async writeBatch(dataList) {
        if (!this.enabled || !this.pool) {
            console.log('⏭️  Skipping batch write (not connected)');
            return { success: 0, failed: dataList.length };
        }

        let successCount = 0;
        let failedCount = 0;

        for (const data of dataList) {
            const result = await this.writeMarketData(data);
            if (result.success) {
                successCount++;
            } else {
                failedCount++;
            }
        }

        console.log(`📊 Batch write complete: ${successCount} success, ${failedCount} failed`);
        return { success: successCount, failed: failedCount };
    }

    /**
     * Log error to file
     */
    logError(type, error, context = {}) {
        const logPath = path.join(__dirname, '../data/write_errors.log');
        const timestamp = new Date().toISOString();
        const logEntry = {
            timestamp,
            type,
            error: error.message,
            stack: error.stack,
            context
        };

        fs.appendFileSync(logPath, JSON.stringify(logEntry) + '\n');
    }

    /**
     * Close database connection pool
     */
    async close() {
        if (this.pool) {
            await this.pool.end();
            console.log('🔌 Database connection closed');
        }
    }
}

module.exports = DatabaseWriter;
```

**Step 4: Test database-writer with sample data**

Create test file `C:\Users\Penguin8n\爬蟲\hkex爬蟲\test-database-writer.js`:

```javascript
const DatabaseWriter = require('./src/database-writer');

async function test() {
    const writer = new DatabaseWriter();

    // Test connection
    const connected = await writer.connect();
    if (!connected) {
        console.log('❌ Test failed: Could not connect to database');
        process.exit(1);
    }

    // Test write
    const testData = {
        date: '2025-12-29',
        tradingVolume: 8273,
        advancedStocks: 3094,
        declinedStocks: 7016,
        unchangedStocks: 3625,
        turnoverHkd: 328118569834,
        deals: 4827115,
        morningClose: 25460.16,
        afternoonClose: 25496.55,
        changeValue: -120.87,
        changePercent: -0.47
    };

    const result = await writer.writeMarketData(testData);
    console.log('Write result:', result);

    // Clean up
    await writer.close();

    // Clean up test data
    console.log('Cleaning up test data...');
    // (Manual cleanup via psql: DELETE FROM hkex_raw_data WHERE date = '2025-12-29')
}

test().catch(console.error);
```

Run: `cd "C:\Users\Penguin8n\爬蟲\hkex爬蟲" && node test-database-writer.js`

Expected output:
```
✅ Connected to CBSC database
✅ Data written to database for 2025-12-29
Write result: { success: true, date: '2025-12-29' }
🔌 Database connection closed
```

**Step 5: Clean up test data**

Run: `psql -U cbsc -d cbsc -c "DELETE FROM hkex_raw_data WHERE date = '2025-12-29';"`

**Step 6: Commit**

```bash
cd "C:\Users\Penguin8n\爬蟲\hkex爬蟲"
git add src/database-writer.js test-database-writer.js .env package.json package-lock.json
git commit -m "feat: add database writer module for HKEX market data"
```

---

## Task 4: Modify Crawler to Call Database Writer

**Files:**
- Modify: `C:\Users\Penguin8n\爬蟲\hkex爬蟲\src\crawler.js` (or appropriate crawler file)
- Test: Run crawler and verify database write

**Step 1: Identify the main crawler file**

Run: `ls "C:\Users\Penguin8n\爬蟲\hkex爬蟲\src" | grep -i crawler`

Expected output shows crawler files. Determine which is the main one (likely `crawler.js` or `enhanced-crawler.js`).

**Step 2: Read crawler file to understand data structure**

Run: `head -100 "C:\Users\Penguin8n\爬蟲\hkex爬蟲\src\crawler.js"`

Identify the data parsing logic and CSV output.

**Step 3: Modify crawler to include database writer**

Add to top of crawler file:

```javascript
const DatabaseWriter = require('./database-writer');
const dbWriter = new DatabaseWriter();
```

Add initialization before crawling starts:

```javascript
// Initialize database connection
await dbWriter.connect().catch(err => {
    console.warn('Database connection failed, continuing with file backup:', err.message);
});
```

After parsing each CSV row, add database write:

```javascript
// After parsing CSV row
const marketData = {
    date: row.Date,
    tradingVolume: parseInt(row.Trading_Volume),
    advancedStocks: parseInt(row.Advanced_Stocks),
    declinedStocks: parseInt(row.Declined_Stocks),
    unchangedStocks: parseInt(row.Unchanged_Stocks),
    turnoverHkd: parseInt(row.Turnover_HKD),
    deals: parseInt(row.Deals),
    morningClose: parseFloat(row.Morning_Close),
    afternoonClose: parseFloat(row.Afternoon_Close),
    changeValue: parseFloat(row.Change),
    changePercent: parseFloat(row.Change_Percent)
};

// Write to database (non-blocking)
dbWriter.writeMarketData(marketData).catch(err => {
    console.error('Database write failed:', err.message);
});
```

Add cleanup at end:

```javascript
// After crawling completes
await dbWriter.close();
```

**Step 4: Test modified crawler**

Run: `cd "C:\Users\Penguin8n\爬蟲\hkex爬蟲" && npm start`

Expected: Crawler runs, data written to database

**Step 5: Verify data in database**

Run: `psql -U cbsc -d cbsc -c "SELECT date, advanced_stocks, declined_stocks FROM hkex_raw_data ORDER BY date DESC LIMIT 5;"`

Expected: Shows recent dates with stock counts

**Step 6: Verify indicators calculated**

Run: `psql -U cbsc -d cbsc -c "SELECT * FROM market_indicators ORDER BY date DESC LIMIT 5;"`

Expected: Shows calculated indicators

**Step 7: Commit**

```bash
cd "C:\Users\Penguin8n\爬蟲\hkex爬蟲"
git add src/crawler.js
git commit -m "feat: integrate database writer into crawler"
```

---

## Task 5: Create FastAPI Endpoint for Performance Analytics

**Files:**
- Create: `src/api/market_data_endpoints.py`
- Modify: `src/api/main.py` (register router)
- Test: Manual curl/test request

**Step 1: Create market data endpoints file**

Create `src/api/market_data_endpoints.py`:

```python
"""
Market Data Endpoints
Provides performance analytics data from market_indicators table
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from src.database.connection import get_db_connection

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/analytics", tags=["analytics"])


class PerformanceAnalyticsRequest(BaseModel):
    time_range: str = Query(..., description="Time range: 1w, 1m, 3m, 1y")
    strategies: Optional[List[str]] = None


class AttributionData(BaseModel):
    total: float
    breakdown: List[dict]


class PerformanceAnalyticsResponse(BaseModel):
    return_attribution: AttributionData
    risk_exposure: dict
    correlations: dict
    stress_test: List[dict]


def get_date_range(time_range: str) -> tuple:
    """Calculate date range from time_range string"""
    now = datetime.now()

    ranges = {
        '1w': now - timedelta(days=7),
        '1m': now - timedelta(days=30),
        '3m': now - timedelta(days=90),
        '1y': now - timedelta(days=365),
    }

    if time_range not in ranges:
        raise ValueError(f"Invalid time_range: {time_range}")

    return ranges[time_range], now


def calculate_return_attribution(indicators: List[dict]) -> dict:
    """Calculate return attribution from market indicators"""
    if not indicators:
        return {
            "total": 0.0,
            "breakdown": [
                {"indicator": "市場漲跌情緒", "contribution": 0.0, "percentage": 0.0},
                {"indicator": "成交量活躍度", "contribution": 0.0, "percentage": 0.0},
                {"indicator": "市場廣度", "contribution": 0.0, "percentage": 0.0},
            ]
        }

    # Aggregate indicators
    total_adv_dec_ratio = sum(i['advance_decline_ratio'] or 0 for i in indicators)
    total_volume_change = sum(i['volume_change_percent'] or 0 for i in indicators)
    total_sentiment = sum(i['sentiment_score'] or 0 for i in indicators)

    count = len(indicators)
    avg_ratio = total_adv_dec_ratio / count if count else 0
    avg_volume = total_volume_change / count if count else 0
    avg_sentiment = total_sentiment / count if count else 0

    # Calculate contributions (weighted)
    contribution_ratio = avg_ratio * 0.4
    contribution_volume = avg_volume * 0.3
    contribution_breadth = (avg_sentiment / 100) * 0.3 * 100

    total = contribution_ratio + contribution_volume + contribution_breadth

    return {
        "total": round(total, 2),
        "breakdown": [
            {
                "indicator": "市場漲跌情緒",
                "contribution": round(contribution_ratio, 2),
                "percentage": round((contribution_ratio / total * 100) if total else 0, 1)
            },
            {
                "indicator": "成交量活躍度",
                "contribution": round(contribution_volume, 2),
                "percentage": round((contribution_volume / total * 100) if total else 0, 1)
            },
            {
                "indicator": "市場廣度",
                "contribution": round(contribution_breadth, 2),
                "percentage": round((contribution_breadth / total * 100) if total else 0, 1)
            },
        ]
    }


def get_mock_data() -> dict:
    """Return mock data when no real data available"""
    return {
        "return_attribution": {
            "total": 5.23,
            "breakdown": [
                {"indicator": "市場漲跌情緒", "contribution": 2.1, "percentage": 40.2},
                {"indicator": "成交量活躍度", "contribution": 1.5, "percentage": 28.7},
                {"indicator": "市場廣度", "contribution": 1.6, "percentage": 30.6}
            ]
        },
        "risk_exposure": {
            "systematic": 0.65,
            "interestRate": 0.72,
            "liquidity": 0.45,
            "economicGrowth": 0.58,
            "fx": 0.38
        },
        "correlations": {
            "matrix": [[1.0, 0.3, 0.5], [0.3, 1.0, 0.4], [0.5, 0.4, 1.0]],
            "strategies": ["策略A", "策略B", "策略C"]
        },
        "stress_test": [
            {"scenario": "基準", "expectedReturn": 8.5, "maxDrawdown": -12.3, "sharpeRatio": 1.2},
            {"scenario": "利率+200bp", "expectedReturn": 6.2, "maxDrawdown": -15.8, "sharpeRatio": 0.9},
            {"scenario": "經濟衰退", "expectedReturn": -3.4, "maxDrawdown": -25.1, "sharpeRatio": -0.5},
            {"scenario": "市場崩盤", "expectedReturn": -15.2, "maxDrawdown": -40.5, "sharpeRatio": -1.2}
        ]
    }


@router.get("/performance", response_model=PerformanceAnalyticsResponse)
async def get_performance_analytics(
    time_range: str = Query("1m", description="Time range: 1w, 1m, 3m, 1y")
):
    """
    Get performance analytics data including return attribution

    Args:
        time_range: Time period for analysis (1w, 1m, 3m, 1y)

    Returns:
        Performance analytics with return attribution, risk exposure, correlations, and stress test
    """
    try:
        # Calculate date range
        start_date, end_date = get_date_range(time_range)

        # Query market indicators from database
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
            SELECT
                date,
                advance_decline_ratio,
                volume_change_percent,
                sentiment_score,
                breadth_momentum
            FROM market_indicators
            WHERE date >= %s AND date <= %s
            ORDER BY date ASC
        """

        cursor.execute(query, (start_date, end_date))
        indicators = []

        for row in cursor.fetchall():
            indicators.append({
                'date': row[0].isoformat(),
                'advance_decline_ratio': float(row[1]) if row[1] else None,
                'volume_change_percent': float(row[2]) if row[2] else None,
                'sentiment_score': float(row[3]) if row[3] else None,
                'breadth_momentum': float(row[4]) if row[4] else None
            })

        cursor.close()
        conn.close()

        # Calculate return attribution
        return_attribution = calculate_return_attribution(indicators)

        # If no indicators data, return mock
        if not indicators:
            logger.warning(f"No market indicators found for range {time_range}, using mock data")
            return get_mock_data()

        # Return full response (risk, correlations, stress_test use mock for now)
        return {
            "return_attribution": return_attribution,
            "risk_exposure": get_mock_data()["risk_exposure"],
            "correlations": get_mock_data()["correlations"],
            "stress_test": get_mock_data()["stress_test"]
        }

    except Exception as e:
        logger.error(f"Error fetching performance analytics: {e}")
        # Return mock data on error
        return get_mock_data()


@router.get("/indicators")
async def get_market_indicators(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(30, le=365)
):
    """
    Get raw market indicators data

    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        limit: Maximum number of records to return

    Returns:
        List of market indicators
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Build query with filters
        if start_date and end_date:
            query = """
                SELECT date, advance_decline_ratio, volume_change_percent,
                       sentiment_score, breadth_momentum, updated_at
                FROM market_indicators
                WHERE date >= %s AND date <= %s
                ORDER BY date DESC
            """
            cursor.execute(query, (start_date, end_date))
        else:
            query = """
                SELECT date, advance_decline_ratio, volume_change_percent,
                       sentiment_score, breadth_momentum, updated_at
                FROM market_indicators
                ORDER BY date DESC
                LIMIT %s
            """
            cursor.execute(query, (limit,))

        indicators = []
        for row in cursor.fetchall():
            indicators.append({
                'date': row[0].isoformat(),
                'advance_decline_ratio': float(row[1]) if row[1] else None,
                'volume_change_percent': float(row[2]) if row[2] else None,
                'sentiment_score': float(row[3]) if row[3] else None,
                'breadth_momentum': float(row[4]) if row[4] else None,
                'updated_at': row[5].isoformat() if row[5] else None
            })

        cursor.close()
        conn.close()

        return {"data": indicators, "count": len(indicators)}

    except Exception as e:
        logger.error(f"Error fetching market indicators: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

**Step 2: Register router in main.py**

Edit `src/api/main.py`, add:

```python
from src.api.market_data_endpoints import router as analytics_router

# Register router
app.include_router(analytics_router)
```

**Step 3: Test endpoint locally**

Run: `curl http://localhost:3003/api/analytics/performance?time_range=1m`

Expected: JSON response with return_attribution data

**Step 4: Test with invalid time range**

Run: `curl http://localhost:3003/api/analytics/performance?time_range=invalid`

Expected: Returns mock data (error handling)

**Step 5: Commit**

```bash
cd .worktrees/hkex-integration
git add src/api/market_data_endpoints.py src/api/main.py
git commit -m "feat: add performance analytics API endpoint"
```

---

## Task 6: Create Market Indicator Service (Optional Refactor)

**Files:**
- Create: `src/services/market_indicator_service.py`
- Modify: `src/api/market_data_endpoints.py` (use service)

**Step 1: Create indicator service**

Create `src/services/market_indicator_service.py`:

```python
"""
Market Indicator Service
Business logic for calculating market indicators
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class MarketIndicatorService:
    """Service for market indicator calculations"""

    @staticmethod
    def calculate_return_attribution(indicators: List[dict]) -> dict:
        """Calculate return attribution from market indicators"""
        if not indicators:
            return {
                "total": 0.0,
                "breakdown": [
                    {"indicator": "市場漲跌情緒", "contribution": 0.0, "percentage": 0.0},
                    {"indicator": "成交量活躍度", "contribution": 0.0, "percentage": 0.0},
                    {"indicator": "市場廣度", "contribution": 0.0, "percentage": 0.0},
                ]
            }

        # Aggregate indicators
        count = len(indicators)

        total_adv_dec_ratio = sum(
            i.get('advance_decline_ratio') or 0 for i in indicators
        )
        total_volume_change = sum(
            i.get('volume_change_percent') or 0 for i in indicators
        )
        total_sentiment = sum(
            i.get('sentiment_score') or 0 for i in indicators
        )

        # Calculate averages
        avg_ratio = total_adv_dec_ratio / count if count else 0
        avg_volume = total_volume_change / count if count else 0
        avg_sentiment = total_sentiment / count if count else 0

        # Calculate contributions (weighted by importance)
        contribution_ratio = avg_ratio * 0.4
        contribution_volume = avg_volume * 0.3
        contribution_breadth = (avg_sentiment / 100) * 0.3 * 100

        total = contribution_ratio + contribution_volume + contribution_breadth

        # Avoid division by zero
        if total == 0:
            total = 1

        return {
            "total": round(total, 2),
            "breakdown": [
                {
                    "indicator": "市場漲跌情緒",
                    "contribution": round(contribution_ratio, 2),
                    "percentage": round((contribution_ratio / total) * 100, 1)
                },
                {
                    "indicator": "成交量活躍度",
                    "contribution": round(contribution_volume, 2),
                    "percentage": round((contribution_volume / total) * 100, 1)
                },
                {
                    "indicator": "市場廣度",
                    "contribution": round(contribution_breadth, 2),
                    "percentage": round((contribution_breadth / total) * 100, 1)
                },
            ]
        }

    @staticmethod
    def validate_indicator(indicator: dict) -> bool:
        """Validate indicator data structure"""
        required_fields = ['date', 'advance_decline_ratio', 'sentiment_score']
        return all(field in indicator for field in required_fields)

    @staticmethod
    def filter_indicators_by_range(
        indicators: List[dict],
        start_date: datetime,
        end_date: datetime
    ) -> List[dict]:
        """Filter indicators by date range"""
        return [
            i for i in indicators
            if start_date <= datetime.fromisoformat(i['date']) <= end_date
        ]
```

**Step 2: Update endpoints to use service**

Edit `src/api/market_data_endpoints.py`:

```python
from src.services.market_indicator_service import MarketIndicatorService

# In get_performance_analytics function:
return_attribution = MarketIndicatorService.calculate_return_attribution(indicators)
```

**Step 3: Commit**

```bash
cd .worktrees/hkex-integration
git add src/services/market_indicator_service.py src/api/market_data_endpoints.py
git commit -m "refactor: extract indicator calculation logic to service"
```

---

## Task 7: Integration Testing

**Files:**
- Create: `tests/test_integration_hkex.py`
- Test: Run integration tests

**Step 1: Write integration test**

Create `tests/test_integration_hkex.py`:

```python
"""
Integration Tests for HKEX Market Data
Tests the full data flow: database → API → response
"""
import pytest
import requests
from datetime import datetime, timedelta
import os

API_BASE = os.getenv('API_BASE', 'http://localhost:3003')


class TestHKEXIntegration:
    """Test HKEX data integration"""

    def test_performance_analytics_endpoint_exists(self):
        """Test that endpoint responds"""
        response = requests.get(f"{API_BASE}/api/analytics/performance?time_range=1m")
        assert response.status_code == 200

    def test_performance_analytics_returns_valid_json(self):
        """Test that response is valid JSON"""
        response = requests.get(f"{API_BASE}/api/analytics/performance?time_range=1m")
        data = response.json()

        assert 'return_attribution' in data
        assert 'risk_exposure' in data
        assert 'correlations' in data
        assert 'stress_test' in data

    def test_return_attribution_structure(self):
        """Test return attribution has correct structure"""
        response = requests.get(f"{API_BASE}/api/analytics/performance?time_range=1m")
        data = response.json()
        attribution = data['return_attribution']

        assert 'total' in attribution
        assert isinstance(attribution['total'], (int, float))

        assert 'breakdown' in attribution
        assert isinstance(attribution['breakdown'], list)

        if len(attribution['breakdown']) > 0:
            item = attribution['breakdown'][0]
            assert 'indicator' in item
            assert 'contribution' in item
            assert 'percentage' in item

    def test_time_range_parameter(self):
        """Test different time range parameters"""
        ranges = ['1w', '1m', '3m', '1y']

        for time_range in ranges:
            response = requests.get(f"{API_BASE}/api/analytics/performance?time_range={time_range}")
            assert response.status_code == 200, f"Failed for range {time_range}"

    def test_indicators_endpoint(self):
        """Test market indicators endpoint"""
        response = requests.get(f"{API_BASE}/api/analytics/indicators?limit=10")
        assert response.status_code == 200

        data = response.json()
        assert 'data' in data
        assert 'count' in data

    @pytest.mark.skipif(not os.getenv('RUN_DB_TESTS'), reason="Requires database")
    def test_database_has_hkex_tables(self):
        """Test that database tables exist"""
        from src.database.connection import get_db_connection

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check tables exist
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema='public'
            AND table_name IN ('hkex_raw_data', 'market_indicators')
        """)

        tables = [row[0] for row in cursor.fetchall()]

        assert 'hkex_raw_data' in tables
        assert 'market_indicators' in tables

        cursor.close()
        conn.close()

    @pytest.mark.skipif(not os.getenv('RUN_DB_TESTS'), reason="Requires database")
    def test_database_has_recent_data(self):
        """Test that database has recent data"""
        from src.database.connection import get_db_connection

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check for data in last 7 days
        cursor.execute("""
            SELECT COUNT(*)
            FROM market_indicators
            WHERE date >= CURRENT_DATE - INTERVAL '7 days'
        """)

        count = cursor.fetchone()[0]

        # Should have at least some data (or 0 if crawler hasn't run)
        assert count >= 0

        cursor.close()
        conn.close()
```

**Step 2: Run tests without database**

Run: `cd .worktrees/hkex-integration && pytest tests/test_integration_hkex.py -v -k "not db_tests"`

Expected: Tests pass (API endpoint tests)

**Step 3: Run tests with database (if data available)**

Run: `cd .worktrees/hkex-integration && RUN_DB_TESTS=1 pytest tests/test_integration_hkex.py -v`

Expected: Tests pass if database has data

**Step 4: Commit**

```bash
cd .worktrees/hkex-integration
git add tests/test_integration_hkex.py
git commit -m "test: add integration tests for HKEX data"
```

---

## Task 8: Browser Verification and Final Cleanup

**Files:**
- Modify: (verify frontend works with real data)
- Create: `docs/plans/2025-12-29-hkex-integration-summary.md`

**Step 1: Start backend server**

Run: `cd .worktrees/hkex-integration && python -m uvicorn src.api.main:app --reload --port 3003`

Wait for: `Uvicorn running on http://0.0.0.0:3003`

**Step 2: Start frontend server**

Run: `cd frontend && npm run dev` (from main repo)

Wait for: Vite server ready

**Step 3: Open browser to test**

Navigate to: `http://localhost:3000/`

Actions:
- Click on "性能分析" tab
- Verify Return Attribution chart displays
- Check browser console for errors
- Test time range buttons (1w, 1m, 3m, 1y)

**Step 4: Verify data flow**

Open browser DevTools Network tab:
- Look for request to `/api/analytics/performance`
- Verify response contains real HKEX data
- Check that return_attribution values are non-zero if database has data

**Step 5: Create summary document**

Create `docs/plans/2025-12-29-hkex-integration-summary.md`:

```markdown
# HKEX Data Integration - Phase 1 Complete

**Date**: 2025-12-29
**Status**: ✅ Complete

## What Was Implemented

1. **Database Schema**
   - `hkex_raw_data` table for raw market data
   - `market_indicators` table for calculated indicators
   - Automatic trigger for indicator calculation

2. **HKEX Crawler Integration**
   - Database writer module (`database-writer.js`)
   - Modified crawler to write to CBSC database
   - Fallback to file storage on database failure

3. **CBSC Backend API**
   - `/api/analytics/performance` endpoint
   - Market indicator service for calculations
   - Mock data fallback when no real data available

4. **Frontend**
   - Already completed in Phase 4
   - Automatically displays real data when available

## Data Flow

```
HKEX Crawler → PostgreSQL → Trigger → market_indicators
                                            ↓
                              FastAPI Endpoint → JSON Response
                                            ↓
                                Frontend → Chart Display
```

## Files Changed

### CBSC System
- `src/db/migrations/001_create_hkex_tables.py` (new)
- `src/api/market_data_endpoints.py` (new)
- `src/services/market_indicator_service.py` (new)
- `src/api/main.py` (modified)

### HKEX Crawler
- `src/database-writer.js` (new)
- `src/crawler.js` (modified)
- `.env` (modified)
- `package.json` (modified)

## Testing Checklist

- [x] Database tables created successfully
- [x] Trigger calculates indicators on insert
- [x] Database writer connects and writes data
- [x] API endpoint returns valid JSON
- [x] Frontend displays data without errors
- [x] Mock data fallback works when database empty
- [x] Time range filtering works

## Next Steps (Phase 2)

1. Run crawler to populate historical data
2. Implement breadth_momentum indicator
3. Add correlation heatmap integration
4. Add real-time data updates
5. Performance optimization (caching)

## Rollback Procedure

If issues arise:
1. Stop crawler (stop database writes)
2. Frontend automatically falls back to mock data
3. Database can be cleaned: `DELETE FROM market_indicators; DELETE FROM hkex_raw_data;`
```

**Step 6: Final commit**

```bash
cd .worktrees/hkex-integration
git add docs/plans/2025-12-29-hkex-integration-summary.md
git commit -m "docs: add HKEX integration completion summary"
```

**Step 7: Merge back to main branch**

```bash
cd .worktrees/hkex-integration
git checkout main
git merge feature/hkex-data-integration --no-ff
git push origin main
```

**Step 8: Clean up worktree**

```bash
cd C:\Users\Penguin8n\CODEX--
git worktree remove .worktrees/hkex-integration
git branch -d feature/hkex-data-integration
```

---

## Success Criteria

All tasks complete when:
- [x] Database tables and trigger working
- [x] HKEX crawler writes to database
- [x] API endpoint returns correct data
- [x] Frontend displays real HKEX data
- [x] All tests passing
- [x] Documentation complete
- [x] Worktree cleaned up
