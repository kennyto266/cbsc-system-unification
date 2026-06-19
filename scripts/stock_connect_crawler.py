#!/usr/bin/env python3
"""
滬港通及深港通（南北水）資金流向爬蟲
數據來源: HKEX Mutual Market
  https://www.hkex.com.hk/chi/csm/script/data_SBSH_Turnover_chi.js  (滬港通 南向)
  https://www.hkex.com.hk/chi/csm/script/data_SBSZ_Turnover_chi.js  (深港通 南向)
  https://www.hkex.com.hk/chi/csm/script/data_NBSH_QuotaUsage_chi.js (滬港通 北向)
  https://www.hkex.com.hk/chi/csm/script/data_NBSZ_QuotaUsage_chi.js (深港通 北向)

 數據結構: JS variable = [ { JSON } ]

用法:
    python scripts/stock_connect_crawler.py                    # 今日
    python scripts/stock_connect_crawler.py --output data/stock_connect.csv
"""

import argparse
import json
import os
import re
import time
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import requests

HKEX_DATA_BASE = "https://www.hkex.com.hk/chi/csm/script"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.hkex.com.hk/Mutual-Market/Stock-Connect?sc_lang=zh-HK",
}

# 四個數據源
SOURCES = {
    "sh_southbound": f"{HKEX_DATA_BASE}/data_SBSH_Turnover_chi.js",  # 港股通(滬) 南向成交
    "sz_southbound": f"{HKEX_DATA_BASE}/data_SBSZ_Turnover_chi.js",  # 港股通(深) 南向成交
    "sh_northbound": f"{HKEX_DATA_BASE}/data_NBSH_QuotaUsage_chi.js",  # 滬股通 北向額度
    "sz_northbound": f"{HKEX_DATA_BASE}/data_NBSZ_QuotaUsage_chi.js",  # 深股通 北向額度
}


def fetch_js_data(url: str) -> list | None:
    """抓取 HKEX JS 數據文件，解析 JSON array"""
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        # JS 格式: varName = [ { ... } ];
        # 提取 = 後面的 JSON array
        text = r.text.strip()
        # 找到第一個 [ 到最後一個 ]
        start = text.find("[")
        end = text.rfind("]")
        if start < 0 or end < 0:
            return None
        json_str = text[start : end + 1]
        # 移除尾部分號
        json_str = json_str.rstrip(";").strip()
        return json.loads(json_str)
    except (requests.RequestException, json.JSONDecodeError) as e:
        print(f"  ⚠ 抓取失敗 {url}: {e}")
        return None


def parse_turnover(data: list, channel: str) -> dict | None:
    """
    解析南向成交數據。

    格式:
    [{ "category": "Southbound", "section": [{ "subtitle": ["成交額", "18/06/2026 (16:10)", {}],
        "item": [["買入及賣出", "HK$90,827 Mil", {}], ["買入", "HK$45,239 Mil", {}], ["賣出", "HK$45,588 Mil", {}]] }] }]
    """
    if not data or not isinstance(data, list):
        return None

    record = {"channel": channel}
    raw_date = None

    for entry in data:
        for section in entry.get("section", []):
            subtitle = section.get("subtitle", [])
            if len(subtitle) >= 2:
                raw_date = subtitle[1]  # e.g. "18/06/2026 (16:10)"

            for item in section.get("item", []):
                if len(item) >= 2:
                    label, value = item[0], item[1]
                    # 解析金額 "HK$90,827 Mil" -> 90827 (百萬)
                    num = parse_money(value)
                    if "買入及賣出" in label or "买入及卖出" in label:
                        record["total_mil"] = num
                    elif "買入" in label or "买入" in label:
                        record["buy_mil"] = num
                    elif "賣出" in label or "卖出" in label:
                        record["sell_mil"] = num
                    # 淨流入 = 買入 - 賣出
                    if "buy_mil" in record and "sell_mil" in record:
                        record["net_buy_mil"] = record["buy_mil"] - record["sell_mil"]

    if raw_date:
        record["update_time"] = raw_date
        # 解析日期 "18/06/2026 (16:10)" -> "2026-06-18"
        m = re.match(r"(\d{2})/(\d{2})/(\d{4})", raw_date)
        if m:
            record["date"] = f"{m.group(3)}-{m.group(2)}-{m.group(1)}"

    return record if "total_mil" in record else None


def parse_quota(data: list, channel: str) -> dict | None:
    """解析北向額度數據"""
    if not data:
        return None
    record = {"channel": channel}
    for entry in data:
        for section in entry.get("section", []):
            subtitle = section.get("subtitle", [])
            if len(subtitle) >= 2:
                record["update_time"] = subtitle[1]
            for item in section.get("item", []):
                if len(item) >= 2:
                    label, value = item[0], item[1]
                    if isinstance(value, str) and ("暫停" in value or "暂停" in value):
                        record["status"] = "暫停"
                    else:
                        record["daily_quota"] = parse_money(str(value))
                        record["status"] = "開放"
    return record if record.get("status") else None


def parse_money(text: str) -> float | None:
    """'HK$90,827 Mil' -> 90827.0"""
    if not isinstance(text, str):
        return None
    m = re.search(r"([\d,]+(?:\.\d+)?)", text)
    if not m:
        return None
    try:
        return float(m.group(1).replace(",", ""))
    except ValueError:
        return None


def crawl_stock_connect() -> dict:
    """抓取全部四個 Stock Connect 數據源"""
    result = {"timestamp": datetime.now().isoformat(), "data": {}}

    for key, url in SOURCES.items():
        data = fetch_js_data(url)
        if data is None:
            continue

        if "southbound" in key:
            channel = "港股通(滬)" if "sh_" in key else "港股通(深)"
            parsed = parse_turnover(data, channel)
            if parsed:
                result["data"][key] = parsed
        elif "northbound" in key:
            channel = "滬股通" if "sh_" in key else "深股通"
            parsed = parse_quota(data, channel)
            if parsed:
                result["data"][key] = parsed

        time.sleep(0.3)

    # 計算南北水總計
    sb_sh = result["data"].get("sh_southbound", {})
    sb_sz = result["data"].get("sz_southbound", {})
    if sb_sh.get("total_mil") and sb_sz.get("total_mil"):
        result["summary"] = {
            "southbound_total_mil": sb_sh["total_mil"] + sb_sz["total_mil"],
            "southbound_buy_mil": sb_sh.get("buy_mil", 0) + sb_sz.get("buy_mil", 0),
            "southbound_sell_mil": sb_sh.get("sell_mil", 0) + sb_sz.get("sell_mil", 0),
            "southbound_net_mil": sb_sh.get("net_buy_mil", 0) + sb_sz.get("net_buy_mil", 0),
            "date": sb_sh.get("date", ""),
        }

    return result


def save_to_csv(result: dict, output: str = "data/stock_connect.csv"):
    """增量保存到 CSV"""
    summary = result.get("summary", {})
    if not summary.get("date"):
        print("⚠ 無有效數據")
        return

    record = {
        "date": summary["date"],
        "southbound_total_mil": summary.get("southbound_total_mil"),
        "southbound_buy_mil": summary.get("southbound_buy_mil"),
        "southbound_sell_mil": summary.get("southbound_sell_mil"),
        "southbound_net_mil": summary.get("southbound_net_mil"),
        "sh_southbound_mil": result["data"].get("sh_southbound", {}).get("total_mil"),
        "sz_southbound_mil": result["data"].get("sz_southbound", {}).get("total_mil"),
    }

    # 增量更新
    if os.path.exists(output):
        df = pd.read_csv(output)
        df = df[df["date"] != record["date"]]
        df = pd.concat([df, pd.DataFrame([record])], ignore_index=True)
    else:
        df = pd.DataFrame([record])

    df = df.sort_values("date").drop_duplicates(subset=["date"])
    os.makedirs(os.path.dirname(output) or ".", exist_ok=True)
    df.to_csv(output, index=False, encoding="utf-8-sig")
    print(f"✅ 已保存到 {output} ({len(df)} 條記錄)")


def fetch_historical_daily(date_str: str) -> dict | None:
    """
    抓取歷史日期的南北水數據。
    URL: https://www.hkex.com.hk/chi/csm/DailyStat/data_tab_daily_{YYYYMMDD}c.js

    只在交易日有數據，週末/假期返回 404。
    """
    url = f"https://www.hkex.com.hk/chi/csm/DailyStat/data_tab_daily_{date_str}c.js"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code == 404:
            return None  # 假期/週末
        r.raise_for_status()
    except requests.RequestException:
        return None

    # 解析 JS JSON
    text = r.text.strip()
    start = text.find("[")
    end = text.rfind("]")
    if start < 0 or end < 0:
        return None
    try:
        data = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None

    # 數據有 4 個 market: SSE/SZSE Northbound/Southbound
    # Southbound 的前 3 行 = [總成交, 買入, 賣出] (HKD Mil)
    def extract_southbound(market_name):
        for entry in data:
            if market_name in entry.get("market", ""):
                content = entry.get("content", [])
                if content:
                    rows = content[0].get("table", {}).get("tr", [])
                    vals = []
                    for row in rows[:3]:  # 前3行
                        cells = row.get("td", [])
                        if cells:
                            text_val = cells[0].get("#text", "") if isinstance(cells[0], dict) else str(cells[0])
                            num = re.search(r"[\d,]+\.?\d*", text_val.replace(",", ""))
                            vals.append(float(num.group().replace(",", "")) if num else None)
                    if len(vals) >= 3:
                        return {"total_mil": vals[0], "buy_mil": vals[1], "sell_mil": vals[2]}
        return None

    sh = extract_southbound("SSE Southbound")
    sz = extract_southbound("SZSE Southbound")

    if not sh and not sz:
        return None

    date_iso = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
    sh = sh or {}
    sz = sz or {}
    sh_t = sh.get("total_mil") or 0
    sh_b = sh.get("buy_mil") or 0
    sh_s = sh.get("sell_mil") or 0
    sz_t = sz.get("total_mil") or 0
    sz_b = sz.get("buy_mil") or 0
    sz_s = sz.get("sell_mil") or 0

    return {
        "date": date_iso,
        "southbound_total_mil": sh_t + sz_t,
        "southbound_buy_mil": sh_b + sz_b,
        "southbound_sell_mil": sh_s + sz_s,
        "southbound_net_mil": sh_b - sh_s + sz_b - sz_s,
        "sh_southbound_mil": sh_t,
        "sz_southbound_mil": sz_t,
    }


def crawl_historical(start: str, end: str, output: str = "data/stock_connect.csv", delay: float = 0.3):
    """歷史回填：逐日抓取，自動跳過假期/週末（404=無數據）"""
    start_dt = datetime.strptime(start, "%Y%m%d")
    end_dt = datetime.strptime(end, "%Y%m%d")

    existing_dates = set()
    if os.path.exists(output):
        old = pd.read_csv(output)
        existing_dates = set(old["date"].tolist())

    records = []
    skipped = 0
    holidays = 0
    current = start_dt

    print(f"歷史回填 {start} 至 {end}")
    while current <= end_dt:
        date_str = current.strftime("%Y%m%d")
        date_iso = current.strftime("%Y-%m-%d")

        # 跳過週末
        if current.weekday() >= 5:
            current += timedelta(days=1)
            continue

        # 跳過已有
        if date_iso in existing_dates:
            skipped += 1
            current += timedelta(days=1)
            continue

        rec = fetch_historical_daily(date_str)
        if rec:
            records.append(rec)
            print(f"  {date_iso} ✓ 淨買入={rec['southbound_net_mil']:+,.0f}M")
        else:
            holidays += 1

        current += timedelta(days=1)
        time.sleep(delay)

    # 合併
    new_df = pd.DataFrame(records)
    if os.path.exists(output):
        old_df = pd.read_csv(output)
        combined = pd.concat([old_df, new_df], ignore_index=True) if not new_df.empty else old_df
    else:
        combined = new_df

    if not combined.empty:
        combined = combined.sort_values("date").drop_duplicates(subset=["date"])
        os.makedirs(os.path.dirname(output) or ".", exist_ok=True)
        combined.to_csv(output, index=False, encoding="utf-8-sig")
        print(f"\n✅ {len(combined)} 條記錄 (新+{len(records)}, 跳過{skipped}, 假期{holidays})")
        print(f"   輸出: {output}")


def main():
    parser = argparse.ArgumentParser(description="滬港通/深港通 資金流向爬蟲")
    parser.add_argument("--output", type=str, default="data/stock_connect.csv")
    parser.add_argument("--json", action="store_true", help="輸出完整 JSON")
    parser.add_argument("--start", type=str, help="歷史回填起始日期 yyyymmdd")
    parser.add_argument("--end", type=str, help="歷史回填結束日期 yyyymmdd")
    args = parser.parse_args()

    # 歷史回填模式
    if args.start and args.end:
        crawl_historical(args.start, args.end, args.output)
        return

    print("抓取 HKEX Stock Connect 數據...")
    result = crawl_stock_connect()

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    summary = result.get("summary", {})
    if summary:
        print(f"\n📅 日期: {summary.get('date', 'N/A')}")
        print(f"📊 港股通總成交: HK${summary.get('southbound_total_mil', 0):,.0f}M")
        print(f"   買入: HK${summary.get('southbound_buy_mil', 0):,.0f}M")
        print(f"   賣出: HK${summary.get('southbound_sell_mil', 0):,.0f}M")
        net = summary.get("southbound_net_mil", 0)
        print(f"   淨買入: HK${net:,.0f}M {'📈' if net > 0 else '📉'}")
        print(f"\n   滬港通: HK${result['data'].get('sh_southbound', {}).get('total_mil', 0):,.0f}M")
        print(f"   深港通: HK${result['data'].get('sz_southbound', {}).get('total_mil', 0):,.0f}M")
        save_to_csv(result, args.output)
    else:
        print("⚠ 未抓取到數據（可能非交易日）")


if __name__ == "__main__":
    main()
