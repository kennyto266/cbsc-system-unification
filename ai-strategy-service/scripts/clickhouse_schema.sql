-- ClickHouse Schema for CBSC Analytics
-- This schema supports high-performance analytics queries for strategy development

-- Create analytics database
CREATE DATABASE IF NOT EXISTS analytics;
USE analytics;

-- 1. Strategy Backtest Results Table
-- Stores historical backtest results for strategy analysis
CREATE TABLE IF NOT EXISTS strategy_backtests (
    strategy_id String,
    backtest_date DateTime,
    symbol String,
    start_date DateTime,
    end_date DateTime,
    total_return Float32,
    sharpe_ratio Float32,
    max_drawdown Float32,
    win_rate Float32,
    profit_factor Float32,
    avg_trade Float32,
    total_trades UInt32,
    parameters String,
    created_at DateTime DEFAULT now()
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(backtest_date)
ORDER BY (strategy_id, backtest_date, symbol)
SETTINGS index_granularity = 8192;

-- 2. Strategy Performance Table
-- Real-time strategy performance metrics
CREATE TABLE IF NOT EXISTS strategy_performance (
    strategy_id String,
    timestamp DateTime,
    symbol String,
    current_pnl Float32,
    unrealized_pnl Float32,
    position_size Float32,
    entry_price Float32,
    current_price Float32,
    last_signal String,
    last_signal_time DateTime
) ENGINE = MergeTree()
PARTITION BY toYYYYMMDD(timestamp)
ORDER BY (strategy_id, timestamp, symbol)
SETTINGS index_granularity = 8192;

-- 3. Market Data Table
-- Historical market data for analysis
CREATE TABLE IF NOT EXISTS market_data (
    symbol String,
    timestamp DateTime,
    open Float32,
    high Float32,
    low Float32,
    close Float32,
    volume UInt64,
    vwap Float32
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (symbol, timestamp)
SETTINGS index_granularity = 8192;

-- 4. Trades Table
-- Individual trade records
CREATE TABLE IF NOT EXISTS trades (
    trade_id String,
    strategy_id String,
    symbol String,
    entry_time DateTime,
    exit_time Nullable(DateTime),
    entry_price Float32,
    exit_price Nullable(Float32),
    quantity Float32,
    side String,
    pnl Nullable(Float32),
    commission Float32
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(entry_time)
ORDER BY (strategy_id, entry_time, symbol)
SETTINGS index_granularity = 8192;

-- 5. ETL Logs Table
-- Track data synchronization operations
CREATE TABLE IF NOT EXISTS etl_logs (
    id UInt64,
    timestamp DateTime DEFAULT now(),
    source_table String,
    target_table String,
    status String,
    records_processed UInt32,
    records_failed UInt32,
    error_message String,
    sync_duration_seconds Float32
) ENGINE = MergeTree()
ORDER BY (timestamp, target_table)
SETTINGS index_granularity = 8192;

-- Materialized Views for Common Queries

-- Top performing strategies by Sharpe ratio
CREATE MATERIALIZED VIEW IF NOT EXISTS top_strategies_mv
ENGINE = ReplacingMergeTree()
ORDER BY (strategy_id, latest_backtest)
AS SELECT
    strategy_id,
    max(backtest_date) as latest_backtest,
    AVG(sharpe_ratio) as avg_sharpe,
    AVG(total_return) as avg_return,
    COUNT(*) as test_count
FROM strategy_backtests
WHERE backtest_date >= now() - INTERVAL 30 DAY
GROUP BY strategy_id;

-- Daily performance summary
CREATE MATERIALIZED VIEW IF NOT EXISTS daily_performance_summary_mv
ENGINE = SummingMergeTree()
ORDER BY (date, strategy_id)
AS SELECT
    toDate(backtest_date) as date,
    strategy_id,
    COUNT(*) as tests,
    AVG(total_return) as avg_return,
    AVG(sharpe_ratio) as avg_sharpe,
    AVG(max_drawdown) as avg_drawdown
FROM strategy_backtests
GROUP BY date, strategy_id;
