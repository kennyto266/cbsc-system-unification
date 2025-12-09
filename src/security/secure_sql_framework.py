"""
Secure SQL Framework - Prevents SQL Injection Attacks
Created: 2025-11-30
Purpose: Provide safe SQL query construction and parameterized queries
"""

import re
import logging
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass
from contextlib import contextmanager
import sqlite3
from enum import Enum

logger = logging.getLogger(__name__)

class SQLInjectionError(Exception):
    """SQL injection attempt detected"""
    pass

class QueryType(Enum):
    """SQL query types"""
    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    CREATE = "CREATE"
    DROP = "DROP"
    ALTER = "ALTER"

@dataclass
class SafeQuery:
    """Safe SQL query with parameters"""
    query_type: QueryType
    template: str
    parameters: Tuple[Any, ...]
    table_names: List[str]
    column_names: List[str]

class SecureSQLFramework:
    """Secure SQL query framework with injection protection"""

    # Allowed SQL keywords
    ALLOWED_KEYWORDS = {
        'SELECT', 'FROM', 'WHERE', 'INSERT', 'INTO', 'VALUES', 'UPDATE', 'SET',
        'DELETE', 'CREATE', 'TABLE', 'DROP', 'ALTER', 'JOIN', 'INNER', 'LEFT',
        'RIGHT', 'OUTER', 'ON', 'AND', 'OR', 'NOT', 'IN', 'EXISTS', 'BETWEEN',
        'LIKE', 'IS', 'NULL', 'ORDER', 'BY', 'GROUP', 'HAVING', 'LIMIT', 'OFFSET',
        'AS', 'DISTINCT', 'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'UNION', 'ALL'
    }

    # Whitelisted table and column patterns
    TABLE_NAME_PATTERN = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')
    COLUMN_NAME_PATTERN = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')

    # SQL injection detection patterns
    INJECTION_PATTERNS = [
        r'(--)',               # SQL comments
        r'(/\\*)',             # Multi-line comment start
        r'(\\*/)',             # Multi-line comment end
        r'(\\bor\\b.*=.*\\bor\\b)',  # OR injection
        r'(\\band\\b.*=.*\\band\\b)', # AND injection
        r'(union.*select)',    # UNION attack
        r'(drop.*table)',      # DROP attack
        r'(delete.*from)',     # DELETE attack
        r'(insert.*into)',     # INSERT attack
        r'(update.*set)',      # UPDATE attack
        r'(exec.*\\()',        # EXEC attack
        r'(xp_cmdshell)',      # SQL Server attack
        r'(sp_executesql)',    # SQL Server attack
        r'(;\\s*(drop|delete|insert|update|create|alter))',  # Stacked queries
    ]

    def __init__(self, allowed_tables: Optional[Dict[str, List[str]]] = None):
        """
        Initialize secure SQL framework

        Args:
            allowed_tables: Dict of table names to allowed column names
        """
        self.allowed_tables = allowed_tables or {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def validate_table_name(self, table_name: str) -> bool:
        """Validate table name against injection patterns"""
        if not self.TABLE_NAME_PATTERN.match(table_name):
            logger.warning(f"Invalid table name format: {table_name}")
            return False

        # Check against injection patterns
        for pattern in self.INJECTION_PATTERNS:
            if re.search(pattern, table_name, re.IGNORECASE):
                logger.warning(f"Potential SQL injection in table name: {table_name}")
                return False

        # Check against allowed tables
        if self.allowed_tables and table_name not in self.allowed_tables:
            logger.warning(f"Table not in allowed list: {table_name}")
            return False

        return True

    def validate_column_name(self, column_name: str, table_name: Optional[str] = None) -> bool:
        """Validate column name against injection patterns"""
        if not self.COLUMN_NAME_PATTERN.match(column_name):
            logger.warning(f"Invalid column name format: {column_name}")
            return False

        # Check against injection patterns
        for pattern in self.INJECTION_PATTERNS:
            if re.search(pattern, column_name, re.IGNORECASE):
                logger.warning(f"Potential SQL injection in column name: {column_name}")
                return False

        # Check against allowed columns for the table
        if table_name and table_name in self.allowed_tables:
            allowed_columns = self.allowed_tables[table_name]
            if column_name not in allowed_columns:
                logger.warning(f"Column not in allowed list for table {table_name}: {column_name}")
                return False

        return True

    def validate_where_clause(self, where_clause: str) -> bool:
        """Validate WHERE clause for injection attempts"""
        # Remove parameterized query patterns first
        cleaned = re.sub(r'%s|\\?|:\\w+', '', where_clause)

        # Check for injection patterns
        for pattern in self.INJECTION_PATTERNS:
            if re.search(pattern, cleaned, re.IGNORECASE):
                logger.warning(f"Potential SQL injection in WHERE clause: {where_clause}")
                return False

        return True

    def create_safe_select(self, table_name: str, columns: List[str] = None,
                          where_clause: str = None, parameters: Tuple = None,
                          order_by: str = None, limit: int = None) -> SafeQuery:
        """Create safe SELECT query"""
        if not self.validate_table_name(table_name):
            raise SQLInjectionError(f"Invalid table name: {table_name}")

        # Validate columns
        if columns is None:
            columns = ['*']
        else:
            for col in columns:
                if col != '*' and not self.validate_column_name(col, table_name):
                    raise SQLInjectionError(f"Invalid column name: {col}")

        # Build query template
        columns_str = ', '.join(columns)
        query_template = f"SELECT {columns_str} FROM {table_name}"

        # Add WHERE clause
        if where_clause:
            if not self.validate_where_clause(where_clause):
                raise SQLInjectionError(f"Invalid WHERE clause: {where_clause}")
            query_template += f" WHERE {where_clause}"

        # Add ORDER BY
        if order_by:
            # Simple validation for ORDER BY
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*(\\s+(ASC|DESC))?$', order_by):
                raise SQLInjectionError(f"Invalid ORDER BY clause: {order_by}")
            query_template += f" ORDER BY {order_by}"

        # Add LIMIT
        if limit:
            if not isinstance(limit, int) or limit <= 0:
                raise SQLInjectionError(f"Invalid LIMIT value: {limit}")
            query_template += f" LIMIT {limit}"

        return SafeQuery(
            query_type=QueryType.SELECT,
            template=query_template,
            parameters=parameters or tuple(),
            table_names=[table_name],
            column_names=columns
        )

    def create_safe_insert(self, table_name: str, columns: List[str],
                          values: Tuple[Any, ...]) -> SafeQuery:
        """Create safe INSERT query"""
        if not self.validate_table_name(table_name):
            raise SQLInjectionError(f"Invalid table name: {table_name}")

        # Validate columns
        for col in columns:
            if not self.validate_column_name(col, table_name):
                raise SQLInjectionError(f"Invalid column name: {col}")

        # Build query template
        columns_str = ', '.join(columns)
        placeholders = ', '.join(['?'] * len(values))
        query_template = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"

        return SafeQuery(
            query_type=QueryType.INSERT,
            template=query_template,
            parameters=values,
            table_names=[table_name],
            column_names=columns
        )

    def create_safe_update(self, table_name: str, set_clauses: List[str],
                          where_clause: str = None, parameters: Tuple = None) -> SafeQuery:
        """Create safe UPDATE query"""
        if not self.validate_table_name(table_name):
            raise SQLInjectionError(f"Invalid table name: {table_name}")

        # Validate SET clauses (format: column_name = ?)
        for clause in set_clauses:
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*\\s*=\\s*\\?$', clause):
                raise SQLInjectionError(f"Invalid SET clause: {clause}")

        # Build query template
        set_str = ', '.join(set_clauses)
        query_template = f"UPDATE {table_name} SET {set_str}"

        # Add WHERE clause
        if where_clause:
            if not self.validate_where_clause(where_clause):
                raise SQLInjectionError(f"Invalid WHERE clause: {where_clause}")
            query_template += f" WHERE {where_clause}"

        return SafeQuery(
            query_type=QueryType.UPDATE,
            template=query_template,
            parameters=parameters or tuple(),
            table_names=[table_name],
            column_names=[clause.split('=')[0].strip() for clause in set_clauses]
        )

    def create_safe_delete(self, table_name: str, where_clause: str = None,
                          parameters: Tuple = None) -> SafeQuery:
        """Create safe DELETE query"""
        if not self.validate_table_name(table_name):
            raise SQLInjectionError(f"Invalid table name: {table_name}")

        query_template = f"DELETE FROM {table_name}"

        # Add WHERE clause (required for safety)
        if not where_clause:
            raise SQLInjectionError("DELETE without WHERE clause is not allowed")

        if not self.validate_where_clause(where_clause):
            raise SQLInjectionError(f"Invalid WHERE clause: {where_clause}")

        query_template += f" WHERE {where_clause}"

        return SafeQuery(
            query_type=QueryType.DELETE,
            template=query_template,
            parameters=parameters or tuple(),
            table_names=[table_name],
            column_names=[]
        )

    @contextmanager
    def safe_execute(self, connection, query: SafeQuery):
        """Safely execute query with error handling"""
        cursor = connection.cursor()
        try:
            # Log query for audit
            self.logger.info(f"Executing {query.query_type.value}: {query.template}")
            self.logger.debug(f"Parameters: {query.parameters}")

            # Execute query
            cursor.execute(query.template, query.parameters)

            # Return cursor for fetching results
            yield cursor

            connection.commit()

        except Exception as e:
            connection.rollback()
            self.logger.error(f"Query execution failed: {e}")
            raise
        finally:
            cursor.close()

# Predefined table schemas for the quantitative trading system
QUANT_TRADING_SCHEMA = {
    'strategy_results': [
        'id', 'strategy_name', 'parameters', 'sharpe_ratio', 'total_return',
        'max_drawdown', 'volatility', 'win_rate', 'created_at'
    ],
    'performance_metrics': [
        'id', 'strategy_id', 'date', 'return', 'cumulative_return',
        'volatility', 'drawdown', 'var'
    ],
    'parameter_optimization': [
        'id', 'strategy_id', 'parameter_name', 'parameter_value',
        'metric_name', 'metric_value', 'optimization_round'
    ],
    'risk_metrics': [
        'id', 'strategy_id', 'date', 'var_95', 'cvar_95', 'beta',
        'alpha', 'information_ratio'
    ]
}

# Global instance for the application
SECURE_SQL = SecureSQLFramework(QUANT_TRADING_SCHEMA)

def secure_read_sql(connection, query: SafeQuery) -> List[Dict]:
    """Safely read data using pandas or manual fetch"""
    try:
        with SECURE_SQL.safe_execute(connection, query) as cursor:
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()

            # Convert to list of dictionaries
            result = []
            for row in rows:
                result.append(dict(zip(columns, row)))

            return result

    except Exception as e:
        logger.error(f"Secure read SQL failed: {e}")
        raise

# Utility functions for common operations
def get_strategy_performance(connection, strategy_id: int = None,
                           start_date: str = None, end_date: str = None) -> List[Dict]:
    """Get strategy performance data safely"""

    conditions = []
    parameters = []

    if strategy_id:
        conditions.append("strategy_id = ?")
        parameters.append(strategy_id)

    if start_date:
        conditions.append("date >= ?")
        parameters.append(start_date)

    if end_date:
        conditions.append("date <= ?")
        parameters.append(end_date)

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    query = SECURE_SQL.create_safe_select(
        table_name="performance_metrics",
        columns=["*"],
        where_clause=where_clause,
        parameters=tuple(parameters),
        order_by="date"
    )

    return secure_read_sql(connection, query)

def save_strategy_result(connection, strategy_name: str, parameters: Dict[str, Any],
                        metrics: Dict[str, float]) -> int:
    """Save strategy results safely"""

    # Serialize parameters and metrics
    import json
    params_json = json.dumps(parameters)
    metrics_json = json.dumps(metrics)

    query = SECURE_SQL.create_safe_insert(
        table_name="strategy_results",
        columns=["strategy_name", "parameters", "sharpe_ratio", "total_return",
                "max_drawdown", "volatility", "win_rate"],
        values=(strategy_name, params_json,
               metrics.get("sharpe_ratio", 0.0),
               metrics.get("total_return", 0.0),
               metrics.get("max_drawdown", 0.0),
               metrics.get("volatility", 0.0),
               metrics.get("win_rate", 0.0))
    )

    try:
        with SECURE_SQL.safe_execute(connection, query) as cursor:
            return cursor.lastrowid
    except Exception as e:
        logger.error(f"Failed to save strategy result: {e}")
        raise

def search_strategies(connection, search_term: str = None,
                     min_sharpe: float = None) -> List[Dict]:
    """Search strategies with safe parameters"""

    conditions = []
    parameters = []

    if search_term:
        conditions.append("strategy_name LIKE ?")
        parameters.append(f"%{search_term}%")

    if min_sharpe:
        conditions.append("sharpe_ratio >= ?")
        parameters.append(min_sharpe)

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    query = SECURE_SQL.create_safe_select(
        table_name="strategy_results",
        columns=["*"],
        where_clause=where_clause,
        parameters=tuple(parameters),
        order_by="sharpe_ratio DESC"
    )

    return secure_read_sql(connection, query)