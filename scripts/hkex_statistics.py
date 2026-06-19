#!/usr/bin/env python3
"""
HKEX 數據統計分析 + 圖表可視化
用統計學方法分析 5-6 月市場數據。

分析內容：
  1. 恆指走勢：移動平均、波動率、收益率分佈
  2. 成交額：均值/中位數/標準差、趨勢線
  3. 升跌統計：升跌比、市場廣度
  4. 十大活躍股：出現頻率、成交額排名
  5. 相關性分析：成交額 vs 升跌、恆指 vs 成交額

輸出：
  - 統計摘要 JSON
  - 圖表 PNG（pyqtgraph，配合 GUI 深色主題）
  - 數據也導出供 Dashboard 使用

用法:
    python scripts/hkex_statistics.py --excel data/hkex_may_jun.xlsx
    python scripts/hkex_statistics.py --excel data/hkex_may_jun.xlsx --charts
"""

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).parent.parent / "data"
GUI_DIR = Path(__file__).parent.parent  # for cbsc_gui.py


def load_excel(excel_path: str) -> dict:
    """讀取 Excel 的所有 sheet"""
    sheets = pd.read_excel(excel_path, sheet_name=None)
    return sheets


def analyze_market_summary(df: pd.DataFrame) -> dict:
    """市場概要統計分析"""
    df = df.sort_values("date").copy()

    # 數值欄位
    for col in ["turnover_hkd", "total_shares", "deals", "advanced", "declined"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    stats = {
        "period": f"{df['date'].min()} 至 {df['date'].max()}",
        "trading_days": len(df),
    }

    # 成交額統計
    if "turnover_hkd" in df.columns:
        tov = df["turnover_hkd"].dropna()
        stats["turnover"] = {
            "mean_billion": round(tov.mean() / 1e9, 2),
            "median_billion": round(tov.median() / 1e9, 2),
            "std_billion": round(tov.std() / 1e9, 2),
            "min_billion": round(tov.min() / 1e9, 2),
            "max_billion": round(tov.max() / 1e9, 2),
            "max_date": df.loc[tov.idxmax(), "date"],
            "min_date": df.loc[tov.idxmin(), "date"],
        }

    # 成交宗數統計
    if "deals" in df.columns:
        deals = df["deals"].dropna()
        stats["deals"] = {
            "mean_million": round(deals.mean() / 1e6, 2),
            "max_million": round(deals.max() / 1e6, 2),
        }

    # 升跌統計
    if "advanced" in df.columns and "declined" in df.columns:
        adv = pd.to_numeric(df["advanced"], errors="coerce")
        dec = pd.to_numeric(df["declined"], errors="coerce")
        # 升跌比
        ad_ratio = adv / dec.replace(0, np.nan)
        bull_days = (adv > dec).sum()
        bear_days = (dec > adv).sum()
        stats["breadth"] = {
            "bull_days": int(bull_days),
            "bear_days": int(bear_days),
            "avg_ad_ratio": round(ad_ratio.mean(), 3),
            "best_breadth_date": df.loc[ad_ratio.idxmax(), "date"] if not ad_ratio.empty else None,
            "best_breadth_ratio": round(ad_ratio.max(), 3) if not ad_ratio.empty else None,
        }

    # 恆指相關（如果 market_summary 有）
    for hsi_col in ["hsi_close", "afternoon_close"]:
        if hsi_col in df.columns:
            hsi = pd.to_numeric(df[hsi_col], errors="coerce").dropna()
            if len(hsi) > 1:
                returns = hsi.pct_change().dropna()
                stats["hsi"] = {
                    "start": round(float(hsi.iloc[0]), 2),
                    "end": round(float(hsi.iloc[-1]), 2),
                    "period_return_pct": round((float(hsi.iloc[-1]) / float(hsi.iloc[0]) - 1) * 100, 2),
                    "max": round(float(hsi.max()), 2),
                    "min": round(float(hsi.min()), 2),
                    "volatility_daily_pct": round(float(returns.std() * 100), 3),
                    "volatility_annualized_pct": round(float(returns.std() * np.sqrt(252) * 100), 2),
                    "sharpe_approx": round(
                        float(returns.mean() / returns.std() * np.sqrt(252)), 3
                    ) if returns.std() > 0 else 0,
                }
            break

    return stats


def analyze_indices(df: pd.DataFrame) -> dict:
    """各指數統計"""
    df = df.copy()
    for col in ["morning_close", "afternoon_close", "prev_close", "change", "change_pct"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    result = {}
    for code in df["code"].unique() if "code" in df.columns else []:
        sub = df[df["code"] == code].sort_values("date")
        close = sub["afternoon_close"].dropna()
        if len(close) < 2:
            continue
        returns = close.pct_change().dropna()
        result[code] = {
            "name": sub.iloc[0].get("name_cn", code),
            "days": len(sub),
            "start": round(float(close.iloc[0]), 2),
            "end": round(float(close.iloc[-1]), 2),
            "return_pct": round((float(close.iloc[-1]) / float(close.iloc[0]) - 1) * 100, 2),
            "volatility_annual": round(float(returns.std() * np.sqrt(252) * 100), 2) if len(returns) > 0 else 0,
            "correlation_with_volume": None,  # TODO if needed
        }

    return result


def analyze_top_stocks(df: pd.DataFrame, category: str) -> dict:
    """十大活躍股分析"""
    df = df.copy()
    if "turnover_hkd" in df.columns:
        df["turnover_hkd"] = pd.to_numeric(df["turnover_hkd"], errors="coerce")

    # 出現頻率（哪些股票最常出現在十大）
    freq = df.groupby(["code", "name_cn"]).size().reset_index(name="appearances")
    freq = freq.sort_values("appearances", ascending=False)

    # 平均成交額
    if "turnover_hkd" in df.columns:
        avg_tov = df.groupby(["code", "name_cn"])["turnover_hkd"].mean().reset_index()
        avg_tov = avg_tov.sort_values("turnover_hkd", ascending=False)

    result = {
        "category": category,
        "total_records": len(df),
        "unique_stocks": df["code"].nunique() if "code" in df.columns else 0,
        "most_frequent": freq.head(5).to_dict("records"),
        "highest_avg_turnover": avg_tov.head(5).to_dict("records") if "turnover_hkd" in df.columns else [],
    }

    # 格式化大數字
    for item in result["highest_avg_turnover"]:
        if "turnover_hkd" in item and item["turnover_hkd"]:
            item["turnover_hkd"] = round(item["turnover_hkd"] / 1e9, 2)  # 億港元

    return result


def generate_statistics(excel_path: str, output: str = "data/hkex_statistics.json"):
    """生成完整統計分析報告"""
    sheets = load_excel(excel_path)
    report = {"generated_at": pd.Timestamp.now().isoformat(), "source": excel_path}

    if "市場概要" in sheets:
        report["market_summary"] = analyze_market_summary(sheets["市場概要"])

    if "各指數" in sheets:
        report["indices"] = analyze_indices(sheets["各指數"])

    if "十大成交金額" in sheets:
        report["top_dollars"] = analyze_top_stocks(sheets["十大成交金額"], "成交金額")

    if "十大成交股數" in sheets:
        report["top_shares"] = analyze_top_stocks(sheets["十大成交股數"], "成交股數")

    # 輸出 JSON
    os.makedirs(os.path.dirname(output) or ".", exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)

    # 打印摘要
    print("\n" + "=" * 60)
    print("📊 HKEX 統計分析報告")
    print("=" * 60)

    ms = report.get("market_summary", {})
    print(f"\n📅 期間: {ms.get('period', 'N/A')}（{ms.get('trading_days', 0)} 個交易日）")

    tov = ms.get("turnover", {})
    print(f"\n💰 成交額（億港元）:")
    print(f"   平均: {tov.get('mean_billion', 'N/A')} | 中位數: {tov.get('median_billion', 'N/A')}")
    print(f"   最高: {tov.get('max_billion', 'N/A')} ({tov.get('max_date', '')})")
    print(f"   最低: {tov.get('min_billion', 'N/A')} ({tov.get('min_date', '')})")
    print(f"   標準差: {tov.get('std_billion', 'N/A')}")

    br = ms.get("breadth", {})
    print(f"\n📈 市場廣度:")
    print(f"   升市天數: {br.get('bull_days', 0)} | 跌市天數: {br.get('bear_days', 0)}")
    print(f"   平均升跌比: {br.get('avg_ad_ratio', 'N/A')}")

    hsi = ms.get("hsi", {})
    if hsi:
        print(f"\n📊 恆生指數:")
        print(f"   期初: {hsi.get('start', 'N/A')} | 期末: {hsi.get('end', 'N/A')}")
        print(f"   期間回報: {hsi.get('period_return_pct', 'N/A')}%")
        print(f"   日波動率: {hsi.get('volatility_daily_pct', 'N/A')}%")
        print(f"   年化波動率: {hsi.get('volatility_annualized_pct', 'N/A')}%")
        print(f"   夏普比率(近似): {hsi.get('sharpe_approx', 'N/A')}")

    td = report.get("top_dollars", {})
    print(f"\n🏆 十大成交金額股（出現最頻密）:")
    for s in td.get("most_frequent", [])[:5]:
        print(f"   {s.get('code', '')} {s.get('name_cn', '')}: {s.get('appearances', 0)} 次")

    print(f"\n💾 報告已保存: {output}")
    return report


def main():
    parser = argparse.ArgumentParser(description="HKEX 數據統計分析")
    parser.add_argument("--excel", type=str, default="data/hkex_may_jun.xlsx")
    parser.add_argument("--output", type=str, default="data/hkex_statistics.json")
    args = parser.parse_args()

    if not os.path.exists(args.excel):
        print(f"❌ {args.excel} 不存在。先運行 hkex_full_crawler.py")
        sys.exit(1)

    generate_statistics(args.excel, args.output)


if __name__ == "__main__":
    main()
