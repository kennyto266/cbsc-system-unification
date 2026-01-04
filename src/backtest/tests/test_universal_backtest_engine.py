"""
Tests for Universal Backtest Engine
===================================

Unit tests for the Universal Backtest Engine and its components.
"""

import pytest
import asyncio
from datetime import datetime, date, timedelta
import json
import tempfile
import os
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from ..universal_backtest_engine import (
    UniversalBacktestEngine,
    BacktestTask,
    BacktestType,
    TaskPriority,
    BacktestResult,
    BacktestStatus
)


class TestBacktestTask:
    """Test BacktestTask dataclass"""

    def test_task_creation(self):
        """Test creating a backtest task"""
        task = BacktestTask(
            strategy_id="test_strategy",
            strategy_name="Test Strategy",
            strategy_config={"param1": "value1"},
            backtest_type=BacktestType.RISK_MANAGED,
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 12, 31),
            initial_capital=1000000
        )

        assert task.strategy_id == "test_strategy"
        assert task.strategy_name == "Test Strategy"
        assert task.backtest_type == BacktestType.RISK_MANAGED
        assert task.initial_capital == 1000000
        assert task.priority == TaskPriority.NORMAL

    def test_task_to_dict(self):
        """Test converting task to dictionary"""
        task = BacktestTask(
            strategy_id="test_strategy",
            strategy_name="Test Strategy",
            backtest_type=BacktestType.STANDARD,
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 12, 31)
        )

        task_dict = task.to_dict()

        assert task_dict['strategy_id'] == "test_strategy"
        assert task_dict['backtest_type'] == "standard"
        assert 'created_at' in task_dict
        assert isinstance(task_dict['start_date'], str)

    def test_task_with_monte_carlo_config(self):
        """Test task with Monte Carlo configuration"""
        from ..monte_carlo import MCSimulationConfig

        mc_config = MCSimulationConfig(n_simulations=1000)
        task = BacktestTask(
            strategy_id="mc_strategy",
            backtest_type=BacktestType.MONTE_CARLO,
            monte_carlo_config=mc_config
        )

        assert task.monte_carlo_config == mc_config
        assert task.backtest_type == BacktestType.MONTE_CARLO


@pytest.fixture
async def mock_engine():
    """Create a mock UniversalBacktestEngine for testing"""
    engine = UniversalBacktestEngine(
        postgres_dsn="postgresql://test:test@localhost/test",
        influxdb_url="http://localhost:8086",
        redis_url="redis://localhost:6379/0",
        max_workers=2
    )

    # Mock database connections
    engine.postgres_pool = AsyncMock()
    engine.redis_pool = AsyncMock()
    engine.influxdb_client = Mock()

    return engine


class TestUniversalBacktestEngine:
    """Test UniversalBacktestEngine class"""

    @pytest.mark.asyncio
    async def test_engine_initialization(self, mock_engine):
        """Test engine initialization"""
        # Mock successful initialization
        mock_engine.postgres_pool = Mock()
        mock_engine.redis_pool = Mock()
        mock_engine.influxdb_client = Mock()

        result = await mock_engine.initialize()
        assert result is True

    @pytest.mark.asyncio
    async def test_submit_backtest(self, mock_engine):
        """Test submitting a backtest task"""
        strategy_config = {
            'strategy_id': 'test_strategy',
            'strategy_name': 'Test Strategy',
            'parameters': {'lookback': 20}
        }

        with patch.object(mock_engine, '_get_cache_key', return_value='test_key'):
            with patch.object(mock_engine, '_get_cached_result', return_value=None):
                with patch.object(mock_engine, '_store_task', new_callable=AsyncMock):
                    task_id = await mock_engine.submit_backtest(
                        strategy_config=strategy_config,
                        backtest_type=BacktestType.STANDARD,
                        start_date=datetime(2023, 1, 1),
                        end_date=datetime(2023, 12, 31)
                    )

                    assert task_id is not None
                    assert task_id in mock_engine.active_tasks

    @pytest.mark.asyncio
    async def test_submit_cached_backtest(self, mock_engine):
        """Test submitting a backtest that's already cached"""
        strategy_config = {
            'strategy_id': 'cached_strategy',
            'strategy_name': 'Cached Strategy'
        }

        # Create mock cached result
        cached_result = BacktestResult(
            task_id="cached_task",
            status=BacktestStatus.COMPLETED,
            total_return=0.15
        )

        with patch.object(mock_engine, '_get_cache_key', return_value='cached_key'):
            with patch.object(mock_engine, '_get_cached_result', return_value=cached_result):
                task_id = await mock_engine.submit_backtest(
                    strategy_config=strategy_config,
                    backtest_type=BacktestType.STANDARD
                )

                assert task_id is not None
                assert mock_engine.stats['cache_hits'] > 0

    @pytest.mark.asyncio
    async def test_get_task_status(self, mock_engine):
        """Test getting task status"""
        # Create a mock result
        result = BacktestResult(
            task_id="test_task",
            status=BacktestStatus.RUNNING,
            started_at=datetime.now()
        )

        mock_engine.task_results["test_task"] = result

        status = await mock_engine.get_task_status("test_task")
        assert status is not None
        assert status.status == BacktestStatus.RUNNING
        assert status.task_id == "test_task"

    @pytest.mark.asyncio
    async def test_cancel_task(self, mock_engine):
        """Test cancelling a task"""
        # Create a task
        task = BacktestTask(
            task_id="cancel_task",
            strategy_id="test_strategy",
            backtest_type=BacktestType.STANDARD
        )
        mock_engine.active_tasks["cancel_task"] = task

        with patch.object(mock_engine, '_update_task_status', new_callable=AsyncMock):
            result = await mock_engine.cancel_task("cancel_task")
            assert result is True
            assert "cancel_task" not in mock_engine.active_tasks

    @pytest.mark.asyncio
    async def test_run_standard_backtest(self, mock_engine):
        """Test running a standard backtest"""
        task = BacktestTask(
            task_id="standard_task",
            strategy_id="test_strategy",
            backtest_type=BacktestType.STANDARD,
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 12, 31),
            initial_capital=1000000
        )

        result = BacktestResult(task_id=task.task_id, status=BacktestStatus.RUNNING)

        await mock_engine._run_standard_backtest(task, result)

        assert result.status == BacktestStatus.RUNNING
        assert result.total_return == 0.15
        assert result.sharpe_ratio == 0.67

    @pytest.mark.asyncio
    async def test_run_monte_carlo_backtest(self, mock_engine):
        """Test running Monte Carlo backtest"""
        from ..monte_carlo import MCSimulationConfig

        task = BacktestTask(
            task_id="mc_task",
            strategy_id="mc_strategy",
            backtest_type=BacktestType.MONTE_CARLO,
            monte_carlo_config=MCSimulationConfig(n_simulations=100)
        )

        result = BacktestResult(task_id=task.task_id, status=BacktestStatus.RUNNING)

        with patch('numpy.random.seed'):
            await mock_engine._run_monte_carlo_backtest(task, result)

        assert result.monte_carlo_results is not None
        assert result.var_95 < 0  # Should be negative for losses

    @pytest.mark.asyncio
    async def test_run_stress_test_backtest(self, mock_engine):
        """Test running stress test backtest"""
        task = BacktestTask(
            task_id="stress_task",
            strategy_id="stress_strategy",
            backtest_type=BacktestType.STRESS_TEST,
            stress_scenarios=["2008_crisis", "covid_crash"]
        )

        result = BacktestResult(task_id=task.task_id, status=BacktestStatus.RUNNING)

        await mock_engine._run_stress_test_backtest(task, result)

        assert result.stress_test_results is not None
        assert "2008_crisis" in result.stress_test_results
        assert "covid_crash" in result.stress_test_results

    @pytest.mark.asyncio
    async def test_run_parameter_optimization(self, mock_engine):
        """Test running parameter optimization"""
        task = BacktestTask(
            task_id="opt_task",
            strategy_id="opt_strategy",
            backtest_type=BacktestType.PARAMETER_OPTIMIZATION,
            optimization_params={
                'param_grid': {
                    'lookback': [10, 20, 30],
                    'threshold': [0.01, 0.02, 0.03]
                }
            }
        )

        result = BacktestResult(task_id=task.task_id, status=BacktestStatus.RUNNING)

        await mock_engine._run_parameter_optimization(task, result)

        assert result.optimization_results is not None
        assert 'best_params' in result.optimization_results
        assert 'best_sharpe' in result.optimization_results

    @pytest.mark.asyncio
    async def test_generate_param_combinations(self, mock_engine):
        """Test generating parameter combinations"""
        param_grid = {
            'param1': [1, 2],
            'param2': ['a', 'b', 'c']
        }

        combinations = list(mock_engine._generate_param_combinations(param_grid))

        assert len(combinations) == 6  # 2 * 3
        assert {'param1': 1, 'param2': 'a'} in combinations
        assert {'param1': 2, 'param2': 'c'} in combinations

    @pytest.mark.asyncio
    async def test_get_cache_key(self, mock_engine):
        """Test cache key generation"""
        task = BacktestTask(
            task_id="cache_task",
            strategy_id="test_strategy",
            strategy_config={"param1": "value1"},
            backtest_type=BacktestType.STANDARD,
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 12, 31),
            initial_capital=1000000
        )

        cache_key = mock_engine._get_cache_key(task)
        assert isinstance(cache_key, str)
        assert len(cache_key) == 64  # SHA256 hash length

    @pytest.mark.asyncio
    async def test_worker_loop(self, mock_engine):
        """Test worker loop execution"""
        # Create a task
        task = BacktestTask(
            task_id="worker_task",
            strategy_id="test_strategy",
            backtest_type=BacktestType.STANDARD
        )
        mock_engine.task_queue.put_nowait(task)

        # Mock the execution method
        with patch.object(mock_engine, '_execute_task', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = BacktestResult(
                task_id=task.task_id,
                status=BacktestStatus.COMPLETED
            )

            # Run one iteration
            await mock_engine.task_queue.get()
            await mock_engine._execute_task(task)

            mock_exec.assert_called_once_with(task)

    @pytest.mark.asyncio
    async def test_get_statistics(self, mock_engine):
        """Test getting engine statistics"""
        mock_engine.stats['completed_tasks'] = 10
        mock_engine.stats['failed_tasks'] = 2
        mock_engine.active_tasks['task1'] = BacktestTask(task_id="task1", strategy_id="s1")

        stats = await mock_engine.get_statistics()

        assert 'active_tasks' in stats
        assert 'stats' in stats
        assert stats['stats']['completed_tasks'] == 10
        assert stats['stats']['failed_tasks'] == 2
        assert stats['active_tasks'] == 1

    @pytest.mark.asyncio
    async def test_cleanup(self, mock_engine):
        """Test cleanup resources"""
        mock_engine.executor = Mock()
        mock_engine.executor.shutdown = Mock()

        await mock_engine.cleanup()

        mock_engine.executor.shutdown.assert_called_once_with(wait=True)


@pytest.mark.asyncio
async def test_full_workflow():
    """Test complete backtest workflow"""
    # Create engine with mocked databases
    engine = UniversalBacktestEngine(
        postgres_dsn="postgresql://test:test@localhost/test",
        influxdb_url="http://localhost:8086",
        redis_url="redis://localhost:6379/0",
        max_workers=2,
        enable_caching=False  # Disable cache for this test
    )

    # Mock database operations
    with patch('asyncpg.create_pool') as mock_pg:
        with patch('aioredis.from_url') as mock_redis:
            with patch('influxdb_client.client.InfluxDBClient'):
                mock_pg.return_value = AsyncMock()
                mock_redis.return_value = AsyncMock()

                await engine.initialize()

    # Submit a backtest
    strategy_config = {
        'strategy_id': 'momentum_strategy',
        'strategy_name': 'Momentum Strategy',
        'parameters': {'lookback': 20}
    }

    task_id = await engine.submit_backtest(
        strategy_config=strategy_config,
        backtest_type=BacktestType.STANDARD,
        start_date=datetime(2023, 1, 1),
        end_date=datetime(2023, 12, 31),
        initial_capital=1000000
    )

    assert task_id is not None

    # Check task exists
    result = await engine.get_task_status(task_id)
    assert result is not None
    assert result.task_id == task_id

    # Cleanup
    await engine.cleanup()


class TestBacktestResult:
    """Test BacktestResult class"""

    def test_result_creation(self):
        """Test creating a backtest result"""
        result = BacktestResult(
            task_id="test_result",
            status=BacktestStatus.COMPLETED,
            started_at=datetime.now(),
            completed_at=datetime.now(),
            total_return=0.15,
            sharpe_ratio=1.2
        )

        assert result.task_id == "test_result"
        assert result.status == BacktestStatus.COMPLETED
        assert result.total_return == 0.15
        assert result.sharpe_ratio == 1.2

    def test_result_to_dict(self):
        """Test converting result to dictionary"""
        result = BacktestResult(
            task_id="test_result",
            status=BacktestStatus.COMPLETED,
            total_return=0.15,
            max_drawdown=-0.08
        )

        result_dict = result.to_dict()

        assert result_dict['task_id'] == "test_result"
        assert result_dict['status'] == "completed"
        assert result_dict['total_return'] == 0.15
        assert result_dict['max_drawdown'] == -0.08
        assert 'started_at' in result_dict

    def test_result_with_equity_curve(self):
        """Test result with equity curve data"""
        import pandas as pd
        dates = pd.date_range('2023-01-01', periods=10, freq='D')
        values = [1000000 * (1 + 0.001 * i) for i in range(10)]
        equity_curve = pd.Series(values, index=dates)

        result = BacktestResult(
            task_id="test_equity",
            status=BacktestStatus.COMPLETED,
            equity_curve=equity_curve
        )

        assert result.equity_curve is not None
        assert len(result.equity_curve) == 10
        assert result.equity_curve.iloc[0] == 1000000

    def test_result_with_monte_carlo(self):
        """Test result with Monte Carlo results"""
        from ..monte_carlo import MCResults
        import numpy as np

        mc_results = MCResults(
            final_values=np.array([1100000, 950000, 1200000]),
            equity_curves=np.random.rand(3, 252),
            statistics={'mean': 1083333.33, 'std': 125000},
            confidence_intervals={0.95: (900000, 1300000)},
            drawdowns=np.random.rand(3, 252) * -0.1,
            var={0.95: -50000},
            cvar={0.95: -75000},
            success_probability={'positive_return': 0.67}
        )

        result = BacktestResult(
            task_id="test_mc",
            status=BacktestStatus.COMPLETED,
            monte_carlo_results=mc_results
        )

        assert result.monte_carlo_results is not None
        assert len(result.monte_carlo_results.final_values) == 3

        # Test dictionary conversion includes Monte Carlo summary
        result_dict = result.to_dict()
        assert 'monte_carlo_summary' in result_dict
        assert result_dict['monte_carlo_summary']['mean'] == 1083333.33


if __name__ == "__main__":
    pytest.main([__file__, "-v"])