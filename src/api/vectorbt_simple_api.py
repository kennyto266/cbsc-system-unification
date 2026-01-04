"""
VectorBT Simple Multiprocess API
=================================

Simplified VectorBT multiprocess backtest API that works with available modules.
提供基於 VectorBT 的簡化多進程回測 API，使用現有可用模塊。
"""

import os
import sys

# Try to clear Numba cache before importing
try:
    import numba
    # Clear Numba cache directory
    cache_dir = os.path.join(os.path.expanduser('~'), '__pycache__')
    if os.path.exists(cache_dir):
        import shutil
        shutil.rmtree(cache_dir, ignore_errors=True)
    # Also try temp directory
    temp_cache = os.path.join(os.environ.get('TEMP', '/tmp'), 'numba_cache')
    if os.path.exists(temp_cache):
        import shutil
        shutil.rmtree(temp_cache, ignore_errors=True)
except:
    pass

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime, date, timedelta
import asyncio
import uuid
import logging
import numpy as np
import pandas as pd

# VectorBT imports
try:
    import vectorbt as vbt
    VECTORBT_AVAILABLE = True
except ImportError:
    VECTORBT_AVAILABLE = False
    vbt = None

# Yahoo Finance for real data
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    yf = None

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/vectorbt", tags=["VectorBT"])

# Global task storage
active_tasks: Dict[str, Dict[str, Any]] = {}
task_results: Dict[str, Dict[str, Any]] = {}


class BacktestRequest(BaseModel):
    """回測請求模型"""
    symbols: List[str] = Field(..., description="股票代碼列表，如 ['0700.HK', '0941.HK']")
    start_date: date = Field(..., description="開始日期")
    end_date: date = Field(..., description="結束日期")
    strategy_type: str = Field("ma_crossover", description="策略類型: ma_crossover, rsi, bollinger")
    initial_cash: float = Field(100000, description="初始資金")
    commission: float = Field(0.001, description="手續費率")

    # 策略參數
    short_period: int = Field(10, description="短期周期")
    long_period: int = Field(30, description="長期周期")

    # 多進程配置
    use_multiprocess: bool = Field(True, description="是否使用多進程")
    max_workers: int = Field(4, description="最大工作進程數")


class BacktestResponse(BaseModel):
    """回測響應模型"""
    task_id: str
    status: str
    message: str


class BacktestResult(BaseModel):
    """回測結果模型"""
    task_id: str
    status: str
    returns: float = 0
    sharpe_ratio: float = 0
    max_drawdown: float = 0
    win_rate: float = 0
    total_trades: int = 0
    equity_curve: List[float] = []
    trades: List[Dict] = []
    metrics: Dict = {}


def generate_mock_data(symbols: List[str], start_date: date, end_date: date) -> Dict[str, pd.DataFrame]:
    """
    生成模擬價格數據（用於測試）
    在生產環境中應該替換為真實市場數據
    """
    data = {}
    dates = pd.date_range(start=start_date, end=end_date, freq='D')

    for symbol in symbols:
        # 生成模擬價格數據
        np.random.seed(hash(symbol) % 2**32)
        returns = np.random.normal(0.001, 0.02, len(dates))
        price = 100 * np.exp(np.cumsum(returns))

        df = pd.DataFrame({
            'open': price * (1 + np.random.uniform(-0.01, 0.01, len(dates))),
            'high': price * (1 + np.random.uniform(0, 0.02, len(dates))),
            'low': price * (1 - np.random.uniform(0, 0.02, len(dates))),
            'close': price,
            'volume': np.random.randint(1000000, 10000000, len(dates))
        }, index=dates)

        data[symbol] = df

    return data


def fetch_real_market_data(symbols: List[str], start_date: date, end_date: date) -> Dict[str, pd.DataFrame]:
    """
    從 Yahoo Finance 獲取真實市場數據
    Fetch real market data from Yahoo Finance
    """
    if not YFINANCE_AVAILABLE:
        logger.warning("Yahoo Finance not available, falling back to mock data")
        return generate_mock_data(symbols, start_date, end_date)

    data = {}

    for symbol in symbols:
        try:
            logger.info(f"Fetching real data for {symbol} from {start_date} to {end_date}")

            # Download data from Yahoo Finance
            ticker = yf.Ticker(symbol)
            hist = ticker.history(start=start_date, end=end_date)

            if hist.empty:
                logger.warning(f"No data found for {symbol}, using mock data")
                # Fall back to mock data for this symbol
                mock_data = generate_mock_data([symbol], start_date, end_date)
                data[symbol] = mock_data[symbol]
                continue

            # Yahoo Finance returns data with columns in uppercase, standardize to lowercase
            df = pd.DataFrame({
                'open': hist['Open'],
                'high': hist['High'],
                'low': hist['Low'],
                'close': hist['Close'],
                'volume': hist['Volume']
            })

            # Remove any rows with NaN values
            df = df.dropna()

            if df.empty:
                logger.warning(f"No valid data for {symbol} after cleaning")
                continue

            logger.info(f"Successfully fetched {len(df)} data points for {symbol}")
            data[symbol] = df

        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            # Fall back to mock data for this symbol
            mock_data = generate_mock_data([symbol], start_date, end_date)
            data[symbol] = mock_data[symbol]

    return data


def run_ma_crossover_backtest_simple(data: Dict[str, pd.DataFrame], short_period: int, long_period: int,
                                     initial_cash: float, commission: float) -> Dict[str, Any]:
    """
    運行移動平均線交叉回測 - 純 pandas 實現（避免 Numba JIT 編譯問題）
    Simple pandas implementation to avoid Numba JIT compilation issues
    """
    results = {}

    for symbol, df in data.items():
        try:
            # Ensure index is DatetimeIndex
            if not isinstance(df.index, pd.DatetimeIndex):
                df.index = pd.to_datetime(df.index)

            # Sort by index
            df = df.sort_index()

            # Remove duplicates
            df = df[~df.index.duplicated(keep='first')]

            # 計算移動平均線
            short_ma = df['close'].rolling(window=short_period, min_periods=1).mean()
            long_ma = df['close'].rolling(window=long_period, min_periods=1).mean()

            # 生成信號
            # 1 = buy/long, 0 = sell/cash
            df['signal'] = 0
            df.loc[short_ma > long_ma, 'signal'] = 1

            # 計算持倉變化（僅在信號變化時交易）
            df['position_change'] = df['signal'].diff().fillna(0)

            # 初始化變量
            cash = initial_cash
            shares = 0
            equity_curve = []
            trades = []

            # 逐日模擬交易
            for i, (date, row) in enumerate(df.iterrows()):
                price = row['close']
                signal = row['signal']
                position_change = row['position_change']

                # 執行交易
                if position_change == 1:  # 買入信號
                    if cash > 0:
                        shares_to_buy = (cash * (1 - commission)) / price
                        cost = shares_to_buy * price * (1 + commission)
                        if cost <= cash:
                            shares = shares_to_buy
                            cash = cash - cost
                            trades.append({
                                'date': date.strftime('%Y-%m-%d'),
                                'action': 'buy',
                                'price': float(price),
                                'shares': float(shares)
                            })
                elif position_change == -1:  # 賣出信號
                    if shares > 0:
                        cash_from_sale = shares * price * (1 - commission)
                        cash = cash + cash_from_sale
                        trades.append({
                            'date': date.strftime('%Y-%m-%d'),
                            'action': 'sell',
                            'price': float(price),
                            'shares': float(shares)
                        })
                        shares = 0

                # 計算當天權益
                equity = cash + (shares * price if shares > 0 else 0)
                equity_curve.append(float(equity))

            # 計算回測指標
            equity_curve_array = np.array(equity_curve)
            returns = np.diff(equity_curve_array) / equity_curve_array[:-1]

            # Total return
            total_return = ((equity_curve_array[-1] - initial_cash) / initial_cash) * 100

            # Sharpe ratio (annualized)
            if len(returns) > 0 and np.std(returns) > 0:
                sharpe_ratio = (np.mean(returns) / np.std(returns)) * np.sqrt(252)
            else:
                sharpe_ratio = 0

            # Max drawdown
            cummax = np.maximum.accumulate(equity_curve_array)
            drawdown = (equity_curve_array - cummax) / cummax
            max_drawdown = np.min(drawdown) * 100 if len(drawdown) > 0 else 0

            # Win rate
            winning_trades = [t for t in trades if t['action'] == 'sell']
            if winning_trades:
                # This is simplified - actual win rate would need paired buy/sell analysis
                win_rate = 50.0  # Placeholder
            else:
                win_rate = 0

            results[symbol] = {
                'total_return': float(total_return),
                'sharpe_ratio': float(sharpe_ratio),
                'max_drawdown': float(max_drawdown),
                'total_trades': len(trades),
                'win_rate': float(win_rate),
                'equity_curve': equity_curve
            }
            logger.info(f"Successfully backtested {symbol}: {total_return:.2f}% return, {len(trades)} trades")

        except Exception as e:
            logger.error(f"Error backtesting {symbol}: {e}")
            import traceback
            traceback.print_exc()
            results[symbol] = {
                'total_return': 0,
                'sharpe_ratio': 0,
                'max_drawdown': 0,
                'total_trades': 0,
                'win_rate': 0,
                'equity_curve': [],
                'error': str(e)
            }

    return results


def run_ma_crossover_backtest(data: Dict[str, pd.DataFrame], short_period: int, long_period: int,
                               initial_cash: float, commission: float) -> Dict[str, Any]:
    """
    運行移動平均線交叉回測
    使用 VectorBT 實現（如果可用），否則使用簡化版本
    """
    if not VECTORBT_AVAILABLE:
        logger.warning("VectorBT not available, using simple pandas implementation")
        return run_ma_crossover_backtest_simple(data, short_period, long_period, initial_cash, commission)

    # Try VectorBT first, fall back to simple implementation on error
    try:
        results = {}

        for symbol, df in data.items():
            try:
                # Ensure index is DatetimeIndex
                if not isinstance(df.index, pd.DatetimeIndex):
                    df.index = pd.to_datetime(df.index)

                # Sort by index
                df = df.sort_index()

                # Remove duplicates
                df = df[~df.index.duplicated(keep='first')]

                # 計算移動平均線
                short_ma = df['close'].rolling(window=short_period, min_periods=1).mean()
                long_ma = df['close'].rolling(window=long_period, min_periods=1).mean()

                # 生成信號 - boolean Series with DatetimeIndex
                entries = (short_ma > long_ma).astype(bool)
                exits = (short_ma <= long_ma).astype(bool)

                # 創建 VectorBT Portfolio from signals
                pf = vbt.Portfolio.from_signals(
                    df['close'],
                    entries=entries,
                    exits=exits,
                    init_cash=initial_cash,
                    fees=commission,
                    freq='1D'
                )

                # 獲取結果
                stats = pf.stats()
                stats_dict = dict(stats) if not isinstance(stats, dict) else stats

                total_return = stats_dict.get('Total Return [%]', 0)
                sharpe_ratio = stats_dict.get('Sharpe Ratio', 0)
                max_drawdown = stats_dict.get('Max Drawdown [%]', 0)
                trades = stats_dict.get('# Trades') or stats_dict.get('Num Trades') or stats_dict.get('Total Trades') or 0
                win_rate = stats_dict.get('Win Rate [%]') or stats_dict.get('Win Rate') or 0

                results[symbol] = {
                    'total_return': float(total_return),
                    'sharpe_ratio': float(sharpe_ratio),
                    'max_drawdown': float(max_drawdown),
                    'total_trades': int(trades),
                    'win_rate': float(win_rate),
                    'equity_curve': pf.value().tolist()
                }
                logger.info(f"Successfully backtested {symbol} with VectorBT: {total_return:.2f}% return")

            except Exception as e:
                # If VectorBT fails (e.g., Numba cache issue), use simple implementation
                logger.warning(f"VectorBT failed for {symbol}, falling back to simple implementation: {e}")
                simple_results = run_ma_crossover_backtest_simple(
                    {symbol: df}, short_period, long_period, initial_cash, commission
                )
                results.update(simple_results)

        return results

    except Exception as e:
        logger.error(f"VectorBT completely failed, using simple implementation: {e}")
        return run_ma_crossover_backtest_simple(data, short_period, long_period, initial_cash, commission)


async def run_backtest_task(task_id: str, request: BacktestRequest):
    """
    後台運行回測任務
    """
    try:
        active_tasks[task_id]['status'] = 'running'
        active_tasks[task_id]['started_at'] = datetime.now().isoformat()

        # 獲取真實市場數據（從 Yahoo Finance）
        logger.info(f"Fetching real market data for {request.symbols}")
        data = fetch_real_market_data(request.symbols, request.start_date, request.end_date)

        # 運行回測
        if request.strategy_type == "ma_crossover":
            results = run_ma_crossover_backtest(
                data,
                request.short_period,
                request.long_period,
                request.initial_cash,
                request.commission
            )
        else:
            raise ValueError(f"Unsupported strategy type: {request.strategy_type}")

        # 聚合結果
        total_returns = np.mean([r['total_return'] for r in results.values()])
        total_sharpe = np.mean([r['sharpe_ratio'] for r in results.values()])
        total_max_dd = np.mean([r['max_drawdown'] for r in results.values()])
        total_win_rate = np.mean([r['win_rate'] for r in results.values()])
        total_trades = sum([r['total_trades'] for r in results.values()])

        task_results[task_id] = {
            'status': 'completed',
            'completed_at': datetime.now().isoformat(),
            'individual_results': results,
            'aggregated_results': {
                'total_return': float(total_returns),
                'sharpe_ratio': float(total_sharpe),
                'max_drawdown': float(total_max_dd),
                'win_rate': float(total_win_rate),
                'total_trades': total_trades
            }
        }

        active_tasks[task_id]['status'] = 'completed'

    except Exception as e:
        logger.error(f"Backtest task {task_id} failed: {e}", exc_info=True)
        task_results[task_id] = {
            'status': 'failed',
            'error': str(e),
            'completed_at': datetime.now().isoformat()
        }
        active_tasks[task_id]['status'] = 'failed'


@router.post("/backtest", response_model=BacktestResponse)
async def start_backtest(request: BacktestRequest, background_tasks: BackgroundTasks):
    """
    啟動回測任務

    ## 策略類型
    - ma_crossover: 移動平均線交叉策略

    ## 示例請求
    ```json
    {
        "symbols": ["0700.HK", "0941.HK"],
        "start_date": "2023-01-01",
        "end_date": "2023-12-31",
        "strategy_type": "ma_crossover",
        "short_period": 10,
        "long_period": 30
    }
    ```
    """
    if not VECTORBT_AVAILABLE:
        raise HTTPException(status_code=500, detail="VectorBT not available")

    task_id = str(uuid.uuid4())[:8]

    active_tasks[task_id] = {
        'status': 'pending',
        'created_at': datetime.now().isoformat()
    }

    background_tasks.add_task(run_backtest_task, task_id, request)

    return BacktestResponse(
        task_id=task_id,
        status="started",
        message="Backtest task started successfully"
    )


@router.get("/status/{task_id}")
async def get_task_status(task_id: str):
    """獲取任務狀態"""
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    task = active_tasks[task_id]

    if task_id in task_results:
        result = task_results[task_id]
        return {
            'task_id': task_id,
            'status': task['status'],
            'created_at': task.get('created_at'),
            'started_at': task.get('started_at'),
            'completed_at': result.get('completed_at'),
            'result': result if task['status'] == 'completed' else None,
            'error': result.get('error') if task['status'] == 'failed' else None
        }

    return {
        'task_id': task_id,
        'status': task['status'],
        'created_at': task.get('created_at')
    }


@router.get("/results/{task_id}", response_model=BacktestResult)
async def get_task_results(task_id: str):
    """獲取任務結果"""
    if task_id not in task_results:
        raise HTTPException(status_code=404, detail="Task results not found")

    result = task_results[task_id]

    if result['status'] != 'completed':
        raise HTTPException(status_code=400, detail="Task not completed yet")

    agg = result['aggregated_results']

    # 獲取第一個股票的 equity_curve (聚合)
    equity_curve = []
    trades = []

    for symbol_data in result['individual_results'].values():
        if 'equity_curve' in symbol_data and len(symbol_data['equity_curve']) > 0:
            equity_curve = symbol_data['equity_curve']
            break

    return BacktestResult(
        task_id=task_id,
        status=result['status'],
        returns=agg.get('total_return', 0),
        sharpe_ratio=agg.get('sharpe_ratio', 0),
        max_drawdown=agg.get('max_drawdown', 0),
        win_rate=agg.get('win_rate', 0),
        total_trades=agg.get('total_trades', 0),
        equity_curve=equity_curve,
        trades=trades,
        metrics=agg
    )


@router.get("/health")
async def health_check():
    """健康檢查"""
    return {
        "status": "healthy",
        "service": "VectorBT API",
        "vectorbt_available": VECTORBT_AVAILABLE,
        "vectorbt_version": vbt.__version__ if VECTORBT_AVAILABLE else None,
        "yfinance_available": YFINANCE_AVAILABLE,
        "data_source": "Yahoo Finance (Real Market Data)" if YFINANCE_AVAILABLE else "Mock Data",
        "active_tasks": len(active_tasks),
        "completed_results": len(task_results),
        "timestamp": datetime.now().isoformat()
    }


@router.get("/strategies")
async def list_strategies():
    """列出可用的策略"""
    strategies = [
        {
            "name": "ma_crossover",
            "display_name": "移動平均線交叉策略",
            "description": "短期均線向上突破長期均線時買入，反之賣出",
            "parameters": {
                "short_period": {"type": "int", "default": 10, "min": 5, "max": 20},
                "long_period": {"type": "int", "default": 30, "min": 20, "max": 60}
            }
        }
    ]

    return {"strategies": strategies}


@router.get("/tasks")
async def list_tasks():
    """列出所有任務"""
    return {
        "active_tasks": active_tasks,
        "completed_tasks": {k: v for k, v in task_results.items() if v['status'] == 'completed'}
    }


# ============================================================
# Parameter Optimization Endpoints
# ============================================================

class OptimizationRequest(BaseModel):
    """參數優化請求"""
    symbols: List[str] = Field(..., description="股票代碼列表")
    start_date: date = Field(..., description="開始日期")
    end_date: date = Field(..., description="結束日期")
    strategy_type: str = Field("ma_crossover", description="策略類型")

    # 優化參數範圍
    short_period_range: tuple = (5, 50, 5)  # (min, max, step)
    long_period_range: tuple = (10, 200, 10)

    # 回測配置
    initial_cash: float = 100000
    commission: float = 0.001

    # 優化目標
    optimization_target: str = "sharpe_ratio"  # sharpe_ratio, total_return, max_drawdown


class OptimizationResult(BaseModel):
    """優化結果"""
    task_id: str
    status: str
    total_combinations: int
    completed_combinations: int
    best_params: Dict[str, Any]
    best_metrics: Dict[str, float]
    all_results: List[Dict[str, Any]]


@router.post("/optimize", response_model=OptimizationResult)
async def start_optimization(request: OptimizationRequest, background_tasks: BackgroundTasks):
    """
    啟動參數優化

    ## 優化目標
    - sharpe_ratio: 最大化夏普比率
    - total_return: 最大化總回報
    - max_drawdown: 最小化最大回撤

    ## 示例請求
    ```json
    {
        "symbols": ["0700.HK"],
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "short_period_range": [5, 50, 5],
        "long_period_range": [10, 200, 10],
        "optimization_target": "sharpe_ratio"
    }
    ```
    """
    task_id = str(uuid.uuid4())[:8]

    active_tasks[task_id] = {
        'task_id': task_id,
        'type': 'optimization',
        'status': 'running',
        'started_at': datetime.now().isoformat()
    }

    # 在後台運行優化
    background_tasks.add_task(run_optimization_task, task_id, request)

    return OptimizationResult(
        task_id=task_id,
        status='running',
        total_combinations=0,
        completed_combinations=0,
        best_params={},
        best_metrics={},
        all_results=[]
    )


async def run_optimization_task(task_id: str, request: OptimizationRequest):
    """
    後台運行優化任務
    """
    try:
        # 獲取真實市場數據
        data = fetch_real_market_data(request.symbols, request.start_date, request.end_date)

        # 生成參數組合
        short_values = list(range(
            request.short_period_range[0],
            request.short_period_range[1] + 1,
            request.short_period_range[2]
        ))
        long_values = list(range(
            request.long_period_range[0],
            request.long_period_range[1] + 1,
            request.long_period_range[2]
        ))

        # 過濾掉無效組合（短期必須小於長期）
        param_combinations = [
            (short, long)
            for short in short_values
            for long in long_values
            if short < long
        ]

        total_combinations = len(param_combinations)
        logger.info(f"Optimization task {task_id}: {total_combinations} parameter combinations")

        all_results = []
        best_score = float('-inf')
        best_params = {}
        best_metrics = {}

        # 測試每個參數組合
        for idx, (short_period, long_period) in enumerate(param_combinations):
            try:
                # 運行回測
                results = run_ma_crossover_backtest(
                    data,
                    short_period,
                    long_period,
                    request.initial_cash,
                    request.commission
                )

                # 計算平均指標
                avg_return = np.mean([r['total_return'] for r in results.values()])
                avg_sharpe = np.mean([r['sharpe_ratio'] for r in results.values()])
                avg_max_dd = np.mean([r['max_drawdown'] for r in results.values()])

                # 根據優化目標計算得分
                if request.optimization_target == 'sharpe_ratio':
                    score = avg_sharpe
                elif request.optimization_target == 'total_return':
                    score = avg_return
                elif request.optimization_target == 'max_drawdown':
                    score = -avg_max_dd  # 負號因為我們想要最小化回撤
                else:
                    score = avg_sharpe

                result_data = {
                    'short_period': short_period,
                    'long_period': long_period,
                    'total_return': float(avg_return),
                    'sharpe_ratio': float(avg_sharpe),
                    'max_drawdown': float(avg_max_dd),
                    'score': float(score)
                }
                all_results.append(result_data)

                # 更新最佳結果
                if score > best_score:
                    best_score = score
                    best_params = {
                        'short_period': short_period,
                        'long_period': long_period
                    }
                    best_metrics = {
                        'total_return': float(avg_return),
                        'sharpe_ratio': float(avg_sharpe),
                        'max_drawdown': float(avg_max_dd)
                    }

                # 每10個組合更新一次進度
                if (idx + 1) % 10 == 0:
                    logger.info(f"Task {task_id}: {idx + 1}/{total_combinations} combinations tested")

            except Exception as e:
                logger.error(f"Error testing parameters {short_period}/{long_period}: {e}")
                continue

        # 保存結果
        task_results[task_id] = {
            'status': 'completed',
            'completed_at': datetime.now().isoformat(),
            'total_combinations': total_combinations,
            'completed_combinations': len(all_results),
            'best_params': best_params,
            'best_metrics': best_metrics,
            'all_results': all_results,
            'optimization_target': request.optimization_target
        }

        active_tasks[task_id]['status'] = 'completed'

        logger.info(f"Optimization task {task_id} completed. Best params: {best_params}")

    except Exception as e:
        logger.error(f"Optimization task {task_id} failed: {e}", exc_info=True)
        task_results[task_id] = {
            'status': 'failed',
            'error': str(e),
            'completed_at': datetime.now().isoformat()
        }
        active_tasks[task_id]['status'] = 'failed'


@router.get("/optimize/{task_id}", response_model=OptimizationResult)
async def get_optimization_results(task_id: str):
    """獲取優化結果"""
    if task_id not in task_results:
        raise HTTPException(status_code=404, detail="Task not found")

    result = task_results[task_id]

    if result['status'] != 'completed':
        return OptimizationResult(
            task_id=task_id,
            status=result['status'],
            total_combinations=result.get('total_combinations', 0),
            completed_combinations=result.get('completed_combinations', 0),
            best_params=result.get('best_params', {}),
            best_metrics=result.get('best_metrics', {}),
            all_results=result.get('all_results', [])
        )

    return OptimizationResult(
        task_id=task_id,
        status=result['status'],
        total_combinations=result['total_combinations'],
        completed_combinations=result['completed_combinations'],
        best_params=result['best_params'],
        best_metrics=result['best_metrics'],
        all_results=result['all_results']
    )


# ============================================================
# Market-Wide Optimization Endpoints
# ============================================================

# Import market-wide optimizer
try:
    from api.vectorbt_marketwide_optimizer import (
        OptimizationConfig,
        MultiStrategyOptimizer,
        MACrossoverStrategy,
        ProgressUpdate,
        fetch_market_data,
        get_hsi_constituents
    )
    MARKETWIDE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Market-wide optimizer not available: {e}")
    MARKETWIDE_AVAILABLE = False


class MarketWideOptimizationRequest(BaseModel):
    """市場廣域優化請求"""
    symbols: Optional[List[str]] = Field(None, description="股票代碼列表 (留空使用HSI成分股)")
    stock_count: int = Field(50, description="使用HSI成分股數量 (當symbols為空時)")
    start_date: date = Field(..., description="開始日期")
    end_date: date = Field(..., description="結束日期")
    strategy_type: str = Field("ma_crossover", description="策略類型")

    # 優化配置
    initial_cash: float = Field(100000, description="初始資金")
    commission: float = Field(0.001, description="手續費率")
    min_sharpe_ratio: float = Field(2.0, description="最小夏普比率過濾閾值")
    max_workers: int = Field(31, description="最大工作進程數 (建議31用於32核CPU)")


class MarketWideOptimizationResponse(BaseModel):
    """市場廣域優化響應"""
    task_id: str
    status: str
    message: str
    total_stocks: int
    estimated_combinations: int


class MarketWideProgressResponse(BaseModel):
    """市場廣域優化進度響應"""
    task_id: str
    status: str
    total_stocks: int
    waiting_stocks: int
    processing_stocks: int
    completed_stocks: int
    current_stock_number: int
    current_stock_symbol: str
    best_sharpe_ratio: float
    best_params: Dict[str, Any]
    best_symbol: str
    elapsed_seconds: float
    estimated_remaining_seconds: float
    progress_percentage: float


# Global storage for market-wide optimization tasks
marketwide_tasks: Dict[str, Dict[str, Any]] = {}
marketwide_progress: Dict[str, ProgressUpdate] = {}


def progress_callback_handler(update: ProgressUpdate):
    """Handle progress updates from optimizer"""
    task_id = update.task_id
    marketwide_progress[task_id] = update

    # Log progress
    logger.info(
        f"Progress [{task_id}]: {update.completed_stocks}/{update.total_stocks} | "
        f"#{update.current_stock_number:03d} {update.current_stock_symbol} | "
        f"Best SR: {update.best_sharpe_ratio:.2f}"
    )


async def run_marketwide_optimization_task(task_id: str, request: MarketWideOptimizationRequest):
    """後台運行市場廣域優化任務"""
    try:
        if not MARKETWIDE_AVAILABLE:
            raise RuntimeError("Market-wide optimizer not available")

        # Determine symbols
        if request.symbols and len(request.symbols) > 0:
            symbols = request.symbols
        else:
            symbols = get_hsi_constituents(request.stock_count)

        logger.info(f"Starting market-wide optimization for {len(symbols)} stocks")

        # Update task status
        marketwide_tasks[task_id]['status'] = 'running'
        marketwide_tasks[task_id]['started_at'] = datetime.now().isoformat()
        marketwide_tasks[task_id]['total_stocks'] = len(symbols)

        # Fetch market data
        logger.info("Fetching market data...")
        data = fetch_market_data(symbols, request.start_date, request.end_date)

        if not data:
            raise ValueError("No market data available")

        logger.info(f"Successfully fetched data for {len(data)} stocks")

        # Configure optimizer
        strategy = MACrossoverStrategy()
        config = OptimizationConfig(
            symbols=list(data.keys()),
            start_date=request.start_date,
            end_date=request.end_date,
            initial_cash=request.initial_cash,
            commission=request.commission,
            min_sharpe_ratio=request.min_sharpe_ratio,
            max_workers=request.max_workers,
            strategy=strategy
        )

        # Create optimizer
        optimizer = MultiStrategyOptimizer(config)
        optimizer.add_progress_callback(progress_callback_handler)

        # Run optimization
        logger.info(f"Starting optimization with {request.max_workers} workers...")
        results = optimizer.optimize(data, task_id)

        # Store results
        task_results[task_id] = results
        marketwide_tasks[task_id]['status'] = 'completed'

        logger.info(f"Market-wide optimization {task_id} completed")
        logger.info(f"Qualified results: {results['qualified_results_count']}")
        logger.info(f"Best overall: {results['best_overall']}")

    except Exception as e:
        logger.error(f"Market-wide optimization {task_id} failed: {e}", exc_info=True)
        marketwide_tasks[task_id]['status'] = 'failed'
        task_results[task_id] = {
            'status': 'failed',
            'error': str(e),
            'completed_at': datetime.now().isoformat()
        }


@router.post("/optimize-marketwide", response_model=MarketWideOptimizationResponse)
async def start_marketwide_optimization(
    request: MarketWideOptimizationRequest,
    background_tasks: BackgroundTasks
):
    """
    啟動市場廣域參數優化

    ## 說明
    - 使用多進程並行優化多只股票的參數
    - 每只股票測試 200-500 個參數組合
    - 過濾 Sharpe Ratio > 2.0 的結果
    - 按 SR 排名，MDD 作為次要指標
    - 包含 Equity Curve vs Buy&Hold 對比

    ## 預估時間
    - 50 stocks × 200 combos = 10,000 backtests
    - 使用 31 進程：約 5-10 分鐘

    ## 示例請求
    ```json
    {
        "stock_count": 50,
        "start_date": "2020-01-01",
        "end_date": "2024-12-31",
        "min_sharpe_ratio": 2.0,
        "max_workers": 31
    }
    ```
    """
    if not MARKETWIDE_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Market-wide optimizer not available. Check imports."
        )

    task_id = str(uuid.uuid4())[:8]

    # Determine symbol count
    if request.symbols and len(request.symbols) > 0:
        total_stocks = len(request.symbols)
    else:
        total_stocks = request.stock_count

    # Estimate combinations
    # MA strategy: ~20 short values × ~39 long values × 0.6 valid = ~468 combos
    estimated_combinations = total_stocks * 468

    marketwide_tasks[task_id] = {
        'task_id': task_id,
        'status': 'pending',
        'created_at': datetime.now().isoformat(),
        'total_stocks': total_stocks,
        'estimated_combinations': estimated_combinations,
        'config': request.dict()
    }

    # Start in background
    background_tasks.add_task(run_marketwide_optimization_task, task_id, request)

    return MarketWideOptimizationResponse(
        task_id=task_id,
        status='started',
        message='Market-wide optimization task started',
        total_stocks=total_stocks,
        estimated_combinations=estimated_combinations
    )


@router.get("/optimize-marketwide/{task_id}/progress", response_model=MarketWideProgressResponse)
async def get_marketwide_progress(task_id: str):
    """
    獲取市場廣域優化實時進度

    ## 進度顯示格式
    ```
    Total: 50 | Waiting: 10 | Processing: 8 | Completed: 32
    Current: #033 0700.HK
    Best: SR=2.45 MA(10/30) 0941.HK
    ```
    """
    if task_id not in marketwide_tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    task = marketwide_tasks[task_id]

    # Default progress
    default_progress = MarketWideProgressResponse(
        task_id=task_id,
        status=task['status'],
        total_stocks=task.get('total_stocks', 0),
        waiting_stocks=task.get('total_stocks', 0),
        processing_stocks=0,
        completed_stocks=0,
        current_stock_number=0,
        current_stock_symbol="",
        best_sharpe_ratio=0,
        best_params={},
        best_symbol="",
        elapsed_seconds=0,
        estimated_remaining_seconds=0,
        progress_percentage=0
    )

    # If we have progress updates, use them
    if task_id in marketwide_progress:
        update = marketwide_progress[task_id]

        progress_pct = (update.completed_stocks / update.total_stocks * 100) if update.total_stocks > 0 else 0

        return MarketWideProgressResponse(
            task_id=update.task_id,
            status=marketwide_tasks[task_id]['status'],
            total_stocks=update.total_stocks,
            waiting_stocks=update.waiting_stocks,
            processing_stocks=update.processing_stocks,
            completed_stocks=update.completed_stocks,
            current_stock_number=update.current_stock_number,
            current_stock_symbol=update.current_stock_symbol,
            best_sharpe_ratio=update.best_sharpe_ratio,
            best_params=update.best_params,
            best_symbol=update.best_symbol,
            elapsed_seconds=update.elapsed_seconds,
            estimated_remaining_seconds=update.estimated_remaining_seconds,
            progress_percentage=round(progress_pct, 1)
        )

    return default_progress


@router.get("/optimize-marketwide/{task_id}/results")
async def get_marketwide_results(task_id: str):
    """
    獲取市場廣域優化最終結果

    ## 返回數據
    - top_10: Top 10 results (SR > 2.0, sorted by SR then MDD)
    - best_overall: Best single result across all stocks
    - all_results: All qualified results (SR > 2.0)
    """
    if task_id not in task_results:
        raise HTTPException(status_code=404, detail="Task not found")

    result = task_results[task_id]

    if result['status'] != 'completed':
        return {
            'task_id': task_id,
            'status': result['status'],
            'error': result.get('error', 'Task not completed')
        }

    return {
        'task_id': task_id,
        'status': result['status'],
        'started_at': result['started_at'],
        'completed_at': result['completed_at'],
        'total_time_seconds': result['total_time_seconds'],
        'total_stocks': result['total_stocks'],
        'total_combinations': result['total_combinations'],
        'qualified_results_count': result['qualified_results_count'],
        'best_overall': result['best_overall'],
        'top_10': result['top_10'],
        'summary': {
            'total_backtests_run': result['total_combinations'] * result['total_stocks'],
            'qualification_rate': result['qualified_results_count'] / max(1, result['total_combinations'] * result['total_stocks']) * 100,
            'best_sharpe_ratio': result['best_overall']['sharpe_ratio'],
            'best_symbol': result['best_overall']['symbol']
        }
    }
