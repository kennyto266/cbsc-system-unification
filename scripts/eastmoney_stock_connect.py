#!/usr/bin/env python3
"""
東方財富 南北水歷史數據爬蟲（12年完整數據）
數據來源: https://data.eastmoney.com/ (RPT_MUTUAL_DEAL_HISTORY API)

 數據範圍: 2014-11-17（滬港通首日）至今
 約 15,000+ 條記錄

用法:
    python scripts/eastmoney_stock_connect.py                    # 全部歷史
    python scripts/eastmoney_stock_connect.py --start 20200101   # 從指定日期
    python scripts/eastmoney_stock_connect.py --output data/stock_connect/sc_full.csv
"""

import argparse
import json
import os
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

API_URL = "https://datacenter-web.eastmoney.com/api/data/v1/get"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://data.eastmoney.com/",
}
PAGE_SIZE = 500  # 每頁 500 條（API 最大值，大幅減少頁數）


def fetch_page(page: int, page_size: int = PAGE_SIZE) -> list:
    """抓取一頁數據"""
    params = {
        "reportName": "RPT_MUTUAL_DEAL_HISTORY",
        "columns": "ALL",
        "source": "WEB",
        "sortColumns": "TRADE_DATE",
        "sortTypes": "1",  # 正序（舊→新）
        "pageNumber": page,
        "pageSize": page_size,
    }
    try:
        r = requests.get(API_URL, params=params, headers=HEADERS, timeout=20)
        r.raise_for_status()
        data = r.json()
        result = data.get("result", {})
        return result.get("data", []) or []
    except Exception as e:
        print(f"  ⚠ 頁 {page} 失敗: {e}")
        return []


def parse_record(rec: dict) -> dict:
    """解析一條記錄"""
    # MUTUAL_TYPE: '001'=滬股通北向, '002'=滬港通南向, '003'=深股通北向, '004'=深港通南向, '005'=合計
    date_str = rec.get("TRADE_DATE", "")[:10]
    return {
        "date": date_str,
        "mutual_type": rec.get("MUTUAL_TYPE", ""),
        "type_name": {
            "001": "北向_滬股通",
            "002": "南向_港股通滬",
            "003": "北向_深股通",
            "004": "南向_港股通深",
            "005": "合計",
        }.get(rec.get("MUTUAL_TYPE", ""), rec.get("MUTUAL_TYPE", "")),
        "net_buy": _num(rec.get("NET_DEAL_AMT")),       # 淨買入（百萬）
        "buy": _num(rec.get("BUY_AMT")),                 # 買入
        "sell": _num(rec.get("SELL_AMT")),               # 賣出
        "total": _num(rec.get("DEAL_AMT")),               # 成交總額
        "fund_inflow": _num(rec.get("FUND_INFLOW")),      # 資金流入
        "quota_balance": _num(rec.get("QUOTA_BALANCE")),   # 額度餘額
        "accum_buy": _num(rec.get("ACCUM_DEAL_AMT")),      # 累計成交
    }


def _num(val) -> float | None:
    if val is None or val == "":
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def crawl_all(output: str = "data/stock_connect/sc_full.csv", max_pages: int = None):
    """抓取全部歷史數據"""
    print("📥 東方財富 南北水歷史數據爬蟲")
    print(f"   數據源: {API_URL}")

    # 先拿第1頁確認總頁數
    first_page = fetch_page(1)
    if not first_page:
        print("❌ 無法獲取數據")
        return

    # 從 response 拿總頁數
    params = {
        "reportName": "RPT_MUTUAL_DEAL_HISTORY",
        "columns": "ALL", "source": "WEB",
        "sortColumns": "TRADE_DATE", "sortTypes": "1",
        "pageNumber": 1, "pageSize": 1,
    }
    r = requests.get(API_URL, params=params, headers=HEADERS, timeout=10)
    total = r.json().get("result", {})
    total_pages = total.get("pages", 200)
    total_count = total.get("count", 0)
    if max_pages:
        total_pages = min(total_pages, max_pages)

    print(f"   總記錄: {total_count} 條, {total_pages} 頁")
    print(f"   範圍: {first_page[0].get('TRADE_DATE','?')[:10]} 至 ...")
    print()

    all_records = []
    # 增量寫入：每 10 頁存一次
    os.makedirs(os.path.dirname(output) or ".", exist_ok=True)

    for page in range(1, total_pages + 1):
        data = fetch_page(page) if page > 1 else first_page
        if not data:
            print(f"  頁 {page}: 無數據，跳過")
            continue

        for rec in data:
            parsed = parse_record(rec)
            all_records.append(parsed)

        if page % 5 == 0 or page == total_pages:
            print(f"  進度: {page}/{total_pages} 頁 ({len(all_records)} 條)")
            # 增量保存（防止斷線丟失）
            pd.DataFrame(all_records).to_csv(output, index=False, encoding="utf-8-sig")

        time.sleep(0.05)  # 禮貌延遲（500/page 只需 30 頁）

    # 轉 DataFrame
    df = pd.DataFrame(all_records)
    if df.empty:
        print("❌ 無數據")
        return

    df = df.sort_values(["date", "mutual_type"])

    # 輸出
    os.makedirs(os.path.dirname(output) or ".", exist_ok=True)
    df.to_csv(output, index=False, encoding="utf-8-sig")

    print(f"\n✅ 完成！")
    print(f"   總記錄: {len(df)} 條")
    print(f"   日期範圍: {df['date'].min()} 至 {df['date'].max()}")
    print(f"   年份: {df['date'].str[:4].nunique()} 個")
    print(f"   數據類型: {df['type_name'].nunique()} 種")
    print(f"   輸出: {output}")

    # 統計
    print(f"\n📊 各類型記錄數:")
    for tname, count in df["type_name"].value_counts().items():
        print(f"   {tname}: {count} 條")


def main():
    parser = argparse.ArgumentParser(description="東方財富南北水歷史爬蟲")
    parser.add_argument("--output", type=str, default="data/stock_connect/sc_full.csv")
    parser.add_argument("--max-pages", type=int, default=None, help="最大頁數（測試用）")
    args = parser.parse_args()

    crawl_all(args.output, args.max_pages)


if __name__ == "__main__":
    main()
