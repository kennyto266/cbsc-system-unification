#!/usr/bin/env python3
"""
把爬蟲/回測數據導出為 JSON，供 Dashboard 前端讀取。
輸出到 unified-dashboard/public/data/ 目錄。

用法:
    python scripts/export_dashboard_data.py        # 導出全部
    python scripts/export_dashboard_data.py --refresh  # 重新抓取最新數據再導出
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd

# Dashboard public data 目錄
OUTPUT_DIR = Path(__file__).parent.parent / "unified-dashboard" / "public" / "data"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def export_csv_to_json(csv_path: str, json_name: str, transform=None):
    """讀取 CSV，轉為 JSON 寫入 public/data/"""
    if not os.path.exists(csv_path):
        print(f"  ⚠ {csv_path} 不存在，跳過 {json_name}")
        return False
    df = pd.read_csv(csv_path)
    if transform:
        df = transform(df)
    # 替換 NaN/None 為 null（JSON 不支援 NaN）
    records = df.where(pd.notnull(df), None).to_dict("records")
    out = OUTPUT_DIR / json_name
    with open(out, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2, default=str)
    print(f"  ✓ {json_name}: {len(records)} 條記錄")
    return True


def fetch_fresh_data():
    """重新抓取最新數據"""
    print("📥 重新抓取最新數據...")
    scripts = [
        ("HKEX 每日報告", ["python", "scripts/hkex_daily_crawler.py", "--start", "20260601", "--end", "20260619", "--delay", "0.3"]),
        ("南北水資金流向", ["python", "scripts/stock_connect_crawler.py"]),
    ]
    for name, cmd in scripts:
        print(f"  抓取 {name}...")
        subprocess.run(cmd, capture_output=True, text=True)


def export_hkex_daily():
    """HKEX 每日成交統計"""
    def transform(df):
        # 確保數值欄位是數字
        for col in ["turnover_hkd", "total_shares", "deals", "hsi_close", "hsi_change"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        # 按日期降序（最新的在前）
        df = df.sort_values("date", ascending=False)
        return df
    return export_csv_to_json("data/hkex_daily.csv", "hkex_daily.json", transform)


def export_stock_connect():
    """南北水資金流向"""
    return export_csv_to_json("data/stock_connect.csv", "stock_connect.json")


def export_backtest():
    """回測結果"""
    def transform(df):
        ok = df[df.get("status", "ok") == "ok"].copy() if "status" in df.columns else df.copy()
        return ok.sort_values("sharpe", ascending=False) if "sharpe" in ok.columns else ok
    return export_csv_to_json("data/backtest_results.csv", "backtest_results.json", transform)


def export_summary():
    """匯總信息"""
    summary = {"generated_at": pd.Timestamp.now().isoformat()}
    
    # HKEX 最新
    hkex_path = OUTPUT_DIR / "hkex_daily.json"
    if hkex_path.exists():
        data = json.loads(hkex_path.read_text(encoding="utf-8"))
        if data:
            latest = data[0]
            summary["hkex_latest"] = {
                "date": latest.get("date"),
                "hsi_close": latest.get("hsi_close"),
                "turnover_hkd": latest.get("turnover_hkd"),
                "advanced": latest.get("advanced_stocks"),
                "declined": latest.get("declined_stocks"),
            }
    
    # Stock Connect 最新
    sc_path = OUTPUT_DIR / "stock_connect.json"
    if sc_path.exists():
        data = json.loads(sc_path.read_text(encoding="utf-8"))
        if data:
            latest = data[-1]
            summary["stock_connect_latest"] = {
                "date": latest.get("date"),
                "total_mil": latest.get("southbound_total_mil"),
                "net_mil": latest.get("southbound_net_mil"),
            }
    
    with open(OUTPUT_DIR / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"  ✓ summary.json")
    return True


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true", help="先重新抓取數據")
    args = parser.parse_args()

    print(f"導出數據到 {OUTPUT_DIR}")
    
    if args.refresh:
        fetch_fresh_data()
    
    print("\n轉換為 JSON:")
    export_hkex_daily()
    export_stock_connect()
    export_backtest()
    export_summary()
    
    print(f"\n✅ 完成！Dashboard 可讀取 /data/*.json")


if __name__ == "__main__":
    main()
