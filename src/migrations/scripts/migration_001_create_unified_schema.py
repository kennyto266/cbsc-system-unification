"""
創建統一數據庫模式遷移腳本

建立CBSC統一數據模型的6大核心模組表結構。
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List

from sqlalchemy import text, inspect
from sqlalchemy.ext.asyncio import AsyncSession

from ...database.connection import db_manager
from ..migration_script import MigrationScript
from ...models import *  # 导入所有统一模型

logger = logging.getLogger(__name__)

class CreateUnifiedSchemaMigration(MigrationScript):
    """創建統一數據庫模式遷移腳本"""

    def __init__(self):
        super().__init__(
            version="001",
            name="create_unified_schema",
            description="創建CBSC統一數據模型的6大核心模組表結構",
            author="Data Migration System"
        )

    def get_up_sql(self) -> str:
        """獲取升級SQL語句"""
        return """
        -- 1. 用戶和權限管理模組
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            first_name VARCHAR(100),
            last_name VARCHAR(100),
            phone VARCHAR(20),
            avatar_url VARCHAR(500),
            timezone VARCHAR(50) DEFAULT 'UTC',
            language VARCHAR(10) DEFAULT 'en',
            is_active BOOLEAN DEFAULT TRUE,
            is_verified BOOLEAN DEFAULT FALSE,
            last_login_at TIMESTAMP WITH TIME ZONE,
            password_changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            metadata JSONB DEFAULT '{}'
        );

        CREATE TABLE IF NOT EXISTS roles (
            id SERIAL PRIMARY KEY,
            name VARCHAR(50) UNIQUE NOT NULL,
            display_name VARCHAR(100),
            description TEXT,
            is_system_role BOOLEAN DEFAULT FALSE,
            permissions JSONB DEFAULT '[]',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS user_roles (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
            assigned_by INTEGER REFERENCES users(id),
            assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            expires_at TIMESTAMP WITH TIME ZONE,
            is_active BOOLEAN DEFAULT TRUE,
            UNIQUE(user_id, role_id)
        );

        -- 2. 策略管理模組
        CREATE TABLE IF NOT EXISTS strategy_categories (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) UNIQUE NOT NULL,
            display_name VARCHAR(100),
            description TEXT,
            parent_id INTEGER REFERENCES strategy_categories(id),
            icon VARCHAR(50),
            color VARCHAR(7),
            sort_order INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS strategies (
            id SERIAL PRIMARY KEY,
            name VARCHAR(200) NOT NULL,
            code VARCHAR(50) UNIQUE,
            category_id INTEGER REFERENCES strategy_categories(id),
            description TEXT,
            version VARCHAR(20) DEFAULT '1.0.0',
            status VARCHAR(20) DEFAULT 'draft',
            risk_level VARCHAR(20) DEFAULT 'medium',
            author_id INTEGER REFERENCES users(id),
            tags JSONB DEFAULT '[]',
            parameters JSONB DEFAULT '{}',
            config_schema JSONB DEFAULT '{}',
            is_public BOOLEAN DEFAULT FALSE,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            metadata JSONB DEFAULT '{}'
        );

        CREATE TABLE IF NOT EXISTS strategy_configs (
            id SERIAL PRIMARY KEY,
            strategy_id INTEGER REFERENCES strategies(id) ON DELETE CASCADE,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            name VARCHAR(200) NOT NULL,
            config JSONB DEFAULT '{}',
            parameters JSONB DEFAULT '{}',
            is_default BOOLEAN DEFAULT FALSE,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            UNIQUE(strategy_id, user_id, name)
        );

        CREATE TABLE IF NOT EXISTS strategy_performance (
            id SERIAL PRIMARY KEY,
            strategy_id INTEGER REFERENCES strategies(id) ON DELETE CASCADE,
            config_id INTEGER REFERENCES strategy_configs(id) ON DELETE CASCADE,
            symbol VARCHAR(20) NOT NULL,
            timeframe VARCHAR(10) DEFAULT '1d',
            start_date DATE,
            end_date DATE,
            total_return DECIMAL(15,6),
            annualized_return DECIMAL(15,6),
            sharpe_ratio DECIMAL(10,6),
            max_drawdown DECIMAL(10,6),
            win_rate DECIMAL(5,4),
            profit_factor DECIMAL(10,4),
            total_trades INTEGER,
            winning_trades INTEGER,
            losing_trades INTEGER,
            avg_trade_return DECIMAL(15,6),
            volatility DECIMAL(10,6),
            benchmark VARCHAR(20),
            benchmark_return DECIMAL(15,6),
            beta DECIMAL(10,6),
            alpha DECIMAL(15,6),
            backtest_date DATE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            metadata JSONB DEFAULT '{}'
        );

        -- 3. 市場數據模組
        CREATE TABLE IF NOT EXISTS market_data (
            id SERIAL PRIMARY KEY,
            symbol VARCHAR(20) NOT NULL,
            timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
            timeframe VARCHAR(10) DEFAULT '1d',
            open_price DECIMAL(15,6),
            high_price DECIMAL(15,6),
            low_price DECIMAL(15,6),
            close_price DECIMAL(15,6),
            volume BIGINT,
            turnover DECIMAL(20,4),
            source VARCHAR(50),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            UNIQUE(symbol, timestamp, timeframe)
        );

        CREATE TABLE IF NOT EXISTS technical_indicators (
            id SERIAL PRIMARY KEY,
            symbol VARCHAR(20) NOT NULL,
            timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
            timeframe VARCHAR(10) DEFAULT '1d',
            indicator_type VARCHAR(50) NOT NULL,
            indicator_name VARCHAR(100) NOT NULL,
            value DECIMAL(15,6),
            parameters JSONB DEFAULT '{}',
            source VARCHAR(50),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            UNIQUE(symbol, timestamp, timeframe, indicator_type, indicator_name)
        );

        CREATE TABLE IF NOT EXISTS sentiment_data (
            id SERIAL PRIMARY KEY,
            symbol VARCHAR(20),
            market VARCHAR(50),
            timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
            source VARCHAR(100) NOT NULL,
            sentiment_score DECIMAL(5,4),
            sentiment_label VARCHAR(50),
            confidence DECIMAL(5,4),
            volume_mentions INTEGER,
            impact_level VARCHAR(20),
            text_content TEXT,
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );

        -- 4. 交易和投資組合模組
        CREATE TABLE IF NOT EXISTS portfolios (
            id SERIAL PRIMARY KEY,
            name VARCHAR(200) NOT NULL,
            user_id INTEGER REFERENCES users(id),
            description TEXT,
            portfolio_type VARCHAR(50) DEFAULT 'discretionary',
            base_currency VARCHAR(3) DEFAULT 'USD',
            initial_capital DECIMAL(20,4),
            current_value DECIMAL(20,4),
            cash_balance DECIMAL(20,4),
            status VARCHAR(20) DEFAULT 'active',
            is_public BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            metadata JSONB DEFAULT '{}'
        );

        CREATE TABLE IF NOT EXISTS positions (
            id SERIAL PRIMARY KEY,
            portfolio_id INTEGER REFERENCES portfolios(id) ON DELETE CASCADE,
            symbol VARCHAR(20) NOT NULL,
            asset_type VARCHAR(20) DEFAULT 'stock',
            quantity DECIMAL(20,8),
            avg_cost DECIMAL(15,6),
            current_price DECIMAL(15,6),
            market_value DECIMAL(20,4),
            unrealized_pnl DECIMAL(20,4),
            unrealized_pnl_pct DECIMAL(10,6),
            status VARCHAR(20) DEFAULT 'open',
            opened_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            closed_at TIMESTAMP WITH TIME ZONE,
            metadata JSONB DEFAULT '{}',
            UNIQUE(portfolio_id, symbol, status)
        );

        CREATE TABLE IF NOT EXISTS orders (
            id SERIAL PRIMARY KEY,
            portfolio_id INTEGER REFERENCES portfolios(id),
            position_id INTEGER REFERENCES positions(id),
            user_id INTEGER REFERENCES users(id),
            order_type VARCHAR(20) NOT NULL,
            side VARCHAR(10) NOT NULL,
            symbol VARCHAR(20) NOT NULL,
            quantity DECIMAL(20,8),
            price DECIMAL(15,6),
            stop_price DECIMAL(15,6),
            time_in_force VARCHAR(20) DEFAULT 'GTC',
            status VARCHAR(20) DEFAULT 'pending',
            filled_quantity DECIMAL(20,8) DEFAULT 0,
            avg_fill_price DECIMAL(15,6),
            commission DECIMAL(15,6),
            order_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            filled_at TIMESTAMP WITH TIME ZONE,
            expires_at TIMESTAMP WITH TIME ZONE,
            strategy_id INTEGER REFERENCES strategies(id),
            metadata JSONB DEFAULT '{}'
        );

        CREATE TABLE IF NOT EXISTS trades (
            id SERIAL PRIMARY KEY,
            order_id INTEGER REFERENCES orders(id),
            portfolio_id INTEGER REFERENCES portfolios(id),
            symbol VARCHAR(20) NOT NULL,
            side VARCHAR(10) NOT NULL,
            quantity DECIMAL(20,8),
            price DECIMAL(15,6),
            commission DECIMAL(15,6),
            trade_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            strategy_id INTEGER REFERENCES strategies(id),
            metadata JSONB DEFAULT '{}'
        );

        -- 5. 分析和報告模組
        CREATE TABLE IF NOT EXISTS analysis_reports (
            id SERIAL PRIMARY KEY,
            title VARCHAR(300) NOT NULL,
            report_type VARCHAR(50) NOT NULL,
            description TEXT,
            content JSONB,
            status VARCHAR(20) DEFAULT 'draft',
            author_id INTEGER REFERENCES users(id),
            portfolio_id INTEGER REFERENCES portfolios(id),
            strategy_id INTEGER REFERENCES strategies(id),
            generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            scheduled_at TIMESTAMP WITH TIME ZONE,
            parameters JSONB DEFAULT '{}',
            metadata JSONB DEFAULT '{}'
        );

        CREATE TABLE IF NOT EXISTS backtest_results (
            id SERIAL PRIMARY KEY,
            strategy_id INTEGER REFERENCES strategies(id),
            config_id INTEGER REFERENCES strategy_configs(id),
            symbol VARCHAR(20) NOT NULL,
            timeframe VARCHAR(10) DEFAULT '1d',
            start_date DATE,
            end_date DATE,
            initial_capital DECIMAL(20,4),
            final_capital DECIMAL(20,4),
            total_return DECIMAL(15,6),
            annualized_return DECIMAL(15,6),
            sharpe_ratio DECIMAL(10,6),
            sortino_ratio DECIMAL(10,6),
            max_drawdown DECIMAL(10,6),
            calmar_ratio DECIMAL(10,6),
            win_rate DECIMAL(5,4),
            profit_factor DECIMAL(10,4),
            total_trades INTEGER,
            winning_trades INTEGER,
            losing_trades INTEGER,
            avg_trade_return DECIMAL(15,6),
            best_trade_return DECIMAL(15,6),
            worst_trade_return DECIMAL(15,6),
            volatility DECIMAL(10,6),
            var_95 DECIMAL(10,6),
            benchmark VARCHAR(20),
            benchmark_return DECIMAL(15,6),
            beta DECIMAL(10,6),
            alpha DECIMAL(15,6),
            information_ratio DECIMAL(10,6),
            equity_curve JSONB,
            trade_history JSONB,
            performance_metrics JSONB,
            backtest_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            execution_time_ms INTEGER,
            metadata JSONB DEFAULT '{}'
        );

        CREATE TABLE IF NOT EXISTS performance_metrics (
            id SERIAL PRIMARY KEY,
            metric_type VARCHAR(50) NOT NULL,
            metric_name VARCHAR(100) NOT NULL,
            metric_value DECIMAL(15,6),
            metric_unit VARCHAR(20),
            period VARCHAR(20),
            portfolio_id INTEGER REFERENCES portfolios(id),
            strategy_id INTEGER REFERENCES strategies(id),
            symbol VARCHAR(20),
            date DATE,
            timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            metadata JSONB DEFAULT '{}',
            UNIQUE(metric_type, metric_name, portfolio_id, strategy_id, symbol, date)
        );

        -- 6. 系統管理模組
        CREATE TABLE IF NOT EXISTS system_config (
            id SERIAL PRIMARY KEY,
            config_key VARCHAR(200) UNIQUE NOT NULL,
            config_value TEXT,
            config_type VARCHAR(20) DEFAULT 'string',
            description TEXT,
            category VARCHAR(50),
            is_sensitive BOOLEAN DEFAULT FALSE,
            is_public BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_by INTEGER REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS audit_logs (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            action VARCHAR(100) NOT NULL,
            resource_type VARCHAR(50) NOT NULL,
            resource_id VARCHAR(100),
            ip_address INET,
            user_agent TEXT,
            request_data JSONB,
            response_status INTEGER,
            execution_time_ms INTEGER,
            timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            metadata JSONB DEFAULT '{}'
        );

        CREATE TABLE IF NOT EXISTS data_schemas (
            id SERIAL PRIMARY KEY,
            schema_name VARCHAR(200) UNIQUE NOT NULL,
            schema_version VARCHAR(20) DEFAULT '1.0.0',
            schema_definition JSONB NOT NULL,
            description TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_by INTEGER REFERENCES users(id)
        );

        -- 創建索引
        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
        CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
        CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);
        CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);

        CREATE INDEX IF NOT EXISTS idx_strategies_author_id ON strategies(author_id);
        CREATE INDEX IF NOT EXISTS idx_strategies_category_id ON strategies(category_id);
        CREATE INDEX IF NOT EXISTS idx_strategies_status ON strategies(status);
        CREATE INDEX IF NOT EXISTS idx_strategies_is_active ON strategies(is_active);

        CREATE INDEX IF NOT EXISTS idx_market_data_symbol ON market_data(symbol);
        CREATE INDEX IF NOT EXISTS idx_market_data_timestamp ON market_data(timestamp);
        CREATE INDEX IF NOT EXISTS idx_market_data_symbol_timestamp ON market_data(symbol, timestamp);
        CREATE INDEX IF NOT EXISTS idx_market_data_timeframe ON market_data(timeframe);

        CREATE INDEX IF NOT EXISTS idx_technical_indicators_symbol ON technical_indicators(symbol);
        CREATE INDEX IF NOT EXISTS idx_technical_indicators_timestamp ON technical_indicators(timestamp);
        CREATE INDEX IF NOT EXISTS idx_technical_indicators_type ON technical_indicators(indicator_type);

        CREATE INDEX IF NOT EXISTS idx_backtest_results_strategy_id ON backtest_results(strategy_id);
        CREATE INDEX IF NOT EXISTS idx_backtest_results_symbol ON backtest_results(symbol);
        CREATE INDEX IF NOT EXISTS idx_backtest_results_backtest_date ON backtest_results(backtest_date);

        CREATE INDEX IF NOT EXISTS idx_trades_portfolio_id ON trades(portfolio_id);
        CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol);
        CREATE INDEX IF NOT EXISTS idx_trades_trade_date ON trades(trade_date);

        CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
        CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
        CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp);
        CREATE INDEX IF NOT EXISTS idx_audit_logs_resource_type ON audit_logs(resource_type);
        """

    def get_down_sql(self) -> str:
        """獲取回滾SQL語句"""
        return """
        DROP TABLE IF EXISTS data_schemas CASCADE;
        DROP TABLE IF EXISTS audit_logs CASCADE;
        DROP TABLE IF EXISTS system_config CASCADE;
        DROP TABLE IF EXISTS performance_metrics CASCADE;
        DROP TABLE IF EXISTS backtest_results CASCADE;
        DROP TABLE IF EXISTS analysis_reports CASCADE;
        DROP TABLE IF EXISTS trades CASCADE;
        DROP TABLE IF EXISTS orders CASCADE;
        DROP TABLE IF EXISTS positions CASCADE;
        DROP TABLE IF EXISTS portfolios CASCADE;
        DROP TABLE IF EXISTS sentiment_data CASCADE;
        DROP TABLE IF EXISTS technical_indicators CASCADE;
        DROP TABLE IF EXISTS market_data CASCADE;
        DROP TABLE IF EXISTS strategy_performance CASCADE;
        DROP TABLE IF EXISTS strategy_configs CASCADE;
        DROP TABLE IF EXISTS strategies CASCADE;
        DROP TABLE IF EXISTS strategy_categories CASCADE;
        DROP TABLE IF EXISTS user_roles CASCADE;
        DROP TABLE IF EXISTS roles CASCADE;
        DROP TABLE IF EXISTS users CASCADE;
        """

    async def validate_migration(self, session: AsyncSession) -> Dict[str, Any]:
        """驗證遷移結果"""
        result = {
            "success": True,
            "tables_created": [],
            "indexes_created": [],
            "errors": []
        }

        try:
            # 檢查表是否創建成功
            expected_tables = [
                'users', 'roles', 'user_roles', 'strategy_categories',
                'strategies', 'strategy_configs', 'strategy_performance',
                'market_data', 'technical_indicators', 'sentiment_data',
                'portfolios', 'positions', 'orders', 'trades',
                'analysis_reports', 'backtest_results', 'performance_metrics',
                'system_config', 'audit_logs', 'data_schemas'
            ]

            for table_name in expected_tables:
                try:
                    await session.execute(text(f"SELECT 1 FROM {table_name} LIMIT 1"))
                    result["tables_created"].append(table_name)
                    logger.info(f"Table {table_name} exists and is accessible")
                except Exception as e:
                    result["errors"].append(f"Table {table_name} not accessible: {str(e)}")
                    result["success"] = False

            # 檢查關鍵索引
            expected_indexes = [
                'idx_users_email', 'idx_strategies_author_id',
                'idx_market_data_symbol', 'idx_backtest_results_strategy_id',
                'idx_audit_logs_user_id'
            ]

            for index_name in expected_indexes:
                try:
                    await session.execute(text(f"SELECT 1 FROM pg_indexes WHERE indexname = '{index_name}'"))
                    result["indexes_created"].append(index_name)
                except Exception as e:
                    result["errors"].append(f"Index {index_name} not found: {str(e)}")

            logger.info(f"Migration validation completed. Tables: {len(result['tables_created'])}, Indexes: {len(result['indexes_created'])}")

        except Exception as e:
            result["success"] = False
            result["errors"].append(f"Validation failed: {str(e)}")
            logger.error(f"Migration validation failed: {e}")

        return result

# 註冊遷移腳本
migration = CreateUnifiedSchemaMigration()