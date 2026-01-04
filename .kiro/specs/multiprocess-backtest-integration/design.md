# VectorBT多進程回測集成技術設計文檔

## 技術架構設計

### 系統概述

本文檔描述了將基於VectorBT框架的多進程回測功能集成到CBSC量化策略管理系統的完整技術架構。該設計利用VectorBT的向量化計算優勢和現有的多進程處理器，實現高性能的量化策略回測。

### 核心架構組件

```
┌─────────────────────────────────────────────────────────────────┐
│                        CBSC前端層                                │
│                   (React Dashboard)                             │
└─────────────────────────┬───────────────────────────────────────┘
                          │ HTTP/WebSocket
┌─────────────────────────▼───────────────────────────────────────┐
│                    API網關層                                     │
│                   (FastAPI + 路由)                              │
└───────────────────────┬─────────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────────┐
│                VectorBT服務層                                   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐            │
│  │向量化引擎   │ │多進程管理器 │ │結果聚合器       │            │
│  │VectorBT Engine│ │Process Mgr │ │Result Aggregator│            │
│  └─────────────┘ └─────────────┘ └─────────────────┘            │
└───────────────────────┬─────────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────────┐
│                 數據與存儲層                                      │
│  ┌──────────┐ ┌──────────┐ ┌─────────┐ ┌─────────────┐        │
│  │Redis緩存 │ │PostgreSQL│ │InfluxDB  │ │市場數據API │        │
│  └──────────┘ └──────────┘ └─────────┘ └─────────────┘        │
└─────────────────────────────────────────────────────────────────┘
```

### VectorBT集成模式

#### 1. 向量化計算引擎

```python
class VectorBTComputeEngine:
    """
    VectorBT向量化計算引擎
    提供高性能的向量化回測計算能力
    """

    def __init__(self, config: VectorBTConfig):
        self.config = config
        self.computing_resources = ResourceMonitor()
        self.chunk_size = self._calculate_optimal_chunk_size()

    async def execute_vectorized_backtest(
        self,
        strategy: StrategyFunction,
        data: pd.DataFrame,
        symbols: List[str],
        chunk_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        執行向量化回測

        將數據分塊並利用VectorBT的並行能力進行計算
        """
        # 數據預處理和驗證
        processed_data = self._prepare_vectorized_data(data, symbols)

        # 計算最優分塊大小
        chunk_size = chunk_size or self.chunk_size
        data_chunks = self._chunk_data(processed_data, chunk_size)

        # 創建向量化任務
        tasks = []
        for chunk_id, chunk_data in enumerate(data_chunks):
            task = VectorizedTask(
                task_id=f"vbt_chunk_{chunk_id}",
                strategy=strategy,
                data=chunk_data,
                symbols=symbols
            )
            tasks.append(task)

        # 並行執行
        results = await self._execute_parallel_tasks(tasks)

        # 聚合結果
        return self._aggregate_vectorized_results(results)
```

#### 2. 多進程執行流程

```python
class VectorBTMultiprocessManager:
    """
    VectorBT多進程管理器
    協調VectorBT計算在多個進程中的執行
    """

    async def run_parallel_backtest(
        self,
        backtest_request: BacktestRequest
    ) -> BacktestResult:
        """
        運行並行回測的主流程
        """
        # 1. 初始化階段
        await self._initialize_vectorbt_environment()

        # 2. 數據準備階段
        market_data = await self._fetch_and_validate_data(
            backtest_request.symbols,
            backtest_request.start_date,
            backtest_request.end_date
        )

        # 3. 任務分發階段
        task_distribution = self._create_task_distribution(
            backtest_request.strategies,
            market_data,
            backtest_request.optimization_params
        )

        # 4. 並行執行階段
        execution_results = await self._execute_vectorized_tasks(
            task_distribution
        )

        # 5. 結果聚合階段
        final_results = await self._aggregate_and_validate_results(
            execution_results
        )

        # 6. 持久化階段
        await self._persist_results(final_results)

        return final_results
```

### 數據流設計

```
市場數據 → 數據預處理 → 向量化轉換 → 分塊分發 → 並行計算 → 結果聚合 → 報告生成
    ↓           ↓           ↓           ↓           ↓           ↓           ↓
InfluxDB → DataProcessor → Vectorizer → TaskQueue → ProcessPool → Aggregator → ReportGen
```

## 組件設計

### 1. VectorBT多進程引擎

```python
from typing import Dict, List, Optional, Any, Callable, Union
import numpy as np
import pandas as pd
import vectorbt as vbt
from concurrent.futures import ProcessPoolExecutor
import asyncio
from dataclasses import dataclass
from enum import Enum

class VectorBTExecutionMode(Enum):
    """VectorBT執行模式"""
    SINGLE_PROCESS = "single_process"
    MULTI_PROCESS = "multi_process"
    DISTRIBUTED = "distributed"
    HYBRID = "hybrid"  # 混合模式：進程+線程

@dataclass
class VectorBTTask:
    """VectorBT計算任務"""
    task_id: str
    strategy_config: Dict[str, Any]
    data_chunk: pd.DataFrame
    symbols: List[str]
    execution_params: Dict[str, Any]
    result_path: Optional[str] = None

class VectorBTMultiprocessEngine:
    """
    VectorBT多進程引擎
    核心組件：負責協調VectorBT的向量化計算和多進程執行
    """

    def __init__(
        self,
        max_workers: int = None,
        execution_mode: VectorBTExecutionMode = VectorBTExecutionMode.MULTI_PROCESS,
        memory_limit: float = 8.0  # GB
    ):
        self.max_workers = max_workers or min(32, (os.cpu_count() or 1))
        self.execution_mode = execution_mode
        self.memory_limit = memory_limit

        # 初始化執行器
        self.process_pool = None
        self.task_queue = asyncio.Queue()
        self.result_cache = {}

        # 監控組件
        self.resource_monitor = ResourceMonitor()
        self.performance_tracker = PerformanceTracker()

    async def initialize(self):
        """初始化引擎"""
        # 創建進程池
        self.process_pool = ProcessPoolExecutor(
            max_workers=self.max_workers
        )

        # 設置VectorBT全局配置
        await self._configure_vectorbt()

        logger.info(f"VectorBT engine initialized with {self.max_workers} workers")

    async def execute_portfolio_backtest(
        self,
        strategies: List[Dict[str, Any]],
        data: Dict[str, pd.DataFrame],
        optimization_params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        執行投資組合回測
        使用VectorBT的Portfolio.from_signals進行向量化計算
        """
        # 1. 數據向量化準備
        vectorized_data = await self._prepare_vectorized_data(data)

        # 2. 創建信號生成任務
        signal_tasks = await self._create_signal_generation_tasks(
            strategies,
            vectorized_data
        )

        # 3. 並行生成交易信號
        signals = await self._generate_signals_parallel(signal_tasks)

        # 4. 創建投資組合並執行回測
        portfolio_results = await self._execute_portfolio_simulation(
            signals,
            vectorized_data
        )

        # 5. 計算性能指標
        performance_metrics = await self._calculate_performance_metrics(
            portfolio_results
        )

        return {
            'portfolio_results': portfolio_results,
            'performance_metrics': performance_metrics,
            'execution_stats': self.performance_tracker.get_stats()
        }

    async def execute_parameter_optimization(
        self,
        strategy_template: Dict[str, Any],
        param_grid: Dict[str, List[Any]],
        data: pd.DataFrame,
        objective_func: str = 'sharpe_ratio'
    ) -> Dict[str, Any]:
        """
        執行參數優化
        使用VectorBT的並行能力進行網格搜索
        """
        # 1. 生成參數組合
        param_combinations = self._generate_param_combinations(param_grid)

        # 2. 創建優化任務
        optimization_tasks = []
        for i, params in enumerate(param_combinations):
            task = VectorBTTask(
                task_id=f"opt_task_{i}",
                strategy_config={**strategy_template, **params},
                data_chunk=data,
                symbols=[],
                execution_params={'objective': objective_func}
            )
            optimization_tasks.append(task)

        # 3. 批量執行優化
        results = await self._execute_task_batch(optimization_tasks)

        # 4. 排序和選擇最佳參數
        best_results = self._select_best_parameters(
            results,
            objective_func
        )

        return {
            'best_parameters': best_results,
            'all_results': results,
            'optimization_stats': self._calculate_optimization_stats(results)
        }
```

### 2. API接口設計

```python
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from typing import List, Dict, Any, Optional
import asyncio

router = APIRouter(prefix="/api/v2/vectorbt", tags=["VectorBT"])

@router.post("/backtest/submit")
async def submit_vectorbt_backtest(
    request: VectorBTBacktestRequest
) -> Dict[str, str]:
    """
    提交VectorBT回測任務

    支持單策略回測、多策略比較、參數優化等多種模式
    """
    try:
        # 驗證請求
        await validate_backtest_request(request)

        # 創建任務
        task_id = await vectorbt_manager.create_backtest_task(request)

        return {
            "task_id": task_id,
            "status": "submitted",
            "message": "VectorBT backtest task submitted successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/backtest/{task_id}/status")
async def get_backtest_status(
    task_id: str
) -> Dict[str, Any]:
    """獲取回測任務狀態"""
    status = await vectorbt_manager.get_task_status(task_id)
    if not status:
        raise HTTPException(status_code=404, detail="Task not found")
    return status

@router.get("/backtest/{task_id}/results")
async def get_backtest_results(
    task_id: str,
    include_charts: bool = True
) -> Dict[str, Any]:
    """獲取回測結果"""
    results = await vectorbt_manager.get_task_results(task_id)
    if not results:
        raise HTTPException(status_code=404, detail="Results not available")

    # 如果需要圖表，生成VectorBT圖表
    if include_charts:
        results['charts'] = await generate_vectorbt_charts(results)

    return results

@router.post("/backtest/{task_id}/cancel")
async def cancel_backtest(
    task_id: str
) -> Dict[str, str]:
    """取消正在運行的回測任務"""
    success = await vectorbt_manager.cancel_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found or cannot be cancelled")
    return {"message": "Task cancelled successfully"}

@router.websocket("/ws/{task_id}")
async def websocket_backtest_monitor(
    websocket: WebSocket,
    task_id: str
):
    """
    WebSocket實時監控回測進度
    廣播VectorBT計算進度、資源使用情況等
    """
    await websocket.accept()

    try:
        # 訂閱任務更新
        async for update in vectorbt_manager.subscribe_task_updates(task_id):
            await websocket.send_json(update)
    except WebSocketDisconnect:
        # 客戶端斷開連接
        pass
    except Exception as e:
        await websocket.send_json({
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        })
    finally:
        await websocket.close()
```

### 3. WebSocket通知機制

```python
class VectorBTNotificationManager:
    """
    VectorBT實時通知管理器
    處理回測進度、性能指標等實時更新
    """

    def __init__(self):
        self.connections: Dict[str, WebSocket] = {}
        self.subscribers: Dict[str, Set[str]] = {}  # task_id -> connection_ids

    async def register_connection(
        self,
        connection_id: str,
        websocket: WebSocket
    ):
        """註冊WebSocket連接"""
        self.connections[connection_id] = websocket

    async def subscribe_task(
        self,
        connection_id: str,
        task_id: str
    ):
        """訂閱任務更新"""
        if task_id not in self.subscribers:
            self.subscribers[task_id] = set()
        self.subscribers[task_id].add(connection_id)

    async def broadcast_progress_update(
        self,
        task_id: str,
        progress_data: Dict[str, Any]
    ):
        """廣播進度更新"""
        if task_id in self.subscribers:
            message = {
                "type": "progress_update",
                "task_id": task_id,
                "data": progress_data,
                "timestamp": datetime.utcnow().isoformat()
            }

            # 發送給所有訂閱者
            for connection_id in self.subscribers[task_id]:
                if connection_id in self.connections:
                    websocket = self.connections[connection_id]
                    try:
                        await websocket.send_json(message)
                    except:
                        # 連接已斷開，清理
                        await self._cleanup_connection(connection_id)

    async def broadcast_performance_metrics(
        self,
        task_id: str,
        metrics: Dict[str, Any]
    ):
        """廣播性能指標"""
        if task_id in self.subscribers:
            message = {
                "type": "performance_metrics",
                "task_id": task_id,
                "data": {
                    "cpu_usage": metrics.get('cpu_usage'),
                    "memory_usage": metrics.get('memory_usage'),
                    "vectorization_efficiency": metrics.get('vectorization_efficiency'),
                    "throughput": metrics.get('throughput'),
                    "eta": metrics.get('eta')
                },
                "timestamp": datetime.utcnow().isoformat()
            }

            # 廣播給訂閱者
            for connection_id in self.subscribers[task_id]:
                if connection_id in self.connections:
                    websocket = self.connections[connection_id]
                    try:
                        await websocket.send_json(message)
                    except:
                        await self._cleanup_connection(connection_id)
```

### 4. 緩存和存儲策略

```python
class VectorBTCacheManager:
    """
    VectorBT緩存管理器
    優化數據加載和計算結果緩存
    """

    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client
        self.cache_ttl = {
            'market_data': 3600,  # 1小時
            'computed_signals': 1800,  # 30分鐘
            'backtest_results': 86400,  # 24小時
            'optimization_cache': 7200  # 2小時
        }

    async def get_cached_data(
        self,
        cache_key: str,
        data_type: str
    ) -> Optional[pd.DataFrame]:
        """獲取緩存的數據"""
        try:
            cached_data = await self.redis.get(cache_key)
            if cached_data:
                # 反序列化pandas DataFrame
                return pd.read_json(cached_data)
        except Exception as e:
            logger.error(f"Cache retrieval error: {e}")
        return None

    async def cache_data(
        self,
        cache_key: str,
        data: pd.DataFrame,
        data_type: str
    ):
        """緩存數據"""
        try:
            # 序列化pandas DataFrame
            serialized_data = data.to_json()
            ttl = self.cache_ttl.get(data_type, 3600)
            await self.redis.setex(cache_key, ttl, serialized_data)
        except Exception as e:
            logger.error(f"Cache storage error: {e}")

    def generate_cache_key(
        self,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        freq: str = '1d'
    ) -> str:
        """生成緩存鍵"""
        symbol_str = ','.join(sorted(symbols))
        key_data = f"{symbol_str}:{start_date}:{end_date}:{freq}"
        return hashlib.md5(key_data.encode()).hexdigest()
```

## 實現細節

### 1. 關鍵算法和代碼結構

#### VectorBT信號生成器

```python
class VectorBTSignalGenerator:
    """
    VectorBT信號生成器
    利用向量化操作高效生成交易信號
    """

    @staticmethod
    async def generate_signals_vectorized(
        data: pd.DataFrame,
        indicators: Dict[str, Dict[str, Any]]
    ) -> pd.DataFrame:
        """
        向量化生成交易信號
        使用VectorBT的高效向量化操作
        """
        # 計算技術指標
        indicator_results = {}

        for indicator_name, params in indicators.items():
            if indicator_name == 'sma_crossover':
                # 範例：SMA交叉策略
                fast_sma = vbt.MA.run(
                    data['close'],
                    window=params['fast_window']
                )
                slow_sma = vbt.MA.run(
                    data['close'],
                    window=params['slow_window']
                )

                # 生成信號
                entries = fast_sma.ma_crossed_above(slow_sma)
                exits = fast_sma.ma_crossed_below(slow_sma)

                indicator_results['entries'] = entries
                indicator_results['exits'] = exits

            elif indicator_name == 'rsi':
                # RSI策略
                rsi = vbt.RSI.run(
                    data['close'],
                    window=params['window']
                )

                # RSI信號
                entries = rsi.rsi_crossed_below(params['oversold'])
                exits = rsi.rsi_crossed_above(params['overbought'])

                indicator_results['entries'] = entries
                indicator_results['exits'] = exits

        return indicator_results

    @staticmethod
    async def create_portfolio_from_signals(
        entries: pd.DataFrame,
        exits: pd.DataFrame,
        prices: pd.DataFrame,
        init_cash: float = 1000000,
        fees: float = 0.001
    ) -> vbt.Portfolio:
        """
        從信號創建投資組合
        """
        portfolio = vbt.Portfolio.from_signals(
            prices=prices,
            entries=entries,
            exits=exits,
            init_cash=init_cash,
            fees=fees,
            slippage=0.0005
        )

        return portfolio
```

#### 性能優化模塊

```python
class VectorBTOptimizer:
    """
    VectorBT性能優化器
    自動調優參數以獲得最佳性能
    """

    async def auto_optimize_execution(
        self,
        data_size: int,
        num_strategies: int,
        available_memory: float
    ) -> Dict[str, Any]:
        """
        自動優化執行參數
        """
        # 計算最優分塊大小
        optimal_chunk_size = self._calculate_chunk_size(
            data_size,
            available_memory
        )

        # 計算最優並行度
        optimal_workers = self._calculate_optimal_workers(
            data_size,
            num_strategies,
            available_memory
        )

        # 計算內存優化策略
        memory_strategy = self._determine_memory_strategy(
            data_size,
            available_memory
        )

        return {
            'chunk_size': optimal_chunk_size,
            'num_workers': optimal_workers,
            'memory_strategy': memory_strategy,
            'use_memory_mapping': data_size > available_memory * 0.5,
            'prefetch_enabled': True
        }

    def _calculate_chunk_size(
        self,
        data_size: int,
        available_memory: float
    ) -> int:
        """計算最優數據分塊大小"""
        # 每個數據點估計需要100字節（包括索引和多列）
        bytes_per_point = 100
        max_memory_per_chunk = available_memory * 0.2 * 1024 * 1024 * 1024  # 20%內存

        # 計算可以處理的數據點數量
        max_points = int(max_memory_per_chunk / bytes_per_point)

        # 確保至少1000行，最多100萬行
        chunk_size = max(1000, min(1000000, max_points))

        return chunk_size
```

### 2. 配置管理

```python
# config/vectorbt_config.py
from pydantic import BaseSettings, Field
from typing import Optional, List, Dict, Any

class VectorBTConfig(BaseSettings):
    """
    VectorBT配置管理
    統一管理所有VectorBT相關的配置參數
    """

    # 執行配置
    max_workers: int = Field(default=4, description="最大工作進程數")
    default_execution_mode: str = Field(default="multi_process", description="默認執行模式")
    memory_limit_gb: float = Field(default=8.0, description="內存限制(GB)")

    # 數據配置
    default_chunk_size: int = Field(default=10000, description="默認數據塊大小")
    max_cache_size_mb: int = Field(default=1024, description="最大緩存大小(MB)")
    cache_ttl_seconds: int = Field(default=3600, description="緩存TTL(秒)")

    # VectorBT特定配置
    vectorbt_settings: Dict[str, Any] = Field(
        default={
            'freq': '1d',
            'init_cash': 1000000,
            'fees': 0.001,
            'slippage': 0.0005,
            'allow_partial': True,
            'cash_sharing': True
        },
        description="VectorBT默認設置"
    )

    # 優化配置
    enable_auto_optimization: bool = Field(default=True, description="啟用自動優化")
    optimization_objectives: List[str] = Field(
        default=['sharpe_ratio', 'sortino_ratio', 'max_drawdown'],
        description="優化目標列表"
    )

    # 監控配置
    enable_performance_monitoring: bool = Field(default=True, description="啟用性能監控")
    metrics_collection_interval: int = Field(default=5, description="指標收集間隔(秒)")

    # 告警配置
    memory_warning_threshold: float = Field(default=0.8, description="內存警告閾值")
    cpu_warning_threshold: float = Field(default=0.9, description="CPU警告閾值")
    task_timeout_minutes: int = Field(default=60, description="任務超時時間(分鐘)")

    class Config:
        env_prefix = "VBT_"
        env_file = ".env"
```

### 3. 錯誤處理機制

```python
class VectorBTErrorHandler:
    """
    VectorBT錯誤處理器
    統一處理VectorBT相關的異常
    """

    async def handle_vectorbt_error(
        self,
        error: Exception,
        task_id: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        處理VectorBT執行錯誤
        """
        error_type = type(error).__name__

        if isinstance(error, MemoryError):
            return await self._handle_memory_error(task_id, context)
        elif isinstance(error, ValueError) and "insufficient data" in str(error):
            return await self._handle_insufficient_data_error(task_id, context)
        elif isinstance(error, TimeoutError):
            return await self._handle_timeout_error(task_id, context)
        else:
            return await self._handle_generic_error(error, task_id, context)

    async def _handle_memory_error(
        self,
        task_id: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """處理內存不足錯誤"""
        # 減少並行度
        new_workers = max(1, context.get('current_workers', 4) // 2)

        # 建議使用更大的分塊
        new_chunk_size = context.get('current_chunk_size', 10000) * 2

        # 返回恢復建議
        return {
            'error_type': 'memory_error',
            'message': 'Insufficient memory for VectorBT computation',
            'recovery_actions': [
                f'Reduce number of workers to {new_workers}',
                f'Increase chunk size to {new_chunk_size}',
                'Enable memory mapping for large datasets'
            ],
            'auto_recover': True,
            'recovery_params': {
                'num_workers': new_workers,
                'chunk_size': new_chunk_size,
                'use_memory_mapping': True
            }
        }
```

### 4. 性能優化策略

#### 內存優化

```python
class VectorBTMemoryOptimizer:
    """
    VectorBT內存優化器
    優化DataFrame操作和內存使用
    """

    async def optimize_dataframe_memory(
        self,
        df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        優化DataFrame內存使用
        """
        # 降低數值精度
        for col in df.select_dtypes(include=['float64']).columns:
            df[col] = pd.to_numeric(df[col], downcast='float')

        for col in df.select_dtypes(include=['int64']).columns:
            df[col] = pd.to_numeric(df[col], downcast='integer')

        # 使用分類數據類型
        for col in df.select_dtypes(include=['object']).columns:
            if df[col].nunique() / len(df) < 0.5:  # 重複率高
                df[col] = df[col].astype('category')

        return df

    async def implement_lazy_loading(
        self,
        data_path: str,
        chunk_size: int = 100000
    ) -> pd.DataFrame:
        """
        實現懶加載以減少內存使用
        """
        # 使用HDF5或Parquet格式進行分塊加載
        if data_path.endswith('.h5'):
            return pd.read_hdf(data_path, chunksize=chunk_size)
        elif data_path.endswith('.parquet'):
            return pd.read_parquet(data_path, engine='pyarrow')
        else:
            # 對於CSV，實現分塊讀取
            chunks = []
            for chunk in pd.read_csv(data_path, chunksize=chunk_size):
                chunks.append(chunk)
            return pd.concat(chunks, axis=0)
```

#### 計算優化

```python
class VectorBTComputeOptimizer:
    """
    VectorBT計算優化器
    優化向量化計算過程
    """

    def __init__(self):
        self.numba_enabled = True
        self.gpu_available = self._check_gpu_availability()

    async def optimize_indicator_calculation(
        self,
        data: pd.DataFrame,
        indicator_configs: List[Dict[str, Any]]
    ) -> pd.DataFrame:
        """
        優化技術指標計算
        使用向量化操作和緩存
        """
        results = {}

        # 批量計算相似指標
        grouped_configs = self._group_similar_indicators(indicator_configs)

        for group_name, configs in grouped_configs.items():
            if group_name == 'moving_averages':
                # 批量計算移動平均
                windows = [c['window'] for c in configs]
                mas = vbt.MA.run(data['close'], window=windows)

                for i, config in enumerate(configs):
                    results[f"ma_{config['window']}"] = mas.ma[i]

            elif group_name == 'oscillators':
                # 批量計算振盪器
                for config in configs:
                    if config['type'] == 'rsi':
                        rsi = vbt.RSI.run(data['close'], window=config['window'])
                        results[f"rsi_{config['window']}"] = rsi.rsi

        return pd.DataFrame(results)

    def _check_gpu_availability(self) -> bool:
        """檢查GPU是否可用"""
        try:
            import cudf
            return True
        except ImportError:
            return False
```

## 集成指南

### 1. 與現有系統的集成步驟

#### 步驟1：安裝依賴

```bash
# 安裝VectorBT及其依賴
pip install vectorbt[numba,gpu]

# 安裝額外的性能優化庫
pip install numba pandas ta-lib
pip install cupy-cuda11x  # 如果有GPU
```

#### 步驟2：數據庫模式擴展

```sql
-- 擴展現有回測表以支持VectorBT
ALTER TABLE backtest_results
ADD COLUMN vectorbt_config JSONB,
ADD COLUMN vectorbt_performance JSONB,
ADD COLUMN optimization_params JSONB,
ADD COLUMN chunk_strategy VARCHAR(50),
ADD COLUMN vectorization_metrics JSONB;

-- 創建VectorBT特定表
CREATE TABLE vectorbt_optimization_cache (
    id SERIAL PRIMARY KEY,
    strategy_id VARCHAR(100),
    param_hash VARCHAR(64),
    parameters JSONB,
    performance_metrics JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    UNIQUE(strategy_id, param_hash)
);

CREATE INDEX idx_vectorbt_cache_hash ON vectorbt_optimization_cache(param_hash);
```

#### 步驟3：服務集成

```python
# src/services/vectorbt_service.py
from .backtest_service_v2 import BacktestServiceV2
from .vectorbt_engine import VectorBTMultiprocessEngine
from .vectorbt_notification import VectorBTNotificationManager

class IntegratedBacktestService:
    """
    集成的回測服務
    統一管理傳統回測和VectorBT回測
    """

    def __init__(self):
        # 初始化傳統回測引擎
        self.traditional_engine = BacktestServiceV2()

        # 初始化VectorBT引擎
        self.vectorbt_engine = VectorBTMultiprocessEngine()

        # 初始化通知管理器
        self.notification_manager = VectorBTNotificationManager()

        # 路由策略
        self.execution_router = ExecutionRouter()

    async def execute_backtest(
        self,
        request: BacktestRequest
    ) -> BacktestResult:
        """
        智能路由到最適合的引擎
        """
        # 根據請求特點選擇引擎
        engine_type = await self.execution_router.select_engine(
            request
        )

        if engine_type == 'vectorbt':
            # 使用VectorBT引擎
            return await self.vectorbt_engine.execute(request)
        else:
            # 使用傳統引擎
            return await self.traditional_engine.execute(request)
```

### 2. 部署配置

#### Docker配置

```dockerfile
# docker/vectorbt.dockerfile
FROM python:3.9-slim

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    build-essential \
    libhdf5-dev \
    libta-lib-dev \
    && rm -rf /var/lib/apt/lists/*

# 安裝Python依賴
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 設置工作目錄
WORKDIR /app

# 複製代碼
COPY . .

# 設置環境變量
ENV PYTHONPATH=/app
ENV VBT_MAX_WORKERS=8
ENV VBT_MEMORY_LIMIT=16.0

# 暴露端口
EXPOSE 8000

# 啟動命令
CMD ["python", "-m", "src.main"]
```

#### Kubernetes配置

```yaml
# k8s/deployments/vectorbt-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vectorbt-backtest
  labels:
    app: vectorbt-backtest
spec:
  replicas: 3
  selector:
    matchLabels:
      app: vectorbt-backtest
  template:
    metadata:
      labels:
        app: vectorbt-backtest
    spec:
      containers:
      - name: vectorbt-engine
        image: cbsc/vectorbt:latest
        resources:
          requests:
            memory: "4Gi"
            cpu: "2"
          limits:
            memory: "16Gi"
            cpu: "8"
        env:
        - name: VBT_MAX_WORKERS
          value: "8"
        - name: VBT_MEMORY_LIMIT
          value: "16.0"
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: redis-url
```

### 3. 監控和告警

#### Prometheus指標

```python
# src/metrics/vectorbt_metrics.py
from prometheus_client import Counter, Histogram, Gauge

# 定義VectorBT特定的指標
vectorbt_backtest_requests = Counter(
    'vectorbt_backtest_requests_total',
    'Total number of VectorBT backtest requests',
    ['strategy_type', 'execution_mode']
)

vectorbt_execution_duration = Histogram(
    'vectorbt_execution_duration_seconds',
    'VectorBT backtest execution duration',
    ['task_type'],
    buckets=[0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0, 300.0]
)

vectorbt_memory_usage = Gauge(
    'vectorbt_memory_usage_bytes',
    'Current memory usage by VectorBT engine'
)

vectorbt_cpu_usage = Gauge(
    'vectorbt_cpu_usage_percent',
    'Current CPU usage by VectorBT engine'
)

vectorbt_active_tasks = Gauge(
    'vectorbt_active_tasks',
    'Number of active VectorBT tasks'
)
```

#### Grafana儀表板

```json
{
  "dashboard": {
    "title": "VectorBT Performance Dashboard",
    "panels": [
      {
        "title": "Backtest Execution Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(vectorbt_execution_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "title": "Active Tasks",
        "type": "stat",
        "targets": [
          {
            "expr": "vectorbt_active_tasks",
            "legendFormat": "Active"
          }
        ]
      },
      {
        "title": "Resource Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "vectorbt_memory_usage_bytes / 1024 / 1024",
            "legendFormat": "Memory (MB)"
          },
          {
            "expr": "vectorbt_cpu_usage_percent",
            "legendFormat": "CPU (%)"
          }
        ]
      }
    ]
  }
}
```

### 4. 測試策略

#### 單元測試

```python
# tests/vectorbt/test_engine.py
import pytest
import pandas as pd
import numpy as np
from src.backtest.vectorbt_engine import VectorBTMultiprocessEngine

@pytest.fixture
def sample_data():
    """創建測試數據"""
    dates = pd.date_range('2023-01-01', '2023-12-31', freq='D')
    np.random.seed(42)
    prices = 100 * np.cumprod(1 + np.random.normal(0.0005, 0.02, len(dates)))

    return pd.DataFrame({
        'open': prices,
        'high': prices * 1.01,
        'low': prices * 0.99,
        'close': prices,
        'volume': np.random.randint(1000000, 5000000, len(dates))
    }, index=dates)

@pytest.mark.asyncio
async def test_vectorbt_sma_strategy(sample_data):
    """測試VectorBT SMA策略"""
    engine = VectorBTMultiprocessEngine()
    await engine.initialize()

    strategy_config = {
        'type': 'sma_crossover',
        'fast_window': 10,
        'slow_window': 30
    }

    result = await engine.execute_backtest(
        strategy_config,
        sample_data
    )

    assert result is not None
    assert 'portfolio' in result
    assert 'performance' in result
    assert result['performance']['total_return'] > 0

@pytest.mark.asyncio
async def test_parameter_optimization(sample_data):
    """測試參數優化"""
    engine = VectorBTMultiprocessEngine()
    await engine.initialize()

    param_grid = {
        'fast_window': [5, 10, 15],
        'slow_window': [20, 30, 40]
    }

    result = await engine.execute_parameter_optimization(
        {'type': 'sma_crossover'},
        param_grid,
        sample_data
    )

    assert 'best_parameters' in result
    assert len(result['best_parameters']) == 2
    assert result['optimization_stats']['total_combinations'] == 9
```

#### 性能基準測試

```python
# tests/vectorbt/test_performance.py
import time
import psutil
from src.benchmarks.vectorbt_benchmarks import VectorBTBenchmarks

async def benchmark_parallel_vs_sequential():
    """基準測試：並行 vs 順序執行"""
    benchmark = VectorBTBenchmarks()

    # 準備測試數據
    test_data = await benchmark.generate_test_data(
        symbols=['AAPL', 'GOOGL', 'MSFT'],
        years=5
    )

    # 測試順序執行
    start_time = time.time()
    sequential_results = await benchmark.run_sequential(test_data)
    sequential_time = time.time() - start_time

    # 測試並行執行
    start_time = time.time()
    parallel_results = await benchmark.run_parallel(test_data)
    parallel_time = time.time() - start_time

    # 計算加速比
    speedup = sequential_time / parallel_time

    print(f"Sequential time: {sequential_time:.2f}s")
    print(f"Parallel time: {parallel_time:.2f}s")
    print(f"Speedup: {speedup:.2f}x")

    # 驗證結果一致性
    assert benchmark.compare_results(sequential_results, parallel_results)

    return {
        'sequential_time': sequential_time,
        'parallel_time': parallel_time,
        'speedup': speedup
    }
```

## 代碼示例

### 1. VectorBT策略示例

```python
# examples/vectorbt_momentum_strategy.py
"""
使用VectorBT實現動量策略示例
展示向量化回測的強大功能
"""

import vectorbt as vbt
import pandas as pd
import numpy as np
from typing import Dict, List, Any

class VectorBTMomentumStrategy:
    """
    VectorBT動量策略實現
    利用向量化操作高效執行動量策略回測
    """

    def __init__(self, lookback_period: int = 20):
        self.lookback_period = lookback_period

    def calculate_momentum_signals(
        self,
        price_data: pd.DataFrame
    ) -> pd.DataFrame:
        """
        計算動量信號
        使用向量化操作提高效率
        """
        # 計算過去N天的收益率
        returns = price_data.pct_change(self.lookback_period)

        # 創建排名信號（排名前30%的股票）
        signals = vbt.signals.factory(
            entries_func=lambda X: X.rank(axis=1) <= X.shape[1] * 0.3,
            exits_func=lambda X: X.rank(axis=1) >= X.shape[1] * 0.7
        )

        return signals.generate(returns)

    def execute_backtest(
        self,
        price_data: pd.DataFrame,
        init_cash: float = 1000000
    ) -> vbt.Portfolio:
        """
        執行回測
        """
        # 生成交易信號
        signals = self.calculate_momentum_signals(price_data)

        # 創建投資組合
        portfolio = vbt.Portfolio.from_signals(
            price_data['close'],
            entries=signals.entries,
            exits=signals.exits,
            init_cash=init_cash,
            fees=0.001,
            slippage=0.0005,
            cash_sharing=True,
            allow_partial=True
        )

        return portfolio

    def analyze_performance(
        self,
        portfolio: vbt.Portfolio
    ) -> Dict[str, Any]:
        """
        分析性能指標
        """
        stats = portfolio.stats()

        return {
            'total_return': stats['Total Return [%]'],
            'annual_return': stats['Annual Return [%]'],
            'sharpe_ratio': stats['Sharpe Ratio'],
            'max_drawdown': stats['Max Drawdown [%]'],
            'win_rate': stats['Win Rate [%]'],
            'profit_factor': stats['Profit Factor'],
            'total_trades': stats['# Trades']
        }

# 使用示例
async def run_momentum_strategy_example():
    """
    運行動量策略示例
    """
    # 載入數據
    price_data = pd.read_csv('data/stock_prices.csv', index_col=0, parse_dates=True)

    # 創建策略
    strategy = VectorBTMomentumStrategy(lookback_period=20)

    # 執行回測
    portfolio = strategy.execute_backtest(price_data)

    # 分析結果
    performance = strategy.analyze_performance(portfolio)

    print("策略性能指標:")
    for metric, value in performance.items():
        print(f"{metric}: {value:.2f}")

    # 生成圖表
    portfolio.plot().show()

    return portfolio, performance

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_momentum_strategy_example())
```

### 2. 多進程回測示例

```python
# examples/vectorbt_multiprocess_example.py
"""
VectorBT多進程回測示例
展示如何利用多進程加速策略回測
"""

import asyncio
import pandas as pd
import time
from concurrent.futures import ProcessPoolExecutor
from src.backtest.vectorbt_engine import VectorBTMultiprocessEngine
from src.strategies.enhanced_factory_v2 import StrategyFactoryV2

async def run_multiprocess_backtest():
    """
    運行多進程回測示例
    """
    # 初始化引擎
    engine = VectorBTMultiprocessEngine(
        max_workers=8,
        memory_limit=16.0
    )
    await engine.initialize()

    # 載入數據
    symbols = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'FB']
    data = {}
    for symbol in symbols:
        data[symbol] = pd.read_csv(
            f'data/{symbol}_daily.csv',
            index_col=0,
            parse_dates=True
        )

    # 定義多個策略
    strategies = [
        {
            'name': 'SMA_Crossover_5_20',
            'type': 'sma_crossover',
            'fast_window': 5,
            'slow_window': 20
        },
        {
            'name': 'SMA_Crossover_10_30',
            'type': 'sma_crossover',
            'fast_window': 10,
            'slow_window': 30
        },
        {
            'name': 'RSI_Mean_Reversion',
            'type': 'rsi',
            'window': 14,
            'oversold': 30,
            'overbought': 70
        },
        {
            'name': 'Momentum_20',
            'type': 'momentum',
            'lookback': 20
        }
    ]

    # 執行並行回測
    print("開始並行回測...")
    start_time = time.time()

    results = await engine.execute_batch_backtest(
        strategies=strategies,
        data=data,
        mode='multiprocess'
    )

    execution_time = time.time() - start_time

    # 輸出結果
    print(f"\n並行回測完成，耗時: {execution_time:.2f}秒")
    print("\n策略對比:")

    for strategy_name, result in results.items():
        print(f"\n{strategy_name}:")
        print(f"  總回報: {result['total_return']:.2%}")
        print(f"  夏普比率: {result['sharpe_ratio']:.2f}")
        print(f"  最大回撤: {result['max_drawdown']:.2%}")
        print(f"  總交易次數: {result['total_trades']}")

    return results

if __name__ == "__main__":
    results = asyncio.run(run_multiprocess_backtest())
```

### 3. 最佳實踐指南

```python
# best_practices/vectorbt_best_practices.py
"""
VectorBT最佳實踐指南
提供高效的VectorBT使用模式和性能優化技巧
"""

class VectorBTBestPractices:
    """
    VectorBT最佳實踐集合
    """

    @staticmethod
    def data_preparation_tips():
        """
        數據準備最佳實踐
        """
        tips = {
            'use_datetime_index': "確保數據使用datetime類型的索引",
            'handle_missing_data': "處理缺失數據，避免NaN值影響計算",
            'optimize_dtypes': "使用適當的數據類型減少內存使用",
            'precompute_indicators': "預計算常用指標以避免重複計算",
            'cache_frequent_data': "緩存頻繁使用的數據"
        }
        return tips

    @staticmethod
    def performance_optimization_tips():
        """
        性能優化最佳實踐
        """
        tips = {
            'use_numba': "啟用Numba加速向量化操作",
            'batch_operations': "批量處理操作而非逐個處理",
            'avoid_loops': "盡量避免在pandas中使用循環",
            'vectorize_everything': "將所有操作向量化",
            'chunk_large_data': "對大數據集進行分塊處理",
            'use_gpu': "對大規模計算使用GPU加速"
        }
        return tips

    @staticmethod
    def memory_management_tips():
        """
        內存管理最佳實踐
        """
        tips = {
            'release_unused': "及時釋放不需要的變量",
            'use_generators': "使用生成器處理大量數據",
            'monitor_usage': "監控內存使用情況",
            'clear_cache': "定期清理緩存",
            'use_sparse': "對稀疏數據使用稀疏矩陣"
        }
        return tips

# 實用工具函數
def create_optimized_dataframe(
    data: Dict[str, List],
    index: pd.DatetimeIndex
) -> pd.DataFrame:
    """
    創建優化的DataFrame
    """
    df = pd.DataFrame(data, index=index)

    # 優化數據類型
    for col in df.select_dtypes(include=['float64']).columns:
        df[col] = pd.to_numeric(df[col], downcast='float')

    for col in df.select_dtypes(include=['int64']).columns:
        df[col] = pd.to_numeric(df[col], downcast='integer')

    return df

def implement_rolling_window_optimization(
    data: pd.DataFrame,
    window_size: int,
    func: callable
) -> pd.DataFrame:
    """
    實現滾動窗口優化
    """
    # 使用Numba加速滾動計算
    from numba import jit

    @jit(nopython=True)
    def rolling_calc_numba(values, window):
        result = np.empty(len(values))
        for i in range(window - 1, len(values)):
            result[i] = func(values[i - window + 1:i + 1])
        return result

    return data.apply(rolling_calc_numba, window=window_size)
```

## 總結

本設計文檔提供了VectorBT多進程回測集成的完整技術架構和實現細節。通過VectorBT的向量化計算能力和多進程並行處理，可以顯著提升回測執行效率，支持大規模策略並行回測。

關鍵優勢：
1. **高性能向量化計算**：利用VectorBT的向量化操作大幅提升計算速度
2. **智能多進程管理**：自動管理進程池和資源分配
3. **靈活的擴展性**：支持從單機到分布式的無縫擴展
4. **完整的監控體系**：實時監控性能指標和資源使用
5. **與現有系統兼容**：平滑集成到CBSC現有架構中

通過遵循本設計文檔的實現方案，可以構建一個高效、可靠、可擴展的VectorBT多進程回測系統。