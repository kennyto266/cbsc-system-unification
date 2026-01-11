-- CBSC System Development Database Initialization
-- Creates basic database structure for development

-- Create database if not exists
SELECT 'CREATE DATABASE cbsc_dev'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'cbsc_dev')\gexec

-- Connect to development database
\c cbsc_dev

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS cbsc;
CREATE SCHEMA IF NOT EXISTS auth;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS config;

-- Grant permissions
GRANT ALL PRIVILEGES ON SCHEMA cbsc TO PUBLIC;
GRANT ALL PRIVILEGES ON SCHEMA auth TO PUBLIC;
GRANT ALL PRIVILEGES ON SCHEMA analytics TO PUBLIC;
GRANT ALL PRIVILEGES ON SCHEMA config TO PUBLIC;

-- Create basic users table
CREATE TABLE IF NOT EXISTS auth.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    roles JSONB DEFAULT '["user"]',
    permissions JSONB DEFAULT '["read"]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE
);

-- Create strategies table
CREATE TABLE IF NOT EXISTS cbsc.strategies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    strategy_type VARCHAR(100) NOT NULL,
    parameters JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    version INTEGER DEFAULT 1
);

-- Create performance metrics table
CREATE TABLE IF NOT EXISTS analytics.performance_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    strategy_id UUID REFERENCES cbsc.strategies(id),
    metric_type VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15,6) NOT NULL,
    metric_date DATE NOT NULL,
    additional_data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create configuration table
CREATE TABLE IF NOT EXISTS config.system_config (
    key VARCHAR(255) PRIMARY KEY,
    value JSONB NOT NULL,
    description TEXT,
    is_encrypted BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by UUID REFERENCES auth.users(id)
);

-- Insert default configuration
INSERT INTO config.system_config (key, value, description) VALUES
('system_version', '"2.0.0"', 'System version information'),
('maintenance_mode', 'false', 'System maintenance mode flag'),
('default_page_size', '50', 'Default pagination size'),
('max_upload_size', '52428800', 'Maximum upload file size in bytes (50MB)')
ON CONFLICT (key) DO NOTHING;

-- Create default admin user (password: admin123)
INSERT INTO auth.users (username, email, password_hash, roles, permissions, is_active, is_verified)
VALUES (
    'admin',
    'admin@cbsc.local',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.s5uO.G',  -- bcrypt hash of admin123
    '["admin", "user"]',
    '["read", "write", "delete", "admin"]',
    true,
    true
) ON CONFLICT (username) DO NOTHING;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_username ON auth.users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON auth.users(email);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON auth.users(is_active);
CREATE INDEX IF NOT EXISTS idx_strategies_type ON cbsc.strategies(strategy_type);
CREATE INDEX IF NOT EXISTS idx_strategies_active ON cbsc.strategies(is_active);
CREATE INDEX IF NOT EXISTS idx_performance_strategy_date ON analytics.performance_metrics(strategy_id, metric_date);
CREATE INDEX IF NOT EXISTS idx_config_updated_at ON config.system_config(updated_at);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON auth.users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_strategies_updated_at BEFORE UPDATE ON cbsc.strategies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_config_updated_at BEFORE UPDATE ON config.system_config
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create sample strategy data for development
INSERT INTO cbsc.strategies (name, description, strategy_type, parameters, is_active, version)
VALUES
    ('Moving Average Crossover', 'Simple moving average crossover strategy', 'technical', '{"short_period": 10, "long_period": 20, "symbols": ["AAPL", "GOOGL"]}', true, 1),
    ('RSI Mean Reversion', 'RSI-based mean reversion strategy', 'momentum', '{"rsi_period": 14, "oversold": 30, "overbought": 70, "symbols": ["TSLA", "MSFT"]}', true, 1),
    ('Bollinger Bands Breakout', 'Bollinger bands breakout strategy', 'volatility', '{"period": 20, "std_dev": 2, "symbols": ["AMZN", "NVDA"]}', false, 1)
ON CONFLICT DO NOTHING;

-- Create sample performance data
INSERT INTO analytics.performance_metrics (strategy_id, metric_type, metric_value, metric_date)
SELECT
    s.id,
    'sharpe_ratio',
    (random() * 2 + 0.5)::DECIMAL(15,6),
    CURRENT_DATE - INTERVAL '1 day' * (floor(random() * 30) + 1)
FROM cbsc.strategies s
LIMIT 10
ON CONFLICT DO NOTHING;

-- Create helpful views
CREATE OR REPLACE VIEW auth.active_users AS
SELECT id, username, email, roles, permissions, created_at, last_login
FROM auth.users
WHERE is_active = true AND is_verified = true;

CREATE OR REPLACE VIEW cbsc.active_strategies AS
SELECT id, name, description, strategy_type, created_at, version
FROM cbsc.strategies
WHERE is_active = true;

CREATE OR REPLACE VIEW analytics.strategy_summary AS
SELECT
    s.id as strategy_id,
    s.name as strategy_name,
    s.strategy_type,
    COUNT(pm.id) as metric_count,
    AVG(pm.metric_value) as avg_metric_value,
    MAX(pm.metric_date) as last_metric_date
FROM cbsc.strategies s
LEFT JOIN analytics.performance_metrics pm ON s.id = pm.strategy_id
WHERE s.is_active = true
GROUP BY s.id, s.name, s.strategy_type;

-- Grant permissions on views
GRANT SELECT ON auth.active_users TO PUBLIC;
GRANT SELECT ON cbsc.active_strategies TO PUBLIC;
GRANT SELECT ON analytics.strategy_summary TO PUBLIC;

-- Development-specific settings
ALTER SYSTEM SET log_statement = 'all';
ALTER SYSTEM SET log_min_duration_statement = 0;
SELECT pg_reload_conf();

-- Output initialization complete message
DO $$
BEGIN
    RAISE NOTICE 'CBSC Development Database initialized successfully';
    RAISE NOTICE 'Default admin user: admin / admin123';
    RAISE NOTICE 'Sample data has been created for testing';
END $$;