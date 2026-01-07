# AGX Analytics System - User Guide

## 📋 Overview

The AGX Analytics System provides high-performance data analysis capabilities for the CBSC quantitative trading strategy management platform. This guide will help you get started with using AGX for strategy development and analysis.

---

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Python 3.8+ installed
- AGX cloned and configured

### Starting the System

**Linux/macOS:**
```bash
./scripts/start_agx_system.sh
```

**Windows:**
```cmd
scripts\start_agx_system.bat
```

This script will:
1. Start AGX and ClickHouse containers
2. Initialize the database schema
3. Import sample data
4. Start the ETL scheduler

---

## 🔧 Configuration

### ClickHouse Connection

Configure AGX to connect to ClickHouse:

1. Open AGX at http://localhost:8080
2. Navigate to Settings → Database Connections
3. Add new connection with:
   - **Host**: `localhost`
   - **Port**: `8123`
   - **Database**: `analytics`
   - **User**: `default`
   - **Password**: (leave empty)

Alternatively, import the configuration from:
```
agx/config/clickhouse_connection.json
```

---

## 📊 Data Schema

The system includes four main tables:

### 1. strategy_backtests
Historical backtest results for strategy analysis.

**Key Columns:**
- `strategy_id` - Strategy identifier
- `backtest_date` - When the backtest was run
- `symbol` - Trading symbol
- `total_return` - Total return percentage
- `sharpe_ratio` - Sharpe ratio
- `max_drawdown` - Maximum drawdown
- `parameters` - Strategy parameters (JSON)

### 2. strategy_performance
Real-time strategy performance metrics.

**Key Columns:**
- `strategy_id` - Strategy identifier
- `timestamp` - Performance snapshot time
- `current_pnl` - Realized profit and loss
- `unrealized_pnl` - Unrealized P&L
- `position_size` - Current position

### 3. market_data
Historical market data for analysis.

**Key Columns:**
- `symbol` - Trading symbol
- `timestamp` - Data timestamp
- `open`, `high`, `low`, `close` - OHLC prices
- `volume` - Trading volume

### 4. trades
Individual trade records.

**Key Columns:**
- `trade_id` - Unique trade identifier
- `strategy_id` - Strategy that generated the trade
- `entry_time`, `exit_time` - Trade timing
- `pnl` - Trade profit/loss

---

## 💡 Common Analysis Patterns

### 1. Strategy Performance Comparison

**Goal**: Find the best performing strategies

```sql
SELECT
    strategy_id,
    AVG(total_return) as avg_return,
    AVG(sharpe_ratio) as avg_sharpe,
    AVG(max_drawdown) as avg_drawdown,
    COUNT(*) as test_count
FROM strategy_backtests
WHERE backtest_date >= now() - INTERVAL 30 DAY
GROUP BY strategy_id
ORDER BY avg_sharpe DESC
LIMIT 10
```

### 2. Parameter Sensitivity Analysis

**Goal**: Analyze which parameter combinations work best

```sql
SELECT
    JSONExtractString(parameters, 'short_ma') as short_ma,
    JSONExtractString(parameters, 'long_ma') as long_ma,
    AVG(total_return) as avg_return,
    AVG(sharpe_ratio) as avg_sharpe,
    COUNT(*) as tests
FROM strategy_backtests
WHERE strategy_id = 'ma_crossover_v2'
GROUP BY short_ma, long_ma
ORDER BY avg_return DESC
```

### 3. Real-Time Performance Monitoring

**Goal**: Check current strategy performance

```sql
SELECT
    strategy_id,
    argMax(current_pnl, timestamp) as latest_pnl,
    argMax(last_signal, timestamp) as latest_signal,
    countIf(last_signal = 'BUY') as buy_signals,
    countIf(last_signal = 'SELL') as sell_signals
FROM strategy_performance
WHERE timestamp >= now() - INTERVAL 1 HOUR
GROUP BY strategy_id
ORDER BY latest_pnl DESC
```

### 4. Symbol Performance Analysis

**Goal**: Understand which symbols perform best

```sql
SELECT
    symbol,
    AVG(total_return) as avg_return,
    AVG(win_rate) as avg_win_rate,
    COUNT(*) as trade_count,
    sumIf(total_return, total_return > 0) as profitable_trades
FROM strategy_backtests
WHERE backtest_date >= now() - INTERVAL 7 DAY
GROUP BY symbol
ORDER BY avg_return DESC
```

### 5. Drawdown Analysis

**Goal**: Find strategies with acceptable drawdown

```sql
SELECT
    strategy_id,
    AVG(max_drawdown) as avg_drawdown,
    quantile(0.95)(max_drawdown) as max_drawdown_95th,
    COUNT(*) as tests
FROM strategy_backtests
WHERE backtest_date >= now() - INTERVAL 30 DAY
GROUP BY strategy_id
HAVING avg_drawdown < 0.15  -- Less than 15% drawdown
ORDER BY avg_drawdown ASC
```

---

## 🔄 Data Synchronization

The system uses an ETL pipeline to sync data from PostgreSQL to ClickHouse every 5 minutes.

### Manual Sync

Run a one-time sync:
```bash
cd ai-strategy-service
python scripts/etl_sync.py --once
```

### Check Sync Status

Query the ETL logs:
```sql
SELECT
    timestamp,
    source_table,
    target_table,
    status,
    records_processed,
    sync_duration_seconds
FROM etl_logs
ORDER BY timestamp DESC
LIMIT 10
```

---

## 📈 Strategy Development Workflow

### Phase 1: Data Exploration

Start by exploring existing backtest results:

1. **View all strategies**
   ```sql
   SELECT DISTINCT strategy_id FROM strategy_backtests ORDER BY strategy_id
   ```

2. **Analyze strategy types**
   ```sql
   SELECT
       splitByChar('_', strategy_id)[1] as strategy_type,
       COUNT(*) as count
   FROM strategy_backtests
   GROUP BY strategy_type
   ```

3. **Find top performers**
   ```sql
   SELECT * FROM top_strategies_mv ORDER BY avg_sharpe DESC LIMIT 10
   ```

### Phase 2: Parameter Optimization

Analyze parameter sensitivity for your chosen strategy:

1. **Extract parameter distribution**
   ```sql
   SELECT
       JSONExtractString(parameters, 'lookback') as lookback,
       AVG(total_return) as avg_return
   FROM strategy_backtests
   WHERE strategy_id = 'momentum_v2'
   GROUP BY lookback
   ORDER BY avg_return DESC
   ```

2. **Find optimal combinations**
   ```sql
   SELECT
       parameters,
       AVG(total_return) as avg_return,
       STD(total_return) as return_std
   FROM strategy_backtests
   WHERE strategy_id = 'your_strategy'
   GROUP BY parameters
   ORDER BY avg_return DESC, return_std ASC
   ```

### Phase 3: Validation

Validate your findings:

1. **Check consistency**
   ```sql
   SELECT
       toDate(backtest_date) as date,
       AVG(total_return) as daily_return
   FROM strategy_backtests
   WHERE strategy_id = 'your_strategy'
       AND parameters = '{"param": "value"}'
   GROUP BY date
   ORDER BY date
   ```

2. **Compare to baseline**
   ```sql
   SELECT
       'optimized' as label,
       AVG(total_return) as avg_return
   FROM strategy_backtests
   WHERE parameters = '{"optimized": true}'
   UNION ALL
   SELECT
       'baseline' as label,
       AVG(total_return) as avg_return
   FROM strategy_backtests
   WHERE parameters = '{"baseline": true}'
   ```

### Phase 4: Real-Time Monitoring

Monitor live performance:

1. **Current positions**
   ```sql
   SELECT
       strategy_id,
       symbol,
       position_size,
       current_pnl,
       unrealized_pnl
   FROM strategy_performance
   WHERE position_size != 0
   ORDER BY current_pnl DESC
   ```

2. **Recent signals**
   ```sql
   SELECT
       strategy_id,
       symbol,
       last_signal,
       last_signal_time
   FROM strategy_performance
   WHERE last_signal_time >= now() - INTERVAL 1 HOUR
   ORDER BY last_signal_time DESC
   ```

---

## 🛠️ Troubleshooting

### AGX cannot connect to ClickHouse

**Symptoms**: Connection error in AGX

**Solutions**:
1. Verify ClickHouse is running:
   ```bash
   docker ps | grep clickhouse
   ```

2. Test connection:
   ```bash
   docker exec agx-clickhouse-1 clickhouse-client --query "SELECT 1"
   ```

3. Check port:
   ```bash
   curl http://localhost:8123/ping
   ```

### No data appears in AGX

**Symptoms**: Tables exist but are empty

**Solutions**:
1. Check if ETL ran:
   ```sql
   SELECT * FROM etl_logs ORDER BY timestamp DESC LIMIT 5
   ```

2. Import sample data:
   ```bash
   cd ai-strategy-service
   python scripts/import_sample_data.py
   ```

3. Manually run ETL:
   ```bash
   python scripts/etl_sync.py --once
   ```

### Queries are slow

**Symptoms**: Queries take more than 30 seconds

**Solutions**:
1. Add date filtering:
   ```sql
   -- Good
   SELECT * FROM strategy_backtests
   WHERE backtest_date >= now() - INTERVAL 7 DAY

   -- Avoid
   SELECT * FROM strategy_backtests
   ```

2. Use materialized views:
   ```sql
   -- Pre-aggregated data is faster
   SELECT * FROM top_strategies_mv
   ```

3. Limit results:
   ```sql
   SELECT * FROM strategy_backtests LIMIT 10000
   ```

---

## 📚 Advanced Topics

### Custom Queries

Save frequently used queries as templates in AGX:

1. Run your query
2. Click "Save" → "New Query"
3. Name it descriptively (e.g., "Parameter Analysis - MA Crossover")

### Data Export

Export query results for further analysis:

1. Run your query
2. Click "Export"
3. Choose format (CSV, JSON, Excel)

### Performance Tips

1. **Use partitions**: Filter by `backtest_date` when possible
2. **Limit columns**: Select only needed columns
3. **Use aggregates**: Pre-aggregate with materialized views
4. **Batch operations**: Process 10,000 records at a time

---

## 📞 Support

For issues or questions:
- Check logs: `tail -f logs/etl_scheduler.log`
- Review ETL logs in ClickHouse: `SELECT * FROM etl_logs ORDER BY timestamp DESC LIMIT 10`
- Consult the main CBSC documentation

---

*Last Updated: 2026-01-07*
