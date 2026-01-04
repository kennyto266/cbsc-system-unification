-- Migration: 003_create_strategy_management_tables
-- Description: Create comprehensive strategy management tables for the quant strategy management system
-- Version: 1.0.0
-- Created: 2025-12-18
-- Author: CBSC Development Team

-- Create strategy configurations table (user-specific strategy configurations)
CREATE TABLE IF NOT EXISTS strategy_configs (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid(),
    strategy_id VARCHAR(36) NOT NULL REFERENCES strategies(id),
    user_id VARCHAR(36) NOT NULL REFERENCES users(id),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    custom_parameters JSONB NOT NULL,
    risk_tolerance VARCHAR(20) DEFAULT 'medium' NOT NULL,
    max_position_size NUMERIC(15,2) DEFAULT 100000.00 NOT NULL,
    stop_loss_percent NUMERIC(5,2) DEFAULT 5.0 NOT NULL,
    take_profit_percent NUMERIC(5,2),
    leverage_ratio NUMERIC(5,2) DEFAULT 1.0 NOT NULL,
    rebalance_frequency VARCHAR(20) DEFAULT 'daily' NOT NULL,
    min_trade_interval INTEGER DEFAULT 300 NOT NULL, -- seconds
    max_drawdown_limit NUMERIC(5,2) DEFAULT 20.0 NOT NULL,
    volatility_target NUMERIC(5,2),
    correlation_limit NUMERIC(5,2) DEFAULT 0.7 NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    is_simulation BOOLEAN DEFAULT TRUE NOT NULL,
    auto_execute BOOLEAN DEFAULT FALSE NOT NULL,
    notification_settings JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    created_by VARCHAR(36),
    updated_by VARCHAR(36),
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    deleted_at TIMESTAMP WITH TIME ZONE,
    deleted_by VARCHAR(36),
    version INTEGER DEFAULT 1 NOT NULL,
    metadata JSONB,
    notes TEXT,
    UNIQUE(strategy_id, user_id, name)
);

-- Create backtest results table
CREATE TABLE IF NOT EXISTS backtest_results (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid(),
    strategy_id VARCHAR(36) NOT NULL REFERENCES strategies(id),
    strategy_config_id VARCHAR(36) REFERENCES strategy_configs(id),
    user_id VARCHAR(36) NOT NULL REFERENCES users(id),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    backtest_type VARCHAR(20) DEFAULT 'standard' NOT NULL, -- standard, risk_management, stress_test, monte_carlo
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    initial_capital NUMERIC(20,2) NOT NULL,
    final_capital NUMERIC(20,2) NOT NULL,
    total_return NUMERIC(10,4) NOT NULL,
    annualized_return NUMERIC(10,4),
    max_drawdown NUMERIC(10,4) NOT NULL,
    max_drawdown_duration INTEGER, -- days
    sharpe_ratio NUMERIC(10,4),
    sortino_ratio NUMERIC(10,4),
    calmar_ratio NUMERIC(10,4),
    information_ratio NUMERIC(10,4),
    beta NUMERIC(10,4),
    alpha NUMERIC(10,4),
    tracking_error NUMERIC(10,4),
    volatility NUMERIC(10,4),
    downside_deviation NUMERIC(10,4),
    var_95 NUMERIC(10,4), -- Value at Risk at 95% confidence
    var_99 NUMERIC(10,4), -- Value at Risk at 99% confidence
    expected_shortfall NUMERIC(10,4),
    win_rate NUMERIC(5,4) NOT NULL,
    profit_factor NUMERIC(10,4),
    recovery_factor NUMERIC(10,4),
    payoff_ratio NUMERIC(10,4),
    average_win NUMERIC(20,2),
    average_loss NUMERIC(20,2),
    largest_win NUMERIC(20,2),
    largest_loss NUMERIC(20,2),
    total_trades INTEGER NOT NULL,
    winning_trades INTEGER NOT NULL,
    losing_trades INTEGER NOT NULL,
    average_trade_duration NUMERIC(10,2), -- days
    commission_total NUMERIC(20,2) DEFAULT 0.0 NOT NULL,
    slippage_total NUMERIC(20,2) DEFAULT 0.0 NOT NULL,
    benchmark_return NUMERIC(10,4),
    benchmark_volatility NUMERIC(10,4),
    correlation_with_benchmark NUMERIC(5,4),
    monthly_returns JSONB,
    yearly_returns JSONB,
    rolling_returns JSONB,
    trade_distribution JSONB,
    risk_metrics JSONB,
    performance_attribution JSONB,
    sector_allocation JSONB,
    regional_allocation JSONB,
    scenarios_tested JSONB,
    stress_test_results JSONB,
    monte_carlo_results JSONB,
    status VARCHAR(20) DEFAULT 'completed' NOT NULL, -- running, completed, failed, cancelled
    error_message TEXT,
    execution_time_seconds INTEGER,
    data_points_analyzed INTEGER,
    parameters_used JSONB,
    market_conditions JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    created_by VARCHAR(36),
    updated_by VARCHAR(36),
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    deleted_at TIMESTAMP WITH TIME ZONE,
    deleted_by VARCHAR(36),
    version INTEGER DEFAULT 1 NOT NULL,
    metadata JSONB,
    notes TEXT
);

-- Create performance records table (for tracking real-time strategy performance)
CREATE TABLE IF NOT EXISTS performance_records (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid(),
    strategy_id VARCHAR(36) NOT NULL REFERENCES strategies(id),
    strategy_config_id VARCHAR(36) REFERENCES strategy_configs(id),
    user_id VARCHAR(36) NOT NULL REFERENCES users(id),
    record_date DATE NOT NULL,
    record_time TIMESTAMP WITH TIME ZONE NOT NULL,
    portfolio_value NUMERIC(20,2) NOT NULL,
    cash_balance NUMERIC(20,2) NOT NULL,
    invested_value NUMERIC(20,2) NOT NULL,
    daily_return NUMERIC(10,4) NOT NULL,
    daily_return_pct NUMERIC(10,4) NOT NULL,
    cumulative_return NUMERIC(10,4) NOT NULL,
    cumulative_return_pct NUMERIC(10,4) NOT NULL,
    running_max_drawdown NUMERIC(10,4) NOT NULL,
    running_sharpe_ratio NUMERIC(10,4),
    running_volatility NUMERIC(10,4),
    running_var NUMERIC(10,4),
    positions_count INTEGER NOT NULL,
    active_positions INTEGER NOT NULL,
    long_positions INTEGER NOT NULL,
    short_positions INTEGER NOT NULL,
    sector_exposure JSONB,
    country_exposure JSONB,
    currency_exposure JSONB,
    risk_metrics JSONB,
    greeks JSONB, -- Options Greeks if applicable
    correlation_matrix JSONB,
    beta_portfolio NUMERIC(10,4),
    tracking_error NUMERIC(10,4),
    information_ratio NUMERIC(10,4),
    turnover_rate NUMERIC(10,4),
    trading_volume NUMERIC(20,2) NOT NULL,
    commissions NUMERIC(20,2) DEFAULT 0.0 NOT NULL,
    slippage NUMERIC(20,2) DEFAULT 0.0 NOT NULL,
    margin_used NUMERIC(20,2) DEFAULT 0.0 NOT NULL,
    margin_available NUMERIC(20,2),
    leverage_ratio NUMERIC(10,4) DEFAULT 1.0 NOT NULL,
    risk_score NUMERIC(5,4),
    performance_score NUMERIC(5,4),
    efficiency_score NUMERIC(5,4),
    alerts_triggered JSONB,
    benchmark_comparison JSONB,
    market_conditions JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    created_by VARCHAR(36),
    updated_by VARCHAR(36),
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    deleted_at TIMESTAMP WITH TIME ZONE,
    deleted_by VARCHAR(36),
    version INTEGER DEFAULT 1 NOT NULL,
    metadata JSONB,
    notes TEXT,
    UNIQUE(strategy_id, strategy_config_id, record_date, record_time)
);

-- Create indexes for strategy management tables
CREATE INDEX IF NOT EXISTS idx_strategy_configs_strategy_user ON strategy_configs(strategy_id, user_id);
CREATE INDEX IF NOT EXISTS idx_strategy_configs_user_active ON strategy_configs(user_id, is_active);
CREATE INDEX IF NOT EXISTS idx_strategy_configs_risk_tolerance ON strategy_configs(risk_tolerance);

CREATE INDEX IF NOT EXISTS idx_backtest_results_strategy ON backtest_results(strategy_id);
CREATE INDEX IF NOT EXISTS idx_backtest_results_user ON backtest_results(user_id);
CREATE INDEX IF NOT EXISTS idx_backtest_results_date_range ON backtest_results(start_date, end_date);
CREATE INDEX IF NOT EXISTS idx_backtest_results_type ON backtest_results(backtest_type);
CREATE INDEX IF NOT EXISTS idx_backtest_results_return ON backtest_results(total_return DESC);
CREATE INDEX IF NOT EXISTS idx_backtest_results_sharpe ON backtest_results(sharpe_ratio DESC NULLS LAST);

CREATE INDEX IF NOT EXISTS idx_performance_records_strategy_date ON performance_records(strategy_id, record_date);
CREATE INDEX IF NOT EXISTS idx_performance_records_config_date ON performance_records(strategy_config_id, record_date);
CREATE INDEX IF NOT EXISTS idx_performance_records_user_date ON performance_records(user_id, record_date);
CREATE INDEX IF NOT EXISTS idx_performance_records_date_time ON performance_records(record_date, record_time);

-- Create triggers for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_strategy_configs_updated_at
    BEFORE UPDATE ON strategy_configs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_backtest_results_updated_at
    BEFORE UPDATE ON backtest_results
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_performance_records_updated_at
    BEFORE UPDATE ON performance_records
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add check constraints
ALTER TABLE strategy_configs ADD CONSTRAINT chk_strategy_configs_position_size
    CHECK (max_position_size > 0);

ALTER TABLE strategy_configs ADD CONSTRAINT chk_strategy_configs_percentages
    CHECK (stop_loss_percent >= 0 AND stop_loss_percent <= 100
          AND (take_profit_percent IS NULL OR (take_profit_percent >= 0 AND take_profit_percent <= 100))
          AND max_drawdown_limit >= 0 AND max_drawdown_limit <= 100
          AND (volatility_target IS NULL OR (volatility_target >= 0 AND volatility_target <= 100))
          AND correlation_limit >= 0 AND correlation_limit <= 1);

ALTER TABLE strategy_configs ADD CONSTRAINT chk_strategy_configs_leverage
    CHECK (leverage_ratio > 0);

ALTER TABLE strategy_configs ADD CONSTRAINT chk_strategy_configs_interval
    CHECK (min_trade_interval >= 0);

ALTER TABLE backtest_results ADD CONSTRAINT chk_backtest_results_capital
    CHECK (initial_capital > 0 AND final_capital >= 0);

ALTER TABLE backtest_results ADD CONSTRAINT chk_backtest_results_return
    CHECK (annualized_return IS NULL OR (annualized_return >= -1 AND annualized_return <= 10));

ALTER TABLE backtest_results ADD CONSTRAINT chk_backtest_results_drawdown
    CHECK (max_drawdown <= 0 AND max_drawdown_duration >= 0);

ALTER TABLE backtest_results ADD CONSTRAINT chk_backtest_results_ratios
    CHECK ((sharpe_ratio IS NULL OR sharpe_ratio >= -10 AND sharpe_ratio <= 10)
          AND (sortino_ratio IS NULL OR sortino_ratio >= -10 AND sortino_ratio <= 10)
          AND (calmar_ratio IS NULL OR calmar_ratio >= -10 AND calmar_ratio <= 10));

ALTER TABLE backtest_results ADD CONSTRAINT chk_backtest_results_trades
    CHECK (total_trades >= 0 AND winning_trades >= 0 AND losing_trades >= 0
          AND winning_trades + losing_trades <= total_trades);

ALTER TABLE backtest_results ADD CONSTRAINT chk_backtest_results_win_rate
    CHECK (win_rate >= 0 AND win_rate <= 1);

ALTER TABLE performance_records ADD CONSTRAINT chk_performance_records_values
    CHECK (portfolio_value >= 0 AND cash_balance >= 0 AND invested_value >= 0
          AND portfolio_value = cash_balance + invested_value);

ALTER TABLE performance_records ADD CONSTRAINT chk_performance_records_positions
    CHECK (positions_count >= 0 AND active_positions >= 0
          AND long_positions >= 0 AND short_positions >= 0
          AND active_positions <= positions_count
          AND long_positions + short_positions = active_positions);

ALTER TABLE performance_records ADD CONSTRAINT chk_performance_records_turnover
    CHECK (turnover_rate >= 0);

-- Create views for common queries
CREATE OR REPLACE VIEW v_strategy_configs_active AS
SELECT
    sc.*,
    s.name as strategy_name,
    s.code as strategy_code,
    s.strategy_type,
    u.username as user_name,
    u.display_name as user_display_name
FROM strategy_configs sc
JOIN strategies s ON sc.strategy_id = s.id
JOIN users u ON sc.user_id = u.id
WHERE sc.is_active = TRUE AND sc.is_deleted = FALSE AND s.is_deleted = FALSE;

CREATE OR REPLACE VIEW v_backtest_results_summary AS
SELECT
    br.*,
    s.name as strategy_name,
    s.code as strategy_code,
    sc.name as config_name,
    u.username as user_name,
    CASE
        WHEN br.total_return >= 0.2 THEN 'Excellent'
        WHEN br.total_return >= 0.1 THEN 'Good'
        WHEN br.total_return >= 0.05 THEN 'Average'
        WHEN br.total_return >= 0 THEN 'Below Average'
        ELSE 'Poor'
    END as performance_rating,
    CASE
        WHEN br.sharpe_ratio >= 2 THEN 'Excellent'
        WHEN br.sharpe_ratio >= 1 THEN 'Good'
        WHEN br.sharpe_ratio >= 0.5 THEN 'Average'
        WHEN br.sharpe_ratio >= 0 THEN 'Below Average'
        ELSE 'Poor'
    END as sharpe_rating
FROM backtest_results br
JOIN strategies s ON br.strategy_id = s.id
LEFT JOIN strategy_configs sc ON br.strategy_config_id = sc.id
JOIN users u ON br.user_id = u.id
WHERE br.is_deleted = FALSE;

CREATE OR REPLACE VIEW v_performance_latest AS
SELECT DISTINCT ON (strategy_id, strategy_config_id)
    pr.*,
    s.name as strategy_name,
    sc.name as config_name,
    u.username as user_name,
    pr.cumulative_return_pct as latest_return,
    pr.running_max_drawdown as latest_drawdown
FROM performance_records pr
JOIN strategies s ON pr.strategy_id = s.id
LEFT JOIN strategy_configs sc ON pr.strategy_config_id = sc.id
JOIN users u ON pr.user_id = u.id
WHERE pr.is_deleted = FALSE
ORDER BY pr.strategy_id, pr.strategy_config_id, pr.record_date DESC, pr.record_time DESC;

-- Insert default strategy categories if they don't exist
INSERT INTO strategy_categories (name, display_name, description, level) VALUES
    ('technical_indicators', 'Technical Indicators', 'Strategies based on technical analysis indicators', 1),
    ('momentum', 'Momentum Strategies', 'Strategies that exploit market momentum', 1),
    ('mean_reversion', 'Mean Reversion', 'Strategies that bet on price reversion to mean', 1),
    ('volume', 'Volume Based', 'Strategies using volume analysis', 1),
    ('volatility', 'Volatility Strategies', 'Strategies that trade volatility', 1),
    ('fundamental', 'Fundamental Analysis', 'Strategies based on fundamental data', 1),
    ('quantitative', 'Quantitative Models', 'Mathematical and statistical models', 1),
    ('portfolio', 'Portfolio Management', 'Multi-asset portfolio strategies', 1),
    ('arbitrage', 'Arbitrage', 'Statistical and risk arbitrage strategies', 1),
    ('macro', 'Macro Strategies', 'Strategies based on macroeconomic factors', 1)
ON CONFLICT DO NOTHING;

-- Insert sub-categories for technical indicators
INSERT INTO strategy_categories (name, display_name, description, parent_id, level)
SELECT
    'ma_crossover', 'MA Crossover', 'Moving average crossover strategies',
    id, 2
FROM strategy_categories
WHERE name = 'technical_indicators'
ON CONFLICT DO NOTHING;

INSERT INTO strategy_categories (name, display_name, description, parent_id, level)
SELECT
    'rsi_strategies', 'RSI Strategies', 'Relative Strength Index based strategies',
    id, 2
FROM strategy_categories
WHERE name = 'technical_indicators'
ON CONFLICT DO NOTHING;

INSERT INTO strategy_categories (name, display_name, description, parent_id, level)
SELECT
    'bollinger_bands', 'Bollinger Bands', 'Bollinger Band strategies',
    id, 2
FROM strategy_categories
WHERE name = 'technical_indicators'
ON CONFLICT DO NOTHING;

INSERT INTO strategy_categories (name, display_name, description, parent_id, level)
SELECT
    'macd_strategies', 'MACD Strategies', 'MACD indicator strategies',
    id, 2
FROM strategy_categories
WHERE name = 'technical_indicators'
ON CONFLICT DO NOTHING;

-- Grant permissions if needed (optional, adjust for your setup)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;

-- Migration completed successfully
COMMENT ON SCHEMA public IS 'CBSC Quantitative Strategy Management System';