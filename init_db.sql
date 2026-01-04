-- CBSC Database Initialization Script
-- CBSC 數據庫初始化腳本

-- Create migrations tracking table
CREATE TABLE IF NOT EXISTS migrations (
    id SERIAL PRIMARY KEY,
    version VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    applied_at TIMESTAMP DEFAULT NOW()
);

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Log initialization
INSERT INTO migrations (version, description) VALUES
    ('001', 'Database initialized'),
    ('002', 'Extensions created')
ON CONFLICT (version) DO NOTHING;
