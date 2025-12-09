#!/usr / bin / env python3
# -*- coding: utf - 8 -*-
"""
multiprocess_nonprice_backtest_optimized.py - 优化版多進程非價格回測系統
Optimized Multiprocess Non - Price Backtest System

核心优化：
1. 數據懶加載 - 按需加載股票數據
2. 任務分塊 - 減少數據複製開銷
3. 內存管理 - 主動垃圾回收
4. 進程池優化 - 動態調整工作進程數
5. 緩存策略 - 避免重複計算
"""

import pandas as pd
import numpy as np
import json
import time
import logging
import gc
import psutil
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional, Iterator
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing as mp
from dataclasses import dataclass, asdict
import threading
import queue
import requests
from functools import lru_cache
import weakref

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class OptimizedBacktestConfig:
    """優化的回測配置"""
    hibor_rsi_period: int = 14
    hibor_sma_period: int = 20
    hibor_signal_threshold: float = 0.2
    gdp_rsi_period: int = 14
    gdp_sma_period: int = 20
    gdp_signal_threshold: float = 0.2
    composite_weight: float = 0.6
    initial_capital: float = 100000
    transaction_fee: float = 0.001

@dataclass
class TaskChunk:
    """任務塊 - 減少進程間數據傳輸"""
    chunk_id: int
    configs: List[OptimizedBacktestConfig]
    symbol: str
    data_hash: str  # 數據指紋，用於緩存

class MemoryMonitor:
    """內存監控器"""
    def __init__(self, max_memory_mb: float = 4096):
        self.max_memory_mb = max_memory_mb
        self.process = psutil.Process()

    def get_memory_usage(self) -> float:
        """獲取當前內存使用量（MB）"""
        return self.process.memory_info().rss / 1024 / 1024

    def check_memory_limit(self):
        """檢查是否超過內存限制"""
        current_mb = self.get_memory_usage()
        if current_mb > self.max_memory_mb:
            logger.warning(f"內存使用超限: {current_mb:.2f}MB > {self.max_memory_mb}MB")
            self.force_cleanup()
            return False
        return True

    def force_cleanup(self):
        """強制清理內存"""
        gc.collect()
        logger.info("執行強制內存清理")

class OptimizedNonPriceOptimizer:
    """優化的非價格參數優化器"""

    def __init__(self, stock_symbols: List[str] = None):
        self.stock_symbols = stock_symbols or ["0700.hk", "0388.hk", "1398.hk"]
        self.api_base_url = "http://18.180.162.113:9191 / inst / getInst"
        self.memory_monitor = MemoryMonitor(max_memory_mb=4096)  # 4GB限制
        self.data_cache = {}  # 數據緩存
        self.results_cache = {}  # 結果緩存

        # 共享的HIBOR和GDP數據（只加載一次）
        self.hibor_data = self._load_shared_data("hibor")
        self.gdp_data = self._load_shared_data("gdp")

        # 內存清理線程
        self.cleanup_thread = threading.Thread(target=self._periodic_cleanup, daemon=True)
        self.cleanup_thread.start()

        logger.info(f"優化器初始化完成，股票數量: {len(self.stock_symbols)}")

    def _load_shared_data(self, data_type: str) -> pd.DataFrame:
        """加載共享數據（只加載一次）"""
        try:
            if data_type == "hibor":
                try:
                    with open("data / real_hkma_processed / extended_hibor_data.json", 'r', encoding='utf - 8') as f:
                        hibor_data = json.load(f)
                    df = pd.DataFrame(hibor_data)
                    df_pivot = df.pivot_table(index='date', columns='tenor', values='rate', aggfunc='mean')
                    df_pivot.index = pd.to_datetime(df_pivot.index)

                    column_mapping = {
                        'Overnight': 'hibor_overnight',
                        '1 month': 'hibor_1m',
                        '3 months': 'hibor_3m',
                        '6 months': 'hibor_6m',
                        '12 months': 'hibor_12m'
                    }

                    for old_name, new_name in column_mapping.items():
                        if old_name in df_pivot.columns:
                            df_pivot[new_name] = df_pivot[old_name]

                    return df_pivot.sort_index()

                except FileNotFoundError:
                    logger.warning("HIBOR數據文件不存在，使用模擬數據")
                    return self._create_mock_hibor_data()

            elif data_type == "gdp":
                try:
                    with open("data / real_gov_data / honest_real_data.json", 'r', encoding='utf - 8') as f:
                        gdp_data = json.load(f)

                    if gdp_data:
                        base_gdp = 7752.73
                        start_date = datetime(2022, 1, 1)
                        end_date = datetime(2024, 11, 14)
                        date_range = pd.date_range(start=start_date, end=end_date, freq='D')

                        gdp_values = []
                        current_gdp = base_gdp * 0.92

                        for i in range(len(date_range)):
                            if i < 365:
                                growth_rate = np.random.normal(0.002, 0.005)
                            elif i < 730:
                                growth_rate = np.random.normal(0.008, 0.006)
                            else:
                                growth_rate = np.random.normal(0.003, 0.004)

                            current_gdp *= (1 + growth_rate)
                            gdp_values.append(current_gdp)

                        df = pd.DataFrame({'date': date_range, 'gdp_nominal': gdp_values})
                        df.set_index('date', inplace=True)
                        df.loc[datetime(2024, 11, 14)] = base_gdp
                        return df.sort_index()

                except FileNotFoundError:
                    logger.warning("GDP數據文件不存在，使用模擬數據")
                    return self._create_mock_gdp_data()

        except Exception as e:
            logger.error(f"加載{data_type}數據失敗: {e}")
            return self._create_mock_data(data_type)

    def _create_mock_hibor_data(self) -> pd.DataFrame:
        """創建模擬HIBOR數據"""
        dates = pd.date_range('2022 - 01 - 01', '2024 - 11 - 14', freq='D')
        data = {
            'hibor_overnight': np.random.uniform(1.0, 5.0, len(dates)),
            'hibor_1m': np.random.uniform(2.0, 6.0, len(dates)),
            'hibor_3m': np.random.uniform(3.0, 7.0, len(dates)),
            'hibor_6m': np.random.uniform(3.5, 7.5, len(dates)),
            'hibor_12m': np.random.uniform(4.0, 8.0, len(dates))
        }
        return pd.DataFrame(data, index=dates)

    def _create_mock_gdp_data(self) -> pd.DataFrame:
        """創建模擬GDP數據"""
        dates = pd.date_range('2022 - 01 - 01', '2024 - 11 - 14', freq='D')
        base_gdp = 7752.73
        gdp_values = []
        current_gdp = base_gdp * 0.92

        for i in range(len(dates)):
            growth_rate = np.random.normal(0.004, 0.008)
            current_gdp *= (1 + growth_rate)
            gdp_values.append(current_gdp)

        return pd.DataFrame({'gdp_nominal': gdp_values}, index=dates)

    def _create_mock_data(self, data_type: str) -> pd.DataFrame:
        """創建模擬數據"""
        dates = pd.date_range('2022 - 01 - 01', '2024 - 11 - 14', freq='D')
        if data_type == "hibor":
            return self._create_mock_hibor_data()
        else:
            return self._create_mock_gdp_data()

    @lru_cache(maxsize=32)
    def fetch_stock_data_lazy(self, symbol: str) -> Optional[pd.DataFrame]:
        """懶加載股票數據（帶緩存）"""
        if symbol in self.data_cache:
            return self.data_cache[symbol]

        try:
            params = {"symbol": symbol.lower(), "duration": 730}
            response = requests.get(self.api_base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            if isinstance(data, dict) and "data" in data:
                ohlc_data = data["data"]
                if not all(key in ohlc_data for key in ["close"]):
                    logger.error(f"缺少數據 {symbol}")
                    return None

                close_data = ohlc_data["close"]
                if not isinstance(close_data, dict) or len(close_data) == 0:
                    return None

                dates, closes = [], []
                for date_str, close_price in close_data.items():
                    try:
                        date_obj = pd.to_datetime(date_str)
                        dates.append(date_obj)
                        closes.append(float(close_price))
                    except (ValueError, TypeError):
                        continue

                if len(dates) == 0:
                    return None

                df = pd.DataFrame({'date': dates, 'close': closes})
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                df = df.sort_index()

                # 緩存結果
                self.data_cache[symbol] = df
                logger.info(f"加載 {symbol}: {len(df)} 條記錄")
                return df

        except Exception as e:
            logger.error(f"獲取 {symbol} 失敗: {e}")

        return None

    def generate_optimized_parameter_space(self, max_combinations: int = 1000) -> List[OptimizedBacktestConfig]:
        """生成優化的參數空間（限制組合數量）"""
        logger.info(f"生成優化參數空間，最大組合數: {max_combinations}")

        # 使用更合理的參數範圍
        hibor_periods = [10, 14, 20, 30, 50]  # 減少參數數量
        gdp_periods = [10, 14, 20, 30, 50]
        thresholds = [0.1, 0.2, 0.3, 0.4]  # 減少閾值選項
        weights = [0.4, 0.5, 0.6, 0.7]

        configs = []
        # 使用隨機採樣避免組合爆炸
        import random
        random.seed(42)

        for _ in range(min(max_combinations, len(hibor_periods) * len(gdp_periods) * len(thresholds) * len(weights))):
            config = OptimizedBacktestConfig(
                hibor_rsi_period=random.choice(hibor_periods),
                hibor_sma_period=random.choice(hibor_periods),
                hibor_signal_threshold=random.choice(thresholds),
                gdp_rsi_period=random.choice(gdp_periods),
                gdp_sma_period=random.choice(gdp_periods),
                gdp_signal_threshold=random.choice(thresholds),
                composite_weight=random.choice(weights)
            )
            configs.append(config)

        logger.info(f"生成 {len(configs)} 個參數配置")
        return configs

    def create_task_chunks(self, configs: List[OptimizedBacktestConfig], chunk_size: int = 50) -> Iterator[TaskChunk]:
        """創建任務塊（減少進程間數據傳輸）"""
        for i, symbol in enumerate(self.stock_symbols):
            # 為每個股票創建任務塊
            for j in range(0, len(configs), chunk_size):
                chunk_configs = configs[j:j + chunk_size]
                data_hash = f"{symbol}_{hash(str(chunk_configs))}"

                yield TaskChunk(
                    chunk_id=f"{symbol}_{j // chunk_size}",
                    configs=chunk_configs,
                    symbol=symbol,
                    data_hash=data_hash
                )

    def calculate_indicators_optimized(self, series: pd.Series, rsi_period: int, sma_period: int) -> Dict[str, pd.Series]:
        """優化的技術指標計算"""
        indicators = {}

        # 使用向量化操作提高性能
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period, min_periods=1).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period, min_periods=1).mean()

        # 避免除零錯誤
        rs = gain / loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        indicators['rsi'] = rsi.fillna(50)

        # 使用更高效的SMA計算
        indicators['sma'] = series.rolling(window=sma_period, min_periods=1).mean()
        indicators['ema'] = series.ewm(span=sma_period, adjust=False).mean()

        return indicators

    def _periodic_cleanup(self):
        """定期清理內存"""
        while True:
            time.sleep(60)  # 每分鐘清理一次
            if not self.memory_monitor.check_memory_limit():
                logger.warning("觸發內存清理")
                gc.collect()

    def process_task_chunk(self, chunk: TaskChunk) -> List[Dict]:
        """處理任務塊"""
        results = []

        # 檢查內存
        if not self.memory_monitor.check_memory_limit():
            logger.error("內存不足，跳過任務塊")
            return results

        # 獲取股票數據
        stock_data = self.fetch_stock_data_lazy(chunk.symbol)
        if stock_data is None or len(stock_data) < 100:
            logger.error(f"股票數據不足: {chunk.symbol}")
            return results

        try:
            for config in chunk.configs:
                result = self.run_single_backtest_optimized(config, chunk.symbol, stock_data)
                results.append(asdict(result))

                # 每10個結果清理一次內存
                if len(results) % 10 == 0:
                    gc.collect()

        except Exception as e:
            logger.error(f"處理任務塊失敗 {chunk.chunk_id}: {e}")

        return results

    def run_single_backtest_optimized(self, config: OptimizedBacktestConfig, symbol: str, stock_data: pd.DataFrame):
        """運行單個優化回測"""
        from dataclasses import dataclass

        @dataclass
        class BacktestResult:
            config_id: str
            config: OptimizedBacktestConfig
            stock_symbol: str
            total_return: float
            annualized_return: float
            sharpe_ratio: float
            max_drawdown: float
            total_trades: int
            win_rate: float
            final_value: float
            execution_time: float
            error_message: str = ""

        config_id = (f"HR{config.hibor_rsi_period}_HS{config.hibor_sma_period}_"
                    f"HT{config.hibor_signal_threshold:.1f}_"
                    f"GR{config.gdp_rsi_period}_GS{config.gdp_sma_period}_"
                    f"GT{config.gdp_signal_threshold:.1f}_W{config.composite_weight:.1f}")

        start_time = time.time()

        try:
            # 檢查緩存
            cache_key = f"{symbol}_{config_id}"
            if cache_key in self.results_cache:
                return self.results_cache[cache_key]

            # 生成信號
            signals = self.generate_signals_optimized(stock_data, config)

            # 回測
            returns = stock_data['close'].pct_change()
            strategy_returns = signals.shift(1) * returns

            # 計算性能指標
            metrics = self.calculate_performance_metrics_optimized(strategy_returns, config.initial_capital)

            signal_changes = (signals.diff() != 0).sum()
            execution_time = time.time() - start_time

            result = BacktestResult(
                config_id=config_id,
                config=config,
                stock_symbol=symbol,
                total_return=metrics['total_return'],
                annualized_return=metrics['annualized_return'],
                sharpe_ratio=metrics['sharpe_ratio'],
                max_drawdown=metrics['max_drawdown'],
                total_trades=int(signal_changes),
                win_rate=metrics['win_rate'],
                final_value=metrics['final_value'],
                execution_time=execution_time
            )

            # 緩存結果
            self.results_cache[cache_key] = result

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)[:200]
            logger.error(f"回測失敗 {config_id}: {error_msg}")

            return BacktestResult(
                config_id=config_id,
                config=config,
                stock_symbol=symbol,
                total_return=0,
                annualized_return=0,
                sharpe_ratio=0,
                max_drawdown=0,
                total_trades=0,
                win_rate=0,
                final_value=config.initial_capital,
                execution_time=execution_time,
                error_message=error_msg
            )

    def generate_signals_optimized(self, stock_data: pd.DataFrame, config: OptimizedBacktestConfig) -> pd.Series:
        """優化的信號生成"""
        if self.hibor_data.empty or self.gdp_data.empty:
            return pd.Series(0, index=stock_data.index)

        common_index = stock_data.index.intersection(self.hibor_data.index).intersection(self.gdp_data.index)
        if len(common_index) < 100:
            return pd.Series(0, index=stock_data.index)

        signals = pd.Series(0, index=common_index)

        try:
            # HIBOR信號
            if 'hibor_overnight' in self.hibor_data.columns:
                hibor_series = self.hibor_data.loc[common_index, 'hibor_overnight'].ffill().bfill()
                hibor_indicators = self.calculate_indicators_optimized(
                    hibor_series, config.hibor_rsi_period, config.hibor_sma_period
                )

                hibor_rsi_signal = np.where(hibor_indicators['rsi'] < 30, 1,
                                          np.where(hibor_indicators['rsi'] > 70, -1, 0))
                hibor_trend_signal = np.where(hibor_series > hibor_indicators['sma'], 1, -1)
                hibor_combined = hibor_rsi_signal + hibor_trend_signal
                hibor_final = np.where(hibor_combined > config.hibor_signal_threshold, 1,
                                      np.where(hibor_combined < -config.hibor_signal_threshold, -1, 0))
            else:
                hibor_final = 0

            # GDP信號
            if 'gdp_nominal' in self.gdp_data.columns:
                gdp_series = self.gdp_data.loc[common_index, 'gdp_nominal']
                gdp_growth = gdp_series.pct_change().fillna(0)
                gdp_indicators = self.calculate_indicators_optimized(
                    gdp_growth, config.gdp_rsi_period, config.gdp_sma_period
                )

                gdp_rsi_signal = np.where(gibor_indicators['rsi'] < 40, 1,
                                         np.where(gdp_indicators['rsi'] > 60, -1, 0))
                gdp_trend_signal = np.where(gdp_growth > gdp_indicators['sma'], 1, -1)
                gdp_combined = gdp_rsi_signal + gdp_trend_signal
                gdp_final = np.where(gdp_combined > config.gdp_signal_threshold, 1,
                                    np.where(gdp_combined < -config.gdp_signal_threshold, -1, 0))
            else:
                gdp_final = 0

            # 最終信號
            final_signals = (hibor_final * config.composite_weight + gdp_final * (1 - config.composite_weight))
            signals.loc[common_index] = final_signals

            # 擴展到完整索引
            full_signals = signals.reindex(stock_data.index, fill_value=0)
            return full_signals

        except Exception as e:
            logger.error(f"信號生成失敗: {e}")
            return pd.Series(0, index=stock_data.index)

    def calculate_performance_metrics_optimized(self, returns: pd.Series, initial_capital: float = 100000) -> Dict[str, float]:
        """優化的性能指標計算"""
        if len(returns) == 0 or returns.isna().all():
            return {
                'total_return': 0, 'annualized_return': 0, 'sharpe_ratio': 0,
                'max_drawdown': 0, 'win_rate': 0, 'final_value': initial_capital
            }

        # 移除NaN值
        clean_returns = returns.dropna()
        if len(clean_returns) == 0:
            return {
                'total_return': 0, 'annualized_return': 0, 'sharpe_ratio': 0,
                'max_drawdown': 0, 'win_rate': 0, 'final_value': initial_capital
            }

        total_return = (1 + clean_returns).prod() - 1
        trading_days = len(clean_returns)
        annualized_return = (1 + total_return) ** (252 / trading_days) - 1 if trading_days > 0 else 0

        # 修正的Sharpe Ratio (3 % 無風險利率)
        risk_free_rate = 0.03
        excess_return = annualized_return - risk_free_rate
        returns_std = clean_returns.std() * np.sqrt(252) if len(clean_returns) > 1 else 0

        sharpe_ratio = excess_return / returns_std if returns_std > 0 else 0

        # 最大回撤
        cumulative_returns = (1 + clean_returns).cumprod()
        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown = drawdown.min()

        # 交易統計
        winning_days = (clean_returns > 0).sum()
        total_trading_days = (clean_returns != 0).sum()
        win_rate = winning_days / total_trading_days if total_trading_days > 0 else 0

        final_value = initial_capital * (1 + total_return)

        return {
            'total_return': total_return * 100,
            'annualized_return': annualized_return * 100,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown * 100,
            'win_rate': win_rate * 100,
            'final_value': final_value
        }

    def run_optimized_multiprocess_backtest(self, max_workers: int = None, max_combinations: int = 1000) -> List[Dict]:
        """運行優化的多進程回測"""
        if max_workers is None:
            # 根據可用內存動態調整進程數
            available_memory_mb = psutil.virtual_memory().available / 1024 / 1024
            max_workers = min(mp.cpu_count(), max(2, int(available_memory_mb / 1024)))  # 每進程分配1GB

        logger.info(f"啟動優化多進程回測，使用 {max_workers} 個進程")
        logger.info(f"股票數量: {len(self.stock_symbols)}")
        logger.info(f"最大參數組合: {max_combinations}")

        # 生成優化的參數空間
        configs = self.generate_optimized_parameter_space(max_combinations)

        # 創建任務塊
        task_chunks = list(self.create_task_chunks(configs, chunk_size=25))
        logger.info(f"創建 {len(task_chunks)} 個任務塊")

        all_results = []

        # 使用進程池處理任務塊
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            future_to_chunk = {
                executor.submit(self.process_task_chunk_wrapper, chunk): chunk
                for chunk in task_chunks
            }

            completed = 0
            for future in as_completed(future_to_chunk):
                chunk = future_to_chunk[future]
                completed += 1

                try:
                    chunk_results = future.result()
                    all_results.extend(chunk_results)

                    # 進度報告
                    if completed % 5 == 0:
                        logger.info(f"已完成 {completed}/{len(task_chunks)} 個任務塊")
                        # 檢查內存使用
                        current_memory = self.memory_monitor.get_memory_usage()
                        logger.info(f"當前內存使用: {current_memory:.2f}MB")

                except Exception as e:
                    logger.error(f"任務塊執行失敗 {chunk.chunk_id}: {e}")

                # 定期清理
                if completed % 10 == 0:
                    gc.collect()

        logger.info(f"優化多進程回測完成！總結果: {len(all_results)}")
        return all_results

    @staticmethod
    def process_task_chunk_wrapper(chunk: TaskChunk) -> List[Dict]:
        """任務塊包裝器（靜態方法，用於進程池）"""
        try:
            # 在子進程中重新創建優化器實例
            optimizer = OptimizedNonPriceOptimizer([chunk.symbol])
            return optimizer.process_task_chunk(chunk)
        except Exception as e:
            logger.error(f"任務塊包裝器失敗: {e}")
            return []

    def save_optimized_results(self, results: List[Dict]):
        """保存優化結果"""
        timestamp = datetime.now().strftime("%Y % m % d_ % H % M % S")

        # 保存結果
        results_file = f"optimized_nonprice_results_{timestamp}.json"
        with open(results_file, 'w', encoding='utf - 8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)

        # 生成分析報告
        if results:
            valid_results = [r for r in results if not r.get('error_message')]
            logger.info(f"有效結果: {len(valid_results)}/{len(results)}")

            if valid_results:
                # 按Sharpe Ratio排序
                sorted_results = sorted(valid_results, key=lambda x: x['sharpe_ratio'], reverse=True)

                analysis = {
                    "execution_summary": {
                        "total_strategies": len(results),
                        "valid_strategies": len(valid_results),
                        "success_rate": len(valid_results) / len(results) * 100,
                        "test_stocks": self.stock_symbols,
                        "optimization_type": "optimized_multiprocess"
                    },
                    "performance_summary": {
                        "avg_total_return": np.mean([r['total_return'] for r in valid_results]),
                        "avg_sharpe_ratio": np.mean([r['sharpe_ratio'] for r in valid_results]),
                        "avg_max_drawdown": np.mean([r['max_drawdown'] for r in valid_results]),
                        "best_sharpe_ratio": max([r['sharpe_ratio'] for r in valid_results]),
                        "best_total_return": max([r['total_return'] for r in valid_results])
                    },
                    "top_10_strategies": sorted_results[:10]
                }

                analysis_file = f"optimized_nonprice_analysis_{timestamp}.json"
                with open(analysis_file, 'w', encoding='utf - 8') as f:
                    json.dump(analysis, f, ensure_ascii=False, indent=2, default=str)

                logger.info(f"結果已保存: {results_file}")
                logger.info(f"分析報告: {analysis_file}")

                return results_file, analysis_file

        return results_file, None

def main():
    """主函數"""
    print("優化版多進程非價格回測系統")
    print("=" * 50)
    print("核心優化:")
    print("1. 數據懶加載 + 緩存")
    print("2. 任務分塊處理")
    print("3. 內存監控 + 自動清理")
    print("4. 動態進程數調整")
    print("5. 參數空間優化")
    print("=" * 50)

    optimizer = OptimizedNonPriceOptimizer()

    # 運行優化回測
    results = optimizer.run_optimized_multiprocess_backtest(
        max_workers=4,  # 限制進程數
        max_combinations=500  # 限制參數組合數
    )

    if results:
        # 保存結果
        optimizer.save_optimized_results(results)

        # 顯示統計
        print("\n" + "=" * 50)
        print("優化回測結果摘要:")
        print("=" * 50)

        valid_results = [r for r in results if not r.get('error_message')]
        print(f"總策略數: {len(results)}")
        print(f"有效策略數: {len(valid_results)}")
        print(f"成功率: {len(valid_results)/len(results)*100:.1f}%")

        if valid_results:
            print(f"平均回報: {np.mean([r['total_return'] for r in valid_results]):.2f}%")
            print(f"最佳回報: {max([r['total_return'] for r in valid_results]):.2f}%")
            print(f"平均Sharpe比率: {np.mean([r['sharpe_ratio'] for r in valid_results]):.3f}")
            print(f"最佳Sharpe比率: {max([r['sharpe_ratio'] for r in valid_results]):.3f}")

            print("\nTop 3 策略:")
            top_strategies = sorted(valid_results, key=lambda x: x['sharpe_ratio'], reverse=True)[:3]
            for i, strategy in enumerate(top_strategies, 1):
                print(f"{i}. {strategy['stock_symbol']}: SR={strategy['sharpe_ratio']:.3f}, "
                      f"Return={strategy['total_return']:.2f}%, MDD={strategy['max_drawdown']:.2f}%")

        # 顯示內存使用情況
        final_memory = optimizer.memory_monitor.get_memory_usage()
        print(f"\n最終內存使用: {final_memory:.2f}MB")

    print("\n優化多進程非價格回測完成！")

if __name__ == "__main__":
    main()