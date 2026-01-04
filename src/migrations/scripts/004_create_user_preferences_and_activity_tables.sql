-- Migration: 004_create_user_preferences_and_activity_tables.sql
-- Description: Create user preferences and activity tracking tables
-- Created: 2025-12-18
-- Version: 1.0

-- Start transaction
BEGIN;

-- Create user_preferences table
CREATE TABLE IF NOT EXISTS user_preferences (
    id VARCHAR(36) PRIMARY KEY DEFAULT (uuid_generate_v4()),
    user_id VARCHAR(36) NOT NULL UNIQUE,

    -- Interface preferences
    theme VARCHAR(20) DEFAULT 'light' NOT NULL,
    primary_color VARCHAR(7) DEFAULT '#3B82F6' NOT NULL,
    accent_color VARCHAR(7) DEFAULT '#10B981' NOT NULL,
    font_size VARCHAR(10) DEFAULT 'medium' NOT NULL,
    font_family VARCHAR(50) DEFAULT 'Inter' NOT NULL,
    sidebar_collapsed BOOLEAN DEFAULT FALSE NOT NULL,

    -- Language and region
    language VARCHAR(10) DEFAULT 'zh-TW' NOT NULL,
    timezone VARCHAR(50) DEFAULT 'Asia/Taipei' NOT NULL,
    date_format VARCHAR(20) DEFAULT 'YYYY-MM-DD' NOT NULL,
    time_format VARCHAR(10) DEFAULT '24h' NOT NULL,
    number_format VARCHAR(10) DEFAULT '1,234.56' NOT NULL,
    currency VARCHAR(3) DEFAULT 'TWD' NOT NULL,

    -- Dashboard preferences
    default_dashboard VARCHAR(50) DEFAULT 'overview' NOT NULL,
    widget_layout JSONB,
    refresh_interval INTEGER DEFAULT 30 NOT NULL,
    auto_refresh_enabled BOOLEAN DEFAULT TRUE NOT NULL,

    -- Table preferences
    table_page_size INTEGER DEFAULT 20 NOT NULL,
    table_density VARCHAR(10) DEFAULT 'medium' NOT NULL,
    table_pagination_enabled BOOLEAN DEFAULT TRUE NOT NULL,

    -- Common fields
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by VARCHAR(36),
    updated_by VARCHAR(36),

    -- Foreign key constraint
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,

    -- Indexes
    INDEX idx_user_preferences_user_id (user_id),
    INDEX idx_user_preferences_created_at (created_at)
);

-- Create notification_preferences table
CREATE TABLE IF NOT EXISTS notification_preferences (
    id VARCHAR(36) PRIMARY KEY DEFAULT (uuid_generate_v4()),
    user_preference_id VARCHAR(36) NOT NULL,

    -- Notification type and category
    notification_type VARCHAR(50) NOT NULL,
    category VARCHAR(50) NOT NULL,

    -- Settings
    enabled BOOLEAN DEFAULT TRUE NOT NULL,
    frequency VARCHAR(20) DEFAULT 'immediate' NOT NULL,
    digest_time VARCHAR(5) DEFAULT '09:00' NOT NULL,
    digest_timezone VARCHAR(50) DEFAULT 'Asia/Taipei' NOT NULL,

    -- Channel settings
    email_enabled BOOLEAN DEFAULT TRUE NOT NULL,
    sms_enabled BOOLEAN DEFAULT FALSE NOT NULL,
    push_enabled BOOLEAN DEFAULT TRUE NOT NULL,
    in_app_enabled BOOLEAN DEFAULT TRUE NOT NULL,

    -- Filters
    min_severity VARCHAR(10) DEFAULT 'info' NOT NULL,
    max_frequency_per_hour INTEGER DEFAULT 10 NOT NULL,

    -- Additional settings
    settings JSONB,

    -- Common fields
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by VARCHAR(36),
    updated_by VARCHAR(36),

    -- Foreign key constraint
    FOREIGN KEY (user_preference_id) REFERENCES user_preferences(id) ON DELETE CASCADE,

    -- Indexes
    INDEX idx_notification_preferences_user_pref_id (user_preference_id),
    INDEX idx_notification_preferences_type (notification_type),
    INDEX idx_notification_preferences_category (category),

    -- Unique constraint
    UNIQUE(user_preference_id, notification_type, category)
);

-- Create user_widgets table
CREATE TABLE IF NOT EXISTS user_widgets (
    id VARCHAR(36) PRIMARY KEY DEFAULT (uuid_generate_v4()),
    user_id VARCHAR(36) NOT NULL,

    -- Widget information
    widget_id VARCHAR(100) NOT NULL,
    widget_name VARCHAR(100) NOT NULL,
    widget_type VARCHAR(50) NOT NULL,
    dashboard VARCHAR(50) DEFAULT 'main' NOT NULL,

    -- Position and size
    position_x INTEGER DEFAULT 0 NOT NULL,
    position_y INTEGER DEFAULT 0 NOT NULL,
    width INTEGER DEFAULT 4 NOT NULL,
    height INTEGER DEFAULT 3 NOT NULL,

    -- Configuration
    config JSONB,
    data_source JSONB,
    refresh_interval INTEGER DEFAULT 30 NOT NULL,

    -- Status
    is_visible BOOLEAN DEFAULT TRUE NOT NULL,
    is_collapsed BOOLEAN DEFAULT FALSE NOT NULL,

    -- Sorting
    sort_order INTEGER DEFAULT 0 NOT NULL,

    -- Common fields
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by VARCHAR(36),
    updated_by VARCHAR(36),

    -- Foreign key constraint
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,

    -- Indexes
    INDEX idx_user_widgets_user_id (user_id),
    INDEX idx_user_widgets_dashboard (dashboard),
    INDEX idx_user_widgets_type (widget_type),
    INDEX idx_user_widgets_sort_order (sort_order)
);

-- Create user_shortcuts table
CREATE TABLE IF NOT EXISTS user_shortcuts (
    id VARCHAR(36) PRIMARY KEY DEFAULT (uuid_generate_v4()),
    user_id VARCHAR(36) NOT NULL,

    -- Shortcut information
    name VARCHAR(100) NOT NULL,
    description TEXT,
    url VARCHAR(500) NOT NULL,
    icon VARCHAR(100),

    -- Category
    category VARCHAR(50) DEFAULT 'custom' NOT NULL,

    -- Status
    is_visible BOOLEAN DEFAULT TRUE NOT NULL,
    opens_in_new_tab BOOLEAN DEFAULT FALSE NOT NULL,

    -- Sorting
    sort_order INTEGER DEFAULT 0 NOT NULL,

    -- Common fields
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by VARCHAR(36),
    updated_by VARCHAR(36),

    -- Foreign key constraint
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,

    -- Indexes
    INDEX idx_user_shortcuts_user_id (user_id),
    INDEX idx_user_shortcuts_category (category),
    INDEX idx_user_shortcuts_sort_order (sort_order)
);

-- Create user_activities table
CREATE TABLE IF NOT EXISTS user_activities (
    id VARCHAR(36) PRIMARY KEY DEFAULT (uuid_generate_v4()),
    user_id VARCHAR(36) NOT NULL,

    -- Activity information
    activity_type VARCHAR(50) NOT NULL,
    action VARCHAR(100) NOT NULL,
    resource VARCHAR(100),
    resource_id VARCHAR(36),

    -- Context information
    session_id VARCHAR(255),
    ip_address VARCHAR(45),
    user_agent TEXT,
    referrer VARCHAR(500),

    -- Page information
    page_url VARCHAR(500),
    page_title VARCHAR(200),
    page_category VARCHAR(50),

    -- Feature information
    feature VARCHAR(100),
    module VARCHAR(50),
    component VARCHAR(100),

    -- Performance
    response_time DOUBLE PRECISION,
    load_time DOUBLE PRECISION,

    -- Status
    status VARCHAR(20) DEFAULT 'success' NOT NULL,
    error_code VARCHAR(50),
    error_message TEXT,

    -- Additional data
    metadata JSONB,
    tags JSONB,

    -- Common fields
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by VARCHAR(36),
    updated_by VARCHAR(36),

    -- Foreign key constraint
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,

    -- Indexes
    INDEX idx_user_activities_user_id (user_id),
    INDEX idx_user_activities_type (activity_type),
    INDEX idx_user_activities_action (action),
    INDEX idx_user_activities_feature (feature),
    INDEX idx_user_activities_module (module),
    INDEX idx_user_activities_status (status),
    INDEX idx_user_activities_session_id (session_id),
    INDEX idx_user_activities_created_at (created_at)
);

-- Create user_sessions table
CREATE TABLE IF NOT EXISTS user_sessions (
    id VARCHAR(36) PRIMARY KEY DEFAULT (uuid_generate_v4()),
    user_id VARCHAR(36) NOT NULL,

    -- Session information
    session_id VARCHAR(255) NOT NULL UNIQUE,
    session_token VARCHAR(255) NOT NULL UNIQUE,

    -- Time information
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    last_activity_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    ended_at TIMESTAMP WITH TIME ZONE,

    -- Session statistics
    duration INTEGER,
    page_views INTEGER DEFAULT 0 NOT NULL,
    clicks INTEGER DEFAULT 0 NOT NULL,
    api_calls INTEGER DEFAULT 0 NOT NULL,
    errors INTEGER DEFAULT 0 NOT NULL,

    -- Context information
    ip_address VARCHAR(45),
    user_agent TEXT,
    device_type VARCHAR(50),
    browser VARCHAR(50),
    browser_version VARCHAR(20),
    os VARCHAR(50),
    os_version VARCHAR(20),
    location JSONB,

    -- Status
    is_active BOOLEAN DEFAULT TRUE NOT NULL,

    -- Common fields
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by VARCHAR(36),
    updated_by VARCHAR(36),

    -- Foreign key constraint
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,

    -- Indexes
    INDEX idx_user_sessions_user_id (user_id),
    INDEX idx_user_sessions_session_id (session_id),
    INDEX idx_user_sessions_is_active (is_active),
    INDEX idx_user_sessions_started_at (started_at),
    INDEX idx_user_sessions_last_activity_at (last_activity_at)
);

-- Create user_behavior_patterns table
CREATE TABLE IF NOT EXISTS user_behavior_patterns (
    id VARCHAR(36) PRIMARY KEY DEFAULT (uuid_generate_v4()),
    user_id VARCHAR(36) NOT NULL,

    -- Pattern information
    pattern_type VARCHAR(50) NOT NULL,
    pattern_name VARCHAR(100) NOT NULL,
    pattern_value JSONB NOT NULL,

    -- Statistics
    confidence DOUBLE PRECISION DEFAULT 0.0 NOT NULL,
    frequency DOUBLE PRECISION DEFAULT 0.0 NOT NULL,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,

    -- Status
    is_active BOOLEAN DEFAULT TRUE NOT NULL,

    -- Common fields
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by VARCHAR(36),
    updated_by VARCHAR(36),

    -- Foreign key constraint
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,

    -- Indexes
    INDEX idx_user_behavior_patterns_user_id (user_id),
    INDEX idx_user_behavior_patterns_type (pattern_type),
    INDEX idx_user_behavior_patterns_is_active (is_active),
    INDEX idx_user_behavior_patterns_last_updated (last_updated)
);

-- Create user_feature_usage table
CREATE TABLE IF NOT EXISTS user_feature_usage (
    id VARCHAR(36) PRIMARY KEY DEFAULT (uuid_generate_v4()),
    user_id VARCHAR(36) NOT NULL,

    -- Feature information
    feature VARCHAR(100) NOT NULL,
    module VARCHAR(50) NOT NULL,
    component VARCHAR(100),

    -- Statistics period
    period_type VARCHAR(10) NOT NULL,
    period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    period_end TIMESTAMP WITH TIME ZONE NOT NULL,

    -- Usage statistics
    usage_count INTEGER DEFAULT 0 NOT NULL,
    total_time DOUBLE PRECISION DEFAULT 0.0 NOT NULL,
    avg_session_time DOUBLE PRECISION DEFAULT 0.0 NOT NULL,

    -- Success statistics
    success_count INTEGER DEFAULT 0 NOT NULL,
    error_count INTEGER DEFAULT 0 NOT NULL,
    success_rate DOUBLE PRECISION DEFAULT 0.0 NOT NULL,

    -- Additional statistics
    unique_days_used INTEGER DEFAULT 0 NOT NULL,
    peak_usage_time VARCHAR(5),
    preferred_devices JSONB,

    -- Common fields
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by VARCHAR(36),
    updated_by VARCHAR(36),

    -- Foreign key constraint
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,

    -- Indexes
    INDEX idx_user_feature_usage_user_id (user_id),
    INDEX idx_user_feature_usage_feature (feature),
    INDEX idx_user_feature_usage_module (module),
    INDEX idx_user_feature_usage_period_type (period_type),
    INDEX idx_user_feature_usage_period_start (period_start),
    INDEX idx_user_feature_usage_period_end (period_end),

    -- Unique constraint
    UNIQUE(user_id, feature, period_type, period_start)
);

-- Create user_personas table
CREATE TABLE IF NOT EXISTS user_personas (
    id VARCHAR(36) PRIMARY KEY DEFAULT (uuid_generate_v4()),
    user_id VARCHAR(36) NOT NULL UNIQUE,

    -- User type and category
    user_type VARCHAR(50) NOT NULL,
    user_category VARCHAR(50) NOT NULL,

    -- Preferences
    preferred_features JSONB,
    usage_patterns JSONB,
    work_schedule JSONB,

    -- Skill levels
    technical_skill_level INTEGER DEFAULT 0 NOT NULL,
    trading_experience INTEGER DEFAULT 0 NOT NULL,
    familiarity_score DOUBLE PRECISION DEFAULT 0.0 NOT NULL,

    -- Behavioral traits
    risk_appetite VARCHAR(20) DEFAULT 'moderate' NOT NULL,
    decision_style VARCHAR(20),
    learning_style VARCHAR(20),

    -- Engagement
    engagement_score DOUBLE PRECISION DEFAULT 0.0 NOT NULL,
    activity_level VARCHAR(20) DEFAULT 'normal' NOT NULL,
    retention_score DOUBLE PRECISION DEFAULT 0.0 NOT NULL,

    -- Predictions
    churn_risk DOUBLE PRECISION DEFAULT 0.0 NOT NULL,
    upsell_opportunity DOUBLE PRECISION DEFAULT 0.0 NOT NULL,
    next_actions JSONB,

    -- Update information
    last_analyzed TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    analysis_version VARCHAR(20) DEFAULT '1.0' NOT NULL,

    -- Common fields
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by VARCHAR(36),
    updated_by VARCHAR(36),

    -- Foreign key constraint
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,

    -- Indexes
    INDEX idx_user_personas_user_id (user_id),
    INDEX idx_user_personas_user_type (user_type),
    INDEX idx_user_personas_user_category (user_category),
    INDEX idx_user_personas_last_analyzed (last_analyzed)
);

-- Create user_engagement_metrics table
CREATE TABLE IF NOT EXISTS user_engagement_metrics (
    id VARCHAR(36) PRIMARY KEY DEFAULT (uuid_generate_v4()),
    user_id VARCHAR(36) NOT NULL,

    -- Time period
    metric_date TIMESTAMP WITH TIME ZONE NOT NULL,
    period_type VARCHAR(10) NOT NULL,

    -- Activity metrics
    active_days INTEGER DEFAULT 0 NOT NULL,
    total_sessions INTEGER DEFAULT 0 NOT NULL,
    avg_session_duration DOUBLE PRECISION DEFAULT 0.0 NOT NULL,
    total_interactions INTEGER DEFAULT 0 NOT NULL,

    -- Feature usage
    features_used INTEGER DEFAULT 0 NOT NULL,
    new_features_tried INTEGER DEFAULT 0 NOT NULL,
    core_feature_usage JSONB,

    -- Content engagement
    reports_generated INTEGER DEFAULT 0 NOT NULL,
    strategies_created INTEGER DEFAULT 0 NOT NULL,
    backtests_run INTEGER DEFAULT 0 NOT NULL,

    -- Social engagement
    shares INTEGER DEFAULT 0 NOT NULL,
    comments INTEGER DEFAULT 0 NOT NULL,
    feedback_given INTEGER DEFAULT 0 NOT NULL,

    -- Quality metrics
    error_rate DOUBLE PRECISION DEFAULT 0.0 NOT NULL,
    satisfaction_score DOUBLE PRECISION,
    net_promoter_score INTEGER,

    -- Common fields
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by VARCHAR(36),
    updated_by VARCHAR(36),

    -- Foreign key constraint
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,

    -- Indexes
    INDEX idx_user_engagement_metrics_user_id (user_id),
    INDEX idx_user_engagement_metrics_metric_date (metric_date),
    INDEX idx_user_engagement_metrics_period_type (period_type),

    -- Unique constraint
    UNIQUE(user_id, metric_date, period_type)
);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_user_preferences_updated_at BEFORE UPDATE ON user_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_notification_preferences_updated_at BEFORE UPDATE ON notification_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_widgets_updated_at BEFORE UPDATE ON user_widgets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_shortcuts_updated_at BEFORE UPDATE ON user_shortcuts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_activities_updated_at BEFORE UPDATE ON user_activities
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_sessions_updated_at BEFORE UPDATE ON user_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_behavior_patterns_updated_at BEFORE UPDATE ON user_behavior_patterns
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_feature_usage_updated_at BEFORE UPDATE ON user_feature_usage
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_personas_updated_at BEFORE UPDATE ON user_personas
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_engagement_metrics_updated_at BEFORE UPDATE ON user_engagement_metrics
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create partitioned table for user_activities (optional, for high volume)
-- This will create monthly partitions
DO $$
BEGIN
    -- Check if the table is already partitioned
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_name = 'user_activities'
        AND table_schema = 'public'
        AND is_partitioned = true
    ) THEN
        -- Enable partitioning
        ALTER TABLE user_activities SET (autovacuum_enabled = true, fillfactor = 90);
    END IF;
END $$;

-- Insert initial notification preference templates
INSERT INTO notification_preferences (user_preference_id, notification_type, category, enabled, frequency)
SELECT
    p.id,
    'email',
    'system',
    true,
    'immediate'
FROM user_preferences p
ON CONFLICT (user_preference_id, notification_type, category) DO NOTHING;

INSERT INTO notification_preferences (user_preference_id, notification_type, category, enabled, frequency)
SELECT
    p.id,
    'push',
    'system',
    true,
    'immediate'
FROM user_preferences p
ON CONFLICT (user_preference_id, notification_type, category) DO NOTHING;

INSERT INTO notification_preferences (user_preference_id, notification_type, category, enabled, frequency)
SELECT
    p.id,
    'email',
    'strategy',
    true,
    'daily'
FROM user_preferences p
ON CONFLICT (user_preference_id, notification_type, category) DO NOTHING;

-- Commit transaction
COMMIT;

-- Log migration completion
DO $$
BEGIN
    RAISE NOTICE 'Migration 004: Created user preferences and activity tracking tables successfully';
END $$;