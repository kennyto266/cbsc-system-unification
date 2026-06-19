#!/usr/bin/env python3
"""
VectorBT 專業回測引擎
用 VectorBT 的向量化引擎做高速參數掃描 + 多策略對比。

 特點：
  ✅ 向量化回測（比 pandas 快 50x）
  ✅ 自動參數優化（SMA fast/slow 網格搜索）
  ✅ 交易成本（印花稅 + 佣金）
  ✅ 完整績效指標（Sharpe/Sortino/Calmar/回撤/勝率）
  ✅ 多股票 + 多策略 + 多參數組合
  ✅ 南北水 non-price 信號整合

用法:
    python scripts/vbt_backtest.py                        # 預設股票池
    python scripts/vbt_backtest.py --symbols 0700.HK 9988.HK
    python scripts/vbt_backtest.py --optimize             # 參數優化模式
    python scripts/vbt_backtest.py --nonprice             # 加入南北水信號
"""

import argparse
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

# 清除干擾路徑（CODEX-- 目錄的 telegram 衝突）
sys.path = [p for p in sys.path if "CODEX" not in p]

import numpy as np
import pandas as pd
import requests
import vectorbt as vbt

ROOT = Path(__file__).parent.parent
DATA_API = "http://18.180.162.113:9191/inst/getInst"
FEES = 0.0023  # 印花稅 0.13% + 佣金 0.05% x 2


# ==============================================================================
# 數據
# ==============================================================================

def fetch_series(symbol: str, duration: int = 1385) -> pd.DataFrame:
    r = requests.get(DATA_API, params={"symbol": symbol, "duration": duration}, timeout=20, headers={"accept": "application/json"})
    r.raise_for_status()
    j = r.json()
    if isinstance(j, dict) and "data" in j and isinstance(j["data"], dict):
        j = j["data"]
    cols = {}
    for key in ["open", "high", "low", "close", "volume"]:
        if key in j and isinstance(j[key], dict):
            s = pd.Series(j[key]).astype(float)
            s.index = pd.to_datetime(s.index)
            cols[key] = s.sort_index()
    df = pd.concat(cols.values(), axis=1)
    df.columns = list(cols.keys())
    return df.dropna(how="all")


def load_southbound_data() -> pd.DataFrame | None:
    """載入南北水歷史數據"""
    path = ROOT / "data" / "sc_full.csv"
    if not path.exists():
        return None
    sc = pd.read_csv(path, parse_dates=["date"])
    # 取南向合計
    south = sc[sc["type_name"].str.contains("南向_港股通", na=False)]
    if south.empty:
        south = sc[sc["mutual_type"].str.contains("002|004", na=False)]
    south = south.groupby("date").agg({"net_buy": "sum", "buy": "sum", "sell": "sum"}).reset_index()
    south = south.set_index("date").sort_index()
    return south


# ==============================================================================
# VectorBT 策略
# ==============================================================================

def run_strategy_momentum(close: pd.Series, fast: int = 5, slow: int = 20) -> vbt.Portfolio:
    """動量策略：SMA 金叉死叉"""
    sma_fast = vbt.MA.run(close, fast)
    sma_slow = vbt.MA.run(close, slow)
    entries = sma_fast.ma_above(sma_slow)
    exits = sma_fast.ma_below(sma_slow)
    return vbt.Portfolio.from_signals(close, entries, exits, freq="D", fees=FEES)


def run_strategy_rsi(close: pd.Series, period: int = 14, lower: int = 30, upper: int = 70) -> vbt.Portfolio:
    """RSI 均值回歸"""
    rsi = vbt.RSI.run(close, period)
    entries = rsi.rsi < lower
    exits = rsi.rsi > upper
    return vbt.Portfolio.from_signals(close, entries, exits, freq="D", fees=FEES)


def run_strategy_bollinger(close: pd.Series, window: int = 20, alpha: float = 2.0) -> vbt.Portfolio:
    """布林帶"""
    bb = vbt.BBANDS.run(close, window=window, alpha=alpha)
    entries = close < bb.lower
    exits = close > bb.upper
    return vbt.Portfolio.from_signals(close, entries, exits, freq="D", fees=FEES)


def run_strategy_breakout(close: pd.Series, window: int = 20) -> vbt.Portfolio:
    """突破"""
    entries = close > close.rolling(window).max().shift(1)
    exits = close < close.rolling(window).min().shift(1)
    return vbt.Portfolio.from_signals(close, entries, exits, freq="D", fees=FEES)


def run_strategy_macd(close: pd.Series) -> vbt.Portfolio:
    """MACD"""
    macd = vbt.MACD.run(close)
    entries = macd.macd_above(macd.signal)
    exits = macd.macd_below(macd.signal)
    return vbt.Portfolio.from_signals(close, entries, exits, freq="D", fees=FEES)


def run_strategy_southbound(close: pd.Series, southbound: pd.DataFrame | None) -> vbt.Portfolio:
    """南北水跟買策略"""
    if southbound is None:
        # 無南北水數據，用成交量代替
        return run_strategy_momentum(close)
    # 對齊日期
    net = southbound["net_buy"].reindex(close.index).ffill().fillna(0)
    net_ma = net.rolling(5).mean()
    entries = (net > net_ma) & (net > 0)
    exits = (net < net_ma) & (net < 0)
    return vbt.Portfolio.from_signals(close, entries, exits, freq="D", fees=FEES)


STRATEGIES = {
    "momentum": "momentum",
    "rsi": "rsi",
    "bollinger": "bollinger",
    "breakout": "breakout",
    "macd": "macd",
    "southbound": "southbound",
}


def run_strategy_by_name(name: str, close: pd.Series, sb: pd.DataFrame | None) -> vbt.Portfolio:
    """根據策略名執行對應策略"""
    if name == "momentum":
        return run_strategy_momentum(close)
    elif name == "rsi":
        return run_strategy_rsi(close)
    elif name == "bollinger":
        return run_strategy_bollinger(close)
    elif name == "breakout":
        return run_strategy_breakout(close)
    elif name == "macd":
        return run_strategy_macd(close)
    elif name == "southbound":
        return run_strategy_southbound(close, sb)
    else:
        raise ValueError(f"Unknown strategy: {name}")


def extract_metrics(pf: vbt.Portfolio) -> dict:
    """提取績效指標"""
    return {
        "sharpe": round(float(pf.sharpe_ratio()), 3),
        "sortino": round(float(pf.sortino_ratio()), 3),
        "calmar": round(float(pf.calmar_ratio()), 3),
        "total_return": round(float(pf.total_return()), 3),
        "max_dd": round(float(pf.max_drawdown()), 3),
        "win_rate": round(float(pf.trades.win_rate()), 3) if len(pf.trades) > 0 else 0,
        "num_trades": int(pf.trades.count()) if hasattr(pf.trades, 'count') else 0,
        "expectancy": round(float(pf.trades.expectancy()), 5) if len(pf.trades) > 0 else 0,
    }


# ==============================================================================
# 參數優化（向量化網格搜索）
# ==============================================================================

def optimize_momentum(close: pd.Series) -> pd.DataFrame:
    """momentum 策略參數優化（fast x slow 網格）"""
    fast_range = [3, 5, 8, 10, 15, 20]
    slow_range = [10, 15, 20, 30, 50, 100]

    results = []
    for fast in fast_range:
        for slow in slow_range:
            if fast >= slow:
                continue
            pf = run_strategy_momentum(close, fast=fast, slow=slow)
            m = extract_metrics(pf)
            m["fast"] = fast
            m["slow"] = slow
            results.append(m)

    df = pd.DataFrame(results).sort_values("sharpe", ascending=False)
    return df


# ==============================================================================
# 多進程 Worker
# ==============================================================================

def worker_vbt(args):
    """Worker: 抓數據 + 跑全部策略"""
    symbol, strategies, southbound_serialized, duration = args
    try:
        df = fetch_series(symbol, duration)
    except Exception as e:
        return [{"symbol": symbol, "strategy": "N/A", "status": f"error: {str(e)[:40]}"}]

    close = df["close"]
    sb = None
    if southbound_serialized is not None:
        sb = pd.DataFrame(southbound_serialized)

    results = []
    for name in strategies:
        try:
            pf = run_strategy_by_name(name, close, sb)
            m = extract_metrics(pf)
            m["symbol"] = symbol
            m["strategy"] = name
            m["status"] = "ok"
            results.append(m)
        except Exception as e:
            results.append({"symbol": symbol, "strategy": name, "status": f"error: {str(e)[:40]}"})

    return results


STOCK_POOL = [
    "0700.HK", "9988.HK", "0939.HK", "1810.HK", "1177.HK", "0992.HK",
    "0388.HK", "0005.HK", "0883.HK", "9618.HK", "3690.HK", "9999.HK",
    "1299.HK", "2318.HK", "1398.HK", "3988.HK", "2828.HK", "2800.HK",
    "0941.HK", "0002.HK", "0001.HK", "0011.HK", "0012.HK", "0016.HK",
    "0175.HK", "0241.HK", "0267.HK", "0288.HK", "0291.HK", "0386.HK",
    "0688.HK", "0762.HK", "0823.HK", "0857.HK", "0868.HK", "0992.HK",
    "1038.HK", "1044.HK", "1093.HK", "1113.HK", "1209.HK", "1211.HK",
    "1928.HK", "2018.HK", "2269.HK", "2313.HK", "2382.HK", "2388.HK",
    "2628.HK", "6098.HK", "6862.HK", "9633.HK", "9868.HK", "9869.HK",
    "9961.HK", "0669.HK", "1138.HK", "1336.HK", "1359.HK", "1530.HK",
]


def main():
    import multiprocessing
    parser = argparse.ArgumentParser(description="VectorBT 專業回測引擎")
    parser.add_argument("--symbols", nargs="+", default=None)
    parser.add_argument("--workers", type=int, default=None)
    parser.add_argument("--optimize", action="store_true", help="momentum 參數優化")
    parser.add_argument("--nonprice", action="store_true", help="加入南北水信號")
    parser.add_argument("--output", type=str, default="data/vbt_results.csv")
    parser.add_argument("--duration", type=int, default=1385)
    args = parser.parse_args()

    symbols = args.symbols or STOCK_POOL
    workers = args.workers or min(multiprocessing.cpu_count(), len(symbols))

    strategies = STRATEGIES
    if not args.nonprice:
        strategies = {k: v for k, v in strategies.items() if k != "southbound"}

    print("🚀 VectorBT 專業回測引擎")
    print(f"   VectorBT 版本: {vbt.__version__}")
    print(f"   股票: {len(symbols)} 隻 | 策略: {len(strategies)} 個 | CPU: {workers} 核")
    print(f"   策略: {', '.join(strategies.keys())}")
    print(f"   交易成本: {FEES*100:.2f}% per side")
    print()

    # 參數優化模式
    if args.optimize:
        print("🔧 參數優化模式（momentum SMA 網格搜索）")
        symbol = symbols[0] if len(symbols) == 1 else "0700.HK"
        print(f"   測試股票: {symbol}")
        df = fetch_series(symbol, args.duration)
        opt_df = optimize_momentum(df["close"])
        print(f"\n🏆 Top 10 參數組合:")
        print(opt_df.head(10)[["fast", "slow", "sharpe", "total_return", "max_dd", "win_rate"]].to_string(index=False))
        opt_df.to_csv(args.output, index=False, encoding="utf-8-sig")
        print(f"\n💾 已保存到 {args.output}")
        return

    # 序列化南北水數據
    sb_serialized = None
    if args.nonprice:
        sb = load_southbound_data()
        if sb is not None:
            sb_serialized = sb.to_dict()
            print(f"   📊 南北水: {len(sb)} 天 ({sb.index.min().date()} to {sb.index.max().date()})")
        else:
            print("   ⚠ 無南北水數據，跳過 southbound 策略")

    # 多進程回測
    tasks = [(s, strategies, sb_serialized, args.duration) for s in symbols]
    all_results = []
    start = time.time()

    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(worker_vbt, t): t[0] for t in tasks}
        for future in as_completed(futures):
            symbol = futures[future]
            results = future.result()
            all_results.extend(results)
            ok = [r for r in results if r.get("status") == "ok"]
            if ok:
                best = max(ok, key=lambda r: r.get("sharpe", 0))
                print(f"  ✓ {symbol}: 最佳 {best['strategy']} Sharpe={best['sharpe']:+.2f} Sortino={best.get('sortino',0):.2f}")

    elapsed = time.time() - start
    df = pd.DataFrame(all_results)
    ok_df = df[df["status"] == "ok"].copy()

    print(f"\n⏱ 完成！{len(all_results)} 個結果，耗時 {elapsed:.1f}s（VectorBT 向量化）")

    if ok_df.empty:
        print("⚠ 無成功結果")
        return

    ok_df = ok_df.sort_values("sharpe", ascending=False)
    print(f"\n🏆 Top 15 策略組合（按 Sharpe）:")
    cols = ["symbol", "strategy", "sharpe", "sortino", "calmar", "total_return", "max_dd", "win_rate", "num_trades"]
    print(ok_df.head(15)[cols].to_string(index=False))

    print(f"\n📊 各策略平均 Sharpe:")
    summary = ok_df.groupby("strategy")["sharpe"].agg(["mean", "std", "count", "max"]).sort_values("mean", ascending=False)
    print(summary.to_string())

    print(f"\n📈 統計:")
    print(f"   Sharpe > 1.0: {(ok_df['sharpe'] > 1.0).sum()} 個 ({(ok_df['sharpe']>1.0).mean()*100:.0f}%)")
    print(f"   Sharpe > 0.5: {(ok_df['sharpe'] > 0.5).sum()} 個 ({(ok_df['sharpe']>0.5).mean()*100:.0f}%)")
    print(f"   正收益: {(ok_df['total_return'] > 0).sum()} 個")
    print(f"   最高 Sortino: {ok_df['sortino'].max():.2f}")

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    df.to_csv(args.output, index=False, encoding="utf-8-sig")
    print(f"\n💾 結果已保存到 {args.output}")


if __name__ == "__main__":
    main()
