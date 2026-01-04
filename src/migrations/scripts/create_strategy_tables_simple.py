#!/usr/bin/env python3
"""
Create strategy management tables (simple version)
創建策略管理表 (簡化版本)
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

import psycopg2
from psycopg2.extras import DictCursor

def create_strategy_tables():
    """Create strategy management tables directly"""

    # Database connection parameters from docker-compose.yml
    db_url = "postgresql://cbsc_user:cbsc_password@localhost:5432/cbsc_strategy"

    print("Creating strategy management tables...")

    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()

        # Create strategy_configs table
        strategy_configs_sql = """
        CREATE TABLE IF NOT EXISTS strategy_configs (
            id VARCHAR(36) PRIMARY KEY,
            strategy_id VARCHAR(36) NOT NULL REFERENCES strategies(id),
            user_id VARCHAR(36) NOT NULL REFERENCES users(id),
            name VARCHAR(200) NOT NULL,
            description TEXT,
            custom_parameters JSONB NOT NULL,
            risk_tolerance VARCHAR(20) DEFAULT 'medium' NOT NULL,
            max_position_size NUMERIC(15,2) DEFAULT 100000.00 NOT NULL,
            stop_loss_percent NUMERIC(5,2) DEFAULT 5.0 NOT NULL,
            take_profit_percent NUMERIC(5,2),
            leverage_ratio NUMERIC(5,2) DEFAULT 1.0 NOT NULL,
            rebalance_frequency VARCHAR(20) DEFAULT 'daily' NOT NULL,
            min_trade_interval INTEGER DEFAULT 300 NOT NULL,
            max_drawdown_limit NUMERIC(5,2) DEFAULT 20.0 NOT NULL,
            volatility_target NUMERIC(5,2),
            correlation_limit NUMERIC(5,2) DEFAULT 0.7 NOT NULL,
            is_active BOOLEAN DEFAULT TRUE NOT NULL,
            is_simulation BOOLEAN DEFAULT TRUE NOT NULL,
            auto_execute BOOLEAN DEFAULT FALSE NOT NULL,
            notification_settings JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
            created_by VARCHAR(36),
            updated_by VARCHAR(36),
            is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
            deleted_at TIMESTAMP WITH TIME ZONE,
            deleted_by VARCHAR(36),
            version INTEGER DEFAULT 1 NOT NULL,
            metadata JSONB,
            notes TEXT,
            UNIQUE(strategy_id, user_id, name)
        );
        """
        cursor.execute(strategy_configs_sql)
        print("Strategy configs table created")

        # Create backtest_results table
        backtest_results_sql = """
        CREATE TABLE IF NOT EXISTS backtest_results (
            id VARCHAR(36) PRIMARY KEY,
            strategy_id VARCHAR(36) NOT NULL REFERENCES strategies(id),
            strategy_config_id VARCHAR(36) REFERENCES strategy_configs(id),
            user_id VARCHAR(36) NOT NULL REFERENCES users(id),
            name VARCHAR(200) NOT NULL,
            description TEXT,
            backtest_type VARCHAR(20) DEFAULT 'standard' NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            initial_capital NUMERIC(20,2) NOT NULL,
            final_capital NUMERIC(20,2) NOT NULL,
            total_return NUMERIC(10,4) NOT NULL,
            annualized_return NUMERIC(10,4),
            max_drawdown NUMERIC(10,4) NOT NULL,
            max_drawdown_duration INTEGER,
            sharpe_ratio NUMERIC(10,4),
            sortino_ratio NUMERIC(10,4),
            calmar_ratio NUMERIC(10,4),
            information_ratio NUMERIC(10,4),
            beta NUMERIC(10,4),
            alpha NUMERIC(10,4),
            tracking_error NUMERIC(10,4),
            volatility NUMERIC(10,4),
            downside_deviation NUMERIC(10,4),
            var_95 NUMERIC(10,4),
            var_99 NUMERIC(10,4),
            expected_shortfall NUMERIC(10,4),
            win_rate NUMERIC(5,4) NOT NULL,
            profit_factor NUMERIC(10,4),
            recovery_factor NUMERIC(10,4),
            payoff_ratio NUMERIC(10,4),
            average_win NUMERIC(20,2),
            average_loss NUMERIC(20,2),
            largest_win NUMERIC(20,2),
            largest_loss NUMERIC(20,2),
            total_trades INTEGER NOT NULL,
            winning_trades INTEGER NOT NULL,
            losing_trades INTEGER NOT NULL,
            average_trade_duration NUMERIC(10,2),
            commission_total NUMERIC(20,2) DEFAULT 0.0 NOT NULL,
            slippage_total NUMERIC(20,2) DEFAULT 0.0 NOT NULL,
            benchmark_return NUMERIC(10,4),
            benchmark_volatility NUMERIC(10,4),
            correlation_with_benchmark NUMERIC(5,4),
            monthly_returns JSONB,
            yearly_returns JSONB,
            rolling_returns JSONB,
            trade_distribution JSONB,
            risk_metrics JSONB,
            performance_attribution JSONB,
            sector_allocation JSONB,
            regional_allocation JSONB,
            scenarios_tested JSONB,
            stress_test_results JSONB,
            monte_carlo_results JSONB,
            status VARCHAR(20) DEFAULT 'completed' NOT NULL,
            error_message TEXT,
            execution_time_seconds INTEGER,
            data_points_analyzed INTEGER,
            parameters_used JSONB,
            market_conditions JSONB,
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
        """
        cursor.execute(backtest_results_sql)
        print("Backtest results table created")

        # Create performance_records table
        performance_records_sql = """
        CREATE TABLE IF NOT EXISTS performance_records (
            id VARCHAR(36) PRIMARY KEY,
            strategy_id VARCHAR(36) NOT NULL REFERENCES strategies(id),
            strategy_config_id VARCHAR(36) REFERENCES strategy_configs(id),
            user_id VARCHAR(36) NOT NULL REFERENCES users(id),
            record_date DATE NOT NULL,
            record_time TIMESTAMP WITH TIME ZONE NOT NULL,
            portfolio_value NUMERIC(20,2) NOT NULL,
            cash_balance NUMERIC(20,2) NOT NULL,
            invested_value NUMERIC(20,2) NOT NULL,
            daily_return NUMERIC(10,4) NOT NULL,
            daily_return_pct NUMERIC(10,4) NOT NULL,
            cumulative_return NUMERIC(10,4) NOT NULL,
            cumulative_return_pct NUMERIC(10,4) NOT NULL,
            running_max_drawdown NUMERIC(10,4) NOT NULL,
            running_sharpe_ratio NUMERIC(10,4),
            running_volatility NUMERIC(10,4),
            running_var NUMERIC(10,4),
            positions_count INTEGER NOT NULL,
            active_positions INTEGER NOT NULL,
            long_positions INTEGER NOT NULL,
            short_positions INTEGER NOT NULL,
            sector_exposure JSONB,
            country_exposure JSONB,
            currency_exposure JSONB,
            risk_metrics JSONB,
            greeks JSONB,
            correlation_matrix JSONB,
            beta_portfolio NUMERIC(10,4),
            tracking_error NUMERIC(10,4),
            information_ratio NUMERIC(10,4),
            turnover_rate NUMERIC(10,4),
            trading_volume NUMERIC(20,2) NOT NULL,
            commissions NUMERIC(20,2) DEFAULT 0.0 NOT NULL,
            slippage NUMERIC(20,2) DEFAULT 0.0 NOT NULL,
            margin_used NUMERIC(20,2) DEFAULT 0.0 NOT NULL,
            margin_available NUMERIC(20,2),
            leverage_ratio NUMERIC(10,4) DEFAULT 1.0 NOT NULL,
            risk_score NUMERIC(5,4),
            performance_score NUMERIC(5,4),
            efficiency_score NUMERIC(5,4),
            alerts_triggered JSONB,
            benchmark_comparison JSONB,
            market_conditions JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
            created_by VARCHAR(36),
            updated_by VARCHAR(36),
            is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
            deleted_at TIMESTAMP WITH TIME ZONE,
            deleted_by VARCHAR(36),
            version INTEGER DEFAULT 1 NOT NULL,
            metadata JSONB,
            notes TEXT,
            UNIQUE(strategy_id, strategy_config_id, record_date, record_time)
        );
        """
        cursor.execute(performance_records_sql)
        print("Performance records table created")

        # Create indexes
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_strategy_configs_strategy_user ON strategy_configs(strategy_id, user_id);",
            "CREATE INDEX IF NOT EXISTS idx_strategy_configs_user_active ON strategy_configs(user_id, is_active);",
            "CREATE INDEX IF NOT EXISTS idx_strategy_configs_risk_tolerance ON strategy_configs(risk_tolerance);",
            "CREATE INDEX IF NOT EXISTS idx_backtest_results_strategy ON backtest_results(strategy_id);",
            "CREATE INDEX IF NOT EXISTS idx_backtest_results_user ON backtest_results(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_backtest_results_date_range ON backtest_results(start_date, end_date);",
            "CREATE INDEX IF NOT EXISTS idx_backtest_results_type ON backtest_results(backtest_type);",
            "CREATE INDEX IF NOT EXISTS idx_backtest_results_return ON backtest_results(total_return DESC);",
            "CREATE INDEX IF NOT EXISTS idx_backtest_results_sharpe ON backtest_results(sharpe_ratio DESC NULLS LAST);",
            "CREATE INDEX IF NOT EXISTS idx_performance_records_strategy_date ON performance_records(strategy_id, record_date);",
            "CREATE INDEX IF NOT EXISTS idx_performance_records_config_date ON performance_records(strategy_config_id, record_date);",
            "CREATE INDEX IF NOT EXISTS idx_performance_records_user_date ON performance_records(user_id, record_date);",
            "CREATE INDEX IF NOT EXISTS idx_performance_records_date_time ON performance_records(record_date, record_time);"
        ]

        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
            except Exception as e:
                print(f"Index creation warning: {e}")

        print("Indexes created")

        # Create update trigger function
        trigger_function = """
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        """
        cursor.execute(trigger_function)
        print("Update trigger function created")

        # Create triggers for each table
        triggers = [
            "CREATE TRIGGER update_strategy_configs_updated_at BEFORE UPDATE ON strategy_configs FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();",
            "CREATE TRIGGER update_backtest_results_updated_at BEFORE UPDATE ON backtest_results FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();",
            "CREATE TRIGGER update_performance_records_updated_at BEFORE UPDATE ON performance_records FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();"
        ]

        for trigger_sql in triggers:
            try:
                cursor.execute(trigger_sql)
            except Exception as e:
                print(f"Trigger creation warning: {e}")

        print("Triggers created")

        # Insert sample data
        sample_config = """
        INSERT INTO strategy_configs (
            id, strategy_id, user_id, name, description, custom_parameters,
            risk_tolerance, max_position_size, stop_loss_percent, leverage_ratio
        ) VALUES (
            'config-001', 'strategy-001', 'admin-001', 'MA Crossover Default',
            'Default configuration for MA Crossover strategy',
            '{"fast_period": 10, "slow_period": 30, "signal_period": 9}',
            'medium', 50000.00, 3.0, 1.0
        ) ON CONFLICT (strategy_id, user_id, name) DO NOTHING;
        """
        cursor.execute(sample_config)
        print("Sample strategy config inserted")

        sample_backtest = """
        INSERT INTO backtest_results (
            id, strategy_id, strategy_config_id, user_id, name, description,
            backtest_type, start_date, end_date, initial_capital, final_capital,
            total_return, max_drawdown, sharpe_ratio, win_rate, total_trades,
            winning_trades, losing_trades
        ) VALUES (
            'backtest-001', 'strategy-001', 'config-001', 'admin-001', 'MA Crossover Test',
            'Backtest of MA Crossover strategy on historical data',
            'standard', '2023-01-01', '2024-01-01', 100000.00, 115000.00,
            0.15, -0.08, 1.25, 0.65, 125, 81, 44
        ) ON CONFLICT DO NOTHING;
        """
        cursor.execute(sample_backtest)
        print("Sample backtest result inserted")

        conn.commit()
        print("Strategy management tables created successfully!")

        # Verify tables
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('strategy_configs', 'backtest_results', 'performance_records')
            ORDER BY table_name;
        """)

        tables = cursor.fetchall()
        print("\nCreated strategy tables:")
        for (table_name,) in tables:
            print(f"  {table_name}")

        cursor.close()
        conn.close()

        return True

    except Exception as e:
        print(f"Error creating strategy tables: {e}")
        return False

if __name__ == "__main__":
    success = create_strategy_tables()
    print(f"Strategy tables creation: {success}")

    if success:
        print("Database schema is ready for use!")
    else:
        print("Failed to create strategy tables!")