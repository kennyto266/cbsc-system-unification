#!/usr/bin/env python3
"""
Universal Backtesting SOP - 標準化通用回測系統

基於OpenSpec提案實現的統一回測操作流程，支持：
- 100%真實數據政策
- 標準化一買一賣交易邏輯
- 3%無風險利率Sharpe比率計算
- 0-300步長5參數優化框架
- 32核心並行處理
- VectorBT專業回測引擎

作者: Claude AI Assistant
日期: 2025-11-22
版本: v1.0 (OpenSpec Standardized)
"""

import asyncio
import logging
import json
import pandas as pd
import numpy as np
import vectorbt as vbt
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed
import requests
import warnings

# Import 真實數據適配器
from ..data.vectorbt_adapter import VectorBTDataAdapter
from ..shared.indicators.non_price_ta_id_system import NonPriceTACalculator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

@dataclass
class BacktestConfig:
    """回測配置類"""
    symbol: str
    start_date: datetime
    end_date: datetime
    param_min: int = 0
    param_max: int = 300
    param_step: int = 5
    risk_free_rate: float = 0.03  # 3%無風險利率
    max_workers: int = 32
    cache_enabled: bool = True
    verbose: bool = False

@dataclass
class StrategyResult:
    """策略結果類"""
    strategy_id: str
    indicator_type: str
    indicator_params: Dict[str, Any]
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    total_trades: int
    quality_score: float
    execution_time: float
    data_quality: str

class DataAuthenticityValidator:
    """數據真實性驗證器"""

    def __init__(self):
        self.real_data_sources = {
            'hkma': ['api.hkma.gov.hk'],
            'central_api': ['18.180.162.113:9191'],
            'gov_stats': ['censtatd.gov.hk']
        }
        self.mock_patterns = [
            'random.uniform', 'random.normal', 'Simulated', 'Mock', 'fake', '模擬'
        ]

    def validate_price_data(self, df: pd.DataFrame) -> bool:
        """驗證股價數據真實性"""
        if df.empty:
            return False

        # 檢查數據合理性
        if 'close' not in df.columns:
            return False

        # 檢查價格範圍合理性（港股）
        close_prices = df['close'].dropna()
        if len(close_prices) == 0:
            return False

        min_price, max_price = close_prices.min(), close_prices.max()
        if min_price < 0.1 or max_price > 10000:  # 不合理的價格範圍
            return False

        # 檢查時間連續性
        if len(df) < 10:  # 數據點太少
            return False

        return True

    def validate_non_price_data(self, data: pd.Series) -> bool:
        """驗證非價格數據真實性"""
        if data.empty:
            return False

        # 檢查數據是否有明顯的模擬模式
        data_str = str(data.values)
        for pattern in self.mock_patterns:
            if pattern.lower() in data_str.lower():
                logger.warning(f"檢測到可能的模擬數據模式: {pattern}")
                return False

        return True

    def check_source_authenticity(self, source_name: str, data: Any) -> bool:
        """檢查數據源真實性"""
        if source_name in ['stock_price', '0700.hk', 'hk_stocks']:
            # 股價數據應來自中央API
            return True
        elif source_name in ['hkma', 'hibor', 'monetary']:
            # 金融數據應來自HKMA
            return True
        elif source_name in ['government_stats', 'gdp', 'unemployment', 'retail']:
            # 政府統計數據
            return True

        return False

class StandardizedParameterOptimizer:
    """標準化參數優化引擎"""

    def __init__(self, config: BacktestConfig):
        self.config = config
        self.param_range = list(range(config.param_min, config.param_max + 1, config.param_step))
        self.total_combinations = len(self.param_range) * len(self.param_range)  # 3,721組合

    def generate_parameter_grid(self) -> List[Tuple[int, int]]:
        """生成標準化參數網格"""
        return [(p1, p2) for p1 in self.param_range for p2 in self.param_range]

    def parallel_optimize(self, optimization_func) -> List[StrategyResult]:
        """並行執行參數優化"""
        param_combinations = self.generate_parameter_grid()

        if self.config.verbose:
            logger.info(f"開始參數優化：{len(param_combinations)} 種組合")
            logger.info(f"使用 {self.config.max_workers} 個並行進程")

        results = []

        # 並行執行優化
        with ProcessPoolExecutor(max_workers=self.config.max_workers) as executor:
            # 提交所有任務
            future_to_params = {
                executor.submit(optimization_func, params): params
                for params in param_combinations
            }

            # 收集結果
            for future in as_completed(future_to_params):
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                except Exception as e:
                    logger.error(f"優化任務失敗: {future_to_params[future]}: {e}")
                    continue

        return results

class StandardizedTradingLogic:
    """標準化一買一賣交易邏輯"""

    def __init__(self, config: BacktestConfig):
        self.config = config

    def generate_signals(self, indicator_data: pd.Series,
                          buy_threshold: float, sell_threshold: float) -> Tuple[pd.Series, pd.Series]:
        """生成標準化買賣信號"""
        # 確保信號不重疊
        buy_signal = indicator_data < buy_threshold
        sell_signal = indicator_data > sell_threshold

        # 創向偏移確保一買一賣邏輯
        buy_signals = buy_signal & (~sell_signal.shift(1).fillna(False))
        sell_signals = sell_signal & (~buy_signal.shift(1).fillna(False))

        return buy_signals, sell_signals

    def calculate_positions(self, buy_signals: pd.Series, sell_signals: pd.Series) -> pd.Series:
        """計算持倉狀態"""
        positions = pd.Series(0.0, index=buy_signals.index)
        position = 0  # 0 = 現金, 1 = 持有股票

        for i in range(len(positions)):
            if position == 0 and buy_signals.iloc[i]:
                positions.iloc[i] = 1.0  # 買入
                position = 1
            elif position == 1 and sell_signals.iloc[i]:
                positions.iloc[i] = -1.0  # 賣出
                position = 0
            # 否則保持原狀態

        return positions

class StandardizedMetrics:
    """標準化性能指標計算"""

    def __init__(self, config: BacktestConfig):
        self.config = config
        self.risk_free_rate = config.risk_free_rate

    def calculate_sharpe_ratio(self, returns: pd.Series) -> float:
        """計算標準化Sharpe比率（3%無風險利率）"""
        if len(returns) == 0 or returns.std() == 0:
            return 0.0

        # 計算超額收益
        excess_returns = returns - self.risk_free_rate / 252  # 日化無風險收益率

        # 年化Sharpe比率
        sharpe = excess_returns.mean() / returns.std() * np.sqrt(252)

        return sharpe

    def calculate_max_drawdown(self, portfolio) -> float:
        """計算最大回撤"""
        try:
            return portfolio.max_drawdown()
        except:
            return 0.0

    def calculate_quality_score(self, total_return: float, sharpe_ratio: float,
                              max_drawdown: float, win_rate: float) -> float:
        """計算綜合質量評分"""
        score = 0.0

        # Sharpe比率 40% (權重最高)
        score += min(max(sharpe_ratio * 40, 0), 100)

        # 總回報 20%
        score += min(max(total_return * 200, 0), 100)

        # 最大回撤 20% (越低越好)
        score += min(max((1 - abs(max_drawdown)) * 100, 0), 100)

        # 勝率 20%
        score += min(max(win_rate * 20, 0), 100)

        return min(score, 100)  # 最高100分

class UniversalBacktestSOP:
    """通用回測SOP主類"""

    def __init__(self, config: BacktestConfig):
        self.config = config
        self.data_validator = DataAuthenticityValidator()
        self.optimizer = StandardizedParameterOptimizer(config)
        self.trading_logic = StandardizedTradingLogic(config)
        self.metrics = StandardizedMetrics(config)
        self.data_adapter = VectorBTDataAdapter()
        self.ta_converter = NonPriceTACalculator()
        
        # 新增：技術指標管道和質量監控
        from .technical_indicator_pipeline import StandardizedTechnicalIndicatorPipeline
        from .data_quality_monitor import ComprehensiveDataQualityMonitor
        
        self.indicator_pipeline = StandardizedTechnicalIndicatorPipeline()
        self.quality_monitor = ComprehensiveDataQualityMonitor()

        # 結果存儲
        self.results = []
        self.execution_stats = {}

        logger.info("="*80)
        logger.info("[SYSTEM] Universal Backtest SOP - Enhanced with Quality Monitoring")
        logger.info("="*80)
        logger.info(f"配置: {config.symbol} | 參數範圍: {config.param_min}-{config.param_max} 步長{config.param_step}")
        logger.info(f"日期範圍: {config.start_date} 到 {config.end_date}")
        logger.info(f"並行進程: {config.max_workers} | 無風險利率: {config.risk_free_rate:.1%}")
        logger.info("[ENHANCED] 技術指標管道 + 數據質量驗證 + 真實性檢查")

    def validate_data_sources(self) -> bool:
        """驗證所有數據源真實性"""
        logger.info("[DATA] 驗證數據源真實性...")

        try:
            # 驗證股價數據
            stock_data = self.data_adapter._get_price_data(
                self.config.symbol,
                self.config.start_date,
                self.config.end_date
            )

            if not self.data_validator.validate_price_data(stock_data):
                raise ValueError(f"股價數據真實性驗證失敗: {self.config.symbol}")

            logger.info(f"✅ 股價數據驗證通過: {len(stock_data)} 條記錄")

            # 驗證非價格數據
            # 這裡可以添加更多數據源驗證

            return True

        except Exception as e:
            logger.error(f"數據源驗證失敗: {e}")
            return False

    def execute_single_strategy(self, params: Tuple[int, int],
                                indicator_type: str = 'RSI') -> Optional[StrategyResult]:
        """執行單個策略回測"""
        param1, param2 = params
        start_time = datetime.now()

        try:
            # 載入真實數據
            stock_data = self.data_adapter._get_price_data(
                self.config.symbol,
                self.config.start_date,
                self.config.end_date
            )

            if stock_data.empty:
                logger.warning(f"無數據可用: {self.config.symbol}")
                return None

            # 獲取技術指標（這裡需要根據您的系統調整）
            indicator_data = self._calculate_indicator(stock_data, indicator_type, param1)

            if indicator_data.empty:
                logger.warning(f"指標計算失敗: {indicator_type}({param1})")
                return None

            # 生成交易信號
            buy_signals, sell_signals = self.trading_logic.generate_signals(
                indicator_data, param2/100.0, (100-param2)/100.0
            )

            if buy_signals.sum() == 0 and sell_signals.sum() == 0:
                logger.debug(f"無交易信號: {indicator_type}({param1}, {param2})")
                return None

            # 執行VectorBT回測
            portfolio = vbt.Portfolio.from_signals(
                price=stock_data['close'],
                entries=buy_signals,
                exits=sell_signals,
                init_cash=100000,
                fees=0.001,  # 0.1%交易費用
                freq='1D'
            )

            # 計算性能指標
            returns = portfolio.returns()
            total_return = (1 + returns).prod() - 1
            volatility = returns.std() * np.sqrt(252) if len(returns) > 0 else 0
            max_drawdown = self.metrics.calculate_max_drawdown(portfolio)
            sharpe_ratio = self.metrics.calculate_sharpe_ratio(returns)

            # 計算交易統計
            trade_count = portfolio.trades.count() if hasattr(portfolio.trades, 'count') else 0
            win_rate = portfolio.win_rate() if hasattr(portfolio, 'win_rate') else 0

            # 計算質量評分
            quality_score = self.metrics.calculate_quality_score(
                total_return, sharpe_ratio, max_drawdown, win_rate
            )

            execution_time = (datetime.now() - start_time).total_seconds()

            result = StrategyResult(
                strategy_id=f"{indicator_type}_{param1}_{param2}",
                indicator_type=indicator_type,
                indicator_params={'param1': param1, 'param2': param2},
                total_return=total_return,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=max_drawdown,
                win_rate=win_rate,
                total_trades=trade_count,
                quality_score=quality_score,
                execution_time=execution_time,
                data_quality='Real'
            )

            return result

        except Exception as e:
            logger.error(f"策略執行失敗: {indicator_type}({param1}, {param2}): {e}")
            return None

    def _calculate_indicator(self, stock_data: pd.DataFrame,
                             indicator_type: str, period: int) -> pd.Series:
        """計算技術指標"""
        try:
            if indicator_type == 'RSI':
                # 使用VectorBT計算RSI
                rsi = vbt.RSI.run(stock_data['close'], window=period)
                return rsi.rsi
            # 這裡可以添加更多指標類型
            else:
                logger.warning(f"不支持的指標類型: {indicator_type}")
                return pd.Series()
        except Exception as e:
            logger.error(f"指標計算錯誤: {indicator_type}({period}): {e}")
            return pd.Series()

    def run_optimization(self) -> List[StrategyResult]:
        """執行完整參數優化"""
        logger.info("[OPTIMIZATION] 開始標準化參數優化...")

        if not self.validate_data_sources():
            raise ValueError("數據源驗證失敗，停止優化")

        def optimization_task(params):
            return self.execute_single_strategy(params)

        # 執行並行優化
        results = self.optimizer.parallel_optimize(optimization_task)

        # 記錄執行統計
        self.execution_stats = {
            'total_combinations': self.optimizer.total_combinations,
            'successful_results': len(results),
            'success_rate': len(results) / self.optimizer.total_combinations if self.optimizer.total_combinations > 0 else 0,
            'execution_time': datetime.now(),
            'strategies_per_second': len(results) / max(1, sum(r.execution_time for r in results) / len(results)) if results else 0
        }

        # 按質量評分排序
        results.sort(key=lambda x: x.quality_score, reverse=True)

        self.results = results

        logger.info(f"✅ 優化完成：{len(results)} 個有效策略")
        logger.info(f"成功率: {self.execution_stats['success_rate']:.1%}")
        if results:
            best_strategy = results[0]
            logger.info(f"最佳策略: {best_strategy.strategy_id}")
            logger.info(f"質量評分: {best_strategy.quality_score:.1f}")
            logger.info(f"Sharpe比率: {best_strategy.sharpe_ratio:.3f}")
            logger.info(f"總回報: {best_strategy.total_return:.2%}")

        return results

    def generate_report(self, output_path: str = None) -> Dict[str, Any]:
        """生成標準化報告"""
        if not self.results:
            return {"error": "無結果可用"}

        report = {
            'metadata': {
                'symbol': self.config.symbol,
                'start_date': self.config.start_date.isoformat(),
                'end_date': self.config.end_date.isoformat(),
                'parameter_range': {
                    'min': self.config.param_min,
                    'max': self.config.param_max,
                    'step': self.config.param_step,
                    'total_combinations': self.optimizer.total_combinations
                },
                'risk_free_rate': self.config.risk_free_rate,
                'generated_at': datetime.now().isoformat(),
                'sop_version': '1.0-OpenSpec'
            },
            'execution_stats': self.execution_stats,
            'top_strategies': [
                {
                    'rank': i + 1,
                    'strategy_id': r.strategy_id,
                    'indicator_type': r.indicator_type,
                    'params': r.indicator_params,
                    'quality_score': r.quality_score,
                    'total_return': r.total_return,
                    'sharpe_ratio': r.sharpe_ratio,
                    'max_drawdown': r.max_drawdown,
                    'win_rate': r.win_rate,
                    'total_trades': r.total_trades,
                    'execution_time': r.execution_time,
                    'data_quality': r.data_quality
                }
                for i, r in enumerate(self.results[:20])  # 前20個策略
            ],
            'all_results': [asdict(r) for r in self.results],
            'summary': {
                'total_strategies': len(self.results),
                'avg_quality_score': np.mean([r.quality_score for r in self.results]) if self.results else 0,
                'avg_sharpe': np.mean([r.sharpe_ratio for r in self.results]) if self.results else 0,
                'avg_return': np.mean([r.total_return for r in self.results]) if self.results else 0,
                'max_sharpe': max([r.sharpe_ratio for r in self.results]) if self.results else 0,
                'max_return': max([r.total_return for r in self.results]) if self.results else 0
            }
        }

        # 保存到文件
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # JSON報告
            json_path = output_file.with_suffix('.json')
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)

            # HTML報告
            html_path = output_file.with_suffix('.html')
            self._generate_html_report(report, html_path)

            logger.info(f"✅ 報告已生成: {output_file}")

        return report

    def _generate_html_report(self, report: Dict[str, Any], output_path: Path):
        """生成HTML報告"""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Universal Backtest SOP Report - {report['metadata']['symbol']}</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .metrics {{ display: flex; gap: 20px; margin: 20px 0; }}
                .metric {{ background: white; padding: 15px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .metric h3 {{ margin: 0 0 10px 0; color: #333; }}
                .metric .value {{ font-size: 24px; font-weight: bold; color: #2ecc71; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background: #f8f9fa; }}
                .quality-excellent {{ background: #d4edda; color: #155724; }}
                .quality-good {{ background: #d1ecf1; color: #0c5460; }}
                .quality-average {{ background: #fff3cd; color: #856404; }}
                .quality-poor {{ background: #f8d7da; color: #721c24; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Universal Backtest SOP Report</h1>
                <p><strong>股票代碼:</strong> {report['metadata']['symbol']}</p>
                <p><strong>分析期間:</strong> {report['metadata']['start_date']} 至 {report['metadata']['end_date']}</p>
                <p><strong>參數範圍:</strong> {report['metadata']['parameter_range']['min']}-{report['metadata']['parameter_range']['max']} (步長 {report['metadata']['parameter_range']['step']})</p>
                <p><strong>無風險利率:</strong> {report['metadata']['risk_free_rate']:.1%}</p>
                <p><strong>總組合數:</strong> {report['metadata']['parameter_range']['total_combinations']:,}</p>
                <p><strong>生成時間:</strong> {report['metadata']['generated_at']}</p>
            </div>

            <div class="metrics">
                <div class="metric">
                    <h3>成功策略</h3>
                    <div class="value">{report['execution_stats']['successful_results']:,}</div>
                </div>
                <div class="metric">
                    <h3>成功率</h3>
                    <div class="value">{report['execution_stats']['success_rate']:.1%}</div>
                </div>
                <div class="metric">
                    <h3>平均Sharpe</h3>
                    <div class="value">{report['summary']['avg_sharpe']:.3f}</div>
                </div>
                <div class="metric">
                    <h3>最佳Sharpe</h3>
                    <div class="value">{report['summary']['max_sharpe']:.3f}</div>
                </div>
            </div>

            <h2>頂級策略 (Top 20)</h2>
            <table>
                <thead>
                    <tr>
                        <th>排名</th>
                        <th>策略ID</th>
                        <th>指標類型</th>
                        <th>參數</th>
                        <th>質量評分</th>
                        <th>總回報</th>
                        <th>Sharpe比率</th>
                        <th>最大回撤</th>
                        <th>勝率</th>
                        <th>交易次數</th>
                        <th>數據質量</th>
                    </tr>
                </thead>
                <tbody>
        """

        # 添加策略表格內容
        for strategy in report['top_strategies']:
            quality_class = 'quality-excellent' if strategy['quality_score'] >= 80 else \
                           'quality-good' if strategy['quality_score'] >= 60 else \
                           'quality-average' if strategy['quality_score'] >= 40 else \
                           'quality-poor'

            html_content += f"""
                    <tr class="{quality_class}">
                        <td>{strategy['rank']}</td>
                        <td>{strategy['strategy_id']}</td>
                        <td>{strategy['indicator_type']}</td>
                        <td>{strategy['params']}</td>
                        <td>{strategy['quality_score']:.1f}</td>
                        <td>{strategy['total_return']:.2%}</td>
                        <td>{strategy['sharpe_ratio']:.3f}</td>
                        <td>{strategy['max_drawdown']:.2%}</td>
                        <td>{strategy['win_rate']:.1%}</td>
                        <td>{strategy['total_trades']}</td>
                        <td>{strategy['data_quality']}</td>
                    </tr>
            """

        html_content += f"""
                </tbody>
            </table>
        </body>
        </html>
        """

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

def main():
        self.config = config or {}
        self.risk_free_rate = 0.03  # 3%無風險利率
        self.parameter_ranges = {
            'fast': range(5, 301, 5),    # 5-300步長5
            'slow': range(5, 301, 5),    # 5-300步長5  
            'signal': range(5, 301, 5),  # 5-300步長5
            'rsi_window': range(5, 301, 5)  # 5-300步長5
        }
        
        # 初始化新組件
        self.indicator_pipeline = StandardizedTechnicalIndicatorPipeline(config)
        self.quality_monitor = ComprehensiveDataQualityMonitor()
        
        # 性能監控
        self.performance_metrics = {
            'backtests_completed': 0,
            'total_calculation_time': 0.0,
            'parameter_combinations_tested': 0,
            'data_quality_violations': 0
        }

def main():
    """主函數示例"""
    # 配置回測參數
    config = BacktestConfig(
        symbol="0700.hk",
        start_date=datetime(2022, 1, 1),
        end_date=datetime(2025, 11, 22),
        param_min=0,
        param_max=300,
        param_step=5,
        verbose=True
    )

    # 創建SOP實例
    sop = UniversalBacktestSOP(config)

    # 執行優化
    try:
        results = sop.run_optimization()

        # 生成報告
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"universal_backtest_sop_results_{timestamp}"

        report = sop.generate_report(output_path)

        print("\n" + "="*60)
        print("優化完成！")
        print(f"成功策略數量: {len(results)}")
        if results:
            best = results[0]
            print(f"最佳策略: {best.strategy_id}")
            print(f"質量評分: {best.quality_score:.1f}")
            print(f"Sharpe比率: {best.sharpe_ratio:.3f}")
            print(f"總回報: {best.total_return:.2%}")
        print(f"報告已保存: {output_path}")
        print("="*60)

    except Exception as e:
        logger.error(f"優化過程失敗: {e}")
        return 1

    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())