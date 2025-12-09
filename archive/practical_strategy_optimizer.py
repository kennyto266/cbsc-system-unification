#!/usr/bin/env python3
"""
Practical Strategy Optimizer - 實用策略優化器
使用步長5，獨立測試每個策略，實用高效的32核心並行處理

Usage: python practical_strategy_optimizer.py --symbol 0700.HK --workers 32 --strategy all
"""

import argparse
import requests
import pandas as pd
import numpy as np
import json
import logging
from datetime import datetime
import multiprocessing as mp
from functools import partial
import vectorbt as vbt
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_stock_data(symbol, days=1095):
    """獲取股價數據"""
    try:
        url = "http://18.180.162.113:9191/inst/getInst"
        params = {"symbol": symbol.lower(), "duration": days}

        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()
        close_data = data['data']['close']
        dates = list(close_data.keys())
        closes = list(close_data.values())

        df = pd.DataFrame({
            'date': pd.to_datetime(dates),
            'close': [float(x) for x in closes]
        })
        df.set_index('date', inplace=True)
        df.sort_index(inplace=True)

        # 添加OHLCV
        df['open'] = df['close'].shift(1).fillna(df['close'])
        df['high'] = df['close'] * 1.01
        df['low'] = df['close'] * 0.99
        df['volume'] = np.random.randint(1000000, 5000000, len(df))

        logger.info(f"獲取成功: {len(df)}天數據, 價格範圍: {df['close'].min():.2f} - {df['close'].max():.2f}")
        return df

    except Exception as e:
        logger.error(f"獲取數據失敗: {str(e)}")
        return None

def generate_rsi_parameters():
    """生成RSI參數 - 步長5策略"""
    rsi_periods = list(range(5, 31, 5))  # 5, 10, 15, 20, 25, 30
    overbought_thresholds = list(range(65, 86, 5))  # 65, 70, 75, 80, 85
    oversold_thresholds = list(range(15, 36, 5))  # 15, 20, 25, 30, 35

    params = []
    for period in rsi_periods:
        for ob in overbought_thresholds:
            for os in oversold_thresholds:
                if ob > os:  # 合理性檢查
                    params.append({
                        'strategy': 'RSI',
                        'rsi_period': period,
                        'overbought_threshold': ob,
                        'oversold_threshold': os,
                        'stop_loss': 0.10,
                        'take_profit': 0.20,
                        'position_size': 0.5
                    })
    return params

def generate_macd_parameters():
    """生成MACD參數"""
    fast_periods = list(range(8, 17, 2))  # 8, 10, 12, 14, 16
    slow_periods = list(range(20, 31, 2))  # 20, 22, 24, 26, 28, 30
    signal_periods = list(range(8, 13, 1))  # 8, 9, 10, 11, 12

    params = []
    for fast in fast_periods:
        for slow in slow_periods:
            for signal in signal_periods:
                if fast < slow:  # 合理性檢查
                    params.append({
                        'strategy': 'MACD',
                        'macd_fast': fast,
                        'macd_slow': slow,
                        'macd_signal': signal,
                        'stop_loss': 0.10,
                        'take_profit': 0.20,
                        'position_size': 0.5
                    })
    return params

def generate_bollinger_parameters():
    """生成布林帶參數"""
    periods = list(range(10, 26, 5))  # 10, 15, 20, 25
    std_devs = [1.5, 2.0, 2.5]  # 標準差倍數

    params = []
    for period in periods:
        for std in std_devs:
            params.append({
                'strategy': 'Bollinger',
                'bb_period': period,
                'bb_std': std,
                'stop_loss': 0.10,
                'take_profit': 0.20,
                'position_size': 0.5
            })
    return params

def generate_combined_parameters():
    """生成組合策略參數 - 小規模但有意義的組合"""
    # RSI精選參數
    rsi_params = [
        {'rsi_period': 14, 'overbought_threshold': 70, 'oversold_threshold': 30},
        {'rsi_period': 10, 'overbought_threshold': 75, 'oversold_threshold': 25},
        {'rsi_period': 20, 'overbought_threshold': 65, 'oversold_threshold': 35}
    ]

    # MACD精選參數
    macd_params = [
        {'macd_fast': 12, 'macd_slow': 26, 'macd_signal': 9},
        {'macd_fast': 10, 'macd_slow': 24, 'macd_signal': 8}
    ]

    # 布林帶精選參數
    bb_params = [
        {'bb_period': 20, 'bb_std': 2.0},
        {'bb_period': 15, 'bb_std': 1.5}
    ]

    # 風險管理參數
    risk_params = [
        {'stop_loss': 0.05, 'take_profit': 0.15, 'position_size': 0.3},
        {'stop_loss': 0.10, 'take_profit': 0.20, 'position_size': 0.5},
        {'stop_loss': 0.15, 'take_profit': 0.25, 'position_size': 0.7}
    ]

    params = []
    for rsi in rsi_params:
        for macd in macd_params:
            for bb in bb_params:
                for risk in risk_params:
                    combined = {
                        'strategy': 'Combined_RSI_MACD_BB',
                        **rsi, **macd, **bb, **risk
                    }
                    params.append(combined)

    return params

def evaluate_single_strategy(params, data, risk_free_rate=0.03):
    """評估單個策略參數"""
    try:
        # 初始化信號
        signals = pd.Series(0, index=data.index)

        # RSI信號
        if 'rsi_period' in params:
            delta = data['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=params['rsi_period'], min_periods=1).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=params['rsi_period'], min_periods=1).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))

            buy_signals = rsi < params['oversold_threshold']
            sell_signals = rsi > params['overbought_threshold']
            rsi_signal = np.where(buy_signals, 1, np.where(sell_signals, -1, 0))
            signals += rsi_signal

        # MACD信號
        if 'macd_fast' in params:
            exp1 = data['close'].ewm(span=params['macd_fast']).mean()
            exp2 = data['close'].ewm(span=params['macd_slow']).mean()
            macd = exp1 - exp2
            signal_line = macd.ewm(span=params['macd_signal']).mean()
            histogram = macd - signal_line
            macd_signal = np.where(histogram > 0, 1, -1)
            signals += macd_signal

        # 布林帶信號
        if 'bb_period' in params:
            sma = data['close'].rolling(window=params['bb_period']).mean()
            std = data['close'].rolling(window=params['bb_period']).std()
            upper_band = sma + (std * params['bb_std'])
            lower_band = sma - (std * params['bb_std'])

            buy_signals = data['close'] < lower_band
            sell_signals = data['close'] > upper_band
            bb_signal = np.where(buy_signals, 1, np.where(sell_signals, -1, 0))
            signals += bb_signal

        # 最終信號（僅使用主要信號）
        final_signals = np.where(signals > 0, 1, np.where(signals < 0, -1, 0))

        # VectorBT回測
        portfolio = vbt.Portfolio.from_signals(
            close=data['close'],
            entries=(final_signals == 1),
            exits=(final_signals == -1),
            init_cash=100000,
            fees=0.001,
            slippage=0.001
        )

        # 計算性能指標
        portfolio_value = portfolio.value()
        returns = portfolio_value.pct_change().dropna()

        total_return = (portfolio_value.iloc[-1] / portfolio_value.iloc[0]) - 1

        # Sharpe比率
        if len(returns) == 0 or returns.std() == 0:
            sharpe_ratio = 0.0
        else:
            excess_returns = returns - risk_free_rate / 252
            sharpe_ratio = np.sqrt(252) * excess_returns.mean() / returns.std()

        # 最大回撤
        rolling_max = portfolio_value.expanding().max()
        drawdown = (portfolio_value - rolling_max) / rolling_max
        max_drawdown = drawdown.min()

        # 其他指標
        calmar_ratio = total_return / abs(max_drawdown) if max_drawdown != 0 else 0

        downside_returns = returns[returns < 0]
        downside_std = downside_returns.std() if len(downside_returns) > 0 else 0.01
        sortino_ratio = (returns.mean() - risk_free_rate / 252) / downside_std * np.sqrt(252)

        win_rate = (returns > 0).sum() / len(returns) if len(returns) > 0 else 0

        return {
            'parameters': params,
            'sharpe_ratio': sharpe_ratio,
            'total_return': total_return,
            'max_drawdown': max_drawdown,
            'calmar_ratio': calmar_ratio,
            'sortino_ratio': sortino_ratio,
            'win_rate': win_rate
        }

    except Exception as e:
        logger.error(f"Error evaluating params {params}: {str(e)}")
        return {
            'parameters': params,
            'sharpe_ratio': -999.0,
            'total_return': -1.0,
            'max_drawdown': -1.0,
            'calmar_ratio': -999.0,
            'sortino_ratio': -999.0,
            'win_rate': 0.0
        }

def run_strategy_optimization(data, strategy_type, workers=32):
    """運行單個策略優化"""
    logger.info(f"開始優化 {strategy_type} 策略...")

    # 生成參數
    if strategy_type == 'RSI':
        params_list = generate_rsi_parameters()
    elif strategy_type == 'MACD':
        params_list = generate_macd_parameters()
    elif strategy_type == 'Bollinger':
        params_list = generate_bollinger_parameters()
    elif strategy_type == 'Combined':
        params_list = generate_combined_parameters()
    else:
        logger.error(f"未知策略類型: {strategy_type}")
        return None

    total_params = len(params_list)
    logger.info(f"{strategy_type} 策略參數組合數: {total_params}")

    # 分塊並行處理
    chunk_size = max(1, total_params // (workers * 4))  # 每個worker處理4個chunk
    chunks = [params_list[i:i + chunk_size] for i in range(0, len(params_list), chunk_size)]

    logger.info(f"分塊數: {len(chunks)}, 每塊大小: {chunk_size}")

    # 設置multiprocessing
    mp.set_start_method('spawn', force=True)

    # 並行執行
    start_time = datetime.now()

    with mp.Pool(processes=workers) as pool:
        evaluate_func = partial(evaluate_single_strategy, data=data)
        chunk_results = pool.map(evaluate_func, chunks)

    end_time = datetime.now()

    # 合併結果
    all_results = []
    for chunk_result in chunk_results:
        if isinstance(chunk_result, list):
            all_results.extend(chunk_result)
        else:
            all_results.append(chunk_result)

    # 找到最佳結果
    valid_results = [r for r in all_results if r['sharpe_ratio'] > -900]
    if valid_results:
        best_result = max(valid_results, key=lambda x: x['sharpe_ratio'])

        # 排序前10個結果
        sorted_results = sorted(valid_results, key=lambda x: x['sharpe_ratio'], reverse=True)
        top_10_results = sorted_results[:10]
    else:
        best_result = all_results[0]
        top_10_results = []

    execution_time = (end_time - start_time).total_seconds()

    result = {
        'strategy_type': strategy_type,
        'best_parameters': best_result['parameters'],
        'best_sharpe_ratio': best_result['sharpe_ratio'],
        'total_return': best_result['total_return'],
        'max_drawdown': best_result['max_drawdown'],
        'calmar_ratio': best_result['calmar_ratio'],
        'sortino_ratio': best_result['sortino_ratio'],
        'win_rate': best_result['win_rate'],
        'total_combinations': total_params,
        'valid_combinations': len(valid_results),
        'execution_time': execution_time,
        'top_results': top_10_results
    }

    logger.info(f"{strategy_type} 策略優化完成!")
    logger.info(f"最佳Sharpe比率: {result['best_sharpe_ratio']:.4f}")
    logger.info(f"執行時間: {execution_time:.2f}秒")
    logger.info(f"處理效率: {len(valid_results) / execution_time:.1f} 組合/秒")

    return result

def run_all_strategies_optimization(data, workers=32):
    """運行所有策略優化"""
    strategies = ['RSI', 'MACD', 'Bollinger', 'Combined']
    results = {}

    start_time = datetime.now()

    for strategy in strategies:
        result = run_strategy_optimization(data, strategy, workers)
        if result:
            results[strategy] = result

    end_time = datetime.now()
    total_time = (end_time - start_time).total_seconds()

    # 找到最佳策略
    best_strategy = max(results.keys(), key=lambda k: results[k]['best_sharpe_ratio'])
    best_result = results[best_strategy]

    summary = {
        'symbol': '0700.HK',
        'data_period': f"{data.index[0].strftime('%Y-%m-%d')} to {data.index[-1].strftime('%Y-%m-%d')}",
        'data_points': len(data),
        'workers_used': workers,
        'total_execution_time': total_time,
        'best_strategy': best_strategy,
        'best_overall_sharpe': best_result['best_sharpe_ratio'],
        'best_overall_return': best_result['total_return'],
        'strategy_results': results
    }

    return summary

def save_results(results, symbol):
    """保存優化結果"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # 保存JSON
    json_file = f"practical_strategy_optimization_{symbol}_{timestamp}.json"

    # 確保所有值都可以序列化
    def make_serializable(obj):
        if isinstance(obj, dict):
            return {k: make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [make_serializable(item) for item in obj]
        elif isinstance(obj, (np.integer, np.floating)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return obj

    serializable_results = make_serializable(results)

    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(serializable_results, f, indent=2, ensure_ascii=False, default=str)

    # 生成HTML報告
    html_file = f"practical_strategy_report_{symbol}_{timestamp}.html"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Practical Strategy Optimization Report - {symbol}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .header {{ background: linear-gradient(45deg, #3498db, #2ecc71); color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; }}
            .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 30px 0; }}
            .summary-card {{ background: #f8f9fa; padding: 20px; border-radius: 10px; text-align: center; border-left: 5px solid #3498db; }}
            .summary-value {{ font-size: 1.8em; font-weight: bold; color: #2c3e50; margin-bottom: 10px; }}
            .strategy-section {{ margin: 30px 0; padding: 20px; border: 2px solid #ddd; border-radius: 10px; }}
            .best-strategy {{ border-color: #27ae60; background-color: #f0fff4; }}
            .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin: 20px 0; }}
            .metric {{ background: #f1f3f4; padding: 15px; border-radius: 8px; text-align: center; }}
            .metric-value {{ font-size: 1.3em; font-weight: bold; color: #2c3e50; }}
            table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
            th {{ background-color: #3498db; color: white; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🎯 Practical Strategy Optimization Report</h1>
            <h2>{symbol} - 實用策略優化結果</h2>
            <p>生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>

        <div class="summary">
            <div class="summary-card">
                <div class="summary-value">{results['best_overall_sharpe']:.4f}</div>
                <div>最佳Sharpe比率</div>
            </div>
            <div class="summary-card">
                <div class="summary-value">{results['best_overall_return']:.2%}</div>
                <div>最佳總回報</div>
            </div>
            <div class="summary-card">
                <div class="summary-value">{results['total_execution_time']:.1f}s</div>
                <div>總執行時間</div>
            </div>
            <div class="summary-card">
                <div class="summary-value">{results['data_points']}</div>
                <div>數據點數</div>
            </div>
        </div>
    """

    # 各策略結果
    if 'strategy_results' in results:
        for strategy_name, strategy_result in results['strategy_results'].items():
            is_best = strategy_name == results['best_strategy']
            css_class = "best-strategy" if is_best else "strategy-section"

            html_content += f"""
            <div class="{css_class}">
                <h3>{strategy_name} 策略 {'🏆' if is_best else ''}</h3>
                <p>測試組合: {strategy_result['total_combinations']:,} | 有效組合: {strategy_result['valid_combinations']:,} | 執行時間: {strategy_result['execution_time']:.2f}s</p>

                <div class="metrics">
                    <div class="metric">
                        <div class="metric-value">{strategy_result['best_sharpe_ratio']:.4f}</div>
                        <div>Sharpe比率</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{strategy_result['total_return']:.2%}</div>
                        <div>總回報</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{strategy_result['max_drawdown']:.2%}</div>
                        <div>最大回撤</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{strategy_result['calmar_ratio']:.4f}</div>
                        <div>Calmar比率</div>
                    </div>
                </div>

                <h4>最佳參數:</h4>
                <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; font-family: monospace;">
            """

            if isinstance(strategy_result['best_parameters'], dict):
                for param, value in strategy_result['best_parameters'].items():
                    if param != 'strategy':
                        html_content += f"<strong>{param}:</strong> {value}<br>"
            else:
                html_content += f"<pre>{strategy_result['best_parameters']}</pre>"

            html_content += "</div>"

            # Top 5結果
            if 'top_results' in strategy_result and len(strategy_result['top_results']) > 1:
                html_content += """
                <h4>Top 5 結果:</h4>
                <table>
                    <tr><th>排名</th><th>Sharpe比率</th><th>總回報</th><th>最大回撤</th><th>主要參數</th></tr>
                """

                for i, top_result in enumerate(strategy_result['top_results'][:5]):
                    # 提取主要參數
                    main_params = []
                    for param, value in top_result['parameters'].items():
                        if param != 'strategy' and 'stop_loss' not in param and 'take_profit' not in param and 'position_size' not in param:
                            main_params.append(f"{param}: {value}")

                    html_content += f"""
                    <tr>
                        <td>{i+1}</td>
                        <td>{top_result['sharpe_ratio']:.4f}</td>
                        <td>{top_result['total_return']:.2%}</td>
                        <td>{top_result['max_drawdown']:.2%}</td>
                        <td>{', '.join(main_params[:3])}</td>
                    </tr>
                    """

                html_content += "</table>"

            html_content += "</div>"

    html_content += """
    </body>
    </html>
    """

    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    logger.info(f"結果已保存: {json_file}")
    logger.info(f"報告已生成: {html_file}")

    return json_file, html_file

def main():
    parser = argparse.ArgumentParser(description='Practical Strategy Optimizer - 實用策略優化器')
    parser.add_argument('--symbol', type=str, default='0700.HK', help='Stock symbol')
    parser.add_argument('--workers', type=int, default=32, help='Number of parallel workers')
    parser.add_argument('--strategy', type=str, choices=['RSI', 'MACD', 'Bollinger', 'Combined', 'all'], default='all', help='Strategy to optimize')

    args = parser.parse_args()

    logger.info("=" * 80)
    logger.info("🎯 PRACTICAL STRATEGY OPTIMIZER")
    logger.info("=" * 80)
    logger.info(f"股票代碼: {args.symbol}")
    logger.info(f"並行核心: {args.workers}")
    logger.info(f"優化策略: {args.strategy}")
    logger.info("=" * 80)

    # 獲取數據
    logger.info("正在獲取數據...")
    data = get_stock_data(args.symbol, days=1095)

    if data is None:
        logger.error("無法獲取數據，程序退出")
        return

    logger.info(f"數據範圍: {data.index[0].strftime('%Y-%m-%d')} to {data.index[-1].strftime('%Y-%m-%d')}")
    logger.info(f"數據點數: {len(data)}")

    # 運行優化
    if args.strategy == 'all':
        results = run_all_strategies_optimization(data, args.workers)
    else:
        results = run_strategy_optimization(data, args.strategy, args.workers)

    # 保存結果
    if args.strategy == 'all':
        json_file, html_file = save_results(results, args.symbol)

        logger.info("=" * 80)
        logger.info("🏆 所有策略優化完成！")
        logger.info("=" * 80)
        logger.info(f"最佳策略: {results['best_strategy']}")
        logger.info(f"最佳Sharpe比率: {results['best_overall_sharpe']:.4f}")
        logger.info(f"最佳總回報: {results['best_overall_return']:.2%}")
        logger.info(f"總執行時間: {results['total_execution_time']:.2f}秒")
    else:
        # 單策略結果
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        json_file = f"single_strategy_{args.strategy}_{args.symbol}_{timestamp}.json"

        serializable_results = {
            'strategy': args.strategy,
            'symbol': args.symbol,
            'timestamp': timestamp,
            'result': results
        }

        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(serializable_results, f, indent=2, ensure_ascii=False, default=str)

        html_file = f"single_strategy_report_{args.strategy}_{args.symbol}_{timestamp}.html"

        logger.info("=" * 80)
        logger.info(f"🎯 {args.strategy} 策略優化完成！")
        logger.info("=" * 80)
        logger.info(f"最佳Sharpe比率: {results['best_sharpe_ratio']:.4f}")
        logger.info(f"總回報率: {results['total_return']:.2%}")
        logger.info(f"最大回撤: {results['max_drawdown']:.2%}")
        logger.info(f"執行時間: {results['execution_time']:.2f}秒")
        logger.info(f"測試組合: {results['total_combinations']:,}")

    logger.info(f"📄 詳細報告: {html_file}")
    logger.info(f"💾 數據文件: {json_file}")
    logger.info("=" * 80)
    logger.info("🎉 實用策略優化成功完成！")

if __name__ == "__main__":
    main()