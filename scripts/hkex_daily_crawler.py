#!/usr/bin/env python3
"""
HKEX 每日成交統計爬蟲
數據來源: https://www.hkex.com.hk/chi/stat/smstat/dayquot/d{YYMMDD}c.htm

 HKEX 日報表（主板）提供：
  - 成交股份/金額/宗數
  - 上升/下降/無變股份數
  - 恆生指數 / 國企指數（開/高/低/收/變動）
  - 十大成交金額/股數最多股票
  - 所有主板證券報價

用法:
    python scripts/hkex_daily_crawler.py                          # 今日
    python scripts/hkex_daily_crawler.py --date 20260619          # 指定日期
    python scripts/hkex_daily_crawler.py --start 20260601 --end 20260619
    python scripts/hkex_daily_crawler.py --output data/hkex_daily.csv
"""

import argparse
import os
import re
import time
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

# HKEX 日報表 URL pattern: d{YYMMDD}c.htm (c = 中文版)
HKEX_BASE = "https://www.hkex.com.hk/chi/stat/smstat/dayquot"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
}


def build_url(date_str: str) -> str:
    """date_str yyyymmdd -> URL d{YYMMDD}c.htm"""
    yy = date_str[2:4]
    mm = date_str[4:6]
    dd = date_str[6:8]
    return f"{HKEX_BASE}/d{yy}{mm}{dd}c.htm"


def fetch_page(date_str: str) -> str:
    """抓取 HKEX 日報表 HTML（Big5 編碼）"""
    url = build_url(date_str)
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
        if r.status_code == 404:
            return ""  # 假期/週末沒有數據
        r.raise_for_status()
        r.encoding = "big5"  # HKEX 中文頁面用 Big5
        return r.text
    except requests.RequestException:
        return ""


def parse_daily(html: str, date_str: str) -> dict | None:
    """
    解析 HKEX 日報表，提取成交統計 + 恆指 + 十大活躍股。

    數據格式（實測）:
      成交股份 Sec. Traded: 8446
      上升股份 Advanced   : 5124
      下降股份 Declined   : 7173
      無變股份 Unchanged  : 3477
      金額(HK$):    358,714,541,610
      股數(Shares): 330,320,857,390
      宗數(Deals):        5,049,735
      恆生指數 HANG SENG INDEX     23900.01 23924.81 24312.16   -387.35   -1.593
    """
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator="\n")
    date_iso = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"

    def find_num(pattern: str) -> int | float | None:
        m = re.search(pattern, text)
        if not m:
            return None
        raw = m.group(1).replace(",", "").strip()
        if not raw or raw == "-":
            return None
        try:
            return float(raw) if "." in raw else int(raw)
        except ValueError:
            return None

    record = {
        "date": date_iso,
        "trading_volume": find_num(r"成交股份.*?:\s*([\d,]+)"),
        "advanced_stocks": find_num(r"上升股份.*?:\s*([\d,]+)"),
        "declined_stocks": find_num(r"下降股份.*?:\s*([\d,]+)"),
        "unchanged_stocks": find_num(r"無變股份.*?:\s*([\d,]+)"),
        "turnover_hkd": find_num(r"金額\(HK\$\):\s*([\d,]+)"),
        "total_shares": find_num(r"股數\(Shares\):\s*([\d,]+)"),
        "deals": find_num(r"宗數\(Deals\):\s*([\d,]+)"),
    }

    # 恆生指數: "恆生指數 HANG SENG INDEX  open  high  close  change  change%"
    # 實測: 23900.01 23924.81 24312.16   -387.35   -1.593
    hsi_match = re.search(
        r"恆生指數.*?INDEX\s+([\d,.]+)\s+([\d,.]+)\s+([\d,.]+)\s+(-?[\d,.]+)\s+(-?[\d,.]+)",
        text,
    )
    if hsi_match:
        def clean(x):
            return float(x.replace(",", ""))
        record["hsi_open"] = clean(hsi_match.group(1))
        record["hsi_close"] = clean(hsi_match.group(3))
        record["hsi_change"] = clean(hsi_match.group(4))
        record["hsi_change_pct"] = clean(hsi_match.group(5))
        # morning/afternoon close mapping
        record["morning_close"] = record["hsi_open"]
        record["afternoon_close"] = record["hsi_close"]
        record["change_value"] = record["hsi_change"]
        record["change_percent"] = record["hsi_change_pct"]

    # 國企指數（H 股指數）
    hcei_match = re.search(
        r"企業指數.*?INDEX\s+([\d,.]+)\s+([\d,.]+)\s+([\d,.]+)\s+(-?[\d,.]+)\s+(-?[\d,.]+)",
        text,
    )
    if hcei_match:
        def clean(x):
            return float(x.replace(",", ""))
        record["hcei_close"] = clean(hcei_match.group(3))
        record["hcei_change_pct"] = clean(hcei_match.group(5))

    # 十大成交金額最多股票
    top_active = []
    in_top = False
    for line in text.split("\n"):
        if "十大成交金額最多" in line:
            in_top = True
            continue
        if in_top:
            if "十大成交股數最多" in line or "所有主板" in line:
                break
            # 格式: "9988 BABA-W  阿里巴巴 HKD  16,645,497,803  160,333,163  106.00  102.40"
            m = re.match(
                r"(\d{4,5})\s+(\S+)\s+(.+?)\s+HKD\s+([\d,]+)\s+([\d,]+)\s+([\d.]+)\s+([\d.]+)",
                line.strip(),
            )
            if m:
                top_active.append({
                    "code": m.group(1),
                    "name_en": m.group(2),
                    "name_cn": m.group(3).strip(),
                    "turnover": int(m.group(4).replace(",", "")),
                    "volume": int(m.group(5).replace(",", "")),
                    "high": float(m.group(6)),
                    "low": float(m.group(7)),
                })
    record["top_active"] = top_active

    # 驗證有有效數據
    has_data = any(
        v is not None for k, v in record.items() if k not in ("date", "top_active")
    )
    return record if has_data else None


def crawl_single_date(date_str: str) -> dict | None:
    """抓取單日數據"""
    html = fetch_page(date_str)
    return parse_daily(html, date_str) if html else None


def crawl_date_range(
    start: str, end: str, output: str = "data/hkex_daily.csv", delay: float = 0.5
) -> pd.DataFrame:
    """抓取日期範圍，增量更新 CSV"""
    start_dt = datetime.strptime(start, "%Y%m%d")
    end_dt = datetime.strptime(end, "%Y%m%d")

    existing_dates = set()
    existing_records = []
    if os.path.exists(output):
        old = pd.read_csv(output)
        existing_dates = set(old["date"].tolist())
        existing_records = old.to_dict("records")
        print(f"已有 {len(existing_dates)} 條記錄")

    new_records = []
    current = start_dt
    skipped = 0

    print(f"抓取 {start} 至 {end}")

    while current <= end_dt:
        date_str = current.strftime("%Y%m%d")
        date_iso = current.strftime("%Y-%m-%d")

        if current.weekday() >= 5 or date_iso in existing_dates:
            skipped += 1
            current += timedelta(days=1)
            continue

        print(f"  {date_iso} ...", end=" ")
        rec = crawl_single_date(date_str)
        if rec:
            new_records.append(rec)
            print(f"✓ 成交額={rec.get('turnover_hkd', 'N/A')}")
        else:
            print("— 假期")

        current += timedelta(days=1)
        time.sleep(delay)

    # 合併
    all_records = existing_records + [
        {k: v for k, v in r.items() if k != "top_active"} for r in new_records
    ]
    df = pd.DataFrame(all_records)
    if not df.empty:
        df = df.sort_values("date").drop_duplicates(subset=["date"])
        os.makedirs(os.path.dirname(output) or ".", exist_ok=True)
        df.to_csv(output, index=False, encoding="utf-8-sig")
        print(f"\n✅ {len(df)} 條記錄 (新+{len(new_records)}), 跳過 {skipped}")
        print(f"   輸出: {output}")

    return df


def main():
    parser = argparse.ArgumentParser(description="HKEX 每日成交統計爬蟲")
    parser.add_argument("--date", type=str, help="單日 (yyyymmdd)")
    parser.add_argument("--start", type=str, help="起始日期")
    parser.add_argument("--end", type=str, help="結束日期")
    parser.add_argument("--output", type=str, default="data/hkex_daily.csv")
    parser.add_argument("--delay", type=float, default=0.5)
    args = parser.parse_args()

    today = datetime.now().strftime("%Y%m%d")

    if args.date:
        print(f"抓取 {args.date} ...")
        rec = crawl_single_date(args.date)
        if rec:
            for k, v in rec.items():
                if k == "top_active":
                    print(f"  十大成交股 ({len(v)} 隻):")
                    for s in v[:5]:
                        print(f"    {s['code']} {s['name_cn']} 成交額={s['turnover']:,}")
                else:
                    print(f"  {k}: {v}")
        else:
            print("❌ 無數據（假期？）")
    elif args.start and args.end:
        crawl_date_range(args.start, args.end, args.output, args.delay)
    else:
        print(f"抓取今日 {today} ...")
        rec = crawl_single_date(today)
        if rec:
            print(f"✅ 恆指={rec.get('hsi_close')}, 成交額={rec.get('turnover_hkd')}")
        else:
            print("❌ 今日無數據（假期/週末）")


if __name__ == "__main__":
    main()
