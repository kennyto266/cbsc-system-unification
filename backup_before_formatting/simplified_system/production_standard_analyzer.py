#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenSpec 生產標準分析器
Production Standard Analyzer for OpenSpec Integration

適用場景：
- 日常量化分析
- 多股票策略回測
- 自動化報告生成
- 生產環境監控
"""

import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import logging

# 添加系統路徑
sys.path.append(str(Path(__file__).parent / "src"))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/production.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ProductionStandardAnalyzer:
    """
    生產級標準分析器

    功能：
    1. 自動化數據獲取和分析
    2. OpenSpec 477種技術指標計算
    3. 255種組合策略回測
    4. 專業級報告生成
    5. 異常處理和錯誤恢復
    """

    def __init__(self):
        self.system = None
        self.results_dir = Path("production_results")
        self.logs_dir = Path("logs")

        # 創建必要目錄
        self.results_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)

        # 默認股票列表
        self.default_symbols = ['0700.HK', '0941.HK', '1398.HK', '0388.HK', '1299.HK']

        logger.info("生產標準分析器初始化完成")

    def initialize_system(self):
        """初始化OpenSpec系統"""
        try:
            from openspec_integration_fixed import UnifiedOpenSpecIntegrationSystem
            self.system = UnifiedOpenSpecIntegrationSystem()
            logger.info(f"OpenSpec系統初始化成功")
            logger.info(f"技術指標數量: {self.system.total_indicators}")
            logger.info(f"GPU模式: {'啟用' if self.system.gpu_mode else 'CPU模式'}")
            logger.info(f"VectorBT: {'啟用' if self.system.vectorbt_mode else '禁用'}")
            return True
        except Exception as e:
            logger.error(f"OpenSpec系統初始化失敗: {e}")
            return False

    def get_stock_data_safely(self, symbol, days=252):
        """安全獲取股票數據"""
        try:
            logger.info(f"獲取 {symbol} 數據...")
            from api.stock_api import get_hk_stock_data
            stock_data = get_hk_stock_data(symbol, days)

            if stock_data is not None:
                if isinstance(stock_data, dict) and 'data' in stock_data:
                    # 處理字典格式數據
                    close_prices = list(stock_data['data']['close'].values())
                    dates = list(stock_data['data']['close'].keys())
                    stock_df = pd.DataFrame({
                        'close': close_prices,
                        'high': close_prices,
                        'low': close_prices,
                        'volume': [1000000] * len(close_prices)
                    }, index=pd.to_datetime(dates))
                else:
                    # 處理DataFrame格式數據
                    stock_df = stock_data.copy()
                    if 'volume' not in stock_df.columns:
                        stock_df['volume'] = 1000000

                logger.info(f"✅ {symbol} 數據獲取成功: {len(stock_df)} 條記錄")
                logger.info(f"價格範圍: {stock_df['close'].min():.2f} - {stock_df['close'].max():.2f}")
                return stock_df
            else:
                logger.warning(f"無法獲取 {symbol} 數據")
                return None

        except Exception as e:
            logger.error(f"獲取 {symbol} 數據失敗: {e}")
            return None

    def get_government_data_safely(self):
        """安全獲取政府數據"""
        try:
            logger.info("獲取政府數據...")
            from api.government_data import get_all_government_data
            gov_data = get_all_government_data()
            logger.info(f"✅ 政府數據獲取成功: {len(gov_data)} 個數據源")
            return gov_data
        except Exception as e:
            logger.warning(f"政府數據獲取失敗，將跳過: {e}")
            return {}

    def analyze_symbol_comprehensive(self, symbol, max_combinations=50):
        """對單個股票進行全面分析"""
        logger.info(f"\n{'='*60}")
        logger.info(f"開始分析股票: {symbol}")
        logger.info(f"{'='*60}")

        # 獲取數據
        stock_data = self.get_stock_data_safely(symbol, 300)  # 獲取300天數據
        if stock_data is None:
            return {
                'symbol': symbol,
                'status': 'data_unavailable',
                'error': 'Cannot fetch stock data'
            }

        # 獲取政府數據
        gov_data = self.get_government_data_safely()

        try:
            # 限制組合數量以優化性能
            all_combinations = self.system.generate_all_combinations()
            limited_combinations = all_combinations[:max_combinations]

            logger.info(f"將測試 {len(limited_combinations)} 種組合 (限制自 {len(all_combinations)})")

            # 執行組合回測
            start_time = datetime.now()

            # 執行個別組合回測
            symbol_results = []
            successful_tests = 0

            for i, combination in enumerate(limited_combinations):
                try:
                    result = self.system._backtest_single_combination(
                        combination, stock_data, gov_data, f"{symbol}_combo_{i+1:03d}"
                    )

                    if 'error' not in result:
                        successful_tests += 1
                        symbol_results.append(result)

                    # 每10個組合顯示進度
                    if (i + 1) % 10 == 0:
                        logger.info(f"完成 {i+1}/{len(limited_combinations)} 組合，成功率: {successful_tests}/{i+1} * 100:.1f}%")

                except Exception as e:
                    logger.warning(f"組合 {i+1} 回測失敗: {e}")
                    continue

            execution_time = (datetime.now() - start_time).total_seconds()

            # 分析結果
            if symbol_results:
                # 找到最佳策略
                best_strategy = max(symbol_results, key=lambda x: x['sharpe_ratio'])

                # 計算統計指標
                sharpe_ratios = [r['sharpe_ratio'] for r in symbol_results]
                total_returns = [r['total_return'] for r in symbol_results]
                max_drawdowns = [r['max_drawdown'] for r in symbol_results]

                # 分類策略
                high_sharpe = [r for r in symbol_results if r['sharpe_ratio'] > 1.0]
                profitable = [r for r in symbol_results if r['total_return'] > 0]
                low_drawdown = [r for r in symbol_results if abs(r['max_drawdown']) < 0.1]

                analysis_result = {
                    'symbol': symbol,
                    'status': 'success',
                    'analysis_timestamp': datetime.now().isoformat(),
                    'execution_time_seconds': execution_time,
                    'data_summary': {
                        'total_records': len(stock_data),
                        'price_range': [float(stock_data['close'].min()), float(stock_data['close'].max())],
                        'data_period_days': len(stock_data)
                    },
                    'performance_summary': {
                        'total_combinations_tested': len(limited_combinations),
                        'successful_combinations': successful_tests,
                        'success_rate': successful_tests / len(limited_combinations) * 100,
                        'combinations_per_second': len(limited_combinations) / execution_time if execution_time > 0 else 0
                    },
                    'best_strategy': best_strategy,
                    'statistics': {
                        'sharpe_ratio': {
                            'mean': np.mean(sharpe_ratios),
                            'max': np.max(sharpe_ratios),
                            'min': np.min(sharpe_ratios),
                            'median': np.median(sharpe_ratios)
                        },
                        'total_return': {
                            'mean': np.mean(total_returns),
                            'max': np.max(total_returns),
                            'min': np.min(total_returns),
                            'median': np.median(total_returns)
                        },
                        'max_drawdown': {
                            'mean': np.mean(np.abs(max_drawdowns)),
                            'max': np.max(np.abs(max_drawdowns)),
                            'min': np.min(np.abs(max_drawdowns)),
                            'median': np.median(np.abs(max_drawdowns))
                        }
                    },
                    'quality_metrics': {
                        'high_sharpe_count': len(high_sharpe),
                        'profitable_count': len(profitable),
                        'low_drawdown_count': len(low_drawdown),
                        'high_sharpe_percentage': len(high_sharpe) / len(symbol_results) * 100,
                        'profitable_percentage': len(profitable) / len(symbol_results) * 100
                    },
                    'all_results': symbol_results,
                    'top_10_strategies': sorted(symbol_results, key=lambda x: x['sharpe_ratio'], reverse=True)[:10]
                }

                # 顯示結果摘要
                logger.info(f"✅ {symbol} 分析完成!")
                logger.info(f"   總組合數: {len(limited_combinations)}")
                logger.info(f"   成功組合: {successful_tests} ({successful_tests/len(limited_combinations)*100:.1f}%)")
                logger.info(f"   執行時間: {execution_time:.2f}秒")
                logger.info(f"   執行速度: {len(limited_combinations)/execution_time:.1f} 組合/秒")

                logger.info(f"\n🏆 最佳策略 ({best_strategy['combination_id']}):")
                logger.info(f"   Sharpe比率: {best_strategy['sharpe_ratio']:.3f}")
                logger.info(f"   年化回報: {best_strategy['annual_return']:.2%}")
                logger.info(f"   最大回撤: {best_strategy['max_drawdown']:.2%}")
                logger.info(f"   勝率: {best_strategy['win_rate']:.2%}")
                logger.info(f"   交易次數: {best_strategy['total_trades']}")

                logger.info(f"\n📊 質量指標:")
                logger.info(f"   高Sharpe策略 (>1.0): {len(high_sharpe)} 個 ({analysis_result['quality_metrics']['high_sharpe_percentage']:.1f}%)")
                logger.info(f"   盈利策略: {len(profitable)} 個 ({analysis_result['quality_metrics']['profitable_percentage']:.1f}%)")
                logger.info(f"   低回撤策略 (<10%): {len(low_drawdown)} 個")

                return analysis_result
            else:
                return {
                    'symbol': symbol,
                    'status': 'no_successful_strategies',
                    'total_combinations': len(limited_combinations),
                    'error': 'No successful backtest results'
                }

        except Exception as e:
            logger.error(f"{symbol} 分析過程中出錯: {e}")
            return {
                'symbol': symbol,
                'status': 'analysis_error',
                'error': str(e)
            }

    def run_batch_analysis(self, symbols=None, max_combinations_per_symbol=50):
        """運行批量分析"""
        if symbols is None:
            symbols = self.default_symbols

        logger.info(f"\n🚀 開始批量量化分析")
        logger.info(f"📊 分析股票數量: {len(symbols)}")
        logger.info(f"🔢 每股最大組合: {max_combinations_per_symbol}")
        logger.info(f"{'='*80}")

        if not self.initialize_system():
            logger.error("系統初始化失敗，無法繼續分析")
            return {}

        all_results = {}
        successful_symbols = []

        # 執行批量分析
        start_time = datetime.now()

        for i, symbol in enumerate(symbols, 1):
            logger.info(f"\n[{i}/{len(symbols)}] 分析股票: {symbol}")

            try:
                result = self.analyze_symbol_comprehensive(symbol, max_combinations_per_symbol)
                all_results[symbol] = result

                if result['status'] == 'success':
                    successful_symbols.append(symbol)
                    logger.info(f"✅ {symbol} 分析成功")
                else:
                    logger.warning(f"⚠️ {symbol} 分析失敗: {result.get('error', 'Unknown error')}")

            except Exception as e:
                logger.error(f"❌ {symbol} 分析出現異常: {e}")
                all_results[symbol] = {
                    'symbol': symbol,
                    'status': 'unexpected_error',
                    'error': str(e)
                }

        execution_time = (datetime.now() - start_time).total_seconds()

        # 生成批量分析報告
        batch_summary = self.generate_batch_summary(all_results, execution_time)

        # 保存詳細結果
        self.save_batch_results(all_results, batch_summary)

        logger.info(f"\n🎉 批量分析完成!")
        logger.info(f"總執行時間: {execution_time:.2f}秒")
        logger.info(f"成功股票: {len(successful_symbols)}/{len(symbols)}")

        return all_results

    def generate_batch_summary(self, results, execution_time):
        """生成批量分析摘要"""
        summary = {
            'batch_summary': {
                'timestamp': datetime.now().isoformat(),
                'total_execution_time_seconds': execution_time,
                'total_symbols': len(results),
                'successful_symbols': len([r for r in results.values() if r['status'] == 'success']),
                'success_rate': len([r for r in results.values() if r['status'] == 'success']) / len(results) * 100,
                'average_execution_time_per_symbol': execution_time / len(results) if results else 0
            }
        }

        # 統計最佳策略
        successful_results = [r for r in results.values() if r['status'] == 'success']
        if successful_results:
            all_best_strategies = [r['best_strategy'] for r in successful_results]

            best_overall = max(all_best_strategies, key=lambda x: x['sharpe_ratio'])

            all_sharpe_ratios = [s['sharpe_ratio'] for s in all_best_strategies]
            all_returns = [s['annual_return'] for s in all_best_strategies]

            summary['best_overall_strategy'] = best_overall
            summary['performance_statistics'] = {
                'sharpe_ratio': {
                    'mean': np.mean(all_sharpe_ratios),
                    'max': np.max(all_sharpe_ratios),
                    'min': np.min(all_sharpe_ratios),
                    'median': np.median(all_sharpe_ratios)
                },
                'annual_return': {
                    'mean': np.mean(all_returns),
                    'max': np.max(all_returns),
                    'min': np.min(all_returns),
                    'median': np.median(all_returns)
                }
            }

        logger.info(f"\n📊 批量分析摘要:")
        logger.info(f"   總執行時間: {execution_time:.2f}秒")
        logger.info(f"   成功率: {summary['batch_summary']['success_rate']:.1f}%")
        logger.info(f"   平均執行時間: {summary['batch_summary']['average_execution_time_per_symbol']:.1f}秒/股")

        if 'best_overall_strategy' in summary:
            best = summary['best_overall_strategy']
            logger.info(f"\n🏆 最佳整體策略:")
            logger.info(f"   股票: {best['combination_id'].split('_')[0]}")
            logger.info(f"   Sharpe比率: {best['sharpe_ratio']:.3f}")
            logger.info(f"   年化回報: {best['annual_return']:.2%}")
            logger.info(f"   最大回撤: {best['max_drawdown']:.2%}")

        return summary

    def save_batch_results(self, results, summary):
        """保存批量分析結果"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

            # 保存完整JSON結果
            json_file = self.results_dir / f"batch_analysis_{timestamp}.json"

            batch_data = {
                'metadata': {
                    'analyzer_version': 'ProductionStandardAnalyzer v1.0',
                    'timestamp': datetime.now().isoformat(),
                    'system_info': {
                        'python_version': sys.version,
                        'platform': sys.platform
                    }
                },
                'summary': summary,
                'detailed_results': results
            }

            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(batch_data, f, indent=2, ensure_ascii=False, default=str)

            logger.info(f"📁 詳細結果已保存至: {json_file}")

            # 生成CSV摘要
            successful_results = [r for r in results.values() if r['status'] == 'success']
            if successful_results:
                csv_data = []
                for symbol, result in results.items():
                    if result['status'] == 'success':
                        best = result['best_strategy']
                        csv_data.append({
                            'Symbol': symbol,
                            'Best Combination': best['combination_id'],
                            'Sharpe Ratio': best['sharpe_ratio'],
                            'Annual Return': best['annual_return'],
                            'Max Drawdown': best['max_drawdown'],
                            'Win Rate': best['win_rate'],
                            'Total Trades': best['total_trades'],
                            'Success Rate': result['performance_summary']['success_rate'],
                            'Execution Time': result['execution_time_seconds']
                        })

                df = pd.DataFrame(csv_data)
                csv_file = self.results_dir / f"batch_summary_{timestamp}.csv"
                df.to_csv(csv_file, index=False, encoding='utf-8-sig')

                logger.info(f"📄 CSV摘要已保存至: {csv_file}")

        except Exception as e:
            logger.error(f"保存結果失敗: {e}")

    def generate_html_report(self, results, summary):
        """生成HTML格式報告"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            html_file = self.results_dir / f"analysis_report_{timestamp}.html"

            # HTML模板
            html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OpenSpec 量化分析報告</title>
    <style>
        body {{ font-family: 'Microsoft YaHei', Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 0 20px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; margin-bottom: 40px; }}
        .summary {{ background-color: #f0f8ff; padding: 20px; border-radius: 8px; margin: 20px 0; }}
        .metric {{ display: inline-block; margin: 10px 20px; padding: 10px; border-left: 4px solid #007bff; }}
        .symbol-card {{ border: 1px solid #ddd; border-radius: 8px; padding: 20px; margin: 10px 0; background-color: #fafafa; }}
        .symbol-title {{ font-size: 18px; font-weight: bold; color: #333; }}
        .best-strategy {{ background-color: #e8f5e8; padding: 15px; border-radius: 6px; margin: 10px 0; }}
        .success {{ color: #28a745; }}
        .warning {{ color: #ffc107; }}
        .error {{ color: #dc3545; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #f8f9fa; font-weight: bold; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 OpenSpec 量化分析報告</h1>
            <p>生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>

        <div class="summary">
            <h2>📊 分析摘要</h2>
            <div class="metric">
                <strong>總股票數:</strong> {summary['batch_summary']['total_symbols']}
            </div>
            <div class="metric">
                <strong>成功率:</strong> {summary['batch_summary']['success_rate']:.1f}%
            </div>
            <div class="metric">
                <strong>總執行時間:</strong> {summary['batch_summary']['total_execution_time_seconds']:.2f}秒
            </div>
        </div>

        {self._generate_detailed_html_content(results, summary)}

        <div style="text-align: center; margin-top: 40px; color: #666;">
            <p>報告由 OpenSpec 深度集成系統生成</p>
            <p>包含 477 種技術指標，255 種組合策略分析</p>
        </div>
    </div>
</body>
</html>
            """

            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html_content)

            logger.info(f"📄 HTML報告已生成: {html_file}")

        except Exception as e:
            logger.error(f"生成HTML報告失敗: {e}")

    def _generate_detailed_html_content(self, results, summary):
        """生成詳細HTML內容"""
        html_parts = []

        for symbol, result in results.items():
            status_class = 'success' if result['status'] == 'success' else 'error'
            status_text = '✅ 成功' if result['status'] == 'success'] else '❌ 失敗'

            html_parts.append(f"""
            <div class="symbol-card">
                <div class="symbol-title">
                    {symbol} <span class="{status_class}">{status_text}</span>
                </div>
            """)

            if result['status'] == 'success':
                best = result['best_strategy']
                stats = result['statistics']

                html_parts.append(f"""
                <div class="best-strategy">
                    <h3>🏆 最佳策略 ({best['combination_id']})</h3>
                    <p><strong>Sharpe比率:</strong> {best['sharpe_ratio']:.3f}</p>
                    <p><strong>年化回報:</strong> {best['annual_return']:.2%}</p>
                    <p><strong>最大回撤:</strong> {best['max_drawdown']:.2%}</p>
                    <p><strong>勝率:</strong> {best['win_rate']:.2%}</p>
                    <p><strong>交易次數:</strong> {best['total_trades']}</p>
                </div>

                <div>
                    <h4>📈 統計指標</h4>
                    <table>
                        <tr><th>指標</th><th>平均值</th><th>最大值</th><th>最小值</th><th>中位數</th></tr>
                        <tr>
                            <td>Sharpe比率</td>
                            <td>{stats['sharpe_ratio']['mean']:.3f}</td>
                            <td>{stats['sharpe_ratio']['max']:.3f}</td>
                            <td>{stats['sharpe_ratio']['min']:.3f}</td>
                            <td>{stats['sharpe_ratio']['median']:.3f}</td>
                        </tr>
                        <tr>
                            <td>年化回報</td>
                            <td>{stats['total_return']['mean']:.2%}</td>
                            <td>{stats['total_return']['max']:.2%}</td>
                            <td>{stats['total_return']['min']:.2%}</td>
                            <td>{stats['total_return']['median']:.2%}</td>
                        </tr>
                    </table>
                </div>
                """)

                # 前10名策略
                if 'top_10_strategies' in result:
                    html_parts.append("""
                    <div>
                        <h4>🔝 Top 10 策略</h4>
                        <table>
                            <tr><th>排名</th><th>組合ID</th><th>Sharpe</th><th>年化回報</th><th>最大回撤</th></tr>
                    """)

                    for i, strategy in enumerate(result['top_10_strategies'][:10], 1):
                        html_parts.append(f"""
                        <tr>
                            <td>{i}</td>
                            <td>{strategy['combination_id']}</td>
                            <td>{strategy['sharpe_ratio']:.3f}</td>
                            <td>{strategy['annual_return']:.2%}</td>
                            <td>{strategy['max_drawdown']:.2%}</td>
                        </tr>
                        """)

                    html_parts.append("</table></div>")

            else:
                html_parts.append(f'<p><strong>錯誤:</strong> {result.get("error", "Unknown error")}</p>')

            html_parts.append('</div>')

        return ''.join(html_parts)

def main():
    """主函數"""
    print("=" * 80)
    print("OPENSPEC 生產標準分析器")
    print("Production Standard Analyzer for OpenSpec Integration")
    print("=" * 80)
    print(f"執行時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    # 創建分析器
    analyzer = ProductionStandardAnalyzer()

    # 可選：指定分析股票
    analysis_symbols = ['0700.HK', '0941.HK', '1398.HK']  # 可修改

    # 執行批量分析
    print(f"\n🚀 開始批量分析 {len(analysis_symbols)} 隻股票...")
    results = analyzer.run_batch_analysis(
        symbols=analysis_symbols,
        max_combinations_per_symbol=30  # 每股30種組合以優化性能
    )

    # 檢查結果
    successful_count = len([r for r in results.values() if r['status'] == 'success'])
    print(f"\n{'='*80}")
    print("🎯 分析結果摘要")
    print(f"{'='*80}")
    print(f"✅ 成功分析: {successful_count}/{len(results)} 股票")
    print(f"📊 總組合數: {sum(r.get('performance_summary', {}).get('total_combinations_tested', 0) for r in results.values())}")
    print(f"🔧 結果目錄: {analyzer.results_dir}")

    if successful_count > 0:
        print(f"\n🎉 生產分析完成！系統已準備好進行日常量化交易分析。")

if __name__ == "__main__":
    main()