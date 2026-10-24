-- Migration: 001_create_base_tables
-- Description: Create base tables for CBSC unified database
-- Version: 1.0.0
-- Created: 2025-12-10
-- Author: CBSC Development Team

-- Enable UUID extension for PostgreSQL
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create custom types
CREATE TYPE IF NOT EXISTS order_type AS ENUM ('market', 'limit', 'stop', 'stop_limit', 'trailing_stop');
CREATE TYPE IF NOT EXISTS order_side AS ENUM ('buy', 'sell');
CREATE TYPE IF NOT EXISTS order_status AS ENUM ('pending', 'submitted', 'partial_filled', 'filled', 'cancelled', 'rejected', 'expired');
CREATE TYPE IF NOT EXISTS position_side AS ENUM ('long', 'short');
CREATE TYPE IF NOT EXISTS strategy_status AS ENUM ('active', 'inactive', 'testing', 'archived');
CREATE TYPE IF NOT EXISTS risk_level AS ENUM ('low', 'medium', 'high', 'extreme');
CREATE TYPE IF NOT EXISTS report_type AS ENUM ('performance', 'risk', 'compliance', 'audit', 'backtest', 'strategy', 'portfolio');
CREATE TYPE IF NOT EXISTS log_level AS ENUM ('debug', 'info', 'warning', 'error', 'critical');

-- Create user and permission tables
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    display_name VARCHAR(200),
    avatar_url VARCHAR(500),
    phone VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    is_verified BOOLEAN DEFAULT FALSE NOT NULL,
    is_premium BOOLEAN DEFAULT FALSE NOT NULL,
    mfa_enabled BOOLEAN DEFAULT FALSE NOT NULL,
    mfa_secret VARCHAR(32),
    failed_login_attempts INTEGER DEFAULT 0 NOT NULL,
    locked_until TIMESTAMP WITH TIME ZONE,
    last_login_at TIMESTAMP WITH TIME ZONE,
    last_login_ip VARCHAR(45),
    timezone VARCHAR(50) DEFAULT 'UTC' NOT NULL,
    language VARCHAR(10) DEFAULT 'en' NOT NULL,
    theme VARCHAR(20) DEFAULT 'light' NOT NULL,
    notifications JSONB,
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

CREATE TABLE IF NOT EXISTS roles (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(50) UNIQUE NOT NULL,
    display_name VARCHAR(200) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    is_system_role BOOLEAN DEFAULT FALSE NOT NULL,
    level INTEGER DEFAULT 0 NOT NULL,
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

CREATE TABLE IF NOT EXISTS permissions (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL,
    resource VARCHAR(50) NOT NULL,
    action VARCHAR(50) NOT NULL,
    level INTEGER DEFAULT 0 NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    is_system_permission BOOLEAN DEFAULT FALSE NOT NULL,
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

-- Create many-to-many relationship tables
CREATE TABLE IF NOT EXISTS user_roles (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(36) NOT NULL REFERENCES users(id),
    role_id VARCHAR(36) NOT NULL REFERENCES roles(id),
    assigned_by VARCHAR(36),
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    created_by VARCHAR(36),
    updated_by VARCHAR(36),
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    deleted_at TIMESTAMP WITH TIME ZONE,
    deleted_by VARCHAR(36),
    version INTEGER DEFAULT 1 NOT NULL,
    metadata JSONB,
    PRIMARY KEY (user_id, role_id)
);

CREATE TABLE IF NOT EXISTS role_permissions (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4(),
    role_id VARCHAR(36) NOT NULL REFERENCES roles(id),
    permission_id VARCHAR(36) NOT NULL REFERENCES permissions(id),
    granted_by VARCHAR(36),
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    created_by VARCHAR(36),
    updated_by VARCHAR(36),
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    deleted_at TIMESTAMP WITH TIME ZONE,
    deleted_by VARCHAR(36),
    version INTEGER DEFAULT 1 NOT NULL,
    metadata JSONB,
    PRIMARY KEY (role_id, permission_id)
);

-- Create strategy management tables
CREATE TABLE IF NOT EXISTS strategy_categories (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(200) NOT NULL,
    description TEXT,
    parent_id VARCHAR(36) REFERENCES strategy_categories(id),
    level INTEGER DEFAULT 0 NOT NULL,
    sort_order INTEGER DEFAULT 0 NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
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

CREATE TABLE IF NOT EXISTS strategies (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(200) NOT NULL,
    code VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    category_id VARCHAR(36) REFERENCES strategy_categories(id),
    strategy_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'inactive' NOT NULL,
    risk_level VARCHAR(20) DEFAULT 'medium' NOT NULL,
    total_return FLOAT DEFAULT 0.0 NOT NULL,
    sharpe_ratio FLOAT,
    max_drawdown FLOAT DEFAULT 0.0 NOT NULL,
    win_rate FLOAT DEFAULT 0.0 NOT NULL,
    profit_factor FLOAT,
    volatility FLOAT,
    default_parameters JSONB,
    required_indicators JSONB,
    supported_timeframes JSONB,
    version_str VARCHAR(20) DEFAULT '1.0.0' NOT NULL,
    is_public BOOLEAN DEFAULT FALSE NOT NULL,
    total_users INTEGER DEFAULT 0 NOT NULL,
    active_users INTEGER DEFAULT 0 NOT NULL,
    total_signals INTEGER DEFAULT 0 NOT NULL,
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

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active, is_deleted);
CREATE INDEX IF NOT EXISTS idx_strategies_code ON strategies(code);
CREATE INDEX IF NOT EXISTS idx_strategies_type_status ON strategies(strategy_type, status);
CREATE INDEX IF NOT EXISTS idx_strategies_category ON strategies(category_id);
CREATE INDEX IF NOT EXISTS idx_permissions_code ON permissions(code);
CREATE INDEX IF NOT EXISTS idx_permissions_category ON permissions(category, resource, action);

-- Create triggers for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_roles_updated_at BEFORE UPDATE ON roles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_permissions_updated_at BEFORE UPDATE ON permissions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_strategy_categories_updated_at BEFORE UPDATE ON strategy_categories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_strategies_updated_at BEFORE UPDATE ON strategies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default system roles and permissions
INSERT INTO roles (name, display_name, description, is_system_role, level) VALUES
    ('super_admin', 'Super Administrator', 'Full system access with all permissions', TRUE, 1000),
    ('admin', 'Administrator', 'Administrative access to most system functions', TRUE, 800),
    ('manager', 'Manager', 'Managerial access with limited administrative functions', TRUE, 600),
    ('trader', 'Trader', 'Trading and strategy management access', TRUE, 400),
    ('analyst', 'Analyst', 'Read-only access to analysis and reports', TRUE, 200),
    ('viewer', 'Viewer', 'Basic read-only access', TRUE, 100)
ON CONFLICT (name) DO NOTHING;

-- Insert default system permissions
INSERT INTO permissions (code, name, description, category, resource, action, level, is_system_permission) VALUES
    -- User management
    ('user.create', 'Create User', 'Create new user accounts', 'user', 'user', 'create', 800, TRUE),
    ('user.read', 'Read User', 'View user information', 'user', 'user', 'read', 100, TRUE),
    ('user.update', 'Update User', 'Update user information', 'user', 'user', 'update', 400, TRUE),
    ('user.delete', 'Delete User', 'Delete user accounts', 'user', 'user', 'delete', 800, TRUE),

    -- Strategy management
    ('strategy.create', 'Create Strategy', 'Create new trading strategies', 'strategy', 'strategy', 'create', 400, TRUE),
    ('strategy.read', 'Read Strategy', 'View strategy information', 'strategy', 'strategy', 'read', 100, TRUE),
    ('strategy.update', 'Update Strategy', 'Update strategy configuration', 'strategy', 'strategy', 'update', 400, TRUE),
    ('strategy.delete', 'Delete Strategy', 'Delete strategies', 'strategy', 'strategy', 'delete', 600, TRUE),

    -- Portfolio management
    ('portfolio.create', 'Create Portfolio', 'Create new portfolios', 'portfolio', 'portfolio', 'create', 400, TRUE),
    ('portfolio.read', 'Read Portfolio', 'View portfolio information', 'portfolio', 'portfolio', 'read', 100, TRUE),
    ('portfolio.update', 'Update Portfolio', 'Update portfolio configuration', 'portfolio', 'portfolio', 'update', 400, TRUE),
    ('portfolio.delete', 'Delete Portfolio', 'Delete portfolios', 'portfolio', 'portfolio', 'delete', 600, TRUE),

    -- Trading operations
    ('trade.create', 'Create Trade', 'Execute trades', 'trading', 'trade', 'create', 400, TRUE),
    ('trade.read', 'Read Trade', 'View trade information', 'trading', 'trade', 'read', 100, TRUE),
    ('trade.update', 'Update Trade', 'Update trade information', 'trading', 'trade', 'update', 400, TRUE),

    -- System management
    ('system.config', 'System Configuration', 'Access system configuration', 'system', 'config', 'manage', 800, TRUE),
    ('system.audit', 'System Audit', 'View audit logs', 'system', 'audit', 'read', 600, TRUE),
    ('system.monitor', 'System Monitoring', 'Access system monitoring', 'system', 'monitor', 'read', 400, TRUE)
ON CONFLICT (code) DO NOTHING;

-- Insert default admin user (password: admin123 - should be changed in production)
INSERT INTO users (username, email, password_hash, first_name, last_name, display_name, is_active, is_verified, is_premium) VALUES
    ('admin', 'admin@cbsc.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6hsxq9w5Ku', 'System', 'Administrator', 'System Administrator', TRUE, TRUE, TRUE)
ON CONFLICT (username) DO NOTHING;

-- Assign admin role to admin user
INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id
FROM users u, roles r
WHERE u.username = 'admin' AND r.name = 'super_admin'
ON CONFLICT (user_id, role_id) DO NOTHING;

-- Assign all permissions to super admin role
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.name = 'super_admin'
ON CONFLICT (role_id, permission_id) DO NOTHING;