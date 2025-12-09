#!/usr/bin/env python3
"""
Simplified System - Jupyter Integration Core
深度數據連接系統核心模塊

Phase 1.4: 建立Jupyter Notebook與Simplified System的深度數據連接

核心功能:
1. 統一的數據接口 (JupyterDataInterface)
2. 高性能緩存機制
3. 實時數據更新功能
4. Alpha因子分析引擎
5. 回測結果可視化

Author: Claude Code Assistant
Date: 2025-11-27
Version: 1.0.0
"""

import asyncio
import logging
import time
import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Union, Callable
from pathlib import Path
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import requests
from functools import wraps, lru_cache
import weakref
import gc

# Jupyter和可視化相關
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import ipywidgets as widgets
from IPython.display import display, HTML, clear_output

# 性能和監控
import psutil
import memory_profiler
from tqdm.auto import tqdm

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 配置matplotlib和seaborn樣式
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

@dataclass
class DataLoadConfig:
    """數據加載配置"""
    # 緩存配置
    enable_cache: bool = True
    cache_timeout: int = 3600  # 1小時
    max_cache_size: int = 1000  # 最大緩存條目數

    # 並發配置
    max_workers: int = 8
    timeout: int = 30

    # 數據預加載
    preload_symbols: List[str] = field(default_factory=lambda: ["0700.HK", "0941.HK", "1398.HK"])
    preload_days: int = 365

    # 實時更新配置
    enable_realtime: bool = True
    realtime_interval: int = 60  # 秒

    # Alpha因子配置
    enable_alpha_factors: bool = True
    factor_lookback_days: int = 252  # 1年

@dataclass
class PerformanceMetrics:
    """性能指標"""
    load_time: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    memory_usage: float = 0.0  # MB
    cpu_usage: float = 0.0  # %

    @property
    def cache_hit_rate(self) -> float:
        total = self.cache_hits + self.cache_misses
        return self.cache_hits / total if total > 0 else 0.0

class HighPerformanceCache:
    """高性能緩存系統"""

    def __init__(self, max_size: int = 1000, timeout: int = 3600):
        self.max_size = max_size
        self.timeout = timeout
        self._cache = {}
        self._access_times = {}
        self._lock = threading.RLock()

    def _is_expired(self, key: str) -> bool:
        """檢查緩存是否過期"""
        if key not in self._access_times:
            return True
        return (time.time() - self._access_times[key]) > self.timeout

    def _evict_if_needed(self):
        """如果需要，清理舊緩存"""
        if len(self._cache) >= self.max_size:
            # 移除最舊的條目
            oldest_key = min(self._access_times.keys(),
                           key=lambda k: self._access_times[k])
            del self._cache[oldest_key]
            del self._access_times[oldest_key]

    def get(self, key: str) -> Optional[Any]:
        """獲取緩存值"""
        with self._lock:
            if key in self._cache and not self._is_expired(key):
                self._access_times[key] = time.time()  # 更新訪問時間
                return self._cache[key]
            return None

    def set(self, key: str, value: Any):
        """設置緩存值"""
        with self._lock:
            self._evict_if_needed()
            self._cache[key] = value
            self._access_times[key] = time.time()

    def clear(self):
        """清空緩存"""
        with self._lock:
            self._cache.clear()
            self._access_times.clear()

    def get_stats(self) -> Dict[str, Any]:
        """獲取緩存統計"""
        with self._lock:
            return {
                'size': len(self._cache),
                'max_size': self.max_size,
                'memory_usage': sum(sys.getsizeof(v) for v in self._cache.values()) / 1024 / 1024  # MB
            }

class JupyterDataInterface:
    """
    Jupyter Notebook與Simplified System的深度數據接口

    提供統一的數據訪問、高性能緩存、實時更新和可視化功能
    """

    def __init__(self, config: Optional[DataLoadConfig] = None):
        self.config = config or DataLoadConfig()

        # 初始化緩存系統
        self.cache = HighPerformanceCache(
            max_size=self.config.max_cache_size,
            timeout=self.config.cache_timeout
        )

        # 性能指標
        self.metrics = PerformanceMetrics()

        # 實時更新線程
        self._realtime_thread = None
        self._stop_realtime = threading.Event()

        # 數據源連接
        self._init_data_sources()

        # Alpha因子引擎
        self._alpha_factors = {}

        logger.info("JupyterDataInterface initialized successfully")

    def _init_data_sources(self):
        """初始化數據源連接"""
        try:
            # 導入Simplified System模塊
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), 'simplified_system'))

            from src.api.stock_api import StockDataAPI
            from src.api.government_data import GovernmentDataAPI
            from src.indicators.core_indicators import CoreIndicators
            from src.backtest.vectorbt_engine import VectorBTEngine

            # 初始化API
            self.stock_api = StockDataAPI()
            self.gov_api = GovernmentDataAPI()
            self.indicators = CoreIndicators()
            self.vbt_engine = VectorBTEngine()

            logger.info("All data sources initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize data sources: {e}")
            raise

    def _measure_performance(func):
        """性能測量裝飾器"""
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            start_time = time.time()
            start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

            try:
                result = func(self, *args, **kwargs)

                # 更新性能指標
                self.metrics.load_time = time.time() - start_time
                self.metrics.memory_usage = psutil.Process().memory_info().rss / 1024 / 1024 - start_memory
                self.metrics.cpu_usage = psutil.cpu_percent()

                return result

            except Exception as e:
                logger.error(f"Error in {func.__name__}: {e}")
                raise

        return wrapper

    @_measure_performance
    def get_stock_data(self, symbol: str, days: int = 365, use_cache: bool = True) -> pd.DataFrame:
        """
        獲取股票數據 (高性能版本)

        Args:
            symbol: 股票代碼 (e.g., "0700.HK")
            days: 數據天數
            use_cache: 是否使用緩存

        Returns:
            標準化的DataFrame，包含OHLCV數據
        """
        cache_key = f"stock_{symbol}_{days}"

        # 檢查緩存
        if use_cache:
            cached_data = self.cache.get(cache_key)
            if cached_data is not None:
                self.metrics.cache_hits += 1
                logger.debug(f"Cache hit for {symbol}")
                return cached_data
            else:
                self.metrics.cache_misses += 1

        # 從API獲取數據
        try:
            raw_data = self.stock_api.get_stock_data(symbol, days)

            if raw_data and 'data' in raw_data and 'close' in raw_data['data']:
                # 轉換為DataFrame
                close_data = raw_data['data']['close']

                # 創建標準化的OHLCV DataFrame
                df = pd.DataFrame({
                    'close': list(close_data.values()),
                    'volume': raw_data['data'].get('volume', [0] * len(close_data)),
                    'high': raw_data['data'].get('high', list(close_data.values())),
                    'low': raw_data['data'].get('low', list(close_data.values())),
                    'open': raw_data['data'].get('open', list(close_data.values()))
                }, index=pd.to_datetime(list(close_data.keys())))

                df = df.sort_index()

                # 計算基本指標
                df['returns'] = df['close'].pct_change()
                df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
                df['volatility'] = df['returns'].rolling(20).std()

                # 緩存結果
                if use_cache:
                    self.cache.set(cache_key, df)

                logger.info(f"Successfully loaded {len(df)} records for {symbol}")
                return df
            else:
                raise ValueError(f"Invalid data format for {symbol}")

        except Exception as e:
            logger.error(f"Failed to load data for {symbol}: {e}")
            raise

    @_measure_performance
    def get_multiple_stocks(self, symbols: List[str], days: int = 365,
                          parallel: bool = True) -> Dict[str, pd.DataFrame]:
        """
        批量獲取多只股票數據 (支持並行處理)

        Args:
            symbols: 股票代碼列表
            days: 數據天數
            parallel: 是否使用並行處理

        Returns:
            股票數據字典 {symbol: DataFrame}
        """
        results = {}

        if parallel and len(symbols) > 1:
            # 並行處理
            with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
                future_to_symbol = {
                    executor.submit(self.get_stock_data, symbol, days): symbol
                    for symbol in symbols
                }

                for future in as_completed(future_to_symbol):
                    symbol = future_to_symbol[future]
                    try:
                        results[symbol] = future.result()
                    except Exception as e:
                        logger.error(f"Failed to load {symbol}: {e}")
        else:
            # 順序處理
            for symbol in symbols:
                try:
                    results[symbol] = self.get_stock_data(symbol, days)
                except Exception as e:
                    logger.error(f"Failed to load {symbol}: {e}")

        logger.info(f"Successfully loaded {len(results)}/{len(symbols)} stocks")
        return results

    @_measure_performance
    def get_government_data(self, data_type: str = 'hibor', days: int = 30) -> pd.DataFrame:
        """
        獲取政府數據

        Args:
            data_type: 數據類型 ('hibor', 'exchange_rates', 'monetary_base', etc.)
            days: 數據天數

        Returns:
            政府數據DataFrame
        """
        cache_key = f"gov_{data_type}_{days}"

        # 檢查緩存
        cached_data = self.cache.get(cache_key)
        if cached_data is not None:
            self.metrics.cache_hits += 1
            return cached_data
        else:
            self.metrics.cache_misses += 1

        try:
            if data_type == 'hibor':
                raw_data = self.gov_api.get_hibor_data(days)
            elif data_type == 'exchange_rates':
                raw_data = self.gov_api.get_exchange_rate_data(days)
            elif data_type == 'monetary_base':
                raw_data = self.gov_api.get_monetary_base_data(days)
            else:
                raise ValueError(f"Unsupported data type: {data_type}")

            if raw_data:
                df = pd.DataFrame(raw_data)
                if 'date' in df.columns:
                    df['date'] = pd.to_datetime(df['date'])
                    df.set_index('date', inplace=True)

                # 緩存結果
                self.cache.set(cache_key, df)

                logger.info(f"Successfully loaded {len(df)} {data_type} records")
                return df
            else:
                raise ValueError(f"No data returned for {data_type}")

        except Exception as e:
            logger.error(f"Failed to load {data_type} data: {e}")
            raise

    def calculate_alpha_factors(self, symbol: str, data: Optional[pd.DataFrame] = None) -> Dict[str, pd.Series]:
        """
        計算Alpha因子

        Args:
            symbol: 股票代碼
            data: 股票數據 (如果為None，會自動獲取)

        Returns:
            Alpha因子字典
        """
        if data is None:
            data = self.get_stock_data(symbol, self.config.factor_lookback_days)

        factors = {}

        try:
            # 技術因子
            factors['momentum_20'] = data['close'].pct_change(20)
            factors['momentum_60'] = data['close'].pct_change(60)
            factors['volatility_20'] = data['returns'].rolling(20).std()
            factors['rsi_14'] = self.indicators.calculate_rsi(data['close'], 14)
            factors['macd_signal'] = self.indicators.calculate_macd(data['close'])[1]

            # 價格因子
            factors['price_to_ma20'] = data['close'] / data['close'].rolling(20).mean()
            factors['price_to_ma60'] = data['close'] / data['close'].rolling(60).mean()
            factors['bollinger_position'] = (data['close'] - data['close'].rolling(20).mean()) / data['close'].rolling(20).std()

            # 成交量因子
            factors['volume_ratio'] = data['volume'] / data['volume'].rolling(20).mean()
            factors['volume_price_trend'] = (data['returns'] * data['volume']).rolling(20).sum()

            # 波動率因子
            factors['realized_vol'] = data['returns'].rolling(20).std() * np.sqrt(252)
            factors['vol_of_vol'] = factors['volatility_20'].rolling(20).std()

            self._alpha_factors[symbol] = factors
            logger.info(f"Calculated {len(factors)} alpha factors for {symbol}")

        except Exception as e:
            logger.error(f"Failed to calculate alpha factors for {symbol}: {e}")

        return factors

    def start_realtime_updates(self, symbols: List[str], update_interval: int = None):
        """
        啟動實時數據更新

        Args:
            symbols: 要監控的股票代碼列表
            update_interval: 更新間隔(秒)
        """
        if self._realtime_thread and self._realtime_thread.is_alive():
            logger.warning("Realtime updates already running")
            return

        interval = update_interval or self.config.realtime_interval
        self._stop_realtime.clear()

        def update_worker():
            """實時更新工作線程"""
            logger.info(f"Starting realtime updates for {symbols}")

            while not self._stop_realtime.wait(interval):
                try:
                    for symbol in symbols:
                        # 強制刷新緩存並獲取新數據
                        self.get_stock_data(symbol, days=1, use_cache=False)

                    logger.debug(f"Updated data for {len(symbols)} symbols")

                except Exception as e:
                    logger.error(f"Realtime update error: {e}")

        self._realtime_thread = threading.Thread(target=update_worker, daemon=True)
        self._realtime_thread.start()

        logger.info(f"Realtime updates started with {interval}s interval")

    def stop_realtime_updates(self):
        """停止實時數據更新"""
        if self._realtime_thread and self._realtime_thread.is_alive():
            self._stop_realtime.set()
            self._realtime_thread.join(timeout=5)
            logger.info("Realtime updates stopped")

    def get_performance_report(self) -> Dict[str, Any]:
        """獲取性能報告"""
        cache_stats = self.cache.get_stats()

        return {
            'performance_metrics': {
                'avg_load_time': self.metrics.load_time,
                'cache_hit_rate': self.metrics.cache_hit_rate,
                'cache_hits': self.metrics.cache_hits,
                'cache_misses': self.metrics.cache_misses,
                'memory_usage_mb': self.metrics.memory_usage,
                'cpu_usage_percent': self.metrics.cpu_usage
            },
            'cache_stats': cache_stats,
            'alpha_factors_count': len(self._alpha_factors),
            'realtime_updates_running': self._realtime_thread.is_alive() if self._realtime_thread else False
        }

    def create_interactive_dashboard(self, symbol: str):
        """
        創建交互式儀表板

        Args:
            symbol: 股票代碼
        """
        # 獲取數據
        data = self.get_stock_data(symbol)
        factors = self.calculate_alpha_factors(symbol, data)

        # 創建選項卡
        tab = widgets.Tab()

        # 價格圖表選項卡
        price_fig = go.Figure()
        price_fig.add_trace(go.Candlestick(
            x=data.index,
            open=data['open'],
            high=data['high'],
            low=data['low'],
            close=data['close'],
            name='Price'
        ))
        price_fig.update_layout(title=f'{symbol} Price Chart', template='plotly_white')

        # Alpha因子選項卡
        factor_fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=list(factors.keys())[:6],
            vertical_spacing=0.1
        )

        for i, (name, series) in enumerate(list(factors.items())[:6]):
            row = i // 2 + 1
            col = i % 2 + 1
            factor_fig.add_trace(
                go.Scatter(x=series.index, y=series, name=name),
                row=row, col=col
            )

        factor_fig.update_layout(title=f'{symbol} Alpha Factors', template='plotly_white')

        # 性能指標選項卡
        perf_report = self.get_performance_report()
        perf_html = self._format_performance_report(perf_report)

        # 設置選項卡內容
        tab.children = [
            go.FigureWidget(price_fig),
            go.FigureWidget(factor_fig),
            widgets.HTML(value=perf_html)
        ]

        tab.set_title(0, 'Price Chart')
        tab.set_title(1, 'Alpha Factors')
        tab.set_title(2, 'Performance')

        display(tab)

    def _format_performance_report(self, report: Dict[str, Any]) -> str:
        """格式化性能報告為HTML"""
        html = """
        <div style="padding: 20px; font-family: Arial, sans-serif;">
            <h3>Performance Report</h3>
            <table style="border-collapse: collapse; width: 100%;">
                <tr style="background-color: #f2f2f2;">
                    <th style="border: 1px solid #ddd; padding: 8px;">Metric</th>
                    <th style="border: 1px solid #ddd; padding: 8px;">Value</th>
                </tr>
        """

        for key, value in report['performance_metrics'].items():
            if isinstance(value, float):
                value = f"{value:.3f}"
            html += f"""
                <tr>
                    <td style="border: 1px solid #ddd; padding: 8px;">{key}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{value}</td>
                </tr>
            """

        html += "</table></div>"
        return html

    def __del__(self):
        """清理資源"""
        self.stop_realtime_updates()
        self.cache.clear()
        gc.collect()

# 便利函數
def create_jupyter_interface(config: Optional[DataLoadConfig] = None) -> JupyterDataInterface:
    """創建Jupyter數據接口實例"""
    return JupyterDataInterface(config)

# Jupyter魔法命令
def load_ipython_extension(ipython):
    """IPython擴展加載"""
    ipython.push_vars({
        'jupyter_interface': create_jupyter_interface(),
        'load_stock_data': lambda symbol, days=365: jupyter_interface.get_stock_data(symbol, days),
        'load_multiple_stocks': lambda symbols, days=365: jupyter_interface.get_multiple_stocks(symbols, days),
        'calculate_alpha': lambda symbol, data=None: jupyter_interface.calculate_alpha_factors(symbol, data),
        'create_dashboard': lambda symbol: jupyter_interface.create_interactive_dashboard(symbol)
    })

    print("🚀 Simplified System Jupyter Integration loaded successfully!")
    print("Available functions:")
    print("- jupyter_interface: Main interface object")
    print("- load_stock_data(symbol, days): Load single stock data")
    print("- load_multiple_stocks(symbols, days): Load multiple stocks")
    print("- calculate_alpha(symbol, data): Calculate alpha factors")
    print("- create_dashboard(symbol): Create interactive dashboard")

if __name__ == "__main__":
    # 測�试代碼
    interface = JupyterDataInterface()

    # 測試單股票數據加載
    print("Testing single stock data loading...")
    data = interface.get_stock_data("0700.HK", 100)
    print(f"Loaded {len(data)} records for 0700.HK")

    # 測試多股票並行加載
    print("\nTesting parallel data loading...")
    symbols = ["0700.HK", "0941.HK", "1398.HK"]
    multi_data = interface.get_multiple_stocks(symbols, 100, parallel=True)
    print(f"Loaded data for {len(multi_data)} stocks")

    # 測試Alpha因子計算
    print("\nTesting alpha factor calculation...")
    factors = interface.calculate_alpha_factors("0700.HK")
    print(f"Calculated {len(factors)} alpha factors")

    # 性能報告
    print("\nPerformance Report:")
    report = interface.get_performance_report()
    print(json.dumps(report, indent=2, default=str))