#!/usr/bin/env python3
"""
CBSC 量化交易系統 - 桌面 GUI 應用
一鍵打開，顯示 HKEX 報告 + 南北水資金流向 + 回測結果 + 每日自動更新。

打包成 EXE:
    pip install pyinstaller
    pyinstaller --onefile --windowed --name CBSC cbsc_gui.py

用法:
    python cbsc_gui.py        # 直接運行
    CBSC.exe                   # 打包後雙擊
"""

import sys
import os
import json
import subprocess
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import numpy as np

# 確保能 import scripts 目錄
sys.path.insert(0, str(Path(__file__).parent))

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QProgressBar, QStatusBar, QSystemTrayIcon, QMenu, QCheckBox,
    QSpinBox, QGroupBox, QGridLayout, QHeaderView, QFileDialog,
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QIcon, QColor, QFont

import pyqtgraph as pg

# 數據目錄
DATA_DIR = Path(__file__).parent / "data"
SCRIPTS_DIR = Path(__file__).parent / "scripts"


# ==============================================================================
# 數據更新 Worker（後台線程）
# ==============================================================================

class UpdateWorker(QThread):
    """後台運行爬蟲 + 回測"""
    progress = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, run_backtest=False):
        super().__init__()
        self.run_backtest = run_backtest

    def run(self):
        try:
            today = datetime.now().strftime("%Y%m%d")
            month_ago = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")

            # 1. HKEX 每日報告
            self.progress.emit("📥 抓取 HKEX 每日報告...")
            subprocess.run(
                [sys.executable, str(SCRIPTS_DIR / "hkex_daily_crawler.py"),
                 "--start", month_ago, "--end", today, "--delay", "0.3"],
                capture_output=True, text=True, cwd=str(Path(__file__).parent)
            )
            self.progress.emit("✅ HKEX 完成")

            # 2. 南北水
            self.progress.emit("💰 抓取南北水資金流向...")
            subprocess.run(
                [sys.executable, str(SCRIPTS_DIR / "stock_connect_crawler.py")],
                capture_output=True, text=True, cwd=str(Path(__file__).parent)
            )
            self.progress.emit("✅ 南北水完成")

            # 3. 回測（可選）
            if self.run_backtest:
                self.progress.emit("🔬 運行多 CPU 回測...")
                subprocess.run(
                    [sys.executable, str(SCRIPTS_DIR / "multiprocess_backtest.py"), "--workers", "16"],
                    capture_output=True, text=True, cwd=str(Path(__file__).parent)
                )
                self.progress.emit("✅ 回測完成")

            self.finished_signal.emit(True, "全部更新完成！")
        except Exception as e:
            self.finished_signal.emit(False, f"更新失敗: {e}")


# ==============================================================================
# HKEX 報告 Tab
# ==============================================================================

class HkexTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # 統計卡片
        stats = QGroupBox("📊 最新市場統計")
        stats_layout = QGridLayout()
        self.lbl_hsi = QLabel("恆指: --")
        self.lbl_turnover = QLabel("成交額: --")
        self.lbl_deals = QLabel("成交宗數: --")
        self.lbl_ad = QLabel("升/跌: --")
        for lbl in [self.lbl_hsi, self.lbl_turnover, self.lbl_deals, self.lbl_ad]:
            f = lbl.font(); f.setPointSize(12); f.setBold(True); lbl.setFont(f)
        stats_layout.addWidget(self.lbl_hsi, 0, 0)
        stats_layout.addWidget(self.lbl_turnover, 0, 1)
        stats_layout.addWidget(self.lbl_deals, 1, 0)
        stats_layout.addWidget(self.lbl_ad, 1, 1)
        stats.setLayout(stats_layout)
        layout.addWidget(stats)

        # 恆指走勢圖
        self.plot = pg.PlotWidget(title="恆生指數走勢")
        self.plot.setLabel("left", "點數")
        self.plot.setLabel("bottom", "日期")
        self.plot.showGrid(x=True, y=True)
        layout.addWidget(self.plot)

        # 成交額柱狀圖
        self.plot_turnover = pg.PlotWidget(title="每日成交額（億港元）")
        self.plot_turnover.setLabel("left", "億 HKD")
        self.plot_turnover.showGrid(x=True, y=True)
        layout.addWidget(self.plot_turnover)

        # 升跌比走勢圖
        self.plot_ad = pg.PlotWidget(title="升跌比走勢（>1=升市多, <1=跌市多）")
        self.plot_ad.setLabel("left", "升/跌比")
        self.plot_ad.showGrid(x=True, y=True)
        layout.addWidget(self.plot_ad)

        # 數據表格
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["日期", "恆指收市", "變動", "成交額", "升", "跌"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        # 十大成交金額最多股票表格
        top_group = QGroupBox("🏆 最新十大成交金額最多股票")
        top_layout = QVBoxLayout()
        self.top_table = QTableWidget()
        self.top_table.setColumnCount(5)
        self.top_table.setHorizontalHeaderLabels(["排名", "代號", "股票", "成交額", "成交股數"])
        self.top_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.top_table.setMaximumHeight(250)
        top_layout.addWidget(self.top_table)
        top_group.setLayout(top_layout)
        layout.addWidget(top_group)

        # 散戶牛熊情緒指標
        sentiment_group = QGroupBox("🐂🐻 散戶牛熊情緒指標（逆向信號：恐懼=買, 貪婪=賣）")
        sl = QHBoxLayout()

        self.lbl_sentiment_score = QLabel("情緒: --")
        self.lbl_bull_pct = QLabel("牛證: --%")
        self.lbl_bear_pct = QLabel("熊證: --%")
        self.lbl_sentiment_ratio = QLabel("牛熊比: --")
        for lbl in [self.lbl_sentiment_score, self.lbl_bull_pct, self.lbl_bear_pct, self.lbl_sentiment_ratio]:
            f = lbl.font(); f.setPointSize(11); f.setBold(True); lbl.setFont(f)
            sl.addWidget(lbl)
        sl.addStretch()

        # 情緒走勢圖
        self.plot_sentiment = pg.PlotWidget(title="散戶情緒走勢（綠=貪婪, 紅=恐懼, 50=中性）")
        self.plot_sentiment.setLabel("left", "牛證%")
        self.plot_sentiment.showGrid(x=True, y=True)
        sentiment_layout = QVBoxLayout()
        sentiment_layout.addLayout(sl)
        sentiment_layout.addWidget(self.plot_sentiment)
        sentiment_group.setLayout(sentiment_layout)
        layout.addWidget(sentiment_group)

    def load_data(self):
        csv_path = DATA_DIR / "hkex_daily.csv"
        if not csv_path.exists():
            return
        df = pd.read_csv(csv_path).sort_values("date")

        if df.empty:
            return

        latest = df.iloc[-1]

        # 統計卡片
        hsi = latest.get("hsi_close")
        chg = latest.get("hsi_change", 0) or 0
        color = "#3f8600" if chg >= 0 else "#cf1322"
        self.lbl_hsi.setText(f"恆指: {hsi:,.2f}" if pd.notna(hsi) else "恆指: --")
        self.lbl_hsi.setStyleSheet(f"color: {color};")

        turnover = latest.get("turnover_hkd", 0) or 0
        self.lbl_turnover.setText(f"成交額: HK${turnover/1e9:.1f}B")
        self.lbl_deals.setText(f"成交宗數: {(latest.get('deals',0) or 0):,.0f}")
        adv = latest.get("advanced_stocks", 0) or 0
        dec = latest.get("declined_stocks", 0) or 0
        self.lbl_ad.setText(f"升/跌: {adv:,} / {dec:,}")

        # 恆指走勢圖
        valid = df.dropna(subset=["hsi_close"]).tail(30)
        if not valid.empty:
            x = range(len(valid))
            y = valid["hsi_close"].values
            self.plot.clear()
            self.plot.plot(list(x), list(y), pen=pg.mkPen(color="#1890ff", width=2))
            # 設定 x 軸標籤
            ticks = [[(i, d[:5]) for i, d in enumerate(valid["date"].values) if i % 5 == 0]]
            self.plot.getAxis("bottom").setTicks(ticks)

        # 成交額柱狀圖
        valid_t = df.dropna(subset=["turnover_hkd"]).tail(30)
        if not valid_t.empty:
            x2 = range(len(valid_t))
            y2 = (valid_t["turnover_hkd"].values / 1e8)  # 億港元
            self.plot_turnover.clear()
            for xi, yi in zip(x2, y2):
                self.plot_turnover.addItem(pg.BarGraphItem(x=[xi], height=[yi], width=0.6, brush="#1890ff"))

        # 升跌比走勢圖
        adv_col = "advanced_stocks" if "advanced_stocks" in df.columns else "advanced"
        dec_col = "declined_stocks" if "declined_stocks" in df.columns else "declined"
        if adv_col in df.columns and dec_col in df.columns:
            adv = pd.to_numeric(df[adv_col], errors="coerce")
            dec = pd.to_numeric(df[dec_col], errors="coerce")
            ratio = (adv / dec.replace(0, np.nan)).dropna()
            if not ratio.empty:
                self.plot_ad.clear()
                self.plot_ad.addItem(pg.InfiniteLine(pos=1, angle=0, pen=pg.mkPen(color="#666", width=1, style=Qt.PenStyle.DashLine)))
                x3 = list(range(len(ratio)))
                y3 = ratio.values
                for i in range(1, len(y3)):
                    c = "#52c41a" if y3[i] >= 1 else "#f5222d"
                    self.plot_ad.plot([i-1, i], [y3[i-1], y3[i]], pen=pg.mkPen(color=c, width=2))
                self.plot_ad.plot(x3, list(y3), pen=None, symbol="o", symbolSize=5,
                                  symbolBrush=["#52c41a" if v >= 1 else "#f5222d" for v in y3])

        # 表格（最近 14 天）
        recent = df.tail(14).iloc[::-1]
        self.table.setRowCount(len(recent))
        for i, (_, row) in enumerate(recent.iterrows()):
            self.table.setItem(i, 0, QTableWidgetItem(str(row.get("date", ""))))
            hsi_val = row.get("hsi_close")
            self.table.setItem(i, 1, QTableWidgetItem(f"{hsi_val:,.2f}" if pd.notna(hsi_val) else "-"))
            chg_val = row.get("hsi_change", 0) or 0
            item = QTableWidgetItem(f"{chg_val:+.2f}")
            item.setForeground(QColor("#3f8600" if chg_val >= 0 else "#cf1322"))
            self.table.setItem(i, 2, item)
            tov = row.get("turnover_hkd", 0) or 0
            self.table.setItem(i, 3, QTableWidgetItem(f"${tov/1e9:.1f}B"))
            self.table.setItem(i, 4, QTableWidgetItem(f"{row.get('advanced_stocks',0) or 0:,}"))
            self.table.setItem(i, 5, QTableWidgetItem(f"{row.get('declined_stocks',0) or 0:,}"))

        # 十大成交金額最多股票（從 Excel JSON 讀取）
        self.load_top_dollars()

        # 散戶牛熊情緒指標
        self.load_sentiment()

    def load_sentiment(self):
        """從 hkex_sentiment.xlsx 讀取散戶牛熊情緒"""
        import openpyxl
        xlsx_path = DATA_DIR / "hkex_sentiment.xlsx"
        if not xlsx_path.exists():
            # 嘗試 hkex_may_jun.xlsx
            xlsx_path = DATA_DIR / "hkex_may_jun.xlsx"
            if not xlsx_path.exists():
                return
        try:
            sent = pd.read_excel(xlsx_path, sheet_name="散戶牛熊情緒")
        except Exception:
            return
        if sent.empty:
            return

        sent = sent.sort_values("date")
        latest = sent.iloc[-1]

        # 更新標籤
        score = latest.get("bull_pct", 50)
        label = latest.get("sentiment_label", "?")
        color = "#52c41a" if score > 70 else "#f5222d" if score < 30 else "#faad14"
        self.lbl_sentiment_score.setText(f"情緒: {score:.0f}/100 ({label})")
        self.lbl_sentiment_score.setStyleSheet(f"color: {color};")
        self.lbl_bull_pct.setText(f"牛證: {latest.get('bull_pct',0):.1f}%")
        self.lbl_bear_pct.setText(f"熊證: {latest.get('bear_pct',0):.1f}%")
        ratio = latest.get("bull_bear_ratio", 1)
        self.lbl_sentiment_ratio.setText(f"牛熊比: {ratio:.1f}" if ratio < 999 else "牛熊比: ∞")

        # 情緒走勢圖
        bull = sent["bull_pct"].values
        x = list(range(len(bull)))
        self.plot_sentiment.clear()
        # 中線（50%）
        self.plot_sentiment.addItem(pg.InfiniteLine(pos=50, angle=0, pen=pg.mkPen(color="#666", width=1, style=Qt.PenStyle.DashLine)))
        # 恐懼區（<30%）和貪婪區（>80%）
        self.plot_sentiment.addItem(pg.InfiniteLine(pos=30, angle=0, pen=pg.mkPen(color="#f5222d", width=1, style=Qt.PenStyle.DashLine)))
        self.plot_sentiment.addItem(pg.InfiniteLine(pos=80, angle=0, pen=pg.mkPen(color="#52c41a", width=1, style=Qt.PenStyle.DashLine)))
        # 散戶情緒線
        for i in range(1, len(bull)):
            c = "#52c41a" if bull[i] > 70 else "#f5222d" if bull[i] < 30 else "#faad14"
            self.plot_sentiment.plot([i-1, i], [bull[i-1], bull[i]], pen=pg.mkPen(color=c, width=2))
        self.plot_sentiment.plot(x, list(bull), pen=None, symbol="o", symbolSize=6,
                                 symbolBrush=["#52c41a" if v > 70 else "#f5222d" if v < 30 else "#faad14" for v in bull])

    def load_top_dollars(self):
        """從 hkex_top_dollars.json 讀取最新一天的十大活躍股"""
        json_path = Path(__file__).parent / "unified-dashboard" / "public" / "data" / "hkex_top_dollars.json"
        if not json_path.exists():
            return
        import json
        data = json.loads(json_path.read_text(encoding="utf-8"))
        if not data:
            return
        # 取最新日期
        latest_date = max(d["date"] for d in data)
        today_top = [d for d in data if d["date"] == latest_date]
        today_top.sort(key=lambda x: x.get("rank", 0))

        self.top_table.setRowCount(len(today_top))
        for i, stock in enumerate(today_top):
            self.top_table.setItem(i, 0, QTableWidgetItem(str(stock.get("rank", i+1))))
            self.top_table.setItem(i, 1, QTableWidgetItem(str(stock.get("code", ""))))
            self.top_table.setItem(i, 2, QTableWidgetItem(str(stock.get("name_cn", ""))))
            tov = stock.get("turnover_hkd", 0)
            self.top_table.setItem(i, 3, QTableWidgetItem(f"${tov/1e8:.1f}億" if tov else "-"))
            vol = stock.get("volume_shares", 0)
            self.top_table.setItem(i, 4, QTableWidgetItem(f"{vol/1e6:.1f}M" if vol else "-"))


# ==============================================================================
# 南北水 Tab
# ==============================================================================

class StockConnectTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # 統計卡片
        stats = QGroupBox("💰 港股通資金流向")
        sl = QGridLayout()
        self.lbl_total = QLabel("總成交: --")
        self.lbl_net = QLabel("淨買入: --")
        self.lbl_sh = QLabel("滬港通: --")
        self.lbl_sz = QLabel("深港通: --")
        for lbl in [self.lbl_total, self.lbl_net, self.lbl_sh, self.lbl_sz]:
            f = lbl.font(); f.setPointSize(12); f.setBold(True); lbl.setFont(f)
        sl.addWidget(self.lbl_total, 0, 0)
        sl.addWidget(self.lbl_net, 0, 1)
        sl.addWidget(self.lbl_sh, 1, 0)
        sl.addWidget(self.lbl_sz, 1, 1)
        stats.setLayout(sl)
        layout.addWidget(stats)

        # 淨買入走勢圖
        self.plot = pg.PlotWidget(title="南北水淨買入走勢（綠=流入hk 買入多 / 紅=流出 賣出多）")
        self.plot.setLabel("left", "百萬 HKD")
        self.plot.showGrid(x=True, y=True)
        layout.addWidget(self.plot)

        # 累計淨流入圖
        self.plot_cumulative = pg.PlotWidget(title="累計淨流入（正=累計流入, 負=累計流出）")
        self.plot_cumulative.setLabel("left", "累計 百萬 HKD")
        self.plot_cumulative.showGrid(x=True, y=True)
        layout.addWidget(self.plot_cumulative)

        # 滬深對比圖
        self.plot_sh_sz = pg.PlotWidget(title="滬港通 vs 深港通 成交對比")
        self.plot_sh_sz.setLabel("left", "百萬 HKD")
        self.plot_sh_sz.showGrid(x=True, y=True)
        layout.addWidget(self.plot_sh_sz)

        # 表格
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["日期", "總成交", "買入", "賣出", "淨買入", "滬/深"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

    def load_data(self):
        csv_path = DATA_DIR / "stock_connect.csv"
        if not csv_path.exists():
            return
        df = pd.read_csv(csv_path).sort_values("date")
        if df.empty:
            return

        latest = df.iloc[-1]
        total = latest.get("southbound_total_mil", 0) or 0
        net = latest.get("southbound_net_mil", 0) or 0
        sh = latest.get("sh_southbound_mil", 0) or 0
        sz = latest.get("sz_southbound_mil", 0) or 0

        self.lbl_total.setText(f"總成交: HK${total:,.0f}M")
        net_color = "#3f8600" if net >= 0 else "#cf1322"
        self.lbl_net.setText(f"淨買入: {'+' if net>=0 else ''}HK${net:,.0f}M")
        self.lbl_net.setStyleSheet(f"color: {net_color};")
        self.lbl_sh.setText(f"滬港通: HK${sh:,.0f}M")
        self.lbl_sz.setText(f"深港通: HK${sz:,.0f}M")

        # 圖表：淨買入線性走勢圖（正=流入綠色，負=流出紅色）
        valid = df.dropna(subset=["southbound_net_mil"])
        if not valid.empty:
            x = list(range(len(valid)))
            y = valid["southbound_net_mil"].values
            self.plot.clear()
            # 畫零軸線
            self.plot.addItem(pg.InfiniteLine(pos=0, angle=0, pen=pg.mkPen(color="#666", width=1, style=Qt.PenStyle.DashLine)))
            # 線性圖：正值段用綠色，負值段用紅色
            for i in range(len(y)):
                if i == 0:
                    continue
                y_prev, y_curr = y[i-1], y[i]
                # 每段連線根據當前值上色
                color = "#52c41a" if y_curr >= 0 else "#f5222d"
                self.plot.plot([i-1, i], [y_prev, y_curr], pen=pg.mkPen(color=color, width=2))
            # 數據點
            self.plot.plot(x, list(y), pen=None, symbol="o", symbolSize=6,
                          symbolBrush=["#52c41a" if v >= 0 else "#f5222d" for v in y])
            # x 軸日期標籤
            ticks = [[(i, d[5:]) for i, d in enumerate(valid["date"].values)]]
            self.plot.getAxis("bottom").setTicks(ticks)

        # 累計淨流入圖
        if not valid.empty:
            cumsum = valid["southbound_net_mil"].cumsum().values
            self.plot_cumulative.clear()
            self.plot_cumulative.plot(list(range(len(cumsum))), list(cumsum),
                                      pen=pg.mkPen(color="#1890ff", width=2))
            self.plot_cumulative.addItem(pg.InfiniteLine(pos=0, angle=0, pen=pg.mkPen(color="#666", width=1, style=Qt.PenStyle.DashLine)))
            ticks2 = [[(i, d[5:]) for i, d in enumerate(valid["date"].values)]]
            self.plot_cumulative.getAxis("bottom").setTicks(ticks2)

        # 滬深對比圖
        sh_vals = pd.to_numeric(valid.get("sh_southbound_mil"), errors="coerce").fillna(0).values
        sz_vals = pd.to_numeric(valid.get("sz_southbound_mil"), errors="coerce").fillna(0).values
        if len(sh_vals) > 0:
            self.plot_sh_sz.clear()
            self.plot_sh_sz.plot(list(range(len(sh_vals))), list(sh_vals),
                                 pen=pg.mkPen(color="#1890ff", width=2), name="滬港通")
            self.plot_sh_sz.plot(list(range(len(sz_vals))), list(sz_vals),
                                 pen=pg.mkPen(color="#fa8c16", width=2), name="深港通")

        # 表格
        recent = df.iloc[::-1]
        self.table.setRowCount(len(recent))
        for i, (_, row) in enumerate(recent.iterrows()):
            self.table.setItem(i, 0, QTableWidgetItem(str(row.get("date", ""))))
            self.table.setItem(i, 1, QTableWidgetItem(f"${row.get('southbound_total_mil',0) or 0:,.0f}M"))
            self.table.setItem(i, 2, QTableWidgetItem(f"${row.get('southbound_buy_mil',0) or 0:,.0f}M"))
            self.table.setItem(i, 3, QTableWidgetItem(f"${row.get('southbound_sell_mil',0) or 0:,.0f}M"))
            net_v = row.get("southbound_net_mil", 0) or 0
            item = QTableWidgetItem(f"{'+' if net_v>=0 else ''}{net_v:,.0f}M")
            item.setForeground(QColor("#3f8600" if net_v >= 0 else "#cf1322"))
            self.table.setItem(i, 4, item)
            self.table.setItem(i, 5, QTableWidgetItem(f"${row.get('sh_southbound_mil',0) or 0:,.0f} / ${row.get('sz_southbound_mil',0) or 0:,.0f}"))


# ==============================================================================
# 回測 Tab
# ==============================================================================

class BacktestTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # 統計
        stats = QGroupBox("🔬 回測概覽")
        sl = QGridLayout()
        self.lbl_count = QLabel("股票數: --")
        self.lbl_best = QLabel("最佳 Sharpe: --")
        self.lbl_avg = QLabel("平均回報: --")
        for lbl in [self.lbl_count, self.lbl_best, self.lbl_avg]:
            f = lbl.font(); f.setPointSize(12); f.setBold(True); lbl.setFont(f)
        sl.addWidget(self.lbl_count, 0, 0)
        sl.addWidget(self.lbl_best, 0, 1)
        sl.addWidget(self.lbl_avg, 0, 2)
        stats.setLayout(sl)
        layout.addWidget(stats)

        # Sharpe 對比圖
        self.plot = pg.PlotWidget(title="Top 10 策略組合 Sharpe Ratio（扣除交易成本後）")
        self.plot.setLabel("left", "Sharpe")
        self.plot.setLabel("bottom", "股票+策略")
        self.plot.showGrid(x=True, y=True)
        layout.addWidget(self.plot)

        # 最大回撤對比圖
        self.plot_dd = pg.PlotWidget(title="Top 10 最大回撤對比（越小越好）")
        self.plot_dd.setLabel("left", "回撤 %")
        self.plot_dd.showGrid(x=True, y=True)
        layout.addWidget(self.plot_dd)

        # 表格（含策略 + walk-forward 欄位）
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels(["股票", "策略", "Sharpe", "年回報", "回撤", "Calmar", "勝率", "成本", "顯著"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

    def load_data(self):
        # 優先使用 backtest_pro_results.csv（含成本 + walk-forward）
        pro_path = DATA_DIR / "backtest_pro_results.csv"
        old_path = DATA_DIR / "backtest_results.csv"
        csv_path = pro_path if pro_path.exists() else old_path
        if not csv_path.exists():
            return
        df = pd.read_csv(csv_path)
        if "status" in df.columns:
            df = df[df["status"] == "ok"]
        if df.empty:
            return

        # 取每隻股票最佳策略（pro 版有多策略）
        if "strategy" in df.columns:
            df = df.sort_values("sharpe", ascending=False).drop_duplicates(subset=["symbol"], keep="first")

        df = df.sort_values("sharpe", ascending=False).head(20)
        self.lbl_count.setText(f"策略數: {len(df)}")
        self.lbl_best.setText(f"最佳 Sharpe: {df['sharpe'].max():.3f}")
        avg_ret = df["return_annual"].mean() if "return_annual" in df.columns else df["return"].mean()
        self.lbl_avg.setText(f"平均年回報: {avg_ret*100:.1f}%")
        self.lbl_avg.setText(f"平均年回報: {avg_ret*100:.1f}%")

        # 取 top 10 做圖表
        top = df.head(10)
        labels = [f"{r['symbol'][:4]}\n{r.get('strategy','')[:6]}" for _, r in top.iterrows()]
        x = list(range(len(top)))

        # Sharpe 圖
        self.plot.clear()
        for xi, (_, row) in zip(x, top.iterrows()):
            yi = row["sharpe"]
            c = "#52c41a" if yi >= 0.5 else "#faad14" if yi >= 0 else "#f5222d"
            self.plot.addItem(pg.BarGraphItem(x=[xi], height=[yi], width=0.6, brush=c))
        self.plot.getAxis("bottom").setTicks([[(i, labels[i]) for i in range(len(labels))]])

        # 最大回撤圖
        self.plot_dd.clear()
        for xi, (_, row) in zip(x, top.iterrows()):
            yi = row.get("max_dd", 0) * 100
            self.plot_dd.addItem(pg.BarGraphItem(x=[xi], height=[yi], width=0.6, brush="#f5222d"))
        self.plot_dd.getAxis("bottom").setTicks([[(i, labels[i]) for i in range(len(labels))]])

        # 表格
        self.table.setRowCount(len(df))
        for i, (_, row) in enumerate(df.iterrows()):
            self.table.setItem(i, 0, QTableWidgetItem(str(row.get("symbol", ""))))
            self.table.setItem(i, 1, QTableWidgetItem(str(row.get("strategy", ""))))
            sh = row.get("sharpe", 0)
            item = QTableWidgetItem(f"{sh:.3f}")
            item.setForeground(QColor("#3f8600" if sh >= 0.5 else "#faad14" if sh >= 0 else "#cf1322"))
            self.table.setItem(i, 2, item)
            ret = row.get("return_annual", row.get("return", 0))
            item2 = QTableWidgetItem(f"{ret*100:+.1f}%")
            item2.setForeground(QColor("#3f8600" if ret >= 0 else "#cf1322"))
            self.table.setItem(i, 3, item2)
            self.table.setItem(i, 4, QTableWidgetItem(f"{row.get('max_dd',0)*100:.1f}%"))
            calmar = row.get("calmar", 0)
            self.table.setItem(i, 5, QTableWidgetItem(f"{calmar:.2f}" if calmar else "-"))
            self.table.setItem(i, 6, QTableWidgetItem(f"{row.get('win_rate',0)*100:.0f}%"))
            cost = row.get("cost_total", 0)
            self.table.setItem(i, 7, QTableWidgetItem(f"{cost:.3f}" if cost else "-"))
            sig = row.get("significant", False)
            sig_item = QTableWidgetItem("✓" if sig else "—")
            sig_item.setForeground(QColor("#3f8600" if sig else "#999"))
            self.table.setItem(i, 8, sig_item)
            self.table.setItem(i, 5, QTableWidgetItem(f"{row.get('win_rate',0)*100:.0f}%"))


# ==============================================================================
# 主視窗
# ==============================================================================

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CBSC 量化交易系統")
        self.setMinimumSize(1200, 800)

        # 深色背景
        self.setStyleSheet("""
            QMainWindow { background: #1a1a2e; }
            QGroupBox { color: #e0e0e0; font-weight: bold; border: 1px solid #333; border-radius: 6px; margin-top: 8px; padding-top: 12px; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; }
            QLabel { color: #e0e0e0; }
            QTableWidget { background: #16213e; color: #e0e0e0; gridline-color: #333; }
            QHeaderView::section { background: #0f3460; color: #e0e0e0; }
            QPushButton { background: #1890ff; color: white; border: none; padding: 8px 16px; border-radius: 4px; font-size: 13px; }
            QPushButton:hover { background: #40a9ff; }
            QPushButton:pressed { background: #096dd9; }
            QCheckBox { color: #e0e0e0; }
        """)

        self.init_ui()
        self.init_timer()
        self.refresh_all()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # 頂部工具欄
        toolbar = QHBoxLayout()
        title = QLabel("📊 CBSC 量化交易系統")
        f = title.font(); f.setPointSize(16); f.setBold(True); title.setFont(f)
        title.setStyleSheet("color: #1890ff;")
        toolbar.addWidget(title)
        toolbar.addStretch()

        self.chk_backtest = QCheckBox("更新時跑回測")
        self.chk_backtest.setChecked(False)
        toolbar.addWidget(self.chk_backtest)

        self.chk_auto = QCheckBox("每日自動更新 (16:15)")
        self.chk_auto.setChecked(True)
        self.chk_auto.stateChanged.connect(self.toggle_auto_update)
        toolbar.addWidget(self.chk_auto)

        self.btn_update = QPushButton("🔄 立即更新數據")
        self.btn_update.clicked.connect(self.update_data)
        toolbar.addWidget(self.btn_update)

        layout.addLayout(toolbar)

        # 進度條
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        # Tab 頁
        self.tabs = QTabWidget()
        self.hkex_tab = HkexTab()
        self.sc_tab = StockConnectTab()
        self.bt_tab = BacktestTab()
        self.tabs.addTab(self.hkex_tab, "📈 HKEX 每日報告")
        self.tabs.addTab(self.sc_tab, "💰 南北水資金流向")
        self.tabs.addTab(self.bt_tab, "🔬 回測結果")
        layout.addWidget(self.tabs)

        # 狀態欄
        self.statusBar().showMessage(f"就緒 | 數據目錄: {DATA_DIR}")

    def init_timer(self):
        """每日定時更新（16:15 HKT，收市後15分鐘）"""
        self.auto_timer = QTimer(self)
        self.auto_timer.timeout.connect(self.check_auto_update)
        self.auto_timer.start(60000)  # 每分鐘檢查一次
        self.last_auto_date = None

    def check_auto_update(self):
        if not self.chk_auto.isChecked():
            return
        now = datetime.now()
        # 交易日 16:15 自動更新（週一到週五）
        if now.weekday() < 5 and now.hour == 16 and now.minute >= 15:
            today_key = now.strftime("%Y%m%d")
            if today_key != self.last_auto_date:
                self.last_auto_date = today_key
                self.update_data()

    def toggle_auto_update(self):
        if self.chk_auto.isChecked():
            self.statusBar().showMessage("✅ 每日自動更新已開啟 (16:15)")
        else:
            self.statusBar().showMessage("⛔ 自動更新已關閉")

    def update_data(self):
        """觸發數據更新"""
        self.btn_update.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)  # 不確定進度

        self.worker = UpdateWorker(run_backtest=self.chk_backtest.isChecked())
        self.worker.progress.connect(lambda msg: self.statusBar().showMessage(msg))
        self.worker.finished_signal.connect(self.on_update_done)
        self.worker.start()

    def on_update_done(self, success, message):
        self.progress.setVisible(False)
        self.btn_update.setEnabled(True)
        self.statusBar().showMessage(message)
        if success:
            self.refresh_all()

    def refresh_all(self):
        """重新載入所有 tab 的數據"""
        self.hkex_tab.load_data()
        self.sc_tab.load_data()
        self.bt_tab.load_data()
        self.statusBar().showMessage(f"✅ 數據已更新 | {datetime.now().strftime('%H:%M:%S')}")


# ==============================================================================
# 入口
# ==============================================================================

def main():
    # 高 DPI 支援
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

    app = QApplication(sys.argv)
    app.setApplicationName("CBSC 量化交易系統")

    # pyqtgraph 深色主題
    pg.setConfigOption("background", "#1a1a2e")
    pg.setConfigOption("foreground", "#e0e0e0")

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
