# VectorBT多進程回測集成 - 實施計劃

## 技術架構設計

### 核心組件架構

```
┌─────────────────────────────────────────────────────┐
│                 Frontend Dashboard                   │
│              (React + TypeScript)                    │
└───────────────────┬─────────────────────────────────┘
                    │ HTTP/WebSocket
                    ▼
┌─────────────────────────────────────────────────────┐
│               Backtest API Gateway                   │
│                 (FastAPI)                            │
├───────────────────┬─────────────────────────────────┤
│                   │                                     │
│                   ▼                                     │
│  ┌─────────────────────────────┐                      │
│  │    Task Queue Manager       │                      │
│  │        (Redis)              │                      │
│  └─────────────────┬───────────┘                      │
│                    │                                 │
│                    ▼                                 │
│  ┌─────────────────────────────┐                      │
│  │   VectorBT Adapter Layer    │                      │
│  └─────────────────┬───────────┘                      │
│                    │                                 │
│                    ▼                                 │
│  ┌─────────────────────────────┐                      │
│  │  Parallel Processing Pool   │                      │
│  │   (ProcessPoolExecutor)     │                      │
│  └─────────────────┬───────────┘                      │
│                    │                                 │
└────────────────────┼─────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│                Storage Layer                        │
│  PostgreSQL │ InfluxDB │ Redis │ File System        │
└─────────────────────────────────────────────────────┘
```

## 詳細實施指南

### 1. VectorBT適配器實現

#### 文件結構
```
src/backtest/
├── vectorbt_adapter.py          # 核心適配器
├── vectorbt_utils.py            # 工具函數
├── vectorbt_indicators.py       # 向量化指標
└── vectorbt_strategies.py       # 策略模板
```

#### 核心適配器實現示例

```python
# src/backtest/vectorbt_adapter.py
import vectorbt as vbt
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor
import asyncio

@dataclass
class VectorBTConfig:
    """VectorBT配置參數"""
    init_capital: float = 1000000
    commission: float = 0.001
    slippage: float = 0.0005
    freq: str = '1D'
    cash_sharing: bool = True
    call_seq: str = 'auto'
    segment_reps: int = 1

class VectorBTAdapter:
    """VectorBT適配器主類"""

    def __init__(self, config: VectorBTConfig):
        self.config = config
        self.data = None
        self.portfolio = None

    def load_data(self, price_data: pd.DataFrame) -> 'VectorBTAdapter':
        """
        加載價格數據

        Args:
            price_data: DataFrame with columns ['open', 'high', 'low', 'close', 'volume']

        Returns:
            Self for chaining
        """
        # 轉換為VectorBT格式
        self.data = vbt.Data.from_data(price_data)
        return self

    def run_backtest(
        self,
        entries: pd.DataFrame,
        exits: pd.DataFrame,
        **kwargs
    ) -> Dict[str, Any]:
        """
        執行回測

        Args:
            entries: 進場信號矩陣
            exits: 出場信號矩陣
            **kwargs: 其他VectorBT參數

        Returns:
            回測結果字典
        """
        # 創建投資組合
        self.portfolio = vbt.Portfolio.from_signals(
            self.data.close,
            entries,
            exits,
            init_cash=self.config.init_capital,
            fees=self.config.commission,
            slippage=self.config.slippage,
            freq=self.config.freq,
            cash_sharing=self.config.cash_sharing,
            call_seq=self.config.call_seq
        )

        # 計算統計指標
        stats = self.portfolio.stats()

        return {
            'total_return': self.portfolio.total_return(),
            'sharpe_ratio': self.portfolio.sharpe_ratio(),
            'max_drawdown': self.portfolio.max_drawdown(),
            'win_rate': self.portfolio.trades.win_rate(),
            'profit_factor': self.portfolio.trades.profit_factor(),
            'total_trades': len(self.portfolio.trades),
            'equity_curve': self.portfolio.value(),
            'positions': self.portfolio.positions,
            'trades': self.portfolio.trades.records_readable,
            'detailed_stats': stats
        }

    @staticmethod
    def parallel_backtest_worker(
        task_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        並行回測工作進程

        Args:
            task_data: 包含數據和參數的字典

        Returns:
            回測結果
        """
        try:
            # 解包任務數據
            data = task_data['data']
            config = VectorBTConfig(**task_data['config'])
            entries = task_data['entries']
            exits = task_data['exits']
            task_id = task_data['task_id']

            # 創建適配器並運行回測
            adapter = VectorBTAdapter(config)
            adapter.load_data(data)
            result = adapter.run_backtest(entries, exits)
            result['task_id'] = task_id

            return result

        except Exception as e:
            return {
                'task_id': task_data.get('task_id', 'unknown'),
                'error': str(e),
                'status': 'failed'
            }
```

### 2. 並行處理增強

#### 數據分片策略

```python
# src/backtest/vectorbt_sharding.py
import pandas as pd
import numpy as np
from typing import List, Tuple, Dict, Any
from datetime import datetime, timedelta

class DataSharder:
    """數據分片管理器"""

    @staticmethod
    def time_based_shard(
        data: pd.DataFrame,
        num_shards: int
    ) -> List[pd.DataFrame]:
        """
        基於時間窗口分片

        Args:
            data: 原始數據
            num_shards: 分片數量

        Returns:
            分片後的數據列表
        """
        if len(data) < num_shards:
            return [data]

        shard_size = len(data) // num_shards
        shards = []

        for i in range(num_shards):
            start_idx = i * shard_size
            end_idx = (i + 1) * shard_size if i < num_shards - 1 else len(data)
            shards.append(data.iloc[start_idx:end_idx])

        return shards

    @staticmethod
    def asset_based_shard(
        data: pd.DataFrame,
        symbols: List[str],
        num_shards: int
    ) -> List[pd.DataFrame]:
        """
        基於資產分片

        Args:
            data: 多資產數據 (MultiIndex DataFrame)
            symbols: 資產列表
            num_shards: 分片數量

        Returns:
            分片後的數據列表
        """
        symbols_per_shard = len(symbols) // num_shards
        shards = []

        for i in range(num_shards):
            start_idx = i * symbols_per_shard
            end_idx = (i + 1) * symbols_per_shard if i < num_shards - 1 else len(symbols)
            shard_symbols = symbols[start_idx:end_idx]
            shards.append(data.loc[:, pd.IndexSlice[shard_symbols, :]])

        return shards
```

### 3. 向量化策略模板

#### 技術指標向量化

```python
# src/backtest/vectorbt_indicators.py
import vectorbt as vbt
import pandas as pd
import numpy as np
from typing import Optional, Tuple, Dict, Any

class VectorBTIndicators:
    """向量化技術指標庫"""

    @staticmethod
    def moving_average_crossover(
        data: pd.DataFrame,
        fast_window: int = 20,
        slow_window: int = 50
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        移動平均線交叉策略

        Args:
            data: 價格數據
            fast_window: 快線窗口
            slow_window: 慢線窗口

        Returns:
            (進場信號, 出場信號)
        """
        # 計算移動平均線
        fast_ma = vbt.MA.run(data.close, window=fast_window)
        slow_ma = vbt.MA.run(data.close, window=slow_window)

        # 生成信號
        entries = fast_ma.ma_crossed_above(slow_ma.ma)
        exits = fast_ma.ma_crossed_below(slow_ma.ma)

        return entries, exits

    @staticmethod
    def rsi_strategy(
        data: pd.DataFrame,
        rsi_window: int = 14,
        oversold: float = 30,
        overbought: float = 70
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        RSI策略

        Args:
            data: 價格數據
            rsi_window: RSI窗口
            oversold: 超賣線
            overbought: 超買線

        Returns:
            (進場信號, 出場信號)
        """
        # 計算RSI
        rsi = vbt.RSI.run(data.close, window=rsi_window)

        # 生成信號
        entries = rsi.rsi_crossed_below(oversold)
        exits = rsi.rsi_crossed_above(overbought)

        return entries, exits

    @staticmethod
    def bollinger_bands(
        data: pd.DataFrame,
        window: int = 20,
        num_std: float = 2.0
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        布林帶策略

        Args:
            data: 價格數據
            window: 窗口大小
            num_std: 標準差倍數

        Returns:
            (進場信號, 出場信號)
        """
        # 計算布林帶
        bb = vbt.BBANDS.run(data.close, window=window, num_std=num_std)

        # 生成信號
        entries = data.close_crossed_below(bb.lower)
        exits = data.close_crossed_above(bb.upper)

        return entries, exits
```

### 4. API集成

#### FastAPI端點實現

```python
# src/api/vectorbt_endpoints.py
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import asyncio
from datetime import datetime

from ..backtest.vectorbt_adapter import VectorBTAdapter, VectorBTConfig
from ..backtest.parallel_processor import ParallelProcessor
from ..backtest.vectorbt_sharding import DataSharder

router = APIRouter(prefix="/api/v2/vectorbt", tags=["vectorbt"])

class VectorBTRequest(BaseModel):
    """VectorBT回測請求模型"""
    symbols: List[str]
    start_date: str
    end_date: str
    strategy_type: str  # 'ma_cross', 'rsi', 'bbands', 'custom'
    strategy_params: Dict[str, Any] = {}
    initial_capital: float = 1000000
    commission: float = 0.001
    slippage: float = 0.0005
    enable_parallel: bool = True
    num_processes: Optional[int] = None
    chunk_size: Optional[int] = None

class VectorBTResponse(BaseModel):
    """VectorBT回測響應模型"""
    task_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None

@router.post("/backtest", response_model=VectorBTResponse)
async def run_vectorbt_backtest(
    request: VectorBTRequest,
    background_tasks: BackgroundTasks
):
    """
    執行VectorBT回測

    Args:
        request: 回測請求
        background_tasks: 後台任務

    Returns:
        任務ID和狀態
    """
    try:
        # 生成任務ID
        task_id = f"vbt_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(str(request))}"

        # 獲取數據
        data = await get_market_data(
            symbols=request.symbols,
            start_date=request.start_date,
            end_date=request.end_date
        )

        # 創建配置
        config = VectorBTConfig(
            init_capital=request.initial_capital,
            commission=request.commission,
            slippage=request.slippage
        )

        # 生成信號
        if request.strategy_type == 'ma_cross':
            entries, exits = VectorBTIndicators.moving_average_crossover(
                data, **request.strategy_params
            )
        elif request.strategy_type == 'rsi':
            entries, exits = VectorBTIndicators.rsi_strategy(
                data, **request.strategy_params
            )
        # ... 其他策略

        # 提交到後台任務
        if request.enable_parallel and len(data) > 10000:
            background_tasks.add_task(
                run_parallel_backtest,
                task_id,
                data,
                config,
                entries,
                exits,
                request.num_processes,
                request.chunk_size
            )
        else:
            background_tasks.add_task(
                run_single_backtest,
                task_id,
                data,
                config,
                entries,
                exits
            )

        return VectorBTResponse(
            task_id=task_id,
            status="submitted"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def run_parallel_backtest(
    task_id: str,
    data: pd.DataFrame,
    config: VectorBTConfig,
    entries: pd.DataFrame,
    exits: pd.DataFrame,
    num_processes: Optional[int],
    chunk_size: Optional[int]
):
    """執行並行回測"""
    try:
        # 初始化並行處理器
        processor = ParallelProcessor(
            max_workers=num_processes or mp.cpu_count(),
            execution_mode="process"
        )

        # 數據分片
        shards = DataSharder.time_based_shard(
            data,
            num_shards=processor.max_workers
        )

        # 創建任務列表
        tasks = []
        for i, shard in enumerate(shards):
            task_data = {
                'task_id': f"{task_id}_shard_{i}",
                'data': shard,
                'config': config.__dict__,
                'entries': entries.iloc[shard.index],
                'exits': exits.iloc[shard.index]
            }
            tasks.append(task_data)

        # 並行執行
        results = await processor.process_batch([
            (task['task_id'], VectorBTAdapter.parallel_backtest_worker, (task,), {})
            for task in tasks
        ])

        # 聚合結果
        aggregated_result = aggregate_results(results)

        # 保存結果
        await save_backtest_result(task_id, aggregated_result)

    except Exception as e:
        await save_backtest_result(task_id, {'error': str(e), 'status': 'failed'})
```

### 5. 前端集成

#### React組件更新

```typescript
// frontend/src/components/VectorBTBacktest.tsx
import React, { useState, useEffect } from 'react';
import { Card, Button, Select, DatePicker, InputNumber, Spin } from 'antd';
import { Line } from '@ant-design/plots';
import axios from 'axios';

interface VectorBTConfig {
  symbols: string[];
  startDate: string;
  endDate: string;
  strategyType: string;
  strategyParams: Record<string, any>;
  initialCapital: number;
  commission: number;
  slippage: number;
  enableParallel: boolean;
}

export const VectorBTBacktest: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [result, setResult] = useState<any>(null);
  const [progress, setProgress] = useState(0);

  const [config, setConfig] = useState<VectorBTConfig>({
    symbols: ['AAPL', 'GOOGL', 'MSFT'],
    startDate: '2023-01-01',
    endDate: '2023-12-31',
    strategyType: 'ma_cross',
    strategyParams: { fast_window: 20, slow_window: 50 },
    initialCapital: 1000000,
    commission: 0.001,
    slippage: 0.0005,
    enableParallel: true
  });

  const runBacktest = async () => {
    setLoading(true);
    setProgress(0);

    try {
      // 提交回測任務
      const response = await axios.post('/api/v2/vectorbt/backtest', config);
      const newTaskId = response.data.task_id;
      setTaskId(newTaskId);

      // 輪詢任務狀態
      const pollInterval = setInterval(async () => {
        const statusResponse = await axios.get(`/api/v2/vectorbt/status/${newTaskId}`);

        if (statusResponse.data.status === 'completed') {
          clearInterval(pollInterval);
          const resultResponse = await axios.get(`/api/v2/vectorbt/result/${newTaskId}`);
          setResult(resultResponse.data);
          setLoading(false);
        } else if (statusResponse.data.status === 'failed') {
          clearInterval(pollInterval);
          console.error('Backtest failed:', statusResponse.data.error);
          setLoading(false);
        } else {
          setProgress(statusResponse.data.progress || 0);
        }
      }, 1000);

    } catch (error) {
      console.error('Error running backtest:', error);
      setLoading(false);
    }
  };

  const renderEquityCurve = () => {
    if (!result?.equity_curve) return null;

    const data = result.equity_curve.map((value: number, index: number) => ({
      date: index,
      value
    }));

    const config = {
      data,
      xField: 'date',
      yField: 'value',
      smooth: true,
      animation: {
        appear: {
          animation: 'path-in',
          duration: 1000,
        },
      },
    };

    return <Line {...config} />;
  };

  return (
    <div className="vectorbt-backtest">
      <Card title="VectorBT 回測配置">
        <div className="config-form">
          <div className="form-item">
            <label>股票代碼:</label>
            <Select
              mode="multiple"
              value={config.symbols}
              onChange={(symbols) => setConfig({...config, symbols})}
              style={{ width: '100%' }}
            >
              <Select.Option value="AAPL">AAPL</Select.Option>
              <Select.Option value="GOOGL">GOOGL</Select.Option>
              <Select.Option value="MSFT">MSFT</Select.Option>
              <Select.Option value="TSLA">TSLA</Select.Option>
            </Select>
          </div>

          <div className="form-item">
            <label>策略類型:</label>
            <Select
              value={config.strategyType}
              onChange={(strategyType) => setConfig({...config, strategyType})}
            >
              <Select.Option value="ma_cross">移動平均線交叉</Select.Option>
              <Select.Option value="rsi">RSI策略</Select.Option>
              <Select.Option value="bbands">布林帶</Select.Option>
            </Select>
          </div>

          <div className="form-item">
            <label>初始資金:</label>
            <InputNumber
              value={config.initialCapital}
              onChange={(value) => setConfig({...config, initialCapital: value || 1000000})}
              formatter={value => `$ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
            />
          </div>

          <div className="form-item">
            <label>
              <input
                type="checkbox"
                checked={config.enableParallel}
                onChange={(e) => setConfig({...config, enableParallel: e.target.checked})}
              />
              啟用並行處理
            </label>
          </div>

          <Button
            type="primary"
            onClick={runBacktest}
            loading={loading}
            disabled={loading}
          >
            {loading ? '執行中...' : '運行回測'}
          </Button>
        </div>
      </Card>

      {loading && (
        <Card title="執行進度">
          <Spin size="large" />
          <div className="progress-text">進度: {progress.toFixed(1)}%</div>
        </Card>
      )}

      {result && (
        <Card title="回測結果">
          <div className="result-summary">
            <div>總收益率: {(result.total_return * 100).toFixed(2)}%</div>
            <div>夏普比率: {result.sharpe_ratio.toFixed(2)}</div>
            <div>最大回撤: {(result.max_drawdown * 100).toFixed(2)}%</div>
            <div>勝率: {(result.win_rate * 100).toFixed(2)}%</div>
            <div>總交易次數: {result.total_trades}</div>
          </div>

          <div className="equity-curve">
            <h3>資金曲線</h3>
            {renderEquityCurve()}
          </div>
        </Card>
      )}
    </div>
  );
};
```

### 6. 性能優化建議

#### 內存優化

```python
# src/backtest/memory_optimizer.py
import gc
import psutil
from typing import Any, Generator
import numpy as np

class MemoryOptimizer:
    """內存優化工具"""

    @staticmethod
    def optimize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """
        優化DataFrame內存使用

        Args:
            df: 輸入DataFrame

        Returns:
            優化後的DataFrame
        """
        for col in df.columns:
            col_type = df[col].dtype

            if col_type == 'float64':
                df[col] = df[col].astype('float32')
            elif col_type == 'int64':
                df[col] = pd.to_numeric(df[col], downcast='integer')
            elif col_type == 'object':
                if df[col].nunique() < len(df) * 0.5:
                    df[col] = df[col].astype('category')

        return df

    @staticmethod
    def chunk_generator(
        data: Any,
        chunk_size: int
    ) -> Generator[Any, None, None]:
        """
        生成數據塊以減少內存使用

        Args:
            data: 輸入數據
            chunk_size: 塊大小

        Yields:
            數據塊
        """
        for i in range(0, len(data), chunk_size):
            yield data[i:i + chunk_size]

    @staticmethod
    def monitor_memory() -> dict:
        """監控內存使用情況"""
        process = psutil.Process()
        memory_info = process.memory_info()

        return {
            'rss': memory_info.rss / 1024 / 1024,  # MB
            'vms': memory_info.vms / 1024 / 1024,  # MB
            'percent': process.memory_percent()
        }
```

### 7. 監控和日誌

#### 性能監控裝飾器

```python
# src/utils/performance_monitor.py
import time
import functools
from typing import Callable, Any
import logging

logger = logging.getLogger(__name__)

def monitor_performance(func: Callable) -> Callable:
    """
    性能監控裝飾器

    Args:
        func: 要監控的函數

    Returns:
        包裝後的函數
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss

        try:
            result = func(*args, **kwargs)
            success = True
            error = None
        except Exception as e:
            result = None
            success = False
            error = str(e)
            raise
        finally:
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss

            # 記錄性能指標
            metrics = {
                'function': func.__name__,
                'duration': end_time - start_time,
                'memory_delta': (end_memory - start_memory) / 1024 / 1024,  # MB
                'success': success,
                'error': error
            }

            logger.info(f"Performance metrics: {metrics}")

        return result

    return wrapper
```

## 部署指南

### 1. 環境準備

```bash
# 安裝依賴
pip install vectorbt-pro
pip install rapids-cudf  # GPU加速（可選）
pip install redis
pip install psycopg2-binary

# 設置環境變量
export VECTORBT_LICENSE_KEY="your_license_key"
export REDIS_URL="redis://localhost:6379"
export DATABASE_URL="postgresql://user:pass@localhost/backtest"
```

### 2. Docker部署

```dockerfile
# Dockerfile.vectorbt
FROM python:3.9-slim

WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 安裝Python依賴
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製源代碼
COPY src/ ./src/

# 設置環境
ENV PYTHONPATH=/app
ENV VECTORBT_PRO_LICENSE=${VECTORBT_LICENSE_KEY}

# 暴露端口
EXPOSE 8002

# 啟動命令
CMD ["python", "-m", "uvicorn", "src.api.backtest_service:app", "--host", "0.0.0.0", "--port", "8002"]
```

### 3. Kubernetes部署

```yaml
# k8s/vectorbt-deployment.yaml
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
      - name: vectorbt-backtest
        image: cbsc/vectorbt-backtest:latest
        ports:
        - containerPort: 8002
        env:
        - name: REDIS_URL
          value: "redis://redis-service:6379"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "8Gi"
            cpu: "4000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8002
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8002
          initialDelaySeconds: 5
          periodSeconds: 5
```

## 測試策略

### 1. 單元測試

```python
# tests/test_vectorbt_adapter.py
import pytest
import pandas as pd
import numpy as np
from src.backtest.vectorbt_adapter import VectorBTAdapter, VectorBTConfig

@pytest.fixture
def sample_data():
    """創建測試數據"""
    dates = pd.date_range('2023-01-01', '2023-12-31', freq='D')
    np.random.seed(42)

    data = pd.DataFrame({
        'open': 100 + np.cumsum(np.random.randn(len(dates)) * 0.01),
        'high': lambda x: x['open'] * (1 + np.random.rand(len(x)) * 0.02),
        'low': lambda x: x['open'] * (1 - np.random.rand(len(x)) * 0.02),
        'close': lambda x: x['open'] + np.random.randn(len(x)) * 0.5,
        'volume': np.random.randint(1000000, 10000000, len(dates))
    }, index=dates)

    return data

def test_vectorbt_adapter_initialization():
    """測試適配器初始化"""
    config = VectorBTConfig(init_capital=1000000)
    adapter = VectorBTAdapter(config)

    assert adapter.config.init_capital == 1000000
    assert adapter.data is None
    assert adapter.portfolio is None

def test_vectorbt_backtest(sample_data):
    """測試回測功能"""
    config = VectorBTConfig(init_capital=1000000)
    adapter = VectorBTAdapter(config)

    # 加載數據
    adapter.load_data(sample_data)

    # 創建簡單信號
    entries = pd.DataFrame(False, index=sample_data.index, columns=['AAPL'])
    exits = pd.DataFrame(False, index=sample_data.index, columns=['AAPL'])

    entries.iloc[10] = True  # 第10天買入
    exits.iloc[20] = True    # 第20天賣出

    # 運行回測
    result = adapter.run_backtest(entries, exits)

    assert 'total_return' in result
    assert 'sharpe_ratio' in result
    assert 'max_drawdown' in result
    assert result['total_trades'] >= 0

def test_parallel_backtest_worker():
    """測試並行回測工作進程"""
    task_data = {
        'task_id': 'test_001',
        'data': sample_data,
        'config': VectorBTConfig().__dict__,
        'entries': entries,
        'exits': exits
    }

    result = VectorBTAdapter.parallel_backtest_worker(task_data)

    assert result['task_id'] == 'test_001'
    assert 'error' not in result
    assert result['status'] != 'failed'
```

### 2. 性能測試

```python
# tests/test_performance.py
import time
import pytest
import pandas as pd
import numpy as np
from src.backtest.vectorbt_adapter import VectorBTAdapter, VectorBTConfig
from src.backtest.parallel_processor import ParallelProcessor

@pytest.mark.performance
def test_single_vs_parallel_performance():
    """比較單進程與並行性能"""
    # 生成大量數據
    data = generate_large_dataset(100000, 100)  # 10萬條記錄，100個資產

    # 配置
    config = VectorBTConfig(init_capital=1000000)

    # 單進程測試
    start_time = time.time()
    result_single = run_single_backtest(data, config)
    single_time = time.time() - start_time

    # 並行測試
    processor = ParallelProcessor(max_workers=4)
    start_time = time.time()
    result_parallel = run_parallel_backtest(data, config, processor)
    parallel_time = time.time() - start_time

    # 性能提升應該至少2倍
    speedup = single_time / parallel_time
    assert speedup > 2.0, f"並行加速不足: {speedup:.2f}x"

    print(f"單進程時間: {single_time:.2f}秒")
    print(f"並行時間: {parallel_time:.2f}秒")
    print(f"加速比: {speedup:.2f}x")

@pytest.mark.performance
def test_memory_usage():
    """測試內存使用"""
    import psutil
    import gc

    process = psutil.Process()
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB

    # 運行大型回測
    data = generate_large_dataset(500000, 50)
    config = VectorBTConfig(init_capital=1000000)

    adapter = VectorBTAdapter(config)
    adapter.load_data(data)
    result = adapter.run_backtest(entries, exits)

    peak_memory = process.memory_info().rss / 1024 / 1024  # MB
    memory_increase = peak_memory - initial_memory

    # 清理
    del adapter
    del result
    gc.collect()

    # 內存增長應該合理（小於2GB）
    assert memory_increase < 2048, f"內存使用過多: {memory_increase:.2f}MB"

    print(f"初始內存: {initial_memory:.2f}MB")
    print(f"峰值內存: {peak_memory:.2f}MB")
    print(f"內存增長: {memory_increase:.2f}MB")
```

## 故障排除指南

### 常見問題和解決方案

1. **VectorBT許可證問題**
   ```python
   # 檢查許可證
   import vectorbt as vbt
   print(vbt.settings.license)

   # 設置許可證
   vbt.settings.license = "your_license_key"
   ```

2. **內存不足錯誤**
   ```python
   # 使用數據分片
   shards = DataSharder.time_based_shard(data, num_shards=10)
   for shard in shards:
       result = process_shard(shard)
   ```

3. **並行進程錯誤**
   ```python
   # 限制進程數
   processor = ParallelProcessor(max_workers=mp.cpu_count() - 1)
   ```

4. **數據格式錯誤**
   ```python
   # 確保數據格式正確
   data = data.astype({
       'open': 'float32',
       'high': 'float32',
       'low': 'float32',
       'close': 'float32',
       'volume': 'int32'
   })
   ```

## 總結

本實施計劃提供了VectorBT多進程回測集成的詳細技術實現方案，包括：

1. **核心適配器設計**：提供與現有系統兼容的接口
2. **並行處理優化**：充分利用多核CPU提升性能
3. **向量化策略庫**：預置常用技術指標和策略
4. **API集成方案**：無縫集成現有API架構
5. **前端更新**：提供直觀的用戶界面
6. **性能優化**：內存和計算效率優化
7. **部署指南**：生產環境部署方案

通過遵循本計劃，可以順利完成VectorBT與CBSC系統的深度集成，實現高性能的向量化回測能力。