-- Migration: 002_create_market_data_tables
-- Description: Create market data, technical indicators, and sentiment data tables
-- Version: 1.0.0
-- Created: 2025-12-10
-- Author: CBSC Development Team

-- Create market data tables
CREATE TABLE IF NOT EXISTS market_data (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(20) NOT NULL,
    exchange VARCHAR(20) NOT NULL,
    asset_type VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    open_price NUMERIC(15,4) NOT NULL,
    high_price NUMERIC(15,4) NOT NULL,
    low_price NUMERIC(15,4) NOT NULL,
    close_price NUMERIC(15,4) NOT NULL,
    adjusted_close NUMERIC(15,4),
    volume INTEGER NOT NULL,
    turnover NUMERIC(20,2),
    vwap NUMERIC(15,4),
    market_cap NUMERIC(20,2),
    shares_outstanding INTEGER,
    pe_ratio NUMERIC(10,4),
    pb_ratio NUMERIC(10,4),
    dividend_yield NUMERIC(8,4),
    beta NUMERIC(6,4),
    data_source VARCHAR(50) NOT NULL,
    quality_score FLOAT DEFAULT 1.0 NOT NULL,
    is_adjusted BOOLEAN DEFAULT FALSE NOT NULL,
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

CREATE TABLE IF NOT EXISTS technical_indicators (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4(),
    market_data_id VARCHAR(36) REFERENCES market_data(id),
    symbol VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    indicator_type VARCHAR(50) NOT NULL,
    indicator_name VARCHAR(50) NOT NULL,
    period INTEGER,
    values JSONB NOT NULL,
    parameters JSONB,
    signal VARCHAR(20),
    confidence FLOAT,
    strength FLOAT,
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    calculation_method VARCHAR(50),
    data_points_used INTEGER,
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

CREATE TABLE IF NOT EXISTS sentiment_data (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(20) NOT NULL,
    source VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    overall_score FLOAT NOT NULL,
    sentiment_score FLOAT,
    fear_greed_index FLOAT,
    news_sentiment FLOAT,
    social_sentiment FLOAT,
    analyst_sentiment FLOAT,
    options_sentiment FLOAT,
    mention_count INTEGER DEFAULT 0 NOT NULL,
    positive_count INTEGER DEFAULT 0 NOT NULL,
    negative_count INTEGER DEFAULT 0 NOT NULL,
    neutral_count INTEGER DEFAULT 0 NOT NULL,
    weight FLOAT DEFAULT 1.0 NOT NULL,
    confidence FLOAT DEFAULT 1.0 NOT NULL,
    reliability_score FLOAT DEFAULT 1.0 NOT NULL,
    keywords JSONB,
    topics JSONB,
    collection_method VARCHAR(50),
    processing_algorithm VARCHAR(50),
    raw_data_reference VARCHAR(500),
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

CREATE TABLE IF NOT EXISTS economic_indicators (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4(),
    indicator_code VARCHAR(50) NOT NULL,
    indicator_name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    country VARCHAR(10) NOT NULL,
    value FLOAT NOT NULL,
    unit VARCHAR(20),
    period_type VARCHAR(20) NOT NULL,
    period_end_date TIMESTAMP WITH TIME ZONE NOT NULL,
    previous_value FLOAT,
    change_percent FLOAT,
    year_over_year FLOAT,
    forecast_value FLOAT,
    consensus_value FLOAT,
    surprise_percent FLOAT,
    importance_level VARCHAR(20) NOT NULL,
    market_impact JSONB,
    source VARCHAR(50) NOT NULL,
    release_time TIMESTAMP WITH TIME ZONE NOT NULL,
    reliability_score FLOAT DEFAULT 1.0 NOT NULL,
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

-- Create indexes for market data tables
CREATE INDEX IF NOT EXISTS idx_market_data_symbol_time ON market_data(symbol, timestamp, timeframe);
CREATE INDEX IF NOT EXISTS idx_market_data_exchange_symbol ON market_data(exchange, symbol, timestamp);
CREATE INDEX IF NOT EXISTS idx_market_data_timestamp_timeframe ON market_data(timestamp, timeframe);
CREATE INDEX IF NOT EXISTS idx_market_data_data_source ON market_data(data_source);

CREATE INDEX IF NOT EXISTS idx_technical_symbol_time ON technical_indicators(symbol, timestamp, indicator_name);
CREATE INDEX IF NOT EXISTS idx_technical_type_name ON technical_indicators(indicator_type, indicator_name, timestamp);
CREATE INDEX IF NOT EXISTS idx_technical_market_data ON technical_indicators(market_data_id);

CREATE INDEX IF NOT EXISTS idx_sentiment_symbol_time ON sentiment_data(symbol, timestamp, source);
CREATE INDEX IF NOT EXISTS idx_sentiment_overall_score ON sentiment_data(overall_score, timestamp);
CREATE INDEX IF NOT EXISTS idx_sentiment_source ON sentiment_data(source);

CREATE INDEX IF NOT EXISTS idx_economic_code_date ON economic_indicators(indicator_code, period_end_date);
CREATE INDEX IF NOT EXISTS idx_economic_category_date ON economic_indicators(category, period_end_date);
CREATE INDEX IF NOT EXISTS idx_economic_importance_date ON economic_indicators(importance_level, period_end_date);
CREATE INDEX IF NOT EXISTS idx_economic_country ON economic_indicators(country);

-- Create triggers for updated_at
CREATE TRIGGER update_market_data_updated_at BEFORE UPDATE ON market_data
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_technical_indicators_updated_at BEFORE UPDATE ON technical_indicators
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sentiment_data_updated_at BEFORE UPDATE ON sentiment_data
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_economic_indicators_updated_at BEFORE UPDATE ON economic_indicators
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add check constraints
ALTER TABLE market_data ADD CONSTRAINT chk_market_data_prices
    CHECK (high_price >= low_price AND high_price >= open_price AND high_price >= close_price
          AND low_price <= open_price AND low_price <= close_price AND volume >= 0);

ALTER TABLE market_data ADD CONSTRAINT chk_market_data_quality_score
    CHECK (quality_score >= 0.0 AND quality_score <= 1.0);

ALTER TABLE technical_indicators ADD CONSTRAINT chk_technical_confidence
    CHECK (confidence IS NULL OR (confidence >= 0.0 AND confidence <= 1.0));

ALTER TABLE technical_indicators ADD CONSTRAINT chk_technical_strength
    CHECK (strength IS NULL OR (strength >= 0.0 AND strength <= 1.0));

ALTER TABLE sentiment_data ADD CONSTRAINT chk_sentiment_scores
    CHECK (overall_score >= -1.0 AND overall_score <= 1.0
          AND (sentiment_score IS NULL OR (sentiment_score >= -1.0 AND sentiment_score <= 1.0))
          AND (fear_greed_index IS NULL OR (fear_greed_index >= 0.0 AND fear_greed_index <= 100.0)));

ALTER TABLE sentiment_data ADD CONSTRAINT chk_sentiment_counts
    CHECK (mention_count >= 0 AND positive_count >= 0 AND negative_count >= 0 AND neutral_count >= 0);

ALTER TABLE sentiment_data ADD CONSTRAINT chk_sentiment_weights
    CHECK (weight >= 0.0 AND confidence >= 0.0 AND confidence <= 1.0
          AND reliability_score >= 0.0 AND reliability_score <= 1.0);

-- Create partitioned table for large market data (PostgreSQL 10+)
-- This is optional and can be enabled based on data volume requirements
-- Uncomment the following if you need partitioning:

/*
-- Create partitioned table for market data (if using PostgreSQL 10+)
CREATE TABLE market_data_partitioned (
    LIKE market_data INCLUDING ALL
) PARTITION BY RANGE (timestamp);

-- Create monthly partitions
CREATE TABLE market_data_y2024m01 PARTITION OF market_data_partitioned
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE market_data_y2024m02 PARTITION OF market_data_partitioned
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

-- Add more partitions as needed
*/

-- Insert default economic indicator categories
INSERT INTO economic_indicators (indicator_code, indicator_name, category, country, value, unit, period_type, period_end_date, source, release_time, importance_level) VALUES
    ('GDP_US', 'US Gross Domestic Product', 'gdp', 'US', 0.0, 'trillion_usd', 'quarterly', NOW(), 'bea.gov', NOW(), 'critical'),
    ('CPI_US', 'US Consumer Price Index', 'inflation', 'US', 0.0, 'index', 'monthly', NOW(), 'bls.gov', NOW(), 'critical'),
    ('UNEMPLOYMENT_US', 'US Unemployment Rate', 'employment', 'US', 0.0, 'percent', 'monthly', NOW(), 'bls.gov', NOW(), 'high'),
    ('FED_FUNDS_RATE', 'Federal Funds Rate', 'interest_rate', 'US', 0.0, 'percent', 'daily', NOW(), 'federalreserve.gov', NOW(), 'critical'),
    ('HIBOR_HK', 'HK Interbank Offered Rate', 'interest_rate', 'HK', 0.0, 'percent', 'daily', NOW(), 'hkma.gov.hk', NOW(), 'high'),
    ('HSI_CLOSE', 'Hang Seng Index Close', 'market_index', 'HK', 0.0, 'points', 'daily', NOW(), 'hkex.com.hk', NOW(), 'high')
ON CONFLICT (indicator_code, period_end_date) DO NOTHING;

-- Create views for common queries
CREATE OR REPLACE VIEW v_market_data_latest AS
SELECT DISTINCT ON (symbol, timeframe)
    symbol,
    exchange,
    asset_type,
    timeframe,
    close_price,
    volume,
    timestamp,
    data_source,
    quality_score
FROM market_data
WHERE is_deleted = FALSE
ORDER BY symbol, timeframe, timestamp DESC;

CREATE OR REPLACE VIEW v_technical_indicators_latest AS
SELECT DISTINCT ON (symbol, indicator_name, timeframe)
    symbol,
    indicator_name,
    indicator_type,
    timeframe,
    values,
    signal,
    confidence,
    strength,
    timestamp
FROM technical_indicators
WHERE is_deleted = FALSE
ORDER BY symbol, indicator_name, timeframe, timestamp DESC;

CREATE OR REPLACE VIEW v_sentiment_data_latest AS
SELECT DISTINCT ON (symbol, source)
    symbol,
    source,
    overall_score,
    sentiment_score,
    fear_greed_index,
    mention_count,
    timestamp
FROM sentiment_data
WHERE is_deleted = FALSE
ORDER BY symbol, source, timestamp DESC;