"""
VectorBT Multiprocess Integration Engine
======================================

統一的VectorBT多進程回測引擎，整合現有組件：
- Personal VectorBT Engine (個人策略)
- High-Performance VectorBT Engine (高性能回測)
- Parallel Processor (多進程執行)

核心特性：
- 動態進程池管理
- 智能資源分配
- 結果聚合和優化
- 實時監控和故障恢復
"""

import asyncio
import multiprocessing as mp
import time
from typing import Dict, List, Optional, Any, Callable, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum
import numpy as np
import pandas as pd
import json
import logging
from pathlib import Path
import pickle
from concurrent.futures import ProcessPoolExecutor, as_completed
import uuid

# VectorBT imports
try:
    import vectorbt as vbt
    VECTORBT_AVAILABLE = True
except ImportError:
    VECTORBT_AVAILABLE = False
    vbt = None

# Internal imports
from .parallel_processor import ParallelProcessor, ExecutionMode, TaskStatus
from .vectorbt_engine import VectorbtBacktestEngine, BacktestConfig, BacktestResult
from personal_trading_system.vectorbt_engine import PersonalVectorBTEngine, BacktestConfig as PersonalConfig

logger = logging.getLogger(__name__)


class MultiprocessMode(str, Enum):
    """多進程執行模式"""
    PORTFOLIO_LEVEL = "portfolio"      # 投資組合級別並行
    STRATEGY_LEVEL = "strategy"        # 策略級別並行
    SYMBOL_LEVEL = "symbol"            # 股票級別並行
    PARAMETER_LEVEL = "parameter"      # 參數級別並行
    HYBRID = "hybrid"                  # 混合模式


@dataclass
class VectorBTMultiprocessConfig:
    """VectorBT多進程配置"""
    # 基礎配置
    symbols: List[str]
    start_date: date
    end_date: date
    initial_capital: float = 100000
    commission: float = 0.001

    # 多進程配置
    execution_mode: MultiprocessMode = MultiprocessMode.PORTFOLIO_LEVEL
    max_workers: int = field(default_factory=lambda: min(32, mp.cpu_count()))
    chunk_size: int = 10
    enable_resource_monitoring: bool = True
    memory_limit_per_worker: float = 1024  # MB

    # VectorBT特定配置
    vectorbt_settings: Dict[str, Any] = field(default_factory=dict)
    cache_data: bool = True
    optimize_memory: bool = True

    # 輸出配置
    save_results: bool = True
    output_dir: str = "backtest_results"
    generate_report: bool = True


@dataclass
class MultiprocessTask:
    """多進程任務定義"""
    task_id: str
    task_type: str  # 'single_backtest', 'parameter_optimization', 'portfolio_analysis'
    symbol: Optional[str] = None
    strategy_func: Optional[Callable] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0

    # 任務元數據
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None

    # 依賴關係
    dependencies: List[str] = field(default_factory=list)
    children: List[str] = field(default_factory=list)


class VectorBTMultiprocessEngine:
    """
    VectorBT多進程回測引擎

    整合現有VectorBT組件，提供統一的多進程回測能力
    """

    def __init__(self, config: VectorBTMultiprocessConfig):
        """
        初始化多進程引擎

        Args:
            config: 多進程配置
        """
        if not VECTORBT_AVAILABLE:
            raise ImportError("VectorBT not installed. Install with: pip install vectorbt>=0.25.0")

        self.config = config
        self.engine_id = str(uuid.uuid4())[:8]

        # 初始化組件
        self.parallel_processor = ParallelProcessor(
            max_workers=config.max_workers,
            execution_mode=ExecutionMode.PROCESS,
            enable_resource_monitoring=config.enable_resource_monitoring,
            max_memory_per_worker=config.memory_limit_per_worker
        )

        # 數據緩存
        self.data_cache: Dict[str, pd.DataFrame] = {}
        self.hkma_data: Optional[pd.DataFrame] = None

        # 任務管理
        self.tasks: Dict[str, MultiprocessTask] = {}
        self.task_results: Dict[str, BacktestResult] = {}
        self.completed_tasks: List[str] = []
        self.failed_tasks: List[str] = []

        # 統計信息
        self.stats = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'total_execution_time': 0.0,
            'average_task_time': 0.0,
            'peak_memory_usage': 0.0,
            'cache_hit_rate': 0.0
        }

        logger.info(f"VectorBT Multiprocess Engine initialized: {self.engine_id}")

    async def initialize(self) -> bool:
        """
        初始化引擎和數據

        Returns:
            True if successful
        """
        try:
            logger.info("Initializing VectorBT Multiprocess Engine...")

            # 初始化並行處理器
            await self.parallel_processor.initialize()

            # 預加載數據（如果啟用緩存）
            if self.config.cache_data:
                await self._preload_data()

            # 創建輸出目錄
            if self.config.save_results:
                Path(self.config.output_dir).mkdir(parents=True, exist_ok=True)

            logger.info("VectorBT Multiprocess Engine initialization complete")
            return True

        except Exception as e:
            logger.error(f"Engine initialization failed: {e}", exc_info=True)
            return False

    async def _preload_data(self):
        """預加載所有股票數據到緩存"""
        try:
            logger.info(f"Preloading data for {len(self.config.symbols)} symbols...")

            # 使用個人VectorBT引擎加載數據
            personal_engine = PersonalVectorBTEngine()

            for symbol in self.config.symbols:
                try:
                    data = personal_engine.load_data(
                        symbol=symbol,
                        start_date=self.config.start_date,
                        end_date=self.config.end_date,
                        hkma_data=self.hkma_data
                    )

                    if data is not None and not data.empty:
                        self.data_cache[symbol] = data
                        logger.debug(f"Loaded {len(data)} records for {symbol}")

                except Exception as e:
                    logger.warning(f"Failed to load data for {symbol}: {e}")

            logger.info(f"Data preloading complete: {len(self.data_cache)} symbols cached")

        except Exception as e:
            logger.error(f"Data preloading failed: {e}")

    async def run_portfolio_backtest(
        self,
        strategy_func: Callable,
        symbols: Optional[List[str]] = None,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, BacktestResult]:
        """
        運行投資組合回測（多股票並行）

        Args:
            strategy_func: 策略函數
            symbols: 股票列表（None表示使用配置中的所有股票）
            parameters: 策略參數

        Returns:
            股票回測結果字典
        """
        symbols = symbols or self.config.symbols
        parameters = parameters or {}

        logger.info(f"Starting portfolio backtest: {len(symbols)} symbols")
        start_time = time.time()

        # 創建任務
        tasks = []
        for symbol in symbols:
            task_id = f"portfolio_{symbol}_{self.engine_id}"
            task = MultiprocessTask(
                task_id=task_id,
                task_type="single_backtest",
                symbol=symbol,
                strategy_func=strategy_func,
                parameters=parameters.copy(),
                priority=1
            )
            tasks.append(task)
            self.tasks[task_id] = task

        # 根據執行模式處理
        if self.config.execution_mode == MultiprocessMode.PORTFOLIO_LEVEL:
            results = await self._execute_portfolio_parallel(tasks)
        elif self.config.execution_mode == MultiprocessMode.SYMBOL_LEVEL:
            results = await self._execute_symbol_parallel(tasks)
        else:
            results = await self._execute_hybrid_parallel(tasks)

        # 聚合結果
        execution_time = time.time() - start_time
        self.stats['total_execution_time'] += execution_time
        self.stats['average_task_time'] = execution_time / len(tasks) if tasks else 0

        logger.info(f"Portfolio backtest completed: {len(results)} results in {execution_time:.2f}s")
        return results

    async def _execute_portfolio_parallel(
        self,
        tasks: List[MultiprocessTask]
    ) -> Dict[str, BacktestResult]:
        """投資組合級別並行執行"""
        logger.info("Executing portfolio-level parallel backtest")

        # 準備批量任務
        batch_tasks = []
        for task in tasks:
            task_data = (
                task.task_id,
                self._run_single_backtest,
                (task.symbol, task.strategy_func, task.parameters)
            )
            batch_tasks.append(task_data)

        # 執行批量任務
        task_results = await self.parallel_processor.process_batch(
            batch_tasks,
            max_concurrent=self.config.max_workers
        )

        # 處理結果
        results = {}
        for task_id, result in task_results.items():
            if result.status == TaskStatus.COMPLETED and result.result:
                results[task_id] = result.result
                self.completed_tasks.append(task_id)
            else:
                self.failed_tasks.append(task_id)
                logger.error(f"Task {task_id} failed: {result.error}")

        return results

    async def _execute_symbol_parallel(
        self,
        tasks: List[MultiprocessTask]
    ) -> Dict[str, BacktestResult]:
        """股票級別並行執行"""
        logger.info("Executing symbol-level parallel backtest")

        # 按股票分組任務
        symbol_groups = {}
        for task in tasks:
            symbol = task.symbol
            if symbol not in symbol_groups:
                symbol_groups[symbol] = []
            symbol_groups[symbol].append(task)

        # 並行處理每個股票的任務
        results = {}
        for symbol, symbol_tasks in symbol_groups.items():
            if len(symbol_tasks) == 1:
                # 單個任務直接執行
                task = symbol_tasks[0]
                result = await self._execute_single_task(task)
                if result:
                    results[task.task_id] = result
            else:
                # 多個任務按順序執行（同一股票的任務）
                for task in symbol_tasks:
                    result = await self._execute_single_task(task)
                    if result:
                        results[task.task_id] = result

        return results

    async def _execute_hybrid_parallel(
        self,
        tasks: List[MultiprocessTask]
    ) -> Dict[str, BacktestResult]:
        """混合模式並行執行"""
        logger.info("Executing hybrid parallel backtest")

        # 智能分組：按資源需求和依賴關係
        high_priority_tasks = [t for t in tasks if t.priority >= 2]
        normal_tasks = [t for t in tasks if t.priority < 2]

        results = {}

        # 先執行高優先級任務
        if high_priority_tasks:
            high_results = await self._execute_portfolio_parallel(high_priority_tasks)
            results.update(high_results)

        # 再執行普通任務
        if normal_tasks:
            normal_results = await self._execute_portfolio_parallel(normal_tasks)
            results.update(normal_results)

        return results

    async def _execute_single_task(self, task: MultiprocessTask) -> Optional[BacktestResult]:
        """執行單個任務"""
        try:
            task.started_at = time.time()

            # 提交任務到並行處理器
            await self.parallel_processor.submit_task(
                task_id=task.task_id,
                func=self._run_single_backtest,
                args=(task.symbol, task.strategy_func, task.parameters),
                priority=task.priority
            )

            # 等待完成
            result = await self.parallel_processor.wait_for_completion([task.task_id])

            task.completed_at = time.time()

            if task.task_id in result and result[task.task_id].status == TaskStatus.COMPLETED:
                self.completed_tasks.append(task.task_id)
                return result[task.task_id].result
            else:
                self.failed_tasks.append(task.task_id)
                return None

        except Exception as e:
            logger.error(f"Task {task.task_id} execution failed: {e}")
            self.failed_tasks.append(task.task_id)
            return None

    @staticmethod
    def _run_single_backtest(
        symbol: str,
        strategy_func: Callable,
        parameters: Dict[str, Any]
    ) -> BacktestResult:
        """
        在工作進程中運行單個回測（靜態方法，可被pickle）

        Args:
            symbol: 股票代碼
            strategy_func: 策略函數
            parameters: 策略參數

        Returns:
            回測結果
        """
        try:
            # 創建個人VectorBT引擎
            engine = PersonalVectorBTEngine()

            # 解析參數
            start_date = parameters.get('start_date', date(2020, 1, 1))
            end_date = parameters.get('end_date', date(2025, 1, 1))

            # 運行回測
            result = engine.backtest_strategy(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                strategy_func=strategy_func,
                strategy_name=parameters.get('strategy_name', 'VectorBT Strategy'),
                parameters=parameters
            )

            # 轉換為標準BacktestResult格式
            backtest_result = BacktestResult(
                strategy_name=result.strategy_name,
                start_date=start_date,
                end_date=end_date,
                initial_capital=parameters.get('initial_capital', 100000),
                final_capital=result.final_capital,
                total_return=result.total_return,
                annualized_return=result.annualized_return,
                sharpe_ratio=result.sharpe_ratio,
                max_drawdown=result.max_drawdown,
                metrics={
                    'win_rate': result.win_rate,
                    'total_trades': result.total_trades,
                    'symbol': symbol,
                    'parameters': result.parameters
                },
                trades=result.trades,
                portfolio_values=result.equity_curve,
                daily_returns=[]
            )

            return backtest_result

        except Exception as e:
            logger.error(f"Single backtest failed for {symbol}: {e}")
            raise

    async def run_parameter_optimization(
        self,
        strategy_func: Callable,
        param_grid: Dict[str, List[Any]],
        symbols: Optional[List[str]] = None,
        objective: str = 'sharpe_ratio'
    ) -> Dict[str, Any]:
        """
        運行參數優化（多進程）

        Args:
            strategy_func: 策略函數
            param_grid: 參數網格
            symbols: 優化股票列表
            objective: 優化目標

        Returns:
            優化結果
        """
        symbols = symbols or self.config.symbols[:1]  # 默認只用第一個股票優化

        logger.info(f"Starting parameter optimization: {len(param_grid)} parameters")
        start_time = time.time()

        # 使用個人VectorBT引擎的優化功能
        if len(symbols) == 1:
            # 單股票優化
            symbol = symbols[0]
            engine = PersonalVectorBTEngine()

            optimization_result = engine.optimize_strategy(
                symbol=symbol,
                start_date=self.config.start_date,
                end_date=self.config.end_date,
                strategy_func=strategy_func,
                param_grid=param_grid,
                objective=objective
            )

            execution_time = time.time() - start_time
            optimization_result['execution_time'] = execution_time
            optimization_result['engine_id'] = self.engine_id

            logger.info(f"Parameter optimization completed in {execution_time:.2f}s")
            return optimization_result

        else:
            # 多股票並行優化
            return await self._run_multi_symbol_optimization(
                strategy_func, param_grid, symbols, objective
            )

    async def _run_multi_symbol_optimization(
        self,
        strategy_func: Callable,
        param_grid: Dict[str, List[Any]],
        symbols: List[str],
        objective: str
    ) -> Dict[str, Any]:
        """多股票並行參數優化"""
        logger.info("Running multi-symbol parallel optimization")

        # 為每個股票創建優化任務
        tasks = []
        for symbol in symbols:
            task_id = f"opt_{symbol}_{self.engine_id}"
            task = MultiprocessTask(
                task_id=task_id,
                task_type="parameter_optimization",
                symbol=symbol,
                strategy_func=strategy_func,
                parameters={'param_grid': param_grid, 'objective': objective},
                priority=2  # 優化任務優先級較高
            )
            tasks.append(task)

        # 並行執行優化
        results = await self._execute_portfolio_parallel(tasks)

        # 聚合優化結果
        best_params = {}
        best_scores = {}
        all_results = {}

        for task_id, result in results.items():
            symbol = task_id.split('_')[1]
            if result.metrics:
                best_params[symbol] = result.metrics.get('best_parameters', {})
                best_scores[symbol] = result.metrics.get('best_score', 0)
                all_results[symbol] = result

        return {
            'best_parameters': best_params,
            'best_scores': best_scores,
            'all_results': all_results,
            'engine_id': self.engine_id,
            'execution_mode': 'multi_symbol_parallel'
        }

    async def aggregate_results(self, results: Dict[str, BacktestResult]) -> Dict[str, Any]:
        """
        聚合回測結果

        Args:
            results: 回測結果字典

        Returns:
            聚合結果
        """
        if not results:
            return {}

        logger.info(f"Aggregating {len(results)} backtest results")

        # 提取所有指標
        total_returns = [r.total_return for r in results.values()]
        sharpe_ratios = [r.sharpe_ratio for r in results.values()]
        max_drawdowns = [r.max_drawdown for r in results.values()]
        final_capitals = [r.final_capital for r in results.values()]

        # 計算聚合統計
        aggregation = {
            'total_strategies': len(results),
            'successful_strategies': len([r for r in results.values() if r.total_return > 0]),
            'average_return': np.mean(total_returns),
            'median_return': np.median(total_returns),
            'best_return': np.max(total_returns),
            'worst_return': np.min(total_returns),
            'average_sharpe': np.mean(sharpe_ratios),
            'median_sharpe': np.median(sharpe_ratios),
            'best_sharpe': np.max(sharpe_ratios),
            'average_max_drawdown': np.mean(max_drawdowns),
            'worst_max_drawdown': np.max(max_drawdowns),
            'total_final_capital': sum(final_capitals),
            'average_final_capital': np.mean(final_capitals),
            'win_rate': len([r for r in results.values() if r.total_return > 0]) / len(results) * 100,
            'engine_id': self.engine_id
        }

        # 添加詳細結果
        aggregation['detailed_results'] = {
            task_id: {
                'symbol': result.metrics.get('symbol', 'Unknown'),
                'total_return': result.total_return,
                'sharpe_ratio': result.sharpe_ratio,
                'max_drawdown': result.max_drawdown,
                'final_capital': result.final_capital,
                'parameters': result.metrics.get('parameters', {})
            }
            for task_id, result in results.items()
        }

        # 性能統計
        aggregation['performance_stats'] = {
            'total_execution_time': self.stats['total_execution_time'],
            'average_task_time': self.stats['average_task_time'],
            'completed_tasks': len(self.completed_tasks),
            'failed_tasks': len(self.failed_tasks),
            'success_rate': len(self.completed_tasks) / (len(self.completed_tasks) + len(self.failed_tasks)) * 100 if (len(self.completed_tasks) + len(self.failed_tasks)) > 0 else 0
        }

        logger.info("Results aggregation complete")
        return aggregation

    async def save_results(self, results: Dict[str, Any], filename: Optional[str] = None):
        """
        保存結果到文件

        Args:
            results: 結果數據
            filename: 文件名（可選）
        """
        if not self.config.save_results:
            return

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"vectorbt_backtest_{self.engine_id}_{timestamp}.json"

        filepath = Path(self.config.output_dir) / filename

        try:
            # 轉換結果為可序列化格式
            serializable_results = {}
            for key, value in results.items():
                if isinstance(value, BacktestResult):
                    serializable_results[key] = {
                        'strategy_name': value.strategy_name,
                        'start_date': value.start_date.isoformat(),
                        'end_date': value.end_date.isoformat(),
                        'total_return': value.total_return,
                        'sharpe_ratio': value.sharpe_ratio,
                        'max_drawdown': value.max_drawdown,
                        'final_capital': value.final_capital,
                        'metrics': value.metrics
                    }
                else:
                    serializable_results[key] = value

            # 添加元數據
            output_data = {
                'metadata': {
                    'engine_id': self.engine_id,
                    'timestamp': datetime.now().isoformat(),
                    'config': {
                        'symbols': self.config.symbols,
                        'execution_mode': self.config.execution_mode,
                        'max_workers': self.config.max_workers
                    },
                    'stats': self.stats
                },
                'results': serializable_results
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Results saved to: {filepath}")

        except Exception as e:
            logger.error(f"Failed to save results: {e}")

    async def get_engine_status(self) -> Dict[str, Any]:
        """獲取引擎狀態"""
        processor_stats = await self.parallel_processor.get_statistics()

        return {
            'engine_id': self.engine_id,
            'status': 'running',
            'config': {
                'execution_mode': self.config.execution_mode,
                'max_workers': self.config.max_workers,
                'symbols_count': len(self.config.symbols),
                'cache_enabled': self.config.cache_data
            },
            'tasks': {
                'total': len(self.tasks),
                'completed': len(self.completed_tasks),
                'failed': len(self.failed_tasks),
                'pending': len(self.tasks) - len(self.completed_tasks) - len(self.failed_tasks)
            },
            'performance': self.stats,
            'system_resources': processor_stats.get('system_resources', {}),
            'cache_status': {
                'cached_symbols': len(self.data_cache),
                'cache_hit_rate': self.stats.get('cache_hit_rate', 0)
            }
        }

    async def shutdown(self):
        """關閉引擎並清理資源"""
        logger.info("Shutting down VectorBT Multiprocess Engine...")

        try:
            # 關閉並行處理器
            await self.parallel_processor.shutdown()

            # 清理緩存
            self.data_cache.clear()

            logger.info("VectorBT Multiprocess Engine shutdown complete")

        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

    async def __aenter__(self):
        """異步上下文管理器支持"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """異步上下文管理器清理"""
        await self.shutdown()


# 便利函數
async def run_vectorbt_multiprocess_backtest(
    symbols: List[str],
    strategy_func: Callable,
    start_date: date,
    end_date: date,
    execution_mode: MultiprocessMode = MultiprocessMode.PORTFOLIO_LEVEL,
    max_workers: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    運行VectorBT多進程回測的便利函數

    Args:
        symbols: 股票列表
        strategy_func: 策略函數
        start_date: 開始日期
        end_date: 結束日期
        execution_mode: 執行模式
        max_workers: 最大工作進程數
        **kwargs: 其他參數

    Returns:
        回測結果
    """
    config = VectorBTMultiprocessConfig(
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        execution_mode=execution_mode,
        max_workers=max_workers or min(32, mp.cpu_count()),
        **kwargs
    )

    async with VectorBTMultiprocessEngine(config) as engine:
        # 運行投資組合回測
        results = await engine.run_portfolio_backtest(strategy_func)

        # 聚合結果
        aggregated = await engine.aggregate_results(results)

        # 保存結果
        await engine.save_results(aggregated)

        # 獲取引擎狀態
        status = await engine.get_engine_status()

        return {
            'individual_results': results,
            'aggregated_results': aggregated,
            'engine_status': status
        }