"""
Data Flow Integrity Validator
Comprehensive data integrity validation across the entire system
"""

import asyncio
import hashlib
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import asyncpg
import redis.asyncio as aioredis
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import aiohttp
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataFlowStage(Enum):
    """Data flow stages in the system"""
    MARKET_DATA_INGESTION = "market_data_ingestion"
    DATA_VALIDATION = "data_validation"
    INDICATOR_CALCULATION = "indicator_calculation"
    STRATEGY_EXECUTION = "strategy_execution"
    SIGNAL_GENERATION = "signal_generation"
    ORDER_GENERATION = "order_generation"
    PORTFOLIO_UPDATE = "portfolio_update"
    PERFORMANCE_CALCULATION = "performance_calculation"
    RISK_ASSESSMENT = "risk_assessment"
    REPORTING = "reporting"


class IntegrityCheckType(Enum):
    """Types of integrity checks"""
    CHECKSUM_VALIDATION = "checksum_validation"
    CONSISTENCY_CHECK = "consistency_check"
    REFERENTIAL_INTEGRITY = "referential_integrity"
    TEMPORAL_INTEGRITY = "temporal_integrity"
    BUSINESS_RULE_VALIDATION = "business_rule_validation"
    DATA_TYPE_VALIDATION = "data_type_validation"
    RANGE_VALIDATION = "range_validation"
    COMPLETENESS_CHECK = "completeness_check"


@dataclass
class DataRecord:
    """Data record for integrity checking"""
    id: str
    stage: DataFlowStage
    data: Dict[str, Any]
    timestamp: datetime
    checksum: str
    source: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IntegrityViolation:
    """Integrity violation record"""
    id: str
    stage: DataFlowStage
    check_type: IntegrityCheckType
    severity: str  # "low", "medium", "high", "critical"
    description: str
    affected_records: List[str]
    detected_at: datetime
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """Result of integrity validation"""
    stage: DataFlowStage
    check_type: IntegrityCheckType
    passed: bool
    violations: List[IntegrityViolation] = field(default_factory=list)
    execution_time: float = 0.0
    records_checked: int = 0


class DataFlowIntegrityValidator:
    """Comprehensive data flow integrity validator"""

    def __init__(self):
        self.db_config = {
            "host": "localhost",
            "port": 5432,
            "database": "cbsc_test",
            "user": "test_user",
            "password": "test_password"
        }

        self.redis_config = {
            "host": "localhost",
            "port": 6379,
            "db": 2  # Use separate DB for integrity checks
        }

        self.influx_config = {
            "url": "http://localhost:8086",
            "token": "test_token",
            "org": "cbsc",
            "bucket": "integrity_checks"
        }

        # Integrity thresholds
        self.thresholds = {
            "max_data_delay_seconds": 300,  # 5 minutes
            "checksum_mismatch_tolerance": 0,
            "consistency_deviation_threshold": 0.01,  # 1%
            "missing_data_threshold": 0.05,  # 5%
            "price_change_threshold": 0.5,  # 50% max price change
            "volume_spike_threshold": 10.0,  # 10x normal volume
            "min_portfolio_balance": -0.1  # Allow 10% temporary negative
        }

        # Monitoring cache
        self.redis_client: Optional[aioredis.Redis] = None
        self.db_pool: Optional[asyncpg.Pool] = None
        self.influx_client: Optional[InfluxDBClient] = None

    async def setup(self):
        """Setup validator connections and initialization"""
        logger.info("Setting up data flow integrity validator...")

        # Setup database connections
        self.db_pool = await asyncpg.create_pool(
            **self.db_config,
            min_size=5,
            max_size=20
        )

        # Setup Redis connection
        self.redis_client = aioredis.from_url(
            f"redis://{self.redis_config['host']}:{self.redis_config['port']}/{self.redis_config['db']}",
            decode_responses=True
        )

        # Setup InfluxDB connection
        self.influx_client = InfluxDBClient(**self.influx_config)

        # Create integrity check tables if not exists
        await self._setup_integrity_tables()

        logger.info("Data flow integrity validator setup complete")

    async def cleanup(self):
        """Cleanup validator connections"""
        if self.db_pool:
            await self.db_pool.close()
        if self.redis_client:
            await self.redis_client.close()
        if self.influx_client:
            self.influx_client.close()
        logger.info("Data flow integrity validator cleaned up")

    async def _setup_integrity_tables(self):
        """Setup integrity monitoring tables"""
        async with self.db_pool.acquire() as conn:
            # Create integrity checks table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS integrity_checks (
                    id SERIAL PRIMARY KEY,
                    stage VARCHAR(50) NOT NULL,
                    check_type VARCHAR(50) NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    violations_count INTEGER DEFAULT 0,
                    records_checked INTEGER DEFAULT 0,
                    execution_time FLOAT,
                    check_timestamp TIMESTAMP DEFAULT NOW(),
                    details JSONB
                )
            """)

            # Create integrity violations table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS integrity_violations (
                    id SERIAL PRIMARY KEY,
                    violation_id VARCHAR(100) UNIQUE NOT NULL,
                    stage VARCHAR(50) NOT NULL,
                    check_type VARCHAR(50) NOT NULL,
                    severity VARCHAR(20) NOT NULL,
                    description TEXT,
                    affected_records TEXT[],
                    detected_at TIMESTAMP DEFAULT NOW(),
                    resolved_at TIMESTAMP,
                    details JSONB
                )
            """)

            # Create indexes
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_integrity_checks_stage ON integrity_checks(stage)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_integrity_checks_timestamp ON integrity_checks(check_timestamp)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_integrity_violations_stage ON integrity_violations(stage)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_integrity_violations_severity ON integrity_violations(severity)")

    def _calculate_checksum(self, data: Dict[str, Any]) -> str:
        """Calculate checksum for data integrity"""
        # Sort data for consistent checksum calculation
        sorted_data = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(sorted_data.encode()).hexdigest()

    async def validate_market_data_integrity(self,
                                           symbols: List[str] = None,
                                           start_time: datetime = None,
                                           end_time: datetime = None) -> ValidationResult:
        """Validate market data integrity"""
        logger.info("Validating market data integrity...")

        if symbols is None:
            symbols = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"]

        if start_time is None:
            start_time = datetime.utcnow() - timedelta(hours=24)
        if end_time is None:
            end_time = datetime.utcnow()

        start_validation = time.time()
        violations = []
        records_checked = 0

        try:
            # Check data completeness
            for symbol in symbols:
                async with self.db_pool.acquire() as conn:
                    # Get expected data points
                    expected_points = await conn.fetchval("""
                        SELECT COUNT(*)
                        FROM market_data
                        WHERE symbol = $1
                        AND timestamp BETWEEN $2 AND $3
                    """, symbol, start_time, end_time)

                    # Get actual data points
                    actual_points = await conn.fetchval("""
                        SELECT COUNT(*)
                        FROM market_data
                        WHERE symbol = $1
                        AND timestamp BETWEEN $2 AND $3
                        AND price IS NOT NULL
                        AND volume IS NOT NULL
                    """, symbol, start_time, end_time)

                    records_checked += actual_points

                    # Check for missing data
                    if expected_points > 0:
                        missing_rate = 1 - (actual_points / expected_points)
                        if missing_rate > self.thresholds["missing_data_threshold"]:
                            violations.append(IntegrityViolation(
                                id=f"missing_data_{symbol}_{int(time.time())}",
                                stage=DataFlowStage.MARKET_DATA_INGESTION,
                                check_type=IntegrityCheckType.COMPLETENESS_CHECK,
                                severity="high" if missing_rate > 0.1 else "medium",
                                description=f"High missing data rate for {symbol}: {missing_rate:.2%}",
                                affected_records=[symbol],
                                detected_at=datetime.utcnow(),
                                details={
                                    "symbol": symbol,
                                    "expected_points": expected_points,
                                    "actual_points": actual_points,
                                    "missing_rate": missing_rate
                                }
                            ))

                    # Check for price anomalies
                    price_anomalies = await conn.fetch("""
                        WITH price_changes AS (
                            SELECT
                                symbol,
                                timestamp,
                                price,
                                LAG(price) OVER (ORDER BY timestamp) as prev_price,
                                ABS(price - LAG(price) OVER (ORDER BY timestamp)) / LAG(price) OVER (ORDER BY timestamp) as price_change
                            FROM market_data
                            WHERE symbol = $1
                            AND timestamp BETWEEN $2 AND $3
                            AND price IS NOT NULL
                        )
                        SELECT symbol, timestamp, price, prev_price, price_change
                        FROM price_changes
                        WHERE price_change > $4
                        ORDER BY price_change DESC
                        LIMIT 10
                    """, symbol, start_time, end_time, self.thresholds["price_change_threshold"])

                    for anomaly in price_anomalies:
                        violations.append(IntegrityViolation(
                            id=f"price_anomaly_{symbol}_{anomaly['timestamp'].isoformat()}",
                            stage=DataFlowStage.MARKET_DATA_INGESTION,
                            check_type=IntegrityCheckType.RANGE_VALIDATION,
                            severity="medium",
                            description=f"Price anomaly detected for {symbol}: {anomaly['price_change']:.2%} change",
                            affected_records=[f"{symbol}_{anomaly['timestamp'].isoformat()}"],
                            detected_at=datetime.utcnow(),
                            details={
                                "symbol": symbol,
                                "timestamp": anomaly['timestamp'].isoformat(),
                                "price": float(anomaly['price']),
                                "prev_price": float(anomaly['prev_price']) if anomaly['prev_price'] else None,
                                "price_change": float(anomaly['price_change'])
                            }
                        ))

                    # Check for volume spikes
                    volume_spikes = await conn.fetch("""
                        WITH volume_stats AS (
                            SELECT
                                symbol,
                                AVG(volume) as avg_volume,
                                STDDEV(volume) as std_volume
                            FROM market_data
                            WHERE symbol = $1
                            AND timestamp BETWEEN $2 AND $3
                            AND volume IS NOT NULL
                        ),
                        volume_anomalies AS (
                            SELECT
                                md.symbol,
                                md.timestamp,
                                md.volume,
                                vs.avg_volume,
                                md.volume / NULLIF(vs.avg_volume, 0) as volume_ratio
                            FROM market_data md
                            CROSS JOIN volume_stats vs
                            WHERE md.symbol = $1
                            AND md.timestamp BETWEEN $2 AND $3
                            AND md.volume IS NOT NULL
                        )
                        SELECT symbol, timestamp, volume, avg_volume, volume_ratio
                        FROM volume_anomalies
                        WHERE volume_ratio > $4
                        ORDER BY volume_ratio DESC
                        LIMIT 5
                    """, symbol, start_time, end_time, self.thresholds["volume_spike_threshold"])

                    for spike in volume_spikes:
                        violations.append(IntegrityViolation(
                            id=f"volume_spike_{symbol}_{spike['timestamp'].isoformat()}",
                            stage=DataFlowStage.MARKET_DATA_INGESTION,
                            check_type=IntegrityCheckType.RANGE_VALIDATION,
                            severity="low",
                            description=f"Volume spike detected for {symbol}: {spike['volume_ratio']:.1f}x normal",
                            affected_records=[f"{symbol}_{spike['timestamp'].isoformat()}"],
                            detected_at=datetime.utcnow(),
                            details={
                                "symbol": symbol,
                                "timestamp": spike['timestamp'].isoformat(),
                                "volume": int(spike['volume']),
                                "avg_volume": float(spike['avg_volume']),
                                "volume_ratio": float(spike['volume_ratio'])
                            }
                        ))

            execution_time = time.time() - start_validation

            result = ValidationResult(
                stage=DataFlowStage.MARKET_DATA_INGESTION,
                check_type=IntegrityCheckType.CONSISTENCY_CHECK,
                passed=len(violations) == 0,
                violations=violations,
                execution_time=execution_time,
                records_checked=records_checked
            )

            # Log integrity check to database
            await self._log_integrity_check(result)

            return result

        except Exception as e:
            logger.error(f"Market data integrity validation error: {str(e)}")
            return ValidationResult(
                stage=DataFlowStage.MARKET_DATA_INGESTION,
                check_type=IntegrityCheckType.CONSISTENCY_CHECK,
                passed=False,
                violations=[IntegrityViolation(
                    id=f"validation_error_{int(time.time())}",
                    stage=DataFlowStage.MARKET_DATA_INGESTION,
                    check_type=IntegrityCheckType.CONSISTENCY_CHECK,
                    severity="critical",
                    description=f"Validation failed: {str(e)}",
                    affected_records=[],
                    detected_at=datetime.utcnow()
                )],
                execution_time=time.time() - start_validation
            )

    async def validate_strategy_execution_integrity(self,
                                                   strategy_id: int = None,
                                                   start_time: datetime = None,
                                                   end_time: datetime = None) -> ValidationResult:
        """Validate strategy execution integrity"""
        logger.info("Validating strategy execution integrity...")

        if start_time is None:
            start_time = datetime.utcnow() - timedelta(hours=24)
        if end_time is None:
            end_time = datetime.utcnow()

        start_validation = time.time()
        violations = []
        records_checked = 0

        try:
            async with self.db_pool.acquire() as conn:
                # Get strategy executions in time range
                if strategy_id:
                    executions = await conn.fetch("""
                        SELECT se.*, s.name as strategy_name, s.type as strategy_type
                        FROM strategy_executions se
                        JOIN strategies s ON se.strategy_id = s.id
                        WHERE se.strategy_id = $1
                        AND se.executed_at BETWEEN $2 AND $3
                        ORDER BY se.executed_at DESC
                        LIMIT 1000
                    """, strategy_id, start_time, end_time)
                else:
                    executions = await conn.fetch("""
                        SELECT se.*, s.name as strategy_name, s.type as strategy_type
                        FROM strategy_executions se
                        JOIN strategies s ON se.strategy_id = s.id
                        WHERE se.executed_at BETWEEN $1 AND $2
                        ORDER BY se.executed_at DESC
                        LIMIT 1000
                    """, start_time, end_time)

                records_checked = len(executions)

                for execution in executions:
                    # Check execution data consistency
                    if not execution['signal']:
                        violations.append(IntegrityViolation(
                            id=f"missing_signal_{execution['id']}",
                            stage=DataFlowStage.STRATEGY_EXECUTION,
                            check_type=IntegrityCheckType.COMPLETENESS_CHECK,
                            severity="medium",
                            description=f"Missing signal in strategy execution {execution['id']}",
                            affected_records=[str(execution['id'])],
                            detected_at=datetime.utcnow(),
                            details={
                                "execution_id": execution['id'],
                                "strategy_name": execution['strategy_name'],
                                "executed_at": execution['executed_at'].isoformat()
                            }
                        ))

                    # Check for duplicate executions
                    duplicate_check = await conn.fetchval("""
                        SELECT COUNT(*)
                        FROM strategy_executions
                        WHERE strategy_id = $1
                        AND executed_at = $2
                        AND id != $3
                    """, execution['strategy_id'], execution['executed_at'], execution['id'])

                    if duplicate_check > 0:
                        violations.append(IntegrityViolation(
                            id=f"duplicate_execution_{execution['id']}",
                            stage=DataFlowStage.STRATEGY_EXECUTION,
                            check_type=IntegrityCheckType.CONSISTENCY_CHECK,
                            severity="high",
                            description=f"Duplicate execution detected for strategy {execution['strategy_name']}",
                            affected_records=[str(execution['id'])],
                            detected_at=datetime.utcnow(),
                            details={
                                "execution_id": execution['id'],
                                "strategy_id": execution['strategy_id'],
                                "executed_at": execution['executed_at'].isoformat(),
                                "duplicate_count": duplicate_check
                            }
                        ))

                    # Validate signal format
                    if execution['signal']:
                        try:
                            signal_data = json.loads(execution['signal'])
                            required_fields = ['action', 'symbol', 'confidence']
                            missing_fields = [field for field in required_fields if field not in signal_data]

                            if missing_fields:
                                violations.append(IntegrityViolation(
                                    id=f"invalid_signal_{execution['id']}",
                                    stage=DataFlowStage.SIGNAL_GENERATION,
                                    check_type=IntegrityCheckType.DATA_TYPE_VALIDATION,
                                    severity="medium",
                                    description=f"Invalid signal format: missing fields {missing_fields}",
                                    affected_records=[str(execution['id'])],
                                    detected_at=datetime.utcnow(),
                                    details={
                                        "execution_id": execution['id'],
                                        "missing_fields": missing_fields,
                                        "signal_data": signal_data
                                    }
                                ))
                        except (json.JSONDecodeError, TypeError):
                            violations.append(IntegrityViolation(
                                id=f"corrupt_signal_{execution['id']}",
                                stage=DataFlowStage.SIGNAL_GENERATION,
                                check_type=IntegrityCheckType.DATA_TYPE_VALIDATION,
                                severity="high",
                                description="Corrupt signal data (invalid JSON)",
                                affected_records=[str(execution['id'])],
                                detected_at=datetime.utcnow(),
                                details={
                                    "execution_id": execution['id'],
                                    "signal_raw": execution['signal'][:200]  # First 200 chars
                                }
                            ))

                # Check strategy performance consistency
                performance_anomalies = await conn.fetch("""
                    WITH strategy_stats AS (
                        SELECT
                            strategy_id,
                            AVG(CAST(CASE WHEN performance IS NOT NULL THEN performance ELSE '0' END AS DECIMAL)) as avg_performance,
                            STDDEV(CAST(CASE WHEN performance IS NOT NULL THEN performance ELSE '0' END AS DECIMAL)) as std_performance
                        FROM strategy_executions
                        WHERE executed_at BETWEEN $1 AND $2
                        AND performance IS NOT NULL
                        GROUP BY strategy_id
                    ),
                    performance_anomalies AS (
                        SELECT
                            se.strategy_id,
                            se.executed_at,
                            se.performance,
                            ss.avg_performance,
                            ss.std_performance,
                            ABS(se.performance - ss.avg_performance) / NULLIF(ss.std_performance, 0) as z_score
                        FROM strategy_executions se
                        JOIN strategy_stats ss ON se.strategy_id = ss.strategy_id
                        WHERE se.executed_at BETWEEN $1 AND $2
                        AND se.performance IS NOT NULL
                        AND ss.std_performance > 0
                    )
                    SELECT sa.*, s.name as strategy_name
                    FROM performance_anomalies sa
                    JOIN strategies s ON sa.strategy_id = s.id
                    WHERE z_score > 3  # 3 standard deviations
                    ORDER BY z_score DESC
                    LIMIT 10
                """, start_time, end_time)

                for anomaly in performance_anomalies:
                    violations.append(IntegrityViolation(
                        id=f"performance_anomaly_{anomaly['strategy_id']}_{anomaly['executed_at'].isoformat()}",
                        stage=DataFlowStage.PERFORMANCE_CALCULATION,
                        check_type=IntegrityCheckType.RANGE_VALIDATION,
                        severity="medium",
                        description=f"Performance anomaly for {anomaly['strategy_name']}: {anomaly['z_score']:.2f} sigma",
                        affected_records=[f"{anomaly['strategy_id']}_{anomaly['executed_at'].isoformat()}"],
                        detected_at=datetime.utcnow(),
                        details={
                            "strategy_id": anomaly['strategy_id'],
                            "strategy_name": anomaly['strategy_name'],
                            "executed_at": anomaly['executed_at'].isoformat(),
                            "performance": float(anomaly['performance']),
                            "avg_performance": float(anomaly['avg_performance']),
                            "z_score": float(anomaly['z_score'])
                        }
                    ))

            execution_time = time.time() - start_validation

            result = ValidationResult(
                stage=DataFlowStage.STRATEGY_EXECUTION,
                check_type=IntegrityCheckType.CONSISTENCY_CHECK,
                passed=len(violations) == 0,
                violations=violations,
                execution_time=execution_time,
                records_checked=records_checked
            )

            # Log integrity check to database
            await self._log_integrity_check(result)

            return result

        except Exception as e:
            logger.error(f"Strategy execution integrity validation error: {str(e)}")
            return ValidationResult(
                stage=DataFlowStage.STRATEGY_EXECUTION,
                check_type=IntegrityCheckType.CONSISTENCY_CHECK,
                passed=False,
                violations=[IntegrityViolation(
                    id=f"validation_error_{int(time.time())}",
                    stage=DataFlowStage.STRATEGY_EXECUTION,
                    check_type=IntegrityCheckType.CONSISTENCY_CHECK,
                    severity="critical",
                    description=f"Validation failed: {str(e)}",
                    affected_records=[],
                    detected_at=datetime.utcnow()
                )],
                execution_time=time.time() - start_validation
            )

    async def validate_portfolio_integrity(self,
                                         portfolio_id: int = None,
                                         start_time: datetime = None,
                                         end_time: datetime = None) -> ValidationResult:
        """Validate portfolio data integrity"""
        logger.info("Validating portfolio integrity...")

        if start_time is None:
            start_time = datetime.utcnow() - timedelta(hours=24)
        if end_time is None:
            end_time = datetime.utcnow()

        start_validation = time.time()
        violations = []
        records_checked = 0

        try:
            async with self.db_pool.acquire() as conn:
                # Get portfolio snapshots
                if portfolio_id:
                    snapshots = await conn.fetch("""
                        SELECT *
                        FROM portfolio_snapshots
                        WHERE portfolio_id = $1
                        AND snapshot_time BETWEEN $2 AND $3
                        ORDER BY snapshot_time DESC
                    """, portfolio_id, start_time, end_time)
                else:
                    snapshots = await conn.fetch("""
                        SELECT *
                        FROM portfolio_snapshots
                        WHERE snapshot_time BETWEEN $1 AND $2
                        ORDER BY snapshot_time DESC
                        LIMIT 1000
                    """, start_time, end_time)

                records_checked = len(snapshots)

                for snapshot in snapshots:
                    # Check portfolio balance consistency
                    total_value = snapshot['total_value'] or 0
                    cash_balance = snapshot['cash_balance'] or 0
                    positions_value = snapshot['positions_value'] or 0

                    calculated_total = cash_balance + positions_value
                    tolerance = 0.01  # 1% tolerance

                    if abs(total_value - calculated_total) > tolerance:
                        violations.append(IntegrityViolation(
                            id=f"balance_mismatch_{snapshot['id']}",
                            stage=DataFlowStage.PORTFOLIO_UPDATE,
                            check_type=IntegrityCheckType.CONSISTENCY_CHECK,
                            severity="high",
                            description=f"Portfolio balance mismatch: reported {total_value}, calculated {calculated_total}",
                            affected_records=[str(snapshot['id'])],
                            detected_at=datetime.utcnow(),
                            details={
                                "snapshot_id": snapshot['id'],
                                "portfolio_id": snapshot['portfolio_id'],
                                "total_value": float(total_value),
                                "cash_balance": float(cash_balance),
                                "positions_value": float(positions_value),
                                "calculated_total": float(calculated_total),
                                "difference": float(abs(total_value - calculated_total))
                            }
                        ))

                    # Check for negative balances beyond threshold
                    if total_value < self.thresholds["min_portfolio_balance"]:
                        violations.append(IntegrityViolation(
                            id=f"negative_balance_{snapshot['id']}",
                            stage=DataFlowStage.PORTFOLIO_UPDATE,
                            check_type=IntegrityCheckType.RANGE_VALIDATION,
                            severity="medium",
                            description=f"Negative portfolio balance: {total_value}",
                            affected_records=[str(snapshot['id'])],
                            detected_at=datetime.utcnow(),
                            details={
                                "snapshot_id": snapshot['id'],
                                "portfolio_id": snapshot['portfolio_id'],
                                "total_value": float(total_value),
                                "threshold": self.thresholds["min_portfolio_balance"]
                            }
                        ))

                # Check position data consistency
                position_anomalies = await conn.fetch("""
                    WITH position_summary AS (
                        SELECT
                            portfolio_id,
                            symbol,
                            SUM(quantity) as total_quantity,
                            COUNT(*) as position_count
                        FROM positions
                        WHERE updated_at BETWEEN $1 AND $2
                        GROUP BY portfolio_id, symbol
                    ),
                    duplicate_positions AS (
                        SELECT ps.*
                        FROM position_summary ps
                        WHERE ps.position_count > 1
                    )
                    SELECT dp.*, p.name as portfolio_name
                    FROM duplicate_positions dp
                    JOIN portfolios p ON dp.portfolio_id = p.id
                    LIMIT 20
                """, start_time, end_time)

                for anomaly in position_anomalies:
                    violations.append(IntegrityViolation(
                        id=f"duplicate_positions_{anomaly['portfolio_id']}_{anomaly['symbol']}",
                        stage=DataFlowStage.PORTFOLIO_UPDATE,
                        check_type=IntegrityCheckType.CONSISTENCY_CHECK,
                        severity="medium",
                        description=f"Duplicate positions for {anomaly['symbol']} in portfolio {anomaly['portfolio_name']}",
                        affected_records=[f"{anomaly['portfolio_id']}_{anomaly['symbol']}"],
                        detected_at=datetime.utcnow(),
                        details={
                            "portfolio_id": anomaly['portfolio_id'],
                            "portfolio_name": anomaly['portfolio_name'],
                            "symbol": anomaly['symbol'],
                            "total_quantity": float(anomaly['total_quantity']),
                            "position_count": anomaly['position_count']
                        }
                    ))

                # Check for orphaned positions (positions without corresponding portfolio)
                orphaned_positions = await conn.fetch("""
                    SELECT COUNT(*) as orphaned_count
                    FROM positions p
                    LEFT JOIN portfolios pf ON p.portfolio_id = pf.id
                    WHERE pf.id IS NULL
                    AND p.updated_at BETWEEN $1 AND $2
                """, start_time, end_time)

                if orphaned_positions[0]['orphaned_count'] > 0:
                    violations.append(IntegrityViolation(
                        id=f"orphaned_positions_{int(time.time())}",
                        stage=DataFlowStage.PORTFOLIO_UPDATE,
                        check_type=IntegrityCheckType.REFERENTIAL_INTEGRITY,
                        severity="high",
                        description=f"Found {orphaned_positions[0]['orphaned_count']} orphaned positions",
                        affected_records=[],
                        detected_at=datetime.utcnow(),
                        details={
                            "orphaned_count": orphaned_positions[0]['orphaned_count']
                        }
                    ))

            execution_time = time.time() - start_validation

            result = ValidationResult(
                stage=DataFlowStage.PORTFOLIO_UPDATE,
                check_type=IntegrityCheckType.CONSISTENCY_CHECK,
                passed=len(violations) == 0,
                violations=violations,
                execution_time=execution_time,
                records_checked=records_checked
            )

            # Log integrity check to database
            await self._log_integrity_check(result)

            return result

        except Exception as e:
            logger.error(f"Portfolio integrity validation error: {str(e)}")
            return ValidationResult(
                stage=DataFlowStage.PORTFOLIO_UPDATE,
                check_type=IntegrityCheckType.CONSISTENCY_CHECK,
                passed=False,
                violations=[IntegrityViolation(
                    id=f"validation_error_{int(time.time())}",
                    stage=DataFlowStage.PORTFOLIO_UPDATE,
                    check_type=IntegrityCheckType.CONSISTENCY_CHECK,
                    severity="critical",
                    description=f"Validation failed: {str(e)}",
                    affected_records=[],
                    detected_at=datetime.utcnow()
                )],
                execution_time=time.time() - start_validation
            )

    async def validate_cross_system_consistency(self) -> ValidationResult:
        """Validate consistency across different system components"""
        logger.info("Validating cross-system consistency...")

        start_validation = time.time()
        violations = []
        records_checked = 0

        try:
            async with self.db_pool.acquire() as conn:
                # Check strategy vs backtest consistency
                inconsistent_strategies = await conn.fetch("""
                    SELECT
                        s.id as strategy_id,
                        s.name as strategy_name,
                        COUNT(DISTINCT bt.id) as backtest_count,
                        COUNT(DISTINCT se.id) as execution_count
                    FROM strategies s
                    LEFT JOIN backtests bt ON s.id = bt.strategy_id
                    LEFT JOIN strategy_executions se ON s.id = se.strategy_id
                    WHERE s.is_active = true
                    GROUP BY s.id, s.name
                    HAVING (COUNT(DISTINCT bt.id) = 0 AND COUNT(DISTINCT se.id) > 10)
                    OR (COUNT(DISTINCT bt.id) > 0 AND COUNT(DISTINCT se.id) = 0)
                    LIMIT 20
                """)

                for strategy in inconsistent_strategies:
                    violations.append(IntegrityViolation(
                        id=f"inconsistent_strategy_{strategy['strategy_id']}",
                        stage=DataFlowStage.DATA_VALIDATION,
                        check_type=IntegrityCheckType.CONSISTENCY_CHECK,
                        severity="medium",
                        description=f"Strategy {strategy['strategy_name']} has inconsistent backtest/execution data",
                        affected_records=[str(strategy['strategy_id'])],
                        detected_at=datetime.utcnow(),
                        details={
                            "strategy_id": strategy['strategy_id'],
                            "strategy_name": strategy['strategy_name'],
                            "backtest_count": strategy['backtest_count'],
                            "execution_count": strategy['execution_count']
                        }
                    ))

                # Check user vs portfolio consistency
                orphaned_portfolios = await conn.fetch("""
                    SELECT
                        p.id as portfolio_id,
                        p.name as portfolio_name
                    FROM portfolios p
                    LEFT JOIN users u ON p.user_id = u.id
                    WHERE u.id IS NULL
                    LIMIT 10
                """)

                for portfolio in orphaned_portfolios:
                    violations.append(IntegrityViolation(
                        id=f"orphaned_portfolio_{portfolio['portfolio_id']}",
                        stage=DataFlowStage.DATA_VALIDATION,
                        check_type=IntegrityCheckType.REFERENTIAL_INTEGRITY,
                        severity="high",
                        description=f"Portfolio {portfolio['portfolio_name']} has no associated user",
                        affected_records=[str(portfolio['portfolio_id'])],
                        detected_at=datetime.utcnow(),
                        details={
                            "portfolio_id": portfolio['portfolio_id'],
                            "portfolio_name": portfolio['portfolio_name']
                        }
                    ))

                # Check transaction consistency
                inconsistent_transactions = await conn.fetch("""
                    SELECT
                        t.id as transaction_id,
                        t.portfolio_id,
                        t.symbol,
                        t.quantity,
                        t.price,
                        p.total_value as portfolio_value_at_time
                    FROM transactions t
                    LEFT JOIN portfolio_snapshots p ON
                        t.portfolio_id = p.portfolio_id AND
                        ABS(EXTRACT(EPOCH FROM (t.executed_at - p.snapshot_time))) < 300  -- Within 5 minutes
                    WHERE p.total_value IS NULL
                    AND t.executed_at > NOW() - INTERVAL '24 hours'
                    LIMIT 50
                """)

                if inconsistent_transactions:
                    violations.append(IntegrityViolation(
                        id=f"transaction_consistency_{int(time.time())}",
                        stage=DataFlowStage.DATA_VALIDATION,
                        check_type=IntegrityCheckType.CONSISTENCY_CHECK,
                        severity="low",
                        description=f"Found {len(inconsistent_transactions)} transactions without corresponding portfolio snapshots",
                        affected_records=[str(t['transaction_id']) for t in inconsistent_transactions],
                        detected_at=datetime.utcnow(),
                        details={
                            "transaction_count": len(inconsistent_transactions),
                            "sample_transactions": [
                                {
                                    "transaction_id": t['transaction_id'],
                                    "portfolio_id": t['portfolio_id'],
                                    "symbol": t['symbol'],
                                    "executed_at": t['executed_at'].isoformat()
                                }
                                for t in inconsistent_transactions[:5]
                            ]
                        }
                    ))

                records_checked = (
                    len(inconsistent_strategies) +
                    len(orphaned_portfolios) +
                    len(inconsistent_transactions)
                )

            execution_time = time.time() - start_validation

            result = ValidationResult(
                stage=DataFlowStage.DATA_VALIDATION,
                check_type=IntegrityCheckType.CONSISTENCY_CHECK,
                passed=len(violations) == 0,
                violations=violations,
                execution_time=execution_time,
                records_checked=records_checked
            )

            # Log integrity check to database
            await self._log_integrity_check(result)

            return result

        except Exception as e:
            logger.error(f"Cross-system consistency validation error: {str(e)}")
            return ValidationResult(
                stage=DataFlowStage.DATA_VALIDATION,
                check_type=IntegrityCheckType.CONSISTENCY_CHECK,
                passed=False,
                violations=[IntegrityViolation(
                    id=f"validation_error_{int(time.time())}",
                    stage=DataFlowStage.DATA_VALIDATION,
                    check_type=IntegrityCheckType.CONSISTENCY_CHECK,
                    severity="critical",
                    description=f"Validation failed: {str(e)}",
                    affected_records=[],
                    detected_at=datetime.utcnow()
                )],
                execution_time=time.time() - start_validation
            )

    async def _log_integrity_check(self, result: ValidationResult):
        """Log integrity check results to database"""
        try:
            async with self.db_pool.acquire() as conn:
                # Log integrity check
                check_id = await conn.fetchval("""
                    INSERT INTO integrity_checks (
                        stage, check_type, status, violations_count,
                        records_checked, execution_time, details
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                    RETURNING id
                """,
                    result.stage.value,
                    result.check_type.value,
                    "passed" if result.passed else "failed",
                    len(result.violations),
                    result.records_checked,
                    result.execution_time,
                    {
                        "check_timestamp": datetime.utcnow().isoformat(),
                        "violation_summary": [
                            {
                                "severity": v.severity,
                                "type": v.check_type.value,
                                "description": v.description
                            }
                            for v in result.violations[:10]  # Limit summary
                        ]
                    }
                )

                # Log individual violations
                for violation in result.violations:
                    await conn.execute("""
                        INSERT INTO integrity_violations (
                            violation_id, stage, check_type, severity,
                            description, affected_records, details
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                        ON CONFLICT (violation_id) DO NOTHING
                    """,
                        violation.id,
                        violation.stage.value,
                        violation.check_type.value,
                        violation.severity,
                        violation.description,
                        violation.affected_records,
                        {
                            "detected_at": violation.detected_at.isoformat(),
                            "check_id": check_id,
                            **violation.details
                        }
                    )

            # Log to InfluxDB for monitoring
            if self.influx_client:
                write_api = self.influx_client.write_api(write_options=SYNCHRONOUS)

                point = Point("integrity_check") \
                    .tag("stage", result.stage.value) \
                    .tag("check_type", result.check_type.value) \
                    .tag("status", "passed" if result.passed else "failed") \
                    .field("violations_count", len(result.violations)) \
                    .field("records_checked", result.records_checked) \
                    .field("execution_time", result.execution_time) \
                    .time(datetime.utcnow())

                write_api.write(bucket=self.influx_config["bucket"], record=point)

            # Cache result in Redis for quick access
            if self.redis_client:
                cache_key = f"integrity_check:{result.stage.value}:{result.check_type.value}"
                await self.redis_client.setex(
                    cache_key,
                    3600,  # 1 hour cache
                    json.dumps({
                        "status": "passed" if result.passed else "failed",
                        "violations_count": len(result.violations),
                        "execution_time": result.execution_time,
                        "checked_at": datetime.utcnow().isoformat()
                    })
                )

        except Exception as e:
            logger.error(f"Failed to log integrity check: {str(e)}")

    async def run_comprehensive_integrity_validation(self) -> Dict[str, Any]:
        """Run comprehensive integrity validation across all stages"""
        logger.info("Starting comprehensive data flow integrity validation...")

        await self.setup()

        try:
            # Run all validation checks
            validation_tasks = [
                self.validate_market_data_integrity(),
                self.validate_strategy_execution_integrity(),
                self.validate_portfolio_integrity(),
                self.validate_cross_system_consistency()
            ]

            results = await asyncio.gather(*validation_tasks, return_exceptions=True)

            # Process results
            validation_results = {}
            total_violations = 0
            total_records_checked = 0
            critical_violations = []

            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Validation check {i} failed: {str(result)}")
                    continue

                stage_name = result.stage.value
                validation_results[stage_name] = {
                    "passed": result.passed,
                    "violations_count": len(result.violations),
                    "execution_time": result.execution_time,
                    "records_checked": result.records_checked,
                    "violations": [
                        {
                            "id": v.id,
                            "severity": v.severity,
                            "description": v.description,
                            "affected_records": v.affected_records
                        }
                        for v in result.violations
                    ]
                }

                total_violations += len(result.violations)
                total_records_checked += result.records_checked

                # Track critical violations
                critical_violations.extend([
                    v for v in result.violations
                    if v.severity == "critical"
                ])

            # Generate integrity report
            report = {
                "validation_summary": {
                    "total_checks": len(validation_results),
                    "passed_checks": sum(1 for r in validation_results.values() if r["passed"]),
                    "failed_checks": sum(1 for r in validation_results.values() if not r["passed"]),
                    "total_violations": total_violations,
                    "critical_violations": len(critical_violations),
                    "total_records_checked": total_records_checked,
                    "overall_integrity_score": max(0, 100 - (total_violations / max(total_records_checked, 1) * 100))
                },
                "stage_results": validation_results,
                "critical_violations": [
                    {
                        "id": v.id,
                        "stage": v.stage.value,
                        "description": v.description,
                        "affected_records": v.affected_records,
                        "detected_at": v.detected_at.isoformat()
                    }
                    for v in critical_violations
                ],
                "recommendations": self._generate_integrity_recommendations(validation_results),
                "validation_timestamp": datetime.utcnow().isoformat()
            }

            logger.info(f"Integrity validation complete: {total_violations} violations found")
            return report

        finally:
            await self.cleanup()

    def _generate_integrity_recommendations(self, validation_results: Dict) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []

        # Analyze violation patterns
        violation_counts = {
            stage: result["violations_count"]
            for stage, result in validation_results.items()
        }

        # Find stages with most violations
        if violation_counts:
            max_violations_stage = max(violation_counts, key=violation_counts.get)
            max_violations_count = violation_counts[max_violations_stage]

            if max_violations_count > 10:
                recommendations.append(f"Priority attention needed for {max_violations_stage}: {max_violations_count} violations found")

        # Check for critical issues
        critical_issues = sum(
            len([v for v in result["violations"] if v["severity"] == "critical"])
            for result in validation_results.values()
        )

        if critical_issues > 0:
            recommendations.append(f"URGENT: {critical_issues} critical violations require immediate attention")

        # Data quality recommendations
        total_violations = sum(result["violations_count"] for result in validation_results.values())
        total_records = sum(result["records_checked"] for result in validation_results.values())

        if total_records > 0:
            violation_rate = total_violations / total_records
            if violation_rate > 0.05:  # 5%
                recommendations.append("High data quality issues detected - implement automated data validation pipelines")
            elif violation_rate > 0.01:  # 1%
                recommendations.append("Consider implementing additional data quality checks")

        # Performance recommendations
        execution_times = [
            result["execution_time"]
            for result in validation_results.values()
        ]

        if execution_times:
            avg_execution_time = sum(execution_times) / len(execution_times)
            if avg_execution_time > 10.0:  # 10 seconds
                recommendations.append("Optimize integrity validation performance - average execution time too high")

        # Stage-specific recommendations
        stage_recommendations = {
            "market_data_ingestion": [
                "Implement real-time data validation",
                "Set up automated anomaly detection",
                "Review data source configurations"
            ],
            "strategy_execution": [
                "Add execution result validation",
                "Implement signal format standardization",
                "Review strategy logic consistency"
            ],
            "portfolio_update": [
                "Implement portfolio balance validation",
                "Add position reconciliation checks",
                "Review portfolio update frequency"
            ],
            "data_validation": [
                "Add cross-system data consistency checks",
                "Implement referential integrity validation",
                "Review data migration procedures"
            ]
        }

        for stage, result in validation_results.items():
            if not result["passed"] and stage in stage_recommendations:
                recommendations.extend(stage_recommendations[stage])

        if not recommendations:
            recommendations.append("Data integrity is within acceptable thresholds")

        return recommendations


# Async context manager for easy usage
class IntegrityValidatorContext:
    """Context manager for integrity validator"""

    def __init__(self):
        self.validator = None

    async def __aenter__(self):
        self.validator = DataFlowIntegrityValidator()
        await self.validator.setup()
        return self.validator

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.validator:
            await self.validator.cleanup()


if __name__ == "__main__":
    # Run comprehensive validation
    async def main():
        async with IntegrityValidatorContext() as validator:
            report = await validator.run_comprehensive_integrity_validation()

            print("\n" + "="*60)
            print("DATA FLOW INTEGRITY VALIDATION REPORT")
            print("="*60)

            summary = report["validation_summary"]
            print(f"Total Checks: {summary['total_checks']}")
            print(f"Passed: {summary['passed_checks']}")
            print(f"Failed: {summary['failed_checks']}")
            print(f"Total Violations: {summary['total_violations']}")
            print(f"Critical Violations: {summary['critical_violations']}")
            print(f"Records Checked: {summary['total_records_checked']}")
            print(f"Integrity Score: {summary['overall_integrity_score']:.1f}%")

            print(f"\nStage Results:")
            for stage, result in report["stage_results"].items():
                status = "✓" if result["passed"] else "✗"
                print(f"  {status} {stage}: {result['violations_count']} violations ({result['execution_time']:.2f}s)")

            if report["critical_violations"]:
                print(f"\nCRITICAL VIOLATIONS:")
                for violation in report["critical_violations"]:
                    print(f"  - {violation['stage']}: {violation['description']}")

            print(f"\nRecommendations:")
            for rec in report["recommendations"]:
                print(f"  - {rec}")

            print("="*60)

    asyncio.run(main())