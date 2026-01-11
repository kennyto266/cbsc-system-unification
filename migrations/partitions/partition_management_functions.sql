-- Partition Management Functions for CBSC System
-- Created: 2025-12-11
-- Description: Functions for automatic partition creation and maintenance

-- Create extension if not exists
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Function to create all necessary partitions for a given month
CREATE OR REPLACE FUNCTION create_partitions_for_month(
    p_target_date DATE DEFAULT CURRENT_DATE,
    p_months_ahead INTEGER DEFAULT 6
)
RETURNS JSONB AS $$
DECLARE
    v_partition_name TEXT;
    v_start_date DATE;
    v_end_date DATE;
    v_created_partitions TEXT[] := '{}';
    v_tables TEXT[] := ARRAY['strategy_performance_partitioned', 'trades_partitioned', 'performance_metrics_partitioned'];
    v_table_name TEXT;
BEGIN
    -- Loop through each partitioned table
    FOREACH v_table_name IN ARRAY v_tables LOOP
        -- Create partitions for future months
        FOR i IN 0..p_months_ahead LOOP
            v_start_date := DATE_TRUNC('month', p_target_date + INTERVAL '1 month' * i);
            v_end_date := v_start_date + INTERVAL '1 month';

            -- Generate partition name based on table
            IF v_table_name = 'strategy_performance_partitioned' THEN
                v_partition_name := 'strategy_performance_y' || EXTRACT(YEAR FROM v_start_date) || '_m' || LPAD(EXTRACT(MONTH FROM v_start_date)::TEXT, 2, '0');
            ELSIF v_table_name = 'trades_partitioned' THEN
                v_partition_name := 'trades_y' || EXTRACT(YEAR FROM v_start_date) || '_m' || LPAD(EXTRACT(MONTH FROM v_start_date)::TEXT, 2, '0');
            ELSIF v_table_name = 'performance_metrics_partitioned' THEN
                v_partition_name := 'perf_metrics_y' || EXTRACT(YEAR FROM v_start_date) || '_m' || LPAD(EXTRACT(MONTH FROM v_start_date)::TEXT, 2, '0');
            END IF;

            -- Create partition if it doesn't exist
            IF NOT EXISTS (
                SELECT 1 FROM pg_tables
                WHERE tablename = v_partition_name
            ) THEN
                EXECUTE format('
                    CREATE TABLE %I PARTITION OF %I
                    FOR VALUES FROM (%L) TO (%L)',
                    v_partition_name, v_table_name, v_start_date, v_end_date
                );

                -- Create appropriate indexes based on table type
                IF v_table_name = 'strategy_performance_partitioned' THEN
                    EXECUTE format('
                        CREATE INDEX idx_%s_strategy ON %I (strategy_id)',
                        v_partition_name, v_partition_name
                    );
                ELSIF v_table_name = 'trades_partitioned' THEN
                    EXECUTE format('
                        CREATE INDEX idx_%s_symbol ON %I (symbol);
                        CREATE INDEX idx_%s_portfolio ON %I (portfolio_id)',
                        v_partition_name, v_partition_name,
                        v_partition_name, v_partition_name
                    );
                ELSIF v_table_name = 'performance_metrics_partitioned' THEN
                    EXECUTE format('
                        CREATE INDEX idx_%s_portfolio ON %I (portfolio_id);
                        CREATE INDEX idx_%s_strategy ON %I (strategy_id);
                        CREATE INDEX idx_%s_type_name ON %I (metric_type, metric_name)',
                        v_partition_name, v_partition_name,
                        v_partition_name, v_partition_name,
                        v_partition_name, v_partition_name
                    );
                END IF;

                v_created_partitions := array_append(v_created_partitions, v_partition_name);
                RAISE NOTICE 'Created partition: % for table: %', v_partition_name, v_table_name;
            END IF;
        END LOOP;
    END LOOP;

    RETURN jsonb_build_object(
        'created_partitions', v_created_partitions,
        'target_date', p_target_date,
        'months_ahead', p_months_ahead
    );
END;
$$ LANGUAGE plpgsql;

-- Function to drop old partitions (older than specified months)
CREATE OR REPLACE FUNCTION drop_old_partitions(
    p_months_to_keep INTEGER DEFAULT 24,
    p_dry_run BOOLEAN DEFAULT TRUE
)
RETURNS JSONB AS $$
DECLARE
    v_cutoff_date DATE;
    v_partition_name TEXT;
    v_partitions_to_drop TEXT[] := '{}';
    v_dropped_count INTEGER := 0;
    v_tables TEXT[] := ARRAY['strategy_performance', 'trades', 'perf_metrics'];
    v_prefix TEXT;
    v_table_name TEXT;
    v_partition_date DATE;
BEGIN
    v_cutoff_date := DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month' * p_months_to_keep);

    -- Find partitions older than cutoff date
    FOR v_table_name IN ARRAY v_tables LOOP
        IF v_table_name = 'strategy_performance' THEN
            v_prefix := 'strategy_performance_y';
        ELSIF v_table_name = 'trades' THEN
            v_prefix := 'trades_y';
        ELSIF v_table_name = 'perf_metrics' THEN
            v_prefix := 'perf_metrics_y';
        END IF;

        -- Find matching partitions
        FOR v_partition_name IN
            SELECT tablename
            FROM pg_tables
            WHERE tablename LIKE v_prefix || '_%'
        LOOP
            -- Extract date from partition name
            BEGIN
                v_partition_date := TO_DATE(
                    SUBSTRING(v_partition_name FROM LENGTH(v_prefix) + 2 FOR 7),
                    'YYYY"m"MM'
                );

                IF v_partition_date < v_cutoff_date THEN
                    v_partitions_to_drop := array_append(v_partitions_to_drop, v_partition_name);

                    IF NOT p_dry_run THEN
                        EXECUTE format('DROP TABLE IF EXISTS %I CASCADE', v_partition_name);
                        v_dropped_count := v_dropped_count + 1;
                        RAISE NOTICE 'Dropped partition: %', v_partition_name;
                    END IF;
                END IF;
            EXCEPTION WHEN OTHERS THEN
                RAISE WARNING 'Could not parse date from partition name: %', v_partition_name;
            END;
        END LOOP;
    END LOOP;

    RETURN jsonb_build_object(
        'partitions_to_drop', v_partitions_to_drop,
        'cutoff_date', v_cutoff_date,
        'months_to_keep', p_months_to_keep,
        'dry_run', p_dry_run,
        'dropped_count', v_dropped_count
    );
END;
$$ LANGUAGE plpgsql;

-- Function to get partition status and statistics
CREATE OR REPLACE FUNCTION get_partition_statistics()
RETURNS JSONB AS $$
DECLARE
    v_result JSONB;
    v_table_name TEXT;
    v_partition_name TEXT;
    v_partition_count INTEGER;
    v_total_rows BIGINT;
    v_total_size BIGINT;
    v_stats JSONB := '[]'::JSONB;
BEGIN
    -- Get statistics for each partitioned table
    FOR v_table_name IN ARRAY ARRAY['strategy_performance', 'trades', 'perf_metrics'] LOOP
        v_partition_count := 0;
        v_total_rows := 0;
        v_total_size := 0;

        -- Count partitions and get sizes
        FOR v_partition_name IN
            SELECT tablename
            FROM pg_tables
            WHERE tablename LIKE v_table_name || '_%'
            OR tablename = v_table_name || '_y%'
            OR tablename LIKE 'strategy_performance_%'
            OR tablename LIKE 'trades_%'
            OR tablename LIKE 'perf_metrics_%'
        LOOP
            v_partition_count := v_partition_count + 1;

            -- Get row count and size for this partition
            BEGIN
                EXECUTE format('
                    SELECT
                        COALESCE((SELECT COUNT(*) FROM %I), 0)::BIGINT as row_count,
                        COALESCE(pg_total_relation_size(%L::regclass), 0)::BIGINT as size_bytes
                ', v_partition_name, v_partition_name)
                INTO v_total_rows, v_total_size;

                v_stats := v_stats || jsonb_build_object(
                    'table', v_table_name,
                    'partition', v_partition_name,
                    'row_count', v_total_rows,
                    'size_bytes', v_total_size,
                    'size_mb', ROUND(v_total_size / 1024.0 / 1024.0, 2)
                );
            EXCEPTION WHEN OTHERS THEN
                RAISE WARNING 'Could not get statistics for partition: %', v_partition_name;
            END;
        END LOOP;
    END LOOP;

    -- Return comprehensive statistics
    v_result := jsonb_build_object(
        'generated_at', NOW(),
        'partition_stats', v_stats,
        'summary', jsonb_build_object(
            'total_partitions', (SELECT COUNT(*) FROM pg_tables WHERE tablename LIKE '%_y%' OR tablename LIKE 'strategy_performance_%' OR tablename LIKE 'trades_%' OR tablename LIKE 'perf_metrics_%'),
            'total_size_mb', ROUND((SELECT COALESCE(SUM(pg_total_relation_size(schemaname||'.'||tablename)), 0) FROM pg_tables WHERE tablename LIKE '%_y%' OR tablename LIKE 'strategy_performance_%' OR tablename LIKE 'trades_%' OR tablename LIKE 'perf_metrics_%') / 1024.0 / 1024.0, 2)
        )
    );

    RETURN v_result;
END;
$$ LANGUAGE plpgsql;

-- Function to analyze and vacuum partitions
CREATE OR REPLACE FUNCTION maintain_partitions(
    p_analyze BOOLEAN DEFAULT TRUE,
    p_vacuum BOOLEAN DEFAULT TRUE,
    p_vacuum_full BOOLEAN DEFAULT FALSE,
    p_table_filter TEXT DEFAULT '%'  -- Filter for specific tables
)
RETURNS JSONB AS $$
DECLARE
    v_partition_name TEXT;
    v_maintained_count INTEGER := 0;
    v_maintained_partitions TEXT[] := '{}';
    v_start_time TIMESTAMP := NOW();
BEGIN
    -- Iterate through all partition tables
    FOR v_partition_name IN
        SELECT tablename
        FROM pg_tables
        WHERE tablename LIKE p_table_filter
          AND (tablename LIKE '%_y%' OR tablename LIKE 'strategy_performance_%' OR tablename LIKE 'trades_%' OR tablename LIKE 'perf_metrics_%')
    LOOP
        BEGIN
            -- Analyze table if requested
            IF p_analyze THEN
                EXECUTE format('ANALYZE %I', v_partition_name);
            END IF;

            -- Vacuum table if requested
            IF p_vacuum THEN
                IF p_vacuum_full THEN
                    EXECUTE format('VACUUM FULL %I', v_partition_name);
                ELSE
                    EXECUTE format('VACUUM %I', v_partition_name);
                END IF;
            END IF;

            v_maintained_partitions := array_append(v_maintained_partitions, v_partition_name);
            v_maintained_count := v_maintained_count + 1;

            RAISE NOTICE 'Maintained partition: %', v_partition_name;

        EXCEPTION WHEN OTHERS THEN
            RAISE WARNING 'Failed to maintain partition: % - Error: %', v_partition_name, SQLERRM;
        END;
    END LOOP;

    RETURN jsonb_build_object(
        'maintained_count', v_maintained_count,
        'maintained_partitions', v_maintained_partitions,
        'execution_time_seconds', EXTRACT(EPOCH FROM (NOW() - v_start_time)),
        'options', jsonb_build_object(
            'analyze', p_analyze,
            'vacuum', p_vacuum,
            'vacuum_full', p_vacuum_full,
            'table_filter', p_table_filter
        )
    );
END;
$$ LANGUAGE plpgsql;

-- Function to check partition health and integrity
CREATE OR REPLACE FUNCTION check_partition_health()
RETURNS JSONB AS $$
DECLARE
    v_result JSONB;
    v_health_issues JSONB := '[]'::JSONB;
    v_partition_name TEXT;
    v_partition_count INTEGER;
    v_row_count BIGINT;
    v_max_date TIMESTAMP;
    v_min_date TIMESTAMP;
BEGIN
    -- Check for missing future partitions
    FOR i IN 0..3 LOOP
        IF NOT EXISTS (
            SELECT 1 FROM pg_tables
            WHERE tablename = 'strategy_performance_y' || EXTRACT(YEAR FROM DATE_TRUNC('month', CURRENT_DATE + INTERVAL '1 month' * i)) || '_m' || LPAD(EXTRACT(MONTH FROM DATE_TRUNC('month', CURRENT_DATE + INTERVAL '1 month' * i))::TEXT, 2, '0')
        ) THEN
            v_health_issues := v_health_issues || jsonb_build_object(
                'type', 'missing_partition',
                'table', 'strategy_performance',
                'missing_month', DATE_TRUNC('month', CURRENT_DATE + INTERVAL '1 month' * i),
                'severity', 'warning'
            );
        END IF;
    END LOOP;

    -- Check for empty partitions (should have data)
    FOR v_partition_name IN
        SELECT tablename
        FROM pg_tables
        WHERE tablename LIKE 'strategy_performance_%'
        AND tablename NOT LIKE '%backup'
        LIMIT 10  -- Check only recent partitions
    LOOP
        BEGIN
            EXECUTE format('SELECT COUNT(*) FROM %I', v_partition_name) INTO v_row_count;

            IF v_row_count = 0 THEN
                v_health_issues := v_health_issues || jsonb_build_object(
                    'type', 'empty_partition',
                    'partition', v_partition_name,
                    'severity', 'info'
                );
            END IF;
        EXCEPTION WHEN OTHERS THEN
            v_health_issues := v_health_issues || jsonb_build_object(
                'type', 'partition_error',
                'partition', v_partition_name,
                'error', SQLERRM,
                'severity', 'error'
            );
        END;
    END LOOP;

    -- Check data continuity in strategy_performance
    BEGIN
        SELECT MIN(date), MAX(date) INTO v_min_date, v_max_date FROM strategy_performance;

        IF v_min_date IS NOT NULL AND v_max_date IS NOT NULL THEN
            -- Check for large gaps in data
            FOR v_partition_name IN
                SELECT tablename
                FROM pg_tables
                WHERE tablename LIKE 'strategy_performance_%'
                ORDER BY tablename DESC
                LIMIT 5
            LOOP
                -- This would need more complex logic to check actual data gaps
                NULL;
            END LOOP;
        END IF;
    EXCEPTION WHEN OTHERS THEN
        v_health_issues := v_health_issues || jsonb_build_object(
            'type', 'data_continuity_error',
            'error', SQLERRM,
            'severity', 'error'
        );
    END;

    v_result := jsonb_build_object(
        'checked_at', NOW(),
        'health_issues', v_health_issues,
        'issue_count', jsonb_array_length(v_health_issues),
        'status', CASE
            WHEN jsonb_array_length(v_health_issues) = 0 THEN 'healthy'
            WHEN EXISTS (SELECT 1 FROM jsonb_array_elements(v_health_issues) WHERE value->>'severity' = 'error') THEN 'error'
            ELSE 'warning'
        END
    );

    RETURN v_result;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions for maintenance functions
GRANT EXECUTE ON FUNCTION create_partitions_for_month TO cbsc_app;
GRANT EXECUTE ON FUNCTION drop_old_partitions TO cbsc_app;
GRANT EXECUTE ON FUNCTION get_partition_statistics TO cbsc_app;
GRANT EXECUTE ON FUNCTION maintain_partitions TO cbsc_app;
GRANT EXECUTE ON FUNCTION check_partition_health TO cbsc_app;