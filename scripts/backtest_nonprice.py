#!/usr/bin/env python3
"""
Non-Price Data 策略回測
用南北水資金流向 + 成交額 + 升跌比做交易信號，唔依賴股價指標。

 策略：
  1. southbound_follow — 大陸資金淨流入跟買（南北水 > 均值 → 加倉）
  2. volume_surge — 放量突破策略（成交額 > 1.5x均值 → 買入）
  3. breadth_trend — 市場廣度趨勢（升跌比連續 > 1 → 買入）
  4. smart_money — 綜合非價格信號（南北水+成交額+升跌比投票）
  5. flow_momentum — 資金動量（南北水5日變化 > 0 → 買入）

用法:
    python scripts/backtest_nonprice.py
    python scripts/backtest_nonprice.py --symbols 0700.HK 9988.HK 1810.HK
"""

import argparse
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import requests

DATA_API = "http://18.180.162.113:9191/inst/getInst"
TOTAL_COST = 0.0023  # 印花稅 + 佣金
ROOT = Path(__file__).parent.parent


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


def load_nonprice_data() -> dict:
    """載入南北水 + HKEX 成交統計"""
    data = {}

    # 南北水
    sc_path = ROOT / "data" / "stock_connect.csv"
    if sc_path.exists():
        sc = pd.read_csv(sc_path, parse_dates=["date"])
        sc = sc.set_index("date")
        data["stock_connect"] = sc

    # HKEX 每日統計
    hk_path = ROOT / "data" / "hkex_daily.csv"
    if hk_path.exists():
        hk = pd.read_csv(hk_path, parse_dates=["date"])
        hk = hk.set_index("date")
        data["hkex"] = hk

    return data


# ==============================================================================
# Non-Price Data 策略
# ==============================================================================

def strat_volume_surge(df, nonprice=None, window=20, threshold=1.5):
    """
    放量策略：成交額 > 1.5x 均值 → 買入信號
    縮量 → 減倉
    """
    vol = df["volume"]
    vol_ma = vol.rolling(window).mean().shift(1)
    pos = pd.Series(0, index=df.index)
    pos[vol > vol_ma * threshold] = 1   # 放量買入
    pos[vol < vol_ma * 0.5] = -1        # 縮量減倉
    return pos


def strat_breadth_trend(df, nonprice=None, lookback=3):
    """
    市場廣度策略：連續 N 日升跌比 > 1 → 買入
    需要 HKEX 升跌數據（nonprice["hkex"]）
    """
    pos = pd.Series(0, index=df.index)
    if nonprice is None or "hkex" not in nonprice:
        return pos

    hk = nonprice["hkex"]
    adv_col = "advanced_stocks" if "advanced_stocks" in hk.columns else "advanced"
    dec_col = "declined_stocks" if "declined_stocks" in hk.columns else "declined"

    if adv_col not in hk.columns or dec_col not in hk.columns:
        return pos

    adv = pd.to_numeric(hk[adv_col], errors="coerce")
    dec = pd.to_numeric(hk[dec_col], errors="coerce")
    ad_ratio = adv / dec.replace(0, np.nan)

    # 連續 lookback 日升跌比 > 1 = 升市
    bull = (ad_ratio > 1).rolling(lookback).sum()
    bear = (ad_ratio < 1).rolling(lookback).sum()

    for date in df.index:
        if date in bull.index:
            b = bull.get(date)
            s = bear.get(date)
            if pd.notna(b) and b >= lookback:
                pos.loc[date] = 1
            elif pd.notna(s) and s >= lookback:
                pos.loc[date] = -1

    return pos


def strat_southbound_follow(df, nonprice=None, ma_window=5):
    """
    南北水跟買策略：大陸資金淨流入 > 均值 → 買入
    淨流出 → 賣出
    """
    pos = pd.Series(0, index=df.index)
    if nonprice is None or "stock_connect" not in nonprice:
        return pos

    sc = nonprice["stock_connect"]
    if "southbound_net_mil" not in sc.columns:
        return pos

    net = sc["southbound_net_mil"]
    net_ma = net.rolling(ma_window).mean()

    for date in df.index:
        # 找最近的南北水數據
        mask = sc.index <= date
        if mask.any():
            latest = sc[mask].iloc[-1]
            net_val = latest.get("southbound_net_mil", 0)
            ma_val = net_ma[sc[mask].index[-1]] if len(net_ma[sc[mask].index]) > 0 else 0

            if pd.notna(net_val) and pd.notna(ma_val):
                if net_val > ma_val and net_val > 0:
                    pos.loc[date] = 1    # 資金流入跟買
                elif net_val < ma_val and net_val < 0:
                    pos.loc[date] = -1   # 資金流出賣出

    return pos


def strat_flow_momentum(df, nonprice=None, window=5):
    """
    資金動量：南北水 5 日變化為正 → 買入
    """
    pos = pd.Series(0, index=df.index)
    if nonprice is None or "stock_connect" not in nonprice:
        return pos

    sc = nonprice["stock_connect"]
    if "southbound_net_mil" not in sc.columns:
        return pos

    net = sc["southbound_net_mil"]
    flow_change = net.diff(window)

    for date in df.index:
        mask = sc.index <= date
        if mask.any():
            latest_change = flow_change.get(sc[mask].index[-1])
            if pd.notna(latest_change):
                pos.loc[date] = 1 if latest_change > 0 else -1 if latest_change < 0 else 0

    return pos


def strat_smart_money(df, nonprice=None):
    """
    智慧資金策略：綜合非價格信號投票
    - 南北水淨流入 > 0 → +1
    - 成交額上升 → +1
    - 升跌比 > 1 → +1
    票數 > 1 → 買入
    """
    pos = pd.Series(0, index=df.index)
    if nonprice is None:
        return pos

    sc = nonprice.get("stock_connect")
    hk = nonprice.get("hkex")

    for date in df.index:
        votes = 0

        # 南北水信號
        if sc is not None and "southbound_net_mil" in sc.columns:
            mask = sc.index <= date
            if mask.any():
                net = sc[mask]["southbound_net_mil"].iloc[-1]
                if pd.notna(net):
                    votes += 1 if net > 0 else -1 if net < 0 else 0

        # 成交額信號（放量 = +1）
        if "volume" in df.columns:
            vol_ma = df["volume"].rolling(20).mean()
            mask = df.index <= date
            if mask.any() and pd.notna(vol_ma.get(date)):
                if df.loc[date, "volume"] > vol_ma.get(date, 0) * 1.2:
                    votes += 1
                elif df.loc[date, "volume"] < vol_ma.get(date, 0) * 0.8:
                    votes -= 1

        # 升跌比信號
        if hk is not None:
            adv_col = "advanced_stocks" if "advanced_stocks" in hk.columns else "advanced"
            dec_col = "declined_stocks" if "declined_stocks" in hk.columns else "declined"
            if adv_col in hk.columns:
                mask = hk.index <= date
                if mask.any():
                    adv = pd.to_numeric(hk[mask][adv_col], errors="coerce").iloc[-1]
                    dec = pd.to_numeric(hk[mask][dec_col], errors="coerce").iloc[-1]
                    if pd.notna(adv) and pd.notna(dec) and dec > 0:
                        votes += 1 if adv > dec else -1

        pos.loc[date] = 1 if votes > 0 else -1 if votes < 0 else 0

    return pos


STRATEGIES = {
    "volume_surge": strat_volume_surge,
    "breadth_trend": strat_breadth_trend,
    "southbound_follow": strat_southbound_follow,
    "flow_momentum": strat_flow_momentum,
    "smart_money": strat_smart_money,
}


# ==============================================================================
# 回測引擎
# ==============================================================================

def backtest(df, strategy_fn, nonprice=None, cost=TOTAL_COST):
    pos = strategy_fn(df, nonprice=nonprice).shift(1).fillna(0)
    ret = df["close"].pct_change().fillna(0)
    turnover = pos.diff().abs()
    strat_ret = ret * pos - turnover * cost

    equity = (1 + strat_ret).cumprod()
    max_dd = float((equity / equity.cummax() - 1).min()) if len(equity) else 0
    mean_ret = strat_ret.mean() * 252
    std_ret = strat_ret.std(ddof=0) * np.sqrt(252)
    sharpe = float(mean_ret / std_ret) if std_ret > 0 else 0.0
    trades = int(turnover[turnover > 0].count())
    nonzero = strat_ret[strat_ret != 0]
    win_rate = float((nonzero[nonzero > 0].count()) / max(1, len(nonzero)))
    calmar = float(mean_ret / abs(max_dd)) if max_dd != 0 else 0

    return {
        "sharpe": round(sharpe, 3),
        "return_annual": round(mean_ret, 3),
        "max_dd": round(max_dd, 3),
        "calmar": round(calmar, 3),
        "trades": trades,
        "win_rate": round(win_rate, 3),
        "total_return": round(float(equity.iloc[-1] - 1), 3) if len(equity) else 0,
    }


def worker(args):
    symbol, nonprice_data, duration = args
    try:
        df = fetch_series(symbol, duration)
    except Exception as e:
        return [{"symbol": symbol, "strategy": "N/A", "status": f"error: {str(e)[:40]}"}]

    # 重建 nonprice dict（多進程需要可序列化）
    results = []
    for name, fn in STRATEGIES.items():
        try:
            res = backtest(df, fn, nonprice=nonprice_data)
            res.update({"symbol": symbol, "strategy": name, "status": "ok"})
            results.append(res)
        except Exception as e:
            results.append({"symbol": symbol, "strategy": name, "status": f"error: {str(e)[:40]}"})

    return results


STOCK_POOL = [
    "0700.HK", "9988.HK", "0939.HK", "1810.HK", "1177.HK", "0992.HK",
    "0388.HK", "0005.HK", "0883.HK", "9618.HK", "3690.HK", "9999.HK",
    "1299.HK", "2318.HK", "1398.HK", "2828.HK", "2800.HK",
]


def main():
    import multiprocessing
    parser = argparse.ArgumentParser(description="Non-Price Data 策略回測")
    parser.add_argument("--symbols", nargs="+", default=STOCK_POOL)
    parser.add_argument("--workers", type=int, default=None)
    parser.add_argument("--output", type=str, default="data/backtest_nonprice.csv")
    parser.add_argument("--duration", type=int, default=1385)
    args = parser.parse_args()

    workers = args.workers or min(multiprocessing.cpu_count(), len(args.symbols))

    print("🧠 Non-Price Data 策略回測")
    print(f"   股票: {len(args.symbols)} 隻 | 策略: {len(STRATEGIES)} 個 | CPU: {workers} 核")
    print(f"   策略: {', '.join(STRATEGIES.keys())}")
    print(f"   信號來源: 南北水資金流向 + 成交額 + 升跌比")
    print()

    # 載入 non-price data
    nonprice = load_nonprice_data()
    if nonprice:
        for k, v in nonprice.items():
            print(f"   📊 {k}: {len(v)} 天數據 ({v.index.min().date()} to {v.index.max().date()})")

    # 序列化 nonprice dict 傳給子進程
    np_serializable = {k: v for k, v in nonprice.items()}

    tasks = [(s, np_serializable, args.duration) for s in args.symbols]
    all_results = []
    start = time.time()

    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(worker, t): t[0] for t in tasks}
        for future in as_completed(futures):
            symbol = futures[future]
            results = future.result()
            all_results.extend(results)
            ok = [r for r in results if r.get("status") == "ok"]
            if ok:
                best = max(ok, key=lambda r: r.get("sharpe", 0))
                print(f"  ✓ {symbol}: 最佳 {best['strategy']} Sharpe={best['sharpe']:+.2f}")

    elapsed = time.time() - start
    df = pd.DataFrame(all_results)
    ok_df = df[df["status"] == "ok"].copy()

    print(f"\n⏱ 完成！{len(all_results)} 個結果，耗時 {elapsed:.1f}s")

    if ok_df.empty:
        print("⚠ 無成功結果")
        return

    ok_df = ok_df.sort_values("sharpe", ascending=False)
    print(f"\n🏆 Top 10 Non-Price 策略（按 Sharpe）:")
    print(ok_df.head(10)[["symbol", "strategy", "sharpe", "return_annual", "max_dd", "win_rate", "trades"]].to_string(index=False))

    print(f"\n📊 各策略平均 Sharpe:")
    summary = ok_df.groupby("strategy")["sharpe"].agg(["mean", "std", "count", "max"]).sort_values("mean", ascending=False)
    print(summary.to_string())

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    df.to_csv(args.output, index=False, encoding="utf-8-sig")
    print(f"\n💾 結果已保存到 {args.output}")


if __name__ == "__main__":
    main()
