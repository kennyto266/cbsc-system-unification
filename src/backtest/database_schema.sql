-- Backtest Database Schema
-- =========================
-- PostgreSQL schema for storing backtest results and metadata

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_backtest_results_created_at
ON backtest_results(created_at DESC);

-- Strategies table
CREATE TABLE IF NOT EXISTS strategies (
    strategy_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    strategy_name VARCHAR(255) NOT NULL,
    strategy_type VARCHAR(100) NOT NULL,
    description TEXT,
    parameters JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    tags TEXT[] DEFAULT '{}',

    CONSTRAINT valid_strategy_type CHECK (strategy_type IN (
        'momentum', 'mean_reversion', 'arbitrage', 'hft',
        'portfolio_optimization', 'risk_parity', 'custom'
    ))
);

-- Backtest tasks table (enhanced version)
CREATE TABLE IF NOT EXISTS backtest_tasks (
    task_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    strategy_id UUID NOT NULL REFERENCES strategies(strategy_id),
    strategy_version INTEGER DEFAULT 1,
    task_name VARCHAR(255),

    -- Task configuration
    backtest_type VARCHAR(50) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    initial_capital DECIMAL(20,2) NOT NULL DEFAULT 1000000.00,
    commission_rate DECIMAL(10,6) NOT NULL DEFAULT 0.001,
    slippage_rate DECIMAL(10,6) NOT NULL DEFAULT 0.0005,

    -- Execution parameters
    priority INTEGER NOT NULL DEFAULT 2,
    max_runtime INTEGER, -- seconds
    retry_count INTEGER NOT NULL DEFAULT 0,
    max_retries INTEGER NOT NULL DEFAULT 3,

    -- Special configurations
    monte_carlo_config JSONB,
    stress_scenarios TEXT[],
    optimization_params JSONB,
    walk_forward_config JSONB,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_by VARCHAR(100),
    tags TEXT[] DEFAULT '{}',
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    progress DECIMAL(5,2) DEFAULT 0.00, -- Percentage complete
    error_message TEXT,
    error_traceback TEXT,

    CONSTRAINT valid_backtest_type CHECK (backtest_type IN (
        'standard', 'risk_managed', 'stress_test',
        'monte_carlo', 'parameter_optimization', 'walk_forward'
    )),
    CONSTRAINT valid_status CHECK (status IN (
        'pending', 'running', 'completed', 'failed', 'cancelled'
    )),
    CONSTRAINT valid_progress CHECK (progress >= 0 AND progress <= 100)
);

-- Backtest results table (enhanced version)
CREATE TABLE IF NOT EXISTS backtest_results (
    task_id UUID PRIMARY KEY REFERENCES backtest_tasks(task_id) ON DELETE CASCADE,

    -- Basic performance metrics
    total_return DECIMAL(15,6),
    annualized_return DECIMAL(15,6),
    volatility DECIMAL(15,6),
    sharpe_ratio DECIMAL(15,6),
    sortino_ratio DECIMAL(15,6),
    calmar_ratio DECIMAL(15,6),
    max_drawdown DECIMAL(15,6),
    max_drawdown_duration INTEGER, -- days

    -- Risk metrics
    var_95 DECIMAL(15,6),
    var_99 DECIMAL(15,6),
    cvar_95 DECIMAL(15,6),
    cvar_99 DECIMAL(15,6),
    beta DECIMAL(15,6),
    alpha DECIMAL(15,6),
    information_ratio DECIMAL(15,6),
    tracking_error DECIMAL(15,6),

    -- Trade statistics
    total_trades INTEGER,
    winning_trades INTEGER,
    losing_trades INTEGER,
    win_rate DECIMAL(5,4),
    avg_win DECIMAL(20,6),
    avg_loss DECIMAL(20,6),
    profit_factor DECIMAL(15,6),
    avg_trade_duration DECIMAL(10,2), -- days
    largest_win DECIMAL(20,6),
    largest_loss DECIMAL(20,6),

    -- Portfolio metrics
    avg_position_size DECIMAL(20,6),
    max_position_size DECIMAL(20,6),
    avg_leverage DECIMAL(10,4),
    max_leverage DECIMAL(10,4),
    turnover_rate DECIMAL(15,6),

    -- Detailed data (stored as JSON)
    equity_curve JSONB,
    daily_returns JSONB,
    positions JSONB,
    trades JSONB,
    risk_metrics JSONB,
    performance_attribution JSONB,

    -- Special results
    monte_carlo_summary JSONB,
    stress_test_summary JSONB,
    optimization_summary JSONB,
    walk_forward_summary JSONB,

    -- Execution details
    execution_time_seconds DECIMAL(10,2),
    data_points_processed INTEGER,
    signals_generated INTEGER,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Benchmark data table
CREATE TABLE IF NOT EXISTS benchmarks (
    benchmark_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(255),
    description TEXT,
    data_source VARCHAR(100),

    -- Benchmark data
    start_date DATE,
    end_date DATE,
    total_return DECIMAL(15,6),
    annualized_return DECIMAL(15,6),
    volatility DECIMAL(15,6),
    sharpe_ratio DECIMAL(15,6),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Strategy-benchmark correlations
CREATE TABLE IF NOT EXISTS strategy_benchmark_correlation (
    task_id UUID REFERENCES backtest_results(task_id) ON DELETE CASCADE,
    benchmark_id UUID REFERENCES benchmarks(benchmark_id) ON DELETE CASCADE,
    correlation DECIMAL(15,6),
    beta DECIMAL(15,6),
    alpha DECIMAL(15,6),
    tracking_error DECIMAL(15,6),
    information_ratio DECIMAL(15,6),

    PRIMARY KEY (task_id, benchmark_id)
);

-- Performance snapshots for historical tracking
CREATE TABLE IF NOT EXISTS performance_snapshots (
    snapshot_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID REFERENCES backtest_results(task_id) ON DELETE CASCADE,
    snapshot_date DATE NOT NULL,
    portfolio_value DECIMAL(20,6),
    benchmark_value DECIMAL(20,6),
    cumulative_return DECIMAL(15,6),
    benchmark_return DECIMAL(15,6),
    excess_return DECIMAL(15,6),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(task_id, snapshot_date)
);

-- Risk events tracking
CREATE TABLE IF NOT EXISTS risk_events (
    event_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID REFERENCES backtest_results(task_id) ON DELETE CASCADE,
    event_date DATE NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    severity VARCHAR(50) NOT NULL,
    description TEXT,
    portfolio_value_before DECIMAL(20,6),
    portfolio_value_after DECIMAL(20,6),
    drawdown_at_event DECIMAL(15,6),
    var_breach BOOLEAN DEFAULT false,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT valid_event_type CHECK (event_type IN (
        'large_loss', 'var_breach', 'drawdown_peak',
        'volatility_spike', 'correlation_breakdown', 'liquidity_crisis'
    )),
    CONSTRAINT valid_severity CHECK (severity IN (
        'low', 'medium', 'high', 'critical'
    ))
);

-- Performance comparison matrix
CREATE TABLE IF NOT EXISTS performance_comparison (
    comparison_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_a UUID REFERENCES backtest_results(task_id) ON DELETE CASCADE,
    task_b UUID REFERENCES backtest_results(task_id) ON DELETE CASCADE,

    -- Performance differential
    return_difference DECIMAL(15,6),
    sharpe_difference DECIMAL(15,6),
    max_drawdown_difference DECIMAL(15,6),
    var_difference DECIMAL(15,6),

    -- Statistical tests
    t_statistic DECIMAL(15,6),
    p_value DECIMAL(15,6),
    correlation DECIMAL(15,6),

    comparison_date DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CHECK (task_a < task_b) -- Ensure consistent ordering
);

-- User strategy ratings
CREATE TABLE IF NOT EXISTS strategy_ratings (
    rating_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    strategy_id UUID REFERENCES strategies(strategy_id) ON DELETE CASCADE,
    user_id VARCHAR(100) NOT NULL,
    rating INTEGER NOT NULL,
    review TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT valid_rating CHECK (rating >= 1 AND rating <= 5),
    UNIQUE(strategy_id, user_id)
);

-- Backtest configurations (reusable templates)
CREATE TABLE IF NOT EXISTS backtest_templates (
    template_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    template_name VARCHAR(255) NOT NULL,
    description TEXT,

    -- Template configuration
    backtest_type VARCHAR(50) NOT NULL,
    default_initial_capital DECIMAL(20,6) DEFAULT 1000000,
    default_commission_rate DECIMAL(10,6) DEFAULT 0.001,
    default_slippage_rate DECIMAL(10,6) DEFAULT 0.0005,

    -- Risk parameters
    default_var_limit DECIMAL(10,6),
    default_max_drawdown_limit DECIMAL(10,6),
    default_leverage_limit DECIMAL(10,6),

    -- Special configurations
    monte_carlo_template JSONB,
    stress_test_template JSONB,
    optimization_template JSONB,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(100),
    is_public BOOLEAN DEFAULT false,
    usage_count INTEGER DEFAULT 0
);

-- Data versioning for reproducibility
CREATE TABLE IF NOT EXISTS data_versions (
    version_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    version_name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,

    -- Data source information
    data_source VARCHAR(100) NOT NULL,
    data_hash VARCHAR(128), -- SHA-512 hash of data
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    symbols TEXT[] NOT NULL,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(100),
    is_active BOOLEAN DEFAULT true
);

-- Link tasks to data versions
CREATE TABLE IF NOT EXISTS backtest_data_versions (
    task_id UUID REFERENCES backtest_tasks(task_id) ON DELETE CASCADE,
    version_id UUID REFERENCES data_versions(version_id) ON DELETE CASCADE,

    PRIMARY KEY (task_id, version_id)
);

-- Create useful indexes
CREATE INDEX IF NOT EXISTS idx_strategies_type ON strategies(strategy_type);
CREATE INDEX IF NOT EXISTS idx_strategies_active ON strategies(is_active);
CREATE INDEX IF NOT EXISTS idx_strategies_created_at ON strategies(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_backtest_tasks_strategy ON backtest_tasks(strategy_id);
CREATE INDEX IF NOT EXISTS idx_backtest_tasks_type ON backtest_tasks(backtest_type);
CREATE INDEX IF NOT EXISTS idx_backtest_tasks_status ON backtest_tasks(status);
CREATE INDEX IF NOT EXISTS idx_backtest_tasks_dates ON backtest_tasks(start_date, end_date);
CREATE INDEX IF NOT EXISTS idx_backtest_tasks_created_at ON backtest_tasks(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_backtest_tasks_priority ON backtest_tasks(priority DESC);

CREATE INDEX IF NOT EXISTS idx_results_sharpe ON backtest_results(sharpe_ratio DESC);
CREATE INDEX IF NOT EXISTS idx_results_return ON backtest_results(total_return DESC);
CREATE INDEX IF NOT EXISTS idx_results_drawdown ON backtest_results(max_drawdown);
CREATE INDEX IF NOT EXISTS idx_results_created_at ON backtest_results(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_snapshots_task ON performance_snapshots(task_id);
CREATE INDEX IF NOT EXISTS idx_snapshots_date ON performance_snapshots(snapshot_date);

CREATE INDEX IF NOT EXISTS idx_risk_events_task ON risk_events(task_id);
CREATE INDEX IF NOT EXISTS idx_risk_events_date ON risk_events(event_date);
CREATE INDEX IF NOT EXISTS idx_risk_events_type ON risk_events(event_type);

CREATE INDEX IF NOT EXISTS idx_comparison_date ON performance_comparison(comparison_date DESC);

-- Create GIN indexes for JSONB columns
CREATE INDEX IF NOT EXISTS idx_results_equity_curve ON backtest_results USING GIN(equity_curve);
CREATE INDEX IF NOT EXISTS idx_results_risk_metrics ON backtest_results USING GIN(risk_metrics);
CREATE INDEX IF NOT EXISTS idx_tasks_tags ON backtest_tasks USING GIN(tags);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add triggers for updated_at columns
CREATE TRIGGER update_strategies_updated_at
    BEFORE UPDATE ON strategies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_backtest_results_updated_at
    BEFORE UPDATE ON backtest_results
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_strategy_ratings_updated_at
    BEFORE UPDATE ON strategy_ratings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create view for strategy performance summary
CREATE OR REPLACE VIEW strategy_performance_summary AS
SELECT
    s.strategy_id,
    s.strategy_name,
    s.strategy_type,
    COUNT(br.task_id) AS total_backtests,
    AVG(br.total_return) AS avg_total_return,
    AVG(br.sharpe_ratio) AS avg_sharpe_ratio,
    AVG(br.max_drawdown) AS avg_max_drawdown,
    MAX(br.total_return) AS best_return,
    MIN(br.max_drawdown) AS worst_drawdown,
    AVG(br.execution_time_seconds) AS avg_execution_time,
    MAX(bt.created_at) AS last_backtest_date
FROM strategies s
LEFT JOIN backtest_tasks bt ON s.strategy_id = bt.strategy_id
LEFT JOIN backtest_results br ON bt.task_id = br.task_id
GROUP BY s.strategy_id, s.strategy_name, s.strategy_type;

-- Create view for recent backtest activity
CREATE OR REPLACE VIEW recent_backtest_activity AS
SELECT
    bt.task_id,
    s.strategy_name,
    bt.backtest_type,
    bt.status,
    bt.created_at,
    bt.started_at,
    bt.completed_at,
    bt.progress,
    br.total_return,
    br.sharpe_ratio
FROM backtest_tasks bt
JOIN strategies s ON bt.strategy_id = s.strategy_id
LEFT JOIN backtest_results br ON bt.task_id = br.task_id
ORDER BY bt.created_at DESC
LIMIT 100;

-- Create view for top performing strategies
CREATE OR REPLACE VIEW top_performing_strategies AS
SELECT
    s.strategy_id,
    s.strategy_name,
    s.strategy_type,
    AVG(br.total_return) AS avg_return,
    AVG(br.sharpe_ratio) AS avg_sharpe,
    COUNT(br.task_id) AS backtest_count,
    STDDEV(br.total_return) AS return_volatility,
    AVG(br.total_return) / NULLIF(STDDEV(br.total_return), 0) AS sharpe_of_returns
FROM strategies s
JOIN backtest_tasks bt ON s.strategy_id = bt.strategy_id
JOIN backtest_results br ON bt.task_id = br.task_id
WHERE bt.status = 'completed'
GROUP BY s.strategy_id, s.strategy_name, s.strategy_type
HAVING COUNT(br.task_id) >= 3  -- At least 3 backtests
ORDER BY sharpe_of_returns DESC, avg_sharpe DESC
LIMIT 50;

-- Create materialized view for strategy rankings (refreshed daily)
CREATE MATERIALIZED VIEW IF NOT EXISTS strategy_rankings AS
SELECT
    s.strategy_id,
    s.strategy_name,
    s.strategy_type,
    -- Performance metrics
    AVG(br.total_return) AS avg_return,
    AVG(br.sharpe_ratio) AS avg_sharpe,
    AVG(br.max_drawdown) AS avg_max_drawdown,
    -- Risk-adjusted metrics
    AVG(br.calmar_ratio) AS avg_calmar,
    AVG(br.sortino_ratio) AS avg_sortino,
    -- Consistency metrics
    COUNT(br.task_id) AS backtest_count,
    STDDEV(br.total_return) AS return_stddev,
    -- Ranking
    ROW_NUMBER() OVER (ORDER BY AVG(br.sharpe_ratio) DESC) AS sharpe_rank,
    ROW_NUMBER() OVER (ORDER BY AVG(br.calmar_ratio) DESC) AS calmar_rank,
    ROW_NUMBER() OVER (ORDER BY AVG(br.total_return) DESC) DESC,
    ROW_NUMBER() OVER (ORDER BY AVG(br.max_drawdown) ASC) AS drawdown_rank
FROM strategies s
JOIN backtest_tasks bt ON s.strategy_id = bt.strategy_id
JOIN backtest_results br ON bt.task_id = br.task_id
WHERE bt.status = 'completed'
  AND bt.created_at > NOW() - INTERVAL '1 year'
GROUP BY s.strategy_id, s.strategy_name, s.strategy_type
HAVING COUNT(br.task_id) >= 5;

-- Create unique index on materialized view
CREATE UNIQUE INDEX IF NOT EXISTS idx_strategy_rankings_id
ON strategy_rankings(strategy_id);

-- Function to refresh materialized view
CREATE OR REPLACE FUNCTION refresh_strategy_rankings()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY strategy_rankings;
END;
$$ LANGUAGE plpgsql;

-- Create partition for large tables (optional)
-- Uncomment if you expect very large amounts of data
/*
-- Partition backtest_results by year
CREATE TABLE backtest_results_y2024 PARTITION OF backtest_results
    FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');

CREATE TABLE backtest_results_y2025 PARTITION OF backtest_results
    FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');

-- Partition performance_snapshots by month for better query performance
CREATE TABLE performance_snapshots_y2024m01 PARTITION OF performance_snapshots
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
*/

-- Create sample data (for testing)
INSERT INTO benchmarks (symbol, name, description) VALUES
('SPY', 'S&P 500 ETF', 'Tracks the S&P 500 index'),
('QQQ', 'NASDAQ-100 ETF', 'Tracks the NASDAQ-100 index'),
('VTI', 'Total Stock Market ETF', 'Tracks the entire US stock market')
ON CONFLICT (symbol) DO NOTHING;

-- Create sample template
INSERT INTO backtest_templates (
    template_name,
    description,
    backtest_type,
    default_initial_capital,
    default_var_limit,
    default_max_drawdown_limit
) VALUES (
    'Standard Risk-Managed Backtest',
    'Default template for risk-managed backtests with common risk limits',
    'risk_managed',
    1000000,
    0.02,
    0.15
) ON CONFLICT DO NOTHING;