-- Migration: Create partitioned trades table
-- Version: 002
-- Description: Convert trades table to monthly partitions
-- Created: 2025-12-11

-- Create backup of original table
CREATE TABLE IF NOT EXISTS trades_backup AS
SELECT * FROM trades;

-- Create partitioned table
CREATE TABLE trades_partitioned (
    -- UUID primary key from unified base
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Metadata from unified base
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID,
    updated_by UUID,
    is_deleted BOOLEAN DEFAULT FALSE,
    version INTEGER DEFAULT 1,
    metadata JSONB,

    -- Foreign keys
    order_id UUID NOT NULL,
    user_id UUID,
    portfolio_id UUID,

    -- Trade basic information
    symbol VARCHAR(20) NOT NULL,
    exchange VARCHAR(20) NOT NULL,
    asset_type VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL,  -- 'buy' or 'sell'

    -- Trade quantity and price
    quantity INTEGER NOT NULL,
    price DECIMAL(15,4) NOT NULL,
    notional DECIMAL(15,4) NOT NULL,

    -- Execution time and ID
    trade_time TIMESTAMP WITH TIME ZONE NOT NULL,
    external_trade_id VARCHAR(100),
    execution_venue VARCHAR(50),

    -- Costs and fees
    commission DECIMAL(15,4) DEFAULT 0 NOT NULL,
    slippage DECIMAL(15,4) DEFAULT 0 NOT NULL,
    taxes DECIMAL(15,4) DEFAULT 0 NOT NULL,
    total_cost DECIMAL(15,4) NOT NULL,

    -- Settlement information
    settlement_date TIMESTAMP WITH TIME ZONE,
    settlement_currency VARCHAR(10),
    fx_rate DECIMAL(12,6) DEFAULT 1.0 NOT NULL,

    -- Trade reason and analysis
    trade_reason VARCHAR(100),
    strategy_signal JSONB,
    market_conditions JSONB,

    -- Audit information
    broker_reference VARCHAR(100),
    clearing_firm VARCHAR(100)
) PARTITION BY RANGE (trade_time);

-- Create indexes
CREATE INDEX idx_trades_partitioned_time ON trades_partitioned (trade_time);
CREATE INDEX idx_trades_partitioned_symbol ON trades_partitioned (symbol);
CREATE INDEX idx_trades_partitioned_order ON trades_partitioned (order_id);
CREATE INDEX idx_trades_partitioned_portfolio ON trades_partitioned (portfolio_id);
CREATE INDEX idx_trades_partitioned_user ON trades_partitioned (user_id);

-- Composite indexes for common queries
CREATE INDEX idx_trades_partitioned_symbol_time ON trades_partitioned (symbol, trade_time);
CREATE INDEX idx_trades_partitioned_portfolio_time ON trades_partitioned (portfolio_id, trade_time);

-- Create foreign key constraints
ALTER TABLE trades_partitioned
ADD CONSTRAINT fk_trades_order
FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE;

ALTER TABLE trades_partitioned
ADD CONSTRAINT fk_trades_user
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;

ALTER TABLE trades_partitioned
ADD CONSTRAINT fk_trades_portfolio
FOREIGN KEY (portfolio_id) REFERENCES portfolios(id) ON DELETE SET NULL;

-- Create initial partitions (current year + 1 year ahead)
DO $$
DECLARE
    start_date TIMESTAMP WITH TIME ZONE;
    end_date TIMESTAMP WITH TIME ZONE;
    partition_name TEXT;
BEGIN
    -- Create partitions for current month and next 11 months
    FOR i IN 0..11 LOOP
        start_date := DATE_TRUNC('month', CURRENT_TIMESTAMP + INTERVAL '1 month' * i);
        end_date := start_date + INTERVAL '1 month';
        partition_name := 'trades_y' || EXTRACT(YEAR FROM start_date) || '_m' || LPAD(EXTRACT(MONTH FROM start_date)::TEXT, 2, '0');

        EXECUTE format('
            CREATE TABLE IF NOT EXISTS %I PARTITION OF trades_partitioned
            FOR VALUES FROM (%L) TO (%L)',
            partition_name, start_date, end_date
        );

        -- Create partition-specific indexes
        EXECUTE format('
            CREATE INDEX IF NOT EXISTS idx_%s_symbol
            ON %I (symbol)',
            partition_name, partition_name
        );

        EXECUTE format('
            CREATE INDEX IF NOT EXISTS idx_%s_portfolio
            ON %I (portfolio_id)',
            partition_name, partition_name
        );
    END LOOP;

    -- Create partitions for historical data (2 years back)
    FOR i IN -24..-1 LOOP
        start_date := DATE_TRUNC('month', CURRENT_TIMESTAMP + INTERVAL '1 month' * i);
        end_date := start_date + INTERVAL '1 month';
        partition_name := 'trades_y' || EXTRACT(YEAR FROM start_date) || '_m' || LPAD(EXTRACT(MONTH FROM start_date)::TEXT, 2, '0');

        EXECUTE format('
            CREATE TABLE IF NOT EXISTS %I PARTITION OF trades_partitioned
            FOR VALUES FROM (%L) TO (%L)',
            partition_name, start_date, end_date
        );
    END LOOP;
END $$;

-- Create trigger to automatically create new partitions
CREATE OR REPLACE FUNCTION create_trades_monthly_partition()
RETURNS TRIGGER AS $$
DECLARE
    start_date TIMESTAMP WITH TIME ZONE;
    end_date TIMESTAMP WITH TIME ZONE;
    partition_name TEXT;
BEGIN
    -- Check if partition exists for the new trade_time
    start_date := DATE_TRUNC('month', NEW.trade_time);
    partition_name := 'trades_y' || EXTRACT(YEAR FROM start_date) || '_m' || LPAD(EXTRACT(MONTH FROM start_date)::TEXT, 2, '0');

    IF NOT EXISTS (
        SELECT 1 FROM pg_tables
        WHERE tablename = partition_name
    ) THEN
        end_date := start_date + INTERVAL '1 month';

        EXECUTE format('
            CREATE TABLE %I PARTITION OF trades_partitioned
            FOR VALUES FROM (%L) TO (%L)',
            partition_name, start_date, end_date
        );

        EXECUTE format('
            CREATE INDEX idx_%s_symbol
            ON %I (symbol)',
            partition_name, partition_name
        );

        EXECUTE format('
            CREATE INDEX idx_%s_portfolio
            ON %I (portfolio_id)',
            partition_name, partition_name
        );

        RAISE NOTICE 'Created new trades partition: %', partition_name;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger
CREATE TRIGGER trigger_create_trades_partition
BEFORE INSERT ON trades_partitioned
FOR EACH ROW EXECUTE FUNCTION create_trades_monthly_partition();

-- Create function to migrate data from old table
CREATE OR REPLACE FUNCTION migrate_trades_data(
    p_batch_size INTEGER DEFAULT 10000,
    p_date_from TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    p_date_to TIMESTAMP WITH TIME ZONE DEFAULT NULL
)
RETURNS JSONB AS $$
DECLARE
    v_total_migrated INTEGER := 0;
    v_batch_count INTEGER := 0;
    v_start_time TIMESTAMP := NOW();
    v_min_date TIMESTAMP WITH TIME ZONE;
    v_max_date TIMESTAMP WITH TIME ZONE;
BEGIN
    -- Get date range if not provided
    IF p_date_from IS NULL THEN
        SELECT MIN(trade_time) INTO v_min_date FROM trades_backup;
    ELSE
        v_min_date := p_date_from;
    END IF;

    IF p_date_to IS NULL THEN
        SELECT MAX(trade_time) INTO v_max_date FROM trades_backup;
    ELSE
        v_max_date := p_date_to;
    END IF;

    -- Migrate data in batches by hour
    WHILE v_min_date <= v_max_date LOOP
        -- Insert batch
        INSERT INTO trades_partitioned (
            id, created_at, updated_at, created_by, updated_by, is_deleted, version, metadata,
            order_id, user_id, portfolio_id, symbol, exchange, asset_type, side,
            quantity, price, notional, trade_time, external_trade_id, execution_venue,
            commission, slippage, taxes, total_cost, settlement_date, settlement_currency,
            fx_rate, trade_reason, strategy_signal, market_conditions, broker_reference, clearing_firm
        )
        SELECT
            id, created_at, updated_at, created_by, updated_by, is_deleted, version, metadata,
            order_id, user_id, portfolio_id, symbol, exchange, asset_type, side,
            quantity, price, notional, trade_time, external_trade_id, execution_venue,
            commission, slippage, taxes, total_cost, settlement_date, settlement_currency,
            fx_rate, trade_reason, strategy_signal, market_conditions, broker_reference, clearing_firm
        FROM trades_backup
        WHERE trade_time >= v_min_date
          AND trade_time < v_min_date + INTERVAL '1 hour'
        LIMIT p_batch_size;

        v_batch_count := v_batch_count + 1;
        GET DIAGNOSTICS v_total_migrated = ROW_COUNT;

        -- Move to next hour
        v_min_date := v_min_date + INTERVAL '1 hour';

        -- Log progress every 100 batches
        IF v_batch_count % 100 = 0 THEN
            RAISE NOTICE 'Migrated % batches, % total trades', v_batch_count, v_total_migrated;
        END IF;
    END LOOP;

    -- Return migration statistics
    RETURN jsonb_build_object(
        'total_migrated', v_total_migrated,
        'batch_count', v_batch_count,
        'execution_time_seconds', EXTRACT(EPOCH FROM (NOW() - v_start_time)),
        'date_from', p_date_from,
        'date_to', p_date_to
    );
END;
$$ LANGUAGE plpgsql;

-- Create view for backward compatibility
CREATE OR REPLACE VIEW trades AS
SELECT * FROM trades_partitioned;

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON trades_partitioned TO cbsc_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON trades TO cbsc_app;