#!/usr/bin/env python3
"""
用 yfinance 抓取真實港股歷史數據（20+ 年）。
比數據 API 的 862 天多 7 倍，可以做更穩健的回測。

用法:
    python scripts/yf_fetcher.py                        # 全部 HSI 成分股
    python scripts/yf_fetcher.py --symbols 0700.HK 9988.HK  # 指定股票
    python scripts/yf_fetcher.py --years 5              # 最近5年
"""

import argparse
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
import yfinance as yf

ROOT = Path(__file__).parent.parent


def get_constituents() -> list[str]:
    """讀取 HSI 成分股"""
    import json
    path = ROOT / "data" / "cache" / "hsi_constituents_82.json"
    data = json.load(open(path, encoding="utf-8"))
    stocks = data["blue_chip_stocks"]
    return [s["symbol"] for s in stocks]


def fetch_one(symbol: str, years: int = 5) -> tuple[str, pd.DataFrame | None]:
    """用 yfinance 抓取一隻股票"""
    try:
        period = f"{years}y"
        t = yf.Ticker(symbol)
        hist = t.history(period=period, auto_adjust=True)
        if hist.empty or len(hist) < 100:
            return symbol, None
        hist.index = hist.index.tz_localize(None)
        return symbol, hist
    except Exception:
        return symbol, None


def main():
    parser = argparse.ArgumentParser(description="yfinance 港股歷史數據抓取")
    parser.add_argument("--symbols", nargs="+", default=None)
    parser.add_argument("--years", type=int, default=5, help="歷史年數")
    parser.add_argument("--output", type=str, default="data/price_data/yf_data.pkl")
    parser.add_argument("--workers", type=int, default=10)
    args = parser.parse_args()

    symbols = args.symbols or get_constituents()
    print(f"📥 yfinance 數據抓取")
    print(f"   股票: {len(symbols)} 隻 | 歷史: {args.years} 年 | 線程: {args.workers}")
    print()

    all_data = {}
    all_returns = {}
    all_close = {}
    all_volume = {}

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(fetch_one, s, args.years): s for s in symbols}
        done = 0
        for future in as_completed(futures):
            symbol, df = future.result()
            done += 1
            if df is not None:
                all_data[symbol] = df
                all_close[symbol] = df["Close"]
                all_volume[symbol] = df["Volume"]
                all_returns[symbol] = df["Close"].pct_change()
                print(f"  ✓ [{done}/{len(symbols)}] {symbol}: {len(df)} 天 ({df.index[0].date()} to {df.index[-1].date()})")
            else:
                print(f"  ✗ [{done}/{len(symbols)}] {symbol}: 無數據")

    if not all_data:
        print("❌ 無數據")
        return

    # 構建收益率矩陣
    all_dates = set()
    for s in all_close.values():
        all_dates.update(s.index)
    all_dates = sorted(all_dates)

    returns_df = pd.DataFrame(index=all_dates)
    close_df = pd.DataFrame(index=all_dates)
    vol_df = pd.DataFrame(index=all_dates)

    for sym in all_data:
        returns_df[sym] = all_returns[sym].reindex(all_dates)
        close_df[sym] = all_close[sym].reindex(all_dates)
        vol_df[sym] = all_volume[sym].reindex(all_dates)

    # 載入南北水
    sb_path = ROOT / "data" / "sc_full.csv"
    sb_aligned = None
    if sb_path.exists():
        sc = pd.read_csv(sb_path, parse_dates=["date"])
        south = sc[sc["type_name"].str.contains("南向", na=False)]
        daily = south.groupby("date").agg({"net_buy": "sum"}).sort_index()
        sb_aligned = daily["net_buy"].reindex(all_dates).ffill().fillna(0)

    # 行業
    import json
    sectors_raw = json.load(open(ROOT / "data" / "cache" / "hsi_constituents_82.json", encoding="utf-8"))["blue_chip_stocks"]
    sector_df = pd.DataFrame(sectors_raw)[["symbol", "name", "sector"]]

    save_data = {
        "returns": returns_df,
        "close": close_df,
        "volume": vol_df,
        "southbound": sb_aligned,
        "sectors": sector_df,
        "symbols": list(all_data.keys()),
        "source": "yfinance",
        "fetch_date": pd.Timestamp.now().isoformat(),
    }

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    pd.to_pickle(save_data, args.output)

    print(f"\n✅ 完成！{len(all_data)} 隻股票")
    print(f"   數據源: yfinance（真實歷史數據）")
    print(f"   日期: {returns_df.index.min().date()} to {returns_df.index.max().date()}")
    print(f"   收益率矩陣: {returns_df.shape}")
    print(f"   輸出: {args.output}")


if __name__ == "__main__":
    main()
