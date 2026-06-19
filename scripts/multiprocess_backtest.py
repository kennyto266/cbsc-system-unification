#!/usr/bin/env python3
"""
多 CPU 港股回測系統
基於 backtest_research_strategy_0939.py，用 multiprocessing 同時回測多隻股票。

 功能：
  1. 多股票並行回測（32 核同時跑）
  2. 參數網格搜索（fast/slow/rsi 組合）
  3. 結果排序 + CSV 輸出

用法:
    python scripts/multiprocess_backtest.py                           # 預設股票池
    python scripts/multiprocess_backtest.py --symbols 0939.HK 0700.HK 9988.HK
    python scripts/multiprocess_backtest.py --workers 16               # 指定 CPU 數
    python scripts/multiprocess_backtest.py --grid                     # 參數網格搜索
    python scripts/multiprocess_backtest.py --output data/backtest_results.csv
"""

import argparse
import itertools
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import requests

# ==============================================================================
# 數據獲取
# ==============================================================================

DATA_API = "http://18.180.162.113:9191/inst/getInst"


def fetch_series(symbol: str, duration: int = 1385) -> pd.DataFrame:
    """從數據 API 獲取股票 OHLCV 時間序列"""
    r = requests.get(
        DATA_API,
        params={"symbol": symbol, "duration": duration},
        timeout=20,
        headers={"accept": "application/json"},
    )
    r.raise_for_status()
    j = r.json()
    if isinstance(j, dict) and "data" in j and isinstance(j["data"], dict):
        j = j["data"]

    def to_series(d):
        if not isinstance(d, dict):
            return pd.Series(dtype=float)
        s = pd.Series(d)
        s.index = pd.to_datetime(s.index)
        return s.sort_index().astype(float)

    cols = {}
    for key in ["open", "high", "low", "close", "volume"]:
        if key in j and isinstance(j[key], dict):
            cols[key] = to_series(j[key])
        elif key.capitalize() in j and isinstance(j[key.capitalize()], dict):
            cols[key] = to_series(j[key.capitalize()])

    if not cols:
        raise ValueError(f"{symbol}: API 返回不含時間序列")

    df = pd.concat(cols.values(), axis=1)
    df.columns = list(cols.keys())
    df = df.dropna(how="all")
    if "volume" in df.columns:
        df["volume"] = df["volume"].fillna(0).round()
    return df


# ==============================================================================
# 策略 + 回測核心
# ==============================================================================


def compute_indicators(df: pd.DataFrame, fast: int = 5, slow: int = 14, rsi_n: int = 14) -> pd.DataFrame:
    out = df.copy()
    out["sma_fast"] = out["close"].rolling(fast).mean()
    out["sma_slow"] = out["close"].rolling(slow).mean()
    delta = out["close"].diff()
    gain = delta.where(delta > 0, 0.0).rolling(rsi_n).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(rsi_n).mean()
    rs = gain / loss.replace(0, np.nan)
    out["rsi"] = 100 - (100 / (1 + rs))
    return out


def derive_decision(row_prev: pd.Series, hist: pd.DataFrame, idx: int) -> int:
    """多因子投票決策（技術 + 動量 + 基本面 proxy）"""
    tech_dir = 0
    if not np.isnan(row_prev.get("sma_fast", np.nan)) and not np.isnan(
        row_prev.get("sma_slow", np.nan)
    ) and not np.isnan(row_prev.get("rsi", np.nan)):
        if row_prev["sma_fast"] > row_prev["sma_slow"] and row_prev["rsi"] > 50:
            tech_dir = 1
        elif row_prev["sma_fast"] < row_prev["sma_slow"] and row_prev["rsi"] < 50:
            tech_dir = -1

    sent_dir = 0
    if idx >= 20:
        p = hist["close"].iloc[idx - 20 : idx + 1]
        mom5 = p.iloc[-1] / p.iloc[-6] - 1 if len(p) >= 6 else 0.0
        mom20 = p.iloc[-1] / p.iloc[0] - 1 if len(p) >= 1 else 0.0
        sent_dir = 1 if mom5 > mom20 * 1.05 else -1 if mom5 < mom20 * 0.95 else 0

    fund_dir = 0
    if idx >= 60:
        p60 = hist["close"].iloc[idx - 60 : idx + 1]
        long_mom = p60.iloc[-1] / p60.iloc[0] - 1
        fund_dir = 1 if long_mom > 0 else -1 if long_mom < 0 else 0

    votes = tech_dir + sent_dir + fund_dir
    return 1 if votes > 0 else -1 if votes < 0 else 0


def backtest(df: pd.DataFrame, fast=5, slow=14, rsi_n=14) -> dict:
    """單次回測，返回績效指標"""
    ind = compute_indicators(df, fast, slow, rsi_n).dropna().copy()
    if len(ind) < 60:
        return {"sharpe": 0, "max_dd": 0, "trades": 0, "win_rate": 0, "points": len(ind), "return": 0}

    dirs = [0] + [derive_decision(ind.iloc[i - 1], ind, i - 1) for i in range(1, len(ind))]
    pos = pd.Series(dirs, index=ind.index)

    ret = ind["close"].pct_change().fillna(0)
    strat_ret = ret * pos.shift(1).fillna(0)

    cum = (1 + strat_ret).cumprod()
    total_return = float(cum.iloc[-1] - 1) if len(cum) else 0.0
    max_dd = float((cum / cum.cummax() - 1).min()) if len(cum) else 0.0
    mean = strat_ret.mean() * 252
    std = strat_ret.std(ddof=0) * np.sqrt(252)
    sharpe = float(mean / std) if std and std > 0 else 0.0
    trades = int((pos.diff().abs() == 2).sum() + (pos.diff() == 1).sum() + (pos.diff() == -1).sum())
    nonzero = strat_ret[strat_ret != 0]
    win_rate = float((nonzero[nonzero > 0].count()) / max(1, len(nonzero)))

    return {
        "sharpe": round(sharpe, 3),
        "max_dd": round(max_dd, 3),
        "trades": trades,
        "win_rate": round(win_rate, 3),
        "points": len(ind),
        "return": round(total_return, 3),
    }


# ==============================================================================
# 多進程 Worker
# ==============================================================================


def worker_backtest_symbol(args):
    """Worker: 抓取數據 + 回測單隻股票"""
    symbol, duration = args
    try:
        df = fetch_series(symbol, duration)
        result = backtest(df)
        result["symbol"] = symbol
        result["status"] = "ok"
        return result
    except Exception as e:
        return {"symbol": symbol, "status": f"error: {str(e)[:60]}", "sharpe": 0}


def worker_backtest_params(args):
    """Worker: 用已加載數據 + 指定參數回測"""
    symbol, df_dict, fast, slow, rsi_n = args
    try:
        df = df_dict.get(symbol)
        if df is None or df.empty:
            return {"symbol": symbol, "fast": fast, "slow": slow, "rsi": rsi_n, "status": "no data"}
        result = backtest(df, fast, slow, rsi_n)
        result.update({"symbol": symbol, "fast": fast, "slow": slow, "rsi": rsi_n, "status": "ok"})
        return result
    except Exception as e:
        return {"symbol": symbol, "fast": fast, "slow": slow, "rsi": rsi_n, "status": f"error: {str(e)[:40]}"}


# ==============================================================================
# 主控
# ==============================================================================

# 預設港股池（藍籌 + 熱門）
DEFAULT_SYMBOLS = [
    "0700.HK",  # 騰訊
    "0939.HK",  # 建設銀行
    "9988.HK",  # 阿里巴巴
    "1299.HK",  # 友邦保險
    "0005.HK",  # 匯豐
    "0388.HK",  # 港交所
    "0941.HK",  # 中國移動
    "0883.HK",  # 中海油
    "1398.HK",  # 工商銀行
    "3988.HK",  # 中國銀行
    "2318.HK",  # 平安
    "9618.HK",  # 京東
    "3690.HK",  # 美團
    "1810.HK",  # 小米
    "9999.HK",  # 網易
    "1024.HK",  # 快手
]


def run_multiprocess_backtest(
    symbols: list[str], workers: int = None, duration: int = 1385
) -> pd.DataFrame:
    """多進程回測多隻股票"""
    import multiprocessing

    if workers is None:
        workers = min(multiprocessing.cpu_count(), len(symbols))

    print(f"🚀 多 CPU 回測：{len(symbols)} 隻股票，{workers} 核並行")
    print(f"   股票: {', '.join(symbols[:5])}{'...' if len(symbols) > 5 else ''}")

    tasks = [(s, duration) for s in symbols]
    results = []
    start = time.time()

    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(worker_backtest_symbol, t): t[0] for t in tasks}
        for future in as_completed(futures):
            symbol = futures[future]
            result = future.result()
            status = result.get("status", "?")
            sharpe = result.get("sharpe", 0)
            ret = result.get("return", 0)
            icon = "✓" if status == "ok" else "✗"
            print(f"  {icon} {symbol}: Sharpe={sharpe:+.2f}, Return={ret:+.1%}, {status}")
            results.append(result)

    elapsed = time.time() - start
    print(f"\n⏱ 完成！{len(results)} 隻股票，耗時 {elapsed:.1f}s（{workers} 核）")
    if len(results) > 1:
        print(f"   平均每隻: {elapsed/len(results):.2f}s")

    return pd.DataFrame(results)


def run_param_grid(
    symbols: list[str],
    fast_range=[3, 5, 8, 10],
    slow_range=[14, 20, 26, 50],
    rsi_range=[7, 14, 21],
    workers: int = None,
) -> pd.DataFrame:
    """參數網格搜索（先用單核抓數據，再多核跑參數）"""
    import multiprocessing

    if workers is None:
        workers = multiprocessing.cpu_count()

    # Step 1: 抓取所有股票數據（單核，因為 API 限流）
    print(f"📥 抓取 {len(symbols)} 隻股票數據...")
    data = {}
    for s in symbols:
        try:
            data[s] = fetch_series(s)
            print(f"  ✓ {s}: {len(data[s])} bars")
        except Exception as e:
            print(f"  ✗ {s}: {e}")

    # Step 2: 構建參數組合
    combos = list(itertools.product(symbols, fast_range, slow_range, rsi_range))
    print(f"\n🔧 參數網格：{len(combos)} 個組合，{workers} 核並行")

    # Step 3: 多進程回測
    # 注意：DataFrame 不能直接傳給子進程，轉成 dict
    # 用 worker 函數內部重新構建
    results = []
    start = time.time()

    # 為了傳遞數據到子進程，我們把 DataFrame 存為全局（fork 時複製）
    # Windows 沒有 fork，用 pickle 傳遞——用 Pool 的 initializer
    manager_dict = {}

    def init_worker(d):
        manager_dict.update(d)

    # 將 DataFrame 序列化為 dict
    serializable = {k: v.to_dict() for k, v in data.items()}

    def grid_worker(args):
        symbol, fast, slow, rsi, sdata = args
        if symbol not in sdata:
            return {"symbol": symbol, "fast": fast, "slow": slow, "rsi": rsi, "status": "no data"}
        df = pd.DataFrame(sdata[symbol])
        df.index = pd.to_datetime(df.index)
        try:
            result = backtest(df, fast, slow, rsi)
            result.update({"symbol": symbol, "fast": fast, "slow": slow, "rsi": rsi, "status": "ok"})
            return result
        except Exception as e:
            return {"symbol": symbol, "fast": fast, "slow": slow, "rsi": rsi, "status": str(e)[:40]}

    # 傳遞序列化數據給每個 task（簡單但有效）
    tasks = [(s, f, sl, r, serializable) for s, f, sl, r in combos]

    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(grid_worker, t): t for t in tasks}
        done = 0
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            done += 1
            if done % 20 == 0:
                print(f"  進度: {done}/{len(combos)}")

    elapsed = time.time() - start
    print(f"\n⏱ 完成！{len(results)} 個組合，耗時 {elapsed:.1f}s（{workers} 核）")

    return pd.DataFrame(results)


def main():
    parser = argparse.ArgumentParser(description="多 CPU 港股回測系統")
    parser.add_argument("--symbols", nargs="+", default=DEFAULT_SYMBOLS, help="股票代碼列表")
    parser.add_argument("--workers", type=int, default=None, help="CPU 核數（預設全部）")
    parser.add_argument("--duration", type=int, default=1385, help="數據天數")
    parser.add_argument("--grid", action="store_true", help="參數網格搜索模式")
    parser.add_argument("--output", type=str, default="data/backtest_results.csv", help="輸出 CSV")
    args = parser.parse_args()

    if args.grid:
        df = run_param_grid(args.symbols, workers=args.workers)
        # 找最佳參數
        ok = df[df["status"] == "ok"]
        if not ok.empty:
            best = ok.nlargest(5, "sharpe")
            print("\n🏆 Top 5 參數組合（按 Sharpe）:")
            print(best[["symbol", "fast", "slow", "rsi", "sharpe", "return", "max_dd", "win_rate"]].to_string(index=False))
    else:
        df = run_multiprocess_backtest(args.symbols, args.workers, args.duration)
        # 排序
        ok = df[df["status"] == "ok"].sort_values("sharpe", ascending=False)
        if not ok.empty:
            print("\n📊 回測結果（按 Sharpe 排序）:")
            print(ok[["symbol", "sharpe", "return", "max_dd", "trades", "win_rate"]].to_string(index=False))

    # 保存
    if not df.empty:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        df.to_csv(args.output, index=False, encoding="utf-8-sig")
        print(f"\n💾 結果已保存到 {args.output}")


if __name__ == "__main__":
    main()
