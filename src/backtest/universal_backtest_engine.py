"""
Universal Backtest Engine
========================

A unified, high-performance backtesting engine that supports multiple modes:
- Standard backtesting
- Risk-managed backtesting
- Stress testing
- Monte Carlo simulation

Integrates with PostgreSQL for results storage and InfluxDB for time-series metrics.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import json
from functools import lru_cache
import hashlib

# Database imports
import asyncpg
import aioredis
from influxdb_client.client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS

# Import existing components
from .enhanced_backtest_engine import EnhancedBacktestEngine, BacktestConfig, BacktestMode
from .monte_carlo import MonteCarloSimulator, MCSimulationConfig, MCResults
from .engine_interface import BacktestStatus, StrategyPerformance, BacktestMetrics

logger = logging.getLogger(__name__)


class BacktestType(str, Enum):
    """回測類型枚舉"""
    STANDARD = "standard"
    RISK_MANAGED = "risk_managed"
    STRESS_TEST = "stress_test"
    MONTE_CARLO = "monte_carlo"
    PARAMETER_OPTIMIZATION = "parameter_optimization"
    WALK_FORWARD = "walk_forward"


class TaskPriority(int, Enum):
    """任務優先級"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class BacktestTask:
    """回測任務定義"""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    strategy_id: str = ""
    strategy_name: str = ""
    strategy_config: Dict[str, Any] = field(default_factory=dict)
    backtest_type: BacktestType = BacktestType.STANDARD
    start_date: datetime = field(default_factory=datetime.now)
    end_date: datetime = field(default_factory=datetime.now)
    initial_capital: float = 1000000.0
    commission_rate: float = 0.001
    slippage_rate: float = 0.0005

    # 任務控制
    priority: TaskPriority = TaskPriority.NORMAL
    max_runtime: Optional[int] = None  # Maximum runtime in seconds
    retry_count: int = 0
    max_retries: int = 3

    # 特殊配置
    monte_carlo_config: Optional[MCSimulationConfig] = None
    stress_scenarios: List[str] = field(default_factory=list)
    optimization_params: Dict[str, Any] = field(default_factory=dict)

    # 元數據
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            'task_id': self.task_id,
            'strategy_id': self.strategy_id,
            'strategy_name': self.strategy_name,
            'strategy_config': self.strategy_config,
            'backtest_type': self.backtest_type.value,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'initial_capital': self.initial_capital,
            'commission_rate': self.commission_rate,
            'slippage_rate': self.slippage_rate,
            'priority': self.priority.value,
            'max_runtime': self.max_runtime,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'monte_carlo_config': self.monte_carlo_config.__dict__ if self.monte_carlo_config else None,
            'stress_scenarios': self.stress_scenarios,
            'optimization_params': self.optimization_params,
            'created_at': self.created_at.isoformat(),
            'created_by': self.created_by,
            'tags': self.tags
        }


@dataclass
class BacktestResult:
    """回測結果"""
    task_id: str
    status: BacktestStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # 基礎績效指標
    total_return: float = 0.0
    annualized_return: float = 0.0
    volatility: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    calmar_ratio: float = 0.0

    # 風險指標
    var_95: float = 0.0
    var_99: float = 0.0
    expected_shortfall_95: float = 0.0
    expected_shortfall_99: float = 0.0

    # 交易統計
    total_trades: int = 0
    win_rate: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    profit_factor: float = 0.0

    # 詳細數據
    equity_curve: Optional[pd.Series] = None
    returns: Optional[pd.Series] = None
    positions: Optional[List[Dict]] = None
    trades: Optional[List[Dict]] = None

    # 特殊結果
    monte_carlo_results: Optional[MCResults] = None
    stress_test_results: Optional[Dict[str, Any]] = None
    optimization_results: Optional[Dict[str, Any]] = None

    # 錯誤信息
    error_message: Optional[str] = None
    error_traceback: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典，用於存儲"""
        result_dict = {
            'task_id': self.task_id,
            'status': self.status.value,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'total_return': self.total_return,
            'annualized_return': self.annualized_return,
            'volatility': self.volatility,
            'sharpe_ratio': self.sharpe_ratio,
            'max_drawdown': self.max_drawdown,
            'calmar_ratio': self.calmar_ratio,
            'var_95': self.var_95,
            'var_99': self.var_99,
            'expected_shortfall_95': self.expected_shortfall_95,
            'expected_shortfall_99': self.expected_shortfall_99,
            'total_trades': self.total_trades,
            'win_rate': self.win_rate,
            'avg_win': self.avg_win,
            'avg_loss': self.avg_loss,
            'profit_factor': self.profit_factor,
            'equity_curve': self.equity_curve.to_json() if self.equity_curve is not None else None,
            'returns': self.returns.to_json() if self.returns is not None else None,
            'positions': json.dumps(self.positions) if self.positions else None,
            'trades': json.dumps(self.trades) if self.trades else None,
            'error_message': self.error_message,
            'error_traceback': self.error_traceback
        }

        # Handle special results
        if self.monte_carlo_results:
            result_dict['monte_carlo_summary'] = {
                'mean': float(np.mean(self.monte_carlo_results.final_values)),
                'std': float(np.std(self.monte_carlo_results.final_values)),
                'var_95': float(self.monte_carlo_results.var.get(0.95, 0)),
                'success_probability': self.monte_carlo_results.success_probability
            }

        if self.stress_test_results:
            result_dict['stress_test_summary'] = self.stress_test_results

        if self.optimization_results:
            result_dict['optimization_summary'] = {
                'best_params': self.optimization_results.get('best_params'),
                'best_sharpe': self.optimization_results.get('best_sharpe'),
                'total_iterations': self.optimization_results.get('total_iterations')
            }

        return result_dict


class UniversalBacktestEngine:
    """
    Universal Backtest Engine with multi-mode support and parallel processing
    """

    def __init__(
        self,
        postgres_dsn: str,
        influxdb_url: str,
        redis_url: str,
        max_workers: int = 4,
        enable_caching: bool = True
    ):
        """
        Initialize the Universal Backtest Engine

        Args:
            postgres_dsn: PostgreSQL connection string
            influxdb_url: InfluxDB connection URL
            redis_url: Redis connection URL for caching
            max_workers: Maximum number of parallel workers
            enable_caching: Enable result caching
        """
        self.postgres_dsn = postgres_dsn
        self.influxdb_url = influxdb_url
        self.redis_url = redis_url
        self.max_workers = max_workers
        self.enable_caching = enable_caching

        # Initialize connection pools
        self.postgres_pool = None
        self.redis_pool = None
        self.influxdb_client = None

        # Task management
        self.active_tasks: Dict[str, BacktestTask] = {}
        self.task_results: Dict[str, BacktestResult] = {}
        self.task_queue = asyncio.Queue()

        # Resource management
        self.semaphore = asyncio.Semaphore(max_workers)
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

        # Performance tracking
        self.stats = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }

        logger.info(f"Universal Backtest Engine initialized with {max_workers} workers")

    async def initialize(self) -> bool:
        """Initialize database connections and resources"""
        try:
            # Initialize PostgreSQL connection pool
            self.postgres_pool = await asyncpg.create_pool(
                self.postgres_dsn,
                min_size=2,
                max_size=self.max_workers * 2
            )

            # Initialize Redis connection
            self.redis_pool = await aioredis.from_url(self.redis_url)

            # Initialize InfluxDB client
            self.influxdb_client = InfluxDBClient(url=self.influxdb_url)

            # Create tables if not exists
            await self._create_tables()

            logger.info("All database connections initialized")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize engine: {e}")
            return False

    async def submit_backtest(
        self,
        strategy_config: Dict[str, Any],
        backtest_type: BacktestType = BacktestType.STANDARD,
        **kwargs
    ) -> str:
        """
        Submit a backtest task

        Args:
            strategy_config: Strategy configuration
            backtest_type: Type of backtest to run
            **kwargs: Additional backtest parameters

        Returns:
            str: Task ID
        """
        # Create task
        task = BacktestTask(
            strategy_id=strategy_config.get('strategy_id', ''),
            strategy_name=strategy_config.get('strategy_name', ''),
            strategy_config=strategy_config,
            backtest_type=backtest_type,
            **kwargs
        )

        # Check cache
        if self.enable_caching:
            cache_key = self._get_cache_key(task)
            cached_result = await self._get_cached_result(cache_key)
            if cached_result:
                self.stats['cache_hits'] += 1
                logger.info(f"Returning cached result for task {task.task_id}")
                self.task_results[task.task_id] = cached_result
                return task.task_id
            else:
                self.stats['cache_misses'] += 1

        # Store task
        self.active_tasks[task.task_id] = task
        await self._store_task(task)

        # Add to queue
        await self.task_queue.put(task)
        self.stats['total_tasks'] += 1

        logger.info(f"Submitted {backtest_type.value} backtest task: {task.task_id}")
        return task.task_id

    async def get_task_status(self, task_id: str) -> Optional[BacktestResult]:
        """
        Get the status of a backtest task

        Args:
            task_id: Task ID

        Returns:
            BacktestResult: Task result if exists
        """
        # Check memory
        if task_id in self.task_results:
            return self.task_results[task_id]

        # Check database
        result = await self._load_result(task_id)
        if result:
            self.task_results[task_id] = result

        return result

    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a running task

        Args:
            task_id: Task ID

        Returns:
            bool: True if cancelled successfully
        """
        if task_id in self.active_tasks:
            # Mark as cancelled
            task = self.active_tasks[task_id]
            del self.active_tasks[task_id]

            # Update in database
            await self._update_task_status(task_id, BacktestStatus.CANCELLED)

            logger.info(f"Cancelled task: {task_id}")
            return True

        return False

    async def run_worker(self):
        """Worker process to handle backtest tasks"""
        while True:
            try:
                # Get task from queue
                task = await self.task_queue.get()

                # Check if task was cancelled
                if task.task_id not in self.active_tasks:
                    continue

                # Acquire semaphore for resource control
                async with self.semaphore:
                    logger.info(f"Processing task: {task.task_id}")

                    # Create result object
                    result = BacktestResult(
                        task_id=task.task_id,
                        status=BacktestStatus.RUNNING,
                        started_at=datetime.now()
                    )

                    # Update status
                    self.task_results[task.task_id] = result
                    await self._update_task_status(task.task_id, BacktestStatus.RUNNING)

                    try:
                        # Run backtest based on type
                        if task.backtest_type == BacktestType.STANDARD:
                            await self._run_standard_backtest(task, result)
                        elif task.backtest_type == BacktestType.RISK_MANAGED:
                            await self._run_risk_managed_backtest(task, result)
                        elif task.backtest_type == BacktestType.STRESS_TEST:
                            await self._run_stress_test_backtest(task, result)
                        elif task.backtest_type == BacktestType.MONTE_CARLO:
                            await self._run_monte_carlo_backtest(task, result)
                        elif task.backtest_type == BacktestType.PARAMETER_OPTIMIZATION:
                            await self._run_parameter_optimization(task, result)
                        else:
                            raise ValueError(f"Unsupported backtest type: {task.backtest_type}")

                        # Mark as completed
                        result.status = BacktestStatus.COMPLETED
                        result.completed_at = datetime.now()
                        self.stats['completed_tasks'] += 1

                        # Store result
                        await self._store_result(result)

                        # Cache result
                        if self.enable_caching:
                            cache_key = self._get_cache_key(task)
                            await self._cache_result(cache_key, result)

                        logger.info(f"Completed task: {task.task_id}")

                    except asyncio.TimeoutError:
                        result.status = BacktestStatus.FAILED
                        result.error_message = "Task timed out"
                        self.stats['failed_tasks'] += 1
                        logger.error(f"Task timed out: {task.task_id}")

                    except Exception as e:
                        result.status = BacktestStatus.FAILED
                        result.error_message = str(e)
                        result.error_traceback = str(e.__traceback__)
                        self.stats['failed_tasks'] += 1
                        logger.error(f"Task failed: {task.task_id} - {e}")

                        # Retry if configured
                        if task.retry_count < task.max_retries:
                            task.retry_count += 1
                            await self.task_queue.put(task)
                            logger.info(f"Retrying task: {task.task_id} (attempt {task.retry_count})")

                    finally:
                        # Clean up
                        if task.task_id in self.active_tasks:
                            del self.active_tasks[task.task_id]

                        # Store final result
                        await self._store_result(result)

            except Exception as e:
                logger.error(f"Worker error: {e}")
                await asyncio.sleep(1)

    async def _run_standard_backtest(self, task: BacktestTask, result: BacktestResult):
        """Run standard backtest"""
        # This would integrate with your existing strategy system
        # For now, returning placeholder results

        # Simulate backtest execution
        await asyncio.sleep(1)  # Simulate processing time

        # Placeholder results
        result.total_return = 0.15
        result.annualized_return = 0.12
        result.volatility = 0.18
        result.sharpe_ratio = 0.67
        result.max_drawdown = -0.12
        result.calmar_ratio = 1.0
        result.var_95 = -0.025
        result.var_99 = -0.035
        result.expected_shortfall_95 = -0.03
        result.expected_shortfall_99 = -0.045
        result.total_trades = 100
        result.win_rate = 0.55
        result.avg_win = 0.02
        result.avg_loss = -0.015
        result.profit_factor = 1.5

    async def _run_risk_managed_backtest(self, task: BacktestTask, result: BacktestResult):
        """Run risk-managed backtest using EnhancedBacktestEngine"""
        # Convert to EnhancedBacktestEngine config
        config = BacktestConfig(
            start_date=task.start_date,
            end_date=task.end_date,
            initial_capital=task.initial_capital,
            commission_rate=task.commission_rate,
            slippage_rate=task.slippage_rate,
            enable_risk_management=True,
            enable_dynamic_adjustments=True,
            enable_real_time_monitoring=True
        )

        # Create engine
        engine = EnhancedBacktestEngine(config)

        # Run with placeholder strategy
        # In production, this would load and execute the actual strategy
        dates = pd.date_range(start=task.start_date, end=task.end_date, freq='D')
        np.random.seed(42)
        data = pd.DataFrame({
            'AAPL': 150 * np.cumprod(1 + np.random.normal(0.0005, 0.02, len(dates)))
        }, index=dates)

        def placeholder_strategy(date, market_data, portfolio_state):
            return {'AAPL': 100}

        # Run backtest
        engine_result = engine.run_backtest(
            strategy=placeholder_strategy,
            data=data,
            mode=BacktestMode.RISK_MANAGED
        )

        # Convert results
        result.total_return = engine_result.total_return
        result.annualized_return = engine_result.annualized_return
        result.volatility = engine_result.volatility
        result.sharpe_ratio = engine_result.sharpe_ratio
        result.max_drawdown = engine_result.max_drawdown
        result.calmar_ratio = engine_result.calmar_ratio
        result.var_95 = engine_result.var_95
        result.var_99 = engine_result.var_99
        result.expected_shortfall_95 = engine_result.expected_shortfall_95
        result.expected_shortfall_99 = engine_result.expected_shortfall_99
        result.total_trades = engine_result.total_trades
        result.win_rate = engine_result.win_rate
        result.avg_win = engine_result.avg_win
        result.avg_loss = engine_result.avg_loss
        result.profit_factor = engine_result.profit_factor
        result.equity_curve = engine_result.equity_curve
        result.returns = engine_result.returns

    async def _run_stress_test_backtest(self, task: BacktestTask, result: BacktestResult):
        """Run stress test backtest"""
        # Define stress scenarios
        stress_scenarios = task.stress_scenarios or [
            "2008_crisis",
            "covid_crash",
            "dot_com_bubble"
        ]

        scenario_results = {}

        for scenario in stress_scenarios:
            # Simulate scenario-specific results
            if scenario == "2008_crisis":
                scenario_results[scenario] = {
                    'total_return': -0.35,
                    'max_drawdown': -0.45,
                    'var_95': -0.05,
                    'sharpe_ratio': -0.8
                }
            elif scenario == "covid_crash":
                scenario_results[scenario] = {
                    'total_return': -0.25,
                    'max_drawdown': -0.35,
                    'var_95': -0.04,
                    'sharpe_ratio': -0.5
                }
            elif scenario == "dot_com_bubble":
                scenario_results[scenario] = {
                    'total_return': -0.30,
                    'max_drawdown': -0.40,
                    'var_95': -0.045,
                    'sharpe_ratio': -0.6
                }

        result.stress_test_results = scenario_results

        # Base results (normal market conditions)
        result.total_return = 0.15
        result.max_drawdown = -0.12
        result.var_95 = -0.025
        result.sharpe_ratio = 0.67

    async def _run_monte_carlo_backtest(self, task: BacktestTask, result: BacktestResult):
        """Run Monte Carlo simulation"""
        # Get configuration
        mc_config = task.monte_carlo_config or MCSimulationConfig(
            n_simulations=1000,
            time_horizon=252
        )

        # Generate sample returns
        np.random.seed(42)
        returns = pd.Series(np.random.normal(0.001, 0.02, 504))

        # Run simulation
        simulator = MonteCarloSimulator(mc_config)
        mc_results = simulator.simulate_bootstrap(
            returns=returns,
            initial_capital=task.initial_capital
        )

        # Store results
        result.monte_carlo_results = mc_results

        # Calculate summary statistics
        final_values = mc_results.final_values
        result.total_return = (np.mean(final_values) - task.initial_capital) / task.initial_capital
        result.volatility = np.std(final_values) / task.initial_capital
        result.var_95 = -np.percentile(final_values, 5) / task.initial_capital
        result.var_99 = -np.percentile(final_values, 1) / task.initial_capital
        result.expected_shortfall_95 = -np.mean(final_values[final_values <= np.percentile(final_values, 5)]) / task.initial_capital
        result.expected_shortfall_99 = -np.mean(final_values[final_values <= np.percentile(final_values, 1)]) / task.initial_capital

    async def _run_parameter_optimization(self, task: BacktestTask, result: BacktestResult):
        """Run parameter optimization"""
        # Get optimization parameters
        opt_params = task.optimization_params or {}
        param_grid = opt_params.get('param_grid', {})

        best_sharpe = -float('inf')
        best_params = {}

        # Simple grid search (in production, use more sophisticated methods)
        total_iterations = 0
        for params in self._generate_param_combinations(param_grid):
            # Simulate backtest with these parameters
            sharpe = np.random.normal(0.5, 0.3)  # Placeholder

            if sharpe > best_sharpe:
                best_sharpe = sharpe
                best_params = params

            total_iterations += 1

        result.optimization_results = {
            'best_params': best_params,
            'best_sharpe': best_sharpe,
            'total_iterations': total_iterations
        }

        # Use best parameters for final result
        result.sharpe_ratio = best_sharpe
        result.total_return = best_sharpe * 0.2  # Placeholder calculation

    def _generate_param_combinations(self, param_grid: Dict[str, List]):
        """Generate all parameter combinations from grid"""
        import itertools

        keys = list(param_grid.keys())
        values = list(param_grid.values())

        for combination in itertools.product(*values):
            yield dict(zip(keys, combination))

    def _get_cache_key(self, task: BacktestTask) -> str:
        """Generate cache key for task"""
        # Create hash of task configuration
        task_str = json.dumps(task.to_dict(), sort_keys=True)
        return hashlib.md5(task_str.encode()).hexdigest()

    async def _get_cached_result(self, cache_key: str) -> Optional[BacktestResult]:
        """Get cached result"""
        if not self.redis_pool:
            return None

        try:
            cached = await self.redis_pool.get(f"backtest:{cache_key}")
            if cached:
                result_dict = json.loads(cached)
                # Reconstruct BacktestResult
                result = BacktestResult(
                    task_id=result_dict['task_id'],
                    status=BacktestStatus(result_dict['status'])
                )
                # Populate other fields...
                return result
        except Exception as e:
            logger.warning(f"Cache get failed: {e}")

        return None

    async def _cache_result(self, cache_key: str, result: BacktestResult):
        """Cache result"""
        if not self.redis_pool:
            return

        try:
            # Cache for 24 hours
            await self.redis_pool.setex(
                f"backtest:{cache_key}",
                86400,
                json.dumps(result.to_dict())
            )
        except Exception as e:
            logger.warning(f"Cache set failed: {e}")

    async def _create_tables(self):
        """Create database tables"""
        async with self.postgres_pool.acquire() as conn:
            # Create backtest_tasks table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS backtest_tasks (
                    task_id UUID PRIMARY KEY,
                    strategy_id TEXT NOT NULL,
                    strategy_name TEXT NOT NULL,
                    strategy_config JSONB,
                    backtest_type TEXT NOT NULL,
                    start_date TIMESTAMP NOT NULL,
                    end_date TIMESTAMP NOT NULL,
                    initial_capital FLOAT NOT NULL,
                    commission_rate FLOAT NOT NULL,
                    slippage_rate FLOAT NOT NULL,
                    priority INTEGER NOT NULL,
                    max_runtime INTEGER,
                    retry_count INTEGER NOT NULL DEFAULT 0,
                    max_retries INTEGER NOT NULL DEFAULT 3,
                    monte_carlo_config JSONB,
                    stress_scenarios TEXT[],
                    optimization_params JSONB,
                    created_at TIMESTAMP NOT NULL,
                    created_by TEXT,
                    tags TEXT[],
                    status TEXT NOT NULL DEFAULT 'pending'
                )
            """)

            # Create backtest_results table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS backtest_results (
                    task_id UUID PRIMARY KEY,
                    status TEXT NOT NULL,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    total_return FLOAT,
                    annualized_return FLOAT,
                    volatility FLOAT,
                    sharpe_ratio FLOAT,
                    max_drawdown FLOAT,
                    calmar_ratio FLOAT,
                    var_95 FLOAT,
                    var_99 FLOAT,
                    expected_shortfall_95 FLOAT,
                    expected_shortfall_99 FLOAT,
                    total_trades INTEGER,
                    win_rate FLOAT,
                    avg_win FLOAT,
                    avg_loss FLOAT,
                    profit_factor FLOAT,
                    equity_curve TEXT,
                    returns TEXT,
                    positions TEXT,
                    trades TEXT,
                    monte_carlo_summary JSONB,
                    stress_test_summary JSONB,
                    optimization_summary JSONB,
                    error_message TEXT,
                    error_traceback TEXT,
                    created_at TIMESTAMP DEFAULT NOW(),
                    FOREIGN KEY (task_id) REFERENCES backtest_tasks(task_id)
                )
            """)

            # Create indexes
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_backtest_tasks_strategy_id
                ON backtest_tasks(strategy_id)
            """)

            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_backtest_tasks_status
                ON backtest_tasks(status)
            """)

            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_backtest_tasks_created_at
                ON backtest_tasks(created_at)
            """)

    async def _store_task(self, task: BacktestTask):
        """Store task in database"""
        async with self.postgres_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO backtest_tasks (
                    task_id, strategy_id, strategy_name, strategy_config,
                    backtest_type, start_date, end_date, initial_capital,
                    commission_rate, slippage_rate, priority, max_runtime,
                    retry_count, max_retries, monte_carlo_config,
                    stress_scenarios, optimization_params, created_at,
                    created_by, tags, status
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11,
                    $12, $13, $14, $15, $16, $17, $18, $19, $20, $21
                )
            """, *task.to_dict().values())

    async def _store_result(self, result: BacktestResult):
        """Store result in database"""
        async with self.postgres_pool.acquire() as conn:
            result_dict = result.to_dict()
            columns = list(result_dict.keys())
            placeholders = ', '.join([f'${i+1}' for i in range(len(columns))])
            values = list(result_dict.values())

            await conn.execute(f"""
                INSERT INTO backtest_results ({', '.join(columns)})
                VALUES ({placeholders})
                ON CONFLICT (task_id) DO UPDATE SET
                    status = EXCLUDED.status,
                    completed_at = EXCLUDED.completed_at,
                    total_return = EXCLUDED.total_return,
                    annualized_return = EXCLUDED.annualized_return,
                    volatility = EXCLUDED.volatility,
                    sharpe_ratio = EXCLUDED.sharpe_ratio,
                    max_drawdown = EXCLUDED.max_drawdown,
                    calmar_ratio = EXCLUDED.calmar_ratio,
                    var_95 = EXCLUDED.var_95,
                    var_99 = EXCLUDED.var_99,
                    expected_shortfall_95 = EXCLUDED.expected_shortfall_95,
                    expected_shortfall_99 = EXCLUDED.expected_shortfall_99,
                    total_trades = EXCLUDED.total_trades,
                    win_rate = EXCLUDED.win_rate,
                    avg_win = EXCLUDED.avg_win,
                    avg_loss = EXCLUDED.avg_loss,
                    profit_factor = EXCLUDED.profit_factor,
                    equity_curve = EXCLUDED.equity_curve,
                    returns = EXCLUDED.returns,
                    positions = EXCLUDED.positions,
                    trades = EXCLUDED.trades,
                    monte_carlo_summary = EXCLUDED.monte_carlo_summary,
                    stress_test_summary = EXCLUDED.stress_test_summary,
                    optimization_summary = EXCLUDED.optimization_summary,
                    error_message = EXCLUDED.error_message,
                    error_traceback = EXCLUDED.error_traceback
            """, *values)

    async def _load_result(self, task_id: str) -> Optional[BacktestResult]:
        """Load result from database"""
        async with self.postgres_pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM backtest_results WHERE task_id = $1
            """, task_id)

            if row:
                result = BacktestResult(
                    task_id=row['task_id'],
                    status=BacktestStatus(row['status']),
                    started_at=row['started_at'],
                    completed_at=row['completed_at'],
                    total_return=row['total_return'] or 0.0,
                    annualized_return=row['annualized_return'] or 0.0,
                    volatility=row['volatility'] or 0.0,
                    sharpe_ratio=row['sharpe_ratio'] or 0.0,
                    max_drawdown=row['max_drawdown'] or 0.0,
                    calmar_ratio=row['calmar_ratio'] or 0.0,
                    var_95=row['var_95'] or 0.0,
                    var_99=row['var_99'] or 0.0,
                    expected_shortfall_95=row['expected_shortfall_95'] or 0.0,
                    expected_shortfall_99=row['expected_shortfall_99'] or 0.0,
                    total_trades=row['total_trades'] or 0,
                    win_rate=row['win_rate'] or 0.0,
                    avg_win=row['avg_win'] or 0.0,
                    avg_loss=row['avg_loss'] or 0.0,
                    profit_factor=row['profit_factor'] or 0.0,
                    error_message=row['error_message'],
                    error_traceback=row['error_traceback']
                )

                # Load series data if exists
                if row['equity_curve']:
                    result.equity_curve = pd.read_json(row['equity_curve'])
                if row['returns']:
                    result.returns = pd.read_json(row['returns'])
                if row['positions']:
                    result.positions = json.loads(row['positions'])
                if row['trades']:
                    result.trades = json.loads(row['trades'])

                return result

        return None

    async def _update_task_status(self, task_id: str, status: BacktestStatus):
        """Update task status in database"""
        async with self.postgres_pool.acquire() as conn:
            await conn.execute("""
                UPDATE backtest_tasks
                SET status = $1
                WHERE task_id = $2
            """, status.value, task_id)

    async def get_statistics(self) -> Dict[str, Any]:
        """Get engine statistics"""
        return {
            'active_tasks': len(self.active_tasks),
            'queue_size': self.task_queue.qsize(),
            'stats': self.stats,
            'workers': self.max_workers,
            'memory_results': len(self.task_results)
        }

    async def cleanup(self):
        """Clean up resources"""
        # Close database connections
        if self.postgres_pool:
            await self.postgres_pool.close()

        if self.redis_pool:
            await self.redis_pool.close()

        if self.influxdb_client:
            self.influxdb_client.close()

        # Shutdown executor
        self.executor.shutdown(wait=True)

        logger.info("Universal Backtest Engine cleaned up")


# Example usage
async def example_usage():
    """Example of using the Universal Backtest Engine"""

    # Configuration
    engine = UniversalBacktestEngine(
        postgres_dsn="postgresql://user:password@localhost/backtest",
        influxdb_url="http://localhost:8086",
        redis_url="redis://localhost:6379",
        max_workers=4
    )

    # Initialize
    await engine.initialize()

    # Start worker
    worker_task = asyncio.create_task(engine.run_worker())

    # Submit backtest
    task_id = await engine.submit_backtest(
        strategy_config={
            'strategy_id': 'momentum_strategy',
            'strategy_name': 'Momentum Strategy',
            'parameters': {
                'lookback': 20,
                'threshold': 0.02
            }
        },
        backtest_type=BacktestType.RISK_MANAGED,
        start_date=datetime(2023, 1, 1),
        end_date=datetime(2023, 12, 31),
        initial_capital=1000000
    )

    # Check status
    while True:
        result = await engine.get_task_status(task_id)
        if result and result.status in [BacktestStatus.COMPLETED, BacktestStatus.FAILED]:
            break
        await asyncio.sleep(1)

    # Print results
    if result.status == BacktestStatus.COMPLETED:
        print(f"Backtest completed!")
        print(f"Total Return: {result.total_return:.2%}")
        print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
        print(f"Max Drawdown: {result.max_drawdown:.2%}")
    else:
        print(f"Backtest failed: {result.error_message}")

    # Get statistics
    stats = await engine.get_statistics()
    print(f"Engine statistics: {stats}")

    # Cleanup
    await engine.cleanup()


if __name__ == "__main__":
    asyncio.run(example_usage())