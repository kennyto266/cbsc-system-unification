-- Migration: Create partitioned performance_metrics table
-- Version: 003
-- Description: Convert performance_metrics table to monthly partitions
-- Created: 2025-12-11

-- Create backup of original table
CREATE TABLE IF NOT EXISTS performance_metrics_backup AS
SELECT * FROM performance_metrics;

-- Create partitioned table
CREATE TABLE performance_metrics_partitioned (
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
    portfolio_id UUID,
    strategy_id UUID,
    user_id UUID,

    -- Metric basic information
    metric_type VARCHAR(50) NOT NULL,  -- return, risk, trading, custom
    metric_name VARCHAR(100) NOT NULL,
    metric_category VARCHAR(50) NOT NULL,  -- daily, weekly, monthly, ytd, all_time

    -- Time range
    calculation_date TIMESTAMP WITH TIME ZONE NOT NULL,
    period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    period_end TIMESTAMP WITH TIME ZONE NOT NULL,

    -- Metric values
    value DECIMAL(15,6) NOT NULL,
    benchmark_value DECIMAL(15,6),
    percentile_rank DECIMAL(5,4),

    -- Statistical information
    sample_size INTEGER,
    confidence_interval_lower DECIMAL(15,6),
    confidence_interval_upper DECIMAL(15,6),
    standard_error DECIMAL(15,6),

    -- Calculation parameters
    calculation_method VARCHAR(100),
    parameters JSONB,
    data_quality_score DECIMAL(3,2) DEFAULT 1.0 NOT NULL,

    -- Comparative analysis
    yoy_change DECIMAL(10,6),  -- Year-over-year change
    mom_change DECIMAL(10,6),  -- Month-over-month change
    rolling_30d_avg DECIMAL(15,6),
    rolling_90d_avg DECIMAL(15,6)
) PARTITION BY RANGE (calculation_date);

-- Create indexes
CREATE INDEX idx_perf_metrics_partitioned_date ON performance_metrics_partitioned (calculation_date);
CREATE INDEX idx_perf_metrics_partitioned_type_name ON performance_metrics_partitioned (metric_type, metric_name);
CREATE INDEX idx_perf_metrics_partitioned_portfolio_type_date ON performance_metrics_partitioned (portfolio_id, metric_type, calculation_date);
CREATE INDEX idx_perf_metrics_partitioned_strategy_type_date ON performance_metrics_partitioned (strategy_id, metric_type, calculation_date);
CREATE INDEX idx_perf_metrics_partitioned_category_date ON performance_metrics_partitioned (metric_category, calculation_date);

-- Create foreign key constraints
ALTER TABLE performance_metrics_partitioned
ADD CONSTRAINT fk_perf_metrics_portfolio
FOREIGN KEY (portfolio_id) REFERENCES portfolios(id) ON DELETE CASCADE;

ALTER TABLE performance_metrics_partitioned
ADD CONSTRAINT fk_perf_metrics_strategy
FOREIGN KEY (strategy_id) REFERENCES strategies(id) ON DELETE CASCADE;

ALTER TABLE performance_metrics_partitioned
ADD CONSTRAINT fk_perf_metrics_user
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

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
        partition_name := 'perf_metrics_y' || EXTRACT(YEAR FROM start_date) || '_m' || LPAD(EXTRACT(MONTH FROM start_date)::TEXT, 2, '0');

        EXECUTE format('
            CREATE TABLE IF NOT EXISTS %I PARTITION OF performance_metrics_partitioned
            FOR VALUES FROM (%L) TO (%L)',
            partition_name, start_date, end_date
        );

        -- Create partition-specific indexes
        EXECUTE format('
            CREATE INDEX IF NOT EXISTS idx_%s_portfolio
            ON %I (portfolio_id)',
            partition_name, partition_name
        );

        EXECUTE format('
            CREATE INDEX IF NOT EXISTS idx_%s_strategy
            ON %I (strategy_id)',
            partition_name, partition_name
        );

        EXECUTE format('
            CREATE INDEX IF NOT EXISTS idx_%s_type_name
            ON %I (metric_type, metric_name)',
            partition_name, partition_name
        );
    END LOOP;

    -- Create partitions for historical data (2 years back)
    FOR i IN -24..-1 LOOP
        start_date := DATE_TRUNC('month', CURRENT_TIMESTAMP + INTERVAL '1 month' * i);
        end_date := start_date + INTERVAL '1 month';
        partition_name := 'perf_metrics_y' || EXTRACT(YEAR FROM start_date) || '_m' || LPAD(EXTRACT(MONTH FROM start_date)::TEXT, 2, '0');

        EXECUTE format('
            CREATE TABLE IF NOT EXISTS %I PARTITION OF performance_metrics_partitioned
            FOR VALUES FROM (%L) TO (%L)',
            partition_name, start_date, end_date
        );
    END LOOP;
END $$;

-- Create trigger to automatically create new partitions
CREATE OR REPLACE FUNCTION create_performance_metrics_monthly_partition()
RETURNS TRIGGER AS $$
DECLARE
    start_date TIMESTAMP WITH TIME ZONE;
    end_date TIMESTAMP WITH TIME ZONE;
    partition_name TEXT;
BEGIN
    -- Check if partition exists for the new calculation_date
    start_date := DATE_TRUNC('month', NEW.calculation_date);
    partition_name := 'perf_metrics_y' || EXTRACT(YEAR FROM start_date) || '_m' || LPAD(EXTRACT(MONTH FROM start_date)::TEXT, 2, '0');

    IF NOT EXISTS (
        SELECT 1 FROM pg_tables
        WHERE tablename = partition_name
    ) THEN
        end_date := start_date + INTERVAL '1 month';

        EXECUTE format('
            CREATE TABLE %I PARTITION OF performance_metrics_partitioned
            FOR VALUES FROM (%L) TO (%L)',
            partition_name, start_date, end_date
        );

        EXECUTE format('
            CREATE INDEX idx_%s_portfolio
            ON %I (portfolio_id)',
            partition_name, partition_name
        );

        EXECUTE format('
            CREATE INDEX idx_%s_strategy
            ON %I (strategy_id)',
            partition_name, partition_name
        );

        RAISE NOTICE 'Created new performance_metrics partition: %', partition_name;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger
CREATE TRIGGER trigger_create_performance_metrics_partition
BEFORE INSERT ON performance_metrics_partitioned
FOR EACH ROW EXECUTE FUNCTION create_performance_metrics_monthly_partition();

-- Create function to migrate data from old table
CREATE OR REPLACE FUNCTION migrate_performance_metrics_data(
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
        SELECT MIN(calculation_date) INTO v_min_date FROM performance_metrics_backup;
    ELSE
        v_min_date := p_date_from;
    END IF;

    IF p_date_to IS NULL THEN
        SELECT MAX(calculation_date) INTO v_max_date FROM performance_metrics_backup;
    ELSE
        v_max_date := p_date_to;
    END IF;

    -- Migrate data in batches by day
    WHILE v_min_date <= v_max_date LOOP
        -- Insert batch
        INSERT INTO performance_metrics_partitioned (
            id, created_at, updated_at, created_by, updated_by, is_deleted, version, metadata,
            portfolio_id, strategy_id, user_id, metric_type, metric_name, metric_category,
            calculation_date, period_start, period_end, value, benchmark_value, percentile_rank,
            sample_size, confidence_interval_lower, confidence_interval_upper, standard_error,
            calculation_method, parameters, data_quality_score, yoy_change, mom_change,
            rolling_30d_avg, rolling_90d_avg
        )
        SELECT
            id, created_at, updated_at, created_by, updated_by, is_deleted, version, metadata,
            portfolio_id, strategy_id, user_id, metric_type, metric_name, metric_category,
            calculation_date, period_start, period_end, value, benchmark_value, percentile_rank,
            sample_size, confidence_interval_lower, confidence_interval_upper, standard_error,
            calculation_method, parameters, data_quality_score, yoy_change, mom_change,
            rolling_30d_avg, rolling_90d_avg
        FROM performance_metrics_backup
        WHERE calculation_date >= v_min_date
          AND calculation_date < v_min_date + INTERVAL '1 day'
        LIMIT p_batch_size;

        v_batch_count := v_batch_count + 1;
        GET DIAGNOSTICS v_total_migrated = ROW_COUNT;

        -- Move to next day
        v_min_date := v_min_date + INTERVAL '1 day';

        -- Log progress every 100 batches
        IF v_batch_count % 100 = 0 THEN
            RAISE NOTICE 'Migrated % batches, % total metrics', v_batch_count, v_total_migrated;
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
CREATE OR REPLACE VIEW performance_metrics AS
SELECT * FROM performance_metrics_partitioned;

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON performance_metrics_partitioned TO cbsc_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON performance_metrics TO cbsc_app;