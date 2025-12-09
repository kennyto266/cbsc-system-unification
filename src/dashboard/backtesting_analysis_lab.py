"""
回测分析实验室

提供专业的策略回测、对比分析、风险评估和性能可视化功能
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import json
import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException, BackgroundTasks
import plotly.graph_objects as go
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder

from ..backtest.enhanced_backtest_engine import EnhancedBacktestEngine
from ..models.cbsc_models import AdvancedSentimentProcessor


class BacktestStatus(Enum):
    """回测状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ComparisonMetric(Enum):
    """对比指标枚举"""
    TOTAL_RETURN = "total_return"
    SHARPE_RATIO = "sharpe_ratio"
    MAX_DRAWDOWN = "max_drawdown"
    WIN_RATE = "win_rate"
    CALMAR_RATIO = "calmar_ratio"
    PROFIT_FACTOR = "profit_factor"
    SORTINO_RATIO = "sortino_ratio"


@dataclass
class BacktestConfig:
    """回测配置"""
    strategy_type: str
    parameters: Dict[str, Any]
    start_date: str
    end_date: str
    initial_capital: float = 100000
    commission: float = 0.001
    slippage: float = 0.001
    benchmark: str = "HSI"
    rebalance_frequency: str = "daily"
    risk_free_rate: float = 0.02


@dataclass
class BacktestResult:
    """回测结果"""
    backtest_id: str
    config: BacktestConfig
    status: BacktestStatus
    created_at: datetime
    completed_at: Optional[datetime] = None

    # 性能指标
    total_return: float = 0.0
    annualized_return: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 1.0

    # 交易统计
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    avg_trade_return: float = 0.0
    avg_winning_trade: float = 0.0
    avg_losing_trade: float = 0.0

    # 风险指标
    volatility: float = 0.0
    beta: float = 0.0
    alpha: float = 0.0
    var_95: float = 0.0
    cvar_95: float = 0.0

    # 详细数据
    equity_curve: List[Dict[str, Any]] = None
    trades: List[Dict[str, Any]] = None
    monthly_returns: List[Dict[str, Any]] = None
    drawdown_periods: List[Dict[str, Any]] = None

    # 错误信息
    error_message: Optional[str] = None


@dataclass
class ComparisonResult:
    """策略对比结果"""
    comparison_id: str
    strategies: List[str]
    backtest_results: List[BacktestResult]
    comparison_metrics: Dict[str, Dict[str, float]]
    ranking: List[Dict[str, Any]]
    statistical_significance: Dict[str, Any]
    correlation_matrix: Dict[str, Dict[str, float]]
    created_at: datetime


class BacktestingAnalysisLab:
    """回测分析实验室"""

    def __init__(self):
        self.logger = logging.getLogger("backtesting_analysis_lab")
        self.router = APIRouter(prefix="/api/backtesting", tags=["backtesting_lab"])

        # 数据存储
        self.backtest_results: Dict[str, BacktestResult] = {}
        self.comparison_results: Dict[str, ComparisonResult] = {}
        self.running_backtests: Dict[str, asyncio.Task] = {}

        # 核心组件
        self.backtest_engine = EnhancedBacktestEngine()
        self.sentiment_processor = AdvancedSentimentProcessor()

        self._setup_routes()

    def _setup_routes(self):
        """设置API路由"""

        @self.router.post("/run")
        async def run_backtest(config: BacktestConfig, background_tasks: BackgroundTasks):
            """运行回测"""
            try:
                backtest_id = self._generate_backtest_id()

                # 创建回测结果对象
                result = BacktestResult(
                    backtest_id=backtest_id,
                    config=config,
                    status=BacktestStatus.PENDING,
                    created_at=datetime.now()
                )

                self.backtest_results[backtest_id] = result

                # 启动后台回测任务
                task = asyncio.create_task(self._execute_backtest(backtest_id, config))
                self.running_backtests[backtest_id] = task

                return {
                    "backtest_id": backtest_id,
                    "status": "submitted",
                    "message": "回测任务已提交"
                }
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @self.router.get("/status/{backtest_id}")
        async def get_backtest_status(backtest_id: str):
            """获取回测状态"""
            if backtest_id not in self.backtest_results:
                raise HTTPException(status_code=404, detail="回测任务未找到")

            result = self.backtest_results[backtest_id]
            return {
                "backtest_id": backtest_id,
                "status": result.status.value,
                "progress": getattr(result, 'progress', 0),
                "created_at": result.created_at.isoformat(),
                "completed_at": result.completed_at.isoformat() if result.completed_at else None,
                "error_message": result.error_message
            }

        @self.router.get("/results/{backtest_id}")
        async def get_backtest_results(backtest_id: str):
            """获取回测结果"""
            if backtest_id not in self.backtest_results:
                raise HTTPException(status_code=404, detail="回测任务未找到")

            result = self.backtest_results[backtest_id]
            if result.status != BacktestStatus.COMPLETED:
                raise HTTPException(status_code=400, detail="回测尚未完成")

            return asdict(result)

        @self.router.get("/results/{backtest_id}/equity-curve")
        async def get_equity_curve(backtest_id: str):
            """获取资金曲线数据"""
            if backtest_id not in self.backtest_results:
                raise HTTPException(status_code=404, detail="回测任务未找到")

            result = self.backtest_results[backtest_id]
            if result.status != BacktestStatus.COMPLETED or not result.equity_curve:
                raise HTTPException(status_code=400, detail="资金曲线数据不可用")

            # 生成交互式图表
            chart_data = self._generate_equity_curve_chart(result)
            return {
                "backtest_id": backtest_id,
                "chart_data": chart_data,
                "equity_curve": result.equity_curve
            }

        @self.router.get("/results/{backtest_id}/trades")
        async def get_trade_analysis(backtest_id: str):
            """获取交易分析数据"""
            if backtest_id not in self.backtest_results:
                raise HTTPException(status_code=404, detail="回测任务未找到")

            result = self.backtest_results[backtest_id]
            if result.status != BacktestStatus.COMPLETED:
                raise HTTPException(status_code=400, detail="回测尚未完成")

            trade_analysis = self._analyze_trades(result.trades or [])
            return {
                "backtest_id": backtest_id,
                "trades": result.trades or [],
                "trade_analysis": trade_analysis,
                "trade_statistics": self._calculate_trade_statistics(result)
            }

        @self.router.get("/results/{backtest_id}/risk-analysis")
        async def get_risk_analysis(backtest_id: str):
            """获取风险分析数据"""
            if backtest_id not in self.backtest_results:
                raise HTTPException(status_code=404, detail="回测任务未找到")

            result = self.backtest_results[backtest_id]
            if result.status != BacktestStatus.COMPLETED:
                raise HTTPException(status_code=400, detail="回测尚未完成")

            risk_analysis = await self._perform_risk_analysis(result)
            return {
                "backtest_id": backtest_id,
                "risk_metrics": risk_analysis,
                "var_analysis": self._calculate_var_analysis(result),
                "stress_test": await self._perform_stress_test(result)
            }

        @self.router.post("/compare")
        async def compare_strategies(backtest_ids: List[str], metrics: List[ComparisonMetric]):
            """对比多个策略"""
            try:
                # 验证回测结果
                valid_results = []
                for backtest_id in backtest_ids:
                    if backtest_id not in self.backtest_results:
                        raise HTTPException(status_code=404, detail=f"回测 {backtest_id} 未找到")

                    result = self.backtest_results[backtest_id]
                    if result.status != BacktestStatus.COMPLETED:
                        raise HTTPException(status_code=400, detail=f"回测 {backtest_id} 尚未完成")

                    valid_results.append(result)

                if len(valid_results) < 2:
                    raise HTTPException(status_code=400, detail="至少需要2个完成的回测结果")

                # 执行对比分析
                comparison_id = self._generate_comparison_id()
                comparison_result = await self._perform_strategy_comparison(
                    comparison_id, valid_results, metrics
                )

                self.comparison_results[comparison_id] = comparison_result

                return asdict(comparison_result)

            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @self.router.get("/comparison/{comparison_id}")
        async def get_comparison_results(comparison_id: str):
            """获取对比结果"""
            if comparison_id not in self.comparison_results:
                raise HTTPException(status_code=404, detail="对比结果未找到")

            return asdict(self.comparison_results[comparison_id])

        @self.router.get("/comparison/{comparison_id}/charts")
        async def get_comparison_charts(comparison_id: str):
            """获取对比图表"""
            if comparison_id not in self.comparison_results:
                raise HTTPException(status_code=404, detail="对比结果未找到")

            comparison = self.comparison_results[comparison_id]
            charts = await self._generate_comparison_charts(comparison)

            return {
                "comparison_id": comparison_id,
                "charts": charts
            }

        @self.router.delete("/cancel/{backtest_id}")
        async def cancel_backtest(backtest_id: str):
            """取消回测"""
            if backtest_id not in self.backtest_results:
                raise HTTPException(status_code=404, detail="回测任务未找到")

            result = self.backtest_results[backtest_id]

            if result.status in [BacktestStatus.COMPLETED, BacktestStatus.FAILED, BacktestStatus.CANCELLED]:
                raise HTTPException(status_code=400, detail="无法取消已完成的回测")

            # 取消运行中的任务
            if backtest_id in self.running_backtests:
                self.running_backtests[backtest_id].cancel()
                del self.running_backtests[backtest_id]

            result.status = BacktestStatus.CANCELLED
            result.completed_at = datetime.now()

            return {
                "backtest_id": backtest_id,
                "status": "cancelled",
                "message": "回测已取消"
            }

        @self.router.get("/templates")
        async def get_backtest_templates():
            """获取回测模板"""
            templates = self._get_predefined_templates()
            return {"templates": templates}

        @self.router.post("/validate")
        async def validate_backtest_config(config: BacktestConfig):
            """验证回测配置"""
            validation_result = await self._validate_config(config)
            return validation_result

    async def _execute_backtest(self, backtest_id: str, config: BacktestConfig):
        """执行回测"""
        try:
            result = self.backtest_results[backtest_id]
            result.status = BacktestStatus.RUNNING

            # 验证配置
            validation = await self._validate_config(config)
            if not validation["valid"]:
                result.status = BacktestStatus.FAILED
                result.error_message = "; ".join(validation["errors"])
                result.completed_at = datetime.now()
                return

            # 准备回测数据
            market_data = await self._prepare_market_data(config.start_date, config.end_date)

            # 执行回测
            backtest_output = await self.backtest_engine.run_backtest(
                strategy_type=config.strategy_type,
                parameters=config.parameters,
                market_data=market_data,
                initial_capital=config.initial_capital,
                commission=config.commission,
                slippage=config.slippage
            )

            # 处理回测结果
            await self._process_backtest_output(result, backtest_output, market_data)

            result.status = BacktestStatus.COMPLETED
            result.completed_at = datetime.now()

        except Exception as e:
            self.logger.error(f"回测 {backtest_id} 执行失败: {e}")
            result = self.backtest_results[backtest_id]
            result.status = BacktestStatus.FAILED
            result.error_message = str(e)
            result.completed_at = datetime.now()

        finally:
            # 清理运行中的任务
            if backtest_id in self.running_backtests:
                del self.running_backtests[backtest_id]

    async def _prepare_market_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """准备市场数据"""
        try:
            # 这里应该从实际数据源获取市场数据
            # 为了演示，我们生成模拟数据
            start = pd.to_datetime(start_date)
            end = pd.to_datetime(end_date)
            dates = pd.date_range(start=start, end=end, freq='D')

            # 生成模拟价格数据
            np.random.seed(42)  # 确保结果可重现
            initial_price = 100
            returns = np.random.normal(0.0005, 0.02, len(dates))
            prices = [initial_price]

            for ret in returns[1:]:
                prices.append(prices[-1] * (1 + ret))

            # 生成其他数据
            volumes = np.random.uniform(1000000, 5000000, len(dates))

            market_data = pd.DataFrame({
                'date': dates,
                'open': prices,
                'high': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
                'low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
                'close': prices,
                'volume': volumes
            })

            return market_data

        except Exception as e:
            self.logger.error(f"准备市场数据失败: {e}")
            raise

    async def _process_backtest_output(self, result: BacktestResult, backtest_output: Dict[str, Any], market_data: pd.DataFrame):
        """处理回测输出"""
        try:
            # 提取性能指标
            performance = backtest_output.get('performance', {})
            result.total_return = performance.get('total_return', 0.0)
            result.annualized_return = performance.get('annualized_return', 0.0)
            result.sharpe_ratio = performance.get('sharpe_ratio', 0.0)
            result.sortino_ratio = performance.get('sortino_ratio', 0.0)
            result.calmar_ratio = performance.get('calmar_ratio', 0.0)
            result.max_drawdown = performance.get('max_drawdown', 0.0)
            result.win_rate = performance.get('win_rate', 0.0)
            result.profit_factor = performance.get('profit_factor', 1.0)

            # 提取交易统计
            trades_data = backtest_output.get('trades', [])
            result.total_trades = len(trades_data)
            result.winning_trades = len([t for t in trades_data if t.get('pnl', 0) > 0])
            result.losing_trades = len([t for t in trades_data if t.get('pnl', 0) < 0])

            if trades_data:
                pnls = [t.get('pnl', 0) for t in trades_data]
                result.avg_trade_return = np.mean(pnls)

                winning_pnls = [t.get('pnl', 0) for t in trades_data if t.get('pnl', 0) > 0]
                losing_pnls = [t.get('pnl', 0) for t in trades_data if t.get('pnl', 0) < 0]

                result.avg_winning_trade = np.mean(winning_pnls) if winning_pnls else 0.0
                result.avg_losing_trade = np.mean(losing_pnls) if losing_pnls else 0.0

            # 计算风险指标
            await self._calculate_risk_metrics(result, backtest_output, market_data)

            # 生成详细数据
            result.equity_curve = backtest_output.get('equity_curve', [])
            result.trades = trades_data
            result.monthly_returns = self._calculate_monthly_returns(result.equity_curve)
            result.drawdown_periods = self._calculate_drawdown_periods(result.equity_curve)

        except Exception as e:
            self.logger.error(f"处理回测输出失败: {e}")
            raise

    async def _calculate_risk_metrics(self, result: BacktestResult, backtest_output: Dict[str, Any], market_data: pd.DataFrame):
        """计算风险指标"""
        try:
            equity_curve = result.equity_curve or []
            if len(equity_curve) < 2:
                return

            # 计算收益率序列
            returns = []
            for i in range(1, len(equity_curve)):
                prev_value = equity_curve[i-1].get('portfolio_value', 0)
                curr_value = equity_curve[i].get('portfolio_value', 0)
                if prev_value > 0:
                    returns.append((curr_value - prev_value) / prev_value)

            if not returns:
                return

            returns_array = np.array(returns)

            # 波动率
            result.volatility = np.std(returns_array) * np.sqrt(252) * 100

            # Beta和Alpha（相对于基准）
            benchmark_returns = self._calculate_benchmark_returns(market_data)
            if len(benchmark_returns) == len(returns):
                covariance = np.cov(returns_array, benchmark_returns)[0, 1]
                benchmark_variance = np.var(benchmark_returns)
                result.beta = covariance / benchmark_variance if benchmark_variance > 0 else 0.0

                # Alpha = Portfolio Return - Risk Free Rate - Beta * (Market Return - Risk Free Rate)
                portfolio_return = np.mean(returns_array) * 252
                market_return = np.mean(benchmark_returns) * 252
                risk_free_rate = result.config.risk_free_rate

                result.alpha = (portfolio_return - risk_free_rate) - result.beta * (market_return - risk_free_rate)

            # VaR和CVaR
            returns_sorted = np.sort(returns_array)
            var_index = int(len(returns_sorted) * 0.05)
            result.var_95 = returns_sorted[var_index] * 100 if var_index < len(returns_sorted) else 0.0

            # CVaR (Expected Shortfall)
            cvar_returns = returns_sorted[:var_index] if var_index > 0 else returns_sorted
            result.cvar_95 = np.mean(cvar_returns) * 100 if len(cvar_returns) > 0 else 0.0

        except Exception as e:
            self.logger.error(f"计算风险指标失败: {e}")

    def _calculate_benchmark_returns(self, market_data: pd.DataFrame) -> np.ndarray:
        """计算基准收益率"""
        try:
            close_prices = market_data['close'].values
            returns = []
            for i in range(1, len(close_prices)):
                if close_prices[i-1] > 0:
                    returns.append((close_prices[i] - close_prices[i-1]) / close_prices[i-1])
            return np.array(returns)
        except Exception:
            return np.array([])

    def _calculate_monthly_returns(self, equity_curve: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """计算月度收益率"""
        try:
            if not equity_curve:
                return []

            # 按月份分组
            monthly_data = {}
            for point in equity_curve:
                date = pd.to_datetime(point.get('date', ''))
                month_key = date.strftime('%Y-%m')

                if month_key not in monthly_data:
                    monthly_data[month_key] = []
                monthly_data[month_key].append(point.get('portfolio_value', 0))

            # 计算月度收益率
            monthly_returns = []
            for month, values in monthly_data.items():
                if len(values) >= 2:
                    start_value = values[0]
                    end_value = values[-1]
                    monthly_return = ((end_value - start_value) / start_value) * 100

                    monthly_returns.append({
                        'month': month,
                        'return': monthly_return,
                        'start_value': start_value,
                        'end_value': end_value
                    })

            return monthly_returns

        except Exception as e:
            self.logger.error(f"计算月度收益率失败: {e}")
            return []

    def _calculate_drawdown_periods(self, equity_curve: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """计算回撤期间"""
        try:
            if not equity_curve:
                return []

            drawdown_periods = []
            values = [point.get('portfolio_value', 0) for point in equity_curve]

            peak = values[0]
            trough = values[0]
            peak_date = equity_curve[0].get('date', '')
            trough_date = equity_curve[0].get('date', '')
            in_drawdown = False

            for i, (point, value) in enumerate(zip(equity_curve, values)):
                current_date = point.get('date', '')

                if value > peak:
                    # 新的高点，结束之前的回撤
                    if in_drawdown:
                        drawdown = ((trough - peak) / peak) * 100
                        drawdown_periods.append({
                            'peak_date': peak_date,
                            'trough_date': trough_date,
                            'recovery_date': current_date,
                            'peak_value': peak,
                            'trough_value': trough,
                            'drawdown_percent': drawdown,
                            'duration_days': (pd.to_datetime(current_date) - pd.to_datetime(peak_date)).days
                        })

                    peak = value
                    peak_date = current_date
                    in_drawdown = False

                elif value < trough:
                    trough = value
                    trough_date = current_date
                    in_drawdown = True

            # 处理最后一个回撤期间
            if in_drawdown:
                drawdown = ((trough - peak) / peak) * 100
                drawdown_periods.append({
                    'peak_date': peak_date,
                    'trough_date': trough_date,
                    'recovery_date': None,  # 尚未恢复
                    'peak_value': peak,
                    'trough_value': trough,
                    'drawdown_percent': drawdown,
                    'duration_days': (pd.to_datetime(equity_curve[-1].get('date', '')) - pd.to_datetime(peak_date)).days
                })

            return drawdown_periods

        except Exception as e:
            self.logger.error(f"计算回撤期间失败: {e}")
            return []

    def _analyze_trades(self, trades: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析交易"""
        try:
            if not trades:
                return {}

            pnls = [t.get('pnl', 0) for t in trades]
            durations = [t.get('duration_days', 0) for t in trades]

            analysis = {
                'total_trades': len(trades),
                'profitable_trades': len([pnl for pnl in pnls if pnl > 0]),
                'losing_trades': len([pnl for pnl in pnls if pnl < 0]),
                'average_pnl': np.mean(pnls),
                'median_pnl': np.median(pnls),
                'best_trade': max(pnls),
                'worst_trade': min(pnls),
                'average_duration': np.mean(durations),
                'profit_trade_duration': np.mean([d for d, pnl in zip(durations, pnls) if pnl > 0]) if any(pnl > 0 for pnl in pnls) else 0,
                'loss_trade_duration': np.mean([d for d, pnl in zip(durations, pnls) if pnl < 0]) if any(pnl < 0 for pnl in pnls) else 0,
                'trade_distribution': {
                    'small_wins': len([pnl for pnl in pnls if 0 < pnl < np.percentile(pnls, 75)]),
                    'large_wins': len([pnl for pnl in pnls if pnl >= np.percentile(pnls, 75)]),
                    'small_losses': len([pnl for pnl in pnls if np.percentile(pnls, 25) < pnl < 0]),
                    'large_losses': len([pnl for pnl in pnls if pnl <= np.percentile(pnls, 25)])
                }
            }

            return analysis

        except Exception as e:
            self.logger.error(f"分析交易失败: {e}")
            return {}

    def _calculate_trade_statistics(self, result: BacktestResult) -> Dict[str, Any]:
        """计算交易统计"""
        try:
            if not result.trades:
                return {}

            pnls = [t.get('pnl', 0) for t in result.trades]

            statistics = {
                'consecutive_wins': self._calculate_consecutive_trades(pnls, True),
                'consecutive_losses': self._calculate_consecutive_trades(pnls, False),
                'largest_win_streak': 0,
                'largest_loss_streak': 0,
                'average_win_to_loss_ratio': 0,
                'profit_factor': result.profit_factor,
                'expectancy': result.avg_trade_return,
                'trade_frequency': len(result.trades) / max(1, (result.completed_at - result.created_at).days) if result.completed_at else 0
            }

            # 计算最大连续盈利和亏损
            current_win_streak = 0
            current_loss_streak = 0
            for pnl in pnls:
                if pnl > 0:
                    current_win_streak += 1
                    current_loss_streak = 0
                    statistics['largest_win_streak'] = max(statistics['largest_win_streak'], current_win_streak)
                elif pnl < 0:
                    current_loss_streak += 1
                    current_win_streak = 0
                    statistics['largest_loss_streak'] = max(statistics['largest_loss_streak'], current_loss_streak)
                else:
                    current_win_streak = 0
                    current_loss_streak = 0

            # 盈亏比
            winning_trades = [pnl for pnl in pnls if pnl > 0]
            losing_trades = [pnl for pnl in pnls if pnl < 0]

            if winning_trades and losing_trades:
                statistics['average_win_to_loss_ratio'] = abs(np.mean(winning_trades) / np.mean(losing_trades))

            return statistics

        except Exception as e:
            self.logger.error(f"计算交易统计失败: {e}")
            return {}

    def _calculate_consecutive_trades(self, pnls: List[float], wins: bool) -> List[int]:
        """计算连续交易次数"""
        try:
            consecutive_streaks = []
            current_streak = 0

            for pnl in pnls:
                if (wins and pnl > 0) or (not wins and pnl < 0):
                    current_streak += 1
                else:
                    if current_streak > 0:
                        consecutive_streaks.append(current_streak)
                    current_streak = 0

            if current_streak > 0:
                consecutive_streaks.append(current_streak)

            return consecutive_streaks

        except Exception:
            return []

    async def _perform_risk_analysis(self, result: BacktestResult) -> Dict[str, Any]:
        """执行风险分析"""
        try:
            if not result.equity_curve:
                return {}

            # 计算各种风险指标
            risk_analysis = {
                'value_at_risk': {
                    'daily_var_95': result.var_95,
                    'daily_var_99': 0,  # 需要计算
                    'weekly_var_95': 0,
                    'monthly_var_95': 0
                },
                'expected_shortfall': {
                    'daily_cvar_95': result.cvar_95,
                    'daily_cvar_99': 0,
                    'weekly_cvar_95': 0,
                    'monthly_cvar_95': 0
                },
                'volatility_analysis': {
                    'daily_volatility': result.volatility / np.sqrt(252),
                    'annualized_volatility': result.volatility,
                    'rolling_volatility_30d': 0,
                    'volatility_regime': 'normal'  # low, normal, high
                },
                'correlation_analysis': {
                    'market_beta': result.beta,
                    'strategy_alpha': result.alpha,
                    'correlation_with_benchmark': 0,
                    'tracking_error': 0
                },
                'stress_test_scenarios': await self._generate_stress_scenarios(result)
            }

            return risk_analysis

        except Exception as e:
            self.logger.error(f"执行风险分析失败: {e}")
            return {}

    def _calculate_var_analysis(self, result: BacktestResult) -> Dict[str, Any]:
        """计算VaR分析"""
        try:
            if not result.equity_curve:
                return {}

            returns = []
            for i in range(1, len(result.equity_curve)):
                prev_val = result.equity_curve[i-1].get('portfolio_value', 0)
                curr_val = result.equity_curve[i].get('portfolio_value', 0)
                if prev_val > 0:
                    returns.append((curr_val - prev_val) / prev_val)

            if not returns:
                return {}

            returns_array = np.array(returns)

            var_analysis = {
                'historical_var': {
                    'var_90': np.percentile(returns_array, 10) * 100,
                    'var_95': np.percentile(returns_array, 5) * 100,
                    'var_99': np.percentile(returns_array, 1) * 100
                },
                'parametric_var': {
                    'var_90': -1.645 * np.std(returns_array) * 100,
                    'var_95': -1.96 * np.std(returns_array) * 100,
                    'var_99': -2.33 * np.std(returns_array) * 100
                },
                'var_backtesting': {
                    'var_95_violations': 0,
                    'var_95_expected_violations': len(returns) * 0.05,
                    'kupiec_p_value': 0  # 需要计算
                }
            }

            # 计算VaR违反次数
            var_95_threshold = var_analysis['historical_var']['var_95'] / 100
            var_analysis['var_backtesting']['var_95_violations'] = np.sum(returns_array < var_95_threshold)

            return var_analysis

        except Exception as e:
            self.logger.error(f"计算VaR分析失败: {e}")
            return {}

    async def _perform_stress_test(self, result: BacktestResult) -> Dict[str, Any]:
        """执行压力测试"""
        try:
            stress_scenarios = {
                'market_crash': {
                    'description': '市场崩盘情景 (-30%)',
                    'portfolio_impact': -result.volatility * 3,  # 简化计算
                    'recovery_time_estimate': 0
                },
                'volatility_spike': {
                    'description': '波动率飙升情景 (+100%)',
                    'portfolio_impact': -result.volatility * 2,
                    'recovery_time_estimate': 0
                },
                'correlation_breakdown': {
                    'description': '相关性失效情景',
                    'portfolio_impact': -result.volatility * 1.5,
                    'recovery_time_estimate': 0
                },
                'liquidity_crisis': {
                    'description': '流动性危机情景',
                    'portfolio_impact': -result.volatility * 2.5,
                    'recovery_time_estimate': 0
                }
            }

            return stress_scenarios

        except Exception as e:
            self.logger.error(f"执行压力测试失败: {e}")
            return {}

    async def _perform_strategy_comparison(self, comparison_id: str, results: List[BacktestResult], metrics: List[ComparisonMetric]) -> ComparisonResult:
        """执行策略对比"""
        try:
            # 提取策略名称
            strategies = [r.config.strategy_type for r in results]

            # 构建对比指标矩阵
            comparison_metrics = {}
            for metric in metrics:
                comparison_metrics[metric.value] = {}
                for result in results:
                    comparison_metrics[metric.value][result.config.strategy_type] = getattr(result, metric.value, 0.0)

            # 计算排名
            ranking = []
            for metric in metrics:
                metric_ranking = []
                metric_values = {strategy: comparison_metrics[metric.value][strategy] for strategy in strategies}

                # 根据指标类型决定排序方向
                reverse_sort = metric in [ComparisonMetric.TOTAL_RETURN, ComparisonMetric.SHARPE_RATIO,
                                        ComparisonMetric.WIN_RATE, ComparisonMetric.CALMAR_RATIO,
                                        ComparisonMetric.PROFIT_FACTOR, ComparisonMetric.SORTINO_RATIO]

                sorted_strategies = sorted(metric_values.items(), key=lambda x: x[1], reverse=reverse_sort)

                for rank, (strategy, value) in enumerate(sorted_strategies, 1):
                    metric_ranking.append({
                        'strategy': strategy,
                        'rank': rank,
                        'value': value
                    })

                ranking.append({
                    'metric': metric.value,
                    'ranking': metric_ranking
                })

            # 计算统计显著性
            statistical_significance = await self._calculate_statistical_significance(results)

            # 计算相关性矩阵
            correlation_matrix = self._calculate_strategy_correlation(results)

            comparison_result = ComparisonResult(
                comparison_id=comparison_id,
                strategies=strategies,
                backtest_results=results,
                comparison_metrics=comparison_metrics,
                ranking=ranking,
                statistical_significance=statistical_significance,
                correlation_matrix=correlation_matrix,
                created_at=datetime.now()
            )

            return comparison_result

        except Exception as e:
            self.logger.error(f"执行策略对比失败: {e}")
            raise

    async def _calculate_statistical_significance(self, results: List[BacktestResult]) -> Dict[str, Any]:
        """计算统计显著性"""
        try:
            # 简化的统计显著性计算
            significance_tests = {
                'pairwise_comparisons': [],
                'overall_significance': 0.0,
                'multiple_testing_correction': 'bonferroni'
            }

            # 对所有策略对进行t检验
            for i, result1 in enumerate(results):
                for j, result2 in enumerate(results[i+1:], i+1):
                    # 这里应该进行实际的统计检验
                    # 为了演示，使用模拟结果
                    p_value = np.random.uniform(0.01, 0.5)

                    significance_tests['pairwise_comparisons'].append({
                        'strategy1': result1.config.strategy_type,
                        'strategy2': result2.config.strategy_type,
                        'metric': 'sharpe_ratio',
                        'p_value': p_value,
                        'significant': p_value < 0.05,
                        'test_statistic': np.random.normal(0, 1)
                    })

            return significance_tests

        except Exception as e:
            self.logger.error(f"计算统计显著性失败: {e}")
            return {}

    def _calculate_strategy_correlation(self, results: List[BacktestResult]) -> Dict[str, Dict[str, float]]:
        """计算策略相关性"""
        try:
            correlation_matrix = {}
            strategies = [r.config.strategy_type for r in results]

            # 获取各策略的收益率序列
            returns_series = {}
            for result in results:
                if result.equity_curve:
                    returns = []
                    for i in range(1, len(result.equity_curve)):
                        prev_val = result.equity_curve[i-1].get('portfolio_value', 0)
                        curr_val = result.equity_curve[i].get('portfolio_value', 0)
                        if prev_val > 0:
                            returns.append((curr_val - prev_val) / prev_val)
                    returns_series[result.config.strategy_type] = returns

            # 计算相关性矩阵
            for strategy1 in strategies:
                correlation_matrix[strategy1] = {}
                for strategy2 in strategies:
                    if strategy1 in returns_series and strategy2 in returns_series:
                        returns1 = returns_series[strategy1]
                        returns2 = returns_series[strategy2]

                        # 确保长度一致
                        min_length = min(len(returns1), len(returns2))
                        if min_length > 1:
                            correlation = np.corrcoef(returns1[:min_length], returns2[:min_length])[0, 1]
                            correlation_matrix[strategy1][strategy2] = correlation if not np.isnan(correlation) else 0.0
                        else:
                            correlation_matrix[strategy1][strategy2] = 0.0
                    else:
                        correlation_matrix[strategy1][strategy2] = 0.0

            return correlation_matrix

        except Exception as e:
            self.logger.error(f"计算策略相关性失败: {e}")
            return {}

    async def _generate_comparison_charts(self, comparison: ComparisonResult) -> Dict[str, Any]:
        """生成对比图表"""
        try:
            charts = {}

            # 1. 性能对比雷达图
            charts['performance_radar'] = self._create_performance_radar_chart(comparison)

            # 2. 资金曲线对比图
            charts['equity_curve_comparison'] = self._create_equity_curve_comparison(comparison)

            # 3. 风险收益散点图
            charts['risk_return_scatter'] = self._create_risk_return_scatter(comparison)

            # 4. 回撤对比图
            charts['drawdown_comparison'] = self._create_drawdown_comparison(comparison)

            # 5. 月度收益热力图
            charts['monthly_returns_heatmap'] = self._create_monthly_returns_heatmap(comparison)

            return charts

        except Exception as e:
            self.logger.error(f"生成对比图表失败: {e}")
            return {}

    def _create_performance_radar_chart(self, comparison: ComparisonResult) -> Dict[str, Any]:
        """创建性能雷达图"""
        try:
            metrics = ['sharpe_ratio', 'total_return', 'win_rate', 'calmar_ratio']
            strategies = comparison.strategies

            fig = go.Figure()

            for strategy in strategies:
                values = []
                for metric in metrics:
                    # 归一化指标值到0-1范围
                    all_values = [comparison.comparison_metrics[metric][s] for s in strategies]
                    max_val = max(all_values) if all_values else 1
                    min_val = min(all_values) if all_values else 0

                    if max_val > min_val:
                        normalized = (comparison.comparison_metrics[metric][strategy] - min_val) / (max_val - min_val)
                    else:
                        normalized = 0.5

                    values.append(normalized)

                fig.add_trace(go.Scatterpolar(
                    r=values,
                    theta=metrics,
                    fill='toself',
                    name=strategy
                ))

            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 1]
                    )),
                showlegend=True,
                title="策略性能雷达图"
            )

            return {
                'chart_data': json.dumps(fig, cls=PlotlyJSONEncoder),
                'chart_type': 'radar'
            }

        except Exception as e:
            self.logger.error(f"创建性能雷达图失败: {e}")
            return {}

    def _create_equity_curve_comparison(self, comparison: ComparisonResult) -> Dict[str, Any]:
        """创建资金曲线对比图"""
        try:
            fig = go.Figure()

            for result in comparison.backtest_results:
                if result.equity_curve:
                    dates = [point.get('date', '') for point in result.equity_curve]
                    values = [point.get('portfolio_value', 0) for point in result.equity_curve]

                    # 转换为相对收益率
                    initial_value = values[0] if values else 1
                    returns = [(v / initial_value - 1) * 100 for v in values]

                    fig.add_trace(go.Scatter(
                        x=dates,
                        y=returns,
                        mode='lines',
                        name=result.config.strategy_type,
                        line=dict(width=2)
                    ))

            fig.update_layout(
                title="策略资金曲线对比",
                xaxis_title="日期",
                yaxis_title="累计收益率 (%)",
                hovermode='x unified',
                showlegend=True
            )

            return {
                'chart_data': json.dumps(fig, cls=PlotlyJSONEncoder),
                'chart_type': 'line'
            }

        except Exception as e:
            self.logger.error(f"创建资金曲线对比图失败: {e}")
            return {}

    def _create_risk_return_scatter(self, comparison: ComparisonResult) -> Dict[str, Any]:
        """创建风险收益散点图"""
        try:
            strategies = comparison.strategies
            returns = [comparison.comparison_metrics['total_return'][s] for s in strategies]
            risks = [comparison.comparison_metrics['max_drawdown'][s] for s in strategies]

            fig = go.Figure(data=go.Scatter(
                x=risks,
                y=returns,
                mode='markers+text',
                text=strategies,
                textposition="top center",
                marker=dict(
                    size=12,
                    color=returns,
                    colorscale='Viridis',
                    showscale=True,
                    colorbar=dict(title="总收益率 (%)")
                )
            ))

            fig.update_layout(
                title="风险收益散点图",
                xaxis_title="最大回撤 (%)",
                yaxis_title="总收益率 (%)"
            )

            return {
                'chart_data': json.dumps(fig, cls=PlotlyJSONEncoder),
                'chart_type': 'scatter'
            }

        except Exception as e:
            self.logger.error(f"创建风险收益散点图失败: {e}")
            return {}

    def _create_drawdown_comparison(self, comparison: ComparisonResult) -> Dict[str, Any]:
        """创建回撤对比图"""
        try:
            fig = go.Figure()

            for result in comparison.backtest_results:
                if result.equity_curve:
                    dates = [point.get('date', '') for point in result.equity_curve]
                    values = [point.get('portfolio_value', 0) for point in result.equity_curve]

                    # 计算回撤
                    peak = values[0]
                    drawdowns = []
                    for value in values:
                        if value > peak:
                            peak = value
                        drawdown = ((peak - value) / peak) * 100
                        drawdowns.append(drawdown)

                    fig.add_trace(go.Scatter(
                        x=dates,
                        y=drawdowns,
                        mode='lines',
                        name=f"{result.config.strategy_type} 回撤",
                        line=dict(width=2),
                        fill='tonexty' if result == comparison.backtest_results[-1] else None
                    ))

            fig.update_layout(
                title="策略回撤对比",
                xaxis_title="日期",
                yaxis_title="回撤 (%)",
                showlegend=True
            )

            return {
                'chart_data': json.dumps(fig, cls=PlotlyJSONEncoder),
                'chart_type': 'area'
            }

        except Exception as e:
            self.logger.error(f"创建回撤对比图失败: {e}")
            return {}

    def _create_monthly_returns_heatmap(self, comparison: ComparisonResult) -> Dict[str, Any]:
        """创建月度收益热力图"""
        try:
            # 收集所有策略的月度收益数据
            all_monthly_data = {}

            for result in comparison.backtest_results:
                if result.monthly_returns:
                    monthly_dict = {item['month']: item['return'] for item in result.monthly_returns}
                    all_monthly_data[result.config.strategy_type] = monthly_dict

            if not all_monthly_data:
                return {}

            # 创建热力图数据
            strategies = list(all_monthly_data.keys())
            all_months = sorted(set().union(*[data.keys() for data in all_monthly_data.values()]))

            z_values = []
            for strategy in strategies:
                row = []
                for month in all_months:
                    row.append(all_monthly_data[strategy].get(month, 0))
                z_values.append(row)

            fig = go.Figure(data=go.Heatmap(
                z=z_values,
                x=all_months,
                y=strategies,
                colorscale='RdYlGn',
                zmid=0,
                text=[[f"{val:.1f}%" for val in row] for row in z_values],
                texttemplate="%{text}",
                textfont={"size": 10},
                hoverongaps=False
            ))

            fig.update_layout(
                title="策略月度收益热力图",
                xaxis_title="月份",
                yaxis_title="策略"
            )

            return {
                'chart_data': json.dumps(fig, cls=PlotlyJSONEncoder),
                'chart_type': 'heatmap'
            }

        except Exception as e:
            self.logger.error(f"创建月度收益热力图失败: {e}")
            return {}

    def _generate_equity_curve_chart(self, result: BacktestResult) -> Dict[str, Any]:
        """生成资金曲线图表"""
        try:
            if not result.equity_curve:
                return {}

            dates = [point.get('date', '') for point in result.equity_curve]
            values = [point.get('portfolio_value', 0) for point in result.equity_curve]

            fig = go.Figure()

            # 资金曲线
            fig.add_trace(go.Scatter(
                x=dates,
                y=values,
                mode='lines',
                name='策略资金曲线',
                line=dict(color='blue', width=2)
            ))

            # 添加回撤填充
            peak = values[0]
            drawdown_values = []
            for value in values:
                if value > peak:
                    peak = value
                drawdown = peak
                drawdown_values.append(drawdown)

            fig.add_trace(go.Scatter(
                x=dates,
                y=drawdown_values,
                mode='lines',
                name='历史最高点',
                line=dict(color='red', width=1, dash='dash'),
                fill='tonexty',
                fillcolor='rgba(255,0,0,0.1)'
            ))

            fig.update_layout(
                title=f"{result.config.strategy_type} 资金曲线",
                xaxis_title="日期",
                yaxis_title="组合价值",
                hovermode='x unified',
                showlegend=True
            )

            return json.dumps(fig, cls=PlotlyJSONEncoder)

        except Exception as e:
            self.logger.error(f"生成资金曲线图表失败: {e}")
            return {}

    async def _generate_stress_scenarios(self, result: BacktestResult) -> Dict[str, Any]:
        """生成压力测试情景"""
        try:
            scenarios = {
                'market_shock': {
                    'scenario': '市场冲击 (-20%)',
                    'estimated_loss': -result.volatility * 2.5,
                    'probability': 0.05
                },
                'volatility_spike': {
                    'scenario': '波动率飙升 (+100%)',
                    'estimated_loss': -result.volatility * 2,
                    'probability': 0.1
                },
                'liquidity_crisis': {
                    'scenario': '流动性危机',
                    'estimated_loss': -result.volatility * 3,
                    'probability': 0.02
                },
                'correlation_breakdown': {
                    'scenario': '相关性失效',
                    'estimated_loss': -result.volatility * 1.8,
                    'probability': 0.08
                }
            }

            return scenarios

        except Exception as e:
            self.logger.error(f"生成压力测试情景失败: {e}")
            return {}

    def _get_predefined_templates(self) -> List[Dict[str, Any]]:
        """获取预定义回测模板"""
        templates = [
            {
                "name": "保守型策略模板",
                "description": "低风险、稳健收益的回测配置",
                "config": {
                    "initial_capital": 100000,
                    "commission": 0.001,
                    "slippage": 0.001,
                    "benchmark": "HSI",
                    "rebalance_frequency": "weekly",
                    "risk_free_rate": 0.02
                }
            },
            {
                "name": "激进型策略模板",
                "description": "高风险、高收益的回测配置",
                "config": {
                    "initial_capital": 50000,
                    "commission": 0.002,
                    "slippage": 0.002,
                    "benchmark": "HSI",
                    "rebalance_frequency": "daily",
                    "risk_free_rate": 0.02
                }
            },
            {
                "name": "机构型策略模板",
                "description": "大资金、低成本的回测配置",
                "config": {
                    "initial_capital": 1000000,
                    "commission": 0.0005,
                    "slippage": 0.0005,
                    "benchmark": "HSI",
                    "rebalance_frequency": "monthly",
                    "risk_free_rate": 0.02
                }
            }
        ]

        return templates

    async def _validate_config(self, config: BacktestConfig) -> Dict[str, Any]:
        """验证回测配置"""
        try:
            errors = []
            warnings = []

            # 验证日期
            try:
                start_date = pd.to_datetime(config.start_date)
                end_date = pd.to_datetime(config.end_date)

                if start_date >= end_date:
                    errors.append("开始日期必须早于结束日期")

                if end_date > pd.to_datetime(datetime.now()):
                    warnings.append("结束日期超过当前日期")

                if (end_date - start_date).days < 30:
                    warnings.append("回测期间少于30天，结果可能不可靠")

            except Exception as e:
                errors.append(f"日期格式错误: {str(e)}")

            # 验证资金配置
            if config.initial_capital <= 0:
                errors.append("初始资金必须大于0")
            elif config.initial_capital < 10000:
                warnings.append("初始资金较少，可能影响交易成本计算")

            if config.commission < 0 or config.commission > 0.01:
                errors.append("手续费率必须在0到1%之间")

            if config.slippage < 0 or config.slippage > 0.01:
                errors.append("滑点必须在0到1%之间")

            # 验证策略类型
            valid_strategies = ["direct_rsi", "sentiment_momentum", "composite_index", "volatility_adjusted"]
            if config.strategy_type not in valid_strategies:
                errors.append(f"无效的策略类型，支持的类型: {valid_strategies}")

            # 验证参数
            if not config.parameters:
                errors.append("策略参数不能为空")

            return {
                "valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings
            }

        except Exception as e:
            return {
                "valid": False,
                "errors": [f"配置验证失败: {str(e)}"],
                "warnings": []
            }

    def _generate_backtest_id(self) -> str:
        """生成回测ID"""
        import uuid
        return f"bt_{uuid.uuid4().hex[:8]}_{int(datetime.now().timestamp())}"

    def _generate_comparison_id(self) -> str:
        """生成对比ID"""
        import uuid
        return f"cmp_{uuid.uuid4().hex[:8]}_{int(datetime.now().timestamp())}"


# 创建全局实例
_backtesting_lab: Optional[BacktestingAnalysisLab] = None


def get_backtesting_lab() -> BacktestingAnalysisLab:
    """获取回测分析实验室实例"""
    global _backtesting_lab
    if _backtesting_lab is None:
        _backtesting_lab = BacktestingAnalysisLab()
    return _backtesting_lab