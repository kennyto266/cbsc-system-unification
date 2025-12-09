-- Configuration Service Database Initialization
-- 配置服務數據庫初始化

-- 創建數據庫（如果不存在）
-- CREATE DATABASE IF NOT EXISTS config_service;

-- 使用配置服務數據庫
-- \c config_service;

-- 創建配置表
CREATE TABLE IF NOT EXISTS configs (
    id SERIAL PRIMARY KEY,
    key VARCHAR(255) NOT NULL,
    value JSONB NOT NULL,
    value_type VARCHAR(20) NOT NULL DEFAULT 'string',
    environment VARCHAR(20) NOT NULL DEFAULT 'development',
    service VARCHAR(50) NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    encrypted BOOLEAN NOT NULL DEFAULT FALSE,
    description TEXT,
    tags TEXT[],
    created_by VARCHAR(100) DEFAULT 'system',
    updated_by VARCHAR(100) DEFAULT 'system',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(key, environment, service)
);

-- 創建配置歷史表
CREATE TABLE IF NOT EXISTS config_history (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(255) NOT NULL,
    environment VARCHAR(20) NOT NULL,
    service VARCHAR(50) NOT NULL,
    old_value JSONB,
    new_value JSONB,
    changed_by VARCHAR(100) DEFAULT 'system',
    change_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    change_reason TEXT
);

-- 創建配置模板表
CREATE TABLE IF NOT EXISTS config_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    service VARCHAR(50) NOT NULL,
    environment VARCHAR(20) NOT NULL,
    config_schema JSONB NOT NULL,
    default_values JSONB NOT NULL,
    description TEXT,
    version VARCHAR(20) NOT NULL DEFAULT '1.0.0',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 創建索引
CREATE INDEX IF NOT EXISTS idx_configs_key_env_service ON configs(key, environment, service);
CREATE INDEX IF NOT EXISTS idx_configs_service ON configs(service);
CREATE INDEX IF NOT EXISTS idx_configs_environment ON configs(environment);
CREATE INDEX IF NOT EXISTS idx_configs_created_at ON configs(created_at);
CREATE INDEX IF NOT EXISTS idx_configs_updated_at ON configs(updated_at);
CREATE INDEX IF NOT EXISTS idx_configs_tags ON configs USING GIN(tags);

CREATE INDEX IF NOT EXISTS idx_config_history_config_key ON config_history(config_key);
CREATE INDEX IF NOT EXISTS idx_config_history_change_time ON config_history(change_time);
CREATE INDEX IF NOT EXISTS idx_config_history_service_env ON config_history(service, environment);

CREATE INDEX IF NOT EXISTS idx_config_templates_service ON config_templates(service);
CREATE INDEX IF NOT EXISTS idx_config_templates_environment ON config_templates(environment);

-- 創建觸發器以自動更新 updated_at 字段
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_configs_updated_at BEFORE UPDATE ON configs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_config_templates_updated_at BEFORE UPDATE ON config_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 插入默認配置模板

-- Data Service 模板
INSERT INTO config_templates (name, service, environment, config_schema, default_values, description)
VALUES (
    'data_service_template',
    'data',
    'development',
    '{
        "type": "object",
        "properties": {
            "data_source": {
                "type": "object",
                "properties": {
                    "timeout": {"type": "integer", "minimum": 1, "maximum": 3600},
                    "cache_ttl": {"type": "integer", "minimum": 0},
                    "retry_attempts": {"type": "integer", "minimum": 0, "maximum": 10},
                    "base_url": {"type": "string", "format": "uri"}
                }
            },
            "api": {
                "type": "object",
                "properties": {
                    "port": {"type": "integer", "minimum": 1, "maximum": 65535},
                    "workers": {"type": "integer", "minimum": 1},
                    "log_level": {"type": "string", "enum": ["DEBUG", "INFO", "WARNING", "ERROR"]}
                }
            }
        }
    }',
    '{
        "data_source": {
            "timeout": 30,
            "cache_ttl": 300,
            "retry_attempts": 3
        },
        "api": {
            "port": 8001,
            "workers": 4,
            "log_level": "INFO"
        }
    }',
    'Default configuration template for Data Service'
) ON CONFLICT (name) DO NOTHING;

-- Analytics Service 模板
INSERT INTO config_templates (name, service, environment, config_schema, default_values, description)
VALUES (
    'analytics_service_template',
    'analytics',
    'development',
    '{
        "type": "object",
        "properties": {
            "computation": {
                "type": "object",
                "properties": {
                    "parallel_workers": {"type": "integer", "minimum": 1},
                    "chunk_size": {"type": "integer", "minimum": 1},
                    "memory_limit": {"type": "string"},
                    "timeout": {"type": "integer", "minimum": 1}
                }
            },
            "algorithms": {
                "type": "object",
                "properties": {
                    "sharpe_ratio_risk_free_rate": {"type": "number", "minimum": 0},
                    "max_drawdown_threshold": {"type": "number", "minimum": 0, "maximum": 1}
                }
            }
        }
    }',
    '{
        "computation": {
            "parallel_workers": 4,
            "chunk_size": 1000,
            "memory_limit": "4GB",
            "timeout": 300
        },
        "algorithms": {
            "sharpe_ratio_risk_free_rate": 0.03,
            "max_drawdown_threshold": 0.1
        }
    }',
    'Default configuration template for Analytics Service'
) ON CONFLICT (name) DO NOTHING;

-- Backtest Service 模板
INSERT INTO config_templates (name, service, environment, config_schema, default_values, description)
VALUES (
    'backtest_service_template',
    'backtest',
    'development',
    '{
        "type": "object",
        "properties": {
            "vectorbt": {
                "type": "object",
                "properties": {
                    "chunk_size": {"type": "integer", "minimum": 1},
                    "parallel_cores": {"type": "integer", "minimum": 1},
                    "memory_limit": {"type": "string"}
                }
            },
            "performance": {
                "type": "object",
                "properties": {
                    "annualization_factor": {"type": "integer", "minimum": 1},
                    "risk_free_rate": {"type": "number", "minimum": 0}
                }
            }
        }
    }',
    '{
        "vectorbt": {
            "chunk_size": 10000,
            "parallel_cores": 4,
            "memory_limit": "8GB"
        },
        "performance": {
            "annualization_factor": 252,
            "risk_free_rate": 0.03
        }
    }',
    'Default configuration template for Backtest Service'
) ON CONFLICT (name) DO NOTHING;

-- Notification Service 模板
INSERT INTO config_templates (name, service, environment, config_schema, default_values, description)
VALUES (
    'notification_service_template',
    'notification',
    'development',
    '{
        "type": "object",
        "properties": {
            "telegram": {
                "type": "object",
                "properties": {
                    "bot_token": {"type": "string"},
                    "chat_id": {"type": "string"},
                    "enabled": {"type": "boolean"},
                    "timeout": {"type": "integer", "minimum": 1}
                }
            },
            "email": {
                "type": "object",
                "properties": {
                    "smtp_server": {"type": "string"},
                    "smtp_port": {"type": "integer", "minimum": 1, "maximum": 65535},
                    "username": {"type": "string"},
                    "password": {"type": "string"},
                    "enabled": {"type": "boolean"}
                }
            }
        }
    }',
    '{
        "telegram": {
            "enabled": false,
            "timeout": 30
        },
        "email": {
            "smtp_port": 587,
            "enabled": false
        }
    }',
    'Default configuration template for Notification Service'
) ON CONFLICT (name) DO NOTHING;

-- 插入示例全局配置
INSERT INTO configs (key, value, value_type, environment, service, description, tags)
VALUES
    ('sharpe_ratio.risk_free_rate', '0.03', 'float', 'development', 'global', 'Risk-free rate for Sharpe ratio calculation', ARRAY['sharpe', 'risk', 'calculation']),
    ('max_drawdown.default_threshold', '0.1', 'float', 'development', 'global', 'Default maximum drawdown threshold', ARRAY['drawdown', 'risk', 'threshold']),
    ('trading_days_per_year', '252', 'int', 'development', 'global', 'Number of trading days per year', ARRAY['trading', 'calendar', 'calculation']),
    ('default_currency', 'HKD', 'string', 'development', 'global', 'Default currency for trading', ARRAY['currency', 'trading', 'default']),
    ('log.default_level', 'INFO', 'string', 'development', 'global', 'Default logging level', ARRAY['logging', 'system', 'default'])
ON CONFLICT (key, environment, service) DO NOTHING;

-- 設置行級安全策略（可選，用於多租戶環境）
-- ALTER TABLE configs ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE config_history ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE config_templates ENABLE ROW LEVEL SECURITY;

-- 創建視圖用於簡化查詢
CREATE OR REPLACE VIEW config_summary AS
SELECT
    service,
    environment,
    COUNT(*) as total_configs,
    COUNT(CASE WHEN encrypted = TRUE THEN 1 END) as encrypted_configs,
    COUNT(CASE WHEN created_at > NOW() - INTERVAL '24 hours' THEN 1 END) as recent_configs,
    MAX(updated_at) as last_update
FROM configs
GROUP BY service, environment;

-- 創建統計函數
CREATE OR REPLACE FUNCTION get_service_metrics(service_param VARCHAR DEFAULT NULL)
RETURNS TABLE(
    total_configs BIGINT,
    encrypted_configs BIGINT,
    recent_configs BIGINT,
    last_update TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*),
        COUNT(CASE WHEN encrypted = TRUE THEN 1 END),
        COUNT(CASE WHEN created_at > NOW() - INTERVAL '24 hours' THEN 1 END),
        MAX(updated_at)
    FROM configs
    WHERE (service_param IS NULL OR service = service_param);
END;
$$ LANGUAGE plpgsql;

-- 創建配置變更審計函數
CREATE OR REPLACE FUNCTION audit_config_change()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'UPDATE' THEN
        INSERT INTO config_history (config_key, environment, service, old_value, new_value, changed_by, change_reason)
        VALUES (NEW.key, NEW.environment, NEW.service, OLD.value, NEW.value, NEW.updated_by, 'Configuration updated via UPDATE');
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO config_history (config_key, environment, service, old_value, changed_by, change_reason)
        VALUES (OLD.key, OLD.environment, OLD.service, OLD.value, OLD.updated_by, 'Configuration deleted');
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- 創建審計觸發器
CREATE TRIGGER audit_config_changes
    AFTER UPDATE OR DELETE ON configs
    FOR EACH ROW EXECUTE FUNCTION audit_config_change();

-- 創建配置備份函數
CREATE OR REPLACE FUNCTION backup_configs(backup_name TEXT)
RETURNS TEXT AS $$
DECLARE
    backup_file TEXT;
BEGIN
    backup_file := 'config_backup_' || backup_name || '_' || to_char(NOW(), 'YYYY-MM-DD_HH24-MI-SS') || '.json';

    -- 這裡可以添加實際的備份邏輯
    -- 例如：使用COPY命令導出數據到文件

    RETURN backup_file;
END;
$$ LANGUAGE plpgsql;

COMMENT ON TABLE configs IS 'Configuration storage table with environment and service isolation';
COMMENT ON TABLE config_history IS 'Audit trail for all configuration changes';
COMMENT ON TABLE config_templates IS 'Configuration templates for different services and environments';
COMMENT ON VIEW config_summary IS 'Summary view of configuration statistics by service and environment';