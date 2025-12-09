#!/usr/bin/env python3
"""
VectorBT API路由
为前端提供VectorBT集成接口
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from ..data.vectorbt_adapter import VectorBTDataAdapter
from ..indicators.vectorbt_indicators import (
    EconomicTechnicalIndicators,
    VectorBTTechnicalIndicators,
)
from ..performance.parallel_optimizer import OptimizationConfig, ParallelOptimizer
from ..performance.vectorbt_engine import BacktestConfig, VectorBTComputeEngine
from ..strategy.hybrid_signals import HybridSignalFramework, SignalConfig

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/api/vectorbt", tags=["VectorBT"])

# 全局实例
vectorbt_adapter = VectorBTDataAdapter()
hybrid_framework = HybridSignalFramework()
vectorbt_engine = VectorBTComputeEngine()
technical_indicators = VectorBTTechnicalIndicators()
economic_indicators = EconomicTechnicalIndicators()

# WebSocket连接管理
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # 连接已断开，移除
                self.active_connections.remove(connection)

manager = ConnectionManager()

# Pydantic模型
class SignalRequest(BaseModel):
    symbols: List[str] = Field(..., description="股票代码列表")
    start_date: str = Field(..., description="开始日期 (YYYY-MM-DD)")
    end_date: str = Field(..., description="结束日期 (YYYY-MM-DD)")
    signal_config: Optional[Dict[str, Any]] = Field(default=None, description="信号配置")

class BacktestRequest(BaseModel):
    symbols: List[str] = Field(..., description="股票代码列表")
    start_date: str = Field(..., description="开始日期 (YYYY-MM-DD)")
    end_date: str = Field(..., description="结束日期 (YYYY-MM-DD)")
    initial_cash: float = Field(default=100000, description="初始资金")
    fees: float = Field(default=0.001, description="手续费率")
    slippage: float = Field(default=0.001, description="滑点")

class OptimizationRequest(BaseModel):
    symbols: List[str] = Field(..., description="股票代码列表")
    start_date: str = Field(..., description="开始日期 (YYYY-MM-DD)")
    end_date: str = Field(..., description="结束日期 (YYYY-MM-DD)")
    param_grid: Dict[str, List[Any]] = Field(..., description="参数网格")
    optimization_config: Optional[Dict[str, Any]] = Field(default=None, description="优化配置")

# API端点
@router.get("/symbols")
async def get_available_symbols():
    """获取可用股票列表"""
    try:
        # 这里应该从实际数据源获取
        # 暂时返回示例数据
        symbols = [
            "0700.HK", "0005.HK", "1398.HK", "0941.HK", "2318.HK",
            "1299.HK", "0388.HK", "0883.HK", "0885.HK", "1810.HK"
        ]

        return {
            "symbols": symbols,
            "count": len(symbols),
            "updated_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"获取股票列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/signals")
async def generate_signals(request: SignalRequest):
    """生成混合信号"""
    try:
        start_date = datetime.strptime(request.start_date, "%Y-%m-%d")
        end_date = datetime.strptime(request.end_date, "%Y-%m-%d")

        # 配置信号参数
        signal_config = SignalConfig()
        if request.signal_config:
            signal_config = SignalConfig(**request.signal_config)

        hybrid_framework.config = signal_config

        results = {}

        for symbol in request.symbols:
            try:
                # 获取数据
                vbt_data = await vectorbt_adapter.get_vectorbt_data(
                    symbol, start_date, end_date
                )

                if vbt_data["price"].empty:
                    logger.warning(f"获取 {symbol} 数据失败")
                    continue

                # 生成信号
                signal_result = await hybrid_framework.generate_hybrid_signals(
                    symbol,
                    vbt_data["price"],
                    vbt_data["economic"],
                    start_date,
                    end_date
                )

                # 转换为JSON可序列化格式
                results[symbol] = {
                    "signals": signal_result.signals.fillna(0).to_dict('records'),
                    "quality_score": signal_result.quality_score,
                    "regime": signal_result.regime.value,
                    "weights": signal_result.weights,
                    "performance_metrics": signal_result.performance_metrics,
                    "signal_interpretation": hybrid_framework.get_signal_interpretation(
                        signal_result.signals
                    )
                }

            except Exception as e:
                logger.error(f"生成 {symbol} 信号失败: {e}")
                results[symbol] = {"error": str(e)}

        return {
            "symbols": request.symbols,
            "signals": results,
            "generated_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"生成信号失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/signals/{symbol}")
async def get_symbol_signals(symbol: str,
                           start_date: str = None,
                           end_date: str = None,
                           signal_type: str = "hybrid"):
    """获取单个股票的信号"""
    try:
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")

        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")

        # 获取数据
        vbt_data = await vectorbt_adapter.get_vectorbt_data(symbol, start_dt, end_dt)

        if vbt_data["price"].empty:
            raise HTTPException(status_code=404, detail=f"未找到 {symbol} 的数据")

        # 生成信号
        signal_result = await hybrid_framework.generate_hybrid_signals(
            symbol, vbt_data["price"], vbt_data["economic"], start_dt, end_dt
        )

        # 根据信号类型返回数据
        signals_df = signal_result.signals
        if signal_type == "price":
            signals_df = signals_df[[col for col in signals_df.columns if 'price' in col or any(
                indicator in col for indicator in ['rsi', 'macd', 'bb_', 'adx', 'cci', 'stoch', 'atr']
            )]]
        elif signal_type == "economic":
            signals_df = signals_df[[col for col in signals_df.columns if any(
                econ in col for econ in ['hibor', 'gdp', 'trade', 'cpi', 'unemployment']
            )]]

        return {
            "symbol": symbol,
            "signal_type": signal_type,
            "signals": signals_df.fillna(0).to_dict('records'),
            "quality_score": signal_result.quality_score,
            "regime": signal_result.regime.value,
            "weights": signal_result.weights,
            "performance_metrics": signal_result.performance_metrics,
            "signal_interpretation": hybrid_framework.get_signal_interpretation(signal_result.signals),
            "updated_at": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取 {symbol} 信号失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/backtest")
async def run_backtest(request: BacktestRequest):
    """运行回测"""
    try:
        start_date = datetime.strptime(request.start_date, "%Y-%m-%d")
        end_date = datetime.strptime(request.end_date, "%Y-%m-%d")

        # 配置回测参数
        backtest_config = BacktestConfig(
            start_date=start_date,
            end_date=end_date,
            initial_cash=request.initial_cash,
            fees=request.fees,
            slippage=request.slippage
        )

        # 获取数据和信号
        price_data = {}
        signals = {}

        for symbol in request.symbols:
            try:
                vbt_data = await vectorbt_adapter.get_vectorbt_data(
                    symbol, start_date, end_date
                )

                if not vbt_data["price"].empty:
                    price_data[symbol] = vbt_data["price"]

                    # 生成信号
                    signal_result = await hybrid_framework.generate_hybrid_signals(
                        symbol, vbt_data["price"], vbt_data["economic"], start_date, end_date
                    )

                    if not signal_result.signals.empty:
                        signals[symbol] = signal_result.signals

            except Exception as e:
                logger.error(f"获取 {symbol} 数据失败: {e}")
                continue

        if not price_data or not signals:
            raise HTTPException(status_code=400, detail="没有有效的数据或信号")

        # 运行回测
        backtest_results = vectorbt_engine.vectorized_backtest(
            request.symbols, price_data, signals, backtest_config
        )

        # 转换结果格式
        results = {}
        for symbol, result in backtest_results.items():
            results[symbol] = {
                "equity_curve": result.equity_curve.fillna(0).to_dict(),
                "trades": result.trades.fillna(0).to_dict('records'),
                "metrics": result.metrics,
                "execution_time": result.execution_time,
                "benchmark_metrics": result.benchmark_metrics or {}
            }

        # 生成汇总报告
        summary = _generate_backtest_summary(backtest_results)

        return {
            "symbols": request.symbols,
            "backtest_config": {
                "start_date": request.start_date,
                "end_date": request.end_date,
                "initial_cash": request.initial_cash,
                "fees": request.fees,
                "slippage": request.slippage
            },
            "results": results,
            "summary": summary,
            "executed_at": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"回测失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/backtest/{symbol}")
async def get_symbol_backtest(symbol: str,
                             start_date: str = None,
                             end_date: str = None):
    """获取单个股票的回测结果"""
    try:
        if not start_date:
            start_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")

        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")

        backtest_config = BacktestConfig(
            start_date=start_dt,
            end_date=end_dt
        )

        # 获取数据和信号
        vbt_data = await vectorbt_adapter.get_vectorbt_data(symbol, start_dt, end_dt)

        if vbt_data["price"].empty:
            raise HTTPException(status_code=404, detail=f"未找到 {symbol} 的数据")

        signal_result = await hybrid_framework.generate_hybrid_signals(
            symbol, vbt_data["price"], vbt_data["economic"], start_dt, end_dt
        )

        # 运行回测
        backtest_results = vectorbt_engine.vectorized_backtest(
            [symbol], {symbol: vbt_data["price"]},
            {symbol: signal_result.signals}, backtest_config
        )

        if symbol not in backtest_results:
            raise HTTPException(status_code=500, detail="回测执行失败")

        result = backtest_results[symbol]

        return {
            "symbol": symbol,
            "equity_curve": result.equity_curve.fillna(0).to_dict(),
            "trades": result.trades.fillna(0).to_dict('records'),
            "metrics": result.metrics,
            "benchmark_metrics": result.benchmark_metrics or {},
            "execution_time": result.execution_time,
            "signal_quality": signal_result.quality_score,
            "executed_at": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取 {symbol} 回测结果失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/optimize")
async def run_optimization(request: OptimizationRequest):
    """运行参数优化"""
    try:
        start_date = datetime.strptime(request.start_date, "%Y-%m-%d")
        end_date = datetime.strptime(request.end_date, "%Y-%m-%d")

        # 配置优化参数
        optimization_config = OptimizationConfig()
        if request.optimization_config:
            optimization_config = OptimizationConfig(**request.optimization_config)

        backtest_config = BacktestConfig(
            start_date=start_date,
            end_date=end_date
        )

        # 获取数据
        price_data = {}
        economic_data = {}

        for symbol in request.symbols[:5]:  # 限制标的数量以提高速度
            try:
                vbt_data = await vectorbt_adapter.get_vectorbt_data(
                    symbol, start_date, end_date
                )

                if not vbt_data["price"].empty:
                    price_data[symbol] = vbt_data["price"]
                    economic_data.update(vbt_data["economic"])

            except Exception as e:
                logger.error(f"获取 {symbol} 数据失败: {e}")
                continue

        if not price_data:
            raise HTTPException(status_code=400, detail="没有有效的数据")

        # 创建并行优化器
        parallel_optimizer = ParallelOptimizer(optimization_config)

        # 运行优化
        optimization_results = parallel_optimizer.optimize_parameters_parallel(
            request.symbols, price_data, economic_data,
            request.param_grid, backtest_config
        )

        # 转换结果格式
        results = []
        for result in optimization_results:
            results.append({
                "parameters": result.parameters,
                "performance_metrics": result.performance_metrics,
                "sharpe_ratio": result.sharpe_ratio,
                "max_drawdown": result.max_drawdown,
                "total_return": result.total_return,
                "quality_score": result.quality_score,
                "execution_time": result.execution_time
            })

        # 生成优化报告
        report = _generate_optimization_report(optimization_results)

        return {
            "symbols": request.symbols,
            "param_grid": request.param_grid,
            "results": results,
            "report": report,
            "total_combinations": parallel_optimizer._count_combinations(request.param_grid),
            "execution_time": sum(r.execution_time for r in optimization_results),
            "optimized_at": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"参数优化失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/indicators/{symbol}")
async def get_technical_indicators(symbol: str,
                                 start_date: str = None,
                                 end_date: str = None):
    """获取技术指标"""
    try:
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")

        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")

        # 获取价格数据
        vbt_data = await vectorbt_adapter.get_vectorbt_data(symbol, start_dt, end_dt)

        if vbt_data["price"].empty:
            raise HTTPException(status_code=404, detail=f"未找到 {symbol} 的数据")

        # 计算技术指标
        price_indicators = technical_indicators.calculate_all_indicators(vbt_data["price"])
        economic_indicators_result = {}

        # 计算经济技术指标
        if vbt_data["economic"]:
            econ_signals = {}
            for source, df in vbt_data["economic"].items():
                if not df.empty and 'rate' in df.columns:
                    econ_signals[source] = df['rate']

            if econ_signals:
                economic_indicators_result = economic_indicators.composite_economic_signal(econ_signals)

        return {
            "symbol": symbol,
            "period": {
                "start_date": start_date,
                "end_date": end_date
            },
            "price_indicators": price_indicators.fillna(0).to_dict('records'),
            "economic_indicators": economic_indicators_result.fillna(0).to_dict() if not economic_indicators_result.empty else {},
            "updated_at": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取 {symbol} 技术指标失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket端点
@router.websocket("/ws/vectorbt")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # 处理WebSocket消息
            # 可以添加实时数据推送功能
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# 辅助函数
def _generate_backtest_summary(backtest_results: Dict[str, Any]) -> Dict[str, Any]:
    """生成回测汇总"""
    if not backtest_results:
        return {"status": "no_results"}

    all_metrics = [result.metrics for result in backtest_results.values()]
    sharpe_ratios = [m.get('sharpe_ratio', 0) for m in all_metrics]
    total_returns = [m.get('total_return', 0) for m in all_metrics]
    max_drawdowns = [m.get('max_drawdown', 0) for m in all_metrics]

    return {
        "total_strategies": len(backtest_results),
        "avg_sharpe_ratio": np.mean(sharpe_ratios) if sharpe_ratios else 0,
        "best_sharpe_ratio": max(sharpe_ratios) if sharpe_ratios else 0,
        "avg_total_return": np.mean(total_returns) if total_returns else 0,
        "best_total_return": max(total_returns) if total_returns else 0,
        "avg_max_drawdown": np.mean(max_drawdowns) if max_drawdowns else 0,
        "profitable_strategies": sum(1 for r in total_returns if r > 0)
    }

def _generate_optimization_report(optimization_results: List[Any]) -> Dict[str, Any]:
    """生成优化报告"""
    if not optimization_results:
        return {"status": "no_results"}

    quality_scores = [r.quality_score for r in optimization_results]
    sharpe_ratios = [r.sharpe_ratio for r in optimization_results]

    # 找到最佳参数
    best_result = max(optimization_results, key=lambda r: r.quality_score)

    return {
        "total_optimizations": len(optimization_results),
        "best_quality_score": max(quality_scores) if quality_scores else 0,
        "avg_quality_score": np.mean(quality_scores) if quality_scores else 0,
        "best_sharpe_ratio": max(sharpe_ratios) if sharpe_ratios else 0,
        "avg_sharpe_ratio": np.mean(sharpe_ratios) if sharpe_ratios else 0,
        "best_parameters": best_result.parameters,
        "best_performance": {
            "sharpe_ratio": best_result.sharpe_ratio,
            "max_drawdown": best_result.max_drawdown,
            "total_return": best_result.total_return,
            "quality_score": best_result.quality_score
        }
    }
