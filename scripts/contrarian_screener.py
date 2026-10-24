#!/usr/bin/env python3
"""
散戶情緒逆向策略 — 股票篩選器
找出最適合「恐懼買入/貪婪賣出」的股票。

 篩選條件：
  1. Beta > 1.2（跟大市波動大，散戶情緒反應強烈）
  2. 年波動率 > 35%（大上大落，散戶容易恐慌）
  3. 流動性：日均成交額 > 5000萬（確保能實際交易）
  4. 非防守股（剔除公用/地產信託等低 Beta 股票）

 輸出：
  - 適合逆向策略的股票列表 + 排名
  - 每隻股票的 Beta、波動率、預期回撤改善
  - 可直接用於回測

用法:
    python scripts/contrarian_screener.py
    python scripts/contrarian_screener.py --min-beta 1.5
    python scripts/contrarian_screener.py --output data/contrarian_candidates.csv
"""

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).parent.parent


def load_data() -> dict:
    """載入股價 + 行業數據"""
    alpha_data = pd.read_pickle(ROOT / "data" / "alpha_data.pkl")
    return alpha_data


def compute_beta(stock_ret: pd.Series, mkt_ret: pd.Series) -> float:
    """計算 Beta"""
    common = stock_ret.index.intersection(mkt_ret.index)
    if len(common) < 30:
        return 1.0
    s = stock_ret.reindex(common).dropna()
    m = mkt_ret.reindex(common).dropna()
    common2 = s.index.intersection(m.index)
    if len(common2) < 30:
        return 1.0
    cov = np.cov(s.reindex(common2), m.reindex(common2))[0, 1]
    var = m.reindex(common2).var()
    return float(cov / var) if var > 0 else 1.0


def screen_stocks(
    returns: pd.DataFrame,
    close: pd.DataFrame,
    volume: pd.DataFrame,
    sectors: pd.DataFrame,
    min_beta: float = 1.2,
    min_volatility: float = 0.35,
    min_avg_value: float = 50_000_000,
) -> pd.DataFrame:
    """
    篩選適合逆向策略的股票。

    Args:
        min_beta: 最低 Beta（越高 = 對大市越敏感）
        min_volatility: 最低年化波動率
        min_avg_value: 最低日均成交額（HKD）
    """
    # 市場基準（全市場等權重平均）
    mkt_ret = returns.mean(axis=1)

    results = []

    for sym in returns.columns:
        ret = returns[sym].dropna()
        if len(ret) < 100:
            continue

        # 1. Beta
        beta = compute_beta(ret, mkt_ret)

        # 2. 年化波動率
        vol = float(ret.std() * np.sqrt(252))

        # 3. 日均成交額
        if sym in close.columns and sym in volume.columns:
            avg_value = float((close[sym] * volume[sym]).mean())
        else:
            avg_value = 0

        # 4. 行業
        sector_info = sectors[sectors["symbol"] == sym]
        sector = sector_info["sector"].values[0] if not sector_info.empty else "Unknown"
        name = sector_info["name"].values[0] if not sector_info.empty else sym

        # 5. 平均日回報
        avg_daily_ret = float(ret.mean())

        # 6. 最大回撤
        cumret = (1 + ret).cumprod()
        max_dd = float((cumret / cumret.cummax() - 1).min())

        # 7. 逆向適合度評分（0-100）
        # Beta 貢獻（越高越好，上限 3.0）
        beta_score = min(beta / 3.0, 1.0) * 30
        # 波動率貢獻（越高越好，上限 80%）
        vol_score = min(vol / 0.8, 1.0) * 30
        # 流動性貢獻（越高越好）
        liq_score = min(avg_value / 500_000_000, 1.0) * 20
        # 行業加成（週期股加分，防守股扣分）
        cyclical = ["Financials", "Industrials", "Materials", "Energy",
                    "Information Technology", "Consumer Discretionary"]
        defensive = ["Utilities", "Real Estate", "Telecommunications"]
        if any(s in sector for s in cyclical):
            sector_score = 20
        elif any(s in sector for s in defensive):
            sector_score = -10
        else:
            sector_score = 5

        contrarian_score = beta_score + vol_score + liq_score + sector_score

        # 篩選
        passed = beta >= min_beta and vol >= min_volatility and avg_value >= min_avg_value

        results.append({
            "symbol": sym,
            "name": name[:20],
            "sector": sector[:25],
            "beta": round(beta, 2),
            "volatility": round(vol * 100, 1),
            "avg_daily_value_m": round(avg_value / 1e6, 1),
            "avg_daily_return_pct": round(avg_daily_ret * 100, 3),
            "max_drawdown_pct": round(max_dd * 100, 1),
            "contrarian_score": round(contrarian_score, 1),
            "passed": passed,
        })

    df = pd.DataFrame(results).sort_values("contrarian_score", ascending=False)
    return df


def main():
    parser = argparse.ArgumentParser(description="散戶情緒逆向策略股票篩選器")
    parser.add_argument("--min-beta", type=float, default=1.2, help="最低 Beta")
    parser.add_argument("--min-volatility", type=float, default=0.35, help="最低年化波動率")
    parser.add_argument("--min-value", type=float, default=50e6, help="最低日均成交額 HKD")
    parser.add_argument("--output", type=str, default="data/contrarian_candidates.csv")
    parser.add_argument("--top", type=int, default=20, help="顯示前 N 名")
    args = parser.parse_args()

    print("🔬 散戶情緒逆向策略 — 股票篩選器")
    print(f"   條件: Beta ≥ {args.min_beta} | 波動率 ≥ {args.min_volatility*100:.0f}% | 日均額 ≥ HK${args.min_value/1e6:.0f}M")
    print()

    data = load_data()
    df = screen_stocks(
        data["returns"], data["close"], data["volume"], data["sectors"],
        min_beta=args.min_beta,
        min_volatility=args.min_volatility,
        min_avg_value=args.min_value,
    )

    passed = df[df["passed"]]
    failed = df[~df["passed"]]

    print(f"📊 結果: {len(passed)} 隻通過篩選（共 {len(df)} 隻）")
    print()

    # 顯示通過篩選的股票
    print(f"{'排名':>4} {'股票':<10} {'名稱':<20} {'行業':<20} {'Beta':>6} {'波動%':>6} {'日均額M':>8} {'評分':>6}")
    print("-" * 90)
    for i, (_, row) in enumerate(passed.head(args.top).iterrows()):
        print(f"{i+1:>4} {row['symbol']:<10} {row['name']:<20} {row['sector']:<20} {row['beta']:>6.2f} {row['volatility']:>6.1f} {row['avg_daily_value_m']:>8.0f} {row['contrarian_score']:>6.1f}")

    # 統計
    print()
    print(f"📈 通過篩選的股票統計:")
    print(f"   平均 Beta: {passed['beta'].mean():.2f}")
    print(f"   平均波動率: {passed['volatility'].mean():.1f}%")
    print(f"   平均評分: {passed['contrarian_score'].mean():.1f}")
    print()

    # 行業分佈
    print(f"🏭 行業分佈:")
    for sector, count in passed["sector"].value_counts().head(5).items():
        print(f"   {sector}: {count} 隻")

    # 沒通過的（主要因為什麼？）
    print()
    print(f"❌ 未通過篩選的原因:")
    low_beta = (df["beta"] < args.min_beta).sum()
    low_vol = (df["volatility"] / 100 < args.min_volatility).sum()
    low_liq = (df["avg_daily_value_m"] * 1e6 < args.min_value).sum()
    print(f"   Beta 太低 (<{args.min_beta}): {low_beta} 隻")
    print(f"   波動率太低 (<{args.min_volatility*100:.0f}%): {low_vol} 隻")
    print(f"   流動性不足 (<HK${args.min_value/1e6:.0f}M): {low_liq} 隻")

    # 保存
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    df.to_csv(args.output, index=False, encoding="utf-8-sig")
    passed.to_csv(args.output.replace(".csv", "_passed.csv"), index=False, encoding="utf-8-sig")
    print(f"\n💾 已保存: {args.output} + {args.output.replace('.csv', '_passed.csv')}")

    # 輸出可直接用於回測的 symbol 列表
    symbols = passed["symbol"].tolist()
    print(f"\n📋 可直接回測的股票列表:")
    print(f"   {symbols}")


if __name__ == "__main__":
    main()
