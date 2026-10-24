#!/usr/bin/env python3
"""
CBSC 一鍵數據收集 + 回測 + 分析平台
個人使用，本地運行。

 1. 抓取 HKEX 每日報告（完整：十大成交 + 各指數）
 2. 抓取南北水資金流向
 3. 多 CPU 回測（6 策略 × 70+ 股票）
 4. 統計分析 + Excel 報告
 5. 導出 JSON 供 Dashboard / GUI

用法:
    python run_platform.py                    # 全部步驟
    python run_platform.py --skip-crawl       # 跳過爬蟲（已有數據）
    python run_platform.py --skip-backtest    # 跳過回測
    python run_platform.py --quick            # 快速模式（少量股票）
"""

import argparse
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).parent
SCRIPTS = ROOT / "scripts"
DATA = ROOT / "data"
PYTHON = sys.executable


def run_step(name, cmd, cwd=None):
    """運行一個步驟"""
    print(f"\n{'='*60}")
    print(f"📋 {name}")
    print(f"{'='*60}")
    start = time.time()
    result = subprocess.run(cmd, cwd=cwd or str(ROOT), capture_output=False)
    elapsed = time.time() - start
    status = "✅" if result.returncode == 0 else "❌"
    print(f"{status} {name} 完成 ({elapsed:.1f}s)")
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description="CBSC 一鍵平台")
    parser.add_argument("--skip-crawl", action="store_true")
    parser.add_argument("--skip-backtest", action="store_true")
    parser.add_argument("--quick", action="store_true", help="快速模式（6隻股票）")
    args = parser.parse_args()

    print("🚀 CBSC 量化交易平台")
    print(f"   時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   模式: {'快速' if args.quick else '完整'}")

    today = datetime.now().strftime("%Y%m%d")
    month_ago = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
    all_ok = True

    # Step 1: HKEX 每日報告
    if not args.skip_crawl:
        all_ok &= run_step(
            "Step 1/5: HKEX 每日報告爬蟲",
            [PYTHON, str(SCRIPTS / "hkex_full_crawler.py"),
             "--start", month_ago, "--end", today,
             "--excel", str(DATA / "hkex_latest.xlsx")],
        )

    # Step 2: 南北水
    if not args.skip_crawl:
        all_ok &= run_step(
            "Step 2/5: 南北水資金流向",
            [PYTHON, str(SCRIPTS / "stock_connect_crawler.py"),
             "--start", month_ago, "--end", today],
        )

    # Step 3: 多 CPU 回測
    if not args.skip_backtest:
        bt_cmd = [PYTHON, str(SCRIPTS / "backtest_pro.py"), "--walk-forward"]
        if args.quick:
            bt_cmd += ["--symbols", "0700.HK", "9988.HK", "0939.HK", "1810.HK", "1177.HK", "0992.HK"]
        bt_cmd += ["--output", str(DATA / "backtest_pro_results.csv")]
        all_ok &= run_step("Step 3/5: 多 CPU 回測（6 策略 × 多股票）", bt_cmd)

    # Step 4: 統計分析
    excel_path = DATA / "hkex_latest.xlsx"
    if excel_path.exists():
        all_ok &= run_step(
            "Step 4/5: 統計分析",
            [PYTHON, str(SCRIPTS / "hkex_statistics.py"),
             "--excel", str(excel_path)],
        )

    # Step 5: 導出 JSON
    all_ok &= run_step(
        "Step 5/5: 導出 Dashboard JSON",
        [PYTHON, str(SCRIPTS / "export_dashboard_data.py")],
    )

    # 總結
    print(f"\n{'='*60}")
    print(f"{'🎉 全部完成！' if all_ok else '⚠ 部分步驟失敗'}")
    print(f"{'='*60}")
    print(f"\n📂 輸出文件:")
    for f in DATA.glob("*"):
        if f.is_file() and f.stat().st_size > 0:
            print(f"   {f.name} ({f.stat().st_size / 1024:.0f} KB)")
    print(f"\n🖥️ 開啟方式:")
    print(f"   GUI:   dist/CBSC/CBSC.exe")
    print(f"   Web:   http://localhost:3001/market-data")
    print(f"   Excel: data/hkex_latest.xlsx")


if __name__ == "__main__":
    main()
