-- Migration: Create aggregate views for performance optimization
-- Version: 004
-- Description: Create materialized views and aggregate functions for faster queries
-- Created: 2025-12-11

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- 1. Strategy Daily Performance Summary (Materialized View)
CREATE MATERIALIZED VIEW IF NOT EXISTS strategy_daily_performance_summary AS
SELECT
    strategy_id,
    date,
    AVG(total_return) as avg_total_return,
    AVG(daily_return) as avg_daily_return,
    AVG(cumulative_return) as avg_cumulative_return,
    AVG(benchmark_return) as avg_benchmark_return,
    AVG(alpha) as avg_alpha,
    AVG(volatility) as avg_volatility,
    AVG(sharpe_ratio) as avg_sharpe_ratio,
    AVG(sortino_ratio) as avg_sortino_ratio,
    AVG(max_drawdown) as avg_max_drawdown,
    AVG(var_95) as avg_var_95,
    AVG(cvar_95) as avg_cvar_95,
    SUM(total_trades) as total_trades,
    SUM(winning_trades) as total_winning_trades,
    AVG(win_rate) as avg_win_rate,
    AVG(profit_factor) as avg_profit_factor,
    AVG(average_win) as avg_average_win,
    AVG(average_loss) as avg_average_loss,
    AVG(current_positions) as avg_current_positions,
    AVG(open_positions_value) as avg_open_positions_value,
    AVG(cash_balance) as avg_cash_balance,
    COUNT(*) as record_count,
    MIN(created_at) as first_record_time,
    MAX(created_at) as last_record_time
FROM strategy_performance
GROUP BY strategy_id, date;

-- Create unique index for concurrent refresh
CREATE UNIQUE INDEX IF NOT EXISTS idx_strategy_daily_perf_summary_unique
ON strategy_daily_performance_summary (strategy_id, date);

-- Create additional indexes for query performance
CREATE INDEX IF NOT EXISTS idx_strategy_daily_perf_summary_date
ON strategy_daily_performance_summary (date);
CREATE INDEX IF NOT EXISTS idx_strategy_daily_perf_summary_return
ON strategy_daily_performance_summary (avg_total_return DESC);

-- 2. Strategy Monthly Performance Summary (Materialized View)
CREATE MATERIALIZED VIEW IF NOT EXISTS strategy_monthly_performance_summary AS
SELECT
    strategy_id,
    DATE_TRUNC('month', date) as month,
    AVG(total_return) as avg_total_return,
    MAX(total_return) as max_total_return,
    MIN(total_return) as min_total_return,
    STDDEV(total_return) as stddev_total_return,
    AVG(daily_return) as avg_daily_return,
    AVG(volatility) as avg_volatility,
    AVG(sharpe_ratio) as avg_sharpe_ratio,
    AVG(max_drawdown) as avg_max_drawdown,
    SUM(total_trades) as total_trades,
    AVG(win_rate) as avg_win_rate,
    SUM(open_positions_value) as total_value_traded,
    COUNT(DISTINCT date) as trading_days,
    MIN(date) as month_start,
    MAX(date) as month_end
FROM strategy_performance
GROUP BY strategy_id, DATE_TRUNC('month', date);

-- Create indexes
CREATE UNIQUE INDEX IF NOT EXISTS idx_strategy_monthly_perf_summary_unique
ON strategy_monthly_performance_summary (strategy_id, month);
CREATE INDEX IF NOT EXISTS idx_strategy_monthly_perf_summary_month
ON strategy_monthly_performance_summary (month);

-- 3. Strategy Performance Leaderboard (Materialized View)
CREATE MATERIALIZED VIEW IF NOT EXISTS strategy_performance_leaderboard AS
WITH latest_performance AS (
    SELECT DISTINCT ON (strategy_id)
        strategy_id,
        total_return,
        sharpe_ratio,
        max_drawdown,
        win_rate,
        date
    FROM strategy_performance
    ORDER BY strategy_id, date DESC
),
strategy_info AS (
    SELECT
        s.id,
        s.name,
        s.code,
        s.strategy_type,
        s.risk_level,
        sc.display_name as category_name
    FROM strategies s
    LEFT JOIN strategy_categories sc ON s.category_id = sc.id
    WHERE s.is_deleted = FALSE AND s.status = 'active'
)
SELECT
    lp.strategy_id,
    si.name,
    si.code,
    si.strategy_type,
    si.risk_level,
    si.category_name,
    lp.total_return,
    lp.sharpe_ratio,
    lp.max_drawdown,
    lp.win_rate,
    lp.date as last_updated,
    -- Rank by different metrics
    ROW_NUMBER() OVER (ORDER BY lp.total_return DESC) as rank_by_return,
    ROW_NUMBER() OVER (ORDER BY lp.sharpe_ratio DESC NULLS LAST) as rank_by_sharpe,
    ROW_NUMBER() OVER (ORDER BY lp.max_drawdown ASC) as rank_by_drawdown,
    ROW_NUMBER() OVER (ORDER BY lp.win_rate DESC NULLS LAST) as rank_by_win_rate,
    -- Composite score (weighted average)
    (COALESCE(lp.total_return, 0) * 0.4 +
     COALESCE(lp.sharpe_ratio, 0) * 0.3 +
     COALESCE(-lp.max_drawdown, 0) * 0.2 +
     COALESCE(lp.win_rate, 0) * 0.1) as composite_score
FROM latest_performance lp
JOIN strategy_info si ON lp.strategy_id = si.id;

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_strategy_leaderboard_return
ON strategy_performance_leaderboard (total_return DESC);
CREATE INDEX IF NOT EXISTS idx_strategy_leaderboard_sharpe
ON strategy_performance_leaderboard (sharpe_ratio DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_strategy_leaderboard_type
ON strategy_performance_leaderboard (strategy_type, risk_level);

-- 4. User Portfolio Summary (Materialized View)
CREATE MATERIALIZED VIEW IF NOT EXISTS user_portfolio_summary AS
SELECT
    u.id as user_id,
    u.username,
    COUNT(DISTINCT p.id) as portfolio_count,
    COALESCE(SUM(p.total_value), 0) as total_portfolio_value,
    COALESCE(AVG(p.total_return_percent), 0) as avg_return_percent,
    COALESCE(AVG(p.sharpe_ratio), 0) as avg_sharpe_ratio,
    COALESCE(SUM(p.total_trades), 0) as total_trades,
    COALESCE(SUM(p.active_positions), 0) as total_active_positions,
    MAX(p.last_rebalanced) as last_rebalanced,
    COUNT(DISTINCT s.id) as strategy_count,
    CURRENT_TIMESTAMP as calculated_at
FROM users u
LEFT JOIN portfolios p ON u.id = p.user_id AND p.is_active = TRUE
LEFT JOIN strategy_configs sc ON p.id = sc.user_id AND sc.is_active = TRUE
LEFT JOIN strategies s ON sc.strategy_id = s.id
GROUP BY u.id, u.username;

-- Create indexes
CREATE UNIQUE INDEX IF NOT EXISTS idx_user_portfolio_summary_unique
ON user_portfolio_summary (user_id);
CREATE INDEX IF NOT EXISTS idx_user_portfolio_summary_value
ON user_portfolio_summary (total_portfolio_value DESC);

-- 5. Trading Volume Statistics (Materialized View)
CREATE MATERIALIZED VIEW IF NOT EXISTS trading_volume_statistics AS
SELECT
    DATE_TRUNC('day', trade_time) as trade_date,
    symbol,
    exchange,
    side,
    COUNT(*) as trade_count,
    SUM(quantity) as total_quantity,
    SUM(notional) as total_notional,
    AVG(price) as avg_price,
    MIN(price) as min_price,
    MAX(price) as max_price,
    SUM(total_cost) as total_cost,
    COUNT(DISTINCT portfolio_id) as unique_portfolios,
    COUNT(DISTINCT user_id) as unique_users
FROM trades
GROUP BY DATE_TRUNC('day', trade_time), symbol, exchange, side;

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_trading_volume_date
ON trading_volume_statistics (trade_date DESC);
CREATE INDEX IF NOT EXISTS idx_trading_volume_symbol
ON trading_volume_statistics (symbol, trade_date DESC);
CREATE INDEX IF NOT EXISTS idx_trading_volume_notional
ON trading_volume_statistics (total_notional DESC);

-- 6. Performance Metrics Trends (Materialized View)
CREATE MATERIALIZED VIEW IF NOT EXISTS performance_metrics_trends AS
WITH monthly_metrics AS (
    SELECT
        strategy_id,
        portfolio_id,
        metric_name,
        DATE_TRUNC('month', calculation_date) as month,
        AVG(value) as avg_value,
        MIN(value) as min_value,
        MAX(value) as max_value,
        STDDEV(value) as stddev_value,
        COUNT(*) as sample_count
    FROM performance_metrics
    WHERE metric_type IN ('return', 'risk')
    GROUP BY strategy_id, portfolio_id, metric_name, DATE_TRUNC('month', calculation_date)
),
monthly_trends AS (
    SELECT
        strategy_id,
        portfolio_id,
        metric_name,
        month,
        avg_value,
        LAG(avg_value) OVER (PARTITION BY strategy_id, portfolio_id, metric_name ORDER BY month) as prev_month_value,
        (avg_value - LAG(avg_value) OVER (PARTITION BY strategy_id, portfolio_id, metric_name ORDER BY month)) / NULLIF(LAG(avg_value) OVER (PARTITION BY strategy_id, portfolio_id, metric_name ORDER BY month), 0) * 100 as month_over_month_change
    FROM monthly_metrics
)
SELECT
    mt.*,
    s.name as strategy_name,
    p.name as portfolio_name,
    CASE
        WHEN mt.month_over_month_change > 5 THEN 'improving'
        WHEN mt.month_over_month_change < -5 THEN 'declining'
        ELSE 'stable'
    END as trend_status
FROM monthly_trends mt
LEFT JOIN strategies s ON mt.strategy_id = s.id
LEFT JOIN portfolios p ON mt.portfolio_id = p.id;

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_perf_trends_strategy_metric
ON performance_metrics_trends (strategy_id, metric_name, month DESC);
CREATE INDEX IF NOT EXISTS idx_perf_trends_portfolio_metric
ON performance_metrics_trends (portfolio_id, metric_name, month DESC);

-- 7. Create refresh functions for materialized views

-- Function to refresh all performance-related materialized views
CREATE OR REPLACE FUNCTION refresh_performance_views()
RETURNS JSONB AS $$
DECLARE
    v_start_time TIMESTAMP := NOW();
    v_results JSONB := '{}'::JSONB;
    v_view_name TEXT;
    v_views TEXT[] := ARRAY[
        'strategy_daily_performance_summary',
        'strategy_monthly_performance_summary',
        'strategy_performance_leaderboard',
        'user_portfolio_summary',
        'trading_volume_statistics',
        'performance_metrics_trends'
    ];
BEGIN
    -- Refresh each materialized view concurrently
    FOREACH v_view_name IN ARRAY v_views LOOP
        BEGIN
            EXECUTE format('REFRESH MATERIALIZED VIEW CONCURRENTLY %I', v_view_name);
            v_results := jsonb_set(
                v_results,
                ARRAY[v_view_name],
                jsonb_build_object('status', 'success', 'refreshed_at', NOW())
            );
        EXCEPTION WHEN OTHERS THEN
            v_results := jsonb_set(
                v_results,
                ARRAY[v_view_name],
                jsonb_build_object('status', 'error', 'error', SQLERRM)
            );
        END;
    END LOOP;

    RETURN jsonb_build_object(
        'started_at', v_start_time,
        'completed_at', NOW(),
        'duration_seconds', EXTRACT(EPOCH FROM (NOW() - v_start_time)),
        'results', v_results
    );
END;
$$ LANGUAGE plpgsql;

-- Function to refresh specific materialized view
CREATE OR REPLACE FUNCTION refresh_materialized_view(view_name TEXT)
RETURNS JSONB AS $$
DECLARE
    v_start_time TIMESTAMP := NOW();
    v_exists BOOLEAN;
BEGIN
    -- Check if view exists
    SELECT EXISTS (
        SELECT 1 FROM pg_matviews
        WHERE matviewname = view_name
    ) INTO v_exists;

    IF NOT v_exists THEN
        RETURN jsonb_build_object(
            'error', 'Materialized view not found',
            'view_name', view_name
        );
    END IF;

    -- Refresh the view
    EXECUTE format('REFRESH MATERIALIZED VIEW CONCURRENTLY %I', view_name);

    RETURN jsonb_build_object(
        'view_name', view_name,
        'status', 'success',
        'started_at', v_start_time,
        'completed_at', NOW(),
        'duration_seconds', EXTRACT(EPOCH FROM (NOW() - v_start_time))
    );
END;
$$ LANGUAGE plpgsql;

-- 8. Create optimized views for common queries

-- Strategy performance with latest data
CREATE OR REPLACE VIEW strategy_performance_latest AS
WITH latest_dates AS (
    SELECT
        strategy_id,
        MAX(date) as latest_date
    FROM strategy_performance
    GROUP BY strategy_id
)
SELECT
    sp.*,
    s.name as strategy_name,
    s.code as strategy_code,
    sc.display_name as category_name
FROM strategy_performance sp
JOIN latest_dates ld ON sp.strategy_id = ld.strategy_id AND sp.date = ld.latest_date
JOIN strategies s ON sp.strategy_id = s.id
LEFT JOIN strategy_categories sc ON s.category_id = sc.id;

-- Top performing strategies this week
CREATE OR REPLACE VIEW top_strategies_week AS
SELECT
    s.id as strategy_id,
    s.name,
    s.code,
    s.strategy_type,
    s.risk_level,
    AVG(sp.total_return) as avg_weekly_return,
    AVG(sp.sharpe_ratio) as avg_sharpe_ratio,
    AVG(sp.max_drawdown) as avg_max_drawdown,
    COUNT(*) as days_active
FROM strategies s
JOIN strategy_performance sp ON s.id = sp.strategy_id
WHERE sp.date >= CURRENT_DATE - INTERVAL '7 days'
  AND s.is_deleted = FALSE
  AND s.status = 'active'
GROUP BY s.id, s.name, s.code, s.strategy_type, s.risk_level
HAVING COUNT(*) >= 3  -- At least 3 days of data this week
ORDER BY avg_weekly_return DESC
LIMIT 50;

-- User trading activity summary
CREATE OR REPLACE VIEW user_trading_activity AS
SELECT
    u.id as user_id,
    u.username,
    COUNT(DISTINCT t.id) as total_trades,
    COUNT(DISTINCT DATE(t.trade_time)) as trading_days,
    SUM(t.notional) as total_volume,
    AVG(t.notional) as avg_trade_size,
    SUM(t.total_cost) as total_costs,
    COUNT(DISTINCT t.symbol) as unique_symbols,
    MAX(t.trade_time) as last_trade_time,
    CURRENT_TIMESTAMP as calculated_at
FROM users u
LEFT JOIN trades t ON u.id = t.user_id
GROUP BY u.id, u.username;

-- Grant permissions
GRANT SELECT ON strategy_daily_performance_summary TO cbsc_app;
GRANT SELECT ON strategy_monthly_performance_summary TO cbsc_app;
GRANT SELECT ON strategy_performance_leaderboard TO cbsc_app;
GRANT SELECT ON user_portfolio_summary TO cbsc_app;
GRANT SELECT ON trading_volume_statistics TO cbsc_app;
GRANT SELECT ON performance_metrics_trends TO cbsc_app;
GRANT SELECT ON strategy_performance_latest TO cbsc_app;
GRANT SELECT ON top_strategies_week TO cbsc_app;
GRANT SELECT ON user_trading_activity TO cbsc_app;

-- Grant execution permissions for refresh functions
GRANT EXECUTE ON FUNCTION refresh_performance_views TO cbsc_app;
GRANT EXECUTE ON FUNCTION refresh_materialized_view(TEXT) TO cbsc_app;