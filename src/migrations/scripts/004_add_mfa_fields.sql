-- Add MFA fields to users table
-- Migration script for adding multi-factor authentication support

-- Add MFA related columns to users table
ALTER TABLE users
ADD COLUMN IF NOT EXISTS mfa_enabled BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS mfa_type VARCHAR(20) NULL, -- 'totp', 'sms', 'email'
ADD COLUMN IF NOT EXISTS mfa_secret VARCHAR(255) NULL, -- Encrypted TOTP secret
ADD COLUMN IF NOT EXISTS mfa_backup_codes TEXT NULL, -- Encrypted backup codes
ADD COLUMN IF NOT EXISTS mfa_phone_verified BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS mfa_preferences JSONB NULL, -- MFA settings preferences

-- Add temporary columns for MFA setup flow
ALTER TABLE users
ADD COLUMN IF NOT EXISTS email_verification_code VARCHAR(10) NULL,
ADD COLUMN IF NOT EXISTS email_verification_expires TIMESTAMPTZ NULL,
ADD COLUMN IF NOT EXISTS login_verification_code VARCHAR(10) NULL,
ADD COLUMN IF NOT EXISTS login_verification_expires TIMESTAMPTZ NULL,
ADD COLUMN IF NOT EXISTS operation_verification_code VARCHAR(10) NULL,
ADD COLUMN IF NOT EXISTS operation_verification_expires TIMESTAMPTZ NULL,
ADD COLUMN IF NOT EXISTS operation_type VARCHAR(50) NULL,
ADD COLUMN IF NOT EXISTS totp_secret_temp VARCHAR(255) NULL,
ADD COLUMN IF NOT EXISTS totp_backup_codes_temp TEXT NULL,
ADD COLUMN IF NOT EXISTS backup_code_regeneration_required BOOLEAN DEFAULT FALSE;

-- Add indexes for MFA fields
CREATE INDEX IF NOT EXISTS idx_users_mfa_enabled ON users(mfa_enabled);
CREATE INDEX IF NOT EXISTS idx_users_mfa_type ON users(mfa_type);
CREATE INDEX IF NOT EXISTS idx_users_email_verification_expires ON users(email_verification_expires);
CREATE INDEX IF NOT EXISTS idx_users_login_verification_expires ON users(login_verification_expires);
CREATE INDEX IF NOT EXISTS idx_users_operation_verification_expires ON users(operation_verification_expires);

-- Create MFA sessions table for tracking MFA verification sessions
CREATE TABLE IF NOT EXISTS mfa_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    mfa_type VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending', -- 'pending', 'verified', 'expired', 'failed'
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    verified_at TIMESTAMPTZ NULL,
    ip_address INET NULL,
    user_agent TEXT NULL,
    attempt_count INTEGER NOT NULL DEFAULT 0,
    max_attempts INTEGER NOT NULL DEFAULT 3,
    metadata JSONB NULL
);

-- Add indexes for mfa_sessions
CREATE INDEX IF NOT EXISTS idx_mfa_sessions_user_id ON mfa_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_mfa_sessions_token ON mfa_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_mfa_sessions_status ON mfa_sessions(status);
CREATE INDEX IF NOT EXISTS idx_mfa_sessions_expires_at ON mfa_sessions(expires_at);

-- Create MFA trusted devices table
CREATE TABLE IF NOT EXISTS mfa_trusted_devices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    device_fingerprint VARCHAR(255) NOT NULL,
    device_name VARCHAR(100) NULL,
    device_type VARCHAR(50) NULL, -- 'mobile', 'desktop', 'tablet'
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_used_at TIMESTAMPTZ NULL,
    expires_at TIMESTAMPTZ NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ip_address INET NULL,
    user_agent TEXT NULL,
    metadata JSONB NULL
);

-- Add indexes for mfa_trusted_devices
CREATE INDEX IF NOT EXISTS idx_mfa_trusted_devices_user_id ON mfa_trusted_devices(user_id);
CREATE INDEX IF NOT EXISTS idx_mfa_trusted_devices_fingerprint ON mfa_trusted_devices(device_fingerprint);
CREATE INDEX IF NOT EXISTS idx_mfa_trusted_devices_active ON mfa_trusted_devices(is_active);
CREATE INDEX IF NOT EXISTS idx_mfa_trusted_devices_expires_at ON mfa_trusted_devices(expires_at);

-- Create MFA audit log table
CREATE TABLE IF NOT EXISTS mfa_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    action VARCHAR(50) NOT NULL, -- 'enable', 'disable', 'verify', 'failed_attempt'
    mfa_type VARCHAR(20) NULL,
    status VARCHAR(20) NOT NULL, -- 'success', 'failed', 'bypass'
    ip_address INET NULL,
    user_agent TEXT NULL,
    error_message TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB NULL
);

-- Add indexes for mfa_audit_log
CREATE INDEX IF NOT EXISTS idx_mfa_audit_log_user_id ON mfa_audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_mfa_audit_log_action ON mfa_audit_log(action);
CREATE INDEX IF NOT EXISTS idx_mfa_audit_log_status ON mfa_audit_log(status);
CREATE INDEX IF NOT EXISTS idx_mfa_audit_log_created_at ON mfa_audit_log(created_at);

-- Create user_security_settings table for per-user security preferences
CREATE TABLE IF NOT EXISTS user_security_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- MFA requirements
    require_mfa_for_login BOOLEAN DEFAULT FALSE,
    require_mfa_for_sensitive_operations BOOLEAN DEFAULT TRUE,

    -- MFA methods preferences
    preferred_mfa_method VARCHAR(20) NULL, -- 'totp', 'sms', 'email'
    allow_backup_codes BOOLEAN DEFAULT TRUE,

    -- Trusted device settings
    enable_trusted_devices BOOLEAN DEFAULT TRUE,
    trusted_device_duration_days INTEGER DEFAULT 30,

    -- Session security
    session_timeout_minutes INTEGER DEFAULT 480, -- 8 hours
    max_concurrent_sessions INTEGER DEFAULT 5,

    -- Notification settings
    notify_on_new_device BOOLEAN DEFAULT TRUE,
    notify_on_failed_login BOOLEAN DEFAULT TRUE,

    -- Created/Updated timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Add indexes for user_security_settings
CREATE INDEX IF NOT EXISTS idx_user_security_settings_user_id ON user_security_settings(user_id);

-- Insert default security settings for existing users
INSERT INTO user_security_settings (user_id)
SELECT id FROM users
WHERE id NOT IN (SELECT user_id FROM user_security_settings);

-- Create or update trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_user_security_settings_updated_at
    BEFORE UPDATE ON user_security_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add comments
COMMENT ON TABLE mfa_sessions IS 'Stores MFA verification sessions for users';
COMMENT ON TABLE mfa_trusted_devices IS 'Stores trusted devices for users to skip MFA';
COMMENT ON TABLE mfa_audit_log IS 'Audit log for all MFA related activities';
COMMENT ON TABLE user_security_settings IS 'Per-user security preferences and MFA settings';

-- Add comments for columns
COMMENT ON COLUMN users.mfa_enabled IS 'Whether MFA is enabled for the user';
COMMENT ON COLUMN users.mfa_type IS 'Type of MFA enabled (totp, sms, email)';
COMMENT ON COLUMN users.mfa_secret IS 'Encrypted TOTP secret';
COMMENT ON COLUMN users.mfa_backup_codes IS 'Encrypted backup codes for TOTP';
COMMENT ON COLUMN users.mfa_phone_verified IS 'Whether phone number is verified for SMS MFA';
COMMENT ON COLUMN users.mfa_preferences IS 'User preferences for MFA (JSON)';

COMMIT;