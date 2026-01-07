#!/usr/bin/env python3
"""
ETL Configuration for PostgreSQL to ClickHouse data sync.

This module contains all configuration settings for the ETL pipeline.
"""

import os
from typing import Dict

# PostgreSQL Configuration (Source)
PG_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'cbsc'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres')
}

# ClickHouse Configuration (Target)
CH_CONFIG = {
    'host': os.getenv('CLICKHOUSE_HOST', 'localhost'),
    'port': int(os.getenv('CLICKHOUSE_PORT', 8123)),
    'database': 'analytics',
    'user': os.getenv('CLICKHOUSE_USER', 'default'),
    'password': os.getenv('CLICKHOUSE_PASSWORD', '')
}

# ETL Sync Settings
SYNC_INTERVAL_SECONDS = 300  # 5 minutes
BATCH_SIZE = 10000
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5

# Table Mappings
# Maps PostgreSQL tables to ClickHouse tables
TABLE_MAPPINGS: Dict[str, Dict] = {
    'strategy_backtests': {
        'source_table': 'strategy_backtests',
        'target_table': 'strategy_backtests',
        'key_columns': ['strategy_id', 'backtest_date', 'symbol'],
        'sync_type': 'incremental',
        'timestamp_column': 'created_at'
    },
    'strategy_performance': {
        'source_table': 'strategy_performance',
        'target_table': 'strategy_performance',
        'key_columns': ['strategy_id', 'timestamp', 'symbol'],
        'sync_type': 'incremental',
        'timestamp_column': 'timestamp'
    },
    'market_data': {
        'source_table': 'market_data',
        'target_table': 'market_data',
        'key_columns': ['symbol', 'timestamp'],
        'sync_type': 'incremental',
        'timestamp_column': 'timestamp'
    },
    'trades': {
        'source_table': 'trades',
        'target_table': 'trades',
        'key_columns': ['trade_id'],
        'sync_type': 'incremental',
        'timestamp_column': 'entry_time'
    }
}

# Column Type Mappings
# Maps PostgreSQL types to ClickHouse types
TYPE_MAPPINGS = {
    'integer': 'UInt32',
    'bigint': 'UInt64',
    'smallint': 'UInt16',
    'decimal': 'Float64',
    'numeric': 'Float64',
    'real': 'Float32',
    'double precision': 'Float64',
    'varchar': 'String',
    'text': 'String',
    'char': 'String',
    'boolean': 'UInt8',
    'date': 'Date',
    'timestamp': 'DateTime',
    'timestamptz': 'DateTime',
    'json': 'String',
    'jsonb': 'String'
}

# Performance Thresholds
MAX_RECORDS_PER_SYNC = 100000
MAX_SYNC_DURATION_SECONDS = 300
WARNING_RECORD_THRESHOLD = 50000

# Logging Configuration
LOG_TABLE = 'etl_logs'
LOG_LEVEL = os.getenv('ETL_LOG_LEVEL', 'INFO')

# Data Validation Rules
VALIDATION_RULES = {
    'strategy_backtests': {
        'required_columns': ['strategy_id', 'backtest_date', 'total_return'],
        'numeric_columns': ['total_return', 'sharpe_ratio', 'max_drawdown', 'win_rate'],
        'nullable_columns': ['profit_factor', 'avg_trade']
    },
    'strategy_performance': {
        'required_columns': ['strategy_id', 'timestamp', 'symbol'],
        'numeric_columns': ['current_pnl', 'unrealized_pnl', 'position_size'],
        'nullable_columns': ['exit_price', 'pnl']
    }
}
