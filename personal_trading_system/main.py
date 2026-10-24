#!/usr/bin/env python3
"""
Personal Trading System CLI
个人交易系统命令行界面
基于VectorBT的简化量化交易工具
"""

import argparse
import logging
import sys
from datetime import datetime, date, timedelta
from typing import List, Dict, Any
import json
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from vectorbt_engine import PersonalVectorBTEngine, BacktestResult
from hkma_data_adapter import HKMADataAdapter
from strategy_templates import StrategyFactory, get_strategy_function
from config import get_config

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PersonalTradingCLI:
    """个人交易系统命令行界面"""

    def __init__(self):
        self.engine = PersonalVectorBTEngine()
        self.hkma_adapter = HKMADataAdapter()
        self.config = get_config()

    def print_banner(self):
        """打印系统横幅"""
        print("=" * 60)
        print("         个人量化交易系统 v1.0")
        print("    Personal Quantitative Trading System")
        print("=" * 60)
        print("基于VectorBT的专业回测引擎")
        print("集成HKMA香港金管局经济数据")
        print("支持RSI、MACD、移动平均、布林带等经典策略")
        print("=" * 60)
        print()

    def run_single_backtest(self, args) -> None:
        """
        运行单个策略回测

        Args:
            args: 命令行参数
        """
        try:
            print(f"🚀 开始单策略回测: {args.strategy} - {args.symbol}")
            print()

            # 验证策略
            if args.strategy not in StrategyFactory.get_available_strategies():
                print(f"❌ 不支持的策略: {args.strategy}")
                print(f"可用策略: {', '.join(StrategyFactory.get_available_strategies())}")
                return

            # 解析日期
            start_date = self._parse_date(args.start_date)
            end_date = self._parse_date(args.end_date)

            if start_date >= end_date:
                print("❌ 开始日期必须早于结束日期")
                return

            # 解析参数
            params = self._parse_strategy_params(args.strategy, args.params)

            print(f"📊 回测配置:")
            print(f"  股票代码: {args.symbol}")
            print(f"  策略: {args.strategy}")
            print(f"  时间范围: {start_date} - {end_date}")
            print(f"  参数: {params}")
            print()

            # 获取HKMA数据（可选）
            hkma_data = None
            if args.use_hkma:
                print("📈 获取HKMA经济数据...")
                try:
                    hkma_data = self.hkma_adapter.get_hibor_data(start_date, end_date)
                    print(f"✅ 成功获取 {len(hkma_data)} 条HIBOR数据")
                except Exception as e:
                    print(f"⚠️ 获取HKMA数据失败: {e}")
                    print("继续使用股票数据进行回测...")
                print()

            # 执行回测
            strategy_func = get_strategy_function(args.strategy)
            result = self.engine.backtest_strategy(
                symbol=args.symbol,
                start_date=start_date,
                end_date=end_date,
                strategy_func=strategy_func,
                strategy_name=args.strategy,
                parameters=params,
                hkma_data=hkma_data
            )

            # 显示结果
            self._print_backtest_result(result)

            # 保存结果
            if args.output:
                self._save_result(result, args.output)

        except Exception as e:
            print(f"❌ 回测失败: {e}")
            logger.error(f"回测失败: {e}", exc_info=True)

    def run_optimization(self, args) -> None:
        """
        运行策略参数优化

        Args:
            args: 命令行参数
        """
        try:
            print(f"🔬 开始策略优化: {args.strategy} - {args.symbol}")
            print()

            # 验证策略
            if args.strategy not in StrategyFactory.get_available_strategies():
                print(f"❌ 不支持的策略: {args.strategy}")
                return

            # 解析日期
            start_date = self._parse_date(args.start_date)
            end_date = self._parse_date(args.end_date)

            # 获取参数网格
            strategy = StrategyFactory.create_strategy(args.strategy)
            param_grid = strategy.get_param_grid()

            print(f"🔍 优化配置:")
            print(f"  股票代码: {args.symbol}")
            print(f"  策略: {args.strategy}")
            print(f"  时间范围: {start_date} - {end_date}")
            print(f"  优化目标: {args.objective}")
            print(f"  参数网格: {param_grid}")
            print()

            # 获取HKMA数据（可选）
            hkma_data = None
            if args.use_hkma:
                print("📈 获取HKMA经济数据...")
                try:
                    hkma_data = self.hkma_adapter.get_hibor_data(start_date, end_date)
                    print(f"✅ 成功获取 {len(hkma_data)} 条HIBOR数据")
                except Exception as e:
                    print(f"⚠️ 获取HKMA数据失败: {e}")
                print()

            # 执行优化
            strategy_func = get_strategy_function(args.strategy)
            optimization_result = self.engine.optimize_strategy(
                symbol=args.symbol,
                start_date=start_date,
                end_date=end_date,
                strategy_func=strategy_func,
                param_grid=param_grid,
                objective=args.objective,
                hkma_data=hkma_data
            )

            # 显示优化结果
            self._print_optimization_result(optimization_result, args.strategy)

            # 保存结果
            if args.output:
                self._save_optimization_result(optimization_result, args.output)

        except Exception as e:
            print(f"❌ 优化失败: {e}")
            logger.error(f"优化失败: {e}", exc_info=True)

    def run_comparison(self, args) -> None:
        """
        运行多策略比较

        Args:
            args: 命令行参数
        """
        try:
            print(f"🏆 开始多策略比较: {args.symbols}")
            print()

            # 解析符号列表
            symbols = [s.strip() for s in args.symbols.split(',')]
            strategies = args.strategies.split(',') if args.strategies else StrategyFactory.get_available_strategies()

            # 解析日期
            start_date = self._parse_date(args.start_date)
            end_date = self._parse_date(args.end_date)

            print(f"📊 比较配置:")
            print(f"  股票代码: {symbols}")
            print(f"  策略列表: {strategies}")
            print(f"  时间范围: {start_date} - {end_date}")
            print()

            results = []

            for symbol in symbols:
                for strategy in strategies:
                    try:
                        print(f"⏳ 正在测试: {strategy} on {symbol}")

                        # 获取默认参数
                        strategy_obj = StrategyFactory.create_strategy(strategy)
                        params = strategy_obj.get_default_params()

                        # 执行回测
                        strategy_func = get_strategy_function(strategy)
                        result = self.engine.backtest_strategy(
                            symbol=symbol,
                            start_date=start_date,
                            end_date=end_date,
                            strategy_func=strategy_func,
                            strategy_name=strategy,
                            parameters=params
                        )

                        results.append(result)

                    except Exception as e:
                        logger.warning(f"策略测试失败 {strategy} on {symbol}: {e}")
                        continue

            # 显示比较结果
            self._print_comparison_results(results)

            # 保存结果
            if args.output:
                self._save_comparison_results(results, args.output)

        except Exception as e:
            print(f"❌ 比较失败: {e}")
            logger.error(f"比较失败: {e}", exc_info=True)

    def list_strategies(self, args) -> None:
        """列出可用策略"""
        print("📚 可用策略列表:")
        print()

        for strategy_name in StrategyFactory.get_available_strategies():
            strategy_info = StrategyFactory.get_strategy_info(strategy_name)
            print(f"🎯 {strategy_name}")
            print(f"   名称: {strategy_info['name']}")
            print(f"   默认参数: {strategy_info['default_params']}")
            print(f"   参数范围: {strategy_info['param_grid']}")
            print()

    def check_system(self, args) -> None:
        """检查系统状态"""
        print("🔧 系统状态检查:")
        print()

        # 检查VectorBT
        try:
            import vectorbt as vbt
            print("✅ VectorBT: 已安装")
        except ImportError:
            print("❌ VectorBT: 未安装")

        # 检查配置
        try:
            config_summary = self.config.get_config_summary()
            print("✅ 配置: 正常")
            for key, value in config_summary.items():
                print(f"   {key}: {value}")
        except Exception as e:
            print(f"❌ 配置: {e}")

        # 检查数据目录
        data_dir = Path(self.config.hkma.cache_dir)
        if data_dir.exists():
            print(f"✅ 数据目录: {data_dir}")
        else:
            print(f"⚠️ 数据目录: 不存在，将自动创建")

        # 检查默认股票
        try:
            default_symbols = self.config.get_default_symbols()
            print(f"✅ 默认股票: {len(default_symbols)} 只")
        except Exception as e:
            print(f"❌ 默认股票: {e}")

        print()

    def _parse_date(self, date_str: str) -> date:
        """解析日期字符串"""
        try:
            if date_str == 'today':
                return date.today()
            elif date_str == '1y':
                return date.today() - timedelta(days=365)
            elif date_str == '6m':
                return date.today() - timedelta(days=180)
            elif date_str == '3m':
                return date.today() - timedelta(days=90)
            elif date_str == '1m':
                return date.today() - timedelta(days=30)
            else:
                return datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            raise ValueError(f"不支持的日期格式: {date_str}")

    def _parse_strategy_params(self, strategy: str, param_str: str) -> Dict[str, Any]:
        """解析策略参数"""
        if not param_str:
            # 使用默认参数
            strategy_obj = StrategyFactory.create_strategy(strategy)
            return strategy_obj.get_default_params()

        try:
            # 解析JSON格式参数
            params = json.loads(param_str)
            return params
        except json.JSONDecodeError:
            # 解析key=value格式
            params = {}
            for item in param_str.split(','):
                if '=' in item:
                    key, value = item.strip().split('=', 1)
                    # 尝试转换为数字
                    try:
                        if '.' in value:
                            value = float(value)
                        else:
                            value = int(value)
                    except ValueError:
                        pass  # 保持字符串
                    params[key.strip()] = value
            return params

    def _print_backtest_result(self, result: BacktestResult) -> None:
        """打印回测结果"""
        print("📈 回测结果")
        print("=" * 50)
        print(f"股票代码: {result.symbol}")
        print(f"策略名称: {result.strategy_name}")
        print(f"策略参数: {result.parameters}")
        print()
        print("💰 收益指标:")
        print(f"  总回报: {result.total_return:.2%}")
        print(f"  年化回报: {result.annualized_return:.2%}")
        print(f"  最终资金: {result.final_capital:,.2f}")
        print()
        print("⚖️ 风险指标:")
        print(f"  夏普比率: {result.sharpe_ratio:.3f}")
        print(f"  最大回撤: {result.max_drawdown:.2%}")
        print(f"  胜率: {result.win_rate:.2%}")
        print(f"  交易次数: {result.total_trades}")
        print()
        print("=" * 50)

    def _print_optimization_result(self, result: Dict[str, Any], strategy_name: str) -> None:
        """打印优化结果"""
        print("🎯 参数优化结果")
        print("=" * 50)
        print(f"策略: {strategy_name}")
        print(f"测试组合数: {result['total_combinations']}")
        print(f"最佳分数: {result['best_score']:.4f}")
        print()
        print("🏆 最佳参数:")
        for param, value in result['best_parameters'].items():
            print(f"  {param}: {value}")
        print()

        # 显示前5个结果
        print("📊 Top 5 结果:")
        print("排名  |  参数组合  |  夏普比率  |  总回报  |  最大回撤")
        print("-" * 70)

        sorted_results = sorted(
            result['all_results'],
            key=lambda x: x['sharpe_ratio'],
            reverse=True
        )[:5]

        for i, res in enumerate(sorted_results, 1):
            params_str = str(res['parameters'])
            if len(params_str) > 20:
                params_str = params_str[:17] + "..."
            print(f"{i:2d}    | {params_str:20s} | {res['sharpe_ratio']:8.3f} | {res['total_return']:7.2%} | {res['max_drawdown']:7.2%}")

        print()
        print("=" * 50)

    def _print_comparison_results(self, results: List[BacktestResult]) -> None:
        """打印比较结果"""
        if not results:
            print("❌ 没有有效的比较结果")
            return

        print("🏆 策略比较结果")
        print("=" * 80)
        print("股票   |  策略   |  总回报   |  夏普比率 |  最大回撤 |  交易次数")
        print("-" * 80)

        # 按夏普比率排序
        sorted_results = sorted(results, key=lambda x: x.sharpe_ratio, reverse=True)

        for result in sorted_results:
            symbol = result.symbol
            strategy = result.strategy_name
            total_return = result.total_return
            sharpe = result.sharpe_ratio
            max_dd = result.max_drawdown
            trades = result.total_trades

            print(f"{symbol:6s} | {strategy:6s} | {total_return:7.2%} | {sharpe:8.3f} | {max_dd:7.2%} | {trades:8d}")

        print("=" * 80)

        # 显示最佳策略
        best_result = sorted_results[0]
        print()
        print("🥇 最佳策略:")
        print(f"  股票: {best_result.symbol}")
        print(f"  策略: {best_result.strategy_name}")
        print(f"  夏普比率: {best_result.sharpe_ratio:.3f}")
        print(f"  总回报: {best_result.total_return:.2%}")
        print(f"  参数: {best_result.parameters}")

    def _save_result(self, result: BacktestResult, filename: str) -> None:
        """保存回测结果"""
        try:
            result_dict = {
                'symbol': result.symbol,
                'strategy': result.strategy_name,
                'parameters': result.parameters,
                'total_return': result.total_return,
                'annualized_return': result.annualized_return,
                'sharpe_ratio': result.sharpe_ratio,
                'max_drawdown': result.max_drawdown,
                'win_rate': result.win_rate,
                'total_trades': result.total_trades,
                'final_capital': result.final_capital,
                'trades': result.trades
            }

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result_dict, f, ensure_ascii=False, indent=2, default=str)

            print(f"✅ 结果已保存到: {filename}")

        except Exception as e:
            print(f"❌ 保存结果失败: {e}")

    def _save_optimization_result(self, result: Dict[str, Any], filename: str) -> None:
        """保存优化结果"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2, default=str)

            print(f"✅ 优化结果已保存到: {filename}")

        except Exception as e:
            print(f"❌ 保存优化结果失败: {e}")

    def _save_comparison_results(self, results: List[BacktestResult], filename: str) -> None:
        """保存比较结果"""
        try:
            comparison_data = []
            for result in results:
                comparison_data.append({
                    'symbol': result.symbol,
                    'strategy': result.strategy_name,
                    'parameters': result.parameters,
                    'total_return': result.total_return,
                    'sharpe_ratio': result.sharpe_ratio,
                    'max_drawdown': result.max_drawdown,
                    'win_rate': result.win_rate,
                    'total_trades': result.total_trades,
                    'final_capital': result.final_capital
                })

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(comparison_data, f, ensure_ascii=False, indent=2, default=str)

            print(f"✅ 比较结果已保存到: {filename}")

        except Exception as e:
            print(f"❌ 保存比较结果失败: {e}")


def create_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description='个人量化交易系统 - 基于VectorBT的回测工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # RSI策略回测
  python main.py backtest --strategy RSI --symbol 0700.HK --start-date 1y

  # MACD策略优化
  python main.py optimize --strategy MACD --symbol 0700.HK --start-date 6m --objective sharpe_ratio

  # 多策略比较
  python main.py compare --symbols 0700.HK,0941.HK --strategies RSI,MACD --start-date 1y

  # 查看可用策略
  python main.py list-strategies

  # 系统状态检查
  python main.py check
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # 回测命令
    backtest_parser = subparsers.add_parser('backtest', help='运行单策略回测')
    backtest_parser.add_argument('--strategy', required=True, help='策略名称')
    backtest_parser.add_argument('--symbol', required=True, help='股票代码')
    backtest_parser.add_argument('--start-date', default='1y', help='开始日期 (YYYY-MM-DD 或 1y/6m/3m/1m/today)')
    backtest_parser.add_argument('--end-date', default='today', help='结束日期')
    backtest_parser.add_argument('--params', help='策略参数 (JSON格式或 key=value,key=value)')
    backtest_parser.add_argument('--use-hkma', action='store_true', help='使用HKMA经济数据')
    backtest_parser.add_argument('--output', help='结果保存路径')

    # 优化命令
    optimize_parser = subparsers.add_parser('optimize', help='运行策略参数优化')
    optimize_parser.add_argument('--strategy', required=True, help='策略名称')
    optimize_parser.add_argument('--symbol', required=True, help='股票代码')
    optimize_parser.add_argument('--start-date', default='6m', help='开始日期')
    optimize_parser.add_argument('--end-date', default='today', help='结束日期')
    optimize_parser.add_argument('--objective', default='sharpe_ratio', choices=['sharpe_ratio', 'total_return', 'max_drawdown'], help='优化目标')
    optimize_parser.add_argument('--use-hkma', action='store_true', help='使用HKMA经济数据')
    optimize_parser.add_argument('--output', help='结果保存路径')

    # 比较命令
    compare_parser = subparsers.add_parser('compare', help='运行多策略比较')
    compare_parser.add_argument('--symbols', required=True, help='股票代码列表 (逗号分隔)')
    compare_parser.add_argument('--strategies', help='策略列表 (逗号分隔，默认全部)')
    compare_parser.add_argument('--start-date', default='1y', help='开始日期')
    compare_parser.add_argument('--end-date', default='today', help='结束日期')
    compare_parser.add_argument('--output', help='结果保存路径')

    # 策略列表命令
    subparsers.add_parser('list-strategies', help='列出可用策略')

    # 系统检查命令
    subparsers.add_parser('check', help='检查系统状态')

    return parser


def main():
    """主函数"""
    try:
        parser = create_parser()
        args = parser.parse_args()

        if not args.command:
            parser.print_help()
            return

        # 创建CLI实例
        cli = PersonalTradingCLI()

        # 显示横幅（除了help和check命令）
        if args.command not in ['check']:
            cli.print_banner()

        # 执行命令
        if args.command == 'backtest':
            cli.run_single_backtest(args)
        elif args.command == 'optimize':
            cli.run_optimization(args)
        elif args.command == 'compare':
            cli.run_comparison(args)
        elif args.command == 'list-strategies':
            cli.list_strategies(args)
        elif args.command == 'check':
            cli.check_system(args)

    except KeyboardInterrupt:
        print("\n👋 用户中断操作")
        sys.exit(0)
    except Exception as e:
        print(f"❌ 系统错误: {e}")
        logger.error(f"系统错误: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()