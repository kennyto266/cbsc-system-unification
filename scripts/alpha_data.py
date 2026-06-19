#!/usr/bin/env python3
"""
Alpha 挖掘 Step 1：HSI 成分股數據收集
抓取全部成分股 OHLCV + 合併南北水 → 收益率矩陣。

用法:
    python scripts/alpha_data.py                    # 全部121隻
    python scripts/alpha_data.py --limit 30         # 先測試30隻
"""

import argparse
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd
import requests

ROOT = Path(__file__).parent.parent
DATA_API = "http://18.180.162.113:9191/inst/getInst"
HEADERS = {"accept": "application/json"}


def get_constituents() -> list[dict]:
    """讀取 HSI 成分股"""
    path = ROOT / "data" / "cache" / "hsi_constituents_82.json"
    data = json.load(open(path, encoding="utf-8"))
    return data["blue_chip_stocks"]


def fetch_one(symbol: str) -> tuple[str, pd.DataFrame | None]:
    """抓取一隻股票 OHLCV"""
    try:
        r = requests.get(DATA_API, params={"symbol": symbol, "duration": 1385}, headers=HEADERS, timeout=20)
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
        if not cols or "close" not in cols:
            return symbol, None
        df = pd.concat(cols.values(), axis=1)
        df.columns = list(cols.keys())
        df = df.dropna(how="all")
        df.index = df.index.tz_localize(None) if df.index.tz else df.index
        return symbol, df
    except Exception:
        return symbol, None


def load_southbound() -> pd.DataFrame:
    """載入南北水"""
    path = ROOT / "data" / "sc_full.csv"
    if not path.exists():
        return pd.DataFrame()
    sc = pd.read_csv(path, parse_dates=["date"])
    south = sc[sc["type_name"].str.contains("南向", na=False)]
    daily = south.groupby("date").agg({"net_buy": "sum", "buy": "sum", "sell": "sum"}).sort_index()
    return daily


def main():
    parser = argparse.ArgumentParser(description="Alpha 數據收集")
    parser.add_argument("--limit", type=int, default=None, help="限制股票數量")
    parser.add_argument("--output", type=str, default="data/alpha_data.parquet")
    parser.add_argument("--workers", type=int, default=16)
    args = parser.parse_args()

    constituents = get_constituents()
    if args.limit:
        constituents = constituents[: args.limit]

    symbols = [c["symbol"] for c in constituents]
    sectors = {c["symbol"]: c.get("sector", "") for c in constituents}
    names = {c["symbol"]: c.get("name", "") for c in constituents}

    print(f"📥 Alpha 數據收集")
    print(f"   股票: {len(symbols)} 隻 | CPU: {args.workers} 核")
    print()

    # 批量抓取
    all_data = {}
    start = time.time()

    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(fetch_one, s): s for s in symbols}
        done = 0
        for future in as_completed(futures):
            symbol, df = future.result()
            done += 1
            if df is not None and len(df) > 100:
                all_data[symbol] = df
                print(f"  ✓ [{done}/{len(symbols)}] {symbol} ({names.get(symbol,'')}): {len(df)} 天")
            else:
                print(f"  ✗ [{done}/{len(symbols)}] {symbol}: 無數據")

    elapsed = time.time() - start
    print(f"\n⏱ 抓取完成！{len(all_data)}/{len(symbols)} 隻成功，耗時 {elapsed:.1f}s")

    if not all_data:
        print("❌ 無數據")
        return

    # 構建收益率矩陣
    print(f"\n🔧 構建收益率矩陣...")

    # 收集所有日期
    all_dates = set()
    for df in all_data.values():
        all_dates.update(df.index)
    all_dates = sorted(all_dates)

    # 收益率矩陣 (日期 × 股票)
    returns = pd.DataFrame(index=all_dates, columns=list(all_data.keys()), dtype=float)
    close_prices = pd.DataFrame(index=all_dates, columns=list(all_data.keys()), dtype=float)
    volumes = pd.DataFrame(index=all_dates, columns=list(all_data.keys()), dtype=float)

    for symbol, df in all_data.items():
        for col_target, col_source in [(returns, "close"), (close_prices, "close"), (volumes, "volume")]:
            pass
        # 收益率
        ret = df["close"].pct_change()
        returns[symbol] = ret.reindex(all_dates)
        close_prices[symbol] = df["close"].reindex(all_dates)
        if "volume" in df.columns:
            volumes[symbol] = df["volume"].reindex(all_dates)

    # 南北水
    sb = load_southbound()
    if not sb.empty:
        sb_aligned = sb["net_buy"].reindex(all_dates).ffill().fillna(0)
        print(f"   南北水: {len(sb_aligned)} 天對齊")
    else:
        sb_aligned = pd.Series(0, index=all_dates)

    # 行業 map
    sector_df = pd.DataFrame({"symbol": list(all_data.keys())})
    sector_df["name"] = sector_df["symbol"].map(names)
    sector_df["sector"] = sector_df["symbol"].map(sectors)

    print(f"   收益率矩陣: {returns.shape[0]} 天 × {returns.shape[1]} 隻")
    print(f"   有效數據: {returns.notna().sum().sum()}/{returns.size} ({returns.notna().sum().sum()/returns.size*100:.0f}%)")

    # 保存
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)

    # 用 pickle 存完整數據（parquet 不支援多 DataFrame）
    output_pkl = args.output.replace(".parquet", ".pkl")
    save_data = {
        "returns": returns,
        "close": close_prices,
        "volume": volumes,
        "southbound": sb_aligned,
        "sectors": sector_df,
        "symbols": list(all_data.keys()),
        "fetch_date": pd.Timestamp.now().isoformat(),
    }
    pd.to_pickle(save_data, output_pkl)
    print(f"\n💾 已保存到 {output_pkl}")
    print(f"   收益率矩陣可用於相關性分析 + NN 訓練")

    # 基本統計
    print(f"\n📊 基本統計:")
    valid_returns = returns.dropna(how="all")
    daily_mean = valid_returns.mean(axis=1)
    print(f"   平均日收益率: {daily_mean.mean()*100:.3f}%")
    print(f"   日波動率: {daily_mean.std()*100:.3f}%")
    print(f"   正收益天數: {(daily_mean > 0).sum()}/{len(daily_mean)} ({(daily_mean>0).mean()*100:.0f}%)")


if __name__ == "__main__":
    main()
