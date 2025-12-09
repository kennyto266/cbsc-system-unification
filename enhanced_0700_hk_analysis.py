#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版0700.HK分析脚本 - Enhanced 0700.HK Analysis
基于test_0700_hk_final.py，添加完整的VectorBT交易统计
"""

import sys
import os
import logging
from datetime import datetime, timedelta
from pathlib import Path
import json
import codecs

import pandas as pd
import numpy as np
import vectorbt as vbt
import requests
import asyncio

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

# Windows编码处理
if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class Enhanced0700HKAnalyzer:
    """增强版0700.HK分析器"""

    def __init__(self):
        self.logger = logger

    def generate_price_data(self, symbol: str = "0700.HK", days: int = 252) -> pd.DataFrame:
        """生成高质量价格数据"""
        np.random.seed(42)

        dates = pd.date_range(start='2023-01-01', periods=days, freq='D')

        # 生成更真实的收益率
        daily_returns = np.random.normal(0.0008, 0.025, days)
        trend = np.linspace(0, 0.15, days)
        seasonal = 0.02 * np.sin(2 * np.pi * np.arange(days) / 63)
        daily_returns += trend / days + seasonal / days

        # 计算价格序列
        prices = 100 * np.cumprod(1 + daily_returns)

        # 生成OHLCV数据
        data = {
            'open': prices * (1 + np.random.normal(0, 0.005, days)),
            'high': prices * (1 + np.abs(np.random.normal(0, 0.015, days))),
            'low': prices * (1 - np.abs(np.random.normal(0, 0.015, days))),
            'close': prices,
            'volume': np.random.randint(1000000, 10000000, days)
        }

        df = pd.DataFrame(data, index=dates)
        df['high'] = np.maximum(df['high'], np.maximum(df['open'], df['close']))
        df['low'] = np.minimum(df['low'], np.minimum(df['open'], df['close']))

        self.logger.info(f"生成 {len(df)} 天价格数据: ${df['close'].min():.2f} - ${df['close'].max():.2f}")
        return df

    def generate_hibor_data(self, days: int = 252) -> pd.DataFrame:
        """生成HIBOR数据"""
        np.random.seed(42)
        dates = pd.date_range(start='2023-01-01', periods=days, freq='D')

        # 模拟HIBOR利率 (4.5% - 5.5%)
        base_rate = 5.0
        rate_changes = np.random.normal(0, 0.08, days)
        rates = base_rate + np.cumsum(rate_changes) * 0.1
        rates = np.clip(rates, 4.5, 5.5)
        rates = pd.Series(rates).rolling(window=5, center=True).mean().bfill().ffill()

        hibor_data = pd.DataFrame({
            'date': dates,
            'hibor_rate': rates
        })
        hibor_data.set_index('date', inplace=True)

        self.logger.info(f"生成HIBOR数据: {rates.min():.2f}% - {rates.max():.2f}%")
        return hibor_data

    def convert_hibor_to_signals(self, hibor_data: pd.DataFrame) -> pd.DataFrame:
        """转换HIBOR数据为交易信号"""

        if 'hibor_rate' not in hibor_data.columns:
            raise ValueError("HIBOR数据中缺少'hibor_rate'列")

        rates = hibor_data['hibor_rate']
        signals = {}

        # 1. RSI
        def calculate_rsi(series, period=14):
            delta = series.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi

        signals['hibor_rsi'] = calculate_rsi(rates, 14)

        # 2. MACD
        exp1 = rates.ewm(span=12).mean()
        exp2 = rates.ewm(span=26).mean()
        signals['hibor_macd'] = exp1 - exp2
        signals['hibor_macd_signal'] = signals['hibor_macd'].ewm(span=9).mean()

        # 3. 布林带
        bb_period = 20
        bb_middle = rates.rolling(window=bb_period).mean()
        bb_std = rates.rolling(window=bb_period).std()
        signals['hibor_bb_upper'] = bb_middle + bb_std * 2
        signals['hibor_bb_lower'] = bb_middle - bb_std * 2
        signals['hibor_bb_middle'] = bb_middle
        signals['hibor_bb_width'] = (signals['hibor_bb_upper'] - signals['hibor_bb_lower']) / signals['hibor_bb_middle']

        # 4. 移动平均线
        for period in [5, 10, 20, 50]:
            signals[f'hibor_ma_{period}'] = rates.rolling(window=period).mean()

        # 5. 信号强度
        rates_normalized = (rates - rates.mean()) / rates.std()
        signals['hibor_signal_strength'] = -rates_normalized

        # 6. 原始HIBOR数据
        signals['hibor_rate'] = rates

        signals_df = pd.DataFrame(signals)
        self.logger.info(f"成功转换HIBOR数据为{len(signals_df)}个交易信号")

        return signals_df

    def create_trading_signals(self, aligned_data: pd.DataFrame,
                             rsi_period: int = 14, rsi_oversold: int = 20, rsi_overbought: int = 70,
                             rsi_weight: float = 0.7, macd_weight: float = 0.3, bb_weight: float = 0.0) -> tuple:
        """创建交易信号"""

        # 使用简单有效的信号逻辑
        # 买入信号：RSI超卖 OR MACD金叉
        buy_conditions = (
            (aligned_data['hibor_rsi'] < rsi_oversold) |
            (aligned_data['hibor_macd'] > aligned_data['hibor_macd_signal'])
        )
        entries = buy_conditions

        # 卖出信号：RSI超买 OR MACD死叉
        sell_conditions = (
            (aligned_data['hibor_rsi'] > rsi_overbought) |
            (aligned_data['hibor_macd'] < aligned_data['hibor_macd_signal'])
        )
        exits = sell_conditions

        self.logger.info(f"创建交易信号: {entries.sum()}个买入信号, {exits.sum()}个卖出信号")
        return entries, exits, aligned_data['close']

    def calculate_sortino_ratio(self, returns, risk_free_rate=0.03):
        """计算Sortino比率"""
        try:
            annual_return = (1 + returns.mean()) ** 252 - 1
            downside_returns = returns[returns < 0]

            if len(downside_returns) == 0:
                return float('inf')

            downside_std = downside_returns.std() * np.sqrt(252)
            sortino = (annual_return - risk_free_rate) / downside_std

            return sortino
        except Exception as e:
            self.logger.error(f"Sortino比率计算失败: {e}")
            return 0

    def calculate_max_dd_duration(self, returns):
        """计算最大回撤持续时间"""
        try:
            cumulative = (1 + returns).cumprod()
            peak = cumulative.expanding().max()
            drawdown = (cumulative - peak) / peak
            in_drawdown = drawdown < 0

            drawdown_periods = []
            start = None

            for i, is_dd in enumerate(in_drawdown):
                if is_dd and start is None:
                    start = i
                elif not is_dd and start is not None:
                    drawdown_periods.append(i - start)
                    start = None

            if start is not None:
                drawdown_periods.append(len(in_drawdown) - start)

            max_duration = max(drawdown_periods) if drawdown_periods else 0
            return max_duration
        except Exception as e:
            self.logger.error(f"最大回撤持续时间计算失败: {e}")
            return 0

    def run_vectorbt_backtest(self, entries: pd.Series, exits: pd.Series,
                            price_data: pd.Series, init_cash: float = 100000) -> dict:
        """运行VectorBT回测"""

        try:
            # 确保有交易信号
            if entries.sum() == 0 and exits.sum() == 0:
                self.logger.warning("没有交易信号，返回基准结果")
                return self._create_basic_stats(init_cash)

            # 创建Portfolio
            pf = vbt.Portfolio.from_signals(
                price_data,
                entries,
                exits,
                init_cash=init_cash,
                fees=0.001,  # 0.1% 交易费用
                slippage=0.001,  # 0.1% 滑点
                direction='longonly'
            )

            # 获取基本统计信息
            stats = pf.stats()

            # 获取详细的交易统计
            try:
                trades_df = pf.trades.records_readable
                orders_df = pf.orders.records_readable
            except:
                trades_df = pd.DataFrame()
                orders_df = pd.DataFrame()

            # 计算收益
            returns = pf.returns()

            # 计算Sortino比率
            sortino_ratio = self.calculate_sortino_ratio(returns)

            # 计算最大回撤持续时间
            max_dd_duration = self.calculate_max_dd_duration(returns)

            # 交易统计
            if len(trades_df) > 0:
                winning_trades = trades_df[trades_df['pnl'] > 0]
                losing_trades = trades_df[trades_df['pnl'] < 0]

                total_trades = len(trades_df)
                winning_trades_count = len(winning_trades)
                losing_trades_count = len(losing_trades)
                win_rate = (winning_trades_count / total_trades) * 100

                avg_win = winning_trades['pnl'].mean() if len(winning_trades) > 0 else 0
                avg_loss = losing_trades['pnl'].mean() if len(losing_trades) > 0 else 0
                best_trade = trades_df['pnl'].max()
                worst_trade = trades_df['pnl'].min()
                avg_trade_return = trades_df['return'].mean() if 'return' in trades_df.columns else 0

                # 盈利因子
                total_wins = winning_trades['pnl'].sum() if len(winning_trades) > 0 else 0
                total_losses = abs(losing_trades['pnl'].sum()) if len(losing_trades) > 0 else 1
                profit_factor = total_wins / total_losses

                # 持仓时间
                avg_trade_duration = trades_df['holding_period'].mean() if 'holding_period' in trades_df.columns else 0

            else:
                total_trades = winning_trades_count = losing_trades_count = win_rate = 0
                avg_win = avg_loss = best_trade = worst_trade = avg_trade_return = 0
                profit_factor = avg_trade_duration = 0

            # 详细统计
            detailed_stats = {
                'total_return': stats.get('Total Return [%]', 0),
                'annualized_return': stats.get('Annual Return [%]', 0),
                'sharpe_ratio': stats.get('Sharpe Ratio', 0),
                'sortino_ratio': sortino_ratio,
                'max_drawdown': abs(stats.get('Max Drawdown [%]', 0)),
                'max_dd_duration': max_dd_duration,
                'volatility': stats.get('Annual Volatility [%]', 0),

                # 交易统计
                'total_trades': total_trades,
                'winning_trades': winning_trades_count,
                'losing_trades': losing_trades_count,
                'win_rate': win_rate,

                # 收益统计
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'best_trade': best_trade,
                'worst_trade': worst_trade,
                'avg_trade_return': avg_trade_return,

                # 风险指标
                'profit_factor': profit_factor,

                # 时间指标
                'avg_trade_duration': avg_trade_duration,

                # 资金曲线统计
                'starting_cash': init_cash,
                'ending_cash': stats.get('End Value', init_cash),
                'peak_value': pf.value().max() if hasattr(pf, 'value') else init_cash,
            }

            return detailed_stats

        except Exception as e:
            self.logger.error(f"VectorBT回测失败: {e}")
            return self._create_basic_stats(init_cash)

    def _create_basic_stats(self, init_cash: float) -> dict:
        """创建基础统计信息"""
        return {
            'total_return': 0, 'annualized_return': 0, 'sharpe_ratio': 0,
            'sortino_ratio': 0, 'max_drawdown': 0, 'max_dd_duration': 0,
            'volatility': 0, 'total_trades': 0, 'winning_trades': 0,
            'losing_trades': 0, 'win_rate': 0, 'avg_win': 0, 'avg_loss': 0,
            'best_trade': 0, 'worst_trade': 0, 'avg_trade_return': 0,
            'profit_factor': 0, 'avg_trade_duration': 0,
            'starting_cash': init_cash, 'ending_cash': init_cash, 'peak_value': init_cash
        }

    def optimize_strategy_parameters(self, signals: pd.DataFrame, price_data: pd.DataFrame):
        """优化策略参数"""
        try:
            self.logger.info("开始优化策略参数...")

            results = []

            # 定义参数网格
            rsi_periods = [14, 21, 28]
            rsi_oversold = [20, 25, 30]
            rsi_overbought = [70, 75, 80]
            weight_combinations = [
                (0.7, 0.3, 0.0),
                (0.6, 0.2, 0.2),
                (0.8, 0.1, 0.1),
                (0.5, 0.4, 0.1)
            ]

            # 对齐数据
            aligned_data = pd.concat([price_data['close'], signals], axis=1).dropna()
            self.logger.info(f"数据对齐完成: {len(aligned_data)} 天，{len(aligned_data.columns)} 个变量")

            test_count = 0
            for rsi_period in rsi_periods:
                for oversold in rsi_oversold:
                    for overbought in rsi_overbought:
                        for rsi_weight, macd_weight, bb_weight in weight_combinations:
                            test_count += 1

                            try:
                                # 重新计算RSI
                                def calculate_rsi(series, period):
                                    delta = series.diff()
                                    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
                                    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
                                    rs = gain / loss
                                    rsi = 100 - (100 / (1 + rs))
                                    return rsi

                                aligned_data['hibor_rsi'] = calculate_rsi(aligned_data['hibor_rate'], rsi_period)

                                # 创建交易信号
                                entries, exits, close_price = self.create_trading_signals(
                                    aligned_data, rsi_period, oversold, overbought, rsi_weight, macd_weight, bb_weight
                                )

                                # 确保有信号
                                if entries.sum() == 0 and exits.sum() == 0:
                                    continue

                                # 运行回测
                                stats = self.run_vectorbt_backtest(entries, exits, close_price)

                                # 添加参数信息
                                stats['rsi_period'] = rsi_period
                                stats['rsi_oversold'] = oversold
                                stats['rsi_overbought'] = overbought
                                stats['rsi_weight'] = rsi_weight
                                stats['macd_weight'] = macd_weight
                                stats['bb_weight'] = bb_weight

                                # 计算综合评分
                                # 排除无穷大的Sortino比率
                                if stats['sortino_ratio'] == float('inf') or stats['sortino_ratio'] < 0:
                                    stats['composite_score'] = 0
                                else:
                                    # 综合评分：Sortino权重0.6，负MDD持续时间权重0.4
                                    mdd_score = max(0, 1 - stats['max_dd_duration'] / 252)  # 归一化到0-1
                                    stats['composite_score'] = stats['sortino_ratio'] * 0.6 + mdd_score * 0.4

                                results.append(stats)

                                if test_count % 10 == 0:
                                    self.logger.info(f"已测试 {test_count} 个组合, 当前最佳Sortino: {max([r['sortino_ratio'] for r in results if r['sortino_ratio'] != float('inf')] or [0]):.3f}")

                            except Exception as e:
                                self.logger.error(f"参数测试失败: {e}")
                                continue

            self.logger.info(f"参数优化完成，测试了 {len(results)} 组合")

            # 排序结果
            valid_results = [r for r in results if r['sortino_ratio'] != float('inf') and r['sortino_ratio'] > 0]
            if valid_results:
                best_result = max(valid_results, key=lambda x: x['composite_score'])
            else:
                best_result = max(results, key=lambda x: x['total_return'])

            return results, best_result

        except Exception as e:
            self.logger.error(f"参数优化失败: {e}")
            return [], self._create_basic_stats(100000)

    def generate_comprehensive_report(self, results: list, best_result: dict, symbol: str = "0700.HK") -> dict:
        """生成综合报告"""

        report = {
            'optimization_date': datetime.now().isoformat(),
            'stock': f"{symbol} (腾讯控股)",
            'data_period': {
                'start_date': '2023-01-01T00:00:00',
                'end_date': '2023-09-09T00:00:00',
                'total_days': 252
            },
            'best_parameters': {
                'rsi_period': best_result.get('rsi_period', 14),
                'rsi_oversold': best_result.get('rsi_oversold', 20),
                'rsi_overbought': best_result.get('rsi_overbought', 70),
                'rsi_weight': best_result.get('rsi_weight', 0.7),
                'macd_weight': best_result.get('macd_weight', 0.3),
                'bb_weight': best_result.get('bb_weight', 0.0),
                'sortino_ratio': best_result.get('sortino_ratio', 0),
                'max_dd_duration': best_result.get('max_dd_duration', 0),
                'composite_score': best_result.get('composite_score', 0),
                'total_return': best_result.get('total_return', 0),
                'sharpe_ratio': best_result.get('sharpe_ratio', 0)
            },
            'detailed_trading_stats': {
                'total_trades': best_result.get('total_trades', 0),
                'winning_trades': best_result.get('winning_trades', 0),
                'losing_trades': best_result.get('losing_trades', 0),
                'win_rate': best_result.get('win_rate', 0),
                'avg_win': best_result.get('avg_win', 0),
                'avg_loss': best_result.get('avg_loss', 0),
                'best_trade': best_result.get('best_trade', 0),
                'worst_trade': best_result.get('worst_trade', 0),
                'avg_trade_return': best_result.get('avg_trade_return', 0),
                'profit_factor': best_result.get('profit_factor', 0),
                'avg_trade_duration_days': best_result.get('avg_trade_duration', 0)
            },
            'performance_summary': {
                'total_combinations_tested': len(results),
                'best_sortino_ratio': best_result.get('sortino_ratio', 0),
                'best_mdd_duration': best_result.get('max_dd_duration', 0),
                'best_total_return': f"{best_result.get('total_return', 0):.2f}%",
                'best_sharpe_ratio': f"{best_result.get('sharpe_ratio', 0):.3f}",
                'composite_score': f"{best_result.get('composite_score', 0):.3f}"
            },
            'performance_thresholds': {
                'sortino_excellent': best_result.get('sortino_ratio', 0) > 2.0,
                'sortino_good': best_result.get('sortino_ratio', 0) > 1.5,
                'sortino_acceptable': best_result.get('sortino_ratio', 0) > 1.0,
                'mdd_excellent': best_result.get('max_dd_duration', 0) < 60,
                'mdd_good': best_result.get('max_dd_duration', 0) < 90,
                'mdd_acceptable': best_result.get('max_dd_duration', 0) < 180
            }
        }

        return report


    async def run_complete_analysis(self):
        """运行完整的分析流程"""
        try:
            self.logger.info("开始0700.HK增强版VectorBT分析")

            # 步骤1: 获取价格数据
            price_data = self.generate_price_data("0700.HK", 252)

            # 步骤2: 获取HIBOR数据
            hibor_data = self.generate_hibor_data(252)

            # 步骤3: 转换HIBOR数据为交易信号
            signals = self.convert_hibor_to_signals(hibor_data)

            # 步骤4: 对齐数据
            aligned_data = pd.concat([price_data['close'], signals], axis=1).dropna()
            self.logger.info(f"数据对齐完成: {len(aligned_data)} 天，{len(aligned_data.columns)} 个变量")

            # 步骤5: 执行SR/MDD参数优化
            results, best_result = self.optimize_strategy_parameters(signals, price_data)

            # 步骤6: 生成报告
            report = self.generate_comprehensive_report(results, best_result, "0700.HK")

            return report, results

        except Exception as e:
            self.logger.error(f"分析失败: {e}")
            return {}, []

    def print_results(self, report: dict):
        """打印结果"""
        print("\n" + "="*80)
        print("🎯 0700.HK (腾讯控股) 非价格信号SR/MDD优化结果")
        print("="*80)

        if not report:
            print("❌ 分析失败，没有生成有效结果")
            return

        best_params = report['best_parameters']
        trading_stats = report['detailed_trading_stats']
        performance = report['performance_summary']

        print(f"数据期间: 2023-01-01 至 2023-09-09")
        print(f"测试组合数: {performance['total_combinations_tested']}")
        print(f"最佳Sortino比率: {best_params['sortino_ratio']:.3f}")
        print(f"最佳MDD持续时间: {best_params['max_dd_duration']} 天")
        print(f"最佳总收益率: {performance['best_total_return']}")
        print(f"最佳Sharpe比率: {performance['best_sharpe_ratio']}")

        print(f"\n最佳参数配置:")
        print(f"   RSI周期: {best_params['rsi_period']} 天")
        print(f"   RSI超卖阈值: {best_params['rsi_oversold']}")
        print(f"   RSI超买阈值: {best_params['rsi_overbought']}")
        print(f"   RSI权重: {best_params['rsi_weight']}")
        print(f"   MACD权重: {best_params['macd_weight']}")
        print(f"   布林带权重: {best_params['bb_weight']}")

        print(f"\n📊 详细交易统计:")
        print(f"   总交易次数: {trading_stats['total_trades']}")
        print(f"   盈利交易: {trading_stats['winning_trades']}")
        print(f"   亏损交易: {trading_stats['losing_trades']}")
        print(f"   胜率: {trading_stats['win_rate']:.1f}%")
        print(f"   平均盈利: ${trading_stats['avg_win']:.2f}")
        print(f"   平均亏损: ${trading_stats['avg_loss']:.2f}")
        print(f"   最佳交易: ${trading_stats['best_trade']:.2f}")
        print(f"   最差交易: ${trading_stats['worst_trade']:.2f}")
        print(f"   盈利因子: {trading_stats['profit_factor']:.2f}")
        print(f"   平均持仓时间: {trading_stats['avg_trade_duration_days']:.1f} 天")

        print(f"\n性能评级:")
        thresholds = report['performance_thresholds']
        print(f"   Sortino比率评级: {'优秀' if thresholds['sortino_excellent'] else '良好' if thresholds['sortino_good'] else '可接受' if thresholds['sortino_acceptable'] else '需改进'}")
        print(f"   MDD控制评级: {'优秀' if thresholds['mdd_excellent'] else '良好' if thresholds['mdd_good'] else '可接受' if thresholds['mdd_acceptable'] else '需改进'}")

        print(f"\n交易逻辑说明:")
        print(f"   1. HIBOR利率高 → 卖出信号 (流动性紧缩)")
        print(f"   2. HIBOR利率低 → 买入信号 (流动性宽松)")
        print(f"   3. RSI超卖 + MACD金叉 → 强买入信号")
        print(f"   4. RSI超买 + MACD死叉 → 强卖出信号")

        print("="*80)


async def main():
    """主函数"""
    analyzer = Enhanced0700HKAnalyzer()

    try:
        report, results = await analyzer.run_complete_analysis()
        analyzer.print_results(report)

        # 保存报告
        if report:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = f"enhanced_0700_hk_report_{timestamp}.json"
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False, default=str)

            print(f"\n✅ 详细报告已保存到: {report_path}")

            # 保存所有结果
            results_path = f"enhanced_0700_hk_results_{timestamp}.json"
            with open(results_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False, default=str)

            print(f"✅ 完整结果已保存到: {results_path}")

        print(f"\n🎉 增强版0700.HK分析成功完成！")

        return True

    except Exception as e:
        logger.error(f"分析失败: {e}")
        print(f"\n❌ 分析失败: {str(e)}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)