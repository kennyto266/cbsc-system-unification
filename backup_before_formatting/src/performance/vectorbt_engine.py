#!/usr/bin/env python3
"""
VectorBT高性能计算引擎
提供向量化回测、并行优化和GPU加速功能
"""

import logging
import multiprocessing as mp
import numpy as np
import pandas as pd
import vectorbt as vbt
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union, Iterator
from dataclasses import dataclass
from functools import lru_cache
import time
import pickle
import hashlib

from ..strategy.hybrid_signals import HybridSignalFramework, SignalResult, SignalConfig

logger = logging.getLogger(__name__)


@dataclass
class BacktestConfig:
    """回测配置"""
    start_date: datetime
    end_date: datetime
    initial_cash: float = 100000
    fees: float = 0.001
    slippage: float = 0.001
    cash_sharing: bool = True
    call_seq: str = "auto"
    directional_hedges: bool = False
    seatbelt: bool = True


@dataclass
class OptimizationResult:
    """优化结果"""
    parameters: Dict[str, Any]
    performance_metrics: Dict[str, float]
    sharpe_ratio: float
    max_drawdown: float
    total_return: float
    quality_score: float
    execution_time: float


@dataclass
class BacktestResult:
    """回测结果"""
    symbol: str
    strategy_name: str
    parameters: Dict[str, Any]
    equity_curve: pd.Series
    trades: pd.DataFrame
    metrics: Dict[str, float]
    execution_time: float
    benchmark_metrics: Optional[Dict[str, float]] = None


class VectorBTComputeEngine:
    """VectorBT高性能计算引擎"""
    
    def __init__(self, 
                 max_processes: Optional[int] = None,
                 use_gpu: bool = False,
                 cache_enabled: bool = True):
        self.max_processes = max_processes or min(mp.cpu_count(), 8)
        self.use_gpu = use_gpu
        self.cache_enabled = cache_enabled
        self._cache = {}
        self.hybrid_framework = HybridSignalFramework()
        
        # GPU支持检查
        if self.use_gpu:
            try:
                import torch
                self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
                logger.info(f"GPU加速已启用，设备: {self.device}")
            except ImportError:
                logger.warning("PyTorch未安装，使用CPU计算")
                self.device = "cpu"
                self.use_gpu = False
        else:
            self.device = "cpu"
    
    def vectorized_backtest(self, 
                           symbols: List[str],
                           price_data: Dict[str, pd.DataFrame],
                           signals: Dict[str, pd.DataFrame],
                           config: BacktestConfig) -> Dict[str, BacktestResult]:
        """向量化回测"""
        logger.info(f"开始向量化回测 {len(symbols)} 个标的...")
        start_time = time.time()
        
        results = {}
        
        try:
            for symbol in symbols:
                if symbol not in price_data or symbol not in signals:
                    logger.warning(f"跳过 {symbol}：缺少价格或信号数据")
                    continue
                
                symbol_start = time.time()
                result = self._backtest_single_symbol(
                    symbol, 
                    price_data[symbol], 
                    signals[symbol], 
                    config
                )
                
                if result:
                    results[symbol] = result
                    logger.info(f"{symbol} 回测完成 ({time.time() - symbol_start:.2f}s)")
            
            total_time = time.time() - start_time
            logger.info(f"向量化回测完成，总计 {len(results)} 个标的，耗时 {total_time:.2f}s")
            
            return results
            
        except Exception as e:
            logger.error(f"向量化回测失败: {e}")
            return {}
    
    def _backtest_single_symbol(self, 
                               symbol: str,
                               price_data: pd.DataFrame,
                               signals: pd.DataFrame,
                               config: BacktestConfig) -> Optional[BacktestResult]:
        """单个标的回测"""
        try:
            # 数据对齐
            common_index = price_data.index.intersection(signals.index)
            if len(common_index) == 0:
                logger.warning(f"{symbol} 价格和信号数据时间范围不匹配")
                return None
            
            price_aligned = price_data.reindex(common_index, method='ffill').dropna()
            signals_aligned = signals.reindex(common_index, method='ffill').dropna()
            
            if len(price_aligned) < 50:  # 数据不足
                logger.warning(f"{symbol} 数据不足 ({len(price_aligned)} 行)")
                return None
            
            # 创建投资组合
            if 'hybrid_signal' in signals_aligned.columns:
                portfolio = vbt.Portfolio.from_signals(
                    price_aligned['close'],
                    signals_aligned['hybrid_signal'] > 0.3,  # 买入信号
                    signals_aligned['hybrid_signal'] < -0.3,  # 卖出信号
                    init_cash=config.initial_cash,
                    fees=config.fees,
                    slippage=config.slippage,
                    cash_sharing=config.cash_sharing,
                    call_seq=config.call_seq,
                    directional_hedges=config.directional_hedges,
                    seatbelt=config.seatbelt
                )
            else:
                # 使用第一个可用信号
                signal_cols = [col for col in signals_aligned.columns if 'signal' in col]
                if not signal_cols:
                    logger.warning(f"{symbol} 无有效交易信号")
                    return None
                
                portfolio = vbt.Portfolio.from_signals(
                    price_aligned['close'],
                    signals_aligned[signal_cols[0]] > 0.3,
                    signals_aligned[signal_cols[0]] < -0.3,
                    init_cash=config.initial_cash,
                    fees=config.fees,
                    slippage=config.slippage
                )
            
            # 计算基准指标 (买入持有策略)
            benchmark = vbt.Portfolio.from_holding(
                price_aligned['close'],
                init_cash=config.initial_cash,
                fees=0,  # 基准不考虑手续费
                slippage=0
            )
            
            # 获取回测结果
            equity_curve = portfolio.value()
            trades = portfolio.trades.records_readable
            
            # 计算性能指标
            metrics = self._calculate_portfolio_metrics(portfolio)
            benchmark_metrics = self._calculate_portfolio_metrics(benchmark)
            
            return BacktestResult(
                symbol=symbol,
                strategy_name="hybrid_vectorbt",
                parameters={"signal_threshold": 0.3},
                equity_curve=equity_curve,
                trades=trades,
                metrics=metrics,
                execution_time=time.time(),
                benchmark_metrics=benchmark_metrics
            )
            
        except Exception as e:
            logger.error(f"{symbol} 回测失败: {e}")
            return None
    
    def parallel_optimization(self, 
                            symbols: List[str],
                            price_data: Dict[str, pd.DataFrame],
                            economic_data: Dict[str, pd.DataFrame],
                            param_grid: Dict[str, List[Any]],
                            config: BacktestConfig) -> List[OptimizationResult]:
        """并行参数优化"""
        logger.info(f"开始并行优化，参数组合数: {self._count_param_combinations(param_grid)}")
        
        # 生成参数组合
        param_combinations = self._generate_param_combinations(param_grid)
        
        if not param_combinations:
            logger.warning("无有效参数组合")
            return []
        
        # 并行执行优化
        all_results = []
        
        with ProcessPoolExecutor(max_workers=self.max_processes) as executor:
            futures = []
            
            for params in param_combinations:
                future = executor.submit(
                    self._optimize_single_param_set,
                    symbols, price_data, economic_data, params, config
                )
                futures.append(future)
            
            # 收集结果
            for i, future in enumerate(as_completed(futures)):
                try:
                    result = future.result(timeout=300)  # 5分钟超时
                    if result:
                        all_results.append(result)
                    
                    if (i + 1) % 10 == 0:
                        logger.info(f"完成 {i + 1}/{len(futures)} 个参数组合")
                        
                except Exception as e:
                    logger.error(f"参数组合优化失败: {e}")
        
        # 按质量评分排序
        all_results.sort(key=lambda x: x.quality_score, reverse=True)
        
        logger.info(f"并行优化完成，有效结果: {len(all_results)}")
        return all_results
    
    async def _optimize_single_param_set(self,
                                         symbols: List[str],
                                         price_data: Dict[str, pd.DataFrame],
                                         economic_data: Dict[str, pd.DataFrame],
                                         params: Dict[str, Any],
                                         config: BacktestConfig) -> Optional[OptimizationResult]:
        """单个参数集优化"""
        try:
            start_time = time.time()

            # 更新信号配置
            signal_config = SignalConfig(
                price_weight=params.get('price_weight', 0.6),
                economic_weight=params.get('economic_weight', 0.4),
                adaptive_weights=params.get('adaptive_weights', True),
                regime_aware=params.get('regime_aware', True)
            )

            # 创建混合信号框架
            hybrid_framework = HybridSignalFramework(signal_config)

            # 生成信号
            all_signals = {}
            for symbol in symbols[:5]:  # 限制标的数量以提高速度
                if symbol in price_data:
                    symbol_econ_data = {k: v for k, v in economic_data.items()
                                      if isinstance(v, pd.DataFrame)}

                    signal_result = await hybrid_framework.generate_hybrid_signals(
                        symbol, price_data[symbol], symbol_econ_data,
                        config.start_date, config.end_date
                    )
                    
                    if signal_result and not signal_result.signals.empty:
                        all_signals[symbol] = signal_result.signals
            
            if not all_signals:
                return None
            
            # 回测
            backtest_results = self.vectorized_backtest(
                list(all_signals.keys()), price_data, all_signals, config
            )
            
            if not backtest_results:
                return None
            
            # 计算综合指标
            sharpe_ratios = [r.metrics.get('sharpe_ratio', 0) for r in backtest_results.values()]
            max_drawdowns = [r.metrics.get('max_drawdown', 0) for r in backtest_results.values()]
            total_returns = [r.metrics.get('total_return', 0) for r in backtest_results.values()]
            
            avg_sharpe = np.mean(sharpe_ratios) if sharpe_ratios else 0
            avg_drawdown = np.mean(max_drawdowns) if max_drawdowns else 0
            avg_return = np.mean(total_returns) if total_returns else 0
            
            # 质量评分
            quality_score = self._calculate_optimization_quality(
                avg_sharpe, avg_drawdown, avg_return, len(backtest_results)
            )
            
            return OptimizationResult(
                parameters=params,
                performance_metrics={
                    'avg_sharpe': avg_sharpe,
                    'avg_max_drawdown': avg_drawdown,
                    'avg_total_return': avg_return,
                    'success_rate': len(backtest_results) / len(symbols)
                },
                sharpe_ratio=avg_sharpe,
                max_drawdown=avg_drawdown,
                total_return=avg_return,
                quality_score=quality_score,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"参数集优化失败 {params}: {e}")
            return None
    
    def portfolio_simulation(self, 
                           weights: pd.DataFrame,
                           returns: pd.DataFrame,
                           config: BacktestConfig) -> Dict[str, Any]:
        """投资组合模拟"""
        try:
            logger.info(f"开始投资组合模拟，资产数: {len(weights.columns)}")
            
            # 创建投资组合
            portfolio = vbt.Portfolio.from_orders(
                returns,
                sizes=weights,
                init_cash=config.initial_cash,
                fees=config.fees,
                slippage=config.slippage
            )
            
            # 计算指标
            metrics = self._calculate_portfolio_metrics(portfolio)
            
            # 风险分析
            risk_metrics = self._calculate_risk_metrics(returns, weights)
            
            # 相关性分析
            correlation_matrix = returns.corr()
            
            result = {
                'portfolio_metrics': metrics,
                'risk_metrics': risk_metrics,
                'correlation_matrix': correlation_matrix,
                'portfolio_value': portfolio.value(),
                'portfolio_drawdown': portfolio.drawdown(),
                'weights_history': weights if isinstance(weights, pd.DataFrame) else weights
            }
            
            logger.info("投资组合模拟完成")
            return result
            
        except Exception as e:
            logger.error(f"投资组合模拟失败: {e}")
            return {}
    
    def _calculate_portfolio_metrics(self, portfolio) -> Dict[str, float]:
        """计算投资组合指标"""
        try:
            metrics = {}
            
            # 基本指标
            metrics['total_return'] = portfolio.total_return()
            metrics['annual_return'] = portfolio.annual_return()
            metrics['sharpe_ratio'] = portfolio.sharpe_ratio()
            metrics['sortino_ratio'] = portfolio.sortino_ratio()
            metrics['calmar_ratio'] = portfolio.calmar_ratio()
            metrics['max_drawdown'] = portfolio.max_drawdown()
            metrics['avg_drawdown'] = portfolio.avg_drawdown()
            
            # 交易统计
            trades = portfolio.trades
            metrics['total_trades'] = len(trades) if trades is not None else 0
            metrics['win_rate'] = portfolio.win_rate()
            metrics['avg_trade'] = portfolio.avg_trade()
            metrics['profit_factor'] = portfolio.profit_factor()
            
            # 时间指标
            metrics['exposure_time'] = portfolio.exposure_time()
            metrics['position_changes'] = portfolio.position_changes()
            
            return metrics
            
        except Exception as e:
            logger.error(f"计算投资组合指标失败: {e}")
            return {}
    
    def _calculate_risk_metrics(self, returns: pd.DataFrame, weights: pd.DataFrame) -> Dict[str, float]:
        """计算风险指标"""
        try:
            risk_metrics = {}
            
            # 投资组合收益
            if isinstance(weights, pd.DataFrame):
                portfolio_returns = (returns * weights).sum(axis=1)
            else:
                portfolio_returns = returns.mean(axis=1)
            
            # 风险指标
            risk_metrics['volatility'] = portfolio_returns.std() * np.sqrt(252)
            risk_metrics['downside_deviation'] = portfolio_returns[portfolio_returns < 0].std() * np.sqrt(252)
            risk_metrics['var_95'] = portfolio_returns.quantile(0.05)
            risk_metrics['cvar_95'] = portfolio_returns[portfolio_returns <= portfolio_returns.quantile(0.05)].mean()
            
            # 相关性风险
            if len(returns.columns) > 1:
                avg_correlation = returns.corr().values[np.triu_indices_from(returns.corr().values, k=1)].mean()
                risk_metrics['avg_correlation'] = avg_correlation
                
                # 有效边界指标
                risk_metrics['diversification_ratio'] = (weights.abs().sum() if isinstance(weights, pd.DataFrame) else 1) / np.sqrt(len(returns.columns))
            
            return risk_metrics
            
        except Exception as e:
            logger.error(f"计算风险指标失败: {e}")
            return {}
    
    def _count_param_combinations(self, param_grid: Dict[str, List[Any]]) -> int:
        """计算参数组合数量"""
        count = 1
        for values in param_grid.values():
            count *= len(values)
        return count
    
    def _generate_param_combinations(self, param_grid: Dict[str, List[Any]]) -> List[Dict[str, Any]]:
        """生成参数组合"""
        if not param_grid:
            return []
        
        import itertools
        
        keys = list(param_grid.keys())
        values = list(param_grid.values())
        
        combinations = []
        for combination in itertools.product(*values):
            param_dict = dict(zip(keys, combination))
            combinations.append(param_dict)
        
        return combinations
    
    def _calculate_optimization_quality(self, 
                                      sharpe_ratio: float, 
                                      max_drawdown: float, 
                                      total_return: float,
                                      success_rate: float) -> float:
        """计算优化质量评分"""
        try:
            # Sharpe比率评分 (0-40分)
            sharpe_score = min(40, max(0, sharpe_ratio * 20))
            
            # 最大回撤评分 (0-30分，回撤越小分数越高)
            drawdown_score = min(30, max(0, (1 - abs(max_drawdown)) * 30))
            
            # 总收益评分 (0-20分)
            return_score = min(20, max(0, total_return * 100))
            
            # 成功率评分 (0-10分)
            success_score = min(10, success_rate * 10)
            
            total_score = sharpe_score + drawdown_score + return_score + success_score
            
            return round(total_score, 2)
            
        except Exception as e:
            logger.error(f"计算优化质量评分失败: {e}")
            return 0.0
    
    @lru_cache(maxsize=128)
    def _get_cache_key(self, data: Any) -> str:
        """生成缓存键"""
        try:
            serialized = pickle.dumps(data, protocol=4)
            return hashlib.md5(serialized).hexdigest()
        except:
            return str(hash(data))
    
    def clear_cache(self):
        """清除缓存"""
        self._cache.clear()
        if hasattr(self, '_get_cache_key'):
            self._get_cache_key.cache_clear()
        logger.info("计算引擎缓存已清除")


# 辅助函数
def run_parallel_backtest(engine: VectorBTComputeEngine,
                         symbols: List[str],
                         price_data: Dict[str, pd.DataFrame],
                         signals: Dict[str, pd.DataFrame],
                         config: BacktestConfig) -> Dict[str, BacktestResult]:
    """运行并行回测"""
    return engine.vectorized_backtest(symbols, price_data, signals, config)


def run_parameter_optimization(engine: VectorBTComputeEngine,
                             symbols: List[str],
                             price_data: Dict[str, pd.DataFrame],
                             economic_data: Dict[str, pd.DataFrame],
                             param_grid: Dict[str, List[Any]],
                             config: BacktestConfig) -> List[OptimizationResult]:
    """运行参数优化"""
    return engine.parallel_optimization(symbols, price_data, economic_data, param_grid, config)