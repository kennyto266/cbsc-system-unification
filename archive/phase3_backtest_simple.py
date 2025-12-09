#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 3: 簡化回測引擎與報告生成
Phase 3: Simplified Backtest Engine and Reporting
"""

import numpy as np
import pandas as pd
import time
import logging
import json
from typing import Dict, List, Optional, Union, Tuple, Any
from datetime import datetime, timedelta

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BacktestConfig:
    def __init__(self):
        self.initial_capital = 100000.0  # 初始資本
        self.risk_free_rate = 0.03       # 無風險利率 3%
        self.commission = 0.001          # 手續費
        self.slippage = 0.0005           # 滑點

class PerformanceMetrics:
    def __init__(self):
        self.total_return = 0.0
        self.annual_return = 0.0
        self.sharpe_ratio = 0.0
        self.max_drawdown = 0.0
        self.win_rate = 0.0
        self.profit_factor = 0.0
        self.calmar_ratio = 0.0
        self.total_trades = 0
        self.volatility = 0.0

class Phase3SimpleBacktest:
    """Phase 3 簡化回測引擎"""

    def __init__(self, gpu_device: int = 0):
        """初始化回測引擎"""
        self.config = BacktestConfig()
        self.gpu_device = gpu_device

        # 嘗試導入GPU
        try:
            import cupy as cp
            self.gpu_available = True
            cp.cuda.Device(gpu_device).use()
            logger.info(f"GPU設備 {gpu_device} 可用")
        except:
            self.gpu_available = False
            logger.info("使用CPU版本")

        # 導入Phase 2引擎
        try:
            from phase2_gpu_ta_engine_with_real_data import Phase2GPUBacktestEngine, RealGovDataLoader
            self.phase2_engine = Phase2GPUBacktestEngine(gpu_device)
            self.data_loader = RealGovDataLoader()
        except Exception as e:
            logger.error(f"無法導入Phase 2引擎: {e}")
            self.phase2_engine = None

        logger.info("Phase 3 簡化回測引擎初始化完成")

    def calculate_returns(self, prices: np.ndarray, signals: np.ndarray) -> np.ndarray:
        """計算交易回報"""
        if len(prices) != len(signals):
            return np.array([0.0])

        # 日回報率
        daily_returns = np.diff(prices) / prices[:-1]

        # 應用信號
        position = np.zeros(len(signals))
        position[signals == 1] = 1   # 買入
        position[signals == -1] = -1 # 賣出

        # 交易回報
        trading_returns = daily_returns * position[:-1]
        return trading_returns

    def calculate_performance_metrics(self, prices: np.ndarray, signals: np.ndarray) -> PerformanceMetrics:
        """計算性能指標"""
        trading_returns = self.calculate_returns(prices, signals)

        if len(trading_returns) == 0:
            return PerformanceMetrics()

        # 基本指標
        total_return = np.prod(1 + trading_returns) - 1
        trading_days = len(trading_returns)
        annual_return = (1 + total_return) ** (252 / trading_days) - 1

        # 波動率
        volatility = np.std(trading_returns) * np.sqrt(252)

        # Sharpe比率 (3%無風險利率)
        excess_returns = trading_returns - self.config.risk_free_rate / 252
        sharpe_ratio = np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252) if np.std(excess_returns) > 0 else 0

        # 最大回撤
        cumulative_returns = np.cumprod(1 + trading_returns)
        peak = np.maximum.accumulate(cumulative_returns)
        drawdown = (cumulative_returns - peak) / peak
        max_drawdown = np.min(drawdown)

        # Calmar比率
        calmar_ratio = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0

        # 交易統計
        total_trades = np.sum(np.abs(np.diff(signals)) > 0)
        winning_trades = np.sum(trading_returns > 0)
        win_rate = winning_trades / total_trades if total_trades > 0 else 0

        # Profit Factor
        profits = trading_returns[trading_returns > 0]
        losses = trading_returns[trading_returns < 0]
        profit_factor = np.sum(profits) / abs(np.sum(losses)) if len(losses) > 0 else float('inf')

        # 創建性能對象
        metrics = PerformanceMetrics()
        metrics.total_return = total_return
        metrics.annual_return = annual_return
        metrics.sharpe_ratio = sharpe_ratio
        metrics.max_drawdown = max_drawdown
        metrics.win_rate = win_rate
        metrics.profit_factor = profit_factor
        metrics.calmar_ratio = calmar_ratio
        metrics.total_trades = int(total_trades)
        metrics.volatility = volatility

        return metrics

    def run_strategy_backtest(self, strategy_name: str, strategy_function, days: int = 252) -> Dict[str, Any]:
        """運行策略回測"""
        logger.info(f"回測策略: {strategy_name}")

        try:
            # 加載數據
            data = self.phase2_engine.load_0700_hk_data(days)
            if not data.get('success', False):
                return {'success': False, 'error': '數據加載失敗'}

            # 執行策略
            strategy_result = strategy_function(data)
            if not strategy_result.get('success', False):
                return {'success': False, 'error': f'策略失敗: {strategy_result.get("error")}'}

            # 計算性能
            prices = data['stock_data']['prices']
            signals = strategy_result['signals']
            metrics = self.calculate_performance_metrics(prices, signals)

            return {
                'strategy_name': strategy_name,
                'success': True,
                'performance': metrics,
                'total_signals': np.sum(signals != 0),
                'buy_signals': np.sum(signals == 1),
                'sell_signals': np.sum(signals == -1),
                'execution_time': strategy_result.get('performance', {}).get('calculation_time', 0)
            }

        except Exception as e:
            logger.error(f"策略回測失敗: {e}")
            return {'success': False, 'error': str(e), 'strategy_name': strategy_name}

    def run_all_strategies(self, days: int = 252) -> Dict[str, Any]:
        """運行所有策略"""
        logger.info(f"開始運行所有策略，天數: {days}")

        start_time = time.time()

        # 定義策略
        strategies = {
            'HIBOR_RSI': self.phase2_engine.run_hibor_rsi_strategy,
            'Monetary_MACD': self.phase2_engine.run_monetary_macd_strategy
        }

        # 運行策略
        results = {}
        for name, func in strategies.items():
            result = self.run_strategy_backtest(name, func, days)
            results[name] = result

        # 計算總體統計
        total_time = time.time() - start_time
        successful = sum(1 for r in results.values() if r.get('success', False))

        # 比較策略
        comparison = self.compare_strategies(results)

        return {
            'success': True,
            'phase': 'Phase 3 Simple Backtest',
            'timestamp': datetime.now().isoformat(),
            'strategy_results': results,
            'strategy_comparison': comparison,
            'summary': {
                'total_execution_time': total_time,
                'successful_strategies': successful,
                'total_strategies': len(strategies),
                'success_rate': successful / len(strategies),
                'gpu_available': self.gpu_available
            }
        }

    def compare_strategies(self, results: Dict[str, Dict]) -> Dict[str, Any]:
        """比較策略性能"""
        successful = {k: v for k, v in results.items() if v.get('success', False)}

        if not successful:
            return {'error': '沒有成功策略'}

        # 收集指標
        metrics = {}
        for name, result in successful.items():
            perf = result['performance']
            metrics[name] = {
                'total_return': perf.total_return,
                'sharpe_ratio': perf.sharpe_ratio,
                'max_drawdown': perf.max_drawdown,
                'win_rate': perf.win_rate,
                'calmar_ratio': perf.calmar_ratio
            }

        # 找出最佳
        best_sharpe = max(metrics.items(), key=lambda x: x[1]['sharpe_ratio'])
        best_return = max(metrics.items(), key=lambda x: x[1]['total_return'])
        best_drawdown = min(metrics.items(), key=lambda x: x[1]['max_drawdown'])

        # 排名
        ranking = sorted(metrics.items(), key=lambda x: x[1]['sharpe_ratio'], reverse=True)

        return {
            'metrics': metrics,
            'ranking': ranking,
            'best_strategies': {
                'best_sharpe': best_sharpe[0],
                'best_return': best_return[0],
                'best_drawdown': best_drawdown[0]
            }
        }

    def generate_simple_report(self, results: Dict[str, Any]) -> str:
        """生成簡單文本報告"""
        report = []
        report.append("=" * 60)
        report.append("Phase 3 GPU量化交易回測報告")
        report.append("=" * 60)

        summary = results.get('summary', {})
        comparison = results.get('strategy_comparison', {})

        # 摘要
        report.append("\n[回測摘要]")
        report.append(f"總策略數: {summary.get('total_strategies', 0)}")
        report.append(f"成功策略: {summary.get('successful_strategies', 0)}")
        report.append(f"成功率: {summary.get('success_rate', 0):.1%}")
        report.append(f"執行時間: {summary.get('total_execution_time', 0):.4f}秒")
        report.append(f"GPU狀態: {'啟用' if summary.get('gpu_available', False) else 'CPU版本'}")

        # 策略結果
        report.append("\n[策略性能]")
        strategy_results = results.get('strategy_results', {})
        for name, result in strategy_results.items():
            if result.get('success', False):
                perf = result['performance']
                report.append(f"\n{name}:")
                report.append(f"  總回報: {perf.total_return:.2%}")
                report.append(f"  Sharpe比率: {perf.sharpe_ratio:.3f}")
                report.append(f"  最大回撤: {perf.max_drawdown:.2%}")
                report.append(f"  勝率: {perf.win_rate:.2%}")
                report.append(f"  交易次數: {perf.total_trades}")
                report.append(f"  執行時間: {result.get('execution_time', 0):.4f}秒")
            else:
                report.append(f"\n{name}: 執行失敗")

        # 最佳策略
        if 'best_strategies' in comparison:
            best = comparison['best_strategies']
            report.append(f"\n[最佳策略]")
            report.append(f"最高Sharpe比率: {best.get('best_sharpe', 'N/A')}")
            report.append(f"最高總回報: {best.get('best_return', 'N/A')}")
            report.append(f"最低回撤: {best.get('best_drawdown', 'N/A')}")

        report.append(f"\n報告生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 60)

        return "\n".join(report)

    def save_results(self, results: Dict[str, Any], filename: str = None) -> str:
        """保存結果"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"phase3_simple_results_{timestamp}.json"

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False, default=str)
            logger.info(f"結果已保存: {filename}")
            return filename
        except Exception as e:
            logger.error(f"保存失敗: {e}")
            return None

def main():
    """主函數"""
    print("=" * 60)
    print("Phase 3: 簡化回測引擎與報告生成")
    print("=" * 60)

    try:
        # 初始化引擎
        engine = Phase3SimpleBacktest(gpu_device=0)

        # 運行回測
        print("\n開始運行策略回測...")
        results = engine.run_all_strategies(days=252)

        if results.get('success', False):
            # 生成報告
            report = engine.generate_simple_report(results)
            print("\n" + report)

            # 保存結果
            json_file = engine.save_results(results)
            if json_file:
                print(f"\n結果已保存至: {json_file}")

            # 生成文本報告
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            txt_file = f"phase3_report_{timestamp}.txt"
            with open(txt_file, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"報告已保存至: {txt_file}")

        else:
            print(f"\n回測失敗: {results.get('error', 'Unknown error')}")

    except Exception as e:
        logger.error(f"執行失敗: {e}")
        print(f"執行失敗: {e}")

if __name__ == "__main__":
    main()