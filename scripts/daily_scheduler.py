#!/usr/bin/env python3
"""
CBSC 每日自動更新服務（Windows 背景執行）
每天收市後自動抓取 HKEX 完整日報表 + 南北水 + 累積歷史。

 安裝為 Windows 排程任務（開機自動執行，每日 16:15 更新）:
    python scripts/daily_scheduler.py --install

移除排程:
    python scripts/daily_scheduler.py --uninstall

手動執行一次:
    python scripts/daily_scheduler.py --run-now
"""

import argparse
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).parent.parent
SCRIPTS = ROOT / "scripts"
DATA = ROOT / "data"
PYTHON = sys.executable

# 每日日誌
LOG_FILE = DATA / "daily_update.log"


def log(msg: str):
    """寫入日誌"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    DATA.mkdir(exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def run_daily_update():
    """執行完整每日更新流程"""
    log("=" * 60)
    log("🚀 CBSC 每日自動更新開始")
    log("=" * 60)

    today = datetime.now().strftime("%Y%m%d")
    today_iso = datetime.now().strftime("%Y-%m-%d")
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y%m%d")
    cwd = str(ROOT)

    # Step 1: HKEX 完整日報表（市場概要 + 指數 + 十大成交 + 牛熊情緒 + 沽空）
    log("📥 Step 1: HKEX 完整日報表（牛熊情緒 + 沽空 + 十大成交）...")
    result = subprocess.run(
        [PYTHON, str(SCRIPTS / "hkex_full_crawler.py"),
         "--start", week_ago, "--end", today,
         "--excel", str(DATA / "raw_hkex/hkex_sentiment.xlsx")],
        capture_output=True, text=True, cwd=cwd
    )
    if result.returncode == 0:
        log("  ✅ HKEX 完成")
    else:
        log(f"  ⚠ HKEX 有問題: {result.stderr[:100]}")

    # Step 1b: 把今日日報表存為獨立 CSV（永不覆蓋，每日歸檔）
    log("📂 Step 1b: 歸檔今日日報表為 CSV...")
    archive_daily_report(today_iso)
    log("  ✅ 日報表已歸檔")

    # Step 2: 累積牛熊情緒歷史
    log("🐂 Step 2: 累積牛熊情緒歷史...")
    try:
        append_sentiment()
        log("  ✅ 情緒歷史已更新")
    except Exception as e:
        log(f"  ⚠ 情緒累積失敗: {e}")

    # Step 2b: 累積沽空歷史
    log("📉 Step 2b: 累積沽空歷史...")
    try:
        append_short_selling()
        log("  ✅ 沽空歷史已更新")
    except Exception as e:
        log(f"  ⚠ 沽空累積失敗: {e}")

    # Step 3: 南北水
    log("💰 Step 3: 南北水資金流向...")
    result = subprocess.run(
        [PYTHON, str(SCRIPTS / "stock_connect_crawler.py"),
         "--start", week_ago, "--end", today],
        capture_output=True, text=True, cwd=cwd
    )
    if result.returncode == 0:
        log("  ✅ 南北水完成")
    else:
        log(f"  ⚠ 南北水有問題: {result.stderr[:100]}")

    # Step 4: 導出 Dashboard JSON
    log("📊 Step 4: 導出 Dashboard JSON...")
    result = subprocess.run(
        [PYTHON, str(SCRIPTS / "export_dashboard_data.py")],
        capture_output=True, text=True, cwd=cwd
    )
    log("  ✅ JSON 導出完成")

    log("=" * 60)
    log("✅ 每日更新完成！")
    log("=" * 60)


def archive_daily_report(date_iso: str):
    """把今日日報表歸檔為獨立 CSV（每日一個，永不覆蓋）"""
    import pandas as pd

    xlsx = DATA / "raw_hkex/hkex_sentiment.xlsx"
    archive_dir = DATA / "daily_archive"
    archive_dir.mkdir(exist_ok=True)

    if not xlsx.exists():
        return

    sheets = pd.read_excel(xlsx, sheet_name=None)

    # 把每個 sheet 追加到對應的累積 CSV
    sheet_names = {
        "市場概要": "raw_hkex/market_summary_history.csv",
        "各指數": "raw_hkex/indices_history.csv",
        "十大成交金額": "raw_hkex/top_dollars_history.csv",
        "十大成交股數": "raw_hkex/top_shares_history.csv",
        "散戶牛熊情緒": "sentiment/sentiment_history.csv",
        "全市場沽空比率": "raw_hkex/short_ratio_history.csv",
        "十大沽空股票": "raw_hkex/top_short_history.csv",
    }

    for sheet_name, csv_name in sheet_names.items():
        if sheet_name not in sheets:
            continue
        new_data = sheets[sheet_name]
        if new_data.empty:
            continue

        csv_path = DATA / csv_name
        if csv_path.exists():
            old = pd.read_csv(csv_path)
            # 只加入新日期的數據
            if "date" in new_data.columns and "date" in old.columns:
                new_dates = set(new_data["date"]) - set(old["date"])
                if not new_dates:
                    continue
                new_only = new_data[new_data["date"].isin(new_dates)]
                combined = pd.concat([old, new_only], ignore_index=True)
            else:
                combined = pd.concat([old, new_data], ignore_index=True).drop_duplicates()
            combined = combined.sort_values("date") if "date" in combined.columns else combined
        else:
            combined = new_data

        combined.to_csv(csv_path, index=False, encoding="utf-8-sig")
        log(f"    {csv_name}: {len(combined)} 行")


def append_short_selling():
    """累積沽空數據到獨立 CSV"""
    import pandas as pd

    xlsx = DATA / "raw_hkex/hkex_sentiment.xlsx"
    if not xlsx.exists():
        return

    try:
        ss = pd.read_excel(xlsx, sheet_name="十大沽空股票")
        if ss.empty:
            return
        csv_path = DATA / "raw_hkex/short_selling_history.csv"
        if csv_path.exists():
            old = pd.read_csv(csv_path)
            combined = pd.concat([old, ss], ignore_index=True).drop_duplicates()
        else:
            combined = ss
        combined.to_csv(csv_path, index=False, encoding="utf-8-sig")
        log(f"  沽空歷史: {len(combined)} 行")
    except Exception:
        pass


def append_sentiment():
    """累積牛熊情緒到 sentiment_history.csv"""
    import pandas as pd

    xlsx = DATA / "raw_hkex/hkex_sentiment.xlsx"
    csv_path = DATA / "sentiment/sentiment_history.csv"

    if not xlsx.exists():
        return

    new = pd.read_excel(xlsx, sheet_name="散戶牛熊情緒")
    if new.empty:
        return
    new["date"] = pd.to_datetime(new["date"])

    if csv_path.exists():
        old = pd.read_csv(csv_path, parse_dates=["date"])
        combined = pd.concat([old, new], ignore_index=True)
        combined = combined.drop_duplicates(subset=["date"], keep="last")
        combined = combined.sort_values("date")
    else:
        combined = new.sort_values("date")

    combined.to_csv(csv_path, index=False, encoding="utf-8-sig")
    log(f"  情緒歷史: {len(combined)} 天 ({combined['date'].min().date()} to {combined['date'].max().date()})")


def install_scheduler():
    """安裝為 Windows 排程任務（每日 16:15 執行）"""
    script = str(Path(__file__).resolve())
    python = PYTHON

    # 用 schtasks 創建排程
    cmd = (
        f'schtasks /create /tn "CBSC_Daily_Update" /tr '
        f'"\\"{python}\\" \\"{script}\\" --run-now" '
        f'/sc daily /st 16:15 /f'
    )
    log(f"安裝 Windows 排程任務...")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    if result.returncode == 0:
        log("✅ 排程已安裝！每日 16:15 自動更新")
        log(f"   任務名稱: CBSC_Daily_Update")
        log(f"   執行: {python} {script} --run-now")
        log(f"   日誌: {LOG_FILE}")
    else:
        log(f"❌ 安裝失敗: {result.stderr}")
        log("嘗試用 --run-now 手動測試")


def uninstall_scheduler():
    """移除排程"""
    result = subprocess.run(
        'schtasks /delete /tn "CBSC_Daily_Update" /f',
        shell=True, capture_output=True, text=True
    )
    if result.returncode == 0:
        log("✅ 排程已移除")
    else:
        log(f"❌ 移除失敗: {result.stderr}")


def main():
    parser = argparse.ArgumentParser(description="CBSC 每日自動更新服務")
    parser.add_argument("--install", action="store_true", help="安裝為 Windows 排程（每日16:15）")
    parser.add_argument("--uninstall", action="store_true", help="移除排程")
    parser.add_argument("--run-now", action="store_true", help="立即執行一次")
    args = parser.parse_args()

    if args.install:
        install_scheduler()
    elif args.uninstall:
        uninstall_scheduler()
    elif args.run_now:
        run_daily_update()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
