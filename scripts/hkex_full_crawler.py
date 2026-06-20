#!/usr/bin/env python3
"""
HKEX 日報表（主板）完整數據爬蟲 + Excel 分類導出
數據來源: https://www.hkex.com.hk/chi/stat/smstat/dayquot/d{YYMMDD}c.htm

 提取完整數據：
  1. 市場概要（成交股數/金額/宗數、升跌股數）
  2. 各指數（恆指/國企/上證/深證：上午收市、下午收市、上次、變幅、變幅率）
  3. 十大成交金額最多股票（10 MOST ACTIVES DOLLARS）
  4. 十大成交股數最多股票（10 MOST ACTIVES SHARES）

導出 Excel，每個分類一個 sheet。

用法:
    python scripts/hkex_full_crawler.py --start 20260501 --end 20260619
    python scripts/hkex_full_crawler.py --date 20260618
    python scripts/hkex_full_crawler.py --start 20260501 --end 20260619 --excel data/raw_hkex/hkex_full.xlsx
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

HKEX_BASE = "https://www.hkex.com.hk/chi/stat/smstat/dayquot"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


def build_url(date_str: str) -> str:
    yy = date_str[2:4]
    return f"{HKEX_BASE}/d{yy}{date_str[4:6]}{date_str[6:8]}c.htm"


def fetch_page(date_str: str) -> str:
    url = build_url(date_str)
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
        if r.status_code == 404:
            return ""
        r.raise_for_status()
        r.encoding = "big5"
        return r.text
    except requests.RequestException:
        return ""


def parse_num(text: str) -> float | None:
    """提取數字（去掉逗號）"""
    m = re.search(r"[\d,]+\.?\d*", text.replace(",", ""))
    if not m:
        return None
    try:
        return float(m.group())
    except ValueError:
        return None


def parse_full_daily(html: str, date_str: str) -> dict | None:
    """解析完整的 HKEX 日報表"""
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")
    lines = [l.strip() for l in soup.get_text(separator="\n").split("\n") if l.strip()]
    full_text = "\n".join(lines)
    date_iso = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"

    result = {
        "date": date_iso,
        "market_summary": {},
        "indices": [],
        "top_dollars": [],
        "top_shares": [],
    }

    # === 1. 市場概要 ===
    ms = result["market_summary"]
    ms["date"] = date_iso

    for line in lines:
        if "成交股份" in line and "Sec. Traded" in line:
            m = re.search(r"Traded:\s*([\d,]+)", line)
            if m:
                ms["securities_traded"] = int(m.group(1).replace(",", ""))
        elif "上升股份" in line or "Advanced" in line:
            m = re.search(r":\s*([\d,]+)", line)
            if m:
                ms["advanced"] = int(m.group(1).replace(",", ""))
        elif "下降股份" in line or "Declined" in line:
            m = re.search(r":\s*([\d,]+)", line)
            if m:
                ms["declined"] = int(m.group(1).replace(",", ""))
        elif "無變股份" in line or "Unchanged" in line:
            m = re.search(r":\s*([\d,]+)", line)
            if m:
                ms["unchanged"] = int(m.group(1).replace(",", ""))
        elif "金額(HK$)" in line:
            ms["turnover_hkd"] = parse_num(line.split(":")[-1])
        elif "股數(Shares)" in line:
            ms["total_shares"] = parse_num(line.split(":")[-1])
        elif "宗數(Deals)" in line:
            ms["deals"] = parse_num(line.split(":")[-1])

    # === 2. 各指數 ===
    # 格式: 恆生指數 HANG SENG INDEX  23900.01 23924.81 24312.16  -387.35  -1.593
    # 5個數字 = 上午收市/下午收市/上次收市/變幅/變幅率
    index_patterns = [
        ("恆生指數", "HSI", "HANG SENG INDEX"),
        ("企業指數", "HSCEI", "ENTERPRISES INDEX"),
    ]

    for cn_name, code, en_name in index_patterns:
        pattern = rf"{cn_name}\s+{en_name}\s+([\d,.]+)\s+([\d,.]+)\s+([\d,.]+)\s+(-?[\d,.]+)\s+(-?[\d,.]+)"
        m = re.search(pattern, full_text)
        if m:
            def clean(x):
                return float(x.replace(",", ""))
            result["indices"].append({
                "date": date_iso,
                "name_cn": cn_name,
                "code": code,
                "morning_close": clean(m.group(1)),   # 上午收市
                "afternoon_close": clean(m.group(2)),  # 下午收市
                "prev_close": clean(m.group(3)),       # 上次收市
                "change": clean(m.group(4)),           # 變幅
                "change_pct": clean(m.group(5)),       # 變幅率
            })

    # 港股通大型股指數 / 上證 / 深證（可能有額外指數）
    # 嘗試匹配其他指數行（格式：名稱 + 5個數字）
    for line in lines:
        if any(kw in line for kw in ["大型股指數", "指數 INDEX", "易所大型股"]):
            m = re.search(r"([\d,.]+)\s+([\d,.]+)\s+([\d,.]+)\s+(-?[\d,.]+)\s+(-?[\d,.]+)", line)
            if m and "恆生" not in line and "企業" not in line:
                def clean(x):
                    return float(x.replace(",", ""))
                result["indices"].append({
                    "date": date_iso,
                    "name_cn": "交易所大型股指數",
                    "code": "INDEX",
                    "morning_close": clean(m.group(1)),
                    "afternoon_close": clean(m.group(2)),
                    "prev_close": clean(m.group(3)),
                    "change": clean(m.group(4)),
                    "change_pct": clean(m.group(5)),
                })

    # === 3. 十大成交金額最多股票 ===
    in_section = None
    for line in lines:
        if "十大成交金額最多" in line or "10 MOST ACTIVES (DOLLARS)" in line:
            in_section = "dollars"
            continue
        elif "十大成交股數最多" in line or "10 MOST ACTIVES (SHARES)" in line:
            in_section = "shares"
            continue
        elif "代號" in line and "NAME OF STOCK" in line:
            continue  # header row

        if in_section and line and line[0].isdigit():
            # 格式: 9988 BABA-W  阿里巴巴 HKD  16,645,497,803  160,333,163  106.00  102.40
            m = re.match(
                r"(\d{1,5})\s+(\S+)\s+(.+?)\s+HKD\s+([\d,]+)\s+([\d,]+)\s+([\d.]+)\s+([\d.]+)",
                line,
            )
            if m:
                stock = {
                    "date": date_iso,
                    "rank": len(result[f"top_{in_section}"]) + 1,
                    "code": m.group(1),
                    "name_en": m.group(2).strip(),
                    "name_cn": m.group(3).strip(),
                    "value1": int(m.group(4).replace(",", "")),  # 成交金額 or 成交股數
                    "value2": int(m.group(5).replace(",", "")),  # 成交股數 or 成交金額
                    "high": float(m.group(6)),
                    "low": float(m.group(7)),
                }
                if in_section == "dollars":
                    stock["turnover_hkd"] = stock.pop("value1")
                    stock["volume_shares"] = stock.pop("value2")
                else:
                    stock["volume_shares"] = stock.pop("value1")
                    stock["turnover_hkd"] = stock.pop("value2")
                result[f"top_{in_section}"].append(stock)

            # 如果進入所有主板證券區域，停止
            if len(result[f"top_{in_section}"]) >= 10:
                in_section = None

    # === 5. 十大成交股數 = 牛熊證散戶情緒指標 ===
    # RC = 牛證(Callable Bull), RP = 熊證(Callable Bear)
    bull_shares = 0
    bear_shares = 0
    bull_value = 0
    bear_value = 0
    cbbc_records = []

    # 找十大成交股數區段
    sc_start = None
    for i, line in enumerate(lines):
        if "十大成交股數" in line or "10 MOST ACTIVES (SHARES)" in line:
            sc_start = i + 1
            break

    if sc_start:
        for line in lines[sc_start : sc_start + 15]:
            if "HKD" not in line:
                continue
            m = re.match(
                r"(\d{5})\s+(\S+)\s+(\S+)\s+(.+?)\s+HKD\s+([\d,]+)\s+([\d,]+)\s+([\d.]+)\s+([\d.]+)",
                line,
            )
            if not m:
                continue

            rc_code = m.group(3)
            shares = int(m.group(5).replace(",", ""))
            turnover = int(m.group(6).replace(",", ""))

            # RC = 牛證, RP = 熊證
            is_bull = rc_code.startswith("RC")
            is_bear = rc_code.startswith("RP")

            if is_bull:
                bull_shares += shares
                bull_value += turnover
            elif is_bear:
                bear_shares += shares
                bear_value += turnover

            cbbc_records.append({
                "code": m.group(1),
                "direction": "bull" if is_bull else "bear" if is_bear else "?",
                "shares": shares,
                "turnover": turnover,
            })

    total_cbbc_shares = bull_shares + bear_shares
    if total_cbbc_shares > 0:
        bull_pct = bull_shares / total_cbbc_shares * 100
        result["retail_sentiment"] = {
            "date": date_iso,
            "bull_shares": bull_shares,
            "bear_shares": bear_shares,
            "bull_pct": round(bull_pct, 1),
            "bear_pct": round(100 - bull_pct, 1),
            "bull_bear_ratio": round(bull_shares / bear_shares, 2) if bear_shares > 0 else 999,
            "bull_value_hkd": bull_value,
            "bear_value_hkd": bear_value,
            "sentiment_score": round(bull_pct, 1),  # 0-100, 50=中性
            "sentiment_label": (
                "極度貪婪" if bull_pct > 90
                else "偏貪婪" if bull_pct > 70
                else "中性" if bull_pct > 40
                else "偏恐懼" if bull_pct > 20
                else "極度恐懼"
            ),
            "top_cbbc": cbbc_records[:10],
        }

    # === 6. 沽空比率（Short Selling Ratio）===
    # 找「賣空成交-每日報表」區段（第二個出現的，含實際數據）
    short_sell_start = None
    ss_count = 0
    for i, line in enumerate(lines):
        if "賣空成交-每日報表" in line or "SHORT SELL" in line.upper():
            ss_count += 1
            if ss_count >= 2:  # 第二個出現的是數據段
                short_sell_start = i + 3  # 跳過標題行
                break

    top_short = []
    market_short_ratio = None
    if short_sell_start:
        for line in lines[short_sell_start : short_sell_start + 15]:
            # 格式: 代號 股票名稱 沽空股數 沽空金額 總成交股數 總成交金額
            m = re.match(
                r"(\d{1,5})\s+(.+?)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)", line
            )
            if m:
                short_shares = int(m.group(3).replace(",", ""))
                total_shares = int(m.group(5).replace(",", ""))
                ratio = short_shares / total_shares * 100 if total_shares > 0 else 0
                top_short.append({
                    "code": m.group(1),
                    "name": m.group(2).strip()[:15],
                    "short_shares": short_shares,
                    "short_value": int(m.group(4).replace(",", "")),
                    "short_ratio_pct": round(ratio, 1),
                })

            # 總計行
            if "總計" in line or "TOTAL" in line.upper():
                m2 = re.match(r"總計\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)", line)
                if m2:
                    ts = int(m2.group(1).replace(",", ""))
                    ta = int(m2.group(3).replace(",", ""))
                    market_short_ratio = round(ts / ta * 100, 2) if ta > 0 else 0

    if top_short or market_short_ratio:
        result["short_selling"] = {
            "date": date_iso,
            "market_short_ratio": market_short_ratio,
            "top_short_stocks": top_short[:10],
        }

    # 檢查至少有市場概要數據
    if not ms.get("turnover_hkd") and not ms.get("deals"):
        return None

    return result


def crawl_date_range(start: str, end: str, delay: float = 0.3) -> list[dict]:
    """抓取日期範圍，跳過假期/週末"""
    start_dt = datetime.strptime(start, "%Y%m%d")
    end_dt = datetime.strptime(end, "%Y%m%d")
    records = []
    skipped = 0

    print(f"抓取 {start} 至 {end}")
    current = start_dt
    while current <= end_dt:
        date_str = current.strftime("%Y%m%d")
        date_iso = current.strftime("%Y-%m-%d")

        if current.weekday() >= 5:
            current += timedelta(days=1)
            continue

        print(f"  {date_iso} ...", end=" ")
        html = fetch_page(date_str)
        if html:
            record = parse_full_daily(html, date_str)
            if record:
                records.append(record)
                ms = record["market_summary"]
                print(f"✓ 成交額={ms.get('turnover_hkd','N/A')}, 十大金額={len(record['top_dollars'])}隻")
            else:
                print("— 解析失敗")
        else:
            print("— 假期/無數據")

        current += timedelta(days=1)
        time.sleep(delay)

    print(f"\n✅ 完成！{len(records)} 個交易日")
    return records


def export_excel(records: list[dict], output: str):
    """導出分類 Excel（多 sheet）"""
    if not records:
        print("⚠ 無數據可導出")
        return

    os.makedirs(os.path.dirname(output) or ".", exist_ok=True)

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        # Sheet 1: 市場概要
        ms_df = pd.DataFrame([r["market_summary"] for r in records])
        ms_df = ms_df.sort_values("date", ascending=False)
        ms_df.to_excel(writer, sheet_name="市場概要", index=False)

        # Sheet 2: 各指數
        idx_list = []
        for r in records:
            idx_list.extend(r["indices"])
        idx_df = pd.DataFrame(idx_list)
        if not idx_df.empty:
            idx_df.to_excel(writer, sheet_name="各指數", index=False)

        # Sheet 3: 十大成交金額
        td_list = []
        for r in records:
            td_list.extend(r["top_dollars"])
        td_df = pd.DataFrame(td_list)
        if not td_df.empty:
            td_df.to_excel(writer, sheet_name="十大成交金額", index=False)

        # Sheet 4: 十大成交股數（牛熊證）
        ts_list = []
        for r in records:
            ts_list.extend(r["top_shares"])
        ts_df = pd.DataFrame(ts_list)
        if not ts_df.empty:
            ts_df.to_excel(writer, sheet_name="十大成交股數", index=False)

        # Sheet 5: 散戶牛熊情緒指標
        sentiment_list = []
        for r in records:
            if "retail_sentiment" in r:
                rs = r["retail_sentiment"]
                sentiment_list.append({
                    "date": rs["date"],
                    "bull_shares": rs["bull_shares"],
                    "bear_shares": rs["bear_shares"],
                    "bull_pct": rs["bull_pct"],
                    "bear_pct": rs["bear_pct"],
                    "bull_bear_ratio": rs["bull_bear_ratio"],
                    "bull_value_hkd": rs["bull_value_hkd"],
                    "bear_value_hkd": rs["bear_value_hkd"],
                    "sentiment_score": rs["sentiment_score"],
                    "sentiment_label": rs["sentiment_label"],
                })
        sent_df = pd.DataFrame(sentiment_list)
        if not sent_df.empty:
            sent_df.to_excel(writer, sheet_name="散戶牛熊情緒", index=False)

        # Sheet 6: 沽空比率
        short_list = []
        market_short_list = []
        for r in records:
            if "short_selling" in r:
                ss = r["short_selling"]
                market_short_list.append({
                    "date": ss["date"],
                    "market_short_ratio": ss.get("market_short_ratio"),
                })
                for stock in ss.get("top_short_stocks", []):
                    short_list.append({**stock, "date": ss["date"]})
        market_ss_df = pd.DataFrame(market_short_list)
        stock_ss_df = pd.DataFrame(short_list)
        if not market_ss_df.empty:
            market_ss_df.to_excel(writer, sheet_name="全市場沽空比率", index=False)
        if not stock_ss_df.empty:
            stock_ss_df.to_excel(writer, sheet_name="十大沽空股票", index=False)

    sent_count = len(sent_df) if 'sent_df' in dir() and not sent_df.empty else 0
    print(f"✅ Excel 已導出: {output}")
    print(f"   Sheets: 市場概要({len(ms_df)}), 各指數({len(idx_df)}), 十大金額({len(td_df)}), 十大股數({len(ts_df)}), 散戶情緒({sent_count})")


def main():
    parser = argparse.ArgumentParser(description="HKEX 日報表完整爬蟲 + Excel 導出")
    parser.add_argument("--date", type=str, help="單日 (yyyymmdd)")
    parser.add_argument("--start", type=str, help="起始日期")
    parser.add_argument("--end", type=str, help="結束日期")
    parser.add_argument("--excel", type=str, default="data/raw_hkex/hkex_full.xlsx", help="Excel 輸出路徑")
    args = parser.parse_args()

    today = datetime.now().strftime("%Y%m%d")

    if args.date:
        print(f"抓取 {args.date} ...")
        html = fetch_page(args.date)
        record = parse_full_daily(html, args.date) if html else None
        if record:
            export_excel([record], args.excel)
        else:
            print("❌ 無數據")
    elif args.start and args.end:
        records = crawl_date_range(args.start, args.end)
        if records:
            export_excel(records, args.excel)
    else:
        print(f"抓取今日 {today} ...")
        html = fetch_page(today)
        record = parse_full_daily(html, today) if html else None
        if record:
            export_excel([record], args.excel)
        else:
            print("❌ 無數據")


if __name__ == "__main__":
    main()
