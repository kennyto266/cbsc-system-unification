#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 3: 完整回測引擎與報告生成系統
Phase 3: Complete Backtest Engine and Reporting System

專為0700.HK GPU加速量化交易設計的專業級回測引擎
包含完整的性能指標計算、風險分析、和HTML報告生成
"""

import numpy as np
import pandas as pd
import time
import logging
import json
import sys
import os
from typing import Dict, List, Optional, Union, Tuple, Any
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
from dataclasses import dataclass
from pathlib import Path

# 設置matplotlib中文字體
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class BacktestConfig:
    """回測配置"""
    initial_capital: float = 100000.0  # 初始資本 10萬港元
    risk_free_rate: float = 0.03      # 無風險利率 3%
    commission: float = 0.001         # 手續費 0.1%
    slippage: float = 0.0005          # 滑點 0.05%
    max_position_size: float = 1.0    # 最大倉位 100%
    stop_loss: float = 0.05           # 止損 5%
    take_profit: float = 0.10         # 止盈 10%

@dataclass
class PerformanceMetrics:
    """性能指標"""
    total_return: float = 0.0
    annual_return: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    calmar_ratio: float = 0.0
    sortino_ratio: float = 0.0
    total_trades: int = 0
    profitable_trades: int = 0
    losing_trades: int = 0
    avg_trade_return: float = 0.0
    volatility: float = 0.0
    beta: float = 0.0
    alpha: float = 0.0

class Phase3BacktestEngine:
    """Phase 3 完整回測引擎"""

    def __init__(self, gpu_device: int = 0, config: BacktestConfig = None):
        """初始化回測引擎"""
        self.gpu_device = gpu_device
        self.config = config or BacktestConfig()

        # 嘗試導入GPU模塊
        try:
            import cupy as cp
            self.gpu_available = True
            cp.cuda.Device(gpu_device).use()
            logger.info(f"GPU設備 {gpu_device} 初始化成功")
        except ImportError:
            self.gpu_available = False
            logger.info("使用CPU版本進行回測")
        except Exception as e:
            self.gpu_available = False
            logger.warning(f"GPU初始化失敗: {e}，使用CPU版本")

        # 導入Phase 2引擎
        try:
            from phase2_gpu_ta_engine_with_real_data import Phase2GPUBacktestEngine, RealGovDataLoader
            self.phase2_engine = Phase2GPUBacktestEngine(gpu_device)
            self.data_loader = RealGovDataLoader()
        except ImportError:
            logger.error("無法導入Phase 2引擎")
            self.phase2_engine = None
            self.data_loader = None

        # 初始化性能指標
        self.performance_metrics = PerformanceMetrics()

        # 存儲回測結果
        self.backtest_results = {}

        logger.info("Phase 3 完整回測引擎初始化完成")

    def calculate_returns(self, prices: np.ndarray, signals: np.ndarray) -> np.ndarray:
        """計算交易回報"""
        if len(prices) != len(signals):
            raise ValueError("價格和信號長度不匹配")

        # 計算日回報率
        daily_returns = np.diff(prices) / prices[:-1]

        # 應用交易信號
        position = np.zeros(len(signals))
        position[signals == 1] = 1   # 買入倉位
        position[signals == -1] = -1 # 賣出倉位

        # 計算交易回報
        trading_returns = daily_returns * position[:-1]

        return trading_returns

    def calculate_performance_metrics(self, prices: np.ndarray, signals: np.ndarray,
                                    benchmark_returns: np.ndarray = None) -> PerformanceMetrics:
        """計算完整的性能指標"""

        # 計算交易回報
        trading_returns = self.calculate_returns(prices, signals)

        # 基本回報指標
        total_return = np.prod(1 + trading_returns) - 1
        trading_days = len(trading_returns)
        annual_return = (1 + total_return) ** (252 / trading_days) - 1

        # 波動率
        volatility = np.std(trading_returns) * np.sqrt(252)

        # Sharpe比率 (使用3%無風險利率)
        excess_returns = trading_returns - self.config.risk_free_rate / 252
        sharpe_ratio = np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252) if np.std(excess_returns) > 0 else 0

        # 最大回撤
        cumulative_returns = np.cumprod(1 + trading_returns)
        peak = np.maximum.accumulate(cumulative_returns)
        drawdown = (cumulative_returns - peak) / peak
        max_drawdown = np.min(drawdown)

        # Calmar比率
        calmar_ratio = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0

        # Sortino比率 (只考慮下行波動率)
        downside_returns = trading_returns[trading_returns < 0]
        downside_volatility = np.std(downside_returns) * np.sqrt(252) if len(downside_returns) > 0 else 0
        sortino_ratio = (annual_return - self.config.risk_free_rate) / downside_volatility if downside_volatility > 0 else 0

        # 交易統計
        total_trades = np.sum(np.abs(np.diff(signals)) > 0)
        profitable_trades = np.sum(trading_returns > 0)
        losing_trades = np.sum(trading_returns < 0)
        win_rate = profitable_trades / total_trades if total_trades > 0 else 0
        avg_trade_return = np.mean(trading_returns) if len(trading_returns) > 0 else 0

        # Profit Factor
        gross_profit = np.sum(trading_returns[trading_returns > 0])
        gross_loss = abs(np.sum(trading_returns[trading_returns < 0]))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')

        # Alpha和Beta (相對基準)
        alpha, beta = 0.0, 1.0
        if benchmark_returns is not None and len(benchmark_returns) == len(trading_returns):
            benchmark_returns = benchmark_returns[:len(trading_returns)]
            covariance = np.cov(trading_returns, benchmark_returns)[0, 1]
            benchmark_variance = np.var(benchmark_returns)
            beta = covariance / benchmark_variance if benchmark_variance > 0 else 1.0
            benchmark_mean = np.mean(benchmark_returns)
            alpha = np.mean(trading_returns) - (self.config.risk_free_rate / 252 + beta * (benchmark_mean - self.config.risk_free_rate / 252))

        return PerformanceMetrics(
            total_return=total_return,
            annual_return=annual_return,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            profit_factor=profit_factor,
            calmar_ratio=calmar_ratio,
            sortino_ratio=sortino_ratio,
            total_trades=int(total_trades),
            profitable_trades=int(profitable_trades),
            losing_trades=int(losing_trades),
            avg_trade_return=avg_trade_return,
            volatility=volatility,
            beta=beta,
            alpha=alpha
        )

    def run_strategy_backtest(self, strategy_name: str, strategy_function, days: int = 252) -> Dict[str, Any]:
        """運行單個策略回測"""
        logger.info(f"開始回測策略: {strategy_name}")

        try:
            # 加載數據
            data = self.phase2_engine.load_0700_hk_data(days)
            if not data.get('success', False):
                return {'success': False, 'error': '數據加載失敗'}

            # 執行策略
            strategy_result = strategy_function(data)
            if not strategy_result.get('success', False):
                return {'success': False, 'error': f'策略執行失敗: {strategy_result.get("error")}'}

            # 獲取價格和信號
            prices = data['stock_data']['prices']
            signals = strategy_result['signals']

            # 計算基準回報（買入持有策略）
            benchmark_returns = np.diff(prices) / prices[:-1]

            # 計算性能指標
            performance = self.calculate_performance_metrics(prices, signals, benchmark_returns)

            # 計算資產曲線
            equity_curve = self.calculate_equity_curve(prices, signals)

            # 風險分析
            risk_analysis = self.analyze_risk(equity_curve, trading_returns=self.calculate_returns(prices, signals))

            return {
                'strategy_name': strategy_name,
                'success': True,
                'performance': performance,
                'equity_curve': equity_curve,
                'risk_analysis': risk_analysis,
                'strategy_signals': signals,
                'data_info': data['data_info'],
                'execution_time': strategy_result.get('performance', {}).get('calculation_time', 0)
            }

        except Exception as e:
            logger.error(f"回測策略 {strategy_name} 失敗: {e}")
            return {'success': False, 'error': str(e), 'strategy_name': strategy_name}

    def calculate_equity_curve(self, prices: np.ndarray, signals: np.ndarray) -> Dict[str, np.ndarray]:
        """計算資產曲線"""
        equity = self.config.initial_capital
        equity_curve = [equity]
        position = 0
        cash = equity

        for i in range(1, len(prices)):
            if signals[i] != signals[i-1]:  # 信號變化，執行交易
                # 平倉
                if position != 0:
                    equity += position * (prices[i] - prices[i-1])
                    position = 0
                    cash = equity

                # 開倉
                if signals[i] == 1:  # 買入
                    position_size = min(cash * self.config.max_position_size / prices[i],
                                      cash * (1 - self.config.commission) / prices[i])
                    position = position_size
                    cash -= position * prices[i] * (1 + self.config.commission + self.config.slippage)

                elif signals[i] == -1:  # 賣出（做空）
                    position_size = min(cash * self.config.max_position_size / prices[i],
                                      cash * (1 - self.config.commission) / prices[i])
                    position = -position_size
                    cash += abs(position) * prices[i] * (1 - self.config.commission - self.config.slippage)

            # 持倉損益
            if position != 0:
                unrealized_pnl = position * (prices[i] - prices[i-1])
                equity = cash + position * prices[i]
            else:
                equity = cash

            equity_curve.append(equity)

        return {
            'equity': np.array(equity_curve),
            'returns': np.diff(equity_curve) / equity_curve[:-1],
            'drawdown': self.calculate_drawdown(np.array(equity_curve))
        }

    def calculate_drawdown(self, equity: np.ndarray) -> np.ndarray:
        """計算回撤"""
        peak = np.maximum.accumulate(equity)
        return (equity - peak) / peak

    def analyze_risk(self, equity_curve: Dict[str, np.ndarray], trading_returns: np.ndarray) -> Dict[str, Any]:
        """分析風險指標"""
        equity = equity_curve['equity']
        drawdown = equity_curve['drawdown']

        # VaR計算 (95%置信度)
        var_95 = np.percentile(trading_returns, 5)

        # CVaR計算 (95%置信度)
        cvar_95 = np.mean(trading_returns[trading_returns <= var_95])

        # 最長回撤期
        drawdown_periods = self.calculate_drawdown_periods(drawdown)

        # 波動率分析
        volatility_30d = np.std(trading_returns[-30:]) * np.sqrt(252) if len(trading_returns) >= 30 else 0

        return {
            'var_95': var_95,
            'cvar_95': cvar_95,
            'max_drawdown_duration': max(drawdown_periods) if drawdown_periods else 0,
            'current_drawdown': drawdown[-1],
            'volatility_30d': volatility_30d,
            'skewness': self.calculate_skewness(trading_returns),
            'kurtosis': self.calculate_kurtosis(trading_returns)
        }

    def calculate_drawdown_periods(self, drawdown: np.ndarray) -> List[int]:
        """計算回撤持續期"""
        in_drawdown = drawdown < 0
        periods = []
        current_period = 0

        for is_dd in in_drawdown:
            if is_dd:
                current_period += 1
            else:
                if current_period > 0:
                    periods.append(current_period)
                current_period = 0

        if current_period > 0:
            periods.append(current_period)

        return periods

    def calculate_skewness(self, returns: np.ndarray) -> float:
        """計算偏度"""
        if len(returns) < 3:
            return 0.0
        mean = np.mean(returns)
        std = np.std(returns)
        if std == 0:
            return 0.0
        return np.mean(((returns - mean) / std) ** 3)

    def calculate_kurtosis(self, returns: np.ndarray) -> float:
        """計算峰度"""
        if len(returns) < 4:
            return 0.0
        mean = np.mean(returns)
        std = np.std(returns)
        if std == 0:
            return 0.0
        return np.mean(((returns - mean) / std) ** 4) - 3

    def run_comprehensive_backtest(self, days: int = 252) -> Dict[str, Any]:
        """運行綜合回測"""
        logger.info(f"開始Phase 3綜合回測，數據天數: {days}")

        start_time = time.time()

        # 定義策略函數
        strategies = {
            'HIBOR_RSI': self.phase2_engine.run_hibor_rsi_strategy,
            'Monetary_MACD': self.phase2_engine.run_monetary_macd_strategy
        }

        # 運行所有策略
        results = {}
        for strategy_name, strategy_func in strategies.items():
            logger.info(f"運行策略: {strategy_name}")
            result = self.run_strategy_backtest(strategy_name, strategy_func, days)
            results[strategy_name] = result

        # 計算綜合比較
        comparison = self.compare_strategies(results)

        # 生成總體統計
        total_time = time.time() - start_time
        successful_strategies = sum(1 for r in results.values() if r.get('success', False))

        comprehensive_results = {
            'success': True,
            'phase': 'Phase 3: Complete Backtest Engine',
            'timestamp': datetime.now().isoformat(),
            'config': self.config.__dict__,
            'strategy_results': results,
            'strategy_comparison': comparison,
            'summary': {
                'total_execution_time': total_time,
                'successful_strategies': successful_strategies,
                'total_strategies': len(strategies),
                'success_rate': successful_strategies / len(strategies),
                'gpu_available': self.gpu_available
            }
        }

        logger.info(f"Phase 3綜合回測完成，耗時: {total_time:.4f}秒")
        logger.info(f"策略成功率: {successful_strategies}/{len(strategies)}")

        return comprehensive_results

    def compare_strategies(self, results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """比較策略性能"""
        successful_results = {k: v for k, v in results.items() if v.get('success', False)}

        if not successful_results:
            return {'error': '沒有成功執行的策略'}

        # 收集性能指標
        metrics_comparison = {}
        for strategy_name, result in successful_results.items():
            perf = result['performance']
            metrics_comparison[strategy_name] = {
                'total_return': perf.total_return,
                'sharpe_ratio': perf.sharpe_ratio,
                'max_drawdown': perf.max_drawdown,
                'win_rate': perf.win_rate,
                'calmar_ratio': perf.calmar_ratio,
                'profit_factor': perf.profit_factor
            }

        # 找出最佳策略
        best_strategies = {}
        for metric in ['total_return', 'sharpe_ratio', 'calmar_ratio', 'win_rate']:
            if metric == 'max_drawdown':  # 越小越好
                best_strategy = min(metrics_comparison.items(), key=lambda x: x[1][metric])
            else:  # 越大越好
                best_strategy = max(metrics_comparison.items(), key=lambda x: x[1][metric])
            best_strategies[f'best_{metric}'] = best_strategy[0]

        return {
            'metrics_comparison': metrics_comparison,
            'best_strategies': best_strategies,
            'ranking': self.rank_strategies(metrics_comparison)
        }

    def rank_strategies(self, metrics_comparison: Dict[str, Dict[str, float]]) -> List[Tuple[str, float]]:
        """策略排名（基於Sharpe比率）"""
        return sorted(metrics_comparison.items(), key=lambda x: x[1]['sharpe_ratio'], reverse=True)

    def generate_html_report(self, results: Dict[str, Any], filename: str = None) -> str:
        """生成HTML報告"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"phase3_backtest_report_{timestamp}.html"

        try:
            html_content = self._create_html_report(results)

            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)

            logger.info(f"HTML報告已生成: {filename}")
            return filename

        except Exception as e:
            logger.error(f"生成HTML報告失敗: {e}")
            return None

    def _create_html_report(self, results: Dict[str, Any]) -> str:
        """創建HTML報告內容"""
        # 這裡創建一個基礎的HTML報告模板
        html_template = """
<!DOCTYPE html>
<html lang="zh-HK">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Phase 3 GPU量化交易回測報告</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #2c3e50; text-align: center; margin-bottom: 30px; }
        h2 { color: #34495e; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
        .summary { background-color: #ecf0f1; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
        .metric { display: inline-block; margin: 10px 20px; text-align: center; }
        .metric-value { font-size: 24px; font-weight: bold; color: #3498db; }
        .metric-label { font-size: 12px; color: #7f8c8d; }
        table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
        th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
        th { background-color: #3498db; color: white; }
        tr:nth-child(even) { background-color: #f9f9f9; }
        .best-strategy { background-color: #d5f4e6; font-weight: bold; }
        .success { color: #27ae60; }
        .warning { color: #f39c12; }
        .error { color: #e74c3c; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Phase 3 GPU量化交易回測報告</h1>
        <div class="summary">
            <h3>📊 回測摘要</h3>
            <div class="metric">
                <div class="metric-value">{total_strategies}</div>
                <div class="metric-label">總策略數</div>
            </div>
            <div class="metric">
                <div class="metric-value">{successful_strategies}</div>
                <div class="metric-label">成功策略</div>
            </div>
            <div class="metric">
                <div class="metric-value">{success_rate:.1%}</div>
                <div class="metric-label">成功率</div>
            </div>
            <div class="metric">
                <div class="metric-value">{execution_time:.2f}s</div>
                <div class="metric-label">執行時間</div>
            </div>
            <div class="metric">
                <div class="metric-value">{gpu_status}</div>
                <div class="metric-label">GPU狀態</div>
            </div>
        </div>

        <h2>📈 策略性能比較</h2>
        <table>
            <thead>
                <tr>
                    <th>策略名稱</th>
                    <th>總回報</th>
                    <th>年化回報</th>
                    <th>Sharpe比率</th>
                    <th>最大回撤</th>
                    <th>勝率</th>
                    <th>Calmar比率</th>
                    <th>總交易次數</th>
                </tr>
            </thead>
            <tbody>
                {strategy_rows}
            </tbody>
        </table>

        <h2>🏆 最佳策略</h2>
        <div class="summary">
            <p><strong>最高Sharpe比率:</strong> {best_sharpe_strategy}</p>
            <p><strong>最高總回報:</strong> {best_return_strategy}</p>
            <p><strong>最低回撤:</strong> {best_drawdown_strategy}</p>
            <p><strong>最高Calmar比率:</strong> {best_calmar_strategy}</p>
        </div>

        <h2>⚙️ 回測配置</h2>
        <table>
            <tr><td>初始資本</td><td>${initial_capital:,.0f}</td></tr>
            <tr><td>無風險利率</td><td>{risk_free_rate:.1%}</td></tr>
            <tr><td>手續費</td><td>{commission:.2%}</td></tr>
            <tr><td>滑點</td><td>{slippage:.2%}</td></tr>
            <tr><td>最大倉位</td><td>{max_position_size:.0%}</td></tr>
        </table>

        <div style="text-align: center; margin-top: 30px; color: #7f8c8d; font-size: 12px;">
            <p>報告生成時間: {timestamp}</p>
            <p>Phase 3 GPU加速量化交易系統 | 0700.HK 腾訊控股</p>
        </div>
    </div>
</body>
</html>
        """

        # 填充模板數據
        summary = results.get('summary', {})
        strategy_comparison = results.get('strategy_comparison', {})

        # 生成策略行
        strategy_rows = ""
        if 'metrics_comparison' in strategy_comparison:
            for strategy, metrics in strategy_comparison['metrics_comparison'].items():
                strategy_rows += f"""
                <tr>
                    <td>{strategy}</td>
                    <td>{metrics['total_return']:.2%}</td>
                    <td>{metrics.get('annual_return', 0):.2%}</td>
                    <td>{metrics['sharpe_ratio']:.3f}</td>
                    <td>{metrics['max_drawdown']:.2%}</td>
                    <td>{metrics['win_rate']:.2%}</td>
                    <td>{metrics['calmar_ratio']:.3f}</td>
                    <td>{metrics.get('total_trades', 0)}</td>
                </tr>
                """

        # 最佳策略
        best_strategies = strategy_comparison.get('best_strategies', {})

        return html_template.format(
            total_strategies=summary.get('total_strategies', 0),
            successful_strategies=summary.get('successful_strategies', 0),
            success_rate=summary.get('success_rate', 0),
            execution_time=summary.get('total_execution_time', 0),
            gpu_status="啟用" if summary.get('gpu_available', False) else "CPU版本",
            strategy_rows=strategy_rows,
            best_sharpe_strategy=best_strategies.get('best_sharpe_ratio', 'N/A'),
            best_return_strategy=best_strategies.get('best_total_return', 'N/A'),
            best_drawdown_strategy=best_strategies.get('best_max_drawdown', 'N/A'),
            best_calmar_strategy=best_strategies.get('best_calmar_ratio', 'N/A'),
            initial_capital=self.config.initial_capital,
            risk_free_rate=self.config.risk_free_rate,
            commission=self.config.commission,
            slippage=self.config.slippage,
            max_position_size=self.config.max_position_size,
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )

def main():
    """主函數"""
    print("=" * 80)
    print("Phase 3: 完整回測引擎與報告生成系統")
    print("Phase 3: Complete Backtest Engine and Reporting System")
    print("=" * 80)

    try:
        # 初始化回測引擎
        config = BacktestConfig(
            initial_capital=100000.0,
            risk_free_rate=0.03,
            commission=0.001,
            slippage=0.0005
        )

        engine = Phase3BacktestEngine(gpu_device=0, config=config)

        # 運行綜合回測
        print("\n🚀 開始運行綜合回測...")
        results = engine.run_comprehensive_backtest(days=252)

        if results.get('success', False):
            print("\n✅ Phase 3綜合回測成功完成！")

            # 顯示關鍵結果
            summary = results['summary']
            comparison = results.get('strategy_comparison', {})

            print(f"\n📊 回測摘要:")
            print(f"   總策略數: {summary['total_strategies']}")
            print(f"   成功策略: {summary['successful_strategies']}")
            print(f"   成功率: {summary['success_rate']:.1%}")
            print(f"   執行時間: {summary['total_execution_time']:.4f}秒")
            print(f"   GPU狀態: {'啟用' if summary['gpu_available'] else 'CPU版本'}")

            # 策略比較
            if 'metrics_comparison' in comparison:
                print(f"\n🏆 策略性能排名 (按Sharpe比率):")
                ranking = comparison.get('ranking', [])
                for i, (strategy, metrics) in enumerate(ranking, 1):
                    print(f"   {i}. {strategy}: Sharpe={metrics['sharpe_ratio']:.3f}, "
                          f"回報={metrics['total_return']:.2%}, "
                          f"回撤={metrics['max_drawdown']:.2%}")

            # 最佳策略
            best_strategies = comparison.get('best_strategies', {})
            print(f"\n🥇 最佳策略:")
            for metric, strategy in best_strategies.items():
                print(f"   {metric}: {strategy}")

            # 生成HTML報告
            print(f"\n📄 生成HTML報告...")
            html_file = engine.generate_html_report(results)
            if html_file:
                print(f"   報告已保存: {html_file}")

            # 保存JSON結果
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            json_file = f"phase3_backtest_results_{timestamp}.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False, default=str)
            print(f"   JSON結果已保存: {json_file}")

        else:
            print(f"\n❌ Phase 3綜合回測失敗: {results.get('error', 'Unknown error')}")

    except Exception as e:
        logger.error(f"回測執行失敗: {e}")
        print(f"回測執行失敗: {e}")

if __name__ == "__main__":
    main()