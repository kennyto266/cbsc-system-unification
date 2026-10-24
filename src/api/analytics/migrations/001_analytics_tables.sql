-- Analytics Database Schema
-- Migration 001: Create analytics tables

-- Performance metrics cache table
CREATE TABLE IF NOT EXISTS performance_metrics_cache (
    strategy_id VARCHAR(50) NOT NULL,
    period VARCHAR(10) NOT NULL,
    calculated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    benchmark_symbol VARCHAR(20),
    total_return DECIMAL(10,4),
    sharpe_ratio DECIMAL(8,4),
    sortino_ratio DECIMAL(8,4),
    max_drawdown DECIMAL(10,4),
    volatility DECIMAL(8,4),
    calmar_ratio DECIMAL(8,4),
    win_rate DECIMAL(5,2),
    profit_factor DECIMAL(8,4),
    avg_trade_duration DECIMAL(8,4),
    beta DECIMAL(8,4),
    alpha DECIMAL(8,4),
    PRIMARY KEY (strategy_id, period, benchmark_symbol),
    INDEX idx_strategy_id (strategy_id),
    INDEX idx_calculated_at (calculated_at)
);

-- Historical aggregates table
CREATE TABLE IF NOT EXISTS historical_aggregates (
    strategy_id VARCHAR(50) NOT NULL,
    date DATE NOT NULL,
    granularity VARCHAR(10) NOT NULL,
    total_pnl DECIMAL(15,2),
    position_count INTEGER,
    trade_count INTEGER,
    max_position_size DECIMAL(15,2),
    turnover_rate DECIMAL(8,4),
    exposure DECIMAL(15,2),
    leverage DECIMAL(8,4),
    volatility_30d DECIMAL(8,4),
    PRIMARY KEY (strategy_id, date, granularity),
    INDEX idx_strategy_date (strategy_id, date),
    INDEX idx_granularity (granularity)
);

-- Daily strategy performance
CREATE TABLE IF NOT EXISTS daily_strategy_performance (
    strategy_id VARCHAR(50) NOT NULL,
    date DATE NOT NULL,
    open_value DECIMAL(15,2),
    close_value DECIMAL(15,2),
    high_value DECIMAL(15,2),
    low_value DECIMAL(15,2),
    daily_return DECIMAL(10,6),
    daily_pnl DECIMAL(15,2),
    volume BIGINT,
    trade_count INTEGER,
    commission_total DECIMAL(15,2),
    max_drawdown_intraday DECIMAL(10,4),
    var_1d DECIMAL(15,2),
    PRIMARY KEY (strategy_id, date),
    INDEX idx_date (date),
    INDEX idx_strategy_date (strategy_id, date)
);

-- Asset correlations cache
CREATE TABLE IF NOT EXISTS asset_correlations (
    symbol1 VARCHAR(20) NOT NULL,
    symbol2 VARCHAR(20) NOT NULL,
    correlation DECIMAL(8,6),
    calculated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    sample_size INTEGER,
    period_days INTEGER,
    PRIMARY KEY (symbol1, symbol2),
    INDEX idx_correlation (correlation),
    INDEX idx_calculated_at (calculated_at)
);

-- Asset daily returns for correlation calculations
CREATE TABLE IF NOT EXISTS asset_daily_returns (
    symbol VARCHAR(20) NOT NULL,
    date DATE NOT NULL,
    daily_return DECIMAL(10,6),
    volume BIGINT,
    market_cap DECIMAL(20,2),
    sector VARCHAR(50),
    PRIMARY KEY (symbol, date),
    INDEX idx_date (date),
    INDEX idx_symbol_date (symbol, date)
);

-- Portfolio snapshots
CREATE TABLE IF NOT EXISTS portfolio_snapshots (
    user_id VARCHAR(50) NOT NULL,
    snapshot_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total_value DECIMAL(20,2),
    cash DECIMAL(20,2),
    invested DECIMAL(20,2),
    available_margin DECIMAL(20,2),
    initial_capital DECIMAL(20,2),
    day_change DECIMAL(20,2),
    day_change_percent DECIMAL(8,4),
    total_return DECIMAL(20,2),
    total_return_percent DECIMAL(8,4),
    active_strategies INTEGER,
    total_positions INTEGER,
    leverage DECIMAL(8,4),
    var_95 DECIMAL(20,2),
    cvar_95 DECIMAL(20,2),
    PRIMARY KEY (user_id, snapshot_date),
    INDEX idx_snapshot_date (snapshot_date),
    INDEX idx_user_date (user_id, snapshot_date)
);

-- Strategy daily P&L summary
CREATE TABLE IF NOT EXISTS strategy_daily_pnl (
    strategy_id VARCHAR(50) NOT NULL,
    user_id VARCHAR(50) NOT NULL,
    date DATE NOT NULL,
    daily_pnl DECIMAL(15,2),
    realized_pnl DECIMAL(15,2),
    unrealized_pnl DECIMAL(15,2),
    commission DECIMAL(15,2),
    trade_count INTEGER,
    win_rate DECIMAL(5,2),
    profit_factor DECIMAL(8,4),
    max_drawdown DECIMAL(10,4),
    sharpe_ratio_30d DECIMAL(8,4),
    PRIMARY KEY (strategy_id, date),
    INDEX idx_user_date (user_id, date),
    INDEX idx_date (date)
);

-- Background task tracking
CREATE TABLE IF NOT EXISTS background_tasks (
    task_id VARCHAR(100) NOT NULL,
    task_type VARCHAR(50) NOT NULL,
    strategy_id VARCHAR(50),
    user_id VARCHAR(50),
    status ENUM('pending', 'running', 'completed', 'failed') NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    error_message TEXT,
    result_json JSON,
    progress INTEGER DEFAULT 0,
    priority INTEGER DEFAULT 0,
    PRIMARY KEY (task_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    INDEX idx_strategy_type (strategy_id, task_type)
);

-- Strategy performance benchmarks
CREATE TABLE IF NOT EXISTS strategy_benchmarks (
    strategy_id VARCHAR(50) NOT NULL,
    benchmark_symbol VARCHAR(20) NOT NULL,
    period VARCHAR(10) NOT NULL,
    correlation DECIMAL(8,6),
    beta DECIMAL(8,4),
    alpha DECIMAL(8,4),
    tracking_error DECIMAL(8,4),
    information_ratio DECIMAL(8,4),
    up_capture DECIMAL(8,4),
    down_capture DECIMAL(8,4),
    calculated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (strategy_id, benchmark_symbol, period),
    INDEX idx_correlation (correlation),
    INDEX idx_alpha (alpha)
);

-- Risk metrics cache
CREATE TABLE IF NOT EXISTS risk_metrics_cache (
    strategy_id VARCHAR(50) NOT NULL,
    period VARCHAR(10) NOT NULL,
    confidence_level VARCHAR(10) NOT NULL,
    var DECIMAL(15,2),
    cvar DECIMAL(15,2),
    expected_shortfall DECIMAL(15,2),
    max_loss_1d DECIMAL(15,2),
    max_loss_1w DECIMAL(15,2),
    volatility DECIMAL(8,4),
    downside_volatility DECIMAL(8,4),
    skewness DECIMAL(8,4),
    kurtosis DECIMAL(8,4),
    calculated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (strategy_id, period, confidence_level),
    INDEX idx_strategy_period (strategy_id, period)
);

-- Sector performance tracking
CREATE TABLE IF NOT EXISTS sector_performance (
    sector VARCHAR(50) NOT NULL,
    date DATE NOT NULL,
    total_return DECIMAL(10,4),
    volatility DECIMAL(8,4),
    volume BIGINT,
    market_cap DECIMAL(20,2),
    num_positions INTEGER,
    weight DECIMAL(5,2),
    contribution_to_return DECIMAL(10,4),
    contribution_to_risk DECIMAL(8,4),
    PRIMARY KEY (sector, date),
    INDEX idx_date (date),
    INDEX idx_return (total_return)
);

-- Analytics query log for performance monitoring
CREATE TABLE IF NOT EXISTS analytics_query_log (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(50),
    endpoint VARCHAR(100) NOT NULL,
    query_params JSON,
    execution_time_ms INTEGER,
    cache_hit BOOLEAN,
    result_size INTEGER,
    error_code INTEGER,
    error_message TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_endpoint (endpoint),
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at),
    INDEX idx_execution_time (execution_time_ms)
);

-- Create optimized composite indexes for common queries
CREATE INDEX idx_portfolio_user_latest ON portfolio_snapshots(user_id, snapshot_date DESC);
CREATE INDEX idx_performance_cache_strategy_period ON performance_metrics_cache(strategy_id, period, calculated_at DESC);
CREATE INDEX idx_daily_pnl_strategy_date ON strategy_daily_pnl(strategy_id, date DESC);
CREATE INDEX idx_historical_agg_strategy_granularity ON historical_aggregates(strategy_id, granularity, date DESC);

-- Create partitions for large tables (MySQL 8.0+)
-- This would be executed separately based on MySQL version
-- ALTER TABLE daily_strategy_performance PARTITION BY RANGE (YEAR(date)) (
--     PARTITION p2023 VALUES LESS THAN (2024),
--     PARTITION p2024 VALUES LESS THAN (2025),
--     PARTITION p2025 VALUES LESS THAN (2026),
--     PARTITION pmax VALUES LESS THAN MAXVALUE
-- );

-- Insert initial configuration values
INSERT IGNORE INTO asset_correlations (symbol1, symbol2, correlation, sample_size, period_days) VALUES
    ('SPY', 'QQQ', 0.92, 252, 252),
    ('SPY', 'IWM', 0.89, 252, 252),
    ('QQQ', 'IWM', 0.85, 252, 252);

-- Create views for common queries
CREATE OR REPLACE VIEW v_strategy_performance_summary AS
SELECT
    s.strategy_id,
    s.name,
    s.status,
    s.created_at,
    COALESCE(perf.total_return, 0) as latest_return,
    COALESCE(perf.sharpe_ratio, 0) as latest_sharpe,
    COALESCE(perf.calculated_at, s.created_at) as last_updated
FROM strategies s
LEFT JOIN (
    SELECT
        strategy_id,
        total_return,
        sharpe_ratio,
        calculated_at,
        ROW_NUMBER() OVER (PARTITION BY strategy_id ORDER BY calculated_at DESC) as rn
    FROM performance_metrics_cache
) perf ON s.strategy_id = perf.strategy_id AND perf.rn = 1;

-- Grant permissions (adjust based on your user setup)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON analytics_.* TO 'analytics_user'@'%';