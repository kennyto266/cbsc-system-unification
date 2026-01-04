"""
Enhanced Secure SQL Framework
增強版安全 SQL 查詢框架

提供防範 SQL 注入的安全查詢構造器
"""

import re
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

try:
    import psycopg2.sql
    from psycopg2 import sql
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    logging.warning("psycopg2 not available, limited security features")

logger = logging.getLogger('secure_sql_framework')


class SQLOperationType(Enum):
    """支持的 SQL 操作類型"""
    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    CREATE = "CREATE"
    ALTER = "ALTER"
    DROP = "DROP"


class SecurityError(Exception):
    """安全相關錯誤"""
    pass


@dataclass
class CBSCSchemaDefinition:
    """CBSC 系統數據庫模式定義"""
    table_name: str
    allowed_columns: List[str]
    primary_key: str
    sensitive_columns: List[str] = None
    foreign_keys: Dict[str, str] = None
    validation_rules: Dict[str, Dict[str, Any]] = None


class EnhancedSecureSQLFramework:
    """
    增強版安全 SQL 查詢框架

    功能：
    1. 表名白名單驗證
    2. 列名白名單驗證
    3. 參數化查詢構造
    4. SQL 注入檢測
    5. 輸入驗證和清理
    """

    # CBSC 系統數據庫模式
    CBSC_SECURE_SCHEMA = {
        'strategy_results': CBSCSchemaDefinition(
            table_name='strategy_results',
            allowed_columns=[
                'id', 'strategy_name', 'parameters', 'sharpe_ratio',
                'total_return', 'max_drawdown', 'volatility', 'win_rate',
                'created_at', 'updated_at'
            ],
            primary_key='id',
            sensitive_columns=['parameters']
        ),
        'cbsc_sentiment_data': CBSCSchemaDefinition(
            table_name='cbsc_sentiment_data',
            allowed_columns=[
                'id', 'timestamp', 'bull_bear_ratio', 'sentiment_score',
                'volume', 'price_impact', 'confidence_level'
            ],
            primary_key='id',
            validation_rules={
                'bull_bear_ratio': {'min': 0, 'max': 10, 'type': 'float'},
                'sentiment_score': {'min': -1, 'max': 1, 'type': 'float'}
            }
        ),
        'user_strategies': CBSCSchemaDefinition(
            table_name='user_strategies',
            allowed_columns=[
                'id', 'user_id', 'strategy_type', 'parameters',
                'is_active', 'performance_metrics'
            ],
            primary_key='id',
            foreign_keys={'user_id': 'users.id'}
        ),
        'strategy_signals': CBSCSchemaDefinition(
            table_name='strategy_signals',
            allowed_columns=[
                'id', 'strategy_id', 'timestamp', 'symbol', 'signal_type',
                'confidence', 'strength', 'metadata'
            ],
            primary_key='id'
        ),
        'backtest_results': CBSCSchemaDefinition(
            table_name='backtest_results',
            allowed_columns=[
                'id', 'strategy_id', 'symbol', 'start_date', 'end_date',
                'total_return', 'sharpe_ratio', 'max_drawdown', 'win_rate',
                'total_trades', 'created_at'
            ],
            primary_key='id'
        ),
        'audit_logs': CBSCSchemaDefinition(
            table_name='audit_logs',
            allowed_columns=[
                'id', 'timestamp', 'user_id', 'event_type', 'severity',
                'success', 'details', 'ip_address', 'user_agent'
            ],
            primary_key='id'
        ),
        'users': CBSCSchemaDefinition(
            table_name='users',
            allowed_columns=[
                'id', 'username', 'email', 'is_active', 'email_verified',
                'created_at', 'updated_at'
            ],
            primary_key='id',
            sensitive_columns=['email']
        ),
    }

    # 分區表前綴白名單
    ALLOWED_PARTITION_PREFIXES = [
        'strategy_signals_', 'stock_data_', 'strategy_executions_',
        'backtest_results_', 'performance_metrics_'
    ]

    # SQL 注入檢測模式
    INJECTION_PATTERNS = [
        r'--',
        r'/\*',
        r'\*/',
        r'union.*select',
        r'drop.*table',
        r'delete.*from',
        r'insert.*into',
        r'update.*set',
        r'waitfor.*delay',
        r'benchmark\s*\(',
        r'sleep\s*\(',
        r'information_schema',
        r'sysobjects',
        r'syscolumns',
        r'xp_cmdshell',
        r'sp_executesql',
    ]

    def __init__(self):
        """初始化框架"""
        self.injection_detector = AdvancedInjectionDetector()
        self.query_validator = CBSCQueryValidator(self.CBSC_SECURE_SCHEMA)

    def validate_table_name(self, table_name: str) -> bool:
        """
        驗證表名是否在白名單中

        Args:
            table_name: 要驗證的表名

        Returns:
            bool: 表名是否有效

        Raises:
            SecurityError: 表名無效
        """
        # 檢查完整表名
        if table_name in self.CBSC_SECURE_SCHEMA:
            return True

        # 檢查分區表
        for prefix in self.ALLOWED_PARTITION_PREFIXES:
            if table_name.startswith(prefix):
                # 驗證分區表名格式
                suffix = table_name[len(prefix):]
                if self._is_valid_partition_suffix(suffix):
                    return True

        raise SecurityError(f"Invalid table name: {table_name}")

    def _is_valid_partition_suffix(self, suffix: str) -> bool:
        """
        驗證分區後綴格式

        支持格式:
        - YYYY_MM (月份分區): strategy_signals_2025_01
        - YYYYMMDD (日期分區): strategy_signals_20250125
        """
        # 月份分區格式: YYYY_MM
        if re.match(r'^\d{4}_\d{2}$', suffix):
            return True

        # 日期分區格式: YYYYMMDD
        if re.match(r'^\d{8}$', suffix):
            return True

        return False

    def validate_column_name(self, table_name: str, column_name: str) -> bool:
        """
        驗證列名是否允許

        Args:
            table_name: 表名
            column_name: 列名

        Returns:
            bool: 列名是否有效

        Raises:
            SecurityError: 列名無效
        """
        self.validate_table_name(table_name)

        schema = self.CBSC_SECURE_SCHEMA.get(table_name)
        if not schema:
            raise SecurityError(f"Table schema not found: {table_name}")

        if column_name not in schema.allowed_columns:
            raise SecurityError(
                f"Column '{column_name}' not allowed in table '{table_name}'"
            )

        return True

    def validate_input(self, value: Any, field_name: str = None,
                      table_name: str = None) -> bool:
        """
        驗證輸入值

        Args:
            value: 要驗證的值
            field_name: 字段名（可選）
            table_name: 表名（可選）

        Returns:
            bool: 輸入是否有效
        """
        # 檢測 SQL 注入
        if self.injection_detector.detect(value):
            raise SecurityError(
                f"SQL injection detected in value: {str(value)[:50]}..."
            )

        # 如果提供了表和字段，進行類型驗證
        if table_name and field_name:
            schema = self.CBSC_SECURE_SCHEMA.get(table_name)
            if schema and schema.validation_rules:
                rules = schema.validation_rules.get(field_name)
                if rules:
                    self._validate_by_rules(value, rules)

        return True

    def _validate_by_rules(self, value: Any, rules: Dict[str, Any]):
        """根據規則驗證值"""
        value_type = rules.get('type')
        min_val = rules.get('min')
        max_val = rules.get('max')

        if value_type == 'float':
            try:
                float_val = float(value)
                if min_val is not None and float_val < min_val:
                    raise SecurityError(f"Value {value} below minimum {min_val}")
                if max_val is not None and float_val > max_val:
                    raise SecurityError(f"Value {value} above maximum {max_val}")
            except (ValueError, TypeError):
                raise SecurityError(f"Invalid float value: {value}")

    def create_secure_query(
        self,
        table: str,
        operation: SQLOperationType,
        columns: List[str] = None,
        where_clause: str = None,
        where_params: Dict[str, Any] = None,
        limit: int = None
    ) -> Tuple[str, List[Any]]:
        """
        創建安全 SQL 查詢

        Args:
            table: 表名
            operation: 操作類型
            columns: 列名列表
            where_clause: WHERE 子句（使用命名參數）
            where_params: WHERE 參數值
            limit: 限制結果數量

        Returns:
            Tuple[查詢字符串, 參數列表]
        """
        # 驗證表名
        self.validate_table_name(table)

        # 驗證操作類型
        if operation not in SQLOperationType:
            raise SecurityError(f"Invalid operation: {operation}")

        # 驗證列名
        if columns:
            for col in columns:
                self.validate_column_name(table, col)

        # 構造查詢
        query_parts = []
        params = []

        # SELECT 查詢
        if operation == SQLOperationType.SELECT:
            if columns:
                query_parts.append(f"SELECT {', '.join(columns)}")
            else:
                query_parts.append("SELECT *")
            query_parts.append(f"FROM {table}")

        # INSERT 查詢
        elif operation == SQLOperationType.INSERT:
            if not columns:
                raise SecurityError("Columns required for INSERT")
            query_parts.append(f"INSERT INTO {table} ({', '.join(columns)})")
            query_parts.append(f"VALUES ({', '.join(['%s'] * len(columns))})")

        # UPDATE 查詢
        elif operation == SQLOperationType.UPDATE:
            if not columns:
                raise SecurityError("Columns required for UPDATE")
            set_clause = ', '.join([f"{col} = %s" for col in columns])
            query_parts.append(f"UPDATE {table}")
            query_parts.append(f"SET {set_clause}")

        # DELETE 查詢
        elif operation == SQLOperationType.DELETE:
            query_parts.append(f"DELETE FROM {table}")

        # WHERE 子句
        if where_clause and where_params:
            # 驗證 WHERE 參數
            for key, value in where_params.items():
                self.validate_input(value, key, table)
                params.append(value)
            query_parts.append(f"WHERE {where_clause}")

        # LIMIT
        if limit:
            query_parts.append(f"LIMIT {int(limit)}")

        query = ' '.join(query_parts)

        return query, params

    def create_safe_partition(
        self,
        cursor,
        table_name: str,
        partition_name: str,
        start_date: datetime,
        end_date: datetime
    ):
        """
        安全創建分區表

        使用 psycopg2.sql 模塊防止 SQL 注入
        """
        if not PSYCOPG2_AVAILABLE:
            raise SecurityError("psycopg2 required for partition operations")

        # 驗證表名
        self.validate_table_name(table_name)

        # 驗證分區名
        if not partition_name.startswith(table_name):
            raise SecurityError(f"Partition name must start with table name: {table_name}")

        suffix = partition_name[len(table_name) + 1:]  # Remove underscore
        if not self._is_valid_partition_suffix(suffix):
            raise SecurityError(f"Invalid partition suffix: {suffix}")

        # 使用 psycopg2.sql 安全構造查詢
        query = sql.SQL("""
            CREATE TABLE IF NOT EXISTS {}
            PARTITION OF {}
            FOR VALUES FROM (%s) TO (%s)
        """).format(
            sql.Identifier(partition_name),
            sql.Identifier(table_name)
        )

        cursor.execute(query, (start_date, end_date))
        logger.info(f"Created partition: {partition_name}")

    def safe_drop_partition(self, cursor, partition_name: str):
        """
        安全刪除分區表

        Args:
            cursor: 數據庫游標
            partition_name: 分區表名
        """
        if not PSYCOPG2_AVAILABLE:
            raise SecurityError("psycopg2 required for partition operations")

        # 驗證分區名
        valid_prefix = False
        for prefix in self.ALLOWED_PARTITION_PREFIXES:
            if partition_name.startswith(prefix):
                valid_prefix = True
                break

        if not valid_prefix:
            raise SecurityError(
                f"Invalid partition name: {partition_name}. "
                f"Must start with one of: {self.ALLOWED_PARTITION_PREFIXES}"
            )

        # 使用 Identifier 防止注入
        query = sql.SQL("DROP TABLE IF EXISTS {} CASCADE").format(
            sql.Identifier(partition_name)
        )

        cursor.execute(query)
        logger.info(f"Dropped partition: {partition_name}")

    def refresh_materialized_view_safe(self, cursor, view_name: str):
        """
        安全刷新物化視圖

        Args:
            cursor: 數據庫游標
            view_name: 視圖名
        """
        if not PSYCOPG2_AVAILABLE:
            raise SecurityError("psycopg2 required for view operations")

        # 視圖名白名單
        ALLOWED_VIEWS = [
            'v_strategy_signal_summary',
            'v_strategy_signals_daily',
            'v_strategy_signals_weekly',
            'v_stock_data_daily',
            'v_performance_summary'
        ]

        if view_name not in ALLOWED_VIEWS:
            raise SecurityError(
                f"View '{view_name}' not in allowed list: {ALLOWED_VIEWS}"
            )

        query = sql.SQL("REFRESH MATERIALIZED VIEW CONCURRENTLY {}").format(
            sql.Identifier(view_name)
        )

        cursor.execute(query)
        logger.info(f"Refreshed materialized view: {view_name}")


class AdvancedInjectionDetector:
    """高級 SQL 注入檢測器"""

    def __init__(self):
        """初始化檢測器"""
        self.injection_patterns = [
            # 基礎注入模式
            r'--',
            r'/\*',
            r'\*/',

            # 高級注入模式
            r'union.*select',
            r'drop.*table',
            r'delete.*from',
            r'insert.*into',
            r'update.*set',
            r'waitfor.*delay',
            r'benchmark\s*\(',
            r'sleep\s*\(',
            r'information_schema',
            r'sysobjects',
            r'syscolumns',
            r'xp_cmdshell',
            r'sp_executesql',

            # CBSC 特定模式
            r'cbsc_.*\s*;',
            r'strategy_.*\s*;',
        ]

        # 編譯正則表達式
        self.compiled_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.injection_patterns
        ]

    def detect(self, value: Any) -> bool:
        """
        檢測值是否包含 SQL 注入

        Args:
            value: 要檢測的值

        Returns:
            bool: 是否檢測到注入
        """
        if value is None:
            return False

        value_str = str(value)

        for pattern in self.compiled_patterns:
            if pattern.search(value_str):
                logger.warning(f"SQL injection pattern detected: {pattern.pattern}")
                return True

        return False

    def scan_query(self, query: str) -> Dict[str, Any]:
        """
        掃描查詢是否存在注入風險

        Args:
            query: SQL 查詢字符串

        Returns:
            Dict: 掃描結果
        """
        results = {
            'is_safe': True,
            'risk_level': 'LOW',
            'detected_patterns': [],
            'recommendations': []
        }

        for pattern in self.compiled_patterns:
            matches = pattern.findall(query)
            if matches:
                results['is_safe'] = False
                results['risk_level'] = 'HIGH'
                results['detected_patterns'].append({
                    'pattern': pattern.pattern,
                    'matches': matches
                })

        if not results['is_safe']:
            results['recommendations'].append(
                "Use parameterized queries instead of string concatenation"
            )
            results['recommendations'].append(
                "Validate and sanitize all user inputs"
            )

        return results


class CBSCQueryValidator:
    """CBSC 系統查詢驗證器"""

    def __init__(self, schema: Dict[str, CBSCSchemaDefinition]):
        """
        初始化驗證器

        Args:
            schema: 數據庫模式定義
        """
        self.schema = schema

    def validate_select_query(
        self,
        table: str,
        columns: List[str],
        where_clause: str = None,
        limit: int = None
    ) -> bool:
        """
        驗證 SELECT 查詢

        Args:
            table: 表名
            columns: 列名列表
            where_clause: WHERE 子句
            limit: 限制數量

        Returns:
            bool: 查詢是否有效
        """
        # 驗證表名
        if table not in self.schema:
            raise SecurityError(f"Table not in schema: {table}")

        schema_def = self.schema[table]

        # 驗證列名
        for col in columns:
            if col not in schema_def.allowed_columns:
                raise SecurityError(
                    f"Column '{col}' not allowed in table '{table}'"
                )

        # 驗證 WHERE 子句（檢查是否有直接拼接）
        if where_clause:
            if '%' in where_clause or '$' in where_clause:
                # 檢查是否使用了參數化
                if not re.search(r'(%s|\$\d+|:\w+)', where_clause):
                    raise SecurityError(
                        "WHERE clause must use parameterized queries"
                    )

        # 驗證 LIMIT
        if limit is not None:
            if not isinstance(limit, int) or limit < 0 or limit > 10000:
                raise SecurityError(f"Invalid LIMIT value: {limit}")

        return True


# 單例模式
_secure_framework_instance = None

def get_secure_framework() -> EnhancedSecureSQLFramework:
    """獲取安全框架實例"""
    global _secure_framework_instance
    if _secure_framework_instance is None:
        _secure_framework_instance = EnhancedSecureSQLFramework()
    return _secure_framework_instance
