-- Migration 004: Create Authentication v2 Tables
-- Migration 004: 創建認證 v2 表結構

-- Start transaction
BEGIN;

-- Create user_mfa table for MFA configuration
-- 創建用戶多因子認證配置表
CREATE TABLE IF NOT EXISTS user_mfa (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    mfa_type VARCHAR(20) NOT NULL CHECK (mfa_type IN ('totp', 'email', 'sms')),
    secret VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(20),
    is_enabled BOOLEAN DEFAULT FALSE,
    backup_codes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP WITH TIME ZONE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(user_id, mfa_type)
);

-- Create refresh_tokens table for JWT refresh tokens
-- 創建刷新令牌表
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id SERIAL PRIMARY KEY,
    token_id VARCHAR(255) UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    device_name VARCHAR(100),
    device_fingerprint VARCHAR(255),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_revoked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create login_attempts table for rate limiting and security
-- 創建登入嘗試記錄表用於速率限制和安全監控
CREATE TABLE IF NOT EXISTS login_attempts (
    id SERIAL PRIMARY KEY,
    ip_address INET NOT NULL,
    username VARCHAR(50) NOT NULL,
    attempt_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    success BOOLEAN NOT NULL,
    user_agent TEXT,
    failure_reason VARCHAR(100)
);

-- Create indexes for better performance
-- 創建索引以提高性能

-- Index for user_mfa
CREATE INDEX IF NOT EXISTS idx_user_mfa_user_id ON user_mfa(user_id);
CREATE INDEX IF NOT EXISTS idx_user_mfa_enabled ON user_mfa(user_id, is_enabled);

-- Index for refresh_tokens
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_token_id ON refresh_tokens(token_id);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_expires ON refresh_tokens(expires_at);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_active ON refresh_tokens(user_id, is_revoked, expires_at);

-- Index for login_attempts
CREATE INDEX IF NOT EXISTS idx_login_attempts_ip ON login_attempts(ip_address);
CREATE INDEX IF NOT EXISTS idx_login_attempts_username ON login_attempts(username);
CREATE INDEX IF NOT EXISTS idx_login_attempts_time ON login_attempts(attempt_time);
CREATE INDEX IF NOT EXISTS idx_login_attempts_recent ON login_attempts(ip_address, attempt_time) WHERE attempt_time > CURRENT_TIMESTAMP - INTERVAL '1 hour';

-- Create audit_log table for security events
-- 創建安全事件審計日誌表
CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    user_id INTEGER,
    ip_address INET,
    user_agent TEXT,
    details JSONB,
    risk_level VARCHAR(20) DEFAULT 'low' CHECK (risk_level IN ('low', 'medium', 'high', 'critical')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Indexes for audit_log
CREATE INDEX IF NOT EXISTS idx_audit_log_event_type ON audit_log(event_type);
CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON audit_log(created_at);
CREATE INDEX IF NOT EXISTS idx_audit_log_risk_level ON audit_log(risk_level);

-- Create api_keys table for API authentication
-- 創建 API 密鑰表
CREATE TABLE IF NOT EXISTS api_keys (
    id SERIAL PRIMARY KEY,
    key_id VARCHAR(100) UNIQUE NOT NULL,
    api_key_hash VARCHAR(255) NOT NULL,
    user_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    permissions TEXT[] DEFAULT '{}',
    expires_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    last_used TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

-- Indexes for api_keys
CREATE INDEX IF NOT EXISTS idx_api_keys_key_id ON api_keys(key_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_active ON api_keys(user_id, is_active);

-- Add columns to existing users table if they don't exist
-- 如果 users 表中不存在以下欄位，則添加

DO $$
BEGIN
    -- Add full_name column
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='users' AND column_name='full_name'
    ) THEN
        ALTER TABLE users ADD COLUMN full_name VARCHAR(100);
    END IF;

    -- Add is_verified column
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='users' AND column_name='is_verified'
    ) THEN
        ALTER TABLE users ADD COLUMN is_verified BOOLEAN DEFAULT FALSE;
    END IF;

    -- Add verification_token column
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='users' AND column_name='verification_token'
    ) THEN
        ALTER TABLE users ADD COLUMN verification_token VARCHAR(255);
    END IF;

    -- Add reset_token column
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='users' AND column_name='reset_token'
    ) THEN
        ALTER TABLE users ADD COLUMN reset_token VARCHAR(255);
    END IF;

    -- Add reset_token_expires column
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='users' AND column_name='reset_token_expires'
    ) THEN
        ALTER TABLE users ADD COLUMN reset_token_expires TIMESTAMP WITH TIME ZONE;
    END IF;

    -- Add two_factor_secret column (legacy)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='users' AND column_name='two_factor_secret'
    ) THEN
        ALTER TABLE users ADD COLUMN two_factor_secret VARCHAR(255);
    END IF;
END $$;

-- Create or update function to clean up expired refresh tokens
-- 創建或更新清理過期刷新令牌的函數
CREATE OR REPLACE FUNCTION cleanup_expired_tokens()
RETURNS void AS $$
BEGIN
    -- Delete expired refresh tokens
    DELETE FROM refresh_tokens
    WHERE expires_at < CURRENT_TIMESTAMP - INTERVAL '7 days';

    -- Delete old login attempts (older than 30 days)
    DELETE FROM login_attempts
    WHERE attempt_time < CURRENT_TIMESTAMP - INTERVAL '30 days';

    -- Log the cleanup
    INSERT INTO audit_log (event_type, details, created_at)
    VALUES ('token_cleanup', jsonb_build_object('timestamp', CURRENT_TIMESTAMP), CURRENT_TIMESTAMP);
END;
$$ LANGUAGE plpgsql;

-- Add comments to tables
-- 為表添加註釋
COMMENT ON TABLE user_mfa IS 'User MFA configuration settings';
COMMENT ON TABLE refresh_tokens IS 'JWT refresh tokens for session management';
COMMENT ON TABLE login_attempts IS 'Login attempt tracking for rate limiting and security';
COMMENT ON TABLE audit_log IS 'Security audit log for important events';
COMMENT ON TABLE api_keys IS 'API keys for programmatic access';

-- Create view for active sessions
-- 創建活躍會話視圖
CREATE OR REPLACE VIEW active_sessions AS
SELECT
    rt.id,
    rt.user_id,
    u.username,
    u.email,
    rt.device_name,
    rt.device_fingerprint,
    rt.created_at,
    rt.last_used,
    rt.expires_at,
    CASE
        WHEN rt.expires_at < CURRENT_TIMESTAMP THEN 'expired'
        WHEN rt.is_revoked THEN 'revoked'
        ELSE 'active'
    END as status
FROM refresh_tokens rt
JOIN users u ON rt.user_id = u.id
WHERE rt.is_revoked = FALSE;

-- Grant permissions if using PostgreSQL
-- 如果使用 PostgreSQL，授予權限
-- GRANT SELECT, INSERT, UPDATE, DELETE ON user_mfa, refresh_tokens, login_attempts, audit_log, api_keys TO your_app_user;

-- Commit transaction
COMMIT;

-- Log migration success
-- 記錄遷移成功
INSERT INTO audit_log (event_type, details, created_at)
VALUES ('migration', jsonb_build_object('migration', '004', 'description', 'Auth v2 tables created'), CURRENT_TIMESTAMP);