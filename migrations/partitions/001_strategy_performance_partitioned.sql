-- Migration: Create partitioned strategy_performance table
-- Version: 001
-- Description: Convert strategy_performance table to monthly partitions
-- Created: 2025-12-11

-- Create backup of original table
CREATE TABLE IF NOT EXISTS strategy_performance_backup AS
SELECT * FROM strategy_performance;

-- Create partitioned table
CREATE TABLE strategy_performance_partitioned (
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
    strategy_id UUID NOT NULL,
    config_id UUID,

    -- Performance data
    date DATE NOT NULL,
    total_return DECIMAL(15,6) NOT NULL,
    daily_return DECIMAL(10,6),
    cumulative_return DECIMAL(15,6) NOT NULL,
    benchmark_return DECIMAL(10,6),
    alpha DECIMAL(10,6),

    -- Risk metrics
    volatility DECIMAL(10,6),
    sharpe_ratio DECIMAL(8,4),
    sortino_ratio DECIMAL(8,4),
    max_drawdown DECIMAL(10,6),
    var_95 DECIMAL(10,6),
    cvar_95 DECIMAL(10,6),

    -- Trading statistics
    total_trades INTEGER DEFAULT 0 NOT NULL,
    winning_trades INTEGER DEFAULT 0 NOT NULL,
    win_rate DECIMAL(5,4) DEFAULT 0.0 NOT NULL,
    profit_factor DECIMAL(8,4),
    average_win DECIMAL(15,6),
    average_loss DECIMAL(15,6),

    -- Position information
    current_positions INTEGER DEFAULT 0 NOT NULL,
    open_positions_value DECIMAL(20,4) DEFAULT 0.0 NOT NULL,
    cash_balance DECIMAL(20,4) DEFAULT 0.0 NOT NULL,

    -- Metadata
    market_conditions JSONB,
    data_quality_score DECIMAL(3,2) DEFAULT 1.0 NOT NULL
) PARTITION BY RANGE (date);

-- Create indexes
CREATE INDEX idx_strategy_perf_partitioned_strategy_date ON strategy_performance_partitioned (strategy_id, date);
CREATE INDEX idx_strategy_perf_partitioned_date ON strategy_performance_partitioned (date);
CREATE INDEX idx_strategy_perf_partitioned_config ON strategy_performance_partitioned (config_id);

-- Create foreign key constraints
ALTER TABLE strategy_performance_partitioned
ADD CONSTRAINT fk_strategy_perf_strategy
FOREIGN KEY (strategy_id) REFERENCES strategies(id) ON DELETE CASCADE;

ALTER TABLE strategy_performance_partitioned
ADD CONSTRAINT fk_strategy_perf_config
FOREIGN KEY (config_id) REFERENCES strategy_configs(id) ON DELETE SET NULL;

-- Create initial partitions (current year + 1 year ahead)
DO $$
DECLARE
    start_date DATE;
    end_date DATE;
    partition_name TEXT;
BEGIN
    -- Create partitions for current month and next 11 months
    FOR i IN 0..11 LOOP
        start_date := DATE_TRUNC('month', CURRENT_DATE + INTERVAL '1 month' * i);
        end_date := start_date + INTERVAL '1 month';
        partition_name := 'strategy_performance_y' || EXTRACT(YEAR FROM start_date) || '_m' || LPAD(EXTRACT(MONTH FROM start_date)::TEXT, 2, '0');

        EXECUTE format('
            CREATE TABLE IF NOT EXISTS %I PARTITION OF strategy_performance_partitioned
            FOR VALUES FROM (%L) TO (%L)',
            partition_name, start_date, end_date
        );

        -- Create partition-specific indexes
        EXECUTE format('
            CREATE INDEX IF NOT EXISTS idx_%s_strategy
            ON %I (strategy_id)',
            partition_name, partition_name
        );
    END LOOP;

    -- Create partitions for historical data (2 years back)
    FOR i IN -24..-1 LOOP
        start_date := DATE_TRUNC('month', CURRENT_DATE + INTERVAL '1 month' * i);
        end_date := start_date + INTERVAL '1 month';
        partition_name := 'strategy_performance_y' || EXTRACT(YEAR FROM start_date) || '_m' || LPAD(EXTRACT(MONTH FROM start_date)::TEXT, 2, '0');

        EXECUTE format('
            CREATE TABLE IF NOT EXISTS %I PARTITION OF strategy_performance_partitioned
            FOR VALUES FROM (%L) TO (%L)',
            partition_name, start_date, end_date
        );
    END LOOP;
END $$;

-- Create trigger to automatically create new partitions
CREATE OR REPLACE FUNCTION create_monthly_partition()
RETURNS TRIGGER AS $$
DECLARE
    start_date DATE;
    end_date DATE;
    partition_name TEXT;
BEGIN
    -- Check if partition exists for the new date
    start_date := DATE_TRUNC('month', NEW.date);
    partition_name := 'strategy_performance_y' || EXTRACT(YEAR FROM start_date) || '_m' || LPAD(EXTRACT(MONTH FROM start_date)::TEXT, 2, '0');

    IF NOT EXISTS (
        SELECT 1 FROM pg_tables
        WHERE tablename = partition_name
    ) THEN
        end_date := start_date + INTERVAL '1 month';

        EXECUTE format('
            CREATE TABLE %I PARTITION OF strategy_performance_partitioned
            FOR VALUES FROM (%L) TO (%L)',
            partition_name, start_date, end_date
        );

        EXECUTE format('
            CREATE INDEX idx_%s_strategy
            ON %I (strategy_id)',
            partition_name, partition_name
        );

        RAISE NOTICE 'Created new partition: %', partition_name;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger
CREATE TRIGGER trigger_create_strategy_performance_partition
BEFORE INSERT ON strategy_performance_partitioned
FOR EACH ROW EXECUTE FUNCTION create_monthly_partition();

-- Create function to migrate data from old table
CREATE OR REPLACE FUNCTION migrate_strategy_performance_data(
    p_batch_size INTEGER DEFAULT 10000,
    p_date_from DATE DEFAULT NULL,
    p_date_to DATE DEFAULT NULL
)
RETURNS JSONB AS $$
DECLARE
    v_total_migrated INTEGER := 0;
    v_batch_count INTEGER := 0;
    v_start_time TIMESTAMP := NOW();
    v_min_date DATE;
    v_max_date DATE;
BEGIN
    -- Get date range if not provided
    IF p_date_from IS NULL THEN
        SELECT MIN(date) INTO v_min_date FROM strategy_performance_backup;
    ELSE
        v_min_date := p_date_from;
    END IF;

    IF p_date_to IS NULL THEN
        SELECT MAX(date) INTO v_max_date FROM strategy_performance_backup;
    ELSE
        v_max_date := p_date_to;
    END IF;

    -- Migrate data in batches
    WHILE v_min_date <= v_max_date LOOP
        -- Insert batch
        INSERT INTO strategy_performance_partitioned (
            id, created_at, updated_at, created_by, updated_by, is_deleted, version, metadata,
            strategy_id, config_id, date, total_return, daily_return, cumulative_return,
            benchmark_return, alpha, volatility, sharpe_ratio, sortino_ratio, max_drawdown,
            var_95, cvar_95, total_trades, winning_trades, win_rate, profit_factor,
            average_win, average_loss, current_positions, open_positions_value, cash_balance,
            market_conditions, data_quality_score
        )
        SELECT
            id, created_at, updated_at, created_by, updated_by, is_deleted, version, metadata,
            strategy_id, config_id, date, total_return, daily_return, cumulative_return,
            benchmark_return, alpha, volatility, sharpe_ratio, sortino_ratio, max_drawdown,
            var_95, cvar_95, total_trades, winning_trades, win_rate, profit_factor,
            average_win, average_loss, current_positions, open_positions_value, cash_balance,
            market_conditions, data_quality_score
        FROM strategy_performance_backup
        WHERE date >= v_min_date
          AND date < v_min_date + INTERVAL '1 day'
        LIMIT p_batch_size;

        v_batch_count := v_batch_count + 1;
        GET DIAGNOSTICS v_total_migrated = ROW_COUNT;

        -- Move to next day
        v_min_date := v_min_date + INTERVAL '1 day';

        -- Log progress every 100 batches
        IF v_batch_count % 100 = 0 THEN
            RAISE NOTICE 'Migrated % batches, % total records', v_batch_count, v_total_migrated;
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
CREATE OR REPLACE VIEW strategy_performance AS
SELECT * FROM strategy_performance_partitioned;

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON strategy_performance_partitioned TO cbsc_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON strategy_performance TO cbsc_app;
GRANT USAGE ON SCHEMA public TO cbsc_app;