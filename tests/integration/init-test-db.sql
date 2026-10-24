-- Initialize test database schema and data

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create indexes for better test performance
CREATE INDEX IF NOT EXISTS idx_strategies_user_id ON strategies(user_id);
CREATE INDEX IF NOT EXISTS idx_strategies_status ON strategies(status);
CREATE INDEX IF NOT EXISTS idx_strategies_created_at ON strategies(created_at);

CREATE INDEX IF NOT EXISTS idx_trades_user_id ON trades(user_id);
CREATE INDEX IF NOT EXISTS idx_trades_strategy_id ON trades(strategy_id);
CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol);
CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp);

CREATE INDEX IF NOT EXISTS idx_portfolios_user_id ON portfolios(user_id);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

-- Create test user for integration tests
INSERT INTO users (
    id,
    username,
    email,
    hashed_password,
    is_active,
    is_superuser,
    created_at,
    updated_at
) VALUES (
    uuid_generate_v4(),
    'testuser',
    'test@example.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewYcXaHqgD.sKhp2', -- password: testpassword
    true,
    false,
    NOW(),
    NOW()
) ON CONFLICT (username) DO NOTHING;

-- Create another test user for multi-user tests
INSERT INTO users (
    id,
    username,
    email,
    hashed_password,
    is_active,
    is_superuser,
    created_at,
    updated_at
) VALUES (
    uuid_generate_v4(),
    'testuser2',
    'test2@example.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewYcXaHqgD.sKhp2',
    true,
    false,
    NOW(),
    NOW()
) ON CONFLICT (username) DO NOTHING;

-- Create test admin user
INSERT INTO users (
    id,
    username,
    email,
    hashed_password,
    is_active,
    is_superuser,
    created_at,
    updated_at
) VALUES (
    uuid_generate_v4(),
    'testadmin',
    'admin@example.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewYcXaHqgD.sKhp2',
    true,
    true,
    NOW(),
    NOW()
) ON CONFLICT (username) DO NOTHING;

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO test_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO test_user;