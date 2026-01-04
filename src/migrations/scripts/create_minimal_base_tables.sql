-- Minimal base tables for strategy management
-- 策略管理基礎表結構

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    email_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    last_login TIMESTAMP WITH TIME ZONE,
    metadata JSONB
);

-- Create strategies table
CREATE TABLE IF NOT EXISTS strategies (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(200) NOT NULL,
    code VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    strategy_type VARCHAR(50) NOT NULL,
    version VARCHAR(20) DEFAULT '1.0.0' NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    is_system BOOLEAN DEFAULT FALSE NOT NULL,
    author_id VARCHAR(36),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    created_by VARCHAR(36),
    updated_by VARCHAR(36),
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    deleted_at TIMESTAMP WITH TIME ZONE,
    deleted_by VARCHAR(36),
    version INTEGER DEFAULT 1 NOT NULL,
    metadata JSONB,
    config_schema JSONB,
    parameters_template JSONB
);

-- Create strategy_categories table
CREATE TABLE IF NOT EXISTS strategy_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(200) NOT NULL,
    description TEXT,
    parent_id INTEGER REFERENCES strategy_categories(id),
    level INTEGER DEFAULT 1 NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Insert default categories
INSERT INTO strategy_categories (name, display_name, description, level) VALUES
    ('technical_indicators', 'Technical Indicators', 'Strategies based on technical analysis indicators', 1),
    ('momentum', 'Momentum Strategies', 'Strategies that exploit market momentum', 1),
    ('mean_reversion', 'Mean Reversion', 'Strategies that bet on price reversion to mean', 1)
ON CONFLICT (name) DO NOTHING;

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);

CREATE INDEX IF NOT EXISTS idx_strategies_code ON strategies(code);
CREATE INDEX IF NOT EXISTS idx_strategies_type ON strategies(strategy_type);
CREATE INDEX IF NOT EXISTS idx_strategies_active ON strategies(is_active, is_deleted);
CREATE INDEX IF NOT EXISTS idx_strategies_author ON strategies(author_id);

CREATE INDEX IF NOT EXISTS idx_strategy_categories_parent ON strategy_categories(parent_id);
CREATE INDEX IF NOT EXISTS idx_strategy_categories_level ON strategy_categories(level);

-- Create trigger for updated_at (optional, can be handled by application)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_strategies_updated_at
    BEFORE UPDATE ON strategies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_strategy_categories_updated_at
    BEFORE UPDATE ON strategy_categories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();