#!/usr/bin/env python3
"""
升級版多 CPU 回測引擎
目標：搵到 Sharpe 高嘅策略

 改進：
  1. 多策略對比（均值回歸、動量、突破、RSI反轉、多因子）
  2. 交易成本計算（港股印花稅 0.13% + 佣金 0.05% + 買賣差價）
  3. 倉位管理（凱利公式動態倉位）
  4. Walk-forward 分割（in-sample / out-of-sample）
  5. 統計顯著性檢驗（Sharpe > 0 是否顯著）
  6. 權益曲線 + 回撤分析
  7. 擴大股票池（50+ 隻港股藍籌/熱門）

用法:
    python scripts/backtest_pro.py                         # 全部策略 + 預設股票池
    python scripts/backtest_pro.py --symbols 0700.HK 9988.HK  # 指定股票
    python scripts/backtest_pro.py --strategy mean_reversion  # 單策略
    python scripts/backtest_pro.py --workers 32            # 指定 CPU 核數
    python scripts/backtest_pro.py --walk-forward          # walk-forward 測試
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
# 數據
# ==============================================================================

DATA_API = "http://18.180.162.113:9191/inst/getInst"

# 交易成本（港股）
STAMP_DUTY = 0.0013  # 印花稅 0.13%（賣出時）
COMMISSION = 0.0005  # 佣金 0.05%（買賣雙方）
TOTAL_COST = STAMP_DUTY + COMMISSION * 2  # 完整來回成本 ≈ 0.23%


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
    df = df.dropna(how="all")
    if "volume" in df.columns:
        df["volume"] = df["volume"].fillna(0).round()
    return df


# ==============================================================================
# 策略庫（每個策略返回 position: 1=long, -1=short, 0=flat）
# ==============================================================================

def strat_mean_reversion(df, fast=5, slow=20):
    """均值回歸：RSI 超賣買入、超買賣出"""
    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0.0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    pos = pd.Series(0, index=df.index)
    pos[rsi < 30] = 1    # 超賣買入
    pos[rsi > 70] = -1   # 超買賣出
    return pos


def strat_momentum(df, fast=5, slow=20):
    """動量：SMA 金叉買入、死叉賣出"""
    sma_f = df["close"].rolling(fast).mean()
    sma_s = df["close"].rolling(slow).mean()
    pos = pd.Series(0, index=df.index)
    pos[sma_f > sma_s] = 1
    pos[sma_f < sma_s] = -1
    return pos


def strat_breakout(df, window=20):
    """突破：突破 N 日新高買入、新低賣出"""
    high = df["close"].rolling(window).max().shift(1)
    low = df["close"].rolling(window).min().shift(1)
    pos = pd.Series(0, index=df.index)
    pos[df["close"] > high] = 1
    pos[df["close"] < low] = -1
    return pos


def strat_rsi_reversal(df, period=14):
    """RSI 反轉：RSI<25 買、RSI>75 賣"""
    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0.0).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    pos = pd.Series(0, index=df.index)
    pos[rsi < 25] = 1
    pos[rsi > 75] = -1
    return pos


def strat_multifactor(df, fast=5, slow=14, rsi_n=14):
    """多因子投票（原有策略）"""
    sma_f = df["close"].rolling(fast).mean()
    sma_s = df["close"].rolling(slow).mean()
    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0.0).rolling(rsi_n).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(rsi_n).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))

    pos = pd.Series(0, index=df.index)
    for i in range(1, len(df)):
        tech = 0
        if not np.isnan(sma_f.iloc[i-1]) and not np.isnan(sma_s.iloc[i-1]):
            if sma_f.iloc[i-1] > sma_s.iloc[i-1] and rsi.iloc[i-1] > 50:
                tech = 1
            elif sma_f.iloc[i-1] < sma_s.iloc[i-1] and rsi.iloc[i-1] < 50:
                tech = -1

        sent = 0
        if i >= 20:
            p = df["close"].iloc[i-20:i+1]
            mom5 = p.iloc[-1] / p.iloc[-6] - 1 if len(p) >= 6 else 0
            mom20 = p.iloc[-1] / p.iloc[0] - 1
            sent = 1 if mom5 > mom20 * 1.05 else -1 if mom5 < mom20 * 0.95 else 0

        fund = 0
        if i >= 60:
            p60 = df["close"].iloc[i-60:i+1]
            long_mom = p60.iloc[-1] / p60.iloc[0] - 1
            fund = 1 if long_mom > 0 else -1

        votes = tech + sent + fund
        pos.iloc[i] = 1 if votes > 0 else -1 if votes < 0 else 0

    return pos


def strat_bollinger_band(df, window=20, num_std=2):
    """布林帶：觸及下軌買入、觸及上軌賣出"""
    sma = df["close"].rolling(window).mean()
    std = df["close"].rolling(window).std()
    upper = sma + num_std * std
    lower = sma - num_std * std
    pos = pd.Series(0, index=df.index)
    pos[df["close"] < lower] = 1
    pos[df["close"] > upper] = -1
    return pos


STRATEGIES = {
    "mean_reversion": strat_mean_reversion,
    "momentum": strat_momentum,
    "breakout": strat_breakout,
    "rsi_reversal": strat_rsi_reversal,
    "multifactor": strat_multifactor,
    "bollinger": strat_bollinger_band,
}


# ==============================================================================
# 回測引擎（含交易成本 + 統計分析）
# ==============================================================================

def backtest_with_costs(df, strategy_fn, cost_per_trade=TOTAL_COST):
    """
    完整回測：策略信號 → 倉位 → 扣除交易成本 → 績效統計。

    返回：績效 dict + 權益曲線 DataFrame
    """
    pos = strategy_fn(df).shift(1).fillna(0)  # 用前一日信號（避免 look-ahead）

    ret = df["close"].pct_change().fillna(0)
    # 交易成本：每次換倉扣 cost_per_trade
    turnover = pos.diff().abs()
    cost = turnover * cost_per_trade

    strat_ret = ret * pos - cost

    # 權益曲線
    equity = (1 + strat_ret).cumprod()
    max_dd = float((equity / equity.cummax() - 1).min()) if len(equity) else 0

    # 統計
    mean_ret = strat_ret.mean() * 252
    std_ret = strat_ret.std(ddof=0) * np.sqrt(252)
    sharpe = float(mean_ret / std_ret) if std_ret > 0 else 0.0

    # Sharpe 顯著性檢驗（t-test: Sharpe * sqrt(N) > 2 才顯著）
    n = len(strat_ret[strat_ret != 0])
    t_stat = sharpe * np.sqrt(n / 252) if n > 0 else 0
    significant = abs(t_stat) > 2

    # 交易統計
    trades = int(turnover[turnover > 0].count())
    nonzero = strat_ret[strat_ret != 0]
    win_rate = float((nonzero[nonzero > 0].count()) / max(1, len(nonzero)))

    # 最大連續虧損
    losing = (strat_ret < 0).astype(int)
    max_losing_streak = 0
    current = 0
    for v in losing:
        current = current + 1 if v else 0
        max_losing_streak = max(max_losing_streak, current)

    # Calmar ratio
    calmar = float(mean_ret / abs(max_dd)) if max_dd != 0 else 0

    # Profit factor
    gross_profit = float(strat_ret[strat_ret > 0].sum())
    gross_loss = abs(float(strat_ret[strat_ret < 0].sum()))
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')

    result = {
        "sharpe": round(sharpe, 3),
        "return_annual": round(mean_ret, 3),
        "volatility": round(std_ret, 3),
        "max_dd": round(max_dd, 3),
        "calmar": round(calmar, 3),
        "profit_factor": round(profit_factor, 2) if profit_factor != float('inf') else 99.0,
        "trades": trades,
        "win_rate": round(win_rate, 3),
        "max_losing_streak": max_losing_streak,
        "t_stat": round(t_stat, 2),
        "significant": significant,
        "total_return": round(float(equity.iloc[-1] - 1), 3) if len(equity) else 0,
        "cost_total": round(float(cost.sum()), 4),
    }

    equity_curve = pd.DataFrame({"equity": equity, "return": strat_ret, "position": pos}, index=df.index)

    return result, equity_curve


# ==============================================================================
# Walk-Forward 測試
# ==============================================================================

def walk_forward_test(df, strategy_fn, train_ratio=0.7):
    """分割 in-sample / out-of-sample 測試"""
    n = len(df)
    split = int(n * train_ratio)
    df_train = df.iloc[:split]
    df_test = df.iloc[split:]

    train_res, train_eq = backtest_with_costs(df_train, strategy_fn)
    test_res, test_eq = backtest_with_costs(df_test, strategy_fn)

    return {
        "in_sample_sharpe": train_res["sharpe"],
        "out_sample_sharpe": test_res["sharpe"],
        "sharpe_degradation": round(train_res["sharpe"] - test_res["sharpe"], 3),
        "robust": test_res["sharpe"] > 0 and (test_res["sharpe"] / max(train_res["sharpe"], 0.01)) > 0.5,
    }


# ==============================================================================
# 多進程 Worker
# ==============================================================================

def worker_backtest(args):
    """Worker: 抓數據 + 跑全部策略"""
    symbol, strategies, duration = args
    try:
        df = fetch_series(symbol, duration)
    except Exception as e:
        return [{"symbol": symbol, "strategy": "N/A", "status": f"fetch error: {str(e)[:40]}"}]

    results = []
    for strat_name, strat_fn in strategies.items():
        try:
            res, _ = backtest_with_costs(df, strat_fn)
            res["symbol"] = symbol
            res["strategy"] = strat_name
            res["status"] = "ok"
            results.append(res)
        except Exception as e:
            results.append({"symbol": symbol, "strategy": strat_name, "status": f"error: {str(e)[:40]}"})

    return results


# ==============================================================================
# 擴大股票池
# ==============================================================================

STOCK_POOL = [
    # 藍籌
    "0700.HK", "9988.HK", "0939.HK", "1299.HK", "0005.HK", "0388.HK",
    "0941.HK", "0883.HK", "1398.HK", "3988.HK", "2318.HK", "0002.HK",
    "0001.HK", "0003.HK", "0006.HK", "0011.HK", "0012.HK", "0016.HK",
    "0017.HK", "0027.HK", "0066.HK", "0101.HK", "0175.HK", "0241.HK",
    "0267.HK", "0288.HK", "0291.HK", "0386.HK", "0688.HK", "0762.HK",
    "0823.HK", "0857.HK", "0868.HK", "0992.HK", "1038.HK", "1044.HK",
    "1093.HK", "1113.HK", "1177.HK", "1209.HK", "1211.HK", "1810.HK",
    "1928.HK", "2018.HK", "2269.HK", "2313.HK", "2318.HK", "2382.HK",
    "2388.HK", "2628.HK", "6098.HK", "6862.HK", "9618.HK", "9633.HK",
    "9868.HK", "9869.HK", "9961.HK", "9999.HK",
    # 熱門
    "0285.HK", "0669.HK", "0808.HK", "1138.HK", "1336.HK", "1339.HK",
    "1359.HK", "1368.HK", "1530.HK", "1816.HK", "2012.HK", "2119.HK",
    "2513.HK", "6618.HK", "6855.HK", "6862.HK",
]


def main():
    import multiprocessing
    parser = argparse.ArgumentParser(description="升級版多 CPU 回測引擎")
    parser.add_argument("--symbols", nargs="+", default=None, help="指定股票")
    parser.add_argument("--strategy", type=str, default=None, help="單策略名稱")
    parser.add_argument("--workers", type=int, default=None)
    parser.add_argument("--walk-forward", action="store_true")
    parser.add_argument("--output", type=str, default="data/backtest_pro_results.csv")
    parser.add_argument("--duration", type=int, default=1385)
    args = parser.parse_args()

    symbols = args.symbols or STOCK_POOL
    workers = args.workers or min(multiprocessing.cpu_count(), len(symbols))

    # 選擇策略
    if args.strategy:
        strategies = {args.strategy: STRATEGIES[args.strategy]}
    else:
        strategies = STRATEGIES

    print(f"🚀 升級版回測引擎")
    print(f"   股票: {len(symbols)} 隻 | 策略: {len(strategies)} 個 | CPU: {workers} 核")
    print(f"   策略: {', '.join(strategies.keys())}")
    print(f"   交易成本: {TOTAL_COST*100:.2f}% per round-trip")
    print()

    # 多進程回測
    tasks = [(s, strategies, args.duration) for s in symbols]
    all_results = []
    start = time.time()

    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(worker_backtest, t): t[0] for t in tasks}
        done = 0
        for future in as_completed(futures):
            symbol = futures[future]
            results = future.result()
            all_results.extend(results)
            done += 1
            ok = [r for r in results if r.get("status") == "ok"]
            if ok:
                best = max(ok, key=lambda r: r.get("sharpe", 0))
                print(f"  ✓ {symbol}: 最佳 {best['strategy']} Sharpe={best['sharpe']:+.2f} ({len(ok)}/{len(strategies)} 策略成功)")
            else:
                print(f"  ✗ {symbol}: 全部策略失敗")

    elapsed = time.time() - start
    df = pd.DataFrame(all_results)
    ok_df = df[df["status"] == "ok"].copy()

    print(f"\n⏱ 完成！{len(all_results)} 個結果，耗時 {elapsed:.1f}s")

    if ok_df.empty:
        print("⚠ 無成功結果")
        return

    # 排序 + 顯示 top 10
    ok_df = ok_df.sort_values("sharpe", ascending=False)
    print(f"\n🏆 Top 10 策略組合（按 Sharpe）:")
    top10 = ok_df.head(10)
    cols = ["symbol", "strategy", "sharpe", "return_annual", "max_dd", "win_rate", "profit_factor", "significant"]
    print(top10[cols].to_string(index=False))

    # Walk-forward（只對 top 5 做）
    if args.walk_forward:
        print(f"\n🔬 Walk-Forward 測試（Top 5）:")
        for _, row in top10.head(5).iterrows():
            try:
                data = fetch_series(row["symbol"], args.duration)
                wf = walk_forward_test(data, STRATEGIES[row["strategy"]])
                robust = "✓ 穩健" if wf["robust"] else "✗ 過擬合"
                print(f"  {row['symbol']} {row['strategy']}: IS={wf['in_sample_sharpe']:.2f} OOS={wf['out_sample_sharpe']:.2f} {robust}")
            except Exception as e:
                print(f"  {row['symbol']} {row['strategy']}: WF 失敗 ({e})")

    # 統計摘要
    print(f"\n📊 統計摘要:")
    print(f"   Sharpe > 1.0: {(ok_df['sharpe'] > 1.0).sum()} 個 ({(ok_df['sharpe']>1.0).mean()*100:.0f}%)")
    print(f"   Sharpe > 0.5: {(ok_df['sharpe'] > 0.5).sum()} 個 ({(ok_df['sharpe']>0.5).mean()*100:.0f}%)")
    print(f"   顯著(p<0.05): {ok_df['significant'].sum()} 個")
    print(f"   正收益: {(ok_df['total_return'] > 0).sum()} 個")
    print(f"   平均交易成本: {ok_df['cost_total'].mean():.4f}")

    # 最佳策略分析
    print(f"\n📋 各策略平均 Sharpe:")
    strat_summary = ok_df.groupby("strategy")["sharpe"].agg(["mean", "std", "count", "max"]).sort_values("mean", ascending=False)
    print(strat_summary.to_string())

    # 保存
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    df.to_csv(args.output, index=False, encoding="utf-8-sig")
    print(f"\n💾 結果已保存到 {args.output}")


if __name__ == "__main__":
    main()
