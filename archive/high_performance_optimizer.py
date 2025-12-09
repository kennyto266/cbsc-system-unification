#!/usr/bin/env python3
"""
High Performance VectorBT Optimizer - 真正的32核心並行優化器
使用multiprocessing和chunking策略實現高效並行

Usage: python high_performance_optimizer.py --symbol 0700.HK --workers 32
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
from itertools import product
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

def calculate_rsi_signals(data, period, overbought, oversold):
    """計算RSI信號"""
    delta = data['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period, min_periods=1).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period, min_periods=1).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    buy_signals = rsi < oversold
    sell_signals = rsi > overbought
    return np.where(buy_signals, 1, np.where(sell_signals, -1, 0))

def calculate_macd_signals(data, fast, slow, signal):
    """計算MACD信號"""
    exp1 = data['close'].ewm(span=fast).mean()
    exp2 = data['close'].ewm(span=slow).mean()
    macd = exp1 - exp2
    signal_line = macd.ewm(span=signal).mean()
    histogram = macd - signal_line
    return np.where(histogram > 0, 1, -1)

def calculate_bb_signals(data, period, std_dev):
    """計算布林帶信號"""
    sma = data['close'].rolling(window=period).mean()
    std = data['close'].rolling(window=period).std()
    upper_band = sma + (std * std_dev)
    lower_band = sma - (std * std_dev)

    buy_signals = data['close'] < lower_band
    sell_signals = data['close'] > upper_band
    return np.where(buy_signals, 1, np.where(sell_signals, -1, 0))

def evaluate_parameters(params_chunk, data, risk_free_rate=0.03):
    """評估參數塊 - 為並行處理設計"""
    results = []

    for params in params_chunk:
        try:
            # 生成交易信號
            signals = pd.Series(0, index=data.index)

            # RSI信號
            if params.get('rsi_period', 0) > 0:
                rsi_signal = calculate_rsi_signals(
                    data, params['rsi_period'],
                    params['overbought_threshold'], params['oversold_threshold']
                )
                signals += rsi_signal

            # MACD信號
            if params.get('macd_fast', 0) > 0 and params.get('macd_slow', 0) > 0:
                macd_signal = calculate_macd_signals(
                    data, params['macd_fast'], params['macd_slow'], params['macd_signal']
                )
                signals += macd_signal

            # 布林帶信號
            if params.get('bb_period', 0) > 0:
                bb_signal = calculate_bb_signals(
                    data, params['bb_period'], params['bb_std']
                )
                signals += bb_signal

            # 最終信號
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

            # Sharpe比率計算
            if len(returns) == 0 or returns.std() == 0:
                sharpe_ratio = 0.0
            else:
                excess_returns = returns - risk_free_rate / 252
                sharpe_ratio = np.sqrt(252) * excess_returns.mean() / returns.std()

            # 最大回撤
            rolling_max = portfolio_value.expanding().max()
            drawdown = (portfolio_value - rolling_max) / rolling_max
            max_drawdown = drawdown.min()

            # Calmar比率
            calmar_ratio = total_return / abs(max_drawdown) if max_drawdown != 0 else 0

            # Sortino比率
            downside_returns = returns[returns < 0]
            downside_std = downside_returns.std() if len(downside_returns) > 0 else 0.01
            sortino_ratio = (returns.mean() - risk_free_rate / 252) / downside_std * np.sqrt(252)

            # 勝率
            win_rate = (returns > 0).sum() / len(returns) if len(returns) > 0 else 0

            results.append({
                'parameters': params,
                'sharpe_ratio': sharpe_ratio,
                'total_return': total_return,
                'max_drawdown': max_drawdown,
                'calmar_ratio': calmar_ratio,
                'sortino_ratio': sortino_ratio,
                'win_rate': win_rate
            })

        except Exception as e:
            logger.error(f"Error evaluating params {params}: {str(e)}")
            results.append({
                'parameters': params,
                'sharpe_ratio': -999.0,
                'total_return': -1.0,
                'max_drawdown': -1.0,
                'calmar_ratio': -999.0,
                'sortino_ratio': -999.0,
                'win_rate': 0.0
            })

    return results

def generate_parameter_combinations():
    """生成合理的參數組合 - 平衡規模和質量"""

    # RSI參數
    rsi_periods = [5, 10, 14, 20, 25, 30]
    overbought_thresholds = [65, 70, 75, 80, 85]
    oversold_thresholds = [15, 20, 25, 30, 35]

    # 風險管理參數
    stop_losses = [0.05, 0.10, 0.15, 0.20]
    take_profits = [0.15, 0.20, 0.25, 0.30, 0.35]
    position_sizes = [0.1, 0.2, 0.3, 0.5, 1.0]

    # MACD參數
    macd_fasts = [12, 13, 14, 15]
    macd_slows = [26, 27, 28, 29]
    macd_signals = [9, 10, 11, 12]

    # 布林帶參數
    bb_periods = [10, 15, 20, 25]
    bb_stds = [1.5, 2.0, 2.5]

    combinations = []

    for rsi_period, ob, os in product(rsi_periods, overbought_thresholds, oversold_thresholds):
        # 過濾不合理組合
        if ob <= os:
            continue

        for sl, tp, pos in product(stop_losses, take_profits, position_sizes):
            for mf, ms, msig in product(macd_fasts, macd_slows, macd_signals):
                # 過濾不合理MACD組合
                if mf >= ms:
                    continue

                for bbp, bbs in product(bb_periods, bb_stds):
                    combinations.append({
                        'rsi_period': rsi_period,
                        'overbought_threshold': ob,
                        'oversold_threshold': os,
                        'stop_loss': sl,
                        'take_profit': tp,
                        'position_size': pos,
                        'macd_fast': mf,
                        'macd_slow': ms,
                        'macd_signal': msig,
                        'bb_period': bbp,
                        'bb_std': bbs
                    })

    return combinations

def run_parallel_optimization(data, workers=32, chunk_size=1000):
    """運行並行優化"""

    # 生成參數組合
    logger.info("生成參數組合...")
    combinations = generate_parameter_combinations()
    total_combinations = len(combinations)

    logger.info(f"總組合數: {total_combinations:,}")

    # 分塊處理
    chunks = [combinations[i:i + chunk_size] for i in range(0, len(combinations), chunk_size)]

    logger.info(f"分塊數: {len(chunks)}, 每塊大小: {chunk_size}")
    logger.info(f"使用 {workers} 個核心進行並行處理...")

    # 設置multiprocessing
    mp.set_start_method('spawn', force=True)

    # 創建部分函數
    evaluate_func = partial(evaluate_parameters, data=data)

    # 並行執行
    start_time = datetime.now()

    with mp.Pool(processes=workers) as pool:
        results = pool.map(evaluate_func, chunks)

    end_time = datetime.now()

    # 合併結果
    all_results = []
    for chunk_result in results:
        all_results.extend(chunk_result)

    # 找到最佳結果
    best_result = max(all_results, key=lambda x: x['sharpe_ratio'])

    # 排序前10個結果
    sorted_results = sorted(all_results, key=lambda x: x['sharpe_ratio'], reverse=True)
    top_10_results = [r for r in sorted_results[:10] if r['sharpe_ratio'] > -900]

    execution_time = (end_time - start_time).total_seconds()

    return {
        'best_parameters': best_result['parameters'],
        'best_sharpe_ratio': best_result['sharpe_ratio'],
        'total_return': best_result['total_return'],
        'max_drawdown': best_result['max_drawdown'],
        'calmar_ratio': best_result['calmar_ratio'],
        'sortino_ratio': best_result['sortino_ratio'],
        'win_rate': best_result['win_rate'],
        'optimization_id': f"parallel_opt_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        'method': 'parallel_grid_search',
        'total_combinations': total_combinations,
        'executed_combinations': len(all_results),
        'execution_time': execution_time,
        'top_results': top_10_results
    }

def save_results(result, symbol, workers):
    """保存優化結果"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # 保存JSON
    json_file = f"parallel_optimization_{symbol}_{timestamp}.json"

    # 確保所有值都可以序列化
    serializable_result = result.copy()
    if 'top_results' in serializable_result:
        for i, top_result in enumerate(serializable_result['top_results']):
            if isinstance(top_result, dict):
                # 轉換numpy類型為Python原生類型
                for key, value in top_result.items():
                    if isinstance(value, (np.integer, np.floating)):
                        top_result[key] = float(value)
                    elif isinstance(value, np.ndarray):
                        top_result[key] = value.tolist()

    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(serializable_result, f, indent=2, ensure_ascii=False, default=str)

    # 生成HTML報告
    html_file = f"parallel_optimization_report_{symbol}_{timestamp}.html"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>High Performance Parallel Optimization - {symbol}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .header {{ background: linear-gradient(45deg, #e74c3c, #f39c12); color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; }}
            .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 30px 0; }}
            .stat-card {{ background: #f8f9fa; padding: 20px; border-radius: 10px; text-align: center; border-left: 5px solid #e74c3c; }}
            .stat-value {{ font-size: 2em; font-weight: bold; color: #2c3e50; margin-bottom: 10px; }}
            .parameters {{ background: #f1f3f4; padding: 20px; border-radius: 10px; font-family: monospace; margin: 20px 0; }}
            table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
            th {{ background-color: #e74c3c; color: white; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🚀 High Performance Parallel Optimization</h1>
            <h2>{symbol} - 32核心並行處理結果</h2>
            <p>生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>並行核心: {workers} 核心處理</p>
        </div>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">{result['best_sharpe_ratio']:.4f}</div>
                <div>最佳Sharpe比率</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{result['total_return']:.2%}</div>
                <div>總回報率</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{result['max_drawdown']:.2%}</div>
                <div>最大回撤</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{result['calmar_ratio']:.4f}</div>
                <div>Calmar比率</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{result['execution_time']:.2f}s</div>
                <div>執行時間</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{result['total_combinations']:,}</div>
                <div>總組合數</div>
            </div>
        </div>

        <h3>🏆 最佳參數配置:</h3>
        <div class="parameters">
    """

    for param, value in result['best_parameters'].items():
        html_content += f"<strong>{param}:</strong> {value}<br>"

    html_content += "</div>"

    if 'top_results' in result and len(result['top_results']) > 1:
        html_content += """
        <h3>📊 Top 5 結果:</h3>
        <table>
            <tr><th>排名</th><th>Sharpe比率</th><th>總回報</th><th>最大回撤</th><th>Calmar比率</th></tr>
        """

        for i, top_result in enumerate(result['top_results'][:5]):
            html_content += f"""
            <tr>
                <td>{i+1}</td>
                <td>{top_result['sharpe_ratio']:.4f}</td>
                <td>{top_result['total_return']:.2%}</td>
                <td>{top_result['max_drawdown']:.2%}</td>
                <td>{top_result['calmar_ratio']:.4f}</td>
            </tr>
            """

        html_content += "</table>"

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
    parser = argparse.ArgumentParser(description='High Performance Parallel VectorBT Optimizer')
    parser.add_argument('--symbol', type=str, default='0700.HK', help='Stock symbol')
    parser.add_argument('--workers', type=int, default=32, help='Number of parallel workers')
    parser.add_argument('--chunk-size', type=int, default=1000, help='Chunk size for parallel processing')

    args = parser.parse_args()

    logger.info("=" * 80)
    logger.info("🚀 HIGH PERFORMANCE PARALLEL VECTORBT OPTIMIZER")
    logger.info("=" * 80)
    logger.info(f"股票代碼: {args.symbol}")
    logger.info(f"並行核心: {args.workers}")
    logger.info(f"塊大小: {args.chunk_size}")
    logger.info("=" * 80)

    # 獲取數據
    logger.info("正在獲取數據...")
    data = get_stock_data(args.symbol, days=1095)

    if data is None:
        logger.error("無法獲取數據，程序退出")
        return

    logger.info(f"數據範圍: {data.index[0].strftime('%Y-%m-%d')} to {data.index[-1].strftime('%Y-%m-%d')}")
    logger.info(f"數據點數: {len(data)}")

    # 運行並行優化
    result = run_parallel_optimization(data, args.workers, args.chunk_size)

    # 保存結果
    json_file, html_file = save_results(result, args.symbol, args.workers)

    # 顯示結果
    logger.info("=" * 80)
    logger.info("🏆 並行優化完成！")
    logger.info("=" * 80)
    logger.info(f"最佳Sharpe比率: {result['best_sharpe_ratio']:.4f}")
    logger.info(f"總回報率: {result['total_return']:.2%}")
    logger.info(f"最大回撤: {result['max_drawdown']:.2%}")
    logger.info(f"Calmar比率: {result['calmar_ratio']:.4f}")
    logger.info(f"執行時間: {result['execution_time']:.2f}秒")
    logger.info(f"處理效率: {result['executed_combinations'] / result['execution_time']:.1f} 組合/秒")
    logger.info(f"📄 詳細報告: {html_file}")
    logger.info(f"💾 數據文件: {json_file}")
    logger.info("=" * 80)
    logger.info("🎉 高性能並行優化成功完成！")

if __name__ == "__main__":
    main()